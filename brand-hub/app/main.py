"""
Brand Intelligence Content Hub - Main Application Entry Point

Streamlit multi-page application with sidebar navigation,
database initialization, and environment validation.
"""

import sys
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so app.* imports work when
# Streamlit is launched from any directory.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import (
    BASE_DIR,
    REQUIRED_ENV_KEYS,
    OPTIONAL_ENV_KEYS,
    ensure_directories,
    get_env,
    validate_env,
)
from app.database.models import init_db

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Brand Intelligence Content Hub",
    page_icon="\U0001f3e2",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ---- Sidebar ---- */
    [data-testid="stSidebar"] {
        background-color: #1a1a2e;
        color: #e0e0e0;
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #00d2ff;
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] .stMarkdown span {
        color: #c0c0c0;
    }

    /* ---- Branded accent colors ---- */
    .stButton>button {
        background-color: #0066cc;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
        font-weight: 600;
        transition: background-color 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #0052a3;
        color: #ffffff;
    }

    /* ---- Card styling ---- */
    .brand-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
    .brand-card h3 {
        margin-top: 0;
        color: #1a1a2e;
    }
    .brand-card p {
        color: #555;
    }

    /* ---- Status indicator ---- */
    .status-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 6px;
    }
    .status-green { background-color: #28a745; }
    .status-yellow { background-color: #ffc107; }
    .status-red { background-color: #dc3545; }

    /* ---- Metric tweaks ---- */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #0066cc;
    }

    /* ---- Section dividers ---- */
    .section-divider {
        border-top: 2px solid #0066cc;
        margin: 2rem 0 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# One-time initialisation (runs once per session)
# ---------------------------------------------------------------------------
if "initialized" not in st.session_state:
    # Create project directories
    ensure_directories()

    # Initialise the database
    try:
        init_db()
        st.session_state["db_ok"] = True
    except Exception as exc:
        st.session_state["db_ok"] = False
        st.session_state["db_error"] = str(exc)

    # Validate environment configuration
    env_warnings: list[str] = []
    env_present: dict[str, str] = {}
    for key in REQUIRED_ENV_KEYS:
        import os
        val = os.getenv(key, "").strip()
        if val:
            env_present[key] = val
        else:
            env_warnings.append(key)

    st.session_state["env_present"] = env_present
    st.session_state["env_warnings"] = env_warnings
    st.session_state["initialized"] = True

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## \U0001f3e2 Brand Intelligence")
    st.markdown("### Content Hub")
    st.caption("AI-powered brand management and content generation platform")
    st.markdown("---")

    st.markdown("#### Navigation")
    st.markdown(
        "Use the **page selector** in the sidebar above to navigate between modules. "
        "Each page handles a specific part of the brand intelligence workflow."
    )

    st.markdown("---")

    # System status indicator
    st.markdown("#### System Status")
    db_ok = st.session_state.get("db_ok", False)
    env_warnings = st.session_state.get("env_warnings", [])

    if db_ok and not env_warnings:
        st.markdown(
            '<span class="status-dot status-green"></span> All systems operational',
            unsafe_allow_html=True,
        )
    elif db_ok and env_warnings:
        st.markdown(
            '<span class="status-dot status-yellow"></span> Running with warnings',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="status-dot status-red"></span> System issues detected',
            unsafe_allow_html=True,
        )

    if env_warnings:
        with st.expander("Missing API Keys"):
            for key in env_warnings:
                st.warning(f"`{key}` not configured")

    st.markdown("---")
    st.markdown(
        "<small style='color:#888;'>Brand Intelligence Content Hub<br>"
        "Version 1.0.0 &middot; Phase 1</small>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Main content area - Welcome page (shown when running main.py directly)
# ---------------------------------------------------------------------------
st.title("\U0001f3e2 Brand Intelligence Content Hub")
st.markdown("---")

st.markdown(
    """
    Welcome to the **Brand Intelligence Content Hub** -- your centralized platform for
    managing brand identity and generating on-brand content at scale.

    ### Getting Started

    1. **Dashboard** -- View brand health score, recent activity, and system status.
    2. **Brand Repository** -- Set up your brand identity: colors, fonts, voice, terminology, and templates.
    3. **Content Generator** -- Generate branded presentations, documents, and training materials.
    4. **Content Library** -- Browse, search, and reuse previously generated content.

    Use the sidebar to navigate between modules.
    """
)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        '<div class="brand-card">'
        "<h3>\U0001f3af Brand Setup</h3>"
        "<p>Configure your brand identity with the Brand Wizard. "
        "Extract colors, voice, and terminology from existing materials.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        '<div class="brand-card">'
        "<h3>\u2699\ufe0f Content Engine</h3>"
        "<p>Generate presentations, documents, infographics, and training materials "
        "that perfectly match your brand guidelines.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        '<div class="brand-card">'
        "<h3>\U0001f4ca Analytics</h3>"
        "<p>Track content generation metrics, brand consistency scores, "
        "and usage patterns across your organization.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

# Environment status summary
if st.session_state.get("env_warnings"):
    st.warning(
        "Some API keys are not configured. "
        "Certain features may be unavailable until you add them to your `.env` file."
    )

if not st.session_state.get("db_ok", False):
    st.error(
        f"Database initialization failed: {st.session_state.get('db_error', 'Unknown error')}. "
        "Please check your data directory permissions."
    )

# ---------------------------------------------------------------------------
# Build Document download
# ---------------------------------------------------------------------------
build_doc_path = BASE_DIR / "BUILD_DOCUMENT.md"
if build_doc_path.exists():
    st.markdown("---")
    st.subheader("Build Document")
    st.caption("Download the comprehensive technical build document for this platform.")
    with open(build_doc_path, "r") as f:
        build_doc_content = f.read()
    st.download_button(
        label="Download Build Document",
        data=build_doc_content,
        file_name="Brand_Hub_Build_Document.md",
        mime="text/markdown",
    )
