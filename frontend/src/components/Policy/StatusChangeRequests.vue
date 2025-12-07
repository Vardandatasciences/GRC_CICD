<template>
  <div class="statuschange-container">
    <div class="statuschange-header">
      <h2 class="statuschange-heading">Status Change Approval Tasks</h2>
      <div class="statuschange-actions">
        <!-- User selection moved to framework filter section -->
      </div>
    </div>

    <!-- Framework Filter Section -->
    <div class="framework_filter_section">
      <!-- Framework Filter -->
      <div class="framework_filter_block">
        <div class="framework_filter_label">
          <i class="fas fa-filter"></i>
          <span>FRAMEWORK FILTER</span>
        </div>
        <select 
          id="framework-filter" 
          v-model="selectedFrameworkId" 
          @change="onFrameworkChange"
          class="framework_filter_dropdown"
        >
          <option value="">All Frameworks</option>
          <option 
            v-for="framework in filteredFrameworks" 
            :key="framework.id" 
            :value="framework.id"
          >
            {{ framework.name }}
          </option>
        </select>
      </div>
      
      <!-- User Selection for Administrators -->
      <div v-if="isAdministrator" class="framework_filter_block">
        <div class="framework_filter_label">
          <i class="fas fa-users"></i>
          <span>USER SELECTION</span>
        </div>
        <select 
          id="userSelect" 
          v-model="selectedUserId" 
          @change="onUserChange" 
          class="framework_filter_dropdown"
        >
          <option v-for="user in availableUsers" :key="user.UserId" :value="user.UserId">
            {{ user.UserName }} ({{ user.Role }}) - ID: {{ user.UserId }}
          </option>
        </select>
      </div>
    </div>



    <!-- Add tabs for My Tasks and Reviewer Tasks -->
    <div class="tabs-container">
      <div class="tabs">
        <button 
          class="tab-button"
          :class="{ active: activeTab === 'myTasks' }"
          @click="switchTab('myTasks')"
        >
          My Tasks
          <span class="tab-count">{{ myTasksCount }}</span>
        </button>
        <button 
          class="tab-button"
          :class="{ active: activeTab === 'reviewerTasks' }"
          @click="switchTab('reviewerTasks')"
        >
          Reviewer Tasks
          <span class="tab-count">{{ reviewerTasksCount }}</span>
        </button>
      </div>
    </div>
    
    <!-- Tab Content -->
    <div class="tab-content">
      <!-- My Tasks Tab -->
      <div v-if="activeTab === 'myTasks'" class="approvals-list">
                 <h3>
           My Status Change Tasks
         </h3>
        
        <div v-if="isLoadingMyTasks" class="loading-indicator">
          <i class="fas fa-spinner fa-spin"></i> Loading my tasks...
        </div>
        
        <div v-else-if="myTasks.length === 0" class="no-tasks-message">
          <div class="no-tasks-icon">
            <i class="fas fa-clipboard-check"></i>
          </div>
          <h4>No My Tasks</h4>
          <p>{{ selectedUserInfo && isAdministrator ? `${selectedUserInfo.UserName} doesn't have` : 'You don\'t have' }} any status change tasks at the moment.</p>
        </div>
        
        <div v-else>
          <!-- Collapsible Table for My Tasks -->
          <CollapsibleTable
            v-if="myTasksPendingRequests.length > 0"
            :sectionConfig="{ name: 'Pending', statusClass: 'pending', tasks: myTasksPendingTableRows }"
            :tableHeaders="pendingTableHeaders"
            :isExpanded="true"
            @taskClick="openRequestDetails"
          />
          
          <!-- Framework Grid for non-pending my tasks -->
          <div class="framework-grid">
            <div v-for="request in myTasks.filter(r => r.Status !== 'Pending Approval')" :key="request.ApprovalId" class="framework-card">
              <div class="framework-header">
                <i :class="request.ItemType === 'policy' ? 'fas fa-file-alt' : 'fas fa-book'"></i>
                <span>{{ request.FrameworkName || request.PolicyName }}</span>
              </div>
              
              <div class="category-tag">
                {{ request.ItemType === 'policy' ? 'Department' : 'Category' }}: 
                {{ request.Category || request.Department }}
              </div>
              
              <div class="framework-description">{{ request.Reason }}</div>
              
              <div class="framework-footer">
                <div class="status-toggle">
                  <input 
                    type="checkbox" 
                    :checked="request.Status === 'Approved'" 
                    disabled
                  />
                  <span class="switch-label" :class="{
                    'active': request.Status === 'Rejected' || request.Status === 'Pending Approval',
                    'inactive': request.Status === 'Approved'
                  }">
                    {{ request.Status === 'Approved' ? 'Inactive' : 
                       request.Status === 'Rejected' ? 'Active' : 'Pending' }}
                  </span>
                </div>
                
                <div class="actions">
                  <button class="view-btn" @click="openRequestDetails(request)">
                    <i class="fas fa-eye"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Reviewer Tasks Tab -->
      <div v-if="activeTab === 'reviewerTasks'" class="approvals-list">
                 <h3>
           Reviewer Status Change Tasks
         </h3>
        
        <div v-if="isLoadingReviewerTasks" class="loading-indicator">
          <i class="fas fa-spinner fa-spin"></i> Loading reviewer tasks...
        </div>
        
        <div v-else-if="reviewerTasks.length === 0" class="no-tasks-message">
          <div class="no-tasks-icon">
            <i class="fas fa-clipboard-check"></i>
          </div>
          <h4>No Reviewer Tasks</h4>
          <p>{{ selectedUserInfo && isAdministrator ? `${selectedUserInfo.UserName} doesn't have` : 'You don\'t have' }} any reviewer tasks at the moment.</p>
        </div>
        
        <div v-else>
          <!-- Collapsible Table for Reviewer Tasks -->
          <CollapsibleTable
            v-if="reviewerTasksPendingRequests.length > 0"
            :sectionConfig="{ name: 'Pending', statusClass: 'pending', tasks: reviewerTasksPendingTableRows }"
            :tableHeaders="pendingTableHeaders"
            :isExpanded="true"
            @taskClick="openRequestDetails"
          />
          
          <!-- Framework Grid for non-pending reviewer tasks -->
          <div class="framework-grid">
            <div v-for="request in reviewerTasks.filter(r => r.Status !== 'Pending Approval')" :key="request.ApprovalId" class="framework-card">
              <div class="framework-header">
                <i :class="request.ItemType === 'policy' ? 'fas fa-file-alt' : 'fas fa-book'"></i>
                <span>{{ request.FrameworkName || request.PolicyName }}</span>
              </div>
              
              <div class="category-tag">
                {{ request.ItemType === 'policy' ? 'Department' : 'Category' }}: 
                {{ request.Category || request.Department }}
              </div>
              
              <div class="framework-description">{{ request.Reason }}</div>
              
              <div class="framework-footer">
                <div class="status-toggle">
                  <input 
                    type="checkbox" 
                    :checked="request.Status === 'Approved'" 
                    disabled
                  />
                  <span class="switch-label" :class="{
                    'active': request.Status === 'Rejected' || request.Status === 'Pending Approval',
                    'inactive': request.Status === 'Approved'
                  }">
                    {{ request.Status === 'Approved' ? 'Inactive' : 
                       request.Status === 'Rejected' ? 'Active' : 'Pending' }}
                  </span>
                </div>
                
                <div class="actions">
                  <button class="view-btn" @click="openRequestDetails(request)">
                    <i class="fas fa-eye"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Legacy content for backwards compatibility -->
    <div v-if="!activeTab" class="legacy-content">
      <div v-if="isLoading" class="loading-indicator">
        <i class="fas fa-spinner fa-spin"></i> Loading status change requests...
      </div>
      
      <div v-else-if="requests.length === 0" class="no-requests">
        <p>No status change requests found.</p>
      </div>
      
      <div v-else>
        <!-- Collapsible Table for Pending Approval Tasks -->
        <CollapsibleTable
          v-if="pendingRequests.length > 0"
          :sectionConfig="{ name: 'Pending', statusClass: 'pending', tasks: pendingTableRows }"
          :tableHeaders="pendingTableHeaders"
          :isExpanded="true"
          @taskClick="openRequestDetails"
        />
        
        <!-- Framework Grid for non-pending requests -->
        <div class="framework-grid">
          <div v-for="request in requests.filter(r => r.Status !== 'Pending Approval')" :key="request.ApprovalId" class="framework-card">
            <div class="framework-header">
              <i :class="request.ItemType === 'policy' ? 'fas fa-file-alt' : 'fas fa-book'"></i>
              <span>{{ request.FrameworkName || request.PolicyName }}</span>
            </div>
            
            <div class="category-tag">
              {{ request.ItemType === 'policy' ? 'Department' : 'Category' }}: 
              {{ request.Category || request.Department }}
            </div>
            
            <div class="framework-description">{{ request.Reason }}</div>
            
            <div class="framework-footer">
              <div class="status-toggle">
                <input 
                  type="checkbox" 
                  :checked="request.Status === 'Approved'" 
                  disabled
                />
                <span class="switch-label" :class="{
                  'active': request.Status === 'Rejected' || request.Status === 'Pending Approval',
                  'inactive': request.Status === 'Approved'
                }">
                  {{ request.Status === 'Approved' ? 'Inactive' : 
                     request.Status === 'Rejected' ? 'Active' : 'Pending' }}
                </span>
              </div>
              
              <div class="actions">
                <button class="view-btn" @click="openRequestDetails(request)">
                  <i class="fas fa-eye"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Status Change Request Details Modal -->
    <div v-if="showDetails && selectedRequest" class="framework-details-modal">
      <div class="framework-details-content">
        <span class="close-x" @click="closeRequestDetails" title="Close">&times;</span>
        <h3>
          <span class="detail-type-indicator">
            {{ selectedRequest.ItemType === 'policy' ? 'POLICY' : 'FRAMEWORK' }} STATUS CHANGE REQUEST
          </span> 
          Details: {{ selectedRequest.FrameworkName || selectedRequest.PolicyName }}
          <span class="version-pill">Version: {{ selectedRequest.Version }}</span>
        </h3>
        
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
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import policyDataService from '@/services/policyService'
import { API_ENDPOINTS } from '../../config/api.js'
import { PopupService } from '@/modules/popus/popupService'
import PopupModal from '@/modules/popus/PopupModal.vue'
import CollapsibleTable from '@/components/CollapsibleTable.vue'

