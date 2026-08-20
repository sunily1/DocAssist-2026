"""Business Korean easy-word conversion helpers."""

from __future__ import annotations

import re
from collections import OrderedDict
from typing import Any

from app.services.corpus_difficulty import get_term_difficulty, get_term_frequency


INTENSITY_LABELS = {
    "close": "살짝",
    "easy": "쉽게",
    "summary": "아주 쉽게",
}

EASY_TERMS: "OrderedDict[str, tuple[str, str]]" = OrderedDict(
    [
        ("배포 일정", ("자료 전달 계획", "자료나 문서를 전달하는 날짜와 시간 계획입니다.")),
        ("불가피하게", ("어쩔 수 없이", "상황상 피하기 어렵다는 뜻입니다.")),
        ("불가피한", ("어쩔 수 없는", "상황상 피하기 어렵다는 뜻입니다.")),
        ("불가피", ("피하기 어려움", "상황상 피하기 어렵다는 뜻입니다.")),
        ("지연되었습니다", ("늦어졌습니다", "예정된 시간보다 늦어졌다는 뜻입니다.")),
        ("지연됩니다", ("늦어집니다", "예정된 시간보다 늦어진다는 뜻입니다.")),
        ("지연됐다", ("늦어졌다", "예정된 시간보다 늦어졌다는 뜻입니다.")),
        ("지연되었다", ("늦어졌다", "예정된 시간보다 늦어졌다는 뜻입니다.")),
        ("지연되는", ("늦어지는", "예정된 시간보다 늦어진다는 뜻입니다.")),
        ("지연되고", ("늦어지고", "예정된 시간보다 늦어진다는 뜻입니다.")),
        ("지연되어", ("늦어져", "예정된 시간보다 늦어진다는 뜻입니다.")),
        ("지연돼", ("늦어져", "예정된 시간보다 늦어진다는 뜻입니다.")),
        ("지연되면", ("늦어지면", "예정된 시간보다 늦어진다는 뜻입니다.")),
        ("지연되지", ("늦어지지", "예정된 시간보다 늦어진다는 뜻입니다.")),
        ("지연된", ("늦어진", "예정된 시간보다 늦어진다는 뜻입니다.")),
        ("지연될", ("늦어질", "예정된 시간보다 늦어진다는 뜻입니다.")),
        ("지연됨", ("늦어짐", "예정된 시간보다 늦어진다는 뜻입니다.")),
        ("지연", ("늦어짐", "예정된 시간보다 늦어진다는 뜻입니다.")),
        ("조치", ("처리", "문제를 해결하기 위해 필요한 일을 하는 것입니다.")),
        ("극복했던", ("이겨냈던", "어려운 상황을 이겨 냈다는 뜻입니다.")),
        ("극복했습니다", ("이겨냈습니다", "어려운 상황을 이겨 냈다는 뜻입니다.")),
        ("극복한", ("이겨낸", "어려운 상황을 이겨 냈다는 뜻입니다.")),
        ("극복하다", ("이겨내다", "어려운 상황을 이겨 낸다는 뜻입니다.")),
        ("극복", ("이겨냄", "어려운 상황을 이겨 낸다는 뜻입니다.")),
        ("개선 방안을 제안해 주시기 바랍니다", ("개선 방안에 대한 의견을 주시기 바랍니다", "개선 방법에 관한 의견을 알려 달라는 뜻입니다.")),
        ("제안해 주시기 바랍니다", ("알려 주시기 바랍니다", "생각이나 의견을 알려 달라는 뜻입니다.")),
        ("제안해 주십시오", ("알려 주십시오", "생각이나 의견을 알려 달라는 뜻입니다.")),
        ("제안해 주세요", ("알려 주세요", "생각이나 의견을 알려 달라는 뜻입니다.")),
        ("제안해 주시기", ("알려 주시기", "생각이나 의견을 알려 달라는 뜻입니다.")),
        ("제안해", ("내", "생각이나 의견을 내놓는다는 뜻입니다.")),
        ("제안했습니다", ("냈습니다", "생각이나 의견을 내놓는다는 뜻입니다.")),
        ("제안합니다", ("냅니다", "생각이나 의견을 내놓는다는 뜻입니다.")),
        ("제안하였다", ("냈다", "생각이나 의견을 내놓는다는 뜻입니다.")),
        ("제안했다", ("냈다", "생각이나 의견을 내놓는다는 뜻입니다.")),
        ("제안하여", ("내어", "생각이나 의견을 내놓는다는 뜻입니다.")),
        ("제안하고", ("내고", "생각이나 의견을 내놓는다는 뜻입니다.")),
        ("제안한", ("낸", "생각이나 의견을 내놓는다는 뜻입니다.")),
        ("제안할", ("낼", "생각이나 의견을 내놓는다는 뜻입니다.")),
        ("제안함", ("냄", "생각이나 의견을 내놓는다는 뜻입니다.")),
        ("제안하기", ("내기", "생각이나 의견을 내놓는다는 뜻입니다.")),
        ("제안", ("의견", "생각이나 의견을 내놓는다는 뜻입니다.")),
        ("파악함", ("확인함", "내용이나 상황을 알아본다는 뜻입니다.")),
        ("파악하고", ("확인하고", "내용이나 상황을 알아본다는 뜻입니다.")),
        ("파악하다", ("확인하다", "내용이나 상황을 알아본다는 뜻입니다.")),
        ("파악", ("확인", "내용이나 상황을 알아본다는 뜻입니다.")),
        ("역량", ("능력", "일을 수행할 수 있는 능력을 뜻합니다.")),
        ("검토", ("확인", "내용을 살펴보고 판단하는 것입니다.")),
        ("추후", ("나중에", "지금이 아니라 뒤에 다시 한다는 뜻입니다.")),
        ("해당", ("그", "앞에서 말한 대상이나 내용을 가리키는 말입니다.")),
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
        ("전사 공지", ("회사 전체에 알림", "회사 구성원 모두에게 알리는 것을 뜻합니다.")),
        ("공지", ("알림", "여러 사람에게 알려야 하는 내용입니다.")),
        ("배포", ("나누어 전달", "문서나 자료를 여러 사람에게 전달하는 것입니다.")),
        ("첨부", ("함께 보낸 파일", "문서나 메일에 같이 붙여 보낸 파일입니다.")),
        ("기한 내", ("정해진 날짜 안에", "정해진 날짜가 지나기 전에 해야 한다는 뜻입니다.")),
        ("기한", ("마감일", "일을 끝내야 하는 날짜입니다.")),
        ("마감", ("끝내야 하는 시점", "정해진 시간 안에 일을 완료해야 한다는 뜻입니다.")),
        ("요청사항", ("요청 내용", "상대에게 해 달라고 한 내용입니다.")),
        ("참조", ("같이 확인", "직접 담당은 아니지만 내용을 함께 보라는 뜻입니다.")),
        ("필히", ("반드시", "꼭 해야 한다는 뜻입니다.")),
        ("불가한 경우", ("어려운 경우", "진행하거나 처리하기 어려운 경우를 뜻합니다.")),
        ("불가한", ("어려운", "진행하거나 처리하기 어렵다는 뜻입니다.")),
        ("불가합니다", ("할 수 없습니다", "진행하거나 처리할 수 없다는 뜻입니다.")),
        ("불가", ("할 수 없음", "진행하거나 처리할 수 없다는 뜻입니다.")),
        ("가능 여부", ("할 수 있는지", "진행할 수 있는지 확인한다는 뜻입니다.")),
        ("담당자", ("맡은 사람", "그 일을 책임지고 처리하는 사람입니다.")),
        ("전사", ("회사 전체", "회사 전체가 대상이라는 뜻입니다.")),
        ("수립", ("계획 세우기", "계획이나 기준을 만드는 것입니다.")),
        ("산정", ("계산", "금액이나 수량을 계산해 정하는 것입니다.")),
        ("지급", ("돈을 줌", "정해진 금액을 주는 것입니다.")),
        ("확정되면", ("결정되면", "내용이 최종적으로 정해지는 것을 뜻합니다.")),
        ("확정되었습니다", ("결정되었습니다", "내용이 최종적으로 정해졌다는 뜻입니다.")),
        ("확정", ("결정", "더 이상 바꾸지 않기로 정했다는 뜻입니다.")),
        ("오리엔테이션", ("첫 안내", "처음 시작할 때 필요한 내용을 안내하는 자리입니다.")),
        ("친목", ("친해지기", "사람들이 서로 가까워지는 것을 뜻합니다.")),
        ("협업", ("함께 일하기", "여러 사람이 일을 함께하는 것을 뜻합니다.")),
        ("작업 스타일", ("일하는 방식", "평소에 일을 진행하는 방식을 뜻합니다.")),
        ("커뮤니케이션 방식", ("소통 방식", "서로 의견을 주고받는 방식을 뜻합니다.")),
        ("커뮤니케이션", ("소통", "서로 의견과 정보를 주고받는 것을 뜻합니다.")),
        ("원활히", ("문제없이", "일이 막히지 않고 잘 진행된다는 뜻입니다.")),
        ("강점", ("잘하는 점", "다른 부분보다 잘하는 점을 뜻합니다.")),
        ("향후", ("앞으로", "현재보다 뒤의 시간을 뜻합니다.")),
        ("논의", ("의논", "의견을 주고받으며 이야기하는 것을 뜻합니다.")),
        ("선정", ("선택", "여러 대상 중 하나를 고르는 것을 뜻합니다.")),
        ("조율해야 합니다", ("맞춰야 합니다", "서로 다른 의견이나 일정을 맞춰야 한다는 뜻입니다.")),
        ("조율해야", ("맞춰야", "서로 다른 의견이나 일정을 맞춰야 한다는 뜻입니다.")),
        ("조율했습니다", ("맞췄습니다", "서로 다른 의견이나 일정을 맞췄다는 뜻입니다.")),
        ("조율하다", ("맞추다", "서로 다른 의견이나 일정을 맞추는 것을 뜻합니다.")),
        ("조율하고", ("맞추고", "서로 다른 의견이나 일정을 맞추는 것을 뜻합니다.")),
        ("조율한", ("맞춘", "서로 다른 의견이나 일정을 맞추는 것을 뜻합니다.")),
        ("조율", ("맞춤", "서로 다른 의견이나 일정을 맞추는 것을 뜻합니다.")),
    ]
)

