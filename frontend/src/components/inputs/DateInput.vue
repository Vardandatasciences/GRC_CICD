<template>
  <BaseInput
    :id="id"
    :label="label"
    :required="required"
    :helper-text="helperText"
    :error-message="errorMessage"
  >
    <input
      :id="id"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :readonly="readonly"
      :min="min"
      :max="max"
      :name="name"
      class="date-input"
      :class="{ 'input-error': hasError, 'input-disabled': disabled }"
      @input="handleInput"
      @blur="handleBlur"
      @focus="handleFocus"
    />
  </BaseInput>
</template>

<script setup>
/* eslint-disable no-undef */
import { computed } from 'vue';
import BaseInput from './BaseInput.vue';

const props = defineProps({
  id: {
    type: String,
    required: true
  },
  modelValue: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'date',
    validator: (value) => ['date', 'time', 'datetime-local', 'month', 'week'].includes(value)
  },
  label: {
    type: String,
    default: ''
  },
  placeholder: {
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
  readonly: {
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
  min: {
    type: String,
    default: ''
  },
  max: {
    type: String,
    default: ''
  },
  name: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['update:modelValue', 'blur', 'focus']);

const hasError = computed(() => !!props.errorMessage);

const handleInput = (event) => {
  emit('update:modelValue', event.target.value);
};

const handleBlur = (event) => {
  emit('blur', event);
};

const handleFocus = (event) => {
  emit('focus', event);
};
</script>

<style scoped>
.date-input {
  width: 100%;
  padding: var(--input-padding);
  border: 1px solid var(--input-border);
  border-radius: var(--input-border-radius);
  font-size: var(--input-font-size);
  color: var(--input-text);
  background-color: var(--input-bg);
  transition: all 0.2s;
  box-sizing: border-box;
}

.date-input:focus {
  outline: none;
  border-color: var(--input-border-focus);
  box-shadow: 0 0 0 3px var(--input-shadow-focus);
}

.date-input::placeholder {
  color: var(--input-placeholder);
}

/* Custom styling for date/time inputs */
.date-input[type="date"],
.date-input[type="time"],
.date-input[type="datetime-local"],
.date-input[type="month"],
.date-input[type="week"] {
  position: relative;
}

/* Hide default calendar icon in some browsers */
.date-input[type="date"]::-webkit-calendar-picker-indicator,
.date-input[type="time"]::-webkit-calendar-picker-indicator,
.date-input[type="datetime-local"]::-webkit-calendar-picker-indicator,
.date-input[type="month"]::-webkit-calendar-picker-indicator,
.date-input[type="week"]::-webkit-calendar-picker-indicator {
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.date-input[type="date"]::-webkit-calendar-picker-indicator:hover,
.date-input[type="time"]::-webkit-calendar-picker-indicator:hover,
.date-input[type="datetime-local"]::-webkit-calendar-picker-indicator:hover,
.date-input[type="month"]::-webkit-calendar-picker-indicator:hover,
.date-input[type="week"]::-webkit-calendar-picker-indicator:hover {
  opacity: 1;
}

.input-error {
  border-color: var(--input-border-error);
}

.input-error:focus {
  border-color: var(--input-border-error);
  box-shadow: 0 0 0 3px var(--input-shadow-error);
}

.input-disabled {
  background-color: var(--input-bg-disabled);
  color: var(--input-text-disabled);
  cursor: not-allowed;
}

.input-disabled:focus {
  border-color: var(--input-border-disabled);
  box-shadow: none;
}
</style> 