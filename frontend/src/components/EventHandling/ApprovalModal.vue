<template>
  <div v-if="isOpen" class="approval-modal-overlay">
    <div class="approval-modal-container">
      <!-- Header -->
      <div class="approval-modal-header">
        <div class="approval-modal-title-section">
          <div class="approval-modal-icon-section">
            <component :is="config.icon" :class="`approval-modal-icon ${config.iconClass}`" />
          </div>
          <div class="approval-modal-title-content">
            <h2 class="approval-modal-title">
              {{ type === 'approve' ? 'Approve Event' : type === 'reject' ? 'Reject Event' : config.title }}
            </h2>
            <p class="approval-modal-subtitle">Event: {{ eventTitle }}</p>
          </div>
        </div>
        <button
          @click="$emit('cancel')"
          class="approval-modal-close-btn"
        >
          <svg class="approval-modal-close-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Content -->
      <div class="approval-modal-content">
        <div v-if="type === 'archive'" class="approval-modal-archive-section">
          <div class="approval-modal-archive-icon">
            <svg class="approval-modal-archive-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-14 0a2 2 0 012-2h10a2 2 0 012 2"></path>
            </svg>
          </div>
          <h3 class="approval-modal-archive-title">Archive Event</h3>
          <p class="approval-modal-archive-message">
            Are you sure you want to archive this event? Archived events will be moved to the Archived Events section and can be restored later if needed.
          </p>
        </div>

        <div v-else class="approval-modal-comment-section">
          <div class="approval-modal-comment-header">
            <h3 class="approval-modal-comment-title">
              {{ type === 'approve' ? 'Approval Comments' : 'Rejection Reason' }}
            </h3>
            <p class="approval-modal-comment-subtitle">
              {{ config.placeholder }}
            </p>
          </div>
          <div class="approval-modal-textarea-container">
            <textarea
              v-model="comment"
              :placeholder="config.placeholder"
              rows="4"
              class="approval-modal-textarea"
              :required="config.required"
            />
            <div v-if="config.required" class="approval-modal-required-indicator">
              <span class="approval-modal-required-text">Required</span>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="approval-modal-actions">
          <button
            @click="$emit('cancel')"
            class="approval-modal-btn approval-modal-btn-cancel"
          >
            <svg class="approval-modal-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
            Cancel
          </button>
          <button
            @click="handleSubmit"
            :disabled="config.required && !comment.trim()"
            :class="`approval-modal-btn ${config.buttonClass}`"
            :style="type === 'archive' ? 'background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); color: #ffffff;' : 'display: flex !important; visibility: visible !important;'"
          >
            <svg v-if="type === 'approve'" class="approval-modal-btn-icon" width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            <svg v-else-if="type === 'reject'" class="approval-modal-btn-icon" width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
            <svg v-else-if="type === 'archive'" class="approval-modal-btn-icon" width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-14 0a2 2 0 012-2h10a2 2 0 012 2"></path>
            </svg>
            <component v-else :is="config.icon" class="approval-modal-btn-icon" />
            {{ type === 'approve' ? 'Approve' : type === 'reject' ? 'Reject' : type === 'archive' ? 'Archive' : 'Submit' }}
          </button>
        </div>
      </div>

      <!-- Internal Success/Error Messages -->
      <div v-if="showSuccessMessage" class="approval-modal-message approval-modal-message-success">
        <div class="approval-modal-message-content">
          <div class="approval-modal-message-icon">
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
          </div>
          <div class="approval-modal-message-text">
            <h4 class="approval-modal-message-title">{{ messageTitle }}</h4>
            <p class="approval-modal-message-body">{{ messageText }}</p>
          </div>
          <button @click="hideMessages" class="approval-modal-message-close">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>

      <div v-if="showErrorMessage" class="approval-modal-message approval-modal-message-error">
        <div class="approval-modal-message-content">
          <div class="approval-modal-message-icon">
            <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </div>
          <div class="approval-modal-message-text">
            <h4 class="approval-modal-message-title">{{ messageTitle }}</h4>
            <p class="approval-modal-message-body">{{ messageText }}</p>
          </div>
          <button @click="hideMessages" class="approval-modal-message-close">
            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import PopupModal from '../../modules/popus/PopupModal.vue'

