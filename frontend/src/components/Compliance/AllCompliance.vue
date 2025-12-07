<template>
  <div class="compliance-container">
    <div class="compliance-view-header">
      <h2 class="compliance-view-title">Control Management</h2>
      <div class="compliance-header-actions">
        <!-- View Toggle removed - only list view available -->
        
        <!-- Export controls -->
        <div class="compliance-export-controls">
          <select v-model="exportFormat" class="compliance-export-format-select">
            <option value="" disabled>Select format</option>
            <option value="xlsx">Excel (.xlsx)</option>
            <option value="csv">CSV (.csv)</option>
            <option value="pdf">PDF (.pdf)</option>
            <option value="json">JSON (.json)</option>
            <option value="xml">XML (.xml)</option>
            <option value="txt">Text (.txt)</option>
          </select>
          <button @click="exportCompliances" class="compliance-export-btn" :disabled="isExporting">
            <i v-if="!isExporting" class="fas fa-download"></i>
            <span v-if="isExporting">Exporting...</span>
            <span v-else>Export</span>
          </button>
        </div>
      </div>
    </div>


    <!-- Loading State -->
    

    <!-- Breadcrumbs -->
    <div class="breadcrumbs" v-if="breadcrumbs.length > 0">
      <div v-for="(crumb, index) in breadcrumbs" :key="crumb.id" class="breadcrumb-chip">
        {{ crumb.name }}
        <span class="breadcrumb-close" @click="goToStep(index)">&times;</span>
      </div>
    </div>

    <div class="compliance-content-wrapper">
      <!-- Frameworks Section -->
      <template v-if="showFrameworks">
        <div class="compliance-section-header">Frameworks</div>
        
        <!-- List View for Frameworks -->
        <div class="compliance-list-view">
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
                <tr v-for="fw in filteredFrameworks" :key="fw.id" @click="selectFramework(fw)" class="clickable-row">
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
        
        <!-- List View for Policies -->
        <div class="compliance-list-view">
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
        
        <!-- List View for Subpolicies -->
        <div class="compliance-list-view">
          <div class="compliance-dynamic-table-wrapper">
            <table class="compliance-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Description</th>
                  <th>Control</th>
                  <th>Duration</th>
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
                  <td data-label="Duration">{{ subpolicy.permanent_temporary }}</td>
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
        </div>
        
        <div v-if="loading" class="compliance-loading-spinner">
          <i class="fas fa-circle-notch fa-spin"></i>
          <span>Loading controls...</span>
        </div>
        
        <div v-else-if="!hasCompliances" class="compliance-no-data">
          <i class="fas fa-inbox"></i>
          <p>No controls found for this subpolicy</p>
        </div>
        
        <!-- List View -->
        <div class="compliance-list-view">
          <div class="compliance-dynamic-table-wrapper">
            <DynamicTable
              :data="filteredCompliances"
              :columns="tableColumns"
              uniqueKey="id"
              :showPagination="true"
              :showActions="true"
            >
              <template #actions="{ row }">
                <button class="compliance-action-btn" @click="handleViewCompliance(row)"><i class="fas fa-eye"></i></button>
              </template>
            </DynamicTable>
          </div>
        </div>
      </template>
    </div>

    <!-- Versions Modal -->
    <div v-if="showVersionsModal" class="modal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ versionModalTitle }}</h3>
          <button class="close-btn" @click="closeVersionsModal">&times;</button>
        </div>
        <div class="modal-body">
          <div v-if="versions.length === 0" class="no-versions">
            No versions found.
          </div>
          <div v-else class="version-grid">
            <div v-for="version in versions" :key="version.id" class="version-card">
              <div class="version-header">
                <span class="version-number">Version {{ version.version }}</span>
                <div class="version-badges">
                  <span class="status-badge" :class="statusClass(version.status)">{{ version.status }}</span>
                  <span class="status-badge" :class="statusClass(version.activeInactive)">{{ version.activeInactive }}</span>
                </div>
              </div>
              <div class="version-details">
                <p class="version-desc">{{ version.description }}</p>
                <div class="version-info-grid">
                  <div class="info-group">
                    <span class="info-label">Maturity Level:</span>
                    <span class="info-value">{{ version.maturityLevel }}</span>
                  </div>
                  <div class="info-group">
                    <span class="info-label">Type:</span>
                    <span class="info-value">{{ version.mandatoryOptional }} | {{ version.manualAutomatic }}</span>
                  </div>
                  <div class="info-group">
                    <span class="info-label">Criticality:</span>
                    <span class="info-value" :class="'criticality-' + version.criticality.toLowerCase()">
                      {{ version.criticality }}
                    </span>
                  </div>
                  <div class="info-group" v-if="version.isRisk">
                    <span class="info-label">Risk Status:</span>
                    <span class="info-value risk">Risk Identified</span>
                  </div>
                </div>
                <div class="version-metadata">
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

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { PopupService } from '@/modules/popup'
import DynamicTable from '../DynamicTable.vue'
import AccessUtils from '@/utils/accessUtils'
import { API_ENDPOINTS } from '../../config/api.js'
import complianceDataService from '@/services/complianceService' // NEW: Use cached compliance data

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
// Removed viewMode - only list view is available
// const expandedCompliance = ref(null)
const router = useRouter()

// Framework session state
const sessionFrameworkId = ref(null)

// Export state
const exportFormat = ref('')
const isExporting = ref(false)

