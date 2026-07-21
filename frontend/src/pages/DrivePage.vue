<!-- 인수인계용: 문서 목록/관리(드라이브) 화면 -->
<template>
  <AppLayout>
    <main class="doq-drive">
      <header class="doq-drive-head">
        <div><h1>내 드라이브</h1><p>업로드한 문서 {{ docs.length }}건</p></div>
        <button type="button" @click="go('upload')">+ 새 문서 업로드</button>
      </header>

      <section class="doq-drive-filters">
        <label class="doq-search"><span>⌕</span><input v-model="q" placeholder="문서 검색" /></label>
        <select v-model="typeFilter" aria-label="문서 유형"><option value="all">유형 전체</option><option value="PDF">PDF</option><option value="DOCX">DOCX</option><option value="TXT">TXT</option></select>
        <select v-model="statusFilter" aria-label="문서 상태"><option value="all">상태 전체</option><option value="done">완료</option><option value="processing">분석 중</option><option value="queued">대기</option><option value="failed">실패</option></select>
        <select v-model="sortBy" aria-label="정렬"><option value="new">최신순</option><option value="old">오래된순</option><option value="title">제목순</option></select>
      </section>

      <section class="doq-doc-grid">
        <article v-for="doc in pagedDocs" :key="doc.id" class="doq-doc-card" :class="{ disabled: doc.status !== 'done' }" @click="openDoc(doc)">
          <div class="doq-doc-top">
            <span :class="['doq-doc-type', `type-${doc.type.toLowerCase()}`]">{{ doc.type }}</span>
            <div class="doq-doc-actions">
              <span :class="['doq-status', badgeClass(doc.status)]">{{ designStatusLabel(doc.status) }}</span>
              <button type="button" :title="`${doc.title} 삭제`" :aria-label="`${doc.title} 삭제`" :disabled="deletingIds.has(doc.id)" @click.stop="removeDocument(doc)"><Trash2 :size="15" /></button>
            </div>
          </div>
          <strong>{{ doc.title.replace(/\.[^.]+$/, '') }}</strong>
          <p>{{ formatDate(doc.createdAt) }} · {{ designDocMeta(doc.status) }}</p>
        </article>
        <button class="doq-add-card" type="button" @click="go('upload')"><span>+</span><strong>새 문서 추가</strong></button>
      </section>

      <div v-if="filteredDocs.length === 0" class="doq-drive-empty">검색 결과가 없어요.<button type="button" @click="resetFilters">필터 초기화</button></div>
    </main>


  </AppLayout>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import documentService from "../api/document.service";
import { useAuthStore } from "../stores/auth";
import AppLayout from "../components/layout/AppLayout.vue";
import { Trash2 } from "@lucide/vue";

type DocStatus = "queued" | "processing" | "done" | "failed";
type DocType = "PDF" | "DOCX" | "TXT" | "UNKNOWN";

interface DocItem {
  id: string;
  title: string;
  type: DocType;
  status: DocStatus;
  createdAt: string; // ISO 형식
}

const router = useRouter();
const authStore = useAuthStore();

const theme = ref<"light" | "dark">("light");

function applyTheme(next: "light" | "dark") {
  theme.value = next;
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
}

onMounted(async () => {
  const savedTheme = (localStorage.getItem("theme") as "light" | "dark") || "light";
  applyTheme(savedTheme);

  if (authStore.token && !authStore.user) {
      await authStore.fetchUser();
  }
  
  await fetchDocuments();
});

function go(name: string) {
  router.push({ name }).catch(() => {});
}

/* ===== Drive logic ===== */
const q = ref("");
const typeFilter = ref<"all" | DocType>("all");
const statusFilter = ref<"all" | DocStatus>("all");
const sortBy = ref<"new" | "old" | "title">("new");

const page = ref(1);
const perPage = 6;

const docs = ref<DocItem[]>([]);
const selectedIds = ref<Set<string>>(new Set());
const deletingIds = ref<Set<string>>(new Set());

async function fetchDocuments() {
    try {
        const res = await documentService.getDocuments(0, 100);
        const data = res.data;
        docs.value = data.map((d: any) => ({
            id: d.id,
            title: d.title,
            type: (d.file_type || "UNKNOWN") as DocType,
            status: normalizeStatus(d.status),
            createdAt: d.created_at
        }));
    } catch (e) {
        console.error("Failed to fetch documents", e);
    }
}

