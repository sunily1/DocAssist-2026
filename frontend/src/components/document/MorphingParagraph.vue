<template>
  <p class="morph-paragraph" :class="{ 'show-original': showOriginal }">
    <span
      class="morph-layer morph-original"
      :class="{ active: showOriginal }"
      :aria-hidden="!showOriginal"
    >
      <template v-for="(segment, index) in originalSegments" :key="`original-${index}`">
        <span
          v-if="segment.changed"
          class="morph-word morph-hard-word"
          :style="delayStyle(segment.order)"
        >{{ segment.text }}</span>
        <template v-else>{{ segment.text }}</template>
      </template>
    </span>

    <span
      class="morph-layer morph-easy"
      :class="{ active: !showOriginal }"
      :aria-hidden="showOriginal"
    >
      <template v-for="(segment, index) in easySegments" :key="`easy-${index}`">
        <mark
          v-if="segment.changed"
          class="morph-word morph-easy-word"
          :style="delayStyle(segment.order)"
        >{{ segment.text }}</mark>
        <template v-else>{{ segment.text }}</template>
      </template>
    </span>
  </p>
</template>

<script setup lang="ts">
import { computed, type CSSProperties } from "vue";

interface ChangedTerm {
  from: string;
  to: string;
}

interface TextSegment {
  text: string;
  changed: boolean;
  order: number;
}

const props = withDefaults(defineProps<{
  original: string;
  easy: string;
  changes?: ChangedTerm[];
  showOriginal?: boolean;
}>(), {
  changes: () => [],
  showOriginal: false,
});

const originalSegments = computed(() => segmentText(props.original, "from"));
const easySegments = computed(() => segmentText(props.easy || props.original, "to"));

function delayStyle(order: number): CSSProperties {
  return { "--morph-delay": `${Math.min(order, 8) * 0.1}s` } as CSSProperties;
}

function segmentText(textValue: string, field: "from" | "to"): TextSegment[] {
  const text = String(textValue || "");
  if (!text || !props.changes.length) return [{ text, changed: false, order: 0 }];

  const ranges: Array<{ start: number; end: number; order: number }> = [];
  props.changes.forEach((change, order) => {
    const term = String(change[field] || "").trim();
    if (!term) return;

    let start = text.indexOf(term);
    let matchedLength = term.length;
    if (start < 0) {
      let prefix = term;
      while (prefix.length >= 2 && (start = text.indexOf(prefix)) < 0) prefix = prefix.slice(0, -1);
      if (start < 0 || prefix.length < 2) return;

      const wordCount = term.split(/\s+/).length;
      const tokenPattern = wordCount > 1
        ? new RegExp(`^(?:[^\\s,.!?]+\\s+){${wordCount - 1}}[^\\s,.!?]+`)
        : /^[^\s,.!?]+/;
      matchedLength = text.slice(start).match(tokenPattern)?.[0].length || prefix.length;
    }

    const range = { start, end: start + matchedLength, order };
    const overlaps = ranges.some((existing) => range.start < existing.end && range.end > existing.start);
    if (!overlaps) ranges.push(range);
  });

  ranges.sort((a, b) => a.start - b.start);
  if (!ranges.length) return [{ text, changed: false, order: 0 }];

  const segments: TextSegment[] = [];
  let cursor = 0;
  ranges.forEach((range) => {
    if (range.start > cursor) {
      segments.push({ text: text.slice(cursor, range.start), changed: false, order: 0 });
    }
    segments.push({ text: text.slice(range.start, range.end), changed: true, order: range.order });
    cursor = range.end;
  });
  if (cursor < text.length) segments.push({ text: text.slice(cursor), changed: false, order: 0 });
  return segments;
}
</script>

<style scoped>
.morph-paragraph {
  position: relative;
  margin: 0 0 26px;
  overflow-wrap: anywhere;
}

.morph-paragraph:last-child { margin-bottom: 0; }

.morph-layer {
  display: block;
  width: 100%;
  transition: opacity .4s ease, transform .4s ease;
}

.morph-layer:not(.active) {
  position: absolute;
  inset: 0;
  opacity: 0;
  pointer-events: none;
}

.morph-layer.active {
  position: relative;
  opacity: 1;
  transform: translateY(0);
}

.morph-original:not(.active) { transform: translateY(-40%); }
.morph-easy:not(.active) { transform: translateY(40%); }

.morph-word {
  display: inline-block;
  transition: opacity .4s ease var(--morph-delay, 0s), transform .4s ease var(--morph-delay, 0s);
}

.morph-original:not(.active) .morph-word {
  opacity: 0;
  transform: translateY(-40%);
}

.morph-easy:not(.active) .morph-word {
  opacity: 0;
  transform: translateY(40%);
}

.morph-hard-word { font-weight: 600; }

.morph-easy-word {
  color: var(--ink);
  background: linear-gradient(transparent 64%, #ddd2ff 64%) left bottom / 0 100% no-repeat;
  font-weight: 700;
  text-decoration: none;
}

.morph-easy.active .morph-easy-word {
  animation: morph-easy-word-in .55s ease var(--morph-delay, 0s) both;
}

[data-theme="dark"] .morph-easy-word {
  background-image: linear-gradient(transparent 64%, #574883 64%);
}

@keyframes morph-easy-word-in {
  from {
    opacity: 0;
    transform: translateY(40%);
    background-size: 0 100%;
  }
  to {
    opacity: 1;
    transform: translateY(0);
    background-size: 100% 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .morph-layer,
  .morph-word { transition: none; }
  .morph-easy.active .morph-easy-word { animation: none; background-size: 100% 100%; }
}
</style>
