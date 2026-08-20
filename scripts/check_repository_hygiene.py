"""Fail CI when tracked files contain private runtime data or likely credentials."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
ALLOWED_ENV_FILES = {".env.example", "backend/env.example"}
FORBIDDEN_SUFFIXES = {
    ".db",
    ".docx",
    ".hwp",
    ".hwpx",
    ".key",
    ".p12",
    ".pdf",
    ".pem",
    ".sqlite",
    ".sqlite3",
    ".tgz",
    ".zip",
}
SECRET_PATTERNS = {
    "school LLM key": re.compile(rb"dcu_llm_[A-Za-z0-9]+"),
    "OpenAI-style key": re.compile(rb"sk-[A-Za-z0-9_-]{16,}"),
    "GitHub token": re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    "private key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def forbidden_path(relative: str) -> bool:
    path = Path(relative)
    lowered = relative.lower()
    if path.name.startswith(".env") and relative not in ALLOWED_ENV_FILES:
        return True
    if any(part in {"uploads", "logs"} for part in path.parts):
        return True
    if lowered.startswith("backend/app/data/nikl_") and lowered.endswith(".json"):
        return True
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        return True
    return lowered.endswith((".tar.gz", ".corpus.zip"))


def main() -> int:
    errors: list[str] = []
    for relative in tracked_files():
        path = ROOT / relative
        if forbidden_path(relative):
            errors.append(f"forbidden tracked file: {relative}")
        if not path.is_file() or path.resolve() == SELF:
            continue
        content = path.read_bytes()
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                errors.append(f"possible {label}: {relative}")

    if errors:
        print("Repository hygiene check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Repository hygiene check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
