<template>
  <AppLayout>
    <main class="doq-document" :class="{ 'pdf-wide': isPdf && isPdfPanelWide }" :style="{ '--reader-size': fontSize + 'px' }">
      <header class="doq-document-head">
        <div class="doq-document-title">
          <span>{{ docMeta.type || "FILE" }}</span>
          <div><strong>{{ docMeta.title || "문서를 불러오는 중" }}</strong><small>{{ statusLabel(status) }} · {{ changeItems.length }}개 표현이 쉬워졌어요</small></div>
        </div>
        <div class="doq-document-actions">
          <label v-if="isPdf" class="doq-pdf-width-control">
            <span>문서 너비</span>
            <input v-model.number="pdfPanelWidth" type="range" min="65" max="100" step="1" aria-label="PDF 영역 너비" />
            <output>{{ pdfPanelWidth }}%</output>
          </label>
          <span class="doq-font-controls"><button type="button" aria-label="글자 및 PDF 축소" @click="fontDown">A−</button><output>{{ pdfZoomPercent }}%</output><button type="button" aria-label="글자 및 PDF 확대" @click="fontUp">A+</button></span>
          <button type="button" :disabled="!originalBlob" @click="downloadOriginal">↓ 원본 내려받기</button>
          <button class="primary" type="button" :disabled="!isDone" @click="downloadConvertedOriginal">↓ 쉬운말 내려받기</button>
        </div>
      </header>

      <nav class="doq-view-tabs">
        <button :class="{ active: activeTab === 'converted' || activeTab === 'original' }" @click="activeTab = 'converted'">쉬운말 보기</button>
        <button :class="{ active: activeTab === 'compare' }" @click="activeTab = 'compare'">나란히 비교</button>
        <button :class="{ active: activeTab === 'summary' }" @click="activeTab = 'summary'">요약·용어</button>
      </nav>

      <section v-if="loading" class="doq-doc-state">문서를 불러오는 중입니다.</section>
      <section v-else-if="status === 'QUEUED' || status === 'PROCESSING'" class="doq-doc-state">문서를 분석하고 있습니다. 완료되면 자동으로 표시됩니다.</section>
      <section v-else-if="status === 'FAILED'" class="doq-doc-state error">문서 분석에 실패했습니다. 다시 업로드해 주세요.</section>

      <section
        v-else
        class="doq-reader-grid"
        :class="{ 'wide-pdf-layout': isPdf && isPdfPanelWide }"
        :style="{ '--pdf-panel-width': `${pdfPanelWidth}%` }"
      >
        <article class="doq-reader">
          <template v-if="activeTab === 'converted' || activeTab === 'original'">
            <header class="doq-reader-head">
              <strong>{{ showHard ? "원문" : "쉬운말 문서" }}</strong>
              <button type="button" :class="{ on: !showHard }" @click="showHard = !showHard"><span>✓</span>{{ showHard ? "쉬운말 보기" : "원문 보기" }}</button>
            </header>
            <div class="doq-level-row"><span>쉬운 정도</span><div><button v-for="level in [1,2,3]" :key="level" :class="{ active: easyLevel === level }" :disabled="reprocessing || !isDone" @click="changeEasyLevel(level)">{{ level === 1 ? "살짝" : level === 2 ? "쉽게" : "아주 쉽게" }}</button></div></div>
            <div class="doq-reader-divider" />
            <div class="doq-document-viewport">
              <Transition name="doq-document-swap">
                <div :key="isTxt ? 'text' : (showHard ? 'original' : 'converted')" class="doq-document-stage" :data-view-mode="showHard ? 'original' : 'converted'">
                  <div v-if="isPdf && !(showHard ? originalBlob : convertedOriginalBlob)" class="doq-file-viewer-state">PDF 문서 화면을 준비하고 있습니다.</div>
                  <PdfDocumentViewer
                    v-else-if="isPdf"
                    :blob="showHard ? originalBlob : convertedOriginalBlob"
                    :annotations="showHard ? originalPdfAnnotations : convertedPdfAnnotations"
                    :original="showHard"
                    :selected-id="selectedChange?.id"
                    :zoom="pdfZoom"
                    @select="selectAnnotation"
                  />
                  <div v-else-if="isDocx && !(showHard ? originalBlob : convertedOriginalBlob)" class="doq-file-viewer-state">DOCX 문서 화면을 준비하고 있습니다.</div>
                  <DocxDocumentViewer
                    v-else-if="isDocx"
                    :blob="showHard ? originalBlob : convertedOriginalBlob"
                    :changes="changeItems"
                    :original="showHard"
                    :selected-id="selectedChange?.id"
                    @select="selectAnnotation"
                  />
                  <div v-else-if="paragraphs.length" class="doq-reading doq-txt-paper">
                    <MorphingParagraph
                      v-for="(paragraph, index) in paragraphs"
                      :key="index"
                      :original="paragraph.original"
                      :easy="paragraph.easy || paragraph.original"
                      :changes="paragraph.changed_terms"
                      :show-original="showHard"
                    />
                  </div>
                  <div v-else class="doq-reading doq-txt-paper">
                    <MorphingParagraph :original="originalText" :easy="easyText" :show-original="showHard" />
                  </div>
                </div>
              </Transition>
            </div>
          </template>

          <template v-else-if="activeTab === 'compare'">
            <div class="doq-compare-head"><strong>원문</strong><span /><strong>쉬운말</strong></div>
            <div class="doq-side-compare">
              <div v-for="(paragraph, index) in paragraphs" :key="index" :id="compareCardId(index)" :class="{ highlighted: selectedChange?.paragraphIndex === index }">
                <p>{{ paragraph.original || "원문 내용이 없습니다." }}</p><span>→</span><p>{{ paragraph.easy || paragraph.original }}</p>
              </div>
            </div>
          </template>

          <template v-else>
            <h2 class="doq-summary-title">핵심 요약</h2>
            <div class="doq-summary-box">{{ analysis.summary || "요약 정보가 없습니다." }}</div>
            <h2 class="doq-summary-title">어려운 용어</h2>
            <div class="doq-term-chips"><button v-for="term in terms" :key="term.term" @click="selectedTerm = term">{{ term.term }}</button></div>
            <div v-if="selectedTerm" class="doq-term-definition"><strong>{{ selectedTerm.term }}</strong><p>{{ selectedTerm.definition }}</p></div>
          </template>

          <div class="doq-doc-feedback">
            <template v-if="!docFeedback"><span>이 쉬운말 변환이 도움이 됐나요?</span><button @click="docFeedback = 'good'">😊</button><button @click="docFeedback = 'soso'">😐</button><button @click="docFeedback = 'bad'">😞</button></template>
            <span v-else class="thanks">✓ 의견을 남겨 주셔서 고마워요.</span>
          </div>
        </article>

        <aside class="doq-reader-side">
          <section>
            <header><strong>바뀐 표현</strong><span>{{ changeItems.length }}개</span></header>
            <div class="doq-change-list">
              <button v-for="item in changeItems" :key="item.id" :class="{ active: selectedChange?.id === item.id }" @click="selectChange(item)"><span>{{ item.from }}</span><b>→</b><em>{{ item.to }}</em></button>
              <p v-if="!changeItems.length">바뀐 표현이 없습니다.</p>
            </div>
          </section>
          <section class="doq-easy-meter">
            <strong>쉬운 정도</strong>
            <div><span :style="{ width: easyMeterPercent + '%' }" /></div>
            <p>{{ easyMeterLabel }}</p>
          </section>
        </aside>
      </section>
    </main>


  </AppLayout>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import documentService from "../api/document.service";
