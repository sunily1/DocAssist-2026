<template>
  <AppLayout v-slot="{ toggleSidebar }">
    <header class="topbar">
      <div class="tb-left">
        <button class="hamburger" type="button" aria-label="메뉴 열기" @click="toggleSidebar">☰</button>
        <div class="title-wrap">
          <div class="tb-title-strong">문서 보기</div>
          <div class="tb-sub">{{ docMeta.title || "문서를 불러오는 중" }}</div>
        </div>
      </div>

      <div class="tb-right">
        <span :class="['badge', badgeClass(status)]">{{ statusLabel(status) }}</span>
        <button class="icon-btn" type="button" title="글자 작게" @click="fontDown">A-</button>
        <button class="icon-btn" type="button" title="글자 크게" @click="fontUp">A+</button>
        <button class="btn btn-outline" type="button" :disabled="!originalBlob" @click="downloadOriginal">원본 다운로드</button>
        <button class="btn btn-primary" type="button" :disabled="!isDone" @click="downloadConvertedOriginal">쉬운말 다운로드</button>
      </div>
    </header>

    <main class="content" :style="{ fontSize: `${fontSize}px` }">
      <section v-if="loading" class="state-card">문서를 불러오는 중입니다.</section>

      <section v-else-if="status === 'QUEUED' || status === 'PROCESSING'" class="state-card">
        <div class="state-title">문서를 분석하고 있습니다.</div>
        <div class="muted">원본은 먼저 볼 수 있고, 쉬운말 변환과 요약은 완료되면 자동으로 표시됩니다.</div>
      </section>

      <section v-else-if="status === 'FAILED'" class="state-card error">
        <div class="state-title">문서 분석에 실패했습니다.</div>
        <div class="muted">원본 파일은 볼 수 있습니다. 변환이 필요하면 다시 업로드해 주세요.</div>
      </section>

      <section class="view-switch" aria-label="문서 보기 방식">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab"
          :class="{ active: activeTab === tab.key }"
          type="button"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </section>

      <section v-if="activeTab === 'original' || activeTab === 'converted'" class="reader-layout">
        <section class="document-preview">
          <div class="preview-head">
            <div>
              <div class="preview-title">{{ activeTab === "original" ? "원본 문서" : "쉬운말 문서" }}</div>
              <p>
                {{
                  activeTab === "original"
                    ? "업로드한 파일을 가능한 원래 모양 그대로 보여줍니다."
                    : "원본 모양을 유지하면서 어려운 표현만 쉬운말로 바꾼 화면입니다."
                }}
              </p>
            </div>
            <span class="doc-type">{{ activeTab === "original" ? docMeta.type || "FILE" : "변환본" }}</span>
          </div>

          <button
            v-if="selectedChange"
            class="selected-change"
            type="button"
            title="바뀐 문장 위치로 이동"
            @click="goToChangedLocation"
          >
            <span class="old-word">{{ selectedChange.from }}</span>
            <span class="arrow">→</span>
            <strong>{{ selectedChange.to }}</strong>
            <span v-if="selectedChange.definition" class="muted">{{ selectedChange.definition }}</span>
            <span class="location-hint">위치 보기</span>
          </button>

          <template v-if="activeTab === 'original'">
            <ViewerState
              v-if="originalLoading || originalError"
              :loading="originalLoading"
              :error="originalError"
              @retry="loadOriginalFile(true)"
            />
            <iframe
              v-else-if="isPdf && originalUrl"
              class="file-frame"
              :src="`${originalUrl}#toolbar=1&navpanes=0&view=FitH`"
              title="원본 PDF"
            ></iframe>
            <pre v-else-if="isTxt" ref="originalTxtContainer" class="txt-viewer">{{ originalText }}</pre>
            <div v-else-if="isDocx" ref="originalDocxShell" class="docx-shell">
              <div v-if="originalRenderError" class="viewer-state error">{{ originalRenderError }}</div>
              <div ref="originalDocxContainer" class="docx-container"></div>
            </div>
            <div v-else class="viewer-state">이 파일 형식은 미리보기를 지원하지 않습니다. 다운로드로 확인해 주세요.</div>
          </template>

          <template v-else>
            <ViewerState
              v-if="convertedOriginalLoading || convertedOriginalError"
              :loading="convertedOriginalLoading"
              :error="convertedOriginalError"
              @retry="loadConvertedOriginalFile(true)"
            />
            <iframe
              v-else-if="isPdf && convertedOriginalUrl"
              class="file-frame"
              :src="`${convertedOriginalUrl}#toolbar=1&navpanes=0&view=FitH`"
              title="쉬운말 PDF"
            ></iframe>
            <pre v-else-if="isTxt" ref="convertedTxtContainer" class="txt-viewer">{{ easyText }}</pre>
            <div v-else-if="isDocx" ref="convertedDocxShell" class="docx-shell">
              <div v-if="convertedRenderError" class="viewer-state error">{{ convertedRenderError }}</div>
              <div ref="convertedDocxContainer" class="docx-container"></div>
            </div>
            <div v-else class="viewer-state">쉬운말 미리보기를 지원하지 않는 파일입니다. 다운로드로 확인해 주세요.</div>
          </template>
        </section>

        <aside class="side-panel" aria-label="문서 읽기 도구">
          <section class="side-card">
            <div class="side-title">읽기 흐름</div>
            <div class="step-list">
              <button class="step" type="button" @click="activeTab = 'converted'">
                <span>1</span>
                <strong>쉬운말로 먼저 읽기</strong>
              </button>
              <button class="step" type="button" @click="activeTab = 'original'">
                <span>2</span>
                <strong>필요할 때 원본 확인</strong>
              </button>
              <button class="step" type="button" @click="activeTab = 'compare'">
                <span>3</span>
                <strong>바뀐 문장만 보기</strong>
              </button>
            </div>
          </section>

          <section class="side-card">
            <div class="side-head">
              <div>
                <div class="side-title">바뀐 표현</div>
                <p>{{ changeItems.length }}개 표현이 쉬운말로 바뀌었습니다.</p>
              </div>
              <button v-if="changeSearch" class="small-btn" type="button" @click="changeSearch = ''">초기화</button>
            </div>

            <input
              v-model="changeSearch"
              class="search-input"
              type="search"
              placeholder="표현 검색"
            />

            <div v-if="filteredChangeItems.length" class="change-list">
              <button
                v-for="item in filteredChangeItems"
                :key="item.id"
                class="change-card"
                :class="{ active: selectedChange?.id === item.id }"
                type="button"
                @click="selectChange(item)"
              >
                <span class="change-from">{{ item.from }}</span>
                <span class="change-arrow">→</span>
                <span class="change-to">{{ item.to }}</span>
                <span v-if="item.definition" class="change-definition">{{ item.definition }}</span>
                <span class="change-meta">{{ item.paragraphIndex + 1 }}번 문단</span>
              </button>
            </div>
            <div v-else class="change-empty">표시할 바뀐 표현이 없습니다.</div>
          </section>

          <section v-if="selectedChange" class="side-card selected-info">
            <div class="side-title">선택한 표현</div>
            <div class="selected-words">
              <span class="old-word">{{ selectedChange.from }}</span>
              <span class="arrow">→</span>
              <strong>{{ selectedChange.to }}</strong>
            </div>
            <p>{{ selectedChange.definition || "설명 정보가 없습니다." }}</p>
            <button class="btn btn-outline full-btn" type="button" @click="goToChangedLocation">해당 문장 보기</button>
          </section>

          <section class="side-card">
            <div class="side-title">빠른 저장</div>
            <div class="quick-actions">
              <button class="btn btn-outline full-btn" type="button" :disabled="!isDone" @click="download('summary')">요약 DOCX</button>
              <button class="btn btn-outline full-btn" type="button" :disabled="!isDone" @click="download('comparison')">비교 DOCX</button>
            </div>
          </section>
        </aside>
      </section>

      <section v-else-if="activeTab === 'compare'" class="compare-list">
        <article
          v-for="(paragraph, index) in paragraphs"
          :key="`compare-${index}`"
          :id="compareCardId(index)"
          class="compare-card"
          :class="{ highlighted: selectedChange?.paragraphIndex === index }"
        >
          <div class="para-no">{{ index + 1 }}</div>
          <div class="compare-body">
            <div>
              <div class="mini-label">원문</div>
              <p>{{ paragraph.original || "원문 내용이 없습니다." }}</p>
            </div>
            <div class="down-arrow">↓</div>
            <div>
              <div class="mini-label">쉬운말</div>
              <p class="easy">{{ paragraph.easy || paragraph.original || "변환문이 없습니다." }}</p>
            </div>
            <div v-if="paragraphChanges(index).length" class="inline-changes">
              <button
                v-for="item in paragraphChanges(index)"
                :key="item.id"
                class="change-chip"
                type="button"
                @click="selectChange(item)"
              >
                {{ item.from }} → {{ item.to }}
              </button>
            </div>
          </div>
        </article>
      </section>

      <section v-else class="summary-grid">
        <article class="card">
          <div class="card-title">핵심 요약</div>
          <p>{{ analysis.summary || "요약 정보가 없습니다." }}</p>
        </article>

        <article class="card">
          <div class="card-title">어려운 단어</div>
          <div v-if="terms.length" class="chips">
            <button v-for="term in terms" :key="term.term" class="chip" type="button" @click="selectedTerm = term">
              {{ term.term }}
            </button>
          </div>
          <p v-else class="muted">추출된 어려운 단어가 없습니다.</p>
        </article>

        <article v-if="selectedTerm" class="card term-card">
          <div>
            <div class="card-title">{{ selectedTerm.term }}</div>
            <p>{{ selectedTerm.definition }}</p>
          </div>
          <button class="icon-btn" type="button" @click="selectedTerm = null">닫기</button>
        </article>
      </section>
    </main>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, nextTick, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { renderAsync } from "docx-preview";
