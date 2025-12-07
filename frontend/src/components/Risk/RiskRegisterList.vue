<template>
  <div class="risk-register-container">
    <!-- Export Controls -->
    <div class="risk-register-export-controls">
      <select v-model="selectedExportFormat" class="risk-register-export-dropdown">
        <option value="" disabled>Select format</option>
        <option value="xlsx">Excel (.xlsx)</option>
        <option value="pdf">PDF (.pdf)</option>
        <option value="csv">CSV (.csv)</option>
        <option value="json">JSON (.json)</option>
        <option value="xml">XML (.xml)</option>
        <option value="txt">Text (.txt)</option>
      </select>
      <button @click="exportRiskRegister" :disabled="!selectedExportFormat" class="risk-register-export-btn">
        <i class="fas fa-download"></i>
        Export
      </button>
    </div>
    <!-- Add PopupModal component -->
    <PopupModal />
    
    <div class="risk-register-header-row">
      <h2 class="risk-register-title"> Risk Register List</h2>
      <p
        v-if="dataSourceMessage"
        class="risk-register-data-source"
      >
        {{ dataSourceMessage }}
      </p>
    </div>
    
    <!-- Filters Section - Search bar and dropdowns -->
    <div class="risk-register-filters-section">
      <!-- Search bar row -->
      <!-- <div class="risk-register-search-row">
        <Dynamicalsearch 
          v-model="searchQuery" 
          placeholder="Search risks..."
        />
      </div> -->
      <!-- <div class="risk-register-column-controls">
        <button type="button" class="risk-register-column-edit-btn" @click="toggleColumnEditor">
          <i class="fas fa-edit"></i>
          <span>Edit Columns</span>
        </button>
      </div> -->
      <transition name="fade">
        <div
          v-if="showColumnEditor"
          class="risk-register-column-editor-overlay"
          @click.self="toggleColumnEditor"
        >
          <div class="risk-register-column-editor" role="dialog" aria-modal="true">
            <div class="column-editor-header">
              <span class="column-editor-title">Choose Columns</span>
              <button type="button" class="column-editor-close-btn" @click="toggleColumnEditor" aria-label="Close column editor">
                <i class="fas fa-times"></i>
              </button>
            </div>
            <div class="column-editor-search">
              <i class="fas fa-search"></i>
              <input
                type="text"
                v-model="columnSearchQuery"
                placeholder="Search..."
                class="column-search-input"
              />
            </div>
            <div class="column-editor-body">
              <label
                v-for="column in filteredColumnDefinitions"
                :key="column.key"
                class="column-editor-option"
              >
                <input
                  type="checkbox"
                  :value="column.key"
                  v-model="columnSelection"
                  :disabled="column.removable === false"
                />
                <i class="fas fa-grip-vertical column-drag-handle"></i>
                <span class="column-label-text">{{ column.label }}</span>
              </label>
              <div v-if="filteredColumnDefinitions.length === 0" class="column-editor-empty">
                No columns found
              </div>
            </div>
          </div>
        </div>
      </transition>
    </div>


    <!-- Dynamic Table -->
    <DynamicTable
      :title="''"
      :data="tableData"
      :columns="tableColumns"
      :filters="[]"
      :show-checkbox="false"
      :show-actions="false"
      :show-pagination="true"
      :default-page-size="10"
      unique-key="RiskId"
      :get-row-class="getRowClass"
      @filter-change="handleFilterChange"
      @sort-change="handleSortChange"
      @page-change="handlePageChange"
      @row-click="handleRowClick"
      @remove-column="handleColumnRemove"
      @open-column-chooser="toggleColumnEditor"
      @reset-columns="resetColumnSelection"
    >
      <template #cell-RiskTitle="{ row }">
        <div class="risk-register-title-cell" :class="{ 'risk-register-new-row': isNewRisk(row) }">
          {{ row.RiskTitle }}
          <span v-if="isNewRisk(row)" class="risk-register-new-badge">NEW</span>
        </div>
      </template>
    </DynamicTable>
  </div>
</template>

<script>
import './RiskRegisterList.css'
import DynamicTable from '../DynamicTable.vue'
// import Dynamicalsearch from '../Dynamicalsearch.vue'
import { PopupModal } from '@/modules/popup'
import { API_ENDPOINTS, axiosInstance } from '../../config/api.js'
import riskDataService from '@/services/riskService' // NEW: Use cached risk data

