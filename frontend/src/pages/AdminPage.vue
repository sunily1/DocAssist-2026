<!-- 인수인계용: 관리자 대시보드/관리 화면 -->
<template>
  <AppLayout v-slot="{ toggleSidebar }">
    <!-- 상단바 -->
    <header class="topbar">
      <div class="tb-left">
        <div class="tb-title">
          <button class="hamburger" @click="toggleSidebar" aria-label="Open menu">☰</button>
          <span class="tb-title-strong">관리자</span>
          <span class="tb-sub">· 운영 현황 & 관리</span>
        </div>

        <div class="tb-meta">
          <span class="pill">상태: 정상</span>
          <span class="muted">·</span>
          <span class="muted">데이터</span>
        </div>
      </div>

      <div class="tb-right">
        <button class="btn btn-outline" type="button" @click="refreshMetrics">새로고침</button>
      </div>
    </header>

    <!-- 메인 콘텐츠(탭 + 섹션) -->
    <div class="page-content admin-page">
      <!-- 탭 -->
      <section class="tabs-bar">
        <div class="tabs">
          <button class="tab" :class="{ on: tab === 'dashboard' }" @click="tab = 'dashboard'">대시보드</button>
          <button class="tab" :class="{ on: tab === 'users' }" @click="tab = 'users'">사용자</button>
          <button class="tab" :class="{ on: tab === 'docs' }" @click="tab = 'docs'">문서 관리</button>
        </div>
      </section>

      <!-- 본문 -->
      <main class="content">
        <!-- 대시보드 -->
        <section v-if="tab === 'dashboard'" class="grid dash-grid admin-dashboard">
          <article class="card span2">
            <div class="card-head">
              <h2>운영 핵심 지표</h2>
              <span class="muted">오늘 기준 주요 현황</span>
            </div>
            <div class="metric-grid">
              <div class="metric-card">
                <div class="stat-label">회원가입 수</div>
                <div class="stat-value">{{ stats.users }}</div>
              </div>
              <div class="metric-card">
                <div class="stat-label">당일 로그인 수</div>
                <div class="stat-value">{{ stats.loginsToday }}</div>
              </div>
              <div class="metric-card">
                <div class="stat-label">실시간 접속자 수</div>
                <div class="stat-value">{{ stats.activeUsers }}</div>
              </div>
              <div class="metric-card">
                <div class="stat-label">오늘 업로드</div>
                <div class="stat-value">{{ stats.uploadsToday }}</div>
              </div>
            </div>
          </article>

          <article class="card chart-card">
            <div class="card-head">
              <h2>시스템 만족도</h2>
            </div>
            <div class="chart-layout">
              <div class="donut" :style="donutStyle(stats.satisfaction)">
                <div class="donut-hole">
                  <strong>{{ firstPercent(stats.satisfaction) }}%</strong>
                  <span>만족</span>
                </div>
              </div>
              <div class="legend">
                <div v-for="item in stats.satisfaction" :key="item.label" class="legend-row">
                  <span class="legend-dot" :style="{ background: item.color }"></span>
                  <span>{{ item.label }}</span>
                  <b>{{ slicePercent(item, stats.satisfaction) }}%</b>
                </div>
              </div>
            </div>
          </article>

          <article class="card chart-card">
            <div class="card-head">
              <h2>접속 디바이스</h2>
            </div>
            <div class="chart-layout">
              <div class="donut" :style="donutStyle(stats.devices)">
                <div class="donut-hole">
                  <strong>{{ firstPercent(stats.devices) }}%</strong>
                  <span>{{ stats.devices[0]?.label || "-" }}</span>
                </div>
              </div>
              <div class="legend">
                <div v-for="item in stats.devices" :key="item.label" class="legend-row">
                  <span class="legend-dot" :style="{ background: item.color }"></span>
                  <span>{{ item.label }}</span>
                  <b>{{ slicePercent(item, stats.devices) }}%</b>
                </div>
              </div>
            </div>
          </article>

          <article class="card">
            <div class="card-head">
              <h2>서비스 이용 현황</h2>
              <span class="muted">텍스트 변환 · 파일 변환 · 챗봇 · 용어집</span>
            </div>
            <div class="usage-list">
              <div v-for="item in stats.serviceUsage" :key="item.label" class="usage-row">
                <div class="usage-head">
                  <span>{{ item.label }}</span>
                  <b>{{ item.value }}</b>
                </div>
                <div class="usage-bar">
                  <div class="usage-fill" :style="{ width: usagePercent(item.value) + '%' }"></div>
                </div>
              </div>
            </div>
          </article>

          <article class="card">
            <div class="card-head">
              <h2>API 연결 확인</h2>
            </div>
            <div class="api-grid">
              <div
                v-for="item in Object.values(stats.apiStatus)"
                :key="item.label"
                :class="['api-row', apiTone(item.status)]"
              >
                <div>
                  <div class="api-name">{{ item.label }}</div>
                  <div class="muted">{{ item.message }}</div>
                </div>
                <span class="api-status">{{ apiStatusLabel(item.status) }}</span>
              </div>
            </div>
          </article>
        </section>

        <!-- 사용자 -->
        <section v-else-if="tab === 'users'" class="grid">
          <article class="card span2">
            <div class="card-head">
              <h2>사용자 관리</h2>
              <div class="head-actions">
                <input class="input" v-model="userQ" placeholder="이메일/이름 검색..." />
              </div>
            </div>
            <div class="table">
              <div class="thead users">
                <div class="th">ID</div>
                <div class="th">이메일</div>
                <div class="th">권한</div>
                <div class="th">상태</div>
                <div class="th">가입</div>
              </div>
              <div v-for="u in filteredUsers" :key="u.id" class="trow users">
                <div class="td mono">{{ u.id.slice(0, 8) }}</div>
                <div class="td">
                  <div class="strong">{{ u.email }}</div>
                  <div class="muted small">{{ u.name }}</div>
                </div>
                <div class="td">
                  <span class="chip" :class="{ admin: u.role === 'ADMIN' }">{{ u.role }}</span>
                </div>
                <div class="td">
                  <span :class="['badge', u.is_active ? 'ok' : 'bad']">{{ u.is_active ? "활성" : "정지" }}</span>
                </div>
                <div class="td muted">{{ fmt(u.created_at) }}</div>
              </div>
            </div>
          </article>
        </section>

        <!-- 문서 -->
        <section v-else-if="tab === 'docs'" class="grid">
          <article class="card span2">
            <div class="card-head">
              <h2>문서/분석 관리</h2>
              <div class="head-actions">
                <select class="select" v-model="docStatus">
                  <option value="all">상태 전체</option>
                  <option value="DONE">완료</option>
                  <option value="PROCESSING">처리중</option>
                  <option value="FAILED">실패</option>
                </select>
              </div>
            </div>
            <div class="table">
              <div class="thead docs">
                <div class="th">문서 ID</div>
                <div class="th">제목</div>
                <div class="th">사용자</div>
                <div class="th">상태</div>
                <div class="th">업로드</div>
                <div class="th">작업</div>
              </div>
              <div v-for="d in filteredDocs" :key="d.id" class="trow docs">
                <div class="td mono">{{ d.id.slice(0, 8) }}</div>
                <div class="td">
                  <div class="strong">{{ d.title }}</div>
                  <div class="muted small">{{ d.file_type }}</div>
                </div>
                <div class="td">{{ d.user_id.slice(0, 8) }}</div>
                <div class="td">
                  <span :class="['badge', docBadge(d.status)]">{{ docLabel(d.status) }}</span>
                </div>
                <div class="td muted">{{ fmt(d.created_at) }}</div>
                <div class="td">
                  <button class="btn btn-sm" @click="openDoc(d.id)" :disabled="d.status !== 'DONE'">열기</button>
                </div>
              </div>
            </div>
          </article>
        </section>


        <div v-if="toast" class="toast">{{ toast }}</div>
      </main>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import AppLayout from "../components/layout/AppLayout.vue";
