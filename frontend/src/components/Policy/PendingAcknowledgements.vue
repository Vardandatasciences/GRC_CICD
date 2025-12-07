<template>
  <div class="pending-acknowledgements">
      <div class="header">
        <button class="back-btn" @click="goBack">
          <i class="icon-arrow-left"></i> Back
        </button>
        <h3>
          <!-- <i class="icon-clipboard"></i> -->
          Pending Policy Acknowledgements
          <span v-if="!loading && pendingCount > 0" class="badge">{{ pendingCount }}</span>
        </h3>
        <!-- <button class="refresh-btn" @click="fetchPendingAcknowledgements" :disabled="loading">
          <i class="icon-refresh" :class="{ 'spinning': loading }"></i>
        </button> -->
      </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner-large"></div>
      <p>Loading pending acknowledgements...</p>
    </div>

    <div v-else-if="pendingAcknowledgements.length === 0" class="empty-state">
      <i class="icon-check-circle"></i>
      <p>No pending acknowledgements</p>
      <span>You're all caught up!</span>
    </div>

    <div v-else class="acknowledgement-list">
      <div
        v-for="ack in pendingAcknowledgements"
        :key="ack.acknowledgement_user_id"
        class="acknowledgement-item"
        :class="{ 'overdue': ack.is_overdue }"
      >
        <div class="ack-header">  
          <div class="ack-title">
            <h4>{{ ack.title }}</h4>
            <span v-if="ack.is_overdue" class="overdue-badge">Overdue</span>
            <span v-else class="pending-badge">Pending</span>
          </div>
          <div class="ack-due-date" v-if="ack.due_date">
            <i class="icon-calendar"></i>
            Due: {{ formatDate(ack.due_date) }}
          </div>
        </div>

        <div class="ack-body">
          <div class="policy-info">
            <div class="policy-name-section">
              <strong>{{ ack.policy_name }}</strong>
              <span class="policy-version">Version {{ ack.policy_version }}</span>
            </div>
            <div class="policy-details">
              <div class="detail-item">
                <!-- <i class="icon-file"></i> -->
                <span>Policy ID: {{ ack.policy_id }}</span>
              </div>
            </div>
          </div>

          <p v-if="ack.description" class="ack-description">
            {{ ack.description }}
          </p>
          <p v-else class="ack-description">
            Please review and acknowledge this policy to confirm your understanding.
          </p>

          <div class="ack-meta">
            <span><i class="icon-clock"></i> Assigned {{ formatRelativeTime(ack.assigned_at) }}</span>
            <span v-if="ack.notified_at"><i class="icon-bell"></i> Notified {{ formatRelativeTime(ack.notified_at) }}</span>
          </div>
        </div>

        <div class="ack-actions">
          <button class="btn-view" @click="viewPolicy(ack)">
            <i class="icon-eye"></i>
            View Policy
          </button>
          <button class="btn-acknowledge" @click="showAcknowledgeModal(ack)">
            <i class="icon-check"></i>
            Acknowledge
          </button>
        </div>
      </div>
    </div>

      <!-- Acknowledge Modal -->
      <AcknowledgeModal
        v-if="selectedAcknowledgement"
        :acknowledgement="selectedAcknowledgement"
        @close="closeAcknowledgeModal"
        @acknowledged="handleAcknowledged"
      />
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { API_ENDPOINTS, API_BASE_URL } from '../../config/api'
import { PopupService } from '@/modules/popus/popupService'
import AcknowledgeModal from './AcknowledgeModal.vue'

