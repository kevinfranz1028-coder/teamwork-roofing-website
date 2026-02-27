"""
Brand Intelligence Content Hub - Template Engine

Opens corporate PPTX/DOCX templates and injects content into existing
placeholders, preserving slide masters, colour themes, font themes,
logos, and headers/footers.  Falls back gracefully when templates are
missing so the from-scratch generators still work.

Usage:
    from app.brand.template_engine import PptxTemplateEngine, DocxTemplateEngine

    engine = PptxTemplateEngine()
    if engine.available:
        prs = engine.create_from_template(slides_data, title="My Deck")
"""

import glob
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.chart import XL_CHART_TYPE
from pptx.oxml.ns import qn

from docx import Document

from app.config import TEMPLATES_DIR

logger = logging.getLogger(__name__)


# ======================================================================
# PPTX Template Engine
# ======================================================================

class PptxTemplateEngine:
    """Opens a corporate PPTX template, removes sample slides, and
    creates new slides using the template's layouts and masters.
    """

    # Map generator layout types -> template layout name priority lists
    LAYOUT_MAP: dict[str, list[str]] = {
        "title":           ["01 Cover", "01 Cover CoBrand"],
        "section_divider": ["Chapter A", "Chapter B"],
        "content":         ["4_Regular Slide", "7_Regular Slide"],
        "two_column":      ["8_Regular Slide", "4_Regular Slide"],
        "image_text":      ["9_Regular Slide", "4_Regular Slide"],
        "chart_data":      ["10_Regular Slide", "4_Regular Slide"],
        "quote_callout":   ["11_Regular Slide", "Chapter B"],
        "closing":         ["Back Cover", "01 Cover"],
    }

    def __init__(self, template_path: Optional[str] = None):
        """Initialise the engine.

        Args:
            template_path: Explicit path to a PPTX template.  When *None*
                the engine auto-discovers the default template in
                ``TEMPLATES_DIR``.
        """
        self.template_path: Optional[Path] = None
        self.available: bool = False
        self._layout_catalog: dict[str, list[int]] = {}  # layout_name -> [placeholder indices]

        if template_path:
            p = Path(template_path)
            if p.exists() and p.suffix.lower() == ".pptx":
                self.template_path = p
        else:
            self.template_path = self._find_default_template()

        if self.template_path:
            try:
                self._analyze_template()
                self.available = True
                logger.info(
                    "PptxTemplateEngine ready: %s (%d layouts catalogued)",
                    self.template_path.name,
                    len(self._layout_catalog),
                )
            except Exception as exc:
                logger.warning("Failed to analyse PPTX template: %s", exc)
                self.available = False

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _find_default_template(self) -> Optional[Path]:
        """Glob-search for ``GMT_PPT_Template_Global*.pptx``.

        Prefers the base file (no timestamp suffix) over timestamped copies.
        """
        if not TEMPLATES_DIR.exists():
            return None

        candidates = sorted(TEMPLATES_DIR.glob("GMT_PPT_Template_Global*.pptx"))
        if not candidates:
            return None

        # Prefer the shortest name (base file without timestamp suffix)
        candidates.sort(key=lambda p: len(p.name))
        return candidates[0]

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def _analyze_template(self) -> None:
        """Open the template and catalogue layout names with their
        placeholder indices.
        """
        prs = Presentation(str(self.template_path))
        self._layout_catalog = {}

        for slide_master in prs.slide_masters:
            for layout in slide_master.slide_layouts:
                name = layout.name
                indices = []
                for ph in layout.placeholders:
                    indices.append(ph.placeholder_format.idx)
                self._layout_catalog[name] = sorted(indices)

        logger.debug("Template layouts: %s", list(self._layout_catalog.keys()))

    # ------------------------------------------------------------------
    # Slide removal
    # ------------------------------------------------------------------

    @staticmethod
    def _remove_all_slides(prs: Presentation) -> None:
        """Remove all sample slides from the presentation while
        preserving slide masters and layouts.

        Works by removing ``sldId`` elements from the presentation XML
        and dropping the corresponding relationship entries.
        """
        # prs.element is the <p:presentation> CT_Presentation XML element
        prs_element = prs.element

        # Collect rIds of all slides
        sldIdLst = prs_element.find(qn("p:sldIdLst"))
        if sldIdLst is None:
            return

        slide_ids = list(sldIdLst)
        for sldId in slide_ids:
            rId = sldId.get(qn("r:id"))
            if rId:
                try:
                    prs.part.drop_rel(rId)
                except Exception:
                    pass  # Relationship may already be removed
            sldIdLst.remove(sldId)

        logger.debug("Removed %d sample slides from template", len(slide_ids))

    # ------------------------------------------------------------------
    # Layout resolution
    # ------------------------------------------------------------------

    def _resolve_layout(self, prs: Presentation, layout_type: str):
        """Find the best matching slide layout in *prs* for the given
        generator layout type.

        Matching is whitespace-insensitive to handle template layout names
        that may have trailing spaces.

        Returns:
            A SlideLayout object, or None if nothing matches.
        """
        priority = self.LAYOUT_MAP.get(layout_type, ["4_Regular Slide"])

        for target_name in priority:
            target_stripped = target_name.strip()
            for master in prs.slide_masters:
                for layout in master.slide_layouts:
                    if layout.name.strip() == target_stripped:
                        return layout

        # Ultimate fallback: first available layout
        for master in prs.slide_masters:
            if master.slide_layouts:
                return master.slide_layouts[0]

        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_from_template(
        self,
        slides_data: list[dict],
        title: str = "Presentation",
    ) -> Presentation:
        """Open the template, remove sample slides, and create new slides
        by injecting content into template placeholders.

        Args:
            slides_data: List of slide dicts (same format as the fallback
                generator).
            title: Presentation title for metadata.

        Returns:
            A python-pptx Presentation object (not yet saved).

        Raises:
            RuntimeError: If the template is not available.
        """
        if not self.available or not self.template_path:
            raise RuntimeError("PPTX template not available")

        prs = Presentation(str(self.template_path))
        self._remove_all_slides(prs)

        for slide_data in slides_data:
            layout_type = slide_data.get("layout", "content")
            layout = self._resolve_layout(prs, layout_type)
            if layout is None:
                logger.warning("No layout found for type '%s', skipping", layout_type)
                continue

            slide = prs.slides.add_slide(layout)
            self._inject_content(slide, slide_data, layout_type)

            # Speaker notes
            notes_text = slide_data.get("speaker_notes", "")
            if notes_text:
                notes_slide = slide.notes_slide
                notes_slide.notes_text_frame.text = notes_text

        return prs

    # ------------------------------------------------------------------
    # Content injection dispatcher
    # ------------------------------------------------------------------

    def _inject_content(self, slide, slide_data: dict, layout_type: str) -> None:
        """Dispatch to the appropriate per-type injector."""
        injectors = {
            "title":           self._inject_title_slide,
            "section_divider": self._inject_section_slide,
            "content":         self._inject_content_slide,
            "two_column":      self._inject_two_column_slide,
            "image_text":      self._inject_image_text_slide,
            "chart_data":      self._inject_chart_slide,
            "quote_callout":   self._inject_quote_slide,
            "closing":         self._inject_closing_slide,
        }
        injector = injectors.get(layout_type, self._inject_content_slide)
        injector(slide, slide_data)

    # ------------------------------------------------------------------
    # Per-type injectors
    # ------------------------------------------------------------------

    def _inject_title_slide(self, slide, data: dict) -> None:
        """Inject content into a Cover layout.

        Looks for placeholder idx 0 (title) and idx 1 (subtitle).
        """
        title_text = data.get("title", "Untitled Presentation")
        subtitle_text = data.get("body", "") or data.get("subtitle", "")

        self._set_placeholder_text(slide, 0, title_text)
        if subtitle_text:
            self._set_placeholder_text(slide, 1, subtitle_text)

    def _inject_section_slide(self, slide, data: dict) -> None:
        """Inject content into a Chapter/section divider layout."""
        title_text = data.get("title", "")
        subtitle_text = data.get("body", "") or data.get("subtitle", "")

        self._set_placeholder_text(slide, 0, title_text)
        if subtitle_text:
            self._set_placeholder_text(slide, 1, subtitle_text)

    def _inject_content_slide(self, slide, data: dict) -> None:
        """Inject content into a regular content layout.

        Fills idx 0 with title.  Finds the first BODY placeholder
        (idx 1, or another body-type index) for bullets or body text.
        """
        title_text = data.get("title", "")
        self._set_placeholder_text(slide, 0, title_text)

        # Build body content from bullets or body text
        bullets = data.get("bullets", [])
        body = data.get("body", "")
        body_idx = self._first_body_placeholder(slide)

        if body_idx is not None:
            if bullets:
                self._set_placeholder_bullets(slide, body_idx, bullets)
            elif body:
                self._set_placeholder_text(slide, body_idx, body)

        # If table_data present, add as a shape
        table_data = data.get("table_data")
        if table_data:
            self._add_table_shape(slide, table_data)

    def _inject_two_column_slide(self, slide, data: dict) -> None:
        """Inject content into a two-column layout.

        Uses idx 0 for title (if available), then tries to find two BODY
        placeholders for left/right columns.  Falls back to a single body
        placeholder with combined content.
        """
        title_text = data.get("title", "")
        self._set_placeholder_text(slide, 0, title_text)

        columns = data.get("columns", [])

        # Find all body-type placeholders (exclude title, date, slide number)
        body_phs = self._find_body_placeholders(slide)

        if len(columns) >= 2:
            left_text = self._column_to_text(columns[0])
            right_text = self._column_to_text(columns[1])

            if len(body_phs) >= 2:
                self._set_placeholder_text(slide, body_phs[0], left_text)
                self._set_placeholder_text(slide, body_phs[1], right_text)
            elif body_phs:
                combined = left_text + "\n\n" + right_text
                self._set_placeholder_text(slide, body_phs[0], combined)
        elif columns:
            text = self._column_to_text(columns[0])
            if body_phs:
                self._set_placeholder_text(slide, body_phs[0], text)

    def _inject_image_text_slide(self, slide, data: dict) -> None:
        """Inject content into an image+text layout.

        Title in idx 0, body/bullets in the first body placeholder.
        """
        title_text = data.get("title", "")
        self._set_placeholder_text(slide, 0, title_text)

        bullets = data.get("bullets", [])
        body = data.get("body", "")
        body_idx = self._first_body_placeholder(slide)
        if body_idx is not None:
            if bullets:
                self._set_placeholder_bullets(slide, body_idx, bullets)
            elif body:
                self._set_placeholder_text(slide, body_idx, body)

        # Insert image if path provided and a picture placeholder exists
        image_path = data.get("image_path", "")
        if image_path:
            self._insert_image(slide, image_path)

    def _inject_chart_slide(self, slide, data: dict) -> None:
        """Inject content into a chart layout.

        Title in idx 0.  Chart data is added as a shape since templates
        don't have native chart placeholders.
        """
        title_text = data.get("title", "")
        self._set_placeholder_text(slide, 0, title_text)

        chart_data = data.get("chart_data")
        if chart_data:
            self._add_chart_shape(slide, chart_data)

        # Also handle bullets/body in the first body placeholder
        bullets = data.get("bullets", [])
        body = data.get("body", "")
        body_idx = self._first_body_placeholder(slide)
        if body_idx is not None:
            if bullets:
                self._set_placeholder_bullets(slide, body_idx, bullets)
            elif body:
                self._set_placeholder_text(slide, body_idx, body)

    def _inject_quote_slide(self, slide, data: dict) -> None:
        """Inject a quote into the slide.

        Puts title in idx 0, quote text in the first body placeholder.
        """
        quote = data.get("quote", "")
        attribution = data.get("attribution", "")
        title_text = data.get("title", "")

        if title_text:
            self._set_placeholder_text(slide, 0, title_text)

        quote_display = f'"{quote}"'
        if attribution:
            quote_display += f"\n\n\u2014 {attribution}"

        # Find the first body placeholder for the quote text
        body_idx = self._first_body_placeholder(slide)
        if body_idx is not None:
            self._set_placeholder_text(slide, body_idx, quote_display)
        elif not title_text:
            # No body placeholder and no title set — use title placeholder
            self._set_placeholder_text(slide, 0, quote_display)

    def _inject_closing_slide(self, slide, data: dict) -> None:
        """Inject content into a closing/back-cover layout."""
        title_text = data.get("title", "Thank You")
        subtitle_text = data.get("body", "") or data.get("subtitle", "")

        self._set_placeholder_text(slide, 0, title_text)
        if subtitle_text:
            self._set_placeholder_text(slide, 1, subtitle_text)

    # ------------------------------------------------------------------
    # Placeholder helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_placeholder(slide, idx: int):
        """Find a placeholder by its ``placeholder_format.idx``.

        Returns the placeholder Shape or None.
        """
        for ph in slide.placeholders:
            if ph.placeholder_format.idx == idx:
                return ph
        return None

    @staticmethod
    def _find_body_placeholders(slide) -> list[int]:
        """Return sorted list of BODY placeholder indices (excluding title,
        date, slide number, and picture placeholders).

        BODY type = 2, TITLE = 1 / 15, DATE = 16, SLIDE_NUMBER = 13,
        PICTURE = 18.
        """
        skip_types = {1, 13, 15, 16, 18}  # TITLE, SLIDE_NUMBER, CENTER_TITLE, DATE, PICTURE
        result = []
        for ph in slide.placeholders:
            pf = ph.placeholder_format
            ptype = pf.type
            # ptype is an enum; compare its int value
            try:
                type_val = int(ptype)
            except (TypeError, ValueError):
                type_val = -1
            if type_val not in skip_types and pf.idx != 0:
                result.append(pf.idx)
        return sorted(result)

    @staticmethod
    def _first_body_placeholder(slide) -> Optional[int]:
        """Return the index of the first body-type placeholder, or None.

        Prefers idx 1, then the lowest body-type index.
        """
        skip_types = {1, 13, 15, 16, 18}
        body_indices = []
        for ph in slide.placeholders:
            pf = ph.placeholder_format
            try:
                type_val = int(pf.type)
            except (TypeError, ValueError):
                type_val = -1
            if type_val not in skip_types and pf.idx != 0:
                body_indices.append(pf.idx)
        if not body_indices:
            return None
        # Prefer idx 1 if available
        if 1 in body_indices:
            return 1
        return min(body_indices)

    @staticmethod
    def _set_placeholder_text(slide, idx: int, text: str) -> bool:
        """Set the text of a placeholder by index.

        Preserves the first run's formatting from the template by
        clearing only the text, not the run formatting.

        Returns True if the placeholder was found and updated.
        """
        for ph in slide.placeholders:
            if ph.placeholder_format.idx == idx:
                tf = ph.text_frame
                # Clear existing text but keep formatting
                if tf.paragraphs:
                    first_para = tf.paragraphs[0]
                    # Preserve formatting from the first run if it exists
                    if first_para.runs:
                        template_run = first_para.runs[0]
                        first_para.clear()
                        run = first_para.add_run()
                        run.text = text
                        # Copy font properties from template run
                        if template_run.font.name:
                            run.font.name = template_run.font.name
                        if template_run.font.size:
                            run.font.size = template_run.font.size
                        if template_run.font.bold is not None:
                            run.font.bold = template_run.font.bold
                        if template_run.font.color and template_run.font.color.rgb:
                            run.font.color.rgb = template_run.font.color.rgb
                    else:
                        first_para.text = text
                else:
                    tf.text = text
                return True
        return False

    @staticmethod
    def _set_placeholder_bullets(slide, idx: int, bullets: list[str]) -> bool:
        """Set bullet content in a placeholder by index.

        Each bullet becomes a separate paragraph.  Sub-bullets (prefixed
        with ``"- "``) are indented to level 1.

        Returns True if the placeholder was found and updated.
        """
        for ph in slide.placeholders:
            if ph.placeholder_format.idx == idx:
                tf = ph.text_frame

                # Capture formatting from template's first paragraph/run
                template_font_name = None
                template_font_size = None
                if tf.paragraphs and tf.paragraphs[0].runs:
                    trun = tf.paragraphs[0].runs[0]
                    template_font_name = trun.font.name
                    template_font_size = trun.font.size

                # Clear existing content
                tf.clear()

                for i, bullet in enumerate(bullets):
                    if i == 0:
                        p = tf.paragraphs[0]
                    else:
                        p = tf.add_paragraph()

                    # Handle sub-bullets
                    clean_text = bullet
                    if bullet.startswith("- "):
                        clean_text = bullet[2:]
                        p.level = 1
                    else:
                        p.level = 0

                    run = p.add_run()
                    run.text = clean_text
                    if template_font_name:
                        run.font.name = template_font_name
                    if template_font_size:
                        run.font.size = template_font_size

                return True
        return False

    # ------------------------------------------------------------------
    # Shape helpers (for content without native placeholders)
    # ------------------------------------------------------------------

    @staticmethod
    def _add_table_shape(slide, table_data: list[list]) -> None:
        """Add a table shape to the slide.

        Args:
            table_data: 2-D list with the first row as headers.
        """
        if not table_data or not table_data[0]:
            return

        rows = len(table_data)
        cols = len(table_data[0])

        # Position the table below the title area
        left = Inches(0.8)
        top = Inches(2.5)
        width = Inches(11.5)
        height = Inches(0.4) * rows

        table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
        table = table_shape.table

        for row_idx, row_data in enumerate(table_data):
            for col_idx, cell_val in enumerate(row_data):
                if col_idx < cols:
                    cell = table.cell(row_idx, col_idx)
                    cell.text = str(cell_val)

    @staticmethod
    def _add_chart_shape(slide, chart_data: dict) -> None:
        """Add a chart shape to the slide.

        Args:
            chart_data: Dict with ``type``, ``categories``, and ``series``.
        """
        from pptx.chart.data import CategoryChartData

        chart_type_str = chart_data.get("type", "bar").lower()
        chart_type_map = {
            "bar": XL_CHART_TYPE.BAR_CLUSTERED,
            "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
            "line": XL_CHART_TYPE.LINE,
            "pie": XL_CHART_TYPE.PIE,
        }
        xl_chart_type = chart_type_map.get(chart_type_str, XL_CHART_TYPE.BAR_CLUSTERED)

        categories = chart_data.get("categories", [])
        series_list = chart_data.get("series", [])

        # Fallback: convert "data" format to categories/series
        if not categories and not series_list and "data" in chart_data:
            raw = chart_data["data"]
            if raw and len(raw) > 1:
                categories = [str(row[0]) for row in raw[1:]]
                headers = raw[0][1:]
                series_list = []
                for col_idx, header in enumerate(headers):
                    values = []
                    for row in raw[1:]:
                        try:
                            values.append(float(row[col_idx + 1]))
                        except (ValueError, IndexError):
                            values.append(0)
                    series_list.append({"name": str(header), "values": values})

        if not categories or not series_list:
            return

        cd = CategoryChartData()
        cd.categories = categories
        for s in series_list:
            cd.add_series(s.get("name", "Series"), s.get("values", []))

        left = Inches(1.0)
        top = Inches(2.2)
        width = Inches(10.5)
        height = Inches(4.5)

        slide.shapes.add_chart(xl_chart_type, left, top, width, height, cd)

    # ------------------------------------------------------------------
    # Image helper
    # ------------------------------------------------------------------

    @staticmethod
    def _insert_image(slide, image_path: str) -> None:
        """Insert an image into a picture placeholder or as a free shape."""
        from pathlib import Path as _Path

        if not _Path(image_path).exists():
            return

        # Try to find a picture placeholder (type 18 = PICTURE)
        for ph in slide.placeholders:
            if ph.placeholder_format.type is not None:
                try:
                    ph_type_val = ph.placeholder_format.type
                    # PP_PLACEHOLDER.PICTURE == 18
                    if ph_type_val == 18:
                        ph.insert_picture(image_path)
                        return
                except Exception:
                    pass

        # Fallback: add as a free-positioned shape
        try:
            slide.shapes.add_picture(
                image_path,
                Inches(6.5),
                Inches(1.5),
                width=Inches(5.5),
            )
        except Exception as exc:
            logger.warning("Could not insert image: %s", exc)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _column_to_text(col: dict) -> str:
        """Convert a column dict (with heading/title, bullets, body) to
        a single text string.
        """
        parts = []
        heading = col.get("heading", "") or col.get("title", "")
        if heading:
            parts.append(heading)

        bullets = col.get("bullets", [])
        if bullets:
            for b in bullets:
                parts.append(f"  \u2022 {b}")

        body = col.get("body", "")
        if body:
            parts.append(body)

        return "\n".join(parts)


