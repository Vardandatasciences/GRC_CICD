<template>
  <div class="risk-instance-container">
    <!-- Add PopupModal component -->
    <PopupModal />
    <!-- Combined Header Row with Title and Export Controls -->
    <div class="risk-instance-header-row">
      <h2 class="risk-instance-title">Risk Instances</h2>
      <p
        v-if="dataSourceMessage"
        class="risk-instance-data-source"
      >
        {{ dataSourceMessage }}
      </p>
      <div class="risk-instance-export-controls">
        <select v-model="selectedExportFormat" class="risk-instance-export-dropdown">
          <option value="" disabled>Select format</option>
          <option value="xlsx">Excel (.xlsx)</option>
          <option value="pdf">PDF (.pdf)</option>
          <option value="csv">CSV (.csv)</option>
          <option value="json">JSON (.json)</option>
          <option value="xml">XML (.xml)</option>
          <option value="txt">Text (.txt)</option>
        </select>
        <button @click="exportRiskInstances" :disabled="!selectedExportFormat" class="risk-instance-export-button">
          <i class="fas fa-download"></i>
          Export
        </button>
      </div>
    </div>
    
    <!-- Filters Section - Search bar on top, dropdowns below -->
    <div class="risk-instance-filters-section">
      <!-- Search bar row -->
      <!-- <div class="risk-instance-search-row">
        <Dynamicalsearch 
          v-model="searchQuery" 
          placeholder="Search risk instances..."
          @input="applyFilters"
        />
      </div> -->
    </div>

    <!-- Dynamic Table -->
    <DynamicTable
      :title="''"
      :data="filteredInstances"
      :columns="tableColumns"
      :filters="[]"
      :show-checkbox="false"
      :show-actions="false"
      :show-pagination="true"
      :default-page-size="10"
      unique-key="RiskInstanceId"
      :get-row-class="getRowClass"
      @row-select="handleRowSelect"
      @open-column-chooser="toggleColumnEditor"
      @reset-columns="resetColumnSelection"
    >
      <!-- Custom cell slots for badges and styling -->
      <template #cell-Origin>
        <span class="risk-instance-origin-badge">MANUAL</span>
      </template>
      
      <template #cell-RiskDescription="{ row }">
        <a 
          @click="viewInstanceDetails(row.RiskInstanceId)" 
          class="risk-description-link"
          href="javascript:void(0)"
        >
          {{ row.RiskDescription || 'No description available' }}
        </a>
      </template>
      
      <template #cell-Criticality="{ row }">
        <span :class="'risk-instance-criticality-' + (row.Criticality || 'unknown').toLowerCase()">
          {{ row.Criticality || 'N/A' }}
        </span>
      </template>
      
      <template #cell-RiskStatus="{ row }">
        <span>{{ row.RiskStatus || 'Open' }}</span>
      </template>
      

    </DynamicTable>

    <!-- Column Editor Modal -->
    <div v-if="showColumnEditor" class="risk-instance-column-editor-overlay" @click.self="toggleColumnEditor">
      <div class="risk-instance-column-editor">
        <div class="column-editor-header">
          <h3 class="column-editor-title">Choose Columns</h3>
          <button @click="toggleColumnEditor" class="column-editor-close">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="column-editor-search">
          <input
            type="text"
            v-model="columnSearchQuery"
            placeholder="Search columns..."
            class="column-search-input"
          />
        </div>

        <div class="column-editor-body">
          <div v-if="filteredColumnDefinitions.length === 0" class="column-editor-empty">
            No columns found
          </div>
          <label
            v-for="column in filteredColumnDefinitions"
            :key="column.key"
            class="column-editor-item"
          >
            <span class="column-drag-handle">
              <i class="fas fa-grip-vertical"></i>
            </span>
            <input
              type="checkbox"
              :value="column.key"
              v-model="columnSelection"
              :disabled="column.removable === false"
            />
            <span class="column-label-text">{{ column.label }}</span>
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import DynamicTable from '../DynamicTable.vue'
// import Dynamicalsearch from '../Dynamicalsearch.vue'
import { PopupModal } from '@/modules/popup'
import AccessUtils from '@/utils/accessUtils'
import { API_ENDPOINTS } from '../../config/api.js'
import riskDataService from '@/services/riskService'

