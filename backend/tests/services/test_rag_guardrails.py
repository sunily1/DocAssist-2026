from uuid import uuid4

import pytest

from app.services.rag_service import RAGService


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def first(self):
        return self.value


class _QueryResult:
    def __init__(self, value):
        self.value = value

    def scalars(self):
        return _ScalarResult(self.value)


class _FakeDb:
    def __init__(self, analysis):
        self.analysis = analysis

    async def execute(self, _statement):
        return _QueryResult(self.analysis)


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


def test_llm_failure_message_explains_provider_status():
    service = RAGService()
    provider_error = RuntimeError("provider failed")
    provider_error.status_code = 500

    message = service._llm_failure_message(provider_error)

    assert "제공 서버" in message
    assert "오류 500" in message


@pytest.mark.asyncio
async def test_summary_request_uses_saved_analysis_without_keyword_overlap(monkeypatch):
    service = RAGService()
    analysis = type(
        "Analysis",
        (),
        {
            "summary": "창의융합 수업의 운영 방식과 과제 일정을 설명하는 문서입니다.",
            "paragraphs": [
                {
                    "summary": "학생은 14주차에 결과물을 제출합니다.",
                    "easy": "14주차에 결과물을 내야 합니다.",
                    "original": "14주차 결과물 제출",
                }
            ],
        },
    )()

    async def no_embedding(_text):
        return []

    monkeypatch.setattr(service, "get_embedding", no_embedding)
    context, citations = await service.retrieve_context_bundle(
        _FakeDb(analysis),
        "내용 요약해줘",
        uuid4(),
    )

    assert "창의융합 수업의 운영 방식" in context
    assert "14주차에 결과물을 제출" in context
    assert citations[0]["section"] == "요약"
