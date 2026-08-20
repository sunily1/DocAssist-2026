<template>
  <AppLayout>
    <main class="doq-upload" :class="{ 'has-result': conversion }">
      <header v-if="!conversion" class="doq-page-head">
        <h1>쉬운말 검사기</h1>
        <p>맞춤법 검사기처럼, 텍스트를 넣으면 어려운 표현을 그 자리에서 쉬운말로 바꿔 표시해 드려요.</p>
      </header>

      <div v-if="!conversion" class="doq-segment">
        <button :class="{ active: activeUploadTab === 'text' }" type="button" @click="activeUploadTab = 'text'">텍스트 입력</button>
        <button :class="{ active: activeUploadTab === 'file' }" type="button" @click="activeUploadTab = 'file'">파일 첨부</button>
      </div>

      <header v-else class="doq-text-result-head">
        <div class="doq-text-result-title"><span>TXT</span><div><strong>직접 입력 문서</strong><small>변환 완료 · {{ changedTerms.length }}개 표현이 쉬워졌어요</small></div></div>
        <div class="doq-result-actions">
          <button type="button" @click="copyConvertedText">복사</button>
          <button class="primary" type="button" :disabled="downloadingText" @click="downloadText">{{ downloadingText ? "저장 중" : "↓ 쉬운말 DOCX" }}</button>
          <button type="button" @click="resetConversion">새로 입력</button>
        </div>
      </header>

      <template v-if="activeUploadTab === 'text'">
        <section v-if="!conversion" class="doq-editor">
          <div class="doq-editor-head"><strong>변환할 내용</strong><span>{{ textInput.length ? `${textInput.length.toLocaleString()} / 5,000자` : "최대 5,000자" }}</span></div>
          <textarea v-model="textInput" maxlength="5000" placeholder="변환할 문서를 입력하세요." />
          <div class="doq-editor-foot">
            <span>공지·계약서·메일 어떤 글이든 붙여넣어 보세요.</span>
            <button type="button" :disabled="!textInput.trim() || converting" @click="convertInput()">{{ converting ? "검사 중..." : "쉬운말로 검사하기 →" }}</button>
          </div>
        </section>

        <template v-else>
          <div class="doq-result-toolbar">
            <nav class="doq-result-tabs" aria-label="변환 결과 보기 방식">
              <button :class="{ active: resultTab === 'converted' }" type="button" @click="resultTab = 'converted'">쉬운말 보기</button>
              <button :class="{ active: resultTab === 'compare' }" type="button" @click="resultTab = 'compare'">나란히 비교</button>
              <button :class="{ active: resultTab === 'summary' }" type="button" @click="resultTab = 'summary'">요약·용어</button>
            </nav>
          </div>

          <section class="doq-result-grid">
            <article class="doq-result">
              <template v-if="resultTab === 'converted'">
                <div class="doq-result-head">
                  <strong>{{ showOriginal ? "원문" : "쉬운말 문서" }}</strong>
                  <button class="doq-original-toggle" :class="{ on: !showOriginal }" type="button" @click="showOriginal = !showOriginal"><span>✓</span>{{ showOriginal ? "쉬운말 보기" : "원문 보기" }}</button>
                </div>
                <div class="doq-level-row">
                  <span>쉬운 정도</span>
                  <div><button v-for="level in [1, 2, 3]" :key="level" :class="{ active: easyLevel === level }" type="button" :disabled="converting" @click="changeEasyLevel(level)">{{ levelLabel(level) }}</button></div>
                </div>
                <div class="doq-divider" />
                <div v-if="conversion.paragraphs.length" class="doq-reading">
                  <MorphingParagraph
                    v-for="(paragraph, paragraphIndex) in conversion.paragraphs"
                    :key="paragraphIndex"
                    :original="paragraph.original"
                    :easy="paragraph.easy || paragraph.original"
                    :changes="paragraph.changed_terms"
                    :show-original="showOriginal"
                  />
                </div>
                <div v-else class="doq-reading">
                  <MorphingParagraph :original="textInput" :easy="convertedText" :show-original="showOriginal" />
                </div>
              </template>

              <template v-else-if="resultTab === 'compare'">
                <div class="doq-compare-head"><strong>원문</strong><span /><strong>쉬운말</strong></div>
                <div class="doq-side-compare">
                  <div v-for="(paragraph, index) in conversion.paragraphs" :key="index" :class="{ highlighted: selectedChange?.paragraphIndex === index }">
                    <p>{{ paragraph.original }}</p><span>→</span><p>{{ paragraph.easy || paragraph.original }}</p>
                  </div>
                </div>
              </template>

              <template v-else>
                <h2 class="doq-summary-title">핵심 요약</h2>
                <div class="doq-summary-box">{{ conversion.summary || "요약 정보가 없습니다." }}</div>
                <h2 class="doq-summary-title">어려운 용어</h2>
                <div v-if="conversion.terms?.length" class="doq-term-chips"><button v-for="term in conversion.terms" :key="term.term || term.word" type="button">{{ term.term || term.word }}</button></div>
                <p v-else class="doq-empty-terms">표시할 어려운 용어가 없어요.</p>
              </template>

              <div class="doq-result-feedback">
                <template v-if="!resultFeedback"><span>이 쉬운말 변환이 도움이 됐나요?</span><button type="button" :disabled="feedbackSaving" @click="submitResultFeedback('good')">😊</button><button type="button" :disabled="feedbackSaving" @click="submitResultFeedback('soso')">😐</button><button type="button" :disabled="feedbackSaving" @click="submitResultFeedback('bad')">😞</button></template>
                <span v-else class="thanks">✓ 의견을 남겨 주셔서 고마워요.</span>
              </div>
            </article>

            <aside class="doq-result-side">
              <section class="doq-changes">
                <header><strong>바뀐 표현</strong><span>{{ changedTerms.length }}개</span></header>
                <button v-for="item in changedTerms" :key="item.id" type="button" :class="{ active: selectedChange?.id === item.id }" @click="selectedChange = item">
                  <span>{{ item.from }}</span><b>→</b><em>{{ item.to }}</em>
                </button>
                <p v-if="!changedTerms.length">바뀐 표현이 없습니다.</p>
              </section>
              <section class="doq-easy-meter">
                <strong>쉬운 정도</strong>
                <div><span :style="{ width: easyPercent + '%' }" /></div>
                <p>{{ easyMeterLabel }}</p>
              </section>
            </aside>
          </section>
        </template>
      </template>

      <template v-else>
        <section class="doq-file-card">
          <div class="doq-drop" :class="{ dragging }" @dragenter.prevent="onDragEnter" @dragleave.prevent="onDragLeave" @dragover.prevent @drop.prevent="onDrop">
            <div class="doq-upload-icon">↑</div>
            <strong>파일을 끌어다 놓으세요</strong>
            <p>문서 원래 모양 그대로, 쉬운말이 적용되어 보여요 · PDF, DOCX, TXT</p>
            <input ref="fileInput" class="hidden" type="file" accept=".pdf,.docx,.txt" @change="onPick" />
            <button type="button" @click="pickFile">파일 선택</button>
          </div>
          <div v-if="selectedFile" class="doq-selected-file">
            <span class="doq-file-type">{{ fileExt(selectedFile.name) }}</span>
            <div><strong>{{ selectedFile.name }}</strong><small>{{ humanSize(selectedFile.size) }} · 방금 첨부됨</small></div>
            <button type="button" :disabled="uploading" @click="startUpload">{{ uploading ? `변환 중 ${progress}%` : "변환" }}</button>
          </div>
        </section>
      </template>

      <div v-if="!conversion" class="doq-warning"><TriangleAlert :size="17" /><span>AI 변환 결과는 원문 의미와 다를 수 있어요. 중요한 문서는 원문도 함께 확인해 주세요.</span></div>
    </main>


  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import documentService, { type AssistIntensity, type DownloadMode } from "../api/document.service";
