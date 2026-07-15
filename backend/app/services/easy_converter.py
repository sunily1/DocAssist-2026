"""Business Korean easy-word conversion helpers."""

from __future__ import annotations

import re
from collections import OrderedDict
from typing import Any


INTENSITY_LABELS = {
    "close": "원문에 가깝게",
    "easy": "쉽게",
    "summary": "요약 중심",
}

EASY_TERMS: "OrderedDict[str, tuple[str, str]]" = OrderedDict(
    [
        ("배포 일정", ("자료 전달 계획", "자료나 문서를 전달하는 날짜와 시간 계획입니다.")),
        ("불가피하게", ("어쩔 수 없이", "상황상 피하기 어렵다는 뜻입니다.")),
        ("불가피한", ("어쩔 수 없는", "상황상 피하기 어렵다는 뜻입니다.")),
        ("불가피", ("피하기 어려움", "상황상 피하기 어렵다는 뜻입니다.")),
        ("지연될", ("늦어질", "예정된 시간보다 늦어진다는 뜻입니다.")),
        ("지연", ("늦어짐", "예정된 시간보다 늦어진다는 뜻입니다.")),
        ("조치", ("처리", "문제를 해결하기 위해 필요한 일을 하는 것입니다.")),
        ("검토", ("확인", "내용을 살펴보고 판단하는 것입니다.")),
        ("추후", ("나중에", "지금이 아니라 뒤에 다시 한다는 뜻입니다.")),
        ("해당", ("그", "앞에서 말한 대상이나 내용을 가리키는 말입니다.")),
        ("관련", ("관계된", "어떤 일이나 내용과 연결되어 있다는 뜻입니다.")),
        ("제고하다", ("높이다", "수준이나 정도를 더 높인다는 뜻입니다.")),
        ("제고", ("높임", "수준이나 정도를 더 높이는 일입니다.")),
        ("유관 부서", ("관련 부서", "이 일과 관련된 부서입니다.")),
        ("추후 안내 예정", ("나중에 다시 알려드리겠습니다", "아직 확정되지 않아 나중에 공지한다는 뜻입니다.")),
        ("본 건", ("이 일", "지금 말하고 있는 업무나 사안을 뜻합니다.")),
        ("상기 내용", ("위 내용", "앞에서 말한 내용을 뜻합니다.")),
        ("이행하다", ("실행하다", "약속한 일이나 정해진 절차를 실제로 하는 것입니다.")),
        ("이행", ("실행", "정해진 내용을 실제로 하는 것입니다.")),
        ("검토 요청드립니다", ("확인 부탁드립니다", "내용을 확인하고 의견을 달라는 뜻입니다.")),
        ("검토 요청", ("확인 요청", "내용을 확인해 달라는 뜻입니다.")),
        ("협의", ("상의", "관련 사람이 함께 의논하는 것입니다.")),
        ("조치", ("처리", "문제를 해결하기 위해 필요한 일을 하는 것입니다.")),
        ("공지", ("알림", "여러 사람에게 알려야 하는 내용입니다.")),
        ("배포", ("나누어 전달", "문서나 자료를 여러 사람에게 전달하는 것입니다.")),
        ("첨부", ("함께 보낸 파일", "문서나 메일에 같이 붙여 보낸 파일입니다.")),
        ("기한", ("마감일", "일을 끝내야 하는 날짜입니다.")),
        ("마감", ("끝내야 하는 시점", "정해진 시간 안에 일을 완료해야 한다는 뜻입니다.")),
        ("요청사항", ("부탁한 일", "상대에게 해 달라고 한 내용입니다.")),
        ("참조", ("같이 확인", "직접 담당은 아니지만 내용을 함께 보라는 뜻입니다.")),
        ("필히", ("반드시", "꼭 해야 한다는 뜻입니다.")),
        ("불가", ("할 수 없음", "진행하거나 처리할 수 없다는 뜻입니다.")),
        ("가능 여부", ("할 수 있는지", "진행할 수 있는지 확인한다는 뜻입니다.")),
        ("일정", ("날짜와 시간 계획", "업무가 진행되는 날짜와 시간 계획입니다.")),
        ("담당자", ("맡은 사람", "그 일을 책임지고 처리하는 사람입니다.")),
        ("전사", ("회사 전체", "회사 전체가 대상이라는 뜻입니다.")),
        ("수립", ("계획 세우기", "계획이나 기준을 만드는 것입니다.")),
        ("산정", ("계산", "금액이나 수량을 계산해 정하는 것입니다.")),
        ("지급", ("돈을 줌", "정해진 금액을 주는 것입니다.")),
        ("확정", ("최종 결정", "더 이상 바꾸지 않기로 정했다는 뜻입니다.")),
    ]
)

ACTION_PATTERNS = [
    r"[^.?!\n]*(?:요청|제출|확인|검토|공유|회신|등록|작성|서명|승인|보고|참석|완료|처리)[^.?!\n]*",
]
DATE_PATTERN = re.compile(
    r"(\d{4}[./-]\d{1,2}[./-]\d{1,2}|\d{1,2}\s*월\s*\d{1,2}\s*일|오늘|내일|익일|금일|이번 주|다음 주|월요일|화요일|수요일|목요일|금요일)"
)
AMOUNT_PATTERN = re.compile(r"(\d[\d,]*(?:\.\d+)?\s*(?:원|만원|억원|천원|달러|USD|KRW|%))")
CONDITION_PATTERN = re.compile(r"[^.?!\n]*(?:경우|조건|단,|다만|한하여|이상|이하|초과|미만|필수|제외)[^.?!\n]*")
OWNER_PATTERN = re.compile(r"([가-힣A-Za-z0-9·/\s]{1,24}(?:팀|부서|담당자|담당|본부|센터|파트))")


