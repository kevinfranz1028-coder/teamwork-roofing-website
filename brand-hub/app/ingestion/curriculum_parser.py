"""
Curriculum parsing module for Brand Intelligence Content Hub.

Uses the Anthropic Claude API to intelligently parse raw text content
into structured curriculum and training material JSON.
"""

import json
import logging
import os
from typing import Any

from anthropic import Anthropic

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_MAX_TOKENS = 4096


class CurriculumParser:
    """Parses raw content into structured curriculum using Claude AI.

    Takes unstructured text (from PDFs, DOCX, web pages, etc.) and
    uses the Anthropic API to extract a well-organized curriculum
    structure with modules, objectives, sections, activities, and
    assessments.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        """Initialize the CurriculumParser with an Anthropic client.

        The API key is read from the ANTHROPIC_API_KEY environment variable.

        Args:
            model: The Claude model to use for parsing.
            max_tokens: Maximum tokens in the response.

        Raises:
            ValueError: If the ANTHROPIC_API_KEY environment variable is
                not set.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable must be set "
                "to use CurriculumParser"
            )

        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def parse(
        self,
        raw_content: str,
        content_type: str = "training",
    ) -> dict[str, Any]:
        """Parse raw content into a structured curriculum.

        Args:
            raw_content: The raw text content to parse into curriculum
                structure.
            content_type: The type of content being parsed. Supported
                values include 'training', 'onboarding', 'course',
                'workshop', and 'certification'. Defaults to 'training'.

        Returns:
            A dictionary containing:
                - title: The curriculum title.
                - modules: List of module dicts, each with:
                    - title: Module title.
                    - objectives: List of learning objective strings.
                    - sections: List of section dicts with title and content.
                    - activities: List of activity descriptions.
                    - assessments: List of assessment descriptions.
                - metadata: Dict with content_type, module_count, and
                  estimated_duration.

        Raises:
            ValueError: If raw_content is empty.
            Exception: If the API call fails.
        """
        if not raw_content or not raw_content.strip():
            raise ValueError("raw_content must not be empty")

        prompt = self._build_curriculum_prompt(raw_content, content_type)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": prompt},
                ],
                system=(
                    "You are an expert instructional designer. You parse raw "
                    "content into well-structured curriculum JSON. Always "
                    "respond with valid JSON only, no markdown fences or "
                    "explanatory text."
                ),
            )

            response_text = message.content[0].text.strip()

            # Strip markdown code fences if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                # Remove first line (```json or ```) and last line (```)
                lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                response_text = "\n".join(lines)

            curriculum = json.loads(response_text)

            # Ensure the expected top-level keys exist
            curriculum.setdefault("title", "Untitled Curriculum")
            curriculum.setdefault("modules", [])

            # Normalize each module to have all expected fields
            for module in curriculum["modules"]:
                module.setdefault("title", "Untitled Module")
                module.setdefault("objectives", [])
                module.setdefault("sections", [])
                module.setdefault("activities", [])
                module.setdefault("assessments", [])

            curriculum["metadata"] = {
                "content_type": content_type,
                "module_count": len(curriculum["modules"]),
                "estimated_duration": self._estimate_duration(curriculum["modules"]),
            }

            return curriculum

        except json.JSONDecodeError as exc:
            logger.error(
                "Failed to parse Claude response as JSON: %s", exc
            )
            raise ValueError(
                "Claude returned invalid JSON. Try again with cleaner input."
            ) from exc
        except Exception as exc:
            logger.error("Curriculum parsing failed: %s", exc)
            raise

    def _build_curriculum_prompt(
        self,
        content: str,
        content_type: str,
    ) -> str:
        """Build the prompt sent to Claude for curriculum extraction.

        Args:
            content: The raw text content to be structured.
            content_type: The type of curriculum (e.g. 'training',
                'onboarding', 'course').

        Returns:
            A formatted prompt string.
        """
        return f"""Analyze the following raw content and transform it into a structured {content_type} curriculum.

Return a JSON object with this exact structure:
{{
    "title": "Curriculum title derived from the content",
    "modules": [
        {{
            "title": "Module title",
            "objectives": [
                "Learning objective 1",
                "Learning objective 2"
            ],
            "sections": [
                {{
                    "title": "Section title",
                    "content": "Section content text"
                }}
            ],
            "activities": [
                "Hands-on activity or exercise description"
            ],
            "assessments": [
                "Quiz, test, or evaluation description"
            ]
        }}
    ]
}}

Guidelines:
- Identify logical module boundaries in the content.
- Extract clear, measurable learning objectives for each module.
- Organize content into coherent sections within each module.
- Suggest practical activities that reinforce the material.
- Propose assessments that verify understanding.
- If the content is sparse, create fewer but higher-quality modules.
- Maintain the original meaning and terminology of the content.
- Content type is "{content_type}" -- adapt the structure accordingly.

RAW CONTENT:
---
{content}
---

Respond with valid JSON only."""

    @staticmethod
    def _estimate_duration(modules: list[dict[str, Any]]) -> str:
        """Estimate total curriculum duration based on module content.

        Uses a rough heuristic: each module takes approximately 30-60
        minutes depending on section count and activities.

        Args:
            modules: List of module dictionaries.

        Returns:
            A human-readable duration estimate string.
        """
        if not modules:
            return "0 minutes"

        total_minutes = 0
        for module in modules:
            # Base time per module
            base_minutes = 30
            # Additional time for sections
            section_count = len(module.get("sections", []))
            base_minutes += section_count * 10
            # Additional time for activities
            activity_count = len(module.get("activities", []))
            base_minutes += activity_count * 15
            # Additional time for assessments
            assessment_count = len(module.get("assessments", []))
            base_minutes += assessment_count * 10

            total_minutes += base_minutes

        if total_minutes < 60:
            return f"{total_minutes} minutes"
        hours = total_minutes / 60
        if hours == int(hours):
            return f"{int(hours)} hours"
        return f"{hours:.1f} hours"
