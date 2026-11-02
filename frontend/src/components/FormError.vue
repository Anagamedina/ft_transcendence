<!--
  FormError — an error of the whole form (network, rate limit, an API error
  that is not of one field), the same box in every form. role="alert" reads
  it out when it appears; focus() moves the focus there when the form has
  no field to send it to.

    <FormError ref="formError" :message="generalError" />
-->
<template>
  <p
    v-if="message"
    ref="box"
    role="alert"
    tabindex="-1"
    class="rounded-lg border border-danger/40 bg-danger-light px-4 py-3 text-sm text-danger-dark focus:outline-none"
  >
    {{ message }}
    <slot />
  </p>
</template>

<script setup>
import { ref } from "vue";

defineProps({
  message: { type: String, default: "" },
});

const box = ref(null);

defineExpose({ focus: () => box.value?.focus() });
</script>
