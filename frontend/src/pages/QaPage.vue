<template>
  <AppLayout>
    <main class="doq-qa">
      <header class="doq-qa-head">
        <span class="doq-qa-logo"><MessageSquareText :size="19" /></span>
        <div><h1>무엇이든 물어보기</h1><small>{{ selectedDoc ? `${selectedDoc.title} 내용으로 답해 드려요.` : "문서 없이 일반적인 질문에 답해요." }}</small></div>
      </header>

      <div class="doq-picker-wrap">
        <button class="doq-doc-picker" type="button" :aria-expanded="docPickerOpen" @click="docPickerOpen = !docPickerOpen">
          <FileText :size="16" />
          <span>{{ selectedDoc?.title || "문서 없이 질문" }}</span>
          <ChevronDown :size="15" />
        </button>
        <div v-if="docPickerOpen" class="doq-doc-menu">
          <label><Search :size="15" /><input v-model.trim="docQuery" placeholder="문서 검색" /></label>
          <div class="doq-doc-options">
            <button type="button" @click="pickDocument('')"><span class="general"><MessageSquareText :size="14" /></span><em>문서 없이 질문</em></button>
            <button v-for="doc in filteredDocs" :key="doc.id" type="button" :disabled="doc.status !== 'DONE'" @click="pickDocument(doc.id)"><span>{{ doc.type }}</span><em>{{ doc.title }}</em><small v-if="doc.status !== 'DONE'">{{ documentStatusLabel(doc.status) }}</small></button>
            <p v-if="filteredDocs.length === 0">검색 결과가 없어요.</p>
          </div>
        </div>
      </div>

      <section ref="chatRef" class="doq-chat">
        <article v-if="messages.length === 0" class="doq-message assistant">
          <span class="doq-assistant"><Search :size="16" :stroke-width="2.5" /></span>
          <div class="doq-bubble">
            <template v-if="selectedDoc">선택한 문서에서 궁금한 점을 물어보세요. 답변은 문서 내용 안에서 찾고 근거 문단도 함께 보여드려요.</template>
            <template v-else>안녕하세요! 문서 없이도 궁금한 걸 편하게 물어보세요. 예를 들어 <strong>“전세와 월세는 뭐가 달라요?”, “계약할 때 조심할 점은?”</strong> 같은 질문도 좋아요. 위에서 문서를 고르면 그 문서 내용으로 답해 드려요.</template>
          </div>
        </article>

        <article v-for="message in messages" :key="message.id" :class="['doq-message', message.role]">
          <span v-if="message.role === 'assistant'" class="doq-assistant"><Search :size="16" :stroke-width="2.5" /></span>
          <div>
            <div class="doq-bubble"><p v-for="(line, index) in message.text.split('\n')" :key="index">{{ line }}</p></div>
            <div v-if="message.role === 'assistant' && message.citations?.length" class="doq-citations">
              <button v-for="citation in message.citations" :key="citation.citeId" type="button" @click="selectEvidence(citation)">{{ citationLabel(citation) }}</button>
            </div>
          </div>
        </article>
      </section>

      <article v-if="activeEvidence" class="doq-evidence">
        <div><strong>답변 근거</strong><span>{{ citationLabel(activeEvidence) }}</span></div>
        <p>{{ activeEvidence.quote }}</p>
        <button type="button" @click="clearEvidence">닫기</button>
      </article>

      <form class="doq-composer" @submit.prevent="send">
        <input v-model="input" :placeholder="selectedDoc ? '이 문서에서 궁금한 내용을 물어보세요.' : '궁금한 내용을 입력하세요.'" :disabled="sending" />
        <button type="submit" aria-label="메시지 전송" :disabled="sending || !input.trim()"><ArrowRight :size="19" /></button>
      </form>
      <div v-if="toast" class="toast">{{ toast }}</div>
    </main>


  </AppLayout>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { ArrowRight, ChevronDown, FileText, MessageSquareText, Search } from "@lucide/vue";
