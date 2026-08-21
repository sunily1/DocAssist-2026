import fitz

from app.services.document_processor import processor
from app.services.easy_converter import is_meaningful_change


def _make_pdf(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page(width=612, height=792)
    page.insert_text((72, 96), text, fontname="helv", fontsize=12)
    content = document.tobytes()
    document.close()
    return content


def test_build_pdf_change_annotations_for_original_and_converted(tmp_path):
    original_text = "Terminate this contract in writing."
    easy_text = "End this contract with written notice."
    original_pdf = _make_pdf(original_text)
    converted_pdf = _make_pdf(easy_text)
    file_path = tmp_path / "contract.pdf"
    file_path.write_bytes(original_pdf)
    paragraphs = [
        {
            "original": original_text,
            "easy": easy_text,
            "changed_terms": [
                {
                    "from": "Terminate",
                    "to": "End",
                    "definition": "Finish an agreement.",
                }
            ],
        }
    ]

    original = processor.build_pdf_change_annotations(
        str(file_path), paragraphs, mode="original"
    )
    converted = processor.build_pdf_change_annotations(
        str(file_path),
        paragraphs,
        mode="converted",
        converted_pdf=converted_pdf,
    )

    assert len(original) == 1
    assert len(converted) == 1
    assert original[0]["id"] == "0-0-Terminate-End"
    assert converted[0]["id"] == original[0]["id"]
    assert original[0]["page"] == converted[0]["page"] == 1
    assert original[0]["page_width"] == converted[0]["page_width"] == 612
    assert original[0]["page_height"] == converted[0]["page_height"] == 792
    assert original[0]["original"] == "Terminate"
    assert converted[0]["easy"] == "End"
    assert original[0]["definition"] == "Finish an agreement."
    assert original[0]["width"] > converted[0]["width"] > 0
    assert original[0]["height"] > 0
    assert original[0]["approximate"] is False
    assert converted[0]["approximate"] is False


def test_pdf_conversion_only_changes_blocks_containing_the_source_expression():
    layout = [
        {
            "page": 1,
            "blocks": [
                {"original": "회의록", "easy": "회의록"},
                {"original": "본 건은 서면 통보 후 종료한다.", "easy": "본 건은 서면 통보 후 종료한다."},
                {"original": "참석자 서명", "easy": "참석자 서명"},
            ],
        }
    ]
    paragraphs = [
        {
            "original": "본 건은 서면 통보 후 종료한다.",
            "easy": "이 일은 글로 알린 후 끝낸다.",
            "changed_terms": [
                {"from": "본 건", "to": "이 일"},
                {"from": "서면 통보", "to": "글로 알림"},
                {"from": "종료한다", "to": "끝낸다"},
            ],
        }
    ]

    converted = processor.attach_converted_pdf_text(layout, paragraphs)
    blocks = converted[0]["blocks"]

    assert blocks[0]["easy"] == "회의록"
    assert blocks[1]["easy"] == "이 일은 글로 알림 후 끝낸다."
    assert blocks[2]["easy"] == "참석자 서명"


def test_pdf_conversion_does_not_match_a_term_inside_another_korean_word():
    layout = [
        {
            "page": 1,
            "blocks": [
                {"original": "인공지능부트캠프사업단", "easy": "인공지능부트캠프사업단"},
                {"original": "교육 공지 후 시작", "easy": "교육 공지 후 시작"},
            ],
        }
    ]
    paragraphs = [
        {
            "original": "교육 공지 후 시작",
            "easy": "교육 알림 후 시작",
            "changed_terms": [{"from": "공지", "to": "알림"}],
        }
    ]

    converted = processor.attach_converted_pdf_text(layout, paragraphs)
    blocks = converted[0]["blocks"]

    assert blocks[0]["easy"] == "인공지능부트캠프사업단"
    assert blocks[1]["easy"] == "교육 알림 후 시작"
    assert processor._pdf_changes_for_block(blocks[0]["original"], paragraphs) == []


def test_layout_pdf_preserves_text_outside_the_replaced_phrase(tmp_path):
    document = fitz.open()
    page = document.new_page(width=612, height=792)
    page.insert_text((72, 80), "Header unchanged", fontname="helv", fontsize=12)
    page.insert_text((72, 160), "Terminate contract by written notice.", fontname="helv", fontsize=12)
    page.insert_text((72, 240), "Footer unchanged", fontname="helv", fontsize=12)
    file_path = tmp_path / "positioned-contract.pdf"
    file_path.write_bytes(document.tobytes())
    document.close()

    paragraphs = [
        {
            "original": "Terminate contract by written notice.",
            "easy": "End contract by written notice.",
            "changed_terms": [{"from": "Terminate", "to": "End"}],
        }
    ]
    converted_bytes = processor.build_layout_preserved_pdf(str(file_path), paragraphs)

    converted = fitz.open(stream=converted_bytes, filetype="pdf")
    converted_text = converted[0].get_text()
    converted.close()

    assert "Header unchanged" in converted_text
    assert "Footer unchanged" in converted_text
    assert "End" in converted_text
    assert "contract by written notice." in converted_text


def test_overlong_explanation_is_not_counted_as_an_easy_word_change():
    assert is_meaningful_change("익일", "다음 날") is True
    assert is_meaningful_change("일정", "날짜와 시간 계획") is False
