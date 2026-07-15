<!-- 인수인계용: 공통 레이아웃(사이드바/본문 레이아웃) -->
<template>
  <div class="app">
    <!-- 모바일 오버레이 -->
    <div class="overlay" v-if="sidebarOpen" @click="closeSidebar" />

    <!-- 사이드바 컴포넌트 -->
    <Sidebar :isOpen="sidebarOpen" @close="closeSidebar" />

    <!-- 본문 영역 -->
    <div class="main">
      <slot :toggleSidebar="toggleSidebar" :sidebarOpen="sidebarOpen"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue';
import Sidebar from './Sidebar.vue';
import userService from '../../api/user.service';

const sidebarOpen = ref(false);
let presenceTimer: number | undefined;

async function sendPresence() {
  if (!localStorage.getItem('token') || document.visibilityState === 'hidden') return;
  try {
    await userService.updatePresence();
  } catch (error) {
    console.error('Presence update failed', error);
  }
}

function handleVisibilityChange() {
  if (document.visibilityState === 'visible') sendPresence();
}

onMounted(() => {
  sendPresence();
  presenceTimer = window.setInterval(sendPresence, 60_000);
  document.addEventListener('visibilitychange', handleVisibilityChange);
});

onUnmounted(() => {
  if (presenceTimer) window.clearInterval(presenceTimer);
  document.removeEventListener('visibilitychange', handleVisibilityChange);
});

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value;
}

function closeSidebar() {
  sidebarOpen.value = false;
}
</script>

<style scoped>
.app {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Noto Sans KR", Arial;
  color: var(--ink);
  background: var(--bg);
}

.main {
  display: grid;
  grid-template-rows: 76px 1fr;
  min-height: 100vh;
  min-width: 0;
}

/* Mobile responsive */
@media (max-width: 820px) {
  .app {
    grid-template-columns: 1fr;
  }
  
  .overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: 900;
  }
}

/* Global variable support if needed */
:global(:root) {
  --b1: #1d4ed8;
  --b2: #0ea5e9;
  --ring: rgba(29, 78, 216, 0.18);
}
</style>
