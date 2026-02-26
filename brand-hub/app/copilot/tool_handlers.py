"""
Brand Intelligence Content Hub - Copilot Tool Handlers

Dispatches Copilot tool calls to real application functions.
When Claude returns a ``tool_use`` block, :func:`execute_tool` runs
the matching handler and returns a JSON-serializable string that
becomes the ``tool_result`` content sent back to Claude.
"""

import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import (
    BASE_DIR,
    BRAND_ASSETS_DIR,
    OUTPUT_DIR,
    PRESENTATIONS_DIR,
    DOCUMENTS_DIR,
    TRAINING_DIR,
    VISUALS_DIR,
    TRANSLATIONS_DIR,
)
from app.database.models import (
    get_session,
    BrandAsset,
    BrandConfig,
    GeneratedContent,
    ContentLibraryItem,
    Template,
    BatchJob,
    PromptTemplate,
)

# ---------------------------------------------------------------------------
# Optional generator / module imports -- wrapped so the copilot still loads
# even when a particular dependency is missing.
# ---------------------------------------------------------------------------

try:
    from app.generators.presentation_gen import BrandedPresentationGenerator
except ImportError:
    BrandedPresentationGenerator = None  # type: ignore[assignment,misc]

try:
    from app.generators.document_gen import BrandedDocumentGenerator, DOCUMENT_TEMPLATES
except ImportError:
    BrandedDocumentGenerator = None  # type: ignore[assignment,misc]
    DOCUMENT_TEMPLATES = {}  # type: ignore[assignment]

try:
    from app.generators.visual_gen import VisualPipeline
except ImportError:
    VisualPipeline = None  # type: ignore[assignment,misc]

try:
    from app.generators.training_pipeline import TrainingPipeline, PipelineOptions
except ImportError:
    TrainingPipeline = None  # type: ignore[assignment,misc]
    PipelineOptions = None  # type: ignore[assignment,misc]

try:
    from app.integrations.translation_client import TranslationEngine
except ImportError:
    TranslationEngine = None  # type: ignore[assignment,misc]

try:
    from app.brand.asset_manager import AssetManager
except ImportError:
    AssetManager = None  # type: ignore[assignment,misc]

try:
    from app.database.vector_store import VectorStore
except ImportError:
    VectorStore = None  # type: ignore[assignment,misc]

try:
    from app.utils.analytics import AnalyticsEngine
except ImportError:
    AnalyticsEngine = None  # type: ignore[assignment,misc]

# Ingestion parsers (for reading source files)
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

# Anthropic SDK for content generation sub-calls
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # type: ignore[assignment,misc]

try:
    from app.copilot.audit_log import AuditLog
except ImportError:
    AuditLog = None

try:
    from app.integrations.napkin_client import NapkinClient
    _NAPKIN_OK = True
except ImportError:
    _NAPKIN_OK = False

try:
    from app.database.models import BrandProfile
except ImportError:
    BrandProfile = None

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLAUDE_MODEL = "claude-sonnet-4-20250514"
BRAND_CONFIG_PATH = BRAND_ASSETS_DIR / "brand_config.json"


# ---------------------------------------------------------------------------
# Brand config sync — ensure brand_config.json exists on disk
# ---------------------------------------------------------------------------

def _extract_pptx_theme(file_path: str) -> dict:
    """Extract color scheme and font scheme from a PPTX template's theme XML."""
    result: dict = {"colors": {}, "fonts": {}}
    try:
        from pptx import Presentation as PptxPresentation
        from lxml import etree
        ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}

        prs = PptxPresentation(file_path)
        # Find theme part via relationships
        for rel in prs.part.rels.values():
            if "theme" in str(rel.reltype).lower():
                tree = etree.fromstring(rel.target_part.blob)
                # Colors
                clr = tree.find(".//a:clrScheme", ns)
                if clr is not None:
                    color_map = {}
                    for child in clr:
                        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                        srgb = child.find("a:srgbClr", ns)
                        if srgb is not None:
                            color_map[tag] = f"#{srgb.get('val')}"
                    # Map OOXML names to brand roles
                    result["colors"] = {
                        "primary": color_map.get("accent1", ""),
                        "secondary": color_map.get("accent3", color_map.get("dk2", "")),
                        "accent": color_map.get("accent2", ""),
                        "background": color_map.get("lt1", "#FFFFFF"),
                        "text": color_map.get("dk1", "#000000"),
                    }
                    # Store full palette for reference
                    result["full_palette"] = color_map
                # Fonts
                fs = tree.find(".//a:fontScheme", ns)
                if fs is not None:
                    major = fs.find(".//a:majorFont/a:latin", ns)
                    minor = fs.find(".//a:minorFont/a:latin", ns)
                    result["fonts"] = {
                        "heading": major.get("typeface", "Arial") if major is not None else "Arial",
                        "body": minor.get("typeface", "Calibri") if minor is not None else "Calibri",
                    }
                break
    except Exception as exc:
        logger.debug("Could not extract PPTX theme: %s", exc)
    return result