const router = useRouter()
const requests = ref([])
const isLoading = ref(false)
const isLoadingMyTasks = ref(false)
const isLoadingReviewerTasks = ref(false)
const showDetails = ref(false)
const selectedRequest = ref(null)
const reviewers = ref([])
const currentUserId = ref(null)

// New tab functionality
const activeTab = ref('myTasks') // Default to My Tasks tab
const isAdministrator = ref(false) // Will be set based on user role
const availableUsers = ref([]) // List of users for administrator dropdown
const selectedUserId = ref(null) // Currently selected user (for administrators)
const selectedUserInfo = ref(null) // Information about selected user
const myTasks = ref([]) // Tasks assigned to user
const reviewerTasks = ref([]) // Tasks where user is reviewer

// Framework functionality
const frameworks = ref([]) // List of frameworks
const selectedFrameworkId = ref('') // Currently selected framework

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

// Switch between tabs
const switchTab = (tab) => {
  activeTab.value = tab
}


// Framework-related methods
const fetchFrameworks = async () => {
  try {
    console.log('🔍 DEBUG: Checking for cached frameworks in StatusChangeRequests...')

    if (!window.policyDataFetchPromise && !policyDataService.hasFrameworksListCache()) {
      console.log('🚀 DEBUG: Starting policy prefetch from StatusChangeRequests (user navigated directly)...')
      window.policyDataFetchPromise = policyDataService.fetchAllPolicyData()
    }

    if (window.policyDataFetchPromise) {
      console.log('⏳ DEBUG: Waiting for policy prefetch to complete in StatusChangeRequests...')
      try {
        await window.policyDataFetchPromise
        console.log('✅ DEBUG: Policy prefetch completed for StatusChangeRequests')
      } catch (prefetchError) {
        console.warn('⚠️ DEBUG: Policy prefetch failed in StatusChangeRequests, will fetch directly', prefetchError)
      }
    }

    if (policyDataService.hasFrameworksListCache()) {
      console.log('✅ DEBUG: Using cached frameworks in StatusChangeRequests')
      const cachedFrameworks = policyDataService.getFrameworksList() || []
      frameworks.value = cachedFrameworks.map(fw => ({
        id: fw.FrameworkId || fw.id,
        name: fw.FrameworkName || fw.name
      }))
      console.log('✅ DEBUG: Frameworks loaded from cache:', frameworks.value)

      await checkSelectedFrameworkFromSession()
      return
    }

    console.log('⚠️ DEBUG: No cached frameworks, fetching via API in StatusChangeRequests...')
    const response = await axios.get(API_ENDPOINTS.FRAMEWORKS)
    frameworks.value = response.data.map(fw => ({
      id: fw.FrameworkId,
      name: fw.FrameworkName
    }))
    console.log('✅ DEBUG: Frameworks loaded:', frameworks.value)

    policyDataService.setFrameworksList(response.data)
    
    await checkSelectedFrameworkFromSession()
  } catch (error) {
    console.error('❌ DEBUG: Error fetching frameworks:', error)
  }
}

