<!-- 인수인계용: 문서 목록/관리(드라이브) 화면 -->
<template>
  <AppLayout v-slot="{ toggleSidebar }">
    <!-- 상단바 -->
    <header class="topbar">
      <div class="tb-left">
        <div class="tb-title">
          <button class="hamburger" @click="toggleSidebar" aria-label="Open menu">☰</button>
          <span class="tb-title-strong">내 드라이브</span>
          <span class="tb-sub">· 업로드한 문서를 관리하세요</span>
        </div>

        <div class="tb-meta">
          <span class="pill">총 {{ filteredDocs.length }}건</span>
          <span class="muted">·</span>
          <span class="muted">최근 {{ recentDays }}일</span>
        </div>
      </div>

      <div class="tb-right">
        <button class="btn btn-outline" type="button" @click="refreshMock">새로고침</button>
        <button class="btn btn-primary" type="button" @click="go('upload')">+ 새 문서 업로드</button>
      </div>
    </header>

    <!-- 본문 -->
    <main class="content">
      <!-- 검색 / 필터 -->
      <section class="filters">
        <div class="search">
          <input
            v-model="q"
            class="input"
            placeholder="문서 제목/유형/상태로 검색..."
            @keydown.enter.prevent
          />
        </div>

        <div class="selects">
          <select class="select" v-model="typeFilter">
            <option value="all">유형 전체</option>
            <option value="PDF">PDF</option>
            <option value="DOCX">DOCX</option>
            <option value="TXT">TXT</option>
          </select>

          <select class="select" v-model="statusFilter">
            <option value="all">상태 전체</option>
            <option value="done">분석 완료</option>
            <option value="queued">대기 중</option>
            <option value="processing">분석 중</option>
            <option value="failed">실패</option>
          </select>

          <select class="select" v-model="sortBy">
            <option value="new">최신순</option>
            <option value="old">오래된순</option>
            <option value="title">제목순</option>
          </select>
        </div>
      </section>

      <!-- 목록 테이블 -->
      <section class="card">
        <div class="card-head">
          <h2>문서 목록</h2>
          <div class="head-actions">
            <button class="link" type="button" @click="selectAll">전체 선택</button>
            <button class="link" type="button" @click="clearSelect">선택 해제</button>
            <button
              class="btn btn-outline btn-sm"
              type="button"
              :disabled="selectedIds.size === 0"
              @click="deleteMock"
            >
              삭제
            </button>
          </div>
        </div>

        <div v-if="filteredDocs.length === 0" class="empty">
          검색 결과가 없어요.
          <button class="inline" type="button" @click="resetFilters">필터 초기화</button>
        </div>

        <div v-else class="table">
          <div class="thead">
            <div class="th chk"></div>
            <div class="th title">제목</div>
            <div class="th meta">유형</div>
            <div class="th meta">상태</div>
            <div class="th meta">업로드</div>
            <div class="th actions">작업</div>
          </div>

          <div
            v-for="doc in pagedDocs"
            :key="doc.id"
            class="trow"
            :class="{ selected: selectedIds.has(doc.id) }"
          >
            <div class="td chk">
              <input
                type="checkbox"
                :checked="selectedIds.has(doc.id)"
                @change="toggleSelect(doc.id)"
              />
            </div>

            <div class="td title">
              <div class="doc-title">{{ doc.title }}</div>
              <div class="doc-sub muted">ID: {{ doc.id }}</div>
            </div>

            <div class="td meta">
              <span class="chip">{{ doc.type }}</span>
            </div>

            <div class="td meta">
              <span :class="['badge', badgeClass(doc.status)]">
                {{ statusLabel(doc.status) }}
              </span>
            </div>

            <div class="td meta muted">{{ formatDate(doc.createdAt) }}</div>

            <div class="td actions">
              <button
                class="btn btn-sm"
                type="button"
                @click="openDoc(doc)"
                :disabled="doc.status !== 'done'"
              >
                열기
              </button>
              <button class="btn btn-sm btn-outline" type="button" @click="renameMock()">
                이름변경
              </button>
            </div>
          </div>
        </div>

        <!-- 페이지네이션 -->
        <div v-if="filteredDocs.length > 0" class="pager">
          <div class="muted">페이지 {{ page }} / {{ totalPages }}</div>
          <div class="pager-actions">
            <button class="btn btn-outline btn-sm" type="button" :disabled="page <= 1" @click="page--">
              이전
            </button>
            <button
              class="btn btn-outline btn-sm"
              type="button"
              :disabled="page >= totalPages"
              @click="page++"
            >
              다음
            </button>
          </div>
        </div>
      </section>

      <!-- 우측 요약/통계 -->
      <section class="grid">
        <article class="card">
          <div class="card-head">
            <h2>상태 요약</h2>
          </div>

          <div class="stat-grid">
            <div class="stat">
              <div class="stat-label">분석 완료</div>
              <div class="stat-value">{{ counts.done }}</div>
            </div>
            <div class="stat">
              <div class="stat-label">분석 중</div>
              <div class="stat-value">{{ counts.processing }}</div>
            </div>
            <div class="stat">
              <div class="stat-label">실패</div>
              <div class="stat-value">{{ counts.failed }}</div>
            </div>
            <div class="stat">
              <div class="stat-label">전체</div>
              <div class="stat-value">{{ counts.total }}</div>
            </div>
          </div>
        </article>

        <article class="card">
          <div class="card-head">
            <h2>선택한 문서</h2>
          </div>

          <div v-if="selectedIds.size === 0" class="empty small">
            아직 선택한 문서가 없어요.
          </div>

          <div v-else>
            <ul class="sel-list">
              <li v-for="id in Array.from(selectedIds)" :key="id" class="sel-item">
                <span class="sel-dot"></span>
                <span class="sel-text">{{ getDocTitle(id) }}</span>
              </li>
            </ul>

            <div class="batch-actions">
              <button class="btn btn-primary btn-sm full" type="button" @click="batchExport">
                일괄 내보내기
              </button>
              <button class="btn btn-outline btn-sm full" type="button" @click="deleteMock">
                일괄 삭제
              </button>
            </div>
          </div>
        </article>
      </section>
    </main>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import documentService from "../api/document.service";
