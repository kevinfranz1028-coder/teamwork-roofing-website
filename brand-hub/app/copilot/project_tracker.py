"""
Brand Intelligence Content Hub - Multi-Step Project Tracker

Manages multi-step project workflows for the Brand Hub Copilot.
Each project consists of ordered steps that can be executed sequentially,
with progress tracking, status management, and markdown checklist output.

Persists state via Streamlit session_state (falls back to dict for
non-Streamlit contexts such as testing or CLI usage).
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Streamlit state access — mirrors the pattern in conversation.py
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ProjectStep:
    """A single step within a multi-step project.

    Attributes
    ----------
    step_id : str
        Unique identifier (auto-generated UUID).
    title : str
        Short human-readable title for the step.
    description : str
        Longer explanation of what this step does.
    status : str
        One of "pending", "in_progress", "completed", "skipped", "failed".
    tool_name : str | None
        The copilot tool to execute for this step (e.g. "generate_caption").
    tool_input : dict
        Input parameters forwarded to the tool.
    result_summary : str
        A brief summary of the step's output after execution.
    generated_files : list
        Paths or references to files produced by this step.
    created_at : str
        ISO-format timestamp of when the step was created.
    completed_at : str | None
        ISO-format timestamp of when the step finished, or None.
    """

    title: str
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    status: str = "pending"
    tool_name: str | None = None
    tool_input: dict = field(default_factory=dict)
    result_summary: str = ""
    generated_files: list = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None


@dataclass
class Project:
    """A multi-step project that groups related steps together.

    Attributes
    ----------
    project_id : str
        Unique identifier (auto-generated UUID).
    title : str
        Human-readable project title.
    description : str
        Longer explanation of the project's goal.
    steps : list[ProjectStep]
        Ordered list of steps that make up this project.
    status : str
        One of "active", "completed", "paused", "cancelled".
    created_at : str
        ISO-format timestamp of when the project was created.
    completed_at : str | None
        ISO-format timestamp of when the project finished, or None.
    knowledge_mode : str
        The knowledge mode used for this project ("grounded", "creative", etc.).
    """

    title: str
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    steps: list[ProjectStep] = field(default_factory=list)
    status: str = "active"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None
    knowledge_mode: str = "grounded"


# ---------------------------------------------------------------------------
# Project Tracker
# ---------------------------------------------------------------------------

class ProjectTracker:
    """Manages a single active project stored in Streamlit session_state.

    The tracker provides helpers to create projects, append steps, update
    step status, query progress, and render a markdown checklist for the
    chat UI.

    Usage
    -----
    >>> tracker = ProjectTracker()
    >>> project = tracker.create_project("Weekly content batch")
    >>> tracker.add_step("Generate captions", tool_name="generate_caption")
    >>> tracker.add_step("Create images", tool_name="generate_image")
    >>> tracker.update_step(step.step_id, status="completed", result_summary="Done")
    >>> print(tracker.to_checklist())
    """

    STATE_KEY = "copilot_active_project"

    def __init__(self) -> None:
        """Initialize the project tracker.

        Ensures the session_state key exists so downstream code can
        safely read/write without KeyError guards.
        """
        state = _get_state()
        if self.STATE_KEY not in state:
            state[self.STATE_KEY] = None

    # ------------------------------------------------------------------
    # Project lifecycle
    # ------------------------------------------------------------------

    def create_project(
        self,
        title: str,
        description: str = "",
        steps: list[ProjectStep] | None = None,
        knowledge_mode: str = "grounded",
    ) -> Project:
        """Create a new active project.

        Parameters
        ----------
        title : str
            Human-readable name for the project.
        description : str
            Optional longer description of the project goal.
        steps : list[ProjectStep] | None
            Pre-defined steps to include. If ``None`` an empty list is used.
        knowledge_mode : str
            Knowledge mode for the project (default "grounded").

        Returns
        -------
        Project
            The newly created project instance.
        """
        project = Project(
            title=title,
            description=description,
            steps=steps or [],
            knowledge_mode=knowledge_mode,
        )
        state = _get_state()
        state[self.STATE_KEY] = project
        logger.info("Created project '%s' (%s) with %d steps",
                     title, project.project_id, len(project.steps))
        return project

    def get_active_project(self) -> Project | None:
        """Return the current active project, or ``None`` if none exists."""
        state = _get_state()
        return state.get(self.STATE_KEY)

    # ------------------------------------------------------------------
    # Step management
    # ------------------------------------------------------------------

    def add_step(
        self,
        title: str,
        description: str = "",
        tool_name: str | None = None,
        tool_input: dict | None = None,
    ) -> ProjectStep:
        """Append a new step to the active project.

        Parameters
        ----------
        title : str
            Short label for the step.
        description : str
            Longer explanation (optional).
        tool_name : str | None
            Copilot tool to execute (optional).
        tool_input : dict | None
            Input parameters for the tool (optional).

        Returns
        -------
        ProjectStep
            The newly created step.

        Raises
        ------
        RuntimeError
            If there is no active project.
        """
        project = self.get_active_project()
        if project is None:
            raise RuntimeError("No active project. Call create_project() first.")

        step = ProjectStep(
            title=title,
            description=description,
            tool_name=tool_name,
            tool_input=tool_input or {},
        )
        project.steps.append(step)
        logger.debug("Added step '%s' to project '%s'", title, project.title)
        return step

    def update_step(
        self,
        step_id: str,
        status: str | None = None,
        result_summary: str | None = None,
        generated_files: list | None = None,
    ) -> bool:
        """Update an existing step's status and/or results.

        Parameters
        ----------
        step_id : str
            The UUID of the step to update.
        status : str | None
            New status value (e.g. "completed", "failed").
        result_summary : str | None
            Brief text summarising the step result.
        generated_files : list | None
            File paths or references produced by the step.

        Returns
        -------
        bool
            ``True`` if the step was found and updated, ``False`` otherwise.
        """
        project = self.get_active_project()
        if project is None:
            return False

        for step in project.steps:
            if step.step_id == step_id:
                if status is not None:
                    step.status = status
                    if status == "completed":
                        step.completed_at = datetime.now().isoformat()
                if result_summary is not None:
                    step.result_summary = result_summary
                if generated_files is not None:
                    step.generated_files.extend(generated_files)
                logger.debug("Updated step %s -> status=%s", step_id, step.status)
                return True

        logger.warning("Step %s not found in active project", step_id)
        return False

    # ------------------------------------------------------------------
    # Progress & queries
    # ------------------------------------------------------------------

    def get_progress(self) -> dict:
        """Return a progress summary for the active project.

        Returns
        -------
        dict
            Keys: total, completed, in_progress, pending, percentage.
            Returns zeroes if there is no active project.
        """
        project = self.get_active_project()
        if project is None or not project.steps:
            return {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "percentage": 0.0,
            }

        total = len(project.steps)
        completed = sum(1 for s in project.steps if s.status == "completed")
        in_progress = sum(1 for s in project.steps if s.status == "in_progress")
        pending = sum(1 for s in project.steps if s.status == "pending")
        percentage = (completed / total) * 100.0 if total else 0.0

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "percentage": round(percentage, 1),
        }

    def get_next_step(self) -> ProjectStep | None:
        """Return the first pending step, or ``None`` if all steps are done.

        Returns
        -------
        ProjectStep | None
            The next step awaiting execution.
        """
        project = self.get_active_project()
        if project is None:
            return None

        for step in project.steps:
            if step.status == "pending":
                return step
        return None

    # ------------------------------------------------------------------
    # Project completion / cancellation
    # ------------------------------------------------------------------

    def complete_project(self) -> bool:
        """Mark the active project as completed.

        Returns
        -------
        bool
            ``True`` if there was an active project to complete.
        """
        project = self.get_active_project()
        if project is None:
            return False

        project.status = "completed"
        project.completed_at = datetime.now().isoformat()
        logger.info("Project '%s' marked as completed", project.title)
        return True

    def cancel_project(self) -> bool:
        """Mark the active project as cancelled.

        Returns
        -------
        bool
            ``True`` if there was an active project to cancel.
        """
        project = self.get_active_project()
        if project is None:
            return False

        project.status = "cancelled"
        project.completed_at = datetime.now().isoformat()
        logger.info("Project '%s' cancelled", project.title)
        return True

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def to_checklist(self) -> str:
        """Render the active project as a markdown checklist.

        Returns
        -------
        str
            Markdown string with progress header and checkbox list.
            Returns an empty string if there is no active project.
        """
        project = self.get_active_project()
        if project is None:
            return ""

        progress = self.get_progress()
        lines: list[str] = []

        # Header with progress bar
        lines.append(f"**{project.title}** - "
                      f"{progress['percentage']}% complete "
                      f"({progress['completed']}/{progress['total']} steps)")
        lines.append("")

        # Step checklist
        for step in project.steps:
            if step.status == "completed":
                checkbox = "[x]"
                suffix = "(completed)"
            elif step.status == "in_progress":
                checkbox = "[ ]"
                suffix = "(in progress)"
            elif step.status == "skipped":
                checkbox = "[x]"
                suffix = "(skipped)"
            elif step.status == "failed":
                checkbox = "[ ]"
                suffix = "(failed)"
            else:
                checkbox = "[ ]"
                suffix = "(pending)"

            lines.append(f"- {checkbox} {step.title} {suffix}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Remove the active project from session_state."""
        state = _get_state()
        state[self.STATE_KEY] = None
        logger.info("Active project cleared")
