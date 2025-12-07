<template>
  <div class="reviewer-page">
    <h1 class="reviewer-title">Review Audit</h1>
    <div v-if="loading" >
     
    </div>
    
    <div v-else-if="error" class="error-message">
      <p>{{ error }}</p>
      <button @click="fetchReviewTasks" class="btn-retry">Retry</button>
    </div>
    
    <div v-else-if="audits.length === 0" class="no-data">
      <p>No review tasks found</p>
    </div>
    
    <DynamicTable
      v-else
      :title="'Review Tasks'"
      :data="filteredAudits"
      :columns="visibleColumns"
      :filters="filters"
      :uniqueKey="'audit_id'"
      :showPagination="true"
      :defaultPageSize="10"
      @open-column-chooser="toggleColumnEditor"
    >
      <!-- Policy Cell -->
      <template #cell-policy="{ row }">
        <div class="cell-content-wrapper">
          {{ row.policy || 'All Policies' }}
        </div>
      </template>
      <!-- Subpolicy Cell -->
      <template #cell-subpolicy="{ row }">
        <div class="cell-content-wrapper">
          {{ row.subpolicy || 'All Subpolicies' }}
        </div>
      </template>
      <!-- Business Unit Cell -->
      <template #cell-business_unit="{ row }">
        <div class="cell-content-wrapper">
          {{ row.business_unit || 'Not Specified' }}
        </div>
      </template>
      <!-- Review Status Cell -->
      <template #cell-review_status="{ row }">
        <div class="cell-content-wrapper">
          <select 
            v-model="row.review_status" 
            @change="updateReviewStatus(row)" 
            class="review-status-select"
            v-if="row.status === 'Under review' && row.review_status !== 'Yet to Start' && row.review_status !== 'In Review' && row.review_status !== 'Reject'"
          >
            <option value="Accept">Approved</option>
            <option value="Reject">Reject</option>
          </select>
          <span v-else-if="row.review_status === 'Yet to Start' && row.status === 'Under review'">
            <button 
              @click="startReview(row)" 
              class="btn-review"
              title="Start review process"
            >
              Start
            </button>
          </span>
          <span v-else-if="(row.review_status === 'In Review' || row.review_status === 'Reject') && row.status === 'Under review'">
            <button 
              @click="openReviewDialog(row)" 
              class="btn-review btn-in-progress"
              title="Edit review in progress"
            >
              Edit Review
            </button>
            <span v-if="row.approved_rejected === 'Rejected'" class="approved-rejected-badge rejected" style="display: block; margin-top: 5px;">
              Rejected
            </span>
          </span>
          <span v-else-if="!row.approved_rejected">
            <div v-if="row.review_status === 'Accept'" class="review-status-dot-text approved">
              <span class="review-status-dot"></span>
              <span class="review-status-text">Approved</span>
            </div>
            <div v-else class="review-status-dot-text yet-to-start">
              <span class="review-status-dot"></span>
              <span class="review-status-text">{{ row.review_status }}</span>
            </div>
          </span>
          <span v-if="row.approved_rejected && !(row.review_status === 'Reject' && row.status === 'Under review')" class="review-status-dot-text" :class="getApprovedRejectedClass(row.approved_rejected)">
            <span class="review-status-dot"></span>
            <span class="review-status-text">{{ row.approved_rejected }}</span>
          </span>
        </div>
      </template>
      <!-- Audit Status Cell -->
      <template #cell-status="{ row }">
        <div class="cell-content-wrapper">
          <div class="status-dot-text" :class="getAuditStatusClass(row.status)">
            <span class="status-dot"></span>
            <span class="status-text">{{ row.status }}</span>
          </div>
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
import { api } from '../../data/api';
import axios from 'axios';
import auditorDataService from '@/services/auditorService'; // NEW: Use cached auditor data
import DynamicTable from '../DynamicTable.vue';
import { AccessUtils } from '@/utils/accessUtils';
import { API_ENDPOINTS } from '../../config/api.js';

