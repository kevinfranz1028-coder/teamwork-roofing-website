"""
Brand Intelligence Content Hub - Content Generator

Unified content generation page that provides quick-access forms for
creating branded presentations, documents, training packages, and visuals.
Uses the same generators that power the Copilot, but with a form-based UI.
"""

import json
import os
import sys
import time
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Content Generator",
    page_icon="\U0001f4dd",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Imports (graceful degradation)
# ---------------------------------------------------------------------------
from app.config import BASE_DIR, BRAND_ASSETS_DIR, OUTPUT_DIR, UPLOADS_DIR
from app.database.models import init_db, get_session, GeneratedContent

try:
    from app.generators.presentation_gen import BrandedPresentationGenerator
    PRES_AVAILABLE = True
except ImportError:
    PRES_AVAILABLE = False

try:
    from app.generators.document_gen import BrandedDocumentGenerator, DOCUMENT_TEMPLATES
    DOC_AVAILABLE = True
except ImportError:
    DOC_AVAILABLE = False
    DOCUMENT_TEMPLATES = {}

try:
    from app.generators.visual_gen import VisualPipeline
    VIS_AVAILABLE = True
except ImportError:
    VIS_AVAILABLE = False

try:
    from app.generators.training_pipeline import TrainingPipeline, PipelineOptions
    TRAIN_AVAILABLE = True
except ImportError:
    TRAIN_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None
    ANTHROPIC_AVAILABLE = False

# ---------------------------------------------------------------------------
# Initialise database
# ---------------------------------------------------------------------------
if "db_ok" not in st.session_state:
    try:
        init_db()
        st.session_state["db_ok"] = True
    except Exception:
        st.session_state["db_ok"] = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CLAUDE_MODEL = "claude-sonnet-4-20250514"
BRAND_CONFIG_PATH = BRAND_ASSETS_DIR / "brand_config.json"


def _load_brand_config() -> dict:
    if BRAND_CONFIG_PATH.exists():
        try:
            return json.loads(BRAND_CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _get_anthropic_client():
    if not ANTHROPIC_AVAILABLE:
        return None
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    try:
        return Anthropic(api_key=api_key)
    except Exception:
        return None


def _parse_json_response(raw: str):
    """Parse JSON from Claude, stripping markdown fences."""
    text = raw.strip()
    if text.startswith("```"):
        first_nl = text.find("\n")
        if first_nl != -1:
            text = text[first_nl + 1:]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3].rstrip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for o, c in [("{", "}"), ("[", "]")]:
        s, e = text.find(o), text.rfind(c)
        if s != -1 and e > s:
            try:
                return json.loads(text[s:e + 1])
            except json.JSONDecodeError:
                continue
    return {}


def _record_generation(title, content_type, output_path, fmt, gen_time, summary=""):
    session = get_session()
    try:
        rec = GeneratedContent(
            title=title, content_type=content_type,
            output_path=str(output_path), format=fmt,
            generation_time_seconds=round(gen_time, 2),
            input_summary=summary[:500] if summary else "",
        )
        session.add(rec)
        session.commit()
        return rec.id
    except Exception:
        session.rollback()
        return -1
    finally:
        session.close()


