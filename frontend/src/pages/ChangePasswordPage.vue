<!-- 인수인계용: 비밀번호 변경 화면 -->
<template>
  <div class="page">
    <div class="shell">
      <div class="header">
        <h1>비밀번호 변경</h1>
        <p>계정 보안을 위해 비밀번호를 변경합니다.</p>
      </div>

      <form class="form" @submit.prevent="submit">
        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
        
        <label class="field">
          <span class="label">현재 비밀번호</span>
          <input
            class="input"
            type="password"
            v-model="currentPassword"
            required
            placeholder="현재 사용 중인 비밀번호"
          />
        </label>

        <label class="field">
          <span class="label">새 비밀번호</span>
          <input
            class="input"
            type="password"
            v-model="newPassword"
            required
            placeholder="새로운 비밀번호"
          />
        </label>

        <label class="field">
          <span class="label">새 비밀번호 확인</span>
          <input
            class="input"
            type="password"
            v-model="confirmPassword"
            required
            placeholder="새로운 비밀번호 재입력"
          />
        </label>

        <div class="actions">
          <button class="btn btn-primary" type="submit" :disabled="loading">
            {{ loading ? "변경 중..." : "변경하기" }}
          </button>
          <button class="btn btn-ghost" type="button" @click="cancel">
            취소
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const loading = ref(false);
const errorMsg = ref("");

async function submit() {
  if (newPassword.value !== confirmPassword.value) {
    errorMsg.value = "새 비밀번호가 일치하지 않습니다.";
    return;
  }
  if (newPassword.value.length < 6) {
    errorMsg.value = "비밀번호는 6자 이상이어야 합니다.";
    return;
  }

  loading.value = true;
  errorMsg.value = "";

  try {
    await authStore.changePassword(currentPassword.value, newPassword.value);
    alert("비밀번호가 변경되었습니다.");
    router.push({ name: "profile" });
  } catch (error: any) {
    if (error.response?.data?.detail) {
      errorMsg.value = error.response.data.detail;
    } else {
      errorMsg.value = "비밀번호 변경에 실패했습니다. 현재 비밀번호를 확인해주세요.";
    }
  } finally {
    loading.value = false;
  }
}

function cancel() {
  router.back();
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: var(--bg);
  color: var(--ink);
}

.shell {
  width: min(480px, 100%);
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 32px;
  box-shadow: var(--shadow-lg);
}

.header {
  text-align: center;
  margin-bottom: 24px;
}
.header h1 {
  font-size: 24px;
  font-weight: 1000;
  margin: 0 0 8px;
}
.header p {
  color: var(--muted);
  font-size: 14px;
  margin: 0;
}

.form {
  display: grid;
  gap: 16px;
}

.field {
  display: grid;
  gap: 8px;
}
.label {
  font-size: 12px;
  font-weight: 900;
  color: var(--muted);
}
.input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--bg);
  color: var(--ink);
  outline: none;
  font-weight: 900;
}
.input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}

.error-msg {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
  padding: 10px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 800;
  text-align: center;
}

.actions {
  margin-top: 10px;
  display: grid;
  gap: 10px;
}

.btn {
  padding: 12px;
  border-radius: 12px;
  font-weight: 1000;
  cursor: pointer;
  border: 1px solid transparent;
}
.btn-primary {
  background: #2563eb;
  color: #fff;
}
.btn-primary:hover {
  background: #1d4ed8;
}
.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.btn-ghost {
  background: transparent;
  color: var(--muted);
  border: 1px solid var(--line);
}
.btn-ghost:hover {
  background: var(--bg);
  color: var(--ink);
}
</style>