export default {
  name: 'ApprovalModal',
  components: {
    PopupModal
  },
  props: {
    isOpen: {
      type: Boolean,
      default: false
    },
    type: {
      type: String,
      required: true,
      validator: (value) => ['approve', 'reject', 'archive'].includes(value)
    },
    eventTitle: {
      type: String,
      required: true
    }
  },
  emits: ['submit', 'cancel'],
  expose: ['showSuccess', 'showError', 'hideMessages'],
  setup(props, { emit }) {
    const comment = ref('')
    const showSuccessMessage = ref(false)
    const showErrorMessage = ref(false)
    const messageText = ref('')
    const messageTitle = ref('')

    const config = computed(() => {
      switch (props.type) {
        case 'approve':
          return {
            title: 'Approve Event',
            icon: 'CheckIcon',
            iconClass: 'approval-modal-icon-approve',
            buttonClass: 'approval-modal-btn-approve',
            placeholder: 'Add comments (optional)',
            required: false
          }
        case 'reject':
          return {
            title: 'Reject Event',
            icon: 'XIcon',
            iconClass: 'approval-modal-icon-reject',
            buttonClass: 'approval-modal-btn-reject',
            placeholder: 'Reason for rejection (required)',
            required: true
          }
        case 'archive':
          return {
            title: 'Archive Event',
            icon: 'ArchiveIcon',
            iconClass: 'approval-modal-icon-archive',
            buttonClass: 'approval-modal-btn-archive',
            placeholder: '',
            required: false
          }
        default:
          return {}
      }
    })

    // Icon components
    const CheckIcon = {
      template: '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>'
    }

    const XIcon = {
      template: '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>'
    }

    const ArchiveIcon = {
      template: '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-14 0a2 2 0 012-2h10a2 2 0 012 2"></path></svg>'
    }

    const showSuccess = (message, title = 'Success') => {
      messageText.value = message
      messageTitle.value = title
      showSuccessMessage.value = true
      showErrorMessage.value = false
    }

    const showError = (message, title = 'Error') => {
      messageText.value = message
      messageTitle.value = title
      showErrorMessage.value = true
      showSuccessMessage.value = false
    }

    const hideMessages = () => {
      showSuccessMessage.value = false
      showErrorMessage.value = false
    }

    const handleSubmit = () => {
      if (props.type === 'reject' && !comment.value.trim()) {
        return // Reject requires a reason
      }
      emit('submit', comment.value)
      comment.value = ''
    }

    return {
      comment,
      config,
      CheckIcon,
      XIcon,
      ArchiveIcon,
      handleSubmit,
      showSuccessMessage,
      showErrorMessage,
      messageText,
      messageTitle,
      showSuccess,
      showError,
      hideMessages
    }
  }
}
</script>

<style>
/* Global modal isolation */
.approval-modal-overlay * {
  box-sizing: border-box !important;
}

/* Approval Modal Overlay */
.approval-modal-overlay {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  background: rgba(0, 0, 0, 0.5) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: 9999 !important;
  backdrop-filter: blur(4px) !important;
  animation: approval-modal-fadeIn 0.3s ease-out !important;
  isolation: isolate !important;
}

/* Approval Modal Container */
.approval-modal-container {
  background: #ffffff !important;
  border-radius: 16px !important;
  box-shadow: 0 20px 25px rgba(0, 0, 0, 0.15), 0 10px 10px rgba(0, 0, 0, 0.04) !important;
  max-width: 500px !important;
  width: 90% !important;
  max-height: 90vh !important;
  overflow-y: auto !important;
  margin: 20px !important;
  animation: approval-modal-slideIn 0.4s ease-out !important;
  position: relative !important;
  z-index: 10000 !important;
  isolation: isolate !important;
}

/* Approval Modal Header */
.approval-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-radius: 16px 16px 0 0;
}

.approval-modal-title-section {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.approval-modal-icon-section {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  flex-shrink: 0;
}

.approval-modal-icon {
  width: 24px;
  height: 24px;
  stroke-width: 2.5;
}

.approval-modal-icon-approve {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  color: #155724;
}

.approval-modal-icon-reject {
  background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
  color: #721c24;
}

.approval-modal-icon-archive {
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e0 100%);
  color: #4a5568;
}

.approval-modal-title-content {
  flex: 1;
}

.approval-modal-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 4px 0;
  line-height: 1.3;
}

.approval-modal-subtitle {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0;
  font-weight: 500;
}

.approval-modal-close-btn {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.approval-modal-close-btn:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.approval-modal-close-icon {
  width: 24px;
  height: 24px;
}

/* Approval Modal Content */
.approval-modal-content {
  padding: 32px;
  background: #ffffff;
}

/* Archive Section */
.approval-modal-archive-section {
  text-align: center;
  padding: 24px 0;
}

.approval-modal-archive-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e0 100%);
  border-radius: 16px;
}

.approval-modal-archive-svg {
  width: 32px;
  height: 32px;
  color: #4a5568;
}

.approval-modal-archive-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 12px 0;
}

.approval-modal-archive-message {
  font-size: 0.95rem;
  color: #6b7280;
  line-height: 1.6;
  margin: 0;
}

/* Comment Section */
.approval-modal-comment-section {
  margin-bottom: 24px;
}

.approval-modal-comment-header {
  margin-bottom: 16px;
}

.approval-modal-comment-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 4px 0;
}

.approval-modal-comment-subtitle {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0;
}

.approval-modal-textarea-container {
  position: relative;
}

.approval-modal-textarea {
  width: 100%;
  padding: 16px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 0.95rem;
  color: #374151;
  background: #ffffff;
  transition: all 0.3s ease;
  resize: vertical;
  min-height: 120px;
  font-family: inherit;
}

