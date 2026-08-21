import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Any, Dict, List

import fitz  # PyMuPDF(PDF 처리 라이브러리)
import openai
import tiktoken

from app.core.config import settings
from app.services.easy_converter import (
    build_easy_conversion,
    contains_standalone_term,
    has_valid_openai_key,
    is_meaningful_change,
    normalize_intensity,
    replace_standalone_term,
)


def build_openai_client():
    client_options = {"api_key": settings.OPENAI_API_KEY or "not-configured"}
    if settings.OPENAI_BASE_URL:
        client_options["base_url"] = settings.OPENAI_BASE_URL
    return openai.AsyncOpenAI(**client_options)


class DocumentProcessor:
    """문서 텍스트 추출/청킹/임베딩/분석을 담당하는 서비스."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.client = build_openai_client()

    @property
    def has_llm(self) -> bool:
        key = (settings.OPENAI_API_KEY or "").strip()
        return has_valid_openai_key(key) and bool(settings.OPENAI_BASE_URL or key.startswith("sk-"))

    def extract_text(self, file_path: str, file_type: str) -> str:
        """파일 타입에 따라 텍스트를 추출합니다."""
        text = ""
        file_type = file_type.lower()

        if "pdf" in file_type:
            try:
                text = self._extract_pdf_text(file_path)
            except Exception as e:
                print(f"Error extracting text from PDF: {e}")
        elif "txt" in file_type:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            except UnicodeDecodeError:
                with open(file_path, "r", encoding="cp949") as f:
                    text = f.read()
            except Exception as e:
                print(f"Error extracting text from TXT: {e}")
        elif "docx" in file_type:
            try:
                text = self._extract_docx_text(file_path)
            except Exception as e:
                print(f"Error extracting text from DOCX: {e}")

        return text

    def _clean_pdf_block(self, value: str) -> str:
        lines = [line.strip() for line in value.replace("\uf06c", "• ").splitlines() if line.strip()]
        if not lines:
            return ""
        joined = " ".join(lines)
        joined = re.sub(r"\s+", " ", joined)
        joined = re.sub(
            r"(?<![가-힣])(?:[가-힣]\s+){2,}[가-힣](?![가-힣])",
            lambda match: match.group(0).replace(" ", ""),
            joined,
        )
        joined = re.sub(r"\s+([,.:;!?%])", r"\1", joined)
        joined = re.sub(r"([([{])\s+", r"\1", joined)
        joined = re.sub(r"\s+([])}])", r"\1", joined)
        joined = joined.replace("• ", "\n• ")
        return joined.strip()

    def _extract_pdf_text(self, file_path: str) -> str:
        layout = self.extract_pdf_layout(file_path)
        blocks = [
            block["original"]
            for page in layout
            for block in page.get("blocks", [])
            if block.get("original")
        ]
        return "\n\n".join(blocks)

    def extract_pdf_layout(self, file_path: str) -> list[dict[str, Any]]:
        """PDF의 페이지 크기와 텍스트 블록 좌표/기본 서식을 추출합니다."""
        pages: list[dict[str, Any]] = []
        with fitz.open(file_path) as doc:
            global_index = 0
            for page_index, page in enumerate(doc):
                page_blocks: list[dict[str, Any]] = []
                page_dict = page.get_text("dict", sort=True)
                for raw_block in page_dict.get("blocks", []):
                    if raw_block.get("type") != 0:
                        continue

                    lines: list[str] = []
                    spans: list[dict[str, Any]] = []
                    for line in raw_block.get("lines", []):
                        line_text = "".join(span.get("text", "") for span in line.get("spans", []))
                        if line_text.strip():
                            lines.append(line_text)
                        spans.extend(line.get("spans", []))

                    original = self._clean_pdf_block("\n".join(lines))
                    bbox = raw_block.get("bbox")
                    if not original or not bbox or len(bbox) != 4:
                        continue

                    visible_spans = [span for span in spans if span.get("text", "").strip()]
                    first_span = visible_spans[0] if visible_spans else {}
                    sizes = [float(span.get("size", 10)) for span in visible_spans if span.get("size")]
                    font_size = max(5.0, min(36.0, sum(sizes) / len(sizes))) if sizes else 10.0

                    page_blocks.append(
                        {
                            "index": global_index,
                            "bbox": [round(float(value), 3) for value in bbox],
                            "original": original,
                            "easy": original,
                            "font_size": round(font_size, 2),
                            "color": int(first_span.get("color", 0) or 0),
                        }
                    )
                    global_index += 1

                pages.append(
                    {
                        "page": page_index + 1,
                        "width": round(float(page.rect.width), 3),
                        "height": round(float(page.rect.height), 3),
                        "blocks": page_blocks,
                    }
                )
        return pages

    def attach_converted_pdf_text(
        self,
        layout: list[dict[str, Any]],
        paragraphs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """실제 원문 표현이 있는 PDF 블록만 쉬운말로 부분 치환합니다."""
        for page in layout:
            for block in page.get("blocks", []):
                original = str(block.get("original") or "")
                easy = original
                changes = self._pdf_changes_for_block(original, paragraphs)
                for _, _, term in sorted(
                    changes,
                    key=lambda item: len(str(item[2].get("from") or "")),
                    reverse=True,
                ):
                    source = str(term.get("from") or "").strip()
                    replacement = str(term.get("to") or "").strip()
                    if source and replacement and source != replacement:
                        easy = replace_standalone_term(easy, source, replacement)
                block["easy"] = easy
        return layout

    def _pdf_changes_for_block(
        self,
        block_text: str,
        paragraphs: list[dict[str, Any]],
    ) -> list[tuple[int, int, dict[str, Any]]]:
        """PDF 블록 원문에 실제로 존재하는 변경 표현과 원래 문단 위치를 반환합니다."""
        text = str(block_text or "")
        matches: list[tuple[int, int, dict[str, Any]]] = []
        seen: set[tuple[str, str]] = set()
        for paragraph_index, paragraph in enumerate(paragraphs):
            for term_index, term in enumerate(paragraph.get("changed_terms") or []):
                source = str(term.get("from") or "").strip()
                replacement = str(term.get("to") or "").strip()
                key = (source, replacement)
                if (
                    source
                    and replacement
                    and source != replacement
                    and is_meaningful_change(source, replacement)
                    and contains_standalone_term(text, source)
                    and key not in seen
                ):
                    matches.append((paragraph_index, term_index, term))
                    seen.add(key)
        return matches

    def _pdf_font_path(self) -> str | None:
        configured = os.getenv("PDF_KOREAN_FONT_PATH", "").strip()
        candidates = [
            configured,
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
            "/System/Library/Fonts/Supplemental/NotoSansGothic-Regular.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        ]
        return next((path for path in candidates if path and os.path.exists(path)), None)

    def _pdf_text_color(self, value: Any) -> tuple[float, float, float]:
        try:
            red, green, blue = fitz.sRGB_to_rgb(int(value or 0))
            return red / 255, green / 255, blue / 255
        except Exception:
            return 0, 0, 0

    def build_layout_preserved_pdf(
        self,
        file_path: str,
        paragraphs: list[dict[str, Any]],
    ) -> bytes:
        """원본 페이지를 유지하고 변경이 있는 텍스트 블록을 쉬운말로 다시 배치합니다."""
        layout = self.extract_pdf_layout(file_path)
        font_path = self._pdf_font_path()
        changed_blocks: list[str] = []
        for page_layout in layout:
            for block in page_layout.get("blocks", []):
                original = str(block.get("original") or "").strip()
                if original and self._pdf_changes_for_block(original, paragraphs):
                    changed_blocks.append(original)
        needs_korean_font = any(re.search(r"[가-힣]", text) for text in changed_blocks)
        if needs_korean_font and not font_path:
            raise RuntimeError("Korean PDF font is not available")

        with fitz.open(file_path) as doc:
            for page_index, page_layout in enumerate(layout):
                if page_index >= len(doc):
                    break
                page = doc[page_index]
                font_name = f"docassist_ko_{page_index}" if font_path else "helv"
                blocks = page_layout.get("blocks", [])

                for block_index, block in enumerate(blocks):
                    original = str(block.get("original") or "").strip()
                    changes = self._pdf_changes_for_block(original, paragraphs)
                    if not original or not changes:
                        continue

                    converted = original
                    for _, _, term in sorted(
                        changes,
                        key=lambda item: len(str(item[2].get("from") or "")),
                        reverse=True,
                    ):
                        source = str(term.get("from") or "").strip()
                        replacement = str(term.get("to") or "").strip()
                        if source and replacement and source != replacement:
                            converted = replace_standalone_term(converted, source, replacement)
                    if converted == original:
                        continue

                    block_rect = fitz.Rect(block.get("bbox", []))
                    block_rect.intersect(page.rect)
                    if block_rect.is_empty:
                        continue

                    next_y = page.rect.y1
                    for later_block in blocks[block_index + 1:]:
                        later_rect = fitz.Rect(later_block.get("bbox", []))
                        if later_rect.y0 >= block_rect.y1:
                            next_y = later_rect.y0
                            break

                    target = fitz.Rect(
                        block_rect.x0 - 0.5,
                        block_rect.y0 - 0.3,
                        block_rect.x1 + 0.5,
                        max(block_rect.y1 + 0.3, next_y - 1.0),
                    )
                    target.intersect(page.rect)
                    self._replace_pdf_text_block(
                        page,
                        block_rect,
                        target,
                        converted,
                        font_name=font_name,
                        font_path=font_path,
                        preferred_size=float(block.get("font_size") or 10),
                        color=self._pdf_text_color(block.get("color")),
                    )

            return doc.tobytes(garbage=4, deflate=True, clean=True)

    def _replace_pdf_text_block(
        self,
        page: fitz.Page,
        original_rect: fitz.Rect,
        target: fitz.Rect,
        text: str,
        *,
        font_name: str,
        font_path: str | None,
        preferred_size: float,
        color: tuple[float, float, float],
    ) -> bool:
        """블록 전체를 같은 글자 크기로 다시 써 긴 쉬운말도 문장 흐름에 포함합니다."""
        start_size = min(preferred_size, max(5.5, original_rect.height * 0.76))
        minimum_size = max(5.5, start_size * 0.85)
        size = start_size
        while size >= minimum_size:
            shape = page.new_shape()
            remaining = shape.insert_textbox(
                target,
                text,
                fontname=font_name,
                fontfile=font_path,
                fontsize=size,
                color=color,
                lineheight=1.15,
            )
            if remaining >= 0:
                page.draw_rect(original_rect, color=None, fill=(1, 1, 1), overlay=True)
                shape.commit(overlay=True)
                return True
            size -= 0.5
        return False

    def _replace_pdf_phrase_at_rect(
        self,
        page: fitz.Page,
        rect: fitz.Rect,
        replacement: str,
        *,
        font_name: str,
        font_path: str | None,
        preferred_size: float,
        color: tuple[float, float, float],
    ) -> bool:
        """원문 표현의 사각형 안에 들어갈 때만 해당 영역을 가리고 쉬운말을 삽입합니다."""
        target = fitz.Rect(rect.x0 - 0.5, rect.y0 - 0.3, rect.x1 + 0.5, rect.y1 + 0.3)
        target.intersect(page.rect)
        start_size = min(preferred_size, max(5.0, target.height * 0.76))
        # 긴 쉬운말을 원래의 짧은 칸에 억지로 넣어 글자가 작아지는 것을 막습니다.
        # 원문 크기의 88% 안에서 들어가지 않으면 원문 PDF는 유지하고, 뷰어의
        # 페이지 기준 오버레이가 동일한 크기로 쉬운말을 표시합니다.
        minimum_size = max(5.5, start_size * 0.88)
        size = start_size
        while size >= minimum_size:
            shape = page.new_shape()
            remaining = shape.insert_textbox(
                target,
                replacement,
                fontname=font_name,
                fontfile=font_path,
                fontsize=size,
                color=color,
                lineheight=1.0,
            )
            if remaining >= 0:
                page.draw_rect(target, color=None, fill=(1, 1, 1), overlay=True)
                shape.commit(overlay=True)
                return True
            size -= 0.5
        return False

    def build_pdf_change_annotations(
        self,
        file_path: str,
        paragraphs: list[dict[str, Any]],
        mode: str = "converted",
        converted_pdf: bytes | None = None,
    ) -> list[dict[str, Any]]:
        """PDF 페이지에서 변경 표현의 실제 좌표를 찾아 뷰어 오버레이로 반환합니다."""
        normalized_mode = "original" if mode == "original" else "converted"
        layout = self.extract_pdf_layout(file_path)
        if normalized_mode == "converted":
            pdf_bytes = converted_pdf or self.build_layout_preserved_pdf(file_path, paragraphs)
            pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
        else:
            pdf = fitz.open(file_path)

        annotations: list[dict[str, Any]] = []
        try:
            for page_index, page_layout in enumerate(layout):
                if page_index >= len(pdf):
                    break
                page = pdf[page_index]
                page_width = float(page.rect.width)
                page_height = float(page.rect.height)

                for block in page_layout.get("blocks", []):
                    original_text = str(block.get("original") or "").strip()
                    converted_block = self.attach_converted_pdf_text(
                        [{"blocks": [dict(block)]}], paragraphs
                    )[0]["blocks"][0]
                    easy_text = str(converted_block.get("easy") or original_text).strip()
                    clip = fitz.Rect(block.get("bbox", []))
                    clip.intersect(page.rect)

                    for paragraph_index, term_index, term in self._pdf_changes_for_block(
                        original_text, paragraphs
                    ):
                        original = str(term.get("from") or "").strip()
                        easy = str(term.get("to") or "").strip()
                        if not original or not easy or original == easy or clip.is_empty:
                            continue

                        needle = original if normalized_mode == "original" else easy
                        rects = self._search_pdf_phrase(page, needle, clip)
                        approximate = False
                        if not rects:
                            block_text = original_text if normalized_mode == "original" else easy_text
                            estimated = self._estimate_pdf_phrase_rect(clip, block_text, needle)
                            rects = [estimated] if estimated else []
                            approximate = bool(rects)

                        annotation_id = f"{paragraph_index}-{term_index}-{original}-{easy}"
                        for segment, rect in enumerate(rects):
                            annotations.append(
                                {
                                    "id": annotation_id,
                                    "segment": segment,
                                    "page": page_index + 1,
                                    "page_width": round(page_width, 3),
                                    "page_height": round(page_height, 3),
                                    "x": round(float(rect.x0), 3),
                                    "y": round(float(rect.y0), 3),
                                    "width": round(float(rect.width), 3),
                                    "height": round(float(rect.height), 3),
                                    "original": original,
                                    "easy": easy,
                                    "definition": str(term.get("definition") or "").strip(),
                                    "approximate": approximate,
                                }
                            )
        finally:
            pdf.close()
        return annotations

    def _search_pdf_phrase(self, page: fitz.Page, phrase: str, clip: fitz.Rect) -> list[fitz.Rect]:
        candidates = [phrase]
        compact = " ".join(phrase.split())
        if compact and compact != phrase:
            candidates.append(compact)
        prefix = compact
        while len(prefix) > 2:
            prefix = prefix[:-1]
            if prefix not in candidates and len(prefix) >= max(2, len(compact) // 2):
                candidates.append(prefix)

        for candidate in candidates:
            found = page.search_for(candidate, clip=clip)
            if found:
                return [rect & page.rect for rect in found if not (rect & page.rect).is_empty]
        return []

    def _estimate_pdf_phrase_rect(
        self,
        block: fitz.Rect,
        block_text: str,
        phrase: str,
    ) -> fitz.Rect | None:
        text = " ".join(str(block_text or "").split())
        needle = " ".join(str(phrase or "").split())
        if not text or not needle or block.is_empty:
            return None

        index = text.find(needle)
        if index < 0:
            prefix = needle
            while len(prefix) >= 2 and (index := text.find(prefix)) < 0:
                prefix = prefix[:-1]
            if index < 0 or len(prefix) < 2:
                return None
            needle = prefix

        line_height = max(8.0, min(block.height, 16.0))
        estimated_lines = max(1, round(block.height / line_height))
        chars_per_line = max(1, int(len(text) / estimated_lines))
        line_index = min(estimated_lines - 1, index // chars_per_line)
        column = index % chars_per_line
        line_chars = min(chars_per_line, max(1, len(text) - line_index * chars_per_line))
        x0 = block.x0 + block.width * min(1.0, column / line_chars)
        width = max(8.0, block.width * min(1.0, len(needle) / line_chars))
        y0 = block.y0 + block.height * (line_index / estimated_lines)
        y1 = block.y0 + block.height * ((line_index + 1) / estimated_lines)
        return fitz.Rect(x0, y0, min(block.x1, x0 + width), y1)

    def _extract_docx_text(self, file_path: str) -> str:
        """DOCX 내부 XML에서 문단 텍스트를 추출합니다."""
        paragraphs: list[str] = []
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        with zipfile.ZipFile(file_path) as docx:
            xml = docx.read("word/document.xml")
        root = ET.fromstring(xml)
        for paragraph in root.findall(".//w:p", namespace):
            pieces = []
            for node in paragraph.findall(".//w:t", namespace):
                if node.text:
                    pieces.append(node.text)
            line = "".join(pieces).strip()
            if line:
                paragraphs.append(line)
        return "\n\n".join(paragraphs)

    def chunk_text(self, text: str) -> List[str]:
        """토큰 수를 기준으로 텍스트를 청크로 분할합니다."""
        if not text:
            return []

        tokens = self.encoding.encode(text)
        total_tokens = len(tokens)
        chunks = []

        start = 0
        while start < total_tokens:
            end = min(start + self.chunk_size, total_tokens)
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)

            if end == total_tokens:
                break

            start += self.chunk_size - self.chunk_overlap

        return chunks

    async def create_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """OpenAI API를 사용하여 텍스트 청크에 대한 임베딩을 생성합니다."""
        if not chunks or not self.has_llm:
            return []

        embeddings = []
        batch_size = 20

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            try:
                response = await self.client.embeddings.create(
                    input=batch,
                    model=settings.OPENAI_EMBEDDING_MODEL,
                )
                embeddings.extend([data.embedding for data in response.data])
            except Exception:
                print("Error creating embeddings for batch.")

        return embeddings

    async def analyze_document(self, text: str, intensity: str = "easy") -> Dict[str, Any]:
        """문서를 업무용 쉬운말로 변환하고 이해 보조 정보를 추출합니다."""
        if not text:
            return {}

        normalized_intensity = normalize_intensity(intensity)
        fallback_result = build_easy_conversion(text, normalized_intensity)
        if not self.has_llm:
            return fallback_result

        context_text = text[:30000]
        intensity_guide = {
            "close": "Keep the original business tone. Replace mainly difficult words and expressions.",
            "easy": "Split long sentences, explain difficult expressions, and keep a clear professional tone.",
            "summary": "Rewrite difficult Sino-Korean, technical, and loanword expressions more actively. Keep every fact, date, name, and obligation, and split long sentences into very easy professional Korean.",
        }[normalized_intensity]

        system_prompt = f"""