import AppLayout from "../components/layout/AppLayout.vue";
import MorphingParagraph from "../components/document/MorphingParagraph.vue";
import { TriangleAlert } from "@lucide/vue";
import userService, { type SatisfactionRating } from "../api/user.service";

interface ConversionTerm {
  from: string;
  to: string;
  definition?: string;
}

interface ConversionParagraph {
  original: string;
  easy: string;
  summary?: string;
  todo?: string[];
  dates?: string[];
  amounts?: string[];
  conditions?: string[];
  changed_terms?: ConversionTerm[];
}

interface ChangeItem extends ConversionTerm {
  id: string;
  paragraphIndex: number;
}

type ResultTab = "converted" | "compare" | "summary";

interface ConversionResult {
  summary: string;
  converted_text: string;
  paragraphs: ConversionParagraph[];
  rules: any[];
  terms: any[];
}

const router = useRouter();
const DEFAULT_INTENSITY: AssistIntensity = "easy";
const activeUploadTab = ref<"text" | "file">("text");
const textInput = ref("");
const conversion = ref<ConversionResult | null>(null);
const converting = ref(false);
const downloadingText = ref(false);
const downloadMode = ref<DownloadMode>("converted");
const selectedChange = ref<ChangeItem | null>(null);
const resultTab = ref<ResultTab>("converted");
const showOriginal = ref(false);
const easyLevel = ref(2);
const resultFeedback = ref("");
const feedbackSaving = ref(false);

