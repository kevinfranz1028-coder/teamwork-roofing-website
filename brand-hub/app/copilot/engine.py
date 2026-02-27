"""
Copilot Engine — the brain of the Brand Hub Copilot.

Uses Claude's tool_use capability to decide when to take actions
(generate content, query data, update settings) vs. when to just
respond conversationally.

The engine manages a multi-round tool loop within a single chat turn:
  1. Takes user message + conversation history
  2. Builds a system prompt with current app state
  3. Sends to Claude with tool definitions
  4. If Claude wants to use tools: execute them, return results, loop
  5. When Claude gives a final text response: return it
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None
    ANTHROPIC_AVAILABLE = False

from app.copilot.tools import COPILOT_TOOLS
from app.copilot.tool_handlers import execute_tool
from app.copilot.context_builder import build_copilot_system_prompt

try:
    from app.copilot.audit_log import AuditLog, estimate_cost
    from app.copilot.verification import verify_content, SourceAttribution, get_grounding_instruction, KnowledgeMode
except ImportError:
    AuditLog = None
    estimate_cost = None
    verify_content = None
    SourceAttribution = None
    get_grounding_instruction = None
    KnowledgeMode = None

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response data class
# ---------------------------------------------------------------------------

@dataclass
class CopilotResponse:
    """Result from a copilot chat turn."""
    text: str = ""
    generated_files: list = field(default_factory=list)
    tool_calls_made: list = field(default_factory=list)
    error: str | None = None
    duration_seconds: float = 0.0
    awaiting_confirmation: bool = False
    action_plan: dict | None = None
    confidence: dict | None = None  # ConfidenceScore as dict
    sources: list = field(default_factory=list)
    knowledge_mode: str = "grounded"


# ---------------------------------------------------------------------------
# Engine constants
# ---------------------------------------------------------------------------

COPILOT_MODEL = "claude-sonnet-4-20250514"
MAX_TOOL_ROUNDS = 10  # safety limit to prevent infinite tool loops

CONFIRM_REQUIRED_TOOLS = {
    "generate_presentation",
    "generate_document",
    "generate_training_package",
    "generate_visual",
    "generate_batch",
    "generate_with_agents",
    "generate_image",
    "update_brand_config",
    "approve_content",
    "translate_content",
}

READ_ONLY_TOOLS = {
    "search_brand_assets",
    "get_brand_config",
    "search_content_library",
    "get_content_stats",
    "list_templates",
    "search_brand_knowledge",
    "check_brand_compliance",
}


# ---------------------------------------------------------------------------
# Main engine class
# ---------------------------------------------------------------------------

class CopilotEngine:
    """Main Copilot engine using Claude tool_use for app control.

    The engine manages the conversation loop:
    1. Takes user message + conversation history
    2. Builds a system prompt with current app state
    3. Sends to Claude with tool definitions
    4. If Claude wants to use tools: execute them, return results, loop
    5. When Claude gives a final text response: return it
    """

    def __init__(self):
        """Initialize the engine.

        Loads API key from environment.
        Does NOT take brand_engine/db_session/etc as args — the tool_handlers
        module manages its own connections to app modules.
        """
        self.client = None
        self.model = COPILOT_MODEL
        api_key = os.getenv("ANTHROPIC_API_KEY", "")

        if api_key and ANTHROPIC_AVAILABLE:
            try:
                self.client = Anthropic(api_key=api_key)
            except Exception as exc:
                logger.warning("Could not init Anthropic client: %s", exc)

        self.available = self.client is not None

        self.audit_log = None
        if AuditLog is not None:
            try:
                self.audit_log = AuditLog()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: list[dict],
        uploaded_files: list | None = None,
        knowledge_mode: str = "grounded",
        progress_callback: "callable | None" = None,
    ) -> CopilotResponse:
        """Process a chat turn.

        Parameters
        ----------
        messages : list[dict]
            Full conversation history in Anthropic API format:
            [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
        uploaded_files : list | None
            Optional list of file info dicts for files uploaded with this message.

        Returns
        -------
        CopilotResponse
            The response including text, generated files, and tool call log.
        """
        if not self.available:
            return CopilotResponse(
                text=(
                    "I'm sorry, I can't process your request right now. "
                    "The Anthropic API key is not configured. Please set it "
                    "in Settings > API Keys."
                ),
                error="ANTHROPIC_API_KEY not configured",
            )

        start_time = time.time()

        # Build system prompt with current app state
        system_prompt = build_copilot_system_prompt()

        # Inject knowledge mode grounding rules
        if get_grounding_instruction is not None:
            grounding = get_grounding_instruction(knowledge_mode)
            system_prompt += f"\n\n## KNOWLEDGE MODE: {knowledge_mode.upper()}\n{grounding}"

        # Track tool calls for the response
        all_tool_calls: list[dict] = []
        all_generated_files: list[dict] = []

        # Make initial API call
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                tools=COPILOT_TOOLS,
                messages=messages,
            )
        except Exception as exc:
            logger.error("Claude API error: %s", exc)
            return CopilotResponse(
                text=f"I encountered an error communicating with Claude: {exc}",
                error=str(exc),
                duration_seconds=time.time() - start_time,
            )

        # ---------------------------------------------------------------
        # Tool use loop
        # ---------------------------------------------------------------
        rounds = 0
        while response.stop_reason == "tool_use" and rounds < MAX_TOOL_ROUNDS:
            rounds += 1

            # Extract tool use blocks from response
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

            # Execute each tool and collect results
            tool_results = []
            for tool_block in tool_use_blocks:
                tool_name = tool_block.name
                tool_input = tool_block.input
                logger.info("Executing tool: %s", tool_name)

                # Report progress
                if progress_callback:
                    progress_callback("tool", tool_name, tool_input)

                # Check if this tool requires confirmation
                if tool_name in CONFIRM_REQUIRED_TOOLS:
                    action_plan = self._build_action_plan(tool_name, tool_input)

                    # Log the pending confirmation
                    if self.audit_log:
                        self.audit_log.log_confirmation(tool_name, "pending", tool_input)

                    # Store the pending tool info for later execution
                    return CopilotResponse(
                        text=self._format_action_plan_text(action_plan),
                        awaiting_confirmation=True,
                        action_plan={
                            "tool_name": tool_name,
                            "tool_input": tool_input,
                            "tool_block_id": tool_block.id,
                            "plan": action_plan,
                            "messages": messages,
                            "assistant_content": self._serialize_response_content(response.content),
                        },
                        knowledge_mode=knowledge_mode,
                        tool_calls_made=all_tool_calls,
                        duration_seconds=time.time() - start_time,
                    )

                try:
                    result_str = execute_tool(tool_name, tool_input)

                    # Track the tool call
                    tool_call_record = {
                        "name": tool_name,
                        "input": tool_input,
                        "result_preview": (
                            result_str[:200] + "..."
                            if len(result_str) > 200
                            else result_str
                        ),
                    }

                    # Check if the result contains generated files
                    tool_call_record = self._extract_generated_files(
                        result_str, tool_call_record, all_generated_files,
                    )
                    all_tool_calls.append(tool_call_record)

                    # Audit log the tool call
                    if self.audit_log:
                        self.audit_log.log_tool_call(
                            tool_name, tool_input, result_str[:200], knowledge_mode
                        )

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": result_str,
                    })

                except Exception as exc:
                    logger.error("Tool execution error for %s: %s", tool_name, exc)
                    error_result = json.dumps({"error": str(exc)})
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": error_result,
                        "is_error": True,
                    })
                    all_tool_calls.append({
                        "name": tool_name,
                        "input": tool_input,
                        "summary": f"Error: {exc}",
                    })

            # Build the messages for the next round:
            # Append assistant message (with tool_use blocks) + user
            # message (with tool_results).
            assistant_content = self._serialize_response_content(response.content)

            messages = messages + [
                {"role": "assistant", "content": assistant_content},
                {"role": "user", "content": tool_results},
            ]

            # Next API call
            if progress_callback:
                progress_callback("thinking", f"round {rounds + 1}", None)
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system_prompt,
                    tools=COPILOT_TOOLS,
                    messages=messages,
                )
            except Exception as exc:
                logger.error("Claude API error in tool loop: %s", exc)
                return CopilotResponse(
                    text=f"I encountered an error during processing: {exc}",
                    tool_calls_made=all_tool_calls,
                    generated_files=all_generated_files,
                    error=str(exc),
                    duration_seconds=time.time() - start_time,
                )

        # ---------------------------------------------------------------
        # Extract final text from response
        # ---------------------------------------------------------------
        final_text = ""
        for block in response.content:
            if block.type == "text":
                final_text += block.text

        return CopilotResponse(
            text=final_text,
            generated_files=all_generated_files,
            tool_calls_made=all_tool_calls,
            knowledge_mode=knowledge_mode,
            duration_seconds=time.time() - start_time,
        )

    # ------------------------------------------------------------------
    # Confirmation workflow
    # ------------------------------------------------------------------

    def execute_confirmed_action(self, action_plan: dict, knowledge_mode: str = "grounded") -> CopilotResponse:
        """Execute a previously confirmed action plan.

        Called after the user confirms an action in the UI.
        """
        start_time = time.time()

        tool_name = action_plan.get("tool_name", "")
        tool_input = action_plan.get("tool_input", {})
        tool_block_id = action_plan.get("tool_block_id", "")
        messages = action_plan.get("messages", [])
        assistant_content = action_plan.get("assistant_content", [])

        all_tool_calls = []
        all_generated_files = []

        # Log confirmation
        if self.audit_log:
            self.audit_log.log_confirmation(tool_name, "confirmed", tool_input)

        try:
            result_str = execute_tool(tool_name, tool_input)

            tool_call_record = {
                "name": tool_name,
                "input": tool_input,
                "result_preview": result_str[:200] + "..." if len(result_str) > 200 else result_str,
            }
            tool_call_record = self._extract_generated_files(
                result_str, tool_call_record, all_generated_files,
            )
            all_tool_calls.append(tool_call_record)

            # Audit log
            if self.audit_log:
                self.audit_log.log_tool_call(tool_name, tool_input, result_str[:200], knowledge_mode)
                if all_generated_files:
                    for gf in all_generated_files:
                        self.audit_log.log_generation(
                            tool_name, gf.get("path", ""), gf.get("title", "")
                        )

            tool_results = [{
                "type": "tool_result",
                "tool_use_id": tool_block_id,
                "content": result_str,
            }]

        except Exception as exc:
            logger.error("Confirmed tool execution failed for %s: %s", tool_name, exc)
            return CopilotResponse(
                text=f"The action failed: {exc}",
                error=str(exc),
                tool_calls_made=[{"name": tool_name, "summary": f"Error: {exc}"}],
                duration_seconds=time.time() - start_time,
            )

        # Continue the conversation with tool results
        system_prompt = build_copilot_system_prompt()
        if get_grounding_instruction is not None:
            grounding = get_grounding_instruction(knowledge_mode)
            system_prompt += f"\n\n## KNOWLEDGE MODE: {knowledge_mode.upper()}\n{grounding}"

        continued_messages = messages + [
            {"role": "assistant", "content": assistant_content},
            {"role": "user", "content": tool_results},
        ]

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                tools=COPILOT_TOOLS,
                messages=continued_messages,
            )
        except Exception as exc:
            logger.error("Claude API error after confirmed action: %s", exc)
            return CopilotResponse(
                text=f"Action completed but I encountered an error generating the summary: {exc}",
                tool_calls_made=all_tool_calls,
                generated_files=all_generated_files,
                error=str(exc),
                duration_seconds=time.time() - start_time,
            )

        # Handle any further tool rounds (read-only tools only)
        rounds = 0
        while response.stop_reason == "tool_use" and rounds < MAX_TOOL_ROUNDS:
            rounds += 1
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            further_results = []

            for tb in tool_use_blocks:
                try:
                    res = execute_tool(tb.name, tb.input)
                    tc_rec = {"name": tb.name, "input": tb.input, "result_preview": res[:200]}
                    tc_rec = self._extract_generated_files(res, tc_rec, all_generated_files)
                    all_tool_calls.append(tc_rec)
                    further_results.append({"type": "tool_result", "tool_use_id": tb.id, "content": res})
                except Exception as exc:
                    further_results.append({"type": "tool_result", "tool_use_id": tb.id, "content": json.dumps({"error": str(exc)}), "is_error": True})

            ac = self._serialize_response_content(response.content)
            continued_messages = continued_messages + [
                {"role": "assistant", "content": ac},
                {"role": "user", "content": further_results},
            ]

            try:
                response = self.client.messages.create(
                    model=self.model, max_tokens=4096, system=system_prompt,
                    tools=COPILOT_TOOLS, messages=continued_messages,
                )
            except Exception as exc:
                return CopilotResponse(
                    text=f"Error during follow-up: {exc}", error=str(exc),
                    tool_calls_made=all_tool_calls, generated_files=all_generated_files,
                    duration_seconds=time.time() - start_time,
                )

        final_text = ""
        for block in response.content:
            if block.type == "text":
                final_text += block.text

        return CopilotResponse(
            text=final_text,
            generated_files=all_generated_files,
            tool_calls_made=all_tool_calls,
            knowledge_mode=knowledge_mode,
            duration_seconds=time.time() - start_time,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_response_content(content_blocks) -> list[dict]:
        """Convert Anthropic response content blocks to plain dicts.

        This is necessary so we can append them back into the messages
        list for subsequent API calls during the tool loop.
        """
        serialized = []
        for block in content_blocks:
            if block.type == "text":
                serialized.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                serialized.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
        return serialized

    @staticmethod
    def _extract_generated_files(
        result_str: str,
        tool_call_record: dict,
        all_generated_files: list[dict],
    ) -> dict:
        """Parse a tool result string for generated file info.

        If the result JSON contains ``file_path`` or ``files`` keys the
        relevant entries are appended to *all_generated_files* and a
        human-readable summary is added to *tool_call_record*.

        Returns the (possibly updated) *tool_call_record*.
        """
        try:
            result_data = json.loads(result_str)
            if not isinstance(result_data, dict):
                tool_call_record["summary"] = result_str[:100]
                return tool_call_record

            if result_data.get("file_path"):
                file_info = {
                    "title": result_data.get("title", "Generated File"),
                    "path": result_data["file_path"],
                    "format": result_data.get("format", "unknown"),
                    "size": result_data.get("file_size", ""),
                }
                all_generated_files.append(file_info)
                tool_call_record["summary"] = f"Generated: {file_info['title']}"
            elif result_data.get("files"):
                for f in result_data["files"]:
                    all_generated_files.append(f)
                tool_call_record["summary"] = (
                    f"Generated {len(result_data['files'])} files"
                )
            else:
                tool_call_record["summary"] = result_str[:100]

        except (json.JSONDecodeError, TypeError):
            tool_call_record["summary"] = result_str[:100]

        return tool_call_record

    @staticmethod
    def _build_action_plan(tool_name: str, tool_input: dict) -> dict:
        """Build a human-readable action plan from a tool call."""
        TOOL_LABELS = {
            "generate_presentation": "Create Presentation",
            "generate_document": "Create Document",
            "generate_training_package": "Create Training Package",
            "generate_visual": "Create Visual",
            "generate_image": "Generate Image",
            "generate_batch": "Batch Generation",
            "generate_with_agents": "Agent Pipeline Generation",
            "update_brand_config": "Update Brand Config",
            "approve_content": "Approve Content",
            "translate_content": "Translate Content",
        }

        # Estimate cost based on tool type
        COST_ESTIMATES = {
            "generate_presentation": "$0.08 - $0.15",
            "generate_document": "$0.05 - $0.10",
            "generate_training_package": "$0.20 - $0.40",
            "generate_visual": "$0.03 - $0.06",
            "generate_image": "$0.04 - $0.12",
            "generate_batch": "$0.10 - $0.50",
            "generate_with_agents": "$0.10 - $0.30",
            "update_brand_config": "Free",
            "approve_content": "Free",
            "translate_content": "$0.02 - $0.08",
        }

        return {
            "action": TOOL_LABELS.get(tool_name, tool_name),
            "tool_name": tool_name,
            "title": tool_input.get("title", tool_input.get("batch_name", "")),
            "details": {k: v for k, v in tool_input.items() if k != "content_source" and v},
            "estimated_cost": COST_ESTIMATES.get(tool_name, "Unknown"),
        }

    @staticmethod
    def _format_action_plan_text(plan: dict) -> str:
        """Format an action plan as readable markdown text."""
        lines = [
            f"**I'd like to: {plan['action']}**",
            "",
        ]
        if plan.get("title"):
            lines.append(f"**Title:** {plan['title']}")

        details = plan.get("details", {})
        if details:
            lines.append("")
            lines.append("**Parameters:**")
            for k, v in details.items():
                if isinstance(v, list):
                    v = ", ".join(str(i) for i in v)
                lines.append(f"- {k.replace('_', ' ').title()}: {v}")

        lines.append("")
        lines.append(f"**Estimated API Cost:** {plan.get('estimated_cost', 'Unknown')}")
        lines.append("")
        lines.append("*Please confirm, cancel, or modify this action.*")

        return "\n".join(lines)
