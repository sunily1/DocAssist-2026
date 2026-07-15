<!-- 인수인계용: 문서 기반 Q&A 화면 -->
<template>
  <AppLayout v-slot="{ toggleSidebar }">
    <!-- 상단바 -->
    <header class="topbar">
      <div class="tb-left">
        <div class="tb-title">
          <button class="hamburger" @click="toggleSidebar" aria-label="Open menu">☰</button>
          <span class="tb-title-strong">Q&A 챗봇</span>
          <span class="tb-sub">· 문서 질문과 일반 질문을 함께 처리합니다</span>
        </div>
      </div>

      <div class="tb-right">
        <button class="btn btn-outline" type="button" @click="newChat">새 대화</button>
      </div>
    </header>

    <main class="content">
      <!-- 2컬럼 레이아웃 -->
      <section class="grid">
        <!-- 중앙: Q&A 보드 -->
        <section class="card center">
          <div class="qa">
            <div class="qa-head">
              <div class="qa-head-left">
                <div class="qa-title">{{ selectedDoc ? "문서 기반 질문" : "일반 질문" }}</div>
                <div class="doc-context-row">
                  <select v-model="selectedDocId" class="doc-select">
                    <option value="" disabled>문서 선택</option>
                    <option v-for="d in docs" :key="d.id" :value="d.id">
                      {{ d.title }}
                    </option>
                  </select>
                  <button v-if="selectedDocId" class="btn btn-outline btn-sm" type="button" @click="clearSelectedDoc">
                    문서 해제
                  </button>
                </div>
              </div>
              <div class="qa-actions">
                <span class="muted small">메시지 {{ messages.length }}개</span>
              </div>
            </div>

            <div class="qa-body" ref="chatRef">
              <div v-if="messages.length === 0" class="empty">
                아래 입력창에 질문을 적어보세요.
              </div>

              <div v-else class="chat">
                <div
                  v-for="m in messages"
                  :key="m.id"
                  class="msg"
                  :class="m.role"
                >
                  <div class="bubble">
                    <div class="meta">
                      <span class="who">{{ m.role === 'user' ? '나' : 'DocAssist' }}</span>
                      <span class="muted">·</span>
                      <span class="muted">{{ formatTime(m.at) }}</span>
                    </div>

                    <div class="text">
                      <p v-for="(line, idx) in m.text.split('\n')" :key="idx">{{ line }}</p>
                    </div>

                    <div v-if="m.role === 'assistant' && m.citations?.length" class="cite">
                      <div class="cite-title">
                        {{ citeMode === 'top' ? "근거(요약)" : "근거(인라인 요약)" }}
                      </div>
                      <div class="cite-chips">
                        <button
                          v-for="c in m.citations"
                          :key="c.citeId"
                          class="cite-chip"
                          type="button"
                          @click="selectEvidence(c)"
                        >
                          §{{ c.section }} · p{{ c.page }} · {{ c.score }}%
                        </button>
                      </div>
                    </div>

                    <div v-if="m.role === 'assistant'" class="assist-actions">
                      <button class="link" type="button" @click="copyText(m.text)">답변 복사</button>
                      <button class="link" type="button" @click="pinAnswer(m.id)">답변 저장</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <form class="qa-input" @submit.prevent="send">
              <input
                v-model="input"
                class="input"
                :placeholder="inputPlaceholder"
                :disabled="sending"
                @keydown.enter.exact.prevent="send"
              />
              <button class="btn btn-primary" type="submit" :disabled="sending || !input.trim()">
                {{ sending ? "전송..." : "전송" }}
              </button>
            </form>

            <div class="hint muted">
              {{ selectedDoc ? "선택한 문서 내용 안에서만 답변합니다." : "문서를 선택하지 않으면 일반 질문으로 답변합니다." }}
            </div>
          </div>
        </section>

        <!-- 오른쪽: 근거 패널 -->
        <aside class="card right">
          <div class="card-head">
            <h2>근거 패널</h2>
            <div class="head-actions">
              <button class="btn btn-outline btn-sm" type="button" @click="clearEvidence" :disabled="!activeEvidence">
                해제
              </button>
            </div>
          </div>

          <div v-if="!activeEvidence" class="empty">
            답변 아래의 근거 칩(§/p)을 클릭하면<br />
            해당 문단 근거를 여기에서 볼 수 있어요.
          </div>

          <div v-else class="evidence">
            <div class="ev-head">
              <div class="ev-title">섹션 §{{ activeEvidence.section }}</div>
              <div class="muted small">
                page {{ activeEvidence.page }} · score {{ activeEvidence.score }}%
              </div>
            </div>

            <div class="ev-body" :class="{ hl: highlightEvidence }">
              {{ activeEvidence.quote }}
            </div>

            <div class="ev-actions">
              <button class="btn btn-outline btn-sm" type="button" @click="copyText(activeEvidence.quote)">
                근거 복사
              </button>
              <button class="btn btn-sm" type="button" @click="openDocFromEvidence">
                문서에서 보기
              </button>
            </div>

          </div>

          <div class="sep"></div>

          <div class="card-head">
            <h2>저장한 답변</h2>
          </div>

          <div v-if="pinned.length === 0" class="empty small">
            저장한 답변이 없어요.
          </div>

          <ul v-else class="pin-list">
            <li v-for="p in pinned" :key="p.id" class="pin-item">
              <div class="pin-text">{{ p.text }}</div>
              <button class="link" type="button" @click="removePin(p.id)">삭제</button>
            </li>
          </ul>
        </aside>
      </section>

      <div v-if="toast" class="toast">{{ toast }}</div>
    </main>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import documentService from "../api/document.service";
