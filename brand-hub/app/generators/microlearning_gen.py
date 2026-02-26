"""
Brand Intelligence Content Hub - Microlearning Generator

Breaks long-form training content into focused 5-10 minute learning modules,
each with a single objective, key points, practice activity, and reflection.
"""

import json
import logging
import os
import re
import time
import zipfile
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
# Colour helpers (docx-compatible)
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
# MicrolearningGenerator
# ---------------------------------------------------------------------------

class MicrolearningGenerator:
    """Breaks long-form training content into focused micro-modules.

    Each micro-module is designed to be completable in 5-10 minutes, covers a
    single concept, and includes a learning objective, key points, a practice
    activity, and a reflection question. Modules can be rendered as individual
    DOCX documents, slide decks, or email-ready content, and packaged into a
    ZIP archive for distribution.
    """

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(self, brand_config: Optional[dict] = None):
        """Initialise the microlearning generator.

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
        module_duration: int = 7,
        output_format: str = "docx",
        title: str = "",
    ) -> dict:
        """Generate microlearning modules from curriculum content.

        Args:
            curriculum_content: Structured curriculum data with ``title``,
                ``modules`` (list of ``{title, content, objectives}``), and
                optional ``description``.
            module_duration: Target duration per module in minutes (5-10).
            output_format: ``"docx"``, ``"slides"``, or ``"email"``.
            title: Series title. Auto-generated if empty.

        Returns:
            A dict with keys: ``modules`` (list of module metadata),
            ``file_paths`` (list of str), ``zip_path`` (str), ``error`` (str or None).
        """
        start = time.time()
        result: dict[str, Any] = {
            "modules": [],
            "file_paths": [],
            "zip_path": None,
            "error": None,
        }

        try:
            # Clamp duration to sensible range
            module_duration = max(3, min(15, module_duration))

            # Default title
            if not title:
                curriculum_title = curriculum_content.get("title", "Training")
                title = f"{curriculum_title} - Microlearning Series"

            # Break content into micro-modules via Claude
            logger.info(
                "Breaking curriculum into %d-minute micro-modules",
                module_duration,
            )
            modules = self._break_into_modules(curriculum_content, module_duration)
            result["modules"] = modules

            if not modules:
                result["error"] = "No modules generated from content"
                return result

            # Ensure output directory
            TRAINING_DIR.mkdir(parents=True, exist_ok=True)

            # Render in the requested format
            file_paths: list[str] = []
            if output_format == "slides":
                file_paths = self.render_slide_modules(modules, title)
            elif output_format == "email":
                file_paths = self.render_email_modules(modules, title)
            else:
                file_paths = self.render_docx_modules(modules, title)

            result["file_paths"] = file_paths

            # Package into ZIP
            if file_paths:
                zip_path = self.package_modules(file_paths, title)
                result["zip_path"] = zip_path

            elapsed = time.time() - start
            logger.info(
                "Microlearning generated in %.1fs: %d modules, format=%s",
                elapsed,
                len(modules),
                output_format,
            )

        except Exception as exc:
            logger.error("Microlearning generation failed: %s", exc, exc_info=True)
            result["error"] = str(exc)

        return result

    # ------------------------------------------------------------------
    # Module breakdown via Claude
    # ------------------------------------------------------------------

    def _break_into_modules(self, content: dict, duration: int) -> list[dict]:
        """Call Claude to break curriculum into focused micro-modules.

        Each module dict contains: module_number, title, learning_objective,
        key_points (list of {point, explanation}), practice_activity
        ({title, instructions, duration}), reflection_question,
        estimated_minutes, source_topic.
        """
        prompt = self._build_breakdown_prompt(content, duration)
        system = (
            "You are an expert instructional designer specialising in microlearning. "
            "You break complex training material into focused, bite-sized modules "
            "that each teach exactly one concept. Each module must be completable "
            "in the specified time frame. Always return valid JSON."
        )

        raw = self._call_claude(system=system, user=prompt, max_tokens=4096)
        parsed = self._parse_json_response(raw)

        if isinstance(parsed, dict) and "modules" in parsed:
            modules = parsed["modules"]
        elif isinstance(parsed, list):
            modules = parsed
        else:
            logger.warning("Unexpected module response structure, wrapping as list")
            modules = [parsed] if parsed else []

        # Normalise and validate
        validated: list[dict] = []
        for idx, m in enumerate(modules):
            if not isinstance(m, dict):
                continue
            m["module_number"] = idx + 1
            m.setdefault("title", f"Module {idx + 1}")
            m.setdefault("learning_objective", "")
            m.setdefault("estimated_minutes", duration)
            m.setdefault("source_topic", "General")

            # Key points normalisation
            raw_points = m.get("key_points", [])
            normalised_points: list[dict] = []
            for kp in raw_points:
                if isinstance(kp, dict):
                    kp.setdefault("point", "")
                    kp.setdefault("explanation", "")
                    normalised_points.append(kp)
                elif isinstance(kp, str):
                    normalised_points.append({"point": kp, "explanation": ""})
            m["key_points"] = normalised_points

            # Practice activity normalisation
            activity = m.get("practice_activity", {})
            if isinstance(activity, str):
                activity = {"title": "Practice", "instructions": activity, "duration": 2}
            elif isinstance(activity, dict):
                activity.setdefault("title", "Practice Activity")
                activity.setdefault("instructions", "")
                activity.setdefault("duration", 2)
            else:
                activity = {"title": "Practice Activity", "instructions": "", "duration": 2}
            m["practice_activity"] = activity

            m.setdefault("reflection_question", "")

            validated.append(m)

        return validated

    def _build_breakdown_prompt(self, content: dict, duration: int) -> str:
        """Build a detailed prompt for Claude to decompose curriculum into micro-modules.

        Each module covers ONE concept, is completable in ``duration`` minutes,
        has exactly 1 learning objective, 3-5 key points with explanations,
        1 hands-on practice activity, and 1 reflection question.
        """
        if isinstance(content, dict):
            curriculum_text = json.dumps(content, indent=2, default=str)
        else:
            curriculum_text = str(content)

        prompt = f"""Break the following curriculum content into focused microlearning modules.

