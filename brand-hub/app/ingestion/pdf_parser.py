"""
PDF text extraction module for Brand Intelligence Content Hub.

Uses pdfplumber to extract text, metadata, and structural elements
from PDF documents.
"""

import logging
from pathlib import Path
from typing import Any

import pdfplumber

logger = logging.getLogger(__name__)


class PDFParser:
    """Parses PDF documents into structured text with metadata.

    Extracts full text, per-page text, document metadata, and structural
    elements (headings, paragraphs, lists) from PDF files using pdfplumber.
    """

    def parse(self, file_path: str) -> dict[str, Any]:
        """Parse a PDF file and return structured content.

        Args:
            file_path: Path to the PDF file.

        Returns:
            A dictionary containing:
                - text: Full concatenated text from all pages.
                - pages: List of per-page text strings.
                - metadata: Dict with title, author, and page_count.
                - structure: List of dicts each with 'type'
                  (heading/paragraph/list) and 'content'.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file cannot be parsed as a PDF.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        if not path.suffix.lower() == ".pdf":
            raise ValueError(f"File is not a PDF: {file_path}")

        try:
            with pdfplumber.open(file_path) as pdf:
                pages_text: list[str] = []
                structure: list[dict[str, str]] = []

                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    pages_text.append(page_text)
                    structure.extend(self._extract_structure(page))

                full_text = "\n\n".join(pages_text)

                pdf_metadata = pdf.metadata or {}
                metadata = {
                    "title": pdf_metadata.get("Title", ""),
                    "author": pdf_metadata.get("Author", ""),
                    "page_count": len(pdf.pages),
                }

                return {
                    "text": full_text,
                    "pages": pages_text,
                    "metadata": metadata,
                    "structure": structure,
                }

        except pdfplumber.pdfminer.pdfparser.PDFSyntaxError as exc:
            raise ValueError(f"Invalid or corrupted PDF file: {file_path}") from exc
        except Exception as exc:
            logger.error("Failed to parse PDF '%s': %s", file_path, exc)
            raise

    def _extract_structure(self, page: pdfplumber.page.Page) -> list[dict[str, str]]:
        """Extract structural elements from a single PDF page.

        Analyses text lines and classifies them as headings, list items,
        or paragraphs based on formatting heuristics:
          - Lines that are short, title-cased or all-caps, and lack trailing
            punctuation are treated as headings.
          - Lines starting with bullet characters or ordered-list prefixes
            are treated as list items.
          - Everything else is grouped into paragraphs.

        Args:
            page: A pdfplumber Page object.

        Returns:
            A list of dicts, each with keys 'type' and 'content'.
        """
        text = page.extract_text() or ""
        if not text.strip():
            return []

        elements: list[dict[str, str]] = []
        lines = text.split("\n")
        paragraph_buffer: list[str] = []

        def flush_paragraph() -> None:
            if paragraph_buffer:
                content = " ".join(paragraph_buffer).strip()
                if content:
                    elements.append({"type": "paragraph", "content": content})
                paragraph_buffer.clear()

        for line in lines:
            stripped = line.strip()
            if not stripped:
                flush_paragraph()
                continue

            # Detect list items: bullets, dashes, or ordered prefixes
            if self._is_list_item(stripped):
                flush_paragraph()
                elements.append({"type": "list", "content": stripped})
                continue

            # Detect headings: short, title-case/uppercase, no trailing period
            if self._is_heading(stripped):
                flush_paragraph()
                elements.append({"type": "heading", "content": stripped})
                continue

            # Default: accumulate into paragraph
            paragraph_buffer.append(stripped)

        flush_paragraph()
        return elements

    @staticmethod
    def _is_list_item(line: str) -> bool:
        """Determine whether a line looks like a list item."""
        bullet_prefixes = ("\u2022", "\u2023", "\u25e6", "\u2043", "-", "*", "\u2013", "\u2014")
        if line.startswith(bullet_prefixes):
            return True
        # Ordered list: "1.", "1)", "a.", "a)", etc.
        if len(line) > 2:
            first_token = line.split()[0]
            if (
                first_token.endswith((".", ")"))
                and len(first_token) <= 4
                and (first_token[:-1].isdigit() or first_token[:-1].isalpha())
            ):
                return True
        return False

    @staticmethod
    def _is_heading(line: str) -> bool:
        """Determine whether a line looks like a heading."""
        if len(line) > 120:
            return False
        if line.endswith((".", ",", ";", ":")):
            return False
        if line.isupper() and len(line) > 2:
            return True
        if line.istitle() and len(line.split()) <= 10:
            return True
        return False
