"""
Brand Intelligence Content Hub - Writer Agent

Takes a :class:`ContentBrief` and user request, then calls Claude to
produce structured JSON content that existing generators consume directly.

Usage:
    from app.agents.writer_agent import WriterAgent

    agent = WriterAgent()
    content = agent.write(
        request="Create a sales training presentation about FACTS",
        content_type="presentation",
        brief=brief,
    )
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Optional

from app.agents.task_plan import ContentBrief
from app.config import BRAND_ASSETS_DIR

logger = logging.getLogger(__name__)

DEFAULT_WRITER_MODEL = "claude-sonnet-4-20250514"

# ---------------------------------------------------------------------------
# Document-type schemas — exact keys expected by document_gen.py builders
# ---------------------------------------------------------------------------

DOCUMENT_SCHEMAS: dict[str, str] = {
    "job_aid": """\
Return JSON with these keys:
- title (str)
- purpose (str): 1-2 sentence purpose statement
- sections (list of objects): each has "heading" (str), "steps" (list of str), "tips" (list of str)
- reference_table (list of lists): 2D table where first row is headers, remaining rows are data""",

    "case_study": """\
Return JSON with these keys:
- title (str)
- client_name (str)
- industry (str)
- executive_summary (str): 2-3 sentences
- challenge (str): paragraph describing the problem
- solution (str): paragraph describing the solution
- approach_steps (list of str): numbered implementation steps
- results: object with "metrics" (list of lists, header row + data) and "narrative" (str)
- key_takeaways (list of str)
- testimonial: object with "quote" (str) and "attribution" (str)""",

    "weekly_report": """\
Return JSON with these keys:
- title (str)
- period (str): e.g. "Feb 17-21, 2026"
- kpi_data (list of lists): header row ["KPI", "Target", "Actual", "Status"] + data rows
- accomplishments (list of str)
- challenges (list of str)
- priorities (list of str): next week's priorities
- notes (str): additional notes""",

    "monthly_report": """\
Return JSON with these keys:
- title (str)
- period (str): e.g. "January 2026"
- executive_summary (str): 2-3 paragraph summary
- metrics_data (list of lists): header row + data rows
- sections (list of objects): each has "heading" (str), "content" (str), "subsections" (list of objects with "heading" and "content")
- recommendations (list of str)
- appendix_items (list of str)""",

    "sop": """\
Return JSON with these keys:
- title (str)
- doc_number (str): e.g. "SOP-001"
- version (str): e.g. "1.0"
- effective_date (str)
- author (str)
- approved_by (str)
- purpose (str)
- scope (str)
- responsibilities (list of lists): header row ["Role", "Responsibility"] + data rows
- procedure_steps (list of objects): each has "step" (str), "sub_steps" (list of str), "notes" (str)
- safety_notes (list of str)""",

    "training_guide": """\
Return JSON with these keys:
- title (str)
- course_overview (str): 2-3 sentence overview
- modules (list of objects): each has "title" (str), "objectives" (list of str), "content" (list of str paragraphs), "activities" (list of str), "key_takeaways" (list of str)
- assessment_questions (list of objects): each has "question" (str), "options" (list of str), "answer" (str)
- glossary (object): term-to-definition mapping
- appendix (list of str)""",

    "internal_memo": """\
Return JSON with these keys:
- to (str)
- from_name (str)
- date (str)
- subject (str)
- body_paragraphs (list of str)
- action_items (list of str)
- cc (list of str)""",

    "battle_card": """\
Return JSON with these keys:
- title (str)
- product_name (str)
- at_a_glance (str): 2-3 sentence product summary
- competitors (list of lists): header row ["Feature", "Us", "Competitor A", "Competitor B"] + data rows
- differentiators (list of str)
- objection_responses (list of objects): each has "objection" (str) and "response" (str)
- talk_track (str): 1-2 paragraph elevator pitch
- pricing_table (list of lists): header row + data rows""",

    "capability_overview": """\
Return JSON with these keys:
- title (str)
- tagline (str)
- capabilities (list of objects): each has "name" (str) and "description" (str)
- statistics (list of objects): each has "label" (str) and "value" (str)
- contact: object with "name" (str), "email" (str), "phone" (str)""",

    "proposal": """\
Return JSON with these keys:
- title (str)
- client_name (str)
- executive_summary (str)
- needs_analysis (str)
- proposed_solution (str)
- scope_items (list of lists): header row + data rows
- timeline (list of lists): header row ["Phase", "Duration", "Deliverables"] + data rows
- pricing (list of lists): header row + data rows
- team_members (list of objects): each has "name" (str), "role" (str), "bio" (str)
- terms (str)
- next_steps (list of str)""",
}

PRESENTATION_SCHEMA = """\
Return JSON with exactly this structure:
{
  "slides": [<8-15 slide objects>],
  "title": "<presentation title>"
}