import chatService from "../api/chat.service";
import AppLayout from "../components/layout/AppLayout.vue";

type DocType = "PDF" | "JPG" | "PNG" | "TXT" | "UNK";
interface DocItem {
  id: string;
  title: string;
  type: DocType;
}

interface Citation {
  citeId: string;
  section: string;
  page: number;
  score: number;
  quote: string;
}

type Role = "user" | "assistant";
interface ChatMsg {
  id: string;
  role: Role;
  text: string;
  at: string; // ISO 형식
  citations?: Citation[];
}

interface PinItem {
  id: string;
  text: string;
}

const router = useRouter();
const route = useRoute();
let initializingScope = true;

// API로 불러올 문서 목록
const docs = ref<DocItem[]>([]);

const selectedDocId = ref<string>("");
const selectedDoc = computed(() => docs.value.find((d) => d.id === selectedDocId.value) ?? null);
const inputPlaceholder = computed(() =>
  selectedDoc.value
    ? "예) 이 문서에서 보유기간은 얼마나야?"
    : "예) 어려운 업무 표현 뜻을 알려줘"
);

// 채팅 세션 ID (문서별 1개 세션 유지 정책 - 임시)
const currentSessionId = ref<string | null>(null);

const citeMode = ref<"top" | "inline">("top");
const highlightEvidence = ref(true);

const input = ref("");
const messages = ref<ChatMsg[]>([]);
const sending = ref(false);

const activeEvidence = ref<Citation | null>(null);
const pinned = ref<PinItem[]>([]);

const chatRef = ref<HTMLElement | null>(null);

const toast = ref("");
let toastTimer: number | undefined;

function showToast(msg: string) {
  toast.value = msg;
  if (toastTimer) window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => (toast.value = ""), 1800);
}

async function newChat() {
  try {
    const docId = selectedDocId.value || undefined;
    const title = selectedDoc.value ? `${selectedDoc.value.title} Q&A` : "일반 질문";
    const res = await chatService.createSession(title, docId);
    currentSessionId.value = res.data.id;
    messages.value = [];
    activeEvidence.value = null;
    input.value = "";
    showToast("새 대화를 시작했어요");
  } catch (err) {
    console.error(err);
    showToast("대화 생성 실패");
  }
}

function formatTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
}

async function copyText(text: string) {
  try {
    await navigator.clipboard.writeText(text);
    showToast("복사 완료");
  } catch {
    showToast("복사 실패(권한/브라우저 설정 확인)");
  }
}

