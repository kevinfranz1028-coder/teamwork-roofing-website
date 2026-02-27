"""
Brand Intelligence Content Hub - Orchestrator Agent

Decomposes a user request into a :class:`TaskPlan` by calling an LLM
(Claude Sonnet by default, OpenAI optionally) to classify the request,
then builds a deterministic step ordering.

Usage:
    from app.agents.orchestrator import OrchestratorAgent

    orch = OrchestratorAgent()
    plan = orch.plan("Create a sales training presentation about FACTS")
    print(plan.to_summary())
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from app.agents.task_plan import AgentType, TaskPlan, TaskStatus, TaskStep

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-20250514"
DEFAULT_OPENAI_MODEL = "gpt-4.1"

PLANNING_SYSTEM_PROMPT = """\
You are a project planner for Brand Hub, a branded-content generation system.
Given a user request, determine:

1. content_type: "presentation" or "document"
2. doc_type: (only for documents) one of: job_aid, case_study, weekly_report,
   monthly_report, sop, training_guide, internal_memo, battle_card,
   capability_overview, proposal
3. title: A clear title for the output
4. needs_visuals: true or false — whether the output benefits from generated
   visual assets (infographics, charts, images). Presentations usually do;
   memos and SOPs usually do not.
5. description: A brief (1-2 sentence) description of what to generate

