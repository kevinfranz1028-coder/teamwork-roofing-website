"""
Brand Intelligence Content Hub - Dashboard Page

Displays brand health score, quick actions, recent generations,
analytics overview, content library summary, system status, and key metrics.
"""

import json
import os
import sys
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
    BRAND_ASSETS_DIR,
    CHROMADB_DIR,
    DATA_DIR,
    LOGOS_DIR,
    TEMPLATES_DIR,
    REQUIRED_ENV_KEYS,
    get_env,
)
from app.database.models import (
    BrandAsset,
    BrandConfig,
    ContentLibraryItem,
    GeneratedContent,
    Template,
    get_session,
    init_db,
)

# ---------------------------------------------------------------------------
# Optional analytics import
# ---------------------------------------------------------------------------
try:
    from app.utils.analytics import AnalyticsEngine
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard - Brand Intelligence",
    page_icon="\U0001f4ca",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Initialise DB if not yet done
# ---------------------------------------------------------------------------
if "db_ok" not in st.session_state:
    try:
        init_db()
        st.session_state["db_ok"] = True
    except Exception as exc:
        st.session_state["db_ok"] = False
        st.session_state["db_error"] = str(exc)


# ---------------------------------------------------------------------------
# Helper: calculate brand health score
# ---------------------------------------------------------------------------
def calculate_brand_health() -> dict:
    """Return a dict with individual checks and overall score (0-100)."""
    checks = {
        "has_brand_config": False,
        "has_logo": False,
        "has_voice_profile": False,
        "has_templates": False,
        "has_generated_content": False,
    }

    try:
        session = get_session()

        # Check brand config exists
        config_row = (
            session.query(BrandConfig)
            .filter(BrandConfig.config_key == "brand_config")
            .first()
        )
        if config_row and config_row.config_value:
            checks["has_brand_config"] = True

        # Check for logos
        logo_count = (
            session.query(BrandAsset)
            .filter(BrandAsset.asset_type == "logo", BrandAsset.is_active.is_(True))
            .count()
        )
        # Also check filesystem
        logo_files = list(LOGOS_DIR.glob("*")) if LOGOS_DIR.exists() else []
        if logo_count > 0 or len(logo_files) > 0:
            checks["has_logo"] = True

        # Check voice profile
        voice_row = (
            session.query(BrandConfig)
            .filter(BrandConfig.config_key == "voice_profile")
            .first()
        )
        if voice_row and voice_row.config_value:
            checks["has_voice_profile"] = True

        # Check templates
        template_count = session.query(Template).count()
        template_files = list(TEMPLATES_DIR.rglob("*.*")) if TEMPLATES_DIR.exists() else []
        if template_count > 0 or len(template_files) > 0:
            checks["has_templates"] = True

        # Check generated content
        gen_count = session.query(GeneratedContent).count()
        if gen_count > 0:
            checks["has_generated_content"] = True

        session.close()
    except Exception:
        pass

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    score = int((passed / total) * 100) if total else 0

    return {"checks": checks, "score": score, "passed": passed, "total": total}


# ---------------------------------------------------------------------------
# Helper: get key stats
# ---------------------------------------------------------------------------
def get_key_stats() -> dict:
    """Return counts for the metric cards."""
    stats = {
        "total_assets": 0,
        "templates": 0,
        "generated_items": 0,
        "library_items": 0,
    }
    try:
        session = get_session()
        stats["total_assets"] = (
            session.query(BrandAsset).filter(BrandAsset.is_active.is_(True)).count()
        )
        stats["templates"] = session.query(Template).count()
        stats["generated_items"] = session.query(GeneratedContent).count()
        stats["library_items"] = session.query(ContentLibraryItem).count()
        session.close()
    except Exception:
        pass
    return stats


# ---------------------------------------------------------------------------
# Helper: recent generations
# ---------------------------------------------------------------------------
def get_recent_generations(limit: int = 10) -> list[dict]:
    """Fetch the most recent generated content records."""
    results = []
    try:
        session = get_session()
        rows = (
            session.query(GeneratedContent)
            .order_by(GeneratedContent.generated_at.desc())
            .limit(limit)
            .all()
        )
        for row in rows:
            results.append(
                {
                    "id": row.id,
                    "title": row.title,
                    "content_type": row.content_type,
                    "format": row.format or "N/A",
                    "generated_at": (
                        row.generated_at.strftime("%Y-%m-%d %H:%M")
                        if row.generated_at
                        else "N/A"
                    ),
                    "rating": row.user_rating,
                }
            )
        session.close()
    except Exception:
        pass
    return results


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.title("\U0001f4ca Dashboard")
st.caption("Brand health overview, quick actions, and recent activity")
st.markdown("---")

