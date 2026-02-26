"""
Brand Intelligence Content Hub - Presentation Studio

Interactive workspace for generating, previewing, importing templates,
and managing AI-powered branded presentations.
"""

import json
import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from app.config import (
    BASE_DIR,
    BRAND_ASSETS_DIR,
    PRESENTATIONS_DIR,
    TEMPLATES_DIR,
    LOGOS_DIR,
    get_env,
)
from app.database.models import (
    get_session,
    Template,
    GeneratedContent,
    ContentLibraryItem,
)
from app.integrations.presenton_client import PresentonClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Presentation Studio", layout="wide")

st.markdown(
    """<style>
.slide-preview {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
    background: white;
}
.slide-number {
    background: #0066cc;
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
}
.type-badge {
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
}
.type-badge-title { background: #e8f0fe; color: #1a73e8; }
.type-badge-content { background: #e6f4ea; color: #137333; }
.type-badge-section { background: #fef7e0; color: #b06000; }
.type-badge-chart { background: #fce8e6; color: #c5221f; }
.type-badge-closing { background: #f3e8fd; color: #7627bb; }
.type-badge-quote { background: #e8eaed; color: #5f6368; }
.stProgress > div > div > div > div { background-color: #0066cc; }
.metric-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
    border: 1px solid #e0e0e0;
}
</style>""",
    unsafe_allow_html=True,
)

st.title("Presentation Studio")
st.markdown("Generate professional, branded presentations powered by AI")

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "generated_slides" not in st.session_state:
    st.session_state.generated_slides = None
if "generated_title" not in st.session_state:
    st.session_state.generated_title = None
if "generated_file_path" not in st.session_state:
    st.session_state.generated_file_path = None
if "generation_time" not in st.session_state:
    st.session_state.generation_time = None
if "slide_count_actual" not in st.session_state:
    st.session_state.slide_count_actual = 0


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
# Helper: build slide generation prompt
# ---------------------------------------------------------------------------

def build_slide_generation_prompt(
    pres_type: str,
    content: str,
    n_slides: int,
    include_notes: bool,
    include_visuals: bool,
    brand_config: dict,
) -> str:
    """Return the system prompt for Claude to generate slide JSON."""

    type_structures = {
        "Training Module": (
            "Structure: Title slide, Learning Objectives, 2-4 Content sections "
            "(each with section divider + 1-3 content slides), Activity/Exercise "
            "slide, Key Takeaways/Recap, Closing"
        ),
        "Client Pitch": (
            "Structure: Title slide, Problem/Challenge, Market Opportunity, "
            "Our Solution, Key Benefits (2-3 slides), Case Study/Social Proof, "
            "Implementation Approach, Pricing/Investment, Call to Action, Closing"
        ),
        "Quarterly Business Review (QBR)": (
            "Structure: Title slide, Executive Summary, Key Metrics Dashboard, "
            "Revenue/Performance Data (chart), Achievements & Wins, Challenges & "
            "Lessons, Customer Highlights, Strategic Initiatives, Next Quarter Goals, Closing"
        ),
        "General Presentation": (
            "Structure: Title slide, Agenda/Overview, Content sections as "
            "appropriate, Summary, Closing"
        ),
        "Program Rollout": (
            "Structure: Title slide, Program Overview, Objectives & Goals, "
            "Timeline/Phases, Roles & Responsibilities, Resources & Support, "
            "FAQ, Next Steps, Closing"
        ),
    }

    voice_context = ""
    if brand_config and brand_config.get("voice"):
        voice = brand_config["voice"]
        tone = voice.get("tone", "professional")
        formality = voice.get("formality", 3)
        key_phrases = ", ".join(voice.get("key_phrases", [])[:5])
        avoid_phrases = ", ".join(voice.get("avoid_phrases", [])[:5])
        voice_context = f"""
Brand Voice Guidelines:
- Tone: {tone}
- Formality: {formality}/5
- Key phrases to incorporate: {key_phrases}
- Phrases to avoid: {avoid_phrases}
"""

    notes_instruction = (
        "Include detailed speaker notes for each slide"
        if include_notes
        else "Omit speaker_notes field"
    )
    visuals_instruction = (
        "Include suggested_visual descriptions"
        if include_visuals
        else "Omit suggested_visual field"
    )

    system_prompt = f"""You are a professional presentation designer. Generate a structured slide deck as JSON.

{type_structures.get(pres_type, type_structures["General Presentation"])}

{voice_context}

Return ONLY valid JSON with this structure:
{{
  "title": "Presentation Title",
  "slides": [
    {{
      "layout": "title|section_divider|content|two_column|image_text|chart_data|quote_callout|closing",
      "title": "Slide Title",
      "bullets": ["bullet 1", "bullet 2"],
      "body": "paragraph text if no bullets",
      "speaker_notes": "detailed speaker notes for this slide",
      "suggested_visual": "description of a relevant image or diagram",
      "subtitle": "for title slides only",
      "columns": [{{"title": "Col 1", "bullets": ["..."]}}, {{"title": "Col 2", "bullets": ["..."]}}],
      "chart_data": {{"type": "bar|column|line|pie", "categories": ["..."], "series": [{{"name": "...", "values": [1,2,3]}}]}},
      "table_data": [["Header1", "Header2"], ["row1col1", "row1col2"]],
      "quote": "quote text",
      "attribution": "quote source"
    }}
  ]
}}

Rules:
- Generate exactly {n_slides} slides
- First slide must use "title" layout
- Last slide must use "closing" layout
- Use "section_divider" to separate major sections
- Each content slide should have 3-6 bullet points max
- {notes_instruction}
- {visuals_instruction}
- Only include fields relevant to each slide's layout
- Make content actionable, specific, and engaging
- Use data and metrics where appropriate (create realistic placeholder data for charts)
"""
    return system_prompt


