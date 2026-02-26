"""
Brand Intelligence Content Hub - Content Library

Searchable, filterable catalog of all generated content with approval
workflows, collections management, version history, and usage analytics.
"""

import io
import json
import logging
import os
import shutil
import sys
import zipfile
from collections import Counter
from datetime import datetime, date, timedelta
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
    OUTPUT_DIR,
    PRESENTATIONS_DIR,
    DOCUMENTS_DIR,
    TRAINING_DIR,
    VISUALS_DIR,
    EXPORTS_DIR,
    REPORTS_DIR,
    UPLOADS_DIR,
)
from app.database.models import (
    get_session,
    init_db,
    GeneratedContent,
    ContentLibraryItem,
    Template,
    BrandConfig,
)

# Optional imports for generators (availability flags)
try:
    from app.generators.document_gen import BrandedDocumentGenerator
    DOCUMENT_GEN_AVAILABLE = True
except ImportError:
    DOCUMENT_GEN_AVAILABLE = False

try:
    from app.generators.training_pipeline import TrainingPipeline
    TRAINING_GEN_AVAILABLE = True
except ImportError:
    TRAINING_GEN_AVAILABLE = False

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
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from app.ingestion.smart_classifier import SmartClassifier
    CLASSIFIER_AVAILABLE = True
except ImportError:
    CLASSIFIER_AVAILABLE = False

try:
    from app.ingestion.url_scraper import URLScraper
    SCRAPER_AVAILABLE = True
except ImportError:
    SCRAPER_AVAILABLE = False

try:
    from app.database.vector_store import VectorStore
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False

try:
    from app.ingestion.chunker import SemanticChunker
    CHUNKER_AVAILABLE = True