# ---------------------------------------------------------------------------
# Brand health score (gauge chart)
# ---------------------------------------------------------------------------
health = calculate_brand_health()

col_gauge, col_checks = st.columns([1, 2])

with col_gauge:
    st.subheader("Brand Health Score")

    try:
        import plotly.graph_objects as go

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=health["score"],
                title={"text": "Brand Readiness", "font": {"size": 18}},
                number={"suffix": "%", "font": {"size": 40, "color": "#0066cc"}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#ccc"},
                    "bar": {"color": "#0066cc"},
                    "bgcolor": "#f0f0f0",
                    "steps": [
                        {"range": [0, 40], "color": "#ffcccc"},
                        {"range": [40, 70], "color": "#fff3cd"},
                        {"range": [70, 100], "color": "#d4edda"},
                    ],
                    "threshold": {
                        "line": {"color": "#28a745", "width": 4},
                        "thickness": 0.75,
                        "value": 80,
                    },
                },
            )
        )
        fig.update_layout(
            height=280,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.metric("Brand Health", f"{health['score']}%")

with col_checks:
    st.subheader("Health Check Details")
    st.markdown(f"**{health['passed']}** of **{health['total']}** checks passed")
    st.markdown("")

    check_labels = {
        "has_brand_config": ("Brand Configuration", "Core brand settings saved"),
        "has_logo": ("Logo Uploaded", "At least one logo in the repository"),
        "has_voice_profile": ("Voice Profile", "Brand voice and tone defined"),
        "has_templates": ("Templates Available", "Document/presentation templates loaded"),
        "has_generated_content": ("Content Generated", "At least one content item created"),
    }

    for key, (label, description) in check_labels.items():
        passed = health["checks"].get(key, False)
        icon = "\u2705" if passed else "\u274c"
        st.markdown(f"{icon} **{label}** -- {description}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Key metrics
# ---------------------------------------------------------------------------
st.subheader("Key Metrics")
stats = get_key_stats()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Brand Assets", stats["total_assets"])
m2.metric("Templates", stats["templates"])
m3.metric("Generated Items", stats["generated_items"])
m4.metric("Library Items", stats["library_items"])

st.markdown("---")

# ---------------------------------------------------------------------------
# Quick actions
# ---------------------------------------------------------------------------
st.subheader("Quick Actions")

qa1, qa2, qa3, qa4 = st.columns(4)

with qa1:
    st.markdown(
        '<div class="brand-card">'
        "<h3>\U0001f9d9 Run Brand Wizard</h3>"
        "<p>Extract brand identity from your website and existing materials.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    if st.button("Launch Wizard", key="qa_wizard", use_container_width=True):
        st.switch_page("pages/02_Brand_Repository.py")

with qa2:
    st.markdown(
        '<div class="brand-card">'
        "<h3>\U0001f4e4 Upload Assets</h3>"
        "<p>Add logos, fonts, templates, and sample content to your repository.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    if st.button("Upload Assets", key="qa_assets", use_container_width=True):
        st.switch_page("pages/02_Brand_Repository.py")

with qa3:
    st.markdown(
        '<div class="brand-card">'
        "<h3>\u2699\ufe0f Generate Content</h3>"
        "<p>Create branded presentations, documents, and training materials.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    if st.button("Generate", key="qa_generate", use_container_width=True):
        st.switch_page("pages/03_Content_Generator.py")

with qa4:
    st.markdown(
        '<div class="brand-card">'
        "<h3>\U0001f4da View Library</h3>"
        "<p>Browse and reuse previously generated branded content.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    if st.button("Open Library", key="qa_library", use_container_width=True):
        st.switch_page("pages/08_Content_Library.py")

# --- Additional quick actions row ---
qa5, qa6, _qa_spacer1, _qa_spacer2 = st.columns(4)

with qa5:
    st.markdown(
        '<div class="brand-card">'
        "<h3>\U0001f4e6 Batch Processing</h3>"
        "<p>Generate multiple content items in a single run.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    if st.button("Batch Processing", key="qa_batch", use_container_width=True):
        st.switch_page("pages/09_Batch_Processing.py")

with qa6:
    st.markdown(
        '<div class="brand-card">'
        "<h3>\U0001f4c8 Analytics</h3>"
        "<p>View generation trends, costs, and content performance.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    if st.button("Analytics", key="qa_analytics", use_container_width=True):
        st.switch_page("pages/10_Analytics.py")

st.markdown("---")

# ---------------------------------------------------------------------------
# Recent generations
# ---------------------------------------------------------------------------
st.subheader("Recent Generations")

recent = get_recent_generations(limit=10)

if recent:
    import pandas as pd

    df = pd.DataFrame(recent)
    df = df.rename(
        columns={
            "id": "ID",
            "title": "Title",
            "content_type": "Type",
            "format": "Format",
            "generated_at": "Generated At",
            "rating": "Rating",
        }
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info(
        "No content has been generated yet. "
        "Head to the **Content Generator** to create your first branded output."
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# Agent Pipeline Metrics
# ---------------------------------------------------------------------------
st.subheader("Agent Pipeline")

try:
    from app.database.models import AgentRun
    _agent_session = get_session()
    _total_runs = _agent_session.query(AgentRun).count()

    if _total_runs > 0:
        _completed_runs = _agent_session.query(AgentRun).filter(
            AgentRun.status == "completed"
        ).count()
        _compliance_passed = _agent_session.query(AgentRun).filter(
            AgentRun.compliance_passed.is_(True)
        ).count()
        _total_cost = sum(
            r.total_cost_usd or 0
            for r in _agent_session.query(AgentRun).all()
        )
        _avg_retries = sum(
            r.retry_count or 0
            for r in _agent_session.query(AgentRun).all()
        ) / max(_total_runs, 1)

        ap1, ap2, ap3, ap4 = st.columns(4)
        ap1.metric("Total Runs", _total_runs)
        ap2.metric(
            "Compliance Pass Rate",
            f"{(_compliance_passed / max(_total_runs, 1)) * 100:.0f}%",
        )
        ap3.metric("Total Cost", f"${_total_cost:.4f}")
        ap4.metric("Avg Retries", f"{_avg_retries:.1f}")

        # Recent agent runs table
        _recent_runs = (
            _agent_session.query(AgentRun)
            .order_by(AgentRun.started_at.desc())
            .limit(5)
            .all()
        )
        if _recent_runs:
            import pandas as pd

            _run_data = []
            for r in _recent_runs:
                _run_data.append({
                    "Title": r.title or "Untitled",
                    "Type": r.content_type or "N/A",
                    "Status": r.status or "N/A",
                    "Compliance": "Pass" if r.compliance_passed else "Fail",
                    "Score": f"{(r.compliance_score or 0):.0%}",
                    "Cost": f"${r.total_cost_usd or 0:.4f}",
                    "Retries": r.retry_count or 0,
                })
            st.dataframe(
                pd.DataFrame(_run_data),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info(
            "No agent pipeline runs yet. Use the Copilot to generate content "
            "with the multi-agent pipeline."
        )
    _agent_session.close()
except ImportError:
    st.info(
        "Agent pipeline metrics will appear here once the agent "
        "pipeline has been used."
    )
except Exception as _agent_exc:
    st.warning(f"Could not load agent pipeline metrics: {_agent_exc}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Analytics Overview
# ---------------------------------------------------------------------------
if ANALYTICS_AVAILABLE:
    st.subheader("Analytics Overview")

    try:
        analytics = AnalyticsEngine()
    except Exception:
        analytics = None

    if analytics is not None:
        # --- Content Generation Trends (line chart, last 30 days) ---
        try:
            timeline_data = analytics.get_generation_timeline(days=30)
            if timeline_data:
                st.markdown("#### Content Generation Trends (Last 30 Days)")
                try:
                    import plotly.graph_objects as go
                    import pandas as pd

                    tl_df = pd.DataFrame(timeline_data)
                    fig_timeline = go.Figure()
                    fig_timeline.add_trace(
                        go.Scatter(
                            x=tl_df.get("date", tl_df.iloc[:, 0]),
                            y=tl_df.get("count", tl_df.iloc[:, 1]),
                            mode="lines+markers",
                            name="Generations",
                            line=dict(color="#0066cc", width=2),
                            marker=dict(size=6),
                        )
                    )
                    fig_timeline.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Items Generated",
                        height=350,
                        margin=dict(l=40, r=20, t=20, b=40),
                    )
                    st.plotly_chart(fig_timeline, use_container_width=True)
                except ImportError:
                    import pandas as pd

                    tl_df = pd.DataFrame(timeline_data)
                    if "date" in tl_df.columns and "count" in tl_df.columns:
                        tl_df = tl_df.set_index("date")
                        st.line_chart(tl_df["count"])
                    else:
                        st.line_chart(tl_df)
                except Exception as chart_exc:
                    st.warning(f"Could not render generation trends chart: {chart_exc}")
        except Exception as tl_exc:
            st.warning(f"Could not load generation timeline: {tl_exc}")

        st.markdown("")

        # --- Content Type Breakdown (pie chart) ---
        try:
            type_breakdown = analytics.get_content_type_breakdown()
            if type_breakdown:
                st.markdown("#### Content Type Breakdown")
                try:
                    import plotly.graph_objects as go
                    import pandas as pd

                    tb_df = pd.DataFrame(type_breakdown)
                    labels = tb_df.get("content_type", tb_df.iloc[:, 0])
                    values = tb_df.get("count", tb_df.iloc[:, 1])

                    fig_pie = go.Figure(
                        go.Pie(
                            labels=labels,
                            values=values,
                            hole=0.4,
                            textinfo="label+percent",
                            marker=dict(
                                colors=[
                                    "#0066cc", "#28a745", "#ffc107",
                                    "#dc3545", "#6f42c1", "#17a2b8",
                                    "#fd7e14", "#6c757d",
                                ]
                            ),
                        )
                    )
                    fig_pie.update_layout(
                        height=350,
                        margin=dict(l=20, r=20, t=20, b=20),
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                except ImportError:
                    import pandas as pd

                    tb_df = pd.DataFrame(type_breakdown)
                    st.dataframe(tb_df, use_container_width=True, hide_index=True)
                except Exception as pie_exc:
                    st.warning(f"Could not render content type chart: {pie_exc}")
        except Exception as tb_exc:
            st.warning(f"Could not load content type breakdown: {tb_exc}")

        st.markdown("")

        # --- Time Saved Estimate ---
        try:
            time_saved = analytics.get_time_saved_estimate()
            if time_saved:
                st.markdown("#### Time Saved")
                ts_cols = st.columns(4)
                total_hours = time_saved.get("total_hours", 0)
                ts_cols[0].metric("Total Hours Saved", f"{total_hours:.1f} hrs")

                by_type = time_saved.get("by_type", {})
                col_idx = 1
                for content_type, hours in list(by_type.items())[:3]:
                    ts_cols[col_idx].metric(
                        f"{content_type.title()}",
                        f"{hours:.1f} hrs",
                    )
                    col_idx += 1
        except Exception as ts_exc:
            st.warning(f"Could not load time saved estimate: {ts_exc}")

        st.markdown("")

        # --- API Cost Tracking ---
        try:
            cost_data = analytics.get_api_cost_estimate(days=30)
            if cost_data:
                st.markdown("#### API Cost Tracking (Last 30 Days)")
                cost_cols = st.columns(4)
                monthly_cost = cost_data.get("monthly_total", 0)
                daily_avg = cost_data.get("daily_average", 0)
                cost_cols[0].metric(
                    "Estimated Monthly Cost",
                    f"${monthly_cost:.2f}",
                )
                cost_cols[1].metric(
                    "Daily Average",
                    f"${daily_avg:.2f}",
                )

                # Show per-provider breakdown if available
                by_provider = cost_data.get("by_provider", {})
                col_idx = 2
                for provider, amount in list(by_provider.items())[:2]:
                    cost_cols[col_idx].metric(
                        f"{provider}",
                        f"${amount:.2f}",
                    )
                    col_idx += 1
        except Exception as cost_exc:
            st.warning(f"Could not load API cost data: {cost_exc}")

        st.markdown("---")

        # -------------------------------------------------------------------
        # Content Library Summary
        # -------------------------------------------------------------------
        st.subheader("Content Library Summary")

        # --- Library Health ---
        try:
            library_stats = analytics.get_library_stats()
            if library_stats:
                st.markdown("#### Library Health")
                lib_cols = st.columns(4)
                lib_cols[0].metric(
                    "Total Items",
                    library_stats.get("total_items", 0),
                )
                lib_cols[1].metric(
                    "Approved",
                    library_stats.get("approved", 0),
                )
                lib_cols[2].metric(
                    "Pending Review",
                    library_stats.get("pending", 0),
                )
                avg_rating = library_stats.get("avg_rating", 0)
                lib_cols[3].metric(
                    "Avg Rating",
                    f"{avg_rating:.1f} / 5" if avg_rating else "N/A",
                )

                # Top 5 most downloaded items
                top_items = library_stats.get("top_downloaded", [])
                if top_items:
                    st.markdown("**Top 5 Most Downloaded Items**")
                    try:
                        import pandas as pd

                        top_df = pd.DataFrame(top_items)
                        st.dataframe(
                            top_df, use_container_width=True, hide_index=True
                        )
                    except Exception:
                        for item in top_items[:5]:
                            title = item.get("title", "Untitled")
                            downloads = item.get("downloads", 0)
                            st.markdown(f"- **{title}** -- {downloads} downloads")
        except Exception as lib_exc:
            st.warning(f"Could not load library stats: {lib_exc}")

        st.markdown("")

        # --- Rating Distribution ---
        try:
            rating_dist = analytics.get_rating_distribution()
            if rating_dist:
                st.markdown("#### Rating Distribution")
                try:
                    import plotly.graph_objects as go

                    labels = [str(r.get("stars", r.get("rating", ""))) for r in rating_dist]
                    values = [r.get("count", 0) for r in rating_dist]

                    fig_ratings = go.Figure(
                        go.Bar(
                            x=values,
                            y=labels,
                            orientation="h",
                            marker_color="#0066cc",
                            text=values,
                            textposition="auto",
                        )
                    )
                    fig_ratings.update_layout(
                        xaxis_title="Count",
                        yaxis_title="Stars",
                        height=250,
                        margin=dict(l=40, r=20, t=20, b=40),
                    )
                    st.plotly_chart(fig_ratings, use_container_width=True)
                except ImportError:
                    import pandas as pd

                    rd_df = pd.DataFrame(rating_dist)
                    if "stars" in rd_df.columns:
                        rd_df = rd_df.set_index("stars")
                    elif "rating" in rd_df.columns:
                        rd_df = rd_df.set_index("rating")
                    st.bar_chart(rd_df["count"] if "count" in rd_df.columns else rd_df)
                except Exception as rd_exc:
                    st.warning(f"Could not render rating distribution chart: {rd_exc}")
        except Exception as rd_exc:
            st.warning(f"Could not load rating distribution: {rd_exc}")

        st.markdown("---")
    else:
        st.info(
            "Analytics engine could not be initialised. "
            "Check configuration and try again."
        )
        st.markdown("---")
else:
    # Analytics module not available -- show placeholder
    st.subheader("Analytics Overview")
    st.info(
        "Analytics module is not yet installed. "
        "Install it to see generation trends, cost tracking, and content library stats."
    )
    st.markdown("---")

# ---------------------------------------------------------------------------
# System status
# ---------------------------------------------------------------------------
st.subheader("System Status")

s1, s2, s3, s4 = st.columns(4)

with s1:
    db_ok = st.session_state.get("db_ok", False)
    if db_ok:
        st.success("Database: Connected")
    else:
        st.error(f"Database: Error -- {st.session_state.get('db_error', 'Unknown')}")

with s2:
    chroma_ok = CHROMADB_DIR.exists()
    if chroma_ok:
        st.success("ChromaDB: Directory Ready")
    else:
        st.warning("ChromaDB: Not initialised")

with s3:
    api_keys_configured = []
    api_keys_missing = []
    for key in REQUIRED_ENV_KEYS:
        if os.getenv(key, "").strip():
            api_keys_configured.append(key)
        else:
            api_keys_missing.append(key)

    if not api_keys_missing:
        st.success(f"API Keys: {len(api_keys_configured)}/{len(REQUIRED_ENV_KEYS)} configured")
    else:
        st.warning(
            f"API Keys: {len(api_keys_configured)}/{len(REQUIRED_ENV_KEYS)} configured"
        )
        with st.expander("Missing keys"):
            for k in api_keys_missing:
                st.code(k)

with s4:
    presenton_url = get_env("PRESENTON_URL")
    if presenton_url:
        st.info(f"Presenton: {presenton_url}")
    else:
        st.warning("Presenton: Not configured")

# --- Storage Usage (analytics-powered) ---
if ANALYTICS_AVAILABLE:
    try:
        analytics_for_storage = AnalyticsEngine()
        storage_data = analytics_for_storage.get_storage_usage()
        if storage_data:
            st.markdown("")
            st.markdown("#### Storage Usage")
            stor_cols = st.columns(4)
            total_storage = storage_data.get("total_mb", 0)
            stor_cols[0].metric(
                "Total Storage Used",
                f"{total_storage:.1f} MB" if total_storage < 1024 else f"{total_storage / 1024:.2f} GB",
            )
            assets_storage = storage_data.get("assets_mb", None)
            if assets_storage is not None:
                stor_cols[1].metric("Assets", f"{assets_storage:.1f} MB")
            generated_storage = storage_data.get("generated_mb", None)
            if generated_storage is not None:
                stor_cols[2].metric("Generated Content", f"{generated_storage:.1f} MB")
            db_storage = storage_data.get("database_mb", None)
            if db_storage is not None:
                stor_cols[3].metric("Database", f"{db_storage:.1f} MB")
    except Exception:
        pass
