<!-- 인수인계용: 관리자 대시보드/관리 화면 -->
<template>
  <AppLayout>
    <main class="doq-admin">
      <header class="doq-admin-head">
        <div><h1>관리자</h1><p>운영 현황과 사용자·문서를 관리해요.</p></div>
        <span><i />상태: 정상</span>
      </header>
      <nav class="doq-admin-tabs">
        <button :class="{ active: tab === 'dashboard' }" @click="tab = 'dashboard'">대시보드</button>
        <button :class="{ active: tab === 'users' }" @click="tab = 'users'">사용자</button>
        <button :class="{ active: tab === 'docs' }" @click="tab = 'docs'">문서 관리</button>
        <button :class="{ active: tab === 'inquiries' }" @click="tab = 'inquiries'">문의</button>
      </nav>

      <template v-if="tab === 'dashboard'">
        <section class="doq-admin-metrics">
          <article><span>회원가입 수</span><strong>{{ stats.users }}</strong></article>
          <article><span>당일 로그인</span><strong>{{ stats.loginsToday }}</strong></article>
          <article><span>실시간 접속자</span><strong class="green">{{ stats.activeUsers }}</strong></article>
          <article><span>오늘 업로드</span><strong>{{ stats.uploadsToday }}</strong></article>
        </section>
        <section class="doq-trend">
          <div><h2>기간별 추이</h2><p><span><i class="violet" />가입</span><span><i class="mint" />변환</span></p></div>
          <svg viewBox="0 0 600 170" preserveAspectRatio="none"><polyline fill="none" stroke="#6a4dff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" points="0,120 86,100 172,110 258,70 344,80 430,44 516,58 600,30"/><polyline fill="none" stroke="#12b39a" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" points="0,140 86,132 172,120 258,124 344,96 430,104 516,72 600,84"/></svg>
          <footer><span>월</span><span>화</span><span>수</span><span>목</span><span>금</span><span>토</span><span>일</span><span>오늘</span></footer>
        </section>
        <section class="doq-chart-grid">
          <article class="doq-donut-card"><h2>시스템 만족도</h2><div><div class="doq-donut" :style="donutStyle(stats.satisfaction)"><span><b>{{ firstPercent(stats.satisfaction) }}%</b><small>만족</small></span></div><ul><li v-for="item in stats.satisfaction" :key="item.label"><i :style="{ background: item.color }" /><span>{{ item.label }}</span><b>{{ slicePercent(item, stats.satisfaction) }}%</b></li></ul></div></article>
          <article class="doq-donut-card"><h2>접속 디바이스</h2><div><div class="doq-donut" :style="donutStyle(stats.devices)"><span><b>{{ firstPercent(stats.devices) }}%</b><small>{{ stats.devices[0]?.label || "-" }}</small></span></div><ul><li v-for="item in stats.devices" :key="item.label"><i :style="{ background: item.color }" /><span>{{ item.label }}</span><b>{{ slicePercent(item, stats.devices) }}%</b></li></ul></div></article>
        </section>
        <section class="doq-chart-grid">
          <article class="doq-usage"><h2>서비스 이용 현황</h2><div v-for="item in stats.serviceUsage" :key="item.label"><p><span>{{ item.label }}</span><b>{{ item.value }}</b></p><div><span :style="{ width: usagePercent(item.value) + '%' }" /></div></div></article>
          <article class="doq-api"><h2>API 연결 확인</h2><div v-for="item in Object.values(stats.apiStatus)" :key="item.label"><span><strong>{{ item.label }}</strong><small>{{ item.message }}</small></span><b :class="apiTone(item.status)">{{ apiStatusLabel(item.status) }}</b></div></article>
        </section>
      </template>

      <section v-else-if="tab === 'users'" class="doq-admin-table">
        <header><h2>사용자 관리</h2><input v-model="userQ" placeholder="이메일·이름 검색" /></header>
        <div class="doq-table-scroll"><div class="doq-user-row doq-table-head"><span>ID</span><span>이메일 · 이름</span><span>권한</span><span>상태</span><span>가입</span></div><div v-for="userItem in filteredUsers" :key="userItem.id" class="doq-user-row"><span>{{ userItem.id.slice(0, 8) }}</span><span><strong>{{ userItem.email }}</strong><small>{{ userItem.name }}</small></span><span><b class="role">{{ userItem.role }}</b></span><span><b :class="['state', userItem.is_active ? 'ok' : 'bad']">{{ userItem.is_active ? "활성" : "정지" }}</b></span><span>{{ fmt(userItem.created_at) }}</span></div></div>
      </section>

      <section v-else-if="tab === 'docs'" class="doq-admin-table">
        <header><h2>문서 · 분석 관리</h2><select v-model="docStatus"><option value="all">상태 전체</option><option value="DONE">완료</option><option value="PROCESSING">처리중</option><option value="FAILED">실패</option></select></header>
        <div class="doq-table-scroll"><div class="doq-doc-admin-row doq-table-head"><span>문서 ID</span><span>제목 · 유형</span><span>사용자</span><span>상태</span><span>업로드</span><span /></div><div v-for="doc in filteredDocs" :key="doc.id" class="doq-doc-admin-row"><span>{{ doc.id.slice(0, 8) }}</span><span><strong>{{ doc.title }}</strong><small>{{ doc.file_type }}</small></span><span>{{ doc.user_id.slice(0, 8) }}</span><span><b :class="['state', docBadge(doc.status)]">{{ docLabel(doc.status) }}</b></span><span>{{ fmt(doc.created_at) }}</span><button type="button" :disabled="doc.status !== 'DONE'" @click="openDoc(doc.id)">열기</button></div></div>
      </section>

      <section v-else class="doq-admin-table">
        <header><h2>문의 관리</h2><span class="waiting">대기 2건</span></header>
        <div class="doq-table-scroll"><div class="doq-inquiry-row doq-table-head"><span>유형</span><span>내용</span><span>보낸이</span><span>상태</span><span /></div><div v-for="item in inquiries" :key="item.content" class="doq-inquiry-row"><span><b class="kind">{{ item.kind }}</b></span><span>{{ item.content }}</span><span>{{ item.sender }}</span><span><b :class="['state', item.done ? 'ok' : 'warn']">{{ item.done ? "완료" : "대기" }}</b></span><button type="button" @click="answerInquiry(item)">{{ item.done ? "보기" : "답변" }}</button></div></div>
      </section>
      <div v-if="toast" class="toast">{{ toast }}</div>
    </main>

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

