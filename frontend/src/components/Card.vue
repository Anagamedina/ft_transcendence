<template>
  <div class="card bg-base-100 shadow-xl p-4">
    <h3 class="text-lg font-bold">{{ title }}</h3>
    <p class="text-gray-600">{{ description }}</p>
    <button 
      class="btn btn-primary mt-4"
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
  buttonText: String
})

defineEmits(['click'])
</script>