const fileInput = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);
const dragging = ref(false);
const uploading = ref(false);
const progress = ref(0);

const convertedText = computed(() => {
  if (!conversion.value) return "";
  const fromParagraphs = conversion.value.paragraphs
    .map((paragraph) => paragraph.easy || paragraph.original)
    .filter(Boolean)
    .join("\n\n");
  return conversion.value.converted_text || fromParagraphs || "변환문이 없습니다.";
});

const changedTerms = computed<ChangeItem[]>(() => {
  if (!conversion.value) return [];
  const seen = new Set<string>();
  const items: ChangeItem[] = [];
  conversion.value.paragraphs.forEach((paragraph, paragraphIndex) => {
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
      seen.add(key);
      items.push({
        id: `${paragraphIndex}-${termIndex}-${from}-${to}`,
        from,
        to,
        definition: String(term.definition || ""),
        paragraphIndex,
      });
    });
  });
  return items;
});

const easyPercent = computed(() => changedTerms.value.length
  ? (easyLevel.value === 1 ? 60 : easyLevel.value === 2 ? 78 : 93)
  : 0);
const easyMeterLabel = computed(() => changedTerms.value.length
  ? `${levelLabel(easyLevel.value)} · ${changedTerms.value.length}개 표현을 쉬운말로 바꿨어요`
  : "바꿀 어려운 표현이 없어 원문을 유지했어요");

function isMeaningfulChange(from: string, to: string) {
  const source = from.replace(/\s+/g, "");
  const replacement = to.replace(/\s+/g, "");
  return Boolean(source && replacement && source !== replacement && !(source.length <= 2 && replacement.length > source.length * 3));
}

onMounted(async () => {
  const savedTheme = (localStorage.getItem("theme") as "light" | "dark") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
  try {
    const response = await userService.getFeedback();
    const rating = response.data?.rating as SatisfactionRating | undefined;
    resultFeedback.value = rating === "satisfied" ? "good" : rating === "neutral" ? "soso" : rating === "dissatisfied" ? "bad" : "";
  } catch (error: any) {
    if (error?.response?.status !== 404) console.error("Failed to load feedback", error);
  }
});

watch(changedTerms, (items) => {
  selectedChange.value = items[0] || null;
});

async function convertInput(intensity: AssistIntensity = DEFAULT_INTENSITY) {
  const text = textInput.value.trim();
  if (!text) return;
  converting.value = true;
  try {
    const res = await documentService.convertText({ text, intensity, title: "직접 입력 문서" });
    conversion.value = res.data;
    easyLevel.value = intensity === "close" ? 1 : intensity === "summary" ? 3 : 2;
    resultTab.value = "converted";
    showOriginal.value = false;
  } catch (e) {
    console.error(e);
    alert("텍스트 변환에 실패했습니다.");
  } finally {
    converting.value = false;
  }
}

async function changeEasyLevel(level: number) {
  if (level === easyLevel.value || converting.value) return;
  const intensity: AssistIntensity = level === 1 ? "close" : level === 3 ? "summary" : "easy";
  await convertInput(intensity);
}

function levelLabel(level: number) {
  return level === 1 ? "살짝" : level === 3 ? "아주 쉽게" : "쉽게";
}