import AppLayout from "../components/layout/AppLayout.vue";
import MorphingParagraph from "../components/document/MorphingParagraph.vue";

const PdfDocumentViewer = defineAsyncComponent(() => import("../components/document/PdfDocumentViewer.vue"));
const DocxDocumentViewer = defineAsyncComponent(() => import("../components/document/DocxDocumentViewer.vue"));

interface PdfAnnotation {
  id: string;
  segment: number;
  page: number;
  page_width: number;
  page_height: number;
  x: number;
  y: number;
  width: number;
  height: number;
  original: string;
  easy: string;
  definition: string;
  approximate?: boolean;
}

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

const route = useRoute();
const docId = computed(() => String(route.params.id ?? ""));
const loading = ref(true);
const status = ref<DocStatus>("");
const fontPreset: Record<string, number> = { sm: 15, md: 16.5, lg: 18.5 };
const savedFontMode = localStorage.getItem("font_size") || "md";
const savedCustomFont = Number(localStorage.getItem("custom_font_size") || 18.5);
const fontSize = ref(savedFontMode === "custom" ? Math.min(24, Math.max(14, savedCustomFont)) : (fontPreset[savedFontMode] || 16.5));
const savedPdfPanelWidth = Number(localStorage.getItem("pdf_panel_width") || 74);
const pdfPanelWidth = ref(Math.min(100, Math.max(65, savedPdfPanelWidth)));
const pollTimer = ref<number | null>(null);
const activeTab = ref<ViewTab>("converted");
const selectedTerm = ref<TermItem | null>(null);
const selectedChange = ref<ChangeItem | null>(null);
const showHard = ref(false);
const easyLevel = ref(2);
const reprocessing = ref(false);
const docFeedback = ref("");

