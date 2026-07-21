<template>
  <aside class="sidebar" :class="{ open: isOpen }">
    <button class="brand" type="button" aria-label="홈으로 이동" @click="navigate('home')">
      <span class="brand-mark"><Search :size="19" :stroke-width="2.5" /></span>
      <span class="brand-name">DOQ</span>
    </button>

    <div class="nav-label">메뉴</div>
    <nav class="sb-nav" aria-label="주요 메뉴">
      <button class="sb-item" :class="{ active: currentRouteName === 'home' }" @click="navigate('home')">
        <House :size="19" /><span>홈</span>
      </button>
      <button class="sb-item" :class="{ active: currentRouteName === 'upload' }" @click="navigate('upload')">
        <Upload :size="19" /><span>업로드</span>
      </button>
      <button class="sb-item" :class="{ active: currentRouteName === 'drive' }" @click="navigate('drive')">
        <FolderOpen :size="19" /><span>드라이브</span>
      </button>
      <button class="sb-item" :class="{ active: currentRouteName === 'qa' }" @click="navigate('qa')">
        <MessageSquareText :size="19" /><span>Q&amp;A</span>
      </button>
      <button class="sb-item" :class="{ active: currentRouteName === 'terms' }" @click="navigate('terms')">
        <BookOpen :size="19" /><span>용어집</span>
      </button>
    </nav>

    <div class="sb-sep" />

    <nav class="sb-nav" aria-label="계정 메뉴">
      <button class="sb-item" :class="{ active: currentRouteName === 'profile' }" @click="navigate('profile')">
        <UserRound :size="19" /><span>프로필</span>
      </button>
      <button v-if="isAdmin" class="sb-item" :class="{ active: currentRouteName === 'admin' }" @click="navigate('admin')">
        <ShieldCheck :size="19" /><span>관리자</span>
      </button>
    </nav>

    <div class="account-card">
      <div class="account-row">
        <span class="avatar">{{ initial }}</span>
        <span class="account-copy">
          <strong>{{ userName }}</strong>
          <small>{{ userEmail }}</small>
        </span>
      </div>
      <button class="logout" type="button" @click="handleLogout">
        <LogOut :size="16" /><span>로그아웃</span>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import {
  BookOpen,
  FolderOpen,
  House,
  LogOut,
  MessageSquareText,
  Search,
  ShieldCheck,
  Upload,
  UserRound,
} from "@lucide/vue";
import { useAuthStore } from "../../stores/auth";

defineProps<{ isOpen: boolean }>();
const emit = defineEmits<{ (e: "close"): void }>();

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const currentRouteName = computed(() => route.name);
const isAdmin = computed(() => authStore.user?.role === "ADMIN");
const userName = computed(() => authStore.user?.name || "사용자");
const userEmail = computed(() => authStore.user?.email || "로그인 계정");
const initial = computed(() => userName.value.trim().charAt(0).toUpperCase() || "U");

function navigate(name: string) {
  emit("close");
  router.push({ name }).catch(() => {});
}

function handleLogout() {
  emit("close");
  authStore.logout();
  router.push({ name: "login" });
}
</script>

<style scoped>
.sidebar {
  width: 244px;
  height: 100vh;
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  color: var(--sidebar-fg);
  background: var(--sidebar-bg);
  border-right: 1px solid var(--line);
}

.brand {
  width: 100%;
  margin: 0;
  padding: 6px 8px 22px;
  display: inline-flex;
  align-items: center;
  gap: 11px;
  border: 0;
  color: var(--ink);
  background: transparent;
  cursor: pointer;
}

.brand-mark {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: #fff;
  background: var(--accent-gradient);
  box-shadow: 0 7px 18px rgb(106 77 255 / 0.28);
}

.brand-name {
  color: var(--sidebar-fg);
  font-family: "Space Grotesk", "IBM Plex Sans KR", sans-serif;
  font-size: 21px;
  font-weight: 700;
  letter-spacing: .02em;
}

.nav-label {
  padding: 0 10px 8px;
  color: var(--sidebar-muted);
  font-size: 11px;
  font-weight: 600;
}

.sb-nav { display: grid; gap: 3px; }

.sb-item {
  width: 100%;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 11px;
  border: 0;
  border-radius: 12px;
  color: var(--sidebar-fg);
  background: transparent;
  font-size: 13.5px;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  transition: color .18s ease, background .18s ease, border-color .18s ease;
}

.sb-item:hover { background: #f4f2fd; }
[data-theme="dark"] .sb-item:hover { background: rgb(255 255 255 / .06); }
.sb-item.active {
  color: var(--accent-strong);
  font-weight: 600;
  background: var(--accent-soft);
}

.sb-sep { height: 1px; margin: 14px 6px; background: var(--line); }

.account-card {
  margin-top: auto;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 15px;
  background: var(--soft);
}

.account-row { display: flex; align-items: center; gap: 10px; min-width: 0; }
.avatar {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  flex: none;
  border-radius: 11px;
  color: #fff;
  background: linear-gradient(135deg, #ffb86b, #ff7eb3);
  font-size: 14px;
  font-weight: 700;
}
.account-copy { min-width: 0; display: grid; }
.account-copy strong, .account-copy small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.account-copy strong { color: var(--ink); font-size: 13px; font-weight: 600; }
.account-copy small { margin-top: 2px; color: var(--muted); font-size: 11px; }
.logout {
  width: 100%;
  min-height: 36px;
  margin-top: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border: 1px solid var(--field-border);
  border-radius: 10px;
  color: var(--muted);
  background: var(--card);
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
}
.logout:hover { color: var(--ink); border-color: var(--accent-border); }

@media (max-width: 820px) {
  .sidebar {
    width: 66px;
    padding-left: 10px;
    padding-right: 10px;
    transform: none;
    box-shadow: none;
  }
  .brand { width: 100%; margin-left: 0; margin-right: 0; justify-content: center; }
  .brand-name, .nav-label, .sb-item span, .account-card { display: none; }
  .sb-item { justify-content: center; padding-left: 0; padding-right: 0; gap: 0; }
}
</style>