import documentService, { type DownloadMode } from "../api/document.service";
import AppLayout from "../components/layout/AppLayout.vue";

type DocStatus = "QUEUED" | "PROCESSING" | "DONE" | "FAILED" | "";
type ViewTab = "converted" | "original" | "compare" | "summary";

interface ChangedTerm {
  from: string;
  to: string;
  definition?: string;
}

interface ParagraphItem {
  original: string;
  easy: string;
  summary?: string;
  changed_terms?: ChangedTerm[];
}

interface TermItem {
  term: string;
  definition: string;
}

interface ChangeItem {
  id: string;
  from: string;
  to: string;
  definition: string;
  paragraphIndex: number;
}

const ViewerState = defineComponent({
  props: {
    loading: { type: Boolean, required: true },
    error: { type: String, required: true },
  },
  emits: ["retry"],
  setup(props, { emit }) {
    return () =>
      props.loading
        ? h("div", { class: "viewer-state" }, "문서를 불러오는 중입니다.")
        : h("div", { class: "viewer-state error" }, [
            h("span", props.error),
            h("button", { class: "btn btn-outline", type: "button", onClick: () => emit("retry") }, "다시 시도"),
          ]);
  },
});

const route = useRoute();
const docId = computed(() => String(route.params.id ?? ""));
const loading = ref(true);
const status = ref<DocStatus>("");
const fontSize = ref(14);
const pollTimer = ref<number | null>(null);
const activeTab = ref<ViewTab>("converted");
const selectedTerm = ref<TermItem | null>(null);
const selectedChange = ref<ChangeItem | null>(null);
const changeSearch = ref("");

