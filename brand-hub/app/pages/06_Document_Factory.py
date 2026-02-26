"""
Brand Intelligence Content Hub - Document Factory

Interactive workspace for generating professional branded documents from
templates and AI-powered content. Supports 10 document types with both
AI-assisted and manual content modes, data import, batch generation,
template management, and generation history.
"""

import csv
import io
import json
import logging
import os
import tempfile
import time
import zipfile
from datetime import datetime, date
from pathlib import Path

import streamlit as st

from app.config import (
    BASE_DIR,
    BRAND_ASSETS_DIR,
    DOCUMENTS_DIR,
    EXPORTS_DIR,
    REPORTS_DIR,
    TEMPLATES_DIR,
    get_env,
)
from app.database.models import (
    get_session,
    Template,
    GeneratedContent,
    ContentLibraryItem,
    BatchJob,
)

# Graceful imports for generators that may not yet exist
try:
    from app.generators.document_gen import (
        BrandedDocumentGenerator,
        BrandedDocumentStyles,
        DOCUMENT_TEMPLATES,
    )
    DOCUMENT_GEN_AVAILABLE = True
except ImportError:
    DOCUMENT_GEN_AVAILABLE = False
    DOCUMENT_TEMPLATES = {
        "job_aid": {"name": "Job Aid", "description": "Quick-reference guide for tasks and procedures", "typical_pages": "1-2", "use_cases": ["Process checklists", "Quick-reference cards", "How-to guides"]},
        "case_study": {"name": "Case Study", "description": "Client success story with measurable outcomes", "typical_pages": "2-4", "use_cases": ["Client success stories", "ROI showcases", "Solution highlights"]},
        "weekly_report": {"name": "Weekly Report", "description": "Weekly performance summary with KPIs and priorities", "typical_pages": "2-3", "use_cases": ["Team status updates", "Sprint summaries", "Weekly metrics"]},
        "monthly_report": {"name": "Monthly Report", "description": "Comprehensive monthly business review", "typical_pages": "4-8", "use_cases": ["Executive reviews", "Department summaries", "Financial overviews"]},
        "sop": {"name": "Standard Operating Procedure", "description": "Detailed step-by-step operational procedure", "typical_pages": "3-10", "use_cases": ["Process documentation", "Compliance procedures", "Onboarding guides"]},
        "training_guide": {"name": "Training Guide", "description": "Structured training curriculum with modules and assessments", "typical_pages": "5-15", "use_cases": ["New hire training", "Product training", "Skill development"]},
        "internal_memo": {"name": "Internal Memo", "description": "Formal internal communication document", "typical_pages": "1-2", "use_cases": ["Policy announcements", "Project updates", "Leadership communications"]},
        "battle_card": {"name": "Battle Card", "description": "Competitive intelligence reference for sales teams", "typical_pages": "1-2", "use_cases": ["Sales enablement", "Competitive positioning", "Objection handling"]},
        "capability_overview": {"name": "Capability Overview", "description": "Company or team capability summary", "typical_pages": "2-4", "use_cases": ["Service catalogs", "Team introductions", "Vendor responses"]},
        "proposal": {"name": "Proposal", "description": "Formal business proposal with scope and pricing", "typical_pages": "5-12", "use_cases": ["Client proposals", "Project bids", "Partnership proposals"]},
    }

try:
    from app.generators.pdf_gen import PDFGenerator
    PDF_GEN_AVAILABLE = True
except ImportError:
    PDF_GEN_AVAILABLE = False

try:
    from app.generators.spreadsheet_gen import BrandedSpreadsheetGenerator
    SPREADSHEET_GEN_AVAILABLE = True
except ImportError:
    SPREADSHEET_GEN_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Document Factory", layout="wide")

st.markdown("""<style>
.doc-card { border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px; margin: 8px 0; background: white; transition: box-shadow 0.2s; }
.doc-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.template-badge { background: #e8f0fe; color: #1a73e8; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; }
.pages-badge { background: #e6f4ea; color: #137333; padding: 4px 12px; border-radius: 12px; font-size: 12px; }
.format-selector { display: flex; gap: 8px; }
.stProgress > div > div > div > div { background-color: #0066cc; }
.history-row { border-bottom: 1px solid #eee; padding: 8px 0; }
.use-case-tag { background: #f0f0f0; color: #444; padding: 2px 8px; border-radius: 8px; font-size: 11px; display: inline-block; margin: 2px; }
</style>""", unsafe_allow_html=True)

st.title("Document Factory")
st.markdown("Generate professional branded documents from templates and AI-powered content")

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

_defaults = {
    "doc_selected_template": "job_aid",
    "doc_content_mode": "AI-Assisted",
    "doc_generated_path": None,
    "doc_generation_time": None,
    "doc_generated_content": None,
    "doc_ai_content_json": None,
    "doc_export_format": "DOCX",
    "data_import_df": None,
    "data_import_columns": None,
    "batch_specs": None,
    "batch_results": None,
}
for key, default in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

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
# Helper: parse CSV text to list of dicts
# ---------------------------------------------------------------------------

def parse_csv_text(csv_text: str) -> list:
    """Parse CSV text into a list of dicts."""
    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    return list(reader)


def parse_csv_to_rows(csv_text: str) -> list:
    """Parse CSV text into a list of lists (rows)."""
    reader = csv.reader(io.StringIO(csv_text.strip()))
    return list(reader)


# ---------------------------------------------------------------------------
# Build document generation prompt
# ---------------------------------------------------------------------------

