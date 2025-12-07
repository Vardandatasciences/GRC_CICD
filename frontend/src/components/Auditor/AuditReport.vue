<template>
  <div class="audit-report-container">

    <h1 class="audit-report-title">Audit Report</h1>
    <div v-if="loading" class="loading-message">Loading audit reports...</div>
    <div v-else-if="error" class="error-message">{{ error }}</div>
    <DynamicTable
      v-else
      :title="'Audit Reports'"
      :data="audits"
      :columns="visibleColumns"
      :unique-key="'AuditId'"
      :show-pagination="true"
      :default-page-size="10"
      :page-size-options="[5, 10, 20, 50]"
      @open-column-chooser="toggleColumnEditor"
    >
      <template #cell-AuditId="{ value }">
        <span class="audit-id-text">{{ value }}</span>
      </template>
      <template #cell-SubPolicy="{ value }">
        <span>{{ value || '-' }}</span>
      </template>
      <template #cell-reports="{ row }">
        <div class="report-actions">
          <i class="fas fa-eye action-icon view-icon" @click="viewReport(row.AuditId)" title="View Report"></i>
                     <i class="fas fa-download action-icon download-icon" @click="downloadReport(row.AuditId)" title="Download DOCX Report"></i>
        </div>
      </template>
    </DynamicTable>

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

<script>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';
import DynamicTable from '../DynamicTable.vue';
import { AccessUtils } from '@/utils/accessUtils';
import { API_ENDPOINTS } from '../../config/api.js';
import PopupService from '../../modules/popus/popupService.js';