def _file_size_str(path: str) -> str:
    try:
        size = os.path.getsize(path)
    except OSError:
        return "unknown"
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _read_uploaded_file(uploaded_file) -> str:
    """Read text from an uploaded file."""
    name = uploaded_file.name.lower()
    if name.endswith(".txt") or name.endswith(".md"):
        return uploaded_file.read().decode("utf-8", errors="replace")
    elif name.endswith(".csv"):
        return uploaded_file.read().decode("utf-8", errors="replace")
    else:
        # For PDF/DOCX/PPTX, save temporarily and use parsers
        dest = UPLOADS_DIR / uploaded_file.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(uploaded_file.getbuffer())
        try:
            if name.endswith(".pdf"):
                from app.ingestion.pdf_parser import PDFParser
                return PDFParser().parse(str(dest)).get("text", "")
            elif name.endswith(".docx"):
                from app.ingestion.docx_parser import DOCXParser
                return DOCXParser().parse(str(dest)).get("text", "")
            elif name.endswith(".pptx"):
                from app.ingestion.pptx_parser import PPTXParser
                result = PPTXParser().parse(str(dest))
                parts = []
                for slide in result.get("slides", []):
                    if slide.get("title"):
                        parts.append(slide["title"])
                    parts.extend(slide.get("content", []))
                return "\n\n".join(parts)
        except ImportError:
            return f"[Could not parse {uploaded_file.name} — parser not installed]"
    return ""


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.title("\U0001f4dd Content Generator")
st.caption("Create branded content using AI-powered generators")

brand_cfg = _load_brand_config()
company = brand_cfg.get("company_name", "")
if company:
    st.markdown(f"Generating content for **{company}**")

client = _get_anthropic_client()
if not client:
    st.warning(
        "Anthropic API key not configured. Set it on the **Settings** page "
        "or in your `.env` file to enable AI content generation."
    )

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_pres, tab_doc, tab_train, tab_vis = st.tabs([
    "\U0001f4ca Presentations",
    "\U0001f4c4 Documents",
    "\U0001f4da Training Packages",
    "\U0001f5bc\ufe0f Visuals",
])

# ===== PRESENTATIONS TAB ===================================================
with tab_pres:
    st.subheader("Create a Branded Presentation")

    if not PRES_AVAILABLE:
        st.info("Presentation generator requires `python-pptx`. Install it to enable this feature.")
    else:
        with st.form("pres_form"):
            pres_title = st.text_input("Presentation Title", placeholder="e.g., Q1 Business Review")
            pres_type = st.selectbox(
                "Presentation Type",
                ["general", "training_deck", "client_pitch", "qbr", "program_rollout"],
                format_func=lambda x: x.replace("_", " ").title(),
            )
            pres_slides = st.slider("Number of Slides", 3, 25, 8)

            pres_content = st.text_area(
                "Content / Topic Description",
                height=150,
                placeholder="Describe what the presentation should cover, or paste raw content...",
            )
            pres_file = st.file_uploader(
                "Or upload source material",
                type=["txt", "md", "pdf", "docx", "pptx", "csv"],
                key="pres_upload",
            )
            pres_instructions = st.text_input(
                "Additional Instructions",
                placeholder="e.g., Emphasize ROI, keep it concise",
            )

            submitted = st.form_submit_button("\U0001f680 Generate Presentation", type="primary")

        if submitted:
            content = pres_content
            if pres_file and not content:
                content = _read_uploaded_file(pres_file)

            if not content:
                st.error("Please provide content or upload a source file.")
            elif not client:
                st.error("Anthropic API key required for content generation.")
            else:
                with st.spinner(f"Generating {pres_slides}-slide presentation..."):
                    try:
                        start = time.time()

                        # Generate slide data via Claude
                        system_prompt = (
                            "You are a presentation architect. Return a JSON array of slide objects.\n"
                            "Each slide MUST have: \"layout\" (title/content/two_column/section/closing), \"title\".\n"
                            "May have: \"body\", \"bullets\" (array), \"subtitle\", \"speaker_notes\", \"columns\".\n"
                            "Return ONLY the JSON array."
                        )
                        resp = client.messages.create(
                            model=CLAUDE_MODEL, max_tokens=4096, system=system_prompt,
                            messages=[{"role": "user", "content": (
                                f"Create a {pres_slides}-slide {pres_type} presentation "
                                f'titled "{pres_title}".\n\nContent:\n{content[:8000]}\n\n'
                                f"Instructions: {pres_instructions}" if pres_instructions else ""
                            )}],
                        )
                        slides_data = _parse_json_response(resp.content[0].text)
                        if isinstance(slides_data, dict):
                            slides_data = slides_data.get("slides", [])

                        # Build PPTX
                        gen = BrandedPresentationGenerator()
                        output_path = gen.generate(slides_data=slides_data, title=pres_title)
                        elapsed = time.time() - start

                        _record_generation(pres_title, "presentation", output_path, "pptx", elapsed, content[:300])

                        st.success(f"Presentation generated in {elapsed:.1f}s!")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Slides", len(slides_data))
                        with col2:
                            st.metric("File Size", _file_size_str(str(output_path)))

                        with open(str(output_path), "rb") as f:
                            st.download_button(
                                "\u2b07\ufe0f Download Presentation",
                                data=f.read(),
                                file_name=Path(output_path).name,
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                use_container_width=True,
                            )
                    except Exception as exc:
                        st.error(f"Generation failed: {exc}")