import documentService from "../api/document.service";
import chatService from "../api/chat.service";
import AppLayout from "../components/layout/AppLayout.vue";

type DocType = "PDF" | "JPG" | "PNG" | "TXT" | "UNK";
type DocStatus = "QUEUED" | "PROCESSING" | "DONE" | "FAILED";
interface DocItem { id: string; title: string; type: DocType; status: DocStatus; }
interface Citation { citeId: string; section: string; page: number; score: number; quote: string; }
type Role = "user" | "assistant";
interface ChatMsg { id: string; role: Role; text: string; at: string; citations?: Citation[]; }
const route = useRoute();
let initializingScope = true;
const docs = ref<DocItem[]>([]);
const selectedDocId = ref("");
const selectedDoc = computed(() => docs.value.find((doc) => doc.id === selectedDocId.value) ?? null);
const docPickerOpen = ref(false);
const docQuery = ref("");
const filteredDocs = computed(() => {
  const keyword = docQuery.value.toLocaleLowerCase("ko-KR");
  return keyword ? docs.value.filter((doc) => doc.title.toLocaleLowerCase("ko-KR").includes(keyword)) : docs.value;
});
const currentSessionId = ref<string | null>(null);
const input = ref("");
const messages = ref<ChatMsg[]>([]);
const sending = ref(false);
const activeEvidence = ref<Citation | null>(null);
const chatRef = ref<HTMLElement | null>(null);
const toast = ref("");
let toastTimer: number | undefined;

function showToast(message: string) {
  toast.value = message;
  if (toastTimer) window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => (toast.value = ""), 1800);
}
function clearEvidence() { activeEvidence.value = null; }
function selectEvidence(citation: Citation) { activeEvidence.value = citation; }
function documentStatusLabel(status: DocStatus) {
  if (status === "FAILED") return "분석 실패";
  if (status === "PROCESSING") return "분석 중";
  return "분석 대기";
}
function citationLabel(citation: Citation) {
  if (citation.section === "요약") return "문서 요약";
  const number = citation.section.match(/(?:문단|청크)\s*(\d+)/)?.[1];
  return number ? `${number}번 문단` : citation.section;
}
function pickDocument(id: string) {
  const document = docs.value.find((doc) => doc.id === id);
  if (document && document.status !== "DONE") {
    showToast("문서 분석이 완료된 후 선택할 수 있습니다.");
    return;
  }
  selectedDocId.value = id;
  docPickerOpen.value = false;
  docQuery.value = "";
}
async function loadDocuments() {
  try {
    const response = await documentService.getDocuments(0, 100);
    docs.value = response.data.map((doc: any) => ({ id: doc.id, title: doc.title, type: (doc.file_type || "UNK").toUpperCase(), status: doc.status }));
  } catch (error) { console.error("Failed to load documents", error); showToast("문서 목록을 불러오지 못했습니다."); }
}
async function loadSessionForScope(docId: string | null) {
  try {
    const sessions = (await chatService.getSessions(0, 50)).data;
    const match = sessions.find((session: any) => docId ? session.document_id === docId : !session.document_id);
    if (match) {
      currentSessionId.value = match.id;
      const hasLegacyConnectionMessage = await loadMessages(match.id);
      if (!docId && hasLegacyConnectionMessage) {
        const session = await chatService.createSession("일반 질문");
        currentSessionId.value = session.data.id;
        messages.value = [];
      }
    } else {
      const title = docId ? `${docs.value.find((doc) => doc.id === docId)?.title || "문서"} Q&A` : "일반 질문";
      const session = await chatService.createSession(title, docId || undefined);
      currentSessionId.value = session.data.id;
      messages.value = [];
    }
  } catch (error) { console.error("Session load failed", error); showToast("대화 세션을 불러오지 못했습니다."); }
}
async function loadMessages(sessionId: string): Promise<boolean> {
  try {
    const response = await chatService.getMessages(sessionId);
    messages.value = response.data.map((message: any) => ({ id: message.id, role: message.role, text: message.content, at: message.created_at, citations: message.citations || [] }));
    await nextTick();
    scrollToBottom();
    return messages.value.some((message) => message.role === "assistant" && message.text.includes("일반 질문 답변은 LLM 연결이 필요합니다"));
  } catch (error) { console.error("Message load failed", error); return false; }
}
async function send() {
  const question = input.value.trim();
  if (!question) return;
  if (!currentSessionId.value) await loadSessionForScope(selectedDocId.value || null);
  if (!currentSessionId.value) { showToast("대화 세션을 만들지 못했습니다."); return; }
  sending.value = true;
  messages.value.push({ id: `temp_${Date.now()}`, role: "user", text: question, at: new Date().toISOString() });
  input.value = "";
  await nextTick();
  scrollToBottom();
  try {
    const data = (await chatService.askQuestion(currentSessionId.value, question)).data;
    const answer: ChatMsg = { id: data.id, role: "assistant", text: data.content, at: data.created_at, citations: data.citations || [] };
    messages.value.push(answer);
  } catch (error: any) { console.error("Send failed", error); showToast(error?.response?.data?.detail || "메시지 전송에 실패했습니다."); }
  finally { sending.value = false; await nextTick(); scrollToBottom(); }
}
function scrollToBottom() { if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight; }

