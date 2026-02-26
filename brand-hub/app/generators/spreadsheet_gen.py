"""
Brand Intelligence Content Hub - Spreadsheet Generator (openpyxl)

Creates branded Excel reports with formatted data tables, charts,
and KPI dashboards.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.drawing.image import Image as XlImage

from app.config import BASE_DIR, BRAND_ASSETS_DIR, REPORTS_DIR, EXPORTS_DIR, LOGOS_DIR

logger = logging.getLogger(__name__)


class BrandedSpreadsheetGenerator:
    """Generates branded Excel workbooks from structured content JSON.

    Supports: data_table, kpi_dashboard, comparison_report, financial_summary.
    """

    STATUS_GREEN = "22B14C"
    STATUS_RED = "ED1C24"
    STATUS_YELLOW = "FFC90E"

    def __init__(self, brand_config: Optional[dict] = None):
        self.brand_config: dict = brand_config or self._load_brand_config()
        colors_cfg = self.brand_config.get("colors", {})
        self.primary = self._hex_to_openpyxl(colors_cfg.get("primary", "#0066CC"))
        self.secondary = self._hex_to_openpyxl(colors_cfg.get("secondary", "#004499"))
        self.background = self._hex_to_openpyxl(colors_cfg.get("background", "#FFFFFF"))
        self.accent = self._hex_to_openpyxl(colors_cfg.get("accent", "#FF6600"))
        self.text_color = self._hex_to_openpyxl(colors_cfg.get("text", "#333333"))
        fonts_cfg = self.brand_config.get("fonts", {})
        self.heading_font = fonts_cfg.get("heading", "Arial")
        self.body_font = fonts_cfg.get("body", "Calibri")
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

    @staticmethod
    def _hex_to_openpyxl(hex_color: str) -> str:
        """Strip ``#`` prefix and return six-char uppercase hex for openpyxl fills."""
        cleaned = hex_color.lstrip("#").upper()
        return cleaned if len(cleaned) == 6 else "000000"

    def _find_logo(self) -> Optional[str]:
        """Return path to the first logo image (PNG/JPG) in ``brand_assets/logos/``."""
        if not LOGOS_DIR.exists():
            return None
        for ext in ("*.png", "*.jpg", "*.jpeg"):
            logos = list(LOGOS_DIR.glob(ext))
            if logos:
                return str(logos[0])
        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, content: dict, report_type: str = "data_table",
                 title: str = "", save_path: Optional[str] = None) -> str:
        """Generate a branded Excel workbook and save it to disk. Returns file path."""
        if not title:
            title = content.get("title", report_type.replace("_", " ").title())
        builders = {
            "data_table": self.build_data_table,
            "kpi_dashboard": self.build_kpi_dashboard,
            "comparison_report": self.build_comparison_report,
            "financial_summary": self.build_financial_summary,
        }
        builder = builders.get(report_type)
        if builder is None:
            logger.warning("Unknown report type '%s', falling back to data_table", report_type)
            builder = self.build_data_table
        wb = builder(content)
        return self._save_workbook(wb, title, save_path)

    def _save_workbook(self, wb: Workbook, title: str, save_path: Optional[str]) -> str:
        """Persist a workbook to disk and return its path."""
        if save_path is None:
            safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in title).strip()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = str(REPORTS_DIR / f"{safe}_{ts}.xlsx")
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        wb.save(save_path)
        logger.info("Workbook saved to %s", save_path)
        return save_path

    # ==================================================================
    # Builder: data_table
    # ==================================================================

    def build_data_table(self, content: dict) -> Workbook:
        """Single-sheet data table with logo, title, headers, data rows, optional totals.

        Content: { title, subtitle, headers: [], rows: [[]], totals_row: [] }
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Report"

        title = content.get("title", "Data Report")
        subtitle = content.get("subtitle", "")
        headers = content.get("headers", [])
        rows = content.get("rows", [])
        totals_row = content.get("totals_row", [])
        num_cols = max(len(headers), 1)
        end_col = get_column_letter(num_cols)

        self._add_logo(ws, "A1")

        # Title row (merged, row 4 to leave logo space)
        cr = 4
        ws.merge_cells(f"A{cr}:{end_col}{cr}")
        tc = ws.cell(row=cr, column=1, value=title)
        tc.font = Font(name=self.heading_font, size=16, bold=True, color=self.primary)
        tc.alignment = Alignment(horizontal="center", vertical="center")
        cr += 1

        # Subtitle / date row
        ws.merge_cells(f"A{cr}:{end_col}{cr}")
        if subtitle:
            sc = ws.cell(row=cr, column=1, value=subtitle)
            sc.font = Font(name=self.body_font, size=11, italic=True, color=self.secondary)
            sc.alignment = Alignment(horizontal="center")
        else:
            dc = ws.cell(row=cr, column=1, value=datetime.now().strftime("Generated %B %d, %Y"))
            dc.font = Font(name=self.body_font, size=10, italic=True, color="888888")
            dc.alignment = Alignment(horizontal="center")
        cr += 2  # blank row

        # Header row
        for ci, h in enumerate(headers, 1):
            ws.cell(row=cr, column=ci, value=h)
        self._style_header_row(ws, cr, num_cols)
        cr += 1

        # Data rows
        data_start = cr
        for rd in rows:
            for ci, v in enumerate(rd, 1):
                ws.cell(row=cr, column=ci, value=v)
            cr += 1
        if data_start <= cr - 1:
            self._style_data_rows(ws, data_start, cr - 1, num_cols)

        # Totals row
        if totals_row:
            border = Border(top=Side(style="thin", color=self.primary))
            for ci, v in enumerate(totals_row, 1):
                cell = ws.cell(row=cr, column=ci, value=v)
                cell.font = Font(name=self.body_font, size=11, bold=True, color=self.text_color)
                cell.border = border

        self._auto_fit_columns(ws)
        return wb

    # ==================================================================
    # Builder: kpi_dashboard
    # ==================================================================

    def build_kpi_dashboard(self, content: dict) -> Workbook:
        """Multi-sheet KPI dashboard with status cards, detail table, optional chart.

        Content: { title, kpis: [{ name, value, target, unit }],
                   detail_data: { headers, rows }, chart_config: { type, title } }
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Dashboard"

        title = content.get("title", "KPI Dashboard")
        kpis = content.get("kpis", [])

        # Title area
        self._add_logo(ws, "A1")
        ws.merge_cells("A4:F4")
        tc = ws.cell(row=4, column=1, value=title)
        tc.font = Font(name=self.heading_font, size=18, bold=True, color=self.primary)
        tc.alignment = Alignment(horizontal="center")
        ws.merge_cells("A5:F5")
        ws.cell(row=5, column=1, value=datetime.now().strftime("As of %B %d, %Y")).font = Font(
            name=self.body_font, size=10, italic=True, color="888888")
        ws.cell(row=5, column=1).alignment = Alignment(horizontal="center")

        # KPI header row
        kpi_row = 7
        for ci, lbl in enumerate(["Metric", "Value", "Target", "Status"], 1):
            c = ws.cell(row=kpi_row, column=ci, value=lbl)
            c.font = Font(name=self.heading_font, size=11, bold=True, color="FFFFFF")
            c.fill = PatternFill(start_color=self.primary, end_color=self.primary, fill_type="solid")
            c.alignment = Alignment(horizontal="center")

        # KPI data rows
        currency_units = ("$", "\u00a3", "\u20ac")
        for idx, kpi in enumerate(kpis):
            row = kpi_row + 1 + idx
            name, value, target = kpi.get("name", ""), kpi.get("value", 0), kpi.get("target", 0)
            unit = kpi.get("unit", "")
            fmt = (lambda u, v: f"{u}{v}") if unit in currency_units else (lambda u, v: f"{v} {u}".strip())
            ratio = (value / target) if target else 1.0
            if ratio >= 1.0:
                status_text, status_clr = "On Target", self.STATUS_GREEN
            elif ratio >= 0.9:
                status_text, status_clr = "Near Target", self.STATUS_YELLOW
            else:
                status_text, status_clr = "Below Target", self.STATUS_RED

            ws.cell(row=row, column=1, value=name).font = Font(
                name=self.body_font, size=11, bold=True, color=self.text_color)
            for col, val in [(2, fmt(unit, value)), (3, fmt(unit, target))]:
                ws.cell(row=row, column=col, value=val).font = Font(
                    name=self.body_font, size=11, color=self.text_color)
                ws.cell(row=row, column=col).alignment = Alignment(horizontal="center")
            sc = ws.cell(row=row, column=4, value=status_text)
            sc.font = Font(name=self.body_font, size=11, bold=True, color=status_clr)
            sc.fill = PatternFill(start_color=status_clr, end_color=status_clr, fill_type="solid")
            sc.alignment = Alignment(horizontal="center")
            if idx % 2 == 0:
                for c in range(1, 4):
                    ws.cell(row=row, column=c).fill = PatternFill(
                        start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")
        self._auto_fit_columns(ws)

        # Details sheet
        detail = content.get("detail_data", {})
        if detail:
            wd = wb.create_sheet("Details")
            dh = detail.get("headers", [])
            dr = detail.get("rows", [])
            nc = max(len(dh), 1)
            for ci, h in enumerate(dh, 1):
                wd.cell(row=1, column=ci, value=h)
            self._style_header_row(wd, 1, nc)
            for ri, rd in enumerate(dr, 2):
                for ci, v in enumerate(rd, 1):
                    wd.cell(row=ri, column=ci, value=v)
            if dr:
                self._style_data_rows(wd, 2, 1 + len(dr), nc)
            self._auto_fit_columns(wd)

            # Optional chart sheet
            cc = content.get("chart_config")
            if cc:
                wc = wb.create_sheet("Chart")
                self._add_chart(wc, cc, wd, anchor="B2")

        return wb

    # ==================================================================
    # Builder: comparison_report
    # ==================================================================

    def build_comparison_report(self, content: dict) -> Workbook:
        """Comparison matrix with colour-coded scores and summary section.

        Content: { title, criteria: [], items: [{ name, scores: {} }], summary }
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Comparison"

        title = content.get("title", "Comparison Report")
        criteria = content.get("criteria", [])
        items = content.get("items", [])
        summary = content.get("summary", "")
        num_cols = 1 + len(criteria)
        end_col = get_column_letter(num_cols)

        self._add_logo(ws, "A1")
        cr = 4
        ws.merge_cells(f"A{cr}:{end_col}{cr}")
        tc = ws.cell(row=cr, column=1, value=title)
        tc.font = Font(name=self.heading_font, size=16, bold=True, color=self.primary)
        tc.alignment = Alignment(horizontal="center")
        cr += 2

        # Header: "Item" + criteria
        ws.cell(row=cr, column=1, value="Item")
        for ci, crit in enumerate(criteria, 2):
            ws.cell(row=cr, column=ci, value=crit)
        self._style_header_row(ws, cr, num_cols)
        cr += 1

        # Data rows with score colour coding
        data_start = cr
        for item in items:
            ws.cell(row=cr, column=1, value=item.get("name", "")).font = Font(
                name=self.body_font, size=11, bold=True, color=self.text_color)
            scores = item.get("scores", {})
            for ci, crit in enumerate(criteria, 2):
                score = scores.get(crit, "")
                cell = ws.cell(row=cr, column=ci, value=score)
                cell.alignment = Alignment(horizontal="center")
                if isinstance(score, (int, float)):
                    if score >= 8:
                        cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                        cell.font = Font(name=self.body_font, size=11, bold=True, color="006100")
                    elif score >= 5:
                        cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                        cell.font = Font(name=self.body_font, size=11, color="9C6500")
                    else:
                        cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                        cell.font = Font(name=self.body_font, size=11, color="9C0006")
                else:
                    cell.font = Font(name=self.body_font, size=11, color=self.text_color)
            cr += 1

        # Alternating shading on name column (score cells already coloured)
        for r in range(data_start, cr):
            if (r - data_start) % 2 == 0:
                ws.cell(row=r, column=1).fill = PatternFill(
                    start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")

        # Summary section
        if summary:
            cr += 1
            ws.merge_cells(f"A{cr}:{end_col}{cr}")
            ws.cell(row=cr, column=1, value="Summary").font = Font(
                name=self.heading_font, size=13, bold=True, color=self.secondary)
            cr += 1
            ws.merge_cells(f"A{cr}:{end_col}{cr}")
            sc = ws.cell(row=cr, column=1, value=summary)
            sc.font = Font(name=self.body_font, size=11, color=self.text_color)
            sc.alignment = Alignment(wrap_text=True, vertical="top")

        self._auto_fit_columns(ws)
        return wb

    # ==================================================================
    # Builder: financial_summary
    # ==================================================================

    def build_financial_summary(self, content: dict) -> Workbook:
        """Financial summary with category sections, currency formatting, change column, chart.

        Content: { title, period, periods: [], categories: [{ name,
                   line_items: [{ label, values: [] }] }],
                   chart_data: { type, series: [{ name, values }] } }
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Financial Summary"

        title = content.get("title", "Financial Summary")
        period = content.get("period", "")
        periods = content.get("periods", [])
        categories = content.get("categories", [])
        chart_data = content.get("chart_data")

        npc = len(periods)
        num_cols = 1 + npc + (1 if npc >= 2 else 0)
        end_col = get_column_letter(max(num_cols, 1))

        self._add_logo(ws, "A1")
        cr = 4
        ws.merge_cells(f"A{cr}:{end_col}{cr}")
        tc = ws.cell(row=cr, column=1, value=title)
        tc.font = Font(name=self.heading_font, size=16, bold=True, color=self.primary)
        tc.alignment = Alignment(horizontal="center")
        cr += 1
        if period:
            ws.merge_cells(f"A{cr}:{end_col}{cr}")
            pc = ws.cell(row=cr, column=1, value=period)
            pc.font = Font(name=self.body_font, size=11, italic=True, color=self.secondary)
            pc.alignment = Alignment(horizontal="center")
        cr += 2

        # Header row
        ws.cell(row=cr, column=1, value="")
        for pi, pl in enumerate(periods, 2):
            ws.cell(row=cr, column=pi, value=pl)
        if npc >= 2:
            ws.cell(row=cr, column=num_cols, value="Change")
        self._style_header_row(ws, cr, num_cols)
        cr += 1

        # Category sections
        cur_fmt = '#,##0'
        for cat in categories:
            ws.merge_cells(f"A{cr}:{end_col}{cr}")
            cc = ws.cell(row=cr, column=1, value=cat.get("name", ""))
            cc.font = Font(name=self.heading_font, size=12, bold=True, color=self.secondary)
            cc.fill = PatternFill(start_color="E8E8E8", end_color="E8E8E8", fill_type="solid")
            cr += 1

            cat_totals = [0] * npc
            for li in cat.get("line_items", []):
                label, values = li.get("label", ""), li.get("values", [])
                ws.cell(row=cr, column=1, value=f"  {label}").font = Font(
                    name=self.body_font, size=11, color=self.text_color)
                for vi, val in enumerate(values):
                    cell = ws.cell(row=cr, column=vi + 2, value=val)
                    cell.number_format = cur_fmt
                    cell.font = Font(name=self.body_font, size=11, color=self.text_color)
                    cell.alignment = Alignment(horizontal="right")
                    if vi < npc:
                        cat_totals[vi] += val if isinstance(val, (int, float)) else 0
                # Period-over-period change
                if npc >= 2 and len(values) >= 2:
                    fv = values[0] if isinstance(values[0], (int, float)) else 0
                    lv = values[-1] if isinstance(values[-1], (int, float)) else 0
                    if fv != 0:
                        pct = (lv - fv) / abs(fv)
                        chg = ws.cell(row=cr, column=num_cols, value=pct)
                        chg.number_format = '0.0%'
                        chg.alignment = Alignment(horizontal="center")
                        chg.font = Font(name=self.body_font, size=11,
                                        color="006100" if pct >= 0 else "9C0006")
                cr += 1

            # Category total row
            tb = Border(top=Side(style="thin", color=self.secondary))
            ws.cell(row=cr, column=1, value=f"Total {cat.get('name', '')}").font = Font(
                name=self.body_font, size=11, bold=True, color=self.text_color)
            ws.cell(row=cr, column=1).border = tb
            for ti, tv in enumerate(cat_totals):
                cell = ws.cell(row=cr, column=ti + 2, value=tv)
                cell.number_format = cur_fmt
                cell.font = Font(name=self.body_font, size=11, bold=True, color=self.text_color)
                cell.alignment = Alignment(horizontal="right")
                cell.border = tb
            if npc >= 2 and cat_totals[0] != 0:
                pct = (cat_totals[-1] - cat_totals[0]) / abs(cat_totals[0])
                chg = ws.cell(row=cr, column=num_cols, value=pct)
                chg.number_format = '0.0%'
                chg.alignment = Alignment(horizontal="center")
                chg.border = tb
                chg.font = Font(name=self.body_font, size=11, bold=True,
                                color="006100" if pct >= 0 else "9C0006")
            cr += 2

        self._auto_fit_columns(ws)

        # Chart sheet
        if chart_data and chart_data.get("series"):
            wcd = wb.create_sheet("Chart Data")
            sl = chart_data.get("series", [])
            for pi, pl in enumerate(periods, 2):
                wcd.cell(row=1, column=pi, value=pl)
            for si, s in enumerate(sl):
                r = si + 2
                wcd.cell(row=r, column=1, value=s.get("name", f"Series {si+1}"))
                for vi, v in enumerate(s.get("values", []), 2):
                    wcd.cell(row=r, column=vi, value=v)
            wcs = wb.create_sheet("Trends")
            cfg = {"type": chart_data.get("type", "line"), "title": chart_data.get("title", title)}
            self._add_chart_from_series(wcs, cfg, wcd, len(sl), npc, anchor="B2")

        return wb

    # ==================================================================
    # Shared styling helpers
    # ==================================================================

    def _add_logo(self, ws, cell: str = "A1") -> None:
        """Insert brand logo into worksheet. Silently skips if unavailable."""
        if not self.logo_path or not os.path.isfile(self.logo_path):
            return
        try:
            img = XlImage(self.logo_path)
            max_h = 100
            if img.height > max_h:
                ratio = max_h / img.height
                img.width = int(img.width * ratio)
                img.height = max_h
            ws.add_image(img, cell)
        except Exception as exc:
            logger.warning("Could not add logo to worksheet: %s", exc)

    def _style_header_row(self, ws, row_num: int, num_cols: int) -> None:
        """Apply primary-colour fill, white bold font, centred alignment to header row."""
        fill = PatternFill(start_color=self.primary, end_color=self.primary, fill_type="solid")
        font = Font(name=self.heading_font, size=11, bold=True, color="FFFFFF")
        align = Alignment(horizontal="center", vertical="center")
        border = Border(bottom=Side(style="thin", color=self.secondary))
        for col in range(1, num_cols + 1):
            c = ws.cell(row=row_num, column=col)
            c.fill, c.font, c.alignment, c.border = fill, font, align, border

    def _style_data_rows(self, ws, start_row: int, end_row: int, num_cols: int) -> None:
        """Apply alternating light-grey / white shading to data rows."""
        lt = PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")
        wh = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        bf = Font(name=self.body_font, size=11, color=self.text_color)
        for row in range(start_row, end_row + 1):
            fill = lt if (row - start_row) % 2 == 0 else wh
            for col in range(1, num_cols + 1):
                c = ws.cell(row=row, column=col)
                c.fill = fill
                if c.font == Font():
                    c.font = bf

    def _add_chart(self, ws, chart_config: dict, data_ws, anchor: str = "A1") -> None:
        """Add bar/line/pie chart to *ws* sourced from *data_ws* used range."""
        chart = self._make_chart(chart_config)
        max_row, max_col = data_ws.max_row or 1, data_ws.max_column or 1
        if max_row < 2 or max_col < 2:
            logger.warning("Not enough data for chart in '%s'", data_ws.title)
            return
        chart.add_data(Reference(data_ws, min_col=2, min_row=1, max_col=max_col, max_row=max_row),
                       titles_from_data=True)
        chart.set_categories(Reference(data_ws, min_col=1, min_row=2, max_row=max_row))
        ws.add_chart(chart, anchor)

    def _add_chart_from_series(self, ws, chart_config: dict, data_ws,
                                num_series: int, num_points: int, anchor: str = "A1") -> None:
        """Add chart where each series is a row (col 1 = name, cols 2+ = values)."""
        chart = self._make_chart(chart_config)
        chart.set_categories(Reference(data_ws, min_col=2, max_col=1 + num_points, min_row=1))
        for si in range(num_series):
            row = si + 2
            ref = Reference(data_ws, min_col=2, max_col=1 + num_points, min_row=row)
            chart.add_data(ref, from_rows=True, titles_from_data=False)
            chart.series[si].title = data_ws.cell(row=row, column=1).value or f"Series {si+1}"
        ws.add_chart(chart, anchor)

    @staticmethod
    def _make_chart(chart_config: dict):
        """Instantiate a chart object based on config type."""
        ct = chart_config.get("type", "bar").lower()
        chart = LineChart() if ct == "line" else PieChart() if ct == "pie" else BarChart()
        chart.title = chart_config.get("title", "")
        chart.style = 10
        chart.width = 20
        chart.height = 14
        return chart

    def _auto_fit_columns(self, ws) -> None:
        """Approximate column width auto-fit based on cell content length."""
        for col_cells in ws.columns:
            max_len = 0
            letter = None
            for cell in col_cells:
                if letter is None:
                    letter = get_column_letter(cell.column)
                try:
                    if cell.value is not None:
                        max_len = max(max_len, len(str(cell.value)))
                except (TypeError, AttributeError):
                    pass
            if letter:
                ws.column_dimensions[letter].width = min(max(max_len + 3, 10), 50)