def normalize_intensity(value: str | None) -> str:
    if value in INTENSITY_LABELS:
        return value
    return "easy"


def has_valid_openai_key(key: str | None) -> bool:
    if not key:
        return False
    stripped = key.strip()
    blocked = ("...", "CHANGE", "your_", "changeme", "none", "null")
    return len(stripped) >= 24 and not any(token in stripped.lower() for token in blocked)


def split_paragraphs(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []
    parts = [p.strip() for p in re.split(r"\n\s*\n+", normalized) if p.strip()]
    if len(parts) == 1:
        lines = [line.strip() for line in normalized.split("\n") if line.strip()]
        if len(lines) > 1:
            return lines
    return parts


def apply_easy_terms(text: str) -> tuple[str, list[dict[str, str]]]:
    converted = text
    changed: list[dict[str, str]] = []
    for term, (replacement, definition) in EASY_TERMS.items():
        if term in converted:
            converted = converted.replace(term, replacement)
            changed.append({"from": term, "to": replacement, "definition": definition})
    return converted, changed


def split_long_sentences(text: str) -> str:
    sentences = re.split(r"(?<!\d\.)(?<=[.!?。])\s+|(?<=다\.)\s+|(?<=요\.)\s+", text)
    cleaned = [s.strip() for s in sentences if s.strip()]
    if len(cleaned) <= 1:
        return text
    return "\n".join(cleaned)


def summarize_sentence(text: str, max_len: int = 90) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_len:
        return compact
    cut = compact[:max_len].rsplit(" ", 1)[0].strip()
    return f"{cut}..."


def find_actions(text: str) -> list[str]:
    actions: list[str] = []
    for pattern in ACTION_PATTERNS:
        for match in re.findall(pattern, text):
            cleaned = re.sub(r"\s+", " ", match).strip(" .")
            if cleaned and cleaned not in actions:
                actions.append(cleaned)
    return actions[:4]


def find_conditions(text: str) -> list[str]:
    values: list[str] = []
    for match in CONDITION_PATTERN.findall(text):
        cleaned = re.sub(r"\s+", " ", match).strip(" .")
        if cleaned and cleaned not in values:
            values.append(cleaned)
    return values[:4]


def find_unique(pattern: re.Pattern[str], text: str, limit: int = 6) -> list[str]:
    found: list[str] = []
    for match in pattern.findall(text):
        value = match.strip()
        if value and value not in found:
            found.append(value)
        if len(found) >= limit:
            break
    return found


def convert_paragraph(original: str, index: int, intensity: str) -> dict[str, Any]:
    easy, changed_terms = apply_easy_terms(original)
    if intensity == "easy":
        easy = split_long_sentences(easy)
    elif intensity == "summary":
        easy = summarize_sentence(easy, 120)

    actions = find_actions(original)
    dates = find_unique(DATE_PATTERN, original)
    amounts = find_unique(AMOUNT_PATTERN, original)
    conditions = find_conditions(original)
    owners = find_unique(OWNER_PATTERN, original, limit=4)
    terms = [
        {
            "term": item["from"],
            "replacement": item["to"],
            "definition": item["definition"],
            "para": index,
            "snippet": summarize_sentence(original, 120),
        }
        for item in changed_terms
    ]

    bullets = []
    summary = summarize_sentence(easy if intensity != "summary" else original, 100)
    if summary:
        bullets.append(summary)
    if actions:
        bullets.append(f"해야 할 일: {actions[0]}")
    if dates:
        bullets.append(f"중요 날짜: {', '.join(dates)}")
    if amounts:
        bullets.append(f"금액: {', '.join(amounts)}")

    return {
        "original": original,
        "easy": easy,
        "summary": summary,
        "bullets": bullets[:5],
        "todo": actions,
        "dates": dates,
        "amounts": amounts,
        "conditions": conditions,
        "owners": owners,
        "terms": terms,
        "changed_terms": changed_terms,
    }


def build_rules(paragraphs: list[dict[str, Any]]) -> list[dict[str, str]]:
    rules: list[dict[str, str]] = []
    for i, para in enumerate(paragraphs, start=1):
        for todo in para.get("todo", [])[:2]:
            rules.append({"title": "해야 할 일", "desc": todo, "source": f"{i}번 문단"})
        for condition in para.get("conditions", [])[:2]:
            rules.append({"title": "조건", "desc": condition, "source": f"{i}번 문단"})
    return rules[:12]


def build_terms(paragraphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    terms: list[dict[str, Any]] = []
    for para in paragraphs:
        for term in para.get("terms", []):
            key = term["term"]
            if key in seen:
                continue
            seen.add(key)
            terms.append(term)
    return terms[:20]


def build_easy_conversion(text: str, intensity: str | None = "easy") -> dict[str, Any]:
    normalized_intensity = normalize_intensity(intensity)
    raw_paragraphs = split_paragraphs(text)
    paragraphs = [
        convert_paragraph(original, index, normalized_intensity)
        for index, original in enumerate(raw_paragraphs, start=1)
    ]

    if normalized_intensity == "summary":
        converted_text = "\n\n".join(p["summary"] for p in paragraphs if p["summary"])
    else:
        converted_text = "\n\n".join(p["easy"] for p in paragraphs if p["easy"])

    summary_candidates = [p["summary"] for p in paragraphs if p["summary"]]
    summary = " ".join(summary_candidates[:3])
    if len(summary) > 260:
        summary = summarize_sentence(summary, 260)

    return {
        "intensity": normalized_intensity,
        "intensity_label": INTENSITY_LABELS[normalized_intensity],
        "summary": summary,
        "converted_text": converted_text,
        "paragraphs": paragraphs,
        "rules": build_rules(paragraphs),
        "terms": build_terms(paragraphs),
    }
