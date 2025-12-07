<template>
  <div class="checkbox-group" :class="{ 'checkbox-group-error': hasError }">
    <label v-if="label" class="checkbox-group-label">
      {{ label }}
      <span v-if="required" class="required">*</span>
    </label>
    
    <div class="checkbox-options">
      <div
        v-for="option in options"
        :key="option.value"
        class="checkbox-item"
        :class="{ 'checkbox-disabled': disabled || option.disabled }"
      >
        <input
          :id="`${id}-${option.value}`"
          type="checkbox"
          :value="option.value"
          :checked="isChecked(option.value)"
          :disabled="disabled || option.disabled"
          :name="name"
          class="checkbox-input"
          @change="handleChange"
        />
        <label :for="`${id}-${option.value}`" class="checkbox-label">
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
    type: [Array, Boolean],
    default: () => []
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
  },
  single: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:modelValue', 'change']);

const hasError = computed(() => !!props.errorMessage);

const isChecked = (value) => {
  if (props.single) {
    return props.modelValue === value;
  }
  return Array.isArray(props.modelValue) && props.modelValue.includes(value);
};

const handleChange = (event) => {
  const value = event.target.value;
  const checked = event.target.checked;
  
  if (props.single) {
    emit('update:modelValue', checked ? value : '');
  } else {
    const currentValues = Array.isArray(props.modelValue) ? [...props.modelValue] : [];
    
    if (checked) {
      if (!currentValues.includes(value)) {
        currentValues.push(value);
      }
    } else {
      const index = currentValues.indexOf(value);
      if (index > -1) {
        currentValues.splice(index, 1);
      }
    }
    
    emit('update:modelValue', currentValues);
  }
  
  emit('change', event);
};
</script>

<style scoped>
.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checkbox-group-error {
  margin-bottom: 4px;
}

.checkbox-group-label {
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

.checkbox-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.checkbox-input {
  width: 16px;
  height: 16px;
  border: 2px solid var(--checkbox-border);
  border-radius: 3px;
  background-color: var(--checkbox-bg);
  cursor: pointer;
  transition: all 0.2s;
  appearance: none;
  position: relative;
}

.checkbox-input:checked {
  background-color: var(--checkbox-bg-checked);
  border-color: var(--checkbox-border-checked);
}

.checkbox-input:checked::after {
  content: '';
  position: absolute;
  left: 4px;
  top: 1px;
  width: 4px;
  height: 8px;
  border: solid var(--checkbox-checkmark);
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox-input:focus {
  outline: none;
  border-color: var(--input-border-focus);
  box-shadow: 0 0 0 3px var(--input-shadow-focus);
}

.checkbox-input:disabled {
  background-color: var(--checkbox-bg-disabled);
  border-color: var(--checkbox-border-disabled);
  cursor: not-allowed;
}

.checkbox-input:disabled:checked {
  background-color: var(--checkbox-bg-disabled-checked);
  border-color: var(--checkbox-bg-disabled-checked);
}

.checkbox-label {
  font-size: var(--input-font-size);
  color: var(--input-text);
  cursor: pointer;
  user-select: none;
}

.checkbox-disabled .checkbox-label {
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

.checkbox-group-error .checkbox-group-label {
  color: var(--label-text-error);
}
</style> 