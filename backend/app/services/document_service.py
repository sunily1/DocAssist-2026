import io
import logging
import os
import shutil
import uuid
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID
from xml.sax.saxutils import escape

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.document import (
    DocStatus,
    Document,
    DocumentAnalysis,
    DocumentEmbedding,
    DocumentJob,
    GlossaryTerm,
    JobStatus,
)
from app.schemas.document import DocumentUpdate
from app.services.document_processor import processor
from app.services.easy_converter import INTENSITY_LABELS, normalize_intensity

logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def get(db: AsyncSession, id: UUID) -> Optional[Document]:
    """문서 단건 조회(분석/용어집 관계 포함)."""
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.analysis), selectinload(Document.glossary_terms))
        .filter(Document.id == id, Document.deleted_at == None)
    )
    return result.scalars().first()


async def get_multi_by_user(
    db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100
) -> List[Document]:
    """사용자 기준 문서 목록 조회."""
    result = await db.execute(
        select(Document)
        .filter(Document.user_id == user_id, Document.deleted_at == None)
        .offset(skip)
        .limit(limit)
        .order_by(Document.created_at.desc())
    )
    return result.scalars().all()


async def get_authorized(db: AsyncSession, id: UUID, user_id: UUID) -> Optional[Document]:
    """사용자 소유 문서만 반환."""
    doc = await get(db, id)
    if doc and doc.user_id == user_id:
        return doc
    return None


async def create_with_file(
    db: AsyncSession, user_id: UUID, file: UploadFile, intensity: str = "easy"
) -> Document:
    """업로드 파일을 저장하고 문서 레코드를 생성."""
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="PDF, DOCX, TXT 파일만 업로드할 수 있습니다.")

    saved_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="빈 파일은 업로드할 수 없습니다.")

    try:
        extracted_text = processor.extract_text(file_path, file_ext.replace(".", "").upper())
    except Exception as exc:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="파일에서 읽을 수 있는 텍스트를 찾지 못했습니다.") from exc
    if not str(extracted_text or "").strip():
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="파일에서 읽을 수 있는 텍스트를 찾지 못했습니다.")

    normalized_intensity = normalize_intensity(intensity)

    db_obj = Document(
        user_id=user_id,
        title=file.filename,
        original_filename=file.filename,
        s3_key=file_path,
        file_type=file_ext.replace(".", "").upper(),
        file_size=file_size,
        status=DocStatus.QUEUED,
        meta_data={
            "intensity": normalized_intensity,
            "intensity_label": INTENSITY_LABELS[normalized_intensity],
        },
    )

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)

    return db_obj


async def update(
    db: AsyncSession, db_obj: Document, obj_in: DocumentUpdate
) -> Document:
    """문서 메타데이터 갱신."""
    update_data = obj_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def remove(db: AsyncSession, id: UUID) -> Optional[Document]:
    """문서 소프트 삭제."""
    result = await db.execute(select(Document).filter(Document.id == id))
    db_obj = result.scalars().first()
    if db_obj:
        db_obj.deleted_at = datetime.utcnow()
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
    return db_obj


