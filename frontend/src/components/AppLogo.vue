<!--
  APP LOGO (F29)
  The only AquaGuard logo of the app: water drop + name. Used by the public
  Header and by the admin and client Sidebars, so every screen shows the
  same drop. The text takes the colour of its parent (currentColor), so the
  same logo works on light and dark backgrounds.
-->

<template>
  <span class="inline-flex items-center gap-2">
    <svg
      :class="iconSize"
      viewBox="0 0 20 24"
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        <linearGradient :id="gradientId" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" :stop-color="aqua[300]" />
          <stop offset="55%" :stop-color="aqua[400]" />
          <stop offset="100%" :stop-color="aqua[600]" />
        </linearGradient>
      </defs>
      <!-- Drop: pointed top, round bottom -->
      <path
        d="M10 1 C10 1 2 10.5 2 15.5 A8 8 0 0 0 18 15.5 C18 10.5 10 1 10 1 Z"
        :fill="`url(#${gradientId})`"
      />
      <!-- Small highlight so it reads as water -->
      <ellipse cx="7" cy="15" rx="1.6" ry="2.6" fill="white" opacity="0.55" />
    </svg>
    <span
      v-if="!iconOnly"
      :class="[
        'font-bold leading-tight',
        size === 'lg' ? 'text-xl sm:text-2xl' : 'text-lg',
      ]"
      >{{ text }}</span
    >
  </span>
</template>

<script setup>
import { computed, useId } from "vue";
import { aqua } from "../theme/palette.js";

const props = defineProps({
  text: { type: String, default: "AquaGuard" },
  // md: Sidebars; lg: public header; xl: big decorative drop (Landing)
  size: { type: String, default: "md" },
  // Only the drop, without the name
  iconOnly: { type: Boolean, default: false },
});

const ICON_SIZES = { md: "h-6 w-5", lg: "h-8 w-7", xl: "h-24 w-20" };
const iconSize = computed(() => ICON_SIZES[props.size] ?? ICON_SIZES.md);

// Unique id per instance: two logos on one page must not share a gradient id
const gradientId = `aqua-drop-${useId()}`;
</script>