import adminService, { type AdminMetrics, type MetricSlice, type UserItem, type DocItem } from "../api/admin.service";

const router = useRouter();
const theme = ref<"light" | "dark">("light");

function applyTheme(next: "light" | "dark") {
  theme.value = next;
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
}

onMounted(async () => {
  const savedTheme = (localStorage.getItem("theme") as "light" | "dark") || "light";
  applyTheme(savedTheme);
  await loadMetrics();
});

async function loadMetrics() {
  try {
    const res = await adminService.getMetrics();
    stats.value = mergeStats(res.data);
  } catch (e) {
    console.error("Failed to load metrics", e);
    showToast("지표 로딩 실패");
  }
}

/* ---- Dashboard data ---- */
function defaultStats(): AdminMetrics {
  return {
    users: 0,
    docs: 0,
    queue: 0,
    qaToday: 0,
    signups: 0,
    loginsToday: 0,
    activeUsers: 0,
    uploadsToday: 0,
    glossaryTerms: 0,
    glossaryTermsToday: 0,
    glossaryPinned: 0,
    serviceUsage: [
      { label: "텍스트 변환", value: 0 },
      { label: "파일 변환", value: 0 },
      { label: "챗봇", value: 0 },
      { label: "용어집", value: 0 },
    ],
    satisfaction: [
      { label: "만족", value: 0, color: "#5b8cff" },
      { label: "보통", value: 0, color: "#21c7b7" },
      { label: "불만", value: 0, color: "#fb7185" },
    ],
    devices: [
      { label: "데스크톱", value: 0, color: "#5b8cff" },
      { label: "모바일", value: 0, color: "#21c7b7" },
      { label: "태블릿", value: 0, color: "#fbbf24" },
    ],
    apiStatus: {
      backend: { status: "ok", label: "백엔드", message: "정상" },
      db: { status: "ok", label: "DB", message: "정상" },
      openai: { status: "warn", label: "OpenAI", message: "키 확인 필요" },
      dictionary: { status: "warn", label: "국어사전", message: "연동 예정" },
    },
  };
}

