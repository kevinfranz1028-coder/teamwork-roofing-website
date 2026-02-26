"""
Brand Intelligence Content Hub - Training Content Builder

Interactive pipeline for transforming curriculum content into complete training
packages: decks, facilitator guides, handouts, job aids, quizzes, microlearning
modules, and agent scripts.
"""

import json
import logging
import os
import tempfile
import time
import zipfile
from datetime import datetime
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Project imports (with graceful fallbacks)
# ---------------------------------------------------------------------------

try:
    from app.config import (
        BASE_DIR,
        BRAND_ASSETS_DIR,
        TRAINING_DIR,
        DOCUMENTS_DIR,
        PRESENTATIONS_DIR,
        get_env,
    )
except ImportError:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    BRAND_ASSETS_DIR = BASE_DIR / "brand_assets"
    TRAINING_DIR = BASE_DIR / "output" / "training"
    DOCUMENTS_DIR = BASE_DIR / "output" / "documents"
    PRESENTATIONS_DIR = BASE_DIR / "output" / "presentations"

    def get_env(key: str) -> str:
        return os.getenv(key, "")

try:
    from app.database.models import (
        get_session,
        GeneratedContent,
        ContentLibraryItem,
        BatchJob,
    )

    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    get_session = None
    GeneratedContent = None
    ContentLibraryItem = None
    BatchJob = None

try:
    from app.generators.training_pipeline import (
        TrainingModule,
        ParsedCurriculum,
        PipelineOptions,
        TrainingPackage,
        TrainingPipeline,
    )

    PIPELINE_AVAILABLE = True
except ImportError:
    PIPELINE_AVAILABLE = False
    TrainingModule = None
    ParsedCurriculum = None
    PipelineOptions = None
    TrainingPackage = None
    TrainingPipeline = None

try:
    from app.generators.quiz_gen import (
        QuizGenerator,
        QUESTION_TYPES,
        DIFFICULTY_LEVELS,
    )

    QUIZ_AVAILABLE = True
except ImportError:
    QUIZ_AVAILABLE = False
    QuizGenerator = None
    QUESTION_TYPES = [
        "Multiple Choice",
        "True/False",
        "Fill in the Blank",
        "Short Answer",
        "Matching",
        "Scenario-Based",
    ]
    DIFFICULTY_LEVELS = ["Comprehension", "Application", "Analysis"]

try:
    from app.generators.microlearning_gen import MicrolearningGenerator

    MICROLEARNING_AVAILABLE = True
except ImportError:
    MICROLEARNING_AVAILABLE = False
    MicrolearningGenerator = None

try:
    from app.ingestion.pdf_parser import PDFParser

    PDF_PARSER_AVAILABLE = True
except ImportError:
    PDF_PARSER_AVAILABLE = False
    PDFParser = None

try:
    from app.ingestion.docx_parser import DOCXParser

    DOCX_PARSER_AVAILABLE = True
except ImportError:
    DOCX_PARSER_AVAILABLE = False
    DOCXParser = None

try:
    from app.ingestion.pptx_parser import PPTXParser

    PPTX_PARSER_AVAILABLE = True
except ImportError:
    PPTX_PARSER_AVAILABLE = False
    PPTXParser = None

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ensure output directory exists
# ---------------------------------------------------------------------------

TRAINING_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Training Builder", layout="wide")

st.markdown(
    """<style>
.pipeline-step {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
    background: white;
}
.step-active {
    border-color: #0066cc;
    background: #f0f7ff;
}
.step-complete {
    border-color: #137333;
    background: #e6f4ea;
}
.step-error {
    border-color: #c5221f;
    background: #fce8e6;
}
.module-card {
    border-left: 4px solid #0066cc;
    padding: 12px;
    margin: 8px 0;
    background: #f8f9fa;
    border-radius: 0 8px 8px 0;
}
.output-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
    margin: 2px 4px;
}
.ob-deck { background: #e8f0fe; color: #1a73e8; }
.ob-guide { background: #e6f4ea; color: #137333; }
.ob-handout { background: #fef7e0; color: #b06000; }
.ob-jobaid { background: #f3e8fd; color: #7627bb; }
.ob-quiz { background: #fce8e6; color: #c5221f; }
.ob-micro { background: #e0f2f1; color: #00695c; }
.ob-script { background: #fce4ec; color: #c62828; }
.stProgress > div > div > div > div { background-color: #0066cc; }
.metric-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
    border: 1px solid #e0e0e0;
}
.curriculum-header {
    background: linear-gradient(135deg, #0066cc 0%, #004999 100%);
    color: white;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 16px;
}
</style>""",
    unsafe_allow_html=True,
)

st.title("Training Content Builder")
st.markdown("Transform curriculum content into complete training packages")

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

_SESSION_DEFAULTS = {
    "training_input_content": "",
    "training_input_type": "text",
    "training_parsed_curriculum": None,
    "training_package": None,
    "training_outputs": [],
    "training_errors": [],
    "training_generation_time": None,
    "training_zip_path": None,
    "training_session_count": 0,
    "training_history_refresh": 0,
    "training_modified_curriculum": None,
    "quick_quiz_result": None,
    "quick_micro_result": None,
    "quick_script_result": None,
}

for key, default in _SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _load_brand_config() -> dict:
    """Load brand_config.json if it exists."""
    config_path = BRAND_ASSETS_DIR / "brand_config.json"
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _extract_text_from_upload(uploaded_file) -> str:
    """Extract text from an uploaded file using the appropriate parser."""
    suffix = Path(uploaded_file.name).suffix.lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    try:
        if suffix == ".pdf" and PDF_PARSER_AVAILABLE:
            parser = PDFParser()
            result = parser.parse(tmp_path)
            return result.get("text", "")
        elif suffix in (".docx", ".docm") and DOCX_PARSER_AVAILABLE:
            parser = DOCXParser()
            result = parser.parse(tmp_path)
            return result.get("text", "")
        elif suffix in (".pptx", ".pptm") and PPTX_PARSER_AVAILABLE:
            parser = PPTXParser()
            result = parser.parse(tmp_path)
            slides = result.get("slides", [])
            text_parts = []
            for slide in slides:
                if slide.get("title"):
                    text_parts.append(f"## {slide['title']}")
                for content_item in slide.get("content", []):
                    text_parts.append(content_item)
                if slide.get("notes"):
                    text_parts.append(f"Notes: {slide['notes']}")
            return "\n\n".join(text_parts)
        elif suffix == ".txt":
            return uploaded_file.getvalue().decode("utf-8", errors="replace")
        else:
            return uploaded_file.getvalue().decode("utf-8", errors="replace")
    except Exception as e:
        st.error(f"Failed to parse {uploaded_file.name}: {e}")
        return ""
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _save_to_db(title: str, content_type: str, output_path: str,
                file_format: str, gen_time: float, input_summary: str = "") -> None:
    """Record a generated output in the database."""
    if not DB_AVAILABLE:
        return
    try:
        session = get_session()
        record = GeneratedContent(
            title=title,
            content_type=content_type,
            output_path=output_path,
            format=file_format,
            generation_time_seconds=gen_time,
            input_summary=input_summary[:500] if input_summary else "",
            generated_at=datetime.utcnow(),
        )
        session.add(record)
        session.commit()
        session.close()
    except Exception as e:
        logger.warning("Failed to save to database: %s", e)