# ======================================================================
# DOCX Template Engine
# ======================================================================

class DocxTemplateEngine:
    """Opens a corporate DOCX template and provides a clean Document
    with the template's styles, margins, headers, and footers preserved.
    """

    def __init__(self, template_path: Optional[str] = None):
        """Initialise the engine.

        Args:
            template_path: Explicit path to a DOCX template.  When *None*
                the engine auto-discovers the default template.
        """
        self.template_path: Optional[Path] = None
        self.available: bool = False
        self._style_catalog: list[str] = []

        if template_path:
            p = Path(template_path)
            if p.exists() and p.suffix.lower() == ".docx":
                self.template_path = p
        else:
            self.template_path = self._find_default_template()

        if self.template_path:
            try:
                self._analyze_template()
                self.available = True
                logger.info(
                    "DocxTemplateEngine ready: %s (%d styles)",
                    self.template_path.name,
                    len(self._style_catalog),
                )
            except Exception as exc:
                logger.warning("Failed to analyse DOCX template: %s", exc)
                self.available = False

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _find_default_template(self) -> Optional[Path]:
        """Glob-search for ``GMT_Word Template*.docx``."""
        if not TEMPLATES_DIR.exists():
            return None

        candidates = sorted(TEMPLATES_DIR.glob("GMT_Word Template*.docx"))
        if not candidates:
            return None

        # Prefer the shortest name (base file without timestamp suffix)
        candidates.sort(key=lambda p: len(p.name))
        return candidates[0]

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def _analyze_template(self) -> None:
        """Open the template and catalogue available style names."""
        doc = Document(str(self.template_path))
        self._style_catalog = [s.name for s in doc.styles if s.name]
        logger.debug("Template styles: %s", self._style_catalog[:20])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_from_template(self) -> tuple[Document, list[str]]:
        """Open the template and return a clean Document.

        Clears the body content (paragraphs and tables) of the template
        while preserving headers, footers, styles, and margins.

        Returns:
            Tuple of (Document, style_catalog) where *style_catalog*
            is a list of style names available in the template.

        Raises:
            RuntimeError: If the template is not available.
        """
        if not self.available or not self.template_path:
            raise RuntimeError("DOCX template not available")

        doc = Document(str(self.template_path))

        # Clear body content but keep section properties (headers/footers/margins)
        body = doc.element.body
        # Remove paragraphs and tables, keep sectPr
        for child in list(body):
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag in ("p", "tbl"):
                body.remove(child)

        # Add a single empty paragraph so the document is valid
        doc.add_paragraph()

        return doc, self._style_catalog
