<template>
  <div class="status-change-details-page">
    <!-- Header with Navigation -->
    <div class="page-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <i class="fas fa-arrow-left"></i>
        </button>
        <div class="page-title">
          <div class="page-title-primary">
            <span class="detail-type-indicator">
              {{ selectedRequest?.ItemType === 'policy'
                ? 'Policy Status Change Request'
                : 'Framework Status Change Request' }}
            </span>
          </div>
          <div class="page-title-secondary">
            <span class="page-title-details">
              Details: {{ selectedRequest?.FrameworkName || selectedRequest?.PolicyName }}
            </span>
            <span class="version-pill" v-if="selectedRequest">Version: {{ selectedRequest.Version }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>Loading status change request details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <div class="error-message">
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Error Loading Request</h3>
        <p>{{ error }}</p>
        <button class="retry-btn" @click="fetchRequestDetails">Try Again</button>
      </div>
    </div>

    <!-- Status Change Request Details Content -->
    <div v-else-if="selectedRequest" class="request-details-content">
      <!-- Status Change Approval Section -->
      <div class="framework-approval-section">
        <h4>Status Change Approval</h4>
        
        <!-- Status Change Request indicator -->
        <div class="framework-status-indicator">
          <span class="status-label">Request Type:</span>
          <span class="status-value status-inactive">
            Change Status to Inactive
          </span>
        </div>
        
        <div class="approval-status-indicator">
          <span class="status-label">Status:</span>
          <span class="status-value" :class="{
            'status-approved': selectedRequest.Status === 'Approved',
            'status-inactive': selectedRequest.Status === 'Rejected',
            'status-pending': selectedRequest.Status === 'Pending Approval'
          }">
            {{ selectedRequest.Status }}
          </span>
        </div>
        
        <div v-if="selectedRequest.Status === 'Pending Approval' && selectedRequest.ApprovedNot === null" class="framework-actions">
          <!-- Check if current user is the assigned reviewer -->
          <div v-if="!isCurrentUserReviewer(selectedRequest)" class="reviewer-restriction-message">
            <i class="fas fa-clock"></i>
            <span>This {{ selectedRequest.ItemType }} is currently under review by the assigned reviewer. Only the assigned reviewer can approve or reject this status change request.</span>
          </div>
          <div v-else class="approval-buttons">
            <button class="approve-btn" @click="approveRequest(selectedRequest)">
              <i class="fas fa-check"></i> Approve
            </button>
            <button class="reject-btn" @click="rejectRequest(selectedRequest)">
              <i class="fas fa-times"></i> Reject
            </button>
          </div>
        </div>
        
        <div v-else class="approval-result">
          <div v-if="selectedRequest.Remarks" class="approval-remarks">
            <strong>Remarks:</strong> {{ selectedRequest.Remarks }}
          </div>
          <div v-if="selectedRequest.ApprovedDate" class="approval-date">
            <strong>Date:</strong> {{ formatDate(selectedRequest.ApprovedDate) }}
          </div>
        </div>
      </div>
      
      <!-- Display request details -->
      <div class="request-details">
        <div class="framework-detail-row">
          <strong>{{ selectedRequest.ItemType === 'policy' ? 'Policy' : 'Framework' }} Name:</strong> 
          <span>{{ selectedRequest.FrameworkName || selectedRequest.PolicyName }}</span>
        </div>
        <div class="framework-detail-row">
          <strong>{{ selectedRequest.ItemType === 'policy' ? 'Department' : 'Category' }}:</strong> 
          <span>{{ selectedRequest.Category || selectedRequest.Department }}</span>
        </div>
        <div class="framework-detail-row">
          <strong>Request Date:</strong> <span>{{ formatDate(selectedRequest.RequestDate) }}</span>
        </div>
        <div class="framework-detail-row">
          <strong>Current Status:</strong> 
          <span :class="{
            'status-active': selectedRequest.Status === 'Rejected' || selectedRequest.Status === 'Pending Approval',
            'status-inactive': selectedRequest.Status === 'Approved'
          }">
            {{ selectedRequest.Status === 'Approved' ? 'Inactive' : 'Active' }}
          </span>
        </div>
        <div class="framework-detail-row">
          <strong>Reason for Change:</strong> <span>{{ selectedRequest.Reason }}</span>
        </div>
        <div class="framework-detail-row" v-if="selectedRequest.ItemType === 'framework'">
          <strong>Cascade to Policies:</strong> 
          <span :class="{'cascade-yes': selectedRequest.CascadeToApproved, 'cascade-no': !selectedRequest.CascadeToApproved}">
            {{ selectedRequest.CascadeToApproved ? 'Yes' : 'No' }}
            <span class="policy-count" v-if="selectedRequest.PolicyCount > 0">
              ({{ selectedRequest.PolicyCount }} policies will be affected)
            </span>
          </span>
        </div>
        <div class="framework-detail-row" v-if="selectedRequest.ItemType === 'policy'">
          <strong>Cascade to Subpolicies:</strong> 
          <span :class="{'cascade-yes': selectedRequest.CascadeToSubpolicies, 'cascade-no': !selectedRequest.CascadeToSubpolicies}">
            {{ selectedRequest.CascadeToSubpolicies ? 'Yes' : 'No' }}
            <span class="policy-count" v-if="selectedRequest.SubpolicyCount > 0">
              ({{ selectedRequest.SubpolicyCount }} subpolicies will be affected)
            </span>
          </span>
        </div>
      </div>

      <!-- Affected Policies/Subpolicies Section -->
      <div v-if="(selectedRequest.AffectedPolicies && selectedRequest.AffectedPolicies.length > 0) || 
                 (selectedRequest.AffectedSubpolicies && selectedRequest.AffectedSubpolicies.length > 0)" 
           class="affected-policies-section">
        <h4>{{ selectedRequest.ItemType === 'policy' ? 'Affected Subpolicies' : 'Affected Policies' }}</h4>
        <p class="section-description">
          <span v-if="selectedRequest.Status === 'Approved'">
            The following {{ selectedRequest.ItemType === 'policy' ? 'subpolicies' : 'policies' }} have been set to Inactive:
          </span>
          <span v-else>
            The following {{ selectedRequest.ItemType === 'policy' ? 'subpolicies' : 'policies' }} will become inactive if this request is approved:
          </span>
        </p>
        
        <div class="policies-list">
          <!-- Framework Policies -->
          <template v-if="selectedRequest.ItemType === 'framework'">
            <div v-for="policy in selectedRequest.AffectedPolicies" 
                 :key="policy.PolicyId" 
                 class="policy-item">
              <div class="policy-header">
                <span class="policy-name">{{ policy.PolicyName }}</span>
                <span class="policy-status" :class="{
                  'active': selectedRequest.Status !== 'Approved',
                  'inactive': selectedRequest.Status === 'Approved'
                }">
                  {{ selectedRequest.Status === 'Approved' ? 'Inactive' : 'Active' }}
                </span>
              </div>
              <div class="policy-details">
                <div class="policy-detail-item" v-if="policy.Identifier">
                  <strong>Identifier:</strong> {{ policy.Identifier }}
                </div>
                <div class="policy-detail-item" v-if="policy.Department">
                  <strong>Department:</strong> {{ policy.Department }}
                </div>
                <div class="policy-detail-item" v-if="policy.Description">
                  <strong>Description:</strong> {{ policy.Description }}
                </div>
              </div>
            </div>
          </template>
          
          <!-- Policy Subpolicies -->
          <template v-if="selectedRequest.ItemType === 'policy'">
            <div v-for="subpolicy in selectedRequest.AffectedSubpolicies" 
                 :key="subpolicy.SubPolicyId" 
                 class="policy-item">
              <div class="policy-header">
                <span class="policy-name">{{ subpolicy.SubPolicyName }}</span>
                <span class="policy-status" :class="{
                  'active': selectedRequest.Status !== 'Approved',
                  'inactive': selectedRequest.Status === 'Approved'
                }">
                  {{ selectedRequest.Status === 'Approved' ? 'Inactive' : 'Active' }}
                </span>
              </div>
              <div class="policy-details">
                <div class="policy-detail-item" v-if="subpolicy.Identifier">
                  <strong>Identifier:</strong> {{ subpolicy.Identifier }}
                </div>
                <div class="policy-detail-item" v-if="subpolicy.Control">
                  <strong>Control:</strong> {{ subpolicy.Control }}
                </div>
                <div class="policy-detail-item" v-if="subpolicy.Description">
                  <strong>Description:</strong> {{ subpolicy.Description }}
                </div>
              </div>
            </div>
          </template>
        </div>
        
        <div v-if="selectedRequest.Status !== 'Approved'" class="affected-policies-summary">
          <div class="summary-warning">
            <i class="fas fa-exclamation-triangle"></i>
            <span>All of these policies will be changed to <strong>Inactive</strong> if the request is approved.</span>
          </div>
        </div>
      </div>

      <div v-else-if="selectedRequest.CascadeToApproved" class="no-policies-message">
        <i class="fas fa-info-circle"></i>
        <span>No active policies found that would be affected by this change.</span>
      </div>

      <div class="approval-implications" v-if="selectedRequest.Status === 'Pending Approval'">
        <h4>Approval Implications</h4>
        <div class="implication-item warning">
          <i class="fas fa-exclamation-triangle"></i>
          <div class="implication-text">
            <strong>If approved:</strong> The framework will become <span class="status-inactive">Inactive</span>.
            <span v-if="selectedRequest.CascadeToApproved && selectedRequest.PolicyCount > 0">
              Additionally, <strong>{{ selectedRequest.PolicyCount }} approved policies</strong> will also become inactive.
            </span>
          </div>
        </div>
        <div class="implication-item info">
          <i class="fas fa-info-circle"></i>
          <div class="implication-text">
            <strong>If rejected:</strong> The framework will remain <span class="status-approved">Active</span> and no changes will be made.
          </div>
        </div>
      </div>
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { API_ENDPOINTS } from '../../config/api.js'
import { PopupService } from '@/modules/popus/popupService'
import PopupModal from '@/modules/popus/PopupModal.vue'

