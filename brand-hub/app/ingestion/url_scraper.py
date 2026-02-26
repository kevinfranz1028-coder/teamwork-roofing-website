"""
Web scraping module for Brand Intelligence Content Hub.

Uses requests and BeautifulSoup to fetch and parse web pages,
extracting clean text, headings, links, images, and metadata.
"""

import logging
import re
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Comment

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 "
    "BrandHub/1.0"
)

DEFAULT_TIMEOUT = 30


class URLScraper:
    """Scrapes web pages and extracts structured content.

    Fetches HTML from a URL, strips non-content elements, and returns
    clean text along with headings, links, images, and meta information.
    """

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the scraper with configurable settings.

        Args:
            user_agent: The User-Agent header string to send with requests.
            timeout: Request timeout in seconds.
        """
        self.user_agent = user_agent
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def scrape(self, url: str) -> dict[str, Any]:
        """Scrape a web page and return structured content.

        Args:
            url: The URL of the page to scrape.

        Returns:
            A dictionary containing:
                - url: The final URL (after any redirects).
                - title: The page <title> text.
                - text: Cleaned body text with scripts/styles removed.
                - headings: List of heading strings (from h1-h6 tags).
                - links: List of absolute URLs found on the page.
                - meta_description: The meta description content, if present.
                - images: List of absolute image src URLs.

        Raises:
            ValueError: If the URL is empty or malformed.
            requests.RequestException: If the HTTP request fails.
        """
        if not url or not url.strip():
            raise ValueError("URL must not be empty")

        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Failed to fetch URL '%s': %s", url, exc)
            raise

        final_url = response.url
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        title = self._extract_title(soup)
        meta_description = self._extract_meta_description(soup)
        text = self._clean_text(html)
        headings = self._extract_headings(soup)
        links = self._extract_links(soup, final_url)
        images = self._extract_images(soup, final_url)

        return {
            "url": final_url,
            "title": title,
            "text": text,
            "headings": headings,
            "links": links,
            "meta_description": meta_description,
            "images": images,
        }

    def _clean_text(self, html: str) -> str:
        """Extract and clean visible text from raw HTML.

        Removes script tags, style tags, HTML comments, and other
        non-content elements before extracting text. Collapses
        excessive whitespace into single spaces and trims lines.

        Args:
            html: Raw HTML string.

        Returns:
            A cleaned plain-text string.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove non-content elements
        tags_to_remove = [
            "script", "style", "noscript", "iframe", "svg",
            "header", "footer", "nav",
        ]
        for tag_name in tags_to_remove:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Remove HTML comments
        for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
            comment.extract()

        # Get text with newlines separating block elements
        raw_text = soup.get_text(separator="\n")

        # Clean up whitespace
        lines = []
        for line in raw_text.splitlines():
            cleaned = line.strip()
            if cleaned:
                # Collapse multiple internal spaces
                cleaned = re.sub(r"[ \t]+", " ", cleaned)
                lines.append(cleaned)

        return "\n".join(lines)

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> str:
        """Extract the page title.

        Args:
            soup: Parsed BeautifulSoup object.

        Returns:
            The title string, or empty string if not found.
        """
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        return ""

    @staticmethod
    def _extract_meta_description(soup: BeautifulSoup) -> str:
        """Extract the meta description content.

        Args:
            soup: Parsed BeautifulSoup object.

        Returns:
            The meta description string, or empty string if not found.
        """
        meta = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if meta and meta.get("content"):
            return meta["content"].strip()
        return ""

    @staticmethod
    def _extract_headings(soup: BeautifulSoup) -> list[str]:
        """Extract all heading texts (h1 through h6).

        Args:
            soup: Parsed BeautifulSoup object.

        Returns:
            A list of heading text strings in document order.
        """
        headings: list[str] = []
        for tag in soup.find_all(re.compile(r"^h[1-6]$")):
            text = tag.get_text(strip=True)
            if text:
                headings.append(text)
        return headings

    @staticmethod
    def _extract_links(soup: BeautifulSoup, base_url: str) -> list[str]:
        """Extract all unique absolute link URLs from anchor tags.

        Args:
            soup: Parsed BeautifulSoup object.
            base_url: The base URL for resolving relative links.

        Returns:
            A list of unique absolute URL strings.
        """
        links: list[str] = []
        seen: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            absolute = urljoin(base_url, href)
            if absolute not in seen:
                seen.add(absolute)
                links.append(absolute)

        return links

    @staticmethod
    def _extract_images(soup: BeautifulSoup, base_url: str) -> list[str]:
        """Extract all unique absolute image source URLs.

        Args:
            soup: Parsed BeautifulSoup object.
            base_url: The base URL for resolving relative image paths.

        Returns:
            A list of unique absolute image URL strings.
        """
        images: list[str] = []
        seen: set[str] = set()

        for img in soup.find_all("img", src=True):
            src = img["src"].strip()
            if not src or src.startswith("data:"):
                continue
            absolute = urljoin(base_url, src)
            if absolute not in seen:
                seen.add(absolute)
                images.append(absolute)

        return images
