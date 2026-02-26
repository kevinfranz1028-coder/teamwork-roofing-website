"""
Brand Hub Copilot — Claude Tool Definitions
=============================================

This module defines every tool available to the Brand Hub Copilot.  The
``COPILOT_TOOLS`` list is passed directly to the Anthropic
``messages.create(tools=COPILOT_TOOLS)`` call so that Claude can invoke
any Brand Intelligence Content Hub capability through structured
tool_use requests.

Tool categories:
    - Brand Repository   : search assets, read/write brand configuration
    - Content Generation : presentations, documents, training packages,
                           visuals, and batch operations
    - Content Library    : search, stats, and approval workflows
    - Templates          : list available branded templates
    - Translation        : translate generated content
    - Strategic Advisor  : semantic search across the brand knowledge base

Exports:
    COPILOT_TOOLS   — list[dict]  (tool definitions for the API call)
    TOOL_NAMES      — set[str]    (quick look-up of valid tool names)
    get_tool_by_name(name) -> dict | None
"""

from __future__ import annotations

from typing import Optional

# ---------------------------------------------------------------------------
# Brand Repository Tools
# ---------------------------------------------------------------------------

_search_brand_assets = {
    "name": "search_brand_assets",
    "description": (
        "Search the brand asset repository for logos, templates, uploaded "
        "documents, presentations, brand guidelines, and marketing collateral. "
        "Use this tool whenever the user asks to find, locate, or list brand "
        "materials.  Results are returned ranked by relevance.  You can narrow "
        "results by asset type and date range."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Free-text search query describing the asset the user is "
                    "looking for (e.g. 'onboarding deck Q4', 'logo dark mode')."
                ),
            },
            "asset_type": {
                "type": "string",
                "enum": ["logo", "font", "template", "collateral", "guideline", "all"],
                "description": (
                    "Filter results to a specific asset category.  Use 'all' "
                    "or omit when the user has not specified a type."
                ),
            },
            "date_filter": {
                "type": "string",
                "description": (
                    "Optional date-range filter in natural language or ISO "
                    "format (e.g. 'last 30 days', '2025-01-01..2025-06-30')."
                ),
            },
        },
        "required": ["query"],
    },
}

_get_brand_config = {
    "name": "get_brand_config",
    "description": (
        "Retrieve the current brand configuration.  Returns structured data "
        "about the brand's approved colors, fonts, voice guidelines, "
        "terminology dictionary, or template settings.  Use this tool when "
        "the user asks about brand standards, wants to verify correct hex "
        "codes, check the approved font stack, review voice/tone rules, or "
        "inspect template defaults."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "section": {
                "type": "string",
                "enum": ["all", "colors", "fonts", "voice", "terminology", "templates"],
                "description": (
                    "Which section of the brand config to return.  Use 'all' "
                    "to return the full configuration."
                ),
            },
        },
        "required": ["section"],
    },
}

_update_brand_config = {
    "name": "update_brand_config",
    "description": (
        "Update a section of the brand configuration.  Use this tool when "
        "the user wants to change brand colors, swap fonts, adjust the voice "
        "and tone guidelines, or add/remove terminology entries.  The updates "
        "object should contain only the fields to change; existing fields not "
        "included are left untouched.  This operation is audited — every "
        "change is recorded in the brand config history."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "section": {
                "type": "string",
                "enum": ["colors", "fonts", "voice", "terminology"],
                "description": "The brand config section to update.",
            },
            "updates": {
                "type": "object",
                "description": (
                    "A JSON object whose keys and values depend on the section "
                    "being updated.  For 'colors': keys are role names "
                    "('primary', 'secondary', 'accent') mapped to hex values.  "
                    "For 'fonts': keys are usage contexts ('heading', 'body') "
                    "mapped to font-family strings.  For 'voice': keys are "
                    "attributes ('tone', 'formality', 'perspective') mapped to "
                    "descriptive strings.  For 'terminology': keys are terms "
                    "mapped to their approved replacements or definitions."
                ),
            },
        },
        "required": ["section", "updates"],
    },
}

# ---------------------------------------------------------------------------
# Content Generation Tools
# ---------------------------------------------------------------------------