const route = useRoute()
const router = useRouter()

const selectedRequest = ref(null)
const loading = ref(true)
const error = ref(null)
const currentUserId = ref(null)

// Get current user ID from session or localStorage
const getCurrentUserId = () => {
  // Try to get from sessionStorage first
  const sessionUserId = sessionStorage.getItem('user_id')
  if (sessionUserId) {
    return parseInt(sessionUserId)
  }
  
  // Try to get from localStorage
  const localUserId = localStorage.getItem('user_id')
  if (localUserId) {
    return parseInt(localUserId)
  }
  
  // Try to get from the user context if available
  if (window.currentUser && window.currentUser.id) {
    return window.currentUser.id
  }
  
  return null
}

// Check if current user is the assigned reviewer
const isCurrentUserReviewer = (request) => {
  if (!currentUserId.value || !request.ReviewerId) {
    return false
  }
  return currentUserId.value === request.ReviewerId
}

// Format date for display
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString()
  } catch (e) {
    return dateString
  }
}

// Send push notification
const sendPushNotification = async (notificationData) => {
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
}

// Approve status change request
const approveRequest = async (request) => {
  const itemName = request.FrameworkName || request.PolicyName
  const itemType = request.ItemType === 'policy' ? 'policy' : 'framework'
  const cascadeMessage = request.ItemType === 'policy' 
    ? (request.CascadeToSubpolicies ? ' This will also make all subpolicies inactive.' : '')
    : (request.CascadeToApproved ? ' This will also make all approved policies inactive.' : '')
  
  // Use PopupService.confirm with callbacks
  PopupService.confirm(
    `Are you sure you want to approve changing the status of "${itemName}" to Inactive?${cascadeMessage}`,
    'Confirm Approval',
    async () => {
      // User confirmed - now ask for remarks
      PopupService.comment(
        'Enter any remarks (optional):',
        'Approval Remarks',
        async (remarks) => {
          try {
            const endpoint = request.ItemType === 'policy' 
              ? `/api/policy-approvals/${request.ApprovalId}/approve-status-change/`
              : `/api/framework-approvals/${request.ApprovalId}/approve-status-change/`
            
            await axios.post(endpoint, {
              approved: true,
              remarks: remarks || 'Status change approved'
            })
            
            const affectedCount = request.ItemType === 'policy' ? request.SubpolicyCount : request.PolicyCount
            const affectedType = request.ItemType === 'policy' ? 'subpolicies' : 'policies'
            
            // Send push notification for successful approval
            await sendPushNotification({
              title: 'Status Change Request Approved',
              message: `${itemType.charAt(0).toUpperCase() + itemType.slice(1)} "${itemName}" has been set to Inactive.${affectedCount > 0 ? ` ${affectedCount} ${affectedType} were also made inactive.` : ''}`,
              category: 'status_change',
              priority: 'high',
              user_id: 'default_user'
            });
            
            // Update the selectedRequest status immediately
            if (selectedRequest.value && selectedRequest.value.ApprovalId === request.ApprovalId) {
              selectedRequest.value.Status = 'Approved'
              selectedRequest.value.ApprovedNot = true
              selectedRequest.value.Remarks = remarks || 'Status change approved'
              selectedRequest.value.ApprovedDate = new Date().toISOString()
            }
            
            PopupService.success(
              `${itemType.charAt(0).toUpperCase() + itemType.slice(1)} "${itemName}" has been set to Inactive.${affectedCount > 0 ? ` ${affectedCount} ${affectedType} were also made inactive.` : ''}`,
              'Status Changed'
            )
            
            // Navigate back to StatusChangeRequests after a short delay
            setTimeout(() => {
              router.push({ name: 'StatusChangeRequests' });
            }, 1500);
          } catch (error) {
            console.error('Error approving request:', error)
            
            // Handle specific error for reviewer restriction
            if (error.response?.status === 403) {
              PopupService.error(
                'You are not the assigned reviewer for this request. Only the assigned reviewer can approve or reject status change requests.',
                'Access Denied'
              )
            } else {
              PopupService.error(
                error.response?.data?.error || 'Failed to approve request. Please try again.',
                'Approval Failed'
              )
            }
            
            // Send push notification for failed approval
            await sendPushNotification({
              title: 'Status Change Approval Failed',
              message: `Failed to approve status change request for "${itemName}". Please try again.`,
              category: 'status_change',
              priority: 'high',
              user_id: 'default_user'
            });
          }
        }
      )
    }
  )
}

