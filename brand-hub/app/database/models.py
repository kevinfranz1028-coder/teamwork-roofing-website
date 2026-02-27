"""
Brand Intelligence Content Hub - Database Models

SQLAlchemy ORM models for managing brand assets, templates,
generated content, and batch processing jobs.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# ---------------------------------------------------------------------------
# Engine / Session / Base
# ---------------------------------------------------------------------------

DATABASE_URL = "sqlite:///data/brand_hub.db"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class BrandProfile(Base):
    """Named brand profiles — each contains a full brand configuration."""

    __tablename__ = "brand_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False)  # Only one active at a time
    config_json = Column(Text, nullable=True)   # Full brand_config stored as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assets = relationship("BrandAsset", back_populates="profile")

    def __repr__(self):
        return f"<BrandProfile id={self.id} name='{self.name}' active={self.is_active}>"


class BrandAsset(Base):
    """Uploaded brand assets such as logos, fonts, color palettes, and collateral."""

    __tablename__ = "brand_assets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)  # logo / font / color / template / collateral / sample
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(Text, nullable=True)
    tags = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    brand_profile_id = Column(Integer, ForeignKey("brand_profiles.id"), nullable=True)

    # Relationships
    profile = relationship("BrandProfile", back_populates="assets")

    def __repr__(self):
        return f"<BrandAsset id={self.id} filename='{self.filename}' type='{self.asset_type}'>"


class BrandConfig(Base):
    """Key-value configuration store for brand-level settings."""

    __tablename__ = "brand_configs"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String, unique=True, nullable=False)
    config_value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<BrandConfig key='{self.config_key}'>"


class Template(Base):
    """Reusable document templates with frozen and editable zones."""

    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    template_type = Column(String, nullable=False)  # pptx / docx / brand_guidelines
    file_path = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    frozen_zones_json = Column(Text, nullable=True)
    editable_zones_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usage_count = Column(Integer, default=0)

    # Relationships
    generated_contents = relationship("GeneratedContent", back_populates="template")

    def __repr__(self):
        return f"<Template id={self.id} name='{self.name}' type='{self.template_type}'>"


class GeneratedContent(Base):
    """Records of AI-generated content outputs."""

    __tablename__ = "generated_content"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True)
    input_summary = Column(Text, nullable=True)
    output_path = Column(String, nullable=True)
    format = Column(String, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    generation_time_seconds = Column(Float, nullable=True)
    user_rating = Column(Integer, nullable=True)
    feedback_notes = Column(Text, nullable=True)
    # --- Enhancement fields ---
    status = Column(String, default="draft")  # draft / review / approved / published
    version = Column(Integer, default=1)
    knowledge_mode = Column(String, nullable=True)  # grounded / enhanced / research
    confidence_score = Column(Float, nullable=True)  # 0.0 - 1.0
    sources_json = Column(Text, nullable=True)  # JSON array of source references

    # Relationships
    template = relationship("Template", back_populates="generated_contents")
    library_items = relationship("ContentLibraryItem", back_populates="generated_content")

    def __repr__(self):
        return f"<GeneratedContent id={self.id} title='{self.title}' type='{self.content_type}'>"


class ContentLibraryItem(Base):
    """Curated library of approved generated content for browsing and reuse."""

    __tablename__ = "content_library_items"

    id = Column(Integer, primary_key=True, index=True)
    generated_content_id = Column(Integer, ForeignKey("generated_content.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(String, nullable=True)
    category = Column(String, nullable=True)
    is_approved = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    # --- Ingestion fields ---
    source_type = Column(String, nullable=True)       # file_upload / url / manual / generated
    source_path = Column(String, nullable=True)       # File path or URL
    ingested_at = Column(DateTime, nullable=True)
    content_text = Column(Text, nullable=True)         # Extracted text (for search)
    auto_classified = Column(Boolean, default=False)   # Was this auto-classified?
    classification_confidence = Column(Float, nullable=True)
    brand_profile_id = Column(Integer, ForeignKey("brand_profiles.id"), nullable=True)

    # Relationships
    generated_content = relationship("GeneratedContent", back_populates="library_items")

    def __repr__(self):
        return f"<ContentLibraryItem id={self.id} title='{self.title}' approved={self.is_approved}>"


class PromptTemplate(Base):
    """Versioned prompt templates for different content generation tasks."""

    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    system_prompt = Column(Text, nullable=True)
    user_prompt_template = Column(Text, nullable=True)
    variables_json = Column(Text, nullable=True)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<PromptTemplate id={self.id} name='{self.name}' v{self.version}>"


class BatchJob(Base):
    """Batch content-generation jobs for processing multiple items at once."""

    __tablename__ = "batch_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending / running / completed / failed
    items_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    results_json = Column(Text, nullable=True)

    def __repr__(self):
        return f"<BatchJob id={self.id} name='{self.name}' status='{self.status}'>"


class AgentRun(Base):
    """Audit record for a multi-agent orchestration run."""

    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(String, nullable=False, index=True)
    request = Column(Text, nullable=False)
    content_type = Column(String, default="")
    doc_type = Column(String, default="")
    title = Column(String, default="")
    status = Column(String, default="running")  # running / completed / failed
    output_file = Column(String, default="")
    steps_json = Column(Text, default="{}")
    compliance_score = Column(Float, default=0.0)
    compliance_passed = Column(Boolean, default=False)
    total_cost_usd = Column(Float, default=0.0)
    retry_count = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, default="")

    def __repr__(self):
        return f"<AgentRun id={self.id} plan='{self.plan_id[:8]}' status='{self.status}'>"


class CopilotAuditLog(Base):
    """Audit trail for every Copilot action — tool calls, confirmations, and generations."""

    __tablename__ = "copilot_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    session_id = Column(String, nullable=True, index=True)
    user_message = Column(Text, nullable=True)
    action_type = Column(String, nullable=False)  # tool_call / confirmation / generation / error
    tool_name = Column(String, nullable=True)
    tool_input_json = Column(Text, nullable=True)
    tool_result_summary = Column(Text, nullable=True)
    knowledge_mode = Column(String, nullable=True)  # grounded / enhanced / research
    sources_used_json = Column(Text, nullable=True)  # JSON array of sources
    confirmation_status = Column(String, nullable=True)  # pending / confirmed / cancelled / modified
    generated_file_path = Column(String, nullable=True)
    api_tokens_used = Column(Integer, nullable=True)
    api_cost_estimate = Column(Float, nullable=True)

    def __repr__(self):
        return f"<CopilotAuditLog id={self.id} action='{self.action_type}' tool='{self.tool_name}'>"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def init_db():
    """Create all database tables. Safe to call multiple times."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Return a new SQLAlchemy session. Caller is responsible for closing it."""
    return SessionLocal()