const originalDocxContainer = ref<HTMLElement | null>(null);
const convertedDocxContainer = ref<HTMLElement | null>(null);
const originalDocxShell = ref<HTMLElement | null>(null);
const convertedDocxShell = ref<HTMLElement | null>(null);
const originalTxtContainer = ref<HTMLElement | null>(null);
const convertedTxtContainer = ref<HTMLElement | null>(null);
const originalRenderError = ref("");
const convertedRenderError = ref("");

const originalBlob = ref<Blob | null>(null);
const originalUrl = ref("");
const originalText = ref("");
const originalLoading = ref(false);
const originalError = ref("");

const convertedOriginalBlob = ref<Blob | null>(null);
const convertedOriginalUrl = ref("");
const convertedOriginalLoading = ref(false);
const convertedOriginalError = ref("");

const docMeta = reactive({ title: "", type: "" });
const analysis = reactive({ summary: "" });
const paragraphs = ref<ParagraphItem[]>([]);
const terms = ref<TermItem[]>([]);
const convertedText = ref("");

const tabs: Array<{ key: ViewTab; label: string }> = [
  { key: "converted", label: "쉬운말 보기" },
  { key: "original", label: "원본 보기" },
  { key: "compare", label: "바뀐 문장" },
  { key: "summary", label: "요약/용어" },
];

