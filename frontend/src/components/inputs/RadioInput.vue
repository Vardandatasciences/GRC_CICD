<template>
  <div class="radio-group" :class="{ 'radio-group-error': hasError }">
    <label v-if="label" class="radio-group-label">
      {{ label }}
      <span v-if="required" class="required">*</span>
    </label>
    
    <div class="radio-options">
      <div
        v-for="option in options"
        :key="option.value"
        class="radio-item"
        :class="{ 'radio-disabled': disabled || option.disabled }"
      >
        <input
          :id="`${id}-${option.value}`"
          type="radio"
          :value="option.value"
          :checked="modelValue === option.value"
          :disabled="disabled || option.disabled"
          :name="name"
          class="radio-input"
          @change="handleChange"
        />
        <label :for="`${id}-${option.value}`" class="radio-label">
          {{ option.label }}
        </label>
      </div>
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
  modelValue: {
    type: [String, Number],
    default: ''
  },
  label: {
    type: String,
    default: ''
  },
  required: {
    type: Boolean,
    default: false
  },
  disabled: {
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
  },
  options: {
    type: Array,
    default: () => [],
    validator: (value) => {
      return value.every(option => 
        typeof option === 'object' && 
        'value' in option && 
        'label' in option
      );
    }
  },
  name: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['update:modelValue', 'change']);

const hasError = computed(() => !!props.errorMessage);

const handleChange = (event) => {
  const value = event.target.value;
  emit('update:modelValue', value);
  emit('change', event);
};
</script>

<style scoped>
.radio-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.radio-group-error {
  margin-bottom: 4px;
}

.radio-group-label {
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

.radio-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.radio-disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.radio-input {
  width: 16px;
  height: 16px;
  border: 2px solid var(--radio-border);
  border-radius: 50%;
  background-color: var(--radio-bg);
  cursor: pointer;
  transition: all 0.2s;
  appearance: none;
  position: relative;
}

.radio-input:checked {
  border-color: var(--radio-border-checked);
}

.radio-input:checked::after {
  content: '';
  position: absolute;
  left: 3px;
  top: 3px;
  width: 6px;
  height: 6px;
  background-color: var(--radio-dot);
  border-radius: 50%;
}

.radio-input:focus {
  outline: none;
  border-color: var(--input-border-focus);
  box-shadow: 0 0 0 3px var(--input-shadow-focus);
}

.radio-input:disabled {
  background-color: var(--radio-bg-disabled);
  border-color: var(--radio-border-disabled);
  cursor: not-allowed;
}

.radio-input:disabled:checked {
  border-color: var(--radio-bg-disabled-checked);
}

.radio-input:disabled:checked::after {
  background-color: var(--radio-dot-disabled);
}

.radio-label {
  font-size: var(--input-font-size);
  color: var(--input-text);
  cursor: pointer;
  user-select: none;
}

.radio-disabled .radio-label {
  color: var(--input-text-disabled);
  cursor: not-allowed;
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

.radio-group-error .radio-group-label {
  color: var(--label-text-error);
}
</style> 