// Check for selected framework from session and set it as default
const checkSelectedFrameworkFromSession = async () => {
  try {
    console.log('🔍 DEBUG: Checking for selected framework from session in StatusChangeRequests...')
    const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
    console.log('📊 DEBUG: Selected framework response:', response.data)
    
    if (response.data && response.data.success) {
      // Check if a framework is selected (not null)
      if (response.data.frameworkId) {
      const sessionFrameworkId = response.data.frameworkId
      console.log('✅ DEBUG: Found selected framework in session:', sessionFrameworkId)
      
      // Check if this framework exists in our loaded frameworks
      const frameworkExists = frameworks.value.find(f => f.id.toString() === sessionFrameworkId.toString())
      
      if (frameworkExists) {
        selectedFrameworkId.value = sessionFrameworkId.toString()
        console.log('✅ DEBUG: Set selectedFrameworkId from session:', selectedFrameworkId.value)
        console.log('✅ DEBUG: Framework exists in loaded frameworks:', frameworkExists.name)
      } else {
        console.log('⚠️ DEBUG: Framework from session not found in loaded frameworks')
        console.log('📋 DEBUG: Available frameworks:', frameworks.value.map(f => ({ id: f.id, name: f.name })))
        }
      } else {
        // "All Frameworks" is selected (frameworkId is null)
        console.log('ℹ️ DEBUG: No framework selected in session (All Frameworks selected)')
        console.log('🌐 DEBUG: Clearing framework selection to show all frameworks')
        selectedFrameworkId.value = null
      }
    } else {
      console.log('ℹ️ DEBUG: No framework found in session')
      selectedFrameworkId.value = null
    }
  } catch (error) {
    console.error('❌ DEBUG: Error checking selected framework from session:', error)
    selectedFrameworkId.value = null
  }
}

// Handle framework selection change
const onFrameworkChange = async () => {
  if (selectedFrameworkId.value) {
    // Save the selected framework to session
    try {
      const userId = localStorage.getItem('user_id') || 'default_user'
      console.log('🔍 DEBUG: Saving framework to session in StatusChangeRequests:', selectedFrameworkId.value)
      
      const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
        frameworkId: selectedFrameworkId.value,
        userId: userId
      })
      
      if (response.data && response.data.success) {
        console.log('✅ DEBUG: Framework saved to session successfully in StatusChangeRequests')
        console.log('🔑 DEBUG: Session key:', response.data.sessionKey)
      } else {
        console.error('❌ DEBUG: Failed to save framework to session in StatusChangeRequests')
      }
    } catch (error) {
      console.error('❌ DEBUG: Error saving framework to session in StatusChangeRequests:', error)
    }
    
    // Note: Removed loadUserTasks() call to keep content consistent
    // Framework filter is now only visual and doesn't affect displayed content
  }
}

// Clear framework filter
// Get selected framework name for display

// Computed property to filter frameworks - show only the selected framework
const filteredFrameworks = computed(() => {
  if (selectedFrameworkId.value) {
    // If a framework is selected, show only that framework
    const selectedFramework = frameworks.value.find(f => f.id.toString() === selectedFrameworkId.value.toString());
    return selectedFramework ? [selectedFramework] : [];
  } else {
    // If no framework is selected, show all frameworks
    return frameworks.value;
  }
})

// Handle user selection change
const onUserChange = () => {
  console.log('onUserChange called with selectedUserId:', selectedUserId.value)
  
  // Clear existing data first
  myTasks.value = []
  reviewerTasks.value = []
  
  if (selectedUserId.value) {
    // First try to find user in availableUsers
    let selectedUser = availableUsers.value.find(u => u.UserId == selectedUserId.value)
    
    // If not found in availableUsers but it's the current user, use selectedUserInfo
    if (!selectedUser && selectedUserId.value == currentUserId.value && selectedUserInfo.value) {
      selectedUser = selectedUserInfo.value
    }
    
    selectedUserInfo.value = selectedUser
    console.log('Selected user info:', selectedUser)
    // Force reload with new user
    loadUserTasks()
  } else {
    selectedUserInfo.value = null
    console.log('Cleared tasks - no user selected')
  }
}