def _add_to_library(content_id: int, title: str, category: str) -> bool:
    """Add a GeneratedContent record to the content library."""
    if not DB_AVAILABLE:
        return False
    try:
        session = get_session()
        item = ContentLibraryItem(
            generated_content_id=content_id,
            title=title,
            category=category,
            is_approved=False,
        )
        session.add(item)
        session.commit()
        session.close()
        return True
    except Exception as e:
        logger.warning("Failed to add to library: %s", e)
        return False


def _create_zip(file_paths: list, zip_name: str) -> str:
    """Create a ZIP archive from a list of file paths."""
    zip_path = str(TRAINING_DIR / zip_name)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in file_paths:
            fp_path = Path(fp)
            if fp_path.exists():
                zf.write(fp_path, fp_path.name)
    return zip_path


def _format_duration(minutes: int) -> str:
    """Format minutes into a human-readable duration string."""
    if minutes < 60:
        return f"{minutes} min"
    hours = minutes // 60
    remaining = minutes % 60
    if remaining == 0:
        return f"{hours}h"
    return f"{hours}h {remaining}m"


def _output_type_badge(output_type: str) -> str:
    """Return an HTML badge for the given output type."""
    badge_map = {
        "training_deck": ("Training Deck", "ob-deck"),
        "facilitator_guide": ("Facilitator Guide", "ob-guide"),
        "participant_handout": ("Participant Handout", "ob-handout"),
        "job_aid": ("Job Aid", "ob-jobaid"),
        "quiz": ("Quiz", "ob-quiz"),
        "microlearning": ("Microlearning", "ob-micro"),
        "agent_script": ("Agent Script", "ob-script"),
        "training_package": ("Full Package", "ob-deck"),
    }
    label, css_class = badge_map.get(output_type, (output_type, "ob-deck"))
    return f'<span class="output-badge {css_class}">{label}</span>'


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.subheader("Pipeline Status")

    status_items = [
        ("Training Pipeline", PIPELINE_AVAILABLE),
        ("Quiz Generator", QUIZ_AVAILABLE),
        ("Microlearning Generator", MICROLEARNING_AVAILABLE),
        ("PDF Parser", PDF_PARSER_AVAILABLE),
        ("DOCX Parser", DOCX_PARSER_AVAILABLE),
        ("PPTX Parser", PPTX_PARSER_AVAILABLE),
        ("Database", DB_AVAILABLE),
    ]

    for name, available in status_items:
        icon = "+" if available else "-"
        color = "#137333" if available else "#c5221f"
        st.markdown(
            f'<span style="color:{color}; font-weight:600;">[{icon}]</span> {name}',
            unsafe_allow_html=True,
        )

    st.divider()

    st.subheader("Current Session")
    st.metric("Outputs Generated", st.session_state.training_session_count)

    if st.session_state.training_outputs:
        st.divider()
        st.subheader("Quick Links")
        for output_info in st.session_state.training_outputs:
            out_path = Path(output_info.get("path", ""))
            if out_path.exists():
                with open(out_path, "rb") as f:
                    st.download_button(
                        label=f"  {output_info.get('label', out_path.name)}",
                        data=f.read(),
                        file_name=out_path.name,
                        mime="application/octet-stream",
                        key=f"sidebar_dl_{out_path.name}",
                    )

    if st.session_state.training_zip_path:
        zip_p = Path(st.session_state.training_zip_path)
        if zip_p.exists():
            st.divider()
            with open(zip_p, "rb") as f:
                st.download_button(
                    label="Download Full Package (ZIP)",
                    data=f.read(),
                    file_name=zip_p.name,
                    mime="application/zip",
                    key="sidebar_zip_dl",
                )


# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------

tab_build, tab_preview, tab_quick, tab_history = st.tabs([
    "Build Training Package",
    "Curriculum Preview",
    "Quick Generate",
    "History",
])


# =========================================================================
# TAB 1: Build Training Package
# =========================================================================