const isDone = computed(() => status.value === "DONE");
const isPdf = computed(() => docMeta.type.toUpperCase() === "PDF");
const isDocx = computed(() => docMeta.type.toUpperCase() === "DOCX");
const isTxt = computed(() => docMeta.type.toUpperCase() === "TXT");
const displayTitle = computed(() => (docMeta.title || "document").replace(/\.[^.]+$/, ""));
const easyText = computed(() => {
  const fromParagraphs = paragraphs.value.map((item) => item.easy || item.original).filter(Boolean).join("\n\n");
  return convertedText.value || fromParagraphs;
});

const changeItems = computed<ChangeItem[]>(() => {
  const seen = new Set<string>();
  const items: ChangeItem[] = [];
  paragraphs.value.forEach((paragraph, paragraphIndex) => {
    (paragraph.changed_terms || []).forEach((term, termIndex) => {
      const from = String(term.from || "").trim();
      const to = String(term.to || "").trim();
      if (!from || !to || from === to) return;
      const key = `${paragraphIndex}:${from}:${to}`;
      if (seen.has(key)) return;
      seen.add(key);
      items.push({
        id: `${paragraphIndex}-${termIndex}-${from}-${to}`,
        from,
        to,
        definition: String(term.definition || "").trim(),
        paragraphIndex,
      });
    });
  });
  return items;
});

const filteredChangeItems = computed(() => {
  const query = changeSearch.value.trim().toLowerCase();
  if (!query) return changeItems.value;
  return changeItems.value.filter((item) =>
    [item.from, item.to, item.definition].some((value) => value.toLowerCase().includes(query)),
  );
});

onMounted(() => {
  const savedTheme = (localStorage.getItem("theme") as "light" | "dark") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
  loadDocument();
});

onUnmounted(() => {
  if (pollTimer.value) window.clearInterval(pollTimer.value);
  clearOriginalUrl();
  clearConvertedOriginalUrl();
});

watch(activeTab, async (value) => {
  if (value === "original") {
    await loadOriginalFile();
    await nextTick();
    await renderOriginalDocx();
  }
  if (value === "converted") {
    await loadConvertedOriginalFile();
    await nextTick();
    await renderConvertedDocx();
  }
});

watch([originalBlob, originalDocxContainer], () => nextTick(renderOriginalDocx));
watch([convertedOriginalBlob, convertedDocxContainer], () => nextTick(renderConvertedDocx));

watch(changeItems, (items) => {
  if (!selectedChange.value && items.length) selectedChange.value = items[0];
});

