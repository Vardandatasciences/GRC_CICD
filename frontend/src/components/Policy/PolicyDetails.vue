<template>
  <div class="policy_details_page">
    <!-- Header with Navigation -->
    <div class="policy_header">
      <div class="policy_header_left">
        <button class="policy_back_btn" @click="goBack">
          <i class="fas fa-arrow-left"></i> {{ backButtonText }}
        </button>
        <h1 class="policy_title">
          Policy Details: {{ getPolicyId(selectedApproval) }}
          <span class="version-text" v-if="selectedApproval">(Version: {{ selectedApproval.version || selectedApproval.Version || 'u1' }})</span>
        </h1>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="policy_loading_container">
      <div class="policy_loading_spinner"></div>
      <p>Loading policy details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="policy_error_container">
      <div class="policy_error_message">
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Error Loading Policy</h3>
        <p>{{ error }}</p>
        <button class="policy_retry_btn" @click="fetchPolicyDetails">Try Again</button>
      </div>
    </div>

    <!-- Policy Details Content -->
    <div v-else-if="selectedApproval" class="policy_details_container">
      <!-- Policy Approval Section -->
      <div class="policy_approval_section">
        <h4>Policy Approval</h4>
        
        <!-- Policy status indicator -->
        <div class="policy_status_indicator">
          <span class="status-label">Status:</span>
          <span class="status-value" :class="{
            'status-approved': correctPolicyStatus === 'Approved',
            'status-rejected': correctPolicyStatus === 'Rejected',
            'status-pending': correctPolicyStatus === 'Under Review'
          }">
            {{ correctPolicyStatus }}
          </span>
          <span v-if="selectedApproval.ApprovedDate" class="approval-date">
            (Approved on: {{ formatDate(selectedApproval.ApprovedDate) }})
          </span>
          <span v-if="!canSubmitReview(selectedApproval) && canPerformReviewActions(selectedApproval)" class="status-note">
            <i class="fas fa-info-circle"></i>
            Review already submitted
          </span>
        </div>

        <div class="policy_actions">
          <!-- Final Policy Approval Button - Show when all subpolicies are approved -->
          <button 
            class="final-approve-btn" 
            @click="approveEntirePolicy()" 
            v-if="canPerformReviewActions(selectedApproval) && canApprovePolicy() && selectedApproval.ApprovedNot === null && selectedApproval.ExtractedData?.Status !== 'Rejected'"
          >
            <i class="fas fa-check-double"></i> Final Approval
          </button>
          
          <!-- Reject Button - Show when policy is under review -->
          <button class="reject-btn" @click="rejectPolicy()" v-if="canPerformReviewActions(selectedApproval) && selectedApproval.ApprovedNot === null && selectedApproval.ExtractedData?.Status !== 'Rejected'">
            <i class="fas fa-times"></i> Reject
          </button>
          
          <button 
            class="submit-btn" 
            @click="submitReview()" 
            :disabled="isSubmittingRejection || !canSubmitReview(selectedApproval)" 
            :title="getSubmitButtonTooltip(selectedApproval)"
            v-if="canPerformReviewActions(selectedApproval) && canSubmitReview(selectedApproval)"
          >
            <i class="fas fa-paper-plane"></i> {{ isSubmittingRejection ? 'Submitting...' : 'Submit Review' }}
          </button>
          
          <!-- Show message when policy is already processed -->
          <div v-if="canPerformReviewActions(selectedApproval) && !canSubmitReview(selectedApproval)" class="processed-policy-message">
            <i class="fas fa-check-circle" v-if="selectedApproval.ExtractedData?.Status === 'Approved'"></i>
            <i class="fas fa-times-circle" v-if="selectedApproval.ExtractedData?.Status === 'Rejected'"></i>
            <span v-if="selectedApproval.ExtractedData?.Status === 'Approved'">This policy has already been approved and cannot be submitted for review again.</span>
            <span v-if="selectedApproval.ExtractedData?.Status === 'Rejected'">This policy has already been rejected and cannot be submitted for review again.</span>
          </div>
          
          <!-- Show message for policy creators -->
          <div v-if="isCurrentUserCreator(selectedApproval) && selectedApproval.ApprovedNot === null && selectedApproval.ExtractedData?.Status !== 'Rejected'" class="creator-message">
            <i class="fas fa-info-circle"></i>
            <span>This policy is under review. You cannot approve or reject your own policy.</span>
          </div>
          
          <!-- Show message for administrators who are not assigned as reviewers -->
          <div v-if="isGRCAdministrator && !canPerformReviewActions(selectedApproval) && selectedApproval.ApprovedNot === null && selectedApproval.ExtractedData?.Status !== 'Rejected'" class="admin-message">
            <i class="fas fa-eye"></i>
            <span>Viewing policy. You are not assigned as the reviewer for this policy.</span>
          </div>
        </div>
      </div>

      <!-- Display policy details -->
      <div v-if="selectedApproval.ExtractedData" class="policy_info_section">
        <h4>Policy Information</h4>
        <div v-for="(value, key) in selectedApproval.ExtractedData" :key="key" class="policy_detail_row">
          <template v-if="key !== 'subpolicies' && key !== 'policy_approval' && key !== 'type' && key !== 'totalSubpolicies'">
            <strong>{{ formatFieldName(key) }}:</strong> 
            <span v-if="key === 'Status'">
              {{ correctPolicyStatus }}
            </span>
            <span v-else>{{ sanitizeValue(value) }}</span>
          </template>
        </div>
      </div>

      <!-- Display subpolicies from ExtractedData -->
      <div v-if="selectedApproval && selectedApproval.ExtractedData && selectedApproval.ExtractedData.subpolicies" class="subpolicies-section">
        <h4>Policy Subpolicies ({{ selectedApproval.ExtractedData.subpolicies.length }})</h4>
        
        <!-- Debug information -->
        <div v-if="selectedApproval.ExtractedData.subpolicies.length === 0" class="no-subpolicies-message">
          <p>No subpolicies found in this policy.</p>
        </div>

        <div v-for="subpolicy in selectedApproval.ExtractedData.subpolicies" :key="subpolicy.SubPolicyId" class="subpolicy-item">
          <div class="subpolicy-header">
            <h5 class="subpolicy-name">{{ subpolicy.SubPolicyName || 'Unnamed Subpolicy' }}</h5>
            <div class="subpolicy-header-actions">
              <span class="subpolicy-status" :class="{
                'status-approved': subpolicy.Status === 'Approved',
                'status-rejected': subpolicy.Status === 'Rejected',
                'status-pending': subpolicy.Status === 'Under Review' || !subpolicy.Status
              }">{{ subpolicy.Status || 'Under Review' }}</span>
              
              <!-- Subpolicy Actions - Only show if user is reviewer -->
              <div v-if="canPerformReviewActions(selectedApproval) && selectedApproval.ApprovedNot === null && selectedApproval.ExtractedData?.Status !== 'Rejected'" class="subpolicy-actions">
                <button 
                  class="approve-subpolicy-btn" 
                  @click="approveSubpolicy(subpolicy)"
                  :disabled="subpolicy.Status === 'Approved'"
                >
                  <i class="fas fa-check"></i>
                </button>
                <button 
                  class="reject-subpolicy-btn" 
                  @click="rejectSubpolicy(subpolicy)"
                >
                  <i class="fas fa-times"></i>
                </button>
              </div>
              
              <!-- Show message for policy creators -->
              <div v-if="isCurrentUserCreator(selectedApproval) && selectedApproval.ApprovedNot === null && selectedApproval.ExtractedData?.Status !== 'Rejected'" class="creator-message-small">
                <i class="fas fa-info-circle"></i>
                <span>Under review</span>
              </div>
            </div>
          </div>
          
          <div class="subpolicy-details">
            <div class="subpolicy-detail-item" v-if="subpolicy.Description">
              <strong>Description:</strong> {{ sanitizeValue(subpolicy.Description) }}
            </div>
            <div class="subpolicy-detail-item" v-if="subpolicy.Control">
              <strong>Control:</strong> {{ sanitizeValue(subpolicy.Control) }}
            </div>
            <div class="subpolicy-detail-item" v-if="subpolicy.Identifier">
              <strong>Identifier:</strong> {{ sanitizeValue(subpolicy.Identifier) }}
            </div>
            <div class="subpolicy-detail-item" v-if="subpolicy.Scope">
              <strong>Scope:</strong> {{ sanitizeValue(subpolicy.Scope) }}
            </div>
            <div class="subpolicy-detail-item" v-if="subpolicy.Objective">
              <strong>Objective:</strong> {{ sanitizeValue(subpolicy.Objective) }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- Add a message for rejected policies -->
      <div v-if="selectedApproval.ApprovedNot === false" class="rejected-policy-message">
        <div class="rejection-note">
          <i class="fas fa-exclamation-triangle"></i>
          This policy has been rejected. All subpolicies within this policy have been automatically rejected.
        </div>
      </div>
    </div>

    <!-- Rejection Modal -->
    <div v-if="showRejectModal" class="policy_reject_modal">
      <div class="policy_reject_modal_content">
        <h4>Rejection Reason</h4>
        <p>Please provide a reason for rejecting this {{ currentRejectionType }}</p>
        <textarea 
          v-model="rejectionComment" 
          class="policy_rejection_comment" 
          placeholder="Enter your comments here..."></textarea>
        <div class="policy_reject_modal_actions">
          <button class="policy_cancel_btn" @click="cancelRejection" :disabled="isSubmittingRejection">Cancel</button>
          <button class="policy_confirm_btn" @click="confirmRejection" :disabled="isSubmittingRejection">
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

export default {
  name: 'PolicyDetails',
  components: {
    PopupModal
  },
  props: {
    policyId: {
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
      currentRejectionType: 'policy',
      currentRejectionItem: null,
      isSubmittingRejection: false,
      // User management
      currentUserId: null,
      currentUserName: '',
      isGRCAdministrator: false,
      userInitialized: false,
      // Navigation context
      frameworkId: null,
      fromAcknowledgements: false
    }
  },
  computed: {
    backButtonText() {
      if (this.fromAcknowledgements) {
        return 'Back';
      }
      return this.frameworkId ? 'Back to Framework Policies' : 'Back to Policy Approver';
    },
    // Computed property to get the correct policy status
    correctPolicyStatus() {
      if (!this.selectedApproval) return 'Unknown';
      
      // Check ApprovedNot first (most reliable)
      if (this.selectedApproval.ApprovedNot === true) return 'Approved';
      if (this.selectedApproval.ApprovedNot === false) return 'Rejected';
      
      // Fallback to ExtractedData.Status
      return this.selectedApproval.ExtractedData?.Status || 'Under Review';
    }
  },
  async mounted() {
    // Check if we came from Framework Explorer
    this.frameworkId = this.$route.query.frameworkId || null;
    // Check if we came from Pending Acknowledgements
    this.fromAcknowledgements = this.$route.query.fromAcknowledgements === 'true';
    await this.initializeUser();
    await this.fetchPolicyDetails();
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

    async fetchPolicyDetails() {
      try {
        this.loading = true;
        this.error = null;

        console.log('Fetching policy details for ID:', this.policyId);

        // Check if policy data was passed from PolicyApprover
        const storedPolicyData = sessionStorage.getItem('policyData');
        if (storedPolicyData) {
          console.log('Using stored policy data from PolicyApprover');
          const policyData = JSON.parse(storedPolicyData);
          
          // Verify the policy ID matches
          const storedPolicyId = this.getPolicyId(policyData);
          if (storedPolicyId == this.policyId) {
            this.selectedApproval = policyData;
            console.log('Policy details loaded from stored data:', this.selectedApproval);
            
            // Clear the stored data after use
            sessionStorage.removeItem('policyData');
            
            // Fetch subpolicies if not already present
            if (!this.selectedApproval.ExtractedData.subpolicies || this.selectedApproval.ExtractedData.subpolicies.length === 0) {
              await this.fetchPolicySubpolicies(this.policyId);
            }
            
            this.loading = false;
            return;
          } else {
            console.log('Stored policy ID does not match, fetching from API');
          }
        }

        // Try to fetch the latest approval record first (for approval workflow)
        try {
          const response = await axios.get(API_ENDPOINTS.POLICY_APPROVALS_LATEST(this.policyId));
          console.log('Latest policy approval:', response.data);
          
          if (response.data && response.data.ExtractedData) {
            const latestApproval = response.data;
            
            this.selectedApproval = {
              ...latestApproval,
              ExtractedData: latestApproval.ExtractedData
            };
            
            // Update status consistency
            if (this.selectedApproval.ApprovedNot === true && this.selectedApproval.ExtractedData) {
              if (this.selectedApproval.ExtractedData.Status === 'Approved') {
                if (this.selectedApproval.ExtractedData.subpolicies) {
                  this.selectedApproval.ExtractedData.subpolicies.forEach(subpolicy => {
                    if (subpolicy.Status !== 'Approved') {
                      subpolicy.Status = 'Approved';
                    }
                  });
                }
              }
            }
            
            // Fetch subpolicies if not already present
            if (!this.selectedApproval.ExtractedData.subpolicies || this.selectedApproval.ExtractedData.subpolicies.length === 0) {
              await this.fetchPolicySubpolicies(this.policyId);
            }
            
            console.log('Policy details loaded successfully from approval data');
            return;
          }
        } catch (approvalError) {
          // If approval endpoint returns 404, fall back to regular policy details
          if (approvalError.response && approvalError.response.status === 404) {
            console.log('No approval data found, falling back to regular policy details endpoint...');
            
            try {
              // Fetch regular policy details
              const policyResponse = await axios.get(API_ENDPOINTS.POLICY_DETAILS(this.policyId));
              console.log('Policy details from regular endpoint:', policyResponse.data);
              
              if (policyResponse.data) {
                const policyData = policyResponse.data;
                
                // Transform regular policy data into the format expected by the component
                this.selectedApproval = {
                  PolicyId: policyData.PolicyId,
                  Version: policyData.CurrentVersion || 'u1',
                  ApprovedNot: null, // No approval data available
                  ExtractedData: {
                    PolicyName: policyData.PolicyName,
                    PolicyDescription: policyData.PolicyDescription,
                    Status: policyData.Status || 'Active',
                    ActiveInactive: policyData.ActiveInactive || 'Active',
                    Department: policyData.Department,
                    CreatedByName: policyData.CreatedByName,
                    CreatedByDate: policyData.CreatedByDate,
                    Applicability: policyData.Applicability,
                    DocURL: policyData.DocURL,
                    Scope: policyData.Scope,
                    Objective: policyData.Objective,
                    Identifier: policyData.Identifier,
                    PermanentTemporary: policyData.PermanentTemporary,
                    StartDate: policyData.StartDate,
                    EndDate: policyData.EndDate,
                    CurrentVersion: policyData.CurrentVersion,
                    subpolicies: policyData.subpolicies || []
                  }
                };
                
                // Fetch subpolicies if not already present
                if (!this.selectedApproval.ExtractedData.subpolicies || this.selectedApproval.ExtractedData.subpolicies.length === 0) {
                  await this.fetchPolicySubpolicies(this.policyId);
                }
                
                console.log('Policy details loaded successfully from regular endpoint');
                this.loading = false;
                return; // Successfully loaded, exit early
              } else {
                throw new Error('No policy data received from server');
              }
            } catch (policyError) {
              console.error('Error fetching regular policy details:', policyError);
              // Only throw if the fallback also fails
              throw policyError;
            }
          } else {
            // Re-throw if it's not a 404 error (we want to show error for other errors)
            throw approvalError;
          }
        }
        
        // If we get here, something went wrong
        console.error('Invalid policy data received');
        this.error = 'Invalid policy data received from server';
      } catch (error) {
        console.error('Error fetching policy details:', error);
        this.error = this.handleError(error, 'loading policy details');
      } finally {
        this.loading = false;
      }
    },

    // Fetch policy subpolicies
    async fetchPolicySubpolicies(policyId) {
      try {
        const response = await axios.get(API_ENDPOINTS.POLICY_GET_SUBPOLICIES(policyId));
        console.log('Policy subpolicies:', response.data);
        if (response.data) {
          // Update subpolicies with status
          const subpolicies = response.data.map(subpolicy => ({
            ...subpolicy,
            Status: subpolicy.Status || 'Under Review'
          }));

          // Update the policy data with subpolicies
          this.selectedApproval.ExtractedData.subpolicies = subpolicies;
          
          console.log('All subpolicies loaded');
        }
      } catch (error) {
        console.error('Error fetching subpolicies:', error);
        PopupService.error('Error loading subpolicies. Please try again.', 'Loading Error');
      }
    },

    goBack() {
      // If we came from Pending Acknowledgements, go back there
      if (this.fromAcknowledgements) {
        this.$router.push({ name: 'PendingAcknowledgements' });
      }
      // If we came from Framework Explorer, go back to Framework Policies
      else if (this.frameworkId) {
        this.$router.push({
          name: 'FrameworkPolicies',
          params: { frameworkId: this.frameworkId }
        });
      } else {
        // Otherwise, go back to Policy Approver
        this.$router.push({ name: 'PolicyApprover' });
      }
    },

    getPolicyId(policy) {
      if (!policy) return this.policyId;
      if (policy.PolicyId) {
        return typeof policy.PolicyId === 'object' ? policy.PolicyId.PolicyId : policy.PolicyId;
      }
      return policy.ApprovalId || this.policyId;
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

    // Check if current user is the reviewer for this policy
    isCurrentUserReviewer(policy) {
      if (!policy || !this.currentUserId) return false;
      
      console.log('Checking if current user is reviewer for policy:', {
        policyId: policy.PolicyId,
        currentUserId: this.currentUserId,
        currentUserName: this.getCurrentUserName(),
        reviewer: policy.ExtractedData?.Reviewer,
        reviewerId: policy.ReviewerId,
        isGRCAdmin: this.isGRCAdministrator
      });
      
      // For GRC Administrators, they can only review policies specifically assigned to them
      if (this.isGRCAdministrator) {
        // Check if they are specifically assigned as the reviewer for this policy
        const reviewerId = policy.ReviewerId || policy.ExtractedData?.Reviewer;
        const reviewerName = policy.ExtractedData?.Reviewer;
        
        // Check by ID first
        if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
          console.log('GRC Administrator is specifically assigned as reviewer for this policy (by ID)');
          return true;
        }
        
        // Check by username
        if (reviewerName && String(reviewerName) === String(this.getCurrentUserName())) {
          console.log('GRC Administrator is specifically assigned as reviewer for this policy (by username)');
          return true;
        }
        
        console.log('GRC Administrator is not assigned as reviewer for this policy');
        return false;
      }
      
      // Check if current user is the reviewer for this policy
      // The reviewer information is stored in the ReviewerId field of the approval record
      const reviewerId = policy.ReviewerId || policy.ExtractedData?.Reviewer;
      const reviewerName = policy.ExtractedData?.Reviewer;
      
      console.log('Reviewer check details:', {
        reviewerId: reviewerId,
        reviewerName: reviewerName,
        currentUserId: this.currentUserId,
        currentUserName: this.getCurrentUserName(),
        policyReviewerId: policy.ReviewerId,
        extractedDataReviewer: policy.ExtractedData?.Reviewer
      });
      
      // Check by ID first
      if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
        console.log('Current user is the assigned reviewer (by ID)');
        return true;
      }
      
      // Check by username (fallback for when reviewer is stored as username)
      if (reviewerName && String(reviewerName) === String(this.getCurrentUserName())) {
        console.log('Current user is the assigned reviewer (by username)');
        return true;
      }
      
      // Check if the policy was created by the current user (they shouldn't review their own policies)
      if (this.isCurrentUserCreator(policy)) {
        console.log('Current user is the creator - not the reviewer');
        return false;
      }
      
      console.log('Current user is not the reviewer');
      return false;
    },

    // Check if current user can perform review actions (approve/reject)
    canPerformReviewActions(policy) {
      if (!policy || !this.currentUserId) return false;
      
      // Only allow review actions if the user is specifically assigned as the reviewer
      // AND is not the creator of the policy
      return this.isCurrentUserReviewer(policy) && !this.isCurrentUserCreator(policy);
    },

    // Check if current user is the creator of this policy
    isCurrentUserCreator(policy) {
      if (!policy || !this.currentUserId) return false;
      
      const createdBy = policy.ExtractedData?.CreatedByName || policy.CreatedByName;
      const createdById = policy.ExtractedData?.CreatedBy || policy.CreatedBy;
      const userId = policy.ExtractedData?.UserID || policy.UserID;
      
      console.log('Creator check details:', {
        createdBy: createdBy,
        createdById: createdById,
        userId: userId,
        currentUserId: this.currentUserId,
        currentUserName: this.getCurrentUserName(),
        policyData: policy.ExtractedData
      });
      
      // Check by ID first (most reliable)
      if (createdById && String(createdById) === String(this.currentUserId)) {
        console.log('Current user is creator (by ID)');
        return true;
      }
      
      // Check by UserID (from approval record)
      if (userId && String(userId) === String(this.currentUserId)) {
        console.log('Current user is creator (by UserID)');
        return true;
      }
      
      // Check by name (fallback)
      if (createdBy && String(createdBy) === String(this.getCurrentUserName())) {
        console.log('Current user is creator (by name)');
        return true;
      }
      
      console.log('Current user is not the creator');
      return false;
    },

    // Helper method to get current user name
    getCurrentUserName() {
      // For current user, use stored username or fallback to localStorage
      return this.currentUserName || localStorage.getItem('user_name') || '';
    },

    // Helper method to check if review can be submitted
    canSubmitReview(policy) {
      if (!policy || !policy.ExtractedData) return false;
      
      // Can only submit review if policy is under review and not already processed
      return this.correctPolicyStatus === 'Under Review' && 
             policy.ApprovedNot === null;
    },

    // Helper method to get tooltip for submit button
    getSubmitButtonTooltip(policy) {
      if (!policy || !policy.ExtractedData) return 'Cannot submit review';
      
      if (this.correctPolicyStatus === 'Approved') {
        return 'Policy is already approved';
      } else if (this.correctPolicyStatus === 'Rejected') {
        return 'Policy is already rejected';
      } else if (policy.ApprovedNot !== null) {
        return 'Review decision already made';
      } else {
        return 'Submit your review decision';
      }
    },

    getStatusClass(status) {
      return {
        'status-approved': status === 'Approved',
        'status-rejected': status === 'Rejected',
        'status-pending': status === 'Under Review' || !status
      };
    },

    canApproveSubpolicy(subpolicy) {
      // Can't approve if already approved or rejected
      if (subpolicy.Status === 'Approved' || subpolicy.Status === 'Rejected') {
        return false;
      }

      // Can approve if under review
      return true;
    },

    areAllSubpoliciesApproved() {
      if (!this.selectedApproval?.ExtractedData?.subpolicies) return false;
      
      return this.selectedApproval.ExtractedData.subpolicies.every(subpolicy => {
        return subpolicy.Status === 'Approved';
      });
    },

    canApprovePolicy() {
      if (!this.selectedApproval || !this.selectedApproval.ExtractedData) return false;
      if (this.selectedApproval.ApprovedNot !== null) return false; // Already approved/rejected
      
      // Check if all subpolicies are approved
      return this.areAllSubpoliciesApproved();
    },

    // Policy Actions
    approveSubpolicy(subpolicy) {
      if (!this.selectedApproval || !this.selectedApproval.PolicyId) {
        console.error('No policy selected for subpolicy approval');
        return;
      }

      // Set subpolicy approval status in UI
      if (!subpolicy.approval) {
        subpolicy.approval = {};
      }
      subpolicy.approval.approved = true;
      subpolicy.approval.remarks = '';

      // Call backend endpoint for subpolicy review
      axios.put(API_ENDPOINTS.SUBPOLICY_REVIEW(subpolicy.SubPolicyId), {
        Status: 'Approved'
      })
        .then(response => {
          console.log('Subpolicy approval submitted successfully:', response.data);
          
          // Update the subpolicy status in the UI
          subpolicy.Status = 'Approved';

          // Check if all subpolicies are approved to update policy status
          const allSubpoliciesApproved = this.selectedApproval.ExtractedData.subpolicies.every(sp => 
            sp.Status === 'Approved'
          );

          if (allSubpoliciesApproved) {
            this.selectedApproval.ExtractedData.Status = 'Ready for Final Approval';
          }

          PopupService.success('Subpolicy approved successfully!', 'Subpolicy Approved');
        })
        .catch(error => {
          this.handleError(error, 'approving subpolicy');
        });
    },

    rejectSubpolicy(subpolicy) {
      if (!this.selectedApproval || !this.selectedApproval.PolicyId) {
        console.error('No policy selected for subpolicy rejection');
        return;
      }
      
      this.currentRejectionType = 'subpolicy';
      this.currentRejectionItem = subpolicy;
      this.showRejectModal = true;
    },

    rejectPolicy() {
      this.currentRejectionType = 'policy';
      this.currentRejectionItem = null;
      this.showRejectModal = true;
    },

    approveEntirePolicy() {
      if (!this.selectedApproval || !this.selectedApproval.PolicyId) {
        console.error('No policy selected for entire policy approval');
        return;
      }
      
      if (!this.canApprovePolicy()) {
        PopupService.warning('All subpolicies must be approved before approving the policy', 'Subpolicies Not Approved');
        return;
      }
      
      PopupService.confirm(
        'Are you sure you want to give final approval to this entire policy?',
        'Confirm Final Approval',
        () => {
          this.proceedWithPolicyApproval();
        }
      );
    },

    proceedWithPolicyApproval() {
      const policyId = this.getPolicyId(this.selectedApproval);
      
      // Use the same approach as PolicyApprover - submit policy review with approval
      const reviewData = {
        ExtractedData: JSON.parse(JSON.stringify(this.selectedApproval.ExtractedData)),
        approved: true,
        remarks: '',
        UserId: this.selectedApproval.UserId || this.selectedApproval.UserID || this.selectedApproval.ExtractedData?.CreatedBy,
        ReviewerId: this.currentUserId,
        currentVersion: this.selectedApproval.version || this.selectedApproval.Version || 'u1'
      };
      
      // Set all subpolicies to Approved status
      if (reviewData.ExtractedData.subpolicies) {
        reviewData.ExtractedData.subpolicies.forEach(subpolicy => {
          subpolicy.Status = 'Approved';
        });
      }
      
      // Set policy ActiveInactive to Active when approved
      reviewData.ExtractedData.ActiveInactive = 'Active';
      
      // Submit policy review
      axios.post(API_ENDPOINTS.POLICY_SUBMIT_REVIEW(policyId), reviewData)
        .then(response => {
          console.log('Policy approved successfully:', response.data);
          
          // Update policy status and store approval date
          this.selectedApproval.ExtractedData.Status = 'Approved';
          this.selectedApproval.ApprovedNot = true;
          
          // Store the approval date from the response
          if (response.data.ApprovedDate) {
            this.selectedApproval.ApprovedDate = response.data.ApprovedDate;
          }
          
          // Update all subpolicies to Approved status
          if (this.selectedApproval.ExtractedData.subpolicies) {
            this.selectedApproval.ExtractedData.subpolicies.forEach(subpolicy => {
              subpolicy.Status = 'Approved';
            });
          }
          
          PopupService.success('Policy approved successfully!', 'Policy Approved');
        })
        .catch(error => {
          this.handleError(error, 'approving entire policy');
        });
    },

    submitReview() {
      console.log('submitReview called with approval:', this.selectedApproval);
      
      // Prevent submission if policy is already processed (approved or rejected)
      if (this.selectedApproval && this.selectedApproval.ExtractedData?.Status === 'Rejected') {
        console.log('Policy is already rejected, preventing duplicate submission');
        PopupService.warning('Policy has already been rejected and cannot be submitted again.', 'Already Rejected');
        return;
      }
      
      if (this.selectedApproval && this.selectedApproval.ExtractedData?.Status === 'Approved') {
        console.log('Policy is already approved, preventing duplicate submission');
        PopupService.warning('Policy has already been approved and cannot be submitted again.', 'Already Approved');
        return;
      }
      
      if (this.selectedApproval && this.selectedApproval.ApprovedNot !== null) {
        console.log('Delegating to submitPolicyReview with approval status:', this.selectedApproval.ApprovedNot);
        this.submitPolicyReview(this.selectedApproval.ApprovedNot);
      } else {
        console.error('Cannot submit review - no approval or approval status set');
      }
    },

    // Helper method to submit policy review
    submitPolicyReview(approved, remarks = '') {
      // Prevent duplicate submission
      if (this.isSubmittingRejection) {
        console.log('Review submission already in progress, preventing duplicate call');
        return;
      }
      
      if (!this.selectedApproval || !this.selectedApproval.PolicyId) {
        console.error('No policy selected for review submission');
        return;
      }
      
      // Prevent duplicate submission if policy is already processed
      if (this.selectedApproval.ExtractedData?.Status === 'Rejected') {
        console.log('Policy is already rejected, preventing duplicate submission');
        PopupService.warning('Policy has already been rejected and cannot be submitted again.', 'Already Rejected');
        return;
      }
      
      if (this.selectedApproval.ExtractedData?.Status === 'Approved') {
        console.log('Policy is already approved, preventing duplicate submission');
        PopupService.warning('Policy has already been approved and cannot be submitted again.', 'Already Approved');
        return;
      }
      
      // Set loading state to prevent duplicate submissions
      this.isSubmittingRejection = true;
      
      const policyId = this.getPolicyId(this.selectedApproval);
      console.log(`Submitting policy review for policy ${policyId}`, {
        approved: approved,
        remarks: remarks
      });
      
      // Preserve the original UserId (policy creator) and set ReviewerId to current user
      const originalUserId = this.selectedApproval.UserId || this.selectedApproval.UserID || this.selectedApproval.ExtractedData?.CreatedBy;
      
      console.log('User ID preservation:', {
        originalUserId: originalUserId,
        currentUserId: this.currentUserId,
        selectedApprovalUserId: this.selectedApproval.UserId,
        selectedApprovalUserID: this.selectedApproval.UserID,
        extractedDataCreatedBy: this.selectedApproval.ExtractedData?.CreatedBy
      });
      
      // Create the policy review data
      const reviewData = {
        ExtractedData: JSON.parse(JSON.stringify(this.selectedApproval.ExtractedData)),
        ApprovedNot: approved,
        remarks: remarks,
        UserId: originalUserId, // Preserve original policy creator's ID
        ReviewerId: this.currentUserId, // Set reviewer ID to current user
        currentVersion: this.selectedApproval.version || this.selectedApproval.Version || 'u1'
      };
      
      // If approving, set all subpolicies to Approved status
      if (approved === true && reviewData.ExtractedData.subpolicies) {
        reviewData.ExtractedData.subpolicies.forEach(subpolicy => {
          subpolicy.Status = 'Approved';
        });
      }

      // Set policy ActiveInactive to Active when approved
      if (approved === true) {
        reviewData.ExtractedData.ActiveInactive = 'Active';
      }
      
      // If rejecting, ensure policy_approval contains rejection remarks
      if (approved === false && remarks) {
        if (!reviewData.ExtractedData.policy_approval) {
          reviewData.ExtractedData.policy_approval = {};
        }
        reviewData.ExtractedData.policy_approval.remarks = remarks;
      }
      
      // Submit policy review
      axios.post(API_ENDPOINTS.POLICY_SUBMIT_REVIEW(policyId), reviewData)
        .then(response => {
          console.log('Policy review submitted successfully:', response.data);
          console.log('Response data details:', {
            ApprovalId: response.data.ApprovalId,
            Version: response.data.Version,
            ApprovedNot: response.data.ApprovedNot,
            ApprovedDate: response.data.ApprovedDate
          });
          
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
            
            // Update all subpolicies to Approved status in the UI
            if (this.selectedApproval.ExtractedData.subpolicies) {
              this.selectedApproval.ExtractedData.subpolicies.forEach(subpolicy => {
                subpolicy.Status = 'Approved';
              });
            }
            
            PopupService.success('Policy approved successfully!', 'Policy Approved');
          } else {
            this.selectedApproval.ExtractedData.Status = 'Rejected';
            console.log('Policy rejected - updating UI state');
            PopupService.success('Policy rejected successfully!', 'Policy Rejected');
          }
        })
        .catch(error => {
          this.handleError(error, 'submitting policy review');
          // Reset loading state on error
          this.isSubmittingRejection = false;
        });
    },

    cancelRejection() {
      this.showRejectModal = false;
      this.rejectionComment = '';
      this.currentRejectionType = 'policy';
      this.currentRejectionItem = null;
      this.isSubmittingRejection = false; // Reset loading state
    },

    confirmRejection() {
      if (!this.rejectionComment.trim()) {
        PopupService.warning('Please provide a rejection reason', 'Missing Reason');
        return;
      }

      // Prevent double submission
      if (this.isSubmittingRejection) {
        console.log('Rejection already in progress, preventing duplicate submission');
        return;
      }

      console.log('DEBUG: confirmRejection called');
      console.log('DEBUG: currentRejectionType:', this.currentRejectionType);
      console.log('DEBUG: currentRejectionItem:', this.currentRejectionItem);
      console.log('DEBUG: selectedApproval:', this.selectedApproval);

      this.isSubmittingRejection = true;
      const policyId = this.getPolicyId(this.selectedApproval);
      console.log('DEBUG: policyId:', policyId);
      
      if (this.currentRejectionType === 'subpolicy' && this.currentRejectionItem) {
        const subpolicy = this.currentRejectionItem;
        console.log('DEBUG: Rejecting subpolicy - subpolicy:', subpolicy);
        console.log('DEBUG: rejection_reason:', this.rejectionComment);
        
        const url = API_ENDPOINTS.SUBPOLICY_REVIEW(subpolicy.SubPolicyId);
        console.log('DEBUG: Calling URL:', url);
        
        // Call backend endpoint for subpolicy rejection
        axios.put(url, {
          Status: 'Rejected',
          remarks: this.rejectionComment
        })
          .then(response => {
            console.log('Subpolicy rejected successfully:', response.data);

          // Update local state
            subpolicy.Status = 'Rejected';
            this.selectedApproval.ExtractedData.Status = 'Rejected';
            this.selectedApproval.ApprovedNot = false;
            
            // Update the approval record with the response data if available
            if (response.data.ApprovalId) {
              this.selectedApproval.ApprovalId = response.data.ApprovalId;
            }
            if (response.data.Version) {
              this.selectedApproval.Version = response.data.Version;
            }
            
            PopupService.success('Subpolicy rejected. Policy has been rejected and sent back for revision.', 'Subpolicy Rejected');
            this.cancelRejection();
          })
          .catch(error => {
            console.log('DEBUG: Error rejecting subpolicy:', error);
            console.log('DEBUG: Error response:', error.response);
            this.handleError(error, 'rejecting subpolicy');
          })
          .finally(() => {
            this.isSubmittingRejection = false;
          });
          
      } else if (this.currentRejectionType === 'policy') {
        // For direct policy rejection, use submitPolicyReview with rejection reason
        if (!this.selectedApproval || !this.selectedApproval.PolicyId) {
          console.error('No policy selected for rejection');
          this.cancelRejection();
            return;
          }
        
        // Initialize policy approval if doesn't exist
        if (!this.selectedApproval.ExtractedData.policy_approval) {
          this.selectedApproval.ExtractedData.policy_approval = {};
        }
        
        // Update the policy status and approval state in the UI
        this.selectedApproval.ExtractedData.policy_approval.approved = false;
        this.selectedApproval.ExtractedData.policy_approval.remarks = this.rejectionComment;
        this.selectedApproval.ExtractedData.Status = 'Rejected';
        this.selectedApproval.ApprovedNot = false;
        
        // Submit the review with rejection data
        this.submitPolicyReview(false, this.rejectionComment);
        
        this.cancelRejection();
        this.isSubmittingRejection = false;
      }
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
  }
}
</script>

