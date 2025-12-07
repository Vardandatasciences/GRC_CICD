<template>
  <div class="compliance-all-compliances-container">
    <!-- Add loading overlay for navigation -->
    <div v-if="isNavigating" class="compliance-navigation-overlay">
      <div class="compliance-navigation-loader">
        <div class="compliance-loader-spinner">
          <div class="compliance-spinner-circle"></div>
        </div>
        <div class="compliance-loader-message">
          <h3>{{ navigationMessage }}</h3>
          <p>{{ navigationSubMessage }}</p>
        </div>
      </div>
    </div>

    <div class="compliance-view-header">
      <h2 class="compliance-view-title">Compliance Audit Status</h2>
      <div class="compliance-header-actions">
        <!-- View Toggle - Show for frameworks, policies, and subpolicies only (not for compliances) -->
        <div class="compliance-view-controls" v-if="showMainViewToggle">
          <button 
            class="compliance-view-toggle-btn" 
            :class="{ active: viewMode === 'list' }"
            @click="setViewMode('list')">
            <i class="fas fa-list"></i>
            List
          </button>
          <button 
            class="compliance-view-toggle-btn" 
            :class="{ active: viewMode === 'card' }"
            @click="setViewMode('card')">
            <i class="fas fa-th-large"></i>
            Card
          </button>
        </div>
        
        <!-- Export controls -->
        <div class="compliance-export-controls" v-if="!selectedSubpolicy">
          <select v-model="exportFormat" class="compliance-export-format-select">
            <option value="xlsx">Excel (.xlsx)</option>
            <option value="csv">CSV (.csv)</option>
            <option value="pdf">PDF (.pdf)</option>
            <option value="json">JSON (.json)</option>
            <option value="xml">XML (.xml)</option>
            <option value="txt">Text (.txt)</option>
          </select>
                     <button @click="handleExport(exportFormat)" class="compliance-export-btn" :disabled="isExporting">
            <i v-if="!isExporting" class="fas fa-download"></i>
            <span v-if="isExporting">Exporting...</span>
            <span v-else>Export</span>
          </button>
        </div>
      </div>
    </div>


    <!-- Error Message -->
    <div v-if="error" class="compliance-error-message">
      <i class="fas fa-exclamation-circle"></i>
      <span>{{ error }}</span>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="compliance-loading-spinner">
      <i class="fas fa-circle-notch fa-spin"></i>
      <span>Loading...</span>
    </div>

    <!-- Breadcrumbs -->
    <div class="compliance-breadcrumbs" v-if="breadcrumbs.length > 0">
      <div v-for="(crumb, index) in breadcrumbs" :key="crumb.id" class="compliance-breadcrumb-chip">
        {{ crumb.name }}
        <span class="compliance-breadcrumb-close" @click="goToStep(index)">&times;</span>
      </div>
    </div>

    <div class="compliance-content-wrapper">
      <!-- Frameworks Section -->
      <template v-if="showFrameworks">
        <div class="compliance-section-header">Frameworks</div>
        
        <!-- Card View for Frameworks -->
        <div v-if="viewMode === 'card'" class="compliance-card-grid">
          <div v-for="fw in frameworks" :key="fw.id" class="compliance-card" @click="selectFramework(fw)">
            <div class="compliance-card-icon">
              <i :class="categoryIcon(fw.category)"></i>
            </div>
            <div class="compliance-card-content">
              <div class="compliance-card-title">{{ fw.name }}</div>
              <div class="compliance-card-category">{{ fw.category }}</div>
              <div class="compliance-card-status" :class="statusClass(fw.status)">{{ fw.status }}</div>
              <div class="compliance-card-desc">{{ fw.description }}</div>
              <div class="compliance-version-info">
                <span>Versions: {{ fw.versions.length }}</span>
              </div>
              <div class="compliance-card-actions">
                <button class="compliance-action-btn primary" @click.stop="viewAllCompliances('framework', fw.id, fw.name)">
                  <i class="fas fa-list"></i> View All Compliances
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- List View for Frameworks -->
        <div v-else class="compliance-list-view">
          <div class="compliance-dynamic-table-wrapper">
            <table class="compliance-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Description</th>
                  <th>Versions</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="fw in frameworks" :key="fw.id" @click="selectFramework(fw)" class="clickable-row">
                  <td class="compliance-name" data-label="Name">{{ fw.name }}</td>
                  <td data-label="Category">{{ fw.category }}</td>
                  <td data-label="Status">
                    <span class="compliance-card-status" :class="statusClass(fw.status)">{{ fw.status }}</span>
                  </td>
                  <td class="compliance-description" data-label="Description">{{ truncateDescription(fw.description) }}</td>
                  <td data-label="Versions">{{ fw.versions.length }}</td>
                  <td data-label="Actions">
                    <button class="compliance-action-btn" @click.stop="viewAllCompliances('framework', fw.id, fw.name)">
                      <i class="fas fa-list"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>

      <!-- Policies Section -->
      <template v-else-if="showPolicies">
        <div class="compliance-section-header">Policies in {{ selectedFramework.name }}</div>
        
        <!-- Card View for Policies -->
        <div v-if="viewMode === 'card'" class="compliance-card-grid">
          <div v-for="policy in policies" :key="policy.id" class="compliance-card" @click="selectPolicy(policy)">
            <div class="compliance-card-icon">
              <i :class="categoryIcon(policy.category)"></i>
            </div>
            <div class="compliance-card-content">
              <div class="compliance-card-title">{{ policy.name }}</div>
              <div class="compliance-card-category">{{ policy.category }}</div>
              <div class="compliance-card-status" :class="statusClass(policy.status)">{{ policy.status }}</div>
              <div class="compliance-card-desc">{{ policy.description }}</div>
              <div class="compliance-version-info">
                <span>Versions: {{ policy.versions.length }}</span>
              </div>
              <div class="compliance-card-actions">
                <button class="compliance-action-btn primary" @click.stop="viewAllCompliances('policy', policy.id, policy.name)">
                  <i class="fas fa-list"></i> View All Compliances
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- List View for Policies -->
        <div v-else class="compliance-list-view">
          <div class="compliance-dynamic-table-wrapper">
            <table class="compliance-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Description</th>
                  <th>Versions</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="policy in policies" :key="policy.id" @click="selectPolicy(policy)" class="clickable-row">
                  <td class="compliance-name" data-label="Name">{{ policy.name }}</td>
                  <td data-label="Category">{{ policy.category }}</td>
                  <td data-label="Status">
                    <span class="compliance-card-status" :class="statusClass(policy.status)">{{ policy.status }}</span>
                  </td>
                  <td class="compliance-description" data-label="Description">{{ truncateDescription(policy.description) }}</td>
                  <td data-label="Versions">{{ policy.versions.length }}</td>
                  <td data-label="Actions">
                    <button class="compliance-action-btn" @click.stop="viewAllCompliances('policy', policy.id, policy.name)">
                      <i class="fas fa-list"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>

      <!-- Subpolicies Section -->
      <template v-else-if="showSubpolicies">
        <div class="compliance-section-header">Subpolicies in {{ selectedPolicy.name }}</div>
        
        <!-- Card View for Subpolicies -->
        <div v-if="viewMode === 'card'" class="compliance-card-grid">
          <div v-for="subpolicy in subpolicies" :key="subpolicy.id" class="compliance-card" @click="selectSubpolicy(subpolicy)">
            <div class="compliance-card-icon">
              <i :class="categoryIcon(subpolicy.category)"></i>
            </div>
            <div class="compliance-card-content">
              <div class="compliance-card-title">{{ subpolicy.name }}</div>
              <div class="compliance-card-category">{{ subpolicy.category }}</div>
              <div class="compliance-card-status" :class="statusClass(subpolicy.status)">{{ subpolicy.status }}</div>
              <div class="compliance-card-desc">{{ subpolicy.description }}</div>
              <div class="compliance-metadata">
                <span>Control: {{ subpolicy.control }}</span>
                <span>{{ subpolicy.permanent_temporary }}</span>
              </div>
              <div class="compliance-card-actions">
                <button class="compliance-action-btn primary" @click.stop="viewAllCompliances('subpolicy', subpolicy.id, subpolicy.name)">
                  <i class="fas fa-list"></i> View All Compliances
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- List View for Subpolicies -->
        <div v-else class="compliance-list-view">
          <div class="compliance-dynamic-table-wrapper">
            <table class="compliance-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Description</th>
                  <th>Control</th>
                  <th>Type</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="subpolicy in subpolicies" :key="subpolicy.id" @click="selectSubpolicy(subpolicy)" class="clickable-row">
                  <td class="compliance-name" data-label="Name">{{ subpolicy.name }}</td>
                  <td data-label="Category">{{ subpolicy.category }}</td>
                  <td data-label="Status">
                    <span class="compliance-card-status" :class="statusClass(subpolicy.status)">{{ subpolicy.status }}</span>
                  </td>
                  <td class="compliance-description" data-label="Description">{{ truncateDescription(subpolicy.description) }}</td>
                  <td data-label="Control">{{ truncateDescription(subpolicy.control) }}</td>
                  <td data-label="Type">{{ subpolicy.permanent_temporary }}</td>
                  <td data-label="Actions">
                    <button class="compliance-action-btn" @click.stop="viewAllCompliances('subpolicy', subpolicy.id, subpolicy.name)">
                      <i class="fas fa-list"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>

      <!-- Compliances Section -->
      <template v-else-if="selectedSubpolicy">
        <div class="compliance-section-header">
          <span>Compliances in {{ selectedSubpolicy.name }}</span>
          <div class="compliance-section-actions compliance-section-actions-right">
            <!-- Export Controls -->
            <div class="compliance-inline-export-controls">
              <select v-model="selectedFormat" class="compliance-format-select">
                <option value="xlsx">Excel (.xlsx)</option>
                <option value="csv">CSV (.csv)</option>
                <option value="pdf">PDF (.pdf)</option>
                <option value="json">JSON (.json)</option>
                <option value="xml">XML (.xml)</option>
              </select>
              <button class="compliance-export-btn" @click="handleExport(selectedFormat)">
                <i class="fas fa-download"></i> Export
              </button>
            </div>
            <button class="compliance-view-toggle-btn" @click="toggleViewMode">
              <i :class="viewMode === 'card' ? 'fas fa-list' : 'fas fa-th-large'"></i>
              {{ viewMode === 'card' ? 'List View' : 'Card View' }}
            </button>
          </div>
        </div>
        <div v-if="loading" class="compliance-loading-spinner">
          <i class="fas fa-circle-notch fa-spin"></i>
          <span>Loading compliances...</span>
        </div>
        <div v-else-if="!hasCompliances" class="compliance-no-data">
          <i class="fas fa-inbox"></i>
          <p>No compliances found for this subpolicy</p>
        </div>
        <div v-else-if="filteredCompliances.length === 0" class="compliance-no-data">
          <i class="fas fa-filter"></i>
          <p>No approved compliances found for this subpolicy</p>
        </div>
        <!-- Card View -->
        <div v-else-if="viewMode === 'card'" class="compliance-card-grid">
          <div v-for="compliance in filteredCompliances" 
               :key="compliance.id" 
               class="compliance-card">
            <div class="compliance-header">
              <span :class="['compliance-criticality-badge', 'compliance-criticality-' + compliance.category.toLowerCase()]">
                {{ compliance.category }}
              </span>
            </div>
            
            <div class="compliance-body">
              <h3>{{ compliance.name }}</h3>
              
              <div class="compliance-clean-details-grid">
                <div class="compliance-fetch-audit-actions" v-if="!complianceAudits[compliance.id]">
                  <button class="compliance-fetch-audit-btn" @click="fetchAuditInfo(compliance.id)">
                    <i class="fas fa-sync"></i> Load Compliance Information
                  </button>
                </div>
                
                <div class="compliance-detail-row">
                  <span class="compliance-detail-label">Compliance Performed By:</span>
                  <span class="compliance-detail-value">{{ complianceAudits[compliance.id]?.audit_performer_name || 'N/A' }}</span>
                </div>
                
                <div class="compliance-detail-row">
                  <span class="compliance-detail-label">Compliance Approved By:</span>
                  <span class="compliance-detail-value">{{ complianceAudits[compliance.id]?.audit_approver_name || 'N/A' }}</span>
                </div>
                
                <div class="compliance-detail-row">
                  <span class="compliance-detail-label">Completion Date:</span>
                  <span class="compliance-detail-value">{{ complianceAudits[compliance.id]?.audit_date || 'N/A' }}</span>
                </div>
                
                <div class="compliance-detail-row">
                  <span class="compliance-detail-label">Completion Status:</span>
                  <span class="compliance-detail-value" :class="getAuditStatusClass(complianceAudits[compliance.id]?.audit_findings_status)">
                    <i :class="getAuditStatusIcon(complianceAudits[compliance.id]?.audit_findings_status)"></i>
                    {{ formatAuditStatus(complianceAudits[compliance.id]?.audit_findings_status) }}
                  </span>
                </div>
              </div>
              
              <div class="compliance-footer">
                <div class="compliance-identifier">ID: {{ compliance.identifier }}</div>
              </div>
            </div>
          </div>
        </div>
        <!-- List View using DynamicTable -->
        <div v-else>
          <DynamicTable
            :data="complianceTableData"
            :columns="complianceTableColumns"
            :show-pagination="true"
            :show-actions="false"
            :unique-key="'id'"
          />
        </div>
      </template>
    </div>

    <!-- Versions Modal -->
    <div v-if="showVersionsModal" class="compliance-modal">
      <div class="compliance-modal-content">
        <div class="compliance-modal-header">
          <h3>{{ versionModalTitle }}</h3>
          <button class="compliance-close-btn" @click="closeVersionsModal">&times;</button>
        </div>
        <div class="compliance-modal-body">
          <div v-if="versions.length === 0" class="compliance-no-versions">
            No versions found.
          </div>
          <div v-else class="compliance-version-grid">
            <div v-for="version in versions" :key="version.id" class="compliance-version-card">
              <div class="compliance-version-header">
                <span class="compliance-version-number">Version {{ version.version }}</span>
                <div class="compliance-version-badges">
                  <span class="compliance-status-badge" :class="statusClass(version.status)">{{ version.status }}</span>
                  <span class="compliance-status-badge" :class="statusClass(version.activeInactive)">{{ version.activeInactive }}</span>
                </div>
              </div>
              <div class="compliance-version-details">
                <p class="compliance-version-desc">{{ version.description }}</p>
                <div class="compliance-version-info-grid">
                  <div class="compliance-info-group">
                    <span class="compliance-info-label">Maturity Level:</span>
                    <span class="compliance-info-value">{{ version.maturityLevel }}</span>
                  </div>
                  <div class="compliance-info-group">
                    <span class="compliance-info-label">Type:</span>
                    <span class="compliance-info-value">{{ version.mandatoryOptional }} | {{ version.manualAutomatic }}</span>
                  </div>
                  <div class="compliance-info-group">
                    <span class="compliance-info-label">Criticality:</span>
                    <span class="compliance-info-value" :class="'compliance-criticality-' + version.criticality.toLowerCase()">
                      {{ version.criticality }}
                    </span>
                  </div>
                  <div class="compliance-info-group" v-if="version.isRisk">
                    <span class="compliance-info-label">Risk Status:</span>
                    <span class="compliance-info-value risk">Risk Identified</span>
                  </div>
                </div>
                <div class="compliance-version-metadata">
                  <span>
                    <i class="fas fa-user"></i>
                    {{ version.createdBy }}
                  </span>
                  <span>
                    <i class="fas fa-calendar"></i>
                    {{ formatDate(version.createdDate) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import DynamicTable from '../DynamicTable.vue'
import { API_ENDPOINTS } from '../../config/api.js'
import complianceDataService from '@/services/complianceService' // NEW: Use cached compliance data

export default {
  name: 'ComplianceManagement',
  components: { DynamicTable },
  setup() {
// State
const frameworks = ref([])
const selectedFramework = ref(null)
const selectedPolicy = ref(null)
const selectedSubpolicy = ref(null)
const showVersionsModal = ref(false)
const versions = ref([])
const policies = ref([])
const subpolicies = ref([])
const loading = ref(false)
const error = ref(null)
const versionModalTitle = ref('')
const selectedFormat = ref('xlsx')
const exportFormat = ref('xlsx')
const isExporting = ref(false)
const exportError = ref(null)
const complianceAudits = ref({})
const viewMode = ref('card') // Default to card view to match other pages
const router = useRouter() // Add router for navigation
const isNavigating = ref(false) // New state for navigation loading
const navigationMessage = ref('Navigating...')
const navigationSubMessage = ref('Please wait while we load the compliance details.')

// Add columns for DynamicTable
const complianceTableColumns = [
  { key: 'audit_findings_id', label: 'Audit Findings ID', sortable: true },
  { key: 'name', label: 'Compliance', sortable: true },
  { key: 'category', label: 'Criticality', sortable: true },
  { key: 'audit_findings_status', label: 'Completion Status', sortable: true, width: '300px' },
  { key: 'audit_performer_name', label: 'Compliance Performed By', sortable: true },
  { key: 'audit_approver_name', label: 'Compliance Approved By', sortable: true },
  { key: 'audit_date', label: 'Completion Date', sortable: true }
]

const complianceTableData = computed(() => {
  if (!selectedSubpolicy.value || !selectedSubpolicy.value.compliances) return [];
  return filteredCompliances.value.map(compliance => {
    const audit = complianceAudits.value[compliance.id] || {};
    return {
      audit_findings_id: audit.audit_findings_id || 'N/A',
      name: compliance.name,
      category: compliance.category,
      audit_findings_status: audit.audit_findings_status || 'Not Audited',
      audit_performer_name: audit.audit_performer_name || 'N/A',
      audit_approver_name: audit.audit_approver_name || 'N/A',
      audit_date: audit.audit_date || 'N/A',
      id: compliance.id
    }
  })
})

// Computed
const breadcrumbs = computed(() => {
  const arr = []
  if (selectedFramework.value) arr.push({ id: 0, name: selectedFramework.value.name })
  if (selectedPolicy.value) arr.push({ id: 1, name: selectedPolicy.value.name })
  if (selectedSubpolicy.value) arr.push({ id: 2, name: selectedSubpolicy.value.name })
  return arr
})

const showFrameworks = computed(() => !selectedFramework.value)
const showPolicies = computed(() => selectedFramework.value && !selectedPolicy.value)
const showSubpolicies = computed(() => selectedPolicy.value && !selectedSubpolicy.value)

const showMainViewToggle = computed(() => {
  return showFrameworks.value || showPolicies.value || showSubpolicies.value
})

const hasCompliances = computed(() => {
  return selectedSubpolicy.value && 
         selectedSubpolicy.value.compliances && 
         selectedSubpolicy.value.compliances.length > 0;
})

// Lifecycle
onMounted(async () => {
  try {
    loading.value = true
    console.log('🔍 [Compliances] Checking for cached framework data...')
    
    // ==========================================
    // NEW: Ensure prefetch is running if needed
    // ==========================================
    if (!window.complianceDataFetchPromise && !complianceDataService.hasFrameworksCache()) {
      console.log('🚀 [Compliances] Starting compliance prefetch (user navigated directly)...')
      window.complianceDataFetchPromise = complianceDataService.fetchAllComplianceData()
    }

    // Wait for any ongoing prefetch to finish
    if (window.complianceDataFetchPromise) {
      console.log('⏳ [Compliances] Waiting for compliance prefetch to complete...')
      try {
        await window.complianceDataFetchPromise
        console.log('✅ [Compliances] Prefetch completed')
      } catch (prefetchError) {
        console.warn('⚠️ [Compliances] Prefetch failed, falling back to direct API fetch', prefetchError)
      }
    }
    
    // FIRST: Try to get data from cache
    if (complianceDataService.hasFrameworksCache()) {
      console.log('✅ [Compliances] Using cached framework data')
      const cachedFrameworks = complianceDataService.getData('frameworks') || []
      
      frameworks.value = cachedFrameworks.map(framework => ({
        id: framework.FrameworkId || framework.id,
        name: framework.FrameworkName || framework.name,
        versions: framework.versions || []
      }))
      console.log(`[Compliances] Loaded ${frameworks.value.length} frameworks from cache (prefetched on Home page)`)
    } else {
      // FALLBACK: Fetch from API if cache is empty
      console.log('⚠️ [Compliances] No cached data found, fetching from API...')
      const response = await axios.get(API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_FRAMEWORKS)
      if (response.data && Array.isArray(response.data)) {
        frameworks.value = response.data.map(framework => ({
          ...framework,
          versions: framework.versions || []
        }))
        console.log(`[Compliances] Loaded ${frameworks.value.length} frameworks directly from API (cache unavailable)`)
        
        // Update cache so subsequent pages benefit
        complianceDataService.setData('frameworks', response.data)
        console.log('ℹ️ [Compliances] Cache updated after direct API fetch')
      } else {
        frameworks.value = []
      }
    }
  } catch (err) {
    error.value = 'Failed to load frameworks'
    console.error('Error fetching frameworks:', err)
    frameworks.value = []
  } finally {
    loading.value = false
  }
})

// Methods
async function selectFramework(fw) {
  try {
    loading.value = true
    selectedFramework.value = fw
    selectedPolicy.value = null
    selectedSubpolicy.value = null
    
    // Get active policies for the selected framework using the correct endpoint
          const response = await axios.get(API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_POLICIES, {
      params: { 
        framework_id: fw.id
      }
    })
    
    if (response.data && Array.isArray(response.data)) {
      policies.value = response.data.map(policy => ({
        ...policy,
        versions: policy.versions || [] // Versions count should be included in the response
      }))
    } else {
      policies.value = []
    }
  } catch (err) {
    error.value = 'Failed to load policies'
    console.error('Error fetching policies:', err)
    policies.value = []
  } finally {
    loading.value = false
  }
}

async function selectPolicy(policy) {
  try {
    loading.value = true
    selectedPolicy.value = policy
    selectedSubpolicy.value = null
    
    // Get active subpolicies for the selected policy using the correct endpoint
          const response = await axios.get(API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_SUBPOLICIES, {
      params: { 
        policy_id: policy.id
      }
    })
    
    if (response.data && Array.isArray(response.data)) {
      subpolicies.value = response.data
    } else {
      subpolicies.value = []
    }
  } catch (err) {
    error.value = 'Failed to load subpolicies'
    console.error('Error fetching subpolicies:', err)
    subpolicies.value = []
  } finally {
    loading.value = false
  }
}

async function selectSubpolicy(subpolicy) {
  try {
    loading.value = true;
    selectedSubpolicy.value = subpolicy;
        complianceAudits.value = {}; // Reset audit data
        
        console.log(`Selecting subpolicy: ${subpolicy.id} - ${subpolicy.name}`);
    
            const response = await axios.get(API_ENDPOINTS.COMPLIANCE_SUBPOLICY_COMPLIANCES(subpolicy.id));
    console.log('Subpolicy compliances response:', response.data);
    
    if (response.data && response.data.success) {
          const compliances = response.data.compliances.map(compliance => ({
          id: compliance.ComplianceId,
          name: compliance.ComplianceItemDescription,
          status: compliance.Status,
          description: compliance.ComplianceItemDescription,
          category: compliance.Criticality,
          maturityLevel: compliance.MaturityLevel,
          mandatoryOptional: compliance.MandatoryOptional,
          manualAutomatic: compliance.ManualAutomatic,
          createdBy: compliance.CreatedByName,
          createdDate: compliance.CreatedByDate,
          isRisk: compliance.IsRisk,
          activeInactive: compliance.ActiveInactive,
          identifier: compliance.Identifier,
          version: compliance.ComplianceVersion
          }));
          
          selectedSubpolicy.value = {
            ...subpolicy,
            compliances: compliances
          };
          
          console.log(`Found ${compliances.length} compliances for subpolicy ${subpolicy.id}`);
          
          // Fetch audit info for each compliance
          if (compliances.length > 0) {
            for (const compliance of compliances) {
              try {
                await fetchAuditInfo(compliance.id);
                // Add a small delay to prevent overwhelming the server
                await new Promise(resolve => setTimeout(resolve, 100));
              } catch (auditErr) {
                console.error(`Error fetching audit info for compliance ${compliance.id}:`, auditErr);
                // Continue with next compliance
              }
            }
            console.log('All audit information fetched:', complianceAudits.value);
          }
    } else {
          selectedSubpolicy.value = {
            ...subpolicy,
            compliances: []
          };
          console.log('No compliances found or API returned error');
    }
  } catch (err) {
    console.error('Error fetching subpolicy compliances:', err);
    error.value = 'Failed to load compliances';
        selectedSubpolicy.value = {
          ...subpolicy,
          compliances: []
        };
  } finally {
    loading.value = false;
  }
}

async function showVersions(type, item) {
  try {
    loading.value = true
    
    switch (type) {
      case 'policy':
        versionModalTitle.value = `Versions of ${item.name}`
        break
      case 'compliance':
        versionModalTitle.value = `Versions of Compliance ${item.name}`
        break
    }
    
            const response = await axios.get(API_ENDPOINTS.COMPLIANCE_AUDIT_INFO(item.id))
    if (response.data && Array.isArray(response.data)) {
      versions.value = response.data.map(version => ({
        id: version.ComplianceId,
        version: version.ComplianceVersion,
        name: version.ComplianceItemDescription,
        status: version.Status,
        description: version.ComplianceItemDescription,
        criticality: version.Criticality,
        maturityLevel: version.MaturityLevel,
        mandatoryOptional: version.MandatoryOptional,
        manualAutomatic: version.ManualAutomatic,
        createdBy: version.CreatedByName,
        createdDate: version.CreatedByDate,
        isRisk: version.IsRisk,
        activeInactive: version.ActiveInactive,
        identifier: version.Identifier
      }))
    } else {
      versions.value = []
    }
    showVersionsModal.value = true
  } catch (err) {
    error.value = `Failed to load ${type} versions`
    console.error(`Error fetching ${type} versions:`, err)
    versions.value = []
  } finally {
    loading.value = false
  }
}

function closeVersionsModal() {
  showVersionsModal.value = false
  versions.value = []
  versionModalTitle.value = ''
}

function goToStep(idx) {
  if (idx <= 0) {
    selectedFramework.value = null
    selectedPolicy.value = null
    selectedSubpolicy.value = null
  } else if (idx === 1) {
    selectedPolicy.value = null
    selectedSubpolicy.value = null
  } else if (idx === 2) {
    selectedSubpolicy.value = null
  }
}

function formatDate(date) {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString()
}

function categoryIcon(category) {
  switch ((category || '').toLowerCase()) {
    case 'governance': return 'fas fa-shield-alt'
    case 'access control': return 'fas fa-user-shield'
    case 'asset management': return 'fas fa-boxes'
    case 'cryptography': return 'fas fa-key'
    case 'data management': return 'fas fa-database'
    case 'device management': return 'fas fa-mobile-alt'
    case 'risk management': return 'fas fa-exclamation-triangle'
    case 'supplier management': return 'fas fa-handshake'
    case 'business continuity': return 'fas fa-business-time'
    case 'privacy': return 'fas fa-user-secret'
    case 'system protection': return 'fas fa-shield-virus'
    case 'incident response': return 'fas fa-ambulance'
    default: return 'fas fa-file-alt'
  }
}

function statusClass(status) {
  if (!status) return ''
  const s = status.toLowerCase()
  if (s.includes('active')) return 'active'
  if (s.includes('inactive')) return 'inactive'
  if (s.includes('pending')) return 'pending'
  return ''
}

const viewAllCompliances = async (type, id, name) => {
  try {
    isNavigating.value = true;
    
    // Set custom messages based on the type
    if (type === 'framework') {
      navigationMessage.value = `Loading Framework Compliances`;
      navigationSubMessage.value = `Preparing compliance audit data for ${name}...`;
    } else if (type === 'policy') {
      navigationMessage.value = `Loading Policy Compliances`;
      navigationSubMessage.value = `Fetching compliance audit data for ${name}...`;
    } else if (type === 'subpolicy') {
      navigationMessage.value = `Loading Subpolicy Compliances`;
      navigationSubMessage.value = `Retrieving compliance audit data for ${name}...`;
    } else {
      navigationMessage.value = 'Loading Compliances';
      navigationSubMessage.value = 'Please wait while we load the compliance details.';
    }
    
    // Simulate a short delay to show the loader even on fast connections
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Navigate to the ComplianceAuditView component
    await router.push({
      name: 'ComplianceAuditView',
      params: {
        type: type,
        id: id,
        name: encodeURIComponent(name)
      }
    });
    
    // Hide the loader after navigation is complete
    // Use a small timeout to ensure smooth transition
    setTimeout(() => {
      isNavigating.value = false;
    }, 200);
  } catch (error) {
    console.error('Error navigating to audit view:', error);
    error.value = 'Failed to navigate to audit view. Please try again.';
    
    // Show error in the navigation overlay
    navigationMessage.value = 'Navigation Error';
    navigationSubMessage.value = 'Failed to load compliance details. Please try again.';
    
    // Hide the error message after a delay
    setTimeout(() => {
      isNavigating.value = false;
    }, 2000);
  }
}

async function handleExport(format) {
  try {
    isExporting.value = true;
    exportError.value = null;
    
    let itemType = '';
    let itemId = null;
    let dataToExport = [];
    
    // Determine the item type and ID based on current selection
    if (selectedSubpolicy.value) {
      itemType = 'subpolicy';
      itemId = selectedSubpolicy.value.id;
      // Export compliances for selected subpolicy
      if (selectedSubpolicy.value.compliances) {
        dataToExport = selectedSubpolicy.value.compliances.map(compliance => ({
          ComplianceId: compliance.id,
          ComplianceItemDescription: compliance.name,
          Status: compliance.status,
          Criticality: compliance.category,
          MaturityLevel: compliance.maturityLevel,
          MandatoryOptional: compliance.mandatoryOptional,
          ManualAutomatic: compliance.manualAutomatic,
          CreatedByName: compliance.createdBy,
          CreatedByDate: compliance.createdDate,
          ComplianceVersion: compliance.version,
          Identifier: compliance.identifier,
          SubPolicyName: selectedSubpolicy.value.name,
          PolicyName: selectedPolicy.value?.name || '',
          FrameworkName: selectedFramework.value?.name || ''
        }));
      }
    } else if (selectedPolicy.value) {
      itemType = 'policy';
      itemId = selectedPolicy.value.id;
    } else if (selectedFramework.value) {
      itemType = 'framework';
      itemId = selectedFramework.value.id;
    } else {
      // If no specific item is selected, export all frameworks
      itemType = 'all';
    }
    
    console.log(`Attempting export for ${itemType} ${itemId} in ${format} format`);
    
    // Use the POST endpoint that returns S3 URL
    const response = await axios.post(API_ENDPOINTS.COMPLIANCE_EXPORT, {
      file_format: format,
      data: JSON.stringify(dataToExport),
      options: JSON.stringify({
        item_type: itemType,
        item_id: itemId,
        filters: {
          ...(itemType === 'subpolicy' && { subpolicy_id: itemId }),
          ...(itemType === 'policy' && { policy_id: itemId }),
          ...(itemType === 'framework' && { framework_id: itemId })
        }
      })
    });

    console.log('Export successful:', response.data);
    
    // Check if we have a file URL
    if (response.data && response.data.file_url) {
      // Try to open the file URL in a new tab, fallback to download if it fails
      try {
        const newWindow = window.open(response.data.file_url, '_blank');
        if (newWindow) {
          ElMessage({
            message: 'Export completed successfully! File opened in new tab.',
            type: 'success',
            duration: 3000
          });
        } else {
          // Fallback to download if popup is blocked
          const link = document.createElement('a');
          link.href = response.data.file_url;
          link.setAttribute('download', response.data.file_name || `compliance_export.${format}`);
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          ElMessage({
            message: 'Export completed successfully! File downloaded.',
            type: 'success',
            duration: 3000
          });
        }
      } catch (downloadErr) {
        // Fallback to download if window.open fails
        const link = document.createElement('a');
        link.href = response.data.file_url;
        link.setAttribute('download', response.data.file_name || `compliance_export.${format}`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        ElMessage({
          message: 'Export completed successfully! File downloaded.',
          type: 'success',
          duration: 3000
        });
        console.error(downloadErr);
      }
    } else {
      ElMessage({
        message: 'Export completed successfully!',
        type: 'success',
        duration: 3000
      });
    }
  } catch (error) {
    console.error('Export error:', error);
    const errorMessage = error.response?.data?.message || error.message || 'Failed to export compliances';
    exportError.value = errorMessage;
    ElMessage({
      message: errorMessage,
      type: 'error',
      duration: 5000
    });
  } finally {
    isExporting.value = false;
  }
}

const toggleViewMode = () => {
  viewMode.value = viewMode.value === 'card' ? 'list' : 'card'
}

const setViewMode = (mode) => {
  viewMode.value = mode
}

const truncateDescription = (text, maxLength = 100) => {
  if (!text) return 'No description available'
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}



const filteredCompliances = computed(() => {
  if (!selectedSubpolicy.value || !selectedSubpolicy.value.compliances) return [];
  return selectedSubpolicy.value.compliances.filter(compliance => compliance.status === 'Approved');
});

async function fetchAuditInfo(complianceId) {
  try {
    console.log(`Fetching audit info for compliance ID: ${complianceId}`);
    
    // Check if we already have this data to avoid unnecessary requests
    if (complianceAudits.value[complianceId] && 
        complianceAudits.value[complianceId].audit_findings_status !== 'Not Audited') {
      console.log(`Using cached audit data for compliance ID: ${complianceId}`);
      return;
    }
    
    // Set a temporary loading state in the audit data
    complianceAudits.value = {
      ...complianceAudits.value,
      [complianceId]: { 
        audit_findings_status: 'Loading...',
        isLoading: true
      }
    };
    
    const response = await axios.get(`/api/compliance/compliance/${complianceId}/audit-info/`);
    console.log(`Audit info response for compliance ID ${complianceId}:`, response.data);
    
    if (response.data && response.data.success) {
      complianceAudits.value = {
        ...complianceAudits.value,
        [complianceId]: {
          ...response.data.data,
          isLoading: false
        }
      };
      console.log(`Updated audit data for compliance ID ${complianceId}:`, complianceAudits.value[complianceId]);
    } else {
      throw new Error(response.data.message || 'Failed to fetch audit data');
    }
  } catch (err) {
    console.error(`Error fetching audit info for compliance ${complianceId}:`, err);
    // Set an empty object to prevent repeated requests
    complianceAudits.value = {
      ...complianceAudits.value,
      [complianceId]: { 
        audit_findings_status: 'Not Audited',
        isLoading: false,
        error: err.message
      }
    };
  }
}

function getAuditStatusClass(status) {
  if (!status) return 'not-audited';
  
  const statusLower = status.toLowerCase();
  if (statusLower.includes('non') || statusLower.includes('not compliant')) return 'non-compliant';
  if (statusLower.includes('partially')) return 'partially-compliant';
  if (statusLower.includes('fully')) return 'fully-compliant';
  if (statusLower.includes('not applicable')) return 'not-applicable';
  
  return 'not-audited';
}

function getAuditStatusIcon(status) {
  if (!status) return 'fas fa-question-circle';
  
  const statusLower = status.toLowerCase();
  if (statusLower.includes('non') || statusLower.includes('not compliant')) return 'fas fa-times-circle';
  if (statusLower.includes('partially')) return 'fas fa-exclamation-circle';
  if (statusLower.includes('fully')) return 'fas fa-check-circle';
  if (statusLower.includes('not applicable')) return 'fas fa-ban';
  
  return 'fas fa-question-circle';
}

// Method to format the status display text for the UI
function formatAuditStatus(status) {
  if (!status) return 'Not Audited';
  
  const statusLower = status.toLowerCase();
  if (statusLower.includes('non') || statusLower.includes('not compliant')) return 'Non Conformity';
  if (statusLower.includes('partially')) return 'Control Gap';
  
  // Return the original status for other cases
  return status;
}

const handleAuditLinkClick = (auditFindingsId) => {
  if (!auditFindingsId) return;
  console.log(`Clicked on audit findings ID: ${auditFindingsId}`);
  // This function will be used for redirecting in the future
  // You can implement the redirection logic here when needed
}

return {
  frameworks,
  selectedFramework,
  selectedPolicy,
  selectedSubpolicy,
  showVersionsModal,
  versions,
  policies,
  subpolicies,
  loading,
  error,
  versionModalTitle,
  selectedFormat,
  exportFormat,
  isExporting,
  exportError,
  complianceAudits,
  viewMode,
  router,
  breadcrumbs,
  showFrameworks,
  showPolicies,
  showSubpolicies,
  showMainViewToggle,
  hasCompliances,
  selectFramework,
  selectPolicy,
  selectSubpolicy,
  showVersions,
  closeVersionsModal,
  goToStep,
  formatDate,
  categoryIcon,
  statusClass,
  viewAllCompliances,
  handleExport,
  fetchAuditInfo,
  getAuditStatusClass,
  getAuditStatusIcon,
  formatAuditStatus,
  handleAuditLinkClick,
  toggleViewMode,
  setViewMode,
  truncateDescription,
  filteredCompliances,
  complianceTableColumns,
  complianceTableData,
  DynamicTable,
  isNavigating,
  navigationMessage,
  navigationSubMessage
}
}
}
</script>

<style src="./Compliances.css"></style>

<style>
/* Framework Explorer inspired styling */
.compliance-all-compliances-container {
  padding: 20px;
  background-color: #f8f9fa;
  min-height: 100vh;
}

.compliance-custom-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 10px;
  border-bottom: 2px solid #4f8cff;
}

.compliance-custom-header span {
  margin: 0;
  color: #344054;
  font-size: 1.8rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.compliance-custom-header-underline {
  width: 100%;
  height: 2px;
  background: linear-gradient(135deg, #4f8cff 0%, #3d7aff 100%);
  margin-top: 5px;
}

/* View Toggle Buttons - Framework Explorer Style */
.compliance-view-controls {
  display: flex;
  align-items: center;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 4px;
  border: 1px solid #e9ecef;
}

.compliance-view-toggle-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: transparent;
  border: none;
  color: #6c757d;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s ease;
  cursor: pointer;
  font-size: 0.9rem;
}

.compliance-view-toggle-btn:hover {
  background: #e9ecef;
  color: #495057;
}

.compliance-view-toggle-btn.active {
  background: #4f8cff;
  color: white;
  box-shadow: 0 2px 4px rgba(79, 140, 255, 0.3);
}

.compliance-view-toggle-btn i {
  font-size: 1rem;
}

/* Section Headers */
.compliance-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  font-size: 1.4rem;
  font-weight: 600;
  color: #344054;
  padding-bottom: 8px;
  border-bottom: 1px solid #e9ecef;
}

.compliance-section-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.compliance-section-actions .compliance-view-toggle-btn {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  padding: 6px 12px;
  font-size: 0.85rem;
}

/* Export Controls */
.compliance-inline-export-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.compliance-format-select {
  padding: 8px 12px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background-color: white;
  font-size: 14px;
  min-width: 150px;
  color: #495057;
}

.compliance-export-btn {
  padding: 8px 16px;
  background-color: #4f8cff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(79, 140, 255, 0.2);
}

.compliance-export-btn:hover {
  background-color: #3d7aff;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(79, 140, 255, 0.3);
}

.compliance-export-btn:disabled {
  background-color: #adb5bd;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* Enhanced Table Styling - Framework Explorer Style */
.compliance-list-view {
  background-color: #ffffff;
  border-radius: 12px;
  border: 1px solid #e9ecef;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  margin-top: 20px;
}

.compliance-table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  margin: 0;
}

.compliance-table th {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 16px 12px;
  text-align: left;
  font-weight: 600;
  color: #495057;
  border-bottom: 2px solid #dee2e6;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 10;
}

.compliance-table td {
  padding: 16px 12px;
  border-bottom: 1px solid #f1f3f4;
  color: #495057;
  vertical-align: middle;
  font-size: 0.9rem;
}

.compliance-table tr {
  transition: all 0.2s ease;
}

.compliance-table tr:hover {
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f7ff 100%);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(79, 140, 255, 0.1);
}

.compliance-table tr.clickable-row {
  cursor: pointer;
}

.compliance-table tr:last-child td {
  border-bottom: none;
}

/* Status Badges - Framework Explorer Style */
.compliance-card-status {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: 2px solid transparent;
}

.compliance-card-status.active {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  color: #155724;
  border-color: #c3e6cb;
}

.compliance-card-status.inactive {
  background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
  color: #721c24;
  border-color: #f5c6cb;
}

.compliance-card-status.pending {
  background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
  color: #856404;
  border-color: #ffeaa7;
}

/* Criticality Badges */
.compliance-criticality-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  border: 2px solid transparent;
}