export default {
  name: 'RiskInstances',
  components: {
    DynamicTable,
    // Dynamicalsearch,
    PopupModal
  },
  data() {
    return {
      instances: [],
      dataSourceMessage: '',
      searchQuery: '',
      showAddForm: false,
      newInstance: {
        RiskId: null,
        RiskTitle: '',                    // Title
        RiskDescription: '',              // Description
        Criticality: '',                  // Criticality
        Category: '',                     // Category
        RiskLikelihood: '',               // Risk Likelihood
        RiskImpact: '',                   // Risk Impact
        RiskExposureRating: '',           // Risk Exposure Rating
        RiskPriority: '',                 // Risk Priority
        RiskResponseType: '',             // Response Type
        RiskStatus: 'Open',               // Risk Status
        BusinessImpact: '',               // Business Impact
        Origin: '',                       // Origin
        ComplianceId: null,               // Compliance ID
        RiskType: '',                     // Risk Type
        RiskMitigation: '',               // Risk Mitigation
        PossibleDamage: '',               // Possible Damage
        RiskResponseDescription: '',
        RiskOwner: '',
        Appetite: '',
        UserId: 1,
        IncidentId: null,
        ReportedBy: null,
        MitigationDueDate: null,
        ModifiedMitigations: null,
        MitigationStatus: '',
        MitigationCompletedDate: null,
        ReviewerCount: null,
        RiskFormDetails: null,
        RecurrenceCount: 1,
        Reviewer: '',
        ReviewerId: null
      },
      selectedExportFormat: '',
      columnDefinitions: [
        {
          key: 'RiskInstanceId',
          label: 'riskInstanceId',
          sortable: true,
          headerClass: 'risk-instance-id',
          cellClass: 'risk-instance-id',
          defaultVisible: true,
          width: '150px'
        },
        {
          key: 'RiskTitle',
          label: 'riskTitle',
          sortable: true,
          defaultVisible: false
        },
        {
          key: 'RiskDescription',
          label: 'riskDescription',
          sortable: true,
          cellClass: 'risk-instance-description-cell',
          slot: true,
          defaultVisible: true
        },
        {
          key: 'PossibleDamage',
          label: 'possibleDamage',
          sortable: true,
          defaultVisible: false
        },
        {
          key: 'RiskPriority',
          label: 'riskPriority',
          sortable: true,
          defaultVisible: false
        },
        {
          key: 'Criticality',
          label: 'criticality',
          sortable: true,
          cellClass: 'risk-instance-criticality-cell',
          slot: true,
          defaultVisible: true
        },
        {
          key: 'Category',
          label: 'category',
          sortable: true,
          cellClass: 'risk-instance-category-cell',
          defaultVisible: true
        },
        {
          key: 'Origin',
          label: 'origin',
          sortable: true,
          cellClass: 'risk-instance-origin-cell',
          defaultVisible: true
        },
        // {
        //   key: 'RiskMultiplierX',
        //   label: 'riskMultiplierX',
        //   sortable: true,
        //   defaultVisible: false
        // },
        // {
        //   key: 'RiskMultiplierY',
        //   label: 'riskMultiplierY',
        //   sortable: true,
        //   defaultVisible: false
        // },
        {
          key: 'Appetite',
          label: 'appetite',
          sortable: true,
          defaultVisible: false
        },
        {
          key: 'RiskResponseType',
          label: 'riskResponseType',
          sortable: true,
          defaultVisible: false
        },
        {
          key: 'RiskResponseDescription',
          label: 'riskResponseDescription',
          sortable: true,
          defaultVisible: false
        },
        {
          key: 'RiskMitigation',
          label: 'riskMitigation',
          sortable: false,
          defaultVisible: false
        },
        {
          key: 'RiskType',
          label: 'riskType',
          sortable: true,
          defaultVisible: false
        },
        // {
        //   key: 'RiskOwner',
        //   label: 'riskOwner',
        //   sortable: true,
        //   defaultVisible: false
        // },
        {
          key: 'BusinessImpact',
          label: 'businessImpact',
          sortable: true,
          defaultVisible: false
        },
        {
          key: 'MitigationDueDate',
          label: 'mitigationDueDate',
          sortable: true,
          defaultVisible: false
        },
        // {
        //   key: 'ModifiedMitigations',
        //   label: 'modifiedMitigations',
        //   sortable: false,
        //   defaultVisible: false
        // },
        {
          key: 'MitigationStatus',
          label: 'mitigationStatus',
          sortable: true,
          defaultVisible: false
        },
        // {
        //   key: 'Reviewer',
        //   label: 'reviewer',
        //   sortable: true,
        //   defaultVisible: false
        // },
        // {
        //   key: 'ReviewerId',
        //   label: 'reviewerId',
        //   sortable: true,
        //   defaultVisible: false
        // },
        {
          key: 'FirstResponseAt',
          label: 'firstResponseAt',
          sortable: true,
          defaultVisible: false
        },
        {
          key: 'RiskStatus',
          label: 'riskStatus',
          sortable: true,
          cellClass: 'risk-instance-status-cell',
          slot: true,
          defaultVisible: true
        },
        {
          key: 'DepartmentName',
          label: 'department',
          sortable: true,
          cellClass: 'risk-instance-department-cell',
          defaultVisible: true
        }
      ],
      visibleColumnKeys: [],
      showColumnEditor: false,
      columnSearchQuery: ''
    }
  },
  computed: {
    filteredColumnDefinitions() {
      if (!this.columnSearchQuery || this.columnSearchQuery.trim() === '') {
        return this.columnDefinitions;
      }
      const query = this.columnSearchQuery.toLowerCase().trim();
      return this.columnDefinitions.filter(column =>
        column.label.toLowerCase().includes(query)
      );
    },
    columnSelection: {
      get() {
        return this.visibleColumnKeys;
      },
      set(value) {
        const requiredKeys = this.columnDefinitions
          .filter(column => column.removable === false)
          .map(column => column.key);
        const incomingKeys = Array.isArray(value) ? value : [];
        let nextKeys = Array.from(new Set([...incomingKeys, ...requiredKeys]));

        if (nextKeys.length === 0) {
          nextKeys = this.columnDefinitions
            .filter(column => column.defaultVisible !== false)
            .map(column => column.key);
        }

        this.visibleColumnKeys = nextKeys;
      }
    },
    filteredInstances() {
      let filtered = this.instances
      
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        filtered = filtered.filter(instance => 
          (instance.RiskDescription && instance.RiskDescription.toLowerCase().includes(query)) ||
          (instance.RiskInstanceId && instance.RiskInstanceId.toString().includes(query)) ||
          (instance.Category && instance.Category.toLowerCase().includes(query)) ||
          (instance.RiskStatus && instance.RiskStatus.toLowerCase().includes(query)) ||
          (instance.Criticality && instance.Criticality.toLowerCase().includes(query)) ||
          (instance.DepartmentName && instance.DepartmentName.toLowerCase().includes(query))
        )
      }
      
      // Transform data for DynamicTable
      return filtered.map(instance => ({
        ...instance,
        Origin: 'MANUAL', // Add Origin field for the table
        RiskInstanceId: instance.RiskInstanceId || 'N/A',
        Category: instance.Category || 'Operational',
        Criticality: instance.Criticality || 'Low',
        RiskStatus: instance.RiskStatus || 'Open',
        RiskDescription: instance.RiskDescription || 'No description available',
        // Department now handled by backend with random assignment
        DepartmentName: instance.DepartmentName
      }))
    },
    // Table columns configuration for DynamicTable
    tableColumns() {
      return this.columnDefinitions.filter(column =>
        this.visibleColumnKeys.includes(column.key)
      );
    }
  },
  mounted() {
    // Initialize visible column keys from default values
    const defaultVisibleKeys = this.columnDefinitions
      .filter(column => column.defaultVisible !== false)
      .map(column => column.key);
    this.visibleColumnKeys = [...defaultVisibleKeys];
    
    this.fetchInstances()
  },
  methods: {
    applyFilters() {
      // Filter logic is handled in computed properties
    },
    toggleColumnEditor() {
      this.showColumnEditor = !this.showColumnEditor;
      if (!this.showColumnEditor) {
        this.columnSearchQuery = '';
      }
    },
    resetColumnSelection() {
      const defaultVisibleKeys = this.columnDefinitions
        .filter(column => column.defaultVisible !== false)
        .map(column => column.key);
      this.visibleColumnKeys = [...defaultVisibleKeys];
    },
    
    sanitizeQueryParams(params) {
      const processed = {}
      
      for (const [key, value] of Object.entries(params)) {
        if (value === null || value === undefined || value === '') continue
        processed[key] = value
      }
      
      return processed
    },
    
    async fetchInstances() {
      this.loading = true
      this.dataSourceMessage = 'Loading risk instances...'
      try {
        console.log('🔍 [RiskInstances] Checking for cached risk instances...')

        // Wait for global prefetch if it's still running
        if (typeof window !== 'undefined' && window.riskDataFetchPromise) {
          try {
            await window.riskDataFetchPromise
          } catch (prefetchError) {
            console.warn('⚠️ [RiskInstances] Prefetch promise rejected:', prefetchError)
          }
        }

        if (riskDataService.hasRiskInstancesCache()) {
          console.log('✅ [RiskInstances] Using cached risk instances')
          this.instances = riskDataService.getData('riskInstances') || []
          this.dataSourceMessage = ''
        } else {
          console.log('⚠️ [RiskInstances] No cached data found, fetching from API...')
          const response = await axios.get(API_ENDPOINTS.RISK_INSTANCES)
          this.instances = response.data
          this.dataSourceMessage = ''

          // Update cache so subsequent pages benefit
          riskDataService.setData('riskInstances', this.instances)
          console.log('ℹ️ [RiskInstances] Cache updated after direct API fetch')
        }
      } catch (error) {
        console.error('❌ [RiskInstances] Error fetching risk instances:', error)
        this.dataSourceMessage = 'Failed to load risk instances'
          
          // Check if it's an access denied error
          if (AccessUtils.handleApiError(error, 'view risk instances')) {
            this.loading = false
            return // Access denied popup already shown
          }
          
          await this.tryAlternativeEndpoint()
      } finally {
        this.loading = false
      }
    },
    
    async tryAlternativeEndpoint() {
      try {
        console.log('🔁 [RiskInstances] Trying alternative endpoint...')
        const response = await axios.get(API_ENDPOINTS.RISK_INSTANCES)
        this.instances = response.data
        this.dataSourceMessage = `Loaded ${this.instances.length} risk instances directly from API (alternative path)`
        riskDataService.setData('riskInstances', this.instances)
        console.log('✅ [RiskInstances] Alternative fetch succeeded')
      } catch (error) {
          console.error('❌ [RiskInstances] Error with alternative endpoint:', error)
        this.dataSourceMessage = 'Failed to load risk instances (alternative endpoint failed)'
      }
    },
    
    validateResponseData(data) {
      if (!Array.isArray(data)) {
        console.error('Expected array response, got:', typeof data)
        return []
      }
      
      return data
    },
    
    viewInstanceDetails(instanceId) {
      this.$router.push(`/view-instance/${instanceId}`)
    },
    
    handleRowSelect(data) {
      console.log('Row selected:', data)
    },
    
    handleRowClick(row) {
      this.viewInstanceDetails(row.RiskInstanceId);
    },

    getRowClass(row) {
      const baseClass = 'dynamic-table-row';
      if (!row.Criticality) return baseClass;
      
      const criticality = row.Criticality.toLowerCase();
      return `${baseClass} criticality-${criticality}`;
    },
    
    async sendPushNotification(riskData) {
      try {
        const notificationData = {
          title: 'Risk Instance Update',
          message: riskData.message || `Risk instance "${riskData.RiskDescription || 'Untitled Risk'}" has been updated in the Risk module.`,
          category: 'risk',
          priority: 'high',
          user_id: 'default_user' // You can replace this with actual user ID
        };
        const response = await axios.post(API_ENDPOINTS.PUSH_NOTIFICATION, notificationData);
        if (response.status === 200) {
          console.log('Push notification sent successfully');
        } else {
          console.error('Failed to send push notification');
        }
      } catch (error) {
        console.error('Error sending push notification:', error);
      }
    },
    
    
    submitInstance() {
      const formData = {
        RiskId: parseInt(this.newInstance.RiskId) || null,
        RiskTitle: this.newInstance.RiskTitle,
        RiskDescription: this.newInstance.RiskDescription,
        Criticality: this.newInstance.Criticality,
        Category: this.newInstance.Category,
        RiskLikelihood: parseFloat(this.newInstance.RiskLikelihood) || 0,
        RiskImpact: parseFloat(this.newInstance.RiskImpact) || 0,
        RiskExposureRating: this.newInstance.RiskExposureRating ? 
          parseFloat(this.newInstance.RiskExposureRating) : null,
        RiskPriority: this.newInstance.RiskPriority,
        RiskResponseType: this.newInstance.RiskResponseType,
        RiskStatus: this.newInstance.RiskStatus,
        BusinessImpact: this.newInstance.BusinessImpact,
        Origin: this.newInstance.Origin,
        ComplianceId: parseInt(this.newInstance.ComplianceId) || null,
        RiskType: this.newInstance.RiskType,
        RiskMitigation: this.newInstance.RiskMitigation,
        PossibleDamage: this.newInstance.PossibleDamage,
        RiskResponseDescription: this.newInstance.RiskResponseDescription,
        RiskOwner: this.newInstance.RiskOwner,
        Appetite: this.newInstance.Appetite,
        UserId: parseInt(this.newInstance.UserId) || null,
        IncidentId: parseInt(this.newInstance.IncidentId) || null,
        ReportedBy: parseInt(this.newInstance.ReportedBy) || null,
        MitigationDueDate: this.newInstance.MitigationDueDate,
        ModifiedMitigations: this.newInstance.ModifiedMitigations,
        MitigationStatus: this.newInstance.MitigationStatus,
        MitigationCompletedDate: this.newInstance.MitigationCompletedDate,
        ReviewerCount: parseInt(this.newInstance.ReviewerCount) || null,
        RiskFormDetails: this.newInstance.RiskFormDetails,
        RecurrenceCount: parseInt(this.newInstance.RecurrenceCount) || 1,
        Reviewer: this.newInstance.Reviewer,
        ReviewerId: parseInt(this.newInstance.ReviewerId) || null
      }
      
              axios.post(API_ENDPOINTS.CREATE_RISK_INSTANCE, formData)
        .then(response => {
          this.instances.push(response.data)
          
          this.newInstance = {
            RiskId: null,
            RiskTitle: '',                    // Title
            RiskDescription: '',              // Description
            Criticality: '',                  // Criticality
            Category: '',                     // Category
            RiskLikelihood: '',               // Risk Likelihood
            RiskImpact: '',                   // Risk Impact
            RiskExposureRating: '',           // Risk Exposure Rating
            RiskPriority: '',                 // Risk Priority
            RiskResponseType: '',             // Response Type
            RiskStatus: 'Open',               // Risk Status
            BusinessImpact: '',               // Business Impact
            Origin: '',                       // Origin
            ComplianceId: null,               // Compliance ID
            RiskType: '',                     // Risk Type
            RiskMitigation: '',               // Risk Mitigation
            PossibleDamage: '',               // Possible Damage
            RiskResponseDescription: '',
            RiskOwner: '',
            Appetite: '',
            UserId: 1,
            IncidentId: null,
            ReportedBy: null,
            MitigationDueDate: null,
            ModifiedMitigations: null,
            MitigationStatus: '',
            MitigationCompletedDate: null,
            ReviewerCount: null,
            RiskFormDetails: null,
            RecurrenceCount: 1,
            Reviewer: '',
            ReviewerId: null
          }
          
          
          this.showAddForm = false
          this.$popup.success('Risk instance added successfully!')
          
          // Send push notification for successful creation
          this.sendPushNotification({
            RiskDescription: formData.RiskDescription,
            message: `A new risk instance "${formData.RiskDescription || 'Untitled Risk'}" has been created in the Risk module.`
          })
        })
        .catch(error => {
          console.error('Error adding risk instance:', error.response?.data || error.message)
          
          // Check if it's an access denied error
          if (AccessUtils.handleApiError(error, 'create risk instances')) {
            return // Access denied popup already shown
          }
          
          this.$popup.error('Error adding risk instance. Please check your data and try again.')
          
          // Send push notification for failed creation
          this.sendPushNotification({
            RiskDescription: formData.RiskDescription,
            message: `Failed to create risk instance "${formData.RiskDescription || 'Untitled Risk'}". Please check your data and try again.`
          })
        })
    },
    async exportRiskInstances() {
      if (!this.selectedExportFormat) return;
      try {
        const exportData = this.filteredInstances;
        const payload = {
          export_format: this.selectedExportFormat,
          risk_data: exportData,
          user_id: 'default_user',
          file_name: 'risk_instances_export'
        };
        // Increase timeout for long-running exports
        const response = await axios.post(
          API_ENDPOINTS.EXPORT_RISK_REGISTER,
          payload,
          { timeout: 180000 } // 3 minutes
        );
        const result = response.data;
        if (result.success && result.file_url) {
          window.open(result.file_url, '_blank');
          if (this.$popup) {
            this.$popup.success('Export completed successfully!', 'Export Success');
          } else if (window.PopupService) {
            window.PopupService.success('Export completed successfully!', 'Export Success');
          }
        } else {
          if (this.$popup) {
            this.$popup.error('Export failed: ' + (result.error || 'Unknown error'), 'Export Error');
          } else if (window.PopupService) {
            window.PopupService.error('Export failed: ' + (result.error || 'Unknown error'), 'Export Error');
          }
        }
      } catch (error) {
        if (this.$popup) {
          this.$popup.error('Export error: ' + error.message, 'Export Error');
        } else if (window.PopupService) {
          window.PopupService.error('Export error: ' + error.message, 'Export Error');
        }
      }
    }
  }
}
</script>