onMounted(async () => {
  await loadDocuments();
  const requestedDocumentId = typeof route.query.documentId === "string" ? route.query.documentId : "";
  if (requestedDocumentId && docs.value.some((doc) => doc.id === requestedDocumentId)) selectedDocId.value = requestedDocumentId;
  if (typeof route.query.question === "string") input.value = route.query.question;
  await loadSessionForScope(selectedDocId.value || null);
  initializingScope = false;
});
watch(selectedDocId, async (newValue) => {
  if (initializingScope) return;
  activeEvidence.value = null;
  await loadSessionForScope(newValue || null);
});
</script>


<style scoped>
.doq-qa { width: min(900px, 100%); height: 100vh; margin: 0 auto; padding: 24px 34px; display: flex; flex-direction: column; }
.doq-qa-head { margin-bottom: 16px; padding-bottom: 16px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid var(--line); }
.doq-qa-logo, .doq-assistant { display: grid; place-items: center; flex: none; color: #fff; background: var(--accent-gradient); }
.doq-qa-logo { width: 38px; height: 38px; border-radius: 11px; }.doq-qa-head > div { min-width: 0; display: grid; flex: 1; }.doq-qa-head h1 { margin: 0; font-size: 16px; }.doq-qa-head small { margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--muted); font-size: 12.5px; }
.doq-picker-wrap { position: relative; width: fit-content; max-width: 340px; margin-bottom: 16px; }
.doq-doc-picker { width: fit-content; max-width: 340px; height: 40px; padding: 0 11px 0 13px; display: flex; align-items: center; gap: 8px; border: 1px solid var(--line); border-radius: 12px; color: var(--accent); background: var(--surface); cursor: pointer; }
.doq-doc-picker > span { min-width: 0; max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--sub); font-size: 13px; font-weight: 600; }
.doq-doc-picker > svg:last-child { color: var(--muted); }
.doq-doc-menu { position: absolute; z-index: 20; top: 46px; left: 0; width: 340px; padding: 10px; border: 1px solid var(--line); border-radius: 14px; background: var(--surface); box-shadow: 0 14px 36px rgb(32 25 68 / .14); }
.doq-doc-menu > label { height: 38px; padding: 0 11px; display: flex; align-items: center; gap: 8px; border: 1px solid var(--line); border-radius: 10px; color: var(--muted); background: var(--soft); }
.doq-doc-menu input { min-width: 0; flex: 1; border: 0; outline: 0; color: var(--ink); background: transparent; font-size: 13px; }
.doq-doc-options { max-height: 248px; margin-top: 7px; display: flex; flex-direction: column; gap: 2px; overflow-y: auto; }
.doq-doc-options button { width: 100%; min-width: 0; padding: 8px; display: flex; align-items: center; gap: 10px; border: 0; border-radius: 9px; color: var(--sub); background: transparent; text-align: left; cursor: pointer; }
.doq-doc-options button:hover { background: var(--soft); }
.doq-doc-options button:disabled { opacity: .55; cursor: not-allowed; }
.doq-doc-options button > span { width: 32px; height: 30px; display: grid; place-items: center; flex: none; border-radius: 8px; color: #e14a6b; background: #fdecef; font-size: 9px; font-weight: 700; }
.doq-doc-options button > span.general { color: var(--accent); background: var(--accent-soft); }
.doq-doc-options em { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 12.5px; font-style: normal; font-weight: 600; }
.doq-doc-options button > small { margin-left: auto; color: var(--muted); font-size: 10.5px; white-space: nowrap; }
.doq-doc-options p { margin: 0; padding: 14px 8px; color: var(--muted); text-align: center; font-size: 12px; }
.doq-chat { min-height: 0; padding-right: 6px; display: flex; flex: 1; flex-direction: column; gap: 18px; overflow-y: auto; }
.doq-message { max-width: 82%; display: flex; gap: 11px; }.doq-message.user { align-self: flex-end; }.doq-message.assistant { align-self: flex-start; }
.doq-assistant { width: 32px; height: 32px; margin-top: 2px; border-radius: 10px; }
.doq-bubble { padding: 15px 18px; border: 1px solid var(--line); border-radius: 18px 18px 18px 5px; color: var(--sub); background: var(--surface); font-size: 14.5px; line-height: 1.75; }
.doq-bubble p { margin: 0; white-space: pre-wrap; }.doq-bubble p + p { margin-top: 8px; }
.doq-message.user .doq-bubble { border: 0; border-radius: 18px 18px 5px 18px; color: #fff; background: var(--accent-gradient); }
.doq-citations { margin-top: 9px; display: flex; flex-wrap: wrap; gap: 7px; }.doq-citations button { padding: 5px 10px; border: 1px solid #e7e3f6; border-radius: 999px; color: var(--accent); background: var(--soft); font-size: 11.5px; font-weight: 600; cursor: pointer; }
.doq-evidence { position: relative; margin: 10px 0 0 43px; padding: 12px 44px 12px 14px; border: 1px solid var(--accent-border); border-radius: 12px; background: var(--accent-soft); }
.doq-evidence > div { display: flex; gap: 8px; font-size: 12px; }.doq-evidence span { color: var(--muted); }.doq-evidence p { margin: 5px 0 0; color: var(--sub); font-size: 12.5px; line-height: 1.6; }.doq-evidence > button { position: absolute; top: 9px; right: 10px; border: 0; color: var(--muted); background: transparent; font-size: 12px; cursor: pointer; }
.doq-composer { margin-top: 18px; padding: 7px 7px 7px 18px; display: flex; align-items: center; gap: 10px; border: 1.5px solid var(--line); border-radius: 16px; background: var(--surface); }.doq-composer:focus-within { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.doq-composer input { min-width: 0; flex: 1; border: 0; outline: 0; color: var(--ink); background: transparent; font-size: 14.5px; }.doq-composer > button { width: 42px; height: 42px; display: grid; place-items: center; flex: none; border: 0; border-radius: 12px; color: #fff; background: var(--accent-gradient); cursor: pointer; }.doq-composer > button:disabled { opacity: .45; cursor: default; }
@media (max-width: 620px) { .doq-qa { padding: 18px 16px; }.doq-message { max-width: 92%; }.doq-qa-head small { max-width: 220px; }.doq-picker-wrap, .doq-doc-picker { max-width: 100%; }.doq-doc-picker > span { max-width: calc(100vw - 145px); }.doq-doc-menu { width: min(340px, calc(100vw - 32px)); } }
</style>
