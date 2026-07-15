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
from app.services.easy_converter import build_easy_conversion, has_valid_openai_key, normalize_intensity


def build_openai_client():
    client_options = {"api_key": settings.OPENAI_API_KEY}
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
        """분석 문단을 추출 순서에 맞춰 PDF 블록에 연결합니다."""
        converted = [
            str(paragraph.get("easy") or paragraph.get("original") or "").strip()
            for paragraph in paragraphs
        ]
        block_index = 0
        for page in layout:
            for block in page.get("blocks", []):
                if block_index < len(converted) and converted[block_index]:
                    block["easy"] = converted[block_index]
                block_index += 1
        return layout

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
        """원본 페이지/그래픽을 유지하고 텍스트 블록만 변환문으로 덮어씁니다."""
        layout = self.attach_converted_pdf_text(self.extract_pdf_layout(file_path), paragraphs)
        font_path = self._pdf_font_path()
        if not font_path:
            raise RuntimeError("Korean PDF font is not available")

        with fitz.open(file_path) as doc:
            for page_index, page_layout in enumerate(layout):
                if page_index >= len(doc):
                    break
                page = doc[page_index]
                font_name = f"docassist_ko_{page_index}"

                for block in page_layout.get("blocks", []):
                    original = str(block.get("original") or "").strip()
                    easy = str(block.get("easy") or original).strip()
                    if not easy or easy == original:
                        continue

                    rect = fitz.Rect(block.get("bbox", []))
                    rect.intersect(page.rect)
                    if rect.is_empty or rect.width < 2 or rect.height < 2:
                        continue

                    cover = fitz.Rect(rect.x0 - 0.8, rect.y0 - 0.8, rect.x1 + 0.8, rect.y1 + 0.8)
                    cover.intersect(page.rect)
                    page.draw_rect(cover, color=None, fill=(1, 1, 1), overlay=True)

                    start_size = min(float(block.get("font_size") or 10), max(6.0, rect.height * 0.78))
                    inserted = False
                    size = start_size
                    while size >= 4.5:
                        shape = page.new_shape()
                        remaining = shape.insert_textbox(
                            rect,
                            easy,
                            fontname=font_name,
                            fontfile=font_path,
                            fontsize=size,
                            color=self._pdf_text_color(block.get("color")),
                            lineheight=1.08,
                        )
                        if remaining >= 0:
                            shape.commit(overlay=True)
                            inserted = True
                            break
                        size -= 0.5

                    if not inserted:
                        fallback = easy[: max(1, int(rect.width / 4.5) * max(1, int(rect.height / 6)))]
                        page.insert_textbox(
                            rect,
                            fallback,
                            fontname=font_name,
                            fontfile=font_path,
                            fontsize=4.5,
                            color=self._pdf_text_color(block.get("color")),
                            lineheight=1.0,
                            overlay=True,
                        )

            return doc.tobytes(garbage=4, deflate=True, clean=True)

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
            "summary": "Prioritize paragraph summaries, action items, dates, amounts, conditions, and responsible teams.",
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
5. Return only valid JSON.
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
            result = json.loads(content)
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
        return fallback_count > 0 and result_count == 0


processor = DocumentProcessor()
