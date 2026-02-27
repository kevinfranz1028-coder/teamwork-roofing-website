"""
Brand Intelligence Content Hub - Visual Generation Pipeline

Orchestrates visual content creation by analyzing content for visual
opportunities, generating descriptions via Claude, and producing
visuals through Napkin AI. Integrates with presentation and document generators.
"""

import json
import logging
import os
import re
import textwrap
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from anthropic import Anthropic

from app.config import BRAND_ASSETS_DIR, VISUALS_DIR, CACHE_DIR
from app.integrations.napkin_client import NapkinClient, VISUAL_TYPES

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Priority weights for sorting visual opportunities
PRIORITY_WEIGHTS = {"high": 3, "medium": 2, "low": 1}

# Default brand colours used when brand_config.json is absent
DEFAULT_BRAND_COLORS = {
    "primary": "#0066CC",
    "secondary": "#004499",
    "accent": "#FF6600",
    "background": "#FFFFFF",
    "text": "#333333",
}


# =========================================================================
# VisualContentAnalyzer
# =========================================================================

class VisualContentAnalyzer:
    """Uses Claude to analyze content and suggest where visuals would be effective.

    The analyzer inspects textual content, identifies locations that would
    benefit from a visual element, recommends an appropriate visual type
    from Napkin AI's repertoire, and generates detailed text descriptions
    optimized for Napkin AI rendering.
    """

    def __init__(self) -> None:
        """Initialise the Anthropic client."""
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def analyze_content_for_visuals(
        self,
        content: str,
        content_type: str = "general",
    ) -> list[dict]:
        """Identify opportunities for visual elements in the given content.

        Parameters
        ----------
        content:
            The textual content to analyze.
        content_type:
            One of ``general``, ``presentation``, ``training``, ``report``.

        Returns
        -------
        list[dict]
            Each dict contains:
            - ``location`` (str): e.g. "after paragraph 2"
            - ``visual_type`` (str): one of the VISUAL_TYPES keys
            - ``description`` (str): what the visual should convey
            - ``title`` (str): suggested visual title
            - ``priority`` (str): ``high``, ``medium``, or ``low``
        """
        prompt = self._build_analysis_prompt(content, content_type)

        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text
            suggestions = self._parse_json_response(raw)

            if not isinstance(suggestions, list):
                logger.warning(
                    "Visual analysis returned non-list; wrapping: %s",
                    type(suggestions).__name__,
                )
                suggestions = suggestions.get("visuals", []) if isinstance(suggestions, dict) else []

            # Validate and normalise each suggestion
            validated: list[dict] = []
            for item in suggestions:
                if not isinstance(item, dict):
                    continue
                entry = {
                    "location": str(item.get("location", "unspecified")),
                    "visual_type": str(item.get("visual_type", "flowchart")),
                    "description": str(item.get("description", "")),
                    "title": str(item.get("title", "Untitled Visual")),
                    "priority": str(item.get("priority", "medium")).lower(),
                }
                # Ensure visual_type is a known type; fall back to flowchart
                if entry["visual_type"] not in VISUAL_TYPES:
                    entry["visual_type"] = "flowchart"
                if entry["priority"] not in PRIORITY_WEIGHTS:
                    entry["priority"] = "medium"
                validated.append(entry)

            # Sort by priority descending
            validated.sort(
                key=lambda v: PRIORITY_WEIGHTS.get(v["priority"], 0),
                reverse=True,
            )
            return validated

        except Exception as exc:
            logger.error("Visual content analysis failed: %s", exc)
            return []

    def generate_visual_description(
        self,
        content: str,
        visual_type: str,
        context: str = "",
    ) -> str:
        """Generate a detailed text description optimized for Napkin AI.

        The description is structured with clear hierarchy, labelled
        relationships, and explicit data points so that Napkin AI can
        render a professional visual.

        Parameters
        ----------
        content:
            Source material the visual should be based on.
        visual_type:
            Target visual type (e.g. ``flowchart``, ``comparison_table``).
        context:
            Optional surrounding context to improve relevance.

        Returns
        -------
        str
            A structured natural-language description ready for Napkin AI.
        """
        prompt = self._build_description_prompt(content, visual_type, context)

        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            description = response.content[0].text.strip()

            # Strip any surrounding markdown fences the model may add
            description = re.sub(
                r"^```(?:text|markdown)?\s*\n?", "", description,
            )
            description = re.sub(r"\n?```\s*$", "", description)

            return description

        except Exception as exc:
            logger.error("Visual description generation failed: %s", exc)
            return f"[Visual description unavailable: {exc}]"

    def enhance_slide_visuals(self, slides_data: list[dict]) -> list[dict]:
        """Enhance presentation slides that have a ``suggested_visual`` field.

        For each slide containing ``suggested_visual``, a detailed Napkin AI-
        ready description is generated via Claude and stored in a new
        ``visual_description`` key on the slide dict.

        Parameters
        ----------
        slides_data:
            List of slide dictionaries from the presentation pipeline.

        Returns
        -------
        list[dict]
            The same list with ``visual_description`` added where applicable.
        """
        for idx, slide in enumerate(slides_data):
            suggested = slide.get("suggested_visual")
            if not suggested:
                continue

            visual_type = suggested if isinstance(suggested, str) else suggested.get("type", "flowchart")
            slide_content = slide.get("body", "") or slide.get("title", "")
            slide_context = (
                f"Slide {idx + 1} of a presentation. "
                f"Title: {slide.get('title', 'Untitled')}. "
                f"Layout: {slide.get('layout', 'content')}."
            )

            description = self.generate_visual_description(
                content=slide_content,
                visual_type=visual_type,
                context=slide_context,
            )
            slide["visual_description"] = description
            slide["visual_type"] = visual_type

            logger.info(
                "Enhanced slide %d with %s visual description",
                idx + 1,
                visual_type,
            )

        return slides_data

    def enhance_document_visuals(
        self,
        content: dict,
        doc_type: str,
    ) -> dict:
        """Analyze document content and attach visual suggestions.

        Parameters
        ----------
        content:
            Document content dictionary (title, sections, body, etc.).
        doc_type:
            Document template type (e.g. ``weekly_report``, ``case_study``).

        Returns
        -------
        dict
            The original content dict with a ``visual_suggestions`` key
            containing a list of visual opportunity dicts.
        """
        # Flatten document content into a text block for analysis
        text_parts: list[str] = []
        if "title" in content:
            text_parts.append(f"Title: {content['title']}")
        if "executive_summary" in content:
            text_parts.append(f"Executive Summary: {content['executive_summary']}")
        for section in content.get("sections", []):
            if isinstance(section, dict):
                text_parts.append(
                    f"Section: {section.get('heading', '')}\n{section.get('body', '')}"
                )
            elif isinstance(section, str):
                text_parts.append(section)
        if "body" in content:
            text_parts.append(content["body"])

        flat_text = "\n\n".join(text_parts)

        content_type_map = {
            "weekly_report": "report",
            "monthly_report": "report",
            "case_study": "general",
            "job_aid": "training",
            "training_manual": "training",
            "sop": "training",
            "onboarding_guide": "training",
        }
        mapped_type = content_type_map.get(doc_type, "general")

        suggestions = self.analyze_content_for_visuals(flat_text, mapped_type)
        content["visual_suggestions"] = suggestions

        logger.info(
            "Found %d visual opportunities in %s document",
            len(suggestions),
            doc_type,
        )
        return content

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_analysis_prompt(self, content: str, content_type: str) -> str:
        """Build the Claude prompt for identifying visual opportunities."""

        visual_types_desc = "\n".join(
            f"  - **{key}**: {meta.get('description', key)}"
            for key, meta in VISUAL_TYPES.items()
        )

        content_type_guidance = {
            "presentation": (
                "This content is for a slide presentation. Favour visuals that "
                "are bold, simple, and scannable at a glance. Diagrams and "
                "comparison tables work well. Avoid text-heavy visuals."
            ),
            "training": (
                "This content is for training material. Favour step-by-step "
                "flowcharts, process diagrams, checklists, and reference "
                "tables that aid learning and retention."
            ),
            "report": (
                "This content is for a business report. Favour data "
                "visualisations, trend charts, KPI dashboards, and summary "
                "tables that highlight metrics and insights."
            ),
            "general": (
                "This is general content. Suggest visuals wherever they would "
                "improve clarity, engagement, or information retention."
            ),
        }
        guidance = content_type_guidance.get(
            content_type,
            content_type_guidance["general"],
        )

        return f"""You are a visual content strategist. Analyze the following content and identify specific locations where visual elements would enhance comprehension, engagement, and professional impact.

CONTENT TYPE: {content_type}
GUIDANCE: {guidance}

AVAILABLE VISUAL TYPES:
{visual_types_desc}

CONTENT TO ANALYZE:
---
{content}
---

INSTRUCTIONS:
1. Read the content carefully and identify 2-6 locations where a visual would add clear value.
2. For each opportunity, specify:
   - "location": Where in the content the visual should appear (e.g. "after paragraph 1", "between sections 2 and 3", "within the introduction").
   - "visual_type": The most appropriate type from the list above.
   - "description": A concise explanation of what the visual should depict, including the key data points, relationships, or concepts.
   - "title": A short, descriptive title for the visual.
   - "priority": "high" if the visual is essential for understanding, "medium" if it adds significant value, "low" if it is a nice-to-have enhancement.

3. Do NOT suggest visuals where they would be redundant or distracting.
4. Prioritise clarity and purpose over decoration.

Respond with a JSON array only (no surrounding text, no markdown fences). Example:
[
  {{
    "location": "after paragraph 2",
    "visual_type": "flowchart",
    "description": "A flowchart showing the three-stage approval process from submission through review to final sign-off.",
    "title": "Approval Workflow",
    "priority": "high"
  }}
]"""

    def _build_description_prompt(
        self,
        content: str,
        visual_type: str,
        context: str,
    ) -> str:
        """Build the Claude prompt for generating a Napkin AI description."""

        type_meta = VISUAL_TYPES.get(visual_type, {})
        type_name = type_meta.get("name", visual_type.replace("_", " ").title())
        type_desc = type_meta.get("description", "")

        context_block = f"\nADDITIONAL CONTEXT: {context}" if context else ""

        return f"""You are a visual content architect specializing in structured text descriptions for AI-powered visual generation tools.

TARGET VISUAL TYPE: {type_name}
TYPE DESCRIPTION: {type_desc}
{context_block}

SOURCE CONTENT:
---
{content}
---

TASK:
Create a detailed, structured text description that an AI visual generation tool (Napkin AI) can use to produce a professional {type_name}.

REQUIREMENTS FOR THE DESCRIPTION:
1. **Hierarchy**: Use clear headings, numbered lists, and indentation to establish information hierarchy.
2. **Relationships**: Explicitly state connections between elements (e.g. "A leads to B", "X is a subset of Y").
3. **Labels**: Include exact labels for all nodes, columns, rows, axes, or segments.
4. **Data**: If the content contains numbers or metrics, include them precisely.
5. **Flow direction**: For process diagrams, state the flow direction (left-to-right, top-to-bottom).
6. **Grouping**: Clearly indicate which elements belong together.
7. **Emphasis**: Note which elements should be visually emphasised.

OUTPUT FORMAT:
Return ONLY the structured description text. Do NOT include instructions to the tool or meta-commentary. The text itself should be self-contained and directly usable as input to Napkin AI.

Begin the description with a clear title line, then organise the content logically for the {type_name} format."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_json_response(self, raw: str) -> Any:
        """Parse JSON from a Claude response, handling markdown fences.

        Claude sometimes wraps JSON in ````json ... ``` `` blocks. This
        method strips those before parsing.
        """
        cleaned = raw.strip()

        # Remove markdown code fences
        fence_match = re.search(
            r"```(?:json)?\s*\n?(.*?)\n?\s*```",
            cleaned,
            re.DOTALL,
        )
        if fence_match:
            cleaned = fence_match.group(1).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Attempt to find a JSON array or object within the text
            for pattern in [r"\[.*\]", r"\{.*\}"]:
                match = re.search(pattern, cleaned, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(0))
                    except json.JSONDecodeError:
                        continue
            logger.warning("Could not parse JSON from Claude response")
            return []


# =========================================================================
# VisualPipeline
# =========================================================================

class VisualPipeline:
    """Main pipeline that orchestrates the full visual generation flow.

    Bridges content analysis (via Claude) with visual rendering (via
    Napkin AI), providing fallback placeholder generation when the
    Napkin service is unavailable.
    """

    def __init__(self, brand_config: Optional[dict] = None) -> None:
        """Initialise pipeline components.

        Parameters
        ----------
        brand_config:
            Brand configuration dict. If *None*, loads from
            ``brand_assets/brand_config.json``.
        """
        self.napkin = NapkinClient()
        self.analyzer = VisualContentAnalyzer()
        self.brand_config: dict = brand_config or self._load_brand_config()
        self.colors: dict[str, str] = self.brand_config.get(
            "colors", DEFAULT_BRAND_COLORS,
        )

        # Ensure output directory exists
        VISUALS_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def _load_brand_config(self) -> dict:
        """Load ``brand_assets/brand_config.json``, returning defaults on failure."""
        config_path = BRAND_ASSETS_DIR / "brand_config.json"
        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not load brand config: %s", exc)
        return {"colors": DEFAULT_BRAND_COLORS}

    # ------------------------------------------------------------------
    # Single visual generation
    # ------------------------------------------------------------------

    def generate_visual(
        self,
        description: str,
        visual_type: str = "flowchart",
        style: str = "professional",
        color_mode: str = "brand",
        output_format: str = "png",
        save_path: Optional[str] = None,
    ) -> dict:
        """Generate a single visual, falling back to a placeholder if needed.

        Parameters
        ----------
        description:
            Structured text description for the visual.
        visual_type:
            One of the VISUAL_TYPES keys (e.g. ``flowchart``).
        style:
            Napkin style preset (e.g. ``professional``, ``minimal``).
        color_mode:
            Colour mode (e.g. ``brand``, ``monochrome``).
        output_format:
            Output format (``png``, ``svg``, ``pdf``).
        save_path:
            Explicit save path. Auto-generated if *None*.

        Returns
        -------
        dict
            Keys: ``success``, ``file_path``, ``visual_type``, ``method``,
            ``error``.
        """
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{visual_type}_{timestamp}_{uuid4().hex[:8]}.{output_format}"
            save_path = str(VISUALS_DIR / filename)

        # Route DALL-E / Pexels types through VisualAgent when available
        try:
            from app.agents.visual_agent import VisualAgent, DALLE_TYPES, PEXELS_TYPES
            if visual_type in DALLE_TYPES or visual_type in PEXELS_TYPES:
                agent = VisualAgent(brand_config=self.brand_config)
                result = agent.generate(
                    request=description,
                    visual_type=visual_type,
                    output_format=output_format,
                )
                if result.get("success"):
                    return result
                logger.warning(
                    "VisualAgent failed for %s: %s — trying fallback",
                    visual_type, result.get("error"),
                )
        except ImportError:
            pass

        # Attempt Napkin AI first
        if self.napkin.available:
            try:
                result = self.napkin.generate_visual(
                    text_content=description,
                    visual_type=visual_type,
                    style=style,
                    color_mode=color_mode,
                    output_format=output_format,
                    save_path=save_path,
                )
                if result.get("success"):
                    return {
                        "success": True,
                        "file_path": result.get("file_path", save_path),
                        "visual_type": visual_type,
                        "method": "napkin",
                        "error": None,
                    }
                else:
                    logger.warning(
                        "Napkin generation failed: %s — falling back to placeholder",
                        result.get("error", "unknown error"),
                    )
            except Exception as exc:
                logger.warning(
                    "Napkin generation raised exception: %s — falling back to placeholder",
                    exc,
                )

        # Fallback: placeholder image
        return self._create_placeholder(description, visual_type, save_path)

    # ------------------------------------------------------------------
    # Content-driven generation
    # ------------------------------------------------------------------

    def generate_from_content(
        self,
        content: str,
        content_type: str = "general",
        output_format: str = "png",
    ) -> list[dict]:
        """Full pipeline: analyze -> describe -> generate visuals.

        Parameters
        ----------
        content:
            Raw textual content to analyze for visual opportunities.
        content_type:
            Content category (``general``, ``presentation``, ``training``,
            ``report``).
        output_format:
            Image format for all generated visuals.

        Returns
        -------
        list[dict]
            One result dict per visual generated, each containing the
            standard ``success``/``file_path``/``visual_type``/``method``
            keys plus ``title``, ``location``, and ``priority``.
        """
        logger.info(
            "Starting visual generation pipeline for %s content (%d chars)",
            content_type,
            len(content),
        )

        # Step 1: Analyze content for visual opportunities
        opportunities = self.analyzer.analyze_content_for_visuals(
            content, content_type,
        )
        if not opportunities:
            logger.info("No visual opportunities identified in content")
            return []

        logger.info(
            "Identified %d visual opportunities", len(opportunities),
        )

        # Step 2: Generate detailed descriptions and produce visuals
        results: list[dict] = []
        for opp in opportunities:
            description = self.analyzer.generate_visual_description(
                content=opp["description"],
                visual_type=opp["visual_type"],
                context=f"Title: {opp['title']}. Location: {opp['location']}.",
            )

            result = self.generate_visual(
                description=description,
                visual_type=opp["visual_type"],
                output_format=output_format,
            )
            result["title"] = opp["title"]
            result["location"] = opp["location"]
            result["priority"] = opp["priority"]
            results.append(result)

            logger.info(
                "Generated %s visual: %s (method=%s, success=%s)",
                opp["visual_type"],
                opp["title"],
                result.get("method"),
                result.get("success"),
            )

        return results

    # ------------------------------------------------------------------
    # Presentation integration
    # ------------------------------------------------------------------

    def generate_for_slides(
        self,
        slides_data: list[dict],
        output_format: str = "png",
    ) -> list[dict]:
        """Generate visuals for presentation slides.

        Processes each slide that has a ``suggested_visual`` field. The
        analyzer enhances the slides with detailed descriptions, then
        visuals are rendered and linked back to their slide index.

        Parameters
        ----------
        slides_data:
            List of slide dicts from the presentation pipeline.
        output_format:
            Image format (``png``, ``svg``, ``pdf``).

        Returns
        -------
        list[dict]
            One result dict per visual, each with ``slide_index`` and the
            standard visual result keys.
        """
        logger.info(
            "Generating visuals for %d slides", len(slides_data),
        )

        # Enhance slides with detailed visual descriptions
        enhanced = self.analyzer.enhance_slide_visuals(slides_data)

        results: list[dict] = []
        for idx, slide in enumerate(enhanced):
            visual_desc = slide.get("visual_description")
            if not visual_desc:
                continue

            visual_type = slide.get("visual_type", "flowchart")
            slide_title = slide.get("title", f"slide_{idx + 1}")
            safe_title = re.sub(r"[^\w\-]", "_", slide_title)[:40]

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"slide_{idx + 1}_{safe_title}_{timestamp}.{output_format}"
            save_path = str(VISUALS_DIR / filename)

            result = self.generate_visual(
                description=visual_desc,
                visual_type=visual_type,
                save_path=save_path,
                output_format=output_format,
            )
            result["slide_index"] = idx
            result["slide_title"] = slide.get("title", "")
            results.append(result)

            # Attach the file path back to the slide dict for downstream use
            if result.get("success"):
                slide["visual_path"] = result["file_path"]

            logger.info(
                "Slide %d visual: %s (method=%s)",
                idx + 1,
                visual_type,
                result.get("method"),
            )

        return results

    # ------------------------------------------------------------------
    # Document integration
    # ------------------------------------------------------------------

    def generate_for_document(
        self,
        content: dict,
        doc_type: str,
        output_format: str = "png",
    ) -> list[dict]:
        """Generate visuals for a document.

        Analyzes the document content for visual opportunities, then
        generates a visual for each suggestion.

        Parameters
        ----------
        content:
            Document content dictionary.
        doc_type:
            Document type identifier (e.g. ``weekly_report``).
        output_format:
            Image format for generated visuals.

        Returns
        -------
        list[dict]
            One result dict per visual with standard keys plus ``location``
            and ``title``.
        """
        logger.info("Generating visuals for %s document", doc_type)

        # Enhance the document content with visual suggestions
        enhanced = self.analyzer.enhance_document_visuals(content, doc_type)
        suggestions = enhanced.get("visual_suggestions", [])

        if not suggestions:
            logger.info("No visual suggestions for %s document", doc_type)
            return []

        results: list[dict] = []
        for suggestion in suggestions:
            description = self.analyzer.generate_visual_description(
                content=suggestion["description"],
                visual_type=suggestion["visual_type"],
                context=f"Document type: {doc_type}. Title: {suggestion.get('title', '')}.",
            )

            doc_title = content.get("title", doc_type)
            safe_title = re.sub(r"[^\w\-]", "_", doc_title)[:30]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = (
                f"doc_{safe_title}_{suggestion['visual_type']}"
                f"_{timestamp}_{uuid4().hex[:6]}.{output_format}"
            )
            save_path = str(VISUALS_DIR / filename)

            result = self.generate_visual(
                description=description,
                visual_type=suggestion["visual_type"],
                save_path=save_path,
                output_format=output_format,
            )
            result["title"] = suggestion.get("title", "")
            result["location"] = suggestion.get("location", "")
            result["priority"] = suggestion.get("priority", "medium")
            results.append(result)

        logger.info(
            "Generated %d visuals for %s document", len(results), doc_type,
        )
        return results

    # ------------------------------------------------------------------
    # Batch generation
    # ------------------------------------------------------------------

    def batch_generate(self, descriptions: list[dict]) -> list[dict]:
        """Generate multiple visuals from a batch of description dicts.

        Parameters
        ----------
        descriptions:
            Each dict should contain:
            - ``description`` (str): text description for the visual
            - ``visual_type`` (str, optional): defaults to ``flowchart``
            - ``style`` (str, optional): defaults to ``professional``
            - ``color_mode`` (str, optional): defaults to ``brand``
            - ``output_format`` (str, optional): defaults to ``png``

        Returns
        -------
        list[dict]
            One result dict per item with standard keys.
        """
        if not descriptions:
            return []

        logger.info("Batch generating %d visuals", len(descriptions))

        # If Napkin is available, try its native batch endpoint first
        if self.napkin.available:
            napkin_items = []
            for item in descriptions:
                napkin_items.append({
                    "text_content": item.get("description", ""),
                    "visual_type": item.get("visual_type", "flowchart"),
                    "style": item.get("style", "professional"),
                    "color_mode": item.get("color_mode", "brand"),
                    "output_format": item.get("output_format", "png"),
                })

            try:
                napkin_results = self.napkin.batch_generate(napkin_items)
                # Check if all succeeded — if any failed, fall through
                # to individual generation which includes placeholder fallback
                all_ok = all(r.get("success", False) for r in napkin_results)
                if all_ok:
                    results: list[dict] = []
                    for idx, nr in enumerate(napkin_results):
                        results.append({
                            "success": True,
                            "file_path": nr.get("file_path"),
                            "visual_type": descriptions[idx].get("visual_type", "flowchart"),
                            "method": "napkin",
                            "error": None,
                        })
                    return results
                logger.info("Some Napkin batch items failed — falling back to individual generation")
            except Exception as exc:
                logger.warning(
                    "Napkin batch generation failed: %s — falling back to individual generation",
                    exc,
                )

        # Fallback: generate individually (placeholder or retry Napkin)
        results = []
        for item in descriptions:
            result = self.generate_visual(
                description=item.get("description", ""),
                visual_type=item.get("visual_type", "flowchart"),
                style=item.get("style", "professional"),
                color_mode=item.get("color_mode", "brand"),
                output_format=item.get("output_format", "png"),
            )
            results.append(result)

        return results

    # ------------------------------------------------------------------
    # Placeholder generation
    # ------------------------------------------------------------------

    def _create_placeholder(
        self,
        description: str,
        visual_type: str,
        save_path: Optional[str] = None,
    ) -> dict:
        """Create a placeholder image when Napkin AI is unavailable.

        Uses Pillow to draw a simple 800x500 image with brand-coloured
        borders, the visual type label, wrapped description text, and a
        footer notice.

        Parameters
        ----------
        description:
            The visual description text to display in the body.
        visual_type:
            The intended visual type (displayed as a header).
        save_path:
            File path for the image. Auto-generated if *None*.

        Returns
        -------
        dict
            Standard result dict with ``method`` set to ``placeholder``.
        """
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"placeholder_{visual_type}_{timestamp}_{uuid4().hex[:8]}.png"
            save_path = str(VISUALS_DIR / filename)

        # Ensure parent directory exists
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            from PIL import Image, ImageDraw, ImageFont

            width, height = 800, 500

            # Parse brand colours
            primary_hex = self.colors.get("primary", "#0066CC").lstrip("#")
            bg_hex = self.colors.get("background", "#FFFFFF").lstrip("#")

            primary_rgb = tuple(
                int(primary_hex[i : i + 2], 16) for i in (0, 2, 4)
            )
            bg_rgb = tuple(int(bg_hex[i : i + 2], 16) for i in (0, 2, 4))

            # Create image with light gray background
            img = Image.new("RGB", (width, height), (245, 245, 245))
            draw = ImageDraw.Draw(img)

            # Brand-coloured border (4px)
            border_width = 4
            draw.rectangle(
                [0, 0, width - 1, height - 1],
                outline=primary_rgb,
                width=border_width,
            )

            # Header background bar
            header_h = 60
            draw.rectangle(
                [border_width, border_width, width - border_width - 1, header_h],
                fill=primary_rgb,
            )

            # Try to load a reasonable font; fall back to default
            try:
                title_font = ImageFont.truetype("Arial", 22)
                body_font = ImageFont.truetype("Arial", 14)
                footer_font = ImageFont.truetype("Arial", 12)
            except (OSError, IOError):
                try:
                    title_font = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22,
                    )
                    body_font = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14,
                    )
                    footer_font = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12,
                    )
                except (OSError, IOError):
                    title_font = ImageFont.load_default()
                    body_font = ImageFont.load_default()
                    footer_font = ImageFont.load_default()

            # Visual type label in header
            type_label = visual_type.replace("_", " ").upper()
            draw.text(
                (width // 2, header_h // 2 + border_width),
                type_label,
                fill=(255, 255, 255),
                font=title_font,
                anchor="mm",
            )

            # Wrapped description text in body
            body_top = header_h + 20
            body_left = 30
            body_right = width - 30
            max_chars = (body_right - body_left) // 8  # rough estimate
            wrapped = textwrap.fill(description[:600], width=max_chars)
            lines = wrapped.split("\n")[:15]  # cap at 15 lines
            y = body_top
            for line in lines:
                draw.text(
                    (body_left, y),
                    line,
                    fill=(60, 60, 60),
                    font=body_font,
                )
                y += 22
                if y > height - 60:
                    break

            # Footer notice
            footer_text = "Placeholder - Napkin AI unavailable"
            draw.text(
                (width // 2, height - 25),
                footer_text,
                fill=(150, 150, 150),
                font=footer_font,
                anchor="mm",
            )

            # Ensure save_path ends with .png for Pillow compatibility
            if not save_path.lower().endswith(".png"):
                save_path = str(Path(save_path).with_suffix(".png"))

            img.save(save_path, "PNG")

            logger.info("Created placeholder visual: %s", save_path)
            return {
                "success": True,
                "file_path": save_path,
                "visual_type": visual_type,
                "method": "placeholder",
                "error": None,
            }

        except ImportError:
            logger.error(
                "Pillow is not installed; cannot create placeholder image. "
                "Install with: pip install Pillow",
            )
            return {
                "success": False,
                "file_path": None,
                "visual_type": visual_type,
                "method": "placeholder",
                "error": "Pillow not installed",
            }
        except Exception as exc:
            logger.error("Placeholder creation failed: %s", exc)
            return {
                "success": False,
                "file_path": None,
                "visual_type": visual_type,
                "method": "placeholder",
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Inventory & stats
    # ------------------------------------------------------------------

    def list_generated_visuals(self) -> list[dict]:
        """List all visual files in the output directory with metadata.

        Returns
        -------
        list[dict]
            Each dict contains: ``name``, ``path``, ``size_bytes``,
            ``created``, ``visual_type`` (inferred from filename).
        """
        visuals: list[dict] = []

        if not VISUALS_DIR.exists():
            return visuals

        image_extensions = {".png", ".jpg", ".jpeg", ".svg", ".pdf", ".webp"}

        for entry in sorted(VISUALS_DIR.iterdir()):
            if not entry.is_file():
                continue
            if entry.suffix.lower() not in image_extensions:
                continue

            stat = entry.stat()

            # Infer visual type from the filename convention:
            #   <visual_type>_<timestamp>_<uuid>.<ext>  OR
            #   slide_<n>_<title>_<timestamp>.<ext>     OR
            #   doc_<title>_<visual_type>_<timestamp>_<uuid>.<ext>
            stem = entry.stem
            visual_type = "unknown"
            for vtype in VISUAL_TYPES:
                if vtype in stem:
                    visual_type = vtype
                    break
            if visual_type == "unknown" and stem.startswith("placeholder_"):
                parts = stem.split("_", 2)
                if len(parts) >= 2:
                    visual_type = parts[1]

            visuals.append({
                "name": entry.name,
                "path": str(entry),
                "size_bytes": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "visual_type": visual_type,
            })

        return visuals

    def get_visual_stats(self) -> dict:
        """Return summary statistics about generated visuals.

        Returns
        -------
        dict
            Keys: ``total_visuals``, ``total_size_bytes``,
            ``total_size_mb``, ``by_type`` (counts per visual type),
            ``napkin_available``, ``cache_dir_size_bytes``.
        """
        visuals = self.list_generated_visuals()

        total_size = sum(v["size_bytes"] for v in visuals)

        by_type: dict[str, int] = {}
        for v in visuals:
            vt = v["visual_type"]
            by_type[vt] = by_type.get(vt, 0) + 1

        # Calculate cache directory size
        cache_size = 0
        cache_path = CACHE_DIR
        if cache_path.exists():
            for entry in cache_path.rglob("*"):
                if entry.is_file():
                    try:
                        cache_size += entry.stat().st_size
                    except OSError:
                        pass

        return {
            "total_visuals": len(visuals),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_type": by_type,
            "napkin_available": self.napkin.available,
            "cache_dir_size_bytes": cache_size,
        }
