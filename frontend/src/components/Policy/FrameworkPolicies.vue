<template>
  <div class="framework-policies-container">
    <div class="export-controls">
      <div class="export-controls-inner">
        <select v-model="selectedExportFormat" class="export-dropdown">
          <option value="" disabled>Select format</option>
          <option value="xlsx">Excel (.xlsx)</option>
          <option value="pdf">PDF (.pdf)</option>
          <option value="csv">CSV (.csv)</option>
          <option value="json">JSON (.json)</option>
          <option value="xml">XML (.xml)</option>
          <option value="txt">Text (.txt)</option>
        </select>
        <button @click="exportPolicies">
          <i class="fas fa-download"></i>
          Export
        </button>
      </div>
    </div>

    <div class="breadcrumb-tab">
      <span class="breadcrumb-chip">
        {{ frameworkName }}
        <span class="breadcrumb-close" @click="goBack">×</span>
      </span>
    </div>

    <h1>Policies for {{ frameworkName }}</h1>
    <div class="page-header-underline"></div>

    <!-- Policy Summary Cards -->
    <div class="summary-section">
      <div class="summary-cards">
        <!-- Policy Cards -->
        <div class="summary-card" :class="{ 'active-policy': activePolicyTab === 'Active' }" @click="filterByStatus('Active', 'policy')">
          <div class="summary-card-content">
            <div class="summary-label">ACTIVE POLICIES</div>
            <div class="summary-value">{{ policyCounts.active }}</div>
          </div>
        </div>
        <div class="summary-card" :class="{ 'active-policy': activePolicyTab === 'Inactive' }" @click="filterByStatus('Inactive', 'policy')">
          <div class="summary-card-content">
            <div class="summary-label">INACTIVE POLICIES</div>
            <div class="summary-value">{{ policyCounts.inactive }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="top-controls">
      <div class="entity-dropdown-section">
        <CustomDropdown
          :config="entityDropdownConfig"
          v-model="selectedEntity"
          :show-search-bar="true"
        />
      </div>

      <!-- View Toggle Controls -->
      <div class="view-toggle-controls">
        <button 
          class="view-toggle-btn" 
          :class="{ active: currentView === 'list' }"
          @click="currentView = 'list'"
          title="List View"
        >
          <i class="fas fa-list"></i>
        </button>
        <button 
          class="view-toggle-btn" 
          :class="{ active: currentView === 'card' }"
          @click="currentView = 'card'"
          title="Card View"
        >
          <i class="fas fa-th-large"></i>
        </button>
      </div>
    </div>

    <!-- Card View (Default/Existing) -->
    <div v-if="currentView === 'card'" class="policy-card-grid">
      <div v-for="policy in policies" :key="policy.id" class="policy-card">
        <div class="policy-card-header">
          <div class="policy-title-section">
            <span class="policy-icon">
              <i class="fas fa-file-alt"></i>
            </span>
            <span class="policy-card-title">{{ policy.name }}</span>
          </div>
        </div>
        <div class="policy-card-meta">
          <span class="policy-card-category">Category: {{ policy.category }}</span>
          <span class="policy-card-type" :class="policy.type === 'External' ? 'external' : ''">
            Type: {{ policy.type || 'External' }}
          </span>
        </div>
        <div class="policy-card-desc">{{ policy.description }}</div>
        <div class="policy-card-actions">
          <div class="action-buttons">
            <label class="switch" @click.stop>
              <input type="checkbox" :checked="policy.status === 'Active'" @change="toggleStatus(policy)" />
              <span class="slider"></span>
            </label>
            <button v-if="policy.status === 'Active'"
                    @click="acknowledgePolicy(policy)"
                    class="acknowledge-btn"
                    title="Create acknowledgement request for this policy">
              Request Ack
            </button>
            <button v-if="policy.status === 'Active'"
                    @click="viewPolicyAcknowledgements(policy)"
                    class="view-reports-btn"
                    title="View acknowledgement reports for this policy">
              View Reports
            </button>
            <span class="document-icon" @click="showPolicyDetails(policy.id)">
              <i class="fas fa-file-lines"></i>
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- List View -->
    <div v-if="currentView === 'list'" class="policy-list-container">
      <div class="policy-list-header">
        <div class="list-header-item">Policy</div>
        <div class="list-header-item">Category</div>
        <div class="list-header-item">Type</div>
        <div class="list-header-item">Description</div>
        <div class="list-header-item">Status</div>
        <div class="list-header-item">Actions</div>
      </div>
      
      <div class="policy-list">
        <div v-for="policy in policies" :key="policy.id" class="policy-list-item">
          <div class="list-item-content">
            <div class="policy-name-cell">
              <div class="policy-name-text">
                <div class="policy-title">{{ policy.name }}</div>
                <div class="policy-id">ID: {{ policy.id }}</div>
              </div>
            </div>
            
            <div class="policy-category-cell">
              <span class="category-text">{{ policy.category }}</span>
            </div>
            
            <div class="policy-type-cell">
              <span class="type-text">{{ policy.type || 'External' }}</span>
            </div>
            
            <div class="policy-description-cell">
              <p class="description-text">{{ policy.description }}</p>
            </div>
            
            <div class="policy-status-cell">
              <div class="status-controls">
                <label class="switch" @click.stop>
                  <input type="checkbox" :checked="policy.status === 'Active'" @change="toggleStatus(policy)" />
                  <span class="slider"></span>
                </label>
                <span class="switch-label" :class="policy.status === 'Active' ? 'active' : 'inactive'">{{ policy.status }}</span>
              </div>
            </div>
            
            <div class="policy-actions-cell">
              <div class="list-action-buttons">
                <button v-if="policy.status === 'Active'"
                        @click="acknowledgePolicy(policy)"
                        class="acknowledge-btn-list"
                        title="Create acknowledgement request for this policy">
                  Request Ack
                </button>
                <button v-if="policy.status === 'Active'"
                        @click="viewPolicyAcknowledgements(policy)"
                        class="view-reports-btn-list"
                        title="View acknowledgement reports for this policy">
                  View Reports
                </button>
                <button class="action-btn details-btn" @click="showPolicyDetails(policy.id)">
                  <span>Details</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
 
    <!-- Popup Modal -->
    <PopupModal />
    
    <!-- Acknowledgement Request Modal -->
    <CreateAcknowledgementModal
      v-if="showAcknowledgementModal && selectedPolicyForAck"
      :isVisible="showAcknowledgementModal"
      :policy="selectedPolicyForAck"
      @close="closeAcknowledgementModal"
      @created="handleAcknowledgementCreated"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { PopupService } from '@/modules/popus/popupService'
import PopupModal from '@/modules/popus/PopupModal.vue'
import CustomDropdown from '@/components/CustomDropdown.vue'
import CreateAcknowledgementModal from './CreateAcknowledgementModal.vue'
import {  API_ENDPOINTS } from '../../config/api.js'

// Add view state
const currentView = ref('list') // 'list' or 'card' - default to list view

// Add active policy tab state
const activePolicyTab = ref('Active') // 'Active' or 'Inactive'
 
const router = useRouter()
const route = useRoute()
const frameworkId = route.params.frameworkId
const frameworkName = ref('')
const frameworkStatus = ref('')
const policies = ref([])
const allPolicies = ref([]) // Store all policies for filtering
const selectedEntity = ref('')
const entities = ref([])
const isLoading = ref(false)

// Acknowledgement modal state
const showAcknowledgementModal = ref(false)
const selectedPolicyForAck = ref(null)

// Add policy counts state
const policyCounts = ref({
  active: 0,
  inactive: 0
})

// Add status filter state
const statusFilter = ref(null)
const typeFilter = ref(null)

// Add export format state
const selectedExportFormat = ref('')

// Push notification method
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

// Export policies function
const exportPolicies = async () => {
  if (!selectedExportFormat.value) {
    PopupService.warning('Please select a format.', 'Missing Selection');
    return;
  }
  try {
    const res = await axios.post(`/api/frameworks/${frameworkId}/policies/export/`, {
      format: selectedExportFormat.value
    });
    const { file_url, file_name } = res.data;
    if (!file_url || !file_name) {
      PopupService.error('Export failed: No file URL or name returned.', 'Export Error');
      sendPushNotification({
        title: 'Policy Export Failed',
        message: 'Export failed: No file URL or name returned.',
        category: 'policy',
        priority: 'high',
        user_id: 'default_user'
      });
      return;
    }
    // Try to open the file URL in a new tab, fallback to download if it fails
    try {
      const newWindow = window.open(file_url, '_blank');
      if (newWindow) {
        PopupService.success('Export completed successfully! File opened in new tab.', 'Export Success');
        sendPushNotification({
          title: 'Policy Export Completed',
          message: `Policy export completed successfully in ${selectedExportFormat.value.toUpperCase()} format. File opened in new tab.`,
          category: 'policy',
          priority: 'medium',
          user_id: 'default_user'
        });
      } else {
        // Fallback to download if popup is blocked
        const fileRes = await axios.get(file_url, { responseType: 'blob' });
        const url = window.URL.createObjectURL(new Blob([fileRes.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', file_name);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        PopupService.success('Export completed successfully! File downloaded.', 'Export Success');
        sendPushNotification({
          title: 'Policy Export Completed',
          message: `Policy export completed successfully in ${selectedExportFormat.value.toUpperCase()} format. File downloaded.`,
          category: 'policy',
          priority: 'medium',
          user_id: 'default_user'
        });
      }
    } catch (downloadErr) {
      PopupService.success('Export completed successfully!', 'Export Success');
      sendPushNotification({
        title: 'Policy Export Completed',
        message: `Policy export completed successfully in ${selectedExportFormat.value.toUpperCase()} format.`,
        category: 'policy',
        priority: 'medium',
        user_id: 'default_user'
      });
      console.error(downloadErr);
    }
  } catch (err) {
    PopupService.error('Export failed. Please try again.', 'Export Error');
    sendPushNotification({
      title: 'Policy Export Failed',
      message: `Failed to export policies: ${err.response?.data?.error || err.message}`,
      category: 'policy',
      priority: 'high',
      user_id: 'default_user'
    });
    console.error(err);
  }
};
 
// Format date for display
// Check for selected framework from session and set it as default
const checkSelectedFrameworkFromSession = async () => {
  try {
    console.log('🔍 DEBUG: Checking for selected framework from session in FrameworkPolicies...')
    console.log('🔍 DEBUG: Current route frameworkId:', frameworkId)
    const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
    console.log('📊 DEBUG: Selected framework response:', response.data)
    
    if (response.data && response.data.success) {
      // Check if a framework is selected (not null)
      if (response.data.frameworkId) {
        const sessionFrameworkId = response.data.frameworkId
        console.log('✅ DEBUG: Found selected framework in session:', sessionFrameworkId)
        
        // Update the frameworkId from route params to use session framework
        if (sessionFrameworkId.toString() !== frameworkId.toString()) {
          console.log('🔄 DEBUG: Updating frameworkId from session:', sessionFrameworkId)
          console.log('🔄 DEBUG: Current route frameworkId:', frameworkId)
          // Update the route parameter to use the session framework
          await router.replace({ 
            name: 'FrameworkPolicies', 
            params: { frameworkId: sessionFrameworkId },
            query: route.query 
          })
          console.log('✅ DEBUG: Route updated to use session framework')
        } else {
          console.log('✅ DEBUG: Route already using session framework')
        }
      } else {
        // "All Frameworks" is selected (frameworkId is null)
        console.log('ℹ️ DEBUG: No framework selected in session (All Frameworks selected)')
        console.log('🌐 DEBUG: Redirecting to Framework Explorer to show all frameworks')
        // Redirect back to Framework Explorer when "All Frameworks" is selected
        await router.push({ name: 'FrameworkExplorer' })
      }
    } else {
      console.log('ℹ️ DEBUG: No framework found in session, using route frameworkId:', frameworkId)
    }
  } catch (error) {
    console.error('❌ DEBUG: Error checking selected framework from session:', error)
  }
}

// Fetch policies for the selected framework
const fetchPolicies = async () => {
  isLoading.value = true
  try {
    // First check for session framework
    await checkSelectedFrameworkFromSession()
    
    // Use the current frameworkId (which might have been updated from session)
    const currentFrameworkId = route.params.frameworkId
    console.log('🔍 DEBUG: Fetching policies for framework:', currentFrameworkId)
    
    // Guard: Check if frameworkId is valid
    if (!currentFrameworkId || currentFrameworkId === 'undefined') {
      console.error('❌ DEBUG: Invalid frameworkId, cannot fetch policies')
      isLoading.value = false
      return
    }
    
    const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_POLICIES_LIST(currentFrameworkId))
    allPolicies.value = response.data.policies
    frameworkName.value = response.data.framework.name
    frameworkStatus.value = response.data.framework.status || 'Unknown'
    
    // Calculate policy counts from the policies data
    const activeCount = allPolicies.value.filter(policy => policy.status === 'Active').length
    const inactiveCount = allPolicies.value.filter(policy => policy.status === 'Inactive').length
    
    policyCounts.value = {
      active: response.data.policy_counts?.active || activeCount,
      inactive: response.data.policy_counts?.inactive || inactiveCount
    }
  } catch (error) {
    console.error('Error fetching policies:', error)
    sendPushNotification({
      title: 'Policy List Loading Failed',
      message: `Failed to load policies for framework "${frameworkName.value || 'Unknown Framework'}": ${error.response?.data?.error || error.message}`,
      category: 'policy',
      priority: 'high',
      user_id: 'default_user'
    });
  } finally {
    isLoading.value = false
  }
}

// Fetch entities from API
const fetchEntities = async () => {
  try {
    const response = await axios.get(API_ENDPOINTS.ENTITIES)
    entities.value = response.data.entities || []
  } catch (error) {
    console.error('Error fetching entities:', error)
    sendPushNotification({
      title: 'Entity List Loading Failed',
      message: `Failed to load entities for policy filtering: ${error.response?.data?.error || error.message}`,
      category: 'policy',
      priority: 'medium',
      user_id: 'default_user'
    });
  }
}

// Filter policies based on selected entity
const filteredPolicies = computed(() => {
  let result = allPolicies.value
  
  // Apply entity filter
  if (selectedEntity.value) {
    console.log('Filtering policies with entity:', selectedEntity.value)
    console.log('Total policies before filtering:', allPolicies.value.length)
    
    result = result.filter(policy => {
      // If policy has no entities field, don't show it when filtering
      if (!policy.Entities) return false
      
      // If policy applies to all entities, always show it when any entity filter is active
      if (policy.Entities === 'all') {
        return true
      }
      
      // If "All Entities" is selected, show all policies
      if (selectedEntity.value === 'all') {
        return true
      }
      
      // For specific entity selection
      if (Array.isArray(policy.Entities)) {
        // Show policy if it applies to all entities OR includes the selected entity
        // Handle both string and numeric entity IDs
        const selectedEntityInt = parseInt(selectedEntity.value)
        const selectedEntityStr = selectedEntity.value.toString()
        
        return policy.Entities.includes('all') || 
               policy.Entities.includes(selectedEntityInt) || 
               policy.Entities.includes(selectedEntityStr)
      }
      
      return false
    })
  }
  
  // Apply status filter
  if (statusFilter.value && typeFilter.value === 'policy') {
    result = result.filter(policy => policy.status === statusFilter.value)
  }
  
  console.log('Filtered policies count:', result.length)
  console.log('Filtered policies:', result.map(p => ({ name: p.name, entities: p.Entities, status: p.status })))
  
  return result
})

// Filter by status function
const filterByStatus = (status, type) => {
  // Check if we're clicking the same filter that's already active
  if (statusFilter.value === status && typeFilter.value === type) {
    // Clear the filter if it's already active
    clearFilter();
  } else {
    // Apply the new filter
    statusFilter.value = status;
    typeFilter.value = type;
    
    // Update active policy tab for visual indicator
    if (type === 'policy') {
      activePolicyTab.value = status;
    }
  }
}

// Clear all filters
const clearFilter = () => {
  statusFilter.value = null
  typeFilter.value = null
  selectedEntity.value = ''
  activePolicyTab.value = 'Active' // Reset to default
}

// Assign filtered policies to the reactive ref
watch(filteredPolicies, (newPolicies) => {
  policies.value = newPolicies
}, { immediate: true })
 
// Show policy details page
const showPolicyDetails = (policyId) => {
  router.push({
    name: 'PolicyDetails',
    params: {
      policyId
    },
    query: {
      frameworkId: route.params.frameworkId
    }
  })
}
 
// Toggle policy status
const toggleStatus = async (policy) => {
  // Prevent multiple simultaneous calls for the same policy
  if (policy.isProcessing) {
    console.log('Policy is already being processed, skipping duplicate request');
    return;
  }
  
  // Set processing flag
  policy.isProcessing = true;
  
  try {
    // Check if we're deactivating (Active -> Inactive)
    if (policy.status === 'Active') {
      // First: Show reviewer selection popup
      try {
        const response = await axios.get(API_ENDPOINTS.USERS_FOR_REVIEWER_SELECTION);
        const reviewers = response.data;
        
        if (reviewers.length === 0) {
          PopupService.warning('No reviewers available. Please contact administrator.', 'No Reviewers');
          sendPushNotification({
            title: 'No Reviewers Available',
            message: 'No reviewers are available for policy deactivation requests. Please contact administrator.',
            category: 'policy',
            priority: 'high',
            user_id: 'default_user'
          });
          return;
        }
        
        // Step 1: Select reviewer
        const reviewerOptions = reviewers.map(reviewer => ({
          value: reviewer.UserId,
          label: `${reviewer.UserName} (${reviewer.Email})`
        }));
        
        PopupService.select(
          'Select a reviewer for this policy deactivation request:',
          'Select Reviewer',
          reviewerOptions,
          async (selectedReviewerId) => {
            console.log('Selected reviewer ID:', selectedReviewerId);
            
            // Step 2: Get reason after reviewer selection
            PopupService.comment(
              'Please provide a reason for deactivating this policy:',
              'Policy Deactivation Reason',
              async (reason) => {
                if (!reason || reason.trim() === '') {
                  PopupService.warning('Deactivation reason is required.', 'Missing Information');
                  sendPushNotification({
                    title: 'Missing Deactivation Reason',
                    message: 'Policy deactivation request cancelled: Reason is required.',
                    category: 'policy',
                    priority: 'medium',
                    user_id: 'default_user'
                  });
                  return;
                }
                
                try {
                  // Call the API to request status change approval with reviewer ID
                  await axios.post(`/api/policies/${policy.id}/toggle-status/`, {
                    reason: reason.trim(),
                    ReviewerId: selectedReviewerId,
                    cascadeSubpolicies: true
                  });
                  
                  // Show success message
                  PopupService.success('Policy deactivation request submitted. Awaiting approval.', 'Request Submitted');
                  
                  sendPushNotification({
                    title: 'Policy Deactivation Request Submitted',
                    message: `Policy "${policy.name}" deactivation request has been submitted and is awaiting approval.`,
                    category: 'policy',
                    priority: 'high',
                    user_id: 'default_user'
                  });
                  
                  // Refresh data to reflect the new 'Under Review' status
                  await fetchPolicies();
                } catch (error) {
                  console.error('Error submitting deactivation request:', error);
                  
                  // Handle specific error cases
                  if (error.response?.status === 400) {
                    const errorMessage = error.response?.data?.error || '';
                    
                    if (errorMessage.includes('already a pending status change request')) {
                      PopupService.error(
                        'There is already a pending status change request for this policy. Please wait for the current request to be processed.',
                        'Duplicate Request'
                      );
                      sendPushNotification({
                        title: 'Duplicate Policy Deactivation Request',
                        message: `Policy "${policy.name}" already has a pending deactivation request. Please wait for approval.`,
                        category: 'policy',
                        priority: 'medium',
                        user_id: 'default_user'
                      });
                    } else {
                      PopupService.error(
                        `Failed to submit deactivation request: ${errorMessage}`,
                        'Request Failed'
                      );
                      sendPushNotification({
                        title: 'Policy Deactivation Request Failed',
                        message: `Failed to submit deactivation request for policy "${policy.name}": ${errorMessage}`,
                        category: 'policy',
                        priority: 'high',
                        user_id: 'default_user'
                      });
                    }
                  } else {
                    PopupService.error('Failed to submit deactivation request. Please try again.', 'Request Failed');
                    sendPushNotification({
                      title: 'Policy Deactivation Request Failed',
                      message: `Failed to submit deactivation request for policy "${policy.name}": ${error.response?.data?.error || error.message}`,
                      category: 'policy',
                      priority: 'high',
                      user_id: 'default_user'
                    });
                  }
                } finally {
                  // Clear processing flag
                  policy.isProcessing = false;
                }
              }
            );
          }
        );
      } catch (error) {
        console.error('Error fetching reviewers:', error);
        PopupService.error('Failed to load reviewers. Please try again.', 'Load Error');
        sendPushNotification({
          title: 'Reviewers Loading Failed',
          message: `Failed to load reviewers for policy deactivation: ${error.response?.data?.error || error.message}`,
          category: 'policy',
          priority: 'high',
          user_id: 'default_user'
        });
      }
    } else {
      // For activation (Inactive -> Active), use the direct toggle endpoint
      const response = await axios.post(`/api/policies/${policy.id}/toggle-status/`, {
        cascadeSubpolicies: true
      });
     
      // Update local state
      policy.status = response.data.status || 'Active';
     
      // Show feedback to the user
      let message = `Policy status change request submitted.`;
     
      if (response.data.other_versions_deactivated > 0) {
        message += ` ${response.data.other_versions_deactivated} previous version(s) of this policy were automatically deactivated.`;
      }
     
      if (response.data.subpolicies_affected > 0) {
        message += ` ${response.data.subpolicies_affected} subpolicies were also activated.`;
      }
     
      PopupService.success(message, 'Status Update');
      
      sendPushNotification({
        title: 'Policy Activation Successful',
        message: `Policy "${policy.name}" has been successfully activated.`,
        category: 'policy',
        priority: 'high',
        user_id: 'default_user'
      });
     
      // Refresh summary counts
      await fetchPolicies();
    }
  } catch (error) {
    console.error('Error toggling policy status:', error);
    
    // Handle specific error cases
    if (error.response?.status === 400) {
      const errorMessage = error.response?.data?.error || '';
      
      if (errorMessage.includes('already a pending status change request')) {
        PopupService.error(
          'There is already a pending status change request for this policy. Please wait for the current request to be processed.',
          'Duplicate Request'
        );
        sendPushNotification({
          title: 'Duplicate Policy Status Change Request',
          message: `Policy "${policy.name}" already has a pending status change request. Please wait for approval.`,
          category: 'policy',
          priority: 'medium',
          user_id: 'default_user'
        });
      } else {
        PopupService.error(
          `Failed to update policy status: ${errorMessage}`,
          'Update Failed'
        );
        sendPushNotification({
          title: 'Policy Status Update Failed',
          message: `Failed to update status for policy "${policy.name}": ${errorMessage}`,
          category: 'policy',
          priority: 'high',
          user_id: 'default_user'
        });
      }
    } else {
      PopupService.error('Failed to update policy status. Please try again.', 'Update Failed');
      sendPushNotification({
        title: 'Policy Status Update Failed',
        message: `Failed to update status for policy "${policy.name}": ${error.response?.data?.error || error.message}`,
        category: 'policy',
        priority: 'high',
        user_id: 'default_user'
      });
    }
  } finally {
    // Clear processing flag
    policy.isProcessing = false;
  }
}
 
// Add acknowledge policy function - Opens modal to request acknowledgement
const acknowledgePolicy = async (policy) => {
  // Open the acknowledgement request modal for admins
  selectedPolicyForAck.value = policy
  showAcknowledgementModal.value = true
}

// Handle acknowledgement request created
const handleAcknowledgementCreated = async (data) => {
  showAcknowledgementModal.value = false
  selectedPolicyForAck.value = null
  
  // Send notification
  sendPushNotification({
    title: 'Acknowledgement Request Created',
    message: `Acknowledgement request created for "${data.policy_name || 'policy'}". ${data.total_users} users assigned.`,
    category: 'policy',
    priority: 'high',
    user_id: 'default_user'
  });
  
  // Show success with option to view report
  if (data.acknowledgement_request_id) {
    PopupService.confirm(
      `Acknowledgement request created successfully. ${data.total_users} users assigned.\n\nWould you like to view the report now?`,
      'Request Created',
      async () => {
        // Navigate to report when "Yes" is clicked
        router.push({
          name: 'AcknowledgementReport',
          params: { requestId: data.acknowledgement_request_id }
        })
      },
      async () => {
        // Just refresh policies when "No" is clicked
        await fetchPolicies()
      }
    )
  } else {
    // Fallback: just refresh policies
    await fetchPolicies()
  }
}

// Close acknowledgement modal
const closeAcknowledgementModal = () => {
  showAcknowledgementModal.value = false
  selectedPolicyForAck.value = null
}

// View policy acknowledgement reports
const viewPolicyAcknowledgements = async (policy) => {
  try {
    // Fetch all acknowledgement requests for this policy
    const response = await axios.get(API_ENDPOINTS.GET_POLICY_ACKNOWLEDGEMENT_REQUESTS(policy.id))
    
    if (response.data.success && response.data.acknowledgement_requests && response.data.acknowledgement_requests.length > 0) {
      // If there are multiple requests, show the most recent one
      const latestRequest = response.data.acknowledgement_requests[0]
      
      // Navigate to the report page
      router.push({
        name: 'AcknowledgementReport',
        params: { requestId: latestRequest.acknowledgement_request_id }
      })
    } else {
      // No reports found - show info message instead of error
      PopupService.info(
        'There are no reports for this policy.',
        'No Reports Found'
      )
    }
  } catch (error) {
    console.error('Error fetching acknowledgement requests:', error)
    
    // For any error when fetching acknowledgement reports, show "no reports found"
    // This handles cases where policy doesn't exist, no requests exist, or any other error
    PopupService.info(
      'There are no reports for this policy.',
      'No Reports Found'
    )
  }
}
 
function goBack() {
  const routeParams = { name: 'FrameworkExplorer' }
  
  // If an entity filter is selected, pass it back as a query parameter
  if (selectedEntity.value) {
    routeParams.query = { entity: selectedEntity.value }
  }
  
  router.push(routeParams)
}
 
// Fetch policies on component mount
onMounted(async () => {
  // Check for session framework first, then fetch policies
  await checkSelectedFrameworkFromSession()
  await fetchPolicies()
  await fetchEntities()
  
  // Check if there's an entity filter from the route query parameters
  const entityFromRoute = route.query.entity
  if (entityFromRoute) {
    selectedEntity.value = entityFromRoute
  }
})

const entityDropdownConfig = computed(() => ({
  label: 'Entity',
  values: [
    { value: '', label: 'All Entities' },
    ...entities.value.map(e => ({ value: e.id, label: e.label }))
  ]
}))
</script>
 
<style scoped>
.framework-policies-container {
  padding: 24px 32px;
  margin-left: 280px;
  width: calc(100vw - 280px - 64px);
  max-width: 100%;
  box-sizing: border-box;
  position: relative;
  padding-top: 25px; /* Add space for export controls */
  overflow-x: hidden;
}

h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 8px 0;
  letter-spacing: -1px;
  text-align: left;
  margin-bottom: 50px;
  margin-top: 0;
}


.export-controls {
  position: absolute;
  top: 20px;
  right: 32px;
  z-index: 10;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  width: auto;
  margin-bottom: 0;
}

.export-controls-inner {
  display: flex;
  gap: 8px;
  align-items: center;
}

.export-dropdown {
  min-width: 120px;
  height: 32px;
  border-radius: 8px;
  border: 1.5px solid #e2e8f0;
  font-size: 0.85rem;
  padding: 0 10px;
  background: #fff;
  color: #222;
}

.export-controls button {
  padding: 6px 16px;
  border-radius: 8px;
  border: none;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  background: #4f6cff;
  color: #fff;
  transition: background 0.2s;
}

.export-controls button:disabled {
  background: #bfc8e6;
  cursor: not-allowed;
}
 
.breadcrumb-tab {
  margin-bottom: 24px;
}
 
.breadcrumb-chip {
  background: #e8edfa;
  color: #4f6cff;
  border-radius: 24px;
  padding: 10px 12px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  font-size: 0.95rem;
  box-shadow: 0 2px 8px rgba(79,108,255,0.12);
  letter-spacing: 0.01em;
  transition: all 0.2s ease;
}
 
.breadcrumb-chip:hover {
  box-shadow: 0 4px 12px rgba(79,108,255,0.18);
  transform: translateY(-1px);
}
 
.breadcrumb-close {
  margin-left: 12px;
  color: #888;
  font-size: 1.1rem;
  cursor: pointer;
  font-weight: bold;
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
}
 
.breadcrumb-close:hover {
  color: #e53935;
  background-color: rgba(229, 57, 53, 0.1);
}

.top-controls {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 20px;
  margin-bottom: 5px;
  width: 100%;
  flex-wrap: wrap;
  max-width: 100%;
}

.entity-dropdown-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 0;
}

/* View Toggle Controls */
.view-toggle-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #f8faff;
  border-radius: 8px;
  padding: 4px;
  border: 1px solid #e8edfa;
  margin-left: auto;
}

