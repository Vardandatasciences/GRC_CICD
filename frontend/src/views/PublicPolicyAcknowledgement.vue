<template>
  <div class="public-acknowledgement-container">
    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Loading policy details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <div class="error-icon">⚠️</div>
      <h2>Unable to Load Policy</h2>
      <p>{{ error }}</p>
      <p class="error-hint">This link may have expired or is invalid.</p>
    </div>

    <!-- Already Acknowledged State -->
    <div v-else-if="alreadyAcknowledged" class="content-container">
      <!-- Header -->
      <div class="header">
        <div class="logo">
          <h1>🛡️ GRC Policy Management</h1>
        </div>
        <div class="user-info" v-if="userData">
          <p><strong>Hello,</strong> {{ userData.user_name }}</p>
          <p class="email">{{ userData.email }}</p>
        </div>
      </div>

      <!-- Success Card -->
      <div class="policy-card acknowledged-card">
        <div class="acknowledged-header">
          <div class="success-icon-large">✅</div>
          <h2>Policy Already Acknowledged</h2>
          <p class="acknowledged-message">You have successfully acknowledged this policy.</p>
        </div>

        <div class="acknowledged-details">
          <div class="detail-section">
            <h3>Acknowledgement Details</h3>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">Policy Name:</span>
                <span class="detail-value">{{ policyData?.policy_name || 'N/A' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Version:</span>
                <span class="detail-value">{{ policyData?.policy_version || 'N/A' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Acknowledged At:</span>
                <span class="detail-value">{{ formatDate(acknowledgedAt) }}</span>
              </div>
              <div class="detail-item" v-if="requestData?.title">
                <span class="detail-label">Request Title:</span>
                <span class="detail-value">{{ requestData.title }}</span>
              </div>
            </div>
          </div>

          <div class="info-note">
            <p><strong>✓ Your acknowledgement has been recorded in the system.</strong></p>
            <p>This acknowledgement will appear in the acknowledgement reports and audit logs.</p>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="footer">
        <p>© 2025 GRC Policy Management System. This is a secure policy acknowledgement page.</p>
        <p class="security-note">🔒 This link is unique to you and should not be shared.</p>
      </div>
    </div>

    <!-- Main Content - Policy Details and Acknowledgement -->
    <div v-else-if="policyData" class="content-container">
      <!-- Header -->
      <div class="header">
        <div class="logo">
          <h1>🛡️ GRC Policy Management</h1>
        </div>
        <div class="user-info">
          <p><strong>Hello,</strong> {{ userData?.user_name }}</p>
          <p class="email">{{ userData?.email }}</p>
        </div>
      </div>

      <!-- Policy Information Card -->
      <div class="policy-card">
        <div class="policy-header">
          <h2>{{ requestData?.title }}</h2>
          <span class="status-badge" :class="statusClass">{{ status }}</span>
        </div>

        <div class="policy-meta">
          <div class="meta-item">
            <span class="meta-label">Policy Name:</span>
            <span class="meta-value">{{ policyData.policy_name }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Version:</span>
            <span class="meta-value">{{ policyData.policy_version }}</span>
          </div>
          <div class="meta-item" v-if="requestData?.due_date">
            <span class="meta-label">Due Date:</span>
            <span class="meta-value" :class="{ 'overdue': isOverdue }">
              {{ formatDate(requestData.due_date) }}
              <span v-if="isOverdue" class="overdue-badge">OVERDUE</span>
            </span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Assigned:</span>
            <span class="meta-value">{{ formatDate(assignedAt) }}</span>
          </div>
        </div>

        <div class="policy-description" v-if="requestData?.description">
          <h3>Request Details</h3>
          <p>{{ requestData.description }}</p>
        </div>

        <!-- Policy Content -->
        <div class="policy-content">
          <h3>Policy Information</h3>
          
          <div class="policy-section" v-if="policyData.policy_description">
            <h4>Description</h4>
            <p>{{ policyData.policy_description }}</p>
          </div>

          <div class="policy-section" v-if="policyData.policy_objective">
            <h4>Objective</h4>
            <p>{{ policyData.policy_objective }}</p>
          </div>

          <div class="policy-dates" v-if="policyData.effective_date || policyData.review_date">
            <div v-if="policyData.effective_date">
              <strong>Effective Date:</strong> {{ formatDate(policyData.effective_date) }}
            </div>
            <div v-if="policyData.review_date">
              <strong>Review Date:</strong> {{ formatDate(policyData.review_date) }}
            </div>
          </div>
        </div>

        <!-- Acknowledgement Section -->
        <div class="acknowledgement-section">
          <h3>Acknowledgement</h3>
          <p class="acknowledgement-text">
            By acknowledging this policy, you confirm that you have read, understood, and agree to comply with the policy requirements.
          </p>

          <!-- Comments Field -->
          <div class="form-group">
            <label for="comments">Comments (Optional)</label>
            <textarea
              id="comments"
              v-model="comments"
              rows="4"
              placeholder="Add any comments or questions about this policy..."
              :disabled="submitting"
            ></textarea>
          </div>

          <!-- Acknowledgement Button -->
          <button
            class="acknowledge-button"
            @click="acknowledgePolicy"
            :disabled="submitting"
          >
            <span v-if="submitting">
              <div class="button-spinner"></div>
              Submitting...
            </span>
            <span v-else>
              ✓ I Acknowledge This Policy
            </span>
          </button>

          <p class="disclaimer">
            This acknowledgement will be recorded with your IP address and timestamp for audit purposes.
          </p>
        </div>
      </div>

      <!-- Footer -->
      <div class="footer">
        <p>© 2025 GRC Policy Management System. This is a secure policy acknowledgement page.</p>
        <p class="security-note">🔒 This link is unique to you and should not be shared.</p>
      </div>
    </div>

    <!-- Success Modal -->
    <div v-if="showSuccessModal" class="modal-overlay" @click="closeSuccessModal">
      <div class="modal-content success-modal" @click.stop>
        <div class="success-icon-large">✅</div>
        <h2>Policy Acknowledged Successfully!</h2>
        <p>Your acknowledgement has been recorded and saved to the database.</p>
        <div class="success-details">
          <p><strong>Policy:</strong> {{ policyData?.policy_name }}</p>
          <p><strong>Version:</strong> {{ policyData?.policy_version }}</p>
          <p><strong>Acknowledged At:</strong> {{ formatDate(acknowledgementTime) }}</p>
        </div>
        <p style="margin-top: 20px; color: #666; font-size: 14px;">
          This acknowledgement will appear in the acknowledgement reports.
        </p>
        <button class="modal-close-button" @click="closeSuccessModal">Close</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { API_BASE_URL } from '../config/api.js'

export default {
  name: 'PublicPolicyAcknowledgement',
  
  setup() {
    const route = useRoute()
    const token = ref(route.params.token)
    
    // State
    const loading = ref(true)
    const error = ref(null)
    const policyData = ref(null)
    const requestData = ref(null)
    const userData = ref(null)
    const status = ref('')
    const assignedAt = ref(null)
    const isOverdue = ref(false)
    const acknowledgementUserId = ref(null)
    const alreadyAcknowledged = ref(false)
    const acknowledgedAt = ref(null)
    
    // Form state
    const comments = ref('')
    const submitting = ref(false)
    const showSuccessModal = ref(false)
    const acknowledgementTime = ref(null)
    
    // Computed
    const statusClass = computed(() => {
      return status.value === 'Pending' ? 'status-pending' : 
             status.value === 'Overdue' ? 'status-overdue' : 
             'status-acknowledged'
    })
    
    // Methods
    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
    
    const loadAcknowledgementData = async () => {
      try {
        loading.value = true
        error.value = null
        
        // URL encode the token to handle special characters
        const encodedToken = encodeURIComponent(token.value)
        const apiUrl = `${API_BASE_URL}/api/policy-acknowledgements/public/${encodedToken}/`
        
        console.log('Loading acknowledgement data...')
        console.log('Token:', token.value)
        console.log('API Base URL:', API_BASE_URL)
        console.log('API URL:', apiUrl)
        
        const response = await axios.get(apiUrl)
        
        if (response.data.success) {
          if (response.data.already_acknowledged) {
            alreadyAcknowledged.value = true
            acknowledgedAt.value = response.data.acknowledged_at
            // Also load the policy data for display
            if (response.data.data) {
              const data = response.data.data
              policyData.value = data.policy
              requestData.value = data.request
              userData.value = data.user
              status.value = data.status
              assignedAt.value = data.assigned_at
              isOverdue.value = data.is_overdue
            }
          } else {
            const data = response.data.data
            policyData.value = data.policy
            requestData.value = data.request
            userData.value = data.user
            status.value = data.status
            assignedAt.value = data.assigned_at
            isOverdue.value = data.is_overdue
            acknowledgementUserId.value = data.acknowledgement_user_id
          }
        } else {
          error.value = response.data.error || 'Failed to load policy details'
        }
      } catch (err) {
        console.error('Error loading acknowledgement data:', err)
        console.error('Error response:', err.response)
        console.error('Error data:', err.response?.data)
        
        // Show more detailed error message
        const errorMessage = err.response?.data?.error || 
                           err.response?.data?.debug_error ||
                           err.message || 
                           'Invalid or expired acknowledgement link'
        
        error.value = errorMessage
        
        // Log debug info if available
        if (err.response?.data?.debug_info) {
          console.log('Debug info:', err.response.data.debug_info)
        }
      } finally {
        loading.value = false
      }
    }
    
    const acknowledgePolicy = async () => {
      if (submitting.value) return
      
      try {
        submitting.value = true
        
        // URL encode the token
        const encodedToken = encodeURIComponent(token.value)
        const apiUrl = `${API_BASE_URL}/api/policy-acknowledgements/public/${encodedToken}/acknowledge/`
        
        const response = await axios.post(apiUrl, {
          comments: comments.value
        })
        
        if (response.data.success) {
          acknowledgementTime.value = response.data.acknowledged_at
          showSuccessModal.value = true
          
          // Reload the data to get updated status
          await loadAcknowledgementData()
          
          // Keep success modal open for 5 seconds, then close
          setTimeout(() => {
            showSuccessModal.value = false
          }, 5000)
        }
      } catch (err) {
        console.error('Error acknowledging policy:', err)
        
        // Handle already acknowledged case gracefully
        if (err.response?.status === 400 && err.response?.data?.error?.includes('already been acknowledged')) {
          // Reload data to show already acknowledged state
          await loadAcknowledgementData()
          // Show success message since it was already acknowledged
          acknowledgementTime.value = err.response.data.acknowledged_at
          showSuccessModal.value = true
          setTimeout(() => {
            showSuccessModal.value = false
          }, 5000)
        } else {
          alert(err.response?.data?.error || 'Failed to acknowledge policy. Please try again.')
        }
      } finally {
        submitting.value = false
      }
    }
    
    const closeSuccessModal = async () => {
      showSuccessModal.value = false
      // Reload data to show the acknowledged state
      await loadAcknowledgementData()
    }
    
    // Lifecycle
    onMounted(() => {
      loadAcknowledgementData()
    })
    
    return {
      loading,
      error,
      policyData,
      requestData,
      userData,
      status,
      statusClass,
      assignedAt,
      isOverdue,
      alreadyAcknowledged,
      acknowledgedAt,
      comments,
      submitting,
      showSuccessModal,
      acknowledgementTime,
      formatDate,
      acknowledgePolicy,
      closeSuccessModal
    }
  }
}
</script>

<style scoped>
.public-acknowledgement-container {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  width: 100%;
  margin: 0;
}

/* Loading State */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  color: #333;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error State */
.error-container {
  max-width: 800px;
  margin: 50px auto;
  background: white;
  padding: 40px;
  border: 1px solid #ddd;
  text-align: center;
}

.error-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.error-hint {
  color: #666;
  font-size: 14px;
  margin-top: 10px;
}

/* Already Acknowledged State */
.acknowledged-card {
  margin-top: 0;
}

.acknowledged-header {
  text-align: center;
  padding: 40px 20px;
  border-bottom: 2px solid #e0e0e0;
  margin-bottom: 30px;
}

.success-icon-large {
  font-size: 48px;
  margin-bottom: 20px;
  display: block;
}

.acknowledged-header h2 {
  font-size: 28px;
  color: #333;
  margin: 0 0 10px 0;
  font-weight: 600;
}

.acknowledged-message {
  font-size: 16px;
  color: #666;
  margin: 0;
}

.acknowledged-details {
  padding: 0 20px 30px 20px;
}

.detail-section {
  margin-bottom: 30px;
}

.detail-section h3 {
  font-size: 18px;
  color: #333;
  margin-bottom: 20px;
  font-weight: 600;
  border-bottom: 2px solid #333;
  padding-bottom: 8px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  padding: 15px;
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
}

.detail-label {
  font-size: 11px;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 6px;
  font-weight: 600;
}

.detail-value {
  font-size: 16px;
  color: #333;
  font-weight: 500;
}

.info-note {
  background: #e8f5e9;
  border: 1px solid #4caf50;
  padding: 20px;
  margin-top: 30px;
}

.info-note p {
  margin: 8px 0;
  color: #2e7d32;
  font-size: 14px;
  line-height: 1.6;
}

.info-note p:first-child {
  font-weight: 600;
  font-size: 15px;
}

/* Main Content */
.content-container {
  width: 100%;
  max-width: 100%;
  margin: 0;
  padding: 0;
}

.header {
  background: #fff;
  padding: 20px 40px;
  border-bottom: 2px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.logo h1 {
  font-size: 22px;
  margin: 0;
  color: #333;
  font-weight: 600;
}

.user-info {
  text-align: right;
}

.user-info p {
  margin: 4px 0;
}

.user-info .email {
  font-size: 14px;
  color: #666;
}

/* Policy Card */
.policy-card {
  background: white;
  padding: 40px;
  width: 100%;
  max-width: 100%;
  border-top: 1px solid #e0e0e0;
}

.policy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f0f0f0;
}

.policy-header h2 {
  margin: 0;
  color: #333;
  font-size: 24px;
  font-weight: 600;
}

.status-badge {
  padding: 6px 14px;
  border: 1px solid #ddd;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-pending {
  background: #fff;
  color: #856404;
  border-color: #ffc107;
}

.status-overdue {
  background: #fff;
  color: #721c24;
  border-color: #dc3545;
}

.status-acknowledged {
  background: #fff;
  color: #155724;
  border-color: #28a745;
}

/* Policy Meta */
.policy-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
  padding: 25px;
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
}

.meta-item {
  display: flex;
  flex-direction: column;
}

.meta-label {
  font-size: 11px;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 6px;
  font-weight: 600;
}

.meta-value {
  font-size: 15px;
  color: #333;
  font-weight: 500;
}

.overdue {
  color: #dc3545;
}

.overdue-badge {
  background: #dc3545;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  margin-left: 8px;
}

/* Policy Content */
.policy-description,
.policy-content {
  margin-bottom: 30px;
}

.policy-description h3,
.policy-content h3 {
  color: #333;
  font-size: 18px;
  margin-bottom: 15px;
  font-weight: 600;
  border-bottom: 2px solid #333;
  padding-bottom: 8px;
}

.policy-section {
  margin-bottom: 20px;
}

.policy-section h4 {
  color: #333;
  font-size: 15px;
  margin-bottom: 10px;
  font-weight: 600;
}

.policy-section p {
  color: #555;
  line-height: 1.8;
  font-size: 14px;
}

.policy-dates {
  padding: 20px;
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  margin-top: 20px;
}

.policy-dates div {
  margin: 8px 0;
}

/* Acknowledgement Section */
.acknowledgement-section {
  background: #f8f9fa;
  padding: 30px;
  border: 1px solid #e0e0e0;
  border-left: 4px solid #333;
  margin-top: 30px;
}

.acknowledgement-section h3 {
  color: #333;
  margin-bottom: 15px;
  font-size: 18px;
  font-weight: 600;
}

.acknowledgement-text {
  color: #555;
  line-height: 1.6;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 2px solid #dee2e6;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.3s;
}

.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
}

.acknowledge-button {
  width: 100%;
  padding: 16px;
  background: #333;
  color: white;
  border: 2px solid #333;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.acknowledge-button:hover:not(:disabled) {
  background: #000;
  border-color: #000;
}

.acknowledge-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.button-spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.disclaimer {
  font-size: 12px;
  color: #666;
  text-align: center;
  margin-top: 12px;
}

/* Footer */
.footer {
  background: #fff;
  padding: 20px 40px;
  border-top: 1px solid #e0e0e0;
  text-align: center;
  color: #666;
  font-size: 13px;
  width: 100%;
}

.security-note {
  color: #333;
  font-weight: 600;
  margin-top: 8px;
}

/* Success Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: white;
  padding: 40px;
  border: 1px solid #ddd;
  max-width: 500px;
  text-align: center;
  animation: slideUp 0.3s;
}

@keyframes slideUp {
  from {
    transform: translateY(50px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.success-icon-large {
  font-size: 48px;
  margin-bottom: 20px;
  animation: scaleIn 0.5s;
}

@keyframes scaleIn {
  from {
    transform: scale(0);
  }
  to {
    transform: scale(1);
  }
}

.success-details {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin: 20px 0;
  text-align: left;
}

.success-details p {
  margin: 8px 0;
}

.modal-close-button {
  padding: 12px 32px;
  background: #333;
  color: white;
  border: 2px solid #333;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.modal-close-button:hover {
  background: #000;
  border-color: #000;
}

/* Responsive Design */
@media (max-width: 768px) {
  .header {
    flex-direction: column;
    gap: 16px;
    padding: 20px;
  }

  .user-info {
    text-align: center;
  }

  .policy-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .policy-meta {
    grid-template-columns: 1fr;
  }

  .policy-card {
    padding: 20px;
  }

  .acknowledgement-section {
    padding: 20px;
  }
}
</style>

