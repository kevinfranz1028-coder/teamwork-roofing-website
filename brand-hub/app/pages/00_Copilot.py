"""
Brand Intelligence Content Hub - Copilot Chat Page

The DEFAULT landing page (page 00) of the Brand Intelligence Content Hub.
Provides a full conversational chat interface powered by Claude tool_use,
allowing users to generate presentations, documents, training packages,
visuals, reports, translations, and more through natural language.
"""

import json
import os
import sys
import time
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Page config (must be the first Streamlit command)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Brand Hub Copilot",
    page_icon="\U0001f9e0",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Copilot module imports (graceful degradation)
# ---------------------------------------------------------------------------
try:
    from app.copilot.engine import CopilotEngine, CopilotResponse
    from app.copilot.conversation import ConversationManager
    from app.copilot.response_renderer import (
        render_copilot_response,
        render_welcome_message,
        render_error_message,
        render_confirmation_request,
        render_project_tracker,
    )
    COPILOT_AVAILABLE = True
except ImportError as e:
    COPILOT_AVAILABLE = False
    _import_error = str(e)

try:
    from app.copilot.project_tracker import ProjectTracker
    TRACKER_AVAILABLE = True
except ImportError:
    TRACKER_AVAILABLE = False

try:
    from app.copilot.audit_log import AuditLog
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False

from app.config import BASE_DIR, BRAND_ASSETS_DIR, UPLOADS_DIR
from app.database.models import init_db

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
_CUSTOM_CSS = """
<style>
/* ---- Chat container ---- */
[data-testid="stChatMessage"] {
    padding: 1rem 1.2rem;
    border-radius: 12px;
    margin-bottom: 0.6rem;
}

/* ---- User bubble ---- */
[data-testid="stChatMessage"][data-testid-role="user"] {
    background: linear-gradient(135deg, #e8f0fe 0%, #d2e3fc 100%);
    border: 1px solid #c0d8f8;
}

/* ---- Assistant bubble ---- */
[data-testid="stChatMessage"][data-testid-role="assistant"] {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
}

/* ---- File cards ---- */
.file-card {
    background: #ffffff;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin: 0.4rem 0;
    transition: box-shadow 0.2s ease;
}
.file-card:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* ---- Quick action buttons ---- */
div[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    text-align: left;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 0.5rem 0.8rem;
    margin-bottom: 0.25rem;
    background: #ffffff;
    color: #212529;
    font-size: 0.88rem;
    transition: all 0.15s ease;
}
div[data-testid="stSidebar"] .stButton > button:hover {
    background: #e8f0fe;
    border-color: #4285f4;
    color: #1a73e8;
}

/* ---- Sidebar section headings ---- */
.sidebar-heading {
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #5f6368;
    margin-top: 1rem;
    margin-bottom: 0.4rem;
}

/* ---- Stats row ---- */
.stat-pill {
    display: inline-block;
    background: #e8f0fe;
    border-radius: 12px;
    padding: 0.2rem 0.6rem;
    font-size: 0.78rem;
    color: #1a73e8;
    margin-right: 0.4rem;
}

/* ---- Welcome card ---- */
.welcome-card {
    background: linear-gradient(135deg, #f0f4ff 0%, #e8f0fe 100%);
    border: 1px solid #c0d8f8;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin: 1rem 0;
}

/* ---- Responsive tweaks ---- */
@media (max-width: 768px) {
    [data-testid="stChatMessage"] {
        padding: 0.7rem 0.8rem;
    }
    .file-card {
        padding: 0.5rem 0.7rem;
    }
}
</style>
"""

st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Initialise database
# ---------------------------------------------------------------------------
if "db_ok" not in st.session_state:
    try:
        init_db()
        st.session_state["db_ok"] = True
    except Exception as exc:
        st.session_state["db_ok"] = False
        st.session_state["db_error"] = str(exc)

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.title("\U0001f9e0 Brand Hub Copilot")
st.caption("Your AI-powered brand content assistant")