def build_document_generation_prompt(doc_type: str, user_input: str, brand_config: dict) -> str:
    """Return a system prompt instructing Claude to generate the correct JSON
    structure for the requested document type."""

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

    company_context = ""
    if brand_config:
        company_name = brand_config.get("company_name", "")
        tagline = brand_config.get("tagline", "")
        if company_name:
            company_context = f"\nCompany: {company_name}"
        if tagline:
            company_context += f"\nTagline: {tagline}"

    structures = {
        "job_aid": """{
  "title": "Job Aid Title",
  "purpose": "Brief statement of what this job aid helps accomplish",
  "sections": [
    {
      "heading": "Section Heading",
      "steps": ["Step 1 description", "Step 2 description", "Step 3 description"],
      "tips": ["Helpful tip or best practice"]
    }
  ],
  "reference_table": [
    ["Column Header 1", "Column Header 2", "Column Header 3"],
    ["Row 1 Data", "Row 1 Data", "Row 1 Data"]
  ]
}""",
        "case_study": """{
  "title": "Case Study Title",
  "client_name": "Client or Company Name",
  "industry": "Industry sector",
  "executive_summary": "2-3 sentence overview of the success story",
  "challenge": "Detailed description of the client's challenge",
  "solution": "Detailed description of the solution provided",
  "approach_steps": ["Step 1 of the approach", "Step 2", "Step 3"],
  "results": [
    {"metric": "Revenue Growth", "value": "+35%", "description": "Year-over-year revenue increase"},
    {"metric": "Efficiency", "value": "50% reduction", "description": "In processing time"}
  ],
  "takeaways": ["Key takeaway 1", "Key takeaway 2"],
  "testimonial": {
    "quote": "Quote from the client about their experience",
    "attribution": "Client Name, Title, Company"
  }
}""",
        "weekly_report": """{
  "title": "Weekly Report Title",
  "period": "Week of January 1-7, 2026",
  "kpi_data": [
    {"kpi": "KPI Name", "target": "100", "actual": "105", "status": "On Track"},
    {"kpi": "KPI Name 2", "target": "50", "actual": "42", "status": "At Risk"}
  ],
  "accomplishments": ["Accomplishment 1", "Accomplishment 2", "Accomplishment 3"],
  "challenges": ["Challenge 1 and mitigation plan", "Challenge 2"],
  "priorities": ["Priority for next week 1", "Priority 2"],
  "notes": "Additional context or commentary"
}""",
        "monthly_report": """{
  "title": "Monthly Report Title",
  "period": "January 2026",
  "executive_summary": "High-level summary of the month's performance and key outcomes",
  "metrics": [
    {"category": "Revenue", "metric": "Total Revenue", "value": "$1.2M", "change": "+8%"},
    {"category": "Operations", "metric": "Tickets Resolved", "value": "450", "change": "+12%"}
  ],
  "sections": [
    {
      "heading": "Section Heading",
      "content": "Detailed narrative content for this section"
    }
  ],
  "recommendations": ["Recommendation 1 with rationale", "Recommendation 2"]
}""",
        "sop": """{
  "title": "Standard Operating Procedure Title",
  "doc_number": "SOP-001",
  "version": "1.0",
  "effective_date": "2026-01-01",
  "review_date": "2027-01-01",
  "author": "Author Name",
  "approver": "Approver Name",
  "purpose": "Clear statement of the procedure's purpose",
  "scope": "What this procedure covers and any exclusions",
  "responsibilities": [
    {"role": "Role Name", "responsibility": "What this role is responsible for"}
  ],
  "procedure_steps": [
    {
      "step_number": 1,
      "title": "Step Title",
      "description": "Detailed description of what to do",
      "substeps": ["Substep a", "Substep b"],
      "notes": "Any cautions or tips for this step"
    }
  ],
  "safety_notes": ["Safety consideration 1", "Safety consideration 2"],
  "references": ["Reference document or link 1", "Reference 2"]
}""",
        "training_guide": """{
  "title": "Training Guide Title",
  "course_overview": "Description of what the training covers and target audience",
  "modules": [
    {
      "module_title": "Module 1 Title",
      "objectives": ["Learning objective 1", "Learning objective 2"],
      "content": "Detailed instructional content for the module",
      "activities": ["Hands-on activity 1", "Group discussion topic"],
      "key_takeaways": ["Takeaway 1", "Takeaway 2"]
    }
  ],
  "assessment_questions": [
    {
      "question": "Assessment question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A"
    }
  ]
}""",
        "internal_memo": """{
  "title": "Memo Subject Line",
  "to": "Recipient name(s) or department",
  "from_field": "Sender name and title",
  "date": "February 26, 2026",
  "subject": "Clear subject line",
  "body_paragraphs": [
    "Opening paragraph with purpose and context",
    "Detail paragraph with supporting information",
    "Closing paragraph with call to action"
  ],
  "action_items": [
    {"item": "Action item description", "owner": "Responsible person", "due_date": "Due date"}
  ],
  "cc": "CC recipients if any"
}""",
        "battle_card": """{
  "title": "Battle Card Title",
  "product_name": "Your Product or Service Name",
  "at_a_glance": "1-2 sentence elevator pitch summarizing the value proposition",
  "competitor_comparison": [
    ["Feature", "Our Product", "Competitor A", "Competitor B"],
    ["Feature 1", "Strong capability", "Limited", "Not available"],
    ["Feature 2", "Included", "Add-on cost", "Included"]
  ],
  "differentiators": [
    "Key differentiator 1 with brief explanation",
    "Key differentiator 2 with brief explanation"
  ],
  "objection_responses": [
    {"objection": "Common objection from prospects", "response": "Recommended response with proof points"},
    {"objection": "Price objection", "response": "Value-based response"}
  ],
  "talk_track": "Suggested conversation flow for sales calls: open with..., transition to..., close with...",
  "pricing_table": [
    ["Tier", "Price", "Includes"],
    ["Basic", "$X/mo", "Feature list"],
    ["Pro", "$Y/mo", "Feature list"]
  ]
}""",
        "capability_overview": """{
  "title": "Capability Overview Title",
  "tagline": "Brief tagline or value proposition",
  "capabilities": [
    {"name": "Capability Name", "description": "What this capability includes and its value"},
    {"name": "Capability 2", "description": "Description of capability 2"}
  ],
  "statistics": [
    {"label": "Years of Experience", "value": "15+"},
    {"label": "Clients Served", "value": "500+"}
  ],
  "contact": {
    "name": "Contact Name",
    "email": "email@company.com",
    "phone": "555-0100"
  }
}""",
        "proposal": """{
  "title": "Proposal Title",
  "client_name": "Client Company Name",
  "executive_summary": "High-level overview of the proposal and expected outcomes",
  "needs_analysis": "Description of the client's needs and pain points identified",
  "proposed_solution": "Detailed description of the proposed solution",
  "scope_items": [
    "Deliverable or scope item 1",
    "Deliverable or scope item 2",
    "Deliverable or scope item 3"
  ],
  "timeline": [
    {"phase": "Phase 1 - Discovery", "duration": "2 weeks", "deliverables": "Requirements doc"},
    {"phase": "Phase 2 - Build", "duration": "6 weeks", "deliverables": "Working prototype"}
  ],
  "pricing": [
    {"item": "Line item description", "quantity": "1", "unit_price": "$5,000", "total": "$5,000"}
  ],
  "team_members": [
    {"name": "Team Member Name", "role": "Project Lead", "bio": "Brief bio"}
  ],
  "terms": "Payment terms, warranty, and contractual conditions",
  "next_steps": ["Immediate next step 1", "Follow-up action 2"]
}""",
    }

    template_info = DOCUMENT_TEMPLATES.get(doc_type, {})
    template_name = template_info.get("name", doc_type)

    system_prompt = f"""You are a professional document content writer. Generate structured content for a {template_name} document.

{company_context}
{voice_context}

You MUST return ONLY valid JSON matching this exact structure for a {doc_type} document:

{structures.get(doc_type, structures["job_aid"])}

Rules:
- Return ONLY the JSON object, no markdown fences or explanation
- All text should be professional, specific, and actionable
- Use realistic data and concrete examples
- Content should be detailed enough for a polished final document
- Adapt the content to match the user's specific topic and requirements
- If the user provides data or metrics, incorporate them accurately
"""
    return system_prompt


# ---------------------------------------------------------------------------
# Helper: generate document via generator
# ---------------------------------------------------------------------------

def generate_document(content: dict, doc_type: str, title: str, export_format: str) -> dict:
    """Generate a branded document and return result dict."""
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)[:60].strip()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_title}_{timestamp}"

    result = {"success": False, "path": None, "format": export_format, "error": None}

    try:
        if export_format == "DOCX" and DOCUMENT_GEN_AVAILABLE:
            gen = BrandedDocumentGenerator()
            save_path = str(DOCUMENTS_DIR / f"{filename}.docx")
            out_path = gen.generate(content, doc_type, title, save_path)
            result["success"] = True
            result["path"] = out_path

        elif export_format == "PDF":
            if not DOCUMENT_GEN_AVAILABLE:
                result["error"] = "Document generator module is not available."
                return result
            gen = BrandedDocumentGenerator()
            docx_path = str(DOCUMENTS_DIR / f"{filename}.docx")
            out_path = gen.generate(content, doc_type, title, docx_path)

            if PDF_GEN_AVAILABLE:
                pdf_gen = PDFGenerator()
                if pdf_gen.available:
                    pdf_path = str(DOCUMENTS_DIR / f"{filename}.pdf")
                    pdf_result = pdf_gen.convert_docx_to_pdf(out_path, pdf_path)
                    if pdf_result["success"]:
                        result["success"] = True
                        result["path"] = pdf_result["pdf_path"]
                        result["format"] = "PDF"
                    else:
                        result["success"] = True
                        result["path"] = out_path
                        result["format"] = "DOCX"
                        result["error"] = f"PDF conversion failed ({pdf_result['error']}). DOCX saved instead."
                else:
                    result["success"] = True
                    result["path"] = out_path
                    result["format"] = "DOCX"
                    result["error"] = "PDF converter not available. DOCX saved instead."
            else:
                result["success"] = True
                result["path"] = out_path
                result["format"] = "DOCX"
                result["error"] = "PDF generator module not available. DOCX saved instead."

        elif export_format == "XLSX" and SPREADSHEET_GEN_AVAILABLE:
            report_types = ["weekly_report", "monthly_report"]
            if doc_type in report_types:
                gen = BrandedSpreadsheetGenerator()
                save_path = str(REPORTS_DIR / f"{filename}.xlsx")
                REPORTS_DIR.mkdir(parents=True, exist_ok=True)
                out_path = gen.generate(content, doc_type, title, save_path)
                result["success"] = True
                result["path"] = out_path
                result["format"] = "XLSX"
            else:
                result["error"] = "XLSX format is only available for report-type documents."

        elif export_format == "DOCX" and not DOCUMENT_GEN_AVAILABLE:
            # Fallback: save content as JSON for later processing
            save_path = str(DOCUMENTS_DIR / f"{filename}_content.json")
            with open(save_path, "w", encoding="utf-8") as fh:
                json.dump({"title": title, "doc_type": doc_type, "content": content}, fh, indent=2)
            result["success"] = True
            result["path"] = save_path
            result["format"] = "JSON"
            result["error"] = "Document generator not available. Content saved as JSON."

        else:
            result["error"] = f"Format '{export_format}' is not supported or the required generator is not installed."

    except Exception as exc:
        logger.exception("Document generation failed")
        result["error"] = str(exc)

    return result


