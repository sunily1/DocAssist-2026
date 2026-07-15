<!-- 인수인계용: 로그인 화면 -->
<template>
  <div class="page">
    <div class="shell">
      <!-- 왼쪽 영역 -->
      <section class="left">
        <div class="left-top">
          <!-- ✅ 로고 클릭 시 홈으로 -->
          <img
            class="logo"
            src="/logo.png"
            alt="DoQ"
            @click="goHome"
            role="button"
            tabindex="0"
            @keydown.enter="goHome"
          />
        </div>

        <div class="left-center">
          <div class="welcome">Welcome<br />Back</div>
          <div class="left-sub">AI 문서 이해 보조를 계속해요</div>
        </div>

        <div class="left-bottom">
          <div class="mini">© {{ new Date().getFullYear() }} DoQ</div>
        </div>
      </section>

      <!-- 오른쪽 영역 -->
      <section class="right">
        <h1 class="title">Login</h1>
        <p class="desc">이메일과 비밀번호로 로그인하세요.</p>

        <form class="form" @submit.prevent="login">
          <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
          <label class="field">
            <span class="label">Email / ID</span>
            <input
              class="input"
              type="text"
              placeholder="아이디 또는 이메일"
              v-model="email"
              autocomplete="username"
              required
            />
          </label>

          <label class="field">
            <span class="label">Password</span>
            <div class="pw-wrap">
              <input
                class="input"
                :type="showPassword ? 'text' : 'password'"
                placeholder="비밀번호"
                v-model="password"
                autocomplete="current-password"
                required
              />
              <button class="eye" type="button" @click="showPassword = !showPassword">
                {{ showPassword ? "숨기기" : "보기" }}
              </button>
            </div>
          </label>

          <button class="btn" type="submit">
            로그인
          </button>

          <div class="footer">
            <button class="link" type="button" @click="goForgot">비밀번호 찾기</button>
            <span class="muted">·</span>
            <span class="muted">계정이 없으신가요?</span>
            <button class="link strong" type="button" @click="goSignup">Signup</button>
          </div>
        </form>
      </section>
    </div>

    <div class="bg" />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const email = ref("");
const password = ref("");
const showPassword = ref(false);
const loading = ref(false);
const errorMsg = ref("");

/**
 * ✅ 로그인 (Backend 연동)
 */
async function login() {
  loading.value = true;
  errorMsg.value = "";
  try {
    await authStore.login(email.value, password.value);
    router.push({ name: "home" });
  } catch (error: any) {
    if (error.response?.data?.detail) {
      errorMsg.value = error.response.data.detail;
    } else {
      errorMsg.value = "로그인에 실패했습니다. 이메일과 비밀번호를 확인해주세요.";
    }
  } finally {
    loading.value = false;
  }
}

function goSignup() {
  router.push({ name: "signup" });
}

function goForgot() {
  router.push({ name: "forgotPassword" });
}

function goHome() {
  router.push({ name: "home" });
}
</script>

<style scoped>
:root {
  --b1: #1d4ed8;
  --b2: #0ea5e9;
  --ink: #111827;
  --muted: #6b7280;
  --line: #e5e7eb;
  --ring: rgba(29, 78, 216, 0.18);
}

.page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: #f3f7ff;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Noto Sans KR", Arial;
  position: relative;
  overflow: hidden;
}

.bg {
  position: absolute;
  inset: -40%;
  background:
    radial-gradient(circle at 20% 20%, rgba(14,165,233,0.22), transparent 45%),
    radial-gradient(circle at 80% 60%, rgba(29,78,216,0.18), transparent 45%),
    radial-gradient(circle at 50% 90%, rgba(59,130,246,0.14), transparent 40%);
  filter: blur(20px);
  z-index: 0;
}

.shell {
  width: min(980px, 100%);
  min-height: 520px;
  background: #fff;
  border-radius: 22px;
  box-shadow: 0 24px 70px rgba(17, 24, 39, 0.18);
  overflow: hidden;
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  z-index: 1;
}

