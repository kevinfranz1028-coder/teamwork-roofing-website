"""
Brand Intelligence Content Hub - Feedback Loop Module

Learns from user edits to improve future content generation.  When a user
modifies AI-generated content, this module records the edit, computes a
structured diff, and uses Claude to identify recurring editing patterns
(e.g. "user always shortens paragraphs", "user prefers active voice").

Those patterns are persisted in the ``BrandConfig`` table (key
``feedback_patterns``) and can be injected as a prompt suffix into any
future content-generation call so that the model avoids the same mistakes.

Usage:
    from app.core.feedback_loop import FeedbackLoop

    fl = FeedbackLoop()

    # After a user edits generated content
    result = fl.record_edit(
        content_id=42,
        original_text="The report was written by the team...",
        edited_text="The team wrote the report...",
        content_type="document",
    )

    # Before generating new content
    enhancement = fl.get_prompt_enhancement("document")
    full_prompt = base_prompt + enhancement
"""

import difflib
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Optional

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None  # type: ignore[assignment,misc]
    ANTHROPIC_AVAILABLE = False

from app.config import BASE_DIR, DATA_DIR
from app.database.models import BrandConfig, GeneratedContent, get_session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DB_CONFIG_KEY = "feedback_patterns"
"""BrandConfig.config_key used to persist the feedback-loop data."""

CLAUDE_MODEL = "claude-sonnet-4-20250514"
"""Model identifier for all Claude API calls in this module."""

MAX_EDITS_STORED = 500
"""Maximum number of individual edit records kept in the database.
Oldest edits are pruned when this limit is exceeded."""

MAX_PATTERNS_PER_TYPE = 25
"""Maximum number of learned patterns retained per content type."""

MINIMUM_EDITS_FOR_ANALYSIS = 3
"""Minimum number of recorded edits required before pattern analysis runs."""

