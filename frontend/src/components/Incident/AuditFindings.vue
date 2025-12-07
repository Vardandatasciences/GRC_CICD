<template>
  <div class="audit-findings-container">
    <div class="audit-findings-header">
      <h1>Audit Finding Incidents</h1>
      <div class="incident-actions">
        <!-- Export controls -->
        <div class="incident-export-controls">
          <select v-model="exportFormat" class="incident-export-format-select">
            <option value="xlsx">Excel (.xlsx)</option>
            <option value="csv">CSV (.csv)</option>
            <option value="pdf">PDF (.pdf)</option>
            <option value="json">JSON (.json)</option>
            <option value="xml">XML (.xml)</option>
            <option value="txt">Text (.txt)</option>
          </select>
          <button @click="exportAuditFindings" class="incident-export-btn" :disabled="isExporting">
            <i class="fas fa-download" v-if="!isExporting"></i>
            <span v-if="isExporting">Exporting...</span>
            <span v-else>Export</span>
          </button>
        </div>
        <button class="incident-refresh-btn" @click="fetchData">
          <i class="fas fa-sync"></i> Refresh
        </button>
      </div>
    </div>

    <div class="error-container" v-if="error">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
      <button @click="fetchData">Retry</button>
    </div>

    <!-- Quick loading indicator -->
    <div class="quick-loading" v-if="isQuickLoading">
      <div class="loading-spinner"></div>
      <span>Loading...</span>
    </div>

    <div class="incident-findings-content" v-if="!error && !isQuickLoading">
      <div class="incident-summary-cards">
        <div class="incident-summary-card open-card" :class="{ active: filterStatus === 'open' }" @click="filterByStatus('open')">
          <div class="card-icon open">
            <i class="fas fa-exclamation-circle"></i>
          </div>
          <div class="card-content">
            <h3>Open</h3>
            <div class="card-value">{{ summary.open || 0 }}</div>
          </div>
        </div>

        <div class="incident-summary-card assigned-card" :class="{ active: filterStatus === 'assigned' }" @click="filterByStatus('assigned')">
          <div class="card-icon assigned">
            <i class="fas fa-user-check"></i>
          </div>
          <div class="card-content">
            <h3>Assigned</h3>
            <div class="card-value">{{ summary.assigned || 0 }}</div>
          </div>
        </div>

        <div class="incident-summary-card closed-card" :class="{ active: filterStatus === 'closed' }" @click="filterByStatus('closed')">
          <div class="card-icon closed">
            <i class="fas fa-check-circle"></i>
          </div>
          <div class="card-content">
            <h3>Closed</h3>
            <div class="card-value">{{ summary.closed || 0 }}</div>
          </div>
        </div>

        <div class="incident-summary-card rejected-card" :class="{ active: filterStatus === 'rejected' }" @click="filterByStatus('rejected')">
          <div class="card-icon rejected">
            <i class="fas fa-times-circle"></i>
          </div>
          <div class="card-content">
            <h3>Rejected</h3>
            <div class="card-value">{{ summary.rejected || 0 }}</div>
          </div>
        </div>

        <div class="incident-summary-card mitigated-card" :class="{ active: filterStatus === 'scheduled' }" @click="filterByStatus('scheduled')">
          <div class="card-icon mitigated">
            <i class="fas fa-shield-alt"></i>
          </div>
          <div class="card-content">
            <h3>Mitigated to Risk</h3>
            <div class="card-value">{{ summary.mitigated || 0 }}</div>
          </div>
        </div>

        <div class="incident-summary-card total-card" :class="{ active: filterStatus === 'all' }" @click="filterByStatus('all')">
          <div class="card-icon total">
            <i class="fas fa-list-alt"></i>
          </div>
          <div class="card-content">
            <h3>Total Incidents</h3>
            <div class="card-value">{{ summary.total || 0 }}</div>
          </div>
        </div>
      </div>


      <!-- Dynamic Table -->
      <DynamicTable
        v-if="!isQuickLoading"
        :data="findings"
        :columns="visibleTableColumns"
        :unique-key="'IncidentId'"
        :show-pagination="true"
        :default-page-size="20"
        :page-size-options="[10, 20, 50, 100]"
        @open-column-chooser="toggleColumnEditor"
      >
        <!-- Custom Title Cell with Link -->
        <template #cell-IncidentTitle="{ row }">
          <span class="incident-title-link" @click="viewDetails(row)" style="cursor: pointer;">
            {{ row.IncidentTitle }}
          </span>
        </template>

        <!-- Custom Status Cell with Status Badge -->
        <template #cell-Status="{ row }">
          <span :class="getStatusClass(row.Status)">
            {{ row.Status || 'Open' }}
          </span>
        </template>

        <!-- Custom Actions Cell -->
        <template #cell-Actions="{ row }">
          <div class="action-buttons">
            <template v-if="!row.Status || row.Status === 'Open'">
              <div class="icon-row">
                <button 
                  class="incident-action-icon"
                  @click.stop="handleDropdownAction('assign', row)"
                  title="Assign as Incident"
                >
                  <i class="fas fa-user-plus"></i>
                </button>
                <button 
                  class="incident-action-icon"
                  @click.stop="handleDropdownAction('escalate', row)"
                  title="Escalate to Risk"
                >
                  <i class="fas fa-arrow-up"></i>
                </button>
                <button 
                  class="incident-action-icon"
                  @click.stop="handleDropdownAction('close', row)"
                  title="Close Incident"
                >
                  <i class="fas fa-check-circle"></i>
                </button>
              </div>
              <button 
                class="view-details-btn-small"
                @click.stop="handleDropdownAction('view', row)"
                title="View Details"
              >
                View Details
              </button>
            </template>
            <template v-else>
              <button 
                class="view-details-btn-small"
                @click.stop="handleDropdownAction('view', row)"
                title="View Details"
              >
                View Details
              </button>
            </template>
          </div>
        </template>
      </DynamicTable>

      <!-- Column Chooser Modal -->
      <transition name="modal-fade">
        <div v-if="showColumnEditor" class="incident-column-editor-overlay" @click.self="toggleColumnEditor">
          <div class="incident-column-editor-modal">
            <div class="incident-column-editor-header">
              <h3 class="incident-column-editor-title">Choose Columns</h3>
              <button type="button" class="incident-column-editor-close" @click="toggleColumnEditor">
                <i class="fas fa-times"></i>
              </button>
            </div>
            
            <div class="incident-column-editor-search">
              <i class="fas fa-search incident-column-search-icon"></i>
              <input
                type="text"
                v-model="columnSearchQuery"
                placeholder="Search columns..."
                class="incident-column-search-input"
              />
            </div>
            
            <div class="incident-column-editor-actions">
              <button @click="selectAllColumns" class="incident-column-action-btn">
                <i class="fas fa-check-double"></i> Select All
              </button>
              <button @click="deselectAllColumns" class="incident-column-action-btn">
                <i class="fas fa-times"></i> Deselect All
              </button>
            </div>
            
            <div class="incident-column-editor-list">
              <div
                v-for="column in filteredColumnDefinitions"
                :key="column.key"
                class="incident-column-editor-item"
                @click="toggleColumnVisibility(column.key)"
              >
                <input
                  type="checkbox"
                  :checked="isColumnVisible(column.key)"
                  @change.stop="toggleColumnVisibility(column.key)"
                  class="incident-column-checkbox"
                />
                <label class="incident-column-label">{{ column.label }}</label>
              </div>
            </div>
            
            <div v-if="filteredColumnDefinitions.length === 0" class="incident-column-editor-empty">
              <p>No columns found matching "{{ columnSearchQuery }}"</p>
            </div>
          </div>
        </div>
      </transition>

      <div v-if="!isQuickLoading && findings.length === 0" class="empty-state">
        <i class="fas fa-search"></i>
        <p>No audit finding incidents match your criteria.</p>
      </div>
    </div>

    <!-- Modal for Solve/Reject -->
    <div v-if="showModal && modalAction !== 'assign'" class="modal-overlay" @click="closeModal">
      <div class="modal-container" @click.stop>
        <button class="modal-close-btn" @click="closeModal">✕</button>
        <div class="modal-content">
          <div v-if="modalAction === 'solve'" class="solve-container">
            <div class="solve-icon">🔄</div>
            <h3 class="modal-title solve">Forwarded to Risk</h3>
            <p class="modal-subtitle">You will be directed to the Risk module</p>
            <div class="modal-footer">
              <button @click="confirmSolve" class="modal-btn confirm-btn">Confirm Forward</button>
              <button @click="closeModal" class="modal-btn cancel-btn">Cancel</button>
            </div>
          </div>
          
          <div v-else-if="modalAction === 'close'" class="closed-container">
            <div class="closed-icon">✔</div>
            <h3 class="modal-title closed">CLOSED</h3>
            <div class="modal-footer">
              <button @click="confirmClose" class="modal-btn close-btn">Confirm Close</button>
              <button @click="closeModal" class="modal-btn cancel-btn">Cancel</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Assignment Workflow Section -->
    <div v-if="showAssignmentWorkflow" class="assignment-workflow-section">
      <div class="assignment-header">
        <button class="back-btn" @click="closeAssignmentWorkflow">
          <i class="fas fa-arrow-left"></i> Back to Audit Findings
        </button>
      </div>
      <div class="assignment-body">
        <div class="incident-summary">
          <h3>{{ selectedIncident.IncidentTitle || 'Incident #' + selectedIncident.IncidentId }}</h3>
          <div class="incident-details">
            <p><strong>ID:</strong> {{ selectedIncident.IncidentId }}</p>
            <p><strong>Priority:</strong> {{ selectedIncident.RiskPriority }}</p>
            <p><strong>Origin:</strong> {{ selectedIncident.Origin }}</p>
          </div>
        </div>

        <!-- User Selection -->
        <div class="user-selection">
          <h3>Assignment Details</h3>
          <div class="user-form">
              <div class="form-group">
                <label for="assigner">Assigner:</label>
                <div class="current-user-display">
                  <span class="current-user-name">{{ currentUserName || 'Loading...' }}</span>
                  <span class="current-user-note">(You - Current User)</span>
                </div>
              </div>
              
              <div class="form-group">
                <label for="reviewer">Reviewer:</label>
                <select v-model="selectedReviewer" id="reviewer" class="assign-select" required :disabled="loadingUsers">
                  <option value="">
                    {{ loadingUsers ? 'Loading reviewers...' : 'Select Reviewer' }}
                  </option>
                  <option v-for="user in availableUsers" :key="user.id" :value="user.id">
                    {{ user.name }} {{ user.role ? `(${user.role})` : '' }}
                  </option>
                </select>
                <div v-if="loadingUsers" class="loading-indicator">
                  <i class="fas fa-spinner fa-spin"></i> Loading reviewers...
                </div>
                <div v-else-if="availableUsers.length === 0" class="no-users-message">
                  <i class="fas fa-exclamation-triangle"></i> No reviewers available
                  <button @click="fetchUsers" class="retry-btn" :disabled="loadingUsers">
                    <i class="fas fa-redo"></i> Retry
                  </button>
                </div>
            </div>
          </div>
        </div>
        
        <!-- Mitigation Workflow -->
        <div class="mitigation-workflow">
          <h3>Mitigation Steps</h3>
          <!-- Existing Mitigation Steps -->
          <div v-if="mitigationSteps.length" class="workflow-timeline">
            <div v-for="(step, index) in mitigationSteps" :key="index" class="workflow-step">
              <div class="step-number">{{ index + 1 }}</div>
              <div class="step-content">
                <textarea 
                  v-model="step.description" 
                  class="mitigation-textarea"
                  placeholder="Enter mitigation step description"
                ></textarea>
                <div class="step-actions">
                  <button @click="removeMitigationStep(index)" class="remove-step-btn">
                    <i class="fas fa-trash"></i> Remove
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="no-mitigations">
            <p>No mitigation steps found for this incident. Add steps below.</p>
          </div>
          
          <!-- Add New Mitigation Step -->
          <div class="add-mitigation">
            <textarea 
              v-model="newMitigationStep" 
              class="mitigation-textarea"
              placeholder="Enter mitigation step description(s). You can add multiple steps by separating them with commas or new lines."
            ></textarea>
            <button @click="addMitigationStep" class="add-step-btn" :disabled="!newMitigationStep.trim()">
              <i class="fas fa-plus"></i> Add Mitigation Step
            </button>
          </div>
          
          <!-- Due Date Input -->
          <div class="due-date-section">
            <h4>Due Date for Mitigation Completion</h4>
            <input 
              type="date" 
              v-model="mitigationDueDate" 
              class="due-date-input" 
              :min="getTodayDate()"
            />
          </div>

          <!-- Assignment Notes -->
          <div class="assignment-notes-section">
            <h4>Assignment Notes (Optional)</h4>
                <textarea 
                  v-model="assignmentNotes" 
              class="assignment-notes-textarea"
                  placeholder="Add any specific instructions or notes for the assignees..."
                  rows="3"
                ></textarea>
            </div>
            
          <!-- Submit Section -->
          <div class="assignment-actions">
              <button 
              @click="confirmAssignmentWorkflow" 
              class="submit-assignment-btn"
              :disabled="!selectedReviewer || mitigationSteps.length === 0 || !mitigationDueDate"
              >
              <i class="fas fa-user-plus"></i> Assign Incident with Mitigations
              </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { axiosInstance } from '@/config/api.js';
