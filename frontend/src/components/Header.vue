<template>
  <header class="bg-aqua-600 p-4 text-white">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold">{{ title }}</h1>
      <button class="btn btn-sm btn-ghost">Menu</button>
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: String
})
</script>