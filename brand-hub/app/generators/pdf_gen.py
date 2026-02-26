"""
Brand Intelligence Content Hub - PDF Generator

Converts DOCX documents to PDF using LibreOffice headless or
provides a fallback notification when conversion tools are unavailable.
"""

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from app.config import DOCUMENTS_DIR, EXPORTS_DIR

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Converts DOCX files to PDF with branded elements."""

    def __init__(self):
        self.libreoffice_path = self._find_libreoffice()
        self._available: Optional[bool] = None

    @property
    def available(self) -> bool:
        """Check if PDF conversion is available."""
        if self._available is None:
            self._available = self.libreoffice_path is not None
        return self._available

    def _find_libreoffice(self) -> Optional[str]:
        """Locate LibreOffice binary on the system.

        Checks common paths for macOS, Linux, and Windows.
        """
        candidates = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "/usr/bin/libreoffice",
            "/usr/bin/soffice",
            "/usr/local/bin/libreoffice",
            "/usr/local/bin/soffice",
            "/snap/bin/libreoffice",
            # Windows
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]

        # Also try which/where
        for cmd in ["libreoffice", "soffice"]:
            result = shutil.which(cmd)
            if result:
                return result

        for path in candidates:
            if os.path.isfile(path):
                return path

        return None

    def convert_docx_to_pdf(self, docx_path: str, output_path: Optional[str] = None,
                             timeout: int = 120) -> dict:
        """Convert a DOCX file to PDF.

        Args:
            docx_path: Path to the source DOCX file.
            output_path: Optional path for the output PDF. Defaults to same name with .pdf extension.
            timeout: Maximum seconds to wait for conversion.

        Returns:
            dict with: success (bool), pdf_path (str or None), method (str), error (str or None).
        """
        path = Path(docx_path)
        if not path.exists():
            return {"success": False, "pdf_path": None, "method": "none", "error": f"File not found: {docx_path}"}

        if output_path is None:
            output_path = str(path.with_suffix(".pdf"))

        # Try LibreOffice headless
        if self.libreoffice_path:
            result = self._convert_with_libreoffice(docx_path, output_path, timeout)
            if result["success"]:
                return result

        return {
            "success": False,
            "pdf_path": None,
            "method": "none",
            "error": "No PDF conversion tool available. Install LibreOffice for PDF export.",
        }

    def _convert_with_libreoffice(self, docx_path: str, output_path: str, timeout: int) -> dict:
        """Convert using LibreOffice headless mode."""
        try:
            output_dir = str(Path(output_path).parent)
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # Use a temp dir so we control the output name
            with tempfile.TemporaryDirectory() as tmp_dir:
                cmd = [
                    self.libreoffice_path,
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", tmp_dir,
                    docx_path,
                ]

                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

                if proc.returncode != 0:
                    logger.error("LibreOffice conversion failed: %s", proc.stderr)
                    return {
                        "success": False,
                        "pdf_path": None,
                        "method": "libreoffice",
                        "error": f"LibreOffice error: {proc.stderr[:200]}",
                    }

                # Find the generated PDF in tmp_dir
                source_name = Path(docx_path).stem + ".pdf"
                source_pdf = Path(tmp_dir) / source_name

                if not source_pdf.exists():
                    # Try to find any PDF in the tmp dir
                    pdfs = list(Path(tmp_dir).glob("*.pdf"))
                    if pdfs:
                        source_pdf = pdfs[0]
                    else:
                        return {
                            "success": False,
                            "pdf_path": None,
                            "method": "libreoffice",
                            "error": "PDF file not found after conversion",
                        }

                shutil.move(str(source_pdf), output_path)

            return {
                "success": True,
                "pdf_path": output_path,
                "method": "libreoffice",
                "error": None,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "pdf_path": None,
                "method": "libreoffice",
                "error": f"Conversion timed out after {timeout}s",
            }
        except Exception as exc:
            return {
                "success": False,
                "pdf_path": None,
                "method": "libreoffice",
                "error": str(exc),
            }

    def batch_convert(self, docx_paths: list[str], output_dir: Optional[str] = None) -> list[dict]:
        """Convert multiple DOCX files to PDF.

        Args:
            docx_paths: List of DOCX file paths.
            output_dir: Directory for output PDFs. Uses each file's directory if None.

        Returns:
            List of result dicts, one per file.
        """
        results = []
        for docx_path in docx_paths:
            if output_dir:
                pdf_name = Path(docx_path).stem + ".pdf"
                out_path = str(Path(output_dir) / pdf_name)
            else:
                out_path = None
            results.append(self.convert_docx_to_pdf(docx_path, out_path))
        return results