# ===== DOCUMENTS TAB =======================================================
with tab_doc:
    st.subheader("Create a Branded Document")

    if not DOC_AVAILABLE:
        st.info("Document generator requires `python-docx`. Install it to enable this feature.")
    else:
        doc_types = list(DOCUMENT_TEMPLATES.keys()) if DOCUMENT_TEMPLATES else [
            "job_aid", "case_study", "weekly_report", "monthly_report",
            "sop", "training_guide", "internal_memo", "battle_card",
            "capability_overview", "proposal",
        ]

        with st.form("doc_form"):
            doc_title = st.text_input("Document Title", placeholder="e.g., Customer Onboarding SOP")
            doc_type = st.selectbox(
                "Document Type", doc_types,
                format_func=lambda x: x.replace("_", " ").title(),
            )
            doc_format = st.selectbox("Output Format", ["docx", "pdf", "both"])

            doc_content = st.text_area(
                "Content / Topic Description",
                height=150,
                placeholder="Describe the document content, or paste raw text...",
            )
            doc_file = st.file_uploader(
                "Or upload source material",
                type=["txt", "md", "pdf", "docx", "csv"],
                key="doc_upload",
            )
            doc_data = st.text_area(
                "Structured Data (optional)",
                height=80,
                placeholder="Paste JSON, CSV, or key-value pairs for reports...",
            )
            doc_instructions = st.text_input(
                "Additional Instructions",
                placeholder="e.g., Keep under 3 pages, include metrics",
            )

            submitted = st.form_submit_button("\U0001f680 Generate Document", type="primary")

        if submitted:
            content = doc_content
            if doc_file and not content:
                content = _read_uploaded_file(doc_file)

            if not content:
                st.error("Please provide content or upload a source file.")
            elif not client:
                st.error("Anthropic API key required for content generation.")
            else:
                with st.spinner(f"Generating {doc_type.replace('_', ' ')} document..."):
                    try:
                        start = time.time()

                        # Generate structured content via Claude
                        system_prompt = (
                            f"You are a document architect. Generate structured JSON content "
                            f"for a '{doc_type}' document. Include a 'title' key. "
                            f"Return ONLY the JSON object."
                        )
                        user_msg = f'Generate content for "{doc_title}" (type: {doc_type}).\n\nContent:\n{content[:8000]}'
                        if doc_data:
                            user_msg += f"\n\nData:\n{doc_data[:4000]}"
                        if doc_instructions:
                            user_msg += f"\n\nInstructions: {doc_instructions}"

                        resp = client.messages.create(
                            model=CLAUDE_MODEL, max_tokens=4096, system=system_prompt,
                            messages=[{"role": "user", "content": user_msg}],
                        )
                        content_dict = _parse_json_response(resp.content[0].text)
                        if not isinstance(content_dict, dict):
                            content_dict = {"title": doc_title, "body": str(content_dict)}
                        if "title" not in content_dict:
                            content_dict["title"] = doc_title

                        gen = BrandedDocumentGenerator()
                        output_path = gen.generate(
                            content=content_dict, doc_type=doc_type, title=doc_title,
                        )
                        elapsed = time.time() - start

                        _record_generation(doc_title, "document", output_path, "docx", elapsed, content[:300])

                        st.success(f"Document generated in {elapsed:.1f}s!")
                        st.metric("File Size", _file_size_str(str(output_path)))

                        with open(str(output_path), "rb") as f:
                            st.download_button(
                                "\u2b07\ufe0f Download Document",
                                data=f.read(),
                                file_name=Path(output_path).name,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True,
                            )
                    except Exception as exc:
                        st.error(f"Generation failed: {exc}")

