<template>
  <AppLayout>
    <main class="doq-terms">
      <header class="doq-terms-head"><h1>용어집</h1><p>모르는 말은 국어사전에서 바로 찾고, 나만의 용어장에 저장해 두세요.</p></header>
      <section class="doq-dictionary">
        <strong><BookOpen :size="15" />국어사전에서 찾기</strong>
        <form @submit.prevent="lookupDictionaryQuery">
          <label><Search :size="16" /><input v-model.trim="dictionaryQuery" placeholder="모르는 단어를 입력하세요 (예: 잔여, 명시)" /></label>
          <button type="submit" :disabled="dictionarySearchLoading || !dictionaryQuery">{{ dictionarySearchLoading ? "찾는 중" : "찾기" }}</button>
        </form>
        <article v-if="dictionarySearchResults[0]" class="doq-dict-result">
          <div><strong>{{ dictionarySearchResults[0].word || dictionaryQuery }}</strong><button type="button" @click="copyText(dictionarySearchResults[0].definition, '뜻을 복사했습니다.')">뜻 복사</button></div>
          <p>{{ dictionarySearchResults[0].definition }}</p>
          <a v-if="dictionarySearchResults[0].link" :href="dictionarySearchResults[0].link" target="_blank" rel="noreferrer">국어사전에서 더 보기 →</a>
        </article>
        <div v-if="dictionarySearchError" class="doq-dict-error">{{ dictionarySearchError }}</div>
      </section>
      <section class="doq-terms-grid">
        <div class="doq-doc-terms">
          <div class="doq-list-head">
            <div><h2>이 문서의 어려운 용어</h2><span>{{ filteredTerms.length }}개</span></div>
            <div class="doq-term-tools">
              <label><Search :size="14" /><input v-model.trim="query" placeholder="용어 검색" /></label>
              <button type="button" @click="cycleTermSort">{{ sortBy === "freq" ? "빈도순" : sortBy === "alpha" ? "가나다순" : "최근순" }}</button>
            </div>
          </div>
          <div class="doq-term-filters" aria-label="용어 필터">
            <select v-model="docFilter" aria-label="문서 선택">
              <option value="all">문서 전체</option>
              <option v-for="doc in docs" :key="doc.id" :value="doc.id">{{ doc.title }}</option>
            </select>
            <select v-model="tagFilter" aria-label="분류 선택">
              <option value="all">분류 전체</option>
              <option value="legal">법·계약</option>
              <option value="security">보안</option>
              <option value="finance">재무</option>
              <option value="policy">정책</option>
              <option value="general">일반</option>
            </select>
            <label class="doq-pinned-only"><input v-model="pinnedOnly" type="checkbox" /><span>저장한 용어만</span></label>
          </div>
          <div v-if="loading" class="doq-term-empty">용어를 불러오는 중입니다.</div>
          <div v-else-if="pagedTerms.length === 0" class="doq-term-empty">표시할 어려운 용어가 없어요.</div>
          <div v-else class="doq-term-list">
            <article v-for="term in pagedTerms" :key="term.id" class="doq-term-row">
              <div><div><strong>{{ term.term }}</strong><span>·</span><em>{{ tagLabel(term.primaryTag) }}</em></div><p>{{ term.definition }}</p></div>
              <div class="doq-term-actions">
                <button type="button" :disabled="pinSaving" @click="savePinnedTerm(term)">{{ term.isPinned ? "✓ 저장됨" : "＋ 저장" }}</button>
                <button type="button" title="문서에서 보기" aria-label="문서에서 보기" @click="openTermDocument(term)"><ArrowRight :size="15" /></button>
              </div>
            </article>
          </div>
        </div>
        <aside class="doq-my-terms">
          <div class="doq-my-head"><div><h2>내 용어장</h2><span>{{ pinnedTerms.length }}개</span></div><button type="button" @click="exportCsv"><Download :size="13" />내보내기</button></div>
          <div v-if="pinnedTerms.length" class="doq-saved-list">
            <article v-for="term in pinnedTerms" :key="term.id">
              <div><strong>{{ term.term }}</strong><button type="button" aria-label="용어장에서 삭제" @click="removePinnedTerm(term)"><X :size="14" /></button></div>
              <p>{{ term.definition }}</p>
            </article>
          </div>
          <div v-else class="doq-saved-empty">아직 저장한 용어가 없어요.<br />왼쪽에서 ‘저장’을 눌러 보세요.</div>
        </aside>
      </section>
      <div v-if="toast" class="toast" role="status">{{ toast }}</div>
    </main>

  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ArrowRight, BookOpen, Download, Search, X } from "@lucide/vue";
