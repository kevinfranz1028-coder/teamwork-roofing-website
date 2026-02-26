"""
Brand Intelligence Content Hub - Document Generator (python-docx)

Creates branded DOCX documents from structured content JSON.
Supports 10 pre-built document templates with consistent brand formatting.

Usage:
    from app.generators.document_gen import BrandedDocumentGenerator

    gen = BrandedDocumentGenerator()
    path = gen.generate(
        content={"title": "Q1 Report", "period": "Jan-Mar 2026", ...},
        doc_type="weekly_report",
        title="Q1 Weekly Report",
    )
"""

import csv
import io
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

from app.config import BASE_DIR, BRAND_ASSETS_DIR, DOCUMENTS_DIR, LOGOS_DIR, TEMPLATES_DIR

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Template metadata registry
# ---------------------------------------------------------------------------

DOCUMENT_TEMPLATES = {
    "job_aid": {
        "name": "Job Aid",
        "description": "1-2 page quick reference guide with step-by-step instructions",
        "typical_pages": "1-2",
        "use_cases": [
            "Quick reference cards",
            "How-to guides",
            "Cheat sheets",
        ],
    },
    "case_study": {
        "name": "Case Study",
        "description": "Challenge/Solution/Results format showcasing success stories",
        "typical_pages": "2-4",
        "use_cases": [
            "Client success stories",
            "Project retrospectives",
            "Marketing collateral",
        ],
    },
    "weekly_report": {
        "name": "Weekly Report",
        "description": "Concise weekly status report with KPIs, accomplishments, and priorities",
        "typical_pages": "1-2",
        "use_cases": [
            "Team status updates",
            "Project progress reports",
            "Stakeholder briefings",
        ],
    },
    "monthly_report": {
        "name": "Monthly Report",
        "description": "Comprehensive monthly report with executive summary, metrics, and recommendations",
        "typical_pages": "4-8",
        "use_cases": [
            "Monthly business reviews",
            "Department reports",
            "Executive summaries",
        ],
    },
    "sop": {
        "name": "Standard Operating Procedure",
        "description": "Formal SOP with document control, numbered procedures, and revision history",
        "typical_pages": "3-6",
        "use_cases": [
            "Process documentation",
            "Compliance procedures",
            "Operational guidelines",
        ],
    },
    "training_guide": {
        "name": "Training Guide",
        "description": "Multi-module training document with objectives, activities, and assessments",
        "typical_pages": "5-15",
        "use_cases": [
            "Employee onboarding",
            "Skill development courses",
            "Certification prep materials",
        ],
    },
    "internal_memo": {
        "name": "Internal Memo",
        "description": "Formal memorandum with TO/FROM/DATE/RE header and action items",
        "typical_pages": "1-2",
        "use_cases": [
            "Policy announcements",
            "Internal communications",
            "Decision documentation",
        ],
    },
    "battle_card": {
        "name": "Battle Card",
        "description": "Competitive positioning document with comparison tables and objection handling",
        "typical_pages": "1-2",
        "use_cases": [
            "Sales enablement",
            "Competitive analysis",
            "Product positioning",
        ],
    },
    "capability_overview": {
        "name": "Capability Overview",
        "description": "One-page company or product capability summary with key stats",
        "typical_pages": "1-2",
        "use_cases": [
            "Company overviews",
            "Service catalogs",
            "Capability briefs",
        ],
    },
    "proposal": {
        "name": "Business Proposal",
        "description": "Full business proposal with scope, timeline, pricing, and terms",
        "typical_pages": "5-10",
        "use_cases": [
            "Client proposals",
            "Project bids",
            "Partnership offers",
        ],
    },
}


# ---------------------------------------------------------------------------
# Colour helpers (docx-compatible, independent of pptx module)
# ---------------------------------------------------------------------------

def hex_to_rgb(hex_color: str) -> RGBColor:
    """Convert a hex colour string (e.g. ``#0066CC``) to a python-docx ``RGBColor``.

    Handles missing ``#`` prefix gracefully and returns black for invalid input.
    """
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


def hex_to_hex_str(hex_color: str) -> str:
    """Return a clean 6-char hex string (no ``#``) for XML shading values."""
    return hex_color.lstrip("#").upper()


def lighten_hex(hex_color: str, factor: float = 0.85) -> str:
    """Lighten a hex colour by blending towards white. Returns 6-char hex string."""
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
# BrandedDocumentStyles
# ---------------------------------------------------------------------------