# ---------------------------------------------------------------------------
# Helper: call Claude API
# ---------------------------------------------------------------------------

def call_claude(system_prompt: str, user_content: str) -> str:
    """Call the Anthropic Claude API and return the text response."""
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. Please configure it in your .env file."
        )

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    return message.content[0].text


# ---------------------------------------------------------------------------
# Helper: parse uploaded file content
# ---------------------------------------------------------------------------

def extract_uploaded_file_content(uploaded_file) -> str:
    """Read text from an uploaded file (.txt, .pdf, .docx, .pptx)."""
    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix == ".txt":
        return uploaded_file.read().decode("utf-8", errors="replace")

    # Save to a temp file so parsers can open by path
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        if suffix == ".pdf":
            from app.ingestion.pdf_parser import PDFParser
            result = PDFParser().parse(tmp_path)
            return result.get("text", "")

        if suffix in (".docx", ".docm"):
            from app.ingestion.docx_parser import DOCXParser
            result = DOCXParser().parse(tmp_path)
            return result.get("text", "")

        if suffix in (".pptx", ".pptm"):
            from app.ingestion.pptx_parser import PPTXParser
            result = PPTXParser().parse(tmp_path)
            slides = result.get("slides", [])
            parts = []
            for s in slides:
                if s.get("title"):
                    parts.append(f"Slide {s['slide_number']}: {s['title']}")
                for c in s.get("content", []):
                    parts.append(c)
            return "\n".join(parts)

        return uploaded_file.read().decode("utf-8", errors="replace")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Helper: generate the PPTX file from slides JSON
# ---------------------------------------------------------------------------

