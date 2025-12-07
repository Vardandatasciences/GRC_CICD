<template>
  <div class="policy-tabs-container single-container" id="policy-container">
    <!-- Page Header -->
    <div class="page-header">
      <h1>All Policies</h1>
    </div>

    <!-- RBAC Loading Indicator -->
    <!-- <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner">
        <i class="fas fa-circle-notch fa-spin"></i>
        <span>Loading...</span>
      </div>
    </div> -->

    <!-- Error Message -->
    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-circle"></i>
      <span>{{ error }}</span>
    </div>

    <!-- Modern Pill Toggle Tabs: Only show on first page (framework selection) -->
    <div v-if="!selectedFramework" class="pill-tabs-bar">
      <button class="pill-tab" :class="{active: activeTab==='framework'}" @click="navigateToTab('framework')">
        <span v-if="activeTab==='framework'" class="pill-dot"></span>
        Compliance Frameworks
      </button>
      <button class="pill-tab" :class="{active: activeTab==='policies'}" @click="navigateToTab('policies')">
        <span v-if="activeTab==='policies'" class="pill-dot"></span>
        Policies
      </button>
      <button class="pill-tab" :class="{active: activeTab==='subpolicies'}" @click="navigateToTab('subpolicies')">
        <span v-if="activeTab==='subpolicies'" class="pill-dot"></span>
        Subpolicies
      </button>
    </div>

    <!-- Breadcrumb chips for navigation context -->
    <div class="breadcrumbs" v-if="breadcrumbs.length">
      <TransitionGroup name="breadcrumb">
        <span v-for="(crumb, idx) in breadcrumbs" 
              :key="crumb.id" 
              class="breadcrumb-chip">
          {{ crumb.name }}
          <span class="breadcrumb-close" @click.stop="resetNavigation(idx)">×</span>
        </span>
      </TransitionGroup>
    </div>

    <!-- Framework selection step (tab toggle) -->
    <template v-if="!selectedFramework">
      <template v-if="activeTab==='framework'">
        <div class="framework-page-desc">
          <!-- <h2>Select the framework you are interested, and we will display Subpolicies and Policies.</h2> -->
        </div>
        <div style="display: flex; flex-direction: column; align-items: flex-start; justify-content: flex-start; max-width:260px; margin:0 0 8px 0;">
          <div class="dropdown-with-info">
            <CustomDropdown
              v-model="frameworkDropdown"
              :config="{
                label: 'Framework',
                options: frameworks.map(fw => ({ label: fw.name, value: fw.id }))
              }"
              :showSearchBar="true"
              @change="handleFrameworkSelection"
            />
            <span class="info-icon" title="Select a framework to view its policies and subpolicies">🛈</span>
          </div>
        </div>
        <!-- Framework heading removed -->

      <table class="table-view">
        <thead>
          <tr>
            <th>Name</th>
            <th>Category</th>
            <th>Status</th>
            <th>Description</th>
            <th><i class="fas fa-chevron-down"></i></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="fw in filteredFrameworks" :key="fw.id">
            <tr @click="toggleFrameworkExpansion(fw.id)" class="table-row-clickable">
            <td>{{ fw.name }}</td>
            <td>{{ fw.category }}</td>
            <td>
              <span class="table-status-badge" :class="statusClass(fw.status)">
                {{ fw.status }}
              </span>
            </td>
            <td>{{ fw.description }}</td>
            <td>
                <i :class="expandedFrameworks.includes(fw.id) ? 'fas fa-chevron-up' : 'fas fa-chevron-down'" class="expand-arrow"></i>
              </td>
            </tr>
            <!-- Expandable Row -->
            <tr v-if="expandedFrameworks.includes(fw.id)" class="expandable-row">
              <td colspan="5" class="expandable-cell">
                <div class="expandable-content">
                  <div class="expandable-header">
                    <h4>Framework Versions</h4>
                    <div class="hierarchy-breadcrumb">
                      <span class="hierarchy-item active">{{ fw.name }}</span>
                    </div>
                  </div>
                  <div v-if="fw.versions && fw.versions.length > 0" class="versions-list">
                                            <div v-for="version in fw.versions" :key="version.id" class="version-item">
                        <div class="version-header" @click="toggleFrameworkVersionExpansion(version.id)">
                          <div class="version-main-info">
                            <span class="version-name">{{ version.name }}</span>
                            <span class="version-description">{{ version.description }}</span>
                          </div>
                          <div class="version-info">
                            <span v-if="version.previous_version_name" class="previous-version">Previous: {{ version.previous_version_name }}</span>
                            <span class="version-status" :class="statusClass(version.status)">{{ version.status }}</span>
                            <i :class="expandedFrameworkVersions.includes(version.id) ? 'fas fa-chevron-up' : 'fas fa-chevron-down'" class="expand-arrow"></i>
                          </div>
                        </div>
                      
                      <!-- Framework Version Policies -->
                      <div v-if="expandedFrameworkVersions.includes(version.id)" class="drill-down-item indent-level-1">
                        <div v-if="version.policies && version.policies.length > 0">
                          <div v-for="policy in version.policies" :key="policy.id" class="drill-down-item">
                            <div class="version-header" @click="togglePolicyInVersionExpansion(policy.id)">
                              <div class="version-main-info">
                                <span class="version-name">{{ policy.name }}</span>
                                <span class="version-description">{{ policy.description }}</span>
                              </div>
                              <div class="version-info">
                                <span class="table-status-badge" :class="statusClass(policy.status)">{{ policy.status }}</span>
                                <i :class="expandedPoliciesInVersion.includes(policy.id) ? 'fas fa-chevron-up' : 'fas fa-chevron-down'" class="expand-arrow"></i>
                              </div>
                            </div>
                            
                            <!-- Policy Versions -->
                            <div v-if="expandedPoliciesInVersion.includes(policy.id)" class="drill-down-item indent-level-2">
                              <div v-if="policy.versions && policy.versions.length > 0">
                                <div v-for="policyVersion in policy.versions" :key="policyVersion.id" class="drill-down-item">
                                  <div class="version-header" @click="togglePolicyVersionExpansion(policyVersion.id)">
                                    <div class="version-main-info">
                                      <span class="version-name">{{ policyVersion.name }}</span>
                                      <span class="version-description">{{ policyVersion.description }}</span>
                                    </div>
                                    <div class="version-info">
                                      <span v-if="policyVersion.previous_version_name" class="previous-version">Previous: {{ policyVersion.previous_version_name }}</span>
                                      <span class="table-status-badge" :class="statusClass(policyVersion.status)">{{ policyVersion.status }}</span>
                                      <i :class="expandedPolicyVersions.includes(policyVersion.id) ? 'fas fa-chevron-up' : 'fas fa-chevron-down'" class="expand-arrow"></i>
                                    </div>
                                  </div>
                                  
                                  <!-- Subpolicies -->
                                  <div v-if="expandedPolicyVersions.includes(policyVersion.id)" class="drill-down-item indent-level-3">
                                    <div v-if="policyVersion.subpolicies && policyVersion.subpolicies.length > 0">
                                      <div v-for="subpolicy in policyVersion.subpolicies" :key="subpolicy.id" class="drill-down-item">
                                        <div class="version-header">
                                          <div class="version-main-info">
                                            <span class="version-name">{{ subpolicy.name }}</span>
                                            <span class="version-description">{{ subpolicy.description }}</span>
                                          </div>
                                          <div class="version-info">
                                            <span class="table-status-badge" :class="statusClass(subpolicy.status)">{{ subpolicy.status }}</span>
                                          </div>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </td>
            </tr>
            </template>
          </tbody>
        </table>
      </template>
    
    <!-- Policies Tab Content -->
    <template v-else-if="activeTab==='policies'">
      <div class="framework-select-container">
        <div class="framework-select-wrapper">
          
          <CustomDropdown
            v-model="selectedPolicyFramework"
            :config="{
              label: 'Framework',
              options: selectedPolicyFramework ? frameworks.filter(fw => fw.id == selectedPolicyFramework).map(fw => ({ label: fw.name, value: fw.id })) : frameworks.map(fw => ({ label: fw.name, value: fw.id }))
            }"
            :showSearchBar="true"
          />
        </div>
      </div>

      <table class="table-view">
        <thead>
          <tr>
            <th>Name</th>
            <th>Category</th>
            <th>Status</th>
            <th>Versions</th>
            <th>Description</th>
            <th><i class="fas fa-chevron-down"></i></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="policy in filteredPolicies" :key="policy.id">
            <tr @click="togglePolicyExpansion(policy.id)" class="table-row-clickable">
            <td>{{ policy.name }}</td>
            <td>{{ policy.category }}</td>
            <td>
              <span class="table-status-badge" :class="statusClass(policy.status)">
                {{ policy.status }}
              </span>
            </td>
            <td>
              <div class="table-version-tags">
                <span v-for="version in policy.versions" :key="version.id" class="table-version-tag">
                  {{ version.name }}
                </span>
              </div>
            </td>
            <td>{{ policy.description }}</td>
              <td>
                <i :class="expandedPolicies.includes(policy.id) ? 'fas fa-chevron-up' : 'fas fa-chevron-down'" class="expand-arrow"></i>
              </td>
          </tr>
            <!-- Expandable Row -->
            <tr v-if="expandedPolicies.includes(policy.id)" class="expandable-row">
              <td colspan="6" class="expandable-cell">
                <div class="expandable-content">
                  <div class="expandable-header">
                    <h4>Sub-Policies</h4>
                  </div>
                  <div v-if="policy.subpolicies && policy.subpolicies.length > 0">
                    <table class="nested-table">
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Status</th>
                          <th>Control</th>
                          <th>Description</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="subpolicy in policy.subpolicies" :key="subpolicy.id" class="table-row-clickable">
                          <td>{{ subpolicy.name }}</td>
                          <td>
                            <span class="table-status-badge" :class="statusClass(subpolicy.status)">
                              {{ subpolicy.status }}
                            </span>
                          </td>
                          <td>{{ subpolicy.control || 'N/A' }}</td>
                          <td>{{ subpolicy.description }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div v-else-if="policy.subpolicies && policy.subpolicies.length === 0" class="no-data-message">
                    <p>No sub-policies found for this policy.</p>
                  </div>
                  <div v-else class="loading-message">
                    <p>Loading sub-policies...</p>
                  </div>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </template>

    <!-- Subpolicies Tab Content -->
    <template v-else-if="activeTab==='subpolicies'">
      <div class="framework-select-container">
        <div class="framework-select-wrapper">
          <CustomDropdown
            v-model="selectedSubpolicyFramework"
            :config="{
              label: 'Framework',
              options: selectedSubpolicyFramework ? frameworks.filter(fw => fw.id == selectedSubpolicyFramework).map(fw => ({ label: fw.name, value: fw.id })) : frameworks.map(fw => ({ label: fw.name, value: fw.id }))
            }"
            :showSearchBar="true"
          />
        </div>
      </div>

      <table class="table-view">
        <thead>
          <tr>
            <th>Name</th>
            <th>Category</th>
            <th>Status</th>
            <th>Description</th>
            <th><i class="fas fa-chevron-down"></i></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="subpolicy in filteredSubpolicies" :key="subpolicy.id">
            <tr @click="toggleSubpolicyExpansion(subpolicy.id)" class="table-row-clickable">
            <td>{{ subpolicy.name }}</td>
            <td>{{ subpolicy.category }}</td>
            <td>
              <span class="table-status-badge" :class="statusClass(subpolicy.status)">
                {{ subpolicy.status }}
              </span>
            </td>
            <td>{{ subpolicy.description }}</td>
              <td>
                <i :class="expandedSubpolicies.includes(subpolicy.id) ? 'fas fa-chevron-up' : 'fas fa-chevron-down'" class="expand-arrow"></i>
              </td>
          </tr>
            <!-- Expandable Row -->
            <tr v-if="expandedSubpolicies.includes(subpolicy.id)" class="expandable-row">
              <td colspan="5" class="expandable-cell">
                <div class="expandable-content">
                  <div class="expandable-header">
                    <h4>Subpolicy Details</h4>
                  </div>
                  <table class="nested-table">
                    <tbody>
                      <tr>
                        <td><strong>Name:</strong></td>
                        <td>{{ subpolicy.name }}</td>
                      </tr>
                      <tr>
                        <td><strong>Category:</strong></td>
                        <td>{{ subpolicy.category }}</td>
                      </tr>
                      <tr>
                        <td><strong>Status:</strong></td>
                        <td>
                          <span class="table-status-badge" :class="statusClass(subpolicy.status)">
                            {{ subpolicy.status }}
                          </span>
                        </td>
                      </tr>
                      <tr>
                        <td><strong>Description:</strong></td>
                        <td>{{ subpolicy.description }}</td>
                      </tr>
                      <tr v-if="subpolicy.created_date">
                        <td><strong>Created:</strong></td>
                        <td>{{ formatDate(subpolicy.created_date) }}</td>
                      </tr>
                      <tr v-if="subpolicy.created_by">
                        <td><strong>Created By:</strong></td>
                        <td>{{ subpolicy.created_by }}</td>
                      </tr>
                      <tr>
                        <!-- <td><strong>Actions:</strong></td>
                        <td>
                          <button class="view-details-btn" @click.stop="selectSubpolicy(subpolicy)">
                            <i class="fas fa-eye"></i>
                            View Full Details
                          </button>
                        </td> -->
                      </tr>
                    </tbody>
                  </table>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </template>
    </template>

    <!-- Framework versions step (after framework selection, before policies) -->
    <template v-if="selectedFramework && !selectedFrameworkVersion">
      <!-- Versions heading removed -->

      <table class="table-view">
        <thead>
          <tr>
            <th>Name</th>
            <th>Category</th>
            <th>Status</th>
            <th></th>
            <th>Previous Version</th>
            <th>Description</th>
            <th><i class="fas fa-chevron-down"></i></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="version in selectedFramework.versions" :key="version.id" @click="selectFrameworkVersion(version)" class="table-row-clickable">
            <td>{{ version.name }}</td>
            <td>{{ version.category }}</td>
            <td>
              <span class="table-status-badge" :class="statusClass(version.status)">
                {{ version.status }}
              </span>
            </td>
            <td>-</td>
            <td>{{ version.previous_version_name || 'N/A' }}</td>
            <td>{{ version.description }}</td>
            <td>
              <i class="fas fa-chevron-down expand-arrow"></i>
            </td>
          </tr>
        </tbody>
      </table>
    </template>

    <!-- Policies in framework version step -->
    <template v-else-if="selectedFramework && selectedFrameworkVersion && !selectedPolicy">
      <!-- Policies heading removed -->

      <table class="table-view">
        <thead>
          <tr>
            <th>Name</th>
            <th>Category</th>
            <th>Status</th>
            <th>Versions</th>
            <th>Description</th>
            <th><i class="fas fa-chevron-down"></i></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="policy in selectedFrameworkVersion.policies" :key="policy.id" @click="selectPolicy(policy)" class="table-row-clickable">
            <td>{{ policy.name }}</td>
            <td>{{ policy.category }}</td>
            <td>
              <span class="table-status-badge" :class="statusClass(policy.status)">
                {{ policy.status }}
              </span>
            </td>
            <td>{{ policy.version_count || (policy.versions ? policy.versions.length : 0) }}</td>
            <td>{{ policy.description }}</td>
            <td>
              <i class="fas fa-chevron-down expand-arrow"></i>
            </td>
          </tr>
        </tbody>
      </table>
    </template>

    <!-- Policy versions step (after policy selection) -->
    <template v-else-if="selectedFramework && selectedFrameworkVersion && selectedPolicy && !selectedPolicyVersion">
      <!-- Policy Versions heading removed -->

      <table class="table-view">
        <thead>
          <tr>
            <th>Name</th>
            <th>Category</th>
            <th>Status</th>
            <th>Subpolicy Count</th>
            <th>Previous Version</th>
            <th>Description</th>
            <th><i class="fas fa-chevron-down"></i></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="version in selectedPolicy.versions" :key="version.id">
            <tr @click="toggleVersionExpansion(version.id)" class="table-row-clickable">
            <td>{{ version.name }}</td>
            <td>{{ version.category }}</td>
            <td>
              <span class="table-status-badge" :class="statusClass(version.status)">
                {{ version.status }}
              </span>
            </td>
            <td>-</td>
            <td>{{ version.previous_version_name || 'N/A' }}</td>
            <td>{{ version.description }}</td>
            <td>
                <i :class="expandedVersions.includes(version.id) ? 'fas fa-chevron-up' : 'fas fa-chevron-down'" class="expand-arrow"></i>
            </td>
          </tr>
            <!-- Expandable Row -->
            <tr v-if="expandedVersions.includes(version.id)" class="expandable-row">
              <td colspan="7" class="expandable-cell">
                <div class="expandable-content">
                  <div class="expandable-header">
                    <h4>Version Subpolicies</h4>
                  </div>
                  <div v-if="version.subpolicies && version.subpolicies.length > 0">
                    <table class="nested-table">
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Category</th>
                          <th>Status</th>
                          <th>Description</th>
                          <th>Created</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="subpolicy in version.subpolicies" :key="subpolicy.id" class="table-row-clickable">
                          <td>{{ subpolicy.name }}</td>
                          <td>{{ subpolicy.category }}</td>
                          <td>
                            <span class="table-status-badge" :class="statusClass(subpolicy.status)">
                              {{ subpolicy.status }}
                            </span>
                          </td>
                          <td>{{ subpolicy.description }}</td>
                          <td>{{ subpolicy.created_date ? formatDate(subpolicy.created_date) : 'N/A' }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </template>

    <!-- Policy version step: show subpolicies -->
    <template v-else-if="selectedFramework && selectedFrameworkVersion && selectedPolicy && selectedPolicyVersion">
      <!-- Subpolicies heading removed -->

      <div v-if="selectedPolicyVersion.subpolicies && selectedPolicyVersion.subpolicies.length > 0" class="versions-list">
        <div v-for="subpolicy in selectedPolicyVersion.subpolicies" :key="subpolicy.id" class="version-item">
          <div class="version-header">
            <div class="version-main-info">
              <span class="version-name">{{ subpolicy.name }}</span>
              <span class="version-description">{{ subpolicy.description }}</span>
            </div>
            <div class="version-info">
              <span class="table-status-badge" :class="statusClass(subpolicy.status)">{{ subpolicy.status }}</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="no-data-message">
        <p>No subpolicies found for {{ selectedPolicyVersion.name }}</p>
      </div>
    </template>


  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import axios from 'axios'
import CustomDropdown from '../CustomDropdown.vue'
import policyDataService from '@/services/policyService'
// Remove RBAC import
// import { usePolicyRbac } from '@/mixins/policyRbacMixin'

// Remove RBAC logic and permission checks
// const {
//   canViewPolicies,
//   rbacLoading,
//   rbacError,
//   initializeRBAC,
// } = usePolicyRbac()

const activeTab = ref('framework')
const selectedFramework = ref(null)
const selectedFrameworkVersion = ref(null)
const selectedPolicy = ref(null)
const selectedPolicyVersion = ref(null)
const frameworkDropdown = ref('')
const selectedPolicyFramework = ref('')
const selectedSubpolicyFramework = ref('')

const loading = ref(false)
const policiesLoading = ref(false)
const error = ref(null)
const subpoliciesCache = ref({ lastFetched: null, data: null, frameworkFilter: null })
const subpoliciesLoading = ref(false)

// Expandable state tracking
const expandedFrameworks = ref([])
const expandedPolicies = ref([])
const expandedSubpolicies = ref([])
const expandedVersions = ref([])
const expandedFrameworkVersions = ref([])
const expandedPoliciesInVersion = ref([])
const expandedPolicyVersions = ref([])
import {  API_BASE_URL, API_ENDPOINTS } from '../../config/api.js'
const API_BASE_URL_FULL = `${API_BASE_URL}/api`
const frameworks = ref([])
const policies = ref([])
const subpolicies = ref([])
const policiesCache = ref({ lastFetched: null, data: null, frameworkFilter: null })

// Fetch all frameworks from API
const fetchFrameworks = async () => {
  loading.value = true
  error.value = null

  try {
    console.log('🔍 [AllPolicies] Checking for cached policy frameworks...')

    if (!window.policyDataFetchPromise && !policyDataService.hasAllPoliciesFrameworksCache()) {
      console.log('🚀 [AllPolicies] Starting policy prefetch (user navigated directly)...')
      window.policyDataFetchPromise = policyDataService.fetchAllPolicyData()
    }

    if (window.policyDataFetchPromise) {
      console.log('⏳ [AllPolicies] Waiting for policy prefetch to complete...')
      try {
        await window.policyDataFetchPromise
        console.log('✅ [AllPolicies] Prefetch completed')
      } catch (prefetchError) {
        console.warn('⚠️ [AllPolicies] Prefetch failed, will fetch directly from API', prefetchError)
      }
    }

    if (policyDataService.hasAllPoliciesFrameworksCache()) {
      console.log('✅ [AllPolicies] Using cached policy frameworks data')
      const cachedFrameworks = policyDataService.getAllPoliciesFrameworks() || []
      frameworks.value = cachedFrameworks.map(fw => ({ ...fw }))

      await checkSelectedFrameworkFromSession()
      return
    }

    console.log('⚠️ [AllPolicies] No cached data found, fetching from API...')
    const response = await axios.get(`${API_BASE_URL_FULL}/all-policies/frameworks/`)
    frameworks.value = response.data || []

    // Update cache for subsequent loads
    policyDataService.setAllPoliciesFrameworks(frameworks.value)

    await checkSelectedFrameworkFromSession()
  } catch (err) {
    console.error('Error fetching frameworks:', err)
    error.value = 'Failed to load frameworks. Please try again.'
    frameworks.value = []
  } finally {
    loading.value = false
  }
}

// Check for selected framework from session and set it as default
const checkSelectedFrameworkFromSession = async () => {
  try {
    console.log('🔍 DEBUG: Checking for selected framework from session in AllPolicies...')
    const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
    console.log('📊 DEBUG: Selected framework response:', response.data)
    
    if (response.data && response.data.success) {
      // Check if a framework is selected (not null)
      if (response.data.frameworkId) {
      const sessionFrameworkId = response.data.frameworkId
      console.log('✅ DEBUG: Found selected framework in session:', sessionFrameworkId)
      
      // Check if this framework exists in our loaded frameworks
      const frameworkExists = frameworks.value.find(f => f.id == sessionFrameworkId)
      
      if (frameworkExists) {
        // Set the framework dropdown value
        frameworkDropdown.value = sessionFrameworkId
        selectedPolicyFramework.value = sessionFrameworkId
        selectedSubpolicyFramework.value = sessionFrameworkId
        
        console.log('✅ DEBUG: Set framework dropdowns from session:', sessionFrameworkId)
        
        // If in framework tab, also set the selected framework for navigation
        if (activeTab.value === 'framework') {
          selectedFramework.value = { ...frameworkExists }
          console.log('✅ DEBUG: Set selected framework for navigation')
        }
      } else {
        console.log('⚠️ DEBUG: Framework from session not found in loaded frameworks')
        }
      } else {
        // "All Frameworks" is selected (frameworkId is null)
        console.log('ℹ️ DEBUG: No framework selected in session (All Frameworks selected)')
        console.log('🌐 DEBUG: Clearing framework selection to show all frameworks')
        frameworkDropdown.value = null
        selectedPolicyFramework.value = null
        selectedSubpolicyFramework.value = null
        selectedFramework.value = null
      }
    } else {
      console.log('ℹ️ DEBUG: No framework found in session')
      frameworkDropdown.value = null
      selectedPolicyFramework.value = null
      selectedSubpolicyFramework.value = null
    }
  } catch (error) {
    console.error('❌ DEBUG: Error checking selected framework from session:', error)
    // Clear selection on error
    frameworkDropdown.value = null
    selectedPolicyFramework.value = null
    selectedSubpolicyFramework.value = null
  }
}

// Fetch framework versions
const fetchFrameworkVersions = async (frameworkId) => {
  loading.value = true
  error.value = null
  
  try {
    console.log(`Fetching framework versions for framework ID: ${frameworkId}`)
    const response = await axios.get(`${API_BASE_URL_FULL}/all-policies/frameworks/${frameworkId}/versions/`)
    
    console.log('Framework versions response:', response.data)
    
    // Initialize versions array if not present
    if (!selectedFramework.value.versions) {
      selectedFramework.value.versions = []
    }
    
    // Update the selected framework with the versions data
    selectedFramework.value.versions = response.data
    
    loading.value = false
  } catch (err) {
    console.error('Error fetching framework versions:', err)
    
    // Initialize empty versions array to prevent UI errors
    if (selectedFramework.value) {
      selectedFramework.value.versions = []
    }
    
    loading.value = false
  }
}

// Fetch policies for a specific framework version
const fetchFrameworkVersionPolicies = async (versionId) => {
  loading.value = true
  error.value = null
  
  try {
    console.log(`Fetching policies for framework version: ${versionId}`)
    const response = await axios.get(`${API_BASE_URL_FULL}/all-policies/framework-versions/${versionId}/policies/`)
    console.log(`Received ${response.data.length} policies for framework version ${versionId}`)
    
    // Update the policies in the framework's version object for hierarchical view
    frameworks.value.forEach(framework => {
      if (framework.versions) {
        const version = framework.versions.find(v => v.id === versionId)
        if (version) {
          version.policies = response.data
          console.log(`Updated policies for version ${version.name} in framework ${framework.name}`)
        }
      }
    })
    
    // Also update the selected framework version with the policies data (for backward compatibility)
    if (selectedFrameworkVersion.value && selectedFrameworkVersion.value.id === versionId) {
      selectedFrameworkVersion.value.policies = response.data
    }
    
    loading.value = false
  } catch (err) {
    console.error('Error fetching framework version policies:', err)
    loading.value = false
  }
}

// Fetch all policies for Policies tab with optimized performance
const fetchAllPolicies = async () => {
  policiesLoading.value = true
  error.value = null
  
  const currentFrameworkFilter = selectedPolicyFramework.value
  
  // Check if we have cached data for this filter and it's recent (less than 1 minute old)
  const now = Date.now()
  const cacheAge = policiesCache.value.lastFetched ? now - policiesCache.value.lastFetched : null
  const isCacheValid = policiesCache.value.data && 
                      cacheAge && 
                      cacheAge < 60000 && // Cache valid for 1 minute
                      policiesCache.value.frameworkFilter === currentFrameworkFilter
  
  if (isCacheValid) {
    console.log("Using cached policies data")
    policies.value = policiesCache.value.data
    policiesLoading.value = false
    return
  }
  
  console.log("Cache invalid, fetching fresh policy data")
  
  let url = `${API_BASE_URL_FULL}/all-policies/policies/`
  
  // Add framework filter if selected
  if (currentFrameworkFilter) {
    url += `?framework_id=${currentFrameworkFilter}`
  }
  
  try {
    console.log("Fetching all policies...")
    const response = await axios.get(url)
    
    // Show initial data immediately for better user experience
    const initialPolicies = response.data
    policies.value = initialPolicies.map(policy => ({
      ...policy,
      // Initialize with null version_count to show loading indicator
      version_count: policy.version_count
    }))
    
    // Check if the backend can provide versions count without needing additional API calls
    const hasVersionsInfo = initialPolicies.length > 0 && 
                          (initialPolicies[0].version_count !== undefined || 
                           (initialPolicies[0].versions && Array.isArray(initialPolicies[0].versions)))
    
    if (hasVersionsInfo) {
      // Backend already provides version info, no need for additional calls
      console.log("Backend already provides version info, using it directly")
      
      // Ensure all policies have version_count property
      const processedPolicies = initialPolicies.map(policy => ({
        ...policy,
        version_count: policy.version_count || (policy.versions ? policy.versions.length : 0)
      }))
      
      policies.value = processedPolicies
      
      // Update cache
      policiesCache.value = {
        lastFetched: now,
        data: processedPolicies,
        frameworkFilter: currentFrameworkFilter
      }
      
      policiesLoading.value = false
      return
    }
    
    // If we need version info, use a more efficient approach with Promise.all
    console.log("Fetching version info for policies in parallel")
    
    // Prepare all version fetch promises
    const versionFetchPromises = initialPolicies.map(policy => {
      return axios.get(`${API_BASE_URL_FULL}/all-policies/policies/${policy.id}/versions/`)
        .then(versionsResponse => {
          if (versionsResponse.data && Array.isArray(versionsResponse.data)) {
            return {
              ...policy,
              versions: versionsResponse.data,
              version_count: versionsResponse.data.length
            }
          }
          return policy
        })
        .catch(err => {
          console.error(`Error fetching versions for policy ${policy.id}:`, err)
          return policy
        })
    })
    
    // Wait for all promises to resolve in parallel
    const enhancedPolicies = await Promise.all(versionFetchPromises)
    
    policies.value = enhancedPolicies
    
    // Update cache
    policiesCache.value = {
      lastFetched: now,
      data: enhancedPolicies,
      frameworkFilter: currentFrameworkFilter
    }
    
    console.log(`Loaded ${enhancedPolicies.length} policies with complete version data`)
    
  } catch (err) {
    console.error('Error fetching policies:', err)
  } finally {
    policiesLoading.value = false
  }
}

// Fetch policy versions
const fetchPolicyVersions = async (policyId) => {
  loading.value = true
  error.value = null
  
  try {
    console.log(`Fetching policy versions for policy ID: ${policyId}`)
    
    // This is the most reliable endpoint to get ALL versions
    const response = await axios.get(`${API_BASE_URL_FULL}/all-policies/policies/${policyId}/versions/`)
    
    console.log('Policy versions response:', response.data)
    
    // Update policy versions in the hierarchical structure
    frameworks.value.forEach(framework => {
      if (framework.versions) {
        framework.versions.forEach(version => {
          if (version.policies) {
            const policy = version.policies.find(p => p.id === policyId)
            if (policy) {
              policy.versions = response.data
              policy.version_count = response.data.length
              console.log(`Updated versions for policy ${policy.name} in version ${version.name}`)
            }
          }
        })
      }
    })
    
    // Initialize versions array if not present
    if (!selectedPolicy.value.versions) {
      selectedPolicy.value.versions = []
    }
    
    // Update the selected policy with the versions data
    selectedPolicy.value.versions = response.data
    
    // Also update the versions count in the display
    if (selectedPolicy.value && response.data.length > 0) {
      // Update the versions count property to match actual number of versions
      selectedPolicy.value.version_count = response.data.length
    }
    
    loading.value = false
  } catch (err) {
    console.error('Error fetching policy versions:', err)
    
    // Initialize empty versions array to prevent UI errors
    if (selectedPolicy.value) {
      selectedPolicy.value.versions = []
    }
    
    loading.value = false
  }
}

// Fetch all subpolicies for Subpolicies tab
const fetchAllSubpolicies = async () => {
  subpoliciesLoading.value = true
  error.value = null
  
  const currentFrameworkFilter = selectedSubpolicyFramework.value
  
  // Check if we have cached data for this filter and it's recent (less than 1 minute old)
  const now = Date.now()
  const cacheAge = subpoliciesCache.value.lastFetched ? now - subpoliciesCache.value.lastFetched : null
  const isCacheValid = subpoliciesCache.value.data && 
                      cacheAge && 
                      cacheAge < 60000 && // Cache valid for 1 minute
                      subpoliciesCache.value.frameworkFilter === currentFrameworkFilter
  
  if (isCacheValid) {
    console.log("Using cached subpolicies data")
    subpolicies.value = subpoliciesCache.value.data
    subpoliciesLoading.value = false
    return
  }
  
  console.log("Cache invalid, fetching fresh subpolicies data")
  
  let url = `${API_BASE_URL_FULL}/all-policies/subpolicies/`
  
  // Add framework filter if selected
  if (currentFrameworkFilter) {
    url += `?framework_id=${currentFrameworkFilter}`
  }
  
  try {
    console.log(`Fetching subpolicies from: ${url}`)
    const response = await axios.get(url)
    console.log(`Received ${response.data.length} subpolicies`)
    
    // For debugging
    if (response.data.length > 0) {
      console.log('Sample subpolicy:', response.data[0])
    }
    
    const subpolicyData = response.data
    
    // Update the subpolicies with the data
    subpolicies.value = subpolicyData
    
    // Update cache
    subpoliciesCache.value = {
      lastFetched: now,
      data: subpolicyData,
      frameworkFilter: currentFrameworkFilter
    }
    
    console.log(`Successfully loaded ${subpolicyData.length} subpolicies`)
  } catch (err) {
    console.error('Error fetching subpolicies:', err)
    
    // Initialize empty array if error occurs
    subpolicies.value = []
  } finally {
    subpoliciesLoading.value = false
  }
}

// Fetch subpolicies for a specific policy version
const fetchPolicyVersionSubpolicies = async (versionId) => {
  loading.value = true
  
  try {
    console.log(`Fetching subpolicies for policy version ID: ${versionId}`)
    const response = await axios.get(`${API_BASE_URL_FULL}/all-policies/policy-versions/${versionId}/subpolicies/`)
    
    console.log('Subpolicies response:', response.data)
    
    // Update subpolicies in the hierarchical structure
    frameworks.value.forEach(framework => {
      if (framework.versions) {
        framework.versions.forEach(fwVersion => {
          if (fwVersion.policies) {
            fwVersion.policies.forEach(policy => {
              if (policy.versions) {
                const policyVersion = policy.versions.find(pv => pv.id === versionId)
                if (policyVersion) {
                  policyVersion.subpolicies = response.data
                  policyVersion.subpolicy_count = response.data.length
                  console.log(`Updated subpolicies for policy version ${policyVersion.name}`)
                }
              }
            })
          }
        })
      }
    })
    
    // Initialize subpolicies array if not present
    if (selectedPolicyVersion.value && !selectedPolicyVersion.value.subpolicies) {
      selectedPolicyVersion.value.subpolicies = []
    }
    
    // Update the selected policy version with the subpolicies data
    if (selectedPolicyVersion.value) {
      selectedPolicyVersion.value.subpolicies = response.data
    }
    
    loading.value = false
  } catch (err) {
    console.error('Error fetching policy version subpolicies:', err)
    
    // Initialize empty subpolicies array to prevent UI errors
    if (selectedPolicyVersion.value) {
      selectedPolicyVersion.value.subpolicies = []
    }
    
    loading.value = false
  }
}

// Event handlers for selection changes

const selectFrameworkVersion = (version) => {
  selectedFrameworkVersion.value = version
  selectedPolicy.value = null
  selectedPolicyVersion.value = null
  
  // Fetch policies for this framework version
  fetchFrameworkVersionPolicies(version.id)
}

const selectPolicy = (policy) => {
  selectedPolicy.value = policy
  selectedPolicyVersion.value = null
  
  // Fetch policy versions
  fetchPolicyVersions(policy.id)
}



// const selectSubpolicy = (subpolicy) => {
//   console.log('Subpolicy selected:', subpolicy)
//   // For now, just show details - extend this based on your requirements
//   showDetails(subpolicy)
// }

// Toggle methods for expandable functionality
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

const togglePolicyExpansion = async (policyId) => {
  const index = expandedPolicies.value.indexOf(policyId)
  
  if (index > -1) {
    // Collapse
    expandedPolicies.value.splice(index, 1)
  } else {
    // Expand
    expandedPolicies.value.push(policyId)
    
    // Fetch subpolicies if not already loaded
    const policy = policies.value.find(p => p.id === policyId)
    if (policy && (!policy.subpolicies || policy.subpolicies.length === 0)) {
      await fetchPolicySubpolicies(policyId)
    }
  }
}

const toggleSubpolicyExpansion = async (subpolicyId) => {
  const index = expandedSubpolicies.value.indexOf(subpolicyId)
  
  if (index > -1) {
    // Collapse
    expandedSubpolicies.value.splice(index, 1)
  } else {
    // Expand
    expandedSubpolicies.value.push(subpolicyId)
  }
}

const toggleVersionExpansion = async (versionId) => {
  const index = expandedVersions.value.indexOf(versionId)
  
  if (index > -1) {
    // Collapse
    expandedVersions.value.splice(index, 1)
  } else {
    // Expand
    expandedVersions.value.push(versionId)
    
    // Fetch subpolicies if not already loaded
    const version = selectedPolicy.value?.versions?.find(v => v.id === versionId)
    if (version && (!version.subpolicies || version.subpolicies.length === 0)) {
      await fetchPolicyVersionSubpolicies(versionId)
    }
  }
}

const toggleFrameworkVersionExpansion = async (versionId) => {
  const index = expandedFrameworkVersions.value.indexOf(versionId)
  
  if (index > -1) {
    // Collapse
    expandedFrameworkVersions.value.splice(index, 1)
  } else {
    // Expand
    expandedFrameworkVersions.value.push(versionId)
    
    // Find the framework version in the hierarchical structure and fetch policies if not already loaded
    let versionFound = false
    for (const framework of frameworks.value) {
      if (framework.versions) {
        const version = framework.versions.find(v => v.id === versionId)
        if (version && (!version.policies || version.policies.length === 0)) {
          console.log(`Fetching policies for framework version ${version.name} in framework ${framework.name}`)
          await fetchFrameworkVersionPolicies(versionId)
          versionFound = true
          break
        }
      }
      if (versionFound) break
    }
  }
}

const togglePolicyInVersionExpansion = async (policyId) => {
  const index = expandedPoliciesInVersion.value.indexOf(policyId)
  
  if (index > -1) {
    // Collapse
    expandedPoliciesInVersion.value.splice(index, 1)
  } else {
    // Expand
    expandedPoliciesInVersion.value.push(policyId)
    
    // Find the policy in the hierarchical structure and fetch versions if not already loaded
    let policyFound = false
    for (const framework of frameworks.value) {
      if (framework.versions) {
        for (const version of framework.versions) {
          if (version.policies) {
            const policy = version.policies.find(p => p.id === policyId)
            if (policy && (!policy.versions || policy.versions.length === 0)) {
              console.log(`Fetching versions for policy ${policy.name} in framework ${framework.name}, version ${version.name}`)
              await fetchPolicyVersions(policyId)
              policyFound = true
              break
            }
          }
        }
        if (policyFound) break
      }
    }
  }
}

const togglePolicyVersionExpansion = async (policyVersionId) => {
  const index = expandedPolicyVersions.value.indexOf(policyVersionId)
  
  if (index > -1) {
    // Collapse
    expandedPolicyVersions.value.splice(index, 1)
  } else {
    // Expand
    expandedPolicyVersions.value.push(policyVersionId)
    
    // Find the policy version in the hierarchical structure and fetch subpolicies if not already loaded
    let versionFound = false
    for (const framework of frameworks.value) {
      if (framework.versions) {
        for (const fwVersion of framework.versions) {
          if (fwVersion.policies) {
            for (const policy of fwVersion.policies) {
              if (policy.versions) {
                const policyVersion = policy.versions.find(pv => pv.id === policyVersionId)
                if (policyVersion && (!policyVersion.subpolicies || policyVersion.subpolicies.length === 0)) {
                  console.log(`Fetching subpolicies for policy version ${policyVersion.name} in policy ${policy.name}`)
                  await fetchPolicyVersionSubpolicies(policyVersionId)
                  versionFound = true
                  break
                }
              }
            }
            if (versionFound) break
          }
        }
        if (versionFound) break
      }
    }
  }
}

// Navigation function for the navigation headings
const navigateToTab = async (tabName) => {
  console.log(`🔍 DEBUG: Navigating to ${tabName} tab`)
  
  // Set the active tab
  activeTab.value = tabName
  
  // Clear error message when switching tabs
  error.value = null
  
  // Check if we have a stored framework in session
  try {
    const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
    
    if (response.data && response.data.success && response.data.frameworkId) {
      const sessionFrameworkId = response.data.frameworkId
      console.log(`✅ DEBUG: Found stored framework ${sessionFrameworkId} for ${tabName} tab`)
      
      // Set the framework dropdown values based on the stored framework
      if (tabName === 'policies') {
        selectedPolicyFramework.value = sessionFrameworkId
        console.log('✅ DEBUG: Set selectedPolicyFramework from session')
        await fetchAllPolicies()
      } else if (tabName === 'subpolicies') {
        selectedSubpolicyFramework.value = sessionFrameworkId
        console.log('✅ DEBUG: Set selectedSubpolicyFramework from session')
        await fetchAllSubpolicies()
      } else if (tabName === 'framework') {
        frameworkDropdown.value = sessionFrameworkId
        console.log('✅ DEBUG: Set frameworkDropdown from session')
        // Load the framework for navigation
        const fw = frameworks.value.find(f => f.id == sessionFrameworkId)
        if (fw) {
          selectedFramework.value = { ...fw }
          await fetchFrameworkVersions(fw.id)
        }
      }
    } else {
      console.log(`ℹ️ DEBUG: No stored framework found, loading default data for ${tabName} tab`)
      // No stored framework, load default data
      if (tabName === 'policies') {
        await fetchAllPolicies()
      } else if (tabName === 'subpolicies') {
        await fetchAllSubpolicies()
      }
    }
  } catch (error) {
    console.error(`❌ DEBUG: Error navigating to ${tabName} tab:`, error)
    // Fallback to default behavior
    if (tabName === 'policies') {
      await fetchAllPolicies()
    } else if (tabName === 'subpolicies') {
      await fetchAllSubpolicies()
    }
  }
}

// Watch for tab changes to load relevant data
const handleTabChange = () => {
  // Clear error message when switching tabs
  error.value = null;
  
  if (activeTab.value === 'policies') {
    console.log('Switching to Policies tab, fetching all policies...');
    fetchAllPolicies();
  } else if (activeTab.value === 'subpolicies') {
    console.log('Switching to Subpolicies tab, fetching all subpolicies...');
    fetchAllSubpolicies();
  } else if (activeTab.value === 'framework') {
    console.log('Switching to Frameworks tab');
    // Frameworks are already loaded on component mount
  }
}

// Watch for framework filter changes in policies tab
const handlePolicyFrameworkChange = async () => {
  // Save the selected framework to session
  if (selectedPolicyFramework.value) {
    try {
      const userId = localStorage.getItem('user_id') || 'default_user'
      console.log('🔍 DEBUG: Saving policy framework to session in AllPolicies:', selectedPolicyFramework.value)
      
      const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
        frameworkId: selectedPolicyFramework.value,
        userId: userId
      })
      
      if (response.data && response.data.success) {
        console.log('✅ DEBUG: Policy framework saved to session successfully')
      } else {
        console.error('❌ DEBUG: Failed to save policy framework to session')
      }
    } catch (error) {
      console.error('❌ DEBUG: Error saving policy framework to session:', error)
    }
  }
  
  fetchAllPolicies()
}

