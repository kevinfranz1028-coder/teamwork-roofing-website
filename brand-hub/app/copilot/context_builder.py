"""
Brand Intelligence Content Hub - Copilot Context Builder

Builds the rich system prompt that gives the Copilot full awareness of the
app's current state.  Called on every message to Claude so the assistant
always has an up-to-date picture of brand configuration, templates,
generated content, assets, and vector-store health.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from sqlalchemy import func

from app.config import BASE_DIR, BRAND_ASSETS_DIR, OUTPUT_DIR
from app.database.models import (
    BatchJob,
    BrandAsset,
    BrandConfig,
    ContentLibraryItem,
    GeneratedContent,
    PromptTemplate,
    Template,
    get_session,
)

try:
    from app.copilot.verification import get_grounding_instruction, KnowledgeMode
except ImportError:
    get_grounding_instruction = None
    KnowledgeMode = None

try:
    from app.copilot.project_tracker import ProjectTracker
except ImportError:
    ProjectTracker = None

logger = logging.getLogger(__name__)

# Brand-config file path (written by BrandWizard)
_BRAND_CONFIG_PATH = BRAND_ASSETS_DIR / "brand_config.json"


# ---------------------------------------------------------------------------
# PUBLIC ENTRY POINT
# ---------------------------------------------------------------------------

def build_copilot_system_prompt(
    knowledge_mode: str = "grounded",
    pinned_context: list | None = None,
    active_project: dict | None = None,
) -> str:
    """Build a comprehensive system prompt with current app state.

    Assembles:
      1. Brand config summary (company name, colors, fonts, voice)
      2. Available templates list
      3. Content library stats (total items, by type, recent)
      4. Recent generations (last 10)
      5. Uploaded asset summary
      6. Vector store status

    Returns a single formatted string for the system prompt.
    """
    brand_config = _get_brand_config_summary()
    templates = _get_template_list()
    stats = _get_content_stats()
    recent = _get_recent_generations(limit=10)
    assets = _get_asset_summary()
    vector_status = _get_vector_store_status()
    today = datetime.now().strftime("%A, %B %d, %Y")

    # Knowledge mode grounding rules
    grounding = ""
    if get_grounding_instruction is not None:
        grounding = get_grounding_instruction(knowledge_mode)

    # Pinned context
    pinned_text = ""
    if pinned_context:
        pinned_lines = []
        for pin in pinned_context:
            label = pin.get("label", "Note")
            text = pin.get("text", "")
            pinned_lines.append(f"- **{label}**: {text}")
        pinned_text = "\n".join(pinned_lines)

    # Active project
    project_text = ""
    if active_project:
        project_text = (
            f"Project: {active_project.get('title', 'Untitled')}\n"
            f"Status: {active_project.get('status', 'active')}\n"
            f"Progress: {active_project.get('progress', 'N/A')}"
        )

    prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        brand_config=brand_config,
        templates=templates,
        stats=stats,
        recent=recent,
        assets=assets,
        vector_status=vector_status,
        today=today,
        knowledge_mode=knowledge_mode.upper(),
        grounding=grounding,
        pinned_context=pinned_text if pinned_text else "(No pinned context)",
        active_project=project_text if project_text else "(No active project)",
    )

    logger.debug("Built copilot system prompt (%d chars)", len(prompt))
    return prompt


# ---------------------------------------------------------------------------
# HELPER: Brand Configuration
# ---------------------------------------------------------------------------

def _get_brand_config_summary() -> str:
    """Load brand_config.json and format as readable text.

    Returns something like:
    Company: Acme Corp
    Primary Color: #0066CC
    Secondary Color: #004499
    Font: Arial
    Voice: Professional, confident, approachable
    Terminology: [list of brand terms]
    """
    try:
        if not _BRAND_CONFIG_PATH.exists():
            return _get_brand_config_from_db()

        with open(_BRAND_CONFIG_PATH, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)

        lines: list[str] = []

        # Company name
        company = cfg.get("company_name", "")
        lines.append(f"Company: {company}" if company else "Company: (not set)")

        # Colors
        colors = cfg.get("colors", {})
        if isinstance(colors, dict):
            for key, label in [
                ("primary", "Primary Color"),
                ("secondary", "Secondary Color"),
                ("accent", "Accent Color"),
                ("background", "Background Color"),
                ("text", "Text Color"),
            ]:
                val = colors.get(key, "")
                if val:
                    lines.append(f"{label}: {val}")
        if not any("Color" in ln for ln in lines):
            lines.append("Colors: (not configured)")

        # Fonts
        fonts = cfg.get("fonts", {})
        if isinstance(fonts, dict):
            for key, label in [("heading", "Font (heading)"), ("body", "Font (body)")]:
                val = fonts.get(key, "")
                if val:
                    lines.append(f"{label}: {val}")
        if not any("Font" in ln for ln in lines):
            lines.append("Fonts: (not configured)")

        # Voice
        voice = cfg.get("voice", {})
        if isinstance(voice, dict):
            tone = voice.get("tone", "")
            formality = voice.get("formality", "")
            vocab = voice.get("vocabulary_level", "")
            themes = voice.get("messaging_themes", [])
            key_phrases = voice.get("key_phrases", [])
            avoid = voice.get("avoid_phrases", [])

            if tone:
                lines.append(f"Voice Tone: {tone}")
            if formality:
                lines.append(f"Formality Level: {formality}/5")
            if vocab:
                lines.append(f"Vocabulary Level: {vocab}")
            if themes and isinstance(themes, list):
                lines.append(f"Messaging Themes: {', '.join(str(t) for t in themes)}")
            if key_phrases and isinstance(key_phrases, list):
                display = key_phrases[:8]
                suffix = f" (+{len(key_phrases) - 8} more)" if len(key_phrases) > 8 else ""
                lines.append(f"Key Phrases: {', '.join(str(p) for p in display)}{suffix}")
            if avoid and isinstance(avoid, list):
                lines.append(f"Avoid Phrases: {', '.join(str(a) for a in avoid)}")
        if not any("Voice" in ln or "Tone" in ln for ln in lines):
            lines.append("Voice: (not configured)")

        # Terminology
        terminology = cfg.get("terminology", {})
        if isinstance(terminology, dict):
            preferred = terminology.get("preferred_terms", {})
            programs = terminology.get("program_names", [])
            acronyms = terminology.get("acronyms", {})
            term_parts: list[str] = []
            if preferred:
                term_parts.append(f"{len(preferred)} preferred terms")
            if programs:
                term_parts.append(f"{len(programs)} program names")
            if acronyms:
                term_parts.append(f"{len(acronyms)} acronyms")
            if term_parts:
                lines.append(f"Terminology: {', '.join(term_parts)} configured")
            else:
                lines.append("Terminology: (none configured)")
        else:
            lines.append("Terminology: (none configured)")

        return "\n".join(lines)

    except Exception as exc:
        logger.warning("Failed to load brand config summary: %s", exc)
        return "(Brand configuration not available)"


def _get_brand_config_from_db() -> str:
    """Fall-back: read key-value pairs from the BrandConfig table."""
    try:
        session = get_session()
        try:
            rows = session.query(BrandConfig).all()
            if not rows:
                return "(No brand configuration found. Run the Brand Wizard to set up.)"
            lines: list[str] = []
            for row in rows:
                key = row.config_key or ""
                value = row.config_value or ""
                if len(value) > 200:
                    value = value[:200] + "..."
                lines.append(f"{key}: {value}")
            return "\n".join(lines) if lines else "(No brand configuration found.)"
        finally:
            session.close()
    except Exception as exc:
        logger.warning("Failed to read BrandConfig from DB: %s", exc)
        return "(Brand configuration not available)"


# ---------------------------------------------------------------------------
# HELPER: Templates
# ---------------------------------------------------------------------------

def _get_template_list() -> str:
    """Query Template table and list available templates.

    Returns formatted list like:
    - Job Aid (docx) -- 15 uses
    - Case Study (docx) -- 8 uses
    - Training Deck (pptx) -- 12 uses
    Also include built-in document/presentation templates.
    """
    try:
        session = get_session()
        try:
            templates = (
                session.query(Template)
                .order_by(Template.usage_count.desc())
                .all()
            )
            if not templates:
                return "(No custom templates uploaded yet.)"

            lines: list[str] = []
            for tmpl in templates:
                name = tmpl.name or "Untitled"
                ttype = tmpl.template_type or "unknown"
                uses = tmpl.usage_count or 0
                desc = f" -- {tmpl.description}" if tmpl.description else ""
                lines.append(f"- {name} ({ttype}) -- {uses} uses{desc}")

            lines.append(f"Total: {len(templates)} templates available")
            return "\n".join(lines)
        finally:
            session.close()
    except Exception as exc:
        logger.warning("Failed to load template list: %s", exc)
        return "(Template list not available)"


# ---------------------------------------------------------------------------
# HELPER: Content Statistics
# ---------------------------------------------------------------------------

def _get_content_stats() -> str:
    """Query GeneratedContent for statistics.

    Returns:
    Total generated: 45 items
    By type: presentations (12), documents (18), training (8), visuals (7)
    Library items: 30 (25 approved, 5 pending)
    Average rating: 4.2/5
    """
    try:
        session = get_session()
        try:
            total_generated = (
                session.query(func.count(GeneratedContent.id)).scalar() or 0
            )

            if total_generated == 0:
                return "Total generated: 0 items\nNo content has been generated yet."

            # Breakdown by content_type
            type_counts = (
                session.query(
                    GeneratedContent.content_type,
                    func.count(GeneratedContent.id),
                )
                .group_by(GeneratedContent.content_type)
                .all()
            )
            type_parts = [
                f"{ctype or 'other'} ({count})" for ctype, count in type_counts
            ]

            # Library items
            total_library = (
                session.query(func.count(ContentLibraryItem.id)).scalar() or 0
            )
            approved = (
                session.query(func.count(ContentLibraryItem.id))
                .filter(ContentLibraryItem.is_approved.is_(True))
                .scalar() or 0
            )
            pending = total_library - approved

            # Average user rating (ignoring nulls)
            avg_rating = (
                session.query(func.avg(GeneratedContent.user_rating))
                .filter(GeneratedContent.user_rating.isnot(None))
                .scalar()
            )

            # Active batch jobs
            active_batches = (
                session.query(func.count(BatchJob.id))
                .filter(BatchJob.status.in_(["pending", "running"]))
                .scalar() or 0
            )

            lines: list[str] = [f"Total generated: {total_generated} items"]
            if type_parts:
                lines.append(f"By type: {', '.join(type_parts)}")
            if total_library > 0:
                lines.append(
                    f"Library items: {total_library} "
                    f"({approved} approved, {pending} pending)"
                )
            else:
                lines.append("Library items: 0")
            if avg_rating is not None:
                lines.append(f"Average rating: {avg_rating:.1f}/5")
            else:
                lines.append("Average rating: (no ratings yet)")
            if active_batches > 0:
                lines.append(f"Active batch jobs: {active_batches}")

            return "\n".join(lines)
        finally:
            session.close()
    except Exception as exc:
        logger.warning("Failed to load content stats: %s", exc)
        return "(Content statistics not available)"


# ---------------------------------------------------------------------------
# HELPER: Recent Generations
# ---------------------------------------------------------------------------

def _get_recent_generations(limit: int = 10) -> str:
    """Get last N generated items.

    Returns formatted list:
    1. "Q1 Training Deck" (presentation, Feb 25, stars)
    2. "Customer Onboarding SOP" (document, Feb 24, stars)
    """
    try:
        session = get_session()
        try:
            items = (
                session.query(GeneratedContent)
                .order_by(GeneratedContent.generated_at.desc())
                .limit(limit)
                .all()
            )
            if not items:
                return "(No content generated yet.)"

            lines: list[str] = []
            for idx, item in enumerate(items, start=1):
                title = item.title or "Untitled"
                ctype = item.content_type or "unknown"
                date_str = (
                    item.generated_at.strftime("%b %d")
                    if item.generated_at else "unknown date"
                )
                if item.user_rating is not None:
                    filled = min(item.user_rating, 5)
                    stars = "\u2605" * filled + "\u2606" * (5 - filled)
                else:
                    stars = "unrated"
                lines.append(f'{idx}. "{title}" ({ctype}, {date_str}, {stars})')

            return "\n".join(lines)
        finally:
            session.close()
    except Exception as exc:
        logger.warning("Failed to load recent generations: %s", exc)
        return "(Recent generations not available)"


# ---------------------------------------------------------------------------
# HELPER: Uploaded Assets
# ---------------------------------------------------------------------------

def _get_asset_summary() -> str:
    """Summarize uploaded brand assets.

    Returns:
    Logos: 3 files
    Templates: 5 files
    Collateral: 12 files
    Total: 20 assets
    """
    try:
        session = get_session()
        try:
            type_counts = (
                session.query(BrandAsset.asset_type, func.count(BrandAsset.id))
                .filter(BrandAsset.is_active.is_(True))
                .group_by(BrandAsset.asset_type)
                .all()
            )
            total_active = sum(count for _, count in type_counts)
            total_all = session.query(func.count(BrandAsset.id)).scalar() or 0

            if total_all == 0:
                return "(No brand assets uploaded yet.)"

            label_map = {
                "logo": "Logos",
                "font": "Fonts",
                "color": "Color Palettes",
                "template": "Templates",
                "collateral": "Collateral",
                "sample": "Voice Samples",
            }

            lines: list[str] = []
            for asset_type, count in sorted(type_counts, key=lambda x: -x[1]):
                label = label_map.get(
                    asset_type, asset_type.title() if asset_type else "Other"
                )
                lines.append(f"{label}: {count} files")

            inactive = total_all - total_active
            total_line = f"Total: {total_all} assets"
            if inactive > 0:
                total_line += f" ({total_active} active, {inactive} inactive)"
            lines.append(total_line)

            return "\n".join(lines)
        finally:
            session.close()
    except Exception as exc:
        logger.warning("Failed to load asset summary: %s", exc)
        return "(Asset summary not available)"


# ---------------------------------------------------------------------------
# HELPER: Vector Store Status
# ---------------------------------------------------------------------------

def _get_vector_store_status() -> str:
    """Check vector store collections.

    Returns:
    brand_content: 150 documents
    brand_voice: 5 samples
    generated_examples: 30 items
    terminology: 45 terms
    """
    try:
        from app.database.vector_store import VectorStore
        from app.config import get_chroma_path

        vs = VectorStore(persist_directory=get_chroma_path())
        stats = vs.get_collection_stats()

        suffix_map = {
            "brand_content": "documents",
            "brand_voice": "samples",
            "generated_examples": "items",
            "terminology": "terms",
        }

        lines: list[str] = []
        total_docs = 0
        for collection_name, count in stats.items():
            suffix = suffix_map.get(collection_name, "items")
            lines.append(f"{collection_name}: {count} {suffix}")
            total_docs += count

        if total_docs == 0:
            lines.append(
                "(Vector store is empty -- ingest brand materials "
                "to enable semantic search)"
            )

        if vs.is_fallback:
            lines.append("Status: In-memory fallback (ChromaDB unavailable)")
        else:
            lines.append("Status: ChromaDB persistent")

        return "\n".join(lines)

    except Exception as exc:
        logger.warning("Failed to read vector store status: %s", exc)
        return "(Vector store status not available)"


# ---------------------------------------------------------------------------
# SYSTEM PROMPT TEMPLATE
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_TEMPLATE = """\
You are the Brand Intelligence Copilot -- an expert AI assistant embedded \
inside the Brand Intelligence Content Hub. You are the user's strategic \
partner for all branded content creation.

