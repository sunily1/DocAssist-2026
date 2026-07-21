from uuid import uuid4

import pytest

from app.services.rag_service import RAGService


@pytest.mark.asyncio
async def test_document_question_without_context_returns_not_found(monkeypatch):
    service = RAGService()

    async def no_context(*args, **kwargs):
        return "", []

    monkeypatch.setattr(service, "retrieve_context_bundle", no_context)
    result = await service.get_chat_completion(
        db=object(),
        query="문서에 없는 출장비 규정은?",
        messages=[],
        document_id=uuid4(),
    )

    assert result.content == "선택한 문서에서 질문과 관련된 내용을 찾지 못했습니다."
    assert result.citations == []
    assert result.prompt_tokens == 0
    assert result.completion_tokens == 0


def test_lexical_overlap_filters_unrelated_evidence():
    service = RAGService()

    assert service._has_lexical_overlap("회의 날짜와 시간", "회의 일시는 7월 20일 오전 10시입니다.")
    assert not service._has_lexical_overlap("부산 출장비 항공권", "회의 일시는 7월 20일 오전 10시입니다.")
