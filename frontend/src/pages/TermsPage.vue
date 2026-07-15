<template>
  <AppLayout v-slot="{ toggleSidebar }">
    <header class="topbar">
      <div class="title-wrap">
        <button class="icon-button menu-button" type="button" aria-label="메뉴 열기" @click="toggleSidebar">☰</button>
        <div>
          <div class="title-line">
            <h1>용어집</h1>
            <span>문서에서 찾은 어려운 표현을 모아 보여줍니다.</span>
          </div>
          <div class="meta-line">
            <strong>총 {{ filteredTerms.length }}개</strong>
            <span>{{ selectedDocLabel }}</span>
          </div>
        </div>
      </div>

      <div class="top-actions">
        <button class="button secondary" type="button" :disabled="filteredTerms.length === 0" @click="exportCsv">
          CSV 내보내기
        </button>
        <button class="button primary" type="button" @click="goUpload">문서 업로드</button>
      </div>
    </header>

    <main class="content">
      <section class="filters" aria-label="용어 필터">
        <select v-model="docFilter" class="field">
          <option value="all">문서 전체</option>
          <option v-for="doc in docs" :key="doc.id" :value="doc.id">{{ doc.title }}</option>
        </select>

        <select v-model="tagFilter" class="field">
          <option value="all">분류 전체</option>
          <option value="legal">법·계약</option>
          <option value="security">보안</option>
          <option value="finance">재무</option>
          <option value="policy">정책</option>
          <option value="general">일반</option>
        </select>

        <select v-model="sortBy" class="field">
          <option value="freq">빈도순</option>
          <option value="alpha">가나다순</option>
          <option value="new">최근 추가순</option>
        </select>

        <input v-model.trim="query" class="field search" type="search" placeholder="용어 또는 뜻 검색" />
        <button class="button secondary" type="button" @click="resetFilters">초기화</button>
      </section>

      <section class="dictionary-search" aria-label="국어사전 단어 검색">
        <div>
          <h2>국어사전 단어 검색</h2>
          <p>문서에 없는 단어도 바로 찾아볼 수 있습니다.</p>
        </div>
        <form class="dictionary-search-form" @submit.prevent="lookupDictionaryQuery">
          <input
            v-model.trim="dictionaryQuery"
            class="field"
            type="search"
            placeholder="검색할 단어 입력"
            autocomplete="off"
          />
          <button class="button primary" type="submit" :disabled="dictionarySearchLoading || !dictionaryQuery">
            {{ dictionarySearchLoading ? "검색 중" : "검색" }}
          </button>
        </form>
        <div v-if="dictionarySearchError" class="dictionary-error">{{ dictionarySearchError }}</div>
        <div v-else-if="dictionarySearchResults.length" class="dictionary-list dictionary-search-results">
          <article v-for="item in dictionarySearchResults" :key="item.word + item.definition" class="dictionary-item">
            <div class="dictionary-head">
              <strong>{{ item.word || dictionaryQuery }}</strong>
              <span v-if="item.pos">{{ item.pos }}</span>
            </div>
            <p>{{ item.definition }}</p>
            <a v-if="item.link" :href="item.link" target="_blank" rel="noreferrer">원문 보기</a>
          </article>
        </div>
      </section>

      <div v-if="errorMessage" class="notice error" role="alert">
        <span>{{ errorMessage }}</span>
        <button type="button" @click="loadData">다시 시도</button>
      </div>

      <section class="workspace">
        <article class="panel list-panel">
          <div class="panel-header">
            <h2>용어 목록</h2>
            <button class="text-button" type="button" @click="pinnedOnly = !pinnedOnly">
              {{ pinnedOnly ? "전체 보기" : "고정한 용어만" }}
            </button>
          </div>

          <div v-if="loading" class="empty-state">용어를 불러오는 중입니다.</div>
          <div v-else-if="filteredTerms.length === 0" class="empty-state">
            <template v-if="terms.length === 0">
              <strong>아직 저장된 용어가 없습니다.</strong>
              <span>문서를 업로드하고 변환하면 어려운 표현이 이곳에 모입니다.</span>
              <button class="button primary" type="button" @click="goUpload">문서 업로드</button>
            </template>
            <template v-else>
              <strong>조건에 맞는 용어가 없습니다.</strong>
              <button class="text-button" type="button" @click="resetFilters">필터 초기화</button>
            </template>
          </div>

          <ul v-else class="term-list">
            <li v-for="term in pagedTerms" :key="term.id">
              <button
                class="term-row"
                :class="{ active: selected?.id === term.id }"
                type="button"
                @click="selected = term"
              >
                <span class="term-main">
                  <span class="term-name">{{ term.term }}</span>
                  <span class="term-context">
                    <span class="tag">{{ tagLabel(term.primaryTag) }}</span>
                    <span>{{ term.documentTitle }}</span>
                  </span>
                </span>
                <span class="term-side">
                  <span>{{ term.frequency }}회</span>
                  <span v-if="term.isPinned" title="고정됨">★</span>
                </span>
              </button>
            </li>
          </ul>

          <div v-if="filteredTerms.length > 0" class="pagination">
            <span>{{ page }} / {{ totalPages }} 페이지</span>
            <div>
              <button class="icon-button" type="button" aria-label="이전 페이지" :disabled="page === 1" @click="page--">‹</button>
              <button class="icon-button" type="button" aria-label="다음 페이지" :disabled="page === totalPages" @click="page++">›</button>
            </div>
          </div>
        </article>

        <article class="panel detail-panel">
          <div class="panel-header">
            <h2>용어 설명</h2>
            <button class="button secondary small" type="button" :disabled="!selected" @click="openDocument">
              문서에서 보기
            </button>
          </div>

          <div v-if="!selected" class="empty-state">
            <strong>확인할 용어를 선택하세요.</strong>
            <span>쉬운 뜻과 원문에서 사용된 문장을 함께 보여드립니다.</span>
          </div>

          <div v-else class="detail-body">
            <div class="term-heading">
              <div>
                <span class="tag">{{ tagLabel(selected.primaryTag) }}</span>
                <h3>{{ selected.term }}</h3>
                <p>{{ selected.documentTitle }} · 문서 내 {{ selected.frequency }}회</p>
              </div>
              <button
                class="icon-button pin-button"
                type="button"
                :title="selected.isPinned ? '고정 해제' : '용어 고정'"
                :aria-label="selected.isPinned ? '고정 해제' : '용어 고정'"
                :disabled="pinSaving"
                @click="togglePin"
              >
                {{ selected.isPinned ? "★" : "☆" }}
              </button>
            </div>

            <section class="detail-section">
              <div class="section-title">
                <h4>쉬운 뜻</h4>
                <button class="text-button" type="button" @click="copyText(selected.definition, '뜻을 복사했습니다.')">복사</button>
              </div>
              <p class="definition">{{ selected.definition }}</p>
            </section>

            <section class="detail-section">
              <div class="section-title">
                <h4>국어사전</h4>
                <button
                  class="text-button"
                  type="button"
                  :disabled="dictionaryLoading"
                  @click="lookupDictionary"
                >
                  {{ dictionaryLoading ? "조회 중" : "사전 뜻 조회" }}
                </button>
              </div>
              <div v-if="dictionaryError" class="dictionary-error">{{ dictionaryError }}</div>
              <div v-else-if="dictionaryResults.length" class="dictionary-list">
                <article v-for="item in dictionaryResults" :key="item.word + item.definition" class="dictionary-item">
                  <div class="dictionary-head">
                    <strong>{{ item.word || selected.term }}</strong>
                    <span v-if="item.pos">{{ item.pos }}</span>
                  </div>
                  <p>{{ item.definition }}</p>
                  <a v-if="item.link" :href="item.link" target="_blank" rel="noreferrer">원문 보기</a>
                </article>
              </div>
              <p v-else class="muted">선택한 용어의 국어사전 뜻을 조회할 수 있습니다.</p>
            </section>

            <section class="detail-section">
              <div class="section-title"><h4>문서에서 사용된 문장</h4></div>
              <ol v-if="selected.evidence.length" class="evidence-list">
                <li v-for="sentence in selected.evidence" :key="sentence">{{ sentence }}</li>
              </ol>
              <p v-else class="muted">원문에서 일치하는 문장을 찾지 못했습니다.</p>
            </section>

            <div class="detail-actions">
              <button class="button primary" type="button" @click="askAboutTerm">Q&A에서 질문</button>
              <button class="button secondary" type="button" @click="copyText(selected.term, '용어를 복사했습니다.')">용어 복사</button>
            </div>
          </div>
        </article>
      </section>
    </main>

    <div v-if="toast" class="toast" role="status">{{ toast }}</div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
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
const sortBy = ref<SortOption>("freq");
const pinnedOnly = ref(false);
const dictionaryLoading = ref(false);
const dictionaryError = ref("");
const dictionaryResults = ref<DictionaryItem[]>([]);
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
const selectedDocLabel = computed(() => {
  if (docFilter.value === "all") return "모든 문서";
  return docs.value.find((doc) => doc.id === docFilter.value)?.title || "선택 문서";
});

