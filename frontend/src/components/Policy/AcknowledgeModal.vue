<template>
  <div class="modal-overlay" @click.self="closeModal">
    <div class="modal-container">
      <div class="modal-header">
        <h2>Acknowledge Policy</h2>
        <button class="close-btn" @click="closeModal">&times;</button>
      </div>

      <div class="modal-body">
        <!-- Policy Information -->
        <div class="policy-info-section">
          <h3 class="policy-name">{{ acknowledgement.policy_name }}</h3>
          <span class="version-text">Version {{ acknowledgement.policy_version }}</span>
          <span class="assigned-date">Assigned: {{ formatDate(acknowledgement.assigned_at) }}</span>

          <div v-if="acknowledgement.due_date" class="policy-meta">
            <div class="meta-item" :class="{ 'overdue': acknowledgement.is_overdue }">
              <i class="icon-clock"></i>
              <span>Due: {{ formatDate(acknowledgement.due_date) }}</span>
              <span v-if="acknowledgement.is_overdue" class="overdue-label">(Overdue)</span>
            </div>
          </div>

          <div v-if="acknowledgement.description" class="policy-description">
            <p>{{ acknowledgement.description }}</p>
          </div>
        </div>

        <!-- Acknowledgement Form -->
        <div class="acknowledgement-form">
          <div class="form-section">
            <label class="checkbox-label-simple">
              <input type="checkbox" v-model="hasReadPolicy" />
              <span>I confirm that I have read and understood this policy</span>
            </label>
          </div>

          <div class="form-section">
            <label for="comments">Comments (Optional):</label>
            <textarea
              id="comments"
              v-model="comments"
              placeholder="Add any comments or acknowledgements..."
              class="form-textarea"
              rows="4"
            ></textarea>
            <!-- <span class="hint">Your comments will be recorded in the audit log</span> -->
          </div>

          <div v-if="!hasReadPolicy" class="warning-box">
            <!-- <i class="icon-warning"></i> -->
            <span>Please confirm that you have read the policy before acknowledging</span>
          </div>
        </div>

        <!-- Audit Information -->
        <!-- <div class="audit-info">
          <i class="icon-info"></i>
          <p>By acknowledging this policy, the following information will be recorded:</p>
          <ul>
            <li>Your user ID and name</li>
            <li>Date and time of acknowledgement</li>
            <li>IP address: {{ clientInfo.ip || 'Detecting...' }}</li>
            <li>Browser information</li>
          </ul>
        </div> -->
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="closeModal" :disabled="acknowledging">
          Cancel
        </button>
        <button 
          class="btn btn-primary" 
          @click="acknowledgePolicy" 
          :disabled="!hasReadPolicy || acknowledging"
        >
          <span v-if="acknowledging" class="spinner"></span>
          {{ acknowledging ? 'Acknowledging...' : 'Acknowledge Policy' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { API_ENDPOINTS } from '../../config/api'
import { PopupService } from '@/modules/popus/popupService'

export default {
  name: 'AcknowledgeModal',
  props: {
    acknowledgement: {
      type: Object,
      required: true
    }
  },
  emits: ['close', 'acknowledged'],
  setup(props, { emit }) {
    const hasReadPolicy = ref(false)
    const comments = ref('')
    const acknowledging = ref(false)
    const clientInfo = ref({
      ip: null,
      userAgent: navigator.userAgent
    })

    const getClientIP = async () => {
      try {
        // Try to get IP from ipify service
        const response = await axios.get('https://api.ipify.org?format=json')
        clientInfo.value.ip = response.data.ip
      } catch (error) {
        // Fallback - will be captured on backend
        clientInfo.value.ip = 'Unknown'
      }
    }

    const acknowledgePolicy = async () => {
      if (!hasReadPolicy.value) {
        PopupService.warning('Please confirm that you have read the policy', 'Confirmation Required')
        return
      }

      try {
        acknowledging.value = true

        const requestData = {
          comments: comments.value.trim() || null
        }

        const response = await axios.post(
          API_ENDPOINTS.ACKNOWLEDGE_POLICY_NEW(props.acknowledgement.acknowledgement_user_id),
          requestData
        )

        PopupService.success(
          'Thank you for acknowledging the policy. Your acknowledgement has been recorded.',
          'Policy Acknowledged'
        )

        // Emit with acknowledgement data including policy info
        emit('acknowledged', {
          ...response.data,
          policy_id: props.acknowledgement.policy_id,
          policy_name: props.acknowledgement.policy_name,
          acknowledgement_user_id: props.acknowledgement.acknowledgement_user_id
        })
      } catch (error) {
        console.error('Error acknowledging policy:', error)
        PopupService.error(
          error.response?.data?.error || 'Failed to acknowledge policy. Please try again.',
          'Error'
        )
      } finally {
        acknowledging.value = false
      }
    }

    const closeModal = () => {
      emit('close')
    }

    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }

    onMounted(() => {
      getClientIP()
    })

    return {
      hasReadPolicy,
      comments,
      acknowledging,
      clientInfo,
      acknowledgePolicy,
      closeModal,
      formatDate
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
  padding: 20px;
}

.modal-container {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 650px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #6b7280;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.policy-info-section {
  margin-bottom: 24px;
}

.policy-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #000000;
}

.version-text {
  display: block;
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 8px;
}

.assigned-date {
  display: block;
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 16px;
}

.policy-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  opacity: 0.9;
}

.meta-item.overdue {
  color: #000000;
  font-weight: 700;
}

.overdue-label {
  font-weight: 600;
}

.policy-description {
  padding-top: 16px;
  border-top: 1px solid #000000;
}

.policy-description p {
  margin: 0;
  line-height: 1.6;
  opacity: 0.95;
}

.acknowledgement-form {
  margin-bottom: 24px;
}

.form-section {
  margin-bottom: 20px;
}

.form-section label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.checkbox-label-simple {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: all 0.2s;
  width: 100%;
  padding: 0;
  background: transparent;
  border: none;
}

.checkbox-label-simple:hover {
  opacity: 0.8;
}

.checkbox-label-simple input[type="checkbox"] {
  cursor: pointer;
  width: 18px;
  height: 18px;
  accent-color: #000000;
  flex-shrink: 0;
  margin: 0;
}

.checkbox-label-simple span {
  font-size: 15px;
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
}

.form-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  transition: all 0.2s;
}

