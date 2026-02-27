"""
Brand Intelligence Content Hub - Training Content Pipeline

End-to-end pipeline that transforms raw curriculum content into a complete
training package: presentation deck, facilitator guide, participant handouts,
job aids, quizzes, microlearning modules, and agent scripts.

Usage:
    from app.generators.training_pipeline import TrainingPipeline, PipelineOptions

    pipeline = TrainingPipeline()
    package = pipeline.process_curriculum(
        input_content="<raw curriculum text or topic description>",
        input_type="text",          # "text", "curriculum_json", "topic_description"
        options=PipelineOptions(
            training_deck=True,
            facilitator_guide=True,
            participant_handouts=True,
            job_aids=True,
            quiz=True,
            microlearning=False,
            agent_script=False,
        ),
    )
    print(package.outputs)          # {output_type: file_path, ...}
    print(package.zip_path)         # path to bundled ZIP archive
"""

import json
import logging
import os
import re
import shutil
import time
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from anthropic import Anthropic

from app.config import (
    BASE_DIR,
    BRAND_ASSETS_DIR,
    TRAINING_DIR,
    DOCUMENTS_DIR,
    PRESENTATIONS_DIR,
    LOGOS_DIR,
)

logger = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-sonnet-4-20250514"

# ---------------------------------------------------------------------------
# Training-type metadata used to tailor Claude prompts
# ---------------------------------------------------------------------------

TRAINING_TYPE_CONTEXT = {
    "general": {
        "tone": "professional and engaging",
        "focus": "broad skill development",
        "activities": "group discussions, case studies, role-plays",
    },
    "onboarding": {
        "tone": "welcoming and supportive",
        "focus": "company culture, processes, and role expectations",
        "activities": "icebreakers, buddy introductions, system walkthroughs",
    },
    "product": {
        "tone": "enthusiastic and detail-oriented",
        "focus": "product features, benefits, and competitive positioning",
        "activities": "product demos, hands-on labs, feature comparisons",
    },
    "compliance": {
        "tone": "authoritative and precise",
        "focus": "regulatory requirements, policies, and consequences of non-compliance",
        "activities": "scenario analysis, policy review exercises, compliance checklists",
    },
    "sales": {
        "tone": "energetic and persuasive",
        "focus": "sales methodology, objection handling, and closing techniques",
        "activities": "role-plays, call simulations, pipeline exercises",
    },
    "technical": {
        "tone": "clear and methodical",
        "focus": "technical concepts, procedures, and troubleshooting",
        "activities": "lab exercises, code reviews, system configuration tasks",
    },
}