<style scoped>
/* Modern Card Layout - sidebar-inspired */
.risk-instance-container {
  padding: 55px 16px 16px 285px;
  font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: var(--risk-gray-800, #343a40);
  display: flex;
  margin-top: 0;
  flex-direction: column;
  width: 100%;
  box-sizing: border-box;
  overflow: visible;
  background-color: #ffffff;
}

.risk-instance-cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 15px;
  margin-left: 0;
  padding-left: 0;
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
}

/* Simplified card styling with gradient accent */
.risk-instance-item-card {
  position: relative;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  padding: 16px;
  height: auto;
  min-height: 180px;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  border: 1px solid #f0f0f0;
  margin-left: 0;
  overflow: hidden;
}

.risk-instance-item-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(to right, #6a5acd, #3f3f3f);
}

.risk-instance-item-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(106, 90, 205, 0.15);
}

/* Simplified header */
.risk-instance-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  position: relative;
}

.risk-instance-item-header h3 {
  color: #7B6FDD;
  font-weight: 600;
  font-size: 1.05rem;
  margin: 0;
  position: relative;
  padding-bottom: 5px;
  font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.risk-instance-item-header h3::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 25px;
  height: 2px;
  background: #6a5acd;
  border-radius: 2px;
}

/* Badge styling */
.risk-instance-priority-badge {
  padding: 3px 12px;
  border-radius: 16px;
  font-size: 0.8em;
  font-weight: 600;
  text-align: center;
  background: transparent;
  border: 2px solid;
}