Return ONLY valid JSON with these 5 keys. No markdown, no commentary.
"""


class OrchestratorAgent:
    """Classifies a user request and builds a deterministic TaskPlan."""

    def __init__(self, model_provider: str | None = None) -> None:
        self._provider = (
            model_provider
            or os.environ.get("ORCHESTRATOR_MODEL", "claude")
        ).lower()
        self._claude_client = None
        self._openai_client = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plan(self, request: str) -> TaskPlan:
        """Classify *request* via LLM and return a fully-wired TaskPlan."""
        try:
            if self._provider == "openai":
                classification = self._plan_with_openai(request)
            else:
                classification = self._plan_with_claude(request)
        except Exception as exc:
            logger.warning("LLM planning failed: %s — using fallback", exc)
            classification = self._fallback_classification(request)

        content_type = classification.get("content_type", "presentation")
        doc_type = classification.get("doc_type", "")
        title = classification.get("title", "Untitled")
        needs_visuals = classification.get("needs_visuals", False)
        description = classification.get("description", request[:120])

        # Determine output format from content type
        output_format = "pptx" if content_type == "presentation" else "docx"

        task_plan = TaskPlan(
            request=request,
            content_type=content_type,
            output_format=output_format,
            doc_type=doc_type,
            title=title,
            metadata={"description": description, "needs_visuals": needs_visuals},
        )

        # --- Fixed step ordering ---
        task_plan.add_step(TaskStep(
            step_id="research",
            agent_type=AgentType.RESEARCH,
            description=f"Research brand context for: {title}",
        ))

        task_plan.add_step(TaskStep(
            step_id="write",
            agent_type=AgentType.WRITER,
            description=f"Write structured {content_type} content",
            depends_on=["research"],
        ))

        if needs_visuals:
            task_plan.add_step(TaskStep(
                step_id="visual",
                agent_type=AgentType.VISUAL,
                description="Generate visual assets",
                depends_on=["research"],
            ))

        designer_deps = ["write"]
        if needs_visuals:
            designer_deps.append("visual")

        task_plan.add_step(TaskStep(
            step_id="design",
            agent_type=AgentType.DESIGNER,
            description=f"Build final {output_format.upper()} file",
            depends_on=designer_deps,
        ))

        task_plan.add_step(TaskStep(
            step_id="compliance",
            agent_type=AgentType.COMPLIANCE,
            description="Validate against brand guidelines",
            depends_on=["design"],
        ))

        logger.info("Plan created: %s steps for '%s'", len(task_plan.steps), title)
        return task_plan

    def assemble(self, plan: TaskPlan) -> dict:
        """Collect results from a completed plan into a summary dict."""
        compliance_step = plan.get_step("compliance")
        compliance_result = compliance_step.result if compliance_step else None

        design_step = plan.get_step("design")
        output_file = ""
        if design_step and isinstance(design_step.result, dict):
            output_file = design_step.result.get("file_path", "")

        steps_summary = []
        for s in plan.steps:
            steps_summary.append({
                "step_id": s.step_id,
                "agent_type": s.agent_type.value,
                "status": s.status.value,
                "retry_count": s.retry_count,
                "cost_usd": s.cost_usd,
                "error": s.error,
            })

        return {
            "plan_id": plan.plan_id,
            "request": plan.request,
            "title": plan.title,
            "content_type": plan.content_type,
            "output_format": plan.output_format,
            "doc_type": plan.doc_type,
            "output_file": output_file,
            "compliance_result": compliance_result,
            "total_cost": plan.total_cost(),
            "elapsed": plan.elapsed(),
            "steps_summary": steps_summary,
        }

    # ------------------------------------------------------------------
    # Claude planning
    # ------------------------------------------------------------------

    def _get_claude_client(self):
        if self._claude_client is None:
            try:
                from anthropic import Anthropic

                api_key = os.environ.get("ANTHROPIC_API_KEY", "")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not set")
                self._claude_client = Anthropic(api_key=api_key)
            except Exception as exc:
                logger.error("Could not init Anthropic client: %s", exc)
                raise
        return self._claude_client

    def _plan_with_claude(self, request: str) -> dict:
        """Call Claude Sonnet to classify the request."""
        client = self._get_claude_client()
        model = os.environ.get("ORCHESTRATOR_CLAUDE_MODEL", DEFAULT_CLAUDE_MODEL)

        try:
            message = client.messages.create(
                model=model,
                max_tokens=500,
                system=PLANNING_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": request}],
            )
            raw = message.content[0].text.strip()
            return self._parse_json(raw)
        except Exception as exc:
            logger.warning("Claude planning failed: %s — using fallback", exc)
            return self._fallback_classification(request)

    # ------------------------------------------------------------------
    # OpenAI planning
    # ------------------------------------------------------------------

    def _get_openai_client(self):
        if self._openai_client is None:
            try:
                from openai import OpenAI

                api_key = os.environ.get("OPENAI_API_KEY", "")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not set")
                self._openai_client = OpenAI(api_key=api_key)
            except Exception as exc:
                logger.error("Could not init OpenAI client: %s", exc)
                raise
        return self._openai_client

    def _plan_with_openai(self, request: str) -> dict:
        """Call OpenAI to classify the request."""
        client = self._get_openai_client()
        model = os.environ.get("ORCHESTRATOR_OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=500,
                messages=[
                    {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
                    {"role": "user", "content": request},
                ],
            )
            raw = response.choices[0].message.content.strip()
            return self._parse_json(raw)
        except Exception as exc:
            logger.warning("OpenAI planning failed: %s — using fallback", exc)
            return self._fallback_classification(request)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """Extract JSON from an LLM response, stripping markdown fences."""
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        return json.loads(raw)

    @staticmethod
    def _fallback_classification(request: str) -> dict:
        """Keyword-based fallback when the LLM is unavailable."""
        req_lower = request.lower()

        # Detect content type
        pres_keywords = ["presentation", "deck", "slides", "pptx", "training deck"]
        is_presentation = any(kw in req_lower for kw in pres_keywords)
        content_type = "presentation" if is_presentation else "document"

        # Detect doc type
        doc_type = ""
        if not is_presentation:
            doc_type_map = {
                "job aid": "job_aid",
                "case study": "case_study",
                "weekly report": "weekly_report",
                "monthly report": "monthly_report",
                "sop": "sop",
                "standard operating": "sop",
                "training guide": "training_guide",
                "memo": "internal_memo",
                "battle card": "battle_card",
                "capability": "capability_overview",
                "proposal": "proposal",
            }
            for keyword, dtype in doc_type_map.items():
                if keyword in req_lower:
                    doc_type = dtype
                    break
            if not doc_type:
                doc_type = "job_aid"  # safe default

        # Simple title extraction
        title = request.strip().split("\n")[0][:80]

        return {
            "content_type": content_type,
            "doc_type": doc_type,
            "title": title,
            "needs_visuals": is_presentation,
            "description": request[:120],
        }