// Load tasks for the selected user
const loadUserTasks = async () => {
  const targetUserId = selectedUserId.value || currentUserId.value
  
  console.log('Loading user tasks for user ID:', targetUserId)
  console.log('Selected user ID:', selectedUserId.value)
  console.log('Current user ID:', currentUserId.value)
  console.log('Is Administrator:', isAdministrator.value)
  
  // If administrator and no user selected, don't load any tasks
  if (isAdministrator.value && !selectedUserId.value) {
    console.log('Administrator with no user selected - clearing tasks')
    myTasks.value = []
    reviewerTasks.value = []
    return
  }
  
  try {
    // Set loading states
    isLoadingMyTasks.value = true
    isLoadingReviewerTasks.value = true
    
    // Fetch My Tasks (where user is the creator/owner)
    await fetchMyTasks(targetUserId)
    
    // Fetch Reviewer Tasks (where user is the reviewer)
    await fetchReviewerTasks(targetUserId)
    
    // Debug: Log the final counts
    console.log('=== FINAL COUNTS ===')
    console.log('My Tasks Count:', myTasks.value.length)
    console.log('Reviewer Tasks Count:', reviewerTasks.value.length)
    console.log('My Tasks:', myTasks.value.map(t => ({ name: t.FrameworkName || t.PolicyName, userId: t.UserId, reviewerId: t.ReviewerId, approvalId: t.ApprovalId })))
    console.log('Reviewer Tasks:', reviewerTasks.value.map(t => ({ name: t.FrameworkName || t.PolicyName, userId: t.UserId, reviewerId: t.ReviewerId, approvalId: t.ApprovalId })))
    
    // Check if data is the same
    const myTaskIds = myTasks.value.map(t => t.ApprovalId).sort()
    const reviewerTaskIds = reviewerTasks.value.map(t => t.ApprovalId).sort()
    const sameData = JSON.stringify(myTaskIds) === JSON.stringify(reviewerTaskIds)
    console.log('Same data for both tabs:', sameData)
    console.log('==================')
  } catch (error) {
    console.error('Error loading user tasks:', error)
    myTasks.value = []
    reviewerTasks.value = []
  } finally {
    // Clear loading states
    isLoadingMyTasks.value = false
    isLoadingReviewerTasks.value = false
  }
}

// Fetch My Tasks (created by user)
const fetchMyTasks = async (userId) => {
  try {
    console.log(`Fetching my tasks for user ID: ${userId}`)
    
    // Fetch framework status change requests where user is the creator
    const frameworkResponse = await axios.get(API_ENDPOINTS.FRAMEWORK_STATUS_CHANGE_REQUESTS_USER(userId))
    console.log('Framework response:', frameworkResponse.data)
    
    // Fetch policy status change requests where user is the creator
    const policyResponse = await axios.get(API_ENDPOINTS.POLICY_STATUS_CHANGE_REQUESTS_USER(userId))
    console.log('Policy response:', policyResponse.data)
    
    let frameworkRequests = []
    let policyRequests = []
    
    // Process framework requests
    if (frameworkResponse.data && Array.isArray(frameworkResponse.data)) {
      frameworkRequests = processFrameworks(frameworkResponse.data)
      console.log('Processed framework requests:', frameworkRequests.length)
    }
    
    // Process policy requests
    if (policyResponse.data && Array.isArray(policyResponse.data)) {
      policyRequests = processPolicies(policyResponse.data.map(request => ({
        ...request,
        RequestType: 'Policy Status Change',
        ItemType: 'policy'
      })))
      console.log('Processed policy requests:', policyRequests.length)
    }
    
    // Combine and sort by request date (newest first)
    let allRequests = [...frameworkRequests, ...policyRequests]
    allRequests.forEach(request => {
      if (!request.ItemType) {
        request.ItemType = 'framework'
      }
    })

    // Filter by selected framework if one is selected
    if (selectedFrameworkId.value) {
      console.log('🔍 DEBUG: Filtering my tasks by selected framework ID:', selectedFrameworkId.value);
      allRequests = allRequests.filter(request => {
        // For framework requests, check FrameworkId
        if (request.ItemType === 'framework' && request.FrameworkId) {
          return request.FrameworkId.toString() === selectedFrameworkId.value.toString()
        }
        // For policy requests, check if they belong to the selected framework
        if (request.ItemType === 'policy' && request.FrameworkId) {
          return request.FrameworkId.toString() === selectedFrameworkId.value.toString()
        }
        return false
      });
      console.log('✅ DEBUG: Filtered my tasks count:', allRequests.length);
    }
    
    myTasks.value = allRequests.sort((a, b) => {
      const dateA = new Date(a.RequestDate || 0)
      const dateB = new Date(b.RequestDate || 0)
      return dateB - dateA
    })
    
    console.log('Final my tasks count:', myTasks.value.length)
    console.log('My tasks data:', myTasks.value.map(t => ({
      name: t.FrameworkName || t.PolicyName,
      userId: t.UserId,
      reviewerId: t.ReviewerId,
      approvalId: t.ApprovalId
    })))
    
  } catch (error) {
    console.error('Error fetching my tasks:', error)
    myTasks.value = []
  }
}

// Fetch Reviewer Tasks (where user is reviewer)
const fetchReviewerTasks = async (userId) => {
  try {
    console.log(`Fetching reviewer tasks for user ID: ${userId}`)
    
    // Fetch framework status change requests where user is the reviewer
    const frameworkResponse = await axios.get(API_ENDPOINTS.FRAMEWORK_STATUS_CHANGE_REQUESTS_REVIEWER(userId))
    console.log('Framework reviewer response:', frameworkResponse.data)
    
    // Fetch policy status change requests where user is the reviewer
    const policyResponse = await axios.get(API_ENDPOINTS.POLICY_STATUS_CHANGE_REQUESTS_REVIEWER(userId))
    console.log('Policy reviewer response:', policyResponse.data)
    
    let frameworkRequests = []
    let policyRequests = []
    
    // Process framework requests
    if (frameworkResponse.data && Array.isArray(frameworkResponse.data)) {
      frameworkRequests = processFrameworks(frameworkResponse.data)
      console.log('Processed framework reviewer requests:', frameworkRequests.length)
    }
    
    // Process policy requests
    if (policyResponse.data && Array.isArray(policyResponse.data)) {
      policyRequests = processPolicies(policyResponse.data.map(request => ({
        ...request,
        RequestType: 'Policy Status Change',
        ItemType: 'policy'
      })))
      console.log('Processed policy reviewer requests:', policyRequests.length)
    }
    
    // Combine and sort by request date (newest first)
    let allRequests = [...frameworkRequests, ...policyRequests]
    allRequests.forEach(request => {
      if (!request.ItemType) {
        request.ItemType = 'framework'
      }
    })

    // Filter by selected framework if one is selected
    if (selectedFrameworkId.value) {
      console.log('🔍 DEBUG: Filtering reviewer tasks by selected framework ID:', selectedFrameworkId.value);
      allRequests = allRequests.filter(request => {
        // For framework requests, check FrameworkId
        if (request.ItemType === 'framework' && request.FrameworkId) {
          return request.FrameworkId.toString() === selectedFrameworkId.value.toString()
        }
        // For policy requests, check if they belong to the selected framework
        if (request.ItemType === 'policy' && request.FrameworkId) {
          return request.FrameworkId.toString() === selectedFrameworkId.value.toString()
        }
        return false
      });
      console.log('✅ DEBUG: Filtered reviewer tasks count:', allRequests.length);
    }
    
    reviewerTasks.value = allRequests.sort((a, b) => {
      const dateA = new Date(a.RequestDate || 0)
      const dateB = new Date(b.RequestDate || 0)
      return dateB - dateA
    })
    
    console.log('Final reviewer tasks count:', reviewerTasks.value.length)
    console.log('Reviewer tasks data:', reviewerTasks.value.map(t => ({
      name: t.FrameworkName || t.PolicyName,
      userId: t.UserId,
      reviewerId: t.ReviewerId,
      approvalId: t.ApprovalId
    })))
    
  } catch (error) {
    console.error('Error fetching reviewer tasks:', error)
    reviewerTasks.value = []
  }
}