// Watch for framework filter changes in subpolicies tab
const handleSubpolicyFrameworkChange = async () => {
  // Save the selected framework to session
  if (selectedSubpolicyFramework.value) {
    try {
      const userId = localStorage.getItem('user_id') || 'default_user'
      console.log('🔍 DEBUG: Saving subpolicy framework to session in AllPolicies:', selectedSubpolicyFramework.value)
      
      const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
        frameworkId: selectedSubpolicyFramework.value,
        userId: userId
      })
      
      if (response.data && response.data.success) {
        console.log('✅ DEBUG: Subpolicy framework saved to session successfully')
      } else {
        console.error('❌ DEBUG: Failed to save subpolicy framework to session')
      }
    } catch (error) {
      console.error('❌ DEBUG: Error saving subpolicy framework to session:', error)
    }
  }
  
  fetchAllSubpolicies()
}

// Add a simple, direct selection method for the framework dropdown
const handleFrameworkSelection = async () => {
  try {
    if (!frameworkDropdown.value) {
      // If no framework is selected, reset the state
      selectedFramework.value = null
      selectedFrameworkVersion.value = null
      selectedPolicy.value = null
      selectedPolicyVersion.value = null
      return
    }

    // Find the selected framework
    const fwId = String(frameworkDropdown.value)
    console.log(`Selecting framework ID: ${fwId}`)
    
    const fw = frameworks.value.find(f => String(f.id) === fwId)
    if (fw) {
      console.log(`Found framework: ${fw.name}`)
      
      // Save the selected framework to session
      try {
        const userId = localStorage.getItem('user_id') || 'default_user'
        console.log('🔍 DEBUG: Saving framework to session in AllPolicies:', fwId)
        
        const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
          frameworkId: fwId,
          userId: userId
        })
        
        if (response.data && response.data.success) {
          console.log('✅ DEBUG: Framework saved to session successfully in AllPolicies')
          console.log('🔑 DEBUG: Session key:', response.data.sessionKey)
        } else {
          console.error('❌ DEBUG: Failed to save framework to session in AllPolicies')
        }
      } catch (error) {
        console.error('❌ DEBUG: Error saving framework to session in AllPolicies:', error)
      }
      
      // Wait for the next tick to avoid reactivity issues
      await nextTick()
      
      // Set the selected framework
      selectedFramework.value = { ...fw }  // Use spread operator to create a new object
      
      // Reset other selections
      selectedFrameworkVersion.value = null
      selectedPolicy.value = null
      selectedPolicyVersion.value = null
      
      // Fetch versions
      fetchFrameworkVersions(fw.id)
    } else {
      console.error(`No framework found with ID: ${fwId}`)
    }
  } catch (err) {
    console.error('Error in framework selection:', err)
  }
}