.view-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.9rem;
}

.view-toggle-btn:hover {
  background: #e8edfa;
  color: #4f6cff;
}

.view-toggle-btn.active {
  background: #4f6cff;
  color: white;
  box-shadow: 0 2px 4px rgba(79, 108, 255, 0.2);
}

/* Card View Styles (Existing) */
.policy-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
  width: 100%;
  max-width: 100%;
  margin-top: 24px;
  box-sizing: border-box;
  padding: 0 8px;
  overflow-x: hidden;
}
 
.policy-card {
  background: #f7f7fa;
  border-radius: 12px;
  padding: 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
  font-size: 0.85rem;
  cursor: pointer;
  min-height: 100px;
  box-shadow: 0 2px 8px rgba(79,108,255,0.08);
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  margin: 0;
  min-width: 0;
  overflow: hidden;
}
 
.policy-card:hover {
  transform: translateY(-2px) scale(1.025);
  box-shadow: 0 8px 24px rgba(79,108,255,0.13);
}
 
.policy-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1.1rem;
  font-weight: 700;
  width: 100%;
  margin-bottom: 4px;
}
 
.policy-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #e8edfa;
  border-radius: 8px;
  color: #000000;
  font-size: 1rem;
}
 
.policy-card-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.policy-card-category {
  font-size: 0.85rem;
  color: #000000;
  font-weight: 600;
  background: #e8edfa;
  border-radius: 8px;
  padding: 2px 8px;
  width: fit-content;
  margin-bottom: 6px;
}

