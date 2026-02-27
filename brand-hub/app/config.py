"""
Brand Intelligence Content Hub - Configuration Module

Environment loading, path management, and validation for the entire application.
Uses python-dotenv to load .env and defines all project paths and API key helpers.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env from project root
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # /Users/kevinfranzsr./brand-hub
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Directory paths
# ---------------------------------------------------------------------------
DATA_DIR = BASE_DIR / "data"
BRAND_ASSETS_DIR = BASE_DIR / "brand_assets"
OUTPUT_DIR = BASE_DIR / "output"

# Data sub-directories
CHROMADB_DIR = DATA_DIR / "chromadb"
PRESENTON_DIR = DATA_DIR / "presenton"
UPLOADS_DIR = DATA_DIR / "uploads"
CACHE_DIR = DATA_DIR / "cache"

# Output sub-directories
PRESENTATIONS_DIR = OUTPUT_DIR / "presentations"
DOCUMENTS_DIR = OUTPUT_DIR / "documents"
TRAINING_DIR = OUTPUT_DIR / "training"
VISUALS_DIR = OUTPUT_DIR / "visuals"
INFOGRAPHICS_DIR = OUTPUT_DIR / "infographics"
TRANSLATIONS_DIR = OUTPUT_DIR / "translations"
REPORTS_DIR = OUTPUT_DIR / "reports"
EXPORTS_DIR = OUTPUT_DIR / "exports"

# Brand asset sub-directories
LOGOS_DIR = BRAND_ASSETS_DIR / "logos"
FONTS_DIR = BRAND_ASSETS_DIR / "fonts"
TEMPLATES_DIR = BRAND_ASSETS_DIR / "templates"

# Collect every directory so setup helpers can create them in one pass
ALL_DIRS = [
    DATA_DIR,
    BRAND_ASSETS_DIR,
    OUTPUT_DIR,
    CHROMADB_DIR,
    PRESENTON_DIR,
    UPLOADS_DIR,
    CACHE_DIR,
    PRESENTATIONS_DIR,
    DOCUMENTS_DIR,
    TRAINING_DIR,
    VISUALS_DIR,
    INFOGRAPHICS_DIR,
    TRANSLATIONS_DIR,
    REPORTS_DIR,
    EXPORTS_DIR,
    LOGOS_DIR,
    FONTS_DIR,
    TEMPLATES_DIR,
]

# ---------------------------------------------------------------------------
# Required / optional environment keys
# ---------------------------------------------------------------------------
REQUIRED_ENV_KEYS = [
    "ANTHROPIC_API_KEY",
    "NAPKIN_API_TOKEN",
]

OPTIONAL_ENV_KEYS = {
    "PRESENTON_URL": "http://localhost:5001",
    "DEEPL_API_KEY": "",
    "PEXELS_API_KEY": "",
    "GOOGLE_SERVICE_ACCOUNT_JSON": "",
    "GOOGLE_OAUTH_CREDENTIALS_JSON": "",
    # Multi-agent orchestrator
    "ORCHESTRATOR_MODEL": "claude",
    "ORCHESTRATOR_CLAUDE_MODEL": "claude-sonnet-4-20250514",
    "ORCHESTRATOR_OPENAI_MODEL": "gpt-4.1",
    "WRITER_MODEL": "claude-sonnet-4-20250514",
    "DESIGNER_MODEL": "claude-haiku-4-5-20251001",
    "AGENT_MAX_RETRIES": "2",
    "AGENT_TIMEOUT_SECONDS": "300",
    "OPENAI_API_KEY": "",
    # DALL-E / Visual Agent
    "DALLE_IMAGE_SIZE": "1024x1024",
    "DALLE_IMAGE_QUALITY": "standard",
    "DALLE_IMAGE_STYLE": "natural",
}


def validate_env() -> dict:
    """Check that every required environment variable is set.

    Returns
    -------
    dict
        A mapping of ``{key: value}`` for all required keys that are present.

    Raises
    ------
    EnvironmentError
        If one or more required keys are missing or empty.
    """
    missing: list[str] = []
    present: dict[str, str] = {}

    for key in REQUIRED_ENV_KEYS:
        value = os.getenv(key, "").strip()
        if not value:
            missing.append(key)
        else:
            present[key] = value

    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Please set them in your .env file or export them in the shell."
        )

    return present


# ---------------------------------------------------------------------------
# Convenience getters
# ---------------------------------------------------------------------------

def get_env(key: str) -> str:
    """Return the value of an environment variable, falling back to the
    optional-key defaults defined in ``OPTIONAL_ENV_KEYS``.
    """
    default = OPTIONAL_ENV_KEYS.get(key, "")
    return os.getenv(key, default)


def get_db_url() -> str:
    """Return the SQLAlchemy database URL for the project SQLite database."""
    return f"sqlite:///{DATA_DIR / 'brand_hub.db'}"


def get_chroma_path() -> str:
    """Return the filesystem path used by ChromaDB for persistent storage."""
    return str(CHROMADB_DIR)


def ensure_directories() -> None:
    """Create every project directory if it does not already exist."""
    for directory in ALL_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