// Fetch subpolicies for a specific policy
const fetchPolicySubpolicies = async (policyId) => {
  loading.value = true
  
  try {
    console.log(`Fetching subpolicies for policy ID: ${policyId}`)
    const response = await axios.get(`${API_BASE_URL_FULL}/all-policies/subpolicies/?policy_id=${policyId}`)
    
    console.log('Policy subpolicies response:', response.data)
    
    // Update subpolicies in the policies list
    const policyIndex = policies.value.findIndex(p => p.id === policyId)
    if (policyIndex !== -1) {
      policies.value[policyIndex].subpolicies = response.data
      policies.value[policyIndex].subpolicy_count = response.data.length
      console.log(`Updated subpolicies for policy ${policies.value[policyIndex].name}`)
    }
    
    loading.value = false
  } catch (err) {
    console.error('Error fetching policy subpolicies:', err)
    
    // Initialize empty subpolicies array to prevent UI errors
    const policyIndex = policies.value.findIndex(p => p.id === policyId)
    if (policyIndex !== -1) {
      policies.value[policyIndex].subpolicies = []
    }
    
    loading.value = false
  }
}



// Reset navigation to previous level
const resetNavigation = (idx) => {
  // Always go back to the previous filter (one step back)
  switch(idx) {
    case 0:
      // If first breadcrumb, reset everything
      selectedFramework.value = null;
      selectedFrameworkVersion.value = null;
      selectedPolicy.value = null;
      selectedPolicyVersion.value = null;
      frameworkDropdown.value = '';
      activeTab.value = 'framework';
      break;
    case 1:
      selectedFrameworkVersion.value = null;
      selectedPolicy.value = null;
      selectedPolicyVersion.value = null;
      break;
    case 2:
      selectedPolicy.value = null;
      selectedPolicyVersion.value = null;
      break;
    case 3:
      selectedPolicyVersion.value = null;
      break;
    default:
      // fallback: reset all
      selectedFramework.value = null;
      selectedFrameworkVersion.value = null;
      selectedPolicy.value = null;
      selectedPolicyVersion.value = null;
      frameworkDropdown.value = '';
      activeTab.value = 'framework';
      break;
  }
}