def _ensure_brand_config_on_disk() -> dict:
    """Build brand_config.json from DB data if missing/stale and return it."""
    # If it already exists and is recent, just load and return
    if BRAND_CONFIG_PATH.exists():
        try:
            with open(BRAND_CONFIG_PATH, encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            pass

    # Build from DB
    config: dict = {}
    session = get_session()
    try:
        # Pull all BrandConfig rows
        for row in session.query(BrandConfig).all():
            try:
                val = json.loads(row.config_value) if row.config_value else {}
            except json.JSONDecodeError:
                val = row.config_value
            if row.config_key == "brand_config" and isinstance(val, dict):
                config.update(val)
            elif row.config_key in ("voice_profile", "terminology"):
                config[row.config_key] = val

        # Pull active BrandProfile config_json
        if BrandProfile is not None:
            profile = session.query(BrandProfile).filter(
                BrandProfile.is_active.is_(True)
            ).first()
            if profile and profile.config_json:
                try:
                    profile_cfg = json.loads(profile.config_json)
                    if isinstance(profile_cfg, dict):
                        # Profile config takes precedence
                        for k, v in profile_cfg.items():
                            if v:  # only override if non-empty
                                config[k] = v
                except json.JSONDecodeError:
                    pass
            if profile and not config.get("company_name"):
                config["company_name"] = profile.name
    finally:
        session.close()

    # If no company name, try to detect from asset tags
    if not config.get("company_name") or config["company_name"] == "Default":
        try:
            assets = session.query(BrandAsset).filter(BrandAsset.is_active.is_(True)).all()
            # Look for common brand keywords in tags/filenames
            all_tags = " ".join((a.tags or "") + " " + (a.filename or "") for a in assets).lower()
            # Common pattern: check for brand names in filenames
            for asset in assets:
                if "logo" in (asset.asset_type or "").lower():
                    # Extract company name from logo filename
                    name_parts = Path(asset.filename).stem.replace("_", " ").replace("-", " ")
                    # Remove common suffixes like "Logo", "RGB", "CMYK", dates
                    import re as _re
                    cleaned = _re.sub(
                        r'\b(logo|rgb|cmyk|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|'
                        r'january|february|march|white|black|transparent|20\d{2})\b',
                        '', name_parts, flags=_re.IGNORECASE
                    ).strip()
                    cleaned = _re.sub(r'\s+', ' ', cleaned).strip()
                    if cleaned and len(cleaned) > 1:
                        config["company_name"] = cleaned.title()
                        break
        except Exception:
            pass

    # If no colors/fonts configured, extract from PPTX templates first (best source)
    if not config.get("colors") or not config.get("fonts"):
        try:
            templates_dir = BRAND_ASSETS_DIR / "templates"
            if templates_dir.exists():
                for pptx_file in templates_dir.rglob("*.pptx"):
                    theme = _extract_pptx_theme(str(pptx_file))
                    if theme.get("colors") and any(theme["colors"].values()):
                        if not config.get("colors"):
                            config["colors"] = theme["colors"]
                            logger.info("Auto-extracted brand colors from PPTX template: %s", pptx_file.name)
                        if not config.get("fonts") and theme.get("fonts"):
                            config["fonts"] = theme["fonts"]
                            logger.info("Auto-extracted brand fonts from PPTX template: %s", pptx_file.name)
                        if theme.get("full_palette"):
                            config["full_palette"] = theme["full_palette"]
                        break
        except Exception as exc:
            logger.debug("Could not extract from PPTX templates: %s", exc)

    # Fallback: extract colors from logo if still missing
    if not config.get("colors"):
        try:
            from app.brand.color_extractor import ColorExtractor
            logos_dir = BRAND_ASSETS_DIR / "logos"
            if logos_dir.exists():
                for ext in ("*.png", "*.jpg", "*.jpeg"):
                    logo_files = list(logos_dir.glob(ext))
                    if logo_files:
                        extractor = ColorExtractor()
                        colors = extractor.extract_from_image(str(logo_files[0]))
                        if colors:
                            categorized = extractor.categorize_colors(colors)
                            config["colors"] = categorized
                            logger.info("Auto-extracted brand colors from logo")
                        break
        except Exception as exc:
            logger.debug("Could not auto-extract colors from logo: %s", exc)

    # Write to disk
    BRAND_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(BRAND_CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump(config, fh, indent=2, default=str)
    except OSError as exc:
        logger.warning("Could not write brand_config.json: %s", exc)

    return config


# =========================================================================
# Public entry point
# =========================================================================


def execute_tool(tool_name: str, tool_input: dict, **context) -> str:
    """Execute a copilot tool and return the result as a JSON string.

    Parameters
    ----------
    tool_name : str
        Name of the tool to execute.
    tool_input : dict
        Input parameters from Claude's tool_use block.
    **context
        Additional context (not used currently, but allows future extension).

    Returns
    -------
    str
        JSON string result to return as tool_result content to Claude.
    """
    handler_map: dict[str, Any] = {
        "search_brand_assets": _handle_search_brand_assets,
        "get_brand_config": _handle_get_brand_config,
        "update_brand_config": _handle_update_brand_config,
        "generate_presentation": _handle_generate_presentation,
        "generate_document": _handle_generate_document,
        "generate_training_package": _handle_generate_training_package,
        "generate_visual": _handle_generate_visual,
        "generate_batch": _handle_generate_batch,
        "search_content_library": _handle_search_content_library,
        "get_content_stats": _handle_get_content_stats,
        "approve_content": _handle_approve_content,
        "list_templates": _handle_list_templates,
        "translate_content": _handle_translate_content,
        "search_brand_knowledge": _handle_search_brand_knowledge,
        "web_search": _handle_web_search,
        "confirm_action": _handle_confirm_action,
    }

    handler = handler_map.get(tool_name)
    if handler is None:
        logger.warning("Unknown tool requested: %s", tool_name)
        return json.dumps({
            "error": f"Unknown tool: '{tool_name}'",
            "available_tools": sorted(handler_map.keys()),
        })

    logger.info("Executing copilot tool: %s", tool_name)
    try:
        return handler(tool_input)
    except Exception as exc:
        logger.exception("Tool '%s' failed with unhandled error", tool_name)
        return json.dumps({
            "error": f"Tool execution failed: {exc}",
            "tool": tool_name,
        })


# =========================================================================
# Shared helpers
# =========================================================================


def _parse_json_response(raw: str) -> Any:
    """Parse a JSON response from Claude, stripping markdown fences if present.

    Claude sometimes wraps JSON output in triple-backtick code fences
    (```json ... ```).  This helper strips those before parsing.

    Parameters
    ----------
    raw : str
        Raw text from ``response.content[0].text``.

    Returns
    -------
    dict | list
        The parsed JSON payload.

    Raises
    ------
    ValueError
        If the response cannot be parsed as valid JSON.
    """
    if not raw:
        return {}

    text = raw.strip()

    # Remove markdown code fences
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3].rstrip()

    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback: locate the outermost { ... } or [ ... ] block
    for open_ch, close_ch in [("{", "}"), ("[", "]")]:
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not parse JSON from Claude response: {text[:200]}")


def _get_anthropic_client() -> Any:
    """Return an Anthropic client instance or raise if unavailable."""
    if Anthropic is None:
        raise RuntimeError(
            "The anthropic package is not installed. "
            "Run `pip install anthropic` to enable content generation."
        )
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Please configure it in your .env file."
        )
    return Anthropic(api_key=api_key)