import { useAuthStore } from "../stores/auth";
import AppLayout from "../components/layout/AppLayout.vue";

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
const recentDays = 30;
const q = ref("");
const typeFilter = ref<"all" | DocType>("all");
const statusFilter = ref<"all" | DocStatus>("all");
const sortBy = ref<"new" | "old" | "title">("new");

const page = ref(1);
const perPage = 6;

const docs = ref<DocItem[]>([]);
const selectedIds = ref<Set<string>>(new Set());

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
function statusLabel(status: DocStatus) {
  if (status === "done") return "분석 완료";
  if (status === "queued") return "대기 중";
  if (status === "processing") return "분석 중";
  if (status === "failed") return "실패";
  return status;
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

const counts = computed(() => {
  const all = filteredDocs.value;
  return {
    total: all.length,
    done: all.filter((d) => d.status === "done").length,
    processing: all.filter((d) => d.status === "processing" || d.status === "queued").length,
    failed: all.filter((d) => d.status === "failed").length,
  };
});

function resetFilters() {
  q.value = "";
  typeFilter.value = "all";
  statusFilter.value = "all";
  sortBy.value = "new";
  page.value = 1;
  selectedIds.value = new Set();
}

function toggleSelect(id: string) {
  const next = new Set(selectedIds.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  selectedIds.value = next;
}
function selectAll() {
  selectedIds.value = new Set(filteredDocs.value.map((d) => d.id));
}
function clearSelect() {
  selectedIds.value = new Set();
}

function getDocTitle(id: string) {
  const doc = docs.value.find((d) => d.id === id);
  return doc ? doc.title : id;
}

function openDoc(doc: DocItem) {
  if (doc.status !== "done") return;
  router.push({ name: "documentView", params: { id: doc.id } }).catch(() => {});
}

//  액션들
async function refreshMock() {
  await fetchDocuments();
}
function renameMock() {
  // 이름 변경 API 필요(현재는 화면 알림 또는 임시 처리)
  // const name = prompt("새 제목을 입력하세요", doc.title);
  // if (!name) return;
  alert("이름 변경 API 연동 필요");
}
async function deleteMock() {
  if (selectedIds.value.size === 0) return;
  const ok = confirm(`선택한 ${selectedIds.value.size}개 문서를 삭제할까요?`);
  if (!ok) return;
  
  // 선택 문서별 API 호출
  for (const id of selectedIds.value) {
      try {
          await documentService.deleteDocument(id);
      } catch (e) {
          console.error(`Failed to delete doc ${id}`, e);
      }
  }
  
  await fetchDocuments();
  selectedIds.value = new Set();
}

function batchExport() {
  alert("일괄 내보내기 기능 준비 중");
}
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
  border: 1px solid var(--field-border);
  background: var(--field-bg);
  color: var(--field-text);
  font-weight: 900;
}
.muted {
  color: #6b7280;
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

/* Filters */
.filters {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  align-items: center;
}
.search {
  display: flex;
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
.selects {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.select {
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 10px 12px;
  background: var(--card);
  font-weight: 700;
}

/* Cards */
.card {
  background: var(--card);
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 16px;
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
.head-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

/* Table */
.table {
  width: 100%;
}
.thead,
.trow {
  display: grid;
  grid-template-columns: 44px 1fr 120px 130px 140px 220px;
  gap: 10px;
  align-items: center;
}
.thead {
  padding: 10px 10px;
  border-bottom: 1px solid #eef2f7;
  color: #6b7280;
  font-size: 12px;
  font-weight: 900;
}
.trow {
  padding: 12px 10px;
  border-bottom: 1px solid #f1f5f9;
}
.trow:last-child {
  border-bottom: none;
}
.trow.selected {
  background: #f8fbff;
}
.td.title .doc-title {
  font-weight: 900;
}
.doc-sub {
  margin-top: 4px;
}

.chip {
  font-size: 12px;
  border: 1px solid #e5e7eb;
  padding: 2px 8px;
  border-radius: 999px;
  background: #f9fafb;
  font-weight: 900;
}
.badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid transparent;
  white-space: nowrap;
  font-weight: 900;
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

/* Pager */
.pager {
  margin-top: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}
.pager-actions {
  display: flex;
  gap: 10px;
}

/* Right grid */
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.stat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.stat {
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 12px;
  background: #fff;
}
.stat-label {
  color: #6b7280;
  font-size: 12px;
  font-weight: 900;
}
.stat-value {
  font-weight: 900;
  font-size: 20px;
  margin-top: 6px;
}

.sel-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 8px;
}
.sel-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.sel-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #2563eb;
}
.sel-text {
  font-weight: 800;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.batch-actions {
  display: grid;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}
.full {
  width: 100%;
}

.empty {
  padding: 16px;
  border: 1px dashed #e5e7eb;
  border-radius: 14px;
  color: #6b7280;
  background: #fafafa;
}
.empty.small {
  padding: 12px;
}
.inline {
  border: none;
  background: transparent;
  color: #2563eb;
  font-weight: 900;
  cursor: pointer;
  padding: 0 2px;
}
.hint {
  margin-top: 10px;
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
  font-weight: 800;
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

/* Hamburger button styling */
.hamburger {
  display: none;
  font-size: 20px;
  background: transparent;
  border: none;
  cursor: pointer;
}

/* Responsive */
@media (max-width: 1180px) {
  /* No changes to .app needed here as it's in AppLayout */
}
@media (max-width: 980px) {
  .filters {
    grid-template-columns: 1fr;
  }
  .thead,
  .trow {
    grid-template-columns: 44px 1fr 90px 110px 120px 180px;
  }
  .grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 820px) {
  /* Overlay and Sidebar styles removed (handled by AppLayout/Sidebar) */
  .hamburger {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
}
@media (max-width: 720px) {
  .thead {
    display: none;
  }
  .trow {
    grid-template-columns: 44px 1fr;
    gap: 8px;
  }
  .td.meta,
  .td.actions {
    grid-column: 2 / 3;
  }
  .td.actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }
}

.input,
.select,
.btn,
.pill,
.chip {
  color: var(--field-text);
}

.card,
.stat,
.empty {
  color: var(--ink);
}

.btn-primary {
  color: #fff;
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

:global([data-theme="dark"]) .topbar {
  background: var(--topbar-bg);
  border-bottom-color: var(--line);
}

:global([data-theme="dark"]) .tb-sub,
:global([data-theme="dark"]) .muted,
:global([data-theme="dark"]) .thead,
:global([data-theme="dark"]) .stat-label {
  color: var(--muted);
}

:global([data-theme="dark"]) .input,
:global([data-theme="dark"]) .select,
:global([data-theme="dark"]) .btn,
:global([data-theme="dark"]) .pill,
:global([data-theme="dark"]) .chip {
  background: var(--field-bg);
  border-color: var(--field-border);
  color: var(--field-text);
}

:global([data-theme="dark"]) .input::placeholder {
  color: var(--muted);
}

:global([data-theme="dark"]) .card {
  background: var(--card);
  border-color: var(--line);
}

:global([data-theme="dark"]) .stat,
:global([data-theme="dark"]) .empty {
  background: var(--field-bg);
  border-color: var(--field-border);
  color: var(--ink);
}

:global([data-theme="dark"]) .stat-value,
:global([data-theme="dark"]) .doc-title,
:global([data-theme="dark"]) .card-head h2 {
  color: var(--ink);
}

:global([data-theme="dark"]) .trow {
  border-bottom-color: var(--line);
}

:global([data-theme="dark"]) .trow.selected {
  background: var(--accent-soft);
}

:global([data-theme="dark"]) .btn:hover {
  background: var(--button-hover);
}

:global([data-theme="dark"]) .btn-primary {
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  border-color: transparent;
  color: #fff;
}

:global([data-theme="dark"]) .btn-outline {
  background: transparent;
  border-color: var(--field-border);
  color: var(--ink);
}

:global([data-theme="dark"]) .link,
:global([data-theme="dark"]) .inline {
  color: var(--accent);
}

:global([data-theme="dark"]) .link:hover {
  background: var(--accent-soft);
}
</style>
