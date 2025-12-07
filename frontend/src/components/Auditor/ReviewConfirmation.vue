<template>
  <div class="review-confirmation">
    <div class="confirmation-card">
      <div class="confirmation-header">
        <h1 v-if="reviewData.reviewStatus === 'Accept'" class="confirmation-title accept-title">
          <span class="confirmation-icon">✓</span> Review Approved
        </h1>
        <h1 v-else-if="reviewData.reviewStatus === 'Reject'" class="confirmation-title reject-title">
          <span class="confirmation-icon">✗</span> Review Rejected
        </h1>
        <h1 v-else class="confirmation-title">
          <span class="confirmation-icon">ⓘ</span> Review Submitted
        </h1>
      </div>
      
      <div class="confirmation-body">
        <div class="confirmation-message">
          <p v-if="reviewData.reviewStatus === 'Accept'">
            You have approved the audit. The audit has been marked as completed.
          </p>
          <p v-else-if="reviewData.reviewStatus === 'Reject'">
            You have rejected the audit. The audit has been sent back to the auditor for revisions.
          </p>
          <p v-else>
            Your review has been saved successfully.
          </p>
        </div>
        
        <div class="confirmation-details">
          <div class="detail-row">
            <span class="detail-label">Audit ID:</span>
            <span class="detail-value">{{ reviewData.auditId }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Framework:</span>
            <span class="detail-value">{{ reviewData.frameworkName }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Review Status:</span>
            <span class="detail-value" :class="getStatusClass(reviewData.reviewStatus)">
              {{ reviewData.reviewStatus }}
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Audit Status:</span>
            <span class="detail-value">{{ reviewData.auditStatus }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Submitted:</span>
            <span class="detail-value">{{ formatDate(reviewData.timestamp) }}</span>
          </div>
          
          <div v-if="reviewData.reviewComments" class="review-comments-section">
            <h3>Review Comments:</h3>
            <div class="review-comments">
              {{ reviewData.reviewComments }}
            </div>
          </div>
        </div>
      </div>
      
      <div class="confirmation-actions">
        <button @click="goToReviews" class="btn-back">
          Back to Reviews
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { AccessUtils } from '@/utils/accessUtils';

export default {
  name: 'ReviewConfirmation',
  props: {
    auditId: {
      type: [String, Number],
      required: true
    }
  },
  data() {
    return {
      reviewData: {
        auditId: this.auditId,
        frameworkName: '',
        reviewStatus: '',
        reviewComments: '',
        auditStatus: '',
        timestamp: new Date().toISOString()
      }
    };
  },
  created() {
    this.loadReviewData();
  },
  methods: {
    loadReviewData() {
      try {
        // Load the review data from localStorage
        const storedData = localStorage.getItem('reviewSubmissionResult');
        if (storedData) {
          const parsedData = JSON.parse(storedData);
          
          // Check if the data is for the current audit
          if (parsedData.auditId == this.auditId) {
            this.reviewData = parsedData;
          } else {
            console.warn('Stored review data is for a different audit');
          }
        } else {
          console.warn('No review data found in localStorage');
        }
      } catch (error) {
        console.error('Error loading review data:', error);
      }
    },
    formatDate(dateString) {
      try {
        const date = new Date(dateString);
        return date.toLocaleString();
      } catch (error) {
        return 'Unknown date';
      }
    },
    getStatusClass(status) {
      if (status === 'Accept') return 'status-accept';
      if (status === 'Reject') return 'status-reject';
      return '';
    },
    goToReviews() {
      // Clear the stored review data
      localStorage.removeItem('reviewSubmissionResult');
      
      // Navigate back to the reviews page
      this.$router.push('/auditor/reviewer');
    },
    
    // Method to check review confirmation permission
    checkReviewConfirmationPermission() {
      AccessUtils.showReviewAuditDenied();
    }
  }
};
</script>

<style scoped>
.review-confirmation {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 90vh;
  background-color: #f5f7fa;
  padding: 20px;
  margin-left: 280px !important;
}

.confirmation-card {
  max-width: 800px;
  width: 100%;
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.confirmation-header {
  padding: 30px;
  text-align: center;
  border-bottom: 1px solid #eee;
}

.confirmation-title {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  justify-content: center;
}

.accept-title {
  color: #28a745;
}

.reject-title {
  color: #dc3545;
}

.confirmation-icon {
  font-size: 32px;
  margin-right: 15px;
}

.confirmation-body {
  padding: 30px;
}

.confirmation-message {
  font-size: 18px;
  line-height: 1.5;
  margin-bottom: 30px;
  text-align: center;
  color: #555;
}

.confirmation-details {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.detail-row {
  display: flex;
  margin-bottom: 12px;
  font-size: 16px;
}

.detail-label {
  font-weight: 600;
  min-width: 120px;
  color: #555;
}

.detail-value {
  flex: 1;
}

.status-accept {
  color: #28a745;
  font-weight: 600;
}

.status-reject {
  color: #dc3545;
  font-weight: 600;
}

.review-comments-section {
  margin-top: 20px;
  border-top: 1px solid #eee;
  padding-top: 20px;
}

.review-comments-section h3 {
  font-size: 16px;
  margin-bottom: 10px;
  color: #555;
}

.review-comments {
  background-color: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 15px;
  min-height: 100px;
  white-space: pre-wrap;
}

.confirmation-actions {
  padding: 20px 30px;
  border-top: 1px solid #eee;
  text-align: center;
}

.btn-back {
  background-color: #4f7cff;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-back:hover {
  background-color: #3a63cc;
}
</style> 