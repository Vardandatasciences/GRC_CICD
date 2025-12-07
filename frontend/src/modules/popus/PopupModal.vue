<template>
  <div v-if="visible" class="popup-backdrop" @keydown.esc="onClose" tabindex="0" aria-modal="true" role="dialog">
    <div class="popup-modal" :class="type">
      <div class="popup-icon" v-if="icon">
        <span v-html="icon"></span>
      </div>
      <h2 class="popup-heading">{{ heading }}</h2>
      <p class="popup-message">{{ message }}</p>
      <textarea
        v-if="type === 'comment'"
        v-model="comment"
        class="popup-input"
        :placeholder="inputPlaceholder"
        @keydown.enter.stop
      ></textarea>
      <select
        v-if="type === 'select'"
        v-model="selectedValue"
        class="popup-select"
      >
        <option v-for="option in selectOptions" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </select>
      <div class="popup-actions">
        <button
          v-for="(btn, idx) in buttons"
          :key="idx"
          @click="onAction(btn.action)"
          :class="btn.class"
          
        >{{ btn.label }}</button>
      </div>
    </div>
  </div>
</template>

<script>
import { PopupService } from './popupService';

const ICONS = {
  success: '✓',
  error: '✗',
  warning: '⚠️',
  info: 'ℹ️',
  confirm: '❓',
  comment: '💬',
  select: '📋',
  'access-denied': '🚫'
};

