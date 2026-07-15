<!-- 인수인계용: 프로필/환경 설정 화면 -->
<template>
  <AppLayout v-slot="{ toggleSidebar }">
    <!-- 상단바 -->
    <header class="topbar">
      <div class="tb-left">
        <div class="tb-title">
          <button class="hamburger" @click="toggleSidebar" aria-label="Open menu">☰</button>
          <span class="tb-title-strong">프로필/설정</span>
          <span class="tb-sub">· 계정 정보와 환경 설정</span>
        </div>
      </div>
      <div class="tb-right">
        <button class="btn btn-save" @click="save">저장</button>
      </div>
    </header>

    <main class="content">
      <!-- 프로필 카드 -->
      <section class="card profile-card">
        <div class="pc-left">
          <div class="avatar">
            <div class="avatar-ring"></div>
            <div class="avatar-img">{{ initials(user.name) }}</div>
          </div>

          <div class="pc-meta">
            <div class="name-row">
              <div class="name">{{ user.name || "이름 없음" }}</div>
              <span class="role-pill">{{ roleLabel }}</span>
            </div>
            <div class="email muted">{{ user.email }}</div>

            <div class="meta-line">
              <span class="tag">Last login</span>
              <span class="muted">{{ formatDateTime(user.lastLoginAt) }}</span>
              <span class="sep">·</span>
              <span class="tag">Joined</span>
              <span class="muted">{{ formatDate(user.joinedAt) }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- ✅ 3개 카드 그리드 -->
      <section class="grid">
        <!-- 챗봇 답변 설정 -->
        <article class="card card-eq">
          <div class="card-head">
            <h2>챗봇 답변 설정</h2>
            <div class="badge">Chatbot</div>
          </div>

          <div class="form form-eq">
            <div class="field">
              <div class="label">챗봇 답변 방식</div>
              <div class="seg">
                <button
                  :class="['seg-btn', assist.level === 'close' && 'on']"
                  @click="assist.level = 'close'"
                >
                  원문형
                </button>
                <button
                  :class="['seg-btn', assist.level === 'easy' && 'on']"
                  @click="assist.level = 'easy'"
                >
                  쉽게 설명
                </button>
                <button
                  :class="['seg-btn', assist.level === 'summary' && 'on']"
                  @click="assist.level = 'summary'"
                >
                  요약 중심
                </button>
              </div>
              <div class="help muted">
                Q&A 챗봇 답변 톤에만 적용됩니다. 파일 업로드 변환은 항상 쉽게 처리됩니다.
              </div>
            </div>

            <div class="field">
              <div class="label">용어 설명 깊이</div>
              <input class="range" type="range" min="1" max="5" v-model="assist.termDepth" />
              <div class="range-row">
                <span class="muted">간단</span>
                <span class="mono">Lv. {{ assist.termDepth }}</span>
                <span class="muted">자세히</span>
              </div>
            </div>

            <div class="field">
              <div class="label">근거 표시 방식</div>
              <select class="select" v-model="assist.evidenceMode">
                <option value="inline">문장 옆(Inline)</option>
                <option value="panel">오른쪽 패널(Panel)</option>
                <option value="hover">하이라이트 + 호버(Hover)</option>
              </select>
            </div>
          </div>

          <div class="card-foot">
            <span class="foot-muted muted">일반 질문과 문서 질문의 답변 스타일을 설정합니다.</span>
          </div>
        </article>

        <!-- 화면 표시 -->
        <article class="card card-eq">
          <div class="card-head">
            <h2>화면 표시</h2>
            <div class="badge">UI</div>
          </div>

          <div class="form form-eq">
            <div class="field">
              <div class="label">테마</div>
              <div class="row">
                <button
                  class="btn btn-outline theme-btn"
                  :class="{ on: theme === 'light' }"
                  @click="setTheme('light')"
                >
                  라이트
                </button>
                <button
                  class="btn btn-outline theme-btn"
                  :class="{ on: theme === 'dark' }"
                  @click="setTheme('dark')"
                >
                  다크
                </button>
              </div>
              <div class="help muted">전 페이지 공통으로 적용됩니다.</div>
            </div>

            <div class="field">
              <div class="label">글자 크기</div>
              <div class="seg">
                <button
                  :class="['seg-btn', ui.fontSize === 'sm' && 'on']"
                  @click="setFontSize('sm')"
                >
                  작게
                </button>
                <button
                  :class="['seg-btn', ui.fontSize === 'md' && 'on']"
                  @click="setFontSize('md')"
                >
                  보통
                </button>
                <button
                  :class="['seg-btn', ui.fontSize === 'lg' && 'on']"
                  @click="setFontSize('lg')"
                >
                  크게
                </button>
                <button
                  :class="['seg-btn', ui.fontSize === 'custom' && 'on']"
                  @click="setFontSize('custom')"
                >
                  커스텀
                </button>
              </div>
              <div v-if="ui.fontSize === 'custom'" class="custom-size-panel">
                <input
                  class="range"
                  type="range"
                  min="12"
                  max="24"
                  step="1"
                  v-model.number="ui.customFontSize"
                  @input="setCustomFontSize(ui.customFontSize)"
                />
                <div class="custom-size-row">
                  <span class="muted">12px</span>
                  <label class="custom-number">
                    <input
                      class="input number-input"
                      type="number"
                      min="12"
                      max="24"
                      step="1"
                      v-model.number="ui.customFontSize"
                      @input="setCustomFontSize(ui.customFontSize)"
                      @blur="setCustomFontSize(ui.customFontSize)"
                    />
                    <span>px</span>
                  </label>
                  <span class="muted">24px</span>
                </div>
              </div>
            </div>

            <div class="field">
              <div class="label">문장 단위 표시</div>
              <label class="toggle">
                <input type="checkbox" v-model="ui.sentenceMode" />
                <span class="knob"></span>
                <span class="toggle-text muted">문장별 구분선/번호 표시</span>
              </label>
            </div>
          </div>

          <div class="card-foot">
            <span class="foot-muted muted">가독성과 표시 스타일을 설정합니다.</span>
          </div>
        </article>

        <!-- 계정 관리 -->
        <article class="card card-eq">
          <div class="card-head">
            <h2>계정 관리</h2>
            <div class="right-badges">
              <span class="badge">Account</span>
              <span v-if="isAdmin" class="admin-badge">🛡️ Admin</span>
            </div>
          </div>

          <div class="form form-eq">
            <div class="field">
              <div class="label">이름</div>
              <input class="input" v-model.trim="user.name" placeholder="이름" />
            </div>

            <div class="field">
              <div class="label">이메일</div>
              <input class="input" :value="user.email" disabled />
            </div>

            <div class="account-info">
              <div class="info-item">
                <span class="muted">역할</span>
                <strong>{{ roleLabel }}</strong>
              </div>
              <div class="info-item">
                <span class="muted">가입일</span>
                <strong>{{ formatDate(user.joinedAt) }}</strong>
              </div>
              <div class="info-item">
                <span class="muted">최근 로그인</span>
                <strong>{{ formatDateTime(user.lastLoginAt) }}</strong>
              </div>
            </div>

            <div class="field">
              <div class="label">보안</div>
              <button class="btn btn-primary full" @click="goChangePassword">비밀번호 변경</button>
            </div>

            <div class="field">
              <div class="label">세션</div>
              <button class="btn btn-ghost full" @click="logout">로그아웃</button>
            </div>
          </div>

          <div class="card-foot">
            <span class="foot-muted muted">계정과 보안 설정을 관리합니다.</span>
          </div>
        </article>
      </section>
    </main>

    <!-- ✅ 토스트 -->
    <div class="toast" :class="{ show: toast.show }">
      설정이 저장되었습니다
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import AppLayout from "../components/layout/AppLayout.vue";

const router = useRouter();
const authStore = useAuthStore();

const theme = ref<"light" | "dark">("light");

const role = ref<"ADMIN" | "USER" | "">("");
const isAdmin = computed(() => role.value === "ADMIN");
const roleLabel = computed(() => (role.value === "ADMIN" ? "관리자" : "일반 사용자"));

const user = reactive({
  name: "User",
  email: "",
  lastLoginAt: new Date().toISOString(),
  joinedAt: new Date().toISOString(),
});

type AssistLevel = "close" | "easy" | "summary";

const assist = reactive({
  level: "easy" as AssistLevel,
  termDepth: 3,
  evidenceMode: "panel" as "inline" | "panel" | "hover",
});

type FontSizeMode = "sm" | "md" | "lg" | "custom";

const ui = reactive({
  theme: "light" as "light" | "dark",
  fontSize: "md" as FontSizeMode,
  customFontSize: 16,
  sentenceMode: true,
});

const toast = reactive({
  show: false,
  timer: 0 as unknown as number,
});

function applyTheme(next: "light" | "dark") {
  theme.value = next;
  ui.theme = next;
  document.documentElement.setAttribute("data-theme", next);
  document.body.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
}
function setTheme(next: "light" | "dark") {
  applyTheme(next);
}
const presetFontSize: Record<Exclude<FontSizeMode, "custom">, number> = {
  sm: 14,
  md: 16,
  lg: 18,
};

function clampCustomFontSize(value: unknown) {
  const next = Number(value);
  if (!Number.isFinite(next)) return 16;
  return Math.min(24, Math.max(12, Math.round(next)));
}

function applyFontSize(mode: FontSizeMode) {
  const custom = clampCustomFontSize(ui.customFontSize);
  ui.customFontSize = custom;
  const baseSize = mode === "custom" ? custom : presetFontSize[mode];

  document.documentElement.setAttribute("data-size", mode);
  document.documentElement.setAttribute("data-custom-font-size", String(custom));
  document.documentElement.style.setProperty("--base-font-size", `${baseSize}px`);
  document.body.style.setProperty("--app-title-size", `${Math.min(28, baseSize + 2)}px`);
  document.body.style.setProperty("--app-body-size", `${baseSize}px`);
  document.body.style.setProperty("--app-control-size", `${baseSize}px`);
  document.body.style.setProperty("--app-small-size", `${Math.max(10, baseSize - 2)}px`);
  document.body.classList.remove("font-size-sm", "font-size-md", "font-size-lg", "font-size-custom");
  document.body.classList.add(`font-size-${mode}`);
  localStorage.setItem("font_size", mode);
  localStorage.setItem("custom_font_size", String(custom));
}

function setFontSize(next: FontSizeMode) {
  ui.fontSize = next;
  applyFontSize(next);
}

function setCustomFontSize(value: unknown) {
  ui.customFontSize = clampCustomFontSize(value);
  ui.fontSize = "custom";
  applyFontSize("custom");
}

function normalizeAssistLevel(value: unknown): AssistLevel {
  const next = String(value || "");
  if (next === "close" || next === "easy" || next === "summary") return next;
  if (next === "low") return "close";
  if (next === "mid") return "easy";
  if (next === "high") return "summary";
  return "easy";
}

function goChangePassword() {
  router.push({ name: "changePassword" }).catch(() => {});
}

function logout() {
  authStore.logout();
  router.push({ name: "login" }).catch(() => {});
}

async function save() {
  try {
    const payload = { assist: { ...assist }, ui: { ...ui, theme: theme.value } };
    
    await authStore.updateUser({ name: user.name.trim() || "User", profile_settings: payload });

    localStorage.setItem("profile_settings", JSON.stringify(payload));
    localStorage.setItem("theme", theme.value);
    localStorage.setItem("font_size", ui.fontSize);

    toast.show = false;
    if (toast.timer) window.clearTimeout(toast.timer);

    requestAnimationFrame(() => {
      toast.show = true;
      toast.timer = window.setTimeout(() => {
        toast.show = false;
      }, 1800);
    });
  } catch (error) {
    console.error("Failed to save settings", error);
    // 에러 처리 필요(토스트 등으로)
  }
}

function initials(name: string) {
  const s = (name || "").trim();
  if (!s) return "U";
  const parts = s.split(/\s+/);
  const a = parts[0]?.[0] ?? "U";
  const b = parts.length > 1 ? parts[1]?.[0] ?? "" : "";
  return (a + b).toUpperCase();
}

function formatDate(iso: string) {
  if (!iso) return "-";
  const d = new Date(iso);
  return d.toLocaleDateString("ko-KR", { year: "numeric", month: "2-digit", day: "2-digit" });
}
function formatDateTime(iso: string) {
  if (!iso) return "-";
  const d = new Date(iso);
  return d.toLocaleString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

onMounted(async () => {
  const savedTheme = (localStorage.getItem("theme") as "light" | "dark") || "light";
  const savedFontSize = (localStorage.getItem("font_size") as FontSizeMode) || "md";
  ui.customFontSize = clampCustomFontSize(localStorage.getItem("custom_font_size") || 16);
  applyTheme(savedTheme);
  setFontSize(savedFontSize === "sm" || savedFontSize === "md" || savedFontSize === "lg" || savedFontSize === "custom" ? savedFontSize : "md");

  // 사용자 정보 가져오기
  if (!authStore.user) {
    await authStore.fetchUser();
  }

  if (authStore.user) {
    user.name = authStore.user.name;
    user.email = authStore.user.email;
    user.lastLoginAt = authStore.user.last_login_at || new Date().toISOString();
    user.joinedAt = authStore.user.created_at || new Date().toISOString();
    role.value = (authStore.user.role as "ADMIN" | "USER") || "";

    // 설정 복원(DB > 로컬 스토리지)
    const settings = authStore.user.profile_settings;
    if (settings) {
      if (settings.assist) {
        Object.assign(assist, settings.assist);
        assist.level = normalizeAssistLevel(settings.assist.level);
      }
      if (settings.ui) {
        Object.assign(ui, settings.ui);
        if (settings.ui.theme === "light" || settings.ui.theme === "dark") applyTheme(settings.ui.theme);
        if (settings.ui.customFontSize) ui.customFontSize = clampCustomFontSize(settings.ui.customFontSize);
        if (settings.ui.fontSize === "sm" || settings.ui.fontSize === "md" || settings.ui.fontSize === "lg" || settings.ui.fontSize === "custom") setFontSize(settings.ui.fontSize);
      }
    } else {
       // DB에 없으면 로컬 스토리지 확인(마이그레이션 과도기)
       const localSaved = localStorage.getItem("profile_settings");
       if (localSaved) {
         try {
           const obj = JSON.parse(localSaved);
           if (obj?.assist) {
             Object.assign(assist, obj.assist);
             assist.level = normalizeAssistLevel(obj.assist.level);
           }
           if (obj?.ui) {
             Object.assign(ui, obj.ui);
             if (obj.ui.theme === "light" || obj.ui.theme === "dark") applyTheme(obj.ui.theme);
             if (obj.ui.customFontSize) ui.customFontSize = clampCustomFontSize(obj.ui.customFontSize);
             if (obj.ui.fontSize === "sm" || obj.ui.fontSize === "md" || obj.ui.fontSize === "lg" || obj.ui.fontSize === "custom") setFontSize(obj.ui.fontSize);
           }
         } catch {}
       }
    }
  }
});
</script>

<style scoped>
/* Main */
.main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* Header */
.topbar {
  background: var(--topbar-bg);
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 18px;
  /* height handled by AppLayout grid */
  height: 100%;
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
  font-weight: 1000;
  font-size: 16px;
  letter-spacing: -0.2px;
}
.tb-sub {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}
.tb-right {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.muted {
  color: var(--muted);
  font-size: 12px;
}
.small {
  font-size: 12px;
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

/* Cards */
.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 18px;
  box-shadow: var(--shadow);
  padding: 16px;
  backdrop-filter: blur(10px);
}
.profile-card {
  padding: 18px;
}

.pc-left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.avatar {
  position: relative;
  width: 74px;
  height: 74px;
  flex: 0 0 auto;
}
.avatar-ring {
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--b1), var(--b2));
}
.avatar-img {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: var(--card-solid);
  border: 1px solid var(--line);
  display: grid;
  place-items: center;
  font-weight: 1100;
  letter-spacing: -0.3px;
}

.pc-meta {
  min-width: 0;
}
.name-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.name {
  font-weight: 1100;
  font-size: 18px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 520px;
}
.email {
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 520px;
}
.meta-line {
  margin-top: 8px;
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--button-bg);
  font-weight: 1000;
}
.sep {
  opacity: 0.6;
}

