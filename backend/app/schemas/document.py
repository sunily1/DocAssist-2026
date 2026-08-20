"""인수인계용: 문서/분석/용어 관련 스키마."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.document import DocStatus


class DocumentBase(BaseModel):
    """문서 공통 필드."""

    title: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    status: Optional[DocStatus] = DocStatus.QUEUED
    meta_data: Optional[Dict[str, Any]] = None


class DocumentCreate(DocumentBase):
    """문서 생성 스키마."""

    title: str
    original_filename: str
    s3_key: str
    file_type: str
    file_size: int


class DocumentUpdate(BaseModel):
    """문서 수정 스키마."""

    title: Optional[str] = None
    status: Optional[DocStatus] = None
    meta_data: Optional[Dict[str, Any]] = None


class DocumentInDBBase(DocumentBase):
    """DB 공통 필드 포함 스키마."""

    id: UUID
    user_id: UUID
    original_filename: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentRead(DocumentInDBBase):
    """문서 조회 응답 스키마."""

    pass


class DocumentAnalysisRead(BaseModel):
    """문서 분석 결과 응답 스키마."""

    id: UUID
    document_id: UUID
    summary: Optional[str] = None
    paragraphs: List[Dict[str, Any]] = Field(default_factory=list)
    rules: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class GlossaryTermRead(BaseModel):
    """용어 응답 스키마."""

    id: UUID
    document_id: Optional[UUID] = None
    term: str
    definition: str
    tags: List[str] = Field(default_factory=list)
    complexity_level: int = 1
    is_pinned: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class GlossaryEntryRead(BaseModel):
    """사용자 용어집 목록에서 사용하는 문서 맥락 포함 응답."""

    id: UUID
    document_id: UUID
    document_title: str
    term: str
    definition: str
    evidence: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    primary_tag: str = "general"
    frequency: int = 1
    is_pinned: bool = False
    created_at: datetime


class GlossaryPinUpdate(BaseModel):
    is_pinned: bool


class DocumentWithAnalysis(DocumentRead):
    """문서 + 분석/용어 확장 응답."""

    analysis: Optional[DocumentAnalysisRead] = None
    glossary_terms: List[GlossaryTermRead] = Field(default_factory=list)


class TextConvertRequest(BaseModel):
    """텍스트 직접 변환 요청."""

    text: str = Field(..., min_length=1)
    intensity: str = "easy"
    title: Optional[str] = "직접 입력 문서"


class TextConvertResponse(BaseModel):
    """텍스트 직접 변환 응답."""

    intensity: str
    intensity_label: str
    summary: str = ""
    converted_text: str = ""
    paragraphs: List[Dict[str, Any]] = Field(default_factory=list)
    rules: List[Dict[str, Any]] = Field(default_factory=list)
    terms: List[Dict[str, Any]] = Field(default_factory=list)


class TextDocxDownloadRequest(TextConvertRequest):
    """직접 변환 결과 DOCX 다운로드 요청."""

    mode: str = "summary"


class DocumentReprocessRequest(BaseModel):
    """저장된 문서를 다른 쉬운말 강도로 다시 변환하는 요청."""

    intensity: str = "easy"


class DocumentAnnotationRead(BaseModel):
    """실제 파일 페이지 위에 표시할 변경 표현 좌표."""

    id: str
    segment: int = 0
    page: int
    page_width: float
    page_height: float
    x: float
    y: float
    width: float
    height: float
    original: str
    easy: str
    definition: str = ""
    approximate: bool = False


class DocumentAnnotationsRead(BaseModel):
    mode: str
    annotations: List[DocumentAnnotationRead] = Field(default_factory=list)
