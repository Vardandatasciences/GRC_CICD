<template>
  <div class="compliance-view-container">
    <div class="action-bar">
      <div class="action-buttons">
        <!-- Export Section -->
        <div class="export-section">
          <select v-model="selectedFormat" class="format-select">
            <option value="xlsx">Excel (.xlsx)</option>
            <option value="csv">CSV (.csv)</option>
            <option value="pdf">PDF (.pdf)</option>
            <option value="json">JSON (.json)</option>
            <option value="xml">XML (.xml)</option>
          </select>
          <button class="btn btn-primary" @click="handleExport(selectedFormat)">
            <i class="fas fa-download"></i>
            Export
          </button>
        </div>
        <button class="btn btn-outline" @click="goBack">
          <i class="fas fa-arrow-left"></i>
          Back
        </button>
      </div>
    </div>
    <h1>{{ title }}</h1>

    <!-- Filter Section -->
    <div class="filter-section">
      <div class="filter-controls">
        <div class="filter-group">
          <label for="framework-filter">Filter by Framework:</label>
          <select 
            id="framework-filter" 
            v-model="selectedFramework" 
            @change="handleFrameworkChange"
            class="framework-select"
          >
            <option value="">All Frameworks</option>
            <option 
              v-for="framework in filteredFrameworks" 
              :key="framework.FrameworkId" 
              :value="framework.FrameworkId"
            >
              {{ framework.FrameworkName }}
            </option>
          </select>
        </div>
        
        
        <div class="filter-group">
          <button class="btn btn-primary" @click="testFiltering">
            <i class="fas fa-test"></i>
            Test Filtering
          </button>
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-circle"></i>
      <span>{{ error }}</span>
    </div>


    <div class="content-wrapper">
      
      <!-- Data Summary -->
      <div v-if="compliances.length > 0" class="data-summary">
        <div class="summary-item">
          <span class="summary-label">Total Compliances:</span>
          <span class="summary-value">{{ filteredCompliances.length }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Audited:</span>
          <span class="summary-value">{{ getAuditedCount() }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Not Audited:</span>
          <span class="summary-value">{{ getNotAuditedCount() }}</span>
        </div>
      </div>
      
      <div v-if="!filteredCompliances.length" class="no-data">
        <i class="fas fa-inbox"></i>
        <p>No compliances found</p>
      </div>
      
      <!-- Card View -->
      <div v-else-if="viewMode === 'card'" class="compliances-grid">
        <div v-for="compliance in compliances" 
             :key="compliance.ComplianceId" 
             class="compliance-card">
          <div class="compliance-header">
            <span :class="['criticality-badge', 'criticality-' + compliance.Criticality.toLowerCase()]">
              {{ compliance.Criticality }}
            </span>
          </div>
          
          <div class="compliance-body">
            <h3>{{ compliance.ComplianceItemDescription }}</h3>
            
            <div class="clean-details-grid">
              <div class="detail-row">
                <span class="detail-label">Audit ID:</span>
                <span class="detail-value">
                  <a v-if="compliance.audit_id && compliance.audit_id !== 'N/A'" 
                     href="#" 
                     class="audit-id-link" 
                     @click.prevent="handleAuditIdClick(compliance.audit_id)">
                    {{ compliance.audit_id }}
                  </a>
                  <span v-else>N/A</span>
                </span>
              </div>
              
              <div class="detail-row">
                <span class="detail-label">Audit Findings ID:</span>
                <span class="detail-value">
                  <a v-if="compliance.audit_findings_id && compliance.audit_findings_id !== 'N/A'" 
                     href="#" 
                     class="audit-id-link" 
                     @click.prevent="handleAuditLinkClick(compliance.audit_findings_id)">
                    {{ compliance.audit_findings_id }}
                  </a>
                  <span v-else>N/A</span>
                </span>
              </div>
              
              <div class="detail-row">
                <span class="detail-label">Compliance Performed By:</span>
                <span class="detail-value">{{ compliance.audit_performer_name || 'N/A' }}</span>
              </div>
              
              <div class="detail-row">
                <span class="detail-label">Compliance Approved By:</span>
                <span class="detail-value">{{ compliance.audit_approver_name || 'N/A' }}</span>
              </div>
              
              <div class="detail-row">
                <span class="detail-label">Completion Date:</span>
                <span class="detail-value">{{ formatDate(compliance.audit_date) }}</span>
              </div>
              
              <div class="detail-row">
                <span class="detail-label">Completion Status:</span>
                <span class="detail-value" :class="getAuditStatusClass(compliance.audit_findings_status)">
                  <i :class="getAuditStatusIcon(compliance.audit_findings_status)"></i>
                  {{ formatAuditStatus(compliance.audit_findings_status) }}
                </span>
              </div>
            </div>
            
            <div class="compliance-footer">
              <div class="identifier">ID: {{ compliance.Identifier }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- List View -->
      <div v-else class="compliances-list-view">
        <DynamicTable
          :data="tableData"
          :columns="visibleColumns"
          :show-pagination="true"
          :show-actions="false"
          :unique-key="'ComplianceId'"
          :default-page-size="20"
          :page-size-options="[10, 20, 50, 100, 'all']"
          @open-column-chooser="toggleColumnEditor"
        >
          <template #cell-audit_id="{ value }">
            <a v-if="value && value !== 'N/A'" href="#" class="audit-id-link" @click.prevent="handleAuditIdClick(value)">{{ value }}</a>
            <span v-else>N/A</span>
          </template>
          
          <template #cell-audit_findings_id="{ value }">
            <a v-if="value && value !== 'N/A'" href="#" class="audit-id-link" @click.prevent="handleAuditLinkClick(value)">{{ value }}</a>
            <span v-else>N/A</span>
          </template>
          
          <template #cell-audit_findings_status="{ value }">
            <div class="status-with-icon" :class="getAuditStatusClass(value)">
              <i :class="getAuditStatusIcon(value)"></i>
              <span>{{ formatAuditStatus(value) }}</span>
            </div>
          </template>
        </DynamicTable>
      </div>
    </div>

    <!-- Column Chooser Modal -->
    <div v-if="showColumnEditor" class="incident-column-editor-overlay" @click.self="toggleColumnEditor">
      <div class="incident-column-editor-modal">
        <div class="incident-column-editor-header">
          <h3>Choose Columns</h3>
          <button class="incident-column-editor-close" @click="toggleColumnEditor">&times;</button>
        </div>

        <div class="incident-column-editor-search">
          <input
            type="text"
            v-model="columnSearchQuery"
            placeholder="Search columns..."
            class="incident-column-search-input"
          />
        </div>

        <div class="incident-column-editor-actions">
          <button class="incident-column-select-btn" @click="selectAllColumns">Select All</button>
          <button class="incident-column-select-btn" @click="deselectAllColumns">Deselect All</button>
        </div>

        <div class="incident-column-editor-list">
          <div
            v-for="column in filteredColumnDefinitions"
            :key="column.key"
            class="incident-column-editor-item"
          >
            <label class="incident-column-editor-label">
              <input
                type="checkbox"
                :checked="isColumnVisible(column.key)"
                @change="toggleColumnVisibility(column.key)"
                class="incident-column-editor-checkbox"
              />
              <span class="incident-column-editor-text">{{ column.label }}</span>
            </label>
          </div>
        </div>

        <div class="incident-column-editor-footer">
          <button class="incident-column-done-btn" @click="toggleColumnEditor">Done</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import DynamicTable from '../DynamicTable.vue'
import { API_ENDPOINTS } from '../../config/api.js'
import complianceDataService from '@/services/complianceService' // NEW: Use cached compliance data

const route = useRoute()
const router = useRouter()

// Get route parameters
const type = ref(route.params.type)
const id = ref(route.params.id)
const name = ref(decodeURIComponent(route.params.name))

// State
const compliances = ref([])
const allCompliances = ref([]) // Store all compliances for filtering
const frameworks = ref([])
const loading = ref(false)
const loadingAuditInfo = ref(false)
const error = ref(null)
const selectedFormat = ref('xlsx')
const selectedFramework = ref('')
const viewMode = ref('list') // Default to list view

// Framework session state
const sessionFrameworkId = ref(null)

// Column chooser state
const showColumnEditor = ref(false)
const columnSearchQuery = ref('')
const visibleColumnKeys = ref(['audit_id', 'audit_findings_id', 'ComplianceItemDescription', 'Criticality', 'audit_findings_status', 'audit_performer_name', 'audit_approver_name', 'audit_date'])

// Computed properties
const title = computed(() => {
  if (type.value && id.value && name.value) {
    return `Compliance Audit Status - ${name.value}`
  }
  return 'Compliance Audit Status - All Compliances'
})

// Filter frameworks based on session framework ID
const filteredFrameworks = computed(() => {
  if (sessionFrameworkId.value) {
    // If there's a session framework ID, show only that framework
    return frameworks.value.filter(fw => fw.FrameworkId.toString() === sessionFrameworkId.value.toString())
  }
  // If no session framework ID, show all frameworks
  return frameworks.value
})

// Filtered compliances based on framework selection
const filteredCompliances = computed(() => {
  console.log('🔍 DEBUG: Filtering compliances in ComplianceAuditView...')
  console.log('🔍 DEBUG: Total compliances:', allCompliances.value.length)
  console.log('🔍 DEBUG: Selected framework ID:', selectedFramework.value)
  console.log('🔍 DEBUG: Session framework ID:', sessionFrameworkId.value)
  console.log('🔍 DEBUG: Available frameworks:', frameworks.value.map(f => ({ id: f.FrameworkId, name: f.FrameworkName })))
  
  if (!selectedFramework.value) {
    console.log('ℹ️ DEBUG: No framework selected, showing all compliances')
    return allCompliances.value
  }
  
  // Find framework name by ID for filtering
  const selectedFrameworkName = frameworks.value.find(f => f.FrameworkId.toString() === selectedFramework.value.toString())?.FrameworkName
  console.log('🔍 DEBUG: Selected framework name:', selectedFrameworkName)
  
  if (selectedFrameworkName) {
    const beforeCount = allCompliances.value.length
    const filtered = allCompliances.value.filter(compliance => compliance.FrameworkName === selectedFrameworkName)
    console.log('🔍 DEBUG: Filtered compliances count:', filtered.length, 'from', beforeCount)
    console.log('🔍 DEBUG: Sample compliance framework names:', filtered.slice(0, 3).map(c => c.FrameworkName))
    console.log('🔍 DEBUG: All unique framework names in compliance data:', [...new Set(allCompliances.value.map(c => c.FrameworkName))])
    return filtered
  }
  
  console.log('⚠️ DEBUG: Could not find framework name for ID:', selectedFramework.value)
  return allCompliances.value
})

// All available columns for list view
const allColumns = [
  { key: 'audit_id', label: 'Audit ID', sortable: true, slot: true, resizable: true },
  { key: 'audit_findings_id', label: 'Audit Findings ID', sortable: true, slot: true, resizable: true },
  { key: 'PolicyName', label: 'Policy', sortable: true, resizable: true },
  { key: 'SubPolicyName', label: 'Sub Policy', sortable: true, resizable: true },
  { key: 'ComplianceItemDescription', label: 'Compliance', sortable: true, resizable: true },
  { key: 'Criticality', label: 'Criticality', sortable: true, resizable: true },
  { key: 'audit_findings_status', label: 'Completion Status', sortable: true, slot: true, resizable: true },
  { key: 'audit_performer_name', label: 'Compliance Performed By', sortable: true, resizable: true },
  { key: 'audit_approver_name', label: 'Compliance Approved By', sortable: true, resizable: true },
  { key: 'audit_date', label: 'Completion Date', sortable: true, resizable: true },
  { key: 'BusinessUnitsCovered', label: 'Business Units', sortable: true, resizable: true },
  { key: 'Category', label: 'Category', sortable: true, resizable: true },
  { key: 'ComplianceType', label: 'Compliance Type', sortable: true, resizable: true },
  { key: 'MandatoryOptional', label: 'Mandatory/Optional', sortable: true, resizable: true },
  { key: 'ManualAutomatic', label: 'Manual/Automatic', sortable: true, resizable: true },
  { key: 'Impact', label: 'Impact', sortable: true, resizable: true },
  { key: 'Probability', label: 'Probability', sortable: true, resizable: true },
  { key: 'MaturityLevel', label: 'Maturity Level', sortable: true, resizable: true },
  { key: 'Status', label: 'Status', sortable: true, resizable: true },
  { key: 'RiskCategory', label: 'Risk Category', sortable: true, resizable: true }
]

// Column definitions for column chooser
const columnDefinitions = [
  { key: 'audit_id', label: 'Audit ID', defaultVisible: true },
  { key: 'audit_findings_id', label: 'Audit Findings ID', defaultVisible: true },
  { key: 'PolicyName', label: 'Policy', defaultVisible: false },
  { key: 'SubPolicyName', label: 'Sub Policy', defaultVisible: false },
  { key: 'ComplianceItemDescription', label: 'Compliance', defaultVisible: true },
  { key: 'Criticality', label: 'Criticality', defaultVisible: true },
  { key: 'audit_findings_status', label: 'Completion Status', defaultVisible: true },
  { key: 'audit_performer_name', label: 'Compliance Performed By', defaultVisible: true },
  { key: 'audit_approver_name', label: 'Compliance Approved By', defaultVisible: true },
  { key: 'audit_date', label: 'Completion Date', defaultVisible: true },
  { key: 'BusinessUnitsCovered', label: 'Business Units', defaultVisible: false },
  { key: 'Category', label: 'Category', defaultVisible: false },
  { key: 'ComplianceType', label: 'Compliance Type', defaultVisible: false },
  { key: 'MandatoryOptional', label: 'Mandatory/Optional', defaultVisible: false },
  { key: 'ManualAutomatic', label: 'Manual/Automatic', defaultVisible: false },
  { key: 'Impact', label: 'Impact', defaultVisible: false },
  { key: 'Probability', label: 'Probability', defaultVisible: false },
  { key: 'MaturityLevel', label: 'Maturity Level', defaultVisible: false },
  { key: 'Status', label: 'Status', defaultVisible: false },
  { key: 'RiskCategory', label: 'Risk Category', defaultVisible: false }
]

// Visible columns based on user selection
const visibleColumns = computed(() => {
  return allColumns.filter(col => visibleColumnKeys.value.includes(col.key))
})

// Filtered column definitions for search
const filteredColumnDefinitions = computed(() => {
  if (!columnSearchQuery.value) {
    return columnDefinitions
  }
  const query = columnSearchQuery.value.toLowerCase()
  return columnDefinitions.filter(col =>
    col.label.toLowerCase().includes(query) ||
    col.key.toLowerCase().includes(query)
  )
})

const tableData = computed(() => {
  return filteredCompliances.value.map(c => ({
    audit_id: c.audit_id || 'N/A',
    audit_findings_id: c.audit_findings_id || 'N/A',
    PolicyName: c.PolicyName || '-',
    SubPolicyName: c.SubPolicyName || '-',
    ComplianceItemDescription: c.ComplianceItemDescription,
    Criticality: c.Criticality,
    audit_findings_status: c.audit_findings_status || 'Not Audited',
    audit_performer_name: c.audit_performer_name || 'N/A',
    audit_approver_name: c.audit_approver_name || 'N/A',
    audit_date: formatDate(c.audit_date),
    BusinessUnitsCovered: c.BusinessUnitsCovered || '-',
    Category: c.Category || '-',
    ComplianceType: c.ComplianceType || '-',
    MandatoryOptional: c.MandatoryOptional || '-',
    ManualAutomatic: c.ManualAutomatic || '-',
    Impact: c.Impact || '-',
    Probability: c.Probability || '-',
    MaturityLevel: c.MaturityLevel || '-',
    Status: c.Status || '-',
    RiskCategory: c.RiskCategory || '-',
    ComplianceId: c.ComplianceId
  }))
})

// Check for selected framework from session and set it as default
const checkSelectedFrameworkFromSession = async () => {
  try {
    console.log('🔍 DEBUG: Checking for selected framework from session in ComplianceAuditView...')
    const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
    console.log('📊 DEBUG: Selected framework response:', response.data)
    
    if (response.data && response.data.success && response.data.frameworkId) {
      const frameworkIdFromSession = response.data.frameworkId
      console.log('✅ DEBUG: Found selected framework in session:', frameworkIdFromSession)
      
      // Store the session framework ID for filtering
      sessionFrameworkId.value = frameworkIdFromSession
      
      // Check if this framework exists in our loaded frameworks
      const frameworkExists = frameworks.value.find(f => f.FrameworkId.toString() === frameworkIdFromSession.toString())
      
      if (frameworkExists) {
        console.log('✅ DEBUG: Framework exists in loaded frameworks:', frameworkExists.FrameworkName)
        // Automatically select the framework from session
        selectedFramework.value = frameworkExists.FrameworkId.toString()
        console.log('✅ DEBUG: Auto-selected framework from session:', selectedFramework.value)
        console.log('✅ DEBUG: Framework name for filtering:', frameworkExists.FrameworkName)
        console.log('✅ DEBUG: selectedFramework.value after setting:', selectedFramework.value)
        console.log('✅ DEBUG: Framework ID type:', typeof selectedFramework.value)
      } else {
        console.log('⚠️ DEBUG: Framework from session (ID:', frameworkIdFromSession, ') not found in loaded frameworks')
        console.log('📋 DEBUG: Available frameworks:', frameworks.value.map(f => ({ id: f.FrameworkId, name: f.FrameworkName })))
        console.log('📋 DEBUG: Looking for framework ID:', frameworkIdFromSession, 'type:', typeof frameworkIdFromSession)
        // Clear the session framework ID since it doesn't exist
        sessionFrameworkId.value = null
      }
    } else {
      console.log('ℹ️ DEBUG: No framework found in session')
      sessionFrameworkId.value = null
    }
  } catch (error) {
    console.error('❌ DEBUG: Error checking selected framework from session:', error)
    sessionFrameworkId.value = null
  }
}

// Watch for changes in selectedFramework
watch(selectedFramework, (newValue, oldValue) => {
  console.log('🔍 DEBUG: selectedFramework changed from', oldValue, 'to', newValue)
}, { immediate: true })

// Watch for changes in frameworks
watch(frameworks, (newFrameworks) => {
  console.log('🔍 DEBUG: Frameworks loaded:', newFrameworks.length, 'frameworks')
  console.log('🔍 DEBUG: Framework IDs:', newFrameworks.map(f => f.FrameworkId))
}, { immediate: true })

// Fetch compliances on component mount
onMounted(async () => {
  // First, fetch frameworks
  await fetchFrameworks()
  
  // Check for selected framework from session after loading frameworks
  await checkSelectedFrameworkFromSession()
  
  // Then fetch compliance data (this will be filtered by the selected framework)
  await fetchCompliances()
})

// Methods
async function fetchFrameworks() {
  try {
    console.log('🔍 [ComplianceAuditView] Checking for cached framework data...')

    // ==========================================
    // NEW: Ensure compliance prefetch is running
    // ==========================================
    if (!window.complianceDataFetchPromise && !complianceDataService.hasFrameworksCache()) {
      console.log('🚀 [ComplianceAuditView] Starting compliance prefetch (user navigated directly)...')
      window.complianceDataFetchPromise = complianceDataService.fetchAllComplianceData()
    }

    if (window.complianceDataFetchPromise) {
      console.log('⏳ [ComplianceAuditView] Waiting for compliance prefetch to complete...')
      try {
        await window.complianceDataFetchPromise
        console.log('✅ [ComplianceAuditView] Prefetch completed')
      } catch (prefetchError) {
        console.warn('⚠️ [ComplianceAuditView] Prefetch failed, will fetch directly from API', prefetchError)
      }
    }
    
    // FIRST: Try to get data from cache
    if (complianceDataService.hasFrameworksCache()) {
      console.log('✅ [ComplianceAuditView] Using cached framework data')
      frameworks.value = complianceDataService.getData('frameworks') || []
      console.log(`[ComplianceAuditView] Loaded ${frameworks.value.length} frameworks from cache (prefetched on Home page)`)
    } else {
      // FALLBACK: Fetch from API if cache is empty
      console.log('⚠️ [ComplianceAuditView] No cached data found, fetching from API...')
    const response = await axios.get('/api/compliance/frameworks/public/')
    console.log('🔍 DEBUG: Frameworks API response:', response.data)
    
    if (response.data && response.data.success) {
      frameworks.value = response.data.frameworks || []
        console.log(`[ComplianceAuditView] Loaded ${frameworks.value.length} frameworks directly from API (cache unavailable)`)
        
        // Update cache so subsequent pages benefit
        complianceDataService.setData('frameworks', frameworks.value)
        console.log('ℹ️ [ComplianceAuditView] Cache updated after direct API fetch')
    } else {
      console.error('🔍 DEBUG: Frameworks API response not successful:', response.data)
      }
    }
  } catch (err) {
    console.error('Error fetching frameworks:', err)
  }
}

async function fetchCompliances() {
  try {
    loading.value = true
    error.value = null
    
    let endpoint = ''
    
    // If we have specific type and id, use the specific endpoint
    if (type.value && id.value) {
      switch(type.value) {
        case 'framework':
          endpoint = `/api/compliance/view/framework/${id.value}/`
          break
        case 'policy':
          endpoint = `/api/compliance/view/policy/${id.value}/`
          break
        case 'subpolicy':
          endpoint = `/api/compliance/view/subpolicy/${id.value}/`
          break
        default:
          throw new Error('Invalid type specified')
      }
    } else {
      // Load all compliances for audit management
      endpoint = '/api/compliance/all-for-audit-management/'
    }
    
    const response = await axios.get(endpoint)
    console.log('API Response:', response.data)
    
    if (response.data && response.data.success) {
      // Get the compliances
      const fetchedCompliances = response.data.compliances
      
      // Show loading state for audit information
      loadingAuditInfo.value = true
      
              // Fetch audit information for each compliance with better error handling
        const compliancesWithAudit = await Promise.allSettled(
          fetchedCompliances.map(async (compliance) => {
            try {
              const auditResponse = await axios.get(`/api/compliance/compliance/${compliance.ComplianceId}/audit-info/`)
              if (auditResponse.data && auditResponse.data.success) {
                return {
                  ...compliance,
                  ...auditResponse.data.data
                }
              }
              return compliance
            } catch (err) {
              // Don't log every 404 error to reduce console noise
              if (err.response && err.response.status !== 404) {
                console.error(`Error fetching audit info for compliance ${compliance.ComplianceId}:`, err)
              }
              return compliance
            }
          })
        )
      
      // Extract the results from Promise.allSettled
      const processedCompliances = compliancesWithAudit.map(result => 
        result.status === 'fulfilled' ? result.value : result.reason
      )
      
      // Store in both arrays
      allCompliances.value = processedCompliances
      compliances.value = processedCompliances
      
      console.log('🔍 DEBUG: Loaded compliances count:', processedCompliances.length)
      console.log('🔍 DEBUG: Sample compliance framework names:', processedCompliances.slice(0, 5).map(c => c.FrameworkName))
      console.log('🔍 DEBUG: Unique framework names in compliance data:', [...new Set(processedCompliances.map(c => c.FrameworkName))])
      
      // Hide loading state for audit information
      loadingAuditInfo.value = false
    } else {
      throw new Error(response.data.message || 'Failed to fetch compliances')
    }
  } catch (err) {
    console.error('Error fetching compliances:', err)
    error.value = 'Failed to fetch compliances. Please try again.'
    compliances.value = []
    allCompliances.value = []
  } finally {
    loading.value = false
  }
}

function formatDate(date) {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString()
}

function getAuditStatusClass(status) {
  if (!status) return 'not-audited'
  
  const statusLower = status.toLowerCase()
  
  // Fully Compliant / Approved - Green
  if (statusLower.includes('fully') || statusLower.includes('approved')) {
    return 'fully-compliant'
  }
  
  // Non Compliant / Rejected - Red
  if (statusLower.includes('non') || statusLower.includes('not compliant') || statusLower.includes('rejected')) {
    return 'non-compliant'
  }
  
  // Partially Compliant - Orange
  if (statusLower.includes('partially') || statusLower.includes('partial')) {
    return 'partially-compliant'
  }
  
  // Not Applicable - Gray
  if (statusLower.includes('not applicable') || statusLower.includes('n/a')) {
    return 'not-applicable'
  }
  
  // Not Audited - Light gray
  if (statusLower.includes('not audited')) {
    return 'not-audited'
  }
  
  return 'not-audited'
}

function getAuditStatusIcon(status) {
  if (!status) return 'fas fa-question-circle'
  
  const statusLower = status.toLowerCase()
  
  // Fully Compliant / Approved - Green tick
  if (statusLower.includes('fully') || statusLower.includes('approved')) {
    return 'fas fa-check-circle'
  }
  
  // Non Compliant / Rejected - Red cross
  if (statusLower.includes('non') || statusLower.includes('not compliant') || statusLower.includes('rejected')) {
    return 'fas fa-times-circle'
  }
  
  // Partially Compliant - Orange warning
  if (statusLower.includes('partially') || statusLower.includes('partial')) {
    return 'fas fa-exclamation-triangle'
  }
  
  // Not Applicable - Gray info
  if (statusLower.includes('not applicable') || statusLower.includes('n/a')) {
    return 'fas fa-info-circle'
  }
  
  // Not Audited - Gray question
  if (statusLower.includes('not audited')) {
    return 'fas fa-question-circle'
  }
  
  return 'fas fa-question-circle'
}

// Method to format the status display text for the UI
function formatAuditStatus(status) {
  if (!status) return 'Not Audited'
  
  const statusLower = status.toLowerCase()
  
  // Fully Compliant / Approved
  if (statusLower.includes('fully') || statusLower.includes('approved')) {
    return 'Fully Compliant'
  }
  
  // Non Compliant / Rejected
  if (statusLower.includes('non') || statusLower.includes('not compliant') || statusLower.includes('rejected')) {
    return 'Non Compliant'
  }
  
  // Partially Compliant
  if (statusLower.includes('partially') || statusLower.includes('partial')) {
    return 'Partially Compliant'
  }
  
  // Not Applicable
  if (statusLower.includes('not applicable') || statusLower.includes('n/a')) {
    return 'Not Applicable'
  }
  
  // Not Audited
  if (statusLower.includes('not audited')) {
    return 'Not Audited'
  }
  
  // Return the original status if no match
  return status
}

function getAuditedCount() {
  return compliances.value.filter(c => 
    c.audit_findings_status && 
    (c.audit_findings_status.toLowerCase().includes('fully') || 
     c.audit_findings_status.toLowerCase().includes('partially') || 
     c.audit_findings_status.toLowerCase().includes('non') || 
     c.audit_findings_status.toLowerCase().includes('not compliant'))
  ).length
}

function getNotAuditedCount() {
  return filteredCompliances.value.filter(c => 
    !c.audit_findings_status || 
    c.audit_findings_status.toLowerCase() === 'not audited'
  ).length
}

function handleFrameworkChange() {
  console.log('🔍 DEBUG: handleFrameworkChange called with:', selectedFramework.value)
  // Save the selected framework to session
  if (selectedFramework.value) {
    saveFrameworkToSession(selectedFramework.value)
  }
  // Filter will be applied automatically through computed property
}

// Save framework selection to session
const saveFrameworkToSession = async (frameworkId) => {
  try {
    const userId = localStorage.getItem('user_id') || 'default_user'
    console.log('🔍 DEBUG: Saving framework to session in ComplianceAuditView:', frameworkId)
    
    const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
      frameworkId: frameworkId,
      userId: userId
    })
    
    if (response.data && response.data.success) {
      console.log('✅ DEBUG: Framework saved to session successfully in ComplianceAuditView')
      console.log('🔑 DEBUG: Session key:', response.data.sessionKey)
      // Update the session framework ID
      sessionFrameworkId.value = frameworkId
    } else {
      console.error('❌ DEBUG: Failed to save framework to session in ComplianceAuditView')
    }
  } catch (error) {
    console.error('❌ DEBUG: Error saving framework to session in ComplianceAuditView:', error)
  }
}


function testFiltering() {
  console.log('🔍 DEBUG: Testing filtering...')
  console.log('🔍 DEBUG: Current selectedFramework.value:', selectedFramework.value)
  console.log('🔍 DEBUG: Current frameworks:', frameworks.value.map(f => ({ id: f.FrameworkId, name: f.FrameworkName })))
  console.log('🔍 DEBUG: Current allCompliances count:', allCompliances.value.length)
  console.log('🔍 DEBUG: Current filteredCompliances count:', filteredCompliances.value.length)
  
  // Try to set a framework manually
  if (frameworks.value.length > 0) {
    const firstFramework = frameworks.value[0]
    console.log('🔍 DEBUG: Setting framework to:', firstFramework.FrameworkId, firstFramework.FrameworkName)
    selectedFramework.value = firstFramework.FrameworkId.toString()
  }
}


function goBack() {
  router.back()
}

// Column chooser methods
const toggleColumnEditor = () => {
  showColumnEditor.value = !showColumnEditor.value
  if (!showColumnEditor.value) {
    columnSearchQuery.value = ''
  }
}

const toggleColumnVisibility = (columnKey) => {
  const index = visibleColumnKeys.value.indexOf(columnKey)
  if (index > -1) {
    visibleColumnKeys.value.splice(index, 1)
  } else {
    visibleColumnKeys.value.push(columnKey)
  }
}

const isColumnVisible = (columnKey) => {
  return visibleColumnKeys.value.includes(columnKey)
}

const selectAllColumns = () => {
  visibleColumnKeys.value = columnDefinitions.map(col => col.key)
}

const deselectAllColumns = () => {
  visibleColumnKeys.value = []
}

function handleAuditIdClick(auditId) {
  if (!auditId) return
  // Redirect to the audit report page
  router.push(`/audit-report/${auditId}`)
}

function handleAuditLinkClick(auditFindingsId) {
  if (!auditFindingsId) return
  // Redirect to the audit findings detail page
  router.push(`/audit-findings/${auditFindingsId}`)
}

async function handleExport(format) {
  try {
    console.log(`Attempting export for ${type.value} ${id.value} in ${format} format`)
    
    // Update the API endpoint URL with path parameters
    const response = await axios({
      url: `/api/export/audit-compliances/${format}/${type.value}/${id.value}/`,
      method: 'GET',
      responseType: 'blob',
      timeout: 30000,
      headers: {
        'Accept': 'application/json, application/pdf, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, text/csv, application/xml'
      }
    })

    // Check if we have a file URL in the response
    if (response.data && response.data.file_url) {
      // Open the file URL in a new tab
      window.open(response.data.file_url, '_blank');
      
      ElMessage({
        message: 'Export completed successfully! File opened in new tab.',
        type: 'success',
        duration: 3000
      })
    } else {
      // Fallback: Handle successful download as blob
      const contentType = response.headers['content-type']
      const blob = new Blob([response.data], { type: contentType })
      
      // Get filename from header or create default
      let filename = `audit_compliances_${type.value}_${id.value}.${format}`
      const disposition = response.headers['content-disposition']
      if (disposition && disposition.includes('filename=')) {
        filename = disposition.split('filename=')[1].replace(/"/g, '')
      }
      
      // Trigger download
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(link.href)
      
      ElMessage({
        message: 'Export completed successfully! File downloaded.',
        type: 'success',
        duration: 3000
      })
    }
  } catch (error) {
    console.error('Export error:', error)
    const errorMessage = error.response?.data?.message || error.message || 'Failed to export compliances'
    ElMessage({
      message: errorMessage,
      type: 'error',
      duration: 5000
    })
  }
}
</script>

<style>
.compliance-view-container {
  padding: 20px;
  width: calc(100% - 220px);
  margin: 0;
  margin-left: 220px;
  position: relative;
  box-sizing: border-box;
}

.compliance-view-container h1 {
  color: #2c3e50;
  margin-bottom: 30px;
  font-weight: 600;
}

.compliance-view-container .error-message {
  background-color: #fee2e2;
  border: 1px solid #ef4444;
  color: #b91c1c;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.compliance-view-container .loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  width: 100%;
}

.professional-loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 30px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
  max-width: 500px;
  width: 90%;
  animation: fadeIn 0.4s ease-out;
}

.loader-spinner {
  position: relative;
  width: 70px;
  height: 70px;
}

.spinner-ring {
  box-sizing: border-box;
  position: absolute;
  width: 100%;
  height: 100%;
  border: 4px solid #f0f0f0;
  border-top-color: #4f8cff;
  border-radius: 50%;
  animation: spinnerRotate 1.2s linear infinite;
}

.loader-text {
  text-align: center;
}

.loader-text h3 {
  margin: 0 0 10px 0;
  color: #344054;
  font-size: 1.2rem;
  font-weight: 600;
}

.loader-text p {
  margin: 0;
  color: #6c757d;
  font-size: 0.95rem;
  line-height: 1.5;
}

@keyframes spinnerRotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.compliance-view-container .content-wrapper {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 24px;
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

/* Filter Section Styles */
.filter-section {
  background: #f8fafc;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
  border: 1px solid #e2e8f0;
}

.filter-controls {
  display: flex;
  gap: 20px;
  align-items: end;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 200px;
}

.filter-group label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.framework-select {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background-color: #ffffff;
  color: #374151;
  font-size: 14px;
  outline: none;
  transition: all 0.2s ease;
}

.framework-select:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Data Summary Styles */
.data-summary {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  justify-content: space-around;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  min-width: 150px;
  padding: 10px 20px;
  border-radius: 6px;
  background-color: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.summary-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-value {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
}

/* New Action Bar Styling */
.action-bar {
  position: absolute;
  top: 24px;
  right: 20px;
  background: none !important;
  box-shadow: none;
  border: none;
  padding: 0;
  z-index: 10;
  margin-bottom: 50px; /* Add space below the action bar */
}

.action-buttons {
  display: flex;
  gap: 30px;
  align-items: center;
  background: none !important;
  box-shadow: none !important;
  justify-content: flex-end;
}

.export-section {
  display: flex;
  align-items: center;
  gap: 12px;
  background: none !important;
  padding: 0;
  border: none;
  box-shadow: none;
}

.format-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background-color: #f9fafb;
  color: #374151;
  font-size: 14px;
  outline: none;
  min-width: 140px;
  transition: all 0.2s ease;
}

.format-select:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Button Styles */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 40px;
  white-space: nowrap;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.btn:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: 1px solid #2563eb;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

.btn-secondary {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  color: white;
  border: 1px solid #475569;
}

.btn-secondary:hover {
  background: linear-gradient(135deg, #475569 0%, #334155 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(100, 116, 139, 0.3);
}

.btn-outline {
  background: #ffffff;
  color: #64748b;
  border: 1px solid #d1d5db;
}

.btn-outline:hover {
  background: #f8fafc;
  color: #334155;
  border-color: #94a3b8;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(100, 116, 139, 0.15);
}

.btn i {
  font-size: 14px;
}

.compliance-view-container .compliances-list-view {
  background-color: #ffffff;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  overflow: auto;
  margin-top: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  width: 100%;
}

.compliance-view-container .compliances-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

.compliance-view-container .compliances-table th {
  background-color: #f9fafb;
  padding: 12px 15px;
  text-align: left;
  font-weight: 600;
  color: #4b5563;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
  min-width: 140px;
  overflow: visible;
}

.compliance-view-container .compliances-table th:nth-child(1) {
  min-width: 120px;
}

.compliance-view-container .compliances-table th:nth-child(2) {
  min-width: 250px;
}

.compliance-view-container .compliances-table th:nth-child(3) {
  min-width: 100px;
}

.compliance-view-container .compliances-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #e5e7eb;
  color: #1f2937;
}

.compliance-view-container .compliances-table tr:last-child td {
  border-bottom: none;
}

.compliance-view-container .compliances-table tr:hover {
  background-color: #f9fafb;
}

.compliance-view-container .compliance-name {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.compliance-view-container .audit-id {
  font-family: monospace;
  color: #6b7280;
}

.compliance-view-container .compliances-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-top: 20px;
  width: 100%;
}

@media (max-width: 1600px) {
  .compliance-view-container .compliances-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 1200px) {
  .compliance-view-container .compliances-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .compliance-view-container .compliances-grid {
    grid-template-columns: 1fr;
  }
}

.compliance-view-container .compliance-card {
  transition: all 0.25s ease;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  background: #ffffff;
}

.compliance-view-container .compliance-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  border-color: #d1d5db;
}

.compliance-view-container .compliance-header {
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
}

.compliance-view-container .compliance-body {
  padding: 16px;
}

.compliance-view-container .compliance-body h3 {
  margin-top: 0;
  margin-bottom: 12px;
  color: #1f2937;
  font-size: 1.1rem;
  line-height: 1.4;
}

.compliance-view-container .compliance-footer {
  padding-top: 12px;
  margin-top: 12px;
  border-top: 1px solid #e5e7eb;
  font-size: 0.85rem;
  color: #6b7280;
}

.compliance-view-container .no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #6b7280;
  text-align: center;
}