.compliance-criticality-high {
  background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
  color: #c62828;
  border-color: #ffcdd2;
}

.compliance-criticality-medium {
  background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
  color: #ef6c00;
  border-color: #ffecb3;
}

.compliance-criticality-low {
  background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
  color: #2e7d32;
  border-color: #c8e6c9;
}

/* Action Buttons - Framework Explorer Style */
.compliance-action-btn {
  padding: 8px 12px;
  font-size: 0.85rem;
  margin-right: 6px;
  border-radius: 8px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  color: #495057;
  border: 1px solid #dee2e6;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.compliance-action-btn:hover {
  background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
  color: #212529;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.compliance-action-btn.primary {
  background: linear-gradient(135deg, #4f8cff 0%, #3d7aff 100%);
  color: white;
  border-color: #4f8cff;
}

.compliance-action-btn.primary:hover {
  background: linear-gradient(135deg, #3d7aff 0%, #2b68ff 100%);
  border-color: #3d7aff;
}

.compliance-action-btn i {
  font-size: 0.9rem;
}

/* Card View Enhancements */
.compliance-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
  margin-top: 24px;
}

.compliance-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border: 1px solid #e9ecef;
  border-radius: 16px;
  padding: 0;
  transition: all 0.3s ease;
  cursor: pointer;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.compliance-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(79, 140, 255, 0.15);
  border-color: #4f8cff;
}