async def process_document_background(db: AsyncSession, document_id: UUID):
    """문서 처리 백그라운드 태스크: 텍스트 추출 -> 청킹 -> 임베딩 -> 변환/분석."""
    result = await db.execute(select(Document).filter(Document.id == document_id))
    doc = result.scalars().first()

    if not doc:
        print(f"Document {document_id} not found for processing")
        return

    job = DocumentJob(
        document_id=document_id,
        status=JobStatus.RUNNING,
        started_at=datetime.utcnow(),
    )
    db.add(job)

    try:
        doc.status = DocStatus.PROCESSING
        db.add(doc)
        await db.commit()

        text = processor.extract_text(doc.s3_key, doc.file_type or "")
        if not text:
            raise Exception("No text extracted or empty file")

        chunks = processor.chunk_text(text)
        embeddings = await processor.create_embeddings(chunks)

        await db.execute(delete(DocumentEmbedding).where(DocumentEmbedding.document_id == document_id))

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if not embedding:
                continue
            db_emb = DocumentEmbedding(
                document_id=document_id,
                chunk_index=i,
                chunk_content=chunk,
                embedding=embedding,
            )
            db.add(db_emb)

        intensity = normalize_intensity((doc.meta_data or {}).get("intensity"))
        logger.info(f"Analyzing document {document_id} with intensity={intensity}")
        analysis_result = await processor.analyze_document(text, intensity=intensity)

        existing_terms = (
            await db.execute(
                select(GlossaryTerm.term, GlossaryTerm.is_pinned).where(
                    GlossaryTerm.document_id == document_id
                )
            )
        ).all()
        pinned_by_term = {
            str(term or "").strip().lower(): bool(is_pinned)
            for term, is_pinned in existing_terms
            if term
        }

        await db.execute(delete(DocumentAnalysis).where(DocumentAnalysis.document_id == document_id))
        await db.execute(delete(GlossaryTerm).where(GlossaryTerm.document_id == document_id))

        if analysis_result:
            db_analysis = DocumentAnalysis(
                document_id=document_id,
                summary=analysis_result.get("summary"),
                paragraphs=analysis_result.get("paragraphs", []),
                rules=analysis_result.get("rules", []),
            )
            db.add(db_analysis)

            for term in analysis_result.get("terms", []):
                if not term.get("term"):
                    continue
                db_term = GlossaryTerm(
                    document_id=document_id,
                    term=term.get("term"),
                    definition=term.get("definition") or term.get("replacement") or "",
                    tags=[],
                    complexity_level=1,
                    is_pinned=pinned_by_term.get(str(term.get("term") or "").strip().lower(), False),
                )
                db.add(db_term)

            doc.meta_data = {
                **(doc.meta_data or {}),
                "intensity": intensity,
                "intensity_label": INTENSITY_LABELS[intensity],
                "converted_text": analysis_result.get("converted_text", ""),
                "processed_at": datetime.utcnow().isoformat(),
            }

        doc.status = DocStatus.DONE
        job.status = JobStatus.COMPLETED
        job.finished_at = datetime.utcnow()
        job.result_data = {
            "chunks": len(chunks),
            "embeddings": len(embeddings),
            "analysis": bool(analysis_result),
        }

        db.add(doc)
        db.add(job)
        await db.commit()
        logger.info(f"Document {document_id} processed successfully.")

    except Exception as e:
        logger.error(f"Processing failed for document {document_id}: {e}")
        await db.rollback()

        doc.status = DocStatus.FAILED
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        job.finished_at = datetime.utcnow()

        db.add(doc)
        db.add(job)
        await db.commit()


def _docx_paragraph(text: Any, bold: bool = False) -> str:
    value = "" if text is None else str(text)
    escaped_lines = [escape(line) for line in value.splitlines()] or [""]
    run_props = "<w:rPr><w:b/></w:rPr>" if bold else ""
    body = ""
    for index, line in enumerate(escaped_lines):
        if index:
            body += "<w:br/>"
        body += f'<w:t xml:space="preserve">{line}</w:t>'
    return f"<w:p><w:r>{run_props}{body}</w:r></w:p>"


def _docx_package(paragraph_xml: list[str]) -> bytes:
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {''.join(paragraph_xml)}
    <w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>
  </w:body>
