import json

from app.services import corpus_difficulty
from app.services.corpus_difficulty import get_term_difficulty, get_term_frequency
from app.services.easy_converter import (
    apply_easy_terms,
    build_document_summary_points,
    build_easy_conversion,
    contains_standalone_term,
    replace_standalone_term,
)


def test_easy_term_does_not_change_part_of_another_korean_word():
    converted, changes = apply_easy_terms("인공지능 교육 공지 후 시작합니다.", "summary")

    assert converted == "인공지능 교육 알림 후 시작합니다."
    assert [item["from"] for item in changes] == ["공지"]
    assert contains_standalone_term("인공지능", "공지") is False
    assert contains_standalone_term("교육 공지", "공지") is True
    assert replace_standalone_term("인공지능 공지", "공지", "알림") == "인공지능 알림"


def test_delay_conjugation_is_replaced_as_a_complete_expression():
    converted, changes = apply_easy_terms("출도제한이 내려졌고 심사는 지연됐다.")

    assert converted == "출도제한이 내려졌고 심사는 늦어졌다."
    assert "늦어짐됐다" not in converted
    assert any(change["from"] == "지연됐다" and change["to"] == "늦어졌다" for change in changes)


def test_formal_delay_conjugation_remains_grammatical():
    converted, _ = apply_easy_terms("검토가 지연됩니다.")

    assert converted == "확인이 늦어집니다."


def test_particles_follow_the_replacement_word_batchim():
    converted, changes = apply_easy_terms("검토가 필요하며 검토를 요청합니다.")

    assert converted == "확인이 필요하며 확인을 요청합니다."
    assert any(change["from"] == "검토가" and change["to"] == "확인이" for change in changes)
    assert any(change["from"] == "검토를" and change["to"] == "확인을" for change in changes)


def test_intensity_levels_expand_the_conversion_scope():
    text = "향후 협업 역량을 검토하고 불가피한 상황을 극복했던 방안을 제안합니다."

    close = build_easy_conversion(text, "close")
    easy = build_easy_conversion(text, "easy")
    very_easy = build_easy_conversion(text, "summary")

    assert "어쩔 수 없는 상황" in close["converted_text"]
    assert "능력을 확인하고" in easy["converted_text"]
    assert "앞으로 함께 일하기 능력을" in very_easy["converted_text"]
    assert len(close["paragraphs"][0]["changed_terms"]) < len(easy["paragraphs"][0]["changed_terms"])
    assert len(easy["paragraphs"][0]["changed_terms"]) < len(very_easy["paragraphs"][0]["changed_terms"])


def test_nikl_frequency_statistics_drive_term_difficulty(tmp_path, monkeypatch):
    stats_path = tmp_path / "term_frequency.json"
    stats_path.write_text(
        json.dumps(
            {
                "metadata": {"available": True},
                "terms": {
                    "검토": {"frequency_per_million": 12.5, "difficulty": 2},
                    "향후": {"frequency_per_million": 25.0, "difficulty": 1},
                    "조율": {"frequency_per_million": 3.0, "difficulty": 2},
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(corpus_difficulty, "CORPUS_STATS_PATH", stats_path)
    corpus_difficulty.load_corpus_stats.cache_clear()

    try:
        assert get_term_frequency("검토")["frequency_per_million"] > 0
        assert get_term_difficulty("검토") == 2
        assert get_term_difficulty("향후") == 1
        assert get_term_difficulty("조율") == 2
    finally:
        corpus_difficulty.load_corpus_stats.cache_clear()


def test_proposal_conjugation_stays_natural():
    converted, changes = apply_easy_terms("새 아이디어를 제안합니다.", "easy")

    assert converted == "새 아이디어를 냅니다."
    assert "의견합니다" not in converted
    assert changes[0]["to"] == "냅니다"


def test_proposal_request_is_replaced_as_a_complete_phrase():
    converted, changes = apply_easy_terms(
        "금요일까지 개선 방안을 제안해 주시기 바랍니다.",
        "easy",
    )

    assert converted == "금요일까지 개선 방안에 대한 의견을 주시기 바랍니다."
    assert "의견해" not in converted
    assert len(changes) == 1
    assert changes[0]["from"] == "개선 방안을 제안해 주시기 바랍니다"
    assert changes[0]["to"] == "개선 방안에 대한 의견을 주시기 바랍니다"
    assert changes[0]["difficulty"] in {1, 2, 3}


def test_changed_terms_follow_their_order_in_the_source_text():
    _, changes = apply_easy_terms(
        "유관 부서와 협의한 뒤 본 건을 검토했으며 불가피하게 지연되었습니다.",
        "summary",
    )

    assert [item["from"] for item in changes] == [
        "유관 부서와",
        "협의",
        "본 건을",
        "검토",
        "불가피하게",
        "지연되었습니다",
    ]


def test_business_phrases_are_rewritten_without_broken_conjugations():
    source = (
        "향후 업무를 원활히 이행하기 위해 각 부서의 요청사항을 파악하고 "
        "역할을 조율해야 합니다. 최종 계획이 확정되면 전사 공지 후 관련 자료를 "
        "배포할 예정입니다. 기한 내 회신이 불가한 경우에는 담당자에게 알려주세요."
    )

    converted, _ = apply_easy_terms(source, "summary")

    assert "요청 내용을 확인하고 역할을 맞춰야 합니다" in converted
    assert "계획이 결정되면 회사 전체에 알림" in converted
    assert "정해진 날짜 안에 회신이 어려운 경우" in converted
    assert "맞추기해야" not in converted
    assert "할 수 없음한" not in converted
    assert "최종 결정되면" not in converted

    close, _ = apply_easy_terms("전사 공지 후 기한 내 회신이 불가한 경우", "close")
    assert close == "회사 전체에 알림 후 기한 내 회신이 어려운 경우"


def test_document_summary_ignores_pdf_headers_and_keeps_decisions():
    paragraphs = [
        {"easy": "본부장 교수님 대표님"},
        {"easy": "회의록"},
        {"easy": "작성자 소속 윈터 인턴쉽 작성자 직급 팀장 작성자명 조혜진"},
        {"easy": "회의 일시 2025. 12. 15 회의 시간 11:00 ~ 12:00 장소 대회의실"},
        {"easy": "안건 첫 회의 진행 및 과제 수행 방식 공유"},
        {"easy": "• 각자 개 이상의 과제 아이디어를 보고서 또는 형식으로 정리해 오기로 1 PPT 함."},
        {"easy": "• 다음 회의에서 각 자료를 공유하고 아이디어를 비교하기로 함."},
        {"easy": "윈터 인턴쉽 조혜진 010-6398-0041 100%"},
    ]

    points = build_document_summary_points(paragraphs)

    assert any("2025. 12. 15" in point for point in points)
    assert any("각자 1개 이상의" in point and "PPT 형식" in point for point in points)
    assert any("다음 회의" in point for point in points)
    assert all("본부장 교수님" not in point for point in points)
    assert all("010-6398-0041" not in point for point in points)
