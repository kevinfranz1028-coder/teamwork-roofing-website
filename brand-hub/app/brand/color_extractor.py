"""
Brand Intelligence Content Hub - Color Extractor

Extracts dominant colors from logo images using ColorThief, categorises them
into brand-palette roles (primary, secondary, accent, background), generates
complementary / analogous variations, and computes WCAG contrast ratios for
accessibility checking.
"""

import colorsys
import math
from pathlib import Path

from colorthief import ColorThief


class ColorExtractor:
    """Extract and analyse brand colors from images."""

    # ------------------------------------------------------------------
    # Core extraction
    # ------------------------------------------------------------------

    def extract_from_image(self, image_path: str, num_colors: int = 6) -> list[str]:
        """Extract the dominant colors from an image file.

        Parameters
        ----------
        image_path : str
            Filesystem path to a PNG, JPEG, or other image supported by
            Pillow / ColorThief.
        num_colors : int
            Number of dominant colors to return (default 6).

        Returns
        -------
        list[str]
            Hex colour strings, e.g. ``["#1a2b3c", "#ff9900", ...]``.

        Raises
        ------
        FileNotFoundError
            If *image_path* does not exist.
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        ct = ColorThief(str(path))

        # ColorThief.get_palette returns (num_colors - 1) entries when
        # color_count equals the requested number; request one extra.
        try:
            palette = ct.get_palette(color_count=num_colors + 1, quality=1)
        except Exception:
            # Fallback: just grab the single dominant color
            dominant = ct.get_color(quality=1)
            palette = [dominant]

        # Trim to requested count and convert to hex
        return [self.rgb_to_hex(rgb) for rgb in palette[:num_colors]]

    # ------------------------------------------------------------------
    # Colour conversions
    # ------------------------------------------------------------------

    @staticmethod
    def rgb_to_hex(rgb_tuple: tuple[int, int, int]) -> str:
        """Convert an (R, G, B) tuple to a ``#rrggbb`` hex string.

        Parameters
        ----------
        rgb_tuple : tuple[int, int, int]
            Each component in the range 0 - 255.

        Returns
        -------
        str
            Lowercase hex colour string, e.g. ``"#0a1b2c"``.
        """
        r, g, b = rgb_tuple
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """Convert a ``#rrggbb`` hex string to an (R, G, B) tuple."""
        hex_color = hex_color.lstrip("#")
        return (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
        )

    # ------------------------------------------------------------------
    # Categorisation
    # ------------------------------------------------------------------

    def categorize_colors(self, colors: list[str]) -> dict:
        """Suggest brand-palette roles for a list of hex colors.

        Heuristics
        ----------
        * The **most saturated, mid-lightness** color becomes *primary*.
        * The **second most saturated** becomes *secondary*.
        * The **lightest** color becomes *background*.
        * A remaining saturated color becomes *accent*.
        * The **darkest** color is suggested as *text*.

        Parameters
        ----------
        colors : list[str]
            Hex colour strings extracted from an image.

        Returns
        -------
        dict
            ``{"primary": "#...", "secondary": "#...", "accent": "#...",
              "background": "#...", "text": "#..."}``
        """
        if not colors:
            return {
                "primary": "#000000",
                "secondary": "#333333",
                "accent": "#666666",
                "background": "#ffffff",
                "text": "#000000",
            }

        # Compute HSL for sorting
        analyzed = []
        for hex_color in colors:
            r, g, b = self._hex_to_rgb(hex_color)
            h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            analyzed.append({"hex": hex_color, "h": h, "l": l, "s": s})

        # Sort by saturation descending
        by_saturation = sorted(analyzed, key=lambda c: c["s"], reverse=True)
        # Sort by lightness ascending (dark first)
        by_lightness = sorted(analyzed, key=lambda c: c["l"])

        result = {
            "primary": by_saturation[0]["hex"] if len(by_saturation) > 0 else "#000000",
            "secondary": by_saturation[1]["hex"] if len(by_saturation) > 1 else "#333333",
            "accent": by_saturation[2]["hex"] if len(by_saturation) > 2 else "#666666",
            "background": by_lightness[-1]["hex"] if by_lightness else "#ffffff",
            "text": by_lightness[0]["hex"] if by_lightness else "#000000",
        }
        return result

    # ------------------------------------------------------------------
    # Palette generation
    # ------------------------------------------------------------------

    def generate_color_palette(self, colors: list[str]) -> dict:
        """Generate complementary and analogous variations for each color.

        Parameters
        ----------
        colors : list[str]
            Base hex colours.

        Returns
        -------
        dict
            ``{"complementary": [...], "analogous": [...], "triadic": [...]}``
        """
        complementary: list[str] = []
        analogous: list[str] = []
        triadic: list[str] = []

        for hex_color in colors:
            r, g, b = self._hex_to_rgb(hex_color)
            h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)

            # Complementary: rotate hue by 180 degrees
            comp_h = (h + 0.5) % 1.0
            comp_rgb = colorsys.hls_to_rgb(comp_h, l, s)
            complementary.append(self.rgb_to_hex(self._float_to_int_rgb(comp_rgb)))

            # Analogous: +/- 30 degrees
            ana1_h = (h + 30 / 360) % 1.0
            ana2_h = (h - 30 / 360) % 1.0
            ana1_rgb = colorsys.hls_to_rgb(ana1_h, l, s)
            ana2_rgb = colorsys.hls_to_rgb(ana2_h, l, s)
            analogous.append(self.rgb_to_hex(self._float_to_int_rgb(ana1_rgb)))
            analogous.append(self.rgb_to_hex(self._float_to_int_rgb(ana2_rgb)))

            # Triadic: +/- 120 degrees
            tri1_h = (h + 120 / 360) % 1.0
            tri2_h = (h - 120 / 360) % 1.0
            tri1_rgb = colorsys.hls_to_rgb(tri1_h, l, s)
            tri2_rgb = colorsys.hls_to_rgb(tri2_h, l, s)
            triadic.append(self.rgb_to_hex(self._float_to_int_rgb(tri1_rgb)))
            triadic.append(self.rgb_to_hex(self._float_to_int_rgb(tri2_rgb)))

        return {
            "complementary": complementary,
            "analogous": analogous,
            "triadic": triadic,
        }

    # ------------------------------------------------------------------
    # Accessibility
    # ------------------------------------------------------------------

    def get_contrast_ratio(self, color1: str, color2: str) -> float:
        """Compute the WCAG 2.0 contrast ratio between two colours.

        Parameters
        ----------
        color1, color2 : str
            Hex colour strings.

        Returns
        -------
        float
            Contrast ratio in the range 1.0 (identical) to 21.0 (black/white).
            WCAG AA requires >= 4.5 for normal text, >= 3.0 for large text.
        """
        lum1 = self._relative_luminance(color1)
        lum2 = self._relative_luminance(color2)

        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)

        return (lighter + 0.05) / (darker + 0.05)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _float_to_int_rgb(rgb_floats: tuple[float, float, float]) -> tuple[int, int, int]:
        """Clamp float (0-1) RGB components to int (0-255)."""
        return (
            max(0, min(255, round(rgb_floats[0] * 255))),
            max(0, min(255, round(rgb_floats[1] * 255))),
            max(0, min(255, round(rgb_floats[2] * 255))),
        )

    def _relative_luminance(self, hex_color: str) -> float:
        """Compute WCAG relative luminance for a hex color."""
        r, g, b = self._hex_to_rgb(hex_color)

        def linearise(c: int) -> float:
            c_srgb = c / 255
            if c_srgb <= 0.03928:
                return c_srgb / 12.92
            return math.pow((c_srgb + 0.055) / 1.055, 2.4)

        return 0.2126 * linearise(r) + 0.7152 * linearise(g) + 0.0722 * linearise(b)