async function loadDocument() {
  try {
    const res = await documentService.getDocument(docId.value);
    const doc = res.data;

    docMeta.title = doc.title;
    docMeta.type = doc.file_type || "UNKNOWN";
    status.value = doc.status;
    analysis.summary = doc.analysis?.summary || "";
    paragraphs.value = doc.analysis?.paragraphs || [];
    convertedText.value = doc.meta_data?.converted_text || "";
    terms.value = (doc.glossary_terms || []).map((item: any) => ({
      term: item.term,
      definition: item.definition,
    }));

    await loadOriginalFile();
    if (doc.status === "DONE") await loadConvertedOriginalFile();

    if (status.value === "QUEUED" || status.value === "PROCESSING") {
      startPolling();
    } else if (pollTimer.value) {
      window.clearInterval(pollTimer.value);
      pollTimer.value = null;
    }
  } catch (e) {
    console.error("Load failed", e);
    status.value = "FAILED";
  } finally {
    loading.value = false;
    await nextTick();
    await renderOriginalDocx();
    await renderConvertedDocx();
  }
}

function startPolling() {
  if (pollTimer.value) return;
  pollTimer.value = window.setInterval(() => {
    loadDocument();
  }, 2500);
}

async function loadOriginalFile(force = false) {
  if (originalBlob.value && !force) return;
  originalLoading.value = true;
  originalError.value = "";
  try {
    const res = await documentService.getOriginalFile(docId.value);
    originalBlob.value = res.data;
    clearOriginalUrl();
    originalUrl.value = URL.createObjectURL(res.data);
    if (isTxt.value) originalText.value = await res.data.text();
  } catch (e) {
    console.error(e);
    originalError.value = "원본 문서를 불러오지 못했습니다.";
  } finally {
    originalLoading.value = false;
  }
}

async function loadConvertedOriginalFile(force = false) {
  if (convertedOriginalBlob.value && !force) return;
  if (!isDone.value) return;
  convertedOriginalLoading.value = true;
  convertedOriginalError.value = "";
  try {
    if (isTxt.value) {
      convertedOriginalBlob.value = new Blob([easyText.value], { type: "text/plain;charset=utf-8" });
    } else {
      const res = await documentService.getConvertedOriginalFile(docId.value);
      convertedOriginalBlob.value = res.data;
    }
    clearConvertedOriginalUrl();
    if (convertedOriginalBlob.value) convertedOriginalUrl.value = URL.createObjectURL(convertedOriginalBlob.value);
  } catch (e) {
    console.error(e);
    convertedOriginalError.value = "쉬운말 문서를 불러오지 못했습니다.";
  } finally {
    convertedOriginalLoading.value = false;
  }
}

async function renderOriginalDocx() {
  if (!isDocx.value || !originalBlob.value || !originalDocxContainer.value || activeTab.value !== "original") return;
  originalRenderError.value = "";
  try {
    originalDocxContainer.value.innerHTML = "";
    await renderAsync(originalBlob.value, originalDocxContainer.value, undefined, {
      className: "docx",
      inWrapper: false,
      ignoreWidth: false,
      ignoreHeight: false,
      ignoreFonts: false,
      breakPages: true,
      experimental: true,
    });
  } catch (error) {
    console.error(error);
    originalRenderError.value = "DOCX 미리보기를 표시하지 못했습니다. 다운로드로 확인해 주세요.";
  }
}

async function renderConvertedDocx() {
  if (!isDocx.value || !convertedOriginalBlob.value || !convertedDocxContainer.value || activeTab.value !== "converted") return;
  convertedRenderError.value = "";
  try {
    convertedDocxContainer.value.innerHTML = "";
    await renderAsync(convertedOriginalBlob.value, convertedDocxContainer.value, undefined, {
      className: "docx",
      inWrapper: false,
      ignoreWidth: false,
      ignoreHeight: false,
      ignoreFonts: false,
      breakPages: true,
      experimental: true,
    });
  } catch (error) {
    console.error(error);
    convertedRenderError.value = "쉬운말 DOCX 미리보기를 표시하지 못했습니다. 다운로드로 확인해 주세요.";
  }
}

function clearOriginalUrl() {
  if (originalUrl.value) URL.revokeObjectURL(originalUrl.value);
  originalUrl.value = "";
}

function clearConvertedOriginalUrl() {
  if (convertedOriginalUrl.value) URL.revokeObjectURL(convertedOriginalUrl.value);
  convertedOriginalUrl.value = "";
}