# ===== TRAINING TAB ========================================================
with tab_train:
    st.subheader("Create a Training Package")

    if not TRAIN_AVAILABLE:
        st.info("Training pipeline not available. Check dependencies.")
    else:
        with st.form("train_form"):
            train_title = st.text_input("Training Program Title", placeholder="e.g., New Hire Onboarding")
            train_type = st.selectbox(
                "Training Type",
                ["product_training", "compliance", "onboarding", "sales_training", "process_training", "general"],
                format_func=lambda x: x.replace("_", " ").title(),
            )
            train_audience = st.selectbox(
                "Target Audience",
                ["new_hires", "experienced_agents", "managers", "clients", "general"],
                format_func=lambda x: x.replace("_", " ").title(),
            )

            train_outputs = st.multiselect(
                "Deliverables to Generate",
                ["training_deck", "facilitator_guide", "participant_handout", "job_aids", "quiz", "microlearning", "agent_script"],
                default=["training_deck", "facilitator_guide", "job_aids", "quiz"],
                format_func=lambda x: x.replace("_", " ").title(),
            )

            train_content = st.text_area(
                "Curriculum Content",
                height=200,
                placeholder="Paste curriculum, knowledge base content, or describe the training topic...",
            )
            train_file = st.file_uploader(
                "Or upload source material",
                type=["txt", "md", "pdf", "docx", "pptx"],
                key="train_upload",
            )

            submitted = st.form_submit_button("\U0001f680 Generate Training Package", type="primary")

        if submitted:
            content = train_content
            if train_file and not content:
                content = _read_uploaded_file(train_file)

            if not content:
                st.error("Please provide curriculum content or upload source material.")
            else:
                with st.spinner("Generating training package (this may take a minute)..."):
                    try:
                        start = time.time()
                        options = PipelineOptions(
                            training_type=train_type,
                            audience_level=train_audience,
                        )
                        # Set requested outputs
                        for field in ["training_deck", "facilitator_guide", "participant_handouts",
                                      "job_aids", "quiz", "microlearning", "agent_script"]:
                            setattr(options, field, False)
                        output_map = {
                            "training_deck": "training_deck", "facilitator_guide": "facilitator_guide",
                            "participant_handout": "participant_handouts", "job_aids": "job_aids",
                            "quiz": "quiz", "microlearning": "microlearning", "agent_script": "agent_script",
                        }
                        for out in train_outputs:
                            mapped = output_map.get(out)
                            if mapped:
                                setattr(options, mapped, True)

                        pipeline = TrainingPipeline()
                        package = pipeline.process_curriculum(
                            input_content=content, input_type="text", options=options,
                        )
                        elapsed = time.time() - start

                        if package.zip_path:
                            _record_generation(train_title, "training_package", str(package.zip_path), "zip", elapsed, content[:300])

                        st.success(f"Training package generated in {elapsed:.1f}s!")

                        cols = st.columns(3)
                        with cols[0]:
                            st.metric("Deliverables", len(package.outputs))
                        with cols[1]:
                            st.metric("Time", f"{elapsed:.1f}s")
                        with cols[2]:
                            if package.zip_path:
                                st.metric("Package Size", _file_size_str(str(package.zip_path)))

                        st.markdown("**Generated Files:**")
                        for out_type, fpath in package.outputs.items():
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.markdown(f"- {out_type.replace('_', ' ').title()}")
                            with col_b:
                                if os.path.exists(str(fpath)):
                                    with open(str(fpath), "rb") as f:
                                        st.download_button(
                                            "\u2b07\ufe0f",
                                            data=f.read(),
                                            file_name=Path(fpath).name,
                                            key=f"dl_train_{out_type}",
                                        )

                        if package.zip_path and os.path.exists(str(package.zip_path)):
                            with open(str(package.zip_path), "rb") as f:
                                st.download_button(
                                    "\U0001f4e6 Download Complete Package (ZIP)",
                                    data=f.read(),
                                    file_name=Path(package.zip_path).name,
                                    mime="application/zip",
                                    use_container_width=True,
                                )

                        if package.errors:
                            with st.expander("Warnings", expanded=False):
                                for err in package.errors:
                                    st.warning(err)

                    except Exception as exc:
                        st.error(f"Generation failed: {exc}")

