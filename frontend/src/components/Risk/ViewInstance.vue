<template>
  <div class="instance-view-container">
    <PopupModal />
    
    <div class="instance-view-header">
      <h2 class="instance-view-title">Risk Instance Details</h2>
      <div class="instance-view-header-actions">
        <button v-if="!isEditMode" class="instance-view-edit-button" @click="toggleEditMode">
          <i class="fas fa-edit"></i> Edit Instance
        </button>
        <button v-if="isEditMode" class="instance-view-save-button" @click="saveInstance" :disabled="isSaving">
          <i class="fas fa-save"></i> {{ isSaving ? 'Saving...' : 'Save Changes' }}
        </button>
        <button v-if="isEditMode" class="instance-view-cancel-button" @click="cancelEdit">
          <i class="fas fa-times"></i> Cancel
        </button>
        <button class="instance-view-back-button" @click="goBack">
          <i class="fas fa-arrow-left"></i> Back to Risk Instances
        </button>
      </div>
    </div>

    <div class="instance-view-details-card" v-if="instance">
      <div class="instance-view-details-header">
        <div class="instance-view-id-section">
          <span class="instance-view-id-label">Risk ID:</span>
          <span class="instance-view-id-value">{{ instance.RiskId }}</span>
          <span class="instance-view-id-label">Instance ID:</span>
          <span class="instance-view-id-value">{{ instance.RiskInstanceId }}</span>
        </div>
        <div class="instance-view-meta">
          <div class="instance-view-meta-item">
            <span class="instance-view-origin-badge">MANUAL</span>
          </div>
          <div class="instance-view-meta-item">
            <span v-if="!isEditMode" class="instance-view-category-badge">{{ instance.Category }}</span>
            <select v-if="isEditMode" v-model="editInstance.Category" class="instance-view-select">
              <option value="">Select Category</option>
              <option value="Operational">Operational</option>
              <option value="Financial">Financial</option>
              <option value="Technical">Technical</option>
              <option value="Strategic">Strategic</option>
              <option value="Compliance">Compliance</option>
              <option value="Reputational">Reputational</option>
            </select>
          </div>
          <div class="instance-view-meta-item">
            <span v-if="!isEditMode" :class="'instance-view-priority-' + instance.Criticality.toLowerCase()">
              {{ instance.Criticality }}
            </span>
            <select v-if="isEditMode" v-model="editInstance.Criticality" class="instance-view-select">
              <option value="">Select Criticality</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </div>
          <div class="instance-view-meta-item">
            <span v-if="!isEditMode" :class="'instance-view-status-' + (instance.RiskStatus ? instance.RiskStatus.toLowerCase().replace(/\s+/g, '-') : 'open')">
              {{ instance.RiskStatus || 'Open' }}
            </span>
            <select v-if="isEditMode" v-model="editInstance.RiskStatus" class="instance-view-select">
              <option value="">Select Status</option>
              <option value="Open">Open</option>
              <option value="In Progress">In Progress</option>
              <option value="Mitigated">Mitigated</option>
              <option value="Closed">Closed</option>
              <option value="Transferred">Transferred</option>
            </select>
          </div>
        </div>
      </div>

      <div class="instance-view-content">
        <div class="instance-view-content-row">
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Description:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskDescription || 'Not specified' }}</div>
            <textarea v-if="isEditMode" v-model="editInstance.RiskDescription" class="instance-view-textarea" placeholder="Enter risk description" rows="4"></textarea>
          </div>
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Category:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.Category || 'Not specified' }}</div>
            <input v-if="isEditMode" v-model="editInstance.Category" class="instance-view-input" placeholder="Enter category" readonly />
          </div>
        </div>

        <div class="instance-view-content-row">
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Criticality:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.Criticality || 'Not specified' }}</div>
            <input v-if="isEditMode" v-model="editInstance.Criticality" class="instance-view-input" placeholder="Enter criticality" readonly />
          </div>
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Status:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskStatus || 'Open' }}</div>
            <input v-if="isEditMode" v-model="editInstance.RiskStatus" class="instance-view-input" placeholder="Enter status" readonly />
          </div>
        </div>

        <div class="instance-view-content-row">
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Possible Damage:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.PossibleDamage || 'Not specified' }}</div>
            <textarea v-if="isEditMode" v-model="editInstance.PossibleDamage" class="instance-view-textarea" placeholder="Enter possible damage" rows="3"></textarea>
          </div>
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Risk Appetite:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.Appetite || 'Not specified' }}</div>
            <input v-if="isEditMode" v-model="editInstance.Appetite" class="instance-view-input" placeholder="Enter risk appetite" />
          </div>
        </div>

        <div class="instance-view-content-row">
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Likelihood:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskLikelihood || 'Not specified' }}</div>
            <select v-if="isEditMode" v-model="editInstance.RiskLikelihood" class="instance-view-select">
              <option value="">Select Likelihood</option>
              <option value="Very Low">Very Low</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Very High">Very High</option>
            </select>
          </div>
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Impact:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskImpact || 'Not specified' }}</div>
            <select v-if="isEditMode" v-model="editInstance.RiskImpact" class="instance-view-select">
              <option value="">Select Impact</option>
              <option value="Very Low">Very Low</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Very High">Very High</option>
            </select>
          </div>
        </div>

        <div class="instance-view-content-row">
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Exposure Rating:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskExposureRating || 'Not specified' }}</div>
            <input v-if="isEditMode" v-model="editInstance.RiskExposureRating" class="instance-view-input" placeholder="Enter exposure rating" />
          </div>
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Priority:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskPriority || 'Not specified' }}</div>
            <select v-if="isEditMode" v-model="editInstance.RiskPriority" class="instance-view-select">
              <option value="">Select Priority</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>
          </div>
        </div>

        <div class="instance-view-content-row">
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Response Type:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskResponseType || 'Not specified' }}</div>
            <select v-if="isEditMode" v-model="editInstance.RiskResponseType" class="instance-view-select">
              <option value="">Select Response Type</option>
              <option value="Accept">Accept</option>
              <option value="Avoid">Avoid</option>
              <option value="Mitigate">Mitigate</option>
              <option value="Transfer">Transfer</option>
            </select>
          </div>
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Response Description:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskResponseDescription || 'Not specified' }}</div>
            <textarea v-if="isEditMode" v-model="editInstance.RiskResponseDescription" class="instance-view-textarea" placeholder="Enter response description" rows="3"></textarea>
          </div>
        </div>

        <div class="instance-view-content-row">
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Mitigation:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskMitigation || 'Not specified' }}</div>
            <textarea v-if="isEditMode" v-model="editInstance.RiskMitigation" class="instance-view-textarea" placeholder="Enter risk mitigation" rows="3"></textarea>
          </div>
          <div class="instance-view-content-column">
            <h4 class="instance-view-section-title">Risk Owner:</h4>
            <div v-if="!isEditMode" class="instance-view-section-content">{{ instance.RiskOwner || 'Not assigned' }}</div>
            <input v-if="isEditMode" v-model="editInstance.RiskOwner" class="instance-view-input" placeholder="Enter risk owner" />
          </div>
        </div>
      </div>
    </div>

    <div v-else class="instance-view-no-data">
      Loading instance details or no instance found...
    </div>

    <!-- Success/Error Messages -->
    <div v-if="successMessage" class="instance-view-success-message">
      <i class="fas fa-check-circle"></i> {{ successMessage }}
    </div>
    <div v-if="errorMessage" class="instance-view-error-message">
      <i class="fas fa-exclamation-circle"></i> {{ errorMessage }}
    </div>
  </div>