// Define columns for DynamicTable
const tableColumns = [
  { key: 'identifier', label: 'ID', sortable: true },
  { key: 'name', label: 'Control', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'category', label: 'Criticality', sortable: true },
  { key: 'maturityLevel', label: 'Maturity Level', sortable: true },
  { key: 'mandatoryOptional', label: 'Type', sortable: true },
  { key: 'version', label: 'Version', sortable: true },
  { key: 'createdBy', label: 'Created By', sortable: true },
  { key: 'createdDate', label: 'Created Date', sortable: true },
]

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

// Filter frameworks based on session framework ID
const filteredFrameworks = computed(() => {
  if (sessionFrameworkId.value) {
    // If there's a session framework ID, show only that framework
    return frameworks.value.filter(fw => fw.id.toString() === sessionFrameworkId.value.toString())
  }
  // If no session framework ID, show all frameworks
  return frameworks.value
})

// View toggle logic removed - only list view is available

const hasCompliances = computed(() => {
  return selectedSubpolicy.value && 
         selectedSubpolicy.value.compliances && 
         selectedSubpolicy.value.compliances.length > 0;
})

// Replace the filtered computed properties
const filteredCompliances = computed(() => {
  if (!selectedSubpolicy.value || !selectedSubpolicy.value.compliances) return [];
  return selectedSubpolicy.value.compliances; // Return all compliances without filtering
});

