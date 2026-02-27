"""
Brand Intelligence Content Hub - Visual Agent

Routes visual generation requests to the best backend:
- **Diagrams** (flowchart, mind_map, timeline, org_chart, process,
  infographic, comparison) → Napkin AI
- **Custom images** (hero_image, illustration, background, icon_set)
  → DALL-E 3 via OpenAIClient
- **Stock photos** (stock_photo, team_photo, office_photo)
  → Pexels API

Auto-detects visual type from the request text when not specified.
Injects brand colours into DALL-E prompts for consistency.

Usage:
    from app.agents.visual_agent import VisualAgent

    agent = VisualAgent()
    result = agent.generate("A hero image for sales training", visual_type="hero_image")
    print(result["file_path"])  # output/visuals/dalle_20260226_143022.png
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.config import BRAND_ASSETS_DIR, VISUALS_DIR

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Visual type routing tables
# ---------------------------------------------------------------------------

# Types handled by Napkin AI (structured diagrams)
NAPKIN_TYPES = {
    "flowchart",
    "mind_map",
    "timeline",
    "org_chart",
    "process_diagram",
    "process",
    "infographic",
    "comparison_chart",
    "comparison",
}

# Types handled by DALL-E 3 (custom AI-generated images)
DALLE_TYPES = {
    "hero_image",
    "illustration",
    "background",
    "icon_set",
}

# Types handled by Pexels (stock photography)
PEXELS_TYPES = {
    "stock_photo",
    "team_photo",
    "office_photo",
}

ALL_VISUAL_TYPES = NAPKIN_TYPES | DALLE_TYPES | PEXELS_TYPES

# ---------------------------------------------------------------------------
# Keyword patterns for auto-detection
# ---------------------------------------------------------------------------

_DETECTION_RULES: list[tuple[list[str], str]] = [
    # Napkin types
    (["flowchart", "flow chart", "decision tree", "workflow"], "flowchart"),
    (["mind map", "mindmap", "brainstorm"], "mind_map"),
    (["timeline", "roadmap", "milestones", "chronolog"], "timeline"),
    (["org chart", "organization chart", "hierarchy", "reporting structure"], "org_chart"),
    (["process diagram", "process flow", "step-by-step", "sop diagram"], "process_diagram"),
    (["infographic", "data visual", "statistics visual", "metrics visual"], "infographic"),
    (["comparison", "compare", "versus", "vs ", "pros and cons"], "comparison_chart"),
    # DALL-E types
    (["hero image", "banner image", "cover image", "header image"], "hero_image"),
    (["illustration", "artistic", "conceptual art", "creative visual"], "illustration"),
    (["background", "wallpaper", "backdrop"], "background"),
    (["icon set", "icons", "icon collection"], "icon_set"),
    # Pexels types
    (["stock photo", "photograph", "real photo", "actual photo"], "stock_photo"),
    (["team photo", "people photo", "group photo", "employees"], "team_photo"),
    (["office photo", "workspace", "call center", "work environment"], "office_photo"),
]

# DALL-E size mapping based on visual purpose
DALLE_SIZE_MAP = {
    "hero_image": "1792x1024",     # Wide/landscape for banners
    "illustration": "1024x1024",   # Square for general use
    "background": "1792x1024",     # Wide for slides
    "icon_set": "1024x1024",       # Square
}


class VisualAgent:
    """Intelligent router for visual generation across multiple backends."""

    def __init__(self, brand_config: dict | None = None) -> None:
        self.brand_config: dict = brand_config or self._load_brand_config()
        self._openai_client = None
        self._napkin_client = None

        VISUALS_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Brand config
    # ------------------------------------------------------------------

    @staticmethod
    def _load_brand_config() -> dict:
        config_path = BRAND_ASSETS_DIR / "brand_config.json"
        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not load brand config: %s", exc)
        return {}

    # ------------------------------------------------------------------
    # Lazy backend clients
    # ------------------------------------------------------------------

    def _get_openai_client(self):
        if self._openai_client is None:
            from app.integrations.openai_client import OpenAIClient
            self._openai_client = OpenAIClient()
        return self._openai_client

    def _get_napkin_client(self):
        if self._napkin_client is None:
            from app.integrations.napkin_client import NapkinClient
            self._napkin_client = NapkinClient()
        return self._napkin_client

    # ------------------------------------------------------------------
    # Visual type detection
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_visual_type(request: str) -> str:
        """Auto-detect the visual type from natural-language request text.

        Returns the best matching visual type string, or ``"illustration"``
        as a general-purpose default.
        """
        req_lower = request.lower()

        for keywords, vtype in _DETECTION_RULES:
            for kw in keywords:
                if kw in req_lower:
                    return vtype

        # Default to illustration (DALL-E) for unmatched requests
        return "illustration"

    @staticmethod
    def route_for_type(visual_type: str) -> str:
        """Return the backend name for a visual type.

        Returns:
            ``"napkin"``, ``"dalle"``, ``"pexels"``, or ``"dalle"`` as
            fallback for unknown types.
        """
        if visual_type in NAPKIN_TYPES:
            return "napkin"
        if visual_type in DALLE_TYPES:
            return "dalle"
        if visual_type in PEXELS_TYPES:
            return "pexels"
        return "dalle"  # default fallback

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        request: str,
        visual_type: str | None = None,
        output_format: str = "png",
        size: str | None = None,
        quality: str = "standard",
        style: str = "natural",
    ) -> dict:
        """Generate a visual, routing to the appropriate backend.

        Args:
            request: Natural-language description of the visual.
            visual_type: Explicit visual type.  Auto-detected when *None*.
            output_format: Output format (``png``, ``svg``, ``ppt``).
            size: DALL-E size override (e.g. ``1024x1024``).
            quality: DALL-E quality (``standard`` or ``hd``).
            style: DALL-E style (``natural`` or ``vivid``).

        Returns:
            Dict with ``success``, ``file_path``, ``visual_type``,
            ``method`` (``napkin``/``dalle``/``pexels``/``placeholder``),
            ``error``, and backend-specific metadata.
        """
        if not request or not request.strip():
            return {
                "success": False,
                "file_path": None,
                "visual_type": visual_type or "unknown",
                "method": None,
                "error": "Request is empty",
            }

        # Detect type if not provided
        if not visual_type or visual_type == "auto":
            visual_type = self._detect_visual_type(request)

        backend = self.route_for_type(visual_type)
        logger.info(
            "Visual request routed: type=%s, backend=%s", visual_type, backend
        )

        if backend == "napkin":
            return self._generate_napkin(request, visual_type, output_format)
        elif backend == "dalle":
            return self._generate_dalle(
                request, visual_type, size, quality, style
            )
        elif backend == "pexels":
            return self._generate_pexels(request, visual_type)
        else:
            return {
                "success": False,
                "file_path": None,
                "visual_type": visual_type,
                "method": None,
                "error": f"No backend available for visual type: {visual_type}",
            }

    # ------------------------------------------------------------------
    # Napkin AI backend
    # ------------------------------------------------------------------

    def _generate_napkin(
        self,
        description: str,
        visual_type: str,
        output_format: str,
    ) -> dict:
        """Route to Napkin AI for diagram/infographic generation."""
        try:
            napkin = self._get_napkin_client()

            # Normalise type names to Napkin's catalogue
            napkin_type_map = {
                "process": "process_diagram",
                "comparison": "comparison_chart",
            }
            mapped_type = napkin_type_map.get(visual_type, visual_type)

            result = napkin.generate_visual(
                text_content=description,
                visual_type=mapped_type,
                style="professional",
                color_mode="brand",
                output_format=output_format,
            )

            return {
                "success": result.get("success", False),
                "file_path": result.get("file_path"),
                "visual_type": visual_type,
                "method": "napkin",
                "error": result.get("error"),
                "cache_hit": result.get("cache_hit", False),
            }

        except Exception as exc:
            logger.error("Napkin generation failed: %s", exc)
            return {
                "success": False,
                "file_path": None,
                "visual_type": visual_type,
                "method": "napkin",
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # DALL-E 3 backend
    # ------------------------------------------------------------------

    def _generate_dalle(
        self,
        prompt: str,
        visual_type: str,
        size: str | None,
        quality: str,
        style: str,
    ) -> dict:
        """Route to DALL-E 3 for custom image generation."""
        from app.integrations.openai_client import OpenAIClient

        if not OpenAIClient.is_available():
            logger.warning("DALL-E unavailable (no OPENAI_API_KEY); using placeholder")
            return self._create_placeholder(prompt, visual_type, "dalle")

        try:
            client = self._get_openai_client()

            # Choose size based on visual type if not explicitly set
            if size is None:
                size = DALLE_SIZE_MAP.get(visual_type, "1024x1024")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = str(VISUALS_DIR / f"dalle_{visual_type}_{timestamp}.png")

            result = client.generate_image(
                prompt=prompt,
                size=size,
                quality=quality,
                style=style,
                save_path=save_path,
                inject_brand_colors=True,
            )

            return {
                "success": result.get("success", False),
                "file_path": result.get("file_path"),
                "visual_type": visual_type,
                "method": "dalle",
                "error": result.get("error"),
                "revised_prompt": result.get("revised_prompt"),
                "size": size,
                "quality": quality,
                "style": style,
            }

        except Exception as exc:
            logger.error("DALL-E generation failed: %s", exc)
            return {
                "success": False,
                "file_path": None,
                "visual_type": visual_type,
                "method": "dalle",
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Pexels backend
    # ------------------------------------------------------------------

    def _generate_pexels(
        self,
        query: str,
        visual_type: str,
    ) -> dict:
        """Route to Pexels API for stock photography."""
        pexels_key = os.environ.get("PEXELS_API_KEY", "")
        if not pexels_key:
            logger.warning("Pexels unavailable (no PEXELS_API_KEY); using placeholder")
            return self._create_placeholder(query, visual_type, "pexels")

        try:
            import requests as req

            # Search Pexels for matching photos
            headers = {"Authorization": pexels_key}
            search_url = "https://api.pexels.com/v1/search"
            params = {
                "query": query,
                "per_page": 1,
                "orientation": "landscape",
            }

            resp = req.get(search_url, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            photos = data.get("photos", [])
            if not photos:
                return {
                    "success": False,
                    "file_path": None,
                    "visual_type": visual_type,
                    "method": "pexels",
                    "error": f"No Pexels results for: {query[:60]}",
                }

            photo = photos[0]
            image_url = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("large", "")
            photographer = photo.get("photographer", "Unknown")

            if not image_url:
                return {
                    "success": False,
                    "file_path": None,
                    "visual_type": visual_type,
                    "method": "pexels",
                    "error": "No image URL in Pexels response",
                }

            # Download the photo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = str(VISUALS_DIR / f"pexels_{visual_type}_{timestamp}.jpg")

            img_resp = req.get(image_url, timeout=30)
            img_resp.raise_for_status()
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            Path(save_path).write_bytes(img_resp.content)

            logger.info("Pexels photo downloaded: %s (by %s)", save_path, photographer)
            return {
                "success": True,
                "file_path": save_path,
                "visual_type": visual_type,
                "method": "pexels",
                "error": None,
                "photographer": photographer,
                "pexels_url": photo.get("url", ""),
            }

        except Exception as exc:
            logger.error("Pexels search/download failed: %s", exc)
            return {
                "success": False,
                "file_path": None,
                "visual_type": visual_type,
                "method": "pexels",
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Placeholder fallback
    # ------------------------------------------------------------------

    def _create_placeholder(
        self,
        description: str,
        visual_type: str,
        intended_backend: str,
    ) -> dict:
        """Create a placeholder image when the intended backend is unavailable.

        Delegates to VisualPipeline's placeholder generator if available,
        otherwise returns a simple error dict.
        """
        try:
            from app.generators.visual_gen import VisualPipeline

            pipeline = VisualPipeline(brand_config=self.brand_config)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = str(
                VISUALS_DIR / f"placeholder_{visual_type}_{timestamp}.png"
            )
            result = pipeline._create_placeholder(
                description=f"[{intended_backend.upper()} unavailable] {description}",
                visual_type=visual_type,
                save_path=save_path,
            )
            result["method"] = "placeholder"
            result["intended_backend"] = intended_backend
            return result

        except Exception as exc:
            logger.warning("Placeholder creation failed: %s", exc)
            return {
                "success": False,
                "file_path": None,
                "visual_type": visual_type,
                "method": "placeholder",
                "error": f"{intended_backend} unavailable and placeholder failed: {exc}",
            }

    # ------------------------------------------------------------------
    # Bulk generation for slides
    # ------------------------------------------------------------------

    def generate_for_slides(
        self,
        slides: list[dict],
        default_type: str | None = None,
    ) -> list[dict]:
        """Generate visuals for slides that have a ``suggested_visual`` field.

        Args:
            slides: Slide dicts from the presentation pipeline.
            default_type: Default visual type when not specified per slide.

        Returns:
            List of result dicts, one per visual generated, each with
            ``slide_index`` attached.
        """
        results: list[dict] = []
        for idx, slide in enumerate(slides):
            suggested = slide.get("suggested_visual")
            if not suggested:
                continue

            if isinstance(suggested, dict):
                visual_type = suggested.get("type", default_type or "illustration")
                description = suggested.get("description", slide.get("title", ""))
            else:
                visual_type = default_type
                description = str(suggested)

            result = self.generate(
                request=description,
                visual_type=visual_type,
            )
            result["slide_index"] = idx
            result["slide_title"] = slide.get("title", "")
            results.append(result)

            # Attach file path back to the slide for downstream use
            if result.get("success") and result.get("file_path"):
                slide["image_path"] = result["file_path"]

        return results

    # ------------------------------------------------------------------
    # Informational
    # ------------------------------------------------------------------

    @staticmethod
    def get_supported_types() -> dict[str, list[str]]:
        """Return visual types grouped by backend."""
        return {
            "napkin": sorted(NAPKIN_TYPES),
            "dalle": sorted(DALLE_TYPES),
            "pexels": sorted(PEXELS_TYPES),
        }
