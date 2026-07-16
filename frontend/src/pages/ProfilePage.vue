<!-- 인수인계용: 프로필/환경 설정 화면 -->
<template>
  <AppLayout>
    <main class="doq-profile">
      <h1>프로필</h1>
      <section class="doq-profile-card">
        <div class="doq-profile-avatar">{{ initials(user.name) }}</div>
        <div class="doq-profile-copy">
          <strong>{{ user.name || "이름 없음" }}</strong>
          <span>{{ user.email }}</span>
          <small>▣ {{ formatDate(user.joinedAt) }} 가입 · {{ daysSinceJoin }}일째</small>
        </div>
        <button type="button" @click="profileModal = 'edit'">프로필 편집</button>
      </section>

      <section class="doq-screen-settings">
        <h2>화면 설정</h2>
        <div class="doq-setting-row">
          <div><strong>테마</strong><span>밝게 / 어둡게</span></div>
          <div class="doq-mini-segment"><button :class="{ active: theme === 'light' }" @click="setTheme('light')">밝게</button><button :class="{ active: theme === 'dark' }" @click="setTheme('dark')">어둡게</button></div>
        </div>
        <div class="doq-setting-row doq-size-row">
          <div><strong>글자 크기</strong><span>읽기 편한 크기로 조절</span></div>
          <div class="doq-mini-segment"><button :class="{ active: ui.fontSize === 'sm' }" @click="setFontSize('sm')">작게</button><button :class="{ active: ui.fontSize === 'md' }" @click="setFontSize('md')">중간</button><button :class="{ active: ui.fontSize === 'lg' }" @click="setFontSize('lg')">크게</button><button :class="{ active: ui.fontSize === 'custom' }" @click="setFontSize('custom')">커스텀</button></div>
          <div v-if="ui.fontSize === 'custom'" class="doq-custom-size"><input type="range" min="12" max="24" step="1" v-model.number="ui.customFontSize" @input="setCustomFontSize(ui.customFontSize)" /><span>{{ ui.customFontSize }}px</span></div>
        </div>
        <div class="doq-setting-row">
          <div><strong>변환 알림</strong><span>문서 변환이 끝나면 알려드려요</span></div>
          <button class="doq-toggle" :class="{ on: ui.sentenceMode }" type="button" role="switch" :aria-checked="ui.sentenceMode" @click="toggleNotification"><span /></button>
        </div>
      </section>

      <section class="doq-help-card">
        <div><strong>도움이 필요하신가요?</strong><span>사용 중 궁금한 점이나 오류를 문의해 주세요.</span></div>
        <button type="button" @click="profileModal = 'inquiry'">문의하기</button>
      </section>
      <button class="doq-profile-logout" type="button" @click="logout">로그아웃</button>

      <div v-if="profileModal" class="doq-modal-backdrop" @click.self="profileModal = ''">
        <section class="doq-modal">
          <header><h2>{{ profileModal === 'edit' ? "프로필 편집" : "문의하기" }}</h2><button type="button" @click="profileModal = ''">×</button></header>
          <template v-if="profileModal === 'edit'">
            <div class="doq-modal-avatar">{{ initials(user.name) }}</div>
            <label>이름<input v-model.trim="user.name" /></label>
            <label>이메일<input :value="user.email" disabled /></label>
            <footer><button type="button" @click="profileModal = ''">취소</button><button type="button" @click="saveProfileModal">저장</button></footer>
          </template>
          <template v-else>
            <p>보통 1영업일 안에 이메일로 답변드려요.</p>
            <label>문의 유형<select><option>사용 방법</option><option>오류 신고</option><option>기능 제안</option><option>기타</option></select></label>
            <label>내용<textarea placeholder="궁금한 점이나 겪으신 문제를 적어 주세요." /></label>
            <label>회신받을 이메일<input :value="user.email" /></label>
            <footer><button type="button" @click="profileModal = ''">취소</button><button type="button" @click="submitInquiry">보내기</button></footer>
          </template>
        </section>
      </div>
      <div class="toast" :class="{ show: toast.show }">설정이 저장되었습니다</div>
    </main>


  </AppLayout>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import AppLayout from "../components/layout/AppLayout.vue";

const router = useRouter();
const authStore = useAuthStore();