type Tab = "dashboard" | "users" | "docs" | "inquiries";
const tab = ref<Tab>("dashboard");
const inquiries = [
  { kind: "오류", content: "PDF 변환이 중간에 멈춰요", sender: "최민수", done: false },
  { kind: "제안", content: "용어 저장 폴더 기능이 있으면 좋겠어요", sender: "이하은", done: false },
  { kind: "사용법", content: "쉬운말 저장은 어디서 하나요?", sender: "박서준", done: true },
];

function answerInquiry(item: { content: string; done: boolean }) {
  showToast(item.done ? "완료된 문의입니다." : `답변 작성: ${item.content}`);
}

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
</script>


<style scoped>
.doq-admin { width: min(1120px, 100%); margin: 0 auto; padding: 34px 40px 56px; }.doq-admin-head { margin-bottom: 18px; display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }.doq-admin-head h1 { margin: 0 0 5px; font-size: 24px; letter-spacing: -.01em; }.doq-admin-head p { margin: 0; color: var(--muted); font-size: 14px; }.doq-admin-head > span { padding: 6px 12px; display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 999px; color: var(--accent-strong); background: var(--soft); font-size: 12px; font-weight: 600; }.doq-admin-head > span i { width: 7px; height: 7px; border-radius: 50%; background: #12a58a; }
.doq-admin-tabs { width: fit-content; margin-bottom: 22px; padding: 4px; display: flex; gap: 5px; border-radius: 13px; background: var(--soft); }.doq-admin-tabs button { padding: 8px 15px; border: 0; border-radius: 9px; color: var(--muted); background: transparent; font-size: 13px; font-weight: 600; cursor: pointer; }.doq-admin-tabs button.active { color: var(--ink); background: var(--surface); box-shadow: 0 1px 3px rgb(30 20 70 / .1); }
.doq-admin-metrics { margin-bottom: 16px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }.doq-admin-metrics article { padding: 18px 20px; border: 1px solid var(--line); border-radius: 18px; background: var(--surface); }.doq-admin-metrics span { display: block; margin-bottom: 10px; color: var(--muted); font-size: 13px; }.doq-admin-metrics strong { font-family: "Space Grotesk", sans-serif; font-size: 27px; }.doq-admin-metrics .green { color: #12a58a; }
.doq-trend, .doq-donut-card, .doq-usage, .doq-api, .doq-admin-table { border: 1px solid var(--line); border-radius: 20px; background: var(--surface); }.doq-trend { margin-bottom: 14px; padding: 22px; }.doq-trend > div { display: flex; align-items: center; justify-content: space-between; }.doq-trend h2, .doq-donut-card h2, .doq-usage h2, .doq-api h2, .doq-admin-table h2 { margin: 0; font-size: 15px; }.doq-trend p { margin: 0; display: flex; gap: 16px; }.doq-trend p span { display: flex; align-items: center; gap: 6px; color: var(--muted); font-size: 12px; }.doq-trend i { width: 9px; height: 9px; border-radius: 50%; }.doq-trend .violet { background: #6a4dff; }.doq-trend .mint { background: #12b39a; }.doq-trend svg { width: 100%; height: 170px; display: block; }.doq-trend footer { margin-top: 8px; display: flex; justify-content: space-between; color: var(--muted); font-size: 11px; }
.doq-chart-grid { margin-bottom: 14px; display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }.doq-donut-card, .doq-usage, .doq-api { padding: 22px; }.doq-donut-card h2, .doq-usage h2, .doq-api h2 { margin-bottom: 16px; }.doq-donut-card > div { display: flex; align-items: center; gap: 20px; }.doq-donut { width: 120px; height: 120px; display: grid; place-items: center; flex: none; border-radius: 50%; }.doq-donut > span { width: 74px; height: 74px; display: grid; place-items: center; align-content: center; border-radius: 50%; background: var(--surface); }.doq-donut b { font-family: "Space Grotesk", sans-serif; font-size: 20px; }.doq-donut small { color: var(--muted); font-size: 11px; }.doq-donut-card ul { margin: 0; padding: 0; display: flex; flex: 1; flex-direction: column; gap: 9px; list-style: none; }.doq-donut-card li { display: flex; align-items: center; gap: 8px; font-size: 13px; }.doq-donut-card li i { width: 10px; height: 10px; border-radius: 50%; }.doq-donut-card li span { flex: 1; }
.doq-usage > div { margin-bottom: 14px; }.doq-usage > div:last-child { margin-bottom: 0; }.doq-usage p { margin: 0 0 6px; display: flex; justify-content: space-between; font-size: 13px; }.doq-usage > div > div { height: 8px; overflow: hidden; border-radius: 5px; background: var(--soft); }.doq-usage > div > div span { height: 100%; display: block; background: var(--accent-gradient); }
.doq-api > div { margin-bottom: 10px; padding: 12px 14px; display: flex; align-items: center; justify-content: space-between; border: 1px solid var(--line); border-radius: 12px; }.doq-api > div:last-child { margin-bottom: 0; }.doq-api > div > span { display: grid; }.doq-api strong { font-size: 13.5px; }.doq-api small { margin-top: 2px; color: var(--muted); font-size: 12px; }.doq-api b { padding: 4px 10px; border-radius: 999px; font-size: 11px; }.doq-api b.ok { color: #0c7a68; background: #e7f8f3; }.doq-api b.warn { color: #a9711a; background: #fff6e6; }.doq-api b.bad { color: #c0392b; background: #fdeef0; }
.doq-admin-table { padding: 22px; }.doq-admin-table > header { margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; gap: 12px; }.doq-admin-table h2 { font-size: 16px; }.doq-admin-table input, .doq-admin-table select { width: 260px; height: 38px; padding: 0 12px; border: 1px solid var(--line); border-radius: 11px; outline: 0; color: var(--ink); background: var(--soft); font-size: 13px; }.doq-admin-table select { width: auto; background: var(--surface); font-weight: 600; }.doq-table-scroll { overflow-x: auto; }
.doq-user-row, .doq-doc-admin-row, .doq-inquiry-row { min-width: 720px; padding: 12px 6px; display: grid; align-items: center; gap: 12px; border-top: 1px solid var(--line); font-size: 13px; }.doq-user-row { grid-template-columns: 90px 1.6fr 90px 80px 110px; }.doq-doc-admin-row { grid-template-columns: 90px 1.7fr 90px 80px 100px 60px; }.doq-inquiry-row { grid-template-columns: 90px 1fr 90px 80px 70px; }.doq-table-head { padding-top: 0; border-top: 0; color: var(--muted); font-size: 11.5px; font-weight: 600; }.doq-user-row > span:first-child, .doq-doc-admin-row > span:first-child, .doq-doc-admin-row > span:nth-child(3) { color: var(--muted); font-family: "Space Grotesk", sans-serif; }.doq-user-row > span:nth-child(2), .doq-doc-admin-row > span:nth-child(2) { min-width: 0; display: grid; }.doq-user-row strong, .doq-doc-admin-row strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.doq-user-row small, .doq-doc-admin-row small { margin-top: 2px; color: var(--muted); font-size: 12px; }.role, .kind { padding: 3px 8px; border-radius: 7px; color: var(--accent-strong); background: var(--soft); font-size: 11px; }.state { padding: 3px 8px; border-radius: 999px; font-size: 11px; }.state.ok { color: #0c7a68; background: #e7f8f3; }.state.warn { color: #a9711a; background: #fff6e6; }.state.bad { color: #c0392b; background: #fdeef0; }.doq-doc-admin-row button, .doq-inquiry-row button { height: 30px; border: 1px solid var(--line); border-radius: 8px; color: var(--accent-strong); background: var(--surface); font-size: 12px; font-weight: 600; cursor: pointer; }.doq-doc-admin-row button:disabled { color: var(--muted); cursor: default; }.waiting { padding: 4px 11px; border-radius: 999px; color: var(--accent-strong); background: var(--soft); font-size: 12px; font-weight: 700; }
@media (max-width: 900px) { .doq-admin-metrics { grid-template-columns: repeat(2, 1fr); }.doq-chart-grid { grid-template-columns: 1fr; } }
@media (max-width: 620px) { .doq-admin { padding: 24px 18px 40px; }.doq-admin-tabs { width: 100%; overflow-x: auto; }.doq-admin-tabs button { white-space: nowrap; flex: 1; padding-inline: 10px; }.doq-admin-table > header { align-items: stretch; flex-direction: column; }.doq-admin-table input { width: 100%; } }
</style>
