"""
Brand Intelligence Content Hub - Quiz & Assessment Generator

Generates branded assessments from curriculum content with multiple
question types, answer keys, scoring rubrics, and multiple output formats.
"""

import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from anthropic import Anthropic
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml

from app.config import BRAND_ASSETS_DIR, TRAINING_DIR, LOGOS_DIR

logger = logging.getLogger(__name__)
CLAUDE_MODEL = "claude-sonnet-4-20250514"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

QUESTION_TYPES = {
    "multiple_choice": "Multiple Choice (4 options, 1 correct)",
    "true_false": "True/False",
    "fill_in_blank": "Fill in the Blank",
    "short_answer": "Short Answer (1-3 sentences)",
    "matching": "Matching (pair items from two columns)",
    "scenario_based": "Scenario-Based (situational question with analysis)",
}

DIFFICULTY_LEVELS = {
    "comprehension": "Recall and understanding of facts",
    "application": "Apply knowledge to new situations",
    "analysis": "Analyze, compare, evaluate information",
}

DEFAULT_PASSING_PERCENTAGE = 70
POINTS_BY_TYPE = {
    "multiple_choice": 2,
    "true_false": 1,
    "fill_in_blank": 2,
    "short_answer": 5,
    "matching": 3,
    "scenario_based": 8,
}


# ---------------------------------------------------------------------------
# Colour helper (docx-compatible)
# ---------------------------------------------------------------------------

