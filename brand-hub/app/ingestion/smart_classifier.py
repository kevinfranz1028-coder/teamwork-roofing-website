"""
Brand Intelligence Content Hub - Smart Content Classifier

Uses Claude AI + file heuristics to automatically classify uploaded files
and URLs into the correct category with auto-generated tags and descriptions.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Claude model for classification
CLASSIFIER_MODEL = "claude-sonnet-4-20250514"

# File extension to broad category mapping (fast heuristic, before AI)
EXTENSION_HINTS = {
    # Images (likely logos or visuals)
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".svg": "image",
    ".ico": "image",
    ".webp": "image",
    ".bmp": "image",
    ".tiff": "image",
    ".tif": "image",
    # Documents
    ".pdf": "document",
    ".docx": "document",
    ".doc": "document",
    ".rtf": "document",
    ".odt": "document",
    # Presentations
    ".pptx": "presentation",
    ".ppt": "presentation",
    ".odp": "presentation",
    # Spreadsheets / Data
    ".xlsx": "spreadsheet",
    ".xls": "spreadsheet",
    ".csv": "data",
    ".tsv": "data",
    ".json": "data",
    # Text / HTML
    ".txt": "text",
    ".md": "text",
    ".markdown": "text",
    ".html": "document",
    ".htm": "document",
    ".xml": "data",
    # Fonts
    ".ttf": "font",
    ".otf": "font",
    ".woff": "font",
    ".woff2": "font",
    # Templates
    ".dotx": "template",
    ".potx": "template",
}

# Asset type mapping for Brand Repository
ASSET_TYPE_MAP = {
    "logo": "logo",
    "icon": "logo",
    "brand_mark": "logo",
    "font": "font",
    "typography": "font",
    "color_palette": "color",
    "style_guide": "collateral",
    "brand_guidelines": "collateral",
    "template": "template",
    "marketing_collateral": "collateral",
    "brochure": "collateral",
    "flyer": "collateral",
    "business_card": "collateral",
    "letterhead": "collateral",
    "social_media": "collateral",
    "banner": "collateral",
    "sample_content": "sample",
    "voice_sample": "sample",
}

# Content Library category mapping
CONTENT_CATEGORY_MAP = {
    "training_material": "training",
    "onboarding": "training",
    "course": "training",
    "curriculum": "training",
    "marketing_collateral": "marketing",
    "brochure": "marketing",
    "case_study": "marketing",
    "report": "report",
    "analytics": "report",
    "dashboard": "report",
    "policy": "reference",
    "procedure": "reference",
    "sop": "reference",
    "guideline": "reference",
    "reference_material": "reference",
    "presentation": "presentation",
    "pitch_deck": "presentation",
    "proposal": "proposal",
    "data_file": "data",
    "spreadsheet": "data",
    "photo": "visual",
    "infographic": "visual",
    "diagram": "visual",
    "other": "general",
}

# ---------------------------------------------------------------------------
# Optional dependency imports
# ---------------------------------------------------------------------------

try:
    from app.ingestion.pdf_parser import PDFParser
except ImportError:
    PDFParser = None  # type: ignore[assignment,misc]

try:
    from app.ingestion.docx_parser import DOCXParser
except ImportError:
    DOCXParser = None  # type: ignore[assignment,misc]

try:
    from app.ingestion.pptx_parser import PPTXParser
except ImportError:
    PPTXParser = None  # type: ignore[assignment,misc]

try:
    from app.ingestion.url_scraper import URLScraper
except ImportError:
    URLScraper = None  # type: ignore[assignment,misc]

try:
    from anthropic import Anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None  # type: ignore[assignment,misc]
    ANTHROPIC_AVAILABLE = False


# ---------------------------------------------------------------------------
# SmartClassifier
# ---------------------------------------------------------------------------


class SmartClassifier:
    """AI-powered content classifier for auto-organizing files and URLs.

    When an Anthropic API key is available the classifier delegates to Claude
    for high-accuracy classification.  Otherwise it falls back to a
    deterministic heuristic based on file extension and filename keywords.
    """

    def __init__(self) -> None:
        self.client = None
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if api_key and ANTHROPIC_AVAILABLE:
            try:
                self.client = Anthropic(api_key=api_key)
            except Exception:
                logger.debug("Could not initialise Anthropic client")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify_file(self, file_path: str) -> dict[str, Any]:
        """Classify a file and return structured metadata.

        Returns a dict with the following keys:

        - asset_type      -- str  (logo/font/color/template/collateral/sample)
        - content_type    -- str  (training/marketing/report/reference/
                                   presentation/data/visual/general)
        - category        -- str  (detailed sub-category)
        - tags            -- list[str] (auto-generated tags)
        - description     -- str  (auto-generated description)
        - confidence      -- float (0.0-1.0)
        - extracted_text  -- str  (preview, first 500 chars of content)
        - metadata        -- dict (additional file metadata)
        """
        path = Path(file_path)
        if not path.exists():
            return self._error_result(f"File not found: {file_path}")

        ext = path.suffix.lower()
        filename = path.name
        file_size = path.stat().st_size
        ext_hint = EXTENSION_HINTS.get(ext, "unknown")

        # Extract content preview for AI analysis
        content_preview = ""
        file_metadata: dict[str, Any] = {
            "filename": filename,
            "extension": ext,
            "size_bytes": file_size,
        }

        try:
            if ext in (".pdf",) and PDFParser:
                result = PDFParser().parse(str(path))
                content_preview = result.get("text", "")[:3000]
                file_metadata.update(result.get("metadata", {}))

            elif ext in (".docx", ".doc") and DOCXParser:
                result = DOCXParser().parse(str(path))
                content_preview = result.get("text", "")[:3000]
                file_metadata.update(result.get("metadata", {}))

            elif ext in (".pptx", ".ppt") and PPTXParser:
                result = PPTXParser().parse(str(path))
                slides = result.get("slides", [])
                parts: list[str] = []
                for s in slides:
                    if s.get("title"):
                        parts.append(s["title"])
                    parts.extend(s.get("content", []))
                content_preview = "\n".join(parts)[:3000]
                file_metadata["slide_count"] = len(slides)

            elif ext in (".html", ".htm", ".xml"):
                raw_html = path.read_text(
                    encoding="utf-8", errors="replace"
                )
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(raw_html, "html.parser")
                    # Remove non-content elements
                    for tag in soup.find_all(["script", "style", "noscript", "iframe", "svg"]):
                        tag.decompose()
                    content_preview = soup.get_text(separator="\n", strip=True)[:3000]
                except ImportError:
                    # Fallback: strip HTML tags with regex
                    import re as _re
                    content_preview = _re.sub(r"<[^>]+>", " ", raw_html)
                    content_preview = _re.sub(r"\s+", " ", content_preview).strip()[:3000]

            elif ext in (".txt", ".md", ".csv", ".json", ".tsv"):
                content_preview = path.read_text(
                    encoding="utf-8", errors="replace"
                )[:3000]

            elif ext in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp"):
                content_preview = f"[Image file: {filename}, {file_size} bytes]"
                # Check if it is likely a logo by filename
                name_lower = filename.lower()
                if any(
                    kw in name_lower
                    for kw in ["logo", "icon", "mark", "brand", "emblem"]
                ):
                    file_metadata["likely_logo"] = True

            elif ext in (".ttf", ".otf", ".woff", ".woff2"):
                # Fonts can be classified deterministically
                content_preview = f"[Font file: {filename}]"
                return {
                    "asset_type": "font",
                    "content_type": "font",
                    "category": "typography",
                    "tags": ["font", "typography", filename.replace(ext, "")],
                    "description": f"Font file: {filename}",
                    "confidence": 0.95,
                    "extracted_text": "",
                    "metadata": file_metadata,
                }

            elif ext in (".xlsx", ".xls"):
                content_preview = f"[Spreadsheet: {filename}]"

        except Exception as exc:
            logger.warning("Failed to extract content from %s: %s", filename, exc)
            content_preview = f"[Could not extract content from {filename}]"

        # Use AI classification if available, otherwise fall back to heuristics
        if self.client and content_preview:
            return self._classify_with_ai(
                filename, ext, ext_hint, content_preview, file_metadata
            )
        return self._classify_with_heuristics(
            filename, ext, ext_hint, content_preview, file_metadata
        )

    def classify_url(self, url: str) -> dict[str, Any]:
        """Classify a URL by scraping and analysing its content."""
        if URLScraper is None:
            return self._error_result(
                "URL scraper not available. Install requests and beautifulsoup4."
            )

        try:
            scraper = URLScraper()
            result = scraper.scrape(url)

            title = result.get("title", "")
            text = result.get("text", "")[:3000]
            meta_desc = result.get("meta_description", "")
            headings = result.get("headings", [])

            content_preview = f"Title: {title}\n"
            if meta_desc:
                content_preview += f"Description: {meta_desc}\n"
            if headings:
                content_preview += (
                    "Headings: "
                    + ", ".join(h.get("text", "") for h in headings[:10])
                    + "\n"
                )
            content_preview += f"\nContent:\n{text}"

            file_metadata: dict[str, Any] = {
                "url": url,
                "title": title,
                "meta_description": meta_desc,
                "heading_count": len(headings),
            }

            if self.client:
                return self._classify_with_ai(
                    url, ".html", "webpage", content_preview, file_metadata
                )
            return {
                "asset_type": "collateral",
                "content_type": "reference",
                "category": "web_content",
                "tags": ["url", "web"],
                "description": title or url,
                "confidence": 0.5,
                "extracted_text": text[:500],
                "metadata": file_metadata,
            }
        except Exception as exc:
            return self._error_result(f"Failed to scrape URL: {exc}")

    def classify_bulk(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Classify multiple items.

        Each item dict must contain:
        - ``type`` -- ``"file"`` or ``"url"``
        - ``path`` -- file path or URL string
        """
        results: list[dict[str, Any]] = []
        for item in items:
            if item.get("type") == "url":
                results.append(self.classify_url(item["path"]))
            else:
                results.append(self.classify_file(item["path"]))
        return results

    # ------------------------------------------------------------------
    # AI classification (Claude)
    # ------------------------------------------------------------------

    def _classify_with_ai(
        self,
        name: str,
        ext: str,
        ext_hint: str,
        content_preview: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Use Claude to classify content."""
        try:
            system = (
                "You are a content classification expert for a brand intelligence "
                "platform. Analyze the provided file/content and classify it.\n\n"
                "Return a JSON object with EXACTLY these keys:\n"
                '- "asset_type": one of [logo, font, color, template, collateral, sample]\n'
                '- "content_type": one of [training, marketing, report, reference, '
                "presentation, proposal, data, visual, general]\n"
                '- "category": a specific sub-category (e.g., "brand_guidelines", '
                '"case_study", "onboarding_deck")\n'
                '- "tags": array of 3-8 relevant tags\n'
                '- "description": a 1-2 sentence description of what this content is\n'
                '- "confidence": float 0.0-1.0 indicating classification confidence\n\n'
                "Return ONLY the JSON object, no markdown fences."
            )

            user_msg = (
                f"Classify this content:\n"
                f"Filename/Source: {name}\n"
                f"File type: {ext} ({ext_hint})\n"
                f"Metadata: {json.dumps(metadata, default=str)}\n\n"
                f"Content preview:\n{content_preview[:2500]}"
            )

            response = self.client.messages.create(
                model=CLASSIFIER_MODEL,
                max_tokens=500,
                system=system,
                messages=[{"role": "user", "content": user_msg}],
            )

            raw = response.content[0].text.strip()

            # Strip markdown fences if the model included them
            if raw.startswith("```"):
                first_nl = raw.find("\n")
                if first_nl != -1:
                    raw = raw[first_nl + 1:]
                if raw.rstrip().endswith("```"):
                    raw = raw.rstrip()[:-3].rstrip()

            result: dict[str, Any] = json.loads(raw)
            result["extracted_text"] = content_preview[:500]
            result["metadata"] = metadata

            # Normalise asset_type to the canonical set
            at = result.get("asset_type", "collateral")
            if at not in ("logo", "font", "color", "template", "collateral", "sample"):
                result["asset_type"] = ASSET_TYPE_MAP.get(at, at)

            return result

        except Exception as exc:
            logger.warning("AI classification failed for %s: %s", name, exc)
            return self._classify_with_heuristics(
                name, ext, ext_hint, content_preview, metadata
            )

    # ------------------------------------------------------------------
    # Heuristic fallback
    # ------------------------------------------------------------------

    def _classify_with_heuristics(
        self,
        name: str,
        ext: str,
        ext_hint: str,
        content_preview: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Fallback heuristic classification when AI is unavailable."""
        name_lower = name.lower()

        # --- Determine asset_type ---
        if ext_hint == "font":
            asset_type = "font"
        elif ext_hint == "image":
            if any(
                kw in name_lower
                for kw in ["logo", "icon", "mark", "brand", "emblem"]
            ):
                asset_type = "logo"
            else:
                asset_type = "collateral"
        elif ext_hint == "presentation" or ext in (".pptx", ".ppt"):
            asset_type = "template" if "template" in name_lower else "collateral"
        elif ext_hint in ("document", "text"):
            if any(
                kw in name_lower for kw in ["guideline", "brand", "style"]
            ):
                asset_type = "collateral"
            elif "template" in name_lower:
                asset_type = "template"
            else:
                asset_type = "sample"
        else:
            asset_type = "collateral"

        # --- Determine content_type ---
        content_type = "general"
        if ext_hint == "presentation":
            content_type = "presentation"
        elif ext_hint in ("spreadsheet", "data"):
            content_type = "data"
        elif ext_hint == "image":
            content_type = "visual"
        elif any(kw in name_lower for kw in ["train", "onboard", "course", "learn"]):
            content_type = "training"
        elif any(
            kw in name_lower for kw in ["report", "analytic", "metric", "dashboard"]
        ):
            content_type = "report"
        elif any(
            kw in name_lower for kw in ["market", "brochure", "flyer", "campaign"]
        ):
            content_type = "marketing"
        elif any(
            kw in name_lower
            for kw in ["guide", "policy", "sop", "procedure", "reference"]
        ):
            content_type = "reference"

        # --- Generate tags from filename ---
        tags: list[str] = [ext.lstrip(".")]
        name_parts = Path(name).stem.replace("-", " ").replace("_", " ").split()
        tags.extend([p.lower() for p in name_parts if len(p) > 2][:5])

        return {
            "asset_type": asset_type,
            "content_type": content_type,
            "category": f"{ext_hint}_{content_type}",
            "tags": tags,
            "description": f"{name} ({ext_hint})",
            "confidence": 0.4,
            "extracted_text": content_preview[:500] if content_preview else "",
            "metadata": metadata,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _error_result(message: str) -> dict[str, Any]:
        """Return a minimal result dict indicating an error."""
        return {
            "asset_type": "collateral",
            "content_type": "general",
            "category": "unknown",
            "tags": [],
            "description": message,
            "confidence": 0.0,
            "extracted_text": "",
            "metadata": {},
            "error": message,
        }
