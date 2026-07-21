<!-- 인수인계용: 전역 루트 컴포넌트(라우터 출력/전역 UI 상태 적용) -->
<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue';
import { useAuthStore } from './stores/auth';

const authStore = useAuthStore();

type FontSize = 'sm' | 'md' | 'lg' | 'custom';
type Theme = 'light' | 'dark';

const presetFontSize: Record<'sm' | 'md' | 'lg', number> = {
  sm: 15,
  md: 16.5,
  lg: 18.5,
};

function normalizeFontSize(size: unknown): FontSize {
  if (size === 'sm' || size === 'lg' || size === 'custom') return size;
  return 'md';
}

function normalizeCustomFontSize(size: unknown) {
  const value = Number(size);
  if (!Number.isFinite(value)) return 16;
  return Math.min(24, Math.max(14, Math.round(value * 2) / 2));
}

function applyFontSize(size: unknown, customSize?: unknown) {
  const mode = normalizeFontSize(size);
  const custom = normalizeCustomFontSize(customSize ?? localStorage.getItem('custom_font_size'));
  const baseSize = mode === 'custom' ? custom : presetFontSize[mode];

  document.documentElement.style.setProperty('--reader-font-size', `${baseSize}px`);
  document.documentElement.setAttribute('data-size', mode);
  document.documentElement.setAttribute('data-custom-font-size', String(custom));
  localStorage.setItem('font_size', mode);
  localStorage.setItem('custom_font_size', String(custom));
}

function applyTheme(theme: unknown) {
  const next: Theme = theme === 'dark' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', next);
  document.body.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
}

function applyUiSettings(ui: any) {
  if (!ui) return;
  if (ui.theme) applyTheme(ui.theme);
  if (ui.fontSize) applyFontSize(ui.fontSize, ui.customFontSize);
}

watch(
  () => authStore.user?.profile_settings?.ui,
  (ui) => applyUiSettings(ui),
  { immediate: true, deep: true }
);

onMounted(async () => {
  applyTheme(localStorage.getItem('theme') || 'light');
  applyFontSize(localStorage.getItem('font_size') || 'md', localStorage.getItem('custom_font_size') || 16);

  const localSettings = localStorage.getItem('profile_settings');
  if (localSettings) {
    try {
      const parsed = JSON.parse(localSettings);
      applyUiSettings(parsed.ui);
    } catch (e) {
      console.error('Failed to parse local profile settings', e);
    }
  }

  if (authStore.token && !authStore.user) {
    await authStore.fetchUser();
  }
});
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  width: 100%;
  min-height: 100vh;
  font-family: "IBM Plex Sans KR", system-ui, sans-serif;
}
</style>