// Utility functions
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

// Icon mapping for categories
// const categoryIcon = (category) => {
//   switch ((category || '').toLowerCase()) {
//     case 'governance': return 'fas fa-shield-alt';
//     case 'access control': return 'fas fa-user-shield';
//     case 'asset management': return 'fas fa-boxes';
//     case 'cryptography': return 'fas fa-key';
//     case 'data management': return 'fas fa-database';
//     case 'device management': return 'fas fa-mobile-alt';
//     case 'risk management': return 'fas fa-exclamation-triangle';
//     case 'supplier management': return 'fas fa-handshake';
//     case 'business continuity': return 'fas fa-business-time';
//     case 'privacy': return 'fas fa-user-secret';
//     case 'system protection': return 'fas fa-shield-virus';
//     case 'incident response': return 'fas fa-ambulance';
//   }
// }

// Computed properties for filtered data
const filteredFrameworks = computed(() => {
  // If no frameworks data yet, return empty array to avoid errors
  if (!frameworks.value || frameworks.value.length === 0) {
    return []
  }

  // If no dropdown selection, show all frameworks
  if (!frameworkDropdown.value) {
    return frameworks.value
  }
  
  // Safe string comparison to handle different types
  const fwId = String(frameworkDropdown.value)
  const filtered = frameworks.value.filter(fw => String(fw.id) === fwId)
  
  console.log(`Framework filtering: looking for ID ${fwId}, found ${filtered.length} matches`)
  
  // If we couldn't find any matches, return all frameworks instead of empty array
  return filtered.length > 0 ? filtered : frameworks.value
})

