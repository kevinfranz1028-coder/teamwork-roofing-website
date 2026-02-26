"""
Brand Intelligence Content Hub - Analytics & Insights

Comprehensive analytics dashboards covering generation volume, quality
metrics, cost tracking, storage usage, and system health.  Pulls data
from the AnalyticsEngine (app.utils.analytics) and FeedbackLoop
(app.core.feedback_loop) modules and renders interactive charts via
Plotly with graceful fallback to native Streamlit charts.
"""

import json
import sys
from datetime import datetime, timedelta
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
from app.config import BASE_DIR, OUTPUT_DIR
from app.database.models import (
    get_session,
    init_db,
    GeneratedContent,
    ContentLibraryItem,
    BatchJob,
    Template,
)

# ---------------------------------------------------------------------------
# Optional imports -- analytics engine
# ---------------------------------------------------------------------------
try:
    from app.utils.analytics import AnalyticsEngine

    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Optional imports -- feedback loop
# ---------------------------------------------------------------------------
try:
    from app.core.feedback_loop import FeedbackLoop

    FEEDBACK_AVAILABLE = True
except ImportError:
    FEEDBACK_AVAILABLE = False

# ---------------------------------------------------------------------------
# Optional imports -- Plotly
# ---------------------------------------------------------------------------
try:
    import plotly.graph_objects as go
    import plotly.express as px

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ---------------------------------------------------------------------------
# Optional imports -- Pandas
# ---------------------------------------------------------------------------
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Analytics & Insights",
    page_icon="\U0001f4ca",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
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
.stat-card {
    background: linear-gradient(135deg, #ffffff 0%, #f0f4ff 100%);
    border: 1px solid #d0d9f0;
    border-radius: 10px;
    padding: 16px;
    margin: 6px 0;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.stat-card h4 {
    margin: 0 0 4px 0;
    color: #0066cc;
    font-size: 1.8rem;
}
.stat-card p {
    margin: 0;
    color: #666;
    font-size: 0.85rem;
}
.section-header {
    border-left: 4px solid #0066cc;
    padding-left: 12px;
    margin: 16px 0 12px 0;
}
</style>""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Initialise database
# ---------------------------------------------------------------------------
if "db_ok" not in st.session_state:
    try:
        init_db()
        st.session_state["db_ok"] = True
    except Exception as exc:
        st.session_state["db_ok"] = False
        st.session_state["db_error"] = str(exc)

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.title("\U0001f4ca Analytics & Insights")
st.caption(
    "Comprehensive dashboards for content generation metrics, quality "
    "tracking, cost analysis, and system health."
)
st.markdown("---")

# ---------------------------------------------------------------------------
# Guard: analytics engine availability
# ---------------------------------------------------------------------------
if not ANALYTICS_AVAILABLE:
    st.warning(
        "The **AnalyticsEngine** module could not be imported. "
        "Please ensure `app.utils.analytics` is available and all "
        "dependencies are installed."
    )
    st.info(
        "Once the analytics module is available, this page will display "
        "interactive dashboards covering generation volume, quality metrics, "
        "cost tracking, storage usage, and system health."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Instantiate analytics engine
# ---------------------------------------------------------------------------
try:
    analytics = AnalyticsEngine()
except Exception as exc:
    st.error(f"Failed to initialise AnalyticsEngine: {exc}")
    st.stop()

# ---------------------------------------------------------------------------
# Instantiate feedback loop (optional)
# ---------------------------------------------------------------------------
feedback_loop = None
if FEEDBACK_AVAILABLE:
    try:
        feedback_loop = FeedbackLoop()
    except Exception:
        feedback_loop = None


# =========================================================================
# Helper: format type label
# =========================================================================
def _label(content_type: str) -> str:
    """Turn a snake_case content type into a Title Case label."""
    return content_type.replace("_", " ").title()


# =========================================================================
# Helper: render a stat card
# =========================================================================
def _stat_card(value: str, label: str) -> None:
    """Render a styled stat card via markdown."""
    st.markdown(
        f'<div class="stat-card">'
        f"<h4>{value}</h4>"
        f"<p>{label}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )


# =========================================================================
# Helper: Plotly colour palette
# =========================================================================
CHART_COLORS = [
    "#0066cc",
    "#28a745",
    "#ffc107",
    "#dc3545",
    "#6f42c1",
    "#17a2b8",
    "#fd7e14",
    "#6c757d",
    "#e83e8c",
    "#20c997",
]


# =========================================================================
# TABS
# =========================================================================
tab_overview, tab_generation, tab_quality, tab_cost, tab_system = st.tabs(
    [
        "\U0001f3e0 Overview",
        "\U0001f4c8 Generation Analytics",
        "\u2b50 Quality & Feedback",
        "\U0001f4b0 Cost & Performance",
        "\U0001f5a5\ufe0f Storage & System",
    ]
)

# =========================================================================
# TAB 1 -- OVERVIEW DASHBOARD
# =========================================================================
with tab_overview:
    st.markdown(
        '<div class="section-header"><h3>Dashboard Overview</h3></div>',
        unsafe_allow_html=True,
    )

    # --- Hero metrics row ---
    try:
        volume = analytics.get_generation_volume(days=30)
        time_saved = analytics.get_time_saved_estimate()
        cost_data = analytics.get_api_cost_estimate(days=30)
        library = analytics.get_library_stats()
    except Exception:
        volume = {"total": 0, "by_type": {}, "by_day": []}
        time_saved = {"total_hours": 0.0, "total_minutes": 0, "by_type": {}}
        cost_data = {"total_cost": 0.0, "by_type": {}, "daily_avg": 0.0}
        library = {
            "total_items": 0,
            "approved": 0,
            "pending": 0,
            "by_category": {},
            "avg_rating": 0.0,
            "top_downloaded": [],
        }

    hero_c1, hero_c2, hero_c3, hero_c4 = st.columns(4)
    with hero_c1:
        st.metric("Total Generated (30d)", volume.get("total", 0))
    with hero_c2:
        hours = time_saved.get("total_hours", 0.0)
        st.metric("Time Saved", f"{hours:.1f} hrs")
    with hero_c3:
        total_cost = cost_data.get("total_cost", 0.0)
        st.metric("Est. API Cost (30d)", f"${total_cost:.2f}")
    with hero_c4:
        st.metric("Library Items", library.get("total_items", 0))

    st.markdown("---")

    # --- Generation trends line chart (30 days) ---
    st.markdown("#### Content Generation Trends (Last 30 Days)")

    try:
        timeline_data = analytics.get_generation_timeline(days=30)
    except Exception:
        timeline_data = []

    if timeline_data:
        if PLOTLY_AVAILABLE and PANDAS_AVAILABLE:
            try:
                tl_df = pd.DataFrame(timeline_data)
                fig_trend = go.Figure()

                # Determine content type columns (everything except 'date')
                type_cols = [c for c in tl_df.columns if c != "date"]

                for idx, col in enumerate(type_cols):
                    fig_trend.add_trace(
                        go.Scatter(
                            x=tl_df["date"],
                            y=tl_df[col],
                            mode="lines+markers",
                            name=_label(col),
                            line=dict(
                                color=CHART_COLORS[idx % len(CHART_COLORS)],
                                width=2,
                            ),
                            marker=dict(size=5),
                        )
                    )

                fig_trend.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Items Generated",
                    height=380,
                    margin=dict(l=40, r=20, t=30, b=40),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                    hovermode="x unified",
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            except Exception as chart_exc:
                st.warning(f"Could not render Plotly trend chart: {chart_exc}")
        elif PANDAS_AVAILABLE:
            try:
                tl_df = pd.DataFrame(timeline_data)
                tl_df = tl_df.set_index("date")
                st.line_chart(tl_df)
            except Exception as chart_exc:
                st.warning(f"Could not render trend chart: {chart_exc}")
        else:
            st.info("Install pandas to view generation trend charts.")
    else:
        st.info("No generation data available for the last 30 days.")

    st.markdown("---")

    # --- Content type breakdown pie/donut chart ---
    col_pie, col_stats = st.columns([1, 1])

    with col_pie:
        st.markdown("#### Content Type Breakdown")

        try:
            type_breakdown = analytics.get_content_type_breakdown()
        except Exception:
            type_breakdown = []

        if type_breakdown:
            if PLOTLY_AVAILABLE:
                try:
                    labels = [_label(item["type"]) for item in type_breakdown]
                    values = [item["count"] for item in type_breakdown]

                    fig_pie = go.Figure(
                        go.Pie(
                            labels=labels,
                            values=values,
                            hole=0.45,
                            textinfo="label+percent",
                            marker=dict(
                                colors=CHART_COLORS[: len(labels)]
                            ),
                        )
                    )
                    fig_pie.update_layout(
                        height=350,
                        margin=dict(l=20, r=20, t=30, b=20),
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.15,
                            xanchor="center",
                            x=0.5,
                        ),
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                except Exception as pie_exc:
                    st.warning(f"Could not render pie chart: {pie_exc}")
            elif PANDAS_AVAILABLE:
                try:
                    tb_df = pd.DataFrame(type_breakdown)
                    tb_df["type"] = tb_df["type"].apply(_label)
                    st.bar_chart(tb_df.set_index("type")["count"])
                except Exception:
                    for item in type_breakdown:
                        st.write(f"- {_label(item['type'])}: {item['count']} ({item['pct']}%)")
            else:
                for item in type_breakdown:
                    st.write(f"- {_label(item['type'])}: {item['count']} ({item['pct']}%)")
        else:
            st.info("No content type data available yet.")

    # --- Quick stats cards for each content type ---
    with col_stats:
        st.markdown("#### Quick Stats by Content Type")

        by_type = volume.get("by_type", {})
        time_by_type = time_saved.get("by_type", {})
        cost_by_type = cost_data.get("by_type", {})

        if by_type:
            # Display in a 2-column grid within this column
            type_keys = [k for k in by_type.keys() if by_type[k] > 0]
            if not type_keys:
                type_keys = list(by_type.keys())[:5]

            for i in range(0, len(type_keys), 2):
                row_cols = st.columns(2)
                for j, col in enumerate(row_cols):
                    idx = i + j
                    if idx < len(type_keys):
                        ct = type_keys[idx]
                        count = by_type.get(ct, 0)
                        minutes = time_by_type.get(ct, 0)
                        cost = cost_by_type.get(ct, 0.0)
                        with col:
                            st.markdown(
                                f'<div class="brand-card">'
                                f"<h3>{_label(ct)}</h3>"
                                f"<p><strong>{count}</strong> items generated</p>"
                                f"<p>{minutes} min saved &bull; ${cost:.2f} est. cost</p>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
        else:
            st.info("No generation stats available yet.")


# =========================================================================
# TAB 2 -- GENERATION ANALYTICS
# =========================================================================
with tab_generation:
    st.markdown(
        '<div class="section-header"><h3>Generation Analytics</h3></div>',
        unsafe_allow_html=True,
    )

    # --- Date range selector ---
    gen_range_label = st.selectbox(
        "Time Range",
        options=["Last 7 Days", "Last 30 Days", "Last 90 Days"],
        index=1,
        key="gen_range",
    )
    gen_days_map = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90}
    gen_days = gen_days_map.get(gen_range_label, 30)

    # Fetch data for the selected range
    try:
        gen_volume = analytics.get_generation_volume(days=gen_days)
    except Exception:
        gen_volume = {"total": 0, "by_type": {}, "by_day": []}

    try:
        gen_timeline = analytics.get_generation_timeline(days=gen_days)
    except Exception:
        gen_timeline = []

    try:
        avg_time = analytics.get_avg_generation_time()
    except Exception:
        avg_time = {}

    try:
        template_usage = analytics.get_template_usage()
    except Exception:
        template_usage = []

    st.markdown("---")

    # --- Volume by content type bar chart ---
    st.markdown("#### Generation Volume by Content Type")

    gen_by_type = gen_volume.get("by_type", {})
    if gen_by_type and any(v > 0 for v in gen_by_type.values()):
        if PLOTLY_AVAILABLE:
            try:
                sorted_types = sorted(gen_by_type.items(), key=lambda x: x[1], reverse=True)
                types_labels = [_label(t) for t, _ in sorted_types]
                types_values = [v for _, v in sorted_types]

                fig_vol = go.Figure(
                    go.Bar(
                        x=types_labels,
                        y=types_values,
                        marker_color=CHART_COLORS[: len(types_labels)],
                        text=types_values,
                        textposition="auto",
                    )
                )
                fig_vol.update_layout(
                    xaxis_title="Content Type",
                    yaxis_title="Count",
                    height=350,
                    margin=dict(l=40, r=20, t=20, b=60),
                )
                st.plotly_chart(fig_vol, use_container_width=True)
            except Exception as vol_exc:
                st.warning(f"Could not render volume chart: {vol_exc}")
        elif PANDAS_AVAILABLE:
            try:
                vol_df = pd.DataFrame(
                    [{"Type": _label(k), "Count": v} for k, v in gen_by_type.items()]
                )
                st.bar_chart(vol_df.set_index("Type")["Count"])
            except Exception:
                for k, v in gen_by_type.items():
                    st.write(f"- {_label(k)}: {v}")
        else:
            for k, v in gen_by_type.items():
                st.write(f"- {_label(k)}: {v}")
    else:
        st.info(f"No generation data available for the last {gen_days} days.")

    st.markdown("---")

    # --- Average generation time by type ---
    col_avg_time, col_timeline = st.columns(2)

    with col_avg_time:
        st.markdown("#### Avg Generation Time by Type")

        if avg_time and any(v > 0 for v in avg_time.values()):
            if PLOTLY_AVAILABLE:
                try:
                    sorted_times = sorted(avg_time.items(), key=lambda x: x[1], reverse=True)
                    time_labels = [_label(t) for t, _ in sorted_times]
                    time_values = [v for _, v in sorted_times]

                    fig_time = go.Figure(
                        go.Bar(
                            y=time_labels,
                            x=time_values,
                            orientation="h",
                            marker_color=CHART_COLORS[: len(time_labels)],
                            text=[f"{v:.1f}s" for v in time_values],
                            textposition="auto",
                        )
                    )
                    fig_time.update_layout(
                        xaxis_title="Seconds",
                        height=320,
                        margin=dict(l=120, r=20, t=20, b=40),
                    )
                    st.plotly_chart(fig_time, use_container_width=True)
                except Exception as time_exc:
                    st.warning(f"Could not render generation time chart: {time_exc}")
            elif PANDAS_AVAILABLE:
                try:
                    time_df = pd.DataFrame(
                        [{"Type": _label(k), "Seconds": v} for k, v in avg_time.items() if v > 0]
                    )
                    if not time_df.empty:
                        st.bar_chart(time_df.set_index("Type")["Seconds"])
                except Exception:
                    for k, v in avg_time.items():
                        if v > 0:
                            st.write(f"- {_label(k)}: {v:.1f}s")
            else:
                for k, v in avg_time.items():
                    if v > 0:
                        st.write(f"- {_label(k)}: {v:.1f}s")
        else:
            st.info("No generation time data recorded yet.")

    # --- Generation timeline ---
    with col_timeline:
        st.markdown(f"#### Generation Timeline ({gen_range_label})")

        if gen_timeline:
            if PLOTLY_AVAILABLE and PANDAS_AVAILABLE:
                try:
                    tl_df = pd.DataFrame(gen_timeline)
                    type_cols = [c for c in tl_df.columns if c != "date"]

                    # Stack all types into a single total line for this view
                    tl_df["total"] = tl_df[type_cols].sum(axis=1)

                    fig_tl = go.Figure(
                        go.Scatter(
                            x=tl_df["date"],
                            y=tl_df["total"],
                            mode="lines+markers",
                            name="Total",
                            line=dict(color="#0066cc", width=2),
                            marker=dict(size=5),
                            fill="tozeroy",
                            fillcolor="rgba(0, 102, 204, 0.1)",
                        )
                    )
                    fig_tl.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Items",
                        height=320,
                        margin=dict(l=40, r=20, t=20, b=40),
                    )
                    st.plotly_chart(fig_tl, use_container_width=True)
                except Exception as tl_exc:
                    st.warning(f"Could not render timeline chart: {tl_exc}")
            elif PANDAS_AVAILABLE:
                try:
                    tl_df = pd.DataFrame(gen_timeline).set_index("date")
                    tl_df["total"] = tl_df.sum(axis=1)
                    st.line_chart(tl_df["total"])
                except Exception:
                    st.info("Could not render timeline chart.")
            else:
                st.info("Install pandas and plotly to view timeline charts.")
        else:
            st.info(f"No timeline data for the last {gen_days} days.")

    st.markdown("---")

    # --- Peak generation analysis ---
    st.markdown("#### Peak Generation Analysis")

    try:
        gen_by_day = gen_volume.get("by_day", [])
    except Exception:
        gen_by_day = []

    if gen_by_day and PANDAS_AVAILABLE:
        try:
            day_df = pd.DataFrame(gen_by_day)
            if "date" in day_df.columns and "count" in day_df.columns:
                day_df["date"] = pd.to_datetime(day_df["date"])
                day_df["day_of_week"] = day_df["date"].dt.day_name()

                # Aggregate by day of week
                dow_agg = (
                    day_df.groupby("day_of_week")["count"]
                    .sum()
                    .reindex(
                        [
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                            "Saturday",
                            "Sunday",
                        ]
                    )
                    .fillna(0)
                )

                peak_col1, peak_col2 = st.columns(2)

                with peak_col1:
                    st.markdown("**Generation by Day of Week**")
                    if PLOTLY_AVAILABLE:
                        try:
                            fig_dow = go.Figure(
                                go.Bar(
                                    x=dow_agg.index.tolist(),
                                    y=dow_agg.values.tolist(),
                                    marker_color="#0066cc",
                                    text=dow_agg.values.astype(int).tolist(),
                                    textposition="auto",
                                )
                            )
                            fig_dow.update_layout(
                                height=280,
                                margin=dict(l=40, r=20, t=20, b=40),
                                xaxis_title="Day",
                                yaxis_title="Count",
                            )
                            st.plotly_chart(fig_dow, use_container_width=True)
                        except Exception:
                            st.bar_chart(dow_agg)
                    else:
                        st.bar_chart(dow_agg)

                with peak_col2:
                    st.markdown("**Peak Days Summary**")
                    if not day_df.empty:
                        busiest_day = dow_agg.idxmax()
                        busiest_count = int(dow_agg.max())
                        quietest_day = dow_agg.idxmin()
                        quietest_count = int(dow_agg.min())
                        total_gen = int(dow_agg.sum())
                        avg_per_day = round(total_gen / max(gen_days, 1), 1)

                        st.markdown(
                            f'<div class="brand-card">'
                            f"<p><strong>Busiest Day:</strong> {busiest_day} ({busiest_count} items)</p>"
                            f"<p><strong>Quietest Day:</strong> {quietest_day} ({quietest_count} items)</p>"
                            f"<p><strong>Daily Average:</strong> {avg_per_day} items/day</p>"
                            f"<p><strong>Total ({gen_range_label}):</strong> {total_gen} items</p>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.info("Not enough data for peak analysis.")
            else:
                st.info("Generation day data not in expected format.")
        except Exception as peak_exc:
            st.warning(f"Could not compute peak analysis: {peak_exc}")
    elif not gen_by_day:
        st.info("No daily generation data available for peak analysis.")
    else:
        st.info("Install pandas to view peak generation analysis.")

    st.markdown("---")

    # --- Template usage ranking ---
    st.markdown("#### Template Usage Ranking")

    if template_usage:
        if PANDAS_AVAILABLE:
            try:
                tmpl_df = pd.DataFrame(template_usage)
                display_cols = ["name", "type", "usage_count"]
                available_cols = [c for c in display_cols if c in tmpl_df.columns]
                if available_cols:
                    tmpl_display = tmpl_df[available_cols].rename(
                        columns={
                            "name": "Template Name",
                            "type": "Type",
                            "usage_count": "Uses",
                        }
                    )
                    st.dataframe(tmpl_display, use_container_width=True, hide_index=True)
                else:
                    st.dataframe(tmpl_df, use_container_width=True, hide_index=True)
            except Exception:
                for tmpl in template_usage:
                    st.write(
                        f"- **{tmpl.get('name', 'N/A')}** ({tmpl.get('type', 'N/A')}): "
                        f"{tmpl.get('usage_count', 0)} uses"
                    )
        else:
            for tmpl in template_usage:
                st.write(
                    f"- **{tmpl.get('name', 'N/A')}** ({tmpl.get('type', 'N/A')}): "
                    f"{tmpl.get('usage_count', 0)} uses"
                )
    else:
        st.info("No templates have been used yet.")


# =========================================================================
# TAB 3 -- QUALITY & FEEDBACK
# =========================================================================
with tab_quality:
    st.markdown(
        '<div class="section-header"><h3>Quality & Feedback</h3></div>',
        unsafe_allow_html=True,
    )

    # --- Rating distribution ---
    st.markdown("#### Rating Distribution")

    try:
        rating_dist = analytics.get_rating_distribution()
    except Exception:
        rating_dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "avg": 0.0, "total_rated": 0}

    total_rated = rating_dist.get("total_rated", 0)
    avg_rating = rating_dist.get("avg", 0.0)

    # Metrics row
    rating_m1, rating_m2, rating_m3, rating_m4 = st.columns(4)
    with rating_m1:
        st.metric("Average Rating", f"{avg_rating:.1f} / 5.0" if avg_rating else "N/A")
    with rating_m2:
        st.metric("Total Rated", total_rated)
    with rating_m3:
        five_stars = rating_dist.get("5", 0)
        pct_5 = round((five_stars / max(total_rated, 1)) * 100, 1)
        st.metric("5-Star Rate", f"{pct_5}%")
    with rating_m4:
        low_stars = rating_dist.get("1", 0) + rating_dist.get("2", 0)
        pct_low = round((low_stars / max(total_rated, 1)) * 100, 1)
        st.metric("Low Rating Rate (1-2)", f"{pct_low}%")

    st.markdown("")

    # Rating bar chart
    if total_rated > 0:
        rating_labels = ["1 Star", "2 Stars", "3 Stars", "4 Stars", "5 Stars"]
        rating_values = [
            rating_dist.get("1", 0),
            rating_dist.get("2", 0),
            rating_dist.get("3", 0),
            rating_dist.get("4", 0),
            rating_dist.get("5", 0),
        ]
        rating_colors = ["#dc3545", "#fd7e14", "#ffc107", "#28a745", "#0066cc"]

        if PLOTLY_AVAILABLE:
            try:
                fig_rating = go.Figure(
                    go.Bar(
                        y=rating_labels,
                        x=rating_values,
                        orientation="h",
                        marker_color=rating_colors,
                        text=rating_values,
                        textposition="auto",
                    )
                )
                fig_rating.update_layout(
                    xaxis_title="Number of Ratings",
                    height=300,
                    margin=dict(l=80, r=20, t=20, b=40),
                )
                st.plotly_chart(fig_rating, use_container_width=True)
            except Exception as rat_exc:
                st.warning(f"Could not render rating chart: {rat_exc}")
        elif PANDAS_AVAILABLE:
            try:
                rat_df = pd.DataFrame(
                    {"Rating": rating_labels, "Count": rating_values}
                )
                st.bar_chart(rat_df.set_index("Rating")["Count"])
            except Exception:
                for lbl, val in zip(rating_labels, rating_values):
                    st.write(f"- {lbl}: {val}")
        else:
            for lbl, val in zip(rating_labels, rating_values):
                st.write(f"- {lbl}: {val}")
    else:
        st.info("No ratings have been recorded yet. Rate your generated content to see distribution data.")

    st.markdown("---")

    # --- Average rating by content type ---
    st.markdown("#### Average Rating by Content Type")

    try:
        session = get_session()
        from sqlalchemy import func as sa_func

        type_rating_rows = (
            session.query(
                GeneratedContent.content_type,
                sa_func.avg(GeneratedContent.user_rating),
                sa_func.count(GeneratedContent.id),
            )
            .filter(GeneratedContent.user_rating.isnot(None))
            .group_by(GeneratedContent.content_type)
            .all()
        )
        session.close()

        type_ratings = []
        for content_type, avg_r, count in type_rating_rows:
            key = (content_type or "").lower().strip() or "unknown"
            type_ratings.append(
                {
                    "type": _label(key),
                    "avg_rating": round(float(avg_r), 2) if avg_r else 0.0,
                    "count": count,
                }
            )
    except Exception:
        type_ratings = []

    if type_ratings:
        if PLOTLY_AVAILABLE:
            try:
                tr_labels = [r["type"] for r in type_ratings]
                tr_values = [r["avg_rating"] for r in type_ratings]
                tr_counts = [r["count"] for r in type_ratings]

                fig_tr = go.Figure(
                    go.Bar(
                        x=tr_labels,
                        y=tr_values,
                        marker_color=CHART_COLORS[: len(tr_labels)],
                        text=[f"{v:.1f} ({c})" for v, c in zip(tr_values, tr_counts)],
                        textposition="auto",
                    )
                )
                fig_tr.update_layout(
                    xaxis_title="Content Type",
                    yaxis_title="Average Rating",
                    yaxis=dict(range=[0, 5.5]),
                    height=320,
                    margin=dict(l=40, r=20, t=20, b=60),
                )
                st.plotly_chart(fig_tr, use_container_width=True)
            except Exception as tr_exc:
                st.warning(f"Could not render type rating chart: {tr_exc}")
        elif PANDAS_AVAILABLE:
            try:
                tr_df = pd.DataFrame(type_ratings)
                st.bar_chart(tr_df.set_index("type")["avg_rating"])
            except Exception:
                for r in type_ratings:
                    st.write(f"- {r['type']}: {r['avg_rating']:.1f} ({r['count']} ratings)")
        else:
            for r in type_ratings:
                st.write(f"- {r['type']}: {r['avg_rating']:.1f} ({r['count']} ratings)")
    else:
        st.info("No rated content available for per-type breakdown.")

    st.markdown("---")

    # --- Approval rate ---
    st.markdown("#### Approval Status")

    try:
        lib_stats = analytics.get_library_stats()
    except Exception:
        lib_stats = {"total_items": 0, "approved": 0, "pending": 0, "by_category": {}, "avg_rating": 0.0, "top_downloaded": []}

    lib_total = lib_stats.get("total_items", 0)
    lib_approved = lib_stats.get("approved", 0)
    lib_pending = lib_stats.get("pending", 0)

    if lib_total > 0:
        approval_rate = round((lib_approved / lib_total) * 100, 1)

        appr_c1, appr_c2, appr_c3 = st.columns(3)
        with appr_c1:
            st.metric("Approval Rate", f"{approval_rate}%")
        with appr_c2:
            st.metric("Approved", lib_approved)
        with appr_c3:
            st.metric("Pending Review", lib_pending)

        if PLOTLY_AVAILABLE:
            try:
                fig_appr = go.Figure(
                    go.Pie(
                        labels=["Approved", "Pending"],
                        values=[lib_approved, lib_pending],
                        hole=0.5,
                        marker=dict(colors=["#28a745", "#ffc107"]),
                        textinfo="label+percent",
                    )
                )
                fig_appr.update_layout(
                    height=280,
                    margin=dict(l=20, r=20, t=20, b=20),
                    showlegend=False,
                )
                st.plotly_chart(fig_appr, use_container_width=True)
            except Exception:
                pass
    else:
        st.info("No library items available. Add content to the library to track approval status.")

    st.markdown("---")

    # --- Feedback loop patterns ---
    st.markdown("#### Feedback Loop Patterns")

    if feedback_loop is not None:
        try:
            has_patterns = feedback_loop.has_patterns()
        except Exception:
            has_patterns = False

        if has_patterns:
            try:
                pattern_summary = feedback_loop.get_pattern_summary()
            except Exception:
                pattern_summary = {}

            if pattern_summary:
                fb_c1, fb_c2, fb_c3 = st.columns(3)
                with fb_c1:
                    st.metric("Total Edits Tracked", pattern_summary.get("total_edits", 0))
                with fb_c2:
                    edits_by_type = pattern_summary.get("edits_by_type", {})
                    st.metric("Content Types Edited", len(edits_by_type))
                with fb_c3:
                    top_patterns = pattern_summary.get("top_patterns", [])
                    st.metric("Learned Patterns", len(top_patterns))

                st.markdown("")

                # Edits by content type
                if edits_by_type:
                    st.markdown("**Edits by Content Type**")
                    if PLOTLY_AVAILABLE:
                        try:
                            ebt_labels = [_label(k) for k in edits_by_type.keys()]
                            ebt_values = list(edits_by_type.values())

                            fig_ebt = go.Figure(
                                go.Bar(
                                    x=ebt_labels,
                                    y=ebt_values,
                                    marker_color=CHART_COLORS[: len(ebt_labels)],
                                    text=ebt_values,
                                    textposition="auto",
                                )
                            )
                            fig_ebt.update_layout(
                                xaxis_title="Content Type",
                                yaxis_title="Number of Edits",
                                height=280,
                                margin=dict(l=40, r=20, t=20, b=60),
                            )
                            st.plotly_chart(fig_ebt, use_container_width=True)
                        except Exception:
                            for k, v in edits_by_type.items():
                                st.write(f"- {_label(k)}: {v} edits")
                    else:
                        for k, v in edits_by_type.items():
                            st.write(f"- {_label(k)}: {v} edits")

                st.markdown("")

                # Top learned patterns
                if top_patterns:
                    st.markdown("**Most Common Edit Patterns**")
                    for i, pattern in enumerate(top_patterns[:10], 1):
                        if isinstance(pattern, dict):
                            desc = pattern.get("description", pattern.get("pattern", str(pattern)))
                            freq = pattern.get("frequency", pattern.get("count", ""))
                            st.markdown(f"{i}. {desc}" + (f" *(frequency: {freq})*" if freq else ""))
                        else:
                            st.markdown(f"{i}. {pattern}")

                st.markdown("")

                # Patterns by content type
                patterns_by_type = pattern_summary.get("patterns_by_type", {})
                if patterns_by_type:
                    st.markdown("**Patterns by Content Type**")
                    for ct, count in patterns_by_type.items():
                        st.write(f"- {_label(ct)}: {count} pattern(s) learned")

                st.markdown("")

                # Recent edit history
                with st.expander("Recent Edit History", expanded=False):
                    try:
                        edit_history = feedback_loop.get_edit_history(limit=20)
                    except Exception:
                        edit_history = []

                    if edit_history:
                        if PANDAS_AVAILABLE:
                            try:
                                hist_records = []
                                for edit in edit_history:
                                    hist_records.append(
                                        {
                                            "Content Type": _label(
                                                edit.get("content_type", "unknown")
                                            ),
                                            "Change Ratio": f"{edit.get('change_ratio', 0):.1%}"
                                            if edit.get("change_ratio") is not None
                                            else "N/A",
                                            "Timestamp": edit.get("timestamp", "N/A"),
                                        }
                                    )
                                hist_df = pd.DataFrame(hist_records)
                                st.dataframe(hist_df, use_container_width=True, hide_index=True)
                            except Exception:
                                for edit in edit_history[:20]:
                                    ct = _label(edit.get("content_type", "unknown"))
                                    ts = edit.get("timestamp", "N/A")
                                    st.write(f"- [{ts}] {ct}")
                        else:
                            for edit in edit_history[:20]:
                                ct = _label(edit.get("content_type", "unknown"))
                                ts = edit.get("timestamp", "N/A")
                                st.write(f"- [{ts}] {ct}")
                    else:
                        st.info("No edit history available.")
        else:
            st.info(
                "No feedback patterns have been learned yet. "
                "Edit generated content to start building feedback patterns."
            )
    else:
        st.info(
            "The Feedback Loop module is not available. "
            "Install it to track editing patterns and improve future content generation."
        )


# =========================================================================
# TAB 4 -- COST & PERFORMANCE
# =========================================================================
with tab_cost:
    st.markdown(
        '<div class="section-header"><h3>Cost & Performance</h3></div>',
        unsafe_allow_html=True,
    )

    # --- Date range selector ---
    cost_range_label = st.selectbox(
        "Time Range",
        options=["Last 7 Days", "Last 30 Days", "Last 90 Days"],
        index=1,
        key="cost_range",
    )
    cost_days_map = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90}
    cost_days = cost_days_map.get(cost_range_label, 30)

    try:
        cost_info = analytics.get_api_cost_estimate(days=cost_days)
    except Exception:
        cost_info = {"total_cost": 0.0, "by_type": {}, "daily_avg": 0.0}

    st.markdown("---")

    # --- Cost headline metrics ---
    cost_m1, cost_m2, cost_m3 = st.columns(3)
    with cost_m1:
        st.metric("Total Est. Cost", f"${cost_info.get('total_cost', 0):.2f}")
    with cost_m2:
        st.metric("Daily Average", f"${cost_info.get('daily_avg', 0):.2f}")
    with cost_m3:
        projected_monthly = cost_info.get("daily_avg", 0) * 30
        st.metric("Projected Monthly", f"${projected_monthly:.2f}")

    st.markdown("---")

    # --- API cost breakdown by type ---
    st.markdown("#### Cost Breakdown by Content Type")

    cost_by_type = cost_info.get("by_type", {})
    if cost_by_type and any(v > 0 for v in cost_by_type.values()):
        col_cost_chart, col_cost_table = st.columns([2, 1])

        with col_cost_chart:
            if PLOTLY_AVAILABLE:
                try:
                    sorted_costs = sorted(cost_by_type.items(), key=lambda x: x[1], reverse=True)
                    cost_labels = [_label(k) for k, _ in sorted_costs]
                    cost_values = [v for _, v in sorted_costs]

                    fig_cost = go.Figure(
                        go.Bar(
                            x=cost_labels,
                            y=cost_values,
                            marker_color=CHART_COLORS[: len(cost_labels)],
                            text=[f"${v:.2f}" for v in cost_values],
                            textposition="auto",
                        )
                    )
                    fig_cost.update_layout(
                        xaxis_title="Content Type",
                        yaxis_title="Cost (USD)",
                        height=350,
                        margin=dict(l=40, r=20, t=20, b=60),
                    )
                    st.plotly_chart(fig_cost, use_container_width=True)
                except Exception as cost_exc:
                    st.warning(f"Could not render cost chart: {cost_exc}")
            elif PANDAS_AVAILABLE:
                try:
                    cost_df = pd.DataFrame(
                        [{"Type": _label(k), "Cost ($)": v} for k, v in cost_by_type.items()]
                    )
                    st.bar_chart(cost_df.set_index("Type")["Cost ($)"])
                except Exception:
                    for k, v in cost_by_type.items():
                        st.write(f"- {_label(k)}: ${v:.2f}")
            else:
                for k, v in cost_by_type.items():
                    st.write(f"- {_label(k)}: ${v:.2f}")

        with col_cost_table:
            st.markdown("**Cost per Type**")
            for k, v in sorted(cost_by_type.items(), key=lambda x: x[1], reverse=True):
                pct = round((v / max(cost_info.get("total_cost", 1), 0.01)) * 100, 1)
                st.markdown(
                    f'<div class="stat-card">'
                    f"<h4>${v:.2f}</h4>"
                    f"<p>{_label(k)} ({pct}%)</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
    else:
        st.info(f"No cost data available for the last {cost_days} days.")

    st.markdown("---")

    # --- Cost trend over time ---
    st.markdown("#### Cost Trend Over Time")

    try:
        cost_timeline = analytics.get_generation_timeline(days=cost_days)
    except Exception:
        cost_timeline = []

    if cost_timeline and PANDAS_AVAILABLE:
        try:
            from app.utils.analytics import COST_PER_TYPE

            ct_df = pd.DataFrame(cost_timeline)
            type_cols = [c for c in ct_df.columns if c != "date"]

            # Compute daily cost by multiplying each type count by its unit cost
            ct_df["daily_cost"] = 0.0
            for col in type_cols:
                unit = COST_PER_TYPE.get(col, 0.03)
                ct_df["daily_cost"] += ct_df[col] * unit

            if PLOTLY_AVAILABLE:
                try:
                    fig_cost_trend = go.Figure(
                        go.Scatter(
                            x=ct_df["date"],
                            y=ct_df["daily_cost"],
                            mode="lines+markers",
                            name="Daily Cost",
                            line=dict(color="#dc3545", width=2),
                            marker=dict(size=4),
                            fill="tozeroy",
                            fillcolor="rgba(220, 53, 69, 0.1)",
                        )
                    )
                    fig_cost_trend.update_layout(
                        xaxis_title="Date",
                        yaxis_title="Est. Cost (USD)",
                        height=320,
                        margin=dict(l=40, r=20, t=20, b=40),
                    )
                    st.plotly_chart(fig_cost_trend, use_container_width=True)
                except Exception as ct_exc:
                    st.warning(f"Could not render cost trend chart: {ct_exc}")
            else:
                try:
                    st.line_chart(ct_df.set_index("date")["daily_cost"])
                except Exception:
                    st.info("Could not render cost trend.")
        except Exception as ct_exc:
            st.warning(f"Could not compute cost trend: {ct_exc}")
    elif not cost_timeline:
        st.info("No timeline data available for cost trend.")
    else:
        st.info("Install pandas to view cost trend charts.")

    st.markdown("---")

    # --- Cost per content type comparison ---
    st.markdown("#### Cost Efficiency Comparison")

    try:
        gen_vol_cost = analytics.get_generation_volume(days=cost_days)
        gen_by_type_cost = gen_vol_cost.get("by_type", {})
    except Exception:
        gen_by_type_cost = {}

    if cost_by_type and gen_by_type_cost:
        efficiency_data = []
        for ct in set(list(cost_by_type.keys()) + list(gen_by_type_cost.keys())):
            count = gen_by_type_cost.get(ct, 0)
            cost = cost_by_type.get(ct, 0.0)
            cost_per_item = round(cost / max(count, 1), 3) if count > 0 else 0.0
            efficiency_data.append(
                {
                    "Content Type": _label(ct),
                    "Items": count,
                    "Total Cost": f"${cost:.2f}",
                    "Cost/Item": f"${cost_per_item:.3f}",
                }
            )

        if efficiency_data and PANDAS_AVAILABLE:
            eff_df = pd.DataFrame(efficiency_data)
            st.dataframe(eff_df, use_container_width=True, hide_index=True)
        elif efficiency_data:
            for row in efficiency_data:
                st.write(
                    f"- {row['Content Type']}: {row['Items']} items, "
                    f"{row['Total Cost']}, {row['Cost/Item']}/item"
                )
    else:
        st.info("Not enough data for cost efficiency comparison.")

    st.markdown("---")

    # --- Batch processing stats ---
    st.markdown("#### Batch Processing Performance")

    try:
        batch_stats = analytics.get_batch_job_stats()
    except Exception:
        batch_stats = {
            "total_jobs": 0,
            "completed": 0,
            "failed": 0,
            "pending": 0,
            "running": 0,
            "avg_items_per_job": 0.0,
            "success_rate": 0.0,
        }

    if batch_stats.get("total_jobs", 0) > 0:
        batch_c1, batch_c2, batch_c3, batch_c4 = st.columns(4)
        with batch_c1:
            st.metric("Total Batch Jobs", batch_stats.get("total_jobs", 0))
        with batch_c2:
            success_rate = batch_stats.get("success_rate", 0.0)
            st.metric("Success Rate", f"{success_rate:.0%}")
        with batch_c3:
            st.metric("Avg Items/Batch", batch_stats.get("avg_items_per_job", 0.0))
        with batch_c4:
            st.metric("Failed Jobs", batch_stats.get("failed", 0))

        st.markdown("")

        # Batch status breakdown
        batch_status_col1, batch_status_col2 = st.columns(2)

        with batch_status_col1:
            st.markdown("**Job Status Breakdown**")
            if PLOTLY_AVAILABLE:
                try:
                    status_labels = ["Completed", "Failed", "Pending", "Running"]
                    status_values = [
                        batch_stats.get("completed", 0),
                        batch_stats.get("failed", 0),
                        batch_stats.get("pending", 0),
                        batch_stats.get("running", 0),
                    ]
                    status_colors = ["#28a745", "#dc3545", "#ffc107", "#17a2b8"]

                    # Filter out zero values
                    filtered = [
                        (l, v, c)
                        for l, v, c in zip(status_labels, status_values, status_colors)
                        if v > 0
                    ]
                    if filtered:
                        f_labels, f_values, f_colors = zip(*filtered)
                        fig_batch = go.Figure(
                            go.Pie(
                                labels=list(f_labels),
                                values=list(f_values),
                                hole=0.4,
                                marker=dict(colors=list(f_colors)),
                                textinfo="label+value",
                            )
                        )
                        fig_batch.update_layout(
                            height=280,
                            margin=dict(l=20, r=20, t=20, b=20),
                            showlegend=False,
                        )
                        st.plotly_chart(fig_batch, use_container_width=True)
                except Exception:
                    for lbl, val in zip(status_labels, status_values):
                        if val > 0:
                            st.write(f"- {lbl}: {val}")
            else:
                st.write(f"- Completed: {batch_stats.get('completed', 0)}")
                st.write(f"- Failed: {batch_stats.get('failed', 0)}")
                st.write(f"- Pending: {batch_stats.get('pending', 0)}")
                st.write(f"- Running: {batch_stats.get('running', 0)}")

        with batch_status_col2:
            st.markdown("**Batch Summary**")
            st.markdown(
                f'<div class="brand-card">'
                f"<p><strong>Total Jobs:</strong> {batch_stats.get('total_jobs', 0)}</p>"
                f"<p><strong>Completed:</strong> {batch_stats.get('completed', 0)}</p>"
                f"<p><strong>Failed:</strong> {batch_stats.get('failed', 0)}</p>"
                f"<p><strong>Success Rate:</strong> {success_rate:.0%}</p>"
                f"<p><strong>Avg Items/Job:</strong> {batch_stats.get('avg_items_per_job', 0.0)}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No batch processing jobs have been run yet.")

    st.markdown("---")

    # --- Performance metrics: avg generation time ---
    st.markdown("#### Generation Performance Metrics")

    try:
        perf_avg_time = analytics.get_avg_generation_time()
    except Exception:
        perf_avg_time = {}

    if perf_avg_time and any(v > 0 for v in perf_avg_time.values()):
        active_types = {k: v for k, v in perf_avg_time.items() if v > 0}

        perf_cols = st.columns(min(len(active_types), 5))
        for idx, (ct, seconds) in enumerate(
            sorted(active_types.items(), key=lambda x: x[1], reverse=True)
        ):
            if idx < len(perf_cols):
                with perf_cols[idx]:
                    _stat_card(f"{seconds:.1f}s", f"{_label(ct)} Avg Time")

        st.markdown("")

        if PLOTLY_AVAILABLE and len(active_types) > 1:
            try:
                sorted_perf = sorted(active_types.items(), key=lambda x: x[1])
                perf_labels = [_label(k) for k, _ in sorted_perf]
                perf_values = [v for _, v in sorted_perf]

                fig_perf = go.Figure(
                    go.Bar(
                        y=perf_labels,
                        x=perf_values,
                        orientation="h",
                        marker_color=CHART_COLORS[: len(perf_labels)],
                        text=[f"{v:.1f}s" for v in perf_values],
                        textposition="auto",
                    )
                )
                fig_perf.update_layout(
                    xaxis_title="Avg Generation Time (seconds)",
                    height=max(200, len(active_types) * 50),
                    margin=dict(l=130, r=20, t=20, b=40),
                )
                st.plotly_chart(fig_perf, use_container_width=True)
            except Exception:
                pass
    else:
        st.info(
            "No generation time data available yet. "
            "Generate content to start collecting performance metrics."
        )


# =========================================================================
# TAB 5 -- STORAGE & SYSTEM
# =========================================================================
with tab_system:
    st.markdown(
        '<div class="section-header"><h3>Storage & System</h3></div>',
        unsafe_allow_html=True,
    )

    # --- Storage usage ---
    st.markdown("#### Storage Usage")

    try:
        storage = analytics.get_storage_usage()
    except Exception:
        storage = {"total_bytes": 0, "total_mb": 0.0, "by_dir": {}}

    total_mb = storage.get("total_mb", 0.0)
    by_dir = storage.get("by_dir", {})

    # Storage headline
    stor_m1, stor_m2, stor_m3 = st.columns(3)
    with stor_m1:
        if total_mb >= 1024:
            st.metric("Total Storage", f"{total_mb / 1024:.2f} GB")
        else:
            st.metric("Total Storage", f"{total_mb:.2f} MB")
    with stor_m2:
        st.metric("Categories", len(by_dir))
    with stor_m3:
        largest_dir = max(by_dir.items(), key=lambda x: x[1])[0] if by_dir else "N/A"
        st.metric("Largest Category", _label(largest_dir) if largest_dir != "N/A" else "N/A")

    st.markdown("")

    # Storage by category bar chart
    if by_dir:
        col_stor_chart, col_stor_table = st.columns([2, 1])

        with col_stor_chart:
            st.markdown("**Storage by Category**")
            if PLOTLY_AVAILABLE:
                try:
                    sorted_dirs = sorted(by_dir.items(), key=lambda x: x[1], reverse=True)
                    dir_labels = [_label(k) for k, _ in sorted_dirs]
                    dir_values = [v for _, v in sorted_dirs]

                    fig_stor = go.Figure(
                        go.Bar(
                            x=dir_labels,
                            y=dir_values,
                            marker_color=CHART_COLORS[: len(dir_labels)],
                            text=[f"{v:.2f} MB" for v in dir_values],
                            textposition="auto",
                        )
                    )
                    fig_stor.update_layout(
                        xaxis_title="Category",
                        yaxis_title="Size (MB)",
                        height=350,
                        margin=dict(l=40, r=20, t=20, b=60),
                    )
                    st.plotly_chart(fig_stor, use_container_width=True)
                except Exception as stor_exc:
                    st.warning(f"Could not render storage chart: {stor_exc}")
            elif PANDAS_AVAILABLE:
                try:
                    stor_df = pd.DataFrame(
                        [{"Category": _label(k), "MB": v} for k, v in by_dir.items()]
                    )
                    st.bar_chart(stor_df.set_index("Category")["MB"])
                except Exception:
                    for k, v in by_dir.items():
                        st.write(f"- {_label(k)}: {v:.2f} MB")
            else:
                for k, v in by_dir.items():
                    st.write(f"- {_label(k)}: {v:.2f} MB")

        with col_stor_table:
            st.markdown("**Storage Breakdown**")
            for k, v in sorted(by_dir.items(), key=lambda x: x[1], reverse=True):
                pct = round((v / max(total_mb, 0.01)) * 100, 1) if total_mb > 0 else 0.0
                st.markdown(
                    f'<div class="stat-card">'
                    f"<h4>{v:.2f} MB</h4>"
                    f"<p>{_label(k)} ({pct}%)</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
    else:
        st.info("No storage data available. Output directories may be empty.")

    st.markdown("---")

    # --- Library composition ---
    st.markdown("#### Library Composition")

    try:
        lib_comp = analytics.get_library_stats()
    except Exception:
        lib_comp = {"total_items": 0, "approved": 0, "pending": 0, "by_category": {}, "avg_rating": 0.0, "top_downloaded": []}

    by_category = lib_comp.get("by_category", {})

    if by_category:
        col_lib_chart, col_lib_info = st.columns([2, 1])

        with col_lib_chart:
            if PLOTLY_AVAILABLE:
                try:
                    cat_labels = [str(k) for k in by_category.keys()]
                    cat_values = list(by_category.values())

                    fig_lib = go.Figure(
                        go.Pie(
                            labels=cat_labels,
                            values=cat_values,
                            hole=0.4,
                            textinfo="label+percent",
                            marker=dict(colors=CHART_COLORS[: len(cat_labels)]),
                        )
                    )
                    fig_lib.update_layout(
                        height=350,
                        margin=dict(l=20, r=20, t=30, b=20),
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.15,
                            xanchor="center",
                            x=0.5,
                        ),
                    )
                    st.plotly_chart(fig_lib, use_container_width=True)
                except Exception as lib_exc:
                    st.warning(f"Could not render library chart: {lib_exc}")
            elif PANDAS_AVAILABLE:
                try:
                    cat_df = pd.DataFrame(
                        [{"Category": k, "Count": v} for k, v in by_category.items()]
                    )
                    st.bar_chart(cat_df.set_index("Category")["Count"])
                except Exception:
                    for k, v in by_category.items():
                        st.write(f"- {k}: {v}")
            else:
                for k, v in by_category.items():
                    st.write(f"- {k}: {v}")

        with col_lib_info:
            st.markdown("**Library Summary**")
            st.markdown(
                f'<div class="brand-card">'
                f"<p><strong>Total Items:</strong> {lib_comp.get('total_items', 0)}</p>"
                f"<p><strong>Approved:</strong> {lib_comp.get('approved', 0)}</p>"
                f"<p><strong>Pending:</strong> {lib_comp.get('pending', 0)}</p>"
                f"<p><strong>Avg Rating:</strong> {lib_comp.get('avg_rating', 0.0):.1f} / 5.0</p>"
                f"<p><strong>Categories:</strong> {len(by_category)}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

            # Top downloaded
            top_dl = lib_comp.get("top_downloaded", [])
            if top_dl:
                st.markdown("**Most Downloaded**")
                for item in top_dl[:5]:
                    title = item.get("title", "Untitled")
                    dl_count = item.get("download_count", 0)
                    st.write(f"- {title} ({dl_count} downloads)")
    else:
        st.info("No library items available for composition analysis.")

    st.markdown("---")

    # --- Content freshness analysis ---
    st.markdown("#### Content Freshness")

    try:
        session = get_session()
        from sqlalchemy import func as sa_func

        # Total content count
        total_content = session.query(GeneratedContent).count()

        # Content in the last 7 days
        cutoff_7 = datetime.utcnow() - timedelta(days=7)
        recent_7 = (
            session.query(sa_func.count(GeneratedContent.id))
            .filter(GeneratedContent.generated_at >= cutoff_7)
            .scalar()
        ) or 0

        # Content in the last 30 days
        cutoff_30 = datetime.utcnow() - timedelta(days=30)
        recent_30 = (
            session.query(sa_func.count(GeneratedContent.id))
            .filter(GeneratedContent.generated_at >= cutoff_30)
            .scalar()
        ) or 0

        # Content older than 90 days
        cutoff_90 = datetime.utcnow() - timedelta(days=90)
        older_90 = (
            session.query(sa_func.count(GeneratedContent.id))
            .filter(GeneratedContent.generated_at < cutoff_90)
            .scalar()
        ) or 0

        # Most recent generation date
        latest_gen = (
            session.query(sa_func.max(GeneratedContent.generated_at)).scalar()
        )

        session.close()

        fresh_c1, fresh_c2, fresh_c3, fresh_c4 = st.columns(4)
        with fresh_c1:
            st.metric("Total Content", total_content)
        with fresh_c2:
            st.metric("Last 7 Days", recent_7)
        with fresh_c3:
            st.metric("Last 30 Days", recent_30)
        with fresh_c4:
            st.metric("Older than 90 Days", older_90)

        st.markdown("")

        if total_content > 0:
            freshness_data = {
                "Last 7 Days": recent_7,
                "8-30 Days": recent_30 - recent_7,
                "31-90 Days": (total_content - older_90) - recent_30,
                "Over 90 Days": older_90,
            }

            if PLOTLY_AVAILABLE:
                try:
                    fresh_labels = list(freshness_data.keys())
                    fresh_values = list(freshness_data.values())
                    fresh_colors = ["#28a745", "#17a2b8", "#ffc107", "#dc3545"]

                    # Filter out zero values
                    filtered_fresh = [
                        (l, v, c)
                        for l, v, c in zip(fresh_labels, fresh_values, fresh_colors)
                        if v > 0
                    ]

                    if filtered_fresh:
                        ff_labels, ff_values, ff_colors = zip(*filtered_fresh)
                        fig_fresh = go.Figure(
                            go.Pie(
                                labels=list(ff_labels),
                                values=list(ff_values),
                                hole=0.45,
                                marker=dict(colors=list(ff_colors)),
                                textinfo="label+percent+value",
                            )
                        )
                        fig_fresh.update_layout(
                            height=300,
                            margin=dict(l=20, r=20, t=20, b=20),
                            showlegend=True,
                        )
                        st.plotly_chart(fig_fresh, use_container_width=True)
                except Exception:
                    for lbl, val in freshness_data.items():
                        st.write(f"- {lbl}: {val} items")
            else:
                for lbl, val in freshness_data.items():
                    st.write(f"- {lbl}: {val} items")

            if latest_gen:
                st.caption(f"Most recent generation: {latest_gen.strftime('%Y-%m-%d %H:%M UTC')}")
        else:
            st.info("No content has been generated yet.")
    except Exception as fresh_exc:
        st.warning(f"Could not load content freshness data: {fresh_exc}")

    st.markdown("---")

    # --- System health indicators ---
    st.markdown("#### System Health")

    health_c1, health_c2, health_c3, health_c4 = st.columns(4)

    with health_c1:
        db_ok = st.session_state.get("db_ok", False)
        if db_ok:
            st.success("Database: Connected")
        else:
            st.error(f"Database: Error - {st.session_state.get('db_error', 'Unknown')}")

    with health_c2:
        if ANALYTICS_AVAILABLE:
            st.success("Analytics Engine: Active")
        else:
            st.warning("Analytics Engine: Unavailable")

    with health_c3:
        if FEEDBACK_AVAILABLE and feedback_loop is not None:
            st.success("Feedback Loop: Active")
        elif FEEDBACK_AVAILABLE:
            st.warning("Feedback Loop: Import OK, Init Failed")
        else:
            st.warning("Feedback Loop: Unavailable")

    with health_c4:
        if PLOTLY_AVAILABLE:
            st.success("Plotly Charts: Available")
        else:
            st.info("Plotly Charts: Using Fallbacks")

    st.markdown("")

    # Additional system checks
    sys_c1, sys_c2 = st.columns(2)

    with sys_c1:
        st.markdown("**Module Availability**")
        modules = {
            "Analytics Engine": ANALYTICS_AVAILABLE,
            "Feedback Loop": FEEDBACK_AVAILABLE,
            "Plotly Charting": PLOTLY_AVAILABLE,
            "Pandas Data": PANDAS_AVAILABLE,
        }
        for mod_name, available in modules.items():
            icon = "\u2705" if available else "\u274c"
            st.markdown(f"{icon} {mod_name}")

    with sys_c2:
        st.markdown("**Output Directories**")
        try:
            from app.config import (
                PRESENTATIONS_DIR,
                DOCUMENTS_DIR,
                TRAINING_DIR,
                VISUALS_DIR,
                EXPORTS_DIR,
            )

            dir_checks = {
                "Presentations": PRESENTATIONS_DIR,
                "Documents": DOCUMENTS_DIR,
                "Training": TRAINING_DIR,
                "Visuals": VISUALS_DIR,
                "Exports": EXPORTS_DIR,
            }
            for dir_name, dir_path in dir_checks.items():
                exists = dir_path.exists() if dir_path else False
                icon = "\u2705" if exists else "\u274c"
                st.markdown(f"{icon} {dir_name}: `{dir_path}`")
        except Exception:
            st.info("Could not check output directories.")

    st.markdown("---")

    # --- Export analytics data ---
    st.markdown("#### Export Analytics Data")

    st.write(
        "Download a comprehensive JSON export of all analytics data for "
        "external analysis or reporting."
    )

    if st.button("Generate Analytics Export", key="export_analytics", use_container_width=False):
        try:
            with st.spinner("Collecting analytics data..."):
                export_data = {
                    "export_timestamp": datetime.utcnow().isoformat(),
                    "generation_volume_30d": analytics.get_generation_volume(days=30),
                    "generation_volume_90d": analytics.get_generation_volume(days=90),
                    "generation_timeline_30d": analytics.get_generation_timeline(days=30),
                    "avg_generation_time": analytics.get_avg_generation_time(),
                    "api_cost_30d": analytics.get_api_cost_estimate(days=30),
                    "api_cost_90d": analytics.get_api_cost_estimate(days=90),
                    "template_usage": analytics.get_template_usage(),
                    "library_stats": analytics.get_library_stats(),
                    "rating_distribution": analytics.get_rating_distribution(),
                    "time_saved": analytics.get_time_saved_estimate(),
                    "storage_usage": analytics.get_storage_usage(),
                    "batch_job_stats": analytics.get_batch_job_stats(),
                    "content_type_breakdown": analytics.get_content_type_breakdown(),
                }

                # Add feedback data if available
                if feedback_loop is not None:
                    try:
                        export_data["feedback_pattern_summary"] = (
                            feedback_loop.get_pattern_summary()
                        )
                        export_data["feedback_has_patterns"] = feedback_loop.has_patterns()
                    except Exception:
                        export_data["feedback_pattern_summary"] = {}
                        export_data["feedback_has_patterns"] = False

                export_json = json.dumps(export_data, indent=2, default=str)

            st.download_button(
                label="Download Analytics JSON",
                data=export_json,
                file_name=f"analytics_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=False,
            )
            st.success("Analytics export generated successfully.")
        except Exception as export_exc:
            st.error(f"Failed to generate analytics export: {export_exc}")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption(
    "Analytics data is computed from the local SQLite database and output "
    "directory file sizes. Cost estimates are approximate and based on "
    "per-type unit costs. Refresh the page to update all metrics."
)
