"""
Brand Intelligence Content Hub - Settings & Configuration

Full settings management page: API keys, brand configuration, prompt
templates, document templates, output settings, integrations, backup/restore,
and system diagnostics.
"""

import io
import json
import logging
import os
import platform
import shutil
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import (
    BASE_DIR,
    DATA_DIR,
    BRAND_ASSETS_DIR,
    OUTPUT_DIR,
    LOGOS_DIR,
    FONTS_DIR,
    TEMPLATES_DIR,
    REQUIRED_ENV_KEYS,
    OPTIONAL_ENV_KEYS,
    ALL_DIRS,
    get_env,
    ensure_directories,
)
from app.database.models import (
    get_session,
    init_db,
    BrandConfig,
    BrandAsset,
    Template,
    PromptTemplate,
    GeneratedContent,
)

# Optional imports with availability flags
try:
    from app.integrations.translation_client import TranslationEngine
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False

try:
    from app.generators.google_export import GoogleWorkspaceExporter
    GOOGLE_EXPORT_AVAILABLE = True
except ImportError:
    GOOGLE_EXPORT_AVAILABLE = False

try:
    from app.core.feedback_loop import FeedbackLoop
    FEEDBACK_AVAILABLE = True
except ImportError:
    FEEDBACK_AVAILABLE = False

try:
    from app.utils.analytics import AnalyticsEngine
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

try:
    from app.integrations.napkin_client import NapkinClient
    NAPKIN_AVAILABLE = True
except ImportError:
    NAPKIN_AVAILABLE = False

try:
    from app.integrations.presenton_client import PresentonClient
    PRESENTON_AVAILABLE = True
except ImportError:
    PRESENTON_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Settings & Configuration", page_icon="\u2699\ufe0f", layout="wide")

st.markdown(
    """<style>
.brand-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 20px;
    margin: 8px 0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.brand-card h3 {
    margin-top: 0;
    color: #1a1a2e;
}
.brand-card p {
    color: #555;
}
.settings-section {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 16px;
    margin: 6px 0;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}
.status-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}
.status-ok {
    background: #d4edda;
    color: #155724;
}
.status-missing {
    background: #f8d7da;
    color: #721c24;
}
.status-warning {
    background: #fff3cd;
    color: #856404;
}
.key-card {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0;
}
.diag-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
    border: 1px solid #e0e0e0;
}
.integration-card {
    background: linear-gradient(135deg, #f0f4ff 0%, #ffffff 100%);
    border: 1px solid #c5d5f7;
    border-radius: 10px;
    padding: 16px;
    margin: 6px 0;
}
.stProgress > div > div > div > div { background-color: #0066cc; }
</style>""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Initialise DB
# ---------------------------------------------------------------------------
if "db_ok" not in st.session_state:
    try:
        init_db()
        st.session_state["db_ok"] = True
    except Exception as exc:
        st.session_state["db_ok"] = False
        st.session_state["db_error"] = str(exc)

# ---------------------------------------------------------------------------
# Session-state defaults
# ---------------------------------------------------------------------------
_session_defaults = {
    "settings_active_tab": 0,
    "env_values": {},
    "brand_config_data": {},
    "new_template_expanded": False,
    "diag_results": {},
    "reset_db_confirm_1": False,
    "reset_db_confirm_2": False,
    "clean_output_confirm": False,
}
for key, default in _session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ENV_FILE_PATH = BASE_DIR / ".env"
BRAND_CONFIG_PATH = BRAND_ASSETS_DIR / "brand_config.json"
DB_PATH = DATA_DIR / "brand_hub.db"

API_KEY_INFO = {
    "ANTHROPIC_API_KEY": {
        "label": "Anthropic API Key",
        "description": "Required for Claude AI content generation.",
        "required": True,
    },
    "NAPKIN_API_TOKEN": {
        "label": "Napkin AI API Token",
        "description": "Required for diagram and visual generation via Napkin AI.",
        "required": True,
    },
    "DEEPL_API_KEY": {
        "label": "DeepL API Key",
        "description": "Optional. Enables multi-language translation of generated content.",
        "required": False,
    },
    "PEXELS_API_KEY": {
        "label": "Pexels API Key",
        "description": "Optional. Enables royalty-free stock photo search for visuals.",
        "required": False,
    },
    "PRESENTON_URL": {
        "label": "Presenton URL",
        "description": "Optional. URL for the Presenton presentation-generation service.",
        "required": False,
    },
    "GOOGLE_SERVICE_ACCOUNT_JSON": {
        "label": "Google Service Account JSON",
        "description": "Optional. Path to Google service account credentials for Workspace export.",
        "required": False,
    },
    "GOOGLE_OAUTH_CREDENTIALS_JSON": {
        "label": "Google OAuth Credentials JSON",
        "description": "Optional. Path to Google OAuth credentials for Workspace export.",
        "required": False,
    },
    "OPENAI_API_KEY": {
        "label": "OpenAI API Key",
        "description": "Optional. Enables DALL-E 3 image generation and GPT-based orchestration.",
        "required": False,
    },
}

SUPPORTED_LANGUAGES = [
    "English", "Spanish", "French", "German", "Italian", "Portuguese",
    "Dutch", "Russian", "Chinese (Simplified)", "Chinese (Traditional)",
    "Japanese", "Korean", "Arabic", "Hindi", "Turkish", "Polish",
    "Swedish", "Danish", "Norwegian", "Finnish",
]

CONTENT_TYPES_LIST = [
    "presentation", "document", "training", "visual", "quiz",
    "report", "infographic", "spreadsheet",
]

TONE_OPTIONS = [
    "Professional", "Casual", "Academic", "Friendly", "Authoritative",
    "Inspirational", "Technical", "Conversational",
]

AUDIENCE_OPTIONS = [
    "General", "Executive", "Technical", "Sales", "Marketing",
    "Customer", "Internal", "Training Audience",
]


# ============================================================================
# Helper functions
# ============================================================================

def _mask_value(value: str) -> str:
    """Mask an API key/token for display: show first 4 and last 4 characters."""
    if not value:
        return ""
    if len(value) <= 10:
        return value[:2] + "..." + value[-2:]
    return value[:4] + "..." + value[-4:]


def _read_env_file() -> dict[str, str]:
    """Parse the .env file into a dict. Returns empty dict if missing."""
    result: dict[str, str] = {}
    if ENV_FILE_PATH.exists():
        try:
            with open(ENV_FILE_PATH, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, _, value = line.partition("=")
                        key = key.strip()
                        value = value.strip().strip("'\"")
                        result[key] = value
        except Exception:
            pass
    return result


def _write_env_file(env_dict: dict[str, str]) -> bool:
    """Write key=value pairs to the .env file. Preserves comments and order."""
    try:
        lines: list[str] = []
        existing_keys: set[str] = set()

        # Preserve comments and blank lines, update existing keys
        if ENV_FILE_PATH.exists():
            with open(ENV_FILE_PATH, "r") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        lines.append(line.rstrip("\n"))
                        continue
                    if "=" in stripped:
                        key = stripped.partition("=")[0].strip()
                        if key in env_dict:
                            lines.append(f'{key}={env_dict[key]}')
                            existing_keys.add(key)
                        else:
                            lines.append(line.rstrip("\n"))
                            existing_keys.add(key)
                    else:
                        lines.append(line.rstrip("\n"))

        # Append any new keys not already in the file
        for key, value in env_dict.items():
            if key not in existing_keys and value:
                lines.append(f'{key}={value}')

        with open(ENV_FILE_PATH, "w") as f:
            f.write("\n".join(lines) + "\n")
        return True
    except Exception as exc:
        logger.error("Failed to write .env file: %s", exc)
        return False


def _load_brand_config() -> dict:
    """Load brand_config.json. Returns default structure if missing."""
    defaults = {
        "company_name": "",
        "tagline": "",
        "website": "",
        "primary_color": "#0066cc",
        "secondary_color": "#1a1a2e",
        "accent_color": "#f5a623",
        "font_family": "Inter",
        "brand_voice": "",
        "industry": "",
    }
    if BRAND_CONFIG_PATH.exists():
        try:
            with open(BRAND_CONFIG_PATH, "r") as f:
                data = json.load(f)
            # Merge with defaults so all keys exist
            for k, v in defaults.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return defaults


def _save_brand_config(data: dict) -> bool:
    """Persist brand_config.json."""
    try:
        BRAND_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        with open(BRAND_CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as exc:
        logger.error("Failed to save brand config: %s", exc)
        return False


def _dir_size(path: Path) -> int:
    """Compute total size of all files in a directory tree (bytes)."""
    total = 0
    if path.exists():
        for f in path.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
    return total


def _human_size(nbytes: int) -> str:
    """Format a byte count as a human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def _count_files(path: Path) -> int:
    """Count files in a directory (non-recursive)."""
    if not path.exists():
        return 0
    return sum(1 for f in path.iterdir() if f.is_file())


def _test_anthropic_key(api_key: str) -> tuple[bool, str]:
    """Test an Anthropic API key by making a minimal Claude call."""
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say ok"}],
        )
        return True, "Connection successful."
    except Exception as exc:
        return False, f"Failed: {str(exc)[:120]}"