def build_pptx_file(slides_data: list, title: str, template_path: str | None) -> str:
    """Build a PPTX file and return the saved file path.

    Tries PresentonClient first; falls back to BrandedPresentationGenerator;
    falls back to a minimal python-pptx build.
    """
    PRESENTATIONS_DIR.mkdir(parents=True, exist_ok=True)
    safe_title = "".join(c if c.isalnum() or c in " _-" else "" for c in title)[:60]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_title}_{timestamp}.pptx"
    save_path = str(PRESENTATIONS_DIR / filename)

    # --- Attempt 1: Presenton ---
    try:
        pc = PresentonClient()
        if pc.available:
            content_text = json.dumps({"title": title, "slides": slides_data})
            result = pc.generate_presentation(
                content=content_text,
                n_slides=len(slides_data),
            )
            if result.get("success") and result.get("request_id"):
                status = pc.poll_status(result["request_id"], max_wait=120)
                if status.get("status") == "completed":
                    dl = pc.download_result(result["request_id"], save_path=save_path)
                    if dl.get("success"):
                        return dl["file_path"]
    except Exception as exc:
        logger.debug("Presenton generation failed: %s", exc)

    # --- Attempt 2: BrandedPresentationGenerator ---
    try:
        from app.generators.presentation_gen import BrandedPresentationGenerator

        gen = BrandedPresentationGenerator()
        result_path = gen.generate(
            slides_data=slides_data,
            title=title,
            save_path=save_path,
            template_path=template_path,
        )
        if result_path and Path(result_path).exists():
            return result_path
    except ImportError:
        logger.debug("BrandedPresentationGenerator not available; using fallback.")
    except Exception as exc:
        logger.debug("BrandedPresentationGenerator failed: %s", exc)

    # --- Attempt 3: Minimal python-pptx fallback ---
    try:
        from pptx import Presentation as PptxPresentation
        from pptx.util import Inches, Pt

        prs = PptxPresentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        for slide_data in slides_data:
            layout_idx = 1  # default to Title and Content
            layout_type = slide_data.get("layout", "content")
            if layout_type == "title":
                layout_idx = 0
            elif layout_type == "section_divider":
                layout_idx = 2 if len(prs.slide_layouts) > 2 else 1
            elif layout_type == "two_column":
                layout_idx = 3 if len(prs.slide_layouts) > 3 else 1
            elif layout_type == "closing":
                layout_idx = 0

            try:
                slide_layout = prs.slide_layouts[layout_idx]
            except IndexError:
                slide_layout = prs.slide_layouts[0]

            slide = prs.slides.add_slide(slide_layout)

            # Set title
            if slide.shapes.title and slide_data.get("title"):
                slide.shapes.title.text = slide_data["title"]

            # Set subtitle for title slides
            if layout_type == "title" and slide_data.get("subtitle"):
                for ph in slide.placeholders:
                    if ph.placeholder_format.idx == 1:
                        ph.text = slide_data["subtitle"]
                        break

            # Set body content
            body_placeholder = None
            for ph in slide.placeholders:
                if ph.placeholder_format.idx == 1 and layout_type != "title":
                    body_placeholder = ph
                    break

            if body_placeholder is not None:
                tf = body_placeholder.text_frame
                tf.clear()
                bullets = slide_data.get("bullets", [])
                body_text = slide_data.get("body", "")

                if bullets:
                    for i, bullet in enumerate(bullets):
                        if i == 0:
                            tf.text = bullet
                        else:
                            p = tf.add_paragraph()
                            p.text = bullet
                elif body_text:
                    tf.text = body_text

            # Add speaker notes
            notes_text = slide_data.get("speaker_notes", "")
            if notes_text:
                notes_slide = slide.notes_slide
                notes_slide.notes_text_frame.text = notes_text

        prs.save(save_path)
        return save_path
    except Exception as exc:
        logger.error("Fallback PPTX generation failed: %s", exc)
        raise RuntimeError(f"All presentation generation methods failed: {exc}")


# ---------------------------------------------------------------------------
# Helper: record generation in database
# ---------------------------------------------------------------------------

