<template>
  <div class="incident-view-container">
    <div class="incident-view-header">
      <h2 class="incident-view-title">Incident Management</h2>
      <div class="incident-header-actions">
        <!-- Export controls -->
        <div class="incident-export-controls">
          <select v-model="exportFormat" class="incident-export-format-select">
            <option value="xlsx">Select format</option>
            <option value="csv">CSV (.csv)</option>
            <option value="pdf">PDF (.pdf)</option>
            <option value="json">JSON (.json)</option>
            <option value="xml">XML (.xml)</option>
            <option value="txt">Text (.txt)</option>
          </select>
          <button @click="exportIncidents" class="incident-export-btn" :disabled="isExporting">
            <i class="fas fa-download" v-if="!isExporting"></i>
            <span v-if="isExporting">Exporting...</span>
            <span v-else>Export</span>
          </button>
        </div>
      </div>
    </div>
    
    <div class="incident-list-wrapper">
      <!-- Loading State -->
      <div v-if="isLoadingIncidents" class="incident-loading-container">
       
      </div>

      <!-- Search Section (no filter-controls container) -->
      <div v-else class="incident-search-section">
        <!-- <DynamicSearchBar
          v-model="searchQuery"
          placeholder="Search by ID, title, origin, priority, incident category, status, or date..."
          @input="filterIncidents"
          @search="performSearch"
        /> -->
        <!-- Filter Dropdowns -->
        <div class="incident-filter-container">
          <div class="incident-filter-row">
            <div class="incident-filter-item">
              <label class="incident-filter-label">FILTER BY FRAMEWORK:</label>
              <select v-model="selectedFramework" @change="onFrameworkChange" class="incident-filter-select">
                <option value="">All Frameworks</option>
                <option v-for="fw in frameworks" :key="fw.id" :value="fw.id">{{ fw.name }}</option>
              </select>
            </div>
            <!-- <div class="incident-filter-item">
              <label class="incident-filter-label">FILTER BY STATUS:</label>
              <select v-model="selectedStatus" @change="onStatusChange" class="incident-filter-select">
                <option value="">All Statuses</option>
                <option value="Open">Open</option>
                <option value="Assigned">Assigned</option>
                <option value="Approved">Approved</option>
                <option value="Rejected">Rejected</option>
                <option value="Scheduled">Scheduled</option>
                <option value="Under Review">Under Review</option>
                <option value="Pending Review">Pending Review</option>
                <option value="Closed">Closed</option>
                <option value="In Progress">In Progress</option>
              </select>
            </div> -->
            <!-- <div class="incident-filter-item">
              <label class="incident-filter-label">FILTER BY CATEGORY:</label>
              <select v-model="selectedBusinessCategory" @change="onBusinessCategoryChange" class="incident-filter-select">
                <option value="">All Categories</option>
                <option v-for="category in businessCategories" :key="category" :value="category">{{ category }}</option>
              </select>
            </div> -->
            <!-- <div class="incident-filter-item">
              <label class="incident-filter-label">FILTER BY BUSINESS UNIT:</label>
              <select v-model="selectedBusinessUnit" @change="onBusinessUnitChange" class="incident-filter-select">
                <option value="">All Business Units</option>
                <option v-for="businessUnit in businessUnits" :key="businessUnit" :value="businessUnit">{{ businessUnit }}</option>
              </select>
            </div> -->
            <div class="incident-filter-item">
              <button @click="clearAllFilters" class="incident-clear-filters-btn">
                <i class="fas fa-times"></i>
                CLEAR FILTERS
              </button>
            </div>
          </div>
          
          <!-- Debug Filter Info (remove in production) -->
          <div v-if="false" class="incident-debug-info" style="background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 4px; font-size: 12px;">
            <strong>Debug Info:</strong><br>
            Framework: {{ selectedFramework || 'None' }}<br>
            Policy: {{ selectedPolicy || 'None' }}<br>
            SubPolicy: {{ selectedSubPolicy || 'None' }}<br>
            Priority: {{ selectedPriority || 'None' }}<br>
            Frameworks loaded: {{ frameworks.length }}<br>
            Policies loaded: {{ policies.length }}<br>
            Subpolicies loaded: {{ subpolicies.length }}<br>
            Incidents loaded: {{ incidents.length }}
          </div>
          
          <!-- Clear Filters Button -->
        </div>
      </div>

      <!-- Dynamic Table -->
      <DynamicTable
        v-if="!isLoadingIncidents"
        :data="filteredIncidents"
        :columns="visibleTableColumns"
        :unique-key="'IncidentId'"
        :show-pagination="true"
        :default-page-size="20"
        :page-size-options="[10, 20, 50, 100]"
        @row-click="handleRowClick"
        @open-column-chooser="toggleColumnEditor"
      >
        <!-- Custom Title Cell with Router Link -->
        <template #cell-IncidentTitle="{ row }">
          <router-link :to="`/incident/${row.IncidentId}`" class="incident-title-link">
            {{ row.IncidentTitle }}
          </router-link>
        </template>

        <!-- Custom Status Cell with Status Badge -->
        <template #cell-Status="{ row }">
          <span :class="getIncidentStatusClass(row.Status)">
            {{ getStatusDisplayText(row.Status) }}
          </span>
        </template>

        <!-- Custom Actions Cell -->
        <template #cell-Actions="{ row }">
          <div v-if="row.Status === 'Scheduled'" class="incident-action-text">
            Mitigated to Risk
          </div>
          <div v-else-if="row.Status === 'Rejected'" class="incident-action-text">
            {{ row.RejectionSource === 'RISK' ? 'Rejected from Risk' : 'Rejected as Incident' }}
          </div>
          <div v-else-if="row.Status === 'Assigned'" class="incident-action-text">
            Assigned
          </div>
          <div v-else-if="row.Status === 'Approved'" class="incident-action-text">
            Approved
          </div>
          <div v-else-if="row.Status === 'Active'" class="incident-action-text">
            Active
          </div>
          <div v-else-if="row.Status === 'Under Review' || row.Status === 'PENDING REVIEW'" class="incident-action-text">
            Pending Review
          </div>
          <div v-else-if="row.Status === 'Completed'" class="incident-action-text">
            Completed
          </div>
          <div v-else-if="row.Status === 'Closed'" class="incident-action-text">
            Closed
          </div>
          <div v-else-if="row.Status === 'Open' || !row.Status || row.Status.trim() === ''">
            <div class="incident-actions-container">
              <i class="fas fa-user-plus action-icon assign-icon" @click.stop="handleDropdownAction('assign', row)" title="Assign as Incident"></i>
              <i class="fas fa-arrow-up action-icon escalate-icon" @click.stop="handleDropdownAction('escalate', row)" title="Escalate to Risk"></i>
              <i class="fas fa-times action-icon close-icon" @click.stop="handleDropdownAction('close', row)" title="Close Incident"></i>
            </div>
          </div>
          <div v-else-if="row.Status && row.Status.trim() !== ''" class="incident-action-text">
            {{ row.Status }}
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
              <button type="button" class="incident-column-action-btn" @click="selectAllColumns">
                <i class="fas fa-check-double"></i> Select All
              </button>
              <button type="button" class="incident-column-action-btn" @click="deselectAllColumns">
                <i class="fas fa-times-circle"></i> Deselect All
              </button>
              <button type="button" class="incident-column-action-btn" @click="resetColumnSelection">
                <i class="fas fa-undo"></i> Reset to Default
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
                  class="incident-column-checkbox"
                  @click.stop="toggleColumnVisibility(column.key)"
                />
                <label class="incident-column-label">{{ column.label }}</label>
              </div>
            </div>
            
            <div v-if="filteredColumnDefinitions.length === 0" class="incident-column-editor-empty">
              <i class="fas fa-search"></i>
              <p>No columns found matching "{{ columnSearchQuery }}"</p>
            </div>
            
            <div class="incident-column-editor-footer">
              <button type="button" class="incident-column-apply-btn" @click="toggleColumnEditor">
                <i class="fas fa-check"></i> Apply
              </button>
            </div>
          </div>
        </div>
      </transition>

      <!-- No Incidents Message -->
      <div v-if="!isLoadingIncidents && incidents.length === 0" class="incident-no-incidents-message">
        <div class="incident-no-data-container">
          <i class="fas fa-exclamation-triangle incident-no-data-icon"></i>
          <h3>No Incidents Found</h3>
          <p v-if="hasActiveFilters">
            No incidents match your current filters. Try adjusting your search criteria.
          </p>
          <p v-else>
            No incidents are available at the moment.
          </p>
        </div>
      </div>
    </div>
    
    <!-- Modal for Solve/Reject -->
    <div v-if="showModal && modalAction !== 'assign'" class="incident-modal-overlay" @click="closeModal">
      <div class="incident-modal-container" @click.stop>
        <button class="incident-modal-close-btn" @click="closeModal">✕</button>
        <div class="incident-modal-content">
          <div v-if="modalAction === 'solve'" class="incident-solve-container">
            <div class="incident-solve-icon">🔄</div>
            <h3 class="incident-modal-title incident-solve">Forwarded to Risk</h3>
            <p class="incident-modal-subtitle">You will be directed to the Risk module</p>
            <div class="incident-modal-footer">
              <button @click="confirmSolve" class="incident-modal-btn incident-confirm-btn">Confirm Forward</button>
              <button @click="closeModal" class="incident-modal-btn incident-cancel-btn">Cancel</button>
            </div>
          </div>
          
          <div v-else-if="modalAction === 'reject'" class="incident-rejected-container">
            <div class="incident-rejected-icon">✕</div>
            <h3 class="incident-modal-title incident-rejected">REJECTED</h3>
            <div class="incident-modal-footer">
              <button @click="confirmReject" class="incident-modal-btn incident-reject-btn">Confirm Reject</button>
              <button @click="closeModal" class="incident-modal-btn incident-cancel-btn">Cancel</button>
            </div>
          </div>

          <div v-else-if="modalAction === 'close'" class="incident-rejected-container">
            <div class="incident-rejected-icon">✕</div>
            <h3 class="incident-modal-title incident-rejected">CLOSED</h3>
            <div class="incident-modal-footer">
              <button @click="confirmClose" class="incident-modal-btn incident-reject-btn">Confirm Close</button>
              <button @click="closeModal" class="incident-modal-btn incident-cancel-btn">Cancel</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Assignment Workflow Section -->
    <div v-if="showAssignmentWorkflow" class="incident-assignment-workflow-section">
      <div class="incident-assignment-header">
        <button class="incident-back-btn" @click="closeAssignmentWorkflow">
          <i class="fas fa-arrow-left"></i> Back to Incidents
        </button>
      </div>
      <div class="assignment-body">
        <div class="incident-summary">
          <h3>{{ selectedIncident.IncidentTitle || 'Incident #' + selectedIncident.IncidentId }}</h3>
          <div class="incident-details">
            <p><strong>ID:</strong> {{ selectedIncident.IncidentId }}</p>
            <p><strong>Category:</strong> {{ selectedIncident.RiskCategory }}</p>
            <p><strong>Priority:</strong> {{ selectedIncident.RiskPriority }}</p>
            <p><strong>Origin:</strong> {{ selectedIncident.Origin }}</p>
          </div>
        </div>

        <!-- User Selection -->
        <div class="incident-user-selection">
          <h3>Assignment Details</h3>
          <div class="incident-user-form">
              <div class="incident-form-group">
                <label for="assigner">Assigner:</label>
                <div class="incident-current-user-display">
                  <span class="current-user-name">{{ currentUserName || 'Loading...' }}</span>
                  
                </div>
              </div>
              
              <div class="incident-form-group">
                <label for="reviewer">Reviewer:</label>
                <select v-model="selectedReviewer" id="reviewer" class="incident-assign-select" required>
                  <option value="">Select Reviewer</option>
                  <option v-for="user in availableUsers" :key="user.id" :value="user.id">
                    {{ user.name }} ({{ user.role }})
                  </option>
                </select>
            </div>
          </div>
        </div>
        
        <!-- Mitigation Workflow -->
        <div class="incident-mitigation-workflow">
          <h3>Mitigation Steps</h3>
          <!-- Existing Mitigation Steps -->
          <div v-if="mitigationSteps.length" class="incident-workflow-timeline">
            <div v-for="(step, index) in mitigationSteps" :key="index" class="incident-workflow-step">
              <div class="incident-step-number">{{ index + 1 }}</div>
              <div class="incident-step-content">
                <textarea 
                  v-model="step.description" 
                  class="incident-mitigation-textarea"
                  placeholder="Enter mitigation step description"
                ></textarea>
                <div class="incident-step-actions">
                  <button @click="removeMitigationStep(index)" class="incident-remove-step-btn">
                    <i class="fas fa-trash"></i> Remove
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="incident-no-mitigations">
            <p>No mitigation steps found for this incident. Add steps below.</p>
          </div>
          
          <!-- Add New Mitigation Step -->
          <div class="incident-add-mitigation">
            <textarea 
              v-model="newMitigationStep" 
              class="incident-mitigation-textarea"
              placeholder="Enter mitigation step(s). Use commas to separate multiple steps (e.g., 'Step 1, Step 2, Step 3')"
            ></textarea>
            <button @click="addMitigationStep" class="incident-add-step-btn" :disabled="!newMitigationStep.trim()">
              <i class="fas fa-plus"></i> Add Mitigation Step
            </button>
          </div>
          
          <!-- Due Date Input -->
          <div class="incident-due-date-section">
            <h4>Due Date for Mitigation Completion</h4>
            <input 
              type="date" 
              v-model="mitigationDueDate" 
              class="incident-due-date-input" 
              :min="getTodayDate()"
            />
          </div>

          <!-- Assignment Notes -->
          <div class="incident-assignment-notes-section">
            <h4>Assignment Notes (Optional)</h4>
                <textarea 
                  v-model="assignmentNotes" 
              class="incident-assignment-notes-textarea"
                  placeholder="Add any specific instructions or notes for the assignees..."
                  rows="3"
                ></textarea>
            </div>
            
          <!-- Submit Section -->
          <div class="incident-assignment-actions">
              <button 
              @click="confirmAssignmentWorkflow" 
              class="incident-submit-assignment-btn"
              :disabled="!selectedReviewer || mitigationSteps.length === 0 || !mitigationDueDate"
              >
              <i class="fas fa-user-plus"></i> Assign Incident with Mitigations
              </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { axiosInstance } from '@/config/api.js';
