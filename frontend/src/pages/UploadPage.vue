<template>
  <AppLayout v-slot="{ toggleSidebar }">
    <header class="topbar">
      <div class="tb-left">
        <button class="hamburger" type="button" aria-label="메뉴 열기" @click="toggleSidebar">☰</button>
        <div>
          <div class="tb-title-strong">문서 쉬운말 변환</div>
          <div class="tb-sub">업무 문서를 쉬운 표현, 바뀐 표현, 요약으로 정리합니다.</div>
        </div>
      </div>
    </header>

    <main class="content">
      <section class="work-grid">
        <article class="card">
          <div class="card-head">
            <div>
              <h2>텍스트 직접 입력</h2>
              <p>보고서, 공지, 메일, 회의록 내용을 붙여넣어 바로 변환합니다.</p>
            </div>
            <button class="btn btn-primary" type="button" :disabled="!textInput.trim() || converting" @click="convertInput">
              {{ converting ? "변환 중" : "변환" }}
            </button>
          </div>

          <textarea
            v-model="textInput"
            class="textarea"
            placeholder="변환할 업무 문서를 입력하세요."
          />

          <div v-if="conversion" class="result">
            <section class="converted-card">
              <div class="section-head">
                <div>
                  <div class="label">변환문</div>
                  <p>어려운 표현을 쉬운말로 바꾼 결과입니다.</p>
                </div>
                <span class="count-badge">{{ changedTerms.length }}개 변경</span>
              </div>
              <div class="converted-text">{{ convertedText }}</div>
            </section>

            <section v-if="changedTerms.length" class="changed-card">
              <div class="label">바뀐 표현</div>
              <div class="change-list">
                <button
                  v-for="item in changedTerms"
                  :key="item.id"
                  class="change-chip"
                  type="button"
                  @click="selectedChange = item"
                >
                  <span class="old-word">{{ item.from }}</span>
                  <span>→</span>
                  <strong>{{ item.to }}</strong>
                </button>
              </div>
              <div v-if="selectedChange" class="change-detail">
                <strong>{{ selectedChange.from }} → {{ selectedChange.to }}</strong>
                <span>{{ selectedChange.definition || "설명 정보가 없습니다." }}</span>
              </div>
            </section>

            <section class="summary">
              <div class="label">핵심 요약</div>
              <p>{{ conversion.summary || "요약할 내용이 없습니다." }}</p>
            </section>

            <div class="download-row">
              <select v-model="downloadMode" class="select">
                <option value="converted">변환문만</option>
                <option value="comparison">원문 + 변환문</option>
                <option value="summary">문단 요약 포함</option>
              </select>
              <button class="btn btn-outline" type="button" :disabled="downloadingText" @click="downloadText">
                DOCX 다운로드
              </button>
            </div>

            <section class="compare-list">
              <article v-for="(p, index) in conversion.paragraphs" :key="index" class="compare-card">
                <div class="para-no">{{ index + 1 }}</div>
                <div>
                  <div class="mini-label">원문</div>
                  <p>{{ p.original }}</p>
                  <div class="down-arrow">↓</div>
                  <div class="mini-label">변환문</div>
                  <p class="easy">{{ p.easy || p.original }}</p>
                  <div v-if="paragraphChanges(index).length" class="inline-changes">
                    <span v-for="item in paragraphChanges(index)" :key="item.id">
                      {{ item.from }} → {{ item.to }}
                    </span>
                  </div>
                </div>
              </article>
            </section>
          </div>
        </article>

        <article class="card">
          <div class="card-head">
            <div>
              <h2>파일 업로드</h2>
              <p>PDF, DOCX, TXT 파일을 저장하고 변환 결과를 내 문서함에서 다시 확인합니다.</p>
            </div>
          </div>

          <div
            class="dropzone"
            :class="{ dragging }"
            @dragenter.prevent="onDragEnter"
            @dragleave.prevent="onDragLeave"
            @dragover.prevent
            @drop.prevent="onDrop"
          >
            <div class="dz-title">파일을 끌어오거나 선택하세요.</div>
            <div class="dz-desc">지원 형식: PDF, DOCX, TXT</div>

            <input
              ref="fileInput"
              type="file"
              class="hidden"
              accept=".pdf,.docx,.txt"
              @change="onPick"
            />

            <div class="dz-actions">
              <button class="btn btn-primary" type="button" @click="pickFile">파일 선택</button>
              <button class="btn btn-ghost" type="button" :disabled="!selectedFile || uploading" @click="clearFile">
                선택 해제
              </button>
            </div>
          </div>

          <div v-if="selectedFile" class="selected">
            <div>
              <div class="file-name">{{ selectedFile.name }}</div>
              <div class="muted">{{ humanSize(selectedFile.size) }} · {{ selectedFile.type || fileExt(selectedFile.name) }}</div>
            </div>
            <button class="btn btn-primary" type="button" :disabled="uploading" @click="startUpload">
              {{ uploading ? "업로드 중" : "업로드 시작" }}
            </button>
          </div>

          <div v-if="uploading" class="progress">
            <div class="bar" :style="{ width: `${progress}%` }"></div>
          </div>

          <div class="notice">
            민감정보가 포함된 문서는 업로드 전에 확인하세요. AI 변환 결과는 원문 의미와 다를 수 있어 최종 확인이 필요합니다.
          </div>
        </article>
      </section>
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

