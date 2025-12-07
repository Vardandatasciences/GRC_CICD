<template>
  <div class="risk-scoring-container">
    <!-- Add PopupModal component -->
    <PopupModal />
    
    <!-- Page Heading -->
    <div class="risk-scoring-title">
      Risk Scoring
    </div>
    <p
      v-if="dataSourceMessage"
      class="risk-scoring-data-source"
    >
      {{ dataSourceMessage }}
    </p>
    
    <!-- Search and Filter Bar -->
    <!-- <div class="risk-scoring-filters-wrapper">
      <Dynamicalsearch 
        v-model="searchQuery" 
        placeholder="Search..."
        @input="applyFilters"
      />
    </div> -->
    
    <div v-if="error" class="risk-scoring-error-message">
      {{ error }}
    </div>
    
    <div v-else-if="!loading && filteredRiskInstances.length === 0" class="risk-scoring-no-data">
      <p>No risk instances found.</p>
    </div>
    
    <div v-else-if="!loading">
      <DynamicTable
        :title="''"
        :data="filteredRiskInstances"
        :columns="tableColumns"
        :filters="[]"
        :show-checkbox="false"
        :show-actions="true"
        :show-pagination="true"
        :page-size-options="[7, 10, 20, 50]"
        :default-page-size="7"
        unique-key="RiskInstanceId"
        @filter-change="handleFilterChange"
        @open-column-chooser="toggleColumnEditor"
        @reset-columns="resetColumnSelection"
      >
        <template #actions="{ row }">
          <div class="risk-scoring-action-text">
            <span v-if="isScoringCompleted(row)" @click="viewScoringDetails(row.RiskInstanceId)">
              Scoring Completed <i class="fas fa-eye"></i>
            </span>
            <span v-else-if="isRiskRejected(row)" @click="viewScoringDetails(row.RiskInstanceId)">
              Instance Rejected <i class="fas fa-eye"></i>
            </span>
            <div v-else class="risk-scoring-simple-actions">
              <span class="accept-action" @click="mapScoringRisk(row.RiskInstanceId)">Accept</span>
              <span class="reject-action" @click="rejectRisk(row.RiskInstanceId)">Reject</span>
            </div>
          </div>
        </template>
        
        <template #cell-IncidentTitle="{ value }">
          {{ truncateText(value, 25) || 'N/A' }}
        </template>
        
        <template #cell-BusinessUnitName="{ value }">
          {{ truncateText(value, 20) || 'N/A' }}
        </template>
        
        <template #cell-RiskStatus="{ value }">
          <span class="risk-scoring-status-badge" :class="getStatusClass(value)">
            {{ value || 'Not Set' }}
          </span>
        </template>
        
        <template #cell-RiskDescription="{ value }">
          {{ truncateText(value, 50) || 'N/A' }}
        </template>
      </DynamicTable>
    </div>

    <!-- Column Editor Modal -->
    <div v-if="showColumnEditor" class="risk-scoring-column-editor-overlay" @click.self="toggleColumnEditor">
      <div class="risk-scoring-column-editor">
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
import axios from 'axios';
import './RiskScoring.css';
import { reactive } from 'vue';
import DynamicTable from '../DynamicTable.vue';
// import Dynamicalsearch from '../Dynamicalsearch.vue';
import { PopupModal } from '@/modules/popup';
import { API_ENDPOINTS } from '../../config/api.js';
import riskDataService from '@/services/riskService';