with tab_build:
    col_input, col_config = st.columns([2, 1])

    # ----- Left Column: Content Input -----
    with col_input:
        st.subheader("Content Input")

        input_method = st.radio(
            "Input Method",
            ["Paste Content", "Upload File", "Describe Topic"],
            horizontal=True,
            key="tb_input_method",
        )

        input_content = ""
        input_type = "text"

        if input_method == "Paste Content":
            input_content = st.text_area(
                "Curriculum / Training Content",
                height=300,
                placeholder=(
                    "Paste your curriculum outline, training manual text, "
                    "course syllabus, or any content you want to transform "
                    "into training materials..."
                ),
                key="tb_paste_content",
            )
            input_type = "text"

        elif input_method == "Upload File":
            accepted_types = [".txt"]
            type_notes = ["TXT"]
            if PDF_PARSER_AVAILABLE:
                accepted_types.append(".pdf")
                type_notes.append("PDF")
            if DOCX_PARSER_AVAILABLE:
                accepted_types.extend([".docx"])
                type_notes.append("DOCX")
            if PPTX_PARSER_AVAILABLE:
                accepted_types.extend([".pptx"])
                type_notes.append("PPTX")

            uploaded_file = st.file_uploader(
                f"Upload training content ({', '.join(type_notes)})",
                type=[t.lstrip('.') for t in accepted_types],
                key="tb_upload_file",
            )

            if uploaded_file is not None:
                with st.spinner("Extracting text from file..."):
                    extracted = _extract_text_from_upload(uploaded_file)

                if extracted:
                    input_content = extracted
                    input_type = "text"
                    st.success(
                        f"Extracted {len(extracted):,} characters from "
                        f"{uploaded_file.name}"
                    )
                    with st.expander("Preview Extracted Text", expanded=False):
                        st.text_area(
                            "Extracted Content",
                            value=extracted[:5000] + (
                                "\n\n... (truncated)" if len(extracted) > 5000 else ""
                            ),
                            height=250,
                            disabled=True,
                            key="tb_extracted_preview",
                        )
                else:
                    st.warning("Could not extract text from the uploaded file.")

        elif input_method == "Describe Topic":
            input_content = st.text_area(
                "Topic Description",
                height=200,
                placeholder=(
                    "Describe the training topic and the AI will generate a "
                    "full curriculum.\n\n"
                    "Example: 'Customer service excellence for retail employees "
                    "covering communication skills, conflict resolution, "
                    "upselling techniques, and handling difficult customers. "
                    "Target audience is new hires with no prior retail experience.'"
                ),
                key="tb_topic_desc",
            )
            input_type = "topic_description"

        st.divider()

        # Training metadata selectors
        meta_col1, meta_col2 = st.columns(2)
        with meta_col1:
            training_type = st.selectbox(
                "Training Type",
                [
                    "General Training",
                    "Employee Onboarding",
                    "Product Training",
                    "Compliance Training",
                    "Sales Training",
                    "Technical Training",
                ],
                key="tb_training_type",
            )
        with meta_col2:
            audience_level = st.selectbox(
                "Target Audience Level",
                ["Beginner", "Intermediate", "Advanced"],
                key="tb_audience_level",
            )

        language = st.selectbox(
            "Language",
            ["English", "Spanish", "French", "German", "Portuguese"],
            key="tb_language",
        )

    # ----- Right Column: Pipeline Configuration -----
    with col_config:
        st.subheader("Pipeline Configuration")
        st.markdown("Select the outputs to generate:")

        opt_deck = st.checkbox(
            "Training Deck",
            value=True,
            help="Branded PPTX presentation with slides for each module",
            key="tb_opt_deck",
        )
        opt_guide = st.checkbox(
            "Facilitator Guide",
            value=True,
            help="Instructor manual with timing, notes, and discussion prompts",
            key="tb_opt_guide",
        )
        opt_handouts = st.checkbox(
            "Participant Handouts",
            value=False,
            help="Learner-facing materials with note-taking areas",
            key="tb_opt_handouts",
        )
        opt_jobaid = st.checkbox(
            "Job Aids",
            value=False,
            help="Quick reference cards for each module",
            key="tb_opt_jobaid",
        )
        opt_quiz = st.checkbox(
            "Assessment Quiz",
            value=True,
            help="Configurable quiz with answer key",
            key="tb_opt_quiz",
        )
        opt_micro = st.checkbox(
            "Microlearning Modules",
            value=False,
            help="Bite-sized learning units for reinforcement",
            key="tb_opt_micro",
        )

        # Agent Script only shown for Sales Training
        opt_script = False
        if training_type == "Sales Training":
            opt_script = st.checkbox(
                "Agent Script",
                value=False,
                help="Call center / sales conversation script",
                key="tb_opt_script",
            )

        selected_count = sum([
            opt_deck, opt_guide, opt_handouts, opt_jobaid,
            opt_quiz, opt_micro, opt_script,
        ])
        st.caption(f"{selected_count} output(s) selected")

        # ----- Quiz Configuration -----
        if opt_quiz:
            st.divider()
            st.markdown("**Quiz Configuration**")
            quiz_count = st.slider(
                "Number of Questions",
                min_value=5,
                max_value=30,
                value=10,
                step=1,
                key="tb_quiz_count",
            )
            quiz_difficulty = st.selectbox(
                "Difficulty Level",
                ["Comprehension", "Application", "Analysis"],
                key="tb_quiz_difficulty",
            )
            quiz_types = st.multiselect(
                "Question Types",
                QUESTION_TYPES,
                default=["Multiple Choice", "True/False"],
                key="tb_quiz_types",
            )
            if not quiz_types:
                quiz_types = ["Multiple Choice"]

        # ----- Microlearning Configuration -----
        if opt_micro:
            st.divider()
            st.markdown("**Microlearning Configuration**")
            micro_duration = st.slider(
                "Module Duration (minutes)",
                min_value=3,
                max_value=15,
                value=7,
                step=1,
                key="tb_micro_duration",
            )
            micro_format = st.selectbox(
                "Output Format",
                ["1-Page PDFs", "Slide Decks", "Email Content"],
                key="tb_micro_format",
            )

        # ----- Agent Script Configuration -----
        if opt_script:
            st.divider()
            st.markdown("**Agent Script Configuration**")
            script_product_info = st.text_area(
                "Product / Service Information",
                height=100,
                placeholder="Describe the product or service the agent will be selling...",
                key="tb_script_product",
            )
            script_call_objectives = st.text_area(
                "Call Objectives",
                height=100,
                placeholder="What should the agent accomplish on each call?",
                key="tb_script_objectives",
            )

    # ----- Build Button -----
    st.divider()

    build_disabled = not input_content.strip() or selected_count == 0
    build_col1, build_col2, build_col3 = st.columns([1, 2, 1])

    with build_col2:
        build_clicked = st.button(
            "Build Training Package",
            type="primary",
            disabled=build_disabled,
            use_container_width=True,
            key="tb_build_btn",
        )

    if build_disabled and not input_content.strip():
        st.caption("Provide content above to enable the Build button.")

    # ----- Pipeline Execution -----
    if build_clicked and input_content.strip():
        if not PIPELINE_AVAILABLE:
            st.error(
                "Training Pipeline is not available. Ensure "
                "`app.generators.training_pipeline` is installed and importable."
            )
        else:
            # Reset previous outputs
            st.session_state.training_outputs = []
            st.session_state.training_errors = []
            st.session_state.training_zip_path = None
            st.session_state.training_package = None

            # Build PipelineOptions
            pipeline_opts = PipelineOptions(
                training_deck=opt_deck,
                facilitator_guide=opt_guide,
                participant_handouts=opt_handouts,
                job_aids=opt_jobaid,
                quiz=opt_quiz,
                microlearning=opt_micro,
                agent_script=opt_script,
                quiz_question_count=quiz_count if opt_quiz else 10,
                quiz_difficulty=quiz_difficulty if opt_quiz else "Comprehension",
                quiz_question_types=quiz_types if opt_quiz else ["Multiple Choice"],
                module_duration_minutes=micro_duration if opt_micro else 7,
                product_info=script_product_info if opt_script else "",
                call_objectives=script_call_objectives if opt_script else "",
                language=language,
                training_type=training_type,
                audience_level=audience_level,
            )

            start_time = time.time()

            # --- Step 1: Parse curriculum ---
            progress_bar = st.progress(0)
            status_container = st.empty()

            status_container.markdown(
                '<div class="pipeline-step step-active">'
                "<strong>Step 1/3:</strong> Parsing curriculum content..."
                "</div>",
                unsafe_allow_html=True,
            )

            try:
                pipeline = TrainingPipeline()
                parsed = pipeline.parse_input(input_content, input_type, pipeline_opts)
                st.session_state.training_parsed_curriculum = parsed
                st.session_state.training_input_content = input_content
                st.session_state.training_input_type = input_type
                progress_bar.progress(33)

                status_container.markdown(
                    '<div class="pipeline-step step-complete">'
                    "<strong>Step 1/3:</strong> Curriculum parsed successfully"
                    "</div>",
                    unsafe_allow_html=True,
                )
            except Exception as e:
                progress_bar.progress(0)
                status_container.markdown(
                    '<div class="pipeline-step step-error">'
                    f"<strong>Step 1/3:</strong> Parsing failed - {e}"
                    "</div>",
                    unsafe_allow_html=True,
                )
                st.session_state.training_errors.append(
                    {"step": "parse", "error": str(e)}
                )
                st.stop()

            # --- Step 2: Generate outputs ---
            status_container.markdown(
                '<div class="pipeline-step step-active">'
                "<strong>Step 2/3:</strong> Generating training materials..."
                "</div>",
                unsafe_allow_html=True,
            )

            try:
                package = pipeline.process_curriculum(
                    input_content, input_type, pipeline_opts
                )
                st.session_state.training_package = package
                progress_bar.progress(75)

                status_container.markdown(
                    '<div class="pipeline-step step-complete">'
                    "<strong>Step 2/3:</strong> Materials generated"
                    "</div>",
                    unsafe_allow_html=True,
                )
            except Exception as e:
                progress_bar.progress(33)
                status_container.markdown(
                    '<div class="pipeline-step step-error">'
                    f"<strong>Step 2/3:</strong> Generation failed - {e}"
                    "</div>",
                    unsafe_allow_html=True,
                )
                st.session_state.training_errors.append(
                    {"step": "generate", "error": str(e)}
                )
                st.stop()

            # --- Step 3: Package outputs ---
            status_container.markdown(
                '<div class="pipeline-step step-active">'
                "<strong>Step 3/3:</strong> Packaging outputs..."
                "</div>",
                unsafe_allow_html=True,
            )

            try:
                package_title = (
                    getattr(parsed, "title", None)
                    or f"Training Package - {training_type}"
                )
                zip_path = pipeline.package_outputs(package, package_title)
                st.session_state.training_zip_path = zip_path
                progress_bar.progress(100)

                status_container.markdown(
                    '<div class="pipeline-step step-complete">'
                    "<strong>Step 3/3:</strong> Package ready for download"
                    "</div>",
                    unsafe_allow_html=True,
                )
            except Exception as e:
                progress_bar.progress(75)
                status_container.markdown(
                    '<div class="pipeline-step step-error">'
                    f"<strong>Step 3/3:</strong> Packaging failed - {e}"
                    "</div>",
                    unsafe_allow_html=True,
                )
                st.session_state.training_errors.append(
                    {"step": "package", "error": str(e)}
                )

            elapsed = time.time() - start_time
            st.session_state.training_generation_time = elapsed

            # --- Collect output file info ---
            outputs_collected = []

            # Inspect the package object for output paths
            if package is not None:
                output_map = {
                    "training_deck": ("Training Deck", "PPTX"),
                    "facilitator_guide": ("Facilitator Guide", "DOCX"),
                    "participant_handouts": ("Participant Handouts", "DOCX"),
                    "job_aids": ("Job Aids", "DOCX"),
                    "quiz": ("Assessment Quiz", "DOCX"),
                    "microlearning": ("Microlearning Modules", "ZIP"),
                    "agent_script": ("Agent Script", "DOCX"),
                }

                for attr_name, (label, fmt) in output_map.items():
                    output_path = getattr(package, attr_name, None)
                    if output_path and Path(output_path).exists():
                        outputs_collected.append({
                            "label": label,
                            "type": attr_name,
                            "path": str(output_path),
                            "format": fmt,
                        })

                        # Save each output to database
                        _save_to_db(
                            title=f"{package_title} - {label}",
                            content_type=attr_name,
                            output_path=str(output_path),
                            file_format=fmt,
                            gen_time=elapsed,
                            input_summary=input_content[:500],
                        )

            st.session_state.training_outputs = outputs_collected
            st.session_state.training_session_count += len(outputs_collected)

            # Save the package record
            if zip_path and Path(zip_path).exists():
                _save_to_db(
                    title=package_title,
                    content_type="training_package",
                    output_path=str(zip_path),
                    file_format="ZIP",
                    gen_time=elapsed,
                    input_summary=input_content[:500],
                )

            st.rerun()

    # ----- Display results (persisted in session_state) -----
    if st.session_state.training_outputs:
        st.divider()
        st.subheader("Generation Results")

        # Summary row
        gen_time = st.session_state.training_generation_time or 0
        output_count = len(st.session_state.training_outputs)

        summary_cols = st.columns(3)
        with summary_cols[0]:
            st.metric("Outputs Generated", output_count)
        with summary_cols[1]:
            st.metric("Total Time", f"{gen_time:.1f}s")
        with summary_cols[2]:
            st.metric(
                "Avg per Output",
                f"{gen_time / max(output_count, 1):.1f}s",
            )

        # Output badges
        badges_html = " ".join(
            _output_type_badge(o["type"])
            for o in st.session_state.training_outputs
        )
        st.markdown(badges_html, unsafe_allow_html=True)

        st.markdown("")

        # Individual download buttons
        for idx, output_info in enumerate(st.session_state.training_outputs):
            out_path = Path(output_info["path"])
            if out_path.exists():
                dl_col1, dl_col2, dl_col3 = st.columns([3, 1, 1])
                with dl_col1:
                    st.markdown(
                        f'**{output_info["label"]}** '
                        f'<span style="color:#666;">({output_info["format"]})</span>',
                        unsafe_allow_html=True,
                    )
                    st.caption(out_path.name)
                with dl_col2:
                    file_size = out_path.stat().st_size
                    if file_size > 1_048_576:
                        st.caption(f"{file_size / 1_048_576:.1f} MB")
                    else:
                        st.caption(f"{file_size / 1024:.0f} KB")
                with dl_col3:
                    with open(out_path, "rb") as f:
                        st.download_button(
                            "Download",
                            data=f.read(),
                            file_name=out_path.name,
                            mime="application/octet-stream",
                            key=f"dl_output_{idx}",
                        )

        # Download All ZIP
        if st.session_state.training_zip_path:
            zip_p = Path(st.session_state.training_zip_path)
            if zip_p.exists():
                st.divider()
                with open(zip_p, "rb") as f:
                    st.download_button(
                        "Download All as ZIP",
                        data=f.read(),
                        file_name=zip_p.name,
                        mime="application/zip",
                        type="primary",
                        use_container_width=True,
                        key="dl_all_zip",
                    )

    # ----- Errors section -----
    if st.session_state.training_errors:
        st.divider()
        st.subheader("Errors")
        for err in st.session_state.training_errors:
            st.error(f"**Step: {err['step']}** - {err['error']}")