export default {
  name: 'ReviewerPage',
  components: { DynamicTable },
  data() {
    return {
      audits: [],
      loading: true,
      error: null,
      searchQuery: '',
      statusFilter: '',
      businessUnitFilter: '',
      businessUnits: [],
      // Column chooser properties
      showColumnEditor: false,
      columnSearchQuery: '',
      visibleColumnKeys: ['audit_id', 'framework', 'policy', 'subpolicy', 'business_unit', 'duedate', 'status', 'review_status'],
      allColumns: [
        { key: 'audit_id', label: 'ID', sortable: true, resizable: true },
        { key: 'title', label: 'Title', sortable: true, resizable: true },
        { key: 'framework', label: 'Framework', sortable: true, resizable: true },
        { key: 'policy', label: 'Policy', sortable: true, resizable: true, slot: true },
        { key: 'subpolicy', label: 'Subpolicy', sortable: true, resizable: true, slot: true },
        { key: 'business_unit', label: 'Business Unit', sortable: true, resizable: true, slot: true },
        { key: 'duedate', label: 'Due Date', sortable: true, resizable: true },
        { key: 'status', label: 'Audit Status', sortable: true, resizable: true, slot: true },
        { key: 'review_status', label: 'Review Status', sortable: true, resizable: true, slot: true },
        { key: 'scope', label: 'Scope', sortable: true, resizable: true },
        { key: 'objective', label: 'Objective', sortable: true, resizable: true },
        { key: 'role', label: 'Role', sortable: true, resizable: true },
        { key: 'responsibility', label: 'Responsibility', sortable: true, resizable: true },
        { key: 'assignee', label: 'Assignee', sortable: true, resizable: true },
        { key: 'auditor', label: 'Auditor', sortable: true, resizable: true },
        { key: 'reviewer', label: 'Reviewer', sortable: true, resizable: true },
        { key: 'frequency', label: 'Frequency', sortable: true, resizable: true },
        { key: 'completion_date', label: 'Completion Date', sortable: true, resizable: true },
        { key: 'reviewer_comments', label: 'Reviewer Comments', sortable: true, resizable: true },
        { key: 'audit_type', label: 'Audit Type', sortable: true, resizable: true },
        { key: 'evidence', label: 'Evidence', sortable: true, resizable: true },
        { key: 'comments', label: 'Comments', sortable: true, resizable: true },
        { key: 'assigned_date', label: 'Assigned Date', sortable: true, resizable: true },
        { key: 'review_start_date', label: 'Review Start Date', sortable: true, resizable: true },
        { key: 'review_date', label: 'Review Date', sortable: true, resizable: true }
      ],
      columnDefinitions: [
        { key: 'audit_id', label: 'ID', defaultVisible: true },
        { key: 'title', label: 'Title', defaultVisible: false },
        { key: 'framework', label: 'Framework', defaultVisible: true },
        { key: 'policy', label: 'Policy', defaultVisible: true },
        { key: 'subpolicy', label: 'Subpolicy', defaultVisible: true },
        { key: 'business_unit', label: 'Business Unit', defaultVisible: true },
        { key: 'duedate', label: 'Due Date', defaultVisible: true },
        { key: 'status', label: 'Audit Status', defaultVisible: true },
        { key: 'review_status', label: 'Review Status', defaultVisible: true },
        { key: 'scope', label: 'Scope', defaultVisible: false },
        { key: 'objective', label: 'Objective', defaultVisible: false },
        { key: 'role', label: 'Role', defaultVisible: false },
        { key: 'responsibility', label: 'Responsibility', defaultVisible: false },
        { key: 'assignee', label: 'Assignee', defaultVisible: false },
        { key: 'auditor', label: 'Auditor', defaultVisible: false },
        { key: 'reviewer', label: 'Reviewer', defaultVisible: false },
        { key: 'frequency', label: 'Frequency', defaultVisible: false },
        { key: 'completion_date', label: 'Completion Date', defaultVisible: false },
        { key: 'reviewer_comments', label: 'Reviewer Comments', defaultVisible: false },
        { key: 'audit_type', label: 'Audit Type', defaultVisible: false },
        { key: 'evidence', label: 'Evidence', defaultVisible: false },
        { key: 'comments', label: 'Comments', defaultVisible: false },
        { key: 'assigned_date', label: 'Assigned Date', defaultVisible: false },
        { key: 'review_start_date', label: 'Review Start Date', defaultVisible: false },
        { key: 'review_date', label: 'Review Date', defaultVisible: false }
      ],
      filters: []
    };
  },
  computed: {
    filteredAudits() {
      let audits = this.audits;
      // Status filter (handled by DynamicTable filterFunction)
      // Search filter - search in framework, policy, auditor, business unit
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        audits = audits.filter(audit => {
          const searchFields = [
            audit.framework,
            audit.policy,
            audit.subpolicy,
            audit.business_unit,
            audit.auditor,
            audit.status,
            audit.review_status
          ].filter(Boolean).map(field => field.toLowerCase());
          return searchFields.some(field => field.includes(query));
        });
      }
      return audits;
    },
    visibleColumns() {
      return this.allColumns.filter(col => this.visibleColumnKeys.includes(col.key));
    },
    filteredColumnDefinitions() {
      if (!this.columnSearchQuery) {
        return this.columnDefinitions;
      }
      const query = this.columnSearchQuery.toLowerCase();
      return this.columnDefinitions.filter(col =>
        col.label.toLowerCase().includes(query) ||
        col.key.toLowerCase().includes(query)
      );
    },
  },
  created() {
    this.fetchReviewTasks();
    this.fetchBusinessUnits();
  },
  methods: {
    async fetchReviewTasks() {
      this.loading = true;
      this.error = null;
      
      try {
        console.log('Fetching review tasks...');
        const response = await api.getMyReviews();
        this.audits = response.data.audits;
        console.log(`Fetched ${this.audits.length} review tasks`);
        // Push notification for successful fetch (optional, can be omitted if not needed)
      } catch (error) {
        console.error('Error fetching review tasks:', error);
        // Handle access denied errors
        if (AccessUtils.handleApiError(error, 'review tasks access')) {
          this.error = 'Access denied';
        } else {
          this.error = error.response?.data?.error || 'Failed to load review tasks. Please try again.';
        }
        await this.sendPushNotification({
          title: 'Review Tasks Load Failed',
          message: this.error,
          category: 'review',
          priority: 'high',
          user_id: 'default_user'
        });
      } finally {
        this.loading = false;
      }
    },

    async fetchBusinessUnits() {
      try {
        console.log('🔍 [Reviewer] Checking for cached business units data...');
        
        // Try to get data from cache first
        if (auditorDataService.hasBusinessUnitsCache()) {
          console.log('✅ [Reviewer] Using cached business units data');
          this.businessUnits = auditorDataService.getData('businessUnits') || [];
          console.log(`[Reviewer] Loaded ${this.businessUnits.length} business units from cache`);
        } else {
          // Fallback: Fetch from API if cache is empty
          console.log('⚠️ [Reviewer] No cached business units found, fetching from API...');
          const response = await axios.get('/api/business-units/');
          this.businessUnits = response.data;
          
          // Update cache
          auditorDataService.setData('businessUnits', this.businessUnits);
          console.log('ℹ️ [Reviewer] Business units cache updated after direct API fetch');
        }
        
        // Update the business unit filter values
        const businessUnitFilter = this.filters.find(f => f.name === 'businessUnitFilter');
        if (businessUnitFilter) {
          businessUnitFilter.values = [
            { value: '', label: 'All Business Units' },
            ...this.businessUnits.map(bu => ({
              value: bu.value || bu.name,
              label: bu.value || bu.name
            }))
          ];
        }
      } catch (error) {
        console.error('Error fetching business units:', error);
      }
    },
    
    // Progress feature removed
    
    getApprovedRejectedClass(status) {
      if (status === 'Approved') return 'approved';
      if (status === 'Rejected') return 'rejected';
      return '';
    },
    
    getAuditStatusClass(status) {
      if (status === 'Completed') return 'audit-completed';
      if (status === 'Work In Progress') return 'audit-in-progress';
      if (status === 'Yet to Start') return 'audit-not-started';
      if (status === 'Under review') return 'audit-under-review';
      return 'audit-default';
    },
    

    
    startReview(audit) {
      // Change review status to 'In Review'
      audit.review_status = 'In Review';
      this.updateReviewStatus(audit);
      
      // Open the review dialog
      this.openReviewDialog(audit);
    },
    
    openReviewDialog(audit) {
      // Navigate to the ReviewTaskView component with the audit ID
      console.log(`Opening review for audit ${audit.audit_id}`);
      
      // If this was just updated to "Under review" status, add a query parameter
      // to indicate this is a fresh review
      const freshReview = audit.justUpdatedToUnderReview === true;
      
      if (freshReview) {
        console.log('This is a fresh review after status change, adding freshReview parameter');
        this.$router.push(`/reviewer/task/${audit.audit_id}?freshReview=true`);
      } else {
        this.$router.push(`/reviewer/task/${audit.audit_id}`);
      }
    },
    
    async updateReviewStatus(audit) {
      try {
        console.log(`Updating review status for audit ${audit.audit_id} to ${audit.review_status}`);
        
        // Flag to track if we just updated to "Under review" status
        let justUpdatedToUnderReview = false;
        
        // Check if the audit is not in 'Under review' status
        if (audit.status !== 'Under review') {
          console.log(`Audit status is currently ${audit.status}, updating to 'Under review' first`);
          
          // First update the audit status to 'Under review' using direct axios.post call
          // to avoid any method inconsistencies
          try {
            console.log(`Making direct POST request to ${API_ENDPOINTS.AUDIT_STATUS(audit.audit_id)}`);
            const statusResponse = await axios.post(API_ENDPOINTS.AUDIT_STATUS(audit.audit_id), {
              status: 'Under review'
            });
            console.log('Status update response:', statusResponse.data);
            
            // Update the local audit object
            audit.status = 'Under review';
            audit.justUpdatedToUnderReview = true; // Add flag to the audit object
            console.log('Audit status updated to Under review');
            justUpdatedToUnderReview = true;
          } catch (statusError) {
            console.error('Error updating audit status with direct axios:', statusError);
            console.error('Status code:', statusError.response?.status);
            console.error('Error message:', statusError.response?.data || statusError.message);
            
            // Try fallback to api.js implementation
            try {
              console.log('Trying fallback to api.updateAuditStatus...');
              const fallbackResponse = await api.updateAuditStatus(audit.audit_id, {
                status: 'Under review'
              });
              console.log('Fallback status update successful:', fallbackResponse.data);
              
              // Update the local audit object
              audit.status = 'Under review';
              audit.justUpdatedToUnderReview = true;
              console.log('Audit status updated to Under review via fallback');
              justUpdatedToUnderReview = true;
            } catch (fallbackError) {
              console.error('Both direct and fallback status update methods failed:', fallbackError);
              this.$popup.error(`Failed to update audit status. Please try again later. Error: ${fallbackError.message || 'Unknown error'}`);
              throw fallbackError;
            }
          }
        }
        
        // Prompt for review comments if status is being set to Reject
        let review_comments = '';
        if (audit.review_status === 'Reject') {
          review_comments = await this.$popup.comment('Please provide rejection comments:', 'Rejection Comments');
          if (review_comments === null) {
            // User cancelled the prompt, revert the status change
            this.fetchReviewTasks();
            await this.sendPushNotification({
              title: 'Review Rejection Cancelled',
              message: `Rejection for audit ID ${audit.audit_id} was cancelled by the user.`,
              category: 'review',
              priority: 'low',
              user_id: 'default_user'
            });
            return;
          }
        } else if (audit.review_status === 'Accept') {
          // Optionally prompt for approval comments
          review_comments = await this.$popup.comment('Please provide any approval comments (optional):', 'Approval Comments');
          if (review_comments === null) {
            // User cancelled the prompt, revert the status change
            this.fetchReviewTasks();
            await this.sendPushNotification({
              title: 'Review Approval Cancelled',
              message: `Approval for audit ID ${audit.audit_id} was cancelled by the user.`,
              category: 'review',
              priority: 'low',
              user_id: 'default_user'
            });
            return;
          }
        }
        
        const response = await api.updateReviewStatus(audit.audit_id, {
          review_status: audit.review_status,
          review_comments: review_comments
        });
        
        console.log('Review status updated successfully:', response.data);
        
        // Update the local audit object with the comments
        audit.review_comments = review_comments;
        
        // If accepted, update audit status to Completed
        if (audit.review_status === 'Accept' && response.data.audit_status) {
          audit.status = response.data.audit_status;
        }
        
        // Show success message
        this.$popup.success('Review status updated successfully!');
        await this.sendPushNotification({
          title: 'Review Status Updated',
          message: `Review status for audit ID ${audit.audit_id} updated to ${audit.review_status}.`,
          category: 'review',
          priority: 'medium',
          user_id: 'default_user'
        });
        
        // If we just updated to "Under review" and the review status is "In Review",
        // automatically open the review dialog
        if (justUpdatedToUnderReview && audit.review_status === 'In Review') {
          console.log('Automatically opening review dialog after status update');
          this.openReviewDialog(audit);
        }
        
      } catch (error) {
        console.error('Error updating review status:', error);
        // Revert the status change on error
        this.fetchReviewTasks(); // Reload data from server
        this.$popup.error(error.response?.data?.error || 'Failed to update review status. Please try again.');
        await this.sendPushNotification({
          title: 'Review Status Update Failed',
          message: `Failed to update review status for audit ID ${audit.audit_id}. Error: ${error.response?.data?.error || error.message}`,
          category: 'review',
          priority: 'high',
          user_id: 'default_user'
        });
      }
    },
    // --- Push Notification Method ---
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

    // Column chooser methods
    toggleColumnEditor() {
      this.showColumnEditor = !this.showColumnEditor;
      if (!this.showColumnEditor) {
        this.columnSearchQuery = '';
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
      return this.visibleColumnKeys.includes(columnKey);
    },
    
    selectAllColumns() {
      this.visibleColumnKeys = this.columnDefinitions.map(col => col.key);
    },
    
    deselectAllColumns() {
      this.visibleColumnKeys = [];
    }
  }
};
</script>

