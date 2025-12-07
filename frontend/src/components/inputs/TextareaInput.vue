<template>
  <BaseInput
    :id="id"
    :label="label"
    :required="required"
    :helper-text="helperText"
    :error-message="errorMessage"
  >
    <textarea
      :id="id"
      :value="modelValue"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :readonly="readonly"
      :rows="rows"
      :cols="cols"
      :maxlength="maxlength"
      :minlength="minlength"
      :name="name"
      class="textarea-input"
      :class="{ 'input-error': hasError, 'input-disabled': disabled }"
      @input="handleInput"
      @blur="handleBlur"
      @focus="handleFocus"
    ></textarea>
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
  rows: {
    type: Number,
    default: 4
  },
  cols: {
    type: Number,
    default: null
  },
  maxlength: {
    type: Number,
    default: null
  },
  minlength: {
    type: Number,
    default: null
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
.textarea-input {
  width: 100%;
  padding: var(--input-padding);
  border: 1px solid var(--input-border);
  border-radius: var(--input-border-radius);
  font-size: var(--input-font-size);
  color: var(--input-text);
  background-color: var(--input-bg);
  transition: all 0.2s;
  box-sizing: border-box;
  font-family: inherit;
  resize: vertical;
  min-height: 80px;
}

.textarea-input:focus {
  outline: none;
  border-color: var(--input-border-focus);
  box-shadow: 0 0 0 3px var(--input-shadow-focus);
}

.textarea-input::placeholder {
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
  resize: none;
}

.input-disabled:focus {
  border-color: var(--input-border-disabled);
  box-shadow: none;
}
</style> 