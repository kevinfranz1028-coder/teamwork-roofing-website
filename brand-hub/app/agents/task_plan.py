"""
Brand Intelligence Content Hub - Task Plan

Contains:
- ``ContentBrief`` — structured research output from ResearchAgent
- ``AgentType`` / ``TaskStatus`` — step classification enums
- ``TaskStep`` / ``TaskPlan`` — multi-agent orchestration primitives
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ======================================================================
# Enums
# ======================================================================


class AgentType(str, Enum):
    """Agent role within a TaskPlan pipeline."""

    RESEARCH = "research"
    WRITER = "writer"
    DESIGNER = "designer"
    VISUAL = "visual"
    COMPLIANCE = "compliance"


class TaskStatus(str, Enum):
    """Lifecycle status for a single TaskStep."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


# ======================================================================
# TaskStep / TaskPlan
# ======================================================================


@dataclass
class TaskStep:
    """A single unit of work inside a TaskPlan."""

    step_id: str
    agent_type: AgentType
    description: str
    depends_on: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = ""
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    cost_usd: float = 0.0
    retry_count: int = 0


@dataclass
class TaskPlan:
    """Ordered collection of TaskSteps produced by OrchestratorAgent."""

    plan_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    request: str = ""
    content_type: str = ""
    output_format: str = ""
    doc_type: str = ""
    title: str = ""
    steps: list[TaskStep] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    # -- Mutation helpers --------------------------------------------------

    def add_step(self, step: TaskStep) -> None:
        """Append a step to the plan."""
        self.steps.append(step)

    def get_step(self, step_id: str) -> Optional[TaskStep]:
        """Look up a step by its ``step_id``."""
        for s in self.steps:
            if s.step_id == step_id:
                return s
        return None

    def get_next_runnable(self) -> Optional[TaskStep]:
        """Return the first PENDING step whose dependencies are all COMPLETED."""
        completed_ids = {s.step_id for s in self.steps if s.status == TaskStatus.COMPLETED}
        for s in self.steps:
            if s.status == TaskStatus.PENDING:
                if all(dep in completed_ids for dep in s.depends_on):
                    return s
        return None

    # -- Query helpers -----------------------------------------------------

    def is_complete(self) -> bool:
        """True when every step is COMPLETED or at least one is FAILED."""
        return all(
            s.status in (TaskStatus.COMPLETED, TaskStatus.FAILED) for s in self.steps
        )

    def has_failed(self) -> bool:
        """True when any step is in FAILED status."""
        return any(s.status == TaskStatus.FAILED for s in self.steps)

    def total_cost(self) -> float:
        """Sum of ``cost_usd`` across all steps."""
        return sum(s.cost_usd for s in self.steps)

    def elapsed(self) -> float:
        """Seconds since plan creation."""
        return time.time() - self.created_at

    def to_summary(self) -> str:
        """Human-readable multi-line plan summary."""
        lines = [
            f"TaskPlan {self.plan_id[:8]}",
            f"  Request : {self.request[:80]}",
            f"  Type    : {self.content_type} / {self.output_format}",
        ]
        if self.doc_type:
            lines.append(f"  DocType : {self.doc_type}")
        if self.title:
            lines.append(f"  Title   : {self.title}")
        lines.append(f"  Steps   : {len(self.steps)}")
        for s in self.steps:
            dep = f" (depends: {', '.join(s.depends_on)})" if s.depends_on else ""
            lines.append(f"    [{s.status.value:9s}] {s.step_id}: {s.description}{dep}")
        lines.append(f"  Cost    : ${self.total_cost():.4f}")
        lines.append(f"  Elapsed : {self.elapsed():.1f}s")
        return "\n".join(lines)


# ======================================================================
# ContentBrief (Phase 2 — unchanged below)
# ======================================================================


