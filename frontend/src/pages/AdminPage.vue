<!-- 인수인계용: 관리자 대시보드/관리 화면 -->
<template>
  <AppLayout>
    <main class="doq-admin">
      <header class="doq-admin-head">
        <div><h1>관리자</h1><p>운영 현황과 사용자·문서를 관리해요.</p></div>
        <span :class="systemHealth.status"><i />상태: {{ systemHealth.label }}</span>
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
          <svg viewBox="0 0 600 170" preserveAspectRatio="none" aria-label="최근 8일 가입과 변환 추이"><polyline fill="none" stroke="#6a4dff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" :points="trendPoints('signups')"/><polyline fill="none" stroke="#12b39a" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" :points="trendPoints('conversions')"/></svg>
          <footer><span v-for="item in stats.trend" :key="item.date">{{ item.label }}</span></footer>
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
        <div class="doq-table-scroll"><div class="doq-user-row doq-table-head"><span>ID</span><span>이메일 · 이름</span><span>권한</span><span>상태</span><span>가입</span></div><div v-for="userItem in filteredUsers" :key="userItem.id" class="doq-user-row"><span>{{ userItem.id.slice(0, 8) }}</span><span><strong>{{ userItem.email }}</strong><small>{{ userItem.name }}</small></span><span><b class="role">{{ userItem.role }}</b></span><span><b :class="['state', userItem.is_active ? 'ok' : 'bad']">{{ userItem.is_active ? "활성" : "정지" }}</b></span><span>{{ fmt(userItem.created_at) }}</span></div><p v-if="filteredUsers.length === 0" class="doq-admin-empty">검색 결과가 없습니다.</p></div>
      </section>

      <section v-else-if="tab === 'docs'" class="doq-admin-table">
        <header><h2>문서 · 분석 관리</h2><select v-model="docStatus"><option value="all">상태 전체</option><option value="DONE">완료</option><option value="PROCESSING">처리중</option><option value="FAILED">실패</option></select></header>
        <div class="doq-table-scroll"><div class="doq-doc-admin-row doq-table-head"><span>문서 ID</span><span>제목 · 유형</span><span>사용자</span><span>상태</span><span>업로드</span><span /></div><div v-for="doc in filteredDocs" :key="doc.id" class="doq-doc-admin-row"><span>{{ doc.id.slice(0, 8) }}</span><span><strong>{{ doc.title }}</strong><small>{{ doc.file_type }}</small></span><span>{{ doc.user_id.slice(0, 8) }}</span><span><b :class="['state', docBadge(doc.status)]">{{ docLabel(doc.status) }}</b></span><span>{{ fmt(doc.created_at) }}</span><button type="button" :disabled="doc.status !== 'DONE'" @click="openDoc(doc.id)">열기</button></div><p v-if="filteredDocs.length === 0" class="doq-admin-empty">해당 상태의 문서가 없습니다.</p></div>
      </section>

      <section v-else class="doq-admin-table">
        <header><h2>문의 관리</h2><span class="waiting">대기 {{ waitingInquiryCount }}건</span></header>
        <div class="doq-table-scroll"><div class="doq-inquiry-row doq-table-head"><span>유형</span><span>내용</span><span>보낸이</span><span>상태</span><span /></div><div v-for="item in inquiries" :key="item.id" class="doq-inquiry-row"><span><b class="kind">{{ item.type }}</b></span><span>{{ item.content }}</span><span>{{ item.sender_name }}</span><span><b :class="['state', item.status === 'RESOLVED' ? 'ok' : 'warn']">{{ item.status === 'RESOLVED' ? "완료" : "대기" }}</b></span><button type="button" @click="openInquiry(item)">{{ item.status === 'RESOLVED' ? "보기" : "답변" }}</button></div><p v-if="inquiries.length === 0" class="doq-admin-empty">접수된 문의가 없습니다.</p></div>
      </section>
      <div v-if="activeInquiry" class="doq-admin-modal-backdrop" @click.self="activeInquiry = null">
        <section class="doq-admin-modal">
          <header><div><h2>{{ activeInquiry.type }}</h2><span>{{ activeInquiry.sender_name }} · {{ activeInquiry.reply_email || activeInquiry.sender_email }}</span></div><button type="button" aria-label="닫기" @click="activeInquiry = null">×</button></header>
          <p>{{ activeInquiry.content }}</p>
          <label>답변<textarea v-model.trim="inquiryResponse" :disabled="activeInquiry.status === 'RESOLVED'" placeholder="사용자에게 전달할 답변을 입력하세요." /></label>
          <footer><button type="button" @click="activeInquiry = null">닫기</button><button v-if="activeInquiry.status !== 'RESOLVED'" type="button" :disabled="!inquiryResponse || inquirySaving" @click="submitInquiryAnswer">{{ inquirySaving ? "저장 중" : "답변 완료" }}</button></footer>
        </section>
      </div>
      <div v-if="toast" class="toast">{{ toast }}</div>
    </main>

  </AppLayout>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import AppLayout from "../components/layout/AppLayout.vue";
import adminService, { type AdminMetrics, type MetricSlice, type UserItem, type DocItem, type InquiryItem } from "../api/admin.service";

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
    trend: [],
  };
}