class BrandedDocumentStyles:
    """Helper class that applies consistent brand styling to a python-docx Document.

    Manages creation and modification of Word styles, header/footer branding,
    cover pages, tables, and callout boxes.
    """

    def __init__(self, doc: Document, brand_config: dict):
        """Initialise with a Document instance and brand configuration.

        Args:
            doc: A python-docx Document object.
            brand_config: Brand configuration dict with keys ``colors``,
                ``fonts``, ``company_name``, etc.
        """
        self.doc = doc
        self.brand_config = brand_config

        # Resolve brand colours
        colors_cfg = brand_config.get("colors", {})
        self.primary = hex_to_rgb(colors_cfg.get("primary", "#0066CC"))
        self.secondary = hex_to_rgb(colors_cfg.get("secondary", "#004499"))
        self.background = hex_to_rgb(colors_cfg.get("background", "#FFFFFF"))
        self.accent = hex_to_rgb(colors_cfg.get("accent", "#FF6600"))
        self.text_color = hex_to_rgb(colors_cfg.get("text", "#333333"))
        self.white = RGBColor(255, 255, 255)
        self.light_gray = RGBColor(240, 240, 240)
        self.dark_gray = RGBColor(80, 80, 80)

        # Keep raw hex for XML shading
        self.primary_hex = hex_to_hex_str(colors_cfg.get("primary", "#0066CC"))
        self.secondary_hex = hex_to_hex_str(colors_cfg.get("secondary", "#004499"))
        self.accent_hex = hex_to_hex_str(colors_cfg.get("accent", "#FF6600"))
        self.text_hex = hex_to_hex_str(colors_cfg.get("text", "#333333"))
        self.primary_light_hex = lighten_hex(colors_cfg.get("primary", "#0066CC"), 0.85)
        self.secondary_light_hex = lighten_hex(colors_cfg.get("secondary", "#004499"), 0.90)
        self.accent_light_hex = lighten_hex(colors_cfg.get("accent", "#FF6600"), 0.88)

        # Resolve brand fonts
        fonts_cfg = brand_config.get("fonts", {})
        self.heading_font = fonts_cfg.get("heading", "Arial")
        self.body_font = fonts_cfg.get("body", "Calibri")

        self.company_name = brand_config.get("company_name", "")

    # ------------------------------------------------------------------
    # Static colour helper
    # ------------------------------------------------------------------

    @staticmethod
    def hex_to_rgb(hex_color: str) -> RGBColor:
        """Convert a hex colour string to a python-docx RGBColor.

        This static method delegates to the module-level helper so callers
        can access it without a module import.
        """
        return hex_to_rgb(hex_color)

    # ------------------------------------------------------------------
    # Style setup
    # ------------------------------------------------------------------

    def setup_styles(self) -> None:
        """Create or modify all document styles to match the brand identity.

        Configures Title, Heading 1-4, Normal, Quote, Intense Quote,
        Callout, Caption, List Bullet, and List Number styles.
        """
        styles = self.doc.styles

        # --- Title style ---
        title_style = styles["Title"]
        title_fmt = title_style.font
        title_fmt.name = self.heading_font
        title_fmt.size = Pt(28)
        title_fmt.color.rgb = self.primary
        title_fmt.bold = True
        title_style.paragraph_format.space_after = Pt(12)
        title_style.paragraph_format.space_before = Pt(0)

        # --- Heading 1 ---
        h1 = styles["Heading 1"]
        h1.font.name = self.heading_font
        h1.font.size = Pt(22)
        h1.font.color.rgb = self.primary
        h1.font.bold = True
        h1.paragraph_format.space_before = Pt(18)
        h1.paragraph_format.space_after = Pt(6)

        # --- Heading 2 ---
        h2 = styles["Heading 2"]
        h2.font.name = self.heading_font
        h2.font.size = Pt(18)
        h2.font.color.rgb = self.secondary
        h2.font.bold = True
        h2.paragraph_format.space_before = Pt(14)
        h2.paragraph_format.space_after = Pt(4)

        # --- Heading 3 ---
        h3 = styles["Heading 3"]
        h3.font.name = self.heading_font
        h3.font.size = Pt(14)
        h3.font.color.rgb = self.primary
        h3.font.bold = True
        h3.paragraph_format.space_before = Pt(12)
        h3.paragraph_format.space_after = Pt(4)

        # --- Heading 4 ---
        h4 = styles["Heading 4"]
        h4.font.name = self.heading_font
        h4.font.size = Pt(12)
        h4.font.color.rgb = self.secondary
        h4.font.bold = True
        h4.font.italic = True
        h4.paragraph_format.space_before = Pt(10)
        h4.paragraph_format.space_after = Pt(2)

        # --- Normal (body) ---
        normal = styles["Normal"]
        normal.font.name = self.body_font
        normal.font.size = Pt(11)
        normal.font.color.rgb = self.text_color
        normal.paragraph_format.space_after = Pt(6)
        normal.paragraph_format.line_spacing = 1.15

        # --- Quote ---
        quote_style = styles["Quote"]
        quote_style.font.name = self.body_font
        quote_style.font.size = Pt(11)
        quote_style.font.italic = True
        quote_style.font.color.rgb = self.dark_gray
        quote_style.paragraph_format.left_indent = Inches(0.5)
        quote_style.paragraph_format.space_before = Pt(6)
        quote_style.paragraph_format.space_after = Pt(6)
        # Add accent left border via XML
        quote_ppr = quote_style.paragraph_format.element
        borders_xml = (
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:left w:val="single" w:sz="12" w:space="8" w:color="{self.accent_hex}"/>'
            f'</w:pBdr>'
        )
        existing_bdr = quote_ppr.find(qn("w:pBdr"))
        if existing_bdr is not None:
            quote_ppr.remove(existing_bdr)
        quote_ppr.append(parse_xml(borders_xml))

        # --- Intense Quote ---
        intense_quote = styles["Intense Quote"]
        intense_quote.font.name = self.body_font
        intense_quote.font.size = Pt(12)
        intense_quote.font.italic = True
        intense_quote.font.color.rgb = self.primary
        intense_quote.paragraph_format.left_indent = Inches(0.5)
        intense_quote.paragraph_format.right_indent = Inches(0.5)
        intense_quote.paragraph_format.space_before = Pt(10)
        intense_quote.paragraph_format.space_after = Pt(10)
        iq_ppr = intense_quote.paragraph_format.element
        iq_borders_xml = (
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:top w:val="single" w:sz="4" w:space="4" w:color="{self.primary_hex}"/>'
            f'  <w:left w:val="single" w:sz="12" w:space="8" w:color="{self.primary_hex}"/>'
            f'  <w:bottom w:val="single" w:sz="4" w:space="4" w:color="{self.primary_hex}"/>'
            f'</w:pBdr>'
        )
        existing_iq_bdr = iq_ppr.find(qn("w:pBdr"))
        if existing_iq_bdr is not None:
            iq_ppr.remove(existing_iq_bdr)
        iq_ppr.append(parse_xml(iq_borders_xml))

        # --- Callout (custom character style for paragraphs) ---
        # We create a custom paragraph style named "Callout"
        try:
            callout_style = styles["Callout"]
        except KeyError:
            from docx.enum.style import WD_STYLE_TYPE
            callout_style = styles.add_style("Callout", WD_STYLE_TYPE.PARAGRAPH)
        callout_style.font.name = self.body_font
        callout_style.font.size = Pt(10)
        callout_style.font.color.rgb = self.text_color
        callout_style.paragraph_format.left_indent = Inches(0.3)
        callout_style.paragraph_format.space_before = Pt(8)
        callout_style.paragraph_format.space_after = Pt(8)
        # Shading background
        callout_ppr = callout_style.paragraph_format.element
        shading_xml = (
            f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
            f'w:fill="{self.primary_light_hex}"/>'
        )
        existing_shd = callout_ppr.find(qn("w:shd"))
        if existing_shd is not None:
            callout_ppr.remove(existing_shd)
        callout_ppr.append(parse_xml(shading_xml))
        # Left border
        callout_borders_xml = (
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:left w:val="single" w:sz="18" w:space="8" w:color="{self.accent_hex}"/>'
            f'</w:pBdr>'
        )
        existing_cb = callout_ppr.find(qn("w:pBdr"))
        if existing_cb is not None:
            callout_ppr.remove(existing_cb)
        callout_ppr.append(parse_xml(callout_borders_xml))

        # --- Caption ---
        caption_style = styles["Caption"]
        caption_style.font.name = self.body_font
        caption_style.font.size = Pt(9)
        caption_style.font.color.rgb = RGBColor(128, 128, 128)
        caption_style.font.italic = True
        caption_style.paragraph_format.space_before = Pt(2)
        caption_style.paragraph_format.space_after = Pt(8)

        # --- List Bullet ---
        lb = styles["List Bullet"]
        lb.font.name = self.body_font
        lb.font.size = Pt(11)
        lb.font.color.rgb = self.text_color
        lb.paragraph_format.space_after = Pt(3)
        lb.paragraph_format.left_indent = Inches(0.5)

        # --- List Number ---
        ln = styles["List Number"]
        ln.font.name = self.body_font
        ln.font.size = Pt(11)
        ln.font.color.rgb = self.text_color
        ln.paragraph_format.space_after = Pt(3)
        ln.paragraph_format.left_indent = Inches(0.5)

    # ------------------------------------------------------------------
    # Header / footer
    # ------------------------------------------------------------------

    def apply_header_footer(
        self,
        section,
        company_name: str,
        logo_path: Optional[str] = None,
    ) -> None:
        """Add branded header and footer to a document section.

        The header contains the company logo on the left and the company
        name on the right.  The footer has centred page numbers and
        'Confidential' right-aligned.

        Args:
            section: A python-docx Section object.
            company_name: Display name for the company.
            logo_path: Optional filesystem path to the logo image.
        """
        # --- Header ---
        header = section.header
        header.is_linked_to_previous = False
        header_para = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        header_para.clear()

        # Insert logo if available
        if logo_path and os.path.isfile(logo_path):
            try:
                run_logo = header_para.add_run()
                run_logo.add_picture(logo_path, height=Inches(0.35))
            except Exception as exc:
                logger.warning("Could not insert logo in header: %s", exc)

        # Add tab stop and company name on right
        header_para.add_run("  ")
        run_name = header_para.add_run(company_name)
        run_name.font.name = self.heading_font
        run_name.font.size = Pt(9)
        run_name.font.color.rgb = self.primary
        run_name.font.bold = True
        header_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        # Add a thin line under the header
        hdr_ppr = header_para._element.get_or_add_pPr()
        hdr_border_xml = (
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:bottom w:val="single" w:sz="4" w:space="1" w:color="{self.primary_hex}"/>'
            f'</w:pBdr>'
        )
        existing_hdr_bdr = hdr_ppr.find(qn("w:pBdr"))
        if existing_hdr_bdr is not None:
            hdr_ppr.remove(existing_hdr_bdr)
        hdr_ppr.append(parse_xml(hdr_border_xml))

        # --- Footer ---
        footer = section.footer
        footer.is_linked_to_previous = False

        # Page number in centre
        footer_para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        footer_para.clear()
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        run_page = footer_para.add_run()
        run_page.font.name = self.body_font
        run_page.font.size = Pt(8)
        run_page.font.color.rgb = self.dark_gray

        # Insert "Page X" via field code
        fld_char_begin = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>')
        run_page._element.append(fld_char_begin)
        instr_text = parse_xml(f'<w:instrText {nsdecls("w")} xml:space="preserve"> PAGE </w:instrText>')
        run_page._element.append(instr_text)
        fld_char_end = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>')
        run_page._element.append(fld_char_end)

        # Confidential text on right (separate paragraph)
        conf_para = footer.add_paragraph()
        conf_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run_conf = conf_para.add_run("Confidential")
        run_conf.font.name = self.body_font
        run_conf.font.size = Pt(7)
        run_conf.font.color.rgb = RGBColor(180, 180, 180)
        run_conf.font.italic = True

    # ------------------------------------------------------------------
    # Cover page
    # ------------------------------------------------------------------

    def create_cover_page(
        self,
        title: str,
        subtitle: str = "",
        author: str = "",
        date_str: str = "",
    ) -> None:
        """Add a full branded cover page to the document.

        Features a primary-colour block at the top, the document title,
        an optional subtitle, author line, date, and company logo.

        Args:
            title: Main document title.
            subtitle: Optional subtitle / tagline.
            author: Author name displayed on the cover.
            date_str: Date string displayed below the author.
        """
        doc = self.doc

        # Top colour band (simulated with a shaded paragraph)
        color_band = doc.add_paragraph()
        color_band.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cb_ppr = color_band._element.get_or_add_pPr()
        band_shading = (
            f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
            f'w:fill="{self.primary_hex}"/>'
        )
        cb_ppr.append(parse_xml(band_shading))
        color_band.paragraph_format.space_before = Pt(0)
        color_band.paragraph_format.space_after = Pt(0)

        # Add multiple blank lines inside the band for height
        for _ in range(3):
            run_blank = color_band.add_run("\n")
            run_blank.font.size = Pt(18)
            run_blank.font.color.rgb = self.white

        # Company logo centred (if available)
        logo_path = self._find_logo_path()
        if logo_path:
            logo_para = doc.add_paragraph()
            logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            logo_para.paragraph_format.space_before = Pt(24)
            logo_para.paragraph_format.space_after = Pt(12)
            try:
                run_logo = logo_para.add_run()
                run_logo.add_picture(logo_path, height=Inches(0.8))
            except Exception as exc:
                logger.warning("Could not insert logo on cover: %s", exc)

        # Spacing before title
        spacer = doc.add_paragraph()
        spacer.paragraph_format.space_before = Pt(24)
        spacer.paragraph_format.space_after = Pt(0)

        # Title
        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_para.paragraph_format.space_before = Pt(12)
        title_para.paragraph_format.space_after = Pt(6)
        run_title = title_para.add_run(title)
        run_title.font.name = self.heading_font
        run_title.font.size = Pt(32)
        run_title.font.color.rgb = self.primary
        run_title.font.bold = True

        # Subtitle
        if subtitle:
            sub_para = doc.add_paragraph()
            sub_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            sub_para.paragraph_format.space_before = Pt(0)
            sub_para.paragraph_format.space_after = Pt(6)
            run_sub = sub_para.add_run(subtitle)
            run_sub.font.name = self.heading_font
            run_sub.font.size = Pt(16)
            run_sub.font.color.rgb = self.secondary
            run_sub.font.italic = True

        # Decorative line
        line_para = doc.add_paragraph()
        line_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        line_para.paragraph_format.space_before = Pt(12)
        line_para.paragraph_format.space_after = Pt(12)
        line_ppr = line_para._element.get_or_add_pPr()
        line_border_xml = (
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:bottom w:val="single" w:sz="6" w:space="1" w:color="{self.accent_hex}"/>'
            f'</w:pBdr>'
        )
        line_ppr.append(parse_xml(line_border_xml))
        line_para.add_run("                                                  ")

        # Author
        if author:
            author_para = doc.add_paragraph()
            author_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            author_para.paragraph_format.space_before = Pt(18)
            author_para.paragraph_format.space_after = Pt(2)
            run_label = author_para.add_run("Prepared by: ")
            run_label.font.name = self.body_font
            run_label.font.size = Pt(11)
            run_label.font.color.rgb = self.dark_gray
            run_author = author_para.add_run(author)
            run_author.font.name = self.body_font
            run_author.font.size = Pt(12)
            run_author.font.color.rgb = self.text_color
            run_author.font.bold = True

        # Date
        if date_str:
            date_para = doc.add_paragraph()
            date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            date_para.paragraph_format.space_before = Pt(4)
            date_para.paragraph_format.space_after = Pt(0)
            run_date = date_para.add_run(date_str)
            run_date.font.name = self.body_font
            run_date.font.size = Pt(11)
            run_date.font.color.rgb = self.dark_gray

        # Company name at bottom
        if self.company_name:
            company_para = doc.add_paragraph()
            company_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            company_para.paragraph_format.space_before = Pt(48)
            run_co = company_para.add_run(self.company_name)
            run_co.font.name = self.heading_font
            run_co.font.size = Pt(10)
            run_co.font.color.rgb = self.primary
            run_co.font.bold = True

    # ------------------------------------------------------------------
    # Tables
    # ------------------------------------------------------------------

    def add_branded_table(
        self,
        data: list[list[str]],
        has_header: bool = True,
        col_widths: Optional[list] = None,
    ):
        """Add a styled table to the document.

        Header row uses the brand primary colour with white text.
        Data rows use alternating light shading.

        Args:
            data: 2-D list of cell values. First row treated as headers
                when *has_header* is True.
            has_header: If True, the first row gets header styling.
            col_widths: Optional list of column widths in inches.

        Returns:
            The python-docx Table object.
        """
        if not data:
            return None

        rows = len(data)
        cols = len(data[0]) if data else 0
        if cols == 0:
            return None

        table = self.doc.add_table(rows=rows, cols=cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.style = "Table Grid"

        # Apply column widths
        if col_widths and len(col_widths) == cols:
            for i, width in enumerate(col_widths):
                for row in table.rows:
                    row.cells[i].width = Inches(width)

        for row_idx, row_data in enumerate(data):
            row = table.rows[row_idx]
            for col_idx, cell_value in enumerate(row_data):
                cell = row.cells[col_idx]
                # Clear the default paragraph and add styled content
                para = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
                para.clear()
                run = para.add_run(str(cell_value))

                if has_header and row_idx == 0:
                    # Header row styling
                    run.font.name = self.heading_font
                    run.font.size = Pt(10)
                    run.font.color.rgb = self.white
                    run.font.bold = True
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER

                    # Primary colour background
                    shading = parse_xml(
                        f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
                        f'w:fill="{self.primary_hex}"/>'
                    )
                    cell._element.get_or_add_tcPr().append(shading)
                else:
                    # Data row styling
                    run.font.name = self.body_font
                    run.font.size = Pt(10)
                    run.font.color.rgb = self.text_color

                    # Alternating row shading (skip header when counting)
                    effective_idx = row_idx - (1 if has_header else 0)
                    if effective_idx % 2 == 1:
                        alt_shading = parse_xml(
                            f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
                            f'w:fill="{self.primary_light_hex}"/>'
                        )
                        cell._element.get_or_add_tcPr().append(alt_shading)

                # Set vertical alignment to centre
                tc_pr = cell._element.get_or_add_tcPr()
                v_align = parse_xml(f'<w:vAlign {nsdecls("w")} w:val="center"/>')
                existing_va = tc_pr.find(qn("w:vAlign"))
                if existing_va is not None:
                    tc_pr.remove(existing_va)
                tc_pr.append(v_align)

        return table

    # ------------------------------------------------------------------
    # Callout box
    # ------------------------------------------------------------------

    def add_callout_box(self, text: str, callout_type: str = "info") -> None:
        """Add a styled callout box to the document.

        Args:
            text: The callout message.
            callout_type: One of ``"info"``, ``"warning"``, ``"success"``,
                or ``"tip"`` to control the border colour and icon prefix.
        """
        # Map callout types to colours and prefixes
        type_config = {
            "info": {"color": self.primary_hex, "prefix": "INFO: ", "bg": self.primary_light_hex},
            "warning": {"color": self.accent_hex, "prefix": "WARNING: ", "bg": self.accent_light_hex},
            "success": {"color": "28A745", "prefix": "SUCCESS: ", "bg": lighten_hex("#28A745", 0.88)},
            "tip": {"color": self.secondary_hex, "prefix": "TIP: ", "bg": self.secondary_light_hex},
        }
        config = type_config.get(callout_type, type_config["info"])

        callout_para = self.doc.add_paragraph()
        callout_para.paragraph_format.left_indent = Inches(0.3)
        callout_para.paragraph_format.right_indent = Inches(0.3)
        callout_para.paragraph_format.space_before = Pt(8)
        callout_para.paragraph_format.space_after = Pt(8)

        # Prefix run (bold)
        run_prefix = callout_para.add_run(config["prefix"])
        run_prefix.font.name = self.body_font
        run_prefix.font.size = Pt(10)
        run_prefix.font.bold = True
        run_prefix.font.color.rgb = hex_to_rgb(config["color"])

        # Body run
        run_body = callout_para.add_run(text)
        run_body.font.name = self.body_font
        run_body.font.size = Pt(10)
        run_body.font.color.rgb = self.text_color

        # Apply background shading and left border
        ppr = callout_para._element.get_or_add_pPr()
        shading = parse_xml(
            f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
            f'w:fill="{config["bg"]}"/>'
        )
        existing_shd = ppr.find(qn("w:shd"))
        if existing_shd is not None:
            ppr.remove(existing_shd)
        ppr.append(shading)

        border_xml = (
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:left w:val="single" w:sz="24" w:space="8" w:color="{config["color"]}"/>'
            f'</w:pBdr>'
        )
        existing_bdr = ppr.find(qn("w:pBdr"))
        if existing_bdr is not None:
            ppr.remove(existing_bdr)
        ppr.append(parse_xml(border_xml))

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    def add_page_break(self) -> None:
        """Insert a page break into the document."""
        self.doc.add_page_break()

    def set_margins(
        self,
        top: float = 1.0,
        bottom: float = 1.0,
        left: float = 1.0,
        right: float = 1.0,
    ) -> None:
        """Set page margins for all sections in inches.

        Args:
            top: Top margin in inches.
            bottom: Bottom margin in inches.
            left: Left margin in inches.
            right: Right margin in inches.
        """
        for section in self.doc.sections:
            section.top_margin = Inches(top)
            section.bottom_margin = Inches(bottom)
            section.left_margin = Inches(left)
            section.right_margin = Inches(right)

    def _find_logo_path(self) -> Optional[str]:
        """Return path to first logo image found in the logos directory."""
        if not LOGOS_DIR.exists():
            return None
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.svg"):
            logos = list(LOGOS_DIR.glob(ext))
            if logos:
                return str(logos[0])
        return None


# ---------------------------------------------------------------------------
# BrandedDocumentGenerator
# ---------------------------------------------------------------------------

class BrandedDocumentGenerator:
    """Main document generator that creates DOCX files from structured JSON.

    Routes to one of 10 pre-built template builders based on ``doc_type``.
    All documents receive consistent brand styling via :class:`BrandedDocumentStyles`.

    Usage::

        gen = BrandedDocumentGenerator()
        path = gen.generate(
            content={...},
            doc_type="weekly_report",
            title="Week 12 Status Report",
        )
    """

    # Supported document types
    SUPPORTED_TYPES = list(DOCUMENT_TEMPLATES.keys())

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def __init__(self, brand_config: Optional[dict] = None):
        """Initialise with optional brand configuration.

        Args:
            brand_config: A brand-config dictionary. If *None*, the file
                at ``brand_assets/brand_config.json`` is loaded automatically.
        """
        self.brand_config: dict = brand_config or self._load_brand_config()
        self.company_name: str = self.brand_config.get("company_name", "")
        self.logo_path: Optional[str] = self._find_logo()

    def _load_brand_config(self) -> dict:
        """Load brand configuration from ``brand_assets/brand_config.json``.

        Returns an empty dict on failure so the generator always works.
        """
        config_path = BRAND_ASSETS_DIR / "brand_config.json"
        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not load brand config: %s", exc)
        return {}

    def _find_logo(self) -> Optional[str]:
        """Return the path to the first logo image found in ``brand_assets/logos/``.

        Searches for PNG, JPG, JPEG, and SVG files in order.
        """
        if not LOGOS_DIR.exists():
            return None
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.svg"):
            logos = list(LOGOS_DIR.glob(ext))
            if logos:
                return str(logos[0])
        return None

    # ------------------------------------------------------------------
    # Document initialisation helper
    # ------------------------------------------------------------------

    def _init_document(self) -> tuple[Document, BrandedDocumentStyles]:
        """Create a new Document and apply brand styles.

        Returns:
            Tuple of (Document, BrandedDocumentStyles).
        """
        doc = Document()
        styler = BrandedDocumentStyles(doc, self.brand_config)
        styler.setup_styles()
        styler.set_margins(top=1.0, bottom=1.0, left=1.0, right=1.0)

        # Apply header / footer to the default section
        section = doc.sections[0]
        styler.apply_header_footer(section, self.company_name, self.logo_path)

        return doc, styler

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        content: dict,
        doc_type: str,
        title: str = "",
        save_path: Optional[str] = None,
    ) -> str:
        """Generate a branded DOCX document.

        Args:
            content: Structured JSON content for the document. Keys vary
                by *doc_type* (see individual builder docs).
            doc_type: Template type identifier (one of :attr:`SUPPORTED_TYPES`).
            title: Document title used for filename and metadata.
            save_path: Optional full path to save the file. When *None*,
                a timestamped filename is generated in ``output/documents/``.

        Returns:
            The absolute filesystem path to the saved DOCX file.

        Raises:
            ValueError: If *doc_type* is not recognised.
        """
        if doc_type not in DOCUMENT_TEMPLATES:
            supported = ", ".join(sorted(DOCUMENT_TEMPLATES.keys()))
            raise ValueError(
                f"Unknown doc_type '{doc_type}'. Supported types: {supported}"
            )

        if not title:
            title = content.get("title", DOCUMENT_TEMPLATES[doc_type]["name"])

        logger.info("Generating %s document: %s", doc_type, title)
        start_time = time.time()

        # Route to the template builder
        builder_map = {
            "job_aid": self.build_job_aid,
            "case_study": self.build_case_study,
            "weekly_report": self.build_weekly_report,
            "monthly_report": self.build_monthly_report,
            "sop": self.build_sop,
            "training_guide": self.build_training_guide,
            "internal_memo": self.build_internal_memo,
            "battle_card": self.build_battle_card,
            "capability_overview": self.build_capability_overview,
            "proposal": self.build_proposal,
        }

        builder = builder_map[doc_type]
        doc = builder(content)

        elapsed = time.time() - start_time
        logger.info("Document built in %.2f seconds", elapsed)

        return self._save_document(doc, title, save_path)

    # ------------------------------------------------------------------
    # Save helper
    # ------------------------------------------------------------------

    def _save_document(
        self,
        doc: Document,
        title: str,
        save_path: Optional[str] = None,
    ) -> str:
        """Save the document to disk and return the absolute path.

        Args:
            doc: The completed Document to save.
            title: Title used for the filename.
            save_path: Explicit path or *None* to auto-generate.

        Returns:
            Absolute filesystem path to the saved ``.docx`` file.
        """
        if save_path:
            file_path = Path(save_path)
        else:
            # Ensure output directory exists
            DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
            # Sanitise title for filename
            safe_title = "".join(
                c if c.isalnum() or c in (" ", "-", "_") else "_"
                for c in title
            ).strip().replace(" ", "_")[:80]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_title}_{timestamp}.docx"
            file_path = DOCUMENTS_DIR / filename

        file_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(file_path))
        logger.info("Document saved to %s", file_path)
        return str(file_path.resolve())

    # ------------------------------------------------------------------
    # Helper: add body paragraphs
    # ------------------------------------------------------------------

    def _add_body_text(self, doc: Document, text: str, styler: BrandedDocumentStyles) -> None:
        """Add one or more paragraphs of body text to the document.

        Splits on double newlines to create separate paragraphs.
        """
        if not text:
            return
        paragraphs = text.split("\n\n")
        for para_text in paragraphs:
            para_text = para_text.strip()
            if para_text:
                p = doc.add_paragraph(para_text, style="Normal")

    def _add_bullet_list(self, doc: Document, items: list[str]) -> None:
        """Add a bulleted list to the document."""
        for item in items:
            if item:
                doc.add_paragraph(str(item), style="List Bullet")

    def _add_numbered_list(self, doc: Document, items: list[str]) -> None:
        """Add a numbered list to the document."""
        for item in items:
            if item:
                doc.add_paragraph(str(item), style="List Number")

    # ======================================================================
    # TEMPLATE BUILDERS
    # ======================================================================

    # ------------------------------------------------------------------
    # 1. Job Aid
    # ------------------------------------------------------------------

    def build_job_aid(self, content: dict) -> Document:
        """Build a 1-2 page quick-reference Job Aid document.

        Expected content keys:
            - title (str): Document title
            - purpose (str): Purpose statement
            - sections (list[dict]): Each with ``heading``, ``steps`` (list),
              ``tips`` (list)
            - reference_table (list[list[str]]): Quick-lookup data

        Returns:
            A completed Document object.
        """
        doc, styler = self._init_document()

        title = content.get("title", "Job Aid")
        purpose = content.get("purpose", "")
        sections = content.get("sections", [])
        reference_table = content.get("reference_table", [])

        # Title section
        title_para = doc.add_paragraph(title, style="Title")
        title_para.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # Purpose statement with callout
        if purpose:
            styler.add_callout_box(purpose, callout_type="info")

        # Decorative separator
        sep = doc.add_paragraph()
        sep.paragraph_format.space_before = Pt(4)
        sep.paragraph_format.space_after = Pt(8)
        sep_ppr = sep._element.get_or_add_pPr()
        sep_border = (
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:bottom w:val="single" w:sz="4" w:space="1" w:color="{styler.primary_hex}"/>'
            f'</w:pBdr>'
        )
        sep_ppr.append(parse_xml(sep_border))
        sep.add_run(" ")

        # Sections with steps and tips
        for section in sections:
            heading = section.get("heading", "")
            steps = section.get("steps", [])
            tips = section.get("tips", [])

            if heading:
                doc.add_heading(heading, level=2)

            # Numbered steps
            if steps:
                for step_text in steps:
                    doc.add_paragraph(str(step_text), style="List Number")

            # Tips as callouts
            if tips:
                for tip in tips:
                    styler.add_callout_box(str(tip), callout_type="tip")

        # Reference table
        if reference_table and len(reference_table) > 0:
            doc.add_heading("Quick Reference", level=2)
            styler.add_branded_table(reference_table, has_header=True)

        return doc

    # ------------------------------------------------------------------
    # 2. Case Study
    # ------------------------------------------------------------------

    def build_case_study(self, content: dict) -> Document:
        """Build a Challenge/Solution/Results case study document.

        Expected content keys:
            - title (str)
            - client_name (str)
            - industry (str)
            - executive_summary (str)
            - challenge (str)
            - solution (str)
            - approach_steps (list[str])
            - results: { metrics (list[list[str]]), narrative (str) }
            - key_takeaways (list[str])
            - testimonial: { quote (str), attribution (str) }

        Returns:
            A completed Document object.
        """
        doc, styler = self._init_document()

        title = content.get("title", "Case Study")
        client_name = content.get("client_name", "")
        industry = content.get("industry", "")
        executive_summary = content.get("executive_summary", "")
        challenge = content.get("challenge", "")
        solution = content.get("solution", "")
        approach_steps = content.get("approach_steps", [])
        results = content.get("results", {})
        key_takeaways = content.get("key_takeaways", [])
        testimonial = content.get("testimonial", {})

        # Cover page
        subtitle = f"{client_name} | {industry}" if client_name else industry
        styler.create_cover_page(
            title=title,
            subtitle=subtitle,
            date_str=datetime.now().strftime("%B %Y"),
        )
        styler.add_page_break()

        # Executive Summary
        doc.add_heading("Executive Summary", level=1)
        self._add_body_text(doc, executive_summary, styler)

        # Client info callout
        if client_name:
            info_text = f"Client: {client_name}"
            if industry:
                info_text += f"  |  Industry: {industry}"
            styler.add_callout_box(info_text, callout_type="info")

        # The Challenge
        doc.add_heading("The Challenge", level=1)
        self._add_body_text(doc, challenge, styler)

        # The Solution
        doc.add_heading("The Solution", level=1)
        self._add_body_text(doc, solution, styler)

        # Approach steps
        if approach_steps:
            doc.add_heading("Our Approach", level=2)
            self._add_numbered_list(doc, approach_steps)

        styler.add_page_break()

        # Results & Impact
        doc.add_heading("Results & Impact", level=1)

        # Metrics table
        metrics = results.get("metrics", [])
        if metrics:
            styler.add_branded_table(metrics, has_header=True)
            doc.add_paragraph()  # spacing

        # Results narrative
        narrative = results.get("narrative", "")
        if narrative:
            self._add_body_text(doc, narrative, styler)

        # Key Takeaways
        if key_takeaways:
            doc.add_heading("Key Takeaways", level=1)
            self._add_bullet_list(doc, key_takeaways)

        # Testimonial quote
        if testimonial and testimonial.get("quote"):
            doc.add_paragraph()  # spacing
            quote_para = doc.add_paragraph(style="Intense Quote")
            run_quote = quote_para.add_run(f'"{testimonial["quote"]}"')
            run_quote.font.size = Pt(13)
            run_quote.font.italic = True

            if testimonial.get("attribution"):
                attr_para = doc.add_paragraph()
                attr_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                attr_para.paragraph_format.space_before = Pt(2)
                run_attr = attr_para.add_run(f"-- {testimonial['attribution']}")
                run_attr.font.name = styler.body_font
                run_attr.font.size = Pt(10)
                run_attr.font.color.rgb = styler.dark_gray
                run_attr.font.italic = True

        return doc

    # ------------------------------------------------------------------
    # 3. Weekly Report
    # ------------------------------------------------------------------

    def build_weekly_report(self, content: dict) -> Document:
        """Build a concise weekly status report.

        Expected content keys:
            - title (str)
            - period (str): e.g. "Week of Feb 17-21, 2026"
            - kpi_data (list[list[str]]): Header row + data rows
            - accomplishments (list[str])
            - challenges (list[str])
            - priorities (list[str])
            - notes (str)

        Returns:
            A completed Document object.
        """
        doc, styler = self._init_document()

        title = content.get("title", "Weekly Report")
        period = content.get("period", "")
        kpi_data = content.get("kpi_data", [])
        accomplishments = content.get("accomplishments", [])
        challenges = content.get("challenges", [])
        priorities = content.get("priorities", [])
        notes = content.get("notes", "")

        # Title
        title_para = doc.add_paragraph(title, style="Title")
        title_para.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # Report period header
        if period:
            period_para = doc.add_paragraph()
            period_para.paragraph_format.space_before = Pt(0)
            period_para.paragraph_format.space_after = Pt(12)
            run_label = period_para.add_run("Report Period: ")
            run_label.font.name = styler.body_font
            run_label.font.size = Pt(11)
            run_label.font.color.rgb = styler.dark_gray
            run_label.font.bold = True
            run_value = period_para.add_run(period)
            run_value.font.name = styler.body_font
            run_value.font.size = Pt(11)
            run_value.font.color.rgb = styler.text_color

        # Separator
        sep = doc.add_paragraph()
        sep.paragraph_format.space_before = Pt(2)
        sep.paragraph_format.space_after = Pt(8)
        sep_ppr = sep._element.get_or_add_pPr()
        sep_border = (
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:bottom w:val="single" w:sz="4" w:space="1" w:color="{styler.primary_hex}"/>'
            f'</w:pBdr>'
        )
        sep_ppr.append(parse_xml(sep_border))
        sep.add_run(" ")

        # KPI Summary Table
        if kpi_data:
            doc.add_heading("KPI Summary", level=2)
            styler.add_branded_table(kpi_data, has_header=True)
            doc.add_paragraph()  # spacing

        # Accomplishments
        if accomplishments:
            doc.add_heading("Accomplishments", level=2)
            self._add_bullet_list(doc, accomplishments)

        # Challenges & Blockers
        if challenges:
            doc.add_heading("Challenges & Blockers", level=2)
            for challenge_text in challenges:
                styler.add_callout_box(str(challenge_text), callout_type="warning")

        # Next Week Priorities
        if priorities:
            doc.add_heading("Next Week Priorities", level=2)
            self._add_numbered_list(doc, priorities)

        # Notes / Comments
        if notes:
            doc.add_heading("Notes", level=2)
            self._add_body_text(doc, notes, styler)

        return doc

    # ------------------------------------------------------------------
    # 4. Monthly Report
    # ------------------------------------------------------------------

    def build_monthly_report(self, content: dict) -> Document:
        """Build a comprehensive monthly report with cover page and TOC.

        Expected content keys:
            - title (str)
            - period (str)
            - executive_summary (str)
            - metrics_data (list[list[str]])
            - sections (list[dict]): Each with ``heading``, ``content``,
              ``subsections`` (list of dicts with heading/content)
            - recommendations (list[str])
            - appendix_items (list[str])

        Returns:
            A completed Document object.
        """
        doc, styler = self._init_document()

        title = content.get("title", "Monthly Report")
        period = content.get("period", "")
        executive_summary = content.get("executive_summary", "")
        metrics_data = content.get("metrics_data", [])
        sections = content.get("sections", [])
        recommendations = content.get("recommendations", [])
        appendix_items = content.get("appendix_items", [])

        # Cover page
        styler.create_cover_page(
            title=title,
            subtitle=period,
            author=self.company_name,
            date_str=datetime.now().strftime("%B %d, %Y"),
        )
        styler.add_page_break()

        # Table of Contents placeholder
        doc.add_heading("Table of Contents", level=1)
        toc_para = doc.add_paragraph()
        toc_para.paragraph_format.space_after = Pt(12)
        # Insert a TOC field code
        run_toc = toc_para.add_run()
        fld_begin = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>')
        run_toc._element.append(fld_begin)
        instr = parse_xml(
            f'<w:instrText {nsdecls("w")} xml:space="preserve">'
            f' TOC \\o "1-3" \\h \\z \\u </w:instrText>'
        )
        run_toc._element.append(instr)
        fld_separate = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="separate"/>')
        run_toc._element.append(fld_separate)
        run_placeholder = toc_para.add_run(
            "[Right-click and select 'Update Field' to generate Table of Contents]"
        )
        run_placeholder.font.color.rgb = RGBColor(160, 160, 160)
        run_placeholder.font.size = Pt(10)
        run_placeholder.font.italic = True
        run_end = toc_para.add_run()
        fld_end = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>')
        run_end._element.append(fld_end)

        styler.add_page_break()

        # Executive Summary
        doc.add_heading("Executive Summary", level=1)
        self._add_body_text(doc, executive_summary, styler)

        # Key Metrics
        if metrics_data:
            doc.add_heading("Key Metrics", level=1)
            styler.add_branded_table(metrics_data, has_header=True)
            doc.add_paragraph()  # spacing

        # Detailed sections
        for section in sections:
            heading = section.get("heading", "")
            section_content = section.get("content", "")
            subsections = section.get("subsections", [])

            if heading:
                doc.add_heading(heading, level=1)

            if section_content:
                self._add_body_text(doc, section_content, styler)

            for subsection in subsections:
                sub_heading = subsection.get("heading", "")
                sub_content = subsection.get("content", "")
                if sub_heading:
                    doc.add_heading(sub_heading, level=2)
                if sub_content:
                    self._add_body_text(doc, sub_content, styler)

        # Recommendations
        if recommendations:
            styler.add_page_break()
            doc.add_heading("Recommendations", level=1)
            for idx, rec in enumerate(recommendations, 1):
                rec_para = doc.add_paragraph()
                run_num = rec_para.add_run(f"{idx}. ")
                run_num.font.name = styler.heading_font
                run_num.font.size = Pt(11)
                run_num.font.color.rgb = styler.primary
                run_num.font.bold = True
                run_text = rec_para.add_run(str(rec))
                run_text.font.name = styler.body_font
                run_text.font.size = Pt(11)
                run_text.font.color.rgb = styler.text_color

        # Appendix
        if appendix_items:
            styler.add_page_break()
            doc.add_heading("Appendix", level=1)
            for item in appendix_items:
                self._add_body_text(doc, str(item), styler)
                doc.add_paragraph()  # spacing between appendix items

        return doc

    # ------------------------------------------------------------------
    # 5. Standard Operating Procedure (SOP)
    # ------------------------------------------------------------------

    def build_sop(self, content: dict) -> Document:
        """Build a formal Standard Operating Procedure document.

        Expected content keys:
            - title (str)
            - doc_number (str)
            - version (str)
            - effective_date (str)
            - author (str)
            - approved_by (str)
            - purpose (str)
            - scope (str)
            - responsibilities (list[list[str]]): Header row + data
            - procedure_steps (list[dict]): Each with ``step`` (str),
              ``sub_steps`` (list[str]), ``notes`` (str)
            - safety_notes (list[str])
            - references (list[str])
            - revision_history (list[list[str]]): Header row + data

        Returns:
            A completed Document object.
        """
        doc, styler = self._init_document()

        title = content.get("title", "Standard Operating Procedure")
        doc_number = content.get("doc_number", "SOP-001")
        version = content.get("version", "1.0")
        effective_date = content.get("effective_date", datetime.now().strftime("%Y-%m-%d"))
        author = content.get("author", "")
        approved_by = content.get("approved_by", "")
        purpose = content.get("purpose", "")
        scope = content.get("scope", "")
        responsibilities = content.get("responsibilities", [])
        procedure_steps = content.get("procedure_steps", [])
        safety_notes = content.get("safety_notes", [])
        references = content.get("references", [])
        revision_history = content.get("revision_history", [])

        # Title
        title_para = doc.add_paragraph(title, style="Title")
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Document control header table
        control_data = [
            ["Document #", doc_number, "Version", version],
            ["Effective Date", effective_date, "Author", author],
            ["Approved By", approved_by, "Status", "Active"],
        ]
        control_table = doc.add_table(rows=3, cols=4)
        control_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        control_table.style = "Table Grid"

        for row_idx, row_data in enumerate(control_data):
            for col_idx, cell_value in enumerate(row_data):
                cell = control_table.rows[row_idx].cells[col_idx]
                para = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
                para.clear()
                run = para.add_run(str(cell_value))

                if col_idx % 2 == 0:
                    # Label cells
                    run.font.name = styler.heading_font
                    run.font.size = Pt(9)
                    run.font.bold = True
                    run.font.color.rgb = styler.white
                    shading = parse_xml(
                        f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
                        f'w:fill="{styler.primary_hex}"/>'
                    )
                    cell._element.get_or_add_tcPr().append(shading)
                else:
                    # Value cells
                    run.font.name = styler.body_font
                    run.font.size = Pt(9)
                    run.font.color.rgb = styler.text_color

        doc.add_paragraph()  # spacing

        # Purpose
        doc.add_heading("1. Purpose", level=1)
        self._add_body_text(doc, purpose, styler)

        # Scope
        doc.add_heading("2. Scope", level=1)
        self._add_body_text(doc, scope, styler)

        # Responsibilities
        if responsibilities:
            doc.add_heading("3. Responsibilities", level=1)
            styler.add_branded_table(responsibilities, has_header=True)
            doc.add_paragraph()

        # Procedure
        doc.add_heading("4. Procedure", level=1)

        for step_idx, step_data in enumerate(procedure_steps, 1):
            step_text = step_data.get("step", "")
            sub_steps = step_data.get("sub_steps", [])
            notes = step_data.get("notes", "")

            # Main step (numbered heading)
            step_para = doc.add_paragraph()
            step_para.paragraph_format.space_before = Pt(8)
            step_para.paragraph_format.space_after = Pt(4)
            run_num = step_para.add_run(f"Step {step_idx}: ")
            run_num.font.name = styler.heading_font
            run_num.font.size = Pt(12)
            run_num.font.color.rgb = styler.primary
            run_num.font.bold = True
            run_desc = step_para.add_run(str(step_text))
            run_desc.font.name = styler.body_font
            run_desc.font.size = Pt(11)
            run_desc.font.color.rgb = styler.text_color

            # Sub-steps
            if sub_steps:
                for sub_idx, sub_step in enumerate(sub_steps, 1):
                    sub_para = doc.add_paragraph()
                    sub_para.paragraph_format.left_indent = Inches(0.5)
                    sub_para.paragraph_format.space_after = Pt(2)
                    run_sub = sub_para.add_run(f"{step_idx}.{sub_idx}  {str(sub_step)}")
                    run_sub.font.name = styler.body_font
                    run_sub.font.size = Pt(10)
                    run_sub.font.color.rgb = styler.text_color

            # Notes
            if notes:
                styler.add_callout_box(str(notes), callout_type="info")

        # Safety / Compliance notes
        if safety_notes:
            doc.add_heading("5. Safety & Compliance", level=1)
            for note in safety_notes:
                styler.add_callout_box(str(note), callout_type="warning")

        # References
        if references:
            doc.add_heading("6. References", level=1)
            self._add_bullet_list(doc, references)

        # Revision history
        if revision_history:
            doc.add_heading("7. Revision History", level=1)
            styler.add_branded_table(revision_history, has_header=True)

        return doc

    # ------------------------------------------------------------------
    # 6. Training Guide
    # ------------------------------------------------------------------

    def build_training_guide(self, content: dict) -> Document:
        """Build a multi-module training guide with TOC and assessments.

        Expected content keys:
            - title (str)
            - course_overview (str)
            - modules (list[dict]): Each with ``title``, ``objectives`` (list),
              ``content`` (list of paragraphs), ``activities`` (list),
              ``key_takeaways`` (list)
            - assessment_questions (list[dict]): Each with ``question``,
              ``options`` (list), ``answer`` (str)
            - glossary (dict): term -> definition
            - appendix (list[str])

        Returns:
            A completed Document object.
        """
        doc, styler = self._init_document()

        title = content.get("title", "Training Guide")
        course_overview = content.get("course_overview", "")
        modules = content.get("modules", [])
        assessment_questions = content.get("assessment_questions", [])
        glossary = content.get("glossary", {})
        appendix = content.get("appendix", [])

        # Cover page
        styler.create_cover_page(
            title=title,
            subtitle="Training Guide",
            author=self.company_name,
            date_str=datetime.now().strftime("%B %Y"),
        )
        styler.add_page_break()

        # Table of Contents
        doc.add_heading("Table of Contents", level=1)
        toc_para = doc.add_paragraph()
        run_toc = toc_para.add_run()
        fld_begin = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>')
        run_toc._element.append(fld_begin)
        instr = parse_xml(
            f'<w:instrText {nsdecls("w")} xml:space="preserve">'
            f' TOC \\o "1-3" \\h \\z \\u </w:instrText>'
        )
        run_toc._element.append(instr)
        fld_sep = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="separate"/>')
        run_toc._element.append(fld_sep)
        run_ph = toc_para.add_run(
            "[Right-click and select 'Update Field' to generate Table of Contents]"
        )
        run_ph.font.color.rgb = RGBColor(160, 160, 160)
        run_ph.font.size = Pt(10)
        run_ph.font.italic = True
        run_end = toc_para.add_run()
        fld_end = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>')
        run_end._element.append(fld_end)

        styler.add_page_break()

        # Introduction / Course Overview
        doc.add_heading("Introduction", level=1)
        doc.add_heading("Course Overview", level=2)
        self._add_body_text(doc, course_overview, styler)

        # Module count summary
        if modules:
            summary_text = f"This training guide contains {len(modules)} module(s)."
            styler.add_callout_box(summary_text, callout_type="info")

        # Modules
        for mod_idx, module in enumerate(modules, 1):
            styler.add_page_break()

            mod_title = module.get("title", f"Module {mod_idx}")
            objectives = module.get("objectives", [])
            mod_content = module.get("content", [])
            activities = module.get("activities", [])
            key_takeaways = module.get("key_takeaways", [])

            # Module heading
            doc.add_heading(f"Module {mod_idx}: {mod_title}", level=1)

            # Learning Objectives
            if objectives:
                doc.add_heading("Learning Objectives", level=2)
                obj_intro = doc.add_paragraph("Upon completing this module, you will be able to:")
                obj_intro.paragraph_format.space_after = Pt(4)
                self._add_bullet_list(doc, objectives)

            # Module content paragraphs
            if mod_content:
                doc.add_heading("Content", level=2)
                for para_text in mod_content:
                    self._add_body_text(doc, str(para_text), styler)

            # Activities
            if activities:
                doc.add_heading("Activities", level=2)
                for act_idx, activity in enumerate(activities, 1):
                    act_para = doc.add_paragraph()
                    act_para.paragraph_format.space_before = Pt(6)
                    run_label = act_para.add_run(f"Activity {act_idx}: ")
                    run_label.font.name = styler.heading_font
                    run_label.font.size = Pt(11)
                    run_label.font.color.rgb = styler.accent
                    run_label.font.bold = True
                    run_desc = act_para.add_run(str(activity))
                    run_desc.font.name = styler.body_font
                    run_desc.font.size = Pt(11)
                    run_desc.font.color.rgb = styler.text_color

            # Key Takeaways
            if key_takeaways:
                doc.add_heading("Key Takeaways", level=2)
                styler.add_callout_box(
                    " | ".join(str(t) for t in key_takeaways),
                    callout_type="tip",
                )

        # Assessment Questions
        if assessment_questions:
            styler.add_page_break()
            doc.add_heading("Assessment", level=1)
            intro_para = doc.add_paragraph(
                "Answer the following questions to test your understanding of the material."
            )
            intro_para.paragraph_format.space_after = Pt(8)

            for q_idx, q_data in enumerate(assessment_questions, 1):
                question = q_data.get("question", "")
                options = q_data.get("options", [])
                answer = q_data.get("answer", "")

                # Question
                q_para = doc.add_paragraph()
                q_para.paragraph_format.space_before = Pt(10)
                q_para.paragraph_format.space_after = Pt(4)
                run_q = q_para.add_run(f"Q{q_idx}. {question}")
                run_q.font.name = styler.body_font
                run_q.font.size = Pt(11)
                run_q.font.color.rgb = styler.text_color
                run_q.font.bold = True

                # Options
                for opt_idx, option in enumerate(options):
                    letter = chr(65 + opt_idx)  # A, B, C, D...
                    opt_para = doc.add_paragraph()
                    opt_para.paragraph_format.left_indent = Inches(0.4)
                    opt_para.paragraph_format.space_after = Pt(2)
                    run_opt = opt_para.add_run(f"{letter}) {option}")
                    run_opt.font.name = styler.body_font
                    run_opt.font.size = Pt(10)
                    run_opt.font.color.rgb = styler.text_color

                # Answer (small, greyed out)
                if answer:
                    ans_para = doc.add_paragraph()
                    ans_para.paragraph_format.left_indent = Inches(0.4)
                    ans_para.paragraph_format.space_before = Pt(2)
                    run_ans_label = ans_para.add_run("Answer: ")
                    run_ans_label.font.name = styler.body_font
                    run_ans_label.font.size = Pt(9)
                    run_ans_label.font.color.rgb = RGBColor(180, 180, 180)
                    run_ans_label.font.bold = True
                    run_ans = ans_para.add_run(str(answer))
                    run_ans.font.name = styler.body_font
                    run_ans.font.size = Pt(9)
                    run_ans.font.color.rgb = RGBColor(180, 180, 180)

        # Glossary
        if glossary:
            styler.add_page_break()
            doc.add_heading("Glossary", level=1)

            # Build glossary table
            glossary_data = [["Term", "Definition"]]
            for term, definition in sorted(glossary.items()):
                glossary_data.append([str(term), str(definition)])
            styler.add_branded_table(glossary_data, has_header=True)

        # Appendix
        if appendix:
            styler.add_page_break()
            doc.add_heading("Appendix", level=1)
            for app_idx, item in enumerate(appendix, 1):
                app_para = doc.add_paragraph()
                app_para.paragraph_format.space_before = Pt(6)
                run_label = app_para.add_run(f"Appendix {app_idx}: ")
                run_label.font.name = styler.heading_font
                run_label.font.size = Pt(11)
                run_label.font.color.rgb = styler.primary
                run_label.font.bold = True
                run_text = app_para.add_run(str(item))
                run_text.font.name = styler.body_font
                run_text.font.size = Pt(11)
                run_text.font.color.rgb = styler.text_color

        return doc

    # ------------------------------------------------------------------
    # 7. Internal Memo
    # ------------------------------------------------------------------

    def build_internal_memo(self, content: dict) -> Document:
        """Build a formal internal memorandum.

        Expected content keys:
            - to (str)
            - from_name (str)
            - date (str)
            - subject (str)
            - body_paragraphs (list[str])
            - action_items (list[str])
            - cc (list[str])

        Returns:
            A completed Document object.
        """
        doc, styler = self._init_document()

        to = content.get("to", "")
        from_name = content.get("from_name", "")
        date_str = content.get("date", datetime.now().strftime("%B %d, %Y"))
        subject = content.get("subject", "")
        body_paragraphs = content.get("body_paragraphs", [])
        action_items = content.get("action_items", [])
        cc = content.get("cc", [])

        # MEMORANDUM header
        memo_header = doc.add_paragraph()
        memo_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
        memo_header.paragraph_format.space_before = Pt(12)
        memo_header.paragraph_format.space_after = Pt(18)
        run_memo = memo_header.add_run("MEMORANDUM")
        run_memo.font.name = styler.heading_font
        run_memo.font.size = Pt(24)
        run_memo.font.color.rgb = styler.primary
        run_memo.font.bold = True

        # Decorative top border
        memo_ppr = memo_header._element.get_or_add_pPr()
        memo_border = (
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:top w:val="single" w:sz="12" w:space="4" w:color="{styler.primary_hex}"/>'
            f'  <w:bottom w:val="single" w:sz="12" w:space="4" w:color="{styler.primary_hex}"/>'
            f'</w:pBdr>'
        )
        memo_ppr.append(parse_xml(memo_border))

        # TO/FROM/DATE/RE fields as table
        fields_data = [
            ["TO:", to],
            ["FROM:", from_name],
            ["DATE:", date_str],
            ["RE:", subject],
        ]

        field_table = doc.add_table(rows=4, cols=2)
        field_table.alignment = WD_TABLE_ALIGNMENT.LEFT
        field_table.style = "Table Grid"

        # Remove borders from the field table for cleaner look
        tbl = field_table._tbl
        tbl_pr = tbl.tblPr if tbl.tblPr is not None else parse_xml(f'<w:tblPr {nsdecls("w")}/>')
        borders_xml = (
            f'<w:tblBorders {nsdecls("w")}>'
            f'  <w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            f'  <w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            f'  <w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            f'  <w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            f'  <w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            f'  <w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
            f'</w:tblBorders>'
        )
        existing_borders = tbl_pr.find(qn("w:tblBorders"))
        if existing_borders is not None:
            tbl_pr.remove(existing_borders)
        tbl_pr.append(parse_xml(borders_xml))

        for row_idx, (label, value) in enumerate(fields_data):
            # Label cell
            label_cell = field_table.rows[row_idx].cells[0]
            label_para = label_cell.paragraphs[0] if label_cell.paragraphs else label_cell.add_paragraph()
            label_para.clear()
            run_label = label_para.add_run(label)
            run_label.font.name = styler.heading_font
            run_label.font.size = Pt(11)
            run_label.font.bold = True
            run_label.font.color.rgb = styler.primary
            label_cell.width = Inches(1.0)

            # Value cell
            value_cell = field_table.rows[row_idx].cells[1]
            value_para = value_cell.paragraphs[0] if value_cell.paragraphs else value_cell.add_paragraph()
            value_para.clear()
            run_val = value_para.add_run(str(value))
            run_val.font.name = styler.body_font
            run_val.font.size = Pt(11)
            run_val.font.color.rgb = styler.text_color

        doc.add_paragraph()  # spacing

        # Separator line
        sep = doc.add_paragraph()
        sep.paragraph_format.space_before = Pt(4)
        sep.paragraph_format.space_after = Pt(12)
        sep_ppr = sep._element.get_or_add_pPr()
        sep_border = (
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:bottom w:val="single" w:sz="6" w:space="1" w:color="{styler.primary_hex}"/>'
            f'</w:pBdr>'
        )
        sep_ppr.append(parse_xml(sep_border))
        sep.add_run(" ")

        # Body paragraphs
        for para_text in body_paragraphs:
            self._add_body_text(doc, str(para_text), styler)

        # Action Items
        if action_items:
            doc.add_paragraph()  # spacing
            doc.add_heading("Action Items", level=2)
            for idx, item in enumerate(action_items, 1):
                ai_para = doc.add_paragraph()
                ai_para.paragraph_format.left_indent = Inches(0.3)
                ai_para.paragraph_format.space_after = Pt(4)

                # Checkbox-style prefix
                run_check = ai_para.add_run(f"[ ]  {idx}. ")
                run_check.font.name = styler.body_font
                run_check.font.size = Pt(11)
                run_check.font.color.rgb = styler.primary
                run_check.font.bold = True

                run_item = ai_para.add_run(str(item))
                run_item.font.name = styler.body_font
                run_item.font.size = Pt(11)
                run_item.font.color.rgb = styler.text_color

        # CC line
        if cc:
            doc.add_paragraph()  # spacing
            cc_para = doc.add_paragraph()
            cc_para.paragraph_format.space_before = Pt(12)
            run_cc_label = cc_para.add_run("CC: ")
            run_cc_label.font.name = styler.heading_font
            run_cc_label.font.size = Pt(10)
            run_cc_label.font.bold = True
            run_cc_label.font.color.rgb = styler.dark_gray
            run_cc_value = cc_para.add_run(", ".join(str(c) for c in cc))
            run_cc_value.font.name = styler.body_font
            run_cc_value.font.size = Pt(10)
            run_cc_value.font.color.rgb = styler.dark_gray

        return doc

    # ------------------------------------------------------------------
    # 8. Battle Card
    # ------------------------------------------------------------------

    def build_battle_card(self, content: dict) -> Document:
        """Build a competitive positioning battle card.

        Expected content keys:
            - title (str)
            - product_name (str)
            - at_a_glance (str): Summary description
            - competitors (list[list[str]]): Comparison table (header + data)
            - differentiators (list[str])
            - objection_responses (list[dict]): Each with ``objection``,
              ``response``
            - talk_track (str): Elevator pitch text
            - pricing_table (list[list[str]]): Pricing comparison data

        Returns:
            A completed Document object.
        """
        doc, styler = self._init_document()

        title = content.get("title", "Battle Card")
        product_name = content.get("product_name", "")
        at_a_glance = content.get("at_a_glance", "")
        competitors = content.get("competitors", [])
        differentiators = content.get("differentiators", [])
        objection_responses = content.get("objection_responses", [])
        talk_track = content.get("talk_track", "")
        pricing_table = content.get("pricing_table", [])

        # Product / service name header
        title_para = doc.add_paragraph(title, style="Title")
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        if product_name:
            product_para = doc.add_paragraph()
            product_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            product_para.paragraph_format.space_before = Pt(0)
            product_para.paragraph_format.space_after = Pt(6)
            run_prod = product_para.add_run(product_name)
            run_prod.font.name = styler.heading_font
            run_prod.font.size = Pt(16)
            run_prod.font.color.rgb = styler.secondary
            run_prod.font.bold = True

        # Separator
        sep = doc.add_paragraph()
        sep.paragraph_format.space_before = Pt(2)
        sep.paragraph_format.space_after = Pt(8)
        sep_ppr = sep._element.get_or_add_pPr()
        sep_border = (
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:bottom w:val="single" w:sz="6" w:space="1" w:color="{styler.accent_hex}"/>'
            f'</w:pBdr>'
        )
        sep_ppr.append(parse_xml(sep_border))
        sep.add_run(" ")

        # "At a Glance" summary box
        if at_a_glance:
            doc.add_heading("At a Glance", level=2)
            styler.add_callout_box(at_a_glance, callout_type="info")

        # Competitive Comparison Table
        if competitors:
            doc.add_heading("Competitive Comparison", level=2)
            styler.add_branded_table(competitors, has_header=True)
            doc.add_paragraph()

        # Key Differentiators
        if differentiators:
            doc.add_heading("Key Differentiators", level=2)
            for diff in differentiators:
                diff_para = doc.add_paragraph()
                diff_para.paragraph_format.left_indent = Inches(0.3)
                diff_para.paragraph_format.space_after = Pt(4)

                run_bullet = diff_para.add_run("\u2713  ")  # Checkmark
                run_bullet.font.name = styler.heading_font
                run_bullet.font.size = Pt(11)
                run_bullet.font.color.rgb = hex_to_rgb("28A745")  # green
                run_bullet.font.bold = True

                run_text = diff_para.add_run(str(diff))
                run_text.font.name = styler.body_font
                run_text.font.size = Pt(11)
                run_text.font.color.rgb = styler.text_color

        # Objection Handling (2-column table)
        if objection_responses:
            doc.add_heading("Objection Handling", level=2)

            obj_data = [["Objection", "Response"]]
            for obj_resp in objection_responses:
                objection = obj_resp.get("objection", "")
                response = obj_resp.get("response", "")
                obj_data.append([str(objection), str(response)])

            styler.add_branded_table(obj_data, has_header=True)
            doc.add_paragraph()

        # Talk Track / Elevator Pitch
        if talk_track:
            doc.add_heading("Talk Track", level=2)
            talk_para = doc.add_paragraph(style="Intense Quote")
            run_talk = talk_para.add_run(talk_track)
            run_talk.font.name = styler.body_font
            run_talk.font.size = Pt(11)
            run_talk.font.color.rgb = styler.primary

        # Pricing Comparison
        if pricing_table:
            doc.add_heading("Pricing Comparison", level=2)
            styler.add_branded_table(pricing_table, has_header=True)

        return doc

    # ------------------------------------------------------------------
    # 9. Capability Overview
    # ------------------------------------------------------------------

    def build_capability_overview(self, content: dict) -> Document:
        """Build a one-page capability overview document.

        Expected content keys:
            - title (str)
            - tagline (str): Value proposition
            - capabilities (list[dict]): Each with ``name``, ``description``
            - statistics (list[dict]): Each with ``label``, ``value``
            - contact: { name, email, phone }

        Returns:
            A completed Document object.
        """
        doc, styler = self._init_document()

        title = content.get("title", "Capability Overview")
        tagline = content.get("tagline", "")
        capabilities = content.get("capabilities", [])
        statistics = content.get("statistics", [])
        contact = content.get("contact", {})

        # Company logo + name header
        logo_path = styler._find_logo_path()
        if logo_path:
            logo_para = doc.add_paragraph()
            logo_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            logo_para.paragraph_format.space_before = Pt(0)
            logo_para.paragraph_format.space_after = Pt(4)
            try:
                run_logo = logo_para.add_run()
                run_logo.add_picture(logo_path, height=Inches(0.7))
            except Exception as exc:
                logger.warning("Could not insert logo: %s", exc)

        # Company name
        if self.company_name:
            name_para = doc.add_paragraph()
            name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            name_para.paragraph_format.space_before = Pt(2)
            name_para.paragraph_format.space_after = Pt(4)
            run_name = name_para.add_run(self.company_name)
            run_name.font.name = styler.heading_font
            run_name.font.size = Pt(20)
            run_name.font.color.rgb = styler.primary
            run_name.font.bold = True

        # Title
        title_para = doc.add_paragraph(title, style="Title")
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Tagline / value proposition
        if tagline:
            tagline_para = doc.add_paragraph()
            tagline_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            tagline_para.paragraph_format.space_before = Pt(0)
            tagline_para.paragraph_format.space_after = Pt(12)
            run_tag = tagline_para.add_run(tagline)
            run_tag.font.name = styler.body_font
            run_tag.font.size = Pt(13)
            run_tag.font.color.rgb = styler.secondary
            run_tag.font.italic = True

        # Separator
        sep = doc.add_paragraph()
        sep.paragraph_format.space_before = Pt(2)
        sep.paragraph_format.space_after = Pt(8)
        sep_ppr = sep._element.get_or_add_pPr()
        sep_border = (
            f'<w:pBdr {nsdecls("w")}>'
            f'  <w:bottom w:val="single" w:sz="6" w:space="1" w:color="{styler.primary_hex}"/>'
            f'</w:pBdr>'
        )
        sep_ppr.append(parse_xml(sep_border))
        sep.add_run(" ")

        # Capabilities in a 2-column layout (simulated with a table)
        if capabilities:
            doc.add_heading("Our Capabilities", level=2)

            # Arrange capabilities into 2-column rows
            num_caps = len(capabilities)
            rows_needed = (num_caps + 1) // 2

            cap_table = doc.add_table(rows=rows_needed, cols=2)
            cap_table.alignment = WD_TABLE_ALIGNMENT.CENTER

            # Remove table borders for card-like look
            tbl = cap_table._tbl
            tbl_pr = tbl.tblPr if tbl.tblPr is not None else parse_xml(f'<w:tblPr {nsdecls("w")}/>')
            borders_xml = (
                f'<w:tblBorders {nsdecls("w")}>'
                f'  <w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                f'  <w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                f'  <w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                f'  <w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                f'  <w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                f'  <w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                f'</w:tblBorders>'
            )
            existing_borders = tbl_pr.find(qn("w:tblBorders"))
            if existing_borders is not None:
                tbl_pr.remove(existing_borders)
            tbl_pr.append(parse_xml(borders_xml))

            for cap_idx, cap in enumerate(capabilities):
                row_idx = cap_idx // 2
                col_idx = cap_idx % 2
                cell = cap_table.rows[row_idx].cells[col_idx]

                # Clear the cell
                for para in cell.paragraphs:
                    para.clear()

                # Capability name (heading)
                name_para = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
                name_para.clear()
                name_para.paragraph_format.space_before = Pt(8)
                name_para.paragraph_format.space_after = Pt(2)
                run_cap_name = name_para.add_run(cap.get("name", ""))
                run_cap_name.font.name = styler.heading_font
                run_cap_name.font.size = Pt(12)
                run_cap_name.font.color.rgb = styler.primary
                run_cap_name.font.bold = True

                # Capability description
                desc_para = cell.add_paragraph()
                desc_para.paragraph_format.space_after = Pt(8)
                run_desc = desc_para.add_run(cap.get("description", ""))
                run_desc.font.name = styler.body_font
                run_desc.font.size = Pt(10)
                run_desc.font.color.rgb = styler.text_color

                # Add subtle background shading
                cell_shading = parse_xml(
                    f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" '
                    f'w:fill="{styler.primary_light_hex}"/>'
                )
                cell._element.get_or_add_tcPr().append(cell_shading)

            doc.add_paragraph()  # spacing

        # Key Statistics row
        if statistics:
            doc.add_heading("By the Numbers", level=2)

            # Build statistics as a single-row table for visual impact
            stat_count = len(statistics)
            stat_table = doc.add_table(rows=2, cols=stat_count)
            stat_table.alignment = WD_TABLE_ALIGNMENT.CENTER

            # Remove borders
            stat_tbl = stat_table._tbl
            stat_pr = stat_tbl.tblPr if stat_tbl.tblPr is not None else parse_xml(
                f'<w:tblPr {nsdecls("w")}/>'
            )
            stat_borders = (
                f'<w:tblBorders {nsdecls("w")}>'
                f'  <w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                f'  <w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                f'  <w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                f'  <w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                f'  <w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                f'  <w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
                f'</w:tblBorders>'
            )
            existing_stat_b = stat_pr.find(qn("w:tblBorders"))
            if existing_stat_b is not None:
                stat_pr.remove(existing_stat_b)
            stat_pr.append(parse_xml(stat_borders))

            for s_idx, stat in enumerate(statistics):
                # Value row (large, bold)
                val_cell = stat_table.rows[0].cells[s_idx]
                val_para = val_cell.paragraphs[0] if val_cell.paragraphs else val_cell.add_paragraph()
                val_para.clear()
                val_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run_val = val_para.add_run(str(stat.get("value", "")))
                run_val.font.name = styler.heading_font
                run_val.font.size = Pt(22)
                run_val.font.color.rgb = styler.primary
                run_val.font.bold = True

                # Label row (smaller, secondary)
                label_cell = stat_table.rows[1].cells[s_idx]
                label_para = label_cell.paragraphs[0] if label_cell.paragraphs else label_cell.add_paragraph()
                label_para.clear()
                label_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run_label = label_para.add_run(str(stat.get("label", "")))
                run_label.font.name = styler.body_font
                run_label.font.size = Pt(10)
                run_label.font.color.rgb = styler.dark_gray

            doc.add_paragraph()  # spacing

        # Contact Information
        if contact:
            doc.add_heading("Contact Us", level=2)
            contact_name = contact.get("name", "")
            contact_email = contact.get("email", "")
            contact_phone = contact.get("phone", "")

            contact_para = doc.add_paragraph()
            contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            contact_para.paragraph_format.space_before = Pt(8)

            if contact_name:
                run_c_name = contact_para.add_run(contact_name)
                run_c_name.font.name = styler.heading_font
                run_c_name.font.size = Pt(12)
                run_c_name.font.color.rgb = styler.text_color
                run_c_name.font.bold = True
                contact_para.add_run("\n")

            if contact_email:
                run_email = contact_para.add_run(contact_email)
                run_email.font.name = styler.body_font
                run_email.font.size = Pt(11)
                run_email.font.color.rgb = styler.primary
                contact_para.add_run("  |  ")

            if contact_phone:
                run_phone = contact_para.add_run(contact_phone)
                run_phone.font.name = styler.body_font
                run_phone.font.size = Pt(11)
                run_phone.font.color.rgb = styler.text_color

        return doc

    # ------------------------------------------------------------------
    # 10. Proposal
    # ------------------------------------------------------------------

    def build_proposal(self, content: dict) -> Document:
        """Build a full business proposal document.

        Expected content keys:
            - title (str)
            - client_name (str)
            - executive_summary (str)
            - needs_analysis (str)
            - proposed_solution (str)
            - scope_items (list[list[str]]): Scope of work table
            - timeline (list[list[str]]): Timeline / milestones table
            - pricing (list[list[str]]): Investment / pricing table
            - team_members (list[dict]): Each with ``name``, ``role``, ``bio``
            - terms (str)
            - next_steps (list[str])

        Returns:
            A completed Document object.
        """
        doc, styler = self._init_document()

        title = content.get("title", "Business Proposal")
        client_name = content.get("client_name", "")
        executive_summary = content.get("executive_summary", "")
        needs_analysis = content.get("needs_analysis", "")
        proposed_solution = content.get("proposed_solution", "")
        scope_items = content.get("scope_items", [])
        timeline = content.get("timeline", [])
        pricing = content.get("pricing", [])
        team_members = content.get("team_members", [])
        terms = content.get("terms", "")
        next_steps = content.get("next_steps", [])

        # Cover page
        subtitle = f"Prepared for {client_name}" if client_name else ""
        styler.create_cover_page(
            title=title,
            subtitle=subtitle,
            author=self.company_name,
            date_str=datetime.now().strftime("%B %d, %Y"),
        )
        styler.add_page_break()

        # Table of Contents
        doc.add_heading("Table of Contents", level=1)
        toc_entries = [
            "1. Executive Summary",
            "2. Understanding of Needs",
            "3. Proposed Solution",
            "4. Scope of Work",
            "5. Timeline & Milestones",
            "6. Investment",
            "7. Team & Qualifications",
            "8. Terms & Conditions",
            "9. Next Steps",
        ]
        for entry in toc_entries:
            toc_para = doc.add_paragraph()
            toc_para.paragraph_format.space_after = Pt(3)
            toc_para.paragraph_format.left_indent = Inches(0.3)
            run_entry = toc_para.add_run(entry)
            run_entry.font.name = styler.body_font
            run_entry.font.size = Pt(11)
            run_entry.font.color.rgb = styler.primary

        styler.add_page_break()

        # 1. Executive Summary
        doc.add_heading("1. Executive Summary", level=1)
        self._add_body_text(doc, executive_summary, styler)

        if client_name:
            styler.add_callout_box(
                f"This proposal has been prepared exclusively for {client_name}.",
                callout_type="info",
            )

        # 2. Understanding of Needs
        doc.add_heading("2. Understanding of Needs", level=1)
        self._add_body_text(doc, needs_analysis, styler)

        # 3. Proposed Solution
        doc.add_heading("3. Proposed Solution", level=1)
        self._add_body_text(doc, proposed_solution, styler)

        # 4. Scope of Work
        if scope_items:
            doc.add_heading("4. Scope of Work", level=1)
            styler.add_branded_table(scope_items, has_header=True)
            doc.add_paragraph()

        styler.add_page_break()

        # 5. Timeline & Milestones
        if timeline:
            doc.add_heading("5. Timeline & Milestones", level=1)
            styler.add_branded_table(timeline, has_header=True)
            doc.add_paragraph()

        # 6. Investment / Pricing
        if pricing:
            doc.add_heading("6. Investment", level=1)
            intro_para = doc.add_paragraph(
                "The following table outlines the investment required for this engagement."
            )
            intro_para.paragraph_format.space_after = Pt(8)
            styler.add_branded_table(pricing, has_header=True)

            # Total row callout (if identifiable)
            if len(pricing) > 1:
                last_row = pricing[-1]
                if last_row and any("total" in str(c).lower() for c in last_row):
                    total_values = [str(c) for c in last_row if c]
                    styler.add_callout_box(
                        "  |  ".join(total_values),
                        callout_type="info",
                    )
            doc.add_paragraph()

        # 7. Team & Qualifications
        if team_members:
            doc.add_heading("7. Team & Qualifications", level=1)
            intro = doc.add_paragraph(
                "Our team brings deep expertise and a proven track record of delivering results."
            )
            intro.paragraph_format.space_after = Pt(8)

            for member in team_members:
                member_name = member.get("name", "")
                member_role = member.get("role", "")
                member_bio = member.get("bio", "")

                # Member name heading
                name_para = doc.add_paragraph()
                name_para.paragraph_format.space_before = Pt(10)
                name_para.paragraph_format.space_after = Pt(2)
                run_member_name = name_para.add_run(member_name)
                run_member_name.font.name = styler.heading_font
                run_member_name.font.size = Pt(12)
                run_member_name.font.color.rgb = styler.primary
                run_member_name.font.bold = True

                # Role
                if member_role:
                    role_para = doc.add_paragraph()
                    role_para.paragraph_format.space_before = Pt(0)
                    role_para.paragraph_format.space_after = Pt(4)
                    run_role = role_para.add_run(member_role)
                    run_role.font.name = styler.body_font
                    run_role.font.size = Pt(10)
                    run_role.font.color.rgb = styler.secondary
                    run_role.font.italic = True

                # Bio
                if member_bio:
                    self._add_body_text(doc, member_bio, styler)

            doc.add_paragraph()

        styler.add_page_break()

        # 8. Terms & Conditions
        doc.add_heading("8. Terms & Conditions", level=1)
        if terms:
            self._add_body_text(doc, terms, styler)
        else:
            default_terms = (
                "This proposal is valid for 30 days from the date of issue. "
                "All pricing is subject to change after this period. Payment terms, "
                "intellectual property rights, confidentiality obligations, and "
                "limitation of liability are governed by the master service agreement "
                "to be executed between the parties prior to commencement of work."
            )
            self._add_body_text(doc, default_terms, styler)

        # 9. Next Steps
        doc.add_heading("9. Next Steps", level=1)
        if next_steps:
            for idx, step in enumerate(next_steps, 1):
                step_para = doc.add_paragraph()
                step_para.paragraph_format.space_after = Pt(6)

                run_num = step_para.add_run(f"{idx}. ")
                run_num.font.name = styler.heading_font
                run_num.font.size = Pt(11)
                run_num.font.color.rgb = styler.primary
                run_num.font.bold = True

                run_text = step_para.add_run(str(step))
                run_text.font.name = styler.body_font
                run_text.font.size = Pt(11)
                run_text.font.color.rgb = styler.text_color
        else:
            default_next = doc.add_paragraph(
                "We look forward to discussing this proposal with you. "
                "Please do not hesitate to reach out with any questions."
            )
            default_next.paragraph_format.space_after = Pt(8)

        # Closing
        doc.add_paragraph()
        closing_para = doc.add_paragraph()
        closing_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        closing_para.paragraph_format.space_before = Pt(24)
        run_closing = closing_para.add_run("We look forward to partnering with you.")
        run_closing.font.name = styler.heading_font
        run_closing.font.size = Pt(14)
        run_closing.font.color.rgb = styler.primary
        run_closing.font.italic = True

        # Company signature line
        if self.company_name:
            sig_para = doc.add_paragraph()
            sig_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            sig_para.paragraph_format.space_before = Pt(24)

            # Signature line
            sig_line = sig_para.add_run("_" * 40)
            sig_line.font.color.rgb = RGBColor(200, 200, 200)
            sig_para.add_run("\n")
            run_sig_name = sig_para.add_run(self.company_name)
            run_sig_name.font.name = styler.heading_font
            run_sig_name.font.size = Pt(11)
            run_sig_name.font.color.rgb = styler.primary
            run_sig_name.font.bold = True

        return doc


