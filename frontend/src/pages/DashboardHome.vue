<!-- 인수인계용: 홈 대시보드(요약/최근 문서/활동) 화면 -->
<template>
  <AppLayout v-slot="{ toggleSidebar }">
    <header class="topbar">
      <div class="tb-left">
        <button class="hamburger" @click="toggleSidebar" aria-label="Open menu">☰</button>
        <div class="tb-title-strong">DoQ · 문서 이해 보조 시스템</div>
      </div>

      <div class="tb-center">
        <input class="tb-search" placeholder="문서 검색" v-model="sidebarQ" />
      </div>

      <div class="tb-right">
        <button class="btn btn-ghost" @click="goDrive">내 드라이브</button>
      </div>
    </header>

    <main class="container">
      <section class="hero">
        <div class="hero-left">
          <h1>전문 문서를 <span class="accent">원문 그대로</span> 두고,<br />이해를 돕는 설명 레이어를 제공합니다.</h1>
          <p>PDF, DOCX, TXT 문서를 업로드하거나 텍스트를 직접 입력하면 쉬운말 변환과 문단별 요약을 생성합니다.</p>
          <div class="hero-actions">
            <button class="btn btn-primary btn-lg" @click="goUpload">텍스트·파일 변환 시작</button>
          </div>
        </div>

        <div class="hero-right">
          <div class="hero-card">
            <div class="hero-card-title">오늘의 요약</div>
            <div class="stat-grid">
              <div class="stat"><div class="stat-label">총 문서</div><div class="stat-value">{{ stats.totalDocs }}</div></div>
              <div class="stat"><div class="stat-label">분석 완료</div><div class="stat-value">{{ stats.done }}</div></div>
              <div class="stat"><div class="stat-label">분석 중</div><div class="stat-value">{{ stats.processing }}</div></div>
              <div class="stat"><div class="stat-label">이번 주 Q&A</div><div class="stat-value">{{ stats.weekQa }}</div></div>
            </div>
          </div>
        </div>
      </section>

      <section class="grid">
        <article class="card card-large">
          <div class="card-head">
            <h2>최근 업로드 문서</h2>
            <button class="link" @click="goDrive">전체 보기 →</button>
          </div>

          <div v-if="recentDocs.length === 0" class="empty">
            아직 업로드된 문서가 없습니다.
            <button class="inline" @click="goUpload">업로드</button>해보세요.
          </div>

          <ul v-else class="list">
            <li v-for="doc in recentDocs" :key="doc.id" class="list-item">
              <div>
                <div class="doc-title">{{ doc.title }}</div>
                <div class="doc-meta"><span class="chip">{{ doc.type }}</span><span class="muted">{{ formatDate(doc.createdAt) }}</span></div>
              </div>
              <div class="doc-right">
                <span :class="['badge', badgeClass(doc.status)]">{{ statusLabel(doc.status) }}</span>
                <button class="btn btn-sm" :disabled="doc.status !== 'done'" @click="openDocument(doc.id)">열기</button>
              </div>
            </li>
          </ul>
        </article>
      </section>

      <section class="feedback-band">
        <div><h2>서비스 만족도</h2><p class="muted">현재 이용 경험을 선택해 주세요.</p></div>
        <div class="feedback-options" role="group" aria-label="서비스 만족도">
          <button
            v-for="option in feedbackOptions"
            :key="option.value"
            type="button"
            class="feedback-btn"
            :class="{ on: selectedFeedback === option.value }"
            :disabled="feedbackSaving"
            @click="submitFeedback(option.value)"
          ><span aria-hidden="true">{{ option.icon }}</span><span>{{ option.label }}</span></button>
        </div>
        <span v-if="feedbackSaved" class="feedback-saved">반영됨</span>
      </section>

      <section class="card">
        <div class="card-head"><h2>최근 활동</h2></div>
        <ul v-if="activities.length" class="activity">
          <li v-for="activity in activities" :key="activity.id" class="activity-item">
            <span class="dot" />
            <div><div class="activity-title">{{ activity.title }}</div><div class="muted">{{ formatDateTime(activity.at) }}</div></div>
          </li>
        </ul>
        <div v-else class="empty">최근 활동이 없습니다.</div>
      </section>
    </main>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import documentService from "../api/document.service";
import userService, { type SatisfactionRating } from "../api/user.service";
import AppLayout from "../components/layout/AppLayout.vue";

