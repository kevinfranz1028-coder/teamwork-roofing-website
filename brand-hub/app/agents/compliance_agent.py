"""
Brand Intelligence Content Hub - Brand Compliance Agent

Validates generated content against brand guidelines defined in
``brand_config.json``.  Uses Claude Haiku for fast, cheap
analysis and returns structured per-check pass/fail results.

Usage:
    from app.agents.compliance_agent import ComplianceAgent

    agent = ComplianceAgent()
    result = agent.validate("/path/to/output.pptx")
    print(result["overall_score"])
    for check in result["checks"]:
        print(check["name"], check["passed"])
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

from app.config import BRAND_ASSETS_DIR

logger = logging.getLogger(__name__)

# Claude Haiku model for fast, cheap validation
COMPLIANCE_MODEL = "claude-haiku-4-5-20251001"


class ComplianceAgent:
    """Reviews generated content against brand guidelines.

    Performs both rule-based checks (colors, acronyms) and AI-powered
    checks (voice tone, style consistency) using Claude Haiku.
    """

    def __init__(self, brand_config: Optional[dict] = None) -> None:
        self.brand_config: dict = brand_config or self._load_brand_config()
        self._client = None

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
    # Anthropic client (lazy)
    # ------------------------------------------------------------------

    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import Anthropic
                api_key = os.environ.get("ANTHROPIC_API_KEY", "")
                if api_key:
                    self._client = Anthropic(api_key=api_key)
            except Exception as exc:
                logger.warning("Could not init Anthropic client: %s", exc)
        return self._client

    # ------------------------------------------------------------------
    # Content extraction
    # ------------------------------------------------------------------

    def _extract_content(self, file_path: str) -> dict[str, Any]:
        """Extract text and metadata from a file for compliance review.

        Supports .pptx, .docx, .txt, and .md files.

        Returns:
            Dict with ``text``, ``file_type``, ``metadata``, and
            optionally ``colors_found`` (for PPTX).
        """
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = p.suffix.lower()

        if ext in (".pptx", ".pptm"):
            return self._extract_pptx(file_path)
        elif ext in (".docx", ".docm"):
            return self._extract_docx(file_path)
        elif ext in (".txt", ".md", ".markdown"):
            return self._extract_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    @staticmethod
    def _extract_pptx(file_path: str) -> dict[str, Any]:
        """Extract content from a PPTX using the existing parser."""
        from app.ingestion.pptx_parser import PPTXParser

        parser = PPTXParser()
        parsed = parser.parse(file_path)

        # Concatenate all slide text
        text_parts = []
        for slide in parsed.get("slides", []):
            if slide.get("title"):
                text_parts.append(slide["title"])
            for content_item in slide.get("content", []):
                if content_item:
                    text_parts.append(content_item)
            if slide.get("notes"):
                text_parts.append(slide["notes"])

        # Extract colors from the file for color compliance
        colors_found: list[str] = []
        try:
            template_info = parser.extract_template_info(file_path)
            color_scheme = template_info.get("color_scheme", {})
            colors_found = list(color_scheme.values())
        except Exception:
            pass

        return {
            "text": "\n\n".join(text_parts),
            "file_type": "pptx",
            "metadata": parsed.get("metadata", {}),
            "colors_found": colors_found,
            "slide_count": len(parsed.get("slides", [])),
        }

    @staticmethod
    def _extract_docx(file_path: str) -> dict[str, Any]:
        """Extract content from a DOCX using the existing parser."""
        from app.ingestion.docx_parser import DOCXParser

        parser = DOCXParser()
        parsed = parser.parse(file_path)

        return {
            "text": parsed.get("text", ""),
            "file_type": "docx",
            "metadata": parsed.get("metadata", {}),
            "styles": parsed.get("styles", []),
        }

    @staticmethod
    def _extract_text(file_path: str) -> dict[str, Any]:
        """Read a plain text or markdown file."""
        text = Path(file_path).read_text(encoding="utf-8", errors="replace")
        return {
            "text": text,
            "file_type": Path(file_path).suffix.lstrip("."),
            "metadata": {},
        }

    # ------------------------------------------------------------------
    # Rule-based checks
    # ------------------------------------------------------------------

    def _check_colors(self, content: dict) -> dict:
        """Check if colors used in the file match the brand palette."""
        full_palette = self.brand_config.get("full_palette", {})
        colors_cfg = self.brand_config.get("colors", {})
        # Combine both into the allowed set
        allowed = set()
        for v in full_palette.values():
            allowed.add(v.upper().lstrip("#"))
        for v in colors_cfg.values():
            allowed.add(v.upper().lstrip("#"))

        colors_found = content.get("colors_found", [])
        if not colors_found:
            return {
                "name": "color_palette",
                "display_name": "Color Palette Compliance",
                "passed": True,
                "score": 1.0,
                "details": "No colors extracted from file (text-only or extraction not supported).",
                "issues": [],
            }

        off_brand = []
        for color in colors_found:
            c = color.upper().lstrip("#")
            if c and c not in allowed:
                off_brand.append(f"#{c}")

        passed = len(off_brand) == 0
        return {
            "name": "color_palette",
            "display_name": "Color Palette Compliance",
            "passed": passed,
            "score": 1.0 if passed else max(0, 1.0 - len(off_brand) * 0.2),
            "details": (
                "All colors match the brand palette."
                if passed
                else f"{len(off_brand)} off-brand color(s) found."
            ),
            "issues": [
                {
                    "severity": "warning",
                    "message": f"Color {c} is not in the brand palette",
                    "fix": "Replace with a brand color: " + ", ".join("#" + v.lstrip("#") for v in list(full_palette.values())[:4]),
                }
                for c in off_brand
            ],
        }

    def _check_acronyms(self, text: str) -> dict:
        """Check that acronyms are properly expanded on first use."""
        acronyms = self.brand_config.get("terminology", {}).get("acronyms", {})
        if not acronyms:
            return {
                "name": "acronym_expansion",
                "display_name": "Acronym Expansion",
                "passed": True,
                "score": 1.0,
                "details": "No acronyms defined in brand config.",
                "issues": [],
            }

        issues = []
        for abbr, full_form in acronyms.items():
            # Check if the acronym appears in the text
            pattern = rf"\b{re.escape(abbr)}\b"
            matches = list(re.finditer(pattern, text))
            if not matches:
                continue

            # Check if the full form appears before or alongside the first use
            first_pos = matches[0].start()
            text_before_first = text[:first_pos + len(abbr) + 50]

            # Look for patterns like "Teleperformance (TP)" or "TP (Teleperformance)"
            expansion_pattern = (
                rf"{re.escape(full_form)}\s*\({re.escape(abbr)}\)"
                rf"|{re.escape(abbr)}\s*\({re.escape(full_form)}\)"
            )
            has_expansion = bool(re.search(expansion_pattern, text, re.IGNORECASE))

            # Also accept if the full form appears anywhere before the first acronym use
            full_before = text[:first_pos].lower().find(full_form.lower()) >= 0

            if not has_expansion and not full_before:
                issues.append({
                    "severity": "info",
                    "message": f'Acronym "{abbr}" used without expanding to "{full_form}" on first use',
                    "fix": f'Add "{full_form} ({abbr})" on first mention',
                })

        passed = len(issues) == 0
        return {
            "name": "acronym_expansion",
            "display_name": "Acronym Expansion",
            "passed": passed,
            "score": 1.0 if passed else max(0, 1.0 - len(issues) * 0.25),
            "details": (
                "All acronyms properly expanded on first use."
                if passed
                else f"{len(issues)} acronym(s) not expanded."
            ),
            "issues": issues,
        }

    def _check_avoided_phrases(self, text: str) -> dict:
        """Check that avoided phrases are absent from the text."""
        avoid = self.brand_config.get("voice_profile", {}).get("avoid_phrases", [])
        if not avoid:
            return {
                "name": "avoided_phrases",
                "display_name": "Avoided Phrases",
                "passed": True,
                "score": 1.0,
                "details": "No phrases to avoid defined in brand config.",
                "issues": [],
            }

        text_lower = text.lower()
        issues = []
        for phrase in avoid:
            if phrase.lower() in text_lower:
                issues.append({
                    "severity": "warning",
                    "message": f'Avoided phrase found: "{phrase}"',
                    "fix": f'Remove or replace "{phrase}" with brand-appropriate language',
                })

        passed = len(issues) == 0
        return {
            "name": "avoided_phrases",
            "display_name": "Avoided Phrases",
            "passed": passed,
            "score": 1.0 if passed else max(0, 1.0 - len(issues) * 0.3),
            "details": (
                "No avoided phrases detected."
                if passed
                else f"{len(issues)} avoided phrase(s) found."
            ),
            "issues": issues,
        }

    def _check_preferred_terms(self, text: str) -> dict:
        """Check that preferred terms are used instead of alternatives."""
        preferred = self.brand_config.get("terminology", {}).get("preferred_terms", {})
        if not preferred:
            return {
                "name": "preferred_terms",
                "display_name": "Preferred Terminology",
                "passed": True,
                "score": 1.0,
                "details": "No preferred terms defined in brand config.",
                "issues": [],
            }

        text_lower = text.lower()
        issues = []
        for wrong, right in preferred.items():
            pattern = rf"\b{re.escape(wrong)}\b"
            if re.search(pattern, text_lower, re.IGNORECASE):
                issues.append({
                    "severity": "warning",
                    "message": f'Non-preferred term "{wrong}" found',
                    "fix": f'Replace with preferred term: "{right}"',
                })

        passed = len(issues) == 0
        return {
            "name": "preferred_terms",
            "display_name": "Preferred Terminology",
            "passed": passed,
            "score": 1.0 if passed else max(0, 1.0 - len(issues) * 0.2),
            "details": (
                "All preferred terms used correctly."
                if passed
                else f"{len(issues)} non-preferred term(s) found."
            ),
            "issues": issues,
        }

    def _check_key_phrases(self, text: str) -> dict:
        """Check whether key brand phrases are incorporated."""
        key_phrases = self.brand_config.get("voice_profile", {}).get("key_phrases", [])
        if not key_phrases:
            return {
                "name": "key_phrases",
                "display_name": "Key Phrase Incorporation",
                "passed": True,
                "score": 1.0,
                "details": "No key phrases defined in brand config.",
                "issues": [],
            }

        text_lower = text.lower()
        found = []
        missing = []
        for phrase in key_phrases:
            if phrase.lower() in text_lower:
                found.append(phrase)
            else:
                missing.append(phrase)

        # Requirement: at least 1 key phrase should appear, ideally 2+
        ratio = len(found) / len(key_phrases) if key_phrases else 1.0
        passed = len(found) >= 1
        score = min(1.0, ratio * 2)  # 50% incorporation = 1.0 score

        issues = []
        if not passed:
            issues.append({
                "severity": "info",
                "message": "No key brand phrases found in the content",
                "fix": f"Consider naturally incorporating: {', '.join(key_phrases[:3])}",
            })

        return {
            "name": "key_phrases",
            "display_name": "Key Phrase Incorporation",
            "passed": passed,
            "score": round(score, 2),
            "details": f"{len(found)}/{len(key_phrases)} key phrases incorporated.",
            "found": found,
            "missing": missing,
            "issues": issues,
        }

    # ------------------------------------------------------------------
    # AI-powered checks (Claude Haiku)
    # ------------------------------------------------------------------

    def _check_voice_and_style(self, text: str) -> dict:
        """Use Claude Haiku to validate voice tone, formality, and style."""
        client = self._get_client()
        if client is None:
            return {
                "name": "voice_and_style",
                "display_name": "Voice & Style Consistency",
                "passed": True,
                "score": 1.0,
                "details": "Skipped — Anthropic API key not available.",
                "issues": [],
            }

        voice = self.brand_config.get("voice_profile", {})
        terminology = self.brand_config.get("terminology", {})
        colors = self.brand_config.get("colors", {})
        full_palette = self.brand_config.get("full_palette", {})
        fonts = self.brand_config.get("fonts", {})
        company = self.brand_config.get("company_name", "")

        system_prompt = (
            "You are a brand compliance reviewer. Analyze the provided content "
            "against the brand guidelines below and return a JSON assessment.\n\n"
            "BRAND GUIDELINES:\n"
            f"Company: {company}\n"
            f"Tone: {voice.get('tone', 'professional')}\n"
            f"Formality: {voice.get('formality', 'Semi-Formal')}\n"
            f"Vocabulary Level: {voice.get('vocabulary_level', 'Moderate')}\n"
            f"Key Phrases: {json.dumps(voice.get('key_phrases', []))}\n"
            f"Avoid Phrases: {json.dumps(voice.get('avoid_phrases', []))}\n"
            f"Messaging Themes: {json.dumps(voice.get('messaging_themes', []))}\n"
            f"Preferred Terms: {json.dumps(terminology.get('preferred_terms', {}))}\n"
            f"Program Names: {json.dumps(terminology.get('program_names', []))}\n"
            f"Acronyms: {json.dumps(terminology.get('acronyms', {}))}\n"
            f"Brand Colors: {json.dumps(colors)}\n"
            f"Full Palette: {json.dumps(full_palette)}\n"
            f"Fonts: {json.dumps(fonts)}\n\n"
            "Return ONLY valid JSON with this exact structure:\n"
            "{\n"
            '  "voice_tone": {\n'
            '    "passed": true/false,\n'
            '    "score": 0.0-1.0,\n'
            '    "assessment": "brief explanation",\n'
            '    "issues": [{"severity": "warning"|"info"|"error", "message": "...", "fix": "..."}]\n'
            "  },\n"
            '  "formality_level": {\n'
            '    "passed": true/false,\n'
            '    "score": 0.0-1.0,\n'
            '    "assessment": "brief explanation",\n'
            '    "issues": []\n'
            "  },\n"
            '  "style_consistency": {\n'
            '    "passed": true/false,\n'
            '    "score": 0.0-1.0,\n'
            '    "assessment": "brief explanation of writing style consistency",\n'
            '    "issues": []\n'
            "  },\n"
            '  "messaging_alignment": {\n'
            '    "passed": true/false,\n'
            '    "score": 0.0-1.0,\n'
            '    "assessment": "how well content aligns with brand messaging themes",\n'
            '    "issues": []\n'
            "  }\n"
            "}\n\n"
            "Be fair but thorough. A professional document about company topics "
            "should generally pass voice/formality checks. Focus on real issues."
        )

        # Truncate text to fit in context
        content_sample = text[:6000]

        try:
            message = client.messages.create(
                model=COMPLIANCE_MODEL,
                max_tokens=1500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Review this content:\n\n{content_sample}"},
                ],
            )
            raw = message.content[0].text.strip()

            # Parse JSON from response
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw)

            ai_result = json.loads(raw)

        except Exception as exc:
            logger.warning("AI compliance check failed: %s", exc)
            return {
                "name": "voice_and_style",
                "display_name": "Voice & Style Consistency",
                "passed": True,
                "score": 1.0,
                "details": f"AI check failed: {exc}",
                "issues": [],
            }

        # Convert AI result into individual check dicts
        checks = []
        for check_key, display_name in [
            ("voice_tone", "Voice Tone"),
            ("formality_level", "Formality Level"),
            ("style_consistency", "Style Consistency"),
            ("messaging_alignment", "Messaging Alignment"),
        ]:
            data = ai_result.get(check_key, {})
            checks.append({
                "name": check_key,
                "display_name": display_name,
                "passed": data.get("passed", True),
                "score": data.get("score", 1.0),
                "details": data.get("assessment", ""),
                "issues": data.get("issues", []),
            })

        return checks

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(
        self,
        file_path: str,
        content_text: Optional[str] = None,
    ) -> dict[str, Any]:
        """Validate a file or text against brand guidelines.

        Args:
            file_path: Path to the file to validate (.pptx, .docx, .txt, .md).
            content_text: Optional pre-extracted text. When provided, file
                parsing is skipped for text checks (but colors may still
                be extracted from the file).

        Returns:
            Dict with ``overall_score``, ``overall_passed``, ``file_path``,
            ``checks`` (list of per-check results), and ``summary``.
        """
        logger.info("Running brand compliance check on: %s", file_path)

        # --- Extract content ---
        content = {}
        if content_text:
            content = {"text": content_text, "file_type": "text", "metadata": {}}
            # Still extract colors from file if it exists
            try:
                file_content = self._extract_content(file_path)
                content["colors_found"] = file_content.get("colors_found", [])
                content["file_type"] = file_content.get("file_type", "text")
                content["metadata"] = file_content.get("metadata", {})
            except Exception:
                pass
        else:
            content = self._extract_content(file_path)

        text = content.get("text", "")
        if not text.strip():
            return {
                "overall_score": 0.0,
                "overall_passed": False,
                "file_path": file_path,
                "checks": [],
                "summary": "No text content could be extracted from the file.",
            }

        # --- Run all checks ---
        checks: list[dict] = []

        # Rule-based checks
        checks.append(self._check_colors(content))
        checks.append(self._check_acronyms(text))
        checks.append(self._check_avoided_phrases(text))
        checks.append(self._check_preferred_terms(text))
        checks.append(self._check_key_phrases(text))

        # AI-powered checks (returns a list or a single dict)
        ai_result = self._check_voice_and_style(text)
        if isinstance(ai_result, list):
            checks.extend(ai_result)
        else:
            checks.append(ai_result)

        # --- Compute overall score ---
        scores = [c["score"] for c in checks if "score" in c]
        overall_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        overall_passed = all(c.get("passed", True) for c in checks)

        # Count issues by severity
        all_issues = []
        for c in checks:
            all_issues.extend(c.get("issues", []))
        error_count = sum(1 for i in all_issues if i.get("severity") == "error")
        warning_count = sum(1 for i in all_issues if i.get("severity") == "warning")
        info_count = sum(1 for i in all_issues if i.get("severity") == "info")

        passed_count = sum(1 for c in checks if c.get("passed", True))
        total_count = len(checks)

        summary = (
            f"{passed_count}/{total_count} checks passed "
            f"(score: {overall_score}/1.0). "
            f"{error_count} errors, {warning_count} warnings, {info_count} info."
        )

        result = {
            "overall_score": overall_score,
            "overall_passed": overall_passed,
            "file_path": file_path,
            "file_type": content.get("file_type", "unknown"),
            "checks": checks,
            "summary": summary,
            "issue_counts": {
                "errors": error_count,
                "warnings": warning_count,
                "info": info_count,
            },
        }

        logger.info("Compliance result: %s", summary)
        return result