def _hex_to_rgb(hex_color: str) -> RGBColor:
    """Convert a hex colour string to a python-docx RGBColor."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return RGBColor(0, 0, 0)
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return RGBColor(r, g, b)
    except ValueError:
        return RGBColor(0, 0, 0)


def _hex_to_hex_str(hex_color: str) -> str:
    """Return a clean 6-char hex string (no ``#``) for XML shading values."""
    return hex_color.lstrip("#").upper()


def _lighten_hex(hex_color: str, factor: float = 0.85) -> str:
    """Lighten a hex colour by blending towards white."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "F0F0F0"
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    except ValueError:
        return "F0F0F0"
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"{r:02X}{g:02X}{b:02X}"


# ---------------------------------------------------------------------------
# QuizGenerator
# ---------------------------------------------------------------------------

class QuizGenerator:
    """Generates branded quizzes and assessments from curriculum content.

    Supports multiple question types (multiple choice, true/false, fill-in-blank,
    short answer, matching, and scenario-based), three difficulty tiers, and
    output to DOCX, PPTX, and JSON formats. Each quiz ships with a companion
    answer key and scoring rubric.
    """

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(self, brand_config: Optional[dict] = None):
        """Initialise the quiz generator.

        Args:
            brand_config: Brand configuration dict. If *None*, the file
                ``brand_assets/brand_config.json`` is loaded automatically.
        """
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.brand_config: dict = brand_config or self._load_brand_config()

        # Resolve brand colours
        colors_cfg = self.brand_config.get("colors", {})
        self.primary_hex = colors_cfg.get("primary", "#0066CC")
        self.secondary_hex = colors_cfg.get("secondary", "#004499")
        self.accent_hex = colors_cfg.get("accent", "#FF6600")
        self.text_hex = colors_cfg.get("text", "#333333")
        self.primary_rgb = _hex_to_rgb(self.primary_hex)
        self.secondary_rgb = _hex_to_rgb(self.secondary_hex)
        self.accent_rgb = _hex_to_rgb(self.accent_hex)
        self.text_rgb = _hex_to_rgb(self.text_hex)

        # Resolve brand fonts
        fonts_cfg = self.brand_config.get("fonts", {})
        self.heading_font = fonts_cfg.get("heading", "Arial")
        self.body_font = fonts_cfg.get("body", "Calibri")

        self.company_name: str = self.brand_config.get("company_name", "")
        self.logo_path: Optional[str] = self._find_logo()

    def _load_brand_config(self) -> dict:
        """Load ``brand_assets/brand_config.json``, returning ``{}`` on failure."""
        config_path = BRAND_ASSETS_DIR / "brand_config.json"
        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not load brand config: %s", exc)
        return {}

    def _find_logo(self) -> Optional[str]:
        """Return the path to the first logo image found in ``brand_assets/logos/``."""
        if not LOGOS_DIR.exists():
            return None
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.svg"):
            logos = list(LOGOS_DIR.glob(ext))
            if logos:
                return str(logos[0])
        return None

    # ------------------------------------------------------------------
    # Public API - main entry
    # ------------------------------------------------------------------

    def generate(
        self,
        curriculum_content: dict,
        question_count: int = 10,
        difficulty: str = "application",
        question_types: list[str] | None = None,
        title: str = "",
        output_format: str = "docx",
    ) -> dict:
        """Generate a complete quiz with answer key from curriculum content.

        Args:
            curriculum_content: Structured curriculum data with ``title``,
                ``modules`` (list of ``{title, content, objectives}``), and
                optional ``description``.
            question_count: Number of questions to generate.
            difficulty: One of ``comprehension``, ``application``, ``analysis``.
            question_types: Which question types to include. Defaults to all.
            title: Quiz title. Auto-generated if empty.
            output_format: ``"docx"``, ``"pptx"``, or ``"json"``.

        Returns:
            A dict with keys: ``quiz_path``, ``answer_key_path``, ``quiz_data``,
            ``question_count``, ``error``.
        """
        start = time.time()
        result: dict[str, Any] = {
            "quiz_path": None,
            "answer_key_path": None,
            "quiz_data": None,
            "question_count": 0,
            "error": None,
        }

        try:
            # Validate difficulty
            if difficulty not in DIFFICULTY_LEVELS:
                difficulty = "application"

            # Default to all question types
            if not question_types:
                question_types = list(QUESTION_TYPES.keys())
            else:
                question_types = [qt for qt in question_types if qt in QUESTION_TYPES]
                if not question_types:
                    question_types = list(QUESTION_TYPES.keys())

            # Default title
            if not title:
                curriculum_title = curriculum_content.get("title", "Assessment")
                title = f"{curriculum_title} - Quiz"

            # Generate questions via Claude
            logger.info(
                "Generating %d %s-level questions (types: %s)",
                question_count,
                difficulty,
                ", ".join(question_types),
            )
            questions = self._generate_questions(
                content=curriculum_content,
                count=question_count,
                difficulty=difficulty,
                types=question_types,
            )
            result["question_count"] = len(questions)
            result["quiz_data"] = {
                "title": title,
                "difficulty": difficulty,
                "generated_at": datetime.now().isoformat(),
                "questions": questions,
            }

            # Ensure output directory
            TRAINING_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = re.sub(r"[^\w\s-]", "", title)[:60].strip().replace(" ", "_")

            # Render in requested format
            if output_format == "pptx":
                quiz_path = self.render_pptx(questions, title)
                result["quiz_path"] = quiz_path
                # Answer key as JSON for pptx
                ak_path = self.render_json(questions, f"{title} - Answer Key")
                result["answer_key_path"] = ak_path

            elif output_format == "json":
                quiz_path = self.render_json(questions, title)
                result["quiz_path"] = quiz_path
                result["answer_key_path"] = quiz_path  # JSON includes answers

            else:
                # DOCX (default)
                quiz_doc = self.render_docx(questions, title, include_answer_key=False)
                quiz_path = str(TRAINING_DIR / f"{safe_title}_{timestamp}.docx")
                quiz_doc.save(quiz_path)
                result["quiz_path"] = quiz_path

                ak_doc = self.render_answer_key(questions, title)
                ak_path = str(TRAINING_DIR / f"{safe_title}_Answer_Key_{timestamp}.docx")
                ak_doc.save(ak_path)
                result["answer_key_path"] = ak_path

            elapsed = time.time() - start
            logger.info(
                "Quiz generated in %.1fs: %d questions, format=%s",
                elapsed,
                len(questions),
                output_format,
            )

        except Exception as exc:
            logger.error("Quiz generation failed: %s", exc, exc_info=True)
            result["error"] = str(exc)

        return result

    # ------------------------------------------------------------------
    # Question generation via Claude
    # ------------------------------------------------------------------

    def _generate_questions(
        self,
        content: dict,
        count: int,
        difficulty: str,
        types: list[str],
    ) -> list[dict]:
        """Call Claude to generate quiz questions from curriculum content.

        Returns a list of question dicts, each containing: question_number,
        question_type, question_text, options (for MC), correct_answer,
        explanation, difficulty, points, topic. Matching questions include
        a ``pairs`` list; scenario questions include ``scenario_text`` and
        ``analysis_question``.
        """
        prompt = self._build_quiz_prompt(content, count, difficulty, types)
        system = (
            "You are an expert instructional designer and assessment specialist. "
            "You create clear, fair, and pedagogically sound quiz questions that "
            "accurately test learner comprehension at the specified Bloom's taxonomy "
            "level. Always return valid JSON."
        )

        raw = self._call_claude(system=system, user=prompt, max_tokens=4096)
        parsed = self._parse_json_response(raw)

        if isinstance(parsed, dict) and "questions" in parsed:
            questions = parsed["questions"]
        elif isinstance(parsed, list):
            questions = parsed
        else:
            logger.warning("Unexpected quiz response structure, wrapping as list")
            questions = [parsed] if parsed else []

        # Normalise and validate each question
        validated: list[dict] = []
        for idx, q in enumerate(questions):
            if not isinstance(q, dict):
                continue
            q["question_number"] = idx + 1
            q_type = q.get("question_type", "multiple_choice")
            if q_type not in QUESTION_TYPES:
                q_type = "multiple_choice"
            q["question_type"] = q_type
            q.setdefault("question_text", "")
            q.setdefault("correct_answer", "")
            q.setdefault("explanation", "")
            q.setdefault("difficulty", difficulty)
            q.setdefault("points", POINTS_BY_TYPE.get(q_type, 2))
            q.setdefault("topic", "General")

            # Type-specific defaults
            if q_type == "multiple_choice":
                q.setdefault("options", {"A": "", "B": "", "C": "", "D": ""})
            elif q_type == "matching":
                q.setdefault("pairs", [])
            elif q_type == "scenario_based":
                q.setdefault("scenario_text", q.get("question_text", ""))
                q.setdefault("analysis_question", "")

            validated.append(q)

        return validated[:count]

    def _build_quiz_prompt(
        self,
        content: dict,
        count: int,
        difficulty: str,
        types: list[str],
    ) -> str:
        """Build a detailed prompt for Claude to generate quiz questions.

        Specifies the question types, difficulty level, JSON output schema,
        and includes the curriculum content for context.
        """
        # Serialise curriculum content
        if isinstance(content, dict):
            curriculum_text = json.dumps(content, indent=2, default=str)
        else:
            curriculum_text = str(content)

        # Build question-type descriptions
        type_descriptions = "\n".join(
            f"  - {t}: {QUESTION_TYPES[t]}" for t in types
        )

        difficulty_desc = DIFFICULTY_LEVELS.get(
            difficulty, "Apply knowledge to new situations"
        )

        prompt = f"""Generate exactly {count} quiz questions from the following curriculum content.

## Difficulty Level
{difficulty}: {difficulty_desc}

Questions should test learners at this Bloom's taxonomy level:
- comprehension: Remember, Understand (define, describe, identify, explain)
- application: Apply, Demonstrate (solve, use, implement, calculate)
- analysis: Analyze, Evaluate, Create (compare, contrast, critique, design)

## Question Types to Include
Distribute questions across these types as evenly as possible:
{type_descriptions}

## Output Format
Return a JSON object with a "questions" array. Each question object must have:

```json
{{
  "questions": [
    {{
      "question_number": 1,
      "question_type": "multiple_choice",
      "question_text": "What is ...?",
      "options": {{"A": "Option 1", "B": "Option 2", "C": "Option 3", "D": "Option 4"}},
      "correct_answer": "B",
      "explanation": "Option B is correct because ...",
      "difficulty": "{difficulty}",
      "points": 2,
      "topic": "Module or topic name"
    }},
    {{
      "question_number": 2,
      "question_type": "true_false",
      "question_text": "Statement to evaluate.",
      "correct_answer": "True",
      "explanation": "This is true because ...",
      "difficulty": "{difficulty}",
      "points": 1,
      "topic": "Topic name"
    }},
    {{
      "question_number": 3,
      "question_type": "fill_in_blank",
      "question_text": "The process of _______ involves ...",
      "correct_answer": "keyword",
      "explanation": "The blank should be filled with ...",
      "difficulty": "{difficulty}",
      "points": 2,
      "topic": "Topic name"
    }},
    {{
      "question_number": 4,
      "question_type": "short_answer",
      "question_text": "Explain how ...",
      "correct_answer": "Model answer covering key points ...",
      "explanation": "A good answer should mention ...",
      "difficulty": "{difficulty}",
      "points": 5,
      "topic": "Topic name"
    }},
    {{
      "question_number": 5,
      "question_type": "matching",
      "question_text": "Match each term with its definition.",
      "pairs": [
        {{"left": "Term A", "right": "Definition 1"}},
        {{"left": "Term B", "right": "Definition 2"}},
        {{"left": "Term C", "right": "Definition 3"}},
        {{"left": "Term D", "right": "Definition 4"}}
      ],
      "correct_answer": "A-1, B-2, C-3, D-4",
      "explanation": "Each term maps to its corresponding definition.",
      "difficulty": "{difficulty}",
      "points": 3,
      "topic": "Topic name"
    }},
    {{
      "question_number": 6,
      "question_type": "scenario_based",
      "scenario_text": "A detailed scenario describing a situation ...",
      "analysis_question": "Based on this scenario, what would you recommend and why?",
      "question_text": "Scenario: A detailed scenario ...",
      "correct_answer": "Model analysis covering ...",
      "explanation": "The best approach considers ...",
      "difficulty": "{difficulty}",
      "points": 8,
      "topic": "Topic name"
    }}
  ]
}}
```

## Requirements
1. Questions MUST be derived from the curriculum content below.
2. Cover different modules/topics - do NOT cluster all questions on one topic.
3. Each question must have a clear, unambiguous correct answer.
4. Multiple choice distractors should be plausible but clearly wrong.
5. Explanations should teach - explain WHY the answer is correct.
6. For matching questions, include exactly 4-6 pairs.
7. For scenario-based questions, make the scenario realistic and detailed.
8. Return ONLY valid JSON, no markdown fences or extra text.

## Curriculum Content
{curriculum_text}
"""
        return prompt

    # ------------------------------------------------------------------
    # Rendering - DOCX quiz
    # ------------------------------------------------------------------

    def render_docx(
        self,
        questions: list[dict],
        title: str,
        include_answer_key: bool = False,
    ) -> Document:
        """Create a branded DOCX quiz document.

        Renders a title page with instructions, then each question formatted
        according to its type. Optionally appends the answer key.
        """
        doc = Document()
        self._apply_brand_styles(doc)

        # ----- Title page -----
        tp = doc.add_paragraph()
        tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        tp.space_after = Pt(6)
        if self.logo_path and Path(self.logo_path).exists():
            run = tp.add_run()
            run.add_picture(self.logo_path, width=Inches(1.8))

        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_para.add_run(title)
        title_run.font.name = self.heading_font
        title_run.font.size = Pt(26)
        title_run.font.color.rgb = self.primary_rgb
        title_run.bold = True

        if self.company_name:
            comp_para = doc.add_paragraph()
            comp_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            comp_run = comp_para.add_run(self.company_name)
            comp_run.font.name = self.body_font
            comp_run.font.size = Pt(14)
            comp_run.font.color.rgb = self.secondary_rgb

        date_para = doc.add_paragraph()
        date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        date_run = date_para.add_run(datetime.now().strftime("%B %d, %Y"))
        date_run.font.name = self.body_font
        date_run.font.size = Pt(11)
        date_run.font.color.rgb = RGBColor(128, 128, 128)

        # Total points
        total_points = sum(q.get("points", 0) for q in questions)

        # Instructions box
        doc.add_paragraph()  # spacer
        instr_heading = doc.add_paragraph()
        instr_run = instr_heading.add_run("Instructions")
        instr_run.font.name = self.heading_font
        instr_run.font.size = Pt(14)
        instr_run.font.color.rgb = self.primary_rgb
        instr_run.bold = True

        instructions = [
            f"This assessment contains {len(questions)} questions worth a total of {total_points} points.",
            "Read each question carefully before answering.",
            "For multiple choice questions, select the single best answer.",
            "For short answer questions, write 1-3 complete sentences.",
            "For matching questions, draw a line or write the letter of the matching item.",
            f"A passing score is {DEFAULT_PASSING_PERCENTAGE}% ({int(total_points * DEFAULT_PASSING_PERCENTAGE / 100)} points).",
        ]
        for instr in instructions:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(f"\u2022  {instr}")
            run.font.name = self.body_font
            run.font.size = Pt(10)
            run.font.color.rgb = self.text_rgb

        # Name / Date line
        doc.add_paragraph()
        name_para = doc.add_paragraph()
        name_run = name_para.add_run("Name: ________________________________     Date: ________________")
        name_run.font.name = self.body_font
        name_run.font.size = Pt(11)

        # Page break before questions
        doc.add_page_break()

        # ----- Questions -----
        for q in questions:
            self._render_question_docx(doc, q, show_answer=include_answer_key)
            doc.add_paragraph()  # spacer between questions

        # ----- Optional inline answer key -----
        if include_answer_key:
            doc.add_page_break()
            ak_heading = doc.add_paragraph()
            ak_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
            ak_run = ak_heading.add_run("ANSWER KEY")
            ak_run.font.name = self.heading_font
            ak_run.font.size = Pt(20)
            ak_run.font.color.rgb = self.accent_rgb
            ak_run.bold = True

            for q in questions:
                self._render_answer_entry(doc, q)

        return doc

    def _render_question_docx(self, doc: Document, q: dict, show_answer: bool = False) -> None:
        """Render a single question into the DOCX document based on its type."""
        q_num = q.get("question_number", 0)
        q_type = q.get("question_type", "multiple_choice")
        q_text = q.get("question_text", "")
        points = q.get("points", 0)

        # Question header with number, type badge, and points
        header_para = doc.add_paragraph()
        num_run = header_para.add_run(f"Question {q_num}")
        num_run.font.name = self.heading_font
        num_run.font.size = Pt(12)
        num_run.font.color.rgb = self.primary_rgb
        num_run.bold = True

        type_label = QUESTION_TYPES.get(q_type, q_type).split("(")[0].strip()
        badge_run = header_para.add_run(f"   [{type_label}]")
        badge_run.font.name = self.body_font
        badge_run.font.size = Pt(9)
        badge_run.font.color.rgb = self.accent_rgb
        badge_run.italic = True

        pts_run = header_para.add_run(f"   ({points} pts)")
        pts_run.font.name = self.body_font
        pts_run.font.size = Pt(9)
        pts_run.font.color.rgb = RGBColor(128, 128, 128)

        # Render by type
        if q_type == "multiple_choice":
            self._render_mc_question(doc, q)
        elif q_type == "true_false":
            self._render_tf_question(doc, q)
        elif q_type == "fill_in_blank":
            self._render_fib_question(doc, q)
        elif q_type == "short_answer":
            self._render_sa_question(doc, q)
        elif q_type == "matching":
            self._render_matching_question(doc, q)
        elif q_type == "scenario_based":
            self._render_scenario_question(doc, q)
        else:
            # Fallback: plain text
            text_para = doc.add_paragraph()
            run = text_para.add_run(q_text)
            run.font.name = self.body_font
            run.font.size = Pt(11)

        # Show answer inline if requested
        if show_answer:
            ans_para = doc.add_paragraph()
            ans_para.paragraph_format.left_indent = Inches(0.3)
            shading = parse_xml(
                f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
                f'w:fill="{_lighten_hex(self.accent_hex, 0.88)}"/>'
            )
            ans_para.paragraph_format.element.append(shading)
            ans_label = ans_para.add_run("Correct Answer: ")
            ans_label.font.name = self.body_font
            ans_label.font.size = Pt(10)
            ans_label.font.color.rgb = self.accent_rgb
            ans_label.bold = True
            ans_val = ans_para.add_run(str(q.get("correct_answer", "")))
            ans_val.font.name = self.body_font
            ans_val.font.size = Pt(10)
            ans_val.bold = True

    def _render_mc_question(self, doc: Document, q: dict) -> None:
        """Render a multiple-choice question with A/B/C/D options."""
        text_para = doc.add_paragraph()
        text_para.paragraph_format.left_indent = Inches(0.2)
        run = text_para.add_run(q.get("question_text", ""))
        run.font.name = self.body_font
        run.font.size = Pt(11)
        run.font.color.rgb = self.text_rgb

        options = q.get("options", {})
        for letter in ("A", "B", "C", "D"):
            option_text = options.get(letter, "")
            if not option_text:
                continue
            opt_para = doc.add_paragraph()
            opt_para.paragraph_format.left_indent = Inches(0.5)
            opt_para.paragraph_format.space_after = Pt(2)
            circle_run = opt_para.add_run(f"\u25CB  {letter}.  ")
            circle_run.font.name = self.body_font
            circle_run.font.size = Pt(11)
            circle_run.font.color.rgb = self.primary_rgb
            circle_run.bold = True
            text_run = opt_para.add_run(option_text)
            text_run.font.name = self.body_font
            text_run.font.size = Pt(11)
            text_run.font.color.rgb = self.text_rgb

    def _render_tf_question(self, doc: Document, q: dict) -> None:
        """Render a True/False question with checkable blanks."""
        text_para = doc.add_paragraph()
        text_para.paragraph_format.left_indent = Inches(0.2)
        run = text_para.add_run(q.get("question_text", ""))
        run.font.name = self.body_font
        run.font.size = Pt(11)
        run.font.color.rgb = self.text_rgb

        tf_para = doc.add_paragraph()
        tf_para.paragraph_format.left_indent = Inches(0.5)
        tf_para.paragraph_format.space_before = Pt(4)
        true_run = tf_para.add_run("\u25CB  True          ")
        true_run.font.name = self.body_font
        true_run.font.size = Pt(11)
        true_run.font.color.rgb = self.primary_rgb
        true_run.bold = True
        false_run = tf_para.add_run("\u25CB  False")
        false_run.font.name = self.body_font
        false_run.font.size = Pt(11)
        false_run.font.color.rgb = self.primary_rgb
        false_run.bold = True

    def _render_fib_question(self, doc: Document, q: dict) -> None:
        """Render a fill-in-the-blank question with an underline space."""
        text_para = doc.add_paragraph()
        text_para.paragraph_format.left_indent = Inches(0.2)
        q_text = q.get("question_text", "")
        # If text has _______ already, render as-is
        if "_____" in q_text:
            run = text_para.add_run(q_text)
        else:
            run = text_para.add_run(q_text)
        run.font.name = self.body_font
        run.font.size = Pt(11)
        run.font.color.rgb = self.text_rgb

        # Additional blank line for writing
        blank_para = doc.add_paragraph()
        blank_para.paragraph_format.left_indent = Inches(0.5)
        blank_para.paragraph_format.space_before = Pt(4)
        blank_run = blank_para.add_run("Answer: ________________________________________________")
        blank_run.font.name = self.body_font
        blank_run.font.size = Pt(11)
        blank_run.font.color.rgb = RGBColor(180, 180, 180)

    def _render_sa_question(self, doc: Document, q: dict) -> None:
        """Render a short answer question with lined writing space."""
        text_para = doc.add_paragraph()
        text_para.paragraph_format.left_indent = Inches(0.2)
        run = text_para.add_run(q.get("question_text", ""))
        run.font.name = self.body_font
        run.font.size = Pt(11)
        run.font.color.rgb = self.text_rgb

        # Provide 4 lines for writing
        for _ in range(4):
            line_para = doc.add_paragraph()
            line_para.paragraph_format.left_indent = Inches(0.5)
            line_para.paragraph_format.space_after = Pt(0)
            line_para.paragraph_format.space_before = Pt(8)
            line_run = line_para.add_run(
                "________________________________________________________________________________"
            )
            line_run.font.name = self.body_font
            line_run.font.size = Pt(10)
            line_run.font.color.rgb = RGBColor(200, 200, 200)

    def _render_matching_question(self, doc: Document, q: dict) -> None:
        """Render a matching question with two columns in a table."""
        text_para = doc.add_paragraph()
        text_para.paragraph_format.left_indent = Inches(0.2)
        run = text_para.add_run(q.get("question_text", ""))
        run.font.name = self.body_font
        run.font.size = Pt(11)
        run.font.color.rgb = self.text_rgb

        pairs = q.get("pairs", [])
        if not pairs:
            return

        # Build a table with Column A and Column B headers
        table = doc.add_table(rows=1 + len(pairs), cols=3)
        table.style = "Table Grid"

        # Header row
        hdr_cells = table.rows[0].cells
        for cell_idx, hdr_text in enumerate(["Column A", "Match", "Column B"]):
            p = hdr_cells[cell_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(hdr_text)
            run.font.name = self.heading_font
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.bold = True
            shading = parse_xml(
                f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
                f'w:fill="{_hex_to_hex_str(self.primary_hex)}"/>'
            )
            hdr_cells[cell_idx]._element.get_or_add_tcPr().append(shading)

        # Shuffle right column labels for the student
        import random
        right_items = [p.get("right", "") for p in pairs]
        shuffled_right = right_items.copy()
        random.shuffle(shuffled_right)

        for row_idx, pair in enumerate(pairs):
            row_cells = table.rows[row_idx + 1].cells
            # Left item with letter label
            left_label = chr(65 + row_idx)  # A, B, C, ...
            lp = row_cells[0].paragraphs[0]
            lr = lp.add_run(f"{left_label}. {pair.get('left', '')}")
            lr.font.name = self.body_font
            lr.font.size = Pt(10)

            # Blank for match
            mp = row_cells[1].paragraphs[0]
            mp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            mr = mp.add_run("____")
            mr.font.name = self.body_font
            mr.font.size = Pt(10)

            # Right item with number label
            rp = row_cells[2].paragraphs[0]
            rr = rp.add_run(f"{row_idx + 1}. {shuffled_right[row_idx]}")
            rr.font.name = self.body_font
            rr.font.size = Pt(10)

            # Alternate row shading
            if row_idx % 2 == 0:
                for cell in row_cells:
                    alt_shading = parse_xml(
                        f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
                        f'w:fill="{_lighten_hex(self.primary_hex, 0.92)}"/>'
                    )
                    cell._element.get_or_add_tcPr().append(alt_shading)

    def _render_scenario_question(self, doc: Document, q: dict) -> None:
        """Render a scenario-based question with context paragraph and analysis prompt."""
        scenario_text = q.get("scenario_text", q.get("question_text", ""))
        analysis_q = q.get("analysis_question", "")

        # Scenario context in a shaded box
        scenario_para = doc.add_paragraph()
        scenario_para.paragraph_format.left_indent = Inches(0.3)
        scenario_para.paragraph_format.right_indent = Inches(0.3)
        scenario_para.paragraph_format.space_before = Pt(6)
        scenario_para.paragraph_format.space_after = Pt(6)
        # Add background shading
        shading = parse_xml(
            f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
            f'w:fill="{_lighten_hex(self.secondary_hex, 0.90)}"/>'
        )
        scenario_para.paragraph_format.element.append(shading)

        scene_label = scenario_para.add_run("Scenario: ")
        scene_label.font.name = self.heading_font
        scene_label.font.size = Pt(10)
        scene_label.font.color.rgb = self.secondary_rgb
        scene_label.bold = True
        scene_run = scenario_para.add_run(scenario_text)
        scene_run.font.name = self.body_font
        scene_run.font.size = Pt(10)
        scene_run.font.color.rgb = self.text_rgb
        scene_run.italic = True

        # Analysis question
        if analysis_q:
            aq_para = doc.add_paragraph()
            aq_para.paragraph_format.left_indent = Inches(0.3)
            aq_para.paragraph_format.space_before = Pt(6)
            aq_run = aq_para.add_run(analysis_q)
            aq_run.font.name = self.body_font
            aq_run.font.size = Pt(11)
            aq_run.font.color.rgb = self.text_rgb
            aq_run.bold = True

        # Writing space
        for _ in range(5):
            line_para = doc.add_paragraph()
            line_para.paragraph_format.left_indent = Inches(0.5)
            line_para.paragraph_format.space_after = Pt(0)
            line_para.paragraph_format.space_before = Pt(8)
            lr = line_para.add_run(
                "________________________________________________________________________________"
            )
            lr.font.name = self.body_font
            lr.font.size = Pt(10)
            lr.font.color.rgb = RGBColor(200, 200, 200)

    # ------------------------------------------------------------------
    # Rendering - Answer Key DOCX
    # ------------------------------------------------------------------

    def render_answer_key(self, questions: list[dict], title: str) -> Document:
        """Create a branded answer key DOCX with correct answers, explanations, and scoring rubric.

        Each question lists the correct answer (bolded), the full explanation,
        and point value. A summary table and scoring rubric appear at the end.
        """
        doc = Document()
        self._apply_brand_styles(doc)

        # ----- Title -----
        if self.logo_path and Path(self.logo_path).exists():
            logo_para = doc.add_paragraph()
            logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = logo_para.add_run()
            run.add_picture(self.logo_path, width=Inches(1.5))

        ak_title = doc.add_paragraph()
        ak_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        tr = ak_title.add_run(f"{title} - Answer Key")
        tr.font.name = self.heading_font
        tr.font.size = Pt(22)
        tr.font.color.rgb = self.accent_rgb
        tr.bold = True

        confidential = doc.add_paragraph()
        confidential.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cr = confidential.add_run("CONFIDENTIAL - FOR INSTRUCTOR USE ONLY")
        cr.font.name = self.body_font
        cr.font.size = Pt(10)
        cr.font.color.rgb = RGBColor(200, 0, 0)
        cr.bold = True
        cr.italic = True

        date_para = doc.add_paragraph()
        date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        dr = date_para.add_run(datetime.now().strftime("%B %d, %Y"))
        dr.font.name = self.body_font
        dr.font.size = Pt(10)
        dr.font.color.rgb = RGBColor(128, 128, 128)

        doc.add_paragraph()  # spacer

        # ----- Answer entries -----
        for q in questions:
            self._render_answer_entry(doc, q)

        # ----- Summary table -----
        doc.add_page_break()
        summary_heading = doc.add_paragraph()
        sr = summary_heading.add_run("Scoring Summary")
        sr.font.name = self.heading_font
        sr.font.size = Pt(16)
        sr.font.color.rgb = self.primary_rgb
        sr.bold = True

        total_points = sum(q.get("points", 0) for q in questions)

        # Build summary table
        table = doc.add_table(rows=1 + len(questions) + 1, cols=5)
        table.style = "Table Grid"

        # Header
        headers = ["#", "Type", "Topic", "Points", "Correct Answer"]
        hdr_cells = table.rows[0].cells
        for i, hdr_text in enumerate(headers):
            p = hdr_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(hdr_text)
            run.font.name = self.heading_font
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.bold = True
            shading = parse_xml(
                f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
                f'w:fill="{_hex_to_hex_str(self.primary_hex)}"/>'
            )
            hdr_cells[i]._element.get_or_add_tcPr().append(shading)

        # Data rows
        for row_idx, q in enumerate(questions):
            cells = table.rows[row_idx + 1].cells
            row_data = [
                str(q.get("question_number", row_idx + 1)),
                QUESTION_TYPES.get(q.get("question_type", ""), q.get("question_type", "")).split("(")[0].strip(),
                q.get("topic", "General"),
                str(q.get("points", 0)),
                str(q.get("correct_answer", ""))[:50],
            ]
            for i, val in enumerate(row_data):
                p = cells[i].paragraphs[0]
                if i in (0, 3):
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(val)
                run.font.name = self.body_font
                run.font.size = Pt(9)
                run.font.color.rgb = self.text_rgb

            # Alternate row shading
            if row_idx % 2 == 0:
                for cell in cells:
                    alt_shading = parse_xml(
                        f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
                        f'w:fill="{_lighten_hex(self.primary_hex, 0.92)}"/>'
                    )
                    cell._element.get_or_add_tcPr().append(alt_shading)

        # Total row
        total_cells = table.rows[-1].cells
        total_label_p = total_cells[0].paragraphs[0]
        total_label_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        total_cells[0].merge(total_cells[2])
        total_run = total_label_p.add_run("TOTAL")
        total_run.font.name = self.heading_font
        total_run.font.size = Pt(10)
        total_run.bold = True
        total_run.font.color.rgb = self.primary_rgb

        total_pts_p = total_cells[3].paragraphs[0]
        total_pts_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        total_pts_run = total_pts_p.add_run(str(total_points))
        total_pts_run.font.name = self.heading_font
        total_pts_run.font.size = Pt(10)
        total_pts_run.bold = True
        total_pts_run.font.color.rgb = self.primary_rgb

        # Passing score info
        for cell in total_cells:
            ts = parse_xml(
                f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
                f'w:fill="{_lighten_hex(self.accent_hex, 0.85)}"/>'
            )
            cell._element.get_or_add_tcPr().append(ts)

        # ----- Scoring rubric -----
        doc.add_paragraph()
        rubric_heading = doc.add_paragraph()
        rh_run = rubric_heading.add_run("Scoring Rubric")
        rh_run.font.name = self.heading_font
        rh_run.font.size = Pt(14)
        rh_run.font.color.rgb = self.primary_rgb
        rh_run.bold = True

        passing_score = int(total_points * DEFAULT_PASSING_PERCENTAGE / 100)
        rubric_lines = [
            f"Total Points Available: {total_points}",
            f"Passing Score: {passing_score} points ({DEFAULT_PASSING_PERCENTAGE}%)",
            "",
            "Grade Scale:",
            f"  A (Excellent):   {int(total_points * 0.90)}-{total_points} points (90-100%)",
            f"  B (Good):        {int(total_points * 0.80)}-{int(total_points * 0.90) - 1} points (80-89%)",
            f"  C (Satisfactory):{int(total_points * 0.70)}-{int(total_points * 0.80) - 1} points (70-79%)",
            f"  D (Needs Work):  {int(total_points * 0.60)}-{int(total_points * 0.70) - 1} points (60-69%)",
            f"  F (Failing):     Below {int(total_points * 0.60)} points (<60%)",
            "",
            "Short Answer Scoring Guidelines:",
            "  Full credit: Answer addresses all key points with accuracy.",
            "  Partial credit (50%): Answer is partially correct or incomplete.",
            "  No credit: Answer is incorrect or missing.",
            "",
            "Scenario-Based Scoring Guidelines:",
            "  Full credit: Thorough analysis with justified recommendations.",
            "  75% credit: Good analysis, minor gaps in reasoning.",
            "  50% credit: Basic analysis, missing key considerations.",
            "  25% credit: Minimal analysis, significant gaps.",
            "  No credit: Off-topic or missing.",
        ]
        for line in rubric_lines:
            rp = doc.add_paragraph()
            rp.paragraph_format.space_after = Pt(1)
            rr = rp.add_run(line)
            rr.font.name = self.body_font
            rr.font.size = Pt(10)
            rr.font.color.rgb = self.text_rgb

        return doc

    def _render_answer_entry(self, doc: Document, q: dict) -> None:
        """Render a single answer-key entry with the correct answer and explanation."""
        q_num = q.get("question_number", 0)
        q_type = q.get("question_type", "")
        q_text = q.get("question_text", "")
        correct = q.get("correct_answer", "")
        explanation = q.get("explanation", "")
        points = q.get("points", 0)
        topic = q.get("topic", "General")

        # Question reference
        ref_para = doc.add_paragraph()
        ref_para.paragraph_format.space_before = Pt(8)
        num_run = ref_para.add_run(f"Q{q_num}. ")
        num_run.font.name = self.heading_font
        num_run.font.size = Pt(11)
        num_run.font.color.rgb = self.primary_rgb
        num_run.bold = True

        type_label = QUESTION_TYPES.get(q_type, q_type).split("(")[0].strip()
        type_run = ref_para.add_run(f"[{type_label} | {points} pts | {topic}]")
        type_run.font.name = self.body_font
        type_run.font.size = Pt(9)
        type_run.font.color.rgb = RGBColor(128, 128, 128)
        type_run.italic = True

        # Question text (abbreviated)
        qt_para = doc.add_paragraph()
        qt_para.paragraph_format.left_indent = Inches(0.3)
        qt_run = qt_para.add_run(q_text[:200] + ("..." if len(q_text) > 200 else ""))
        qt_run.font.name = self.body_font
        qt_run.font.size = Pt(10)
        qt_run.font.color.rgb = RGBColor(100, 100, 100)
        qt_run.italic = True

        # Correct answer (highlighted)
        ans_para = doc.add_paragraph()
        ans_para.paragraph_format.left_indent = Inches(0.3)
        shading = parse_xml(
            f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
            f'w:fill="{_lighten_hex(self.accent_hex, 0.88)}"/>'
        )
        ans_para.paragraph_format.element.append(shading)
        label_run = ans_para.add_run("Correct Answer: ")
        label_run.font.name = self.body_font
        label_run.font.size = Pt(10)
        label_run.font.color.rgb = self.accent_rgb
        label_run.bold = True
        val_run = ans_para.add_run(str(correct))
        val_run.font.name = self.body_font
        val_run.font.size = Pt(10)
        val_run.font.color.rgb = self.text_rgb
        val_run.bold = True

        # Explanation
        if explanation:
            exp_para = doc.add_paragraph()
            exp_para.paragraph_format.left_indent = Inches(0.3)
            exp_label = exp_para.add_run("Explanation: ")
            exp_label.font.name = self.body_font
            exp_label.font.size = Pt(10)
            exp_label.font.color.rgb = self.secondary_rgb
            exp_label.bold = True
            exp_text = exp_para.add_run(explanation)
            exp_text.font.name = self.body_font
            exp_text.font.size = Pt(10)
            exp_text.font.color.rgb = self.text_rgb

        # Thin separator
        sep_para = doc.add_paragraph()
        sep_para.paragraph_format.space_after = Pt(2)
        sep_para.paragraph_format.space_before = Pt(2)
        border_xml = (
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:bottom w:val="single" w:sz="4" w:space="1" '
            f'w:color="{_hex_to_hex_str(self.primary_hex)}"/>'
            f'</w:pBdr>'
        )
        sep_para.paragraph_format.element.append(parse_xml(border_xml))

    # ------------------------------------------------------------------
    # Rendering - PPTX (slide deck for live polling)
    # ------------------------------------------------------------------

    def render_pptx(self, questions: list[dict], title: str) -> str:
        """Render quiz as a slide deck for live classroom polling.

        Creates one question slide and one answer-reveal slide per question,
        plus title and summary slides. Uses BrandedPresentationGenerator.
        """
        from app.generators.presentation_gen import BrandedPresentationGenerator

        slides_data: list[dict] = []

        # Title slide
        total_points = sum(q.get("points", 0) for q in questions)
        slides_data.append({
            "layout": "title",
            "title": title,
            "subtitle": (
                f"{len(questions)} Questions | {total_points} Total Points | "
                f"Difficulty: {questions[0].get('difficulty', 'application').title() if questions else 'Application'}"
            ),
        })

        # Instructions slide
        slides_data.append({
            "layout": "content",
            "title": "Instructions",
            "bullets": [
                "Read each question carefully before selecting your answer",
                "For multiple choice, select the single best answer",
                f"Total questions: {len(questions)}",
                f"Total points: {total_points}",
                f"Passing score: {DEFAULT_PASSING_PERCENTAGE}%",
            ],
        })

        # Question + answer reveal slides
        for q in questions:
            q_num = q.get("question_number", 0)
            q_type = q.get("question_type", "multiple_choice")
            q_text = q.get("question_text", "")
            points = q.get("points", 0)
            type_label = QUESTION_TYPES.get(q_type, q_type).split("(")[0].strip()

            # Question slide
            q_slide: dict[str, Any] = {
                "layout": "content",
                "title": f"Question {q_num}  [{type_label} - {points} pts]",
            }

            if q_type == "multiple_choice":
                options = q.get("options", {})
                bullets = [q_text, ""]
                for letter in ("A", "B", "C", "D"):
                    opt = options.get(letter, "")
                    if opt:
                        bullets.append(f"{letter}. {opt}")
                q_slide["bullets"] = bullets

            elif q_type == "true_false":
                q_slide["bullets"] = [q_text, "", "True", "False"]

            elif q_type == "matching":
                pairs = q.get("pairs", [])
                bullets = [q_text, ""]
                for idx, pair in enumerate(pairs):
                    bullets.append(f"{chr(65 + idx)}. {pair.get('left', '')}  -->  ?")
                bullets.append("")
                for idx, pair in enumerate(pairs):
                    bullets.append(f"{idx + 1}. {pair.get('right', '')}")
                q_slide["bullets"] = bullets

            elif q_type == "scenario_based":
                scenario = q.get("scenario_text", q_text)
                analysis = q.get("analysis_question", "")
                q_slide["body"] = scenario
                if analysis:
                    q_slide["bullets"] = [analysis]

            else:
                q_slide["bullets"] = [q_text]

            slides_data.append(q_slide)

            # Answer reveal slide
            correct = q.get("correct_answer", "")
            explanation = q.get("explanation", "")
            answer_bullets = [
                f"Correct Answer: {correct}",
            ]
            if explanation:
                answer_bullets.append("")
                answer_bullets.append(f"Explanation: {explanation}")

            slides_data.append({
                "layout": "content",
                "title": f"Answer - Question {q_num}",
                "bullets": answer_bullets,
            })

        # Summary slide
        topic_counts: dict[str, int] = {}
        for q in questions:
            topic = q.get("topic", "General")
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        summary_bullets = [
            f"Total Questions: {len(questions)}",
            f"Total Points: {total_points}",
            f"Passing Score: {int(total_points * DEFAULT_PASSING_PERCENTAGE / 100)} points ({DEFAULT_PASSING_PERCENTAGE}%)",
            "",
            "Topics Covered:",
        ]
        for topic, count in topic_counts.items():
            summary_bullets.append(f"- {topic}: {count} questions")

        slides_data.append({
            "layout": "closing",
            "title": "Quiz Complete",
            "subtitle": f"Review your answers | Passing: {DEFAULT_PASSING_PERCENTAGE}%",
        })

        # Generate via BrandedPresentationGenerator
        gen = BrandedPresentationGenerator(brand_config=self.brand_config)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r"[^\w\s-]", "", title)[:60].strip().replace(" ", "_")
        save_path = str(TRAINING_DIR / f"{safe_title}_Quiz_Slides_{timestamp}.pptx")

        result_path = gen.generate(
            slides_data=slides_data,
            title=title,
            save_path=save_path,
        )

        logger.info("Quiz PPTX saved: %s", result_path)
        return result_path

    # ------------------------------------------------------------------
    # Rendering - JSON
    # ------------------------------------------------------------------

    def render_json(self, questions: list[dict], title: str) -> str:
        """Save quiz data as a structured JSON file.

        Includes metadata, all questions, answer key summary, and scoring
        configuration.
        """
        total_points = sum(q.get("points", 0) for q in questions)
        passing_score = int(total_points * DEFAULT_PASSING_PERCENTAGE / 100)

        # Build answer key summary
        answer_key_entries = []
        for q in questions:
            entry = {
                "question_number": q.get("question_number"),
                "question_type": q.get("question_type"),
                "correct_answer": q.get("correct_answer"),
                "points": q.get("points"),
                "topic": q.get("topic"),
            }
            answer_key_entries.append(entry)

        quiz_data = {
            "metadata": {
                "title": title,
                "company": self.company_name,
                "generated_at": datetime.now().isoformat(),
                "question_count": len(questions),
                "total_points": total_points,
                "passing_score": passing_score,
                "passing_percentage": DEFAULT_PASSING_PERCENTAGE,
            },
            "questions": questions,
            "answer_key": answer_key_entries,
            "scoring": {
                "total_points": total_points,
                "passing_score": passing_score,
                "passing_percentage": DEFAULT_PASSING_PERCENTAGE,
                "grade_scale": {
                    "A": {"min_pct": 90, "max_pct": 100, "label": "Excellent"},
                    "B": {"min_pct": 80, "max_pct": 89, "label": "Good"},
                    "C": {"min_pct": 70, "max_pct": 79, "label": "Satisfactory"},
                    "D": {"min_pct": 60, "max_pct": 69, "label": "Needs Improvement"},
                    "F": {"min_pct": 0, "max_pct": 59, "label": "Failing"},
                },
                "partial_credit_types": ["short_answer", "scenario_based"],
            },
        }

        TRAINING_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r"[^\w\s-]", "", title)[:60].strip().replace(" ", "_")
        file_path = str(TRAINING_DIR / f"{safe_title}_{timestamp}.json")

        with open(file_path, "w", encoding="utf-8") as fh:
            json.dump(quiz_data, fh, indent=2, ensure_ascii=False, default=str)

        logger.info("Quiz JSON saved: %s", file_path)
        return file_path

    # ------------------------------------------------------------------
    # Brand styling
    # ------------------------------------------------------------------

    def _apply_brand_styles(self, doc: Document) -> None:
        """Apply brand fonts, colours, and base formatting to a DOCX document.

        Configures the Title, Heading 1-3, Normal, and List Bullet styles
        to match the loaded brand identity.
        """
        styles = doc.styles

        # Title
        title_style = styles["Title"]
        title_style.font.name = self.heading_font
        title_style.font.size = Pt(28)
        title_style.font.color.rgb = self.primary_rgb
        title_style.font.bold = True
        title_style.paragraph_format.space_after = Pt(12)

        # Heading 1
        h1 = styles["Heading 1"]
        h1.font.name = self.heading_font
        h1.font.size = Pt(22)
        h1.font.color.rgb = self.primary_rgb
        h1.font.bold = True
        h1.paragraph_format.space_before = Pt(18)
        h1.paragraph_format.space_after = Pt(6)

        # Heading 2
        h2 = styles["Heading 2"]
        h2.font.name = self.heading_font
        h2.font.size = Pt(16)
        h2.font.color.rgb = self.secondary_rgb
        h2.font.bold = True
        h2.paragraph_format.space_before = Pt(14)
        h2.paragraph_format.space_after = Pt(4)

        # Heading 3
        h3 = styles["Heading 3"]
        h3.font.name = self.heading_font
        h3.font.size = Pt(13)
        h3.font.color.rgb = self.primary_rgb
        h3.font.bold = True
        h3.paragraph_format.space_before = Pt(12)
        h3.paragraph_format.space_after = Pt(4)

        # Normal (body text)
        normal = styles["Normal"]
        normal.font.name = self.body_font
        normal.font.size = Pt(11)
        normal.font.color.rgb = self.text_rgb
        normal.paragraph_format.space_after = Pt(6)
        normal.paragraph_format.line_spacing = 1.15

        # List Bullet
        lb = styles["List Bullet"]
        lb.font.name = self.body_font
        lb.font.size = Pt(11)
        lb.font.color.rgb = self.text_rgb
        lb.paragraph_format.space_after = Pt(3)

        # Set default page margins
        for section in doc.sections:
            section.top_margin = Inches(0.8)
            section.bottom_margin = Inches(0.8)
            section.left_margin = Inches(0.9)
            section.right_margin = Inches(0.9)

    # ------------------------------------------------------------------
    # Claude integration
    # ------------------------------------------------------------------

    def _call_claude(self, system: str, user: str, max_tokens: int = 4096) -> str:
        """Send a request to the Anthropic API and return the text response.

        Retries once on transient errors with a 2-second delay.
        """
        for attempt in range(2):
            try:
                response = self.client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                # Extract text from the response
                if response.content and len(response.content) > 0:
                    return response.content[0].text
                return ""
            except Exception as exc:
                if attempt == 0:
                    logger.warning("Claude API call failed (attempt 1), retrying: %s", exc)
                    time.sleep(2)
                else:
                    logger.error("Claude API call failed after retry: %s", exc)
                    raise

        return ""

    def _parse_json_response(self, raw: str) -> Any:
        """Parse a JSON response from Claude, stripping markdown fences if present.

        Handles common formatting issues: triple-backtick code fences, leading/
        trailing whitespace, and partial JSON responses.
        """
        if not raw:
            return {}

        text = raw.strip()

        # Remove markdown code fences
        if text.startswith("```"):
            # Remove opening fence (with optional language tag)
            first_newline = text.find("\n")
            if first_newline != -1:
                text = text[first_newline + 1:]
            # Remove closing fence
            if text.rstrip().endswith("```"):
                text = text.rstrip()[:-3].rstrip()

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON object or array within the text
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start_idx = text.find(start_char)
            end_idx = text.rfind(end_char)
            if start_idx != -1 and end_idx > start_idx:
                candidate = text[start_idx:end_idx + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue

        logger.warning("Could not parse JSON from Claude response (length=%d)", len(raw))
        return {}