.admin-pill {
  font-size: 12px;
  font-weight: 1100;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(17, 24, 39, 0.1);
  border: 1px solid rgba(17, 24, 39, 0.15);
}

.role-pill {
  font-size: 12px;
  font-weight: 1000;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--accent-soft);
  border: 1px solid var(--accent-border);
  color: var(--ink);
}
.account-info {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
.info-item {
  display: grid;
  gap: 4px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--field-bg);
  min-width: 0;
}
.info-item strong {
  color: var(--ink);
  font-size: 12px;
  line-height: 1.35;
  overflow-wrap: anywhere;
}
/* Grid equal */
.grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  align-items: stretch;
}
.card-eq {
  display: flex;
  flex-direction: column;
  min-height: 280px;
}
.form-eq {
  display: grid;
  gap: 12px;
  flex: 1 1 auto;
}
.card-foot {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}
.foot-muted {
  font-size: 12px;
  font-weight: 850;
}

/* Card head */
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}
.card-head h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 1100;
}
.badge {
  font-size: 12px;
  font-weight: 1100;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(29, 78, 216, 0.1);
  border: 1px solid rgba(29, 78, 216, 0.18);
}
.right-badges {
  display: flex;
  gap: 8px;
  align-items: center;
}
.admin-badge {
  font-size: 12px;
  font-weight: 1100;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(17, 24, 39, 0.1);
  border: 1px solid rgba(17, 24, 39, 0.15);
}
/* Fields */
.field {
  display: grid;
  gap: 8px;
}
.label {
  font-size: 12px;
  font-weight: 1000;
  color: var(--muted);
}