.policy-card-type {
  font-size: 0.85rem;
  font-weight: 600;
  background: #ffeaea;
  color: #e53935;
  border-radius: 8px;
  padding: 2px 8px;
  width: fit-content;
}

.policy-card-type.external {
  background: #ffeaea;
  color: #e53935;
}
 
.policy-card-desc {
  font-size: 0.9rem;
  line-height: 1.6;
  color: #444;
  font-weight: 400;
  flex-grow: 1;
}
 
.policy-card-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  width: 100%;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 10px;
}

.policy-title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}
 
.policy-card-title {
  margin-left: 0;
  word-break: break-word;
  color: #000000;
}

.document-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #f0f4ff;
  border-radius: 50%;
  color: #4f6cff;
  cursor: pointer;
  transition: all 0.2s ease;
}
 
.document-icon:hover {
  background: #e0e7ff;
  transform: translateY(-2px);
}

.acknowledge-btn {
  height: 28px !important;
  font-size: 0.95rem !important;
  min-width: 90px;
  border-radius: 6px !important;
  padding: 0 12px;
  font-weight: 600 !important;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: #4f6cff;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}
 
.acknowledge-btn.acknowledged {
  background: #22a722 !important;
  color: #fff !important;
  opacity: 1;
  cursor: default;
  box-shadow: 0 2px 8px rgba(34, 167, 34, 0.3);
}
 
.acknowledge-btn.acknowledged::before {
  content: "✓ ";
  margin-right: 4px;
  font-weight: bold;
}
 
.acknowledge-btn:hover:not(.acknowledged) {
  background: #4441d6 !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 108, 255, 0.3);
}

/* View Reports Button */
.view-reports-btn {
  height: 28px !important;
  font-size: 0.9rem !important;
  min-width: 100px;
  border-radius: 6px !important;
  padding: 0 12px;
  font-weight: 600 !important;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1.5px solid #4f6cff;
  background: #fff;
  color: #4f6cff;
  cursor: pointer;
  transition: all 0.2s;
}

.view-reports-btn:hover {
  background: #4f6cff;
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 108, 255, 0.3);
}