.form-textarea:focus {
  outline: none;
  border-color: #000000;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.1);
}

.hint {
  display: block;
  margin-top: 6px;
  font-size: 13px;
  color: #6b7280;
  font-style: italic;
}

.warning-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f5f5f5;
  border: 2px solid #000000;
  border-radius: 8px;
  color: #000000;
  font-size: 14px;
  font-weight: 500;
}

.audit-info {
  background: #f5f5f5;
  border: 2px solid #000000;
  border-radius: 8px;
  padding: 16px;
  color: #000000;
}

.audit-info i {
  margin-right: 8px;
}

.audit-info p {
  margin: 0 0 12px 0;
  font-weight: 500;
  font-size: 14px;
}

.audit-info ul {
  margin: 0;
  padding-left: 24px;
  font-size: 13px;
}

.audit-info li {
  margin-bottom: 6px;
}

.modal-footer {
  padding: 20px 24px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn {
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover:not(:disabled) {
  background: #f9fafb;
}

.btn-primary {
  background: #000000;
  color: white;
  border: 2px solid #000000;
}

.btn-primary:hover:not(:disabled) {
  background: #333333;
  border-color: #333333;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Icon styles */
.icon-calendar::before { content: '📅'; margin-right: 4px; }
.icon-clock::before { content: '🕐'; margin-right: 4px; }
.icon-warning::before { content: '⚠️'; }
.icon-info::before { content: 'ℹ️'; }
</style>

