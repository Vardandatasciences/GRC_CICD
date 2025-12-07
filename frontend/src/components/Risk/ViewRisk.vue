<template>
  <div class="risk-view-container">
    <PopupModal />
    
    <div class="risk-view-header">
      <h2 class="risk-view-title"><i class="fas fa-exclamation-triangle risk-view-icon"></i> Risk Details</h2>
      <div class="risk-view-header-actions">
        <button v-if="!isEditMode" class="risk-view-edit-button" @click="toggleEditMode">
          <i class="fas fa-edit"></i> Edit Risk
        </button>
        <button v-if="isEditMode" class="risk-view-save-button" @click="saveRisk" :disabled="isSaving">
          <i class="fas fa-save"></i> {{ isSaving ? 'Saving...' : 'Save Changes' }}
        </button>
        <button v-if="isEditMode" class="risk-view-cancel-button" @click="cancelEdit">
          <i class="fas fa-times"></i> Cancel
        </button>
        <button class="risk-view-back-button" @click="goBack">
          <i class="fas fa-arrow-left"></i> Back to Risk Register
        </button>
      </div>
    </div>

    <div class="risk-view-details-card" v-if="risk">
      <div class="risk-view-details-top">
        <div class="risk-view-id-section">
          <span class="risk-view-id-label">Risk ID:</span>
          <span class="risk-view-id-value">{{ risk.RiskId }}</span>
        </div>
        <div class="risk-view-meta">
          <div v-if="!isEditMode" class="risk-view-category">{{ risk.Category }}</div>
          <div v-if="!isEditMode" class="risk-view-criticality" :class="getCriticalityClass(risk.Criticality)">{{ risk.Criticality }}</div>
          
          <!-- Edit mode for category and criticality -->
          <div v-if="isEditMode" class="risk-view-edit-meta">
            <select v-model="editRisk.Category" class="risk-view-select">
              <option value="">Select Category</option>
              <option value="Operational">Operational</option>
              <option value="Financial">Financial</option>
              <option value="Technical">Technical</option>
              <option value="Strategic">Strategic</option>
              <option value="Compliance">Compliance</option>
              <option value="Reputational">Reputational</option>
            </select>
            <select v-model="editRisk.Criticality" class="risk-view-select">
              <option value="">Select Criticality</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </div>
        </div>
      </div>

      <div class="risk-view-title-section">
        <h3 v-if="!isEditMode">{{ risk.RiskTitle }}</h3>
        <input v-if="isEditMode" v-model="editRisk.RiskTitle" class="risk-view-title-input" placeholder="Enter risk title" />
        
        <div class="risk-view-compliance-section">
          <span class="risk-view-compliance-label">Compliance ID:</span>
          <span v-if="!isEditMode" class="risk-view-compliance-value">{{ risk.ComplianceId || 'N/A' }}</span>
          <input v-if="isEditMode" v-model="editRisk.ComplianceId" class="risk-view-compliance-input" placeholder="Enter compliance ID" />
        </div>
      </div>

      <div class="risk-view-content">
        <div class="risk-view-content-row">
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Risk Description:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.RiskDescription || 'N/A' }}</div>
            <textarea v-if="isEditMode" v-model="editRisk.RiskDescription" class="risk-view-textarea" placeholder="Enter risk description" rows="4"></textarea>
          </div>
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Business Impact:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.BusinessImpact || 'N/A' }}</div>
            <textarea v-if="isEditMode" v-model="editRisk.BusinessImpact" class="risk-view-textarea" placeholder="Enter business impact" rows="4"></textarea>
          </div>
        </div>

        <div class="risk-view-content-row">
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Possible Damage:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.PossibleDamage || 'N/A' }}</div>
            <textarea v-if="isEditMode" v-model="editRisk.PossibleDamage" class="risk-view-textarea" placeholder="Enter possible damage" rows="3"></textarea>
          </div>
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Risk Likelihood:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.RiskLikelihood || 'N/A' }}</div>
            <select v-if="isEditMode" v-model="editRisk.RiskLikelihood" class="risk-view-select">
              <option value="">Select Likelihood</option>
              <option value="Very Low">Very Low</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Very High">Very High</option>
            </select>
          </div>
        </div>

        <div class="risk-view-content-row">
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Risk Impact:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.RiskImpact || 'N/A' }}</div>
            <select v-if="isEditMode" v-model="editRisk.RiskImpact" class="risk-view-select">
              <option value="">Select Impact</option>
              <option value="Very Low">Very Low</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Very High">Very High</option>
            </select>
          </div>
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Risk Exposure Rating:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.RiskExposureRating || 'N/A' }}</div>
            <input v-if="isEditMode" v-model="editRisk.RiskExposureRating" class="risk-view-input" placeholder="Enter exposure rating" />
          </div>
        </div>

        <div class="risk-view-content-row">
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Risk Priority:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.RiskPriority || 'N/A' }}</div>
            <select v-if="isEditMode" v-model="editRisk.RiskPriority" class="risk-view-select">
              <option value="">Select Priority</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </div>
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Risk Mitigation:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.RiskMitigation || 'N/A' }}</div>
            <textarea v-if="isEditMode" v-model="editRisk.RiskMitigation" class="risk-view-textarea" placeholder="Enter risk mitigation" rows="3"></textarea>
          </div>
        </div>

        <div class="risk-view-content-row">
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Risk Type:</h4>
            <div v-if="!isEditMode" class="risk-view-section-content">{{ risk.RiskType || 'N/A' }}</div>
            <select v-if="isEditMode" v-model="editRisk.RiskType" class="risk-view-select">
              <option value="">Select Type</option>
              <option value="Internal">Internal</option>
              <option value="External">External</option>
              <option value="Emerging">Emerging</option>
              <option value="Systemic">Systemic</option>
            </select>
          </div>
          <div class="risk-view-content-column">
            <h4 class="risk-view-section-title">Created At:</h4>
            <div class="risk-view-section-content">{{ formatDate(risk.CreatedAt) }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="risk-view-no-data">
      Loading risk details or no risk found...
    </div>

    <!-- Success/Error Messages -->
    <div v-if="successMessage" class="risk-view-success-message">
      <i class="fas fa-check-circle"></i> {{ successMessage }}
    </div>
    <div v-if="errorMessage" class="risk-view-error-message">
      <i class="fas fa-exclamation-circle"></i> {{ errorMessage }}
    </div>
  </div>
</template>

<script>
import './ViewRisk.css'
import axios from 'axios'
import { PopupModal } from '@/modules/popup'
import { API_ENDPOINTS } from '../../config/api.js'

export default {
  name: 'ViewRisk',
  components: {
    PopupModal
  },
  data() {
    return {
      risk: null,
      editRisk: {},
      isEditMode: false,
      isSaving: false,
      originalRisk: {},
      successMessage: '',
      errorMessage: ''
    }
  },
  created() {
    this.fetchRiskDetails()
  },
  methods: {
    fetchRiskDetails() {
      const riskId = this.$route.params.id
      if (!riskId) {
        this.$router.push('/risk/riskregister-list')
        return
      }

      axios.get(API_ENDPOINTS.RISK(riskId))
        .then(response => {
          this.risk = response.data
          this.originalRisk = { ...response.data }
          this.editRisk = { ...response.data }
          // Send push notification when risk details are viewed
          this.sendPushNotification(this.risk)
        })
        .catch(error => {
          console.error('Error fetching risk details:', error)
          this.showError('Failed to load risk details')
          // Send push notification for error case
          this.sendPushNotification({
            RiskTitle: 'Error Loading Risk',
            message: `Failed to load risk details: ${error.message}`
          })
        })
    },

    toggleEditMode() {
      this.isEditMode = true
      this.editRisk = { ...this.risk }
      this.clearMessages()
    },

    cancelEdit() {
      this.isEditMode = false
      this.editRisk = { ...this.originalRisk }
      this.clearMessages()
    },

    async saveRisk() {
      if (!this.validateRisk()) {
        return
      }

      this.isSaving = true
      this.clearMessages()

      try {
        const response = await axios.put(API_ENDPOINTS.RISK(this.risk.RiskId), this.editRisk)
        
        this.risk = response.data
        this.originalRisk = { ...response.data }
        this.isEditMode = false
        
        this.showSuccess('Risk updated successfully!')
        
        // Send push notification for successful update
        this.sendPushNotification({
          title: 'Risk Updated',
          message: `Risk "${this.risk.RiskTitle}" has been successfully updated.`,
          category: 'risk',
          priority: 'medium',
          user_id: 'default_user'
        })
        
      } catch (error) {
        console.error('Error updating risk:', error)
        this.showError('Failed to update risk. Please try again.')
        
        // Send push notification for error
        this.sendPushNotification({
          title: 'Risk Update Failed',
          message: `Failed to update risk: ${error.response?.data?.error || error.message}`,
          category: 'risk',
          priority: 'high',
          user_id: 'default_user'
        })
      } finally {
        this.isSaving = false
      }
    },

    validateRisk() {
      if (!this.editRisk.RiskTitle || this.editRisk.RiskTitle.trim() === '') {
        this.showError('Risk title is required')
        return false
      }
      if (!this.editRisk.Category) {
        this.showError('Risk category is required')
        return false
      }
      if (!this.editRisk.Criticality) {
        this.showError('Risk criticality is required')
        return false
      }
      return true
    },

    showSuccess(message) {
      this.successMessage = message
      this.errorMessage = ''
      setTimeout(() => {
        this.successMessage = ''
      }, 5000)
    },

    showError(message) {
      this.errorMessage = message
      this.successMessage = ''
      setTimeout(() => {
        this.errorMessage = ''
      }, 5000)
    },

    clearMessages() {
      this.successMessage = ''
      this.errorMessage = ''
    },

    async sendPushNotification(riskData) {
      try {
        const notificationData = {
          title: riskData.title || 'Risk Details Viewed',
          message: riskData.message || `Risk "${riskData.RiskTitle || 'Untitled Risk'}" details have been viewed in the Risk module.`,
          category: riskData.category || 'risk',
          priority: riskData.priority || 'medium',
          user_id: riskData.user_id || 'default_user'
        };
        const response = await fetch(API_ENDPOINTS.PUSH_NOTIFICATION, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(notificationData)
        });
        if (response.ok) {
          console.log('Push notification sent successfully');
        } else {
          console.error('Failed to send push notification');
        }
      } catch (error) {
        console.error('Error sending push notification:', error);
      }
    },
    
    getCriticalityClass(criticality) {
      if (!criticality) return ''
      criticality = criticality.toLowerCase()
      if (criticality === 'critical') return 'risk-view-priority-critical'
      if (criticality === 'high') return 'risk-view-priority-high'
      if (criticality === 'medium') return 'risk-view-priority-medium'
      if (criticality === 'low') return 'risk-view-priority-low'
      return ''
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleDateString()
    },
    goBack() {
      this.$router.push('/risk/riskregister-list')
    }
  }
}
</script> 