export default {
  name: 'RiskRegisterList',
  components: {
    DynamicTable,
    // Dynamicalsearch,
    PopupModal
  },
  data() {
    const columnDefinitions = [
      {
        key: 'RiskTitle',
        dataSourceMessage: '',
        label: 'riskTitle',
        sortable: true,
        defaultVisible: true
      },
      {
        key: 'RiskId',
        label: 'riskId',
        sortable: true,
        defaultVisible: false
      },
      {
        key: 'RiskType',
        label: 'riskType',
        sortable: true,
        defaultVisible: true
      },
      {
        key: 'Category',
        label: 'category',
        sortable: true,
        defaultVisible: true
      },
      {
        key: 'Criticality',
        label: 'criticality',
        sortable: true,
        defaultVisible: true
      },
      {
        key: 'DepartmentName',
        label: 'department',
        sortable: true,
        defaultVisible: true
      },
      {
        key: 'BusinessUnitName',
        label: 'businessUnit',
        sortable: true,
        defaultVisible: true
      },
      {
        key: 'RiskDescription',
        label: 'riskDescription',
        sortable: false,
        defaultVisible: false,
        maxLength: 120
      },
      {
        key: 'RiskPriority',
        label: 'riskPriority',
        sortable: true,
        defaultVisible: false
      },
      {
        key: 'RiskMitigation',
        label: 'riskMitigation',
        sortable: false,
        defaultVisible: false,
        maxLength: 120
      },
      {
        key: 'PossibleDamage',
        label: 'possibleDamage',
        sortable: false,
        defaultVisible: false,
        maxLength: 120
      },
      {
        key: 'BusinessImpact',
        label: 'businessImpact',
        sortable: false,
        defaultVisible: false,
        maxLength: 120
      },
      {
        key: 'CreatedAt',
        label: 'createdAt',
        sortable: true,
        defaultVisible: false
      }
    ];

    const defaultVisibleKeys = columnDefinitions
      .filter(column => column.defaultVisible !== false)
      .map(column => column.key);

    return {
      risks: [],
      searchQuery: '',
      loading: false,
      selectedExportFormat: '',
      columnDefinitions,
      visibleColumnKeys: [...defaultVisibleKeys],
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
          if (requiredKeys.length > 0) {
            nextKeys = [...requiredKeys];
          } else if (this.visibleColumnKeys.length > 0) {
            nextKeys = [...this.visibleColumnKeys];
          } else if (this.columnDefinitions.length > 0) {
            nextKeys = [this.columnDefinitions[0].key];
          }
        }

        this.visibleColumnKeys = [...nextKeys];
      }
    },
    tableColumns() {
      return this.columnDefinitions.map(column => ({
        ...column,
        hidden: !this.visibleColumnKeys.includes(column.key)
      }));
    },
    filteredRisks() {
      let filtered = this.risks
      
      // Search filter - add type checking to prevent toLowerCase error
      if (this.searchQuery && typeof this.searchQuery === 'string' && this.searchQuery.trim() !== '') {
        const query = this.searchQuery.toLowerCase()
        filtered = filtered.filter(risk =>
          (risk.RiskTitle && risk.RiskTitle.toLowerCase().includes(query)) ||
          (risk.RiskDescription && risk.RiskDescription.toLowerCase().includes(query)) ||
          (risk.Category && risk.Category.toLowerCase().includes(query)) ||
          (risk.Criticality && risk.Criticality.toLowerCase().includes(query)) ||
          (risk.DepartmentName && risk.DepartmentName.toLowerCase().includes(query)) ||
          (risk.BusinessUnitName && risk.BusinessUnitName.toLowerCase().includes(query))
        )
      }
      
      // Sort by creation date - newest first
      filtered.sort((a, b) => {
        const dateA = new Date(a.CreatedAt || '1970-01-01')
        const dateB = new Date(b.CreatedAt || '1970-01-01')
        return dateB - dateA // Descending order (newest first)
      })
      
      return filtered
    },
    
    // Transform data for DynamicTable with proper status formatting
    tableData() {
      return this.filteredRisks.map(risk => ({
        ...risk,
        RiskType: risk.RiskType || 'Operational',
        // Department and Business Unit now handled by backend with random assignment
        DepartmentName: risk.DepartmentName,
        BusinessUnitName: risk.BusinessUnitName
      }))
    }
  },
  watch: {
    searchQuery() {
      // Reset to first page when search changes
    },
    showColumnEditor(value) {
      if (value) {
        document.addEventListener('keydown', this.handleColumnEditorEscape);
      } else {
        document.removeEventListener('keydown', this.handleColumnEditorEscape);
      }
    }
  },
  mounted() {
    this.fetchRisks()
  },
  activated() {
    // Refresh data when component becomes active (useful when coming back from other pages)
    console.log('RiskRegisterList activated - refreshing data...')
    this.fetchRisks()
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleColumnEditorEscape);
  },
  methods: {
    toggleColumnEditor() {
      this.showColumnEditor = !this.showColumnEditor;
      if (!this.showColumnEditor) {
        this.columnSearchQuery = '';
      }
    },

    resetColumnSelection() {
      const defaultKeys = this.columnDefinitions
        .filter(column => column.defaultVisible !== false)
        .map(column => column.key);
      this.visibleColumnKeys = [...defaultKeys];
    },

    handleColumnRemove(column) {
      if (!column || column.removable === false) {
        return;
      }
      const nextKeys = this.visibleColumnKeys.filter(key => key !== column.key);
      if (nextKeys.length === 0 && column.removable !== false) {
        // Prevent removing the last visible column
        return;
      }
      this.visibleColumnKeys = [...nextKeys];
    },

    handleColumnEditorEscape(event) {
      if (event.key === 'Escape' && this.showColumnEditor) {
        this.showColumnEditor = false;
      }
    },

    async fetchRisks() {
      this.loading = true
      try {
        console.log('🔍 [RiskRegisterList] Checking for cached risk data...');
        
        // FIRST: Try to get data from cache
        if (riskDataService.hasValidCache()) {
          console.log('✅ [RiskRegisterList] Using cached risk data');
          this.risks = riskDataService.getData('risks') || [];
          console.log(`[RiskRegisterList] Loaded ${this.risks.length} risks from cache`);
          this.dataSourceMessage = '';
        } else {
          // FALLBACK: If no cached data, fetch from API
          console.log('⚠️ [RiskRegisterList] No cached data found, fetching from API...');
          const response = await axiosInstance.get(API_ENDPOINTS.RISKS_FOR_DROPDOWN)
          
          // Handle both old and new response formats
          if (response.data.success && response.data.risks) {
            this.risks = response.data.risks
          } else {
            this.risks = response.data
          }
          console.log('Fetched risks from API:', this.risks.map(r => ({ id: r.RiskId, createdAt: r.CreatedAt })))
          this.dataSourceMessage = '';
        }
        
        this.loading = false
        
        // Send push notification for successful risk data fetch
        this.sendPushNotification({
          title: 'Risk Register Updated',
          message: `Successfully loaded ${this.risks.length} risks from the Risk Register.`,
          category: 'risk',
          priority: 'medium',
          user_id: 'default_user'
        })
      } catch (error) {
        console.error('Error fetching risks:', error)
        this.loading = false
        this.dataSourceMessage = 'Failed to load risks';
        
        // Send push notification for error
        this.sendPushNotification({
          title: 'Risk Register Load Failed',
          message: `Failed to load risks from the Risk Register: ${error.response?.data?.error || error.message}`,
          category: 'risk',
          priority: 'high',
          user_id: 'default_user'
        })
      }
    },
    async exportRiskRegister() {
      if (!this.selectedExportFormat) return;
      
      const startTime = Date.now();
      console.log(`🚀 [FRONTEND] Export started at ${new Date().toISOString()}`);
      console.log(`📊 [FRONTEND] Export format: ${this.selectedExportFormat}`);
      console.log(`📊 [FRONTEND] Data count: ${this.tableData.length} records`);
      
      try {
        // Prepare export data (filtered risks)
        const exportData = this.tableData;
        const payload = {
          export_format: this.selectedExportFormat,
          risk_data: exportData,
          user_id: 'default_user',
          file_name: 'risk_register_export'
        };
        
        console.log(`📦 [FRONTEND] Payload size: ${JSON.stringify(payload).length} characters`);
        console.log(`⏱️  [FRONTEND] Request timeout: 600000ms (10 minutes)`);
        console.log(`🌐 [FRONTEND] Sending request to: ${API_ENDPOINTS.EXPORT_RISK_REGISTER}`);
        
        // Increased timeout for large exports (10 minutes) - PDF conversion + S3 upload can take time
        const response = await axiosInstance.post(
          API_ENDPOINTS.EXPORT_RISK_REGISTER,
          payload,
          { timeout: 600000 } // 10 minutes for large PDF exports
        );
        
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
        console.log(`✅ [FRONTEND] Response received after ${elapsed} seconds`);
        console.log(`📊 [FRONTEND] Response status: ${response.status}`);
        console.log(`📊 [FRONTEND] Response data:`, response.data);
        const result = response.data;
        if (result.success && result.file_url && result.file_name) {
          // Try to open the file URL in a new tab, fallback to download if it fails
          try {
            const newWindow = window.open(result.file_url, '_blank');
            if (newWindow) {
              if (this.$popup) {
                this.$popup.success('Export completed successfully! File opened in new tab.', 'Export Success');
              } else if (window.PopupService) {
                window.PopupService.success('Export completed successfully! File opened in new tab.', 'Export Success');
              }
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
              if (this.$popup) {
                this.$popup.success('Export completed successfully! File downloaded.', 'Export Success');
              } else if (window.PopupService) {
                window.PopupService.success('Export completed successfully! File downloaded.', 'Export Success');
              }
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
            if (this.$popup) {
              this.$popup.success('Export completed successfully! File downloaded.', 'Export Success');
            } else if (window.PopupService) {
              window.PopupService.success('Export completed successfully! File downloaded.', 'Export Success');
            }
            console.error(downloadErr);
          }
        } else {
          if (this.$popup) {
            this.$popup.error('Export failed: ' + (result.error || 'Unknown error'), 'Export Error');
          } else if (window.PopupService) {
            window.PopupService.error('Export failed: ' + (result.error || 'Unknown error'), 'Export Error');
          }
        }
      } catch (error) {
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
        console.error(`❌ [FRONTEND] Export failed after ${elapsed} seconds`);
        console.error(`❌ [FRONTEND] Error type: ${error.constructor.name}`);
        console.error(`❌ [FRONTEND] Error message: ${error.message}`);
        console.error(`❌ [FRONTEND] Full error:`, error);
        
        if (error.response) {
          console.error(`❌ [FRONTEND] Response status: ${error.response.status}`);
          console.error(`❌ [FRONTEND] Response data:`, error.response.data);
        }
        
        if (error.code === 'ECONNABORTED') {
          console.error(`❌ [FRONTEND] Request timeout - took longer than 180 seconds`);
        }
        
        if (this.$popup) {
          this.$popup.error('Export error: ' + error.message, 'Export Error');
        } else if (window.PopupService) {
          window.PopupService.error('Export error: ' + error.message, 'Export Error');
        }
      }
    },
    
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
    
    handleSearch(value) {
      this.searchQuery = value
    },
    
    handleSortChange(sortInfo) {
      // Handle sorting if needed
      console.log('Sort changed:', sortInfo)
    },
    
    handlePageChange(page) {
      // Handle page change if needed
      console.log('Page changed:', page)
    },
    
    handleRowClick(row) {
      this.viewRiskDetails(row.RiskId);
    },

    getRowClass(row) {
      const baseClass = 'dynamic-table-row';
      if (!row.Criticality) return baseClass;
      
      const criticality = row.Criticality.toLowerCase();
      return `${baseClass} criticality-${criticality}`;
    },

    viewRiskDetails(riskId) {
      // Find the risk data for the notification
      const risk = this.risks.find(r => r.RiskId === riskId)
      
      // Send push notification for risk view action
      this.sendPushNotification({
        title: 'Risk Details Viewed',
        message: `Risk "${risk?.RiskTitle || 'Untitled Risk'}" (ID: ${riskId}) details have been viewed.`,
        category: 'risk',
        priority: 'low',
        user_id: 'default_user'
      })
      
      this.$router.push(`/view-risk/${riskId}`)
    },

    getCriticalityClass(criticality) {
      if (!criticality || typeof criticality !== 'string') return ''
      
      criticality = criticality.toLowerCase()
      if (criticality === 'critical') return 'risk-register-priority-critical'
      if (criticality === 'high') return 'risk-register-priority-high'
      if (criticality === 'medium') return 'risk-register-priority-medium'
      if (criticality === 'low') return 'risk-register-priority-low'
      return ''
    },

    formatDate(dateString) {
      if (!dateString) return 'N/A'
      
      const date = new Date(dateString)
      return date.toLocaleDateString()
    },



    isNewRisk(risk) {
      // Check if a risk was created in the last 2 hours (more generous for testing)
      if (!risk.CreatedAt) {
        console.log('No CreatedAt field for risk:', risk.RiskId)
        return false
      }
      
      const now = new Date()
      const riskCreatedAt = new Date(risk.CreatedAt)
      const timeDifference = now - riskCreatedAt
      const hoursInMilliseconds = 2 * 60 * 60 * 1000 // 2 hours for testing (was 24 hours)
      
      console.log('Risk', risk.RiskId, ':', {
        CreatedAt: risk.CreatedAt,
        parsedDate: riskCreatedAt,
        now: now,
        timeDifference: timeDifference,
        timeDifferenceHours: timeDifference / (60 * 60 * 1000),
        hoursInMs: hoursInMilliseconds,
        isNew: timeDifference <= hoursInMilliseconds
      })
      
      return timeDifference <= hoursInMilliseconds
    },

    refreshRisks() {
      this.fetchRisks();
      this.sendPushNotification({
        title: 'Risk Register Refreshed',
        message: 'Risk Register data has been refreshed.',
        category: 'risk',
        priority: 'medium',
        user_id: 'default_user'
      });
    },
  }
}
</script>