.compliance-card-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #4f8cff 0%, #3d7aff 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.2rem;
  margin-bottom: 16px;
  box-shadow: 0 4px 8px rgba(79, 140, 255, 0.3);
}

.compliance-card-content {
  padding: 20px;
}

.compliance-card-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: #212529;
  margin-bottom: 8px;
  line-height: 1.3;
}

.compliance-card-category {
  font-size: 0.9rem;
  color: #6c757d;
  margin-bottom: 12px;
  font-weight: 500;
}

.compliance-card-desc {
  font-size: 0.95rem;
  color: #495057;
  margin-bottom: 16px;
  line-height: 1.5;
}

.compliance-version-info {
  font-size: 0.9rem;
  color: #6c757d;
  margin-bottom: 16px;
  font-weight: 500;
}

/* Breadcrumbs - Framework Explorer Style */
.compliance-breadcrumbs {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.compliance-breadcrumb-chip {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 0.9rem;
  color: #495057;
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #dee2e6;
  font-weight: 500;
}

.compliance-breadcrumb-close {
  cursor: pointer;
  font-size: 1.1rem;
  line-height: 1;
  color: #6c757d;
  transition: color 0.2s ease;
  padding: 2px;
  border-radius: 50%;
}

.compliance-breadcrumb-close:hover {
  color: #dc3545;
  background: rgba(220, 53, 69, 0.1);
}

/* Loading State */
.compliance-loading-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #495057;
  margin: 48px 0;
  font-size: 1.1rem;
  font-weight: 500;
}