_generate_presentation = {
    "name": "generate_presentation",
    "description": (
        "Generate a fully branded PowerPoint (PPTX) presentation.  Use this "
        "tool when the user asks to create a slide deck, presentation, or "
        "pitch.  The system applies the current brand template, colors, and "
        "fonts automatically.  You may supply raw content, point to a source "
        "file to extract content from, or let the system generate content "
        "from the title and instructions alone."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title of the presentation (appears on the title slide).",
            },
            "content_source": {
                "type": "string",
                "description": (
                    "Raw text, markdown, or bullet points to use as the "
                    "source material for the slides."
                ),
            },
            "source_file_path": {
                "type": "string",
                "description": (
                    "Path to an uploaded file (DOCX, PDF, TXT, MD) whose "
                    "content should be converted into slides."
                ),
            },
            "presentation_type": {
                "type": "string",
                "enum": [
                    "general",
                    "training_deck",
                    "client_pitch",
                    "qbr",
                    "program_rollout",
                ],
                "description": (
                    "The category of presentation.  This determines the "
                    "default structure, section ordering, and slide layout "
                    "strategy used by the generator."
                ),
            },
            "num_slides": {
                "type": "integer",
                "description": (
                    "Desired number of slides (excluding title and closing).  "
                    "If omitted the system decides based on content length."
                ),
            },
            "template_id": {
                "type": "string",
                "description": (
                    "ID of a specific brand template to use.  If omitted the "
                    "default template for the presentation_type is applied."
                ),
            },
            "additional_instructions": {
                "type": "string",
                "description": (
                    "Extra instructions for style, emphasis, or structure "
                    "(e.g. 'keep it under 10 slides', 'emphasize ROI')."
                ),
            },
            "language": {
                "type": "string",
                "description": (
                    "ISO 639-1 language code for the output language "
                    "(e.g. 'en', 'es', 'fr').  Defaults to 'en'."
                ),
            },
        },
        "required": ["title", "presentation_type"],
    },
}

_generate_document = {
    "name": "generate_document",
    "description": (
        "Generate a branded Word document (DOCX) or PDF.  Use this tool when "
        "the user asks to create a job aid, case study, report, SOP, training "
        "guide, memo, battle card, capability overview, or proposal.  Brand "
        "styling (fonts, colors, headers, footers) is applied automatically."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Document title displayed on the cover page.",
            },
            "content_source": {
                "type": "string",
                "description": (
                    "Raw text, markdown, or structured content to populate "
                    "the document."
                ),
            },
            "source_file_path": {
                "type": "string",
                "description": (
                    "Path to an uploaded file whose content should be "
                    "reformatted into the branded document."
                ),
            },
            "document_type": {
                "type": "string",
                "enum": [
                    "job_aid",
                    "case_study",
                    "weekly_report",
                    "monthly_report",
                    "sop",
                    "training_guide",
                    "internal_memo",
                    "battle_card",
                    "capability_overview",
                    "proposal",
                ],
                "description": (
                    "The kind of document to produce.  Each type uses a "
                    "purpose-built section structure and layout."
                ),
            },
            "output_format": {
                "type": "string",
                "enum": ["docx", "pdf", "both"],
                "description": (
                    "Desired output file format.  'both' produces a DOCX and "
                    "a PDF.  Defaults to 'docx'."
                ),
            },
            "additional_instructions": {
                "type": "string",
                "description": (
                    "Extra guidance on tone, length, sections to include or "
                    "exclude, or specific data to highlight."
                ),
            },
            "data_input": {
                "type": "string",
                "description": (
                    "Structured data (JSON, CSV rows, or key-value pairs) to "
                    "merge into the document — useful for reports and case "
                    "studies with metrics."
                ),
            },
            "language": {
                "type": "string",
                "description": (
                    "ISO 639-1 language code for the output language.  "
                    "Defaults to 'en'."
                ),
            },
        },
        "required": ["title", "document_type"],
    },
}

