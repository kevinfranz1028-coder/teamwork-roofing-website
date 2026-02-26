"""
Brand Intelligence Content Hub - Copilot Conversation Manager

Manages conversation history with Streamlit session_state persistence.
Handles message formatting for the Anthropic API, context trimming,
and display message tracking.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Try to import streamlit — fallback to dict-based storage if unavailable
try:
    import streamlit as st
    _HAS_STREAMLIT = True
except ImportError:
    _HAS_STREAMLIT = False


def _get_state() -> dict:
    """Get the persistent state dict (session_state or fallback)."""
    if _HAS_STREAMLIT:
        return st.session_state
    # Fallback for non-Streamlit contexts
    if not hasattr(_get_state, "_fallback"):
        _get_state._fallback = {}
    return _get_state._fallback


@dataclass
class DisplayMessage:
    """A message for display in the chat UI."""
    role: str  # "user" or "assistant"
    content: str  # Text content for display
    files: list = field(default_factory=list)  # Generated file info dicts
    tool_calls: list = field(default_factory=list)  # Tool call records
    timestamp: str = ""  # ISO format timestamp


@dataclass
class PinnedContext:
    """A session-level instruction that persists across messages."""
    label: str
    text: str
    pinned_at: str = ""

    def __post_init__(self):
        if not self.pinned_at:
            from datetime import datetime
            self.pinned_at = datetime.now().isoformat()


class ConversationManager:
    """Manages copilot conversation history with session_state persistence.

    Maintains two parallel structures:
    1. api_messages — Messages in Anthropic API format for the messages parameter
    2. display_messages — Messages formatted for Streamlit chat UI display

    The API messages include tool_use and tool_result blocks that should
    not be shown directly to the user. The display messages contain
    cleaned-up text plus metadata about tool calls and generated files.
    """

    STATE_KEY_API = "copilot_api_messages"
    STATE_KEY_DISPLAY = "copilot_display_messages"
    STATE_KEY_FILES = "copilot_generated_files"
    STATE_KEY_PINNED = "copilot_pinned_context"
    STATE_KEY_KNOWLEDGE_MODE = "copilot_knowledge_mode"
    STATE_KEY_PENDING_CONFIRMATION = "copilot_pending_confirmation"

    def __init__(self, max_messages: int = 50):
        """Initialize the conversation manager.

        Parameters
        ----------
        max_messages : int
            Maximum number of message pairs to retain.
        """
        self.max_messages = max_messages
        state = _get_state()
        if self.STATE_KEY_API not in state:
            state[self.STATE_KEY_API] = []
        if self.STATE_KEY_DISPLAY not in state:
            state[self.STATE_KEY_DISPLAY] = []
        if self.STATE_KEY_FILES not in state:
            state[self.STATE_KEY_FILES] = []
        if self.STATE_KEY_PINNED not in state:
            state[self.STATE_KEY_PINNED] = []
        if self.STATE_KEY_KNOWLEDGE_MODE not in state:
            state[self.STATE_KEY_KNOWLEDGE_MODE] = "grounded"
        if self.STATE_KEY_PENDING_CONFIRMATION not in state:
            state[self.STATE_KEY_PENDING_CONFIRMATION] = None

    # --- API Messages ---

    def add_user_message(self, text: str, file_refs: list[str] | None = None):
        """Add a user message to the API conversation history.

        If file references are provided, append them as context to the message.
        """
        content = text
        if file_refs:
            content += "\n\n[Attached files: " + ", ".join(file_refs) + "]"

        state = _get_state()
        state[self.STATE_KEY_API].append({
            "role": "user",
            "content": content,
        })
        self._trim()

    def add_assistant_response(self, text: str, tool_calls: list | None = None,
                                generated_files: list | None = None):
        """Add an assistant response to the API conversation history.

        This adds just the text portion. Tool use rounds are handled
        internally by the engine and don't need to be persisted for
        future turns (they're already in the engine's message chain).
        """
        state = _get_state()
        state[self.STATE_KEY_API].append({
            "role": "assistant",
            "content": text,
        })

        # Track generated files
        if generated_files:
            state[self.STATE_KEY_FILES].extend(generated_files)

        self._trim()

    def get_api_messages(self) -> list[dict]:
        """Get the full message history in Anthropic API format."""
        state = _get_state()
        return list(state[self.STATE_KEY_API])

    # --- Display Messages ---

    def add_display_message(self, role: str, content: str,
                            files: list | None = None,
                            tool_calls: list | None = None):
        """Add a message to the display history."""
        from datetime import datetime
        state = _get_state()
        msg = DisplayMessage(
            role=role,
            content=content,
            files=files or [],
            tool_calls=tool_calls or [],
            timestamp=datetime.now().isoformat(),
        )
        state[self.STATE_KEY_DISPLAY].append(msg)

    def get_display_messages(self) -> list[DisplayMessage]:
        """Get all display messages."""
        state = _get_state()
        return list(state[self.STATE_KEY_DISPLAY])

    def get_generated_files(self) -> list[dict]:
        """Get all generated files from this conversation."""
        state = _get_state()
        return list(state[self.STATE_KEY_FILES])

    # --- Pinned Context ---

    def add_pinned_context(self, label: str, text: str):
        """Pin a session-level instruction."""
        state = _get_state()
        pin = PinnedContext(label=label, text=text)
        state[self.STATE_KEY_PINNED].append(pin)

    def remove_pinned_context(self, index: int):
        """Remove a pinned context by index."""
        state = _get_state()
        pins = state[self.STATE_KEY_PINNED]
        if 0 <= index < len(pins):
            pins.pop(index)

    def get_pinned_context(self) -> list:
        """Get all pinned context items."""
        state = _get_state()
        return list(state[self.STATE_KEY_PINNED])

    def get_pinned_context_dicts(self) -> list[dict]:
        """Get pinned context as list of dicts (for system prompt)."""
        state = _get_state()
        result = []
        for pin in state[self.STATE_KEY_PINNED]:
            if hasattr(pin, "label"):
                result.append({"label": pin.label, "text": pin.text})
            elif isinstance(pin, dict):
                result.append(pin)
        return result

    # --- Knowledge Mode ---

    def get_knowledge_mode(self) -> str:
        """Get the current knowledge mode."""
        state = _get_state()
        return state.get(self.STATE_KEY_KNOWLEDGE_MODE, "grounded")

    def set_knowledge_mode(self, mode: str):
        """Set the knowledge mode (grounded / enhanced / research)."""
        valid_modes = {"grounded", "enhanced", "research"}
        if mode.lower() in valid_modes:
            state = _get_state()
            state[self.STATE_KEY_KNOWLEDGE_MODE] = mode.lower()

    # --- Confirmation ---

    def set_pending_confirmation(self, action_plan: dict | None):
        """Store a pending confirmation action plan."""
        state = _get_state()
        state[self.STATE_KEY_PENDING_CONFIRMATION] = action_plan

    def get_pending_confirmation(self) -> dict | None:
        """Get the pending confirmation action plan, if any."""
        state = _get_state()
        return state.get(self.STATE_KEY_PENDING_CONFIRMATION)

    def clear_pending_confirmation(self):
        """Clear the pending confirmation."""
        state = _get_state()
        state[self.STATE_KEY_PENDING_CONFIRMATION] = None

    # --- History Management ---

    def clear(self):
        """Clear all conversation history."""
        state = _get_state()
        state[self.STATE_KEY_API] = []
        state[self.STATE_KEY_DISPLAY] = []
        state[self.STATE_KEY_FILES] = []
        state[self.STATE_KEY_PINNED] = []
        state[self.STATE_KEY_KNOWLEDGE_MODE] = "grounded"
        state[self.STATE_KEY_PENDING_CONFIRMATION] = None

    def _trim(self):
        """Trim API message history to stay within limits."""
        state = _get_state()
        msgs = state[self.STATE_KEY_API]
        if len(msgs) > self.max_messages * 2:
            # Keep the most recent messages
            state[self.STATE_KEY_API] = msgs[-(self.max_messages * 2):]

    def get_message_count(self) -> int:
        """Return the number of API messages."""
        state = _get_state()
        return len(state[self.STATE_KEY_API])

    def get_last_user_message(self) -> str | None:
        """Return the last user message text, or None."""
        state = _get_state()
        for msg in reversed(state[self.STATE_KEY_API]):
            if msg["role"] == "user" and isinstance(msg["content"], str):
                return msg["content"]
        return None

    def export_history(self) -> str:
        """Export conversation history as JSON string."""
        state = _get_state()
        export = {
            "api_messages": state[self.STATE_KEY_API],
            "generated_files": state[self.STATE_KEY_FILES],
        }
        return json.dumps(export, indent=2, default=str)