watch([query, docFilter, tagFilter, sortBy, pinnedOnly], () => {
  page.value = 1;
  if (selected.value && !filteredTerms.value.some((term) => term.id === selected.value?.id)) {
    selected.value = null;
  }
});

watch(selected, () => {
  dictionaryError.value = "";
  dictionaryResults.value = [];
});

watch(totalPages, (value) => {
  page.value = Math.min(page.value, value);
});

function tagLabel(tag: Tag) {
  return { legal: "법·계약", security: "보안", finance: "재무", policy: "정책", general: "일반" }[tag];
}

function resetFilters() {
  query.value = "";
  docFilter.value = "all";
  tagFilter.value = "all";
  sortBy.value = "freq";
  pinnedOnly.value = false;
  selected.value = null;
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

async function lookupDictionary() {
  if (!selected.value || dictionaryLoading.value) return;
  dictionaryLoading.value = true;
  dictionaryError.value = "";
  dictionaryResults.value = [];
  try {
    const response = await documentService.searchDictionary(selected.value.term, 5);
    dictionaryResults.value = response.data.items || [];
    if (!dictionaryResults.value.length) {
      dictionaryError.value = "국어사전 결과가 없습니다. API 키 활성화 상태를 확인해 주세요.";
    }
  } catch (error: any) {
    console.error("Failed to lookup dictionary", error);
    dictionaryError.value = error.response?.data?.detail || "국어사전 조회에 실패했습니다.";
  } finally {
    dictionaryLoading.value = false;
  }
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

function openDocument() {
  if (!selected.value) return;
  router.push({ name: "documentView", params: { id: selected.value.documentId } });
}

function askAboutTerm() {
  if (!selected.value) return;
  router.push({
    name: "qa",
    query: {
      documentId: selected.value.documentId,
      question: `이 문서에서 '${selected.value.term}'은 무슨 뜻이야?`,
    },
  });
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

function goUpload() {
  router.push({ name: "upload" });
}

onMounted(loadData);
</script>

<style scoped>
.topbar {
  min-height: 76px;
  padding: 10px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  background: var(--topbar-bg);
  border-bottom: 1px solid var(--line);
}
.title-wrap, .title-line, .meta-line, .top-actions, .panel-header, .section-title, .detail-actions, .pagination, .pagination div { display: flex; align-items: center; }
.title-wrap { gap: 12px; min-width: 0; }
.title-line { gap: 10px; flex-wrap: wrap; }
.title-line h1 { margin: 0; font-size: 18px; color: var(--ink); }
.title-line span, .meta-line span { color: var(--muted); }
.meta-line { gap: 10px; margin-top: 3px; font-size: 12px; }
.meta-line strong { color: var(--ink); }
.top-actions { gap: 10px; flex-wrap: wrap; }
.menu-button { display: none; }
.content { width: 100%; max-width: 1500px; margin: 0 auto; padding: 20px 18px 32px; display: grid; gap: 16px; }
.filters { display: grid; grid-template-columns: 190px 150px 150px minmax(240px, 1fr) auto; gap: 10px; }
.field, .button, .icon-button { min-height: 44px; border: 1px solid var(--field-border); background: var(--field-bg); color: var(--field-text); font: inherit; }
.field { width: 100%; padding: 0 12px; border-radius: 8px; outline: none; }
.field:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.button { border-radius: 8px; padding: 0 15px; font-weight: 800; cursor: pointer; white-space: nowrap; }
.button.primary { color: #fff; background: var(--accent); border-color: var(--accent); }
.button.secondary { background: transparent; color: var(--ink); }
.button.small { min-height: 38px; padding: 0 12px; }
.button:disabled, .icon-button:disabled { opacity: .45; cursor: not-allowed; }
.icon-button { width: 44px; padding: 0; border-radius: 8px; display: inline-grid; place-items: center; cursor: pointer; font-size: 20px; }
.notice { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px 14px; border: 1px solid #fecaca; border-radius: 8px; color: #991b1b; background: #fef2f2; }
.notice button, .text-button { border: 0; padding: 5px; background: transparent; color: var(--accent); font: inherit; font-weight: 800; cursor: pointer; }
.dictionary-search { padding: 16px; border: 1px solid var(--line); border-radius: 8px; background: var(--card); display: grid; gap: 12px; }
.dictionary-search h2 { margin: 0; color: var(--ink); font-size: 17px; }
.dictionary-search p { margin: 4px 0 0; color: var(--muted); font-size: 13px; }
.dictionary-search-form { display: grid; grid-template-columns: minmax(220px, 1fr) auto; gap: 10px; }
.dictionary-search-results { margin-top: 2px; }
.workspace { min-height: 620px; display: grid; grid-template-columns: minmax(360px, .85fr) minmax(440px, 1.15fr); gap: 16px; }
.panel { min-width: 0; padding: 18px; display: flex; flex-direction: column; background: var(--card); border: 1px solid var(--line); border-radius: 8px; }
.panel-header { min-height: 44px; justify-content: space-between; gap: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--line); }
.panel-header h2 { margin: 0; font-size: 18px; color: var(--ink); }
.empty-state { flex: 1; min-height: 300px; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 12px; text-align: center; color: var(--muted); }
.empty-state strong { color: var(--ink); font-size: 17px; }
.term-list { list-style: none; margin: 12px 0 0; padding: 0; flex: 1; min-height: 0; overflow: auto; }
.term-list li + li { border-top: 1px solid var(--line); }
.term-row { width: 100%; min-height: 76px; padding: 12px; border: 0; border-left: 3px solid transparent; display: flex; align-items: center; justify-content: space-between; gap: 14px; text-align: left; color: var(--ink); background: transparent; cursor: pointer; }
.term-row:hover, .term-row.active { background: var(--accent-soft); border-left-color: var(--accent); }
.term-main { min-width: 0; display: grid; gap: 7px; }
.term-name { font-weight: 900; font-size: 16px; word-break: break-word; }
.term-context { min-width: 0; display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 12px; }
.term-context > span:last-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tag { width: max-content; padding: 3px 7px; border: 1px solid var(--accent-border); border-radius: 6px; color: var(--accent); background: var(--accent-soft); font-size: 12px; font-weight: 800; }
.term-side { flex: 0 0 auto; display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 12px; }
.pagination { justify-content: space-between; gap: 12px; padding-top: 12px; border-top: 1px solid var(--line); color: var(--muted); font-size: 12px; }
.pagination div { gap: 6px; }
.detail-body { padding-top: 18px; min-height: 0; overflow: auto; }
.term-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; }
.term-heading h3 { margin: 12px 0 4px; color: var(--ink); font-size: 27px; word-break: break-word; }
.term-heading p { margin: 0; color: var(--muted); }
.pin-button { flex: 0 0 auto; }
.detail-section { padding: 20px 0; border-top: 1px solid var(--line); }
.detail-section:first-of-type { margin-top: 22px; }
.section-title { justify-content: space-between; gap: 12px; }
.section-title h4 { margin: 0 0 10px; color: var(--ink); font-size: 15px; }
.definition { margin: 0; color: var(--ink); line-height: 1.8; }
.dictionary-list { display: grid; gap: 10px; }
.dictionary-item { padding: 12px; border: 1px solid var(--line); border-radius: 8px; background: var(--field-bg); }
.dictionary-head { display: flex; align-items: center; gap: 8px; color: var(--ink); }
.dictionary-head span { color: var(--muted); font-size: 12px; font-weight: 800; }
.dictionary-item p { margin: 8px 0 0; color: var(--ink); line-height: 1.7; }
.dictionary-item a { display: inline-block; margin-top: 8px; color: var(--accent); font-weight: 800; text-decoration: none; }
.dictionary-error { color: #991b1b; font-weight: 800; }
:global([data-theme="dark"]) .dictionary-error { color: #fda4af; }
.evidence-list { margin: 0; padding-left: 24px; display: grid; gap: 12px; color: var(--ink); line-height: 1.7; }
.evidence-list li::marker { color: var(--accent); font-weight: 800; }
.muted { color: var(--muted); }
.detail-actions { gap: 10px; flex-wrap: wrap; padding-top: 4px; }
.toast { position: fixed; right: 24px; bottom: 24px; z-index: 50; padding: 12px 16px; border-radius: 8px; color: #fff; background: #111827; box-shadow: 0 8px 24px rgba(0,0,0,.18); }
:global([data-theme="dark"]) .notice.error { color: #fecaca; background: #451a1a; border-color: #7f1d1d; }

@media (max-width: 1040px) {
  .filters { grid-template-columns: repeat(3, 1fr); }
  .search { grid-column: span 2; }
  .workspace { grid-template-columns: 1fr; }
  .panel { min-height: 480px; }
}
@media (max-width: 720px) {
  .topbar { padding: 14px 16px; align-items: flex-start; flex-wrap: wrap; }
  .menu-button { display: inline-grid; }
  .title-line span { display: none; }
  .top-actions { width: 100%; justify-content: flex-end; }
  .content { padding: 14px; }
  .filters { grid-template-columns: 1fr; }
  .dictionary-search-form { grid-template-columns: 1fr; }
  .search { grid-column: auto; }
  .workspace { min-height: 0; }
  .panel { min-height: 420px; padding: 14px; }
}
</style>