.input,
.select {
  width: 100%;
  padding: 12px 12px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: var(--field-bg);
  outline: none;
  font-weight: 950;
}
.help {
  font-size: 12px;
}
.range {
  width: 100%;
}

.custom-size-panel {
  display: grid;
  gap: 8px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--field-bg);
}
.custom-size-row {
  display: grid;
  grid-template-columns: auto minmax(90px, 130px) auto;
  align-items: center;
  gap: 10px;
}
.custom-number {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 1000;
  color: var(--ink);
}
.number-input {
  text-align: center;
  padding: 8px 10px;
}
.range-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.seg {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.seg-btn {
  border-radius: 14px;
  padding: 10px 12px;
  font-weight: 1100;
  cursor: pointer;
  border: 1px solid var(--line);
  background: var(--field-bg);
}
.seg-btn.on {
  border-color: rgba(29, 78, 216, 0.3);
  background: rgba(29, 78, 216, 0.1);
}

.toggle {
  display: flex;
  align-items: center;
  gap: 10px;
}
.toggle input {
  display: none;
}
.knob {
  width: 46px;
  height: 26px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.35);
  position: relative;
  border: 1px solid var(--line);
}
.knob::after {
  content: "";
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--card-solid);
  transition: all 0.18s ease;
}
.toggle input:checked + .knob {
  background: rgba(29, 78, 216, 0.32);
}
.toggle input:checked + .knob::after {
  left: 23px;
}