const stats = ref<AdminMetrics>(defaultStats());
const usageMax = computed(() => Math.max(1, ...stats.value.serviceUsage.map((item) => item.value)));

function mergeStats(next: AdminMetrics): AdminMetrics {
  const base = defaultStats();
  return {
    ...base,
    ...next,
    serviceUsage: next.serviceUsage?.length ? next.serviceUsage : base.serviceUsage,
    satisfaction: next.satisfaction?.length ? next.satisfaction : base.satisfaction,
    devices: next.devices?.length ? next.devices : base.devices,
    apiStatus: { ...base.apiStatus, ...(next.apiStatus || {}) },
  };
}

function chartTotal(items: MetricSlice[]) {
  return items.reduce((sum, item) => sum + Number(item.value || 0), 0);
}

function firstPercent(items: MetricSlice[]) {
  const total = chartTotal(items);
  if (!total) return 0;
  return Math.round((Number(items[0]?.value || 0) / total) * 100);
}

function slicePercent(item: MetricSlice, items: MetricSlice[]) {
  const total = chartTotal(items);
  if (!total) return 0;
  return Math.round((Number(item.value || 0) / total) * 100);
}

function donutStyle(items: MetricSlice[]) {
  const total = chartTotal(items);
  if (!total) return { background: "conic-gradient(var(--line) 0deg 360deg)" };
  let cursor = 0;
  const fallback = ["#5b8cff", "#21c7b7", "#fbbf24", "#fb7185"];
  const segments = items.map((item, index) => {
    const start = cursor;
    cursor += (Number(item.value || 0) / total) * 360;
    return (item.color || fallback[index % fallback.length]) + " " + start + "deg " + cursor + "deg";
  });
  return { background: "conic-gradient(" + segments.join(", ") + ")" };
}

function usagePercent(value: number) {
  return Math.max(4, Math.round((Number(value || 0) / usageMax.value) * 100));
}

function apiTone(status: string) {
  if (status === "ok") return "ok";
  if (status === "bad") return "bad";
  return "warn";
}

function apiStatusLabel(status: string) {
  if (status === "ok") return "OK";
  if (status === "bad") return "FAIL";
  return "CHECK";
}

type Tab = "dashboard" | "users" | "docs";
const tab = ref<Tab>("dashboard");

watch(tab, async (newTab) => {
  if (newTab === 'users') {
    await loadUsers();
  } else if (newTab === 'docs') {
    await loadDocs();
  }
});

/* ---- Users ---- */
const users = ref<UserItem[]>([]);
const userQ = ref("");

async function loadUsers() {
  try {
    const res = await adminService.getUsers();
    users.value = res.data;
  } catch (e) {
    showToast("사용자 목록 로딩 실패");
  }
}

const filteredUsers = computed(() => {
  const q = userQ.value.trim().toLowerCase();
  if (!q) return users.value;
  return users.value.filter((u) => u.email.toLowerCase().includes(q) || u.name.toLowerCase().includes(q));
});

/* ---- Docs ---- */
const docs = ref<DocItem[]>([]);
const docStatus = ref<"all" | string>("all");