export default {
  name: 'PendingAcknowledgements',
  components: {
    AcknowledgeModal
  },
  setup() {
    const router = useRouter()
    const loading = ref(false)
    const pendingAcknowledgements = ref([])
    const pendingCount = ref(0)
    const selectedAcknowledgement = ref(null)

    const fetchPendingAcknowledgements = async () => {
      try {
        loading.value = true
        const response = await axios.get(API_ENDPOINTS.GET_USER_PENDING_ACKNOWLEDGEMENTS)
        
        pendingAcknowledgements.value = response.data.pending_acknowledgements || []
        pendingCount.value = response.data.pending_count || 0
      } catch (error) {
        console.error('Error fetching pending acknowledgements:', error)
        if (error.response?.status !== 404) {
          PopupService.error('Failed to load pending acknowledgements', 'Error')
        }
      } finally {
        loading.value = false
      }
    }

    const viewPolicy = (ack) => {
      router.push({
        name: 'PolicyDetails',
        params: { policyId: ack.policy_id },
        query: { fromAcknowledgements: 'true' }
      })
    }

    const showAcknowledgeModal = (ack) => {
      selectedAcknowledgement.value = ack
    }

    const closeAcknowledgeModal = () => {
      selectedAcknowledgement.value = null
    }

    const handleAcknowledged = async (acknowledgementData) => {
      closeAcknowledgeModal()
      
      // Mark ONLY the specific notification for this policy as read (action completed)
      try {
        const userId = localStorage.getItem('user_id') || 'default_user'
        const policyId = selectedAcknowledgement.value?.policy_id
        const policyName = selectedAcknowledgement.value?.policy_name
        
        if (policyId && policyName) {
          // Fetch all notifications
          const notificationsResponse = await fetch(`${API_BASE_URL}/api/get-notifications/?user_id=${userId}`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
              'Content-Type': 'application/json'
            }
          })
          
          if (notificationsResponse.ok) {
            const data = await notificationsResponse.json()
            if (data.status === 'success' && data.notifications) {
              // Find ONLY the notification for this specific policy
              // Match by policy name in the message (notification format: "Acknowledgement request created for "policy". X users assigned.")
              const matchingNotification = data.notifications.find(n => 
                !n.status.isRead &&
                n.title && 
                (n.title.includes('Acknowledgement Request') || n.title.includes('Policy Acknowledgement')) &&
                n.message && (
                  // Try to match policy name in message
                  n.message.toLowerCase().includes(policyName.toLowerCase()) ||
                  // Fallback: if message contains the policy ID pattern
                  (policyId && n.message.includes(`policy ${policyId}`)) ||
                  // Generic match for acknowledgement notifications (will match the most recent one)
                  (n.message.includes('acknowledgement request created') && 
                   n.message.includes('users assigned'))
                )
              )
              
              // If still no match, try to find by acknowledgement_request_id if available
              // This is a more reliable way to match
              let finalNotification = matchingNotification
              if (!finalNotification && acknowledgementData?.acknowledgement_request_id) {
                // Try to match by checking if notification was created around the same time
                // as the acknowledgement request (within last 24 hours)
                const recentNotifications = data.notifications.filter(n =>
                  !n.status.isRead &&
                  n.title && 
                  (n.title.includes('Acknowledgement Request') || n.title.includes('Policy Acknowledgement'))
                )
                // Get the most recent one (should be the one for this policy)
                if (recentNotifications.length > 0) {
                  finalNotification = recentNotifications[0]
                }
              } else {
                finalNotification = matchingNotification
              }
              
              // Mark ONLY this specific notification as read
              if (finalNotification) {
                await fetch(`${API_BASE_URL}/api/mark-as-read/`, {
                  method: 'POST',
                  headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify({ notification_id: finalNotification.id })
                })
                console.log(`✅ Marked notification ${finalNotification.id} as read for policy "${policyName}"`)
              } else {
                console.log(`⚠️ No matching notification found for policy "${policyName}" - notification will remain visible`)
              }
            }
          }
        }
      } catch (error) {
        console.error('Error marking notification as read:', error)
      }
      
      // Refresh pending acknowledgements list
      fetchPendingAcknowledgements()
    }

    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const formatRelativeTime = (dateString) => {
      if (!dateString) return ''
      
      const date = new Date(dateString)
      const now = new Date()
      const diffMs = now - date
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
      
      if (diffDays === 0) {
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
        if (diffHours === 0) {
          return 'just now'
        }
        return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
      }
      
      if (diffDays === 1) {
        return 'yesterday'
      }
      
      if (diffDays < 7) {
        return `${diffDays} days ago`
      }
      
      return formatDate(dateString)
    }

    const goBack = () => {
      router.back()
    }

    onMounted(() => {
      fetchPendingAcknowledgements()
    })

    return {
      loading,
      pendingAcknowledgements,
      pendingCount,
      selectedAcknowledgement,
      fetchPendingAcknowledgements,
      viewPolicy,
      showAcknowledgeModal,
      closeAcknowledgeModal,
      handleAcknowledged,
      formatDate,
      formatRelativeTime,
      goBack
    }
  }
}
</script>