import { API_ENDPOINTS } from '../../config/api.js';
import incidentService from '../../services/incidentService.js';
import './Incident.css';
import { PopupService } from '@/modules/popup';
import { AccessUtils, SessionUtils } from '@/utils/accessUtils';
// import DynamicSearchBar from '@/components/Dynamicalsearch.vue';
import DynamicTable from '@/components/DynamicTable.vue';

export default {
  name: 'IncidentManagement',
  components: {
    // DynamicSearchBar,
    DynamicTable
  },
  data() {
    return {
      incidents: [], // Always initialize as empty array
      searchQuery: '',
      sortField: '',
      sortOrder: 'asc',
      searchTimeout: null,
      isLoadingIncidents: false,
      lastFetchTime: null, // Cache timestamp
      cacheTimeout: 300000, // 5 minutes cache (increased to prevent timeouts)
      currentPage: 1,
      incidentsPerPage: 20,
      totalIncidents: 0,
      hasMoreData: false,
      showModal: false,
      modalAction: '', // 'solve', 'reject', or 'assign'
      selectedIncident: null,
      exportFormat: 'xlsx',
      isExporting: false,
      // Assignment related data
      selectedAssigner: '',
      selectedReviewer: '',
      assignmentNotes: '',
      availableUsers: [],
      // Current user data
      currentUser: null,
      currentUserName: '',
      // Assignment workflow data
      showAssignmentWorkflow: false,
      mitigationSteps: [],
      newMitigationStep: '',
      mitigationDueDate: '',
      // Dropdown state
      dropdownOpenFor: null,
      frameworks: [],
      policies: [],
      subpolicies: [],
      priorities: ['Critical', 'High', 'Medium', 'Low'],
      businessUnits: [],
      businessCategories: [],
      selectedFramework: '',
      selectedPolicy: '',
      selectedSubPolicy: '',
      selectedPriority: '',
      selectedBusinessUnit: '',
      selectedBusinessCategory: '',
      selectedStatus: '',
      // Column menu and filter data
      activeFilterColumn: null,
      activeFilterColumnLabel: '',
      columnFilterSearch: '',
      columnFilterTempSelection: [],
      columnFilterPosition: { top: '0px', left: '0px' },
      columnFilters: {},
      lastFilterTrigger: null,
      activeMenuColumn: null,
      activeMenuColumnLabel: '',
      columnMenuPosition: { top: '0px', left: '0px' },
      showPinSubmenu: false,
      columnPins: {},
      columnWidths: {},
      lastMenuTrigger: null,
      // Column chooser data
      showColumnEditor: false,
      columnSearchQuery: '',
      columnDefinitions: [
        { key: 'IncidentId', label: 'ID', defaultVisible: true },
        { key: 'IncidentTitle', label: 'Title', defaultVisible: true },
        { key: 'Description', label: 'Description', defaultVisible: false },
        { key: 'Origin', label: 'Origin', defaultVisible: true },
        { key: 'RiskPriority', label: 'Priority', defaultVisible: true },
        { key: 'IncidentCategory', label: 'Incident Category', defaultVisible: true },
        { key: 'RiskCategory', label: 'Risk Category', defaultVisible: false },
        { key: 'Criticality', label: 'Criticality', defaultVisible: false },
        { key: 'Date', label: 'Date', defaultVisible: true },
        { key: 'Time', label: 'Time', defaultVisible: false },
        { key: 'Status', label: 'Status', defaultVisible: true },
        { key: 'AffectedBusinessUnit', label: 'Business Unit', defaultVisible: true },
        { key: 'SystemsAssetsInvolved', label: 'Systems/Assets', defaultVisible: false },
        { key: 'GeographicLocation', label: 'Location', defaultVisible: false },
        { key: 'InitialImpactAssessment', label: 'Impact Assessment', defaultVisible: false },
        { key: 'InternalContacts', label: 'Internal Contacts', defaultVisible: false },
        { key: 'ExternalPartiesInvolved', label: 'External Parties', defaultVisible: false },
        { key: 'RegulatoryBodies', label: 'Regulatory Bodies', defaultVisible: false },
        { key: 'RelevantPoliciesProceduresViolated', label: 'Policies Violated', defaultVisible: false },
        { key: 'ControlFailures', label: 'Control Failures', defaultVisible: false },
        { key: 'LessonsLearned', label: 'Lessons Learned', defaultVisible: false },
        { key: 'IncidentClassification', label: 'Classification', defaultVisible: false },
        { key: 'PossibleDamage', label: 'Possible Damage', defaultVisible: false },
        { key: 'CostOfIncident', label: 'Cost', defaultVisible: false },
        { key: 'RepeatedNot', label: 'Repeated', defaultVisible: false },
        { key: 'ReopenedNot', label: 'Reopened', defaultVisible: false },
        { key: 'RejectionSource', label: 'Rejection Source', defaultVisible: false },
        { key: 'CreatedAt', label: 'Created At', defaultVisible: false },
        { key: 'IdentifiedAt', label: 'Identified At', defaultVisible: false },
        { key: 'AssignedDate', label: 'Assigned Date', defaultVisible: false },
        { key: 'MitigationDueDate', label: 'Mitigation Due', defaultVisible: false },
        { key: 'MitigationCompletedDate', label: 'Mitigation Completed', defaultVisible: false },
        { key: 'Comments', label: 'Comments', defaultVisible: false },
        { key: 'AssignmentNotes', label: 'Assignment Notes', defaultVisible: false },
        { key: 'Mitigation', label: 'Mitigation', defaultVisible: false },
        { key: 'Actions', label: 'Actions', defaultVisible: true }
      ],
      visibleColumnKeys: [],
      // DynamicTable columns configuration
      tableColumns: []
    }
  },
  computed: {
    hasActiveFilters() {
      return this.selectedFramework || this.selectedPolicy || this.selectedSubPolicy || this.selectedPriority || this.selectedBusinessUnit || this.selectedBusinessCategory || this.searchQuery.trim();
    },
    filteredIncidents() {
      let result = [...(this.incidents || [])];
      
      // Apply search filter
      if (this.searchQuery && this.searchQuery.trim()) {
        const searchLower = this.searchQuery.toLowerCase().trim();
        result = result.filter(inc => 
          String(inc.IncidentId).includes(searchLower) ||
          (inc.IncidentTitle && inc.IncidentTitle.toLowerCase().includes(searchLower)) ||
          (inc.Origin && inc.Origin.toLowerCase().includes(searchLower)) ||
          (inc.RiskPriority && inc.RiskPriority.toLowerCase().includes(searchLower)) ||
          (inc.IncidentCategory && inc.IncidentCategory.toLowerCase().includes(searchLower)) ||
          (inc.Status && inc.Status.toLowerCase().includes(searchLower)) ||
          (inc.AffectedBusinessUnit && inc.AffectedBusinessUnit.toLowerCase().includes(searchLower))
        );
      }
      
      // Apply framework filter
      if (this.selectedFramework) {
        result = result.filter(inc => inc.framework_id == this.selectedFramework);
      }
      
      // Apply status filter
      if (this.selectedStatus) {
        result = result.filter(inc => inc.Status === this.selectedStatus);
      }
      
      // Apply business unit filter
      if (this.selectedBusinessUnit) {
        result = result.filter(inc => inc.AffectedBusinessUnit === this.selectedBusinessUnit);
      }
      
      // Apply category filter
      if (this.selectedBusinessCategory) {
        result = result.filter(inc => inc.IncidentCategory === this.selectedBusinessCategory);
      }
      
      // Add virtual Actions field for sorting/filtering
      return result.map(inc => ({
        ...inc,
        Actions: this.getActionText(inc)
      }));
    },
    visibleTableColumns() {
      // Filter columns based on visibility set in column chooser
      if (this.visibleColumnKeys.length === 0) {
        // If no selection made yet, show default visible columns
        const defaultKeys = this.columnDefinitions
          .filter(col => col.defaultVisible)
          .map(col => col.key);
        return this.tableColumns.filter(col => defaultKeys.includes(col.key));
      }
      return this.tableColumns.filter(col => this.visibleColumnKeys.includes(col.key));
    },
    filteredColumnDefinitions() {
      const search = this.columnSearchQuery.toLowerCase().trim();
      if (!search) {
        return this.columnDefinitions;
      }
      return this.columnDefinitions.filter(col =>
        col.label.toLowerCase().includes(search)
      );
    }
  },
  watch: {
    incidents: {
      handler(newIncidents) {
        console.log('Incidents array updated. Current statuses:', 
          newIncidents.slice(0, 5).map(inc => ({ id: inc.IncidentId, status: inc.Status }))
        );
        console.log('Total incidents in array:', newIncidents.length);
        console.log('All incident IDs:', newIncidents.map(inc => inc.IncidentId));
      },
      deep: true
    }
  },
  async mounted() {
    console.log('Incident component mounted - checking for stored data first...');
    this.loadCurrentUser();
    
    // Initialize table columns
    this.initializeTableColumns();
    
    // First, try to load from stored data (from login)
    let storedData = incidentService.getAllData();
    let hasStoredData = storedData.lastFetchTime !== null;
    
    // Strategy: Check for stored data and wait for first batch if needed
    console.log('🚀 [Incident.vue] Checking for stored incident data...');
    console.log('🔍 [Incident.vue] Current service state:', {
      hasLastFetchTime: !!storedData.lastFetchTime,
      incidentsCount: incidentService.getData('incidents')?.length || 0,
      hasPromise: !!window.incidentDataFetchPromise
    });
    
    // Check if we already have data from the first batch
    const immediateCheck = incidentService.getData('incidents');
    if (immediateCheck && Array.isArray(immediateCheck) && immediateCheck.length > 0) {
      console.log(`✅ [Incident.vue] Found ${immediateCheck.length} incidents immediately! Loading now.`);
      hasStoredData = true;
    } else if (window.incidentDataFetchPromise) {
      // If fetch is in progress, wait for first batch (max 10 seconds)
      console.log('⏳ [Incident.vue] No immediate data. Fetch in progress, waiting for first batch...');
      let waitCount = 0;
      const maxWait = 100; // 10 seconds max (increased from 3)
      let foundData = false;
      
      while (waitCount < maxWait && !foundData) {
        await new Promise(resolve => setTimeout(resolve, 100));
        waitCount++;
        
        // Check if first batch is available
        const incidents = incidentService.getData('incidents');
        if (incidents && Array.isArray(incidents) && incidents.length > 0) {
          console.log(`✅ [Incident.vue] First batch ready after ${waitCount * 100}ms! Found ${incidents.length} incidents.`);
          hasStoredData = true;
          foundData = true;
          break;
        }
        
        // Log progress every second
        if (waitCount % 10 === 0) {
          console.log(`⏳ [Incident.vue] Still waiting... (${waitCount * 100}ms elapsed)`);
        }
      }
      
      if (!foundData) {
        console.warn(`⚠️ [Incident.vue] Timeout after ${waitCount * 100}ms. No stored data found.`);
      }
      
      // Final check
      storedData = incidentService.getAllData();
      hasStoredData = storedData.lastFetchTime !== null || (storedData.incidents && storedData.incidents.length > 0);
    } else {
      console.warn('⚠️ [Incident.vue] No stored data and no fetch promise. Will fetch from API.');
    }
    
    // Continue fetching remaining batches in background (don't block rendering)
    if (window.incidentDataFetchPromise && hasStoredData) {
      console.log('📥 Continuing to fetch remaining batches in background...');
      window.incidentDataFetchPromise.then(() => {
        console.log('✅ All batches completed in background');
      }).catch(() => {
        console.warn('⚠️ Background fetch completed with errors');
      });
    }
    
    if (hasStoredData) {
      const incidentsCount = incidentService.getData('incidents')?.length || 0;
      console.log(`📦 [Incident.vue] Loading ${incidentsCount} incidents from storage...`);
      // Load stored data immediately
      await this.loadFromStoredData();
      console.log(`✅ [Incident.vue] Loaded from storage. Displaying ${this.incidents.length} incidents.`);
    } else {
      console.warn('⚠️ [Incident.vue] No stored data available after waiting. Fetching from API...');
      // Fallback to API calls ONLY if no stored data exists
      await this.fetchFrameworks();
      await this.fetchSelectedFramework();
      // Don't call fetchIncidents() here - it will check stored data first
      // Only call if truly no data exists
      const finalCheck = incidentService.getData('incidents');
      if (!finalCheck || finalCheck.length === 0) {
        console.warn('⚠️ [Incident.vue] No stored data at all - calling API as last resort');
        this.fetchIncidents();
      } else {
        console.log('✅ [Incident.vue] Found stored data after all - loading from storage');
        await this.loadFromStoredData();
      }
    this.fetchBusinessUnits();
    this.fetchBusinessCategories();
    }
    
    // Ensure the main document scrolls to see all checklist data
    document.documentElement.style.overflow = 'auto';
    document.body.style.overflow = 'auto';
    
    // Add resize event listener to handle responsive behavior
    window.addEventListener('resize', this.handleResize);
    
    // Add click event listener to close dropdowns when clicking outside
    document.addEventListener('click', this.closeAllDropdowns);
    
    // Initialize visible columns
    this.visibleColumnKeys = this.columnDefinitions
      .filter(col => col.defaultVisible)
      .map(col => col.key);
  },
  beforeUnmount() {
    // Clean up event listeners
    window.removeEventListener('resize', this.handleResize);
    document.removeEventListener('click', this.closeAllDropdowns);
    
    // Clean up column filter and menu event listeners
    document.removeEventListener('click', this.handleFilterDocumentClick, true);
    document.removeEventListener('keydown', this.handleFilterEscapePress);
    document.removeEventListener('click', this.handleMenuDocumentClick, true);
    document.removeEventListener('keydown', this.handleMenuEscapePress);
  },
  methods: {
      initializeTableColumns() {
        this.tableColumns = [
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
            key: 'Description',
            label: 'Description',
            sortable: true,
            width: '200px',
            resizable: true,
            defaultVisible: false
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
            key: 'RiskPriority',
            label: 'Priority',
            sortable: true,
            width: '120px',
            resizable: true,
            defaultVisible: true
          },
          {
            key: 'IncidentCategory',
            label: 'Incident Category',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: true
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
            key: 'Criticality',
            label: 'Criticality',
            sortable: true,
            width: '120px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'Date',
            label: 'Date',
            sortable: true,
            width: '120px',
            resizable: true,
            defaultVisible: true
          },
          {
            key: 'Time',
            label: 'Time',
            sortable: true,
            width: '100px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'Status',
            label: 'Status',
            sortable: true,
            slot: true,
            width: '150px',
            resizable: true,
            defaultVisible: true
          },
          {
            key: 'AffectedBusinessUnit',
            label: 'Business Unit',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: true
          },
          {
            key: 'SystemsAssetsInvolved',
            label: 'Systems/Assets',
            sortable: true,
            width: '180px',
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
            key: 'InitialImpactAssessment',
            label: 'Impact Assessment',
            sortable: true,
            width: '200px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'InternalContacts',
            label: 'Internal Contacts',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'ExternalPartiesInvolved',
            label: 'External Parties',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'RegulatoryBodies',
            label: 'Regulatory Bodies',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'RelevantPoliciesProceduresViolated',
            label: 'Policies Violated',
            sortable: true,
            width: '200px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'ControlFailures',
            label: 'Control Failures',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'LessonsLearned',
            label: 'Lessons Learned',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'IncidentClassification',
            label: 'Classification',
            sortable: true,
            width: '150px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'PossibleDamage',
            label: 'Possible Damage',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'CostOfIncident',
            label: 'Cost',
            sortable: true,
            width: '120px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'RepeatedNot',
            label: 'Repeated',
            sortable: true,
            width: '100px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'ReopenedNot',
            label: 'Reopened',
            sortable: true,
            width: '100px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'RejectionSource',
            label: 'Rejection Source',
            sortable: true,
            width: '150px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'CreatedAt',
            label: 'Created At',
            sortable: true,
            width: '150px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'IdentifiedAt',
            label: 'Identified At',
            sortable: true,
            width: '150px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'AssignedDate',
            label: 'Assigned Date',
            sortable: true,
            width: '150px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'MitigationDueDate',
            label: 'Mitigation Due',
            sortable: true,
            width: '150px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'MitigationCompletedDate',
            label: 'Mitigation Completed',
            sortable: true,
            width: '180px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'Comments',
            label: 'Comments',
            sortable: true,
            width: '200px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'AssignmentNotes',
            label: 'Assignment Notes',
            sortable: true,
            width: '200px',
            resizable: true,
            defaultVisible: false
          },
          {
            key: 'Actions',
            label: 'Actions',
            sortable: true,
            slot: true,
            width: '180px',
            resizable: true,
            defaultVisible: true,
            filterOptions: [
              { value: 'Mitigated to Risk', label: 'Mitigated to Risk' },
              { value: 'Rejected from Risk', label: 'Rejected from Risk' },
              { value: 'Rejected as Incident', label: 'Rejected as Incident' },
              { value: 'Assigned', label: 'Assigned' },
              { value: 'Approved', label: 'Approved' },
              { value: 'Active', label: 'Active' },
              { value: 'Pending Review', label: 'Pending Review' },
              { value: 'Completed', label: 'Completed' },
              { value: 'Closed', label: 'Closed' },
              { value: 'Open', label: 'Open (with action icons)' }
            ]
          }
        ];
      },
      toggleColumnEditor() {
        this.showColumnEditor = !this.showColumnEditor;
        if (this.showColumnEditor) {
          // Initialize visible column keys if empty
          if (this.visibleColumnKeys.length === 0) {
            this.visibleColumnKeys = this.columnDefinitions
              .filter(col => col.defaultVisible)
              .map(col => col.key);
          }
        }
      },
      toggleColumnVisibility(columnKey) {
        const index = this.visibleColumnKeys.indexOf(columnKey);
        if (index > -1) {
          this.visibleColumnKeys.splice(index, 1);
        } else {
          this.visibleColumnKeys.push(columnKey);
        }
      },
      isColumnVisible(columnKey) {
        if (this.visibleColumnKeys.length === 0) {
          const col = this.columnDefinitions.find(c => c.key === columnKey);
          return col ? col.defaultVisible : false;
        }
        return this.visibleColumnKeys.includes(columnKey);
      },
      selectAllColumns() {
        this.visibleColumnKeys = this.columnDefinitions.map(col => col.key);
      },
      deselectAllColumns() {
        this.visibleColumnKeys = [];
      },
      resetColumnSelection() {
        this.visibleColumnKeys = this.columnDefinitions
          .filter(col => col.defaultVisible)
          .map(col => col.key);
        this.columnSearchQuery = '';
      },
      getActionText(row) {
        // Return the text that would be displayed in the Actions column
        if (row.Status === 'Scheduled') {
          return 'Mitigated to Risk';
        } else if (row.Status === 'Rejected') {
          return row.RejectionSource === 'RISK' ? 'Rejected from Risk' : 'Rejected as Incident';
        } else if (row.Status === 'Assigned') {
          return 'Assigned';
        } else if (row.Status === 'Approved') {
          return 'Approved';
        } else if (row.Status === 'Active') {
          return 'Active';
        } else if (row.Status === 'Under Review' || row.Status === 'PENDING REVIEW') {
          return 'Pending Review';
        } else if (row.Status === 'Completed') {
          return 'Completed';
        } else if (row.Status === 'Closed') {
          return 'Closed';
        } else if (row.Status === 'Open' || !row.Status || row.Status.trim() === '') {
          return 'Open';
        } else if (row.Status && row.Status.trim() !== '') {
          return row.Status;
        }
        return '';
      },
      handleRowClick(row) {
        // Optional: Handle row click if needed
        console.log('Row clicked:', row);
      },
      // Dropdown methods
      toggleActionDropdown(incidentId) {
        console.log('Toggle dropdown for incident:', incidentId);
        console.log('Current dropdownOpenFor:', this.dropdownOpenFor);
        
        if (this.dropdownOpenFor === incidentId) {
          this.dropdownOpenFor = null;
        } else {
          this.dropdownOpenFor = incidentId;
        }
        
        console.log('New dropdownOpenFor:', this.dropdownOpenFor);
      },
      closeAllDropdowns(event) {
        // Only close if clicking outside the dropdown
        if (event && event.target) {
          const isDropdownClick = event.target.closest('.action-dropdown-container');
          if (isDropdownClick) {
            return; // Don't close if clicking inside dropdown
          }
        }
        
        console.log('Closing all dropdowns');
        this.dropdownOpenFor = null;
      },
      handleDropdownAction(action, incident) {
        console.log('Dropdown action:', action, 'for incident:', incident.IncidentId);
        
        switch(action) {
          case 'assign':
            this.openAssignModal(incident);
            break;
          case 'escalate':
            PopupService.confirm(
              `Are you sure you want to escalate Incident #${incident.IncidentId} to Risk? This will forward the incident to the Risk module for further evaluation and mitigation.`,
              'Escalate to Risk',
              () => this.confirmSolve(incident)
            );
            break;
          case 'close':
            PopupService.confirm(
              `Are you sure you want to close Incident #${incident.IncidentId}? This action cannot be undone.`,
              'Close Incident',
              () => this.confirmClose(incident)
            );
            break;
        }
      },
      openSolveModal(incident) {
      this.selectedIncident = incident;
      this.modalAction = 'solve';
      this.showModal = true;
    },
    openRejectModal(incident) {
      this.selectedIncident = incident;
      this.modalAction = 'reject';
      this.showModal = true;
    },
    openAssignModal(incident) {
      this.selectedIncident = incident;
      this.showAssignmentWorkflow = true;
      // Reset assignment form
      this.selectedReviewer = '';
      this.assignmentNotes = '';
      this.newMitigationStep = '';
      this.mitigationDueDate = '';
      
      // Load existing mitigation steps from the incident's Mitigation field
      console.log('Selected incident:', incident);
      console.log('Incident Mitigation field:', incident.Mitigation);
      this.loadExistingMitigations(incident);
      
      // Lazy load users only when needed
      if (this.availableUsers.length === 0) {
        this.fetchUsers();
      }
    },
    openCloseModal(incident) {
      this.selectedIncident = incident;
      this.modalAction = 'close';
      this.showModal = true;
    },
    closeModal() {
      this.showModal = false;
      this.selectedIncident = null;
      // Reset assignment form data
      this.selectedReviewer = '';
      this.assignmentNotes = '';
    },
    closeAssignmentWorkflow() {
      this.showAssignmentWorkflow = false;
      this.selectedIncident = null;
      // Reset assignment form data
      this.selectedReviewer = '';
      this.assignmentNotes = '';
      this.mitigationSteps = [];
      this.newMitigationStep = '';
      this.mitigationDueDate = '';
    },
    addMitigationStep() {
      if (!this.newMitigationStep.trim()) return;
      
      // Check if the user entered multiple steps separated by commas
      const steps = this.newMitigationStep.split(',').filter(step => step.trim());
      
      if (steps.length > 1) {
        // Multiple comma-separated steps
        steps.forEach(step => {
          this.mitigationSteps.push({
            description: step.trim(),
            status: 'Not Started'
          });
        });
      } else {
        // Single step
        this.mitigationSteps.push({
          description: this.newMitigationStep.trim(),
          status: 'Not Started'
        });
      }
      
      this.newMitigationStep = '';
    },
    removeMitigationStep(index) {
      this.mitigationSteps.splice(index, 1);
    },
    getTodayDate() {
      const today = new Date();
      const year = today.getFullYear();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      const day = String(today.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    },
    loadExistingMitigations(incident) {
      // Initialize with empty array
      this.mitigationSteps = [];
      
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
            let steps = [];
            
            // First try splitting by newlines
            const lineSteps = mitigationData.split('\n').filter(step => step.trim());
            
            if (lineSteps.length > 1) {
              // Multiple lines found, use line separation
              steps = lineSteps;
            } else {
              // Single line or no newlines, try splitting by commas
              const commaSteps = mitigationData.split(',').filter(step => step.trim());
              if (commaSteps.length > 1) {
                // Multiple comma-separated items found
                steps = commaSteps;
              } else {
                // Single step
                steps = [mitigationData];
              }
            }
            
            this.mitigationSteps = steps.map((step) => ({
              description: step.trim(),
              status: 'Not Started'
            }));
          } else if (Array.isArray(mitigationData)) {
            // Array format
            this.mitigationSteps = mitigationData.map(item => ({
              description: typeof item === 'string' ? item : (item.description || item.title || 'Mitigation step'),
              status: item.status || 'Not Started'
            }));
          } else if (typeof mitigationData === 'object') {
            // Object format (like {"1": "Step 1", "2": "Step 2"})
            this.mitigationSteps = Object.values(mitigationData).map(step => ({
              description: typeof step === 'string' ? step : (step.description || step.title || 'Mitigation step'),
              status: step.status || 'Not Started'
            }));
          }
          
          console.log('Loaded existing mitigation steps:', this.mitigationSteps);
        } catch (error) {
          console.error('Error parsing mitigation data:', error);
          // Fallback: treat as plain text
          this.mitigationSteps = [{
            description: incident.Mitigation,
            status: 'Not Started'
          }];
        }
      }
      
      // If no mitigation steps were loaded, start with empty array
      if (this.mitigationSteps.length === 0) {
        console.log('No existing mitigation steps found');
      }
    },
    confirmAssignmentWorkflow() {
      // Validate reviewer selection
      if (!this.selectedReviewer) {
        PopupService.warning('Please select a reviewer');
        return;
      }

      // Auto-set current user as assigner
      const currentUserId = this.currentUser?.user_id;
      if (!currentUserId) {
        PopupService.error('Unable to identify current user. Please refresh and try again.');
        return;
      }

      // Check if current user is trying to assign to themselves as reviewer
      if (currentUserId === this.selectedReviewer.toString()) {
        PopupService.warning('You cannot assign yourself as both assigner and reviewer');
        return;
      }

      if (this.mitigationSteps.length === 0) {
        PopupService.warning('Please add at least one mitigation step');
        return;
      }

      if (!this.mitigationDueDate) {
        PopupService.warning('Please select a due date');
        return;
      }

      // Safety check for selectedIncident
      if (!this.selectedIncident || !this.selectedIncident.IncidentId) {
        console.error('No incident selected for assignment');
        PopupService.error('No incident selected for assignment. Please try again.');
        return;
      }

      console.log('Assigning incident:', this.selectedIncident.IncidentId);

      // Safety check for availableUsers array
      if (!this.availableUsers || !Array.isArray(this.availableUsers)) {
        console.error('Available users not loaded');
        PopupService.error('User data not loaded. Please refresh the page and try again.');
        return;
      }

      // Find reviewer details - assigner is automatically the current user
      const reviewer = this.availableUsers.find(user => user.id === this.selectedReviewer);
      
      // Safety check for reviewer
      if (!reviewer) {
        console.error('Selected reviewer not found in available users');
        PopupService.error('Selected reviewer not found. Please try again.');
        return;
      }

      // Convert mitigations to the expected JSON format
      const mitigationsJson = {};
      this.mitigationSteps.forEach((step, index) => {
        mitigationsJson[index + 1] = step.description;
      });

      // Update incident with assignment details and mitigations
      axiosInstance.put(API_ENDPOINTS.INCIDENT_ASSIGN(this.selectedIncident.IncidentId), {
        status: 'Assigned',
        assigner_id: currentUserId,
        assigner_name: this.currentUserName,
        reviewer_id: this.selectedReviewer,
        reviewer_name: reviewer.name,
        assignment_notes: this.assignmentNotes,
        assigned_date: new Date().toISOString(),
        mitigations: mitigationsJson,
        due_date: this.mitigationDueDate
      })
      .then(response => {
        console.log('Incident assigned successfully - API response:', response.data);
        
        // Immediately update the local incident object for instant UI feedback
        if (this.incidents && Array.isArray(this.incidents)) {
          const incident = this.incidents.find(inc => inc.IncidentId === this.selectedIncident.IncidentId);
          if (incident) {
            incident.Status = 'Assigned';
            incident.AssignerId = currentUserId;
            incident.ReviewerId = this.selectedReviewer;
            console.log('Updated local incident status to Assigned');
          }
        }
        
        // Update filtered incidents as well
        if (this.filteredIncidents && Array.isArray(this.filteredIncidents)) {
          const filteredIncident = this.filteredIncidents.find(inc => inc.IncidentId === this.selectedIncident.IncidentId);
          if (filteredIncident) {
            filteredIncident.Status = 'Assigned';
            filteredIncident.AssignerId = currentUserId;
            filteredIncident.ReviewerId = this.selectedReviewer;
          }
        }
        
        // Refresh incidents list after assignment for data consistency
        this.fetchIncidents();
        
        // Show success message and close workflow
        PopupService.success('Incident assigned successfully with mitigation steps!');
        this.closeAssignmentWorkflow();
      })
      .catch(error => {
        console.error('Error assigning incident:', error);
        
        // Check if this is an access denied error first
        if (!AccessUtils.handleApiError(error, 'assign incidents')) {
          // Only show generic error if it's not an access denied error
          PopupService.error('Failed to assign incident. Please try again.');
        }
      });
    },
    confirmSolve(incident) {
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
          PopupService.success(`Incident #${incident.IncidentId} has been successfully escalated to Risk Management for further evaluation and mitigation.`, 'Escalated to Risk');
          
          // Immediately update the local incident object for instant UI feedback
          if (this.incidents && Array.isArray(this.incidents)) {
            const localIncident = this.incidents.find(inc => inc.IncidentId === incident.IncidentId);
            if (localIncident) {
              localIncident.Status = 'Scheduled';
              console.log('Updated local incident status to Scheduled');
            }
          }
          
          // Update filtered incidents as well
          if (this.filteredIncidents && Array.isArray(this.filteredIncidents)) {
            const filteredIncident = this.filteredIncidents.find(inc => inc.IncidentId === incident.IncidentId);
            if (filteredIncident) {
              filteredIncident.Status = 'Scheduled';
            }
          }
          
          // Close the modal immediately
          this.closeModal();
          
          // Refresh incidents list after status update for data consistency
          this.fetchIncidents();
        } else {
          // Handle unsuccessful response
          console.error('API returned unsuccessful response:', response.data);
          PopupService.error(response.data.message || 'Failed to escalate incident. Please try again.');
        }
      })
      .catch(error => {
        console.error('Error updating incident status:', error);
        console.error('Error details:', error.response);
        console.error('Error message:', error.message);
        
        // Check if this is an access denied error first
        if (!AccessUtils.handleApiError(error, 'escalate incidents')) {
          // Only show generic error if it's not an access denied error
          PopupService.error('Failed to escalate incident. Please try again.');
        }
      });
    },
    confirmReject() {
      console.log('Rejecting incident:', this.selectedIncident.IncidentId);
      
      // Update incident status to "Rejected"
      axiosInstance.put(API_ENDPOINTS.INCIDENT_STATUS(this.selectedIncident.IncidentId), {
        status: 'Rejected',
        rejection_source: 'INCIDENT'
      })
      .then(response => {
        console.log('Incident rejected - API response:', response.data);
        
        // Check if the response indicates success
        if (response.data.success) {
          // Show success message
          PopupService.success(`Incident #${this.selectedIncident.IncidentId} rejected successfully!`, 'Incident Rejected');
          
          // Immediately update the local incident object for instant UI feedback
          if (this.incidents && Array.isArray(this.incidents)) {
            const localIncident = this.incidents.find(inc => inc.IncidentId === this.selectedIncident.IncidentId);
            if (localIncident) {
              localIncident.Status = 'Rejected';
              localIncident.RejectionSource = 'INCIDENT';
              console.log('Updated local incident status to Rejected');
            }
          }
          
          // Update filtered incidents as well
          if (this.filteredIncidents && Array.isArray(this.filteredIncidents)) {
            const filteredIncident = this.filteredIncidents.find(inc => inc.IncidentId === this.selectedIncident.IncidentId);
            if (filteredIncident) {
              filteredIncident.Status = 'Rejected';
              filteredIncident.RejectionSource = 'INCIDENT';
            }
          }
          
          // Close the modal immediately
          this.closeModal();
          
          // Refresh incidents list after status update for data consistency
          this.fetchIncidents();
        } else {
          // Handle unsuccessful response
          console.error('API returned unsuccessful response:', response.data);
          PopupService.error(response.data.message || 'Failed to reject incident. Please try again.');
        }
      })
      .catch(error => {
        console.error('Error updating incident status:', error);
        console.error('Error details:', error.response);
        console.error('Error message:', error.message);
        
        // Check if this is an access denied error first
        if (!AccessUtils.handleApiError(error, 'reject incidents')) {
          // Only show generic error if it's not an access denied error
          PopupService.error('Failed to reject incident. Please try again.');
        }
      });
    },
    confirmClose(incident) {
      console.log('Closing incident:', incident.IncidentId);
      // Update incident status to "Closed"
      axiosInstance.put(API_ENDPOINTS.INCIDENT_STATUS(incident.IncidentId), {
        status: 'Closed'
      })
      .then(response => {
        console.log('Incident closed - API response:', response.data);
        
        // Check if the response indicates success
        if (response.data.success) {
          // Show success message
          PopupService.success(`Incident #${incident.IncidentId} closed successfully!`, 'Incident Closed');
          
          // Immediately update the local incident object for instant UI feedback
          if (this.incidents && Array.isArray(this.incidents)) {
            const localIncident = this.incidents.find(inc => inc.IncidentId === incident.IncidentId);
            if (localIncident) {
              localIncident.Status = 'Closed';
              console.log('Updated local incident status to Closed');
            }
          }
          
          // Update filtered incidents as well
          if (this.filteredIncidents && Array.isArray(this.filteredIncidents)) {
            const filteredIncident = this.filteredIncidents.find(inc => inc.IncidentId === incident.IncidentId);
            if (filteredIncident) {
              filteredIncident.Status = 'Closed';
            }
          }
          
          // Close the modal immediately
          this.closeModal();
          
          // Refresh incidents list after status update for data consistency
          this.fetchIncidents();
        } else {
          // Handle unsuccessful response
          console.error('API returned unsuccessful response:', response.data);
          PopupService.error(response.data.message || 'Failed to close incident. Please try again.');
        }
      })
      .catch(error => {
        console.error('Error updating incident status:', error);
        console.error('Error details:', error.response);
        console.error('Error message:', error.message);
        
        if (!AccessUtils.handleApiError(error, 'close incidents')) {
          PopupService.error('Failed to close incident. Please try again.');
        }
      });
    },
    confirmAssign() {
      // Validate reviewer selection
      if (!this.selectedReviewer) {
        PopupService.warning('Please select a reviewer');
        return;
      }

      // Auto-set current user as assigner
      const currentUserId = this.currentUser?.user_id;
      if (!currentUserId) {
        PopupService.error('Unable to identify current user. Please refresh and try again.');
        return;
      }

      // Check if current user is trying to assign to themselves as reviewer
      if (currentUserId === this.selectedReviewer.toString()) {
        PopupService.warning('You cannot assign yourself as both assigner and reviewer');
        return;
      }

      // Find reviewer details - assigner is automatically the current user
      const reviewer = this.availableUsers.find(user => user.id === this.selectedReviewer);

      // Update incident with assignment details
      axiosInstance.put(API_ENDPOINTS.INCIDENT_ASSIGN(this.selectedIncident.IncidentId), {
        status: 'Assigned',
        assigner_id: currentUserId,
        assigner_name: this.currentUserName,
        reviewer_id: this.selectedReviewer,
        reviewer_name: reviewer.name,
        assignment_notes: this.assignmentNotes,
        assigned_date: new Date().toISOString()
      })
      .then(response => {
        console.log('Incident assigned successfully:', response.data);
        // Refresh incidents list after assignment
        this.fetchIncidents();
        
        // Show success message and close modal
        setTimeout(() => {
          this.closeModal();
        }, 1500);
      })
      .catch(error => {
        console.error('Error assigning incident:', error);
        
        // Check if this is an access denied error first
        if (!AccessUtils.handleApiError(error, 'assign incidents')) {
          // Only show generic error if it's not an access denied error
          PopupService.error('Failed to assign incident. Please try again.');
        }
      });
    },
    getRiskCategoryClass(category) {
      if (!category) return '';
      const categoryLower = category.toLowerCase();
      if (categoryLower.includes('security')) return 'category-security';
      if (categoryLower.includes('compliance')) return 'category-compliance';
      if (categoryLower.includes('operational')) return 'category-operational';
      if (categoryLower.includes('financial')) return 'category-financial';
      if (categoryLower.includes('strategic')) return 'category-strategic';
      return 'category-other';
    },
    getIncidentCategoryClass(category) {
      if (!category) return '';
      const categoryLower = category.toLowerCase();
      if (categoryLower.includes('security')) return 'incident-category-security';
      if (categoryLower.includes('compliance')) return 'incident-category-compliance';
      if (categoryLower.includes('operational')) return 'incident-category-operational';
      if (categoryLower.includes('financial')) return 'incident-category-financial';
      if (categoryLower.includes('strategic')) return 'incident-category-strategic';
      if (categoryLower.includes('data breach')) return 'incident-category-data-breach';
      if (categoryLower.includes('system failure')) return 'incident-category-system-failure';
      if (categoryLower.includes('human error')) return 'incident-category-human-error';
      if (categoryLower.includes('malware')) return 'incident-category-malware';
      if (categoryLower.includes('phishing')) return 'incident-category-phishing';
      return 'incident-category-other';
    },
    getIncidentStatusClass(status) {
      if (!status) return 'status-open';
      const statusLower = status.toLowerCase();
      if (statusLower === 'new') return 'status-new';
      if (statusLower === 'open' || statusLower === '') return 'status-open';
      if (statusLower === 'assigned') return 'status-assigned';
      if (statusLower === 'approved') return 'status-approved';
      if (statusLower === 'active') return 'status-active';
      if (statusLower === 'under review' || statusLower === 'pending review') return 'status-pending';
      if (statusLower === 'completed') return 'status-completed';
      if (statusLower === 'closed') return 'status-closed';
      if (statusLower === 'scheduled') return 'status-scheduled';
      if (statusLower === 'rejected') return 'status-rejected';
      return 'status-default';
    },
    getStatusDisplayText(status) {
      if (!status || status.trim() === '') return 'Open';
      const statusLower = status.toLowerCase();
      if (statusLower === 'under review' || statusLower === 'pending review') return 'Pending Review';
      return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();
    },
    getStatusClass(priority) {
      const priorityLower = priority?.toLowerCase() || '';
      if (priorityLower === 'high') return 'status-active';
      if (priorityLower === 'medium') return 'status-medium';
      if (priorityLower === 'low') return 'status-inactive';
      return 'status-default';
    },
    getOriginClass(origin) {
      const originType = origin?.toLowerCase() || '';
      if (originType.includes('manual')) return 'incident-origin-manual';
      if (originType.includes('audit')) return 'incident-origin-audit';
      if (originType.includes('siem')) return 'incident-origin-siem';
      return 'incident-origin-other';
    },
    
    // Load data from stored service (from login)
    async loadFromStoredData() {
      console.log('📦 Loading all data from incidentService...');
      this.isLoadingIncidents = true;
      
      try {
        // Load incidents FIRST (most important)
        const storedIncidents = incidentService.getData('incidents');
        console.log('🔍 [loadFromStoredData] Checking stored incidents:', {
          exists: !!storedIncidents,
          isArray: Array.isArray(storedIncidents),
          length: storedIncidents ? storedIncidents.length : 0,
          sampleId: storedIncidents && storedIncidents.length > 0 ? storedIncidents[0]?.IncidentId : null
        });
        
        if (storedIncidents && Array.isArray(storedIncidents) && storedIncidents.length > 0) {
          console.log(`✅ [loadFromStoredData] Loading ${storedIncidents.length} incidents from storage`);
          
          // Load all incidents for client-side pagination
          this.incidents = [...storedIncidents];
          
          console.log(`📊 [loadFromStoredData] Set this.incidents to ${this.incidents.length} items`);
          
          // Force Vue to recognize the change
          this.$forceUpdate();
          
          // Stop loading immediately after incidents are loaded
          this.isLoadingIncidents = false;
          console.log(`✅ [loadFromStoredData] isLoadingIncidents set to false`);
        } else {
          console.error('❌ [loadFromStoredData] No stored incidents found!');
          console.error('❌ [loadFromStoredData] storedIncidents:', storedIncidents);
          console.error('❌ [loadFromStoredData] Full service data:', incidentService.getAllData());
          console.warn('⚠️ [loadFromStoredData] Falling back to API...');
          await this.fetchIncidents();
        }
        
        // Load supporting data (non-blocking)
        // Load business units
        const storedBusinessUnits = incidentService.getData('incidentBusinessUnits');
        if (storedBusinessUnits && Array.isArray(storedBusinessUnits)) {
          this.businessUnits = storedBusinessUnits;
          console.log(`📦 Loaded ${storedBusinessUnits.length} business units from storage`);
        } else {
          // Fetch in background (don't block)
          this.fetchBusinessUnits().catch(() => {});
        }
        
        // Load categories
        const storedCategories = incidentService.getData('incidentCategories');
        if (storedCategories && Array.isArray(storedCategories)) {
          this.businessCategories = storedCategories;
          console.log(`📦 Loaded ${storedCategories.length} categories from storage`);
        } else {
          // Fetch in background (don't block)
          this.fetchBusinessCategories().catch(() => {});
        }
        
        // Load users
        const storedUsers = incidentService.getData('incidentUsers');
        if (storedUsers && Array.isArray(storedUsers)) {
          this.availableUsers = storedUsers.map(user => ({
            id: user.UserId,
            name: user.UserName,
            role: user.role
          }));
          console.log(`📦 Loaded ${storedUsers.length} users from storage`);
        } else {
          // Fetch in background (don't block)
          this.fetchUsers().catch(() => {});
        }
        
        // Still need to fetch frameworks (not in incidentService) - do this in background
        this.fetchFrameworks().then(() => {
          this.fetchSelectedFramework().catch(() => {});
        }).catch(() => {});
        
        console.log('✅ Critical data loaded from storage! Page should be visible now.');
      } catch (error) {
        console.error('❌ Error loading from stored data:', error);
        // Fallback to API calls
        await this.fetchFrameworks();
        await this.fetchSelectedFramework();
        this.fetchIncidents();
        this.fetchBusinessUnits();
        this.fetchBusinessCategories();
      } finally {
        this.isLoadingIncidents = false;
        this.$nextTick(() => {
          this.handleResize();
        });
      }
    },
    
    async fetchIncidents() {
      try {
        this.isLoadingIncidents = true;
        
        // ALWAYS check for stored data FIRST - Don't call API if we have stored incidents
        const storedIncidents = incidentService.getData('incidents');
        const hasStoredData = storedIncidents && Array.isArray(storedIncidents) && storedIncidents.length > 0;
        
        console.log('🔍 [fetchIncidents] Checking stored data FIRST:', {
          hasStoredData,
          storedCount: storedIncidents ? storedIncidents.length : 0,
          lastFetchTime: incidentService.getAllData().lastFetchTime
        });
        
        // If we have stored data, ALWAYS use it - filter locally, don't call API!
        if (hasStoredData) {
          console.log('✅ [fetchIncidents] Using stored incidents from session - NO API CALL!');
          
          // Apply filters/search to stored data locally (client-side filtering)
          let filteredIncidents = [...storedIncidents];
          
          // Apply search filter
          if (this.searchQuery && this.searchQuery.trim()) {
            const searchLower = this.searchQuery.toLowerCase().trim();
            filteredIncidents = filteredIncidents.filter(inc => 
              String(inc.IncidentId).includes(searchLower) ||
              (inc.IncidentTitle && inc.IncidentTitle.toLowerCase().includes(searchLower)) ||
              (inc.Origin && inc.Origin.toLowerCase().includes(searchLower)) ||
              (inc.RiskPriority && inc.RiskPriority.toLowerCase().includes(searchLower)) ||
              (inc.IncidentCategory && inc.IncidentCategory.toLowerCase().includes(searchLower)) ||
              (inc.Status && inc.Status.toLowerCase().includes(searchLower)) ||
              (inc.AffectedBusinessUnit && inc.AffectedBusinessUnit.toLowerCase().includes(searchLower))
            );
          }
          
          // Apply framework filter
          if (this.selectedFramework) {
            filteredIncidents = filteredIncidents.filter(inc => 
              inc.framework_id == this.selectedFramework
            );
          }
          
          // Apply status filter
          if (this.selectedStatus) {
            filteredIncidents = filteredIncidents.filter(inc => 
              inc.Status === this.selectedStatus
            );
          }
          
          // Apply business unit filter
          if (this.selectedBusinessUnit) {
            filteredIncidents = filteredIncidents.filter(inc => 
              inc.AffectedBusinessUnit === this.selectedBusinessUnit
            );
          }
          
          // Apply category filter
          if (this.selectedBusinessCategory) {
            filteredIncidents = filteredIncidents.filter(inc => 
              inc.IncidentCategory === this.selectedBusinessCategory
            );
          }
          
          // Apply sorting
          if (this.sortField) {
            filteredIncidents.sort((a, b) => {
              const aVal = a[this.sortField] || '';
              const bVal = b[this.sortField] || '';
              
              if (this.sortOrder === 'asc') {
                return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
              } else {
                return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
              }
            });
          }
          
          // Set all filtered incidents - DynamicTable will handle pagination
          this.incidents = filteredIncidents;
          
          console.log(`✅ [fetchIncidents] Loaded ${this.incidents.length} incidents from stored data`);
          console.log(`📊 [fetchIncidents] Filtered from ${storedIncidents.length} total → ${filteredIncidents.length} after filters`);
          
          this.isLoadingIncidents = false;
          
          // Force re-render
          this.$nextTick(() => {
            this.handleResize();
          });
          
          return; // EXIT - Don't call API!
        }
        
        // Only call API if NO stored data exists (shouldn't happen after login!)
        console.warn('⚠️ [fetchIncidents] No stored data found - calling API (this should not happen after login!)');
        
        // Debug authentication
        const token = localStorage.getItem('access_token');
        const userId = localStorage.getItem('user_id');
        console.log('🔐 Authentication debug:', {
          hasToken: !!token,
          tokenLength: token ? token.length : 0,
          userId: userId,
          isAuthenticated: localStorage.getItem('isAuthenticated')
        });
        
        // Build query parameters for backend search and sort
        const params = {};
        
        if (this.searchQuery.trim()) {
          params.search = this.searchQuery.trim();
          console.log('Adding search parameter:', params.search);
        }
        
        if (this.sortField) {
          params.sort_field = this.sortField;
          params.sort_order = this.sortOrder;
          console.log('Adding sort parameters:', params.sort_field, params.sort_order);
        }

        // Add filter parameters
        if (this.selectedFramework) {
          params.framework_id = this.selectedFramework;
          console.log('Adding framework filter:', this.selectedFramework);
        }
        if (this.selectedPolicy) {
          params.policy_id = this.selectedPolicy;
          console.log('Adding policy filter:', this.selectedPolicy);
        }
        if (this.selectedSubPolicy) {
          params.subpolicy_id = this.selectedSubPolicy;
          console.log('Adding subpolicy filter:', this.selectedSubPolicy);
        }
        if (this.selectedPriority) {
          params.priority = this.selectedPriority;
          console.log('Adding priority filter:', this.selectedPriority);
        }
        if (this.selectedBusinessUnit) {
          params.business_unit = this.selectedBusinessUnit;
          console.log('Adding business unit filter:', this.selectedBusinessUnit);
        }
        if (this.selectedBusinessCategory) {
          params.business_category = this.selectedBusinessCategory;
          console.log('Adding business category filter:', this.selectedBusinessCategory);
        }
        if (this.selectedStatus) {
          params.status = this.selectedStatus;
          console.log('Adding status filter:', this.selectedStatus);
        }
        
        console.log('🔄 Fetching incidents from API (filters/search applied)');
        console.log('API URL:', API_ENDPOINTS.INCIDENT_INCIDENTS);
        
        const response = await axiosInstance.get(API_ENDPOINTS.INCIDENT_INCIDENTS, { 
          params,
          timeout: 60000  // Increase timeout to 60 seconds for incidents
        });
        
        console.log('Response received:', response);
        console.log('Response data:', response.data);
        console.log('Response data type:', typeof response.data);
        console.log('Response data is array:', Array.isArray(response.data));
        
        // Handle response - load all incidents for client-side pagination
        let incidentsData = Array.isArray(response.data) ? response.data : (response.data.incidents || []);
        console.log('📦 [Incident.vue] Setting incidents from API response:', incidentsData.length);
        
        this.incidents = Array.isArray(incidentsData) ? [...incidentsData] : [];
        console.log('✅ [Incident.vue] Incidents set:', this.incidents.length);
        
        // IMPORTANT: Set loading to false AFTER setting incidents
        this.isLoadingIncidents = false;
        console.log('🔄 [Incident.vue] isLoadingIncidents set to false');
        console.log('📊 [Incident.vue] Current state:', {
          incidentsLength: this.incidents.length,
          isLoadingIncidents: this.isLoadingIncidents,
          totalIncidents: this.totalIncidents
        });
        
        // Store the fetched incidents in the service for future use (if we got data from API fallback)
        // This should rarely happen since we check stored data first
        if (incidentsData && incidentsData.length > 0) {
          try {
            // Store ALL incidents, not just the current page
            const allStored = incidentService.getData('incidents') || [];
            if (allStored.length === 0) {
              // Only store if service is empty (to avoid overwriting full dataset)
              incidentService.setData('incidents', incidentsData);
              console.log('💾 [Incident.vue] Stored incidents in service for future use:', incidentsData.length);
            }
          } catch (error) {
            console.warn('⚠️ [Incident.vue] Could not store incidents in service:', error);
          }
        }
        
        console.log('✅ [Incident.vue] Fetched incidents:', this.incidents.length);
        console.log('📋 [Incident.vue] Final incidents array:', this.incidents);
        console.log('🔍 [Incident.vue] Sample incidents:', this.incidents.slice(0, 3).map(inc => ({ 
          id: inc.IncidentId, 
          title: inc.IncidentTitle, 
          status: inc.Status 
        })));
        
        // Debug: Show all unique status values
        const uniqueStatuses = [...new Set(this.incidents.map(inc => inc.Status).filter(status => status))];
        console.log('📊 [Incident.vue] All unique status values found:', uniqueStatuses);
        
        // Force re-render after data is loaded to ensure proper layout
        this.$nextTick(() => {
          console.log('🔄 [Incident.vue] $nextTick - Re-checking incidents:', this.incidents.length);
          this.handleResize();
          // Double-check after nextTick
          if (this.incidents.length === 0) {
            console.error('❌ [Incident.vue] WARNING: Incidents array is empty after $nextTick!');
          } else {
            console.log('✅ [Incident.vue] Incidents confirmed after $nextTick:', this.incidents.length);
          }
        });
      } catch (error) {
        console.error('Failed to fetch incidents:', error);
        console.error('Error details:', error.response);
        console.error('Error message:', error.message);
        console.error('Error code:', error.code);
        console.error('Error config:', error.config);
        
        // Check if this is an access denied error first
        if (!AccessUtils.handleApiError(error, 'view incidents')) {
          // Only show generic error if it's not an access denied error
          let errorMessage = 'Failed to load incidents. ';
          
          if (error.code === 'ECONNABORTED') {
            errorMessage += 'Request timed out. The database may be slow or contain many records. Please try applying filters to narrow down the results, or contact your administrator if the issue persists.';
          } else if (error.code === 'ERR_NETWORK') {
            errorMessage += 'Network error. Please check your connection.';
          } else if (error.response && error.response.status === 500) {
            errorMessage += 'Server error. The backend may be experiencing issues. Please try again later or contact your administrator.';
          } else if (error.response && error.response.status) {
            errorMessage += `Server error (${error.response.status}). Please try again.`;
          } else {
            errorMessage += 'Please try again.';
          }
          
          PopupService.error(errorMessage);
        }
      } finally {
        this.isLoadingIncidents = false;
      }
    },
    async fetchUsers() {
      try {
        // Try to get from stored data first
        const storedUsers = incidentService.getData('incidentUsers');
        if (storedUsers && Array.isArray(storedUsers) && storedUsers.length > 0) {
          console.log('📦 Using stored users data from incidentService:', storedUsers.length, 'users');
          this.availableUsers = storedUsers.map(user => ({
            id: user.UserId || user.id,
            name: user.UserName || user.name,
            role: user.role || user.Role || ''
          }));
          console.log('✅ Mapped availableUsers:', this.availableUsers.length);
          return;
        }
        
        // Fallback to API call
        console.log('🔄 Fetching users from API (cache empty or invalid)');
        const response = await axiosInstance.get(API_ENDPOINTS.INCIDENTS_USERS, {
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        console.log('✅ Users API response:', response.data);
        console.log('✅ Response status:', response.status);
        
        // Handle multiple response formats
        let users = [];
        if (response.data && response.data.success && response.data.users) {
          users = response.data.users;
          console.log('✅ Parsed users from success.users format:', users.length);
        } else if (Array.isArray(response.data)) {
          users = response.data;
          console.log('✅ Parsed users from direct array format:', users.length);
        } else if (response.data && Array.isArray(response.data.data)) {
          users = response.data.data;
          console.log('✅ Parsed users from data.data format:', users.length);
        } else {
          console.warn('⚠️ Unexpected response format:', response.data);
        }
        
        // Map the API response to match the expected frontend structure
        this.availableUsers = users.map(user => ({
          id: user.UserId || user.id || user.userId,
          name: user.UserName || user.name || user.username || 'Unknown',
          role: user.role || user.Role || ''
        })).filter(user => user.id); // Filter out invalid users
        
        console.log('✅ Mapped availableUsers:', this.availableUsers.length, 'users');
        console.log('🔍 Sample users:', this.availableUsers.slice(0, 3));
        
        // Update cache for future use
        if (this.availableUsers.length > 0) {
          incidentService.setData('incidentUsers', users);
        }
      } catch (error) {
        console.error('❌ Failed to fetch users:', error);
        console.error('❌ Error details:', error.response?.data);
        console.error('❌ Error status:', error.response?.status);
        
        // Try fallback endpoint
        try {
          console.log('🔄 Trying fallback endpoint: /api/users/');
          const fallbackResponse = await axiosInstance.get('/api/users/', {
            withCredentials: true
          });
          
          let users = [];
          if (fallbackResponse.data && fallbackResponse.data.success && fallbackResponse.data.users) {
            users = fallbackResponse.data.users;
          } else if (Array.isArray(fallbackResponse.data)) {
            users = fallbackResponse.data;
          }
          
          this.availableUsers = users.map(user => ({
            id: user.UserId || user.id,
            name: user.UserName || user.name,
            role: user.role || user.Role || ''
          })).filter(user => user.id);
          
          console.log('✅ Fallback endpoint succeeded:', this.availableUsers.length, 'users');
          
          // Update cache
          if (this.availableUsers.length > 0) {
            incidentService.setData('incidentUsers', users);
          }
        } catch (fallbackError) {
          console.error('❌ Fallback endpoint also failed:', fallbackError);
          
          // Check if this is an access denied error first
          if (!AccessUtils.handleApiError(error, 'view users')) {
            // Only show generic error if it's not an access denied error
            PopupService.error('Failed to load reviewers. Please refresh the page and try again.');
          }
          
          // Keep empty array if fetch fails
          this.availableUsers = [];
        }
      }
    },
    async fetchFrameworks() {
      try {
        const response = await axiosInstance.get(API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_FRAMEWORKS);
        if (response.data && Array.isArray(response.data)) {
          this.frameworks = response.data;
        } else {
          this.frameworks = [];
        }
        console.log('Fetched frameworks:', this.frameworks);
      } catch (error) {
        console.error('Error fetching frameworks:', error);
        this.frameworks = [];
      }
    },
    async fetchSelectedFramework() {
      try {
        console.log('🔍 Fetching selected framework for incident list...');
        const frameworkResponse = await axiosInstance.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED);
        console.log('Framework response:', frameworkResponse.data);
        
        if (frameworkResponse.data && frameworkResponse.data.frameworkId) {
          const frameworkId = parseInt(frameworkResponse.data.frameworkId);
          // If frameworkId is empty, null, undefined, or 0, set it to empty string (All Frameworks)
          this.selectedFramework = frameworkId || '';
          console.log('✅ Set selectedFramework for incident list:', this.selectedFramework);
        } else {
          console.log('⚠️ No framework selected or frameworkId not found in response');
          // Try to get from localStorage as fallback
          const storedFrameworkId = localStorage.getItem('selectedFrameworkId') || localStorage.getItem('frameworkId');
          if (storedFrameworkId && storedFrameworkId !== '' && storedFrameworkId !== 'null') {
            this.selectedFramework = parseInt(storedFrameworkId);
            console.log('✅ Using framework ID from localStorage:', this.selectedFramework);
          } else {
            // No framework selected means "All Frameworks" - set to empty string
            this.selectedFramework = '';
            console.log('✅ No specific framework selected - showing all frameworks');
          }
        }
      } catch (frameworkError) {
        console.warn('⚠️ Could not fetch selected framework:', frameworkError);
        // Try to get from localStorage as fallback
        const storedFrameworkId = localStorage.getItem('selectedFrameworkId') || localStorage.getItem('frameworkId');
        if (storedFrameworkId && storedFrameworkId !== '' && storedFrameworkId !== 'null') {
          this.selectedFramework = parseInt(storedFrameworkId);
          console.log('✅ Using framework ID from localStorage as fallback:', this.selectedFramework);
        } else {
          // No framework found anywhere means "All Frameworks" - set to empty string
          this.selectedFramework = '';
          console.log('✅ No framework ID found - showing all frameworks');
        }
      }
    },
    async fetchBusinessUnits() {
      try {
        // Try to get from stored data first
        const storedBusinessUnits = incidentService.getData('incidentBusinessUnits');
        if (storedBusinessUnits && Array.isArray(storedBusinessUnits)) {
          console.log('📦 Using stored business units data from incidentService');
          this.businessUnits = storedBusinessUnits;
          return;
        }
        
        // Fallback to API call
        console.log('🔄 Fetching business units from API');
        const response = await axiosInstance.get(API_ENDPOINTS.BUSINESS_UNITS);
        if (response.data && Array.isArray(response.data)) {
          this.businessUnits = response.data;
        } else {
          this.businessUnits = [];
        }
        console.log('Fetched business units:', this.businessUnits);
      } catch (error) {
        console.error('Error fetching business units:', error);
        this.businessUnits = [];
      }
    },
    async fetchBusinessCategories() {
      try {
        // Try to get from stored data first
        const storedCategories = incidentService.getData('incidentCategories');
        if (storedCategories && Array.isArray(storedCategories)) {
          console.log('📦 Using stored categories data from incidentService');
          this.businessCategories = storedCategories;
          return;
        }
        
        // Fallback to API call
        console.log('🔄 Fetching categories from API');
        const response = await axiosInstance.get(API_ENDPOINTS.CATEGORIES);
        if (response.data && Array.isArray(response.data)) {
          this.businessCategories = response.data;
        } else {
          this.businessCategories = [];
        }
        console.log('Fetched business categories:', this.businessCategories);
      } catch (error) {
        console.error('Error fetching business categories:', error);
        this.businessCategories = [];
      }
    },
    async fetchPolicies() {
      try {
        if (!this.selectedFramework) {
          this.policies = [];
          return;
        }
        
        const response = await axiosInstance.get(API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_POLICIES, {
          params: { 
            framework_id: this.selectedFramework
          }
        });
        
        if (response.data && Array.isArray(response.data)) {
          this.policies = response.data;
        } else {
          this.policies = [];
        }
        console.log('Fetched policies for framework:', this.selectedFramework, this.policies);
      } catch (error) {
        console.error('Error fetching policies:', error);
        this.policies = [];
      }
    },
    async fetchSubPolicies() {
      try {
        if (!this.selectedPolicy) {
          this.subpolicies = [];
          return;
        }
        
        const response = await axiosInstance.get(API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_SUBPOLICIES, {
          params: { 
            policy_id: this.selectedPolicy
          }
        });
        
        if (response.data && Array.isArray(response.data)) {
          this.subpolicies = response.data;
        } else {
          this.subpolicies = [];
        }
        console.log('Fetched subpolicies for policy:', this.selectedPolicy, this.subpolicies);
      } catch (error) {
        console.error('Error fetching subpolicies:', error);
        this.subpolicies = [];
      }
    },
    filterIncidents() {
      console.log('filterIncidents called with searchQuery:', this.searchQuery);
      
      // Clear existing timeout
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout);
      }
      
      // Set new timeout for debounced search
      this.searchTimeout = setTimeout(() => {
        console.log('Debounce timeout reached, calling performSearch');
        this.performSearch();
      }, 500); // Increased to 500ms for better performance
    },
    
    performSearch() {
      console.log('performSearch called');
      // Reset to first page when searching
      this.currentPage = 1;
      // Perform backend search by refetching data
      this.fetchIncidents();
    },
    
    clearSearch() {
      console.log('Clear search clicked');
      this.searchQuery = '';
      // Clear any pending search timeout
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = null;
      }
      this.fetchIncidents();
    },
    setSortField(field) {
      // Toggle sort order if clicking the same field
      if (this.sortField === field) {
        this.toggleSortOrder();
      } else {
        this.sortField = field;
        // Default to ascending order when changing fields
        this.sortOrder = 'asc';
      }
      // Reset to first page when sorting
      this.currentPage = 1;
      // Refetch data with new sorting from backend
      this.fetchIncidents();
    },
    sortIncidents() {
      // Refetch data with sorting from backend
      this.fetchIncidents();
    },
    toggleSortOrder() {
      this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
      // Refetch data with new sort order from backend
      this.fetchIncidents();
    },
    handleResize() {
      // Update layout when window is resized
      const wrapper = document.querySelector('.incident-list-wrapper');
      if (wrapper) {
        wrapper.style.maxWidth = '100%';
      }
    },
    getPriorityClass(priority) {
      switch(priority?.toLowerCase()) {
        case 'high':
          return 'incident-priority-high';
        case 'medium':
          return 'incident-priority-medium';
        case 'low':
          return 'incident-priority-low';
        default:
          return '';
      }
    },
    formatDate(dateString) {
      if (!dateString) return '';
      
      const [year, month, day] = dateString.split('-');
      return `${month}/${day}/${year}`;
    },
    closeIncidentDetails() {
      this.selectedIncident = null;
      this.showIncidentDetails = false;
    },
    exportIncidents() {
      console.log('Exporting incidents...');
      this.isExporting = true;
      
      // Export current incidents (note: this will only export current page)
      // To export all incidents, we might need to make a separate API call
      const dataToExport = this.incidents;
      
      // Only send necessary fields to reduce payload size
      const trimmedData = dataToExport.map(incident => ({
        IncidentId: incident.IncidentId,
        IncidentTitle: incident.IncidentTitle,
        Date: incident.Date,
        RiskPriority: incident.RiskPriority,
        Origin: incident.Origin,
        Status: incident.Status
      }));
      
      axiosInstance.post(API_ENDPOINTS.INCIDENTS_EXPORT, {
        file_format: this.exportFormat,
        data: JSON.stringify(trimmedData),
        options: JSON.stringify({
          filters: {
            searchQuery: this.searchQuery,
            sortField: this.sortField,
            sortOrder: this.sortOrder
          }
        })
      })
      .then(response => {
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
              link.setAttribute('download', response.data.file_name || `incidents.${this.exportFormat}`);
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
              PopupService.success('Export completed successfully! File downloaded.');
            }
          } catch (downloadErr) {
            // Fallback to download if window.open fails
            const link = document.createElement('a');
            link.href = response.data.file_url;
            link.setAttribute('download', response.data.file_name || `incidents.${this.exportFormat}`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            PopupService.success('Export completed successfully! File downloaded.');
            console.error(downloadErr);
          }
        }
        
        this.isExporting = false;
      })
      .catch(error => {
        console.error('Export failed:', error);
        
        // Check if this is an access denied error first
        if (!AccessUtils.handleApiError(error, 'export incidents')) {
          // Only show generic error if it's not an access denied error
          PopupService.error('Export failed. Please try again.');
        }
        
        this.isExporting = false;
      });
    },
    loadCurrentUser() {
      console.log('Loading current user for incident assignment...');
      try {
        // Get current user from session
        this.currentUser = SessionUtils.getUserSession();
        console.log('Current user session data:', this.currentUser);
        
        if (this.currentUser && this.currentUser.name) {
          this.currentUserName = this.currentUser.name;
          console.log('Set current user name to:', this.currentUserName);
        } else {
          console.warn('No current user name found in session, using fallback');
          this.currentUserName = 'Current User';
        }
      } catch (error) {
        console.error('Error loading current user:', error);
        this.currentUserName = 'Current User';
      }
    },
    async onFrameworkChange() {
      console.log('Framework changed to:', this.selectedFramework);
      this.selectedPolicy = '';
      this.selectedSubPolicy = '';
      this.policies = [];
      this.subpolicies = [];
      this.currentPage = 1; // Reset to first page
      
      if (this.selectedFramework) {
        await this.fetchPolicies();
      }
      this.fetchIncidents();
    },
    async onPolicyChange() {
      console.log('Policy changed to:', this.selectedPolicy);
      this.selectedSubPolicy = '';
      this.subpolicies = [];
      this.currentPage = 1; // Reset to first page
      
      if (this.selectedPolicy) {
        await this.fetchSubPolicies();
      }
      this.fetchIncidents();
    },
    onSubPolicyChange() {
      console.log('SubPolicy changed to:', this.selectedSubPolicy);
      this.currentPage = 1; // Reset to first page
      this.fetchIncidents();
    },
    onPriorityChange() {
      console.log('Priority changed to:', this.selectedPriority);
      this.currentPage = 1; // Reset to first page
      this.fetchIncidents();
    },
    onBusinessUnitChange() {
      console.log('Business Unit changed to:', this.selectedBusinessUnit);
      this.currentPage = 1; // Reset to first page
      this.fetchIncidents();
    },
    onBusinessCategoryChange() {
      console.log('Business Category changed to:', this.selectedBusinessCategory);
      this.currentPage = 1; // Reset to first page
      this.fetchIncidents();
    },
    clearAllFilters() {
      console.log('Clearing all filters');
      this.selectedFramework = '';
      this.selectedPolicy = '';
      this.selectedSubPolicy = '';
      this.selectedPriority = '';
      this.selectedBusinessUnit = '';
      this.selectedBusinessCategory = '';
      this.searchQuery = '';
      this.policies = [];
      this.subpolicies = [];
      this.currentPage = 1; // Reset to first page
      
      // Clear any pending search timeout
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = null;
      }
      
      this.fetchIncidents();
    },
  }
}
</script>