# ---------------------------------------------------------------------------
# Helper: record in database
# ---------------------------------------------------------------------------

def record_generation(title: str, doc_type: str, output_path: str, fmt: str, gen_time: float):
    """Save a GeneratedContent record to the database."""
    try:
        session = get_session()
        record = GeneratedContent(
            title=title,
            content_type="document",
            input_summary=f"Document type: {doc_type}",
            output_path=output_path,
            format=fmt,
            generated_at=datetime.utcnow(),
            generation_time_seconds=gen_time,
        )
        session.add(record)
        session.commit()
        session.close()
    except Exception as exc:
        logger.warning("Failed to record generation: %s", exc)


# ===================================================================
# TABS
# ===================================================================

tab_generate, tab_import, tab_batch, tab_templates, tab_history = st.tabs([
    "Generate Document",
    "Data Import",
    "Batch Generation",
    "Templates",
    "History",
])


# ===================================================================
# TAB 1: Generate Document
# ===================================================================

with tab_generate:

    # --- Template Selection ---
    st.subheader("1. Select Template")

    template_keys = list(DOCUMENT_TEMPLATES.keys())
    template_names = [DOCUMENT_TEMPLATES[k]["name"] for k in template_keys]

    cols_row1 = st.columns(2)
    cols_row2 = st.columns(2)
    cols_row3 = st.columns(2)
    cols_row4 = st.columns(2)
    cols_row5 = st.columns(2)
    all_cols = [cols_row1[0], cols_row1[1], cols_row2[0], cols_row2[1],
                cols_row3[0], cols_row3[1], cols_row4[0], cols_row4[1],
                cols_row5[0], cols_row5[1]]

    for idx, tkey in enumerate(template_keys):
        tmpl = DOCUMENT_TEMPLATES[tkey]
        use_case_tags = " ".join(
            f'<span class="use-case-tag">{uc}</span>' for uc in tmpl.get("use_cases", [])
        )
        with all_cols[idx]:
            st.markdown(f"""<div class="doc-card">
<strong>{tmpl["name"]}</strong><br/>
<span style="color:#666; font-size:13px;">{tmpl["description"]}</span><br/>
<span class="pages-badge">{tmpl["typical_pages"]} pages</span>
<div style="margin-top:6px;">{use_case_tags}</div>
</div>""", unsafe_allow_html=True)

    selected_template = st.selectbox(
        "Choose a document template",
        template_keys,
        format_func=lambda k: DOCUMENT_TEMPLATES[k]["name"],
        index=template_keys.index(st.session_state.doc_selected_template)
        if st.session_state.doc_selected_template in template_keys else 0,
        key="template_selector",
    )
    st.session_state.doc_selected_template = selected_template

    st.divider()

    # --- Content Mode Toggle ---
    st.subheader("2. Content Input")

    content_mode = st.radio(
        "Content creation mode",
        ["AI-Assisted", "Manual"],
        horizontal=True,
        index=0 if st.session_state.doc_content_mode == "AI-Assisted" else 1,
        key="content_mode_radio",
    )
    st.session_state.doc_content_mode = content_mode

    content_dict = {}

    # ---- AI-Assisted Mode ----
    if content_mode == "AI-Assisted":
        st.info("Describe your document topic and requirements. Claude will generate structured content for the selected template.")

        ai_topic = st.text_area(
            "Topic / Description",
            placeholder=f"Describe what this {DOCUMENT_TEMPLATES[selected_template]['name']} should be about. Include key details, data points, names, and any specific requirements.",
            height=180,
            key="ai_topic_input",
        )

        ai_extra_context = st.text_area(
            "Additional context (optional)",
            placeholder="Paste any additional data, bullet points, or reference material here.",
            height=100,
            key="ai_extra_context",
        )

        # If there is imported data in session_state, offer to include it
        if st.session_state.data_import_df is not None:
            use_imported = st.checkbox("Include imported data from the Data Import tab", value=True, key="use_imported_data")
            if use_imported:
                st.caption("Imported data will be appended to your description for the AI to incorporate.")

    # ---- Manual Mode ----
    else:
        st.info("Fill in the fields below to manually compose your document content.")

        if selected_template == "job_aid":
            content_dict["title"] = st.text_input("Title", key="man_ja_title")
            content_dict["purpose"] = st.text_area("Purpose", key="man_ja_purpose", height=80)
            num_sections = st.number_input("Number of sections", 1, 10, 2, key="man_ja_nsec")
            sections = []
            for i in range(int(num_sections)):
                with st.expander(f"Section {i + 1}", expanded=(i == 0)):
                    heading = st.text_input(f"Heading", key=f"man_ja_sec{i}_heading")
                    steps_text = st.text_area(f"Steps (one per line)", key=f"man_ja_sec{i}_steps", height=100)
                    tips_text = st.text_area(f"Tips (one per line)", key=f"man_ja_sec{i}_tips", height=60)
                    sections.append({
                        "heading": heading,
                        "steps": [s.strip() for s in steps_text.split("\n") if s.strip()],
                        "tips": [t.strip() for t in tips_text.split("\n") if t.strip()],
                    })
            content_dict["sections"] = sections
            ref_csv = st.text_area("Reference table (paste CSV)", key="man_ja_ref", height=80,
                                   placeholder="Header1,Header2,Header3\nData1,Data2,Data3")
            if ref_csv.strip():
                content_dict["reference_table"] = parse_csv_to_rows(ref_csv)

        elif selected_template == "case_study":
            content_dict["title"] = st.text_input("Title", key="man_cs_title")
            content_dict["client_name"] = st.text_input("Client Name", key="man_cs_client")
            content_dict["industry"] = st.text_input("Industry", key="man_cs_industry")
            content_dict["executive_summary"] = st.text_area("Executive Summary", key="man_cs_exec", height=80)
            content_dict["challenge"] = st.text_area("Challenge", key="man_cs_challenge", height=100)
            content_dict["solution"] = st.text_area("Solution", key="man_cs_solution", height=100)
            approach_text = st.text_area("Approach Steps (one per line)", key="man_cs_approach", height=80)
            content_dict["approach_steps"] = [s.strip() for s in approach_text.split("\n") if s.strip()]
            results_csv = st.text_area("Results Metrics (CSV: metric,value,description)", key="man_cs_results", height=80)
            if results_csv.strip():
                content_dict["results"] = parse_csv_text(results_csv)
            else:
                content_dict["results"] = []
            takeaways_text = st.text_area("Key Takeaways (one per line)", key="man_cs_takeaways", height=60)
            content_dict["takeaways"] = [t.strip() for t in takeaways_text.split("\n") if t.strip()]
            st.markdown("**Testimonial**")
            quote = st.text_area("Quote", key="man_cs_quote", height=60)
            attribution = st.text_input("Attribution (Name, Title, Company)", key="man_cs_attr")
            content_dict["testimonial"] = {"quote": quote, "attribution": attribution}

        elif selected_template == "weekly_report":
            content_dict["title"] = st.text_input("Report Title", key="man_wr_title")
            col_a, col_b = st.columns(2)
            with col_a:
                start_date = st.date_input("Period Start", key="man_wr_start")
            with col_b:
                end_date = st.date_input("Period End", key="man_wr_end")
            content_dict["period"] = f"Week of {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
            kpi_csv = st.text_area("KPI Data (CSV: kpi,target,actual,status)", key="man_wr_kpi",
                                   height=80, placeholder="kpi,target,actual,status\nRevenue,$100K,$105K,On Track")
            if kpi_csv.strip():
                content_dict["kpi_data"] = parse_csv_text(kpi_csv)
            else:
                content_dict["kpi_data"] = []
            accomp_text = st.text_area("Accomplishments (one per line)", key="man_wr_accomp", height=80)
            content_dict["accomplishments"] = [a.strip() for a in accomp_text.split("\n") if a.strip()]
            challenges_text = st.text_area("Challenges (one per line)", key="man_wr_challenges", height=60)
            content_dict["challenges"] = [c.strip() for c in challenges_text.split("\n") if c.strip()]
            priorities_text = st.text_area("Next Week Priorities (one per line)", key="man_wr_priorities", height=60)
            content_dict["priorities"] = [p.strip() for p in priorities_text.split("\n") if p.strip()]
            content_dict["notes"] = st.text_area("Additional Notes", key="man_wr_notes", height=60)

        elif selected_template == "monthly_report":
            content_dict["title"] = st.text_input("Report Title", key="man_mr_title")
            content_dict["period"] = st.text_input("Period (e.g., January 2026)", key="man_mr_period")
            content_dict["executive_summary"] = st.text_area("Executive Summary", key="man_mr_exec", height=100)
            metrics_csv = st.text_area("Metrics (CSV: category,metric,value,change)", key="man_mr_metrics",
                                       height=80, placeholder="category,metric,value,change\nRevenue,Total Revenue,$1.2M,+8%")
            if metrics_csv.strip():
                content_dict["metrics"] = parse_csv_text(metrics_csv)
            else:
                content_dict["metrics"] = []
            num_sections_mr = st.number_input("Number of sections", 1, 10, 3, key="man_mr_nsec")
            sections_mr = []
            for i in range(int(num_sections_mr)):
                with st.expander(f"Section {i + 1}", expanded=(i == 0)):
                    heading = st.text_input("Section Heading", key=f"man_mr_sec{i}_heading")
                    body = st.text_area("Section Content", key=f"man_mr_sec{i}_content", height=100)
                    sections_mr.append({"heading": heading, "content": body})
            content_dict["sections"] = sections_mr
            recs_text = st.text_area("Recommendations (one per line)", key="man_mr_recs", height=60)
            content_dict["recommendations"] = [r.strip() for r in recs_text.split("\n") if r.strip()]

        elif selected_template == "sop":
            content_dict["title"] = st.text_input("SOP Title", key="man_sop_title")
            col_a, col_b = st.columns(2)
            with col_a:
                content_dict["doc_number"] = st.text_input("Document Number", key="man_sop_docnum", value="SOP-001")
                content_dict["version"] = st.text_input("Version", key="man_sop_ver", value="1.0")
                content_dict["author"] = st.text_input("Author", key="man_sop_author")
            with col_b:
                content_dict["effective_date"] = st.date_input("Effective Date", key="man_sop_effdate").isoformat()
                content_dict["review_date"] = st.date_input("Review Date", key="man_sop_revdate").isoformat()
                content_dict["approver"] = st.text_input("Approver", key="man_sop_approver")
            content_dict["purpose"] = st.text_area("Purpose", key="man_sop_purpose", height=80)
            content_dict["scope"] = st.text_area("Scope", key="man_sop_scope", height=80)
            resp_text = st.text_area("Responsibilities (CSV: role,responsibility)", key="man_sop_resp", height=60)
            if resp_text.strip():
                content_dict["responsibilities"] = parse_csv_text(resp_text)
            else:
                content_dict["responsibilities"] = []
            num_steps = st.number_input("Number of procedure steps", 1, 20, 3, key="man_sop_nsteps")
            proc_steps = []
            for i in range(int(num_steps)):
                with st.expander(f"Step {i + 1}", expanded=(i == 0)):
                    step_title = st.text_input("Step Title", key=f"man_sop_step{i}_title")
                    step_desc = st.text_area("Description", key=f"man_sop_step{i}_desc", height=80)
                    substeps_text = st.text_area("Substeps (one per line)", key=f"man_sop_step{i}_sub", height=60)
                    step_notes = st.text_input("Notes / Cautions", key=f"man_sop_step{i}_notes")
                    proc_steps.append({
                        "step_number": i + 1,
                        "title": step_title,
                        "description": step_desc,
                        "substeps": [s.strip() for s in substeps_text.split("\n") if s.strip()],
                        "notes": step_notes,
                    })
            content_dict["procedure_steps"] = proc_steps
            safety_text = st.text_area("Safety Notes (one per line)", key="man_sop_safety", height=60)
            content_dict["safety_notes"] = [s.strip() for s in safety_text.split("\n") if s.strip()]
            refs_text = st.text_area("References (one per line)", key="man_sop_refs", height=60)
            content_dict["references"] = [r.strip() for r in refs_text.split("\n") if r.strip()]

        elif selected_template == "training_guide":
            content_dict["title"] = st.text_input("Training Guide Title", key="man_tg_title")
            content_dict["course_overview"] = st.text_area("Course Overview", key="man_tg_overview", height=100)
            num_modules = st.number_input("Number of modules", 1, 15, 3, key="man_tg_nmod")
            modules = []
            for i in range(int(num_modules)):
                with st.expander(f"Module {i + 1}", expanded=(i == 0)):
                    mod_title = st.text_input("Module Title", key=f"man_tg_mod{i}_title")
                    objectives = st.text_area("Learning Objectives (one per line)", key=f"man_tg_mod{i}_obj", height=60)
                    mod_content = st.text_area("Content", key=f"man_tg_mod{i}_content", height=120)
                    activities = st.text_area("Activities (one per line)", key=f"man_tg_mod{i}_act", height=60)
                    takeaways = st.text_area("Key Takeaways (one per line)", key=f"man_tg_mod{i}_take", height=60)
                    modules.append({
                        "module_title": mod_title,
                        "objectives": [o.strip() for o in objectives.split("\n") if o.strip()],
                        "content": mod_content,
                        "activities": [a.strip() for a in activities.split("\n") if a.strip()],
                        "key_takeaways": [t.strip() for t in takeaways.split("\n") if t.strip()],
                    })
            content_dict["modules"] = modules
            num_questions = st.number_input("Assessment questions", 0, 20, 2, key="man_tg_nq")
            questions = []
            if int(num_questions) > 0:
                for i in range(int(num_questions)):
                    with st.expander(f"Question {i + 1}", expanded=(i == 0)):
                        q_text = st.text_input("Question", key=f"man_tg_q{i}_text")
                        opts_text = st.text_area("Options (one per line)", key=f"man_tg_q{i}_opts", height=60)
                        correct = st.text_input("Correct Answer", key=f"man_tg_q{i}_correct")
                        questions.append({
                            "question": q_text,
                            "options": [o.strip() for o in opts_text.split("\n") if o.strip()],
                            "correct_answer": correct,
                        })
            content_dict["assessment_questions"] = questions

        elif selected_template == "internal_memo":
            content_dict["to"] = st.text_input("To", key="man_im_to")
            content_dict["from_field"] = st.text_input("From", key="man_im_from")
            content_dict["date"] = st.date_input("Date", key="man_im_date").strftime("%B %d, %Y")
            content_dict["subject"] = st.text_input("Subject", key="man_im_subject")
            content_dict["title"] = content_dict["subject"]
            num_paragraphs = st.number_input("Number of body paragraphs", 1, 10, 3, key="man_im_npara")
            paragraphs = []
            for i in range(int(num_paragraphs)):
                para = st.text_area(f"Paragraph {i + 1}", key=f"man_im_para{i}", height=80)
                paragraphs.append(para)
            content_dict["body_paragraphs"] = paragraphs
            num_actions = st.number_input("Number of action items", 0, 10, 1, key="man_im_nact")
            actions = []
            for i in range(int(num_actions)):
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    item = st.text_input(f"Action {i + 1}", key=f"man_im_act{i}_item")
                with col_b:
                    owner = st.text_input(f"Owner {i + 1}", key=f"man_im_act{i}_owner")
                with col_c:
                    due = st.text_input(f"Due Date {i + 1}", key=f"man_im_act{i}_due")
                actions.append({"item": item, "owner": owner, "due_date": due})
            content_dict["action_items"] = actions
            content_dict["cc"] = st.text_input("CC", key="man_im_cc")

        elif selected_template == "battle_card":
            content_dict["product_name"] = st.text_input("Product / Service Name", key="man_bc_product")
            content_dict["title"] = f"{content_dict['product_name']} Battle Card"
            content_dict["at_a_glance"] = st.text_area("At a Glance (elevator pitch)", key="man_bc_glance", height=60)
            comp_csv = st.text_area(
                "Competitor Comparison Table (CSV)",
                key="man_bc_comp",
                height=100,
                placeholder="Feature,Our Product,Competitor A,Competitor B\nPricing,Competitive,Expensive,Mid-range",
            )
            if comp_csv.strip():
                content_dict["competitor_comparison"] = parse_csv_to_rows(comp_csv)
            else:
                content_dict["competitor_comparison"] = []
            diff_text = st.text_area("Differentiators (one per line)", key="man_bc_diff", height=60)
            content_dict["differentiators"] = [d.strip() for d in diff_text.split("\n") if d.strip()]
            num_objections = st.number_input("Number of objection/response pairs", 1, 10, 3, key="man_bc_nobj")
            objections = []
            for i in range(int(num_objections)):
                col_a, col_b = st.columns(2)
                with col_a:
                    obj = st.text_input(f"Objection {i + 1}", key=f"man_bc_obj{i}")
                with col_b:
                    resp = st.text_input(f"Response {i + 1}", key=f"man_bc_resp{i}")
                objections.append({"objection": obj, "response": resp})
            content_dict["objection_responses"] = objections
            content_dict["talk_track"] = st.text_area("Talk Track", key="man_bc_talk", height=100)
            pricing_csv = st.text_area("Pricing Table (CSV: Tier,Price,Includes)", key="man_bc_pricing", height=80)
            if pricing_csv.strip():
                content_dict["pricing_table"] = parse_csv_to_rows(pricing_csv)
            else:
                content_dict["pricing_table"] = []

        elif selected_template == "capability_overview":
            content_dict["title"] = st.text_input("Title", key="man_co_title")
            content_dict["tagline"] = st.text_input("Tagline", key="man_co_tagline")
            num_caps = st.number_input("Number of capabilities", 1, 12, 4, key="man_co_ncap")
            capabilities = []
            for i in range(int(num_caps)):
                col_a, col_b = st.columns([1, 2])
                with col_a:
                    cap_name = st.text_input(f"Capability {i + 1} Name", key=f"man_co_cap{i}_name")
                with col_b:
                    cap_desc = st.text_input(f"Capability {i + 1} Description", key=f"man_co_cap{i}_desc")
                capabilities.append({"name": cap_name, "description": cap_desc})
            content_dict["capabilities"] = capabilities
            num_stats = st.number_input("Number of statistics", 0, 10, 3, key="man_co_nstat")
            statistics = []
            for i in range(int(num_stats)):
                col_a, col_b = st.columns(2)
                with col_a:
                    stat_label = st.text_input(f"Stat {i + 1} Label", key=f"man_co_stat{i}_label")
                with col_b:
                    stat_val = st.text_input(f"Stat {i + 1} Value", key=f"man_co_stat{i}_val")
                statistics.append({"label": stat_label, "value": stat_val})
            content_dict["statistics"] = statistics
            st.markdown("**Contact Information**")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                c_name = st.text_input("Contact Name", key="man_co_cname")
            with col_b:
                c_email = st.text_input("Contact Email", key="man_co_cemail")
            with col_c:
                c_phone = st.text_input("Contact Phone", key="man_co_cphone")
            content_dict["contact"] = {"name": c_name, "email": c_email, "phone": c_phone}

        elif selected_template == "proposal":
            content_dict["title"] = st.text_input("Proposal Title", key="man_prop_title")
            content_dict["client_name"] = st.text_input("Client Name", key="man_prop_client")
            content_dict["executive_summary"] = st.text_area("Executive Summary", key="man_prop_exec", height=100)
            content_dict["needs_analysis"] = st.text_area("Needs Analysis", key="man_prop_needs", height=100)
            content_dict["proposed_solution"] = st.text_area("Proposed Solution", key="man_prop_solution", height=120)
            scope_text = st.text_area("Scope Items (one per line)", key="man_prop_scope", height=80)
            content_dict["scope_items"] = [s.strip() for s in scope_text.split("\n") if s.strip()]
            num_phases = st.number_input("Number of timeline phases", 1, 10, 3, key="man_prop_nphase")
            timeline = []
            for i in range(int(num_phases)):
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    phase = st.text_input(f"Phase {i + 1} Name", key=f"man_prop_ph{i}_name")
                with col_b:
                    duration = st.text_input(f"Duration", key=f"man_prop_ph{i}_dur")
                with col_c:
                    deliverables = st.text_input(f"Deliverables", key=f"man_prop_ph{i}_del")
                timeline.append({"phase": phase, "duration": duration, "deliverables": deliverables})
            content_dict["timeline"] = timeline
            pricing_csv = st.text_area("Pricing (CSV: item,quantity,unit_price,total)", key="man_prop_pricing", height=80)
            if pricing_csv.strip():
                content_dict["pricing"] = parse_csv_text(pricing_csv)
            else:
                content_dict["pricing"] = []
            num_team = st.number_input("Number of team members", 0, 10, 2, key="man_prop_nteam")
            team = []
            for i in range(int(num_team)):
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    t_name = st.text_input(f"Member {i + 1} Name", key=f"man_prop_tm{i}_name")
                with col_b:
                    t_role = st.text_input(f"Role", key=f"man_prop_tm{i}_role")
                with col_c:
                    t_bio = st.text_input(f"Brief Bio", key=f"man_prop_tm{i}_bio")
                team.append({"name": t_name, "role": t_role, "bio": t_bio})
            content_dict["team_members"] = team
            content_dict["terms"] = st.text_area("Terms & Conditions", key="man_prop_terms", height=80)
            next_steps_text = st.text_area("Next Steps (one per line)", key="man_prop_next", height=60)
            content_dict["next_steps"] = [n.strip() for n in next_steps_text.split("\n") if n.strip()]

    st.divider()

    # --- Export Format ---
    st.subheader("3. Export Format")
    report_types = ["weekly_report", "monthly_report"]
    format_options = ["DOCX"]
    if PDF_GEN_AVAILABLE:
        format_options.append("PDF")
    if SPREADSHEET_GEN_AVAILABLE and selected_template in report_types:
        format_options.append("XLSX")

    export_format = st.radio("Output format", format_options, horizontal=True, key="export_format_radio")
    st.session_state.doc_export_format = export_format

    st.divider()

    # --- Generate Button ---
    st.subheader("4. Generate")

    doc_title_input = st.text_input(
        "Document title",
        value=content_dict.get("title", ""),
        key="gen_doc_title",
        placeholder=f"Enter a title for your {DOCUMENT_TEMPLATES[selected_template]['name']}",
    )

    generate_clicked = st.button("Generate Document", type="primary", use_container_width=True, key="btn_generate")

    if generate_clicked:
        doc_title = doc_title_input.strip() or f"{DOCUMENT_TEMPLATES[selected_template]['name']} - {datetime.now().strftime('%Y-%m-%d')}"

        progress = st.progress(0, text="Preparing content...")
        start_time = time.time()

        try:
            if content_mode == "AI-Assisted":
                # Validate input
                ai_topic_val = st.session_state.get("ai_topic_input", "").strip()
                if not ai_topic_val:
                    st.error("Please enter a topic or description for AI-assisted generation.")
                    st.stop()

                progress.progress(10, text="Loading brand configuration...")
                brand_config = load_brand_config()

                progress.progress(20, text="Building AI prompt...")
                system_prompt = build_document_generation_prompt(selected_template, ai_topic_val, brand_config)

                user_message = f"Create a {DOCUMENT_TEMPLATES[selected_template]['name']} about: {ai_topic_val}"
                extra_ctx = st.session_state.get("ai_extra_context", "").strip()
                if extra_ctx:
                    user_message += f"\n\nAdditional context:\n{extra_ctx}"

                # Include imported data if checkbox was checked
                if st.session_state.data_import_df is not None and st.session_state.get("use_imported_data"):
                    import pandas as pd
                    df = st.session_state.data_import_df
                    user_message += f"\n\nImported data:\n{df.to_csv(index=False)}"

                progress.progress(30, text="Generating content with AI...")
                raw_response = call_claude(system_prompt, user_message)

                progress.progress(60, text="Parsing AI response...")
                # Clean JSON from response
                cleaned = raw_response.strip()
                if cleaned.startswith("```"):
                    lines = cleaned.split("\n")
                    # Remove first and last lines (fences)
                    start_idx = 1 if lines[0].startswith("```") else 0
                    end_idx = -1 if lines[-1].strip() == "```" else len(lines)
                    cleaned = "\n".join(lines[start_idx:end_idx])

                content_dict = json.loads(cleaned)
                st.session_state.doc_ai_content_json = content_dict

                # Ensure title is set
                if "title" not in content_dict or not content_dict["title"]:
                    content_dict["title"] = doc_title

            else:
                # Manual mode - content_dict is already built from form fields
                if not content_dict.get("title"):
                    content_dict["title"] = doc_title
                progress.progress(30, text="Validating content...")

            progress.progress(70, text="Generating document...")
            result = generate_document(content_dict, selected_template, doc_title, export_format)

            progress.progress(90, text="Finalizing...")
            gen_time = time.time() - start_time

            if result["success"]:
                progress.progress(100, text="Done!")

                st.session_state.doc_generated_path = result["path"]
                st.session_state.doc_generation_time = gen_time
                st.session_state.doc_generated_content = content_dict

                # Record in database
                record_generation(doc_title, selected_template, result["path"], result["format"], gen_time)

                st.success(f"Document generated successfully in {gen_time:.1f} seconds!")

                if result.get("error"):
                    st.warning(result["error"])

                # Download button
                if result["path"] and os.path.exists(result["path"]):
                    with open(result["path"], "rb") as f:
                        file_bytes = f.read()
                    file_ext = Path(result["path"]).suffix
                    mime_map = {
                        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        ".pdf": "application/pdf",
                        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        ".json": "application/json",
                    }
                    st.download_button(
                        label=f"Download {result['format']} File",
                        data=file_bytes,
                        file_name=Path(result["path"]).name,
                        mime=mime_map.get(file_ext, "application/octet-stream"),
                        type="primary",
                        key="download_generated_doc",
                    )
            else:
                progress.progress(100, text="Failed")
                st.error(f"Document generation failed: {result.get('error', 'Unknown error')}")

        except json.JSONDecodeError as exc:
            st.error(f"Failed to parse AI-generated content as JSON. Please try again. Details: {exc}")
        except EnvironmentError as exc:
            st.error(str(exc))
        except Exception as exc:
            logger.exception("Document generation error")
            st.error(f"An error occurred during generation: {exc}")

    # Show previously generated content if available
    if st.session_state.doc_generated_path and not generate_clicked:
        st.divider()
        st.subheader("Last Generated Document")
        path = st.session_state.doc_generated_path
        if os.path.exists(path):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(f"**File:** {Path(path).name}")
                if st.session_state.doc_generation_time:
                    st.write(f"**Generation time:** {st.session_state.doc_generation_time:.1f}s")
            with col_b:
                with open(path, "rb") as f:
                    file_bytes = f.read()
                st.download_button(
                    label="Download",
                    data=file_bytes,
                    file_name=Path(path).name,
                    key="download_prev_doc",
                )

        if st.session_state.doc_ai_content_json:
            with st.expander("View generated content JSON"):
                st.json(st.session_state.doc_ai_content_json)