const router = useRouter();
const authStore = useAuthStore();
const sidebarQ = ref("");
const selectedFeedback = ref<SatisfactionRating | "">("");
const feedbackSaving = ref(false);
const feedbackSaved = ref(false);
const feedbackOptions: Array<{ value: SatisfactionRating; label: string; icon: string }> = [
  { value: "satisfied", label: "만족", icon: "✓" },
  { value: "neutral", label: "보통", icon: "−" },
  { value: "dissatisfied", label: "불만", icon: "!" },
];

type DocStatus = "queued" | "processing" | "done" | "failed";
interface DocItem { id: string; title: string; type: "PDF" | "DOCX" | "TXT" | "UNKNOWN"; status: DocStatus; createdAt: string; }
interface ActivityItem { id: string; title: string; at: string; }

const recentDocs = ref<DocItem[]>([]);
const activities = ref<ActivityItem[]>([]);
const stats = ref({ totalDocs: 0, done: 0, processing: 0, weekQa: 0 });

onMounted(async () => {
  if (authStore.token && !authStore.user) await authStore.fetchUser();
  await fetchDashboardData();
  await loadFeedback();
});

async function loadFeedback() {
  try {
    const response = await userService.getFeedback();
    selectedFeedback.value = response.data?.rating || "";
  } catch (error) { console.error("Feedback load failed", error); }
}

async function submitFeedback(rating: SatisfactionRating) {
  feedbackSaving.value = true;
  feedbackSaved.value = false;
  try {
    await userService.updateFeedback(rating);
    selectedFeedback.value = rating;
    feedbackSaved.value = true;
    window.setTimeout(() => (feedbackSaved.value = false), 1600);
  } catch (error) { console.error("Feedback update failed", error); }
  finally { feedbackSaving.value = false; }
}

async function fetchDashboardData() {
  try {
    const recentResponse = await documentService.getDocuments(0, 5);
    recentDocs.value = recentResponse.data.map((doc: any) => ({
      id: doc.id, title: doc.title, type: doc.file_type || "UNKNOWN", status: normalizeStatus(doc.status), createdAt: doc.created_at,
    }));
    const allResponse = await documentService.getDocuments(0, 100);
    const docs = allResponse.data;
    stats.value.totalDocs = docs.length;
    stats.value.done = docs.filter((doc: any) => doc.status === "DONE").length;
    stats.value.processing = docs.filter((doc: any) => doc.status === "PROCESSING" || doc.status === "QUEUED").length;
  } catch (error) { console.error("Dashboard data fetch failed", error); }
}

function normalizeStatus(status: string): DocStatus {
  const value = String(status || "").toLowerCase();
  if (value === "queued" || value === "processing" || value === "done" || value === "failed") return value;
  return "processing";
}
function badgeClass(status: DocStatus) { return status === "done" ? "badge-ok" : status === "failed" ? "badge-bad" : "badge-warn"; }
function statusLabel(status: DocStatus) { return { done: "분석 완료", queued: "대기 중", processing: "분석 중", failed: "실패" }[status]; }
function formatDate(value: string) { return new Date(value).toLocaleDateString("ko-KR", { year: "numeric", month: "2-digit", day: "2-digit" }); }
function formatDateTime(value: string) { return new Date(value).toLocaleString("ko-KR", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }); }
function goUpload() { router.push({ name: "upload" }); }
function goDrive() { router.push({ name: "drive" }); }
function openDocument(id: string) { router.push({ name: "documentView", params: { id } }); }
</script>