function normalizeStatus(status: string): DocStatus {
  const value = String(status || "").toLowerCase();
  if (value === "queued") return "queued";
  if (value === "processing") return "processing";
  if (value === "done") return "done";
  if (value === "failed") return "failed";
  return "processing";
}

function badgeClass(status: DocStatus) {
  if (status === "done") return "badge-ok";
  if (status === "processing" || status === "queued") return "badge-warn";
  return "badge-bad";
}
function designStatusLabel(status: DocStatus) {
  if (status === "done") return "완료";
  if (status === "queued") return "대기";
  if (status === "processing") return "변환 중";
  return "실패";
}
function designDocMeta(status: DocStatus) {
  if (status === "done") return "쉬운말 변환 완료";
  if (status === "failed") return "다시 시도 필요";
  return "분석 중";
}
function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString("ko-KR", { year: "numeric", month: "2-digit", day: "2-digit" });
}

const filteredDocs = computed(() => {
  const qq = q.value.trim().toLowerCase();

  let arr = docs.value.filter((d) => {
    const matchQ =
      !qq ||
      d.title.toLowerCase().includes(qq) ||
      d.type.toLowerCase().includes(qq) ||
      d.status.toLowerCase().includes(qq);

    const matchType = typeFilter.value === "all" ? true : d.type === typeFilter.value;
    const matchStatus = statusFilter.value === "all" ? true : d.status === statusFilter.value;
    return matchQ && matchType && matchStatus;
  });

  if (sortBy.value === "new") arr.sort((a, b) => +new Date(b.createdAt) - +new Date(a.createdAt));
  if (sortBy.value === "old") arr.sort((a, b) => +new Date(a.createdAt) - +new Date(b.createdAt));
  if (sortBy.value === "title") arr.sort((a, b) => a.title.localeCompare(b.title, "ko"));

  return arr;
});

const totalPages = computed(() => Math.max(1, Math.ceil(filteredDocs.value.length / perPage)));
const pagedDocs = computed(() => {
  const start = (page.value - 1) * perPage;
  return filteredDocs.value.slice(start, start + perPage);
});

watch([q, typeFilter, statusFilter, sortBy], () => {
  page.value = 1;
  selectedIds.value = new Set();
});

watch(totalPages, () => {
  page.value = Math.min(page.value, totalPages.value);
});

function resetFilters() {
  q.value = "";
  typeFilter.value = "all";
  statusFilter.value = "all";
  sortBy.value = "new";
  page.value = 1;
  selectedIds.value = new Set();
}

function openDoc(doc: DocItem) {
  if (doc.status !== "done") return;
  localStorage.setItem("last_document_id", doc.id);
  router.push({ name: "documentView", params: { id: doc.id } }).catch(() => {});
}

async function removeDocument(doc: DocItem) {
  if (!window.confirm(`'${doc.title}' 문서를 삭제할까요?`)) return;
  deletingIds.value = new Set(deletingIds.value).add(doc.id);
  try {
    await documentService.deleteDocument(doc.id);
    docs.value = docs.value.filter((item) => item.id !== doc.id);
  } catch (error) {
    console.error("Failed to delete document", error);
    alert("문서를 삭제하지 못했습니다. 잠시 후 다시 시도해 주세요.");
  } finally {
    const next = new Set(deletingIds.value);
    next.delete(doc.id);
    deletingIds.value = next;
  }
}

//  액션들
</script>