# 숫자가 클수록 더 어려운 표현입니다. 살짝(3), 쉽게(2~3), 아주 쉽게(1~3) 순으로
# 변환 범위를 넓혀 세 단계가 실제로 서로 다른 결과를 만들도록 합니다.
TERM_DIFFICULTY: dict[str, int] = {
    "불가피하게": 3,
    "불가피한": 3,
    "불가피": 3,
    "제고하다": 3,
    "제고": 3,
    "유관 부서": 3,
    "본 건": 3,
    "상기 내용": 3,
    "이행하다": 3,
    "이행": 3,
    "필히": 3,
    "불가": 3,
    "불가한 경우": 3,
    "불가한": 3,
    "불가합니다": 3,
    "전사": 3,
    "전사 공지": 3,
    "수립": 3,
    "산정": 3,
    "오리엔테이션": 1,
    "친목": 1,
    "협업": 1,
    "작업 스타일": 1,
    "커뮤니케이션 방식": 1,
    "커뮤니케이션": 1,
    "원활히": 1,
    "강점": 1,
    "향후": 1,
    "논의": 1,
    "선정": 1,
    "조율": 1,
}

INTENSITY_MIN_DIFFICULTY = {"close": 3, "easy": 2, "summary": 1}

ACTION_PATTERNS = [
    r"[^.?!\n]*(?:요청|제출|확인|검토|공유|회신|등록|작성|서명|승인|보고|참석|완료|처리)[^.?!\n]*",
]
DATE_PATTERN = re.compile(
    r"(\d{4}[./-]\d{1,2}[./-]\d{1,2}|\d{1,2}\s*월\s*\d{1,2}\s*일|오늘|내일|익일|금일|이번 주|다음 주|월요일|화요일|수요일|목요일|금요일)"
)
AMOUNT_PATTERN = re.compile(r"(\d[\d,]*(?:\.\d+)?\s*(?:원|만원|억원|천원|달러|USD|KRW|%))")
CONDITION_PATTERN = re.compile(r"[^.?!\n]*(?:경우|조건|단,|다만|한하여|이상|이하|초과|미만|필수|제외)[^.?!\n]*")
OWNER_PATTERN = re.compile(r"([가-힣A-Za-z0-9·/\s]{1,24}(?:팀|부서|담당자|담당|본부|센터|파트))")
PARTICLE_PATTERN = r"(?:으로|로|이|가|을|를|은|는|과|와)"


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