def _read_source_file(file_path: str) -> str:
    """Read content from a source file, dispatching to the appropriate parser.

    Supports PDF, DOCX, PPTX, and plain text files.

    Parameters
    ----------
    file_path : str
        Absolute or relative path to the source file.

    Returns
    -------
    str
        Extracted text content from the file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        if PDFParser is None:
            raise ImportError("PDFParser is not available. Install pdfplumber.")
        parser = PDFParser()
        result = parser.parse(str(path))
        return result.get("text", "")

    if suffix in (".docx", ".docm"):
        if DOCXParser is None:
            raise ImportError("DOCXParser is not available. Install python-docx.")
        parser = DOCXParser()
        result = parser.parse(str(path))
        return result.get("text", "")

    if suffix in (".pptx", ".pptm"):
        if PPTXParser is None:
            raise ImportError("PPTXParser is not available. Install python-pptx.")
        parser = PPTXParser()
        result = parser.parse(str(path))
        # Concatenate slide text
        slides = result.get("slides", [])
        parts = []
        for slide in slides:
            if slide.get("title"):
                parts.append(slide["title"])
            for text_block in slide.get("content", []):
                parts.append(text_block)
            if slide.get("notes"):
                parts.append(slide["notes"])
        return "\n\n".join(parts)

    if suffix in (".html", ".htm"):
        raw_html = path.read_text(encoding="utf-8", errors="replace")
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(raw_html, "html.parser")
            for tag in soup.find_all(["script", "style", "noscript", "iframe", "svg"]):
                tag.decompose()
            return soup.get_text(separator="\n", strip=True)
        except ImportError:
            # Fallback: strip tags
            return re.sub(r"<[^>]+>", " ", raw_html)

    # Default: plain text
    return path.read_text(encoding="utf-8", errors="replace")


def _record_generation(
    title: str,
    content_type: str,
    output_path: str,
    fmt: str,
    generation_time: float,
    input_summary: str = "",
    template_id: int | None = None,
) -> int:
    """Insert a record into the GeneratedContent table.

    Parameters
    ----------
    title : str
        Human-readable title for the generated item.
    content_type : str
        One of presentation, document, training_package, visual, etc.
    output_path : str
        Absolute path to the generated file.
    fmt : str
        File format (pptx, docx, png, zip, etc.).
    generation_time : float
        Wall-clock seconds the generation took.
    input_summary : str
        Brief description of the input used.
    template_id : int | None
        Optional Template FK.

    Returns
    -------
    int
        The ID of the newly inserted record.
    """
    session = get_session()
    try:
        record = GeneratedContent(
            title=title,
            content_type=content_type,
            output_path=output_path,
            format=fmt,
            generation_time_seconds=round(generation_time, 2),
            input_summary=input_summary[:500] if input_summary else "",
            template_id=template_id,
        )
        session.add(record)
        session.commit()
        record_id = record.id
        return record_id
    except Exception as exc:
        session.rollback()
        logger.error("Failed to record generation: %s", exc)
        return -1
    finally:
        session.close()


def _file_size_str(path: str) -> str:
    """Return a human-readable file size string."""
    try:
        size = os.path.getsize(path)
    except OSError:
        return "unknown"

    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _load_brand_config() -> dict:
    """Load brand_config.json from the brand_assets directory."""
    if BRAND_CONFIG_PATH.exists():
        try:
            return json.loads(BRAND_CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load brand_config.json: %s", exc)
    return {}


def _save_brand_config(config: dict) -> None:
    """Save brand configuration back to brand_config.json."""
    BRAND_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    BRAND_CONFIG_PATH.write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# =========================================================================
# Claude content-generation helpers
# =========================================================================


def _generate_slides_from_content(
    content: str,
    title: str,
    num_slides: int,
    presentation_type: str,
    instructions: str,
    brand_context: dict | None = None,
) -> list[dict]:
    """Use Claude to structure content into slide data.

    Parameters
    ----------
    content : str
        Raw textual content to transform into slides.
    title : str
        Presentation title.
    num_slides : int
        Target number of slides.
    presentation_type : str
        Type of presentation (e.g. sales, training, overview).
    instructions : str
        Additional user instructions for Claude.
    brand_context : dict | None
        Brand voice, terminology, colors, and reference content.

    Returns
    -------
    list[dict]
        List of slide dictionaries, each with keys like ``layout``,
        ``title``, ``body``, ``bullets``, ``speaker_notes``, etc.
    """
    client = _get_anthropic_client()

    system_prompt = (
        "You are a presentation content architect. Transform the provided content "
        "into structured slide data for a branded PowerPoint presentation.\n\n"
        "Return a JSON array of slide objects. Each slide object MUST have:\n"
        '- "layout": one of "title", "content", "two_column", "section", "closing"\n'
        '- "title": slide title string\n\n'
        "Each slide object MAY also have:\n"
        '- "body": paragraph text\n'
        '- "bullets": array of bullet-point strings (prefix with "- " for sub-bullets)\n'
        '- "subtitle": subtitle text (for title/closing slides)\n'
        '- "speaker_notes": notes for the presenter\n'
        '- "columns": array of column objects for two_column layout, each with "title" and "bullets"\n'
        '- "suggested_visual": description of a relevant visual or diagram\n\n'
        "Guidelines:\n"
        "- First slide should use 'title' layout\n"
        "- Last slide should use 'closing' layout\n"
        "- Use 'section' layout for major topic transitions\n"
        "- Keep bullets concise (under 12 words each)\n"
        "- Include speaker notes with additional context\n"
        "- Include 'suggested_visual' on at least 3-4 slides describing a diagram, "
        "chart, or infographic that would enhance the slide\n"
        "- Return ONLY the JSON array, no markdown fences or explanation."
    )

    # Inject brand context into system prompt
    bc = brand_context or {}
    if bc:
        voice = bc.get("voice_profile", {})
        terminology = bc.get("terminology", {})
        company = bc.get("company_name", "")
        colors = bc.get("colors", {})

        brand_section = "\n\nBRAND GUIDELINES — follow these strictly:\n"
        if company:
            brand_section += f"- Company: {company}\n"
        if voice.get("tone"):
            brand_section += f"- Tone: {voice['tone']}\n"
        if voice.get("formality"):
            brand_section += f"- Formality: {voice['formality']}\n"
        if voice.get("key_phrases"):
            phrases = voice["key_phrases"][:10]
            brand_section += f"- Use these key phrases where relevant: {', '.join(phrases)}\n"
        if voice.get("messaging_themes"):
            themes = voice["messaging_themes"][:5]
            brand_section += f"- Core messaging themes: {', '.join(themes)}\n"
        if terminology.get("program_names"):
            brand_section += f"- Official program names (use exact spelling): {', '.join(terminology['program_names'])}\n"
        if terminology.get("acronyms"):
            acrs = [f"{k} = {v}" for k, v in list(terminology["acronyms"].items())[:10]]
            brand_section += f"- Acronyms: {'; '.join(acrs)}\n"
        if colors:
            brand_section += f"- Brand colors: primary={colors.get('primary','N/A')}, accent={colors.get('accent','N/A')}, secondary={colors.get('secondary','N/A')}\n"

        system_prompt += brand_section

    user_prompt = (
        f"Create a {num_slides}-slide {presentation_type} presentation titled "
        f'"{title}".\n\n'
        f"Source content:\n{content[:8000]}\n\n"
    )

    # Inject reference material from content library / brand knowledge
    ref_content = bc.get("reference_content", "")
    if ref_content:
        user_prompt += (
            "IMPORTANT: Use the following reference material as the primary source of "
            "facts, data, and talking points. Do NOT make up content — base the slides "
            "on this material:\n\n"
            f"{ref_content[:8000]}\n\n"
        )

    if instructions:
        user_prompt += f"Additional instructions:\n{instructions}\n"

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text
    slides = _parse_json_response(raw)

    if isinstance(slides, dict):
        slides = slides.get("slides", [])
    if not isinstance(slides, list):
        slides = []

    # Validate and normalise each slide
    validated: list[dict] = []
    valid_layouts = {"title", "content", "two_column", "section", "closing"}
    for slide in slides:
        if not isinstance(slide, dict):
            continue
        layout = str(slide.get("layout", "content")).lower()
        if layout not in valid_layouts:
            layout = "content"
        slide["layout"] = layout
        validated.append(slide)

    return validated


def _generate_document_content(
    content_source: str,
    title: str,
    doc_type: str,
    instructions: str,
    data_input: str,
) -> dict:
    """Use Claude to generate structured document content.

    Parameters
    ----------
    content_source : str
        Raw textual content or topic description.
    title : str
        Document title.
    doc_type : str
        Document type identifier (e.g. weekly_report, case_study).
    instructions : str
        Additional user instructions.
    data_input : str
        Any structured data (CSV, JSON) to incorporate.

    Returns
    -------
    dict
        Structured content dictionary suitable for BrandedDocumentGenerator.
    """
    client = _get_anthropic_client()

    # Build template guidance based on doc_type
    template_info = DOCUMENT_TEMPLATES.get(doc_type, {})
    template_name = template_info.get("name", doc_type)
    template_desc = template_info.get("description", "")

    # Load brand context for document styling
    brand_section = ""
    try:
        if BRAND_CONFIG_PATH.exists():
            with open(BRAND_CONFIG_PATH, "r", encoding="utf-8") as f:
                bc = json.load(f)
            company = bc.get("company_name", "")
            voice = bc.get("voice_profile", {})
            terminology = bc.get("terminology", {})
            if company:
                brand_section += f"\n\nBRAND GUIDELINES:\n- Company: {company}\n"
            if voice.get("tone"):
                brand_section += f"- Tone: {voice['tone']}\n"
            if voice.get("formality"):
                brand_section += f"- Formality: {voice['formality']}\n"
            if voice.get("key_phrases"):
                brand_section += f"- Key phrases: {', '.join(voice['key_phrases'][:8])}\n"
            if terminology.get("program_names"):
                brand_section += f"- Official program names: {', '.join(terminology['program_names'])}\n"
            if terminology.get("acronyms"):
                acrs = [f"{k}={v}" for k, v in list(terminology["acronyms"].items())[:8]]
                brand_section += f"- Acronyms: {'; '.join(acrs)}\n"
    except Exception:
        pass

    system_prompt = (
        "You are a document content architect. Generate structured content "
        f"for a '{template_name}' document.\n\n"
        f"Document type description: {template_desc}\n\n"
        "Return a JSON object with the content fields appropriate for this "
        "document type. Always include a 'title' key.\n\n"
        "IMPORTANT: Generate SUBSTANTIAL content. Each section should have "
        "multiple paragraphs of real, detailed content. Never return just a "
        "title or skeleton — fill in all sections with rich, professional text.\n\n"
        "If reference material is provided in the source content, use it "
        "as the PRIMARY source of facts, talking points, and data. Do NOT "
        "make up facts — use what is provided.\n\n"
        "Common fields by document type:\n"
        "- job_aid: title, steps (array of {step_number, title, description, tips}), "
        "  quick_reference (array of strings), notes\n"
        "- case_study: title, client, challenge, solution, results, key_metrics, "
        "  testimonial, lessons_learned\n"
        "- weekly_report: title, period, highlights (array), challenges (array), "
        "  priorities (array), kpis (array of {metric, value, target})\n"
        "- monthly_report: title, period, executive_summary, sections (array of "
        "  {heading, content}), metrics, recommendations\n"
        "- proposal: title, client, executive_summary, problem_statement, "
        "  proposed_solution, deliverables (array), timeline, investment, "
        "  terms_and_conditions\n"
        "- sop: title, purpose, scope, definitions (array), procedure_steps "
        "  (array of {step, description, responsible_party}), revision_history\n"
        "- meeting_minutes: title, date, attendees (array), agenda_items (array), "
        "  discussion_points (array), action_items (array of {item, owner, due_date}), "
        "  next_meeting\n"
        "- newsletter: title, issue_number, date, sections (array of {heading, content}), "
        "  upcoming_events, spotlight\n"
        "- executive_brief: title, situation, background, assessment, recommendation, "
        "  next_steps\n"
        "- onboarding_guide: title, welcome_message, sections (array of {heading, content}), "
        "  key_contacts, first_week_schedule, resources\n"
        "- training_guide: title, objective, sections (array of {heading, content, "
        "  key_takeaways}), exercises, summary, resources\n\n"
        "For any unrecognized type, use: title, executive_summary, sections (array of "
        "{heading, content}), key_takeaways, next_steps\n\n"
        "Return ONLY the JSON object, no markdown fences or explanation."
        + brand_section
    )

    user_prompt = (
        f'Generate content for a "{title}" document (type: {doc_type}).\n\n'
        f"Source content:\n{content_source[:8000]}\n\n"
    )
    if data_input:
        user_prompt += f"Data to incorporate:\n{data_input[:4000]}\n\n"
    if instructions:
        user_prompt += f"Additional instructions:\n{instructions}\n"

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text
    content = _parse_json_response(raw)

    if not isinstance(content, dict):
        content = {"title": title, "body": str(content)}

    if "title" not in content:
        content["title"] = title

    return content


# =========================================================================
# Individual tool handlers
# =========================================================================


def _handle_search_brand_assets(tool_input: dict) -> str:
    """Search the BrandAsset table by query, asset_type, and tags.

    Parameters
    ----------
    tool_input : dict
        Expected keys: ``query`` (str), ``asset_type`` (str, optional).

    Returns
    -------
    str
        JSON array of matching asset records.
    """
    try:
        query = tool_input.get("query", "").strip()
        asset_type = tool_input.get("asset_type", "all").strip().lower()

        session = get_session()
        try:
            q = session.query(BrandAsset).filter(BrandAsset.is_active.is_(True))

            # Filter by asset_type unless "all"
            if asset_type and asset_type != "all":
                q = q.filter(BrandAsset.asset_type == asset_type)

            # Search by filename and tags
            if query:
                like_pattern = f"%{query}%"
                q = q.filter(
                    (BrandAsset.filename.ilike(like_pattern))
                    | (BrandAsset.tags.ilike(like_pattern))
                )

            assets = q.order_by(BrandAsset.uploaded_at.desc()).all()

            results = []
            for asset in assets:
                results.append({
                    "id": asset.id,
                    "filename": asset.filename,
                    "asset_type": asset.asset_type,
                    "file_path": asset.file_path,
                    "uploaded_at": (
                        asset.uploaded_at.isoformat() if asset.uploaded_at else None
                    ),
                    "tags": asset.tags,
                })

            return json.dumps({
                "results": results,
                "count": len(results),
                "query": query,
                "asset_type_filter": asset_type,
            })
        finally:
            session.close()

    except Exception as exc:
        logger.error("search_brand_assets failed: %s", exc)
        return json.dumps({"error": str(exc), "results": [], "count": 0})


def _handle_get_brand_config(tool_input: dict) -> str:
    """Load and return brand configuration.

    Parameters
    ----------
    tool_input : dict
        Expected keys: ``section`` (str) -- "all" or a specific section name.

    Returns
    -------
    str
        JSON object with the requested configuration.
    """
    try:
        section = tool_input.get("section", "all").strip().lower()

        # Load from brand_config.json
        config = _load_brand_config()

        # Also check BrandConfig DB table for additional settings
        session = get_session()
        try:
            db_configs = session.query(BrandConfig).all()
            db_settings = {}
            for cfg in db_configs:
                try:
                    db_settings[cfg.config_key] = json.loads(cfg.config_value)
                except (json.JSONDecodeError, TypeError):
                    db_settings[cfg.config_key] = cfg.config_value
            if db_settings:
                config["db_settings"] = db_settings
        finally:
            session.close()

        if section == "all":
            return json.dumps({
                "config": config,
                "source": str(BRAND_CONFIG_PATH),
            })

        # Return just the requested section
        if section in config:
            return json.dumps({
                "section": section,
                "data": config[section],
                "source": str(BRAND_CONFIG_PATH),
            })

        return json.dumps({
            "error": f"Section '{section}' not found in brand config.",
            "available_sections": list(config.keys()),
        })

    except Exception as exc:
        logger.error("get_brand_config failed: %s", exc)
        return json.dumps({"error": str(exc)})


def _handle_update_brand_config(tool_input: dict) -> str:
    """Merge updates into a section of brand_config.json.

    Parameters
    ----------
    tool_input : dict
        Expected keys: ``section`` (str), ``updates`` (dict).

    Returns
    -------
    str
        JSON object with success/failure message.
    """
    try:
        section = tool_input.get("section", "").strip()
        updates = tool_input.get("updates", {})

        if not section:
            return json.dumps({"error": "No section specified for update."})
        if not updates:
            return json.dumps({"error": "No updates provided."})

        config = _load_brand_config()

        # Merge updates into the specified section
        if section in config and isinstance(config[section], dict):
            config[section].update(updates)
        else:
            config[section] = updates

        _save_brand_config(config)

        logger.info("Updated brand config section '%s'", section)
        return json.dumps({
            "success": True,
            "message": f"Brand config section '{section}' updated successfully.",
            "updated_keys": list(updates.keys()),
        })

    except Exception as exc:
        logger.error("update_brand_config failed: %s", exc)
        return json.dumps({"error": str(exc), "success": False})


def _handle_generate_presentation(tool_input: dict) -> str:
    """Generate a branded PPTX presentation.

    Parameters
    ----------
    tool_input : dict
        Expected keys: ``title`` (str), ``content_source`` (str),
        ``num_slides`` (int), ``presentation_type`` (str),
        ``instructions`` (str, optional), ``source_file_path`` (str, optional).

    Returns
    -------
    str
        JSON object with file path and metadata.
    """
    try:
        if BrandedPresentationGenerator is None:
            return json.dumps({
                "error": "Presentation generator not available. "
                         "Install python-pptx to enable this feature.",
                "success": False,
            })

        title = tool_input.get("title", "Untitled Presentation")
        content_source = tool_input.get("content_source", "")
        num_slides = int(tool_input.get("num_slides", 8))
        presentation_type = tool_input.get("presentation_type", "overview")
        instructions = tool_input.get("instructions", "") or tool_input.get("additional_instructions", "")
        source_file_path = tool_input.get("source_file_path", "")

        # Read content from file if a source file is provided
        if source_file_path and not content_source:
            try:
                content_source = _read_source_file(source_file_path)
            except Exception as file_exc:
                return json.dumps({
                    "error": f"Failed to read source file: {file_exc}",
                    "success": False,
                })

        if not content_source:
            return json.dumps({
                "error": "No content_source or source_file_path provided.",
                "success": False,
            })

        start = time.time()

        # Step 0: Ensure brand_config.json exists on disk
        brand_config = _ensure_brand_config_on_disk()

        # Step 0b: Search brand knowledge base for relevant content
        #   Strategy: first try vector store, then fall back to direct DB
        #   search + source file reading for items with empty content_text.
        reference_content = ""
        try:
            knowledge_result = _handle_search_brand_knowledge({
                "query": f"{title} {presentation_type}",
                "n_results": 5,
            })
            kr = json.loads(knowledge_result)
            if kr.get("results"):
                chunks = []
                for r in kr["results"][:5]:
                    doc = r.get("document", "")
                    if doc:
                        chunks.append(doc[:600])
                reference_content = "\n---\n".join(chunks)
        except Exception:
            pass

        # Step 0c: Direct DB search — find ContentLibraryItems by title/tags
        #   This catches items that were never indexed (empty content_text).
        #   Uses weighted scoring: longer/rarer words count more, stopwords ignored.
        try:
            _STOP = {"a","an","the","in","on","of","to","for","and","or","is","it","at","by","with","from","as","every"}
            session = get_session()
            search_terms = [t.strip(",:;!?.") for t in title.lower().split() if t.strip(",:;!?.") not in _STOP and len(t) > 1]
            db_items = session.query(ContentLibraryItem).all()
            matched_items = []
            for item in db_items:
                item_text = f"{item.title or ''} {item.tags or ''} {item.description or ''}".lower()
                # Weight: longer terms count more (e.g. "facts"=5, "sales"=5)
                score = sum(len(term) for term in search_terms if term in item_text)
                if score > 0:
                    matched_items.append((score, item))
            matched_items.sort(key=lambda x: x[0], reverse=True)
            session.close()

            for _score, item in matched_items[:3]:
                if len(reference_content) >= 12000:
                    break
                # Prefer reading the full source file for richer content
                if item.source_path and Path(item.source_path).exists():
                    try:
                        file_text = _read_source_file(item.source_path)
                        if file_text and len(file_text) > 50:
                            reference_content += f"\n---\n{file_text[:8000]}"
                            # Also backfill content_text in the DB if empty
                            if not item.content_text:
                                try:
                                    s2 = get_session()
                                    db_item = s2.query(ContentLibraryItem).filter_by(id=item.id).first()
                                    if db_item:
                                        db_item.content_text = file_text[:5000]
                                        s2.commit()
                                    s2.close()
                                except Exception:
                                    pass
                            continue
                    except Exception as read_exc:
                        logger.debug("Could not read source file %s: %s", item.source_path, read_exc)
                # Fallback: use content_text from DB
                if item.content_text and len(item.content_text) > 50:
                    reference_content += f"\n---\n{item.content_text[:4000]}"
        except Exception as db_exc:
            logger.debug("Direct DB search failed: %s", db_exc)

        # Build brand context for slide generation
        brand_context = {
            "company_name": brand_config.get("company_name", ""),
            "colors": brand_config.get("colors", {}),
            "voice_profile": brand_config.get("voice_profile", {}),
            "terminology": brand_config.get("terminology", {}),
            "reference_content": reference_content,
        }

        # Step 1: Generate structured slide data from content via Claude
        logger.info("Generating slide data for '%s' (%d slides)", title, num_slides)
        slides_data = _generate_slides_from_content(
            content=content_source,
            title=title,
            num_slides=num_slides,
            presentation_type=presentation_type,
            instructions=instructions,
            brand_context=brand_context,
        )

        if not slides_data:
            return json.dumps({
                "error": "Claude returned no slide data. Please try again.",
                "success": False,
            })

        # Step 1b: Generate Napkin visuals for slides with suggested_visual
        if _NAPKIN_OK:
            try:
                napkin = NapkinClient()
                for slide in slides_data:
                    visual_desc = slide.get("suggested_visual")
                    if not visual_desc:
                        continue
                    try:
                        result = napkin.generate_visual(
                            text_content=visual_desc,
                            visual_type="infographic",
                            style="professional",
                            color_mode="brand",
                            output_format="png",
                        )
                        if result.get("success") and result.get("file_path"):
                            slide["image_path"] = result["file_path"]
                            logger.info("Napkin visual generated for: %s", visual_desc[:50])
                    except Exception as napkin_exc:
                        logger.debug("Napkin visual skipped: %s", napkin_exc)
            except Exception:
                logger.debug("Napkin client not available, skipping visuals")

        # Step 2: Generate the PPTX file
        logger.info("Building PPTX with %d slides", len(slides_data))
        gen = BrandedPresentationGenerator(brand_config=brand_config)
        output_path = gen.generate(slides_data=slides_data, title=title)

        elapsed = time.time() - start

        # Step 3: Record in GeneratedContent
        record_id = _record_generation(
            title=title,
            content_type="presentation",
            output_path=output_path,
            fmt="pptx",
            generation_time=elapsed,
            input_summary=content_source[:300],
        )

        return json.dumps({
            "success": True,
            "file_path": str(output_path),
            "title": title,
            "num_slides": len(slides_data),
            "file_size": _file_size_str(output_path),
            "generation_time_seconds": round(elapsed, 2),
            "record_id": record_id,
        })

    except Exception as exc:
        logger.exception("generate_presentation failed")
        return json.dumps({"error": str(exc), "success": False})


def _handle_generate_document(tool_input: dict) -> str:
    """Generate a branded DOCX document.

    Parameters
    ----------
    tool_input : dict
        Expected keys: ``title`` (str), ``content_source`` (str),
        ``document_type`` (str), ``instructions`` (str, optional),
        ``source_file_path`` (str, optional), ``data_input`` (str, optional).

    Returns
    -------
    str
        JSON object with file path and metadata.
    """
    try:
        if BrandedDocumentGenerator is None:
            return json.dumps({
                "error": "Document generator not available. "
                         "Install python-docx to enable this feature.",
                "success": False,
            })

        title = tool_input.get("title", "Untitled Document")
        content_source = tool_input.get("content_source", "")
        document_type = tool_input.get("document_type", "job_aid")
        instructions = tool_input.get("instructions", "") or tool_input.get("additional_instructions", "")
        source_file_path = tool_input.get("source_file_path", "")
        data_input = tool_input.get("data_input", "")

        # Read content from file if a source file is provided
        if source_file_path and not content_source:
            try:
                content_source = _read_source_file(source_file_path)
            except Exception as file_exc:
                return json.dumps({
                    "error": f"Failed to read source file: {file_exc}",
                    "success": False,
                })

        if not content_source:
            return json.dumps({
                "error": "No content_source or source_file_path provided.",
                "success": False,
            })

        start = time.time()

        # Step 0: Ensure brand_config.json exists on disk
        brand_config = _ensure_brand_config_on_disk()

        # Step 0b: Search content library for relevant reference material
        reference_content = ""
        try:
            knowledge_result = _handle_search_brand_knowledge({
                "query": f"{title} {document_type}",
                "n_results": 5,
            })
            kr = json.loads(knowledge_result)
            if kr.get("results"):
                chunks = []
                for r in kr["results"][:5]:
                    doc = r.get("document", "")
                    if doc:
                        chunks.append(doc[:600])
                reference_content = "\n---\n".join(chunks)
        except Exception:
            pass

        # Step 0c: Direct DB search fallback (same as presentation handler)
        try:
            _STOP = {"a","an","the","in","on","of","to","for","and","or","is","it","at","by","with","from","as","every"}
            session = get_session()
            search_terms = [t.strip(",:;!?.") for t in title.lower().split() if t.strip(",:;!?.") not in _STOP and len(t) > 1]
            db_items = session.query(ContentLibraryItem).all()
            matched_items = []
            for item in db_items:
                item_text = f"{item.title or ''} {item.tags or ''} {item.description or ''}".lower()
                score = sum(len(term) for term in search_terms if term in item_text)
                if score > 0:
                    matched_items.append((score, item))
            matched_items.sort(key=lambda x: x[0], reverse=True)
            session.close()

            for _score, item in matched_items[:3]:
                if len(reference_content) >= 12000:
                    break
                if item.source_path and Path(item.source_path).exists():
                    try:
                        file_text = _read_source_file(item.source_path)
                        if file_text and len(file_text) > 50:
                            reference_content += f"\n---\n{file_text[:8000]}"
                            continue
                    except Exception:
                        pass
                if item.content_text and len(item.content_text) > 50:
                    reference_content += f"\n---\n{item.content_text[:4000]}"
        except Exception:
            pass

        # Enrich content_source with reference material
        if reference_content:
            content_source += (
                "\n\n--- REFERENCE MATERIAL FROM CONTENT LIBRARY ---\n"
                "Use the following as the primary source of facts and data. "
                "Do NOT make up content — base the document on this material:\n"
                f"{reference_content[:10000]}"
            )

        # Step 1: Generate structured document content via Claude
        logger.info("Generating document content for '%s' (type: %s)", title, document_type)
        content_dict = _generate_document_content(
            content_source=content_source,
            title=title,
            doc_type=document_type,
            instructions=instructions,
            data_input=data_input,
        )

        if not content_dict:
            return json.dumps({
                "error": "Claude returned no document content. Please try again.",
                "success": False,
            })

        # Step 2: Generate the DOCX file
        logger.info("Building DOCX document")
        gen = BrandedDocumentGenerator()
        output_path = gen.generate(
            content=content_dict,
            doc_type=document_type,
            title=title,
        )

        elapsed = time.time() - start

        # Step 3: Record in GeneratedContent
        record_id = _record_generation(
            title=title,
            content_type="document",
            output_path=output_path,
            fmt="docx",
            generation_time=elapsed,
            input_summary=content_source[:300],
        )

        return json.dumps({
            "success": True,
            "file_path": str(output_path),
            "title": title,
            "document_type": document_type,
            "file_size": _file_size_str(output_path),
            "generation_time_seconds": round(elapsed, 2),
            "record_id": record_id,
        })

    except Exception as exc:
        logger.exception("generate_document failed")
        return json.dumps({"error": str(exc), "success": False})


def _handle_generate_training_package(tool_input: dict) -> str:
    """Generate a complete training package.

    Parameters
    ----------
    tool_input : dict
        Expected keys: ``title`` (str), ``content_source`` (str),
        ``training_type`` (str), ``audience_level`` (str),
        ``outputs_to_generate`` (list[str]), ``instructions`` (str, optional),
        ``source_file_path`` (str, optional).

    Returns
    -------
    str
        JSON object with generated file paths and metadata.
    """
    try:
        if TrainingPipeline is None or PipelineOptions is None:
            return json.dumps({
                "error": "Training pipeline not available. Check dependencies.",
                "success": False,
            })

        title = tool_input.get("title", "Training Package")
        content_source = tool_input.get("content_source", "")
        training_type = tool_input.get("training_type", "general")
        audience_level = tool_input.get("audience_level", "intermediate")
        outputs_to_generate = tool_input.get("outputs_to_generate", [])
        instructions = tool_input.get("instructions", "")
        source_file_path = tool_input.get("source_file_path", "")

        # Read content from file if provided
        if source_file_path and not content_source:
            try:
                content_source = _read_source_file(source_file_path)
            except Exception as file_exc:
                return json.dumps({
                    "error": f"Failed to read source file: {file_exc}",
                    "success": False,
                })

        if not content_source:
            return json.dumps({
                "error": "No content_source or source_file_path provided.",
                "success": False,
            })

        start = time.time()

        # Build PipelineOptions from outputs_to_generate list
        options = PipelineOptions(
            training_type=training_type,
            audience_level=audience_level,
        )

        if outputs_to_generate:
            # Map output names to PipelineOptions fields
            output_map = {
                "training_deck": "training_deck",
                "deck": "training_deck",
                "presentation": "training_deck",
                "facilitator_guide": "facilitator_guide",
                "guide": "facilitator_guide",
                "participant_handouts": "participant_handouts",
                "handouts": "participant_handouts",
                "job_aids": "job_aids",
                "job_aid": "job_aids",
                "quiz": "quiz",
                "quizzes": "quiz",
                "microlearning": "microlearning",
                "agent_script": "agent_script",
                "script": "agent_script",
            }
            # Start with all off, then enable requested ones
            for field_name in [
                "training_deck", "facilitator_guide", "participant_handouts",
                "job_aids", "quiz", "microlearning", "agent_script",
            ]:
                setattr(options, field_name, False)

            for output_name in outputs_to_generate:
                key = output_name.strip().lower()
                mapped = output_map.get(key)
                if mapped:
                    setattr(options, mapped, True)
                else:
                    logger.warning(
                        "Unknown training output type: '%s' -- skipping", output_name
                    )
        else:
            # Default: generate the standard set
            options.training_deck = True
            options.facilitator_guide = True
            options.participant_handouts = True
            options.job_aids = True
            options.quiz = True

        # Prepend instructions to content if provided
        full_content = content_source
        if instructions:
            full_content = (
                f"[Instructor Notes / Additional Instructions]\n{instructions}\n\n"
                f"[Content]\n{content_source}"
            )

        # Run the pipeline
        logger.info("Running training pipeline for '%s'", title)
        pipeline = TrainingPipeline()
        package = pipeline.process_curriculum(
            input_content=full_content,
            input_type="text",
            options=options,
        )

        elapsed = time.time() - start

        # Record in GeneratedContent
        output_path = package.zip_path or ""
        record_id = _record_generation(
            title=title,
            content_type="training_package",
            output_path=str(output_path) if output_path else "",
            fmt="zip",
            generation_time=elapsed,
            input_summary=content_source[:300],
        )

        # Build result
        outputs_result = {}
        for output_type, file_path in package.outputs.items():
            outputs_result[output_type] = {
                "file_path": str(file_path),
                "file_size": _file_size_str(str(file_path)),
            }

        return json.dumps({
            "success": True,
            "title": title,
            "outputs": outputs_result,
            "zip_path": str(package.zip_path) if package.zip_path else None,
            "errors": package.errors,
            "generation_time_seconds": round(elapsed, 2),
            "record_id": record_id,
        })

    except Exception as exc:
        logger.exception("generate_training_package failed")
        return json.dumps({"error": str(exc), "success": False})


def _handle_generate_visual(tool_input: dict) -> str:
    """Generate a visual using the VisualPipeline.

    Parameters
    ----------
    tool_input : dict
        Expected keys: ``description`` (str), ``visual_type`` (str),
        ``output_format`` (str, optional), ``style`` (str, optional).

    Returns
    -------
    str
        JSON object with file path and metadata.
    """
    try:
        if VisualPipeline is None:
            return json.dumps({
                "error": "Visual pipeline not available. Check dependencies.",
                "success": False,
            })

        description = tool_input.get("description", "")
        visual_type = tool_input.get("visual_type", "flowchart")
        output_format = tool_input.get("output_format", "png")
        style = tool_input.get("style", "professional")

        if not description:
            return json.dumps({
                "error": "No description provided for visual generation.",
                "success": False,
            })

        start = time.time()

        logger.info("Generating visual (type: %s, format: %s)", visual_type, output_format)
        pipeline = VisualPipeline()
        result = pipeline.generate_visual(
            description=description,
            visual_type=visual_type,
            output_format=output_format,
            style=style,
        )

        elapsed = time.time() - start

        if not result.get("success"):
            return json.dumps({
                "error": result.get("error", "Visual generation failed."),
                "success": False,
            })

        file_path = result.get("file_path", "")

        # Record in GeneratedContent
        record_id = _record_generation(
            title=f"Visual: {visual_type}",
            content_type="visual",
            output_path=str(file_path),
            fmt=output_format,
            generation_time=elapsed,
            input_summary=description[:300],
        )

        return json.dumps({
            "success": True,
            "file_path": str(file_path),
            "visual_type": visual_type,
            "output_format": output_format,
            "method": result.get("method", "unknown"),
            "file_size": _file_size_str(str(file_path)),
            "generation_time_seconds": round(elapsed, 2),
            "record_id": record_id,
        })

    except Exception as exc:
        logger.exception("generate_visual failed")
        return json.dumps({"error": str(exc), "success": False})


def _handle_generate_batch(tool_input: dict) -> str:
    """Process a batch of content generation requests.

    Parameters
    ----------
    tool_input : dict
        Expected keys: ``batch_name`` (str), ``items`` (list[dict]).
        Each item dict should have ``tool_name`` and ``tool_input``.

    Returns
    -------
    str
        JSON object with batch results summary.
    """
    try:
        batch_name = tool_input.get("batch_name", f"Batch {datetime.utcnow():%Y-%m-%d %H:%M}")
        items = tool_input.get("items", [])

        if not items:
            return json.dumps({
                "error": "No items provided for batch processing.",
                "success": False,
            })

        start = time.time()

        # Create BatchJob record
        session = get_session()
        try:
            batch_job = BatchJob(
                name=batch_name,
                status="running",
                items_json=json.dumps(items),
            )
            session.add(batch_job)
            session.commit()
            batch_id = batch_job.id
        except Exception as db_exc:
            session.rollback()
            logger.error("Failed to create BatchJob record: %s", db_exc)
            batch_id = -1
        finally:
            session.close()

        # Process each item
        results = []
        success_count = 0
        error_count = 0

        for idx, item in enumerate(items):
            item_tool = item.get("tool_name", "")
            item_input = item.get("tool_input", {})

            logger.info(
                "Batch item %d/%d: %s", idx + 1, len(items), item_tool
            )

            try:
                result_str = execute_tool(item_tool, item_input)
                result_data = json.loads(result_str)
                result_data["_batch_index"] = idx
                result_data["_tool_name"] = item_tool
                results.append(result_data)

                if result_data.get("success", False) or "error" not in result_data:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as item_exc:
                error_count += 1
                results.append({
                    "_batch_index": idx,
                    "_tool_name": item_tool,
                    "error": str(item_exc),
                    "success": False,
                })

        elapsed = time.time() - start

        # Update BatchJob with results
        if batch_id > 0:
            session = get_session()
            try:
                batch_job = session.query(BatchJob).get(batch_id)
                if batch_job:
                    batch_job.status = "completed" if error_count == 0 else "completed_with_errors"
                    batch_job.completed_at = datetime.utcnow()
                    batch_job.results_json = json.dumps(results, default=str)
                    session.commit()
            except Exception as db_exc:
                session.rollback()
                logger.error("Failed to update BatchJob: %s", db_exc)
            finally:
                session.close()

        return json.dumps({
            "success": error_count == 0,
            "batch_id": batch_id,
            "batch_name": batch_name,
            "total_items": len(items),
            "success_count": success_count,
            "error_count": error_count,
            "generation_time_seconds": round(elapsed, 2),
            "results": results,
        })

    except Exception as exc:
        logger.exception("generate_batch failed")
        return json.dumps({"error": str(exc), "success": False})


def _handle_search_content_library(tool_input: dict) -> str:
    """Search the content library for generated content.

    Parameters
    ----------
    tool_input : dict
        Expected keys: ``query`` (str), ``content_type`` (str, optional),
        ``approved_only`` (bool, optional), ``limit`` (int, optional).

    Returns
    -------
    str
        JSON array of matching content records.
    """
    try:
        query = tool_input.get("query", "").strip()
        content_type = tool_input.get("content_type", "all").strip().lower()
        approved_only = tool_input.get("approved_only", False)
        limit = int(tool_input.get("limit", 50))

        session = get_session()
        try:
            results = []

            # Search GeneratedContent table
            gc_query = session.query(GeneratedContent)

            if content_type and content_type != "all":
                gc_query = gc_query.filter(
                    GeneratedContent.content_type == content_type
                )

            if query:
                like_pattern = f"%{query}%"
                gc_query = gc_query.filter(
                    GeneratedContent.title.ilike(like_pattern)
                )

            gc_items = (
                gc_query.order_by(GeneratedContent.generated_at.desc())
                .limit(limit)
                .all()
            )

            for item in gc_items:
                results.append({
                    "id": item.id,
                    "title": item.title,
                    "content_type": item.content_type,
                    "output_path": item.output_path,
                    "format": item.format,
                    "generated_at": (
                        item.generated_at.isoformat() if item.generated_at else None
                    ),
                    "generation_time_seconds": item.generation_time_seconds,
                    "user_rating": item.user_rating,
                    "source": "generated_content",
                })

            # Also search ContentLibraryItem table
            cli_query = session.query(ContentLibraryItem)

            if approved_only:
                cli_query = cli_query.filter(
                    ContentLibraryItem.is_approved.is_(True)
                )

            if query:
                like_pattern = f"%{query}%"
                cli_query = cli_query.filter(
                    (ContentLibraryItem.title.ilike(like_pattern))
                    | (ContentLibraryItem.tags.ilike(like_pattern))
                    | (ContentLibraryItem.description.ilike(like_pattern))
                )

            cli_items = cli_query.limit(limit).all()

            for item in cli_items:
                results.append({
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "category": item.category,
                    "tags": item.tags,
                    "is_approved": item.is_approved,
                    "download_count": item.download_count,
                    "generated_content_id": item.generated_content_id,
                    "source": "content_library",
                })

            return json.dumps({
                "results": results,
                "count": len(results),
                "query": query,
                "content_type_filter": content_type,
                "approved_only": approved_only,
            })
        finally:
            session.close()

    except Exception as exc:
        logger.error("search_content_library failed: %s", exc)
        return json.dumps({"error": str(exc), "results": [], "count": 0})


def _handle_get_content_stats(tool_input: dict) -> str:
    """Retrieve content statistics using the AnalyticsEngine.

    Parameters
    ----------
    tool_input : dict
        Expected keys: ``stat_type`` (str) -- one of "volume", "timeline",
        "generation_time", "costs", "templates", "library", "ratings",
        "time_saved", "storage", "batch", "dashboard", "breakdown".

    Returns
    -------
    str
        JSON object with the requested statistics.
    """
    try:
        if AnalyticsEngine is None:
            return json.dumps({
                "error": "Analytics engine not available.",
                "success": False,
            })

        stat_type = tool_input.get("stat_type", "dashboard").strip().lower()
        days = int(tool_input.get("days", 30))

        engine = AnalyticsEngine()

        stat_dispatch = {
            "volume": lambda: engine.get_generation_volume(days=days),
            "timeline": lambda: engine.get_generation_timeline(days=days),
            "generation_time": lambda: engine.get_avg_generation_time(),
            "costs": lambda: engine.get_api_cost_estimate(days=days),
            "templates": lambda: engine.get_template_usage(),
            "library": lambda: engine.get_library_stats(),
            "ratings": lambda: engine.get_rating_distribution(),
            "time_saved": lambda: engine.get_time_saved_estimate(),
            "storage": lambda: engine.get_storage_usage(),
            "batch": lambda: engine.get_batch_job_stats(),
            "dashboard": lambda: engine.get_dashboard_summary(),
            "breakdown": lambda: engine.get_content_type_breakdown(),
        }

        handler = stat_dispatch.get(stat_type)
        if handler is None:
            return json.dumps({
                "error": f"Unknown stat_type: '{stat_type}'.",
                "available_types": sorted(stat_dispatch.keys()),
            })

        data = handler()

        return json.dumps({
            "stat_type": stat_type,
            "data": data,
            "days": days,
        }, default=str)

    except Exception as exc:
        logger.error("get_content_stats failed: %s", exc)
        return json.dumps({"error": str(exc)})


def _handle_approve_content(tool_input: dict) -> str:
    """Approve a content library item.

    Parameters
    ----------
    tool_input : dict
        Expected keys: ``content_id`` (int).

    Returns
    -------
    str
        JSON object with success/failure message.
    """
    try:
        content_id = tool_input.get("content_id")
        if content_id is None:
            return json.dumps({"error": "No content_id provided.", "success": False})

        content_id = int(content_id)

        session = get_session()
        try:
            item = (
                session.query(ContentLibraryItem)
                .filter(ContentLibraryItem.id == content_id)
                .first()
            )

            if item is None:
                # Also check GeneratedContent in case the ID refers to that table
                gc_item = (
                    session.query(GeneratedContent)
                    .filter(GeneratedContent.id == content_id)
                    .first()
                )
                if gc_item is None:
                    return json.dumps({
                        "error": f"Content item with id={content_id} not found.",
                        "success": False,
                    })

                # Create a library item from the GeneratedContent record
                item = ContentLibraryItem(
                    generated_content_id=gc_item.id,
                    title=gc_item.title,
                    description=f"Auto-approved {gc_item.content_type}",
                    category=gc_item.content_type,
                    is_approved=True,
                )
                session.add(item)
                session.commit()

                return json.dumps({
                    "success": True,
                    "message": (
                        f"Content '{gc_item.title}' (GeneratedContent id={content_id}) "
                        f"added to library and approved."
                    ),
                    "library_item_id": item.id,
                })

            item.is_approved = True
            session.commit()

            return json.dumps({
                "success": True,
                "message": f"Content '{item.title}' (id={content_id}) approved.",
                "content_id": content_id,
            })
        finally:
            session.close()

    except Exception as exc:
        logger.error("approve_content failed: %s", exc)
        return json.dumps({"error": str(exc), "success": False})


def _handle_list_templates(tool_input: dict) -> str:
    """List available templates from the database and built-in registry.

    Parameters
    ----------
    tool_input : dict
        Expected keys: ``template_type`` (str, optional) -- "all", "pptx",
        "docx", "brand_guidelines", etc.

    Returns
    -------
    str
        JSON array of template records.
    """
    try:
        template_type = tool_input.get("template_type", "all").strip().lower()

        results = []

        # Query Template table
        session = get_session()
        try:
            q = session.query(Template)
            if template_type and template_type != "all":
                q = q.filter(Template.template_type == template_type)

            db_templates = q.order_by(Template.usage_count.desc()).all()

            for tmpl in db_templates:
                results.append({
                    "id": tmpl.id,
                    "name": tmpl.name,
                    "template_type": tmpl.template_type,
                    "file_path": tmpl.file_path,
                    "description": tmpl.description,
                    "usage_count": tmpl.usage_count,
                    "created_at": (
                        tmpl.created_at.isoformat() if tmpl.created_at else None
                    ),
                    "source": "database",
                })
        finally:
            session.close()

        # Include built-in document templates
        if template_type in ("all", "docx", "document"):
            for doc_type, info in DOCUMENT_TEMPLATES.items():
                results.append({
                    "id": None,
                    "name": info.get("name", doc_type),
                    "template_type": "docx",
                    "doc_type_key": doc_type,
                    "description": info.get("description", ""),
                    "typical_pages": info.get("typical_pages", ""),
                    "use_cases": info.get("use_cases", []),
                    "source": "built_in",
                })

        return json.dumps({
            "templates": results,
            "count": len(results),
            "filter": template_type,
        })

    except Exception as exc:
        logger.error("list_templates failed: %s", exc)
        return json.dumps({"error": str(exc), "templates": [], "count": 0})


def _handle_translate_content(tool_input: dict) -> str:
    """Translate content or a document to another language.

    Parameters
    ----------
    tool_input : dict
        Expected keys: ``target_language`` (str), ``content_id`` (int, optional),
        ``text`` (str, optional), ``source_language`` (str, optional),
        ``file_path`` (str, optional).

    Returns
    -------
    str
        JSON object with translated file path or translated text.
    """
    try:
        if TranslationEngine is None:
            return json.dumps({
                "error": "Translation engine not available. "
                         "Check that DeepL or Anthropic SDK is installed.",
                "success": False,
            })

        target_lang = tool_input.get("target_language", "").strip().lower()
        source_lang = tool_input.get("source_language", "en").strip().lower()
        content_id = tool_input.get("content_id")
        text = tool_input.get("text", "")
        file_path = tool_input.get("file_path", "")

        if not target_lang:
            return json.dumps({
                "error": "No target_language specified.",
                "success": False,
            })

        engine = TranslationEngine()

        # If content_id is provided, look up the file path
        if content_id is not None:
            content_id = int(content_id)
            session = get_session()
            try:
                gc_item = (
                    session.query(GeneratedContent)
                    .filter(GeneratedContent.id == content_id)
                    .first()
                )
                if gc_item is None:
                    return json.dumps({
                        "error": f"Content with id={content_id} not found.",
                        "success": False,
                    })
                file_path = gc_item.output_path or ""
            finally:
                session.close()

        # Translate a document file
        if file_path:
            logger.info("Translating document '%s' to %s", file_path, target_lang)
            result = engine.translate_document(
                file_path=file_path,
                target_lang=target_lang,
                source_lang=source_lang,
            )

            if result.get("success"):
                return json.dumps({
                    "success": True,
                    "output_path": result.get("output_path", ""),
                    "original_path": result.get("original_path", file_path),
                    "target_language": target_lang,
                    "source_language": source_lang,
                    "word_count": result.get("word_count", 0),
                })
            else:
                return json.dumps({
                    "error": result.get("error", "Translation failed."),
                    "success": False,
                })

        # Translate plain text
        if text:
            logger.info("Translating text to %s", target_lang)
            result = engine.translate_text(
                text=text,
                target_lang=target_lang,
                source_lang=source_lang,
            )

            if result.get("success"):
                return json.dumps({
                    "success": True,
                    "translated_text": result.get("translated_text", ""),
                    "source_language": source_lang,
                    "target_language": target_lang,
                    "provider": result.get("provider", "unknown"),
                    "brand_terms_preserved": result.get("brand_terms_preserved", []),
                })
            else:
                return json.dumps({
                    "error": result.get("error", "Translation failed."),
                    "success": False,
                })

        return json.dumps({
            "error": "No content_id, file_path, or text provided for translation.",
            "success": False,
        })

    except Exception as exc:
        logger.exception("translate_content failed")
        return json.dumps({"error": str(exc), "success": False})


def _handle_search_brand_knowledge(tool_input: dict) -> str:
    """Search the vector store for brand knowledge using semantic search.

    Parameters
    ----------
    tool_input : dict
        Expected keys: ``query`` (str), ``collection`` (str, optional),
        ``n_results`` (int, optional).

    Returns
    -------
    str
        JSON object with search results.
    """
    try:
        if VectorStore is None:
            return json.dumps({
                "error": "Vector store not available. Check ChromaDB installation.",
                "success": False,
            })

        query = tool_input.get("query", "").strip()
        collection = tool_input.get("collection", "all").strip().lower()
        n_results = int(tool_input.get("n_results", 5))

        if not query:
            return json.dumps({
                "error": "No search query provided.",
                "success": False,
            })

        store = VectorStore()

        # Determine which collections to search
        if collection == "all":
            collections_to_search = list(VectorStore.COLLECTIONS.keys())
        else:
            if collection in VectorStore.COLLECTIONS:
                collections_to_search = [collection]
            else:
                return json.dumps({
                    "error": f"Unknown collection: '{collection}'.",
                    "available_collections": list(VectorStore.COLLECTIONS.keys()),
                    "success": False,
                })

        all_results = []

        for coll_name in collections_to_search:
            try:
                search_results = store.query(
                    collection_name=coll_name,
                    query_text=query,
                    n_results=n_results,
                )

                ids = search_results.get("ids", [[]])[0]
                documents = search_results.get("documents", [[]])[0]
                metadatas = search_results.get("metadatas", [[]])[0]
                distances = search_results.get("distances", [[]])[0]

                for i, doc_id in enumerate(ids):
                    all_results.append({
                        "collection": coll_name,
                        "id": doc_id,
                        "document": documents[i] if i < len(documents) else "",
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "distance": distances[i] if i < len(distances) else None,
                    })
            except Exception as coll_exc:
                logger.warning(
                    "Failed to search collection '%s': %s", coll_name, coll_exc
                )

        # Sort by distance (lower is better / more similar)
        all_results.sort(key=lambda r: r.get("distance", float("inf")))

        # Limit total results
        all_results = all_results[:n_results]

        return json.dumps({
            "results": all_results,
            "count": len(all_results),
            "query": query,
            "collections_searched": collections_to_search,
        }, default=str)

    except Exception as exc:
        logger.error("search_brand_knowledge failed: %s", exc)
        return json.dumps({"error": str(exc), "results": [], "count": 0})


def _handle_web_search(tool_input: dict) -> str:
    """Perform a web search for external information (Research mode only).

    This is a simplified implementation that returns a helpful message
    about web search limitations.  In production, this would integrate
    with a web search API (e.g. Brave Search, Serper, etc.).

    Parameters
    ----------
    tool_input : dict
        Expected keys: ``query`` (str), ``num_results`` (int, optional).

    Returns
    -------
    str
        JSON object with search results or guidance.
    """
    try:
        query = tool_input.get("query", "").strip()
        num_results = int(tool_input.get("num_results", 5))

        if not query:
            return json.dumps({
                "error": "No search query provided.",
                "success": False,
            })

        # In production, this would call a real search API.
        # For now, we return guidance about using external knowledge.
        logger.info("Web search requested: '%s' (results: %d)", query, num_results)

        return json.dumps({
            "success": True,
            "query": query,
            "note": (
                "Web search is in preview mode. For now, I'll use my general "
                "knowledge to help with this query. In a future update, this "
                "will connect to a live web search API for real-time results."
            ),
            "results": [],
            "source_type": "external",
            "disclaimer": (
                "[EXTERNAL] This information comes from general knowledge, "
                "not from your brand repository. Please verify before using "
                "in official brand content."
            ),
        })

    except Exception as exc:
        logger.error("web_search failed: %s", exc)
        return json.dumps({"error": str(exc), "success": False})


def _handle_confirm_action(tool_input: dict) -> str:
    """Handle the confirm_action tool (engine-managed, not directly called).

    This tool is managed by the CopilotEngine's confirmation workflow.
    If Claude calls it directly, we return a message explaining the flow.

    Parameters
    ----------
    tool_input : dict
        Expected keys: ``action_summary`` (str).

    Returns
    -------
    str
        JSON object with confirmation guidance.
    """
    return json.dumps({
        "success": True,
        "message": (
            "Action plan has been presented to the user. "
            "Waiting for user confirmation before proceeding."
        ),
        "action_summary": tool_input.get("action_summary", ""),
        "status": "pending_confirmation",
    })