DEFAULT_CONTENT_TYPES = [
    "presentation",
    "document",
    "training",
    "quiz",
    "visual",
    "spreadsheet",
    "general",
]
"""Content types recognised by the feedback loop."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_json_response(raw_text: str) -> dict | list:
    """Extract a JSON object or array from Claude's response text.

    Claude occasionally wraps its JSON output in Markdown code fences
    (````` ```json ... ``` `````).  This helper strips those fences before
    attempting to parse the payload.  If the initial ``json.loads`` call
    fails it falls back to locating the outermost ``{ ... }`` or
    ``[ ... ]`` block in the text.

    Parameters
    ----------
    raw_text : str
        Raw text returned by ``response.content[0].text``.

    Returns
    -------
    dict | list
        The parsed JSON structure, or an empty ``dict`` if parsing fails.
    """
    text = raw_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()

    # First attempt: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Second attempt: find outermost braces / brackets
    obj_start = text.find("{")
    obj_end = text.rfind("}")
    arr_start = text.find("[")
    arr_end = text.rfind("]")

    # Prefer object if it starts earlier, otherwise try array
    candidates: list[tuple[int, int]] = []
    if obj_start != -1 and obj_end != -1 and obj_end > obj_start:
        candidates.append((obj_start, obj_end))
    if arr_start != -1 and arr_end != -1 and arr_end > arr_start:
        candidates.append((arr_start, arr_end))

    # Sort by start position so we try the first-occurring structure
    candidates.sort(key=lambda c: c[0])

    for start, end in candidates:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            continue

    return {}


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


class FeedbackLoop:
    """Learns from user edits to improve future content generations.

    The feedback loop operates in three stages:

    1. **Record** -- ``record_edit()`` captures the original and edited text,
       computes a diff, and (optionally) calls Claude to extract semantic
       patterns from that single edit.
    2. **Analyse** -- ``analyze_patterns()`` takes a batch of recorded edits
       and uses Claude to discover recurring preferences across them.
    3. **Enhance** -- ``get_prompt_enhancement()`` returns a natural-language
       prompt suffix that can be appended to any generation prompt so that
       Claude incorporates the learned preferences.

    All data is persisted in the ``BrandConfig`` table under the key
    ``feedback_patterns`` as a JSON blob.
    """

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(self):
        """Initialise the feedback loop.

        Loads existing pattern data from the database and creates an
        Anthropic client for Claude calls.  If the API key is missing the
        module still works but pattern *analysis* will be skipped (diffs
        are still recorded).
        """
        # Load persisted data
        self.data: dict = self._load_patterns()

        # Ensure top-level keys exist
        if "edits" not in self.data:
            self.data["edits"] = []
        if "learned_patterns" not in self.data:
            self.data["learned_patterns"] = {}

        # Anthropic client (optional -- graceful degradation)
        self.client: Optional[Anthropic] = None
        self.model: str = CLAUDE_MODEL
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if api_key and ANTHROPIC_AVAILABLE:
            try:
                self.client = Anthropic(api_key=api_key)
            except Exception as exc:
                logger.warning("Could not initialise Anthropic client: %s", exc)
        else:
            logger.info(
                "ANTHROPIC_API_KEY not set -- feedback loop will record "
                "diffs but skip Claude-based pattern analysis."
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_edit(
        self,
        content_id: int,
        original_text: str,
        edited_text: str,
        content_type: str,
    ) -> dict:
        """Record a user edit and extract patterns from the changes.

        Parameters
        ----------
        content_id : int
            The ``GeneratedContent.id`` of the content that was edited.
        original_text : str
            The original AI-generated text.
        edited_text : str
            The user-modified version of the text.
        content_type : str
            The content category (e.g. ``"presentation"``, ``"document"``).

        Returns
        -------
        dict
            A summary containing:

            - ``content_id`` -- echoed back for reference.
            - ``content_type`` -- echoed back for reference.
            - ``timestamp`` -- ISO-8601 timestamp of the recording.
            - ``diff_summary`` -- structured diff (see ``_compute_diff``).
            - ``patterns`` -- list of patterns extracted by Claude
              (empty list if Claude is unavailable or text is unchanged).
            - ``total_edits`` -- total number of edits recorded so far.
        """
        timestamp = _now_iso()

        # Compute structured diff
        diff_summary = self._compute_diff(original_text, edited_text)

        # If text is unchanged, skip pattern analysis
        patterns: list[dict] = []
        if diff_summary["change_ratio"] > 0.0 and self.client is not None:
            patterns = self._extract_edit_patterns(
                original_text, edited_text, diff_summary, content_type
            )

        # Build edit record
        edit_record: dict[str, Any] = {
            "content_id": content_id,
            "content_type": content_type,
            "timestamp": timestamp,
            "diff_summary": diff_summary,
            "patterns": patterns,
        }

        # Append and prune
        self.data["edits"].append(edit_record)
        if len(self.data["edits"]) > MAX_EDITS_STORED:
            self.data["edits"] = self.data["edits"][-MAX_EDITS_STORED:]

        # Re-analyse patterns if we have enough edits for this content type
        type_edits = [
            e for e in self.data["edits"] if e["content_type"] == content_type
        ]
        if len(type_edits) >= MINIMUM_EDITS_FOR_ANALYSIS:
            updated_patterns = self.analyze_patterns(type_edits)
            if updated_patterns:
                self.data["learned_patterns"][content_type] = updated_patterns[
                    :MAX_PATTERNS_PER_TYPE
                ]

        # Persist
        self._save_patterns()

        return {
            "content_id": content_id,
            "content_type": content_type,
            "timestamp": timestamp,
            "diff_summary": diff_summary,
            "patterns": patterns,
            "total_edits": len(self.data["edits"]),
        }

    def analyze_patterns(self, edits: list[dict]) -> list[dict]:
        """Use Claude to identify recurring editing patterns across edits.

        Parameters
        ----------
        edits : list[dict]
            A list of edit records (as produced by ``record_edit``).  Each
            record must contain at least ``diff_summary`` and ``patterns``.

        Returns
        -------
        list[dict]
            A list of pattern dictionaries, each with:

            - ``category`` -- pattern category (e.g. ``"tone"``,
              ``"structure"``, ``"length"``, ``"vocabulary"``).
            - ``description`` -- human-readable description of the pattern.
            - ``frequency`` -- approximate number of edits exhibiting this
              pattern.
            - ``example`` -- a short illustrative before/after example.

            Returns an empty list if Claude is unavailable, or if no clear
            patterns are detected.
        """
        if not edits:
            return []

        if self.client is None:
            logger.info("Claude unavailable -- skipping batch pattern analysis.")
            return self._fallback_pattern_analysis(edits)

        # Build a condensed summary of the edits for the prompt
        edit_summaries: list[str] = []
        for i, edit in enumerate(edits[:50], start=1):  # cap at 50 for context
            diff = edit.get("diff_summary", {})
            local_patterns = edit.get("patterns", [])
            summary_lines = [
                f"Edit {i}:",
                f"  Content type: {edit.get('content_type', 'unknown')}",
                f"  Change ratio: {diff.get('change_ratio', 0):.1%}",
                f"  Additions: {diff.get('additions_count', 0)}",
                f"  Deletions: {diff.get('deletions_count', 0)}",
                f"  Length change: {diff.get('length_change', 0):+d} chars",
            ]
            if diff.get("sample_additions"):
                summary_lines.append(
                    f"  Sample additions: {'; '.join(diff['sample_additions'][:3])}"
                )
            if diff.get("sample_deletions"):
                summary_lines.append(
                    f"  Sample deletions: {'; '.join(diff['sample_deletions'][:3])}"
                )
            if local_patterns:
                descs = [p.get("description", "") for p in local_patterns[:3]]
                summary_lines.append(f"  Detected patterns: {'; '.join(descs)}")
            edit_summaries.append("\n".join(summary_lines))

        edits_text = "\n\n".join(edit_summaries)

        prompt = f"""Analyse the following batch of user edits to AI-generated content.