<style scoped>
@import '../styles/theme.css';
@import './Reviewer.css';

/* Remove main container edges and make background white */
:deep(.dynamic-table-container) {
  background: #ffffff !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 !important;
  border-radius: 0 !important;
  outline: none !important;
  width: 100% !important;
  max-width: 100% !important;
  overflow-x: visible !important;
}

:deep(.filters-section-above) {
  background: #ffffff !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 !important;
  border-radius: 0 !important;
  outline: none !important;
}

:deep(.filters-container) {
  background: #ffffff !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 !important;
  border-radius: 0 !important;
  outline: none !important;
}

/* Additional styles for text wrapping and business unit column */
.cell-content-wrapper {
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
  max-width: 100%;
  white-space: normal;
  line-height: 1.4;
}

/* Make table fit within screen without scrolling */
:deep(.table-wrapper) {
  width: 100% !important;
  max-width: 100% !important;
  overflow-x: auto !important;
}

:deep(.dynamic-table) {
  width: 100% !important;
  table-layout: fixed !important;
  max-width: 100% !important;
}

/* Match Audit Report table spacing exactly */
:deep(.dynamic-table th),
:deep(.dynamic-table td) {
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: clip !important;
  padding: 16px 8px !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  vertical-align: top !important;
  min-height: 60px !important;
  font-size: 12px !important;
  word-break: break-word !important;
  hyphens: auto !important;
  max-width: none !important;
  min-width: 80px !important;
  line-height: 1.4 !important;
}

