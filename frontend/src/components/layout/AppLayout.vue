<!-- 인수인계용: 공통 레이아웃(사이드바/본문 레이아웃) -->
<template>
  <div class="app">
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
  grid-template-columns: 244px minmax(0, 1fr);
  font-family: "IBM Plex Sans KR", system-ui, sans-serif;
  color: var(--ink);
  background: var(--bg);
}

.main {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-height: 100vh;
  min-width: 0;
}

/* Mobile responsive */
@media (max-width: 820px) {
  .app {
    grid-template-columns: 66px minmax(0, 1fr);
  }
}

</style>