import AppLayout from "../components/layout/AppLayout.vue";
import documentService from "../api/document.service";

type Tag = "legal" | "security" | "finance" | "policy" | "general";
type SortOption = "freq" | "alpha" | "new";

interface DocumentItem {
  id: string;
  title: string;
}

interface TermItem {
  id: string;
  documentId: string;
  documentTitle: string;
  term: string;
  definition: string;
  evidence: string[];
  primaryTag: Tag;
  frequency: number;
  isPinned: boolean;
  createdAt: string;
}

interface DictionaryItem {
  word: string;
  definition: string;
  pos: string;
  link: string;
  source: string;
}

const router = useRouter();
const docs = ref<DocumentItem[]>([]);
const terms = ref<TermItem[]>([]);
const selected = ref<TermItem | null>(null);
const loading = ref(true);
const pinSaving = ref(false);
const errorMessage = ref("");
const toast = ref("");
const query = ref("");
const docFilter = ref("all");
const tagFilter = ref<"all" | Tag>("all");
const sortBy = ref<SortOption>("new");
const pinnedOnly = ref(false);
const dictionaryQuery = ref("");
const dictionarySearchLoading = ref(false);
const dictionarySearchError = ref("");
const dictionarySearchResults = ref<DictionaryItem[]>([]);
const page = ref(1);
const perPage = 8;
let toastTimer: number | undefined;

function normalizeTag(value: unknown): Tag {
  return ["legal", "security", "finance", "policy", "general"].includes(String(value))
    ? String(value) as Tag
    : "general";
}

function mapTerm(raw: any): TermItem {
  return {
    id: raw.id,
    documentId: raw.document_id,
    documentTitle: raw.document_title,
    term: raw.term,
    definition: raw.definition,
    evidence: Array.isArray(raw.evidence) ? raw.evidence : [],
    primaryTag: normalizeTag(raw.primary_tag),
    frequency: Number(raw.frequency || 1),
    isPinned: Boolean(raw.is_pinned),
    createdAt: raw.created_at,
  };
}

async function loadData() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const [documentResponse, termResponse] = await Promise.all([
      documentService.getDocuments(0, 100),
      documentService.getGlossaryTerms(),
    ]);
    docs.value = documentResponse.data.map((doc: any) => ({ id: doc.id, title: doc.title }));
    terms.value = termResponse.data.map(mapTerm);
    if (selected.value) {
      selected.value = terms.value.find((term) => term.id === selected.value?.id) || null;
    }
  } catch (error) {
    console.error("Failed to load glossary", error);
    errorMessage.value = "용어집을 불러오지 못했습니다.";
  } finally {
    loading.value = false;
  }
}

const filteredTerms = computed(() => {
  const keyword = query.value.toLocaleLowerCase("ko-KR");
  const result = terms.value.filter((term) => {
    const matchesQuery = !keyword
      || term.term.toLocaleLowerCase("ko-KR").includes(keyword)
      || term.definition.toLocaleLowerCase("ko-KR").includes(keyword);
    return matchesQuery
      && (docFilter.value === "all" || term.documentId === docFilter.value)
      && (tagFilter.value === "all" || term.primaryTag === tagFilter.value)
      && (!pinnedOnly.value || term.isPinned);
  });

  return result.sort((a, b) => {
    if (sortBy.value === "alpha") return a.term.localeCompare(b.term, "ko");
    if (sortBy.value === "new") return +new Date(b.createdAt) - +new Date(a.createdAt);
    return b.frequency - a.frequency || a.term.localeCompare(b.term, "ko");
  });
});