import { API_ENDPOINTS } from '../../config/api.js';
import '@fortawesome/fontawesome-free/css/all.min.css';
import { PopupModal, PopupService } from '@/modules/popup';
import { SessionUtils } from '@/utils/accessUtils';
import incidentService from '../../services/incidentService.js';
import DynamicTable from '@/components/DynamicTable.vue';

export default {
  name: 'AuditFindings',
  components: {
    PopupModal,
    DynamicTable
  },
  setup() {
    const router = useRouter();
    const findings = ref([]);
    const loading = ref(false);
    const isQuickLoading = ref(false);
    const error = ref(null);
    const summary = ref({});
    
    // Modal and workflow state
    const showModal = ref(false);
    const modalAction = ref(''); // 'solve', 'reject', or 'assign'
    const selectedIncident = ref(null);
    const showAssignmentWorkflow = ref(false);
    
    // Assignment related data
    const selectedReviewer = ref('');
    const assignmentNotes = ref('');
    const availableUsers = ref([]);
    const loadingUsers = ref(false);
    
    // Current user data
    const currentUser = ref(null);
    const currentUserName = ref('');
    
    // Mitigation workflow data
    const mitigationSteps = ref([]);
    const newMitigationStep = ref('');
    const mitigationDueDate = ref('');
    
    // Filters
    const filterStatus = ref('all');
    const filterBusinessUnit = ref('all');
    const filterCategory = ref('all');
    const sortBy = ref('Date');
    
    // Export controls
    const exportFormat = ref('xlsx');
    const isExporting = ref(false);
    
    // Dropdown state
    const dropdownOpenFor = ref(null);
    
    // Search query with debouncing
    const searchQuery = ref('');
    const debouncedSearch = ref('');
    let searchTimeout = null;
    
    // Framework filter
    const selectedFramework = ref('');
    const frameworks = ref([]);
    const loadingFrameworks = ref(false);
    
    // Business units and categories data
    const businessUnits = ref([]);
    const categories = ref([]);
    
    // Table columns and column chooser
    const tableColumns = ref([]);
    const visibleColumnKeys = ref([]);
    const showColumnEditor = ref(false);
    const columnSearchQuery = ref('');
    const columnDefinitions = ref([
      { key: 'IncidentId', label: 'Incident ID', defaultVisible: true },
      { key: 'IncidentTitle', label: 'Title', defaultVisible: true },
      { key: 'Origin', label: 'Origin', defaultVisible: true },
      { key: 'AffectedBusinessUnit', label: 'Business Unit', defaultVisible: true },
      { key: 'RiskPriority', label: 'Priority', defaultVisible: true },
      { key: 'Status', label: 'Status', defaultVisible: true },
      { key: 'Date', label: 'Date', defaultVisible: true },
      { key: 'Criticality', label: 'Criticality', defaultVisible: false },
      { key: 'AssignedTo', label: 'Assigned To', defaultVisible: false },
      { key: 'ReviewedBy', label: 'Reviewed By', defaultVisible: false },
      { key: 'Description', label: 'Description', defaultVisible: false },
      { key: 'IncidentCategory', label: 'Category', defaultVisible: false },
      { key: 'RiskCategory', label: 'Risk Category', defaultVisible: false },
      { key: 'ImpactAssessment', label: 'Impact Assessment', defaultVisible: false },
      { key: 'RootCause', label: 'Root Cause', defaultVisible: false },
      { key: 'ContainmentActions', label: 'Containment Actions', defaultVisible: false },
      { key: 'SystemsOrAssetsAffected', label: 'Systems/Assets Affected', defaultVisible: false },
      { key: 'GeographicLocation', label: 'Location', defaultVisible: false },
      { key: 'Actions', label: 'Actions', defaultVisible: true }
    ]);
    
    // Computed property for active filters
    const hasActiveFilters = computed(() => {
      return filterStatus.value !== 'all' || 
             filterBusinessUnit.value !== 'all' || 
             filterCategory.value !== 'all' || 
             searchQuery.value !== '';
    });
    
    // Computed property for visible table columns
    const visibleTableColumns = computed(() => {
      if (visibleColumnKeys.value.length === 0) {
        // Show default visible columns
        const defaultKeys = columnDefinitions.value
          .filter(col => col.defaultVisible)
          .map(col => col.key);
        return tableColumns.value.filter(col => defaultKeys.includes(col.key));
      }
      return tableColumns.value.filter(col => visibleColumnKeys.value.includes(col.key));
    });
    
    // Filter configurations
    const statusFilterConfig = {
      name: 'Status',
      values: [
        { value: 'all', label: 'All Status' },
        { value: 'open', label: 'Open' },
        { value: 'assigned', label: 'Assigned' },
        { value: 'closed', label: 'Closed' },
        { value: 'rejected', label: 'Rejected' },
        { value: 'scheduled', label: 'Escalated to Risk' }
      ],
      defaultValue: 'all'
    };

    const sortByConfig = {
      name: 'Sort By',
      values: [
        { value: 'Date', label: 'Date (Newest First)' },
        { value: 'IncidentTitle', label: 'Title' },
        { value: 'RiskPriority', label: 'Priority' },
        { value: 'Status', label: 'Status' }
      ],
      defaultValue: 'Date'
    };

    const businessUnitFilterConfig = ref({
      name: 'Business Unit',
      values: [
        { value: 'all', label: 'All Business Units' }
      ],
      defaultValue: 'all'
    });

    const categoryFilterConfig = ref({
      name: 'Category',
      values: [
        { value: 'all', label: 'All Categories' }
      ],
      defaultValue: 'all'
    });
    
    // Initialize table columns
    const initializeTableColumns = () => {
      tableColumns.value = [
        {
          key: 'IncidentId',
          label: 'ID',
          sortable: true,
          width: '70px',
          resizable: true,
          defaultVisible: true
        },
        {
          key: 'IncidentTitle',
          label: 'Title',
          sortable: true,
          slot: true,
          width: '250px',
          resizable: true,
          defaultVisible: true
        },
        {
          key: 'Origin',
          label: 'Origin',
          sortable: true,
          width: '120px',
          resizable: true,
          defaultVisible: true
        },
        {
          key: 'AffectedBusinessUnit',
          label: 'Business Unit',
          sortable: true,
          width: '160px',
          resizable: true,
          defaultVisible: true
        },
        {
          key: 'RiskPriority',
          label: 'Priority',
          sortable: true,
          width: '110px',
          resizable: true,
          defaultVisible: true
        },
        {
          key: 'Status',
          label: 'Status',
          sortable: true,
          slot: true,
          width: '130px',
          resizable: true,
          defaultVisible: true
        },
        {
          key: 'Date',
          label: 'Date',
          sortable: true,
          width: '130px',
          resizable: true,
          defaultVisible: true
        },
        {
          key: 'Criticality',
          label: 'Criticality',
          sortable: true,
          width: '110px',
          resizable: true,
          defaultVisible: false
        },
        {
          key: 'AssignedTo',
          label: 'Assigned To',
          sortable: true,
          width: '140px',
          resizable: true,
          defaultVisible: false
        },
        {
          key: 'ReviewedBy',
          label: 'Reviewed By',
          sortable: true,
          width: '140px',
          resizable: true,
          defaultVisible: false
        },
        {
          key: 'Description',
          label: 'Description',
          sortable: true,
          width: '200px',
          resizable: true,
          defaultVisible: false
        },
        {
          key: 'IncidentCategory',
          label: 'Category',
          sortable: true,
          width: '150px',
          resizable: true,
          defaultVisible: false
        },
        {
          key: 'RiskCategory',
          label: 'Risk Category',
          sortable: true,
          width: '150px',
          resizable: true,
          defaultVisible: false
        },
        {
          key: 'ImpactAssessment',
          label: 'Impact Assessment',
          sortable: true,
          width: '180px',
          resizable: true,
          defaultVisible: false
        },
        {
          key: 'RootCause',
          label: 'Root Cause',
          sortable: true,
          width: '180px',
          resizable: true,
          defaultVisible: false
        },
        {
          key: 'ContainmentActions',
          label: 'Containment Actions',
          sortable: true,
          width: '200px',
          resizable: true,
          defaultVisible: false
        },
        {
          key: 'SystemsOrAssetsAffected',
          label: 'Systems/Assets Affected',
          sortable: true,
          width: '200px',
          resizable: true,
          defaultVisible: false
        },
        {
          key: 'GeographicLocation',
          label: 'Location',
          sortable: true,
          width: '150px',
          resizable: true,
          defaultVisible: false
        },
        {
          key: 'Actions',
          label: 'Actions',
          sortable: false,
          slot: true,
          width: '220px',
          resizable: true,
          defaultVisible: true
        }
      ];
    };
    
    // Column chooser methods
    const toggleColumnEditor = () => {
      showColumnEditor.value = !showColumnEditor.value;
      if (showColumnEditor.value) {
        if (visibleColumnKeys.value.length === 0) {
          visibleColumnKeys.value = columnDefinitions.value
            .filter(col => col.defaultVisible)
            .map(col => col.key);
        }
      }
    };
    
    const toggleColumnVisibility = (columnKey) => {
      const index = visibleColumnKeys.value.indexOf(columnKey);
      if (index > -1) {
        visibleColumnKeys.value.splice(index, 1);
      } else {
        visibleColumnKeys.value.push(columnKey);
      }
    };
    
    const isColumnVisible = (columnKey) => {
      if (visibleColumnKeys.value.length === 0) {
        const col = columnDefinitions.value.find(c => c.key === columnKey);
        return col ? col.defaultVisible : false;
      }
      return visibleColumnKeys.value.includes(columnKey);
    };
    
    const filteredColumnDefinitions = computed(() => {
      if (!columnSearchQuery.value) return columnDefinitions.value;
      const query = columnSearchQuery.value.toLowerCase();
      return columnDefinitions.value.filter(col => 
        col.label.toLowerCase().includes(query)
      );
    });
    
    const selectAllColumns = () => {
      visibleColumnKeys.value = columnDefinitions.value.map(col => col.key);
    };
    
    const deselectAllColumns = () => {
      visibleColumnKeys.value = [];
    };
    
    // Fetch data from the API with performance optimizations
    const fetchData = async () => {
      console.log('🔄 [AuditFindings] fetchData called');
      error.value = null;
      isQuickLoading.value = true;
      
      try {
        // Check if we have any filters active
        const hasFilters = filterStatus.value !== 'all' || 
                          filterBusinessUnit.value !== 'all' || 
                          filterCategory.value !== 'all' || 
                          searchQuery.value || 
                          selectedFramework.value;
        
        // Try to load from cache FIRST if no filters
        if (!hasFilters) {
          const cachedFindings = incidentService.getData('auditFindings');
          if (cachedFindings && Array.isArray(cachedFindings)) {
            console.log(`✅ [AuditFindings] Loading ${cachedFindings.length} audit findings from cache - FAST!`);
            findings.value = cachedFindings;
            // Calculate summary from cached data
            summary.value = {
              open: cachedFindings.filter(f => f.Status?.toLowerCase() === 'open').length,
              assigned: cachedFindings.filter(f => f.Status?.toLowerCase() === 'assigned').length,
              closed: cachedFindings.filter(f => f.Status?.toLowerCase() === 'closed').length,
              rejected: cachedFindings.filter(f => f.Status?.toLowerCase() === 'rejected').length,
              mitigated_to_risk: cachedFindings.filter(f => f.Status?.toLowerCase() === 'mitigated to risk').length,
              total: cachedFindings.length
            };
            isQuickLoading.value = false;
            return;
          }
        }
        
        // If filters or no cached data, fetch from API
        console.log(hasFilters ? '🔍 [AuditFindings] Filters active, fetching from API' : '⚠️ [AuditFindings] No cached data, fetching from API');
        
        const params = {
          // Set default limit to improve performance
          limit: 100,
          // Add timeout for faster response
          timeout: 5000
        };
        
        // Apply framework filter if selected
        if (selectedFramework.value) {
          params.framework_id = selectedFramework.value;
          console.log('🔍 Applying framework filter to audit findings:', selectedFramework.value);
        } else {
          console.log('ℹ️ Loading audit findings for all frameworks');
        }
        
        // Apply status filter if not 'all'
        if (filterStatus.value !== 'all') {
          params.status = filterStatus.value;
        }

        // Apply business unit filter if not 'all'
        if (filterBusinessUnit.value !== 'all') {
          params.business_unit = filterBusinessUnit.value;
        }

        // Apply category filter if not 'all'
        if (filterCategory.value !== 'all') {
          params.category = filterCategory.value;
        }
        
        // Apply sorting
        params.sort = sortBy.value;
        params.order = sortBy.value === 'Date' ? 'desc' : 'asc';
        
        // Apply search query
        if (searchQuery.value) {
          params.search = searchQuery.value;
        }
        
        console.log('📤 Fetching audit findings with params:', params);
        
        // Use Promise.race to implement timeout
        const fetchPromise = axiosInstance.get(API_ENDPOINTS.AUDIT_FINDINGS, { 
          params,
          timeout: 10000 // 10 second timeout
        });
        
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Request timeout')), 10000)
        );
        
        const response = await Promise.race([fetchPromise, timeoutPromise]);
        
        if (response.data && response.data.success) {
          findings.value = response.data.data || [];
          summary.value = response.data.summary || {};
          console.log('✅ Loaded', findings.value.length, 'audit findings from API');
          
          // Cache the results if no filters
          if (!hasFilters && findings.value.length > 0) {
            incidentService.setData('auditFindings', findings.value);
            console.log('💾 Cached audit findings for future use');
          }
        } else {
          throw new Error(response.data?.message || 'Failed to load audit finding incidents');
        }
      } catch (err) {
        console.error('Error fetching audit finding incidents:', err);
        if (err.message === 'Request timeout') {
          error.value = 'Request timed out. Please try again or check your connection.';
        } else {
          error.value = err.message || 'Failed to load audit finding incidents. Please try again.';
        }
      } finally {
        isQuickLoading.value = false;
      }
    };
    
    // Apply filters and sorting
    const applyFilters = () => {
      fetchData();
    };
    
    // Debounced search function
    const handleSearchInput = (value) => {
      searchQuery.value = value;
      
      // Clear existing timeout
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
      
      // Set new timeout for debounced search
      searchTimeout = setTimeout(() => {
        debouncedSearch.value = value;
        fetchData();
      }, 500); // 500ms delay
    };
    
    // Clear search function
    const clearSearch = () => {
      searchQuery.value = '';
      debouncedSearch.value = '';
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
      fetchData();
    };
    
    // Filter by status when clicking on summary cards
    const filterByStatus = (status) => {
      filterStatus.value = status;
      applyFilters();
    };
    
    // Utility functions for styling
    const getRowClass = (status) => {
      if (!status || status === 'Open') return 'row-open';
      if (status === 'Assigned') return 'row-assigned';
      if (status === 'Closed') return 'row-closed';
      if (status === 'Rejected') return 'row-rejected';
      if (status === 'Scheduled') return 'row-escalated';
      return '';
    };
    
    const getStatusClass = (status) => {
      if (!status || status === 'Open') return 'status-open';
      if (status === 'Assigned') return 'status-assigned';
      if (status === 'Closed') return 'status-closed';
      if (status === 'Rejected') return 'status-rejected';
      if (status === 'Scheduled') return 'status-escalated';
      return '';
    };
    
    // Navigate to audit finding details
    const viewDetails = (item) => {
      router.push(`/incident/audit-finding-details/${item.IncidentId}`);
    };
    
    // Modal and workflow methods
    const openSolveModal = (incident) => {
      selectedIncident.value = incident;
      modalAction.value = 'solve';
      showModal.value = true;
    };
    
    const openRejectModal = (incident) => {
      selectedIncident.value = incident;
      modalAction.value = 'reject';
      showModal.value = true;
    };
    
    const openAssignModal = (incident) => {
      selectedIncident.value = incident;
      showAssignmentWorkflow.value = true;
      // Reset assignment form
      selectedReviewer.value = '';
      assignmentNotes.value = '';
      newMitigationStep.value = '';
      mitigationDueDate.value = '';
      
      // Fetch users for assignment
      fetchUsers();
      
      // Load existing mitigation steps from the incident's Mitigation field
      console.log('Selected incident:', incident);
      console.log('Incident Mitigation field:', incident.Mitigation);
      loadExistingMitigations(incident);
    };
    
    const closeModal = () => {
      showModal.value = false;
      selectedIncident.value = null;
      // Reset assignment form data
      selectedReviewer.value = '';
      assignmentNotes.value = '';
    };
    
    const closeAssignmentWorkflow = () => {
      showAssignmentWorkflow.value = false;
      selectedIncident.value = null;
      // Reset assignment form data
      selectedReviewer.value = '';
      assignmentNotes.value = '';
      mitigationSteps.value = [];
      newMitigationStep.value = '';
      mitigationDueDate.value = '';
    };
    
    const addMitigationStep = () => {
      if (!newMitigationStep.value.trim()) return;
      
      // Split by commas or newlines to allow multiple steps at once
      const steps = newMitigationStep.value.split(/[,\n]/).filter(step => step.trim());
      
      steps.forEach(step => {
        mitigationSteps.value.push({
          description: step.trim(),
          status: 'Not Started'
        });
      });
      
      newMitigationStep.value = '';
    };
    
    const removeMitigationStep = (index) => {
      mitigationSteps.value.splice(index, 1);
    };
    
    const getTodayDate = () => {
      const today = new Date();
      const year = today.getFullYear();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      const day = String(today.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    };
    
    const loadExistingMitigations = (incident) => {
      // Initialize with empty array
      mitigationSteps.value = [];
      
      // Check if incident has existing mitigation data
      if (incident.Mitigation) {
        try {
          let mitigationData = incident.Mitigation;
          
          // If it's a string, try to parse it as JSON
          if (typeof mitigationData === 'string') {
            // Check if it's JSON format
            if (mitigationData.trim().startsWith('{') || mitigationData.trim().startsWith('[')) {
              try {
                mitigationData = JSON.parse(mitigationData);
              } catch (e) {
                // If JSON parsing fails, treat as plain text
                console.log('Mitigation data is not JSON, treating as plain text');
              }
            }
          }
          
          // Handle different mitigation data formats
          if (typeof mitigationData === 'string') {
            // Plain text - split by lines, commas, or use as single step
            const steps = mitigationData.split(/[,\n]/).filter(step => step.trim());
            mitigationSteps.value = steps.map((step) => ({
              description: step.trim(),
              status: 'Not Started'
            }));
          } else if (Array.isArray(mitigationData)) {
            // Array format
            mitigationSteps.value = mitigationData.map(item => ({
              description: typeof item === 'string' ? item : (item.description || item.title || 'Mitigation step'),
              status: item.status || 'Not Started'
            }));
          } else if (typeof mitigationData === 'object') {
            // Object format (like {"1": "Step 1", "2": "Step 2"})
            mitigationSteps.value = Object.values(mitigationData).map(step => ({
              description: typeof step === 'string' ? step : (step.description || step.title || 'Mitigation step'),
              status: step.status || 'Not Started'
            }));
          }
          
          console.log('Loaded existing mitigation steps:', mitigationSteps.value);
        } catch (error) {
          console.error('Error parsing mitigation data:', error);
          // Fallback: treat as plain text
          mitigationSteps.value = [{
            description: incident.Mitigation,
            status: 'Not Started'
          }];
        }
      }
      
      // If no mitigation steps were loaded, start with empty array
      if (mitigationSteps.value.length === 0) {
        console.log('No existing mitigation steps found');
      }
    };
    
    const confirmAssignmentWorkflow = () => {
      // Validate reviewer selection
      if (!selectedReviewer.value) {
        PopupService.error('Please select a reviewer');
        return;
      }

      // Auto-set current user as assigner
      const currentUserId = currentUser.value?.user_id;
      if (!currentUserId) {
        PopupService.error('Unable to identify current user. Please refresh and try again.');
        return;
      }

      // Check if current user is trying to assign to themselves as reviewer
      if (currentUserId === selectedReviewer.value.toString()) {
        PopupService.error('You cannot assign yourself as both assigner and reviewer');
        return;
      }

      if (mitigationSteps.value.length === 0) {
        PopupService.error('Please add at least one mitigation step');
        return;
      }

      if (!mitigationDueDate.value) {
        PopupService.error('Please select a due date');
        return;
      }

      console.log('Assigning incident:', selectedIncident.value.IncidentId);

      // Find reviewer details - assigner is automatically the current user
      const reviewer = availableUsers.value.find(user => user.id === selectedReviewer.value);

      // Convert mitigations to the expected JSON format
      const mitigationsJson = {};
      mitigationSteps.value.forEach((step, index) => {
        mitigationsJson[index + 1] = step.description;
      });

      // Update incident with assignment details and mitigations
      axiosInstance.put(API_ENDPOINTS.INCIDENT_ASSIGN(selectedIncident.value.IncidentId), {
        status: 'Assigned',
        assigner_id: currentUserId,
        assigner_name: currentUserName.value,
        reviewer_id: selectedReviewer.value,
        reviewer_name: reviewer.name,
        assignment_notes: assignmentNotes.value,
        assigned_date: new Date().toISOString(),
        mitigations: mitigationsJson,
        due_date: mitigationDueDate.value
      })
      .then(response => {
        console.log('Incident assigned successfully - API response:', response.data);
        
        // Show success popup
        PopupService.success(`Incident ${selectedIncident.value.IncidentId} assigned successfully with mitigation steps!`);
        
        // Refresh the audit findings data
        fetchData();
        
        // Close workflow and redirect
        closeAssignmentWorkflow();
        setTimeout(() => {
          router.push('/incident/incident');
        }, 2000);
      })
      .catch(err => {
        console.error('Error assigning incident:', err);
        PopupService.error('Failed to assign incident. Please try again.');
      });
    };
    
    const confirmSolve = (incident) => {
      console.log('Escalating incident to risk:', incident.IncidentId);
      
      // Update incident status to "Scheduled"
      axiosInstance.put(API_ENDPOINTS.INCIDENT_STATUS(incident.IncidentId), {
        status: 'Scheduled'
      })
      .then(response => {
        console.log('Incident escalated to risk - API response:', response.data);
        
        // Check if the response indicates success
        if (response.data.success) {
          // Show success popup
          PopupService.success(`Incident #${incident.IncidentId} escalated to Risk successfully!`);
          
          // Refresh the audit findings data
          fetchData();
          
          // Close modal and redirect after 2 seconds
          closeModal();
          setTimeout(() => {
            router.push('/incident/incident');
          }, 2000);
        } else {
          // Handle unsuccessful response
          console.error('API returned unsuccessful response:', response.data);
          PopupService.error(response.data.message || 'Failed to escalate incident. Please try again.');
        }
      })
      .catch(err => {
        console.error('Error updating incident status:', err);
        console.error('Error details:', err.response);
        console.error('Error message:', err.message);
        PopupService.error('Failed to escalate incident. Please try again.');
      });
    };
    
    const confirmReject = () => {
      console.log('Rejecting incident:', selectedIncident.value.IncidentId);
      
      // Update incident status to "Rejected"
      axiosInstance.put(API_ENDPOINTS.INCIDENT_STATUS(selectedIncident.value.IncidentId), {
        status: 'Rejected',
        rejection_source: 'INCIDENT'
      })
      .then(response => {
        console.log('Incident rejected - API response:', response.data);
        
        // Check if the response indicates success
        if (response.data.success) {
          // Show success popup
          PopupService.success(`Incident ${selectedIncident.value.IncidentId} rejected successfully!`);
          
          // Refresh the audit findings data
          fetchData();
          
          // Close modal and redirect after 2 seconds
          closeModal();
          setTimeout(() => {
            router.push('/incident/incident');
          }, 2000);
        } else {
          // Handle unsuccessful response
          console.error('API returned unsuccessful response:', response.data);
          PopupService.error(response.data.message || 'Failed to reject incident. Please try again.');
        }
      })
      .catch(err => {
        console.error('Error updating incident status:', err);
        console.error('Error details:', err.response);
        console.error('Error message:', err.message);
        PopupService.error('Failed to reject incident. Please try again.');
      });
    };
    
    // Fetch users for assignment
    const fetchUsers = async () => {
      loadingUsers.value = true;
      try {
        console.log('🔍 Fetching users for assignment...');
        console.log('Using API endpoint:', API_ENDPOINTS.USERS);
        
        const response = await axiosInstance.get(API_ENDPOINTS.USERS);
        console.log('✅ Users API response:', response.data);
        
        // Map the API response to match the expected frontend structure
        availableUsers.value = response.data.map(user => ({
          id: user.UserId,
          name: user.UserName,
          role: user.role || 'User'
        }));
        
        console.log('✅ Mapped users:', availableUsers.value);
        console.log('✅ Total users loaded:', availableUsers.value.length);
        
      } catch (err) {
        console.error('❌ Failed to fetch users:', err);
        console.error('❌ Error details:', err.response?.data || err.message);
        console.error('❌ Error status:', err.response?.status);
        
        // Try fallback endpoint
        try {
          console.log('🔄 Trying fallback endpoint: CUSTOM_USERS');
          const fallbackResponse = await axiosInstance.get(API_ENDPOINTS.CUSTOM_USERS);
          console.log('✅ Fallback users API response:', fallbackResponse.data);
          
          availableUsers.value = fallbackResponse.data.map(user => ({
            id: user.UserId,
            name: user.UserName,
            role: user.role || 'User'
          }));
          
          console.log('✅ Fallback users loaded:', availableUsers.value.length);
        } catch (fallbackErr) {
          console.error('❌ Fallback also failed:', fallbackErr);
          availableUsers.value = [];
          PopupService.error('Failed to load reviewers list. Please refresh and try again.');
        }
      } finally {
        loadingUsers.value = false;
      }
    };

    // Fetch business units from incidents table
    const fetchBusinessUnits = async () => {
      try {
        const response = await axiosInstance.get(API_ENDPOINTS.INCIDENT_BUSINESS_UNITS);
        
        if (response.data && response.data.success) {
          businessUnits.value = response.data.data || [];
          // Update filter config with fetched business units
          businessUnitFilterConfig.value.values = [
            { value: 'all', label: 'All Business Units' },
            ...businessUnits.value.map(unit => ({
              value: unit,
              label: unit
            }))
          ];
        } else {
          console.error('Failed to fetch business units - invalid response format:', response.data);
          businessUnits.value = [];
        }
      } catch (err) {
        console.error('Failed to fetch business units:', err);
        businessUnits.value = [];
      }
    };

    // Fetch categories from database
    const fetchCategories = async () => {
      try {
        const response = await axiosInstance.get(API_ENDPOINTS.CATEGORY_BUSINESS_UNITS, {
          params: { source: 'Categories' }
        });
        
        if (response.data && response.data.success) {
          categories.value = response.data.data || [];
          // Update filter config with fetched categories
          categoryFilterConfig.value.values = [
            { value: 'all', label: 'All Categories' },
            ...categories.value.map(category => ({
              value: category.value,
              label: category.value
            }))
          ];
        }
      } catch (err) {
        console.error('Failed to fetch categories:', err);
        categories.value = [];
      }
    };

    // Fetch frameworks from database
    const fetchFrameworks = async () => {
      try {
        loadingFrameworks.value = true;
        console.log('🔍 Fetching frameworks for audit findings...');
        const response = await axiosInstance.get(API_ENDPOINTS.INCIDENT_FRAMEWORKS);
        console.log('✅ Frameworks API response:', response.data);
        
        // Handle the API response format
        let frameworksData = [];
        if (response.data.success && response.data.frameworks) {
          frameworksData = response.data.frameworks;
        } else if (response.data.success && Array.isArray(response.data.data)) {
          frameworksData = response.data.data;
        } else if (Array.isArray(response.data)) {
          frameworksData = response.data;
        } else {
          console.error('Unexpected frameworks response format:', response.data);
          frameworks.value = [];
          return;
        }
        
        frameworks.value = frameworksData.map(framework => ({
          id: framework.id || framework.FrameworkId,
          name: framework.name || framework.FrameworkName || 'Unknown Framework'
        }));
        
        console.log('✅ Processed frameworks:', frameworks.value);
      } catch (err) {
        console.error('❌ Error fetching frameworks:', err);
        console.error('❌ Error details:', err.response?.data || err.message);
        frameworks.value = [];
      } finally {
        loadingFrameworks.value = false;
      }
    };

    // Fetch selected framework from home page
    const fetchSelectedFramework = async () => {
      try {
        console.log('🔍 Fetching selected framework from home page for audit findings...');
        const response = await axiosInstance.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED);
        console.log('✅ Selected framework API response:', response.data);
        
        if (response.data && response.data.frameworkId) {
          selectedFramework.value = response.data.frameworkId;
          console.log('✅ Set selected framework ID for audit findings:', selectedFramework.value);
        } else {
          console.log('⚠️ No framework selected or frameworkId not found in response');
          // Try localStorage fallback
          const storedFrameworkId = localStorage.getItem('selectedFrameworkId') || localStorage.getItem('frameworkId');
          if (storedFrameworkId) {
            selectedFramework.value = storedFrameworkId;
            console.log('✅ Using framework ID from localStorage:', selectedFramework.value);
          }
        }
      } catch (error) {
        console.warn('⚠️ Could not fetch selected framework:', error);
        // Try localStorage fallback
        const storedFrameworkId = localStorage.getItem('selectedFrameworkId') || localStorage.getItem('frameworkId');
        if (storedFrameworkId) {
          selectedFramework.value = storedFrameworkId;
          console.log('✅ Using framework ID from localStorage as fallback:', selectedFramework.value);
        }
      }
    };
    

    
    // Format date for display
    const formatDate = (dateString) => {
      if (!dateString) return 'N/A';
      
      const date = new Date(dateString);
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    };
    
    // Truncate long text
    const truncateText = (text, maxLength) => {
      if (!text) return 'N/A';
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    };
    
    // Export audit findings
    const exportAuditFindings = async () => {
      isExporting.value = true;
      
      // Show warning if there are many records
      if (findings.value.length > 5000) {
        const confirmed = confirm(
          `You are about to export ${findings.value.length} audit findings. ` +
          'This may take a while and the export will be limited to 10,000 records for performance. Continue?'
        );
        if (!confirmed) {
          isExporting.value = false;
          return;
        }
      }
      
      try {
        // Instead of sending all data, let the backend fetch the data
        // This avoids the character limit issue
        const response = await axiosInstance.post(API_ENDPOINTS.AUDIT_FINDINGS_EXPORT, {
          file_format: exportFormat.value,
          user_id: 'audit_user', // You might want to get this from your auth system
          options: JSON.stringify({
            filters: {
              filterStatus: filterStatus.value,
              filterBusinessUnit: filterBusinessUnit.value,
              filterCategory: filterCategory.value,
              sortBy: sortBy.value,
              searchQuery: searchQuery.value,
              framework_id: selectedFramework.value
            }
          })
          // Remove the data field to let backend fetch fresh data
        });
        
        console.log('Export successful:', response.data);
        
        // Check if we have a file URL
        if (response.data && response.data.file_url) {
          // Try to open the file URL in a new tab, fallback to download if it fails
          try {
            const newWindow = window.open(response.data.file_url, '_blank');
            if (newWindow) {
              PopupService.success('Export completed successfully! File opened in new tab.');
            } else {
              // Fallback to download if popup is blocked
              const link = document.createElement('a');
              link.href = response.data.file_url;
              link.setAttribute('download', response.data.file_name || `audit_findings.${exportFormat.value}`);
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
              PopupService.success('Export completed successfully! File downloaded.');
            }
          } catch (downloadErr) {
            // Fallback to download if window.open fails
            const link = document.createElement('a');
            link.href = response.data.file_url;
            link.setAttribute('download', response.data.file_name || `audit_findings.${exportFormat.value}`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            PopupService.success('Export completed successfully! File downloaded.');
            console.error(downloadErr);
          }
        }
        
      } catch (err) {
        console.error('Export failed:', err);
        PopupService.error('Export failed. Please try again.');
      } finally {
        isExporting.value = false;
      }
    };
    
    // Dropdown methods
    const toggleActionDropdown = (index) => {
      if (dropdownOpenFor.value === index) {
        dropdownOpenFor.value = null;
        return;
      }
      
      dropdownOpenFor.value = index;
    };
    
    const closeAllDropdowns = () => {
      dropdownOpenFor.value = null;
    };

    // Close dropdown when clicking outside
    const handleClickOutside = (event) => {
      if (!event.target.closest('.actions-dropdown')) {
        closeAllDropdowns();
      }
    };
    
    const handleDropdownAction = (action, item) => {
      closeAllDropdowns();
      
      switch (action) {
        case 'view':
          viewDetails(item);
          break;
        case 'assign':
          openAssignModal(item);
          break;
        case 'escalate':
          PopupService.confirm(
            `Are you sure you want to escalate Incident #${item.IncidentId} to Risk? This will forward the incident to the Risk module for further evaluation and mitigation.`,
            'Escalate to Risk',
            () => confirmSolve(item)
          );
          break;
        case 'close':
          PopupService.confirm(
            `Are you sure you want to close Incident #${item.IncidentId}? This action cannot be undone.`,
            'Close Incident',
            () => confirmClose(item)
          );
          break;
      }
    };
    
    const openCloseModal = (incident) => {
      selectedIncident.value = incident;
      modalAction.value = 'close';
      showModal.value = true;
    };

    const confirmClose = (incident) => {
      axiosInstance.put(API_ENDPOINTS.INCIDENT_STATUS(incident.IncidentId), {
        status: 'Closed',
        close_source: 'INCIDENT'
      })
      .then(response => {
        console.log('Incident closed - API response:', response.data);
        
        // Check if the response indicates success
        if (response.data.success) {
          PopupService.success(`Incident #${incident.IncidentId} closed successfully!`, 'Incident Closed');
          fetchData();
        } else {
          // Handle unsuccessful response
          console.error('API returned unsuccessful response:', response.data);
          PopupService.error(response.data.message || 'Failed to close incident. Please try again.');
        }
      })
      .catch(error => {
        console.error('Error closing incident:', error);
        console.error('Error details:', error.response);
        console.error('Error message:', error.message);
        PopupService.error('Failed to close incident. Please try again.');
      });
    };
    
    // Load current user information
    const loadCurrentUser = () => {
      console.log('Loading current user for audit findings assignment...');
      try {
        // Get current user from session
        currentUser.value = SessionUtils.getUserSession();
        console.log('Current user session data:', currentUser.value);
        
        if (currentUser.value && currentUser.value.name) {
          currentUserName.value = currentUser.value.name;
          console.log('Set current user name to:', currentUserName.value);
        } else {
          console.warn('No current user name found in session, using fallback');
          currentUserName.value = 'Current User';
        }
      } catch (error) {
        console.error('Error loading current user:', error);
        currentUserName.value = 'Current User';
      }
    };
    
    // Clear all filters
    const clearAllFilters = () => {
      filterStatus.value = 'all';
      filterBusinessUnit.value = 'all';
      filterCategory.value = 'all';
      searchQuery.value = '';
      applyFilters();
    };

    // Simple dropdown positioning fix
    const fixDropdownPositioning = () => {
      // Ensure filter containers allow overflow for dropdowns
      const filterContainers = document.querySelectorAll('.incident-filter-container, .incident-filter-row, .incident-filter-item');
      filterContainers.forEach(container => {
        container.style.overflow = 'visible';
      });
    };

    onMounted(async () => {
      console.log('🚀 [AuditFindings] Component mounted');
      loadCurrentUser();
      
      // Initialize table columns
      initializeTableColumns();
      
      // Wait for incident data fetch if still in progress
      if (window.incidentDataFetchPromise) {
        console.log('⏳ [AuditFindings] Waiting for incident data fetch...');
        try {
          await window.incidentDataFetchPromise;
          console.log('✅ [AuditFindings] Incident data fetch completed');
        } catch (error) {
          console.warn('⚠️ [AuditFindings] Incident data fetch failed:', error);
        }
      }
      
      // Fetch frameworks and selected framework first
      await fetchFrameworks();
      await fetchSelectedFramework();
      
      // Then fetch audit findings data (will use cache if available)
      fetchData();
      
      // Load supporting data from cache or API
      const cachedUsers = incidentService.getData('incidentUsers');
      if (cachedUsers && Array.isArray(cachedUsers)) {
        console.log(`✅ [AuditFindings] Loaded ${cachedUsers.length} users from cache`);
        availableUsers.value = cachedUsers;
      } else {
        fetchUsers();
      }
      
      const cachedBusinessUnits = incidentService.getData('incidentBusinessUnits');
      if (cachedBusinessUnits && Array.isArray(cachedBusinessUnits)) {
        console.log(`✅ [AuditFindings] Loaded ${cachedBusinessUnits.length} business units from cache`);
        businessUnitFilterConfig.value.values = [
          { value: 'all', label: 'All Business Units' },
          ...cachedBusinessUnits.map(bu => ({ value: bu, label: bu }))
        ];
      } else {
        fetchBusinessUnits();
      }
      
      const cachedCategories = incidentService.getData('incidentCategories');
      if (cachedCategories && Array.isArray(cachedCategories)) {
        console.log(`✅ [AuditFindings] Loaded ${cachedCategories.length} categories from cache`);
        categoryFilterConfig.value.values = [
          { value: 'all', label: 'All Categories' },
          ...cachedCategories.map(cat => ({ value: cat, label: cat }))
        ];
      } else {
        fetchCategories();
      }
      
      // Close dropdowns when clicking outside
      document.addEventListener('click', handleClickOutside);
      
      // Fix dropdown positioning after component is mounted
      setTimeout(() => {
        fixDropdownPositioning();
      }, 100);
    });

    // Cleanup on unmount
    onUnmounted(() => {
      document.removeEventListener('click', handleClickOutside);
    });
    
    return {
      findings,
      loading,
      error,
      summary,
      statusFilterConfig,
      sortByConfig,
      businessUnitFilterConfig,
      categoryFilterConfig,
      
      // Modal and workflow state
      showModal,
      modalAction,
      selectedIncident,
      showAssignmentWorkflow,
      
      // Assignment related data
      selectedReviewer,
      assignmentNotes,
      availableUsers,
      loadingUsers,
      
      // Current user data
      currentUser,
      currentUserName,
      
      // Mitigation workflow data
      mitigationSteps,
      newMitigationStep,
      mitigationDueDate,

      filterStatus,
      filterBusinessUnit,
      filterCategory,
      sortBy,
      exportFormat,
      isExporting,
      isQuickLoading,
      
      // Framework filter
      selectedFramework,
      frameworks,
      loadingFrameworks,
      
      // Dropdown state
      dropdownOpenFor,
      
      // Search query
      searchQuery,
      
      // Table columns and column chooser
      tableColumns,
      visibleTableColumns,
      visibleColumnKeys,
      showColumnEditor,
      columnSearchQuery,
      columnDefinitions,
      filteredColumnDefinitions,
      
      // Search methods
      handleSearchInput,
      
      fetchData,
      fetchUsers,
      fetchBusinessUnits,
      fetchCategories,
      fetchFrameworks,
      fetchSelectedFramework,
      loadCurrentUser,
      applyFilters,
      filterByStatus,
      getRowClass,
      getStatusClass,
      viewDetails,
      
      // Table methods
      initializeTableColumns,
      
      // Column chooser methods
      toggleColumnEditor,
      toggleColumnVisibility,
      isColumnVisible,
      selectAllColumns,
      deselectAllColumns,
      
      // Dropdown methods
      toggleActionDropdown,
      closeAllDropdowns,
      handleDropdownAction,
      
      // Modal and workflow methods
      openSolveModal,
      openRejectModal,
      openAssignModal,
      closeModal,
      closeAssignmentWorkflow,
      addMitigationStep,
      removeMitigationStep,
      getTodayDate,
      loadExistingMitigations,
      confirmAssignmentWorkflow,
      confirmSolve,
      confirmReject,
      openCloseModal,
      confirmClose,

      formatDate,
      truncateText,
      exportAuditFindings,
      
      // Clear methods
      clearSearch,
      clearAllFilters,
      hasActiveFilters,
      
      // Dropdown positioning fix
      fixDropdownPositioning
    };
  }
};
</script>

<style scoped>
@import './AuditFindings.css';

/* Current user display styles */
.current-user-display {
  padding: 12px 15px;
  background-color: #f8f9fa;
  border: 2px solid #e3f2fd;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.current-user-name {
  font-weight: 600;
  color: #1976d2;
  font-size: 14px;
}

.current-user-note {
  font-size: 12px;
  color: #666;
  font-style: italic;
}

/* Loading and error states for user selection */
.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  color: #1976d2;
  font-size: 14px;
}

.no-users-message {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  color: #f44336;
  font-size: 14px;
}

.assign-select:disabled {
  background-color: #f5f5f5;
  color: #999;
  cursor: not-allowed;
}

.retry-btn {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  margin-left: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s ease;
}

.retry-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #1565c0 0%, #0d47a1 100%);
  transform: translateY(-1px);
}

.retry-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
}
</style> 