_generate_training_package = {
    "name": "generate_training_package",
    "description": (
        "Generate a complete training package consisting of multiple "
        "deliverables (deck, facilitator guide, participant handout, job "
        "aids, quiz, microlearning modules, agent scripts).  Use this tool "
        "when the user wants an end-to-end training program rather than a "
        "single document.  All outputs share consistent content and branding."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Name of the training program or module.",
            },
            "content_source": {
                "type": "string",
                "description": (
                    "Raw content, knowledge-base text, or curriculum outline "
                    "to use as source material."
                ),
            },
            "source_file_path": {
                "type": "string",
                "description": (
                    "Path to an uploaded file containing the source material "
                    "for the training package."
                ),
            },
            "training_type": {
                "type": "string",
                "enum": [
                    "product_training",
                    "compliance",
                    "onboarding",
                    "sales_training",
                    "process_training",
                    "general",
                ],
                "description": (
                    "Category of training.  This influences the pedagogical "
                    "approach, section templates, and assessment style."
                ),
            },
            "target_audience": {
                "type": "string",
                "enum": [
                    "new_hires",
                    "experienced_agents",
                    "managers",
                    "clients",
                    "general",
                ],
                "description": (
                    "Who will consume the training.  Adjusts language "
                    "complexity, assumed knowledge level, and examples."
                ),
            },
            "outputs_to_generate": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "training_deck",
                        "facilitator_guide",
                        "participant_handout",
                        "job_aids",
                        "quiz",
                        "microlearning",
                        "agent_script",
                    ],
                },
                "description": (
                    "Which deliverables to produce.  If omitted, the system "
                    "generates a sensible default set for the training_type."
                ),
            },
            "language": {
                "type": "string",
                "description": (
                    "ISO 639-1 language code for the output language.  "
                    "Defaults to 'en'."
                ),
            },
        },
        "required": ["title", "training_type"],
    },
}

_generate_visual = {
    "name": "generate_visual",
    "description": (
        "Generate a visual diagram or infographic using the Napkin AI "
        "integration.  Use this tool when the user asks for a flowchart, "
        "mind map, timeline, org chart, process diagram, infographic, or "
        "comparison chart.  Provide a clear natural-language description of "
        "the visual and the system will produce a branded image or editable "
        "slide."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": (
                    "A detailed natural-language description of the visual to "
                    "create, including all data points, labels, and "
                    "relationships that should appear."
                ),
            },
            "visual_type": {
                "type": "string",
                "enum": [
                    "flowchart",
                    "mind_map",
                    "timeline",
                    "org_chart",
                    "process_diagram",
                    "infographic",
                    "comparison_chart",
                    "auto",
                ],
                "description": (
                    "The kind of visual to generate.  Use 'auto' to let the "
                    "system choose the best format from the description."
                ),
            },
            "output_format": {
                "type": "string",
                "enum": ["png", "svg", "ppt"],
                "description": (
                    "Desired output format.  'ppt' embeds the visual in an "
                    "editable PowerPoint slide.  Defaults to 'png'."
                ),
            },
        },
        "required": ["description"],
    },
}

_generate_batch = {
    "name": "generate_batch",
    "description": (
        "Generate multiple content items in a single batch operation.  Use "
        "this tool when the user requests several documents, presentations, "
        "or mixed content types at once.  Each item in the batch specifies "
        "its own content_type, title, and generation parameters.  The system "
        "processes all items concurrently and returns download links for each."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "batch_name": {
                "type": "string",
                "description": (
                    "A human-readable name for this batch job "
                    "(e.g. 'Q1 Training Materials')."
                ),
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "content_type": {
                            "type": "string",
                            "description": (
                                "The type of content to generate for this "
                                "item (e.g. 'presentation', 'document', "
                                "'visual', 'training_package')."
                            ),
                        },
                        "title": {
                            "type": "string",
                            "description": "Title for this individual item.",
                        },
                        "params": {
                            "type": "object",
                            "description": (
                                "Additional parameters specific to the "
                                "content_type (mirrors the params of the "
                                "corresponding individual generation tool)."
                            ),
                        },
                    },
                    "required": ["content_type", "title", "params"],
                },
                "description": "List of content items to generate.",
            },
        },
        "required": ["batch_name", "items"],
    },
}

# ---------------------------------------------------------------------------
# Content Library Tools
# ---------------------------------------------------------------------------

_search_content_library = {
    "name": "search_content_library",
    "description": (
        "Search the library of previously generated content (presentations, "
        "documents, training packages, visuals).  Use this tool when the user "
        "wants to find something that was already created, check if similar "
        "content exists before generating new content, or retrieve a past "
        "deliverable.  Supports filtering by type, date, and approval status."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Search query describing the content to find "
                    "(e.g. 'onboarding deck for new hires')."
                ),
            },
            "content_type": {
                "type": "string",
                "description": (
                    "Filter by content type (e.g. 'presentation', 'document', "
                    "'training_package', 'visual').  Omit to search all types."
                ),
            },
            "date_filter": {
                "type": "string",
                "description": (
                    "Date range filter in natural language or ISO format "
                    "(e.g. 'last 7 days', '2025-01-01..2025-03-31')."
                ),
            },
            "approved_only": {
                "type": "boolean",
                "description": (
                    "When true, only return content that has been approved.  "
                    "Defaults to false."
                ),
            },
            "limit": {
                "type": "integer",
                "description": (
                    "Maximum number of results to return.  Defaults to 20."
                ),
            },
        },
        "required": ["query"],
    },
}

