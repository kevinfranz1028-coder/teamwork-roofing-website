"""
Copilot Audit Trail — persistent logging for every Copilot action.

Records tool calls, user confirmations, content generations, and errors
into the ``copilot_audit_log`` table so operators can review exactly what
the Copilot did during a session.

Usage::

    from app.copilot.audit_log import AuditLog

    audit = AuditLog()                       # auto-generates session_id
    audit.log_tool_call("search_assets", {"query": "logo"}, "Found 3 assets")
    audit.log_confirmation("generate_pptx", "confirmed")
    audit.log_generation("generate_pptx", "/output/deck.pptx", title="Q1 Deck")

    stats = audit.get_session_stats()
    print(stats)
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

# Graceful import — the CopilotAuditLog model may not exist yet if the
# migration hasn't been applied.  In that case every write method will
# silently return -1 and every read method will return an empty result.
try:
    from app.database.models import CopilotAuditLog, get_session
except ImportError:
    CopilotAuditLog = None  # type: ignore[assignment,misc]
    get_session = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Standalone cost helper
# ---------------------------------------------------------------------------

def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return an estimated dollar cost for a Claude API call.

    Pricing is a rough approximation and should be treated as a guide
    rather than a billing-accurate figure.

    Parameters
    ----------
    model:
        The model identifier (e.g. ``"claude-sonnet-4"``).
    input_tokens:
        Number of input (prompt) tokens consumed.
    output_tokens:
        Number of output (completion) tokens generated.

    Returns
    -------
    float
        Estimated cost in US dollars.
    """
    pricing: dict[str, tuple[float, float]] = {
        # (cost_per_1M_input, cost_per_1M_output)
        "claude-sonnet-4": (3.0, 15.0),
    }

    input_rate, output_rate = pricing.get(model, (3.0, 15.0))
    cost = (input_tokens / 1_000_000) * input_rate + (output_tokens / 1_000_000) * output_rate
    return round(cost, 6)


# ---------------------------------------------------------------------------
# AuditLog class
# ---------------------------------------------------------------------------