.compliance-loading-spinner i {
  font-size: 1.5rem;
  color: #4f8cff;
}

/* No Data State */
.compliance-no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #6c757d;
  text-align: center;
}

.compliance-no-data i {
  font-size: 4rem;
  margin-bottom: 20px;
  color: #dee2e6;
}

.compliance-no-data p {
  font-size: 1.2rem;
  margin: 0;
  font-weight: 500;
}

/* Error State */
.compliance-error-message {
  display: flex;
  align-items: center;
  gap: 10px;
  background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
  color: #721c24;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid #f5c6cb;
}

.compliance-error-message i {
  font-size: 1.2rem;
}

/* Enhanced compliance cards for detailed view */
.compliance-header {
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.compliance-body {
  padding: 20px;
}

.compliance-body h3 {
  margin-top: 0;
  margin-bottom: 16px;
  color: #1f2937;
  font-size: 1.2rem;
  line-height: 1.4;
  font-weight: 600;
}

.compliance-clean-details-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #f9fafb;
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
  border: 1px solid #e5e7eb;
}

.compliance-detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px dashed #e5e7eb;
  padding-bottom: 8px;
  font-size: 0.95rem;
}

.compliance-detail-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.compliance-detail-label, .compliance-label {
  color: #4b5563;
  font-weight: 500;
  min-width: 150px;
}