const stats = ref<AdminMetrics>(defaultStats());
const systemHealth = computed(() => {
  const statuses = Object.values(stats.value.apiStatus).map((item) => item.status);
  if (statuses.includes("bad")) return { status: "bad", label: "장애" };
  if (statuses.includes("warn")) return { status: "warn", label: "확인 필요" };
  return { status: "ok", label: "정상" };
});
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

function trendPoints(key: "signups" | "conversions") {
  const items = stats.value.trend || [];
  if (!items.length) return "";
  const max = Math.max(1, ...items.map((item) => item[key]));
  return items.map((item, index) => {
    const x = items.length === 1 ? 300 : (index / (items.length - 1)) * 600;
    const y = 150 - (item[key] / max) * 120;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
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
const inquiries = ref<InquiryItem[]>([]);
const activeInquiry = ref<InquiryItem | null>(null);
const inquiryResponse = ref("");
const inquirySaving = ref(false);
const waitingInquiryCount = computed(() => inquiries.value.filter((item) => item.status !== "RESOLVED").length);

async function loadInquiries() {
  try {
    inquiries.value = (await adminService.getInquiries()).data;
  } catch (error) {
    console.error("Failed to load inquiries", error);
    showToast("문의 목록 로딩 실패");
  }
}

function openInquiry(item: InquiryItem) {
  activeInquiry.value = item;
  inquiryResponse.value = item.response || "";
}

async function submitInquiryAnswer() {
  if (!activeInquiry.value || !inquiryResponse.value || inquirySaving.value) return;
  inquirySaving.value = true;
  try {
    const updated = (await adminService.answerInquiry(activeInquiry.value.id, inquiryResponse.value)).data;
    inquiries.value = inquiries.value.map((item) => item.id === updated.id ? updated : item);
    activeInquiry.value = updated;
    showToast("문의 답변을 완료했습니다.");
  } catch (error) {
    console.error("Failed to answer inquiry", error);
    showToast("문의 답변 저장 실패");
  } finally {
    inquirySaving.value = false;
  }
}

watch(tab, async (newTab) => {
  if (newTab === 'users') {
    await loadUsers();
  } else if (newTab === 'docs') {
    await loadDocs();
  } else if (newTab === 'inquiries') {
    await loadInquiries();
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
.doq-admin-head p, .doq-admin-metrics span, .doq-trend p span, .doq-trend footer, .doq-api small, .doq-table-head, .doq-user-row small, .doq-doc-admin-row small { color: var(--sub); }
.doq-admin-head > span { white-space: nowrap; }.doq-admin-head > span.warn i { background: #d4932d; }.doq-admin-head > span.bad i { background: #d0524a; }
.doq-admin-empty { margin: 12px 0 0; padding: 22px; border: 1px dashed var(--line); border-radius: 12px; color: var(--sub); background: var(--soft); text-align: center; font-size: 13px; }
.doq-admin-modal-backdrop { position: fixed; inset: 0; z-index: 1400; padding: 20px; display: grid; place-items: center; background: rgb(15 10 40 / .52); }
.doq-admin-modal { width: min(520px, 100%); padding: 24px; border: 1px solid var(--line); border-radius: 18px; color: var(--ink); background: var(--surface); box-shadow: 0 26px 70px rgb(0 0 0 / .32); }
.doq-admin-modal > header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }.doq-admin-modal h2 { margin: 0; font-size: 17px; }.doq-admin-modal header span { display: block; margin-top: 4px; color: var(--sub); font-size: 12px; }.doq-admin-modal header > button { width: 30px; height: 30px; border: 0; border-radius: 8px; color: var(--sub); background: var(--soft); cursor: pointer; }
.doq-admin-modal > p { margin: 18px 0; padding: 14px; border-radius: 12px; color: var(--sub); background: var(--soft); font-size: 14px; line-height: 1.65; }.doq-admin-modal label { display: grid; gap: 7px; color: var(--sub); font-size: 13px; font-weight: 600; }.doq-admin-modal textarea { min-height: 130px; padding: 12px; border: 1px solid var(--line); border-radius: 12px; color: var(--ink); background: var(--surface); font: inherit; resize: vertical; }.doq-admin-modal footer { margin-top: 18px; display: flex; justify-content: flex-end; gap: 8px; }.doq-admin-modal footer button { height: 40px; padding: 0 15px; border: 1px solid var(--line); border-radius: 10px; color: var(--sub); background: var(--surface); font-weight: 600; cursor: pointer; }.doq-admin-modal footer button:last-child { border: 0; color: #fff; background: var(--accent-gradient); }.doq-admin-modal footer button:disabled { opacity: .5; cursor: default; }
@media (max-width: 900px) { .doq-admin-metrics { grid-template-columns: repeat(2, 1fr); }.doq-chart-grid { grid-template-columns: 1fr; } }
@media (max-width: 620px) { .doq-admin { padding: 24px 18px 40px; }.doq-admin-tabs { width: 100%; overflow-x: auto; }.doq-admin-tabs button { white-space: nowrap; flex: 1; padding-inline: 10px; }.doq-admin-table > header { align-items: stretch; flex-direction: column; }.doq-admin-table input { width: 100%; } }
</style>
