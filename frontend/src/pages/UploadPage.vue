<template>
  <AppLayout>
    <main class="doq-upload">
      <header class="doq-page-head">
        <h1>쉬운말 검사기</h1>
        <p>맞춤법 검사기처럼, 텍스트를 넣으면 어려운 표현을 그 자리에서 쉬운말로 바꿔 표시해 드려요.</p>
      </header>

      <div class="doq-segment">
        <button :class="{ active: activeUploadTab === 'text' }" type="button" @click="activeUploadTab = 'text'">텍스트 입력</button>
        <button :class="{ active: activeUploadTab === 'file' }" type="button" @click="activeUploadTab = 'file'">파일 첨부</button>
      </div>

      <template v-if="activeUploadTab === 'text'">
        <section v-if="!conversion" class="doq-editor">
          <div class="doq-editor-head"><strong>변환할 내용</strong><span>{{ textInput.length.toLocaleString() }} / 5,000자</span></div>
          <textarea v-model="textInput" maxlength="5000" placeholder="변환할 문서를 입력하세요." />
          <div class="doq-editor-foot">
            <span>공지·계약서·메일 어떤 글이든 붙여넣어 보세요.</span>
            <button type="button" :disabled="!textInput.trim() || converting" @click="convertInput">{{ converting ? "검사 중..." : "쉬운말로 검사하기 →" }}</button>
          </div>
        </section>

        <section v-else class="doq-result-grid">
          <article class="doq-result">
            <div class="doq-result-head">
              <div><strong>변환 결과</strong><span>{{ changedTerms.length }}곳 바뀜</span></div>
              <button type="button" @click="conversion = null">새로 입력</button>
            </div>
            <p class="doq-result-help">밑줄 친 표현을 누르면 원래 말과 뜻을 볼 수 있어요.</p>
            <div class="doq-divider" />
            <div class="doq-reader">{{ convertedText }}</div>
            <div v-if="conversion.summary" class="doq-summary"><strong>핵심 요약</strong><p>{{ conversion.summary }}</p></div>
          </article>

          <aside class="doq-result-side">
            <section class="doq-changes">
              <strong>바뀐 표현</strong>
              <button v-for="item in changedTerms" :key="item.id" type="button" :class="{ active: selectedChange?.id === item.id }" @click="selectedChange = item">
                <span>{{ item.from }}</span><b>→</b><em>{{ item.to }}</em>
              </button>
              <p v-if="selectedChange">{{ selectedChange.definition || "더 쉬운 업무 표현으로 바꿨어요." }}</p>
            </section>
            <div class="doq-result-actions">
              <button type="button" @click="copyConvertedText">복사</button>
              <button type="button" :disabled="downloadingText" @click="downloadText">{{ downloadingText ? "저장 중" : "저장" }}</button>
            </div>
          </aside>
        </section>
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

      <div class="doq-warning">AI 변환 결과는 원문 의미와 다를 수 있어요. 중요한 문서는 원문도 함께 확인해 주세요.</div>
    </main>


  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import documentService, { type AssistIntensity, type DownloadMode } from "../api/document.service";
import AppLayout from "../components/layout/AppLayout.vue";

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
        definition: String(term.definition || ""),
        paragraphIndex,
      });
    });
  });
  return items;
});

onMounted(() => {
  const savedTheme = (localStorage.getItem("theme") as "light" | "dark") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
});

watch(changedTerms, (items) => {
  selectedChange.value = items[0] || null;
});