const filteredPolicies = computed(() => {
  return policies.value
})

const filteredSubpolicies = computed(() => {
  return subpolicies.value
})

const breadcrumbs = computed(() => {
  const arr = []
  if (selectedFramework.value) {
    arr.push({ 
      id: 'fw-' + selectedFramework.value.id, 
      name: selectedFramework.value.name 
    })
  }
  if (selectedFrameworkVersion.value) {
    arr.push({ 
      id: 'fwv-' + selectedFrameworkVersion.value.id, 
      name: selectedFrameworkVersion.value.name 
    })
  }
  if (selectedPolicy.value) {
    arr.push({
      id: 'policy-' + selectedPolicy.value.id,
      name: selectedPolicy.value.name
    })
  }
  if (selectedPolicyVersion.value) {
    arr.push({
      id: 'policyv-' + selectedPolicyVersion.value.id,
      name: selectedPolicyVersion.value.name
    })
  }
  return arr
})

// Add a preload function to fetch data in the background
const preloadData = () => {
  // Preload policies data if not cached
  if (!policiesCache.value.data) {
    console.log('Preloading policies data in the background...')
    // Use a setTimeout to avoid blocking the UI
    setTimeout(() => {
      fetchAllPolicies()
    }, 1000) // Wait 1 second after component load before preloading
  }
  
  // Preload subpolicies data if not cached
  if (!subpoliciesCache.value.data) {
    console.log('Preloading subpolicies data in the background...')
    // Use a setTimeout to avoid blocking the UI
    setTimeout(() => {
      fetchAllSubpolicies()
    }, 2000) // Wait 2 seconds after component load before preloading (stagger requests)
  }
}

