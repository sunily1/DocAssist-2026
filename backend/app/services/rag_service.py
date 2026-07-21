from typing import List, Optional
from uuid import UUID
import re

from openai import AsyncOpenAI, AuthenticationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import DocumentAnalysis, DocumentEmbedding
from app.schemas.chat import ChatMessageCreate
from app.services.document_processor import processor


def build_openai_client() -> AsyncOpenAI:
    client_options = {"api_key": settings.OPENAI_API_KEY}
    if settings.OPENAI_BASE_URL:
        client_options["base_url"] = settings.OPENAI_BASE_URL
    return AsyncOpenAI(**client_options)


class RAGService:
    """Generate chat answers with optional document context."""

    def __init__(self):
        self.client = build_openai_client()
        self.model_name = settings.OPENAI_QA_MODEL
        self._authentication_failed = False

    def _can_use_llm(self) -> bool:
        key = (settings.OPENAI_API_KEY or "").strip()
        return bool(
            not self._authentication_failed
            and key
            and (settings.OPENAI_BASE_URL or key.startswith("sk-"))
        )

    def _tokens(self, text: str) -> set[str]:
        return set(re.findall(r"[가-힣A-Za-z0-9]{2,}", (text or "").lower()))

    def _score_text(self, query: str, text: str) -> int:
        query_tokens = self._tokens(query)
        text_tokens = self._tokens(text)
        if not query_tokens or not text_tokens:
            return 55
        overlap = len(query_tokens & text_tokens)
        ratio = overlap / max(len(query_tokens), 1)
        return max(35, min(96, int(45 + ratio * 50 + overlap * 4)))

    def _has_lexical_overlap(self, query: str, text: str) -> bool:
        query_tokens = self._tokens(query)
        return bool(query_tokens and query_tokens & self._tokens(text))

    def _make_citation(self, idx: int, section: str, score: int, quote: str) -> dict:
        return {
            "citeId": f"doc-{idx}",
            "section": section,
            "page": 1,
            "score": score,
            "quote": quote[:700],
        }

    def _compact_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", (value or "").replace("---", " ")).strip()

    async def get_embedding(self, text: str) -> List[float]:
        if not self._can_use_llm():
            return []
        try:
            embeddings = await processor.create_embeddings([text])
            return embeddings[0] if embeddings else []
        except Exception:
            return []

    async def retrieve_context_bundle(
        self,
        db: AsyncSession,
        query: str,
        document_id: Optional[UUID] = None,
        top_k: int = 5,
    ) -> tuple[str, list[dict]]:
        if not document_id:
            return "", []

        context_parts: list[str] = []
        citations: list[dict] = []

        query_embedding = await self.get_embedding(query)
        if query_embedding:
            try:
                stmt = (
                    select(DocumentEmbedding)
                    .filter(DocumentEmbedding.document_id == document_id)
                    .order_by(DocumentEmbedding.embedding.cosine_distance(query_embedding))
                    .limit(top_k)
                )
                result = await db.execute(stmt)
                embeddings = result.scalars().all()
                for idx, emb in enumerate(embeddings, start=1):
                    quote = (emb.chunk_content or "").strip()
                    if not quote or not self._has_lexical_overlap(query, quote):
                        continue
                    section = f"청크 {emb.chunk_index + 1}"
                    score = max(48, 92 - (idx - 1) * 8)
                    context_parts.append(f"[{section}] {quote}")
                    citations.append(self._make_citation(idx, section, score, quote))
            except Exception:
                context_parts = []
                citations = []

        if context_parts:
            return "\n\n---\n\n".join(context_parts), citations

        result = await db.execute(
            select(DocumentAnalysis).filter(DocumentAnalysis.document_id == document_id)
        )
        analysis = result.scalars().first()
        if not analysis:
            return "", []

        candidates: list[tuple[str, str, int]] = []
        if analysis.summary:
            candidates.append(("요약", analysis.summary.strip(), self._score_text(query, analysis.summary)))

        for idx, paragraph in enumerate(analysis.paragraphs or [], start=1):
            pieces = [
                paragraph.get("summary", ""),
                paragraph.get("easy", ""),
                paragraph.get("original", ""),
                " ".join(paragraph.get("todo", []) or []),
                " ".join(paragraph.get("dates", []) or []),
                " ".join(paragraph.get("amounts", []) or []),
                " ".join(paragraph.get("conditions", []) or []),
                " ".join(paragraph.get("owners", []) or []),
            ]
            text = " ".join(str(piece).strip() for piece in pieces if piece and str(piece).strip())
            if text:
                candidates.append((f"문단 {idx}", text, self._score_text(query, text)))

        candidates = [candidate for candidate in candidates if candidate[2] > 45]
        candidates.sort(key=lambda item: item[2], reverse=True)
        for idx, (section, text, score) in enumerate(candidates[:top_k], start=1):
            quote = text[:700]
            context_parts.append(f"[{section}] {quote}")
            citations.append(self._make_citation(idx, section, score, quote))

        return "\n\n---\n\n".join(context_parts), citations

    def _context_blocks(self, context: str) -> list[str]:
        blocks: list[str] = []
        for raw in context.split("---"):
            cleaned = self._compact_text(raw)
            cleaned = re.sub(r"^\[[^\]]+\]\s*", "", cleaned)
            if cleaned:
                blocks.append(cleaned)
        return blocks

    def _fallback_answer(self, query: str, context: str, document_id: Optional[UUID]) -> str:
        if document_id and context:
            snippets = [block[:160] for block in self._context_blocks(context)[:3]]
            if snippets:
                return "문서에서 확인한 관련 내용입니다.\n" + "\n".join(f"- {snippet}" for snippet in snippets)
            return "선택한 문서에서 질문과 관련된 내용을 찾지 못했습니다."
        if document_id:
            return "선택한 문서에서 질문과 관련된 내용을 찾지 못했습니다. 문서 분석이 완료됐는지 확인해 주세요."
        return "지금은 AI 연결이 원활하지 않아 일반 답변을 만들지 못했어요. 잠시 후 다시 시도해 주세요."

    def _extract_answer_content(self, response) -> str:
        message = response.choices[0].message
        content = getattr(message, "content", None)
        if content:
            return content

        reasoning = getattr(message, "reasoning", None)
        if reasoning:
            return reasoning

        tool_calls = getattr(message, "tool_calls", None) or []
        if tool_calls:
            return "모델이 도구 호출 형식으로 응답해 표시할 일반 답변이 없습니다. 질문을 조금 더 구체적으로 다시 입력해 주세요."

        return "답변을 생성하지 못했습니다."

    async def get_chat_completion(
        self,
        db: AsyncSession,
        query: str,
        messages: List[dict],
        document_id: Optional[UUID] = None,
        model: Optional[str] = None,
        user_settings: dict = None,
    ) -> ChatMessageCreate:
        context = ""
        citations: list[dict] = []
        if document_id:
            context, citations = await self.retrieve_context_bundle(db, query, document_id)

        if document_id and not context:
            return ChatMessageCreate(
                role="assistant",
                content="선택한 문서에서 질문과 관련된 내용을 찾지 못했습니다.",
                model_name=model or self.model_name,
                prompt_tokens=0,
                completion_tokens=0,
                citations=[],
            )

        system_message_content = (
            "You are DocAssist, a Korean business document assistant. "
            "Answer in natural, clear Korean. "
            "Answer the user's exact question first. "
            "Keep the answer concise unless the user asks for detail."
        )

        if user_settings and "assist" in user_settings:
            assist = user_settings["assist"]
            level = assist.get("level", "easy")
            if level in ("summary", "high"):
                system_message_content += "\nFocus on key points, actions, dates, amounts, and conditions."
            elif level in ("close", "low"):
                system_message_content += "\nUse a business tone and simplify only difficult terms."
            else:
                system_message_content += "\nUse easy Korean and explain difficult terms briefly."

        if context:
            system_message_content += (
                "\n\nUse ONLY the selected document context below. "
                "If the answer is not supported by the context, say it is not in the document. "
                "Do not quote long raw paragraphs.\n\n"
                f"{context}"
            )
        else:
            system_message_content += "\n\nNo document is selected. Answer the user's general question normally."

        full_messages = [{"role": "system", "content": system_message_content}] + messages

        if not self._can_use_llm():
            return ChatMessageCreate(
                role="assistant",
                content=self._fallback_answer(query, context, document_id),
                model_name=model or self.model_name,
                prompt_tokens=0,
                completion_tokens=0,
                citations=citations,
            )

        try:
            response = await self.client.chat.completions.create(
                model=model or self.model_name,
                messages=full_messages,
                temperature=0.4,
                max_tokens=1000,
            )
            usage = response.usage
            return ChatMessageCreate(
                role="assistant",
                content=self._extract_answer_content(response),
                model_name=model or self.model_name,
                prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
                citations=citations,
            )
        except AuthenticationError:
            self._authentication_failed = True
            print("ERROR: LLM API authentication failed.")
            return ChatMessageCreate(
                role="assistant",
                content=self._fallback_answer(query, context, document_id),
                model_name=model or self.model_name,
                prompt_tokens=0,
                completion_tokens=0,
                citations=citations,
            )
        except Exception as exc:
            print(f"ERROR: LLM API call failed: {exc}")
            return ChatMessageCreate(
                role="assistant",
                content=self._fallback_answer(query, context, document_id),
                model_name=model or self.model_name,
                prompt_tokens=0,
                completion_tokens=0,
                citations=citations,
            )


rag_service = RAGService()