const originalBlob = ref<Blob | null>(null);
const originalText = ref("");
const originalPdfAnnotations = ref<PdfAnnotation[]>([]);
const convertedPdfAnnotations = ref<PdfAnnotation[]>([]);
const pdfAnnotationsLoaded = ref(false);

const convertedOriginalBlob = ref<Blob | null>(null);

const docMeta = reactive({ title: "", type: "" });
const analysis = reactive({ summary: "" });
const paragraphs = ref<ParagraphItem[]>([]);
const terms = ref<TermItem[]>([]);
const convertedText = ref("");

const isDone = computed(() => status.value === "DONE");
const isTxt = computed(() => docMeta.type.toUpperCase() === "TXT");
const isPdf = computed(() => docMeta.type.toUpperCase() === "PDF");
const isDocx = computed(() => docMeta.type.toUpperCase() === "DOCX");
const pdfZoom = computed(() => Math.min(1.5, Math.max(0.8, fontSize.value / 16.5)));
const pdfZoomPercent = computed(() => Math.round(pdfZoom.value * 100));
const isPdfPanelWide = computed(() => pdfPanelWidth.value >= 78);
const displayTitle = computed(() => (docMeta.title || "document").replace(/\.[^.]+$/, ""));
const easyText = computed(() => {
  const fromParagraphs = paragraphs.value.map((item) => item.easy || item.original).filter(Boolean).join("\n\n");
  return convertedText.value || fromParagraphs;
});

const changeItems = computed<ChangeItem[]>(() => {
  const seen = new Set<string>();
  const items: ChangeItem[] = [];
  paragraphs.value.forEach((paragraph, paragraphIndex) => {
    const orderedTerms = (paragraph.changed_terms || [])
      .map((term, termIndex) => ({ term, termIndex }))
      .sort((left, right) => {
        const leftPosition = paragraph.original.indexOf(String(left.term.from || ""));
        const rightPosition = paragraph.original.indexOf(String(right.term.from || ""));
        return (leftPosition < 0 ? Number.MAX_SAFE_INTEGER : leftPosition)
          - (rightPosition < 0 ? Number.MAX_SAFE_INTEGER : rightPosition)
          || left.termIndex - right.termIndex;
      });
    orderedTerms.forEach(({ term, termIndex }) => {
      const from = String(term.from || "").trim();
      const to = String(term.to || "").trim();
      if (!isMeaningfulChange(from, to)) return;
      const key = `${paragraphIndex}:${from}:${to}`;
      if (seen.has(key)) return;
      const id = `${paragraphIndex}-${termIndex}-${from}-${to}`;
      if (isPdf.value && pdfAnnotationsLoaded.value) {
        const annotationExists = [...originalPdfAnnotations.value, ...convertedPdfAnnotations.value]
          .some((annotation) => annotation.id === id);
        if (!annotationExists) return;
      }
      seen.add(key);
      items.push({
        id,
        from,
        to,
        definition: String(term.definition || "").trim(),
        paragraphIndex,
      });
    });
  });
  return items;
});
const easyMeterPercent = computed(() => changeItems.value.length
  ? (easyLevel.value === 1 ? 60 : easyLevel.value === 2 ? 78 : 93)
  : 0);
const easyMeterLabel = computed(() => changeItems.value.length
  ? `${easyLevel.value === 1 ? "살짝" : easyLevel.value === 2 ? "쉽게" : "아주 쉽게"} · ${changeItems.value.length}개 표현을 바꿨어요`
  : "바꿀 어려운 표현이 없어 원문을 유지했어요");