.view-reports-btn-list {
  padding: 6px 12px;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: 6px;
  border: 1.5px solid #4f6cff;
  background: #fff;
  color: #4f6cff;
  cursor: pointer;
  transition: all 0.2s;
}

.view-reports-btn-list:hover {
  background: #4f6cff;
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 108, 255, 0.3);
}

/* List View Styles */
.policy-list-container {
  width: 100%;
  margin-top: 20px;
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid #e8edfa;
}

.policy-list-header {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1fr 2.5fr 1.2fr 1.5fr;
  gap: 20px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #f8faff 0%, #f0f4ff 100%);
  border-bottom: 2px solid #e8edfa;
  font-weight: 700;
  font-size: 0.9rem;
  color: #000;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.list-header-item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  color: #000 !important;
  font-weight: bold !important;
}

.list-header-item:last-child {
  justify-content: center;
}

.policy-list {
  background: #fff;
}

.policy-list-item {
  border-bottom: 1px solid #f1f5f9;
}

.policy-list-item:last-child {
  border-bottom: none;
}

.list-item-content {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1fr 2.5fr 1.2fr 1.5fr;
  gap: 18px;
  padding: 18px 18px;
  align-items: center;
  font-size: 0.85rem;
}

.list-item-content .policy-title,
.list-item-content .category-badge,
.list-item-content .type-badge,
.list-item-content .description-text,
.list-item-content .status-badge,
.list-item-content .policy-actions {
  font-size: 0.85rem;
}

