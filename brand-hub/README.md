# Brand Intelligence Content Hub

A local Streamlit application that serves as a centralized brand repository and AI-powered content factory. Generate branded presentations, training materials, documents, reports, job aids, case studies, and more.

## Quick Start

```bash
# 1. Run setup
chmod +x setup.sh && ./setup.sh

# 2. Configure API keys
#    Edit .env with your actual keys:
#    - ANTHROPIC_API_KEY (required)
#    - NAPKIN_API_TOKEN (required)

# 3. Launch
source venv/bin/activate
streamlit run app/main.py
```

## Project Structure

```
brand-hub/
├── app/
│   ├── main.py                  # Streamlit entry point
│   ├── config.py                # Environment & path configuration
│   ├── pages/
│   │   ├── 01_Dashboard.py      # Brand health score, quick actions, status
│   │   ├── 02_Brand_Repository.py # Asset management, Brand Wizard, voice profile
│   │   ├── 03_Content_Generator.py  # Phase 2
│   │   ├── 04_Presentation_Studio.py # Phase 2
│   │   ├── 05_Training_Builder.py    # Phase 2
│   │   ├── 06_Document_Factory.py    # Phase 2
│   │   ├── 07_Content_Library.py     # Phase 2
│   │   ├── 08_Batch_Processing.py    # Phase 2
│   │   ├── 09_Analytics.py           # Phase 2
│   │   └── 10_Settings.py            # Phase 2
│   ├── database/
│   │   ├── models.py            # SQLAlchemy models (SQLite)
│   │   └── vector_store.py      # ChromaDB wrapper
│   ├── brand/
│   │   ├── asset_manager.py     # File upload & organization
│   │   ├── brand_wizard.py      # Auto-extract brand from URL + files
│   │   ├── color_extractor.py   # Extract colors from logos
│   │   └── voice_analyzer.py    # Analyze brand voice via Claude
│   └── ingestion/
│       ├── pdf_parser.py        # PDF text extraction (pdfplumber)
│       ├── docx_parser.py       # DOCX extraction (python-docx)
│       ├── pptx_parser.py       # PPTX extraction (python-pptx)
│       ├── url_scraper.py       # Web scraping (requests + BeautifulSoup)
│       ├── curriculum_parser.py # AI-powered curriculum structuring
│       └── chunker.py           # Semantic text chunking for ChromaDB
├── brand_assets/                # Brand repository storage
│   ├── logos/
│   ├── fonts/
│   ├── colors/
│   ├── templates/{pptx,docx,brand_guidelines}/
│   ├── collateral/
│   └── sample_content/
├── output/                      # Generated content
│   ├── presentations/
│   ├── documents/
│   ├── training/
│   ├── visuals/
│   ├── reports/
│   └── exports/
├── data/                        # SQLite DB + ChromaDB
├── docker-compose.yml           # Presenton service
├── requirements.txt
├── setup.sh
└── .env.example
```

## Phase 1 Features (Current)

- **Dashboard**: Brand health score, quick actions, recent generations, system status
- **Brand Repository**: Full asset management with drag-and-drop upload
- **Brand Wizard**: Auto-extract brand identity from website URL, logo, and sample documents
- **Color Extraction**: Extract and categorize brand colors from logo images
- **Voice Analysis**: AI-powered brand voice profiling using Claude
- **Content Ingestion**: Parse PDFs, DOCX, PPTX, and web pages
- **Semantic Chunking**: Smart text chunking for vector storage
- **Vector Store**: ChromaDB collections for brand content, voice, examples, and terminology

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key for AI features |
| `NAPKIN_API_TOKEN` | Yes | Napkin API for visual generation |
| `PRESENTON_URL` | No | Presenton URL (default: http://localhost:5001) |
| `DEEPL_API_KEY` | No | DeepL API for translations |
| `PEXELS_API_KEY` | No | Pexels API for stock media |

## Database

- **SQLite** via SQLAlchemy: Brand assets, templates, generated content, prompt templates, batch jobs
- **ChromaDB**: Vector store for semantic search across brand content, voice samples, generated examples, and terminology