async function loadDocs() {
  try {
    const res = await adminService.getDocuments();
    docs.value = res.data;
  } catch (e) {
    showToast("문서 목록 로딩 실패");
  }
}

const filteredDocs = computed(() => {
  if (docStatus.value === "all") return docs.value;
  return docs.value.filter((d) => d.status === docStatus.value);
});

const toast = ref("");
let timer: number | undefined;
function showToast(msg: string) {
  toast.value = msg;
  if (timer) window.clearTimeout(timer);
  timer = window.setTimeout(() => (toast.value = ""), 1400);
}

function openDoc(id: string) {
  router.push({ name: "documentView", params: { id } }).catch(() => {});
}
function fmt(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString("ko-KR", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function docBadge(status: string) {
  if (status === "DONE") return "ok";
  if (status === "PROCESSING" || status === "QUEUED") return "warn";
  return "bad";
}

function docLabel(status: string) {
  if (status === "DONE") return "완료";
  if (status === "PROCESSING") return "처리중";
  if (status === "QUEUED") return "대기";
  return "실패";
}
async function refreshMetrics() {
  await loadMetrics();
  showToast("새로고침 완료");
}

</script>

<style scoped>
/* Main */
.main {
  display: grid;
  grid-template-rows: auto 56px 1fr;
  min-width: 0;
}

/* Topbar */
.topbar {
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 18px;
  gap: 12px;
  /* Topbar height in grid is auto or fixed, but let's stick to flex layout for content */
  height: 76px;
}
.tb-left { display: grid; gap: 6px; }
.tb-title { display: flex; align-items: baseline; gap: 8px; }
.tb-title-strong { font-weight: 1000; font-size: 16px; }
.tb-sub { color: #6b7280; font-size: 12px; font-weight: 700; }
.tb-meta { display: flex; align-items: center; gap: 8px; }
.pill {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  font-weight: 900;
}
.muted { color: #6b7280; font-size: 12px; font-weight: 700; }
.small { font-size: 12px; }
.tb-right { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }

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

.page-content {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%; /* Fill available space in AppLayout main grid */
  overflow: auto; /* Let this container scroll if needed, though usually main scrolls */
}

/* Tabs */
.tabs-bar {
  position: sticky;
  top: 0;
  z-index: 9;
  background: #f4f6fb;
  border-bottom: 1px solid #e5e7eb;
}
.tabs {
  max-width: 1280px;
  margin: 0 auto;
  padding: 10px 18px;
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: nowrap;
  overflow-x: auto;
  scrollbar-width: none;
  height: 56px;
}
.tabs::-webkit-scrollbar { display: none; }
.tab {
  border: 1px solid #e5e7eb;
  background: #fff;
  padding: 10px 12px;
  border-radius: 999px;
  font-weight: 1000;
  cursor: pointer;
  font-size: 13px;
  flex: 0 0 auto;
}
.tab.on {
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
}

/* Grid / Cards */
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  align-items: start;
}
.dash-grid {
  align-items: stretch;
}
.dash-grid .card {
  height: 100%;
}
.card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 16px;
  min-width: 0;
}
.span2 { grid-column: 1 / -1; }
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}
.card-head h2 { margin: 0; font-size: 16px; font-weight: 1000; }
.head-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }

.stat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.stats-compact {
  grid-template-columns: repeat(4, minmax(140px, 1fr));
  margin-bottom: 12px;
}

.stat {
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 12px;
  background: #fff;
}
.stat-label { color: #6b7280; font-size: 12px; font-weight: 900; }
.stat-value { font-weight: 1000; font-size: 22px; margin-top: 6px; }
.hint { margin-top: 10px; }

.health { display: grid; gap: 10px; }
.health-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 12px;
  border: 1px solid #eef2f7;
  border-radius: 14px;
}
.k { font-weight: 900; }
.v { font-weight: 1000; }
.v.ok { color: #065f46; }
.v.warn { color: #92400e; }
.v.bad { color: #991b1b; }

.actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }


.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 14px;
  background: var(--field-bg);
}

.chart-layout {
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 18px;
  align-items: center;
}

.donut {
  width: 150px;
  aspect-ratio: 1;
  border-radius: 50%;
  display: grid;
  place-items: center;
  box-shadow: inset 0 0 0 1px var(--line);
}

.donut-hole {
  width: 92px;
  aspect-ratio: 1;
  border-radius: 50%;
  display: grid;
  place-items: center;
  align-content: center;
  background: var(--card);
  border: 1px solid var(--line);
}

.donut-hole strong {
  font-size: 22px;
  line-height: 1;
}

.donut-hole span {
  margin-top: 6px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
}

.legend,
.usage-list,
.api-grid {
  display: grid;
  gap: 10px;
}

.legend-row,
.usage-head,
.api-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.legend-row {
  color: var(--ink);
  font-size: 13px;
  font-weight: 900;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex: 0 0 auto;
}

.legend-row span:nth-child(2) {
  flex: 1;
}

.usage-row {
  display: grid;
  gap: 8px;
}

.usage-head {
  color: var(--ink);
  font-size: 13px;
  font-weight: 900;
}

.usage-bar {
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: var(--field-bg);
  border: 1px solid var(--line);
}

.usage-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
}

