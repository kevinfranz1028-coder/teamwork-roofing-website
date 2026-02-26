"""
Brand Intelligence Content Hub - Translation Engine

Multi-language translation with brand terminology preservation.
Uses DeepL as the primary provider (faster, cheaper) and falls back
to Claude when DeepL is unavailable.  Brand terms (company names,
product names, acronyms) are shielded via placeholder substitution,
translated, and restored -- with optional Claude verification.
"""

import hashlib
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.config import BASE_DIR, BRAND_ASSETS_DIR, TRANSLATIONS_DIR, get_env
from app.database.models import get_session, GeneratedContent, BrandConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Optional third-party imports
# ---------------------------------------------------------------------------

try:
    import deepl
    DEEPL_AVAILABLE = True
except ImportError:
    DEEPL_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None
    ANTHROPIC_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from pptx import Presentation as PptxPresentation
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLAUDE_MODEL = "claude-sonnet-4-20250514"

SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "it": "Italian",
    "nl": "Dutch",
    "pl": "Polish",
    "ja": "Japanese",
    "zh": "Chinese (Simplified)",
    "ko": "Korean",
    "ar": "Arabic",
    "ru": "Russian",
    "tr": "Turkish",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "nb": "Norwegian",
    "ro": "Romanian",
    "hu": "Hungarian",
    "cs": "Czech",
    "sk": "Slovak",
    "bg": "Bulgarian",
    "el": "Greek",
    "id": "Indonesian",
    "uk": "Ukrainian",
}

# DeepL uses slightly different language codes for some locales
DEEPL_LANG_MAP = {
    "en": "EN-US", "pt": "PT-BR", "zh": "ZH",
    "es": "ES", "fr": "FR", "de": "DE", "it": "IT", "nl": "NL",
    "pl": "PL", "ja": "JA", "ko": "KO", "ru": "RU", "tr": "TR",
    "sv": "SV", "da": "DA", "fi": "FI", "nb": "NB", "ro": "RO",
    "hu": "HU", "cs": "CS", "sk": "SK", "bg": "BG", "el": "EL",
    "id": "ID", "uk": "UK", "ar": "AR",
}

# DeepL source language codes (no region variant needed)
DEEPL_SOURCE_LANG_MAP = {
    "en": "EN", "pt": "PT", "zh": "ZH",
    "es": "ES", "fr": "FR", "de": "DE", "it": "IT", "nl": "NL",
    "pl": "PL", "ja": "JA", "ko": "KO", "ru": "RU", "tr": "TR",
    "sv": "SV", "da": "DA", "fi": "FI", "nb": "NB", "ro": "RO",
    "hu": "HU", "cs": "CS", "sk": "SK", "bg": "BG", "el": "EL",
    "id": "ID", "uk": "UK", "ar": "AR",
}

# Patterns for content that should NOT be translated
_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_FILE_PATH_RE = re.compile(r"(?:[A-Za-z]:\\|/)[^\s]+\.\w{1,5}")
_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")
_EMAIL_RE = re.compile(r"\S+@\S+\.\S+")


# ---------------------------------------------------------------------------
# TranslationEngine
# ---------------------------------------------------------------------------