function isMeaningfulChange(from: string, to: string) {
  const source = from.replace(/\s+/g, "");
  const replacement = to.replace(/\s+/g, "");
  return Boolean(source && replacement && source !== replacement && !(source.length <= 2 && replacement.length > source.length * 3));
}

onMounted(() => {
  const savedTheme = (localStorage.getItem("theme") as "light" | "dark") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
  loadDocument();
});

onUnmounted(() => {
  if (pollTimer.value) window.clearInterval(pollTimer.value);
});

watch(changeItems, (items) => {
  if (!selectedChange.value || !items.some((item) => item.id === selectedChange.value?.id)) {
    selectedChange.value = items[0] || null;
  }
});

watch(pdfPanelWidth, (value) => {
  localStorage.setItem("pdf_panel_width", String(value));
});

async function loadDocument() {
  try {
    localStorage.setItem("last_document_id", docId.value);
    const res = await documentService.getDocument(docId.value);
    const doc = res.data;

    docMeta.title = doc.title;
    docMeta.type = doc.file_type || "UNKNOWN";
    status.value = doc.status;
    analysis.summary = doc.analysis?.summary || "";
    paragraphs.value = doc.analysis?.paragraphs || [];
    convertedText.value = doc.meta_data?.converted_text || "";
    const intensity = String(doc.meta_data?.intensity || "easy");
    easyLevel.value = intensity === "close" ? 1 : intensity === "summary" ? 3 : 2;
    terms.value = (doc.glossary_terms || []).map((item: any) => ({
      term: item.term,
      definition: item.definition,
    }));
    loading.value = false;

    void loadOriginalFile();
    if (doc.status === "DONE") {
      void loadConvertedOriginalFile();
      if (String(doc.file_type || "").toUpperCase() === "PDF") void loadPdfAnnotations();
    }

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
  }
}

function startPolling() {
  if (pollTimer.value) return;
  pollTimer.value = window.setInterval(() => {
    loadDocument();
  }, 2500);
}

async function changeEasyLevel(level: number) {
  if (level === easyLevel.value || reprocessing.value || !isDone.value) return;
  const intensity = level === 1 ? "close" : level === 3 ? "summary" : "easy";
  reprocessing.value = true;
  try {
    await documentService.reprocessDocument(docId.value, intensity);
    easyLevel.value = level;
    status.value = "QUEUED";
    convertedOriginalBlob.value = null;
    originalPdfAnnotations.value = [];
    convertedPdfAnnotations.value = [];
    pdfAnnotationsLoaded.value = false;
    paragraphs.value = [];
    terms.value = [];
    convertedText.value = "";
    selectedChange.value = null;
    startPolling();
  } catch (error) {
    console.error("Reprocess failed", error);
    alert("쉬운 정도를 변경하지 못했습니다. 잠시 후 다시 시도해 주세요.");
  } finally {
    reprocessing.value = false;
  }
}

async function loadOriginalFile(force = false) {
  if (originalBlob.value && !force) return;
  try {
    const res = await documentService.getOriginalFile(docId.value);
    originalBlob.value = res.data;
    if (isTxt.value) originalText.value = await res.data.text();
  } catch (e) {
    console.error(e);
  }
}

async function loadConvertedOriginalFile(force = false) {
  if (convertedOriginalBlob.value && !force) return;
  if (!isDone.value) return;
  try {
    if (isTxt.value) {
      convertedOriginalBlob.value = new Blob([easyText.value], { type: "text/plain;charset=utf-8" });
    } else {
      const res = await documentService.getConvertedOriginalFile(docId.value);
      convertedOriginalBlob.value = res.data;
    }
  } catch (e) {
    console.error(e);
  }
}

async function loadPdfAnnotations() {
  pdfAnnotationsLoaded.value = false;
  try {
    const [originalResponse, convertedResponse] = await Promise.all([
      documentService.getDocumentAnnotations(docId.value, "original"),
      documentService.getDocumentAnnotations(docId.value, "converted"),
    ]);
    originalPdfAnnotations.value = originalResponse.data.annotations || [];
    convertedPdfAnnotations.value = convertedResponse.data.annotations || [];
  } catch (error) {
    console.error("PDF annotations failed", error);
    originalPdfAnnotations.value = [];
    convertedPdfAnnotations.value = [];
  } finally {
    pdfAnnotationsLoaded.value = true;
  }
}