.row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.full {
  width: 100%;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono",
    "Courier New", monospace;
  font-weight: 1100;
}

/* Buttons */
.btn {
  border-radius: 14px;
  padding: 10px 12px;
  font-weight: 1100;
  cursor: pointer;
  border: 1px solid transparent;
  background: var(--button-bg);
}
.btn-save {
  background: linear-gradient(90deg, #2563eb, #1d4ed8);
  color: #fff;
  border-color: rgba(37, 99, 235, 0.35);
}
.btn-primary {
  background: linear-gradient(90deg, var(--b1), var(--b2));
  color: #fff;
  border-color: rgba(29, 78, 216, 0.28);
}
.btn-outline {
  border-color: var(--line);
}
.theme-btn.on {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
.theme-btn.on:hover {
  background: #1f6feb;
}
.btn-ghost {
  background: transparent;
  border-color: var(--line);
}

/* ✅ Toast */
.toast {
  position: fixed;
  right: 24px;
  bottom: 24px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(17, 24, 39, 0.92);
  color: #fff;
  font-weight: 950;
  font-size: 13px;
  transform: translateY(10px);
  opacity: 0;
  pointer-events: none;
  transition: all 0.18s ease;
}
.toast.show {
  transform: translateY(0);
  opacity: 1;
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

/* Responsive */
@media (max-width: 1180px) {
  .grid {
    grid-template-columns: 1fr 1fr;
  }
}
@media (max-width: 820px) {
  .hamburger {
    display: inline-flex;
  }
  .grid {
    grid-template-columns: 1fr;
  }
  .card-eq {
    min-height: auto;
  }
  .account-info {
    grid-template-columns: 1fr;
  }

  .custom-size-row {
    grid-template-columns: 1fr;
    justify-items: stretch;
  }
  .custom-number {
    justify-content: center;
  }
}

.input,
.select,
.seg-btn {
  color: var(--field-text);
}

.btn {
  color: var(--button-text);
}

.btn-save,
.btn-primary,
.theme-btn.on {
  color: #fff;
}

.input:focus,
.select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.seg-btn:hover,
.btn:hover {
  background: var(--button-hover);
}

.seg-btn.on,
.badge {
  border-color: var(--accent-border);
  background: var(--accent-soft);
}

:global([data-theme="dark"]) .topbar {
  background: var(--topbar-bg);
  border-bottom-color: var(--line);
}

:global([data-theme="dark"]) .profile-card {
  background: linear-gradient(135deg, rgb(91 140 255 / 0.1), rgb(33 199 183 / 0.05)), var(--card);
}

:global([data-theme="dark"]) .card {
  background: var(--card);
  border-color: var(--line);
  box-shadow: var(--shadow);
}

:global([data-theme="dark"]) .avatar-img,
:global([data-theme="dark"]) .tag,
:global([data-theme="dark"]) .admin-pill,
:global([data-theme="dark"]) .admin-badge,
:global([data-theme="dark"]) .badge {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: var(--ink);
}

:global([data-theme="dark"]) .input,
:global([data-theme="dark"]) .select,
:global([data-theme="dark"]) .seg-btn,
:global([data-theme="dark"]) .btn {
  background: var(--field-bg);
  border-color: var(--field-border);
  color: var(--field-text);
}

:global([data-theme="dark"]) .seg-btn:hover,
:global([data-theme="dark"]) .btn:hover {
  background: var(--button-hover);
}

:global([data-theme="dark"]) .seg-btn.on,
:global([data-theme="dark"]) .theme-btn.on,
:global([data-theme="dark"]) .btn-save,
:global([data-theme="dark"]) .btn-primary {
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  border-color: transparent;
  color: #fff;
}

:global([data-theme="dark"]) .btn-ghost,
:global([data-theme="dark"]) .btn-outline {
  background: transparent;
  border-color: var(--field-border);
  color: var(--ink);
}

:global([data-theme="dark"]) .knob {
  background: #0d1017;
  border-color: var(--field-border);
}

:global([data-theme="dark"]) .toggle input:checked + .knob {
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

:global([data-theme="dark"]) .hamburger {
  color: var(--ink);
}
</style>