# ===================================================================
# TAB 2: Data Import
# ===================================================================

with tab_import:
    st.subheader("Data Import")
    st.markdown("Import data from CSV files to use in report-type documents (weekly reports, monthly reports, etc.).")

    import_method = st.radio("Import method", ["Upload CSV File", "Paste CSV Data"], horizontal=True, key="import_method")

    raw_csv = None

    if import_method == "Upload CSV File":
        uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"], key="csv_uploader")
        if uploaded_file is not None:
            try:
                raw_csv = uploaded_file.read().decode("utf-8", errors="replace")
            except Exception as exc:
                st.error(f"Failed to read uploaded file: {exc}")
    else:
        raw_csv = st.text_area(
            "Paste CSV data",
            height=200,
            key="csv_paste_area",
            placeholder="Header1,Header2,Header3\nValue1,Value2,Value3\nValue4,Value5,Value6",
        )

    if raw_csv and raw_csv.strip():
        try:
            import pandas as pd

            df = pd.read_csv(io.StringIO(raw_csv))
            st.session_state.data_import_df = df
            st.session_state.data_import_columns = list(df.columns)

            st.success(f"Parsed {len(df)} rows and {len(df.columns)} columns.")

            st.subheader("Data Preview")
            st.dataframe(df, use_container_width=True)

            st.subheader("Column Mapping")
            st.markdown("Select which columns to use in your document.")

            selected_columns = st.multiselect(
                "Columns to include",
                options=list(df.columns),
                default=list(df.columns),
                key="import_col_select",
            )

            if selected_columns:
                filtered_df = df[selected_columns]
                st.session_state.data_import_df = filtered_df
                st.dataframe(filtered_df, use_container_width=True)

            st.divider()

            col_a, col_b = st.columns(2)
            with col_a:
                data_use_type = st.selectbox(
                    "Map data to",
                    ["KPI Data (Weekly Report)", "Metrics (Monthly Report)",
                     "Results Table (Case Study)", "Reference Table (Job Aid)",
                     "Competitor Comparison (Battle Card)", "Pricing Table (Proposal)"],
                    key="data_map_type",
                )
            with col_b:
                st.write("")  # Spacer
                st.write("")
                if st.button("Use This Data", type="primary", key="btn_use_data"):
                    st.session_state.data_import_df = filtered_df if selected_columns else df
                    st.success("Data stored. Switch to the Generate Document tab to use it in your document.")

            st.subheader("Data Statistics")
            stats_cols = st.columns(4)
            with stats_cols[0]:
                st.metric("Rows", len(df))
            with stats_cols[1]:
                st.metric("Columns", len(df.columns))
            with stats_cols[2]:
                numeric_cols = df.select_dtypes(include="number").columns
                st.metric("Numeric Columns", len(numeric_cols))
            with stats_cols[3]:
                st.metric("Missing Values", int(df.isna().sum().sum()))

        except ImportError:
            st.error("pandas is required for data import. Install it with: pip install pandas")
        except Exception as exc:
            st.error(f"Failed to parse CSV data: {exc}")
    else:
        if st.session_state.data_import_df is not None:
            st.info("Previously imported data is available.")
            try:
                import pandas as pd
                st.dataframe(st.session_state.data_import_df, use_container_width=True)
            except Exception:
                st.write("Data loaded but cannot display preview.")


