"""
Brand Intelligence Content Hub - OpenAI Integration

Wraps the OpenAI API for DALL-E 3 image generation and GPT chat
completions (used by the orchestrator when configured for OpenAI mode).

Usage:
    from app.integrations.openai_client import OpenAIClient

    client = OpenAIClient()
    if client.is_available():
        result = client.generate_image("A modern office building at sunset")
        print(result["file_path"])
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import requests

from app.config import BRAND_ASSETS_DIR, VISUALS_DIR

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_DALLE_MODEL = "dall-e-3"
DEFAULT_IMAGE_SIZE = "1024x1024"
DEFAULT_IMAGE_QUALITY = "standard"
DEFAULT_IMAGE_STYLE = "natural"

# Valid parameter values for DALL-E 3
VALID_SIZES = {"1024x1024", "1792x1024", "1024x1792"}
VALID_QUALITIES = {"standard", "hd"}
VALID_STYLES = {"natural", "vivid"}


class OpenAIClient:
    """Client for OpenAI APIs — DALL-E 3 image generation and GPT chat.

    Lazy-initialises the ``openai.OpenAI`` client on first use so the
    module can be imported without ``openai`` being installed or configured.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._client = None
        self._brand_colors: dict = self._load_brand_colors()

        # Ensure output directory exists
        VISUALS_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Availability
    # ------------------------------------------------------------------

    @staticmethod
    def is_available() -> bool:
        """Return True if OPENAI_API_KEY is set in the environment."""
        return bool(os.environ.get("OPENAI_API_KEY", "").strip())

    # ------------------------------------------------------------------
    # Lazy client init
    # ------------------------------------------------------------------

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI

                if not self._api_key:
                    raise ValueError("OPENAI_API_KEY not set")
                self._client = OpenAI(api_key=self._api_key)
            except Exception as exc:
                logger.error("Could not init OpenAI client: %s", exc)
                raise
        return self._client

    # ------------------------------------------------------------------
    # Brand colours
    # ------------------------------------------------------------------

    @staticmethod
    def _load_brand_colors() -> dict:
        config_path = BRAND_ASSETS_DIR / "brand_config.json"
        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as fh:
                    config = json.load(fh)
                return config.get("colors", {})
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _build_brand_color_hint(self) -> str:
        """Return a prompt fragment instructing DALL-E to use brand colours."""
        if not self._brand_colors:
            return ""
        parts = []
        for role, hex_val in self._brand_colors.items():
            if role in ("primary", "secondary", "accent"):
                parts.append(f"{role} color {hex_val}")
        if not parts:
            return ""
        return f" Use a color palette featuring {', '.join(parts)}."

    # ------------------------------------------------------------------
    # DALL-E 3 Image Generation
    # ------------------------------------------------------------------

    def generate_image(
        self,
        prompt: str,
        size: str = DEFAULT_IMAGE_SIZE,
        quality: str = DEFAULT_IMAGE_QUALITY,
        style: str = DEFAULT_IMAGE_STYLE,
        save_path: str | None = None,
        inject_brand_colors: bool = True,
    ) -> dict:
        """Generate an image with DALL-E 3.

        Args:
            prompt: Natural-language description of the image.
            size: Image dimensions — ``1024x1024``, ``1792x1024``,
                or ``1024x1792``.
            quality: ``standard`` or ``hd``.
            style: ``natural`` or ``vivid``.
            save_path: Where to save the downloaded image.  Auto-generated
                when *None*.
            inject_brand_colors: When True, appends brand colour hints to
                the prompt for visual consistency.

        Returns:
            Dict with ``success``, ``file_path``, ``revised_prompt``,
            ``model``, ``size``, ``quality``, ``style``, ``error``.
        """
        if not prompt or not prompt.strip():
            return {
                "success": False,
                "file_path": None,
                "error": "Prompt is empty",
            }

        # Validate parameters
        if size not in VALID_SIZES:
            logger.warning("Invalid size '%s'; using %s", size, DEFAULT_IMAGE_SIZE)
            size = DEFAULT_IMAGE_SIZE
        if quality not in VALID_QUALITIES:
            quality = DEFAULT_IMAGE_QUALITY
        if style not in VALID_STYLES:
            style = DEFAULT_IMAGE_STYLE

        # Inject brand colours into the prompt
        full_prompt = prompt
        if inject_brand_colors:
            color_hint = self._build_brand_color_hint()
            if color_hint:
                full_prompt = prompt + color_hint

        try:
            client = self._get_client()
            response = client.images.generate(
                model=DEFAULT_DALLE_MODEL,
                prompt=full_prompt,
                size=size,
                quality=quality,
                style=style,
                n=1,
            )

            image_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt or prompt

            # Download the image
            file_path = self.download_image(image_url, save_path)
            if not file_path:
                return {
                    "success": False,
                    "file_path": None,
                    "revised_prompt": revised_prompt,
                    "error": "Failed to download generated image",
                }

            logger.info("DALL-E image generated: %s", file_path)
            return {
                "success": True,
                "file_path": file_path,
                "revised_prompt": revised_prompt,
                "model": DEFAULT_DALLE_MODEL,
                "size": size,
                "quality": quality,
                "style": style,
                "error": None,
            }

        except Exception as exc:
            logger.error("DALL-E generation failed: %s", exc)
            return {
                "success": False,
                "file_path": None,
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Image download
    # ------------------------------------------------------------------

    def download_image(
        self,
        url: str,
        save_path: str | None = None,
    ) -> str | None:
        """Download an image from *url* and save to disk.

        Args:
            url: The image URL to download.
            save_path: Destination path.  Auto-generated under
                ``output/visuals/`` when *None*.

        Returns:
            The absolute file path on success, or *None* on failure.
        """
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = str(VISUALS_DIR / f"dalle_{timestamp}.png")

        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()

            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            Path(save_path).write_bytes(resp.content)
            logger.info("Image downloaded: %s (%d bytes)", save_path, len(resp.content))
            return save_path

        except Exception as exc:
            logger.error("Image download failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # GPT Chat Completion (for orchestrator OpenAI mode)
    # ------------------------------------------------------------------

    def chat_completion(
        self,
        messages: list[dict],
        model: str | None = None,
        max_tokens: int = 500,
        temperature: float = 0.3,
    ) -> dict:
        """Run a GPT chat completion.

        Args:
            messages: OpenAI-format messages list (role + content dicts).
            model: Model name.  Defaults to ``ORCHESTRATOR_OPENAI_MODEL``
                env var or ``gpt-4.1``.
            max_tokens: Maximum response tokens.
            temperature: Sampling temperature.

        Returns:
            Dict with ``success``, ``content`` (response text), ``model``,
            ``usage``, ``error``.
        """
        if model is None:
            model = os.environ.get("ORCHESTRATOR_OPENAI_MODEL", "gpt-4.1")

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            choice = response.choices[0]
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            } if response.usage else {}

            return {
                "success": True,
                "content": choice.message.content,
                "model": model,
                "usage": usage,
                "error": None,
            }

        except Exception as exc:
            logger.error("Chat completion failed: %s", exc)
            return {
                "success": False,
                "content": None,
                "model": model,
                "usage": {},
                "error": str(exc),
            }
