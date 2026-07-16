<!-- 인수인계용: 비밀번호 재설정 입력 화면(현재 Mock) -->
<template>
    <div class="page">
      <div class="shell">
        <!-- 왼쪽 영역 -->
        <section class="left">
          <div class="left-top">
            <img class="logo" src="/logo.png" alt="DoQ" />
          </div>
  
          <div class="left-center">
            <div class="welcome">Set New<br />Password</div>
            <div class="left-sub">안전한 새 비밀번호로 변경하세요</div>
          </div>
  
          <div class="left-bottom">
            <div class="mini">© {{ new Date().getFullYear() }} DoQ</div>
          </div>
        </section>
  
        <!-- 오른쪽 영역 -->
        <section class="right">
          <h1 class="title">Reset Password</h1>
          <p class="desc">
            새 비밀번호를 입력하세요.
            <span v-if="token" class="token-pill">token OK</span>
            <span v-else class="token-pill warn">token missing</span>
          </p>
  
          <form class="form" @submit.prevent="onSubmit">
            <label class="field">
              <span class="label">New Password</span>
              <div class="pw-wrap">
                <input
                  class="input"
                  :type="showNew ? 'text' : 'password'"
                  placeholder="8+ characters"
                  v-model="newPassword"
                  autocomplete="new-password"
                  minlength="8"
                  required
                />
                <button class="eye" type="button" @click="showNew = !showNew">
                  {{ showNew ? "Hide" : "Show" }}
                </button>
              </div>
            </label>
  
            <label class="field">
              <span class="label">Confirm Password</span>
              <div class="pw-wrap">
                <input
                  class="input"
                  :type="showConfirm ? 'text' : 'password'"
                  placeholder="repeat password"
                  v-model="confirm"
                  autocomplete="new-password"
                  minlength="8"
                  required
                />
                <button class="eye" type="button" @click="showConfirm = !showConfirm">
                  {{ showConfirm ? "Hide" : "Show" }}
                </button>
              </div>
            </label>
  
            <button class="btn" type="submit" :disabled="loading || !token">
              {{ loading ? "Updating..." : "Update password" }}
            </button>
  
            <div v-if="success" class="success">
              ✅ 비밀번호가 변경되었어요. 이제 로그인 해주세요.
            </div>
  
            <div v-if="error" class="error">{{ error }}</div>
  
            <div class="footer">
              <button class="link strong" type="button" @click="goLogin">← Back to Login</button>
            </div>
          </form>
        </section>
      </div>
  
      <div class="bg" />
    </div>
  </template>
  
  <script setup lang="ts">
  import { computed, ref } from "vue";
  import { useRoute, useRouter } from "vue-router";
  
  const router = useRouter();
  const route = useRoute();
  
  // 예: /reset-password?token=xxxxx
  const token = computed(() => String(route.query.token ?? "").trim());
  
  const newPassword = ref("");
  const confirm = ref("");
  
  const showNew = ref(false);
  const showConfirm = ref(false);
  
  const loading = ref(false);
  const success = ref(false);
  const error = ref("");
  
  function goLogin() {
    router.push({ name: "login" }).catch(() => {});
  }
  
  async function onSubmit() {
    error.value = "";
    success.value = false;
    loading.value = true;
  
    try {
      if (!token.value) throw new Error("재설정 토큰이 없어요. 링크를 다시 확인해주세요.");
      if (newPassword.value.length < 8) throw new Error("비밀번호는 8자 이상이어야 해요.");
      if (newPassword.value !== confirm.value) throw new Error("비밀번호가 서로 달라요.");
  
      // 할일: FastAPI 연결
      // POST /auth/reset-password { token: token.value, password: newPassword.value }
  
      success.value = true;
  
      // 사용자 경험(UX): 성공 후 1.2초 뒤 로그인 화면으로
      setTimeout(() => goLogin(), 1200);
    } catch (e: any) {
      error.value = e?.message ?? "비밀번호 변경에 실패했어요.";
    } finally {
      loading.value = false;
    }
  }
  </script>
  
  <style scoped>
  :root {
    --b1: var(--accent);
    --b2: var(--accent-2);
    --ink: #111827;
    --muted: #6b7280;
    --line: #e5e7eb;
    --ring: var(--accent-soft);
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
  }
  .left-center { margin-top: 68px; }
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
  .desc {
    margin: 10px 0 22px;
    color: var(--muted);
    font-weight: 700;
    font-size: 13px;
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
  }
  .token-pill{
    font-size: 11px;
    padding: 2px 10px;
    border-radius: 999px;
    border: 1px solid #bfdbfe;
    background: #eff6ff;
    color: var(--accent-strong);
    font-weight: 900;
  }
  .token-pill.warn{
    border-color: #fecaca;
    background: #fef2f2;
    color: #991b1b;
  }
  
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
    color: var(--ink);
    background: #fff;
  }
  .input:focus { border-color: rgba(29,78,216,0.35); box-shadow: 0 0 0 3px var(--ring); }
  
  .pw-wrap { position: relative; }
  .pw-wrap .input { padding-right: 70px; }
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
  .btn:disabled { opacity: 0.65; cursor: not-allowed; }
  
  .success {
    border: 1px solid #bbf7d0;
    background: #ecfdf5;
    color: #065f46;
    border-radius: 12px;
    padding: 10px 12px;
    font-weight: 900;
    font-size: 12px;
  }
  
  .error {
    border: 1px solid #fecaca;
    background: #fef2f2;
    color: #991b1b;
    border-radius: 12px;
    padding: 10px 12px;
    font-weight: 900;
    font-size: 12px;
  }
  
  .footer { margin-top: 10px; display: flex; justify-content: center; }
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
  .link:hover { background: var(--accent-soft); }
  .link.strong { padding: 0 6px; }
  
  @media (max-width: 900px) {
    .shell { grid-template-columns: 1fr; }
    .left-center { margin-top: 26px; }
    .welcome { font-size: 44px; }
    .right { padding: 28px 22px 22px; }
  }
  </style>
  




