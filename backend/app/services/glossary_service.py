"""User-owned document glossary queries and derived context."""

from __future__ import annotations

import re
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentAnalysis, GlossaryTerm


TAG_KEYWORDS = {
    "security": ("보안", "접근", "권한", "기밀", "암호", "인증", "정보보호"),
    "finance": ("비용", "금액", "지급", "정산", "증빙", "예산", "회계", "세금"),
    "legal": ("법", "법령", "계약", "의무", "위반", "책임", "조항", "약관"),
    "policy": ("정책", "규정", "지침", "기준", "절차", "개인정보", "보유기간"),
}


def _primary_tag(term: GlossaryTerm) -> str:
    stored = [tag for tag in (term.tags or []) if tag in {*TAG_KEYWORDS, "general"}]
    if stored:
        return stored[0]

    haystack = f"{term.term} {term.definition}".lower()
    for tag, keywords in TAG_KEYWORDS.items():
        if any(keyword.lower() in haystack for keyword in keywords):
            return tag
    return "general"


def _paragraph_text(paragraph: dict[str, Any]) -> str:
    return str(paragraph.get("original") or "").strip()


def _term_context(term: GlossaryTerm, analysis: Optional[DocumentAnalysis]) -> tuple[list[str], int]:
    evidence: list[str] = []
    frequency = 0
    needle = term.term.strip()
    if not needle or not analysis:
        return evidence, 1

    for paragraph in analysis.paragraphs or []:
        original = _paragraph_text(paragraph)
        if not original:
            continue

        occurrences = len(re.findall(re.escape(needle), original, flags=re.IGNORECASE))
        changed_match = any(
            str(item.get("from") or "").strip().lower() == needle.lower()
            for item in paragraph.get("changed_terms", [])
            if isinstance(item, dict)
        )
        if occurrences or changed_match:
            frequency += max(occurrences, 1)
            compact = re.sub(r"\s+", " ", original).strip()
            if compact and compact not in evidence:
                evidence.append(compact)

    return evidence[:5], max(frequency, 1)


def _serialize(term: GlossaryTerm, document: Document, analysis: Optional[DocumentAnalysis]) -> dict[str, Any]:
    evidence, frequency = _term_context(term, analysis)
    primary_tag = _primary_tag(term)
    tags = list(term.tags or [])
    if not tags:
        tags = [primary_tag]
    return {
        "id": term.id,
        "document_id": document.id,
        "document_title": document.title,
        "term": term.term,
        "definition": term.definition,
        "evidence": evidence,
        "tags": tags,
        "primary_tag": primary_tag,
        "frequency": frequency,
        "is_pinned": term.is_pinned,
        "created_at": term.created_at,
    }


async def list_for_user(
    db: AsyncSession,
    user_id: UUID,
    document_id: Optional[UUID] = None,
) -> list[dict[str, Any]]:
    query = (
        select(GlossaryTerm, Document, DocumentAnalysis)
        .join(Document, GlossaryTerm.document_id == Document.id)
        .outerjoin(DocumentAnalysis, DocumentAnalysis.document_id == Document.id)
        .where(Document.user_id == user_id, Document.deleted_at.is_(None))
        .order_by(GlossaryTerm.created_at.desc())
    )
    if document_id:
        query = query.where(Document.id == document_id)

    rows = (await db.execute(query)).all()
    return [_serialize(term, document, analysis) for term, document, analysis in rows]


async def set_pinned(
    db: AsyncSession,
    user_id: UUID,
    term_id: UUID,
    is_pinned: bool,
) -> Optional[dict[str, Any]]:
    result = await db.execute(
        select(GlossaryTerm, Document, DocumentAnalysis)
        .join(Document, GlossaryTerm.document_id == Document.id)
        .outerjoin(DocumentAnalysis, DocumentAnalysis.document_id == Document.id)
        .where(
            GlossaryTerm.id == term_id,
            Document.user_id == user_id,
            Document.deleted_at.is_(None),
        )
    )
    row = result.first()
    if not row:
        return None

    term, document, analysis = row
    term.is_pinned = is_pinned
    db.add(term)
    await db.commit()
    await db.refresh(term)
    return _serialize(term, document, analysis)