.compliance-detail-value, .compliance-value {
  color: #111827;
  font-weight: 500;
  text-align: right;
}

/* Audit status classes */
.compliance-fully-compliant {
  color: #10b981;
  font-weight: 500;
}

.compliance-fully-compliant i {
  color: #10b981;
  margin-right: 5px;
}

/* "Partially Compliant" displayed as "Control Gaps" in UI */
.compliance-partially-compliant {
  color: #f59e0b;
  font-weight: 500;
}

.compliance-partially-compliant i {
  color: #f59e0b;
  margin-right: 5px;
}

/* "Non Compliant" displayed as "Non Conformity" in UI */
.compliance-non-compliant {
  color: #ef4444;
  font-weight: 500;
}

.compliance-non-compliant i {
  color: #ef4444;
  margin-right: 5px;
}

.compliance-not-applicable {
  color: #6b7280;
  font-weight: 500;
}

.compliance-not-applicable i {
  color: #6b7280;
  margin-right: 5px;
}

.compliance-not-audited {
  color: #9ca3af;
  font-style: italic;
}

.compliance-not-audited i {
  color: #9ca3af;
  margin-right: 5px;
}

.compliance-fetch-audit-actions {
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
}

.compliance-fetch-audit-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background-color: #f3f4f6;
  border: 1px solid #d1d5db;
  color: #4b5563;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s ease;
  cursor: pointer;
}