if not COPILOT_AVAILABLE:
    st.warning(
        f"The Copilot module could not be loaded: **{_import_error}**. "
        "Please check that all dependencies are installed and the "
        "`app/copilot/` package is present."
    )
    st.info(
        "While the Copilot engine is unavailable, you can still use "
        "the other pages in the sidebar to generate content manually."
    )
    st.stop()


# ---------------------------------------------------------------------------
# Initialise Copilot engine and conversation manager (cached)
# ---------------------------------------------------------------------------
@st.cache_resource
def get_engine():
    """Return a singleton CopilotEngine instance."""
    return CopilotEngine()


engine = get_engine()
conversation = ConversationManager()


# ---------------------------------------------------------------------------
# Session-state defaults
# ---------------------------------------------------------------------------
if "copilot_uploaded_paths" not in st.session_state:
    st.session_state["copilot_uploaded_paths"] = []


# ---------------------------------------------------------------------------
# Helper: save uploaded files
# ---------------------------------------------------------------------------
def _save_uploaded_files(uploaded_files) -> list[str]:
    """Save uploaded files to UPLOADS_DIR and return their absolute paths."""
    paths: list[str] = []
    for f in uploaded_files:
        dest = UPLOADS_DIR / f.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as out:
            out.write(f.getbuffer())
        paths.append(str(dest))
    return paths


# ---------------------------------------------------------------------------
# Helper: build conversation export payload
# ---------------------------------------------------------------------------
def _build_export_payload() -> str:
    """Return JSON string of the current conversation for download."""
    try:
        return conversation.export_history()
    except Exception:
        return json.dumps({"error": "Could not export conversation"}, indent=2)