def _test_napkin_key(api_token: str) -> tuple[bool, str]:
    """Test a Napkin AI API token with a simple API call."""
    if not REQUESTS_AVAILABLE:
        return False, "requests library not installed."
    try:
        resp = requests.get(
            "https://api.napkin.ai/v1/account",
            headers={"Authorization": f"Bearer {api_token}"},
            timeout=10,
        )
        if resp.status_code < 400:
            return True, f"Connection successful (HTTP {resp.status_code})."
        return False, f"API returned HTTP {resp.status_code}."
    except Exception as exc:
        return False, f"Failed: {str(exc)[:120]}"


def _test_deepl_key(api_key: str) -> tuple[bool, str]:
    """Test a DeepL API key by checking usage."""
    if not REQUESTS_AVAILABLE:
        return False, "requests library not installed."
    try:
        base = "https://api-free.deepl.com" if api_key.endswith(":fx") else "https://api.deepl.com"
        resp = requests.get(
            f"{base}/v2/usage",
            headers={"Authorization": f"DeepL-Auth-Key {api_key}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            used = data.get("character_count", 0)
            limit = data.get("character_limit", 0)
            return True, f"OK. Usage: {used:,}/{limit:,} characters."
        return False, f"API returned HTTP {resp.status_code}."
    except Exception as exc:
        return False, f"Failed: {str(exc)[:120]}"


def _test_pexels_key(api_key: str) -> tuple[bool, str]:
    """Test a Pexels API key with a search query."""
    if not REQUESTS_AVAILABLE:
        return False, "requests library not installed."
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": "test", "per_page": 1},
            headers={"Authorization": api_key},
            timeout=10,
        )
        if resp.status_code == 200:
            total = resp.json().get("total_results", 0)
            return True, f"Connection successful. {total:,} results available."
        return False, f"API returned HTTP {resp.status_code}."
    except Exception as exc:
        return False, f"Failed: {str(exc)[:120]}"


def _test_presenton_url(url: str) -> tuple[bool, str]:
    """Test a Presenton service URL with an HTTP GET."""
    if not REQUESTS_AVAILABLE:
        return False, "requests library not installed."
    try:
        for endpoint in ["/api/health", "/health", "/"]:
            try:
                resp = requests.get(f"{url.rstrip('/')}{endpoint}", timeout=5)
                if resp.status_code < 500:
                    return True, f"Service reachable at {endpoint} (HTTP {resp.status_code})."
            except requests.RequestException:
                continue
        return False, "Service unreachable on all health endpoints."
    except Exception as exc:
        return False, f"Failed: {str(exc)[:120]}"


def _test_google_auth(json_path: str) -> tuple[bool, str]:
    """Test Google credentials by checking if the JSON file exists and is valid."""
    if not json_path:
        return False, "No path provided."
    p = Path(json_path)
    if not p.exists():
        return False, f"File not found: {json_path}"
    try:
        with open(p, "r") as f:
            data = json.load(f)
        if "type" in data or "installed" in data or "web" in data:
            return True, "JSON credentials file is valid."
        return False, "JSON file does not appear to be a Google credentials file."
    except json.JSONDecodeError:
        return False, "File is not valid JSON."
    except Exception as exc:
        return False, f"Error reading file: {str(exc)[:120]}"


# ============================================================================
# Page header
# ============================================================================
st.title("\u2699\ufe0f Settings & Configuration")
st.markdown("Manage API keys, brand identity, templates, integrations, and system settings.")
st.markdown("---")

# ============================================================================
# Tabs
# ============================================================================
tab_api, tab_brand, tab_prompts, tab_docs, tab_output, tab_integrations, tab_agents, tab_backup, tab_diag = st.tabs([
    "\U0001f511 API Keys",
    "\U0001f3a8 Brand Config",
    "\U0001f4dd Prompt Templates",
    "\U0001f4c4 Document Templates",
    "\U0001f4e4 Output Settings",
    "\U0001f517 Integrations",
    "\U0001f916 Agent Config",
    "\U0001f4be Backup & Restore",
    "\U0001f50d System Diagnostics",
])


# ############################################################################
# TAB 1: API Keys
# ############################################################################
with tab_api:
    st.subheader("API Key Management")
    st.warning(
        "\u26a0\ufe0f API keys are stored in your local `.env` file. "
        "Never commit this file to version control."
    )

    current_env = _read_env_file()

    # Summary metrics
    total_keys = len(API_KEY_INFO)
    configured_count = sum(
        1 for k in API_KEY_INFO if current_env.get(k) or os.getenv(k, "")
    )
    missing_required = [
        k for k in REQUIRED_ENV_KEYS
        if not (current_env.get(k) or os.getenv(k, ""))
    ]

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Total Keys", total_keys)
    col_m2.metric("Configured", configured_count, delta=f"{total_keys - configured_count} missing")
    col_m3.metric(
        "Required Missing",
        len(missing_required),
        delta="OK" if not missing_required else ", ".join(missing_required),
        delta_color="normal" if not missing_required else "inverse",
    )

    st.markdown("---")

    # Per-key cards
    updated_values: dict[str, str] = {}

    for env_key, info in API_KEY_INFO.items():
        current_value = current_env.get(env_key) or os.getenv(env_key, "")
        is_set = bool(current_value)
        badge = (
            '<span class="status-badge status-ok">Configured</span>'
            if is_set
            else '<span class="status-badge status-missing">Missing</span>'
        )
        req_tag = " (Required)" if info["required"] else " (Optional)"

        st.markdown(
            f'<div class="key-card">'
            f'<strong>{info["label"]}</strong>{req_tag} {badge}'
            f'<br><small style="color:#888">{info["description"]}</small>'
            f'</div>',
            unsafe_allow_html=True,
        )

        col_val, col_btn = st.columns([3, 1])

        with col_val:
            if is_set:
                st.text(f"Current: {_mask_value(current_value)}")
            new_val = st.text_input(
                f"New value for {env_key}",
                value="",
                key=f"api_input_{env_key}",
                type="password" if "KEY" in env_key or "TOKEN" in env_key else "default",
                label_visibility="collapsed",
                placeholder=f"Enter new {info['label']}...",
            )
            if new_val:
                updated_values[env_key] = new_val

        with col_btn:
            test_key = f"test_result_{env_key}"
            if st.button("\U0001f50c Test", key=f"test_btn_{env_key}"):
                test_val = new_val if new_val else current_value
                if not test_val:
                    st.session_state[test_key] = (False, "No value to test.")
                else:
                    with st.spinner("Testing..."):
                        if env_key == "ANTHROPIC_API_KEY":
                            st.session_state[test_key] = _test_anthropic_key(test_val)
                        elif env_key == "NAPKIN_API_TOKEN":
                            st.session_state[test_key] = _test_napkin_key(test_val)
                        elif env_key == "DEEPL_API_KEY":
                            st.session_state[test_key] = _test_deepl_key(test_val)
                        elif env_key == "PEXELS_API_KEY":
                            st.session_state[test_key] = _test_pexels_key(test_val)
                        elif env_key == "PRESENTON_URL":
                            st.session_state[test_key] = _test_presenton_url(test_val)
                        elif env_key in ("GOOGLE_SERVICE_ACCOUNT_JSON", "GOOGLE_OAUTH_CREDENTIALS_JSON"):
                            st.session_state[test_key] = _test_google_auth(test_val)
                        else:
                            st.session_state[test_key] = (False, "No test available for this key.")

            if test_key in st.session_state:
                ok, msg = st.session_state[test_key]
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

        st.markdown("")

    st.markdown("---")

    # Save button
    col_save, col_spacer = st.columns([1, 3])
    with col_save:
        if st.button("\U0001f4be Save to .env", type="primary"):
            if not updated_values:
                st.info("No changes to save. Enter new values above first.")
            else:
                merged = {**current_env, **updated_values}
                if _write_env_file(merged):
                    st.success(
                        f"Saved {len(updated_values)} key(s) to `.env`. "
                        "Restart the app for changes to take effect."
                    )
                    # Update environment in current process too
                    for k, v in updated_values.items():
                        os.environ[k] = v
                else:
                    st.error("Failed to write .env file. Check file permissions.")


# ############################################################################
# TAB 2: Brand Configuration
# ############################################################################
with tab_brand:
    st.subheader("Brand Identity Configuration")

    brand_data = _load_brand_config()

    col_form, col_preview = st.columns([2, 1])

    with col_form:
        st.markdown("##### Company Details")
        company_name = st.text_input("Company Name", value=brand_data.get("company_name", ""), key="bc_company")
        tagline = st.text_input("Tagline", value=brand_data.get("tagline", ""), key="bc_tagline")
        website = st.text_input("Website", value=brand_data.get("website", ""), key="bc_website")
        industry = st.text_input("Industry / Sector", value=brand_data.get("industry", ""), key="bc_industry")

        st.markdown("---")
        st.markdown("##### Brand Colors")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            primary_color = st.color_picker(
                "Primary Color",
                value=brand_data.get("primary_color", "#0066cc"),
                key="bc_primary_color",
            )
        with col_c2:
            secondary_color = st.color_picker(
                "Secondary Color",
                value=brand_data.get("secondary_color", "#1a1a2e"),
                key="bc_secondary_color",
            )
        with col_c3:
            accent_color = st.color_picker(
                "Accent Color",
                value=brand_data.get("accent_color", "#f5a623"),
                key="bc_accent_color",
            )

        st.markdown("---")
        st.markdown("##### Typography & Voice")
        font_family = st.text_input(
            "Font Family",
            value=brand_data.get("font_family", "Inter"),
            key="bc_font",
        )
        brand_voice = st.text_area(
            "Brand Voice Description",
            value=brand_data.get("brand_voice", ""),
            height=120,
            key="bc_voice",
            placeholder="Describe the tone, style, and personality of your brand communications...",
        )

        st.markdown("---")
        st.markdown("##### Logo Upload")
        uploaded_logo = st.file_uploader(
            "Upload Logo",
            type=["png", "jpg", "jpeg", "svg", "webp"],
            key="bc_logo_upload",
        )
        if uploaded_logo is not None:
            LOGOS_DIR.mkdir(parents=True, exist_ok=True)
            logo_path = LOGOS_DIR / uploaded_logo.name
            with open(logo_path, "wb") as f:
                f.write(uploaded_logo.getbuffer())
            st.success(f"Logo saved to `{logo_path.relative_to(BASE_DIR)}`")

            # Register in DB
            try:
                session = get_session()
                existing = session.query(BrandAsset).filter_by(
                    filename=uploaded_logo.name, asset_type="logo"
                ).first()
                if not existing:
                    asset = BrandAsset(
                        filename=uploaded_logo.name,
                        file_path=str(logo_path),
                        asset_type="logo",
                    )
                    session.add(asset)
                    session.commit()
                session.close()
            except Exception as exc:
                logger.error("Failed to register logo in DB: %s", exc)

    with col_preview:
        st.markdown("##### Preview")
        st.markdown(
            f'<div class="brand-card">'
            f'<h3 style="color:{primary_color}">{company_name or "Company Name"}</h3>'
            f'<p><em>{tagline or "Your tagline here"}</em></p>'
            f'<p style="font-size:13px; color:#666">{industry or "Industry"}</p>'
            f'<div style="display:flex; gap:8px; margin:12px 0;">'
            f'<div style="width:40px;height:40px;border-radius:8px;background:{primary_color}"></div>'
            f'<div style="width:40px;height:40px;border-radius:8px;background:{secondary_color}"></div>'
            f'<div style="width:40px;height:40px;border-radius:8px;background:{accent_color}"></div>'
            f'</div>'
            f'<p style="font-family:{font_family};font-size:12px">Font: {font_family}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Show existing logos
        st.markdown("##### Current Logos")
        if LOGOS_DIR.exists():
            logo_files = [
                f for f in LOGOS_DIR.iterdir()
                if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
            ]
            if logo_files:
                for lf in logo_files[:4]:
                    try:
                        st.image(str(lf), caption=lf.name, width=150)
                    except Exception:
                        st.text(f"  {lf.name}")
            else:
                st.info("No logos uploaded yet.")
        else:
            st.info("Logos directory does not exist.")

    st.markdown("---")
    col_save_bc, col_reset_bc, _ = st.columns([1, 1, 2])
    with col_save_bc:
        if st.button("\U0001f4be Save Brand Config", type="primary", key="save_brand"):
            new_config = {
                "company_name": company_name,
                "tagline": tagline,
                "website": website,
                "primary_color": primary_color,
                "secondary_color": secondary_color,
                "accent_color": accent_color,
                "font_family": font_family,
                "brand_voice": brand_voice,
                "industry": industry,
            }
            if _save_brand_config(new_config):
                st.success("Brand configuration saved.")
            else:
                st.error("Failed to save brand configuration.")

    with col_reset_bc:
        if st.button("\U0001f504 Reset to Default", key="reset_brand"):
            defaults = {
                "company_name": "",
                "tagline": "",
                "website": "",
                "primary_color": "#0066cc",
                "secondary_color": "#1a1a2e",
                "accent_color": "#f5a623",
                "font_family": "Inter",
                "brand_voice": "",
                "industry": "",
            }
            if _save_brand_config(defaults):
                st.success("Brand configuration reset to defaults. Refresh the page to see changes.")
            else:
                st.error("Failed to reset brand configuration.")


# ############################################################################
# TAB 3: Prompt Templates
# ############################################################################
with tab_prompts:
    st.subheader("Prompt Template Management")

    # ------------------------------------------------------------------
    # Create New Template (expandable at the top)
    # ------------------------------------------------------------------
    with st.expander("\u2795 Create New Prompt Template", expanded=st.session_state.get("new_template_expanded", False)):
        with st.form("new_prompt_template_form", clear_on_submit=True):
            st.markdown("##### New Prompt Template")
            new_pt_name = st.text_input("Template Name", placeholder="e.g., Executive Summary Generator")
            new_pt_type = st.selectbox("Content Type", CONTENT_TYPES_LIST, key="new_pt_type")
            new_pt_system = st.text_area(
                "System Prompt",
                height=120,
                placeholder="You are a professional content writer...",
            )
            new_pt_user = st.text_area(
                "User Prompt Template",
                height=120,
                placeholder="Generate a {content_type} about {topic} for {audience}...",
            )
            new_pt_vars = st.text_input(
                "Variables (comma-separated)",
                placeholder="topic, audience, tone, length",
            )

            submitted = st.form_submit_button("\u2705 Create Template")
            if submitted:
                if not new_pt_name:
                    st.error("Template name is required.")
                else:
                    try:
                        session = get_session()
                        variables = [v.strip() for v in new_pt_vars.split(",") if v.strip()] if new_pt_vars else []
                        pt = PromptTemplate(
                            name=new_pt_name,
                            content_type=new_pt_type,
                            system_prompt=new_pt_system,
                            user_prompt_template=new_pt_user,
                            variables_json=json.dumps(variables),
                            version=1,
                            is_active=True,
                        )
                        session.add(pt)
                        session.commit()
                        session.close()
                        st.success(f"Template '{new_pt_name}' created successfully.")
                    except Exception as exc:
                        st.error(f"Failed to create template: {exc}")

    st.markdown("---")

    # ------------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------------
    col_imp, col_exp = st.columns(2)
    with col_exp:
        if st.button("\U0001f4e5 Export All Templates as JSON", key="export_prompts"):
            try:
                session = get_session()
                templates = session.query(PromptTemplate).all()
                export_data = []
                for t in templates:
                    export_data.append({
                        "name": t.name,
                        "content_type": t.content_type,
                        "system_prompt": t.system_prompt,
                        "user_prompt_template": t.user_prompt_template,
                        "variables_json": t.variables_json,
                        "version": t.version,
                        "is_active": t.is_active,
                    })
                session.close()
                json_bytes = json.dumps(export_data, indent=2).encode("utf-8")
                st.download_button(
                    label="\u2b07\ufe0f Download prompt_templates.json",
                    data=json_bytes,
                    file_name="prompt_templates.json",
                    mime="application/json",
                    key="dl_prompt_templates",
                )
            except Exception as exc:
                st.error(f"Export failed: {exc}")

    with col_imp:
        uploaded_pt = st.file_uploader("Import Templates (JSON)", type=["json"], key="import_prompts")
        if uploaded_pt is not None:
            try:
                data = json.load(uploaded_pt)
                if isinstance(data, list):
                    session = get_session()
                    count = 0
                    for item in data:
                        pt = PromptTemplate(
                            name=item.get("name", "Imported"),
                            content_type=item.get("content_type", "general"),
                            system_prompt=item.get("system_prompt", ""),
                            user_prompt_template=item.get("user_prompt_template", ""),
                            variables_json=item.get("variables_json", "[]"),
                            version=item.get("version", 1),
                            is_active=item.get("is_active", True),
                        )
                        session.add(pt)
                        count += 1
                    session.commit()
                    session.close()
                    st.success(f"Imported {count} template(s).")
                else:
                    st.error("Invalid format. Expected a JSON array of template objects.")
            except Exception as exc:
                st.error(f"Import failed: {exc}")

    st.markdown("---")

    # ------------------------------------------------------------------
    # List existing templates as expandable cards
    # ------------------------------------------------------------------
    try:
        session = get_session()
        all_templates = session.query(PromptTemplate).order_by(PromptTemplate.id.desc()).all()
        session.close()
    except Exception as exc:
        all_templates = []
        st.error(f"Failed to load templates: {exc}")

    if not all_templates:
        st.info("No prompt templates found. Create one above to get started.")
    else:
        st.markdown(f"**{len(all_templates)} template(s) in database**")
        for tmpl in all_templates:
            active_icon = "\U0001f7e2" if tmpl.is_active else "\U0001f534"
            with st.expander(f"{active_icon} {tmpl.name} (v{tmpl.version}) - {tmpl.content_type}"):
                st.markdown(
                    f'<div class="brand-card">'
                    f'<strong>{tmpl.name}</strong> | Type: {tmpl.content_type} | '
                    f'Version: {tmpl.version} | Active: {tmpl.is_active}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Editable fields
                edited_system = st.text_area(
                    "System Prompt",
                    value=tmpl.system_prompt or "",
                    height=100,
                    key=f"pt_sys_{tmpl.id}",
                )
                edited_user = st.text_area(
                    "User Prompt Template",
                    value=tmpl.user_prompt_template or "",
                    height=100,
                    key=f"pt_usr_{tmpl.id}",
                )

                # Variables display
                try:
                    variables = json.loads(tmpl.variables_json) if tmpl.variables_json else []
                except (json.JSONDecodeError, TypeError):
                    variables = []
                st.markdown(f"**Variables:** `{', '.join(variables) if variables else 'None'}`")

                edited_active = st.checkbox(
                    "Active",
                    value=tmpl.is_active,
                    key=f"pt_active_{tmpl.id}",
                )

                # Action buttons
                col_s, col_d, col_c = st.columns(3)
                with col_s:
                    if st.button("\U0001f4be Save", key=f"pt_save_{tmpl.id}"):
                        try:
                            session = get_session()
                            db_tmpl = session.query(PromptTemplate).get(tmpl.id)
                            if db_tmpl:
                                db_tmpl.system_prompt = edited_system
                                db_tmpl.user_prompt_template = edited_user
                                db_tmpl.is_active = edited_active
                                session.commit()
                                st.success("Template updated.")
                            session.close()
                        except Exception as exc:
                            st.error(f"Save failed: {exc}")

                with col_d:
                    if st.button("\U0001f5d1\ufe0f Delete", key=f"pt_del_{tmpl.id}"):
                        try:
                            session = get_session()
                            db_tmpl = session.query(PromptTemplate).get(tmpl.id)
                            if db_tmpl:
                                session.delete(db_tmpl)
                                session.commit()
                                st.success("Template deleted. Refresh to see changes.")
                            session.close()
                        except Exception as exc:
                            st.error(f"Delete failed: {exc}")

                with col_c:
                    if st.button("\U0001f4cb Clone", key=f"pt_clone_{tmpl.id}"):
                        try:
                            session = get_session()
                            new_version = tmpl.version + 1
                            clone = PromptTemplate(
                                name=f"{tmpl.name} (Copy)",
                                content_type=tmpl.content_type,
                                system_prompt=tmpl.system_prompt,
                                user_prompt_template=tmpl.user_prompt_template,
                                variables_json=tmpl.variables_json,
                                version=new_version,
                                is_active=False,
                            )
                            session.add(clone)
                            session.commit()
                            session.close()
                            st.success(f"Template cloned as v{new_version}. Refresh to see it.")
                        except Exception as exc:
                            st.error(f"Clone failed: {exc}")


# ############################################################################
# TAB 4: Document Templates
# ############################################################################
with tab_docs:
    st.subheader("Document Template Management")

    # ------------------------------------------------------------------
    # Upload new template
    # ------------------------------------------------------------------
    st.markdown("##### Upload New Template")
    uploaded_doc = st.file_uploader(
        "Upload a PPTX or DOCX template",
        type=["pptx", "docx"],
        key="doc_template_upload",
    )
    if uploaded_doc is not None:
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        dest_path = TEMPLATES_DIR / uploaded_doc.name
        with open(dest_path, "wb") as f:
            f.write(uploaded_doc.getbuffer())

        # Determine type from extension
        ext = Path(uploaded_doc.name).suffix.lower().lstrip(".")
        tmpl_type = ext if ext in ("pptx", "docx") else "other"

        tmpl_name = st.text_input(
            "Template Name",
            value=Path(uploaded_doc.name).stem.replace("_", " ").replace("-", " ").title(),
            key="doc_tmpl_name_input",
        )
        tmpl_desc = st.text_input(
            "Description",
            value="",
            key="doc_tmpl_desc_input",
            placeholder="Brief description of this template...",
        )

        if st.button("\U0001f4be Register Template", key="register_uploaded_tmpl"):
            try:
                session = get_session()
                existing = session.query(Template).filter_by(file_path=str(dest_path)).first()
                if existing:
                    st.warning("A template with this file path already exists in the database.")
                else:
                    new_tmpl = Template(
                        name=tmpl_name,
                        template_type=tmpl_type,
                        file_path=str(dest_path),
                        description=tmpl_desc,
                    )
                    session.add(new_tmpl)
                    session.commit()
                    st.success(f"Template '{tmpl_name}' registered successfully.")
                session.close()
            except Exception as exc:
                st.error(f"Failed to register template: {exc}")

    st.markdown("---")

    # ------------------------------------------------------------------
    # List existing templates
    # ------------------------------------------------------------------
    st.markdown("##### Registered Templates")
    try:
        session = get_session()
        doc_templates = session.query(Template).order_by(Template.id.desc()).all()
        session.close()
    except Exception as exc:
        doc_templates = []
        st.error(f"Failed to load templates: {exc}")

    if not doc_templates:
        st.info("No document templates registered. Upload one above to get started.")
    else:
        for dt in doc_templates:
            with st.expander(f"\U0001f4c4 {dt.name} ({dt.template_type.upper()})"):
                st.markdown(
                    f'<div class="brand-card">'
                    f'<strong>{dt.name}</strong><br>'
                    f'<small>Type: {dt.template_type} | Path: {dt.file_path}</small><br>'
                    f'<small>Description: {dt.description or "N/A"} | '
                    f'Usage count: {dt.usage_count or 0}</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                file_exists = Path(dt.file_path).exists() if dt.file_path else False
                if file_exists:
                    st.markdown(
                        '<span class="status-badge status-ok">File exists</span>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<span class="status-badge status-missing">File not found</span>',
                        unsafe_allow_html=True,
                    )

                col_del_dt, col_spacer_dt = st.columns([1, 3])
                with col_del_dt:
                    if st.button("\U0001f5d1\ufe0f Delete", key=f"dt_del_{dt.id}"):
                        try:
                            session = get_session()
                            db_dt = session.query(Template).get(dt.id)
                            if db_dt:
                                session.delete(db_dt)
                                session.commit()
                                st.success("Template deleted. Refresh to see changes.")
                            session.close()
                        except Exception as exc:
                            st.error(f"Delete failed: {exc}")

    st.markdown("---")

    # ------------------------------------------------------------------
    # Scan for unregistered template files
    # ------------------------------------------------------------------
    st.markdown("##### Scan for Unregistered Templates")
    if st.button("\U0001f50d Scan Templates Directory", key="scan_templates_dir"):
        if TEMPLATES_DIR.exists():
            try:
                session = get_session()
                registered_paths = {
                    t.file_path for t in session.query(Template).all()
                }

                unregistered = []
                for f in TEMPLATES_DIR.iterdir():
                    if f.is_file() and f.suffix.lower() in (".pptx", ".docx"):
                        if str(f) not in registered_paths:
                            unregistered.append(f)

                session.close()

                if not unregistered:
                    st.info("All template files in the directory are already registered.")
                else:
                    st.warning(f"Found {len(unregistered)} unregistered template file(s):")
                    for uf in unregistered:
                        col_uf, col_reg = st.columns([3, 1])
                        with col_uf:
                            st.text(f"  {uf.name}")
                        with col_reg:
                            if st.button("Register", key=f"reg_{uf.name}"):
                                try:
                                    session = get_session()
                                    ext = uf.suffix.lower().lstrip(".")
                                    new_t = Template(
                                        name=uf.stem.replace("_", " ").replace("-", " ").title(),
                                        template_type=ext,
                                        file_path=str(uf),
                                        description="Auto-registered from scan.",
                                    )
                                    session.add(new_t)
                                    session.commit()
                                    session.close()
                                    st.success(f"Registered '{uf.name}'.")
                                except Exception as exc:
                                    st.error(f"Failed: {exc}")
            except Exception as exc:
                st.error(f"Scan failed: {exc}")
        else:
            st.info(f"Templates directory does not exist: `{TEMPLATES_DIR}`")


# ############################################################################
# TAB 5: Output Settings
# ############################################################################
with tab_output:
    st.subheader("Output & Generation Settings")

    # ------------------------------------------------------------------
    # Default output settings
    # ------------------------------------------------------------------
    st.markdown("##### Default Output Formats")

    col_out1, col_out2 = st.columns(2)

    with col_out1:
        st.selectbox(
            "Default Presentation Format",
            ["PPTX", "PDF", "HTML"],
            key="out_pres_fmt",
        )
        st.selectbox(
            "Default Document Format",
            ["DOCX", "PDF", "TXT", "HTML"],
            key="out_doc_fmt",
        )
        st.selectbox(
            "Default Visual Format",
            ["PNG", "SVG", "JPG", "PDF"],
            key="out_vis_fmt",
        )

    with col_out2:
        st.selectbox(
            "Default Training Format",
            ["DOCX", "PDF", "PPTX", "HTML"],
            key="out_train_fmt",
        )
        st.selectbox(
            "Default Report Format",
            ["PDF", "DOCX", "HTML"],
            key="out_report_fmt",
        )
        st.selectbox(
            "Default Export Format",
            ["ZIP", "JSON", "PDF"],
            key="out_export_fmt",
        )

    st.markdown("---")
    st.markdown("##### Generation Defaults")

    col_gen1, col_gen2 = st.columns(2)

    with col_gen1:
        st.number_input(
            "Default Slide Count (Presentations)",
            min_value=3,
            max_value=50,
            value=10,
            step=1,
            key="out_slide_count",
        )
        st.selectbox(
            "Default Language",
            SUPPORTED_LANGUAGES,
            key="out_default_lang",
        )
        st.selectbox(
            "Default Audience",
            AUDIENCE_OPTIONS,
            key="out_default_audience",
        )

    with col_gen2:
        st.selectbox(
            "Default Tone",
            TONE_OPTIONS,
            key="out_default_tone",
        )
        st.toggle(
            "Auto-add generated content to library",
            value=True,
            key="out_auto_library",
        )
        st.toggle(
            "Auto-approve generated content",
            value=False,
            key="out_auto_approve",
        )

    st.markdown("---")
    st.markdown("##### Output Directory Usage")

    output_dirs_info = {
        "Presentations": OUTPUT_DIR / "presentations",
        "Documents": OUTPUT_DIR / "documents",
        "Training": OUTPUT_DIR / "training",
        "Visuals": OUTPUT_DIR / "visuals",
        "Infographics": OUTPUT_DIR / "infographics",
        "Translations": OUTPUT_DIR / "translations",
        "Reports": OUTPUT_DIR / "reports",
        "Exports": OUTPUT_DIR / "exports",
    }

    cols_dir = st.columns(4)
    for idx, (dir_label, dir_path) in enumerate(output_dirs_info.items()):
        with cols_dir[idx % 4]:
            size = _dir_size(dir_path)
            count = _count_files(dir_path) if dir_path.exists() else 0
            st.markdown(
                f'<div class="diag-card">'
                f'<strong>{dir_label}</strong><br>'
                f'<span style="font-size:18px;font-weight:700">{_human_size(size)}</span><br>'
                f'<small>{count} file(s)</small>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("##### Cleanup")

    if not st.session_state.get("clean_output_confirm"):
        if st.button("\U0001f9f9 Clean Output Directories", key="clean_out_btn"):
            st.session_state["clean_output_confirm"] = True
            st.rerun()
    else:
        st.warning(
            "This will permanently delete all files in the output directories. "
            "Make sure you have exported anything you need."
        )
        col_yes, col_no, _ = st.columns([1, 1, 2])
        with col_yes:
            if st.button("\u2705 Yes, Delete All", key="clean_confirm_yes", type="primary"):
                deleted = 0
                for dir_path in output_dirs_info.values():
                    if dir_path.exists():
                        for f in dir_path.iterdir():
                            if f.is_file():
                                try:
                                    f.unlink()
                                    deleted += 1
                                except OSError:
                                    pass
                st.session_state["clean_output_confirm"] = False
                st.success(f"Deleted {deleted} file(s) from output directories.")
        with col_no:
            if st.button("\u274c Cancel", key="clean_confirm_no"):
                st.session_state["clean_output_confirm"] = False
                st.rerun()


# ############################################################################
# TAB 6: Integrations
# ############################################################################
with tab_integrations:
    st.subheader("Integration Status & Configuration")

    # ------------------------------------------------------------------
    # Napkin AI
    # ------------------------------------------------------------------
    st.markdown(
        '<div class="integration-card"><h4>\U0001f58c\ufe0f Napkin AI</h4></div>',
        unsafe_allow_html=True,
    )
    col_nap_info, col_nap_test = st.columns([3, 1])
    with col_nap_info:
        napkin_token = get_env("NAPKIN_API_TOKEN")
        is_napkin = bool(napkin_token)
        _napkin_badge = (
            '<span class="status-badge status-ok">Configured</span>'
            if is_napkin
            else '<span class="status-badge status-missing">Not Configured</span>'
        )
        st.markdown(f"**Status:** {_napkin_badge}", unsafe_allow_html=True)
        st.text(f"Token: {_mask_value(napkin_token) if napkin_token else 'Not set'}")
        if NAPKIN_AVAILABLE:
            try:
                from app.integrations.napkin_client import VISUAL_TYPES
                st.text(f"Visual types available: {', '.join(VISUAL_TYPES.keys())}")
            except Exception:
                st.text("Visual types: Unable to load.")
        else:
            st.text("Napkin client module: Not installed")
    with col_nap_test:
        if st.button("\U0001f50c Test Napkin", key="test_napkin_int"):
            if napkin_token:
                with st.spinner("Testing..."):
                    ok, msg = _test_napkin_key(napkin_token)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.error("No API token configured.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # Presenton
    # ------------------------------------------------------------------
    st.markdown(
        '<div class="integration-card"><h4>\U0001f4ca Presenton</h4></div>',
        unsafe_allow_html=True,
    )
    col_pre_info, col_pre_test = st.columns([3, 1])
    with col_pre_info:
        presenton_url = get_env("PRESENTON_URL")
        _presenton_badge = (
            '<span class="status-badge status-ok">URL Configured</span>'
            if presenton_url
            else '<span class="status-badge status-missing">Not Configured</span>'
        )
        st.markdown(f"**Status:** {_presenton_badge}", unsafe_allow_html=True)
        st.text(f"URL: {presenton_url or 'Not set'}")
        st.text(f"Client module: {'Installed' if PRESENTON_AVAILABLE else 'Not installed'}")
    with col_pre_test:
        if st.button("\U0001f50c Test Presenton", key="test_presenton_int"):
            if presenton_url:
                with st.spinner("Testing..."):
                    ok, msg = _test_presenton_url(presenton_url)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.error("No URL configured.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # DeepL
    # ------------------------------------------------------------------
    st.markdown(
        '<div class="integration-card"><h4>\U0001f310 DeepL Translation</h4></div>',
        unsafe_allow_html=True,
    )
    col_dl_info, col_dl_test = st.columns([3, 1])
    with col_dl_info:
        deepl_key = get_env("DEEPL_API_KEY")
        is_deepl = bool(deepl_key)
        _deepl_badge = (
            '<span class="status-badge status-ok">Configured</span>'
            if is_deepl
            else '<span class="status-badge status-missing">Not Configured</span>'
        )
        st.markdown(f"**Status:** {_deepl_badge}", unsafe_allow_html=True)
        st.text(f"Key: {_mask_value(deepl_key) if deepl_key else 'Not set'}")
        st.text(f"Translation module: {'Available' if TRANSLATION_AVAILABLE else 'Not installed'}")
    with col_dl_test:
        if st.button("\U0001f50c Test DeepL", key="test_deepl_int"):
            if deepl_key:
                with st.spinner("Testing..."):
                    ok, msg = _test_deepl_key(deepl_key)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.error("No API key configured.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # Google Workspace
    # ------------------------------------------------------------------
    st.markdown(
        '<div class="integration-card"><h4>\U0001f4e6 Google Workspace</h4></div>',
        unsafe_allow_html=True,
    )
    col_gw_info, col_gw_test = st.columns([3, 1])
    with col_gw_info:
        gsa_json = get_env("GOOGLE_SERVICE_ACCOUNT_JSON")
        oauth_json = get_env("GOOGLE_OAUTH_CREDENTIALS_JSON")
        has_gsa = bool(gsa_json)
        has_oauth = bool(oauth_json)

        if has_gsa:
            auth_method = "Service Account"
        elif has_oauth:
            auth_method = "OAuth"
        else:
            auth_method = "Not configured"

        _gw_badge = (
            '<span class="status-badge status-ok">Configured</span>'
            if (has_gsa or has_oauth)
            else '<span class="status-badge status-missing">Not Configured</span>'
        )
        st.markdown(f"**Status:** {_gw_badge}", unsafe_allow_html=True)
        st.text(f"Auth method: {auth_method}")
        st.text(f"Service account: {'Set' if has_gsa else 'Not set'}")
        st.text(f"OAuth credentials: {'Set' if has_oauth else 'Not set'}")
        st.text(f"Export module: {'Available' if GOOGLE_EXPORT_AVAILABLE else 'Not installed'}")
    with col_gw_test:
        if st.button("\U0001f50c Test Google", key="test_google_int"):
            creds_path = gsa_json or oauth_json
            if creds_path:
                with st.spinner("Testing..."):
                    ok, msg = _test_google_auth(creds_path)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.error("No credentials configured.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # Pexels
    # ------------------------------------------------------------------
    st.markdown(
        '<div class="integration-card"><h4>\U0001f4f7 Pexels Stock Photos</h4></div>',
        unsafe_allow_html=True,
    )
    col_px_info, col_px_test = st.columns([3, 1])
    with col_px_info:
        pexels_key = get_env("PEXELS_API_KEY")
        is_pexels = bool(pexels_key)
        _pexels_badge = (
            '<span class="status-badge status-ok">Configured</span>'
            if is_pexels
            else '<span class="status-badge status-missing">Not Configured</span>'
        )
        st.markdown(f"**Status:** {_pexels_badge}", unsafe_allow_html=True)
        st.text(f"Key: {_mask_value(pexels_key) if pexels_key else 'Not set'}")
    with col_px_test:
        if st.button("\U0001f50c Test Pexels", key="test_pexels_int"):
            if pexels_key:
                with st.spinner("Testing..."):
                    ok, msg = _test_pexels_key(pexels_key)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.error("No API key configured.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # Test All
    # ------------------------------------------------------------------
    if st.button("\U0001f9ea Test All Integrations", key="test_all_integrations"):
        results = {}
        with st.spinner("Testing all integrations..."):
            # Anthropic
            anthropic_key = get_env("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "")
            if anthropic_key:
                results["Anthropic"] = _test_anthropic_key(anthropic_key)
            else:
                results["Anthropic"] = (False, "Not configured")

            # Napkin
            if napkin_token:
                results["Napkin AI"] = _test_napkin_key(napkin_token)
            else:
                results["Napkin AI"] = (False, "Not configured")

            # Presenton
            if presenton_url:
                results["Presenton"] = _test_presenton_url(presenton_url)
            else:
                results["Presenton"] = (False, "Not configured")

            # DeepL
            if deepl_key:
                results["DeepL"] = _test_deepl_key(deepl_key)
            else:
                results["DeepL"] = (False, "Not configured")

            # Pexels
            if pexels_key:
                results["Pexels"] = _test_pexels_key(pexels_key)
            else:
                results["Pexels"] = (False, "Not configured")

            # Google
            creds = gsa_json or oauth_json
            if creds:
                results["Google Workspace"] = _test_google_auth(creds)
            else:
                results["Google Workspace"] = (False, "Not configured")

        st.markdown("##### Results")
        for svc, (ok, msg) in results.items():
            icon = "\u2705" if ok else "\u274c"
            st.markdown(f"{icon} **{svc}**: {msg}")


# ############################################################################
# TAB 7: Agent Configuration
# ############################################################################
with tab_agents:
    st.subheader("Agent Pipeline Configuration")
    st.caption(
        "Configure the multi-agent orchestration pipeline that powers "
        "intelligent content generation with research, writing, visual "
        "generation, and compliance validation."
    )

    # Load current .env values
    _agent_env = {}
    _env_path = BASE_DIR / ".env"
    if _env_path.exists():
        for line in _env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                _agent_env[k.strip()] = v.strip().strip('"').strip("'")

    st.markdown("---")

    # -- Model Selection --
    st.markdown("#### Model Selection")

    agent_col1, agent_col2 = st.columns(2)

    with agent_col1:
        _orch_model = st.selectbox(
            "Orchestrator Model Provider",
            options=["claude", "openai"],
            index=0 if _agent_env.get("ORCHESTRATOR_MODEL", "claude") == "claude" else 1,
            key="agent_orch_model",
            help="Which AI provider to use for request classification and planning.",
        )

        _orch_claude = st.text_input(
            "Orchestrator Claude Model",
            value=_agent_env.get("ORCHESTRATOR_CLAUDE_MODEL", "claude-sonnet-4-20250514"),
            key="agent_orch_claude_model",
            help="Claude model ID used for orchestration when provider is 'claude'.",
        )

        _orch_openai = st.text_input(
            "Orchestrator OpenAI Model",
            value=_agent_env.get("ORCHESTRATOR_OPENAI_MODEL", "gpt-4.1"),
            key="agent_orch_openai_model",
            help="OpenAI model ID used for orchestration when provider is 'openai'.",
        )

    with agent_col2:
        _writer_model = st.text_input(
            "Writer Model",
            value=_agent_env.get("WRITER_MODEL", "claude-sonnet-4-20250514"),
            key="agent_writer_model",
            help="Claude model used by the WriterAgent for content generation.",
        )

        _designer_model = st.text_input(
            "Designer Model",
            value=_agent_env.get("DESIGNER_MODEL", "claude-haiku-4-5-20251001"),
            key="agent_designer_model",
            help="Model used by the DesignerAgent (lightweight tasks).",
        )

    st.markdown("---")

    # -- DALL-E Settings --
    st.markdown("#### DALL-E Image Settings")

    dalle_col1, dalle_col2, dalle_col3 = st.columns(3)

    with dalle_col1:
        _dalle_size = st.selectbox(
            "Default Image Size",
            options=["1024x1024", "1792x1024", "1024x1792"],
            index=["1024x1024", "1792x1024", "1024x1792"].index(
                _agent_env.get("DALLE_IMAGE_SIZE", "1024x1024")
            ) if _agent_env.get("DALLE_IMAGE_SIZE", "1024x1024") in ["1024x1024", "1792x1024", "1024x1792"] else 0,
            key="agent_dalle_size",
        )

    with dalle_col2:
        _dalle_quality = st.selectbox(
            "Default Quality",
            options=["standard", "hd"],
            index=0 if _agent_env.get("DALLE_IMAGE_QUALITY", "standard") == "standard" else 1,
            key="agent_dalle_quality",
        )

    with dalle_col3:
        _dalle_style = st.selectbox(
            "Default Style",
            options=["natural", "vivid"],
            index=0 if _agent_env.get("DALLE_IMAGE_STYLE", "natural") == "natural" else 1,
            key="agent_dalle_style",
        )

    st.markdown("---")

    # -- Retry & Timeout --
    st.markdown("#### Retry & Timeout")

    retry_col1, retry_col2 = st.columns(2)

    with retry_col1:
        _max_retries = st.number_input(
            "Max Compliance Retries",
            min_value=0,
            max_value=5,
            value=int(_agent_env.get("AGENT_MAX_RETRIES", "2")),
            key="agent_max_retries",
            help="How many times the pipeline retries if compliance validation fails.",
        )

    with retry_col2:
        _timeout = st.number_input(
            "Agent Timeout (seconds)",
            min_value=60,
            max_value=900,
            value=int(_agent_env.get("AGENT_TIMEOUT_SECONDS", "300")),
            step=30,
            key="agent_timeout",
            help="Maximum time in seconds for the entire agent pipeline to complete.",
        )

    st.markdown("---")

    # -- Save button --
    if st.button("Save Agent Configuration", type="primary", key="btn_save_agent_config", use_container_width=True):
        agent_updates = {
            "ORCHESTRATOR_MODEL": _orch_model,
            "ORCHESTRATOR_CLAUDE_MODEL": _orch_claude,
            "ORCHESTRATOR_OPENAI_MODEL": _orch_openai,
            "WRITER_MODEL": _writer_model,
            "DESIGNER_MODEL": _designer_model,
            "DALLE_IMAGE_SIZE": _dalle_size,
            "DALLE_IMAGE_QUALITY": _dalle_quality,
            "DALLE_IMAGE_STYLE": _dalle_style,
            "AGENT_MAX_RETRIES": str(_max_retries),
            "AGENT_TIMEOUT_SECONDS": str(_timeout),
        }

        # Read existing .env, update, write back
        try:
            env_lines = []
            existing_keys = set()
            if _env_path.exists():
                for line in _env_path.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#") and "=" in stripped:
                        key = stripped.split("=", 1)[0].strip()
                        if key in agent_updates:
                            env_lines.append(f"{key}={agent_updates[key]}")
                            existing_keys.add(key)
                            continue
                    env_lines.append(line)

            # Append any new keys
            for k, v in agent_updates.items():
                if k not in existing_keys:
                    env_lines.append(f"{k}={v}")

            _env_path.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

            # Also set in current process
            for k, v in agent_updates.items():
                os.environ[k] = v

            st.success("Agent configuration saved successfully!")
        except Exception as save_exc:
            st.error(f"Failed to save agent configuration: {save_exc}")


# ############################################################################
# TAB 8: Backup & Restore
# ############################################################################
with tab_backup:
    st.subheader("Backup & Restore")

    col_backup, col_restore = st.columns(2)

    # ------------------------------------------------------------------
    # Export section
    # ------------------------------------------------------------------
    with col_backup:
        st.markdown("##### Export")

        # Export brand config
        st.markdown(
            '<div class="settings-section"><strong>Brand Configuration</strong></div>',
            unsafe_allow_html=True,
        )
        if BRAND_CONFIG_PATH.exists():
            try:
                brand_bytes = BRAND_CONFIG_PATH.read_bytes()
                st.download_button(
                    label="\u2b07\ufe0f Download brand_config.json",
                    data=brand_bytes,
                    file_name="brand_config.json",
                    mime="application/json",
                    key="dl_brand_config",
                )
            except Exception as exc:
                st.error(f"Failed to read brand config: {exc}")
        else:
            st.info("No brand_config.json found.")

        st.markdown("")

        # Export all settings as ZIP
        st.markdown(
            '<div class="settings-section"><strong>All Settings Bundle</strong></div>',
            unsafe_allow_html=True,
        )
        if st.button("\U0001f4e6 Build Settings Export ZIP", key="build_export_zip"):
            try:
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    # brand_config.json
                    if BRAND_CONFIG_PATH.exists():
                        zf.write(BRAND_CONFIG_PATH, "brand_config.json")

                    # .env (masked)
                    env_data = _read_env_file()
                    masked_lines = []
                    for k, v in env_data.items():
                        masked_lines.append(f"{k}={_mask_value(v)}")
                    zf.writestr(".env.masked", "\n".join(masked_lines))

                    # Prompt templates
                    try:
                        session = get_session()
                        pts = session.query(PromptTemplate).all()
                        pt_export = []
                        for pt in pts:
                            pt_export.append({
                                "name": pt.name,
                                "content_type": pt.content_type,
                                "system_prompt": pt.system_prompt,
                                "user_prompt_template": pt.user_prompt_template,
                                "variables_json": pt.variables_json,
                                "version": pt.version,
                                "is_active": pt.is_active,
                            })
                        session.close()
                        zf.writestr(
                            "prompt_templates.json",
                            json.dumps(pt_export, indent=2),
                        )
                    except Exception:
                        pass

                    # Brand assets (logos, fonts)
                    for asset_dir, prefix in [(LOGOS_DIR, "logos"), (FONTS_DIR, "fonts")]:
                        if asset_dir.exists():
                            for f in asset_dir.iterdir():
                                if f.is_file():
                                    zf.write(f, f"{prefix}/{f.name}")

                buf.seek(0)
                st.download_button(
                    label="\u2b07\ufe0f Download settings_bundle.zip",
                    data=buf.getvalue(),
                    file_name="settings_bundle.zip",
                    mime="application/zip",
                    key="dl_settings_bundle",
                )
            except Exception as exc:
                st.error(f"Export failed: {exc}")

        st.markdown("")

        # Export database
        st.markdown(
            '<div class="settings-section"><strong>Database Export</strong></div>',
            unsafe_allow_html=True,
        )
        if DB_PATH.exists():
            try:
                db_bytes = DB_PATH.read_bytes()
                st.download_button(
                    label="\u2b07\ufe0f Download brand_hub.db",
                    data=db_bytes,
                    file_name="brand_hub.db",
                    mime="application/octet-stream",
                    key="dl_database",
                )
            except Exception as exc:
                st.error(f"Failed to read database: {exc}")
        else:
            st.info("Database file not found.")

        st.markdown("")

        # Export feedback data
        if FEEDBACK_AVAILABLE:
            st.markdown(
                '<div class="settings-section"><strong>Feedback Loop Data</strong></div>',
                unsafe_allow_html=True,
            )
            if st.button("\U0001f4e5 Export Feedback Data", key="export_feedback"):
                try:
                    session = get_session()
                    fb_config = session.query(BrandConfig).filter_by(
                        config_key="feedback_patterns"
                    ).first()
                    session.close()
                    if fb_config and fb_config.config_value:
                        fb_bytes = fb_config.config_value.encode("utf-8")
                        st.download_button(
                            label="\u2b07\ufe0f Download feedback_patterns.json",
                            data=fb_bytes,
                            file_name="feedback_patterns.json",
                            mime="application/json",
                            key="dl_feedback_data",
                        )
                    else:
                        st.info("No feedback data found.")
                except Exception as exc:
                    st.error(f"Export failed: {exc}")

    # ------------------------------------------------------------------
    # Import section
    # ------------------------------------------------------------------
    with col_restore:
        st.markdown("##### Import / Restore")

        # Import brand config
        st.markdown(
            '<div class="settings-section"><strong>Restore Brand Configuration</strong></div>',
            unsafe_allow_html=True,
        )
        uploaded_bc = st.file_uploader(
            "Upload brand_config.json",
            type=["json"],
            key="import_brand_config",
        )
        if uploaded_bc is not None:
            try:
                data = json.load(uploaded_bc)
                if isinstance(data, dict):
                    if _save_brand_config(data):
                        st.success("Brand configuration restored successfully.")
                    else:
                        st.error("Failed to save brand configuration.")
                else:
                    st.error("Invalid format. Expected a JSON object.")
            except Exception as exc:
                st.error(f"Import failed: {exc}")

        st.markdown("")

        # Import settings bundle
        st.markdown(
            '<div class="settings-section"><strong>Restore Settings Bundle</strong></div>',
            unsafe_allow_html=True,
        )
        uploaded_bundle = st.file_uploader(
            "Upload settings_bundle.zip",
            type=["zip"],
            key="import_settings_bundle",
        )
        if uploaded_bundle is not None:
            try:
                with zipfile.ZipFile(io.BytesIO(uploaded_bundle.read())) as zf:
                    names = zf.namelist()
                    restored = []

                    # brand_config.json
                    if "brand_config.json" in names:
                        bc_data = json.loads(zf.read("brand_config.json"))
                        if _save_brand_config(bc_data):
                            restored.append("brand_config.json")

                    # Prompt templates
                    if "prompt_templates.json" in names:
                        pts = json.loads(zf.read("prompt_templates.json"))
                        if isinstance(pts, list):
                            try:
                                session = get_session()
                                for item in pts:
                                    pt = PromptTemplate(
                                        name=item.get("name", "Imported"),
                                        content_type=item.get("content_type", "general"),
                                        system_prompt=item.get("system_prompt", ""),
                                        user_prompt_template=item.get("user_prompt_template", ""),
                                        variables_json=item.get("variables_json", "[]"),
                                        version=item.get("version", 1),
                                        is_active=item.get("is_active", True),
                                    )
                                    session.add(pt)
                                session.commit()
                                session.close()
                                restored.append("prompt_templates.json")
                            except Exception:
                                pass

                    # Logos
                    logo_files = [n for n in names if n.startswith("logos/")]
                    if logo_files:
                        LOGOS_DIR.mkdir(parents=True, exist_ok=True)
                        for lf in logo_files:
                            fname = Path(lf).name
                            if fname:
                                with open(LOGOS_DIR / fname, "wb") as f:
                                    f.write(zf.read(lf))
                        restored.append(f"{len(logo_files)} logo(s)")

                    # Fonts
                    font_files = [n for n in names if n.startswith("fonts/")]
                    if font_files:
                        FONTS_DIR.mkdir(parents=True, exist_ok=True)
                        for ff in font_files:
                            fname = Path(ff).name
                            if fname:
                                with open(FONTS_DIR / fname, "wb") as f:
                                    f.write(zf.read(ff))
                        restored.append(f"{len(font_files)} font(s)")

                    if restored:
                        st.success(f"Restored: {', '.join(restored)}")
                    else:
                        st.warning("ZIP did not contain any recognized settings files.")
            except Exception as exc:
                st.error(f"Import failed: {exc}")

        st.markdown("")

        # Import database
        st.markdown(
            '<div class="settings-section"><strong>Restore Database</strong></div>',
            unsafe_allow_html=True,
        )
        uploaded_db = st.file_uploader(
            "Upload brand_hub.db",
            type=["db"],
            key="import_database",
        )
        if uploaded_db is not None:
            st.warning(
                "Restoring the database will replace all current data. "
                "This action cannot be undone."
            )
            if st.button("\u2705 Confirm Database Restore", key="confirm_db_restore"):
                try:
                    DATA_DIR.mkdir(parents=True, exist_ok=True)
                    # Backup existing DB
                    if DB_PATH.exists():
                        backup_name = f"brand_hub_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                        shutil.copy2(DB_PATH, DATA_DIR / backup_name)

                    with open(DB_PATH, "wb") as f:
                        f.write(uploaded_db.getbuffer())
                    st.success(
                        "Database restored. A backup of the previous database was saved. "
                        "Restart the app for changes to take effect."
                    )
                except Exception as exc:
                    st.error(f"Restore failed: {exc}")

        st.markdown("")

        # Import feedback data
        if FEEDBACK_AVAILABLE:
            st.markdown(
                '<div class="settings-section"><strong>Restore Feedback Data</strong></div>',
                unsafe_allow_html=True,
            )
            uploaded_fb = st.file_uploader(
                "Upload feedback_patterns.json",
                type=["json"],
                key="import_feedback",
            )
            if uploaded_fb is not None:
                try:
                    fb_data = uploaded_fb.read().decode("utf-8")
                    # Validate it is valid JSON
                    json.loads(fb_data)

                    session = get_session()
                    existing = session.query(BrandConfig).filter_by(
                        config_key="feedback_patterns"
                    ).first()
                    if existing:
                        existing.config_value = fb_data
                    else:
                        new_conf = BrandConfig(
                            config_key="feedback_patterns",
                            config_value=fb_data,
                        )
                        session.add(new_conf)
                    session.commit()
                    session.close()
                    st.success("Feedback data restored.")
                except json.JSONDecodeError:
                    st.error("Invalid JSON file.")
                except Exception as exc:
                    st.error(f"Import failed: {exc}")


# ############################################################################
# TAB 8: System Diagnostics
# ############################################################################
with tab_diag:
    st.subheader("System Diagnostics")

    # ------------------------------------------------------------------
    # System Information
    # ------------------------------------------------------------------
    st.markdown("##### System Information")

    col_sys1, col_sys2, col_sys3, col_sys4 = st.columns(4)
    with col_sys1:
        st.markdown(
            f'<div class="diag-card">'
            f'<strong>Python</strong><br>'
            f'<span style="font-size:16px;font-weight:700">{platform.python_version()}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_sys2:
        st.markdown(
            f'<div class="diag-card">'
            f'<strong>OS</strong><br>'
            f'<span style="font-size:16px;font-weight:700">{platform.system()} {platform.release()}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_sys3:
        st.markdown(
            f'<div class="diag-card">'
            f'<strong>Architecture</strong><br>'
            f'<span style="font-size:16px;font-weight:700">{platform.machine()}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_sys4:
        st.markdown(
            f'<div class="diag-card">'
            f'<strong>Project Root</strong><br>'
            f'<span style="font-size:12px;font-weight:500">{BASE_DIR}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ------------------------------------------------------------------
    # Installed Packages
    # ------------------------------------------------------------------
    st.markdown("##### Key Package Versions")

    packages_to_check = [
        "streamlit", "anthropic", "sqlalchemy", "requests", "python-dotenv",
        "plotly", "pandas", "pptx", "docx", "chromadb", "deepl", "Pillow",
    ]

    pkg_cols = st.columns(4)
    for idx, pkg_name in enumerate(packages_to_check):
        with pkg_cols[idx % 4]:
            try:
                # Handle packages with different import names
                import_name = pkg_name
                if pkg_name == "python-dotenv":
                    import_name = "dotenv"
                elif pkg_name == "pptx":
                    import_name = "pptx"
                elif pkg_name == "docx":
                    import_name = "docx"
                elif pkg_name == "Pillow":
                    import_name = "PIL"

                mod = __import__(import_name)
                version = getattr(mod, "__version__", "installed")
                st.markdown(
                    f'<span class="status-badge status-ok">{pkg_name}: {version}</span>',
                    unsafe_allow_html=True,
                )
            except ImportError:
                st.markdown(
                    f'<span class="status-badge status-missing">{pkg_name}: not installed</span>',
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # ------------------------------------------------------------------
    # Database Status
    # ------------------------------------------------------------------
    st.markdown("##### Database Status")

    col_db1, col_db2 = st.columns(2)

    with col_db1:
        db_exists = DB_PATH.exists()
        db_size = DB_PATH.stat().st_size if db_exists else 0
        st.markdown(
            f'<div class="diag-card">'
            f'<strong>Database File</strong><br>'
            f'<span style="font-size:16px;font-weight:700">'
            f'{"Exists" if db_exists else "Missing"}'
            f'</span><br>'
            f'<small>{_human_size(db_size)}</small>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_db2:
        table_counts = {}
        try:
            session = get_session()
            table_counts["Brand Assets"] = session.query(BrandAsset).count()
            table_counts["Brand Configs"] = session.query(BrandConfig).count()
            table_counts["Templates"] = session.query(Template).count()
            table_counts["Prompt Templates"] = session.query(PromptTemplate).count()
            table_counts["Generated Content"] = session.query(GeneratedContent).count()
            session.close()
        except Exception as exc:
            st.error(f"Failed to query database: {exc}")

        if table_counts:
            total_rows = sum(table_counts.values())
            st.markdown(
                f'<div class="diag-card">'
                f'<strong>Total Rows</strong><br>'
                f'<span style="font-size:16px;font-weight:700">{total_rows:,}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    if table_counts:
        st.markdown("")
        cols_tc = st.columns(len(table_counts))
        for idx, (table_name, count) in enumerate(table_counts.items()):
            with cols_tc[idx]:
                st.metric(table_name, count)

    st.markdown("---")

    # ------------------------------------------------------------------
    # ChromaDB Status
    # ------------------------------------------------------------------
    st.markdown("##### ChromaDB Status")
    from app.config import CHROMADB_DIR

    chroma_exists = CHROMADB_DIR.exists()
    chroma_size = _dir_size(CHROMADB_DIR)

    col_ch1, col_ch2 = st.columns(2)
    with col_ch1:
        st.markdown(
            f'<div class="diag-card">'
            f'<strong>ChromaDB Directory</strong><br>'
            f'<span style="font-size:16px;font-weight:700">'
            f'{"Exists" if chroma_exists else "Missing"}'
            f'</span><br>'
            f'<small>{_human_size(chroma_size)}</small>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_ch2:
        try:
            import chromadb
            chroma_client = chromadb.PersistentClient(path=str(CHROMADB_DIR))
            collections = chroma_client.list_collections()
            collection_count = len(collections) if collections else 0
            st.markdown(
                f'<div class="diag-card">'
                f'<strong>Collections</strong><br>'
                f'<span style="font-size:16px;font-weight:700">{collection_count}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        except ImportError:
            st.markdown(
                '<div class="diag-card">'
                '<strong>ChromaDB</strong><br>'
                '<span class="status-badge status-warning">Not installed</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        except Exception as exc:
            st.markdown(
                f'<div class="diag-card">'
                f'<strong>ChromaDB</strong><br>'
                f'<span class="status-badge status-warning">Error: {str(exc)[:60]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ------------------------------------------------------------------
    # Disk Space
    # ------------------------------------------------------------------
    st.markdown("##### Disk Space Usage")

    dir_space_info = {
        "Output": OUTPUT_DIR,
        "Data": DATA_DIR,
        "Brand Assets": BRAND_ASSETS_DIR,
    }

    cols_disk = st.columns(len(dir_space_info))
    for idx, (label, dpath) in enumerate(dir_space_info.items()):
        with cols_disk[idx]:
            sz = _dir_size(dpath)
            st.markdown(
                f'<div class="diag-card">'
                f'<strong>{label}</strong><br>'
                f'<span style="font-size:18px;font-weight:700">{_human_size(sz)}</span><br>'
                f'<small>{dpath.relative_to(BASE_DIR)}</small>'
                f'</div>',
                unsafe_allow_html=True,
            )

    try:
        total, used, free = shutil.disk_usage(BASE_DIR)
        st.markdown(
            f"**System disk:** {_human_size(total)} total, "
            f"{_human_size(used)} used, {_human_size(free)} free "
            f"({used / total * 100:.1f}% used)"
        )
    except Exception:
        pass

    st.markdown("---")

    # ------------------------------------------------------------------
    # Test All Integrations
    # ------------------------------------------------------------------
    st.markdown("##### Integration Health Check")
    if st.button("\U0001f9ea Run All Integration Tests", key="diag_test_all"):
        results = {}
        with st.spinner("Running integration tests..."):
            # Anthropic
            ak = get_env("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "")
            results["Anthropic API"] = _test_anthropic_key(ak) if ak else (False, "Not configured")

            # Napkin
            nk = get_env("NAPKIN_API_TOKEN") or os.getenv("NAPKIN_API_TOKEN", "")
            results["Napkin AI"] = _test_napkin_key(nk) if nk else (False, "Not configured")

            # Presenton
            pu = get_env("PRESENTON_URL")
            results["Presenton"] = _test_presenton_url(pu) if pu else (False, "Not configured")

            # DeepL
            dk = get_env("DEEPL_API_KEY")
            results["DeepL"] = _test_deepl_key(dk) if dk else (False, "Not configured")

            # Pexels
            pk = get_env("PEXELS_API_KEY")
            results["Pexels"] = _test_pexels_key(pk) if pk else (False, "Not configured")

            # Google
            gp = get_env("GOOGLE_SERVICE_ACCOUNT_JSON") or get_env("GOOGLE_OAUTH_CREDENTIALS_JSON")
            results["Google Workspace"] = _test_google_auth(gp) if gp else (False, "Not configured")

        for svc, (ok, msg) in results.items():
            icon = "\u2705" if ok else "\u274c"
            st.markdown(f"{icon} **{svc}:** {msg}")

    st.markdown("---")

    # ------------------------------------------------------------------
    # Recent Logs
    # ------------------------------------------------------------------
    st.markdown("##### Recent Logs")

    log_file = BASE_DIR / "logs" / "app.log"
    alt_log_file = BASE_DIR / "app.log"

    active_log = None
    if log_file.exists():
        active_log = log_file
    elif alt_log_file.exists():
        active_log = alt_log_file

    if active_log:
        try:
            with open(active_log, "r") as f:
                lines = f.readlines()
            # Show last 50 lines
            tail = lines[-50:] if len(lines) > 50 else lines
            st.code("".join(tail), language="log")
        except Exception as exc:
            st.warning(f"Could not read log file: {exc}")
    else:
        st.info(
            "No log file found. Logs may be displayed in the console. "
            f"Checked: `{log_file.relative_to(BASE_DIR)}`, `app.log`"
        )

    st.markdown("---")

    # ------------------------------------------------------------------
    # Destructive Actions
    # ------------------------------------------------------------------
    st.markdown("##### Maintenance Actions")

    col_maint1, col_maint2 = st.columns(2)

    with col_maint1:
        st.markdown(
            '<div class="settings-section">'
            '<strong>Recreate Directories</strong><br>'
            '<small>Ensures all required project directories exist.</small>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("\U0001f4c1 Recreate Directories", key="recreate_dirs"):
            try:
                ensure_directories()
                st.success(f"All {len(ALL_DIRS)} directories verified/created.")
            except Exception as exc:
                st.error(f"Failed: {exc}")

    with col_maint2:
        st.markdown(
            '<div class="settings-section">'
            '<strong>Reset Database</strong><br>'
            '<small style="color:#dc3545">Drops and recreates all tables. All data will be lost.</small>'
            '</div>',
            unsafe_allow_html=True,
        )

        if not st.session_state.get("reset_db_confirm_1"):
            if st.button("\u26a0\ufe0f Reset Database", key="reset_db_btn"):
                st.session_state["reset_db_confirm_1"] = True
                st.rerun()
        elif not st.session_state.get("reset_db_confirm_2"):
            st.error("Are you sure? This will delete ALL data in the database.")
            col_y1, col_n1, _ = st.columns([1, 1, 2])
            with col_y1:
                if st.button("Yes, I am sure", key="reset_db_confirm_1_btn"):
                    st.session_state["reset_db_confirm_2"] = True
                    st.rerun()
            with col_n1:
                if st.button("Cancel", key="reset_db_cancel_1"):
                    st.session_state["reset_db_confirm_1"] = False
                    st.rerun()
        else:
            st.error(
                "FINAL WARNING: This action is irreversible. "
                "All brand assets, templates, generated content, and configuration will be deleted."
            )
            col_y2, col_n2, _ = st.columns([1, 1, 2])
            with col_y2:
                if st.button("\U0001f6a8 RESET NOW", key="reset_db_final", type="primary"):
                    try:
                        from app.database.models import Base, engine

                        # Backup first
                        if DB_PATH.exists():
                            backup_name = f"brand_hub_pre_reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                            shutil.copy2(DB_PATH, DATA_DIR / backup_name)
                            st.info(f"Backup saved as `{backup_name}`")

                        Base.metadata.drop_all(bind=engine)
                        Base.metadata.create_all(bind=engine)
                        st.session_state["reset_db_confirm_1"] = False
                        st.session_state["reset_db_confirm_2"] = False
                        st.success("Database has been reset. All tables recreated.")
                    except Exception as exc:
                        st.error(f"Reset failed: {exc}")
            with col_n2:
                if st.button("Cancel", key="reset_db_cancel_2"):
                    st.session_state["reset_db_confirm_1"] = False
                    st.session_state["reset_db_confirm_2"] = False
                    st.rerun()


# ============================================================================
# Footer
# ============================================================================
st.markdown("---")
st.markdown(
    '<div style="text-align:center; color:#888; font-size:12px; padding:16px 0">'
    'Brand Intelligence Content Hub &mdash; Settings & Configuration'
    '</div>',
    unsafe_allow_html=True,
)