// Computed property for pending requests
const pendingRequests = computed(() => {
  return requests.value.filter(req => req.Status === 'Pending Approval')
})

// Tab-specific counts
const myTasksCount = computed(() => {
  const count = myTasks.value ? myTasks.value.length : 0
  console.log('Computed myTasksCount:', count, 'for user:', selectedUserId.value || currentUserId.value)
  return count
})

const reviewerTasksCount = computed(() => {
  const count = reviewerTasks.value ? reviewerTasks.value.length : 0
  console.log('Computed reviewerTasksCount:', count, 'for user:', selectedUserId.value || currentUserId.value)
  return count
})

// My Tasks pending requests
const myTasksPendingRequests = computed(() => {
  return myTasks.value.filter(req => req.Status === 'Pending Approval')
})

// Reviewer Tasks pending requests
const reviewerTasksPendingRequests = computed(() => {
  return reviewerTasks.value.filter(req => req.Status === 'Pending Approval')
})

// Table headers for pending requests
const pendingTableHeaders = [
  { key: 'name', label: 'Name' },
  { key: 'type', label: 'Type' },
  { key: 'category', label: 'Category/Department' },
  { key: 'date', label: 'Request Date' },
  { key: 'reason', label: 'Reason' },
  { key: 'actions', label: 'Actions' }
]

// Table rows for pending requests
const pendingTableRows = computed(() =>
  pendingRequests.value.map(req => ({
    ...req,
    name: req.FrameworkName || req.PolicyName,
    type: req.ItemType === 'policy' ? 'POLICY STATUS CHANGE' : 'FRAMEWORK STATUS CHANGE',
    category: req.Category || req.Department,
    date: formatDate(req.RequestDate),
    reason: req.Reason
  }))
)

// Table rows for my tasks pending requests
const myTasksPendingTableRows = computed(() =>
  myTasksPendingRequests.value.map(req => ({
    ...req,
    name: req.FrameworkName || req.PolicyName,
    type: req.ItemType === 'policy' ? 'POLICY STATUS CHANGE' : 'FRAMEWORK STATUS CHANGE',
    category: req.Category || req.Department,
    date: formatDate(req.RequestDate),
    reason: req.Reason
  }))
)

// Table rows for reviewer tasks pending requests
const reviewerTasksPendingTableRows = computed(() =>
  reviewerTasksPendingRequests.value.map(req => ({
    ...req,
    name: req.FrameworkName || req.PolicyName,
    type: req.ItemType === 'policy' ? 'POLICY STATUS CHANGE' : 'FRAMEWORK STATUS CHANGE',
    category: req.Category || req.Department,
    date: formatDate(req.RequestDate),
    reason: req.Reason
  }))
)

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

// Process frameworks and ensure consistent status
const processFrameworks = (frameworks) => {
  // Create a map of framework status by framework name to ensure consistency
  const frameworkStatusMap = {}
  
  // First pass: determine the status of each framework
  frameworks.forEach(framework => {
    if (framework.ApprovedNot === true) {
      frameworkStatusMap[framework.FrameworkName] = 'Approved' // Will display as Inactive
      framework.Status = 'Approved'
    } else if (framework.ApprovedNot === false) {
      frameworkStatusMap[framework.FrameworkName] = 'Rejected' // Will display as Active
      framework.Status = 'Rejected'
    } else {
      frameworkStatusMap[framework.FrameworkName] = 'Pending Approval'
      framework.Status = 'Pending Approval'
    }
  })
  
  // Second pass: ensure all instances of the same framework have the same status
  frameworks.forEach(framework => {
    // Set the status based on the map to ensure consistency
    framework.Status = frameworkStatusMap[framework.FrameworkName]
    
    // Update affected policies status to match framework status
    if (framework.AffectedPolicies) {
      framework.AffectedPolicies.forEach(policy => {
        if (framework.Status === 'Approved') {
          policy.ActiveInactive = 'Inactive'
        } else if (framework.Status === 'Rejected') {
          policy.ActiveInactive = 'Active'
        }
      })
    }
  })
  
  return frameworks
}

// Process policies and ensure consistent status
const processPolicies = (policies) => {
  // Create a map of policy status by policy name to ensure consistency
  const policyStatusMap = {}
  
  // First pass: determine the status of each policy
  policies.forEach(policy => {
    if (policy.ApprovedNot === true) {
      policyStatusMap[policy.PolicyName] = 'Approved' // Will display as Inactive
      policy.Status = 'Approved'
    } else if (policy.ApprovedNot === false) {
      policyStatusMap[policy.PolicyName] = 'Rejected' // Will display as Active
      policy.Status = 'Rejected'
    } else {
      policyStatusMap[policy.PolicyName] = 'Pending Approval'
      policy.Status = 'Pending Approval'
    }
  })
  
  // Second pass: ensure all instances of the same policy have the same status
  policies.forEach(policy => {
    // Set the status based on the map to ensure consistency
    policy.Status = policyStatusMap[policy.PolicyName]
    
    // Update affected subpolicies status to match policy status
    if (policy.AffectedSubpolicies) {
      policy.AffectedSubpolicies.forEach(subpolicy => {
        if (policy.Status === 'Approved') {
          subpolicy.ActiveInactive = 'Inactive'
        } else if (policy.Status === 'Rejected') {
          subpolicy.ActiveInactive = 'Active'
        }
      })
    }
  })
  
  return policies
}