async function convertInput() {
  const text = textInput.value.trim();
  if (!text) return;
  converting.value = true;
  try {
    const res = await documentService.convertText({ text, intensity: DEFAULT_INTENSITY, title: "직접 입력 문서" });
    conversion.value = res.data;
  } catch (e) {
    console.error(e);
    alert("텍스트 변환에 실패했습니다.");
  } finally {
    converting.value = false;
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
      mode: downloadMode.value,
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
  selectedFile.value = input.files?.[0] ?? null;
}

function onDragEnter() {
  dragging.value = true;
}

function onDragLeave() {
  dragging.value = false;
}

function onDrop(e: DragEvent) {
  dragging.value = false;
  selectedFile.value = e.dataTransfer?.files?.[0] ?? null;
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
    console.error(e);
    const status = e?.response?.status;
    const detail = e?.response?.data?.detail;
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
.doq-segment button { padding: 8px 15px; border: 0; border-radius: 9px; color: var(--muted); background: transparent; font-size: 13px; font-weight: 600; cursor: pointer; }
.doq-segment button.active { color: var(--ink); background: var(--surface); box-shadow: 0 1px 3px rgb(30 20 70 / .1); }
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
.doq-result-grid { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 18px; align-items: start; }
.doq-result { padding: 26px 30px; }
.doq-result-head { display: flex; align-items: center; justify-content: space-between; }
.doq-result-head > div { display: flex; align-items: center; gap: 9px; }
.doq-result-head strong { font-size: 15px; }
.doq-result-head span { padding: 4px 10px; border-radius: 999px; color: #0c7a68; background: #e7f8f3; font-size: 11.5px; font-weight: 600; }
.doq-result-head > button { height: 34px; padding: 0 13px; border: 1px solid var(--line); border-radius: 10px; color: var(--muted); background: var(--surface); font-size: 12.5px; font-weight: 600; cursor: pointer; }
.doq-result-help { margin: 6px 0 18px; color: var(--muted); font-size: 12.5px; }
.doq-divider { height: 1px; margin-bottom: 22px; background: var(--line); }
.doq-reader { min-height: 180px; white-space: pre-wrap; color: var(--sub); font-size: 16.5px; line-height: 2.05; }
.doq-summary { margin-top: 24px; padding: 16px 18px; border-radius: 14px; background: var(--soft); }
.doq-summary strong { font-size: 13px; }.doq-summary p { margin: 6px 0 0; color: var(--sub); font-size: 13.5px; line-height: 1.7; }
.doq-result-side { display: flex; flex-direction: column; gap: 14px; }
.doq-changes { padding: 18px; display: flex; flex-direction: column; gap: 8px; }
.doq-changes > strong { margin-bottom: 6px; font-size: 14px; }
.doq-changes > button { width: 100%; padding: 10px 11px; display: flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 10px; color: var(--ink); background: var(--surface); text-align: left; cursor: pointer; }
.doq-changes > button.active { border-color: var(--accent-border); background: var(--accent-soft); }
.doq-changes button span { color: #a09eae; text-decoration: line-through; }.doq-changes button b { color: var(--accent); }.doq-changes button em { font-style: normal; font-weight: 600; }
.doq-changes > p { margin: 6px 0 0; color: var(--muted); font-size: 12.5px; line-height: 1.6; }
.doq-result-actions { display: flex; gap: 8px; }
.doq-result-actions button { height: 42px; flex: 1; border: 1px solid var(--line); border-radius: 12px; color: var(--sub); background: var(--surface); font-size: 13px; font-weight: 600; cursor: pointer; }
.doq-result-actions button:last-child { border-color: #191527; color: #fff; background: #191527; }
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
.doq-warning { margin-top: 18px; padding: 14px 18px; border: 1px solid #f6e6c8; border-radius: 14px; color: #8a6a2a; background: #fff7ea; font-size: 13px; line-height: 1.6; }
[data-theme="dark"] .doq-warning { color: #e9c67d; background: #2d281f; }
@media (max-width: 800px) { .doq-result-grid { grid-template-columns: 1fr; }.doq-result-side { display: grid; grid-template-columns: 1fr; } }
@media (max-width: 620px) { .doq-upload { padding: 24px 18px 40px; }.doq-editor-foot { align-items: stretch; flex-direction: column; }.doq-result { padding: 22px 18px; }.doq-drop { padding: 34px 16px; }.doq-selected-file { align-items: flex-start; flex-wrap: wrap; }.doq-selected-file > button { width: 100%; } }
</style>