.policy-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.policy-icon-list {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #e8edfa 0%, #d0d9f7 100%);
  border-radius: 12px;
  color: #4f6cff;
  font-size: 1.1rem;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(79, 108, 255, 0.15);
}

.policy-name-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.policy-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1.2;
}

.policy-id {
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 500;
}

.policy-category-cell {
  display: flex;
  align-items: center;
}

.category-text {
  color: #000;
  font-size: 0.9rem;
  font-weight: 500;
}

.policy-type-cell {
  display: flex;
  align-items: center;
}

.type-text {
  color: #000;
  font-size: 0.9rem;
  font-weight: 500;
}

.policy-description-cell {
  display: flex;
  align-items: center;
}

.description-text {
  font-size: 0.9rem;
  color: #64748b;
  line-height: 1.4;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.policy-status-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.policy-actions-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.list-action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.acknowledge-btn-list {
  padding: 6px 12px;
  border-radius: 6px;
  border: none;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  background: #4f6cff;
  color: #fff;
  transition: all 0.2s ease;
  min-width: 80px;
  position: relative;
}

.acknowledge-btn-list.acknowledged {
  background: #22a722;
  color: #fff;
  cursor: default;
  box-shadow: 0 2px 8px rgba(34, 167, 34, 0.3);
}

.acknowledge-btn-list.acknowledged::before {
  content: "✓ ";
  margin-right: 4px;
  font-weight: bold;
}

.acknowledge-btn-list:hover:not(.acknowledged) {
  background: #3a57e8;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 108, 255, 0.3);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  background: linear-gradient(135deg, #f0f4ff 0%, #e0e7ff 100%);
  color: #4f6cff;
  border: 1px solid #c7d0f0;
}

.action-btn:hover {
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(79, 108, 255, 0.2);
}

.action-btn i {
  font-size: 0.9rem;
}

.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 26px;
  margin-right: 6px;
  vertical-align: middle;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #4f6cff;
  -webkit-transition: .4s;
  transition: .4s;
  border-radius: 26px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 4px;
  bottom: 4px;
  background-color: #f5f6fa;
  -webkit-transition: .4s;
  transition: .4s;
  border-radius: 50%;
}