<style scoped>
@import './PolicyDetails.css';

/* Page-specific styles */
.policy-details-page {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20px;
  margin-left: 250px; /* Account for sidebar width */
  width: calc(100% - 250px); /* Adjust width to account for sidebar */
  transition: margin-left 0.3s ease, width 0.3s ease;
}

.page-header {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.back-btn {
  background: #e2e8f0;
  border: none;
  border-radius: 8px;
  padding: 10px 16px;
  color: #4a5568;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
}

.back-btn:hover {
  background: #cbd5e0;
  color: #2d3748;
}

.page-title {
  margin: 0;
  font-size: 1.8rem;
  color: #2d3748;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.policy-details-container {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.policy-info-section {
  margin-bottom: 32px;
  padding-bottom: 32px;
  border-bottom: 1px solid #e2e8f0;
}

.policy-info-section h4 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.2rem;
  color: #2d3748;
  font-weight: 600;
}

.loading-container, .error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 32px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  text-align: center;
  color: #e74c3c;
}

.error-message i {
  font-size: 3rem;
  margin-bottom: 16px;
  color: #e74c3c;
}

.error-message h3 {
  margin-bottom: 12px;
  color: #e74c3c;
}

.error-message p {
  margin-bottom: 20px;
  color: #6c757d;
}

.retry-btn {
  padding: 10px 20px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.2s;
}

.retry-btn:hover {
  background-color: #2980b9;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .policy-details-page {
    padding: 10px;
    margin-left: 0; /* Remove sidebar margin on mobile */
    width: 100%; /* Full width on mobile */
  }
  
  .page-header {
    padding: 16px;
  }
  
  .page-title {
    font-size: 1.4rem;
  }
  
  .policy-details-container {
    padding: 20px;
  }
}

/* Sidebar responsive adjustments */
@media (max-width: 1024px) {
  .policy-details-page {
    margin-left: 0; /* Remove sidebar margin on tablet */
    width: 100%; /* Full width on tablet */
  }
}
</style>