export default {
  name: 'PopupModal',
  setup() {
    const popupState = PopupService.getState();

    return {
      popupState
    };
  },
  computed: {
    visible() {
      return this.popupState.visible;
    },
    type() {
      return this.popupState.type;
    },
    heading() {
      return this.popupState.heading;
    },
    message() {
      return this.popupState.message;
    },
    buttons() {
      return this.popupState.buttons;
    },
    autoClose() {
      return this.popupState.autoClose;
    },
    icon() {
      return ICONS[this.type] || '';
    },
    selectOptions() {
      return this.popupState.selectOptions || [];
    },
    inputPlaceholder() {
      return this.popupState.inputPlaceholder;
    }
  },
  watch: {
    visible(val) {
      if (val && this.autoClose > 0) {
        setTimeout(() => this.onAction('auto-close'), this.autoClose);
      }
      if (val) {
        this.comment = '';
        this.selectedValue = this.popupState.selectedValue || '';
      }
    }
  },
  data() {
    return { comment: '', selectedValue: '' }
  },
  methods: {
    onClose() {
      this.onAction('close');
    },
    onAction(action) {
      if (this.type === 'comment') {
        PopupService.handleAction({ action, comment: this.comment });
      } else if (this.type === 'select') {
        PopupService.handleAction({ action, comment: this.selectedValue });
      } else {
        PopupService.handleAction({ action });
      }
    }
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

.popup-backdrop {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  background: rgba(30, 41, 59, 0.55) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: 10000 !important;
  font-family: 'Inter', Arial, sans-serif;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
}
 
/* Override any conflicting modal styles */
.popup-backdrop[class*="modal-overlay"],
.popup-backdrop[class*="modal"] {
  background: rgba(30, 41, 59, 0.55) !important;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
}
.popup-modal {
  background: linear-gradient(135deg, #f8fafc 0%, #e0e7ef 100%) !important;
  border-radius: 18px;
  padding: 2rem 1rem 1.2rem 1rem;
  width: 320px;
  max-width: 90vw;
  min-width: 240px;
  box-shadow: 0 8px 32px 0 rgba(16, 30, 54, 0.18), 0 1.5px 8px 0 rgba(0,0,0,0.08);
  text-align: center;
  position: relative;
  border: 2px solid #e3e8ee;
  transition: box-shadow 0.2s, border-color 0.2s;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* Override any conflicting modal styles */
.popup-modal[class*="modal"],
.popup-modal[class*="overlay"] {
  background: linear-gradient(135deg, #f8fafc 0%, #e0e7ef 100%) !important;
  backdrop-filter: none !important;
}
/* Colored outline for each type */
.success.popup-modal { border-color: #4caf50; }
.error.popup-modal { border-color: #d32f2f; }
.warning.popup-modal { border-color: #fbbf24; }
.info.popup-modal { border-color: #2563eb; }
.confirm.popup-modal { border-color: #6c47b6; }
.comment.popup-modal { border-color: #8e24aa; }
.select.popup-modal { border-color: #1976d2; }
.access-denied.popup-modal { border-color: #dc2626; }

.popup-icon {
  font-size: 1.6rem;
  margin-bottom: 0.5rem;
  margin-top: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #e0e7ef 0%, #f8fafc 100%);
  box-shadow: 0 2px 4px rgba(44, 62, 80, 0.06);
  color: #2563eb;
  position: relative;
  z-index: 2;
  border: 2px solid #fff;
}
.success .popup-icon { background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); color: #219653; }
.error .popup-icon { background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%); color: #d32f2f; }
.warning .popup-icon { background: linear-gradient(135deg, #fffde7 0%, #fff9c4 100%); color: #f59e42; }
.info .popup-icon { background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); color: #2563eb; }
.confirm .popup-icon { background: linear-gradient(135deg, #ede7f6 0%, #d1c4e9 100%); color: #6c47b6; }
.comment .popup-icon { background: linear-gradient(135deg, #f3e8ff 0%, #e1bee7 100%); color: #8e24aa; }
.select .popup-icon { background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); color: #2563eb; }
.access-denied .popup-icon { background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%); color: #dc2626; }

.popup-heading {
  margin: 1.5rem 0 0.5rem 0;
  font-size: 1.2rem;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: 0.01em;
}
.popup-message {
  margin-bottom: 1.1rem;
  color: #475569;
  font-size: 0.98rem;
  line-height: 1.5;
}
.popup-input {
  width: 100%;
  min-height: 48px;
  margin-bottom: 1rem;
  border-radius: 8px;
  border: 1.5px solid #cbd5e1;
  padding: 0.5rem 0.7rem;
  font-size: 0.98rem;
  background: #f8fafc;
  color: #334155;
  resize: vertical;
  transition: border 0.2s;
}
.popup-input:focus {
  border: 1.5px solid #2563eb;
  outline: none;
}
.popup-select {
  width: 100%;
  min-height: 48px;
  margin-bottom: 1rem;
  border-radius: 8px;
  border: 1.5px solid #cbd5e1;
  padding: 0.5rem 0.7rem;
  font-size: 0.98rem;
  background: #f8fafc;
  color: #334155;
  transition: border 0.2s;
}
.popup-select:focus {
  border: 1.5px solid #2563eb;
  outline: none;
}
.popup-actions {
  display: flex;
  justify-content: center;
  gap: 0.7rem;
  margin-top: 0.3rem;
}
button {
  padding: 0.5rem 1.2rem;
  border-radius: 7px;
  border: none;
  font-size: 0.98rem;
  font-weight: 600;
  cursor: pointer;
  background: linear-gradient(90deg, #2563eb 0%, #1e40af 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(44, 62, 80, 0.07);
  letter-spacing: 0.01em;
  transition: background 0.18s, box-shadow 0.18s, transform 0.12s;
}
button.success {
  background: linear-gradient(90deg, #219653 0%, #43a047 100%);
}
button.error {
  background: linear-gradient(90deg, #d32f2f 0%, #b71c1c 100%);
}
button.warning {
  background: linear-gradient(90deg, #f59e42 0%, #fbbf24 100%);
  color: #fff;
}
button:active {
  transform: scale(0.97);
}
button:focus {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

/* Responsive */
@media (max-width: 500px) {
  .popup-modal {
    padding: 0.8rem 0.2rem 0.8rem 0.2rem;
    min-width: 0;
    width: 90vw;
  }
  .popup-heading {
    font-size: 1rem;
  }
  .popup-icon {
    font-size: 1.4rem;
    width: 38px;
    height: 38px;
    top: -19px;
  }
}
</style> 