# ---------------------------------------------------------------------------
# Helper: compute sidebar stats
# ---------------------------------------------------------------------------
def _get_conversation_stats() -> dict:
    """Return lightweight stats about the current conversation."""
    display_msgs = conversation.get_display_messages()
    generated_files = conversation.get_generated_files()

    user_msgs = 0
    assistant_msgs = 0
    for msg in display_msgs:
        role = msg.role if hasattr(msg, "role") else msg.get("role", "")
        if role == "user":
            user_msgs += 1
        elif role == "assistant":
            assistant_msgs += 1

    return {
        "total_messages": len(display_msgs),
        "user_messages": user_msgs,
        "assistant_messages": assistant_msgs,
        "files_generated": len(generated_files),
    }


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    # -- Quick Actions -------------------------------------------------------
    st.markdown('<p class="sidebar-heading">Quick Actions</p>', unsafe_allow_html=True)

    quick_actions = [
        ("\U0001f3af New Presentation", "I need to create a new presentation"),
        ("\U0001f4c4 New Document", "I need to create a document"),
        ("\U0001f4da New Training Package", "I need to build a training package"),
        ("\U0001f5bc\ufe0f New Visual", "I need to create a visual diagram"),
        ("\U0001f4cb New Report", "I need to generate a report"),
        ("\U0001f50d Search Content", "What content do we have in the library?"),
        ("\U0001f310 Translate Content", "I need to translate some content"),
        ("\U0001f4c8 Show Stats", "Show me content generation statistics"),
    ]

    for label, prompt_text in quick_actions:
        if st.button(label, key=f"qa_{label}", use_container_width=True):
            st.session_state["quick_action"] = prompt_text
            st.rerun()

    st.markdown("---")

    # -- Knowledge Mode -------------------------------------------------------
    st.markdown(
        '<p class="sidebar-heading">Knowledge Mode</p>', unsafe_allow_html=True
    )

    knowledge_modes = {
        "grounded": "🔒 Grounded — Repository facts only",
        "enhanced": "🔓 Enhanced — Repository + general knowledge",
        "research": "🌐 Research — Full creative freedom",
    }
    current_mode = conversation.get_knowledge_mode()
    selected_mode = st.radio(
        "Knowledge Mode",
        options=list(knowledge_modes.keys()),
        format_func=lambda x: knowledge_modes[x],
        index=list(knowledge_modes.keys()).index(current_mode),
        key="knowledge_mode_radio",
        label_visibility="collapsed",
    )
    if selected_mode != current_mode:
        conversation.set_knowledge_mode(selected_mode)

    st.markdown("---")

    # -- Pinned Context -------------------------------------------------------
    st.markdown(
        '<p class="sidebar-heading">Pinned Context</p>', unsafe_allow_html=True
    )

    pinned = conversation.get_pinned_context()
    if pinned:
        for idx, pin in enumerate(pinned):
            label = pin.label if hasattr(pin, "label") else pin.get("label", "Note")
            text = pin.text if hasattr(pin, "text") else pin.get("text", "")
            col_pin, col_del = st.columns([4, 1])
            with col_pin:
                st.caption(f"📌 **{label}**: {text[:50]}...")
            with col_del:
                if st.button("✕", key=f"unpin_{idx}", help="Remove pin"):
                    conversation.remove_pinned_context(idx)
                    st.rerun()
    else:
        st.caption("No pinned context. Use 'pin: [instruction]' in chat.")

    with st.expander("➕ Add Pin", expanded=False):
        pin_label = st.text_input("Label", key="pin_label_input", placeholder="e.g., Tone")
        pin_text = st.text_input("Instruction", key="pin_text_input", placeholder="e.g., Always use formal tone")
        if st.button("Pin", key="btn_add_pin"):
            if pin_label and pin_text:
                conversation.add_pinned_context(pin_label, pin_text)
                st.rerun()

    st.markdown("---")

    # -- Conversation controls -----------------------------------------------
    st.markdown(
        '<p class="sidebar-heading">Conversation</p>', unsafe_allow_html=True
    )

    if st.button("\U0001f5d1\ufe0f Clear Conversation", key="btn_clear", use_container_width=True):
        conversation.clear()
        st.session_state["copilot_uploaded_paths"] = []
        st.rerun()

    # -- File Upload ---------------------------------------------------------
    with st.expander("\U0001f4ce Attach Files", expanded=False):
        uploaded_files = st.file_uploader(
            "Upload reference files",
            accept_multiple_files=True,
            type=["pdf", "docx", "pptx", "xlsx", "csv", "png", "jpg", "txt"],
            key="copilot_file_uploader",
            label_visibility="collapsed",
        )
        if uploaded_files:
            saved_paths = _save_uploaded_files(uploaded_files)
            if saved_paths:
                st.session_state["copilot_uploaded_paths"] = saved_paths
                st.success(f"{len(saved_paths)} file(s) attached")
                for p in saved_paths:
                    st.caption(f"  \u2022 {Path(p).name}")

    # -- Export conversation --------------------------------------------------
    export_json = _build_export_payload()
    st.download_button(
        "\U0001f4e5 Export Conversation",
        data=export_json,
        file_name="copilot_conversation.json",
        mime="application/json",
        key="btn_export",
        use_container_width=True,
    )

    # -- Audit Trail ----------------------------------------------------------
    if AUDIT_AVAILABLE:
        with st.expander("📋 Audit Trail", expanded=False):
            try:
                audit = AuditLog()
                recent = audit.get_recent_log(limit=20)
                if recent:
                    for entry in recent:
                        ts = entry.get("timestamp", "")
                        action = entry.get("action_type", "")
                        tool = entry.get("tool_name", "—")
                        st.caption(f"{ts[:16]} | {action} | {tool}")
                else:
                    st.caption("No audit entries yet.")
            except Exception:
                st.caption("Audit trail unavailable.")

    st.markdown("---")

    # -- Conversation stats ---------------------------------------------------
    st.markdown(
        '<p class="sidebar-heading">Session Stats</p>', unsafe_allow_html=True
    )
    stats = _get_conversation_stats()
    stat_col1, stat_col2 = st.columns(2)
    with stat_col1:
        st.metric("Messages", stats["total_messages"])
    with stat_col2:
        st.metric("Files Generated", stats["files_generated"])

    # -- Active Project -------------------------------------------------------
    if TRACKER_AVAILABLE:
        tracker = ProjectTracker()
        project = tracker.get_active_project()
        if project is not None:
            st.markdown("---")
            st.markdown(
                '<p class="sidebar-heading">Active Project</p>',
                unsafe_allow_html=True,
            )
            render_project_tracker(project)

    if not engine.available:
        st.markdown("---")
        st.warning(
            "Anthropic API key not configured. "
            "Set it on the **Settings** page to enable the Copilot."
        )


