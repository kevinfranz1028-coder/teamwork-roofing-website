"""
Brand Intelligence Content Hub - Napkin AI Integration

Wraps the Napkin AI API for generating diagrams, flowcharts, mind maps,
timelines, and infographics from text descriptions.
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

from app.config import get_env, BRAND_ASSETS_DIR, VISUALS_DIR, CACHE_DIR

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Napkin AI API base URL
# ---------------------------------------------------------------------------
NAPKIN_API_BASE = "https://api.napkin.ai/v1"


# ---------------------------------------------------------------------------
# Supported visual types with descriptions
# ---------------------------------------------------------------------------
VISUAL_TYPES = {
    "flowchart": {
        "name": "Flowchart",
        "description": "Process flows with decision points and steps",
        "best_for": ["Processes", "Workflows", "Decision trees"],
    },
    "mind_map": {
        "name": "Mind Map",
        "description": "Hierarchical idea exploration from a central concept",
        "best_for": ["Brainstorming", "Topic exploration", "Concept mapping"],
    },
    "timeline": {
        "name": "Timeline",
        "description": "Chronological sequence of events or milestones",
        "best_for": ["Project plans", "Historical events", "Roadmaps"],
    },
    "org_chart": {
        "name": "Org Chart",
        "description": "Organizational hierarchy and reporting structure",
        "best_for": ["Team structure", "Reporting lines", "Department layout"],
    },
    "process_diagram": {
        "name": "Process Diagram",
        "description": "Step-by-step process with inputs and outputs",
        "best_for": ["SOPs", "Manufacturing", "Service delivery"],
    },
    "infographic": {
        "name": "Infographic",
        "description": "Data visualization with icons and statistics",
        "best_for": ["Statistics", "Comparisons", "Key metrics"],
    },
    "comparison_chart": {
        "name": "Comparison Chart",
        "description": "Side-by-side comparison of features or options",
        "best_for": ["Product comparisons", "Pros/cons", "Feature matrices"],
    },
}

# ---------------------------------------------------------------------------
# Color modes
# ---------------------------------------------------------------------------
COLOR_MODES = {
    "brand": "Use brand colors from configuration",
    "light": "Light background with dark elements",
    "dark": "Dark background with light elements",
    "monochrome": "Single color with shading variations",
    "colorful": "Vibrant multi-color palette",
}

# ---------------------------------------------------------------------------
# Output formats and orientations
# ---------------------------------------------------------------------------
OUTPUT_FORMATS = ["png", "svg", "pptx"]

ORIENTATIONS = ["landscape", "portrait", "square"]


class NapkinClient:
    """Client for the Napkin AI visual generation API.

    Generates diagrams, flowcharts, mind maps, and infographics
    from text descriptions using Napkin AI.  Follows the same
    session / cached-availability / dict-return pattern used by
    ``PresentonClient``.
    """

    def __init__(self, api_token: Optional[str] = None, cache_enabled: bool = True):
        """Initialise the Napkin AI client.

        Args:
            api_token: Napkin API bearer token.  Falls back to the
                ``NAPKIN_API_TOKEN`` environment variable when *None*.
            cache_enabled: When *True* (default), generated visuals are
                cached on disk so identical requests are served instantly.
        """
        self.api_token = api_token or os.getenv("NAPKIN_API_TOKEN", "")
        self.base_url = NAPKIN_API_BASE
        self.session = requests.Session()
        if self.api_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            })
        self.cache_enabled = cache_enabled
        self.cache_dir = CACHE_DIR / "napkin_visuals"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._available: Optional[bool] = None
        self._brand_colors = self._load_brand_colors()

    # ------------------------------------------------------------------
    # Availability
    # ------------------------------------------------------------------

    @property
    def available(self) -> bool:
        """Check if Napkin AI is reachable and configured (cached)."""
        if self._available is None:
            self._available = self._check_availability()
        return self._available

    def _check_availability(self) -> bool:
        """Verify the API token is set and the service responds."""
        if not self.api_token:
            logger.warning("NAPKIN_API_TOKEN is not set")
            return False
        try:
            resp = self.session.get(
                f"{self.base_url}/status",
                timeout=10,
            )
            return resp.status_code < 500
        except requests.RequestException:
            # Even if the status endpoint is not implemented, the token
            # might still work for generation requests.
            return bool(self.api_token)

    # ------------------------------------------------------------------
    # Brand colours
    # ------------------------------------------------------------------

    def _load_brand_colors(self) -> dict:
        """Load brand colors from ``brand_assets/brand_config.json``."""
        config_path = BRAND_ASSETS_DIR / "brand_config.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                return config.get("colors", {})
            except (json.JSONDecodeError, OSError) as exc:
                logger.debug("Could not load brand colors: %s", exc)
        return {}

    def _resolve_colors(self, color_mode: str) -> dict:
        """Resolve a five-key color dict based on *color_mode*.

        When *color_mode* is ``"brand"`` the colours stored in
        ``brand_config.json`` are returned (with sensible defaults for
        any missing keys).  Other modes map to built-in palettes.
        """
        if color_mode == "brand" and self._brand_colors:
            return {
                "primary": self._brand_colors.get("primary", "#0066CC"),
                "secondary": self._brand_colors.get("secondary", "#004499"),
                "accent": self._brand_colors.get("accent", "#FF6600"),
                "background": self._brand_colors.get("background", "#FFFFFF"),
                "text": self._brand_colors.get("text", "#333333"),
            }

        presets = {
            "light": {
                "primary": "#2563EB",
                "secondary": "#3B82F6",
                "accent": "#F59E0B",
                "background": "#FFFFFF",
                "text": "#1F2937",
            },
            "dark": {
                "primary": "#60A5FA",
                "secondary": "#93C5FD",
                "accent": "#FBBF24",
                "background": "#1F2937",
                "text": "#F9FAFB",
            },
            "monochrome": {
                "primary": "#374151",
                "secondary": "#6B7280",
                "accent": "#9CA3AF",
                "background": "#FFFFFF",
                "text": "#111827",
            },
            "colorful": {
                "primary": "#8B5CF6",
                "secondary": "#EC4899",
                "accent": "#10B981",
                "background": "#FFFFFF",
                "text": "#1F2937",
            },
        }
        return presets.get(color_mode, presets["light"])

    # ------------------------------------------------------------------
    # Caching helpers
    # ------------------------------------------------------------------

    def _get_cache_key(self, text: str, visual_type: str, style: str,
                       color_mode: str, output_format: str) -> str:
        """Generate a deterministic cache key for a visual request."""
        content = f"{text}|{visual_type}|{style}|{color_mode}|{output_format}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _get_cached(self, cache_key: str, output_format: str) -> Optional[str]:
        """Return the path of a cached visual if it exists, else *None*."""
        if not self.cache_enabled:
            return None
        cached_path = self.cache_dir / f"{cache_key}.{output_format}"
        if cached_path.exists():
            logger.debug("Cache hit for visual %s", cache_key)
            return str(cached_path)
        return None

    def _save_to_cache(self, cache_key: str, output_format: str,
                       data: bytes) -> str:
        """Write visual bytes and metadata to the cache directory.

        Returns the absolute path of the cached visual file.
        """
        cached_path = self.cache_dir / f"{cache_key}.{output_format}"
        cached_path.write_bytes(data)
        # Persist lightweight metadata alongside the visual
        meta_path = self.cache_dir / f"{cache_key}.json"
        meta = {
            "cache_key": cache_key,
            "format": output_format,
            "cached_at": datetime.now().isoformat(),
            "size_bytes": len(data),
        }
        meta_path.write_text(json.dumps(meta, indent=2))
        return str(cached_path)

    # ------------------------------------------------------------------
    # Internal download helper
    # ------------------------------------------------------------------

    def _download_from_url(self, url: str) -> Optional[bytes]:
        """Download raw file content from *url*.

        Returns the response body as bytes, or *None* on failure.
        """
        try:
            resp = self.session.get(url, timeout=30, stream=True)
            if resp.status_code == 200:
                return resp.content
        except requests.RequestException as exc:
            logger.debug("Download from URL failed: %s", exc)
        return None

    # ------------------------------------------------------------------
    # Core generation
    # ------------------------------------------------------------------

    def generate_visual(
        self,
        text_content: str,
        visual_type: str = "flowchart",
        style: str = "professional",
        color_mode: str = "brand",
        language: str = "en",
        output_format: str = "png",
        orientation: str = "landscape",
        save_path: Optional[str] = None,
    ) -> dict:
        """Generate a visual from a text description using Napkin AI.

        Args:
            text_content: The text description to visualise.
            visual_type: One of the ``VISUAL_TYPES`` keys (e.g.
                ``"flowchart"``, ``"mind_map"``, ``"timeline"``).
            style: Visual style hint -- ``"professional"``,
                ``"minimal"``, ``"playful"``, or ``"technical"``.
            color_mode: One of the ``COLOR_MODES`` keys.
            language: ISO 639-1 language code.
            output_format: ``"png"``, ``"svg"``, or ``"pptx"``.
            orientation: ``"landscape"``, ``"portrait"``, or ``"square"``.
            save_path: Filesystem path for the generated file.  When
                *None* the file is saved under ``output/visuals/``.

        Returns:
            dict with keys:

            * **success** (*bool*) -- whether the visual was generated.
            * **file_path** (*str | None*) -- absolute path to the file.
            * **visual_type** (*str*) -- the requested visual type.
            * **cache_hit** (*bool*) -- whether the result came from cache.
            * **request_id** (*str | None*) -- upstream job id, if any.
            * **error** (*str | None*) -- human-readable error message.
            * **metadata** (*dict*) -- extra information about the result.
        """
        # --- Input validation ------------------------------------------------
        if not text_content or not text_content.strip():
            return {
                "success": False,
                "file_path": None,
                "visual_type": visual_type,
                "cache_hit": False,
                "request_id": None,
                "error": "Text content is empty",
                "metadata": {},
            }

        if visual_type not in VISUAL_TYPES:
            return {
                "success": False,
                "file_path": None,
                "visual_type": visual_type,
                "cache_hit": False,
                "request_id": None,
                "error": (
                    f"Unknown visual type '{visual_type}'. "
                    f"Valid types: {list(VISUAL_TYPES.keys())}"
                ),
                "metadata": {},
            }

        if output_format not in OUTPUT_FORMATS:
            logger.warning(
                "Unsupported output format '%s'; falling back to png",
                output_format,
            )
            output_format = "png"

        if orientation not in ORIENTATIONS:
            logger.warning(
                "Unsupported orientation '%s'; falling back to landscape",
                orientation,
            )
            orientation = "landscape"

        # --- Cache lookup -----------------------------------------------------
        cache_key = self._get_cache_key(
            text_content, visual_type, style, color_mode, output_format,
        )
        cached = self._get_cached(cache_key, output_format)
        if cached:
            return {
                "success": True,
                "file_path": cached,
                "visual_type": visual_type,
                "cache_hit": True,
                "request_id": None,
                "error": None,
                "metadata": {"source": "cache", "cache_key": cache_key},
            }

        # --- Token check ------------------------------------------------------
        if not self.api_token:
            return {
                "success": False,
                "file_path": None,
                "visual_type": visual_type,
                "cache_hit": False,
                "request_id": None,
                "error": (
                    "NAPKIN_API_TOKEN is not configured. "
                    "Set it in your .env file."
                ),
                "metadata": {},
            }

        # --- Build payload ----------------------------------------------------
        colors = self._resolve_colors(color_mode)

        payload = {
            "text": text_content,
            "type": visual_type,
            "style": style,
            "colors": colors,
            "language": language,
            "format": output_format,
            "orientation": orientation,
        }

        # --- API request ------------------------------------------------------
        try:
            resp = self.session.post(
                f"{self.base_url}/visuals/generate",
                json=payload,
                timeout=30,
            )

            if resp.status_code in (200, 201, 202):
                content_type = resp.headers.get("content-type", "")

                # Case 1 -- binary image/application returned directly
                if content_type.startswith("image/") or \
                   content_type.startswith("application/octet"):
                    file_data = resp.content
                    if save_path is None:
                        save_path = str(
                            VISUALS_DIR / f"napkin_{cache_key}.{output_format}"
                        )
                    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                    Path(save_path).write_bytes(file_data)
                    self._save_to_cache(cache_key, output_format, file_data)
                    return {
                        "success": True,
                        "file_path": save_path,
                        "visual_type": visual_type,
                        "cache_hit": False,
                        "request_id": None,
                        "error": None,
                        "metadata": {
                            "source": "api_direct",
                            "size_bytes": len(file_data),
                        },
                    }

                # Parse JSON body for async / URL-based responses
                data = (
                    resp.json()
                    if "json" in content_type
                    else {}
                )

                # Case 2 -- async job: poll until ready
                request_id = (
                    data.get("request_id")
                    or data.get("id")
                    or data.get("job_id")
                )
                if request_id:
                    poll_result = self.poll_status(request_id)
                    if poll_result["status"] == "completed":
                        download = self.download_result(
                            request_id, output_format, save_path, cache_key,
                        )
                        if download["success"]:
                            download["visual_type"] = visual_type
                        return download

                    return {
                        "success": False,
                        "file_path": None,
                        "visual_type": visual_type,
                        "cache_hit": False,
                        "request_id": request_id,
                        "error": poll_result.get(
                            "error", "Generation did not complete"
                        ),
                        "metadata": poll_result,
                    }

                # Case 3 -- response includes a download URL
                visual_url = (
                    data.get("url")
                    or data.get("image_url")
                    or data.get("download_url")
                )
                if visual_url:
                    file_data = self._download_from_url(visual_url)
                    if file_data:
                        if save_path is None:
                            save_path = str(
                                VISUALS_DIR / f"napkin_{cache_key}.{output_format}"
                            )
                        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                        Path(save_path).write_bytes(file_data)
                        self._save_to_cache(cache_key, output_format, file_data)
                        return {
                            "success": True,
                            "file_path": save_path,
                            "visual_type": visual_type,
                            "cache_hit": False,
                            "request_id": None,
                            "error": None,
                            "metadata": {
                                "source": "api_url",
                                "url": visual_url,
                            },
                        }

                # Fallthrough -- unrecognised response shape
                return {
                    "success": False,
                    "file_path": None,
                    "visual_type": visual_type,
                    "cache_hit": False,
                    "request_id": None,
                    "error": "Unexpected API response format",
                    "metadata": {"response_data": data},
                }

            # Non-success status codes
            error_msg = f"API returned status {resp.status_code}"
            try:
                err_data = resp.json()
                error_msg = err_data.get("error", err_data.get("message", error_msg))
            except Exception:
                pass
            return {
                "success": False,
                "file_path": None,
                "visual_type": visual_type,
                "cache_hit": False,
                "request_id": None,
                "error": error_msg,
                "metadata": {},
            }

        except requests.Timeout:
            return {
                "success": False,
                "file_path": None,
                "visual_type": visual_type,
                "cache_hit": False,
                "request_id": None,
                "error": (
                    "Request timed out. The Napkin AI service may be "
                    "slow or unreachable."
                ),
                "metadata": {},
            }
        except requests.ConnectionError:
            return {
                "success": False,
                "file_path": None,
                "visual_type": visual_type,
                "cache_hit": False,
                "request_id": None,
                "error": (
                    "Cannot connect to Napkin AI. "
                    "Check your internet connection."
                ),
                "metadata": {},
            }
        except requests.RequestException as exc:
            return {
                "success": False,
                "file_path": None,
                "visual_type": visual_type,
                "cache_hit": False,
                "request_id": None,
                "error": f"API request failed: {exc}",
                "metadata": {},
            }

    # ------------------------------------------------------------------
    # Async polling
    # ------------------------------------------------------------------

    def poll_status(
        self,
        request_id: str,
        max_wait: int = 120,
        interval: int = 3,
    ) -> dict:
        """Poll until visual generation completes or times out.

        Args:
            request_id: Job identifier returned by the generation endpoint.
            max_wait: Maximum seconds to wait before giving up.
            interval: Seconds to sleep between polls.

        Returns:
            dict with keys:

            * **status** -- ``"completed"``, ``"failed"``, or ``"timeout"``.
            * **progress** -- float between 0 and 1.
            * **result** -- upstream data dict when completed, else *None*.
            * **error** -- human-readable error string, or *None*.
        """
        if not request_id:
            return {
                "status": "error",
                "progress": 0,
                "result": None,
                "error": "No request_id provided",
            }

        elapsed = 0
        while elapsed < max_wait:
            try:
                resp = self.session.get(
                    f"{self.base_url}/visuals/{request_id}/status",
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status", "unknown")
                    progress = data.get("progress", 0)

                    if status in ("completed", "done", "finished", "ready"):
                        return {
                            "status": "completed",
                            "progress": 1.0,
                            "result": data,
                            "error": None,
                        }
                    if status in ("failed", "error"):
                        return {
                            "status": "failed",
                            "progress": progress,
                            "result": data,
                            "error": data.get("error", "Visual generation failed"),
                        }
                    # Still processing -- continue polling
            except requests.RequestException:
                pass

            time.sleep(interval)
            elapsed += interval

        return {
            "status": "timeout",
            "progress": 0,
            "result": None,
            "error": f"Timed out after {max_wait}s waiting for request {request_id}",
        }

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download_result(
        self,
        request_id: str,
        output_format: str = "png",
        save_path: Optional[str] = None,
        cache_key: Optional[str] = None,
    ) -> dict:
        """Download a completed visual by its *request_id*.

        Args:
            request_id: The generation job identifier.
            output_format: File extension (``"png"``, ``"svg"``, ``"pptx"``).
            save_path: Where to write the file.  Auto-generated when *None*.
            cache_key: If provided, the downloaded file is also stored in the
                local cache.

        Returns:
            dict with keys: success, file_path, visual_type, cache_hit,
            request_id, error, metadata.
        """
        try:
            resp = self.session.get(
                f"{self.base_url}/visuals/{request_id}/download",
                timeout=60,
                stream=True,
            )
            if resp.status_code == 200:
                file_data = resp.content
                if save_path is None:
                    name = cache_key or request_id
                    save_path = str(
                        VISUALS_DIR / f"napkin_{name}.{output_format}"
                    )
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                Path(save_path).write_bytes(file_data)

                if cache_key:
                    self._save_to_cache(cache_key, output_format, file_data)

                return {
                    "success": True,
                    "file_path": save_path,
                    "visual_type": "",
                    "cache_hit": False,
                    "request_id": request_id,
                    "error": None,
                    "metadata": {
                        "source": "api_download",
                        "size_bytes": len(file_data),
                    },
                }
        except requests.RequestException as exc:
            logger.error("Download failed for request %s: %s", request_id, exc)

        return {
            "success": False,
            "file_path": None,
            "visual_type": "",
            "cache_hit": False,
            "request_id": request_id,
            "error": "Failed to download visual",
            "metadata": {},
        }

    # ------------------------------------------------------------------
    # Batch generation
    # ------------------------------------------------------------------

    def batch_generate(self, items: list[dict]) -> list[dict]:
        """Generate multiple visuals in sequence.

        Each element of *items* is a dict whose keys match the parameters
        of :meth:`generate_visual` (``text_content``, ``visual_type``,
        ``style``, ``color_mode``, ``language``, ``output_format``,
        ``orientation``, ``save_path``).

        Returns:
            A list of result dicts, one per input item, in the same order.
        """
        results: list[dict] = []
        for idx, item in enumerate(items):
            logger.info(
                "Batch generate %d/%d (type=%s)",
                idx + 1,
                len(items),
                item.get("visual_type", "flowchart"),
            )
            result = self.generate_visual(
                text_content=item.get("text_content", ""),
                visual_type=item.get("visual_type", "flowchart"),
                style=item.get("style", "professional"),
                color_mode=item.get("color_mode", "brand"),
                language=item.get("language", "en"),
                output_format=item.get("output_format", "png"),
                orientation=item.get("orientation", "landscape"),
                save_path=item.get("save_path"),
            )
            results.append(result)
        return results

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def get_cache_stats(self) -> dict:
        """Return statistics about the on-disk visual cache.

        Returns:
            dict with keys: cached_visuals, total_size_bytes,
            total_size_mb, cache_dir.
        """
        cached_files = (
            list(self.cache_dir.glob("*.png"))
            + list(self.cache_dir.glob("*.svg"))
            + list(self.cache_dir.glob("*.pptx"))
        )
        total_size = sum(f.stat().st_size for f in cached_files)
        return {
            "cached_visuals": len(cached_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
        }

    def clear_cache(self) -> int:
        """Remove all files from the visual cache.

        Returns:
            The number of files deleted.
        """
        count = 0
        for f in self.cache_dir.iterdir():
            if f.is_file():
                f.unlink()
                count += 1
        logger.info("Cleared %d files from napkin visual cache", count)
        return count

    def list_cached_visuals(self) -> list[dict]:
        """List all cached visuals with their metadata.

        Returns:
            A list of metadata dicts, each augmented with ``file_path``
            and ``exists`` keys.
        """
        visuals: list[dict] = []
        for meta_file in sorted(self.cache_dir.glob("*.json")):
            try:
                meta = json.loads(meta_file.read_text())
                fmt = meta.get("format", "png")
                visual_file = meta_file.with_suffix(f".{fmt}")
                meta["file_path"] = str(visual_file)
                meta["exists"] = visual_file.exists()
                visuals.append(meta)
            except (json.JSONDecodeError, OSError):
                continue
        return visuals

    # ------------------------------------------------------------------
    # Informational helpers
    # ------------------------------------------------------------------

    def get_visual_types(self) -> dict:
        """Return the full ``VISUAL_TYPES`` catalogue.

        Useful for presenting the user with available options.
        """
        return dict(VISUAL_TYPES)

    def get_color_modes(self) -> dict:
        """Return the ``COLOR_MODES`` catalogue."""
        return dict(COLOR_MODES)

    def get_brand_colors(self) -> dict:
        """Return the currently loaded brand colour palette.

        If no brand colours are configured, returns an empty dict.
        """
        return dict(self._brand_colors)

    def get_output_formats(self) -> list[str]:
        """Return supported output format strings."""
        return list(OUTPUT_FORMATS)

    def get_orientations(self) -> list[str]:
        """Return supported orientation strings."""
        return list(ORIENTATIONS)

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def reset_cache(self):
        """Reset the cached availability flag so the next access re-checks."""
        self._available = None

    def reload_brand_colors(self) -> dict:
        """Reload brand colours from disk and return them.

        Call this after updating ``brand_config.json`` so that subsequent
        ``color_mode="brand"`` requests pick up the new palette.
        """
        self._brand_colors = self._load_brand_colors()
        return dict(self._brand_colors)

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        token_hint = (
            f"{self.api_token[:6]}..." if len(self.api_token) > 6 else "unset"
        )
        return (
            f"NapkinClient(base_url={self.base_url!r}, "
            f"token={token_hint}, "
            f"cache_enabled={self.cache_enabled})"
        )
