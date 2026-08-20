<template>
  <div ref="viewerRef" class="pdf-document-viewer">
    <div v-if="loading" class="pdf-viewer-state">PDF 페이지를 불러오는 중입니다.</div>
    <div v-else-if="errorMessage" class="pdf-viewer-state error">{{ errorMessage }}</div>
    <div v-else class="pdf-pages">
      <section
        v-for="page in pages"
        :key="page.number"
        class="pdf-page-shell"
        :style="{ width: `${page.width}px`, aspectRatio: `${page.width} / ${page.height}` }"
      >
        <canvas :ref="(element) => setCanvasRef(page.number, element)" :aria-label="`PDF ${page.number}페이지`" />
        <button
          v-for="(annotation, annotationIndex) in annotationsForPage(page.number)"
          :key="`${annotation.id}-${annotation.segment}`"
          type="button"
          class="pdf-change-mark"
          :class="{ selected: selectedId === annotation.id, approximate: annotation.approximate, original }"
          :data-annotation-id="annotation.id"
          :style="annotationStyle(annotation, annotationIndex)"
          :title="`${annotation.original} → ${annotation.easy}`"
          :aria-label="`${annotation.original}을 ${annotation.easy}로 변경`"
          @click="$emit('select', annotation.id)"
        >
          <span class="pdf-change-tooltip">{{ annotation.original }} → {{ annotation.easy }}</span>
        </button>
        <span class="pdf-page-number">{{ page.number }}</span>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from "vue";
import { GlobalWorkerOptions, getDocument, type PDFDocumentProxy, type PDFPageProxy } from "pdfjs-dist";
import workerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";

GlobalWorkerOptions.workerSrc = workerUrl;

const pdfAssetBaseUrl = new URL(import.meta.env.BASE_URL, window.location.origin);
const cMapUrl = new URL("pdfjs/cmaps/", pdfAssetBaseUrl).toString();
const standardFontDataUrl = new URL("pdfjs/standard_fonts/", pdfAssetBaseUrl).toString();

interface PdfAnnotation {
  id: string;
  segment: number;
  page: number;
  page_width: number;
  page_height: number;
  x: number;
  y: number;
  width: number;
  height: number;
  original: string;
  easy: string;
  definition: string;
  approximate?: boolean;
}

interface PageMeta {
  number: number;
  width: number;
  height: number;
}

const props = defineProps<{
  blob: Blob | null;
  annotations: PdfAnnotation[];
  original?: boolean;
  selectedId?: string | null;
  zoom?: number;
}>();

defineEmits<{ (event: "select", id: string): void }>();

const viewerRef = ref<HTMLElement | null>(null);
const pages = ref<PageMeta[]>([]);
const loading = ref(false);
const errorMessage = ref("");
const canvasRefs = new Map<number, HTMLCanvasElement>();
let pdfDocument: PDFDocumentProxy | null = null;
let renderGeneration = 0;

function renderScale() {
  return 1.45 * Math.min(1.6, Math.max(0.75, props.zoom || 1));
}

function setCanvasRef(pageNumber: number, element: unknown) {
  if (element instanceof HTMLCanvasElement) canvasRefs.set(pageNumber, element);
  else canvasRefs.delete(pageNumber);
}

function annotationsForPage(pageNumber: number) {
  return props.annotations.filter((annotation) => annotation.page === pageNumber);
}

function annotationStyle(annotation: PdfAnnotation, order: number) {
  const pageWidth = Math.max(1, annotation.page_width);
  const pageHeight = Math.max(1, annotation.page_height);
  return {
    left: `${(annotation.x / pageWidth) * 100}%`,
    top: `${(annotation.y / pageHeight) * 100}%`,
    width: `${Math.max(0.8, (annotation.width / pageWidth) * 100)}%`,
    height: `${Math.max(1.2, (annotation.height / pageHeight) * 100)}%`,
    "--mark-delay": `${Math.min(order, 6) * 0.1}s`,
  };
}

async function renderPage(page: PDFPageProxy, canvas: HTMLCanvasElement, generation: number) {
  const viewport = page.getViewport({ scale: renderScale() });
  const outputScale = Math.min(2, window.devicePixelRatio || 1);
  const context = canvas.getContext("2d");
  if (!context || generation !== renderGeneration) return;

  canvas.width = Math.floor(viewport.width * outputScale);
  canvas.height = Math.floor(viewport.height * outputScale);
  canvas.style.width = `${viewport.width}px`;
  canvas.style.height = `${viewport.height}px`;
  await page.render({
    canvasContext: context,
    viewport,
    transform: outputScale === 1 ? undefined : [outputScale, 0, 0, outputScale, 0, 0],
  }).promise;
}