# ---------------------------------------------------------------------------
# Main chat area: display history
# ---------------------------------------------------------------------------
display_messages = conversation.get_display_messages()

if not display_messages:
    # Show the welcome card when the conversation is empty
    with st.chat_message("assistant", avatar="\U0001f9e0"):
        render_welcome_message()
else:
    for idx, msg in enumerate(display_messages):
        # Handle both DisplayMessage dataclass and dict representations.
        # session_state serialisation may convert dataclasses to dicts in
        # some Streamlit versions.
        if hasattr(msg, "role"):
            role = msg.role
            content = msg.content
            files = msg.files if hasattr(msg, "files") else []
            tool_calls = msg.tool_calls if hasattr(msg, "tool_calls") else []
        else:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            files = msg.get("files", [])
            tool_calls = msg.get("tool_calls", [])

        if role == "user":
            with st.chat_message("user"):
                st.markdown(content)
        elif role == "assistant":
            with st.chat_message("assistant", avatar="\U0001f9e0"):
                # Re-render through the response renderer so file cards
                # and tool-call expanders display correctly.
                if files or tool_calls:
                    render_copilot_response(
                        {
                            "text": content,
                            "generated_files": files,
                            "tool_calls_made": tool_calls,
                            "duration_seconds": 0,
                        },
                        message_index=idx,
                    )
                else:
                    st.markdown(content)


# ---------------------------------------------------------------------------
# Next-steps guidance
# ---------------------------------------------------------------------------

def _render_next_steps(response):
    """Show contextual next-steps guidance based on what the Copilot just did."""
    gen_files = response.generated_files if hasattr(response, "generated_files") else []
    tool_calls = response.tool_calls_made if hasattr(response, "tool_calls_made") else []
    tool_names = {tc.get("name", "") for tc in (tool_calls or [])}

    hints: list[str] = []

    if gen_files:
        for f in gen_files:
            fpath = f.get("path", "")
            if fpath:
                hints.append(f"Your file is ready: **{os.path.basename(fpath)}** — use the download button above to save it locally.")
        hints.append("You can also click **Save to Library** to store it for future use.")
        hints.append("Ask me to make changes, create a new version, or generate something else.")
    elif tool_names & {"generate_presentation", "generate_document", "generate_training_package", "generate_visual", "generate_batch", "translate_content"}:
        hints.append("If you don't see a download button above, the generation may have encountered an issue. Try asking me again or check the error details.")
    elif tool_names & {"search_brand_assets", "search_content_library", "search_brand_knowledge", "get_content_stats", "list_templates"}:
        hints.append("These are your search results. Ask me to generate content using any of these, or refine your search.")
    elif tool_names & {"update_brand_config", "approve_content"}:
        hints.append("Configuration updated. You can verify changes in the **Brand Repository** page.")

    if not hints and not gen_files:
        hints.append("Ask a follow-up question, request content generation, or try a quick action from the sidebar.")

    if hints:
        with st.expander("What to do next", expanded=bool(gen_files)):
            for h in hints:
                st.markdown(f"- {h}")