class TranslationEngine:
    """Multi-provider translation engine with brand terminology preservation."""

    def __init__(self):
        # --- DeepL ----------------------------------------------------------
        self._deepl_client = None
        self._deepl_api_key = get_env("DEEPL_API_KEY")
        if DEEPL_AVAILABLE and self._deepl_api_key:
            try:
                self._deepl_client = deepl.Translator(self._deepl_api_key)
                logger.info("DeepL translator initialised")
            except Exception as exc:
                logger.warning("Failed to initialise DeepL: %s", exc)

        # --- Anthropic / Claude ---------------------------------------------
        self._anthropic_client = None
        self._anthropic_api_key = get_env("ANTHROPIC_API_KEY") or os.getenv(
            "ANTHROPIC_API_KEY", ""
        )
        if ANTHROPIC_AVAILABLE and self._anthropic_api_key:
            try:
                self._anthropic_client = Anthropic(api_key=self._anthropic_api_key)
                logger.info("Anthropic client initialised for translation")
            except Exception as exc:
                logger.warning("Failed to initialise Anthropic client: %s", exc)

        # --- Brand terminology ----------------------------------------------
        self._brand_terms: list[str] = []
        try:
            self._brand_terms = self.load_brand_terminology()
        except Exception as exc:
            logger.debug("Could not load brand terminology at init: %s", exc)

        # --- Ensure output directory ----------------------------------------
        TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)

    # ===================================================================
    #  PUBLIC API -- Single-text Translation
    # ===================================================================

    def translate_text(self, text: str, target_lang: str,
                       source_lang: str = "en",
                       preserve_brand_terms: bool = True) -> dict:
        """Translate text using DeepL (primary) or Claude (fallback).

        Returns
        -------
        dict
            {'success': bool, 'translated_text': str, 'source_lang': str,
             'target_lang': str, 'provider': str,
             'brand_terms_preserved': list, 'error': str | None}
        """
        if not text or not text.strip():
            return self._error_result("Input text is empty", source_lang, target_lang)

        if target_lang not in SUPPORTED_LANGUAGES:
            return self._error_result(
                f"Unsupported target language: '{target_lang}'. "
                f"Supported: {list(SUPPORTED_LANGUAGES.keys())}",
                source_lang, target_lang,
            )

        if source_lang == target_lang:
            return {
                "success": True, "translated_text": text,
                "source_lang": source_lang, "target_lang": target_lang,
                "provider": "passthrough", "brand_terms_preserved": [],
                "error": None,
            }

        # --- Translation memory lookup -------------------------------------
        cached = self._lookup_translation(text, source_lang, target_lang)
        if cached is not None:
            logger.debug("Translation memory hit (%s->%s)", source_lang, target_lang)
            return {
                "success": True, "translated_text": cached,
                "source_lang": source_lang, "target_lang": target_lang,
                "provider": "memory", "brand_terms_preserved": [],
                "error": None,
            }

        # --- Brand term placeholders ---------------------------------------
        brand_terms: list[str] = []
        placeholders: dict[str, str] = {}
        working_text = text
        if preserve_brand_terms:
            brand_terms = [t for t in self._brand_terms if t.lower() in text.lower()]
            if brand_terms:
                working_text, placeholders = self._replace_brand_terms(text, brand_terms)

        # --- Attempt translation -------------------------------------------
        translated: Optional[str] = None
        provider = ""

        if self._deepl_client and target_lang in DEEPL_LANG_MAP:
            try:
                translated = self._translate_deepl(working_text, target_lang, source_lang)
                provider = "deepl"
            except Exception as exc:
                logger.warning("DeepL translation failed: %s", exc)

        if translated is None and self._anthropic_client:
            try:
                translated = self._translate_claude(
                    working_text, target_lang, source_lang, brand_terms
                )
                provider = "claude"
            except Exception as exc:
                logger.warning("Claude translation failed: %s", exc)

        if translated is None:
            return self._error_result(
                "No translation provider available. Configure DEEPL_API_KEY "
                "or ANTHROPIC_API_KEY in your .env file.",
                source_lang, target_lang,
            )

        # --- Restore placeholders & verify ---------------------------------
        if placeholders:
            translated = self._restore_brand_terms(translated, placeholders)

        if brand_terms and self._anthropic_client and provider != "claude":
            try:
                translated = self._post_process_brand_terms(
                    translated, brand_terms, text
                )
            except Exception as exc:
                logger.debug("Brand term post-processing skipped: %s", exc)

        # --- Save to memory ------------------------------------------------
        try:
            self._save_translation(text, translated, source_lang, target_lang)
        except Exception as exc:
            logger.debug("Could not save translation to memory: %s", exc)

        return {
            "success": True, "translated_text": translated,
            "source_lang": source_lang, "target_lang": target_lang,
            "provider": provider, "brand_terms_preserved": brand_terms,
            "error": None,
        }

    # -------------------------------------------------------------------
    #  Provider: DeepL
    # -------------------------------------------------------------------

    def _translate_deepl(self, text: str, target_lang: str,
                         source_lang: str) -> str:
        """Translate via DeepL API."""
        if not self._deepl_client:
            raise RuntimeError("DeepL client is not initialised")

        deepl_target = DEEPL_LANG_MAP.get(target_lang, target_lang.upper())
        deepl_source = DEEPL_SOURCE_LANG_MAP.get(source_lang, source_lang.upper())

        result = self._deepl_client.translate_text(
            text, source_lang=deepl_source, target_lang=deepl_target,
        )
        translated = result.text if hasattr(result, "text") else str(result)
        logger.info("DeepL translation completed (%s -> %s, %d chars)",
                     source_lang, target_lang, len(translated))
        return translated

    # -------------------------------------------------------------------
    #  Provider: Claude
    # -------------------------------------------------------------------

    def _translate_claude(self, text: str, target_lang: str,
                          source_lang: str,
                          brand_terms: list | None = None) -> str:
        """Translate via Claude with brand terminology awareness.

        Uses a prompt that instructs Claude to:
        - Translate naturally while preserving meaning
        - Keep brand names, program names, and acronyms untranslated
        - Maintain formatting (markdown, bullet points, etc.)
        """
        if not self._anthropic_client:
            raise RuntimeError("Anthropic client is not initialised")

        target_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)
        source_name = SUPPORTED_LANGUAGES.get(source_lang, source_lang)

        brand_instruction = ""
        if brand_terms:
            terms_csv = ", ".join(f'"{t}"' for t in brand_terms)
            brand_instruction = (
                f"\n\nIMPORTANT: The following brand terms must NOT be "
                f"translated. Keep them exactly as-is:\n{terms_csv}"
            )

        system_prompt = (
            "You are a professional translator. Produce natural, fluent "
            "translations while preserving meaning, tone, and formatting.\n\n"
            "Rules:\n"
            "1. Translate naturally -- no word-for-word literal output.\n"
            "2. Preserve all formatting: markdown, bullets, headings, links.\n"
            "3. Keep brand names, product names, and acronyms untranslated.\n"
            "4. Maintain paragraph structure and line breaks.\n"
            "5. Return ONLY the translated text, no preamble or commentary."
            f"{brand_instruction}"
        )

        user_prompt = (
            f"Translate from {source_name} to {target_name}.\n\n"
            f"---\n{text}\n---"
        )

        try:
            response = self._anthropic_client.messages.create(
                model=CLAUDE_MODEL, max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            translated = response.content[0].text.strip()
            logger.info("Claude translation completed (%s -> %s, %d chars)",
                         source_lang, target_lang, len(translated))
            return translated
        except Exception as exc:
            logger.error("Claude translation API call failed: %s", exc)
            raise RuntimeError(f"Claude translation failed: {exc}") from exc

    # -------------------------------------------------------------------
    #  Brand Term Post-processing
    # -------------------------------------------------------------------

    def _post_process_brand_terms(self, translated_text: str,
                                   brand_terms: list,
                                   original_text: str) -> str:
        """Use Claude to verify brand terms weren't translated.

        Compares translated text against brand term list and fixes any
        terms that were incorrectly translated.
        """
        if not self._anthropic_client or not brand_terms:
            return translated_text

        # Quick check: are all brand terms already present?
        if all(term in translated_text for term in brand_terms):
            return translated_text

        terms_csv = ", ".join(f'"{t}"' for t in brand_terms)
        prompt = (
            "You are a translation QA assistant.\n\n"
            "Some brand terms may have been incorrectly translated below. "
            "Find any translated brand terms and restore them to their "
            "original form.\n\n"
            f"Brand terms that MUST appear verbatim: {terms_csv}\n\n"
            f"Original text:\n---\n{original_text}\n---\n\n"
            f"Translated text:\n---\n{translated_text}\n---\n\n"
            "Return ONLY the corrected translated text."
        )

        try:
            response = self._anthropic_client.messages.create(
                model=CLAUDE_MODEL, max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as exc:
            logger.warning("Brand term post-processing failed: %s", exc)
            return translated_text

    # ===================================================================
    #  Structured Content Translation
    # ===================================================================

    def translate_structured_content(self, content: dict, target_lang: str,
                                      source_lang: str = "en") -> dict:
        """Translate structured content (slides, sections) preserving structure.

        Recursively walks the dict/list structure, translating string values
        while preserving keys, numbers, and booleans.
        """
        if not content:
            return content
        return self._translate_recursive(content, target_lang, source_lang)

    def _translate_recursive(self, obj: Any, target_lang: str,
                              source_lang: str) -> Any:
        """Recursively translate translatable string values in *obj*."""
        if isinstance(obj, dict):
            return {k: self._translate_recursive(v, target_lang, source_lang)
                    for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._translate_recursive(i, target_lang, source_lang)
                    for i in obj]
        if isinstance(obj, str) and self._should_translate_string(obj):
            result = self.translate_text(obj, target_lang, source_lang)
            if result["success"]:
                return result["translated_text"]
        return obj

    @staticmethod
    def _should_translate_string(value: str) -> bool:
        """Return True if *value* looks like natural language to translate.

        Returns False for short strings (<3 chars), URLs, file paths,
        hex colours, emails, and programmatic identifiers.
        """
        s = value.strip()
        if len(s) < 3:
            return False
        if re.match(r"^[\d.,\s%$+-]+$", s):
            return False
        if _URL_RE.match(s):
            return False
        if _FILE_PATH_RE.match(s):
            return False
        if _HEX_COLOR_RE.match(s):
            return False
        if _EMAIL_RE.match(s):
            return False
        if " " not in s and ("_" in s or s.startswith(".")):
            return False
        return True

    # ===================================================================
    #  Document Translation
    # ===================================================================

    def translate_document(self, file_path: str, target_lang: str,
                           source_lang: str = "en") -> dict:
        """Translate a DOCX, PPTX, or plain-text file.

        For DOCX: extracts paragraphs, translates each, creates new DOCX.
        For PPTX: extracts slide text, translates, creates new PPTX.
        For plain text: translates directly.

        Returns
        -------
        dict
            {'success': bool, 'output_path': str, 'original_path': str,
             'target_lang': str, 'word_count': int, 'error': str}
        """
        src = Path(file_path)
        if not src.exists():
            return self._doc_error(src, target_lang,
                                   f"Source file not found: {file_path}")

        suffix = src.suffix.lower()
        if suffix == ".docx":
            return self._translate_docx(src, target_lang, source_lang)
        elif suffix == ".pptx":
            return self._translate_pptx(src, target_lang, source_lang)
        elif suffix in (".txt", ".md", ".csv", ".html", ".xml"):
            return self._translate_plaintext(src, target_lang, source_lang)
        else:
            return self._doc_error(
                src, target_lang,
                f"Unsupported file type: '{suffix}'. "
                "Supported: .docx, .pptx, .txt, .md",
            )

    # -------------------------------------------------------------------
    #  DOCX translation
    # -------------------------------------------------------------------

    def _translate_docx(self, src: Path, target_lang: str,
                        source_lang: str) -> dict:
        """Translate a DOCX file paragraph-by-paragraph."""
        if not DOCX_AVAILABLE:
            return self._doc_error(
                src, target_lang,
                "python-docx is not installed. pip install python-docx",
            )
        try:
            doc = DocxDocument(str(src))
        except Exception as exc:
            return self._doc_error(src, target_lang,
                                   f"Failed to open DOCX: {exc}")

        word_count = 0
        try:
            # Paragraphs in document body
            for para in doc.paragraphs:
                wc = self._translate_paragraph_runs(para, target_lang, source_lang)
                word_count += wc

            # Paragraphs inside tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            wc = self._translate_paragraph_runs(
                                para, target_lang, source_lang
                            )
                            word_count += wc
        except Exception as exc:
            return self._doc_error(src, target_lang,
                                   f"Error during DOCX translation: {exc}",
                                   word_count)

        return self._save_translated_doc(doc, src, target_lang, word_count, "docx")

    def _translate_paragraph_runs(self, paragraph, target_lang: str,
                                   source_lang: str) -> int:
        """Translate a paragraph's text in-place, preserving run formatting.

        Returns the word count of the original text (0 if skipped).
        """
        original = paragraph.text
        if not original or not original.strip():
            return 0
        if not self._should_translate_string(original):
            return 0

        result = self.translate_text(original, target_lang, source_lang)
        if not result["success"]:
            return 0

        translated = result["translated_text"]
        if paragraph.runs:
            paragraph.runs[0].text = translated
            for run in paragraph.runs[1:]:
                run.text = ""
        else:
            paragraph.text = translated
        return len(original.split())

    # -------------------------------------------------------------------
    #  PPTX translation
    # -------------------------------------------------------------------

    def _translate_pptx(self, src: Path, target_lang: str,
                        source_lang: str) -> dict:
        """Translate a PPTX file slide-by-slide."""
        if not PPTX_AVAILABLE:
            return self._doc_error(
                src, target_lang,
                "python-pptx is not installed. pip install python-pptx",
            )
        try:
            prs = PptxPresentation(str(src))
        except Exception as exc:
            return self._doc_error(src, target_lang,
                                   f"Failed to open PPTX: {exc}")

        word_count = 0
        try:
            for slide in prs.slides:
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for para in shape.text_frame.paragraphs:
                            wc = self._translate_pptx_paragraph(
                                para, target_lang, source_lang
                            )
                            word_count += wc
                    if shape.has_table:
                        for row in shape.table.rows:
                            for cell in row.cells:
                                for para in cell.text_frame.paragraphs:
                                    wc = self._translate_pptx_paragraph(
                                        para, target_lang, source_lang
                                    )
                                    word_count += wc
        except Exception as exc:
            return self._doc_error(src, target_lang,
                                   f"Error during PPTX translation: {exc}",
                                   word_count)

        return self._save_translated_doc(prs, src, target_lang, word_count, "pptx")

    def _translate_pptx_paragraph(self, paragraph, target_lang: str,
                                   source_lang: str) -> int:
        """Translate a PPTX paragraph in-place. Returns source word count."""
        original = paragraph.text
        if not original or not original.strip():
            return 0
        if not self._should_translate_string(original):
            return 0
        result = self.translate_text(original, target_lang, source_lang)
        if not result["success"]:
            return 0
        if paragraph.runs:
            paragraph.runs[0].text = result["translated_text"]
            for run in paragraph.runs[1:]:
                run.text = ""
        return len(original.split())

    # -------------------------------------------------------------------
    #  Plain-text translation
    # -------------------------------------------------------------------

    def _translate_plaintext(self, src: Path, target_lang: str,
                              source_lang: str) -> dict:
        """Translate a plain-text / Markdown file."""
        try:
            original = src.read_text(encoding="utf-8")
        except Exception as exc:
            return self._doc_error(src, target_lang, f"Failed to read file: {exc}")

        if not original.strip():
            return self._doc_error(src, target_lang, "Source file is empty")

        word_count = len(original.split())
        result = self.translate_text(original, target_lang, source_lang)
        if not result["success"]:
            return self._doc_error(src, target_lang,
                                   result.get("error", "Translation failed"),
                                   word_count)

        output_name = f"{src.stem}_{target_lang}{src.suffix}"
        output_path = TRANSLATIONS_DIR / output_name
        try:
            output_path.write_text(result["translated_text"], encoding="utf-8")
            logger.info("Text file translated: %s -> %s (%d words)",
                         src.name, output_name, word_count)
            return {
                "success": True, "output_path": str(output_path),
                "original_path": str(src), "target_lang": target_lang,
                "word_count": word_count, "error": None,
            }
        except Exception as exc:
            return self._doc_error(src, target_lang,
                                   f"Failed to write translated file: {exc}",
                                   word_count)

    # -------------------------------------------------------------------
    #  Document save / error helpers
    # -------------------------------------------------------------------

    def _save_translated_doc(self, doc_obj, src: Path, target_lang: str,
                              word_count: int, ext: str) -> dict:
        """Save a translated DOCX/PPTX object to TRANSLATIONS_DIR."""
        output_name = f"{src.stem}_{target_lang}.{ext}"
        output_path = TRANSLATIONS_DIR / output_name
        try:
            doc_obj.save(str(output_path))
            logger.info("%s translated: %s -> %s (%d words)",
                         ext.upper(), src.name, output_name, word_count)
            return {
                "success": True, "output_path": str(output_path),
                "original_path": str(src), "target_lang": target_lang,
                "word_count": word_count, "error": None,
            }
        except Exception as exc:
            return self._doc_error(
                src, target_lang,
                f"Failed to save translated {ext.upper()}: {exc}",
                word_count,
            )

    @staticmethod
    def _doc_error(src: Path, target_lang: str, error: str,
                   word_count: int = 0) -> dict:
        """Build a standard error result for document translation."""
        return {
            "success": False, "output_path": None,
            "original_path": str(src), "target_lang": target_lang,
            "word_count": word_count, "error": error,
        }

    # ===================================================================
    #  Batch Translation
    # ===================================================================

    def batch_translate(self, text: str, target_langs: list,
                        source_lang: str = "en") -> dict:
        """Translate text into multiple languages at once.

        Returns
        -------
        dict
            {'success': bool, 'translations': {lang: text, ...},
             'failed': {lang: error, ...}}
        """
        if not text or not text.strip():
            return {
                "success": False, "translations": {},
                "failed": {l: "Input text is empty" for l in target_langs},
            }

        translations: dict[str, str] = {}
        failed: dict[str, str] = {}

        for lang in target_langs:
            logger.info("Batch translating to %s (%s)",
                         lang, SUPPORTED_LANGUAGES.get(lang, lang))
            result = self.translate_text(text, lang, source_lang)
            if result["success"]:
                translations[lang] = result["translated_text"]
            else:
                failed[lang] = result.get("error", "Unknown error")

        return {
            "success": len(translations) > 0,
            "translations": translations,
            "failed": failed,
        }

    def batch_translate_document(self, file_path: str, target_langs: list,
                                  source_lang: str = "en") -> dict:
        """Translate a document into multiple languages.

        Creates one output file per language in TRANSLATIONS_DIR.

        Returns
        -------
        dict
            {'success': bool, 'outputs': {lang: path, ...},
             'failed': {lang: error, ...}}
        """
        if not Path(file_path).exists():
            return {
                "success": False, "outputs": {},
                "failed": {l: f"Source file not found: {file_path}"
                           for l in target_langs},
            }

        outputs: dict[str, str] = {}
        failed: dict[str, str] = {}

        for lang in target_langs:
            logger.info("Batch document translation: %s -> %s",
                         Path(file_path).name, lang)
            result = self.translate_document(file_path, lang, source_lang)
            if result["success"]:
                outputs[lang] = result["output_path"]
            else:
                failed[lang] = result.get("error", "Unknown error")

        return {"success": len(outputs) > 0, "outputs": outputs, "failed": failed}

    # ===================================================================
    #  Brand Terminology Management
    # ===================================================================

    def load_brand_terminology(self) -> list:
        """Load brand terms from brand_config.json (terminology section)
        and BrandConfig table. These terms should NOT be translated.

        Returns list of term strings.
        """
        terms: list[str] = []

        # --- Source 1: brand_config.json ------------------------------------
        config_path = BRAND_ASSETS_DIR / "brand_config.json"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                terminology = config.get("terminology", {})
                for key in ("brand_terms", "do_not_translate", "product_names",
                            "program_names", "acronyms"):
                    items = terminology.get(key, [])
                    if isinstance(items, list):
                        terms.extend(items)

                company = config.get("company_name") or config.get("brand_name")
                if company and isinstance(company, str):
                    terms.append(company)
            except (json.JSONDecodeError, OSError) as exc:
                logger.debug("Could not load brand_config.json: %s", exc)

        # --- Source 2: BrandConfig table ------------------------------------
        try:
            session = get_session()
            rows = (
                session.query(BrandConfig)
                .filter(BrandConfig.config_key.like("brand_term_%"))
                .all()
            )
            for row in rows:
                if row.config_value:
                    terms.append(row.config_value.strip())

            glossary_row = (
                session.query(BrandConfig)
                .filter(BrandConfig.config_key == "translation_glossary")
                .first()
            )
            if glossary_row and glossary_row.config_value:
                try:
                    glossary = json.loads(glossary_row.config_value)
                    if isinstance(glossary, list):
                        terms.extend(glossary)
                except json.JSONDecodeError:
                    pass
            session.close()
        except Exception as exc:
            logger.debug("Could not load brand terms from database: %s", exc)

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for term in terms:
            t = term.strip()
            if t and t.lower() not in seen:
                seen.add(t.lower())
                unique.append(t)

        logger.info("Loaded %d brand terms for translation glossary", len(unique))
        self._brand_terms = unique
        return unique

    def add_brand_term(self, term: str) -> bool:
        """Add a term to the brand terminology glossary."""
        term = term.strip()
        if not term:
            return False
        if term.lower() in {t.lower() for t in self._brand_terms}:
            return False

        try:
            session = get_session()
            count = (session.query(BrandConfig)
                     .filter(BrandConfig.config_key.like("brand_term_%"))
                     .count())
            new_key = f"brand_term_{count + 1:04d}"
            session.add(BrandConfig(config_key=new_key, config_value=term))
            session.commit()
            session.close()
            self._brand_terms.append(term)
            logger.info("Added brand term: '%s' (key=%s)", term, new_key)
            return True
        except Exception as exc:
            logger.error("Failed to add brand term '%s': %s", term, exc)
            return False

    def remove_brand_term(self, term: str) -> bool:
        """Remove a term from the glossary."""
        term = term.strip()
        if not term:
            return False

        original_len = len(self._brand_terms)
        self._brand_terms = [t for t in self._brand_terms
                             if t.lower() != term.lower()]
        removed = len(self._brand_terms) < original_len

        try:
            session = get_session()
            rows = (session.query(BrandConfig)
                    .filter(BrandConfig.config_key.like("brand_term_%"))
                    .filter(BrandConfig.config_value == term)
                    .all())
            for row in rows:
                session.delete(row)
                removed = True
            session.commit()
            session.close()
            if removed:
                logger.info("Removed brand term: '%s'", term)
        except Exception as exc:
            logger.error("Failed to remove brand term '%s': %s", term, exc)

        return removed

    def get_brand_terms(self) -> list:
        """Return current list of brand terms."""
        return list(self._brand_terms)

    # ===================================================================
    #  Translation Memory
    # ===================================================================

    def _save_translation(self, original: str, translated: str,
                          source_lang: str, target_lang: str) -> None:
        """Save translation to BrandConfig for reuse (translation memory).

        Key: 'translation_{source}_{target}_{sha256}'
        """
        text_hash = hashlib.sha256(original.encode("utf-8")).hexdigest()
        config_key = f"translation_{source_lang}_{target_lang}_{text_hash}"

        try:
            session = get_session()
            existing = (session.query(BrandConfig)
                        .filter(BrandConfig.config_key == config_key)
                        .first())
            if existing:
                existing.config_value = translated
                existing.updated_at = datetime.utcnow()
            else:
                session.add(BrandConfig(config_key=config_key,
                                        config_value=translated))
            session.commit()
            session.close()
            logger.debug("Saved translation to memory: %s", config_key[:60])
        except Exception as exc:
            logger.debug("Failed to save translation memory: %s", exc)

    def _lookup_translation(self, text: str, source_lang: str,
                            target_lang: str) -> str | None:
        """Check if we've translated this exact text before."""
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        config_key = f"translation_{source_lang}_{target_lang}_{text_hash}"

        try:
            session = get_session()
            row = (session.query(BrandConfig)
                   .filter(BrandConfig.config_key == config_key)
                   .first())
            session.close()
            if row and row.config_value:
                return row.config_value
        except Exception as exc:
            logger.debug("Translation memory lookup failed: %s", exc)
        return None

    # ===================================================================
    #  Brand Term Placeholder Helpers
    # ===================================================================

    @staticmethod
    def _replace_brand_terms(text: str, brand_terms: list) -> tuple[str, dict]:
        """Replace brand terms with <<BRAND_TERM_NNN>> placeholders.

        Sorts terms by length descending to prevent partial-match issues.
        """
        placeholders: dict[str, str] = {}
        working = text
        sorted_terms = sorted(brand_terms, key=len, reverse=True)

        for idx, term in enumerate(sorted_terms):
            placeholder = f"<<BRAND_TERM_{idx:03d}>>"
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            if pattern.search(working):
                working = pattern.sub(placeholder, working)
                placeholders[placeholder] = term

        return working, placeholders

    @staticmethod
    def _restore_brand_terms(text: str, placeholders: dict) -> str:
        """Restore <<BRAND_TERM_NNN>> placeholders to original terms."""
        result = text
        for placeholder, original in placeholders.items():
            result = result.replace(placeholder, original)
        return result

    # ===================================================================
    #  Utility Methods
    # ===================================================================

    def check_providers(self) -> dict:
        """Check which translation providers are available.

        Returns {'deepl': bool, 'claude': bool, 'any_available': bool,
                 'deepl_usage': {...} or None}
        """
        deepl_ok = self._deepl_client is not None
        claude_ok = self._anthropic_client is not None
        deepl_usage = None

        if deepl_ok:
            try:
                usage = self._deepl_client.get_usage()
                deepl_usage = {
                    "character_count": getattr(usage, "character", None),
                    "character_limit": getattr(usage, "character_limit", None),
                }
                if hasattr(usage, "character"):
                    char_usage = usage.character
                    if hasattr(char_usage, "count") and hasattr(char_usage, "limit"):
                        deepl_usage = {
                            "character_count": char_usage.count,
                            "character_limit": char_usage.limit,
                        }
            except Exception as exc:
                logger.debug("Could not fetch DeepL usage: %s", exc)
                deepl_usage = {"error": str(exc)}

        return {
            "deepl": deepl_ok, "claude": claude_ok,
            "any_available": deepl_ok or claude_ok,
            "deepl_usage": deepl_usage,
        }

    def detect_language(self, text: str) -> dict:
        """Detect the language of input text.

        Uses DeepL if available, otherwise Claude.
        Returns {'language': 'en', 'language_name': 'English',
                 'confidence': 0.95}
        """
        if not text or not text.strip():
            return {"language": "unknown", "language_name": "Unknown",
                    "confidence": 0.0}

        # --- DeepL detection -----------------------------------------------
        if self._deepl_client:
            try:
                result = self._deepl_client.translate_text(
                    text[:200], target_lang="EN-US",
                )
                detected = str(result.detected_source_lang).lower()
                if "-" in detected:
                    detected = detected.split("-")[0]
                return {
                    "language": detected,
                    "language_name": SUPPORTED_LANGUAGES.get(detected, detected),
                    "confidence": 0.95,
                }
            except Exception as exc:
                logger.debug("DeepL language detection failed: %s", exc)

        # --- Claude detection ----------------------------------------------
        if self._anthropic_client:
            try:
                prompt = (
                    "Identify the language of the following text. "
                    "Respond with ONLY a JSON object:\n"
                    '{"language": "<ISO 639-1 code>", '
                    '"language_name": "<English name>", '
                    '"confidence": <0-1 float>}\n\n'
                    f"Text:\n---\n{text[:500]}\n---"
                )
                response = self._anthropic_client.messages.create(
                    model=CLAUDE_MODEL, max_tokens=256,
                    messages=[{"role": "user", "content": prompt}],
                )
                parsed = self._parse_json_response(response.content[0].text)
                if parsed and isinstance(parsed, dict):
                    code = parsed.get("language", "unknown")
                    return {
                        "language": code,
                        "language_name": parsed.get(
                            "language_name",
                            SUPPORTED_LANGUAGES.get(code, code)),
                        "confidence": float(parsed.get("confidence", 0.8)),
                    }
            except Exception as exc:
                logger.debug("Claude language detection failed: %s", exc)

        return {"language": "unknown", "language_name": "Unknown",
                "confidence": 0.0}

    def get_supported_languages(self) -> dict:
        """Return the SUPPORTED_LANGUAGES dict."""
        return dict(SUPPORTED_LANGUAGES)

    # -------------------------------------------------------------------
    #  JSON response parsing
    # -------------------------------------------------------------------

    def _parse_json_response(self, text: str) -> dict | list | None:
        """Strip markdown fences and parse JSON from Claude responses."""
        if not text:
            return None

        cleaned = text.strip()

        # Remove markdown code fences
        if cleaned.startswith("```"):
            first_nl = cleaned.find("\n")
            if first_nl != -1:
                cleaned = cleaned[first_nl + 1:]
            if cleaned.rstrip().endswith("```"):
                cleaned = cleaned.rstrip()[:-3].rstrip()

        # Direct parse
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Search for JSON object or array
        for sc, ec in [("{", "}"), ("[", "]")]:
            si = cleaned.find(sc)
            ei = cleaned.rfind(ec)
            if si != -1 and ei > si:
                try:
                    return json.loads(cleaned[si:ei + 1])
                except json.JSONDecodeError:
                    continue

        logger.warning("Could not parse JSON from Claude response (len=%d)",
                        len(text))
        return None

    # -------------------------------------------------------------------
    #  Error result helpers
    # -------------------------------------------------------------------

    @staticmethod
    def _error_result(error_msg: str, source_lang: str,
                      target_lang: str) -> dict:
        """Build a standard error result for translate_text."""
        return {
            "success": False, "translated_text": "",
            "source_lang": source_lang, "target_lang": target_lang,
            "provider": "", "brand_terms_preserved": [],
            "error": error_msg,
        }

    # -------------------------------------------------------------------
    #  Dunder helpers
    # -------------------------------------------------------------------

    def __repr__(self) -> str:
        d = "available" if self._deepl_client else "unavailable"
        c = "available" if self._anthropic_client else "unavailable"
        return (f"TranslationEngine(deepl={d}, claude={c}, "
                f"brand_terms={len(self._brand_terms)})")