export default {
  name: 'RiskScoring',
  components: {
    DynamicTable,
    // Dynamicalsearch,
    PopupModal
  },
  data() {
    return {
      riskInstances: [],
      filteredRiskInstances: [],
      loading: true,
      error: null,
      dataSourceMessage: '',
      showActionButtons: reactive({}),
      searchQuery: '',
      columnDefinitions: [
        {
          key: 'RiskInstanceId',
          label: 'riskInstanceId',
          sortable: true,
          headerClass: 'risk-scoring-col-risk-id',
          cellClass: 'risk-scoring-col-risk-id',
          defaultVisible: true
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
          headerClass: 'risk-scoring-col-description',
          cellClass: 'risk-scoring-col-description',
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
          defaultVisible: false
        },
        {
          key: 'Category',
          label: 'category',
          sortable: true,
          headerClass: 'risk-scoring-col-category',
          cellClass: 'risk-scoring-col-category',
          defaultVisible: true
        },
        {
          key: 'Origin',
          label: 'origin',
          sortable: true,
          defaultVisible: false
        },
        {
          key: 'IncidentTitle',
          label: 'incident',
          sortable: true,
          headerClass: 'risk-scoring-col-incident',
          cellClass: 'risk-scoring-col-incident',
          defaultVisible: true
        },
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
        {
          key: 'BusinessImpact',
          label: 'businessImpact',
          sortable: true,
          defaultVisible: false
        },
        {
          key: 'BusinessUnitName',
          label: 'businessUnit',
          sortable: true,
          headerClass: 'risk-scoring-col-business-unit',
          cellClass: 'risk-scoring-col-business-unit',
          defaultVisible: true
        },
        {
          key: 'MitigationDueDate',
          label: 'mitigationDueDate',
          sortable: true,
          defaultVisible: false
        },
        {
          key: 'MitigationStatus',
          label: 'mitigationStatus',
          sortable: true,
          defaultVisible: false
        },
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
          headerClass: 'risk-scoring-col-status',
          cellClass: 'risk-scoring-col-status',
          slot: true,
          defaultVisible: true
        },
        {
          key: 'DepartmentName',
          label: 'department',
          sortable: true,
          defaultVisible: false
        }
      ],
      visibleColumnKeys: [],
      showColumnEditor: false,
      columnSearchQuery: '',
      mapScoringButtonConfig: {
        name: 'MAP SCORING RISK',
        className: 'risk-scoring-map-btn risk-scoring-map-btn-full',
        disabled: false
      }
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
    
    this.fetchRiskInstances();
    
    // Add event listener for sidebar toggle to adjust container margin
    window.addEventListener('resize', this.handleResize);
    
    // Initial check for sidebar state
    this.handleResize();
    
    // Add Font Awesome if not already present
    if (!document.querySelector('link[href*="font-awesome"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css';
      document.head.appendChild(link);
    }
  },
  // Refresh data when component is activated (coming back from another route)
  activated() {
    console.log('RiskScoring component activated - refreshing data');
    this.fetchRiskInstances();
  },
  beforeUnmount() {
    // Clean up event listener
    window.removeEventListener('resize', this.handleResize);
  },
  methods: {
    // Add push notification method
    async sendPushNotification(notificationData) {
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
    },
    
    applyFilters() {
      this.filterRiskInstances();
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
    handleFilterChange(filterData) {
      // Handle any additional filter changes from DynamicTable if needed
      console.log('Filter change:', filterData);
    },
    filterRiskInstances() {
      this.filteredRiskInstances = this.riskInstances.filter(risk => {
        // Search query filter
        const searchMatch = !this.searchQuery || 
          risk.RiskTitle?.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
          risk.RiskDescription?.toLowerCase().includes(this.searchQuery.toLowerCase());

        return searchMatch;
      });
    },
    
    // Simple response data processing
    validateResponseData(data) {
      if (!Array.isArray(data)) {
        console.error('Expected array response, got:', typeof data);
        return [];
      }
      
      return data;
    },
    
    isScoringCompleted(risk) {
      // Check if risk has RiskLikelihood, RiskImpact, and RiskExposureRating values
      // AND Appetite is 'Yes' (not rejected)
      const hasScoring = (
        risk.RiskLikelihood !== undefined && 
        risk.RiskLikelihood !== null && 
        risk.RiskImpact !== undefined && 
        risk.RiskImpact !== null && 
        risk.RiskExposureRating !== undefined && 
        risk.RiskExposureRating !== null
      );
      
      // Only show "Scoring Completed" if it has scoring AND is not rejected
      // Use case-insensitive comparison for Appetite and RiskStatus
      const appetite = (risk.Appetite || '').toLowerCase();
      const status = (risk.RiskStatus || '').toLowerCase();
      
      return hasScoring && appetite === 'yes' && status !== 'rejected';
    },
    isRiskRejected(risk) {
      // Check if risk has been rejected (Appetite is 'No' or RiskStatus is 'Rejected')
      // AND has scoring completed
      // Note: Rejected risks will not appear in the Risk Resolution screen
      const hasScoring = (
        risk.RiskLikelihood !== undefined && 
        risk.RiskLikelihood !== null && 
        risk.RiskImpact !== undefined && 
        risk.RiskImpact !== null && 
        risk.RiskExposureRating !== undefined && 
        risk.RiskExposureRating !== null
      );
      
      // Use case-insensitive comparison for Appetite and RiskStatus
      const appetite = (risk.Appetite || '').toLowerCase();
      const status = (risk.RiskStatus || '').toLowerCase();
      
      return hasScoring && (appetite === 'no' || status === 'rejected');
    },
    viewScoringDetails(riskId) {
      // Find the risk instance
      const risk = this.riskInstances.find(r => r.RiskInstanceId === riskId);
      
      console.log(`Viewing scoring details for Risk ${riskId}`);
      console.log(`Risk details: Status=${risk.RiskStatus}, Appetite=${risk.Appetite}`);
      console.log(`Display logic: isScoringCompleted=${this.isScoringCompleted(risk)}, isRiskRejected=${this.isRiskRejected(risk)}`);
      
      // Send push notification for viewing scoring details
      this.sendPushNotification({
        title: 'Risk Scoring Details Viewed',
        message: `Risk scoring details for "${risk.RiskTitle || 'Untitled Risk'}" (ID: ${riskId}) have been viewed.`,
        category: 'risk',
        priority: 'medium',
        user_id: 'default_user'
      });
      
      // Navigate to the scoring details page with the risk ID and action=view
      this.$router.push({
        path: `/risk/scoring-details/${riskId}`,
        query: { action: 'view' }
      });
    },
    fetchRiskInstances() {
      this.loading = true;
      this.dataSourceMessage = 'Loading risk instances...';
      
      const applyResponse = (data, source) => {
        console.log('Risk instances data received:', data);
        
        // Process each risk instance to ensure required fields are initialized
        this.riskInstances = data.map(risk => ({
          ...risk,
          RiskLikelihood: risk.RiskLikelihood || 1,
          RiskImpact: risk.RiskImpact || 1,
          RiskExposureRating: risk.RiskExposureRating || (risk.RiskLikelihood || 1) * (risk.RiskImpact || 1)
        }));
        
        this.filteredRiskInstances = [...this.riskInstances]; // Initialize filtered risks
        
        // Log risk status and appetite for debugging
        this.riskInstances.forEach(risk => {
          console.log(`Risk #${risk.RiskInstanceId}: Status=${risk.RiskStatus}, Appetite=${risk.Appetite}, Likelihood=${risk.RiskLikelihood}, Impact=${risk.RiskImpact}, Exposure=${risk.RiskExposureRating}`);
          
          // Initialize showActionButtons for each risk instance
          this.showActionButtons[risk.RiskInstanceId] = false;
        });
        
        // Send push notification for successful data load
        if (this.riskInstances.length > 0) {
          this.sendPushNotification({
            title: 'Risk Instances Loaded Successfully',
            message: `${this.riskInstances.length} risk instances have been loaded for scoring.`,
            category: 'risk',
            priority: 'medium',
            user_id: 'default_user'
          });
        }
        this.dataSourceMessage = source ? `Loaded ${this.riskInstances.length} risk instances ${source}` : '';
      };
      
      const fetchFromApi = () => axios.get(API_ENDPOINTS.RISK_SCORING_INSTANCES_WITH_NAMES)
        .then(response => {
          const apiData = Array.isArray(response.data) ? response.data : (response.data?.riskInstances || response.data || []);
          applyResponse(apiData, 'directly from API');
          riskDataService.setData('riskInstances', apiData);
        });
      
      Promise.resolve()
        .then(() => {
          if (riskDataService.hasRiskInstancesCache()) {
            const cachedData = riskDataService.getData('riskInstances') || [];
            if (cachedData.length > 0) {
              applyResponse(JSON.parse(JSON.stringify(cachedData)), '');
              this.loading = false;
              return null;
            }
          }
          return fetchFromApi();
        })
        .then(result => {
          if (result === null || result === undefined) {
            return;
          }
        })
        .catch(error => {
          console.error('Error fetching risk instances:', error);
          this.error = `Failed to fetch risk instances: ${error.message}`;
          this.dataSourceMessage = 'Failed to load risk instances';
          
          // Send push notification for error
          this.sendPushNotification({
            title: 'Risk Instances Load Failed',
            message: `Failed to load risk instances: ${error.message}`,
            category: 'risk',
            priority: 'high',
            user_id: 'default_user'
          });
        })
        .finally(() => {
          this.loading = false;
        });
    },
    handleResize() {
      // This method can be used to dynamically adjust the container based on sidebar state
      const container = document.querySelector('.risk-scoring-container');
      if (container) {
        // Adjust container based on window size
        if (window.innerWidth < 768) {
          container.style.marginLeft = '0';
          container.style.maxWidth = '100vw';
        } else if (window.innerWidth < 992) {
          container.style.marginLeft = '60px';
          container.style.maxWidth = 'calc(100vw - 60px)';
        } else if (window.innerWidth < 1200) {
          container.style.marginLeft = '200px';
          container.style.maxWidth = 'calc(100vw - 200px)';
        } else {
          container.style.marginLeft = '280px';
          container.style.maxWidth = 'calc(100vw - 280px)';
        }
      }
    },
    truncateText(text, maxLength) {
      if (!text) return '';
      
      // Direct truncation without sanitization
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },
    getStatusClass(status) {
      if (!status) return 'status-not-set';
      
      const normalizedStatus = status.toLowerCase().trim();
      
      switch (normalizedStatus) {
        case 'not assigned':
          return 'status-not-assigned';
        case 'assigned':
          return 'status-assigned';
        case 'approved':
          return 'status-approved';
        case 'rejected':
          return 'status-rejected';
        default:
          return 'status-default';
      }
    },
    toggleActionButtons(riskId) {
      // Direct toggle without validation
      this.showActionButtons[riskId] = !this.showActionButtons[riskId];
    },
    rejectRisk(riskId) {
      // Find the risk instance
      const risk = this.riskInstances.find(r => r.RiskInstanceId === riskId);
      
      // Send push notification for risk rejection
      this.sendPushNotification({
        title: 'Risk Instance Rejection Initiated',
        message: `Risk "${risk.RiskTitle || 'Untitled Risk'}" (ID: ${riskId}) is being rejected for scoring.`,
        category: 'risk',
        priority: 'high',
        user_id: 'default_user'
      });
      
      // Direct navigation without validation
      console.log(`Navigating to Scoring Details for Risk ${riskId} (rejected)`);
      // Navigate to the scoring details page with the risk ID and action=reject
      this.$router.push({
        path: `/risk/scoring-details/${riskId}`,
        query: { action: 'reject' }
      });
    },
    mapScoringRisk(riskId) {
      // Find the risk instance
      const risk = this.riskInstances.find(r => r.RiskInstanceId === riskId);
      
      // Send push notification for risk acceptance
      this.sendPushNotification({
        title: 'Risk Instance Acceptance Initiated',
        message: `Risk "${risk.RiskTitle || 'Untitled Risk'}" (ID: ${riskId}) is being accepted for scoring.`,
        category: 'risk',
        priority: 'high',
        user_id: 'default_user'
      });
      
      // Direct navigation without validation
      console.log(`Navigating to Scoring Details for Risk ${riskId} (accepted)`);
      // Navigate to the scoring details page with the risk ID and action=accept
      this.$router.push({
        path: `/risk/scoring-details/${riskId}`,
        query: { action: 'accept' }
      });
    }
  }
}
</script>

<style scoped>
@import './RiskScoring.css';
.risk-scoring-data-source {
  margin: 0 0 12px 0;
  font-size: 0.85rem;
  color: #2563eb;
  font-weight: 600;
}
/* Remove extra wrapper styling from inside DynamicTable */
:deep(.dynamic-table-container) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
}

:deep(.dynamic-table-container .table-wrapper) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin-top: 0 !important;
}

/* Add borders to table */
:deep(.dynamic-table) {
  border-collapse: separate !important;
  border-spacing: 0 !important;
}

:deep(.dynamic-table th) {
  border-bottom: 1px solid #dee2e6 !important;
  border-right: 1px solid #dee2e6 !important;
  background: rgb(237, 241, 245) !important;
  padding: 8px 12px !important;
  font-weight: 500 !important;
}

:deep(.dynamic-table th:last-child) {
  border-right: none !important;
}

:deep(.dynamic-table td) {
  border-bottom: 1px solid #f0f0f0 !important;
  border-right: 1px solid #f5f5f5 !important;
  padding: 8px 12px !important;
}

:deep(.dynamic-table td:last-child) {
  border-right: none !important;
}

:deep(.dynamic-table tbody tr:last-child td) {
  border-bottom: 1px solid #dee2e6 !important;
}

/* Column Editor Modal Styles */
.risk-scoring-column-editor-overlay {
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

.risk-scoring-column-editor {
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