// Reject status change request
const rejectRequest = async (request) => {
  const itemName = request.FrameworkName || request.PolicyName
  const itemType = request.ItemType === 'policy' ? 'policy' : 'framework'
  
  PopupService.confirm(
    `Are you sure you want to reject the status change request for "${itemName}"? The ${itemType} will remain Active.`,
    'Confirm Rejection',
    async () => {
      // User confirmed - now ask for rejection reason
      PopupService.comment(
        'Enter rejection reason (optional):',
        'Rejection Reason',
        async (remarks) => {
          try {
            const endpoint = request.ItemType === 'policy' 
              ? `/api/policy-approvals/${request.ApprovalId}/approve-status-change/`
              : `/api/framework-approvals/${request.ApprovalId}/approve-status-change/`
            
            await axios.post(endpoint, {
              approved: false,
              remarks: remarks || 'Status change rejected'
            })
            
            // Send push notification for successful rejection
            await sendPushNotification({
              title: 'Status Change Request Rejected',
              message: `Status change request for "${itemName}" has been rejected. The ${itemType} remains Active.`,
              category: 'status_change',
              priority: 'medium',
              user_id: 'default_user'
            });
            
            // Update the selectedRequest status immediately
            if (selectedRequest.value && selectedRequest.value.ApprovalId === request.ApprovalId) {
              selectedRequest.value.Status = 'Rejected'
              selectedRequest.value.ApprovedNot = false
              selectedRequest.value.Remarks = remarks || 'Status change rejected'
              selectedRequest.value.ApprovedDate = new Date().toISOString()
            }
            
            PopupService.success(
              `Status change request for "${itemName}" has been rejected. The ${itemType} remains Active.`,
              'Request Rejected'
            )
            
            // Navigate back to StatusChangeRequests after a short delay
            setTimeout(() => {
              router.push({ name: 'StatusChangeRequests' });
            }, 1500);
          } catch (error) {
            console.error('Error rejecting status change request:', error)
            
            // Handle specific error for reviewer restriction
            if (error.response?.status === 403) {
              PopupService.error(
                'You are not the assigned reviewer for this request. Only the assigned reviewer can approve or reject status change requests.',
                'Access Denied'
              )
            } else {
              PopupService.error(
                error.response?.data?.error || 'Failed to reject request. Please try again.',
                'Rejection Failed'
              )
            }
            
            // Send push notification for failed rejection
            await sendPushNotification({
              title: 'Status Change Rejection Failed',
              message: `Failed to reject status change request for "${itemName}". Please try again.`,
              category: 'status_change',
              priority: 'high',
              user_id: 'default_user'
            });
          }
        }
      )
    }
  )
}

