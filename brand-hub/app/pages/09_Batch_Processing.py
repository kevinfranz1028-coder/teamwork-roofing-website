"""
Brand Intelligence Content Hub - Batch Processing

Bulk content-generation page that lets users queue multiple items,
process them sequentially with live progress, download results as
individual files or ZIP archives, and review historical batch analytics.
"""

import csv
import io
import json
import logging
import os
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

# ---------------------------------------------------------------------------
# Application imports
# ---------------------------------------------------------------------------

from app.config import (
    BASE_DIR,
    OUTPUT_DIR,
    PRESENTATIONS_DIR,
    DOCUMENTS_DIR,
    TRAINING_DIR,
    VISUALS_DIR,
    EXPORTS_DIR,
)
from app.database.models import (
    get_session,
    init_db,
    GeneratedContent,
    ContentLibraryItem,
    BatchJob,
)

# ---------------------------------------------------------------------------
# Generator imports (graceful degradation)
# ---------------------------------------------------------------------------

try:
    from app.generators.presentation_gen import BrandedPresentationGenerator
    PRESENTATION_GEN_AVAILABLE = True
except ImportError:
    PRESENTATION_GEN_AVAILABLE = False

try:
    from app.generators.document_gen import BrandedDocumentGenerator
    DOCUMENT_GEN_AVAILABLE = True
except ImportError:
    DOCUMENT_GEN_AVAILABLE = False

try:
    from app.generators.visual_gen import VisualPipeline
    VISUAL_GEN_AVAILABLE = True
except ImportError:
    VISUAL_GEN_AVAILABLE = False

try:
    from app.generators.quiz_gen import QuizGenerator
    QUIZ_GEN_AVAILABLE = True