// Fetch status change requests
const fetchRequests = async () => {
  isLoading.value = true
  try {
    const [frameworkResponse, policyResponse] = await Promise.all([
      axios.get(API_ENDPOINTS.FRAMEWORK_STATUS_CHANGE_REQUESTS),
      axios.get(API_ENDPOINTS.POLICY_STATUS_CHANGE_REQUESTS)
    ])
    
    // Process all frameworks to ensure consistent status
    const frameworkRequests = processFrameworks(frameworkResponse.data)
    
    // Process policy requests and add type indicator
    const policyRequests = processPolicies(policyResponse.data.map(request => ({
      ...request,
      RequestType: 'Policy Status Change',
      ItemType: 'policy'
    })))
    
    // Combine and sort by request date (newest first)
    const allRequests = [...frameworkRequests, ...policyRequests]
    allRequests.forEach(request => {
      if (!request.ItemType) {
        request.ItemType = 'framework'
      }
    })
    
    requests.value = allRequests.sort((a, b) => {
      const dateA = new Date(a.RequestDate || 0)
      const dateB = new Date(b.RequestDate || 0)
      return dateB - dateA
    })
    
  } catch (error) {
    console.error('Error fetching status change requests:', error)
  } finally {
    isLoading.value = false
  }
}

// Navigate to request details page
const openRequestDetails = (request) => {
  console.log('=== OPENING STATUS CHANGE REQUEST DETAILS ===');
  console.log('Request data:', request);
  
  // Store the request data in sessionStorage for the StatusChangeDetails page
  sessionStorage.setItem('statusChangeRequestData', JSON.stringify(request));
  
  // Navigate to StatusChangeDetails page
  router.push({
    name: 'StatusChangeDetails',
    params: { requestId: request.ApprovalId }
  });
}

// Close request details modal
const closeRequestDetails = () => {
  selectedRequest.value = null
  showDetails.value = false
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
            
            // Update the request status in the tasks arrays
            const updateRequestInArray = (array) => {
              const index = array.findIndex(r => r.ApprovalId === request.ApprovalId)
              if (index !== -1) {
                array[index].Status = 'Approved'
                array[index].ApprovedNot = true
                array[index].Remarks = remarks || 'Status change approved'
                array[index].ApprovedDate = new Date().toISOString()
              }
            }
            
            updateRequestInArray(myTasks.value)
            updateRequestInArray(reviewerTasks.value)
            
            PopupService.success(
              `${itemType.charAt(0).toUpperCase() + itemType.slice(1)} "${itemName}" has been set to Inactive.${affectedCount > 0 ? ` ${affectedCount} ${affectedType} were also made inactive.` : ''}`,
              'Status Changed'
            )
            
            // Close modal and refresh the list
            closeRequestDetails()
            await loadUserTasks()
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
            
            // Update the request status in the tasks arrays
            const updateRequestInArray = (array) => {
              const index = array.findIndex(r => r.ApprovalId === request.ApprovalId)
              if (index !== -1) {
                array[index].Status = 'Rejected'
                array[index].ApprovedNot = false
                array[index].Remarks = remarks || 'Status change rejected'
                array[index].ApprovedDate = new Date().toISOString()
              }
            }
            
            updateRequestInArray(myTasks.value)
            updateRequestInArray(reviewerTasks.value)
            
            PopupService.success(
              `Status change request for "${itemName}" has been rejected. The ${itemType} remains Active.`,
              'Request Rejected'
            )
            
            // Close modal and refresh the list
            closeRequestDetails()
            await loadUserTasks()
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

// Fetch requests on component mount
onMounted(async () => {
  // Initialize current user ID
  currentUserId.value = getCurrentUserId()
  console.log('Current user ID:', currentUserId.value)
  
  // Initialize administrator status and available users
  await initializeUserData()
  
  // Fetch frameworks and check session
  await fetchFrameworks()
  
  // Load user tasks for the current tab
  await loadUserTasks()
  
  // Fetch all requests for legacy compatibility
  fetchRequests()
  fetchReviewers()
  
  console.log('Component mounted - initial state:')
  console.log('Active tab:', activeTab.value)
  console.log('Is administrator:', isAdministrator.value)
  console.log('Selected user ID:', selectedUserId.value)
  console.log('Selected framework ID:', selectedFrameworkId.value)
  console.log('My tasks count:', myTasks.value.length)
  console.log('Reviewer tasks count:', reviewerTasks.value.length)
})

// Initialize user data and administrator status
const initializeUserData = async () => {
  try {
    console.log('Initializing user data...')
    console.log('Current user ID:', currentUserId.value)
    
    // Fetch user role from backend to determine administrator status
    const roleResponse = await axios.get(API_ENDPOINTS.USER_ROLE)
    console.log('User role response:', roleResponse.data)
    
    if (roleResponse.data.success) {
      const userRole = roleResponse.data.role
      const currentUserName = roleResponse.data.username || roleResponse.data.user_name || ''
      console.log('User role:', userRole)
      console.log('Current user name:', currentUserName)
      
      // Check if user is GRC Administrator
      isAdministrator.value = userRole === 'GRC Administrator'
      console.log('Is GRC Administrator:', isAdministrator.value)
      
      if (isAdministrator.value) {
        // Fetch available users for administrator dropdown
        const response = await axios.get(API_ENDPOINTS.USERS_FOR_REVIEWER_SELECTION)
        availableUsers.value = response.data
        console.log('Available users:', availableUsers.value)
        
        // Set default user to current logged-in administrator
        selectedUserId.value = currentUserId.value
        selectedUserInfo.value = {
          UserId: currentUserId.value,
          UserName: currentUserName,
          Role: userRole
        }
        console.log('Setting default user for administrator to current user:', currentUserName)
      } else {
        // Set selected user to current user for non-administrators
        selectedUserId.value = currentUserId.value
        selectedUserInfo.value = {
          UserId: currentUserId.value,
          UserName: currentUserName,
          Role: userRole
        }
        console.log('Regular user mode - selected user ID:', selectedUserId.value)
      }
    } else {
      console.error('Failed to fetch user role:', roleResponse.data.error)
      isAdministrator.value = false
      // Set selected user to current user as fallback
      selectedUserId.value = currentUserId.value
    }
  } catch (error) {
    console.error('Error initializing user data:', error)
    isAdministrator.value = false
    // Set selected user to current user as fallback
    selectedUserId.value = currentUserId.value
  }
}


// Fetch reviewers for dropdown
const fetchReviewers = async () => {
  try {
    const response = await axios.get(API_ENDPOINTS.USERS_FOR_REVIEWER_SELECTION)
    reviewers.value = response.data
  } catch (error) {
    console.error('Error fetching reviewers:', error)
  }
}


</script>

<style scoped>
/* Force white background for the entire page */
:deep(body), :deep(html) {
  background-color: white !important;
}

/* Force dashboard container positioning */
.statuschange-container {
  padding: 0px -10px -10px -10px !important; /* Minimal top padding */
  background-color: white !important;
  background: white !important;
  margin-left: 280px !important; /* Further reduced margin to move content back more towards sidebar */
  width: calc(100% - 250px) !important; /* Adjust width to account for sidebar */
  transition: margin-left 0.3s ease, width 0.3s ease;
  min-height: 100vh;
  padding-right: 40px;
  margin-top: 45px !important; /* Pull content further up */
}

.statuschange-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;
  padding-bottom: 10px;
}

