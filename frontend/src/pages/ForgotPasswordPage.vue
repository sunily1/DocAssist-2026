<!-- 인수인계용: 비밀번호 재설정 안내/요청 화면(현재 Mock) -->
<template>
  <div class="wrap">
    <div class="shell">
      <!-- 왼쪽 비주얼 -->
      <section class="left">
        <div class="brand">
          <img
            class="logo"
            src="/logo.png"
            alt="DoQ"
            @click="goHome"
            role="button"
            tabindex="0"
            @keydown.enter="goHome"
          />
          <div class="brand-text">
            <div class="brand-title">DoQ</div>
            <div class="brand-sub">AI 기반 개인 문서 이해 보조 시스템</div>
          </div>
        </div>

        <div class="hero">
          <h1>비밀번호 재설정</h1>
          <p>
            가입한 이메일을 입력하면<br />
            재설정 링크를 보내드릴게요.
          </p>
        </div>

        <div class="blob"></div>
      </section>

      <!-- 오른쪽 폼 -->
      <section class="right">
        <div class="card">
          <div class="card-head">
            <h2>Forgot Password</h2>
            <p class="muted">이메일로 재설정 링크를 전송합니다.</p>
          </div>

          <form class="form" @submit.prevent="submit">
            <label class="field">
              <span class="label">Email</span>
              <input
                v-model="email"
                class="input"
                type="email"
                placeholder="you@example.com"
                autocomplete="email"
                required
              />
            </label>

            <button class="btn btn-primary" type="submit" :disabled="loading">
              {{ loading ? "Sending..." : "재설정 링크 보내기" }}
            </button>

            <div v-if="info" class="info">
              {{ info }}
            </div>

            <div class="row">
              <button class="link" type="button" @click="goLogin">로그인</button>
              <span class="dot">·</span>
              <button class="link" type="button" @click="goSignup">회원가입</button>
            </div>
          </form>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

const email = ref("");
const loading = ref(false);
const info = ref("");

function goHome() {
  router.push({ name: "home" }).catch(() => {});
}
function goLogin() {
  router.push({ name: "login" }).catch(() => {});
}
function goSignup() {
  router.push({ name: "signup" }).catch(() => {});
}

async function submit() {
  info.value = "";
  loading.value = true;

  try {
    // 실제로는 FastAPI 호출로 교체
    // await fetch("/api/auth/forgot-password", { method:"POST", body: JSON.stringify({ email: email.value }) })
    await new Promise((r) => setTimeout(r, 700));

    info.value = "재설정 링크를 전송했어요. 메일함을 확인해 주세요.";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.wrap {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: radial-gradient(circle at 20% 10%, rgba(37,99,235,0.16), transparent 45%),
              radial-gradient(circle at 70% 40%, rgba(34,211,238,0.12), transparent 50%),
              #f6f7fb;
  padding: 24px;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Noto Sans KR", Arial;
  color: #0f172a;
}

.shell {
  width: min(1040px, 100%);
  min-height: 620px;
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  border-radius: 22px;
  overflow: hidden;
  box-shadow: 0 26px 60px rgba(15, 23, 42, 0.14);
  border: 1px solid rgba(15,23,42,0.08);
  background: #fff;
}

/* Left */
.left {
  position: relative;
  padding: 28px;
  background: linear-gradient(135deg, rgba(37,99,235,0.95), rgba(34,211,238,0.85));
  color: #fff;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}
.logo {
  width: 42px;
  height: 42px;
  object-fit: contain;
  background: rgba(255,255,255,0.18);
  border-radius: 12px;
  padding: 6px;
  cursor: pointer;
}
.brand-title { font-weight: 1000; font-size: 16px; }
.brand-sub { opacity: 0.88; font-weight: 800; font-size: 12px; margin-top: 2px; }

.hero {
  margin-top: 64px;
  max-width: 360px;
}
.hero h1 {
  margin: 0;
  font-size: 44px;
  line-height: 1.05;
  letter-spacing: -0.6px;
  font-weight: 1100;
}
.hero p {
  margin: 16px 0 0;
  opacity: 0.92;
  font-weight: 800;
  line-height: 1.6;
}

.blob {
  position: absolute;
  inset: auto -90px -120px auto;
  width: 340px;
  height: 340px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.35), transparent 55%);
  filter: blur(2px);
  opacity: 0.9;
}

/* Right */
.right {
  display: grid;
  place-items: center;
  padding: 26px;
  background: #ffffff;
}

.card {
  width: min(420px, 100%);
  border-radius: 18px;
  padding: 20px;
}

.card-head h2 {
  margin: 0;
  font-size: 26px;
  font-weight: 1100;
}
.muted { color: #64748b; font-weight: 800; }
.card-head p { margin: 8px 0 0; }

.form {
  margin-top: 18px;
  display: grid;
  gap: 14px;
}

.field { display: grid; gap: 8px; }
.label { font-size: 12px; color: #94a3b8; font-weight: 1000; }

.input {
  width: 100%;
  border: 1px solid rgba(15,23,42,0.12);
  border-radius: 12px;
  padding: 12px 12px;
  outline: none;
  font-weight: 900;
}
.input:focus {
  border-color: rgba(37,99,235,0.4);
  box-shadow: 0 0 0 3px rgba(37,99,235,0.16);
}

.btn {
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 12px 14px;
  font-weight: 1100;
  cursor: pointer;
}
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-primary {
  color: #fff;
  background: linear-gradient(90deg, #2563eb, #22d3ee);
  box-shadow: 0 18px 30px rgba(34,211,238,0.18);
}
.btn-primary:hover { filter: brightness(0.98); }

.info {
  border: 1px solid rgba(37,99,235,0.18);
  background: rgba(37,99,235,0.08);
  color: #1d4ed8;
  padding: 10px 12px;
  border-radius: 12px;
  font-weight: 1000;
  font-size: 12px;
}

.row {
  display: flex;
  justify-content: center;
  gap: 10px;
  align-items: center;
  margin-top: 6px;
}

.link {
  border: none;
  background: transparent;
  color: #2563eb;
  font-weight: 1100;
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 10px;
}
.link:hover { background: rgba(37,99,235,0.08); }
.dot { color: #cbd5e1; }

/* Responsive */
@media (max-width: 920px) {
  .shell { grid-template-columns: 1fr; min-height: auto; }
  .left { padding: 24px; }
  .hero { margin-top: 36px; }
  .hero h1 { font-size: 34px; }
  .blob { display: none; }
}
</style>







