<template>
  <div class="audit-management-container">
    <div class="header-section">
      <div class="header-title-section">
        <button class="btn-back-simple" @click="goBack" title="Go back to previous page">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h1>Compliance Management</h1>
      </div>
      <div class="header-actions">
        <!-- Export Section -->
        <div class="export-section">
          <select v-model="selectedFormat" class="format-select">
            <option value="" disabled>Select format</option>
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
      </div>
    </div>

    <!-- Filter Section -->
    <div class="filter-section">
      <div class="filter-controls" style="display: flex; flex-direction: row; align-items: flex-end; gap: 24px; flex-wrap: nowrap; justify-content: flex-start; width: 100%;">
        <div class="filter-group" style="display: flex; flex-direction: column; gap: 8px; min-width: 250px; flex: 0 0 auto;">
          <label for="framework-filter" style="font-size: 12px; font-weight: 600; color: #374151; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Filter by Framework:</label>
          <select 
            id="framework-filter" 
            v-model="selectedFramework" 
            @change="handleFrameworkChange"
            class="framework-select"
            style="padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 6px; background: #ffffff; color: #374151; font-size: 14px; font-weight: 500; outline: none; min-width: 250px;"
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
        
        <div class="filter-group" style="display: flex; flex-direction: column; gap: 8px; min-width: 200px; flex: 0 0 auto;">
          <label for="status-filter" style="font-size: 12px; font-weight: 600; color: #374151; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Filter by Status:</label>
          <select 
            id="status-filter" 
            v-model="selectedStatus" 
            @change="handleStatusChange"
            class="status-select"
            style="padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 6px; background: #ffffff; color: #374151; font-size: 14px; font-weight: 500; outline: none; min-width: 200px;"
          >
            <option value="">All Statuses</option>
            <option value="Fully Compliant">Fully Compliant</option>
            <option value="Partially Compliant">Partially Compliant</option>
            <option value="Non Compliant">Non Compliant</option>
            <option value="Not Audited">Not Audited</option>
          </select>
        </div>
        
        <div class="filter-group" style="display: flex; flex-direction: column; gap: 8px; min-width: 200px; flex: 0 0 auto;">
          <label for="category-filter" style="font-size: 12px; font-weight: 600; color: #374151; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Filter by Category:</label>
          <select 
            id="category-filter" 
            v-model="selectedCategory" 
            @change="handleCategoryChange"
            class="category-select"
            style="padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 6px; background: #ffffff; color: #374151; font-size: 14px; font-weight: 500; outline: none; min-width: 200px;"
          >
            <option value="">All Categories</option>
            <option 
              v-for="category in categories" 
              :key="category" 
              :value="category"
            >
              {{ category }}
            </option>
          </select>
        </div>
        
        <div class="filter-group" style="display: flex; flex-direction: column; gap: 8px; min-width: 200px; flex: 0 0 auto;">
          <label for="business-unit-filter" style="font-size: 12px; font-weight: 600; color: #374151; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Filter by Business Unit:</label>
          <select 
            id="business-unit-filter" 
            v-model="selectedBusinessUnit" 
            @change="handleBusinessUnitChange"
            class="business-unit-select"
            style="padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 6px; background: #ffffff; color: #374151; font-size: 14px; font-weight: 500; outline: none; min-width: 200px;"
          >
            <option value="">All Business Units</option>
            <option 
              v-for="businessUnit in businessUnits" 
              :key="businessUnit" 
              :value="businessUnit"
            >
              {{ businessUnit }}
            </option>
          </select>
        </div>
        
        <div class="filter-group" style="display: flex; flex-direction: column; gap: 8px; min-width: auto; flex: 0 0 auto; margin-left: auto;">
          <label style="visibility: hidden; height: 20px;">.</label>
          <button class="btn btn-secondary" @click="clearFilters">
            <i class="fas fa-times"></i>
            Clear Filters
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
      <div v-if="filteredCompliances.length > 0" class="data-summary">
        <div class="summary-item">
          <span class="summary-label">Total Compliances:</span>
          <span class="summary-value">{{ filteredCompliances.length }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Fully Compliant:</span>
          <span class="summary-value">{{ getStatusCount('Fully Compliant') }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Partially Compliant:</span>
          <span class="summary-value">{{ getStatusCount('Partially Compliant') }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Non Compliant:</span>
          <span class="summary-value">{{ getStatusCount('Non Compliant') }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Not Audited:</span>
          <span class="summary-value">{{ getStatusCount('Not Audited') }}</span>
        </div>
      </div>
      
      
      <div v-if="!filteredCompliances.length" class="no-data">
        <i class="fas fa-inbox"></i>
        <p>No compliances found</p>
      </div>
      
      <!-- Compliance List -->
      <div v-else class="compliances-list-view">
        <DynamicTable
          :data="tableData"
          :columns="visibleColumns"
          :show-pagination="true"
          :show-actions="false"
          :unique-key="'ComplianceId'"
          :default-page-size="20"
          :page-size-options="[10, 20, 50, 100, 'all']"
          :get-row-class="getRowClass"
          @open-column-chooser="toggleColumnEditor"
          @row-click="handleRowClick"
        >
                     <template #cell-AuditId="{ value }">
             <span v-if="value !== 'N/A'" class="audit-id-link" title="Click row to view audit details">
               <i class="fas fa-external-link-alt"></i> {{ value }}
             </span>
             <span v-else>{{ value }}</span>
           </template>
           
           <template #cell-CompletionStatus="{ value }">
             <span class="status-text" :class="getComplianceStatusClass(value)">
               {{ value }}
             </span>
           </template>
           
            <template #cell-Criticality="{ value }">
              <span class="criticality-text" :class="getCriticalityClass(value)">
                <span class="criticality-dot" :class="getCriticalityClass(value)"></span>
                {{ value }}
              </span>
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
          <button class="incident-column-select-btn" @click="resetColumnSelection">Reset to Default</button>
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
          <div v-if="filteredColumnDefinitions.length === 0" class="incident-column-editor-empty">
            No columns found matching your search.
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
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import DynamicTable from '../DynamicTable.vue'
import { API_ENDPOINTS } from '../../config/api.js'

const router = useRouter()

// State
const compliances = ref([])
const frameworks = ref([])
const categories = ref([])
const businessUnits = ref([])
const error = ref(null)
const selectedFormat = ref('')
const selectedFramework = ref('')
const selectedStatus = ref('')
const selectedCategory = ref('')
const selectedBusinessUnit = ref('')

// Framework session state
const sessionFrameworkId = ref(null)

// Column chooser state - default visible columns matching current display
const showColumnEditor = ref(false)
const columnSearchQuery = ref('')
const visibleColumnKeys = ref(['AuditId', 'PolicyName', 'SubPolicyName', 'ComplianceItemDescription', 'BusinessUnitsCovered', 'RiskCategory', 'Criticality', 'CompletionStatus', 'CompletionDate'])

// Computed properties
const filteredFrameworks = computed(() => {
  if (sessionFrameworkId.value) {
    // If there's a session framework ID, show only that framework
    return frameworks.value.filter(fw => fw.FrameworkId.toString() === sessionFrameworkId.value.toString())
  }
  // If no session framework ID, show all frameworks
  return frameworks.value
})

const filteredCompliances = computed(() => {
  let filtered = compliances.value || []
  
  console.log('🔍 DEBUG: Filtering compliances...')
  console.log('🔍 DEBUG: Total compliances:', filtered.length)
  console.log('🔍 DEBUG: Selected framework ID:', selectedFramework.value)
  console.log('🔍 DEBUG: Selected framework ID type:', typeof selectedFramework.value)
  console.log('🔍 DEBUG: Session framework ID:', sessionFrameworkId.value)

  // If we have a selected framework, filter by framework name
  if (selectedFramework.value) {
    // Find framework name by ID for filtering (convert both to strings for comparison)
    const selectedFrameworkName = frameworks.value.find(f => f.FrameworkId.toString() === selectedFramework.value.toString())?.FrameworkName
    console.log('🔍 DEBUG: Selected framework name:', selectedFrameworkName)
    console.log('🔍 DEBUG: Available frameworks:', frameworks.value.map(f => ({ id: f.FrameworkId, name: f.FrameworkName })))
    
    if (selectedFrameworkName) {
      const beforeCount = filtered.length
      filtered = filtered.filter(compliance => {
        const matches = compliance.FrameworkName === selectedFrameworkName
        if (!matches && beforeCount <= 5) {
          console.log('🔍 DEBUG: Compliance framework mismatch:', compliance.FrameworkName, '!==', selectedFrameworkName)
        }
        return matches
      })
      console.log('🔍 DEBUG: Filtered compliances count:', filtered.length, 'from', beforeCount)
      console.log('🔍 DEBUG: Sample filtered compliance framework names:', filtered.slice(0, 3).map(c => c.FrameworkName))
    } else {
      console.log('⚠️ DEBUG: Could not find framework name for ID:', selectedFramework.value)
      console.log('⚠️ DEBUG: Available framework IDs:', frameworks.value.map(f => f.FrameworkId))
      console.log('⚠️ DEBUG: This means framework ID', selectedFramework.value, 'does not exist in the loaded frameworks list')
      console.log('⚠️ DEBUG: Showing all compliances since selected framework is not in the list')
    }
  } else {
    console.log('ℹ️ DEBUG: No framework selected, showing all compliances')
  }

  // Note: Status filtering is done at row level in tableData computed property
  // to ensure accurate filtering of individual audit findings

  if (selectedCategory.value) {
    filtered = filtered.filter(compliance => compliance.RiskCategory === selectedCategory.value)
  }

  if (selectedBusinessUnit.value) {
    filtered = filtered.filter(compliance => compliance.BusinessUnitsCovered === selectedBusinessUnit.value)
  }

  return filtered
})

// All available columns for list view - matching auditor module columns
const allColumns = [
  { key: 'AuditId', label: 'Audit ID', sortable: true, slot: true, width: '100px', resizable: true },
  { key: 'title', label: 'Title', sortable: true, width: '200px', resizable: true },
  { key: 'framework', label: 'Framework', sortable: true, width: '150px', resizable: true },
  { key: 'PolicyName', label: 'Policy', sortable: true, width: '180px', resizable: true },
  { key: 'SubPolicyName', label: 'Subpolicy', sortable: true, width: '180px', resizable: true },
  { key: 'ComplianceItemDescription', label: 'Compliance', sortable: true, width: '380px', resizable: true },
  { key: 'date', label: 'Due Date', sortable: true, width: '120px', resizable: true },
  { key: 'BusinessUnitsCovered', label: 'Business Unit', sortable: true, width: '150px', resizable: true, slot: true },
  { key: 'RiskCategory', label: 'Category', sortable: true, width: '160px', resizable: true },
  { key: 'auditType', label: 'Audit Type', sortable: true, width: '120px', resizable: true },
  { key: 'Criticality', label: 'Criticality', sortable: true, slot: true, width: '160px', resizable: true },
  { key: 'CompletionStatus', label: 'Status', sortable: true, slot: true, width: '140px', resizable: true },
  { key: 'scope', label: 'Scope', sortable: true, width: '200px', resizable: true },
  { key: 'objective', label: 'Objective', sortable: true, width: '200px', resizable: true },
  { key: 'role', label: 'Role', sortable: true, width: '120px', resizable: true },
  { key: 'responsibility', label: 'Responsibility', sortable: true, width: '180px', resizable: true },
  { key: 'assignee', label: 'Assignee', sortable: true, width: '140px', resizable: true },
  { key: 'auditor', label: 'Auditor', sortable: true, width: '140px', resizable: true },
  { key: 'reviewer', label: 'Reviewer', sortable: true, width: '140px', resizable: true },
  { key: 'frequency', label: 'Frequency', sortable: true, width: '100px', resizable: true },
  { key: 'CompletionDate', label: 'Completion Date', sortable: true, width: '140px', resizable: true },
  { key: 'review_status', label: 'Review Status', sortable: true, width: '130px', resizable: true },
  { key: 'reviewer_comments', label: 'Reviewer Comments', sortable: true, width: '200px', resizable: true },
  { key: 'evidence', label: 'Evidence', sortable: true, width: '150px', resizable: true },
  { key: 'comments', label: 'Comments', sortable: true, width: '200px', resizable: true },
  { key: 'assigned_date', label: 'Assigned Date', sortable: true, width: '140px', resizable: true },
  { key: 'review_start_date', label: 'Review Start Date', sortable: true, width: '150px', resizable: true },
  { key: 'review_date', label: 'Review Date', sortable: true, width: '130px', resizable: true }
]

// Column definitions for column chooser - matching auditor module
const columnDefinitions = [
  { key: 'AuditId', label: 'Audit ID', defaultVisible: true },
  { key: 'title', label: 'Title', defaultVisible: false },
  { key: 'framework', label: 'Framework', defaultVisible: false },
  { key: 'PolicyName', label: 'Policy', defaultVisible: true },
  { key: 'SubPolicyName', label: 'Subpolicy', defaultVisible: true },
  { key: 'ComplianceItemDescription', label: 'Compliance', defaultVisible: true },
  { key: 'date', label: 'Due Date', defaultVisible: false },
  { key: 'BusinessUnitsCovered', label: 'Business Unit', defaultVisible: true },
  { key: 'RiskCategory', label: 'Category', defaultVisible: true },
  { key: 'auditType', label: 'Audit Type', defaultVisible: false },
  { key: 'Criticality', label: 'Criticality', defaultVisible: true },
  { key: 'CompletionStatus', label: 'Status', defaultVisible: true },
  { key: 'scope', label: 'Scope', defaultVisible: false },
  { key: 'objective', label: 'Objective', defaultVisible: false },
  { key: 'role', label: 'Role', defaultVisible: false },
  { key: 'responsibility', label: 'Responsibility', defaultVisible: false },
  { key: 'assignee', label: 'Assignee', defaultVisible: false },
  { key: 'auditor', label: 'Auditor', defaultVisible: false },
  { key: 'reviewer', label: 'Reviewer', defaultVisible: false },
  { key: 'frequency', label: 'Frequency', defaultVisible: false },
  { key: 'CompletionDate', label: 'Completion Date', defaultVisible: true },
  { key: 'review_status', label: 'Review Status', defaultVisible: false },
  { key: 'reviewer_comments', label: 'Reviewer Comments', defaultVisible: false },
  { key: 'evidence', label: 'Evidence', defaultVisible: false },
  { key: 'comments', label: 'Comments', defaultVisible: false },
  { key: 'assigned_date', label: 'Assigned Date', defaultVisible: false },
  { key: 'review_start_date', label: 'Review Start Date', defaultVisible: false },
  { key: 'review_date', label: 'Review Date', defaultVisible: false }
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
  const flattenedData = []
  
  filteredCompliances.value.forEach(compliance => {
    // If there are audit findings, create a row for each finding
    if (compliance.AuditFindings && compliance.AuditFindings.length > 0) {
      compliance.AuditFindings.forEach(finding => {
        const rowStatus = getStatusText(finding.CompletionStatus)
        flattenedData.push({
          ComplianceId: compliance.ComplianceId,
          AuditId: finding.AuditId || 'N/A',
          ComplianceItemDescription: compliance.ComplianceItemDescription || 'N/A',
          BusinessUnitsCovered: compliance.BusinessUnitsCovered || 'N/A',
          RiskCategory: compliance.RiskCategory || 'N/A',
          Criticality: compliance.Criticality || 'N/A',
          CompletionStatus: rowStatus,
          PolicyName: compliance.PolicyName || 'N/A',
          SubPolicyName: compliance.SubPolicyName || 'N/A',
          CompletionDate: finding.CompletionDate ? new Date(finding.CompletionDate).toLocaleDateString() : 'N/A'
        })
      })
    } else {
      // If no audit findings, create a single row with default values
      flattenedData.push({
        ComplianceId: compliance.ComplianceId,
        AuditId: 'N/A',
        ComplianceItemDescription: compliance.ComplianceItemDescription || 'N/A',
        BusinessUnitsCovered: compliance.BusinessUnitsCovered || 'N/A',
        RiskCategory: compliance.RiskCategory || 'N/A',
        Criticality: compliance.Criticality || 'N/A',
        CompletionStatus: 'Not Audited',
        PolicyName: compliance.PolicyName || 'N/A',
        SubPolicyName: compliance.SubPolicyName || 'N/A',
        CompletionDate: 'N/A'
      })
    }
  })
  
  // Apply status filter at row level for accurate filtering
  let filteredRows = flattenedData
  if (selectedStatus.value) {
    filteredRows = flattenedData.filter(row => row.CompletionStatus === selectedStatus.value)
  }
  
  // Sort by audit status: audited first, not audited last
  return filteredRows.sort((a, b) => {
    const aStatus = a.CompletionStatus
    const bStatus = b.CompletionStatus
    
    // Define priority order: Fully Compliant > Partially Compliant > Non Compliant > Not Audited
    const statusPriority = {
      'Fully Compliant': 1,
      'Partially Compliant': 2,
      'Non Compliant': 3,
      'Not Audited': 4
    }
    
    const aPriority = statusPriority[aStatus] || 5
    const bPriority = statusPriority[bStatus] || 5
    
    return aPriority - bPriority
  })
})

// Check for selected framework from session and set it as default
const checkSelectedFrameworkFromSession = async () => {
  try {
    console.log('🔍 DEBUG: Checking for selected framework from session in AuditManagementView...')
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
      } else {
        console.log('⚠️ DEBUG: Framework from session (ID:', frameworkIdFromSession, ') not found in loaded frameworks')
        console.log('📋 DEBUG: Available frameworks:', frameworks.value.map(f => ({ id: f.FrameworkId, name: f.FrameworkName })))
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

// Watch for selectedFramework changes
watch(selectedFramework, (newVal, oldVal) => {
  console.log('🔄 DEBUG: selectedFramework changed from', oldVal, 'to', newVal)
  console.log('🔄 DEBUG: selectedFramework type:', typeof newVal)
})

// Watch for compliances changes
watch(compliances, (newVal) => {
  console.log('📦 DEBUG: compliances updated, count:', newVal?.length)
  if (newVal && newVal.length > 0) {
    console.log('📦 DEBUG: Sample compliance:', newVal[0])
    console.log('📦 DEBUG: Unique framework names:', [...new Set(newVal.map(c => c.FrameworkName))])
  }
})

// Fetch data on component mount
onMounted(async () => {
  // First, fetch frameworks
  await fetchFrameworks()
  
  // Check for selected framework from session after loading frameworks
  await checkSelectedFrameworkFromSession()
  
  // Then fetch compliance data (categories and business units will be extracted from compliance data)
  await fetchAllCompliances()
})

// Methods
async function fetchFrameworks() {
  try {
    // Fetch ALL frameworks (not just compliance frameworks) to ensure session framework is included
    const response = await axios.get(API_ENDPOINTS.FRAMEWORKS)
    console.log('📋 DEBUG: Raw frameworks response:', response.data)
    
    if (response.data) {
      // Transform the data to match frontend expectations
      frameworks.value = response.data.map(framework => ({
        FrameworkId: framework.FrameworkId,
        FrameworkName: framework.FrameworkName,
        Category: framework.Category,
        ActiveInactive: framework.ActiveInactive,
        FrameworkDescription: framework.FrameworkDescription
      }))
      console.log('📋 DEBUG: Transformed frameworks:', frameworks.value.length, 'frameworks')
      console.log('📋 DEBUG: Framework IDs:', frameworks.value.map(f => f.FrameworkId))
    }
  } catch (err) {
    console.error('Error fetching frameworks:', err)
  }
}

function extractCategoriesFromCompliances() {
  // Extract unique categories from compliances data
  try {
    if (compliances.value && compliances.value.length > 0) {
      const uniqueCategories = [...new Set(
        compliances.value
          .map(c => c.RiskCategory || c.Category) // Try both field names
          .filter(cat => cat && cat.trim() !== '')
      )].sort()
      
      categories.value = uniqueCategories
      console.log('📋 DEBUG: Extracted categories:', categories.value)
      console.log('📋 DEBUG: Sample compliance categories:', compliances.value.slice(0, 3).map(c => ({ 
        RiskCategory: c.RiskCategory, 
        Category: c.Category 
      })))
    } else {
      categories.value = []
      console.log('📋 DEBUG: No compliances available to extract categories from')
    }
  } catch (err) {
    console.error('Error extracting categories:', err)
    categories.value = []
  }
}

function extractBusinessUnitsFromCompliances() {
  // Extract unique business units from compliances data
  try {
    if (compliances.value && compliances.value.length > 0) {
      const uniqueBusinessUnits = [...new Set(
        compliances.value
          .map(c => c.BusinessUnitsCovered || c.BusinessUnit) // Try both field names
          .filter(bu => bu && bu.trim() !== '')
      )].sort()
      
      businessUnits.value = uniqueBusinessUnits
      console.log('🏢 DEBUG: Extracted business units:', businessUnits.value)
      console.log('🏢 DEBUG: Sample compliance business units:', compliances.value.slice(0, 3).map(c => ({ 
        BusinessUnitsCovered: c.BusinessUnitsCovered, 
        BusinessUnit: c.BusinessUnit 
      })))
    } else {
      businessUnits.value = []
      console.log('🏢 DEBUG: No compliances available to extract business units from')
    }
  } catch (err) {
    console.error('Error extracting business units:', err)
    businessUnits.value = []
  }
}


async function fetchAllCompliances() {
  try {
    error.value = null
    
    console.log('🔍 DEBUG: Fetching all compliances...')
    const response = await axios.get('/api/compliance/all-for-audit-management/public/')
    console.log('🔍 DEBUG: API Response:', response.data)
    
    // The backend returns the data in a specific format
    if (response.data && response.data.success) {
      compliances.value = response.data.compliances || []
      console.log('🔍 DEBUG: Loaded compliances count:', compliances.value.length)
      console.log('🔍 DEBUG: Sample compliance framework names:', compliances.value.slice(0, 5).map(c => c.FrameworkName))
      console.log('🔍 DEBUG: Unique framework names in data:', [...new Set(compliances.value.map(c => c.FrameworkName))])
      
      // Debug: Log sample compliance data structure
      if (compliances.value.length > 0) {
        console.log('🔍 DEBUG: Sample compliance object structure:', Object.keys(compliances.value[0]))
        console.log('🔍 DEBUG: Sample compliance data:', compliances.value[0])
      }
      
      // Extract categories and business units from the loaded compliance data
      extractCategoriesFromCompliances()
      extractBusinessUnitsFromCompliances()
    } else {
      throw new Error('Invalid response format from server')
    }
  } catch (err) {
    console.error('Error fetching compliances:', err)
    error.value = 'Failed to fetch compliances. Please try again.'
    compliances.value = []
  }
}

function handleFrameworkChange() {
  // Save the selected framework to session
  // If empty string (All Frameworks), save null to session
  if (selectedFramework.value) {
    saveFrameworkToSession(selectedFramework.value)
  } else {
    // Clear framework selection from session when "All Frameworks" is selected
    saveFrameworkToSession(null)
  }
  // Filter will be applied automatically through computed property
}

// Save framework selection to session
const saveFrameworkToSession = async (frameworkId) => {
  try {
    const userId = localStorage.getItem('user_id') || 'default_user'
    console.log('🔍 DEBUG: Saving framework to session in AuditManagementView:', frameworkId)
    
    const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
      frameworkId: frameworkId,
      userId: userId
    })
    
    if (response.data && response.data.success) {
      console.log('✅ DEBUG: Framework saved to session successfully in AuditManagementView')
      console.log('🔑 DEBUG: Session key:', response.data.sessionKey)
      // Update the session framework ID
      sessionFrameworkId.value = frameworkId
    } else {
      console.error('❌ DEBUG: Failed to save framework to session in AuditManagementView')
    }
  } catch (error) {
    console.error('❌ DEBUG: Error saving framework to session in AuditManagementView:', error)
  }
}

function handleStatusChange() {
  // Filter will be applied automatically through computed property
}

function handleCategoryChange() {
  // Filter will be applied automatically through computed property
}

function handleBusinessUnitChange() {
  // Filter will be applied automatically through computed property
}

function clearFilters() {
  selectedFramework.value = ''
  selectedStatus.value = ''
  selectedCategory.value = ''
  selectedBusinessUnit.value = ''
  // Clear session framework ID when clearing filters
  sessionFrameworkId.value = null
}

function getStatusCount(status) {
  let count = 0
  console.log('🔍 DEBUG: getStatusCount called for status:', status)
  console.log('🔍 DEBUG: Total filtered compliances:', filteredCompliances.value.length)
  
  filteredCompliances.value.forEach((compliance, index) => {
    console.log(`🔍 DEBUG: Processing compliance ${index + 1}:`, {
      ComplianceId: compliance.ComplianceId,
      Status: compliance.Status,
      AuditFindings: compliance.AuditFindings?.length || 0,
      hasAuditFindings: !!(compliance.AuditFindings && compliance.AuditFindings.length > 0)
    })
    
    // First check if there are audit findings
    if (compliance.AuditFindings && compliance.AuditFindings.length > 0) {
      compliance.AuditFindings.forEach(finding => {
        const findingStatus = getStatusText(finding.CompletionStatus)
        console.log(`🔍 DEBUG: Finding status: ${findingStatus}, looking for: ${status}`)
        if (findingStatus === status) {
          count++
          console.log(`✅ DEBUG: Found match! Count now: ${count}`)
        }
      })
    } else {
      // If no audit findings, check the compliance status directly
      const complianceStatus = getStatusText(compliance.Status)
      console.log(`🔍 DEBUG: No audit findings, checking compliance status: ${complianceStatus}, looking for: ${status}`)
      
      if (complianceStatus === status) {
        count++
        console.log(`✅ DEBUG: Found match in compliance status! Count now: ${count}`)
      } else if (status === 'Not Audited' && !compliance.AuditFindings) {
        count++
        console.log(`✅ DEBUG: No audit findings, counting as Not Audited. Count now: ${count}`)
      }
    }
  })
  
  console.log(`🔍 DEBUG: Final count for ${status}: ${count}`)
  return count
}

function getComplianceStatusClass(status) {
  if (!status) return 'not-audited'
  
  const statusLower = status.toLowerCase()
  
  // Map numeric status codes to readable status
  if (status === '0' || statusLower.includes('not started')) {
    return 'not-audited'
  }
  
  if (status === '1' || statusLower.includes('in progress')) {
    return 'partially-compliant'
  }
  
  if (status === '2' || statusLower.includes('completed')) {
    return 'fully-compliant'
  }
  
  if (status === '3' || statusLower.includes('not applicable')) {
    return 'non-compliant'
  }
  
  if (statusLower.includes('fully compliant')) {
    return 'fully-compliant'
  }
  
  if (statusLower.includes('partially compliant')) {
    return 'partially-compliant'
  }
  
  if (statusLower.includes('non compliant')) {
    return 'non-compliant'
  }
  
  if (statusLower.includes('not audited')) {
    return 'not-audited'
  }
  
  return 'not-audited'
}


function getStatusText(status) {
  if (!status) return 'Not Audited'
  
  // Convert numeric status to text
  switch (status.toString()) {
    case '0':
      return 'Not Audited'
    case '1':
      return 'Partially Compliant'
    case '2':
      return 'Fully Compliant'
    case '3':
      return 'Non Compliant'
    default:
      return status // Return as-is if it's already text
  }
}

function handleAuditClick(auditId) {
  if (!auditId || auditId === 'N/A') return
  console.log('Navigating to audit details:', auditId)
  try {
    // Navigate to audit details/tasks page
    router.push(`/audit/${auditId}/tasks`)
  } catch (error) {
    console.error('Error navigating to audit details:', error)
    ElMessage({
      message: 'Error navigating to audit details. Please try again.',
      type: 'error',
      duration: 3000
    })
  }
}

function handleRowClick(row) {
  // Navigate to audit details when clicking anywhere on the row
  const auditId = row.AuditId
  if (auditId && auditId !== 'N/A') {
    handleAuditClick(auditId)
  }
}

function getRowClass(row) {
  // Add clickable class if row has a valid AuditId
  if (row.AuditId && row.AuditId !== 'N/A') {
    return 'clickable-audit-row'
  }
  return 'non-clickable-audit-row'
}



function getCriticalityClass(criticality) {
  if (!criticality) return 'unknown'
  
  const criticalityLower = criticality.toLowerCase()
  
  if (criticalityLower.includes('high')) {
    return 'high'
  }
  
  if (criticalityLower.includes('medium')) {
    return 'medium'
  }
  
  if (criticalityLower.includes('low')) {
    return 'low'
  }
  
  return 'unknown'
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

const resetColumnSelection = () => {
  visibleColumnKeys.value = columnDefinitions
    .filter(col => col.defaultVisible)
    .map(col => col.key)
}

async function handleExport(format) {
  try {
    console.log(`Attempting export for compliances in ${format} format`)
    
    // Prepare export data (filtered compliances)
    const exportData = tableData.value;
    const payload = {
      export_format: format,
      compliance_data: exportData,
      user_id: 'default_user',
      file_name: 'compliance_management_export'
    };
    
    const response = await axios.post(API_ENDPOINTS.EXPORT_COMPLIANCE_MANAGEMENT, payload);
    const result = response.data;
    
    if (result.success && result.file_url && result.file_name) {
      // Try to open the file URL in a new tab, fallback to download if it fails
      try {
        const newWindow = window.open(result.file_url, '_blank');
        if (newWindow) {
          ElMessage({
            message: 'Export completed successfully! File opened in new tab.',
            type: 'success',
            duration: 3000
          })
        } else {
          // Fallback to download if popup is blocked
          const fileRes = await fetch(result.file_url);
          const blob = await fileRes.blob();
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', result.file_name);
          document.body.appendChild(link);
          link.click();
          link.remove();
          window.URL.revokeObjectURL(url);
          ElMessage({
            message: 'Export completed successfully! File downloaded.',
            type: 'success',
            duration: 3000
          })
        }
      } catch (downloadErr) {
        // Fallback to download if window.open fails
        const fileRes = await fetch(result.file_url);
        const blob = await fileRes.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', result.file_name);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        ElMessage({
          message: 'Export completed successfully! File downloaded.',
          type: 'success',
          duration: 3000
        })
        console.error(downloadErr);
      }
    } else {
      ElMessage({
        message: 'Export failed: ' + (result.error || 'Unknown error'),
        type: 'error',
        duration: 5000
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

<style scoped>
.audit-management-container {
   padding: 20px;
  width: calc(100% - 240px);
  margin: 0;
  margin-left: 230px;
  margin-right: 0;
  position: relative;
  box-sizing: border-box;
  background: #ffffff;
  min-height: 100vh;
  max-width: 100vw;
  overflow-x: hidden;
}

/* Header Section Styles */
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 24px 0;
  border-bottom: none;
}

.header-title-section {
  display: flex;
  align-items: center;
  gap: 16px;
  
}

.audit-management-container h1 {
  color: #1e293b;
  margin: 0;
  
  font-weight: 700;
  font-size: 2rem;
  position: relative;
}

.audit-management-container h1::after {
  display: none;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}

.audit-management-container .error-message {
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


@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.audit-management-container .content-wrapper {
  background: transparent;
  padding: 0;
  width: 100%;
  box-sizing: border-box;
  overflow: visible;
  margin-top: 32px;
}

/* Filter Section Styles */
.filter-section {
  background: #f8fafc;
  border-radius: 8px;
  padding: 24px;
  margin: 32px 0;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.filter-controls {
  display: flex;
  gap: 24px;
  align-items: flex-end;
  flex-wrap: nowrap;
  justify-content: flex-start;
  width: 100%;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 200px;
  flex: 0 0 auto;
}

.filter-group:last-child {
  margin-left: auto;
  min-width: 70;
  flex: 0 0 auto;
}

.filter-group label {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.framework-select,
.status-select,
.category-select,
.business-unit-select {
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #ffffff;
  color: #374151;
  font-size: 14px;
  font-weight: 500;
  outline: none;
  transition: all 0.2s ease;
  min-width: 200px;
}

.framework-select:hover,
.status-select:hover,
.category-select:hover,
.business-unit-select:hover {
  border-color: #9ca3af;
}

.framework-select:focus,
.status-select:focus,
.category-select:focus,
.business-unit-select:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Data Summary Styles */
.data-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
  padding: 0;
  background: transparent;
  border: none;
  justify-content: stretch;
  box-shadow: none;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 13px 17px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
  position: relative;
  overflow: hidden;
  transition: all 0.2s ease;
}

.summary-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: #2d3748;
}

.summary-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.summary-item:nth-child(1)::before {
  background: #2d3748;
}

.summary-item:nth-child(2)::before {
  background: #059669;
}

.summary-item:nth-child(3)::before {
  background: #d97706;
}

.summary-item:nth-child(4)::before {
  background: #dc2626;
}

.summary-item:nth-child(5)::before {
  background: #6b7280;
}

.summary-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  text-align: center;
  line-height: 1.4;
}

.summary-value {
  font-size: 18px;
  font-weight: 700;
  color: #1a202c;
}

/* Export Section Styling */
.export-section {
  display: flex;
  align-items: center;
  gap: 12px;
  background: transparent;
  padding: 0;
  border: none;
  box-shadow: none;
  min-width: 200px;
}

.format-select {
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
  outline: none !important;
  font-weight: 500 !important;
  transition: all 0.2s ease;
}

.format-select:hover {
  border-color: #cbd5e1 !important;
}

.format-select:focus {
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

/* Button Styles */
.audit-management-container .btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 40px;
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.audit-management-container .btn:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.audit-management-container .btn-primary {
  background-color: #4f8cff;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  padding: 8px 16px;
  font-size: 0.85rem;
  text-transform: none;
  letter-spacing: normal;
  box-shadow: 0 2px 4px rgba(79, 140, 255, 0.2);
}

.audit-management-container .btn-primary:hover {
  background-color: #3d7aff;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(79, 140, 255, 0.3);
}

.audit-management-container .btn-primary:disabled {
  background-color: #adb5bd;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.audit-management-container .btn-secondary {
  background: #e8ecf2;
  color: rgb(101, 98, 98);
  font-weight: 400;
  padding: 2px 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 0.55rem;
  border-radius: 6px;
}

.audit-management-container .btn-secondary:hover {
  background: #f2f2f4;
  border-color: #eff1f4;
  transform: translateY(-1px);
}

.audit-management-container .btn-back-simple {
  background: transparent;
  border: none;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: opacity 0.2s ease;
  color: #000000;
  font-size: 16px;
  min-width: auto;
  height: auto;
  box-shadow: none;
}

.audit-management-container .btn-back-simple:hover {
  background: transparent;
  color: #000000;
  opacity: 0.7;
  transform: none;
  box-shadow: none;
  border: none;
}

.audit-management-container .btn-back-simple:active {
  transform: none;
  box-shadow: none;
  opacity: 0.5;
}

.audit-management-container .btn-back-simple i {
  font-size: 16px;
  color: #000000;
}

.audit-management-container .btn i {
  font-size: 14px;
}

.audit-management-container .audits-list-view {
  background-color: transparent;
  border-radius: 0;
  border: none;
  overflow: auto;
  margin-top: 20px;
  box-shadow: none;
  width: 100%;
}

.audit-management-container .compliances-list-view {
  background-color: transparent;
  border-radius: 0;
  border: none;
  overflow: visible;
  margin-top: 20px;
  box-shadow: none;
  width: 100%;
  padding: 0;
   max-width: 100%;
}

.audit-management-container .no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #6b7280;
  text-align: center;
}

.audit-management-container .no-data i {
  font-size: 2rem;
  margin-bottom: 12px;
}

.audit-management-container .audit-findings-link {
  color: #2563eb;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 4px;
  border-radius: 4px;
  background: rgba(37, 99, 235, 0.05);
}

.audit-management-container .audit-findings-link:hover {
  color: #1d4ed8;
  background: rgba(37, 99, 235, 0.1);
  text-decoration: none;
  transform: translateY(-1px);
}

.audit-management-container .audit-findings-link i {
  font-size: 12px;
  opacity: 0.8;
}

/* Status Text Styles */
.status-text {
  font-weight: 500;
  font-size: 0.875rem;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: break-word;
  line-height: 1.4;
}

/* Table Header Text Wrapping */
:deep(.dynamic-table th) {
  white-space: normal !important;
  word-wrap: break-word;
  word-break: keep-all;
  line-height: 1.4;
  padding: 12px 8px !important;
  text-align: center;
  vertical-align: middle;
  hyphens: none;
}

/* Specific header styling for multi-word headers */
:deep(.dynamic-table th:nth-child(2)), /* Policy */
:deep(.dynamic-table th:nth-child(3)), /* Subpolicy */
:deep(.dynamic-table th:nth-child(8)) { /* Completion Status */
  white-space: normal !important;
  word-wrap: break-word;
  word-break: keep-all;
  line-height: 1.3;
  padding: 12px 8px !important;
  font-size: 0.875rem;
  font-weight: 600;
  hyphens: none;
  overflow-wrap: break-word;
}

/* Ensure table cells have proper spacing */
:deep(.dynamic-table td) {
  padding: 10px 8px !important;
  vertical-align: middle;
}

/* Completion Status column specific styling */
:deep(.dynamic-table td:nth-child(8)) {
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: break-word;
  overflow: visible;
  text-overflow: unset;
  min-width: 320px;
  line-height: 1.4;
}

/* Compliance Status Classes */
.status-text.fully-compliant {
  color: #16a34a;
}

.status-text.partially-compliant {
  color: #d97706;
}

.status-text.non-compliant {
  color: #dc2626;
}

.status-text.not-audited {
  color: #6b7280;
}

/* Criticality Text Classes */
.criticality-text {
  font-weight: 600;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.criticality-text.high {
  color: #dc2626;
}

.criticality-text.medium {
  color: #d97706;
}

.criticality-text.low {
  color: #16a34a;
}

.criticality-text.unknown {
  color: #64748b;
}

/* Criticality Dot Styles */
.criticality-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}

.criticality-dot.high {
  background-color: #dc2626;
}

.criticality-dot.medium {
  background-color: #d97706;
}

.criticality-dot.low {
  background-color: #16a34a;
}

.criticality-dot.unknown {
  background-color: #64748b;
}

/* Remove dynamic table container styling */
:deep(.dynamic-table-container) {
  background: transparent !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  border: none !important;
  padding: 0 !important;
  margin: 0 !important;
  overflow: visible !important;
}

:deep(.dynamic-table-container .table-wrapper) {
  margin-top: 0 !important;
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
}

/* Table Responsive Adjustments */
:deep(.dynamic-table) {
  min-width: 100%;
  table-layout: fixed;
}

:deep(.dynamic-table th),
:deep(.dynamic-table td) {
  border: 1px solid #e5e7eb;
}

:deep(.dynamic-table tbody tr td) {
  background: #ffffff !important;
}

/* Make table rows clickable */
:deep(.dynamic-table tbody tr.clickable-audit-row) {
  cursor: pointer;
  transition: all 0.2s ease;
}

:deep(.dynamic-table tbody tr.clickable-audit-row:hover) {
  background: #f0f7ff !important;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.dynamic-table tbody tr.non-clickable-audit-row) {
  cursor: default;
}

:deep(.dynamic-table tbody tr.non-clickable-audit-row:hover) {
  background: #f9fafb !important;
}

/* Prevent link styling conflicts - make audit ID look like regular text but with icon */
.audit-management-container .audit-id-link {
  color: inherit;
  text-decoration: none;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  pointer-events: none; /* Prevent link clicks since row handles navigation */
}

.audit-management-container .audit-id-link i {
  font-size: 12px;
  opacity: 0.7;
  color: #2563eb;
}

/* Force proper word wrapping for compliance headers */
:deep(.dynamic-table th:nth-child(2)), /* Policy */
:deep(.dynamic-table th:nth-child(3)) { /* Subpolicy */
  word-break: keep-all !important;
  overflow-wrap: break-word !important;
  hyphens: none !important;
  white-space: normal !important;
  text-align: center !important;
}

/* Responsive Design */
@media (max-width: 768px) {
  .audit-management-container {
    margin-left: 0;
    width: 100%;
    padding: 20px;
  }
  
  /* Adjust table for mobile */
  :deep(.dynamic-table) {
    font-size: 0.8rem;
  }
  
  :deep(.dynamic-table th),
  :deep(.dynamic-table td) {
    padding: 8px 4px !important;
  }
  
  .header-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
    padding: 20px 0;
  }
  
  .header-title-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    width: 100%;
  }
  
  .audit-management-container h1 {
    font-size: 2rem;
    margin: 0;
  }
  
  .btn-back-simple {
    align-self: flex-start;
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .export-section {
    flex: 1;
    justify-content: flex-start;
    min-width: 250px;
  }
  
  .format-select {
    min-width: 140px;
  }
  
  .filter-controls {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .filter-group {
    min-width: 100%;
    flex: none;
  }
  
  .filter-group:last-child {
    margin-left: 0;
  }
  
  .framework-select,
  .status-select,
  .category-select,
  .business-unit-select {
    min-width: 100%;
  }
  
  .data-summary {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .summary-item {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    width: 100%;
  }
  
  .summary-value {
    font-size: 28px;
  }
  
  .content-wrapper {
    padding: 0;
  }
  
  /* Responsive table column adjustments */
  .compliances-list-view {
    overflow-x: auto;
  }
  
  .compliances-list-view .dynamic-table {
    min-width: 1200px;
  }
  
  .compliances-list-view .dynamic-table th,
  .compliances-list-view .dynamic-table td {
    padding: 8px 6px;
    font-size: 12px;
  }
  
  .compliances-list-view .status-with-icon {
    font-size: 0.75rem;
    padding: 4px 6px;
    white-space: normal;
    line-height: 1.2;
  }
  
  .compliances-list-view .status-with-icon span {
    word-wrap: break-word;
    word-break: break-word;
    overflow-wrap: break-word;
  }
}

@media (max-width: 640px) {
  .audit-management-container {
    padding: 16px;
  }
  
  .header-section {
    padding: 16px 0;
    gap: 16px;
  }
  
  .header-title-section {
    gap: 10px;
  }
  
  .audit-management-container h1 {
    font-size: 1.8rem;
    margin: 0;
  }
  
  .btn-back-simple {
    font-size: 14px;
  }
  
  .header-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .export-section {
    flex-direction: column;
    gap: 8px;
    min-width: 100%;
  }
  
  .format-select,
  .btn {
    width: 100%;
  }
  
  .filter-section {
    padding: 20px;
  }
  
  .data-summary {
    gap: 12px;
  }
  
  .summary-item {
    padding: 16px;
  }
  
  .summary-value {
    font-size: 24px;
  }
  
  /* Extra responsive table adjustments for very small screens */
  .compliances-list-view .dynamic-table {
    min-width: 1000px;
  }
  
  .compliances-list-view .dynamic-table th,
  .compliances-list-view .dynamic-table td {
    padding: 6px 4px;
    font-size: 11px;
  }
  
  .compliances-list-view .status-with-icon {
    font-size: 0.7rem;
    padding: 3px 4px;
    line-height: 1.1;
  }
  
  .compliances-list-view .criticality-badge {
    font-size: 10px;
    padding: 2px 6px;
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
  background: white;
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
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f9fafb;
}

.incident-column-editor-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.incident-column-editor-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
  line-height: 1;
}

.incident-column-editor-close:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.incident-column-editor-search {
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.incident-column-search-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: all 0.2s ease;
  background: white;
  color: #1f2937;
}

.incident-column-search-input:focus {
  border-color: #4f7cff;
  box-shadow: 0 0 0 3px rgba(79, 124, 255, 0.1);
}

.incident-column-editor-actions {
  padding: 12px 24px;
  display: flex;
  gap: 12px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.incident-column-select-btn {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  background: white;
  color: #1f2937;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.incident-column-select-btn:hover {
  background: #f3f4f6;
  border-color: #4f7cff;
}

.incident-column-editor-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 24px;
  max-height: 400px;
}

.incident-column-editor-item {
  padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
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
  background: #f9fafb;
}

.incident-column-editor-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #4f7cff;
}

.incident-column-editor-text {
  font-size: 14px;
  color: #1f2937;
  font-weight: 500;
}

.incident-column-editor-footer {
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  background: #f9fafb;
}

.incident-column-done-btn {
  padding: 10px 24px;
  background: #4f7cff;
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
  background: #3b5bdb;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(79, 124, 255, 0.3);
}

.incident-column-editor-empty {
  text-align: center;
  padding: 40px 20px;
  color: #6b7280;
  font-size: 14px;
}
</style>