.compliance-fetch-audit-btn:hover {
  background-color: #e5e7eb;
  transform: translateY(-1px);
}

.compliance-fetch-audit-btn i {
  color: #6b7280;
}

.compliance-footer {
  padding-top: 12px;
  margin-top: 12px;
  border-top: 1px solid #e5e7eb;
  font-size: 0.85rem;
  color: #6b7280;
}

.compliance-identifier {
  font-family: monospace;
  font-weight: 500;
}

.compliance-metadata {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0;
  font-size: 0.85rem;
  color: #6b7280;
}

.compliance-metadata span {
  background: #f3f4f6;
  padding: 4px 8px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

/* Modal styling */
.compliance-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.compliance-modal-content {
  background: #ffffff;
  border-radius: 12px;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px rgba(0, 0, 0, 0.2);
}

.compliance-modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
}

.compliance-modal-header h3 {
  margin: 0;
  font-size: 1.3rem;
  color: #1f2937;
  font-weight: 600;
}

.compliance-close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6b7280;
  cursor: pointer;
  padding: 4px;
  line-height: 1;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.compliance-close-btn:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.compliance-modal-body {
  padding: 24px;
}

.compliance-no-versions {
  text-align: center;
  color: #6b7280;
  padding: 40px 0;
  font-size: 1.1rem;
}