## Guidelines
1. Each module should cover exactly ONE concept or skill.
2. Each module should be completable in approximately {duration} minutes.
3. Modules should build on each other in a logical sequence.
4. Cover ALL content from the curriculum - do not skip topics.
5. Aim for 3-5 key points per module with brief, clear explanations.
6. Practice activities should be hands-on and immediately applicable.
7. Reflection questions should prompt deeper thinking about the concept.

## Output Format
Return a JSON object with a "modules" array. Each module object must follow this structure:

```json
{{
  "modules": [
    {{
      "module_number": 1,
      "title": "Clear, descriptive module title",
      "learning_objective": "After completing this module, the learner will be able to [action verb] [specific outcome].",
      "key_points": [
        {{
          "point": "Key concept name or statement",
          "explanation": "2-3 sentence explanation of this concept with practical relevance."
        }},
        {{
          "point": "Second key concept",
          "explanation": "Clear explanation that builds understanding."
        }},
        {{
          "point": "Third key concept",
          "explanation": "Explanation connecting to real-world application."
        }}
      ],
      "practice_activity": {{
        "title": "Short activity title",
        "instructions": "Step-by-step instructions for a hands-on activity that takes 2-3 minutes. Be specific about what the learner should do.",
        "duration": 2
      }},
      "reflection_question": "A thought-provoking question that connects this module's concept to the learner's own experience or work.",
      "estimated_minutes": {duration},
      "source_topic": "The original curriculum topic this was drawn from"
    }}
  ]
}}
```

## Requirements
1. Each module title should be engaging and descriptive (not just "Module 1").
2. Learning objectives must use measurable action verbs (identify, explain, demonstrate, apply, etc.).
3. Key points should progress from foundational to more advanced within each module.
4. Practice activities must be specific and actionable - avoid vague instructions.
5. Reflection questions should not have simple yes/no answers.
6. Return ONLY valid JSON, no markdown fences or extra text.