<style scoped>
.doq-drive { width: min(1120px, 100%); margin: 0 auto; padding: 34px 40px 56px; }
.doq-drive-head { margin-bottom: 22px; display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.doq-drive-head h1 { margin: 0 0 5px; font-size: 24px; letter-spacing: -.01em; }.doq-drive-head p { margin: 0; color: var(--muted); font-size: 14px; }
.doq-drive-head button { height: 44px; padding: 0 18px; border: 0; border-radius: 13px; color: #fff; background: var(--accent-gradient); box-shadow: 0 8px 18px rgb(106 77 255 / .26); font-size: 14px; font-weight: 600; cursor: pointer; }
.doq-drive-filters { margin-bottom: 20px; display: flex; gap: 10px; }
.doq-search { height: 44px; padding: 0 14px; display: flex; align-items: center; gap: 9px; flex: 1; border: 1px solid var(--line); border-radius: 13px; background: var(--surface); }
.doq-search span { color: var(--muted); font-size: 22px; line-height: 1; transform: rotate(-15deg); }.doq-search input { min-width: 0; flex: 1; border: 0; outline: 0; color: var(--ink); background: transparent; font-size: 14px; }
.doq-drive-filters select { height: 44px; padding: 0; appearance: none; border: 1px solid var(--line); border-radius: 13px; color: var(--sub); background: var(--surface); font-size: 13.5px; font-weight: 600; text-align: center; cursor: pointer; }
.doq-drive-filters select { width: 88px; }
.doq-drive-filters select:last-of-type { width: 76px; }
.doq-doc-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.doq-doc-card { min-width: 0; padding: 20px; border: 1px solid var(--line); border-radius: 18px; background: var(--surface); cursor: pointer; transition: border-color .16s ease, transform .16s ease; }
.doq-doc-card:not(.disabled):hover { border-color: var(--accent-border); transform: translateY(-2px); }.doq-doc-card.disabled { cursor: default; }
.doq-doc-top { margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; }
.doq-doc-actions { display: flex; align-items: center; gap: 7px; }
.doq-doc-actions > button { width: 30px; height: 30px; display: grid; place-items: center; border: 1px solid var(--line); border-radius: 9px; color: var(--muted); background: var(--surface); cursor: pointer; }
.doq-doc-actions > button:hover { border-color: #efb4bd; color: #bd3048; background: #fff3f5; }
.doq-doc-actions > button:disabled { opacity: .45; cursor: wait; }
.doq-doc-type { width: 44px; height: 44px; display: grid; place-items: center; border-radius: 13px; color: #e14a6b; background: #fdecef; font-size: 11px; font-weight: 700; }
.doq-doc-type.type-docx { color: #3f68e0; background: #eaf0ff; }.doq-doc-type.type-txt, .doq-doc-type.type-unknown { color: #5b6472; background: #eef1f4; }
.doq-status { padding: 4px 9px; border-radius: 999px; font-size: 11px; font-weight: 600; }.doq-status.badge-ok { color: #0c7a68; background: #e7f8f3; }.doq-status.badge-warn { color: #a9711a; background: #fff6e6; }.doq-status.badge-bad { color: #c0392b; background: #fdeef0; }
.doq-doc-card > strong { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 14.5px; }.doq-doc-card > p { margin: 5px 0 0; color: var(--muted); font-size: 12px; }
.doq-add-card { min-height: 150px; padding: 20px; display: flex; flex-direction: column; align-items: center; justify-content: center; border: 2px dashed #d9d5ec; border-radius: 18px; color: var(--accent); background: var(--soft); cursor: pointer; }
.doq-add-card span { width: 40px; height: 40px; margin-bottom: 10px; display: grid; place-items: center; border: 1px solid #e8e4f5; border-radius: 12px; background: var(--surface); font-size: 20px; }.doq-add-card strong { font-size: 13.5px; }
.doq-drive-empty { margin-top: 20px; padding: 26px; border: 1.5px dashed var(--line); border-radius: 18px; color: var(--muted); background: var(--soft); text-align: center; font-size: 13.5px; }
.doq-drive-empty button { margin-left: 8px; padding: 0; border: 0; color: var(--accent); background: transparent; font-weight: 600; cursor: pointer; }
@media (max-width: 960px) { .doq-doc-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 620px) { .doq-drive { padding: 24px 18px 40px; }.doq-drive-head button { width: 44px; padding: 0; overflow: hidden; white-space: nowrap; font-size: 0 !important; }.doq-drive-head button::before { content: "+"; font-size: 22px; }.doq-drive-filters { flex-wrap: wrap; }.doq-search { flex-basis: 100%; }.doq-drive-filters select { flex: 1; }.doq-doc-grid { grid-template-columns: 1fr; } }
</style>