</template>

<script>
import './ViewInstance.css'
import axios from 'axios'
import { PopupModal } from '@/modules/popup'
import { API_ENDPOINTS } from '../../config/api.js'

export default {
  name: 'ViewInstance',
  components: {
    PopupModal
  },
  data() {
    return {
      instance: null,
      editInstance: {},
      isEditMode: false,
      isSaving: false,
      originalInstance: {},
      successMessage: '',
      errorMessage: ''
    }
  },
  created() {
    this.fetchInstanceDetails()
  },
  methods: {
    async sendPushNotification(notificationData) {
      try {
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
    fetchInstanceDetails() {
      const instanceId = this.$route.params.id
      if (!instanceId) {
        this.$router.push('/risk/riskinstances-list')
        return
      }

      axios.get(API_ENDPOINTS.RISK_INSTANCE(instanceId))
        .then(response => {
          this.instance = response.data
          this.originalInstance = { ...response.data }
          this.editInstance = { ...response.data }
          // Send push notification for successful instance view
          this.sendPushNotification({
            title: 'Risk Instance Viewed',
            message: `Risk instance "${response.data.RiskId || 'Unknown Risk'}" has been viewed in the Risk module.`,
            category: 'risk',
            priority: 'medium',
            user_id: 'default_user'
          });
        })
        .catch(error => {
          console.error('Error fetching risk instance details:', error)
          this.showError('Failed to load risk instance details')
          // Send push notification for error
          this.sendPushNotification({
            title: 'Risk Instance View Failed',
            message: `Failed to load risk instance details: ${error.response?.data?.error || error.message}`,
            category: 'risk',
            priority: 'high',
            user_id: 'default_user'
          });
          // Try alternative endpoint if the first one fails
          this.tryAlternativeEndpoint(instanceId)
        })
    },
    
    toggleEditMode() {
      this.isEditMode = true
      this.editInstance = { ...this.instance }
      this.clearMessages()
    },

    cancelEdit() {
      this.isEditMode = false
      this.editInstance = { ...this.originalInstance }
      this.clearMessages()
    },

    async saveInstance() {
      if (!this.validateInstance()) {
        return
      }

      this.isSaving = true
      this.clearMessages()

      try {
        const response = await axios.put(API_ENDPOINTS.RISK_INSTANCE(this.instance.RiskInstanceId), this.editInstance)
        
        this.instance = response.data
        this.originalInstance = { ...response.data }
        this.isEditMode = false
        
        this.showSuccess('Risk instance updated successfully!')
        
        // Send push notification for successful update
        this.sendPushNotification({
          title: 'Risk Instance Updated',
          message: `Risk instance "${this.instance.RiskId}" has been successfully updated.`,
          category: 'risk',
          priority: 'medium',
          user_id: 'default_user'
        })
        
      } catch (error) {
        console.error('Error updating risk instance:', error)
        this.showError('Failed to update risk instance. Please try again.')
        
        // Send push notification for error
        this.sendPushNotification({
          title: 'Risk Instance Update Failed',
          message: `Failed to update risk instance: ${error.response?.data?.error || error.message}`,
          category: 'risk',
          priority: 'high',
          user_id: 'default_user'
        })
      } finally {
        this.isSaving = false
      }
    },

    validateInstance() {
      if (!this.editInstance.RiskId) {
        this.showError('Risk ID is required')
        return false
      }
      if (!this.editInstance.Category) {
        this.showError('Risk category is required')
        return false
      }
      if (!this.editInstance.Criticality) {
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
    
    tryAlternativeEndpoint(instanceId) {
      axios.get(API_ENDPOINTS.RISK_INSTANCE(instanceId))
        .then(response => {
          this.instance = response.data
          this.originalInstance = { ...response.data }
          this.editInstance = { ...response.data }
          // Send push notification for successful instance view via alternative endpoint
          this.sendPushNotification({
            title: 'Risk Instance Viewed',
            message: `Risk instance "${response.data.RiskId || 'Unknown Risk'}" has been viewed via alternative endpoint.`,
            category: 'risk',
            priority: 'medium',
            user_id: 'default_user'
          });
        })
        .catch(error => {
          console.error('Error with alternative endpoint:', error)
          this.showError('Failed to load risk instance details from both endpoints')
          // Send push notification for alternative endpoint error
          this.sendPushNotification({
            title: 'Risk Instance View Failed',
            message: `Failed to load risk instance details via alternative endpoint: ${error.response?.data?.error || error.message}`,
            category: 'risk',
            priority: 'high',
            user_id: 'default_user'
          });
        })
    },
    goBack() {
      this.$router.push('/risk/riskinstances-list')
    }
  }
}
</script> 