<style scoped>
/* Override CustomDropdown styles to reduce button width and create gaps */
.risk-register-dropdowns-row :deep(.dropdown-container) {
  width: 100% !important;
  max-width: 80% !important;
  min-width: 0 !important;
  margin: 0 !important;
  margin-left: 20px !important;
  margin-right: 20px !important;
  padding: 0 !important;
}

.risk-register-dropdowns-row :deep(.filter-btn) {
  width: 120% !important;
  max-width: 100% !important;
  min-width: 0 !important;
  height: 40px !important;
}

/* Export button styles - scoped to ensure it overrides */
.risk-register-export-btn {
  background-color: #4f8cff !important;
  background: #4f8cff !important;
  color: white !important;
}

.risk-register-export-btn:not(:disabled) {
  background-color: #4f8cff !important;
  background: #4f8cff !important;
  color: white !important;
}

.risk-register-export-btn:hover:not(:disabled) {
  background-color: #3d7aff !important;
  background: #3d7aff !important;
}

.risk-register-export-btn:disabled {
  background-color: #4f8cff !important;
  background: #4f8cff !important;
  color: white !important;
  opacity: 1 !important;
}
.risk-register-data-source {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #2563eb;
}
.risk-register-column-controls {
  display: flex;
  justify-content: flex-start;
  margin: 12px 0 0;
}

