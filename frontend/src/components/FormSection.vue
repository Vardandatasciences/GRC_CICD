<template>
  <div class="form-section">
    <h2 v-if="title" class="section-title">{{ title }}</h2>
    <div class="section-content">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';

defineProps({
  title: {
    type: String,
    default: ''
  }
});
</script>

<style scoped>
.form-section {
  margin-bottom: 30px;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--form-section-title);
  margin-bottom: 20px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--form-section-border);
}

.section-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
</style> 