.switch input:checked + .slider {
  background-color: #4f6cff;
}

.switch input:not(:checked) + .slider {
  background-color: #bfc8e6;
}

.switch input:checked + .slider:before {
  -webkit-transform: translateX(18px);
  -ms-transform: translateX(18px);
  transform: translateX(18px);
}

.switch-label {
  font-weight: 600;
  color: #4f6cff;
  min-width: 50px;
  display: inline-block;
  text-align: left;
  font-size: 0.8rem;
}

.switch-label.active {
  color: #22a722;
}

.switch-label.inactive {
  color: #e53935;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
 
.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 700px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 5px 30px rgba(0, 0, 0, 0.15);
}
 
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
  position: sticky;
  top: 0;
  background: white;
  z-index: 2;
}
 
.modal-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.4rem;
}
 
.close-btn {
  font-size: 1.8rem;
  font-weight: bold;
  color: #666;
  cursor: pointer;
  transition: color 0.2s;
}
 
.close-btn:hover {
  color: #e53935;
}
 
.modal-body {
  padding: 24px;
}
 
.modal-loading, .modal-error {
  padding: 24px;
  text-align: center;
  color: #666;
}
 
.detail-row {
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
}
 
.detail-label {
  font-weight: 600;
  width: 140px;
  color: #555;
}
 
