<template>
  <AppLayout>
    <main class="home-page">
      <header class="page-head">
        <div>
          <div class="today">{{ todayLabel }}</div>
          <h1>안녕하세요, {{ userName }}님</h1>
        </div>
        <button class="new-doc" type="button" @click="goUpload">+ 새 문서 변환</button>
      </header>

      <section class="hero">
        <div class="hero-copy">
          <span class="eyebrow">AI 쉬운말 변환</span>
          <h2>전문 용어가 가득한 문서,<br />3초 만에 읽기 쉬운 글로 바꿔드려요.</h2>
          <p>PDF·DOCX·TXT를 올리거나 텍스트를 붙여넣으면 됩니다. 원문은 그대로 두고 이해를 돕는 설명을 더해요.</p>
          <button class="start-btn" type="button" @click="goUpload">지금 시작하기 →</button>
        </div>
      </section>

      <section class="stat-grid" aria-label="이용 현황">
        <article class="stat"><span>총 문서</span><strong>{{ stats.totalDocs }}</strong></article>
        <article class="stat done"><span>변환 완료</span><strong>{{ stats.done }}</strong></article>
        <article class="stat waiting"><span>변환 중</span><strong>{{ stats.processing }}</strong></article>
        <article class="stat"><span>이번 주 Q&amp;A</span><strong>{{ stats.weekQa }}</strong></article>
      </section>

      <section class="home-grid">
        <article class="panel recent-card">
          <div class="panel-head"><h3>최근 문서</h3><button type="button" @click="goDrive">전체 보기 →</button></div>
          <div v-if="recentDocs.length === 0" class="empty">아직 업로드한 문서가 없습니다. <button @click="goUpload">첫 문서 올리기</button></div>
          <div v-else class="doc-list">
            <button v-for="doc in recentDocs.slice(0, 3)" :key="doc.id" class="doc-row" type="button" :disabled="doc.status !== 'done'" @click="openDocument(doc.id)">
              <span :class="['file-type', `type-${doc.type.toLowerCase()}`]">{{ doc.type }}</span>
              <span class="doc-copy"><strong>{{ doc.title }}</strong><small>{{ formatDate(doc.createdAt) }}</small></span>
              <span :class="['badge', badgeClass(doc.status)]">{{ statusLabel(doc.status) }}</span>
            </button>
          </div>
        </article>

        <article class="panel activity-card">
          <h3>최근 활동</h3>
          <div v-if="recentDocs.length" class="activity-list">
            <div v-for="(doc, index) in recentDocs.slice(0, 3)" :key="doc.id" class="activity-row">
              <span :class="['dot', `dot-${index}`]" />
              <span><strong>{{ doc.title }}을(를) {{ doc.status === 'done' ? '변환했어요' : '처리하고 있어요' }}</strong><small>{{ formatDateTime(doc.createdAt) }}</small></span>
            </div>
          </div>
          <div v-else class="empty compact">최근 활동이 없습니다.</div>
        </article>
      </section>
    </main>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import documentService from "../api/document.service";
import AppLayout from "../components/layout/AppLayout.vue";

const router = useRouter();
const authStore = useAuthStore();
const userName = computed(() => authStore.user?.name || "사용자");
const todayLabel = new Intl.DateTimeFormat("ko-KR", { year: "numeric", month: "long", day: "numeric", weekday: "long" }).format(new Date());
type DocStatus = "queued" | "processing" | "done" | "failed";
interface DocItem { id: string; title: string; type: "PDF" | "DOCX" | "TXT" | "UNKNOWN"; status: DocStatus; createdAt: string; }
const recentDocs = ref<DocItem[]>([]);
const stats = ref({ totalDocs: 0, done: 0, processing: 0, weekQa: 0 });

onMounted(async () => {
  if (authStore.token && !authStore.user) await authStore.fetchUser();
  await fetchDashboardData();
});
async function fetchDashboardData() {
  try {
    const recentResponse = await documentService.getDocuments(0, 5);
    recentDocs.value = recentResponse.data.map((doc: any) => ({ id: doc.id, title: doc.title, type: doc.file_type || "UNKNOWN", status: normalizeStatus(doc.status), createdAt: doc.created_at }));
    const docs = (await documentService.getDocuments(0, 100)).data;
    stats.value.totalDocs = docs.length;
    stats.value.done = docs.filter((doc: any) => doc.status === "DONE").length;
    stats.value.processing = docs.filter((doc: any) => doc.status === "PROCESSING" || doc.status === "QUEUED").length;
  } catch (error) { console.error("Dashboard data fetch failed", error); }
}
function normalizeStatus(status: string): DocStatus {
  const value = String(status || "").toLowerCase();
  return value === "queued" || value === "processing" || value === "done" || value === "failed" ? value : "processing";
}
function badgeClass(status: DocStatus) { return status === "done" ? "badge-ok" : status === "failed" ? "badge-bad" : "badge-warn"; }
function statusLabel(status: DocStatus) { return { done: "변환 완료", queued: "대기 중", processing: "변환 중", failed: "실패" }[status]; }
function formatDate(value: string) { return new Date(value).toLocaleDateString("ko-KR", { year: "numeric", month: "2-digit", day: "2-digit" }); }
function formatDateTime(value: string) { return new Date(value).toLocaleString("ko-KR", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }); }
function goUpload() { router.push({ name: "upload" }); }
function goDrive() { router.push({ name: "drive" }); }
function openDocument(id: string) { router.push({ name: "documentView", params: { id } }); }
</script>