AUDIENCE_LEVEL_CONTEXT = {
    "beginner": {
        "vocabulary": "simple, jargon-free language with definitions for all technical terms",
        "depth": "foundational concepts with plenty of examples and analogies",
        "pacing": "slow and deliberate with frequent comprehension checks",
    },
    "intermediate": {
        "vocabulary": "professional vocabulary assuming basic domain familiarity",
        "depth": "practical application focus connecting concepts to real-world scenarios",
        "pacing": "moderate with periodic review and knowledge-building sequences",
    },
    "advanced": {
        "vocabulary": "expert-level domain terminology used freely",
        "depth": "deep-dive analysis, edge cases, strategic implications, and nuanced scenarios",
        "pacing": "brisk with emphasis on discussion, debate, and peer learning",
    },
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TrainingModule:
    """A single training module within a curriculum."""

    title: str
    objectives: list[str] = field(default_factory=list)
    topics: list[dict] = field(default_factory=list)        # [{title, content, key_points}]
    activities: list[dict] = field(default_factory=list)     # [{title, type, instructions, duration}]
    duration_minutes: int = 30
    key_takeaways: list[str] = field(default_factory=list)


@dataclass
class ParsedCurriculum:
    """Structured representation of a full curriculum."""

    title: str
    description: str = ""
    target_audience: str = ""
    total_duration: str = ""
    modules: list[TrainingModule] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    learning_outcomes: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class PipelineOptions:
    """Configuration for which outputs the pipeline should generate."""

    # --- Output toggles ---
    training_deck: bool = True
    facilitator_guide: bool = True
    participant_handouts: bool = True
    job_aids: bool = True
    quiz: bool = True
    microlearning: bool = False
    agent_script: bool = False

    # --- Quiz options ---
    quiz_question_count: int = 10
    quiz_difficulty: str = "application"           # comprehension, application, analysis
    quiz_question_types: list[str] = field(
        default_factory=lambda: ["multiple_choice", "true_false"],
    )

    # --- Microlearning options ---
    module_duration_minutes: int = 7

    # --- Agent script options ---
    product_info: str = ""
    call_objectives: str = ""

    # --- General options ---
    language: str = "en"
    training_type: str = "general"                 # general, onboarding, product, compliance, sales, technical
    audience_level: str = "intermediate"            # beginner, intermediate, advanced


@dataclass
class TrainingPackage:
    """Complete output package from the training pipeline."""

    curriculum: Optional[ParsedCurriculum] = None
    outputs: dict = field(default_factory=dict)     # {output_type: file_path}
    errors: list[str] = field(default_factory=list)
    generation_time_seconds: float = 0.0
    zip_path: Optional[str] = None


# ---------------------------------------------------------------------------
# Main pipeline class
# ---------------------------------------------------------------------------

class TrainingPipeline:
    """Orchestrates the full curriculum-to-deliverables training workflow.

    Given raw curriculum text, structured JSON, or even just a topic
    description, this pipeline:

    1. Parses / generates a structured ``ParsedCurriculum``.
    2. Produces every requested deliverable (deck, guide, handouts, ...).
    3. Bundles everything into a downloadable ZIP archive.
    """

    def __init__(self, brand_config: Optional[dict] = None) -> None:
        """Initialise the pipeline.

        Args:
            brand_config: Optional brand configuration dict.  When *None*
                the config is loaded from ``brand_assets/brand_config.json``.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable must be set "
                "to use TrainingPipeline"
            )
        self.client = Anthropic(api_key=api_key)

        self.brand_config: dict = brand_config or self._load_brand_config()

        # Sub-generators are initialised lazily on first use
        self._presentation_gen = None
        self._document_gen = None

        # Research agent for content-library-informed generation
        self._research_agent = None
        self._research_context: str = ""  # Cached brief context for this run
        try:
            from app.agents.research_agent import ResearchAgent
            self._research_agent = ResearchAgent(brand_config=self.brand_config)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Brand config
    # ------------------------------------------------------------------

    def _load_brand_config(self) -> dict:
        """Load the brand configuration from ``brand_assets/brand_config.json``.

        Returns:
            Parsed JSON dict or a sensible default when the file is absent.
        """
        config_path = BRAND_ASSETS_DIR / "brand_config.json"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                logger.info("Loaded brand config from %s", config_path)
                return data
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not load brand config: %s", exc)

        # Sensible defaults when no config file is present
        return {
            "company_name": "Our Company",
            "colors": {
                "primary": "#0066CC",
                "secondary": "#004C99",
                "accent": "#FF6600",
                "background": "#FFFFFF",
                "text": "#333333",
            },
            "fonts": {
                "heading": "Calibri",
                "body": "Calibri",
            },
            "voice": "professional, clear, and approachable",
            "terminology": {},
        }

    # ------------------------------------------------------------------
    # Lazy sub-generator accessors
    # ------------------------------------------------------------------

    def _get_presentation_gen(self):
        """Return a lazily-initialised ``BrandedPresentationGenerator``."""
        if self._presentation_gen is None:
            from app.generators.presentation_gen import BrandedPresentationGenerator
            self._presentation_gen = BrandedPresentationGenerator()
        return self._presentation_gen

    def _get_document_gen(self):
        """Return a lazily-initialised ``BrandedDocumentGenerator``."""
        if self._document_gen is None:
            from app.generators.document_gen import BrandedDocumentGenerator
            self._document_gen = BrandedDocumentGenerator()
        return self._document_gen

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def process_curriculum(
        self,
        input_content: str,
        input_type: str = "text",
        options: Optional[PipelineOptions] = None,
    ) -> TrainingPackage:
        """Transform raw curriculum input into a complete training package.

        This is the primary public method.  It orchestrates:

        1. Input parsing / curriculum generation.
        2. Iterating through every enabled output type and generating files.
        3. Bundling all artefacts into a ZIP archive.

        Args:
            input_content: Raw text, JSON string, or topic description.
            input_type: One of ``"text"``, ``"curriculum_json"``, or
                ``"topic_description"``.
            options: Pipeline configuration.  Defaults are used when *None*.

        Returns:
            A :class:`TrainingPackage` with paths to all generated files.
        """
        start_time = time.time()
        options = options or PipelineOptions()
        package = TrainingPackage()

        # Ensure the output directory exists
        TRAINING_DIR.mkdir(parents=True, exist_ok=True)

        # --- Step 0: Build research brief from content library ------------
        if self._research_agent is not None:
            try:
                # Use the first 200 chars of input as the query
                query = input_content[:200].strip()
                brief = self._research_agent.build_brief(
                    query=query, content_type="training",
                )
                self._research_context = brief.to_prompt_context()
                logger.info("Training research brief: %s", brief.summary())
            except Exception as exc:
                logger.debug("Research agent failed for training: %s", exc)
                self._research_context = ""

        # --- Step 1: Parse / generate curriculum --------------------------
        try:
            curriculum = self.parse_input(input_content, input_type, options)
            package.curriculum = curriculum
            logger.info(
                "Parsed curriculum '%s' with %d module(s)",
                curriculum.title,
                len(curriculum.modules),
            )
        except Exception as exc:
            logger.error("Failed to parse curriculum input: %s", exc)
            package.errors.append(f"Curriculum parsing failed: {exc}")
            package.generation_time_seconds = time.time() - start_time
            return package

        # --- Step 2: Generate each requested deliverable ------------------
        generation_steps: list[tuple[str, bool, callable]] = [
            ("training_deck", options.training_deck, self.generate_training_deck),
            ("facilitator_guide", options.facilitator_guide, self.generate_facilitator_guide),
            ("participant_handouts", options.participant_handouts, self.generate_participant_handouts),
            ("job_aids", options.job_aids, self.generate_job_aids),
            ("quiz", options.quiz, self.generate_quiz),
            ("microlearning", options.microlearning, self.generate_microlearning),
            ("agent_script", options.agent_script, self.generate_agent_script),
        ]

        for output_key, enabled, generator_fn in generation_steps:
            if not enabled:
                continue
            try:
                result = generator_fn(curriculum, options)
                package.outputs[output_key] = result
                logger.info("Generated %s -> %s", output_key, result)
            except Exception as exc:
                err_msg = f"{output_key} generation failed: {exc}"
                logger.error(err_msg)
                package.errors.append(err_msg)

        # --- Step 3: Bundle into ZIP --------------------------------------
        if package.outputs:
            try:
                package.zip_path = self.package_outputs(package, curriculum.title)
                logger.info("Package ZIP created at %s", package.zip_path)
            except Exception as exc:
                err_msg = f"ZIP packaging failed: {exc}"
                logger.error(err_msg)
                package.errors.append(err_msg)

        package.generation_time_seconds = round(time.time() - start_time, 2)
        return package

    # ------------------------------------------------------------------
    # Input parsing
    # ------------------------------------------------------------------

    def parse_input(
        self,
        content: str,
        input_type: str,
        options: PipelineOptions,
    ) -> ParsedCurriculum:
        """Route content to the appropriate parsing strategy.

        Args:
            content: Raw text, JSON string, or topic description.
            input_type: ``"text"`` | ``"curriculum_json"`` | ``"topic_description"``.
            options: Pipeline configuration (used to influence generation).

        Returns:
            A fully populated :class:`ParsedCurriculum`.

        Raises:
            ValueError: If *input_type* is not recognised or *content* is empty.
        """
        if not content or not content.strip():
            raise ValueError("Input content must not be empty")

        input_type = input_type.strip().lower()

        if input_type == "curriculum_json":
            return self._parse_curriculum_json(content)
        elif input_type == "text":
            return self._structure_raw_content(content, options)
        elif input_type == "topic_description":
            return self._generate_from_topic(content, options)
        else:
            raise ValueError(
                f"Unrecognised input_type '{input_type}'. "
                "Expected 'text', 'curriculum_json', or 'topic_description'."
            )

    # ------------------------------------------------------------------
    # JSON-based curriculum parsing
    # ------------------------------------------------------------------

    def _parse_curriculum_json(self, raw_json: str) -> ParsedCurriculum:
        """Parse a JSON string directly into a :class:`ParsedCurriculum`.

        The JSON is expected to follow the canonical curriculum schema with
        top-level keys: ``title``, ``description``, ``modules``, etc.

        Args:
            raw_json: A valid JSON string.

        Returns:
            A :class:`ParsedCurriculum` instance.

        Raises:
            ValueError: If the JSON is invalid or missing a ``title``.
        """
        data = self._parse_json_response(raw_json)
        if not isinstance(data, dict):
            raise ValueError("Curriculum JSON must be an object at the top level")

        title = data.get("title", "").strip()
        if not title:
            raise ValueError("Curriculum JSON must include a non-empty 'title'")

        modules: list[TrainingModule] = []
        for raw_mod in data.get("modules", []):
            topics = []
            # Accept both 'topics' and 'sections' keys for flexibility
            for raw_topic in raw_mod.get("topics", raw_mod.get("sections", [])):
                if isinstance(raw_topic, str):
                    topics.append({"title": raw_topic, "content": "", "key_points": []})
                elif isinstance(raw_topic, dict):
                    topics.append({
                        "title": raw_topic.get("title", ""),
                        "content": raw_topic.get("content", ""),
                        "key_points": raw_topic.get("key_points", []),
                    })

            activities = []
            for raw_act in raw_mod.get("activities", []):
                if isinstance(raw_act, str):
                    activities.append({
                        "title": raw_act,
                        "type": "exercise",
                        "instructions": raw_act,
                        "duration": "10 minutes",
                    })
                elif isinstance(raw_act, dict):
                    activities.append({
                        "title": raw_act.get("title", "Activity"),
                        "type": raw_act.get("type", "exercise"),
                        "instructions": raw_act.get("instructions", ""),
                        "duration": raw_act.get("duration", "10 minutes"),
                    })

            modules.append(TrainingModule(
                title=raw_mod.get("title", "Untitled Module"),
                objectives=raw_mod.get("objectives", []),
                topics=topics,
                activities=activities,
                duration_minutes=raw_mod.get("duration_minutes", 30),
                key_takeaways=raw_mod.get("key_takeaways", []),
            ))

        return ParsedCurriculum(
            title=title,
            description=data.get("description", ""),
            target_audience=data.get("target_audience", ""),
            total_duration=data.get("total_duration", ""),
            modules=modules,
            prerequisites=data.get("prerequisites", []),
            learning_outcomes=data.get("learning_outcomes", []),
            metadata=data.get("metadata", {}),
        )

    # ------------------------------------------------------------------
    # Claude-powered structuring of raw text
    # ------------------------------------------------------------------

    def _structure_raw_content(
        self,
        content: str,
        options: PipelineOptions,
    ) -> ParsedCurriculum:
        """Use Claude to extract a structured curriculum from raw text.

        Sends the raw text alongside context about training type and
        audience level so that Claude produces appropriately scoped modules.

        Args:
            content: Unstructured text (e.g. pasted from PDF, DOCX, web).
            options: Pipeline options influencing extraction depth.

        Returns:
            A :class:`ParsedCurriculum`.
        """
        system_prompt = (
            "You are an expert instructional designer who transforms raw content "
            "into structured training curricula. You always respond with valid "
            "JSON only -- no markdown fences, no commentary."
        )
        user_content = self._build_structure_prompt(content, options)
        raw_response = self._call_claude(system_prompt, user_content, max_tokens=4096)
        return self._parse_curriculum_json(raw_response)

    # ------------------------------------------------------------------
    # Claude-powered curriculum generation from topic
    # ------------------------------------------------------------------

    def _generate_from_topic(
        self,
        topic: str,
        options: PipelineOptions,
    ) -> ParsedCurriculum:
        """Use Claude to generate a full curriculum from a topic description.

        This is the most creative mode -- Claude designs the entire
        curriculum including modules, objectives, topics, activities,
        and assessments from scratch.

        Args:
            topic: A short description of the training subject.
            options: Pipeline options influencing scope and depth.

        Returns:
            A :class:`ParsedCurriculum`.
        """
        system_prompt = (
            "You are a senior instructional designer who creates comprehensive "
            "training curricula from scratch. You produce detailed, actionable "
            "training outlines. You always respond with valid JSON only -- no "
            "markdown fences, no commentary."
        )
        user_content = self._build_topic_prompt(topic, options)
        raw_response = self._call_claude(system_prompt, user_content, max_tokens=4096)
        return self._parse_curriculum_json(raw_response)

    # ------------------------------------------------------------------
    # Deliverable generators
    # ------------------------------------------------------------------

    def generate_training_deck(
        self,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> str:
        """Generate a branded PPTX training deck from the curriculum.

        Slide sequence:
            1. Title slide
            2. Agenda / overview
            3. Learning objectives
            4. Per module: section divider, content slides, activity slide
            5. Key takeaways
            6. Assessment preview (if quiz enabled)
            7. Q&A / closing

        Args:
            curriculum: The parsed curriculum.
            options: Pipeline options (used to determine whether to
                include an assessment preview slide).

        Returns:
            Absolute path to the generated PPTX file.
        """
        slides_data = self._build_slides_from_curriculum(curriculum, options)
        safe_title = re.sub(r"[^\w\s-]", "", curriculum.title).strip()[:80]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"training_deck_{safe_title}_{timestamp}.pptx"
        save_path = str(TRAINING_DIR / filename)

        gen = self._get_presentation_gen()
        result_path = gen.generate(
            slides_data=slides_data,
            title=curriculum.title,
            save_path=save_path,
        )
        return result_path

    def generate_facilitator_guide(
        self,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> str:
        """Generate a comprehensive facilitator / instructor guide (DOCX).

        Sections:
            - Cover page with course title and metadata
            - Course overview and preparation checklist
            - Detailed timing guide (table: time, topic, activity, materials)
            - Per-module: instructor notes, discussion prompts, activity
              facilitation instructions, common questions and answers
            - Appendix with answer key references

        Args:
            curriculum: The parsed curriculum.
            options: Pipeline options.

        Returns:
            Absolute path to the generated DOCX file.
        """
        company = self.brand_config.get("company_name", "Our Company")
        voice = self.brand_config.get("voice", "professional")
        tt_ctx = TRAINING_TYPE_CONTEXT.get(options.training_type, TRAINING_TYPE_CONTEXT["general"])

        # -- Build rich content dict for the document generator --
        # Cover / header info
        content: dict[str, Any] = {
            "title": f"Facilitator Guide: {curriculum.title}",
            "subtitle": f"Instructor-Led Training | {company}",
            "prepared_by": company,
            "date": datetime.now().strftime("%B %d, %Y"),
            "version": "1.0",
            "overview": self._build_facilitator_overview(curriculum, options, tt_ctx),
            "preparation_checklist": self._build_preparation_checklist(curriculum),
            "timing_guide": self._build_timing_table(curriculum),
            "modules": [],
            "appendix": self._build_facilitator_appendix(curriculum, options),
        }

        # Per-module sections
        for idx, module in enumerate(curriculum.modules, start=1):
            module_section = self._build_facilitator_module_section(
                module, idx, options, tt_ctx, voice,
            )
            content["modules"].append(module_section)

        # Use Claude to expand thin sections with richer instructor notes
        content = self._enrich_facilitator_guide(content, curriculum, options)

        safe_title = re.sub(r"[^\w\s-]", "", curriculum.title).strip()[:80]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"facilitator_guide_{safe_title}_{timestamp}.docx"
        save_path = str(TRAINING_DIR / filename)

        gen = self._get_document_gen()
        result_path = gen.generate(
            content=content,
            doc_type="training_guide",
            title=f"Facilitator Guide - {curriculum.title}",
            save_path=save_path,
        )
        return result_path

    def generate_participant_handouts(
        self,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> str:
        """Generate participant-facing materials (DOCX).

        Includes:
            - Course title, description, and logistics
            - Learning objectives checklist
            - Per-module: key concepts, note-taking areas, activity worksheets
            - Reference / resource list
            - Self-assessment checklist

        Args:
            curriculum: The parsed curriculum.
            options: Pipeline options.

        Returns:
            Absolute path to the generated DOCX file.
        """
        company = self.brand_config.get("company_name", "Our Company")
        al_ctx = AUDIENCE_LEVEL_CONTEXT.get(
            options.audience_level, AUDIENCE_LEVEL_CONTEXT["intermediate"],
        )

        # Build content dict for the document generator
        content: dict[str, Any] = {
            "title": f"Participant Handout: {curriculum.title}",
            "subtitle": f"Training Materials | {company}",
            "date": datetime.now().strftime("%B %d, %Y"),
            "overview": curriculum.description or f"Welcome to {curriculum.title}.",
            "learning_objectives": curriculum.learning_outcomes or self._collect_all_objectives(curriculum),
            "modules": [],
            "resources": [],
            "self_assessment": [],
        }

        # Per-module handout sections
        for idx, module in enumerate(curriculum.modules, start=1):
            module_content = self._build_participant_module(module, idx, al_ctx)
            content["modules"].append(module_content)

        # Resource list
        content["resources"] = self._build_resource_list(curriculum, options)

        # Self-assessment checklist
        content["self_assessment"] = self._build_self_assessment(curriculum)

        # Enrich with Claude
        content = self._enrich_participant_handouts(content, curriculum, options)

        safe_title = re.sub(r"[^\w\s-]", "", curriculum.title).strip()[:80]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"participant_handout_{safe_title}_{timestamp}.docx"
        save_path = str(TRAINING_DIR / filename)

        gen = self._get_document_gen()
        result_path = gen.generate(
            content=content,
            doc_type="training_guide",
            title=f"Participant Handout - {curriculum.title}",
            save_path=save_path,
        )
        return result_path

    def generate_job_aids(
        self,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> list[str]:
        """Generate 1-2 page job aids for each module.

        Each job aid is a branded quick-reference card produced using
        the ``"job_aid"`` document template.

        Args:
            curriculum: The parsed curriculum.
            options: Pipeline options.

        Returns:
            List of absolute file paths (one per module).
        """
        gen = self._get_document_gen()
        paths: list[str] = []

        for idx, module in enumerate(curriculum.modules, start=1):
            content = self._build_job_aid_content(module, idx, curriculum, options)

            safe_mod_title = re.sub(r"[^\w\s-]", "", module.title).strip()[:60]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"job_aid_{idx:02d}_{safe_mod_title}_{timestamp}.docx"
            save_path = str(TRAINING_DIR / filename)

            result_path = gen.generate(
                content=content,
                doc_type="job_aid",
                title=f"Job Aid - {module.title}",
                save_path=save_path,
            )
            paths.append(result_path)
            logger.info("Generated job aid %d/%d: %s", idx, len(curriculum.modules), result_path)

        return paths

    def generate_quiz(
        self,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> dict:
        """Generate assessment quiz and answer key documents.

        Uses Claude to create questions that match the requested
        difficulty and question types, then outputs both a quiz
        document and a separate answer key.

        Args:
            curriculum: The parsed curriculum.
            options: Pipeline options (quiz_question_count,
                quiz_difficulty, quiz_question_types).

        Returns:
            Dict with ``"quiz_path"`` and ``"answer_key_path"`` keys.
        """
        quiz_data = self._generate_quiz_content(curriculum, options)

        gen = self._get_document_gen()
        safe_title = re.sub(r"[^\w\s-]", "", curriculum.title).strip()[:80]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # --- Quiz document (without answers) ---
        quiz_content = self._build_quiz_document_content(quiz_data, curriculum, show_answers=False)
        quiz_path = str(TRAINING_DIR / f"quiz_{safe_title}_{timestamp}.docx")
        quiz_result = gen.generate(
            content=quiz_content,
            doc_type="training_guide",
            title=f"Assessment Quiz - {curriculum.title}",
            save_path=quiz_path,
        )

        # --- Answer key document ---
        key_content = self._build_quiz_document_content(quiz_data, curriculum, show_answers=True)
        key_path = str(TRAINING_DIR / f"answer_key_{safe_title}_{timestamp}.docx")
        key_result = gen.generate(
            content=key_content,
            doc_type="training_guide",
            title=f"Answer Key - {curriculum.title}",
            save_path=key_path,
        )

        return {"quiz_path": quiz_result, "answer_key_path": key_result}

    def generate_microlearning(
        self,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> list[str]:
        """Generate bite-sized microlearning modules.

        Each microlearning module is designed to be consumed in
        ``options.module_duration_minutes`` minutes or less. They
        distill each training module into a focused, standalone
        mini-lesson.

        Args:
            curriculum: The parsed curriculum.
            options: Pipeline options.

        Returns:
            List of absolute file paths.
        """
        gen = self._get_document_gen()
        paths: list[str] = []

        for idx, module in enumerate(curriculum.modules, start=1):
            micro_content = self._build_microlearning_content(module, idx, curriculum, options)

            safe_mod_title = re.sub(r"[^\w\s-]", "", module.title).strip()[:60]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"microlearning_{idx:02d}_{safe_mod_title}_{timestamp}.docx"
            save_path = str(TRAINING_DIR / filename)

            result_path = gen.generate(
                content=micro_content,
                doc_type="training_guide",
                title=f"Microlearning: {module.title}",
                save_path=save_path,
            )
            paths.append(result_path)
            logger.info(
                "Generated microlearning %d/%d: %s",
                idx,
                len(curriculum.modules),
                result_path,
            )

        return paths

    def generate_agent_script(
        self,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> str:
        """Generate a call-centre / sales agent script (DOCX).

        Sections:
            - Opening / greeting
            - Discovery questions
            - Value propositions by product feature
            - Objection handling table (objection | response)
            - Closing / next steps
            - Compliance disclosures

        Args:
            curriculum: The parsed curriculum.
            options: Pipeline options (product_info, call_objectives).

        Returns:
            Absolute path to the generated DOCX file.
        """
        system_prompt = (
            "You are an expert sales training script writer. You create "
            "detailed, production-ready agent scripts for call centres and "
            "sales teams. Respond with valid JSON only -- no markdown fences."
        )
        user_content = self._build_agent_script_prompt(curriculum, options)
        raw_response = self._call_claude(system_prompt, user_content, max_tokens=4096)
        script_data = self._parse_json_response(raw_response)

        # Build document content from script data
        content = self._build_agent_script_document(script_data, curriculum, options)

        safe_title = re.sub(r"[^\w\s-]", "", curriculum.title).strip()[:80]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"agent_script_{safe_title}_{timestamp}.docx"
        save_path = str(TRAINING_DIR / filename)

        gen = self._get_document_gen()
        result_path = gen.generate(
            content=content,
            doc_type="training_guide",
            title=f"Agent Script - {curriculum.title}",
            save_path=save_path,
        )
        return result_path

    # ------------------------------------------------------------------
    # ZIP packaging
    # ------------------------------------------------------------------

    def package_outputs(self, package: TrainingPackage, title: str) -> str:
        """Bundle all generated files into a ZIP archive.

        Args:
            package: The :class:`TrainingPackage` containing output paths.
            title: Curriculum title (used in the ZIP filename).

        Returns:
            Absolute path to the ZIP file.
        """
        safe_title = re.sub(r"[^\w\s-]", "", title).strip()[:60]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"training_package_{safe_title}_{timestamp}.zip"
        zip_path = TRAINING_DIR / zip_filename

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for output_key, file_ref in package.outputs.items():
                # file_ref may be a string, list of strings, or dict of strings
                file_paths = self._flatten_file_refs(file_ref)
                for fp in file_paths:
                    fp_path = Path(fp)
                    if fp_path.exists():
                        arcname = f"{output_key}/{fp_path.name}"
                        zf.write(fp_path, arcname)
                        logger.debug("Added to ZIP: %s -> %s", fp, arcname)
                    else:
                        logger.warning("File not found, skipping: %s", fp)

            # Include a manifest JSON with metadata
            manifest = {
                "title": title,
                "generated_at": datetime.now().isoformat(),
                "outputs": {
                    k: self._flatten_file_refs(v)
                    for k, v in package.outputs.items()
                },
                "errors": package.errors,
            }
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))

        return str(zip_path)

    @staticmethod
    def _flatten_file_refs(ref: Any) -> list[str]:
        """Normalise a file reference (str, list, or dict) into a flat list of paths."""
        if isinstance(ref, str):
            return [ref]
        elif isinstance(ref, list):
            return [str(p) for p in ref]
        elif isinstance(ref, dict):
            paths = []
            for v in ref.values():
                if isinstance(v, str):
                    paths.append(v)
                elif isinstance(v, list):
                    paths.extend(str(p) for p in v)
            return paths
        return []

    # ==================================================================
    # Claude prompts
    # ==================================================================

    def _build_structure_prompt(self, content: str, options: PipelineOptions) -> str:
        """Build the Claude prompt for structuring raw text into curriculum JSON.

        The prompt instructs Claude to extract logical modules, objectives,
        topics, activities, and key takeaways while respecting the requested
        training type and audience level.
        """
        tt_ctx = TRAINING_TYPE_CONTEXT.get(options.training_type, TRAINING_TYPE_CONTEXT["general"])
        al_ctx = AUDIENCE_LEVEL_CONTEXT.get(options.audience_level, AUDIENCE_LEVEL_CONTEXT["intermediate"])
        company = self.brand_config.get("company_name", "Our Company")
        voice = self.brand_config.get("voice", "professional")

        return f"""Analyse the following raw content and transform it into a structured training curriculum.

CONTEXT:
- Company: {company}
- Brand voice: {voice}
- Training type: {options.training_type} ({tt_ctx['focus']})
- Tone: {tt_ctx['tone']}
- Suggested activity types: {tt_ctx['activities']}
- Audience level: {options.audience_level}
- Vocabulary guidance: {al_ctx['vocabulary']}
- Content depth: {al_ctx['depth']}
- Pacing: {al_ctx['pacing']}
- Language: {options.language}

Return a JSON object matching this schema EXACTLY:
{{
    "title": "Curriculum title derived from the content",
    "description": "2-3 sentence course description",
    "target_audience": "Description of the intended learners",
    "total_duration": "Estimated total duration (e.g. '4 hours')",
    "prerequisites": ["Prerequisite 1", "Prerequisite 2"],
    "learning_outcomes": ["Outcome 1", "Outcome 2"],
    "modules": [
        {{
            "title": "Module title",
            "objectives": ["Specific, measurable learning objective using action verbs"],
            "topics": [
                {{
                    "title": "Topic title",
                    "content": "Detailed topic content / explanation",
                    "key_points": ["Key point 1", "Key point 2"]
                }}
            ],
            "activities": [
                {{
                    "title": "Activity name",
                    "type": "exercise|discussion|role_play|case_study|demonstration|lab",
                    "instructions": "Detailed step-by-step activity instructions",
                    "duration": "Estimated duration (e.g. '15 minutes')"
                }}
            ],
            "duration_minutes": 30,
            "key_takeaways": ["Takeaway 1", "Takeaway 2"]
        }}
    ],
    "metadata": {{}}
}}

GUIDELINES:
1. Identify natural module boundaries in the content. Each module should cover a coherent theme.
2. Write learning objectives using Bloom's taxonomy action verbs appropriate for the {options.audience_level} level.
3. Ensure topic content is substantive -- at least 3-5 sentences per topic explaining the concept clearly.
4. Design activities that reinforce learning and are appropriate for {options.training_type} training.
5. Keep module durations realistic (20-60 minutes each).
6. Maintain the original meaning and terminology of the content.
7. If the content is sparse, create fewer but higher-quality modules rather than many thin ones.
8. Include at least 2 key takeaways per module.

RAW CONTENT:
---
{content}
---

Respond with valid JSON only. No markdown fences. No commentary."""

    def _build_topic_prompt(self, topic: str, options: PipelineOptions) -> str:
        """Build the Claude prompt for generating a full curriculum from a topic.

        This prompt asks Claude to design the entire curriculum from scratch
        based on a short topic description.
        """
        tt_ctx = TRAINING_TYPE_CONTEXT.get(options.training_type, TRAINING_TYPE_CONTEXT["general"])
        al_ctx = AUDIENCE_LEVEL_CONTEXT.get(options.audience_level, AUDIENCE_LEVEL_CONTEXT["intermediate"])
        company = self.brand_config.get("company_name", "Our Company")
        voice = self.brand_config.get("voice", "professional")

        module_count_hint = {
            "beginner": "3-5",
            "intermediate": "4-6",
            "advanced": "5-8",
        }.get(options.audience_level, "4-6")

        return f"""Design a comprehensive training curriculum on the following topic.

TOPIC: {topic}

CONTEXT:
- Company: {company}
- Brand voice: {voice}
- Training type: {options.training_type} ({tt_ctx['focus']})
- Tone: {tt_ctx['tone']}
- Suggested activity types: {tt_ctx['activities']}
- Audience level: {options.audience_level}
- Vocabulary guidance: {al_ctx['vocabulary']}
- Content depth: {al_ctx['depth']}
- Pacing: {al_ctx['pacing']}
- Language: {options.language}

Create a complete curriculum with {module_count_hint} modules. Return a JSON object matching this schema EXACTLY:
{{
    "title": "A compelling, professional curriculum title",
    "description": "2-3 sentence course description explaining what learners will achieve",
    "target_audience": "Description of the intended learners and their background",
    "total_duration": "Estimated total duration (e.g. '6 hours')",
    "prerequisites": ["Prerequisite 1"],
    "learning_outcomes": [
        "By the end of this course, participants will be able to ...",
        "Participants will demonstrate the ability to ..."
    ],
    "modules": [
        {{
            "title": "Module title that clearly states the topic",
            "objectives": [
                "Specific, measurable objective using Bloom's taxonomy verbs"
            ],
            "topics": [
                {{
                    "title": "Topic title",
                    "content": "Detailed explanation of this topic. Include definitions, examples, and context. This should be 4-8 sentences providing real instructional content.",
                    "key_points": ["Key point 1", "Key point 2", "Key point 3"]
                }}
            ],
            "activities": [
                {{
                    "title": "Activity name",
                    "type": "exercise|discussion|role_play|case_study|demonstration|lab",
                    "instructions": "Clear, step-by-step instructions that a facilitator could follow without additional preparation. Include group size, materials needed, and expected outcome.",
                    "duration": "15 minutes"
                }}
            ],
            "duration_minutes": 45,
            "key_takeaways": ["Concise takeaway statement 1", "Concise takeaway statement 2"]
        }}
    ],
    "metadata": {{
        "training_type": "{options.training_type}",
        "audience_level": "{options.audience_level}",
        "language": "{options.language}"
    }}
}}

DESIGN GUIDELINES:
1. Modules should build on each other logically -- start with foundations and progress to application.
2. Each module should include 2-4 substantive topics with real instructional content (not placeholders).
3. Design at least one hands-on activity per module appropriate for {options.training_type} training.
4. Learning objectives must be measurable using action verbs: define, explain, demonstrate, analyse, evaluate, create.
5. Duration estimates should be realistic: topics need 5-10 min each, activities need 10-20 min each.
6. For {options.audience_level} learners: {al_ctx['depth']}.
7. The final module should focus on application, synthesis, or next steps.
8. Include a mix of activity types: {tt_ctx['activities']}.

Respond with valid JSON only. No markdown fences. No commentary."""

    def _build_agent_script_prompt(
        self,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> str:
        """Build the Claude prompt for generating an agent / sales script.

        The script is structured around the curriculum content and enriched
        with product info and call objectives from the pipeline options.
        """
        company = self.brand_config.get("company_name", "Our Company")
        voice = self.brand_config.get("voice", "professional")
        terminology = self.brand_config.get("terminology", {})

        # Collect all topics and key points for script context
        topic_summary_parts: list[str] = []
        for module in curriculum.modules:
            for topic in module.topics:
                tp_title = topic.get("title", "")
                tp_content = topic.get("content", "")
                key_pts = topic.get("key_points", [])
                part = f"- {tp_title}: {tp_content}"
                if key_pts:
                    part += f"  Key points: {'; '.join(key_pts)}"
                topic_summary_parts.append(part)
        topic_summary = "\n".join(topic_summary_parts) if topic_summary_parts else "General training content."

        product_info = options.product_info or "Refer to the training content above for product/service details."
        call_objectives = options.call_objectives or "Educate the customer and advance to the next step."

        term_guidance = ""
        if terminology:
            term_lines = [f"  - Use '{v}' instead of '{k}'" for k, v in terminology.items()]
            term_guidance = "TERMINOLOGY REQUIREMENTS:\n" + "\n".join(term_lines)

        return f"""Create a comprehensive call-centre / sales agent script based on the following training content.

COMPANY: {company}
BRAND VOICE: {voice}
{term_guidance}

PRODUCT/SERVICE INFORMATION:
{product_info}

CALL OBJECTIVES:
{call_objectives}

TRAINING CONTENT SUMMARY:
{topic_summary}

Return a JSON object with this structure:
{{
    "script_title": "Script title",
    "opening": {{
        "greeting": "Word-for-word greeting script with [CUSTOMER_NAME] placeholder",
        "introduction": "How to introduce yourself and the purpose of the call",
        "rapport_building": "1-2 rapport-building statements or questions"
    }},
    "discovery_questions": [
        {{
            "question": "The exact question to ask",
            "purpose": "What this question helps uncover",
            "follow_up": "Suggested follow-up based on common responses"
        }}
    ],
    "value_propositions": [
        {{
            "feature": "Product/service feature name",
            "benefit_statement": "Customer-facing benefit statement",
            "proof_point": "Supporting evidence, statistic, or example",
            "transition": "How to naturally move to the next point"
        }}
    ],
    "objection_handling": [
        {{
            "objection": "Common customer objection",
            "response": "Recommended response (acknowledge, clarify, resolve)",
            "technique": "The objection handling technique being used"
        }}
    ],
    "closing": {{
        "trial_close": "A trial close question to gauge interest",
        "commitment_ask": "The primary call-to-action / commitment request",
        "next_steps": "What to communicate about next steps",
        "wrap_up": "Professional wrap-up and farewell script"
    }},
    "compliance_disclosures": [
        "Required disclosure statement 1",
        "Required disclosure statement 2"
    ],
    "tips": [
        "Coaching tip for agents"
    ]
}}

GUIDELINES:
1. Scripts should sound natural and conversational, not robotic.
2. Include transition phrases between sections.
3. Discovery questions should progress from broad to specific.
4. Value propositions should connect features to customer needs.
5. Objection responses should use the Acknowledge-Clarify-Resolve pattern.
6. Include at least 5 discovery questions and 5 objection handling scenarios.
7. Compliance disclosures should cover standard regulatory requirements.
8. Voice and tone must match: {voice}.

Respond with valid JSON only. No markdown fences. No commentary."""

    # ==================================================================
    # Slide building helpers
    # ==================================================================

    def _build_slides_from_curriculum(
        self,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> list[dict]:
        """Convert a :class:`ParsedCurriculum` into slides_data for the presentation generator.

        Returns:
            A list of slide dicts compatible with
            :meth:`BrandedPresentationGenerator.generate`.
        """
        company = self.brand_config.get("company_name", "Our Company")
        slides: list[dict] = []

        # 1. Title slide
        slides.append({
            "layout": "title",
            "title": curriculum.title,
            "subtitle": f"{company} | {curriculum.target_audience or 'Training Program'}",
            "body": curriculum.description or "",
            "speaker_notes": (
                f"Welcome participants. This training covers: {curriculum.description}. "
                f"Total duration: {curriculum.total_duration or 'see agenda'}."
            ),
        })

        # 2. Agenda / overview slide
        agenda_bullets = [f"Module {i}: {m.title}" for i, m in enumerate(curriculum.modules, 1)]
        if curriculum.total_duration:
            agenda_bullets.append(f"Total Duration: {curriculum.total_duration}")
        slides.append({
            "layout": "content",
            "title": "Agenda",
            "bullets": agenda_bullets,
            "speaker_notes": "Walk through the agenda. Ask if there are questions about the schedule.",
        })

        # 3. Learning objectives slide
        objectives = curriculum.learning_outcomes or self._collect_all_objectives(curriculum)
        if objectives:
            slides.append({
                "layout": "content",
                "title": "Learning Objectives",
                "bullets": objectives[:8],  # Cap at 8 to avoid overcrowding
                "speaker_notes": (
                    "Review the learning objectives. These are what participants "
                    "should be able to do by the end of this training."
                ),
            })

        # 4. Per-module slides
        for mod_idx, module in enumerate(curriculum.modules, start=1):
            # Section divider
            slides.append({
                "layout": "section_divider",
                "title": f"Module {mod_idx}: {module.title}",
                "subtitle": f"Duration: {module.duration_minutes} minutes",
                "speaker_notes": (
                    f"Transition to Module {mod_idx}. "
                    f"Objectives: {'; '.join(module.objectives[:3]) if module.objectives else 'See module content.'}"
                ),
            })

            # Module objectives slide (if module has its own objectives)
            if module.objectives:
                slides.append({
                    "layout": "content",
                    "title": f"{module.title} - Objectives",
                    "bullets": module.objectives,
                    "speaker_notes": "Review module-specific objectives with participants.",
                })

            # Content slides for each topic
            for topic in module.topics:
                topic_title = topic.get("title", "Topic")
                topic_content = topic.get("content", "")
                key_points = topic.get("key_points", [])

                slide: dict[str, Any] = {
                    "layout": "content",
                    "title": topic_title,
                    "speaker_notes": topic_content[:500] if topic_content else "",
                }

                if key_points:
                    slide["bullets"] = key_points
                elif topic_content:
                    # Split long content into bullet-point-like chunks
                    sentences = [s.strip() for s in topic_content.split(". ") if s.strip()]
                    slide["bullets"] = [f"{s}." if not s.endswith(".") else s for s in sentences[:6]]
                else:
                    slide["body"] = topic_title

                slides.append(slide)

            # Activity slide (if module has activities)
            if module.activities:
                activity_bullets = []
                for act in module.activities:
                    act_title = act.get("title", "Activity")
                    act_type = act.get("type", "exercise")
                    act_duration = act.get("duration", "")
                    duration_str = f" ({act_duration})" if act_duration else ""
                    activity_bullets.append(f"{act_title} [{act_type}]{duration_str}")

                slides.append({
                    "layout": "content",
                    "title": f"Activities: {module.title}",
                    "bullets": activity_bullets,
                    "speaker_notes": (
                        "Facilitate the activities listed. "
                        "See the Facilitator Guide for detailed instructions."
                    ),
                })

            # Key takeaways for this module
            if module.key_takeaways:
                slides.append({
                    "layout": "content",
                    "title": f"Key Takeaways: {module.title}",
                    "bullets": module.key_takeaways,
                    "speaker_notes": "Summarise the key takeaways. Ask for questions before moving on.",
                })

        # 5. Overall key takeaways slide
        all_takeaways = []
        for m in curriculum.modules:
            all_takeaways.extend(m.key_takeaways[:2])
        if all_takeaways:
            slides.append({
                "layout": "content",
                "title": "Key Takeaways",
                "bullets": all_takeaways[:8],
                "speaker_notes": "Review the overall key takeaways from the entire training.",
            })

        # 6. Assessment preview slide (if quiz is enabled)
        if options.quiz:
            slides.append({
                "layout": "content",
                "title": "Knowledge Check",
                "bullets": [
                    f"Assessment: {options.quiz_question_count} questions",
                    f"Question types: {', '.join(options.quiz_question_types)}",
                    f"Difficulty level: {options.quiz_difficulty}",
                    "Review your notes and key takeaways before the assessment",
                ],
                "speaker_notes": (
                    "Introduce the upcoming assessment. Reassure participants that "
                    "the goal is to reinforce learning, not to grade them."
                ),
            })

        # 7. Q&A / Closing slide
        slides.append({
            "layout": "closing",
            "title": "Questions & Next Steps",
            "subtitle": f"Thank you for participating! | {company}",
            "speaker_notes": (
                "Open the floor for questions. Provide information about "
                "follow-up resources and next steps."
            ),
        })

        return slides

    # ==================================================================
    # Facilitator guide helpers
    # ==================================================================

    def _build_facilitator_overview(
        self,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
        tt_ctx: dict,
    ) -> str:
        """Build the course overview paragraph for the facilitator guide."""
        audience = curriculum.target_audience or f"{options.audience_level.title()} learners"
        duration = curriculum.total_duration or f"{sum(m.duration_minutes for m in curriculum.modules)} minutes"
        prereqs = ", ".join(curriculum.prerequisites) if curriculum.prerequisites else "None"

        return (
            f"Course: {curriculum.title}\n\n"
            f"Description: {curriculum.description or 'See module summaries below.'}\n\n"
            f"Target Audience: {audience}\n\n"
            f"Total Duration: {duration}\n\n"
            f"Prerequisites: {prereqs}\n\n"
            f"Training Type: {options.training_type.title()} -- {tt_ctx['focus']}\n\n"
            f"Delivery Tone: {tt_ctx['tone']}\n\n"
            f"Number of Modules: {len(curriculum.modules)}"
        )

    def _build_preparation_checklist(self, curriculum: ParsedCurriculum) -> list[str]:
        """Build a preparation checklist for the facilitator."""
        checklist = [
            "Review all module content and speaker notes thoroughly",
            "Prepare printed copies of participant handouts",
            "Set up presentation equipment and test slides",
            "Prepare activity materials (see activity sections for details)",
            "Verify room setup accommodates group activities",
            "Prepare sign-in sheet and evaluation forms",
            "Test any required software or online tools",
            "Review quiz / assessment materials and answer key",
        ]
        # Add module-specific prep items
        for module in curriculum.modules:
            if module.activities:
                for act in module.activities:
                    act_title = act.get("title", "activity")
                    checklist.append(f"Prepare materials for: {act_title}")
        return checklist

    def _build_timing_table(self, curriculum: ParsedCurriculum) -> list[dict]:
        """Build a timing guide as a list of row dicts for the facilitator guide.

        Each row: {time, topic, activity, materials}
        """
        rows: list[dict] = []
        elapsed = 0

        # Welcome / introduction
        rows.append({
            "time": f"0:00 - 0:10",
            "topic": "Welcome & Introductions",
            "activity": "Icebreaker / introductions",
            "materials": "Sign-in sheet, name tags",
        })
        elapsed = 10

        # Objectives overview
        rows.append({
            "time": f"0:{elapsed:02d} - 0:{elapsed + 5:02d}",
            "topic": "Course Overview & Objectives",
            "activity": "Presentation",
            "materials": "Training deck slides 1-3",
        })
        elapsed += 5

        # Modules
        for idx, module in enumerate(curriculum.modules, start=1):
            mod_start = elapsed
            # Content delivery
            content_duration = max(10, module.duration_minutes - sum(
                int(re.search(r"\d+", act.get("duration", "10")).group())
                if re.search(r"\d+", act.get("duration", "10"))
                else 10
                for act in module.activities
            )) if module.activities else module.duration_minutes

            hours_start = mod_start // 60
            mins_start = mod_start % 60
            end_time = mod_start + content_duration
            hours_end = end_time // 60
            mins_end = end_time % 60

            rows.append({
                "time": f"{hours_start}:{mins_start:02d} - {hours_end}:{mins_end:02d}",
                "topic": f"Module {idx}: {module.title}",
                "activity": "Presentation & discussion",
                "materials": f"Slide deck (Module {idx} section), handouts",
            })
            elapsed = end_time

            # Activities
            for act in module.activities:
                act_title = act.get("title", "Activity")
                act_duration_str = act.get("duration", "10 minutes")
                act_minutes = 10
                duration_match = re.search(r"(\d+)", act_duration_str)
                if duration_match:
                    act_minutes = int(duration_match.group(1))

                a_start = elapsed
                a_end = elapsed + act_minutes
                h_s, m_s = divmod(a_start, 60)
                h_e, m_e = divmod(a_end, 60)

                rows.append({
                    "time": f"{h_s}:{m_s:02d} - {h_e}:{m_e:02d}",
                    "topic": f"  Activity: {act_title}",
                    "activity": act.get("type", "exercise").replace("_", " ").title(),
                    "materials": "Activity worksheets, flip chart",
                })
                elapsed = a_end

            # Break after every 2 modules (except the last)
            if idx % 2 == 0 and idx < len(curriculum.modules):
                b_start = elapsed
                b_end = elapsed + 10
                h_s, m_s = divmod(b_start, 60)
                h_e, m_e = divmod(b_end, 60)
                rows.append({
                    "time": f"{h_s}:{m_s:02d} - {h_e}:{m_e:02d}",
                    "topic": "Break",
                    "activity": "---",
                    "materials": "---",
                })
                elapsed = b_end

        # Wrap-up
        w_start = elapsed
        w_end = elapsed + 10
        h_s, m_s = divmod(w_start, 60)
        h_e, m_e = divmod(w_end, 60)
        rows.append({
            "time": f"{h_s}:{m_s:02d} - {h_e}:{m_e:02d}",
            "topic": "Wrap-Up, Q&A, & Evaluation",
            "activity": "Open discussion / feedback forms",
            "materials": "Evaluation forms",
        })

        return rows

    def _build_facilitator_module_section(
        self,
        module: TrainingModule,
        mod_idx: int,
        options: PipelineOptions,
        tt_ctx: dict,
        voice: str,
    ) -> dict:
        """Build a facilitator guide section for a single module.

        Returns a dict with instructor notes, discussion prompts,
        activity instructions, and common Q&A.
        """
        # Instructor notes from topics
        instructor_notes: list[str] = []
        for topic in module.topics:
            title = topic.get("title", "Topic")
            content = topic.get("content", "")
            key_pts = topic.get("key_points", [])
            note = f"TOPIC: {title}\n"
            if content:
                note += f"  Content: {content}\n"
            if key_pts:
                note += f"  Key points to emphasise: {'; '.join(key_pts)}\n"
            instructor_notes.append(note)

        # Discussion prompts
        discussion_prompts: list[str] = []
        if module.objectives:
            discussion_prompts.append(
                f"Opening question: What do you already know about {module.title.lower()}?"
            )
        discussion_prompts.append(
            f"Comprehension check: Can someone summarise the main idea of {module.title}?"
        )
        discussion_prompts.append(
            "Application question: How would you apply what we just covered in your daily work?"
        )
        if options.training_type == "sales":
            discussion_prompts.append(
                "Role-play prompt: Let's practise this scenario with a partner."
            )
        elif options.training_type == "compliance":
            discussion_prompts.append(
                "Scenario analysis: What would you do if you encountered this situation?"
            )

        # Activity facilitation instructions
        activity_instructions: list[dict] = []
        for act in module.activities:
            activity_instructions.append({
                "title": act.get("title", "Activity"),
                "type": act.get("type", "exercise"),
                "duration": act.get("duration", "10 minutes"),
                "setup": f"Prepare materials for {act.get('title', 'this activity')}. "
                         f"Ensure participants are arranged for {act.get('type', 'group work')}.",
                "instructions": act.get("instructions", "Follow the activity worksheet."),
                "debrief": f"After the activity, ask participants to share their key insights. "
                           f"Connect their responses back to the module objectives.",
            })

        # Common questions (generated based on content)
        common_qa: list[dict] = []
        if module.topics:
            first_topic = module.topics[0].get("title", module.title)
            common_qa.append({
                "question": f"Why is {first_topic.lower()} important?",
                "answer": f"Refer to the key points in the topic section. "
                          f"Emphasise practical relevance to the learners' roles.",
            })
        common_qa.append({
            "question": f"How does {module.title} relate to what we covered earlier?",
            "answer": "Draw connections to previous modules. Highlight how skills build on each other.",
        })
        common_qa.append({
            "question": "Can you provide a real-world example?",
            "answer": f"Use examples from the {options.training_type} context. "
                      f"Refer to case studies or past experiences relevant to the audience.",
        })

        return {
            "module_number": mod_idx,
            "title": module.title,
            "duration": f"{module.duration_minutes} minutes",
            "objectives": module.objectives,
            "instructor_notes": instructor_notes,
            "discussion_prompts": discussion_prompts,
            "activity_instructions": activity_instructions,
            "common_qa": common_qa,
            "key_takeaways": module.key_takeaways,
            "transition_note": (
                f"After completing Module {mod_idx}, transition to the next section by "
                f"summarising key takeaways and previewing what comes next."
            ),
        }

    def _build_facilitator_appendix(
        self,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> dict:
        """Build the appendix section for the facilitator guide."""
        appendix: dict[str, Any] = {
            "answer_key_reference": (
                "See the separate Answer Key document for quiz solutions."
                if options.quiz
                else "No formal assessment included in this training package."
            ),
            "additional_resources": [
                f"Participant handouts for {curriculum.title}",
                "Job aids (one per module) for quick reference",
            ],
            "evaluation_guidance": (
                "Distribute evaluation forms at the end of the session. "
                "Collect feedback on content relevance, facilitator effectiveness, "
                "and suggestions for improvement."
            ),
            "revision_history": [
                {
                    "version": "1.0",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "changes": "Initial release",
                },
            ],
        }
        if options.microlearning:
            appendix["additional_resources"].append(
                "Microlearning modules for reinforcement after the training session"
            )
        if options.agent_script:
            appendix["additional_resources"].append(
                "Agent script for call-centre / sales application of training content"
            )
        return appendix

    def _enrich_facilitator_guide(
        self,
        content: dict,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> dict:
        """Use Claude to enrich thin facilitator guide sections with deeper instructor notes.

        Sends the existing guide structure to Claude and asks for expanded
        instructor talking points and facilitation tips.  Updates the content
        dict in-place and returns it.
        """
        company = self.brand_config.get("company_name", "Our Company")
        voice = self.brand_config.get("voice", "professional")
        tt_ctx = TRAINING_TYPE_CONTEXT.get(options.training_type, TRAINING_TYPE_CONTEXT["general"])

        # Build a concise summary of what we already have
        module_summaries: list[str] = []
        for mod_section in content.get("modules", []):
            mod_title = mod_section.get("title", "Module")
            obj_count = len(mod_section.get("objectives", []))
            act_count = len(mod_section.get("activity_instructions", []))
            module_summaries.append(
                f"- {mod_title} ({obj_count} objectives, {act_count} activities)"
            )

        system_prompt = (
            "You are an expert facilitator coach. Expand the provided instructor "
            "notes with practical facilitation tips, timing advice, and engagement "
            "strategies. Respond with valid JSON only."
        )

        user_content = f"""Enhance the facilitator guide for the following training:

TRAINING: {curriculum.title}
COMPANY: {company}
VOICE: {voice}
TYPE: {options.training_type} ({tt_ctx['tone']})
AUDIENCE: {options.audience_level}

EXISTING MODULES:
{chr(10).join(module_summaries)}

For each module (by index starting at 0), provide:
{{
    "enrichments": [
        {{
            "module_index": 0,
            "additional_talking_points": ["point 1", "point 2"],
            "facilitation_tips": ["tip 1", "tip 2"],
            "engagement_strategies": ["strategy 1"],
            "time_management_advice": "Advice for pacing this module"
        }}
    ]
}}

Respond with valid JSON only. No markdown fences."""

        try:
            raw = self._call_claude(system_prompt, user_content, max_tokens=3000)
            enrichments_data = self._parse_json_response(raw)
            enrichments = enrichments_data.get("enrichments", [])

            for enrichment in enrichments:
                mod_idx = enrichment.get("module_index", -1)
                if 0 <= mod_idx < len(content.get("modules", [])):
                    mod = content["modules"][mod_idx]
                    mod["additional_talking_points"] = enrichment.get("additional_talking_points", [])
                    mod["facilitation_tips"] = enrichment.get("facilitation_tips", [])
                    mod["engagement_strategies"] = enrichment.get("engagement_strategies", [])
                    mod["time_management_advice"] = enrichment.get("time_management_advice", "")

        except Exception as exc:
            logger.warning("Failed to enrich facilitator guide (non-fatal): %s", exc)

        return content

    # ==================================================================
    # Participant handout helpers
    # ==================================================================

    def _build_participant_module(
        self,
        module: TrainingModule,
        mod_idx: int,
        al_ctx: dict,
    ) -> dict:
        """Build a participant handout section for a single module."""
        # Key concepts summary
        key_concepts: list[str] = []
        for topic in module.topics:
            title = topic.get("title", "")
            content = topic.get("content", "")
            key_pts = topic.get("key_points", [])
            if key_pts:
                for pt in key_pts:
                    key_concepts.append(f"{title}: {pt}")
            elif content:
                # Take the first sentence as a summary
                first_sentence = content.split(". ")[0].strip()
                if first_sentence:
                    key_concepts.append(f"{title}: {first_sentence}.")

        # Activity worksheets
        worksheets: list[dict] = []
        for act in module.activities:
            worksheets.append({
                "title": act.get("title", "Activity"),
                "type": act.get("type", "exercise"),
                "instructions": act.get("instructions", ""),
                "space_for_notes": True,
            })

        return {
            "module_number": mod_idx,
            "title": module.title,
            "objectives": module.objectives,
            "key_concepts": key_concepts,
            "note_taking_prompts": [
                f"What are the most important ideas from {module.title}?",
                "How does this relate to my current role?",
                "What questions do I still have?",
                "What will I do differently as a result of this module?",
            ],
            "worksheets": worksheets,
            "key_takeaways": module.key_takeaways,
        }

    def _build_resource_list(
        self,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> list[str]:
        """Build a reference / resource list for participant handouts."""
        resources = [
            f"Training presentation deck for {curriculum.title}",
            "Job aids (quick-reference cards) for each module",
        ]
        if options.quiz:
            resources.append("Post-training knowledge assessment")
        if options.microlearning:
            resources.append("Microlearning modules for ongoing reinforcement")
        if curriculum.prerequisites:
            resources.append(f"Prerequisites review: {', '.join(curriculum.prerequisites)}")
        resources.append(
            "Contact your manager or the training team for additional support"
        )
        return resources

    def _build_self_assessment(self, curriculum: ParsedCurriculum) -> list[str]:
        """Build a self-assessment checklist from the curriculum objectives."""
        checklist: list[str] = []
        all_objectives = self._collect_all_objectives(curriculum)
        for obj in all_objectives:
            checklist.append(f"I can {obj.lower().lstrip('to ').lstrip('be able to ')}")
        if not checklist:
            for module in curriculum.modules:
                checklist.append(f"I understand the key concepts of {module.title}")
        return checklist

    def _enrich_participant_handouts(
        self,
        content: dict,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> dict:
        """Use Claude to add additional context and learning tips to handouts."""
        company = self.brand_config.get("company_name", "Our Company")
        al_ctx = AUDIENCE_LEVEL_CONTEXT.get(
            options.audience_level, AUDIENCE_LEVEL_CONTEXT["intermediate"],
        )

        system_prompt = (
            "You are an instructional designer creating participant-friendly "
            "learning materials. Add helpful study tips and memory aids. "
            "Respond with valid JSON only."
        )

        module_titles = [m.title for m in curriculum.modules]
        user_content = f"""Enhance participant handout materials for:

TRAINING: {curriculum.title}
COMPANY: {company}
AUDIENCE LEVEL: {options.audience_level} ({al_ctx['vocabulary']})
MODULES: {json.dumps(module_titles)}

Provide:
{{
    "study_tips": ["Practical study tip 1", "tip 2", "tip 3"],
    "memory_aids": [
        {{
            "module_title": "Module name",
            "mnemonic_or_analogy": "A helpful memory device or analogy"
        }}
    ],
    "application_prompts": ["How to apply this in daily work prompt 1"]
}}

Respond with valid JSON only. No markdown fences."""

        try:
            raw = self._call_claude(system_prompt, user_content, max_tokens=2000)
            enrichment = self._parse_json_response(raw)

            content["study_tips"] = enrichment.get("study_tips", [])
            content["memory_aids"] = enrichment.get("memory_aids", [])
            content["application_prompts"] = enrichment.get("application_prompts", [])
        except Exception as exc:
            logger.warning("Failed to enrich participant handouts (non-fatal): %s", exc)

        return content

    # ==================================================================
    # Job aid helpers
    # ==================================================================

    def _build_job_aid_content(
        self,
        module: TrainingModule,
        mod_idx: int,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> dict:
        """Build the content dict for a single module's job aid.

        Uses Claude to distill the module into a concise 1-2 page
        quick-reference format.
        """
        company = self.brand_config.get("company_name", "Our Company")
        voice = self.brand_config.get("voice", "professional")

        # Gather module content for Claude
        topic_texts: list[str] = []
        for topic in module.topics:
            t = topic.get("title", "")
            c = topic.get("content", "")
            kp = topic.get("key_points", [])
            part = f"{t}: {c}" if c else t
            if kp:
                part += f" (Key: {'; '.join(kp)})"
            topic_texts.append(part)

        system_prompt = (
            "You are a technical writer creating concise job aids. "
            "Produce content suitable for a 1-2 page quick-reference card. "
            "Respond with valid JSON only."
        )

        user_content = f"""Create a job aid for the following training module:

MODULE: {module.title} (Module {mod_idx} of {len(curriculum.modules)} in "{curriculum.title}")
COMPANY: {company}
VOICE: {voice}
AUDIENCE: {options.audience_level}

TOPIC CONTENT:
{chr(10).join(topic_texts)}

OBJECTIVES:
{chr(10).join(f'- {o}' for o in module.objectives)}

Return a JSON object:
{{
    "title": "Job Aid: {module.title}",
    "purpose": "One-sentence purpose statement",
    "when_to_use": "When should the reader reference this job aid",
    "quick_reference_steps": [
        {{
            "step_number": 1,
            "action": "Concise action description",
            "details": "Additional detail or tip",
            "warning": "Optional cautionary note (empty string if none)"
        }}
    ],
    "key_definitions": [
        {{"term": "Term", "definition": "Brief definition"}}
    ],
    "dos_and_donts": {{
        "dos": ["Do this", "Do that"],
        "donts": ["Avoid this", "Never do that"]
    }},
    "quick_tips": ["Practical tip 1", "Practical tip 2"],
    "escalation_path": "Who to contact for help or exceptions"
}}

Respond with valid JSON only. No markdown fences."""

        try:
            raw = self._call_claude(system_prompt, user_content, max_tokens=2500)
            job_aid_data = self._parse_json_response(raw)
        except Exception as exc:
            logger.warning("Claude job aid generation failed, using fallback: %s", exc)
            # Fallback content from the raw module data
            job_aid_data = {
                "title": f"Job Aid: {module.title}",
                "purpose": f"Quick reference for {module.title}",
                "when_to_use": f"Reference this card when applying concepts from {module.title}.",
                "quick_reference_steps": [
                    {
                        "step_number": i + 1,
                        "action": kp,
                        "details": "",
                        "warning": "",
                    }
                    for i, kp in enumerate(module.key_takeaways)
                ],
                "key_definitions": [],
                "dos_and_donts": {"dos": module.key_takeaways, "donts": []},
                "quick_tips": module.key_takeaways[:3],
                "escalation_path": "Contact your manager or training team.",
            }

        return job_aid_data

    # ==================================================================
    # Quiz helpers
    # ==================================================================

    def _generate_quiz_content(
        self,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> dict:
        """Use Claude to generate quiz questions and answers.

        Returns a dict with a ``questions`` list, each containing
        the question text, type, options (for MC), correct answer,
        and explanation.
        """
        company = self.brand_config.get("company_name", "Our Company")

        # Build curriculum summary for context
        module_summaries: list[str] = []
        for mod in curriculum.modules:
            topics = [t.get("title", "") for t in mod.topics]
            key_pts: list[str] = []
            for t in mod.topics:
                key_pts.extend(t.get("key_points", []))
            summary = f"Module: {mod.title}\n  Topics: {', '.join(topics)}\n  Key points: {'; '.join(key_pts)}"
            module_summaries.append(summary)

        difficulty_guidance = {
            "comprehension": (
                "Questions should test whether learners understand and can recall "
                "key concepts, definitions, and facts."
            ),
            "application": (
                "Questions should test whether learners can apply concepts to "
                "realistic scenarios and make appropriate decisions."
            ),
            "analysis": (
                "Questions should test whether learners can analyse complex "
                "situations, compare approaches, and evaluate outcomes."
            ),
        }
        diff_text = difficulty_guidance.get(options.quiz_difficulty, difficulty_guidance["application"])

        q_types = ", ".join(options.quiz_question_types)

        system_prompt = (
            "You are an expert assessment designer. Create high-quality "
            "training assessment questions. Respond with valid JSON only."
        )

        user_content = f"""Create a {options.quiz_question_count}-question assessment for:

TRAINING: {curriculum.title}
COMPANY: {company}
DIFFICULTY: {options.quiz_difficulty}
GUIDANCE: {diff_text}
QUESTION TYPES: {q_types}

CURRICULUM CONTENT:
{chr(10).join(module_summaries)}

Return:
{{
    "quiz_title": "Assessment: {curriculum.title}",
    "instructions": "Instructions for the learner taking the quiz",
    "passing_score": 80,
    "questions": [
        {{
            "number": 1,
            "type": "multiple_choice",
            "question": "Question text?",
            "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
            "correct_answer": "B",
            "explanation": "Why B is correct and the others are not",
            "module_reference": "Module title this question relates to",
            "difficulty": "{options.quiz_difficulty}"
        }},
        {{
            "number": 2,
            "type": "true_false",
            "question": "Statement to evaluate as true or false.",
            "options": ["True", "False"],
            "correct_answer": "True",
            "explanation": "Why this is true",
            "module_reference": "Module title",
            "difficulty": "{options.quiz_difficulty}"
        }}
    ]
}}

GUIDELINES:
1. Distribute questions evenly across all modules.
2. Mix question types as requested: {q_types}.
3. For multiple choice: always provide exactly 4 options (A-D).
4. For true/false: make statements nuanced enough to require understanding.
5. Every question must have a clear, unambiguous correct answer.
6. Explanations should teach -- explain WHY the answer is correct.
7. Avoid trick questions; test genuine understanding.
8. All {options.quiz_question_count} questions must be unique and substantive.

Respond with valid JSON only. No markdown fences."""

        raw = self._call_claude(system_prompt, user_content, max_tokens=4096)
        return self._parse_json_response(raw)

    def _build_quiz_document_content(
        self,
        quiz_data: dict,
        curriculum: ParsedCurriculum,
        show_answers: bool = False,
    ) -> dict:
        """Convert quiz data into a document content dict for the document generator.

        Args:
            quiz_data: The raw quiz data from Claude.
            curriculum: The parsed curriculum.
            show_answers: If True, includes answers and explanations (answer key).
        """
        company = self.brand_config.get("company_name", "Our Company")
        doc_title = quiz_data.get("quiz_title", f"Assessment: {curriculum.title}")
        if show_answers:
            doc_title = f"Answer Key - {doc_title}"

        questions_formatted: list[dict] = []
        for q in quiz_data.get("questions", []):
            q_entry: dict[str, Any] = {
                "number": q.get("number", 0),
                "type": q.get("type", "multiple_choice"),
                "question": q.get("question", ""),
                "options": q.get("options", []),
                "module_reference": q.get("module_reference", ""),
            }
            if show_answers:
                q_entry["correct_answer"] = q.get("correct_answer", "")
                q_entry["explanation"] = q.get("explanation", "")

            questions_formatted.append(q_entry)

        content: dict[str, Any] = {
            "title": doc_title,
            "subtitle": f"{company} | Training Assessment",
            "date": datetime.now().strftime("%B %d, %Y"),
            "instructions": quiz_data.get(
                "instructions",
                "Read each question carefully and select the best answer.",
            ),
            "passing_score": quiz_data.get("passing_score", 80),
            "total_questions": len(questions_formatted),
            "questions": questions_formatted,
        }

        if show_answers:
            content["answer_key_note"] = (
                "CONFIDENTIAL - FOR FACILITATOR USE ONLY. "
                "Do not distribute to participants."
            )

        return content

    # ==================================================================
    # Microlearning helpers
    # ==================================================================

    def _build_microlearning_content(
        self,
        module: TrainingModule,
        mod_idx: int,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> dict:
        """Build content for a single microlearning module.

        Uses Claude to distill a full training module into a focused
        mini-lesson that can be consumed in the target duration.
        """
        company = self.brand_config.get("company_name", "Our Company")
        al_ctx = AUDIENCE_LEVEL_CONTEXT.get(
            options.audience_level, AUDIENCE_LEVEL_CONTEXT["intermediate"],
        )
        target_minutes = options.module_duration_minutes

        topic_texts: list[str] = []
        for topic in module.topics:
            t = topic.get("title", "")
            c = topic.get("content", "")
            kp = topic.get("key_points", [])
            text = f"{t}: {c}" if c else t
            if kp:
                text += f" | Key points: {'; '.join(kp)}"
            topic_texts.append(text)

        system_prompt = (
            "You are a microlearning designer. You create focused, bite-sized "
            "learning modules. Respond with valid JSON only."
        )

        user_content = f"""Create a {target_minutes}-minute microlearning module based on:

MODULE: {module.title} (from "{curriculum.title}")
COMPANY: {company}
AUDIENCE: {options.audience_level} ({al_ctx['vocabulary']})
TARGET DURATION: {target_minutes} minutes

SOURCE CONTENT:
{chr(10).join(topic_texts)}

OBJECTIVES:
{chr(10).join(f'- {o}' for o in module.objectives)}

Return:
{{
    "title": "Microlearning: {module.title}",
    "learning_goal": "One clear, specific learning goal for this micro-lesson",
    "estimated_minutes": {target_minutes},
    "hook": "An engaging opening question or scenario (1-2 sentences)",
    "core_content": [
        {{
            "heading": "Key concept heading",
            "explanation": "Clear, concise explanation (2-3 sentences max)",
            "example": "A concrete example or scenario"
        }}
    ],
    "quick_check": {{
        "question": "A single question to check understanding",
        "answer": "The correct answer with brief explanation"
    }},
    "action_item": "One specific thing the learner should do or try after this module",
    "key_takeaway": "The single most important thing to remember"
}}

GUIDELINES:
1. Focus on ONE key concept from the module (the most impactful one).
2. Keep total reading time under {target_minutes} minutes (~{target_minutes * 150} words).
3. Use simple, direct language appropriate for {options.audience_level} learners.
4. The hook should immediately engage and create relevance.
5. Core content should be scannable and actionable.
6. The quick check should be answerable from the content provided.

Respond with valid JSON only. No markdown fences."""

        try:
            raw = self._call_claude(system_prompt, user_content, max_tokens=2000)
            micro_data = self._parse_json_response(raw)
        except Exception as exc:
            logger.warning("Claude microlearning generation failed, using fallback: %s", exc)
            micro_data = {
                "title": f"Microlearning: {module.title}",
                "learning_goal": module.objectives[0] if module.objectives else f"Understand {module.title}",
                "estimated_minutes": target_minutes,
                "hook": f"Did you know that {module.title.lower()} is essential for success in your role?",
                "core_content": [
                    {
                        "heading": t.get("title", "Key Concept"),
                        "explanation": t.get("content", "")[:200],
                        "example": "See the full training for detailed examples.",
                    }
                    for t in module.topics[:2]
                ],
                "quick_check": {
                    "question": f"What is the most important aspect of {module.title}?",
                    "answer": module.key_takeaways[0] if module.key_takeaways else "Review the module content.",
                },
                "action_item": f"Apply one concept from {module.title} in your work today.",
                "key_takeaway": module.key_takeaways[0] if module.key_takeaways else module.title,
            }

        return micro_data

    # ==================================================================
    # Agent script helpers
    # ==================================================================

    def _build_agent_script_document(
        self,
        script_data: dict,
        curriculum: ParsedCurriculum,
        options: PipelineOptions,
    ) -> dict:
        """Convert the raw agent script JSON from Claude into a document content dict."""
        company = self.brand_config.get("company_name", "Our Company")

        opening = script_data.get("opening", {})
        closing = script_data.get("closing", {})

        # Format discovery questions
        discovery_formatted: list[str] = []
        for dq in script_data.get("discovery_questions", []):
            q = dq.get("question", "")
            purpose = dq.get("purpose", "")
            follow_up = dq.get("follow_up", "")
            entry = f"Q: {q}"
            if purpose:
                entry += f"\n  Purpose: {purpose}"
            if follow_up:
                entry += f"\n  Follow-up: {follow_up}"
            discovery_formatted.append(entry)

        # Format value propositions
        vp_formatted: list[str] = []
        for vp in script_data.get("value_propositions", []):
            feature = vp.get("feature", "")
            benefit = vp.get("benefit_statement", "")
            proof = vp.get("proof_point", "")
            transition = vp.get("transition", "")
            entry = f"Feature: {feature}\n  Benefit: {benefit}"
            if proof:
                entry += f"\n  Proof point: {proof}"
            if transition:
                entry += f"\n  Transition: {transition}"
            vp_formatted.append(entry)

        # Format objection handling
        objection_table: list[dict] = []
        for obj in script_data.get("objection_handling", []):
            objection_table.append({
                "objection": obj.get("objection", ""),
                "response": obj.get("response", ""),
                "technique": obj.get("technique", ""),
            })

        content: dict[str, Any] = {
            "title": script_data.get("script_title", f"Agent Script: {curriculum.title}"),
            "subtitle": f"{company} | Sales / Service Script",
            "date": datetime.now().strftime("%B %d, %Y"),
            "version": "1.0",
            "overview": (
                f"This script supports agents handling calls related to "
                f"{curriculum.title}. Use it as a guide -- not a word-for-word "
                f"script. Adapt your language to the customer's tone and needs."
            ),
            "sections": [
                {
                    "heading": "Opening & Greeting",
                    "content": (
                        f"Greeting: {opening.get('greeting', 'Hello, thank you for calling [COMPANY].')}\n\n"
                        f"Introduction: {opening.get('introduction', 'My name is [AGENT_NAME].')}\n\n"
                        f"Rapport: {opening.get('rapport_building', 'How are you doing today?')}"
                    ),
                },
                {
                    "heading": "Discovery Questions",
                    "content": "\n\n".join(discovery_formatted) if discovery_formatted else "Ask open-ended questions to understand the customer's needs.",
                },
                {
                    "heading": "Value Propositions",
                    "content": "\n\n".join(vp_formatted) if vp_formatted else "Present product features and benefits.",
                },
                {
                    "heading": "Objection Handling",
                    "content": self._format_objection_table_text(objection_table),
                },
                {
                    "heading": "Closing & Next Steps",
                    "content": (
                        f"Trial close: {closing.get('trial_close', 'Does this sound like it could work for you?')}\n\n"
                        f"Commitment: {closing.get('commitment_ask', 'Would you like to proceed?')}\n\n"
                        f"Next steps: {closing.get('next_steps', 'I will send you a follow-up email with details.')}\n\n"
                        f"Wrap-up: {closing.get('wrap_up', 'Thank you for your time. Have a great day!')}"
                    ),
                },
                {
                    "heading": "Compliance Disclosures",
                    "content": "\n".join(
                        f"- {d}" for d in script_data.get("compliance_disclosures", ["Standard disclosures apply."])
                    ),
                },
            ],
            "tips": script_data.get("tips", []),
        }

        return content

    @staticmethod
    def _format_objection_table_text(objection_table: list[dict]) -> str:
        """Format objection handling data as a readable text table."""
        if not objection_table:
            return "Refer to training materials for common objection handling approaches."

        lines: list[str] = []
        lines.append(f"{'OBJECTION':<40} | {'RESPONSE':<60} | {'TECHNIQUE':<20}")
        lines.append("-" * 124)
        for row in objection_table:
            objection = row.get("objection", "")[:38]
            response = row.get("response", "")[:58]
            technique = row.get("technique", "")[:18]
            lines.append(f"{objection:<40} | {response:<60} | {technique:<20}")

        return "\n".join(lines)

    # ==================================================================
    # Utility helpers
    # ==================================================================

    def _collect_all_objectives(self, curriculum: ParsedCurriculum) -> list[str]:
        """Collect all learning objectives from all modules into a single list."""
        objectives: list[str] = []
        for module in curriculum.modules:
            objectives.extend(module.objectives)
        return objectives

    def _parse_json_response(self, raw: str) -> Any:
        """Parse a JSON response from Claude, handling markdown code fences.

        Claude sometimes wraps JSON in ```json ... ``` fences.  This method
        strips those before parsing.

        Args:
            raw: Raw string response from Claude.

        Returns:
            Parsed JSON (usually a dict or list).

        Raises:
            ValueError: If the response cannot be parsed as JSON.
        """
        text = raw.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line if it's a closing fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        # Also handle case where there might be text before/after JSON
        # Try to find JSON object or array boundaries
        if not text.startswith(("{", "[")):
            # Look for the first { or [
            obj_start = text.find("{")
            arr_start = text.find("[")
            if obj_start >= 0 and (arr_start < 0 or obj_start < arr_start):
                text = text[obj_start:]
            elif arr_start >= 0:
                text = text[arr_start:]

        # Trim trailing non-JSON content
        if text.startswith("{"):
            # Find matching closing brace
            depth = 0
            for i, ch in enumerate(text):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        text = text[: i + 1]
                        break
        elif text.startswith("["):
            depth = 0
            for i, ch in enumerate(text):
                if ch == "[":
                    depth += 1
                elif ch == "]":
                    depth -= 1
                    if depth == 0:
                        text = text[: i + 1]
                        break

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse JSON from Claude response: %s", exc)
            logger.debug("Raw response (first 500 chars): %s", raw[:500])
            raise ValueError(
                f"Could not parse Claude response as JSON: {exc}"
            ) from exc

    def _call_claude(
        self,
        system_prompt: str,
        user_content: str,
        max_tokens: int = 4096,
    ) -> str:
        """Make a single request to the Anthropic messages API.

        If a research brief was built during ``process_curriculum()``,
        its context is automatically appended to the system prompt so
        Claude can reference existing brand content and voice guidance.

        Args:
            system_prompt: The system instruction for Claude.
            user_content: The user message content.
            max_tokens: Maximum tokens in the response.

        Returns:
            The text content of Claude's response.

        Raises:
            Exception: Propagated from the Anthropic SDK on API errors.
        """
        # Inject research context if available
        if self._research_context:
            system_prompt = system_prompt + "\n\n" + self._research_context

        logger.debug(
            "Calling Claude (%s) with %d char prompt, max_tokens=%d",
            CLAUDE_MODEL,
            len(user_content),
            max_tokens,
        )
        start = time.time()

        message = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_content},
            ],
        )

        elapsed = round(time.time() - start, 2)
        response_text = message.content[0].text
        logger.debug(
            "Claude responded in %.2fs (%d chars, stop_reason=%s)",
            elapsed,
            len(response_text),
            message.stop_reason,
        )
        return response_text