_get_content_stats = {
    "name": "get_content_stats",
    "description": (
        "Retrieve usage and production statistics for the content library.  "
        "Use this tool when the user asks about content volume, generation "
        "trends, API costs, or wants a dashboard-style summary.  Choose the "
        "stat_type that best matches the question."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "stat_type": {
                "type": "string",
                "enum": [
                    "overview",
                    "by_type",
                    "recent",
                    "unapproved",
                    "most_used",
                    "api_costs",
                ],
                "description": (
                    "The kind of statistics to retrieve.  'overview' gives a "
                    "high-level summary.  'by_type' breaks counts down by "
                    "content type.  'recent' shows the latest generated items. "
                    "'unapproved' lists items awaiting approval.  'most_used' "
                    "ranks content by download/view count.  'api_costs' shows "
                    "Anthropic and third-party API spend."
                ),
            },
            "time_range": {
                "type": "string",
                "description": (
                    "Time range for the statistics (e.g. 'last 30 days', "
                    "'this quarter', '2025').  Defaults to 'all time'."
                ),
            },
        },
        "required": ["stat_type"],
    },
}

_approve_content = {
    "name": "approve_content",
    "description": (
        "Mark a piece of generated content as approved for distribution.  "
        "Use this tool when the user explicitly approves a document, "
        "presentation, or other deliverable.  Approval is recorded with a "
        "timestamp and the approver's identity for audit purposes."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "content_id": {
                "type": "string",
                "description": (
                    "The unique identifier of the content item to approve."
                ),
            },
            "approved_by": {
                "type": "string",
                "description": (
                    "Name or email of the person approving the content.  "
                    "If omitted, the current authenticated user is recorded."
                ),
            },
        },
        "required": ["content_id"],
    },
}

# ---------------------------------------------------------------------------
# Template Tools
# ---------------------------------------------------------------------------

_list_templates = {
    "name": "list_templates",
    "description": (
        "List all available branded templates.  Use this tool when the user "
        "wants to see which templates exist before generating content, or "
        "when they ask what layouts or formats are available.  Returns "
        "template names, descriptions, preview thumbnails, and IDs that can "
        "be passed to generation tools."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "template_type": {
                "type": "string",
                "enum": [
                    "presentation",
                    "document",
                    "report",
                    "job_aid",
                    "case_study",
                    "training",
                    "all",
                ],
                "description": (
                    "Filter templates by type.  Use 'all' to list every "
                    "available template."
                ),
            },
        },
        "required": ["template_type"],
    },
}

# ---------------------------------------------------------------------------
# Translation Tool
# ---------------------------------------------------------------------------

_translate_content = {
    "name": "translate_content",
    "description": (
        "Translate previously generated content or an uploaded file into "
        "another language while preserving brand formatting and layout.  Use "
        "this tool when the user asks to translate, localize, or produce a "
        "foreign-language version of existing content.  You may reference "
        "content by its library ID or by file path.  Optionally supply a "
        "list of brand terms that should NOT be translated (e.g. product "
        "names, taglines)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "content_id": {
                "type": "string",
                "description": (
                    "The library ID of an existing content item to translate."
                ),
            },
            "source_file_path": {
                "type": "string",
                "description": (
                    "Path to an uploaded file to translate.  Provide either "
                    "content_id or source_file_path, not both."
                ),
            },
            "target_language": {
                "type": "string",
                "description": (
                    "ISO 639-1 code of the target language (e.g. 'es' for "
                    "Spanish, 'fr' for French, 'pt' for Portuguese)."
                ),
            },
            "preserve_terms": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of brand-specific terms or phrases that must remain "
                    "untranslated in the output (e.g. product names, "
                    "trademarked slogans)."
                ),
            },
        },
        "required": ["target_language"],
    },
}

# ---------------------------------------------------------------------------
# Strategic Advisor Tool
# ---------------------------------------------------------------------------

