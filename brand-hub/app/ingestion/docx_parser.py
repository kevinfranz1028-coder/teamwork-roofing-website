"""
DOCX text extraction module for Brand Intelligence Content Hub.

Uses python-docx to extract text, structure, metadata, and style
information from Microsoft Word documents.
"""

import logging
from pathlib import Path
from typing import Any

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.text.paragraph import Paragraph

logger = logging.getLogger(__name__)


class DOCXParser:
    """Parses DOCX documents into structured text with metadata and styles.

    Extracts full text, heading hierarchy, list items, paragraphs,
    document metadata, and a list of styles used in the document.
    """

    def parse(self, file_path: str) -> dict[str, Any]:
        """Parse a DOCX file and return structured content.

        Args:
            file_path: Path to the DOCX file.

        Returns:
            A dictionary containing:
                - text: Full concatenated text from all paragraphs.
                - structure: List of dicts with 'type' (heading/paragraph/list),
                  optional 'level' (for headings), and 'content'.
                - metadata: Dict with title and author.
                - styles: List of style names used in the document.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file cannot be parsed as a DOCX.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"DOCX file not found: {file_path}")

        if path.suffix.lower() not in (".docx", ".docm"):
            raise ValueError(f"File is not a DOCX document: {file_path}")

        try:
            doc = Document(file_path)
        except PackageNotFoundError as exc:
            raise ValueError(
                f"Invalid or corrupted DOCX file: {file_path}"
            ) from exc
        except Exception as exc:
            logger.error("Failed to open DOCX '%s': %s", file_path, exc)
            raise

        try:
            structure: list[dict[str, Any]] = []
            text_parts: list[str] = []
            styles_used: set[str] = set()

            for paragraph in doc.paragraphs:
                content = paragraph.text.strip()
                if not content:
                    continue

                text_parts.append(content)

                # Track the style name
                style_name = paragraph.style.name if paragraph.style else None
                if style_name:
                    styles_used.add(style_name)

                heading_level = self._get_heading_level(paragraph)

                if heading_level is not None:
                    structure.append({
                        "type": "heading",
                        "level": heading_level,
                        "content": content,
                    })
                elif self._is_list_item(paragraph):
                    structure.append({
                        "type": "list",
                        "content": content,
                    })
                else:
                    structure.append({
                        "type": "paragraph",
                        "content": content,
                    })

            # Extract metadata from core properties
            core_props = doc.core_properties
            metadata = {
                "title": core_props.title or "",
                "author": core_props.author or "",
            }

            return {
                "text": "\n\n".join(text_parts),
                "structure": structure,
                "metadata": metadata,
                "styles": sorted(styles_used),
            }

        except Exception as exc:
            logger.error("Failed to parse DOCX '%s': %s", file_path, exc)
            raise

    def _get_heading_level(self, paragraph: Paragraph) -> int | None:
        """Determine the heading level of a paragraph.

        Args:
            paragraph: A python-docx Paragraph object.

        Returns:
            An integer heading level (1-9) if the paragraph is a heading,
            or None if it is not a heading.
        """
        style_name = paragraph.style.name if paragraph.style else ""

        # python-docx heading styles are named "Heading 1", "Heading 2", etc.
        if style_name.startswith("Heading"):
            parts = style_name.split()
            if len(parts) == 2:
                try:
                    return int(parts[1])
                except ValueError:
                    pass
            # "Heading" without a number maps to level 1
            if len(parts) == 1:
                return 1

        # Also check the paragraph's outline level from the XML element
        try:
            pPr = paragraph._element.pPr
            if pPr is not None:
                outline_lvl = pPr.find(
                    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}outlineLvl"
                )
                if outline_lvl is not None:
                    val = outline_lvl.get(
                        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
                    )
                    if val is not None:
                        level = int(val) + 1  # outline levels are 0-indexed
                        if 1 <= level <= 9:
                            return level
        except Exception:
            pass

        return None

    @staticmethod
    def _is_list_item(paragraph: Paragraph) -> bool:
        """Determine whether a paragraph is a list item.

        Checks the paragraph's style name and its underlying XML for
        numbering references that indicate list membership.

        Args:
            paragraph: A python-docx Paragraph object.

        Returns:
            True if the paragraph is a list item, False otherwise.
        """
        style_name = paragraph.style.name if paragraph.style else ""
        list_style_keywords = ("List", "Bullet", "Number", "list", "bullet", "number")
        if any(kw in style_name for kw in list_style_keywords):
            return True

        # Check XML for numPr (numbering properties) which indicates a list
        try:
            pPr = paragraph._element.pPr
            if pPr is not None:
                numPr = pPr.find(
                    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}numPr"
                )
                if numPr is not None:
                    return True
        except Exception:
            pass

        return False
