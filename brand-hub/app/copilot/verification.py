"""
Anti-Hallucination and Knowledge Grounding Module for Brand Hub Copilot.

Provides source attribution, confidence scoring, and knowledge-mode-aware
verification utilities so that every piece of generated content can be
traced back to its origin and flagged when grounding is weak.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

VALID_SOURCE_TYPES = frozenset(
    {"brand_asset", "knowledge_base", "user_input", "generated", "external"}
)


@dataclass
class SourceAttribution:
    """Describes a single piece of evidence backing generated content."""

    source_type: str  # one of VALID_SOURCE_TYPES
    source_id: str
    source_name: str
    relevance_score: float  # 0.0 – 1.0
    excerpt: str

    def __post_init__(self) -> None:
        if self.source_type not in VALID_SOURCE_TYPES:
            raise ValueError(
                f"Invalid source_type '{self.source_type}'. "
                f"Must be one of {sorted(VALID_SOURCE_TYPES)}."
            )
        self.relevance_score = max(0.0, min(1.0, self.relevance_score))


@dataclass
class ConfidenceScore:
    """Aggregated confidence assessment for a generated response."""

    overall: float  # 0.0 – 1.0
    factual_accuracy: float  # 0.0 – 1.0
    brand_alignment: float  # 0.0 – 1.0
    source_coverage: float  # 0.0 – 1.0
    sources: List[SourceAttribution] = field(default_factory=list)
    unverified_claims: List[str] = field(default_factory=list)
    verification_notes: str = ""


# ---------------------------------------------------------------------------
# Knowledge modes
# ---------------------------------------------------------------------------


class KnowledgeMode:
    """Pseudo-enum defining the three operational knowledge modes."""

    GROUNDED: str = "grounded"
    ENHANCED: str = "enhanced"
    RESEARCH: str = "research"

    _ALL = None  # populated lazily

    @classmethod
    def all(cls) -> frozenset[str]:
        if cls._ALL is None:
            cls._ALL = frozenset({cls.GROUNDED, cls.ENHANCED, cls.RESEARCH})
        return cls._ALL


GROUNDING_RULES: dict[str, str] = {
    KnowledgeMode.GROUNDED: (
        "Use ONLY verified brand repository facts. Mark gaps with "
        "[INSERT: description]. Flag uncertain claims with [VERIFY: claim]."
    ),
    KnowledgeMode.ENHANCED: (
        "Prefer brand repository facts. May use general knowledge for "
        "context but clearly distinguish. Flag external knowledge with "
        "[EXTERNAL: source]."
    ),
    KnowledgeMode.RESEARCH: (
        "Full creative freedom. Use brand repository as primary source "
        "but supplement with general knowledge. Cite sources where possible."
    ),
}


# ---------------------------------------------------------------------------
# Regex helpers (compiled once)
# ---------------------------------------------------------------------------

_INSERT_RE = re.compile(r"\[INSERT:\s*([^\]]+)\]", re.IGNORECASE)
_VERIFY_RE = re.compile(r"\[VERIFY:\s*([^\]]+)\]", re.IGNORECASE)
_SENTENCE_RE = re.compile(r"[^.!?]*[.!?]")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_placeholders(text: str) -> dict[str, list[str]]:
    """Return all ``[INSERT: ...]`` and ``[VERIFY: ...]`` markers found in *text*.

    Returns
    -------
    dict
        ``{"inserts": [...], "verifies": [...]}``
    """
    inserts = [m.group(1).strip() for m in _INSERT_RE.finditer(text)]
    verifies = [m.group(1).strip() for m in _VERIFY_RE.finditer(text)]
    return {"inserts": inserts, "verifies": verifies}


def build_source_context(sources: list[SourceAttribution]) -> str:
    """Format a list of sources into a human-readable context block.

    Example output::

        Source 1 (brand_asset): logo-guide.pdf - "Use the primary blue…"
        Source 2 (knowledge_base): tone-of-voice - "Always speak in…"
    """
    if not sources:
        return "No sources available."

    lines: list[str] = []
    for idx, src in enumerate(sources, start=1):
        excerpt_preview = src.excerpt[:120].replace("\n", " ")
        if len(src.excerpt) > 120:
            excerpt_preview += "..."
        lines.append(
            f'Source {idx} ({src.source_type}): {src.source_name} - "{excerpt_preview}"'
        )
    return "\n".join(lines)


def get_grounding_instruction(knowledge_mode: str) -> str:
    """Return the grounding-rule string for the requested *knowledge_mode*.

    Falls back to :pyattr:`KnowledgeMode.GROUNDED` when the mode is
    unrecognised, ensuring the safest default behaviour.
    """
    if knowledge_mode not in GROUNDING_RULES:
        logger.warning(
            "Unknown knowledge mode '%s' — falling back to GROUNDED.",
            knowledge_mode,
        )
    return GROUNDING_RULES.get(
        knowledge_mode, GROUNDING_RULES[KnowledgeMode.GROUNDED]
    )


def verify_content(
    text: str,
    sources: list[SourceAttribution],
    knowledge_mode: str = KnowledgeMode.GROUNDED,
) -> ConfidenceScore:
    """Score the trustworthiness of *text* given the supplied *sources*.

    Scoring heuristics
    ------------------
    * **source_coverage** — ratio of sentences in *text* for which at least
      one source has a non-trivial relevance score (>= 0.3).
    * **brand_alignment** — 1.0 when a ``brand_asset`` source is present
      among *sources*; 0.8 otherwise.
    * **factual_accuracy** — starts at 1.0 and is reduced for every
      ``[INSERT: ...]`` or ``[VERIFY: ...]`` placeholder found, to a
      floor of 0.1.
    * **overall** — weighted average:
      ``factual_accuracy * 0.4 + brand_alignment * 0.3 + source_coverage * 0.3``
    """

    # -- extract markers ------------------------------------------------
    placeholders = extract_placeholders(text)
    unverified_claims: list[str] = []
    for desc in placeholders["inserts"]:
        unverified_claims.append(f"[INSERT: {desc}]")
    for claim in placeholders["verifies"]:
        unverified_claims.append(f"[VERIFY: {claim}]")

    marker_count = len(unverified_claims)

    # -- source coverage ------------------------------------------------
    sentences = _SENTENCE_RE.findall(text)
    num_sentences = max(len(sentences), 1)

    relevant_sources = [s for s in sources if s.relevance_score >= 0.3]
    if relevant_sources:
        # Simple heuristic: assume each relevant source covers a
        # proportional share of the text, capped at 1.0.
        covered = min(len(relevant_sources) / num_sentences, 1.0)
    else:
        covered = 0.0

    source_coverage = round(covered, 4)

    # -- brand alignment ------------------------------------------------
    has_brand_source = any(s.source_type == "brand_asset" for s in sources)
    brand_alignment = 1.0 if has_brand_source else 0.8

    # -- factual accuracy -----------------------------------------------
    penalty_per_marker = 0.15
    factual_accuracy = max(0.1, 1.0 - marker_count * penalty_per_marker)
    factual_accuracy = round(factual_accuracy, 4)

    # -- overall --------------------------------------------------------
    overall = round(
        factual_accuracy * 0.4
        + brand_alignment * 0.3
        + source_coverage * 0.3,
        4,
    )

    # -- verification notes ---------------------------------------------
    notes_parts: list[str] = []
    notes_parts.append(f"Mode: {knowledge_mode}.")
    notes_parts.append(f"Sentences analysed: {num_sentences}.")
    notes_parts.append(f"Sources provided: {len(sources)}.")
    if marker_count:
        notes_parts.append(
            f"Unresolved markers: {marker_count} "
            f"({len(placeholders['inserts'])} inserts, "
            f"{len(placeholders['verifies'])} verifies)."
        )
    if not has_brand_source:
        notes_parts.append("No brand_asset source detected — alignment reduced.")

    verification_notes = " ".join(notes_parts)

    logger.debug(
        "verify_content: overall=%.2f factual=%.2f brand=%.2f coverage=%.2f markers=%d",
        overall,
        factual_accuracy,
        brand_alignment,
        source_coverage,
        marker_count,
    )

    return ConfidenceScore(
        overall=overall,
        factual_accuracy=factual_accuracy,
        brand_alignment=brand_alignment,
        source_coverage=source_coverage,
        sources=list(sources),
        unverified_claims=unverified_claims,
        verification_notes=verification_notes,
    )