_search_brand_knowledge = {
    "name": "search_brand_knowledge",
    "description": (
        "Perform a semantic (vector) search across the brand knowledge base.  "
        "Use this tool when the user asks a strategic or conceptual question "
        "about brand positioning, voice guidance, past content examples, or "
        "approved terminology — especially when a keyword search may miss "
        "relevant results.  The knowledge base is organized into collections; "
        "specify one for targeted results or use 'all' for a broad search."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "A natural-language question or topic to search for "
                    "(e.g. 'how do we talk about customer churn?')."
                ),
            },
            "collection": {
                "type": "string",
                "enum": [
                    "brand_content",
                    "brand_voice",
                    "generated_examples",
                    "terminology",
                    "all",
                ],
                "description": (
                    "Which knowledge-base collection to search.  "
                    "'brand_content' covers uploaded brand materials.  "
                    "'brand_voice' covers tone and style guidance.  "
                    "'generated_examples' covers previously generated "
                    "deliverables.  'terminology' covers the approved "
                    "glossary.  'all' searches every collection."
                ),
            },
            "num_results": {
                "type": "integer",
                "description": (
                    "Number of results to return.  Defaults to 5.  Higher "
                    "values provide more context but increase latency."
                ),
            },
        },
        "required": ["query"],
    },
}

# ---------------------------------------------------------------------------
# Web Search Tool (Research Mode only)
# ---------------------------------------------------------------------------

_web_search = {
    "name": "web_search",
    "description": (
        "Search the web for external information.  This tool is only available "
        "when the Copilot is in 'Research' knowledge mode.  Use this tool when "
        "the user explicitly asks for external data, industry benchmarks, "
        "competitor analysis, or information not available in the brand "
        "repository.  Results are clearly marked as [EXTERNAL] in generated "
        "content.  Do NOT use this tool in Grounded or Enhanced mode."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "The search query to execute on the web "
                    "(e.g. 'BPO industry trends 2025')."
                ),
            },
            "num_results": {
                "type": "integer",
                "description": (
                    "Number of results to return.  Defaults to 5."
                ),
            },
        },
        "required": ["query"],
    },
}

# ---------------------------------------------------------------------------
# Confirmation Tool
# ---------------------------------------------------------------------------

_confirm_action = {
    "name": "confirm_action",
    "description": (
        "Present an action plan to the user for confirmation before executing "
        "a generation or modification tool.  This tool is called automatically "
        "by the engine -- you should NOT call it directly.  When the engine "
        "detects a generation tool call, it presents the action plan to the "
        "user and waits for confirmation."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action_summary": {
                "type": "string",
                "description": "Brief summary of the planned action.",
            },
            "details": {
                "type": "object",
                "description": "Detailed parameters of the planned action.",
            },
            "estimated_cost": {
                "type": "string",
                "description": "Estimated API cost for this action.",
            },
        },
        "required": ["action_summary"],
    },
}

# ---------------------------------------------------------------------------
# Aggregated Tool List
# ---------------------------------------------------------------------------

COPILOT_TOOLS: list[dict] = [
    # Brand Repository
    _search_brand_assets,
    _get_brand_config,
    _update_brand_config,
    # Content Generation
    _generate_presentation,
    _generate_document,
    _generate_training_package,
    _generate_visual,
    _generate_batch,
    # Content Library
    _search_content_library,
    _get_content_stats,
    _approve_content,
    # Templates
    _list_templates,
    # Translation
    _translate_content,
    # Strategic Advisor
    _search_brand_knowledge,
    # Web Search (Research mode)
    _web_search,
    # Confirmation
    _confirm_action,
]

TOOL_NAMES: set[str] = {tool["name"] for tool in COPILOT_TOOLS}


def get_tool_by_name(name: str) -> Optional[dict]:
    """Return the tool definition dict for *name*, or ``None`` if not found.

    This is useful for dynamically inspecting a tool's input_schema at
    runtime — for example, to validate incoming tool_use parameters before
    dispatching to the handler.

    Args:
        name: The ``name`` field of the desired tool (e.g.
              ``'generate_presentation'``).

    Returns:
        The full tool definition dictionary, or ``None`` when no tool with
        that name exists in ``COPILOT_TOOLS``.
    """
    for tool in COPILOT_TOOLS:
        if tool["name"] == name:
            return tool
    return None
