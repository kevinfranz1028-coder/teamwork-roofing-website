"""
Brand Intelligence Content Hub - Presenton Integration

Wraps the Presenton Docker API for AI-powered presentation generation.
Falls back gracefully when Presenton is unavailable.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import requests

from app.config import get_env, PRESENTATIONS_DIR, TEMPLATES_DIR

logger = logging.getLogger(__name__)


class PresentonClient:
    """Client for the Presenton presentation generation API.

    Presenton runs as a Docker container and exposes REST endpoints
    for generating PPTX presentations from structured content.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        self.base_url = (base_url or get_env("PRESENTON_URL")).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self._available: Optional[bool] = None

    @property
    def available(self) -> bool:
        """Check if Presenton is reachable (cached after first check)."""
        if self._available is None:
            self._available = self.health_check()
        return self._available

    def health_check(self) -> bool:
        """Ping the Presenton health endpoint.

        Returns True if the service is up, False otherwise.
        Tries /api/health, then /health, then root /.
        """
        for endpoint in ["/api/health", "/health", "/"]:
            try:
                resp = self.session.get(
                    f"{self.base_url}{endpoint}",
                    timeout=5,
                )
                if resp.status_code < 500:
                    self._available = True
                    return True
            except requests.RequestException:
                continue
        self._available = False
        return False

    def generate_presentation(
        self,
        content: str,
        n_slides: int = 10,
        template: Optional[str] = None,
        language: str = "en",
        export_as: str = "pptx",
    ) -> dict:
        """Submit a presentation generation request to Presenton.

        Args:
            content: The topic or full content to generate slides from.
            n_slides: Target number of slides.
            template: Optional template name/ID.
            language: Language code (default "en").
            export_as: Output format - "pptx" or "pdf".

        Returns:
            dict with keys: success (bool), request_id (str or None),
            message (str), error (str or None).

        If Presenton is unavailable, returns success=False with appropriate message.
        """
        if not self.available:
            return {
                "success": False,
                "request_id": None,
                "message": "Presenton service is not available",
                "error": "Service unreachable",
            }

        payload = {
            "topic": content,
            "n_slides": n_slides,
            "language": language,
            "export_as": export_as,
        }
        if template:
            payload["template"] = template

        # Try multiple possible API endpoints
        for endpoint in ["/api/presentations/generate", "/api/generate", "/generate"]:
            try:
                resp = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    timeout=self.timeout,
                )
                if resp.status_code in (200, 201, 202):
                    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                    return {
                        "success": True,
                        "request_id": data.get("request_id") or data.get("id") or data.get("presentation_id"),
                        "message": data.get("message", "Generation submitted"),
                        "error": None,
                        "data": data,
                    }
            except requests.RequestException as exc:
                logger.debug("Presenton endpoint %s failed: %s", endpoint, exc)
                continue

        return {
            "success": False,
            "request_id": None,
            "message": "All Presenton API endpoints failed",
            "error": "No valid endpoint found",
        }

    def poll_status(self, request_id: str, max_wait: int = 300, interval: int = 3) -> dict:
        """Poll Presenton until generation is complete or times out.

        Args:
            request_id: The ID returned from generate_presentation.
            max_wait: Max seconds to wait.
            interval: Seconds between polls.

        Returns:
            dict with: status (str), progress (float 0-1),
            result (dict or None), error (str or None).
        """
        if not request_id:
            return {"status": "error", "progress": 0, "result": None, "error": "No request_id"}

        elapsed = 0
        endpoints = [
            f"/api/presentations/{request_id}/status",
            f"/api/status/{request_id}",
        ]

        while elapsed < max_wait:
            for endpoint in endpoints:
                try:
                    resp = self.session.get(
                        f"{self.base_url}{endpoint}",
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        status = data.get("status", "unknown")
                        progress = data.get("progress", 0)

                        if status in ("completed", "done", "finished", "ready"):
                            return {
                                "status": "completed",
                                "progress": 1.0,
                                "result": data,
                                "error": None,
                            }
                        if status in ("failed", "error"):
                            return {
                                "status": "failed",
                                "progress": progress,
                                "result": data,
                                "error": data.get("error", "Generation failed"),
                            }
                        # Still processing
                        break
                except requests.RequestException:
                    continue

            time.sleep(interval)
            elapsed += interval

        return {
            "status": "timeout",
            "progress": 0,
            "result": None,
            "error": f"Timed out after {max_wait}s",
        }

    def download_result(self, presentation_id: str, save_path: Optional[str] = None) -> dict:
        """Download the generated presentation file.

        Args:
            presentation_id: The presentation/request ID.
            save_path: Where to save the file. Defaults to output/presentations/.

        Returns:
            dict with: success (bool), file_path (str or None), error (str or None).
        """
        if save_path is None:
            save_path = str(PRESENTATIONS_DIR / f"presenton_{presentation_id}.pptx")

        endpoints = [
            f"/api/presentations/{presentation_id}/download",
            f"/api/download/{presentation_id}",
        ]

        for endpoint in endpoints:
            try:
                resp = self.session.get(
                    f"{self.base_url}{endpoint}",
                    timeout=60,
                    stream=True,
                )
                if resp.status_code == 200:
                    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(save_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return {
                        "success": True,
                        "file_path": save_path,
                        "error": None,
                    }
            except requests.RequestException as exc:
                logger.debug("Download from %s failed: %s", endpoint, exc)
                continue

        return {
            "success": False,
            "file_path": None,
            "error": "Failed to download from all endpoints",
        }

    def list_templates(self) -> dict:
        """List available Presenton templates.

        Returns:
            dict with: success (bool), templates (list), error (str or None).
        """
        if not self.available:
            return {"success": False, "templates": [], "error": "Service unavailable"}

        for endpoint in ["/api/templates", "/templates"]:
            try:
                resp = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    templates = data if isinstance(data, list) else data.get("templates", [])
                    return {"success": True, "templates": templates, "error": None}
            except requests.RequestException:
                continue

        return {"success": False, "templates": [], "error": "Failed to list templates"}

    def upload_template(self, pptx_path: str) -> dict:
        """Upload a PPTX template to Presenton.

        Args:
            pptx_path: Path to the .pptx template file.

        Returns:
            dict with: success (bool), template_id (str or None), error (str or None).
        """
        if not self.available:
            return {"success": False, "template_id": None, "error": "Service unavailable"}

        path = Path(pptx_path)
        if not path.exists():
            return {"success": False, "template_id": None, "error": f"File not found: {pptx_path}"}

        for endpoint in ["/api/templates/upload", "/api/templates"]:
            try:
                with open(pptx_path, "rb") as f:
                    resp = self.session.post(
                        f"{self.base_url}{endpoint}",
                        files={"file": (path.name, f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
                        timeout=30,
                    )
                if resp.status_code in (200, 201):
                    data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                    return {
                        "success": True,
                        "template_id": data.get("template_id") or data.get("id"),
                        "error": None,
                    }
            except requests.RequestException as exc:
                logger.debug("Upload to %s failed: %s", endpoint, exc)
                continue

        return {"success": False, "template_id": None, "error": "Failed to upload template"}

    def reset_cache(self):
        """Reset the availability cache so the next access re-checks."""
        self._available = None