.statuschange-heading {
  font-size: 30px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  letter-spacing: 0;
}

.statuschange-heading::after {
  content: '';
  display: block;
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  margin-top: 8px;
  border-radius: 2px;
}

.statuschange-actions {
  display: flex;
  align-items: flex-end;
  gap: 2rem;
  flex-wrap: wrap;
}

/* Framework Filter Section Styles - Matching FrameworkApprover */
.framework_filter_section {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  margin-top: -10px;
}

.framework_filter_block {
  flex: 1;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 12px;
}

.framework_filter_label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.framework_filter_label i {
  font-size: 14px;
  color: #6c757d;
}

.framework_filter_dropdown {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  background: white;
  font-size: 14px;
  color: #212529;
  outline: none;
  transition: border-color 0.2s ease;
  height: 38px;
}

.framework_filter_dropdown:focus {
  border-color: #6366f1;
  outline: none;
}

.clear-filter-btn:hover {
  background: #e9ecef !important;
  border-color: #adb5bd !important;
}


@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-help-text {
  color: #666;
  font-size: 12px;
  display: block;
  margin-top: 8px;
  color: #64748b;
  font-size: 12px;
  font-style: italic;
  padding: 6px 12px;
  background: #ffffff;
  border-radius: 6px;
  border-left: 3px solid #6366f1;
}

.form-control {
  width: 300px;
  min-width: 250px;
  max-width: 350px;
  background: #ffffff;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
  transition: all 0.3s ease;
}

.form-control:hover {
  border-color: #6366f1;
  box-shadow: 0 8px 15px rgba(99, 102, 241, 0.1), 0 3px 6px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.form-control:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15), 0 8px 15px rgba(99, 102, 241, 0.1);
  transform: translateY(-1px);
  background: #ffffff;
}

.statuschange-actions label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #1e293b;
  font-size: 14px;
}


.action-btn {
  background-color: #f5f6fa;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #4f6cff;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background-color: #e8edfa;
  transform: translateY(-2px);
}

.performance-summary {
  display: flex;
  gap: 24px;
  margin-bottom: 32px;
}

.summary-card {
  background: #f5f6fa;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 220px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.summary-card.growth {
  background: linear-gradient(135deg, #e3f0ff 0%, #f5f6fa 100%);
}

.summary-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  background: #4f6cff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.summary-label {
  color: #666;
  font-size: 0.95rem;
}

.summary-value {
  font-size: 1.6rem;
  font-weight: 700;
  color: #2c3e50;
}

.loading-indicator, .no-requests {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  color: #666;
  font-size: 1.1rem;
}

.loading-indicator i {
  margin-right: 10px;
  color: #4f6cff;
}

/* Status Tasks Section */
.section-container {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 32px;
}

.section-title {
  margin-top: 0;
  margin-bottom: 16px;
  color: #2c3e50;
  font-size: 1.2rem;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 12px;
}

.status-tasks {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-task-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.2s ease;
}

.status-task-item:last-child {
  border-bottom: none;
}

.status-task-item:hover {
  background: #f9faff;
}

.task-name {
  flex: 1;
  color: #4f6cff;
  font-weight: 500;
}

.task-type {
  padding: 4px 10px;
  border-radius: 12px;
  background-color: #ffebee;
  color: #e53935;
  font-size: 0.85rem;
  font-weight: 600;
  margin: 0 16px;
}

.task-date {
  color: #666;
  font-size: 0.9rem;
  margin: 0 16px;
}

.task-category {
  font-size: 0.9rem;
  color: #444;
  background: #f5f6fa;
  padding: 4px 10px;
  border-radius: 4px;
  margin-right: 16px;
}

.task-status {
  font-size: 0.85rem;
  font-weight: 600;
}

.task-status.pending {
  color: #f5a623;
}

.task-status.approved {
  color: #22a722;
}

.task-status.rejected {
  color: #e53935;
}

/* Framework Grid */
.framework-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.framework-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  padding: 20px;
  display: flex;
  flex-direction: column;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.framework-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.framework-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.framework-header i {
  color: #4f6cff;
  font-size: 1.2rem;
}

.framework-header span {
  font-weight: 600;
  color: #2c3e50;
  font-size: 1.1rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-tag {
  position: absolute;
  top: 20px;
  right: 20px;
  font-size: 0.8rem;
  background: #f0f0f0;
  padding: 4px 8px;
  border-radius: 4px;
  color: #666;
}

.framework-description {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 16px;
  flex-grow: 1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.framework-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}

.status-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-toggle input[type="checkbox"] {
  appearance: none;
  width: 40px;
  height: 22px;
  background-color: #e0e0e0;
  border-radius: 11px;
  position: relative;
  cursor: pointer;
  transition: background-color 0.3s;
}

.status-toggle input[type="checkbox"]:checked {
  background-color: #4f6cff;
}

.status-toggle input[type="checkbox"]::before {
  content: "";
  position: absolute;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background-color: white;
  top: 2px;
  left: 2px;
  transition: transform 0.3s;
}

.status-toggle input[type="checkbox"]:checked::before {
  transform: translateX(18px);
}

.switch-label {
  font-size: 0.9rem;
  font-weight: 600;
}

.switch-label.active {
  color: #22a722;
}

.switch-label.inactive {
  color: #e53935;
}

.switch-label.pending {
  color: #f5a623;
}

.status-active {
  color: #22a722;
}

.status-inactive {
  color: #e53935;
}

.actions {
  display: flex;
  gap: 8px;
}

.view-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #f5f6fa;
  border: none;
  color: #4f6cff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.view-btn:hover {
  background-color: #4f6cff;
  color: white;
}