.compliance-version-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.compliance-version-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s ease;
}

.compliance-version-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #4f8cff;
}

.compliance-version-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.compliance-version-number {
  font-weight: 600;
  color: #1f2937;
  font-size: 1.1rem;
}

.compliance-version-badges {
  display: flex;
  gap: 8px;
}

.compliance-status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.compliance-version-details {
  color: #4b5563;
  font-size: 0.95rem;
}

.compliance-version-desc {
  margin: 0 0 16px 0;
  line-height: 1.5;
  color: #374151;
}

.compliance-version-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.compliance-info-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.compliance-info-label {
  font-size: 0.8rem;
  color: #6b7280;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.compliance-info-value {
  font-size: 0.9rem;
  color: #1f2937;
  font-weight: 500;
}

.compliance-info-value.risk {
  color: #dc2626;
  font-weight: 600;
}

.compliance-version-metadata {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 0.85rem;
  color: #6b7280;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.compliance-version-metadata span {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Add animation for loading state */
.fa-sync {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Animation for smooth transitions */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.compliance-card,
.compliance-table tr {
  animation: slideIn 0.3s ease-out;
}

/* Focus states for accessibility */
.compliance-view-toggle-btn:focus,
.compliance-action-btn:focus,
.compliance-export-btn:focus {
  outline: 2px solid #4f8cff;
  outline-offset: 2px;
}

/* Responsive design */
@media (max-width: 1200px) {
  .compliance-card-grid {
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  }
  
  .compliance-table {
    min-width: 1000px;
  }
  
  .compliance-list-view {
    overflow-x: auto;
  }
}

@media (max-width: 768px) {
  .compliance-custom-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .compliance-section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .compliance-section-actions {
    width: 100%;
    justify-content: stretch;
  }
  
  .compliance-card-grid {
    grid-template-columns: 1fr;
  }
  
  .compliance-breadcrumbs {
    flex-direction: column;
    gap: 8px;
  }
  
  /* Make table responsive on mobile */
  .compliance-table,
  .compliance-table thead,
  .compliance-table tbody,
  .compliance-table th,
  .compliance-table td,
  .compliance-table tr {
    display: block;
  }
  
  .compliance-table thead tr {
    position: absolute;
    top: -9999px;
    left: -9999px;
  }
  
  .compliance-table tr {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    margin-bottom: 10px;
    padding: 10px;
    background-color: white;
  }
  
  .compliance-table td {
    border: none;
    position: relative;
    padding: 8px 10px 8px 40%;
    border-bottom: 1px solid #f3f4f6;
  }
  
  .compliance-table td:before {
    content: attr(data-label) ": ";
    position: absolute;
    left: 6px;
    width: 35%;
    padding-right: 10px;
    white-space: nowrap;
    font-weight: 600;
    color: #4b5563;
  }
  
  .compliance-table td:last-child {
    border-bottom: none;
  }
}

/* Right-aligned and compact section actions for compliance */
.compliance-section-actions-right {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  width: 100%;
  gap: 6px;
}

/* Ensure completion status column has adequate width */
.compliance-all-compliances-container .dynamic-table th[data-key="audit_findings_status"],
.compliance-all-compliances-container .dynamic-table td[data-key="audit_findings_status"] {
  min-width: 300px !important;
  max-width: 350px !important;
  width: 300px !important;
}

/* Ensure status text doesn't get truncated */
.compliance-all-compliances-container .dynamic-table .status-with-icon {
  white-space: nowrap;
  overflow: visible;
  text-overflow: clip;
}

/* Content wrapper */
.compliance-content-wrapper {
  background-color: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #e9ecef;
}

/* Loading overlay for navigation */
.compliance-navigation-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
  animation: fadeIn 0.3s ease-out;
}

.compliance-navigation-loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 40px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  max-width: 500px;
  width: 90%;
  animation: scaleIn 0.4s ease-out;
  border: 1px solid #f0f0f0;
}

