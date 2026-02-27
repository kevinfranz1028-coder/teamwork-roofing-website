"""
Brand Intelligence Content Hub - Agent Router

Executes a :class:`TaskPlan` step-by-step, dispatching each step to its
responsible agent, managing shared state, and running the compliance
retry loop when validation fails.

Usage:
    from app.agents.orchestrator import OrchestratorAgent
    from app.agents.agent_router import AgentRouter

    orch = OrchestratorAgent()
    plan = orch.plan("Create a sales training presentation about FACTS")

    router = AgentRouter()
    completed = router.execute(plan)
    print(orch.assemble(completed))
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Callable, Optional

from app.agents.task_plan import (
    AgentType,
    ContentBrief,
    TaskPlan,
    TaskStatus,
    TaskStep,
)
from app.config import BRAND_ASSETS_DIR

logger = logging.getLogger(__name__)


class AgentRouter:
    """Executes a TaskPlan by dispatching steps to the appropriate agents."""

    def __init__(
        self,
        brand_config: dict | None = None,
        progress_callback: Callable | None = None,
        max_retries: int | None = None,
    ) -> None:
        self._brand_config = brand_config or self._load_brand_config()
        self._progress_callback = progress_callback
        self._max_retries = max_retries or int(
            os.environ.get("AGENT_MAX_RETRIES", "2")
        )

        # Shared state across steps
        self._content_brief: ContentBrief | None = None
        self._written_content: dict | None = None
        self._visual_assets: list[dict] | None = None
        self._output_file: str | None = None
        self._compliance_result: dict | None = None

    # ------------------------------------------------------------------
    # Main execution loop
    # ------------------------------------------------------------------

    def execute(self, plan: TaskPlan) -> TaskPlan:
        """Run all steps in *plan*, respecting dependencies and retries.

        Returns the mutated plan with all steps in terminal states.
        """
        logger.info(
            "Executing plan %s (%d steps)", plan.plan_id[:8], len(plan.steps)
        )

        self._run_plan_loop(plan)

        # Check compliance and retry if needed
        compliance_step = plan.get_step("compliance")
        retries_done = 0

        while (
            compliance_step
            and compliance_step.status == TaskStatus.COMPLETED
            and not self._compliance_passed()
            and retries_done < self._max_retries
        ):
            retries_done += 1
            logger.info(
                "Compliance failed — retry %d/%d", retries_done, self._max_retries
            )
            self._report_progress(
                compliance_step,
                "retrying",
                f"Compliance failed, retry {retries_done}/{self._max_retries}",
            )

            # Reset writer, designer, and compliance for re-run
            for step_id in ("write", "design", "compliance"):
                step = plan.get_step(step_id)
                if step:
                    step.status = TaskStatus.PENDING
                    step.result = None
                    step.error = ""
                    step.started_at = None
                    step.completed_at = None
                    step.retry_count += 1

            self._run_plan_loop(plan)
            compliance_step = plan.get_step("compliance")

        # Log to database
        self._log_agent_run(plan)

        logger.info(
            "Plan %s complete — %s",
            plan.plan_id[:8],
            "PASSED" if self._compliance_passed() else "FAILED/PARTIAL",
        )
        return plan

    def _run_plan_loop(self, plan: TaskPlan) -> None:
        """Execute runnable steps until none remain."""
        while True:
            step = plan.get_next_runnable()
            if step is None:
                break

            step.status = TaskStatus.RUNNING
            step.started_at = time.time()
            self._report_progress(step, "running", step.description)

            try:
                result = self._run_step(step, plan)
                step.status = TaskStatus.COMPLETED
                step.result = result
                step.completed_at = time.time()
                self._report_progress(step, "completed")
            except Exception as exc:
                step.status = TaskStatus.FAILED
                step.error = str(exc)
                step.completed_at = time.time()
                logger.error(
                    "Step %s failed: %s", step.step_id, exc, exc_info=True
                )
                self._report_progress(step, "failed", str(exc))

    # ------------------------------------------------------------------
    # Step dispatch
    # ------------------------------------------------------------------

    def _run_step(self, step: TaskStep, plan: TaskPlan) -> Any:
        """Dispatch a step to its agent and return the result."""
        match step.agent_type:
            case AgentType.RESEARCH:
                return self._run_research(plan)
            case AgentType.WRITER:
                return self._run_writer(plan, step)
            case AgentType.VISUAL:
                return self._run_visual(plan)
            case AgentType.DESIGNER:
                return self._run_designer(plan)
            case AgentType.COMPLIANCE:
                return self._run_compliance(plan)
            case _:
                raise ValueError(f"Unknown agent type: {step.agent_type}")

    # ------------------------------------------------------------------
    # Individual agent runners
    # ------------------------------------------------------------------

    def _run_research(self, plan: TaskPlan) -> ContentBrief:
        from app.agents.research_agent import ResearchAgent

        agent = ResearchAgent(brand_config=self._brand_config)
        try:
            brief = agent.build_brief(
                query=plan.request, content_type=plan.content_type
            )
        finally:
            agent.close()

        self._content_brief = brief
        return brief

    def _run_writer(self, plan: TaskPlan, step: TaskStep) -> dict:
        from app.agents.writer_agent import WriterAgent

        agent = WriterAgent(brand_config=self._brand_config)
        feedback = self._build_compliance_feedback() if step.retry_count > 0 else ""

        content = agent.write(
            request=plan.request,
            content_type=plan.content_type,
            brief=self._content_brief or ContentBrief(),
            doc_type=plan.doc_type,
            title=plan.title,
            compliance_feedback=feedback,
        )
        self._written_content = content
        return content

    def _run_visual(self, plan: TaskPlan) -> list[dict]:
        from app.generators.visual_gen import VisualPipeline

        pipeline = VisualPipeline(brand_config=self._brand_config)

        if plan.content_type == "presentation" and self._written_content:
            assets = pipeline.generate_for_slides(
                self._written_content.get("slides", [])
            )
        else:
            text = (
                json.dumps(self._written_content)
                if self._written_content
                else plan.request
            )
            assets = pipeline.generate_from_content(text, plan.content_type)

        self._visual_assets = assets
        return assets

    def _run_designer(self, plan: TaskPlan) -> dict:
        from app.agents.designer_agent import DesignerAgent

        agent = DesignerAgent(brand_config=self._brand_config)
        result = agent.design(
            written_content=self._written_content or {},
            content_type=plan.content_type,
            doc_type=plan.doc_type,
            title=plan.title,
            visual_assets=self._visual_assets,
        )
        self._output_file = result.get("file_path")
        return result

    def _run_compliance(self, plan: TaskPlan) -> dict:
        from app.agents.compliance_agent import ComplianceAgent

        agent = ComplianceAgent(brand_config=self._brand_config)

        text = (
            json.dumps(self._written_content)
            if self._written_content
            else None
        )
        result = agent.validate(
            file_path=self._output_file or "", content_text=text
        )
        self._compliance_result = result
        return result

    # ------------------------------------------------------------------
    # Compliance helpers
    # ------------------------------------------------------------------

    def _compliance_passed(self) -> bool:
        """Check whether the last compliance result passed."""
        if self._compliance_result is None:
            return False
        return bool(self._compliance_result.get("overall_passed", False))

    def _build_compliance_feedback(self) -> str:
        """Extract actionable feedback from the last compliance result."""
        if not self._compliance_result:
            return ""

        lines: list[str] = []
        for check in self._compliance_result.get("checks", []):
            if not check.get("passed", True):
                name = check.get("display_name", check.get("name", "Unknown"))
                lines.append(f"FAILED: {name}")
                for issue in check.get("issues", []):
                    msg = issue.get("message", "")
                    fix = issue.get("fix", "")
                    lines.append(f"  - {msg}")
                    if fix:
                        lines.append(f"    Fix: {fix}")

        return "\n".join(lines) if lines else ""

    # ------------------------------------------------------------------
    # Progress reporting
    # ------------------------------------------------------------------

    def _report_progress(
        self, step: TaskStep, status: str, detail: str = ""
    ) -> None:
        if self._progress_callback:
            try:
                self._progress_callback(
                    step_id=step.step_id,
                    agent_type=step.agent_type.value,
                    status=status,
                    detail=detail,
                )
            except Exception as exc:
                logger.debug("Progress callback error: %s", exc)

    # ------------------------------------------------------------------
    # Database logging
    # ------------------------------------------------------------------

    def _log_agent_run(self, plan: TaskPlan) -> None:
        """Persist an AgentRun record to the database."""
        try:
            from app.database.models import AgentRun, get_session

            session = get_session()

            # Build per-step summary
            steps_summary = {}
            for s in plan.steps:
                steps_summary[s.step_id] = {
                    "status": s.status.value,
                    "retry_count": s.retry_count,
                    "cost_usd": s.cost_usd,
                    "error": s.error,
                }

            compliance_score = 0.0
            compliance_passed = False
            if self._compliance_result:
                compliance_score = self._compliance_result.get(
                    "overall_score", 0.0
                )
                compliance_passed = self._compliance_result.get(
                    "overall_passed", False
                )

            max_retry = max((s.retry_count for s in plan.steps), default=0)

            run = AgentRun(
                plan_id=plan.plan_id,
                request=plan.request,
                content_type=plan.content_type,
                doc_type=plan.doc_type,
                title=plan.title,
                status="completed" if not plan.has_failed() else "failed",
                output_file=self._output_file or "",
                steps_json=json.dumps(steps_summary),
                compliance_score=compliance_score,
                compliance_passed=compliance_passed,
                total_cost_usd=plan.total_cost(),
                retry_count=max_retry,
                completed_at=datetime.utcnow(),
            )
            session.add(run)
            session.commit()
            session.close()
            logger.info("AgentRun logged for plan %s", plan.plan_id[:8])
        except Exception as exc:
            logger.warning("Failed to log AgentRun: %s", exc)

    # ------------------------------------------------------------------
    # Brand config
    # ------------------------------------------------------------------

    @staticmethod
    def _load_brand_config() -> dict:
        config_path = BRAND_ASSETS_DIR / "brand_config.json"
        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not load brand config: %s", exc)
        return {}
