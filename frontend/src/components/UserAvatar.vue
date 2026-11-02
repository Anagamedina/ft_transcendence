<!--
  USER AVATAR
  Square with the initials of a name (first letter of its first two words),
  as in the client design. Decorative: the name is always written next to it.
  Usage:
    <UserAvatar name="Lucía Martín" />   → "LM"
-->

<template>
  <span
    class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-aqua-50 text-xs font-bold text-aqua-700"
    aria-hidden="true"
  >
    {{ initials }}
  </span>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  name: { type: String, default: "" },
});

const initials = computed(
  () =>
    props.name
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((word) => word[0] ?? "")
      .join("")
      .toUpperCase() || "?",
);
</script>