/* Modal Styles */
.framework-details-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.framework-details-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 900px;
  max-height: 85vh;
  overflow-y: auto;
  padding: 32px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  position: relative;
}

.framework-details-content h3 {
  color: #2c3e50;
  margin-top: 0;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-type-indicator {
  font-size: 0.9rem;
  padding: 4px 10px;
  border-radius: 8px;
  background: #ffebee;
  color: #e53935;
  font-weight: 600;
}

.version-pill {
  font-size: 0.85rem;
  padding: 2px 8px;
  border-radius: 10px;
  background: #f0f0f0;
  color: #666;
  margin-left: auto;
}

.close-x {
  position: absolute !important;
  top:1px !important;
  right: 10px !important;
  left: auto !important;
  font-size: 2rem !important;
  color: #222 !important;
  font-weight: bold !important;
  cursor: pointer !important;
  z-index: 1002 !important;
  background: none !important;
  border: none !important;
  line-height: 1 !important;
  transition: color 0.2s !important;
  display: block !important;
}
.close-x:hover {
  color: #000 !important;
}

.framework-approval-section {
  background: #f9faff;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 24px;
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
  background: #f5f5f5;
  padding: 12px;
  border-radius: 8px;
  margin-top: 16px;
}

.approval-remarks, .approval-date {
  margin-bottom: 8px;
}

.approval-remarks strong, .approval-date strong {
  color: #444;
}

.request-details {
  margin-bottom: 24px;
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
  width: 180px;
  color: #444;
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

.approval-implications {
  background: #f9faff;
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

.affected-policies-section {
  background: #f9faff;
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

/* Tab Styles */
.tabs-container {
  margin-bottom: 24px;
  background: none;
  border: none;
  box-shadow: none;
  padding: 0;
}

.tabs {
  display: flex;
  gap: -2px;
  border-bottom: 1px solid #e0e0e0;
  background: none;
  border: none;
  box-shadow: none;
  padding: 0;
}

.tab-button {
  background: #f8f9fa;
  border: none;
  padding: 12px 24px;
  font-size: 1rem;
  font-weight: 600;
  color: #333 !important;
  cursor: pointer;
  border-radius: 8px 8px 0 0;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  position: relative;
  text-decoration: none;
  outline: none;
}

.tab-button:hover {
  background-color: #f5f6fa;
  color: #4f6cff;
  border: none;
}

.tab-button.active {
  background-color: #4f6cff;
  color: white;
  border: none;
  border-bottom: 3px solid #4f6cff;
}

.tab-button,
.tab-button:hover,
.tab-button:focus,
.tab-button:active {
  border: none !important;
  box-shadow: none !important;
}

.tab-button.active,
.tab-button.active:hover,
.tab-button.active:focus {
  border: none !important;
  border-bottom: 3px solid #4f6cff !important;
  box-shadow: none !important;
}


.tab-count {
  background: none !important;
  background-color: transparent !important;
  color: #495057;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 600;
  min-width: 20px;
  text-align: center;
}


.tab-content {
  margin-top: 24px;
  background: none;
  border: none;
  box-shadow: none;
  padding: 0;
}

.approvals-list {
  border-bottom: none !important;
}

.approvals-list h3 {
  margin-top: 0;
  margin-bottom: 24px;
  color: #2c3e50;
  font-size: 1.3rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: none !important;
  border: none !important;
  text-decoration: none !important;
  position: relative;
}

.approvals-list h3::before,
.approvals-list h3::after {
  display: none !important;
  content: none !important;
}



.no-tasks-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: #666;
}

.no-tasks-icon {
  font-size: 3rem;
  color: #ddd;
  margin-bottom: 16px;
}

.no-tasks-message h4 {
  margin: 0 0 8px 0;
  color: #444;
  font-size: 1.2rem;
}

.no-tasks-message p {
  margin: 0;
  color: #666;
  font-size: 1rem;
}

/* Filter Section Styles */
.filter-section {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 1;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

/* Custom width for the dropdown filter */
.filter-group :deep(.filter-btn) {
  min-width: 250px !important;
  max-width: 300px !important;
}

.filter-group :deep(.dropdown-menu) {
  min-width: 250px !important;
  max-width: 300px !important;
  z-index: 10000 !important;
  position: absolute !important;
}

/* Remove the old filter styles since CustomDropdown handles its own styling */
.filter-group label {
  display: none; /* Hide the old label since CustomDropdown has its own */
}

.filter-dropdown {
  display: none; /* Hide the old dropdown since we're using CustomDropdown */
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

/* Responsive adjustments for sidebar */
@media (max-width: 1024px) {
  .statuschange-container {
    margin-left: 0; /* Remove sidebar margin on tablet */
    width: 100%; /* Full width on tablet */
  }
}

@media (max-width: 768px) {
  .statuschange-container {
    margin-left: 0; /* Remove sidebar margin on mobile */
    width: 100%; /* Full width on mobile */
    padding: 10px; /* Reduce padding on mobile */
  }
  
  .statuschange-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .statuschange-actions {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
    width: 100%;
  }
  
  .statuschange-actions .form-control {
    width: 100%;
    min-width: 100%;
    max-width: 100%;
  }
  
  .framework_filter_section {
    flex-direction: column;
  }
  
  .framework_filter_block {
    width: 100%;
  }
  
  .tab-navigation {
    flex-direction: column;
    gap: 0;
  }
  
  .tab-button {
    width: 100%;
    justify-content: center;
    border-radius: 0;
  }
  
  .tab-button:first-child {
    border-radius: 8px 8px 0 0;
  }
  
  .tab-button:last-child {
    border-radius: 0 0 8px 8px;
  }
}
</style> 