function resetConversion() {
  conversion.value = null;
  resultTab.value = "converted";
  showOriginal.value = false;
  easyLevel.value = 2;
}

async function submitResultFeedback(value: "good" | "soso" | "bad") {
  if (feedbackSaving.value) return;
  feedbackSaving.value = true;
  const rating: SatisfactionRating = value === "good" ? "satisfied" : value === "soso" ? "neutral" : "dissatisfied";
  try {
    await userService.updateFeedback(rating);
    resultFeedback.value = value;
  } catch (error) {
    console.error("Failed to save feedback", error);
    alert("의견을 저장하지 못했습니다. 잠시 후 다시 시도해 주세요.");
  } finally {
    feedbackSaving.value = false;
  }
}

async function copyConvertedText() {
  try {
    await navigator.clipboard.writeText(convertedText.value);
  } catch (error) {
    console.error("Copy failed", error);
  }
}

async function downloadText() {
  const text = textInput.value.trim();
  if (!text) return;
  downloadingText.value = true;
  try {
    const res = await documentService.downloadTextDocx({
      text,
      intensity: DEFAULT_INTENSITY,
      title: "직접 입력 문서",
      mode: resultTab.value === "compare" ? "comparison" : resultTab.value === "summary" ? "summary" : downloadMode.value,
    });
    saveBlob(res.data, "docassist_text_result.docx");
  } catch (e) {
    console.error(e);
    alert("DOCX 다운로드에 실패했습니다.");
  } finally {
    downloadingText.value = false;
  }
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

function pickFile() {
  fileInput.value?.click();
}

function onPick(e: Event) {
  const input = e.target as HTMLInputElement;
  setSelectedFile(input.files?.[0] ?? null);
}

function onDragEnter() {
  dragging.value = true;
}

function onDragLeave() {
  dragging.value = false;
}

function onDrop(e: DragEvent) {
  dragging.value = false;
  setSelectedFile(e.dataTransfer?.files?.[0] ?? null);
}

function setSelectedFile(file: File | null) {
  if (!file) {
    selectedFile.value = null;
    return;
  }
  const extension = fileExt(file.name);
  if (!['PDF', 'DOCX', 'TXT'].includes(extension)) {
    selectedFile.value = null;
    if (fileInput.value) fileInput.value.value = '';
    alert("PDF, DOCX, TXT 파일만 업로드할 수 있습니다.");
    return;
  }
  if (file.size === 0) {
    selectedFile.value = null;
    if (fileInput.value) fileInput.value.value = '';
    alert("빈 파일은 업로드할 수 없습니다.");
    return;
  }
  selectedFile.value = file;
}

function fileExt(name: string) {
  return name.split(".").pop()?.toUpperCase() || "UNKNOWN";
}

function humanSize(bytes: number) {
  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let index = 0;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index++;
  }
  return `${value.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

async function startUpload() {
  if (!selectedFile.value) return;

  uploading.value = true;
  progress.value = 0;

  const timer = window.setInterval(() => {
    if (progress.value < 90) progress.value += 6;
  }, 200);

  try {
    const form = new FormData();
    form.append("file", selectedFile.value);
    const res = await documentService.uploadDocument(form, DEFAULT_INTENSITY);
    progress.value = 100;
    window.clearInterval(timer);
    await new Promise((resolve) => setTimeout(resolve, 350));
    localStorage.setItem("last_document_id", String(res.data.id));
    router.push({ name: "documentView", params: { id: res.data.id } }).catch(() => {});
  } catch (e: any) {
    const status = e?.response?.status;
    const detail = e?.response?.data?.detail;
    if (!status || status >= 500) console.error("Upload failed", e);
    if (status === 401 || status === 403) {
      alert("로그인이 만료되었습니다. 다시 로그인한 뒤 업로드해 주세요.");
      router.push({ name: "login", query: { redirect: "/upload" } }).catch(() => {});
    } else if (detail) {
      alert(String(detail));
    } else {
      alert("업로드에 실패했습니다. PDF, DOCX, TXT 파일인지 확인해 주세요.");
    }
    window.clearInterval(timer);
  } finally {
    uploading.value = false;
  }
}
</script>


<style scoped>
.doq-upload { width: min(1060px, 100%); margin: 0 auto; padding: 34px 40px 56px; }
.doq-page-head h1 { margin: 0 0 5px; font-size: 24px; letter-spacing: -.01em; }
.doq-page-head p { margin: 0 0 22px; color: var(--muted); font-size: 14px; }
.doq-segment { width: fit-content; margin-bottom: 20px; padding: 4px; display: flex; gap: 5px; border-radius: 13px; background: var(--soft); }
.doq-segment button { padding: 9px 18px; border: 0; border-radius: 10px; color: var(--muted); background: transparent; font-size: 13.5px; font-weight: 600; cursor: pointer; }
.doq-segment button.active { color: var(--ink); background: var(--surface); box-shadow: 0 1px 4px rgb(30 20 70 / .1); }
.doq-editor, .doq-result, .doq-changes, .doq-file-card { border: 1px solid var(--line); border-radius: 20px; background: var(--surface); }
.doq-editor { padding: 22px 22px 18px; }
.doq-editor-head { margin-bottom: 12px; display: flex; justify-content: space-between; font-size: 14px; }
.doq-editor-head span { color: var(--muted); font-size: 12px; }
.doq-editor textarea { width: 100%; min-height: 220px; padding: 16px; resize: vertical; border: 1.5px solid var(--line); border-radius: 14px; outline: none; color: var(--ink); background: var(--soft); font-size: 15px; line-height: 1.85; }
.doq-editor textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.doq-editor-foot { margin-top: 14px; display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.doq-editor-foot > span { color: var(--muted); font-size: 12.5px; }
.doq-editor-foot button, .doq-selected-file > button { height: 46px; padding: 0 22px; border: 0; border-radius: 13px; color: #fff; background: var(--accent-gradient); box-shadow: 0 8px 18px rgb(106 77 255 / .24); font-size: 14px; font-weight: 600; cursor: pointer; }
.doq-editor-foot button:disabled { opacity: .5; cursor: default; }
.doq-upload.has-result { width: min(1180px, 100%); padding: 24px 34px 48px; }
.doq-text-result-head { margin-bottom: 18px; display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.doq-text-result-title { min-width: 0; display: flex; align-items: center; gap: 13px; }.doq-text-result-title > span { width: 44px; height: 44px; display: grid; place-items: center; flex: none; border-radius: 13px; color: #5b6472; background: #eef1f4; font-size: 10px; font-weight: 700; }.doq-text-result-title > div { min-width: 0; display: grid; }.doq-text-result-title strong { font-size: 18px; }.doq-text-result-title small { margin-top: 2px; color: var(--muted); font-size: 12.5px; }
.doq-result-actions { display: flex; gap: 8px; }.doq-result-actions button { height: 38px; padding: 0 13px; border: 1px solid var(--line); border-radius: 11px; color: var(--sub); background: var(--surface); font-size: 13px; font-weight: 600; cursor: pointer; }.doq-result-actions button.primary { border: 0; color: #fff; background: var(--accent-gradient); }.doq-result-actions button:disabled { opacity: .5; cursor: default; }
.doq-result-toolbar { margin-bottom: 18px; display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.doq-result-tabs { width: fit-content; padding: 4px; display: flex; gap: 5px; border-radius: 13px; background: var(--soft); }.doq-result-tabs button { padding: 8px 15px; border: 0; border-radius: 9px; color: var(--muted); background: transparent; font-size: 13px; font-weight: 600; cursor: pointer; }.doq-result-tabs button.active { color: var(--ink); background: var(--surface); box-shadow: 0 1px 3px rgb(30 20 70 / .1); }
.doq-result-grid { display: grid; grid-template-columns: minmax(0, 1fr) 290px; gap: 18px; align-items: start; }
.doq-result { min-height: 420px; padding: 30px 36px; }
.doq-result-head { margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between; }.doq-result-head > strong { font-size: 15px; }
.doq-original-toggle { height: 34px; padding: 0 11px; display: flex; align-items: center; gap: 7px; border: 1px solid var(--line); border-radius: 10px; color: var(--muted); background: var(--surface); font-size: 12px; font-weight: 600; cursor: pointer; }.doq-original-toggle > span { width: 18px; height: 18px; display: grid; place-items: center; border-radius: 50%; color: #fff; background: var(--muted); font-size: 10px; }.doq-original-toggle.on { color: var(--accent-strong); background: var(--soft); }.doq-original-toggle.on > span { background: #12a58a; }
.doq-level-row { margin: 2px 0 6px; display: flex; align-items: center; gap: 10px; }.doq-level-row > span { color: var(--muted); font-size: 12.5px; font-weight: 600; }.doq-level-row > div { padding: 3px; display: flex; gap: 3px; border-radius: 10px; background: var(--soft); }.doq-level-row button { padding: 6px 11px; border: 0; border-radius: 8px; color: var(--muted); background: transparent; font-size: 12px; font-weight: 600; cursor: pointer; }.doq-level-row button.active { color: var(--ink); background: var(--surface); box-shadow: 0 1px 3px rgb(0 0 0 / .08); }.doq-level-row button:disabled { cursor: wait; }
.doq-divider { height: 1px; margin: 12px 0 24px; background: var(--line); }
.doq-reading { color: var(--sub); font-size: var(--reader-font-size, 16.5px); line-height: 2.05; white-space: pre-wrap; }.doq-reading p { margin: 0 0 26px; }.doq-reading p:last-child { margin-bottom: 0; }.doq-reading mark { color: var(--ink); background: linear-gradient(transparent 64%, #ddd2ff 64%); font-weight: 700; }
[data-theme="dark"] .doq-reading mark { background: linear-gradient(transparent 64%, #574883 64%); }
.doq-compare-head { margin-bottom: 12px; display: grid; grid-template-columns: 1fr 40px 1fr; color: var(--muted); font-size: 12px; }.doq-compare-head strong:last-child { color: var(--accent); }.doq-side-compare { display: flex; flex-direction: column; gap: 12px; }.doq-side-compare > div { display: grid; grid-template-columns: 1fr 40px 1fr; align-items: center; border-radius: 13px; }.doq-side-compare > div.highlighted { box-shadow: 0 0 0 3px var(--accent-soft); }.doq-side-compare p { margin: 0; padding: 15px 17px; border: 1px solid var(--line); border-radius: 13px; color: var(--muted); background: var(--soft); font-size: 14px; line-height: 1.85; }.doq-side-compare p:last-child { border-color: var(--accent-border); color: var(--ink); background: var(--accent-soft); font-size: 15px; line-height: 1.9; }.doq-side-compare > div > span { color: var(--accent); text-align: center; font-weight: 700; }
.doq-summary-title { margin: 0 0 12px; font-size: 15px; }.doq-summary-box { margin-bottom: 22px; padding: 18px 20px; border: 1px solid var(--line); border-radius: 14px; color: var(--sub); background: var(--soft); font-size: 14.5px; line-height: 1.85; }.doq-term-chips { display: flex; flex-wrap: wrap; gap: 8px; }.doq-term-chips button { padding: 7px 12px; border: 1px solid var(--line); border-radius: 10px; color: var(--ink); background: var(--surface); font-size: 13px; cursor: pointer; }.doq-empty-terms { color: var(--muted); font-size: 13px; }
.doq-result-feedback { margin-top: 26px; padding-top: 20px; display: flex; align-items: center; gap: 8px; border-top: 1px solid var(--line); }.doq-result-feedback > span:first-child { margin-right: 6px; color: var(--sub); font-size: 13.5px; font-weight: 600; }.doq-result-feedback button { width: 42px; height: 42px; border: 1px solid var(--line); border-radius: 12px; background: var(--surface); font-size: 19px; cursor: pointer; }.doq-result-feedback .thanks { color: var(--accent-strong); font-size: 13.5px; font-weight: 600; }
.doq-result-side { display: flex; flex-direction: column; gap: 14px; }.doq-result-side > section { padding: 18px; border: 1px solid var(--line); border-radius: 18px; background: var(--surface); }
.doq-changes { display: flex; flex-direction: column; gap: 8px; }.doq-changes > header { margin-bottom: 6px; display: flex; align-items: baseline; justify-content: space-between; }.doq-changes > header strong { font-size: 14px; }.doq-changes > header span { color: var(--muted); font-size: 12px; }.doq-changes > button { width: 100%; padding: 10px 11px; display: flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 10px; color: var(--ink); background: var(--surface); text-align: left; cursor: pointer; }.doq-changes > button.active { border-color: var(--accent-border); background: var(--accent-soft); }.doq-changes button span { color: #a09eae; text-decoration: line-through; }.doq-changes button b { color: var(--accent); }.doq-changes button em { font-style: normal; font-weight: 600; }.doq-changes > p { margin: 6px 0 0; color: var(--muted); font-size: 12.5px; line-height: 1.6; }
.doq-easy-meter > strong { display: block; margin-bottom: 12px; font-size: 14px; }.doq-easy-meter > div { height: 9px; overflow: hidden; border-radius: 6px; background: var(--soft); }.doq-easy-meter > div span { height: 100%; display: block; background: linear-gradient(90deg,var(--accent),#12b39a); transition: width .3s; }.doq-easy-meter p { margin: 9px 0 0; color: var(--muted); font-size: 12.5px; line-height: 1.5; }
.doq-file-card { padding: 24px; }
.doq-drop { padding: 44px 20px; border: 2px dashed #d9d5ec; border-radius: 16px; background: var(--soft); text-align: center; }
.doq-drop.dragging { border-color: var(--accent); background: var(--accent-soft); }
.doq-upload-icon { width: 56px; height: 56px; margin: 0 auto 16px; display: grid; place-items: center; border-radius: 16px; color: #fff; background: var(--accent-gradient); box-shadow: 0 8px 18px rgb(106 77 255 / .26); font-size: 28px; }
.doq-drop > strong { display: block; margin-bottom: 5px; font-size: 15px; }.doq-drop > p { margin: 0 0 18px; color: var(--muted); font-size: 12.5px; }
.doq-drop > button { height: 42px; padding: 0 20px; border: 0; border-radius: 12px; color: #fff; background: #191527; font-size: 13.5px; font-weight: 600; cursor: pointer; }
.doq-selected-file { margin-top: 16px; padding: 13px 15px; display: flex; align-items: center; gap: 12px; border: 1px solid var(--line); border-radius: 13px; background: var(--soft); }
.doq-file-type { width: 36px; height: 36px; display: grid; place-items: center; flex: none; border-radius: 10px; color: #e14a6b; background: #fdecef; font-size: 9px; font-weight: 700; }
.doq-selected-file > div { min-width: 0; display: grid; flex: 1; }.doq-selected-file strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13.5px; }.doq-selected-file small { margin-top: 2px; color: var(--muted); font-size: 12px; }
.doq-selected-file > button { height: 36px; padding: 0 14px; border-radius: 10px; font-size: 12.5px; }
.doq-warning { margin-top: 18px; padding: 14px 18px; display: flex; align-items: center; gap: 10px; border: 1px solid #f6e6c8; border-radius: 14px; color: #8a6a2a; background: #fff7ea; font-size: 13px; line-height: 1.6; }.doq-warning svg { flex: none; color: #e0952a; }
[data-theme="dark"] .doq-warning { color: #e9c67d; background: #2d281f; }
@media (max-width: 900px) { .doq-text-result-head { align-items: flex-start; flex-direction: column; }.doq-result-grid { grid-template-columns: 1fr; }.doq-result-side { display: grid; grid-template-columns: 1fr 1fr; } }
@media (max-width: 620px) { .doq-upload, .doq-upload.has-result { padding: 24px 18px 40px; }.doq-editor-foot { align-items: stretch; flex-direction: column; }.doq-result-actions { width: 100%; overflow-x: auto; }.doq-result-actions button { white-space: nowrap; }.doq-result-tabs { width: 100%; }.doq-result-tabs button { min-width: 0; flex: 1; padding-inline: 6px; }.doq-result { padding: 22px 18px; }.doq-result-side { grid-template-columns: 1fr; }.doq-side-compare > div, .doq-compare-head { grid-template-columns: 1fr; gap: 8px; }.doq-side-compare > div > span { transform: rotate(90deg); }.doq-compare-head { display: none; }.doq-drop { padding: 34px 16px; }.doq-selected-file { align-items: flex-start; flex-wrap: wrap; }.doq-selected-file > button { width: 100%; } }
</style>