/* left */
.left {
  position: relative;
  color: #fff;
  padding: 26px 26px 18px;
  background: linear-gradient(135deg, rgba(29,78,216,0.95), rgba(14,165,233,0.90));
  display: flex;
  flex-direction: column;
}
.left::before {
  content: "";
  position: absolute;
  inset: -20%;
  background:
    radial-gradient(circle at 30% 35%, rgba(255,255,255,0.22), transparent 45%),
    radial-gradient(circle at 70% 65%, rgba(255,255,255,0.12), transparent 45%);
  transform: rotate(10deg);
  opacity: 0.9;
}
.left-top, .left-center, .left-bottom { position: relative; z-index: 1; }
.left-top { display: flex; align-items: center; }
.logo {
  width: 34px; height: 34px; object-fit: contain; border-radius: 10px;
  filter: drop-shadow(0 10px 18px rgba(0,0,0,0.22));
  cursor: pointer;
}
.left-center { margin-top: 68px; flex: 1; }
.welcome {
  font-weight: 1000;
  font-size: 56px;
  line-height: 1.02;
  letter-spacing: -0.8px;
  text-shadow: 0 18px 30px rgba(0, 0, 0, 0.18);
}
.left-sub { margin-top: 16px; font-weight: 800; opacity: 0.9; }
.left-bottom { margin-top: auto; padding-top: 80px; }
.mini { font-weight: 800; opacity: 0.7; font-size: 12px; }

/* right */
.right { padding: 46px 46px 34px; display: grid; align-content: start; }
.title { margin: 0; font-size: 32px; font-weight: 1000; color: var(--ink); }
.desc { margin: 10px 0 22px; color: var(--muted); font-weight: 700; font-size: 13px; }

.form { display: grid; gap: 16px; }
.field { display: grid; gap: 8px; }
.label { font-size: 12px; color: #9ca3af; font-weight: 900; }

.input {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 12px 12px;
  outline: none;
  font-weight: 800;
  color: #111827;
  background: #fff;
  caret-color: #111827;
}
.input::placeholder { color: #9ca3af; }
.input:focus { border-color: rgba(29,78,216,0.35); box-shadow: 0 0 0 3px var(--ring); }

.error-msg {
  color: #ef4444;
  font-size: 13px;
  font-weight: 700;
  text-align: center;
  background: rgba(239, 68, 68, 0.1);
  padding: 10px;
  border-radius: 8px;
}

.pw-wrap { position: relative; }
.pw-wrap .input { padding-right: 76px; }
.eye {
  position: absolute;
  top: 50%;
  right: 10px;
  transform: translateY(-50%);
  height: 32px;
  padding: 0 10px;
  border-radius: 10px;
  border: 1px solid var(--line);
  background: #fff;
  cursor: pointer;
  font-weight: 900;
  font-size: 12px;
  color: #374151;
}
.eye:hover { background: #f9fafb; }

.btn {
  margin-top: 6px;
  height: 46px;
  border: none;
  border-radius: 10px;
  font-weight: 1000;
  color: #fff;
  cursor: pointer;
  background: linear-gradient(90deg, var(--b1), var(--b2));
  box-shadow: 0 14px 24px rgba(14,165,233,0.20);
}
.btn:hover { filter: brightness(0.98); }
.btn:disabled { opacity: 0.7; cursor: not-allowed; }

.link {
  border: none;
  background: transparent;
  color: var(--b1);
  font-weight: 900;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 8px;
  font-size: 12px;
}
.link:hover { background: rgba(29, 78, 216, 0.08); }
.link.strong { padding: 0 6px; }

.footer { 
  margin-top: 10px; 
  display: flex; 
  gap: 6px; 
  align-items: center; 
  justify-content: center; 
  flex-wrap: wrap;
}
.muted { color: #9ca3af; font-weight: 800; font-size: 12px; }

:global([data-theme="dark"]) .page { background: var(--bg); }
:global([data-theme="dark"]) .shell,
:global([data-theme="dark"]) .right {
  background: var(--card);
  color: var(--ink);
}
:global([data-theme="dark"]) .title { color: var(--ink); }
:global([data-theme="dark"]) .desc,
:global([data-theme="dark"]) .label,
:global([data-theme="dark"]) .muted {
  color: var(--muted);
}
:global([data-theme="dark"]) .input {
  background: var(--field-bg);
  border-color: var(--field-border);
  color: var(--field-text);
  caret-color: var(--field-text);
}
:global([data-theme="dark"]) .input::placeholder { color: var(--muted); }
:global([data-theme="dark"]) .eye {
  background: var(--button-bg);
  border-color: var(--field-border);
  color: var(--button-text);
}
:global([data-theme="dark"]) .eye:hover { background: var(--button-hover); }

@media (max-width: 900px) {
  .shell { grid-template-columns: 1fr; }
  .left-center { margin-top: 26px; }
  .welcome { font-size: 44px; }
  .right { padding: 28px 22px 22px; }
}
</style>







