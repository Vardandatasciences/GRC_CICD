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
      :maxlength="maxlength"
      :minlength="minlength"
      :pattern="pattern"
      :autocomplete="autocomplete"
      :autofocus="autofocus"
      :name="name"
      class="text-input"
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
    default: 'text',
    validator: (value) => ['text', 'email', 'password', 'search', 'tel', 'url'].includes(value)
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
  maxlength: {
    type: Number,
    default: null
  },
  minlength: {
    type: Number,
    default: null
  },
  pattern: {
    type: String,
    default: ''
  },
  autocomplete: {
    type: String,
    default: ''
  },
  autofocus: {
    type: Boolean,
    default: false
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
.text-input {
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

.text-input:focus {
  outline: none;
  border-color: var(--input-border-focus);
  box-shadow: 0 0 0 3px var(--input-shadow-focus);
}

.text-input::placeholder {
  color: var(--input-placeholder);
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