You are DocAssist, a Korean business document understanding assistant.
Convert difficult Korean business writing into easy business Korean, not childish language.
Intensity: {normalized_intensity} - {intensity_guide}

Analyze the provided text and output a JSON object.
The output must strictly follow this schema:
{{
  "summary": "A concise Korean summary of the entire document",
  "converted_text": "The converted Korean text",
  "terms": [
    {{"term": "Term", "replacement": "Easy business expression", "definition": "Definition in Korean", "para": 1, "snippet": "Source sentence"}}
  ],
  "rules": [
    {{"title": "Action/Condition/Date/Amount", "desc": "Important extracted item", "source": "Paragraph number or context"}}
  ],
  "paragraphs": [
    {{
      "original": "Original paragraph text",
      "easy": "Converted easy business Korean",
      "summary": "Paragraph core summary",
      "bullets": ["Key point 1", "Key point 2"],
      "todo": ["Action item"],
      "dates": ["Important date"],
      "amounts": ["Amount"],
      "conditions": ["Condition"],
      "owners": ["Responsible person/team"],
      "changed_terms": [{{"from": "original expression", "to": "easy expression", "definition": "meaning"}}]
    }}
  ]
}}

Guidelines:
1. Use Korean for every explanation and converted sentence.
2. Preserve business meaning. Do not invent obligations not present in the document.
3. Process the main paragraphs in order. If the document is long, include the most important paragraphs.
4. Extract action items, dates, amounts, conditions, owners, and difficult term explanations when present.
5. Do not replace ordinary words that are already easy, such as "일정". Keep replacements concise and preferably no longer than the source expression.
6. Rewrite complete Korean expressions, including endings and particles. Never make broken forms such as "맞추기해야", "할 수 없음한", or "의견해 주시기".
7. Make the three levels observably different: close changes only highly formal terms, easy also changes normal business jargon, and summary additionally simplifies sentence structure.
8. Return only valid JSON.
"""

        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze and convert this text:\n\n{context_text}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=4000,
            )

            content = response.choices[0].message.content
            result = self._sanitize_analysis_changes(json.loads(content))
            result.setdefault("intensity", normalized_intensity)
            result.setdefault("intensity_label", fallback_result["intensity_label"])
            result.setdefault("converted_text", "\n\n".join(p.get("easy", "") for p in result.get("paragraphs", [])))
            if self._fallback_has_more_changed_terms(fallback_result, result):
                return fallback_result
            if self._is_low_quality_analysis(text, result):
                return fallback_result
            return result
        except Exception:
            print("Error analyzing document with LLM. Falling back to local conversion.")
            return fallback_result

    def _sanitize_analysis_changes(self, result: dict[str, Any]) -> dict[str, Any]:
        """부자연스럽게 길어진 변경은 원문으로 되돌리고 변경 목록에서도 제외합니다."""
        allowed_pairs: set[tuple[str, str]] = set()
        for paragraph in result.get("paragraphs") or []:
            original = str(paragraph.get("original") or "")
            easy = str(paragraph.get("easy") or original)
            kept_terms: list[dict[str, Any]] = []
            for term in paragraph.get("changed_terms") or []:
                source = str(term.get("from") or "").strip()
                replacement = str(term.get("to") or "").strip()
                if is_meaningful_change(source, replacement):
                    kept_terms.append(term)
                    allowed_pairs.add((source, replacement))
                elif source and replacement and source in original:
                    easy = easy.replace(replacement, source)
            paragraph["easy"] = easy
            paragraph["changed_terms"] = kept_terms

        result["terms"] = [
            term
            for term in result.get("terms") or []
            if (
                str(term.get("term") or "").strip(),
                str(term.get("replacement") or "").strip(),
            ) in allowed_pairs
        ]
        result["converted_text"] = "\n\n".join(
            str(paragraph.get("easy") or paragraph.get("original") or "").strip()
            for paragraph in result.get("paragraphs") or []
            if str(paragraph.get("easy") or paragraph.get("original") or "").strip()
        )
        return result

    def _is_low_quality_analysis(self, source_text: str, result: dict[str, Any]) -> bool:
        converted = str(result.get("converted_text") or "").strip()
        paragraphs = result.get("paragraphs") or []
        if not converted or not paragraphs:
            return True

        generic_phrases = (
            "문서를 분석",
            "분석한 텍스트",
            "제공된 텍스트",
            "요약한 한국어",
            "converted korean text",
            "original paragraph text",
        )
        lowered = converted.lower()
        if any(phrase in lowered for phrase in generic_phrases):
            return True

        source_tokens = set(re.findall(r"[가-힣A-Za-z0-9]{2,}", source_text))
        converted_tokens = set(re.findall(r"[가-힣A-Za-z0-9]{2,}", converted))
        if source_tokens and len(source_text.strip()) <= 500:
            overlap = len(source_tokens & converted_tokens) / max(1, len(source_tokens))
            if overlap < 0.25:
                return True

        return False

    def _fallback_has_more_changed_terms(self, fallback_result: dict[str, Any], result: dict[str, Any]) -> bool:
        fallback_count = sum(
            len(paragraph.get("changed_terms") or [])
            for paragraph in fallback_result.get("paragraphs", [])
        )
        result_count = sum(
            len(paragraph.get("changed_terms") or [])
            for paragraph in result.get("paragraphs", [])
        )
        return fallback_count > result_count


processor = DocumentProcessor()