</w:document>"""
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", rels)
        docx.writestr("word/document.xml", document_xml)
    return buffer.getvalue()


def build_layout_pdf_bytes(document: Document) -> bytes:
    """원본 PDF 배치 위에 쉬운말 변환문을 적용한 PDF를 생성합니다."""
    if str(document.file_type or "").upper() != "PDF":
        raise HTTPException(status_code=400, detail="PDF 문서에서만 레이아웃 변환본을 만들 수 있습니다.")
    if not document.analysis:
        raise HTTPException(status_code=409, detail="문서 분석이 아직 완료되지 않았습니다.")
    if not document.s3_key or not os.path.exists(document.s3_key):
        raise HTTPException(status_code=404, detail="원본 PDF 파일을 찾을 수 없습니다.")

    return processor.build_layout_preserved_pdf(
        document.s3_key,
        document.analysis.paragraphs or [],
    )


def build_pdf_annotations(document: Document, mode: str = "converted") -> list[dict[str, Any]]:
    """원본 또는 쉬운말 PDF 위에 표시할 변경 표현 좌표를 생성합니다."""
    if str(document.file_type or "").upper() != "PDF":
        raise HTTPException(status_code=400, detail="PDF 문서에서만 좌표 하이라이트를 사용할 수 있습니다.")
    if not document.analysis:
        raise HTTPException(status_code=409, detail="문서 분석이 아직 완료되지 않았습니다.")
    if not document.s3_key or not os.path.exists(document.s3_key):
        raise HTTPException(status_code=404, detail="원본 PDF 파일을 찾을 수 없습니다.")

    normalized_mode = "original" if mode == "original" else "converted"
    converted_pdf = build_layout_pdf_bytes(document) if normalized_mode == "converted" else None
    return processor.build_pdf_change_annotations(
        document.s3_key,
        document.analysis.paragraphs or [],
        mode=normalized_mode,
        converted_pdf=converted_pdf,
    )


def _changed_term_pairs(document: Document) -> list[tuple[str, str]]:
    if not document.analysis:
        return []
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for paragraph in document.analysis.paragraphs or []:
        for term in paragraph.get("changed_terms", []) or []:
            source = str(term.get("from") or "").strip()
            target = str(term.get("to") or "").strip()
            if not source or not target or source == target:
                continue
            key = (source, target)
            if key in seen:
                continue
            seen.add(key)
            pairs.append(key)
    return pairs


def _replace_text_node_values(root: ET.Element, pairs: list[tuple[str, str]]) -> None:
    from app.services.easy_converter import replace_standalone_term

    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    for node in root.findall(".//w:t", namespace):
        if not node.text:
            continue
        value = node.text
        for source, target in pairs:
            value = replace_standalone_term(value, source, target)
        node.text = value


def build_converted_original_docx_bytes(document: Document) -> bytes:
    """원본 DOCX 구조를 유지하면서 분석된 쉬운말 표현만 치환한 DOCX를 만듭니다."""
    if str(document.file_type or "").upper() != "DOCX":
        raise HTTPException(status_code=400, detail="DOCX 문서에서만 원본 서식 쉬운말 보기를 만들 수 있습니다.")
    if not document.analysis:
        raise HTTPException(status_code=409, detail="문서 분석이 아직 완료되지 않았습니다.")
    if not document.s3_key or not os.path.exists(document.s3_key):
        raise HTTPException(status_code=404, detail="원본 DOCX 파일을 찾을 수 없습니다.")

    pairs = _changed_term_pairs(document)
    if not pairs:
        with open(document.s3_key, "rb") as source:
            return source.read()

    ET.register_namespace("w", "http://schemas.openxmlformats.org/wordprocessingml/2006/main")
    buffer = io.BytesIO()
    with zipfile.ZipFile(document.s3_key, "r") as source_docx:
        document_xml = source_docx.read("word/document.xml")
        root = ET.fromstring(document_xml)
        _replace_text_node_values(root, pairs)
        converted_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as output_docx:
            for item in source_docx.infolist():
                if item.filename == "word/document.xml":
                    output_docx.writestr(item, converted_xml)
                else:
                    output_docx.writestr(item, source_docx.read(item.filename))

    return buffer.getvalue()


def build_docx_bytes(document: Document, mode: str = "summary") -> bytes:
    """문서 분석 결과를 DOCX 파일 바이트로 변환합니다."""
    mode = mode if mode in {"converted", "comparison", "summary"} else "summary"
    analysis = document.analysis
    paragraphs = analysis.paragraphs if analysis else []
    parts: list[str] = []

    parts.append(_docx_paragraph(f"DocAssist 변환 결과 - {document.title}", bold=True))
    parts.append(_docx_paragraph(f"다운로드 옵션: {mode}"))
    parts.append(_docx_paragraph(""))

    if not analysis:
        parts.append(_docx_paragraph("아직 문서 분석 결과가 없습니다."))
        return _docx_package(parts)

    if mode == "converted":
        parts.append(_docx_paragraph("변환문", bold=True))
        for item in paragraphs:
            parts.append(_docx_paragraph(item.get("easy", "")))
            parts.append(_docx_paragraph(""))
    elif mode == "comparison":
        parts.append(_docx_paragraph("원문 + 변환문 비교본", bold=True))
        for index, item in enumerate(paragraphs, start=1):
            parts.append(_docx_paragraph(f"{index}번 문단 원문", bold=True))
            parts.append(_docx_paragraph(item.get("original", "")))
            parts.append(_docx_paragraph(f"{index}번 문단 변환문", bold=True))
            parts.append(_docx_paragraph(item.get("easy", "")))
            parts.append(_docx_paragraph(""))
    else:
        parts.append(_docx_paragraph("전체 요약", bold=True))
        parts.append(_docx_paragraph(analysis.summary or ""))
        parts.append(_docx_paragraph(""))
        for index, item in enumerate(paragraphs, start=1):
            parts.append(_docx_paragraph(f"{index}번 문단", bold=True))
            parts.append(_docx_paragraph(f"핵심 내용: {item.get('summary', '')}"))
            if item.get("todo"):
                parts.append(_docx_paragraph("해야 할 일: " + ", ".join(item.get("todo", []))))
            if item.get("dates"):
                parts.append(_docx_paragraph("중요한 날짜: " + ", ".join(item.get("dates", []))))
            if item.get("amounts"):
                parts.append(_docx_paragraph("금액: " + ", ".join(item.get("amounts", []))))
            if item.get("conditions"):
                parts.append(_docx_paragraph("조건: " + ", ".join(item.get("conditions", []))))
            parts.append(_docx_paragraph("변환문:"))
            parts.append(_docx_paragraph(item.get("easy", "")))
            parts.append(_docx_paragraph(""))

    return _docx_package(parts)