const theme = ref<"light" | "dark">("light");


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
const profileModal = ref<"" | "edit" | "inquiry">("");
const settingsReady = ref(false);
let settingsSaveTimer: number | undefined;
const daysSinceJoin = computed(() => {
  const joined = new Date(user.joinedAt).getTime();
  return Number.isFinite(joined) ? Math.max(1, Math.floor((Date.now() - joined) / 86_400_000) + 1) : 1;
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
  scheduleSettingsSave();
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
  scheduleSettingsSave();
}

function setCustomFontSize(value: unknown) {
  ui.customFontSize = clampCustomFontSize(value);
  ui.fontSize = "custom";
  applyFontSize("custom");
  scheduleSettingsSave();
}

function toggleNotification() {
  ui.sentenceMode = !ui.sentenceMode;
  scheduleSettingsSave();
}

function scheduleSettingsSave() {
  if (!settingsReady.value) return;
  if (settingsSaveTimer) window.clearTimeout(settingsSaveTimer);
  settingsSaveTimer = window.setTimeout(() => { void save(); }, 350);
}

function normalizeAssistLevel(value: unknown): AssistLevel {
  const next = String(value || "");
  if (next === "close" || next === "easy" || next === "summary") return next;
  if (next === "low") return "close";
  if (next === "mid") return "easy";
  if (next === "high") return "summary";
  return "easy";
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

async function saveProfileModal() {
  await save();
  profileModal.value = "";
}

function submitInquiry() {
  profileModal.value = "";
  toast.show = true;
  window.setTimeout(() => { toast.show = false; }, 1800);
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
  settingsReady.value = true;
});

onUnmounted(() => {
  if (settingsSaveTimer) window.clearTimeout(settingsSaveTimer);
  if (toast.timer) window.clearTimeout(toast.timer);
});
</script>


<style scoped>
.doq-profile { width: min(760px, 100%); margin: 0 auto; padding: 34px 40px 56px; }.doq-profile > h1 { margin: 0 0 24px; font-size: 24px; letter-spacing: -.01em; }
.doq-profile-card { margin-bottom: 16px; padding: 24px; display: flex; align-items: center; gap: 18px; border: 1px solid var(--line); border-radius: 20px; background: var(--surface); }
.doq-profile-avatar, .doq-modal-avatar { display: grid; place-items: center; flex: none; color: #fff; background: linear-gradient(135deg,#ffb86b,#ff7eb3); font-weight: 700; }.doq-profile-avatar { width: 64px; height: 64px; border-radius: 20px; font-size: 24px; }.doq-profile-copy { min-width: 0; display: grid; flex: 1; }.doq-profile-copy > strong { font-size: 18px; }.doq-profile-copy > span { margin-top: 3px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--muted); font-size: 13.5px; }.doq-profile-copy > small { margin-top: 8px; color: var(--muted); font-size: 12.5px; }
.doq-profile-card > button { height: 40px; padding: 0 16px; border: 1px solid var(--line); border-radius: 12px; color: var(--sub); background: var(--surface); font-size: 13.5px; font-weight: 600; cursor: pointer; }
.doq-screen-settings { margin-bottom: 16px; padding: 24px; border: 1px solid var(--line); border-radius: 20px; background: var(--surface); }.doq-screen-settings h2 { margin: 0 0 18px; font-size: 16px; }
.doq-setting-row { min-height: 66px; padding: 12px 0; display: flex; align-items: center; justify-content: space-between; gap: 12px; border-bottom: 1px solid var(--line); }.doq-setting-row:last-child { border-bottom: 0; }.doq-setting-row > div:first-child { display: grid; }.doq-setting-row > div:first-child strong { font-size: 14px; font-weight: 500; }.doq-setting-row > div:first-child span { margin-top: 2px; color: var(--muted); font-size: 12.5px; }
.doq-mini-segment { padding: 3px; display: flex; gap: 3px; border-radius: 10px; background: var(--soft); }.doq-mini-segment button { padding: 7px 12px; border: 0; border-radius: 8px; color: var(--muted); background: transparent; font-size: 12.5px; font-weight: 600; cursor: pointer; }.doq-mini-segment button.active { color: var(--ink); background: var(--surface); box-shadow: 0 1px 3px rgb(0 0 0 / .08); }
.doq-size-row { flex-wrap: wrap; }.doq-custom-size { width: 100%; display: flex; align-items: center; gap: 12px; }.doq-custom-size input { flex: 1; accent-color: var(--accent); }.doq-custom-size span { min-width: 46px; color: var(--ink); font-family: "Space Grotesk", sans-serif; font-size: 13px; font-weight: 600; text-align: right; }
.doq-toggle { width: 44px; height: 26px; padding: 3px; border: 0; border-radius: 999px; background: var(--line); cursor: pointer; transition: background .2s; }.doq-toggle span { width: 20px; height: 20px; display: block; border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgb(0 0 0 / .2); transition: transform .2s; }.doq-toggle.on { background: var(--accent-gradient); }.doq-toggle.on span { transform: translateX(18px); }
.doq-help-card { margin-bottom: 16px; padding: 20px 24px; display: flex; align-items: center; justify-content: space-between; gap: 16px; border: 1px solid var(--line); border-radius: 20px; background: var(--surface); }.doq-help-card > div { display: grid; }.doq-help-card strong { font-size: 15px; }.doq-help-card span { margin-top: 3px; color: var(--muted); font-size: 13px; }.doq-help-card button { height: 40px; padding: 0 18px; flex: none; border: 0; border-radius: 12px; color: #fff; background: var(--accent-gradient); font-size: 13.5px; font-weight: 600; cursor: pointer; }
.doq-profile-logout { width: 100%; height: 48px; border: 1px solid #f2d4d4; border-radius: 14px; color: #d0524a; background: var(--surface); font-size: 14px; font-weight: 600; cursor: pointer; }
.toast { position: fixed; left: 50%; bottom: 28px; z-index: 1300; padding: 11px 18px; transform: translate(-50%, 14px); border: 1px solid var(--line); border-radius: 12px; color: var(--ink); background: var(--surface); box-shadow: 0 12px 30px rgb(20 15 45 / .16); opacity: 0; visibility: hidden; pointer-events: none; transition: opacity .2s, transform .2s, visibility .2s; }
.toast.show { transform: translate(-50%, 0); opacity: 1; visibility: visible; }
.doq-modal-backdrop { position: fixed; inset: 0; z-index: 1200; padding: 20px; display: grid; place-items: center; background: rgb(15 10 40 / .5); }.doq-modal { width: min(440px, 100%); padding: 26px; border: 1px solid var(--line); border-radius: 20px; background: var(--surface); box-shadow: 0 30px 70px rgb(0 0 0 / .35); }.doq-modal header { margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; }.doq-modal h2 { margin: 0; font-size: 18px; }.doq-modal header button { width: 30px; height: 30px; border: 0; border-radius: 9px; color: var(--muted); background: var(--soft); cursor: pointer; }.doq-modal > p { margin: -12px 0 18px; color: var(--muted); font-size: 13px; }
.doq-modal-avatar { width: 64px; height: 64px; margin-bottom: 20px; border-radius: 20px; font-size: 24px; }.doq-modal label { display: grid; gap: 6px; margin-bottom: 14px; color: var(--sub); font-size: 13px; font-weight: 600; }.doq-modal input, .doq-modal select, .doq-modal textarea { width: 100%; border: 1.5px solid var(--line); border-radius: 12px; color: var(--ink); background: var(--soft); font-size: 14px; }.doq-modal input, .doq-modal select { height: 44px; padding: 0 14px; }.doq-modal textarea { min-height: 120px; padding: 12px 14px; resize: vertical; }.doq-modal footer { margin-top: 22px; display: flex; justify-content: flex-end; gap: 10px; }.doq-modal footer button { height: 44px; padding: 0 18px; border: 1px solid var(--line); border-radius: 12px; color: var(--sub); background: var(--surface); font-size: 14px; font-weight: 600; cursor: pointer; }.doq-modal footer button:last-child { padding: 0 22px; border: 0; color: #fff; background: var(--accent-gradient); }
@media (max-width: 620px) { .doq-profile { padding: 24px 18px 40px; }.doq-profile-card { align-items: flex-start; flex-wrap: wrap; }.doq-profile-card > button { width: 100%; }.doq-setting-row { align-items: flex-start; flex-direction: column; }.doq-mini-segment { width: 100%; }.doq-mini-segment button { flex: 1; padding-inline: 5px; }.doq-help-card { align-items: flex-start; flex-direction: column; }.doq-help-card button { width: 100%; } }
</style>
