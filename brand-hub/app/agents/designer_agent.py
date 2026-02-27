"""
Brand Intelligence Content Hub - Designer Agent

Thin coordinator that takes written content (from WriterAgent) and
optional visual assets, then delegates to the existing presentation
or document generators to produce the final file.

Usage:
    from app.agents.designer_agent import DesignerAgent

    agent = DesignerAgent()
    result = agent.design(
        written_content={"slides": [...], "title": "My Deck"},
        content_type="presentation",
        title="My Deck",
    )
    print(result["file_path"])
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from app.config import BRAND_ASSETS_DIR

logger = logging.getLogger(__name__)


class DesignerAgent:
    """Merges visual assets into written content and delegates to generators."""

    def __init__(self, brand_config: dict | None = None) -> None:
        self.brand_config: dict = brand_config or self._load_brand_config()

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
    # Public API
    # ------------------------------------------------------------------

    def design(
        self,
        written_content: dict,
        content_type: str,
        doc_type: str = "",
        title: str = "",
        visual_assets: list[dict] | None = None,
    ) -> dict:
        """Build the final file from written content + optional visuals.

        Args:
            written_content: Structured JSON from WriterAgent.
            content_type: ``"presentation"`` or ``"document"``.
            doc_type: Document template type (documents only).
            title: Output title.
            visual_assets: Optional list of visual asset dicts from
                VisualPipeline, each with at least ``file_path`` and
                optionally ``slide_index``.

        Returns:
            Dict with ``file_path``, ``format``, and ``title``.
        """
        if content_type == "presentation":
            return self._build_presentation(written_content, title, visual_assets)
        else:
            return self._build_document(written_content, doc_type, title)

    # ------------------------------------------------------------------
    # Presentation pipeline
    # ------------------------------------------------------------------

    def _build_presentation(
        self,
        written_content: dict,
        title: str,
        visual_assets: list[dict] | None,
    ) -> dict:
        from app.generators.presentation_gen import BrandedPresentationGenerator

        slides = written_content.get("slides", [])
        title = title or written_content.get("title", "Presentation")

        # Merge visual assets into matching slides
        if visual_assets:
            self._merge_visuals_into_slides(slides, visual_assets)

        gen = BrandedPresentationGenerator(brand_config=self.brand_config)
        file_path = gen.generate(slides_data=slides, title=title)

        logger.info("Presentation generated: %s", file_path)
        return {"file_path": file_path, "format": "pptx", "title": title}

    @staticmethod
    def _merge_visuals_into_slides(
        slides: list[dict],
        visual_assets: list[dict],
    ) -> None:
        """Inject image paths from visual assets into matching slides."""
        for asset in visual_assets:
            file_path = asset.get("file_path", "")
            if not file_path:
                continue

            # Match by slide_index if available
            slide_idx = asset.get("slide_index")
            if slide_idx is not None and 0 <= slide_idx < len(slides):
                slides[slide_idx]["image_path"] = file_path
                continue

            # Match by description similarity to slide title (simple keyword match)
            desc = (asset.get("description", "") or "").lower()
            if desc:
                for slide in slides:
                    slide_title = (slide.get("title", "") or "").lower()
                    if not slide.get("image_path") and slide_title:
                        # Check for word overlap
                        desc_words = set(desc.split())
                        title_words = set(slide_title.split())
                        if desc_words & title_words:
                            slide["image_path"] = file_path
                            break

    # ------------------------------------------------------------------
    # Document pipeline
    # ------------------------------------------------------------------

    def _build_document(
        self,
        written_content: dict,
        doc_type: str,
        title: str,
    ) -> dict:
        from app.generators.document_gen import BrandedDocumentGenerator

        title = title or written_content.get("title", "Document")

        gen = BrandedDocumentGenerator(brand_config=self.brand_config)
        file_path = gen.generate(
            content=written_content,
            doc_type=doc_type,
            title=title,
        )

        logger.info("Document generated: %s", file_path)
        return {"file_path": file_path, "format": "docx", "title": title}