export default {
  name: 'AuditReport',
  components: {
    DynamicTable
  },
  setup() {
    const audits = ref([]);
    const loading = ref(true);
    const error = ref(null);
    const downloadingVersion = ref(null);
    const router = useRouter();
    
    // Column chooser properties
    const showColumnEditor = ref(false);
    const columnSearchQuery = ref('');
    const visibleColumnKeys = ref(['AuditId', 'Framework', 'Policy', 'SubPolicy', 'CompletionDate', 'reports']);
    
    // Base URL for API calls
    // const API_BASE_URL = process.env.VUE_APP_API_URL || API_ENDPOINTS.API_BASE_URL;

    // Push notification sender
    const sendPushNotification = async (notificationData) => {
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
    };

    // All available columns - only columns with data
    const allColumns = computed(() => [
      {
        key: 'AuditId',
        label: 'Audit ID',
        sortable: true,
        cellClass: 'audit-id-cell',
        slot: true,
        resizable: true
      },
      {
        key: 'Framework',
        label: 'Framework',
        sortable: true,
        resizable: true
      },
      {
        key: 'Policy',
        label: 'Policy',
        sortable: true,
        resizable: true
      },
      {
        key: 'SubPolicy',
        label: 'Sub Policy',
        sortable: true,
        slot: true,
        resizable: true
      },
      {
        key: 'CompletionDate',
        label: 'Completion Date',
        sortable: true,
        resizable: true
      },
      {
        key: 'ReviewerComments',
        label: 'Reviewer Comments',
        sortable: true,
        resizable: true
      },
      {
        key: 'reports',
        label: 'Reports',
        sortable: false,
        cellClass: 'reports-cell',
        slot: true,
        resizable: true
      }
    ]);

    // Column definitions for column chooser - only columns with data
    const columnDefinitions = computed(() => [
      { key: 'AuditId', label: 'Audit ID', defaultVisible: true },
      { key: 'Framework', label: 'Framework', defaultVisible: true },
      { key: 'Policy', label: 'Policy', defaultVisible: true },
      { key: 'SubPolicy', label: 'Sub Policy', defaultVisible: true },
      { key: 'CompletionDate', label: 'Completion Date', defaultVisible: true },
      { key: 'ReviewerComments', label: 'Reviewer Comments', defaultVisible: false },
      { key: 'reports', label: 'Reports', defaultVisible: true }
    ]);

    // Visible columns based on user selection
    const visibleColumns = computed(() => {
      return allColumns.value.filter(col => visibleColumnKeys.value.includes(col.key));
    });

    // Filtered column definitions for search
    const filteredColumnDefinitions = computed(() => {
      if (!columnSearchQuery.value) {
        return columnDefinitions.value;
      }
      const query = columnSearchQuery.value.toLowerCase();
      return columnDefinitions.value.filter(col =>
        col.label.toLowerCase().includes(query) ||
        col.key.toLowerCase().includes(query)
      );
    });



    // Fetch all completed audits
    const fetchAudits = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        const response = await axios.get(API_ENDPOINTS.AUDIT_REPORTS);
        audits.value = response.data.audits;
      } catch (err) {
        console.error('Error fetching audit reports:', err);
        // Handle access denied errors
        if (AccessUtils.handleApiError(err, 'audit reports access')) {
          error.value = 'Access denied';
        } else {
          error.value = 'Failed to load audit reports. Please try again later.';
        }
      } finally {
        loading.value = false;
      }
    };



    // View report in TaskView
    const viewReport = (auditId) => {
      console.log(`Viewing report for audit ${auditId}`);
      // Store audit ID in localStorage for TaskView to use
      localStorage.setItem('current_audit_id', auditId);
      
      // Navigate to TaskView with this audit ID and specify we're coming from reports
      router.push(`/audit/${auditId}/tasks?from=reports`);
    };



    // Download audit report by generating it
    const downloadReport = async (auditId) => {
      try {
        downloadingVersion.value = auditId;
        
        console.log(`Generating and downloading report for audit ${auditId}`);
        
        // Show loading message
        console.log('Generating audit report...');
        
        // Call the generate audit report endpoint
        const response = await axios.get(`${API_ENDPOINTS.GENERATE_AUDIT_REPORT(auditId)}`, {
          responseType: 'blob',
          timeout: 30000 // 30 second timeout
        });
        
        // Create blob from response
        const blob = new Blob([response.data], {
          type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        });
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `audit_report_${auditId}.docx`;
        link.target = '_blank';
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Clean up
        window.URL.revokeObjectURL(url);
        
        console.log(`Report downloaded successfully for audit ${auditId}`);
        
        // Show success message
        PopupService.success(`Audit report for ID ${auditId} downloaded successfully`);
        
        // Send push notification about successful download
        sendPushNotification({
          title: 'Audit Report Downloaded',
          message: `Audit report for Audit ID ${auditId} has been downloaded successfully.`,
          category: 'audit',
          priority: 'medium',
          user_id: 'default_user'
        });
        
      } catch (err) {
        console.error(`Error downloading report for audit ${auditId}:`, err);
        
        // Handle specific error cases
        if (err.response) {
          if (err.response.status === 404) {
            PopupService.error(`No audit found with ID ${auditId}`);
          } else if (err.response.status === 403) {
            PopupService.error('Access denied. You do not have permission to download this report.');
          } else if (err.response.status === 500) {
            PopupService.error('Server error occurred while generating the report. Please try again later.');
          } else {
            PopupService.error(`Error downloading report: ${err.response.status} - ${err.response.statusText}`);
          }
        } else if (err.code === 'ECONNABORTED') {
          PopupService.error('Request timed out. The report generation is taking longer than expected.');
        } else {
          PopupService.error(`Error downloading report: ${err.message || 'Unknown error'}`);
        }
        
        // Send push notification about download error
        sendPushNotification({
          title: 'Audit Report Download Error',
          message: `Error occurred while downloading report for Audit ID ${auditId}.`,
          category: 'audit',
          priority: 'high',
          user_id: 'default_user'
        });
        
      } finally {
        // Reset the downloading state
        downloadingVersion.value = null;
      }
    };



    // Load audits when component is mounted
    // Column chooser methods
    const toggleColumnEditor = () => {
      showColumnEditor.value = !showColumnEditor.value;
      if (!showColumnEditor.value) {
        columnSearchQuery.value = '';
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
      return visibleColumnKeys.value.includes(columnKey);
    };
    
    const selectAllColumns = () => {
      visibleColumnKeys.value = columnDefinitions.value.map(col => col.key);
    };
    
    const deselectAllColumns = () => {
      visibleColumnKeys.value = [];
    };

    onMounted(fetchAudits);

    return { 
      audits, 
      loading,
      error,
      downloadingVersion,
      visibleColumns,
      viewReport,
      downloadReport,
      sendPushNotification,
      // Column chooser
      showColumnEditor,
      columnSearchQuery,
      filteredColumnDefinitions,
      toggleColumnEditor,
      toggleColumnVisibility,
      isColumnVisible,
      selectAllColumns,
      deselectAllColumns
    };
  }
}
</script>

