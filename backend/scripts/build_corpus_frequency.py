"""Build compact DocAssist term-frequency data from licensed NIKL ZIP files.

The original corpora are intentionally not copied into this repository. This script
stores only aggregate counts for terms already supported by the converter.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Iterable


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.easy_converter import EASY_TERMS, TERM_DIFFICULTY  # noqa: E402


FORM_LINE = re.compile(r'^\s*"form":\s*("(?:[^"\\]|\\.)*")\s*,?\s*$')
HANGUL_TOKEN = re.compile(r"[가-힣]+")


def target_tokens() -> set[str]:
    values = set(EASY_TERMS)
    values.update(replacement for replacement, _ in EASY_TERMS.values())
    return {token for value in values for token in HANGUL_TOKEN.findall(value)}


def count_morpheme_zip(path: Path, targets: set[str]) -> tuple[Counter[str], int]:
    counts: Counter[str] = Counter()
    total = 0
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.lower().endswith(".json"):
                continue
            in_mp = False
            mp_indent = 0
            with archive.open(name) as source:
                for raw_line in source:
                    line = raw_line.decode("utf-8-sig", errors="replace").rstrip()
                    if '"MP": [' in line:
                        in_mp = True
                        mp_indent = len(line) - len(line.lstrip())
                        continue
                    if in_mp and line.strip() == "]" and len(line) - len(line.lstrip()) == mp_indent:
                        in_mp = False
                        continue
                    if not in_mp:
                        continue
                    match = FORM_LINE.match(line)
                    if not match:
                        continue
                    form = json.loads(match.group(1))
                    if not HANGUL_TOKEN.fullmatch(form):
                        continue
                    total += 1
                    if form in targets:
                        counts[form] += 1
    return counts, total


def iter_dialogue_forms(path: Path) -> Iterable[str]:
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.lower().endswith(".json"):
                continue
            with archive.open(name) as source:
                payload = json.load(source)
            for document in payload.get("document", []):
                for utterance in document.get("utterance", []):
                    form = utterance.get("form")
                    if isinstance(form, str):
                        yield form


def count_dialogue_zip(path: Path, targets: set[str]) -> tuple[Counter[str], int, Counter[str]]:
    token_counts: Counter[str] = Counter()
    phrase_counts: Counter[str] = Counter()
    total = 0
    phrases = [term for term in EASY_TERMS if " " in term]
    for form in iter_dialogue_forms(path):
        tokens = HANGUL_TOKEN.findall(form)
        total += len(tokens)
        token_counts.update(token for token in tokens if token in targets)
        for phrase in phrases:
            count = form.count(phrase)
            if count:
                phrase_counts[phrase] += count
    return token_counts, total, phrase_counts


def component_frequency(term: str, counts: Counter[str], phrase_counts: Counter[str]) -> int:
    if phrase_counts.get(term):
        return phrase_counts[term]
    tokens = HANGUL_TOKEN.findall(term)
    if not tokens:
        return 0
    return min(counts.get(token, 0) for token in tokens)


def frequency_band(per_million: float) -> int:
    if per_million >= 100:
        return 1
    if per_million >= 10:
        return 2
    return 3


def build_payload(morpheme_zip: Path, dialogue_zip: Path) -> dict:
    targets = target_tokens()
    mp_counts, mp_total = count_morpheme_zip(morpheme_zip, targets)
    dialogue_counts, dialogue_total, phrase_counts = count_dialogue_zip(dialogue_zip, targets)

    terms = {}
    for term in EASY_TERMS:
        mp_count = component_frequency(term, mp_counts, Counter())
        dialogue_count = component_frequency(term, dialogue_counts, phrase_counts)
        mp_rate = mp_count * 1_000_000 / max(mp_total, 1)
        dialogue_rate = dialogue_count * 1_000_000 / max(dialogue_total, 1)
        combined_rate = math.sqrt((mp_rate + 0.01) * (dialogue_rate + 0.01))
        corpus_band = frequency_band(combined_rate)

        # Converter candidates are formal/business terms. Corpus frequency can raise
        # difficulty, while the curated professional-term floor prevents a common but
        # formal word such as "검토" from being incorrectly treated as plain language.
        professional_floor = TERM_DIFFICULTY.get(term, 2)
        if professional_floor >= 3:
            difficulty = 3
        elif professional_floor == 2:
            difficulty = 2
        else:
            # Familiar business expressions stay in the broadest conversion level.
            # A very rare expression is promoted only one step so it does not make
            # the conservative level rewrite too much of the document.
            difficulty = 1 if corpus_band <= 2 else 2
        terms[term] = {
            "morpheme_count": mp_count,
            "dialogue_count": dialogue_count,
            "frequency_per_million": round(combined_rate, 4),
            "corpus_band": corpus_band,
            "professional_floor": professional_floor,
            "difficulty": difficulty,
        }

    return {
        "metadata": {
            "available": True,
            "generated_on": date.today().isoformat(),
            "source": [morpheme_zip.name, dialogue_zip.name],
            "morpheme_tokens": mp_total,
            "dialogue_tokens": dialogue_total,
            "method": "NIKL corpus frequency with a professional-term difficulty floor",
        },
        "terms": terms,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--morpheme", type=Path, required=True)
    parser.add_argument("--dialogue", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=BACKEND_ROOT / "app" / "data" / "nikl_term_frequency.json",
    )
    args = parser.parse_args()
    payload = build_payload(args.morpheme, args.dialogue)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(payload['terms'])} terms to {args.output}")


if __name__ == "__main__":
    main()