/* Make header text smaller and compact */
:deep(.dynamic-table th) {
  font-size: 11px !important;
  font-weight: 600 !important;
  padding: 16px 8px !important;
  line-height: 1.3 !important;
  min-height: auto !important;
}

/* ID column - keep it narrow */
:deep(.dynamic-table th:first-child),
:deep(.dynamic-table td:first-child) {
  min-width: 60px !important;
  max-width: 80px !important;
}

/* Business unit specific styling */
:deep(.dynamic-table td[data-column="business_unit"]) {
  min-width: 100px !important;
}

/* Responsive adjustments for better text display - maintain spacing */
@media screen and (max-width: 1600px) {
  :deep(.dynamic-table th),
  :deep(.dynamic-table td) {
    font-size: 11px !important;
    padding: 16px 8px !important;
    min-width: 70px !important;
    min-height: 60px !important;
  }
}

@media screen and (max-width: 1400px) {
  :deep(.dynamic-table th),
  :deep(.dynamic-table td) {
    font-size: 11px !important;
    padding: 16px 8px !important;
    min-width: 60px !important;
    min-height: 60px !important;
  }
}

@media screen and (max-width: 1200px) {
  :deep(.dynamic-table th),
  :deep(.dynamic-table td) {
    font-size: 10px !important;
    padding: 14px 6px !important;
    min-width: 50px !important;
    min-height: 55px !important;
  }
  
  :deep(.dynamic-table th) {
    min-height: auto !important;
  }
}

/* Make status indicators and buttons more compact */
:deep(.status-dot-text),
:deep(.review-status-dot-text) {
  font-size: 11px !important;
  padding: 2px 6px !important;
}

:deep(.status-dot),
:deep(.review-status-dot) {
  width: 6px !important;
  height: 6px !important;
}

:deep(.btn-review),
:deep(.btn-in-progress) {
  font-size: 11px !important;
  padding: 4px 8px !important;
}

:deep(.review-status-select) {
  font-size: 11px !important;
  padding: 4px 6px !important;
}

/* Compress action buttons in review status column */
:deep(.approved-rejected-badge) {
  font-size: 10px !important;
  padding: 2px 6px !important;
}

/* Make overflow visible to prevent cut-off on small screens */
:deep(.reviewer-page) {
  overflow-x: visible !important;
}
</style>