## Curriculum Content
{curriculum_text}
"""
        return prompt

    # ------------------------------------------------------------------
    # Rendering - DOCX modules (one page per module)
    # ------------------------------------------------------------------

    def render_docx_modules(self, modules: list[dict], title: str) -> list[str]:
        """Create one branded 1-page DOCX per micro-module.

        Each document contains the module title, learning objective callout,
        numbered key points with explanations, practice activity section,
        reflection section, and a footer with module number and estimated time.

        Returns:
            A list of file paths to the generated DOCX files.
        """
        total = len(modules)
        file_paths: list[str] = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r"[^\w\s-]", "", title)[:40].strip().replace(" ", "_")

        for module in modules:
            num = module.get("module_number", 0)
            mod_title = module.get("title", f"Module {num}")

            doc = Document()
            self._apply_brand_styles(doc)

            # ----- Header bar with module number -----
            header_para = doc.add_paragraph()
            header_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            header_para.paragraph_format.space_after = Pt(2)

            # Series title (small)
            series_run = header_para.add_run(f"{title}")
            series_run.font.name = self.body_font
            series_run.font.size = Pt(8)
            series_run.font.color.rgb = RGBColor(128, 128, 128)

            # Module number + title
            title_para = doc.add_paragraph()
            title_para.paragraph_format.space_before = Pt(4)
            title_para.paragraph_format.space_after = Pt(2)
            num_run = title_para.add_run(f"Module {num}: ")
            num_run.font.name = self.heading_font
            num_run.font.size = Pt(18)
            num_run.font.color.rgb = self.primary_rgb
            num_run.bold = True
            name_run = title_para.add_run(mod_title)
            name_run.font.name = self.heading_font
            name_run.font.size = Pt(18)
            name_run.font.color.rgb = self.secondary_rgb
            name_run.bold = True

            # Thin accent line separator
            sep_para = doc.add_paragraph()
            sep_para.paragraph_format.space_after = Pt(6)
            sep_para.paragraph_format.space_before = Pt(0)
            border_xml = (
                f'<w:pBdr {nsdecls("w")}>'
                f'  <w:bottom w:val="single" w:sz="8" w:space="1" '
                f'w:color="{_hex_to_hex_str(self.accent_hex)}"/>'
                f'</w:pBdr>'
            )
            sep_para.paragraph_format.element.append(parse_xml(border_xml))

            # ----- Learning Objective callout box -----
            obj_text = module.get("learning_objective", "")
            if obj_text:
                obj_para = doc.add_paragraph()
                obj_para.paragraph_format.left_indent = Inches(0.2)
                obj_para.paragraph_format.right_indent = Inches(0.2)
                obj_para.paragraph_format.space_before = Pt(6)
                obj_para.paragraph_format.space_after = Pt(8)

                # Background shading
                shading = parse_xml(
                    f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
                    f'w:fill="{_lighten_hex(self.primary_hex, 0.90)}"/>'
                )
                obj_para.paragraph_format.element.append(shading)

                # Left border accent
                obj_border = parse_xml(
                    f'<w:pBdr {nsdecls("w")}>'
                    f'  <w:left w:val="single" w:sz="18" w:space="8" '
                    f'w:color="{_hex_to_hex_str(self.accent_hex)}"/>'
                    f'</w:pBdr>'
                )
                obj_para.paragraph_format.element.append(obj_border)

                label_run = obj_para.add_run("Learning Objective: ")
                label_run.font.name = self.heading_font
                label_run.font.size = Pt(10)
                label_run.font.color.rgb = self.accent_rgb
                label_run.bold = True

                obj_run = obj_para.add_run(obj_text)
                obj_run.font.name = self.body_font
                obj_run.font.size = Pt(10)
                obj_run.font.color.rgb = self.text_rgb

            # ----- Key Points (numbered list) -----
            kp_heading = doc.add_paragraph()
            kp_heading.paragraph_format.space_before = Pt(8)
            kp_heading.paragraph_format.space_after = Pt(4)
            kp_run = kp_heading.add_run("Key Points")
            kp_run.font.name = self.heading_font
            kp_run.font.size = Pt(13)
            kp_run.font.color.rgb = self.primary_rgb
            kp_run.bold = True

            key_points = module.get("key_points", [])
            for kp_idx, kp in enumerate(key_points):
                point_text = kp.get("point", "") if isinstance(kp, dict) else str(kp)
                explanation = kp.get("explanation", "") if isinstance(kp, dict) else ""

                # Point (bold, numbered)
                pt_para = doc.add_paragraph()
                pt_para.paragraph_format.left_indent = Inches(0.3)
                pt_para.paragraph_format.space_after = Pt(1)
                pt_run = pt_para.add_run(f"{kp_idx + 1}. {point_text}")
                pt_run.font.name = self.body_font
                pt_run.font.size = Pt(11)
                pt_run.font.color.rgb = self.text_rgb
                pt_run.bold = True

                # Explanation (indented, normal weight)
                if explanation:
                    exp_para = doc.add_paragraph()
                    exp_para.paragraph_format.left_indent = Inches(0.5)
                    exp_para.paragraph_format.space_after = Pt(4)
                    exp_run = exp_para.add_run(explanation)
                    exp_run.font.name = self.body_font
                    exp_run.font.size = Pt(10)
                    exp_run.font.color.rgb = RGBColor(80, 80, 80)

            # ----- Practice Activity -----
            activity = module.get("practice_activity", {})
            act_title = activity.get("title", "Practice Activity")
            act_instructions = activity.get("instructions", "")
            act_duration = activity.get("duration", 2)

            act_heading = doc.add_paragraph()
            act_heading.paragraph_format.space_before = Pt(10)
            act_heading.paragraph_format.space_after = Pt(4)
            act_icon = act_heading.add_run("Practice Activity: ")
            act_icon.font.name = self.heading_font
            act_icon.font.size = Pt(13)
            act_icon.font.color.rgb = self.accent_rgb
            act_icon.bold = True
            act_name = act_heading.add_run(f"{act_title}  ({act_duration} min)")
            act_name.font.name = self.heading_font
            act_name.font.size = Pt(11)
            act_name.font.color.rgb = self.secondary_rgb

            if act_instructions:
                # Instruction box with border
                instr_para = doc.add_paragraph()
                instr_para.paragraph_format.left_indent = Inches(0.3)
                instr_para.paragraph_format.right_indent = Inches(0.3)
                instr_para.paragraph_format.space_before = Pt(4)
                instr_para.paragraph_format.space_after = Pt(8)

                instr_shading = parse_xml(
                    f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
                    f'w:fill="{_lighten_hex(self.accent_hex, 0.92)}"/>'
                )
                instr_para.paragraph_format.element.append(instr_shading)

                instr_border = parse_xml(
                    f'<w:pBdr {nsdecls("w")}>'
                    f'  <w:left w:val="single" w:sz="12" w:space="6" '
                    f'w:color="{_hex_to_hex_str(self.accent_hex)}"/>'
                    f'</w:pBdr>'
                )
                instr_para.paragraph_format.element.append(instr_border)

                instr_run = instr_para.add_run(act_instructions)
                instr_run.font.name = self.body_font
                instr_run.font.size = Pt(10)
                instr_run.font.color.rgb = self.text_rgb

            # ----- Reflect -----
            reflection = module.get("reflection_question", "")
            if reflection:
                ref_heading = doc.add_paragraph()
                ref_heading.paragraph_format.space_before = Pt(10)
                ref_heading.paragraph_format.space_after = Pt(4)
                ref_run = ref_heading.add_run("Reflect")
                ref_run.font.name = self.heading_font
                ref_run.font.size = Pt(13)
                ref_run.font.color.rgb = self.primary_rgb
                ref_run.bold = True

                ref_para = doc.add_paragraph()
                ref_para.paragraph_format.left_indent = Inches(0.3)
                ref_para.paragraph_format.space_after = Pt(6)

                # Italic reflection question with accent color
                rq_run = ref_para.add_run(reflection)
                rq_run.font.name = self.body_font
                rq_run.font.size = Pt(11)
                rq_run.font.color.rgb = self.secondary_rgb
                rq_run.italic = True

            # ----- Footer: Module X of Y | Estimated time -----
            est_min = module.get("estimated_minutes", 7)
            footer_para = doc.add_paragraph()
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            footer_para.paragraph_format.space_before = Pt(12)

            # Top border for footer
            footer_border = parse_xml(
                f'<w:pBdr {nsdecls("w")}>'
                f'  <w:top w:val="single" w:sz="4" w:space="4" '
                f'w:color="{_hex_to_hex_str(self.primary_hex)}"/>'
                f'</w:pBdr>'
            )
            footer_para.paragraph_format.element.append(footer_border)

            ft_run = footer_para.add_run(
                f"Module {num} of {total}  |  Estimated Time: {est_min} minutes"
            )
            ft_run.font.name = self.body_font
            ft_run.font.size = Pt(8)
            ft_run.font.color.rgb = RGBColor(128, 128, 128)

            if self.company_name:
                ft_co = footer_para.add_run(f"  |  {self.company_name}")
                ft_co.font.name = self.body_font
                ft_co.font.size = Pt(8)
                ft_co.font.color.rgb = RGBColor(160, 160, 160)

            # Save
            safe_mod = re.sub(r"[^\w\s-]", "", mod_title)[:30].strip().replace(" ", "_")
            file_name = f"{safe_title}_M{num:02d}_{safe_mod}_{timestamp}.docx"
            file_path = str(TRAINING_DIR / file_name)
            doc.save(file_path)
            file_paths.append(file_path)
            logger.info("Module %d/%d saved: %s", num, total, file_path)

        return file_paths

    # ------------------------------------------------------------------
    # Rendering - Slide modules (3-5 slides per module)
    # ------------------------------------------------------------------

    def render_slide_modules(self, modules: list[dict], title: str) -> list[str]:
        """Create one short slide deck (3-5 slides) per micro-module.

        Slide structure:
          1. Module title + learning objective
          2-3. Key points (2-3 per slide)
          4. Practice activity
          5. Reflection question + key takeaway

        Uses BrandedPresentationGenerator. Returns list of file paths.
        """
        from app.generators.presentation_gen import BrandedPresentationGenerator

        total = len(modules)
        file_paths: list[str] = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r"[^\w\s-]", "", title)[:40].strip().replace(" ", "_")

        gen = BrandedPresentationGenerator(brand_config=self.brand_config)

        for module in modules:
            num = module.get("module_number", 0)
            mod_title = module.get("title", f"Module {num}")
            objective = module.get("learning_objective", "")
            key_points = module.get("key_points", [])
            activity = module.get("practice_activity", {})
            reflection = module.get("reflection_question", "")
            est_min = module.get("estimated_minutes", 7)

            slides_data: list[dict] = []

            # Slide 1: Title + learning objective
            slides_data.append({
                "layout": "title",
                "title": f"Module {num}: {mod_title}",
                "subtitle": f"{title}  |  {est_min} minutes",
            })

            # Objective slide
            slides_data.append({
                "layout": "content",
                "title": "Learning Objective",
                "bullets": [objective] if objective else ["Complete this module to build your understanding."],
            })

            # Key points slides (split into groups of 2-3)
            if key_points:
                # Split key points across slides
                chunk_size = 3 if len(key_points) <= 3 else 2
                for slide_idx in range(0, len(key_points), chunk_size):
                    chunk = key_points[slide_idx:slide_idx + chunk_size]
                    slide_num = (slide_idx // chunk_size) + 1
                    total_kp_slides = -(-len(key_points) // chunk_size)  # ceiling div
                    kp_bullets: list[str] = []
                    for kp in chunk:
                        point = kp.get("point", "") if isinstance(kp, dict) else str(kp)
                        explanation = kp.get("explanation", "") if isinstance(kp, dict) else ""
                        kp_bullets.append(point)
                        if explanation:
                            kp_bullets.append(f"- {explanation}")
                    kp_title = "Key Points"
                    if total_kp_slides > 1:
                        kp_title = f"Key Points ({slide_num}/{total_kp_slides})"
                    slides_data.append({
                        "layout": "content",
                        "title": kp_title,
                        "bullets": kp_bullets,
                    })

            # Practice activity slide
            act_title = activity.get("title", "Practice Activity") if isinstance(activity, dict) else "Practice Activity"
            act_instr = activity.get("instructions", "") if isinstance(activity, dict) else str(activity)
            act_dur = activity.get("duration", 2) if isinstance(activity, dict) else 2
            practice_bullets = [
                f"Activity: {act_title}",
                f"Duration: {act_dur} minutes",
                "",
            ]
            # Split instructions into bullet points on sentences
            if act_instr:
                sentences = [s.strip() for s in act_instr.replace(". ", ".\n").split("\n") if s.strip()]
                for sentence in sentences:
                    practice_bullets.append(sentence)
            slides_data.append({
                "layout": "content",
                "title": "Practice Activity",
                "bullets": practice_bullets,
            })

            # Reflection + takeaway slide
            reflect_bullets: list[str] = []
            if reflection:
                reflect_bullets.append("Think About It:")
                reflect_bullets.append(reflection)
                reflect_bullets.append("")

            # Build a key takeaway from the first key point
            if key_points:
                first_kp = key_points[0]
                takeaway = first_kp.get("point", "") if isinstance(first_kp, dict) else str(first_kp)
                reflect_bullets.append("Key Takeaway:")
                reflect_bullets.append(takeaway)

            slides_data.append({
                "layout": "content",
                "title": "Reflect & Remember",
                "bullets": reflect_bullets if reflect_bullets else ["Review the key points from this module."],
            })

            # Closing slide
            next_mod = f"Module {num + 1}" if num < total else "Series Complete"
            slides_data.append({
                "layout": "closing",
                "title": f"Module {num} Complete",
                "subtitle": f"Up Next: {next_mod}  |  Module {num} of {total}",
            })

            # Generate
            safe_mod = re.sub(r"[^\w\s-]", "", mod_title)[:30].strip().replace(" ", "_")
            file_name = f"{safe_title}_M{num:02d}_{safe_mod}_Slides_{timestamp}.pptx"
            save_path = str(TRAINING_DIR / file_name)

            result_path = gen.generate(
                slides_data=slides_data,
                title=f"Module {num}: {mod_title}",
                save_path=save_path,
            )

            file_paths.append(result_path)
            logger.info("Slide module %d/%d saved: %s", num, total, result_path)

        return file_paths

    # ------------------------------------------------------------------
    # Rendering - Email-ready modules
    # ------------------------------------------------------------------

    def render_email_modules(self, modules: list[dict], title: str) -> list[str]:
        """Create email-ready content as simple branded DOCX docs.

        Each email document contains: subject line, engaging intro, key concept
        with bullet points, quick challenge activity, reflection prompt, and
        series footer. Returns list of file paths.
        """
        total = len(modules)
        file_paths: list[str] = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r"[^\w\s-]", "", title)[:40].strip().replace(" ", "_")

        for module in modules:
            num = module.get("module_number", 0)
            mod_title = module.get("title", f"Module {num}")
            objective = module.get("learning_objective", "")
            key_points = module.get("key_points", [])
            activity = module.get("practice_activity", {})
            reflection = module.get("reflection_question", "")
            est_min = module.get("estimated_minutes", 7)

            doc = Document()
            self._apply_brand_styles(doc)

            # ----- Subject line -----
            subject_para = doc.add_paragraph()
            subject_para.paragraph_format.space_after = Pt(2)
            subj_label = subject_para.add_run("Subject: ")
            subj_label.font.name = self.body_font
            subj_label.font.size = Pt(10)
            subj_label.font.color.rgb = RGBColor(128, 128, 128)
            subj_label.bold = True
            subj_text = subject_para.add_run(
                f"[{title}] Module {num}: {mod_title} ({est_min}-min read)"
            )
            subj_text.font.name = self.body_font
            subj_text.font.size = Pt(11)
            subj_text.font.color.rgb = self.text_rgb
            subj_text.bold = True

            # Separator
            sep = doc.add_paragraph()
            sep.paragraph_format.space_after = Pt(4)
            sep.paragraph_format.space_before = Pt(2)
            sep_border = parse_xml(
                f'<w:pBdr {nsdecls("w")}>'
                f'  <w:bottom w:val="single" w:sz="6" w:space="1" '
                f'w:color="{_hex_to_hex_str(self.primary_hex)}"/>'
                f'</w:pBdr>'
            )
            sep.paragraph_format.element.append(sep_border)

            # ----- Logo (if available) -----
            if self.logo_path and Path(self.logo_path).exists():
                logo_para = doc.add_paragraph()
                logo_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                logo_para.paragraph_format.space_after = Pt(6)
                logo_run = logo_para.add_run()
                logo_run.add_picture(self.logo_path, width=Inches(1.2))

            # ----- Brief engaging intro -----
            intro_para = doc.add_paragraph()
            intro_para.paragraph_format.space_after = Pt(8)
            greeting = intro_para.add_run("Hi there,\n\n")
            greeting.font.name = self.body_font
            greeting.font.size = Pt(11)
            greeting.font.color.rgb = self.text_rgb

            intro_text = intro_para.add_run(
                f"Welcome to Module {num} of {total} in your {title} series. "
                f"This {est_min}-minute lesson focuses on: {mod_title}."
            )
            intro_text.font.name = self.body_font
            intro_text.font.size = Pt(11)
            intro_text.font.color.rgb = self.text_rgb

            # Learning objective (subtle)
            if objective:
                obj_para = doc.add_paragraph()
                obj_para.paragraph_format.left_indent = Inches(0.2)
                obj_para.paragraph_format.space_after = Pt(8)
                obj_label = obj_para.add_run("By the end, you'll be able to: ")
                obj_label.font.name = self.body_font
                obj_label.font.size = Pt(10)
                obj_label.font.color.rgb = self.secondary_rgb
                obj_label.bold = True
                obj_val = obj_para.add_run(objective)
                obj_val.font.name = self.body_font
                obj_val.font.size = Pt(10)
                obj_val.font.color.rgb = self.text_rgb
                obj_val.italic = True

            # ----- Key concept with 3 bullet points -----
            concept_heading = doc.add_paragraph()
            concept_heading.paragraph_format.space_before = Pt(6)
            concept_heading.paragraph_format.space_after = Pt(4)
            ch_run = concept_heading.add_run(f"Today's Key Concept: {mod_title}")
            ch_run.font.name = self.heading_font
            ch_run.font.size = Pt(13)
            ch_run.font.color.rgb = self.primary_rgb
            ch_run.bold = True

            for kp in key_points[:5]:  # Limit to 5 for email readability
                point = kp.get("point", "") if isinstance(kp, dict) else str(kp)
                explanation = kp.get("explanation", "") if isinstance(kp, dict) else ""

                bp = doc.add_paragraph()
                bp.paragraph_format.left_indent = Inches(0.3)
                bp.paragraph_format.space_after = Pt(3)

                bullet_run = bp.add_run(f"\u2022  {point}")
                bullet_run.font.name = self.body_font
                bullet_run.font.size = Pt(11)
                bullet_run.font.color.rgb = self.text_rgb
                bullet_run.bold = True

                if explanation:
                    exp_run = bp.add_run(f"\n    {explanation}")
                    exp_run.font.name = self.body_font
                    exp_run.font.size = Pt(10)
                    exp_run.font.color.rgb = RGBColor(100, 100, 100)

            # ----- Quick Challenge -----
            act_instr = activity.get("instructions", "") if isinstance(activity, dict) else str(activity)
            act_dur = activity.get("duration", 2) if isinstance(activity, dict) else 2

            challenge_heading = doc.add_paragraph()
            challenge_heading.paragraph_format.space_before = Pt(10)
            challenge_heading.paragraph_format.space_after = Pt(4)
            cl_run = challenge_heading.add_run(f"Quick Challenge ({act_dur} min)")
            cl_run.font.name = self.heading_font
            cl_run.font.size = Pt(12)
            cl_run.font.color.rgb = self.accent_rgb
            cl_run.bold = True

            if act_instr:
                challenge_para = doc.add_paragraph()
                challenge_para.paragraph_format.left_indent = Inches(0.2)
                challenge_para.paragraph_format.right_indent = Inches(0.2)
                challenge_para.paragraph_format.space_after = Pt(8)

                # Shaded box
                ch_shading = parse_xml(
                    f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
                    f'w:fill="{_lighten_hex(self.accent_hex, 0.90)}"/>'
                )
                challenge_para.paragraph_format.element.append(ch_shading)

                ch_text = challenge_para.add_run(act_instr)
                ch_text.font.name = self.body_font
                ch_text.font.size = Pt(10)
                ch_text.font.color.rgb = self.text_rgb

            # ----- Think About It -----
            if reflection:
                think_heading = doc.add_paragraph()
                think_heading.paragraph_format.space_before = Pt(8)
                think_heading.paragraph_format.space_after = Pt(4)
                th_run = think_heading.add_run("Think About It")
                th_run.font.name = self.heading_font
                th_run.font.size = Pt(12)
                th_run.font.color.rgb = self.primary_rgb
                th_run.bold = True

                think_para = doc.add_paragraph()
                think_para.paragraph_format.left_indent = Inches(0.2)
                think_para.paragraph_format.space_after = Pt(8)
                think_run = think_para.add_run(reflection)
                think_run.font.name = self.body_font
                think_run.font.size = Pt(11)
                think_run.font.color.rgb = self.secondary_rgb
                think_run.italic = True

            # ----- Footer with series info -----
            footer_sep = doc.add_paragraph()
            footer_sep.paragraph_format.space_before = Pt(10)
            fs_border = parse_xml(
                f'<w:pBdr {nsdecls("w")}>'
                f'  <w:top w:val="single" w:sz="4" w:space="4" '
                f'w:color="{_hex_to_hex_str(self.primary_hex)}"/>'
                f'</w:pBdr>'
            )
            footer_sep.paragraph_format.element.append(fs_border)

            footer_para = doc.add_paragraph()
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            footer_para.paragraph_format.space_after = Pt(2)
            ft_text = footer_para.add_run(
                f"Module {num} of {total}  |  {title}"
            )
            ft_text.font.name = self.body_font
            ft_text.font.size = Pt(9)
            ft_text.font.color.rgb = RGBColor(128, 128, 128)

            if num < total:
                next_mod = modules[num] if num < len(modules) else None
                next_title = next_mod.get("title", f"Module {num + 1}") if next_mod else f"Module {num + 1}"
                next_para = doc.add_paragraph()
                next_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                next_para.paragraph_format.space_after = Pt(2)
                nx_run = next_para.add_run(f"Up next: {next_title}")
                nx_run.font.name = self.body_font
                nx_run.font.size = Pt(9)
                nx_run.font.color.rgb = self.accent_rgb
                nx_run.italic = True

            if self.company_name:
                co_para = doc.add_paragraph()
                co_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                co_run = co_para.add_run(self.company_name)
                co_run.font.name = self.body_font
                co_run.font.size = Pt(8)
                co_run.font.color.rgb = RGBColor(180, 180, 180)

            # Save
            safe_mod = re.sub(r"[^\w\s-]", "", mod_title)[:30].strip().replace(" ", "_")
            file_name = f"{safe_title}_M{num:02d}_{safe_mod}_Email_{timestamp}.docx"
            file_path = str(TRAINING_DIR / file_name)
            doc.save(file_path)
            file_paths.append(file_path)
            logger.info("Email module %d/%d saved: %s", num, total, file_path)

        return file_paths

    # ------------------------------------------------------------------
    # Packaging
    # ------------------------------------------------------------------

    def package_modules(self, file_paths: list[str], title: str) -> str:
        """Create a ZIP archive containing all generated module files.

        Args:
            file_paths: List of absolute file paths to include in the archive.
            title: Series title used for the ZIP filename.

        Returns:
            The absolute path to the created ZIP file.
        """
        TRAINING_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r"[^\w\s-]", "", title)[:40].strip().replace(" ", "_")
        zip_name = f"{safe_title}_Microlearning_Bundle_{timestamp}.zip"
        zip_path = str(TRAINING_DIR / zip_name)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fp in file_paths:
                if Path(fp).exists():
                    arcname = Path(fp).name
                    zf.write(fp, arcname)
                    logger.debug("Added to ZIP: %s", arcname)
                else:
                    logger.warning("File not found, skipping: %s", fp)

        logger.info(
            "Microlearning bundle created: %s (%d files)",
            zip_path,
            len(file_paths),
        )
        return zip_path

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

        # Page margins for compact microlearning layout
        for section in doc.sections:
            section.top_margin = Inches(0.6)
            section.bottom_margin = Inches(0.6)
            section.left_margin = Inches(0.8)
            section.right_margin = Inches(0.8)

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
            first_newline = text.find("\n")
            if first_newline != -1:
                text = text[first_newline + 1:]
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