/* Description styling */
.risk-instance-description {
  font-size: 0.9rem;
  line-height: 1.4;
  color: #444;
  margin-bottom: 15px;
  flex-grow: 1;
  font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* Meta items with better spacing and styling */
.risk-instance-meta {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-top: auto;
  padding-top: 10px;
  border-top: 1px solid rgba(106, 90, 205, 0.1);
}

.risk-instance-meta-item {
  display: flex;
  gap: 5px;
  font-size: 0.85rem;
  align-items: center;
  font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.risk-instance-meta-label {
  color: #7B6FDD;
  font-weight: 600;
  min-width: 70px;
}

.risk-instance-meta-value {
  color: #333;
  font-weight: 500;
}

/* Button styling */
.risk-instance-view-details-btn {
  background: #6a5acd;
  color: #fff;
  padding: 5px 15px;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s;
  margin-top: 12px;
  display: inline-block;
  text-align: center;
  font-size: 0.8rem;
}

.risk-instance-view-details-btn:hover {
  background: #5a4abf;
  transform: translateY(-2px);
}

/* Title section styling */
.risk-instance-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  position: relative;
  width: 100%;
}

.risk-instance-title {
  font-size: 1.7rem;
  font-weight: 700;
  color: var(--form-header-text, var(--card-view-title-color, var(--text-primary, #333)));
  margin: 0;
  letter-spacing: 0.01em;
  position: relative;
  display: inline-block;
  padding-bottom: 6px;
  background: transparent;
  font-family: var(--font-family-primary, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif);
  flex: 1;
}

.risk-instance-title::after {
  content: '';
  display: block;
  margin-top: 4px;
  margin-left: 0;
  height: 4px;
  width: 25%;
  background: var(--primary-color, #4f7cff);
  border-radius: 2px;
}
.risk-instance-data-source {
  margin: 0 16px;
  font-size: 0.85rem;
  color: #2563eb;
  font-weight: 600;
  flex: 0 1 auto;
}

/* Priority/Status Badges */
.risk-instance-priority-badge,
.risk-instance-status-badge {
  padding: 3px 12px;
  border-radius: 16px;
  font-size: 0.8em;
  font-weight: 600;
  display: inline-block;
  min-width: 70px;
  text-align: center;
  background: transparent;
  border: 2px solid;
}

/* Priority colors */
.risk-instance-priority-critical {
  color: #990000;
  border-color: #990000;
  background: rgba(153, 0, 0, 0.1);
  border-radius: 999px;
  padding: 4px 18px;
}

.risk-instance-priority-high {
  color: #e57373;
  border-color: #e57373;
  background: rgba(229, 115, 115, 0.1);
  border-radius: 999px;
  padding: 4px 18px;
}

.risk-instance-priority-medium {
  color: #f9a825;
  border-color: #f9a825;
  background: rgba(249, 168, 37, 0.1);
  border-radius: 999px;
  padding: 4px 18px;
}

.risk-instance-priority-low {
  color: #1976d2;
  border-color: #1976d2;
  background: rgba(25, 118, 210, 0.1);
  border-radius: 999px;
  padding: 4px 18px;
}

/* Status indicators */
.risk-instance-status-badge {
  padding: 0;
  border-radius: 0;
  font-size: 0.8em;
  font-weight: 600;
  display: inline;
  min-width: 0;
  text-align: left;
  background: none;
  border: none;
}

.risk-instance-status-open {
  color: #2980b9;
  border: none;
  background: none;
}

.risk-instance-status-in-progress {
  color: #f39c12;
  border: none;
  background: none;
}

.risk-instance-status-approved {
  color: #27ae60;
  border: none;
  background: none;
}

.risk-instance-status-revision {
  color: #8e44ad;
  border: none;
  background: none;
}

.risk-instance-status-closed {
  color: #7f8c8d;
  border: none;
  background: none;
}

.risk-instance-status-rejected {
  color: #c0392b;
  border: none;
  background: none;
}

.risk-instance-due-status {
  margin-left: 4px;
  font-size: 0.75em;
  font-weight: 500;
  border-radius: 8px;
  padding: 2px 6px;
}

.overdue { background: #e74c3c; color: #fff; }
.urgent { background: #e67e22; color: #fff; }
.warning { background: #f1c40f; color: #222; }
.on-track { background: #2ecc71; color: #fff; }

.risk-instance-item-footer {
  margin-top: auto;
  display: flex;
  justify-content: flex-end;
}

/* Animation for cards */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.risk-instance-item-card {
  animation: fadeIn 0.4s ease-out forwards;
}

/* Custom status badge styling */
.risk-instance-status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.status-approved::before,
.status-open::before {
  content: '';
  margin-right: 0;
}

/* Media queries for responsive design */
@media (min-width: 1200px) {
  .risk-instance-cards-container {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Risk Dashboard Filter Status Styles */
.risk-filter-loading {
  font-size: 0.8rem;
  color: #f59e0b;
  margin-top: 4px;
  font-style: italic;
}

.risk-filter-error {
  font-size: 0.8rem;
  color: #ef4444;
  margin-top: 4px;
  font-style: italic;
}

.risk-filter-success {
  font-size: 0.8rem;
  color: #10b981;
  margin-top: 4px;
  font-style: italic;
}

@media (max-width: 1199px) and (min-width: 768px) {
  .risk-instance-cards-container {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 767px) {
  .risk-instance-cards-container {
    grid-template-columns: 1fr;
  }
  
  .risk-instance-container {
    padding: 16px;
  }
}

/* Risk Instances Table Styling - Adapted from RiskRegisterList.css */
:root {
  --risk-primary: #7B6FDD;
  --risk-primary-light: #8F84E8;
  --risk-primary-dark: #6A5ED4;
  --risk-secondary: #f72585;
  --risk-success: #4cc9f0;
  --risk-warning: #f8961e;
  --risk-danger: #e63946;
  --risk-light: #f8f9fa;
  --risk-dark: #212529;
  --risk-gray-100: #f8f9fa;
  --risk-gray-200: #e9ecef;
  --risk-gray-300: #dee2e6;
  --risk-gray-400: #ced4da;
  --risk-gray-500: #adb5bd;
  --risk-gray-600: #6c757d;
  --risk-gray-700: #495057;
  --risk-gray-800: #343a40;
  --risk-gray-900: #212529;
  --risk-border-radius: 8px;
  --risk-box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08);
  --risk-transition: all 0.3s ease;
}

/* Filter Controls Styles - Updated for search bar on top, dropdowns below */
.risk-instance-filters-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px 24px 16px 24px;
  background-color: transparent;
  margin-bottom: 0;
}

.risk-instance-search-row {
  display: flex;
  justify-content: flex-start;
  width: 100%;
}

.risk-instance-search-row :deep(.dynamic-search-bar) {
  min-width: 150px;
  max-width: 350px;
  flex: 0 0 auto;
  position: relative;
  background: transparent;
}

/* Clean Box-style search input styling - Only target input elements */
.risk-instance-search-row :deep(.dynamic-search-bar) input,
.risk-instance-search-row :deep(.dynamic-search-bar) .search-input,
.risk-instance-search-row :deep(.dynamic-search-bar) [type="text"],
.risk-instance-search-row :deep(.dynamic-search-bar) [type="search"] {
  background: #ffffff !important;
  border: 2px solid #e2e8f0 !important;
  border-radius: 4px !important;
  padding: 12px 16px !important;
  font-size: 0.9rem !important;
  font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
  color: #333 !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
  transition: all 0.3s ease !important;
  width: 100% !important;
  min-height: 42px !important;
  box-sizing: border-box !important;
  outline: none !important;
}

.risk-instance-search-row :deep(.dynamic-search-bar) input:focus,
.risk-instance-search-row :deep(.dynamic-search-bar) .search-input:focus,
.risk-instance-search-row :deep(.dynamic-search-bar) [type="text"]:focus,
.risk-instance-search-row :deep(.dynamic-search-bar) [type="search"]:focus {
  outline: none !important;
  border-color: #7B6FDD !important;
  box-shadow: 0 0 0 3px rgba(123, 111, 221, 0.1), 0 2px 8px rgba(0, 0, 0, 0.1) !important;
  background: #ffffff !important;
}

.risk-instance-search-row :deep(.dynamic-search-bar) input:hover,
.risk-instance-search-row :deep(.dynamic-search-bar) .search-input:hover,
.risk-instance-search-row :deep(.dynamic-search-bar) [type="text"]:hover,
.risk-instance-search-row :deep(.dynamic-search-bar) [type="search"]:hover {
  border-color: #cbd5e0 !important;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08) !important;
}

/* Clean styling - removed nuclear option */

/* Search icon styling if present */
.risk-instance-search-row :deep(.dynamic-search-bar) .search-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #666;
  font-size: 0.9rem;
  pointer-events: none;
}

.risk-instance-dropdowns-row {
  /* Use responsive grid for clean alignment */
  display: grid !important;
  grid-template-columns: repeat(4, minmax(180px, 1fr));
  gap: 12px !important;
  align-items: center !important;
  width: 100%;
  overflow: visible;
  padding-right: 0;
}

/* Style overrides for dynamic components */
.risk-instance-dropdowns-row :deep(.dropdown-container) {
  min-width: 0;
  max-width: none;
  width: 100%;
}

.risk-instance-dropdowns-row :deep(.filter-btn) {
  width: 100%;
  height: 40px;
  padding: 2px 10px;
  font-size: 12px;
  border: 1px solid var(--risk-gray-300);
  border-radius: 6px;
  background-color: white;
  transition: all 0.3s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.risk-instance-dropdowns-row :deep(.filter-btn):hover {
  border-color: var(--risk-primary);
  box-shadow: 0 0 0 2px rgba(123, 111, 221, 0.1);
}

.risk-instance-dropdowns-row :deep(.dropdown-label) {
  font-size: 0.75rem;
}

.risk-instance-dropdowns-row :deep(.dropdown-value) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 130px;
  display: inline-block;
}

.risk-instance-dropdowns-row :deep(.filter-btn svg) {
  width: 12px;
  height: 12px;
}

.risk-instance-dropdowns-row :deep(.dropdown-menu) {
  font-size: 0.75rem;
}

.risk-instance-dropdowns-row :deep(.dropdown-item) {
  padding: 6px 10px;
  font-size: 0.75rem;
}

.risk-instance-dropdowns-row :deep(.dropdown-search) {
  padding: 6px 8px;
  font-size: 0.75rem;
}

/* Dynamic Table Cell Styling */
.risk-instance-id {
  text-align: center;
  color: #7B6FDD;
  font-weight: 600;
  background: none !important;
  background-color: transparent !important;
  border-radius: 0 !important;
  width: 150px !important;
  max-width: 150px !important;
  min-width: 150px !important;
}

.risk-instance-origin-cell {
  text-align: center;
}

.risk-instance-category-cell {
  text-align: center;
}

.risk-instance-criticality-cell {
  text-align: center;
}

/* Criticality text colors */
.risk-instance-criticality-low {
  color:rgb(237, 206, 155) !important;
  font-weight: 600 !important;
}

.risk-instance-criticality-medium {
  color:rgb(241, 136, 84) !important;
  font-weight: 600 !important;
}

.risk-instance-criticality-high {
  color:rgb(210, 38, 19) !important;
  font-weight: 600 !important;
}

.risk-instance-criticality-critical {
  color:rgb(152, 31, 18) !important;
  font-weight: 700 !important;
}

.risk-instance-status-cell {
  text-align: center;
}

.risk-instance-department-cell {
  text-align: center;
  max-width: 200px;
  word-wrap: break-word;
}

.risk-instance-business-unit-cell {
  text-align: center;
  max-width: 200px;
  word-wrap: break-word;
}

.risk-instance-description-cell {
  max-width: 400px;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

/* Risk Description Link Styling */
.risk-description-link {
  color: #0066cc;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-block !important;
  line-height: 1.4;
  font-weight: 500;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  max-width: 100% !important;
}

.risk-description-link:hover {
  color: #004499;
  text-decoration: underline;
  background: none !important;
  border: none !important;
  box-shadow: none !important;
}

.risk-description-link:visited {
  color: #0066cc;
}

.risk-description-link:focus {
  outline: 2px solid #0066cc;
  outline-offset: 2px;
  background: none !important;
  border: none !important;
}

/* Risk Instance Row Styling with Criticality Colors */
.risk-instance-container :deep(.dynamic-table-row) {
  cursor: default;
  transition: background 0.2s ease;
  position: relative;
  box-shadow: none !important;
  transform: none !important;
}

/* Criticality-based row colors - Background removed */
.risk-instance-container :deep(.dynamic-table-row.criticality-critical) {
  background: transparent;
}

.risk-instance-container :deep(.dynamic-table-row.criticality-high) {
  background: transparent;
}

.risk-instance-container :deep(.dynamic-table-row.criticality-medium) {
  background: transparent;
}

.risk-instance-container :deep(.dynamic-table-row.criticality-low) {
  background: transparent;
}

/* Hover effects - No background change, no shadow, no transform */
.risk-instance-container :deep(.dynamic-table-row.criticality-critical:hover) {
  background: transparent;
}

.risk-instance-container :deep(.dynamic-table-row.criticality-high:hover) {
  background: transparent;
}

.risk-instance-container :deep(.dynamic-table-row.criticality-medium:hover) {
  background: transparent;
}

.risk-instance-container :deep(.dynamic-table-row.criticality-low:hover) {
  background: transparent;
}

/* Default hover for rows without criticality class */
.risk-instance-container :deep(.dynamic-table-row:hover:not([class*="criticality-"])) {
  background: transparent;
}

/* Responsive adjustments */
@media (max-width: 1200px) {
  .risk-instance-container {
    padding: 80px 16px 16px 210px;
  }
  
  .risk-instance-dropdowns-row {
    gap: 12px !important;
    grid-template-columns: repeat(2, minmax(160px, 1fr));
  }
  
  .risk-instance-dropdowns-row :deep(.dropdown-container) {
    min-width: 0;
    max-width: none;
  }
  
  .risk-instance-search-row :deep(.dynamic-search-bar) {
    min-width: 150px;
    max-width: 300px;
  }
}

@media (max-width: 768px) {
  .risk-instance-container {
    padding: 80px 16px 16px 16px;
  }
  
  .risk-instance-header-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .risk-instance-export-controls {
    align-self: stretch;
    justify-content: space-between;
  }
  
  .risk-instance-export-dropdown {
    min-width: 140px;
    flex: 1;
    margin-right: 12px;
  }
  
  .risk-instance-export-button {
    flex-shrink: 0;
  }
  
  .risk-instance-title {
    font-size: 1.4rem;
    margin-bottom: 0;
  }
  
  .risk-instance-search-row {
    justify-content: center;
  }
  
  .risk-instance-search-row :deep(.dynamic-search-bar) {
    min-width: 100%;
    max-width: 100%;
  }
  
  /* Mobile box styling for search */
  .risk-instance-search-row :deep(.dynamic-search-bar) input,
  .risk-instance-search-row :deep(.dynamic-search-bar) .search-input {
    padding: 10px 14px;
    font-size: 0.85rem;
    min-height: 40px;
  }
  
  .risk-instance-dropdowns-row {
    display: grid !important;
    grid-template-columns: 1fr;
    gap: 12px !important;
    width: 100%;
  }
  
  .risk-instance-dropdowns-row :deep(.dropdown-container) {
    min-width: 0;
    max-width: none;
  }
}

/* Additional responsive adjustments for 4 dropdowns */
@media (max-width: 1200px) {
  .risk-instance-dropdowns-row {
    gap: 8px !important;
  }
  
  .risk-instance-dropdowns-row :deep(.dropdown-container) {
    min-width: 180px;
    max-width: 200px;
  }
}

/* Override dynamic table styles to match risk instance theme - Remove double wrapper */
.risk-instance-container :deep(.dynamic-table-container) {
  background: transparent !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  border: none !important;
  padding: 0 !important;
  margin: 0 !important;
  overflow: visible !important;
}

.risk-instance-container :deep(.dynamic-table-container .table-wrapper) {
  margin-top: 0 !important;
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  overflow-x: hidden !important;
  width: 100% !important;
}

.risk-instance-container :deep(.dynamic-table) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  border-collapse: separate !important;
  table-layout: fixed !important;
  width: 100% !important;
}

.risk-instance-container :deep(.dynamic-table) th {
  background:rgb(237, 241, 245) !important;
  color: #333 !important;
  font-weight: 500 !important;
  padding: 8px 12px !important;
  text-align: left !important;
  font-size: 14px !important;
  border-bottom: 1px solid #dee2e6 !important;
  border-right: 1px solid #dee2e6 !important;
  white-space: nowrap !important;
  position: sticky !important;
  top: 0 !important;
  z-index: 2 !important;
}

.risk-instance-container :deep(.dynamic-table) th:first-child,
.risk-instance-container :deep(.dynamic-table) td:first-child {
  width: 150px !important;
  max-width: 150px !important;
  min-width: 150px !important;
}

.risk-instance-container :deep(.dynamic-table) th:last-child {
  border-right: none !important;
}

.risk-instance-container :deep(.dynamic-table thead th) {
  padding: 8px 12px !important;
}

.risk-instance-container :deep(.dynamic-table) .column-header {
  padding: 0 !important;
  font-size: 14px !important;
  font-weight: 500 !important;
}

.risk-instance-container :deep(.dynamic-table) .column-header span {
  font-weight: 500 !important;
}

.risk-instance-container :deep(.dynamic-table) .sort-btn {
  font-size: 8px !important;
  padding: 0 1px !important;
  margin-left: 2px !important;
}

.risk-instance-container :deep(.dynamic-table) .filter-arrows {
  margin-left: 2px !important;
  gap: 0 !important;
}

.risk-instance-container :deep(.dynamic-table) td {
  padding: 8px 12px !important;
  border-bottom: 1px solid #f1f3f4 !important;
  background-color: transparent !important;
  font-size: 0.8rem !important;
  font-weight: 400 !important;
  color: #333 !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  max-width: 200px !important;
}

.risk-instance-container :deep(.dynamic-table tbody td) {
  padding: 8px 12px !important;
  font-size: 0.8rem !important;
}

.risk-instance-container :deep(.dynamic-table tbody tr:nth-child(even)) {
  background-color: transparent !important;
}

.risk-instance-container :deep(.dynamic-table tbody tr:nth-child(odd)) {
  background-color: transparent !important;
}

.risk-instance-container :deep(.dynamic-table tbody tr:hover) {
  box-shadow: none !important;
  transform: none !important;
}

.risk-instance-container :deep(.dynamic-table-row) {
  box-shadow: none !important;
  transform: none !important;
}

.risk-instance-container :deep(.dynamic-table-row:hover) {
  box-shadow: none !important;
  transform: none !important;
}

.risk-instance-container :deep(.dynamic-table-row:active) {
  box-shadow: none !important;
  transform: none !important;
}

/* Ensure proper cell content display */
.risk-instance-container :deep(.dynamic-table td.risk-instance-origin-cell),
.risk-instance-container :deep(.dynamic-table td.risk-instance-category-cell),
.risk-instance-container :deep(.dynamic-table td.risk-instance-criticality-cell),
.risk-instance-container :deep(.dynamic-table td.risk-instance-status-cell) {
  text-align: center;
}

/* Ensure all cell children are properly truncated */
.risk-instance-container :deep(.dynamic-table td *) {
  max-width: 100% !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

/* Remove any unwanted underlines or black lines from table cells */
.risk-instance-container :deep(.dynamic-table) td,
.risk-instance-container :deep(.dynamic-table) td *,
.risk-instance-container :deep(.dynamic-table) tr,
.risk-instance-container :deep(.dynamic-table) tr * {
  text-decoration: none !important;
  border-bottom: none !important;
}

.risk-instance-container :deep(.dynamic-table) td:hover,
.risk-instance-container :deep(.dynamic-table) td:hover *,
.risk-instance-container :deep(.dynamic-table) tr:hover,
.risk-instance-container :deep(.dynamic-table) tr:hover * {
  text-decoration: none !important;
  border-bottom: none !important;
  box-shadow: none !important;
}

/* Remove old table styles that are no longer needed */
.risk-instance-table-container,
.risk-instance-table,
.risk-instance-search-input,
.risk-instance-filter-select {
  display: none;
}

/* Export controls styling */
.risk-instance-export-controls {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  margin: 0;
  padding: 0;
  position: relative;
  z-index: 10;
  flex-shrink: 0;
}

.risk-instance-export-dropdown-wrapper {
  position: relative;
  display: inline-block;
}

 
.risk-instance-export-dropdown {
  min-width: 150px;
  height: 38px;
  border-radius: 10px;
  border: 1.5px solid #d4d9e3;
  font-size: 0.9rem;
  padding: 0 14px;
  padding-right: 40px;
  background: #ffffff;
  color: #1f2937;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  font-family: inherit;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.06);
  transition: all 0.2s ease;
}
 
.risk-instance-export-dropdown:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 10px rgba(59, 130, 246, 0.12);
}
 
.risk-instance-export-dropdown:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}
 
.risk-instance-export-arrow {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.75rem;
  color: #666;
  pointer-events: none;
}
 
.risk-instance-export-button {
  padding: 9px 22px;
  border-radius: 10px;
  border: none;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  color: #fff;
  transition: all 0.2s ease;
  font-family: inherit;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.2);
}
 
.risk-instance-export-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #1d4ed8 0%, #1e3a8a 100%);
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.28);
}
 
.risk-instance-export-button:disabled {
  background: rgb(51, 134, 228);
  color: #ffffffaa;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.risk-instance-origin-badge {
  background-color: #eef1ff;
  color: #7B6FDD;
  padding: 4px 10px;
  border-radius: 999px;
  font-weight: 600;
  display: inline-block;
  font-size: 0.8rem;
  text-align: center;
}

/* Column Editor Modal Styles */
.risk-instance-column-editor-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  animation: fadeIn 0.2s ease;
}

.risk-instance-column-editor {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 450px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.column-editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.column-editor-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.column-editor-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: #6b7280;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.column-editor-close:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.column-editor-search {
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.column-search-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.9rem;
  transition: all 0.2s;
  box-sizing: border-box;
}

.column-search-input:focus {
  outline: none;
  border-color: #7B6FDD;
  box-shadow: 0 0 0 3px rgba(123, 111, 221, 0.1);
}

.column-editor-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;
  min-height: 200px;
  max-height: calc(80vh - 200px);
}

.column-editor-body::-webkit-scrollbar {
  width: 8px;
}

.column-editor-body::-webkit-scrollbar-track {
  background: #f3f4f6;
  border-radius: 4px;
}

.column-editor-body::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}

.column-editor-body::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

.column-editor-item {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  cursor: pointer;
  transition: background 0.15s;
  gap: 12px;
  user-select: none;
}

.column-editor-item:hover {
  background: #f9fafb;
}

.column-drag-handle {
  color: #9ca3af;
  font-size: 0.9rem;
  cursor: grab;
  display: flex;
  align-items: center;
}

.column-drag-handle:active {
  cursor: grabbing;
}

.column-editor-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #7B6FDD;
}

.column-label-text {
  flex: 1;
  font-size: 0.95rem;
  color: #374151;
}

.column-editor-empty {
  text-align: center;
  padding: 40px 20px;
  color: #9ca3af;
  font-size: 0.95rem;
}

</style>