.risk-register-column-edit-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 8px 14px;
  color: #1f2937;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(15, 23, 42, 0.06);
  transition: background-color 0.2s ease, box-shadow 0.2s ease, color 0.2s ease;
}

.risk-register-column-edit-btn i {
  color: #4f8cff;
}

.risk-register-column-edit-btn:hover {
  background: #f3f4f6;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.12);
}

.risk-register-column-editor-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  padding: 20px;
}

.risk-register-column-editor {
  width: 100%;
  max-width: 360px;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.column-editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.column-editor-title {
  font-weight: 600;
  font-size: 16px;
  color: #111827;
}

.column-editor-close-btn {
  background: transparent;
  border: none;
  color: #6b7280;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s ease;
  font-size: 18px;
}

.column-editor-close-btn:hover {
  background: #f3f4f6;
  color: #111827;
}

.column-editor-search {
  padding: 12px 20px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f9fafb;
}

.column-editor-search i {
  color: #9ca3af;
  font-size: 14px;
}

.column-search-input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 14px;
  color: #111827;
  padding: 0;
}

.column-search-input::placeholder {
  color: #9ca3af;
}

.column-editor-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
  min-height: 200px;
  max-height: 500px;
}

/* Custom scrollbar for column editor */
.column-editor-body::-webkit-scrollbar {
  width: 8px;
}