// Check for selected framework from session and set it as default
const checkSelectedFrameworkFromSession = async () => {
  try {
    console.log('🔍 DEBUG: Checking for selected framework from session in AllCompliance...')
    const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
    console.log('📊 DEBUG: Selected framework response:', response.data)
    
    if (response.data && response.data.success && response.data.frameworkId) {
      const frameworkIdFromSession = response.data.frameworkId
      console.log('✅ DEBUG: Found selected framework in session:', frameworkIdFromSession)
      
      // Store the session framework ID for filtering
      sessionFrameworkId.value = frameworkIdFromSession
      
      // Check if this framework exists in our loaded frameworks
      const frameworkExists = frameworks.value.find(f => f.id.toString() === frameworkIdFromSession.toString())
      
      if (frameworkExists) {
        console.log('✅ DEBUG: Framework exists in loaded frameworks:', frameworkExists.name)
        // Automatically select the framework from session
        await selectFramework(frameworkExists)
        console.log('✅ DEBUG: Auto-selected framework from session')
      } else {
        console.log('⚠️ DEBUG: Framework from session (ID:', frameworkIdFromSession, ') not found in loaded frameworks')
        console.log('📋 DEBUG: Available frameworks:', frameworks.value.map(f => ({ id: f.id, name: f.name })))
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

// Lifecycle
onMounted(async () => {
  try {
    loading.value = true
    console.log('🔍 [AllCompliance] Checking for cached framework data...')
    
    // ==========================================
    // NEW: Ensure compliance prefetch is running
    // ==========================================
    if (!window.complianceDataFetchPromise && !complianceDataService.hasFrameworksCache()) {
      console.log('🚀 [AllCompliance] Starting compliance prefetch (user navigated directly)...')
      window.complianceDataFetchPromise = complianceDataService.fetchAllComplianceData()
    }

    if (window.complianceDataFetchPromise) {
      console.log('⏳ [AllCompliance] Waiting for compliance prefetch to complete...')
      try {
        await window.complianceDataFetchPromise
        console.log('✅ [AllCompliance] Prefetch completed')
      } catch (prefetchError) {
        console.warn('⚠️ [AllCompliance] Prefetch failed, will fetch directly from API', prefetchError)
      }
    }
    
    // FIRST: Try to get data from cache
    if (complianceDataService.hasFrameworksCache()) {
      console.log('✅ [AllCompliance] Using cached framework data')
      const cachedFrameworks = complianceDataService.getData('frameworks') || []
      
      frameworks.value = cachedFrameworks.map(framework => ({
        id: framework.FrameworkId || framework.id,
        name: framework.FrameworkName || framework.name,
        category: framework.FrameworkCategory || framework.category || 'General',
        status: framework.Status || framework.status || 'Active',
        description: framework.Description || framework.description || '',
        versions: framework.versions || []
      }))
      console.log(`[AllCompliance] Loaded ${frameworks.value.length} frameworks from cache (prefetched on Home page)`)
      
      // Check for selected framework from session after loading frameworks
      await checkSelectedFrameworkFromSession()
    } else {
      // FALLBACK: Fetch from API if cache is empty
      console.log('⚠️ [AllCompliance] No cached data found, fetching from API...')
      const response = await axios.get(API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_FRAMEWORKS)
      console.log('Frameworks response:', response.data)
      
      if (response.data && Array.isArray(response.data)) {
        frameworks.value = response.data.map(framework => ({
          id: framework.id,
          name: framework.name,
          category: framework.category || 'General',
          status: framework.status || 'Active',
          description: framework.description || '',
          versions: framework.versions || []
        }))
        console.log(`[AllCompliance] Loaded ${frameworks.value.length} frameworks directly from API (cache unavailable)`)
        
        // Update cache so subsequent pages benefit
        complianceDataService.setData('frameworks', response.data)
        console.log('ℹ️ [AllCompliance] Cache updated after direct API fetch')
        
        // Check for selected framework from session after loading frameworks
        await checkSelectedFrameworkFromSession()
      } else {
        console.error('Invalid frameworks response format:', response.data)
        frameworks.value = []
        error.value = 'Invalid response format from server'
      }
    }
  } catch (err) {
    // Check if it's an access control error
    if (err.response && [401, 403].includes(err.response.status)) {
      AccessUtils.showViewAllComplianceDenied();
      return;
    }
    
    error.value = 'Failed to load frameworks'
    console.error('Error fetching frameworks:', err.response?.data || err.message)
    frameworks.value = []
    PopupService.error('Failed to load frameworks. Please refresh the page and try again.', 'Loading Error')
  } finally {
    loading.value = false
  }
})

// Methods
// setViewMode method removed - only list view is available

async function selectFramework(fw) {
  try {
    loading.value = true
    selectedFramework.value = fw
    selectedPolicy.value = null
    selectedSubpolicy.value = null
    
    // Save the selected framework to session
    await saveFrameworkToSession(fw.id)
    
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
    // Check if it's an access control error
    if (err.response && [401, 403].includes(err.response.status)) {
      AccessUtils.showViewAllComplianceDenied();
      return;
    }
    
    error.value = 'Failed to load policies'
    console.error('Error fetching policies:', err)
    policies.value = []
    PopupService.error('Failed to load policies. Please try selecting a different framework.', 'Loading Error')
  } finally {
    loading.value = false
  }
}

// Save framework selection to session
const saveFrameworkToSession = async (frameworkId) => {
  try {
    const userId = localStorage.getItem('user_id') || 'default_user'
    console.log('🔍 DEBUG: Saving framework to session in AllCompliance:', frameworkId)
    
    const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
      frameworkId: frameworkId,
      userId: userId
    })
    
    if (response.data && response.data.success) {
      console.log('✅ DEBUG: Framework saved to session successfully in AllCompliance')
      console.log('🔑 DEBUG: Session key:', response.data.sessionKey)
      // Update the session framework ID
      sessionFrameworkId.value = frameworkId
    } else {
      console.error('❌ DEBUG: Failed to save framework to session in AllCompliance')
    }
  } catch (error) {
    console.error('❌ DEBUG: Error saving framework to session in AllCompliance:', error)
  }
}

async function selectPolicy(policy) {
  try {
    loading.value = true
    selectedPolicy.value = policy
    selectedSubpolicy.value = null
    
    // Get subpolicies for the selected policy using the correct endpoint and param
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
    PopupService.error('Failed to load subpolicies. Please try selecting a different policy.', 'Loading Error')
  } finally {
    loading.value = false
  }
}

async function selectSubpolicy(subpolicy) {
  try {
    loading.value = true;
    selectedSubpolicy.value = subpolicy;
    
            const response = await axios.get(API_ENDPOINTS.COMPLIANCE_SUBPOLICY_COMPLIANCES(subpolicy.id));
    console.log('Subpolicy compliances response:', response.data);
    
    if (response.data && response.data.success) {
      // Enhanced logging for debugging
      if (response.data.compliances.length > 0) {
        const firstCompliance = response.data.compliances[0];
        console.log('DETAILED COMPLIANCE OBJECT:', JSON.stringify(firstCompliance, null, 2));
        
        // Display all field names and values for better debugging
        console.log('COMPLIANCE FIELD VALUES:');
        Object.keys(firstCompliance).forEach(key => {
          console.log(`- ${key}: ${JSON.stringify(firstCompliance[key])}`);
        });
      }
      
      // Store the original compliance objects as they come from the API
      selectedSubpolicy.value = {
        ...subpolicy,
        compliances: response.data.compliances.map(compliance => {
          return {
            // IMPORTANT: Use the exact PascalCase field names from the API
            id: compliance.ComplianceId,
            name: compliance.ComplianceItemDescription,
            description: compliance.ComplianceItemDescription,
            status: compliance.Status,
            category: compliance.Criticality,
            maturityLevel: compliance.MaturityLevel,
            mandatoryOptional: compliance.MandatoryOptional,
            manualAutomatic: compliance.ManualAutomatic,
            createdBy: compliance.CreatedByName,
            createdDate: compliance.CreatedByDate,
            identifier: compliance.Identifier,
            version: compliance.ComplianceVersion,
            isRisk: compliance.IsRisk,
            
            // Keep the original Pascal case names for these fields
            PossibleDamage: compliance.PossibleDamage,
            mitigation: compliance.mitigation,
            SeverityRating: compliance.Impact,
            Probability: compliance.Probability,
            PermanentTemporary: compliance.PermanentTemporary,
            ActiveInactive: compliance.ActiveInactive,
            
            // Store the original object to access all fields in the expanded view
            originalData: compliance
          };
        })
      };
    } else {
      selectedSubpolicy.value.compliances = [];
    }
  } catch (err) {
    // Check if it's an access control error
    if (err.response && [401, 403].includes(err.response.status)) {
      AccessUtils.showViewAllComplianceDenied();
      return;
    }
    
    console.error('Error fetching subpolicy compliances:', err);
    error.value = 'Failed to load compliances';
    selectedSubpolicy.value.compliances = [];
  } finally {
    loading.value = false;
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
    // If there's a session framework ID, we should still filter to show only that framework
    // but not auto-select it
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

// function categoryIcon(category) {
//   switch ((category || '').toLowerCase()) {
//     case 'governance': return 'fas fa-shield-alt'
//     case 'access control': return 'fas fa-user-shield'
//     case 'asset management': return 'fas fa-boxes'
//     case 'cryptography': return 'fas fa-key'
//     case 'data management': return 'fas fa-database'
//     case 'device management': return 'fas fa-mobile-alt'
//     case 'risk management': return 'fas fa-exclamation-triangle'
//     case 'supplier management': return 'fas fa-handshake'
//     case 'business continuity': return 'fas fa-business-time'
//     case 'privacy': return 'fas fa-user-secret'
//     case 'system protection': return 'fas fa-shield-virus'
//     case 'incident response': return 'fas fa-ambulance'
//     default: return 'fas fa-file-alt'
//   }
// }

function statusClass(status) {
  if (!status) return ''
  const s = status.toLowerCase()
  // Check inactive FIRST because "INACTIVE" contains "ACTIVE"
  if (s.includes('inactive')) return 'inactive'
  if (s.includes('active')) return 'active'
  if (s.includes('scheduled')) return 'scheduled'
  if (s.includes('pending')) return 'pending'
  if (s.includes('under') && s.includes('review')) return 'under-review'
  return ''
}

const viewAllCompliances = (type, id, name) => {
  router.push({
    name: 'ComplianceView',
    params: {
      type: type,
      id: id,
      name: encodeURIComponent(name)
    }
  });
};



const exportCompliances = () => {
  console.log('Exporting compliances...');
  isExporting.value = true;
  
  // Determine what to export based on current selection
  let dataToExport = [];
  let exportOptions = {};
  
  if (selectedSubpolicy.value && selectedSubpolicy.value.compliances) {
    // Export compliances for selected subpolicy
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
    exportOptions = {
      item_type: 'subpolicy',
      item_id: selectedSubpolicy.value.id,
      filters: {
        subpolicy_id: selectedSubpolicy.value.id
      }
    };
  } else if (selectedPolicy.value) {
    // Export compliances for selected policy
    dataToExport = []; // Would need to fetch policy compliances
    exportOptions = {
      item_type: 'policy',
      item_id: selectedPolicy.value.id,
      filters: {
        policy_id: selectedPolicy.value.id
      }
    };
  } else if (selectedFramework.value) {
    // Export compliances for selected framework
    dataToExport = []; // Would need to fetch framework compliances
    exportOptions = {
      item_type: 'framework',
      item_id: selectedFramework.value.id,
      filters: {
        framework_id: selectedFramework.value.id
      }
    };
  } else {
    // Export all compliances
    dataToExport = [];
    exportOptions = {
      item_type: 'all',
      filters: {}
    };
  }
  
  console.log('Export data:', { dataToExport, exportOptions, format: exportFormat.value });
  console.log('API endpoint:', API_ENDPOINTS.COMPLIANCE_EXPORT);
  
  // Only send necessary fields to reduce payload size
  const trimmedData = dataToExport.map(compliance => ({
    ComplianceId: compliance.ComplianceId,
    ComplianceItemDescription: compliance.ComplianceItemDescription,
    Status: compliance.Status,
    Criticality: compliance.Criticality,
    MaturityLevel: compliance.MaturityLevel,
    MandatoryOptional: compliance.MandatoryOptional,
    ManualAutomatic: compliance.ManualAutomatic,
    CreatedByName: compliance.CreatedByName,
    CreatedByDate: compliance.CreatedByDate,
    ComplianceVersion: compliance.ComplianceVersion,
    Identifier: compliance.Identifier,
    SubPolicyName: compliance.SubPolicyName,
    PolicyName: compliance.PolicyName,
    FrameworkName: compliance.FrameworkName
  }));
  
  // Try the risk export endpoint first since we know it works
  console.log('Trying risk export endpoint for compliance data...');
  axios.post(API_ENDPOINTS.EXPORT_RISK_REGISTER, {
    export_format: exportFormat.value,
    risk_data: trimmedData,
    user_id: 'default_user',
    file_name: 'compliance_export'
  })
  .then(async response => {
    console.log('Export successful:', response.data);
    console.log('Response structure:', Object.keys(response.data));
    
    // Use the same response handling as RiskRegisterList
    const result = response.data;
    
    if (result.success && result.file_url && result.file_name) {
      console.log('File URL found:', result.file_url);
      console.log('File name:', result.file_name);
      
      // Try to open the file URL in a new tab, fallback to download if it fails
      try {
        console.log('Attempting to open file in new tab...');
        const newWindow = window.open(result.file_url, '_blank');
        console.log('Window result:', newWindow);
        if (newWindow) {
          console.log('File opened successfully in new tab');
          PopupService.success('Export completed successfully! File opened in new tab.');
        } else {
          console.log('Popup blocked, falling back to download');
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
          PopupService.success('Export completed successfully! File downloaded.');
        }
      } catch (downloadErr) {
        console.error('Download error:', downloadErr);
        // Fallback to download if window.open fails
        try {
          console.log('Attempting final download fallback...');
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
          PopupService.success('Export completed successfully! File downloaded.');
        } catch (finalErr) {
          console.error('Final download fallback failed:', finalErr);
          PopupService.error('Export completed but failed to open/download file. Please check the file URL manually.');
        }
        console.error(downloadErr);
      }
    } else {
      console.error('Export failed or incomplete response:', result);
      PopupService.error('Export failed: ' + (result.error || 'No file URL received from server'));
    }
    
    isExporting.value = false;
  })
  .catch(async error => {
    console.error('Risk export endpoint failed:', error);
    console.error('Error response:', error.response?.data);
    
    // Try the compliance export endpoint as fallback
    try {
      console.log('Trying compliance export endpoint as fallback...');
      const altResponse = await axios.post(API_ENDPOINTS.COMPLIANCE_EXPORT, {
        export_format: exportFormat.value,
        risk_data: trimmedData,
        user_id: 'default_user',
        file_name: 'compliance_export'
      });
      
      console.log('Alternative export successful:', altResponse.data);
      
             // Use the same response handling for compliance endpoint
       const altResult = altResponse.data;
       
       if (altResult.success && altResult.file_url && altResult.file_name) {
         console.log('File URL found from compliance endpoint:', altResult.file_url);
         
         // Try to open the file URL in a new tab
         try {
           const newWindow = window.open(altResult.file_url, '_blank');
           if (newWindow) {
             PopupService.success('Export completed successfully via compliance endpoint! File opened in new tab.');
           } else {
             // Fallback to download
             const fileRes = await fetch(altResult.file_url);
             const blob = await fileRes.blob();
             const url = window.URL.createObjectURL(blob);
             const link = document.createElement('a');
             link.href = url;
             link.setAttribute('download', altResult.file_name);
             document.body.appendChild(link);
             link.click();
             link.remove();
             window.URL.revokeObjectURL(url);
             PopupService.success('Export completed successfully via compliance endpoint! File downloaded.');
           }
         } catch (downloadErr) {
           console.error('Compliance endpoint download failed:', downloadErr);
           PopupService.error('Export completed but failed to open/download file.');
         }
       } else {
         PopupService.error('Export failed via compliance endpoint: ' + (altResult.error || 'No file URL received'));
       }
      
      isExporting.value = false;
    } catch (altError) {
      console.error('Alternative export endpoint also failed:', altError);
      
      // Check if this is an access control error first
      if (!AccessUtils.handleApiError(error, 'export compliances')) {
        // Only show generic error if it's not an access denied error
        PopupService.error('Export failed. Please try again.');
      }
      
      isExporting.value = false;
    }
  });
}

// const handleComplianceExpand = (compliance) => {
//   if (expandedCompliance.value === compliance.id) {
//     expandedCompliance.value = null;
//   } else {
//     expandedCompliance.value = compliance.id;
//   }
// };

// Add method to format mitigation display
// const formatMitigation = (mitigation) => {
//   if (!mitigation) {
//     return 'Not specified';
//   }
//   
//   // Check if it's JSON format
//   if (typeof mitigation === 'string' && (mitigation.startsWith('[') || mitigation.startsWith('{'))) {
//     try {
//       const parsed = JSON.parse(mitigation);
//       
//       // If it's an array of steps
//       if (Array.isArray(parsed)) {
//         return parsed.map((step, index) => `${index + 1}. ${step}`).join('\n');
//       }
//       
//       // If it's an object, extract meaningful values
//       if (typeof parsed === 'object') {
//         if (parsed.steps && Array.isArray(parsed.steps)) {
//           return parsed.steps.map((step, index) => `${index + 1}. ${step}`).join('\n');
//         }
//         if (parsed.description) {
//           return parsed.description;
//         }
//         // Convert object to readable format
//         return Object.entries(parsed)
//           .map(([key, value]) => `${key}: ${value}`)
//           .join('\n');
//       }
//       
//       return String(parsed);
//     } catch (e) {
//       // If JSON parsing fails, treat as plain text
//       return mitigation;
//     }
//   }
//   
//   // Return as plain text
//   return mitigation;
// };

// Add this utility function for truncating descriptions
function truncateDescription(desc) {
  if (!desc) return '';
  const maxLen = 80;
  return desc.length > maxLen ? desc.slice(0, maxLen) + '...' : desc;
}

// Add methods for actions
function handleViewCompliance(row) {
  // Show control details modal
  showControlDetailsModal(row);
}

function showControlDetailsModal(compliance) {
  // Create a modal to show control details
  const modalContent = `
    <div class="control-details-modal">
      <div class="modal-header">
        <h3>Control Details</h3>
        <button class="modal-close" onclick="this.closest('.control-details-modal').remove()">&times;</button>
      </div>
      <div class="modal-body">
        <div class="detail-section">
          <h4>Basic Information</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <label>Title:</label>
              <span>${compliance.name || 'Not specified'}</span>
            </div>
            <div class="detail-item">
              <label>ID:</label>
              <span>${compliance.identifier || 'Not specified'}</span>
            </div>
            <div class="detail-item">
              <label>Status:</label>
              <span class="status-badge ${compliance.status?.toLowerCase() || 'default'}">${compliance.status || 'Not specified'}</span>
            </div>
            <div class="detail-item">
              <label>Criticality:</label>
              <span class="criticality-badge ${compliance.category?.toLowerCase() || 'default'}">${compliance.category || 'Not specified'}</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h4>Description</h4>
          <p>${compliance.description || 'No description available'}</p>
        </div>

        <div class="detail-section">
          <h4>Implementation Details</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <label>Type:</label>
              <span>${compliance.mandatoryOptional || 'Not specified'}</span>
            </div>
            <div class="detail-item">
              <label>Implementation:</label>
              <span>${compliance.manualAutomatic || 'Not specified'}</span>
            </div>
            <div class="detail-item">
              <label>Maturity Level:</label>
              <span>${compliance.maturityLevel || 'Not specified'}</span>
            </div>
          </div>
        </div>

        ${compliance.isRisk ? `
        <div class="detail-section risk-section">
          <h4>Risk Information</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <label>Possible Damage:</label>
              <p>${compliance.PossibleDamage || 'Not specified'}</p>
            </div>
            <div class="detail-item">
              <label>Mitigation:</label>
              <p>${compliance.mitigation || 'Not specified'}</p>
            </div>
          </div>
        </div>
        ` : ''}

        <div class="detail-section">
          <h4>Hierarchy</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <label>Framework:</label>
              <span>${selectedFramework.value?.name || 'Not specified'}</span>
            </div>
            <div class="detail-item">
              <label>Policy:</label>
              <span>${selectedPolicy.value?.name || 'Not specified'}</span>
            </div>
            <div class="detail-item">
              <label>SubPolicy:</label>
              <span>${selectedSubpolicy.value?.name || 'Not specified'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  // Create modal overlay
  const modalOverlay = document.createElement('div');
  modalOverlay.className = 'modal-overlay';
  modalOverlay.innerHTML = modalContent;
  
  // Add click handler to close modal
  modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) {
      modalOverlay.remove();
    }
  });

  // Add modal styles
  const modalStyles = document.createElement('style');
  modalStyles.textContent = `
    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(255, 255, 255, 0.95);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
      padding: 30px;
      backdrop-filter: blur(3px);
    }
    
    .control-details-modal {
      background: transparent;
      border-radius: 0;
      width: 70% !important;
      max-width: 1000px !important;
      min-width: 700px !important;
      max-height: 85vh;
      min-height: 400px;
      overflow: hidden;
      box-shadow: none;
      border: none;
      margin: 30px !important;
      position: relative;
      z-index: 1001;
      box-sizing: border-box;
      flex-shrink: 0;
      display: flex;
      flex-direction: column;
    }
    
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 20px 24px;
      border-bottom: 1px solid #e5e7eb;
      background: transparent;
      border-radius: 12px 12px 0 0;
      position: sticky;
      top: 0;
      z-index: 10;
    }
    
    .modal-header h3 {
      margin: 0;
      color: #1f2937;
      font-size: 1.25rem;
      font-weight: 700;
    }
    
    .modal-close {
      background: rgba(107, 114, 128, 0.1);
      border: none;
      font-size: 1.5rem;
      cursor: pointer;
      color: #6b7280;
      padding: 8px;
      border-radius: 8px;
      transition: all 0.2s ease;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 300;
    }
    
    .modal-close:hover {
      color: #374151;
      background: rgba(107, 114, 128, 0.2);
      transform: scale(1.1);
    }
    
    .modal-body {
      padding: 20px;
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    
    .detail-section {
      margin-bottom: 0;
      background: transparent;
      border-radius: 10px;
      padding: 16px;
      border: 1px solid #f1f5f9;
      box-shadow: none;
      transition: all 0.2s ease;
      flex: 1;
      display: flex;
      flex-direction: column;
    }
    
    .detail-section h4 {
      margin: 0 0 16px 0;
      color: #1f2937;
      font-size: 1.25rem;
      font-weight: 700;
      padding-bottom: 12px;
      border-bottom: 2px solid #e5e7eb;
      position: relative;
    }
    
    .detail-section h4::after {
      content: '';
      position: absolute;
      bottom: -2px;
      left: 0;
      width: 60px;
      height: 3px;
      background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
      border-radius: 2px;
    }
    
    .detail-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
      flex: 1;
    }
    
    .detail-item {
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding: 12px;
      background: transparent;
      border-radius: 8px;
      border-left: 3px solid #3b82f6;
      transition: all 0.2s ease;
      min-height: 50px;
      justify-content: center;
    }
    
    .detail-item label {
      font-weight: 700;
      color: #4b5563;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 4px;
    }
    
    .detail-item span,
    .detail-item p {
      color: #1f2937;
      font-weight: 500;
      line-height: 1.5;
      font-size: 0.9rem;
    }
    
    .detail-item span {
      font-weight: 600;
    }
    
    .status-badge,
    .criticality-badge {
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.025em;
      display: inline-block;
    }
    
    .status-badge.active { 
      background-color: #dcfce7; 
      color: #166534; 
      border: 1px solid #22c55e;
    }
    
    .status-badge.scheduled { 
      background-color: #dcfce7; 
      color: #166534; 
      border: 1px solid #22c55e;
    }
    
    .status-badge.inactive { 
      background-color: #fee2e2; 
      color: #991b1b; 
      border: 1px solid #ef4444;
    }
    
    .status-badge.pending { 
      background-color: #fef3c7; 
      color: #92400e; 
      border: 1px solid #f59e0b;
    }
    
    .status-badge.under-review { 
      background-color: #fef3c7; 
      color: #92400e; 
      border: 1px solid #f59e0b;
    }
    
    .criticality-badge.high { 
      background-color: #fee2e2; 
      color: #991b1b; 
      border: 1px solid #ef4444;
    }
    
    .criticality-badge.medium { 
      background-color: #fef3c7; 
      color: #92400e; 
      border: 1px solid #f59e0b;
    }
    
    .criticality-badge.low { 
      background-color: #dcfce7; 
      color: #166534; 
      border: 1px solid #22c55e;
    }
    
    .risk-section {
      background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
      padding: 16px;
      border-radius: 10px;
      border-left: 4px solid #ef4444;
      box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1);
    }
    
    .risk-section h4::after {
      background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
    }
  `;
  
  document.head.appendChild(modalStyles);
  document.body.appendChild(modalOverlay);
}
</script>

<style src="./AllCompliance.css"></style>

<style>
/* Framework Explorer inspired styling */
.compliance-view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  margin-bottom: 30px;
  padding-top: 20px;
  padding-bottom: 10px;
  border-bottom:none!important;
}

.compliance-view-title {
  margin: 0;
  color: #344054;
  font-size: 1.8rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.compliance-header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

/* View toggle button styles removed - only list view is available */

/* Section header styling */
.compliance-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  font-size: 1.2rem!important;
  font-weight: 600;
  color: #344054;
  padding-bottom: 0;
  margin-bottom: -10px!important;
  border-bottom: none!important;
}

/* Export Controls */
.compliance-export-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.compliance-export-format-select {
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
  background-color: transparent;
  border-radius: 0;
  border: none;
  overflow: hidden;
  box-shadow: none;
  margin-top: 0;
}

.compliance-table {
  width: 100%;
  border-collapse: collapse;
  background-color: transparent;
  margin: 0;
  border: none;
}

.compliance-table th {
  background: #f8f9fa !important;
  padding: 16px 12px;
  text-align: left;
  font-weight: 600;
  color: #495057 !important;
  border-bottom: 2px solid #dee2e6;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 10;
}

/* Force table header to light ash color */
table.compliance-table thead th,
.compliance-table thead th {
  background: #f8f9fa !important;
  color: #495057 !important;
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
  background: transparent;
  transform: translateY(-1px);
  box-shadow: none;
}

.compliance-table tr.clickable-row {
  cursor: pointer;
}

.compliance-table tr:last-child td {
  border-bottom: none;
}

/* Status Text with Dots */
.compliance-card-status {
  display: inline-flex;
  align-items: center;
  font-size: 0.9rem;
  font-weight: 500;
  text-transform: capitalize;
  gap: 6px;
  background: none !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  box-shadow: none !important;
}

.compliance-card-status::before {
  content: '●';
  font-size: 0.8rem;
  font-weight: bold;
}

.compliance-card-status.active {
  color: #22c55e;
}

.compliance-card-status.active::before {
  color: #22c55e;
}

.compliance-card-status.scheduled {
  color: #22c55e;
}

.compliance-card-status.scheduled::before {
  color: #22c55e;
}

.compliance-card-status.inactive {
  color: #ef4444 !important;
}

.compliance-card-status.inactive::before {
  color: #ef4444 !important;
}

/* Force inactive to be red regardless of any other styles */
.compliance-card-status[class*="inactive"] {
  color: #ef4444 !important;
}

.compliance-card-status[class*="inactive"]::before {
  color: #ef4444 !important;
}

.compliance-card-status.pending {
  color: #f59e0b;
}

.compliance-card-status.pending::before {
  color: #f59e0b;
}

.compliance-card-status.under-review {
  color: #f59e0b;
}

.compliance-card-status.under-review::before {
  color: #f59e0b;
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
  background: transparent;
  color: #495057;
  border: 1px solid #dee2e6;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.compliance-action-btn:hover {
  background: rgba(79, 140, 255, 0.1);
  color: #212529;
  transform: translateY(-2px);
  box-shadow: none;
  border-color: #4f8cff;
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

/* Card view styles removed - only list view is available */

/* Breadcrumbs - Framework Explorer Style */
.breadcrumbs {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.breadcrumb-chip {
  background: transparent;
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

.breadcrumb-close {
  cursor: pointer;
  font-size: 1.1rem;
  line-height: 1;
  color: #6c757d;
  transition: color 0.2s ease;
  padding: 2px;
  border-radius: 50%;
}

.breadcrumb-close:hover {
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

/* Additional card-specific overrides can go here if needed */

/* Mobile responsive styles are now in AllCompliance.css */

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
.compliance-action-btn:focus,
.compliance-export-btn:focus {
  outline: 2px solid #4f8cff;
  outline-offset: 2px;
}

/* Expanded details styles are now in AllCompliance.css */

/* Export Controls */
.export-controls {
  margin: 16px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.export-controls .format-selector {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.export-controls .format-selector label {
  font-weight: 500;
  color: #4b5563;
}

.export-controls .format-selector select {
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background-color: transparent;
  color: #374151;
  font-size: 0.95rem;
  min-width: 150px;
}

.export-btn.enhanced {
  background-color: #3b82f6;
  color: white;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  border: none;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: none;
}

.export-btn.enhanced:hover {
  background-color: #2563eb;
  transform: translateY(-2px);
  box-shadow: none;
}

.export-btn.enhanced:active {
  transform: translateY(0);
}

.export-btn.enhanced i {
  font-size: 1.1rem;
}

/* Compliances Grid */
.compliance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.compliance-card {
  border: none;
  border-radius: 0;
  overflow: hidden;
  background-color: transparent;
  box-shadow: none;
}

.compliance-header {
  padding: 10px;
  display: flex;
  justify-content: space-between;
  background-color: transparent;
}

/* Status badges removed - using dot styling instead */

.criticality-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.85em;
  font-weight: 500;
}

.criticality-high { background-color: #ffebee; color: #d32f2f; }
.criticality-medium { background-color: #fff3e0; color: #f57c00; }
.criticality-low { background-color: #e8f5e9; color: #388e3c; }

.compliance-body {
  padding: 0;
  background-color: transparent;
}

.compliance-body h3 {
  margin: 0 0 15px 0;
  font-size: 1.1em;
  color: #333;
}

.compliance-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.compliance-detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.9em;
}

.compliance-detail-row .compliance-label {
  color: #666;
}

.compliance-detail-row .compliance-value {
  font-weight: 500;
  color: #333;
}

.compliance-footer {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
  font-size: 0.85em;
  color: #666;
}

.created-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.identifier {
  font-family: monospace;
  color: #888;
}

/* Loading State */
.loading {
  text-align: center;
  padding: 40px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* No Data State */
.no-data {
  text-align: center;
  padding: 40px;
  color: #666;
}

.no-data i {
  font-size: 48px;
  margin-bottom: 20px;
  color: #ddd;
}

.export-buttons {
  margin: 16px 0;
  text-align: right;
}

.export-controls .el-alert {
  margin-top: 10px;
  text-align: left;
}

/* Styles for expanded details view */
.expanded-details {
  margin-top: 16px;
  padding: 16px;
  background-color: transparent;
  border-radius: 0;
  border: none;
}

.expanded-details h4 {
  margin-top: 0;
  margin-bottom: 16px;
  color: #1f2937;
  font-size: 1.1rem;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 8px;
}

.expanded-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.expanded-section-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background-color: transparent;
  border: none;
  border-radius: 0;
  overflow: hidden;
}

.expanded-section-box h5 {
  margin: 0;
  padding: 10px 15px;
  background-color: transparent;
  color: #374151;
  font-size: 0.9rem;
  font-weight: 600;
  border-bottom: 1px solid #e5e7eb;
}

.expanded-content-box {
  padding: 15px;
  min-height: 40px;
  color: #1f2937;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.95rem;
  line-height: 1.5;
}

/* Add field category headings */
.expanded-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.expanded-details h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 0;
  margin-bottom: 16px;
  color: #1f2937;
  font-size: 1.1rem;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 12px;
}

.expanded-details h4:before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 20px;
  background-color: #4f46e5;
  border-radius: 2px;
}

/* Add "empty value" styling */
.empty-value {
  color: #d1d5db;
  font-style: italic;
  display: inline-block;
  padding: 4px 8px;
  border-radius: 0;
  background-color: transparent;
  border: none;
}

.compliance-expanded-row {
  background-color: transparent !important;
}

.details-row {
  background-color: transparent;
}

.details-row td {
  padding: 20px !important;
  border-bottom: 1px solid #e2e8f0;
}

/* Make expanded boxes slightly larger in list view */
.details-row .expanded-content-box {
  padding: 15px;
  min-height: 50px;
  font-size: 1rem;
}

/* Override grid layout for list view for better readability */
.details-row .expanded-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

/* Add a subtle animation for expanding rows */
.details-row {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Mitigation text formatting */
.mitigation-text {
  font-family: inherit;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  padding: 0;
  background: none;
  border: none;
  color: inherit;
  font-size: inherit;
  line-height: 1.5;
}

/* Responsive design */
@media (max-width: 768px) {
  .compliance-view-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .compliance-header-actions {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  
  .compliance-export-controls {
    justify-content: stretch;
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
    background-color: transparent;
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

/* Loading and empty states */
.compliance-loading-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #4b5563;
  margin: 40px 0;
  font-size: 1.1rem;
}

.compliance-no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #6b7280;
  text-align: center;
}

.compliance-no-data i {
  font-size: 3rem;
  margin-bottom: 16px;
  color: #d1d5db;
}

.compliance-no-data p {
  font-size: 1.1rem;
  margin: 0;
}

/* Action buttons styling */
.compliance-action-btn {
  padding: 6px 8px;
  font-size: 0.85rem;
  margin-right: 4px;
  border-radius: 4px;
  background: transparent;
  color: #4b5563;
  border: 1px solid #d1d5db;
  cursor: pointer;
  transition: all 0.2s ease;
}

.compliance-action-btn:hover {
  background: rgba(79, 140, 255, 0.1);
  color: #1f2937;
  transform: translateY(-1px);
  border-color: #4f8cff;
}

.compliance-action-btn.primary {
  background-color: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.compliance-action-btn.primary:hover {
  background-color: #2563eb;
  border-color: #2563eb;
}

.compliance-action-btn i {
  font-size: 0.9rem;
}

/* Enhanced status badges - removed duplicate, using main styling above */

/* Risk and severity indicators */
.compliance-risk-identified {
  color: #dc2626;
  font-weight: 600;
}

.compliance-no-risk {
  color: #059669;
  font-weight: 600;
}

.compliance-severity-high {
  color: #dc2626;
  font-weight: 600;
}

.compliance-severity-medium {
  color: #d97706;
  font-weight: 600;
}

.compliance-severity-low {
  color: #059669;
  font-weight: 600;
}

.risk-identified {
  color: #dc2626;
  font-weight: 600;
}

.no-risk {
  color: #059669;
  font-weight: 600;
}

.severity-high {
  color: #dc2626;
  font-weight: 600;
}

.severity-medium {
  color: #d97706;
  font-weight: 600;
}

.severity-low {
  color: #059669;
  font-weight: 600;
}

/* Breadcrumbs styling */
.breadcrumbs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.breadcrumb-chip {
  background: transparent;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 0.9rem;
  color: #4b5563;
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #d1d5db;
}

.breadcrumb-close {
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  color: #6b7280;
  transition: color 0.2s ease;
}

.breadcrumb-close:hover {
  color: #ef4444;
}

/* Modal styles */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: transparent;
  border-radius: 0;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  border: none;
}

.modal-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6b7280;
  cursor: pointer;
  padding: 4px;
  line-height: 1;
}

.close-btn:hover {
  color: #ef4444;
}

.modal-body {
  padding: 24px;
}

.no-versions {
  text-align: center;
  color: #6b7280;
  padding: 40px 0;
}

.version-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.version-number {
  font-weight: 600;
  color: #1f2937;
}

.version-badges {
  display: flex;
  gap: 8px;
}

.version-details {
  color: #4b5563;
  font-size: 0.95rem;
}

.version-details p {
  margin: 0 0 12px 0;
  line-height: 1.5;
}

.version-metadata {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 0.85rem;
  color: #6b7280;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.version-metadata span {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>