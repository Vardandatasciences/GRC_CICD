<template>
  <div class="form-group" :class="{ 'form-group-error': hasError }">
    <label v-if="label" :for="id" class="form-label">
      {{ label }}
      <span v-if="required" class="required">*</span>
    </label>
    
    <div class="input-wrapper">
      <slot></slot>
    </div>
    
    <small v-if="helperText" class="helper-text">{{ helperText }}</small>
    <small v-if="errorMessage" class="error-text">{{ errorMessage }}</small>
  </div>
</template>

<script setup>
/* eslint-disable no-undef */
import { computed } from 'vue';

const props = defineProps({
  id: {
    type: String,
    required: true
  },
  label: {
    type: String,
    default: ''
  },
  required: {
    type: Boolean,
    default: false
  },
  helperText: {
    type: String,
    default: ''
  },
  errorMessage: {
    type: String,
    default: ''
  }
});

const hasError = computed(() => !!props.errorMessage);
</script>

<style scoped>
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group-error {
  margin-bottom: 4px;
}

.form-label {
  font-size: var(--label-font-size);
  font-weight: var(--label-font-weight);
  color: var(--label-text);
  display: flex;
  align-items: center;
  gap: 4px;
}

.required {
  color: var(--label-required);
  font-weight: 600;
}

.input-wrapper {
  position: relative;
}

.helper-text {
  font-size: var(--helper-font-size);
  color: var(--helper-text);
  margin-top: 2px;
}

.error-text {
  font-size: var(--helper-font-size);
  color: var(--error-text);
  margin-top: 2px;
}

.form-group-error .form-label {
  color: var(--label-text-error);
}
</style> 