class AuditLog:
    """Manages audit trail persistence for a single Copilot session.

    Every public method is wrapped in a try/except so that audit failures
    never crash the main Copilot flow.
    """

    def __init__(self, session_id: str | None = None) -> None:
        self.session_id: str = session_id or uuid.uuid4().hex

    # ------------------------------------------------------------------
    # Core writer
    # ------------------------------------------------------------------

    def log_action(
        self,
        action_type: str,
        *,
        tool_name: str | None = None,
        tool_input: Any | None = None,
        tool_result_summary: str | None = None,
        knowledge_mode: str | None = None,
        sources: Any | None = None,
        confirmation_status: str | None = None,
        generated_file_path: str | None = None,
        api_tokens_used: int | None = None,
        api_cost_estimate: float | None = None,
        user_message: str | None = None,
    ) -> int:
        """Persist a single audit event to the database.

        Parameters
        ----------
        action_type:
            One of ``"tool_call"``, ``"confirmation"``, ``"generation"``,
            or ``"error"``.
        tool_name:
            Name of the tool invoked (if applicable).
        tool_input:
            Raw input sent to the tool.  Dicts and lists are
            automatically JSON-serialised.
        tool_result_summary:
            Short human-readable summary of the tool result.
        knowledge_mode:
            The knowledge mode in effect (``"grounded"`` / ``"enhanced"``
            / ``"research"``).
        sources:
            List of sources used.  Dicts and lists are automatically
            JSON-serialised.
        confirmation_status:
            ``"confirmed"``, ``"cancelled"``, or ``"modified"``.
        generated_file_path:
            Path to a file produced by this action.
        api_tokens_used:
            Number of API tokens consumed.
        api_cost_estimate:
            Estimated dollar cost of this action.
        user_message:
            The original user message that triggered this action.

        Returns
        -------
        int
            The database primary-key ``id`` of the new record, or ``-1``
            if the write failed.
        """
        if CopilotAuditLog is None or get_session is None:
            logger.warning("CopilotAuditLog model not available — skipping audit write.")
            return -1

        try:
            # Serialise complex types
            tool_input_json = (
                json.dumps(tool_input) if isinstance(tool_input, (dict, list)) else tool_input
            )
            sources_json = (
                json.dumps(sources) if isinstance(sources, (dict, list)) else sources
            )

            db = get_session()
            try:
                record = CopilotAuditLog(
                    session_id=self.session_id,
                    action_type=action_type,
                    tool_name=tool_name,
                    tool_input_json=tool_input_json,
                    tool_result_summary=tool_result_summary,
                    knowledge_mode=knowledge_mode,
                    sources_used_json=sources_json,
                    confirmation_status=confirmation_status,
                    generated_file_path=generated_file_path,
                    api_tokens_used=api_tokens_used,
                    api_cost_estimate=api_cost_estimate,
                    user_message=user_message,
                )
                db.add(record)
                db.commit()
                db.refresh(record)
                return record.id
            finally:
                db.close()

        except Exception:
            logger.exception("Failed to write audit log entry.")
            return -1

    # ------------------------------------------------------------------
    # Convenience wrappers
    # ------------------------------------------------------------------

    def log_tool_call(
        self,
        tool_name: str,
        tool_input: Any,
        result_summary: str,
        knowledge_mode: str | None = None,
    ) -> int:
        """Log a tool invocation.

        A shorthand for :pymeth:`log_action` with
        ``action_type="tool_call"``.
        """
        return self.log_action(
            "tool_call",
            tool_name=tool_name,
            tool_input=tool_input,
            tool_result_summary=result_summary,
            knowledge_mode=knowledge_mode,
        )

    def log_confirmation(
        self,
        tool_name: str,
        status: str,
        tool_input: Any | None = None,
    ) -> int:
        """Log a user confirmation decision.

        Parameters
        ----------
        tool_name:
            The tool whose execution was being confirmed.
        status:
            ``"confirmed"``, ``"cancelled"``, or ``"modified"``.
        tool_input:
            Optional snapshot of the input that was (or was not) approved.
        """
        return self.log_action(
            "confirmation",
            tool_name=tool_name,
            tool_input=tool_input,
            confirmation_status=status,
        )

    def log_generation(
        self,
        tool_name: str,
        file_path: str,
        title: str | None = None,
        api_tokens: int | None = None,
        cost: float | None = None,
    ) -> int:
        """Log a content-generation event.

        Parameters
        ----------
        tool_name:
            The generation tool used (e.g. ``"generate_pptx"``).
        file_path:
            Path to the generated output file.
        title:
            Human-readable title for the generated content.
        api_tokens:
            Total API tokens consumed during generation.
        cost:
            Estimated dollar cost of the generation.
        """
        return self.log_action(
            "generation",
            tool_name=tool_name,
            generated_file_path=file_path,
            tool_result_summary=title,
            api_tokens_used=api_tokens,
            api_cost_estimate=cost,
        )

    # ------------------------------------------------------------------
    # Readers
    # ------------------------------------------------------------------

    def get_session_log(self, limit: int = 50) -> list[dict]:
        """Return audit entries for the current session.

        Results are ordered by ``timestamp`` descending (newest first)
        and capped at *limit* rows.
        """
        if CopilotAuditLog is None or get_session is None:
            return []

        try:
            db = get_session()
            try:
                rows = (
                    db.query(CopilotAuditLog)
                    .filter(CopilotAuditLog.session_id == self.session_id)
                    .order_by(CopilotAuditLog.timestamp.desc())
                    .limit(limit)
                    .all()
                )
                return [self._row_to_dict(r) for r in rows]
            finally:
                db.close()
        except Exception:
            logger.exception("Failed to read session audit log.")
            return []

    def get_recent_log(self, limit: int = 100) -> list[dict]:
        """Return the most recent audit entries across **all** sessions.

        Results are ordered by ``timestamp`` descending and capped at
        *limit* rows.
        """
        if CopilotAuditLog is None or get_session is None:
            return []

        try:
            db = get_session()
            try:
                rows = (
                    db.query(CopilotAuditLog)
                    .order_by(CopilotAuditLog.timestamp.desc())
                    .limit(limit)
                    .all()
                )
                return [self._row_to_dict(r) for r in rows]
            finally:
                db.close()
        except Exception:
            logger.exception("Failed to read recent audit log.")
            return []

    def export_log(self, session_id: str | None = None) -> str:
        """Export audit entries as a JSON string.

        Parameters
        ----------
        session_id:
            Session to export.  Defaults to the current session.

        Returns
        -------
        str
            A JSON document containing metadata and an ``entries`` array.
        """
        target_session = session_id or self.session_id

        if CopilotAuditLog is None or get_session is None:
            return json.dumps({"error": "CopilotAuditLog model not available"})

        try:
            db = get_session()
            try:
                rows = (
                    db.query(CopilotAuditLog)
                    .filter(CopilotAuditLog.session_id == target_session)
                    .order_by(CopilotAuditLog.timestamp.asc())
                    .all()
                )
                entries = [self._row_to_dict(r) for r in rows]
            finally:
                db.close()

            payload = {
                "session_id": target_session,
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "entry_count": len(entries),
                "entries": entries,
            }
            return json.dumps(payload, indent=2, default=str)
        except Exception:
            logger.exception("Failed to export audit log.")
            return json.dumps({"error": "Export failed"})

    def get_session_stats(self) -> dict:
        """Compute aggregate statistics for the current session.

        Returns
        -------
        dict
            Keys: ``session_id``, ``total_actions``, ``tool_calls``,
            ``generations``, ``confirmations``, ``total_tokens``,
            ``total_cost``.
        """
        if CopilotAuditLog is None or get_session is None:
            return self._empty_stats()

        try:
            db = get_session()
            try:
                rows = (
                    db.query(CopilotAuditLog)
                    .filter(CopilotAuditLog.session_id == self.session_id)
                    .all()
                )
            finally:
                db.close()

            total_tokens = 0
            total_cost = 0.0
            tool_calls = 0
            generations = 0
            confirmations = 0

            for row in rows:
                if row.action_type == "tool_call":
                    tool_calls += 1
                elif row.action_type == "generation":
                    generations += 1
                elif row.action_type == "confirmation":
                    confirmations += 1

                if row.api_tokens_used:
                    total_tokens += row.api_tokens_used
                if row.api_cost_estimate:
                    total_cost += row.api_cost_estimate

            return {
                "session_id": self.session_id,
                "total_actions": len(rows),
                "tool_calls": tool_calls,
                "generations": generations,
                "confirmations": confirmations,
                "total_tokens": total_tokens,
                "total_cost": round(total_cost, 6),
            }

        except Exception:
            logger.exception("Failed to compute session stats.")
            return self._empty_stats()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _empty_stats(self) -> dict:
        """Return a zeroed-out stats dictionary."""
        return {
            "session_id": self.session_id,
            "total_actions": 0,
            "tool_calls": 0,
            "generations": 0,
            "confirmations": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
        }

    @staticmethod
    def _row_to_dict(row: Any) -> dict:
        """Convert a CopilotAuditLog ORM instance to a plain dict."""
        return {
            "id": row.id,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "session_id": row.session_id,
            "user_message": row.user_message,
            "action_type": row.action_type,
            "tool_name": row.tool_name,
            "tool_input": row.tool_input_json,
            "tool_result_summary": row.tool_result_summary,
            "knowledge_mode": row.knowledge_mode,
            "sources_used": row.sources_used_json,
            "confirmation_status": row.confirmation_status,
            "generated_file_path": row.generated_file_path,
            "api_tokens_used": row.api_tokens_used,
            "api_cost_estimate": row.api_cost_estimate,
        }
