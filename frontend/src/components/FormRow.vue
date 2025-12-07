<template>
  <div class="form-row" :class="{ 'form-row-responsive': responsive }">
    <slot></slot>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';

defineProps({
  responsive: {
    type: Boolean,
    default: true
  }
});
</script>

<style scoped>
.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--form-row-gap);
  align-items: start;
}

.form-row-responsive {
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}

@media (max-width: 768px) {
  .form-row-responsive {
    grid-template-columns: 1fr;
  }
}
</style> 