// Fetch request details
const fetchRequestDetails = async () => {
  try {
    loading.value = true
    error.value = null

    console.log('Fetching status change request details for ID:', route.params.requestId);

    // Check if request data was passed from StatusChangeRequests
    const storedRequestData = sessionStorage.getItem('statusChangeRequestData');
    if (storedRequestData) {
      console.log('Using stored request data from StatusChangeRequests');
      const requestData = JSON.parse(storedRequestData);
      console.log('Raw request data from sessionStorage:', requestData);
      
      // Verify the request ID matches
      if (requestData.ApprovalId == route.params.requestId) {
        selectedRequest.value = requestData;
        console.log('Request details loaded from stored data:', selectedRequest.value);
        
        // Clear the stored data after use
        sessionStorage.removeItem('statusChangeRequestData');
        
        loading.value = false;
        return;
      } else {
        console.log('Stored request ID does not match, fetching from API');
      }
    }

    // If no stored data, we need to fetch from API
    console.error('No request data found in sessionStorage');
    error.value = 'Please navigate to this page from the Status Change Requests to view request details.';
  } catch (error) {
    console.error('Error fetching request details:', error);
    error.value = 'Failed to load request details. Please try again.';
  } finally {
    loading.value = false;
  }
}

// Navigate back to StatusChangeRequests
const goBack = () => {
  router.push({ name: 'StatusChangeRequests' });
}

