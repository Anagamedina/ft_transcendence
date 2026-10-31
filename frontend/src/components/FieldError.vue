<!--
  FieldError — the message under a wrong field, the same in every form.
  The input points to it with aria-describedby (fieldAttrs of useFieldErrors),
  so a screen reader reads it with the field.

    <FieldError :id="errorId('email')" :message="errors.email" />

  The slot adds something after the message (a link "Entrar").
-->
<template>
  <p v-if="message" :id="id" class="mt-1 text-sm text-danger-dark">
    {{ message }}
    <slot />
  </p>
</template>

<script setup>
defineProps({
  id: { type: String, required: true },
  message: { type: String, default: "" },
});
</script>