function selectChange(item: ChangeItem) {
  selectedChange.value = item;
  if (activeTab.value === "compare") {
    nextTick(() => scrollToChange(item));
  }
}

function paragraphChanges(index: number) {
  return changeItems.value.filter((item) => item.paragraphIndex === index);
}

async function goToChangedLocation() {
  if (!selectedChange.value) return;
  if (activeTab.value !== "original" && activeTab.value !== "converted") {
    activeTab.value = "converted";
  }
  await nextTick();
  const found = await scrollToDocumentChange(selectedChange.value);
  if (!found) {
    activeTab.value = "compare";
    await nextTick();
    scrollToChange(selectedChange.value);
  }
}

function compareCardId(index: number) {
  return `changed-paragraph-${index}`;
}

function scrollToChange(item: ChangeItem) {
  const target = document.getElementById(compareCardId(item.paragraphIndex));
  target?.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function scrollToDocumentChange(item: ChangeItem) {
  if (activeTab.value === "converted") {
    await loadConvertedOriginalFile();
    await nextTick();
    await renderConvertedDocx();
  }
  if (activeTab.value === "original") {
    await loadOriginalFile();
    await nextTick();
    await renderOriginalDocx();
  }
  await nextTick();

  const term = activeTab.value === "original" ? item.from : item.to;
  if (!term) return false;

  if (isTxt.value) {
    const target = activeTab.value === "original" ? originalTxtContainer.value : convertedTxtContainer.value;
    target?.scrollIntoView({ behavior: "smooth", block: "center" });
    flashLocatedElement(target);
    return Boolean(target);
  }

  if (!isDocx.value) return false;

  const container = activeTab.value === "original" ? originalDocxContainer.value : convertedDocxContainer.value;
  const shell = activeTab.value === "original" ? originalDocxShell.value : convertedDocxShell.value;
  const target = findElementContainingText(container, term);
  if (!target || !shell) return false;

  const shellBox = shell.getBoundingClientRect();
  const targetBox = target.getBoundingClientRect();
  shell.scrollTo({
    top: shell.scrollTop + targetBox.top - shellBox.top - shell.clientHeight * 0.28,
    behavior: "smooth",
  });
  flashLocatedElement(target);
  return true;
}

function findElementContainingText(root: HTMLElement | null, term: string) {
  if (!root) return null;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node = walker.nextNode();
  while (node) {
    if ((node.textContent || "").includes(term)) {
      return node.parentElement;
    }
    node = walker.nextNode();
  }
  return null;
}

function flashLocatedElement(element: HTMLElement | null) {
  if (!element) return;
  element.classList.add("located-hit");
  window.setTimeout(() => element.classList.remove("located-hit"), 1800);
}

async function download(mode: DownloadMode) {
  if (!isDone.value) return;
  try {
    const res = await documentService.downloadDocument(docId.value, mode);
    saveBlob(res.data, `${displayTitle.value}_${mode}.docx`);
  } catch (e) {
    console.error(e);
    alert("DOCX 다운로드에 실패했습니다.");
  }
}

async function downloadConvertedOriginal() {
  if (!isDone.value) return;
  await loadConvertedOriginalFile();
  if (!convertedOriginalBlob.value) return;
  const extension = docMeta.type.toUpperCase() === "PDF" ? "pdf" : docMeta.type.toUpperCase() === "TXT" ? "txt" : "docx";
  saveBlob(convertedOriginalBlob.value, `${displayTitle.value}_easy_layout.${extension}`);
}

function downloadOriginal() {
  if (!originalBlob.value) return;
  saveBlob(originalBlob.value, docMeta.title || "original-document");
}

function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function fontUp() {
  fontSize.value = Math.min(20, fontSize.value + 1);
}

function fontDown() {
  fontSize.value = Math.max(12, fontSize.value - 1);
}

function badgeClass(value: DocStatus) {
  if (value === "DONE") return "badge-ok";
  if (value === "FAILED") return "badge-bad";
  return "badge-warn";
}

function statusLabel(value: DocStatus) {
  if (value === "DONE") return "변환 완료";
  if (value === "FAILED") return "분석 실패";
  if (value === "QUEUED") return "대기 중";
  if (value === "PROCESSING") return "분석 중";
  return "불러오는 중";
}
</script>

<style scoped>
.topbar {
  min-height: 76px;
  background: var(--topbar-bg);
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 18px;
  gap: 12px;
}

.tb-left {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-wrap {
  min-width: 0;
}

.hamburger,
.icon-btn,
.btn {
  height: 40px;
  min-height: 40px;
  border: 1px solid var(--field-border);
  background: var(--button-bg);
  color: var(--button-text);
  border-radius: 8px;
  padding: 0 12px;
  font: inherit;
  font-weight: 900;
  cursor: pointer;
  white-space: nowrap;
}

.hamburger {
  width: 42px;
  padding: 0;
  font-size: 19px;
}

.tb-title-strong {
  color: var(--ink);
  font-weight: 900;
  font-size: 18px;
}

.tb-sub,
.muted,
.preview-head p,
.side-head p {
  color: var(--muted);
  font-size: 13px;
}

.tb-sub {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tb-right {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.full-btn {
  width: 100%;
}

.content {
  max-width: 1660px;
  width: 100%;
  margin: 0 auto;
  padding: 18px 16px 36px;
  display: grid;
  gap: 14px;
}

.state-card,
.card,
.document-preview,
.view-switch,
.side-card,
.compare-card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 8px;
}

.state-card {
  padding: 18px;
}

.state-card.error {
  border-color: #fecaca;
  background: #fef2f2;
}

.state-title,
.card-title,
.side-title {
  color: var(--ink);
  font-weight: 900;
}

.view-switch {
  min-height: 54px;
  max-height: 54px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px;
  overflow-x: auto;
}

.tab {
  flex: 0 0 auto;
  height: 40px;
  min-height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 0 14px;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-weight: 900;
  white-space: nowrap;
  cursor: pointer;
}

.tab.active {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.reader-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 360px);
  gap: 14px;
  align-items: start;
}

.document-preview {
  padding: 16px;
  display: grid;
  gap: 14px;
  min-width: 0;
}

.preview-head,
.side-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.preview-title {
  color: var(--ink);
  font-size: 18px;
  font-weight: 1000;
}

.preview-head p,
.side-head p {
  margin: 4px 0 0;
}

.doc-type,
.badge {
  border-radius: 999px;
  padding: 5px 9px;
  font-size: 12px;
  font-weight: 900;
}

.doc-type {
  flex: 0 0 auto;
  color: var(--accent);
  background: var(--accent-soft);
  border: 1px solid var(--accent-border);
}

.selected-change,
.selected-words {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.selected-change {
  padding: 10px 12px;
  border: 1px solid var(--accent-border);
  border-radius: 8px;
  background: var(--accent-soft);
  color: var(--ink);
  text-align: left;
  font: inherit;
  cursor: pointer;
}

.selected-change:hover {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.location-hint {
  margin-left: auto;
  color: var(--accent);
  font-size: 12px;
  font-weight: 1000;
}

.old-word,
.change-from {
  color: var(--muted);
  text-decoration: line-through;
  font-weight: 800;
}

.arrow,
.change-arrow,
.down-arrow {
  color: var(--accent);
  font-weight: 1000;
}

.file-frame,
.docx-shell,
.txt-viewer,
.viewer-state {
  width: 100%;
  min-height: min(78vh, 900px);
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #eef2f7;
}

.file-frame {
  height: min(78vh, 900px);
}

.docx-shell {
  overflow: auto;
  padding: 24px;
}

.docx-container {
  display: grid;
  justify-content: center;
  gap: 18px;
}

.txt-viewer {
  margin: 0;
  padding: 22px;
  white-space: pre-wrap;
  color: #111827;
  font: 14px/1.7 ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
}

.viewer-state {
  display: grid;
  place-content: center;
  justify-items: center;
  gap: 12px;
  padding: 24px;
  color: #475569;
  font-weight: 800;
}

.viewer-state.error {
  color: #991b1b;
}

.side-panel {
  position: sticky;
  top: 14px;
  max-height: calc(100vh - 110px);
  overflow: auto;
  display: grid;
  gap: 12px;
}

.side-card {
  padding: 14px;
  display: grid;
  gap: 12px;
}

.step-list {
  display: grid;
  gap: 8px;
}

.step {
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr);
  gap: 10px;
  align-items: center;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--field-bg);
  color: var(--ink);
  padding: 10px;
  text-align: left;
  font: inherit;
  cursor: pointer;
}

.step span,
.para-no {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 900;
  font-size: 12px;
}

.small-btn {
  height: 32px;
  border: 1px solid var(--field-border);
  border-radius: 8px;
  background: var(--button-bg);
  color: var(--button-text);
  padding: 0 9px;
  font: inherit;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
}

.search-input {
  height: 40px;
  border: 1px solid var(--field-border);
  border-radius: 8px;
  background: var(--field-bg);
  color: var(--ink);
  padding: 0 10px;
  font: inherit;
  font-weight: 750;
}

.change-list {
  min-height: 0;
  display: grid;
  gap: 8px;
}

.change-card {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px;
  background: var(--field-bg);
  color: var(--ink);
  text-align: left;
  display: grid;
  gap: 5px;
  cursor: pointer;
}

.change-card.active,
.change-card:hover {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.change-to {
  color: var(--ink);
  font-weight: 1000;
}

.change-definition,
.change-meta,
.selected-info p {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.45;
}

.change-empty {
  min-height: 120px;
  display: grid;
  place-items: center;
  color: var(--muted);
  text-align: center;
  font-weight: 800;
}

.quick-actions {
  display: grid;
  gap: 8px;
}

.compare-list {
  display: grid;
  gap: 10px;
}

.compare-card {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 12px;
  padding: 14px;
  color: var(--ink);
}

.compare-card.highlighted {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.compare-body {
  display: grid;
  gap: 10px;
}

.compare-body p {
  margin: 4px 0 0;
  line-height: 1.75;
}

.mini-label {
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
}

.inline-changes,
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.change-chip,
.chip {
  border: 1px solid var(--accent-border);
  border-radius: 8px;
  background: var(--accent-soft);
  color: var(--accent);
  padding: 5px 8px;
  font: inherit;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
}

.summary-grid {
  display: grid;
  gap: 12px;
}

.card {
  padding: 16px;
}

.card p {
  margin: 8px 0 0;
  color: var(--ink);
  line-height: 1.7;
}

.term-card {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.badge {
  border: 1px solid transparent;
  white-space: nowrap;
}

.badge-ok {
  background: #ecfdf5;
  border-color: #a7f3d0;
  color: #065f46;
}

.badge-warn {
  background: #fffbeb;
  border-color: #fde68a;
  color: #92400e;
}

.badge-bad {
  background: #fef2f2;
  border-color: #fecaca;
  color: #991b1b;
}

:global([data-theme="dark"]) .docx-shell,
:global([data-theme="dark"]) .txt-viewer {
  background: #f8fafc;
  color: #111827;
  border-color: #3b4658;
}

:global([data-theme="dark"]) .docx-shell :deep(*) {
  color: #111827;
}

.docx-shell :deep(.located-hit),
.txt-viewer.located-hit {
  outline: 3px solid var(--accent);
  background: #dbeafe;
  border-radius: 4px;
  transition: outline-color 180ms ease, background-color 180ms ease;
}

@media (max-width: 1180px) {
  .reader-layout {
    grid-template-columns: 1fr;
  }

  .side-panel {
    position: static;
    max-height: none;
    order: -1;
  }

  .change-list {
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }
}

@media (max-width: 760px) {
  .topbar {
    align-items: flex-start;
    padding: 12px 14px;
    flex-direction: column;
  }

  .tb-right {
    justify-content: flex-start;
  }

  .docx-shell {
    padding: 12px;
  }
}
</style>