except ImportError:
    CHUNKER_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Content Library", page_icon="\U0001f4da", layout="wide")

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
.content-card {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 16px;
    margin: 6px 0;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
    transition: box-shadow 0.2s ease;
}
.content-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}
.content-card h4 {
    margin: 0 0 8px 0;
    color: #1a1a2e;
    font-size: 15px;
}
.content-card .meta {
    color: #888;
    font-size: 12px;
    margin-bottom: 6px;
}
.status-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}
.status-approved {
    background: #d4edda;
    color: #155724;
}
.status-pending {
    background: #fff3cd;
    color: #856404;
}
.status-rejected {
    background: #f8d7da;
    color: #721c24;
}
.type-icon {
    display: inline-block;
    width: 28px;
    height: 28px;
    line-height: 28px;
    text-align: center;
    border-radius: 6px;
    font-size: 16px;
    margin-right: 6px;
}
.type-presentation { background: #e8f0fe; }
.type-document { background: #e6f4ea; }
.type-training { background: #fef7e0; }
.type-visual { background: #fce8e6; }
.type-quiz { background: #f3e8fd; }
.type-report { background: #e8eaed; }
.stars {
    color: #f5a623;
    font-size: 14px;
    letter-spacing: 1px;
}
.download-count {
    color: #666;
    font-size: 12px;
}
.collection-card {
    background: linear-gradient(135deg, #f0f4ff 0%, #ffffff 100%);
    border: 1px solid #c5d5f7;
    border-radius: 10px;
    padding: 16px;
    margin: 6px 0;
}
.version-badge {
    background: #e8f0fe;
    color: #1a73e8;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
}
.stat-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
    border: 1px solid #e0e0e0;
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
# Session state defaults
# ---------------------------------------------------------------------------
_session_defaults = {
    "cl_page": 0,
    "cl_per_page": 12,
    "cl_sort": "Newest First",
    "cl_selected_item": None,
    "cl_search_query": "",
    "cl_filter_types": [],
    "cl_filter_formats": [],
    "cl_filter_rating": (1, 5),
    "cl_filter_approval": "All",
    "cl_filter_tags": "",
    "cl_filter_date_start": None,
    "cl_filter_date_end": None,
    "cl_approval_notes": {},
    "cl_approval_selected": [],
    "cl_collection_name": "",
    "cl_collection_items": [],
}
for key, default in _session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONTENT_TYPE_ICONS = {
    "presentation": "\U0001f4ca",
    "document": "\U0001f4c4",
    "training": "\U0001f393",
    "visual": "\U0001f3a8",
    "quiz": "\U0001f9e9",
    "report": "\U0001f4cb",
    "infographic": "\U0001f4ca",
    "template": "\U0001f4d0",
    "export": "\U0001f4e6",
    "other": "\U0001f4c1",
}

CONTENT_TYPE_CSS = {
    "presentation": "type-presentation",
    "document": "type-document",
    "training": "type-training",
    "visual": "type-visual",
    "quiz": "type-quiz",
    "report": "type-report",
}

FORMAT_EXTENSIONS = [
    "PPTX", "DOCX", "PDF", "XLSX", "PNG", "SVG", "JPG", "HTML", "TXT", "JSON", "ZIP",
]

CONTENT_TYPES = [
    "presentation", "document", "training", "visual", "quiz",
    "report", "infographic", "template", "export",
]

SORT_OPTIONS = {
    "Newest First": ("generated_at", "desc"),
    "Oldest First": ("generated_at", "asc"),
    "Highest Rated": ("user_rating", "desc"),
    "Most Downloads": ("download_count", "desc"),
    "Title A-Z": ("title", "asc"),
    "Title Z-A": ("title", "desc"),
}

# Output directory map for file scanning
OUTPUT_DIRS = {
    "presentation": PRESENTATIONS_DIR,
    "document": DOCUMENTS_DIR,
    "training": TRAINING_DIR,
    "visual": VISUALS_DIR,
    "export": EXPORTS_DIR,
    "report": REPORTS_DIR,
}


# ===========================================================================
# Helper functions
# ===========================================================================


def _stars_html(rating: int | None) -> str:
    """Return HTML star display for a rating value 1-5."""
    if not rating or rating < 1:
        return '<span class="stars">-----</span>'
    filled = min(int(rating), 5)
    empty = 5 - filled
    return f'<span class="stars">{"*" * filled}{"." * empty}</span>'


def _stars_display(rating: int | None) -> str:
    """Return Unicode star display for a rating value 1-5."""
    if not rating or rating < 1:
        return "\u2606" * 5
    filled = min(int(rating), 5)
    empty = 5 - filled
    return "\u2605" * filled + "\u2606" * empty


def _approval_badge(is_approved: bool | None) -> str:
    """Return an HTML badge for approval status."""
    if is_approved is True:
        return '<span class="status-badge status-approved">Approved</span>'
    elif is_approved is False:
        return '<span class="status-badge status-rejected">Rejected</span>'
    return '<span class="status-badge status-pending">Pending</span>'


def _type_icon_html(content_type: str) -> str:
    """Return an HTML icon span for a content type."""
    icon = CONTENT_TYPE_ICONS.get(content_type, CONTENT_TYPE_ICONS["other"])
    css_class = CONTENT_TYPE_CSS.get(content_type, "type-report")
    return f'<span class="type-icon {css_class}">{icon}</span>'


def _format_date(dt) -> str:
    """Format a datetime object to a friendly string."""
    if not dt:
        return "N/A"
    if isinstance(dt, str):
        return dt
    return dt.strftime("%Y-%m-%d %H:%M")


def _resolve_file_path(output_path: str | None) -> Path | None:
    """Resolve a stored output_path to an absolute filesystem path."""
    if not output_path:
        return None
    p = Path(output_path)
    if p.is_absolute() and p.exists():
        return p
    # Try relative to BASE_DIR
    candidate = BASE_DIR / output_path
    if candidate.exists():
        return candidate
    # Try relative to OUTPUT_DIR
    candidate = OUTPUT_DIR / output_path
    if candidate.exists():
        return candidate
    return None


def _file_size_str(path: Path) -> str:
    """Return a human-readable file size."""
    try:
        size = path.stat().st_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
    except Exception:
        return "N/A"


# ---------------------------------------------------------------------------
# DB query helpers
# ---------------------------------------------------------------------------


def fetch_library_items(
    search: str = "",
    content_types: list[str] | None = None,
    formats: list[str] | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
    rating_min: int = 1,
    rating_max: int = 5,
    approval: str = "All",
    tags: str = "",
    sort_key: str = "Newest First",
) -> list[dict]:
    """Fetch library items with optional filters, joined to GeneratedContent."""
    results = []
    try:
        session = get_session()
        query = (
            session.query(ContentLibraryItem, GeneratedContent)
            .outerjoin(
                GeneratedContent,
                ContentLibraryItem.generated_content_id == GeneratedContent.id,
            )
        )

        # --- Filters ---
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (ContentLibraryItem.title.ilike(search_pattern))
                | (ContentLibraryItem.description.ilike(search_pattern))
                | (ContentLibraryItem.tags.ilike(search_pattern))
            )

        if content_types:
            query = query.filter(
                (GeneratedContent.content_type.in_(content_types))
                | (ContentLibraryItem.category.in_(content_types))
            )

        if formats:
            lower_fmts = [f.lower() for f in formats]
            query = query.filter(GeneratedContent.format.in_(lower_fmts + formats))

        if date_start:
            query = query.filter(GeneratedContent.generated_at >= datetime.combine(date_start, datetime.min.time()))
        if date_end:
            query = query.filter(GeneratedContent.generated_at <= datetime.combine(date_end, datetime.max.time()))

        if rating_min > 1:
            query = query.filter(
                (GeneratedContent.user_rating >= rating_min)
                | (GeneratedContent.user_rating.is_(None))
            )
        if rating_max < 5:
            query = query.filter(
                (GeneratedContent.user_rating <= rating_max)
                | (GeneratedContent.user_rating.is_(None))
            )

        if approval == "Approved":
            query = query.filter(ContentLibraryItem.is_approved.is_(True))
        elif approval == "Pending":
            query = query.filter(ContentLibraryItem.is_approved.is_(False))

        if tags:
            for tag in [t.strip() for t in tags.split(",") if t.strip()]:
                query = query.filter(ContentLibraryItem.tags.ilike(f"%{tag}%"))

        # --- Sorting ---
        sort_col, sort_dir = SORT_OPTIONS.get(sort_key, ("generated_at", "desc"))
        if sort_col == "download_count":
            order = ContentLibraryItem.download_count.desc() if sort_dir == "desc" else ContentLibraryItem.download_count.asc()
        elif sort_col == "title":
            order = ContentLibraryItem.title.asc() if sort_dir == "asc" else ContentLibraryItem.title.desc()
        elif sort_col == "user_rating":
            order = GeneratedContent.user_rating.desc() if sort_dir == "desc" else GeneratedContent.user_rating.asc()
        else:
            order = GeneratedContent.generated_at.desc() if sort_dir == "desc" else GeneratedContent.generated_at.asc()

        query = query.order_by(order)
        rows = query.all()

        for lib_item, gen_content in rows:
            results.append({
                "lib_id": lib_item.id,
                "gen_id": gen_content.id if gen_content else None,
                "title": lib_item.title,
                "description": lib_item.description or "",
                "tags": lib_item.tags or "",
                "category": lib_item.category or (gen_content.content_type if gen_content else "other"),
                "is_approved": lib_item.is_approved,
                "download_count": lib_item.download_count or 0,
                "content_type": gen_content.content_type if gen_content else (lib_item.category or "other"),
                "format": gen_content.format if gen_content else "N/A",
                "output_path": gen_content.output_path if gen_content else None,
                "generated_at": gen_content.generated_at if gen_content else None,
                "rating": gen_content.user_rating if gen_content else None,
                "input_summary": gen_content.input_summary if gen_content else None,
                "generation_time": gen_content.generation_time_seconds if gen_content else None,
                "template_id": gen_content.template_id if gen_content else None,
                "feedback_notes": gen_content.feedback_notes if gen_content else None,
            })

        session.close()
    except Exception as exc:
        logger.warning("Failed to fetch library items: %s", exc)
    return results


def fetch_generated_content_all(sort_key: str = "Newest First") -> list[dict]:
    """Fetch all GeneratedContent rows (including those not yet in the library)."""
    results = []
    try:
        session = get_session()
        query = session.query(GeneratedContent)

        sort_col, sort_dir = SORT_OPTIONS.get(sort_key, ("generated_at", "desc"))
        if sort_col == "user_rating":
            order = GeneratedContent.user_rating.desc() if sort_dir == "desc" else GeneratedContent.user_rating.asc()
        elif sort_col == "title":
            order = GeneratedContent.title.asc() if sort_dir == "asc" else GeneratedContent.title.desc()
        else:
            order = GeneratedContent.generated_at.desc() if sort_dir == "desc" else GeneratedContent.generated_at.asc()

        query = query.order_by(order)
        rows = query.all()

        for row in rows:
            results.append({
                "gen_id": row.id,
                "title": row.title,
                "content_type": row.content_type,
                "format": row.format or "N/A",
                "output_path": row.output_path,
                "generated_at": row.generated_at,
                "rating": row.user_rating,
                "input_summary": row.input_summary,
                "generation_time": row.generation_time_seconds,
                "template_id": row.template_id,
                "feedback_notes": row.feedback_notes,
            })

        session.close()
    except Exception as exc:
        logger.warning("Failed to fetch generated content: %s", exc)
    return results


def fetch_pending_approvals() -> list[dict]:
    """Fetch library items that are not yet approved."""
    results = []
    try:
        session = get_session()
        query = (
            session.query(ContentLibraryItem, GeneratedContent)
            .outerjoin(
                GeneratedContent,
                ContentLibraryItem.generated_content_id == GeneratedContent.id,
            )
            .filter(ContentLibraryItem.is_approved.is_(False))
            .order_by(GeneratedContent.generated_at.desc())
        )
        rows = query.all()

        for lib_item, gen_content in rows:
            results.append({
                "lib_id": lib_item.id,
                "gen_id": gen_content.id if gen_content else None,
                "title": lib_item.title,
                "description": lib_item.description or "",
                "tags": lib_item.tags or "",
                "category": lib_item.category or (gen_content.content_type if gen_content else "other"),
                "is_approved": lib_item.is_approved,
                "download_count": lib_item.download_count or 0,
                "content_type": gen_content.content_type if gen_content else "other",
                "format": gen_content.format if gen_content else "N/A",
                "output_path": gen_content.output_path if gen_content else None,
                "generated_at": gen_content.generated_at if gen_content else None,
                "rating": gen_content.user_rating if gen_content else None,
            })

        session.close()
    except Exception as exc:
        logger.warning("Failed to fetch pending approvals: %s", exc)
    return results


def update_approval_status(lib_id: int, approved: bool) -> bool:
    """Set the is_approved flag on a ContentLibraryItem."""
    try:
        session = get_session()
        item = session.query(ContentLibraryItem).filter(ContentLibraryItem.id == lib_id).first()
        if item:
            item.is_approved = approved
            session.commit()
            session.close()
            return True
        session.close()
    except Exception as exc:
        logger.warning("Failed to update approval: %s", exc)
    return False


def increment_download_count(lib_id: int) -> None:
    """Bump the download counter for a library item."""
    try:
        session = get_session()
        item = session.query(ContentLibraryItem).filter(ContentLibraryItem.id == lib_id).first()
        if item:
            item.download_count = (item.download_count or 0) + 1
            session.commit()
        session.close()
    except Exception as exc:
        logger.warning("Failed to increment download count: %s", exc)


def save_rating(gen_id: int, rating: int) -> bool:
    """Save a user rating on a GeneratedContent record."""
    try:
        session = get_session()
        item = session.query(GeneratedContent).filter(GeneratedContent.id == gen_id).first()
        if item:
            item.user_rating = rating
            session.commit()
            session.close()
            return True
        session.close()
    except Exception as exc:
        logger.warning("Failed to save rating: %s", exc)
    return False


# ---------------------------------------------------------------------------
# Collection helpers (stored in BrandConfig)
# ---------------------------------------------------------------------------

def _collection_key(name: str) -> str:
    """Return the BrandConfig key for a collection."""
    safe = name.strip().lower().replace(" ", "_")
    return f"collection_{safe}"


def load_collections() -> dict[str, dict]:
    """Load all collections from BrandConfig."""
    collections = {}
    try:
        session = get_session()
        rows = (
            session.query(BrandConfig)
            .filter(BrandConfig.config_key.like("collection_%"))
            .all()
        )
        for row in rows:
            try:
                data = json.loads(row.config_value) if row.config_value else {}
                name = data.get("name", row.config_key.replace("collection_", "").replace("_", " ").title())
                collections[row.config_key] = {
                    "name": name,
                    "description": data.get("description", ""),
                    "item_ids": data.get("item_ids", []),
                    "created_at": data.get("created_at", ""),
                    "updated_at": row.updated_at.strftime("%Y-%m-%d %H:%M") if row.updated_at else "",
                }
            except (json.JSONDecodeError, AttributeError):
                pass
        session.close()
    except Exception as exc:
        logger.warning("Failed to load collections: %s", exc)
    return collections


def save_collection(name: str, description: str, item_ids: list[int]) -> bool:
    """Save or update a collection in BrandConfig."""
    key = _collection_key(name)
    data = {
        "name": name,
        "description": description,
        "item_ids": item_ids,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
    }
    try:
        session = get_session()
        existing = session.query(BrandConfig).filter(BrandConfig.config_key == key).first()
        if existing:
            # Preserve created_at from existing
            try:
                old_data = json.loads(existing.config_value) if existing.config_value else {}
                data["created_at"] = old_data.get("created_at", data["created_at"])
            except (json.JSONDecodeError, AttributeError):
                pass
            existing.config_value = json.dumps(data)
        else:
            new_config = BrandConfig(config_key=key, config_value=json.dumps(data))
            session.add(new_config)
        session.commit()
        session.close()
        return True
    except Exception as exc:
        logger.warning("Failed to save collection: %s", exc)
    return False


def delete_collection(key: str) -> bool:
    """Delete a collection from BrandConfig."""
    try:
        session = get_session()
        row = session.query(BrandConfig).filter(BrandConfig.config_key == key).first()
        if row:
            session.delete(row)
            session.commit()
        session.close()
        return True
    except Exception as exc:
        logger.warning("Failed to delete collection: %s", exc)
    return False


# ---------------------------------------------------------------------------
# Approval history helpers (stored in BrandConfig)
# ---------------------------------------------------------------------------

def _load_approval_history() -> list[dict]:
    """Load the approval history log from BrandConfig."""
    try:
        session = get_session()
        row = (
            session.query(BrandConfig)
            .filter(BrandConfig.config_key == "approval_history")
            .first()
        )
        if row and row.config_value:
            history = json.loads(row.config_value)
            session.close()
            return history if isinstance(history, list) else []
        session.close()
    except Exception as exc:
        logger.warning("Failed to load approval history: %s", exc)
    return []


def _save_approval_event(lib_id: int, title: str, action: str, notes: str = "") -> None:
    """Append an event to the approval history log."""
    try:
        session = get_session()
        row = (
            session.query(BrandConfig)
            .filter(BrandConfig.config_key == "approval_history")
            .first()
        )
        history = []
        if row and row.config_value:
            try:
                history = json.loads(row.config_value)
                if not isinstance(history, list):
                    history = []
            except json.JSONDecodeError:
                history = []

        event = {
            "lib_id": lib_id,
            "title": title,
            "action": action,
            "notes": notes,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        }
        history.insert(0, event)
        # Keep last 500 events
        history = history[:500]

        if row:
            row.config_value = json.dumps(history)
        else:
            new_row = BrandConfig(config_key="approval_history", config_value=json.dumps(history))
            session.add(new_row)

        session.commit()
        session.close()
    except Exception as exc:
        logger.warning("Failed to save approval event: %s", exc)


# ---------------------------------------------------------------------------
# File-system scanning helpers
# ---------------------------------------------------------------------------

def scan_output_files() -> list[dict]:
    """Scan output directories for files, returning metadata dicts."""
    files = []
    for category, directory in OUTPUT_DIRS.items():
        if not directory.exists():
            continue
        for fp in directory.rglob("*"):
            if fp.is_file() and not fp.name.startswith("."):
                files.append({
                    "path": fp,
                    "name": fp.name,
                    "category": category,
                    "format": fp.suffix.lstrip(".").upper(),
                    "size": fp.stat().st_size,
                    "modified": datetime.fromtimestamp(fp.stat().st_mtime),
                })
    files.sort(key=lambda x: x["modified"], reverse=True)
    return files


def get_version_candidates() -> list[dict]:
    """Find files that share a base name pattern (potential versions)."""
    all_files = scan_output_files()
    name_groups: dict[str, list] = {}
    for f in all_files:
        # Strip common version suffixes: _v2, _v3, (1), (2), _copy, etc.
        base = f["name"]
        for suffix_pattern in [
            "_v", "_V", "_copy", "_backup", "_old", "_new", " (", "_rev",
        ]:
            idx = base.rfind(suffix_pattern)
            if idx > 0:
                base = base[:idx]
                break
        # Also strip extension for grouping
        stem = Path(base).stem
        if stem not in name_groups:
            name_groups[stem] = []
        name_groups[stem].append(f)

    # Only return groups with 2+ files
    versions = []
    for stem, group in name_groups.items():
        if len(group) >= 2:
            group.sort(key=lambda x: x["modified"], reverse=True)
            versions.append({"base_name": stem, "versions": group})
    return versions


# ===========================================================================
# Page header
# ===========================================================================
st.title("\U0001f4da Content Library")
st.caption("Browse, search, filter, approve, and manage all generated content")
st.markdown("---")

# ---------------------------------------------------------------------------
# Quick stats bar
# ---------------------------------------------------------------------------
try:
    session = get_session()
    total_library = session.query(ContentLibraryItem).count()
    total_generated = session.query(GeneratedContent).count()
    total_approved = session.query(ContentLibraryItem).filter(ContentLibraryItem.is_approved.is_(True)).count()
    total_pending = session.query(ContentLibraryItem).filter(ContentLibraryItem.is_approved.is_(False)).count()
    session.close()
except Exception:
    total_library = 0
    total_generated = 0
    total_approved = 0
    total_pending = 0

qs1, qs2, qs3, qs4 = st.columns(4)
qs1.metric("Library Items", total_library)
qs2.metric("Total Generated", total_generated)
qs3.metric("Approved", total_approved)
qs4.metric("Pending Review", total_pending)

st.markdown("---")

# ===========================================================================
# TABS
# ===========================================================================
tab_ingest, tab_browse, tab_search, tab_approval, tab_collections, tab_versions, tab_stats = st.tabs([
    "\U0001f4e5 Ingest Content",
    "\U0001f4d6 Browse Library",
    "\U0001f50d Search & Filter",
    "\u2705 Approval Workflow",
    "\U0001f4c2 Collections",
    "\U0001f504 Version History",
    "\U0001f4ca Usage Stats",
])


# ===========================================================================
# TAB 0: Ingest Content
# ===========================================================================
with tab_ingest:
    st.subheader("\U0001f4e5 Ingest Content into Library")
    st.caption(
        "Upload files, paste URLs, or import data \u2014 everything gets auto-analyzed, "
        "classified, and organized in your content library."
    )

    ingest_method = st.radio(
        "Import Method",
        ["\U0001f4c1 File Upload", "\U0001f517 URL Import", "\U0001f4cb Bulk Import"],
        horizontal=True,
        key="ingest_method",
        label_visibility="collapsed",
    )

    classifier = SmartClassifier() if CLASSIFIER_AVAILABLE else None

    # ---- FILE UPLOAD --------------------------------------------------------
    if ingest_method == "\U0001f4c1 File Upload":
        st.markdown("#### Upload Files")
        st.caption("Drag and drop any files \u2014 PDFs, documents, presentations, spreadsheets, images, CSVs, and more.")

        uploaded_files = st.file_uploader(
            "Drop files here",
            accept_multiple_files=True,
            type=["pdf", "docx", "pptx", "xlsx", "xls", "csv", "png", "jpg", "jpeg",
                  "gif", "svg", "txt", "md", "json", "html", "xml", "rtf", "bmp",
                  "webp", "tiff", "tsv"],
            key="library_ingest_files",
            label_visibility="collapsed",
        )

        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)} file(s) ready for ingestion**")

            if st.button("\U0001f680 Analyze & Ingest All", key="btn_ingest_files", type="primary"):
                progress = st.progress(0)
                results_container = st.container()

                for idx, uploaded_file in enumerate(uploaded_files):
                    progress.progress((idx + 1) / len(uploaded_files))

                    # Save file
                    from pathlib import Path as _Path
                    dest = UPLOADS_DIR / uploaded_file.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with open(dest, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # Classify
                    with st.spinner(f"Analyzing {uploaded_file.name}..."):
                        if classifier:
                            classification = classifier.classify_file(str(dest))
                        else:
                            ext = _Path(uploaded_file.name).suffix.lower()
                            classification = {
                                "content_type": "general", "category": ext.lstrip("."),
                                "tags": [ext.lstrip(".")], "description": uploaded_file.name,
                                "confidence": 0.3, "extracted_text": "",
                            }

                    # Index in vector store
                    extracted = classification.get("extracted_text", "")
                    if extracted and VECTOR_AVAILABLE and CHUNKER_AVAILABLE:
                        try:
                            chunker = SemanticChunker()
                            chunks = chunker.chunk(extracted)
                            vs = VectorStore()
                            docs = [c["text"] for c in chunks if c.get("text")]
                            metas = [{"source": uploaded_file.name, "chunk": i} for i in range(len(docs))]
                            ids = [f"{uploaded_file.name}_chunk_{i}" for i in range(len(docs))]
                            if docs:
                                vs.add_documents("brand_content", docs, metas, ids)
                        except Exception as ve:
                            logger.warning("Vector indexing failed for %s: %s", uploaded_file.name, ve)

                    # Create ContentLibraryItem
                    session = get_session()
                    try:
                        item = ContentLibraryItem(
                            title=classification.get("description", uploaded_file.name)[:200],
                            description=classification.get("description", ""),
                            tags=", ".join(classification.get("tags", [])),
                            category=classification.get("content_type", "general"),
                            source_type="file_upload",
                            source_path=str(dest),
                            ingested_at=datetime.utcnow(),
                            content_text=extracted[:5000] if extracted else None,
                            auto_classified=classifier is not None,
                            classification_confidence=classification.get("confidence", 0),
                            is_approved=False,
                        )
                        session.add(item)
                        session.commit()

                        with results_container:
                            confidence = classification.get("confidence", 0)
                            conf_color = "\U0001f7e2" if confidence >= 0.7 else "\U0001f7e1" if confidence >= 0.4 else "\U0001f534"
                            st.markdown(
                                f"{conf_color} **{uploaded_file.name}** \u2192 "
                                f"_{classification.get('content_type', 'general').title()}_ | "
                                f"Tags: {', '.join(classification.get('tags', [])[:5])} | "
                                f"Confidence: {confidence:.0%}"
                            )
                    except Exception as exc:
                        session.rollback()
                        with results_container:
                            st.error(f"\u274c {uploaded_file.name}: {exc}")
                    finally:
                        session.close()

                st.success(f"\u2705 Ingested {len(uploaded_files)} file(s) into the content library!")

    # ---- URL IMPORT ---------------------------------------------------------
    elif ingest_method == "\U0001f517 URL Import":
        st.markdown("#### Import from URLs")
        st.caption("Paste one or more URLs (one per line). Content will be scraped, analyzed, and added to your library.")

        urls_text = st.text_area(
            "URLs (one per line)",
            height=150,
            placeholder="https://example.com/blog-post\nhttps://example.com/case-study\nhttps://docs.google.com/document/d/...",
            key="ingest_urls",
        )

        if urls_text and st.button("\U0001f680 Scrape & Ingest URLs", key="btn_ingest_urls", type="primary"):
            urls = [u.strip() for u in urls_text.strip().split("\n") if u.strip()]

            if not urls:
                st.error("No valid URLs provided.")
            elif not SCRAPER_AVAILABLE:
                st.error("URL scraper not available. Install `requests` and `beautifulsoup4`.")
            else:
                progress = st.progress(0)
                results_container = st.container()

                for idx, url in enumerate(urls):
                    progress.progress((idx + 1) / len(urls))

                    with st.spinner(f"Scraping {url}..."):
                        if classifier:
                            classification = classifier.classify_url(url)
                        else:
                            try:
                                scraper = URLScraper()
                                result = scraper.scrape(url)
                                classification = {
                                    "content_type": "reference", "category": "web_content",
                                    "tags": ["url", "web"], "description": result.get("title", url),
                                    "confidence": 0.5, "extracted_text": result.get("text", "")[:3000],
                                }
                            except Exception as exc:
                                classification = {
                                    "content_type": "general", "tags": ["url"],
                                    "description": url, "confidence": 0,
                                    "extracted_text": "", "error": str(exc),
                                }

                    if classification.get("error"):
                        with results_container:
                            st.error(f"\u274c {url}: {classification['error']}")
                        continue

                    # Index in vector store
                    extracted = classification.get("extracted_text", "")
                    if extracted and VECTOR_AVAILABLE and CHUNKER_AVAILABLE:
                        try:
                            chunker = SemanticChunker()
                            chunks = chunker.chunk(extracted)
                            vs = VectorStore()
                            docs = [c["text"] for c in chunks if c.get("text")]
                            metas = [{"source": url, "chunk": i} for i in range(len(docs))]
                            ids = [f"url_{hash(url)}_{i}" for i in range(len(docs))]
                            if docs:
                                vs.add_documents("brand_content", docs, metas, ids)
                        except Exception:
                            pass

                    # Create ContentLibraryItem
                    session = get_session()
                    try:
                        item = ContentLibraryItem(
                            title=classification.get("description", url)[:200],
                            description=classification.get("description", ""),
                            tags=", ".join(classification.get("tags", [])),
                            category=classification.get("content_type", "reference"),
                            source_type="url",
                            source_path=url,
                            ingested_at=datetime.utcnow(),
                            content_text=extracted[:5000] if extracted else None,
                            auto_classified=classifier is not None,
                            classification_confidence=classification.get("confidence", 0),
                            is_approved=False,
                        )
                        session.add(item)
                        session.commit()

                        with results_container:
                            confidence = classification.get("confidence", 0)
                            conf_color = "\U0001f7e2" if confidence >= 0.7 else "\U0001f7e1" if confidence >= 0.4 else "\U0001f534"
                            st.markdown(
                                f"{conf_color} **{classification.get('description', url)[:60]}** \u2192 "
                                f"_{classification.get('content_type', 'reference').title()}_ | "
                                f"Confidence: {confidence:.0%}"
                            )
                    except Exception as exc:
                        session.rollback()
                        with results_container:
                            st.error(f"\u274c {url}: {exc}")
                    finally:
                        session.close()

                st.success(f"\u2705 Ingested {len(urls)} URL(s)!")

    # ---- BULK IMPORT --------------------------------------------------------
    elif ingest_method == "\U0001f4cb Bulk Import":
        st.markdown("#### Bulk Import")
        st.caption("Import multiple items at once \u2014 paste a list of URLs, upload a CSV of links, or provide a folder path.")

        bulk_type = st.selectbox(
            "Bulk Import Type",
            ["CSV of URLs", "Paste URLs (bulk)", "Folder Path"],
            key="bulk_import_type",
        )

        if bulk_type == "CSV of URLs":
            csv_file = st.file_uploader("Upload CSV with URLs", type=["csv", "txt"], key="bulk_csv")
            url_column = st.text_input("URL column name (or leave blank for first column)", key="csv_col")

            if csv_file and st.button("\U0001f680 Import from CSV", key="btn_bulk_csv", type="primary"):
                import csv as csv_mod
                content = csv_file.read().decode("utf-8", errors="replace")
                reader = csv_mod.DictReader(io.StringIO(content))
                urls = []
                for row in reader:
                    if url_column and url_column in row:
                        urls.append(row[url_column].strip())
                    else:
                        # Use first column
                        first_val = list(row.values())[0] if row else ""
                        if first_val and first_val.startswith("http"):
                            urls.append(first_val.strip())

                st.info(f"Found {len(urls)} URLs in CSV. Processing...")
                # Process same as URL import (simplified - just create items)
                count = 0
                for url in urls[:100]:  # Limit to 100
                    session = get_session()
                    try:
                        item = ContentLibraryItem(
                            title=url[:200], description=f"Imported from CSV: {url}",
                            tags="csv-import, url", category="reference",
                            source_type="url", source_path=url,
                            ingested_at=datetime.utcnow(), is_approved=False,
                        )
                        session.add(item)
                        session.commit()
                        count += 1
                    except Exception:
                        session.rollback()
                    finally:
                        session.close()
                st.success(f"\u2705 Imported {count} URLs from CSV!")

        elif bulk_type == "Paste URLs (bulk)":
            urls_text = st.text_area(
                "Paste URLs (one per line)", height=200,
                placeholder="Paste up to 100 URLs here...",
                key="bulk_paste_urls",
            )
            if urls_text and st.button("\U0001f680 Bulk Import URLs", key="btn_bulk_paste", type="primary"):
                urls = [u.strip() for u in urls_text.strip().split("\n") if u.strip() and u.strip().startswith("http")]
                count = 0
                progress = st.progress(0)
                for idx, url in enumerate(urls[:100]):
                    progress.progress((idx + 1) / min(len(urls), 100))
                    session = get_session()
                    try:
                        item = ContentLibraryItem(
                            title=url[:200], description=f"Bulk imported: {url}",
                            tags="bulk-import, url", category="reference",
                            source_type="url", source_path=url,
                            ingested_at=datetime.utcnow(), is_approved=False,
                        )
                        session.add(item)
                        session.commit()
                        count += 1
                    except Exception:
                        session.rollback()
                    finally:
                        session.close()
                st.success(f"\u2705 Imported {count} URLs!")

        elif bulk_type == "Folder Path":
            folder_path = st.text_input(
                "Folder Path",
                placeholder="/path/to/your/documents/folder",
                key="bulk_folder",
            )
            if folder_path and st.button("\U0001f680 Scan & Import Folder", key="btn_bulk_folder", type="primary"):
                from pathlib import Path as _Path
                folder = _Path(folder_path)
                if not folder.exists():
                    st.error("Folder not found.")
                elif not folder.is_dir():
                    st.error("Path is not a directory.")
                else:
                    supported = {".pdf", ".docx", ".pptx", ".xlsx", ".csv", ".txt", ".md",
                                 ".png", ".jpg", ".jpeg", ".json", ".html"}
                    files = [f for f in folder.rglob("*") if f.suffix.lower() in supported and f.is_file()]

                    if not files:
                        st.warning("No supported files found in the folder.")
                    else:
                        st.info(f"Found {len(files)} files. Ingesting...")
                        progress = st.progress(0)
                        count = 0
                        for idx, filepath in enumerate(files[:200]):
                            progress.progress((idx + 1) / min(len(files), 200))

                            if classifier:
                                classification = classifier.classify_file(str(filepath))
                            else:
                                classification = {
                                    "content_type": "general",
                                    "tags": [filepath.suffix.lstrip(".")],
                                    "description": filepath.name,
                                    "confidence": 0.3,
                                }

                            session = get_session()
                            try:
                                item = ContentLibraryItem(
                                    title=classification.get("description", filepath.name)[:200],
                                    description=classification.get("description", ""),
                                    tags=", ".join(classification.get("tags", [])),
                                    category=classification.get("content_type", "general"),
                                    source_type="file_upload",
                                    source_path=str(filepath),
                                    ingested_at=datetime.utcnow(),
                                    auto_classified=classifier is not None,
                                    classification_confidence=classification.get("confidence", 0),
                                    is_approved=False,
                                )
                                session.add(item)
                                session.commit()
                                count += 1
                            except Exception:
                                session.rollback()
                            finally:
                                session.close()

                        st.success(f"\u2705 Ingested {count} files from folder!")

    # --- Ingestion stats ---
    st.markdown("---")
    st.markdown("#### Recent Ingestions")
    session = get_session()
    try:
        recent = (
            session.query(ContentLibraryItem)
            .filter(ContentLibraryItem.source_type.isnot(None))
            .order_by(ContentLibraryItem.id.desc())
            .limit(10)
            .all()
        )
        if recent:
            for item in recent:
                src_icon = {"file_upload": "\U0001f4c1", "url": "\U0001f517", "manual": "\u270f\ufe0f"}.get(item.source_type or "", "\U0001f4c4")
                conf = item.classification_confidence or 0
                conf_color = "\U0001f7e2" if conf >= 0.7 else "\U0001f7e1" if conf >= 0.4 else "\U0001f534"
                st.caption(
                    f"{src_icon} {conf_color} **{item.title[:50]}** | "
                    f"{item.category or 'uncategorized'} | "
                    f"Tags: {item.tags or 'none'}"
                )
        else:
            st.caption("No content ingested yet. Use the options above to get started!")
    except Exception:
        st.caption("Could not load recent ingestions.")
    finally:
        session.close()


    # ---- RE-INDEX / REPAIR ---------------------------------------------------
    st.markdown("---")
    with st.expander("Maintenance: Re-index items with missing content"):
        st.caption(
            "Some library items may not have had their text extracted (e.g. HTML files "
            "uploaded before text extraction was supported). This will re-parse those "
            "files and index them in the search engine."
        )
        if st.button("Re-index items with missing content", key="btn_reindex"):
            session = get_session()
            try:
                items = session.query(ContentLibraryItem).filter(
                    (ContentLibraryItem.content_text.is_(None))
                    | (ContentLibraryItem.content_text == "")
                ).all()
                if not items:
                    st.info("All items already have content indexed.")
                else:
                    progress = st.progress(0)
                    repaired = 0
                    for idx, item in enumerate(items):
                        progress.progress((idx + 1) / len(items))
                        src = item.source_path
                        if not src or not Path(src).exists():
                            continue
                        ext = Path(src).suffix.lower()
                        extracted = ""
                        try:
                            if ext in (".html", ".htm"):
                                raw_html = Path(src).read_text(encoding="utf-8", errors="replace")
                                try:
                                    from bs4 import BeautifulSoup
                                    soup = BeautifulSoup(raw_html, "html.parser")
                                    for tag in soup.find_all(["script", "style", "noscript", "iframe", "svg"]):
                                        tag.decompose()
                                    extracted = soup.get_text(separator="\n", strip=True)
                                except ImportError:
                                    import re as _re
                                    extracted = _re.sub(r"<[^>]+>", " ", raw_html)
                                    extracted = _re.sub(r"\s+", " ", extracted).strip()
                            elif ext in (".txt", ".md", ".csv", ".json", ".tsv", ".xml"):
                                extracted = Path(src).read_text(encoding="utf-8", errors="replace")
                            elif ext == ".pdf":
                                from app.ingestion.pdf_parser import PDFParser
                                extracted = PDFParser().parse(str(src)).get("text", "")
                            elif ext in (".docx", ".doc"):
                                from app.ingestion.docx_parser import DOCXParser
                                extracted = DOCXParser().parse(str(src)).get("text", "")
                            elif ext in (".pptx", ".ppt"):
                                from app.ingestion.pptx_parser import PPTXParser
                                result = PPTXParser().parse(str(src))
                                parts = []
                                for s in result.get("slides", []):
                                    if s.get("title"):
                                        parts.append(s["title"])
                                    parts.extend(s.get("content", []))
                                extracted = "\n".join(parts)
                        except Exception as parse_exc:
                            st.warning(f"Could not parse {Path(src).name}: {parse_exc}")
                            continue

                        if not extracted or len(extracted) < 10:
                            continue

                        # Update DB
                        item.content_text = extracted[:5000]
                        session.commit()

                        # Index in vector store
                        if VECTOR_AVAILABLE and CHUNKER_AVAILABLE:
                            try:
                                chunker = SemanticChunker()
                                chunks = chunker.chunk(extracted)
                                vs = VectorStore()
                                docs = [c["text"] for c in chunks if c.get("text")]
                                fname = Path(src).name
                                metas = [{"source": fname, "chunk": i} for i in range(len(docs))]
                                ids = [f"{fname}_chunk_{i}" for i in range(len(docs))]
                                if docs:
                                    vs.add_documents("brand_content", docs, metas, ids)
                            except Exception as ve:
                                st.warning(f"Vector indexing failed for {Path(src).name}: {ve}")
                        repaired += 1

                    if repaired:
                        st.success(f"Re-indexed {repaired} item(s) successfully!")
                    else:
                        st.info("No items could be re-indexed (source files may be missing).")
            except Exception as exc:
                st.error(f"Re-index failed: {exc}")
            finally:
                session.close()


# ===========================================================================
# TAB 1: Browse Library
# ===========================================================================
with tab_browse:
    st.subheader("Browse Content Library")

    # Controls row
    ctrl1, ctrl2, ctrl3 = st.columns([2, 1, 1])
    with ctrl1:
        browse_sort = st.selectbox(
            "Sort by",
            list(SORT_OPTIONS.keys()),
            index=0,
            key="browse_sort_select",
        )
    with ctrl2:
        items_per_page = st.selectbox(
            "Items per page",
            [6, 9, 12, 18, 24],
            index=2,
            key="browse_per_page",
        )
    with ctrl3:
        view_mode = st.radio(
            "View",
            ["Grid", "List"],
            horizontal=True,
            key="browse_view_mode",
        )

    st.markdown("---")

    # Fetch items
    items = fetch_library_items(sort_key=browse_sort)

    if not items:
        # Also try to show generated content that is not yet in the library
        gen_items = fetch_generated_content_all(sort_key=browse_sort)
        if gen_items:
            st.info(
                f"No items in the curated library yet, but **{len(gen_items)}** generated "
                "content items were found. Use the **Approval Workflow** tab to add items "
                "to the library, or browse generated content below."
            )
            st.markdown("#### Generated Content (not yet in library)")

            # Display generated items in grid
            cols_per_row = 3
            for row_start in range(0, min(len(gen_items), items_per_page), cols_per_row):
                cols = st.columns(cols_per_row)
                for col_idx, col in enumerate(cols):
                    item_idx = row_start + col_idx
                    if item_idx >= len(gen_items) or item_idx >= items_per_page:
                        break
                    item = gen_items[item_idx]
                    with col:
                        icon = CONTENT_TYPE_ICONS.get(item["content_type"], "\U0001f4c1")
                        fmt = item.get("format", "N/A")
                        date_str = _format_date(item.get("generated_at"))
                        rating_str = _stars_display(item.get("rating"))

                        st.markdown(
                            f'<div class="content-card">'
                            f'<h4>{icon} {item["title"]}</h4>'
                            f'<div class="meta">{item["content_type"].title()} | {fmt} | {date_str}</div>'
                            f'<div>{rating_str}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        file_path = _resolve_file_path(item.get("output_path"))
                        if file_path and file_path.exists():
                            with open(file_path, "rb") as f:
                                st.download_button(
                                    label="Download",
                                    data=f.read(),
                                    file_name=file_path.name,
                                    mime="application/octet-stream",
                                    key=f"dl_gen_{item['gen_id']}",
                                    use_container_width=True,
                                )
        else:
            st.info(
                "No content has been generated yet. Head to the **Content Generator**, "
                "**Presentation Studio**, **Document Factory**, or **Training Builder** "
                "to create your first branded output."
            )
    else:
        # Pagination
        total_items = len(items)
        total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
        current_page = min(st.session_state["cl_page"], total_pages - 1)

        page_start = current_page * items_per_page
        page_end = min(page_start + items_per_page, total_items)
        page_items = items[page_start:page_end]

        st.caption(f"Showing {page_start + 1}-{page_end} of {total_items} items")

        if view_mode == "Grid":
            # Grid view: 3 columns
            cols_per_row = 3
            for row_start in range(0, len(page_items), cols_per_row):
                cols = st.columns(cols_per_row)
                for col_idx, col in enumerate(cols):
                    item_idx = row_start + col_idx
                    if item_idx >= len(page_items):
                        break
                    item = page_items[item_idx]
                    with col:
                        icon = CONTENT_TYPE_ICONS.get(item["content_type"], "\U0001f4c1")
                        fmt = item.get("format", "N/A")
                        date_str = _format_date(item.get("generated_at"))
                        rating_str = _stars_display(item.get("rating"))
                        dl_count = item.get("download_count", 0)

                        # Approval badge
                        if item["is_approved"]:
                            badge = '<span class="status-badge status-approved">Approved</span>'
                        else:
                            badge = '<span class="status-badge status-pending">Pending</span>'

                        st.markdown(
                            f'<div class="content-card">'
                            f'<h4>{icon} {item["title"]}</h4>'
                            f'<div class="meta">{item["content_type"].title()} | {fmt} | {date_str}</div>'
                            f'<div style="margin: 4px 0;">{badge}</div>'
                            f'<div>{rating_str} &nbsp; '
                            f'<span class="download-count">\u2b07 {dl_count} downloads</span></div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                        # Expand details
                        with st.expander("Details & Download"):
                            if item.get("description"):
                                st.write(item["description"])
                            if item.get("tags"):
                                st.caption(f"Tags: {item['tags']}")
                            if item.get("input_summary"):
                                st.caption(f"Input: {item['input_summary'][:200]}")
                            if item.get("generation_time"):
                                st.caption(f"Generation time: {item['generation_time']:.1f}s")

                            # Rating
                            new_rating = st.slider(
                                "Rate this content",
                                1, 5,
                                value=item.get("rating") or 3,
                                key=f"rate_browse_{item['lib_id']}",
                            )
                            if st.button("Save Rating", key=f"save_rate_{item['lib_id']}"):
                                if item.get("gen_id") and save_rating(item["gen_id"], new_rating):
                                    st.success("Rating saved!")
                                    st.rerun()

                            # Download
                            file_path = _resolve_file_path(item.get("output_path"))
                            if file_path and file_path.exists():
                                st.caption(f"File: {file_path.name} ({_file_size_str(file_path)})")
                                with open(file_path, "rb") as f:
                                    if st.download_button(
                                        label=f"Download {file_path.name}",
                                        data=f.read(),
                                        file_name=file_path.name,
                                        mime="application/octet-stream",
                                        key=f"dl_browse_{item['lib_id']}",
                                        use_container_width=True,
                                    ):
                                        increment_download_count(item["lib_id"])
                            else:
                                st.caption("File not found on disk.")
        else:
            # List view
            for item in page_items:
                icon = CONTENT_TYPE_ICONS.get(item["content_type"], "\U0001f4c1")
                fmt = item.get("format", "N/A")
                date_str = _format_date(item.get("generated_at"))
                rating_str = _stars_display(item.get("rating"))
                dl_count = item.get("download_count", 0)

                col_info, col_meta, col_action = st.columns([3, 2, 1])
                with col_info:
                    st.markdown(f"**{icon} {item['title']}**")
                    if item.get("description"):
                        st.caption(item["description"][:120])
                with col_meta:
                    status_text = "Approved" if item["is_approved"] else "Pending"
                    st.caption(
                        f"{item['content_type'].title()} | {fmt} | {date_str}\n\n"
                        f"{rating_str} | {status_text} | {dl_count} downloads"
                    )
                with col_action:
                    file_path = _resolve_file_path(item.get("output_path"))
                    if file_path and file_path.exists():
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label="Download",
                                data=f.read(),
                                file_name=file_path.name,
                                mime="application/octet-stream",
                                key=f"dl_list_{item['lib_id']}",
                                use_container_width=True,
                            )
                st.markdown("---")

        # Pagination controls
        if total_pages > 1:
            pag1, pag2, pag3 = st.columns([1, 2, 1])
            with pag1:
                if st.button("\u25c0 Previous", disabled=current_page == 0, key="browse_prev"):
                    st.session_state["cl_page"] = max(0, current_page - 1)
                    st.rerun()
            with pag2:
                st.markdown(
                    f"<div style='text-align:center;padding-top:8px;'>"
                    f"Page {current_page + 1} of {total_pages}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with pag3:
                if st.button("Next \u25b6", disabled=current_page >= total_pages - 1, key="browse_next"):
                    st.session_state["cl_page"] = min(total_pages - 1, current_page + 1)
                    st.rerun()


# ===========================================================================
# TAB 2: Search & Filter
# ===========================================================================
with tab_search:
    st.subheader("Search & Filter Content")

    # Search box
    search_query = st.text_input(
        "Full-text search",
        value=st.session_state["cl_search_query"],
        placeholder="Search by title, description, or tags...",
        key="search_input_main",
    )
    st.session_state["cl_search_query"] = search_query

    # Filter controls in expanders
    with st.expander("Filters", expanded=True):
        fcol1, fcol2 = st.columns(2)

        with fcol1:
            filter_types = st.multiselect(
                "Content Type",
                options=CONTENT_TYPES,
                default=st.session_state["cl_filter_types"],
                format_func=lambda x: f"{CONTENT_TYPE_ICONS.get(x, '')} {x.title()}",
                key="filter_type_select",
            )
            st.session_state["cl_filter_types"] = filter_types

            filter_formats = st.multiselect(
                "Format",
                options=FORMAT_EXTENSIONS,
                default=st.session_state["cl_filter_formats"],
                key="filter_format_select",
            )
            st.session_state["cl_filter_formats"] = filter_formats

            filter_tags = st.text_input(
                "Tags (comma-separated)",
                value=st.session_state["cl_filter_tags"],
                placeholder="e.g. onboarding, sales, Q1",
                key="filter_tags_input",
            )
            st.session_state["cl_filter_tags"] = filter_tags

        with fcol2:
            filter_date_start = st.date_input(
                "Date from",
                value=st.session_state["cl_filter_date_start"],
                key="filter_date_start",
            )
            filter_date_end = st.date_input(
                "Date to",
                value=st.session_state["cl_filter_date_end"],
                key="filter_date_end",
            )
            st.session_state["cl_filter_date_start"] = filter_date_start
            st.session_state["cl_filter_date_end"] = filter_date_end

            filter_rating = st.slider(
                "Rating range",
                1, 5, (1, 5),
                key="filter_rating_slider",
            )
            st.session_state["cl_filter_rating"] = filter_rating

            filter_approval = st.selectbox(
                "Approval Status",
                ["All", "Approved", "Pending"],
                index=["All", "Approved", "Pending"].index(st.session_state["cl_filter_approval"]),
                key="filter_approval_select",
            )
            st.session_state["cl_filter_approval"] = filter_approval

    # Search sort
    search_sort = st.selectbox(
        "Sort results by",
        list(SORT_OPTIONS.keys()),
        index=0,
        key="search_sort_select",
    )

    st.markdown("---")

    # Execute search
    search_results = fetch_library_items(
        search=search_query,
        content_types=filter_types if filter_types else None,
        formats=filter_formats if filter_formats else None,
        date_start=filter_date_start if filter_date_start else None,
        date_end=filter_date_end if filter_date_end else None,
        rating_min=filter_rating[0],
        rating_max=filter_rating[1],
        approval=filter_approval,
        tags=filter_tags,
        sort_key=search_sort,
    )

    # Also search generated content if no library results
    if not search_results and search_query:
        gen_all = fetch_generated_content_all(sort_key=search_sort)
        search_results_gen = [
            g for g in gen_all
            if search_query.lower() in (g.get("title", "") or "").lower()
            or search_query.lower() in (g.get("input_summary", "") or "").lower()
        ]
        if search_results_gen:
            st.info(f"No library items matched, but {len(search_results_gen)} generated items found.")
            if PANDAS_AVAILABLE:
                df = pd.DataFrame(search_results_gen)
                display_cols = ["gen_id", "title", "content_type", "format", "generated_at", "rating"]
                available_cols = [c for c in display_cols if c in df.columns]
                df_display = df[available_cols].copy()
                df_display.columns = [c.replace("_", " ").title() for c in available_cols]
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                for item in search_results_gen[:20]:
                    st.write(f"- **{item['title']}** ({item['content_type']}, {item['format']})")

    if search_results:
        st.success(f"Found **{len(search_results)}** matching items")

        # Results as dataframe
        if PANDAS_AVAILABLE:
            df_data = []
            for item in search_results:
                df_data.append({
                    "ID": item["lib_id"],
                    "Title": item["title"],
                    "Type": item["content_type"].title(),
                    "Format": item.get("format", "N/A"),
                    "Date": _format_date(item.get("generated_at")),
                    "Rating": _stars_display(item.get("rating")),
                    "Status": "Approved" if item["is_approved"] else "Pending",
                    "Downloads": item.get("download_count", 0),
                    "Tags": item.get("tags", ""),
                })
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            for item in search_results:
                icon = CONTENT_TYPE_ICONS.get(item["content_type"], "\U0001f4c1")
                st.write(
                    f"- {icon} **{item['title']}** | "
                    f"{item['content_type'].title()} | {item.get('format', 'N/A')} | "
                    f"{'Approved' if item['is_approved'] else 'Pending'}"
                )

        # Action buttons for each result
        st.markdown("---")
        st.markdown("#### Quick Actions")

        action_item = st.selectbox(
            "Select item",
            options=search_results,
            format_func=lambda x: f"{x['title']} (ID: {x['lib_id']})",
            key="search_action_item",
        )

        if action_item:
            act1, act2, act3 = st.columns(3)
            with act1:
                file_path = _resolve_file_path(action_item.get("output_path"))
                if file_path and file_path.exists():
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label=f"Download {file_path.name}",
                            data=f.read(),
                            file_name=file_path.name,
                            mime="application/octet-stream",
                            key="dl_search_action",
                            use_container_width=True,
                        )
                else:
                    st.button("Download (file not found)", disabled=True, key="dl_search_disabled")
            with act2:
                new_r = st.slider("Rate", 1, 5, value=action_item.get("rating") or 3, key="rate_search_action")
                if st.button("Save Rating", key="save_rate_search"):
                    if action_item.get("gen_id") and save_rating(action_item["gen_id"], new_r):
                        st.success("Rating saved!")
                        st.rerun()
            with act3:
                if not action_item["is_approved"]:
                    if st.button("Approve", key="approve_search_action", use_container_width=True):
                        if update_approval_status(action_item["lib_id"], True):
                            _save_approval_event(action_item["lib_id"], action_item["title"], "approved")
                            st.success("Item approved!")
                            st.rerun()
                else:
                    st.success("Already approved")

    elif not search_results and not search_query and not filter_types and not filter_formats:
        st.info("Enter a search term or apply filters to find content.")


# ===========================================================================
# TAB 3: Approval Workflow
# ===========================================================================
with tab_approval:
    st.subheader("Content Approval Workflow")

    approval_sub1, approval_sub2 = st.tabs(["Pending Queue", "Approval History"])

    # ----- Pending Queue -----
    with approval_sub1:
        pending_items = fetch_pending_approvals()

        if not pending_items:
            # Check if there are generated items not yet in library
            gen_items = fetch_generated_content_all()
            if gen_items:
                st.info(
                    f"No items pending approval in the library. However, there are "
                    f"**{len(gen_items)}** generated items that could be added to the library."
                )
                st.markdown("#### Add Generated Content to Library")
                st.caption(
                    "Select generated items below and click 'Add to Library' to include "
                    "them in the approval queue."
                )

                add_selections = []
                for item in gen_items[:20]:
                    icon = CONTENT_TYPE_ICONS.get(item["content_type"], "\U0001f4c1")
                    checked = st.checkbox(
                        f"{icon} {item['title']} ({item['content_type']}, {item['format']})",
                        key=f"add_lib_{item['gen_id']}",
                    )
                    if checked:
                        add_selections.append(item)

                if add_selections and st.button("Add Selected to Library", key="bulk_add_library"):
                    added = 0
                    try:
                        session = get_session()
                        for sel in add_selections:
                            # Check if already in library
                            existing = (
                                session.query(ContentLibraryItem)
                                .filter(ContentLibraryItem.generated_content_id == sel["gen_id"])
                                .first()
                            )
                            if not existing:
                                new_item = ContentLibraryItem(
                                    generated_content_id=sel["gen_id"],
                                    title=sel["title"],
                                    description=sel.get("input_summary", ""),
                                    tags="",
                                    category=sel["content_type"],
                                    is_approved=False,
                                    download_count=0,
                                )
                                session.add(new_item)
                                added += 1
                        session.commit()
                        session.close()
                        if added > 0:
                            st.success(f"Added {added} items to the library approval queue!")
                            st.rerun()
                        else:
                            st.warning("Selected items are already in the library.")
                    except Exception as exc:
                        st.error(f"Failed to add items: {exc}")
            else:
                st.info(
                    "No items pending approval. Generate content first, then "
                    "add it to the library for review."
                )
        else:
            st.markdown(f"**{len(pending_items)}** items awaiting review")

            # Bulk action controls
            st.markdown("##### Bulk Actions")
            bulk_select_all = st.checkbox("Select all", key="bulk_select_all_approval")

            selected_for_bulk = []
            for item in pending_items:
                icon = CONTENT_TYPE_ICONS.get(item["content_type"], "\U0001f4c1")

                col_check, col_info, col_preview, col_actions = st.columns([0.5, 3, 2, 2])

                with col_check:
                    is_selected = st.checkbox(
                        "Select",
                        value=bulk_select_all,
                        key=f"bulk_chk_{item['lib_id']}",
                        label_visibility="collapsed",
                    )
                    if is_selected:
                        selected_for_bulk.append(item)

                with col_info:
                    st.markdown(f"**{icon} {item['title']}**")
                    st.caption(
                        f"{item['content_type'].title()} | {item.get('format', 'N/A')} | "
                        f"{_format_date(item.get('generated_at'))}"
                    )
                    if item.get("description"):
                        st.caption(item["description"][:150])

                with col_preview:
                    file_path = _resolve_file_path(item.get("output_path"))
                    if file_path and file_path.exists():
                        st.caption(f"{file_path.name} ({_file_size_str(file_path)})")
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label="Preview / Download",
                                data=f.read(),
                                file_name=file_path.name,
                                mime="application/octet-stream",
                                key=f"dl_approval_{item['lib_id']}",
                                use_container_width=True,
                            )
                    else:
                        st.caption("File not available on disk")

                with col_actions:
                    notes = st.text_input(
                        "Notes",
                        key=f"approval_notes_{item['lib_id']}",
                        placeholder="Optional review notes...",
                        label_visibility="collapsed",
                    )

                    btn1, btn2 = st.columns(2)
                    with btn1:
                        if st.button("\u2705 Approve", key=f"approve_{item['lib_id']}", use_container_width=True):
                            if update_approval_status(item["lib_id"], True):
                                _save_approval_event(item["lib_id"], item["title"], "approved", notes)
                                st.success(f"Approved: {item['title']}")
                                st.rerun()
                    with btn2:
                        if st.button("\u274c Reject", key=f"reject_{item['lib_id']}", use_container_width=True):
                            if update_approval_status(item["lib_id"], False):
                                _save_approval_event(item["lib_id"], item["title"], "rejected", notes)
                                st.warning(f"Rejected: {item['title']}")
                                st.rerun()

                st.markdown("---")

            # Bulk action buttons
            if selected_for_bulk:
                st.markdown(f"**{len(selected_for_bulk)}** items selected")
                bulk1, bulk2, bulk3 = st.columns(3)
                with bulk1:
                    if st.button(
                        f"\u2705 Approve All Selected ({len(selected_for_bulk)})",
                        key="bulk_approve_all",
                        use_container_width=True,
                    ):
                        approved_count = 0
                        for item in selected_for_bulk:
                            if update_approval_status(item["lib_id"], True):
                                _save_approval_event(item["lib_id"], item["title"], "approved", "Bulk approved")
                                approved_count += 1
                        st.success(f"Approved {approved_count} items!")
                        st.rerun()
                with bulk2:
                    if st.button(
                        f"\u274c Reject All Selected ({len(selected_for_bulk)})",
                        key="bulk_reject_all",
                        use_container_width=True,
                    ):
                        rejected_count = 0
                        for item in selected_for_bulk:
                            if update_approval_status(item["lib_id"], False):
                                _save_approval_event(item["lib_id"], item["title"], "rejected", "Bulk rejected")
                                rejected_count += 1
                        st.warning(f"Rejected {rejected_count} items!")
                        st.rerun()

    # ----- Approval History -----
    with approval_sub2:
        st.markdown("#### Approval History Log")

        history = _load_approval_history()
        if history:
            if PANDAS_AVAILABLE:
                df_history = pd.DataFrame(history)
                display_cols = ["timestamp", "title", "action", "notes", "lib_id"]
                available_cols = [c for c in display_cols if c in df_history.columns]
                df_display = df_history[available_cols].copy()
                df_display.columns = [c.replace("_", " ").title() for c in available_cols]
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                for event in history[:50]:
                    action_icon = "\u2705" if event.get("action") == "approved" else "\u274c"
                    st.write(
                        f"- {action_icon} **{event.get('title', 'Unknown')}** -- "
                        f"{event.get('action', 'N/A')} at {event.get('timestamp', 'N/A')}"
                    )
                    if event.get("notes"):
                        st.caption(f"  Notes: {event['notes']}")
        else:
            st.info("No approval actions recorded yet.")


# ===========================================================================
# TAB 4: Collections
# ===========================================================================
with tab_collections:
    st.subheader("Content Collections")
    st.caption("Organize content into named collections for easy access and export")

    col_create, col_manage = st.columns([1, 1])

    # ----- Create Collection -----
    with col_create:
        st.markdown("#### Create New Collection")

        coll_name = st.text_input(
            "Collection Name",
            placeholder="e.g. Q1 Onboarding Package",
            key="new_coll_name",
        )
        coll_desc = st.text_area(
            "Description",
            placeholder="What is this collection for?",
            key="new_coll_desc",
            height=80,
        )

        # Item selector -- all library items
        all_lib_items = fetch_library_items(sort_key="Title A-Z")
        all_gen_items = fetch_generated_content_all(sort_key="Title A-Z")

        # Combine for selection
        selectable_items = {}
        for item in all_lib_items:
            selectable_items[f"lib_{item['lib_id']}"] = f"\U0001f4d6 {item['title']} (Library #{item['lib_id']})"
        for item in all_gen_items:
            selectable_items[f"gen_{item['gen_id']}"] = f"\u2699\ufe0f {item['title']} (Generated #{item['gen_id']})"

        if selectable_items:
            selected_keys = st.multiselect(
                "Add items to collection",
                options=list(selectable_items.keys()),
                format_func=lambda k: selectable_items[k],
                key="coll_item_select",
            )
        else:
            selected_keys = []
            st.caption("No items available. Generate content first.")

        if st.button("Create Collection", key="create_coll_btn", use_container_width=True):
            if not coll_name.strip():
                st.error("Please enter a collection name.")
            else:
                # Parse selected IDs
                item_ids = []
                for k in selected_keys:
                    try:
                        item_ids.append(int(k.split("_", 1)[1]))
                    except (ValueError, IndexError):
                        pass

                if save_collection(coll_name.strip(), coll_desc.strip(), item_ids):
                    st.success(f"Collection '{coll_name}' created with {len(item_ids)} items!")
                    st.rerun()
                else:
                    st.error("Failed to save collection.")

    # ----- Manage Collections -----
    with col_manage:
        st.markdown("#### Existing Collections")

        collections = load_collections()

        if not collections:
            st.info("No collections created yet. Use the form on the left to create one.")
        else:
            for coll_key, coll_data in collections.items():
                st.markdown(
                    f'<div class="collection-card">'
                    f'<h4>\U0001f4c2 {coll_data["name"]}</h4>'
                    f'<p style="color:#666;font-size:13px;">{coll_data.get("description", "")}</p>'
                    f'<p style="color:#888;font-size:12px;">'
                    f'{len(coll_data.get("item_ids", []))} items | '
                    f'Updated: {coll_data.get("updated_at", "N/A")}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                with st.expander(f"Manage: {coll_data['name']}"):
                    # Show items in collection
                    item_ids = coll_data.get("item_ids", [])
                    if item_ids:
                        st.caption(f"Item IDs: {', '.join(str(i) for i in item_ids)}")

                        # Fetch item details
                        try:
                            session = get_session()
                            items_in_coll = (
                                session.query(GeneratedContent)
                                .filter(GeneratedContent.id.in_(item_ids))
                                .all()
                            )
                            for ci in items_in_coll:
                                icon = CONTENT_TYPE_ICONS.get(ci.content_type, "\U0001f4c1")
                                st.write(f"- {icon} {ci.title} ({ci.content_type}, {ci.format or 'N/A'})")
                            session.close()
                        except Exception:
                            st.caption("Could not load item details.")
                    else:
                        st.caption("No items in this collection.")

                    # Export as ZIP
                    if item_ids and st.button(
                        "Export as ZIP",
                        key=f"export_zip_{coll_key}",
                        use_container_width=True,
                    ):
                        try:
                            session = get_session()
                            gen_items_for_zip = (
                                session.query(GeneratedContent)
                                .filter(GeneratedContent.id.in_(item_ids))
                                .all()
                            )
                            session.close()

                            zip_buffer = io.BytesIO()
                            files_added = 0
                            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                                for gi in gen_items_for_zip:
                                    fp = _resolve_file_path(gi.output_path)
                                    if fp and fp.exists():
                                        zf.write(fp, fp.name)
                                        files_added += 1

                            if files_added > 0:
                                zip_buffer.seek(0)
                                safe_name = coll_data["name"].replace(" ", "_").lower()
                                st.download_button(
                                    label=f"Download ZIP ({files_added} files)",
                                    data=zip_buffer.getvalue(),
                                    file_name=f"collection_{safe_name}.zip",
                                    mime="application/zip",
                                    key=f"dl_zip_{coll_key}",
                                    use_container_width=True,
                                )
                            else:
                                st.warning("No files found on disk for this collection.")
                        except Exception as exc:
                            st.error(f"Export failed: {exc}")

                    # Share as manifest JSON
                    if st.button(
                        "Export Manifest JSON",
                        key=f"manifest_{coll_key}",
                        use_container_width=True,
                    ):
                        manifest = {
                            "collection_name": coll_data["name"],
                            "description": coll_data.get("description", ""),
                            "created_at": coll_data.get("created_at", ""),
                            "item_count": len(item_ids),
                            "item_ids": item_ids,
                            "exported_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        # Try to add file names
                        try:
                            session = get_session()
                            gen_manifest = (
                                session.query(GeneratedContent)
                                .filter(GeneratedContent.id.in_(item_ids))
                                .all()
                            )
                            manifest["items"] = [
                                {
                                    "id": g.id,
                                    "title": g.title,
                                    "type": g.content_type,
                                    "format": g.format,
                                    "output_path": g.output_path,
                                }
                                for g in gen_manifest
                            ]
                            session.close()
                        except Exception:
                            pass

                        manifest_json = json.dumps(manifest, indent=2)
                        safe_name = coll_data["name"].replace(" ", "_").lower()
                        st.download_button(
                            label="Download Manifest",
                            data=manifest_json,
                            file_name=f"manifest_{safe_name}.json",
                            mime="application/json",
                            key=f"dl_manifest_{coll_key}",
                            use_container_width=True,
                        )

                    # Delete collection
                    if st.button(
                        "Delete Collection",
                        key=f"del_coll_{coll_key}",
                        type="secondary",
                        use_container_width=True,
                    ):
                        if delete_collection(coll_key):
                            st.success(f"Collection '{coll_data['name']}' deleted.")
                            st.rerun()
                        else:
                            st.error("Failed to delete collection.")


# ===========================================================================
# TAB 5: Version History
# ===========================================================================
with tab_versions:
    st.subheader("Version History")
    st.caption(
        "Track file versions for regenerated content. Files with similar names "
        "in the same output directory are grouped as potential versions."
    )

    version_groups = get_version_candidates()

    if not version_groups:
        # Fallback: show all files grouped by directory
        all_files = scan_output_files()
        if all_files:
            st.info(
                f"Found **{len(all_files)}** files in output directories. "
                "No version groups detected (files with similar names). "
                "Below is the full file listing."
            )
            if PANDAS_AVAILABLE:
                df_files = pd.DataFrame([
                    {
                        "Name": f["name"],
                        "Category": f["category"].title(),
                        "Format": f["format"],
                        "Size": _file_size_str(f["path"]),
                        "Modified": f["modified"].strftime("%Y-%m-%d %H:%M"),
                    }
                    for f in all_files[:100]
                ])
                st.dataframe(df_files, use_container_width=True, hide_index=True)
            else:
                for f in all_files[:50]:
                    st.write(
                        f"- **{f['name']}** ({f['category']}, {f['format']}, "
                        f"{_file_size_str(f['path'])}, {f['modified'].strftime('%Y-%m-%d %H:%M')})"
                    )
        else:
            st.info(
                "No output files found. Generate content to see version history."
            )
    else:
        st.success(f"Found **{len(version_groups)}** version groups")

        for group in version_groups:
            with st.expander(f"\U0001f4c4 {group['base_name']} ({len(group['versions'])} versions)"):
                versions = group["versions"]

                # Version comparison
                st.markdown("##### Version Timeline")
                for idx, ver in enumerate(versions):
                    version_label = f"v{len(versions) - idx}"
                    is_latest = idx == 0

                    vcol1, vcol2, vcol3, vcol4 = st.columns([2, 1, 1, 1])
                    with vcol1:
                        label_suffix = " (latest)" if is_latest else ""
                        st.markdown(
                            f'<span class="version-badge">{version_label}{label_suffix}</span> '
                            f'**{ver["name"]}**',
                            unsafe_allow_html=True,
                        )
                    with vcol2:
                        st.caption(f"{ver['format']} | {_file_size_str(ver['path'])}")
                    with vcol3:
                        st.caption(ver["modified"].strftime("%Y-%m-%d %H:%M"))
                    with vcol4:
                        if ver["path"].exists():
                            with open(ver["path"], "rb") as f:
                                st.download_button(
                                    label="Download",
                                    data=f.read(),
                                    file_name=ver["name"],
                                    mime="application/octet-stream",
                                    key=f"dl_ver_{group['base_name']}_{idx}",
                                )

                # Side-by-side comparison
                if len(versions) >= 2:
                    st.markdown("##### Compare Versions")
                    cmp1, cmp2 = st.columns(2)
                    with cmp1:
                        st.markdown(f"**Latest: {versions[0]['name']}**")
                        st.caption(
                            f"Modified: {versions[0]['modified'].strftime('%Y-%m-%d %H:%M')}\n\n"
                            f"Size: {_file_size_str(versions[0]['path'])}\n\n"
                            f"Format: {versions[0]['format']}"
                        )
                    with cmp2:
                        st.markdown(f"**Previous: {versions[1]['name']}**")
                        st.caption(
                            f"Modified: {versions[1]['modified'].strftime('%Y-%m-%d %H:%M')}\n\n"
                            f"Size: {_file_size_str(versions[1]['path'])}\n\n"
                            f"Format: {versions[1]['format']}"
                        )

                    # Size difference
                    size_diff = versions[0]["size"] - versions[1]["size"]
                    if size_diff > 0:
                        st.caption(f"Size change: +{_file_size_str(Path('dummy'))} (latest is larger)")
                    elif size_diff < 0:
                        st.caption(f"Size change: latest is smaller by {abs(size_diff)} bytes")
                    else:
                        st.caption("Size change: identical file sizes")

                # Revert option
                if len(versions) >= 2:
                    st.markdown("##### Revert to Previous Version")
                    revert_target = st.selectbox(
                        "Select version to restore",
                        options=list(range(1, len(versions))),
                        format_func=lambda i: f"v{len(versions) - i}: {versions[i]['name']} ({versions[i]['modified'].strftime('%Y-%m-%d')})",
                        key=f"revert_select_{group['base_name']}",
                    )
                    if st.button(
                        f"Revert to {versions[revert_target]['name']}",
                        key=f"revert_btn_{group['base_name']}",
                    ):
                        try:
                            source = versions[revert_target]["path"]
                            dest = versions[0]["path"]
                            # Create a backup of current latest
                            backup_name = f"{dest.stem}_backup_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{dest.suffix}"
                            backup_path = dest.parent / backup_name
                            shutil.copy2(dest, backup_path)
                            # Copy revert source to latest location
                            shutil.copy2(source, dest)
                            st.success(
                                f"Reverted to {versions[revert_target]['name']}. "
                                f"Backup saved as {backup_name}."
                            )
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Revert failed: {exc}")


# ===========================================================================
# TAB 6: Usage Stats
# ===========================================================================
with tab_stats:
    st.subheader("Usage Statistics")
    st.caption("Content analytics, download trends, freshness, and storage metrics")

    # ----- Most Downloaded -----
    st.markdown("#### Most Downloaded Items")

    all_items_for_stats = fetch_library_items(sort_key="Most Downloads")
    top_downloaded = [i for i in all_items_for_stats if (i.get("download_count") or 0) > 0][:10]

    if top_downloaded:
        if PLOTLY_AVAILABLE:
            fig_dl = go.Figure(go.Bar(
                x=[i["title"][:30] for i in top_downloaded],
                y=[i["download_count"] for i in top_downloaded],
                marker_color="#0066cc",
            ))
            fig_dl.update_layout(
                title="Top 10 Most Downloaded",
                xaxis_title="Content Item",
                yaxis_title="Downloads",
                height=350,
                margin=dict(l=40, r=20, t=50, b=100),
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig_dl, use_container_width=True)
        else:
            for item in top_downloaded:
                st.write(f"- **{item['title']}**: {item['download_count']} downloads")
    else:
        st.info("No download data available yet.")

    st.markdown("---")

    # ----- Most Viewed / Accessed (approximated by download count + rating) -----
    st.markdown("#### Most Engaged Content")
    st.caption("Items with highest combined ratings and download activity")

    engaged_items = sorted(
        all_items_for_stats,
        key=lambda x: ((x.get("rating") or 0) * 10) + (x.get("download_count") or 0),
        reverse=True,
    )[:10]

    if engaged_items:
        if PANDAS_AVAILABLE:
            df_engaged = pd.DataFrame([
                {
                    "Title": i["title"][:40],
                    "Type": i["content_type"].title(),
                    "Rating": _stars_display(i.get("rating")),
                    "Downloads": i.get("download_count", 0),
                    "Score": ((i.get("rating") or 0) * 10) + (i.get("download_count") or 0),
                }
                for i in engaged_items
            ])
            st.dataframe(df_engaged, use_container_width=True, hide_index=True)
        else:
            for item in engaged_items:
                st.write(
                    f"- **{item['title']}**: {_stars_display(item.get('rating'))}, "
                    f"{item.get('download_count', 0)} downloads"
                )
    else:
        st.info("No engagement data available yet.")

    st.markdown("---")

    # ----- Content Freshness -----
    st.markdown("#### Content Freshness")
    st.caption("Distribution of content by age")

    all_gen = fetch_generated_content_all()
    if all_gen:
        now = datetime.utcnow()
        age_buckets = {
            "Last 7 days": 0,
            "Last 30 days": 0,
            "Last 90 days": 0,
            "Older than 90 days": 0,
        }
        for item in all_gen:
            gen_at = item.get("generated_at")
            if not gen_at:
                age_buckets["Older than 90 days"] += 1
                continue
            age = (now - gen_at).days
            if age <= 7:
                age_buckets["Last 7 days"] += 1
            elif age <= 30:
                age_buckets["Last 30 days"] += 1
            elif age <= 90:
                age_buckets["Last 90 days"] += 1
            else:
                age_buckets["Older than 90 days"] += 1

        if PLOTLY_AVAILABLE:
            colors = ["#28a745", "#17a2b8", "#ffc107", "#dc3545"]
            fig_fresh = go.Figure(go.Pie(
                labels=list(age_buckets.keys()),
                values=list(age_buckets.values()),
                marker_colors=colors,
                hole=0.4,
            ))
            fig_fresh.update_layout(
                title="Content Age Distribution",
                height=350,
                margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(fig_fresh, use_container_width=True)
        else:
            for bucket, count in age_buckets.items():
                st.write(f"- **{bucket}**: {count} items")

        # Content type distribution
        st.markdown("---")
        st.markdown("#### Content by Type")

        type_counts = Counter(i.get("content_type", "other") for i in all_gen)
        if PLOTLY_AVAILABLE:
            fig_type = go.Figure(go.Bar(
                x=[t.title() for t in type_counts.keys()],
                y=list(type_counts.values()),
                marker_color=["#0066cc", "#28a745", "#ffc107", "#dc3545", "#6f42c1",
                               "#17a2b8", "#fd7e14", "#20c997", "#e83e8c"][:len(type_counts)],
            ))
            fig_type.update_layout(
                title="Items by Content Type",
                xaxis_title="Type",
                yaxis_title="Count",
                height=350,
                margin=dict(l=40, r=20, t=50, b=60),
            )
            st.plotly_chart(fig_type, use_container_width=True)
        else:
            for t, c in type_counts.most_common():
                icon = CONTENT_TYPE_ICONS.get(t, "\U0001f4c1")
                st.write(f"- {icon} **{t.title()}**: {c} items")
    else:
        st.info("No content generated yet. Statistics will appear after content generation.")

    st.markdown("---")

    # ----- Storage Usage -----
    st.markdown("#### Storage Usage by Category")

    storage_data = {}
    total_storage = 0
    for category, directory in OUTPUT_DIRS.items():
        if not directory.exists():
            storage_data[category] = 0
            continue
        cat_size = sum(f.stat().st_size for f in directory.rglob("*") if f.is_file())
        storage_data[category] = cat_size
        total_storage += cat_size

    if total_storage > 0:
        st1, st2 = st.columns([2, 1])

        with st1:
            if PLOTLY_AVAILABLE:
                fig_storage = go.Figure(go.Bar(
                    x=[c.title() for c in storage_data.keys()],
                    y=[s / (1024 * 1024) for s in storage_data.values()],
                    marker_color="#0066cc",
                    text=[f"{s / (1024 * 1024):.1f} MB" for s in storage_data.values()],
                    textposition="auto",
                ))
                fig_storage.update_layout(
                    title="Storage by Category",
                    xaxis_title="Category",
                    yaxis_title="Size (MB)",
                    height=350,
                    margin=dict(l=40, r=20, t=50, b=60),
                )
                st.plotly_chart(fig_storage, use_container_width=True)
            else:
                for cat, size in storage_data.items():
                    if size > 0:
                        st.write(f"- **{cat.title()}**: {size / (1024 * 1024):.2f} MB")

        with st2:
            st.markdown(
                f'<div class="stat-card">'
                f'<h3>Total Storage</h3>'
                f'<h2 style="color:#0066cc;">{total_storage / (1024 * 1024):.1f} MB</h2>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown("")

            for cat, size in sorted(storage_data.items(), key=lambda x: x[1], reverse=True):
                if size > 0:
                    pct = (size / total_storage) * 100 if total_storage > 0 else 0
                    icon = CONTENT_TYPE_ICONS.get(cat, "\U0001f4c1")
                    st.markdown(f"{icon} **{cat.title()}**: {size / (1024 * 1024):.1f} MB ({pct:.0f}%)")
    else:
        st.info("No files stored yet. Output directories are empty.")

    st.markdown("---")

    # ----- Generation Timeline -----
    st.markdown("#### Generation Timeline")
    st.caption("Content generation activity over time")

    if all_gen:
        date_counts: dict[str, int] = {}
        for item in all_gen:
            gen_at = item.get("generated_at")
            if gen_at:
                day_key = gen_at.strftime("%Y-%m-%d")
                date_counts[day_key] = date_counts.get(day_key, 0) + 1

        if date_counts and PLOTLY_AVAILABLE:
            sorted_dates = sorted(date_counts.keys())
            fig_timeline = go.Figure(go.Scatter(
                x=sorted_dates,
                y=[date_counts[d] for d in sorted_dates],
                mode="lines+markers",
                line=dict(color="#0066cc", width=2),
                marker=dict(size=6),
                fill="tozeroy",
                fillcolor="rgba(0, 102, 204, 0.1)",
            ))
            fig_timeline.update_layout(
                title="Daily Generation Activity",
                xaxis_title="Date",
                yaxis_title="Items Generated",
                height=300,
                margin=dict(l=40, r=20, t=50, b=40),
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
        elif date_counts:
            for d in sorted(date_counts.keys(), reverse=True)[:20]:
                st.write(f"- **{d}**: {date_counts[d]} items")
    else:
        st.info("No generation data available for timeline.")


# ===========================================================================
# Footer
# ===========================================================================
st.markdown("---")
st.caption(
    "Content Library -- Brand Intelligence Content Hub | "
    "Browse, search, approve, and manage all your generated content in one place."
)
