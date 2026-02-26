"""
Brand Intelligence Content Hub - Presentation Generator (python-pptx)

Creates branded PPTX presentations from structured slide data.
Serves as fallback when Presenton API is unavailable.

Usage:
    from app.generators.presentation_gen import BrandedPresentationGenerator

    gen = BrandedPresentationGenerator()
    path = gen.generate(
        slides_data=[
            {"layout": "title", "title": "My Deck", "body": "Subtitle here"},
            {"layout": "content", "title": "Agenda", "bullets": ["Item 1", "Item 2"]},
            {"layout": "closing", "title": "Thank You"},
        ],
        title="My Deck",
    )
"""

import json
import logging
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.chart import XL_CHART_TYPE

from app.config import BASE_DIR, BRAND_ASSETS_DIR, PRESENTATIONS_DIR, LOGOS_DIR, TEMPLATES_DIR

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

def hex_to_rgb(hex_color: str) -> RGBColor:
    """Convert a hex colour string (e.g. ``#0066CC``) to a python-pptx ``RGBColor``.

    Gracefully handles missing ``#`` prefix and returns black for invalid input.
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return RGBColor(0, 0, 0)
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return RGBColor(r, g, b)


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

class BrandedPresentationGenerator:
    """Generates fully-branded PPTX files from structured slide JSON.

    The generator reads brand colours, fonts, and logo from the project's
    ``brand_assets/`` directory and applies them to every slide it creates.
    Eight distinct layout types are supported (title, section divider,
    content, two-column, image + text, chart / data, quote callout, and
    closing).  Unknown layout names fall back to the content layout.

    If an existing PPTX is supplied as ``template_path`` the generator
    reuses its slide masters; otherwise it starts from a blank widescreen
    (16:9) canvas.
    """

    # Slide dimensions (widescreen 16:9)
    SLIDE_WIDTH = Inches(13.333)
    SLIDE_HEIGHT = Inches(7.5)

    # Layout type constants
    LAYOUT_TITLE = "title"
    LAYOUT_SECTION = "section_divider"
    LAYOUT_CONTENT = "content"
    LAYOUT_TWO_COLUMN = "two_column"
    LAYOUT_IMAGE_TEXT = "image_text"
    LAYOUT_CHART = "chart_data"
    LAYOUT_QUOTE = "quote_callout"
    LAYOUT_CLOSING = "closing"

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(self, brand_config: Optional[dict] = None):
        """Initialise with brand configuration.

        Args:
            brand_config: A brand-config dictionary matching the schema in
                ``brand_assets/brand_config.json``.  If *None* the file is
                loaded automatically; if the file is missing, sensible
                defaults are used.
        """
        self.brand_config: dict = brand_config or self._load_brand_config()
        self.colors: dict[str, RGBColor] = self._resolve_colors()
        self.fonts: dict[str, str] = self._resolve_fonts()
        self.company_name: str = self.brand_config.get("company_name", "")
        self.logo_path: Optional[str] = self._find_logo()

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------

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

    def _resolve_colors(self) -> dict[str, RGBColor]:
        """Extract colours from brand config with safe defaults."""
        colors_cfg = self.brand_config.get("colors", {})
        return {
            "primary": hex_to_rgb(colors_cfg.get("primary", "#0066CC")),
            "secondary": hex_to_rgb(colors_cfg.get("secondary", "#004499")),
            "background": hex_to_rgb(colors_cfg.get("background", "#FFFFFF")),
            "accent": hex_to_rgb(colors_cfg.get("accent", "#FF6600")),
            "text": hex_to_rgb(colors_cfg.get("text", "#333333")),
            "white": RGBColor(255, 255, 255),
            "light_gray": RGBColor(240, 240, 240),
            "dark_gray": RGBColor(80, 80, 80),
        }

    def _resolve_fonts(self) -> dict[str, str]:
        """Extract font family names from brand config with defaults."""
        fonts_cfg = self.brand_config.get("fonts", {})
        return {
            "heading": fonts_cfg.get("heading", "Arial"),
            "body": fonts_cfg.get("body", "Calibri"),
        }

    def _find_logo(self) -> Optional[str]:
        """Return the path to the first logo image found in ``brand_assets/logos/``.

        Searches for PNG, JPG, JPEG, and SVG files in order.  Returns
        *None* when no logo is available.
        """
        if not LOGOS_DIR.exists():
            return None
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.svg"):
            logos = list(LOGOS_DIR.glob(ext))
            if logos:
                return str(logos[0])
        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        slides_data: list[dict],
        title: str = "Presentation",
        save_path: Optional[str] = None,
        template_path: Optional[str] = None,
    ) -> str:
        """Generate a complete branded PPTX from structured slide data.

        Args:
            slides_data: List of slide dictionaries.  Each dict may contain:

                - **layout** (str): One of the ``LAYOUT_*`` constants.  When
                  omitted the generator auto-selects based on content and
                  position within the deck.
                - **title** (str): Slide title.
                - **subtitle** (str): Subtitle (title/closing slides).
                - **bullets** (list[str]): Bullet-point strings.  Prefix a
                  bullet with ``"- "`` for a sub-bullet (indented level 1).
                - **body** (str): Paragraph text.
                - **speaker_notes** (str): Notes pane text.
                - **suggested_visual** (str): Description of a visual for
                  image placeholder labels.
                - **columns** (list[dict]): Column dicts for ``two_column``
                  layout.  Each column dict may have ``title``/``heading``,
                  ``bullets``, and ``body``.
                - **chart_data** (dict): Chart configuration with ``type``
                  (``"bar"``/``"column"``/``"line"``/``"pie"``),
                  ``categories``, and ``series`` (list of ``{name, values}``
                  dicts).  Alternatively ``data`` as a list of lists (header
                  row then data rows).
                - **quote** (str): Quote text for ``quote_callout`` layout.
                - **attribution** (str): Quote attribution.
                - **table_data** (list[list]): 2-D list; first row is header.
                - **image_path** (str): Path to an image file for the
                  ``image_text`` layout.

            title: Presentation title used for PPTX metadata and the default
                filename.
            save_path: Explicit file path to write to.  When *None* a
                timestamped filename is generated inside
                ``output/presentations/``.
            template_path: Optional path to an existing PPTX file to use as
                the slide-master base.

        Returns:
            The absolute file path of the saved PPTX.
        """
        start_time = time.time()

        # Open template or create blank presentation
        if template_path and Path(template_path).exists():
            prs = Presentation(template_path)
            logger.info("Using template base: %s", template_path)
        else:
            prs = Presentation()
            prs.slide_width = self.SLIDE_WIDTH
            prs.slide_height = self.SLIDE_HEIGHT

        # Build each slide
        total = len(slides_data)
        for idx, slide_data in enumerate(slides_data):
            layout = slide_data.get(
                "layout",
                self._auto_select_layout(slide_data, idx, total),
            )
            self._add_slide(prs, slide_data, layout)

        # Core properties / metadata
        prs.core_properties.title = title
        prs.core_properties.author = self.company_name or "Brand Hub"
        prs.core_properties.comments = "Generated by Brand Intelligence Content Hub"

        # Determine output path
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(
                c if c.isalnum() or c in " -_" else "" for c in title
            ).strip().replace(" ", "_")
            save_path = str(PRESENTATIONS_DIR / f"{safe_title}_{timestamp}.pptx")

        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        prs.save(save_path)

        gen_time = time.time() - start_time
        logger.info(
            "Generated presentation '%s' (%d slides) in %.1fs: %s",
            title,
            total,
            gen_time,
            save_path,
        )
        return save_path

    # ------------------------------------------------------------------
    # Layout auto-selection
    # ------------------------------------------------------------------

    def _auto_select_layout(self, slide_data: dict, index: int, total: int) -> str:
        """Automatically pick the best layout based on content and position.

        Heuristics:
        - First slide -> title
        - Last slide  -> closing
        - Has ``quote`` key -> quote callout
        - Has ``chart_data`` -> chart
        - Has ``columns`` -> two-column
        - Has ``image_path`` -> image + text
        - Title only, no body/bullets -> section divider
        - Everything else -> content
        """
        if index == 0:
            return self.LAYOUT_TITLE
        if index == total - 1:
            return self.LAYOUT_CLOSING
        if slide_data.get("quote"):
            return self.LAYOUT_QUOTE
        if slide_data.get("chart_data"):
            return self.LAYOUT_CHART
        if slide_data.get("columns"):
            return self.LAYOUT_TWO_COLUMN
        if slide_data.get("image_path"):
            return self.LAYOUT_IMAGE_TEXT

        # Short title with no real content -> section divider
        bullets = slide_data.get("bullets", [])
        body = slide_data.get("body", "")
        if not bullets and not body and slide_data.get("title"):
            return self.LAYOUT_SECTION

        return self.LAYOUT_CONTENT

    # ------------------------------------------------------------------
    # Slide dispatcher
    # ------------------------------------------------------------------

    def _add_slide(self, prs: Presentation, slide_data: dict, layout: str) -> None:
        """Add a single slide to the presentation, dispatching to the
        appropriate builder method.

        Uses the blank layout (index 6) as the base; falls back to the last
        available layout if the presentation has fewer than seven layouts.
        All placeholders inherited from the layout are removed so that each
        builder has full control.
        """
        layout_idx = min(6, len(prs.slide_layouts) - 1)
        slide_layout = prs.slide_layouts[layout_idx]
        slide = prs.slides.add_slide(slide_layout)

        # Remove inherited placeholders
        for shape in list(slide.placeholders):
            sp = shape._element
            sp.getparent().remove(sp)

        # Route to the correct builder
        builders = {
            self.LAYOUT_TITLE: self._build_title_slide,
            self.LAYOUT_SECTION: self._build_section_slide,
            self.LAYOUT_CONTENT: self._build_content_slide,
            self.LAYOUT_TWO_COLUMN: self._build_two_column_slide,
            self.LAYOUT_IMAGE_TEXT: self._build_image_text_slide,
            self.LAYOUT_CHART: self._build_chart_slide,
            self.LAYOUT_QUOTE: self._build_quote_slide,
            self.LAYOUT_CLOSING: self._build_closing_slide,
        }
        builder = builders.get(layout, self._build_content_slide)
        builder(slide, slide_data)

        # Speaker notes
        notes_text = slide_data.get("speaker_notes", "")
        if notes_text:
            notes_slide = slide.notes_slide
            notes_slide.notes_text_frame.text = notes_text

    # ==================================================================
    # SLIDE BUILDERS
    # ==================================================================

    def _build_title_slide(self, slide, data: dict) -> None:
        """Title slide with branded background, company name, title,
        subtitle, and logo.

        Visual layout:
        - Full-bleed primary-colour background rectangle.
        - Thin accent bar along the bottom edge.
        - Large bold title text left-aligned.
        - Optional subtitle below the title.
        - Company name in a muted colour at the lower-left.
        - Brand logo at the lower-right.
        """
        # Full-slide background with primary colour
        bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, self.SLIDE_WIDTH, self.SLIDE_HEIGHT
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = self.colors["primary"]
        bg.line.fill.background()

        # Accent bar at the very bottom of the slide
        bar_height = Inches(0.15)
        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            0,
            self.SLIDE_HEIGHT - bar_height,
            self.SLIDE_WIDTH,
            bar_height,
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = self.colors["accent"]
        bar.line.fill.background()

        # Title text
        title_text = data.get("title", "Untitled Presentation")
        title_box = slide.shapes.add_textbox(
            Inches(1), Inches(2.0), Inches(11.3), Inches(2.0)
        )
        tf = title_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(44)
        p.font.bold = True
        p.font.color.rgb = self.colors["white"]
        p.font.name = self.fonts["heading"]
        p.alignment = PP_ALIGN.LEFT

        # Subtitle (from "body" or "subtitle" key)
        subtitle = data.get("body", "") or data.get("subtitle", "")
        if subtitle:
            p2 = tf.add_paragraph()
            p2.text = subtitle
            p2.font.size = Pt(20)
            p2.font.color.rgb = self.colors["white"]
            p2.font.name = self.fonts["body"]
            p2.alignment = PP_ALIGN.LEFT
            p2.space_before = Pt(12)

        # Company name at the lower-left
        if self.company_name:
            comp_box = slide.shapes.add_textbox(
                Inches(1), Inches(6.2), Inches(5), Inches(0.5)
            )
            cp = comp_box.text_frame.paragraphs[0]
            cp.text = self.company_name
            cp.font.size = Pt(14)
            cp.font.color.rgb = RGBColor(200, 200, 220)
            cp.font.name = self.fonts["body"]

        # Logo in the lower-right corner
        self._add_logo(slide, Inches(10.5), Inches(5.8), max_height=Inches(0.9))

    # ------------------------------------------------------------------

    def _build_section_slide(self, slide, data: dict) -> None:
        """Section divider with a large title on a secondary-colour
        background.

        Visual layout:
        - Full-bleed secondary-colour background.
        - Narrow accent stripe on the left edge.
        - Large bold title centred vertically.
        - Optional subtitle text below the title.
        """
        # Secondary-colour background
        bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, self.SLIDE_WIDTH, self.SLIDE_HEIGHT
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = self.colors["secondary"]
        bg.line.fill.background()

        # Accent stripe on the left edge
        stripe = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.4), self.SLIDE_HEIGHT
        )
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = self.colors["accent"]
        stripe.line.fill.background()

        # Title
        title_box = slide.shapes.add_textbox(
            Inches(1.5), Inches(2.5), Inches(10), Inches(2.0)
        )
        tf = title_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = data.get("title", "")
        p.font.size = Pt(40)
        p.font.bold = True
        p.font.color.rgb = self.colors["white"]
        p.font.name = self.fonts["heading"]

        # Optional subtitle / body
        subtitle = data.get("body", "")
        if subtitle:
            p2 = tf.add_paragraph()
            p2.text = subtitle
            p2.font.size = Pt(18)
            p2.font.color.rgb = RGBColor(200, 200, 220)
            p2.font.name = self.fonts["body"]
            p2.space_before = Pt(16)

    # ------------------------------------------------------------------

    def _build_content_slide(self, slide, data: dict) -> None:
        """Standard content slide with a branded title bar, bullet points,
        and an optional data table.

        Visual layout:
        - White background.
        - Primary-colour title bar at the top with white title text.
        - Thin accent line beneath the title bar.
        - Bullet points or body paragraph in the content area.
        - Optional table below the bullets.
        - Small brand logo watermark in the bottom-right corner.
        """
        # White background
        bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, self.SLIDE_WIDTH, self.SLIDE_HEIGHT
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = self.colors["background"]
        bg.line.fill.background()

        # Primary-colour title bar
        title_bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, self.SLIDE_WIDTH, Inches(1.2)
        )
        title_bar.fill.solid()
        title_bar.fill.fore_color.rgb = self.colors["primary"]
        title_bar.line.fill.background()

        # Accent line under the title bar
        accent_line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, Inches(1.2), self.SLIDE_WIDTH, Inches(0.06)
        )
        accent_line.fill.solid()
        accent_line.fill.fore_color.rgb = self.colors["accent"]
        accent_line.line.fill.background()

        # Title text inside the bar
        title_box = slide.shapes.add_textbox(
            Inches(0.8), Inches(0.15), Inches(11), Inches(0.9)
        )
        tf = title_box.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = data.get("title", "")
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = self.colors["white"]
        p.font.name = self.fonts["heading"]

        # Content area coordinates
        content_top = Inches(1.6)
        content_left = Inches(0.8)
        content_width = Inches(11.7)
        content_height = Inches(5.0)

        # Bullets or body paragraph
        bullets = data.get("bullets", [])
        body = data.get("body", "")

        if bullets or body:
            body_box = slide.shapes.add_textbox(
                content_left, content_top, content_width, content_height
            )
            tf_body = body_box.text_frame
            tf_body.word_wrap = True

            if body and not bullets:
                # Plain paragraph text
                p_body = tf_body.paragraphs[0]
                p_body.text = body
                p_body.font.size = Pt(16)
                p_body.font.color.rgb = self.colors["text"]
                p_body.font.name = self.fonts["body"]
                p_body.line_spacing = Pt(24)
            else:
                # Bullet list
                for i, bullet in enumerate(bullets):
                    if i == 0:
                        p_bullet = tf_body.paragraphs[0]
                    else:
                        p_bullet = tf_body.add_paragraph()

                    # Sub-bullet detection: leading "- " indicates indent
                    if isinstance(bullet, str) and bullet.startswith("- "):
                        p_bullet.text = bullet[2:]
                        p_bullet.level = 1
                    else:
                        p_bullet.text = str(bullet)
                        p_bullet.level = 0

                    p_bullet.font.size = Pt(16) if p_bullet.level == 0 else Pt(14)
                    p_bullet.font.color.rgb = self.colors["text"]
                    p_bullet.font.name = self.fonts["body"]
                    p_bullet.space_before = Pt(8)
                    p_bullet.space_after = Pt(4)

        # Optional table below bullets
        table_data = data.get("table_data")
        if table_data and isinstance(table_data, list) and len(table_data) > 0:
            # Push the table below bullets if they exist
            table_top = (
                content_top
                if not bullets
                else content_top + Inches(len(bullets) * 0.4 + 0.5)
            )
            self._add_table(
                slide, table_data, content_left, table_top, content_width
            )

        # Logo watermark in the bottom-right corner
        self._add_logo(slide, Inches(11.8), Inches(6.8), max_height=Inches(0.45))

    # ------------------------------------------------------------------

    def _build_two_column_slide(self, slide, data: dict) -> None:
        """Two-column layout with a branded title bar and a thin vertical
        divider between the columns.

        Visual layout:
        - White background with standard title bar + accent line.
        - Left column at x=0.8, right column at x=7.0.
        - Each column has an optional heading (primary colour, bold) and
          bullet list or body text.
        - Thin light-grey divider line between the columns.
        - Brand logo in the bottom-right corner.
        """
        # Background
        bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, self.SLIDE_WIDTH, self.SLIDE_HEIGHT
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = self.colors["background"]
        bg.line.fill.background()

        # Title bar
        title_bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, self.SLIDE_WIDTH, Inches(1.2)
        )
        title_bar.fill.solid()
        title_bar.fill.fore_color.rgb = self.colors["primary"]
        title_bar.line.fill.background()

        # Accent line
        accent_line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, Inches(1.2), self.SLIDE_WIDTH, Inches(0.06)
        )
        accent_line.fill.solid()
        accent_line.fill.fore_color.rgb = self.colors["accent"]
        accent_line.line.fill.background()

        # Title text
        title_box = slide.shapes.add_textbox(
            Inches(0.8), Inches(0.15), Inches(11), Inches(0.9)
        )
        title_box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        tp = title_box.text_frame.paragraphs[0]
        tp.text = data.get("title", "")
        tp.font.size = Pt(28)
        tp.font.bold = True
        tp.font.color.rgb = self.colors["white"]
        tp.font.name = self.fonts["heading"]

        # Column dimensions
        columns = data.get("columns", [])
        col_width = Inches(5.5)
        col_top = Inches(1.6)
        col_height = Inches(5.0)

        for col_idx in range(2):
            col_left = Inches(0.8) if col_idx == 0 else Inches(7.0)
            col_data = columns[col_idx] if col_idx < len(columns) else {}

            col_box = slide.shapes.add_textbox(
                col_left, col_top, col_width, col_height
            )
            tf = col_box.text_frame
            tf.word_wrap = True

            # Column heading
            col_title = col_data.get("title", col_data.get("heading", ""))
            has_heading = False
            if col_title:
                has_heading = True
                p_head = tf.paragraphs[0]
                p_head.text = col_title
                p_head.font.size = Pt(20)
                p_head.font.bold = True
                p_head.font.color.rgb = self.colors["primary"]
                p_head.font.name = self.fonts["heading"]
                p_head.space_after = Pt(12)

            col_bullets = col_data.get("bullets", [])
            col_body = col_data.get("body", "")

            if col_bullets:
                for j, bullet in enumerate(col_bullets):
                    if j == 0 and not has_heading:
                        p_b = tf.paragraphs[0]
                    else:
                        p_b = tf.add_paragraph()
                    p_b.text = str(bullet)
                    p_b.font.size = Pt(14)
                    p_b.font.color.rgb = self.colors["text"]
                    p_b.font.name = self.fonts["body"]
                    p_b.space_before = Pt(6)
            elif col_body:
                if has_heading:
                    p_b = tf.add_paragraph()
                else:
                    p_b = tf.paragraphs[0]
                p_b.text = col_body
                p_b.font.size = Pt(14)
                p_b.font.color.rgb = self.colors["text"]
                p_b.font.name = self.fonts["body"]

        # Vertical divider line between columns
        divider = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(6.55),
            Inches(1.8),
            Inches(0.03),
            Inches(4.5),
        )
        divider.fill.solid()
        divider.fill.fore_color.rgb = self.colors["light_gray"]
        divider.line.fill.background()

        # Logo
        self._add_logo(slide, Inches(11.8), Inches(6.8), max_height=Inches(0.45))

    # ------------------------------------------------------------------

    def _build_image_text_slide(self, slide, data: dict) -> None:
        """Image on the left (or a styled placeholder) with text content on
        the right.

        Visual layout:
        - White background with standard title bar + accent line.
        - Left half: image or a light-grey placeholder rectangle with a
          label taken from ``suggested_visual``.
        - Right half: bullets or body text.
        - Brand logo in the bottom-right corner.
        """
        # Background
        bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, self.SLIDE_WIDTH, self.SLIDE_HEIGHT
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = self.colors["background"]
        bg.line.fill.background()

        # Title bar
        title_bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, self.SLIDE_WIDTH, Inches(1.2)
        )
        title_bar.fill.solid()
        title_bar.fill.fore_color.rgb = self.colors["primary"]
        title_bar.line.fill.background()

        # Accent line
        accent_line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, Inches(1.2), self.SLIDE_WIDTH, Inches(0.06)
        )
        accent_line.fill.solid()
        accent_line.fill.fore_color.rgb = self.colors["accent"]
        accent_line.line.fill.background()

        # Title text
        title_box = slide.shapes.add_textbox(
            Inches(0.8), Inches(0.15), Inches(11), Inches(0.9)
        )
        title_box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        tp = title_box.text_frame.paragraphs[0]
        tp.text = data.get("title", "")
        tp.font.size = Pt(28)
        tp.font.bold = True
        tp.font.color.rgb = self.colors["white"]
        tp.font.name = self.fonts["heading"]

        # Image area (left half)
        img_left = Inches(0.8)
        img_top = Inches(1.6)
        img_width = Inches(5.5)
        img_height = Inches(5.0)

        image_path = data.get("image_path")
        if image_path and Path(image_path).exists():
            try:
                slide.shapes.add_picture(
                    image_path, img_left, img_top, img_width, img_height
                )
            except Exception as exc:
                logger.debug("Could not insert image '%s': %s", image_path, exc)
                self._add_image_placeholder(
                    slide,
                    img_left,
                    img_top,
                    img_width,
                    img_height,
                    data.get("suggested_visual", "Visual"),
                )
        else:
            self._add_image_placeholder(
                slide,
                img_left,
                img_top,
                img_width,
                img_height,
                data.get("suggested_visual", "Visual"),
            )

        # Text content on the right
        text_box = slide.shapes.add_textbox(
            Inches(7.0), Inches(1.6), Inches(5.5), Inches(5.0)
        )
        tf = text_box.text_frame
        tf.word_wrap = True

        bullets = data.get("bullets", [])
        body = data.get("body", "")
        if bullets:
            for i, bullet in enumerate(bullets):
                p_b = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                p_b.text = str(bullet)
                p_b.font.size = Pt(15)
                p_b.font.color.rgb = self.colors["text"]
                p_b.font.name = self.fonts["body"]
                p_b.space_before = Pt(8)
        elif body:
            p_b = tf.paragraphs[0]
            p_b.text = body
            p_b.font.size = Pt(15)
            p_b.font.color.rgb = self.colors["text"]
            p_b.font.name = self.fonts["body"]
            p_b.line_spacing = Pt(22)

        # Logo
        self._add_logo(slide, Inches(11.8), Inches(6.8), max_height=Inches(0.45))

    # ------------------------------------------------------------------

    def _build_chart_slide(self, slide, data: dict) -> None:
        """Slide with a branded title bar and an embedded chart or table.

        Supports bar, column, line, and pie charts via the ``chart_data``
        key.  Falls back to a table if ``table_data`` is provided, or
        bullets as a last resort.

        Visual layout:
        - White background with standard title bar + accent line.
        - Chart centred in the content area.
        - Brand logo in the bottom-right corner.
        """
        # Background
        bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, self.SLIDE_WIDTH, self.SLIDE_HEIGHT
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = self.colors["background"]
        bg.line.fill.background()

        # Title bar
        title_bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, self.SLIDE_WIDTH, Inches(1.2)
        )
        title_bar.fill.solid()
        title_bar.fill.fore_color.rgb = self.colors["primary"]
        title_bar.line.fill.background()

        # Accent line
        accent_line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, Inches(1.2), self.SLIDE_WIDTH, Inches(0.06)
        )
        accent_line.fill.solid()
        accent_line.fill.fore_color.rgb = self.colors["accent"]
        accent_line.line.fill.background()

        # Title text
        title_box = slide.shapes.add_textbox(
            Inches(0.8), Inches(0.15), Inches(11), Inches(0.9)
        )
        title_box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        tp = title_box.text_frame.paragraphs[0]
        tp.text = data.get("title", "")
        tp.font.size = Pt(28)
        tp.font.bold = True
        tp.font.color.rgb = self.colors["white"]
        tp.font.name = self.fonts["heading"]

        # Determine what data to render
        chart_data_input = data.get("chart_data", {})
        table_data = data.get("table_data")

        if chart_data_input:
            self._add_chart(slide, chart_data_input)
        elif table_data:
            self._add_table(
                slide, table_data, Inches(0.8), Inches(1.6), Inches(11.7)
            )
        else:
            # Last resort: render bullets if available
            bullets = data.get("bullets", [])
            if bullets:
                body_box = slide.shapes.add_textbox(
                    Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.0)
                )
                tf = body_box.text_frame
                tf.word_wrap = True
                for i, bullet in enumerate(bullets):
                    p_b = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                    p_b.text = str(bullet)
                    p_b.font.size = Pt(16)
                    p_b.font.color.rgb = self.colors["text"]
                    p_b.font.name = self.fonts["body"]
                    p_b.space_before = Pt(8)

        # Logo
        self._add_logo(slide, Inches(11.8), Inches(6.8), max_height=Inches(0.45))

    # ------------------------------------------------------------------

    def _build_quote_slide(self, slide, data: dict) -> None:
        """Large quote with attribution on a branded primary-colour
        background.

        Visual layout:
        - Full-bleed primary-colour background.
        - Oversized open-quote character in the accent colour.
        - Italic quote text in white.
        - Em-dash-prefixed attribution in a muted colour.
        - Brand logo in the bottom-right corner.
        """
        # Primary background
        bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, self.SLIDE_WIDTH, self.SLIDE_HEIGHT
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = self.colors["primary"]
        bg.line.fill.background()

        # Large open-quote character
        quote_mark = slide.shapes.add_textbox(
            Inches(1), Inches(1.0), Inches(2), Inches(2)
        )
        qm = quote_mark.text_frame.paragraphs[0]
        qm.text = "\u201C"  # left double quotation mark
        qm.font.size = Pt(120)
        qm.font.color.rgb = self.colors["accent"]
        qm.font.name = self.fonts["heading"]

        # Quote text
        quote_text = data.get("quote", data.get("body", data.get("title", "")))
        quote_box = slide.shapes.add_textbox(
            Inches(1.5), Inches(2.2), Inches(10), Inches(3.0)
        )
        tf = quote_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = quote_text
        p.font.size = Pt(28)
        p.font.italic = True
        p.font.color.rgb = self.colors["white"]
        p.font.name = self.fonts["heading"]
        p.line_spacing = Pt(40)

        # Attribution line
        attribution = data.get("attribution", "")
        if attribution:
            attr_box = slide.shapes.add_textbox(
                Inches(1.5), Inches(5.5), Inches(10), Inches(0.6)
            )
            ap = attr_box.text_frame.paragraphs[0]
            ap.text = f"\u2014 {attribution}"  # em dash + attribution
            ap.font.size = Pt(18)
            ap.font.color.rgb = RGBColor(200, 200, 220)
            ap.font.name = self.fonts["body"]

        # Logo
        self._add_logo(slide, Inches(11.0), Inches(6.5), max_height=Inches(0.5))

    # ------------------------------------------------------------------

    def _build_closing_slide(self, slide, data: dict) -> None:
        """Closing / thank-you slide with branded background and centred
        text.

        Visual layout:
        - Full-bleed primary-colour background.
        - Thin accent bar along the bottom.
        - Large centred title ("Thank You" by default).
        - Optional subtitle / body below.
        - Optional bullet list for contact info.
        - Centred brand logo above the bottom bar.
        """
        # Primary background
        bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, self.SLIDE_WIDTH, self.SLIDE_HEIGHT
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = self.colors["primary"]
        bg.line.fill.background()

        # Accent bar at the bottom
        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            0,
            self.SLIDE_HEIGHT - Inches(0.15),
            self.SLIDE_WIDTH,
            Inches(0.15),
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = self.colors["accent"]
        bar.line.fill.background()

        # Title
        title_text = data.get("title", "Thank You")
        title_box = slide.shapes.add_textbox(
            Inches(1), Inches(2.5), Inches(11.3), Inches(1.5)
        )
        tf = title_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(44)
        p.font.bold = True
        p.font.color.rgb = self.colors["white"]
        p.font.name = self.fonts["heading"]
        p.alignment = PP_ALIGN.CENTER

        # Subtitle / body
        body = data.get("body", "")
        if body:
            p2 = tf.add_paragraph()
            p2.text = body
            p2.font.size = Pt(20)
            p2.font.color.rgb = RGBColor(200, 200, 220)
            p2.font.name = self.fonts["body"]
            p2.alignment = PP_ALIGN.CENTER
            p2.space_before = Pt(16)

        # Contact info or closing bullets
        bullets = data.get("bullets", [])
        if bullets:
            info_box = slide.shapes.add_textbox(
                Inches(3), Inches(4.5), Inches(7), Inches(2)
            )
            tf2 = info_box.text_frame
            tf2.word_wrap = True
            for i, bullet in enumerate(bullets):
                p_b = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
                p_b.text = str(bullet)
                p_b.font.size = Pt(16)
                p_b.font.color.rgb = RGBColor(200, 200, 220)
                p_b.font.name = self.fonts["body"]
                p_b.alignment = PP_ALIGN.CENTER
                p_b.space_before = Pt(4)

        # Large centred logo
        self._add_logo(slide, Inches(5.5), Inches(5.5), max_height=Inches(1.2))

    # ==================================================================
    # HELPER METHODS
    # ==================================================================

    def _add_logo(self, slide, left, top, max_height=Inches(0.6)) -> None:
        """Add the brand logo to the slide if a logo file is available.

        Silently does nothing when no logo has been configured or when the
        file cannot be read.
        """
        if not self.logo_path or not Path(self.logo_path).exists():
            return
        try:
            slide.shapes.add_picture(self.logo_path, left, top, height=max_height)
        except Exception as exc:
            logger.debug("Could not add logo to slide: %s", exc)

    def _add_image_placeholder(
        self,
        slide,
        left,
        top,
        width,
        height,
        label: str = "",
    ) -> None:
        """Add a styled placeholder rectangle where a real image would go.

        The placeholder is a light-grey rectangle with a thin border and a
        centred label such as ``[Infographic]`` or ``[Photo]``.
        """
        placeholder = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, left, top, width, height
        )
        placeholder.fill.solid()
        placeholder.fill.fore_color.rgb = self.colors["light_gray"]
        placeholder.line.color.rgb = RGBColor(200, 200, 200)
        placeholder.line.width = Pt(1)

        # Centred label inside the placeholder
        label_box = slide.shapes.add_textbox(
            left, top + height // 2 - Inches(0.3), width, Inches(0.6)
        )
        tf = label_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f"[{label}]" if label else "[Image]"
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(150, 150, 150)
        p.font.name = self.fonts["body"]
        p.alignment = PP_ALIGN.CENTER

    def _add_table(
        self,
        slide,
        table_data: list[list],
        left,
        top,
        width,
    ) -> None:
        """Add a formatted data table to the slide.

        The first row of ``table_data`` is styled as a header row (primary-
        colour background, white bold text).  Alternating data rows use a
        light-grey zebra stripe.

        Args:
            slide: The python-pptx Slide to add the table to.
            table_data: 2-D list of cell values.  First row = headers.
            left: Left position of the table (EMU or Inches).
            top: Top position of the table (EMU or Inches).
            width: Total table width (EMU or Inches).
        """
        if not table_data or not table_data[0]:
            return

        rows = len(table_data)
        cols = max(len(row) for row in table_data)

        # Cap table height so it does not overflow the slide
        table_height = Inches(min(rows * 0.45, 4.5))

        table_shape = slide.shapes.add_table(
            rows, cols, left, top, width, table_height
        )
        table = table_shape.table

        for row_idx, row_data in enumerate(table_data):
            for col_idx in range(cols):
                cell = table.cell(row_idx, col_idx)
                cell.text = (
                    str(row_data[col_idx]) if col_idx < len(row_data) else ""
                )

                # Style every paragraph in the cell
                for paragraph in cell.text_frame.paragraphs:
                    paragraph.font.size = Pt(12)
                    paragraph.font.name = self.fonts["body"]

                    if row_idx == 0:
                        # Header row
                        paragraph.font.bold = True
                        paragraph.font.color.rgb = self.colors["white"]
                    else:
                        paragraph.font.color.rgb = self.colors["text"]

                # Cell background
                if row_idx == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = self.colors["primary"]
                elif row_idx % 2 == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = self.colors["light_gray"]

    def _add_chart(self, slide, chart_data_input: dict) -> None:
        """Add an embedded chart to the slide.

        Supports four chart types: ``bar``, ``column``, ``line``, and
        ``pie``.  Data may be supplied in two formats:

        1. **Explicit** -- ``categories`` (list of labels) and ``series``
           (list of ``{name, values}`` dicts).
        2. **Table** -- ``data`` as a list of lists where the first row
           contains headers and subsequent rows contain a category label
           followed by numeric values.

        Args:
            slide: The python-pptx Slide to add the chart to.
            chart_data_input: Dict describing the chart type and data.
        """
        from pptx.chart.data import CategoryChartData

        chart_type_map = {
            "bar": XL_CHART_TYPE.BAR_CLUSTERED,
            "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
            "line": XL_CHART_TYPE.LINE,
            "pie": XL_CHART_TYPE.PIE,
        }

        chart_type_str = chart_data_input.get("type", "column")
        chart_type = chart_type_map.get(chart_type_str, XL_CHART_TYPE.COLUMN_CLUSTERED)

        categories = chart_data_input.get("categories", [])
        series_list = chart_data_input.get("series", [])

        # Alternative: convert table-format ``data`` into categories + series
        if not categories and "data" in chart_data_input:
            raw = chart_data_input["data"]
            if raw and len(raw) > 1:
                categories = [str(row[0]) for row in raw[1:]]
                headers = raw[0][1:]
                series_list = []
                for col_idx, header in enumerate(headers):
                    values: list[float] = []
                    for row in raw[1:]:
                        val = row[col_idx + 1] if col_idx + 1 < len(row) else 0
                        try:
                            values.append(float(val))
                        except (ValueError, TypeError):
                            values.append(0)
                    series_list.append({"name": str(header), "values": values})

        if not categories or not series_list:
            logger.warning("Skipping chart: no categories or series data provided.")
            return

        chart_d = CategoryChartData()
        chart_d.categories = categories
        for s in series_list:
            chart_d.add_series(s.get("name", "Series"), s.get("values", []))

        chart_left = Inches(1.0)
        chart_top = Inches(1.8)
        chart_width = Inches(11.0)
        chart_height = Inches(5.0)

        chart_frame = slide.shapes.add_chart(
            chart_type, chart_left, chart_top, chart_width, chart_height, chart_d
        )

        # Basic chart styling
        chart = chart_frame.chart
        chart.has_legend = len(series_list) > 1
        if chart.has_legend:
            chart.legend.include_in_layout = False


# ======================================================================
# Template Importer
# ======================================================================

class TemplateImporter:
    """Import existing branded PPTX files and extract their design DNA.

    The importer uses ``PPTXParser`` to analyse the template structure,
    copies the file into ``brand_assets/templates/pptx/``, and persists a
    ``Template`` record in the database with the extracted colour scheme,
    font theme, and layout information.
    """

    def __init__(self):
        from app.ingestion.pptx_parser import PPTXParser

        self.parser = PPTXParser()

    def import_template(
        self,
        pptx_path: str,
        template_name: str = "",
        description: str = "",
    ) -> dict:
        """Import a PPTX template and extract its brand DNA.

        Workflow:
        1. Parse the PPTX for layout names, colour scheme, and font theme.
        2. Detect recurring small-image positions (probable logo placement).
        3. Copy the file into ``brand_assets/templates/pptx/``.
        4. Create a ``Template`` database record.

        Args:
            pptx_path: Path to the source PPTX file.
            template_name: Human-readable name for the template.  Defaults
                to a title-cased version of the filename.
            description: Optional description.

        Returns:
            Dict with keys:

            - **success** (bool)
            - **template_id** (int) -- database primary key (on success)
            - **template_dna** (dict) -- extracted design information
            - **stored_path** (str) -- destination file path
            - **error** (str | None)
        """
        from app.database.models import get_session, Template

        path = Path(pptx_path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {pptx_path}"}

        # ---- Extract template DNA ----
        try:
            template_info = self.parser.extract_template_info(pptx_path)
            parse_data = self.parser.parse(pptx_path)
        except Exception as exc:
            return {"success": False, "error": f"Failed to parse PPTX: {exc}"}

        # Detect logo position from recurring small images
        logo_info = self._detect_logo_position(parse_data.get("slides", []))

        template_dna = {
            "layouts": template_info.get("layouts", []),
            "color_scheme": template_info.get("color_scheme", {}),
            "font_theme": template_info.get("font_theme", {}),
            "slide_dimensions": {
                "width": parse_data.get("template_properties", {}).get(
                    "slide_width", 13.33
                ),
                "height": parse_data.get("template_properties", {}).get(
                    "slide_height", 7.5
                ),
            },
            "logo_position": logo_info,
            "slide_count": len(parse_data.get("slides", [])),
        }

        # ---- Copy template file to brand_assets/templates/pptx/ ----
        dest_dir = TEMPLATES_DIR / "pptx"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / path.name

        # Handle name collisions by appending a counter
        if dest_path.exists():
            stem = path.stem
            suffix = path.suffix
            counter = 1
            while dest_path.exists():
                dest_path = dest_dir / f"{stem}_{counter}{suffix}"
                counter += 1

        shutil.copy2(pptx_path, dest_path)

        # ---- Persist in database ----
        if not template_name:
            template_name = path.stem.replace("_", " ").replace("-", " ").title()

        session = get_session()
        try:
            template = Template(
                name=template_name,
                template_type="pptx",
                file_path=str(dest_path),
                description=description or f"Imported from {path.name}",
                frozen_zones_json=json.dumps(
                    template_dna.get("color_scheme", {})
                ),
                editable_zones_json=json.dumps(
                    template_dna.get("layouts", [])
                ),
            )
            session.add(template)
            session.commit()
            template_id = template.id
        except Exception as exc:
            session.rollback()
            logger.error("Failed to save template to database: %s", exc)
            return {"success": False, "error": f"Database error: {exc}"}
        finally:
            session.close()

        logger.info(
            "Imported template '%s' (id=%d) from %s -> %s",
            template_name,
            template_id,
            pptx_path,
            dest_path,
        )

        return {
            "success": True,
            "template_id": template_id,
            "template_dna": template_dna,
            "stored_path": str(dest_path),
            "error": None,
        }

    def _detect_logo_position(self, slides: list[dict]) -> dict:
        """Analyse slides to find recurring small-image positions (likely logos).

        Scans every shape across all slides looking for images whose
        dimensions fall within a "logo-sized" range (0.3-2.5 inches wide,
        0.3-2.0 inches tall).  The returned position is the average of all
        qualifying shapes, providing a best guess for the template's
        preferred logo placement.

        Args:
            slides: List of parsed slide dicts from ``PPTXParser.parse()``.

        Returns:
            Dict with ``left``, ``top``, ``width``, ``height`` in inches.
            Falls back to a sensible bottom-right default when no candidate
            shapes are found.
        """
        positions: list[dict] = []
        for slide_data in slides:
            for shape in slide_data.get("shapes", []):
                pos = shape.get("position", {})
                width = pos.get("width") or 0
                height = pos.get("height") or 0
                # Small shapes in corners are likely logos
                if 0.3 < width < 2.5 and 0.3 < height < 2.0:
                    positions.append(
                        {
                            "left": pos.get("left", 0),
                            "top": pos.get("top", 0),
                            "width": width,
                            "height": height,
                        }
                    )

        if not positions:
            # Default: bottom-right corner
            return {"left": 11.8, "top": 6.8, "width": 1.0, "height": 0.5}

        # Return the averaged position across all candidate shapes
        count = len(positions)
        avg = {
            "left": round(sum(p["left"] for p in positions) / count, 2),
            "top": round(sum(p["top"] for p in positions) / count, 2),
            "width": round(sum(p["width"] for p in positions) / count, 2),
            "height": round(sum(p["height"] for p in positions) / count, 2),
        }
        return avg
