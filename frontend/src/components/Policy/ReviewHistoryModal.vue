<template>
  <div class="review-history-modal-overlay" @click="$emit('close')">
    <div class="review-history-modal" @click.stop>
      <div class="modal-header">
        <h3>
          <i class="fas fa-history"></i>
          Review History: {{ policyName }}
        </h3>
        <button class="close-btn" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="modal-body">
        <div class="policy-info">
          <div class="info-item">
            <span class="label">Policy ID:</span>
            <span class="value">{{ policyId }}</span>
          </div>
          <div class="info-item">
            <span class="label">Current Status:</span>
            <span class="value status-badge" :class="`status-${currentStatus.toLowerCase().replace(' ', '-')}`">
              {{ currentStatus }}
            </span>
          </div>
        </div>

        <div class="review-timeline">
          <h4><i class="fas fa-clock"></i> Review Timeline</h4>
          
          <div v-if="loading" class="loading-state">
            <i class="fas fa-spinner fa-spin"></i>
            Loading review history...
          </div>
          
          <div v-else-if="reviewHistory.length === 0" class="empty-state">
            <i class="fas fa-exclamation-circle"></i>
            No review history available for this policy.
          </div>
          
          <div v-else class="timeline">
            <div 
              v-for="(review, index) in reviewHistory" 
              :key="review.approval_id"
              class="timeline-item"
              :class="{
                'latest': index === 0,
                'approved': review.status_label === 'approved',
                'rejected': review.status_label === 'rejected',
                'pending': review.status_label === 'pending'
              }"
            >
              <div class="timeline-marker">
                <i class="fas" :class="{
                  'fa-check-circle': review.status_label === 'approved',
                  'fa-times-circle': review.status_label === 'rejected',
                  'fa-clock': review.status_label === 'pending'
                }"></i>
              </div>
              
              <div class="timeline-content">
                <div class="review-header">
                  <div class="revision-info">
                    <span class="revision-number">{{ review.version }}</span>
                    <span class="status-badge" :class="`status-${review.status_label}`">
                      {{ review.status }}
                    </span>
                  </div>
                  <div class="review-meta">
                    <span class="reviewer">
                      <i class="fas fa-user"></i>
                      {{ review.reviewer_name }}
                    </span>
                    <span class="date">
                      <i class="fas fa-calendar"></i>
                      {{ formatDate(review.approved_date || review.created_date) }}
                    </span>
                  </div>
                </div>
                
                <div v-if="review.rejection_reason" class="rejection-reason">
                  <div class="reason-header">
                    <i class="fas fa-comment-alt"></i>
                    Rejection Reason:
                  </div>
                  <div class="reason-text">{{ review.rejection_reason }}</div>
                </div>
                
                <div v-if="review.extracted_data" class="review-details">
                  <div class="details-header">
                    <i class="fas fa-info-circle"></i>
                    Review Details
                  </div>
                  <div class="details-content">
                    <!-- Add any specific extracted data display here -->
                    <div v-if="review.extracted_data.PolicyName" class="detail-item">
                      <span class="detail-label">Policy Name:</span>
                      <span class="detail-value">{{ review.extracted_data.PolicyName }}</span>
                    </div>
                    <div v-if="review.extracted_data.ReviewComments" class="detail-item">
                      <span class="detail-label">Comments:</span>
                      <span class="detail-value">{{ review.extracted_data.ReviewComments }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-secondary" @click="$emit('close')">
          Close
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { API_ENDPOINTS } from '../../config/api.js'
import axios from 'axios'

export default {
  name: 'ReviewHistoryModal',
  props: {
    policyId: {
      type: [Number, String],
      required: true
    },
    policyName: {
      type: String,
      default: 'Unknown Policy'
    },
    currentStatus: {
      type: String,
      default: 'Unknown'
    }
  },
  emits: ['close'],
  data() {
    return {
      reviewHistory: [],
      loading: true,
      error: null
    }
  },
  async mounted() {
    await this.fetchReviewHistory()
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
    async fetchReviewHistory() {
      try {
        this.loading = true
        const response = await axios.get(API_ENDPOINTS.POLICY_REVIEW_HISTORY(this.policyId))
        
        if (response.data.success) {
          this.reviewHistory = response.data.review_history
          // Send success push notification
          this.sendPushNotification({
            title: 'Review History Loaded Successfully',
            message: `Review history for policy "${this.policyName}" has been loaded successfully.`,
            category: 'policy',
            priority: 'medium',
            user_id: 'default_user'
          });
        } else {
          this.error = response.data.error || 'Failed to load review history'
          // Send error push notification
          this.sendPushNotification({
            title: 'Review History Load Failed',
            message: `Failed to load review history for policy "${this.policyName}": ${this.error}`,
            category: 'policy',
            priority: 'high',
            user_id: 'default_user'
          });
        }
      } catch (error) {
        console.error('Error fetching review history:', error)
        this.error = 'Failed to load review history'
        // Send error push notification
        this.sendPushNotification({
          title: 'Review History Load Failed',
          message: `Failed to load review history for policy "${this.policyName}": ${error.message || 'Network error'}`,
          category: 'policy',
          priority: 'high',
          user_id: 'default_user'
        });
      } finally {
        this.loading = false
      }
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      try {
        return new Date(dateString).toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      } catch (error) {
        return dateString
      }
    }
  }
}
</script>

<style scoped>
.review-history-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.review-history-modal {
  background: white;
  border-radius: 12px;
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  border-radius: 12px 12px 0 0;
}

.modal-header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 1.25rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.close-btn {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.policy-info {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f3f4f6;
  border-radius: 8px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.value {
  font-size: 1rem;
  color: #1f2937;
  font-weight: 600;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.status-approved {
  background: #d1fae5;
  color: #065f46;
}

.status-rejected {
  background: #fee2e2;
  color: #991b1b;
}

.status-pending {
  background: #fef3c7;
  color: #92400e;
}

.status-under-review {
  background: #dbeafe;
  color: #1e40af;
}

.review-timeline h4 {
  margin: 0 0 20px 0;
  color: #1f2937;
  font-size: 1.125rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #6b7280;
}

.loading-state i {
  font-size: 1.5rem;
  margin-bottom: 12px;
  display: block;
}

.empty-state i {
  font-size: 3rem;
  margin-bottom: 16px;
  display: block;
  opacity: 0.5;
}

.timeline {
  position: relative;
  padding-left: 20px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 10px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #e5e7eb;
}

.timeline-item {
  position: relative;
  margin-bottom: 24px;
  padding-left: 32px;
}

.timeline-item.latest .timeline-content {
  border: 2px solid #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.timeline-marker {
  position: absolute;
  left: -10px;
  top: 8px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: white;
  z-index: 2;
}

.timeline-item.approved .timeline-marker {
  background: #10b981;
}

.timeline-item.rejected .timeline-marker {
  background: #ef4444;
}

.timeline-item.pending .timeline-marker {
  background: #f59e0b;
}

.timeline-content {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  margin-left: 8px;
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.revision-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.revision-number {
  font-weight: 700;
  font-size: 1.125rem;
  color: #1f2937;
  background: #f3f4f6;
  padding: 4px 12px;
  border-radius: 6px;
}

.review-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.875rem;
  color: #6b7280;
}

.reviewer,
.date {
  display: flex;
  align-items: center;
  gap: 6px;
}

.rejection-reason {
  margin-top: 12px;
  padding: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
}

.reason-header {
  font-weight: 600;
  color: #991b1b;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.reason-text {
  color: #7f1d1d;
  line-height: 1.5;
}

.review-details {
  margin-top: 12px;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
}

.details-header {
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.detail-item {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
}

.detail-label {
  font-weight: 500;
  color: #6b7280;
  min-width: 100px;
}

.detail-value {
  color: #1f2937;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  background: #f9fafb;
  border-radius: 0 0 12px 12px;
}

.btn-secondary {
  background: #6b7280;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s ease;
}

.btn-secondary:hover {
  background: #4b5563;
}

/* Responsive design */
@media (max-width: 768px) {
  .review-history-modal {
    margin: 10px;
    max-height: calc(100vh - 20px);
  }
  
  .policy-info {
    flex-direction: column;
    gap: 12px;
  }
  
  .review-header {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  
  .timeline {
    padding-left: 16px;
  }
  
  .timeline-item {
    padding-left: 28px;
  }
}
</style> 