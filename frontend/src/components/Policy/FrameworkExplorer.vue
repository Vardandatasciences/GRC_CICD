<template>
  <div class="framework-explorer-container">
    <!-- Framework Details View -->
    <div v-if="showModal" class="framework-details-view">
      <div class="details-header">
        <button class="policy-dashboard-back-btn" @click="closeModal">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h2>Framework Details</h2>
      </div>
      
      <div v-if="isLoadingDetails" class="loading-state">
        <i class="fas fa-spinner fa-spin"></i> Loading details...
      </div>
      
      <div v-else-if="frameworkDetails" class="details-content">
        <div class="detail-row">
          <span class="detail-label">Framework Name</span>
          <span class="detail-value">{{ frameworkDetails.FrameworkName }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Description</span>
          <span class="detail-value">{{ frameworkDetails.FrameworkDescription }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Category</span>
          <span class="detail-value">{{ frameworkDetails.Category }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Version</span>
          <span class="detail-value">{{ frameworkDetails.CurrentVersion }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Status</span>
          <span class="detail-value">{{ frameworkDetails.Status }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Active/Inactive</span>
          <span class="detail-value">{{ frameworkDetails.ActiveInactive }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Identifier</span>
          <span class="detail-value">{{ frameworkDetails.Identifier }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Effective Date</span>
          <span class="detail-value">{{ formatDate(frameworkDetails.EffectiveDate) }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Start Date</span>
          <span class="detail-value">{{ formatDate(frameworkDetails.StartDate) }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">End Date</span>
          <span class="detail-value">{{ formatDate(frameworkDetails.EndDate) }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Created By</span>
          <span class="detail-value">{{ frameworkDetails.CreatedByName }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Created Date</span>
          <span class="detail-value">{{ formatDate(frameworkDetails.CreatedByDate) }}</span>
        </div>
        <div class="detail-row" v-if="frameworkDetails.DocURL">
          <span class="detail-label">Documentation</span>
          <span class="detail-value doc-value">
            <a :href="frameworkDetails.DocURL" target="_blank" class="doc-link">View Documentation</a>
          </span>
        </div>
      </div>
      
      <div v-else class="error-state">
        Failed to load framework details.
      </div>
    </div>

    <!-- Main Framework Explorer Content -->
    <div v-else>
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
          <button class="export-btn" @click="exportFrameworkPolicies">
            <i class="fas fa-download"></i>
            Export
          </button>
        </div>
      </div>
      <h1>Framework Explorer</h1>
    <!-- Framework Summary Cards - Only show in Framework tab -->
    <div v-if="activeMainTab === 'framework'" class="summary-section">
     
      <div class="summary-cards">
        <!-- Framework Cards -->
        <div class="summary-card" :class="{ 'active-framework': activeFrameworkTab === 'Active' }" @click="filterByStatus('Active', 'framework')">
          <div class="summary-card-content">
            <div class="summary-label">ACTIVE FRAMEWORKS</div>
            <div class="summary-value">{{ summary.active_frameworks }}</div>
          </div>
        </div>
        <div class="summary-card" :class="{ 'active-framework': activeFrameworkTab === 'Inactive' }" @click="filterByStatus('Inactive', 'framework')">
          <div class="summary-card-content">
            <div class="summary-label">INACTIVE FRAMEWORKS</div>
            <div class="summary-value">{{ summary.inactive_frameworks }}</div>
              </div>
        </div>
      </div>
    </div>
    
    
    <div class="top-controls">
      <div class="framework-dropdown-section">
        <CustomDropdown
          :config="frameworkDropdownConfig"
          v-model="selectedFrameworkId"
        />
      </div>
      <div class="internal-external-dropdown-section">
        <CustomDropdown
          :config="typeDropdownConfig"
          v-model="selectedInternalExternal"
        />
      </div>
      <div class="entity-dropdown-section">
        <CustomDropdown
          :config="entityDropdownConfig"
          v-model="selectedEntity"
        />
      </div>
      
      <!-- View Toggle Controls -->
      <div class="tab-controls">
        <button 
          class="tab-btn" 
          @click="currentView = 'list'"
        >
          Framework
        </button>
        <button 
          class="tab-btn" 
          @click="currentView = 'card'"
        >
          Policy
        </button>
      </div>
    </div>

    <!-- List View -->
    <div v-if="currentView === 'list'" class="framework-list-container">
      <div class="framework-list-header">
        <div class="list-header-item framework-name">Framework</div>
        <div class="list-header-item framework-category">Category</div>
        <div class="list-header-item framework-type">Type</div>
        <div class="list-header-item framework-description">Description</div>
        <div class="list-header-item framework-status">Status</div>
        <div class="list-header-item framework-actions">Actions</div>
      </div>
      
      <div class="framework-list">
        <template v-for="fw in filteredFrameworks" :key="fw.id">
          <div class="framework-list-item" @click="toggleFrameworkExpansion(fw.id)">
            <div class="list-item-content">
              <div class="framework-name-cell">
                <div class="framework-name-text">
                  <div class="framework-title">{{ fw.name }}</div>
                  <div class="framework-id">ID: {{ fw.id }}</div>
                </div>
              </div>
              
              <div class="framework-category-cell">
                <span class="category-text">{{ fw.category }}</span>
              </div>
              
              <div class="framework-type-cell">
                <span class="type-text">
                  {{ fw.internalExternal || 'Internal' }}
                </span>
              </div>
              
              <div class="framework-description-cell">
                <p class="description-text">{{ fw.description }}</p>
              </div>
              
              <div class="framework-status-cell">
                <div class="status-controls">
                  <label class="switch" @click.stop>
                    <input type="checkbox" :checked="fw.status === 'Active'" @change.stop="toggleStatus(fw)" />
                    <span class="slider"></span>
                  </label>
                  <span class="switch-label" :class="fw.status === 'Active' ? 'active' : 'inactive'">{{ fw.status }}</span>
                </div>
              </div>
              
            <div class="framework-actions-cell">
              <button class="action-btn details-btn" @click.stop="showFrameworkDetails(fw.id)">
                <span>Details</span>
              </button>
              <i
                :class="expandedFrameworks.includes(fw.id) ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"
                class="expand-arrow"
                @click.stop="toggleFrameworkExpansion(fw.id)"
              ></i>
            </div>
            </div>
          </div>
          
          <!-- Expandable Row for Framework Versions -->
          <div v-if="expandedFrameworks.includes(fw.id)" class="framework-expandable-row">
            <div class="expandable-content">
              <div class="expandable-header">
                <h4>Framework Versions</h4>
                <div class="hierarchy-breadcrumb">
                  <span class="hierarchy-item active">{{ fw.name }}</span>
                </div>
              </div>
              <div v-if="fw.versions && fw.versions.length > 0" class="versions-list">
                <div v-for="version in fw.versions" :key="version.id" class="version-item">
                  <div class="version-header" @click="toggleVersionExpansion(version.id, fw.id)">
                    <div class="version-main-info">
                      <span class="version-name">{{ version.name }}</span>
                    </div>
                    <div class="version-info">
                      <span class="version-status" :class="statusClass(version.status)">{{ version.status }}</span>
                      <i :class="expandedVersions.includes(version.id) ? 'fas fa-chevron-up' : 'fas fa-chevron-down'" class="expand-arrow"></i>
                    </div>
                  </div>
                  
                  <!-- Expandable Policies for Version -->
                  <div v-if="expandedVersions.includes(version.id)" class="version-policies">
                    <div v-if="version.policies && version.policies.length > 0" class="version-policies-container">
                      <div class="policy-list-header">
                        <div class="list-header-item">Policy</div>
                        <div class="list-header-item">Category</div>
                        <div class="list-header-item">Type</div>
                        <div class="list-header-item">Description</div>
                        <div class="list-header-item">Status</div>
                        <div class="list-header-item">Actions</div>
                      </div>
                      
                      <div class="policy-list">
                        <div
                          v-for="policy in version.policies"
                          :key="policy.id"
                          class="policy-list-item"
                          @click="toggleInlinePolicyExpansion(policy)"
                        >
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
                                  <input
                                    type="checkbox"
                                    :checked="isPolicyActive(policy)"
                                    @change.stop="togglePolicyStatus(policy, version.id, fw.id)"
                                  />
                                  <span class="slider"></span>
                                </label>
                                <span
                                  class="switch-label"
                                  :class="isPolicyActive(policy) ? 'active' : 'inactive'"
                                >
                                  {{ getPolicyStatusLabel(policy) }}
                                </span>
                              </div>
                            </div>
                            
                            <div class="policy-actions-cell">
                              <div class="list-action-buttons">
                                <button
                                  v-if="isPolicyActive(policy)"
                                  @click.stop="acknowledgePolicy(policy)"
                                  class="acknowledge-btn-list"
                                  title="Create acknowledgement request for this policy"
                                >
                                  Request Ack
                                </button>
                                <button
                                  v-if="isPolicyActive(policy)"
                                  @click.stop="viewPolicyAcknowledgements(policy)"
                                  class="view-reports-btn-list"
                                  title="View acknowledgement reports for this policy"
                                >
                                  View Reports
                                </button>
                                <button
                                  class="action-btn details-btn"
                                  @click.stop="showPolicyDetails(policy.id, fw.id)"
                                >
                                  <span>Details</span>
                                </button>
                              </div>
                            </div>
                          </div>
                          
                          <!-- Inline Policy Versions, then Subpolicies per Version -->
                          <div
                            v-if="expandedInlinePolicies.includes(policy.id)"
                            class="inline-policy-versions-row"
                            @click.stop
                          >
                            <div class="inline-policy-versions-container">
                              <div
                                v-if="policy.versions && policy.versions.length > 0"
                                class="inline-policy-versions-list"
                              >
                                <div
                                  v-for="pVersion in policy.versions"
                                  :key="pVersion.id"
                                  class="inline-policy-version-item"
                                >
                                  <div
                                    class="inline-policy-version-header"
                                    @click="toggleInlinePolicyVersionExpansion(pVersion, policy, version.id, fw.id)"
                                  >
                                    <div class="inline-policy-version-main">
                                      <span class="inline-policy-version-name">
                                        {{ pVersion.name }}
                                      </span>
                                    </div>
                                    <div class="inline-policy-version-meta">
                                      <span
                                        v-if="pVersion.previous_version_name"
                                        class="previous-version"
                                      >
                                        Previous: {{ pVersion.previous_version_name }}
                                      </span>
                                      <i
                                        :class="expandedPolicyVersions.includes(pVersion.id) ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"
                                        class="expand-arrow"
                                      ></i>
                                    </div>
                                  </div>

                                  <!-- Subpolicies for this policy version -->
                                  <div
                                    v-if="expandedPolicyVersions.includes(pVersion.id)"
                                    class="inline-subpolicies-container"
                                  >
                                    <div
                                      v-if="pVersion.subpolicies && pVersion.subpolicies.length > 0"
                                      class="inline-subpolicies-list"
                                    >
                                      <div
                                        v-for="subpolicy in pVersion.subpolicies"
                                        :key="subpolicy.id"
                                        class="inline-subpolicy-item"
                                      >
                                        <div class="inline-subpolicy-main">
                                          <div class="inline-subpolicy-name">
                                            {{ subpolicy.name }}
                                          </div>
                                          <div class="inline-subpolicy-meta">
                                            <span class="inline-subpolicy-category">
                                              {{ subpolicy.category || 'Subpolicy' }}
                                            </span>
                                            <span
                                              class="inline-subpolicy-status"
                                              :class="statusClass(subpolicy.status)"
                                            >
                                              {{ subpolicy.status }}
                                            </span>
                                          </div>
                                        </div>
                                        <div
                                          v-if="subpolicy.description"
                                          class="inline-subpolicy-description"
                                        >
                                          {{ subpolicy.description }}
                                        </div>
                                      </div>
                                    </div>
                                    <div
                                      v-else-if="inlineSubpoliciesLoading[pVersion.id]"
                                      class="loading-message"
                                    >
                                      <p>Loading subpolicies...</p>
                                    </div>
                                    <div v-else class="no-data-message">
                                      <p>No subpolicies found for this version.</p>
                                    </div>
                                  </div>
                                </div>
                              </div>
                              <div v-else class="no-data-message">
                                <p>No versions found for this policy.</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div v-else-if="isLoadingPolicies[version.id]" class="loading-message">
                      <p>Loading policies...</p>
                    </div>
                    <div v-else class="no-data-message">
                      <p>No policies found for this version.</p>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else-if="isLoadingVersions[fw.id]" class="loading-message">
                <p>Loading versions...</p>
              </div>
              <div v-else class="no-data-message">
                <p>No versions found for this framework.</p>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Card View -->
    <div v-if="currentView === 'card'" class="framework-cards-container">
      <div class="framework-cards-grid">
        <div v-for="fw in filteredFrameworks" :key="fw.id" class="framework-card" @click="goToPolicies(fw.id)">
          <div class="framework-card-header">
            <div class="framework-card-icon">
              <i class="fas fa-book"></i>
            </div>
            <div class="framework-card-status">
              <label class="switch" @click.stop>
                <input type="checkbox" :checked="fw.status === 'Active'" @change.stop="toggleStatus(fw)" />
                <span class="slider"></span>
              </label>
            </div>
          </div>
          
          <div class="framework-card-content">
            <h3 class="framework-card-title">{{ fw.name }}</h3>
            <p class="framework-card-id">ID: {{ fw.id }}</p>
            
            <div class="framework-card-badges">
              <span class="category-badge">{{ fw.category }}</span>
              <span class="type-badge" :class="{ 
                'type-internal': (fw.internalExternal || 'Internal') === 'Internal',
                'type-external': (fw.internalExternal || 'Internal') === 'External'
              }">
                {{ fw.internalExternal || 'Internal' }}
              </span>
            </div>
            
            <p class="framework-card-description">{{ fw.description }}</p>
            
            <div class="framework-card-footer">
              <span class="status-indicator" :class="fw.status === 'Active' ? 'active' : 'inactive'">
                {{ fw.status }}
              </span>
              <button class="card-details-btn" @click.stop="showFrameworkDetails(fw.id)">
                <i class="fas fa-info-circle"></i>
                Details
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    </div>

    <!-- Acknowledgement Request Modal -->
    <CreateAcknowledgementModal
      v-if="showAcknowledgementModal && selectedPolicyForAck"
      :isVisible="showAcknowledgementModal"
      :policy="selectedPolicyForAck"
      @close="closeAcknowledgementModal"
      @created="handleAcknowledgementCreated"
    />

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>
 
<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import policyDataService from '@/services/policyService'
import { PopupService } from '@/modules/popus/popupService'
import PopupModal from '@/modules/popus/PopupModal.vue'
import CustomDropdown from '@/components/CustomDropdown.vue'
import CreateAcknowledgementModal from './CreateAcknowledgementModal.vue'
import { API_ENDPOINTS } from '@/config/api.js'

// Add view state
const currentView = ref('list') // 'list' or 'card'

// Add active framework tab state
const activeFrameworkTab = ref('Active') // 'Active' or 'Inactive'
 
const frameworks = ref([])
const selectedFrameworkId = ref('')
const selectedInternalExternal = ref('')
const selectedEntity = ref('')
const entities = ref([])
const router = useRouter()
// Acknowledgement modal state (shared with FrameworkPolicies behaviour)
const showAcknowledgementModal = ref(false)
const selectedPolicyForAck = ref(null)
const summary = ref({
  active_frameworks: 0,
  inactive_frameworks: 0,
  active_policies: 0,
  inactive_policies: 0
})

// Store original summary for when no framework is selected
const allFrameworksSummary = ref({
  active_frameworks: 0,
  inactive_frameworks: 0,
  active_policies: 0,
  inactive_policies: 0
})
const isLoading = ref(false)
const statusFilter = ref(null)
const typeFilter = ref(null)
 
// Modal and details states
const showModal = ref(false)
const isLoadingDetails = ref(false)
const frameworkDetails = ref(null)
 
// Add export controls above the framework grid
const selectedExportFormat = ref('');

// Expandable state for frameworks
const expandedFrameworks = ref([])
const isLoadingVersions = ref({})
const expandedVersions = ref([])
const isLoadingPolicies = ref({})
const expandedInlinePolicies = ref([]) // policies expanded to show their versions
const expandedPolicyVersions = ref([]) // policy versions expanded to show subpolicies
const inlineSubpoliciesLoading = ref({}) // keyed by policy version id

// Add push notification function
const sendPushNotification = async (notificationData) => {
  try {
    // Get JWT token from localStorage
    const token = localStorage.getItem('access_token');
    const headers = {
      'Content-Type': 'application/json',
    };
    
    // Add Authorization header if token exists
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(API_ENDPOINTS.PUSH_NOTIFICATION, {
      method: 'POST',
      headers: headers,
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
};

const exportFrameworkPolicies = async () => {
  if (!selectedExportFormat.value) {
    PopupService.warning('Please select a format.', 'Missing Selection');
    return;
  }
  try {
    // Call the new export-all endpoint
    const res = await axios.post(API_ENDPOINTS.FRAMEWORKS_EXPORT_ALL, {
      format: selectedExportFormat.value
    });
    const { file_url, file_name } = res.data;
    if (!file_url || !file_name) {
      PopupService.error('Export failed: No file URL or name returned.', 'Export Error');
      sendPushNotification({
        title: 'Framework Export Failed',
        message: 'Export failed: No file URL or name returned.',
        category: 'framework',
        priority: 'high',
        user_id: 'default_user'
      });
      return;
    }
    
    // Automatically open the AWS URL in a new tab
    try {
      // Open the file URL in a new tab
      window.open(file_url, '_blank');
      
      PopupService.success('Export completed successfully! File opened in new tab.', 'Export Success');
      sendPushNotification({
        title: 'Framework Export Completed',
        message: `Framework export completed successfully in ${selectedExportFormat.value.toUpperCase()} format (ALL frameworks). File opened in new tab.`,
        category: 'framework',
        priority: 'medium',
        user_id: 'default_user'
      });
    } catch (openErr) {
      // Fallback: if opening in new tab fails, try to download the file
      console.warn('Failed to open file in new tab, falling back to download:', openErr);
      try {
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
          title: 'Framework Export Completed',
          message: `Framework export completed successfully in ${selectedExportFormat.value.toUpperCase()} format (ALL frameworks). File downloaded.`,
          category: 'framework',
          priority: 'medium',
          user_id: 'default_user'
        });
      } catch (downloadErr) {
        PopupService.success('Export completed successfully! File available at AWS URL.', 'Export Success');
        sendPushNotification({
          title: 'Framework Export Completed',
          message: `Framework export completed successfully in ${selectedExportFormat.value.toUpperCase()} format (ALL frameworks). File available at AWS URL.`,
          category: 'framework',
          priority: 'medium',
          user_id: 'default_user'
        });
        console.error('Download fallback also failed:', downloadErr);
      }
    }
  } catch (err) {
    PopupService.error('Export failed. Please try again.', 'Export Error');
    sendPushNotification({
      title: 'Framework Export Failed',
      message: `Failed to export frameworks: ${err.response?.data?.error || err.message}`,
      category: 'framework',
      priority: 'high',
      user_id: 'default_user'
    });
    console.error(err);
  }
};
 
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
 
// Check for selected framework from session and set it as default
const checkSelectedFrameworkFromSession = async () => {
  try {
    console.log('🔍 DEBUG: Checking for selected framework from session in FrameworkExplorer...')
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
          // Set the selected framework ID to the session framework
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

// Fetch frameworks from API
const fetchFrameworks = async () => {
  isLoading.value = true
  try {
    const hasFilters = Boolean(
      selectedEntity.value ||
      statusFilter.value ||
      typeFilter.value ||
      selectedInternalExternal.value
    )

    if (!hasFilters) {
      console.log('🔍 [FrameworkExplorer] Checking for cached framework explorer data...')

      if (!window.policyDataFetchPromise && !policyDataService.hasFrameworkExplorerCache()) {
        console.log('🚀 [FrameworkExplorer] Starting policy prefetch (user navigated directly)...')
        window.policyDataFetchPromise = policyDataService.fetchAllPolicyData()
      }

      if (window.policyDataFetchPromise) {
        console.log('⏳ [FrameworkExplorer] Waiting for policy prefetch to complete...')
        try {
          await window.policyDataFetchPromise
          console.log('✅ [FrameworkExplorer] Prefetch completed')
        } catch (prefetchError) {
          console.warn('⚠️ [FrameworkExplorer] Prefetch failed, will fetch directly from API', prefetchError)
        }
      }

      if (policyDataService.hasFrameworkExplorerCache()) {
        console.log('✅ [FrameworkExplorer] Using cached framework explorer data')
        const cachedFrameworks = policyDataService.getFrameworkExplorerFrameworks() || []
        const cachedSummary = policyDataService.getFrameworkExplorerSummary()

        frameworks.value = cachedFrameworks.map(fw => ({ ...fw }))
        if (cachedSummary) {
          summary.value = { ...cachedSummary }
          allFrameworksSummary.value = { ...cachedSummary }
        }

        await checkSelectedFrameworkFromSession()

        if (selectedFrameworkId.value) {
          summary.value = {
            active_frameworks: 1,
            inactive_frameworks: 0,
            active_policies: 0,
            inactive_policies: 0
          }
        }

        return
      }
    }

    const params = {}
    if (selectedEntity.value) {
      params.entity = selectedEntity.value
    }

    const response = await axios.get(API_ENDPOINTS.FRAMEWORK_EXPLORER, { params })
    frameworks.value = response.data.frameworks || []
    summary.value = response.data.summary || {
      active_frameworks: 0,
      inactive_frameworks: 0,
      active_policies: 0,
      inactive_policies: 0
    }
    allFrameworksSummary.value = response.data.summary || {
      active_frameworks: 0,
      inactive_frameworks: 0,
      active_policies: 0,
      inactive_policies: 0
    }

    if (!hasFilters) {
      policyDataService.setFrameworkExplorerData(frameworks.value, summary.value)
    }

    await checkSelectedFrameworkFromSession()

    if (selectedFrameworkId.value) {
      summary.value = {
        active_frameworks: 1,
        inactive_frameworks: 0,
        active_policies: 0,
        inactive_policies: 0
      }
    }
  } catch (error) {
    console.error('Error fetching frameworks:', error)
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
  }
}
 
// Show framework details
const showFrameworkDetails = async (frameworkId) => {
  frameworkDetails.value = null
  showModal.value = true
  isLoadingDetails.value = true
 
  try {
    const response = await axios.get(API_ENDPOINTS.FRAMEWORK_DETAILS(frameworkId))
    frameworkDetails.value = response.data
  } catch (error) {
    console.error('Error fetching framework details:', error)
  } finally {
    isLoadingDetails.value = false
  }
}
 
// Close the modal
const closeModal = () => {
  showModal.value = false
}
 
// Filter frameworks by status
const filterByStatus = (status, type) => {
  // Check if we're clicking the same filter that's already active
  if (statusFilter.value === status && typeFilter.value === type) {
    // Clear the filter if it's already active
    clearFilter();
  } else {
    // Apply the new filter
    statusFilter.value = status;
    typeFilter.value = type;
    
    // Update active framework tab for visual indicator
    if (type === 'framework') {
      activeFrameworkTab.value = status;
    }
  }
}
 
// Clear all filters
const clearFilter = () => {
  statusFilter.value = null
  typeFilter.value = null
  selectedInternalExternal.value = ''
  selectedEntity.value = ''
  activeFrameworkTab.value = 'Active' // Reset to default
}
 
// Toggle framework expansion
const toggleFrameworkExpansion = async (frameworkId) => {
  const index = expandedFrameworks.value.indexOf(frameworkId)
  
  if (index > -1) {
    // Collapse
    expandedFrameworks.value.splice(index, 1)
  } else {
    // Expand
    expandedFrameworks.value.push(frameworkId)
    
    // Fetch versions if not already loaded
    const framework = frameworks.value.find(fw => fw.id === frameworkId)
    if (framework && (!framework.versions || framework.versions.length === 0)) {
      await fetchFrameworkVersions(frameworkId)
    }
  }
}

// Fetch framework versions
const fetchFrameworkVersions = async (frameworkId) => {
  isLoadingVersions.value[frameworkId] = true
  
  try {
    console.log(`Fetching framework versions for framework ID: ${frameworkId}`)
    const response = await axios.get(API_ENDPOINTS.POLICY_FRAMEWORK_VERSIONS(frameworkId))
    
    console.log('Framework versions response:', response.data)
    
    // Update the framework with versions data
    const framework = frameworks.value.find(fw => fw.id === frameworkId)
    if (framework) {
      framework.versions = response.data || []
    }
  } catch (err) {
    console.error('Error fetching framework versions:', err)
    
    // Initialize empty versions array to prevent UI errors
    const framework = frameworks.value.find(fw => fw.id === frameworkId)
    if (framework) {
      framework.versions = []
    }
  } finally {
    isLoadingVersions.value[frameworkId] = false
  }
}

// Toggle version expansion to show policies
const toggleVersionExpansion = async (versionId, frameworkId) => {
  const index = expandedVersions.value.indexOf(versionId)
  
  if (index > -1) {
    // Collapse
    expandedVersions.value.splice(index, 1)
  } else {
    // Expand
    expandedVersions.value.push(versionId)
    
    // Find the version and fetch policies if not already loaded
    const framework = frameworks.value.find(fw => fw.id === frameworkId)
    if (framework && framework.versions) {
      const version = framework.versions.find(v => v.id === versionId)
      if (version && (!version.policies || version.policies.length === 0)) {
        await fetchFrameworkVersionPolicies(versionId, frameworkId)
      }
    }
  }
}

// Fetch policies for a framework version
const fetchFrameworkVersionPolicies = async (versionId, frameworkId) => {
  isLoadingPolicies.value[versionId] = true
  
  try {
    console.log(`Fetching policies for framework version: ${versionId}`)
    const response = await axios.get(API_ENDPOINTS.POLICY_FRAMEWORK_VERSION_POLICIES(versionId))
    
    console.log(`Received ${response.data.length} policies for framework version ${versionId}`)
    
    // Update the version with policies data
    const framework = frameworks.value.find(fw => fw.id === frameworkId)
    if (framework && framework.versions) {
      const version = framework.versions.find(v => v.id === versionId)
      if (version) {
        version.policies = response.data || []
      }
    }
  } catch (err) {
    console.error('Error fetching framework version policies:', err)
    
    // Initialize empty policies array to prevent UI errors
    const framework = frameworks.value.find(fw => fw.id === frameworkId)
    if (framework && framework.versions) {
      const version = framework.versions.find(v => v.id === versionId)
      if (version) {
        version.policies = []
      }
    }
  } finally {
    isLoadingPolicies.value[versionId] = false
  }
}

// Status class helper
const statusClass = (status) => {
  if (!status) return ''
  const s = status.toLowerCase()
  if (s.includes('inactive')) return 'inactive'
  if (s.includes('active')) return 'active'
  if (s.includes('pending')) return 'pending'
  if (s.includes('approved')) return 'approved'
  if (s.includes('rejected')) return 'rejected'
  if (s.includes('under review')) return 'under-review'
  return ''
}

// Helper: treat both "Active" and "Approved" as active for toggle/label logic
const isPolicyActive = (policy) => {
  if (!policy || !policy.status) return false
  const s = policy.status.toLowerCase()
  return s.includes('active') || s.includes('approved')
}

// Helper: map workflow statuses like "Approved" to display label "Active"
const getPolicyStatusLabel = (policy) => {
  if (!policy || !policy.status) return ''
  const s = policy.status.toLowerCase()
  if (s.includes('approved')) return 'Active'
  return policy.status
}

// Toggle inline policy expansion to show its versions
const toggleInlinePolicyExpansion = async (policy) => {
  const index = expandedInlinePolicies.value.indexOf(policy.id)

  if (index > -1) {
    // Collapse
    expandedInlinePolicies.value.splice(index, 1)
    return
  }

  // Expand
  expandedInlinePolicies.value.push(policy.id)

  // Versions are already included in framework version policies payload,
  // so no extra fetch is required here.
}

// Toggle a specific policy version to show its subpolicies
const toggleInlinePolicyVersionExpansion = async (policyVersion, policy, frameworkVersionId, frameworkId) => {
  const versionId = policyVersion.id
  const index = expandedPolicyVersions.value.indexOf(versionId)

  if (index > -1) {
    // Collapse
    expandedPolicyVersions.value.splice(index, 1)
    return
  }

  // Expand
  expandedPolicyVersions.value.push(versionId)

  // Fetch subpolicies if not already loaded
  if (!policyVersion.subpolicies || policyVersion.subpolicies.length === 0) {
    await fetchPolicyVersionSubpolicies(versionId, policy.id, frameworkVersionId, frameworkId)
  }
}

// Fetch subpolicies for a specific policy version (inline view)
const fetchPolicyVersionSubpolicies = async (versionId, policyId, frameworkVersionId, frameworkId) => {
  inlineSubpoliciesLoading.value[versionId] = true

  try {
    console.log(`Fetching subpolicies for policy version ID: ${versionId}`)
    const response = await axios.get(API_ENDPOINTS.POLICY_VERSION_SUBPOLICIES(versionId))

    const raw = response.data || []
    const subpolicies = Array.isArray(raw)
      ? raw.map((sp) => ({
          id: sp.SubPolicyId ?? sp.id ?? sp.SubpolicyId ?? null,
          name: sp.SubPolicyName || sp.name || sp.Title || 'Untitled Subpolicy',
          category: sp.Category || sp.category || null,
          control: sp.Control,
          description: sp.Description || sp.description || '',
          status: sp.Status || sp.status || 'Under Review'
        }))
      : []

    // Update policy version within the frameworks structure
    const framework = frameworks.value.find((fw) => fw.id === frameworkId)
    if (framework && framework.versions) {
      const frameworkVersion = framework.versions.find((v) => v.id === frameworkVersionId)
      if (frameworkVersion && frameworkVersion.policies) {
        const policy = frameworkVersion.policies.find((p) => p.id === policyId)
        if (policy && policy.versions) {
          const version = policy.versions.find((pv) => pv.id === versionId)
          if (version) {
            version.subpolicies = subpolicies
          }
        }
      }
    }
  } catch (err) {
    console.error('Error fetching policy version subpolicies:', err)

    const framework = frameworks.value.find((fw) => fw.id === frameworkId)
    if (framework && framework.versions) {
      const frameworkVersion = framework.versions.find((v) => v.id === frameworkVersionId)
      if (frameworkVersion && frameworkVersion.policies) {
        const policy = frameworkVersion.policies.find((p) => p.id === policyId)
        if (policy && policy.versions) {
          const version = policy.versions.find((pv) => pv.id === versionId)
          if (version) {
            version.subpolicies = []
          }
        }
      }
    }
  } finally {
    inlineSubpoliciesLoading.value[versionId] = false
  }
}

// (Deprecated helper kept for compatibility elsewhere if re-used)

// Toggle policy status
const togglePolicyStatus = async (policy, versionId, frameworkId) => {
  if (policy.isProcessing) {
    console.log('Policy is already being processed, skipping duplicate request')
    return
  }
  
  policy.isProcessing = true
  
  try {
    const currentlyActive = isPolicyActive(policy)
    if (currentlyActive) {
      try {
        const response = await axios.get(API_ENDPOINTS.USERS_FOR_REVIEWER_SELECTION)
        const reviewers = response.data
        
        if (reviewers.length === 0) {
          PopupService.warning('No reviewers available. Please contact administrator.', 'No Reviewers')
          return
        }
        
        const reviewerOptions = reviewers.map(reviewer => ({
          value: reviewer.UserId,
          label: `${reviewer.UserName} (${reviewer.Email})`
        }))
        
        PopupService.select(
          'Select a reviewer for this policy deactivation request:',
          'Select Reviewer',
          reviewerOptions,
          async (selectedReviewerId) => {
            PopupService.comment(
              'Please provide a reason for deactivating this policy:',
              'Policy Deactivation Reason',
              async (reason) => {
                if (!reason || reason.trim() === '') {
                  PopupService.warning('Deactivation reason is required.', 'Missing Information')
                  return
                }
                
                try {
                  await axios.post(`/api/policies/${policy.id}/toggle-status/`, {
                    reason: reason.trim(),
                    ReviewerId: selectedReviewerId,
                    cascadeSubpolicies: true
                  })
                  
                  PopupService.success('Policy deactivation request submitted. Awaiting approval.', 'Request Submitted')
                  
                  // Refresh policies for this version
                  await fetchFrameworkVersionPolicies(versionId, frameworkId)
                } catch (error) {
                  console.error('Error submitting deactivation request:', error)
                  PopupService.error('Failed to submit deactivation request. Please try again.', 'Request Failed')
                } finally {
                  policy.isProcessing = false
                }
              }
            )
          }
        )
      } catch (error) {
        console.error('Error fetching reviewers:', error)
        PopupService.error('Failed to load reviewers. Please try again.', 'Load Error')
        policy.isProcessing = false
      }
    } else {
      const response = await axios.post(`/api/policies/${policy.id}/toggle-status/`, {
        cascadeSubpolicies: true
      })
      
      policy.status = response.data.status || 'Active'
      PopupService.success('Policy status change request submitted.', 'Status Update')
      
      // Refresh policies for this version
      await fetchFrameworkVersionPolicies(versionId, frameworkId)
      policy.isProcessing = false
    }
  } catch (error) {
    console.error('Error toggling policy status:', error)
    PopupService.error('Failed to update policy status. Please try again.', 'Update Failed')
    policy.isProcessing = false
  }
}

// Acknowledge policy - open modal to request acknowledgement (same behaviour as FrameworkPolicies)
const acknowledgePolicy = async (policy) => {
  selectedPolicyForAck.value = policy
  showAcknowledgementModal.value = true
}

// Handle acknowledgement request created
const handleAcknowledgementCreated = async (data) => {
  showAcknowledgementModal.value = false
  selectedPolicyForAck.value = null

  // Notify user (reusing generic push notification helper)
  try {
    await sendPushNotification({
      title: 'Acknowledgement Request Created',
      message: `Acknowledgement request created for "${data.policy_name || 'policy'}". ${data.total_users} users assigned.`,
      category: 'policy',
      priority: 'high',
      user_id: 'default_user'
    })
  } catch (e) {
    console.error('Error sending acknowledgement request notification:', e)
  }

  // Offer navigation to report page if an acknowledgement_request_id exists
  if (data.acknowledgement_request_id) {
    PopupService.confirm(
      `Acknowledgement request created successfully. ${data.total_users} users assigned.\n\nWould you like to view the report now?`,
      'Request Created',
      async () => {
        router.push({
          name: 'AcknowledgementReport',
          params: { requestId: data.acknowledgement_request_id }
        })
      },
      async () => {
        // No-op for now; inline list does not need a refresh
      }
    )
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
    const response = await axios.get(API_ENDPOINTS.GET_POLICY_ACKNOWLEDGEMENT_REQUESTS(policy.id))
    
    if (response.data.success && response.data.acknowledgement_requests && response.data.acknowledgement_requests.length > 0) {
      const latestRequest = response.data.acknowledgement_requests[0]
      router.push({
        name: 'AcknowledgementReport',
        params: { requestId: latestRequest.acknowledgement_request_id }
      })
    } else {
      PopupService.info('There are no reports for this policy.', 'No Reports Found')
    }
  } catch (error) {
    console.error('Error fetching acknowledgement requests:', error)
    PopupService.info('There are no reports for this policy.', 'No Reports Found')
  }
}

// Show policy details
const showPolicyDetails = (policyId, frameworkId) => {
  router.push({
    name: 'PolicyDetails',
    params: {
      policyId
    },
    query: {
      frameworkId: frameworkId
    }
  })
}

// Toggle framework status
const toggleStatus = async (fw) => {
  try {
    // Check if we're deactivating (Active -> Inactive)
    if (fw.status === 'Active') {
      // First fetch the list of available reviewers
      try {
        const reviewersResponse = await axios.get(API_ENDPOINTS.USERS_FOR_REVIEWER_SELECTION);
        const reviewers = reviewersResponse.data;
        
        if (reviewers.length === 0) {
          PopupService.warning('No reviewers available. Please contact an administrator.', 'No Reviewers');
          // Send push notification for no reviewers available
          sendPushNotification({
            title: 'No Reviewers Available',
            message: 'No reviewers available for framework deactivation. Please contact an administrator.',
            category: 'framework',
            priority: 'medium',
            user_id: 'default_user'
          });
          return;
        }
        
        // Create reviewer selection popup
        const reviewerOptions = reviewers.map(reviewer => ({
          value: reviewer.UserId,
          label: `${reviewer.UserName} (${reviewer.Email})`
        }));
        
        // Use popup service for reviewer selection and reason input
        PopupService.select(
          'Please select a reviewer for this framework deactivation request:',
          'Select Reviewer',
          reviewerOptions,
          async (selectedReviewerId) => {
            console.log('DEBUG: Selected reviewer ID:', selectedReviewerId, 'Type:', typeof selectedReviewerId);
            if (!selectedReviewerId) {
              PopupService.warning('Reviewer selection is required.', 'Missing Information');
              // Send push notification for missing reviewer selection
              sendPushNotification({
                title: 'Reviewer Selection Required',
                message: 'Reviewer selection is required for framework deactivation.',
                category: 'framework',
                priority: 'medium',
                user_id: 'default_user'
              });
              return;
            }
            
            // Now ask for the reason
            PopupService.comment(
              'Please provide a reason for deactivating this framework:',
              'Framework Deactivation',
              async (reason) => {
                console.log('DEBUG: Reason provided:', reason);
                if (!reason || reason.trim() === '') {
                  PopupService.warning('Deactivation reason is required.', 'Missing Information');
                  // Send push notification for missing reason
                  sendPushNotification({
                    title: 'Deactivation Reason Required',
                    message: 'Deactivation reason is required for framework deactivation.',
                    category: 'framework',
                    priority: 'medium',
                    user_id: 'default_user'
                  });
                  return;
                }
                
                try {
                  // Get current user ID from session or localStorage
                  const currentUserId = sessionStorage.getItem('user_id') || localStorage.getItem('user_id') || 1;
                  
                  console.log('DEBUG: Sending API request with data:', {
                    reason: reason.trim(),
                    cascadeToApproved: true,
                    ReviewerId: selectedReviewerId,
                    UserId: currentUserId
                  });
                  
                  // Call the API to request status change approval
                  const response = await axios.post(API_ENDPOINTS.FRAMEWORK_REQUEST_STATUS_CHANGE(fw.id), {
                    reason: reason.trim(),
                    cascadeToApproved: true,
                    ReviewerId: selectedReviewerId,
                    UserId: currentUserId // Use actual logged-in user ID
                  });
                  
                  console.log('DEBUG: API response:', response.data);
                  
                  // Show success message
                  PopupService.success('Framework deactivation request submitted. Awaiting approval.', 'Request Submitted');
                  
                  // Send push notification for successful deactivation request
                  sendPushNotification({
                    title: 'Framework Deactivation Request Submitted',
                    message: `Framework "${fw.name}" deactivation request submitted successfully. Awaiting approval.`,
                    category: 'framework',
                    priority: 'high',
                    user_id: 'default_user'
                  });
                  
                  // Refresh data to reflect the new 'Under Review' status
                  await fetchFrameworks();
                } catch (error) {
                  console.error('Error submitting deactivation request:', error);
                  console.error('Error response:', error.response?.data);
                  PopupService.error('Failed to submit deactivation request. Please try again.', 'Request Failed');
                  
                  // Send push notification for deactivation request failure
                  sendPushNotification({
                    title: 'Framework Deactivation Request Failed',
                    message: `Failed to submit deactivation request for framework "${fw.name}": ${error.response?.data?.error || error.message}`,
                    category: 'framework',
                    priority: 'high',
                    user_id: 'default_user'
                  });
                }
              }
            );
          }
        );
        
      } catch (error) {
        console.error('Error fetching reviewers:', error);
        PopupService.error('Failed to fetch reviewers. Please try again.', 'Error');
        
        // Send push notification for reviewer fetch failure
        sendPushNotification({
          title: 'Failed to Fetch Reviewers',
          message: `Failed to fetch reviewers for framework deactivation: ${error.response?.data?.error || error.message}`,
          category: 'framework',
          priority: 'high',
          user_id: 'default_user'
        });
        return;
      }
    } else {
      // For activation (Inactive -> Active), use the direct toggle endpoint
      const response = await axios.post(API_ENDPOINTS.FRAMEWORK_TOGGLE_STATUS(fw.id), {
        reason: 'Reactivating framework',
        cascadeToApproved: true
      });
     
      // Update local state
      fw.status = response.data.status || 'Active';
     
      // Show feedback to the user
      let message = `Framework status change request submitted.`;
     
      PopupService.success(message, 'Status Update');
      
      // Send push notification for successful activation
      sendPushNotification({
        title: 'Framework Activation Successful',
        message: `Framework "${fw.name}" has been successfully activated.`,
        category: 'framework',
        priority: 'high',
        user_id: 'default_user'
      });
     
      // Refresh summary counts
      await fetchFrameworks();
    }
  } catch (error) {
    console.error('Error toggling framework status:', error);
    PopupService.error('Failed to update framework status. Please try again.', 'Update Failed');
    
    // Send push notification for status toggle failure
    sendPushNotification({
      title: 'Framework Status Update Failed',
      message: `Failed to update framework "${fw.name}" status: ${error.response?.data?.error || error.message}`,
      category: 'framework',
      priority: 'high',
      user_id: 'default_user'
    });
  }
}
 
const filteredFrameworks = computed(() => {
  let result = frameworks.value;
 
  // Apply framework ID filter if selected
  if (selectedFrameworkId.value) {
    console.log('Filtering frameworks by ID:', selectedFrameworkId.value);
    result = result.filter(fw => fw.id === parseInt(selectedFrameworkId.value));
    return result;
  }
 
  // Apply Internal/External filter
  if (selectedInternalExternal.value) {
    result = result.filter(fw => fw.internalExternal === selectedInternalExternal.value);
  }

  // Entity filtering is handled by the backend API
  // The frameworks data is already filtered when selectedEntity changes
 
  // Apply status and type filters
  if (statusFilter.value && typeFilter.value) {
    if (typeFilter.value === 'framework') {
      // Filter frameworks by their status
      result = result.filter(fw => fw.status === statusFilter.value);
    } else if (typeFilter.value === 'policy') {
      // Filter frameworks that have active/inactive policies
      if (statusFilter.value === 'Active') {
        result = result.filter(fw => fw.active_policies_count > 0);
      } else {
        result = result.filter(fw => fw.inactive_policies_count > 0);
      }
    }
  }
 
  return result;
})
 
function goToPolicies(frameworkId) {
  // Set the selected framework ID to trigger the watch function
  selectedFrameworkId.value = frameworkId.toString();
  
  // Store the framework name in localStorage for use in the policies view
  localStorage.setItem('framework_name', frameworks.value.find(fw => fw.id === parseInt(frameworkId))?.name || '');
  
  const routeParams = { name: 'FrameworkPolicies', params: { frameworkId } }
  
  // If an entity filter is selected, pass it as a query parameter
  if (selectedEntity.value) {
    routeParams.query = { entity: selectedEntity.value }
  }
  
  router.push(routeParams)
}
 
// Watch for entity filter changes
watch(selectedEntity, () => {
  fetchFrameworks()
})

// Watch for changes to selectedFrameworkId and fetch policy counts
watch(selectedFrameworkId, async (newVal) => {
  console.log('selectedFrameworkId changed:', newVal);
  if (newVal) {
    // Save the selected framework to session
    try {
      const userId = localStorage.getItem('user_id') || 'default_user'
      console.log('🔍 DEBUG: Saving framework to session in FrameworkExplorer:', newVal)
      
      const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
        frameworkId: newVal,
        userId: userId
      })
      
      if (response.data && response.data.success) {
        console.log('✅ DEBUG: Framework saved to session successfully in FrameworkExplorer')
        console.log('🔑 DEBUG: Session key:', response.data.sessionKey)
      } else {
        console.error('❌ DEBUG: Failed to save framework to session in FrameworkExplorer')
      }
    } catch (error) {
      console.error('❌ DEBUG: Error saving framework to session in FrameworkExplorer:', error)
    }
    
    console.log('Framework selected:', newVal);
    // Update summary to reflect only the selected framework
    summary.value = {
      active_frameworks: 1,
      inactive_frameworks: 0,
      active_policies: 0,
      inactive_policies: 0
    }
  } else {
    console.log('No framework selected, reverting to all frameworks summary');
    // If no framework is selected (e.g., cleared), revert summary to show all frameworks
    summary.value = allFrameworksSummary.value
  }
});


// Fetch frameworks on component mount
onMounted(() => {
  fetchEntities()
  
  // Check if there's an entity filter from the route query parameters
  const entityFromRoute = useRoute().query.entity
  if (entityFromRoute) {
    selectedEntity.value = entityFromRoute
  }
  
  fetchFrameworks() // Fetch frameworks after setting entity filter
})

// Dropdown configs
const frameworkDropdownConfig = computed(() => {
  // Only show the user's stored framework in the dropdown if it exists
  const sessionFrameworkId = selectedFrameworkId.value;
  const sessionFramework = frameworks.value.find(f => f.id.toString() === sessionFrameworkId);
  
  // Create values array based on whether we have a stored framework
  let values = [];
  
  if (sessionFramework) {
    // If we have a stored framework, only show that one
    values = [
      { value: String(sessionFramework.id), label: sessionFramework.name }
    ];
  } else {
    // If no framework is selected, show all frameworks
    values = [
      { value: '', label: 'Select Framework' },
      ...frameworks.value.map(fw => ({ value: String(fw.id), label: fw.name }))
    ];
  }
  
  return {
    label: 'Framework',
    values: values
  };
})
const typeDropdownConfig = {
  label: 'Type',
  values: [
    { value: '', label: 'All Types' },
    { value: 'Internal', label: 'Internal' },
    { value: 'External', label: 'External' }
  ]
}
const entityDropdownConfig = computed(() => ({
  label: 'Entity',
  values: [
    { value: '', label: 'All Entities' },
    ...entities.value.map(entity => ({ value: String(entity.id), label: entity.label }))
  ]
}))
</script>
 
<style scoped>
.framework-explorer-container {
  padding: 54px 32px;
  margin-left: 245px;
  width: calc(100vw - 280px - 64px);
  box-sizing: border-box;
  position: relative;
  padding-top: 40px; /* Add more space for the heading to be visible */
}

/* Framework Details View Styles */
.framework-details-view {
  padding: 20px 0;
}

.details-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e8edfa;
}

/* Removed old .back-btn styling; using global .policy-dashboard-back-btn */

.details-header h2 {
  font-size: 2rem;
  font-weight: 700;
  color: #2c3e50;
  margin: 0;
}

.loading-state, .error-state {
  text-align: center;
  padding: 40px;
  font-size: 1.1rem;
  color: #64748b;
}

.loading-state i {
  margin-right: 10px;
  color: #4f6cff;
}

.error-state {
  color: #ef4444;
}

.details-content {
  background: white;
  border-radius: 12px;
  padding: 20px;
  max-width: 800px;
}

.detail-row {
  display: flex;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f1f5f9;
}

.detail-row:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.detail-label {
  font-weight: 600;
  color: #374151;
  font-size: 0.9rem;
  min-width: 160px;
  margin-right: 15px;
  text-align: left;
  align-self: flex-start;
}

.detail-value {
  color: #2c3e50;
  font-size: 0.9rem;
  flex: 1;
  text-align: left;
  display: block;
}

.doc-value {
  display: inline-block;
}

.doc-link {
  color: #4f6cff;
  text-decoration: none;
  font-weight: 600;
  padding: 6px 12px;
  background: #f0f4ff;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.doc-link:hover {
  background: #e0e7ff;
  transform: translateY(-2px);
  box-shadow: 0 3px 8px rgba(79, 108, 255, 0.15);
}
h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 8px 0;
  letter-spacing: -1px;
  text-align: left;
  margin-bottom: 0;
  margin-top: 0;
}
.page-header-underline {
  width: 90px;
  height: 3px;
  border-radius: 3px;
  background: linear-gradient(90deg, #3b82f6 0%, #6366f1 100%);
  margin-top: 8px;
  margin-bottom: 32px;
  margin-left: 0;
  margin-right: auto;
}
.export-controls {
  position: absolute;
  top: 60px;
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
  min-width: 120px !important;
  height: 42px !important;
  border-radius: 8px !important;
  border: 2px solid #e2e8f0 !important;
  font-size: 0.85rem !important;
  padding: 0 32px 0 10px !important;
  background: #fff !important;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16' fill='none'%3E%3Cpath d='M4 6L8 10L12 6' stroke='%234b5563' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") !important;
  background-repeat: no-repeat !important;
  background-position: right 10px center !important;
  background-size: 14px !important;
  color: #222 !important;
  appearance: none !important;
  -webkit-appearance: none !important;
  -moz-appearance: none !important;
  cursor: pointer !important;
}
/* CSS Variables */
:root {
  --primary-color: #7c8ff3;
  --success-color: #4ade80;
}

.export-btn {
  padding: 10px 16px;
  border-radius: 8px;
  border: 1px solid #3f77e7;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  background: white;
  color: var(--success-color);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.export-btn i {
  margin-right: 6px;
}

.export-btn:disabled,
.export-btn.exporting {
  opacity: 0.7;
  cursor: not-allowed;
  background: #f3f4f6;
}

.export-btn.exporting {
  color: var(--primary-color);
}

.export-btn.exporting i.fa-spinner {
  animation: spin 1s linear infinite;
}

/* Export success animation */
.export-btn.success {
  background: var(--success-color);
  color: white;
  animation: exportSuccess 0.6s ease-in-out;
}

/* Export button hover effects */
.export-btn:not(:disabled):hover {
  background: rgba(74, 222, 128, 0.1);
  border-color: var(--success-color);
  transform: translateY(-2px);
}

.export-btn:not(:disabled):active {
  transform: translateY(0);
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes exportSuccess {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}
/* Summary Section */
.summary-section {
  margin-top: 32px;
  margin-bottom: 32px;
  border: none;
  border-top: none;
  border-bottom: none;
}

.summary-section-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 20px 0;
  text-align: left;
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
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 0;
  padding: 12px 16px;
  font-size: 0.9rem;
  font-weight: 600;
  text-align: center;
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

.summary-card.active-framework {
  background: white !important;
  border-bottom: 3px solid #4f6cff !important;
  border-radius: 0;
}


.summary-card.active-policy {
  background: linear-gradient(135deg, #e6f7ff 60%, #f2f2f7 100%);
}
.summary-card.inactive-policy {
  background: linear-gradient(135deg, #fffbe6 60%, #f2f2f7 100%);
}
.summary-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  text-align: center;
  padding: 8px 0;
  gap: 4px;
}
.summary-icon-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 0;
}
.summary-label {
  font-size: 0.7rem !important;
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
  font-size: 0.9rem;
  font-weight: 300;
  margin-top: 0;
  color: #222;
  text-shadow: none;
  width: 100%;
  text-align: left !important;
  margin-left: 0 !important;
  padding-left: 0 !important;
  align-self: flex-start !important;
}
.summary-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  font-size: 1.6rem;
  transition: all 0.3s ease;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}
.active-framework .summary-icon-wrapper {
  background: #e8f7ee;
  color: #22a722;
}
.active-policy .summary-icon-wrapper {
  background: #e6f7ff;
  color: #4f6cff;
}
.inactive-policy .summary-icon-wrapper {
  background: #fff5e6;
  color: #f5a623;
}
.summary-value {
  display: block;
  font-size: 1.2rem;
  font-weight: 700;
  margin-top: 0;
  color: #222;
  width: 100%;
  text-align: left !important;
  margin-left: 0 !important;
  padding-left: 0 !important;
  align-self: flex-start !important;
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
  position: relative;
  margin-top: 40px;
  z-index: 10;
}
.framework-dropdown-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 0;
  position: relative;
  z-index: 1000;
}

.internal-external-dropdown-section,
.entity-dropdown-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 0;
  position: relative;
  z-index: 100;
}
.framework-dropdown,
.internal-external-dropdown,
.entity-dropdown {
  width:50px;
  min-width: 50px;
  height: 28px;
  border-radius: 8px;
  border: 1.5px solid #e2e8f0;
  font-size: 0.85rem;
  padding: 0 10px;
  background: #ffffff !important;
  cursor: pointer;
  transition: border-color 0.2s ease;
}

/* Target the actual dropdown button */
.framework-dropdown-section :deep(.filter-btn),
.internal-external-dropdown-section :deep(.filter-btn),
.entity-dropdown-section :deep(.filter-btn) {
  background: #ffffff !important;
  box-shadow: none !important;
}

.framework-dropdown-section :deep(.filter-btn:hover),
.internal-external-dropdown-section :deep(.filter-btn:hover),
.entity-dropdown-section :deep(.filter-btn:hover) {
  background: #ffffff !important;
  box-shadow: none !important;
}
.framework-dropdown:hover,
.internal-external-dropdown:hover,
.entity-dropdown:hover {
  border-color: #4f6cff;
}
.framework-dropdown:focus,
.internal-external-dropdown:focus,
.entity-dropdown:focus {
  outline: none;
  border-color: #4f6cff;
  
}

/* Ensure dropdown options appear on top */
.framework-dropdown-section :deep(.dropdown-options) {
  z-index: 9999 !important;
  position: absolute;
}

.internal-external-dropdown-section :deep(.dropdown-options),
.entity-dropdown-section :deep(.dropdown-options) {
  z-index: 1000 !important;
  position: absolute;
}

.framework-dropdown-section :deep(.dropdown-menu) {
  z-index: 9999 !important;
}

.internal-external-dropdown-section :deep(.dropdown-menu),
.entity-dropdown-section :deep(.dropdown-menu) {
  z-index: 1000 !important;
}

/* Tab Controls */
.tab-controls {
  display: flex;
  align-items: center;
  gap: 0;
  margin-left: 0;
  border-bottom: none;
  position: absolute;
  left: 0;
  top: 0;
}

/* Ensure Entity dropdown text wraps properly */
.entity-dropdown-section :deep(.dropdown-option),
.entity-dropdown-section :deep(.dropdown-item) {
  white-space: normal !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  max-width: 300px !important;
  padding: 8px 12px !important;
  line-height: 1.4 !important;
  font-size: 0.85rem !important;
  font-weight: 400 !important;
}

/* Remove bold from Type dropdown */
.internal-external-dropdown-section :deep(.dropdown-option),
.internal-external-dropdown-section :deep(.dropdown-item) {
  font-weight: 400 !important;
}

/* Remove bold from Framework dropdown */
.framework-dropdown-section :deep(.dropdown-option),
.framework-dropdown-section :deep(.dropdown-item) {
  font-weight: 400 !important;
}

.tab-btn {
  padding: 10px 30px;
  border: none;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 1rem;
  font-weight: 500;
  position: relative;
  border-bottom: none;
  text-align: center;
}




.framework-policy-summary-section {
  background: #f8faff;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 2px 10px rgba(79, 108, 255, 0.08);
  border: 1px solid #e8edfa;
}

.framework-policy-summary-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 15px 0;
  text-align: left;
}

.framework-policy-summary-cards {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 20px;
  margin-bottom: 0;
  flex-wrap: nowrap;
  width: 100%;
  max-width: 500px;
  margin: 0;
}

.framework-policy-summary-cards .summary-card {
  flex: 1;
  min-width: 200px;
  max-width: 240px;
  cursor: default;
}

/* Framework List Styles */
.framework-list-container {
  width: 100%;
  margin-top: 20px;
  background: #fff;
  border-radius: 5px;
  overflow: hidden;
  border: 1px solid #e8edfa;
}

.framework-list-header {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1fr 2.5fr 1.2fr 1.2fr;
  gap: 20px;
  padding: 15px 24px;
  background: rgb(245, 250, 250);
  border-bottom: 2px solid #e8edfa;
  font-weight: 700;
  font-size: 0.85rem;
  color: #000000;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.framework-list-header .framework-name {
  font-size: inherit !important;
  font-weight: inherit !important;
  min-width: auto !important;
  max-width: none !important;
  white-space: nowrap !important;
  margin-top: -2px!important;
  margin-left: -125px;
}

.list-header-item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  color: #000000;
}

.list-header-item:last-child {
  justify-content: center;
}

.framework-list {
  background: #fff;
}

.framework-list-item {
  border-bottom: 1px solid #f1f5f9;
  transition: all 0.2s ease;
  cursor: pointer;
}

.framework-list-item:hover {
  background: #f8fafc;
}

.framework-list-item:last-child {
  border-bottom: none;
}

/* Expandable Row Styles */
.framework-expandable-row {
  background: #ffffff;
  border-bottom: 1px solid #f1f5f9;
}

.expandable-content {
  background: transparent;
  border-top: 1px solid #f0f0f0;
  padding: 0;
  margin-top: 0;
  border-radius: 0;
}

.expandable-header {
  padding: 16px 24px;
  background: transparent;
  border-bottom: 1px solid #f0f0f0;
  margin: 0;
}

.expandable-header h4 {
  margin: 0 0 8px 0;
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
}

.hierarchy-breadcrumb {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 8px;
}

.hierarchy-item {
  font-size: 14px;
  color: #6b7280;
}

.hierarchy-item.active {
  color: #3b82f6;
  font-weight: 600;
}

.versions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
  padding: 0 24px 16px 24px;
}

.version-item {
  background: transparent;
  border: none;
  border-bottom: 1px solid #f0f0f0;
  border-radius: 0;
  overflow: hidden;
  transition: all 0.2s ease;
}

.version-item:hover {
  background-color: #f9f9f9;
}

.version-item:last-child {
  border-bottom: none;
}

.version-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: transparent;
  border-bottom: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.version-header:hover {
  background: #f0f4ff;
  border-radius: 6px;
}

.version-main-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.version-name {
  font-weight: 600;
  color: #1f2937;
  font-size: 14px;
}

.version-description {
  color: #6b7280;
  font-size: 12px;
  line-height: 1.3;
  margin: 0;
  font-weight: 400;
}

.version-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.version-status {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 4px;
}

.version-status::before {
  content: '';
  display: inline-block;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  box-shadow: 0 0 1px rgba(0, 0, 0, 0.2);
}

.version-status.active {
  color: #059669;
}

.version-status.active::before {
  background: #059669;
}

.version-status.inactive {
  color: #dc2626;
}

.version-status.inactive::before {
  background: #dc2626;
}

.version-status.pending {
  color: #d97706;
}

.version-status.pending::before {
  background: #d97706;
}

.version-status.approved {
  color: #059669 !important;
  font-weight: 700;
}

.version-status.approved::before {
  background: #059669 !important;
}

.version-status.rejected {
  color: #dc2626 !important;
  font-weight: 700;
}

.version-status.rejected::before {
  background: #dc2626 !important;
}

.version-status.under-review {
  color: #d97706 !important;
  font-weight: 700;
}

.version-status.under-review::before {
  background: #d97706 !important;
}

.previous-version {
  font-style: italic;
  color: #059669;
  background: #d1fae5;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
}

.loading-message {
  text-align: center;
  padding: 20px;
  color: #6b7280;
  font-size: 14px;
}

.no-data-message {
  text-align: center;
  padding: 20px;
  color: #6b7280;
  font-size: 14px;
  font-style: italic;
}

.expand-arrow {
  color: #6b7280;
  font-size: 16px;
  transition: all 0.2s ease;
  cursor: pointer;
  margin-right: 8px;
}

.expand-arrow:hover {
  color: #374151;
  transform: scale(1.1);
}

/* Version Policies Styles - Matching FrameworkPolicies */
.version-policies {
  padding: 0;
  background: transparent;
  border-top: 1px solid #e5e7eb;
  margin-top: 0;
}

.version-policies-container {
  width: 100%;
  background: #fff;
  border-radius: 0;
  overflow: hidden;
  border: none;
}

.version-policies-container .policy-list-header {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1fr 2.5fr 1.2fr 1.5fr;
  gap: 20px;
  padding: 15px 24px;
  background: rgb(245, 250, 250);
  border-bottom: 2px solid #e8edfa;
  font-weight: 700;
  font-size: 0.85rem;
  color: #000000;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.version-policies-container .policy-list-header .list-header-item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  color: #000000;
}

.version-policies-container .policy-list-header .list-header-item:last-child {
  justify-content: center;
}

.version-policies-container .policy-list {
  background: #fff;
}

.version-policies-container .policy-list-item {
  border-bottom: 1px solid #f1f5f9;
  transition: all 0.2s ease;
}

.version-policies-container .policy-list-item:last-child {
  border-bottom: none;
}

.version-policies-container .list-item-content {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1fr 2.5fr 1.2fr 1.5fr;
  gap: 20px;
  padding: 20px 24px;
  align-items: center;
}

.version-policies-container .policy-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.version-policies-container .policy-name-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.version-policies-container .policy-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #2c3e50;
  line-height: 1.2;
}

.version-policies-container .policy-id {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 500;
}

.version-policies-container .policy-category-cell {
  display: flex;
  align-items: center;
}

.version-policies-container .category-text {
  font-size: 0.85rem;
  font-weight: 500;
  color: #374151;
}

.version-policies-container .policy-type-cell {
  display: flex;
  align-items: center;
}

.version-policies-container .type-text {
  font-size: 0.85rem;
  font-weight: 500;
  color: #374151;
  text-transform: capitalize;
}

.version-policies-container .policy-description-cell {
  display: flex;
  align-items: center;
}

.version-policies-container .description-text {
  font-size: 0.85rem;
  color: #64748b;
  line-height: 1.4;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.version-policies-container .policy-status-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.version-policies-container .status-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.version-policies-container .policy-actions-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.version-policies-container .list-action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.version-policies-container .acknowledge-btn-list {
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
}

.version-policies-container .acknowledge-btn-list:hover {
  background: #3a57e8;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 108, 255, 0.3);
}

.version-policies-container .view-reports-btn-list {
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

.version-policies-container .view-reports-btn-list:hover {
  background: #4f6cff;
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 108, 255, 0.3);
}

.version-policies-container .action-btn {
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

.version-policies-container .action-btn:hover {
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(79, 108, 255, 0.2);
}

/* Inline Subpolicies Styles */
.inline-subpolicies-row {
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.inline-subpolicies-container {
  padding: 12px 24px 16px 24px;
}

.inline-policy-versions-row {
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.inline-policy-versions-container {
  padding: 12px 24px 16px 24px;
}

.inline-policy-versions-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.inline-policy-version-item {
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.inline-policy-version-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
}

.inline-policy-version-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #111827;
}

.inline-policy-version-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.inline-subpolicies-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.inline-subpolicy-item {
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  padding: 10px 12px;
}

.inline-subpolicy-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.inline-subpolicy-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: #111827;
}

.inline-subpolicy-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.inline-subpolicy-category {
  font-size: 0.8rem;
  color: #4b5563;
}

.inline-subpolicy-status {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.inline-subpolicy-description {
  margin-top: 6px;
  font-size: 0.8rem;
  color: #6b7280;
  line-height: 1.4;
}

.list-item-content {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1fr 2.5fr 1.2fr 1.2fr;
  gap: 20px;
  padding: 20px 24px;
  align-items: center;
}

.framework-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.framework-icon {
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

.framework-name-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.framework-title {
  font-size: 0.8rem;
  font-weight: 0;
  color: #2c3e50;
  line-height: 1.2;
}

.framework-id {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 500;
}

.framework-category-cell {
  display: flex;
  align-items: center;
}

.category-badge {
  background: linear-gradient(135deg, #e8edfa 0%, #d0d9f7 100%);
  color: #4f6cff;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  border: 1px solid #c7d0f0;
}

.framework-type-cell {
  display: flex;
  align-items: center;
}

.type-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: capitalize;
}

.type-badge.type-internal {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  color: #059669;
  border: 1px solid #6ee7b7;
}

.type-badge.type-external {
  background: linear-gradient(135deg, #fecaca 0%, #fca5a5 100%);
  color: #dc2626;
  border: 1px solid #f87171;
}

/* New text styles for category and type */
.category-text {
  font-size: 0.85rem;
  font-weight: 500;
  color: #374151;
}

.type-text {
  font-size: 0.85rem;
  font-weight: 500;
  color: #374151;
  text-transform: capitalize;
}

.framework-description-cell {
  display: flex;
  align-items: center;
}

.description-text {
  font-size: 0.85rem;
  color: #64748b;
  line-height: 1.4;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.framework-status-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.framework-actions-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-size: 0.8rem;
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

/* Framework Cards Styles */
.framework-cards-container {
  width: 100%;
  margin-top: 20px;
}

.framework-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
  padding: 0;
}

.framework-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(79, 108, 255, 0.08);
  border: 1px solid #e8edfa;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}


.framework-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.framework-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #e8edfa 0%, #d0d9f7 100%);
  border-radius: 12px;
  color: #4f6cff;
  font-size: 1.3rem;
  box-shadow: 0 4px 12px rgba(79, 108, 255, 0.2);
}

.framework-card-status {
  display: flex;
  align-items: center;
}

.framework-card-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.framework-card-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #2c3e50;
  margin: 0;
  line-height: 1.3;
}

.framework-card-id {
  font-size: 0.85rem;
  color: #64748b;
  margin: 0;
  font-weight: 500;
}

.framework-card-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 8px 0;
}

.framework-card-description {
  font-size: 0.95rem;
  color: #64748b;
  line-height: 1.5;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex-grow: 1;
}

.framework-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

.status-indicator {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-indicator.active {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  color: #059669;
  border: 1px solid #6ee7b7;
}

.status-indicator.inactive {
  background: linear-gradient(135deg, #fecaca 0%, #fca5a5 100%);
  color: #dc2626;
  border: 1px solid #f87171;
}

.card-details-btn {
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
  background: linear-gradient(135deg, #f0f4ff 0%, #e0e7ff 100%);
  color: #4f6cff;
  border: 1px solid #c7d0f0;
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
  font-size: 0.75rem;
}
.switch-label.active {
  color: #22a722;
}
.switch-label.inactive {
  color: #e53935;
}

/* Responsive Grid Adjustments */
@media (max-width: 1400px) {
  .framework-list-header,
  .list-item-content {
    grid-template-columns: 1.8fr 1fr 0.8fr 2fr 1fr 1fr;
    gap: 16px;
  }
  
  .framework-cards-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
  }
}

@media (max-width: 1200px) {
  .framework-list-header,
  .list-item-content {
    grid-template-columns: 2fr 1fr 0.8fr 1.5fr 1fr 1fr;
    gap: 12px;
  }
  
  .framework-list-container {
    margin-left: -20px;
    margin-right: -20px;
    border-radius: 0;
  }
  
  .framework-cards-grid {
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 16px;
  }
}

@media (max-width: 768px) {
  .framework-list-header {
    display: none;
  }
  
  .list-item-content {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
  }
  
  .framework-name-cell,
  .framework-category-cell,
  .framework-type-cell,
  .framework-description-cell,
  .framework-status-cell,
  .framework-actions-cell {
    width: 100%;
    justify-content: flex-start;
  }
  
  .framework-list-item:hover {
    transform: none;
    box-shadow: none;
  }
  
  .framework-cards-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .tab-controls {
    margin-left: 0;
    margin-top: 10px;
  }
  
  .top-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
}
 
/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal-content {
  position: relative;
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
  padding: 20px 30px;
  border-bottom: 1px solid #eee;
}
.modal-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.6rem;
  font-weight: 700;
}
.modal-close-btn {
  position: absolute;
  top: 15px;
  right: 20px;
  font-size: 2.2rem;
  font-weight: bold;
  color: #666;
  cursor: pointer;
  transition: color 0.2s;
  background: transparent;
  border: none;
  padding: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}
.modal-close-btn:hover {
  color: #e53935;
}
.modal-body {
  padding: 25px 30px;
}
.modal-loading, .modal-error {
  padding: 30px;
  text-align: center;
  color: #666;
  font-size: 1.1rem;
}
.detail-row {
  margin-bottom: 18px;
  display: flex;
  flex-wrap: wrap;
}
.detail-label {
  font-weight: 600;
  width: 160px;
  color: #444;
  font-size: 1rem;
  position: relative;
  padding-right: 12px;
}
.detail-label::after {
  content: ":";
  position: absolute;
  right: 4px;
}
.detail-value {
  flex: 1;
  min-width: 200px;
  font-size: 1rem;
  color: #2c3e50;
  font-weight: 500;
  text-align: left;
}
.doc-link {
  color: #4f6cff;
  text-decoration: none;
  font-weight: 600;
  display: inline-block;
  padding: 6px 12px;
  background: #f0f4ff;
  border-radius: 6px;
  transition: all 0.2s ease;
  font-size: 0.95rem;
}
.doc-link:hover {
  text-decoration: none;
  background: #e0e7ff;
  transform: translateY(-2px);
  box-shadow: 0 3px 8px rgba(79,108,255,0.15);
}
.framework-details {
  margin-top: 10px;
  background: #fcfcff;
  border-radius: 8px;
  padding: 15px;
}
.simple-modal {
  background: #fff !important;
  border-radius: 16px;
  box-shadow: 0 5px 30px rgba(0,0,0,0.10);
  padding: 28px 32px 24px 32px;
  max-width: 600px !important;
  width: 100%;
  position: relative;
  min-height: 500px !important;
  display: flex;
  flex-direction: column;
}
.simple-modal-header {
  margin-bottom: 32px;
  padding: 0;
}
.simple-modal-header h2 {
  font-size: 1.8rem;
  font-weight: 700;
  color: #222;
  margin: 0;
  text-align: left;
}
.simple-close {
  position: absolute;
  top: 24px;
  right: 32px;
  font-size: 2rem;
  color: #888;
  background: none;
  border: none;
  cursor: pointer;
  z-index: 2;
  padding: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}
.simple-close:hover {
  color: #e53935;
}
.simple-modal-body {
  padding: 0;
}
.simple-framework-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 0;
}
.simple-detail-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: flex-start;
  gap: 32px;
  margin-bottom: 0;
}
.simple-detail-label {
  font-weight: 700;
  color: #222;
  font-size: 0.9rem;
  min-width: 180px;
  letter-spacing: -0.5px;
  margin-bottom: 0;
}
.simple-detail-value {
  font-size: 0.9rem;
  color: #444;
  font-weight: 400;
  margin-bottom: 0;
  word-break: break-word;
  flex: 1;
  margin-left: 0;
  text-align: left;
  display: block;
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
}
</style>