<style scoped>
.topbar { background: var(--topbar-bg); border-bottom: 1px solid var(--line); display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); align-items: center; padding: 0 18px; gap: 12px; }
.tb-left { display: flex; align-items: center; gap: 10px; justify-self: start; }
.tb-title-strong { font-weight: 900; font-size: 16px; }
.tb-center { display: flex; justify-content: center; }
.tb-search { width: min(520px, 42vw); padding: 10px 14px; border-radius: 12px; border: 1px solid var(--field-border); background: var(--field-bg); color: var(--field-text); font-weight: 700; }
.tb-right { justify-self: end; }
.container { max-width: 1120px; margin: 0 auto; padding: 22px 16px 40px; display: grid; gap: 16px; }
.hero { display: grid; grid-template-columns: 1.35fr .65fr; gap: 16px; }
.hero-left, .hero-card, .card, .feedback-band { background: var(--card); border: 1px solid var(--line); border-radius: 14px; }
.hero-left { padding: 26px; }
.hero-left h1 { margin: 0; font-size: 24px; line-height: 1.4; }
.hero-left p { margin: 10px 0 0; color: var(--muted); line-height: 1.65; }
.accent { padding: 2px 6px; border-radius: 7px; color: var(--accent); background: var(--accent-soft); }
.hero-actions { margin-top: 16px; }
.hero-card { height: 100%; padding: 18px; }
.hero-card-title { margin-bottom: 12px; font-weight: 800; }
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.stat { padding: 12px; border: 1px solid var(--line); border-radius: 10px; background: var(--card); }
.stat-label, .muted { color: var(--muted); font-size: 12px; }
.stat-value { margin-top: 6px; font-size: 20px; font-weight: 900; }
.card { padding: 16px; }
.card-large { min-height: 310px; }
.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.card-head h2, .feedback-band h2 { margin: 0; font-size: 16px; font-weight: 900; }
.list, .activity { list-style: none; padding: 0; margin: 0; }
.list-item { display: flex; justify-content: space-between; gap: 12px; padding: 12px 4px; border-bottom: 1px solid var(--line); }
.list-item:last-child { border-bottom: 0; }
.doc-title, .activity-title { font-weight: 800; }
.doc-meta, .doc-right { margin-top: 5px; display: flex; align-items: center; gap: 8px; }
.doc-right { margin-top: 0; }
.chip, .badge { padding: 3px 8px; border-radius: 999px; font-size: 12px; }
.chip { border: 1px solid var(--line); background: var(--field-bg); }
.badge-ok { color: #047857; background: #ecfdf5; }
.badge-warn { color: #92400e; background: #fffbeb; }
.badge-bad { color: #991b1b; background: #fef2f2; }
.feedback-band { padding: 16px 18px; display: grid; grid-template-columns: minmax(180px, 1fr) auto auto; align-items: center; gap: 16px; }
.feedback-band p { margin: 4px 0 0; }
.feedback-options { display: grid; grid-template-columns: repeat(3, minmax(72px, 1fr)); gap: 6px; }
.feedback-btn { min-height: 40px; padding: 0 12px; display: inline-flex; align-items: center; justify-content: center; gap: 7px; border: 1px solid var(--field-border); border-radius: 8px; background: var(--card); color: var(--ink); font-weight: 800; cursor: pointer; }
.feedback-btn:hover, .feedback-btn.on { color: var(--accent); border-color: var(--accent); background: var(--accent-soft); }
.feedback-saved { color: #047857; font-size: 12px; font-weight: 800; }
.activity-item { display: flex; gap: 10px; padding: 10px 8px; border-bottom: 1px solid var(--line); }
.dot { width: 8px; height: 8px; margin-top: 6px; border-radius: 50%; background: var(--accent); }
.empty { padding: 16px; border: 1px dashed var(--line); border-radius: 10px; color: var(--muted); background: var(--field-bg); }
.btn { padding: 10px 12px; border: 1px solid var(--field-border); border-radius: 10px; background: var(--button-bg); color: var(--button-text); font-weight: 800; cursor: pointer; }
.btn-primary { color: #fff; border-color: var(--accent); background: var(--accent); }
.btn-ghost { background: transparent; }
.btn-sm { padding: 8px 10px; }
.btn:disabled { opacity: .55; cursor: not-allowed; }
.link, .inline { border: 0; background: transparent; color: var(--accent); font-weight: 800; cursor: pointer; }
.hamburger { display: none; border: 0; background: transparent; color: var(--ink); font-size: 20px; }
:global([data-theme="dark"]) .badge-ok { color: #a7f3d0; background: rgb(6 95 70 / .45); }
:global([data-theme="dark"]) .badge-warn { color: #fde68a; background: rgb(146 64 14 / .4); }
:global([data-theme="dark"]) .badge-bad { color: #fecaca; background: rgb(153 27 27 / .4); }
@media (max-width: 768px) {
  .topbar { grid-template-columns: auto 1fr auto; }
  .tb-center { display: none; }
  .hamburger { display: inline-flex; }
  .container { padding: 16px 12px 32px; }
  .hero { grid-template-columns: 1fr; }
  .feedback-band { grid-template-columns: 1fr; }
}
</style>