// Load data on component mount
onMounted(async () => {
  try {
    // Only fetch data, skip RBAC
    fetchFrameworks()
    if (activeTab.value === 'policies') {
      fetchAllPolicies()
    } else if (activeTab.value === 'subpolicies') {
      fetchAllSubpolicies()
    } else {
      preloadData()
    }
  } catch (error) {
    console.error('[AllPolicies] Error during component initialization:', error)
  }
})

// Setup watchers outside of onMounted to avoid reactivity issues
watch(activeTab, handleTabChange)
watch(selectedPolicyFramework, handlePolicyFrameworkChange)
watch(selectedSubpolicyFramework, handleSubpolicyFrameworkChange)
// We're not watching frameworkDropdown since we have the direct @change handler
</script> 

<style src="./AllPolicies.css" scoped></style>
<style scoped>
/* .loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.loading-message {
  text-align: center;
  padding: 16px;
  color: #4f6cff;
  font-weight: 500;
}

.loading-versions {
  display: inline-flex;
  align-items: center;
  color: #4f6cff;
  font-size: 0.9rem;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: white;
  padding: 24px 32px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.loading-spinner i {
  font-size: 2rem;
  color: #4f6cff;
  margin-bottom: 12px;
}

.loading-spinner span {
  font-size: 1rem;
  font-weight: 500;
  color: #333;
} */