# ---------------------------------------------------------------------------
# DocumentTemplateInfo
# ---------------------------------------------------------------------------

class DocumentTemplateInfo:
    """Provides metadata about available document templates.

    Use this class to query available templates, their descriptions,
    typical page counts, and intended use cases.
    """

    @staticmethod
    def list_templates() -> dict:
        """Return the full template metadata registry."""
        return DOCUMENT_TEMPLATES

    @staticmethod
    def get_template_info(doc_type: str) -> Optional[dict]:
        """Return metadata for a specific template type.

        Args:
            doc_type: Template type identifier.

        Returns:
            Template metadata dict or None if not found.
        """
        return DOCUMENT_TEMPLATES.get(doc_type)

    @staticmethod
    def get_template_names() -> list[str]:
        """Return a sorted list of all template type identifiers."""
        return sorted(DOCUMENT_TEMPLATES.keys())

    @staticmethod
    def get_template_descriptions() -> dict[str, str]:
        """Return a mapping of template type to human-readable description."""
        return {
            key: info["description"]
            for key, info in DOCUMENT_TEMPLATES.items()
        }

    @staticmethod
    def get_use_cases(doc_type: str) -> list[str]:
        """Return the list of use cases for a given template type.

        Args:
            doc_type: Template type identifier.

        Returns:
            List of use case strings, or empty list if not found.
        """
        info = DOCUMENT_TEMPLATES.get(doc_type)
        if info:
            return info.get("use_cases", [])
        return []

    @staticmethod
    def search_templates(keyword: str) -> list[dict]:
        """Search templates by keyword in name, description, or use cases.

        Args:
            keyword: Search term (case-insensitive).

        Returns:
            List of matching template metadata dicts with ``type`` key added.
        """
        keyword_lower = keyword.lower()
        results = []
        for doc_type, info in DOCUMENT_TEMPLATES.items():
            searchable = (
                info["name"].lower()
                + " "
                + info["description"].lower()
                + " "
                + " ".join(uc.lower() for uc in info.get("use_cases", []))
            )
            if keyword_lower in searchable:
                result = dict(info)
                result["type"] = doc_type
                results.append(result)
        return results