.column-editor-body::-webkit-scrollbar-track {
  background: #f9fafb;
}

.column-editor-body::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}

.column-editor-body::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

.column-editor-option {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #1f2937;
  padding: 10px 20px;
  cursor: pointer;
  transition: background-color 0.15s ease;
  user-select: none;
}

.column-editor-option:hover {
  background: #f9fafb;
}

.column-editor-option input[type='checkbox'] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  margin: 0;
  flex-shrink: 0;
  accent-color: #2563eb;
}

.column-editor-option input[type='checkbox']:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.column-drag-handle {
  color: #9ca3af;
  font-size: 12px;
  cursor: grab;
  flex-shrink: 0;
}

.column-drag-handle:active {
  cursor: grabbing;
}

.column-label-text {
  flex: 1;
  font-size: 13px;
  color: #374151;
}

.column-editor-empty {
  padding: 40px 20px;
  text-align: center;
  color: #9ca3af;
  font-size: 14px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-enter-active .risk-register-column-editor {
  animation: slideIn 0.25s ease;
}

.fade-leave-active .risk-register-column-editor {
  animation: slideOut 0.2s ease;
}

@keyframes slideIn {
  from {
    transform: scale(0.95) translateY(-10px);
    opacity: 0;
  }
  to {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}

@keyframes slideOut {
  from {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
  to {
    transform: scale(0.95) translateY(-10px);
    opacity: 0;
  }
}

@media (max-width: 600px) {
  .risk-register-column-editor {
    padding: 20px;
    max-height: 80vh;
    overflow-y: auto;
  }
}
</style>