except ImportError:
    QUIZ_GEN_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Batch Processing", page_icon="\u26a1", layout="wide")

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown(
    """<style>
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
.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: 600;
}
.status-pending {
    background: #fff3cd;
    color: #856404;
}
.status-running {
    background: #cce5ff;
    color: #004085;
}
.status-completed {
    background: #d4edda;
    color: #155724;
}
.status-failed {
    background: #f8d7da;
    color: #721c24;
}
.status-cancelled {
    background: #e2e3e5;
    color: #383d41;
}
.batch-stat {
    text-align: center;
    padding: 1rem;
}
.batch-stat .number {
    font-size: 2rem;
    font-weight: 700;
    color: #0066cc;
}
.batch-stat .label {
    font-size: 0.85rem;
    color: #666;
    margin-top: 0.25rem;
}
.item-row {
    border-left: 3px solid #0066cc;
    padding: 0.5rem 1rem;
    margin: 0.5rem 0;
    background: #f8f9fa;
    border-radius: 0 6px 6px 0;
}
.item-row.success { border-left-color: #28a745; }
.item-row.failed { border-left-color: #dc3545; }
</style>""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Initialise database
# ---------------------------------------------------------------------------

try:
    init_db()
except Exception as exc:
    logger.warning("Database initialisation error: %s", exc)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONTENT_TYPES = {
    "presentation": {
        "label": "Presentation",
        "icon": "\U0001f4ca",
        "formats": ["pptx"],
        "generator_available": PRESENTATION_GEN_AVAILABLE,
        "output_dir": PRESENTATIONS_DIR,
    },
    "document": {
        "label": "Document",
        "icon": "\U0001f4c4",
        "formats": ["docx"],
        "generator_available": DOCUMENT_GEN_AVAILABLE,
        "output_dir": DOCUMENTS_DIR,
    },
    "job_aid": {
        "label": "Job Aid",
        "icon": "\U0001f4cb",
        "formats": ["docx"],
        "generator_available": DOCUMENT_GEN_AVAILABLE,
        "output_dir": DOCUMENTS_DIR,
    },
    "case_study": {
        "label": "Case Study",
        "icon": "\U0001f4d6",
        "formats": ["docx"],
        "generator_available": DOCUMENT_GEN_AVAILABLE,
        "output_dir": DOCUMENTS_DIR,
    },
    "visual": {
        "label": "Visual / Infographic",
        "icon": "\U0001f3a8",
        "formats": ["png", "svg", "pdf"],
        "generator_available": VISUAL_GEN_AVAILABLE,
        "output_dir": VISUALS_DIR,
    },
    "quiz": {
        "label": "Quiz / Assessment",
        "icon": "\u2753",
        "formats": ["docx", "pptx", "json"],
        "generator_available": QUIZ_GEN_AVAILABLE,
        "output_dir": TRAINING_DIR,
    },
}

TONE_OPTIONS = [
    "Professional",
    "Conversational",
    "Formal",
    "Friendly",
    "Authoritative",
    "Inspirational",
]

AUDIENCE_OPTIONS = [
    "General",
    "Executive / C-Suite",
    "Sales Team",
    "Technical Staff",
    "New Hires / Onboarding",
    "Customers / Prospects",
    "Partners / Vendors",
]

# ---------------------------------------------------------------------------
# Session-state defaults
# ---------------------------------------------------------------------------

_STATE_DEFAULTS = {
    "batch_processing_active": False,
    "batch_cancel_requested": False,
    "current_batch_id": None,
    "batch_items_manual": "",
    "batch_job_name": "",
    "csv_column_mapping": {},
    "batch_results_cache": {},
}

for _key, _val in _STATE_DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _val

# ---------------------------------------------------------------------------
# Helper: status badge HTML
# ---------------------------------------------------------------------------


def _status_badge(status: str) -> str:
    """Return an HTML span styled as a colour-coded status badge."""
    css_class = f"status-{status}" if status in (
        "pending", "running", "completed", "failed", "cancelled",
    ) else "status-pending"
    return f'<span class="status-badge {css_class}">{status.title()}</span>'


# ---------------------------------------------------------------------------
# Helper: safe JSON parse
# ---------------------------------------------------------------------------


def _safe_json_loads(raw: str | None, default=None):
    """Parse a JSON string, returning *default* on failure."""
    if not raw:
        return default if default is not None else []
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


# ---------------------------------------------------------------------------
# Helper: file size formatter
# ---------------------------------------------------------------------------


def _format_file_size(path_str: str) -> str:
    """Return a human-readable file size, or '--' if not available."""
    try:
        size = Path(path_str).stat().st_size
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"
    except (OSError, TypeError):
        return "--"


# ---------------------------------------------------------------------------
# Helper: load all batch jobs from DB
# ---------------------------------------------------------------------------


def _load_batch_jobs(status_filter: str | None = None) -> list:
    """Return BatchJob rows, optionally filtered by status."""
    try:
        session = get_session()
        query = session.query(BatchJob)
        if status_filter:
            query = query.filter(BatchJob.status == status_filter)
        jobs = query.order_by(BatchJob.created_at.desc()).all()
        session.close()
        return jobs
    except Exception as exc:
        logger.error("Failed to load batch jobs: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Helper: load single batch job
# ---------------------------------------------------------------------------


def _load_batch_job(job_id: int) -> BatchJob | None:
    """Return a single BatchJob by primary key."""
    try:
        session = get_session()
        job = session.query(BatchJob).get(job_id)
        session.close()
        return job
    except Exception as exc:
        logger.error("Failed to load batch job %s: %s", job_id, exc)
        return None


# ---------------------------------------------------------------------------
# Helper: update batch job in DB
# ---------------------------------------------------------------------------


def _update_batch_job(job_id: int, **kwargs) -> bool:
    """Update arbitrary columns on a BatchJob row. Returns True on success."""
    try:
        session = get_session()
        job = session.query(BatchJob).get(job_id)
        if not job:
            session.close()
            return False
        for key, value in kwargs.items():
            setattr(job, key, value)
        session.commit()
        session.close()
        return True
    except Exception as exc:
        logger.error("Failed to update batch job %s: %s", job_id, exc)
        return False


# ---------------------------------------------------------------------------
# Helper: parse manual entry text
# ---------------------------------------------------------------------------


def _parse_manual_items(text: str) -> list[dict]:
    """Parse line-separated items in ``title|topic`` format.

    Each line may contain one or two pipe-delimited fields:
        ``My Title | Some topic text``

    Returns a list of item dicts.
    """
    items = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        title = parts[0] if parts else "Untitled"
        topic = parts[1] if len(parts) > 1 else title
        items.append({
            "title": title,
            "topic": topic,
            "audience": "",
            "tone": "",
            "template": "",
        })
    return items


# ---------------------------------------------------------------------------
# Helper: parse CSV / Excel upload
# ---------------------------------------------------------------------------


def _parse_uploaded_file(uploaded_file) -> "pd.DataFrame | None":
    """Read an uploaded CSV or Excel file into a pandas DataFrame."""
    try:
        import pandas as pd
    except ImportError:
        st.error("pandas is required for CSV/Excel uploads. Install it with: pip install pandas")
        return None

    try:
        name = uploaded_file.name.lower()
        if name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        elif name.endswith((".xlsx", ".xls")):
            return pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload a CSV or Excel file.")
            return None
    except Exception as exc:
        st.error(f"Error reading file: {exc}")
        return None


# ---------------------------------------------------------------------------
# Generator dispatch
# ---------------------------------------------------------------------------


def _run_generator(
    content_type: str,
    item: dict,
    output_format: str,
    brand_config_opts: dict,
) -> dict:
    """Dispatch a single item to the appropriate generator.

    Returns a result dict with keys: ``status``, ``output_path``, ``error``,
    ``duration``.
    """
    start = time.time()
    title = item.get("title", "Untitled")
    topic = item.get("topic", title)
    audience = item.get("audience", "General")
    tone = item.get("tone", "Professional")

    try:
        # ----- Presentation -----
        if content_type == "presentation":
            if not PRESENTATION_GEN_AVAILABLE:
                raise ImportError("Presentation generator not available")
            gen = BrandedPresentationGenerator()
            slides_data = [
                {"layout": "title", "title": title, "subtitle": topic},
                {"layout": "content", "title": "Overview", "bullets": [
                    f"Audience: {audience}",
                    f"Tone: {tone}",
                    topic,
                ]},
                {"layout": "closing", "title": "Thank You", "subtitle": title},
            ]
            output_path = gen.generate(
                slides_data=slides_data,
                title=title,
            )
            return {
                "status": "success",
                "output_path": output_path,
                "error": "",
                "duration": round(time.time() - start, 2),
            }

        # ----- Document / Job Aid / Case Study -----
        elif content_type in ("document", "job_aid", "case_study"):
            if not DOCUMENT_GEN_AVAILABLE:
                raise ImportError("Document generator not available")
            gen = BrandedDocumentGenerator()
            doc_type = content_type
            content_body = {
                "title": title,
                "topic": topic,
                "audience": audience,
                "tone": tone,
                "sections": [
                    {"heading": "Introduction", "body": topic},
                    {"heading": "Details", "body": f"Content about {topic} for {audience}."},
                ],
            }
            output_path = gen.generate(
                content=content_body,
                doc_type=doc_type,
                title=title,
            )
            return {
                "status": "success",
                "output_path": output_path,
                "error": "",
                "duration": round(time.time() - start, 2),
            }

        # ----- Visual -----
        elif content_type == "visual":
            if not VISUAL_GEN_AVAILABLE:
                raise ImportError("Visual generator not available")
            pipeline = VisualPipeline()
            result = pipeline.generate_visual(
                description=f"{title}: {topic}",
                visual_type="flowchart",
                output_format=output_format or "png",
            )
            output_path = result.get("file_path", "")
            if not result.get("success", False):
                raise RuntimeError(result.get("error", "Visual generation failed"))
            return {
                "status": "success",
                "output_path": output_path,
                "error": "",
                "duration": round(time.time() - start, 2),
            }

        # ----- Quiz -----
        elif content_type == "quiz":
            if not QUIZ_GEN_AVAILABLE:
                raise ImportError("Quiz generator not available")
            gen = QuizGenerator()
            curriculum_content = {
                "title": title,
                "description": topic,
                "modules": [
                    {"title": title, "content": topic, "objectives": [topic]},
                ],
            }
            result = gen.generate(
                curriculum_content=curriculum_content,
                question_count=10,
                title=title,
                output_format=output_format or "docx",
            )
            output_path = result.get("quiz_path", "")
            if result.get("error"):
                raise RuntimeError(result["error"])
            return {
                "status": "success",
                "output_path": output_path,
                "error": "",
                "duration": round(time.time() - start, 2),
            }

        else:
            raise ValueError(f"Unsupported content type: {content_type}")

    except Exception as exc:
        logger.error("Generator error for '%s' [%s]: %s", title, content_type, exc)
        return {
            "status": "failed",
            "output_path": "",
            "error": str(exc),
            "duration": round(time.time() - start, 2),
        }


# ---------------------------------------------------------------------------
# Helper: record generated content in DB
# ---------------------------------------------------------------------------


def _record_generated_content(
    title: str,
    content_type: str,
    output_path: str,
    duration: float,
) -> int | None:
    """Insert a GeneratedContent row and return its id."""
    try:
        session = get_session()
        record = GeneratedContent(
            title=title,
            content_type=content_type,
            output_path=output_path,
            format=Path(output_path).suffix.lstrip(".") if output_path else "",
            generated_at=datetime.utcnow(),
            generation_time_seconds=duration,
        )
        session.add(record)
        session.commit()
        record_id = record.id
        session.close()
        return record_id
    except Exception as exc:
        logger.error("Failed to record generated content: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Helper: add item to content library
# ---------------------------------------------------------------------------


def _add_to_library(
    title: str,
    content_type: str,
    generated_content_id: int | None = None,
    tags: str = "",
) -> bool:
    """Create a ContentLibraryItem row. Returns True on success."""
    try:
        session = get_session()
        item = ContentLibraryItem(
            generated_content_id=generated_content_id,
            title=title,
            description=f"Batch-generated {content_type}",
            tags=tags or content_type,
            category=content_type,
            is_approved=False,
        )
        session.add(item)
        session.commit()
        session.close()
        return True
    except Exception as exc:
        logger.error("Failed to add library item: %s", exc)
        return False


# ╔═════════════════════════════════════════════════════════════════════════╗
# ║  PAGE HEADER                                                          ║
# ╚═════════════════════════════════════════════════════════════════════════╝

st.title("\u26a1 Batch Processing")
st.markdown(
    "Queue and execute bulk content-generation jobs, process CSV/Excel inputs, "
    "and monitor progress in real time."
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Quick stats row
# ---------------------------------------------------------------------------

all_jobs = _load_batch_jobs()
total_jobs = len(all_jobs)
pending_count = sum(1 for j in all_jobs if j.status == "pending")
running_count = sum(1 for j in all_jobs if j.status == "running")
completed_count = sum(1 for j in all_jobs if j.status == "completed")

s1, s2, s3, s4 = st.columns(4)
with s1:
    st.markdown(
        '<div class="brand-card"><div class="batch-stat">'
        f'<div class="number">{total_jobs}</div>'
        '<div class="label">Total Jobs</div>'
        "</div></div>",
        unsafe_allow_html=True,
    )
with s2:
    st.markdown(
        '<div class="brand-card"><div class="batch-stat">'
        f'<div class="number">{pending_count}</div>'
        '<div class="label">Pending</div>'
        "</div></div>",
        unsafe_allow_html=True,
    )
with s3:
    st.markdown(
        '<div class="brand-card"><div class="batch-stat">'
        f'<div class="number">{running_count}</div>'
        '<div class="label">Running</div>'
        "</div></div>",
        unsafe_allow_html=True,
    )
with s4:
    st.markdown(
        '<div class="brand-card"><div class="batch-stat">'
        f'<div class="number">{completed_count}</div>'
        '<div class="label">Completed</div>'
        "</div></div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ╔═════════════════════════════════════════════════════════════════════════╗
# ║  TABS                                                                 ║
# ╚═════════════════════════════════════════════════════════════════════════╝

tab_create, tab_process, tab_results, tab_history = st.tabs([
    "\U0001f4dd Create Batch Job",
    "\u2699\ufe0f Process Queue",
    "\U0001f4e5 Results & Download",
    "\U0001f4ca History & Analytics",
])

# ╔═════════════════════════════════════════════════════════════════════════╗
# ║  TAB 1 - CREATE BATCH JOB                                            ║
# ╚═════════════════════════════════════════════════════════════════════════╝

with tab_create:
    st.header("Create a New Batch Job")
    st.markdown(
        "Define a batch of content items to be generated in bulk. "
        "You can enter items manually or upload a CSV/Excel file."
    )

    st.markdown("---")

    # ---- Job metadata ----
    col_name, col_type = st.columns([2, 1])
    with col_name:
        job_name = st.text_input(
            "Job Name",
            value=st.session_state.get("batch_job_name", ""),
            placeholder="e.g. Q1 Sales Enablement Batch",
            help="A descriptive name for this batch job.",
            key="create_job_name",
        )
    with col_type:
        content_type_key = st.selectbox(
            "Content Type",
            options=list(CONTENT_TYPES.keys()),
            format_func=lambda k: f"{CONTENT_TYPES[k]['icon']}  {CONTENT_TYPES[k]['label']}",
            key="create_content_type",
        )

    ct_info = CONTENT_TYPES[content_type_key]

    # Show availability warning
    if not ct_info["generator_available"]:
        st.warning(
            f"The {ct_info['label']} generator is not currently installed. "
            "Items of this type will be marked as failed during processing."
        )

    st.markdown("---")

    # ---- Input method ----
    input_method = st.radio(
        "Input Method",
        options=["Manual Entry", "CSV Upload"],
        horizontal=True,
        key="create_input_method",
    )

    batch_items: list[dict] = []

    # ---- Manual entry ----
    if input_method == "Manual Entry":
        st.markdown(
            '<div class="brand-card">'
            "<h3>\U0001f4dd Manual Entry</h3>"
            "<p>Enter one item per line using <code>title | topic</code> format. "
            "If only one value is given, it is used as both title and topic.</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        manual_text = st.text_area(
            "Batch Items (one per line)",
            value=st.session_state.get("batch_items_manual", ""),
            height=200,
            placeholder=(
                "Sales Onboarding Deck | New hire sales training overview\n"
                "Product Feature Guide | Comprehensive feature walkthrough\n"
                "Q1 Performance Report | Quarterly performance metrics"
            ),
            key="create_manual_text",
        )

        if manual_text.strip():
            batch_items = _parse_manual_items(manual_text)

        if batch_items:
            st.markdown(f"**{len(batch_items)}** item(s) parsed:")
            preview_data = []
            for idx, itm in enumerate(batch_items, 1):
                preview_data.append({
                    "#": idx,
                    "Title": itm["title"],
                    "Topic": itm["topic"],
                })
            st.dataframe(preview_data, use_container_width=True, hide_index=True)

    # ---- CSV / Excel upload ----
    else:
        st.markdown(
            '<div class="brand-card">'
            "<h3>\U0001f4c1 CSV / Excel Upload</h3>"
            "<p>Upload a CSV or Excel file containing your batch items. "
            "You will map columns to the required fields below.</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader(
            "Upload CSV or Excel",
            type=["csv", "xlsx", "xls"],
            key="create_file_upload",
        )

        if uploaded_file is not None:
            df = _parse_uploaded_file(uploaded_file)

            if df is not None and not df.empty:
                st.success(f"Loaded {len(df)} rows and {len(df.columns)} columns.")

                with st.expander("Preview uploaded data", expanded=True):
                    st.dataframe(df.head(20), use_container_width=True)

                st.subheader("Column Mapping")
                st.markdown(
                    "Map columns from your file to the batch item fields. "
                    "**Title** is required; other fields are optional."
                )

                available_cols = ["-- not mapped --"] + list(df.columns)

                mc1, mc2, mc3 = st.columns(3)
                with mc1:
                    title_col = st.selectbox(
                        "Title column *",
                        options=available_cols,
                        index=0,
                        key="map_title",
                    )
                    topic_col = st.selectbox(
                        "Topic column",
                        options=available_cols,
                        index=0,
                        key="map_topic",
                    )
                with mc2:
                    audience_col = st.selectbox(
                        "Audience column",
                        options=available_cols,
                        index=0,
                        key="map_audience",
                    )
                    tone_col = st.selectbox(
                        "Tone column",
                        options=available_cols,
                        index=0,
                        key="map_tone",
                    )
                with mc3:
                    template_col = st.selectbox(
                        "Template column",
                        options=available_cols,
                        index=0,
                        key="map_template",
                    )

                if title_col != "-- not mapped --":
                    for _, row in df.iterrows():
                        item = {
                            "title": str(row.get(title_col, "Untitled")),
                            "topic": (
                                str(row.get(topic_col, ""))
                                if topic_col != "-- not mapped --"
                                else str(row.get(title_col, ""))
                            ),
                            "audience": (
                                str(row.get(audience_col, ""))
                                if audience_col != "-- not mapped --"
                                else ""
                            ),
                            "tone": (
                                str(row.get(tone_col, ""))
                                if tone_col != "-- not mapped --"
                                else ""
                            ),
                            "template": (
                                str(row.get(template_col, ""))
                                if template_col != "-- not mapped --"
                                else ""
                            ),
                        }
                        batch_items.append(item)

                    st.markdown(f"**{len(batch_items)}** item(s) mapped:")
                    mapped_preview = []
                    for idx, itm in enumerate(batch_items[:20], 1):
                        mapped_preview.append({
                            "#": idx,
                            "Title": itm["title"],
                            "Topic": itm["topic"][:60] + ("..." if len(itm["topic"]) > 60 else ""),
                            "Audience": itm["audience"] or "--",
                            "Tone": itm["tone"] or "--",
                        })
                    st.dataframe(mapped_preview, use_container_width=True, hide_index=True)
                    if len(batch_items) > 20:
                        st.caption(f"Showing first 20 of {len(batch_items)} items.")
                else:
                    st.info("Please map at least the **Title** column to continue.")

    st.markdown("---")

    # ---- Output format & brand options ----
    st.subheader("Output & Brand Settings")

    opt1, opt2 = st.columns(2)
    with opt1:
        output_format = st.selectbox(
            "Output Format",
            options=ct_info["formats"],
            key="create_output_format",
        )
    with opt2:
        default_audience = st.selectbox(
            "Default Audience",
            options=AUDIENCE_OPTIONS,
            key="create_default_audience",
            help="Applied to items that have no audience specified.",
        )

    opt3, opt4 = st.columns(2)
    with opt3:
        default_tone = st.selectbox(
            "Default Tone",
            options=TONE_OPTIONS,
            key="create_default_tone",
            help="Applied to items that have no tone specified.",
        )
    with opt4:
        voice_style = st.selectbox(
            "Brand Voice Style",
            options=["Default", "Formal", "Casual", "Technical", "Marketing"],
            key="create_voice_style",
        )

    st.markdown("**Brand Config Options**")
    bc1, bc2, bc3 = st.columns(3)
    with bc1:
        use_brand_colors = st.checkbox("Use brand colours", value=True, key="create_brand_colors")
    with bc2:
        include_logo = st.checkbox("Include logo", value=True, key="create_include_logo")
    with bc3:
        st.markdown(f"Voice: **{voice_style}**")

    st.markdown("---")

    # ---- Queue button ----
    queue_disabled = not job_name.strip() or len(batch_items) == 0
    if queue_disabled:
        if not job_name.strip():
            st.info("Enter a **Job Name** to continue.")
        if len(batch_items) == 0:
            st.info("Add at least one item via **Manual Entry** or **CSV Upload**.")

    if st.button(
        f"\u26a1 Queue Batch Job ({len(batch_items)} items)",
        type="primary",
        use_container_width=True,
        disabled=queue_disabled,
        key="btn_queue_batch",
    ):
        # Apply defaults to items missing audience/tone
        for itm in batch_items:
            if not itm.get("audience"):
                itm["audience"] = default_audience
            if not itm.get("tone"):
                itm["tone"] = default_tone

        # Build metadata dict stored alongside items
        job_meta = {
            "content_type": content_type_key,
            "output_format": output_format,
            "brand_config": {
                "use_brand_colors": use_brand_colors,
                "include_logo": include_logo,
                "voice_style": voice_style,
            },
        }

        items_payload = {
            "meta": job_meta,
            "items": batch_items,
        }

        try:
            session = get_session()
            new_job = BatchJob(
                name=job_name.strip(),
                status="pending",
                items_json=json.dumps(items_payload, ensure_ascii=False),
                created_at=datetime.utcnow(),
            )
            session.add(new_job)
            session.commit()
            new_job_id = new_job.id
            session.close()

            st.success(
                f"Batch job **{job_name}** created with {len(batch_items)} items "
                f"(Job #{new_job_id}). Switch to the **Process Queue** tab to start processing."
            )
            st.balloons()

        except Exception as exc:
            st.error(f"Failed to save batch job: {exc}")
            logger.error("BatchJob save error: %s", exc)


# ╔═════════════════════════════════════════════════════════════════════════╗
# ║  TAB 2 - PROCESS QUEUE                                               ║
# ╚═════════════════════════════════════════════════════════════════════════╝

with tab_process:
    st.header("Process Queue")
    st.markdown("View queued batch jobs and start processing them.")

    st.markdown("---")

    # Refresh job list
    queue_jobs = _load_batch_jobs()

    if not queue_jobs:
        st.info(
            "No batch jobs found. Create a new batch job in the "
            "**Create Batch Job** tab to get started."
        )
    else:
        for job in queue_jobs:
            items_data = _safe_json_loads(job.items_json, default={})
            meta = items_data.get("meta", {}) if isinstance(items_data, dict) else {}
            items = items_data.get("items", []) if isinstance(items_data, dict) else []
            ct_key = meta.get("content_type", "document")
            ct_label = CONTENT_TYPES.get(ct_key, {}).get("label", ct_key.title())
            ct_icon = CONTENT_TYPES.get(ct_key, {}).get("icon", "\U0001f4c4")

            results = _safe_json_loads(job.results_json, default=[])
            success_count = sum(1 for r in results if r.get("status") == "success")
            failed_count = sum(1 for r in results if r.get("status") == "failed")

            with st.expander(
                f"{ct_icon}  {job.name}  |  {len(items)} items  |  {job.status.title()}",
                expanded=(job.status in ("pending", "running")),
            ):
                # Job info row
                ic1, ic2, ic3, ic4 = st.columns([2, 1, 1, 1])
                with ic1:
                    st.markdown(f"**Job #{job.id}** - {job.name}")
                    created = job.created_at.strftime("%Y-%m-%d %H:%M") if job.created_at else "--"
                    st.caption(f"Created: {created}")
                with ic2:
                    st.markdown(f"Type: **{ct_label}**")
                with ic3:
                    st.markdown(f"Items: **{len(items)}**")
                with ic4:
                    st.markdown(_status_badge(job.status), unsafe_allow_html=True)

                # If there are partial results, show them
                if results:
                    st.markdown(
                        f"Progress: **{success_count}** succeeded, "
                        f"**{failed_count}** failed, "
                        f"**{len(items) - success_count - failed_count}** remaining"
                    )

                st.markdown("---")

                # ---- Action buttons based on status ----

                # PENDING: Start button
                if job.status == "pending":
                    if st.button(
                        f"\u25b6\ufe0f  Start Processing",
                        key=f"start_{job.id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        st.session_state["batch_processing_active"] = True
                        st.session_state["batch_cancel_requested"] = False
                        st.session_state["current_batch_id"] = job.id

                        # Mark job as running
                        _update_batch_job(job.id, status="running")

                        output_fmt = meta.get("output_format", "docx")
                        brand_cfg = meta.get("brand_config", {})
                        all_results: list[dict] = []

                        # Progress UI
                        progress_bar = st.progress(0, text="Starting batch processing...")
                        status_container = st.status(
                            f"Processing {len(items)} items...",
                            expanded=True,
                        )

                        cancel_col, _ = st.columns([1, 3])
                        with cancel_col:
                            if st.button(
                                "\u274c Cancel",
                                key=f"cancel_{job.id}",
                                type="secondary",
                            ):
                                st.session_state["batch_cancel_requested"] = True

                        with status_container:
                            for idx, item in enumerate(items):
                                # Check for cancellation
                                if st.session_state.get("batch_cancel_requested", False):
                                    st.warning(f"Cancelled at item {idx + 1}/{len(items)}")
                                    _update_batch_job(
                                        job.id,
                                        status="cancelled",
                                        results_json=json.dumps(all_results),
                                    )
                                    break

                                item_title = item.get("title", f"Item {idx + 1}")
                                progress_pct = (idx + 1) / len(items)
                                progress_bar.progress(
                                    progress_pct,
                                    text=f"Processing {idx + 1}/{len(items)}: {item_title}",
                                )

                                st.write(f"\u2699\ufe0f  Generating: **{item_title}**")

                                result = _run_generator(
                                    content_type=ct_key,
                                    item=item,
                                    output_format=output_fmt,
                                    brand_config_opts=brand_cfg,
                                )
                                result["title"] = item_title

                                all_results.append(result)

                                if result["status"] == "success":
                                    st.write(
                                        f"  \u2705 Success ({result['duration']}s) - "
                                        f"{result['output_path']}"
                                    )
                                    # Record to DB
                                    _record_generated_content(
                                        title=item_title,
                                        content_type=ct_key,
                                        output_path=result["output_path"],
                                        duration=result["duration"],
                                    )
                                else:
                                    st.write(
                                        f"  \u274c Failed ({result['duration']}s) - "
                                        f"{result.get('error', 'Unknown error')}"
                                    )

                                # Auto-save progress after each item
                                _update_batch_job(
                                    job.id,
                                    results_json=json.dumps(all_results),
                                )

                            # Final status update
                            if not st.session_state.get("batch_cancel_requested", False):
                                final_success = sum(
                                    1 for r in all_results if r["status"] == "success"
                                )
                                final_failed = sum(
                                    1 for r in all_results if r["status"] == "failed"
                                )
                                final_status = (
                                    "completed" if final_failed == 0 else
                                    "failed" if final_success == 0 else
                                    "completed"
                                )

                                _update_batch_job(
                                    job.id,
                                    status=final_status,
                                    results_json=json.dumps(all_results),
                                    completed_at=datetime.utcnow(),
                                )

                                progress_bar.progress(1.0, text="Batch processing complete!")

                                st.write("---")
                                st.write(
                                    f"\U0001f3c1  **Batch complete**: "
                                    f"{final_success} succeeded, {final_failed} failed "
                                    f"out of {len(items)} items."
                                )

                        st.session_state["batch_processing_active"] = False
                        st.session_state["current_batch_id"] = None

                # RUNNING: Show cancel option
                elif job.status == "running":
                    st.info("This job is currently being processed.")
                    if st.button(
                        "\u274c  Force Cancel",
                        key=f"force_cancel_{job.id}",
                        type="secondary",
                    ):
                        _update_batch_job(job.id, status="cancelled")
                        st.success("Job marked as cancelled.")
                        st.rerun()

                # COMPLETED: Summary
                elif job.status == "completed":
                    st.success(
                        f"Completed: {success_count}/{len(items)} items succeeded. "
                        "View results in the **Results & Download** tab."
                    )

                # FAILED: Summary with retry
                elif job.status == "failed":
                    st.error(
                        f"Failed: {failed_count}/{len(items)} items failed."
                    )
                    if st.button(
                        "\U0001f504  Reset to Pending",
                        key=f"reset_{job.id}",
                    ):
                        _update_batch_job(
                            job.id,
                            status="pending",
                            results_json=None,
                            completed_at=None,
                        )
                        st.success("Job reset to pending.")
                        st.rerun()

                # CANCELLED
                elif job.status == "cancelled":
                    st.warning("This job was cancelled.")
                    if st.button(
                        "\U0001f504  Reset to Pending",
                        key=f"reset_cancelled_{job.id}",
                    ):
                        _update_batch_job(
                            job.id,
                            status="pending",
                            results_json=None,
                            completed_at=None,
                        )
                        st.success("Job reset to pending.")
                        st.rerun()


# ╔═════════════════════════════════════════════════════════════════════════╗
# ║  TAB 3 - RESULTS & DOWNLOAD                                          ║
# ╚═════════════════════════════════════════════════════════════════════════╝

with tab_results:
    st.header("Results & Download")
    st.markdown("Review results from completed batch jobs and download generated files.")

    st.markdown("---")

    # Load jobs with results
    finished_jobs = [
        j for j in _load_batch_jobs()
        if j.status in ("completed", "failed", "cancelled")
        and j.results_json
    ]

    if not finished_jobs:
        st.info(
            "No completed batch jobs with results found. "
            "Process a batch job first in the **Process Queue** tab."
        )
    else:
        # Job selector
        job_options = {
            j.id: (
                f"#{j.id} - {j.name} ({j.status.title()}) "
                f"- {j.completed_at.strftime('%Y-%m-%d %H:%M') if j.completed_at else 'In progress'}"
            )
            for j in finished_jobs
        }

        selected_job_id = st.selectbox(
            "Select Batch Job",
            options=list(job_options.keys()),
            format_func=lambda jid: job_options[jid],
            key="results_job_select",
        )

        selected_job = _load_batch_job(selected_job_id)

        if selected_job:
            items_data = _safe_json_loads(selected_job.items_json, default={})
            meta = items_data.get("meta", {}) if isinstance(items_data, dict) else {}
            items = items_data.get("items", []) if isinstance(items_data, dict) else []
            results = _safe_json_loads(selected_job.results_json, default=[])

            ct_key = meta.get("content_type", "document")
            ct_label = CONTENT_TYPES.get(ct_key, {}).get("label", ct_key.title())

            # Summary stats
            total_items = len(results)
            success_items = [r for r in results if r.get("status") == "success"]
            failed_items = [r for r in results if r.get("status") == "failed"]
            total_duration = sum(r.get("duration", 0) for r in results)

            st.markdown(
                '<div class="brand-card">'
                f"<h3>{selected_job.name}</h3>"
                f"<p>Type: {ct_label} | "
                f"Total: {total_items} | "
                f"Succeeded: {len(success_items)} | "
                f"Failed: {len(failed_items)} | "
                f"Duration: {total_duration:.1f}s</p>"
                "</div>",
                unsafe_allow_html=True,
            )

            st.markdown("---")

            # Results table
            st.subheader("Item Results")

            for idx, result in enumerate(results):
                title = result.get("title", f"Item {idx + 1}")
                status = result.get("status", "unknown")
                output_path = result.get("output_path", "")
                error = result.get("error", "")
                duration = result.get("duration", 0)
                file_size = _format_file_size(output_path) if output_path else "--"

                css_class = "success" if status == "success" else "failed"

                st.markdown(
                    f'<div class="item-row {css_class}">'
                    f"<strong>{title}</strong> "
                    f'{_status_badge(status)} '
                    f"<span style='color:#888; font-size:0.85rem;'>"
                    f"  {duration}s | {file_size}"
                    f"</span>"
                    "</div>",
                    unsafe_allow_html=True,
                )

                if status == "success" and output_path:
                    r_col1, r_col2 = st.columns([3, 1])
                    with r_col1:
                        st.caption(f"File: `{output_path}`")
                    with r_col2:
                        try:
                            file_path = Path(output_path)
                            if file_path.exists():
                                with open(file_path, "rb") as f:
                                    st.download_button(
                                        label="\u2b07\ufe0f Download",
                                        data=f.read(),
                                        file_name=file_path.name,
                                        mime="application/octet-stream",
                                        key=f"dl_{selected_job.id}_{idx}",
                                    )
                            else:
                                st.caption("File not found on disk.")
                        except Exception as exc:
                            st.caption(f"Download error: {exc}")

                elif status == "failed" and error:
                    st.caption(f"Error: {error}")

            st.markdown("---")

            # ---- Bulk actions ----
            st.subheader("Bulk Actions")

            act1, act2, act3 = st.columns(3)

            # Download All as ZIP
            with act1:
                if st.button(
                    "\U0001f4e6  Download All as ZIP",
                    key=f"zip_{selected_job.id}",
                    use_container_width=True,
                    disabled=(len(success_items) == 0),
                ):
                    zip_buffer = io.BytesIO()
                    files_added = 0
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        for result in success_items:
                            fpath = result.get("output_path", "")
                            if fpath and Path(fpath).exists():
                                zf.write(fpath, Path(fpath).name)
                                files_added += 1
                    zip_buffer.seek(0)

                    if files_added > 0:
                        safe_name = (
                            selected_job.name.replace(" ", "_")
                            .replace("/", "-")
                            .replace("\\", "-")
                        )
                        st.download_button(
                            label=f"\u2b07\ufe0f Download ZIP ({files_added} files)",
                            data=zip_buffer.getvalue(),
                            file_name=f"batch_{selected_job.id}_{safe_name}.zip",
                            mime="application/zip",
                            key=f"zip_dl_{selected_job.id}",
                        )
                    else:
                        st.warning("No files available for download.")

            # Add All to Library
            with act2:
                if st.button(
                    "\U0001f4da  Add All to Library",
                    key=f"lib_{selected_job.id}",
                    use_container_width=True,
                    disabled=(len(success_items) == 0),
                ):
                    added = 0
                    for result in success_items:
                        title = result.get("title", "Untitled")
                        output_path = result.get("output_path", "")

                        # Record generated content first
                        gc_id = _record_generated_content(
                            title=title,
                            content_type=ct_key,
                            output_path=output_path,
                            duration=result.get("duration", 0),
                        )

                        if _add_to_library(
                            title=title,
                            content_type=ct_key,
                            generated_content_id=gc_id,
                            tags=f"batch,{ct_key},{selected_job.name}",
                        ):
                            added += 1

                    if added > 0:
                        st.success(f"Added {added} items to the Content Library.")
                    else:
                        st.warning("No items could be added to the library.")

            # Re-run failed items
            with act3:
                if st.button(
                    "\U0001f504  Re-run Failed Items",
                    key=f"rerun_{selected_job.id}",
                    use_container_width=True,
                    disabled=(len(failed_items) == 0),
                ):
                    # Create a new batch job with only the failed items
                    failed_titles = {r.get("title") for r in failed_items}
                    retry_items = [
                        itm for itm in items
                        if itm.get("title") in failed_titles
                    ]

                    if retry_items:
                        retry_payload = {
                            "meta": meta,
                            "items": retry_items,
                        }
                        try:
                            session = get_session()
                            retry_job = BatchJob(
                                name=f"{selected_job.name} (Retry)",
                                status="pending",
                                items_json=json.dumps(retry_payload, ensure_ascii=False),
                                created_at=datetime.utcnow(),
                            )
                            session.add(retry_job)
                            session.commit()
                            retry_job_id = retry_job.id
                            session.close()

                            st.success(
                                f"Created retry job **#{retry_job_id}** with "
                                f"{len(retry_items)} failed items. "
                                "Go to the **Process Queue** tab to start it."
                            )
                        except Exception as exc:
                            st.error(f"Failed to create retry job: {exc}")
                    else:
                        st.warning("Could not match failed items to original batch items.")


# ╔═════════════════════════════════════════════════════════════════════════╗
# ║  TAB 4 - HISTORY & ANALYTICS                                         ║
# ╚═════════════════════════════════════════════════════════════════════════╝

with tab_history:
    st.header("History & Analytics")
    st.markdown("Review all batch job history and view aggregated analytics.")

    st.markdown("---")

    history_jobs = _load_batch_jobs()

    if not history_jobs:
        st.info("No batch jobs found. Create and process batch jobs to see analytics here.")
    else:
        # ---- Overview stats ----
        total_all = len(history_jobs)
        completed_jobs = [j for j in history_jobs if j.status == "completed"]
        failed_jobs = [j for j in history_jobs if j.status == "failed"]

        # Calculate total items processed
        total_items_processed = 0
        total_success_all = 0
        total_failed_all = 0
        content_type_counts: dict[str, int] = {}
        items_per_batch: list[int] = []
        daily_items: dict[str, int] = {}

        for job in history_jobs:
            items_data = _safe_json_loads(job.items_json, default={})
            meta = items_data.get("meta", {}) if isinstance(items_data, dict) else {}
            items = items_data.get("items", []) if isinstance(items_data, dict) else []
            results = _safe_json_loads(job.results_json, default=[])

            item_count = len(items)
            items_per_batch.append(item_count)
            total_items_processed += len(results)

            ct_key = meta.get("content_type", "unknown")
            content_type_counts[ct_key] = content_type_counts.get(ct_key, 0) + item_count

            for r in results:
                if r.get("status") == "success":
                    total_success_all += 1
                elif r.get("status") == "failed":
                    total_failed_all += 1

            if job.created_at:
                day_key = job.created_at.strftime("%Y-%m-%d")
                daily_items[day_key] = daily_items.get(day_key, 0) + len(results)

        avg_items = (
            sum(items_per_batch) / len(items_per_batch)
            if items_per_batch
            else 0
        )
        completion_rate = (
            (total_success_all / total_items_processed * 100)
            if total_items_processed > 0
            else 0
        )

        # Summary cards
        h1, h2, h3, h4 = st.columns(4)
        with h1:
            st.markdown(
                '<div class="brand-card"><div class="batch-stat">'
                f'<div class="number">{total_all}</div>'
                '<div class="label">Total Batch Jobs</div>'
                "</div></div>",
                unsafe_allow_html=True,
            )
        with h2:
            st.markdown(
                '<div class="brand-card"><div class="batch-stat">'
                f'<div class="number">{total_items_processed}</div>'
                '<div class="label">Total Items Processed</div>'
                "</div></div>",
                unsafe_allow_html=True,
            )
        with h3:
            st.markdown(
                '<div class="brand-card"><div class="batch-stat">'
                f'<div class="number">{completion_rate:.1f}%</div>'
                '<div class="label">Success Rate</div>'
                "</div></div>",
                unsafe_allow_html=True,
            )
        with h4:
            st.markdown(
                '<div class="brand-card"><div class="batch-stat">'
                f'<div class="number">{avg_items:.1f}</div>'
                '<div class="label">Avg Items / Batch</div>'
                "</div></div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # ---- Charts ----
        chart_col1, chart_col2 = st.columns(2)

        # Completion rate chart (success vs failed)
        with chart_col1:
            st.subheader("Completion Rate")
            if total_items_processed > 0:
                try:
                    import pandas as pd

                    rate_df = pd.DataFrame({
                        "Status": ["Success", "Failed"],
                        "Count": [total_success_all, total_failed_all],
                    })
                    st.bar_chart(rate_df, x="Status", y="Count", color="Status")
                except ImportError:
                    st.markdown(
                        f"- **Success**: {total_success_all}\n"
                        f"- **Failed**: {total_failed_all}"
                    )
            else:
                st.caption("No data yet.")

        # Content type distribution
        with chart_col2:
            st.subheader("Content Types in Batches")
            if content_type_counts:
                try:
                    import pandas as pd

                    ct_df = pd.DataFrame({
                        "Type": [
                            CONTENT_TYPES.get(k, {}).get("label", k.title())
                            for k in content_type_counts.keys()
                        ],
                        "Items": list(content_type_counts.values()),
                    })
                    st.bar_chart(ct_df, x="Type", y="Items", color="Type")
                except ImportError:
                    for ct, cnt in content_type_counts.items():
                        label = CONTENT_TYPES.get(ct, {}).get("label", ct.title())
                        st.markdown(f"- **{label}**: {cnt} items")
            else:
                st.caption("No data yet.")

        st.markdown("---")

        # Items processed over time
        st.subheader("Items Processed Over Time")
        if daily_items:
            try:
                import pandas as pd

                daily_df = pd.DataFrame({
                    "Date": list(daily_items.keys()),
                    "Items": list(daily_items.values()),
                })
                daily_df["Date"] = pd.to_datetime(daily_df["Date"])
                daily_df = daily_df.sort_values("Date")
                st.line_chart(daily_df, x="Date", y="Items")
            except ImportError:
                for date_str, count in sorted(daily_items.items()):
                    st.markdown(f"- **{date_str}**: {count} items")
        else:
            st.caption("No processing data available yet.")

        st.markdown("---")

        # ---- Job history table ----
        st.subheader("All Batch Jobs")

        history_table = []
        for job in history_jobs:
            items_data = _safe_json_loads(job.items_json, default={})
            meta = items_data.get("meta", {}) if isinstance(items_data, dict) else {}
            items = items_data.get("items", []) if isinstance(items_data, dict) else []
            results = _safe_json_loads(job.results_json, default=[])

            ct_key = meta.get("content_type", "unknown")
            ct_label = CONTENT_TYPES.get(ct_key, {}).get("label", ct_key.title())
            succ = sum(1 for r in results if r.get("status") == "success")
            fail = sum(1 for r in results if r.get("status") == "failed")

            history_table.append({
                "ID": job.id,
                "Name": job.name,
                "Status": job.status.title(),
                "Type": ct_label,
                "Items": len(items),
                "Success": succ,
                "Failed": fail,
                "Created": (
                    job.created_at.strftime("%Y-%m-%d %H:%M") if job.created_at else "--"
                ),
                "Completed": (
                    job.completed_at.strftime("%Y-%m-%d %H:%M") if job.completed_at else "--"
                ),
            })

        st.dataframe(history_table, use_container_width=True, hide_index=True)

        st.markdown("---")

        # ---- Detailed job cards ----
        st.subheader("Job Details")
        for job in history_jobs:
            items_data = _safe_json_loads(job.items_json, default={})
            meta = items_data.get("meta", {}) if isinstance(items_data, dict) else {}
            items = items_data.get("items", []) if isinstance(items_data, dict) else []
            results = _safe_json_loads(job.results_json, default=[])

            ct_key = meta.get("content_type", "unknown")
            ct_icon = CONTENT_TYPES.get(ct_key, {}).get("icon", "\U0001f4c4")

            succ = sum(1 for r in results if r.get("status") == "success")
            fail = sum(1 for r in results if r.get("status") == "failed")
            total_dur = sum(r.get("duration", 0) for r in results)

            with st.expander(f"{ct_icon}  Job #{job.id}: {job.name} - {job.status.title()}"):
                d1, d2, d3 = st.columns(3)
                with d1:
                    st.markdown(f"**Status:** {_status_badge(job.status)}", unsafe_allow_html=True)
                    st.markdown(
                        f"**Created:** "
                        f"{job.created_at.strftime('%Y-%m-%d %H:%M') if job.created_at else '--'}"
                    )
                    if job.completed_at:
                        st.markdown(
                            f"**Completed:** {job.completed_at.strftime('%Y-%m-%d %H:%M')}"
                        )
                with d2:
                    st.markdown(f"**Total Items:** {len(items)}")
                    st.markdown(f"**Succeeded:** {succ}")
                    st.markdown(f"**Failed:** {fail}")
                with d3:
                    st.markdown(f"**Total Duration:** {total_dur:.1f}s")
                    if len(results) > 0:
                        st.markdown(f"**Avg / Item:** {total_dur / len(results):.1f}s")
                    brand_cfg = meta.get("brand_config", {})
                    if brand_cfg:
                        st.markdown(
                            f"**Brand Colors:** {'Yes' if brand_cfg.get('use_brand_colors') else 'No'}  \n"
                            f"**Logo:** {'Yes' if brand_cfg.get('include_logo') else 'No'}  \n"
                            f"**Voice:** {brand_cfg.get('voice_style', 'Default')}"
                        )

                # Show individual item results if available
                if results:
                    st.markdown("---")
                    st.markdown("**Item Results:**")
                    for idx, result in enumerate(results):
                        r_title = result.get("title", f"Item {idx + 1}")
                        r_status = result.get("status", "unknown")
                        r_dur = result.get("duration", 0)
                        r_error = result.get("error", "")

                        icon = "\u2705" if r_status == "success" else "\u274c"
                        detail = f"({r_dur}s)"
                        if r_status == "failed" and r_error:
                            detail += f" - {r_error}"

                        st.markdown(f"{icon}  **{r_title}** {detail}")

        st.markdown("---")

        # ---- Delete old batch jobs ----
        st.subheader("Cleanup")
        st.markdown(
            '<div class="brand-card">'
            "<h3>\U0001f5d1\ufe0f Delete Old Batch Jobs</h3>"
            "<p>Remove completed or failed batch jobs to keep your workspace clean. "
            "This will not delete the generated files themselves.</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        del_col1, del_col2 = st.columns(2)
        with del_col1:
            delete_status_filter = st.multiselect(
                "Select statuses to delete",
                options=["completed", "failed", "cancelled", "pending"],
                default=["failed", "cancelled"],
                key="delete_status_filter",
            )
        with del_col2:
            delete_older_than = st.number_input(
                "Older than (days)",
                min_value=0,
                max_value=365,
                value=30,
                help="Set to 0 to delete all matching jobs regardless of age.",
                key="delete_older_than",
            )

        # Count matching jobs
        cutoff_date = datetime.utcnow()
        if delete_older_than > 0:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=delete_older_than)

        matching_jobs = [
            j for j in history_jobs
            if j.status in delete_status_filter
            and (
                delete_older_than == 0
                or (j.created_at and j.created_at < cutoff_date)
            )
        ]

        st.markdown(f"**{len(matching_jobs)}** job(s) match the deletion criteria.")

        if st.button(
            f"\U0001f5d1\ufe0f  Delete {len(matching_jobs)} Job(s)",
            key="btn_delete_old_jobs",
            type="secondary",
            disabled=(len(matching_jobs) == 0),
        ):
            deleted_count = 0
            try:
                session = get_session()
                for job in matching_jobs:
                    db_job = session.query(BatchJob).get(job.id)
                    if db_job:
                        session.delete(db_job)
                        deleted_count += 1
                session.commit()
                session.close()
                st.success(f"Deleted {deleted_count} batch job(s).")
                st.rerun()
            except Exception as exc:
                st.error(f"Error deleting jobs: {exc}")
                logger.error("Batch job deletion error: %s", exc)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown(
    '<div style="text-align:center; color:#888; font-size:0.8rem;">'
    "Batch Processing | Brand Intelligence Content Hub"
    "</div>",
    unsafe_allow_html=True,
)