.compliance-loader-spinner {
  position: relative;
  width: 80px;
  height: 80px;
}

.compliance-spinner-circle {
  box-sizing: border-box;
  position: absolute;
  width: 100%;
  height: 100%;
  border: 4px solid transparent;
  border-top-color: #4f8cff;
  border-radius: 50%;
  animation: spinnerOne 1.2s linear infinite;
}

.compliance-spinner-circle:before {
  content: "";
  box-sizing: border-box;
  position: absolute;
  top: 4px;
  left: 4px;
  right: 4px;
  bottom: 4px;
  border: 4px solid transparent;
  border-right-color: #3d7aff;
  border-radius: 50%;
  animation: spinnerTwo 0.8s linear infinite;
}

.compliance-spinner-circle:after {
  content: "";
  box-sizing: border-box;
  position: absolute;
  top: 12px;
  left: 12px;
  right: 12px;
  bottom: 12px;
  border: 4px solid transparent;
  border-bottom-color: #2b68ff;
  border-radius: 50%;
  animation: spinnerThree 1s linear infinite;
}

.compliance-loader-message {
  text-align: center;
}

.compliance-loader-message h3 {
  margin: 0 0 10px 0;
  color: #344054;
  font-size: 1.3rem;
  font-weight: 600;
}

.compliance-loader-message p {
  margin: 0;
  color: #6c757d;
  font-size: 1rem;
  line-height: 1.5;
}

@keyframes spinnerOne {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes spinnerTwo {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(-360deg); }
}

@keyframes spinnerThree {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
</style> 