.detail-value {
  flex: 1;
  min-width: 200px;
}
 
.doc-link {
  color: #4f6cff;
  text-decoration: none;
  font-weight: 600;
}
 
.doc-link:hover {
  text-decoration: underline;
}
 
/* Subpolicies section */
.subpolicies-section {
  margin-top: 24px;
  border-top: 1px solid #eee;
  padding-top: 16px;
}
 
.subpolicies-section h4 {
  font-size: 1.2rem;
  margin-bottom: 16px;
  color: #2c3e50;
}
 
.subpolicy-item {
  background: #f8f9fd;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  border-left: 3px solid #4f6cff;
}
 
.subpolicy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
 
.subpolicy-name {
  font-weight: 600;
  font-size: 1rem;
  color: #2c3e50;
}
 
.subpolicy-status {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}
 
.subpolicy-status.approved {
  color: #22a722;
  background: #e8f7ee;
}
 
.subpolicy-status.inactive, .subpolicy-status.rejected {
  color: #e53935;
  background: #fbeaea;
}
 
.subpolicy-status.under.review {
  color: #f5a623;
  background: #fff5e6;
}
 
.subpolicy-detail {
  margin-bottom: 6px;
  font-size: 0.9rem;
}
 
.subpolicy-label {
  font-weight: 600;
  color: #555;
  margin-right: 6px;
}
 