.api-row {
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 12px;
  background: var(--field-bg);
}

.api-name {
  font-weight: 1000;
}

.api-status {
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 1000;
}

.api-row.ok .api-status { background: #ecfdf5; color: #065f46; }
.api-row.warn .api-status { background: #fffbeb; color: #92400e; }
.api-row.bad .api-status { background: #fef2f2; color: #991b1b; }

:global([data-theme="dark"]) .topbar,
:global([data-theme="dark"]) .tabs-bar {
  background: var(--topbar-bg);
  border-color: var(--line);
}

:global([data-theme="dark"]) .card,
:global([data-theme="dark"]) .metric-card,
:global([data-theme="dark"]) .stat,
:global([data-theme="dark"]) .health-row,
:global([data-theme="dark"]) .api-row,
:global([data-theme="dark"]) .log,
:global([data-theme="dark"]) .set-row {
  background: var(--card);
  border-color: var(--line);
  color: var(--ink);
}

:global([data-theme="dark"]) .input,
:global([data-theme="dark"]) .select,
:global([data-theme="dark"]) .btn,
:global([data-theme="dark"]) .pill,
:global([data-theme="dark"]) .tab,
:global([data-theme="dark"]) .chip {
  background: var(--field-bg);
  border-color: var(--field-border);
  color: var(--field-text);
}

:global([data-theme="dark"]) .tab.on,
:global([data-theme="dark"]) .btn-primary {
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  border-color: transparent;
  color: #fff;
}

:global([data-theme="dark"]) .btn-outline {
  background: transparent;
  color: var(--ink);
}

:global([data-theme="dark"]) .muted,
:global([data-theme="dark"]) .stat-label,
:global([data-theme="dark"]) .thead,
:global([data-theme="dark"]) .tb-sub {
  color: var(--muted);
}

:global([data-theme="dark"]) .stat-value,
:global([data-theme="dark"]) .strong,
:global([data-theme="dark"]) .card-head h2,
:global([data-theme="dark"]) .api-name,
:global([data-theme="dark"]) .usage-head,
:global([data-theme="dark"]) .legend-row {
  color: var(--ink);
}

:global([data-theme="dark"]) .trow {
  border-bottom-color: var(--line);
}

@media (max-width: 1180px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .metric-grid,
  .chart-layout {
    grid-template-columns: 1fr;
  }
}

/* Tables */
.table { width: 100%; overflow-x: auto; }
.thead, .trow {
  display: grid;
  grid-template-columns: 140px 1fr 180px 120px 140px 220px;
  gap: 10px;
  align-items: center;
  min-width: 800px; /* Ensure table doesn't squish too much */
}
.thead {
  padding: 10px 10px;
  border-bottom: 1px solid #eef2f7;
  color: #6b7280;
  font-size: 12px;
  font-weight: 1000;
}
.trow {
  padding: 12px 10px;
  border-bottom: 1px solid #f1f5f9;
}
.trow:last-child { border-bottom: none; }

.thead.users, .trow.users {
  grid-template-columns: 120px 1fr 120px 120px 140px;
}
.thead.docs, .trow.docs {
  grid-template-columns: 140px 1fr 180px 120px 140px 220px;
}

.strong { font-weight: 1000; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }

.badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid transparent;
  white-space: nowrap;
  font-weight: 1000;
}
.badge.ok { background: #ecfdf5; border-color: #a7f3d0; color: #065f46; }
.badge.warn { background: #fffbeb; border-color: #fde68a; color: #92400e; }
.badge.bad { background: #fef2f2; border-color: #fecaca; color: #991b1b; }
.badge.info { background: #eff6ff; border-color: #bfdbfe; color: #1d4ed8; }

.chip {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  font-weight: 1000;
}
.chip.admin {
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
}


/* Inputs */
.input {
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 10px 12px;
  outline: none;
  background: #fff;
  font-weight: 900;
}
.select {
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 10px 12px;
  background: #fff;
  font-weight: 900;
}

/* Buttons */
.btn {
  border: 1px solid #e5e7eb;
  background: #fff;
  padding: 10px 12px;
  border-radius: 12px;
  font-weight: 1000;
  cursor: pointer;
}
.btn:hover { background: #f9fafb; }
.btn-primary { background: #2563eb; border-color: #2563eb; color: #fff; }
.btn-primary:hover { background: #1d4ed8; }
.btn-outline { border-color: #cbd5e1; }
.btn-sm { padding: 8px 10px; border-radius: 10px; }

.toast {
  position: fixed;
  left: 50%;
  bottom: 18px;
  transform: translateX(-50%);
  padding: 10px 12px;
  border-radius: 14px;
  font-weight: 1000;
  border: 1px solid #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
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

@media (max-width: 980px) {
  .grid { grid-template-columns: 1fr; }
  .stats-compact { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 820px) {
  .hamburger {
    display: inline-flex;
  }
}

:global([data-theme="dark"] .admin-page),
:global([data-theme="dark"] .admin-page .content),
:global([data-theme="dark"] .admin-page .tabs-bar) {
  background: var(--bg);
  color: var(--ink);
}

:global([data-theme="dark"] .admin-page .topbar),
:global([data-theme="dark"] .admin-page .card),
:global([data-theme="dark"] .admin-page .metric-card),
:global([data-theme="dark"] .admin-page .stat),
:global([data-theme="dark"] .admin-page .api-row),
:global([data-theme="dark"] .admin-page .donut-hole) {
  background: var(--card);
  border-color: var(--line);
  color: var(--ink);
}

:global([data-theme="dark"] .admin-page .tb-title-strong),
:global([data-theme="dark"] .admin-page .card-head h2),
:global([data-theme="dark"] .admin-page .stat-value),
:global([data-theme="dark"] .admin-page .strong),
:global([data-theme="dark"] .admin-page .td),
:global([data-theme="dark"] .admin-page .api-name),
:global([data-theme="dark"] .admin-page .usage-head),
:global([data-theme="dark"] .admin-page .legend-row) {
  color: var(--ink);
}

:global([data-theme="dark"] .admin-page .muted),
:global([data-theme="dark"] .admin-page .tb-sub),
:global([data-theme="dark"] .admin-page .stat-label),
:global([data-theme="dark"] .admin-page .thead),
:global([data-theme="dark"] .admin-page .donut-hole span) {
  color: var(--muted);
}

:global([data-theme="dark"] .admin-page .tab),
:global([data-theme="dark"] .admin-page .input),
:global([data-theme="dark"] .admin-page .select),
:global([data-theme="dark"] .admin-page .btn),
:global([data-theme="dark"] .admin-page .pill),
:global([data-theme="dark"] .admin-page .chip) {
  background: var(--field-bg);
  border-color: var(--field-border);
  color: var(--field-text);
}

:global([data-theme="dark"] .admin-page .tab.on),
:global([data-theme="dark"] .admin-page .btn-primary) {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--accent-contrast);
}

:global([data-theme="dark"] .admin-page .btn:hover) {
  background: var(--button-hover);
}

:global([data-theme="dark"] .admin-page .trow) {
  border-bottom-color: var(--line);
  color: var(--ink);
}

:global([data-theme="dark"] .admin-page .badge.ok) {
  background: rgb(52 211 153 / 0.14);
  border-color: rgb(52 211 153 / 0.34);
  color: #86efac;
}

:global([data-theme="dark"] .admin-page .badge.warn) {
  background: rgb(251 191 36 / 0.14);
  border-color: rgb(251 191 36 / 0.34);
  color: #fde68a;
}

:global([data-theme="dark"] .admin-page .badge.bad) {
  background: rgb(251 113 133 / 0.14);
  border-color: rgb(251 113 133 / 0.34);
  color: #fda4af;
}

:global([data-theme="dark"] .admin-page .chip.admin) {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: #a9c4ff;
}
</style>



