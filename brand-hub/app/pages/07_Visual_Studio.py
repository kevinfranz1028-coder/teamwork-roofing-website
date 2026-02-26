"""
Brand Intelligence Content Hub - Visual Studio

Interactive workspace for generating diagrams, flowcharts, mind maps,
infographics, and other visuals from text descriptions using Napkin AI.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Imports with graceful degradation
# ---------------------------------------------------------------------------

try:
    from app.config import (
        BRAND_ASSETS_DIR,
        VISUALS_DIR,
        CACHE_DIR,
        get_env,
    )
except ImportError:
    BRAND_ASSETS_DIR = Path("brand_assets")
    VISUALS_DIR = Path("output/visuals")
    CACHE_DIR = Path("data/cache")

    def get_env(key: str) -> str:
        return os.getenv(key, "")

try:
    from app.database.models import get_session, GeneratedContent, ContentLibraryItem
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

try:
    from app.integrations.napkin_client import (
        NapkinClient,
        VISUAL_TYPES,
        COLOR_MODES,
        OUTPUT_FORMATS,
        ORIENTATIONS,
    )
    NAPKIN_AVAILABLE = True
except ImportError:
    NAPKIN_AVAILABLE = False
    VISUAL_TYPES = {
        "flowchart": {"name": "Flowchart", "description": "Process and decision flow diagrams", "best_for": ["Processes", "Workflows", "Decision Trees"]},
        "mind_map": {"name": "Mind Map", "description": "Hierarchical idea and concept maps", "best_for": ["Brainstorming", "Topic Exploration", "Planning"]},
        "timeline": {"name": "Timeline", "description": "Chronological event sequences", "best_for": ["Project Plans", "History", "Roadmaps"]},
        "org_chart": {"name": "Org Chart", "description": "Organizational hierarchy diagrams", "best_for": ["Team Structure", "Reporting Lines", "Departments"]},
        "process_diagram": {"name": "Process Diagram", "description": "Step-by-step process visualizations", "best_for": ["SOPs", "Manufacturing", "Onboarding"]},
        "infographic": {"name": "Infographic", "description": "Data-rich visual summaries", "best_for": ["Statistics", "Reports", "Marketing"]},
        "comparison_chart": {"name": "Comparison Chart", "description": "Side-by-side comparison visuals", "best_for": ["Product Comparison", "Pros/Cons", "Feature Matrix"]},
    }
    COLOR_MODES = {
        "brand": "Use brand colors from your brand configuration",
        "light": "Light background with dark accents",
        "dark": "Dark background with light accents",
        "colorful": "Vibrant multi-color palette",
        "monochrome": "Single color with varying shades",
    }
    OUTPUT_FORMATS = ["png", "svg", "pptx"]
    ORIENTATIONS = ["landscape", "portrait", "square"]

try:
    from app.generators.visual_gen import (
        VisualPipeline,
        VisualContentAnalyzer,
    )
    VISUAL_GEN_AVAILABLE = True
except ImportError:
    VISUAL_GEN_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Visual Studio", layout="wide")

st.markdown("""<style>
.visual-card { border: 1px solid #e0e0e0; border-radius: 10px; padding: 16px; margin: 8px 0; background: white; }
.visual-type-badge { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; display: inline-block; }
.vt-flowchart { background: #e8f0fe; color: #1a73e8; }
.vt-mind_map { background: #e6f4ea; color: #137333; }
.vt-timeline { background: #fef7e0; color: #b06000; }
.vt-org_chart { background: #fce8e6; color: #c5221f; }
.vt-process_diagram { background: #f3e8fd; color: #7627bb; }
.vt-infographic { background: #e8eaed; color: #5f6368; }
.vt-comparison_chart { background: #fce4ec; color: #c62828; }
.gallery-img { border-radius: 8px; border: 1px solid #ddd; }
.stat-box { background: #f8f9fa; border-radius: 8px; padding: 16px; text-align: center; border: 1px solid #e0e0e0; }
.stProgress > div > div > div > div { background-color: #0066cc; }
</style>""", unsafe_allow_html=True)

st.title("Visual Studio")
st.markdown("Generate diagrams, flowcharts, mind maps, and infographics from text descriptions")

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

_SESSION_DEFAULTS = {
    "vs_generated_visual": None,
    "vs_generated_visuals_batch": [],
    "vs_enhanced_description": None,
    "vs_analysis_results": None,
    "vs_analysis_generated": [],
    "vs_batch_items": [],
    "vs_batch_results": [],
    "vs_default_style": "Professional",
    "vs_default_color_mode": "brand",
    "vs_default_format": "png",
    "vs_default_orientation": "landscape",
    "vs_generation_count": 0,
}

for key, default in _SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STYLE_OPTIONS = ["Professional", "Minimal", "Playful", "Technical"]
CONTENT_TYPES = ["Presentation", "Training Material", "Report", "General"]

PLACEHOLDER_TEXTS = {
    "flowchart": "Describe the process steps, decisions, and flow...\n\nExample: User visits website -> Clicks sign up -> Fills form -> If valid, create account -> Send welcome email. If invalid, show error -> Return to form.",
    "mind_map": "Describe the central topic and branches...\n\nExample: Central topic: Digital Marketing. Branches: SEO (keywords, backlinks, technical), Social Media (Facebook, Instagram, LinkedIn), Email Marketing (newsletters, automation, segmentation).",
    "timeline": "Describe events in chronological order...\n\nExample: Q1 2025: Project kickoff and requirements gathering. Q2 2025: Design phase and prototyping. Q3 2025: Development and testing. Q4 2025: Launch and post-launch support.",
    "org_chart": "Describe the organizational structure...\n\nExample: CEO at top. Reports: CTO (Engineering, QA, DevOps), CFO (Finance, Accounting), CMO (Marketing, Sales, PR). Engineering team: Frontend, Backend, Mobile.",
    "process_diagram": "Describe the step-by-step process...\n\nExample: Step 1: Receive customer order. Step 2: Verify inventory. Step 3: Process payment. Step 4: Pick and pack items. Step 5: Ship order. Step 6: Send tracking notification.",
    "infographic": "Describe the data, statistics, or information to visualize...\n\nExample: Company growth in 2025: Revenue increased 45% to $2.5M. Customer base grew from 500 to 1,200. Employee count doubled to 50. Launched 3 new products. Expanded to 5 new markets.",
    "comparison_chart": "Describe the items to compare and their attributes...\n\nExample: Compare Plan A vs Plan B vs Plan C. Features: Storage (10GB, 50GB, Unlimited), Users (1, 5, Unlimited), Support (Email, Priority, Dedicated), Price ($9, $29, $99).",
}

# ---------------------------------------------------------------------------
# Helper: render visual type badge
# ---------------------------------------------------------------------------

def render_type_badge(visual_type: str) -> str:
    """Return an HTML badge for a visual type."""
    info = VISUAL_TYPES.get(visual_type, {})
    name = info.get("name", visual_type.replace("_", " ").title())
    css_class = f"vt-{visual_type}" if visual_type in VISUAL_TYPES else "vt-infographic"
    return f'<span class="visual-type-badge {css_class}">{name}</span>'


def render_priority_badge(priority: str) -> str:
    """Return an HTML badge for priority level."""
    colors = {
        "high": ("background: #fce8e6; color: #c5221f;", "High"),
        "medium": ("background: #fef7e0; color: #b06000;", "Medium"),
        "low": ("background: #e6f4ea; color: #137333;", "Low"),
    }
    style, label = colors.get(priority.lower(), ("background: #e8eaed; color: #5f6368;", priority))
    return f'<span style="{style} padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;">{label}</span>'


# ---------------------------------------------------------------------------
# Helper: load brand config
# ---------------------------------------------------------------------------

def load_brand_config() -> dict:
    """Load brand_config.json from brand_assets directory."""
    config_path = BRAND_ASSETS_DIR / "brand_config.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as exc:
            logger.warning("Failed to load brand config: %s", exc)
    return {}


# ---------------------------------------------------------------------------
# Helper: initialise pipeline
# ---------------------------------------------------------------------------

@st.cache_resource
def get_visual_pipeline():
    """Return a cached VisualPipeline instance."""
    if not VISUAL_GEN_AVAILABLE:
        return None
    try:
        return VisualPipeline()
    except Exception as exc:
        logger.error("Failed to initialise VisualPipeline: %s", exc)
        return None


@st.cache_resource
def get_content_analyzer():
    """Return a cached VisualContentAnalyzer instance."""
    if not VISUAL_GEN_AVAILABLE:
        return None
    try:
        return VisualContentAnalyzer()
    except Exception as exc:
        logger.error("Failed to initialise VisualContentAnalyzer: %s", exc)
        return None


@st.cache_resource
def get_napkin_client():
    """Return a cached NapkinClient instance."""
    if not NAPKIN_AVAILABLE:
        return None
    try:
        return NapkinClient()
    except Exception as exc:
        logger.error("Failed to initialise NapkinClient: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Helper: record generation in database
# ---------------------------------------------------------------------------

def record_generation(title: str, visual_type: str, output_path: str, fmt: str, gen_time: float):
    """Record a visual generation in the GeneratedContent table."""
    if not DB_AVAILABLE:
        return None
    try:
        session = get_session()
        record = GeneratedContent(
            title=title,
            content_type=f"visual_{visual_type}",
            input_summary=f"Visual type: {visual_type}, Format: {fmt}",
            output_path=str(output_path) if output_path else None,
            format=fmt,
            generation_time_seconds=gen_time,
        )
        session.add(record)
        session.commit()
        record_id = record.id
        session.close()
        return record_id
    except Exception as exc:
        logger.error("Failed to record generation: %s", exc)
        return None


def add_to_library(title: str, description: str, tags: str, category: str, gen_content_id: int = None):
    """Add a visual to the content library."""
    if not DB_AVAILABLE:
        st.warning("Database not available. Cannot add to library.")
        return False
    try:
        session = get_session()
        item = ContentLibraryItem(
            generated_content_id=gen_content_id,
            title=title,
            description=description,
            tags=tags,
            category=category,
            is_approved=False,
        )
        session.add(item)
        session.commit()
        session.close()
        return True
    except Exception as exc:
        logger.error("Failed to add to library: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Helper: file scanning for gallery
# ---------------------------------------------------------------------------

def scan_visuals_directory() -> list[dict]:
    """Scan the visuals output directory and return metadata for each file."""
    visuals = []
    visuals_path = Path(VISUALS_DIR)
    if not visuals_path.exists():
        return visuals
    for fp in sorted(visuals_path.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if fp.suffix.lower() in (".png", ".svg", ".pptx", ".jpg", ".jpeg"):
            stat = fp.stat()
            # Try to infer visual type from filename
            vtype = "infographic"
            for t in VISUAL_TYPES:
                if t in fp.stem.lower():
                    vtype = t
                    break
            visuals.append({
                "path": str(fp),
                "filename": fp.name,
                "type": vtype,
                "format": fp.suffix.lstrip(".").lower(),
                "size_bytes": stat.st_size,
                "size_display": f"{stat.st_size / 1024:.1f} KB" if stat.st_size < 1024 * 1024 else f"{stat.st_size / (1024 * 1024):.1f} MB",
                "created": datetime.fromtimestamp(stat.st_mtime),
            })
    return visuals


def format_file_size(total_bytes: int) -> str:
    """Format bytes to human-readable size."""
    if total_bytes < 1024:
        return f"{total_bytes} B"
    elif total_bytes < 1024 * 1024:
        return f"{total_bytes / 1024:.1f} KB"
    else:
        return f"{total_bytes / (1024 * 1024):.1f} MB"


# ---------------------------------------------------------------------------
# Helper: enhance description with AI
# ---------------------------------------------------------------------------

def enhance_description_with_ai(description: str, visual_type: str, context: str = "") -> str:
    """Use VisualContentAnalyzer or Anthropic directly to enhance description."""
    analyzer = get_content_analyzer()
    if analyzer:
        try:
            return analyzer.generate_visual_description(description, visual_type, context)
        except Exception as exc:
            logger.warning("Analyzer enhancement failed: %s", exc)

    if ANTHROPIC_AVAILABLE:
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            type_info = VISUAL_TYPES.get(visual_type, {})
            type_name = type_info.get("name", visual_type)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": (
                        f"You are a visual design expert. Enhance the following description for a {type_name} visual. "
                        f"Make it more detailed, structured, and optimized for automated visual generation. "
                        f"Add clear hierarchy, labels, and relationships where appropriate. "
                        f"Return ONLY the enhanced description, no commentary.\n\n"
                        f"Original description:\n{description}"
                    ),
                }],
            )
            return response.content[0].text
        except Exception as exc:
            logger.warning("Anthropic enhancement failed: %s", exc)
    return description


# ===========================================================================
# TABS
# ===========================================================================

tab_generate, tab_analyzer, tab_batch, tab_gallery, tab_settings = st.tabs([
    "Generate Visual",
    "Content Analyzer",
    "Batch Generation",
    "Gallery",
    "Cache & Settings",
])

# ===========================================================================
# TAB 1: Generate Visual
# ===========================================================================

with tab_generate:
    st.subheader("Create a New Visual")

    # --- Visual Type Selector Grid ---
    st.markdown("**Select Visual Type**")
    type_keys = list(VISUAL_TYPES.keys())
    cols_per_row = 4
    selected_type = st.session_state.get("vs_selected_type", type_keys[0])

    type_cols = st.columns(cols_per_row)
    for idx, vtype in enumerate(type_keys):
        info = VISUAL_TYPES[vtype]
        col = type_cols[idx % cols_per_row]
        with col:
            best_for_tags = " | ".join(info.get("best_for", [])[:3])
            st.markdown(
                f'<div class="visual-card">'
                f'{render_type_badge(vtype)}'
                f'<br><small style="color: #666;">{info.get("description", "")}</small>'
                f'<br><small style="color: #999;">Best for: {best_for_tags}</small>'
                f'</div>',
                unsafe_allow_html=True,
            )

    selected_type = st.selectbox(
        "Visual Type",
        options=type_keys,
        format_func=lambda x: VISUAL_TYPES[x]["name"],
        index=type_keys.index(selected_type) if selected_type in type_keys else 0,
        key="vs_type_selector",
    )
    st.session_state["vs_selected_type"] = selected_type

    # --- Layout: Main content and configuration sidebar ---
    gen_col_main, gen_col_config = st.columns([3, 1])

    with gen_col_config:
        st.markdown("**Configuration**")

        style_choice = st.selectbox(
            "Style",
            STYLE_OPTIONS,
            index=STYLE_OPTIONS.index(st.session_state.vs_default_style),
            key="vs_style_select",
        )

        color_mode_keys = list(COLOR_MODES.keys())
        color_choice = st.selectbox(
            "Color Mode",
            color_mode_keys,
            format_func=lambda x: x.title(),
            index=color_mode_keys.index(st.session_state.vs_default_color_mode) if st.session_state.vs_default_color_mode in color_mode_keys else 0,
            key="vs_color_select",
        )
        st.caption(COLOR_MODES.get(color_choice, ""))

        format_choice = st.selectbox(
            "Output Format",
            [f.upper() for f in OUTPUT_FORMATS],
            index=OUTPUT_FORMATS.index(st.session_state.vs_default_format) if st.session_state.vs_default_format in OUTPUT_FORMATS else 0,
            key="vs_format_select",
        )
        format_lower = format_choice.lower()

        orientation_choice = st.selectbox(
            "Orientation",
            [o.title() for o in ORIENTATIONS],
            index=0,
            key="vs_orientation_select",
        )

    with gen_col_main:
        # --- Text Input ---
        placeholder = PLACEHOLDER_TEXTS.get(selected_type, "Describe the visual you want to generate...")
        description_input = st.text_area(
            "Visual Description",
            height=180,
            placeholder=placeholder,
            key="vs_description_input",
        )

        # --- Enhance with AI ---
        enhance_col1, enhance_col2 = st.columns([1, 3])
        with enhance_col1:
            enhance_clicked = st.button("Enhance with AI", key="vs_enhance_btn", type="secondary")

        if enhance_clicked and description_input.strip():
            with st.spinner("Enhancing description with AI..."):
                enhanced = enhance_description_with_ai(description_input, selected_type)
                st.session_state.vs_enhanced_description = enhanced

        if st.session_state.vs_enhanced_description:
            st.markdown("**Enhanced Description** (editable):")
            enhanced_text = st.text_area(
                "Enhanced Description",
                value=st.session_state.vs_enhanced_description,
                height=160,
                key="vs_enhanced_text",
                label_visibility="collapsed",
            )
        else:
            enhanced_text = None

        # --- Generate Button ---
        final_description = enhanced_text if enhanced_text else description_input

        st.divider()
        gen_col_a, gen_col_b, gen_col_c = st.columns([1, 1, 2])
        with gen_col_a:
            generate_clicked = st.button(
                "Generate Visual",
                type="primary",
                key="vs_generate_btn",
                disabled=not final_description.strip() if final_description else True,
            )
        with gen_col_b:
            if st.session_state.vs_generated_visual:
                regenerate_clicked = st.button("Regenerate", key="vs_regenerate_btn")
            else:
                regenerate_clicked = False

        if generate_clicked or regenerate_clicked:
            if not final_description or not final_description.strip():
                st.error("Please enter a description for the visual.")
            else:
                pipeline = get_visual_pipeline()
                if not pipeline and not NAPKIN_AVAILABLE:
                    st.error(
                        "Visual generation is not available. Please ensure the Napkin AI integration "
                        "and Visual Pipeline modules are properly installed and configured."
                    )
                else:
                    with st.spinner("Generating your visual... This may take a moment."):
                        start_time = time.time()
                        progress_bar = st.progress(0)
                        try:
                            # Ensure output directory exists
                            Path(VISUALS_DIR).mkdir(parents=True, exist_ok=True)

                            save_filename = f"{selected_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_lower}"
                            save_path = Path(VISUALS_DIR) / save_filename

                            progress_bar.progress(20)

                            if pipeline:
                                result = pipeline.generate_visual(
                                    description=final_description,
                                    visual_type=selected_type,
                                    style=style_choice.lower(),
                                    color_mode=color_choice,
                                    output_format=format_lower,
                                    save_path=str(save_path),
                                )
                            else:
                                napkin = get_napkin_client()
                                result = napkin.generate_visual(
                                    description=final_description,
                                    visual_type=selected_type,
                                    style=style_choice.lower(),
                                    color_mode=color_choice,
                                    output_format=format_lower,
                                    orientation=orientation_choice.lower(),
                                    save_path=str(save_path),
                                )

                            progress_bar.progress(80)
                            gen_time = time.time() - start_time

                            st.session_state.vs_generated_visual = {
                                "result": result,
                                "path": str(save_path),
                                "type": selected_type,
                                "format": format_lower,
                                "description": final_description,
                                "style": style_choice,
                                "color_mode": color_choice,
                                "gen_time": gen_time,
                            }
                            st.session_state.vs_generation_count += 1

                            # Record in database
                            record_id = record_generation(
                                title=f"{VISUAL_TYPES[selected_type]['name']} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                                visual_type=selected_type,
                                output_path=str(save_path),
                                fmt=format_lower,
                                gen_time=gen_time,
                            )
                            if record_id:
                                st.session_state.vs_generated_visual["db_id"] = record_id

                            progress_bar.progress(100)
                            st.success(f"Visual generated in {gen_time:.1f}s!")

                        except Exception as exc:
                            progress_bar.progress(100)
                            st.error(f"Generation failed: {exc}")
                            logger.error("Visual generation failed: %s", exc)

        # --- Display Generated Visual ---
        if st.session_state.vs_generated_visual:
            st.divider()
            st.markdown("**Generated Visual**")
            vis = st.session_state.vs_generated_visual
            vis_path = Path(vis["path"])

            display_col, info_col = st.columns([3, 1])

            with display_col:
                if vis["format"] in ("png", "svg", "jpg", "jpeg") and vis_path.exists():
                    try:
                        st.image(str(vis_path), use_container_width=True)
                    except Exception:
                        st.info(f"Visual saved at: `{vis_path}`")
                elif vis["format"] == "pptx":
                    st.info(f"PowerPoint visual saved at: `{vis_path}`. Use the download button to get the file.")
                else:
                    st.info(f"Visual saved at: `{vis_path}`")

            with info_col:
                st.markdown(render_type_badge(vis["type"]), unsafe_allow_html=True)
                st.caption(f"Style: {vis['style']}")
                st.caption(f"Color: {vis['color_mode'].title()}")
                st.caption(f"Format: {vis['format'].upper()}")
                st.caption(f"Generated in {vis['gen_time']:.1f}s")

                # Download button
                if vis_path.exists():
                    with open(vis_path, "rb") as f:
                        mime_map = {"png": "image/png", "svg": "image/svg+xml", "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation", "jpg": "image/jpeg"}
                        st.download_button(
                            "Download",
                            data=f.read(),
                            file_name=vis_path.name,
                            mime=mime_map.get(vis["format"], "application/octet-stream"),
                            key="vs_download_btn",
                        )

                # Add to Library button
                if st.button("Add to Library", key="vs_add_to_lib_btn"):
                    success = add_to_library(
                        title=f"{VISUAL_TYPES[vis['type']]['name']} Visual",
                        description=vis["description"][:200],
                        tags=f"{vis['type']},{vis['style']},{vis['format']}",
                        category="visual",
                        gen_content_id=vis.get("db_id"),
                    )
                    if success:
                        st.success("Added to Content Library!")
                    else:
                        st.error("Failed to add to library.")


# ===========================================================================
# TAB 2: Content Analyzer
# ===========================================================================

with tab_analyzer:
    st.subheader("Analyze Content for Visual Opportunities")
    st.markdown("Paste or upload content to identify where visuals would enhance understanding.")

    # --- Input method ---
    analyzer_input_method = st.radio(
        "Input Method",
        ["Paste Text", "Upload File"],
        horizontal=True,
        key="vs_analyzer_input_method",
    )

    analyzer_content = ""

    if analyzer_input_method == "Paste Text":
        analyzer_content = st.text_area(
            "Content to Analyze",
            height=200,
            placeholder="Paste your content here (article, report, training material, etc.)...",
            key="vs_analyzer_text",
        )
    else:
        uploaded_file = st.file_uploader(
            "Upload Content File",
            type=["txt", "md"],
            key="vs_analyzer_upload",
        )
        if uploaded_file:
            try:
                analyzer_content = uploaded_file.read().decode("utf-8")
                st.text_area("Uploaded Content Preview", value=analyzer_content[:2000], height=150, disabled=True)
            except Exception as exc:
                st.error(f"Failed to read file: {exc}")

    # --- Content type ---
    content_type_choice = st.selectbox(
        "Content Type",
        CONTENT_TYPES,
        key="vs_analyzer_content_type",
    )

    # --- Analyze button ---
    analyze_clicked = st.button(
        "Analyze Content",
        type="primary",
        key="vs_analyze_btn",
        disabled=not analyzer_content.strip() if analyzer_content else True,
    )

    if analyze_clicked and analyzer_content.strip():
        analyzer = get_content_analyzer()
        if not analyzer:
            # Fallback: use Anthropic directly for analysis
            if ANTHROPIC_AVAILABLE:
                with st.spinner("Analyzing content with AI..."):
                    try:
                        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                        response = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=2048,
                            messages=[{
                                "role": "user",
                                "content": (
                                    f"Analyze the following {content_type_choice.lower()} content and identify opportunities for visual diagrams. "
                                    f"For each opportunity, provide a JSON array with objects containing: "
                                    f'"location" (brief description of where in the content), '
                                    f'"visual_type" (one of: {", ".join(VISUAL_TYPES.keys())}), '
                                    f'"description" (what the visual should show), '
                                    f'"priority" (high/medium/low). '
                                    f"Return ONLY the JSON array.\n\nContent:\n{analyzer_content[:4000]}"
                                ),
                            }],
                        )
                        raw = response.content[0].text.strip()
                        # Extract JSON from response
                        if raw.startswith("["):
                            suggestions = json.loads(raw)
                        elif "[" in raw:
                            json_str = raw[raw.index("["):raw.rindex("]") + 1]
                            suggestions = json.loads(json_str)
                        else:
                            suggestions = []
                        st.session_state.vs_analysis_results = suggestions
                        st.session_state.vs_analysis_generated = [False] * len(suggestions)
                    except Exception as exc:
                        st.error(f"Analysis failed: {exc}")
                        st.session_state.vs_analysis_results = None
            else:
                st.error("Content analysis requires the Visual Pipeline or Anthropic API. Neither is available.")
        else:
            with st.spinner("Analyzing content for visual opportunities..."):
                try:
                    results = analyzer.analyze_content_for_visuals(analyzer_content, content_type_choice.lower())
                    st.session_state.vs_analysis_results = results
                    st.session_state.vs_analysis_generated = [False] * len(results)
                except Exception as exc:
                    st.error(f"Analysis failed: {exc}")
                    st.session_state.vs_analysis_results = None

    # --- Display analysis results ---
    if st.session_state.vs_analysis_results:
        suggestions = st.session_state.vs_analysis_results
        st.divider()
        st.markdown(f"**Found {len(suggestions)} Visual Opportunities**")

        # Generate All button
        if st.button("Generate All Visuals", type="secondary", key="vs_generate_all_analysis"):
            pipeline = get_visual_pipeline()
            if pipeline:
                progress = st.progress(0)
                generated_items = []
                for i, suggestion in enumerate(suggestions):
                    try:
                        Path(VISUALS_DIR).mkdir(parents=True, exist_ok=True)
                        vtype = suggestion.get("visual_type", "infographic")
                        save_path = Path(VISUALS_DIR) / f"{vtype}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.png"
                        result = pipeline.generate_visual(
                            description=suggestion.get("description", ""),
                            visual_type=vtype,
                            style="professional",
                            color_mode="brand",
                            output_format="png",
                            save_path=str(save_path),
                        )
                        generated_items.append({"result": result, "path": str(save_path), "type": vtype})
                        st.session_state.vs_analysis_generated[i] = True
                    except Exception as exc:
                        logger.error("Batch analysis generation failed for item %d: %s", i, exc)
                    progress.progress((i + 1) / len(suggestions))
                st.session_state.vs_generated_visuals_batch = generated_items
                st.success(f"Generated {len(generated_items)} of {len(suggestions)} visuals!")
            else:
                st.error("Visual Pipeline not available for batch generation.")

        # Individual suggestion cards
        for idx, suggestion in enumerate(suggestions):
            with st.container():
                s_cols = st.columns([3, 1, 1, 1])
                vtype = suggestion.get("visual_type", "infographic")
                with s_cols[0]:
                    st.markdown(
                        f'<div class="visual-card">'
                        f'<strong>{suggestion.get("location", "Section")}</strong><br>'
                        f'{render_type_badge(vtype)} '
                        f'{render_priority_badge(suggestion.get("priority", "medium"))}<br>'
                        f'<small>{suggestion.get("description", "No description")}</small>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with s_cols[1]:
                    st.caption(f"Type: {VISUAL_TYPES.get(vtype, {}).get('name', vtype)}")
                with s_cols[2]:
                    st.caption(f"Priority: {suggestion.get('priority', 'medium').title()}")
                with s_cols[3]:
                    if st.button("Generate This", key=f"vs_gen_suggestion_{idx}"):
                        pipeline = get_visual_pipeline()
                        if pipeline:
                            with st.spinner(f"Generating {VISUAL_TYPES.get(vtype, {}).get('name', vtype)}..."):
                                try:
                                    Path(VISUALS_DIR).mkdir(parents=True, exist_ok=True)
                                    save_path = Path(VISUALS_DIR) / f"{vtype}_analyzed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                                    result = pipeline.generate_visual(
                                        description=suggestion.get("description", ""),
                                        visual_type=vtype,
                                        style="professional",
                                        color_mode="brand",
                                        output_format="png",
                                        save_path=str(save_path),
                                    )
                                    st.session_state.vs_analysis_generated[idx] = True
                                    st.success(f"Generated! Saved to {save_path.name}")
                                    if save_path.exists() and save_path.suffix.lower() in (".png", ".svg", ".jpg"):
                                        st.image(str(save_path), use_container_width=True)
                                except Exception as exc:
                                    st.error(f"Generation failed: {exc}")
                        else:
                            st.error("Visual Pipeline not available.")

        # Show generated visuals gallery from analysis batch
        if st.session_state.vs_generated_visuals_batch:
            st.divider()
            st.markdown("**Generated Visuals from Analysis**")
            batch_cols = st.columns(3)
            for b_idx, bitem in enumerate(st.session_state.vs_generated_visuals_batch):
                col = batch_cols[b_idx % 3]
                with col:
                    bpath = Path(bitem["path"])
                    if bpath.exists() and bpath.suffix.lower() in (".png", ".svg", ".jpg", ".jpeg"):
                        try:
                            st.image(str(bpath), caption=bpath.name, use_container_width=True)
                        except Exception:
                            st.caption(f"File: {bpath.name}")
                    st.markdown(render_type_badge(bitem["type"]), unsafe_allow_html=True)


# ===========================================================================
# TAB 3: Batch Generation
# ===========================================================================

with tab_batch:
    st.subheader("Batch Visual Generation")
    st.markdown("Generate multiple visuals at once from a list of descriptions.")

    # --- Input method toggle ---
    batch_method = st.radio(
        "Input Method",
        ["Manual List", "JSON Upload", "From Content"],
        horizontal=True,
        key="vs_batch_method",
    )

    if batch_method == "Manual List":
        st.markdown("**Add Visual Items**")

        # Add new item form
        with st.expander("Add New Item", expanded=True):
            add_cols = st.columns([3, 1, 1])
            with add_cols[0]:
                new_desc = st.text_area(
                    "Description",
                    height=100,
                    placeholder="Describe the visual...",
                    key="vs_batch_new_desc",
                )
            with add_cols[1]:
                new_type = st.selectbox(
                    "Visual Type",
                    list(VISUAL_TYPES.keys()),
                    format_func=lambda x: VISUAL_TYPES[x]["name"],
                    key="vs_batch_new_type",
                )
            with add_cols[2]:
                new_style = st.selectbox(
                    "Style",
                    STYLE_OPTIONS,
                    key="vs_batch_new_style",
                )
            if st.button("Add to Batch", key="vs_batch_add_btn"):
                if new_desc.strip():
                    st.session_state.vs_batch_items.append({
                        "description": new_desc.strip(),
                        "visual_type": new_type,
                        "style": new_style.lower(),
                    })
                    st.success(f"Added item #{len(st.session_state.vs_batch_items)}")
                    st.rerun()
                else:
                    st.warning("Please enter a description.")

    elif batch_method == "JSON Upload":
        st.markdown("**Upload JSON Specification**")
        st.markdown(
            "Upload a JSON file with an array of objects. Each object should have: "
            "`description` (string), `visual_type` (string), and optionally `style` (string)."
        )
        json_file = st.file_uploader("Upload JSON", type=["json"], key="vs_batch_json_upload")
        if json_file:
            try:
                json_data = json.loads(json_file.read().decode("utf-8"))
                if isinstance(json_data, list):
                    st.session_state.vs_batch_items = []
                    for item in json_data:
                        if isinstance(item, dict) and "description" in item:
                            st.session_state.vs_batch_items.append({
                                "description": item["description"],
                                "visual_type": item.get("visual_type", "infographic"),
                                "style": item.get("style", "professional"),
                            })
                    st.success(f"Loaded {len(st.session_state.vs_batch_items)} items from JSON.")
                else:
                    st.error("JSON file must contain an array of objects.")
            except json.JSONDecodeError as exc:
                st.error(f"Invalid JSON: {exc}")

    elif batch_method == "From Content":
        st.markdown("**Auto-detect Visual Opportunities from Content**")
        content_for_batch = st.text_area(
            "Paste Content",
            height=200,
            placeholder="Paste your content to auto-detect visual opportunities...",
            key="vs_batch_content_input",
        )
        batch_content_type = st.selectbox(
            "Content Type",
            CONTENT_TYPES,
            key="vs_batch_content_type",
        )
        if st.button("Detect Visuals", key="vs_batch_detect_btn"):
            if content_for_batch.strip():
                analyzer = get_content_analyzer()
                if analyzer:
                    with st.spinner("Analyzing content..."):
                        try:
                            results = analyzer.analyze_content_for_visuals(content_for_batch, batch_content_type.lower())
                            st.session_state.vs_batch_items = []
                            for r in results:
                                st.session_state.vs_batch_items.append({
                                    "description": r.get("description", ""),
                                    "visual_type": r.get("visual_type", "infographic"),
                                    "style": "professional",
                                })
                            st.success(f"Detected {len(st.session_state.vs_batch_items)} visual opportunities.")
                        except Exception as exc:
                            st.error(f"Detection failed: {exc}")
                elif ANTHROPIC_AVAILABLE:
                    with st.spinner("Analyzing content with AI..."):
                        try:
                            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                            response = client.messages.create(
                                model="claude-sonnet-4-20250514",
                                max_tokens=2048,
                                messages=[{
                                    "role": "user",
                                    "content": (
                                        f"Analyze this {batch_content_type.lower()} content and identify visual opportunities. "
                                        f"Return a JSON array of objects with 'description' and 'visual_type' "
                                        f"(one of: {', '.join(VISUAL_TYPES.keys())}). Return ONLY JSON.\n\n"
                                        f"Content:\n{content_for_batch[:4000]}"
                                    ),
                                }],
                            )
                            raw = response.content[0].text.strip()
                            if raw.startswith("["):
                                items = json.loads(raw)
                            elif "[" in raw:
                                items = json.loads(raw[raw.index("["):raw.rindex("]") + 1])
                            else:
                                items = []
                            st.session_state.vs_batch_items = [
                                {"description": it.get("description", ""), "visual_type": it.get("visual_type", "infographic"), "style": "professional"}
                                for it in items if isinstance(it, dict) and "description" in it
                            ]
                            st.success(f"Detected {len(st.session_state.vs_batch_items)} visual opportunities.")
                        except Exception as exc:
                            st.error(f"AI detection failed: {exc}")
                else:
                    st.error("No analyzer or Anthropic API available for content detection.")
            else:
                st.warning("Please paste some content first.")

    # --- Preview batch items ---
    if st.session_state.vs_batch_items:
        st.divider()
        st.markdown(f"**Batch Queue ({len(st.session_state.vs_batch_items)} items)**")

        for b_idx, b_item in enumerate(st.session_state.vs_batch_items):
            item_cols = st.columns([4, 1, 1, 0.5])
            with item_cols[0]:
                st.markdown(
                    f"**#{b_idx + 1}** - {b_item['description'][:120]}{'...' if len(b_item['description']) > 120 else ''}",
                )
            with item_cols[1]:
                st.markdown(render_type_badge(b_item["visual_type"]), unsafe_allow_html=True)
            with item_cols[2]:
                st.caption(f"Style: {b_item.get('style', 'professional').title()}")
            with item_cols[3]:
                if st.button("X", key=f"vs_batch_remove_{b_idx}", help="Remove this item"):
                    st.session_state.vs_batch_items.pop(b_idx)
                    st.rerun()

        # Clear all button
        clear_col, gen_all_col, _ = st.columns([1, 1, 2])
        with clear_col:
            if st.button("Clear All", key="vs_batch_clear"):
                st.session_state.vs_batch_items = []
                st.session_state.vs_batch_results = []
                st.rerun()

        # --- Generate All ---
        with gen_all_col:
            generate_batch_clicked = st.button(
                f"Generate All ({len(st.session_state.vs_batch_items)} visuals)",
                type="primary",
                key="vs_batch_generate_all",
            )

        if generate_batch_clicked:
            pipeline = get_visual_pipeline()
            napkin = get_napkin_client()

            if not pipeline and not napkin:
                st.error("Neither Visual Pipeline nor Napkin Client is available for generation.")
            else:
                total = len(st.session_state.vs_batch_items)
                progress = st.progress(0)
                status_text = st.empty()
                results = []

                for i, item in enumerate(st.session_state.vs_batch_items):
                    status_text.text(f"Generating visual {i + 1} of {total}...")
                    try:
                        Path(VISUALS_DIR).mkdir(parents=True, exist_ok=True)
                        vtype = item["visual_type"]
                        save_path = Path(VISUALS_DIR) / f"{vtype}_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.png"

                        if pipeline:
                            result = pipeline.generate_visual(
                                description=item["description"],
                                visual_type=vtype,
                                style=item.get("style", "professional"),
                                color_mode="brand",
                                output_format="png",
                                save_path=str(save_path),
                            )
                        else:
                            result = napkin.generate_visual(
                                description=item["description"],
                                visual_type=vtype,
                                style=item.get("style", "professional"),
                                color_mode="brand",
                                output_format="png",
                                save_path=str(save_path),
                            )

                        results.append({
                            "result": result,
                            "path": str(save_path),
                            "type": vtype,
                            "description": item["description"],
                            "status": "success",
                        })
                    except Exception as exc:
                        results.append({
                            "path": None,
                            "type": vtype,
                            "description": item["description"],
                            "status": "failed",
                            "error": str(exc),
                        })
                        logger.error("Batch item %d failed: %s", i, exc)

                    progress.progress((i + 1) / total)

                st.session_state.vs_batch_results = results
                succeeded = sum(1 for r in results if r["status"] == "success")
                status_text.text("")
                st.success(f"Batch complete: {succeeded}/{total} visuals generated successfully.")

    # --- Batch results gallery ---
    if st.session_state.vs_batch_results:
        st.divider()
        st.markdown("**Batch Results**")

        result_cols = st.columns(3)
        for r_idx, r_item in enumerate(st.session_state.vs_batch_results):
            col = result_cols[r_idx % 3]
            with col:
                if r_item["status"] == "success" and r_item["path"]:
                    rpath = Path(r_item["path"])
                    if rpath.exists() and rpath.suffix.lower() in (".png", ".svg", ".jpg", ".jpeg"):
                        try:
                            st.image(str(rpath), caption=rpath.name, use_container_width=True)
                        except Exception:
                            st.caption(f"File: {rpath.name}")
                    st.markdown(render_type_badge(r_item["type"]), unsafe_allow_html=True)
                    st.caption(r_item["description"][:80])

                    if rpath.exists():
                        with open(rpath, "rb") as f:
                            st.download_button(
                                "Download",
                                data=f.read(),
                                file_name=rpath.name,
                                key=f"vs_batch_dl_{r_idx}",
                            )
                else:
                    st.error(f"Failed: {r_item.get('error', 'Unknown error')}")
                    st.caption(r_item["description"][:80])


# ===========================================================================
# TAB 4: Gallery
# ===========================================================================

with tab_gallery:
    st.subheader("Visual Gallery")
    st.markdown("Browse and manage all generated visuals.")

    all_visuals = scan_visuals_directory()

    # --- Stats at top ---
    if all_visuals:
        total_size = sum(v["size_bytes"] for v in all_visuals)
        type_counts = {}
        for v in all_visuals:
            type_counts[v["type"]] = type_counts.get(v["type"], 0) + 1

        stat_cols = st.columns(4)
        with stat_cols[0]:
            st.markdown(
                f'<div class="stat-box"><h3>{len(all_visuals)}</h3><small>Total Visuals</small></div>',
                unsafe_allow_html=True,
            )
        with stat_cols[1]:
            st.markdown(
                f'<div class="stat-box"><h3>{format_file_size(total_size)}</h3><small>Total Size</small></div>',
                unsafe_allow_html=True,
            )
        with stat_cols[2]:
            most_common_type = max(type_counts, key=type_counts.get) if type_counts else "N/A"
            type_name = VISUAL_TYPES.get(most_common_type, {}).get("name", most_common_type)
            st.markdown(
                f'<div class="stat-box"><h3>{type_name}</h3><small>Most Common Type</small></div>',
                unsafe_allow_html=True,
            )
        with stat_cols[3]:
            format_counts = {}
            for v in all_visuals:
                format_counts[v["format"]] = format_counts.get(v["format"], 0) + 1
            format_summary = ", ".join(f"{k.upper()}: {c}" for k, c in format_counts.items())
            st.markdown(
                f'<div class="stat-box"><h3>{len(format_counts)}</h3><small>Formats ({format_summary})</small></div>',
                unsafe_allow_html=True,
            )

        # Type breakdown chart
        with st.expander("Type Breakdown", expanded=False):
            breakdown_cols = st.columns(len(type_counts) if type_counts else 1)
            for i, (ttype, tcount) in enumerate(sorted(type_counts.items(), key=lambda x: x[1], reverse=True)):
                with breakdown_cols[i % len(breakdown_cols)]:
                    st.markdown(render_type_badge(ttype), unsafe_allow_html=True)
                    st.metric(label="Count", value=tcount)

        st.divider()

        # --- Filters ---
        filter_cols = st.columns([1, 1, 1, 1])
        with filter_cols[0]:
            type_filter = st.selectbox(
                "Filter by Type",
                ["All"] + list(VISUAL_TYPES.keys()),
                format_func=lambda x: "All Types" if x == "All" else VISUAL_TYPES.get(x, {}).get("name", x),
                key="vs_gallery_type_filter",
            )
        with filter_cols[1]:
            format_filter = st.selectbox(
                "Filter by Format",
                ["All", "png", "svg", "pptx"],
                format_func=lambda x: "All Formats" if x == "All" else x.upper(),
                key="vs_gallery_format_filter",
            )
        with filter_cols[2]:
            date_filter = st.selectbox(
                "Filter by Date",
                ["All Time", "Today", "Last 7 Days", "Last 30 Days"],
                key="vs_gallery_date_filter",
            )
        with filter_cols[3]:
            sort_order = st.selectbox(
                "Sort",
                ["Newest First", "Oldest First", "Largest First", "Smallest First"],
                key="vs_gallery_sort",
            )

        # Apply filters
        filtered = all_visuals.copy()
        if type_filter != "All":
            filtered = [v for v in filtered if v["type"] == type_filter]
        if format_filter != "All":
            filtered = [v for v in filtered if v["format"] == format_filter]
        if date_filter == "Today":
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            filtered = [v for v in filtered if v["created"] >= today]
        elif date_filter == "Last 7 Days":
            cutoff = datetime.now() - timedelta(days=7)
            filtered = [v for v in filtered if v["created"] >= cutoff]
        elif date_filter == "Last 30 Days":
            cutoff = datetime.now() - timedelta(days=30)
            filtered = [v for v in filtered if v["created"] >= cutoff]

        # Apply sort
        if sort_order == "Newest First":
            filtered.sort(key=lambda x: x["created"], reverse=True)
        elif sort_order == "Oldest First":
            filtered.sort(key=lambda x: x["created"])
        elif sort_order == "Largest First":
            filtered.sort(key=lambda x: x["size_bytes"], reverse=True)
        elif sort_order == "Smallest First":
            filtered.sort(key=lambda x: x["size_bytes"])

        st.caption(f"Showing {len(filtered)} of {len(all_visuals)} visuals")

        # --- Grid display ---
        if filtered:
            gallery_cols_count = 3
            gallery_cols = st.columns(gallery_cols_count)

            for g_idx, visual in enumerate(filtered):
                col = gallery_cols[g_idx % gallery_cols_count]
                with col:
                    vpath = Path(visual["path"])

                    st.markdown(
                        f'<div class="visual-card">'
                        f'{render_type_badge(visual["type"])}'
                        f'<br><strong>{visual["filename"]}</strong>'
                        f'<br><small>{visual["size_display"]} | {visual["format"].upper()} | {visual["created"].strftime("%Y-%m-%d %H:%M")}</small>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                    # Show thumbnail for image files
                    if visual["format"] in ("png", "svg", "jpg", "jpeg") and vpath.exists():
                        try:
                            st.image(str(vpath), use_container_width=True)
                        except Exception:
                            st.caption("Preview not available")

                    # Action buttons
                    action_cols = st.columns(3)
                    with action_cols[0]:
                        if vpath.exists():
                            with open(vpath, "rb") as f:
                                mime_map = {"png": "image/png", "svg": "image/svg+xml", "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation"}
                                st.download_button(
                                    "Download",
                                    data=f.read(),
                                    file_name=visual["filename"],
                                    mime=mime_map.get(visual["format"], "application/octet-stream"),
                                    key=f"vs_gallery_dl_{g_idx}",
                                )
                    with action_cols[1]:
                        if st.button("Add to Lib", key=f"vs_gallery_lib_{g_idx}"):
                            success = add_to_library(
                                title=visual["filename"],
                                description=f"{VISUAL_TYPES.get(visual['type'], {}).get('name', visual['type'])} visual",
                                tags=f"{visual['type']},{visual['format']}",
                                category="visual",
                            )
                            if success:
                                st.success("Added!")
                            else:
                                st.error("Failed")
                    with action_cols[2]:
                        if st.button("Delete", key=f"vs_gallery_del_{g_idx}"):
                            try:
                                vpath.unlink()
                                st.success(f"Deleted {visual['filename']}")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Delete failed: {exc}")

                    # Expand to full-size view
                    with st.expander("Full Size & Details"):
                        if visual["format"] in ("png", "svg", "jpg", "jpeg") and vpath.exists():
                            try:
                                st.image(str(vpath), use_container_width=True)
                            except Exception:
                                st.caption("Full-size preview not available")
                        st.json({
                            "filename": visual["filename"],
                            "type": visual["type"],
                            "format": visual["format"],
                            "size": visual["size_display"],
                            "created": visual["created"].isoformat(),
                            "path": visual["path"],
                        })
                        st.info(
                            "To insert this visual into a presentation, use the Presentation Studio "
                            "and reference the visual by its filename, or add it to the Content Library "
                            "first for easy access across all modules."
                        )
        else:
            st.info("No visuals match the current filters.")
    else:
        st.info(
            "No visuals found. Generate your first visual in the 'Generate Visual' tab, "
            "or check that the visuals directory exists at: " + str(VISUALS_DIR)
        )


# ===========================================================================
# TAB 5: Cache & Settings
# ===========================================================================

with tab_settings:
    st.subheader("Cache & Settings")

    settings_col_left, settings_col_right = st.columns(2)

    # --- Left: Cache Management ---
    with settings_col_left:
        st.markdown("**Napkin AI Cache**")

        napkin = get_napkin_client()
        if napkin:
            try:
                if hasattr(napkin, "available") and napkin.available:
                    st.success("Napkin AI: Connected")
                else:
                    st.warning("Napkin AI: Client loaded but connection status unknown")
            except Exception:
                st.warning("Napkin AI: Unable to check connection status")

            # Cache statistics
            try:
                cache_stats = napkin.get_cache_stats()
                if cache_stats:
                    cs_cols = st.columns(3)
                    with cs_cols[0]:
                        st.metric("Cached Items", cache_stats.get("total_items", cache_stats.get("count", 0)))
                    with cs_cols[1]:
                        cache_size = cache_stats.get("total_size", cache_stats.get("size_bytes", 0))
                        st.metric("Cache Size", format_file_size(cache_size) if isinstance(cache_size, (int, float)) else str(cache_size))
                    with cs_cols[2]:
                        hit_rate = cache_stats.get("hit_rate", cache_stats.get("hits", "N/A"))
                        st.metric("Hit Rate", f"{hit_rate}%" if isinstance(hit_rate, (int, float)) else str(hit_rate))
                else:
                    st.info("No cache statistics available.")
            except Exception as exc:
                st.warning(f"Could not retrieve cache stats: {exc}")

            # List cached visuals
            with st.expander("Cached Visuals", expanded=False):
                try:
                    cached_visuals = napkin.list_cached_visuals()
                    if cached_visuals:
                        for cv in cached_visuals[:20]:
                            if isinstance(cv, dict):
                                st.markdown(
                                    f"- **{cv.get('name', cv.get('filename', 'Unknown'))}** "
                                    f"({cv.get('type', 'N/A')}, {cv.get('size', 'N/A')})"
                                )
                            else:
                                st.markdown(f"- {cv}")
                        if len(cached_visuals) > 20:
                            st.caption(f"... and {len(cached_visuals) - 20} more")
                    else:
                        st.info("No cached visuals found.")
                except Exception as exc:
                    st.warning(f"Could not list cached visuals: {exc}")

            # Clear cache button
            st.divider()
            if st.button("Clear Cache", type="secondary", key="vs_clear_cache"):
                try:
                    napkin.clear_cache()
                    st.success("Cache cleared successfully!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to clear cache: {exc}")
        else:
            st.warning(
                "Napkin AI client is not available. Please ensure the `napkin_client` module is installed "
                "and the `NAPKIN_API_TOKEN` environment variable is set."
            )

        # Visual Pipeline status
        st.divider()
        st.markdown("**Visual Pipeline Status**")
        pipeline = get_visual_pipeline()
        if pipeline:
            st.success("Visual Pipeline: Available")
            try:
                stats = pipeline.get_visual_stats()
                if stats:
                    vp_cols = st.columns(2)
                    with vp_cols[0]:
                        st.metric("Total Generated", stats.get("total_generated", stats.get("count", 0)))
                    with vp_cols[1]:
                        avg_time = stats.get("avg_generation_time", stats.get("avg_time", "N/A"))
                        st.metric(
                            "Avg Generation Time",
                            f"{avg_time:.1f}s" if isinstance(avg_time, (int, float)) else str(avg_time),
                        )
            except Exception as exc:
                st.caption(f"Could not retrieve pipeline stats: {exc}")
        else:
            st.warning("Visual Pipeline: Not available")

        # Content Analyzer status
        analyzer = get_content_analyzer()
        if analyzer:
            st.success("Content Analyzer: Available")
        else:
            st.warning("Content Analyzer: Not available")

    # --- Right: Default Settings ---
    with settings_col_right:
        st.markdown("**Default Settings**")
        st.markdown("Configure default values for visual generation.")

        new_default_style = st.selectbox(
            "Default Style",
            STYLE_OPTIONS,
            index=STYLE_OPTIONS.index(st.session_state.vs_default_style) if st.session_state.vs_default_style in STYLE_OPTIONS else 0,
            key="vs_settings_default_style",
        )

        color_mode_keys = list(COLOR_MODES.keys())
        new_default_color = st.selectbox(
            "Default Color Mode",
            color_mode_keys,
            format_func=lambda x: f"{x.title()} - {COLOR_MODES[x][:50]}...",
            index=color_mode_keys.index(st.session_state.vs_default_color_mode) if st.session_state.vs_default_color_mode in color_mode_keys else 0,
            key="vs_settings_default_color",
        )

        new_default_format = st.selectbox(
            "Default Output Format",
            OUTPUT_FORMATS,
            format_func=lambda x: x.upper(),
            index=OUTPUT_FORMATS.index(st.session_state.vs_default_format) if st.session_state.vs_default_format in OUTPUT_FORMATS else 0,
            key="vs_settings_default_format",
        )

        new_default_orientation = st.selectbox(
            "Default Orientation",
            ORIENTATIONS,
            format_func=lambda x: x.title(),
            index=ORIENTATIONS.index(st.session_state.vs_default_orientation) if st.session_state.vs_default_orientation in ORIENTATIONS else 0,
            key="vs_settings_default_orientation",
        )

        if st.button("Save Defaults", type="primary", key="vs_save_defaults"):
            st.session_state.vs_default_style = new_default_style
            st.session_state.vs_default_color_mode = new_default_color
            st.session_state.vs_default_format = new_default_format
            st.session_state.vs_default_orientation = new_default_orientation
            st.success("Default settings saved!")

        # --- Session statistics ---
        st.divider()
        st.markdown("**Session Statistics**")
        st.metric("Visuals Generated This Session", st.session_state.vs_generation_count)
        st.metric("Batch Items Queued", len(st.session_state.vs_batch_items))
        st.metric("Batch Results", len(st.session_state.vs_batch_results))

        # --- Module availability summary ---
        st.divider()
        st.markdown("**Module Availability**")
        modules = {
            "Napkin AI Client": NAPKIN_AVAILABLE,
            "Visual Pipeline": VISUAL_GEN_AVAILABLE,
            "Database": DB_AVAILABLE,
            "Anthropic API": ANTHROPIC_AVAILABLE,
        }
        for mod_name, mod_avail in modules.items():
            if mod_avail:
                st.markdown(f"- {mod_name}: Available")
            else:
                st.markdown(f"- {mod_name}: **Not Available**")

        # --- Environment check ---
        st.divider()
        st.markdown("**Environment**")
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        napkin_token = os.getenv("NAPKIN_API_TOKEN", "")
        st.markdown(f"- ANTHROPIC_API_KEY: {'Set' if api_key else '**Not Set**'}")
        st.markdown(f"- NAPKIN_API_TOKEN: {'Set' if napkin_token else '**Not Set**'}")
        st.markdown(f"- Visuals Directory: `{VISUALS_DIR}`")
        st.markdown(f"- Cache Directory: `{CACHE_DIR}`")
        visuals_exist = Path(VISUALS_DIR).exists()
        st.markdown(f"- Visuals Dir Exists: {'Yes' if visuals_exist else 'No'}")