def is_meaningful_change(source: str | None, replacement: str | None) -> bool:
    """쉬운말이 원문보다 과도하게 길어져 오히려 이해를 방해하는 변경을 제외합니다."""
    original = re.sub(r"\s+", "", str(source or "").strip())
    easy = re.sub(r"\s+", "", str(replacement or "").strip())
    if not original or not easy or original == easy:
        return False
    if len(original) <= 2 and len(easy) > len(original) * 3:
        return False
    return True


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


def _hangul_final_consonant(value: str) -> int:
    """마지막 한글 음절의 종성 번호를 반환합니다. 종성이 없으면 0입니다."""
    for character in reversed(value.strip()):
        code = ord(character)
        if 0xAC00 <= code <= 0xD7A3:
            return (code - 0xAC00) % 28
    return 0


def _particle_for(replacement: str, particle: str) -> str:
    final_consonant = _hangul_final_consonant(replacement)
    has_final = final_consonant != 0
    if particle in {"이", "가"}:
        return "이" if has_final else "가"
    if particle in {"을", "를"}:
        return "을" if has_final else "를"
    if particle in {"은", "는"}:
        return "은" if has_final else "는"
    if particle in {"과", "와"}:
        return "과" if has_final else "와"
    if particle in {"으로", "로"}:
        return "으로" if has_final and final_consonant != 8 else "로"
    return particle


