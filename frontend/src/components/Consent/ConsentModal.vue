<template>
  <transition name="modal-fade">
    <div v-show="isVisible" class="consent-modal-overlay" @click.self="handleCancel">
      <div class="consent-modal-container">
        <div class="consent-modal-header">
          <div class="consent-header-icon">
            <i class="fas fa-shield-check"></i>
          </div>
          <h2 class="consent-title">Consent Required</h2>
          <button class="consent-close-btn" @click="handleCancel" aria-label="Close">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="consent-modal-body">
          <div class="consent-action-info">
            <h3>{{ actionLabel }}</h3>
            <p class="consent-action-description">
              You are about to perform an action that requires your explicit consent.
            </p>
          </div>

          <div class="consent-text-container">
            <div class="consent-text-scroll">
              <p class="consent-text">{{ consentText }}</p>
            </div>
          </div>

          <div class="consent-checkbox-container">
            <label class="consent-checkbox-label">
              <input 
                type="checkbox" 
                v-model="hasAgreed" 
                class="consent-checkbox"
              />
              <span class="checkbox-text">
                I have read and agree to the above consent statement
              </span>
            </label>
          </div>

          <div class="consent-info-note">
            <i class="fas fa-info-circle"></i>
            <span>This action will be logged for compliance and audit purposes.</span>
          </div>
        </div>

        <div class="consent-modal-footer">
          <button 
            class="consent-btn consent-btn-cancel" 
            @click="handleCancel"
          >
            Cancel
          </button>
          <button 
            class="consent-btn consent-btn-accept" 
            @click="handleAccept"
            :disabled="!hasAgreed || isProcessing"
          >
            <span v-if="!isProcessing">
              <i class="fas fa-check"></i> Accept & Continue
            </span>
            <span v-else>
              <i class="fas fa-spinner fa-spin"></i> Processing...
            </span>
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
import { ref, computed, defineExpose } from 'vue';
import { recordConsentAcceptance, getActionLabel } from '@/utils/consentManager.js';

export default {
  name: 'ConsentModal',
  
  setup() {
    const isVisible = ref(false);
    const hasAgreed = ref(false);
    const isProcessing = ref(false);
    const currentConfig = ref(null);
    const currentActionType = ref(null);
    const resolveCallback = ref(null);
    const rejectCallback = ref(null);

    const actionLabel = computed(() => {
      return currentActionType.value 
        ? getActionLabel(currentActionType.value) 
        : 'Action';
    });

    const consentText = computed(() => {
      return currentConfig.value?.consent_text || 
        'By proceeding with this action, you acknowledge that you understand the implications and accept responsibility for the action being performed.';
    });

    const show = (actionType, config) => {
      return new Promise((resolve, reject) => {
        currentActionType.value = actionType;
        currentConfig.value = config;
        hasAgreed.value = false;
        isVisible.value = true;
        resolveCallback.value = resolve;
        rejectCallback.value = reject;
      });
    };

    const handleAccept = async () => {
      if (!hasAgreed.value || isProcessing.value) return;

      isProcessing.value = true;

      try {
        const userId = localStorage.getItem('user_id');
        const configId = currentConfig.value.config_id;
        
        // Record consent acceptance
        const success = await recordConsentAcceptance(
          userId,
          configId,
          currentActionType.value
        );

        if (success) {
          isVisible.value = false;
          if (resolveCallback.value) {
            resolveCallback.value(true);
          }
          reset();
        } else {
          console.error('Failed to record consent acceptance');
          // Still allow them to proceed but log the error
          isVisible.value = false;
          if (resolveCallback.value) {
            resolveCallback.value(true);
          }
          reset();
        }
      } catch (error) {
        console.error('Error processing consent:', error);
        // Still allow them to proceed
        isVisible.value = false;
        if (resolveCallback.value) {
          resolveCallback.value(true);
        }
        reset();
      } finally {
        isProcessing.value = false;
      }
    };

    const handleCancel = () => {
      isVisible.value = false;
      if (rejectCallback.value) {
        rejectCallback.value(new Error('User cancelled consent'));
      }
      reset();
    };

    const reset = () => {
      setTimeout(() => {
        hasAgreed.value = false;
        currentConfig.value = null;
        currentActionType.value = null;
        resolveCallback.value = null;
        rejectCallback.value = null;
      }, 300); // Wait for transition to complete
    };

    // Explicitly expose the show method for parent component access
    // Explicitly expose the show method for parent component access via refs
    defineExpose({
      show
    });

    return {
      isVisible,
      hasAgreed,
      isProcessing,
      actionLabel,
      consentText,
      show,
      handleAccept,
      handleCancel
    };
  }
};
</script>

<style scoped>
/* Modal overlay */
.consent-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(4px);
}

/* Modal container */
.consent-modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: modalSlideIn 0.3s ease-out;
}

/* Header */
.consent-modal-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px 24px 16px 24px;
  background-color: white;
  color: white;
  position: relative;
  border-bottom: 1px solid #e2e8f0;
}

.consent-header-icon {
  font-size: 32px;
  display: none;
  align-items: center;
  justify-content: center;
}

.consent-title {
  flex: 1;
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  text-align: left;
  color: #2c3e50;
}

.consent-close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s;
}

.consent-close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Body */
.consent-modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.consent-action-info {
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
}

.consent-action-info h3 {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 8px 0;
  line-height: 1.2;
  text-align: left;
  width: 100%;
}

.consent-action-description {
  font-size: 14px;
  color: #7f8c8d;
  margin: 0;
  line-height: 1.4;
  text-align: left;
  width: 100%;
}

/* Consent text container */
.consent-text-container {
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.consent-text-scroll {
  max-height: 200px;
  overflow-y: auto;
}

.consent-text {
  font-size: 15px;
  line-height: 1.6;
  color: #2c3e50;
  margin: 0;
  white-space: pre-wrap;
}

/* Checkbox */
.consent-checkbox-container {
  margin-bottom: 16px;
}

.consent-checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  user-select: none;
}

.consent-checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
  margin-top: 2px;
  flex-shrink: 0;
}

.checkbox-text {
  font-size: 15px;
  color: #2c3e50;
  font-weight: 500;
  line-height: 1.5;
}

/* Info note */
.consent-info-note {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: #e3f2fd;
  border-left: 4px solid #2196f3;
  border-radius: 4px;
  font-size: 13px;
  color: #1565c0;
}

.consent-info-note i {
  font-size: 16px;
}

/* Footer */
.consent-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.consent-btn {
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

.consent-btn-cancel {
  background: white;
  color: #6c757d;
  border: 2px solid #dee2e6;
}

.consent-btn-cancel:hover {
  background: #f8f9fa;
  border-color: #adb5bd;
}

.consent-btn-accept {
  background: white;
  color: #2c3e50;
  border: 2px solid #dee2e6;
}

.consent-btn-accept:hover:not(:disabled) {
  background: #f8f9fa;
  border-color: #adb5bd;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.consent-btn-accept:disabled {
  background: white;
  color: #2c3e50;
  border: 2px solid #dee2e6;
  opacity: 1;
  cursor: not-allowed;
  transform: none;
}

/* Animations */
@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-50px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-active .consent-modal-container {
  animation: modalSlideIn 0.3s ease-out;
}

.modal-fade-leave-active .consent-modal-container {
  animation: modalSlideIn 0.3s ease-out reverse;
}

/* Scrollbar styling */
.consent-text-scroll::-webkit-scrollbar {
  width: 8px;
}

.consent-text-scroll::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.consent-text-scroll::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.consent-text-scroll::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