function pinAnswer(msgId: string) {
  const msg = messages.value.find((m) => m.id === msgId);
  if (!msg) return;
  const short = msg.text.length > 80 ? msg.text.slice(0, 80) + "…" : msg.text;
  pinned.value = [{ id: `${msgId}_${Date.now()}`, text: short }, ...pinned.value].slice(0, 8);
  showToast("답변을 저장했어요");
}

function removePin(id: string) {
  pinned.value = pinned.value.filter((p) => p.id !== id);
}

function clearEvidence() {
  activeEvidence.value = null;
}

function selectEvidence(c: Citation) {
  activeEvidence.value = c;
}

function openDocFromEvidence() {
  const docId = selectedDocId.value;
  if (!docId) return;
  router.push({ name: "documentView", params: { id: docId } }).catch(() => {});
}

function clearSelectedDoc() {
  selectedDocId.value = "";
}

async function loadDocuments() {
  try {
    const res = await documentService.getDocuments(0, 100);
    // 백엔드의 DocumentRead 목록을 DocItem으로 변환
    docs.value = res.data.map((d: any) => ({
      id: d.id,
      title: d.title,
      type: (d.file_type || "UNK").toUpperCase(),
    }));

  } catch (error) {
    console.error("Failed to load documents", error);
    showToast("문서 목록을 불러오지 못했습니다.");
  }
}

// 문서별/일반 질문별 최신 세션을 찾거나 생성
async function loadSessionForScope(docId: string | null) {
  try {
    const res = await chatService.getSessions(0, 50);
    const sessions = res.data;
    const match = sessions.find((s: any) => docId ? s.document_id === docId : !s.document_id);

    if (match) {
      currentSessionId.value = match.id;
      const hasLegacyConnectionMessage = await loadMessages(match.id);
      if (!docId && hasLegacyConnectionMessage) {
        const newSess = await chatService.createSession("일반 질문");
        currentSessionId.value = newSess.data.id;
        messages.value = [];
      }
    } else {
      const title = docId ? `${docs.value.find(d => d.id === docId)?.title || "문서"} Q&A` : "일반 질문";
      const newSess = await chatService.createSession(title, docId || undefined);
      currentSessionId.value = newSess.data.id;
      messages.value = [];
    }
  } catch (error) {
    console.error("Session load failed", error);
    showToast("대화 세션을 불러오지 못했습니다.");
  }
}

async function loadMessages(sessionId: string): Promise<boolean> {
  try {
    const res = await chatService.getMessages(sessionId);
    // 백엔드 메시지를 UI 형식으로 매핑
    messages.value = res.data.map((m: any) => ({
      id: m.id,
      role: m.role,
      text: m.content,
      at: m.created_at,
      citations: m.citations || []
    }));
    await nextTick();
    scrollToBottom();
    return messages.value.some(
      (message) => message.role === "assistant" && message.text.includes("일반 질문 답변은 LLM 연결이 필요합니다")
    );
  } catch (error) {
    console.error("Message load failed", error);
    return false;
  }
}

async function send() {
  const q = input.value.trim();
  if (!q) return;

  if (!currentSessionId.value) {
    await loadSessionForScope(selectedDocId.value || null);
  }
  if (!currentSessionId.value) {
    showToast("대화 세션을 만들지 못했습니다.");
    return;
  }

  sending.value = true;

  // 낙관적 UI 업데이트
  const tempUserMsg: ChatMsg = {
    id: `temp_${Date.now()}`,
    role: "user",
    text: q,
    at: new Date().toISOString(),
  };
  messages.value.push(tempUserMsg);
  input.value = "";
  await nextTick();
  scrollToBottom();

  try {
    // API 호출
    const res = await chatService.askQuestion(currentSessionId.value, q);
    const assistantMsgData = res.data; // ChatMessageRead 응답
    
    const botMsg: ChatMsg = {
      id: assistantMsgData.id,
      role: "assistant",
      text: assistantMsgData.content,
      at: assistantMsgData.created_at,
      citations: assistantMsgData.citations || []
    };
    messages.value.push(botMsg);
    
    if (botMsg.citations && botMsg.citations.length > 0) {
      activeEvidence.value = botMsg.citations[0];
    }

  } catch (error) {
    console.error("Send failed", error);
    showToast("메시지 전송 실패");
  } finally {
    sending.value = false;
    await nextTick();
    scrollToBottom();
  }
}

