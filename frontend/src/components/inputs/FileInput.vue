<template>
  <BaseInput
    :id="id"
    :label="label"
    :required="required"
    :helper-text="helperText"
    :error-message="errorMessage"
  >
    <div class="file-input-wrapper">
      <input
        :id="id"
        type="file"
        :accept="accept"
        :multiple="multiple"
        :required="required"
        :disabled="disabled"
        :name="name"
        class="file-input"
        :class="{ 'input-error': hasError, 'input-disabled': disabled }"
        @change="handleChange"
        @blur="handleBlur"
        @focus="handleFocus"
      />
      
      <div v-if="selectedFiles.length > 0" class="file-list">
        <div
          v-for="(file, index) in selectedFiles"
          :key="index"
          class="file-item"
        >
          <span class="file-name">{{ file.name }}</span>
          <span class="file-size">({{ formatFileSize(file.size) }})</span>
          <button
            v-if="!disabled"
            type="button"
            class="remove-file"
            @click="removeFile(index)"
          >
            ×
          </button>
        </div>
      </div>
    </div>
  </BaseInput>
</template>

<script setup>
/* eslint-disable no-undef */
import { computed, ref, watch } from 'vue';
import BaseInput from './BaseInput.vue';

const props = defineProps({
  id: {
    type: String,
    required: true
  },
  modelValue: {
    type: [File, FileList, Array],
    default: null
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
  accept: {
    type: String,
    default: ''
  },
  multiple: {
    type: Boolean,
    default: false
  },
  name: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['update:modelValue', 'change', 'blur', 'focus']);

const hasError = computed(() => !!props.errorMessage);
const selectedFiles = ref([]);

// Watch for changes in modelValue and update selectedFiles
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    if (Array.isArray(newValue)) {
      selectedFiles.value = [...newValue];
    } else if (newValue instanceof FileList) {
      selectedFiles.value = Array.from(newValue);
    } else if (newValue instanceof File) {
      selectedFiles.value = [newValue];
    }
  } else {
    selectedFiles.value = [];
  }
}, { immediate: true });

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const handleChange = (event) => {
  const files = event.target.files;
  
  if (props.multiple) {
    emit('update:modelValue', files);
  } else {
    emit('update:modelValue', files[0] || null);
  }
  
  emit('change', event);
};

const removeFile = (index) => {
  const newFiles = [...selectedFiles.value];
  newFiles.splice(index, 1);
  selectedFiles.value = newFiles;
  
  if (props.multiple) {
    emit('update:modelValue', newFiles);
  } else {
    emit('update:modelValue', newFiles[0] || null);
  }
};

const handleBlur = (event) => {
  emit('blur', event);
};

const handleFocus = (event) => {
  emit('focus', event);
};
</script>

<style scoped>
.file-input-wrapper {
  position: relative;
}

.file-input {
  width: 100%;
  padding: var(--input-padding);
  border: 1px solid var(--input-border);
  border-radius: var(--input-border-radius);
  font-size: var(--input-font-size);
  color: var(--input-text);
  background-color: var(--input-bg);
  transition: all 0.2s;
  box-sizing: border-box;
  cursor: pointer;
}

.file-input:focus {
  outline: none;
  border-color: var(--input-border-focus);
  box-shadow: 0 0 0 3px var(--input-shadow-focus);
}

.file-input::file-selector-button {
  background: var(--file-input-btn-bg);
  border: 1px solid var(--file-input-btn-border);
  border-radius: 4px;
  padding: 6px 12px;
  margin-right: 12px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.file-input::file-selector-button:hover {
  background: var(--file-input-btn-hover-bg);
  border-color: var(--file-input-btn-hover-border);
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

.input-disabled::file-selector-button {
  background: var(--file-input-btn-disabled-bg);
  color: var(--file-input-btn-disabled-text);
  cursor: not-allowed;
}

.file-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: var(--file-list-bg);
  border: 1px solid var(--file-list-border);
  border-radius: 4px;
  font-size: 12px;
}

.file-name {
  font-weight: 500;
  color: var(--file-name-text);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  color: var(--file-size-text);
  font-size: 11px;
}

.remove-file {
  background: var(--file-remove-btn-bg);
  color: white;
  border: none;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
  transition: background-color 0.2s;
}

.remove-file:hover {
  background: var(--file-remove-btn-hover-bg);
}
</style> 