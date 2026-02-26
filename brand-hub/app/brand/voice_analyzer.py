"""
Brand Intelligence Content Hub - Voice Analyzer

Uses Claude (via the Anthropic SDK) to analyse the tone, formality, vocabulary
level, recurring phrases, and structural patterns in text so that a brand's
unique voice can be captured and later enforced during content generation.
"""

import json
import os
from pathlib import Path

from anthropic import Anthropic


class VoiceAnalyzer:
    """Analyse brand voice characteristics using Claude."""

    def __init__(self):
        """Initialise the Anthropic client from the environment variable."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. "
                "Please configure it in your .env file or shell environment."
            )
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_text(self, text: str) -> dict:
        """Analyse a single block of text for brand-voice characteristics.

        Parameters
        ----------
        text : str
            The content to analyse (marketing copy, website text, etc.).

        Returns
        -------
        dict
            Keys: ``tone``, ``formality``, ``vocabulary_level``,
            ``key_phrases``, ``patterns``, ``messaging_themes``,
            ``sentence_structure``.
        """
        if not text or not text.strip():
            return self._empty_analysis()

        prompt = self._build_analysis_prompt(text)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text

            # Parse the JSON from the model response
            analysis = self._parse_json_response(raw)
            return analysis
        except Exception as exc:
            return {
                **self._empty_analysis(),
                "error": str(exc),
            }

    def analyze_documents(self, file_paths: list[str]) -> dict:
        """Analyse multiple documents and produce a combined voice profile.

        Parameters
        ----------
        file_paths : list[str]
            Paths to text / markdown / plain-text files to include.

        Returns
        -------
        dict
            A merged voice profile combining insights from every file.
        """
        individual_analyses: list[dict] = []
        texts: list[str] = []

        for fp in file_paths:
            path = Path(fp)
            if not path.exists():
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                texts.append(content)
                analysis = self.analyze_text(content)
                individual_analyses.append(analysis)
            except Exception:
                continue

        if not individual_analyses:
            return self._empty_analysis()

        # Build a combined profile by merging individual analyses
        return self._merge_analyses(individual_analyses)

    def compare_to_brand_voice(self, text: str, brand_voice_config: dict) -> dict:
        """Compare a piece of text against an established brand voice config.

        Parameters
        ----------
        text : str
            New content to evaluate.
        brand_voice_config : dict
            The ``voice`` section from ``brand_config.json`` containing
            ``tone``, ``formality``, ``vocabulary_level``, ``key_phrases``,
            ``avoid_phrases``, and ``messaging_themes``.

        Returns
        -------
        dict
            ``{"alignment_score": float, "deviations": [...], "suggestions": [...]}``
        """
        if not text or not text.strip():
            return {"alignment_score": 0.0, "deviations": [], "suggestions": []}

        prompt = self._build_comparison_prompt(text, brand_voice_config)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text
            result = self._parse_json_response(raw)

            # Ensure expected keys are present
            return {
                "alignment_score": result.get("alignment_score", 0.0),
                "deviations": result.get("deviations", []),
                "suggestions": result.get("suggestions", []),
            }
        except Exception as exc:
            return {
                "alignment_score": 0.0,
                "deviations": [],
                "suggestions": [],
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_analysis_prompt(self, text: str) -> str:
        """Build the Claude prompt for brand-voice analysis."""
        return f"""Analyse the following text for brand voice characteristics.
Return ONLY valid JSON (no markdown fences, no explanation) with these exact keys:

{{
  "tone": "<one of: professional, casual, friendly, authoritative, inspirational, empathetic, playful, formal>",
  "formality": <integer 1-5, where 1=very casual and 5=very formal>,
  "vocabulary_level": "<one of: basic, intermediate, advanced, technical>",
  "key_phrases": ["<recurring or distinctive phrases found in the text>"],
  "patterns": {{
    "average_sentence_length": "<short / medium / long>",
    "use_of_questions": <true or false>,
    "use_of_exclamations": <true or false>,
    "use_of_first_person": <true or false>,
    "use_of_second_person": <true or false>,
    "active_voice_dominant": <true or false>
  }},
  "sentence_structure": "<description of typical sentence structures>",
  "messaging_themes": ["<major themes or value propositions found>"]
}}