# =========================================================================
# TAB 2: Curriculum Preview
# =========================================================================

with tab_preview:
    parsed = st.session_state.training_parsed_curriculum

    if parsed is None:
        st.info(
            "No curriculum has been parsed yet. Use the **Build Training Package** "
            "tab to input content and run the pipeline. The parsed curriculum "
            "structure will appear here for review and editing."
        )
    else:
        # Header section
        curriculum_title = getattr(parsed, "title", "Untitled Curriculum")
        curriculum_desc = getattr(parsed, "description", "")
        curriculum_audience = getattr(parsed, "target_audience", "")
        curriculum_duration = getattr(parsed, "total_duration_minutes", 0)
        prerequisites = getattr(parsed, "prerequisites", [])
        learning_outcomes = getattr(parsed, "learning_outcomes", [])
        modules = getattr(parsed, "modules", [])

        st.markdown(
            f'<div class="curriculum-header">'
            f"<h2 style='margin:0; color:white;'>{curriculum_title}</h2>"
            f"<p style='margin:4px 0 0 0; opacity:0.9;'>{curriculum_desc}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Overview metrics
        ov_col1, ov_col2, ov_col3, ov_col4 = st.columns(4)
        with ov_col1:
            st.metric("Modules", len(modules))
        with ov_col2:
            st.metric("Duration", _format_duration(curriculum_duration))
        with ov_col3:
            st.metric("Audience", curriculum_audience or "Not specified")
        with ov_col4:
            total_topics = sum(
                len(getattr(m, "topics", []))
                for m in modules
            )
            st.metric("Topics", total_topics)

        # Prerequisites
        if prerequisites:
            st.subheader("Prerequisites")
            for prereq in prerequisites:
                st.markdown(f"- {prereq}")

        # Learning Outcomes
        if learning_outcomes:
            st.subheader("Learning Outcomes")
            for idx, outcome in enumerate(learning_outcomes, 1):
                st.markdown(f"{idx}. {outcome}")

        st.divider()

        # ----- Modules -----
        st.subheader("Modules")

        # Track modifications in session state
        if st.session_state.training_modified_curriculum is None:
            st.session_state.training_modified_curriculum = {
                "title": curriculum_title,
                "description": curriculum_desc,
                "modules": [],
            }
            for m in modules:
                mod_data = {
                    "title": getattr(m, "title", "Untitled"),
                    "duration": getattr(m, "duration_minutes", 0),
                    "objectives": list(getattr(m, "objectives", [])),
                    "topics": [],
                    "activities": [],
                    "key_takeaways": list(getattr(m, "key_takeaways", [])),
                }
                for t in getattr(m, "topics", []):
                    mod_data["topics"].append({
                        "title": getattr(t, "title", ""),
                        "content": getattr(t, "content", ""),
                    })
                for a in getattr(m, "activities", []):
                    mod_data["activities"].append({
                        "type": getattr(a, "type", ""),
                        "instructions": getattr(a, "instructions", ""),
                    })
                st.session_state.training_modified_curriculum["modules"].append(
                    mod_data
                )

        modified = st.session_state.training_modified_curriculum

        # Editable curriculum title
        new_title = st.text_input(
            "Curriculum Title",
            value=modified["title"],
            key="cp_title_edit",
        )
        modified["title"] = new_title

        new_desc = st.text_area(
            "Curriculum Description",
            value=modified["description"],
            height=80,
            key="cp_desc_edit",
        )
        modified["description"] = new_desc

        # Module editors
        modules_to_delete = []
        for m_idx, mod in enumerate(modified["modules"]):
            with st.expander(
                f"Module {m_idx + 1}: {mod['title']} "
                f"({_format_duration(mod.get('duration', 0))})",
                expanded=False,
            ):
                mc1, mc2 = st.columns([3, 1])
                with mc1:
                    new_mod_title = st.text_input(
                        "Module Title",
                        value=mod["title"],
                        key=f"cp_mod_title_{m_idx}",
                    )
                    mod["title"] = new_mod_title
                with mc2:
                    new_dur = st.number_input(
                        "Duration (min)",
                        min_value=1,
                        max_value=480,
                        value=max(mod.get("duration", 15), 1),
                        key=f"cp_mod_dur_{m_idx}",
                    )
                    mod["duration"] = new_dur

                # Objectives
                st.markdown("**Objectives**")
                objectives_text = "\n".join(mod.get("objectives", []))
                new_obj_text = st.text_area(
                    "Objectives (one per line)",
                    value=objectives_text,
                    height=100,
                    key=f"cp_mod_obj_{m_idx}",
                    label_visibility="collapsed",
                )
                mod["objectives"] = [
                    o.strip() for o in new_obj_text.split("\n") if o.strip()
                ]

                # Topics
                if mod.get("topics"):
                    st.markdown("**Topics**")
                    for t_idx, topic in enumerate(mod["topics"]):
                        st.markdown(
                            f'<div class="module-card">'
                            f'<strong>{topic.get("title", "Topic")}</strong>'
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                        topic_content = topic.get("content", "")
                        if topic_content:
                            preview_text = (
                                topic_content[:300] + "..."
                                if len(topic_content) > 300
                                else topic_content
                            )
                            st.caption(preview_text)

                # Activities
                if mod.get("activities"):
                    st.markdown("**Activities**")
                    for a_idx, activity in enumerate(mod["activities"]):
                        act_type = activity.get("type", "Activity")
                        act_inst = activity.get("instructions", "")
                        st.markdown(f"- **{act_type}**: {act_inst[:200]}")

                # Key Takeaways
                if mod.get("key_takeaways"):
                    st.markdown("**Key Takeaways**")
                    for kt in mod["key_takeaways"]:
                        st.markdown(f"- {kt}")

                # Delete module button
                if st.button(
                    "Remove Module",
                    key=f"cp_del_mod_{m_idx}",
                    type="secondary",
                ):
                    modules_to_delete.append(m_idx)

        # Process deletions (reverse order to preserve indices)
        if modules_to_delete:
            for d_idx in sorted(modules_to_delete, reverse=True):
                modified["modules"].pop(d_idx)
            st.rerun()

        # Add new module
        st.divider()
        add_col1, add_col2 = st.columns([3, 1])
        with add_col1:
            new_module_title = st.text_input(
                "New Module Title",
                placeholder="Enter title for a new module...",
                key="cp_new_mod_title",
            )
        with add_col2:
            st.markdown("")
            st.markdown("")
            if st.button("Add Module", key="cp_add_mod", disabled=not new_module_title):
                modified["modules"].append({
                    "title": new_module_title,
                    "duration": 30,
                    "objectives": [],
                    "topics": [],
                    "activities": [],
                    "key_takeaways": [],
                })
                st.rerun()

        # Action buttons
        st.divider()
        action_col1, action_col2, action_col3 = st.columns(3)

        with action_col1:
            if st.button(
                "Re-parse Original Content",
                key="cp_reparse",
                disabled=not PIPELINE_AVAILABLE,
            ):
                if st.session_state.training_input_content:
                    with st.spinner("Re-parsing content..."):
                        try:
                            pipeline = TrainingPipeline()
                            re_parsed = pipeline.parse_input(
                                st.session_state.training_input_content,
                                st.session_state.training_input_type,
                                PipelineOptions(
                                    training_deck=False,
                                    facilitator_guide=False,
                                    participant_handouts=False,
                                    job_aids=False,
                                    quiz=False,
                                    microlearning=False,
                                    agent_script=False,
                                    quiz_question_count=10,
                                    quiz_difficulty="Comprehension",
                                    quiz_question_types=["Multiple Choice"],
                                    module_duration_minutes=7,
                                    product_info="",
                                    call_objectives="",
                                    language="English",
                                    training_type="General Training",
                                    audience_level="Beginner",
                                ),
                            )
                            st.session_state.training_parsed_curriculum = re_parsed
                            st.session_state.training_modified_curriculum = None
                            st.success("Curriculum re-parsed successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Re-parse failed: {e}")
                else:
                    st.warning("No original content available to re-parse.")

        with action_col2:
            if st.button("Use Modified Curriculum", key="cp_use_modified"):
                # Serialize the modified curriculum back into JSON
                # so it can be fed as curriculum_json input
                curriculum_json = json.dumps({
                    "title": modified["title"],
                    "description": modified["description"],
                    "modules": modified["modules"],
                })
                st.session_state.training_input_content = curriculum_json
                st.session_state.training_input_type = "curriculum_json"
                st.success(
                    "Modified curriculum saved. Switch to the Build tab "
                    "and click Build to regenerate with updated content."
                )

        with action_col3:
            # Export curriculum as JSON
            curriculum_export = json.dumps(modified, indent=2)
            st.download_button(
                "Export Curriculum JSON",
                data=curriculum_export,
                file_name=f"curriculum_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key="cp_export_json",
            )


# =========================================================================
# TAB 3: Quick Generate
# =========================================================================

with tab_quick:
    st.markdown(
        "Generate individual training components without running the full pipeline."
    )

    quick_section = st.selectbox(
        "Generator",
        ["Quick Quiz", "Quick Microlearning", "Quick Agent Script"],
        key="tq_section_select",
    )

    st.divider()

    # -----------------------------------------------------------------
    # Quick Quiz
    # -----------------------------------------------------------------
    if quick_section == "Quick Quiz":
        st.subheader("Quick Quiz Generator")
        st.markdown(
            "Generate a standalone assessment quiz from any training content."
        )

        qq_col1, qq_col2 = st.columns([2, 1])

        with qq_col1:
            qq_content = st.text_area(
                "Training Content for Quiz",
                height=250,
                placeholder=(
                    "Paste the training content or topic material that the "
                    "quiz questions should be based on..."
                ),
                key="qq_content",
            )
            qq_title = st.text_input(
                "Quiz Title",
                placeholder="e.g., Module 1 Assessment - Customer Service Basics",
                key="qq_title",
            )

        with qq_col2:
            qq_count = st.slider(
                "Number of Questions",
                min_value=5,
                max_value=30,
                value=10,
                key="qq_count",
            )
            qq_difficulty = st.selectbox(
                "Difficulty Level",
                ["Comprehension", "Application", "Analysis"],
                key="qq_difficulty",
            )
            qq_types = st.multiselect(
                "Question Types",
                QUESTION_TYPES,
                default=["Multiple Choice", "True/False"],
                key="qq_types",
            )
            if not qq_types:
                qq_types = ["Multiple Choice"]

            qq_format = st.selectbox(
                "Output Format",
                ["DOCX", "PPTX", "JSON"],
                key="qq_format",
            )

        qq_disabled = not qq_content.strip() or not QUIZ_AVAILABLE
        if not QUIZ_AVAILABLE:
            st.warning(
                "Quiz Generator is not available. Ensure "
                "`app.generators.quiz_gen` is importable."
            )

        if st.button(
            "Generate Quiz",
            type="primary",
            disabled=qq_disabled,
            key="qq_generate",
        ):
            with st.spinner("Generating quiz..."):
                start = time.time()
                try:
                    generator = QuizGenerator()
                    result = generator.generate(
                        curriculum_content=qq_content,
                        question_count=qq_count,
                        difficulty=qq_difficulty,
                        question_types=qq_types,
                        title=qq_title or "Quick Quiz",
                        output_format=qq_format.lower(),
                    )
                    elapsed = time.time() - start

                    st.session_state.quick_quiz_result = {
                        "result": result,
                        "time": elapsed,
                        "title": qq_title or "Quick Quiz",
                        "format": qq_format,
                    }

                    # Save to DB
                    output_path = result.get("output_path", "")
                    _save_to_db(
                        title=qq_title or "Quick Quiz",
                        content_type="quiz",
                        output_path=output_path,
                        file_format=qq_format,
                        gen_time=elapsed,
                        input_summary=qq_content[:500],
                    )
                    st.session_state.training_session_count += 1
                    st.rerun()

                except Exception as e:
                    st.error(f"Quiz generation failed: {e}")

        # Show quiz results
        if st.session_state.quick_quiz_result:
            qr = st.session_state.quick_quiz_result
            st.success(
                f"Quiz generated in {qr['time']:.1f}s - "
                f"{qr['result'].get('question_count', '?')} questions"
            )

            result_data = qr["result"]
            out_path = result_data.get("output_path", "")
            if out_path and Path(out_path).exists():
                with open(out_path, "rb") as f:
                    st.download_button(
                        f"Download Quiz ({qr['format']})",
                        data=f.read(),
                        file_name=Path(out_path).name,
                        mime="application/octet-stream",
                        key="qq_download",
                    )

            # Preview questions if available
            questions = result_data.get("questions", [])
            if questions:
                with st.expander("Preview Questions", expanded=True):
                    for q_idx, question in enumerate(questions[:5], 1):
                        q_text = (
                            question.get("question", "")
                            if isinstance(question, dict)
                            else str(question)
                        )
                        q_type = (
                            question.get("type", "")
                            if isinstance(question, dict)
                            else ""
                        )
                        st.markdown(
                            f"**Q{q_idx}** ({q_type}): {q_text}"
                        )
                        if isinstance(question, dict) and question.get("options"):
                            for opt in question["options"]:
                                st.markdown(f"   - {opt}")
                        st.markdown("---")
                    if len(questions) > 5:
                        st.caption(
                            f"Showing 5 of {len(questions)} questions. "
                            "Download the full file for all questions."
                        )

    # -----------------------------------------------------------------
    # Quick Microlearning
    # -----------------------------------------------------------------
    elif quick_section == "Quick Microlearning":
        st.subheader("Quick Microlearning Generator")
        st.markdown(
            "Break training content into bite-sized microlearning modules."
        )

        qm_col1, qm_col2 = st.columns([2, 1])

        with qm_col1:
            qm_content = st.text_area(
                "Training Content to Chunk",
                height=250,
                placeholder=(
                    "Paste training content to break into micro-modules. "
                    "The generator will identify key concepts and create "
                    "focused, bite-sized learning units..."
                ),
                key="qm_content",
            )
            qm_title = st.text_input(
                "Series Title",
                placeholder="e.g., Customer Service Essentials Micro-Series",
                key="qm_title",
            )

        with qm_col2:
            qm_duration = st.slider(
                "Module Duration (minutes)",
                min_value=3,
                max_value=15,
                value=7,
                key="qm_duration",
            )
            qm_format = st.selectbox(
                "Output Format",
                ["1-Page PDFs", "Slide Decks", "Email Content"],
                key="qm_format",
            )

        qm_disabled = not qm_content.strip() or not MICROLEARNING_AVAILABLE
        if not MICROLEARNING_AVAILABLE:
            st.warning(
                "Microlearning Generator is not available. Ensure "
                "`app.generators.microlearning_gen` is importable."
            )

        if st.button(
            "Generate Microlearning",
            type="primary",
            disabled=qm_disabled,
            key="qm_generate",
        ):
            with st.spinner("Generating microlearning modules..."):
                start = time.time()
                try:
                    generator = MicrolearningGenerator()
                    result = generator.generate(
                        curriculum_content=qm_content,
                        module_duration=qm_duration,
                        output_format=qm_format.lower().replace(" ", "_"),
                        title=qm_title or "Microlearning Series",
                    )
                    elapsed = time.time() - start

                    st.session_state.quick_micro_result = {
                        "result": result,
                        "time": elapsed,
                        "title": qm_title or "Microlearning Series",
                        "format": qm_format,
                    }

                    output_path = result.get("output_path", "")
                    _save_to_db(
                        title=qm_title or "Microlearning Series",
                        content_type="microlearning",
                        output_path=output_path,
                        file_format=qm_format,
                        gen_time=elapsed,
                        input_summary=qm_content[:500],
                    )
                    st.session_state.training_session_count += 1
                    st.rerun()

                except Exception as e:
                    st.error(f"Microlearning generation failed: {e}")

        # Show microlearning results
        if st.session_state.quick_micro_result:
            mr = st.session_state.quick_micro_result
            result_data = mr["result"]
            module_count = result_data.get("module_count", "?")
            st.success(
                f"Generated {module_count} microlearning modules "
                f"in {mr['time']:.1f}s"
            )

            # Download individual modules or full package
            out_path = result_data.get("output_path", "")
            if out_path and Path(out_path).exists():
                with open(out_path, "rb") as f:
                    st.download_button(
                        f"Download Microlearning Package ({mr['format']})",
                        data=f.read(),
                        file_name=Path(out_path).name,
                        mime="application/octet-stream",
                        key="qm_download",
                    )

            # Preview modules if available
            modules_preview = result_data.get("modules", [])
            if modules_preview:
                with st.expander("Preview Modules", expanded=True):
                    for mod_idx, mod in enumerate(modules_preview[:6], 1):
                        mod_title = (
                            mod.get("title", f"Module {mod_idx}")
                            if isinstance(mod, dict)
                            else f"Module {mod_idx}"
                        )
                        mod_summary = (
                            mod.get("summary", "")
                            if isinstance(mod, dict)
                            else str(mod)
                        )
                        mod_dur = (
                            mod.get("duration_minutes", qm_duration)
                            if isinstance(mod, dict)
                            else qm_duration
                        )
                        st.markdown(
                            f'<div class="module-card">'
                            f"<strong>{mod_title}</strong> "
                            f"<em>({mod_dur} min)</em><br>"
                            f"<span style='color:#666;'>{mod_summary[:200]}</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                    if len(modules_preview) > 6:
                        st.caption(
                            f"Showing 6 of {len(modules_preview)} modules."
                        )

    # -----------------------------------------------------------------
    # Quick Agent Script
    # -----------------------------------------------------------------
    elif quick_section == "Quick Agent Script":
        st.subheader("Quick Agent Script Generator")
        st.markdown(
            "Generate a sales or call center agent script with objection "
            "handling and compliance callouts."
        )

        qs_col1, qs_col2 = st.columns([2, 1])

        with qs_col1:
            qs_product = st.text_area(
                "Product / Service Description",
                height=150,
                placeholder=(
                    "Describe the product or service in detail: features, "
                    "benefits, pricing tiers, competitive advantages..."
                ),
                key="qs_product",
            )
            qs_objectives = st.text_area(
                "Call Objectives",
                height=100,
                placeholder=(
                    "What should the agent accomplish? e.g., schedule demo, "
                    "close sale, gather qualification info, upsell..."
                ),
                key="qs_objectives",
            )

        with qs_col2:
            qs_features = st.text_area(
                "Key Features / Benefits",
                height=150,
                placeholder=(
                    "List key selling points, features, and benefits "
                    "the agent should highlight during the call..."
                ),
                key="qs_features",
            )
            qs_title = st.text_input(
                "Script Title",
                placeholder="e.g., Premium Plan Outbound Sales Script",
                key="qs_title",
            )

        qs_disabled = (
            not qs_product.strip()
            or not qs_features.strip()
            or not PIPELINE_AVAILABLE
        )
        if not PIPELINE_AVAILABLE:
            st.warning(
                "Training Pipeline (agent script generator) is not available."
            )

        if st.button(
            "Generate Agent Script",
            type="primary",
            disabled=qs_disabled,
            key="qs_generate",
        ):
            with st.spinner("Generating agent script..."):
                start = time.time()
                try:
                    # Build a curriculum-like input from the features/benefits
                    combined_content = (
                        f"Product/Service: {qs_product}\n\n"
                        f"Key Features and Benefits:\n{qs_features}\n\n"
                        f"Call Objectives:\n{qs_objectives}"
                    )

                    pipeline = TrainingPipeline()
                    opts = PipelineOptions(
                        training_deck=False,
                        facilitator_guide=False,
                        participant_handouts=False,
                        job_aids=False,
                        quiz=False,
                        microlearning=False,
                        agent_script=True,
                        quiz_question_count=10,
                        quiz_difficulty="Comprehension",
                        quiz_question_types=["Multiple Choice"],
                        module_duration_minutes=7,
                        product_info=qs_product,
                        call_objectives=qs_objectives,
                        language="English",
                        training_type="Sales Training",
                        audience_level="Intermediate",
                    )

                    package = pipeline.process_curriculum(
                        combined_content, "text", opts
                    )
                    elapsed = time.time() - start

                    script_path = getattr(package, "agent_script", None)
                    st.session_state.quick_script_result = {
                        "path": str(script_path) if script_path else "",
                        "time": elapsed,
                        "title": qs_title or "Agent Script",
                    }

                    if script_path:
                        _save_to_db(
                            title=qs_title or "Agent Script",
                            content_type="agent_script",
                            output_path=str(script_path),
                            file_format="DOCX",
                            gen_time=elapsed,
                            input_summary=combined_content[:500],
                        )
                    st.session_state.training_session_count += 1
                    st.rerun()

                except Exception as e:
                    st.error(f"Agent script generation failed: {e}")

        # Show script results
        if st.session_state.quick_script_result:
            sr = st.session_state.quick_script_result
            st.success(
                f"Agent script generated in {sr['time']:.1f}s"
            )
            out_path = sr.get("path", "")
            if out_path and Path(out_path).exists():
                with open(out_path, "rb") as f:
                    st.download_button(
                        "Download Agent Script (DOCX)",
                        data=f.read(),
                        file_name=Path(out_path).name,
                        mime="application/vnd.openxmlformats-officedocument"
                             ".wordprocessingml.document",
                        key="qs_download",
                    )


# =========================================================================
# TAB 4: History
# =========================================================================

with tab_history:
    st.subheader("Training Content History")

    if not DB_AVAILABLE:
        st.warning(
            "Database is not available. History requires "
            "`app.database.models` to be importable."
        )
    else:
        # Refresh trigger
        if st.button("Refresh", key="th_refresh"):
            st.session_state.training_history_refresh += 1

        training_content_types = [
            "training_deck",
            "facilitator_guide",
            "participant_handout",
            "participant_handouts",
            "job_aid",
            "job_aids",
            "quiz",
            "microlearning",
            "agent_script",
            "training_package",
        ]

        # Filter controls
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            type_filter = st.selectbox(
                "Filter by Type",
                ["All"] + [
                    "Training Deck",
                    "Facilitator Guide",
                    "Participant Handout",
                    "Job Aid",
                    "Quiz",
                    "Microlearning",
                    "Agent Script",
                    "Training Package",
                ],
                key="th_type_filter",
            )
        with filter_col2:
            sort_order = st.selectbox(
                "Sort By",
                ["Newest First", "Oldest First"],
                key="th_sort_order",
            )

        try:
            session = get_session()
            query = session.query(GeneratedContent).filter(
                GeneratedContent.content_type.in_(training_content_types)
            )

            # Apply type filter
            if type_filter != "All":
                filter_type = type_filter.lower().replace(" ", "_")
                query = query.filter(
                    GeneratedContent.content_type == filter_type
                )

            # Apply sort
            if sort_order == "Newest First":
                query = query.order_by(GeneratedContent.generated_at.desc())
            else:
                query = query.order_by(GeneratedContent.generated_at.asc())

            records = query.limit(50).all()
            session.close()

            if not records:
                st.info(
                    "No training content history found. Generate some "
                    "training materials to see them here."
                )
            else:
                st.caption(f"Showing {len(records)} record(s)")

                for rec in records:
                    rec_col1, rec_col2, rec_col3, rec_col4 = st.columns(
                        [3, 1.5, 1.5, 2]
                    )

                    with rec_col1:
                        st.markdown(f"**{rec.title}**")
                        badge_html = _output_type_badge(rec.content_type)
                        st.markdown(badge_html, unsafe_allow_html=True)

                    with rec_col2:
                        gen_at = rec.generated_at
                        if gen_at:
                            st.caption(gen_at.strftime("%Y-%m-%d %H:%M"))
                        else:
                            st.caption("N/A")

                    with rec_col3:
                        if rec.generation_time_seconds:
                            st.caption(
                                f"Generated in {rec.generation_time_seconds:.1f}s"
                            )
                        if rec.format:
                            st.caption(f"Format: {rec.format}")

                    with rec_col4:
                        btn_cols = st.columns(3)

                        # Download button
                        with btn_cols[0]:
                            out_path = rec.output_path
                            if out_path and Path(out_path).exists():
                                with open(out_path, "rb") as f:
                                    st.download_button(
                                        "DL",
                                        data=f.read(),
                                        file_name=Path(out_path).name,
                                        mime="application/octet-stream",
                                        key=f"th_dl_{rec.id}",
                                        help="Download file",
                                    )
                            else:
                                st.button(
                                    "DL",
                                    disabled=True,
                                    key=f"th_dl_na_{rec.id}",
                                    help="File not found",
                                )

                        # Add to Library button
                        with btn_cols[1]:
                            if st.button(
                                "Lib",
                                key=f"th_lib_{rec.id}",
                                help="Add to Content Library",
                            ):
                                success = _add_to_library(
                                    content_id=rec.id,
                                    title=rec.title,
                                    category=rec.content_type,
                                )
                                if success:
                                    st.toast(
                                        f"Added '{rec.title}' to library"
                                    )
                                else:
                                    st.toast(
                                        "Failed to add to library",
                                        icon="!",
                                    )

                        # Delete button
                        with btn_cols[2]:
                            if st.button(
                                "Del",
                                key=f"th_del_{rec.id}",
                                help="Delete record",
                            ):
                                try:
                                    del_session = get_session()
                                    item = del_session.query(
                                        GeneratedContent
                                    ).get(rec.id)
                                    if item:
                                        # Remove physical file
                                        if (
                                            item.output_path
                                            and Path(item.output_path).exists()
                                        ):
                                            try:
                                                Path(item.output_path).unlink()
                                            except OSError:
                                                pass
                                        del_session.delete(item)
                                        del_session.commit()
                                        st.toast(
                                            f"Deleted '{rec.title}'"
                                        )
                                    del_session.close()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Delete failed: {e}")

                    st.divider()

        except Exception as e:
            st.error(f"Failed to load history: {e}")
            logger.warning("History query failed: %s", e)