<style scoped>
.audit-report-container {
  margin-left: 260px;
  min-height: 100vh;  
  max-width: calc(100vw - 320px);
  width: 100%;
  color: var(--text-primary, #334155);
  box-sizing: border-box;
  overflow-x: auto;
  font-family: var(--font-family-primary, 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif);
  padding: 40px 20px;
}
 
.audit-report-title {
  font-size: 1.8rem;
  font-weight: 700;
  color: black;
  margin-bottom: 28px;
  margin-top: 8px;
  position: relative;
  display: inline-block;
  padding-bottom: 6px;
  background: transparent;
}
 
.audit-report-title::after {
  display: none;
}

/* Table Container Styling */
.audit-report-container .dynamic-table-container {
  max-width: 100%;
  overflow-x: auto;
  position: relative;
  z-index: 1;
  margin: 0;
}

.audit-report-container .table-wrapper {
  width: 100%;
  overflow-x: auto;
}

.audit-report-container .dynamic-table {
  width: 100%;
  min-width: 100%;
  table-layout: fixed;
}

/* Ensure table columns are properly distributed */
.audit-report-container .dynamic-table th,
.audit-report-container .dynamic-table td {
  white-space: normal;
  overflow: visible;
  text-overflow: clip;
  padding: 16px 8px;
  word-wrap: break-word;
  overflow-wrap: break-word;
  vertical-align: top;
  min-height: 60px;
}

/* Make specific columns take appropriate width */
.audit-report-container .audit-id-cell {
  min-width: 80px;
  max-width: 100px;
}

.audit-report-container .reports-cell {
  min-width: 100px;
  max-width: 120px;
  position: relative;
  z-index: 9996;
}

/* Special handling for subpolicy column - display full text like policy column */
.audit-report-container .dynamic-table td:nth-child(4) {
  position: relative;
}

.audit-report-container .dynamic-table td:nth-child(4) span {
  display: block;
  overflow: visible;
  text-overflow: clip;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: break-word;
  line-height: 1.4;
}

.audit-report-container .dynamic-table th:nth-child(1),
.audit-report-container .dynamic-table td:nth-child(1) {
  min-width: 80px;
  max-width: 100px;
}

.audit-report-container .dynamic-table th:nth-child(2),
.audit-report-container .dynamic-table td:nth-child(2) {
  min-width: 100px;
  max-width: 120px;
}

.audit-report-container .dynamic-table th:nth-child(3),
.audit-report-container .dynamic-table td:nth-child(3) {
  min-width: 150px;
  max-width: 180px;
}

.audit-report-container .dynamic-table th:nth-child(4),
.audit-report-container .dynamic-table td:nth-child(4) {
  min-width: 200px;
  max-width: 250px;
}

.audit-report-container .dynamic-table th:nth-child(5),
.audit-report-container .dynamic-table td:nth-child(5) {
  min-width: 120px;
  max-width: 150px;
}

.audit-report-container .dynamic-table th:nth-child(6),
.audit-report-container .dynamic-table td:nth-child(6) {
  min-width: 80px;
  max-width: 100px;
}

.audit-report-container .dynamic-table th:nth-child(7),
.audit-report-container .dynamic-table td:nth-child(7) {
  min-width: 80px;
  max-width: 100px;
}

.audit-report-container .dynamic-table th:nth-child(8),
.audit-report-container .dynamic-table td:nth-child(8) {
  min-width: 100px;
  max-width: 120px;
}

.audit-id-text {
  color: var(--text-primary, #334155);
  font-weight: 600;
}

.report-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  position: relative;
  z-index: 10;
}

.action-icon {
  cursor: pointer;
  font-size: 1.3em;
  color: #475569;
  transition: color 0.2s;
  padding: 4px;
  border-radius: 4px;
}

.action-icon:hover {
  color: #d32f2f;
}

.view-icon {
  color: #2196F3;
}

.view-icon:hover {
  color: #1976D2;
}

.download-icon {
  color: #4CAF50;
}

.download-icon:hover {
  color: #388E3C;
}



.loading-message, 
.error-message, 
.no-data-message {
  text-align: center;
  margin: 20px 0;
  padding: 15px;
  border-radius: 8px;
  font-size: 14px;
}

.loading-message {
  background-color: #e3f2fd;
  color: #1565c0;
}

.error-message {
  background-color: #ffebee;
  color: #c62828;
}

.no-data-message {
  background-color: #fff8e1;
  color: #ff8f00;
}



.audit-report-header {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #334155;
  font-size: 1.8rem;
  margin-bottom: 1.5rem;
}

.audit-report-header i {
  color: #4f7cff;
  font-size: 1.6rem;
}

@media screen and (max-width: 1400px) {
  .audit-report-container {
    padding: 0 16px;
    max-width: calc(100vw - 320px);
  }
  
  .audit-report-container .dynamic-table-container {
    width: 100%;
    overflow-x: auto;
  }
}

@media screen and (max-width: 1200px) {
  .audit-report-container {
    padding: 0 12px;
    max-width: calc(100vw - 320px);
  }
  
  .audit-report-container .dynamic-table-container {
    width: 100%;
    overflow-x: auto;
  }
}

@media screen and (max-width: 700px) {
  .audit-report-container {
    margin-left: 0;
    padding: 10px;
    max-width: 100vw;
    width: 100%;
  }
  
  .audit-report-container .dynamic-table-container {
    width: 100%;
    overflow-x: auto;
  }
  
  .report-actions {
    flex-direction: column;
    gap: 4px;
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