--- TEXT TO ANALYSE ---
{text}
--- END TEXT ---"""

    def _build_comparison_prompt(self, text: str, brand_voice_config: dict) -> str:
        """Build the Claude prompt for comparing text against brand voice."""
        config_json = json.dumps(brand_voice_config, indent=2)
        return f"""Compare the following text against the established brand voice configuration.
Return ONLY valid JSON (no markdown fences, no explanation) with these exact keys:

{{
  "alignment_score": <float 0.0 to 1.0, where 1.0 is perfect alignment>,
  "deviations": [
    "<description of each way the text deviates from the brand voice>"
  ],
  "suggestions": [
    "<actionable suggestion to bring the text closer to the brand voice>"
  ]
}}

--- BRAND VOICE CONFIGURATION ---
{config_json}
--- END CONFIGURATION ---

--- TEXT TO EVALUATE ---
{text}
--- END TEXT ---"""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _empty_analysis() -> dict:
        """Return a blank analysis structure."""
        return {
            "tone": "unknown",
            "formality": 3,
            "vocabulary_level": "intermediate",
            "key_phrases": [],
            "patterns": {
                "average_sentence_length": "medium",
                "use_of_questions": False,
                "use_of_exclamations": False,
                "use_of_first_person": False,
                "use_of_second_person": False,
                "active_voice_dominant": True,
            },
            "sentence_structure": "",
            "messaging_themes": [],
        }

    @staticmethod
    def _parse_json_response(raw_text: str) -> dict:
        """Attempt to extract a JSON object from Claude's response."""
        text = raw_text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last fence lines
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find the first { ... } block
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    pass
            return {}

    @staticmethod
    def _merge_analyses(analyses: list[dict]) -> dict:
        """Merge multiple individual analyses into a combined voice profile."""
        if not analyses:
            return VoiceAnalyzer._empty_analysis()

        # Aggregate tone votes
        tone_counts: dict[str, int] = {}
        formality_sum = 0
        vocab_counts: dict[str, int] = {}
        all_phrases: list[str] = []
        all_themes: list[str] = []

        for a in analyses:
            tone = a.get("tone", "unknown")
            tone_counts[tone] = tone_counts.get(tone, 0) + 1

            formality_sum += a.get("formality", 3)

            vocab = a.get("vocabulary_level", "intermediate")
            vocab_counts[vocab] = vocab_counts.get(vocab, 0) + 1

            all_phrases.extend(a.get("key_phrases", []))
            all_themes.extend(a.get("messaging_themes", []))

        # Dominant tone / vocab by vote count
        dominant_tone = max(tone_counts, key=tone_counts.get)
        dominant_vocab = max(vocab_counts, key=vocab_counts.get)
        avg_formality = round(formality_sum / len(analyses))

        # Deduplicate phrases / themes while preserving order
        seen_phrases: set[str] = set()
        unique_phrases: list[str] = []
        for p in all_phrases:
            lower = p.lower()
            if lower not in seen_phrases:
                seen_phrases.add(lower)
                unique_phrases.append(p)

        seen_themes: set[str] = set()
        unique_themes: list[str] = []
        for t in all_themes:
            lower = t.lower()
            if lower not in seen_themes:
                seen_themes.add(lower)
                unique_themes.append(t)

        # Merge pattern flags using majority vote
        pattern_keys = [
            "use_of_questions",
            "use_of_exclamations",
            "use_of_first_person",
            "use_of_second_person",
            "active_voice_dominant",
        ]
        merged_patterns: dict = {}
        for pk in pattern_keys:
            true_count = sum(
                1 for a in analyses if a.get("patterns", {}).get(pk, False)
            )
            merged_patterns[pk] = true_count > len(analyses) / 2

        # Average sentence length
        length_counts: dict[str, int] = {}
        for a in analyses:
            sl = a.get("patterns", {}).get("average_sentence_length", "medium")
            length_counts[sl] = length_counts.get(sl, 0) + 1
        merged_patterns["average_sentence_length"] = max(
            length_counts, key=length_counts.get
        ) if length_counts else "medium"

        return {
            "tone": dominant_tone,
            "formality": avg_formality,
            "vocabulary_level": dominant_vocab,
            "key_phrases": unique_phrases,
            "patterns": merged_patterns,
            "sentence_structure": analyses[0].get("sentence_structure", ""),
            "messaging_themes": unique_themes,
        }