Identify RECURRING patterns -- preferences or corrections the user applies repeatedly.

Return ONLY valid JSON (no markdown fences, no explanation) as a list of pattern objects:

[
  {{
    "category": "<one of: tone, structure, length, vocabulary, formatting, accuracy, style, clarity>",
    "description": "<clear, actionable description of the recurring pattern>",
    "frequency": <integer -- approximate number of edits showing this pattern>,
    "example": "<short before/after example illustrating the pattern>"
  }}
]

If no clear recurring patterns exist, return an empty list: []

--- EDIT HISTORY ---
{edits_text}
--- END EDIT HISTORY ---"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text
            result = _parse_json_response(raw)

            # Normalise: ensure we have a list of dicts
            if isinstance(result, list):
                patterns = []
                for item in result:
                    if isinstance(item, dict):
                        patterns.append({
                            "category": item.get("category", "general"),
                            "description": item.get("description", ""),
                            "frequency": item.get("frequency", 1),
                            "example": item.get("example", ""),
                        })
                return patterns
            elif isinstance(result, dict) and "patterns" in result:
                # Claude sometimes wraps the list in an object
                return self.analyze_patterns.__wrapped__(result["patterns"])  # type: ignore[attr-defined]

            return []

        except Exception as exc:
            logger.warning("Claude pattern analysis failed: %s", exc)
            return self._fallback_pattern_analysis(edits)

    def get_prompt_enhancement(self, content_type: str) -> str:
        """Build a prompt suffix incorporating learned patterns.

        This suffix should be appended to the generation prompt so that
        Claude produces content that already reflects the user's known
        preferences.

        Parameters
        ----------
        content_type : str
            The content category to retrieve patterns for.  Patterns
            filed under ``"general"`` are always included.

        Returns
        -------
        str
            A natural-language instruction block, or an empty string if
            no patterns have been learned yet.
        """
        type_patterns = self.data.get("learned_patterns", {}).get(content_type, [])
        general_patterns = self.data.get("learned_patterns", {}).get("general", [])

        # Merge, preferring type-specific over general
        all_patterns: list[dict] = []
        seen_descriptions: set[str] = set()

        for p in type_patterns:
            desc = p.get("description", "").lower().strip()
            if desc and desc not in seen_descriptions:
                seen_descriptions.add(desc)
                all_patterns.append(p)

        for p in general_patterns:
            desc = p.get("description", "").lower().strip()
            if desc and desc not in seen_descriptions:
                seen_descriptions.add(desc)
                all_patterns.append(p)

        if not all_patterns:
            return ""

        # Build the enhancement block
        lines: list[str] = [
            "",
            "--- USER PREFERENCE GUIDELINES (learned from previous edits) ---",
            "Based on past feedback, please follow these preferences:",
            "",
        ]

        # Group by category for readability
        by_category: dict[str, list[dict]] = {}
        for p in all_patterns:
            cat = p.get("category", "general").capitalize()
            by_category.setdefault(cat, []).append(p)

        for category, patterns in sorted(by_category.items()):
            lines.append(f"  {category}:")
            for p in patterns:
                desc = p.get("description", "")
                freq = p.get("frequency", 1)
                line = f"    - {desc}"
                if freq > 1:
                    line += f" (observed {freq} times)"
                lines.append(line)
            lines.append("")

        lines.append("--- END USER PREFERENCE GUIDELINES ---")
        lines.append("")

        return "\n".join(lines)

    def get_pattern_summary(self) -> dict:
        """Return summary statistics about recorded edits and patterns.

        Returns
        -------
        dict
            Keys:

            - ``total_edits`` -- total number of edit records stored.
            - ``edits_by_type`` -- ``{content_type: count}`` mapping.
            - ``patterns_by_type`` -- ``{content_type: count}`` mapping of
              learned patterns.
            - ``top_patterns`` -- the 10 most frequent learned patterns
              across all content types.
            - ``oldest_edit`` -- timestamp of the earliest recorded edit.
            - ``newest_edit`` -- timestamp of the most recent recorded edit.
            - ``average_change_ratio`` -- mean change ratio across all edits.
        """
        edits = self.data.get("edits", [])
        learned = self.data.get("learned_patterns", {})

        # Edits by type
        edits_by_type: dict[str, int] = {}
        total_change_ratio = 0.0
        for edit in edits:
            ct = edit.get("content_type", "unknown")
            edits_by_type[ct] = edits_by_type.get(ct, 0) + 1
            total_change_ratio += edit.get("diff_summary", {}).get(
                "change_ratio", 0.0
            )

        # Patterns by type
        patterns_by_type: dict[str, int] = {}
        all_patterns_flat: list[dict] = []
        for ct, patterns in learned.items():
            patterns_by_type[ct] = len(patterns)
            all_patterns_flat.extend(patterns)

        # Top patterns by frequency
        all_patterns_flat.sort(key=lambda p: p.get("frequency", 0), reverse=True)
        top_patterns = all_patterns_flat[:10]

        # Timestamps
        oldest_edit = edits[0].get("timestamp", "") if edits else ""
        newest_edit = edits[-1].get("timestamp", "") if edits else ""

        # Average change ratio
        avg_change_ratio = (
            total_change_ratio / len(edits) if edits else 0.0
        )

        return {
            "total_edits": len(edits),
            "edits_by_type": edits_by_type,
            "patterns_by_type": patterns_by_type,
            "top_patterns": top_patterns,
            "oldest_edit": oldest_edit,
            "newest_edit": newest_edit,
            "average_change_ratio": round(avg_change_ratio, 4),
        }

    def clear_patterns(self, content_type: Optional[str] = None) -> dict:
        """Clear stored patterns and optionally edits for a content type.

        Parameters
        ----------
        content_type : str, optional
            If provided, only patterns and edits for that content type are
            removed.  If ``None``, **all** feedback data is cleared.

        Returns
        -------
        dict
            A summary of what was cleared:

            - ``cleared_type`` -- the content type that was cleared, or
              ``"all"`` for a full reset.
            - ``edits_removed`` -- number of edit records removed.
            - ``patterns_removed`` -- number of pattern entries removed.
        """
        if content_type is None:
            edits_removed = len(self.data.get("edits", []))
            patterns_removed = sum(
                len(v) for v in self.data.get("learned_patterns", {}).values()
            )
            self.data = {"edits": [], "learned_patterns": {}}
            self._save_patterns()
            return {
                "cleared_type": "all",
                "edits_removed": edits_removed,
                "patterns_removed": patterns_removed,
            }

        # Type-specific clear
        edits_before = len(self.data.get("edits", []))
        self.data["edits"] = [
            e for e in self.data.get("edits", [])
            if e.get("content_type") != content_type
        ]
        edits_removed = edits_before - len(self.data["edits"])

        patterns_removed = len(
            self.data.get("learned_patterns", {}).get(content_type, [])
        )
        self.data.get("learned_patterns", {}).pop(content_type, None)

        self._save_patterns()
        return {
            "cleared_type": content_type,
            "edits_removed": edits_removed,
            "patterns_removed": patterns_removed,
        }

    # ------------------------------------------------------------------
    # Diff computation
    # ------------------------------------------------------------------

    def _compute_diff(self, original: str, edited: str) -> dict:
        """Compute a structured diff between original and edited text.

        Uses :mod:`difflib` to produce a unified diff and then parses it
        into a structured summary.

        Parameters
        ----------
        original : str
            The original text.
        edited : str
            The edited text.

        Returns
        -------
        dict
            Keys:

            - ``additions`` -- list of added lines/segments.
            - ``deletions`` -- list of removed lines/segments.
            - ``additions_count`` -- number of added segments.
            - ``deletions_count`` -- number of removed segments.
            - ``change_ratio`` -- ``float`` between 0.0 and 1.0 indicating
              how much of the text changed (based on
              ``SequenceMatcher.ratio``).
            - ``length_change`` -- character-count difference
              (positive = longer, negative = shorter).
            - ``word_count_change`` -- word-count difference.
            - ``sample_additions`` -- up to 5 representative additions.
            - ``sample_deletions`` -- up to 5 representative deletions.
            - ``unchanged_ratio`` -- proportion of text that remained the
              same.
        """
        if not original and not edited:
            return self._empty_diff()

        # Line-level diff
        original_lines = original.splitlines(keepends=True)
        edited_lines = edited.splitlines(keepends=True)

        differ = difflib.unified_diff(
            original_lines,
            edited_lines,
            fromfile="original",
            tofile="edited",
            lineterm="",
        )

        additions: list[str] = []
        deletions: list[str] = []

        for line in differ:
            stripped = line.rstrip("\n\r")
            if line.startswith("+") and not line.startswith("+++"):
                additions.append(stripped[1:].strip())
            elif line.startswith("-") and not line.startswith("---"):
                deletions.append(stripped[1:].strip())

        # Filter out blank entries
        additions = [a for a in additions if a]
        deletions = [d for d in deletions if d]

        # Similarity ratio (1.0 = identical, 0.0 = completely different)
        matcher = difflib.SequenceMatcher(None, original, edited)
        similarity = matcher.ratio()
        change_ratio = round(1.0 - similarity, 4)

        # Length and word-count changes
        length_change = len(edited) - len(original)
        orig_words = len(original.split())
        edit_words = len(edited.split())
        word_count_change = edit_words - orig_words

        return {
            "additions": additions,
            "deletions": deletions,
            "additions_count": len(additions),
            "deletions_count": len(deletions),
            "change_ratio": change_ratio,
            "length_change": length_change,
            "word_count_change": word_count_change,
            "sample_additions": additions[:5],
            "sample_deletions": deletions[:5],
            "unchanged_ratio": round(similarity, 4),
        }

    @staticmethod
    def _empty_diff() -> dict:
        """Return a blank diff structure."""
        return {
            "additions": [],
            "deletions": [],
            "additions_count": 0,
            "deletions_count": 0,
            "change_ratio": 0.0,
            "length_change": 0,
            "word_count_change": 0,
            "sample_additions": [],
            "sample_deletions": [],
            "unchanged_ratio": 1.0,
        }

    # ------------------------------------------------------------------
    # Claude-based pattern extraction (single edit)
    # ------------------------------------------------------------------

    def _extract_edit_patterns(
        self,
        original: str,
        edited: str,
        diff_summary: dict,
        content_type: str,
    ) -> list[dict]:
        """Use Claude to identify what the user changed and why.

        This analyses a *single* edit (as opposed to ``analyze_patterns``
        which looks across many edits).

        Parameters
        ----------
        original : str
            The original generated text.
        edited : str
            The user-edited text.
        diff_summary : dict
            The structured diff from ``_compute_diff``.
        content_type : str
            The content category.

        Returns
        -------
        list[dict]
            A list of pattern dicts, each with ``category``,
            ``description``, and ``example``.
        """
        if self.client is None:
            return []

        # Truncate long texts to stay within reasonable token limits
        max_chars = 8000
        orig_snippet = original[:max_chars]
        edit_snippet = edited[:max_chars]

        prompt = f"""Compare the original AI-generated text with the user's edited version.
Identify what the user changed and categorise each change.

Return ONLY valid JSON (no markdown fences, no explanation) as a list:

[
  {{
    "category": "<one of: tone, structure, length, vocabulary, formatting, accuracy, style, clarity>",
    "description": "<what the user changed and likely why>",
    "example": "<brief before -> after illustration>"
  }}
]

If the changes are trivial (typo fixes only), return an empty list: []

Content type: {content_type}
Change ratio: {diff_summary.get('change_ratio', 0):.1%}
Length change: {diff_summary.get('length_change', 0):+d} characters

--- ORIGINAL TEXT ---
{orig_snippet}
--- END ORIGINAL ---

--- EDITED TEXT ---
{edit_snippet}
--- END EDITED ---"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text
            result = _parse_json_response(raw)

            if isinstance(result, list):
                return [
                    {
                        "category": item.get("category", "general"),
                        "description": item.get("description", ""),
                        "example": item.get("example", ""),
                    }
                    for item in result
                    if isinstance(item, dict)
                ]
            return []

        except Exception as exc:
            logger.warning(
                "Claude edit-pattern extraction failed for content %s: %s",
                content_type,
                exc,
            )
            return []

    # ------------------------------------------------------------------
    # Fallback analysis (no Claude)
    # ------------------------------------------------------------------

    def _fallback_pattern_analysis(self, edits: list[dict]) -> list[dict]:
        """Derive basic patterns from diffs without using Claude.

        This heuristic analysis looks at aggregate statistics across the
        supplied edits to detect simple signals like "user consistently
        shortens text" or "user consistently adds content".

        Parameters
        ----------
        edits : list[dict]
            Edit records containing ``diff_summary`` data.

        Returns
        -------
        list[dict]
            A (possibly empty) list of pattern dicts.
        """
        if not edits:
            return []

        patterns: list[dict] = []
        length_changes: list[int] = []
        word_changes: list[int] = []
        change_ratios: list[float] = []

        for edit in edits:
            diff = edit.get("diff_summary", {})
            length_changes.append(diff.get("length_change", 0))
            word_changes.append(diff.get("word_count_change", 0))
            change_ratios.append(diff.get("change_ratio", 0.0))

        n = len(edits)

        # Detect consistent shortening
        shortening_count = sum(1 for lc in length_changes if lc < -20)
        if shortening_count >= n * 0.6:
            avg_reduction = abs(
                sum(lc for lc in length_changes if lc < 0) / max(shortening_count, 1)
            )
            patterns.append({
                "category": "length",
                "description": (
                    "User consistently shortens AI-generated content, "
                    f"reducing by ~{int(avg_reduction)} characters on average"
                ),
                "frequency": shortening_count,
                "example": "AI generates verbose paragraphs -> User trims to concise versions",
            })

        # Detect consistent lengthening
        lengthening_count = sum(1 for lc in length_changes if lc > 20)
        if lengthening_count >= n * 0.6:
            avg_addition = sum(
                lc for lc in length_changes if lc > 0
            ) / max(lengthening_count, 1)
            patterns.append({
                "category": "length",
                "description": (
                    "User consistently expands AI-generated content, "
                    f"adding ~{int(avg_addition)} characters on average"
                ),
                "frequency": lengthening_count,
                "example": "AI generates brief content -> User adds more detail",
            })

        # Detect heavy editing (high change ratio)
        heavy_edit_count = sum(1 for cr in change_ratios if cr > 0.4)
        if heavy_edit_count >= n * 0.5:
            avg_ratio = sum(change_ratios) / n
            patterns.append({
                "category": "style",
                "description": (
                    f"User makes substantial edits (avg {avg_ratio:.0%} changed), "
                    "suggesting generated content style differs significantly "
                    "from preferences"
                ),
                "frequency": heavy_edit_count,
                "example": "AI output requires major rewriting to match user expectations",
            })

        # Detect light editing (low change ratio -- things are mostly fine)
        light_edit_count = sum(1 for cr in change_ratios if 0.0 < cr < 0.1)
        if light_edit_count >= n * 0.7:
            patterns.append({
                "category": "accuracy",
                "description": (
                    "User makes only minor edits, indicating AI output is "
                    "mostly aligned with expectations"
                ),
                "frequency": light_edit_count,
                "example": "Small tweaks: typo fixes, minor word substitutions",
            })

        # Aggregate any per-edit patterns by description
        per_edit_patterns: dict[str, dict] = {}
        for edit in edits:
            for p in edit.get("patterns", []):
                desc = p.get("description", "")
                if not desc:
                    continue
                key = desc.lower().strip()
                if key in per_edit_patterns:
                    per_edit_patterns[key]["frequency"] += 1
                else:
                    per_edit_patterns[key] = {
                        "category": p.get("category", "general"),
                        "description": desc,
                        "frequency": 1,
                        "example": p.get("example", ""),
                    }

        # Include per-edit patterns that appear multiple times
        for key, pat in per_edit_patterns.items():
            if pat["frequency"] >= 2:
                patterns.append(pat)

        return patterns

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_patterns(self) -> None:
        """Persist the current feedback data to the ``BrandConfig`` table.

        Serialises ``self.data`` (edits + learned_patterns) to JSON and
        stores it under the key ``feedback_patterns``.
        """
        try:
            session = get_session()
            try:
                config = (
                    session.query(BrandConfig)
                    .filter(BrandConfig.config_key == DB_CONFIG_KEY)
                    .first()
                )

                json_value = json.dumps(self.data, default=str)

                if config:
                    config.config_value = json_value
                    config.updated_at = datetime.now(timezone.utc)
                else:
                    config = BrandConfig(
                        config_key=DB_CONFIG_KEY,
                        config_value=json_value,
                    )
                    session.add(config)

                session.commit()
                logger.debug(
                    "Saved feedback patterns: %d edits, %d pattern groups",
                    len(self.data.get("edits", [])),
                    len(self.data.get("learned_patterns", {})),
                )
            except Exception as exc:
                session.rollback()
                logger.error("Failed to save feedback patterns: %s", exc)
            finally:
                session.close()
        except Exception as exc:
            logger.error("Failed to open database session: %s", exc)

    def _load_patterns(self) -> dict:
        """Load feedback data from the ``BrandConfig`` table.

        Returns
        -------
        dict
            The stored feedback data, or a fresh empty structure if nothing
            has been persisted yet or if the load fails.
        """
        empty: dict = {"edits": [], "learned_patterns": {}}

        try:
            session = get_session()
            try:
                config = (
                    session.query(BrandConfig)
                    .filter(BrandConfig.config_key == DB_CONFIG_KEY)
                    .first()
                )

                if config and config.config_value:
                    data = json.loads(config.config_value)
                    if isinstance(data, dict):
                        logger.debug(
                            "Loaded feedback patterns: %d edits, %d pattern groups",
                            len(data.get("edits", [])),
                            len(data.get("learned_patterns", {})),
                        )
                        return data

                return empty

            except json.JSONDecodeError as exc:
                logger.warning("Corrupt feedback_patterns JSON: %s", exc)
                return empty
            except Exception as exc:
                logger.warning("Failed to load feedback patterns: %s", exc)
                return empty
            finally:
                session.close()
        except Exception as exc:
            logger.warning("Failed to open database session: %s", exc)
            return empty

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    def get_edit_history(
        self,
        content_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """Retrieve recent edit records, optionally filtered by content type.

        Parameters
        ----------
        content_type : str, optional
            If provided, only edits for that content type are returned.
        limit : int
            Maximum number of records to return (most recent first).

        Returns
        -------
        list[dict]
            Edit records in reverse chronological order.
        """
        edits = self.data.get("edits", [])

        if content_type:
            edits = [e for e in edits if e.get("content_type") == content_type]

        # Return most recent first
        return list(reversed(edits[-limit:]))

    def get_patterns_for_type(self, content_type: str) -> list[dict]:
        """Return learned patterns for a specific content type.

        Parameters
        ----------
        content_type : str
            The content category to look up.

        Returns
        -------
        list[dict]
            Learned patterns, or an empty list if none exist.
        """
        return self.data.get("learned_patterns", {}).get(content_type, [])

    def has_patterns(self, content_type: Optional[str] = None) -> bool:
        """Check whether any learned patterns exist.

        Parameters
        ----------
        content_type : str, optional
            If provided, checks only for that content type.

        Returns
        -------
        bool
            ``True`` if at least one pattern has been learned.
        """
        learned = self.data.get("learned_patterns", {})

        if content_type:
            return len(learned.get(content_type, [])) > 0

        return any(len(patterns) > 0 for patterns in learned.values())

    def merge_external_patterns(
        self,
        content_type: str,
        patterns: list[dict],
    ) -> int:
        """Merge externally-provided patterns into the learned store.

        This is useful for seeding the feedback loop with known preferences
        (e.g. from a brand style guide) without waiting for edit data.

        Parameters
        ----------
        content_type : str
            The content type to file the patterns under.
        patterns : list[dict]
            Pattern dicts with at least ``category`` and ``description``.

        Returns
        -------
        int
            Number of new patterns actually added (duplicates are skipped).
        """
        existing = self.data.get("learned_patterns", {}).get(content_type, [])
        existing_descs = {
            p.get("description", "").lower().strip() for p in existing
        }

        added = 0
        for p in patterns:
            desc = p.get("description", "").lower().strip()
            if desc and desc not in existing_descs:
                normalised = {
                    "category": p.get("category", "general"),
                    "description": p.get("description", ""),
                    "frequency": p.get("frequency", 1),
                    "example": p.get("example", ""),
                }
                existing.append(normalised)
                existing_descs.add(desc)
                added += 1

        # Trim to limit
        self.data.setdefault("learned_patterns", {})[content_type] = existing[
            :MAX_PATTERNS_PER_TYPE
        ]
        self._save_patterns()

        return added

    def export_data(self) -> dict:
        """Export all feedback data as a plain dictionary.

        This is useful for debugging, backing up, or migrating the
        feedback loop state.

        Returns
        -------
        dict
            A deep copy of the internal data structure.
        """
        return json.loads(json.dumps(self.data, default=str))

    def import_data(self, data: dict) -> bool:
        """Import feedback data from a dictionary, replacing current state.

        Parameters
        ----------
        data : dict
            Must contain ``edits`` (list) and ``learned_patterns`` (dict).

        Returns
        -------
        bool
            ``True`` if the import succeeded, ``False`` if the data was
            invalid.
        """
        if not isinstance(data, dict):
            logger.warning("Import failed: data is not a dict")
            return False

        if "edits" not in data or "learned_patterns" not in data:
            logger.warning(
                "Import failed: data must contain 'edits' and 'learned_patterns'"
            )
            return False

        if not isinstance(data["edits"], list):
            logger.warning("Import failed: 'edits' must be a list")
            return False

        if not isinstance(data["learned_patterns"], dict):
            logger.warning("Import failed: 'learned_patterns' must be a dict")
            return False

        self.data = data
        self._save_patterns()
        logger.info(
            "Imported feedback data: %d edits, %d pattern groups",
            len(data["edits"]),
            len(data["learned_patterns"]),
        )
        return True

    def get_content_types_with_data(self) -> list[str]:
        """Return content types that have at least one edit or pattern.

        Returns
        -------
        list[str]
            Sorted list of content type strings.
        """
        types: set[str] = set()

        for edit in self.data.get("edits", []):
            ct = edit.get("content_type")
            if ct:
                types.add(ct)

        for ct in self.data.get("learned_patterns", {}):
            types.add(ct)

        return sorted(types)

    def reanalyze_all(self) -> dict:
        """Re-run pattern analysis on all stored edits.

        Groups edits by content type and calls ``analyze_patterns`` on
        each group.  This is useful after importing data or when the
        analysis model has been updated.

        Returns
        -------
        dict
            ``{content_type: number_of_patterns_found}`` for each type
            that was re-analysed.
        """
        results: dict[str, int] = {}
        edits = self.data.get("edits", [])

        # Group edits by content type
        by_type: dict[str, list[dict]] = {}
        for edit in edits:
            ct = edit.get("content_type", "general")
            by_type.setdefault(ct, []).append(edit)

        for content_type, type_edits in by_type.items():
            if len(type_edits) < MINIMUM_EDITS_FOR_ANALYSIS:
                results[content_type] = 0
                continue

            patterns = self.analyze_patterns(type_edits)
            if patterns:
                self.data.setdefault("learned_patterns", {})[content_type] = (
                    patterns[:MAX_PATTERNS_PER_TYPE]
                )
            results[content_type] = len(patterns)

        self._save_patterns()
        return results