function scrollToBottom() {
  const el = chatRef.value;
  if (!el) return;
  el.scrollTop = el.scrollHeight;
}

onMounted(async () => {
  await loadDocuments();
  const requestedDocumentId = typeof route.query.documentId === "string" ? route.query.documentId : "";
  if (requestedDocumentId && docs.value.some((doc) => doc.id === requestedDocumentId)) {
    selectedDocId.value = requestedDocumentId;
  }
  if (typeof route.query.question === "string") {
    input.value = route.query.question;
  }
  await loadSessionForScope(selectedDocId.value || null);
  initializingScope = false;
});

watch(selectedDocId, async (newVal) => {
  if (initializingScope) return;
  activeEvidence.value = null;
  await loadSessionForScope(newVal || null);
});
</script>

<style scoped>
  /* Topbar */
.topbar {
  background: var(--topbar-bg);
  border-bottom: 1px solid #e5e7eb;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 18px;
    gap: 12px;
    height: 100%;
  }
  .tb-left {
    display: grid;
    gap: 6px;
  }
  .tb-title {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }
  .tb-title-strong {
    font-weight: 900;
    font-size: 16px;
  }
  .tb-sub {
    color: #6b7280;
    font-size: 12px;
  }
  .tb-meta {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .pill {
    font-size: 12px;
    padding: 2px 10px;
    border-radius: 999px;
    border: 1px solid #e5e7eb;
    background: #f9fafb;
    font-weight: 800;
  }
  .muted {
    color: #6b7280;
    font-size: 12px;
  }
  .small {
    font-size: 12px;
  }
  .tb-right {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
  }
  
  /* Content */
.content {
  max-width: 1480px;
  width: 100%;
  margin: 0 auto;
  padding: 16px 12px 32px;
  display: grid;
  gap: 16px;
  justify-items: stretch;
}
  
  /* Grid */
  .grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 360px;
    gap: 14px;
    align-items: stretch;
  }
  
  /* Cards */
.card {
  background: var(--card);
  border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 16px;
    position: relative;
  }
  .card.center,
  .card.right {
    display: flex;
    flex-direction: column;
    min-height: 520px;
    height: clamp(520px, calc(100vh - 220px), 900px);
    overflow: hidden;
  }
  .card-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 10px;
  }
  .card-head h2 {
    margin: 0;
    font-size: 16px;
    font-weight: 900;
  }
  
  .sep {
    height: 1px;
    background: #eef2f7;
    margin: 14px 0;
  }
  
  .empty {
    padding: 14px;
    border: 1px dashed #e5e7eb;
    border-radius: 14px;
    color: #6b7280;
    background: #fafafa;
  }
  .empty.big {
    padding: 20px;
  }
  
  /* Q&A board */
  .qa {
    display: grid;
    grid-template-rows: auto 1fr auto;
    flex: 1 1 auto;
    min-height: 0;
  }
  .qa-head {
    padding: 6px 12px 12px;
    border-bottom: 1px solid #eef2f7;
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: center;
  }
  .qa-head-left {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .qa-title {
    font-weight: 900;
  }

.doc-context-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.doc-select {
  padding: 6px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #374151;
  background-color: var(--card);
  max-width: 400px;
  outline: none;
}
  .doc-select:focus {
    border-color: #93c5fd;
  }
  .qa-sub {
    margin-top: 4px;
  }
  .qa-actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }
.qa-body {
  padding: 12px 2px;
  background: var(--bg);
  overflow: auto;
  border: 1px solid #eef2f7;
    border-radius: 14px;
  }
  .chat {
    display: grid;
    gap: 10px;
  }
  .msg {
    display: flex;
  }
  .msg.user {
    justify-content: flex-end;
  }
  .msg.assistant {
    justify-content: flex-start;
  }