@dataclass
class ContentBrief:
    """Aggregated research output that informs a single generation task.

    Every field is populated by :class:`ResearchAgent.build_brief` from
    ChromaDB collections, SQLite tables, and ``brand_config.json``.
    Fields that yield no results are left as empty defaults so callers
    never need to check for ``None``.
    """

    # --- ChromaDB: brand_content collection ---
    relevant_existing_content: list[dict] = field(default_factory=list)
    """Semantically similar ingested collateral (documents, PDFs, web pages).
    Each dict has ``text``, ``metadata``, and ``distance``."""

    # --- ChromaDB: generated_examples collection ---
    similar_approved_examples: list[dict] = field(default_factory=list)
    """Previously generated outputs that were approved / rated highly.
    Each dict has ``text``, ``metadata``, and ``distance``."""

    # --- ChromaDB: brand_voice collection ---
    voice_guidance: list[dict] = field(default_factory=list)
    """Voice analysis samples relevant to the request.
    Each dict has ``text``, ``metadata``, and ``distance``."""

    # --- ChromaDB: terminology collection ---
    relevant_terms: list[dict] = field(default_factory=list)
    """Brand-specific terms, acronyms, and preferred vocabulary.
    Each dict has ``text``, ``metadata``, and ``distance``."""

    # --- SQLite: BrandAsset table ---
    recommended_template: Optional[dict] = None
    """Best-matching template asset (``filename``, ``file_path``,
    ``asset_type``, ``tags``)."""

    # --- SQLite: ContentLibraryItem table ---
    library_matches: list[dict] = field(default_factory=list)
    """Approved content library items matching the request keywords.
    Each dict has ``id``, ``title``, ``description``, ``tags``,
    ``category``, ``content_text`` (truncated)."""

    # --- brand_config.json ---
    brand_colors: dict = field(default_factory=dict)
    """Resolved colour palette (primary, secondary, accent, …)."""

    brand_fonts: dict = field(default_factory=dict)
    """Font families (heading, body)."""

    company_name: str = ""
    """Brand / company display name."""

    voice_profile: dict = field(default_factory=dict)
    """Full voice profile from brand_config (tone, formality, key phrases, …)."""

    terminology_config: dict = field(default_factory=dict)
    """Terminology block from brand_config (preferred_terms, acronyms, …)."""

    # --- Web research (placeholder for future Phase 3 agent) ---
    web_research: list[dict] = field(default_factory=list)
    """External web research results (populated by future WebResearchAgent)."""

    # --- Metadata ---
    query: str = ""
    """The original user request / topic that triggered this brief."""

    collection_stats: dict = field(default_factory=dict)
    """Item counts for each ChromaDB collection at query time."""

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    def to_prompt_context(self) -> str:
        """Format the entire brief as injectable prompt text.

        Returns a multi-section string that can be prepended to any
        Claude system prompt so the model is aware of existing brand
        content, voice guidance, approved examples, and terminology.

        Sections with no data are omitted to keep the prompt compact.
        """
        sections: list[str] = []

        # Header
        sections.append("=== BRAND KNOWLEDGE CONTEXT ===")
        sections.append(f"Company: {self.company_name or 'Unknown'}")

        # Brand identity
        if self.brand_colors:
            colors_str = ", ".join(f"{k}: {v}" for k, v in self.brand_colors.items())
            sections.append(f"Brand Colors: {colors_str}")
        if self.brand_fonts:
            fonts_str = ", ".join(f"{k}: {v}" for k, v in self.brand_fonts.items())
            sections.append(f"Brand Fonts: {fonts_str}")

        # Voice profile
        if self.voice_profile:
            sections.append("")
            sections.append("--- VOICE GUIDANCE ---")
            tone = self.voice_profile.get("tone", "")
            formality = self.voice_profile.get("formality", "")
            if tone:
                sections.append(f"Tone: {tone}")
            if formality:
                sections.append(f"Formality: {formality}")
            key_phrases = self.voice_profile.get("key_phrases", [])
            if key_phrases:
                sections.append(f"Key phrases: {', '.join(key_phrases[:8])}")
            avoid = self.voice_profile.get("avoid_phrases", [])
            if avoid:
                sections.append(f"Avoid: {', '.join(avoid[:5])}")
            themes = self.voice_profile.get("messaging_themes", [])
            if themes:
                sections.append(f"Messaging themes: {', '.join(themes[:6])}")

        # Voice samples from ChromaDB
        if self.voice_guidance:
            sections.append("")
            sections.append("--- VOICE SAMPLES (from brand voice collection) ---")
            for i, sample in enumerate(self.voice_guidance[:3], 1):
                text = sample.get("text", "")[:300]
                sections.append(f"Sample {i}: {text}")

        # Terminology
        if self.terminology_config:
            sections.append("")
            sections.append("--- TERMINOLOGY ---")
            acronyms = self.terminology_config.get("acronyms", {})
            if acronyms:
                acr_str = ", ".join(f"{k} = {v}" for k, v in list(acronyms.items())[:10])
                sections.append(f"Acronyms: {acr_str}")
            preferred = self.terminology_config.get("preferred_terms", {})
            if preferred:
                pref_str = ", ".join(
                    f'"{k}" → "{v}"' for k, v in list(preferred.items())[:10]
                )
                sections.append(f"Preferred terms: {pref_str}")
            programs = self.terminology_config.get("program_names", [])
            if programs:
                sections.append(f"Program names: {', '.join(programs[:8])}")

        # Relevant terms from ChromaDB
        if self.relevant_terms:
            sections.append("")
            sections.append("--- RELEVANT TERMS (from terminology collection) ---")
            for term in self.relevant_terms[:5]:
                sections.append(f"  - {term.get('text', '')[:150]}")

        # Existing content
        if self.relevant_existing_content:
            sections.append("")
            sections.append("--- RELEVANT EXISTING CONTENT ---")
            sections.append(
                "The following existing brand content is relevant to this request. "
                "Reference and build upon it where appropriate:"
            )
            for i, item in enumerate(self.relevant_existing_content[:5], 1):
                text = item.get("text", "")[:400]
                meta = item.get("metadata", {})
                source = meta.get("source", meta.get("filename", "unknown"))
                sections.append(f"[{i}] Source: {source}")
                sections.append(f"    {text}")

        # Approved examples
        if self.similar_approved_examples:
            sections.append("")
            sections.append("--- SIMILAR APPROVED EXAMPLES ---")
            sections.append(
                "These previously generated outputs were approved. "
                "Use them as quality/style references:"
            )
            for i, ex in enumerate(self.similar_approved_examples[:3], 1):
                text = ex.get("text", "")[:400]
                meta = ex.get("metadata", {})
                content_type = meta.get("content_type", "unknown")
                sections.append(f"[{i}] Type: {content_type}")
                sections.append(f"    {text}")

        # Library matches
        if self.library_matches:
            sections.append("")
            sections.append("--- CONTENT LIBRARY MATCHES ---")
            for item in self.library_matches[:5]:
                title = item.get("title", "")
                desc = item.get("description", "")[:200]
                tags = item.get("tags", "")
                sections.append(f"  - \"{title}\" (tags: {tags}): {desc}")

        # Web research (future)
        if self.web_research:
            sections.append("")
            sections.append("--- WEB RESEARCH ---")
            for r in self.web_research[:3]:
                sections.append(f"  - {r.get('title', '')}: {r.get('snippet', '')[:200]}")

        sections.append("")
        sections.append("=== END BRAND KNOWLEDGE CONTEXT ===")

        return "\n".join(sections)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def has_content(self) -> bool:
        """Return True if any research data was found."""
        return bool(
            self.relevant_existing_content
            or self.similar_approved_examples
            or self.voice_guidance
            or self.relevant_terms
            or self.library_matches
            or self.voice_profile
            or self.terminology_config
        )

    def summary(self) -> str:
        """One-line summary of what the brief contains."""
        parts = []
        if self.relevant_existing_content:
            parts.append(f"{len(self.relevant_existing_content)} content")
        if self.similar_approved_examples:
            parts.append(f"{len(self.similar_approved_examples)} examples")
        if self.voice_guidance:
            parts.append(f"{len(self.voice_guidance)} voice samples")
        if self.relevant_terms:
            parts.append(f"{len(self.relevant_terms)} terms")
        if self.library_matches:
            parts.append(f"{len(self.library_matches)} library items")
        if self.voice_profile:
            parts.append("voice profile")
        if self.terminology_config:
            parts.append("terminology")
        return f"ContentBrief({', '.join(parts) or 'empty'})"