# ===================================================================
# TAB 3: Batch Generation
# ===================================================================

with tab_batch:
    st.subheader("Batch Document Generation")
    st.markdown("Generate multiple documents at once by uploading a specification file.")

    st.markdown("""
**Specification format (CSV):**
Each row defines one document. Required columns: `doc_type`, `title`. All other columns are passed as content fields.

**Specification format (JSON):**
A JSON array of objects, each with `doc_type`, `title`, and `content` (a nested object with template-specific fields).
    """)

    batch_file = st.file_uploader("Upload specification file", type=["csv", "json"], key="batch_uploader")

    batch_specs = None

    if batch_file is not None:
        try:
            file_ext = Path(batch_file.name).suffix.lower()
            raw_content = batch_file.read().decode("utf-8", errors="replace")

            if file_ext == ".json":
                batch_specs = json.loads(raw_content)
                if not isinstance(batch_specs, list):
                    st.error("JSON file must contain a top-level array of document specifications.")
                    batch_specs = None
            elif file_ext == ".csv":
                reader = csv.DictReader(io.StringIO(raw_content))
                rows = list(reader)
                batch_specs = []
                for row in rows:
                    spec = {
                        "doc_type": row.get("doc_type", "job_aid"),
                        "title": row.get("title", "Untitled"),
                        "content": {k: v for k, v in row.items() if k not in ("doc_type", "title")},
                    }
                    batch_specs.append(spec)

            if batch_specs:
                st.session_state.batch_specs = batch_specs

        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")
        except Exception as exc:
            st.error(f"Failed to parse batch file: {exc}")

    # Display batch preview
    if st.session_state.batch_specs:
        specs = st.session_state.batch_specs
        st.subheader(f"Batch Preview ({len(specs)} documents)")

        try:
            import pandas as pd
            preview_data = []
            for i, spec in enumerate(specs):
                doc_type_key = spec.get("doc_type", "unknown")
                tmpl_info = DOCUMENT_TEMPLATES.get(doc_type_key, {})
                preview_data.append({
                    "#": i + 1,
                    "Title": spec.get("title", "Untitled"),
                    "Document Type": tmpl_info.get("name", doc_type_key),
                    "Typical Pages": tmpl_info.get("typical_pages", "N/A"),
                })
            preview_df = pd.DataFrame(preview_data)
            st.dataframe(preview_df, use_container_width=True, hide_index=True)
        except ImportError:
            for i, spec in enumerate(specs):
                st.write(f"{i + 1}. **{spec.get('title', 'Untitled')}** - {spec.get('doc_type', 'unknown')}")

        st.divider()

        batch_format = st.radio("Export format for all", ["DOCX", "PDF"], horizontal=True, key="batch_format")

        col_a, col_b = st.columns(2)
        with col_a:
            use_ai_batch = st.checkbox("Use AI to generate content for each document", value=False, key="batch_ai_mode")
        with col_b:
            download_zip = st.checkbox("Package all files as ZIP", value=True, key="batch_zip")

        if st.button("Generate All", type="primary", use_container_width=True, key="btn_batch_generate"):
            results = []
            total = len(specs)
            progress = st.progress(0, text=f"Generating 0/{total} documents...")
            start_time = time.time()

            # Create batch job record
            try:
                session = get_session()
                batch_job = BatchJob(
                    name=f"Batch - {total} documents - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    status="running",
                    items_json=json.dumps([{"title": s.get("title"), "doc_type": s.get("doc_type")} for s in specs]),
                    created_at=datetime.utcnow(),
                )
                session.add(batch_job)
                session.commit()
                batch_job_id = batch_job.id
                session.close()
            except Exception as exc:
                logger.warning("Failed to create batch job record: %s", exc)
                batch_job_id = None

            for idx, spec in enumerate(specs):
                doc_type = spec.get("doc_type", "job_aid")
                doc_title = spec.get("title", f"Document {idx + 1}")
                content = spec.get("content", {})

                progress.progress((idx / total), text=f"Generating {idx + 1}/{total}: {doc_title}...")

                try:
                    if use_ai_batch and content:
                        brand_config = load_brand_config()
                        system_prompt = build_document_generation_prompt(doc_type, json.dumps(content), brand_config)
                        user_msg = f"Create a {DOCUMENT_TEMPLATES.get(doc_type, {}).get('name', doc_type)} with these specifications: {json.dumps(content)}"
                        raw_resp = call_claude(system_prompt, user_msg)
                        cleaned = raw_resp.strip()
                        if cleaned.startswith("```"):
                            lines = cleaned.split("\n")
                            start_i = 1
                            end_i = -1 if lines[-1].strip() == "```" else len(lines)
                            cleaned = "\n".join(lines[start_i:end_i])
                        content = json.loads(cleaned)
                    elif not content:
                        content = {"title": doc_title}

                    result = generate_document(content, doc_type, doc_title, batch_format)
                    result["title"] = doc_title
                    result["doc_type"] = doc_type
                    results.append(result)

                    if result["success"]:
                        record_generation(doc_title, doc_type, result.get("path", ""), result.get("format", batch_format),
                                          time.time() - start_time)

                except Exception as exc:
                    logger.warning("Batch item %d failed: %s", idx, exc)
                    results.append({"success": False, "title": doc_title, "doc_type": doc_type, "error": str(exc), "path": None})

            progress.progress(100, text="Batch complete!")
            total_time = time.time() - start_time
            st.session_state.batch_results = results

            # Update batch job
            try:
                session = get_session()
                if batch_job_id:
                    job = session.query(BatchJob).get(batch_job_id)
                    if job:
                        job.status = "completed"
                        job.completed_at = datetime.utcnow()
                        job.results_json = json.dumps([{"title": r.get("title"), "success": r.get("success"), "path": r.get("path")} for r in results])
                        session.commit()
                session.close()
            except Exception as exc:
                logger.warning("Failed to update batch job: %s", exc)

            # Summary
            successful = sum(1 for r in results if r.get("success"))
            failed = total - successful
            st.success(f"Batch complete: {successful}/{total} documents generated in {total_time:.1f}s.")
            if failed > 0:
                st.warning(f"{failed} document(s) failed. Check details below.")

            # Results table
            for r in results:
                icon = "+" if r.get("success") else "-"
                status_label = "Success" if r.get("success") else "Failed"
                st.markdown(f"**{r.get('title', 'Unknown')}** - {status_label}")
                if r.get("error"):
                    st.caption(r["error"])

            # ZIP download
            if download_zip and successful > 0:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for r in results:
                        if r.get("success") and r.get("path") and os.path.exists(r["path"]):
                            zf.write(r["path"], Path(r["path"]).name)
                zip_buffer.seek(0)
                st.download_button(
                    label="Download All (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"batch_documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip",
                    type="primary",
                    key="download_batch_zip",
                )
            elif successful > 0:
                for r in results:
                    if r.get("success") and r.get("path") and os.path.exists(r["path"]):
                        with open(r["path"], "rb") as f:
                            st.download_button(
                                label=f"Download: {Path(r['path']).name}",
                                data=f.read(),
                                file_name=Path(r["path"]).name,
                                key=f"download_batch_{r['path']}",
                            )

    # Show previous batch results
    elif st.session_state.batch_results:
        st.subheader("Previous Batch Results")
        for r in st.session_state.batch_results:
            status_label = "Success" if r.get("success") else "Failed"
            st.markdown(f"**{r.get('title', 'Unknown')}** - {status_label}")
            if r.get("success") and r.get("path") and os.path.exists(r["path"]):
                with open(r["path"], "rb") as f:
                    st.download_button(
                        label=f"Download: {Path(r['path']).name}",
                        data=f.read(),
                        file_name=Path(r["path"]).name,
                        key=f"download_prev_batch_{r['path']}",
                    )