def record_generation(
    title: str,
    file_path: str,
    slide_count: int,
    generation_time: float,
    template_id: int | None,
    input_summary: str,
) -> int | None:
    """Insert a GeneratedContent row and return its ID."""
    try:
        session = get_session()
        record = GeneratedContent(
            title=title,
            content_type="presentation",
            template_id=template_id,
            input_summary=input_summary[:500] if input_summary else "",
            output_path=file_path,
            format="pptx",
            generated_at=datetime.utcnow(),
            generation_time_seconds=round(generation_time, 2),
        )
        session.add(record)

        # Bump template usage count if applicable
        if template_id:
            tpl = session.query(Template).filter_by(id=template_id).first()
            if tpl:
                tpl.usage_count = (tpl.usage_count or 0) + 1

        session.commit()
        record_id = record.id
        session.close()
        return record_id
    except Exception as exc:
        logger.error("Failed to record generation: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Helper: get templates from database
# ---------------------------------------------------------------------------

def get_pptx_templates() -> list[dict]:
    """Return list of dicts for pptx-type templates from the database."""
    try:
        session = get_session()
        templates = (
            session.query(Template)
            .filter(Template.template_type == "pptx")
            .order_by(Template.name)
            .all()
        )
        result = [
            {"id": t.id, "name": t.name, "file_path": t.file_path, "description": t.description or ""}
            for t in templates
        ]
        session.close()
        return result
    except Exception as exc:
        logger.warning("Failed to query templates: %s", exc)
        return []


# ===================================================================
# TABS
# ===================================================================

tab_generate, tab_preview, tab_import, tab_history = st.tabs(
    ["Generate Presentation", "Slide Preview", "Import Template", "History"]
)

# ===================================================================
# TAB 1 -- Generate Presentation
# ===================================================================

with tab_generate:

    col_main, col_config = st.columns([3, 1])

    # ----- Configuration sidebar (right column) -----
    with col_config:
        st.subheader("Configuration")

        slide_count = st.slider(
            "Number of slides",
            min_value=5,
            max_value=30,
            value=10,
            step=1,
            help="Target number of slides to generate.",
        )

        # Template selector
        db_templates = get_pptx_templates()
        template_options = ["Default Brand Template"] + [t["name"] for t in db_templates]
        selected_template_name = st.selectbox("Template", template_options)

        selected_template_id = None
        selected_template_path = None
        if selected_template_name != "Default Brand Template":
            for t in db_templates:
                if t["name"] == selected_template_name:
                    selected_template_id = t["id"]
                    selected_template_path = t["file_path"]
                    break

        language = st.selectbox(
            "Language",
            ["English", "Spanish", "French", "German", "Portuguese"],
            index=0,
        )

        include_notes = st.checkbox("Include speaker notes", value=True)
        include_visuals = st.checkbox("Include suggested visuals", value=True)

    # ----- Main content area (left column) -----
    with col_main:

        # 1. Presentation type
        pres_type = st.selectbox(
            "Presentation Type",
            [
                "Training Module",
                "Client Pitch",
                "Quarterly Business Review (QBR)",
                "General Presentation",
                "Program Rollout",
            ],
            help=(
                "Training Module - instructional slides with objectives, content, activities, recap. "
                "Client Pitch - persuasive flow: problem, solution, benefits, social proof, CTA. "
                "QBR - metrics, achievements, challenges, next steps. "
                "General - flexible structure. "
                "Program Rollout - announcement, timeline, responsibilities, resources, FAQ."
            ),
        )

        # 2. Content input
        st.markdown("---")
        st.subheader("Content Input")
        input_mode = st.radio(
            "How would you like to provide content?",
            ["Describe a Topic", "Paste Content", "Upload Document"],
            horizontal=True,
        )

        user_content = ""

        if input_mode == "Describe a Topic":
            topic_desc = st.text_area(
                "Describe the presentation topic",
                height=120,
                placeholder="e.g. A 10-slide training module on objection handling techniques for new sales reps...",
            )
            key_points = st.text_area(
                "Key points to cover (optional)",
                height=80,
                placeholder="e.g.\n- Common objections\n- Response frameworks\n- Practice scenarios",
            )
            if topic_desc:
                user_content = f"Topic: {topic_desc}"
                if key_points.strip():
                    user_content += f"\n\nKey points to cover:\n{key_points}"

        elif input_mode == "Paste Content":
            pasted = st.text_area(
                "Paste your content below",
                height=250,
                placeholder="Paste article text, outline, notes, or any source content that should be converted into slides...",
            )
            if pasted:
                user_content = pasted

        else:  # Upload Document
            uploaded_file = st.file_uploader(
                "Upload a document",
                type=["txt", "pdf", "docx", "pptx"],
                help="Supported formats: TXT, PDF, DOCX, PPTX",
            )
            if uploaded_file is not None:
                with st.spinner("Extracting text from uploaded file..."):
                    try:
                        user_content = extract_uploaded_file_content(uploaded_file)
                        if user_content:
                            st.success(
                                f"Extracted {len(user_content):,} characters from "
                                f"{uploaded_file.name}"
                            )
                            with st.expander("Preview extracted content"):
                                st.text(user_content[:3000] + ("..." if len(user_content) > 3000 else ""))
                        else:
                            st.warning("No text could be extracted from the uploaded file.")
                    except Exception as exc:
                        st.error(f"Failed to extract content: {exc}")

        # 3. Language note
        if language != "English":
            lang_map = {
                "Spanish": "es", "French": "fr", "German": "de", "Portuguese": "pt",
            }
            user_content += f"\n\n[Generate all slide content in {language} ({lang_map.get(language, 'en')})]"

        # 4. Generate button
        st.markdown("---")
        generate_disabled = not user_content.strip()
        if generate_disabled:
            st.info("Provide content above to enable generation.")

        if st.button(
            "Generate Presentation",
            type="primary",
            disabled=generate_disabled,
            use_container_width=True,
        ):
            brand_config = load_brand_config()
            system_prompt = build_slide_generation_prompt(
                pres_type=pres_type,
                content=user_content,
                n_slides=slide_count,
                include_notes=include_notes,
                include_visuals=include_visuals,
                brand_config=brand_config,
            )

            start_time = time.time()
            progress_bar = st.progress(0, text="Preparing slide generation...")
            status_area = st.empty()

            try:
                # Step 1 -- Generate slide JSON via Claude
                progress_bar.progress(10, text="Step 1/4: Generating slide content with Claude AI...")
                status_area.info("Calling Claude API to generate structured slide data...")

                raw_response = call_claude(system_prompt, user_content)

                # Parse JSON from response (handle markdown code fences)
                json_text = raw_response.strip()
                if json_text.startswith("```"):
                    # Remove code fence markers
                    lines = json_text.split("\n")
                    # Drop first line (```json) and last line (```)
                    lines = [l for l in lines if not l.strip().startswith("```")]
                    json_text = "\n".join(lines)

                slides_json = json.loads(json_text)
                gen_title = slides_json.get("title", f"{pres_type} Presentation")
                slides_list = slides_json.get("slides", [])

                if not slides_list:
                    st.error("Claude returned an empty slides array. Please try again.")
                    st.stop()

                progress_bar.progress(40, text="Step 2/4: Slide content generated. Building PPTX file...")
                status_area.info(
                    f"Generated {len(slides_list)} slides. Building presentation file..."
                )

                # Step 2 -- Build PPTX
                progress_bar.progress(60, text="Step 3/4: Assembling branded PPTX...")
                file_path = build_pptx_file(
                    slides_data=slides_list,
                    title=gen_title,
                    template_path=selected_template_path,
                )

                # Step 3 -- Record in database
                progress_bar.progress(85, text="Step 4/4: Recording to database...")
                elapsed = time.time() - start_time
                record_generation(
                    title=gen_title,
                    file_path=file_path,
                    slide_count=len(slides_list),
                    generation_time=elapsed,
                    template_id=selected_template_id,
                    input_summary=user_content[:500],
                )

                # Step 4 -- Store in session state
                st.session_state.generated_slides = slides_list
                st.session_state.generated_title = gen_title
                st.session_state.generated_file_path = file_path
                st.session_state.generation_time = round(elapsed, 1)
                st.session_state.slide_count_actual = len(slides_list)

                progress_bar.progress(100, text="Complete!")
                status_area.empty()

                st.success(
                    f"Presentation generated in {round(elapsed, 1)}s -- "
                    f"{len(slides_list)} slides created."
                )

                # Download button
                with open(file_path, "rb") as f:
                    st.download_button(
                        label="Download PPTX",
                        data=f.read(),
                        file_name=Path(file_path).name,
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        type="primary",
                    )

            except json.JSONDecodeError as exc:
                progress_bar.empty()
                status_area.empty()
                st.error(f"Failed to parse slide JSON from Claude response: {exc}")
                with st.expander("Raw response"):
                    st.code(raw_response[:5000], language="json")
            except EnvironmentError as exc:
                progress_bar.empty()
                status_area.empty()
                st.error(str(exc))
            except Exception as exc:
                progress_bar.empty()
                status_area.empty()
                st.error(f"Generation failed: {exc}")
                logger.exception("Presentation generation error")

    # Show previous result if available
    if (
        st.session_state.generated_file_path
        and Path(st.session_state.generated_file_path).exists()
        and not generate_disabled
    ):
        st.markdown("---")
        st.subheader("Last Generated Presentation")
        col_info1, col_info2, col_info3 = st.columns(3)
        col_info1.metric("Title", st.session_state.generated_title or "Untitled")
        col_info2.metric("Slides", st.session_state.slide_count_actual)
        col_info3.metric("Generation Time", f"{st.session_state.generation_time}s")

        with open(st.session_state.generated_file_path, "rb") as f:
            st.download_button(
                label="Download Last Presentation",
                data=f.read(),
                file_name=Path(st.session_state.generated_file_path).name,
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                key="download_last",
            )


# ===================================================================
# TAB 2 -- Slide Preview
# ===================================================================

with tab_preview:
    if not st.session_state.generated_slides:
        st.info(
            "No presentation has been generated yet. Go to the "
            "\"Generate Presentation\" tab to create one."
        )
    else:
        slides = st.session_state.generated_slides
        title = st.session_state.generated_title or "Untitled Presentation"

        st.subheader(f"Preview: {title}")
        st.caption(f"{len(slides)} slides")

        # Layout type to badge class mapping
        badge_classes = {
            "title": "type-badge-title",
            "section_divider": "type-badge-section",
            "content": "type-badge-content",
            "two_column": "type-badge-content",
            "image_text": "type-badge-content",
            "chart_data": "type-badge-chart",
            "quote_callout": "type-badge-quote",
            "closing": "type-badge-closing",
        }

        for idx, slide in enumerate(slides):
            layout = slide.get("layout", "content")
            badge_cls = badge_classes.get(layout, "type-badge-content")

            st.markdown(
                f'<div class="slide-preview">'
                f'<span class="slide-number">Slide {idx + 1}</span> '
                f'<span class="type-badge {badge_cls}">{layout.replace("_", " ").title()}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )

            # Title
            slide_title = slide.get("title", "")
            if slide_title:
                st.markdown(f"### {slide_title}")

            # Subtitle (title slides)
            subtitle = slide.get("subtitle", "")
            if subtitle:
                st.markdown(f"*{subtitle}*")

            # Bullets
            bullets = slide.get("bullets", [])
            if bullets:
                for bullet in bullets:
                    st.markdown(f"- {bullet}")

            # Body text
            body = slide.get("body", "")
            if body:
                st.markdown(body)

            # Two-column layout
            columns_data = slide.get("columns", [])
            if columns_data and len(columns_data) >= 2:
                col_left, col_right = st.columns(2)
                for ci, col_widget in enumerate([col_left, col_right]):
                    if ci < len(columns_data):
                        col_info = columns_data[ci]
                        with col_widget:
                            st.markdown(f"**{col_info.get('title', f'Column {ci + 1}')}**")
                            for b in col_info.get("bullets", []):
                                st.markdown(f"- {b}")

            # Chart data
            chart_data = slide.get("chart_data")
            if chart_data:
                with st.expander("Chart Data", expanded=False):
                    chart_type = chart_data.get("type", "bar")
                    categories = chart_data.get("categories", [])
                    series = chart_data.get("series", [])
                    st.markdown(f"**Chart type:** {chart_type}")
                    if categories:
                        st.markdown(f"**Categories:** {', '.join(str(c) for c in categories)}")
                    for s in series:
                        st.markdown(f"- **{s.get('name', 'Series')}:** {s.get('values', [])}")

            # Table data
            table_data = slide.get("table_data")
            if table_data and len(table_data) >= 2:
                try:
                    import pandas as pd
                    headers = table_data[0]
                    rows = table_data[1:]
                    df = pd.DataFrame(rows, columns=headers)
                    st.dataframe(df, use_container_width=True)
                except Exception:
                    for row in table_data:
                        st.text(" | ".join(str(c) for c in row))

            # Quote
            quote = slide.get("quote", "")
            if quote:
                attribution = slide.get("attribution", "")
                st.markdown(f"> {quote}")
                if attribution:
                    st.markdown(f"*-- {attribution}*")

            # Suggested visual
            visual = slide.get("suggested_visual", "")
            if visual:
                st.markdown(f"*Visual suggestion: {visual}*")

            # Speaker notes
            notes = slide.get("speaker_notes", "")
            if notes:
                with st.expander("Speaker Notes"):
                    st.markdown(notes)

            # Regenerate single slide
            regen_key = f"regen_slide_{idx}"
            if st.button(f"Regenerate Slide {idx + 1}", key=regen_key):
                with st.spinner(f"Regenerating slide {idx + 1}..."):
                    try:
                        brand_config = load_brand_config()
                        regen_system = (
                            "You are a professional presentation designer. "
                            "Regenerate a single slide as JSON. Return ONLY valid JSON "
                            "for one slide object with fields: layout, title, bullets, "
                            "body, speaker_notes, suggested_visual, subtitle, columns, "
                            "chart_data, table_data, quote, attribution. "
                            "Only include relevant fields for the layout type."
                        )
                        context = (
                            f"This is slide {idx + 1} of a {len(slides)}-slide "
                            f"\"{st.session_state.generated_title}\" presentation.\n\n"
                            f"Current slide content:\n{json.dumps(slide, indent=2)}\n\n"
                            "Please regenerate this slide with improved, fresh content "
                            "while keeping the same layout type and general topic."
                        )
                        raw = call_claude(regen_system, context)
                        json_text = raw.strip()
                        if json_text.startswith("```"):
                            lines = json_text.split("\n")
                            lines = [l for l in lines if not l.strip().startswith("```")]
                            json_text = "\n".join(lines)
                        new_slide = json.loads(json_text)
                        st.session_state.generated_slides[idx] = new_slide
                        st.success(f"Slide {idx + 1} regenerated.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to regenerate slide: {exc}")

            st.markdown("---")

        # Re-export button
        st.subheader("Re-export Updated Presentation")
        st.markdown(
            "After regenerating individual slides, click below to rebuild "
            "the PPTX file with all current slide content."
        )
        if st.button("Replace & Re-export PPTX", type="primary", use_container_width=True):
            with st.spinner("Rebuilding presentation file..."):
                try:
                    # Determine template path from previous generation context
                    tpl_path = None
                    if selected_template_path:
                        tpl_path = selected_template_path

                    new_path = build_pptx_file(
                        slides_data=st.session_state.generated_slides,
                        title=st.session_state.generated_title or "Presentation",
                        template_path=tpl_path,
                    )
                    st.session_state.generated_file_path = new_path
                    st.success("Presentation rebuilt successfully.")

                    with open(new_path, "rb") as f:
                        st.download_button(
                            label="Download Updated PPTX",
                            data=f.read(),
                            file_name=Path(new_path).name,
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            key="download_reexport",
                        )
                except Exception as exc:
                    st.error(f"Failed to rebuild presentation: {exc}")


# ===================================================================
# TAB 3 -- Import Template
# ===================================================================

with tab_import:
    st.subheader("Import a PowerPoint Template")
    st.markdown(
        "Upload a branded `.pptx` file to extract its design DNA (colors, fonts, "
        "layouts, logo placement) and register it as a reusable template."
    )

    import_col1, import_col2 = st.columns([2, 1])

    with import_col1:
        template_file = st.file_uploader(
            "Upload PPTX template",
            type=["pptx"],
            key="template_upload",
        )
        template_name = st.text_input(
            "Template name",
            placeholder="e.g. Corporate Q1 2026 Theme",
        )
        template_desc = st.text_area(
            "Description",
            height=80,
            placeholder="Describe the template, its intended use, and any special layouts...",
        )

    with import_col2:
        st.markdown("**Template tips:**")
        st.markdown(
            "- Use a `.pptx` with at least a title and content layout\n"
            "- Include your brand logo on the slide master\n"
            "- Set your brand colors in the theme\n"
            "- Add placeholder text so layouts are detected"
        )

    if st.button(
        "Import Template",
        disabled=(template_file is None or not template_name.strip()),
        type="primary",
    ):
        with st.spinner("Importing template..."):
            try:
                # Save uploaded file to templates directory
                TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
                safe_name = "".join(
                    c if c.isalnum() or c in " _-" else "" for c in template_name
                )[:50]
                dest_path = TEMPLATES_DIR / f"{safe_name}.pptx"
                with open(dest_path, "wb") as f:
                    f.write(template_file.read())

                # Try TemplateImporter
                template_dna = None
                try:
                    from app.generators.presentation_gen import TemplateImporter
                    importer = TemplateImporter()
                    template_dna = importer.import_template(
                        pptx_path=str(dest_path),
                        template_name=template_name.strip(),
                        description=template_desc.strip(),
                    )
                except ImportError:
                    logger.debug("TemplateImporter not available; using manual import.")
                except Exception as exc:
                    logger.warning("TemplateImporter failed: %s", exc)

                # If TemplateImporter didn't handle DB registration, do it manually
                if template_dna is None:
                    # Extract template info via PPTXParser
                    from app.ingestion.pptx_parser import PPTXParser
                    parser = PPTXParser()
                    tpl_info = parser.extract_template_info(str(dest_path))

                    template_dna = {
                        "layouts": tpl_info.get("layouts", []),
                        "colors": tpl_info.get("color_scheme", {}),
                        "fonts": tpl_info.get("font_theme", {}),
                    }

                    # Register in DB
                    session = get_session()
                    new_tpl = Template(
                        name=template_name.strip(),
                        template_type="pptx",
                        file_path=str(dest_path),
                        description=template_desc.strip(),
                        frozen_zones_json=json.dumps(template_dna),
                        usage_count=0,
                    )
                    session.add(new_tpl)
                    session.commit()
                    session.close()

                st.success(f"Template \"{template_name}\" imported successfully.")

                # Display extracted DNA
                if template_dna:
                    st.subheader("Extracted Template DNA")
                    dna_col1, dna_col2, dna_col3 = st.columns(3)

                    with dna_col1:
                        st.markdown("**Layouts**")
                        layouts = template_dna.get("layouts", [])
                        if layouts:
                            for lay in layouts:
                                st.markdown(f"- {lay}")
                        else:
                            st.caption("No layouts detected")

                    with dna_col2:
                        st.markdown("**Colors**")
                        colors = template_dna.get("colors", {})
                        if colors:
                            for name, hex_val in colors.items():
                                if hex_val:
                                    st.markdown(
                                        f'<span style="display:inline-block;width:14px;'
                                        f'height:14px;background:{hex_val};border:1px solid '
                                        f'#ccc;border-radius:3px;vertical-align:middle;">'
                                        f'</span> {name}: `{hex_val}`',
                                        unsafe_allow_html=True,
                                    )
                        else:
                            st.caption("No color scheme detected")

                    with dna_col3:
                        st.markdown("**Fonts**")
                        fonts = template_dna.get("fonts", {})
                        if fonts:
                            major = fonts.get("major_font", "")
                            minor = fonts.get("minor_font", "")
                            if major:
                                st.markdown(f"- Major (headings): **{major}**")
                            if minor:
                                st.markdown(f"- Minor (body): **{minor}**")
                        else:
                            st.caption("No font theme detected")

            except Exception as exc:
                st.error(f"Failed to import template: {exc}")
                logger.exception("Template import error")

    # ----- Existing templates list -----
    st.markdown("---")
    st.subheader("Existing Templates")

    existing_templates = get_pptx_templates()
    if not existing_templates:
        st.caption("No templates have been imported yet.")
    else:
        try:
            session = get_session()
            templates_with_usage = (
                session.query(Template)
                .filter(Template.template_type == "pptx")
                .order_by(Template.created_at.desc())
                .all()
            )
            for tpl in templates_with_usage:
                with st.container():
                    t_col1, t_col2, t_col3 = st.columns([3, 1, 1])
                    with t_col1:
                        st.markdown(f"**{tpl.name}**")
                        if tpl.description:
                            st.caption(tpl.description)
                    with t_col2:
                        st.metric("Uses", tpl.usage_count or 0)
                    with t_col3:
                        created = tpl.created_at.strftime("%Y-%m-%d") if tpl.created_at else "N/A"
                        st.caption(f"Added: {created}")
                    st.markdown("---")
            session.close()
        except Exception as exc:
            st.warning(f"Could not load template details: {exc}")


# ===================================================================
# TAB 4 -- History
# ===================================================================

with tab_history:
    st.subheader("Presentation History")

    try:
        session = get_session()
        history_records = (
            session.query(GeneratedContent)
            .filter(GeneratedContent.content_type == "presentation")
            .order_by(GeneratedContent.generated_at.desc())
            .limit(50)
            .all()
        )

        if not history_records:
            st.info("No presentations have been generated yet.")
        else:
            st.caption(f"Showing {len(history_records)} most recent presentations.")

            for record in history_records:
                with st.container():
                    h_col1, h_col2, h_col3, h_col4 = st.columns([3, 1, 1, 2])

                    with h_col1:
                        st.markdown(f"**{record.title}**")
                        if record.input_summary:
                            st.caption(record.input_summary[:120] + ("..." if len(record.input_summary or "") > 120 else ""))

                    with h_col2:
                        gen_date = (
                            record.generated_at.strftime("%b %d, %Y %H:%M")
                            if record.generated_at
                            else "Unknown"
                        )
                        st.caption(f"Generated: {gen_date}")

                    with h_col3:
                        gen_time = (
                            f"{record.generation_time_seconds:.1f}s"
                            if record.generation_time_seconds
                            else "N/A"
                        )
                        st.caption(f"Time: {gen_time}")
                        if record.user_rating:
                            st.caption(f"Rating: {'*' * record.user_rating}")

                    with h_col4:
                        action_cols = st.columns(3)

                        # Download button
                        file_exists = (
                            record.output_path
                            and Path(record.output_path).exists()
                        )
                        with action_cols[0]:
                            if file_exists:
                                with open(record.output_path, "rb") as f:
                                    st.download_button(
                                        label="Download",
                                        data=f.read(),
                                        file_name=Path(record.output_path).name,
                                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                        key=f"dl_{record.id}",
                                    )
                            else:
                                st.caption("File missing")

                        # Add to Library button
                        with action_cols[1]:
                            if st.button("To Library", key=f"lib_{record.id}"):
                                try:
                                    lib_session = get_session()
                                    # Check if already in library
                                    existing = (
                                        lib_session.query(ContentLibraryItem)
                                        .filter_by(generated_content_id=record.id)
                                        .first()
                                    )
                                    if existing:
                                        st.toast("Already in library.", icon="ℹ")
                                    else:
                                        lib_item = ContentLibraryItem(
                                            generated_content_id=record.id,
                                            title=record.title,
                                            description=record.input_summary or "",
                                            tags="presentation",
                                            category="presentation",
                                            is_approved=False,
                                            download_count=0,
                                        )
                                        lib_session.add(lib_item)
                                        lib_session.commit()
                                        st.toast("Added to Content Library!", icon="✓")
                                    lib_session.close()
                                except Exception as exc:
                                    st.error(f"Failed: {exc}")

                        # Delete button
                        with action_cols[2]:
                            if st.button("Delete", key=f"del_{record.id}"):
                                try:
                                    del_session = get_session()
                                    # Remove file
                                    if record.output_path and Path(record.output_path).exists():
                                        try:
                                            os.remove(record.output_path)
                                        except OSError:
                                            pass
                                    # Remove library items that reference this record
                                    del_session.query(ContentLibraryItem).filter_by(
                                        generated_content_id=record.id
                                    ).delete()
                                    # Remove DB record
                                    del_session.query(GeneratedContent).filter_by(
                                        id=record.id
                                    ).delete()
                                    del_session.commit()
                                    del_session.close()
                                    st.toast("Deleted.", icon="✓")
                                    st.rerun()
                                except Exception as exc:
                                    st.error(f"Delete failed: {exc}")

                    st.markdown("---")

        session.close()
    except Exception as exc:
        st.error(f"Failed to load history: {exc}")
        logger.exception("History tab error")