<style scoped>
.home-page { width: min(1080px, 100%); margin: 0 auto; padding: 34px 40px 56px; }
.page-head { margin-bottom: 26px; display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.today { margin-bottom: 5px; color: var(--muted); font-size: 13px; font-weight: 500; }
.page-head h1 { margin: 0; font-size: 27px; }
.new-doc { height: 44px; padding: 0 20px; border: 0; border-radius: 13px; color: #fff; background: var(--accent-gradient); box-shadow: 0 8px 18px rgb(106 77 255 / .26); font-size: 14px; font-weight: 600; cursor: pointer; }
.hero { margin-bottom: 20px; padding: 30px 32px; overflow: hidden; border: 1px solid var(--line); border-radius: 22px; background: var(--soft); }
[data-theme="dark"] .hero { background: var(--soft); }
.hero-copy { max-width: 560px; }
.eyebrow { display: inline-block; margin-bottom: 14px; padding: 5px 11px; border: 1px solid #e8e6f6; border-radius: 999px; color: var(--accent); background: var(--surface); font-size: 12px; font-weight: 600; }
.hero h2 { margin: 0 0 10px; font-size: 23px; line-height: 1.4; }
.hero p { margin: 0 0 18px; color: var(--muted); font-size: 14px; line-height: 1.7; }
.start-btn { height: 42px; padding: 0 18px; border: 0; border-radius: 12px; color: #fff; background: #191527; font-size: 14px; font-weight: 600; cursor: pointer; }
[data-theme="dark"] .start-btn { background: var(--accent-gradient); }
.stat-grid { margin-bottom: 20px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.stat { padding: 18px 20px; border: 1px solid var(--line); border-radius: 18px; background: var(--surface); }
.stat span { display: block; margin-bottom: 10px; color: var(--muted); font-size: 13px; font-weight: 500; }
.stat strong { font-family: "Space Grotesk", sans-serif; font-size: 28px; }
.stat.done strong { color: #12a58a; }
.stat.waiting strong { color: #e0952a; }
.home-grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: 16px; }
.panel { padding: 22px; border: 1px solid var(--line); border-radius: 20px; background: var(--surface); }
.panel h3 { margin: 0; font-size: 16px; }
.panel-head { margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; }
.panel-head button, .empty button { padding: 0; border: 0; color: var(--accent); background: transparent; font-size: 13px; font-weight: 600; cursor: pointer; }
.doc-list { display: flex; flex-direction: column; }
.doc-row { width: 100%; padding: 13px 8px; display: flex; align-items: center; gap: 13px; border: 0; border-bottom: 1px solid #f2f0f7; color: var(--ink); background: transparent; text-align: left; cursor: pointer; }
.doc-row:last-child { border-bottom: 0; }
.doc-row:disabled { cursor: default; }
.file-type { width: 38px; height: 38px; display: grid; place-items: center; flex: none; border-radius: 11px; color: #e14a6b; background: #fdecef; font-size: 10px; font-weight: 700; }
.type-docx { color: #3f68e0; background: #eaf0ff; }
.type-txt, .type-unknown { color: #5b6472; background: #eef1f4; }
.doc-copy { min-width: 0; display: grid; flex: 1; }
.doc-copy strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 14px; font-weight: 600; }
.doc-copy small, .activity-row small { margin-top: 2px; color: var(--muted); font-size: 12px; }
.badge { padding: 4px 10px; border-radius: 999px; font-size: 11.5px; font-weight: 600; }
.badge-ok { color: #0c7a68; background: #e7f8f3; }
.badge-warn { color: #a9711a; background: #fff6e6; }
.badge-bad { color: #c0392b; background: #fdeef0; }
.activity-card > h3 { margin-bottom: 14px; }
.activity-list { display: flex; flex-direction: column; gap: 16px; }
.activity-row { display: flex; gap: 11px; }
.activity-row > span:last-child { min-width: 0; display: grid; }
.activity-row strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13.5px; font-weight: 500; }
.dot { width: 8px; height: 8px; margin-top: 6px; flex: none; border-radius: 50%; background: var(--accent); }
.dot-1 { background: #12b39a; }.dot-2 { background: #ff9f43; }
.empty { padding: 24px; border: 1px dashed var(--line); border-radius: 13px; color: var(--muted); background: var(--soft); text-align: center; }
@media (max-width: 900px) { .stat-grid { grid-template-columns: repeat(2, 1fr); }.home-grid { grid-template-columns: 1fr; } }
@media (max-width: 620px) { .home-page { padding: 24px 18px 40px; }.page-head h1 { font-size: 22px; }.new-doc { width: 44px; padding: 0; overflow: hidden; white-space: nowrap; font-size: 0 !important; }.new-doc::before { content: "+"; font-size: 22px; }.hero { padding: 24px 22px; }.hero h2 { font-size: 20px; }.stat-grid { gap: 10px; }.stat { padding: 15px; } }
</style>