# ===================================================================
# TAB 4: Templates
# ===================================================================

with tab_templates:
    st.subheader("Document Templates")
    st.markdown("Browse available document templates and manage custom templates.")

    # Built-in templates grid
    st.markdown("### Built-in Templates")
    tmpl_keys = list(DOCUMENT_TEMPLATES.keys())

    for row_start in range(0, len(tmpl_keys), 2):
        cols = st.columns(2)
        for col_idx in range(2):
            tmpl_idx = row_start + col_idx
            if tmpl_idx < len(tmpl_keys):
                tkey = tmpl_keys[tmpl_idx]
                tmpl = DOCUMENT_TEMPLATES[tkey]
                with cols[col_idx]:
                    use_cases_html = " ".join(
                        f'<span class="use-case-tag">{uc}</span>'
                        for uc in tmpl.get("use_cases", [])
                    )
                    st.markdown(f"""<div class="doc-card">
<h4 style="margin-top:0;">{tmpl["name"]}</h4>
<p style="color:#666; font-size:14px;">{tmpl["description"]}</p>
<p><span class="template-badge">{tkey}</span> <span class="pages-badge">{tmpl["typical_pages"]} pages</span></p>
<div>{use_cases_html}</div>
</div>""", unsafe_allow_html=True)

    st.divider()

    # Custom template upload
    st.markdown("### Custom Templates")
    st.markdown("Upload a custom DOCX template to use as a base for document generation.")

    uploaded_template = st.file_uploader("Upload DOCX template", type=["docx"], key="custom_template_upload")

    if uploaded_template is not None:
        custom_name = st.text_input("Template name", value=Path(uploaded_template.name).stem, key="custom_tmpl_name")
        custom_desc = st.text_area("Template description", key="custom_tmpl_desc", height=60)
        custom_type = st.selectbox("Template type", list(DOCUMENT_TEMPLATES.keys()),
                                   format_func=lambda k: DOCUMENT_TEMPLATES[k]["name"], key="custom_tmpl_type")

        if st.button("Save Template", type="primary", key="btn_save_template"):
            try:
                TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
                save_path = TEMPLATES_DIR / uploaded_template.name
                with open(save_path, "wb") as f:
                    f.write(uploaded_template.read())

                session = get_session()
                new_template = Template(
                    name=custom_name or uploaded_template.name,
                    template_type="docx",
                    file_path=str(save_path),
                    description=custom_desc,
                    created_at=datetime.utcnow(),
                )
                session.add(new_template)
                session.commit()
                session.close()

                st.success(f"Template '{custom_name}' saved successfully!")
            except Exception as exc:
                st.error(f"Failed to save template: {exc}")

    # List custom templates from database
    st.divider()
    st.markdown("### Saved Custom Templates")

    try:
        session = get_session()
        custom_templates = session.query(Template).filter(Template.template_type == "docx").order_by(Template.created_at.desc()).all()
        session.close()

        if custom_templates:
            for tmpl in custom_templates:
                col_a, col_b, col_c = st.columns([3, 1, 1])
                with col_a:
                    st.write(f"**{tmpl.name}**")
                    if tmpl.description:
                        st.caption(tmpl.description)
                with col_b:
                    st.caption(f"Created: {tmpl.created_at.strftime('%Y-%m-%d') if tmpl.created_at else 'N/A'}")
                    st.caption(f"Used: {tmpl.usage_count or 0} times")
                with col_c:
                    if tmpl.file_path and os.path.exists(tmpl.file_path):
                        with open(tmpl.file_path, "rb") as f:
                            st.download_button(
                                label="Download",
                                data=f.read(),
                                file_name=Path(tmpl.file_path).name,
                                key=f"download_tmpl_{tmpl.id}",
                            )
                    if st.button("Delete", key=f"delete_tmpl_{tmpl.id}"):
                        try:
                            sess = get_session()
                            to_delete = sess.query(Template).get(tmpl.id)
                            if to_delete:
                                if to_delete.file_path and os.path.exists(to_delete.file_path):
                                    os.remove(to_delete.file_path)
                                sess.delete(to_delete)
                                sess.commit()
                            sess.close()
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Failed to delete template: {exc}")
                st.divider()
        else:
            st.info("No custom templates uploaded yet.")
    except Exception as exc:
        st.warning(f"Could not load custom templates: {exc}")


