"""
Brand Intelligence Content Hub - Google Workspace Export Module

Creates Google Slides presentations and Google Docs documents from structured
content with full brand formatting.  Supports service-account and OAuth
credential flows, branded slide/document generation, sharing controls, and
local-file-to-Workspace upload.

This module is designed to be self-contained: when the Google API client
libraries are not installed every public method returns a descriptive error
dict rather than raising an ``ImportError``.

Usage:
    from app.generators.google_export import GoogleWorkspaceExporter

    exporter = GoogleWorkspaceExporter()
    if exporter.authenticate():
        result = exporter.export_to_slides(
            content={
                "slides": [
                    {"layout": "title", "title": "Q1 Review", "body": "Jan - Mar 2026"},
                    {"layout": "content", "title": "Highlights", "bullets": ["Revenue +12%", "NPS 72"]},
                    {"layout": "closing", "title": "Thank You"},
                ]
            },
            title="Q1 Review Deck",
        )
        print(result["url"])
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import (
    BASE_DIR,
    BRAND_ASSETS_DIR,
    LOGOS_DIR,
    PRESENTATIONS_DIR,
    DOCUMENTS_DIR,
    get_env,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional Google API imports
# ---------------------------------------------------------------------------

try:
    from google.oauth2.service_account import Credentials as ServiceAccountCredentials
    from google.oauth2.credentials import Credentials as OAuthCredentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

# ---------------------------------------------------------------------------
# Optional local-file parsers (used by export_from_file)
# ---------------------------------------------------------------------------

try:
    from pptx import Presentation as PptxPresentation
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]

SLIDE_LAYOUTS = {
    "BLANK": 0,
    "TITLE": 1,
    "TITLE_AND_BODY": 2,
    "TITLE_AND_TWO_COLUMNS": 3,
    "TITLE_ONLY": 4,
    "SECTION_HEADER": 5,
}

# Default brand colours (used when brand_config.json is absent)
DEFAULT_BRAND_COLORS = {
    "primary": "#0066CC",
    "secondary": "#004499",
    "accent": "#FF6600",
    "background": "#FFFFFF",
    "text": "#333333",
}

# Default font families
DEFAULT_FONTS = {
    "heading": "Arial",
    "body": "Calibri",
}

# Google Slides page element dimension constants (EMU - English Metric Units)
# 1 inch = 914400 EMU
EMU_PER_INCH = 914_400
SLIDE_WIDTH_EMU = int(10 * EMU_PER_INCH)      # 10 inches (widescreen)
SLIDE_HEIGHT_EMU = int(5.625 * EMU_PER_INCH)   # 5.625 inches (16:9)

# Standard error messages
_ERR_NO_LIB = (
    "Google API libraries not installed. "
    "Run: pip install google-api-python-client google-auth"
)
_ERR_NO_AUTH = (
    "Not authenticated. Configure GOOGLE_SERVICE_ACCOUNT_JSON or "
    "GOOGLE_OAUTH_CREDENTIALS_JSON in .env"
)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _error_dict(message: str) -> dict:
    """Return a standardised error-result dictionary.

    Parameters
    ----------
    message : str
        Human-readable description of the error.

    Returns
    -------
    dict
        ``{'success': False, 'error': <message>}``
    """
    return {"success": False, "error": message}


def _success_dict(**kwargs) -> dict:
    """Return a standardised success-result dictionary.

    All keyword arguments are merged into the returned dict alongside
    ``{'success': True}``.

    Returns
    -------
    dict
        ``{'success': True, ...}``
    """
    result = {"success": True}
    result.update(kwargs)
    return result


# ---------------------------------------------------------------------------
# Main exporter class
# ---------------------------------------------------------------------------


class GoogleWorkspaceExporter:
    """Export content to Google Slides and Google Docs with brand formatting.

    The exporter reads brand colours, fonts, and logo configuration from
    ``brand_assets/brand_config.json`` (falling back to sensible defaults)
    and applies them consistently to every presentation or document it
    creates inside Google Workspace.

    Two authentication modes are supported:

    1. **Service account** -- set the ``GOOGLE_SERVICE_ACCOUNT_JSON``
       environment variable to the path of a service-account JSON key file.
    2. **OAuth** -- set the ``GOOGLE_OAUTH_CREDENTIALS_JSON`` environment
       variable to the path of an OAuth ``credentials.json`` file.

    The exporter attempts service-account authentication first, then falls
    back to OAuth.  Both methods produce scoped credentials for the Slides,
    Docs, and Drive APIs.

    Typical workflow::

        exporter = GoogleWorkspaceExporter()
        exporter.authenticate()
        result = exporter.export_to_slides(content, title="My Deck")
        if result["success"]:
            exporter.set_sharing(result["presentation_id"], anyone=True)
    """

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        """Initialise the exporter.

        Loads the brand configuration, resolves brand colours and fonts,
        and sets the credential / service attributes to ``None`` (call
        :meth:`authenticate` before exporting).
        """
        self.brand_config: dict = self._load_brand_config()
        self.brand_colors: Dict[str, str] = self._resolve_brand_colors()
        self.brand_fonts: Dict[str, str] = self._resolve_brand_fonts()
        self.logo_path: Optional[str] = self._find_logo()
        self.company_name: str = self.brand_config.get("company_name", "")

        # Google API state -- populated by authenticate()
        self.credentials = None
        self.slides_service = None
        self.docs_service = None
        self.drive_service = None
        self.is_authenticated: bool = False
        self._auth_method: str = "none"

        logger.info(
            "GoogleWorkspaceExporter initialised  |  brand=%s  google_libs=%s",
            self.company_name or "(default)",
            GOOGLE_API_AVAILABLE,
        )

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self) -> bool:
        """Authenticate with Google APIs.

        Attempts a service-account flow first (using the path stored in
        the ``GOOGLE_SERVICE_ACCOUNT_JSON`` environment variable).  If that
        is not configured, falls back to an OAuth credential file (from
        ``GOOGLE_OAUTH_CREDENTIALS_JSON``).

        On success the ``slides_service``, ``docs_service``, and
        ``drive_service`` attributes are populated and ``is_authenticated``
        is set to ``True``.

        Returns
        -------
        bool
            ``True`` if authentication succeeded, ``False`` otherwise.
        """
        if not GOOGLE_API_AVAILABLE:
            logger.error("Cannot authenticate: %s", _ERR_NO_LIB)
            return False

        # --- Try service-account credentials first -----------------------
        sa_path = get_env("GOOGLE_SERVICE_ACCOUNT_JSON")
        if sa_path and os.path.isfile(sa_path):
            try:
                self.credentials = ServiceAccountCredentials.from_service_account_file(
                    sa_path,
                    scopes=SCOPES,
                )
                self._auth_method = "service_account"
                logger.info("Authenticated via service account: %s", sa_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Service-account auth failed: %s", exc)
                self.credentials = None

        # --- Fall back to OAuth credentials ------------------------------
        if self.credentials is None:
            oauth_path = get_env("GOOGLE_OAUTH_CREDENTIALS_JSON")
            if oauth_path and os.path.isfile(oauth_path):
                try:
                    with open(oauth_path, encoding="utf-8") as fh:
                        cred_data = json.load(fh)
                    self.credentials = OAuthCredentials.from_authorized_user_info(
                        cred_data,
                        scopes=SCOPES,
                    )
                    self._auth_method = "oauth"
                    logger.info("Authenticated via OAuth credentials: %s", oauth_path)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("OAuth auth failed: %s", exc)
                    self.credentials = None

        if self.credentials is None:
            logger.error("No valid Google credentials found.")
            self.is_authenticated = False
            return False

        # --- Build API service handles -----------------------------------
        try:
            self.slides_service = build("slides", "v1", credentials=self.credentials)
            self.docs_service = build("docs", "v1", credentials=self.credentials)
            self.drive_service = build("drive", "v3", credentials=self.credentials)
            self.is_authenticated = True
            logger.info(
                "Google API services built successfully (method=%s).",
                self._auth_method,
            )
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to build Google API services: %s", exc)
            self.is_authenticated = False
            return False

    # ------------------------------------------------------------------
    # Brand configuration helpers
    # ------------------------------------------------------------------

    def _load_brand_config(self) -> dict:
        """Load ``brand_assets/brand_config.json``.

        Returns an empty dictionary if the file is missing or unparseable,
        ensuring the exporter can always fall back to default styles.

        Returns
        -------
        dict
            Parsed brand configuration or ``{}``.
        """
        config_path = BRAND_ASSETS_DIR / "brand_config.json"
        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as fh:
                    data = json.load(fh)
                logger.info("Loaded brand config from %s", config_path)
                return data
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not load brand config: %s", exc)
        else:
            logger.info("No brand_config.json found; using defaults.")
        return {}

    def _resolve_brand_colors(self) -> Dict[str, str]:
        """Extract hex colour strings from brand config with defaults.

        Returns
        -------
        dict
            Mapping of colour role (``primary``, ``secondary``, etc.) to
            hex colour strings like ``#0066CC``.
        """
        colors_cfg = self.brand_config.get("colors", {})
        return {
            "primary": colors_cfg.get("primary", DEFAULT_BRAND_COLORS["primary"]),
            "secondary": colors_cfg.get("secondary", DEFAULT_BRAND_COLORS["secondary"]),
            "accent": colors_cfg.get("accent", DEFAULT_BRAND_COLORS["accent"]),
            "background": colors_cfg.get("background", DEFAULT_BRAND_COLORS["background"]),
            "text": colors_cfg.get("text", DEFAULT_BRAND_COLORS["text"]),
        }

    def _resolve_brand_fonts(self) -> Dict[str, str]:
        """Extract font family names from brand config with defaults.

        Returns
        -------
        dict
            ``{'heading': '<family>', 'body': '<family>'}``
        """
        fonts_cfg = self.brand_config.get("fonts", {})
        return {
            "heading": fonts_cfg.get("heading", DEFAULT_FONTS["heading"]),
            "body": fonts_cfg.get("body", DEFAULT_FONTS["body"]),
        }

    def _find_logo(self) -> Optional[str]:
        """Return the path to the first logo image in ``brand_assets/logos/``.

        Searches for PNG, JPG, JPEG, and SVG files in that priority order.
        Returns ``None`` when no logo is available.
        """
        if not LOGOS_DIR.exists():
            return None
        for pattern in ("*.png", "*.jpg", "*.jpeg", "*.svg"):
            logos = list(LOGOS_DIR.glob(pattern))
            if logos:
                return str(logos[0])
        return None

    # ------------------------------------------------------------------
    # Colour conversion utilities
    # ------------------------------------------------------------------

    def _hex_to_rgb_float(self, hex_color: str) -> dict:
        """Convert a ``#RRGGBB`` hex colour to Google API float-RGB.

        Google Slides / Docs APIs express colours as floats in [0.0, 1.0].

        Parameters
        ----------
        hex_color : str
            Hex colour string, e.g. ``#0066CC``.  A missing ``#`` prefix
            is tolerated.

        Returns
        -------
        dict
            ``{'red': float, 'green': float, 'blue': float}`` with each
            component in the range [0.0, 1.0].
        """
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return {"red": 0.0, "green": 0.0, "blue": 0.0}
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return {"red": r, "green": g, "blue": b}

    def _rgb_float_to_color(self, hex_color: str) -> dict:
        """Return a full ``rgbColor`` wrapper suitable for the Google API.

        Parameters
        ----------
        hex_color : str
            Hex colour string, e.g. ``#0066CC``.

        Returns
        -------
        dict
            ``{'rgbColor': {'red': ..., 'green': ..., 'blue': ...}}``
        """
        return {"rgbColor": self._hex_to_rgb_float(hex_color)}

    # ------------------------------------------------------------------
    # Pre-flight checks
    # ------------------------------------------------------------------

    def _preflight(self) -> Optional[dict]:
        """Validate that the exporter is ready to make API calls.

        Returns ``None`` if everything is fine, or an error dict that
        should be returned immediately by the calling method.
        """
        if not GOOGLE_API_AVAILABLE:
            return _error_dict(_ERR_NO_LIB)
        if not self.is_authenticated:
            return _error_dict(_ERR_NO_AUTH)
        return None

    # ====================================================================
    # Google Slides
    # ====================================================================

    def export_to_slides(
        self,
        content: dict,
        title: str = "Untitled Presentation",
    ) -> dict:
        """Create a Google Slides presentation from structured content.

        Parameters
        ----------
        content : dict
            Structured content dictionary.  Expected keys:

            - **slides** (``list[dict]``): Ordered slide definitions.  Each
              slide dict may contain:

              - *layout* (``str``): ``"title"``, ``"content"``,
                ``"two_column"``, ``"section"``, or ``"closing"``.
                Defaults to ``"content"``.
              - *title* (``str``): Slide title text.
              - *body* (``str | list``): Body text.  A list is joined
                with newlines.
              - *bullets* (``list[str]``): Bullet points.
              - *notes* (``str``, optional): Speaker-notes text.
              - *left_column* (``str``, optional): Left-column text for
                ``two_column`` layout.
              - *right_column* (``str``, optional): Right-column text for
                ``two_column`` layout.

        title : str
            Presentation title (also used for the Google Drive file name).

        Returns
        -------
        dict
            ``{'success': True, 'presentation_id': str, 'url': str}`` on
            success, or ``{'success': False, 'error': str}`` on failure.
        """
        err = self._preflight()
        if err:
            return err

        try:
            presentation_id = self._create_presentation(title)
            logger.info(
                "Created presentation '%s' (id=%s)", title, presentation_id
            )

            slides = content.get("slides", [])
            if not slides:
                logger.warning("No slides provided in content; returning empty presentation.")
                url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
                return _success_dict(presentation_id=presentation_id, url=url)

            # Dispatch each slide to the appropriate builder
            for idx, slide_data in enumerate(slides):
                layout = slide_data.get("layout", "content").lower().strip()
                logger.debug("Adding slide %d  layout=%s", idx + 1, layout)

                if layout == "title":
                    self._add_title_slide(presentation_id, slide_data)
                elif layout == "two_column":
                    self._add_two_column_slide(presentation_id, slide_data)
                elif layout in ("section", "section_header", "section_divider"):
                    self._add_section_slide(presentation_id, slide_data)
                elif layout == "closing":
                    self._add_closing_slide(presentation_id, slide_data)
                else:
                    # Default: standard content slide
                    self._add_content_slide(presentation_id, slide_data)

            # Apply brand palette across all slides
            self._apply_brand_formatting(presentation_id)

            url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
            logger.info("Presentation ready: %s", url)
            return _success_dict(presentation_id=presentation_id, url=url)

        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to export slides: %s", exc)
            return _error_dict(f"Slides export failed: {exc}")

    # ---- Slide creation helpers ----------------------------------------

    def _create_presentation(self, title: str) -> str:
        """Create a new, empty Google Slides presentation.

        Parameters
        ----------
        title : str
            The presentation title that appears in Google Drive.

        Returns
        -------
        str
            The newly created presentation ID.
        """
        body = {"title": title}
        presentation = (
            self.slides_service.presentations()
            .create(body=body)
            .execute()
        )
        return presentation["presentationId"]

    def _new_object_id(self) -> str:
        """Generate a unique object ID for slide elements.

        Google Slides requires that every page element have a unique
        alphanumeric identifier.  We use a UUID4 hex prefix to guarantee
        uniqueness.

        Returns
        -------
        str
            A unique object-ID string safe for Google Slides API.
        """
        return f"elem_{uuid.uuid4().hex[:12]}"

    def _add_title_slide(self, presentation_id: str, slide_data: dict) -> None:
        """Add a title slide with branded colours.

        Creates a blank slide then places a large title text box centred
        on the page, plus a smaller subtitle box beneath it.  Both are
        styled with brand colours and fonts.

        Parameters
        ----------
        presentation_id : str
            ID of the target presentation.
        slide_data : dict
            Slide definition containing at least ``title`` and optionally
            ``body`` (used as subtitle).
        """
        slide_id = self._new_object_id()
        title_id = self._new_object_id()
        subtitle_id = self._new_object_id()

        title_text = slide_data.get("title", "Untitled")
        subtitle_text = slide_data.get("body", "")
        if isinstance(subtitle_text, list):
            subtitle_text = "\n".join(subtitle_text)

        requests: list[dict] = []

        # --- Create a blank slide ----------------------------------------
        requests.append({
            "createSlide": {
                "objectId": slide_id,
                "slideLayoutReference": {"predefinedLayout": "BLANK"},
            }
        })

        # --- Background colour -------------------------------------------
        requests.append({
            "updatePageProperties": {
                "objectId": slide_id,
                "pageProperties": {
                    "pageBackgroundFill": {
                        "solidFill": {
                            "color": self._rgb_float_to_color(
                                self.brand_colors["primary"]
                            ),
                        }
                    }
                },
                "fields": "pageBackgroundFill.solidFill.color",
            }
        })

        # --- Title text box ----------------------------------------------
        requests.append({
            "createShape": {
                "objectId": title_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": SLIDE_WIDTH_EMU * 0.8, "unit": "EMU"},
                        "height": {"magnitude": SLIDE_HEIGHT_EMU * 0.3, "unit": "EMU"},
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": SLIDE_WIDTH_EMU * 0.1,
                        "translateY": SLIDE_HEIGHT_EMU * 0.25,
                        "unit": "EMU",
                    },
                },
            }
        })

        # Insert title text
        requests.append({
            "insertText": {
                "objectId": title_id,
                "text": title_text,
                "insertionIndex": 0,
            }
        })

        # Style title text
        requests.append({
            "updateTextStyle": {
                "objectId": title_id,
                "style": self._build_text_style(
                    bold=True,
                    font_size=36,
                    color="#FFFFFF",
                    font_family=self.brand_fonts["heading"],
                ),
                "textRange": {"type": "ALL"},
                "fields": "bold,fontSize,foregroundColor,fontFamily",
            }
        })

        # Centre-align title
        requests.append({
            "updateParagraphStyle": {
                "objectId": title_id,
                "style": {"alignment": "CENTER"},
                "textRange": {"type": "ALL"},
                "fields": "alignment",
            }
        })

        # --- Subtitle text box -------------------------------------------
        if subtitle_text:
            requests.append({
                "createShape": {
                    "objectId": subtitle_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": SLIDE_WIDTH_EMU * 0.7, "unit": "EMU"},
                            "height": {"magnitude": SLIDE_HEIGHT_EMU * 0.15, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": SLIDE_WIDTH_EMU * 0.15,
                            "translateY": SLIDE_HEIGHT_EMU * 0.58,
                            "unit": "EMU",
                        },
                    },
                }
            })

            requests.append({
                "insertText": {
                    "objectId": subtitle_id,
                    "text": subtitle_text,
                    "insertionIndex": 0,
                }
            })

            requests.append({
                "updateTextStyle": {
                    "objectId": subtitle_id,
                    "style": self._build_text_style(
                        bold=False,
                        font_size=20,
                        color="#FFFFFF",
                        font_family=self.brand_fonts["body"],
                    ),
                    "textRange": {"type": "ALL"},
                    "fields": "bold,fontSize,foregroundColor,fontFamily",
                }
            })

            requests.append({
                "updateParagraphStyle": {
                    "objectId": subtitle_id,
                    "style": {"alignment": "CENTER"},
                    "textRange": {"type": "ALL"},
                    "fields": "alignment",
                }
            })

        # --- Execute batch -----------------------------------------------
        self.slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests},
        ).execute()

    def _add_content_slide(self, presentation_id: str, slide_data: dict) -> None:
        """Add a content slide with title and body/bullets.

        The slide has a title bar at the top and a body area below.  When
        ``bullets`` is provided each item becomes a bullet-prefixed line;
        otherwise ``body`` text is used as-is.

        Parameters
        ----------
        presentation_id : str
            ID of the target presentation.
        slide_data : dict
            Slide definition with ``title`` and ``body`` or ``bullets``.
        """
        slide_id = self._new_object_id()
        title_id = self._new_object_id()
        body_id = self._new_object_id()

        title_text = slide_data.get("title", "")
        body_text = slide_data.get("body", "")
        if isinstance(body_text, list):
            body_text = "\n".join(body_text)
        bullets = slide_data.get("bullets", [])
        notes_text = slide_data.get("notes", "")

        requests: list[dict] = []

        # --- Create blank slide ------------------------------------------
        requests.append({
            "createSlide": {
                "objectId": slide_id,
                "slideLayoutReference": {"predefinedLayout": "BLANK"},
            }
        })

        # --- Title text box at top ---------------------------------------
        if title_text:
            requests.append({
                "createShape": {
                    "objectId": title_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": SLIDE_WIDTH_EMU * 0.9, "unit": "EMU"},
                            "height": {"magnitude": SLIDE_HEIGHT_EMU * 0.15, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": SLIDE_WIDTH_EMU * 0.05,
                            "translateY": SLIDE_HEIGHT_EMU * 0.04,
                            "unit": "EMU",
                        },
                    },
                }
            })

            requests.append({
                "insertText": {
                    "objectId": title_id,
                    "text": title_text,
                    "insertionIndex": 0,
                }
            })

            requests.append({
                "updateTextStyle": {
                    "objectId": title_id,
                    "style": self._build_text_style(
                        bold=True,
                        font_size=28,
                        color=self.brand_colors["primary"],
                        font_family=self.brand_fonts["heading"],
                    ),
                    "textRange": {"type": "ALL"},
                    "fields": "bold,fontSize,foregroundColor,fontFamily",
                }
            })

        # --- Body area ---------------------------------------------------
        if bullets:
            content_text = "\n".join(f"\u2022 {b}" for b in bullets)
        elif body_text:
            content_text = body_text
        else:
            content_text = ""

        if content_text:
            requests.append({
                "createShape": {
                    "objectId": body_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": SLIDE_WIDTH_EMU * 0.9, "unit": "EMU"},
                            "height": {"magnitude": SLIDE_HEIGHT_EMU * 0.7, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": SLIDE_WIDTH_EMU * 0.05,
                            "translateY": SLIDE_HEIGHT_EMU * 0.22,
                            "unit": "EMU",
                        },
                    },
                }
            })

            requests.append({
                "insertText": {
                    "objectId": body_id,
                    "text": content_text,
                    "insertionIndex": 0,
                }
            })

            requests.append({
                "updateTextStyle": {
                    "objectId": body_id,
                    "style": self._build_text_style(
                        bold=False,
                        font_size=16,
                        color=self.brand_colors["text"],
                        font_family=self.brand_fonts["body"],
                    ),
                    "textRange": {"type": "ALL"},
                    "fields": "bold,fontSize,foregroundColor,fontFamily",
                }
            })

        # --- Speaker notes -----------------------------------------------
        if notes_text:
            requests.append({
                "updateNotesSlide": {
                    "objectId": slide_id,
                    "text": notes_text,
                }
            })

        # --- Execute batch -----------------------------------------------
        self.slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests},
        ).execute()

    def _add_two_column_slide(self, presentation_id: str, slide_data: dict) -> None:
        """Add a two-column layout slide.

        The slide is split vertically into two halves beneath the title.
        Column text comes from ``left_column`` / ``right_column`` keys in
        *slide_data*.

        Parameters
        ----------
        presentation_id : str
            ID of the target presentation.
        slide_data : dict
            Slide definition with ``title``, ``left_column``, and
            ``right_column``.
        """
        slide_id = self._new_object_id()
        title_id = self._new_object_id()
        left_id = self._new_object_id()
        right_id = self._new_object_id()

        title_text = slide_data.get("title", "")
        left_text = slide_data.get("left_column", "")
        right_text = slide_data.get("right_column", "")

        if isinstance(left_text, list):
            left_text = "\n".join(left_text)
        if isinstance(right_text, list):
            right_text = "\n".join(right_text)

        requests: list[dict] = []

        # --- Create blank slide ------------------------------------------
        requests.append({
            "createSlide": {
                "objectId": slide_id,
                "slideLayoutReference": {"predefinedLayout": "BLANK"},
            }
        })

        # --- Title -------------------------------------------------------
        if title_text:
            requests.append({
                "createShape": {
                    "objectId": title_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": SLIDE_WIDTH_EMU * 0.9, "unit": "EMU"},
                            "height": {"magnitude": SLIDE_HEIGHT_EMU * 0.15, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": SLIDE_WIDTH_EMU * 0.05,
                            "translateY": SLIDE_HEIGHT_EMU * 0.04,
                            "unit": "EMU",
                        },
                    },
                }
            })
            requests.append({
                "insertText": {
                    "objectId": title_id,
                    "text": title_text,
                    "insertionIndex": 0,
                }
            })
            requests.append({
                "updateTextStyle": {
                    "objectId": title_id,
                    "style": self._build_text_style(
                        bold=True,
                        font_size=28,
                        color=self.brand_colors["primary"],
                        font_family=self.brand_fonts["heading"],
                    ),
                    "textRange": {"type": "ALL"},
                    "fields": "bold,fontSize,foregroundColor,fontFamily",
                }
            })

        # --- Left column -------------------------------------------------
        if left_text:
            requests.append({
                "createShape": {
                    "objectId": left_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": SLIDE_WIDTH_EMU * 0.42, "unit": "EMU"},
                            "height": {"magnitude": SLIDE_HEIGHT_EMU * 0.68, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": SLIDE_WIDTH_EMU * 0.05,
                            "translateY": SLIDE_HEIGHT_EMU * 0.22,
                            "unit": "EMU",
                        },
                    },
                }
            })
            requests.append({
                "insertText": {
                    "objectId": left_id,
                    "text": left_text,
                    "insertionIndex": 0,
                }
            })
            requests.append({
                "updateTextStyle": {
                    "objectId": left_id,
                    "style": self._build_text_style(
                        bold=False,
                        font_size=14,
                        color=self.brand_colors["text"],
                        font_family=self.brand_fonts["body"],
                    ),
                    "textRange": {"type": "ALL"},
                    "fields": "bold,fontSize,foregroundColor,fontFamily",
                }
            })

        # --- Right column ------------------------------------------------
        if right_text:
            requests.append({
                "createShape": {
                    "objectId": right_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": SLIDE_WIDTH_EMU * 0.42, "unit": "EMU"},
                            "height": {"magnitude": SLIDE_HEIGHT_EMU * 0.68, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": SLIDE_WIDTH_EMU * 0.53,
                            "translateY": SLIDE_HEIGHT_EMU * 0.22,
                            "unit": "EMU",
                        },
                    },
                }
            })
            requests.append({
                "insertText": {
                    "objectId": right_id,
                    "text": right_text,
                    "insertionIndex": 0,
                }
            })
            requests.append({
                "updateTextStyle": {
                    "objectId": right_id,
                    "style": self._build_text_style(
                        bold=False,
                        font_size=14,
                        color=self.brand_colors["text"],
                        font_family=self.brand_fonts["body"],
                    ),
                    "textRange": {"type": "ALL"},
                    "fields": "bold,fontSize,foregroundColor,fontFamily",
                }
            })

        # --- Execute batch -----------------------------------------------
        self.slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests},
        ).execute()

    def _add_section_slide(self, presentation_id: str, slide_data: dict) -> None:
        """Add a section-divider slide.

        A full-bleed branded background with a large centred heading,
        ideal for separating major sections within a presentation.

        Parameters
        ----------
        presentation_id : str
            ID of the target presentation.
        slide_data : dict
            Slide definition with ``title`` and optionally ``body``
            (displayed as a smaller subtitle beneath the heading).
        """
        slide_id = self._new_object_id()
        title_id = self._new_object_id()
        subtitle_id = self._new_object_id()

        title_text = slide_data.get("title", "Section")
        subtitle_text = slide_data.get("body", "")
        if isinstance(subtitle_text, list):
            subtitle_text = "\n".join(subtitle_text)

        requests: list[dict] = []

        # --- Create slide with branded background ------------------------
        requests.append({
            "createSlide": {
                "objectId": slide_id,
                "slideLayoutReference": {"predefinedLayout": "BLANK"},
            }
        })

        requests.append({
            "updatePageProperties": {
                "objectId": slide_id,
                "pageProperties": {
                    "pageBackgroundFill": {
                        "solidFill": {
                            "color": self._rgb_float_to_color(
                                self.brand_colors["secondary"]
                            ),
                        }
                    }
                },
                "fields": "pageBackgroundFill.solidFill.color",
            }
        })

        # --- Section title -----------------------------------------------
        requests.append({
            "createShape": {
                "objectId": title_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": SLIDE_WIDTH_EMU * 0.8, "unit": "EMU"},
                        "height": {"magnitude": SLIDE_HEIGHT_EMU * 0.25, "unit": "EMU"},
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": SLIDE_WIDTH_EMU * 0.1,
                        "translateY": SLIDE_HEIGHT_EMU * 0.3,
                        "unit": "EMU",
                    },
                },
            }
        })

        requests.append({
            "insertText": {
                "objectId": title_id,
                "text": title_text,
                "insertionIndex": 0,
            }
        })

        requests.append({
            "updateTextStyle": {
                "objectId": title_id,
                "style": self._build_text_style(
                    bold=True,
                    font_size=32,
                    color="#FFFFFF",
                    font_family=self.brand_fonts["heading"],
                ),
                "textRange": {"type": "ALL"},
                "fields": "bold,fontSize,foregroundColor,fontFamily",
            }
        })

        requests.append({
            "updateParagraphStyle": {
                "objectId": title_id,
                "style": {"alignment": "CENTER"},
                "textRange": {"type": "ALL"},
                "fields": "alignment",
            }
        })

        # --- Optional subtitle -------------------------------------------
        if subtitle_text:
            requests.append({
                "createShape": {
                    "objectId": subtitle_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": SLIDE_WIDTH_EMU * 0.6, "unit": "EMU"},
                            "height": {"magnitude": SLIDE_HEIGHT_EMU * 0.12, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": SLIDE_WIDTH_EMU * 0.2,
                            "translateY": SLIDE_HEIGHT_EMU * 0.58,
                            "unit": "EMU",
                        },
                    },
                }
            })

            requests.append({
                "insertText": {
                    "objectId": subtitle_id,
                    "text": subtitle_text,
                    "insertionIndex": 0,
                }
            })

            requests.append({
                "updateTextStyle": {
                    "objectId": subtitle_id,
                    "style": self._build_text_style(
                        bold=False,
                        font_size=18,
                        color="#FFFFFF",
                        font_family=self.brand_fonts["body"],
                    ),
                    "textRange": {"type": "ALL"},
                    "fields": "bold,fontSize,foregroundColor,fontFamily",
                }
            })

            requests.append({
                "updateParagraphStyle": {
                    "objectId": subtitle_id,
                    "style": {"alignment": "CENTER"},
                    "textRange": {"type": "ALL"},
                    "fields": "alignment",
                }
            })

        # --- Execute batch -----------------------------------------------
        self.slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests},
        ).execute()

    def _add_closing_slide(self, presentation_id: str, slide_data: dict) -> None:
        """Add a closing / thank-you slide.

        Similar to a title slide but with a branded accent-colour
        background and optional company name line.

        Parameters
        ----------
        presentation_id : str
            ID of the target presentation.
        slide_data : dict
            Slide definition with ``title`` (e.g. ``"Thank You"``),
            optionally ``body`` (e.g. contact info).
        """
        slide_id = self._new_object_id()
        title_id = self._new_object_id()
        body_id = self._new_object_id()
        company_id = self._new_object_id()

        title_text = slide_data.get("title", "Thank You")
        body_text = slide_data.get("body", "")
        if isinstance(body_text, list):
            body_text = "\n".join(body_text)

        requests: list[dict] = []

        # --- Create slide with accent background -------------------------
        requests.append({
            "createSlide": {
                "objectId": slide_id,
                "slideLayoutReference": {"predefinedLayout": "BLANK"},
            }
        })

        requests.append({
            "updatePageProperties": {
                "objectId": slide_id,
                "pageProperties": {
                    "pageBackgroundFill": {
                        "solidFill": {
                            "color": self._rgb_float_to_color(
                                self.brand_colors["primary"]
                            ),
                        }
                    }
                },
                "fields": "pageBackgroundFill.solidFill.color",
            }
        })

        # --- Closing title -----------------------------------------------
        requests.append({
            "createShape": {
                "objectId": title_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": SLIDE_WIDTH_EMU * 0.8, "unit": "EMU"},
                        "height": {"magnitude": SLIDE_HEIGHT_EMU * 0.25, "unit": "EMU"},
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": SLIDE_WIDTH_EMU * 0.1,
                        "translateY": SLIDE_HEIGHT_EMU * 0.2,
                        "unit": "EMU",
                    },
                },
            }
        })

        requests.append({
            "insertText": {
                "objectId": title_id,
                "text": title_text,
                "insertionIndex": 0,
            }
        })

        requests.append({
            "updateTextStyle": {
                "objectId": title_id,
                "style": self._build_text_style(
                    bold=True,
                    font_size=40,
                    color="#FFFFFF",
                    font_family=self.brand_fonts["heading"],
                ),
                "textRange": {"type": "ALL"},
                "fields": "bold,fontSize,foregroundColor,fontFamily",
            }
        })

        requests.append({
            "updateParagraphStyle": {
                "objectId": title_id,
                "style": {"alignment": "CENTER"},
                "textRange": {"type": "ALL"},
                "fields": "alignment",
            }
        })

        # --- Optional body text (contact info, etc.) ---------------------
        if body_text:
            requests.append({
                "createShape": {
                    "objectId": body_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": SLIDE_WIDTH_EMU * 0.7, "unit": "EMU"},
                            "height": {"magnitude": SLIDE_HEIGHT_EMU * 0.15, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": SLIDE_WIDTH_EMU * 0.15,
                            "translateY": SLIDE_HEIGHT_EMU * 0.5,
                            "unit": "EMU",
                        },
                    },
                }
            })

            requests.append({
                "insertText": {
                    "objectId": body_id,
                    "text": body_text,
                    "insertionIndex": 0,
                }
            })

            requests.append({
                "updateTextStyle": {
                    "objectId": body_id,
                    "style": self._build_text_style(
                        bold=False,
                        font_size=16,
                        color="#FFFFFF",
                        font_family=self.brand_fonts["body"],
                    ),
                    "textRange": {"type": "ALL"},
                    "fields": "bold,fontSize,foregroundColor,fontFamily",
                }
            })

            requests.append({
                "updateParagraphStyle": {
                    "objectId": body_id,
                    "style": {"alignment": "CENTER"},
                    "textRange": {"type": "ALL"},
                    "fields": "alignment",
                }
            })

        # --- Company name footer -----------------------------------------
        if self.company_name:
            requests.append({
                "createShape": {
                    "objectId": company_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": SLIDE_WIDTH_EMU * 0.5, "unit": "EMU"},
                            "height": {"magnitude": SLIDE_HEIGHT_EMU * 0.08, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": SLIDE_WIDTH_EMU * 0.25,
                            "translateY": SLIDE_HEIGHT_EMU * 0.85,
                            "unit": "EMU",
                        },
                    },
                }
            })

            requests.append({
                "insertText": {
                    "objectId": company_id,
                    "text": self.company_name,
                    "insertionIndex": 0,
                }
            })

            requests.append({
                "updateTextStyle": {
                    "objectId": company_id,
                    "style": self._build_text_style(
                        bold=False,
                        font_size=12,
                        color="#FFFFFF",
                        font_family=self.brand_fonts["body"],
                    ),
                    "textRange": {"type": "ALL"},
                    "fields": "bold,fontSize,foregroundColor,fontFamily",
                }
            })

            requests.append({
                "updateParagraphStyle": {
                    "objectId": company_id,
                    "style": {"alignment": "CENTER"},
                    "textRange": {"type": "ALL"},
                    "fields": "alignment",
                }
            })

        # --- Execute batch -----------------------------------------------
        self.slides_service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={"requests": requests},
        ).execute()

    # ---- Slide formatting helpers --------------------------------------

    def _apply_brand_formatting(self, presentation_id: str) -> None:
        """Apply brand colours and fonts across all slides in a presentation.

        Iterates over every slide and sets the background of slides that
        do not already have a custom background to the brand background
        colour.  This ensures consistent branding even when slides were
        added by layout-specific methods that did not set a background.

        Parameters
        ----------
        presentation_id : str
            ID of the target presentation.
        """
        try:
            presentation = (
                self.slides_service.presentations()
                .get(presentationId=presentation_id)
                .execute()
            )
            slides = presentation.get("slides", [])
            requests: list[dict] = []

            for slide in slides:
                page_id = slide["objectId"]
                # Only set background if the slide does not have a custom fill
                bg_fill = (
                    slide.get("pageProperties", {})
                    .get("pageBackgroundFill", {})
                )
                has_solid_fill = "solidFill" in bg_fill
                if not has_solid_fill:
                    requests.append({
                        "updatePageProperties": {
                            "objectId": page_id,
                            "pageProperties": {
                                "pageBackgroundFill": {
                                    "solidFill": {
                                        "color": self._rgb_float_to_color(
                                            self.brand_colors["background"]
                                        ),
                                    }
                                }
                            },
                            "fields": "pageBackgroundFill.solidFill.color",
                        }
                    })

            if requests:
                self.slides_service.presentations().batchUpdate(
                    presentationId=presentation_id,
                    body={"requests": requests},
                ).execute()
                logger.debug(
                    "Applied brand background to %d slide(s).", len(requests)
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not apply brand formatting: %s", exc)

    def _build_text_style(
        self,
        bold: bool = False,
        font_size: int = 14,
        color: Optional[str] = None,
        font_family: Optional[str] = None,
    ) -> dict:
        """Build a Google Slides ``TextStyle`` dictionary.

        Parameters
        ----------
        bold : bool
            Whether the text is bold.
        font_size : int
            Font size in points.
        color : str or None
            Hex colour (e.g. ``#333333``).  ``None`` leaves the colour
            unchanged.
        font_family : str or None
            Font family name (e.g. ``"Arial"``).  ``None`` leaves the font
            unchanged.

        Returns
        -------
        dict
            A ``TextStyle`` dict ready for the Slides batch-update API.
        """
        style: dict[str, Any] = {
            "bold": bold,
            "fontSize": {"magnitude": font_size, "unit": "PT"},
        }
        if color is not None:
            style["foregroundColor"] = {
                "opaqueColor": self._rgb_float_to_color(color),
            }
        if font_family is not None:
            style["fontFamily"] = font_family
        return style

    # ====================================================================
    # Google Docs
    # ====================================================================

    def export_to_docs(
        self,
        content: dict,
        title: str = "Untitled Document",
    ) -> dict:
        """Create a Google Doc from structured content.

        Parameters
        ----------
        content : dict
            Structured content dictionary.  Expected keys:

            - **sections** (``list[dict]``): Ordered section definitions.
              Each section dict may contain:

              - *heading* (``str``): Section heading text.
              - *level* (``int``): Heading level 1-3.  Defaults to 1.
              - *body* (``str | list[str]``): Body paragraphs.  Lists are
                treated as multiple paragraphs.
              - *bullets* (``list[str]``): Bullet-point items.
              - *table* (``dict``): Table with ``headers`` (list of
                strings) and ``rows`` (list of lists).
              - *callout* (``str``): Highlighted callout / note text.

        title : str
            Document title (also used for the Google Drive file name).

        Returns
        -------
        dict
            ``{'success': True, 'document_id': str, 'url': str}`` on
            success, or ``{'success': False, 'error': str}`` on failure.
        """
        err = self._preflight()
        if err:
            return err

        try:
            document_id = self._create_document(title)
            logger.info("Created document '%s' (id=%s)", title, document_id)

            sections = content.get("sections", [])
            if not sections:
                logger.warning("No sections provided; returning empty document.")
                url = f"https://docs.google.com/document/d/{document_id}/edit"
                return _success_dict(document_id=document_id, url=url)

            # Google Docs API uses a 1-based insertion index.  Index 1 is
            # immediately after the initial empty paragraph that every new
            # document contains.
            index = 1

            for sec_idx, section in enumerate(sections):
                logger.debug("Processing section %d: %s", sec_idx + 1, section.get("heading", "(no heading)"))

                # --- Heading ---------------------------------------------
                heading = section.get("heading")
                level = section.get("level", 1)
                if heading:
                    index = self._insert_heading(document_id, heading, level, index)

                # --- Body paragraphs -------------------------------------
                body = section.get("body")
                if body:
                    if isinstance(body, str):
                        body = [body]
                    for paragraph in body:
                        index = self._insert_paragraph(document_id, paragraph, index)

                # --- Bullets ---------------------------------------------
                bullets = section.get("bullets")
                if bullets:
                    index = self._insert_bullets(document_id, bullets, index)

                # --- Table -----------------------------------------------
                table = section.get("table")
                if table:
                    index = self._insert_table(document_id, table, index)

                # --- Callout / note --------------------------------------
                callout = section.get("callout")
                if callout:
                    index = self._insert_paragraph(
                        document_id,
                        f"\u25b6 {callout}",
                        index,
                        bold=True,
                        color=self.brand_colors["accent"],
                    )

            # Apply brand styles at the end
            self._apply_doc_brand_styles(document_id)

            url = f"https://docs.google.com/document/d/{document_id}/edit"
            logger.info("Document ready: %s", url)
            return _success_dict(document_id=document_id, url=url)

        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to export doc: %s", exc)
            return _error_dict(f"Docs export failed: {exc}")

    # ---- Document creation helpers -------------------------------------

    def _create_document(self, title: str) -> str:
        """Create a new, empty Google Doc.

        Parameters
        ----------
        title : str
            The document title that appears in Google Drive.

        Returns
        -------
        str
            The newly created document ID.
        """
        body = {"title": title}
        document = self.docs_service.documents().create(body=body).execute()
        return document["documentId"]

    def _insert_heading(
        self,
        document_id: str,
        text: str,
        level: int,
        index: int,
    ) -> int:
        """Insert a heading into a Google Doc.

        Parameters
        ----------
        document_id : str
            ID of the target document.
        text : str
            Heading text.
        level : int
            Heading level (1-3).  Values outside this range are clamped.
        index : int
            The document body index at which to insert.

        Returns
        -------
        int
            The updated insertion index (after the heading and its newline).
        """
        level = max(1, min(level, 3))
        heading_type = f"HEADING_{level}"

        # The text must end with a newline; Google Docs treats each
        # paragraph as terminated by '\n'.
        insert_text = text + "\n"

        requests = [
            {
                "insertText": {
                    "location": {"index": index},
                    "text": insert_text,
                }
            },
            {
                "updateParagraphStyle": {
                    "range": {
                        "startIndex": index,
                        "endIndex": index + len(insert_text),
                    },
                    "paragraphStyle": {
                        "namedStyleType": heading_type,
                    },
                    "fields": "namedStyleType",
                }
            },
            {
                "updateTextStyle": {
                    "range": {
                        "startIndex": index,
                        "endIndex": index + len(insert_text) - 1,
                    },
                    "textStyle": {
                        "bold": True,
                        "foregroundColor": {
                            "color": self._rgb_float_to_color(
                                self.brand_colors["primary"]
                            ),
                        },
                        "fontSize": {
                            "magnitude": {1: 24, 2: 20, 3: 16}.get(level, 16),
                            "unit": "PT",
                        },
                        "weightedFontFamily": {
                            "fontFamily": self.brand_fonts["heading"],
                        },
                    },
                    "fields": "bold,foregroundColor,fontSize,weightedFontFamily",
                }
            },
        ]

        self.docs_service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": requests},
        ).execute()

        return index + len(insert_text)

    def _insert_paragraph(
        self,
        document_id: str,
        text: str,
        index: int,
        bold: bool = False,
        color: Optional[str] = None,
    ) -> int:
        """Insert a body paragraph into a Google Doc.

        Parameters
        ----------
        document_id : str
            ID of the target document.
        text : str
            Paragraph text (should **not** include a trailing newline;
            one is appended automatically).
        index : int
            The document body index at which to insert.
        bold : bool
            Whether the paragraph text should be bold.
        color : str or None
            Hex colour override.  ``None`` uses the brand text colour.

        Returns
        -------
        int
            The updated insertion index.
        """
        insert_text = text + "\n"
        resolved_color = color or self.brand_colors["text"]

        requests = [
            {
                "insertText": {
                    "location": {"index": index},
                    "text": insert_text,
                }
            },
            {
                "updateParagraphStyle": {
                    "range": {
                        "startIndex": index,
                        "endIndex": index + len(insert_text),
                    },
                    "paragraphStyle": {
                        "namedStyleType": "NORMAL_TEXT",
                        "spaceBelow": {"magnitude": 6, "unit": "PT"},
                    },
                    "fields": "namedStyleType,spaceBelow",
                }
            },
            {
                "updateTextStyle": {
                    "range": {
                        "startIndex": index,
                        "endIndex": index + len(insert_text) - 1,
                    },
                    "textStyle": {
                        "bold": bold,
                        "foregroundColor": {
                            "color": self._rgb_float_to_color(resolved_color),
                        },
                        "fontSize": {"magnitude": 11, "unit": "PT"},
                        "weightedFontFamily": {
                            "fontFamily": self.brand_fonts["body"],
                        },
                    },
                    "fields": "bold,foregroundColor,fontSize,weightedFontFamily",
                }
            },
        ]

        self.docs_service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": requests},
        ).execute()

        return index + len(insert_text)

    def _insert_bullets(
        self,
        document_id: str,
        items: list,
        index: int,
    ) -> int:
        """Insert a bulleted list into a Google Doc.

        Each item becomes a separate paragraph.  After insertion, a
        ``createParagraphBullets`` request is applied to the range.

        Parameters
        ----------
        document_id : str
            ID of the target document.
        items : list[str]
            Bullet-point strings.
        index : int
            The document body index at which to insert.

        Returns
        -------
        int
            The updated insertion index (after all bullet paragraphs).
        """
        if not items:
            return index

        # Build the combined text block -- each item on its own line
        combined = "\n".join(items) + "\n"
        end_index = index + len(combined)

        requests = [
            # Insert all bullet text at once
            {
                "insertText": {
                    "location": {"index": index},
                    "text": combined,
                }
            },
            # Apply bullet formatting to the range
            {
                "createParagraphBullets": {
                    "range": {
                        "startIndex": index,
                        "endIndex": end_index,
                    },
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                }
            },
            # Style the bullet text
            {
                "updateTextStyle": {
                    "range": {
                        "startIndex": index,
                        "endIndex": end_index - 1,
                    },
                    "textStyle": {
                        "fontSize": {"magnitude": 11, "unit": "PT"},
                        "foregroundColor": {
                            "color": self._rgb_float_to_color(
                                self.brand_colors["text"]
                            ),
                        },
                        "weightedFontFamily": {
                            "fontFamily": self.brand_fonts["body"],
                        },
                    },
                    "fields": "fontSize,foregroundColor,weightedFontFamily",
                }
            },
        ]

        self.docs_service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": requests},
        ).execute()

        return end_index

    def _insert_table(
        self,
        document_id: str,
        table_data: dict,
        index: int,
    ) -> int:
        """Insert a table with headers and rows into a Google Doc.

        Parameters
        ----------
        document_id : str
            ID of the target document.
        table_data : dict
            Table definition with:

            - **headers** (``list[str]``): Column header labels.
            - **rows** (``list[list[str]]``): Data rows; each row is a
              list of cell strings.

        index : int
            The document body index at which to insert.

        Returns
        -------
        int
            The updated insertion index (after the table).

        Notes
        -----
        Google Docs tables are inserted first as an empty grid, then
        populated cell-by-cell with ``insertText`` requests.  The index
        arithmetic accounts for the structural characters that Google
        inserts for table elements (start-of-table, start-of-row,
        start-of-cell, end-of-cell, newlines, etc.).
        """
        headers = table_data.get("headers", [])
        rows = table_data.get("rows", [])
        if not headers:
            return index

        num_cols = len(headers)
        num_rows = len(rows) + 1  # +1 for header row

        # --- Step 1: insert the empty table grid -------------------------
        insert_requests = [
            {
                "insertTable": {
                    "rows": num_rows,
                    "columns": num_cols,
                    "location": {"index": index},
                }
            }
        ]

        self.docs_service.documents().batchUpdate(
            documentId=document_id,
            body={"requests": insert_requests},
        ).execute()

        # --- Step 2: re-read the document to get accurate table indices --
        doc = self.docs_service.documents().get(documentId=document_id).execute()
        body_content = doc.get("body", {}).get("content", [])

        # Find the table structural element closest to our insertion index
        table_element = None
        for element in body_content:
            if "table" in element:
                start = element.get("startIndex", 0)
                if start >= index:
                    table_element = element
                    break

        if table_element is None:
            logger.warning("Could not locate inserted table; skipping cell population.")
            # Estimate the index advancement
            estimated_advance = num_rows * num_cols * 3 + num_rows + 2
            return index + estimated_advance

        # --- Step 3: populate cells (header row then data rows) ----------
        cell_requests: list[dict] = []
        table_rows = table_element.get("table", {}).get("tableRows", [])

        for row_idx, table_row in enumerate(table_rows):
            cells = table_row.get("tableCells", [])
            for col_idx, cell in enumerate(cells):
                # Determine the text to insert
                if row_idx == 0:
                    cell_text = headers[col_idx] if col_idx < len(headers) else ""
                else:
                    data_row = rows[row_idx - 1] if (row_idx - 1) < len(rows) else []
                    cell_text = str(data_row[col_idx]) if col_idx < len(data_row) else ""

                if not cell_text:
                    continue

                # Each cell's content starts with a paragraph element
                cell_content = cell.get("content", [])
                if cell_content:
                    cell_start = cell_content[0].get("startIndex", 0)
                else:
                    continue

                cell_requests.append({
                    "insertText": {
                        "location": {"index": cell_start},
                        "text": cell_text,
                    }
                })

                # Bold header cells
                if row_idx == 0:
                    cell_requests.append({
                        "updateTextStyle": {
                            "range": {
                                "startIndex": cell_start,
                                "endIndex": cell_start + len(cell_text),
                            },
                            "textStyle": {
                                "bold": True,
                                "foregroundColor": {
                                    "color": self._rgb_float_to_color(
                                        self.brand_colors["primary"]
                                    ),
                                },
                                "weightedFontFamily": {
                                    "fontFamily": self.brand_fonts["heading"],
                                },
                            },
                            "fields": "bold,foregroundColor,weightedFontFamily",
                        }
                    })

        # Cell text must be inserted in reverse index order to prevent
        # shifting.  Sort descending by insertion index.
        cell_requests.sort(
            key=lambda r: (
                r.get("insertText", r.get("updateTextStyle", {}))
                .get("location", r.get("range", {}))
                .get("index", r.get("startIndex", 0))
            ),
            reverse=True,
        )

        if cell_requests:
            self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={"requests": cell_requests},
            ).execute()

        # Calculate new index: past the end of the table element
        table_end = table_element.get("endIndex", index + 1)
        return table_end

    def _apply_doc_brand_styles(self, document_id: str) -> None:
        """Apply brand heading styles and colours to the entire document.

        Updates the document's named styles (HEADING_1 through HEADING_3
        and NORMAL_TEXT) to use brand fonts and colours, giving the
        document a cohesive branded look.

        Parameters
        ----------
        document_id : str
            ID of the target document.
        """
        try:
            requests = [
                {
                    "updateDocumentStyle": {
                        "documentStyle": {
                            "defaultHeaderId": "",
                        },
                        "fields": "defaultHeaderId",
                    }
                },
            ]

            # Update named styles for headings and body text
            named_style_updates = []

            for level in (1, 2, 3):
                size = {1: 24, 2: 20, 3: 16}[level]
                named_style_updates.append({
                    "namedStyleType": f"HEADING_{level}",
                    "textStyle": {
                        "bold": True,
                        "fontSize": {"magnitude": size, "unit": "PT"},
                        "foregroundColor": {
                            "color": self._rgb_float_to_color(
                                self.brand_colors["primary"]
                            ),
                        },
                        "weightedFontFamily": {
                            "fontFamily": self.brand_fonts["heading"],
                        },
                    },
                    "paragraphStyle": {
                        "spaceAbove": {"magnitude": 12, "unit": "PT"},
                        "spaceBelow": {"magnitude": 4, "unit": "PT"},
                    },
                })

            named_style_updates.append({
                "namedStyleType": "NORMAL_TEXT",
                "textStyle": {
                    "fontSize": {"magnitude": 11, "unit": "PT"},
                    "foregroundColor": {
                        "color": self._rgb_float_to_color(
                            self.brand_colors["text"]
                        ),
                    },
                    "weightedFontFamily": {
                        "fontFamily": self.brand_fonts["body"],
                    },
                },
                "paragraphStyle": {
                    "lineSpacing": 115,
                    "spaceBelow": {"magnitude": 6, "unit": "PT"},
                },
            })

            requests.append({
                "updateNamedStyles": {
                    "namedStyles": {
                        "styles": named_style_updates,
                    },
                    "fields": (
                        "textStyle.bold,"
                        "textStyle.fontSize,"
                        "textStyle.foregroundColor,"
                        "textStyle.weightedFontFamily,"
                        "paragraphStyle.spaceAbove,"
                        "paragraphStyle.spaceBelow,"
                        "paragraphStyle.lineSpacing"
                    ),
                }
            })

            self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={"requests": requests},
            ).execute()

            logger.debug("Applied brand named styles to document %s", document_id)

        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not apply document brand styles: %s", exc)

    # ====================================================================
    # Sharing
    # ====================================================================

    def set_sharing(
        self,
        file_id: str,
        permission: str = "reader",
        email: Optional[str] = None,
        anyone: bool = False,
    ) -> dict:
        """Set sharing permissions on a Google Drive file.

        Parameters
        ----------
        file_id : str
            Google Drive file ID (the presentation or document ID).
        permission : str
            Permission role: ``"reader"``, ``"writer"``, or
            ``"commenter"``.
        email : str or None
            Email address to share with.  Ignored when *anyone* is True.
        anyone : bool
            If ``True``, create a public "anyone with the link" permission.

        Returns
        -------
        dict
            ``{'success': True, 'permission_id': str}`` or
            ``{'success': False, 'error': str}``.
        """
        err = self._preflight()
        if err:
            return err

        valid_roles = ("reader", "writer", "commenter")
        if permission not in valid_roles:
            return _error_dict(
                f"Invalid permission '{permission}'. Use one of: {valid_roles}"
            )

        try:
            if anyone:
                perm_body = {
                    "type": "anyone",
                    "role": permission,
                }
            elif email:
                perm_body = {
                    "type": "user",
                    "role": permission,
                    "emailAddress": email,
                }
            else:
                return _error_dict(
                    "Provide either email= or anyone=True for sharing."
                )

            result = (
                self.drive_service.permissions()
                .create(
                    fileId=file_id,
                    body=perm_body,
                    fields="id",
                )
                .execute()
            )

            permission_id = result.get("id", "")
            logger.info(
                "Set %s permission on %s (perm_id=%s, anyone=%s, email=%s)",
                permission,
                file_id,
                permission_id,
                anyone,
                email,
            )
            return _success_dict(permission_id=permission_id)

        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to set sharing: %s", exc)
            return _error_dict(f"Sharing failed: {exc}")

    def get_shareable_link(self, file_id: str) -> str:
        """Return the web link for a Google Slides or Docs file.

        Parameters
        ----------
        file_id : str
            Google Drive file ID.

        Returns
        -------
        str
            The web-view URL for the file.  Returns an empty string if the
            file cannot be retrieved or the API is not available.
        """
        err = self._preflight()
        if err:
            return ""

        try:
            file_meta = (
                self.drive_service.files()
                .get(fileId=file_id, fields="webViewLink")
                .execute()
            )
            return file_meta.get("webViewLink", "")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not retrieve shareable link: %s", exc)
            return ""

    # ====================================================================
    # Utility
    # ====================================================================

    def check_connection(self) -> dict:
        """Test the Google API connection and report status.

        Returns
        -------
        dict
            Connection status dictionary::

                {
                    'connected': bool,
                    'method': 'service_account' | 'oauth' | 'none',
                    'services': ['slides', 'docs', 'drive'],
                    'error': str,
                }
        """
        if not GOOGLE_API_AVAILABLE:
            return {
                "connected": False,
                "method": "none",
                "services": [],
                "error": _ERR_NO_LIB,
            }

        if not self.is_authenticated:
            return {
                "connected": False,
                "method": "none",
                "services": [],
                "error": _ERR_NO_AUTH,
            }

        available_services: list[str] = []
        errors: list[str] = []

        # --- Test Slides API ---------------------------------------------
        try:
            self.slides_service.presentations().create(
                body={"title": "__connection_test__"}
            )
            # We intentionally do NOT execute -- just confirm the service
            # object is functional enough to build the request.
            available_services.append("slides")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"slides: {exc}")

        # --- Test Docs API -----------------------------------------------
        try:
            self.docs_service.documents().create(
                body={"title": "__connection_test__"}
            )
            available_services.append("docs")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"docs: {exc}")

        # --- Test Drive API ----------------------------------------------
        try:
            self.drive_service.files().list(pageSize=1)
            available_services.append("drive")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"drive: {exc}")

        connected = len(available_services) > 0
        error_msg = "; ".join(errors) if errors else ""

        return {
            "connected": connected,
            "method": self._auth_method,
            "services": available_services,
            "error": error_msg,
        }

    def list_recent_exports(self, max_results: int = 10) -> list:
        """List recently created files in Google Drive.

        Queries for Google Slides and Docs files owned by the authenticated
        user, ordered by most recently modified.

        Parameters
        ----------
        max_results : int
            Maximum number of files to return.

        Returns
        -------
        list[dict]
            List of file metadata dicts, each containing ``id``, ``name``,
            ``mimeType``, ``modifiedTime``, and ``webViewLink``.  Returns
            an empty list on error.
        """
        err = self._preflight()
        if err:
            return []

        try:
            query = (
                "(mimeType='application/vnd.google-apps.presentation' "
                "or mimeType='application/vnd.google-apps.document')"
            )
            result = (
                self.drive_service.files()
                .list(
                    q=query,
                    pageSize=max_results,
                    orderBy="modifiedTime desc",
                    fields="files(id,name,mimeType,modifiedTime,webViewLink)",
                )
                .execute()
            )
            files = result.get("files", [])
            logger.info("Retrieved %d recent exports.", len(files))
            return files

        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not list recent exports: %s", exc)
            return []

    # ====================================================================
    # Local file export
    # ====================================================================

    def export_from_file(
        self,
        file_path: str,
        export_type: str = "slides",
    ) -> dict:
        """Export a local PPTX or DOCX file to Google Workspace.

        Reads the local file, extracts its content into the structured
        dict format expected by :meth:`export_to_slides` or
        :meth:`export_to_docs`, then creates the corresponding Google
        Workspace resource.

        Parameters
        ----------
        file_path : str
            Absolute or relative path to a ``.pptx`` or ``.docx`` file.
        export_type : str
            ``"slides"`` or ``"docs"``.  This determines which Google
            Workspace format is created regardless of the source file type.

        Returns
        -------
        dict
            Result dict from :meth:`export_to_slides` or
            :meth:`export_to_docs`, or an error dict if the file cannot
            be read.
        """
        err = self._preflight()
        if err:
            return err

        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return _error_dict(f"File not found: {file_path}")

        extension = file_path_obj.suffix.lower()
        title = file_path_obj.stem

        # --- Extract content from PPTX -----------------------------------
        if extension == ".pptx":
            content = self._extract_pptx_content(file_path_obj)
            if content is None:
                return _error_dict(
                    "Could not parse PPTX. Ensure python-pptx is installed: "
                    "pip install python-pptx"
                )
        # --- Extract content from DOCX -----------------------------------
        elif extension == ".docx":
            content = self._extract_docx_content(file_path_obj)
            if content is None:
                return _error_dict(
                    "Could not parse DOCX. Ensure python-docx is installed: "
                    "pip install python-docx"
                )
        else:
            return _error_dict(
                f"Unsupported file extension '{extension}'. Use .pptx or .docx"
            )

        # --- Route to the appropriate exporter ---------------------------
        if export_type == "slides":
            return self.export_to_slides(content, title=title)
        elif export_type == "docs":
            return self.export_to_docs(content, title=title)
        else:
            return _error_dict(
                f"Invalid export_type '{export_type}'. Use 'slides' or 'docs'."
            )

    # ---- Local file parsers --------------------------------------------

    def _extract_pptx_content(self, file_path: Path) -> Optional[dict]:
        """Extract structured slide content from a local PPTX file.

        Uses python-pptx to iterate over slides and extract titles, body
        text, and notes into the dict format expected by
        :meth:`export_to_slides`.

        Parameters
        ----------
        file_path : Path
            Path to the ``.pptx`` file.

        Returns
        -------
        dict or None
            Structured content dict, or ``None`` if python-pptx is not
            available or the file cannot be read.
        """
        if not PPTX_AVAILABLE:
            logger.error("python-pptx is not installed; cannot parse PPTX.")
            return None

        try:
            prs = PptxPresentation(str(file_path))
            slides: list[dict] = []

            for slide_idx, slide in enumerate(prs.slides):
                slide_data: dict[str, Any] = {}

                # Determine layout name
                if slide_idx == 0:
                    slide_data["layout"] = "title"
                elif slide_idx == len(prs.slides) - 1:
                    slide_data["layout"] = "closing"
                else:
                    slide_data["layout"] = "content"

                # Extract text from shapes
                title_text = ""
                body_parts: list[str] = []

                for shape in slide.shapes:
                    if not shape.has_text_frame:
                        continue
                    text = shape.text_frame.text.strip()
                    if not text:
                        continue

                    if shape == slide.shapes.title or (
                        hasattr(shape, "placeholder_format")
                        and shape.placeholder_format is not None
                        and shape.placeholder_format.idx == 0
                    ):
                        title_text = text
                    else:
                        body_parts.append(text)

                slide_data["title"] = title_text or f"Slide {slide_idx + 1}"

                if body_parts:
                    slide_data["body"] = "\n\n".join(body_parts)

                # Extract speaker notes
                if slide.has_notes_slide:
                    notes = slide.notes_slide.notes_text_frame.text.strip()
                    if notes:
                        slide_data["notes"] = notes

                slides.append(slide_data)

            logger.info("Extracted %d slides from %s", len(slides), file_path.name)
            return {"slides": slides}

        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to extract PPTX content: %s", exc)
            return None

    def _extract_docx_content(self, file_path: Path) -> Optional[dict]:
        """Extract structured section content from a local DOCX file.

        Uses python-docx to iterate over paragraphs and tables, grouping
        content under headings into the dict format expected by
        :meth:`export_to_docs`.

        Parameters
        ----------
        file_path : Path
            Path to the ``.docx`` file.

        Returns
        -------
        dict or None
            Structured content dict, or ``None`` if python-docx is not
            available or the file cannot be read.
        """
        if not DOCX_AVAILABLE:
            logger.error("python-docx is not installed; cannot parse DOCX.")
            return None

        try:
            doc = DocxDocument(str(file_path))
            sections: list[dict] = []
            current_section: Optional[dict] = None

            for element in doc.element.body:
                tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

                if tag == "p":
                    # Find matching paragraph object
                    para = None
                    for p in doc.paragraphs:
                        if p._element is element:
                            para = p
                            break
                    if para is None:
                        continue

                    style_name = para.style.name if para.style else ""
                    text = para.text.strip()
                    if not text:
                        continue

                    # Detect headings
                    if style_name.startswith("Heading"):
                        try:
                            level = int(style_name.replace("Heading", "").strip())
                        except ValueError:
                            level = 1
                        current_section = {
                            "heading": text,
                            "level": level,
                            "body": [],
                        }
                        sections.append(current_section)
                    elif style_name.startswith("List"):
                        # Accumulate as bullets
                        if current_section is None:
                            current_section = {
                                "heading": "Introduction",
                                "level": 1,
                                "body": [],
                                "bullets": [],
                            }
                            sections.append(current_section)
                        if "bullets" not in current_section:
                            current_section["bullets"] = []
                        current_section["bullets"].append(text)
                    else:
                        # Normal paragraph body text
                        if current_section is None:
                            current_section = {
                                "heading": "Introduction",
                                "level": 1,
                                "body": [],
                            }
                            sections.append(current_section)
                        current_section["body"].append(text)

                elif tag == "tbl":
                    # Extract table data
                    for table in doc.tables:
                        if table._element is element:
                            headers = []
                            rows = []
                            for row_idx, row in enumerate(table.rows):
                                cells = [cell.text.strip() for cell in row.cells]
                                if row_idx == 0:
                                    headers = cells
                                else:
                                    rows.append(cells)

                            if current_section is None:
                                current_section = {
                                    "heading": "Data",
                                    "level": 1,
                                    "body": [],
                                }
                                sections.append(current_section)

                            current_section["table"] = {
                                "headers": headers,
                                "rows": rows,
                            }
                            break

            # Ensure at least one section exists
            if not sections:
                all_text = "\n\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
                sections = [{
                    "heading": file_path.stem,
                    "level": 1,
                    "body": [all_text] if all_text else ["(empty document)"],
                }]

            logger.info(
                "Extracted %d sections from %s", len(sections), file_path.name
            )
            return {"sections": sections}

        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to extract DOCX content: %s", exc)
            return None
