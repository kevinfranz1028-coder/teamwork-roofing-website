"""
PPTX extraction module for Brand Intelligence Content Hub.

Uses python-pptx to extract slide content, metadata, template properties,
and design theme information from PowerPoint presentations.
"""

import logging
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Emu

logger = logging.getLogger(__name__)


class PPTXParser:
    """Parses PPTX presentations into structured slide data with metadata.

    Extracts per-slide content (title, text, notes, shapes), document
    metadata, and template/theme information.
    """

    def parse(self, file_path: str) -> dict[str, Any]:
        """Parse a PPTX file and return structured content.

        Args:
            file_path: Path to the PPTX file.

        Returns:
            A dictionary containing:
                - slides: List of dicts, each with slide_number, title,
                  content (list of text strings), notes, and shapes
                  (list of shape info dicts).
                - metadata: Dict with title, author, and slide_count.
                - template_properties: Dict with slide_width, slide_height,
                  and layouts (list of layout name strings).

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file cannot be parsed as a PPTX.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PPTX file not found: {file_path}")

        if path.suffix.lower() not in (".pptx", ".pptm"):
            raise ValueError(f"File is not a PPTX presentation: {file_path}")

        try:
            prs = Presentation(file_path)
        except Exception as exc:
            logger.error("Failed to open PPTX '%s': %s", file_path, exc)
            raise ValueError(
                f"Invalid or corrupted PPTX file: {file_path}"
            ) from exc

        try:
            slides_data: list[dict[str, Any]] = []

            for slide_index, slide in enumerate(prs.slides, start=1):
                slide_info = self._extract_slide(slide, slide_index)
                slides_data.append(slide_info)

            # Metadata from core properties
            core_props = prs.core_properties
            metadata = {
                "title": core_props.title or "",
                "author": core_props.author or "",
                "slide_count": len(prs.slides),
            }

            # Template / layout properties
            slide_width = prs.slide_width
            slide_height = prs.slide_height
            layouts = []
            for layout in prs.slide_layouts:
                layouts.append(layout.name)

            template_properties = {
                "slide_width": self._emu_to_inches(slide_width),
                "slide_height": self._emu_to_inches(slide_height),
                "layouts": layouts,
            }

            return {
                "slides": slides_data,
                "metadata": metadata,
                "template_properties": template_properties,
            }

        except Exception as exc:
            logger.error("Failed to parse PPTX '%s': %s", file_path, exc)
            raise

    def extract_template_info(self, file_path: str) -> dict[str, Any]:
        """Extract template and theme information from a PPTX file.

        Args:
            file_path: Path to the PPTX file.

        Returns:
            A dictionary containing:
                - layouts: List of slide layout names.
                - color_scheme: Dict of theme color names to hex values.
                - font_theme: Dict with major_font and minor_font names.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file cannot be parsed.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PPTX file not found: {file_path}")

        try:
            prs = Presentation(file_path)
        except Exception as exc:
            logger.error("Failed to open PPTX '%s': %s", file_path, exc)
            raise ValueError(
                f"Invalid or corrupted PPTX file: {file_path}"
            ) from exc

        try:
            # Layout names
            layouts = [layout.name for layout in prs.slide_layouts]

            # Color scheme from theme XML
            color_scheme = self._extract_color_scheme(prs)

            # Font theme from theme XML
            font_theme = self._extract_font_theme(prs)

            return {
                "layouts": layouts,
                "color_scheme": color_scheme,
                "font_theme": font_theme,
            }

        except Exception as exc:
            logger.error(
                "Failed to extract template info from '%s': %s", file_path, exc
            )
            raise

    def _extract_slide(self, slide: Any, slide_number: int) -> dict[str, Any]:
        """Extract content from a single slide.

        Args:
            slide: A python-pptx Slide object.
            slide_number: The 1-based slide index.

        Returns:
            Dict with slide_number, title, content, notes, and shapes.
        """
        title = ""
        content: list[str] = []
        shapes_info: list[dict[str, Any]] = []

        for shape in slide.shapes:
            shape_data: dict[str, Any] = {
                "name": shape.name,
                "shape_type": str(shape.shape_type),
                "position": {
                    "left": self._emu_to_inches(shape.left) if shape.left else None,
                    "top": self._emu_to_inches(shape.top) if shape.top else None,
                    "width": self._emu_to_inches(shape.width) if shape.width else None,
                    "height": self._emu_to_inches(shape.height) if shape.height else None,
                },
            }

            if shape.has_text_frame:
                text = shape.text_frame.text.strip()
                shape_data["text"] = text
                if text:
                    content.append(text)

            # Identify the title shape
            if shape.has_text_frame and shape.shape_type == MSO_SHAPE_TYPE.PLACEHOLDER:
                try:
                    if shape.placeholder_format.idx == 0:
                        title = shape.text_frame.text.strip()
                except Exception:
                    pass

            if shape.has_table:
                table_data = self._extract_table(shape.table)
                shape_data["table"] = table_data

            shapes_info.append(shape_data)

        # Extract speaker notes
        notes = ""
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes = slide.notes_slide.notes_text_frame.text.strip()

        return {
            "slide_number": slide_number,
            "title": title,
            "content": content,
            "notes": notes,
            "shapes": shapes_info,
        }

    @staticmethod
    def _extract_table(table: Any) -> list[list[str]]:
        """Extract a table as a list of rows, each a list of cell strings.

        Args:
            table: A python-pptx Table object.

        Returns:
            A 2D list of cell text values.
        """
        rows: list[list[str]] = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            rows.append(cells)
        return rows

    @staticmethod
    def _emu_to_inches(emu_value: int | Emu | None) -> float | None:
        """Convert English Metric Units to inches.

        Args:
            emu_value: Value in EMUs (914400 EMUs = 1 inch).

        Returns:
            Value in inches, rounded to 2 decimal places, or None.
        """
        if emu_value is None:
            return None
        return round(int(emu_value) / 914400, 2)

    @staticmethod
    def _extract_color_scheme(prs: Presentation) -> dict[str, str]:
        """Extract theme color scheme from the presentation.

        Parses the theme XML to find color definitions.

        Args:
            prs: A python-pptx Presentation object.

        Returns:
            Dict mapping color role names (e.g. 'dk1', 'lt1', 'accent1')
            to hex color strings.
        """
        color_scheme: dict[str, str] = {}
        try:
            theme = prs.slide_masters[0].slide_layouts[0].slide_master.element
            nsmap = {
                "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
            }
            theme_elements = theme.findall(".//a:themeElements/a:clrScheme/*", nsmap)
            for elem in theme_elements:
                tag_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                # Color can be in srgbClr or sysClr child
                srgb = elem.find("a:srgbClr", nsmap)
                if srgb is not None:
                    color_scheme[tag_name] = f"#{srgb.get('val', '')}"
                    continue
                sys_clr = elem.find("a:sysClr", nsmap)
                if sys_clr is not None:
                    last_clr = sys_clr.get("lastClr", "")
                    color_scheme[tag_name] = f"#{last_clr}" if last_clr else ""
        except Exception as exc:
            logger.warning("Could not extract color scheme: %s", exc)

        return color_scheme

    @staticmethod
    def _extract_font_theme(prs: Presentation) -> dict[str, str]:
        """Extract theme font information from the presentation.

        Args:
            prs: A python-pptx Presentation object.

        Returns:
            Dict with 'major_font' and 'minor_font' keys.
        """
        font_theme: dict[str, str] = {"major_font": "", "minor_font": ""}
        try:
            theme = prs.slide_masters[0].slide_layouts[0].slide_master.element
            nsmap = {
                "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
            }
            major = theme.find(".//a:themeElements/a:fontScheme/a:majorFont/a:latin", nsmap)
            if major is not None:
                font_theme["major_font"] = major.get("typeface", "")

            minor = theme.find(".//a:themeElements/a:fontScheme/a:minorFont/a:latin", nsmap)
            if minor is not None:
                font_theme["minor_font"] = minor.get("typeface", "")
        except Exception as exc:
            logger.warning("Could not extract font theme: %s", exc)

        return font_theme