.approval-modal-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.approval-modal-textarea::placeholder {
  color: #9ca3af;
  font-style: italic;
}

.approval-modal-required-indicator {
  position: absolute;
  top: -8px;
  right: 12px;
  background: #ffffff;
  padding: 0 8px;
}

.approval-modal-required-text {
  font-size: 0.75rem;
  font-weight: 600;
  color: #ef4444;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Approval Modal Actions */
.approval-modal-actions {
  display: flex !important;
  align-items: center;
  gap: 12px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
  visibility: visible !important;
  opacity: 1 !important;
}

.approval-modal-btn {
  display: inline-flex !important;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  flex: 1;
  justify-content: center;
  visibility: visible !important;
  opacity: 1 !important;
}

.approval-modal-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.approval-modal-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.approval-modal-btn-icon {
  width: 16px;
  height: 16px;
  stroke-width: 2.5;
}

/* Button Variants */
.approval-modal-btn-cancel {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  color: #374151;
  border: 1px solid #d1d5db;
}

.approval-modal-btn-cancel:hover {
  background: linear-gradient(135deg, #e5e7eb 0%, #d1d5db 100%);
}

.approval-modal-btn-approve {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
  color: #ffffff !important;
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.approval-modal-btn-approve:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

.approval-modal-btn-reject {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
  color: #ffffff !important;
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.approval-modal-btn-reject:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
}

.approval-modal-btn-archive {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%) !important;
  color: #ffffff !important;
  border: none !important;
  font-weight: 600 !important;
  text-shadow: none !important;
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.approval-modal-container .approval-modal-btn-archive {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%) !important;
  color: #ffffff !important;
}

.approval-modal-btn-archive:hover {
  background: linear-gradient(135deg, #4b5563 0%, #374151 100%) !important;
  color: #ffffff !important;
}

.approval-modal-btn-archive:focus {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%) !important;
  color: #ffffff !important;
  outline: 2px solid #3b82f6 !important;
  outline-offset: 2px !important;
}

/* Animations */
@keyframes approval-modal-fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes approval-modal-slideIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .approval-modal-container {
    width: 95%;
    margin: 10px;
    max-height: 95vh;
  }
  
  .approval-modal-header {
    padding: 20px;
  }
  
  .approval-modal-title {
    font-size: 1.3rem;
  }
  
  .approval-modal-content {
    padding: 20px;
  }
  
  .approval-modal-actions {
    flex-direction: column;
    gap: 12px;
  }
  
  .approval-modal-btn {
    width: 100%;
  }
  
  .approval-modal-title-section {
    gap: 12px;
  }
  
  .approval-modal-icon-section {
    width: 40px;
    height: 40px;
  }
  
  .approval-modal-icon {
    width: 20px;
    height: 20px;
  }
}

/* Focus states for accessibility */
.approval-modal-btn:focus,
.approval-modal-close-btn:focus,
.approval-modal-textarea:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Scrollbar styling */
.approval-modal-container::-webkit-scrollbar {
  width: 8px;
}

.approval-modal-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.approval-modal-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.approval-modal-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Force button visibility - Debug styles */
.approval-modal-actions button {
  display: inline-flex !important;
  visibility: visible !important;
  opacity: 1 !important;
  min-width: 100px !important;
  min-height: 40px !important;
}

.approval-modal-actions button[class*="approve"] {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
  color: #ffffff !important;
}

.approval-modal-actions button[class*="reject"] {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
  color: #ffffff !important;
}

.approval-modal-actions button[class*="archive"] {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%) !important;
  color: #ffffff !important;
}

/* Internal Message Styles */
.approval-modal-message {
  position: absolute;
  top: 20px;
  left: 20px;
  right: 20px;
  z-index: 10001;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: approval-modal-message-slideIn 0.3s ease-out;
}

.approval-modal-message-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-radius: 12px;
}

.approval-modal-message-success {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  border: 1px solid #c3e6cb;
}

.approval-modal-message-error {
  background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
  border: 1px solid #f5c6cb;
}

.approval-modal-message-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
}

.approval-modal-message-success .approval-modal-message-icon {
  background: #28a745;
  color: #ffffff;
}

.approval-modal-message-error .approval-modal-message-icon {
  background: #dc3545;
  color: #ffffff;
}

.approval-modal-message-text {
  flex: 1;
}

.approval-modal-message-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: #155724;
}

.approval-modal-message-error .approval-modal-message-title {
  color: #721c24;
}

.approval-modal-message-body {
  font-size: 0.9rem;
  margin: 0;
  color: #155724;
  line-height: 1.4;
}

.approval-modal-message-error .approval-modal-message-body {
  color: #721c24;
}

.approval-modal-message-close {
  background: none;
  border: none;
  color: #6c757d;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.approval-modal-message-close:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #495057;
}

@keyframes approval-modal-message-slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