# ===================================================================
# TAB 5: History
# ===================================================================

with tab_history:
    st.subheader("Generation History")
    st.markdown("View and manage previously generated documents.")

    try:
        session = get_session()
        history_records = (
            session.query(GeneratedContent)
            .filter(GeneratedContent.content_type == "document")
            .order_by(GeneratedContent.generated_at.desc())
            .limit(100)
            .all()
        )
        session.close()

        if history_records:
            # Summary metrics
            metric_cols = st.columns(4)
            with metric_cols[0]:
                st.metric("Total Documents", len(history_records))
            with metric_cols[1]:
                avg_time = sum(r.generation_time_seconds or 0 for r in history_records) / max(len(history_records), 1)
                st.metric("Avg Generation Time", f"{avg_time:.1f}s")
            with metric_cols[2]:
                formats = {}
                for r in history_records:
                    fmt = r.format or "Unknown"
                    formats[fmt] = formats.get(fmt, 0) + 1
                most_common_fmt = max(formats, key=formats.get) if formats else "N/A"
                st.metric("Most Used Format", most_common_fmt)
            with metric_cols[3]:
                today_count = sum(
                    1 for r in history_records
                    if r.generated_at and r.generated_at.date() == date.today()
                )
                st.metric("Generated Today", today_count)

            st.divider()

            # Filter controls
            filter_cols = st.columns(3)
            with filter_cols[0]:
                type_options = sorted(set(
                    (r.input_summary or "").replace("Document type: ", "")
                    for r in history_records if r.input_summary
                ))
                type_filter = st.multiselect("Filter by document type", type_options, key="history_type_filter")
            with filter_cols[1]:
                format_options = sorted(set(r.format or "Unknown" for r in history_records))
                format_filter = st.multiselect("Filter by format", format_options, key="history_format_filter")
            with filter_cols[2]:
                search_query = st.text_input("Search by title", key="history_search")

            # Apply filters
            filtered = history_records
            if type_filter:
                filtered = [r for r in filtered if any(
                    t in (r.input_summary or "") for t in type_filter
                )]
            if format_filter:
                filtered = [r for r in filtered if (r.format or "Unknown") in format_filter]
            if search_query:
                q = search_query.lower()
                filtered = [r for r in filtered if q in (r.title or "").lower()]

            st.caption(f"Showing {len(filtered)} of {len(history_records)} records")

            # Display records
            for record in filtered:
                with st.container():
                    col_title, col_type, col_date, col_format, col_actions = st.columns([3, 2, 2, 1, 3])

                    with col_title:
                        st.write(f"**{record.title}**")

                    with col_type:
                        doc_type_display = (record.input_summary or "").replace("Document type: ", "")
                        tmpl_info = DOCUMENT_TEMPLATES.get(doc_type_display, {})
                        display_name = tmpl_info.get("name", doc_type_display)
                        st.write(display_name)

                    with col_date:
                        if record.generated_at:
                            st.write(record.generated_at.strftime("%Y-%m-%d %H:%M"))
                        else:
                            st.write("N/A")

                    with col_format:
                        st.write(record.format or "N/A")

                    with col_actions:
                        action_cols = st.columns(4)

                        # Download
                        with action_cols[0]:
                            if record.output_path and os.path.exists(record.output_path):
                                with open(record.output_path, "rb") as f:
                                    st.download_button(
                                        label="DL",
                                        data=f.read(),
                                        file_name=Path(record.output_path).name,
                                        key=f"hist_dl_{record.id}",
                                    )
                            else:
                                st.button("DL", disabled=True, key=f"hist_dl_dis_{record.id}")

                        # Add to Library
                        with action_cols[1]:
                            if st.button("Lib", key=f"hist_lib_{record.id}"):
                                try:
                                    sess = get_session()
                                    existing = sess.query(ContentLibraryItem).filter(
                                        ContentLibraryItem.generated_content_id == record.id
                                    ).first()
                                    if existing:
                                        st.warning("Already in library.")
                                    else:
                                        lib_item = ContentLibraryItem(
                                            generated_content_id=record.id,
                                            title=record.title,
                                            description=record.input_summary,
                                            category="document",
                                            tags=(record.input_summary or "").replace("Document type: ", ""),
                                            is_approved=False,
                                        )
                                        sess.add(lib_item)
                                        sess.commit()
                                        st.success("Added to library!")
                                    sess.close()
                                except Exception as exc:
                                    st.error(f"Error: {exc}")

                        # Export as PDF
                        with action_cols[2]:
                            if record.output_path and record.format != "PDF" and PDF_GEN_AVAILABLE:
                                if st.button("PDF", key=f"hist_pdf_{record.id}"):
                                    try:
                                        pdf_gen = PDFGenerator()
                                        if pdf_gen.available:
                                            pdf_path = str(Path(record.output_path).with_suffix(".pdf"))
                                            result = pdf_gen.convert_docx_to_pdf(record.output_path, pdf_path)
                                            if result["success"]:
                                                st.success("PDF exported!")
                                                with open(pdf_path, "rb") as f:
                                                    st.download_button(
                                                        label="Get PDF",
                                                        data=f.read(),
                                                        file_name=Path(pdf_path).name,
                                                        key=f"hist_getpdf_{record.id}",
                                                    )
                                            else:
                                                st.error(f"PDF conversion failed: {result.get('error')}")
                                        else:
                                            st.warning("PDF converter not available.")
                                    except Exception as exc:
                                        st.error(f"PDF export error: {exc}")
                            else:
                                st.button("PDF", disabled=True, key=f"hist_pdf_dis_{record.id}")

                        # Delete
                        with action_cols[3]:
                            if st.button("Del", key=f"hist_del_{record.id}"):
                                try:
                                    sess = get_session()
                                    to_del = sess.query(GeneratedContent).get(record.id)
                                    if to_del:
                                        if to_del.output_path and os.path.exists(to_del.output_path):
                                            os.remove(to_del.output_path)
                                        # Remove associated library items
                                        sess.query(ContentLibraryItem).filter(
                                            ContentLibraryItem.generated_content_id == record.id
                                        ).delete()
                                        sess.delete(to_del)
                                        sess.commit()
                                    sess.close()
                                    st.rerun()
                                except Exception as exc:
                                    st.error(f"Delete failed: {exc}")

                    st.divider()
        else:
            st.info("No documents have been generated yet. Use the Generate Document tab to create your first document.")

    except Exception as exc:
        st.warning(f"Could not load generation history: {exc}")
        st.info("The database may not be initialized. Generate a document first to create the necessary tables.")


# ---------------------------------------------------------------------------
# Sidebar summary
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("---")
    st.markdown("### Document Factory")
    st.caption(f"Templates available: {len(DOCUMENT_TEMPLATES)}")
    st.caption(f"Document generator: {'Available' if DOCUMENT_GEN_AVAILABLE else 'Not installed'}")
    st.caption(f"PDF export: {'Available' if PDF_GEN_AVAILABLE else 'Not installed'}")
    st.caption(f"Spreadsheet export: {'Available' if SPREADSHEET_GEN_AVAILABLE else 'Not installed'}")

    if st.session_state.doc_generated_path:
        st.markdown("---")
        st.markdown("**Last generated:**")
        st.caption(Path(st.session_state.doc_generated_path).name)
