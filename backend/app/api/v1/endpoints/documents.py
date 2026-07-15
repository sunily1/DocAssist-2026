import io
import os
from types import SimpleNamespace
from typing import Any, List
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import SessionLocal
from app.models.user import User
from app.models.system import SystemLog
from app.schemas.document import (
    DocumentRead,
    DocumentUpdate,
    DocumentWithAnalysis,
    GlossaryEntryRead,
    GlossaryPinUpdate,
    TextConvertRequest,
    TextConvertResponse,
    TextDocxDownloadRequest,
)
from app.services import document_service
from app.services import glossary_service
from app.services.document_processor import processor

router = APIRouter()


async def run_document_processing(document_id: UUID):
    """백그라운드에서 문서 분석 파이프라인 실행."""
    async with SessionLocal() as db:
        await document_service.process_document_background(db, document_id)


async def _get_doc_or_404(db: AsyncSession, document_id: UUID, user: User):
    """문서 소유권 확인 후 조회, 없으면 404."""
    doc = await document_service.get_authorized(db, document_id, user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def _docx_response(content: bytes, filename: str) -> StreamingResponse:
    encoded = quote(filename)
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"}
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )


def _media_type_for_file_type(file_type: str | None) -> str:
    value = str(file_type or "").upper()
    if value == "PDF":
        return "application/pdf"
    if value == "DOCX":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if value == "TXT":
        return "text/plain; charset=utf-8"
    return "application/octet-stream"


@router.post("/convert-text", response_model=TextConvertResponse)
async def convert_text(
    payload: TextConvertRequest,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """직접 입력한 텍스트를 업무용 쉬운말로 변환."""
    result = await processor.analyze_document(payload.text, intensity=payload.intensity)
    db.add(
        SystemLog(
            level="METRIC",
            message="text_convert",
            context={"user_id": str(current_user.id), "intensity": payload.intensity},
        )
    )
    await db.commit()
    return result


@router.post("/convert-text/download")
async def download_converted_text(
    payload: TextDocxDownloadRequest,
    current_user: User = Depends(deps.get_current_user),
) -> StreamingResponse:
    """직접 입력 텍스트 변환 결과를 DOCX로 다운로드."""
    result = await processor.analyze_document(payload.text, intensity=payload.intensity)
    document = SimpleNamespace(
        title=payload.title or "직접 입력 문서",
        analysis=SimpleNamespace(
            summary=result.get("summary", ""),
            paragraphs=result.get("paragraphs", []),
        ),
    )
    content = document_service.build_docx_bytes(document, mode=payload.mode)
    return _docx_response(content, "docassist_text_result.docx")


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    intensity: str = Form("easy"),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """문서 업로드: 파일 저장 후 변환/분석 작업을 백그라운드로 실행."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file name provided.")

    document = await document_service.create_with_file(db, current_user.id, file, intensity=intensity)
    background_tasks.add_task(run_document_processing, document.id)

    return document


@router.get("/", response_model=List[DocumentRead])
async def read_documents(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """현재 사용자 문서 목록 조회."""
    documents = await document_service.get_multi_by_user(db, current_user.id, skip=skip, limit=limit)
    return documents


@router.get("/glossary/terms", response_model=List[GlossaryEntryRead])
async def read_glossary_terms(
    document_id: UUID | None = Query(None),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """현재 사용자의 문서에서 추출된 용어를 문서 맥락과 함께 조회합니다."""
    return await glossary_service.list_for_user(db, current_user.id, document_id=document_id)


@router.patch("/glossary/terms/{term_id}/pin", response_model=GlossaryEntryRead)
async def update_glossary_pin(
    term_id: UUID,
    payload: GlossaryPinUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """현재 사용자가 소유한 문서 용어의 핀 상태를 저장합니다."""
    term = await glossary_service.set_pinned(db, current_user.id, term_id, payload.is_pinned)
    if not term:
        raise HTTPException(status_code=404, detail="Glossary term not found")
    return term


@router.get("/{document_id}", response_model=DocumentWithAnalysis)
async def read_document(
    document_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """문서 상세 조회(분석/용어 포함)."""
    return await _get_doc_or_404(db, document_id, current_user)


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    mode: str = Query("summary", pattern="^(converted|comparison|summary)$"),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> StreamingResponse:
    """저장된 문서 변환 결과를 DOCX로 다운로드."""
    document = await _get_doc_or_404(db, document_id, current_user)
    content = document_service.build_docx_bytes(document, mode=mode)
    safe_title = (document.title or "document").rsplit(".", 1)[0]
    return _docx_response(content, f"{safe_title}_docassist.docx")


@router.get("/{document_id}/original")
async def read_original_document(
    document_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> StreamingResponse:
    """업로드한 원본 파일을 그대로 반환합니다."""
    document = await _get_doc_or_404(db, document_id, current_user)
    if not document.s3_key or not os.path.exists(document.s3_key):
        raise HTTPException(status_code=404, detail="Original file not found")

    filename = document.original_filename or document.title or "document"
    encoded = quote(filename)
    disposition = "inline" if str(document.file_type or "").upper() in {"PDF", "TXT"} else "attachment"
    headers = {"Content-Disposition": f"{disposition}; filename*=UTF-8''{encoded}"}
    return StreamingResponse(
        open(document.s3_key, "rb"),
        media_type=_media_type_for_file_type(document.file_type),
        headers=headers,
    )


@router.get("/{document_id}/converted-original")
async def read_converted_original_document(
    document_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> StreamingResponse:
    """원본 DOCX 서식을 유지하면서 쉬운말 표현만 치환한 파일을 반환합니다."""
    document = await _get_doc_or_404(db, document_id, current_user)
    file_type = str(document.file_type or "").upper()
    if file_type == "PDF":
        content = document_service.build_layout_pdf_bytes(document)
        media_type = "application/pdf"
        extension = "pdf"
    elif file_type == "TXT":
        paragraphs = document.analysis.paragraphs if document.analysis else []
        converted_text = "\n\n".join(
            str(paragraph.get("easy") or paragraph.get("original") or "").strip()
            for paragraph in paragraphs
            if str(paragraph.get("easy") or paragraph.get("original") or "").strip()
        )
        content = converted_text.encode("utf-8")
        media_type = "text/plain; charset=utf-8"
        extension = "txt"
    else:
        content = document_service.build_converted_original_docx_bytes(document)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        extension = "docx"

    safe_title = (document.title or "document").rsplit(".", 1)[0]
    encoded = quote(f"{safe_title}_easy_layout.{extension}")
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{encoded}"},
    )


@router.get("/{document_id}/layout-pdf")
async def download_layout_pdf(
    document_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> StreamingResponse:
    """원본 페이지 배치를 유지한 쉬운말 변환 PDF를 반환합니다."""
    document = await _get_doc_or_404(db, document_id, current_user)
    content = document_service.build_layout_pdf_bytes(document)
    safe_title = (document.title or "document").rsplit(".", 1)[0]
    encoded = quote(f"{safe_title}_layout_docassist.pdf")
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{encoded}"},
    )


@router.patch("/{document_id}", response_model=DocumentRead)
async def update_document(
    document_id: UUID,
    document_in: DocumentUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """문서 메타데이터 수정."""
    document = await _get_doc_or_404(db, document_id, current_user)
    document = await document_service.update(db, document, document_in)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> None:
    """문서 소프트 삭제."""
    await _get_doc_or_404(db, document_id, current_user)
    await document_service.remove(db, document_id)
    return
