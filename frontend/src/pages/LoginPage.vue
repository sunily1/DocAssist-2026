<template>
  <main class="login-page">
    <section class="brand-panel" aria-label="DOQ 소개">
      <div class="brand-lockup">
        <span class="brand-icon"><Search :size="21" :stroke-width="2.4" /></span>
        <span>DOQ</span>
      </div>

      <div class="brand-copy">
        <p>문서 이해 보조 서비스</p>
        <h1>어려운 문서를<br />가장 쉬운 말로.</h1>
        <span>복잡한 계약서·공문서를 올리면 어려운 표현을 쉬운말로 바꾸고, 무엇이 어떻게 달라졌는지 한눈에 보여드려요.</span>
      </div>

      <div class="feature-list" aria-label="주요 기능">
        <span>쉬운말 변환</span>
        <span>문단 요약</span>
        <span>문서 Q&amp;A</span>
      </div>
    </section>

    <section class="form-panel">
      <div class="form-shell">
        <h2>다시 오신 걸 환영해요</h2>
        <p class="form-desc">계정으로 로그인하고 문서를 쉬운말로 바꿔보세요.</p>

        <form class="login-form" @submit.prevent="login">
          <div v-if="errorMsg" class="error-msg" role="alert">{{ errorMsg }}</div>

          <label class="field">
            <span>이메일</span>
            <input v-model="email" type="text" placeholder="you@example.com" autocomplete="username" required />
          </label>

          <label class="field">
            <span>비밀번호</span>
            <span class="password-field">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="비밀번호를 입력하세요"
                autocomplete="current-password"
                required
              />
              <button type="button" :aria-label="showPassword ? '비밀번호 숨기기' : '비밀번호 보기'" @click="showPassword = !showPassword">
                <EyeOff v-if="showPassword" :size="18" />
                <Eye v-else :size="18" />
              </button>
            </span>
          </label>

          <div class="form-options">
            <label><input v-model="rememberMe" type="checkbox" /> 로그인 유지</label>
            <button type="button" @click="goForgot">비밀번호 찾기</button>
          </div>

          <button class="submit" type="submit" :disabled="loading">
            <LoaderCircle v-if="loading" class="spinner" :size="18" />
            <span>{{ loading ? "로그인 중" : "로그인" }}</span>
          </button>
        </form>

        <p class="signup-copy">아직 계정이 없으신가요? <button type="button" @click="goSignup">회원가입</button></p>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { Eye, EyeOff, LoaderCircle, Search } from "@lucide/vue";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();
const email = ref("");
const password = ref("");
const rememberMe = ref(false);
const showPassword = ref(false);
const loading = ref(false);
const errorMsg = ref("");

async function login() {
  loading.value = true;
  errorMsg.value = "";
  try {
    await authStore.login(email.value, password.value, rememberMe.value);
    router.push({ name: "home" });
  } catch (error: any) {
    errorMsg.value = error.response?.data?.detail || "로그인에 실패했습니다. 이메일과 비밀번호를 확인해 주세요.";
  } finally {
    loading.value = false;
  }
}

function goSignup() { router.push({ name: "signup" }); }
function goForgot() { router.push({ name: "forgotPassword" }); }
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.05fr .95fr;
  color: var(--ink);
  background: var(--card);
}
.brand-panel {
  min-height: 100vh;
  padding: 54px 60px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: #2f2452;
  background: linear-gradient(150deg, #e3d0fd 0%, #d3c0fb 55%, #efe3fe 100%);
}
.brand-lockup { display: flex; align-items: center; gap: 12px; color: #2f2452; font-family: "Space Grotesk", sans-serif; font-size: 24px; font-weight: 700; }
.brand-icon { width: 40px; height: 40px; display: grid; place-items: center; border-radius: 13px; color: #fff; background: var(--accent-gradient); box-shadow: 0 8px 18px rgb(106 77 255 / .3); }
.brand-copy { max-width: 500px; }
.brand-copy p { margin: 0 0 16px; color: #5638e0; font-size: 14px; font-weight: 600; }
.brand-copy h1 { margin: 0; color: #2b2350; font-size: 44px; line-height: 1.25; font-weight: 700; }
.brand-copy > span { display: block; max-width: 400px; margin-top: 20px; color: #5c5578; font-size: 16px; line-height: 1.7; }
.feature-list { display: flex; flex-wrap: wrap; gap: 10px; }
.feature-list span { padding: 8px 14px; border: 1px solid rgb(255 255 255 / .9); border-radius: 999px; color: #5638e0; background: rgb(255 255 255 / .7); font-size: 13px; font-weight: 600; }
.form-panel { min-height: 100vh; padding: 40px; display: grid; place-items: center; background: var(--card); }
.form-shell { width: min(380px, 100%); }
.form-shell h2 { margin: 0; color: var(--ink); font-size: 26px; font-weight: 700; }
.form-desc { margin: 8px 0 30px; color: var(--muted); font-size: 14px; }
.login-form { display: grid; gap: 18px; }
.field { display: grid; gap: 7px; }
.field > span:first-child { color: var(--sub); font-size: 13px; font-weight: 600; }
.field input { width: 100%; height: 48px; padding: 0 15px; border: 1.5px solid var(--field-border); border-radius: 13px; outline: none; color: var(--field-text); background: var(--field-bg); }
.field input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.password-field { position: relative; display: block; }
.password-field input { padding-right: 48px; }
.password-field button { position: absolute; top: 50%; right: 10px; width: 34px; height: 34px; display: grid; place-items: center; transform: translateY(-50%); border: 0; border-radius: 9px; color: var(--muted); background: transparent; cursor: pointer; }
.password-field button:hover { color: var(--ink); background: var(--soft); }
.form-options { margin-top: -2px; display: flex; align-items: center; justify-content: space-between; color: var(--muted); font-size: 13px; }
.form-options label { display: inline-flex; align-items: center; gap: 7px; }
.form-options input { accent-color: var(--accent); }
.form-options button, .signup-copy button { padding: 0; border: 0; color: var(--accent); background: transparent; font-weight: 600; cursor: pointer; }
.submit { width: 100%; height: 50px; display: inline-flex; align-items: center; justify-content: center; gap: 9px; border: 0; border-radius: 13px; color: #fff; background: var(--accent-gradient); box-shadow: 0 9px 22px rgb(106 77 255 / .26); font-size: 15px; font-weight: 600; cursor: pointer; }
.submit:disabled { opacity: .7; cursor: wait; }
.spinner { animation: spin .8s linear infinite; }
.error-msg { padding: 11px 13px; border: 1px solid rgb(220 75 103 / .22); border-radius: 11px; color: #b92e4b; background: rgb(220 75 103 / .08); font-size: 13px; }
.signup-copy { margin: 26px 0 0; color: var(--muted); text-align: center; font-size: 13px; }
.or { margin: 22px 0; display: flex; align-items: center; gap: 12px; color: #a9a7b6; font-size: 12px; }
.or span { height: 1px; flex: 1; background: #eceaf2; }
.google { width: 100%; height: 48px; border: 1.5px solid var(--field-border); border-radius: 13px; color: var(--ink); background: var(--surface); font-size: 14px; font-weight: 600; cursor: pointer; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 820px) {
  .login-page { grid-template-columns: 1fr; }
  .brand-panel { min-height: 260px; padding: 28px 24px; }
  .brand-copy { margin: 42px 0 24px; }
  .brand-copy h1 { font-size: 34px; }
  .brand-copy > span, .feature-list { display: none; }
  .form-panel { min-height: auto; padding: 44px 24px 60px; }
}
</style>
