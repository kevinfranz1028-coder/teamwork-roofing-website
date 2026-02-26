"""
Brand Intelligence Content Hub - Brand Wizard

Auto-extracts brand identity from a company URL, logo image, and/or existing
documents, then compiles everything into a unified ``brand_config.json`` that
the rest of the platform uses for on-brand content generation.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from anthropic import Anthropic

from app.brand.color_extractor import ColorExtractor
from app.brand.voice_analyzer import VoiceAnalyzer
from app.config import BRAND_ASSETS_DIR


class BrandWizard:
    """One-click brand identity extraction and configuration builder."""

    CONFIG_FILENAME = "brand_config.json"

    def __init__(self):
        """Initialise sub-components and the Anthropic client."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. "
                "Please configure it in your .env file or shell environment."
            )
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        self.color_extractor = ColorExtractor()
        self.voice_analyzer = VoiceAnalyzer()
        self.config_path = BRAND_ASSETS_DIR / self.CONFIG_FILENAME

    # ------------------------------------------------------------------
    # Extraction from a URL
    # ------------------------------------------------------------------

    def extract_from_url(self, url: str) -> dict:
        """Fetch a webpage and use Claude to extract brand signals.

        Parameters
        ----------
        url : str
            The company website URL (e.g. ``"https://example.com"``).

        Returns
        -------
        dict
            Extracted brand data including ``company_name``, ``colors``,
            ``fonts``, ``tone``, ``key_terminology``, and
            ``messaging_themes``.
        """
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            html_content = response.text

            # Truncate to avoid exceeding context limits
            max_chars = 50_000
            if len(html_content) > max_chars:
                html_content = html_content[:max_chars]

            prompt = self._build_url_extraction_prompt(html_content)

            claude_response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = claude_response.content[0].text
            data = self._parse_json_response(raw)

            data["source_url"] = url
            return data

        except requests.RequestException as exc:
            return {
                "company_name": "",
                "colors": {},
                "fonts": {},
                "tone": "",
                "key_terminology": [],
                "messaging_themes": [],
                "source_url": url,
                "error": f"Failed to fetch URL: {exc}",
            }
        except Exception as exc:
            return {
                "company_name": "",
                "colors": {},
                "fonts": {},
                "tone": "",
                "key_terminology": [],
                "messaging_themes": [],
                "source_url": url,
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Extraction from a logo
    # ------------------------------------------------------------------

    def extract_from_logo(self, logo_path: str) -> dict:
        """Extract brand colours from a logo image.

        Parameters
        ----------
        logo_path : str
            Path to the logo file.

        Returns
        -------
        dict
            ``{"colors_hex": [...], "categorized": {...}, "palette": {...}}``
        """
        try:
            colors = self.color_extractor.extract_from_image(logo_path, num_colors=6)
            categorized = self.color_extractor.categorize_colors(colors)
            palette = self.color_extractor.generate_color_palette(colors)

            # Compute accessibility info for primary text combinations
            accessibility: dict[str, float] = {}
            if categorized.get("primary") and categorized.get("background"):
                accessibility["primary_on_background"] = (
                    self.color_extractor.get_contrast_ratio(
                        categorized["primary"], categorized["background"]
                    )
                )
            if categorized.get("text") and categorized.get("background"):
                accessibility["text_on_background"] = (
                    self.color_extractor.get_contrast_ratio(
                        categorized["text"], categorized["background"]
                    )
                )

            return {
                "colors_hex": colors,
                "categorized": categorized,
                "palette": palette,
                "accessibility": accessibility,
                "source_logo": logo_path,
            }
        except Exception as exc:
            return {
                "colors_hex": [],
                "categorized": {},
                "palette": {},
                "accessibility": {},
                "source_logo": logo_path,
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Extraction from documents
    # ------------------------------------------------------------------

    def extract_from_documents(self, doc_paths: list[str]) -> dict:
        """Analyse brand voice from existing documents.

        Parameters
        ----------
        doc_paths : list[str]
            Paths to text / markdown files that represent the brand's
            existing content (marketing copy, blog posts, etc.).

        Returns
        -------
        dict
            Combined voice profile from ``VoiceAnalyzer``.
        """
        try:
            voice_profile = self.voice_analyzer.analyze_documents(doc_paths)
            voice_profile["source_documents"] = doc_paths
            return voice_profile
        except Exception as exc:
            return {
                "tone": "unknown",
                "formality": 3,
                "vocabulary_level": "intermediate",
                "key_phrases": [],
                "patterns": {},
                "messaging_themes": [],
                "source_documents": doc_paths,
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Compilation
    # ------------------------------------------------------------------

    def compile_brand_config(
        self,
        url_data: dict | None = None,
        logo_data: dict | None = None,
        doc_data: dict | None = None,
    ) -> dict:
        """Merge extraction results from all sources into a unified config.

        Parameters
        ----------
        url_data : dict | None
            Output of :meth:`extract_from_url`.
        logo_data : dict | None
            Output of :meth:`extract_from_logo`.
        doc_data : dict | None
            Output of :meth:`extract_from_documents`.

        Returns
        -------
        dict
            The canonical ``brand_config`` structure.
        """
        config = {
            "company_name": "",
            "colors": {
                "primary": "",
                "secondary": "",
                "background": "",
                "accent": "",
                "text": "",
            },
            "fonts": {
                "heading": "",
                "body": "",
            },
            "voice": {
                "tone": "",
                "formality": 3,
                "vocabulary_level": "",
                "key_phrases": [],
                "avoid_phrases": [],
                "messaging_themes": [],
            },
            "terminology": {
                "preferred_terms": {},
                "program_names": [],
                "acronyms": {},
            },
            "extracted_at": datetime.now(timezone.utc).isoformat(),
            "sources": [],
        }

        # --- Merge URL data ---
        if url_data:
            config["sources"].append(url_data.get("source_url", "url"))
            if url_data.get("company_name"):
                config["company_name"] = url_data["company_name"]

            # Colors from URL (CSS/mentioned)
            url_colors = url_data.get("colors", {})
            if isinstance(url_colors, dict):
                for key in ("primary", "secondary", "background", "accent", "text"):
                    if url_colors.get(key):
                        config["colors"][key] = url_colors[key]

            # Fonts from URL
            url_fonts = url_data.get("fonts", {})
            if isinstance(url_fonts, dict):
                if url_fonts.get("heading"):
                    config["fonts"]["heading"] = url_fonts["heading"]
                if url_fonts.get("body"):
                    config["fonts"]["body"] = url_fonts["body"]

            # Voice signals from URL
            if url_data.get("tone"):
                config["voice"]["tone"] = url_data["tone"]
            if url_data.get("messaging_themes"):
                config["voice"]["messaging_themes"] = url_data["messaging_themes"]

            # Terminology from URL
            if url_data.get("key_terminology"):
                terms = url_data["key_terminology"]
                if isinstance(terms, list):
                    for term in terms:
                        if isinstance(term, dict):
                            config["terminology"]["preferred_terms"].update(term)
                        elif isinstance(term, str):
                            config["terminology"]["preferred_terms"][term] = term

        # --- Merge logo data (overrides URL colors if available) ---
        if logo_data:
            config["sources"].append(logo_data.get("source_logo", "logo"))
            categorized = logo_data.get("categorized", {})
            if isinstance(categorized, dict):
                for key in ("primary", "secondary", "background", "accent", "text"):
                    if categorized.get(key):
                        config["colors"][key] = categorized[key]

        # --- Merge document data ---
        if doc_data:
            sources = doc_data.get("source_documents", [])
            if isinstance(sources, list):
                config["sources"].extend(sources)
            else:
                config["sources"].append("documents")

            if doc_data.get("tone") and doc_data["tone"] != "unknown":
                config["voice"]["tone"] = doc_data["tone"]
            if doc_data.get("formality"):
                config["voice"]["formality"] = doc_data["formality"]
            if doc_data.get("vocabulary_level"):
                config["voice"]["vocabulary_level"] = doc_data["vocabulary_level"]
            if doc_data.get("key_phrases"):
                # Merge without duplicates
                existing = set(config["voice"]["key_phrases"])
                for phrase in doc_data["key_phrases"]:
                    if phrase not in existing:
                        config["voice"]["key_phrases"].append(phrase)
                        existing.add(phrase)
            if doc_data.get("messaging_themes"):
                existing_themes = set(config["voice"]["messaging_themes"])
                for theme in doc_data["messaging_themes"]:
                    if theme not in existing_themes:
                        config["voice"]["messaging_themes"].append(theme)
                        existing_themes.add(theme)

        return config

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_brand_config(self, config: dict) -> str:
        """Save the brand configuration to ``brand_assets/brand_config.json``.

        Parameters
        ----------
        config : dict
            The brand configuration dictionary.

        Returns
        -------
        str
            The filesystem path where the config was saved.
        """
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return str(self.config_path)

    def load_brand_config(self) -> dict:
        """Load the existing brand configuration from disk.

        Returns
        -------
        dict
            The brand configuration, or an empty dict if the file does
            not exist or cannot be parsed.
        """
        if not self.config_path.exists():
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_url_extraction_prompt(self, html_content: str) -> str:
        """Build the Claude prompt for extracting brand signals from HTML."""
        return f"""Analyse the following HTML from a company website and extract brand identity information.
Return ONLY valid JSON (no markdown fences, no explanation) with these exact keys:

{{
  "company_name": "<the company or brand name>",
  "colors": {{
    "primary": "<hex color if detectable from CSS or meta>",
    "secondary": "<hex color>",
    "background": "<hex color>",
    "accent": "<hex color>",
    "text": "<hex color>"
  }},
  "fonts": {{
    "heading": "<font family name if detectable>",
    "body": "<font family name if detectable>"
  }},
  "tone": "<one of: professional, casual, friendly, authoritative, inspirational, empathetic, playful, formal>",
  "key_terminology": ["<industry-specific or brand-specific terms used>"],
  "messaging_themes": ["<main value propositions and messaging themes>"]
}}

If a value cannot be determined, use an empty string for strings or an empty list for arrays.

--- HTML CONTENT ---
{html_content}
--- END HTML ---"""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json_response(raw_text: str) -> dict:
        """Attempt to extract a JSON object from Claude's response."""
        text = raw_text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
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