// Initialize component
onMounted(async () => {
  // Initialize current user ID
  currentUserId.value = getCurrentUserId()
  console.log('Current user ID:', currentUserId.value)
  
  // Fetch request details
  await fetchRequestDetails()
})
</script>

<style scoped>
.status-change-details-page {
  padding: 32px 40px;
  margin-left: 200px;
  max-width: calc(100vw - 240px);
  min-height: 100vh;
  background-color: #ffffff;
}

.page-header {
  margin-bottom: 32px;
  display: flex;
  justify-content: flex-start;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  justify-content: flex-start;
  width: 100%;
  margin-left: -5px;
}

.back-btn {
  background: transparent;
  border: none;
  color: #333;
  font-size: 1.2rem;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  transition: background 0.2s;
}

.back-btn:hover {
  background: rgba(0, 0, 0, 0.06);
}

.back-btn i {
  font-size: 1rem;
}

.page-title {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 0;
  align-items: flex-start;
  text-align: left;
  width: 100%;
}

.page-title-primary {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  width: 100%;
}

.page-title-secondary {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  width: 100%;
  margin-left: 10px;
  font-size: 1rem;
  color: #2c3e50;
  font-weight: 600;
}

.page-title-details {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.detail-type-indicator {
  font-size: 1.3rem;
  padding: 4px 10px;
  border-radius: 8px;
  color: black;
  font-weight: 600;
}

.version-pill {
  font-size: 0.85rem;
  padding: 2px 8px;
  border-radius: 10px;
  background: #f0f0f0;
  color: #666;
}

.loading-container, .error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #4f6cff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  background: #fff5f5;
  border: 1px solid #fed7d7;
  border-radius: 8px;
  padding: 24px;
  color: #c53030;
}

.error-message i {
  font-size: 2rem;
  margin-bottom: 16px;
}

.error-message h3 {
  margin: 0 0 8px 0;
  color: #c53030;
}

.error-message p {
  margin: 0 0 16px 0;
}

.retry-btn {
  background: #4f6cff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.retry-btn:hover {
  background: #3b5bdb;
}

.request-details-content {
  background: white;
  border-radius: 12px;
  padding: 32px;
}

.framework-approval-section {
  background: #ffffff;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 24px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.06);
}

.framework-approval-section h4 {
  margin-top: 0;
  margin-bottom: 16px;
  color: #4f6cff;
}

.framework-status-indicator, .approval-status-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.status-label {
  font-weight: 600;
  color: #444;
}

.status-value {
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.9rem;
}

.status-approved {
  background: #e8f7ee;
  color: #22a722;
}

.status-inactive {
  background: #ffebee;
  color: #e53935;
}