# ===== VISUALS TAB ==========================================================
with tab_vis:
    st.subheader("Create a Visual / Diagram")

    if not VIS_AVAILABLE:
        st.info("Visual pipeline not available. Check dependencies.")
    else:
        with st.form("vis_form"):
            vis_type = st.selectbox(
                "Visual Type",
                ["flowchart", "mind_map", "timeline", "org_chart", "process_diagram", "infographic", "comparison_chart", "auto"],
                format_func=lambda x: x.replace("_", " ").title(),
            )
            vis_format = st.selectbox("Output Format", ["png", "svg", "ppt"])
            vis_desc = st.text_area(
                "Visual Description",
                height=150,
                placeholder="Describe the visual in detail — include all data points, labels, and relationships...",
            )

            submitted = st.form_submit_button("\U0001f680 Generate Visual", type="primary")

        if submitted:
            if not vis_desc:
                st.error("Please describe the visual you want to create.")
            else:
                with st.spinner("Generating visual..."):
                    try:
                        start = time.time()
                        pipeline = VisualPipeline()
                        result = pipeline.generate_visual(
                            description=vis_desc,
                            visual_type=vis_type,
                            output_format=vis_format,
                        )
                        elapsed = time.time() - start

                        if result.get("success"):
                            fpath = result.get("file_path", "")
                            _record_generation(
                                f"Visual: {vis_type}", "visual", fpath,
                                vis_format, elapsed, vis_desc[:300],
                            )
                            st.success(f"Visual generated in {elapsed:.1f}s!")

                            if fpath and os.path.exists(fpath):
                                if vis_format in ("png", "svg", "jpg"):
                                    st.image(fpath, caption=f"{vis_type.replace('_', ' ').title()}")
                                st.metric("File Size", _file_size_str(fpath))
                                with open(fpath, "rb") as f:
                                    st.download_button(
                                        "\u2b07\ufe0f Download Visual",
                                        data=f.read(),
                                        file_name=Path(fpath).name,
                                        use_container_width=True,
                                    )
                        else:
                            st.error(result.get("error", "Visual generation failed."))
                    except Exception as exc:
                        st.error(f"Generation failed: {exc}")

# ---------------------------------------------------------------------------
# Recent generations sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Recent Generations")
    try:
        session = get_session()
        try:
            recent = (
                session.query(GeneratedContent)
                .order_by(GeneratedContent.generated_at.desc())
                .limit(5)
                .all()
            )
            if recent:
                for item in recent:
                    st.caption(
                        f"{'📊' if item.content_type == 'presentation' else '📄' if item.content_type == 'document' else '📚' if item.content_type == 'training_package' else '🖼️'} "
                        f"**{item.title}** — {item.generated_at.strftime('%b %d') if item.generated_at else ''}"
                    )
            else:
                st.caption("No content generated yet.")
        finally:
            session.close()
    except Exception:
        st.caption("Could not load recent generations.")