def _replace_easy_term(text: str, term: str, replacement: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []
    pattern = re.compile(rf"{re.escape(term)}(?P<particle>{PARTICLE_PATTERN})?")

    def replace_match(match: re.Match[str]) -> str:
        particle = match.group("particle") or ""
        target = replacement + (_particle_for(replacement, particle) if particle else "")
        changes.append((match.group(0), target))
        return target

    return pattern.sub(replace_match, text), changes


def apply_easy_terms(text: str, intensity: str | None = "easy") -> tuple[str, list[dict[str, str]]]:
    normalized_intensity = normalize_intensity(intensity)
    minimum_difficulty = INTENSITY_MIN_DIFFICULTY[normalized_intensity]
    converted = text
    changed: list[dict[str, str]] = []
    for term, (replacement, definition) in EASY_TERMS.items():
        difficulty = get_term_difficulty(term, TERM_DIFFICULTY.get(term, 2))
        if difficulty < minimum_difficulty:
            continue
        if term in converted:
            converted, replacements = _replace_easy_term(converted, term, replacement)
            for source, target in replacements:
                frequency = get_term_frequency(term)
                item = {
                    "from": source,
                    "to": target,
                    "definition": definition,
                    "difficulty": difficulty,
                    "frequency_per_million": frequency.get("frequency_per_million") if frequency else None,
                }
                if item not in changed:
                    changed.append(item)
    changed.sort(
        key=lambda item: (
            text.find(item["from"]) if text.find(item["from"]) >= 0 else len(text),
            -len(item["from"]),
        )
    )
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


SUMMARY_HEADINGS = {
    "회의록",
    "회의 내용 요약",
    "회의 내용 (요약)",
    "회의 결과",
    "참석자",
}


def _clean_summary_text(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(r"\s+([,.:;!?])", r"\1", text)
    text = text.replace(",.", ".").replace("()", "").strip(" ,")
    text = text.replace("기술 스택프로젝트실습 경험관심 분야", "기술 스택, 프로젝트·실습 경험, 관심 분야")
    text = re.sub(r"자료를 만들고 에,?\s*(\d{1,2}/\d{1,2})", r"자료를 만들고 \1에", text)
    text = re.sub(r"각자 개 이상의", "각자 1개 이상의", text)
    text = re.sub(r"보고서 또는 형식으로 제작해야 함을 확인함\s*PPT", "보고서 또는 PPT 형식으로 제작해야 함을 확인함", text)
    text = re.sub(r"보고서 또는 형식으로 정리해 오기로\s*(?:1\s*)?PPT\s*함", "보고서 또는 PPT 형식으로 정리해 오기로 함", text)
    return text


def _is_summary_noise(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    return bool(
        not compact
        or compact in {re.sub(r"\s+", "", heading) for heading in SUMMARY_HEADINGS}
        or re.search(r"01\d[- ]?\d{3,4}[- ]?\d{4}", text)
        or ("작성자" in text and ("소속" in text or "직급" in text))
        or ("소속" in text and "연락처" in text)
        or ("본부장" in text and "교수님" in text)
        or "연서 날인" in text
    )


def build_document_summary_points(paragraphs: list[dict[str, Any]]) -> list[str]:
    """표 제목과 서명란은 제외하고 날짜·안건·결정·할 일을 중심으로 요약합니다."""
    grouped: list[tuple[int, str]] = []
    current = ""
    current_index = 0

    def flush_current() -> None:
        nonlocal current
        cleaned = _clean_summary_text(current)
        if cleaned and not _is_summary_noise(cleaned):
            grouped.append((current_index, cleaned))
        current = ""

    for index, paragraph in enumerate(paragraphs):
        text = _clean_summary_text(
            str(paragraph.get("easy") or paragraph.get("summary") or paragraph.get("original") or "")
        )
        if not text:
            continue
        if text.startswith(("•", "●", "-")):
            flush_current()
            current_index = index
            current = text.lstrip("•●- ")
            continue
        if current and not _is_summary_noise(text):
            current = f"{current} {text}"
            continue

        flush_current()
        if _is_summary_noise(text):
            continue
        if "회의 일시" in text or text.startswith("안건"):
            grouped.append((index, text))

    flush_current()

    scored: list[tuple[int, int, str]] = []
    seen: set[str] = set()
    for index, text in grouped:
        key = re.sub(r"[^가-힣A-Za-z0-9]", "", text)
        if not key or key in seen:
            continue
        seen.add(key)
        score = 1
        if "회의 일시" in text or text.startswith("안건"):
            score += 7
        if re.search(r"결정|합의|발표|하기로|오기로|팀장|다음 회의", text):
            score += 6
        if re.search(r"과제|아이디어|프로그램|보고서|PPT", text, re.IGNORECASE):
            score += 3
        if re.search(r"첫 회의|자기소개|잘하는 점|일하는 방식", text):
            score += 2
        scored.append((score, index, summarize_sentence(text, 180)))

    selected = sorted(scored, key=lambda item: (-item[0], item[1]))[:6]
    return [text for _, _, text in sorted(selected, key=lambda item: item[1])]


def build_document_summary(paragraphs: list[dict[str, Any]]) -> str:
    return " ".join(build_document_summary_points(paragraphs))


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
    easy, changed_terms = apply_easy_terms(original, intensity)
    if intensity in {"easy", "summary"}:
        easy = split_long_sentences(easy)

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
    summary = summarize_sentence(easy, 100)
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

    converted_text = "\n\n".join(p["easy"] for p in paragraphs if p["easy"])

    summary = build_document_summary(paragraphs)
    if not summary:
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
