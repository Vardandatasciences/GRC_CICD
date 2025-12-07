<template>
  <div class="form-container">
    <!-- Form Header -->
    <div class="form-header" v-if="header || subheader">
      <h1 v-if="header">{{ header }}</h1>
      <p v-if="subheader">{{ subheader }}</p>
    </div>

    <!-- Form Content -->
    <form @submit.prevent="handleSubmit" class="form-content">
      <slot></slot>
      
      <!-- Form Actions -->
      <div class="form-actions" v-if="showActions">
        <slot name="actions">
          <button 
            v-if="resetButton" 
            type="button" 
            @click="handleReset" 
            class="btn-secondary"
          >
            {{ resetButtonText }}
          </button>
          <button 
            v-if="submitButton" 
            type="submit" 
            class="btn-primary"
          >
            {{ submitButtonText }}
          </button>
        </slot>
      </div>
    </form>
  </div>
</template>

<script setup>
/* eslint-disable no-undef */
import { defineProps, defineEmits } from 'vue';
import './styles/theme.css'
defineProps({
  header: {
    type: String,
    default: ''
  },
  subheader: {
    type: String,
    default: ''
  },
  showActions: {
    type: Boolean,
    default: true
  },
  resetButton: {
    type: Boolean,
    default: true
  },
  submitButton: {
    type: Boolean,
    default: true
  },
  resetButtonText: {
    type: String,
    default: 'Reset Form'
  },
  submitButtonText: {
    type: String,
    default: 'Submit'
  }
});

const emit = defineEmits(['submit', 'reset']);

const handleSubmit = () => {
  emit('submit');
};

const handleReset = () => {
  emit('reset');
};
</script>

<style scoped>
.form-container {
  max-width: var(--form-container-max-width);
  margin: 0 auto;
  padding: var(--form-container-padding, 20px);
  background: var(--form-container-bg);
}

.form-header {
  margin-bottom: 30px;
  text-align: center;
}

.form-header h1 {
  font-size: 2rem;
  font-weight: 600;
  color: var(--form-header-text);
  margin-bottom: 8px;
}

.form-header p {
  font-size: 1rem;
  color: var(--form-header-subtext);
  margin: 0;
}

.form-content {
  background: var(--form-content-bg);
  border-radius: var(--form-content-border-radius);
  box-shadow: var(--form-content-shadow);
  padding: 30px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid var(--form-actions-border);
}

.btn-primary {
  background: var(--btn-primary-bg);
  color: var(--btn-primary-text);
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background: var(--btn-primary-hover-bg);
}

.btn-secondary {
  background: var(--btn-secondary-bg);
  color: var(--btn-secondary-text);
  border: 1px solid var(--btn-secondary-border);
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: var(--btn-secondary-hover-bg);
  border-color: var(--btn-secondary-hover-border);
}
</style> 