## YOUR ROLE
You help the user create professional, on-brand content by understanding \
their needs, finding relevant resources in the brand repository, and \
executing content generation workflows. You can search the content library, \
generate presentations, documents, training materials, visuals, and more \
-- all through natural conversation.

You are proactive: suggest what might help, offer to create supporting \
materials, and anticipate needs. When the user describes what they need, \
figure out the best approach and either ask clarifying questions or execute \
directly if you have enough information.

## CURRENT BRAND CONFIGURATION
{brand_config}

## AVAILABLE TEMPLATES
{templates}

## CONTENT LIBRARY STATUS
{stats}

## RECENT GENERATIONS
{recent}

## UPLOADED BRAND ASSETS
{assets}

## VECTOR STORE STATUS
{vector_status}

## KNOWLEDGE MODE: {knowledge_mode}
{grounding}

## PINNED CONTEXT (session-level instructions from the user)
{pinned_context}

## ACTIVE PROJECT
{active_project}

## CONFIRMATION PROTOCOL
Before executing any generation tool (generate_presentation, generate_document,
generate_training_package, generate_visual, generate_batch) or modification tool
(update_brand_config, approve_content, translate_content), you MUST present an
action plan to the user showing:
1. What you plan to create/modify
2. Key parameters (title, type, slide count, etc.)
3. Estimated API cost
4. Sources you'll use

