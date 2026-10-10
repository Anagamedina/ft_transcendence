<template>
  <div
    class="bg-white border-2 border-aqua-200 rounded-xl shadow-2xl shadow-aqua-500/40 hover:shadow-aqua-500/60 p-6 transition max-w-sm"
  >
    <div v-if="$slots.icon" class="w-10 h-10 mb-3 text-aqua-600">
      <slot name="icon" />
    </div>
    <h3 class="text-lg font-bold text-gray-900 mb-2">{{ title }}</h3>
    <p class="text-gray-700 text-base mb-4">{{ description }}</p>
    <button
      v-if="showButton"
      class="w-full bg-gradient-to-r from-blue-600 to-cyan-500 text-white py-2 rounded font-semibold hover:shadow-md transition"
      @click="$emit('click')"
    >
      {{ buttonText }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  description: String,
  buttonText: { type: String, default: "Ver detalles" },
  showButton: { type: Boolean, default: true },
});

defineEmits(["click"]);
</script>