.error-message {
  margin: 0 auto 20px auto;
  padding: 12px 16px;
  background: #fbeaea;
  color: #dc2626;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: 600px;
}

.error-message i {
  font-size: 1.2rem;
}

.card-version-info {
  margin: 8px 0;
  padding: 6px 10px;
  background: #f0f5ff;
  border-radius: 6px;
  font-size: 0.85rem;
  color: #4a5568;
  border-left: 3px solid #4f6cff;
}

.card-version-info span {
  display: block;
  font-weight: 500;
}

.version-info-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #f7f9fb;
  padding: 12px;
  border-radius: 8px;
}

.version-info-item {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 8px;
}

.version-info-label {
  font-weight: 600;
  color: #4a5568;
  min-width: 120px;
}

.version-info-value {
  color: #1f2937;
}

.policies-count {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  color: #4a5568;
}

.policies-count i {
  color: #4f6cff;
  font-size: 0.9rem;
}

.card-actions {
  display: flex;
  align-items: center;
      justify-content: flex-end;
  }

  /* RBAC Access Control Styles */
  .access-denied-container {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    padding: 2rem;
  }

  .access-denied-content {
    text-align: center;
    max-width: 500px;
    background: white;
    padding: 3rem 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    border: 1px solid #f1f5f9;
  }

  .access-denied-icon {
    font-size: 4rem;
    color: #f59e0b;
    margin-bottom: 1.5rem;
  }

  .access-denied-content h2 {
    color: #1f2937;
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 1rem;
  }

  .access-denied-content p {
    color: #6b7280;
    font-size: 1rem;
    line-height: 1.6;
    margin-bottom: 1.5rem;
  }

  .access-info {
    background: #f9fafb;
    padding: 1rem;
    border-radius: 8px;
    font-size: 0.9rem;
    color: #374151;
    border-left: 4px solid #3b82f6;
    margin-bottom: 1.5rem;
  }

  .access-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
  }

  .access-actions .btn {
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 500;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
  }

  .access-actions .btn-warning {
    background: #f59e0b;
    color: white;
  }

  .access-actions .btn-warning:hover {
    background: #d97706;
  }

  .access-actions .btn-secondary {
    background: #6b7280;
    color: white;
  }

  .access-actions .btn-secondary:hover {
    background: #4b5563;
  }

  /* Navigation Headings Styles */
  .navigation-headings {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin: 2rem 0;
    padding: 1rem;
    border-radius: 12px;
    
  }

  .nav-heading {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem 1.5rem;
    background: white;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.3s ease;
    border: 2px solid transparent;
    min-width: 140px;
    box-shadow: 4px 4px 4px 4px rgba(0, 0, 0, 0.05);
  }

  .nav-heading:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    border-color: #4f6cff;
  }

  .nav-heading.active {
    background: linear-gradient(135deg, #4f6cff 0%, #3b5bdb 100%);
    color: white;
    border-color: #4f6cff;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(79, 108, 255, 0.3);
  }

  .nav-heading i {
    font-size: 1.5rem;
    color: #4f6cff;
    transition: color 0.3s ease;
  }

  .nav-heading.active i {
    color: white;
  }

  .nav-heading span {
    font-weight: 600;
    font-size: 0.9rem;
    text-align: center;
    color: #374151;
    transition: color 0.3s ease;
  }

  .nav-heading.active span {
    color: white;
  }

  /* Page Header Styles */
  .page-header {
    margin-bottom: 2rem;
    padding: 1rem 0;
    text-align: left !important;
    margin-left: 0 !important;
    padding-left: 0 !important;
    display: block !important;
    width: 100% !important;
  }

  .page-header h1 {
    font-size: 2.5rem;
    font-weight: 700;
    color: #1f2937;
    margin: 0 !important;
    letter-spacing: -0.025em;
    text-align: left !important;
    margin-left: 0 !important;
    padding-left: 0 !important;
    width: auto !important;
    display: block !important;
  }

  /* Responsive design for navigation headings */
  @media (max-width: 768px) {
    .navigation-headings {
      flex-direction: column;
      gap: 1rem;
      margin: 1rem 0;
    }

    .nav-heading {
      flex-direction: row;
      justify-content: flex-start;
      min-width: auto;
      padding: 0.75rem 1rem;
    }

    .nav-heading i {
      font-size: 1.2rem;
      margin-right: 0.5rem;
    }

    .nav-heading span {
      font-size: 0.85rem;
    }

    .page-header h1 {
      font-size: 2rem;
    }
  }
</style> 