const totalPages = computed(() => Math.max(1, Math.ceil(filteredTerms.value.length / perPage)));
const pagedTerms = computed(() => filteredTerms.value.slice((page.value - 1) * perPage, page.value * perPage));
const pinnedTerms = computed(() => terms.value.filter((term) => term.isPinned));

watch([query, docFilter, tagFilter, sortBy, pinnedOnly], () => {
  page.value = 1;
  if (selected.value && !filteredTerms.value.some((term) => term.id === selected.value?.id)) {
    selected.value = null;
  }
});

watch(totalPages, (value) => {
  page.value = Math.min(page.value, value);
});

function tagLabel(tag: Tag) {
  return { legal: "법·계약", security: "보안", finance: "재무", policy: "정책", general: "일반" }[tag];
}

function showToast(message: string) {
  toast.value = message;
  if (toastTimer) window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => { toast.value = ""; }, 1800);
}

async function togglePin() {
  if (!selected.value || pinSaving.value) return;
  pinSaving.value = true;
  const next = !selected.value.isPinned;
  try {
    const response = await documentService.setGlossaryPin(selected.value.id, next);
    const updated = mapTerm(response.data);
    terms.value = terms.value.map((term) => term.id === updated.id ? updated : term);
    selected.value = updated;
    showToast(next ? "용어를 고정했습니다." : "고정을 해제했습니다.");
  } catch (error) {
    console.error("Failed to update glossary pin", error);
    showToast("고정 상태를 저장하지 못했습니다.");
  } finally {
    pinSaving.value = false;
  }
}

async function savePinnedTerm(term: TermItem) {
  if (term.isPinned) return;
  selected.value = term;
  await togglePin();
}

async function removePinnedTerm(term: TermItem) {
  selected.value = term;
  await togglePin();
}

function openTermDocument(term: TermItem) {
  localStorage.setItem("last_document_id", term.documentId);
  router.push({ name: "documentView", params: { id: term.documentId } });
}

function cycleTermSort() {
  sortBy.value = sortBy.value === "freq" ? "alpha" : sortBy.value === "alpha" ? "new" : "freq";
}

async function lookupDictionaryQuery() {
  if (!dictionaryQuery.value || dictionarySearchLoading.value) return;
  dictionarySearchLoading.value = true;
  dictionarySearchError.value = "";
  dictionarySearchResults.value = [];
  try {
    const response = await documentService.searchDictionary(dictionaryQuery.value, 5);
    dictionarySearchResults.value = response.data.items || [];
    if (!dictionarySearchResults.value.length) {
      dictionarySearchError.value = "국어사전 결과가 없습니다. API 키 활성화 상태를 확인해 주세요.";
    }
  } catch (error: any) {
    console.error("Failed to search dictionary", error);
    dictionarySearchError.value = error.response?.data?.detail || "국어사전 조회에 실패했습니다.";
  } finally {
    dictionarySearchLoading.value = false;
  }
}

async function copyText(value: string, successMessage: string) {
  try {
    await navigator.clipboard.writeText(value);
    showToast(successMessage);
  } catch {
    showToast("브라우저에서 복사를 허용해 주세요.");
  }
}

