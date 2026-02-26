# Brand Intelligence Content Hub - Comprehensive Build Document

**Version:** 1.0.0
**Date:** February 26, 2026
**Platform:** Streamlit (Python)
**Port:** localhost:8501
**Total Codebase:** 47,052 lines of Python across 50+ modules
**Current Brand:** Teleperformance (TP)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture & Technology Stack](#2-architecture--technology-stack)
3. [Project Structure](#3-project-structure)
4. [Configuration & Environment](#4-configuration--environment)
5. [Database Architecture](#5-database-architecture)
6. [Application Pages (UI Layer)](#6-application-pages-ui-layer)
7. [Content Generators](#7-content-generators)
8. [AI Copilot Engine](#8-ai-copilot-engine)
9. [Brand Management Modules](#9-brand-management-modules)
10. [File Ingestion & Parsing](#10-file-ingestion--parsing)
11. [External Integrations](#11-external-integrations)
12. [Core Utilities](#12-core-utilities)
13. [Brand Configuration (Active)](#13-brand-configuration-active)
14. [Generated Content Inventory](#14-generated-content-inventory)
15. [Setup & Deployment](#15-setup--deployment)
16. [Data Flow & Architecture Diagrams](#16-data-flow--architecture-diagrams)

---

## 1. System Overview

The **Brand Intelligence Content Hub** is a centralized AI-powered Streamlit application that manages brand identity and generates on-brand content at scale. It serves as a single platform for:

- **Brand Identity Management** -- Centralized repository for colors, fonts, voice, terminology, logos, and templates
- **AI-Powered Content Generation** -- Claude-driven generation of presentations, documents, training materials, visuals, reports, and more
- **Agentic AI Copilot** -- Conversational interface with 20+ structured tools for intelligent content workflows
- **Content Lifecycle Management** -- Library curation, approval workflows, version tracking, and analytics
- **Batch Processing** -- Queue-based bulk content generation across all content types
- **Enterprise Analytics** -- Generation metrics, cost tracking, quality scores, and system health monitoring

### Key Statistics

| Metric | Value |
|--------|-------|
| Python Modules | 50+ files |
| Total Lines of Code | 47,052 |
| Streamlit Pages | 12 (including Copilot landing) |
| Content Generators | 9 specialized generators |
| Database Tables | 9 SQLAlchemy models |
| ChromaDB Collections | 4 semantic vector collections |
| Copilot Tools | 20+ structured Claude tools |
| Document Types | 10 branded templates |
| Visual Types | 8 diagram/infographic types |
| Training Deliverables | 7 output types per pipeline run |
| Python Dependencies | 16 packages |

---

## 2. Architecture & Technology Stack

### Frontend
| Component | Technology | Version |
|-----------|-----------|---------|
| Web Framework | Streamlit | >= 1.30.0 |
| Layout | Wide mode, expanded sidebar | -- |
| Styling | Custom CSS (dark sidebar, branded accent colors) | -- |
| Charts | Plotly (with Streamlit fallback) | >= 5.18.0 |
| Data Tables | Pandas DataFrames | >= 2.0.0 |

### Backend
| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.14 |
| ORM | SQLAlchemy | >= 2.0.0 |
| Database | SQLite | (bundled) |
| Vector Store | ChromaDB | >= 0.4.0 |
| Environment | python-dotenv | >= 1.0.0 |
| Token Counting | tiktoken | >= 0.5.0 |

### AI / ML
| Component | Technology | Model |
|-----------|-----------|-------|
| Primary LLM | Anthropic Claude API | claude-sonnet-4-20250514 |
| Tool Use | Claude tool_use | Structured tool definitions |
| Embeddings | ChromaDB default | -- |

### Content Generation
| Component | Technology | Version |
|-----------|-----------|---------|
| Presentations | python-pptx | >= 0.6.21 |
| Documents | python-docx | >= 1.0.0 |
| PDF Extraction | pdfplumber | >= 0.10.0 |
| PDF Conversion | LibreOffice (headless) | System install |
| Spreadsheets | openpyxl | (via python) |
| Image Processing | Pillow | >= 10.0.0 |
| Color Extraction | colorthief | >= 0.2.1 |
| Web Scraping | BeautifulSoup4 + requests | >= 4.12.0 / >= 2.31.0 |

### External Services
| Service | Purpose | Required |
|---------|---------|----------|
| Anthropic Claude | Core AI engine | Yes |
| Napkin AI | Diagram/infographic generation | Yes |
| Presenton | AI presentation generation (Docker) | No |
| DeepL | Multi-language translation | No |
| Pexels | Stock photos & videos | No |
| Google Workspace | Doc export to Google Drive | No |

---

## 3. Project Structure

```
brand-hub/
├── app/                              # Main application package
│   ├── __init__.py
│   ├── main.py                       # Streamlit entry point (267 lines)
│   ├── config.py                     # Environment & path configuration (144 lines)
│   │
│   ├── pages/                        # Streamlit multi-page app (12 pages)
│   │   ├── 00_Copilot.py            # AI chat interface (DEFAULT landing)
│   │   ├── 01_Dashboard.py          # Brand health & metrics overview
│   │   ├── 02_Brand_Repository.py   # 6-tab brand management (70.6 KB)
│   │   ├── 03_Content_Generator.py  # Quick-access generation forms
│   │   ├── 04_Presentation_Studio.py # Interactive PPTX workspace (58.5 KB)
│   │   ├── 05_Training_Builder.py   # Training package pipeline (83.1 KB)
│   │   ├── 06_Document_Factory.py   # 10-type document generator (92.5 KB)
│   │   ├── 07_Visual_Studio.py      # Diagram/infographic studio (77 KB)
│   │   ├── 08_Content_Library.py    # Content catalog & approvals (95 KB)
│   │   ├── 09_Batch_Processing.py   # Bulk content generation (78 KB)
│   │   ├── 10_Analytics.py          # Insights & dashboards (82.5 KB)
│   │   └── 11_Settings.py           # Configuration management (103.1 KB)
│   │
│   ├── database/                     # Data persistence layer
│   │   ├── __init__.py
│   │   ├── models.py                # SQLAlchemy models (9 tables)
│   │   └── vector_store.py          # ChromaDB wrapper (4 collections)
│   │
│   ├── brand/                        # Brand management engines
│   │   ├── __init__.py
│   │   ├── asset_manager.py         # File upload & organization
│   │   ├── brand_wizard.py          # Auto-extract brand from URL + files
│   │   ├── color_extractor.py       # Extract colors from logos (colorthief)
│   │   └── voice_analyzer.py        # AI brand voice profiling (Claude)
│   │
│   ├── generators/                   # Content generation engines
│   │   ├── __init__.py
│   │   ├── presentation_gen.py      # PPTX generation (python-pptx)
│   │   ├── document_gen.py          # DOCX generation (python-docx)
│   │   ├── training_pipeline.py     # Multi-format training packages
│   │   ├── visual_gen.py            # Napkin AI visual pipeline
│   │   ├── quiz_gen.py              # Assessment/quiz generation
│   │   ├── spreadsheet_gen.py       # Branded Excel workbooks
│   │   ├── pdf_gen.py               # DOCX → PDF conversion
│   │   └── google_export.py         # Google Workspace export
│   │
│   ├── ingestion/                    # File parsing & classification
│   │   ├── __init__.py
│   │   ├── pdf_parser.py            # PDF text extraction (pdfplumber)
│   │   ├── docx_parser.py           # DOCX text extraction
│   │   ├── pptx_parser.py           # PPTX text extraction
│   │   ├── url_scraper.py           # Web page scraping
│   │   ├── curriculum_parser.py     # AI curriculum structuring
│   │   ├── chunker.py              # Semantic text chunking (tiktoken)
│   │   └── smart_classifier.py     # AI auto-classification of uploads
│   │
│   ├── copilot/                      # Agentic AI engine
│   │   ├── __init__.py
│   │   ├── engine.py               # Main CopilotEngine (Claude tool loop)
│   │   ├── tools.py                # 20+ structured tool definitions
│   │   ├── tool_handlers.py        # Tool execution logic
│   │   ├── context_builder.py      # System prompt construction
│   │   ├── response_renderer.py    # UI formatting for responses
│   │   ├── conversation.py         # Chat history management
│   │   ├── project_tracker.py      # Goal/project tracking
│   │   ├── audit_log.py            # Action logging & cost estimation
│   │   └── verification.py         # Source attribution & knowledge modes
│   │
│   ├── integrations/                 # External API clients
│   │   ├── __init__.py
│   │   ├── napkin_client.py         # Napkin AI diagram API
│   │   ├── presenton_client.py      # Presenton presentation service
│   │   └── translation_client.py   # DeepL translation API
│   │
│   ├── core/                         # Core business logic
│   │   ├── __init__.py
│   │   └── feedback_loop.py         # Quality feedback & improvement engine
│   │
│   └── utils/                        # Utility modules
│       ├── __init__.py
│       └── analytics.py             # AnalyticsEngine (metrics, costs, trends)
│
├── brand_assets/                     # Brand repository storage
│   ├── logos/                        # Logo files (PNG, PDF, SVG)
│   │   ├── GMT_Logo TP_CMYK_Feb 2025.pdf
│   │   ├── GMT_Logo TP_RGB_Feb 2025_white.png
│   │   └── (timestamped variants)
│   ├── fonts/                        # Font files
│   ├── colors/                       # Color palette exports
│   ├── templates/                    # Branded templates
│   │   ├── pptx/                    # PowerPoint templates
│   │   ├── docx/                    # Word templates
│   │   ├── brand_guidelines/        # Brand guideline PDFs
│   │   ├── GMT_Case study_template.pptx
│   │   ├── GMT_PPT_Template_Global TP.pptx
│   │   └── GMT_Word Template A4.docx
│   ├── collateral/                   # Marketing collateral
│   └── sample_content/               # Reference content samples
│
├── output/                           # Generated content output
│   ├── presentations/                # Generated PPTX files
│   ├── documents/                    # Generated DOCX files
│   ├── training/                     # Training packages (PPTX, DOCX, ZIP)
│   ├── visuals/                      # Generated diagrams (PNG, SVG)
│   ├── infographics/                 # Generated infographics
│   ├── translations/                 # Translated content
│   ├── reports/                      # Generated reports (XLSX)
│   └── exports/                      # Bulk exports
│
├── data/                             # Application data
│   ├── brand_hub.db                  # SQLite database
│   ├── chromadb/                     # ChromaDB vector store
│   ├── uploads/                      # User-uploaded files
│   ├── presenton/                    # Presenton service data
│   └── cache/                        # Application cache
│
├── venv/                             # Python virtual environment
├── brand_config.json                 # Active brand configuration
├── requirements.txt                  # Python dependencies (16 packages)
├── setup.sh                          # Automated setup script
├── docker-compose.yml                # Presenton Docker service
├── .env                              # Environment variables (API keys)
├── .env.example                      # Environment template
└── README.md                         # Project documentation
```

---

## 4. Configuration & Environment

### 4.1 Configuration Module (`app/config.py`)

The configuration module handles environment loading, path management, and validation.

**Directory Constants:**
```python
BASE_DIR        = /Users/.../brand-hub          # Project root
DATA_DIR        = BASE_DIR / "data"             # SQLite + ChromaDB
BRAND_ASSETS_DIR = BASE_DIR / "brand_assets"    # Brand repository
OUTPUT_DIR      = BASE_DIR / "output"           # Generated content

# Data subdirectories
CHROMADB_DIR    = DATA_DIR / "chromadb"
PRESENTON_DIR   = DATA_DIR / "presenton"
UPLOADS_DIR     = DATA_DIR / "uploads"
CACHE_DIR       = DATA_DIR / "cache"

# Output subdirectories
PRESENTATIONS_DIR = OUTPUT_DIR / "presentations"
DOCUMENTS_DIR     = OUTPUT_DIR / "documents"
TRAINING_DIR      = OUTPUT_DIR / "training"
VISUALS_DIR       = OUTPUT_DIR / "visuals"
INFOGRAPHICS_DIR  = OUTPUT_DIR / "infographics"
TRANSLATIONS_DIR  = OUTPUT_DIR / "translations"
REPORTS_DIR       = OUTPUT_DIR / "reports"
EXPORTS_DIR       = OUTPUT_DIR / "exports"

# Brand asset subdirectories
LOGOS_DIR      = BRAND_ASSETS_DIR / "logos"
FONTS_DIR      = BRAND_ASSETS_DIR / "fonts"
TEMPLATES_DIR  = BRAND_ASSETS_DIR / "templates"
```

**Key Functions:**
| Function | Purpose |
|----------|---------|
| `validate_env()` | Check all required env vars are set; raises `EnvironmentError` if missing |
| `get_env(key)` | Get env var with optional-key defaults fallback |
| `get_db_url()` | Return SQLAlchemy connection string for SQLite |
| `get_chroma_path()` | Return filesystem path for ChromaDB storage |
| `ensure_directories()` | Create all 17 project directories if they don't exist |

### 4.2 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | **Yes** | -- | Claude API key for all AI features |
| `NAPKIN_API_TOKEN` | **Yes** | -- | Napkin AI token for diagram generation |
| `PRESENTON_URL` | No | `http://localhost:5001` | Presenton AI presentation service URL |
| `DEEPL_API_KEY` | No | `""` | DeepL translation API key |
| `PEXELS_API_KEY` | No | `""` | Pexels stock media API key |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | No | `""` | Google Cloud service account JSON path |
| `GOOGLE_OAUTH_CREDENTIALS_JSON` | No | `""` | Google OAuth credentials JSON path |

---

## 5. Database Architecture

### 5.1 SQLite Database (`data/brand_hub.db`)

**ORM:** SQLAlchemy 2.0+
**Session Management:** Lazy sessions via `get_session()` context manager
**Initialization:** `init_db()` creates all tables on first run

#### Database Models

**1. BrandProfile**
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| name | String(200) | Profile name |
| description | Text | Profile description |
| config_json | Text | Full brand config as JSON |
| is_active | Boolean | Currently active profile |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**2. BrandAsset**
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| filename | String(500) | Original filename |
| asset_type | String(50) | Type: logo, font, template, collateral, sample |
| file_path | String(1000) | Full filesystem path |
| file_size | Integer | File size in bytes |
| mime_type | String(100) | MIME type |
| description | Text | Asset description |
| tags | Text | Comma-separated tags |
| metadata_json | Text | Additional metadata as JSON |
| is_active | Boolean | Active/archived status |
| created_at | DateTime | Upload timestamp |

**3. BrandConfig**
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| config_key | String(200) | Configuration key (unique) |
| config_value | Text | Configuration value (JSON) |
| updated_at | DateTime | Last update timestamp |

**4. Template**
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| name | String(300) | Template name |
| template_type | String(50) | Type: pptx, docx, training, visual |
| description | Text | Template description |
| file_path | String(1000) | Template file path |
| frozen_zones | Text | JSON of non-editable zones |
| editable_zones | Text | JSON of editable zones |
| metadata_json | Text | Additional metadata |
| is_active | Boolean | Active status |
| created_at | DateTime | Creation timestamp |

**5. GeneratedContent**
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| title | String(500) | Content title |
| content_type | String(50) | Type: presentation, document, training, visual, report |
| output_path | String(1000) | Output file path |
| output_format | String(20) | File format (pptx, docx, pdf, png, etc.) |
| generation_time | Float | Time taken to generate (seconds) |
| summary | Text | Content summary |
| prompt_used | Text | Generation prompt |
| model_used | String(100) | AI model used |
| confidence_score | Float | AI confidence (0.0-1.0) |
| sources | Text | Source documents JSON |
| version | Integer | Content version number |
| status | String(20) | Status: draft, review, approved, published |
| rating | Float | User rating (1-5) |
| generated_at | DateTime | Generation timestamp |

**6. ContentLibraryItem**
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| title | String(500) | Item title |
| description | Text | Item description |
| content_type | String(50) | Content type |
| tags | Text | Comma-separated tags |
| category | String(100) | Content category |
| file_path | String(1000) | File path |
| generated_content_id | Integer (FK) | Link to GeneratedContent |
| is_approved | Boolean | Approval status |
| approved_by | String(200) | Approver name |
| approved_at | DateTime | Approval timestamp |
| download_count | Integer | Download counter |
| rating | Float | User rating |
| metadata_json | Text | Additional metadata |
| created_at | DateTime | Creation timestamp |

**7. PromptTemplate**
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| name | String(300) | Template name |
| content_type | String(50) | Target content type |
| system_prompt | Text | System prompt template |
| user_prompt | Text | User prompt template |
| variables | Text | JSON list of template variables |
| version | Integer | Template version |
| is_active | Boolean | Active status |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**8. BatchJob**
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| job_name | String(300) | Batch job name |
| content_type | String(50) | Content type for batch |
| items_json | Text | JSON array of batch items |
| total_items | Integer | Total items in batch |
| completed_items | Integer | Completed item count |
| failed_items | Integer | Failed item count |
| status | String(20) | Status: queued, processing, completed, failed |
| results_json | Text | JSON results for each item |
| started_at | DateTime | Start timestamp |
| completed_at | DateTime | Completion timestamp |
| created_at | DateTime | Creation timestamp |

**9. CopilotAuditLog**
| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Auto-increment ID |
| session_id | String(100) | Session identifier |
| action_type | String(50) | Action type (tool_call, confirmation, generation) |
| tool_name | String(100) | Tool name used |
| input_summary | Text | Input summary |
| output_summary | Text | Output summary |
| confirmed | Boolean | User confirmation status |
| cost_estimate | Float | Estimated API cost |
| tokens_used | Integer | Tokens consumed |
| duration_ms | Integer | Execution time in milliseconds |
| created_at | DateTime | Timestamp |

### 5.2 ChromaDB Vector Store (`data/chromadb/`)

**Wrapper:** `app/database/vector_store.py`
**Fallback:** In-memory storage if ChromaDB persistence fails

| Collection | Purpose | Content |
|------------|---------|---------|
| `brand_content` | Ingested brand collateral and materials | Text chunks from PDFs, DOCX, PPTX |
| `brand_voice` | Voice analysis samples | Tone, style, and messaging examples |
| `generated_examples` | Approved output examples | High-quality generated content for reference |
| `terminology` | Brand-specific terms | Glossary entries, acronyms, preferred terms |

**Chunking Parameters:**
- Max chunk size: 750 tokens
- Overlap: 100 tokens
- Tokenizer: tiktoken

---

## 6. Application Pages (UI Layer)

### 6.1 Main Entry Point (`app/main.py`)

**Purpose:** Streamlit application bootstrapper
**Actions on Load:**
1. Set page config (wide layout, expanded sidebar, page title + icon)
2. Inject custom CSS (dark sidebar #1a1a2e, branded buttons #0066cc, card styling, status indicators)
3. Initialize database via `init_db()`
4. Validate environment variables
5. Render sidebar (navigation, system status indicator)
6. Render welcome page with 3 feature cards (Brand Setup, Content Engine, Analytics)

**Custom CSS Classes:**
- `.brand-card` -- Gradient card with border radius and shadow
- `.status-dot` -- System status indicator (green/yellow/red)
- `.status-green` / `.status-yellow` / `.status-red` -- Status colors
- `.section-divider` -- Blue horizontal rule

---

### 6.2 Page 00: Copilot (Default Landing)

**File:** `app/pages/00_Copilot.py`
**Purpose:** AI-powered conversational interface -- the primary way users interact with the platform

**Key Features:**
- Multi-turn conversational chat powered by Claude with tool_use
- 8 quick action buttons in sidebar (Generate Presentation, Create Document, Build Training, etc.)
- 3 Knowledge Modes: Grounded (source-only), Enhanced (extended context), Research (web-capable)
- Pinned context management (persistent instructions/guidelines across turns)
- File attachment support (PDF, DOCX, PPTX, XLSX, CSV, PNG, JPG, TXT)
- Action plan confirmation workflow for large/destructive operations
- Conversation export as JSON
- Session stats tracking (messages sent, files generated)
- Audit trail display in sidebar
- Real-time progress updates via `st.status()` during generation

**Session State Keys:**
- `copilot_uploaded_paths` -- Attached file paths
- `quick_action` -- Current sidebar quick action
- `pending_confirm` -- Pending action plan awaiting approval
- `knowledge_mode_radio` -- Active knowledge mode

---

### 6.3 Page 01: Dashboard

**File:** `app/pages/01_Dashboard.py`
**Purpose:** Brand health overview, metrics, and quick navigation

**Key Features:**
- **Brand Health Score** -- 0-100 gauge based on 5 checks (config, logo, voice, templates, content)
- **Key Metrics** -- Brand assets count, templates count, generated items, library items
- **Quick Actions** -- Navigation cards to Brand Wizard, Upload Assets, Generate Content, View Library, Batch Processing, Analytics
- **Recent Generations** -- Table of most recent generated content with timestamps
- **Analytics Overview** (if analytics module available):
  - Generation trends (line chart, last 30 days)
  - Content type breakdown (pie chart)
  - Time saved estimates
  - API cost tracking (last 30 days)
  - Library health statistics
  - Rating distribution (bar chart)
  - Storage usage
- **System Status** -- Database, ChromaDB, API keys, Presenton, storage checks

---

### 6.4 Page 02: Brand Repository

**File:** `app/pages/02_Brand_Repository.py` (70.6 KB)
**Purpose:** Complete brand identity management

**6 Tabs:**

| Tab | Features |
|-----|----------|
| **Brand Wizard** | Auto-extract brand identity from company URL or uploaded samples using Claude; web scraping for brand signals; logo color extraction; voice analysis |
| **Assets** | Upload and organize brand materials with smart classification (SmartClassifier); drag-and-drop file upload; asset tagging and categorization |
| **Colors & Fonts** | Manage color palette with color picker; WCAG accessibility analysis; font family selection with preview; full palette editor (11 colors) |
| **Voice Profile** | Define brand voice (tone, formality, vocabulary level); auto-analysis from uploaded documents via Claude; key phrases, avoid phrases, messaging themes |
| **Terminology** | Build brand glossary with preferred terms; acronym database; auto-extraction from uploaded content; program names |
| **Templates** | Manage PPTX, DOCX, training templates; upload new templates; template metadata editing |

**Multi-Profile Support:** Create, switch, and delete brand profiles for different brand variations

---

### 6.5 Page 03: Content Generator

**File:** `app/pages/03_Content_Generator.py`
**Purpose:** Quick-access forms for all content types

**4 Tabs:**

| Tab | Inputs | Outputs |
|-----|--------|---------|
| **Presentations** | Title, type (general/training/pitch/QBR/rollout), slide count (5-25), content, file upload, instructions | PPTX file |
| **Documents** | Title, type (10 options), format (DOCX/PDF/both), content, file upload, structured data, instructions | DOCX/PDF file |
| **Training Packages** | Program title, type (product/compliance/onboarding/sales/process), audience level, deliverable selection, curriculum, file upload | ZIP package with multiple deliverables |
| **Visuals** | Visual type, output format, description | PNG/SVG/PPTX file |

---

### 6.6 Page 04: Presentation Studio

**File:** `app/pages/04_Presentation_Studio.py` (58.5 KB)
**Purpose:** Interactive workspace for presentation creation

**4 Tabs:**

| Tab | Features |
|-----|----------|
| **Generate** | AI-powered slide generation with brand config; customizable title/type/count; content input or file upload; Presenton integration |
| **Preview** | Slide-by-slide preview with individual slide regeneration; slide editing; metrics display (slides, generation time) |
| **Import Templates** | Analyze and import external PPTX templates; extract design elements (DNA); color palette extraction |
| **History** | View generation history; template library access; draft management |

**Slide Layout Types:** Title, Section, Content, Two-Column, Image+Text, Chart, Quote, Closing (8 total)
**Format:** 16:9 widescreen
**Branding:** Auto-applies colors, fonts, and logo from brand_config.json

---

### 6.7 Page 05: Training Builder

**File:** `app/pages/05_Training_Builder.py` (83.1 KB)
**Purpose:** Transform curriculum into complete training packages

**Training Pipeline Outputs (7 deliverables):**
1. Training presentation deck (PPTX)
2. Facilitator guide (DOCX)
3. Participant handout (DOCX)
4. Job aids -- one per module (DOCX)
5. Quiz/assessment with answer key (DOCX)
6. Microlearning modules (DOCX)
7. Agent scripts (DOCX)

**Configuration Options:**
- Training type: General, Onboarding, Product, Compliance, Sales, Technical
- Audience level: Beginner, Intermediate, Advanced, Expert
- Deliverable selection: Multi-select from 7 types
- Curriculum input: Text area or file upload (TXT, MD, PDF, DOCX, PPTX)

**Output:** Individual files + complete ZIP package

---

### 6.8 Page 06: Document Factory

**File:** `app/pages/06_Document_Factory.py` (92.5 KB)
**Purpose:** Generate professional branded documents

**10 Document Templates:**
| Template | Typical Length |
|----------|--------------|
| Job Aid | 1-2 pages |
| Case Study | 2-4 pages |
| Weekly Report | 1-2 pages |
| Monthly Report | 4-8 pages |
| SOP (Standard Operating Procedure) | 3-6 pages |
| Training Guide | 5-15 pages |
| Internal Memo | 1-2 pages |
| Battle Card | 1-2 pages |
| Capability Overview | 2-4 pages |
| Proposal | 5-12 pages |

**3 Workflow Modes:**
1. **AI-Assisted** -- Claude-powered content generation from topic/description
2. **Manual** -- Template-based document creation with manual content entry
3. **Data Import** -- Generate from structured CSV/JSON data

**Output Formats:** DOCX, PDF, or both
**Batch Mode:** CSV upload for generating multiple documents in one run

---

### 6.9 Page 07: Visual Studio

**File:** `app/pages/07_Visual_Studio.py` (77 KB)
**Purpose:** Diagram and infographic creation

**8 Visual Types:**
1. Flowchart
2. Mind Map
3. Timeline
4. Org Chart
5. Process Diagram
6. Infographic
7. Comparison Chart
8. Auto (AI-selected)

**Configuration:**
- Color modes: Brand, Light, Dark, Monochrome, Colorful
- Output formats: PNG, SVG, PPTX
- Orientation: Landscape, Portrait, Auto

**Integration:** Napkin AI API for diagram generation
**AI Enhancement:** Claude-powered description enhancement for better visual results

**5 Tabs:** Generate, Import, Gallery, History, Settings

---

### 6.10 Page 08: Content Library

**File:** `app/pages/08_Content_Library.py` (95 KB)
**Purpose:** Content catalog, approval workflows, and curation

**7 Tabs:**

| Tab | Features |
|-----|----------|
| **Ingest** | Import from files, URLs, bulk CSV, or directory scan; multi-format support |
| **Browse** | Grid view with pagination; inline preview; download, rate, and approve actions |
| **Search** | Advanced search with filters: type, format, tags, date range, rating, approval status |
| **Approvals** | Workflow for reviewing content (Pending/Approved/Rejected); feedback notes; audit trail |
| **Collections** | Organize content into curated collections; create, delete, download collections |
| **Versions** | Track version history and content variants |
| **Stats** | Usage analytics: download counts, ratings, library health metrics |

**Rating System:** 1-5 stars with aggregation
**Approval Workflow:** Draft → Review → Approved → Published

---

### 6.11 Page 09: Batch Processing

**File:** `app/pages/09_Batch_Processing.py` (78 KB)
**Purpose:** Queue-based bulk content generation

**3 Tabs:**

| Tab | Features |
|-----|----------|
| **Queue** | Add items via manual text entry or CSV/Excel upload; select content type; preview queue; start batch processing |
| **Monitor** | Real-time progress bar; per-item status (Queued/Processing/Complete/Failed); elapsed time; estimated remaining |
| **History** | Batch job history with filtering; view details; download results as ZIP; retry failed items |

**Supported Content Types:** Presentations, Documents, Training Packages, Visuals
**Safety:** Sequential processing with safety limits

---

### 6.12 Page 10: Analytics

**File:** `app/pages/10_Analytics.py` (82.5 KB)
**Purpose:** Comprehensive insights and dashboards

**6 Tab Views:**

| Tab | Metrics |
|-----|---------|
| **Overview** | Total generations, generation rate, avg quality score, cost metrics, KPIs |
| **Content Generation** | Trends (line chart), type distribution (pie), generation patterns, time-series analysis |
| **Quality & Feedback** | Rating distribution, user feedback, content approval rates, improvement trends |
| **Cost Analysis** | API cost by date/type/provider; monthly/daily averages; cost vs. quality scatter plot |
| **Library Performance** | Most popular items, download trends, collection usage, storage consumption |
| **System Health** | Storage usage, database size, API performance, error rates, integration status |

**Time Filters:** Last 7/30/90 days, custom range
**Chart Engine:** Plotly (with Streamlit native fallback)
**Export:** Download analytics data

---

### 6.13 Page 11: Settings

**File:** `app/pages/11_Settings.py` (103.1 KB)
**Purpose:** Complete system configuration and administration

**8 Tabs:**

| Tab | Features |
|-----|----------|
| **API Keys** | Configure and test all API keys (Anthropic, Napkin, DeepL, Pexels, Google, Presenton); masked display; save to `.env` |
| **Brand Config** | Company info, brand values, mission, color palette, feature toggles |
| **Prompt Templates** | Create, edit, delete, clone, and export custom prompt templates with variable support |
| **Document Templates** | Register and manage DOCX/PPTX template files; scan templates directory for unregistered files |
| **Output Settings** | Format preferences, auto-save options, quality settings |
| **Integrations** | Configure external service integrations; individual and bulk testing |
| **Backup & Restore** | Export all settings as ZIP; restore from backup; feedback data export |
| **Diagnostics** | System health check; directory status; database health; full integration test suite; database reset (with confirmation) |

---

## 7. Content Generators

### 7.1 Presentation Generator (`app/generators/presentation_gen.py`)

**Class:** `BrandedPresentationGenerator`

**Capabilities:**
- Generates branded PPTX presentations using python-pptx
- 8 slide layout types: Title, Section, Content, Two-Column, Image+Text, Chart, Quote, Closing
- Auto-applies brand colors, fonts, and logo from brand_config.json
- 16:9 widescreen format
- Supports template-based generation (uses uploaded PPTX templates as base)
- Fallback generation when Presenton service is unavailable

**Key Methods:**
| Method | Purpose |
|--------|---------|
| `__init__(brand_config)` | Initialize with brand configuration |
| `generate(slides_data, title, template_path)` | Generate PPTX from slide data |
| `_apply_brand_styling(prs)` | Apply brand colors and fonts to presentation |
| `_add_slide(prs, slide_data)` | Add individual slide by layout type |
| `_add_logo(slide)` | Place logo on slide |

---

### 7.2 Document Generator (`app/generators/document_gen.py`)

**Class:** `BrandedDocumentGenerator`
**Supporting Class:** `BrandedDocumentStyles`

**10 Document Templates:**
```python
DOCUMENT_TEMPLATES = {
    "job_aid":           {"name": "Job Aid",           "pages": "1-2"},
    "case_study":        {"name": "Case Study",        "pages": "2-4"},
    "weekly_report":     {"name": "Weekly Report",     "pages": "1-2"},
    "monthly_report":    {"name": "Monthly Report",    "pages": "4-8"},
    "sop":               {"name": "SOP",               "pages": "3-6"},
    "training_guide":    {"name": "Training Guide",    "pages": "5-15"},
    "internal_memo":     {"name": "Internal Memo",     "pages": "1-2"},
    "battle_card":       {"name": "Battle Card",       "pages": "1-2"},
    "capability_overview": {"name": "Capability Overview", "pages": "2-4"},
    "proposal":          {"name": "Proposal",          "pages": "5-12"},
}
```

**Key Methods:**
| Method | Purpose |
|--------|---------|
| `__init__(brand_config)` | Initialize with brand config |
| `generate(content, doc_type, title, output_format)` | Generate document |
| `_apply_brand_styles(doc)` | Apply brand colors, fonts, margins |
| `_build_sections(doc, content)` | Build document sections from content |
| `_add_header_footer(doc)` | Add branded header and footer |
| `_add_table(doc, data)` | Insert branded data tables |

---

### 7.3 Training Pipeline (`app/generators/training_pipeline.py`)

**Classes:** `TrainingPipeline`, `TrainingModule`, `TrainingPackage`, `PipelineOptions`

**7 Deliverable Types:**
1. Training deck (PPTX)
2. Facilitator guide (DOCX)
3. Participant handout (DOCX)
4. Job aids (DOCX, one per module)
5. Quiz/assessment with answer key (DOCX)
6. Microlearning modules (DOCX)
7. Agent scripts (DOCX)

**Pipeline Flow:**
```
Curriculum Input → Parse Structure → Generate Modules → Assemble Package → ZIP Output
```

**Key Methods:**
| Method | Purpose |
|--------|---------|
| `__init__(brand_config, anthropic_client)` | Initialize pipeline |
| `generate(curriculum, options)` | Run full pipeline |
| `_parse_curriculum(text)` | Extract modules from curriculum text |
| `_generate_deck(modules)` | Generate training presentation |
| `_generate_facilitator_guide(modules)` | Generate facilitator guide |
| `_generate_handout(modules)` | Generate participant handout |
| `_generate_job_aids(modules)` | Generate per-module job aids |
| `_generate_quiz(modules)` | Generate quiz with answer key |
| `_package_zip(files)` | Bundle all deliverables into ZIP |

---

### 7.4 Visual Generator (`app/generators/visual_gen.py`)

**Class:** `VisualPipeline`

**Capabilities:**
- Integrates with Napkin AI for diagram generation
- 8 visual types: Flowchart, Mind Map, Timeline, Org Chart, Process Diagram, Infographic, Comparison Chart, Auto
- Multiple output formats: PNG, SVG, PPTX
- Color modes: Brand, Light, Dark, Monochrome, Colorful
- Description enhancement via Claude AI before sending to Napkin

**Key Methods:**
| Method | Purpose |
|--------|---------|
| `__init__(brand_config, napkin_client)` | Initialize pipeline |
| `generate(description, visual_type, options)` | Generate visual |
| `_enhance_description(description, visual_type)` | AI-enhance description |
| `_map_brand_colors(color_mode)` | Map brand palette to visual colors |

---

### 7.5 Quiz Generator (`app/generators/quiz_gen.py`)

**Capabilities:**
- Multiple question types: Multiple Choice, True/False, Fill-in-the-Blank, Matching, Essay
- Answer keys with detailed explanations
- Difficulty levels (Easy, Medium, Hard)
- Auto-grading metadata
- Branded DOCX output

---

### 7.6 Spreadsheet Generator (`app/generators/spreadsheet_gen.py`)

**Class:** `BrandedSpreadsheetGenerator`

**Capabilities:**
- Creates branded Excel workbooks (XLSX) from structured JSON data
- Applies brand colors to headers, borders, and formatting
- Multiple sheet support
- Auto-column width adjustment
- Data validation support

---

### 7.7 PDF Generator (`app/generators/pdf_gen.py`)

**Class:** `PDFGenerator`

**Capabilities:**
- Converts DOCX files to PDF using LibreOffice headless mode
- Auto-detects LibreOffice installation path
- Batch conversion support
- Graceful fallback if LibreOffice is not installed

---

### 7.8 Google Export (`app/generators/google_export.py`)

**Capabilities:**
- Export documents to Google Drive
- Create Google Docs from generated content
- Share permissions management
- Service account and OAuth authentication support

---

## 8. AI Copilot Engine

### 8.1 Architecture

```
CopilotEngine (engine.py)
├── Claude Tool Use Loop (multi-round)
├── COPILOT_TOOLS (tools.py)              -- 20+ structured tool definitions
├── Tool Handlers (tool_handlers.py)      -- Execution logic per tool
├── Context Builder (context_builder.py)  -- Dynamic system prompt construction
├── Response Renderer (response_renderer.py) -- Streamlit UI formatting
├── Conversation Manager (conversation.py)   -- Chat history + state
├── Project Tracker (project_tracker.py)     -- Goal/project tracking
├── Audit Log (audit_log.py)                 -- Action logging + cost estimation
└── Verification (verification.py)           -- Source attribution + knowledge modes
```

### 8.2 Engine (`app/copilot/engine.py`)

**Class:** `CopilotEngine`

**Core Loop:**
1. Receive user message
2. Build context (system prompt + conversation history + pinned context)
3. Send to Claude with tool definitions
4. If Claude returns `tool_use` → execute tool → feed result back → repeat
5. If Claude returns `text` → format and display response
6. Log action to audit trail

**Key Methods:**
| Method | Purpose |
|--------|---------|
| `__init__()` | Initialize engine with all dependencies |
| `process_message(user_text, files, mode)` | Process user turn through full tool loop |
| `_build_messages(user_text)` | Construct message array for Claude API |
| `_execute_tool(tool_name, tool_input)` | Route tool call to handler |
| `_handle_confirmation(action_plan)` | Present action plan for user approval |

### 8.3 Available Tools (`app/copilot/tools.py`)

| Tool Name | Category | Description |
|-----------|----------|-------------|
| `search_brand_assets` | Brand | Search logos, templates, guidelines in brand repository |
| `get_brand_config` | Brand | Retrieve current brand settings (colors, voice, terminology) |
| `update_brand_config` | Brand | Modify brand configuration values |
| `generate_presentation` | Generate | Create branded PPTX presentation |
| `generate_document` | Generate | Create branded DOCX document (10 types) |
| `generate_training_package` | Generate | Build complete training package (7 deliverables) |
| `generate_visual` | Generate | Create diagram/infographic via Napkin AI |
| `generate_batch` | Generate | Queue and execute bulk generation |
| `search_content_library` | Library | Find existing content by search/filters |
| `approve_content` | Library | Update content approval status |
| `list_templates` | Templates | List available branded templates |
| `get_content_stats` | Analytics | Fetch generation metrics and analytics |
| `search_brand_knowledge` | Knowledge | Semantic search across ChromaDB collections |
| `translate_content` | Translate | Multi-language translation via DeepL |
| `web_search` | Research | Web-capable research (Research mode only) |
| `confirm_action` | Workflow | Present action plan for user confirmation |

### 8.4 Knowledge Modes

| Mode | Behavior |
|------|----------|
| **Grounded** | Only use brand assets and existing documents as sources; highest accuracy |
| **Enhanced** | Extended context from content library; broader but still internal |
| **Research** | Web-capable with external sources; broadest context but less controlled |

### 8.5 Confirmation Workflow

Large or destructive operations require user approval:
1. Claude proposes an action plan (title, description, estimated cost, affected items)
2. User reviews the plan in a `st.form()`
3. User clicks "Confirm" or "Cancel"
4. If confirmed, the engine executes the planned actions
5. All confirmations logged to `CopilotAuditLog`

### 8.6 Audit Logging (`app/copilot/audit_log.py`)

Every Copilot action is logged with:
- Session ID
- Action type (tool_call, confirmation, generation)
- Tool name and input summary
- Output summary
- Confirmation status
- Cost estimate
- Token usage
- Duration (ms)

---

## 9. Brand Management Modules

### 9.1 Asset Manager (`app/brand/asset_manager.py`)

**Capabilities:**
- File upload with duplicate detection (timestamped naming)
- Asset categorization by type (logo, font, template, collateral, sample)
- Filesystem organization under `brand_assets/`
- Database registration of all uploaded assets
- Tag management

### 9.2 Brand Wizard (`app/brand/brand_wizard.py`)

**Capabilities:**
- Auto-extract brand identity from:
  - Company website URL (web scraping)
  - Uploaded logo (color extraction)
  - Sample documents (voice analysis)
- Generates complete `brand_config.json` from extracted signals
- Uses Claude AI for brand signal interpretation

### 9.3 Color Extractor (`app/brand/color_extractor.py`)

**Capabilities:**
- Extract dominant colors from logo images using colorthief
- Generate 6-color palette (primary, secondary, accents)
- WCAG accessibility analysis (contrast ratios)
- Color categorization (dark/light classification)
- Hex, RGB output formats

### 9.4 Voice Analyzer (`app/brand/voice_analyzer.py`)

**Capabilities:**
- Claude-powered analysis of brand voice from text samples
- Extracts: tone, formality level, vocabulary level
- Identifies key phrases and phrases to avoid
- Detects messaging themes
- Generates structured voice profile JSON

---

## 10. File Ingestion & Parsing

### 10.1 PDF Parser (`app/ingestion/pdf_parser.py`)
- Uses pdfplumber for text extraction
- Page-by-page extraction with metadata
- Handles multi-column layouts

### 10.2 DOCX Parser (`app/ingestion/docx_parser.py`)
- Uses python-docx for text extraction
- Preserves heading structure
- Extracts tables and lists

### 10.3 PPTX Parser (`app/ingestion/pptx_parser.py`)
- Uses python-pptx for text extraction
- Slide-by-slide extraction
- Captures slide titles and body text
- Extracts speaker notes

### 10.4 URL Scraper (`app/ingestion/url_scraper.py`)
- Uses requests + BeautifulSoup for web page scraping
- HTML to text conversion
- Metadata extraction (title, description, keywords)
- Handles redirects and errors

### 10.5 Curriculum Parser (`app/ingestion/curriculum_parser.py`)
- Claude-powered curriculum structure extraction
- Identifies modules, topics, learning objectives
- Outputs structured JSON for training pipeline

### 10.6 Chunker (`app/ingestion/chunker.py`)
- Semantic text chunking for ChromaDB ingestion
- Token-based splitting (tiktoken)
- Max chunk size: 750 tokens
- Overlap: 100 tokens
- Preserves paragraph boundaries

### 10.7 Smart Classifier (`app/ingestion/smart_classifier.py`)
- Claude-powered auto-classification of uploaded files
- Extension-based fast categorization
- AI-generated descriptions and tags
- Maps to asset types (logo, font, template, collateral, etc.)

---

## 11. External Integrations

### 11.1 Napkin AI Client (`app/integrations/napkin_client.py`)

**Class:** `NapkinClient`

**API Integration:**
- REST API calls to Napkin AI service
- Visual type mapping to Napkin API parameters
- Color mode translation
- Output format handling (PNG, SVG, PPTX)
- Error handling with retries

**Constants:**
```python
VISUAL_TYPES = ["flowchart", "mind_map", "timeline", "org_chart",
                "process_diagram", "infographic", "comparison_chart"]
COLOR_MODES = ["brand", "light", "dark", "monochrome", "colorful"]
OUTPUT_FORMATS = ["png", "svg", "pptx"]
ORIENTATIONS = ["landscape", "portrait", "auto"]
```

### 11.2 Presenton Client (`app/integrations/presenton_client.py`)

**Class:** `PresentonClient`

**API Integration:**
- REST API calls to Presenton Docker container (port 5001)
- Presentation generation from structured content
- Health check endpoint
- Template management
- Download generated files

### 11.3 Translation Client (`app/integrations/translation_client.py`)

**API Integration:**
- DeepL API for text translation
- Multi-language support
- Batch translation capability
- Language detection

---

## 12. Core Utilities

### 12.1 Analytics Engine (`app/utils/analytics.py`)

**Class:** `AnalyticsEngine`

**Capabilities:**
- Generation volume tracking (by type, time period, creator)
- Quality metrics (average ratings, approval rates, revision counts)
- Cost tracking (API usage, token counts, estimated costs per generation)
- Storage usage monitoring (database size, output directory breakdown)
- Time-series data for trend charts
- Feedback aggregation

### 12.2 Feedback Loop (`app/core/feedback_loop.py`)

**Class:** `FeedbackLoop`

**Capabilities:**
- User satisfaction tracking
- Quality score aggregation
- Improvement recommendation engine
- Trend analysis over time
- Content type quality comparison

---

## 13. Brand Configuration (Active)

The current active brand configuration (`brand_config.json`):

```json
{
  "company_name": "TP",
  "terminology": {
    "preferred_terms": {},
    "program_names": [
      "TP tools",
      "Processes Re-engineering",
      "TP Microservices Platform",
      "TP Applications"
    ],
    "acronyms": {
      "TP": "Teleperformance",
      "AI": "Artificial Intelligence"
    }
  },
  "voice_profile": {
    "tone": "professional",
    "formality": "Semi-Formal",
    "vocabulary_level": "Moderate",
    "key_phrases": [
      "WE'RE PASSIONATE ABOUT OUR BRAND",
      "#WeAreTP",
      "global brand consistency",
      "We're here to help",
      "Leading global delivery platform",
      "powered by TP experts"
    ],
    "avoid_phrases": [],
    "messaging_themes": [
      "brand consistency",
      "global support",
      "expertise and technology",
      "operational excellence",
      "customer service"
    ]
  },
  "colors": {
    "primary": "#ED1E81",
    "secondary": "#4C3193",
    "accent": "#918D80",
    "background": "#FFFFFF",
    "text": "#000000"
  },
  "fonts": {
    "heading": "Calibri",
    "body": "Calibri"
  },
  "full_palette": {
    "dk1": "#000000",
    "lt1": "#FFFFFF",
    "dk2": "#D4D1CA",
    "lt2": "#4A4C6A",
    "accent1": "#ED1E81",
    "accent2": "#918D80",
    "accent3": "#4C3193",
    "accent4": "#706297",
    "accent5": "#848DAC",
    "accent6": "#C2C7CC",
    "hlink": "#0087FF",
    "folHlink": "#771E95"
  }
}
```

### Brand Assets on Disk

**Logos:**
- `GMT_Logo TP_CMYK_Feb 2025.pdf` -- CMYK print logo
- `GMT_Logo TP_RGB_Feb 2025_white.png` -- RGB digital logo (white variant)

**Templates:**
- `GMT_Case study_template _March_2025.pptx` -- Case study PPTX template (~18 MB)
- `GMT_PPT_Template_Global TP_October_2025.pptx` -- Global TP PPTX template (~22 MB)
- `GMT_Word Template A4_Feb_2025.docx` -- A4 Word template (~594 KB)

---

## 14. Generated Content Inventory

### Presentations (5 files)
| File | Size |
|------|------|
| FACTS Sales Culture Training Row the Boat Together | 22.6 MB |
| FACTS Sales Culture Building Excellence (3 versions) | 107-146 KB each |
| Phase3 Test | 41 KB |

### Documents (14 files)
| File | Size |
|------|------|
| FACTS Sales Culture (3 versions) | 77 KB each |
| Acme Case Study | 39 KB |
| Brand Hub Implementation Proposal | 40 KB |
| Brand Hub Onboarding | 40 KB |
| Brand Hub Platform | 39 KB |
| Brand Hub vs Competitors | 39 KB |
| Content Approval Process | 39 KB |
| February 2026 Monthly Report | 39 KB |
| Q1 Launch Memo | 39 KB |
| Quick Start Guide | 39 KB |
| Week 8 Report | 39 KB |

### Training Packages (15 files + 1 ZIP)
| File | Type | Size |
|------|------|------|
| FACTS Sales Methodology Training Deck | PPTX | 148 KB |
| FACTS Facilitator Guide | DOCX | 79 KB |
| FACTS Job Aid 01-04 | DOCX | 77 KB each |
| FACTS Quiz + Answer Key | DOCX | 78 KB each |
| FACTS Training Package | ZIP | 644 KB |
| Customer Service Excellence (5 files) | Various | 38-68 KB |

### Reports (2 files)
| File | Size |
|------|------|
| KPI Report | 5.4 KB (XLSX) |
| Q1 Dashboard | 6.1 KB (XLSX) |

### Visuals (4 files)
| File | Size |
|------|------|
| Comparison Chart | 10.7 KB (PNG) |
| Flowchart | 12.8 KB (PNG) |
| Org Chart | 9.3 KB (PNG) |
| Timeline | 11.5 KB (PNG) |

---

## 15. Setup & Deployment

### 15.1 Automated Setup (`setup.sh`)

```bash
#!/usr/bin/env bash
# Steps:
# [1/6] Create Python virtual environment (python3 -m venv venv)
# [2/6] Activate virtual environment
# [3/6] Install Python dependencies (pip install -r requirements.txt)
# [4/6] Create all project directories (14 directories)
# [5/6] Copy .env.example to .env (if not exists)
# [6/6] Initialize SQLite database (python -c "from app.database.models import init_db; init_db()")
# [Optional] Start Presenton via Docker Compose
```

### 15.2 Quick Start

```bash
# 1. Clone and setup
chmod +x setup.sh && ./setup.sh

# 2. Configure API keys
# Edit .env with actual keys:
#   ANTHROPIC_API_KEY=sk-ant-...
#   NAPKIN_API_TOKEN=...

# 3. Activate environment and launch
source venv/bin/activate
streamlit run app/main.py
# App opens at http://localhost:8501
```

### 15.3 Docker (Presenton Service)

```yaml
# docker-compose.yml
version: "3.9"
services:
  presenton:
    image: ghcr.io/presenton/presenton:latest
    container_name: brand-hub-presenton
    ports:
      - "5001:5001"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./data/presenton:/app/data
    restart: unless-stopped
```

### 15.4 Dependencies (`requirements.txt`)

```
streamlit>=1.30.0
anthropic>=0.40.0
sqlalchemy>=2.0.0
chromadb>=0.4.0
python-dotenv>=1.0.0
pdfplumber>=0.10.0
python-docx>=1.0.0
python-pptx>=0.6.21
beautifulsoup4>=4.12.0
requests>=2.31.0
colorthief>=0.2.1
Pillow>=10.0.0
tiktoken>=0.5.0
watchdog>=3.0.0
pandas>=2.0.0
plotly>=5.18.0
```

---

## 16. Data Flow & Architecture Diagrams

### 16.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI (localhost:8501)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Copilot  │ │Dashboard │ │  Brand   │ │ Content  │ ... (12)  │
│  │  (Chat)  │ │          │ │  Repo    │ │Generator │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       │             │            │             │                 │
├───────┼─────────────┼────────────┼─────────────┼─────────────────┤
│       ▼             ▼            ▼             ▼                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                     APPLICATION LAYER                       │ │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────────┐ │ │
│  │  │  Copilot  │ │   Brand   │ │Generators │ │ Ingestion  │ │ │
│  │  │  Engine   │ │  Manager  │ │  (9 types)│ │  (7 types) │ │ │
│  │  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └──────┬─────┘ │ │
│  └────────┼──────────────┼─────────────┼──────────────┼────────┘ │
│           │              │             │              │          │
├───────────┼──────────────┼─────────────┼──────────────┼──────────┤
│           ▼              ▼             ▼              ▼          │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                      DATA LAYER                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │ │
│  │  │   SQLite DB   │  │   ChromaDB   │  │   File System    │  │ │
│  │  │  (9 tables)   │  │ (4 vectors)  │  │ (brand_assets/   │  │ │
│  │  │               │  │              │  │  output/ data/)   │  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                     EXTERNAL SERVICES                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐ ┌──────────┐ │
│  │ Claude   │ │ Napkin   │ │Presenton │ │ DeepL │ │  Pexels  │ │
│  │  API     │ │   AI     │ │ (Docker) │ │       │ │          │ │
│  └──────────┘ └──────────┘ └──────────┘ └───────┘ └──────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 16.2 Content Generation Flow

```
User Input (text/file/URL)
    │
    ▼
┌────────────────┐
│  Parse & Ingest │ ← PDF, DOCX, PPTX, URL parsers
│  (chunker.py)   │ ← Smart classification
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Build Prompt   │ ← Brand config (colors, voice, terminology)
│  + Brand Context│ ← ChromaDB semantic search (reference content)
│                 │ ← Template selection
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Claude API     │ ← claude-sonnet-4-20250514
│  (Generate)     │ ← System prompt + user content + tool definitions
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Format Output  │ ← python-pptx (PPTX)
│  + Apply Brand  │ ← python-docx (DOCX)
│                 │ ← Napkin AI (diagrams)
│                 │ ← openpyxl (XLSX)
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  Save & Record  │ → File system (output/)
│                 │ → SQLite (GeneratedContent)
│                 │ → Content Library (optional)
│                 │ → Audit Log (CopilotAuditLog)
└────────────────┘
```

### 16.3 Copilot Tool Loop

```
User Message
    │
    ▼
┌───────────────────┐
│ Context Builder    │ ← System prompt
│                    │ ← Brand context
│                    │ ← Conversation history
│                    │ ← Pinned context
│                    │ ← Knowledge mode
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Claude API Call    │ ← Messages + Tools (20+)
│ (tool_use enabled) │
└────────┬──────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
 [text]    [tool_use]
    │         │
    │         ▼
    │    ┌──────────────┐
    │    │ Tool Handler  │ ← Execute tool
    │    │               │ ← Generate content
    │    │               │ ← Search library
    │    │               │ ← Update config
    │    └──────┬───────┘
    │           │
    │           ▼
    │    ┌──────────────┐
    │    │ Feed Result   │ ← Tool result → Claude
    │    │ Back to Claude│ ← Loop continues
    │    └──────┬───────┘
    │           │
    │     (repeat until text response)
    │           │
    └─────┬─────┘
          │
          ▼
┌───────────────────┐
│ Response Renderer  │ ← Format for Streamlit
│                    │ ← Render markdown
│                    │ ← Show file downloads
│                    │ ← Display charts/images
└───────────────────┘
```

---

## End of Build Document

**Last Updated:** February 26, 2026
**Generated Lines of Code:** 47,052
**Active Services:** Streamlit (8501)
**AI Model:** claude-sonnet-4-20250514
**Brand:** Teleperformance (TP)