# ---------------------------------------------------------------------------
# Pending confirmation handler
#
# If the engine returned an action plan that needs user confirmation,
# it's stored in session_state. We render the confirm/cancel buttons here
# (outside _process_user_turn) so they survive page reruns.
# ---------------------------------------------------------------------------
_pending_plan = conversation.get_pending_confirmation()
if _pending_plan:
    with st.chat_message("assistant", avatar="\U0001f9e0"):
        st.markdown("### Action Plan — Waiting for your approval")
        plan = _pending_plan.get("plan", _pending_plan)

        action_label = plan.get("action", plan.get("tool_name", "Generate Content"))
        title = plan.get("title", "")
        details = plan.get("details", {})
        cost = plan.get("estimated_cost", "~$0.01-0.05")

        st.markdown(f"**Action:** {action_label}")
        if title:
            st.markdown(f"**Title:** {title}")
        if details:
            for k, v in details.items():
                if isinstance(v, list):
                    v = ", ".join(str(i) for i in v)
                st.markdown(f"- **{k.replace('_', ' ').title()}:** {v}")
        st.markdown(f"**Estimated Cost:** {cost}")

        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            _do_confirm = st.button("Confirm & Generate", type="primary", key="pending_confirm", use_container_width=True)
        with c2:
            _do_cancel = st.button("Cancel", key="pending_cancel", use_container_width=True)
        with c3:
            _do_modify = st.button("Modify", key="pending_modify", use_container_width=True)

        if _do_confirm:
            status_w = st.status("Generating your content...", expanded=True)
            status_w.write("Executing the approved action plan...")
            try:
                confirmed_response = engine.execute_confirmed_action(
                    _pending_plan,
                    knowledge_mode=conversation.get_knowledge_mode(),
                )
                status_w.update(label="Complete!", state="complete", expanded=False)
                conversation.clear_pending_confirmation()

                render_copilot_response(confirmed_response, message_index=99900)
                conversation.add_assistant_response(
                    text=confirmed_response.text,
                    tool_calls=confirmed_response.tool_calls_made,
                    generated_files=confirmed_response.generated_files,
                )
                conversation.add_display_message(
                    "assistant", confirmed_response.text,
                    files=confirmed_response.generated_files,
                    tool_calls=confirmed_response.tool_calls_made,
                )
                _render_next_steps(confirmed_response)
            except Exception as exc:
                status_w.update(label="Error", state="error", expanded=False)
                st.error(f"Generation failed: {exc}")

        elif _do_cancel:
            conversation.clear_pending_confirmation()
            st.info("Action cancelled. Ask me something else or refine your request.")
            conversation.add_display_message("assistant", "Action cancelled by user.")
            st.rerun()

        elif _do_modify:
            conversation.clear_pending_confirmation()
            st.info("Tell me what you'd like to change in the chat below.")
            conversation.add_display_message(
                "assistant", "Modification requested. Please describe what you'd like to change."
            )
            st.rerun()


# ---------------------------------------------------------------------------
# Quick-action handler
#
# When a sidebar quick-action button is pressed it sets
# st.session_state["quick_action"] and triggers st.rerun().
# On the re-run we pick up the value here and treat it as user input.
# ---------------------------------------------------------------------------
_pending_quick_action: str | None = st.session_state.pop("quick_action", None)