function exportCsv() {
  const quote = (value: unknown) => `"${String(value ?? "").replace(/"/g, '""')}"`;
  const rows = filteredTerms.value.map((term) => [
    term.term,
    term.definition,
    tagLabel(term.primaryTag),
    term.documentTitle,
    term.frequency,
    term.evidence.join(" | "),
  ]);
  const csv = "\uFEFF" + [["용어", "쉬운 뜻", "분류", "문서", "빈도", "근거 문장"], ...rows]
    .map((row) => row.map(quote).join(","))
    .join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `docassist_glossary_${new Date().toISOString().slice(0, 10)}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}

onMounted(loadData);
</script>


<style scoped>
.doq-terms { width: min(1000px, 100%); margin: 0 auto; padding: 34px 40px 56px; }
.doq-terms-head h1 { margin: 0 0 5px; font-size: 24px; letter-spacing: -.01em; }.doq-terms-head p { margin: 0 0 22px; color: var(--muted); font-size: 14px; }
.doq-dictionary { margin-bottom: 24px; padding: 18px 20px; border: 1px solid var(--line); border-radius: 18px; background: var(--surface); }.doq-dictionary > strong { margin-bottom: 12px; display: flex; align-items: center; gap: 7px; font-size: 13px; }.doq-dictionary > strong svg { color: var(--accent); }
.doq-dictionary form { display: flex; gap: 8px; }.doq-dictionary form label { height: 46px; padding: 0 14px; display: flex; align-items: center; gap: 9px; flex: 1; border: 1px solid var(--line); border-radius: 12px; color: var(--muted); background: var(--soft); }.doq-dictionary input { min-width: 0; flex: 1; border: 0; outline: 0; color: var(--ink); background: transparent; font-size: 14px; }
.doq-dictionary form > button { height: 46px; padding: 0 20px; border: 0; border-radius: 12px; color: #fff; background: var(--accent-gradient); font-size: 14px; font-weight: 600; cursor: pointer; }.doq-dictionary form > button:disabled { opacity: .5; }
.doq-dict-result { margin-top: 14px; padding: 16px 18px; border: 1px solid var(--line); border-radius: 14px; background: var(--soft); }.doq-dict-result > div { display: flex; align-items: center; justify-content: space-between; }.doq-dict-result > div > strong { font-size: 15px; }.doq-dict-result button { height: 30px; padding: 0 12px; border: 0; border-radius: 9px; color: #fff; background: var(--accent-gradient); font-size: 12px; font-weight: 600; cursor: pointer; }.doq-dict-result p { margin: 7px 0 9px; color: var(--sub); font-size: 14px; line-height: 1.7; }.doq-dict-result a { color: var(--accent); font-size: 12px; font-weight: 600; }
.doq-dict-error { margin-top: 14px; padding: 14px 16px; border: 1px solid #f6e6c8; border-radius: 14px; color: #8a6a2a; background: #fff7ea; font-size: 13px; }
.doq-terms-grid { display: grid; grid-template-columns: 1.15fr .85fr; gap: 18px; align-items: start; }
.doq-list-head { margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; gap: 9px; }.doq-list-head > div:first-child { display: flex; align-items: baseline; gap: 9px; }.doq-list-head h2, .doq-my-head h2 { margin: 0; font-size: 16px; }.doq-list-head span, .doq-my-head span { color: var(--muted); font-size: 12.5px; }
.doq-term-tools { display: flex; gap: 6px; }.doq-term-tools label { width: 150px; height: 34px; padding: 0 11px; display: flex; align-items: center; gap: 7px; border: 1px solid var(--line); border-radius: 10px; color: var(--muted); background: var(--soft); }.doq-term-tools input { min-width: 0; flex: 1; border: 0; outline: 0; color: var(--ink); background: transparent; font-size: 12.5px; }.doq-term-tools > button { height: 34px; padding: 0 11px; border: 1px solid var(--line); border-radius: 10px; color: var(--sub); background: var(--surface); font-size: 12px; font-weight: 600; cursor: pointer; }
.doq-term-filters { margin-bottom: 14px; display: flex; gap: 7px; }
.doq-term-filters select { min-width: 0; height: 36px; padding: 0 10px; border: 1px solid var(--line); border-radius: 10px; color: var(--sub); background: var(--surface); font-size: 12px; }
.doq-term-filters select:first-child { flex: 1; }
.doq-pinned-only { height: 36px; padding: 0 10px; display: flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 10px; color: var(--sub); background: var(--surface); font-size: 12px; white-space: nowrap; cursor: pointer; }
.doq-pinned-only input { accent-color: var(--accent); }
.doq-term-list { display: grid; gap: 12px; }.doq-term-row { padding: 16px 18px; display: flex; align-items: center; gap: 14px; border: 1px solid var(--line); border-radius: 18px; background: var(--surface); }.doq-term-row > div:first-child { min-width: 0; flex: 1; }.doq-term-row > div:first-child > div { display: flex; align-items: center; gap: 9px; }.doq-term-row strong { font-size: 15.5px; }.doq-term-row em { color: var(--accent); font-size: 12.5px; font-style: normal; font-weight: 600; }.doq-term-row p { margin: 5px 0 0; color: var(--muted); font-size: 13px; line-height: 1.6; }
.doq-term-actions { display: flex; gap: 7px; flex: none; }.doq-term-actions button { height: 34px; padding: 0 13px; border: 1px solid var(--line); border-radius: 9px; color: var(--accent-strong); background: var(--surface); font-size: 12.5px; font-weight: 600; cursor: pointer; }.doq-term-actions button:last-child { width: 34px; padding: 0; color: var(--muted); }
.doq-term-empty { padding: 26px; border: 1.5px dashed var(--line); border-radius: 18px; color: var(--muted); background: var(--soft); text-align: center; font-size: 13.5px; }
.doq-my-terms { position: sticky; top: 20px; padding: 18px 18px 8px; border: 1px solid var(--line); border-radius: 18px; background: var(--surface); }.doq-my-head { margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; }.doq-my-head > div { display: flex; align-items: baseline; gap: 8px; }.doq-my-head h2 { font-size: 15px; }.doq-my-head > button { height: 30px; padding: 0 10px; display: flex; align-items: center; gap: 5px; border: 1px solid var(--line); border-radius: 9px; color: var(--sub); background: var(--surface); font-size: 11.5px; font-weight: 600; cursor: pointer; }
.doq-saved-list { max-height: 440px; padding: 2px 4px 12px 0; display: flex; flex-direction: column; gap: 8px; overflow-y: auto; }.doq-saved-list article { padding: 12px 13px; border: 1px solid var(--line); border-radius: 13px; background: var(--soft); }.doq-saved-list article > div { display: flex; align-items: center; justify-content: space-between; gap: 8px; }.doq-saved-list strong { font-size: 13.5px; }.doq-saved-list button { width: 24px; height: 24px; border: 0; border-radius: 7px; color: var(--muted); background: var(--surface); cursor: pointer; }.doq-saved-list p { margin: 5px 0 0; color: var(--muted); font-size: 12.5px; line-height: 1.6; }
.doq-saved-empty { margin-bottom: 10px; padding: 22px 16px; border: 1.5px dashed var(--line); border-radius: 13px; color: var(--muted); background: var(--soft); text-align: center; font-size: 12.5px; }
@media (max-width: 850px) { .doq-terms-grid { grid-template-columns: 1fr; }.doq-my-terms { position: static; } }
@media (max-width: 620px) { .doq-terms { padding: 24px 18px 40px; }.doq-dictionary form { align-items: stretch; flex-direction: column; }.doq-list-head { align-items: stretch; flex-direction: column; }.doq-term-tools label { flex: 1; }.doq-term-filters { flex-wrap: wrap; }.doq-term-filters select:first-child { flex-basis: 100%; }.doq-term-filters select:nth-child(2), .doq-pinned-only { flex: 1; }.doq-term-row { align-items: flex-start; flex-direction: column; }.doq-term-actions { width: 100%; }.doq-term-actions button:first-child { flex: 1; } }
</style>