function paragraphChanges(index: number) {
  return changedTerms.value.filter((item) => item.paragraphIndex === index);
}

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

function clearFile() {
  if (uploading.value) return;
  selectedFile.value = null;
  if (fileInput.value) fileInput.value.value = "";
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
  display: flex;
  align-items: center;
  gap: 10px;
}

.hamburger,
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
.card p,
.section-head p,
.notice {
  color: var(--muted);
  font-size: 13px;
}

.content {
  max-width: 1120px;
  width: 100%;
  margin: 0 auto;
  padding: 18px 16px 36px;
}

.work-grid,
.result,
.compare-list {
  display: grid;
  gap: 14px;
}

.card,
.converted-card,
.changed-card,
.summary,
.compare-card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 16px;
}

.card-head,
.section-head,
.download-row,
.selected {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.card h2 {
  margin: 0;
  color: var(--ink);
  font-size: 18px;
}

.card p,
.section-head p {
  margin: 5px 0 0;
  line-height: 1.55;
}

.textarea {
  width: 100%;
  min-height: 220px;
  resize: vertical;
  border: 1px solid var(--field-border);
  border-radius: 8px;
  padding: 12px;
  background: var(--field-bg);
  color: var(--ink);
  line-height: 1.6;
  font: inherit;
  box-sizing: border-box;
}

.result {
  margin-top: 14px;
}

.label,
.mini-label {
  color: var(--ink);
  font-weight: 900;
}

.mini-label {
  color: var(--muted);
  font-size: 12px;
}

.converted-text {
  margin-top: 12px;
  padding: 16px;
  min-height: 120px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--field-bg);
  color: var(--ink);
  white-space: pre-wrap;
  line-height: 1.75;
  font-weight: 750;
}

.count-badge,
.change-chip,
.inline-changes span {
  border: 1px solid var(--accent-border);
  background: var(--accent-soft);
  color: var(--accent);
  border-radius: 8px;
  padding: 5px 8px;
  font-size: 12px;
  font-weight: 900;
}

.change-list,
.inline-changes {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.change-chip {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  font: inherit;
  cursor: pointer;
}

.old-word {
  color: var(--muted);
  text-decoration: line-through;
}

.change-detail {
  margin-top: 12px;
  padding: 12px;
  border-radius: 8px;
  background: var(--field-bg);
  color: var(--ink);
  display: grid;
  gap: 5px;
}

.summary p,
.compare-card p {
  margin: 5px 0 0;
  color: var(--ink);
  line-height: 1.7;
}

.compare-card {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 12px;
}

.para-no {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--accent-soft);
  color: var(--accent);
  display: grid;
  place-items: center;
  font-weight: 900;
  font-size: 12px;
}

.down-arrow {
  margin: 8px 0;
  color: var(--accent);
  font-weight: 1000;
}

.easy {
  font-weight: 800;
}

.download-row {
  justify-content: flex-end;
  align-items: center;
}

.dropzone {
  border: 2px dashed var(--field-border);
  border-radius: 8px;
  min-height: 180px;
  display: grid;
  place-items: center;
  align-content: center;
  text-align: center;
  gap: 10px;
  background: var(--field-bg);
}

.dropzone.dragging {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.dz-title,
.file-name {
  color: var(--ink);
  font-weight: 900;
  font-size: 16px;
}

.dz-desc,
.notice {
  color: var(--muted);
  font-size: 12px;
}

.dz-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
}

.selected {
  margin-top: 12px;
  align-items: center;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 12px;
}

.progress {
  margin-top: 12px;
  height: 10px;
  background: var(--accent-soft);
  border-radius: 999px;
  overflow: hidden;
}

.bar {
  height: 100%;
  background: var(--accent);
  transition: width 140ms linear;
}

.notice {
  margin-top: 12px;
  line-height: 1.6;
}

.hidden {
  display: none;
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

.btn-outline {
  background: var(--card);
}

.btn-ghost {
  background: transparent;
}

.select {
  height: 40px;
  border: 1px solid var(--field-border);
  border-radius: 8px;
  padding: 0 10px;
  background: var(--card);
  color: var(--ink);
  font-weight: 800;
}
</style>
