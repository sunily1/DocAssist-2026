<template>
  <div ref="viewerRef" class="docx-document-viewer">
    <div v-if="loading" class="docx-viewer-state">DOCX 문서를 불러오는 중입니다.</div>
    <div v-else-if="errorMessage" class="docx-viewer-state error">{{ errorMessage }}</div>
    <div ref="documentRef" class="docx-render-target" />
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import { renderAsync } from "docx-preview";

interface ChangeItem {
  id: string;
  from: string;
  to: string;
}

const props = defineProps<{
  blob: Blob | null;
  changes: ChangeItem[];
  original?: boolean;
  selectedId?: string | null;
}>();

const emit = defineEmits<{ (event: "select", id: string): void }>();
const viewerRef = ref<HTMLElement | null>(null);
const documentRef = ref<HTMLElement | null>(null);
const loading = ref(false);
const errorMessage = ref("");
let generation = 0;

function changeRanges(text: string) {
  const ranges: Array<{ start: number; end: number; id: string; label: string }> = [];
  const changes = [...props.changes].sort((a, b) => {
    const aText = props.original ? a.from : a.to;
    const bText = props.original ? b.from : b.to;
    return bText.length - aText.length;
  });

  for (const change of changes) {
    const phrase = String(props.original ? change.from : change.to).trim();
    if (!phrase) continue;
    let start = text.indexOf(phrase);
    let length = phrase.length;
    if (start < 0) {
      let prefix = phrase;
      while (prefix.length >= 2 && (start = text.indexOf(prefix)) < 0) prefix = prefix.slice(0, -1);
      if (start < 0 || prefix.length < 2) continue;
      length = text.slice(start).match(/^[^\s,.!?]+/)?.[0].length || prefix.length;
    }
    const next = { start, end: start + length, id: change.id, label: `${change.from} → ${change.to}` };
    if (!ranges.some((range) => next.start < range.end && next.end > range.start)) ranges.push(next);
  }
  return ranges.sort((a, b) => a.start - b.start);
}

function applyHighlights() {
  if (!documentRef.value) return;
  const walker = document.createTreeWalker(documentRef.value, NodeFilter.SHOW_TEXT);
  const nodes: Text[] = [];
  while (walker.nextNode()) {
    const node = walker.currentNode as Text;
    if (node.data.trim()) nodes.push(node);
  }

  for (const node of nodes) {
    const ranges = changeRanges(node.data);
    if (!ranges.length || !node.parentNode) continue;
    const fragment = document.createDocumentFragment();
    let cursor = 0;
    for (const range of ranges) {
      if (range.start > cursor) fragment.append(document.createTextNode(node.data.slice(cursor, range.start)));
      const mark = document.createElement("mark");
      mark.className = "docx-change-mark";
      mark.dataset.changeId = range.id;
      mark.title = range.label;
      mark.textContent = node.data.slice(range.start, range.end);
      mark.tabIndex = 0;
      const changeOrder = props.changes.findIndex((change) => change.id === range.id);
      mark.style.setProperty("--mark-delay", `${Math.min(Math.max(changeOrder, 0), 6) * 0.1}s`);
      if (props.original) mark.classList.add("original");
      mark.addEventListener("click", () => emit("select", range.id));
      fragment.append(mark);
      cursor = range.end;
    }
    if (cursor < node.data.length) fragment.append(document.createTextNode(node.data.slice(cursor)));
    node.parentNode.replaceChild(fragment, node);
  }
}

async function renderDocument() {
  const current = ++generation;
  errorMessage.value = "";
  if (!props.blob || !documentRef.value) return;
  loading.value = true;
  documentRef.value.replaceChildren();
  try {
    await renderAsync(props.blob, documentRef.value, undefined, {
      className: "docx",
      inWrapper: true,
      breakPages: true,
      ignoreWidth: false,
      ignoreHeight: false,
      ignoreFonts: false,
      useBase64URL: true,
    });
    if (current !== generation) return;
    applyHighlights();
  } catch (error) {
    console.error("DOCX render failed", error);
    errorMessage.value = "DOCX 화면을 표시하지 못했습니다.";
  } finally {
    if (current === generation) loading.value = false;
  }
}

function scrollToSelected(id: string | null | undefined) {
  if (!id || !viewerRef.value) return;
  const target = Array.from(viewerRef.value.querySelectorAll<HTMLElement>("[data-change-id]"))
    .find((element) => element.dataset.changeId === id);
  target?.scrollIntoView({ behavior: "smooth", block: "center" });
  viewerRef.value.querySelectorAll(".selected").forEach((element) => element.classList.remove("selected"));
  target?.classList.add("selected");
}

watch([() => props.blob, () => props.original, () => props.changes], () => nextTick(renderDocument), { immediate: true, deep: true });
watch(() => props.selectedId, (id) => nextTick(() => scrollToSelected(id)));
</script>

<style scoped>
.docx-document-viewer { min-height: 420px; overflow: auto; border-radius: 14px; background: #dedde4; }
.docx-render-target { min-height: 420px; }
.docx-viewer-state { min-height: 360px; display: grid; place-items: center; color: var(--muted); font-size: 13px; }.docx-viewer-state.error { color: #c0392b; }
.docx-document-viewer :deep(.docx-wrapper) { padding: 18px; background: transparent; }
.docx-document-viewer :deep(.docx-wrapper > section.docx) { margin: 0 auto 18px; box-shadow: 0 3px 14px rgb(32 26 58 / .16); }
.docx-document-viewer :deep(.docx-change-mark) { border-bottom: 3px solid #7658ff; border-radius: 2px; color: inherit; background: rgb(106 77 255 / .16); cursor: pointer; animation: docx-mark-in .55s ease var(--mark-delay, 0s) both; }
.docx-document-viewer :deep(.docx-change-mark.original) { animation-name: docx-mark-in-original; }
.docx-document-viewer :deep(.docx-change-mark:hover), .docx-document-viewer :deep(.docx-change-mark.selected) { background: rgb(106 77 255 / .28); box-shadow: 0 0 0 2px rgb(106 77 255 / .32); }
@keyframes docx-mark-in { from { opacity: 0; transform: translateY(40%); background-color: transparent; } to { opacity: 1; transform: translateY(0); background-color: rgb(106 77 255 / .16); } }
@keyframes docx-mark-in-original { from { opacity: 0; transform: translateY(-40%); background-color: transparent; } to { opacity: 1; transform: translateY(0); background-color: rgb(106 77 255 / .16); } }
[data-theme="dark"] .docx-document-viewer { background: #111019; }
@media (max-width: 620px) { .docx-document-viewer :deep(.docx-wrapper) { padding: 8px; }.docx-document-viewer :deep(.docx-wrapper > section.docx) { transform-origin: top left; } }
@media (prefers-reduced-motion: reduce) { .docx-document-viewer :deep(.docx-change-mark) { animation: none; } }
</style>