# ---------------------------------------------------------------------------
# Process a user turn (shared by quick actions and chat input)
# ---------------------------------------------------------------------------
def _process_user_turn(user_text: str, uploaded_file_paths: list[str] | None = None):
    """Handle a single user turn: display, send to engine, render response.

    This function:
    1. Shows the user message in the chat
    2. Sends the full conversation to the CopilotEngine
    3. Renders the assistant response using the response renderer
    4. Persists both messages in the conversation manager
    """
    if not user_text or not user_text.strip():
        return

    # Handle pin command
    stripped = user_text.strip()
    if stripped.lower().startswith("pin:"):
        pin_content = stripped[4:].strip()
        parts = pin_content.split(":", 1) if ":" in pin_content else [pin_content, pin_content]
        label = parts[0].strip() if len(parts) > 1 else "Note"
        text = parts[1].strip() if len(parts) > 1 else parts[0].strip()
        conversation.add_pinned_context(label, text)
        with st.chat_message("assistant", avatar="\U0001f9e0"):
            st.markdown(f"📌 Pinned: **{label}** — {text}")
        conversation.add_display_message("user", user_text)
        conversation.add_display_message("assistant", f"📌 Pinned: **{label}** — {text}")
        return

    file_refs = uploaded_file_paths or []

    # -- Display user message immediately ------------------------------------
    with st.chat_message("user"):
        st.markdown(user_text)

    # -- Add to conversation history (API + display) -------------------------
    conversation.add_user_message(user_text, file_refs=file_refs)
    conversation.add_display_message("user", user_text)

    # -- Call the copilot engine ---------------------------------------------
    # Human-readable labels for tool names
    _TOOL_LABELS = {
        "generate_presentation": "Generating presentation",
        "generate_document": "Generating document",
        "generate_training_package": "Building training package",
        "generate_visual": "Creating visual",
        "generate_batch": "Running batch generation",
        "translate_content": "Translating content",
        "search_brand_assets": "Searching brand assets",
        "get_brand_config": "Reading brand config",
        "update_brand_config": "Updating brand config",
        "search_content_library": "Searching content library",
        "get_content_stats": "Pulling content stats",
        "approve_content": "Approving content",
        "list_templates": "Loading templates",
        "search_brand_knowledge": "Searching brand knowledge",
        "web_search": "Searching the web",
        "confirm_action": "Preparing action plan",
    }

    with st.chat_message("assistant", avatar="\U0001f9e0"):
        response: CopilotResponse | None = None
        error_text: str | None = None

        status_widget = st.status("Working on your request...", expanded=True)

        def _progress_cb(phase: str, detail: str, extra):
            """Called by the engine to report progress."""
            if phase == "tool":
                label = _TOOL_LABELS.get(detail, detail.replace("_", " ").title())
                status_widget.update(label=f"{label}...")
                status_widget.write(f"Running: **{label}**")
            elif phase == "thinking":
                status_widget.update(label="Thinking...")
                status_widget.write("Analyzing results and planning next step...")

        try:
            status_widget.write("Sending your message to Claude...")
            api_messages = conversation.get_api_messages()
            knowledge_mode = conversation.get_knowledge_mode()
            pinned = conversation.get_pinned_context_dicts()
            response = engine.chat(
                api_messages,
                knowledge_mode=knowledge_mode,
                progress_callback=_progress_cb,
            )
            status_widget.update(label="Complete!", state="complete", expanded=False)
        except Exception as exc:
            error_text = str(exc)
            status_widget.update(label="Error", state="error", expanded=False)

        # -- Render the response or error ------------------------------------
        if error_text:
            render_error_message(error_text)
            # Store a user-visible error message
            conversation.add_assistant_response(
                text=f"An error occurred: {error_text}",
                tool_calls=None,
                generated_files=None,
            )
            conversation.add_display_message(
                "assistant",
                f"An error occurred: {error_text}",
            )
            return

        if response is None:
            render_error_message("No response received from the Copilot engine.")
            conversation.add_assistant_response(
                text="No response received.",
                tool_calls=None,
                generated_files=None,
            )
            conversation.add_display_message("assistant", "No response received.")
            return

        # -- Handle confirmation requests ----------------------------------
        msg_idx = conversation.get_message_count()
        if hasattr(response, "awaiting_confirmation") and response.awaiting_confirmation:
            # Store the pending action in session_state — the page-level
            # confirmation handler (above the chat input) will render the
            # buttons and handle the user's choice on the next rerun.
            conversation.set_pending_confirmation(response.action_plan)
            conversation.add_display_message("assistant", response.text)
            st.markdown(response.text)
            st.info("Review the action plan below and click **Confirm & Generate** to proceed.")
            st.session_state["copilot_uploaded_paths"] = []
            st.rerun()

        # Render via the full renderer (text + files + tool calls)
        render_copilot_response(response, message_index=msg_idx)

        # Check for errors surfaced inside the response itself
        resp_error = response.error if hasattr(response, "error") else None
        if resp_error:
            render_error_message(resp_error)

        # -- Persist assistant turn ------------------------------------------
        conversation.add_assistant_response(
            text=response.text,
            tool_calls=response.tool_calls_made,
            generated_files=response.generated_files,
        )
        conversation.add_display_message(
            "assistant",
            response.text,
            files=response.generated_files,
            tool_calls=response.tool_calls_made,
        )

        # -- Next steps guidance --------------------------------------------
        _render_next_steps(response)

    # Clear uploaded file refs after they have been consumed
    st.session_state["copilot_uploaded_paths"] = []


# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
user_input = st.chat_input("What would you like to create?")

# Determine which input to process: quick action takes precedence over
# the chat input on the same rerun cycle.
effective_input = _pending_quick_action or user_input

if effective_input:
    uploaded_paths = st.session_state.get("copilot_uploaded_paths", [])
    _process_user_turn(effective_input, uploaded_file_paths=uploaded_paths)
