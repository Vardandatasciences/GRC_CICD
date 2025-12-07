<template>
  <div class="compliance_details_page">
    <!-- Header with Navigation -->
    <div class="compliance_header">
      <div class="compliance_header_left">
        <button class="compliance_back_btn" @click="goBack" aria-label="Back">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h1 class="compliance_title">
          Details: {{ getComplianceId(selectedApproval) }}
          <span class="version-text" v-if="selectedApproval">(Version: {{ selectedApproval.version || selectedApproval.Version || 'u1' }})</span>
        </h1>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="compliance_loading_container">
      <div class="compliance_loading_spinner"></div>
      <p>Loading compliance details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="compliance_error_container">
      <div class="compliance_error_message">
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Error Loading Compliance</h3>
        <p>{{ error }}</p>
        <button class="compliance_retry_btn" @click="fetchComplianceDetails">Try Again</button>
      </div>
    </div>

    <!-- Compliance Details Content -->
    <div v-else-if="selectedApproval" class="compliance_details_container">
      <!-- Compliance Approval Section -->
      <div class="compliance_approval_section">
        <h4>Compliance Approval</h4>
        
        <!-- Compliance status indicator -->
        <div class="compliance_status_indicator">
          <span class="status-label">Status:</span>
          <span class="status-value" :class="{
            'status-approved': correctComplianceStatus === 'Approved',
            'status-rejected': correctComplianceStatus === 'Rejected',
            'status-pending': correctComplianceStatus === 'Under Review'
          }">
            {{ correctComplianceStatus }}
          </span>
          <span v-if="selectedApproval.ApprovedDate" class="approval-date">
            (Approved on: {{ formatDate(selectedApproval.ApprovedDate) }})
          </span>
          <span v-if="!canSubmitReviewComputed && canPerformReviewActionsComputed" class="status-note">
            <i class="fas fa-info-circle"></i>
            Review already submitted
          </span>
        </div>

        <div class="compliance_actions">
          <!-- Final Compliance Approval Button -->
          <!-- Show resubmission indicator for resubmitted items -->
          <div v-if="isResubmittedCompliance" class="resubmission-indicator">
            <i class="fas fa-redo-alt"></i>
            <span><strong>Resubmitted for Review:</strong> This compliance was previously rejected and has been resubmitted with modifications.</span>
          </div>
          
          <button 
            class="final-approve-btn" 
            @click="approveCompliance()" 
            v-if="canPerformReviewActionsComputed && (selectedApproval.ApprovedNot === null || isResubmittedCompliance || hasRejectionRemarks) && correctComplianceStatus !== 'Rejected'"
          >
            <i class="fas fa-check-double"></i> Final Approval
          </button>
          
          <!-- Reject Button -->
          <button class="reject-btn" @click="rejectCompliance()" v-if="canPerformReviewActionsComputed && (selectedApproval.ApprovedNot === null || isResubmittedCompliance || hasRejectionRemarks) && correctComplianceStatus !== 'Rejected'">
            <i class="fas fa-times"></i> Reject
          </button>
          
          <button 
            class="submit-btn" 
            @click="submitReview()" 
            :disabled="isSubmittingRejection || !canSubmitReviewComputed || showRejectModal" 
            :title="getSubmitButtonTooltip(selectedApproval)"
            v-if="canPerformReviewActionsComputed && canSubmitReviewComputed && !showRejectModal"
          >
            <i class="fas fa-paper-plane"></i> {{ isSubmittingRejection ? 'Submitting...' : 'Submit Review' }}
          </button>
          
          <!-- Show message when compliance is already processed -->
          <div v-if="canPerformReviewActionsComputed && !canSubmitReviewComputed" class="processed-compliance-message">
            <i class="fas fa-check-circle" v-if="correctComplianceStatus === 'Approved'"></i>
            <i class="fas fa-times-circle" v-if="correctComplianceStatus === 'Rejected'"></i>
            <span v-if="correctComplianceStatus === 'Approved'">This compliance has already been approved and cannot be submitted for review again.</span>
            <span v-if="correctComplianceStatus === 'Rejected'">This compliance has already been rejected and cannot be submitted for review again.</span>
          </div>
          
          <!-- Show message for compliance creators -->
          <div v-if="isCurrentUserCreatorComputed && selectedApproval.ApprovedNot === null && correctComplianceStatus !== 'Rejected'" class="creator-message">
            <i class="fas fa-info-circle"></i>
            <span>This compliance is under review. You cannot approve or reject your own compliance.</span>
          </div>
          
          <!-- Show message for administrators who are not assigned as reviewers -->
          <div v-if="isGRCAdministrator && !canPerformReviewActionsComputed && selectedApproval.ApprovedNot === null && correctComplianceStatus !== 'Rejected'" class="admin-message">
            <i class="fas fa-eye"></i>
            <span>Viewing compliance. You are not assigned as the reviewer for this compliance.</span>
          </div>
        </div>
      </div>

      <!-- Display compliance details -->
      <div v-if="selectedApproval.ExtractedData" class="compliance_info_section">
        <h4>Compliance Information</h4>
        <div v-for="(value, key) in selectedApproval.ExtractedData" :key="key" class="compliance_detail_row">
          <template v-if="key !== 'compliance_approval' && key !== 'type'">
            <strong>{{ formatFieldName(key) }}:</strong> 
            <span v-if="key === 'Status'">
              {{ correctComplianceStatus }}
            </span>
            <span v-else>{{ sanitizeValue(value) }}</span>
          </template>
        </div>
      </div>
      
      <!-- Add a message for rejected compliances -->
      <div v-if="selectedApproval.ApprovedNot === false" class="rejected-compliance-message">
        <div class="rejection-note">
          <i class="fas fa-exclamation-triangle"></i>
          This compliance has been rejected.
        </div>
      </div>
    </div>

    <!-- Rejection Modal -->
    <div v-if="showRejectModal" class="compliance_reject_modal">
      <div class="compliance_reject_modal_content">
        <h4>Rejection Reason</h4>
        <p>Please provide a reason for rejecting this compliance</p>
        <textarea 
          v-model="rejectionComment" 
          class="compliance_rejection_comment" 
          placeholder="Enter your comments here..."></textarea>
        <div class="compliance_reject_modal_actions">
          <button class="compliance_cancel_btn" @click="cancelRejection" :disabled="isSubmittingRejection">Cancel</button>
          <button class="compliance_confirm_btn" @click="confirmRejection" :disabled="isSubmittingRejection">
            {{ isSubmittingRejection ? 'Submitting...' : 'Confirm Rejection' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import axios from 'axios'
import { PopupService } from '@/modules/popus/popupService'
import PopupModal from '@/modules/popus/PopupModal.vue'
import { API_ENDPOINTS } from '../../config/api.js'
import { complianceService } from '@/services/api.js'

export default {
  name: 'ComplianceDetails',
  components: {
    PopupModal
  },
  props: {
    complianceId: {
      type: [String, Number],
      required: true
    }
  },
  data() {
    return {
      selectedApproval: null,
      loading: true,
      error: null,
      showRejectModal: false,
      rejectionComment: '',
      isSubmittingRejection: false,
      // User management
      currentUserId: null,
      currentUserName: '',
      isGRCAdministrator: false,
      userInitialized: false
    }
  },
  async mounted() {
    await this.initializeUser();
    await this.fetchComplianceDetails();
  },
  methods: {
    async initializeUser() {
      try {
        console.log('Initializing user and checking role...');
        
        // Get current user role
        const response = await axios.get(API_ENDPOINTS.USER_ROLE);
        console.log('User role API response:', response.data);
        
        if (response.data.success) {
          this.currentUserId = response.data.user_id;
          this.currentUserName = response.data.username || response.data.user_name || '';
          
          // Store username in localStorage for fallback
          if (this.currentUserName) {
            localStorage.setItem('user_name', this.currentUserName);
          }
          
          // Check specifically for "GRC Administrator" role
          const userRole = response.data.role;
          console.log('User role received:', userRole);
          
          // Only GRC Administrator should see the user dropdown
          this.isGRCAdministrator = userRole === 'GRC Administrator';
          
          console.log('Is GRC Administrator:', this.isGRCAdministrator);
          
          this.userInitialized = true;
        } else {
          console.error('User role API did not return success:', response.data);
          // Fallback for development/testing
          console.log('Using fallback user role for testing...');
          this.currentUserId = 2; // Default user ID
          this.isGRCAdministrator = false; // Default to non-administrator
          this.userInitialized = true;
        }
      } catch (error) {
        console.error('Error initializing user:', error);
        // Fallback for development/testing
        console.log('Using fallback user role due to error...');
        this.currentUserId = 2; // Default user ID
        this.isGRCAdministrator = false; // Default to non-administrator  
        this.userInitialized = true;
      }
    },

    async fetchComplianceDetails() {
      try {
        this.loading = true;
        this.error = null;

        console.log('Fetching compliance details for ID:', this.complianceId);

        // Check if compliance data was passed from ComplianceApprover
        const storedComplianceData = sessionStorage.getItem('complianceData');
        if (storedComplianceData) {
          console.log('Using stored compliance data from ComplianceApprover');
          const complianceData = JSON.parse(storedComplianceData);
          console.log('Raw compliance data from sessionStorage:', complianceData);
          
          // Verify the compliance ID matches
          const storedComplianceId = this.getComplianceId(complianceData);
          if (storedComplianceId == this.complianceId) {
            this.selectedApproval = complianceData;
            console.log('Compliance details loaded from stored data:', this.selectedApproval);
            console.log('ExtractedData:', this.selectedApproval.ExtractedData);
            
            // Clear the stored data after use
            sessionStorage.removeItem('complianceData');
            
            this.loading = false;
            return;
          } else {
            console.log('Stored compliance ID does not match, fetching from API');
          }
        }

        // If no stored data, we need to fetch from API
        // Since we don't have a COMPLIANCE_APPROVALS_LATEST endpoint, 
        // we'll show an error asking user to navigate from ComplianceApprover
        console.error('No compliance data found in sessionStorage');
        this.error = 'Please navigate to this page from the Compliance Approver to view compliance details.';
      } catch (error) {
        console.error('Error fetching compliance details:', error);
        this.error = this.handleError(error, 'loading compliance details');
      } finally {
        this.loading = false;
      }
    },

    goBack() {
      this.$router.push({ name: 'ComplianceApprover' });
    },

    getComplianceId(compliance) {
      if (!compliance) {
        console.log('getComplianceId: No compliance provided, returning route complianceId:', this.complianceId);
        return this.complianceId;
      }
      
      console.log('getComplianceId: Checking compliance object:', {
        ComplianceId: compliance.ComplianceId,
        ApprovalId: compliance.ApprovalId,
        routeComplianceId: this.complianceId
      });
      
      if (compliance.ComplianceId) {
        const result = typeof compliance.ComplianceId === 'object' ? compliance.ComplianceId.ComplianceId : compliance.ComplianceId;
        console.log('getComplianceId: Found ComplianceId, returning:', result);
        return result;
      }
      
      const result = compliance.ApprovalId || this.complianceId;
      console.log('getComplianceId: Using ApprovalId or route ID, returning:', result);
      return result;
    },

    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return ''; // Invalid date
      
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    },

    formatFieldName(field) {
      // Convert camelCase or PascalCase to display format
      return field
        // Insert space before all uppercase letters
        .replace(/([A-Z])/g, ' $1')
        // Replace first char with uppercase
        .replace(/^./, str => str.toUpperCase())
        .trim();
    },

    sanitizeValue(value) {
      if (!value) return '';
      
      // If value is a string, clean it up
      if (typeof value === 'string') {
        // Remove HTML tags
        let cleanValue = value.replace(/<[^>]*>/g, '');
        
        // Remove API endpoint patterns
        cleanValue = cleanValue.replace(/api\/[^\s]*/g, '');
        
        // Remove code block patterns
        cleanValue = cleanValue.replace(/\[name='[^']*'\]/g, '');
        
        // Clean up extra whitespace
        cleanValue = cleanValue.replace(/\s+/g, ' ').trim();
        
        return cleanValue;
      }
      
      return value;
    },

    // Check if current user is the reviewer for this compliance (kept for backward compatibility)
    isCurrentUserReviewer(compliance) {
      if (!compliance || !this.currentUserId) return false;
      
      // For GRC Administrators, they can only review compliances specifically assigned to them
      if (this.isGRCAdministrator) {
        const reviewerId = compliance.ReviewerId || compliance.ExtractedData?.Reviewer;
        const reviewerName = compliance.ExtractedData?.Reviewer;
        
        // Check by ID first
        if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
          return true;
        }
        
        // Check by username
        if (reviewerName && String(reviewerName) === String(this.getCurrentUserName())) {
          return true;
        }
        
        return false;
      }
      
      // Check if current user is the reviewer for this compliance
      const reviewerId = compliance.ReviewerId || compliance.ExtractedData?.Reviewer;
      const reviewerName = compliance.ExtractedData?.Reviewer;
      
      // Check by ID first
      if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
        return true;
      }
      
      // Check by username (fallback for when reviewer is stored as username)
      if (reviewerName && String(reviewerName) === String(this.getCurrentUserName())) {
        return true;
      }
      
      // Check if the compliance was created by the current user (they shouldn't review their own compliances)
      if (this.isCurrentUserCreator(compliance)) {
        return false;
      }
      
      return false;
    },

    // Check if current user can perform review actions (approve/reject)
    canPerformReviewActions(compliance) {
      if (!compliance || !this.currentUserId) return false;
      
      // Only allow review actions if the user is specifically assigned as the reviewer
      // AND is not the creator of the compliance
      return this.isCurrentUserReviewer(compliance) && !this.isCurrentUserCreator(compliance);
    },

    // Check if current user is the creator of this compliance (kept for backward compatibility)
    isCurrentUserCreator(compliance) {
      if (!compliance || !this.currentUserId) return false;
      
      const createdBy = compliance.ExtractedData?.CreatedByName || compliance.CreatedByName;
      const createdById = compliance.ExtractedData?.CreatedBy || compliance.CreatedBy;
      const userId = compliance.ExtractedData?.UserID || compliance.UserID;
      
      // Check by ID first (most reliable)
      if (createdById && String(createdById) === String(this.currentUserId)) {
        return true;
      }
      
      // Check by UserID (from approval record)
      if (userId && String(userId) === String(this.currentUserId)) {
        return true;
      }
      
      // Check by name (fallback)
      if (createdBy && String(createdBy) === String(this.getCurrentUserName())) {
        return true;
      }
      
      return false;
    },

    // Helper method to get current user name
    getCurrentUserName() {
      // For current user, use stored username or fallback to localStorage
      return this.currentUserName || localStorage.getItem('user_name') || '';
    },

    // Helper method to check if review can be submitted
    canSubmitReview(compliance) {
      if (!compliance || !compliance.ExtractedData) return false;
      
      // Can only submit review if compliance is under review and not already processed
      return this.correctComplianceStatus === 'Under Review' && 
             compliance.ApprovedNot === null;
    },

    // Helper method to get tooltip for submit button
    getSubmitButtonTooltip(compliance) {
      if (!compliance || !compliance.ExtractedData) return 'Cannot submit review';
      
      if (this.correctComplianceStatus === 'Approved') {
        return 'Compliance is already approved';
      } else if (this.correctComplianceStatus === 'Rejected') {
        return 'Compliance is already rejected';
      } else if (compliance.ApprovedNot !== null) {
        return 'Review decision already made';
      } else {
        return 'Submit your review decision';
      }
    },

    // Compliance Actions
    approveCompliance() {
      console.log('=== APPROVE COMPLIANCE CALLED ===');
      console.log('Selected approval:', this.selectedApproval);
      
      if (!this.selectedApproval || !this.getComplianceId(this.selectedApproval)) {
        console.error('No compliance selected for approval');
        return;
      }

      PopupService.confirm(
        'Are you sure you want to approve this compliance?',
        'Confirm Approval',
        () => {
          console.log('User confirmed approval, calling proceedWithComplianceApproval');
          this.proceedWithComplianceApproval();
        }
      );
    },

    proceedWithComplianceApproval() {
      console.log('=== PROCEED WITH COMPLIANCE APPROVAL ===');
      const complianceId = this.getComplianceId(this.selectedApproval);
      console.log('Compliance ID:', complianceId);
      
      // Use the same approach as ComplianceApprover - submit compliance review with approval
      const reviewData = {
        ExtractedData: this.selectedApproval.ExtractedData || {},
        approved: true,
        remarks: '',
        UserId: this.selectedApproval.UserId || this.selectedApproval.UserID || this.selectedApproval.ExtractedData?.CreatedBy,
        ReviewerId: this.currentUserId,
        currentVersion: this.selectedApproval.version || this.selectedApproval.Version || 'u1'
      };
      
      // Clear resubmission flag when approving
      if (reviewData.ExtractedData.compliance_approval) {
        reviewData.ExtractedData.compliance_approval.inResubmission = false;
        reviewData.ExtractedData.compliance_approval.approved = true;
        reviewData.ExtractedData.compliance_approval.remarks = '';
      }
      
      // Set compliance ActiveInactive to Active when approved
      reviewData.ExtractedData.ActiveInactive = 'Active';
      reviewData.ExtractedData.Status = 'Approved';
      
      console.log('Review data for approval:', reviewData);
      
      // Submit compliance review using the compliance service
      complianceService.submitComplianceReview(complianceId, reviewData)
        .then(response => {
          console.log('Compliance approved successfully:', response.data);
          
          // Update compliance status and store approval date
          this.selectedApproval.ExtractedData.Status = 'Approved';
          this.selectedApproval.ApprovedNot = true;
          
          // Store the approval date from the response
          if (response.data.ApprovedDate) {
            this.selectedApproval.ApprovedDate = response.data.ApprovedDate;
          }
          
          PopupService.success('Compliance approved successfully!', 'Compliance Approved');
          
          // Navigate back to ComplianceApprover after a short delay to ensure backend processing
          setTimeout(() => {
            this.$router.push({ name: 'ComplianceApprover' });
          }, 1500);
        })
        .catch(error => {
          this.handleError(error, 'approving compliance');
        });
    },

    rejectCompliance() {
      this.showRejectModal = true;
    },

    submitReview() {
      console.log('submitReview called with approval:', this.selectedApproval);
      
      // Prevent submission if compliance is already processed (approved or rejected)
      if (this.selectedApproval && this.selectedApproval.ExtractedData?.Status === 'Rejected') {
        console.log('Compliance is already rejected, preventing duplicate submission');
        PopupService.warning('Compliance has already been rejected and cannot be submitted again.', 'Already Rejected');
        return;
      }
      
      if (this.selectedApproval && this.selectedApproval.ExtractedData?.Status === 'Approved') {
        console.log('Compliance is already approved, preventing duplicate submission');
        PopupService.warning('Compliance has already been approved and cannot be submitted again.', 'Already Approved');
        return;
      }
      
      if (this.selectedApproval && this.selectedApproval.ApprovedNot !== null) {
        console.log('Delegating to submitComplianceReview with approval status:', this.selectedApproval.ApprovedNot);
        this.submitComplianceReview(this.selectedApproval.ApprovedNot);
      } else {
        console.error('Cannot submit review - no approval or approval status set');
      }
    },

    // Helper method to submit compliance review
    submitComplianceReview(approved, remarks = '') {
      if (!this.selectedApproval || !this.getComplianceId(this.selectedApproval)) {
        console.error('No compliance selected for review submission');
        return;
      }
      
      const complianceId = this.getComplianceId(this.selectedApproval);
      console.log(`Submitting compliance review for compliance ${complianceId}`, {
        approved: approved,
        remarks: remarks
      });
      
      // Preserve the original UserId (compliance creator) and set ReviewerId to current user
      const originalUserId = this.selectedApproval.UserId || this.selectedApproval.UserID || this.selectedApproval.ExtractedData?.CreatedBy;
      
      // Create the compliance review data
      const reviewData = {
        ExtractedData: this.selectedApproval.ExtractedData || {},
        ApprovedNot: approved,
        remarks: remarks,
        UserId: originalUserId, // Preserve original compliance creator's ID
        ReviewerId: this.currentUserId, // Set reviewer ID to current user
        currentVersion: this.selectedApproval.version || this.selectedApproval.Version || 'u1'
      };
      
      console.log('Review data being sent:', reviewData);

      // Set compliance ActiveInactive to Active when approved
      if (approved === true) {
        reviewData.ExtractedData.ActiveInactive = 'Active';
      }
      
      // If rejecting, ensure compliance_approval contains rejection remarks and clear resubmission flag
      if (approved === false && remarks) {
        if (!reviewData.ExtractedData.compliance_approval) {
          reviewData.ExtractedData.compliance_approval = {};
        }
        reviewData.ExtractedData.compliance_approval.remarks = remarks;
        reviewData.ExtractedData.compliance_approval.approved = false;
        reviewData.ExtractedData.compliance_approval.inResubmission = false; // Clear resubmission flag
      }
      
      // If approving, clear resubmission flag and set approval status
      if (approved === true) {
        if (!reviewData.ExtractedData.compliance_approval) {
          reviewData.ExtractedData.compliance_approval = {};
        }
        reviewData.ExtractedData.compliance_approval.approved = true;
        reviewData.ExtractedData.compliance_approval.remarks = '';
        reviewData.ExtractedData.compliance_approval.inResubmission = false; // Clear resubmission flag
      }
      
      // Submit compliance review using the compliance service
      complianceService.submitComplianceReview(complianceId, reviewData)
        .then(response => {
          console.log('Compliance review submitted successfully:', response.data);
          
          // Reset loading state
          this.isSubmittingRejection = false;
          
          // Update the approval data with the response
          this.selectedApproval.ApprovedNot = approved;
          this.selectedApproval.Version = response.data.Version;
          
          if (approved) {
            this.selectedApproval.ExtractedData.Status = 'Approved';
            
            // Store the approval date from the response
            if (response.data.ApprovedDate) {
              this.selectedApproval.ApprovedDate = response.data.ApprovedDate;
            }
            
            PopupService.success('Compliance approved successfully!', 'Compliance Approved');
            
            // Navigate back to ComplianceApprover after a short delay to ensure backend processing
            setTimeout(() => {
              this.$router.push({ name: 'ComplianceApprover' });
            }, 1500);
          } else {
            this.selectedApproval.ExtractedData.Status = 'Rejected';
            console.log('Compliance rejected - updating UI state');
            PopupService.success('Compliance rejected and sent back to user for revision!', 'Compliance Rejected');
          }
        })
        .catch(error => {
          this.handleError(error, 'submitting compliance review');
          // Reset loading state on error
          this.isSubmittingRejection = false;
        });
    },

    cancelRejection() {
      this.showRejectModal = false;
      this.rejectionComment = '';
      this.isSubmittingRejection = false; // Reset loading state
    },

    confirmRejection() {
      console.log('=== CONFIRM REJECTION CALLED ===');
      console.log('Rejection comment:', this.rejectionComment);
      console.log('Selected approval:', this.selectedApproval);
      
      if (!this.rejectionComment.trim()) {
        PopupService.warning('Please provide a rejection reason', 'Missing Reason');
        return;
      }

      // Prevent double submission
      if (this.isSubmittingRejection) {
        console.log('Rejection already in progress, preventing duplicate submission');
        return;
      }

      this.isSubmittingRejection = true;
      console.log('Setting isSubmittingRejection to true');
      
      // For direct compliance rejection, use submitComplianceReview with rejection reason
      if (!this.selectedApproval || !this.getComplianceId(this.selectedApproval)) {
        console.error('No compliance selected for rejection');
        this.cancelRejection();
        return;
      }
      
      // Initialize ExtractedData if it doesn't exist or is empty
      if (!this.selectedApproval.ExtractedData || Object.keys(this.selectedApproval.ExtractedData).length === 0) {
        this.selectedApproval.ExtractedData = {};
      }
      
      // Initialize compliance approval if doesn't exist
      if (!this.selectedApproval.ExtractedData.compliance_approval) {
        this.selectedApproval.ExtractedData.compliance_approval = {};
      }
      
      // Update the compliance status and approval state in the UI
      this.selectedApproval.ExtractedData.compliance_approval.approved = false;
      this.selectedApproval.ExtractedData.compliance_approval.remarks = this.rejectionComment;
      this.selectedApproval.ExtractedData.Status = 'Rejected';
      this.selectedApproval.ApprovedNot = false;
      
      console.log('Updated selectedApproval:', this.selectedApproval);
      
      // Submit the review with rejection data directly
      console.log('Calling submitComplianceReview with false and comment:', this.rejectionComment);
      this.submitComplianceReview(false, this.rejectionComment);
      
      // Close the modal after submission starts
      this.showRejectModal = false;
      this.rejectionComment = '';
    },

    // Helper method to handle and display errors
    handleError(error, context) {
      console.error(`Error ${context}:`, error);
      let errorMessage = 'An unexpected error occurred';
      
      if (error.response) {
        // The server responded with a status code outside of 2xx range
        if (error.response.data && error.response.data.error) {
          errorMessage = error.response.data.error;
        } else if (error.response.data && typeof error.response.data === 'string') {
          errorMessage = error.response.data;
        } else {
          errorMessage = `Server error: ${error.response.status}`;
        }
      } else if (error.request) {
        // The request was made but no response was received
        errorMessage = 'No response from server. Please check your connection.';
      } else {
        // Something happened in setting up the request
        errorMessage = error.message || errorMessage;
      }
      
      PopupService.error(`Error ${context}: ${errorMessage}`, 'Error');
      return errorMessage;
    }
  },
  computed: {
    // Computed property to get the correct compliance status
    correctComplianceStatus() {
      if (!this.selectedApproval) return 'Unknown';
      
      console.log('=== COMPLIANCE STATUS DEBUG ===');
      console.log('Selected approval:', this.selectedApproval);
      console.log('ApprovedNot:', this.selectedApproval.ApprovedNot);
      console.log('ExtractedData:', this.selectedApproval.ExtractedData);
      console.log('compliance_approval:', this.selectedApproval.ExtractedData?.compliance_approval);
      
      // CRITICAL: Check for resubmitted items FIRST before checking ApprovedNot
      // For resubmitted compliances, ApprovedNot might still be false from the previous rejection
      // but inResubmission flag indicates it's now pending review again
      const isResubmitted = this.selectedApproval.ExtractedData?.compliance_approval?.inResubmission === true;
      console.log('isResubmitted (early check):', isResubmitted);
      
      if (isResubmitted) {
        console.log('✅ RESUBMITTED: Overriding ApprovedNot status - returning Under Review');
        return 'Under Review';
      }
      
      // Check ApprovedNot only if NOT resubmitted
      if (this.selectedApproval.ApprovedNot === true) {
        console.log('Status: Approved (from ApprovedNot)');
        return 'Approved';
      }
      if (this.selectedApproval.ApprovedNot === false) {
        console.log('Status: Rejected (from ApprovedNot)');
        return 'Rejected';
      }
      
      // Additional check: if ApprovedNot is null (pending state) and we have rejection remarks,
      // this could be a resubmitted item where the flag wasn't properly set
      if (this.selectedApproval.ApprovedNot === null) {
        const hasRejectionRemarks = this.selectedApproval.ExtractedData?.compliance_approval?.remarks;
        if (hasRejectionRemarks) {
          console.log('✅ Found pending compliance with rejection remarks - likely resubmitted, returning Under Review status');
          return 'Under Review';
        }
      }
      
      // Fallback to ExtractedData.Status
      const fallbackStatus = this.selectedApproval.ExtractedData?.Status || 'Under Review';
      console.log('Using fallback status:', fallbackStatus);
      return fallbackStatus;
    },

    // Computed property to check if current user is the reviewer
    isCurrentUserReviewerComputed() {
      if (!this.selectedApproval || !this.currentUserId) return false;
      
      // For GRC Administrators, they can only review compliances specifically assigned to them
      if (this.isGRCAdministrator) {
        const reviewerId = this.selectedApproval.ReviewerId || this.selectedApproval.ExtractedData?.Reviewer;
        const reviewerName = this.selectedApproval.ExtractedData?.Reviewer;
        
        // Check by ID first
        if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
          return true;
        }
        
        // Check by username
        if (reviewerName && String(reviewerName) === String(this.getCurrentUserName())) {
          return true;
        }
        
        return false;
      }
      
      // Check if current user is the reviewer for this compliance
      const reviewerId = this.selectedApproval.ReviewerId || this.selectedApproval.ExtractedData?.Reviewer;
      const reviewerName = this.selectedApproval.ExtractedData?.Reviewer;
      
      // Check by ID first
      if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
        return true;
      }
      
      // Check by username (fallback for when reviewer is stored as username)
      if (reviewerName && String(reviewerName) === String(this.getCurrentUserName())) {
        return true;
      }
      
      // Check if the compliance was created by the current user (they shouldn't review their own compliances)
      if (this.isCurrentUserCreatorComputed) {
        return false;
      }
      
      return false;
    },

    // Computed property to check if current user is the creator
    isCurrentUserCreatorComputed() {
      if (!this.selectedApproval || !this.currentUserId) return false;
      
      const createdBy = this.selectedApproval.ExtractedData?.CreatedByName || this.selectedApproval.CreatedByName;
      const createdById = this.selectedApproval.ExtractedData?.CreatedBy || this.selectedApproval.CreatedBy;
      const userId = this.selectedApproval.ExtractedData?.UserID || this.selectedApproval.UserID;
      
      // Check by ID first (most reliable)
      if (createdById && String(createdById) === String(this.currentUserId)) {
        return true;
      }
      
      // Check by UserID (from approval record)
      if (userId && String(userId) === String(this.currentUserId)) {
        return true;
      }
      
      // Check by name (fallback)
      if (createdBy && String(createdBy) === String(this.getCurrentUserName())) {
        return true;
      }
      
      return false;
    },

    // Computed property to check if current user can perform review actions
    canPerformReviewActionsComputed() {
      if (!this.selectedApproval || !this.currentUserId) return false;
      
      // Only allow review actions if the user is specifically assigned as the reviewer
      // AND is not the creator of the compliance
      const canPerform = this.isCurrentUserReviewerComputed && !this.isCurrentUserCreatorComputed;
      console.log('canPerformReviewActionsComputed:', {
        isReviewer: this.isCurrentUserReviewerComputed,
        isCreator: this.isCurrentUserCreatorComputed,
        canPerform: canPerform,
        approvalId: this.selectedApproval.ApprovalId,
        ApprovedNot: this.selectedApproval.ApprovedNot,
        isResubmitted: this.isResubmittedCompliance,
        correctStatus: this.correctComplianceStatus
      });
      return canPerform;
    },

    // Computed property to check if this is a resubmitted compliance
    isResubmittedCompliance() {
      if (!this.selectedApproval || !this.selectedApproval.ExtractedData) return false;
      
      const isResubmitted = this.selectedApproval.ExtractedData?.compliance_approval?.inResubmission === true;
      
      // CRITICAL: Check for resubmitted compliance by looking at the inResubmission flag
      if (isResubmitted) {
        console.log('✅ isResubmittedCompliance: Found inResubmission=true');
        return true;
      }
      
      // Additional check: if ApprovedNot is null (pending) and we have rejection remarks,
      // this is likely a resubmitted compliance
      if (this.selectedApproval.ApprovedNot === null) {
        const hasRejectionRemarks = this.selectedApproval.ExtractedData?.compliance_approval?.remarks;
        if (hasRejectionRemarks && hasRejectionRemarks.trim().length > 0) {
          console.log('✅ isResubmittedCompliance: Found pending compliance with rejection remarks - likely resubmitted');
          return true;
        }
      }
      
      console.log('❌ isResubmittedCompliance: Not a resubmitted compliance');
      return false;
    },

    // Computed property to check if compliance has rejection remarks
    hasRejectionRemarks() {
      if (!this.selectedApproval || !this.selectedApproval.ExtractedData) return false;
      
      const remarks = this.selectedApproval.ExtractedData?.compliance_approval?.remarks;
      const hasRemarks = remarks && remarks.trim().length > 0;
      
      console.log('hasRejectionRemarks check:', {
        remarks: remarks,
        hasRemarks: hasRemarks,
        approvalId: this.selectedApproval.ApprovalId
      });
      
      return hasRemarks;
    },

    // Computed property to check if review can be submitted
    canSubmitReviewComputed() {
      if (!this.selectedApproval || !this.selectedApproval.ExtractedData) return false;
      
      // For resubmitted compliances, ApprovedNot is null and inResubmission is true
      const isResubmitted = this.selectedApproval.ExtractedData?.compliance_approval?.inResubmission === true;
      
      // Can submit review if:
      // 1. ApprovedNot is null (pending state) OR it's a resubmitted compliance AND
      // 2. Either status is "Under Review" OR it's a resubmitted compliance
      return (this.selectedApproval.ApprovedNot === null || this.isResubmittedCompliance) && 
             (this.correctComplianceStatus === 'Under Review' || isResubmitted);
    }
  }
}
</script>

<style scoped>
@import './ComplianceDetails.css';
</style>
