import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Enum, DateTime, ForeignKey, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from apps.api.db.session import Base

class IssueSourceEnum(str, enum.Enum):
    GITHUB = "github"
    JIRA = "jira"
    MANUAL = "manual"

class AnalysisStatusEnum(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    NEEDS_INPUT = "needs_input"
    COMPLETED = "completed"
    FAILED = "failed"

class Issue(Base):
    __tablename__ = "issues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(Enum(IssueSourceEnum), nullable=False)
    source_id = Column(String(255), nullable=True)
    repository_url = Column(String(512), nullable=True)
    title = Column(String(512), nullable=False)
    body = Column(Text, nullable=False)
    raw_logs = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    runs = relationship("AnalysisRun", back_populates="issue", cascade="all, delete-orphan")

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(AnalysisStatusEnum), default=AnalysisStatusEnum.QUEUED, nullable=False)
    overall_confidence = Column(Numeric(3, 2), nullable=True)
    groq_primary_model = Column(String(128), nullable=False)
    groq_fast_model = Column(String(128), nullable=False)
    groq_code_model = Column(String(128), nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    issue = relationship("Issue", back_populates="runs")
    entities = relationship("ExtractedEntity", back_populates="run", uselist=False, cascade="all, delete-orphan")
    repro_steps = relationship("ReproStep", back_populates="run", cascade="all, delete-orphan")
    clarifications = relationship("Clarification", back_populates="run", cascade="all, delete-orphan")
    test_artifacts = relationship("TestArtifact", back_populates="run", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="run", uselist=False, cascade="all, delete-orphan")

class ExtractedEntity(Base):
    __tablename__ = "extracted_entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False)
    facts = Column(JSONB, nullable=False, default=dict)
    inferred_assumptions = Column(JSONB, nullable=False, default=list)
    unknowns = Column(JSONB, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    run = relationship("AnalysisRun", back_populates="entities")

class ReproStep(Base):
    __tablename__ = "repro_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False)
    step_order = Column(Integer, nullable=False)
    action = Column(Text, nullable=False)
    expected_outcome = Column(Text, nullable=True)
    confidence = Column(Numeric(3, 2), nullable=True)
    sandbox_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    run = relationship("AnalysisRun", back_populates="repro_steps")

class Clarification(Base):
    __tablename__ = "clarifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(64), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(JSONB, default=list)
    answer = Column(Text, nullable=True)
    answered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    run = relationship("AnalysisRun", back_populates="clarifications")

class TestArtifact(Base):
    __tablename__ = "test_artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False)
    test_type = Column(String(64), nullable=False)
    framework = Column(String(64), nullable=False)
    file_path = Column(String(512), nullable=False)
    code_content = Column(Text, nullable=False)
    execution_passed = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    run = relationship("AnalysisRun", back_populates="test_artifacts")

class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False)
    markdown_content = Column(Text, nullable=False)
    json_content = Column(JSONB, nullable=False)
    qa_checklist = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    run = relationship("AnalysisRun", back_populates="report")