.status-pending {
  background: #fff5e6;
  color: #f5a623;
}

.framework-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.approve-btn, .reject-btn {
  padding: 10px 20px;
  border-radius: 8px;
  border: none;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.approve-btn {
  background: #22a722;
  color: white;
}

.approve-btn:hover {
  background: #1b8c1b;
  transform: translateY(-2px);
}

.reject-btn {
  background: #e53935;
  color: white;
}

.reject-btn:hover {
  background: #c62828;
  transform: translateY(-2px);
}

.approval-result {
  padding: 12px;
  border-radius: 8px;
  margin-top: 16px;
}

.approval-remarks,
.approval-date {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.approval-remarks strong,
.approval-date strong {
  color: #444;
  width: 160px;
  flex-shrink: 0;
}

.request-details {
  margin-bottom: 24px;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.06);
  padding: 24px;
}

.framework-detail-row {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  flex-wrap: wrap;
}

.framework-detail-row:last-child {
  border-bottom: none;
}

.framework-detail-row strong {
  width: 160px;
  color: #444;
}

.status-active {
  color: #22a722;
}

.status-inactive {
  color: #e53935;
}

.cascade-yes {
  color: #22a722;
  font-weight: 600;
}

.cascade-no {
  color: #e53935;
  font-weight: 600;
}

.policy-count {
  color: #666;
  font-size: 0.85rem;
  margin-left: 6px;
  font-weight: normal;
}

.affected-policies-section {
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 24px;
}

.affected-policies-section h4 {
  margin-top: 0;
  margin-bottom: 16px;
  color: #4f6cff;
  font-size: 1.1rem;
}

.section-description {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 16px;
}

.policies-list {
  margin-bottom: 16px;
}

.policy-item {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s ease;
}

.policy-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.policy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 10px;
}

.policy-name {
  font-weight: 600;
  color: #4f6cff;
  font-size: 1rem;
}

.policy-status {
  font-size: 0.85rem;
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 600;
}

.policy-status.active {
  background-color: #e8f7ee;
  color: #22a722;
}

.policy-status.inactive {
  background-color: #ffebee;
  color: #e53935;
}

.policy-details {
  margin-left: 0;
}

.policy-detail-item {
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.policy-detail-item strong {
  font-weight: 600;
  color: #444;
  display: inline-block;
  width: auto;
  margin-right: 8px;
}

.affected-policies-summary {
  background: #fff5e6;
  border-radius: 10px;
  padding: 16px;
  margin-top: 16px;
}

.summary-warning {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #f5a623;
}

.summary-warning i {
  font-size: 1.2rem;
}

.no-policies-message {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  background: #e3f0ff;
  border-radius: 10px;
  padding: 16px;
  color: #4f6cff;
}

.approval-implications {
  background: #ffffff;
  border-radius: 10px;
  padding: 20px;
}

.approval-implications h4 {
  margin-top: 0;
  margin-bottom: 16px;
  color: #4f6cff;
}

.implication-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  padding: 16px;
  border-radius: 8px;
  align-items: flex-start;
}

.implication-item:last-child {
  margin-bottom: 0;
}

.implication-item.warning {
  background: #fff5e6;
}

.implication-item.info {
  background: #e3f0ff;
}

.implication-item i {
  font-size: 1.2rem;
}

.implication-item.warning i {
  color: #f5a623;
}

.implication-item.info i {
  color: #4f6cff;
}

.implication-text {
  flex: 1;
}

/* Reviewer restriction message styles */
.reviewer-restriction-message {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #e3f0ff;
  border: 1px solid #b3d9ff;
  border-radius: 8px;
  padding: 16px;
  color: #4f6cff;
  font-size: 0.95rem;
  margin-bottom: 16px;
}

.reviewer-restriction-message i {
  color: #4f6cff;
  font-size: 1.1rem;
}

.approval-buttons {
  display: flex;
  gap: 12px;
}

/* Responsive design */
@media (max-width: 768px) {
  .status-change-details-page {
    margin-left: 0;
    padding: 16px;
    max-width: 100%;
  }
  
  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .page-title {
    font-size: 1.4rem;
  }
  
  .request-details-content {
    padding: 20px;
  }
  
  .framework-detail-row strong {
    width: 100%;
    margin-bottom: 4px;
  }
}
</style>