.compliance-view-container .no-data i {
  font-size: 2rem;
  margin-bottom: 12px;
}

.compliance-view-container .criticality-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.85em;
  font-weight: 500;
}

.compliance-view-container .criticality-high { background-color: #ffebee; color: #d32f2f; }
.compliance-view-container .criticality-medium { background-color: #fff3e0; color: #f57c00; }
.compliance-view-container .criticality-low { background-color: #e8f5e9; color: #388e3c; }

.compliance-view-container .clean-details-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #f9fafb;
  border-radius: 8px;
  padding: 14px;
  margin: 15px 0;
}

.compliance-view-container .detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px dashed #e5e7eb;
  padding-bottom: 8px;
  font-size: 0.95rem;
}

.compliance-view-container .detail-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.compliance-view-container .detail-label,
.compliance-view-container .label {
  color: #4b5563;
  font-weight: 500;
  min-width: 150px;
}

.compliance-view-container .detail-value,
.compliance-view-container .value {
  color: #111827;
  font-weight: 500;
}

/* Legacy status styles - kept for card view compatibility */
.compliance-view-container .fully-compliant {
  color: #15803d;
  font-weight: 500;
}

.compliance-view-container .partially-compliant {
  color: #d97706;
  font-weight: 500;
}

.compliance-view-container .non-compliant {
  color: #dc2626;
  font-weight: 500;
}

.compliance-view-container .not-applicable {
  color: #64748b;
  font-weight: 500;
}

.compliance-view-container .not-audited {
  color: #94a3b8;
  font-style: italic;
}

.compliance-view-container .fully-compliant i {
  color: #15803d;
  margin-right: 5px;
}

.compliance-view-container .partially-compliant i {
  color: #d97706;
  margin-right: 5px;
}

.compliance-view-container .non-compliant i {
  color: #dc2626;
  margin-right: 5px;
}

.compliance-view-container .not-applicable i {
  color: #64748b;
  margin-right: 5px;
}

.compliance-view-container .not-audited i {
  color: #94a3b8;
  margin-right: 5px;
}

.compliance-view-container .audit-id-link {
  color: #2563eb;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.compliance-view-container .audit-id-link:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

/* Status with Icon Styles */
.status-with-icon {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.875rem;
  white-space: nowrap;
}

.status-with-icon i {
  font-size: 14px;
  min-width: 14px;
  display: inline-block;
}

.status-with-icon.fully-compliant {
  background-color: #dcfce7;
  color: #15803d;
  border: 1px solid #bbf7d0;
}

.status-with-icon.fully-compliant i {
  color: #15803d;
}

.status-with-icon.partially-compliant {
  background-color: #fef3c7;
  color: #d97706;
  border: 1px solid #fed7aa;
}

.status-with-icon.partially-compliant i {
  color: #d97706;
}

.status-with-icon.non-compliant {
  background-color: #fee2e2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.status-with-icon.non-compliant i {
  color: #dc2626;
}

.status-with-icon.not-applicable {
  background-color: #f1f5f9;
  color: #64748b;
  border: 1px solid #cbd5e1;
}

.status-with-icon.not-applicable i {
  color: #64748b;
}

.status-with-icon.not-audited {
  background-color: #f8fafc;
  color: #94a3b8;
  border: 1px solid #e2e8f0;
  font-style: italic;
}

.status-with-icon.not-audited i {
  color: #94a3b8;
}

/* Responsive Design */
@media (max-width: 768px) {
  .action-buttons {
    flex-direction: column;
    align-items: stretch;
    gap: 30px;
  }
  
  .export-section {
    justify-content: space-between;
  }
  
  .format-select {
    min-width: 120px;
  }
  
  .compliance-view-container {
    margin-left: 0;
    width: 100%;
    padding: 16px;
  }
  
  .compliances-grid {
    grid-template-columns: 1fr;
  }
  
  .data-summary {
    flex-direction: column;
    gap: 16px;
  }
  
  .summary-item {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  }
  
  .summary-value {
    font-size: 20px;
  }
}

@media (max-width: 640px) {
  .export-section {
    flex-direction: column;
    gap: 8px;
  }
  
  .format-select,
  .btn {
    width: 100%;
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.compliance-view-container .fa-sync {
  animation: spin 1s linear infinite;
}

/* Ensure completion status column has adequate width */
.compliance-view-container .dynamic-table th[data-key="audit_findings_status"],
.compliance-view-container .dynamic-table td[data-key="audit_findings_status"] {
  min-width: 300px !important;
  max-width: 350px !important;
  width: 300px !important;
}

/* Ensure status text doesn't get truncated */
.compliance-view-container .dynamic-table .status-with-icon {
  white-space: nowrap;
  overflow: visible;
  text-overflow: clip;
}

/* Additional table layout fixes */
.compliance-view-container .dynamic-table {
  table-layout: fixed !important;
  width: 100% !important;
  border-collapse: separate !important;
  border-spacing: 0 !important;
}

.compliance-view-container .dynamic-table th,
.compliance-view-container .dynamic-table td {
  padding: 12px 8px !important;
  border-right: 1px solid #e0e0e0 !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

/* Ensure proper spacing between columns */
.compliance-view-container .dynamic-table th:not(:last-child),
.compliance-view-container .dynamic-table td:not(:last-child) {
  border-right: 1px solid #e0e0e0 !important;
}

/* Ensure table container handles overflow properly */
.compliance-view-container .dynamic-table-container {
  overflow-x: auto !important;
  max-width: 100% !important;
}

.compliance-view-container .table-wrapper {
  overflow-x: auto !important;
  max-width: 100% !important;
}

/* Force the completion status column to maintain its width */
.compliance-view-container .dynamic-table th[data-key="audit_findings_status"],
.compliance-view-container .dynamic-table td[data-key="audit_findings_status"] {
  min-width: 200px !important;
  max-width: 200px !important;
  width: 200px !important;
  padding-right: 12px !important;
  padding-left: 12px !important;
}

/* Alternative selectors for completion status column */
.compliance-view-container .dynamic-table th:nth-child(5),
.compliance-view-container .dynamic-table td:nth-child(5) {
  min-width: 200px !important;
  max-width: 200px !important;
  width: 200px !important;
  padding-right: 12px !important;
  padding-left: 12px !important;
}

/* Target by label text */
.compliance-view-container .dynamic-table th:contains("Completion Status"),
.compliance-view-container .dynamic-table th:contains("COMPLETION STAT") {
  min-width: 300px !important;
  max-width: 350px !important;
  width: 300px !important;
}

/* Ensure the status-with-icon content fits within the column */
.compliance-view-container .dynamic-table td[data-key="audit_findings_status"] .status-with-icon {
  max-width: 100% !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  display: flex !important;
  align-items: center !important;
  gap: 6px !important;
  padding: 6px 10px !important;
  border-radius: 6px !important;
  font-weight: 500 !important;
  font-size: 0.875rem !important;
}

.compliance-view-container .dynamic-table td[data-key="audit_findings_status"] .status-with-icon span {
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  flex: 1 !important;
}

/* Ensure adjacent columns don't overlap */
.compliance-view-container .dynamic-table th:nth-child(6),
.compliance-view-container .dynamic-table td:nth-child(6) {
  min-width: 180px !important;
  padding-left: 16px !important;
}

.compliance-view-container .dynamic-table th:nth-child(7),
.compliance-view-container .dynamic-table td:nth-child(7) {
  min-width: 180px !important;
  padding-left: 16px !important;
}

/* Add some debugging styles to see column boundaries */
.compliance-view-container .dynamic-table th,
.compliance-view-container .dynamic-table td {
  border: 1px solid #ddd !important;
  position: relative !important;
}

/* Most aggressive approach - target all possible completion status columns */
.compliance-view-container .dynamic-table th,
.compliance-view-container .dynamic-table td {
  box-sizing: border-box !important;
}

/* Force specific widths for all columns to prevent overlap - optimized for full-width layout */
.compliance-view-container .dynamic-table th:nth-child(1),
.compliance-view-container .dynamic-table td:nth-child(1) { width: 8% !important; min-width: 100px !important; }

.compliance-view-container .dynamic-table th:nth-child(2),
.compliance-view-container .dynamic-table td:nth-child(2) { width: 10% !important; min-width: 120px !important; }

.compliance-view-container .dynamic-table th:nth-child(3),
.compliance-view-container .dynamic-table td:nth-child(3) { width: 25% !important; min-width: 250px !important; }

.compliance-view-container .dynamic-table th:nth-child(4),
.compliance-view-container .dynamic-table td:nth-child(4) { width: 8% !important; min-width: 100px !important; }

.compliance-view-container .dynamic-table th:nth-child(5),
.compliance-view-container .dynamic-table td:nth-child(5) { width: 15% !important; min-width: 180px !important; max-width: 200px !important; }

.compliance-view-container .dynamic-table th:nth-child(6),
.compliance-view-container .dynamic-table td:nth-child(6) { width: 12% !important; min-width: 150px !important; }

.compliance-view-container .dynamic-table th:nth-child(7),
.compliance-view-container .dynamic-table td:nth-child(7) { width: 12% !important; min-width: 150px !important; }

.compliance-view-container .dynamic-table th:nth-child(8),
.compliance-view-container .dynamic-table td:nth-child(8) { width: 10% !important; min-width: 120px !important; }

/* IMPORTANT: If changes are not visible, please refresh the page (Ctrl+F5) to clear browser cache */

/* Responsive table adjustments for full-width layout */
@media (max-width: 1600px) {
  .compliance-view-container .dynamic-table th:nth-child(3),
  .compliance-view-container .dynamic-table td:nth-child(3) { 
    width: 22% !important; 
    min-width: 200px !important; 
  }
  
  .compliance-view-container .dynamic-table th:nth-child(5),
  .compliance-view-container .dynamic-table td:nth-child(5) { 
    width: 15% !important; 
    min-width: 180px !important; 
    max-width: 180px !important; 
  }
  
  .compliance-view-container .dynamic-table th:nth-child(6),
  .compliance-view-container .dynamic-table td:nth-child(6),
  .compliance-view-container .dynamic-table th:nth-child(7),
  .compliance-view-container .dynamic-table td:nth-child(7) { 
    width: 12% !important; 
    min-width: 120px !important; 
  }
}

@media (max-width: 1400px) {
  .compliance-view-container .dynamic-table th:nth-child(3),
  .compliance-view-container .dynamic-table td:nth-child(3) { 
    width: 20% !important; 
    min-width: 180px !important; 
  }
  
  .compliance-view-container .dynamic-table th:nth-child(5),
  .compliance-view-container .dynamic-table td:nth-child(5) { 
    width: 15% !important; 
    min-width: 160px !important; 
    max-width: 180px !important; 
  }
}

@media (max-width: 1200px) {
  .compliance-view-container .dynamic-table th:nth-child(3),
  .compliance-view-container .dynamic-table td:nth-child(3) { 
    width: 18% !important; 
    min-width: 160px !important; 
  }
  
  .compliance-view-container .dynamic-table th:nth-child(5),
  .compliance-view-container .dynamic-table td:nth-child(5) { 
    width: 14% !important; 
    min-width: 140px !important; 
    max-width: 160px !important; 
  }
}

/* Column Chooser Styles */
.incident-column-editor-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
  backdrop-filter: blur(4px);
}

.incident-column-editor-modal {
  background: var(--card-bg, white);
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.incident-column-editor-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--header-bg, #f9fafb);
}

.incident-column-editor-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary, #1f2937);
}

.incident-column-editor-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-secondary, #6b7280);
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
  line-height: 1;
}

.incident-column-editor-close:hover {
  background: var(--hover-bg, #f3f4f6);
  color: var(--text-primary, #1f2937);
}

.incident-column-editor-search {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}

.incident-column-search-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--input-border, #d1d5db);
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: all 0.2s ease;
  background: var(--input-bg, white);
  color: var(--input-text, #1f2937);
}

.incident-column-search-input:focus {
  border-color: var(--primary-color, #4f7cff);
  box-shadow: 0 0 0 3px rgba(79, 124, 255, 0.1);
}

.incident-column-editor-actions {
  padding: 12px 24px;
  display: flex;
  gap: 12px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
  background: var(--secondary-bg, #f9fafb);
}

.incident-column-select-btn {
  padding: 6px 12px;
  border: 1px solid var(--border-color, #d1d5db);
  background: var(--btn-bg, white);
  color: var(--text-primary, #1f2937);
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.incident-column-select-btn:hover {
  background: var(--hover-bg, #f3f4f6);
  border-color: var(--primary-color, #4f7cff);
}

.incident-column-editor-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 24px;
  max-height: 400px;
}

.incident-column-editor-item {
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color, #f3f4f6);
}

.incident-column-editor-item:last-child {
  border-bottom: none;
}

.incident-column-editor-label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  user-select: none;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s ease;
}

.incident-column-editor-label:hover {
  background: var(--hover-bg, #f9fafb);
}

.incident-column-editor-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--primary-color, #4f7cff);
}

.incident-column-editor-text {
  font-size: 14px;
  color: var(--text-primary, #1f2937);
  font-weight: 500;
}

.incident-column-editor-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--border-color, #e5e7eb);
  display: flex;
  justify-content: flex-end;
  background: var(--footer-bg, #f9fafb);
}

.incident-column-done-btn {
  padding: 10px 24px;
  background: var(--primary-color, #4f7cff);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(79, 124, 255, 0.2);
}

.incident-column-done-btn:hover {
  background: var(--primary-hover, #3b5bdb);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(79, 124, 255, 0.3);
}

.incident-column-editor-empty {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-secondary, #6b7280);
  font-size: 14px;
}
</style>