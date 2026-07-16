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
  sm: 14,
  md: 16,
  lg: 18,
};

function normalizeFontSize(size: unknown): FontSize {
  if (size === 'sm' || size === 'lg' || size === 'custom') return size;
  return 'md';
}

function normalizeCustomFontSize(size: unknown) {
  const value = Number(size);
  if (!Number.isFinite(value)) return 16;
  return Math.min(24, Math.max(12, Math.round(value)));
}

function applyFontVariables(baseSize: number) {
  const titleSize = Math.min(28, baseSize + 2);
  const bodySize = baseSize;
  const controlSize = baseSize;
  const smallSize = Math.max(10, baseSize - 2);

  document.documentElement.style.setProperty('--base-font-size', `${baseSize}px`);
  document.body.style.setProperty('--app-title-size', `${titleSize}px`);
  document.body.style.setProperty('--app-body-size', `${bodySize}px`);
  document.body.style.setProperty('--app-control-size', `${controlSize}px`);
  document.body.style.setProperty('--app-small-size', `${smallSize}px`);
}

function applyFontSize(size: unknown, customSize?: unknown) {
  const mode = normalizeFontSize(size);
  const custom = normalizeCustomFontSize(customSize ?? localStorage.getItem('custom_font_size'));
  const baseSize = mode === 'custom' ? custom : presetFontSize[mode];

  applyFontVariables(baseSize);
  document.documentElement.setAttribute('data-size', mode);
  document.documentElement.setAttribute('data-custom-font-size', String(custom));
  document.body.classList.remove('font-size-sm', 'font-size-md', 'font-size-lg', 'font-size-custom');
  document.body.classList.add(`font-size-${mode}`);
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

onMounted(() => {
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
