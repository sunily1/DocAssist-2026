import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, TYPE_CHECKING

from sqlalchemy import String, Integer, BigInteger, Text, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.session import Base

if TYPE_CHECKING:
    from .user import User

# 열거형
class DocStatus(str, Enum):
    """문서 처리 상태."""
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"

class JobStatus(str, Enum):
    """문서 처리 작업 상태."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# 모델
class Document(Base):
    """업로드 문서 메타데이터."""
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    status: Mapped[DocStatus] = mapped_column(SAEnum(DocStatus), default=DocStatus.QUEUED)
    meta_data: Mapped[dict] = mapped_column(JSONB, default=lambda: {})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # 관계
    user: Mapped["User"] = relationship("User", back_populates="documents")
    jobs: Mapped[List["DocumentJob"]] = relationship("DocumentJob", back_populates="document", cascade="all, delete-orphan")
    analysis: Mapped[Optional["DocumentAnalysis"]] = relationship("DocumentAnalysis", back_populates="document", uselist=False, cascade="all, delete-orphan")
    glossary_terms: Mapped[List["GlossaryTerm"]] = relationship("GlossaryTerm", back_populates="document", cascade="all, delete-orphan")
    embeddings: Mapped[List["DocumentEmbedding"]] = relationship("DocumentEmbedding", back_populates="document", cascade="all, delete-orphan")


class DocumentJob(Base):
    """문서 처리 작업(비동기 분석) 기록."""
    __tablename__ = "document_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[JobStatus] = mapped_column(SAEnum(JobStatus), default=JobStatus.PENDING)
    worker_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    result_data: Mapped[dict] = mapped_column(JSONB, default=lambda: {})
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship("Document", back_populates="jobs")


class DocumentAnalysis(Base):
    """문서 분석 결과(요약/문단/규칙)."""
    __tablename__ = "document_analysis"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    paragraphs: Mapped[List[dict]] = mapped_column(JSONB, default=list) # 예: [{ "original": "...", "easy": "...", "bullets": ["..."] }]
    rules: Mapped[List[dict]] = mapped_column(JSONB, default=list) # 예: [{ "title": "...", "desc": "...", "source": "..." }]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship("Document", back_populates="analysis")


class GlossaryTerm(Base):
    """문서에서 추출된 용어/정의."""
    __tablename__ = "glossary_terms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=True)
    term: Mapped[str] = mapped_column(String(100), nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list) # 태그 목록 (JSONB 배열 사용)
    complexity_level: Mapped[int] = mapped_column(Integer, default=1)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship("Document", back_populates="glossary_terms")


class DocumentEmbedding(Base):
    """RAG 검색용 문서 임베딩 청크."""
    __tablename__ = "document_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Any] = mapped_column(Vector(1536)) # OpenAI Ada-002 / small-3 차원 (1536)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship("Document", back_populates="embeddings")