<style>
/* Add these styles to your existing CSS file or inline here */
.sort-indicator {
  margin-left: 5px;
  display: inline-block;
}

.checklist-header-row div {
  cursor: pointer;
  user-select: none;
  position: relative;
}

.checklist-header-row div:not(.incident-actions-header):hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.checklist-header-row div.sorted {
  font-weight: bold;
  color: #3366cc;
}

.active-sort {
  background-color: #e0e7ff;
  color: #3366cc;
}

/* Header layout with export controls */
.incident-view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.export-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.export-format-select {
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background-color: white;
  font-size: 14px;
}

.export-btn {
  padding: 8px 15px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.export-btn:hover {
  background-color: #45a049;
}

.export-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

/* Current user display styles */
.incident-current-user-display {
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

.incident-filter-controls {
  display: flex;
  gap: 10px;
  margin: 10px 0 20px 0;
}

.incident-clear-filters {
  margin: 10px 0;
}


/* Risk Category styling */
.category-security {
  background-color: #ffebee;
  color: #c62828;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.category-compliance {
  background-color: #e3f2fd;
  color: #1565c0;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.category-operational {
  background-color: #fff3e0;
  color: #ef6c00;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.category-financial {
  background-color: #e8f5e8;
  color: #2e7d32;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.category-strategic {
  background-color: #f3e5f5;
  color: #7b1fa2;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.category-other {
  background-color: #f5f5f5;
  color: #616161;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

/* Incident Category styling */
/* Incident category - plain text, no badges */
.incident-category-security,
.incident-category-compliance,
.incident-category-operational,
.incident-category-financial,
.incident-category-strategic,
.incident-category-data-breach,
.incident-category-system-failure,
.incident-category-human-error,
.incident-category-malware,
.incident-category-phishing,
.incident-category-other {
  color: inherit;
  font-size: 14px;
  font-weight: normal;
}

/* Status styling - plain text with colored dots */
.status-open,
.status-assigned,
.status-approved,
.status-active,
.status-pending,
.status-completed,
.status-closed,
.status-scheduled,
.status-rejected,
.status-default {
  color: inherit !important;
  background-color: transparent !important;
  padding: 0 !important;
  border: none !important;
  border-radius: 0 !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 8px !important;
  width: 100% !important;
  text-align: left !important;
}

/* Colored dots for each status */
.status-open::before {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #ffc107;
  display: inline-block;
}

.status-assigned::before {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #2196f3;
  display: inline-block;
}

.status-scheduled::before {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #9c27b0;
  display: inline-block;
}

/* For "new" status - green dot */
.status-active::before,
.status-approved::before,
.status-default::before,
.status-new::before {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #4caf50;
  display: inline-block;
}

/* Text colors to match the dots */
.status-new,
.incident-status-cell .status-new {
  color: #4caf50 !important; /* Green */
  background-color: transparent !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
}

.status-open,
.incident-status-cell .status-open {
  color: #ffc107 !important; /* Yellow */
}

.status-assigned,
.incident-status-cell .status-assigned {
  color: #2196f3 !important; /* Blue */
}

.status-scheduled,
.incident-status-cell .status-scheduled {
  color: #9c27b0 !important; /* Violet */
}

/* Additional status dots for other statuses */
.status-pending::before,
.status-completed::before {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #9e9e9e;
  display: inline-block;
}

.status-rejected::before,
.status-closed::before {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #f44336;
  display: inline-block;
}
</style>