<style scoped>
.pending-acknowledgements {
  margin-left: 260px; /* Account for sidebar width - same as CreatePolicy */
  padding: 20px;
  padding-top: 40px;
  position: relative;
  min-height: calc(100vh - 80px);
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  box-sizing: border-box;
  width: calc(100% - 260px); /* Subtract sidebar width */
  overflow-x: hidden;
}

.header {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 16px;
  padding: 20px 24px;
  border-bottom: 1px solid #d1d5db;
  background: #f3f4f6;
  color: #374151;
}

.back-btn {
  background: white;
  border: 1px solid #e5e7eb;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}

.badge {
  background: #ffffff;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}

.refresh-btn {
  background: #ffffff;
  border: 1px solid #d1d5db;
  color: #374151;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #e5e7eb;
  border-color: #9ca3af;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon-refresh.spinning {
  animation: spin 1s linear infinite;
}

.loading-state {
  padding: 60px 20px;
  text-align: center;
  color: #6b7280;
}

.spinner-large {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
  color: #6b7280;
}

.empty-state i {
  font-size: 48px;
  color: #10b981;
  margin-bottom: 16px;
}

.empty-state p {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.empty-state span {
  font-size: 14px;
  color: #6b7280;
}

.acknowledgement-list {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
  padding: 8px;
}

.acknowledgement-item {
  padding: 24px;
  border-bottom: 1px solid #e5e7eb;
  transition: all 0.2s;
  margin-bottom: 12px;
  border-radius: 8px;
  background: white;
}

.acknowledgement-item:hover {
  background: #f9fafb;
}

.acknowledgement-item:last-child {
  border-bottom: none;
}

.acknowledgement-item.overdue {
  border-left: 4px solid #ef4444;
  background: #fef2f2;
}

.ack-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.ack-title {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}

.ack-title h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.pending-badge,
.overdue-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.pending-badge {
  background: #fef3c7;
  color: #92400e;
}

.overdue-badge {
  background: #fee2e2;
  color: #991b1b;
}

.ack-due-date {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #6b7280;
  white-space: nowrap;
}

.ack-body {
  margin-bottom: 16px;
}

.policy-info {
  margin-bottom: 16px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  border-left: 3px solid #000000;
}

.policy-name-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.policy-info strong {
  font-size: 17px;
  color: #1f2937;
  font-weight: 600;
}

.policy-version {
  display: inline-block;
  background: #e0e7ff;
  color: #4f46e5;
  padding: 4px 12px;
  border-radius: 14px;
  font-size: 13px;
  font-weight: 600;
}

.policy-details {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #6b7280;
}

.detail-item i {
  color: #9ca3af;
}

.ack-description {
  color: #6b7280;
  font-size: 14px;
  margin: 8px 0;
  line-height: 1.5;
}

.ack-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  font-size: 13px;
  color: #6b7280;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.ack-meta span {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ack-meta i {
  color: #9ca3af;
  font-size: 14px;
}

.ack-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.btn-view,
.btn-acknowledge {
  flex: 1;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
  min-height: 44px;
}

.btn-view {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-view:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
}

.btn-acknowledge {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-acknowledge:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
}

.btn-view i,
.btn-acknowledge i {
  font-size: 16px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Icon styles */
.icon-arrow-left::before { content: '←'; }
.icon-clipboard::before { content: '📋'; }
.icon-refresh::before { content: '🔄'; }
.icon-check-circle::before { content: '✅'; }
.icon-calendar::before { content: '📅'; }
.icon-clock::before { content: '🕐'; }
.icon-bell::before { content: '🔔'; }
.icon-file::before { content: '📄'; }
.icon-eye::before { content: '👁'; }
.icon-check::before { content: '✓'; }

/* Responsive adjustments */
@media (max-width: 1024px) {
  .pending-acknowledgements {
    margin-left: 0;
    width: 100%;
    padding: 10px;
  }
}
</style>