.no-subpolicies {
  margin-top: 16px;
  color: #666;
  font-style: italic;
  text-align: center;
}

/* Summary Section */
.summary-section {
  margin-bottom: 32px;
}

.summary-section-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 20px 0;
  text-align: center;
  letter-spacing: -0.5px;
}

.summary-cards {
  display: flex;
  width: 100%;
  max-width: 300px;
  margin: 0;
}

.summary-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  background: white;
  border-radius: 0;
  padding: 12px 16px;
  font-size: 0.9rem;
  font-weight: 600;
  text-align: left;
  min-width: 150px;
  min-height: 60px;
  box-shadow: none;
  transition: border-bottom 0.3s ease, background 0.3s ease;
  position: relative;
  cursor: pointer;
  flex: 1;
  border: none;
  border-bottom: none;
}

.summary-card.active-policy {
  background: white !important;
  border-bottom: 3px solid #4f6cff !important;
  border-radius: 0;
}

.summary-card.active-policy:hover {
  background: white !important;
  border-bottom: 3px solid #4f6cff !important;
}

.summary-card.inactive-policy {
  background: white;
  border-radius: 0 20px 20px 0;
}

.summary-card.inactive-policy:hover {
  border-color: rgba(245, 166, 35, 0.4);
  box-shadow: 0 8px 30px rgba(245, 166, 35, 0.25);
}

.summary-card.framework-status-card {
  background: linear-gradient(135deg, #f0f4ff 60%, #f2f2f7 100%);
}

.summary-card.total-policy {
  background: linear-gradient(135deg, #f8f9fa 60%, #f2f2f7 100%);
}

.summary-card-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  width: 100%;
  height: 100%;
  text-align: left;
  padding: 8px 0;
  gap: 4px;
}

.summary-label {
  font-size: 0.75rem !important;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 3px;
  letter-spacing: 0.2px;
  white-space: nowrap;
  overflow: visible;
  text-overflow: clip;
}

.summary-value {
  display: block;
  font-size: 0.6rem;
  font-weight: 300;
  margin-top: 0;
  color: #222;
  text-shadow: none;
  text-align: left!important;
}

.summary-icon-wrapper {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  font-size: 1.4rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.active-policy .summary-icon-wrapper {
  background: #e6f7ff;
  color: #4f6cff;
}

.inactive-policy .summary-icon-wrapper {
  background: #fff5e6;
  color: #f5a623;
}

.framework-status-card .summary-icon-wrapper {
  background: #f0f4ff;
  color: #4f6cff;
}

.total-policy .summary-icon-wrapper {
  background: #f8f9fa;
  color: #6c757d;
}

.framework-status {
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.framework-status.active {
  color: #22a722;
}

.framework-status.inactive {
  color: #e53935;
}

.summary-card:hover .summary-icon-wrapper {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}

.summary-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(79,108,255,0.15);
}

/* Responsive Design */
@media (max-width: 1400px) {
  .policy-list-header,
  .list-item-content {
    grid-template-columns: 1.8fr 1fr 0.8fr 2fr 1fr 1.2fr;
    gap: 16px;
  }
  
  .policy-card-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }
}

@media (max-width: 1200px) {
  .policy-list-header,
  .list-item-content {
    grid-template-columns: 2fr 1fr 0.8fr 1.5fr 1fr 1fr;
    gap: 12px;
  }
  
  .policy-list-container {
    margin-left: -20px;
    margin-right: -20px;
    border-radius: 0;
  }
  
  .policy-card-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }
}


@media (max-width: 800px) {
  .summary-cards {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .summary-card {
    padding: 12px 10px;
    min-height: 80px;
  }
  
  .summary-section-title {
    font-size: 1.2rem;
    margin-bottom: 16px;
  }
  
  .policy-list-header {
    display: none;
  }
  
  .list-item-content {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
  }
  
  .policy-name-cell,
  .policy-category-cell,
  .policy-type-cell,
  .policy-description-cell,
  .policy-status-cell,
  .policy-actions-cell {
    width: 100%;
    justify-content: flex-start;
  }
  
  .policy-list-item:hover {
    transform: none;
    box-shadow: none;
  }
  
  .policy-card-grid {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 0 4px;
  }
  
  .framework-policies-container {
    padding: 20px;
  }
  
  .view-toggle-controls {
    margin-left: 0;
    margin-top: 10px;
  }
  
  .top-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
}
</style>