function selectChange(item: ChangeItem) {
  selectedChange.value = item;
  if (activeTab.value === "compare") {
    nextTick(() => scrollToChange(item));
  }
}

function selectAnnotation(id: string) {
  const item = changeItems.value.find((change) => change.id === id);
  if (item) selectedChange.value = item;
}

function compareCardId(index: number) {
  return `changed-paragraph-${index}`;
}

function scrollToChange(item: ChangeItem) {
  const target = document.getElementById(compareCardId(item.paragraphIndex));
  target?.scrollIntoView({ behavior: "smooth", block: "center" });
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
  fontSize.value = Math.min(24, fontSize.value + 1.5);
}

function fontDown() {
  fontSize.value = Math.max(13, fontSize.value - 1.5);
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
.doq-document { width: min(1180px, 100%); margin: 0 auto; padding: 24px 34px 48px; transition: width .25s ease; }.doq-document.pdf-wide { width: min(1400px, 100%); }
.doq-document-head { margin-bottom: 18px; display: flex; align-items: center; justify-content: space-between; gap: 14px; }.doq-document-title { min-width: 0; display: flex; align-items: center; gap: 13px; }.doq-document-title > span { width: 44px; height: 44px; display: grid; place-items: center; flex: none; border-radius: 13px; color: #e14a6b; background: #fdecef; font-size: 10px; font-weight: 700; }.doq-document-title > div { min-width: 0; display: grid; }.doq-document-title strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 18px; }.doq-document-title small { margin-top: 2px; color: var(--muted); font-size: 12.5px; }
.doq-document-actions { display: flex; align-items: center; justify-content: flex-end; flex-wrap: wrap; gap: 9px; }.doq-document-actions > button { height: 38px; padding: 0 13px; border: 1px solid var(--line); border-radius: 11px; color: var(--sub); background: var(--surface); font-size: 13px; font-weight: 600; cursor: pointer; }.doq-document-actions > button.primary { padding-inline: 14px; border: 0; color: #fff; background: var(--accent-gradient); }.doq-document-actions button:disabled { opacity: .45; cursor: default; }
.doq-pdf-width-control { height: 38px; padding: 0 10px; display: flex; align-items: center; gap: 8px; border: 1px solid var(--line); border-radius: 11px; background: var(--surface); }.doq-pdf-width-control > span { color: var(--muted); white-space: nowrap; font-size: 11px; font-weight: 700; }.doq-pdf-width-control input { width: 88px; accent-color: var(--accent); cursor: ew-resize; }.doq-pdf-width-control output { width: 33px; color: var(--sub); text-align: right; font-size: 11px; font-weight: 700; }
.doq-font-controls { display: flex; align-items: center; overflow: hidden; border: 1px solid var(--line); border-radius: 11px; background: var(--surface); }.doq-font-controls button { width: 40px; height: 38px; border: 0; color: var(--muted); background: transparent; font-size: 13px; font-weight: 700; cursor: pointer; }.doq-font-controls button:last-child { color: var(--ink); font-size: 15px; }.doq-font-controls output { min-width: 47px; padding: 0 8px; border-right: 1px solid var(--line); border-left: 1px solid var(--line); color: var(--sub); text-align: center; font-size: 11px; font-weight: 700; }
.doq-view-tabs { width: fit-content; margin-bottom: 18px; padding: 4px; display: flex; gap: 5px; border-radius: 13px; background: var(--soft); }.doq-view-tabs button { padding: 8px 15px; border: 0; border-radius: 9px; color: var(--muted); background: transparent; font-size: 13px; font-weight: 600; cursor: pointer; }.doq-view-tabs button.active { color: var(--ink); background: var(--surface); box-shadow: 0 1px 3px rgb(30 20 70 / .1); }
.doq-doc-state { padding: 42px; border: 1px solid var(--line); border-radius: 20px; color: var(--muted); background: var(--surface); text-align: center; }.doq-doc-state.error { color: #c0392b; }
.doq-reader-grid { display: grid; grid-template-columns: minmax(0, var(--pdf-panel-width, calc(100% - 308px))) minmax(260px, 1fr); gap: 18px; align-items: start; }.doq-reader-grid.wide-pdf-layout { grid-template-columns: minmax(0, 1fr); }.doq-reader-grid.wide-pdf-layout .doq-reader-side { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }.doq-reader { min-height: 420px; padding: 30px 36px; border: 1px solid var(--line); border-radius: 20px; background: var(--surface); }
.doq-reader-head { margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between; }.doq-reader-head > strong { font-size: 15px; }.doq-reader-head button { height: 34px; padding: 0 11px; display: flex; align-items: center; gap: 7px; border: 1px solid var(--line); border-radius: 10px; color: var(--muted); background: var(--surface); font-size: 12px; font-weight: 600; cursor: pointer; }.doq-reader-head button span { width: 18px; height: 18px; display: grid; place-items: center; border-radius: 50%; color: #fff; background: var(--muted); font-size: 10px; }.doq-reader-head button.on { color: var(--accent-strong); background: var(--soft); }.doq-reader-head button.on span { background: #12a58a; }
.doq-level-row { margin: 2px 0 6px; display: flex; align-items: center; gap: 10px; }.doq-level-row > span { color: var(--muted); font-size: 12.5px; font-weight: 600; }.doq-level-row > div { padding: 3px; display: flex; gap: 3px; border-radius: 10px; background: var(--soft); }.doq-level-row button { padding: 6px 11px; border: 0; border-radius: 8px; color: var(--muted); background: transparent; font-size: 12px; font-weight: 600; cursor: pointer; }.doq-level-row button.active { color: var(--ink); background: var(--surface); box-shadow: 0 1px 3px rgb(0 0 0 / .08); }.doq-level-row button:disabled { cursor: wait; opacity: .58; }
.doq-reader-divider { height: 1px; margin: 12px 0 24px; background: var(--line); }.doq-reading { color: var(--sub); font-size: var(--reader-size); line-height: 2.05; white-space: pre-wrap; }.doq-reading p { margin: 0 0 26px; }.doq-reading p:last-child { margin-bottom: 0; }.doq-reading mark { color: var(--ink); background: linear-gradient(transparent 64%, #ddd2ff 64%) left bottom / 100% 100% no-repeat; font-weight: 700; animation: doq-text-mark-in .55s ease var(--change-delay, 0s) both; }.doq-reading.original mark { animation-name: doq-text-mark-in-original; }[data-theme="dark"] .doq-reading mark { background-image: linear-gradient(transparent 64%, #574883 64%); }
.doq-document-viewport { display: grid; overflow: hidden; }.doq-document-stage { min-width: 0; grid-area: 1 / 1; transform-origin: center top; }.doq-document-swap-enter-active, .doq-document-swap-leave-active { transition: opacity .4s ease, transform .4s ease; }.doq-document-swap-enter-from { opacity: 0; transform: translateY(14px); }.doq-document-swap-leave-to { opacity: 0; transform: translateY(-14px); }
@keyframes doq-text-mark-in { from { opacity: 0; transform: translateY(40%); background-size: 0 100%; } to { opacity: 1; transform: translateY(0); background-size: 100% 100%; } }
@keyframes doq-text-mark-in-original { from { opacity: 0; transform: translateY(-40%); background-size: 0 100%; } to { opacity: 1; transform: translateY(0); background-size: 100% 100%; } }
.doq-txt-paper { min-height: 480px; padding: 46px 52px; border: 1px solid var(--line); background: var(--surface); box-shadow: 0 3px 14px rgb(32 26 58 / .08); }
.doq-file-viewer-state { min-height: 420px; display: grid; place-items: center; border-radius: 14px; color: var(--muted); background: var(--soft); font-size: 13px; }
.doq-compare-head { margin-bottom: 12px; display: grid; grid-template-columns: 1fr 40px 1fr; color: var(--muted); font-size: 12px; }.doq-compare-head strong:last-child { color: var(--accent); }.doq-side-compare { display: flex; flex-direction: column; gap: 12px; }.doq-side-compare > div { display: grid; grid-template-columns: 1fr 40px 1fr; align-items: center; border-radius: 13px; }.doq-side-compare > div.highlighted { box-shadow: 0 0 0 3px var(--accent-soft); }.doq-side-compare p { margin: 0; padding: 15px 17px; border: 1px solid var(--line); border-radius: 13px; color: var(--muted); background: var(--soft); font-size: 14px; line-height: 1.85; }.doq-side-compare p:last-child { border-color: var(--accent-border); color: var(--ink); background: var(--accent-soft); font-size: 15px; line-height: 1.9; }.doq-side-compare > div > span { color: var(--accent); text-align: center; font-weight: 700; }
.doq-summary-title { margin: 0 0 12px; font-size: 15px; }.doq-summary-box { margin-bottom: 22px; padding: 18px 20px; border: 1px solid var(--line); border-radius: 14px; color: var(--sub); background: var(--soft); font-size: 14.5px; line-height: 1.85; }.doq-term-chips { display: flex; flex-wrap: wrap; gap: 8px; }.doq-term-chips button { padding: 7px 12px; border: 1px solid var(--line); border-radius: 10px; color: var(--ink); background: var(--surface); font-size: 13px; font-weight: 500; cursor: pointer; }.doq-term-definition { margin-top: 14px; padding: 14px 16px; border-radius: 12px; background: var(--accent-soft); }.doq-term-definition p { margin: 5px 0 0; color: var(--sub); font-size: 13px; line-height: 1.6; }
.doq-doc-feedback { margin-top: 26px; padding-top: 20px; display: flex; align-items: center; gap: 8px; border-top: 1px solid var(--line); }.doq-doc-feedback > span:first-child { margin-right: 6px; color: var(--sub); font-size: 13.5px; font-weight: 600; }.doq-doc-feedback button { width: 42px; height: 42px; border: 1px solid var(--line); border-radius: 12px; background: var(--surface); font-size: 19px; cursor: pointer; }.doq-doc-feedback .thanks { color: var(--accent-strong); font-size: 13.5px; font-weight: 600; }
.doq-reader-side { display: flex; flex-direction: column; gap: 14px; }.doq-reader-side > section { padding: 18px; border: 1px solid var(--line); border-radius: 18px; background: var(--surface); }.doq-reader-side header { margin-bottom: 14px; display: flex; align-items: baseline; justify-content: space-between; }.doq-reader-side header strong { font-size: 14px; }.doq-reader-side header span { color: var(--muted); font-size: 12px; }.doq-change-list { display: flex; flex-direction: column; gap: 8px; }.doq-change-list button { padding: 10px 11px; display: flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 10px; color: var(--ink); background: var(--surface); font-size: 13px; cursor: pointer; }.doq-change-list button.active { border-color: var(--accent-border); background: var(--accent-soft); }.doq-change-list button span { color: #a09eae; text-decoration: line-through; }.doq-change-list button b { color: var(--accent); }.doq-change-list button em { font-style: normal; font-weight: 600; }.doq-change-list > p { color: var(--muted); font-size: 12.5px; }
.doq-easy-meter > strong { display: block; margin-bottom: 12px; font-size: 14px; }.doq-easy-meter > div { height: 9px; overflow: hidden; border-radius: 6px; background: var(--soft); }.doq-easy-meter > div span { height: 100%; display: block; background: linear-gradient(90deg,var(--accent),#12b39a); transition: width .3s; }.doq-easy-meter p { margin: 9px 0 0; color: var(--muted); font-size: 12.5px; }
@media (max-width: 900px) { .doq-document-head { align-items: flex-start; flex-direction: column; }.doq-document-actions { justify-content: flex-start; }.doq-reader-grid { grid-template-columns: 1fr; }.doq-reader-side, .doq-reader-grid.wide-pdf-layout .doq-reader-side { display: grid; grid-template-columns: 1fr 1fr; } }
@media (max-width: 620px) { .doq-document { padding: 20px 16px 40px; }.doq-document-actions { width: 100%; overflow-x: auto; }.doq-document-actions > button { white-space: nowrap; }.doq-pdf-width-control { flex: none; }.doq-view-tabs { width: 100%; }.doq-view-tabs button { min-width: 0; flex: 1; padding-inline: 6px; }.doq-reader { padding: 22px 18px; }.doq-txt-paper { padding: 28px 22px; }.doq-reader-side, .doq-reader-grid.wide-pdf-layout .doq-reader-side { grid-template-columns: 1fr; }.doq-side-compare > div, .doq-compare-head { grid-template-columns: 1fr; gap: 8px; }.doq-side-compare > div > span { transform: rotate(90deg); }.doq-compare-head { display: none; } }
@media (prefers-reduced-motion: reduce) { .doq-document { transition: none; }.doq-document-swap-enter-active, .doq-document-swap-leave-active { transition: none; }.doq-reading mark { animation: none; } }
</style>
