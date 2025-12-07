<template>
  <div class="framework_details_page">
    <!-- Header with Navigation -->
      <div class="framework_header">
      <div class="framework_header_left">
        <button class="policy-dashboard-back-btn" @click="goBack">
          <i class="fas fa-arrow-left"></i> 
        </button>
        <h1 class="framework_title">
          Framework Details: {{ getFrameworkId(selectedApproval) }}
          <span class="version-text" v-if="selectedApproval">(Version: {{ selectedApproval.version || selectedApproval.Version || 'u1' }})</span>
        </h1>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="framework_loading_container">
      <div class="framework_loading_spinner"></div>
      <p>Loading framework details...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="framework_error_container">
      <div class="framework_error_message">
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Error Loading Framework</h3>
        <p>{{ error }}</p>
        <button class="framework_retry_btn" @click="fetchFrameworkDetails">Try Again</button>
      </div>
    </div>

    <!-- Framework Details Content -->
    <div v-else-if="selectedApproval" class="framework_details_container">
      <!-- Framework Approval Section -->
      <div class="framework_approval_section">
        <h4>Framework Approval</h4>
        
        <!-- Framework status indicator -->
        <div class="framework-status-indicator">
          <span class="status-label">Status:</span>
          <span class="status-value" :class="{
            'status-approved': correctFrameworkStatus === 'Approved',
            'status-rejected': correctFrameworkStatus === 'Rejected',
            'status-pending': correctFrameworkStatus === 'Under Review'
          }">
            {{ correctFrameworkStatus }}
          </span>
          <span v-if="selectedApproval.ApprovedDate" class="approval-date">
            (Approved on: {{ formatDate(selectedApproval.ApprovedDate) }})
          </span>
          <span v-if="!canSubmitReview(selectedApproval) && canPerformReviewActions(selectedApproval)" class="status-note">
            <i class="fas fa-info-circle"></i>
            Review already submitted
          </span>
        </div>

        <div class="framework-actions" v-if="isReadyToShowActions">
          <!-- Final Framework Approval Button - Show when all policies are approved -->
          <button 
            class="final-approve-btn" 
            @click="approveEntireFramework()" 
            v-if="canPerformReviewActions(selectedApproval) && canApproveFramework() && selectedApproval.ApprovedNot === null && selectedApproval.ExtractedData?.Status !== 'Rejected'"
          >
            <i class="fas fa-check-double"></i> Final Approval
          </button>
          
          <!-- Approve Framework Button - Show when framework is under review but not all policies are approved -->
          <button 
            class="approve-btn" 
            @click="approveFramework()" 
            v-if="canPerformReviewActions(selectedApproval) && !canApproveFramework() && selectedApproval.ApprovedNot === null && selectedApproval.ExtractedData?.Status !== 'Rejected'"
          >
            <i class="fas fa-check"></i> Approve Framework
          </button>
          
          <!-- Reject Button - Show when framework is under review -->
          <button class="reject-btn" @click="rejectFramework()" v-if="canPerformReviewActions(selectedApproval) && selectedApproval.ApprovedNot === null && selectedApproval.ExtractedData?.Status !== 'Rejected'">
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
        </div>
      </div>

      <!-- Display framework details -->
      <div v-if="selectedApproval.ExtractedData" class="framework_info_section">
        <h4>Framework Information</h4>
        <div v-for="(value, key) in selectedApproval.ExtractedData" :key="key" class="framework_detail_row">
          <template v-if="key !== 'policies' && key !== 'framework_approval' && key !== 'type' && key !== 'totalPolicies' && key !== 'totalSubpolicies'">
            <strong>{{ formatFieldName(key) }}:</strong> 
            <span v-if="key === 'Status'">
              {{ correctFrameworkStatus }}
            </span>
            <span v-else>{{ value }}</span>
          </template>
        </div>
      </div>

      <!-- Display policies from ExtractedData -->
      <div v-if="selectedApproval && selectedApproval.ExtractedData && selectedApproval.ExtractedData.policies" class="policies-section">
        <h4>Framework Policies ({{ selectedApproval.ExtractedData.policies.length }})</h4>
        
        <!-- Debug information -->
        <div v-if="selectedApproval.ExtractedData.policies.length === 0" class="no-policies-message">
          <p>No policies found in this framework.</p>
        </div>

        <div v-for="policy in selectedApproval.ExtractedData.policies" :key="policy.PolicyId" class="policy-item">
          <div class="policy-header">
            <h5 class="policy-name">{{ policy.PolicyName || 'Unnamed Policy' }}</h5>
            <div class="policy-header-actions">
              <span class="policy-status" :class="{
                'status-approved': policy.Status === 'Approved',
                'status-rejected': policy.Status === 'Rejected',
                'status-pending': policy.Status === 'Under Review' || !policy.Status
              }">{{ policy.Status || 'Under Review' }}</span>
              
              <!-- Policy Actions - Only show if user is reviewer and everything is ready -->
              <div v-if="isReadyToShowActions && canPerformReviewActions(selectedApproval) && selectedApproval.ApprovedNot === null && selectedApproval.ExtractedData?.Status !== 'Rejected'" class="policy-actions">
                <button 
                  class="approve-policy-btn" 
                  @click="approvePolicy(policy)"
                  :disabled="!canApprovePolicy(policy)"
                  :title="!canApprovePolicy(policy) ? 'All subpolicies must be approved first' : 'Approve Policy'"
                >
                  <i class="fas fa-check"></i>
                </button>
                <button 
                  class="reject-policy-btn" 
                  @click="rejectPolicy(policy)"
                >
                  <i class="fas fa-times"></i>
                </button>
              </div>
              
              <!-- Show message for framework creators -->
              <div v-if="isCurrentUserCreator(selectedApproval) && selectedApproval.ApprovedNot === null && selectedApproval.ExtractedData?.Status !== 'Rejected'" class="creator-message-small">
                <i class="fas fa-info-circle"></i>
                <span>Under review</span>
              </div>
            </div>
          </div>
          
          <div class="policy-details">
            <div class="policy-detail-item" v-if="policy.PolicyDescription">
              <strong>Description:</strong> {{ policy.PolicyDescription }}
            </div>
            <div class="policy-detail-item" v-if="policy.Objective">
              <strong>Objective:</strong> {{ policy.Objective }}
            </div>
            <div class="policy-detail-item" v-if="policy.Scope">
              <strong>Scope:</strong> {{ policy.Scope }}
            </div>
            <div class="policy-detail-item" v-if="policy.Department">
              <strong>Department:</strong> {{ policy.Department }}
            </div>
            <div class="policy-detail-item" v-if="policy.Applicability">
              <strong>Applicability:</strong> {{ policy.Applicability }}
            </div>
            <div class="policy-detail-item" v-if="policy.Identifier">
              <strong>Identifier:</strong> {{ policy.Identifier }}
            </div>
            <div class="policy-detail-item" v-if="policy.CoverageRate">
              <strong>Coverage Rate:</strong> {{ policy.CoverageRate }}%
            </div>
            <div class="policy-detail-item" v-if="policy.PolicyType">
              <strong>Policy Type:</strong> {{ policy.PolicyType }}
            </div>
            <div class="policy-detail-item" v-if="policy.PolicyCategory">
              <strong>Policy Category:</strong> {{ policy.PolicyCategory }}
            </div>
            <div class="policy-detail-item" v-if="policy.PolicySubCategory">
              <strong>Policy Sub Category:</strong> {{ policy.PolicySubCategory }}
            </div>

            <!-- Subpolicies Section - Multiple conditions to catch all cases -->
            <div v-if="policy.subpolicies && Array.isArray(policy.subpolicies) && policy.subpolicies.length > 0" class="subpolicies-section">
              <h6 class="subpolicies-heading">
                <i class="fas fa-list-ul"></i>
                Sub-Policies ({{ policy.subpolicies.length }})
              </h6>
              <div v-for="subpolicy in policy.subpolicies" :key="subpolicy.SubPolicyId || subpolicy.id" class="subpolicy-item">
                <div class="subpolicy-header">
                  <div class="subpolicy-name">
                    <strong>{{ subpolicy.SubPolicyName || subpolicy.name || subpolicy.Identifier || 'Unnamed Subpolicy' }}</strong>
                  </div>
                  <div class="subpolicy-actions" v-if="isReadyToShowActions && canPerformReviewActions(selectedApproval) && selectedApproval.ApprovedNot === null && selectedApproval.ExtractedData?.Status !== 'Rejected'">
                    <button 
                      class="approve-btn" 
                      @click="approveSubpolicy(policy, subpolicy)"
                      :disabled="subpolicy.Status === 'Approved'"
                      :class="{ 'approved': subpolicy.Status === 'Approved' }"
                    >
                      <i class="fas fa-check"></i>
                    </button>
                    <button 
                      class="reject-btn" 
                      @click="rejectSubpolicy(policy, subpolicy)"
                      :disabled="subpolicy.Status === 'Rejected'"
                      :class="{ 'rejected': subpolicy.Status === 'Rejected' }"
                    >
                      <i class="fas fa-times"></i>
                    </button>
                  </div>
                </div>
                <div class="subpolicy-content">
                  <div class="subpolicy-detail" v-if="subpolicy.Description">
                    <strong>Description:</strong> {{ subpolicy.Description }}
                  </div>
                  <div class="subpolicy-detail" v-if="subpolicy.Control">
                    <strong>Control:</strong> {{ subpolicy.Control }}
                  </div>
                  <div class="subpolicy-detail" v-if="subpolicy.Identifier">
                    <strong>Identifier:</strong> {{ subpolicy.Identifier }}
                  </div>
                  <div class="subpolicy-status" :class="getStatusClass(subpolicy.Status || 'Under Review')">
                    Status: {{ subpolicy.Status || 'Under Review' }}
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Alternative check for different subpolicy structures -->
            <div v-else-if="policy.SubPolicies && Array.isArray(policy.SubPolicies) && policy.SubPolicies.length > 0" class="subpolicies-section">
              <h6 class="subpolicies-heading">
                <i class="fas fa-list-ul"></i>
                Sub-Policies ({{ policy.SubPolicies.length }})
              </h6>
              <div v-for="subpolicy in policy.SubPolicies" :key="subpolicy.SubPolicyId || subpolicy.id" class="subpolicy-item">
                <div class="subpolicy-header">
                  <div class="subpolicy-name">
                    <strong>{{ subpolicy.SubPolicyName || subpolicy.name || subpolicy.Identifier || 'Unnamed Subpolicy' }}</strong>
                  </div>
                  <div class="subpolicy-actions" v-if="isReadyToShowActions && canPerformReviewActions(selectedApproval) && selectedApproval.ApprovedNot === null && selectedApproval.ExtractedData?.Status !== 'Rejected'">
                    <button 
                      class="approve-btn" 
                      @click="approveSubpolicy(policy, subpolicy)"
                      :disabled="subpolicy.Status === 'Approved'"
                      :class="{ 'approved': subpolicy.Status === 'Approved' }"
                    >
                      <i class="fas fa-check"></i>
                    </button>
                    <button 
                      class="reject-btn" 
                      @click="rejectSubpolicy(policy, subpolicy)"
                      :disabled="subpolicy.Status === 'Rejected'"
                      :class="{ 'rejected': subpolicy.Status === 'Rejected' }"
                    >
                      <i class="fas fa-times"></i>
                    </button>
                  </div>
                </div>
                <div class="subpolicy-content">
                  <div class="subpolicy-detail" v-if="subpolicy.Description">
                    <strong>Description:</strong> {{ subpolicy.Description }}
                  </div>
                  <div class="subpolicy-detail" v-if="subpolicy.Control">
                    <strong>Control:</strong> {{ subpolicy.Control }}
                  </div>
                  <div class="subpolicy-detail" v-if="subpolicy.Identifier">
                    <strong>Identifier:</strong> {{ subpolicy.Identifier }}
                  </div>
                  <div class="subpolicy-status" :class="getStatusClass(subpolicy.Status || 'Under Review')">
                    Status: {{ subpolicy.Status || 'Under Review' }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Message when no subpolicies found -->
            <div v-else class="no-subpolicies-message">
              <p><em>No sub-policies found for this policy.</em></p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Add a message for rejected frameworks -->
      <div v-if="selectedApproval.ApprovedNot === false" class="rejected-framework-message">
        <div class="rejection-note">
          <i class="fas fa-exclamation-triangle"></i>
          This framework has been rejected. All policies and subpolicies within this framework have been automatically rejected.
        </div>
      </div>
    </div>

    <!-- Rejection Modal -->
    <div v-if="showRejectModal" class="reject-modal">
      <div class="reject-modal-content">
        <h4>Rejection Reason</h4>
        <p>Please provide a reason for rejecting this {{ currentRejectionType }}</p>
        <textarea 
          v-model="rejectionComment" 
          class="rejection-comment" 
          placeholder="Enter your comments here..."></textarea>
        <div class="reject-modal-actions">
          <button class="cancel-btn" @click="cancelRejection" :disabled="isSubmittingRejection">Cancel</button>
          <button class="confirm-btn" @click="confirmRejection" :disabled="isSubmittingRejection">
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
  name: 'FrameworkDetails',
  components: {
    PopupModal
  },
  props: {
    frameworkId: {
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
      currentRejectionType: 'framework',
      currentRejectionItem: null,
      isSubmittingRejection: false,
      // User management
      currentUserId: null,
      currentUserName: '',
      isGRCAdministrator: false,
      userInitialized: false,
      // Track when permissions are ready
      permissionsEvaluated: false
    }
  },
  async mounted() {
    console.log('🚀 FrameworkDetails mounted, initializing...');
    // Ensure user is initialized before fetching framework details
    await this.initializeUser();
    console.log('✅ User initialized in FrameworkDetails:', {
      currentUserId: this.currentUserId,
      currentUserName: this.currentUserName,
      isGRCAdmin: this.isGRCAdministrator,
      userInitialized: this.userInitialized
    });
    
    // Add a small delay to ensure all reactive properties are updated
    await new Promise(resolve => setTimeout(resolve, 50));
    
    await this.fetchFrameworkDetails();
    console.log('✅ Framework details loaded in FrameworkDetails');
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

    async fetchFrameworkDetails() {
      try {
        this.loading = true;
        this.error = null;

        console.log('📥 Fetching framework details for ID:', this.frameworkId);
        console.log('📥 User initialized:', this.userInitialized);
        console.log('📥 Current user ID:', this.currentUserId);

        // Ensure user is initialized before proceeding
        if (!this.userInitialized || !this.currentUserId) {
          console.warn('⚠️ User not initialized yet, waiting...');
          // Wait a bit for user initialization
          await new Promise(resolve => setTimeout(resolve, 100));
          
          // Check again
          if (!this.userInitialized || !this.currentUserId) {
            console.error('❌ User initialization failed');
            this.error = 'User initialization failed. Please refresh the page.';
            this.loading = false;
            return;
          }
        }

        // Check if framework data was passed from FrameworkApprover
        const storedFrameworkData = sessionStorage.getItem('frameworkData');
        if (storedFrameworkData) {
          console.log('Found stored framework data from FrameworkApprover');
          sessionStorage.removeItem('frameworkData'); // Clear immediately
        }

        // Always fetch fresh data from API to ensure we have complete reviewer information including ReviewerId
        console.log('Fetching fresh framework data from API to ensure ReviewerId is present');
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_APPROVALS_LATEST(this.frameworkId));
        console.log('Latest framework approval from API:', response.data);
        
        if (response.data && response.data.ExtractedData) {
          const latestApproval = response.data;
          
          this.selectedApproval = {
            ...latestApproval,
            ExtractedData: latestApproval.ExtractedData
          };
          
          console.log('📋 Framework loaded with reviewer info:', {
            frameworkId: this.selectedApproval.FrameworkId,
            reviewerId: this.selectedApproval.ReviewerId,
            reviewer: this.selectedApproval.ExtractedData?.Reviewer,
            approvalId: this.selectedApproval.ApprovalId,
            hasReviewerId: !!this.selectedApproval.ReviewerId
          });
          
          // Update status consistency
          if (this.selectedApproval.ApprovedNot === true && this.selectedApproval.ExtractedData) {
            if (this.selectedApproval.ExtractedData.Status === 'Approved') {
              if (this.selectedApproval.ExtractedData.policies) {
                this.selectedApproval.ExtractedData.policies.forEach(policy => {
                  if (policy.Status !== 'Approved') {
                    policy.Status = 'Approved';
                  }
                  
                  if (policy.subpolicies) {
                    policy.subpolicies.forEach(subpolicy => {
                      if (subpolicy.Status !== 'Approved') {
                        subpolicy.Status = 'Approved';
                      }
                    });
                  }
                });
              }
            }
          }
          
          // Fetch policies if not already present
          if (!this.selectedApproval.ExtractedData.policies || this.selectedApproval.ExtractedData.policies.length === 0) {
            await this.fetchFrameworkPolicies(this.frameworkId);
          }
          
          // Wait for Vue reactivity to complete
          await this.$nextTick();
          await this.$nextTick();
          
          console.log('Framework details loaded successfully from API');
          console.log('🔐 Now checking permissions with complete data...');
          console.log('🔐 Current User ID:', this.currentUserId);
          console.log('🔐 Framework ReviewerId:', this.selectedApproval.ReviewerId);
          console.log('🔐 Can perform review actions:', this.canPerformReviewActions(this.selectedApproval));
          console.log('🔐 Is current user reviewer:', this.isCurrentUserReviewer(this.selectedApproval));
          console.log('🔐 Is current user creator:', this.isCurrentUserCreator(this.selectedApproval));
          
          // Mark permissions as evaluated
          this.permissionsEvaluated = true;
          console.log('✅ Permissions evaluated after API load');
          
          // Force a complete re-render to ensure all conditionals are evaluated correctly
            this.$forceUpdate();
          
          // Wait one more tick to ensure render completes
          await this.$nextTick();
        } else {
          console.error('Invalid approval data received:', response.data);
          this.error = 'Invalid framework data received from server';
        }
      } catch (error) {
        console.error('Error fetching framework details:', error);
        this.error = this.handleError(error, 'loading framework details');
      } finally {
        this.loading = false;
      }
    },

    // Fetch framework policies and subpolicies
    async fetchFrameworkPolicies(frameworkId) {
      try {
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_POLICIES(frameworkId));
        console.log('Framework policies:', response.data);
        if (response.data) {
          // Update policies with status
          const policies = response.data.map(policy => ({
            ...policy,
            Status: policy.Status || 'Under Review',
            subpolicies: []
          }));

          // Update the framework data with policies
          this.selectedApproval.ExtractedData.policies = policies;

          // For each policy, fetch its subpolicies
          const subpolicyPromises = policies.map(policy => 
            axios.get(API_ENDPOINTS.POLICY_GET_SUBPOLICIES(policy.PolicyId))
              .then(subResponse => {
                console.log(`Subpolicies for policy ${policy.PolicyId}:`, subResponse.data);
                if (subResponse.data) {
                  // Find the policy and update its subpolicies
                  const policyToUpdate = this.selectedApproval.ExtractedData.policies.find(p => p.PolicyId === policy.PolicyId);
                  if (policyToUpdate) {
                    policyToUpdate.subpolicies = subResponse.data.map(sub => ({
                      ...sub,
                      Status: sub.Status || 'Under Review'
                    }));
                    console.log(`Updated policy ${policy.PolicyId} with ${subResponse.data.length} subpolicies`);
                  }
                }
              })
              .catch(error => {
                console.error(`Error fetching subpolicies for policy ${policy.PolicyId}:`, error);
              })
          );

          // Wait for all subpolicy requests to complete
          await Promise.all(subpolicyPromises);
          console.log('All policies and subpolicies loaded');
        }
      } catch (error) {
        console.error('Error fetching policies:', error);
        PopupService.error('Error loading policies. Please try again.', 'Loading Error');
      }
    },

    goBack() {
      this.$router.push({ name: 'FrameworkApprover' });
    },

    getFrameworkId(framework) {
      if (!framework) return this.frameworkId;
      if (framework.FrameworkId) {
        return typeof framework.FrameworkId === 'object' ? framework.FrameworkId.FrameworkId : framework.FrameworkId;
      }
      return framework.ApprovalId || this.frameworkId;
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

    // Check if current user is the reviewer for this framework
    isCurrentUserReviewer(framework) {
      if (!framework) {
        console.log('⚠️ FrameworkDetails: No framework provided to isCurrentUserReviewer');
        return false;
      }
      
      if (!this.currentUserId) {
        console.log('⚠️ FrameworkDetails: No currentUserId set in isCurrentUserReviewer');
        console.log('⚠️ FrameworkDetails: userInitialized:', this.userInitialized);
        return false;
      }
      
      console.log('✅ FrameworkDetails: Checking if current user is reviewer for framework:', {
        frameworkId: framework.FrameworkId,
        frameworkReviewerId: framework.ReviewerId,
        extractedDataReviewer: framework.ExtractedData?.Reviewer,
        currentUserId: this.currentUserId,
        currentUserName: this.getCurrentUserName(),
        isGRCAdmin: this.isGRCAdministrator,
        userInitialized: this.userInitialized,
        reviewerIdType: typeof framework.ReviewerId,
        currentUserIdType: typeof this.currentUserId
      });
      
      // For GRC Administrators, they can only review frameworks specifically assigned to them
      if (this.isGRCAdministrator) {
        // Check if they are specifically assigned as the reviewer for this framework
        const reviewerId = framework.ReviewerId || framework.ExtractedData?.Reviewer;
        const reviewerName = framework.ExtractedData?.Reviewer;
        
        // Check by ID first
        if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
          console.log('GRC Administrator is specifically assigned as reviewer for this framework (by ID)');
          return true;
        }
        
        // Check by username
        if (reviewerName && String(reviewerName) === String(this.getCurrentUserName())) {
          console.log('GRC Administrator is specifically assigned as reviewer for this framework (by username)');
          return true;
        }
        
        console.log('GRC Administrator is not assigned as reviewer for this framework');
        return false;
      }
      
      // Check if current user is the reviewer for this framework
      // The reviewer information is stored in the ReviewerId field of the approval record
      const reviewerId = framework.ReviewerId || framework.ExtractedData?.Reviewer;
      const reviewerName = framework.ExtractedData?.Reviewer;
      
      console.log('Reviewer check details:', {
        reviewerId: reviewerId,
        reviewerName: reviewerName,
        currentUserId: this.currentUserId,
        currentUserName: this.getCurrentUserName(),
        frameworkReviewerId: framework.ReviewerId,
        extractedDataReviewer: framework.ExtractedData?.Reviewer
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
      
      // Check if the framework was created by the current user (they shouldn't review their own frameworks)
      if (this.isCurrentUserCreator(framework)) {
        console.log('Current user is the creator - not the reviewer');
        return false;
      }
      
      console.log('Current user is not the reviewer');
      return false;
    },

    // Check if current user can perform review actions (approve/reject)
    canPerformReviewActions(framework) {
      if (!framework || !this.currentUserId) return false;
      
      // Only allow review actions if the user is specifically assigned as the reviewer
      // AND is not the creator of the framework
      return this.isCurrentUserReviewer(framework) && !this.isCurrentUserCreator(framework);
    },

    // Check if current user is the creator of this framework
    isCurrentUserCreator(framework) {
      if (!framework || !this.currentUserId) return false;
      
      const createdBy = framework.ExtractedData?.CreatedByName || framework.CreatedByName;
      const createdById = framework.ExtractedData?.CreatedBy || framework.CreatedBy;
      const userId = framework.ExtractedData?.UserID || framework.UserID;
      
      console.log('Creator check details:', {
        createdBy: createdBy,
        createdById: createdById,
        userId: userId,
        currentUserId: this.currentUserId,
        currentUserName: this.getCurrentUserName(),
        frameworkData: framework.ExtractedData
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
    canSubmitReview(framework) {
      if (!framework || !framework.ExtractedData) return false;
      
      // Can only submit review if framework is under review and not already processed
      return this.correctFrameworkStatus === 'Under Review' && 
             framework.ApprovedNot === null;
    },

    // Helper method to get tooltip for submit button
    getSubmitButtonTooltip(framework) {
      if (!framework || !framework.ExtractedData) return 'Cannot submit review';
      
      if (this.correctFrameworkStatus === 'Approved') {
        return 'Framework is already approved';
      } else if (this.correctFrameworkStatus === 'Rejected') {
        return 'Framework is already rejected';
      } else if (framework.ApprovedNot !== null) {
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

    canApprovePolicy(policy) {
      // Can't approve if already approved or rejected
      if (policy.Status === 'Approved' || policy.Status === 'Rejected') {
        return false;
      }

      // If policy has subpolicies, all must be approved
      if (policy.subpolicies && policy.subpolicies.length > 0) {
        return policy.subpolicies.every(sub => sub.Status === 'Approved');
      }

      // If no subpolicies, can approve
      return true;
    },

    areAllPoliciesApproved() {
      if (!this.selectedApproval?.ExtractedData?.policies) return false;
      
      return this.selectedApproval.ExtractedData.policies.every(policy => {
        // Check policy status
        if (policy.Status !== 'Approved') {
          // If not approved, check if all subpolicies are approved
          return policy.subpolicies && policy.subpolicies.every(sub => sub.Status === 'Approved');
        }
        return true;
      });
    },

    canApproveFramework() {
      if (!this.selectedApproval || !this.selectedApproval.ExtractedData) return false;
      if (this.selectedApproval.ApprovedNot !== null) return false; // Already approved/rejected
      
      // Check if all policies are approved
      return this.areAllPoliciesApproved();
    },

    // Framework Actions
    approvePolicy(policy) {
      if (!this.selectedApproval || !this.selectedApproval.FrameworkId) {
        console.error('No framework selected for policy approval');
        return;
      }

      // Check if all subpolicies are approved
      if (policy.subpolicies && policy.subpolicies.length > 0) {
        const allSubpoliciesApproved = policy.subpolicies.every(sub => sub.Status === 'Approved');
        if (!allSubpoliciesApproved) {
          PopupService.warning('All subpolicies must be approved before approving the policy', 'Subpolicies Not Approved');
          return;
        }
      }

      const frameworkId = this.getFrameworkId(this.selectedApproval);

      // Call backend endpoint
      axios.put(API_ENDPOINTS.FRAMEWORK_POLICY_APPROVE_REJECT(frameworkId, policy.PolicyId), {
        approved: true,
        submit_review: false // Don't submit review automatically
      })
        .then(response => {
          console.log('Policy approved successfully:', response.data);

          // Update policy status
          policy.Status = 'Approved';

          // Check if all policies are approved to update framework status
          const allPoliciesApproved = this.selectedApproval.ExtractedData.policies.every(p => 
            p.Status === 'Approved' || (p.subpolicies && p.subpolicies.every(sub => sub.Status === 'Approved'))
          );

          if (allPoliciesApproved) {
            this.selectedApproval.ExtractedData.Status = 'Ready for Final Approval';
          }

          PopupService.success('Policy approved successfully!', 'Policy Approved');
        })
        .catch(error => {
          this.handleError(error, 'approving policy');
        });
    },

    rejectPolicy(policy) {
      if (!this.selectedApproval || !this.selectedApproval.FrameworkId) {
        console.error('No framework selected for policy rejection');
        return;
      }
      
      this.currentRejectionType = 'policy';
      this.currentRejectionItem = policy;
      this.showRejectModal = true;
    },

    approveSubpolicy(policy, subpolicy) {
      if (!this.selectedApproval || !this.selectedApproval.FrameworkId) {
        console.error('No framework selected for subpolicy approval');
        return;
      }
      
      const frameworkId = this.getFrameworkId(this.selectedApproval);
      
      // Call backend endpoint
      axios.put(API_ENDPOINTS.FRAMEWORK_POLICY_SUBPOLICY_APPROVE_REJECT(frameworkId, policy.PolicyId, subpolicy.SubPolicyId), {
          approved: true,
        submit_review: false // Don't submit review automatically
      })
        .then(response => {
          console.log('Subpolicy approved successfully:', response.data);
          
          // Update subpolicy status
          subpolicy.Status = 'Approved';
          
          // Check if all subpolicies in this policy are approved
          const allSubpoliciesApproved = policy.subpolicies && 
            policy.subpolicies.every(sp => sp.Status === 'Approved');
          
          if (allSubpoliciesApproved) {
            // Update policy status to indicate it's ready for approval
            policy.Status = 'Ready for Approval';
            PopupService.success('All subpolicies approved. Policy is now ready for approval.', 'Subpolicies Approved');
          } else {
            PopupService.success('Subpolicy approved successfully!', 'Subpolicy Approved');
          }
        })
        .catch(error => {
          this.handleError(error, 'approving subpolicy');
        });
    },

    rejectSubpolicy(policy, subpolicy) {
      if (!this.selectedApproval || !this.selectedApproval.FrameworkId) {
        console.error('No framework selected for subpolicy rejection');
        return;
      }
      
      this.currentRejectionType = 'subpolicy';
      this.currentRejectionItem = { policy, subpolicy };
      this.showRejectModal = true;
    },

    rejectFramework() {
      this.currentRejectionType = 'framework';
      this.currentRejectionItem = null;
      this.showRejectModal = true;
    },

    approveFramework() {
      if (!this.selectedApproval || !this.selectedApproval.FrameworkId) {
        console.error('No framework selected for approval');
        return;
      }
      
      PopupService.confirm(
        'Are you sure you want to approve this framework? This will set the framework status to approved.',
        'Confirm Framework Approval',
        () => {
          this.proceedWithFrameworkApproval();
        }
      );
    },

    approveEntireFramework() {
      if (!this.selectedApproval || !this.selectedApproval.FrameworkId) {
        console.error('No framework selected for entire framework approval');
        return;
      }
      
      if (!this.canApproveFramework()) {
        PopupService.warning('All policies must be approved before approving the framework', 'Policies Not Approved');
        return;
      }
      
      PopupService.confirm(
        'Are you sure you want to give final approval to this entire framework?',
        'Confirm Final Approval',
        () => {
          this.proceedWithFrameworkApproval();
        }
      );
    },

    proceedWithFrameworkApproval() {
      const frameworkId = this.getFrameworkId(this.selectedApproval);
      
      // Call backend endpoint for final framework approval
      axios.put(API_ENDPOINTS.FRAMEWORK_APPROVE_FINAL(frameworkId))
        .then(response => {
          console.log('Framework approved successfully:', response.data);
          
          // Update framework status and store approval date
          this.selectedApproval.ExtractedData.Status = 'Approved';
          this.selectedApproval.ApprovedNot = true;
          
          // Store the approval date from the response
          if (response.data.ApprovedDate) {
            this.selectedApproval.ApprovedDate = response.data.ApprovedDate;
          }
          
          // Update all policies and subpolicies to Approved status
          if (this.selectedApproval.ExtractedData.policies) {
            this.selectedApproval.ExtractedData.policies.forEach(policy => {
              policy.Status = 'Approved';
              
              if (policy.subpolicies) {
                policy.subpolicies.forEach(subpolicy => {
                  subpolicy.Status = 'Approved';
                });
              }
            });
          }
          
          PopupService.success('Framework approved successfully!', 'Framework Approved');
        })
        .catch(error => {
          this.handleError(error, 'approving entire framework');
        });
    },

    submitReview() {
      console.log('submitReview called with approval:', this.selectedApproval);
      
      // Prevent submission if framework is already processed (approved or rejected)
      if (this.selectedApproval && this.selectedApproval.ExtractedData?.Status === 'Rejected') {
        console.log('Framework is already rejected, preventing duplicate submission');
        PopupService.warning('Framework has already been rejected and cannot be submitted again.', 'Already Rejected');
        return;
      }
      
      if (this.selectedApproval && this.selectedApproval.ExtractedData?.Status === 'Approved') {
        console.log('Framework is already approved, preventing duplicate submission');
        PopupService.warning('Framework has already been approved and cannot be submitted again.', 'Already Approved');
        return;
      }
      
      if (this.selectedApproval && this.selectedApproval.ApprovedNot !== null) {
        console.log('Delegating to submitFrameworkReview with approval status:', this.selectedApproval.ApprovedNot);
        this.submitFrameworkReview(this.selectedApproval.ApprovedNot);
      } else {
        console.error('Cannot submit review - no approval or approval status set');
      }
    },

    // Helper method to submit framework review
    submitFrameworkReview(approved, remarks = '') {
      if (!this.selectedApproval || !this.selectedApproval.FrameworkId) {
        console.error('No framework selected for review submission');
        return;
      }
      
      // Prevent duplicate submission if framework is already processed
      if (this.selectedApproval.ExtractedData?.Status === 'Rejected') {
        console.log('Framework is already rejected, preventing duplicate submission');
        PopupService.warning('Framework has already been rejected and cannot be submitted again.', 'Already Rejected');
        return;
      }
      
      if (this.selectedApproval.ExtractedData?.Status === 'Approved') {
        console.log('Framework is already approved, preventing duplicate submission');
        PopupService.warning('Framework has already been approved and cannot be submitted again.', 'Already Approved');
        return;
      }
      
      const frameworkId = this.getFrameworkId(this.selectedApproval);
      console.log(`Submitting framework review for framework ${frameworkId}`, {
        approved: approved,
        remarks: remarks
      });
      
      // Preserve the original UserId (framework creator) and set ReviewerId to current user
      const originalUserId = this.selectedApproval.UserId || this.selectedApproval.UserID || this.selectedApproval.ExtractedData?.CreatedBy;
      
      console.log('User ID preservation:', {
        originalUserId: originalUserId,
        currentUserId: this.currentUserId,
        selectedApprovalUserId: this.selectedApproval.UserId,
        selectedApprovalUserID: this.selectedApproval.UserID,
        extractedDataCreatedBy: this.selectedApproval.ExtractedData?.CreatedBy
      });
      
      // Create the framework review data
      const reviewData = {
        ExtractedData: JSON.parse(JSON.stringify(this.selectedApproval.ExtractedData)),
        ApprovedNot: approved,
        remarks: remarks,
        UserId: originalUserId, // Preserve original framework creator's ID
        ReviewerId: this.currentUserId, // Set reviewer ID to current user
        currentVersion: this.selectedApproval.version || this.selectedApproval.Version || 'u1'
      };
      
      // If approving, set all policies and subpolicies to Approved status
      if (approved === true && reviewData.ExtractedData.policies) {
        reviewData.ExtractedData.policies.forEach(policy => {
          policy.Status = 'Approved';
          policy.ActiveInactive = 'Active'; // Set policies to Active when framework is approved
          
              if (policy.subpolicies) {
            policy.subpolicies.forEach(subpolicy => {
              subpolicy.Status = 'Approved';
            });
              }
            });
          }

      // Set framework ActiveInactive to Active when approved
      if (approved === true) {
        reviewData.ExtractedData.ActiveInactive = 'Active';
      }
      
      // If rejecting, ensure framework_approval contains rejection remarks
      if (approved === false && remarks) {
        if (!reviewData.ExtractedData.framework_approval) {
          reviewData.ExtractedData.framework_approval = {};
        }
        reviewData.ExtractedData.framework_approval.remarks = remarks;
      }
      
      // Submit framework review
      axios.post(API_ENDPOINTS.FRAMEWORK_SUBMIT_REVIEW(frameworkId), reviewData)
        .then(response => {
          console.log('Framework review submitted successfully:', response.data);
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
            
            // Update all policies and subpolicies to Approved status in the UI
            if (this.selectedApproval.ExtractedData.policies) {
              this.selectedApproval.ExtractedData.policies.forEach(policy => {
                policy.Status = 'Approved';
                
                if (policy.subpolicies) {
                  policy.subpolicies.forEach(subpolicy => {
                    subpolicy.Status = 'Approved';
                  });
                }
              });
            }
            
            PopupService.success('Framework approved successfully!', 'Framework Approved');
          } else {
            this.selectedApproval.ExtractedData.Status = 'Rejected';
            console.log('Framework rejected - updating UI state');
            PopupService.success('Framework rejected successfully!', 'Framework Rejected');
          }
        })
        .catch(error => {
          this.handleError(error, 'submitting framework review');
          // Reset loading state on error
          this.isSubmittingRejection = false;
        });
    },

    cancelRejection() {
      this.showRejectModal = false;
      this.rejectionComment = '';
      this.currentRejectionType = 'framework';
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
      const frameworkId = this.getFrameworkId(this.selectedApproval);
      console.log('DEBUG: frameworkId:', frameworkId);
      
      if (this.currentRejectionType === 'subpolicy' && this.currentRejectionItem) {
        const { policy, subpolicy } = this.currentRejectionItem;
        console.log('DEBUG: Rejecting subpolicy - policy:', policy);
        console.log('DEBUG: Rejecting subpolicy - subpolicy:', subpolicy);
        console.log('DEBUG: rejection_reason:', this.rejectionComment);
        
        const url = API_ENDPOINTS.FRAMEWORK_POLICY_SUBPOLICY_APPROVE_REJECT(frameworkId, policy.PolicyId, subpolicy.SubPolicyId);
        console.log('DEBUG: Calling URL:', url);
        
        // Call backend endpoint for subpolicy rejection
        axios.put(url, {
            approved: false,
          rejection_reason: this.rejectionComment,
          submit_review: true // Add flag to submit review automatically
        })
          .then(response => {
            console.log('Subpolicy rejected successfully:', response.data);

          // Update local state
            subpolicy.Status = 'Rejected';
            policy.Status = 'Rejected';
            if (policy.subpolicies) {
              policy.subpolicies.forEach(sp => {
                sp.Status = 'Rejected';
              });
            }
            this.selectedApproval.ExtractedData.Status = 'Rejected';
            this.selectedApproval.ApprovedNot = false;
            
            // Update the approval record with the response data if available
            if (response.data.ApprovalId) {
              this.selectedApproval.ApprovalId = response.data.ApprovalId;
            }
            if (response.data.Version) {
              this.selectedApproval.Version = response.data.Version;
            }
            
            PopupService.success('Subpolicy rejected. Framework has been rejected and sent back for revision.', 'Subpolicy Rejected');
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
          
      } else if (this.currentRejectionType === 'policy' && this.currentRejectionItem) {
        const policy = this.currentRejectionItem;
        console.log('DEBUG: Rejecting policy - policy:', policy);
        console.log('DEBUG: rejection_reason:', this.rejectionComment);
        
        const url = API_ENDPOINTS.FRAMEWORK_POLICY_APPROVE_REJECT(frameworkId, policy.PolicyId);
        console.log('DEBUG: Calling URL:', url);
        
        // Call backend endpoint for policy rejection
        axios.put(url, {
          approved: false,
          rejection_reason: this.rejectionComment,
          submit_review: true // Add flag to submit review automatically
        })
          .then(response => {
            console.log('Policy rejected successfully:', response.data);

          // Update local state
            policy.Status = 'Rejected';
            if (policy.subpolicies) {
              policy.subpolicies.forEach(subpolicy => {
                subpolicy.Status = 'Rejected';
              });
            }
            this.selectedApproval.ExtractedData.Status = 'Rejected';
            this.selectedApproval.ApprovedNot = false;
            
            // Update the approval record with the response data if available
            if (response.data.ApprovalId) {
              this.selectedApproval.ApprovalId = response.data.ApprovalId;
            }
            if (response.data.Version) {
              this.selectedApproval.Version = response.data.Version;
            }
            
            PopupService.success('Policy rejected. Framework has been rejected and sent back for revision.', 'Policy Rejected');
            this.cancelRejection();
          })
          .catch(error => {
            console.log('DEBUG: Error rejecting policy:', error);
            console.log('DEBUG: Error response:', error.response);
            this.handleError(error, 'rejecting policy');
          })
          .finally(() => {
            this.isSubmittingRejection = false;
          });
          
      } else if (this.currentRejectionType === 'framework') {
        // For direct framework rejection, use submitFrameworkReview with rejection reason
        if (!this.selectedApproval || !this.selectedApproval.FrameworkId) {
          console.error('No framework selected for rejection');
          this.cancelRejection();
            return;
          }
        
        // Initialize framework approval if doesn't exist
        if (!this.selectedApproval.ExtractedData.framework_approval) {
          this.selectedApproval.ExtractedData.framework_approval = {};
        }
        
        // Update the framework status and approval state in the UI
        this.selectedApproval.ExtractedData.framework_approval.approved = false;
        this.selectedApproval.ExtractedData.framework_approval.remarks = this.rejectionComment;
        this.selectedApproval.ExtractedData.Status = 'Rejected';
        this.selectedApproval.ApprovedNot = false;
        
        // Submit the review with rejection data
        this.submitFrameworkReview(false, this.rejectionComment);
        
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
  },
  watch: {
    // Watch for user initialization to complete
    userInitialized(newVal) {
      if (newVal) {
        console.log('✅ FrameworkDetails: User initialized, current user ID:', this.currentUserId);
        console.log('✅ FrameworkDetails: User initialized, current user name:', this.currentUserName);
        console.log('✅ FrameworkDetails: User initialized, is GRC Admin:', this.isGRCAdministrator);
        // Force update to re-evaluate computed properties and conditional rendering
        this.$forceUpdate();
      }
    },
    // Watch for current user ID changes
    currentUserId(newVal, oldVal) {
      console.log('🔄 FrameworkDetails: Current user ID changed from', oldVal, 'to', newVal);
      if (newVal && this.userInitialized) {
        // Force re-evaluation of reviewer permissions
        this.$forceUpdate();
      }
    },
    // Watch for selected approval changes
    selectedApproval(newVal) {
      if (newVal && this.currentUserId) {
        console.log('📄 FrameworkDetails: Framework loaded, checking permissions...');
        console.log('📄 FrameworkDetails: Can perform review actions:', this.canPerformReviewActions(newVal));
        console.log('📄 FrameworkDetails: Is current user reviewer:', this.isCurrentUserReviewer(newVal));
        console.log('📄 FrameworkDetails: Is current user creator:', this.isCurrentUserCreator(newVal));
      }
    }
  },
  computed: {
    // Computed property to get the correct framework status
    correctFrameworkStatus() {
      if (!this.selectedApproval) return 'Unknown';
      
      // Check ApprovedNot first (most reliable)
      if (this.selectedApproval.ApprovedNot === true) return 'Approved';
      if (this.selectedApproval.ApprovedNot === false) return 'Rejected';
      
      // Fallback to ExtractedData.Status
      return this.selectedApproval.ExtractedData?.Status || 'Under Review';
    },
    
    // Computed property to check if we're ready to show reviewer actions
    isReadyToShowActions() {
      const ready = this.userInitialized && 
                    this.currentUserId && 
                    this.selectedApproval &&
                    !this.loading &&
                    this.permissionsEvaluated;
      
      console.log('🎯 isReadyToShowActions:', {
        ready,
        userInitialized: this.userInitialized,
        currentUserId: this.currentUserId,
        hasSelectedApproval: !!this.selectedApproval,
        loading: this.loading,
        permissionsEvaluated: this.permissionsEvaluated
      });
      
      return ready;
    }
  }
}
</script>

<style scoped>
@import './FrameworkDetails.css';

/* Page-specific overrides */

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

.framework-details-container {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.framework-info-section {
  margin-bottom: 32px;
  padding-bottom: 32px;
  border-bottom: 1px solid #e2e8f0;
}

.framework-info-section h4 {
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
  .framework-details-page {
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
  
  .framework-details-container {
    padding: 20px;
  }
}

/* Approve Button Styling */
.approve-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
}

.approve-btn:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(16, 185, 129, 0.3);
}

.approve-btn:active {
  transform: translateY(0);
}

.approve-btn i {
  font-size: 16px;
}

/* Sidebar responsive adjustments */
@media (max-width: 1024px) {
  .framework-details-page {
    margin-left: 0; /* Remove sidebar margin on tablet */
    width: 100%; /* Full width on tablet */
  }
}
</style>