Each slide object has:
- layout (str): one of "title", "section_divider", "content", "two_column", "image_text", "chart_data", "quote_callout", "closing"
- title (str): slide title
- subtitle (str): for title/closing slides only
- bullets (list of str): bullet points; prefix with "- " for sub-bullets
- body (str): paragraph text
- speaker_notes (str): presenter talking points

Slide ordering:
1. First slide: layout "title" with title + subtitle
2. Middle slides: mix of content, section_divider, two_column, quote_callout
3. Last slide: layout "closing"

Generate 8-15 slides total."""


class WriterAgent:
    """Produces structured content JSON for existing generators."""

    def __init__(self, brand_config: dict | None = None) -> None:
        self.brand_config: dict = brand_config or self._load_brand_config()
        self._client = None

    # ------------------------------------------------------------------
    # Lazy init
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

    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import Anthropic

                api_key = os.environ.get("ANTHROPIC_API_KEY", "")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not set")
                self._client = Anthropic(api_key=api_key)
            except Exception as exc:
                logger.error("Could not init Anthropic client: %s", exc)
                raise
        return self._client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write(
        self,
        request: str,
        content_type: str,
        brief: ContentBrief,
        doc_type: str = "",
        title: str = "",
        compliance_feedback: str = "",
    ) -> dict:
        """Generate structured content JSON.

        Args:
            request: Original user request.
            content_type: ``"presentation"`` or ``"document"``.
            brief: Populated ContentBrief from ResearchAgent.
            doc_type: Document template type (documents only).
            title: Desired output title.
            compliance_feedback: Actionable feedback from a failed compliance
                pass, used on retries.

        Returns:
            Structured dict consumable by the matching generator.
        """
        system_prompt = self._build_system_prompt(
            content_type=content_type,
            doc_type=doc_type,
            brief=brief,
            compliance_feedback=compliance_feedback,
        )

        user_prompt = self._build_user_prompt(
            request=request,
            content_type=content_type,
            doc_type=doc_type,
            title=title,
        )

        client = self._get_client()
        model = os.environ.get("WRITER_MODEL", DEFAULT_WRITER_MODEL)

        try:
            message = client.messages.create(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw = message.content[0].text.strip()
            return self._parse_json(raw)
        except Exception as exc:
            logger.error("WriterAgent.write failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_system_prompt(
        self,
        content_type: str,
        doc_type: str,
        brief: ContentBrief,
        compliance_feedback: str,
    ) -> str:
        sections: list[str] = []

        sections.append(
            "You are a professional content writer for a branded-content system. "
            "You produce structured JSON that will be rendered into final documents. "
            "Output ONLY valid JSON — no markdown fences, no commentary."
        )

        # Brand knowledge
        brand_context = brief.to_prompt_context()
        if brand_context:
            sections.append("")
            sections.append(brand_context)

        # Output schema
        sections.append("")
        sections.append("=== OUTPUT FORMAT ===")
        if content_type == "presentation":
            sections.append(PRESENTATION_SCHEMA)
        elif doc_type and doc_type in DOCUMENT_SCHEMAS:
            sections.append(DOCUMENT_SCHEMAS[doc_type])
        else:
            sections.append(
                "Return a JSON object with keys appropriate for the requested "
                "document type. Include a 'title' key."
            )

        # Voice rules
        voice = self.brand_config.get("voice_profile", {})
        if voice:
            sections.append("")
            sections.append("=== BRAND VOICE RULES ===")
            tone = voice.get("tone", "")
            if tone:
                sections.append(f"Tone: {tone}")
            formality = voice.get("formality", "")
            if formality:
                sections.append(f"Formality: {formality}")
            key_phrases = voice.get("key_phrases", [])
            if key_phrases:
                sections.append(
                    f"Naturally incorporate these key phrases where appropriate: "
                    f"{', '.join(key_phrases[:8])}"
                )
            avoid = voice.get("avoid_phrases", [])
            if avoid:
                sections.append(
                    f"AVOID these phrases: {', '.join(avoid[:5])}"
                )

        # Compliance retry feedback
        if compliance_feedback:
            sections.append("")
            sections.append("=== COMPLIANCE FEEDBACK (from previous attempt) ===")
            sections.append(
                "The previous version failed brand compliance checks. "
                "Fix these issues in this version:"
            )
            sections.append(compliance_feedback)

        return "\n".join(sections)

    @staticmethod
    def _build_user_prompt(
        request: str,
        content_type: str,
        doc_type: str,
        title: str,
    ) -> str:
        parts = [f"Request: {request}"]
        if title:
            parts.append(f"Title: {title}")
        if content_type:
            parts.append(f"Content type: {content_type}")
        if doc_type:
            parts.append(f"Document type: {doc_type}")
        parts.append("\nGenerate the structured JSON content now.")
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """Extract JSON from an LLM response, stripping markdown fences."""
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        return json.loads(raw)