async function loadPdf() {
  const generation = ++renderGeneration;
  pages.value = [];
  canvasRefs.clear();
  errorMessage.value = "";
  if (!props.blob) return;
  loading.value = true;

  try {
    if (pdfDocument) await pdfDocument.destroy();
    const data = await props.blob.arrayBuffer();
    const loadingTask = getDocument({
      data,
      cMapUrl,
      cMapPacked: true,
      standardFontDataUrl,
      useSystemFonts: true,
    });
    pdfDocument = await loadingTask.promise;

    const pageEntries: Array<{ proxy: PDFPageProxy; meta: PageMeta }> = [];
    for (let pageNumber = 1; pageNumber <= pdfDocument.numPages; pageNumber += 1) {
      const proxy = await pdfDocument.getPage(pageNumber);
      const viewport = proxy.getViewport({ scale: renderScale() });
      pageEntries.push({ proxy, meta: { number: pageNumber, width: viewport.width, height: viewport.height } });
    }
    if (generation !== renderGeneration) return;
    pages.value = pageEntries.map((entry) => entry.meta);
    loading.value = false;
    await nextTick();
    await Promise.all(pageEntries.map((entry) => {
      const canvas = canvasRefs.get(entry.meta.number);
      return canvas ? renderPage(entry.proxy, canvas, generation) : Promise.resolve();
    }));
  } catch (error) {
    console.error("PDF render failed", error);
    errorMessage.value = "PDF 화면을 표시하지 못했습니다.";
  } finally {
    if (generation === renderGeneration) loading.value = false;
  }
}

function scrollToSelected(id: string | null | undefined) {
  if (!id || !viewerRef.value) return;
  const target = Array.from(viewerRef.value.querySelectorAll<HTMLElement>("[data-annotation-id]"))
    .find((element) => element.dataset.annotationId === id);
  target?.scrollIntoView({ behavior: "smooth", block: "center" });
}

watch(() => props.blob, loadPdf, { immediate: true });
watch(() => props.zoom, loadPdf);
watch(() => props.selectedId, (id) => nextTick(() => scrollToSelected(id)));

onBeforeUnmount(async () => {
  renderGeneration += 1;
  if (pdfDocument) await pdfDocument.destroy();
});
</script>

<style scoped>
.pdf-document-viewer { width: 100%; max-width: 100%; height: min(72vh, 820px); min-height: 480px; padding: 18px; overflow: auto; overscroll-behavior: contain; scrollbar-gutter: stable both-edges; scrollbar-color: #918ca0 #cbc9d2; scrollbar-width: auto; touch-action: pan-x pan-y; border-radius: 14px; background: #dedde4; }
.pdf-document-viewer::-webkit-scrollbar { width: 12px; height: 12px; }.pdf-document-viewer::-webkit-scrollbar-track { background: #cbc9d2; }.pdf-document-viewer::-webkit-scrollbar-thumb { border: 3px solid #cbc9d2; border-radius: 999px; background: #817b90; }
.pdf-pages { width: max-content; min-width: 100%; display: flex; flex-direction: column; align-items: center; gap: 18px; }
.pdf-page-shell { position: relative; flex: none; overflow: hidden; container-type: inline-size; background: #fff; box-shadow: 0 3px 14px rgb(32 26 58 / .16); transition: width .2s ease; }
.pdf-page-shell canvas { width: 100% !important; height: 100% !important; display: block; }
.pdf-change-mark { position: absolute; z-index: 2; min-width: 6px; min-height: 8px; padding: 0; overflow: visible; border: 0; border-bottom: 3px solid #7658ff; border-radius: 2px; color: transparent; background: rgb(106 77 255 / .13); cursor: pointer; transition: background .15s ease, box-shadow .15s ease; animation: pdf-mark-in .55s ease var(--mark-delay, 0s) both; }
.pdf-change-mark.original { animation-name: pdf-mark-in-original; }
.pdf-change-mark:hover, .pdf-change-mark.selected { background: rgb(106 77 255 / .24); box-shadow: 0 0 0 2px rgb(106 77 255 / .36); }
.pdf-change-mark.approximate { border-bottom-style: solid; }
.pdf-change-tooltip { position: absolute; z-index: 3; left: 50%; bottom: calc(100% + 7px); max-width: 260px; padding: 6px 9px; display: none; transform: translateX(-50%); border-radius: 8px; color: #fff; background: #191527; white-space: nowrap; font-size: 11px; font-weight: 600; box-shadow: 0 6px 18px rgb(25 21 39 / .24); }
.pdf-change-mark:hover .pdf-change-tooltip, .pdf-change-mark:focus-visible .pdf-change-tooltip { display: block; }
.pdf-page-number { position: absolute; right: 10px; bottom: 8px; padding: 3px 7px; border-radius: 999px; color: #686477; background: rgb(255 255 255 / .86); font-size: 10px; }
.pdf-viewer-state { min-height: 360px; display: grid; place-items: center; color: var(--muted); font-size: 13px; }.pdf-viewer-state.error { color: #c0392b; }
@keyframes pdf-mark-in { from { opacity: 0; transform: translateY(40%) scaleX(.12); transform-origin: left bottom; } to { opacity: 1; transform: translateY(0) scaleX(1); } }
@keyframes pdf-mark-in-original { from { opacity: 0; transform: translateY(-40%) scaleX(.12); transform-origin: left bottom; } to { opacity: 1; transform: translateY(0) scaleX(1); } }
[data-theme="dark"] .pdf-document-viewer { scrollbar-color: #6e687d #24222c; background: #111019; }[data-theme="dark"] .pdf-document-viewer::-webkit-scrollbar-track { background: #24222c; }[data-theme="dark"] .pdf-document-viewer::-webkit-scrollbar-thumb { border-color: #24222c; background: #777184; }
@media (max-width: 620px) { .pdf-document-viewer { height: 68vh; min-height: 420px; padding: 8px; }.pdf-pages { gap: 10px; }.pdf-change-mark { border-bottom-width: 2px; } }
@media (prefers-reduced-motion: reduce) { .pdf-page-shell { transition: none; }.pdf-change-mark { animation: none; } }
</style>
