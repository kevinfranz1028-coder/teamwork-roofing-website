"""
Brand Intelligence Content Hub - Copilot Response Renderer

Renders CopilotResponse objects in Streamlit's chat interface.
Handles text with markdown, generated file downloads, library save buttons,
and collapsible tool call transparency logs.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

import streamlit as st

from app.database.models import get_session, GeneratedContent, ContentLibraryItem

try:
    from app.copilot.verification import ConfidenceScore
except ImportError:
    ConfidenceScore = None

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# File type icons
# ---------------------------------------------------------------------------
FILE_ICONS = {
    "pptx": "📊",
    "docx": "📄",
    "pdf": "📕",
    "xlsx": "📗",
    "png": "🖼️",
    "svg": "🎨",
    "jpg": "🖼️",
    "jpeg": "🖼️",
    "zip": "📦",
    "json": "📋",
    "txt": "📝",
}

def _get_icon(fmt: str) -> str:
    return FILE_ICONS.get(fmt.lower(), "📎")

def _human_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_copilot_response(response, message_index: int = 0):
    """Render a CopilotResponse in the Streamlit chat interface.

    Parameters
    ----------
    response : CopilotResponse or dict
        The copilot response to render. Can be a CopilotResponse dataclass
        or a dict with keys: text, generated_files, tool_calls_made.
    message_index : int
        Used to generate unique widget keys across reruns.
    """
    # Handle both dataclass and dict
    if isinstance(response, dict):
        text = response.get("text", "")
        generated_files = response.get("generated_files", [])
        tool_calls = response.get("tool_calls_made", [])
        duration = response.get("duration_seconds", 0)
    else:
        text = response.text
        generated_files = response.generated_files
        tool_calls = response.tool_calls_made
        duration = response.duration_seconds

    # 1. Render main text as markdown
    if text:
        st.markdown(text)

    # 2. Render generated files with download + save buttons
    if generated_files:
        st.markdown("---")
        st.markdown("**Generated Files:**")
        for i, file_info in enumerate(generated_files):
            _render_file_card(file_info, f"msg{message_index}_file{i}")

    # 3. Render tool calls log (collapsed by default)
    if tool_calls:
        with st.expander(f"🔧 Actions taken ({len(tool_calls)})", expanded=False):
            for tc in tool_calls:
                name = tc.get("name", "unknown")
                summary = tc.get("summary", "")
                st.markdown(f"**→ {name}**: {summary}")

    # 4. Show duration if meaningful
    if duration > 1.0:
        st.caption(f"⏱️ {duration:.1f}s")

    # 5. Render confidence score if present
    confidence = None
    if isinstance(response, dict):
        confidence = response.get("confidence")
    elif hasattr(response, "confidence"):
        confidence = response.confidence

    if confidence:
        _render_confidence_badge(confidence)

    # 6. Render source attributions if present
    sources = None
    if isinstance(response, dict):
        sources = response.get("sources")
    elif hasattr(response, "sources"):
        sources = response.sources

    if sources:
        _render_sources(sources)


def _render_file_card(file_info: dict, key_prefix: str):
    """Render a single generated file with download and library buttons."""
    title = file_info.get("title", "Generated File")
    file_path = file_info.get("path", "")
    fmt = file_info.get("format", "")

    # Auto-detect format from path if not provided
    if not fmt and file_path:
        fmt = Path(file_path).suffix.lstrip(".")

    icon = _get_icon(fmt)

    # Get file size
    size_str = file_info.get("size", "")
    if not size_str and file_path and os.path.exists(file_path):
        size_str = _human_size(os.path.getsize(file_path))

    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.markdown(f"{icon} **{title}**")
        st.caption(f"{fmt.upper()} • {size_str}" if size_str else fmt.upper())

    with col2:
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                st.download_button(
                    "⬇️ Download",
                    data=f.read(),
                    file_name=os.path.basename(file_path),
                    key=f"{key_prefix}_dl",
                    use_container_width=True,
                )
        else:
            st.caption("File not found")

    with col3:
        if st.button("📚 Save to Library", key=f"{key_prefix}_lib",
                      use_container_width=True):
            _save_to_library(file_info)
            st.success("Saved!")


def _render_confidence_badge(confidence):
    """Render a confidence score badge in the chat."""
    if isinstance(confidence, dict):
        overall = confidence.get("overall", 0)
        factual = confidence.get("factual_accuracy", 0)
        brand = confidence.get("brand_alignment", 0)
        source_cov = confidence.get("source_coverage", 0)
        unverified = confidence.get("unverified_claims", [])
    elif hasattr(confidence, "overall"):
        overall = confidence.overall
        factual = confidence.factual_accuracy
        brand = confidence.brand_alignment
        source_cov = confidence.source_coverage
        unverified = confidence.unverified_claims if hasattr(confidence, "unverified_claims") else []
    else:
        return

    # Color coding
    if overall >= 0.8:
        color = "#28a745"
        label = "High Confidence"
    elif overall >= 0.5:
        color = "#ffc107"
        label = "Medium Confidence"
    else:
        color = "#dc3545"
        label = "Low Confidence"

    with st.expander(f"📊 {label} ({overall:.0%})", expanded=False):
        cols = st.columns(3)
        with cols[0]:
            st.metric("Factual Accuracy", f"{factual:.0%}")
        with cols[1]:
            st.metric("Brand Alignment", f"{brand:.0%}")
        with cols[2]:
            st.metric("Source Coverage", f"{source_cov:.0%}")

        if unverified:
            st.markdown("**Unverified Claims:**")
            for claim in unverified[:5]:
                st.markdown(f"- ⚠️ {claim}")


def _render_sources(sources):
    """Render source attribution list."""
    if not sources:
        return

    with st.expander(f"📎 Sources ({len(sources)})", expanded=False):
        for src in sources:
            if isinstance(src, dict):
                name = src.get("source_name", "Unknown")
                stype = src.get("source_type", "")
                excerpt = src.get("excerpt", "")
                score = src.get("relevance_score", 0)
            elif hasattr(src, "source_name"):
                name = src.source_name
                stype = src.source_type
                excerpt = src.excerpt
                score = src.relevance_score
            else:
                continue

            type_icon = {
                "brand_asset": "🏷️",
                "knowledge_base": "📚",
                "user_input": "👤",
                "generated": "🤖",
                "external": "🌐",
            }.get(stype, "📄")

            st.markdown(f"{type_icon} **{name}** ({score:.0%} relevant)")
            if excerpt:
                st.caption(excerpt[:150])


def render_confirmation_request(action_plan: dict, message_index: int = 0):
    """Render a confirmation request with Confirm/Cancel/Modify buttons.

    Parameters
    ----------
    action_plan : dict
        The action plan from CopilotResponse.action_plan
    message_index : int
        Used for unique widget keys.

    Returns
    -------
    str or None
        "confirmed", "cancelled", "modified", or None if no button pressed.
    """
    plan = action_plan.get("plan", action_plan)

    st.markdown("---")
    st.markdown("### ⚡ Action Plan")

    action_label = plan.get("action", "Unknown Action")
    title = plan.get("title", "")
    estimated_cost = plan.get("estimated_cost", "Unknown")

    st.markdown(f"**Action:** {action_label}")
    if title:
        st.markdown(f"**Title:** {title}")

    details = plan.get("details", {})
    if details:
        st.markdown("**Parameters:**")
        for k, v in details.items():
            if isinstance(v, list):
                v = ", ".join(str(i) for i in v)
            st.markdown(f"- {k.replace('_', ' ').title()}: {v}")

    st.markdown(f"**Estimated Cost:** {estimated_cost}")

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    result = None
    with col1:
        if st.button("✅ Confirm", key=f"confirm_{message_index}", use_container_width=True, type="primary"):
            result = "confirmed"
    with col2:
        if st.button("❌ Cancel", key=f"cancel_{message_index}", use_container_width=True):
            result = "cancelled"
    with col3:
        if st.button("✏️ Modify", key=f"modify_{message_index}", use_container_width=True):
            result = "modified"

    return result


def render_project_tracker(project):
    """Render the active project tracker in the sidebar or main area.

    Parameters
    ----------
    project : Project or dict
        The active project to render.
    """
    if project is None:
        return

    if isinstance(project, dict):
        title = project.get("title", "Untitled Project")
        steps = project.get("steps", [])
        status = project.get("status", "active")
    elif hasattr(project, "title"):
        title = project.title
        steps = project.steps if hasattr(project, "steps") else []
        status = project.status if hasattr(project, "status") else "active"
    else:
        return

    total = len(steps)
    completed = sum(
        1 for s in steps
        if (s.get("status") if isinstance(s, dict) else getattr(s, "status", "")) == "completed"
    )
    percentage = (completed / total * 100) if total > 0 else 0

    st.markdown(f"**{title}** ({status})")
    st.progress(percentage / 100)
    st.caption(f"{completed}/{total} steps completed ({percentage:.0f}%)")

    for step in steps:
        if isinstance(step, dict):
            step_title = step.get("title", "Step")
            step_status = step.get("status", "pending")
        else:
            step_title = getattr(step, "title", "Step")
            step_status = getattr(step, "status", "pending")

        status_icon = {
            "completed": "✅",
            "in_progress": "🔄",
            "pending": "⬜",
            "skipped": "⏭️",
            "failed": "❌",
        }.get(step_status, "⬜")

        st.markdown(f"{status_icon} {step_title}")


def _save_to_library(file_info: dict):
    """Save a generated file to the content library."""
    try:
        session = get_session()

        # Check if already in library
        existing = session.query(ContentLibraryItem).filter(
            ContentLibraryItem.title == file_info.get("title", "Untitled")
        ).first()

        if existing:
            session.close()
            return

        # Find or create GeneratedContent record
        gen_content = None
        if file_info.get("path"):
            gen_content = session.query(GeneratedContent).filter(
                GeneratedContent.output_path == file_info["path"]
            ).first()

        item = ContentLibraryItem(
            generated_content_id=gen_content.id if gen_content else None,
            title=file_info.get("title", "Untitled"),
            description=f"Generated via Copilot",
            tags=file_info.get("format", ""),
            category=file_info.get("format", "general"),
            is_approved=False,
            download_count=0,
        )
        session.add(item)
        session.commit()
        session.close()
    except Exception as exc:
        logger.warning("Could not save to library: %s", exc)


def render_welcome_message():
    """Render the initial welcome message when the copilot starts."""
    st.markdown("""
**Welcome! I'm your Brand Intelligence Copilot.**

I can help you with:
- 📊 **Presentations** — Create branded slide decks from any topic or source material
- 📄 **Documents** — Generate job aids, case studies, reports, SOPs, and more
- 📚 **Training** — Build complete training packages with decks, guides, quizzes, and handouts
- 🖼️ **Visuals** — Create flowcharts, timelines, org charts, and infographics
- 🔍 **Search** — Find existing content in your brand repository and content library
- 🌐 **Translate** — Translate any content while preserving brand terminology
- 📈 **Analytics** — Get stats on content generation, usage, and costs

**Just tell me what you need in plain language.** For example:
- *"Create a 10-slide training deck on our new product launch"*
- *"Generate a job aid for the customer onboarding process"*
- *"What presentations have we created this month?"*
- *"Translate the latest training deck to Spanish"*
""")


def render_error_message(error: str):
    """Render an error message in the chat interface."""
    st.error(f"Something went wrong: {error}")
    st.info("You can try rephrasing your request or check the Settings page for configuration issues.")