.bubble {
  max-width: 78%;
  min-width: 0;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid #e5e7eb;
  background: var(--card);
  overflow-wrap: anywhere;
}
  .msg.user .bubble {
    background: #2563eb;
    border-color: #2563eb;
    color: #fff;
  }
  .meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }
  .who {
    font-weight: 900;
    font-size: 12px;
  }
  .text p {
    margin: 0;
    line-height: 1.6;
    font-weight: 700;
    color: inherit;
  }
  .text p + p {
    margin-top: 6px;
  }
  .cite {
    margin-top: 10px;
    border-top: 1px dashed #e5e7eb;
    padding-top: 10px;
  }
  .cite-title {
    font-weight: 900;
    font-size: 12px;
    margin-bottom: 8px;
  }
  .cite-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
.cite-chip {
  border: 1px solid #e5e7eb;
  background: var(--card);
  border-radius: 999px;
    padding: 6px 10px;
    font-weight: 900;
    font-size: 12px;
    cursor: pointer;
  }
  .cite-chip:hover {
    background: #f9fafb;
  }
  .assist-actions {
    margin-top: 8px;
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    flex-wrap: wrap;
  }
  .qa-input {
    margin-top: 12px;
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 10px;
  }
.input {
  width: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 10px 12px;
  outline: none;
  background: var(--card);
}
  .input:focus {
    border-color: #93c5fd;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  }
  .hint {
    margin-top: 8px;
  }
  
  /* Right evidence */
  .evidence {
    display: grid;
    gap: 10px;
  }
  .ev-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 10px;
  }
  .ev-title {
    font-weight: 900;
    font-size: 14px;
  }
.ev-body {
  border: 1px solid #eef2f7;
  border-radius: 14px;
  padding: 12px;
  background: var(--card);
  line-height: 1.7;
    color: #374151;
    font-weight: 700;
  }
  .ev-body.hl {
    background: #fff7ed;
    border-color: #fed7aa;
  }
  .ev-actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }
  .ev-note {
    margin-top: 6px;
  }
  
  .pin-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    gap: 10px;
  }
  .pin-item {
    border: 1px solid #eef2f7;
    border-radius: 14px;
    padding: 10px;
    display: grid;
    gap: 8px;
  }
  .pin-text {
    font-weight: 800;
    color: #374151;
    font-size: 13px;
    line-height: 1.5;
  }
  
  /* Buttons */
.btn {
  border: 1px solid #e5e7eb;
  background: var(--card);
  padding: 10px 12px;
    border-radius: 12px;
    font-weight: 900;
    cursor: pointer;
  }
  .btn:hover {
    background: #f9fafb;
  }
  .btn-primary {
    background: #2563eb;
    border-color: #2563eb;
    color: #fff;
  }
  .btn-primary:hover {
    background: #1d4ed8;
  }
  .btn-outline {
    border-color: #cbd5e1;
  }
  .btn-sm {
    padding: 8px 10px;
    border-radius: 10px;
  }
  
  .link {
    border: none;
    background: transparent;
    color: #2563eb;
    font-weight: 900;
    cursor: pointer;
    padding: 6px 8px;
    border-radius: 10px;
  }
  .link:hover {
    background: #eff6ff;
  }
  
  .toast {
    position: fixed;
    left: 50%;
    bottom: 18px;
    transform: translateX(-50%);
    padding: 10px 12px;
    border-radius: 14px;
    font-weight: 900;
    border: 1px solid #a7f3d0;
    background: #ecfdf5;
    color: #065f46;
  }
  
  @media (max-width: 1160px) {
    .grid {
      grid-template-columns: 1fr;
    }
    .card.center,
    .card.right {
      height: auto;
      min-height: 0;
    }
  }
  
  .hamburger {
    display: none;
    font-size: 20px;
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 0;
    margin-right: 8px;
  }

  @media (max-width: 820px) {
    .hamburger {
      display: inline-flex;
    }
    .content {
      padding: 18px 14px 30px;
    }
  }
  </style>