Read-only tools (search, get_config, list_templates, stats) execute immediately
without confirmation.

## HOW TO WORK
1. When the user asks for content, FIRST search for relevant existing \
materials and context using search_brand_assets and search_brand_knowledge
2. If you find relevant source material, reference it and ask if the user \
wants to use it
3. Use generate_presentation, generate_document, generate_training_package, \
or generate_visual to create content
4. Always confirm the approach before generating large content packages
5. After generation, offer related content that might be useful
6. When giving strategic advice, search the brand knowledge base for \
relevant context and examples

## CONVERSATION STYLE
- Be direct and action-oriented -- the user is busy
- When you have enough information, just do it rather than asking excessive \
questions
- Show your work: explain what you found, what you're using, and why
- After generating content, briefly describe what was created and offer \
next steps
- Use the brand terminology from the brand config in your responses
- If something fails, explain what happened and offer alternatives

## IMPORTANT
- You have access to ALL functions of the app through your tools
- You can chain multiple tools together (e.g., search for a file, then use \
it to generate a presentation)
- Always use the brand config for content generation -- never generate \
generic unbranded content
- When the user references "the curriculum" or "that file" or "yesterday's \
upload", use search_brand_assets to find what they mean
- If the user asks you to do something the app cannot do yet, honestly say \
so and suggest a workaround
- When in GROUNDED mode, mark any information gaps with [INSERT: description] \
and uncertain claims with [VERIFY: claim]
- When in ENHANCED mode, mark external knowledge with [EXTERNAL: source]
- Always include source attribution for facts and data you reference
- Respect pinned context instructions — they override default behavior

## TODAY'S DATE
{today}
"""
