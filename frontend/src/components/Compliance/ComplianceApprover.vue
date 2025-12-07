<template>
  <div class="compliance_main_container">
    <!-- Page Header -->
    <div class="compliance_header">
      <div class="compliance_title_section">
        <h1 class="compliance_title">Compliance Approval</h1>
        <p class="compliance_subtitle">Review and manage compliance approval requests</p>
      </div>
    </div>
    
    <!-- Error message -->
    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-triangle"></i>
      <span>{{ error }}</span>
      <button @click="refreshData" class="retry-btn">
        <i class="fas fa-refresh"></i>
        Retry
      </button>
    </div>
    
    <!-- Filter Section -->
    <div class="compliance_filter_section">
      <!-- User Selection for Administrators -->
      <div v-if="isAdministrator" class="compliance_filter_block">
        <div class="compliance_filter_label">
          <i class="fas fa-users"></i>
          <span>USER SELECTION</span>
        </div>
        <select 
          id="userSelect" 
          v-model="selectedUserId" 
          @change="onUserChange" 
          class="compliance_filter_dropdown"
        >
          <option v-for="user in availableUsers" :key="user.UserId" :value="user.UserId">
            {{ user.UserName }} ({{ user.Role }})
          </option>
        </select>
      </div>
      
      <!-- Framework Filter -->
      <div class="compliance_filter_block">
        <div class="compliance_filter_label">
          <i class="fas fa-filter"></i>
          <span>FRAMEWORK FILTER</span>
        </div>
        <select 
          id="framework-filter" 
          v-model="selectedFramework" 
          @change="handleFrameworkChange"
          class="compliance_filter_dropdown"
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
    </div>
    
    <!-- Active Filter Warning -->
    <!-- <div v-if="selectedFramework" class="filter-active-warning">
      <i class="fas fa-info-circle"></i>
      <span>
        <strong>Filter Active:</strong> Showing compliances for 
        <strong>{{ frameworks.find(f => f.FrameworkId.toString() === selectedFramework.toString())?.FrameworkName || 'Unknown Framework' }}</strong>
      </span>
      <button @click="clearFilters" class="clear-warning-btn">
        <i class="fas fa-times"></i>
        Clear
      </button>
    </div> -->
    
    <!-- Summary Cards Section -->
    <div class="compliance_summary_section">
      <div class="compliance_summary_item">
        <div class="compliance_summary_icon pending">
          <i class="fas fa-clock"></i>
        </div>
        <div class="compliance_summary_content">
          <div class="compliance_summary_number">{{ pendingApprovalsCount }}</div>
          <div class="compliance_summary_label">Pending Review</div>
        </div>
      </div>
      
      <div class="compliance_summary_item">
        <div class="compliance_summary_icon approved">
          <i class="fas fa-check-circle"></i>
        </div>
        <div class="compliance_summary_content">
          <div class="compliance_summary_number">{{ approvedApprovalsCount }}</div>
          <div class="compliance_summary_label">Approved</div>
        </div>
      </div>
      
      <div class="compliance_summary_item">
        <div class="compliance_summary_icon rejected">
          <i class="fas fa-times-circle"></i>
        </div>
        <div class="compliance_summary_content">
          <div class="compliance_summary_number">{{ rejectedApprovalsCount }}</div>
          <div class="compliance_summary_label">Rejected</div>
        </div>
      </div>
      
      
    </div>

    <!-- Task Navigation Tabs -->
    <div class="compliance_task_navigation">
      <div class="compliance_nav_tabs">
        <button 
          class="compliance_nav_tab"
          :class="{ active: activeTab === 'myTasks' }"
          @click="switchTab('myTasks')"
        >
          <i class="fas fa-user"></i>
          <span>My Tasks</span>
          <span class="compliance_tab_badge">{{ myTasksCount }}</span>
        </button>
        <button 
          class="compliance_nav_tab"
          :class="{ active: activeTab === 'reviewerTasks' }"
          @click="switchTab('reviewerTasks')"
        >
          <i class="fas fa-users"></i>
          <span>Reviewer Tasks</span>
          <span class="compliance_tab_badge">{{ reviewerTasksCount }}</span>
        </button>
      </div>
    </div>

    <!-- Render My Tasks or Reviewer Tasks based on activeTab -->
    <div v-if="activeTab === 'myTasks'" class="compliance_tasks_container">
      <!-- <h2 class="compliance_tasks_title">My Compliance Approval Tasks (Latest Versions)</h2> -->
      <CollapsibleTable
        v-if="myTasksPending.length"
        :sectionConfig="{ name: 'Pending Review', statusClass: 'pending', tasks: myTasksPendingPaged.map(mapApprovalToRow) }"
        :tableHeaders="approvalTableHeaders"
        :isExpanded="myTasksCollapsible.Pending"
        @toggle="() => myTasksCollapsible.Pending = !myTasksCollapsible.Pending"
        @taskClick="handleApprovalAction"
        :pagination="{
          currentPage: myTasksPagination.Pending.currentPage,
          totalPages: Math.ceil(myTasksPending.length / myTasksPagination.Pending.pageSize),
          pageSize: myTasksPagination.Pending.pageSize,
          totalCount: myTasksPending.length,
          pageSizeOptions: [10],
          onPageSizeChange: () => {},
          onPageChange: page => handleMyTasksPageChange('Pending', page)
        }"
      />
      <CollapsibleTable
        v-if="myTasksApproved.length"
        :sectionConfig="{ name: 'Approved', statusClass: 'approved', tasks: myTasksApprovedPaged.map(mapApprovalToRow) }"
        :tableHeaders="approvalTableHeaders"
        :isExpanded="myTasksCollapsible.Approved"
        @toggle="() => myTasksCollapsible.Approved = !myTasksCollapsible.Approved"
        @taskClick="handleApprovalAction"
        :pagination="{
          currentPage: myTasksPagination.Approved.currentPage,
          totalPages: Math.ceil(myTasksApproved.length / myTasksPagination.Approved.pageSize),
          pageSize: myTasksPagination.Approved.pageSize,
          totalCount: myTasksApproved.length,
          pageSizeOptions: [10],
          onPageSizeChange: () => {},
          onPageChange: page => handleMyTasksPageChange('Approved', page)
        }"
      />
      <CollapsibleTable
        v-if="myTasksRejected.length"
        :sectionConfig="{ name: 'Rejected', statusClass: 'rejected', tasks: myTasksRejectedPaged.map(mapApprovalToRow) }"
        :tableHeaders="approvalTableHeaders"
        :isExpanded="myTasksCollapsible.Rejected"
        @toggle="() => myTasksCollapsible.Rejected = !myTasksCollapsible.Rejected"
        @taskClick="handleApprovalAction"
        :pagination="{
          currentPage: myTasksPagination.Rejected.currentPage,
          totalPages: Math.ceil(myTasksRejected.length / myTasksPagination.Rejected.pageSize),
          pageSize: myTasksPagination.Rejected.pageSize,
          totalCount: myTasksRejected.length,
          pageSizeOptions: [10],
          onPageSizeChange: () => {},
          onPageChange: page => handleMyTasksPageChange('Rejected', page)
        }"
      />
      <div v-if="!myTasksPending.length && !myTasksApproved.length && !myTasksRejected.length" class="no-tasks-message">
        <div class="no-tasks-icon">
          <i class="fas fa-clipboard-check"></i>
        </div>
      </div>
      
      <!-- Rejected Compliances (Edit & Resubmit) Section -->
      <CollapsibleTable
        v-if="rejectedCompliances.length"
        :sectionConfig="{ name: 'Rejected Compliances (Edit & Resubmit)', statusClass: 'rejected', tasks: rejectedCompliances }"
        :tableHeaders="rejectedTableHeaders"
        :isExpanded="myTasksCollapsible.RejectedCompliances"
        @toggle="() => myTasksCollapsible.RejectedCompliances = !myTasksCollapsible.RejectedCompliances"
        @taskClick="handleApprovalAction"
        @editTask="handleEditTask"
      />
      <div v-if="!rejectedCompliances.length" class="compliance_no_tasks">
        <div class="compliance_no_tasks_icon">
          <i class="fas fa-clipboard-check"></i>
        </div>
        <h4>No Rejected Compliances</h4>
        <p>{{ selectedUserInfo && isAdministrator ? `${selectedUserInfo.UserName} doesn't have` : 'You don\'t have' }} any rejected compliances to edit or resubmit.</p>
      </div>
    </div>
    <div v-if="activeTab === 'reviewerTasks'" class="compliance_tasks_container">
      <h2 class="compliance_tasks_title">Reviewer Tasks (Latest Versions)</h2>
      <CollapsibleTable
        v-if="reviewerTasksPending.length"
        :sectionConfig="{ name: 'Pending Review', statusClass: 'pending', tasks: reviewerTasksPendingPaged.map(mapApprovalToRow) }"
        :tableHeaders="approvalTableHeaders"
        :isExpanded="reviewerTasksCollapsible.Pending"
        @toggle="() => reviewerTasksCollapsible.Pending = !reviewerTasksCollapsible.Pending"
        @taskClick="handleApprovalAction"
        :pagination="{
          currentPage: reviewerTasksPagination.Pending.currentPage,
          totalPages: Math.ceil(reviewerTasksPending.length / reviewerTasksPagination.Pending.pageSize),
          pageSize: reviewerTasksPagination.Pending.pageSize,
          totalCount: reviewerTasksPending.length,
          pageSizeOptions: [10],
          onPageSizeChange: () => {},
          onPageChange: page => handleReviewerTasksPageChange('Pending', page)
        }"
      />
      <CollapsibleTable
        v-if="reviewerTasksApproved.length"
        :sectionConfig="{ name: 'Approved', statusClass: 'approved', tasks: reviewerTasksApprovedPaged.map(mapApprovalToRow) }"
        :tableHeaders="approvalTableHeaders"
        :isExpanded="reviewerTasksCollapsible.Approved"
        @toggle="() => reviewerTasksCollapsible.Approved = !reviewerTasksCollapsible.Approved"
        @taskClick="handleApprovalAction"
        :pagination="{
          currentPage: reviewerTasksPagination.Approved.currentPage,
          totalPages: Math.ceil(reviewerTasksApproved.length / reviewerTasksPagination.Approved.pageSize),
          pageSize: reviewerTasksPagination.Approved.pageSize,
          totalCount: reviewerTasksApproved.length,
          pageSizeOptions: [10],
          onPageSizeChange: () => {},
          onPageChange: page => handleReviewerTasksPageChange('Approved', page)
        }"
      />
      <CollapsibleTable
        v-if="reviewerTasksRejected.length"
        :sectionConfig="{ name: 'Rejected', statusClass: 'rejected', tasks: reviewerTasksRejectedPaged.map(mapApprovalToRow) }"
        :tableHeaders="approvalTableHeaders"
        :isExpanded="reviewerTasksCollapsible.Rejected"
        @toggle="() => reviewerTasksCollapsible.Rejected = !reviewerTasksCollapsible.Rejected"
        @taskClick="handleApprovalAction"
        :pagination="{
          currentPage: reviewerTasksPagination.Rejected.currentPage,
          totalPages: Math.ceil(reviewerTasksRejected.length / reviewerTasksPagination.Rejected.pageSize),
          pageSize: reviewerTasksPagination.Rejected.pageSize,
          totalCount: reviewerTasksRejected.length,
          pageSizeOptions: [10],
          onPageSizeChange: () => {},
          onPageChange: page => handleReviewerTasksPageChange('Rejected', page)
        }"
      />
      <div v-if="!reviewerTasksPending.length && !reviewerTasksApproved.length && !reviewerTasksRejected.length" class="reviewer-empty-wrapper">
        <div class="compliance_no_tasks">
          <div class="compliance_no_tasks_icon">
            <i class="fas fa-clipboard-check"></i>
          </div>
          <h4>No Reviewer Tasks</h4>
          <p>{{ selectedUserInfo && isAdministrator ? `${selectedUserInfo.UserName} doesn't have` : 'You don\'t have' }} any reviewer tasks at the moment.</p>
        </div>
      </div>
    </div>

    <!-- (Comment out or remove the old groupedApprovals rendering) -->
    <!--
    <div class="compliance-approval-container">
      ... (old groupedApprovals code) ...
    </div>
    -->
    
    <!-- Edit Modal for Rejected Compliance -->
    <div v-if="showEditComplianceModal && editingCompliance" class="edit-compliance-modal">
      <div class="edit-compliance-content">
        <div class="modal-header">
          <h3>Edit & Resubmit Compliance</h3>
          <button class="close-btn" @click="closeEditComplianceModal">&times;</button>
        </div>
        
        <div class="modal-body">
          <!-- Two column layout -->
          <div class="form-columns">
            <div class="form-column">
              <div class="form-field">
                <label>Identifier:</label>
                <input type="text" v-model="editingCompliance.Identifier" readonly />
              </div>
              
              <div class="form-field">
                <label>Description <span class="required">*</span>:</label>
                <textarea 
                  v-model="editingCompliance.ExtractedData.ComplianceItemDescription"
                  rows="3"
                  class="description-input"
                ></textarea>
              </div>
              
              <div class="form-field">
                <label>Criticality <span class="required">*</span>:</label>
                <select v-model="editingCompliance.ExtractedData.Criticality" class="select-input">
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
              </div>
            </div>
            
            <div class="form-column">
              <div class="form-field">
                <label>Severity Rating <span class="required">*</span>:</label>
                <input 
                  type="text" 
                  v-model="editingCompliance.ExtractedData.Impact" 
                  @input="logFieldChange('Impact', $event.target.value)"
                  class="text-input"
                />
                <small v-if="!editingCompliance.ExtractedData.Impact" class="field-error">⚠️ This field is required</small>
              </div>
              
              <div class="form-field">
                <label>Probability <span class="required">*</span>:</label>
                <input 
                  type="text" 
                  v-model="editingCompliance.ExtractedData.Probability" 
                  @input="logFieldChange('Probability', $event.target.value)"
                  class="text-input"
                />
                <small v-if="!editingCompliance.ExtractedData.Probability" class="field-error">⚠️ This field is required</small>
              </div>
              
              <div class="form-field">
                <label>Mitigation:</label>
                <textarea 
                  v-model="mitigationString"
                  rows="3"
                  class="description-input"
                ></textarea>
              </div>
            </div>
          </div>
          
          <!-- Full width rejection reason -->
          <div class="form-field full-width">
            <label>Rejection Reason:</label>
            <div class="rejection-reason-box">{{ getRejectionReason(editingCompliance) }}</div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="cancel-button" @click="closeEditComplianceModal">
            Cancel
          </button>
          <button 
            class="resubmit-button" 
            @click="validateAndResubmit(editingCompliance)" 
            :disabled="isLoading"
            :class="{ 'submitting': isLoading }">
            <i class="fas fa-redo" v-if="!isLoading"></i>
            <i class="fas fa-spinner fa-spin" v-if="isLoading"></i>
            {{ isLoading ? 'Submitting...' : 'Resubmit for Review' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- Compliance Details Modal -->
    <div v-if="showDetailsModal && selectedApproval" class="compliance-details-modal" @click="closeDetailsModal">
      <div class="compliance-details-modal-content" @click.stop>
        <!-- Header Section -->
        <div class="compliance-details-header">
          <button class="close-btn" @click="closeDetailsModal">&times;</button>
          
          <h3>
            <span class="detail-type-indicator">Compliance</span>
            <span v-if="selectedApproval.ExtractedData?.RequestType === 'Change Status to Inactive' || selectedApproval.ExtractedData?.type === 'compliance_deactivation'">
              Deactivation Request: {{ selectedApproval.Identifier }}
            </span>
            <span v-else>
              Details: {{ selectedApproval.Identifier }}
            </span>
          </h3>
        </div>

        <!-- Main Content Area -->
        <div class="policy-details-content">
          <!-- Compliance Approval Section -->
          <div class="policy-approval-section">
            <h4>
              <span v-if="selectedApproval.ExtractedData?.RequestType === 'Change Status to Inactive' || selectedApproval.ExtractedData?.type === 'compliance_deactivation'">
                Compliance Deactivation Approval
              </span>
              <span v-else>
                Compliance Approval
              </span>
            </h4>
            
            <!-- Quick Action Button - Removed to prevent duplicate submissions -->
            <!-- The Approve/Reject buttons below handle all approval actions -->
            
            <!-- Approval Status Display -->
            <div v-if="approvalStatus" class="policy-approval-status">
              <div class="status-container">
                <div class="status-label">Current Status:</div>
                <div class="status-value" :class="{
                  'approved': approvalStatus.approved === true,
                  'rejected': approvalStatus.approved === false,
                  'pending': approvalStatus.approved === null
                }">
                  {{ approvalStatus.approved === true ? 'Approved' :
                     approvalStatus.approved === false ? 'Rejected' : 'Pending Review' }}
                </div>
              </div>
              
              <!-- Approval Date Display -->
              <div v-if="selectedApproval.ApprovedDate" class="approval-date">
                <div class="date-label">
                  <i class="fas fa-calendar-check"></i>
                  Approved on:
                </div>
                <div class="date-value">{{ formatDate(selectedApproval.ApprovedDate) }}</div>
              </div>
              
              <!-- Rejection Remarks -->
              <div v-if="approvalStatus.approved === false && getRejectionReason(selectedApproval)" class="policy-rejection-remarks">
                <div class="remarks-label">
                  <i class="fas fa-exclamation-circle"></i>
                  Rejection Reason:
                </div>
                <div class="remarks-value">{{ getRejectionReason(selectedApproval) }}</div>
              </div>
            </div>
          </div>
          
          <!-- Compliance Details Display -->
          <div v-if="selectedApproval.ExtractedData" class="compliance-details">
            <!-- Deactivation Request Details -->
            <div v-if="selectedApproval.ExtractedData?.RequestType === 'Change Status to Inactive' || selectedApproval.ExtractedData?.type === 'compliance_deactivation'" 
                 class="deactivation-request-details">
              
              <div class="compliance-detail-row">
                <strong>
                  <i class="fas fa-question-circle"></i>
                  Reason for Deactivation:
                </strong>
                <span>{{ selectedApproval.ExtractedData.reason || 'No reason provided' }}</span>
              </div>
              
              <div class="compliance-detail-row">
                <strong>
                  <i class="fas fa-info-circle"></i>
                  Current Status:
                </strong>
                <span class="status-badge current">{{ selectedApproval.ExtractedData.current_status }}</span>
              </div>
              
              <div class="compliance-detail-row">
                <strong>
                  <i class="fas fa-arrow-right"></i>
                  Requested Status:
                </strong>
                <span class="status-badge requested">{{ selectedApproval.ExtractedData.requested_status }}</span>
              </div>
              
              <div class="compliance-detail-row">
                <strong>
                  <i class="fas fa-sitemap"></i>
                  Cascade to Policies:
                </strong>
                <span class="cascade-indicator" :class="{ 'warning': selectedApproval.ExtractedData.cascade_to_policies === 'Yes' }">
                  {{ selectedApproval.ExtractedData.cascade_to_policies }}
                </span>
              </div>
              
              <div v-if="selectedApproval.ExtractedData.affected_policies_count > 0" class="compliance-detail-row">
                <strong>
                  <i class="fas fa-file-alt"></i>
                  Affected Policies:
                </strong>
                <span class="policy-count">{{ selectedApproval.ExtractedData.affected_policies_count }} policies</span>
              </div>
              
              <!-- Enhanced Warning Message -->
              <div class="warning-message">
                <i class="fas fa-exclamation-triangle"></i>
                <span>
                  <strong>Warning:</strong> Deactivating this compliance will make it inactive.
                  {{ selectedApproval.ExtractedData.cascade_to_policies === 'Yes' ? 
                     'All related policies will also be deactivated.' : 
                     'Related policies will not be affected.' }}
                </span>
              </div>
            </div>
            
            <!-- Regular Compliance Details -->
            <div v-else>
              <div class="compliance-detail-row">
                <strong>
                  <i class="fas fa-hashtag"></i>
                  Identifier:
                </strong>
                <span>{{ selectedApproval.Identifier || selectedApproval.ExtractedData?.Identifier || 'N/A' }}</span>
              </div>
              
              <div class="compliance-detail-row">
                <strong>
                  <i class="fas fa-file-text"></i>
                  Description:
                </strong>
                <span>{{ selectedApproval.ExtractedData.ComplianceItemDescription }}</span>
              </div>
              
              <div class="compliance-detail-row">
                <strong>
                  <i class="fas fa-exclamation"></i>
                  Criticality:
                </strong>
                <span class="criticality-badge" :class="selectedApproval.ExtractedData.Criticality?.toLowerCase()">
                  {{ selectedApproval.ExtractedData.Criticality }}
                </span>
              </div>
              
              <div class="compliance-detail-row">
                <strong>
                  <i class="fas fa-chart-line"></i>
                  Severity Rating:
                </strong>
                <span class="severity-rating">
                  {{ getImpactValue() }}
                  <small v-if="!getImpactValue()" style="color: #999; font-style: italic;">
                    (Field not found in data)
                  </small>
                </span>
              </div>
              
              <div class="compliance-detail-row">
                <strong>
                  <i class="fas fa-percentage"></i>
                  Probability:
                </strong>
                <span class="probability-value">
                  {{ getProbabilityValue() }}
                  <small v-if="!getProbabilityValue()" style="color: #999; font-style: italic;">
                    (Field not found in data)
                  </small>
                </span>
              </div>
              
              <div class="compliance-detail-row">
                <strong>
                  <i class="fas fa-shield-alt"></i>
                  Mitigation:
                </strong>
                <span>{{ formatMitigation(selectedApproval.ExtractedData.mitigation) }}</span>
              </div>
              
              <!-- Debug section - remove after fixing -->
              
            </div>
            
            <!-- Action Buttons -->
            <div class="policy-actions">
              <!-- Debug information for troubleshooting -->
              
              
              <!-- Show approve/reject buttons only for assigned reviewers -->
              <button class="approve-btn" @click="approveCompliance()" :disabled="isLoading || isSubmitting" v-if="canPerformReviewActions(selectedApproval)">
                <i class="fas fa-check"></i>
                <span>{{ isSubmitting ? 'Processing...' : 'Approve' }}</span>
              </button>
              <button class="reject-btn" @click="rejectCompliance()" :disabled="isLoading || isSubmitting" v-if="canPerformReviewActions(selectedApproval)">
                <i class="fas fa-times"></i>
                <span>{{ isSubmitting ? 'Processing...' : 'Reject' }}</span>
              </button>
              

              
              <!-- Show resubmission indicator -->
              <div v-if="selectedApproval.ExtractedData?.compliance_approval?.inResubmission" class="resubmission-indicator">
                <i class="fas fa-redo-alt"></i>
                <span><strong>Resubmitted for Review:</strong> This compliance was previously rejected and has been resubmitted with modifications.</span>
              </div>
              
              <!-- Show message for compliance creators -->
              <div v-if="isCurrentUserCreator(selectedApproval) && approvalStatus && approvalStatus.approved === null" class="creator-message">
                <i class="fas fa-info-circle"></i>
                <span>This compliance is under review. You cannot approve or reject your own compliance.</span>
              </div>
              
              <!-- Show message for administrators who are not assigned as reviewers -->
              <div v-if="isAdministrator && !canPerformReviewActions(selectedApproval) && approvalStatus && approvalStatus.approved === null" class="admin-message">
                <i class="fas fa-eye"></i>
                <span>Viewing compliance. You are not assigned as the reviewer for this compliance.</span>
              </div>
              
              <!-- Show message when buttons are not visible for other reasons -->
              <div v-if="!isCurrentUserCreator(selectedApproval) && !isAdministrator && !canPerformReviewActions(selectedApproval) && approvalStatus && approvalStatus.approved === null" class="debug-message">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Debug: Buttons not visible. Check console for details.</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Enhanced Rejection Modal -->
    <div v-if="showRejectModal" class="reject-modal">
      <div class="reject-modal-content">
        <h4>
          <i class="fas fa-times-circle"></i>
          Rejection Reason Required
        </h4>
        <p>Please provide a detailed reason for rejecting this compliance item. This information will be used to improve future submissions.</p>
        
        <textarea
          v-model="rejectionComment"
          class="rejection-comment"
          placeholder="Enter your detailed comments here...">
        </textarea>
        
        <div class="reject-modal-actions">
          <button class="cancel-btn" @click="cancelRejection">
            <i class="fas fa-arrow-left"></i>
            Cancel
          </button>
          <button class="confirm-btn" @click="confirmRejection">
            <i class="fas fa-check"></i>
            Confirm Rejection
          </button>
        </div>
      </div>
    </div>
    
    <!-- Add PopupModal component -->
    <PopupModal />
  </div>

  <!-- Move Rejected Compliances section inside the tasks container -->
</template>
 
<script>
import { complianceService } from '@/services/api';
import complianceDataService from '@/services/complianceService'; // NEW: Use cached compliance data
import { PopupModal } from '../../modules/popup';
import PopupMixin from './mixins/PopupMixin';
import { CompliancePopups } from './utils/popupUtils';
import CollapsibleTable from '../CollapsibleTable.vue';
import AccessUtils from '@/utils/accessUtils';
import axios from 'axios';
import { API_ENDPOINTS } from '../../config/api.js';
 
export default {
  name: 'ComplianceApprover',
  components: {
    PopupModal,
    CollapsibleTable
  },
  mixins: [PopupMixin],
  data() {
    return {
      approvals: [],
      selectedApproval: null,
      showRejectModal: false,
      rejectionComment: '',
      showEditComplianceModal: false,
      editingCompliance: null,
      originalComplianceData: null, // Store original data for change detection
      isLoading: false,
      isSubmitting: false, // Prevent duplicate submissions
      error: null,
      counts: {
        pending: 0,
        approved: 0,
        rejected: 0
      },
      refreshInterval: null,
      isLoadingRejected: false,
      isDeactivationRequest: false,
      collapsibleStates: {
        Pending: true,
        Approved: false,
        Rejected: false,
        'Recently Approved': false
      },
      // Add pagination state for each section
      pagination: {
        Pending: { currentPage: 1, pageSize: 10, totalCount: 0 },
        Approved: { currentPage: 1, pageSize: 10, totalCount: 0 },
        Rejected: { currentPage: 1, pageSize: 10, totalCount: 0 },
        'Recently Approved': { currentPage: 1, pageSize: 10, totalCount: 0 }
      },
      showDetailsModal: false, // New state for details modal
      activeTab: 'myTasks', // Default to 'myTasks'
      selectedUserId: '', // To hold the selected user ID
      availableUsers: [], // To store available users for dropdown
      myTasks: [],
      reviewerTasks: [],
      isAdministrator: false,
      selectedUserInfo: null,
      currentUserId: null,
      currentUserName: '',
      myTasksCollapsible: {
        Pending: true,
        Approved: false,
        Rejected: false,
        RejectedCompliances: true,
      },
      reviewerTasksCollapsible: {
        Pending: true,
        Approved: false,
        Rejected: false,
      },
      myTasksPagination: {
        Pending: { currentPage: 1, pageSize: 10 },
        Approved: { currentPage: 1, pageSize: 10 },
        Rejected: { currentPage: 1, pageSize: 10 },
      },
      reviewerTasksPagination: {
        Pending: { currentPage: 1, pageSize: 10 },
        Approved: { currentPage: 1, pageSize: 10 },
        Rejected: { currentPage: 1, pageSize: 10 },
      },
      mitigationString: '',
      
      // Framework filtering properties
      frameworks: [],
      selectedFramework: '',
      sessionFrameworkId: null,
    }
  },
  async mounted() {
        // console.log('ComplianceApprover mounted');
    
    // First, fetch frameworks
    await this.fetchFrameworks();
    
    // Check for selected framework from session after loading frameworks
    await this.checkSelectedFrameworkFromSession();
    
    // Initialize user
    await this.initializeUser();
    
    // After framework is set from session, reload tasks to apply the filter
    // This ensures data is loaded with the correct framework filter
    if (this.selectedFramework) {
      console.log('🔄 Reloading tasks with framework filter from session:', this.selectedFramework);
      await this.loadUserTasks();
    }
    
    // Debug user consistency after initialization
    this.debugUserConsistency();
    
    // Set up auto-refresh every 30 seconds
    this.refreshInterval = setInterval(() => {
      this.refreshData();
    }, 30000);
    
    // Add escape key handler for modal
    document.addEventListener('keydown', this.handleKeydown);
  },
  beforeUnmount() {
    // Clear the refresh interval when component is destroyed
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
    
    // Remove escape key handler
    document.removeEventListener('keydown', this.handleKeydown);
  },
  watch: {
    // Watch for changes in data and update pagination counts
    complianceApprovals: {
      handler() {
        this.updatePaginationCounts();
      },
      deep: true
    },
    approvedComplianceItems: {
      handler() {
        this.updatePaginationCounts();
      },
      deep: true
    },
    // Watch for rejected compliances and ensure users are available for name mapping
    rejectedCompliances: {
      handler() {
        // Ensure users are available when rejected compliances change
        this.ensureUsersAvailable();
      },
      deep: true
    },
    editingCompliance: {
      handler(newVal) {
        if (newVal && newVal.ExtractedData && newVal.ExtractedData.mitigation) {
          if (typeof newVal.ExtractedData.mitigation === 'object') {
            this.mitigationString = JSON.stringify(newVal.ExtractedData.mitigation, null, 2);
          } else {
            this.mitigationString = newVal.ExtractedData.mitigation;
          }
        }
      },
      deep: true
    },
    mitigationString(newVal) {
      if (this.editingCompliance && this.editingCompliance.ExtractedData) {
        try {
          // Try to parse as JSON, fallback to string
          this.editingCompliance.ExtractedData.mitigation = JSON.parse(newVal);
        } catch {
          this.editingCompliance.ExtractedData.mitigation = newVal;
        }
      }
    },
  },
  methods: {
    getCriticalityClass(criticality) {
      if (!criticality) return '';
      const criticalityLower = criticality.toLowerCase();
      if (criticalityLower === 'high') {
        return 'criticality-high';
      } else if (criticalityLower === 'medium') {
        return 'criticality-medium';
      } else if (criticalityLower === 'low') {
        return 'criticality-low';
      }
      return '';
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
    async refreshData() {
      if (this.isLoading) return; // Prevent multiple simultaneous refreshes
      
      this.isLoading = true;
      this.error = null;
      // console.log('🔄 Refreshing compliance approval data...');
      
      try {
        // Fetch approvals with reviewer_id - use currentUserId
        const approvalsResponse = await complianceService.getCompliancePolicyApprovals({
          reviewer_id: this.currentUserId
        });
        // console.log('📡 Approvals response:', approvalsResponse);

        if (approvalsResponse.data.success) {
          // Debug the incoming data
          // console.log('📊 Raw approvals data:', approvalsResponse.data.data);
          
          // Check for deactivation requests specifically
          // const deactivationRequests = (approvalsResponse.data.data || []).filter(approval => 
          //   approval.ExtractedData?.type === 'compliance_deactivation' || 
          //   approval.ExtractedData?.RequestType === 'Change Status to Inactive' ||
          //   (approval.Identifier && approval.Identifier.includes('COMP-DEACTIVATE'))
          // );
          
          // console.log(`🔍 Found ${deactivationRequests.length} deactivation requests in the response:`, deactivationRequests);
          
          // Ensure ExtractedData is properly formatted
          this.approvals = (approvalsResponse.data.data || []).map(approval => ({
            ...approval,
            ExtractedData: {
              ...approval.ExtractedData,
              type: approval.ExtractedData?.type || 'compliance',
              compliance_approval: approval.ExtractedData?.compliance_approval || {
                approved: null,
                remarks: ''
              }
            }
          }));
          
          // Debug log to check approval status and identify recently changed items
          // console.log("📋 Refreshed approvals data - checking status:");
          // this.approvals.forEach((approval, index) => {
          //   const approvalStatus = this.getApprovalStatus(approval);
          //   console.log(`Approval ${index}:`, {
          //     ApprovalId: approval.ApprovalId,
          //     Identifier: approval.Identifier,
          //     ApprovedNot: approval.ApprovedNot,
          //     ComplianceApprovalStatus: approval.ExtractedData?.compliance_approval?.approved,
          //     CalculatedStatus: approvalStatus,
          //     Impact: approval.ExtractedData.Impact,
          //     Probability: approval.ExtractedData.Probability,
          //     LastUpdated: approval.UpdatedAt || 'N/A'
          //   });
          // });
          
          this.counts = approvalsResponse.data.counts || {
            pending: 0,
            approved: 0,
            rejected: 0
          };
          
          // Enhanced logging for approved compliances
          // const approvedItems = this.approvals.filter(a => this.getApprovalStatus(a).approved === true);
          // const pendingItems = this.approvals.filter(a => this.getApprovalStatus(a).approved === null);
          // const rejectedItems = this.approvals.filter(a => this.getApprovalStatus(a).approved === false);
          
          // console.log(`✅ Found ${approvedItems.length} approved compliances`);
          // console.log(`⏳ Found ${pendingItems.length} pending compliances`);
          // console.log(`❌ Found ${rejectedItems.length} rejected compliances`);
          
          // Force Vue reactivity update
          this.$nextTick(() => {
            // console.log('🔄 Forcing Vue component re-render after data refresh');
            this.$forceUpdate();
          });
          
        } else {
          throw new Error(approvalsResponse.data.message || 'Failed to fetch approvals');
        }
        
        // Load rejected compliances
        await this.loadRejectedCompliances();
        
        // Load user tasks to sync the new task-based system
        await this.loadUserTasks();
        
        // Update pagination counts after loading data
        this.updatePaginationCounts();
        
        // console.log('✅ Data refresh completed successfully');
        
      } catch (error) {
        // Check if it's an access control error
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showApproveComplianceDenied();
          return;
        }
        
        console.error('❌ Error refreshing data:', error);
        this.error = error.response?.data?.message || error.message || 'Failed to load approvals';
      } finally {
        this.isLoading = false;
      }
    },
   
    openApprovalDetails(approval) {
      // console.log('Opening approval details:', approval);
      this.selectedApproval = approval;
      this.showDetailsModal = true;
    },
   

   

    
    async processApproval(isApproved, remarks = '') {
      try {
        if (!this.selectedApproval) {
          return;
        }
        
        // Prevent multiple simultaneous calls
        if (this.isSubmitting) {
          console.log('Approval process already in progress, ignoring duplicate call');
          return;
        }
        
        this.isSubmitting = true;
        
        let approvalId = this.selectedApproval.ApprovalId;
        
        // Handle different approval types
        if (this.selectedApproval.ExtractedData?.type === 'compliance_deactivation' ||
            this.selectedApproval.ExtractedData?.RequestType === 'Change Status to Inactive') {
          
          // Deactivation approval/rejection
          if (isApproved) {
                    await complianceService.approveComplianceDeactivation(
          approvalId,
          { user_id: this.currentUserId }
        );
          } else {
                      await complianceService.rejectComplianceDeactivation(
            approvalId,
            { 
              user_id: this.currentUserId,
              remarks: remarks
            }
          );
          }
        } else {
          // Regular compliance approval
          
          // Extract data from selected approval
          let extractedData = this.selectedApproval.ExtractedData;
          
          // Update approval status in the extracted data
          if (!extractedData.compliance_approval) {
            extractedData.compliance_approval = {};
          }
          
          extractedData.compliance_approval.approved = isApproved;
          extractedData.compliance_approval.remarks = remarks;
          
          await complianceService.submitComplianceReview(
            approvalId,
            {
              ExtractedData: extractedData,
              ApprovedNot: isApproved,
              user_id: this.currentUserId
            }
          );
        }
        
        // Show success popup
        CompliancePopups.reviewSubmitted(isApproved);
        
        // Update local approval status
        this.approvalStatus = {
          approved: isApproved,
          remarks: remarks
        };
        
        // Refresh the list
        this.refreshData();
      } catch (error) {
        console.error('Error submitting review:', error);
        // Show error popup
        this.showErrorPopup(`Error submitting review: ${error.message || 'Unknown error'}`);
      } finally {
        this.isSubmitting = false;
      }
    },
   
    async approveCompliance() {
      if (!this.selectedApproval) return;
      
      // Prevent multiple simultaneous calls
      if (this.isLoading || this.isSubmitting) {
        console.log('Approval already in progress, ignoring duplicate call');
        return;
      }
      
      // Check if the approval is in a pending state using the same logic as canPerformReviewActions
      // FIXED: Use the ApprovedNot field as the source of truth for approval status
      const isPending = this.selectedApproval.ApprovedNot === null || this.selectedApproval.ApprovedNot === undefined;
      const isApproved = this.selectedApproval.ApprovedNot === true;
      const complianceApproval = this.selectedApproval.ExtractedData?.compliance_approval || {};
      const isResubmitted = complianceApproval.inResubmission === true;
      
      // For resubmitted items, treat them as pending regardless of previous approval status
      const shouldAllowApproval = isPending || isResubmitted;
      
      // Prevent processing if already approved and not resubmitted
      if (isApproved && !isResubmitted) {
        console.log('Compliance already approved, ignoring duplicate call');
        this.showErrorPopup('This compliance has already been approved.', 'Already Approved');
        return;
      }
      
      // Prevent processing if not in pending state and not resubmitted
      if (!shouldAllowApproval) {
        console.log('Compliance not in pending state, ignoring call', {
          ApprovedNot: this.selectedApproval.ApprovedNot,
          compliance_approval_approved: complianceApproval.approved,
          isPending: isPending,
          isResubmitted: isResubmitted,
          shouldAllowApproval: shouldAllowApproval
        });
        this.showErrorPopup('This compliance is not in a pending state for approval.', 'Invalid State');
        return;
      }
     
      try {
        this.isLoading = true;
        this.isSubmitting = true;
        console.log("Starting approval process for compliance ID:", this.selectedApproval.ApprovalId);
       
        // Check if this is a deactivation request
        const isDeactivationRequest = 
          this.selectedApproval.ExtractedData?.type === 'compliance_deactivation' || 
          this.selectedApproval.ExtractedData?.RequestType === 'Change Status to Inactive' ||
          (this.selectedApproval.Identifier && this.selectedApproval.Identifier.includes('COMP-DEACTIVATE'));
        
        console.log(`This is ${isDeactivationRequest ? 'a' : 'not a'} deactivation request`);
        
        let response;
        
        if (isDeactivationRequest) {
          // This is a deactivation request
          console.log("Processing deactivation approval...");
          response = await complianceService.approveComplianceDeactivation(
            this.selectedApproval.ApprovalId,
            { user_id: this.currentUserId }
          );
          
          // Update the local data to reflect the compliance was deactivated
          if (this.selectedApproval.ExtractedData) {
            this.selectedApproval.ExtractedData.current_status = 'Inactive';
            if (this.selectedApproval.ExtractedData.compliance_approval) {
              this.selectedApproval.ExtractedData.compliance_approval.approved = true;
            }
          }
        } else {
          // This is a regular compliance approval
          // Initialize compliance approval if doesn't exist
          if (!this.selectedApproval.ExtractedData.compliance_approval) {
            this.selectedApproval.ExtractedData.compliance_approval = {};
          }
          this.selectedApproval.ExtractedData.compliance_approval.approved = true;
          this.selectedApproval.ExtractedData.compliance_approval.remarks = '';
          // Clear the resubmission flag since it's now approved
          this.selectedApproval.ExtractedData.compliance_approval.inResubmission = false;
          
          console.log('✅ Clearing resubmission flag on approval:', {
            ApprovalId: this.selectedApproval.ApprovalId,
            Identifier: this.selectedApproval.Identifier,
            inResubmission: this.selectedApproval.ExtractedData.compliance_approval.inResubmission
          });
         
          // Update the overall approval status
          this.selectedApproval.ApprovedNot = true;
         
          // Update status in ExtractedData - IMPORTANT for update after approval
          this.selectedApproval.ExtractedData.Status = 'Approved';
          this.selectedApproval.ExtractedData.ActiveInactive = 'Active';
         
          console.log('Approving compliance with data:', JSON.stringify(this.selectedApproval.ExtractedData));
          console.log('Resubmission status before approval:', this.selectedApproval.ExtractedData.compliance_approval.inResubmission);
         
          // Create a payload with just what's needed to reduce chance of network issues
          const reviewPayload = {
            ExtractedData: this.selectedApproval.ExtractedData,
            ApprovedNot: true,
            user_id: this.currentUserId
          };
          
          try {
            // First try with the full data
            console.log('Submitting compliance review with payload:', reviewPayload);
            console.log('Approval ID being updated:', this.selectedApproval.ApprovalId);
            response = await complianceService.submitComplianceReview(
              this.selectedApproval.ApprovalId,
              reviewPayload
            );
          } catch (apiError) {
            console.error('API call failed:', apiError);
            
            // If there's a network error, try with a simplified payload
            if (apiError.message === 'Network Error' || apiError.code === 'ERR_NETWORK') {
              console.log('Retrying with simplified payload due to network error');
              
              // Create a minimal payload for the retry
              const minimalPayload = {
                approved: true,
                remarks: '',
                user_id: this.currentUserId
              };
              
              response = await complianceService.submitComplianceReview(
                this.selectedApproval.ApprovalId, 
                minimalPayload
              );
            } else {
              // If it's not a network error, rethrow
              throw apiError;
            }
          }
        }
       
        console.log('Approval response:', response?.data);
       
        // Note: rejectedCompliances is now a computed property, so it updates automatically
        // when the underlying data changes
       
        // Replace alert with popup
        this.showSuccessPopup(
          isDeactivationRequest ? 
          'Compliance has been deactivated successfully!' : 
          'Compliance has been approved successfully!',
          isDeactivationRequest ? 'Deactivation Complete' : 'Approval Complete'
        );
          
        // Close modal after successful API call
        this.closeDetailsModal();
       
        // Force multiple refreshes to ensure we get the updated data
        // First immediate refresh
        await this.refreshData();
        
        // Second refresh after a delay to ensure backend has fully updated
        setTimeout(async () => {
          console.log('🔄 Performing delayed refresh to ensure status update');
          await this.refreshData();
          
          // Final refresh after another delay if needed
          setTimeout(async () => {
            console.log('🔄 Performing final refresh to verify status update');
            await this.refreshData();
          }, 2000);
        }, 1500);
              } catch (error) {
          console.error('Error approving compliance:', error);
          // Replace alert with popup
          this.showErrorPopup(
            'Error approving compliance: ' + (error.response?.data?.message || error.message || 'Network error - please check server connection'),
            'Approval Error'
          );
        } finally {
          this.isLoading = false;
          this.isSubmitting = false;
        }
    },
   
    rejectCompliance() {
      // console.log('=== REJECT COMPLIANCE CALLED ===');
      // console.log('Selected approval:', this.selectedApproval);
      // console.log('ApprovedNot field:', this.selectedApproval?.ApprovedNot);
      // console.log('Compliance approval:', this.selectedApproval?.ExtractedData?.compliance_approval);
      
      // Check if this is a deactivation request
      const isDeactivationRequest = 
        this.selectedApproval?.ExtractedData?.type === 'compliance_deactivation' || 
        this.selectedApproval?.ExtractedData?.RequestType === 'Change Status to Inactive' ||
        (this.selectedApproval?.Identifier && this.selectedApproval?.Identifier.includes('COMP-DEACTIVATE'));
      
      // Store the request type in the component data to use in confirmation
      this.isDeactivationRequest = isDeactivationRequest;
      
      // console.log('Is deactivation request:', isDeactivationRequest);
      // console.log('Showing reject modal...');
      
      this.showRejectModal = true;
    },
   
    async confirmRejection() {
      if (!this.rejectionComment.trim()) {
        alert('Please provide a reason for rejection');
        return;
      }
      
      // Prevent multiple simultaneous calls
      if (this.isLoading || this.isSubmitting) {
        console.log('Rejection already in progress, ignoring duplicate call');
        return;
      }
      
      // Check if the approval is in a pending state using the same logic as canPerformReviewActions
      // FIXED: Use the ApprovedNot field as the source of truth for approval status
      const isPending = this.selectedApproval.ApprovedNot === null || this.selectedApproval.ApprovedNot === undefined;
      const isRejected = this.selectedApproval.ApprovedNot === false;
      const complianceApproval = this.selectedApproval.ExtractedData?.compliance_approval || {};
      const isResubmitted = complianceApproval.inResubmission === true;
      
      // For resubmitted items, treat them as pending regardless of previous rejection status
      const shouldAllowRejection = isPending || isResubmitted;
      
      // Prevent processing if already rejected and not resubmitted
      if (isRejected && !isResubmitted) {
        console.log('Compliance already rejected, ignoring duplicate call');
        this.showErrorPopup('This compliance has already been rejected.', 'Already Rejected');
        return;
      }
      
      // Prevent processing if not in pending state and not resubmitted
      if (!shouldAllowRejection) {
        console.log('Compliance not in pending state, ignoring call', {
          ApprovedNot: this.selectedApproval.ApprovedNot,
          compliance_approval_approved: complianceApproval.approved,
          isPending: isPending,
          isResubmitted: isResubmitted,
          shouldAllowRejection: shouldAllowRejection
        });
        this.showErrorPopup('This compliance is not in a pending state for rejection.', 'Invalid State');
        return;
      }
     
      try {
        this.isLoading = true;
        this.isSubmitting = true;
        console.log("Starting rejection process for compliance ID:", this.selectedApproval.ApprovalId);
        
        let response;
        
        // Check if this is a deactivation request based on stored value
        if (this.isDeactivationRequest) {
          // This is a deactivation request rejection
          console.log("Processing deactivation rejection...");
          response = await complianceService.rejectComplianceDeactivation(
            this.selectedApproval.ApprovalId,
            { 
              user_id: this.currentUserId,
              remarks: this.rejectionComment
            }
          );
          
          // Update the local data to reflect the deactivation was rejected
          if (this.selectedApproval.ExtractedData) {
            // Ensure compliance status remains Active in the local data
            this.selectedApproval.ExtractedData.current_status = 'Active';
            if (!this.selectedApproval.ExtractedData.compliance_approval) {
              this.selectedApproval.ExtractedData.compliance_approval = {};
            }
            this.selectedApproval.ExtractedData.compliance_approval.approved = false;
            this.selectedApproval.ExtractedData.compliance_approval.remarks = this.rejectionComment;
          }
        } else {
          // This is a regular compliance rejection
          // Initialize compliance approval object if it doesn't exist
          if (!this.selectedApproval.ExtractedData.compliance_approval) {
            this.selectedApproval.ExtractedData.compliance_approval = {};
          }
          // Set the approval status to rejected and add remarks
          this.selectedApproval.ExtractedData.compliance_approval.approved = false;
          this.selectedApproval.ExtractedData.compliance_approval.remarks = this.rejectionComment;
          // Clear the resubmission flag since it's now rejected (user can resubmit again)
          this.selectedApproval.ExtractedData.compliance_approval.inResubmission = false;
          
          console.log('❌ Clearing resubmission flag on rejection:', {
            ApprovalId: this.selectedApproval.ApprovalId,
            Identifier: this.selectedApproval.Identifier,
            inResubmission: this.selectedApproval.ExtractedData.compliance_approval.inResubmission,
            rejectionComment: this.rejectionComment
          });
          this.selectedApproval.ApprovedNot = false;
          // Update status in ExtractedData - IMPORTANT for update after rejection
          this.selectedApproval.ExtractedData.Status = 'Rejected';
          this.selectedApproval.ExtractedData.ActiveInactive = 'Inactive';
          // --- Ensure remarks are included in the payload sent to backend ---
          const payload = {
            ExtractedData: {
              ...this.selectedApproval.ExtractedData,
              compliance_approval: {
                ...this.selectedApproval.ExtractedData.compliance_approval,
                remarks: this.rejectionComment,
                approved: false
              }
            },
            ApprovedNot: false,
            user_id: this.currentUserId
          };
          // Submit the review with the updated data
          console.log('Submitting compliance rejection with payload:', payload);
          console.log('Resubmission status before rejection:', this.selectedApproval.ExtractedData.compliance_approval.inResubmission);
          console.log('Approval ID being updated:', this.selectedApproval.ApprovalId);
          response = await complianceService.submitComplianceReview(
            this.selectedApproval.ApprovalId,
            payload
          );
        }
        
        console.log('Rejection response:', response.data);
        
        // Replace alert with popup
        this.showSuccessPopup(
          this.isDeactivationRequest ? 
          'Deactivation request has been rejected successfully!' : 
          'Compliance rejected and sent back to user for revision!',
          'Compliance Rejected'
        );
          
        // Close modals after successful API call
        this.showRejectModal = false;
        this.rejectionComment = '';
        this.closeDetailsModal();
        
        // Force multiple refreshes to ensure we get the updated data
        // First immediate refresh
        await this.refreshData();
        
        // Second refresh after a delay to ensure backend has fully updated
        setTimeout(async () => {
          console.log('🔄 Performing delayed refresh to ensure rejection status update');
          await this.refreshData();
          
          // Final refresh after another delay if needed
          setTimeout(async () => {
            console.log('🔄 Performing final refresh to verify rejection status update');
            await this.refreshData();
          }, 2000);
        }, 1500);
              } catch (error) {
          console.error('Error rejecting compliance:', error);
          // Replace alert with popup
          this.showErrorPopup(
            'Error rejecting compliance: ' + (error.response?.data?.message || error.message),
            'Rejection Error'
          );
        } finally {
          this.isLoading = false;
          this.isSubmitting = false;
        }
    },
   
    cancelRejection() {
      this.showRejectModal = false;
      this.rejectionComment = '';
    },
   
    openRejectedItem(item) {
      console.log('Opening rejected item:', item);
      this.editingCompliance = JSON.parse(JSON.stringify(item));
      
      // Store the original data for change detection
      this.originalComplianceData = JSON.parse(JSON.stringify(item.ExtractedData || {}));
      this.showEditComplianceModal = true;
      
      // Ensure Impact and Probability fields are preserved
      if (this.editingCompliance.ExtractedData) {
        // If Impact is missing, try to get it from other possible field names
        if (!this.editingCompliance.ExtractedData.Impact) {
          this.editingCompliance.ExtractedData.Impact = 
            this.editingCompliance.ExtractedData.impact ||
            this.editingCompliance.ExtractedData.SeverityRating ||
            this.editingCompliance.ExtractedData.severity_rating ||
            this.editingCompliance.ExtractedData.Severity ||
            'Medium'; // Default value instead of empty string
        }
        
        // If Probability is missing, try to get it from other possible field names
        if (!this.editingCompliance.ExtractedData.Probability) {
          this.editingCompliance.ExtractedData.Probability = 
            this.editingCompliance.ExtractedData.probability ||
            this.editingCompliance.ExtractedData.Likelihood ||
            this.editingCompliance.ExtractedData.likelihood ||
            'Medium'; // Default value instead of empty string
        }
        
        // Ensure these fields are always present in the ExtractedData object
        if (!('Impact' in this.editingCompliance.ExtractedData)) {
          this.editingCompliance.ExtractedData.Impact = 'Medium';
        }
        if (!('Probability' in this.editingCompliance.ExtractedData)) {
          this.editingCompliance.ExtractedData.Probability = 'Medium';
        }
      }
      
      // Log details for debugging
      console.log('Opened rejected item in edit modal:', {
        ApprovalId: this.editingCompliance.ApprovalId,
        Identifier: this.editingCompliance.Identifier,
        ApprovedNot: this.editingCompliance.ApprovedNot,
        remarks: this.editingCompliance.ExtractedData?.compliance_approval?.remarks,
        Impact: this.editingCompliance.ExtractedData?.Impact,
        Probability: this.editingCompliance.ExtractedData?.Probability,
        ExtractedDataKeys: Object.keys(this.editingCompliance.ExtractedData || {})
      });
    },
   
    closeEditComplianceModal() {
      this.showEditComplianceModal = false;
      this.editingCompliance = null;
      this.originalComplianceData = null; // Clear original data
    },
   
    async resubmitCompliance(compliance) {
      try {
        // Check if any changes were made to the compliance
        const hasChanges = this.checkComplianceChanges();
        if (!hasChanges) {
          // Don't show popup since we have inline warning now
          return;
        }
        
        // Reset approval status for resubmission
        if (compliance.ExtractedData.compliance_approval) {
          compliance.ExtractedData.compliance_approval.approved = null;
          compliance.ExtractedData.compliance_approval.remarks = '';
          // Mark as being resubmitted to prevent showing in the rejected list and show in pending
          compliance.ExtractedData.compliance_approval.inResubmission = true;
        } else {
          compliance.ExtractedData.compliance_approval = {
            approved: null,
            remarks: '',
            inResubmission: true
          };
        }
        
        // FIXED: Keep ApprovedNot as false so creator can still see it in rejected list
        // The inResubmission flag will make it appear in reviewer's pending tasks
        // compliance.ApprovedNot = null; // DON'T reset this - keep it as false
        console.log('🔄 Keeping ApprovedNot as false for creator visibility, using inResubmission flag for reviewer pending');
        
        // Also update status fields to reflect pending state
        compliance.ExtractedData.Status = 'Pending Review';
        compliance.ExtractedData.ActiveInactive = 'Pending';
        
        console.log('🔄 Resubmission status set:', {
          ApprovalId: compliance.ApprovalId,
          Identifier: compliance.Identifier,
          ApprovedNot: compliance.ApprovedNot,
          inResubmission: compliance.ExtractedData.compliance_approval.inResubmission,
          Status: compliance.ExtractedData.Status
        });
        
        console.log('📋 After resubmission setup, this compliance should:');
        console.log('  ✅ Remain visible in creator\'s rejected list (for further edits)');
        console.log('  ✅ Appear in reviewer\'s pending tasks (due to inResubmission flag)');
        console.log('  ✅ Show resubmission indicator in modal');
        console.log('  ✅ Show [RESUBMITTED] badge in reviewer\'s pending table');
        
        // Also clear any old rejection remarks fields for consistency
        if (compliance.ExtractedData.rejection_remarks) {
          delete compliance.ExtractedData.rejection_remarks;
        }
       
        this.isLoading = true;
        console.log("Resubmitting compliance with ID:", compliance.ApprovalId);
        console.log("Resubmitting with data:", JSON.stringify(compliance.ExtractedData));
        console.log("Impact field before resubmission:", compliance.ExtractedData.Impact);
        console.log("Probability field before resubmission:", compliance.ExtractedData.Probability);
        
        // Ensure Impact and Probability fields are preserved in the data being sent
        if (!compliance.ExtractedData.Impact && compliance.ExtractedData.impact) {
          compliance.ExtractedData.Impact = compliance.ExtractedData.impact;
        }
        if (!compliance.ExtractedData.Probability && compliance.ExtractedData.probability) {
          compliance.ExtractedData.Probability = compliance.ExtractedData.probability;
        }
        
        // Validate that required fields are present
        if (!compliance.ExtractedData.Impact) {
          console.warn("Impact field is missing! Adding default value.");
          compliance.ExtractedData.Impact = "Medium"; // Default value
        }
        if (!compliance.ExtractedData.Probability) {
          console.warn("Probability field is missing! Adding default value.");
          compliance.ExtractedData.Probability = "Medium"; // Default value
        }
        
        // Log the final data being sent
        console.log("Final data being sent to backend:", {
          Impact: compliance.ExtractedData.Impact,
          Probability: compliance.ExtractedData.Probability,
          AllFields: Object.keys(compliance.ExtractedData),
          compliance_approval: compliance.ExtractedData.compliance_approval
        });
        
        const resubmissionPayload = { 
          ExtractedData: compliance.ExtractedData,
          ApprovedNot: null, // Explicitly set to null to mark as pending
          user_id: this.currentUserId
        };
        
        console.log("Resubmission payload:", resubmissionPayload);
        
        // Use Promise.race to add a timeout and ensure UI updates quickly
        const apiCall = complianceService.resubmitComplianceApproval(
          compliance.ApprovalId,
          resubmissionPayload
        );
        
        // Set a timeout to ensure UI doesn't hang
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Request timeout')), 30000)
        );
        
        const response = await Promise.race([apiCall, timeoutPromise]);
       
        console.log("Resubmission response:", response);
        
        if (response.data && (response.data.ApprovalId || response.data.success)) {
          // Use $nextTick to ensure Vue updates the DOM immediately
          await this.$nextTick();
          
          // Set loading to false immediately so button becomes enabled
          this.isLoading = false;
          
          // Force Vue to update the DOM
          this.$forceUpdate();
          
          // Show success message immediately
          this.showSuccessPopup('Compliance resubmitted for review! Reviewer will be notified.', 'Compliance Resubmitted');
          
          // Close modal immediately for better UX
          this.showEditComplianceModal = false;
          this.editingCompliance = null;
          
          // Show more details about what happened
          console.log(`Resubmitted compliance with ID ${compliance.ApprovalId}. New version: ${response.data.Version}`);
          console.log('Response data:', response.data);
          
          // Refresh data in the background (non-blocking) - don't await
          // Use setTimeout to ensure it runs after UI updates
          setTimeout(() => {
            this.refreshData().catch(error => {
              console.error('Error refreshing data after resubmission:', error);
              // Don't show error to user since resubmission was successful
            });
          }, 100);
        } else {
          throw new Error('Failed to get confirmation from server');
        }
      } catch (error) {
        console.error('Error resubmitting compliance:', error);
        this.showErrorPopup('Error resubmitting compliance: ' + (error.response?.data?.message || error.message), 'Resubmission Error');
        this.isLoading = false;
      }
    },
   
    formatDate(dateString) {
      if (!dateString) return '';
      
      try {
        // Handle different date formats
        let date;
        if (typeof dateString === 'string') {
          // Try different date formats
          if (dateString.includes('T')) {
            // ISO format
            date = new Date(dateString);
          } else if (dateString.includes('-')) {
            // YYYY-MM-DD format
            const parts = dateString.split(' ')[0].split('-');
            date = new Date(parts[0], parts[1] - 1, parts[2]);
          } else if (dateString.includes('/')) {
            // MM/DD/YYYY format
            const parts = dateString.split(' ')[0].split('/');
            date = new Date(parts[2], parts[0] - 1, parts[1]);
          } else {
            date = new Date(dateString);
          }
        } else {
          date = new Date(dateString);
        }
        
        // Format the date
        return date.toLocaleString();
      } catch (e) {
        console.error('Error formatting date:', e);
        return dateString; // Return the original string if parsing fails
      }
    },
    async checkForApprovedIdentifiers() {
      // Note: rejectedCompliances is now a computed property, so it updates automatically
      // when the underlying data changes. No need to manually filter.
      console.log('Rejected compliances computed automatically:', this.rejectedCompliances);
    },
    isCompliantIdentifierApproved(identifier) {
      // Check if any approval with this identifier exists and is approved
      return this.approvals.some(approval => 
        approval.Identifier === identifier && approval.ApprovedNot === true
      );
    },
    // Load rejected compliances
    async loadRejectedCompliances() {
      try {
        this.isLoadingRejected = true;
        
        // Ensure users are available for name mapping
        await this.ensureUsersAvailable();
        
        // The rejectedCompliances computed property now handles this automatically
        // No need to manually populate the array since it's computed from myTasksRejected and reviewerTasksRejected
        console.log('Rejected compliances computed automatically:', this.rejectedCompliances);
      } catch (error) {
        console.error('Error loading rejected compliances:', error);
      } finally {
        this.isLoadingRejected = false;
        // Update pagination counts after loading rejected compliances
        this.updatePaginationCounts();
      }
    },
    mapApprovalToRow(approval) {
      // Enhanced mapping to handle different data structures for compliance versioning
      const extractedData = approval.ExtractedData || {};
      const complianceApproval = extractedData.compliance_approval || {};
      const isResubmitted = complianceApproval.inResubmission === true;
      
      // Helper function to get value from multiple possible locations
      const getValue = (primaryKey, fallbackKeys = [], defaultValue = 'N/A') => {
        // Try primary key first
        if (extractedData[primaryKey]) {
          return extractedData[primaryKey];
        }
        
        // Try fallback keys
        for (const key of fallbackKeys) {
          if (extractedData[key]) {
            return extractedData[key];
          }
        }
        
        // Try direct approval properties
        if (approval[primaryKey]) {
          return approval[primaryKey];
        }
        
        return defaultValue;
      };

      const result = {
        ...approval,
        // Add resubmission flag for visual indicators
        isResubmitted: isResubmitted,
        // Enhanced Identifier extraction
        Identifier: (() => {
          // Try to get from approval.Identifier first (direct property)
          if (approval.Identifier && approval.Identifier !== 'N/A' && approval.Identifier !== 'null') {
            return approval.Identifier;
          }
          
          // Try to get from ExtractedData.Identifier
          if (extractedData.Identifier && extractedData.Identifier !== 'N/A' && extractedData.Identifier !== 'null') {
            return extractedData.Identifier;
          }
          
          // Try other possible identifier fields
          if (extractedData.identifier && extractedData.identifier !== 'N/A' && extractedData.identifier !== 'null') {
            return extractedData.identifier;
          }
          
          if (extractedData.ComplianceId && extractedData.ComplianceId !== 'N/A' && extractedData.ComplianceId !== 'null') {
            return extractedData.ComplianceId;
          }
          
          // Generate a fallback identifier using ApprovalId
          if (approval.ApprovalId) {
            return `COMP-${approval.ApprovalId}`;
          }
          
          return 'N/A';
        })(),
        
        // Enhanced Description extraction with resubmission indicator
        Description: (() => {
          const baseDescription = getValue('ComplianceItemDescription', [
            'reason', 
            'description', 
            'ComplianceTitle',
            'PolicyName',
            'FrameworkName'
          ], 'No Description');
          
          // Add resubmission badge to description if applicable
          if (isResubmitted) {
            return `${baseDescription} [RESUBMITTED]`;
          }
          
          return baseDescription;
        })(),
        
        // Enhanced Criticality extraction
        Criticality: getValue('Criticality', [
          'criticality',
          'Severity',
          'RiskLevel'
        ], 'N/A'),
        
        // Enhanced Impact/Severity Rating extraction
        Impact: getValue('Impact', [
          'impact',
          'SeverityRating',
          'severity_rating',
          'Severity'
        ], 'N/A'),
        
        // Enhanced Probability extraction
        Probability: getValue('Probability', [
          'probability',
          'Likelihood',
          'likelihood'
        ], 'N/A'),
        
        // Enhanced CreatedBy extraction - try multiple sources
        CreatedBy: (() => {
          // Try CreatedByName first (most reliable - should be set by backend)
          if (extractedData.CreatedByName && extractedData.CreatedByName !== 'System' && extractedData.CreatedByName !== 'Unknown User') {
            // If CreatedByName is a number, try to convert it to a name
            if (!isNaN(extractedData.CreatedByName) && extractedData.CreatedByName !== '') {
              const userName = this.getUserNameById(extractedData.CreatedByName);
              if (userName && userName !== 'Unknown') {
                return userName;
              }
            }
            // Return the CreatedByName as is (should be a name string from backend)
            return extractedData.CreatedByName;
          }
          
          // Try to get from UserId using the helper method (fallback)
          if (approval.UserId) {
            const userName = this.getUserNameById(approval.UserId);
            if (userName && userName !== 'Unknown') {
              return userName;
            }
          }
          
          // Try other possible creator fields
          if (extractedData.CreatedBy && extractedData.CreatedBy !== 'System') {
            // If it's a number, try to find the user name
            if (!isNaN(extractedData.CreatedBy) && extractedData.CreatedBy !== '') {
              const userName = this.getUserNameById(extractedData.CreatedBy);
              if (userName && userName !== 'Unknown') {
                return userName;
              }
            }
            // If it's not a number, return as is
            return extractedData.CreatedBy;
          }
          
          if (extractedData.createdBy && extractedData.createdBy !== 'System') {
            return extractedData.createdBy;
          }
          
          if (extractedData.creator && extractedData.creator !== 'System') {
            return extractedData.creator;
          }
          
          // Last resort: Try ReviewerId (shouldn't normally be used for CreatedBy)
          if (approval.ReviewerId) {
            const userName = this.getUserNameById(approval.ReviewerId);
            if (userName && userName !== 'Unknown') {
              return userName;
            }
          }
          
          // If all else fails, return Unknown
          return 'Unknown User';
        })(),
        
        // Enhanced Version extraction
        Version: getValue('ComplianceVersion', [
          'version', 
          'Version',
          'PolicyVersion',
          'FrameworkVersion'
        ], '1.0'),
        
        actions: approval // Pass the whole object for the action button
      };
      
      // Debug log to show successful mapping
      if (result.Identifier !== 'N/A' && result.Criticality !== 'N/A' && result.CreatedBy !== 'System') {
        console.log('✅ Successfully mapped compliance data:', {
          Identifier: result.Identifier,
          Criticality: result.Criticality,
          Impact: result.Impact,
          Probability: result.Probability,
          CreatedBy: result.CreatedBy,
          Version: result.Version
        });
      } else {
        console.log('⚠️ Some fields could not be mapped properly:', {
          Identifier: result.Identifier,
          Criticality: result.Criticality,
          Impact: result.Impact,
          Probability: result.Probability,
          CreatedBy: result.CreatedBy,
          Version: result.Version,
          ExtractedDataKeys: Object.keys(extractedData)
        });
      }
      
      return result;
    },
    mapRejectedToRow(compliance) {
      // Enhanced mapping to handle different data structures for compliance versioning
      const extractedData = compliance.ExtractedData || {};
      
      // Helper function to get value from multiple possible locations
      const getValue = (primaryKey, fallbackKeys = [], defaultValue = 'N/A') => {
        // Try primary key first
        if (extractedData[primaryKey]) {
          return extractedData[primaryKey];
        }
        
        // Try fallback keys
        for (const key of fallbackKeys) {
          if (extractedData[key]) {
            return extractedData[key];
          }
        }
        
        // Try direct compliance properties
        if (compliance[primaryKey]) {
          return compliance[primaryKey];
        }
        
        return defaultValue;
      };

      return {
        ...compliance,
        // Enhanced Identifier extraction
        Identifier: (() => {
          // Try to get from compliance.Identifier first (direct property)
          if (compliance.Identifier && compliance.Identifier !== 'N/A' && compliance.Identifier !== 'null') {
            return compliance.Identifier;
          }
          
          // Try to get from ExtractedData.Identifier
          if (extractedData.Identifier && extractedData.Identifier !== 'N/A' && extractedData.Identifier !== 'null') {
            return extractedData.Identifier;
          }
          
          // Try other possible identifier fields
          if (extractedData.identifier && extractedData.identifier !== 'N/A' && extractedData.identifier !== 'null') {
            return extractedData.identifier;
          }
          
          if (extractedData.ComplianceId && extractedData.ComplianceId !== 'N/A' && extractedData.ComplianceId !== 'null') {
            return extractedData.ComplianceId;
          }
          
          // Generate a fallback identifier using ApprovalId
          if (compliance.ApprovalId) {
            return `COMP-${compliance.ApprovalId}`;
          }
          
          return 'N/A';
        })(),
        
        // Enhanced Description extraction
        Description: getValue('ComplianceItemDescription', [
          'reason', 
          'description', 
          'ComplianceTitle',
          'PolicyName',
          'FrameworkName'
        ], 'No Description'),
        
        // Enhanced Criticality extraction
        Criticality: getValue('Criticality', [
          'criticality',
          'Severity',
          'RiskLevel'
        ], 'N/A'),
        
        // Enhanced Impact/Severity Rating extraction
        Impact: getValue('Impact', [
          'impact',
          'SeverityRating',
          'severity_rating',
          'Severity'
        ], 'N/A'),
        
        // Enhanced Probability extraction
        Probability: getValue('Probability', [
          'probability',
          'Likelihood',
          'likelihood'
        ], 'N/A'),
        
        // Enhanced CreatedBy extraction - try multiple sources
        CreatedBy: (() => {
          // Try CreatedByName first (most reliable)
          if (extractedData.CreatedByName && extractedData.CreatedByName !== 'System') {
            return extractedData.CreatedByName;
          }
          
          // Try to get from UserId using the helper method
          if (compliance.UserId) {
            return this.getUserNameById(compliance.UserId);
          }
          
          // Try other possible creator fields
          if (extractedData.CreatedBy && extractedData.CreatedBy !== 'System') {
            // If it's a number, try to find the user name
            if (!isNaN(extractedData.CreatedBy)) {
              return this.getUserNameById(extractedData.CreatedBy);
            }
            // If it's not a number, return as is
            return extractedData.CreatedBy;
          }
          
          if (extractedData.createdBy && extractedData.createdBy !== 'System') {
            return extractedData.createdBy;
          }
          
          if (extractedData.creator && extractedData.creator !== 'System') {
            return extractedData.creator;
          }
          
          // Try to get from ReviewerId if we have user information
          if (compliance.ReviewerId) {
            return this.getUserNameById(compliance.ReviewerId);
          }
          
          // Debug logging for CreatedBy mapping
          console.log('CreatedBy mapping failed for rejected compliance:', {
            approvalId: compliance.ApprovalId,
            userId: compliance.UserId,
            reviewerId: compliance.ReviewerId,
            createdByName: extractedData.CreatedByName,
            createdBy: extractedData.CreatedBy,
            availableUsersCount: this.availableUsers.length
          });
          
          return 'System';
        })(),
        
        // Enhanced Version extraction
        Version: getValue('ComplianceVersion', [
          'version', 
          'Version',
          'PolicyVersion',
          'FrameworkVersion'
        ], '1.0'),
        
        actions: compliance // Pass the whole object for the action button
      };
    },
    handleApprovalAction(approval) {
      console.log('=== OPENING COMPLIANCE DETAILS ===');
      console.log('Approval data:', approval);
      
      // Get compliance information
      const complianceId = this.getComplianceId(approval);
      
      // Store the compliance data in sessionStorage for the ComplianceDetails page
      sessionStorage.setItem('complianceData', JSON.stringify(approval));
      
      // Navigate to ComplianceDetails page
      this.$router.push({
        name: 'ComplianceDetails',
        params: { complianceId: complianceId }
      });
    },
    handleEditTask(task) {
      console.log('=== EDIT TASK CLICKED ===');
      console.log('Task data:', task);
      
      // Find the original item from the rejected compliances list
      const originalItem = this.rejectedCompliances.find(c => c.ApprovalId === task.ApprovalId);
      
      if (originalItem) {
        this.openRejectedItem(originalItem);
      } else {
        console.error('Could not find original item for editing');
        this.showErrorPopup('Could not find the item to edit', 'Error');
      }
    },
    getImpactValue() {
      if (!this.selectedApproval || !this.selectedApproval.ExtractedData) return null;
      const impact = this.selectedApproval.ExtractedData.Impact;
      console.log('getImpactValue called, returning:', impact);
      return impact;
    },
    getProbabilityValue() {
      if (!this.selectedApproval || !this.selectedApproval.ExtractedData) return null;
      const probability = this.selectedApproval.ExtractedData.Probability;
      console.log('getProbabilityValue called, returning:', probability);
      return probability;
    },
    logFieldChange(fieldName, value) {
      console.log(`Field ${fieldName} changed to:`, value);
      console.log(`Current editingCompliance.ExtractedData.${fieldName}:`, this.editingCompliance.ExtractedData[fieldName]);
    },
    validateAndResubmit(compliance) {
      console.log("Validating compliance before resubmission...");
      console.log("Current ExtractedData:", compliance.ExtractedData);
      
      // Ensure Impact and Probability fields are present
      if (!compliance.ExtractedData.Impact) {
        console.warn("Impact field is missing, setting default value");
        compliance.ExtractedData.Impact = "Medium";
      }
      if (!compliance.ExtractedData.Probability) {
        console.warn("Probability field is missing, setting default value");
        compliance.ExtractedData.Probability = "Medium";
      }
      
      // Log the final data that will be sent
      console.log("Validated data to be sent:", {
        Impact: compliance.ExtractedData.Impact,
        Probability: compliance.ExtractedData.Probability,
        AllFields: Object.keys(compliance.ExtractedData)
      });
      
      // Proceed with resubmission
      this.resubmitCompliance(compliance);
    },
    handleRejectedAction(compliance) {
      this.openRejectedItem(compliance);
    },
    toggleSection(section) {
      this.collapsibleStates = {
        ...this.collapsibleStates,
        [section]: !this.collapsibleStates[section]
      };
    },
    handlePaginationChange(section, newPagination) {
      console.log(`Pagination change for section "${section}":`, {
        old: this.pagination[section],
        new: newPagination
      });
      this.pagination[section] = newPagination;
      console.log(`Updated pagination for section "${section}":`, this.pagination[section]);
    },
    
    // Add pagination methods
    getPaginatedTasks(tasks, section) {
      const pagination = this.pagination[section];
      const startIndex = (pagination.currentPage - 1) * pagination.pageSize;
      const endIndex = startIndex + pagination.pageSize;
      return tasks.slice(startIndex, endIndex);
    },
    
    updatePaginationCounts() {
      // Update pagination counts for each section
      const pendingCount = this.complianceApprovals.length;
      const approvedCount = this.approvedComplianceItems.length;
      const rejectedCount = this.rejectedCompliances.length;
      
      // Ensure minimum count for testing pagination visibility
      this.pagination.Pending.totalCount = Math.max(pendingCount, 1);
      this.pagination.Approved.totalCount = Math.max(approvedCount, 1);
      this.pagination.Rejected.totalCount = Math.max(rejectedCount, 1);
      this.pagination['Recently Approved'].totalCount = Math.max(approvedCount, 1);
      
      console.log('Updated pagination counts:', {
        Pending: this.pagination.Pending.totalCount,
        Approved: this.pagination.Approved.totalCount,
        Rejected: this.pagination.Rejected.totalCount,
        'Recently Approved': this.pagination['Recently Approved'].totalCount
      });
      
      console.log('Current pagination state:', this.pagination);
    },
    
    resetPagination() {
      // Reset pagination to first page for all sections
      Object.keys(this.pagination).forEach(section => {
        this.pagination[section].currentPage = 1;
      });
    },
    
    // Test method to verify pagination is working
    testPagination() {
      console.log('Testing pagination...');
      console.log('Current pagination state:', this.pagination);
      console.log('Compliance approvals count:', this.complianceApprovals.length);
      console.log('Approved items count:', this.approvedComplianceItems.length);
      console.log('Rejected compliances count:', this.rejectedCompliances.length);
      
      // Force update pagination counts
      this.updatePaginationCounts();
    },
         closeDetailsModal() {
       this.showDetailsModal = false;
       this.selectedApproval = null;
     },
     
     // Check if any changes were made to the compliance
     checkComplianceChanges() {
       console.log('Checking for compliance changes...');
       
       // Always allow resubmission - any field can be changed
       // This removes the restrictive validation that was preventing resubmission
       console.log('Allowing resubmission - any field changes are permitted');
       
       return true; // Always return true to allow resubmission
     },
     

     
     handleKeydown(event) {
       if (event.key === 'Escape' && this.showDetailsModal) {
         this.closeDetailsModal();
       }
     },
     async initializeUser() {
      try {
        console.log('Initializing user...');
        
        // Get current user role
        const response = await axios.get(API_ENDPOINTS.USER_ROLE);
        console.log('User role response:', response.data);
        
        if (response.data.success) {
          this.currentUserId = response.data.user_id;
          this.currentUserName = response.data.username || response.data.user_name || '';
          
          console.log('User initialized:', {
            currentUserId: this.currentUserId,
            currentUserName: this.currentUserName
          });
          
          // Store username in localStorage for fallback
          if (this.currentUserName) {
            localStorage.setItem('user_name', this.currentUserName);
          }
          
          const userRole = response.data.role;
          this.isAdministrator = userRole === 'GRC Administrator';
          
          console.log('User role:', userRole, 'isAdministrator:', this.isAdministrator);
          
          // Always fetch users for mapping user IDs to names
          await this.fetchUsers();
          
          if (this.isAdministrator) {
            // Set default user to current logged-in administrator
            this.selectedUserId = this.currentUserId;
            console.log('Setting default user for administrator to current user:', this.currentUserName);
            await this.loadUserTasks();
          } else {
            this.selectedUserId = this.currentUserId;
            console.log('Regular user mode - selected user ID:', this.selectedUserId);
            await this.loadUserTasks();
          }
          
          // Refresh data after users are loaded to ensure proper mapping
          await this.refreshData();
        } else {
          throw new Error('Failed to get user role: ' + (response.data.message || 'Unknown error'));
        }
      } catch (error) {
        console.error('Error initializing user:', error);
        // Fallback for development/testing - use null to force proper user initialization
        console.log('Using fallback user data due to error...');
        this.currentUserId = null; // Don't set a default user ID
        this.currentUserName = 'Unknown User'; // Default username
        this.isAdministrator = false; // Default to non-administrator
        this.selectedUserId = null;
        
        console.log('Fallback user data set:', {
          currentUserId: this.currentUserId,
          currentUserName: this.currentUserName,
          isAdministrator: this.isAdministrator,
          selectedUserId: this.selectedUserId
        });
      }
    },
    async fetchUsers() {
      try {
        const response = await axios.get(API_ENDPOINTS.USERS_FOR_DROPDOWN);
        if (Array.isArray(response.data)) {
          this.availableUsers = response.data;
        } else if (response.data && response.data.success && Array.isArray(response.data.data)) {
          this.availableUsers = response.data.data;
        } else {
          this.availableUsers = response.data || [];
        }
        
        console.log('Fetched users for mapping:', this.availableUsers);
        console.log('Number of users available:', this.availableUsers.length);
      } catch (error) {
        console.error('Error fetching users:', error);
        this.availableUsers = [];
      }
    },
    
    // Method to ensure users are available for mapping
    async ensureUsersAvailable() {
      if (this.availableUsers.length === 0) {
        console.log('No users available, fetching users...');
        await this.fetchUsers();
      }
    },
    
    // Method to get user name by ID with fallbacks
    getUserNameById(userId) {
      console.log('getUserNameById called with userId:', userId);
      console.log('availableUsers length:', this.availableUsers.length);
      
      if (!userId) {
        console.log('No userId provided, returning Unknown');
        return 'Unknown';
      }
      
      // Try to get from availableUsers first
      if (this.availableUsers.length > 0) {
        console.log('Searching in availableUsers for userId:', userId);
        const user = this.availableUsers.find(u => u.UserId == userId);
        console.log('Found user:', user);
        if (user && user.UserName) {
          console.log('Returning userName:', user.UserName);
          return user.UserName;
        }
      } else {
        // If no users available, try to fetch them
        console.log('No users available, attempting to fetch users...');
        this.fetchUsers();
      }
      
      // Try to get from localStorage
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        try {
          const userData = JSON.parse(storedUser);
          if (userData.UserId == userId && userData.UserName) {
            console.log('Found user in localStorage:', userData.UserName);
            return userData.UserName;
          }
        } catch (e) {
          console.log('Error parsing localStorage user data:', e);
        }
      }
      
      // Try to get from sessionStorage
      const sessionUser = sessionStorage.getItem('user');
      if (sessionUser) {
        try {
          const userData = JSON.parse(sessionUser);
          if (userData.UserId == userId && userData.UserName) {
            console.log('Found user in sessionStorage:', userData.UserName);
            return userData.UserName;
          }
        } catch (e) {
          console.log('Error parsing sessionStorage user data:', e);
        }
      }
      
      // Hardcoded fallback mapping for common user IDs (only if no other source found)
      const hardcodedUsers = {
        '1': 'admin',
        '2': 'vikram.patel',
        '3': 'priya.gupta',
        '4': 'rahul.sharma',
        '5': 'neha.verma'
      };
      
      if (hardcodedUsers[userId.toString()]) {
        return hardcodedUsers[userId.toString()];
      }
      
      // Final fallback to formatted user ID
      return `User ${userId}`;
    },
    async onUserChange() {
      if (this.selectedUserId) {
        this.selectedUserInfo = this.availableUsers.find(u => u.UserId == this.selectedUserId);
        await this.loadUserTasks();
      } else {
        this.selectedUserInfo = null;
        this.myTasks = [];
        this.reviewerTasks = [];
      }
    },

    // Get selected user name for display
    getSelectedUserName() {
      if (!this.selectedUserId) return '';
      
      // If the selected user is the current administrator, return their name
      if (this.selectedUserId == this.currentUserId) {
        return this.currentUserName;
      }
      
      // Otherwise, find the user in the available users list
      const selectedUser = this.availableUsers.find(u => u.UserId == this.selectedUserId);
      return selectedUser ? selectedUser.UserName : `User ${this.selectedUserId}`;
    },
    switchTab(tab) {
      this.activeTab = tab;
    },
    async loadUserTasks() {
      const targetUserId = this.selectedUserId || this.currentUserId;
      if (this.isAdministrator && !this.selectedUserId) {
        this.myTasks = [];
        this.reviewerTasks = [];
        return;
      }
      await this.fetchMyTasks(targetUserId);
      await this.fetchReviewerTasks(targetUserId);
    },
    async fetchMyTasks(userId) {
      try {
        const params = {};
        // Only pass framework_id if a specific framework is selected
        // If "All Frameworks" is selected, don't pass it so backend uses session (which should be cleared)
        if (this.selectedFramework && this.selectedFramework !== '') {
          params.framework_id = this.selectedFramework;
          console.log('🔍 Adding framework filter to compliance my tasks:', this.selectedFramework);
        } else {
          console.log('ℹ️ No framework filter - fetching all frameworks data');
        }
        
        const response = await axios.get(API_ENDPOINTS.COMPLIANCE_APPROVALS_USER(userId), { params });
        if (Array.isArray(response.data)) {
          this.myTasks = response.data;
        } else if (response.data && Array.isArray(response.data.data)) {
          this.myTasks = response.data.data;
        } else if (response.data && Array.isArray(response.data.results)) {
          this.myTasks = response.data.results;
        } else {
          this.myTasks = [];
        }
      } catch (error) {
        this.myTasks = [];
      }
    },
    async fetchReviewerTasks(userId) {
      try {
        const params = {};
        // Only pass framework_id if a specific framework is selected
        // If "All Frameworks" is selected, don't pass it so backend uses session (which should be cleared)
        if (this.selectedFramework && this.selectedFramework !== '') {
          params.framework_id = this.selectedFramework;
          console.log('🔍 Adding framework filter to compliance reviewer tasks:', this.selectedFramework);
        } else {
          console.log('ℹ️ No framework filter - fetching all frameworks data');
        }
        
        console.log(`🔍 Fetching reviewer tasks for userId: ${userId}, framework filter: ${params.framework_id || 'none'}`);
        const response = await axios.get(API_ENDPOINTS.COMPLIANCE_APPROVALS_REVIEWER(userId), { params });
        
        let tasks = [];
        if (Array.isArray(response.data)) {
          tasks = response.data;
        } else if (response.data && Array.isArray(response.data.data)) {
          tasks = response.data.data;
        } else if (response.data && Array.isArray(response.data.results)) {
          tasks = response.data.results;
        }
        
        console.log(`✅ Received ${tasks.length} reviewer tasks for userId: ${userId}`);
        if (tasks.length > 0) {
          console.log(`📋 Sample reviewer task:`, {
            ApprovalId: tasks[0].ApprovalId,
            Identifier: tasks[0].Identifier,
            ReviewerId: tasks[0].ReviewerId,
            FrameworkId: tasks[0].FrameworkId || tasks[0].FrameworkId_id
          });
        }
        
        this.reviewerTasks = tasks;
      } catch (error) {
        console.error(`❌ Error fetching reviewer tasks for userId ${userId}:`, error);
        this.reviewerTasks = [];
      }
    },
    handleMyTasksPageChange(section, page) {
      this.myTasksPagination[section].currentPage = page;
    },
    handleReviewerTasksPageChange(section, page) {
      this.reviewerTasksPagination[section].currentPage = page;
    },
    formatMitigation(mitigation) {
      if (!mitigation) return '';
      if (typeof mitigation === 'string') return mitigation;
      if (typeof mitigation === 'object') {
        try {
          // If it's a simple object, join values; otherwise, pretty print
          if (Array.isArray(mitigation)) {
            return mitigation.join(', ');
          } else {
            // Join values if all are strings, else pretty print
            const values = Object.values(mitigation);
            if (values.every(v => typeof v === 'string')) {
              return values.join(', ');
            } else {
              return JSON.stringify(mitigation, null, 2);
            }
          }
        } catch (e) {
          return String(mitigation);
        }
      }
      return String(mitigation);
    },
    
    isTextTruncated(text) {
      if (!text) return false;
      return text.length > 50; // Keep for potential future use
    },
    getRejectionReason(item) {
      if (!item || !item.ExtractedData) return '';
      const ca = item.ExtractedData.compliance_approval || {};
      // Check multiple possible locations for rejection reason
      const reason = ca.remarks || 
             ca.rejection_reason || 
             ca.reason || 
             item.ExtractedData.rejection_remarks || 
             '';
      
      // Debug logging
      if (reason) {
        console.log(`Found rejection reason for ${item.Identifier}:`, {
          'compliance_approval.remarks': ca.remarks,
          'compliance_approval.rejection_reason': ca.rejection_reason,
          'compliance_approval.reason': ca.reason,
          'ExtractedData.rejection_remarks': item.ExtractedData.rejection_remarks,
          'final_reason': reason
        });
      }
      
      return reason;
    },
    
    // Helper method to determine the actual approval status
    getApprovalStatus(approval) {
      if (!approval) return { approved: null, remarks: '' };
      
      // Check both ApprovedNot field and ExtractedData.compliance_approval
      let approved = null;
      let remarks = '';
      
      // Priority 1: Check ApprovedNot field (most reliable for final status)
      if (approval.ApprovedNot !== null && approval.ApprovedNot !== undefined) {
        approved = approval.ApprovedNot;
      }
      
      // Priority 2: Check ExtractedData.compliance_approval
      if (approval.ExtractedData?.compliance_approval?.approved !== null && 
          approval.ExtractedData?.compliance_approval?.approved !== undefined) {
        // If ApprovedNot is null but compliance_approval has a status, use that
        if (approved === null) {
          approved = approval.ExtractedData.compliance_approval.approved;
        }
        remarks = approval.ExtractedData.compliance_approval.remarks || '';
      }
      
      // Check for resubmission status
      const isResubmitted = approval.ExtractedData?.compliance_approval?.inResubmission === true;
      
      return {
        approved: approved,
        remarks: remarks,
        isResubmitted: isResubmitted
      };
    },
         // Check if current user is the reviewer for this compliance
     isCurrentUserReviewer(approval) {
       if (!approval || !this.currentUserId) {
         console.log('isCurrentUserReviewer: Missing approval or currentUserId', { approval, currentUserId: this.currentUserId });
         return false;
       }
       
       console.log('Checking if current user is reviewer for compliance:', {
         approvalId: approval.ApprovalId,
         currentUserId: this.currentUserId,
         reviewerId: approval.ReviewerId,
         isAdministrator: this.isAdministrator
       });
       
       // For GRC Administrators, they can only review compliances specifically assigned to them
       if (this.isAdministrator) {
         // Check if they are specifically assigned as the reviewer for this compliance
         const reviewerId = approval.ReviewerId;
         if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
           console.log('GRC Administrator is specifically assigned as reviewer for this compliance');
           return true;
         }
         console.log('GRC Administrator is not assigned as reviewer for this compliance');
         return false;
       }
       
       // Check if current user is the reviewer for this compliance
       const reviewerId = approval.ReviewerId;
       
       console.log('Reviewer check details:', {
         reviewerId: reviewerId,
         currentUserId: this.currentUserId,
         approvalReviewerId: approval.ReviewerId
       });
       
       // Check by ID - this is the primary check
       if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
         console.log('Current user is the assigned reviewer');
         return true;
       }
       
       // Additional check: if the current user is viewing their own reviewer tasks,
       // and this approval appears in their reviewer tasks, they should be able to review it
       if (this.activeTab === 'reviewerTasks' && this.reviewerTasks.some(task => task.ApprovalId === approval.ApprovalId)) {
         console.log('Current user is viewing this approval in their reviewer tasks');
         return true;
       }
       
       // Check if the compliance was created by the current user (they shouldn't review their own compliances)
       if (this.isCurrentUserCreator(approval)) {
         console.log('Current user is the creator - not the reviewer');
         return false;
       }
       
       console.log('Current user is not the reviewer');
       return false;
     },

     // Check if current user can perform review actions (approve/reject)
     canPerformReviewActions(approval) {
       if (!approval || !this.currentUserId) {
         console.log('canPerformReviewActions: Missing approval or currentUserId', { approval, currentUserId: this.currentUserId });
         return false;
       }
       
       // Check if the approval is in a pending state
       // FIXED: Use the ApprovedNot field as the source of truth for approval status
       const isPending = approval.ApprovedNot === null || approval.ApprovedNot === undefined;
       const complianceApproval = approval.ExtractedData?.compliance_approval || {};
       const isResubmitted = complianceApproval.inResubmission === true;
       
       // For resubmitted items, treat them as pending regardless of previous status
       const shouldAllowActions = isPending || isResubmitted;
       
       console.log('canPerformReviewActions status check:', {
         approvalId: approval.ApprovalId,
         identifier: approval.Identifier,
         ApprovedNot: approval.ApprovedNot,
         isPending: isPending,
         isResubmitted: isResubmitted,
         shouldAllowActions: shouldAllowActions
       });
       
       if (!shouldAllowActions) {
         console.log('canPerformReviewActions: Approval is not in pending/resubmitted state', { 
           ApprovedNot: approval.ApprovedNot,
           compliance_approval_approved: complianceApproval.approved,
           isPending: isPending,
           isResubmitted: isResubmitted,
           shouldAllowActions: shouldAllowActions
         });
         return false;
       }
       
       // Check if current user is the reviewer
       const isReviewer = this.isCurrentUserReviewer(approval);
       
       // Check if current user is the creator (they shouldn't review their own compliances)
       const isCreator = this.isCurrentUserCreator(approval);
       
       console.log('canPerformReviewActions check:', {
         approvalId: approval.ApprovalId,
         currentUserId: this.currentUserId,
         isReviewer: isReviewer,
         isCreator: isCreator,
         canPerform: isReviewer && !isCreator,
         isPending: isPending,
         isResubmitted: isResubmitted
       });
       
       // Only allow review actions if the user is specifically assigned as the reviewer
       // AND is not the creator of the compliance
       return isReviewer && !isCreator;
     },

     // Check if current user is the creator of this compliance
     isCurrentUserCreator(approval) {
       if (!approval || !this.currentUserId) {
         console.log('isCurrentUserCreator: Missing approval or currentUserId', { approval, currentUserId: this.currentUserId });
         return false;
       }
       
       const createdBy = approval.ExtractedData?.CreatedByName;
       const createdById = approval.ExtractedData?.CreatedBy;
       const userId = approval.UserId;
       
       console.log('Creator check details:', {
         createdBy: createdBy,
         createdById: createdById,
         userId: userId,
         currentUserId: this.currentUserId,
         currentUserName: this.getCurrentUserName(),
         approvalData: approval.ExtractedData
       });
       
       // Check by ID first (most reliable)
       if (createdById && String(createdById) === String(this.currentUserId)) {
         console.log('Current user is creator (by ID)');
         return true;
       }
       
       // Check by UserId (from approval record)
       if (userId && String(userId) === String(this.currentUserId)) {
         console.log('Current user is creator (by UserId)');
         return true;
       }
       
       // Check by name (fallback)
       if (createdBy && String(createdBy) === String(this.getCurrentUserName())) {
         console.log('Current user is creator (by name)');
         return true;
       }
       
       console.log('Current user is not the creator');
       return false;
     },

     // Helper method to get current user name
     getCurrentUserName() {
       if (this.selectedUserId && this.availableUsers.length > 0) {
         const selectedUser = this.availableUsers.find(u => u.UserId === this.selectedUserId);
         return selectedUser ? selectedUser.UserName : '';
       }
       // For current user, use stored username or fallback to localStorage
       return this.currentUserName || localStorage.getItem('user_name') || '';
     },

     // Helper method to get compliance ID
     getComplianceId(compliance) {
       if (!compliance) return null;
       if (compliance.ComplianceId) {
         return typeof compliance.ComplianceId === 'object' ? compliance.ComplianceId.ComplianceId : compliance.ComplianceId;
       }
       return compliance.ApprovalId || compliance.Identifier;
     },
    createComplianceContentKey(item) {
      const extractedData = item.ExtractedData || {};
      
      // Create a key based on the most important compliance identifiers
      const identifier = (item.Identifier || extractedData.Identifier || extractedData.identifier || extractedData.ComplianceId || '').toString().trim().toLowerCase();
      const description = (extractedData.ComplianceItemDescription || extractedData.description || extractedData.reason || '').toString().trim().toLowerCase();
      const userId = (item.UserId || extractedData.CreatedBy || '').toString().trim();
      
      // If we have a meaningful identifier, use it as the primary key
      if (identifier && identifier !== 'n/a' && identifier !== 'null') {
        return `identifier_${identifier}`;
      }
      
      // If we have a meaningful description, use it as the key
      if (description && description !== 'no description' && description.length > 5) {
        return `description_${description.substring(0, 50)}`; // Limit length for key
      }
      
      // Fallback to user + approval date combination
      const createdDate = (extractedData.CreatedByDate || item.ApprovedDate || '').toString().trim();
      return `user_${userId}_date_${createdDate}`;
    },
    
    // Framework filtering methods
    async fetchFrameworks() {
      try {
        console.log('🔍 [ComplianceApprover] Checking for cached framework data...')
        
        // ==========================================
        // NEW: Ensure compliance prefetch is running
        // ==========================================
        if (!window.complianceDataFetchPromise && !complianceDataService.hasFrameworksCache()) {
          console.log('🚀 [ComplianceApprover] Starting compliance prefetch (user navigated directly)...')
          window.complianceDataFetchPromise = complianceDataService.fetchAllComplianceData()
        }

        if (window.complianceDataFetchPromise) {
          console.log('⏳ [ComplianceApprover] Waiting for compliance prefetch to complete...')
          try {
            await window.complianceDataFetchPromise
            console.log('✅ [ComplianceApprover] Prefetch completed')
          } catch (prefetchError) {
            console.warn('⚠️ [ComplianceApprover] Prefetch failed, will fetch directly from API', prefetchError)
          }
        }
        
        // FIRST: Try to get data from cache
        if (complianceDataService.hasFrameworksCache()) {
          console.log('✅ [ComplianceApprover] Using cached framework data')
          const cachedFrameworks = complianceDataService.getData('frameworks') || []
          
          // Transform the data to match frontend expectations (keep both formats for compatibility)
          this.frameworks = cachedFrameworks.map(framework => ({
            FrameworkId: framework.FrameworkId || framework.id,
            FrameworkName: framework.FrameworkName || framework.name,
            Category: framework.Category || framework.FrameworkCategory,
            ActiveInactive: framework.ActiveInactive,
            FrameworkDescription: framework.FrameworkDescription || framework.Description,
            // Also add id and name for consistency with Policy Approval
            id: framework.FrameworkId || framework.id,
            name: framework.FrameworkName || framework.name
          }))
          console.log(`[ComplianceApprover] Loaded ${this.frameworks.length} frameworks from cache (prefetched on Home page)`)
          console.log('📋 DEBUG: Framework IDs:', this.frameworks.map(f => f.FrameworkId))
        } else {
          // FALLBACK: Fetch from API if cache is empty
          console.log('⚠️ [ComplianceApprover] No cached data found, fetching from API...')
          const response = await axios.get(API_ENDPOINTS.FRAMEWORKS)
          console.log('📋 DEBUG: Raw frameworks response:', response.data)
          
          if (response.data) {
            // Transform the data to match frontend expectations (keep both formats for compatibility)
            this.frameworks = response.data.map(framework => ({
              FrameworkId: framework.FrameworkId || framework.id,
              FrameworkName: framework.FrameworkName || framework.name,
              Category: framework.Category,
              ActiveInactive: framework.ActiveInactive,
              FrameworkDescription: framework.FrameworkDescription,
              // Also add id and name for consistency with Policy Approval
              id: framework.FrameworkId || framework.id,
              name: framework.FrameworkName || framework.name
            }))
            console.log(`[ComplianceApprover] Loaded ${this.frameworks.length} frameworks directly from API (cache unavailable)`)
            console.log('📋 DEBUG: Framework IDs:', this.frameworks.map(f => f.FrameworkId))
            
            // Update cache so subsequent pages benefit
            complianceDataService.setData('frameworks', response.data)
            console.log('ℹ️ [ComplianceApprover] Cache updated after direct API fetch')
          }
        }
      } catch (err) {
        console.error('Error fetching frameworks:', err)
      }
    },
    
    async checkSelectedFrameworkFromSession() {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in ComplianceApprover...')
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
        console.log('📊 DEBUG: Selected framework response:', response.data)
        
        if (response.data && response.data.success) {
          // Check if a framework is selected (not null)
          if (response.data.frameworkId) {
            const frameworkIdFromSession = response.data.frameworkId
            console.log('✅ DEBUG: Found selected framework in session:', frameworkIdFromSession)
            
            // Store the session framework ID for filtering
            this.sessionFrameworkId = frameworkIdFromSession
            
            // Check if this framework exists in our loaded frameworks
            // Try both FrameworkId and id properties for compatibility
            const frameworkExists = this.frameworks.find(f => {
              const fwId = f.FrameworkId || f.id
              return fwId && fwId.toString() === frameworkIdFromSession.toString()
            })
            
            if (frameworkExists) {
              const frameworkId = frameworkExists.FrameworkId || frameworkExists.id
              const frameworkName = frameworkExists.FrameworkName || frameworkExists.name
              
              console.log('✅ DEBUG: Framework exists in loaded frameworks:', frameworkName)
              // Automatically select the framework from session
              this.selectedFramework = frameworkId.toString()
              console.log('✅ DEBUG: Auto-selected framework from session:', this.selectedFramework)
              console.log('✅ DEBUG: Framework name for display:', frameworkName)
              
              // Save to session to ensure it's properly set (in case it wasn't saved before)
              await this.saveFrameworkToSession(this.selectedFramework)
            } else {
              console.log('⚠️ DEBUG: Framework from session (ID:', frameworkIdFromSession, ') not found in loaded frameworks')
              console.log('📋 DEBUG: Available frameworks:', this.frameworks.map(f => ({ 
                FrameworkId: f.FrameworkId || f.id, 
                FrameworkName: f.FrameworkName || f.name 
              })))
              // Clear the session framework ID since it doesn't exist
              this.sessionFrameworkId = null
              this.selectedFramework = ''
            }
          } else {
            // "All Frameworks" is selected (frameworkId is null)
            console.log('ℹ️ DEBUG: No framework selected in session (All Frameworks selected)')
            console.log('🌐 DEBUG: Clearing framework selection to show all frameworks')
            this.sessionFrameworkId = null
            this.selectedFramework = ''
          }
        } else {
          console.log('ℹ️ DEBUG: No framework found in session - showing All Frameworks')
          this.sessionFrameworkId = null
          this.selectedFramework = ''
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework from session:', error)
        this.sessionFrameworkId = null
        this.selectedFramework = ''
      }
    },
    
    async saveFrameworkToSession(frameworkId) {
      try {
        console.log('💾 DEBUG: Saving framework to session:', frameworkId)
        const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
          frameworkId: frameworkId
        })
        console.log('💾 DEBUG: Save framework response:', response.data)
        
        if (response.data && response.data.success) {
          this.sessionFrameworkId = frameworkId
          console.log('✅ DEBUG: Framework saved to session successfully')
        } else {
          console.error('❌ DEBUG: Failed to save framework to session:', response.data)
        }
      } catch (error) {
        console.error('❌ DEBUG: Error saving framework to session:', error)
      }
    },
    
    async handleFrameworkChange() {
      console.log('🔄 Framework changed to:', this.selectedFramework)
      
      // Save the selected framework to session or clear it
      if (this.selectedFramework) {
        await this.saveFrameworkToSession(this.selectedFramework)
      } else {
        // Clear session if no framework selected (All Frameworks)
        console.log('🧹 Clearing framework from session (All Frameworks selected)')
        this.sessionFrameworkId = null
        try {
          await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
            frameworkId: null,
            userId: localStorage.getItem('user_id') || 'default_user'
          })
          console.log('✅ Framework cleared from session successfully')
        } catch (error) {
          console.error('❌ Error clearing framework from session:', error)
        }
      }
      
      // Reload tasks with the new framework filter
      await this.loadUserTasks()
    },
    
    async clearFilters() {
      console.log('🧹 Clearing all filters...')
      console.log('  Before clear - selectedFramework:', this.selectedFramework)
      console.log('  Before clear - sessionFrameworkId:', this.sessionFrameworkId)
      
      this.selectedFramework = ''
      this.sessionFrameworkId = null
      
      // Clear from session storage as well
      try {
        await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
          frameworkId: null
        })
        console.log('✅ Cleared framework from session successfully')
      } catch (error) {
        console.error('❌ Error clearing framework from session:', error)
      }
      
      console.log('  After clear - selectedFramework:', this.selectedFramework)
      console.log('  After clear - sessionFrameworkId:', this.sessionFrameworkId)
      console.log('✅ All filters cleared')
      
      // Reload tasks without framework filter
      await this.loadUserTasks()
      
      // Force Vue to re-render
      this.$forceUpdate()
    },
    
    // Debug method to check user ID consistency
    debugUserConsistency() {
      console.log('=== USER CONSISTENCY DEBUG ===');
      console.log('Current user data:', {
        currentUserId: this.currentUserId,
        currentUserName: this.currentUserName,
        selectedUserId: this.selectedUserId,
        isAdministrator: this.isAdministrator
      });
      
      console.log('Available users:', this.availableUsers);
      
      if (this.selectedUserId && this.availableUsers.length > 0) {
        const selectedUser = this.availableUsers.find(u => u.UserId == this.selectedUserId);
        console.log('Selected user info:', selectedUser);
      }
      
      console.log('My tasks count:', this.myTasks.length);
      console.log('Reviewer tasks count:', this.reviewerTasks.length);
      
      // Check if there are any tasks with mismatched reviewer IDs
      const myTasksWithReviewerMismatch = this.myTasks.filter(task => 
        task.ReviewerId && String(task.ReviewerId) !== String(this.currentUserId)
      );
      
      const reviewerTasksWithReviewerMismatch = this.reviewerTasks.filter(task => 
        task.ReviewerId && String(task.ReviewerId) !== String(this.currentUserId)
      );
      
      console.log('My tasks with reviewer mismatch:', myTasksWithReviewerMismatch.length);
      console.log('Reviewer tasks with reviewer mismatch:', reviewerTasksWithReviewerMismatch.length);
      
      if (myTasksWithReviewerMismatch.length > 0) {
        console.log('Sample my task with reviewer mismatch:', myTasksWithReviewerMismatch[0]);
      }
      
      if (reviewerTasksWithReviewerMismatch.length > 0) {
        console.log('Sample reviewer task with reviewer mismatch:', reviewerTasksWithReviewerMismatch[0]);
      }
      
      console.log('=== END USER CONSISTENCY DEBUG ===');
    },
  },
  computed: {
    // Framework filtering computed properties
    filteredFrameworks() {
      if (this.sessionFrameworkId) {
        // If there's a session framework ID, show only that framework
        // Check both FrameworkId and id properties for compatibility
        return this.frameworks.filter(fw => {
          const fwId = fw.FrameworkId || fw.id
          return fwId && fwId.toString() === this.sessionFrameworkId.toString()
        })
      }
      // If no session framework ID, show all frameworks
      return this.frameworks
    },
    
    pendingApprovalsCount() {
      // Calculate from actual task data (both myTasks and reviewerTasks)
      const myPending = this.myTasksPending?.length || 0;
      const reviewerPending = this.reviewerTasksPending?.length || 0;
      return myPending + reviewerPending;
    },
    approvedApprovalsCount() {
      // Calculate from actual task data (both myTasks and reviewerTasks)
      const myApproved = this.myTasksApproved?.length || 0;
      const reviewerApproved = this.reviewerTasksApproved?.length || 0;
      return myApproved + reviewerApproved;
    },
    rejectedApprovalsCount() {
      // Calculate from actual task data (both myTasks and reviewerTasks)
      const myRejected = this.myTasksRejected?.length || 0;
      const reviewerRejected = this.reviewerTasksRejected?.length || 0;
      return myRejected + reviewerRejected;
    },
    hasComplianceChanges() {
      if (!this.editingCompliance) return false;
      return this.checkComplianceChanges();
    },
    complianceApprovals() {
      // This computed property now shows only the latest version of each compliance item
      // regardless of its approval status (pending, approved, or rejected)
      // This ensures users see the most recent version sent by the user
      // console.log("Computing complianceApprovals from", this.approvals.length, "total approvals");
      
      // Debug all incoming approval data to verify deactivation requests
      // console.log("All approvals:");
      // this.approvals.forEach((approval, index) => {
      //   if (!approval) {
      //     console.log(`[${index}] Approval is null or undefined`);
      //     return;
      //   }
      //   
      //   console.log(`[${index}] ID: ${approval.ApprovalId}, Identifier: ${approval.Identifier}`);
      //   
      //   if (!approval.ExtractedData) {
      //     console.log(`    WARNING: ExtractedData is null or undefined`);
      //     return;
      //   }
      //   
      //   console.log(`    Type: ${approval.ExtractedData?.type}, RequestType: ${approval.ExtractedData?.RequestType}`);
      //   console.log(`    ApprovedNot: ${approval.ApprovedNot}`);
      //   
      //   // Check if this appears to be a deactivation request
      //   const isDeactivation = 
      //     approval.ExtractedData?.type === 'compliance_deactivation' || 
      //     approval.ExtractedData?.RequestType === 'Change Status to Inactive' ||
      //     (approval.Identifier && approval.Identifier.includes('COMP-DEACTIVATE'));
      //     
      //   console.log(`    Is deactivation request: ${isDeactivation}`);
      //   
      //   if (isDeactivation) {
      //     console.log(`    Deactivation request details:`, 
      //       JSON.stringify({
      //         reason: approval.ExtractedData?.reason,
      //         compliance_id: approval.ExtractedData?.compliance_id,
      //         current_status: approval.ExtractedData?.current_status,
      //         requested_status: approval.ExtractedData?.requested_status
      //       })
      //     );
      //   }
      // });
      
      // Apply the filter with detailed logging - show ALL compliance items (not just pending)
      const filtered = this.approvals.filter(approval => {
        // Skip null or undefined approvals
        if (!approval) {
          console.log(`Skipping null approval`);
          return false;
        }
        
        // Check if ExtractedData exists
        if (!approval.ExtractedData) {
          console.log(`Approval ${approval.ApprovalId || 'unknown'}: ExtractedData is missing`);
          return false;
        }
        
        // For each approval, check if it matches our criteria
        const isCompliance = 
          approval.ExtractedData?.type === 'compliance' ||
          approval.ExtractedData?.type === 'compliance_deactivation' ||
          (approval.Identifier && approval.Identifier.includes('COMP-DEACTIVATE'));
          
        // Show all compliance items regardless of status (pending, approved, rejected)
        const isPending = approval.ApprovedNot === null;
        const isApproved = approval.ApprovedNot === true;
        const isRejected = approval.ApprovedNot === false;
        
        // Framework filtering
        if (this.selectedFramework) {
          // Find framework name by ID for filtering
          const selectedFrameworkName = this.frameworks.find(f => f.FrameworkId.toString() === this.selectedFramework.toString())?.FrameworkName
          console.log('🔍 DEBUG: Selected framework name for filtering:', selectedFrameworkName)
          
          if (selectedFrameworkName) {
            // Check if this approval belongs to the selected framework
            const approvalFrameworkName = approval.ExtractedData?.FrameworkName
            const belongsToSelectedFramework = approvalFrameworkName === selectedFrameworkName
            
            console.log('🔍 DEBUG: Approval framework name:', approvalFrameworkName, 'matches selected:', belongsToSelectedFramework)
            
            if (!belongsToSelectedFramework) {
              console.log('🔍 DEBUG: Filtering out approval not belonging to selected framework')
              return false
            }
          } else {
            console.log('⚠️ DEBUG: Could not find framework name for ID:', this.selectedFramework)
          }
        } else {
          console.log('ℹ️ DEBUG: No framework selected, showing all compliance items')
        }
        
        // CRITICAL: Log the exact properties we're testing for
        if (approval.ExtractedData?.type === 'compliance_deactivation') {
          console.log(`Found deactivation by type: ${approval.Identifier}`);
        }
        
        if (approval.ExtractedData?.RequestType === 'Change Status to Inactive') {
          console.log(`Found deactivation by RequestType: ${approval.Identifier}`);
        }
        
        if (approval.Identifier && approval.Identifier.includes('COMP-DEACTIVATE')) {
          console.log(`Found deactivation by Identifier: ${approval.Identifier}`);
        }
        
        console.log(`Approval ${approval.ApprovalId}: isCompliance=${isCompliance}, status=${isPending ? 'pending' : isApproved ? 'approved' : isRejected ? 'rejected' : 'unknown'}`);
        
        return isCompliance; // Show all compliance items, not just pending ones
      });
      
      console.log(`Filtered to ${filtered.length} compliance approvals (all statuses)`);
      
      // CRITICAL: Remove duplicates and ensure only the most recent version is shown for each identifier
      const uniqueFiltered = [];
      const seenIdentifiers = new Set();
      
      // Sort by ApprovalId to get the most recent first
      const sortedFiltered = filtered.sort((a, b) => b.ApprovalId - a.ApprovalId);
      
      for (const approval of sortedFiltered) {
        if (!seenIdentifiers.has(approval.Identifier)) {
          seenIdentifiers.add(approval.Identifier);
          uniqueFiltered.push(approval);
          console.log(`Added latest version for ${approval.Identifier} (ApprovalId: ${approval.ApprovalId}, Status: ${approval.ApprovedNot === null ? 'pending' : approval.ApprovedNot === true ? 'approved' : 'rejected'})`);
        } else {
          console.log(`Skipping older version of ${approval.Identifier} (ApprovalId: ${approval.ApprovalId})`);
        }
      }
      
      console.log(`After removing duplicates: ${uniqueFiltered.length} unique latest compliance versions`);
      
      // If we have deactivation requests in the original data but none in the filtered list, log a warning
      const deactivationRequests = this.approvals.filter(approval => 
        approval?.ExtractedData?.type === 'compliance_deactivation' || 
        approval?.ExtractedData?.RequestType === 'Change Status to Inactive' ||
        (approval?.Identifier && approval?.Identifier.includes('COMP-DEACTIVATE'))
      );
      
      if (deactivationRequests.length > 0 && !uniqueFiltered.some(item => 
        item?.ExtractedData?.type === 'compliance_deactivation' || 
        item?.ExtractedData?.RequestType === 'Change Status to Inactive' ||
        (item?.Identifier && item?.Identifier.includes('COMP-DEACTIVATE'))
      )) {
        console.warn('WARNING: Deactivation requests exist but none passed the filter!');
        
        // Try to find out why they were filtered out
        deactivationRequests.forEach(request => {
          console.log(`Deactivation request ${request.ApprovalId} with ApprovedNot=${request.ApprovedNot}`);
          
          // Check if it was filtered out due to missing ExtractedData or other issues
          if (!request.ExtractedData) {
            console.log(`This request was filtered because ExtractedData is missing`);
          } else if (!request.Identifier) {
            console.log(`This request was filtered because Identifier is missing`);
          } else {
            console.log(`This request was filtered for unknown reasons`);
          }
        });
      }
      
      return uniqueFiltered;
    },
    approvalStatus() {
      if (!this.selectedApproval) return null;
      
      // Use the helper method to get accurate approval status
      const status = this.getApprovalStatus(this.selectedApproval);
      
      // Enhanced debug logging
      console.log('📊 approvalStatus computed:', {
        selectedApprovalId: this.selectedApproval.ApprovalId,
        identifier: this.selectedApproval.Identifier,
        approvedNot: this.selectedApproval.ApprovedNot,
        complianceApprovalStatus: this.selectedApproval.ExtractedData?.compliance_approval?.approved,
        calculatedStatus: status,
        impactField: this.selectedApproval.ExtractedData?.Impact,
        probabilityField: this.selectedApproval.ExtractedData?.Probability
      });
      
      return status;
    },
    approvedComplianceItems() {
      // Since we now show the latest version in complianceApprovals, 
      // we need to filter from that list to get only approved items
      const latestVersions = this.complianceApprovals;
      
      // Filter to only show approved items from the latest versions
      const approved = latestVersions.filter(approval => approval.ApprovedNot === true);
      
      console.log(`Found ${approved.length} approved compliance items from latest versions`);
      return approved;
    },
    groupedApprovals() {
      // Group approvals by status using ApprovedNot field as source of truth
      const groups = {
        Pending: [],
        Approved: [],
        Rejected: []
      };
      this.approvals.forEach(approval => {
        if (approval.ApprovedNot === null || approval.ApprovedNot === undefined) {
          groups.Pending.push(approval);
        } else if (approval.ApprovedNot === true) {
          groups.Approved.push(approval);
        } else if (approval.ApprovedNot === false) {
          groups.Rejected.push(approval);
        }
      });
      return groups;
    },
    approvalTableHeaders() {
      return [
        { key: 'Identifier', label: 'Identifier' },
        { key: 'Description', label: 'Description' },
        { key: 'Criticality', label: 'Criticality' },
        { key: 'CreatedBy', label: 'Created By' },
        { key: 'Version', label: 'Version' },
        { key: 'actions', label: 'Actions' }
      ];
    },
    rejectedTableHeaders() {
      return [
        { key: 'Identifier', label: 'Identifier' },
        { key: 'Description', label: 'Description' },
        { key: 'Criticality', label: 'Criticality' },
        { key: 'CreatedBy', label: 'Created By' },
        { key: 'Version', label: 'Version' },
        { key: 'actions', label: 'Actions' }
      ];
    },
    myTasksCount() {
      return this.myTasks ? this.myTasks.length : 0;
    },
    reviewerTasksCount() {
      return this.reviewerTasks ? this.reviewerTasks.length : 0;
    },
    myTasksPending() {
      // Apply deduplication logic to show only the latest version of each pending item
      // FIXED: Use the ApprovedNot field as the source of truth for approval status
      console.log('🔍 MyTasksPending filtering - Total myTasks:', this.myTasks.length);
      console.log('🔍 Selected framework:', this.selectedFramework);
      console.log('🔍 Available frameworks:', this.frameworks.map(f => ({ id: f.FrameworkId, name: f.FrameworkName })));
      
      const pending = this.myTasks.filter(t => {
        // Framework filtering - use FrameworkId directly from the ComplianceApproval record
        if (this.selectedFramework) {
          const taskFrameworkId = t.FrameworkId_id || t.FrameworkId
          console.log(`🔍 Framework filter active - Selected ID: "${this.selectedFramework}", Task FrameworkId: "${taskFrameworkId}"`);
          
          if (taskFrameworkId && taskFrameworkId.toString() !== this.selectedFramework.toString()) {
            console.log(`❌ Filtering out ${t.Identifier} - framework ID mismatch (${taskFrameworkId} vs ${this.selectedFramework})`);
            return false
          }
        }
        
        const isPending = t.ApprovedNot === null || t.ApprovedNot === undefined;
        const isApproved = t.ApprovedNot === true;
        const complianceApproval = t.ExtractedData?.compliance_approval || {};
        const isResubmitted = complianceApproval.inResubmission === true;
        
        // CRITICAL: Exclude approved items even if they have resubmission flag
        if (isApproved) {
          console.log(`Excluding approved compliance from pending: ${t.Identifier} (ApprovalId: ${t.ApprovalId})`);
          return false;
        }
        
        // CRITICAL: Check if this compliance exists as approved in raw data (both my and reviewer tasks)
        // If the same compliance is approved elsewhere, don't show it in pending
        const allRawTasks = [...(this.myTasks || []), ...(this.reviewerTasks || [])];
        const isApprovedElsewhere = allRawTasks.some(rawTask => 
          rawTask.Identifier === t.Identifier && rawTask.ApprovedNot === true && rawTask.ApprovalId !== t.ApprovalId
        );
        
        if (isApprovedElsewhere) {
          console.log(`Excluding pending compliance that is approved elsewhere: ${t.Identifier} (ApprovalId: ${t.ApprovalId})`);
          return false;
        }
        
        // Include items that are either pending OR resubmitted (but not approved)
        const shouldInclude = isPending || (isResubmitted && !isApproved);
        
        if (isResubmitted && !isApproved) {
          console.log(`Including resubmitted compliance in pending: ${t.Identifier} (ApprovalId: ${t.ApprovalId})`);
        }
        
        return shouldInclude;
      });
      
      // Sort by ApprovalId to get the most recent first
      const sortedPending = pending.sort((a, b) => b.ApprovalId - a.ApprovalId);
      
      // Remove duplicates based on Identifier
      const uniquePending = [];
      const seenIdentifiers = new Set();
      
      for (const item of sortedPending) {
        if (!seenIdentifiers.has(item.Identifier)) {
          seenIdentifiers.add(item.Identifier);
          uniquePending.push(item);
          console.log(`Added latest pending version for ${item.Identifier} (ApprovalId: ${item.ApprovalId})`);
        } else {
          console.log(`Skipping older pending version of ${item.Identifier} (ApprovalId: ${item.ApprovalId})`);
        }
      }
      
      console.log(`MyTasksPending deduplication: ${pending.length} total -> ${uniquePending.length} unique`);
      return uniquePending;
    },
    myTasksApproved() {
      // Apply deduplication logic to show only the latest version of each approved item
      // FIXED: Use the ApprovedNot field as the source of truth for approval status
      const approved = this.myTasks.filter(t => {
        // Framework filtering - use FrameworkId directly from the ComplianceApproval record
        if (this.selectedFramework) {
          const taskFrameworkId = t.FrameworkId_id || t.FrameworkId
          if (taskFrameworkId && taskFrameworkId.toString() !== this.selectedFramework.toString()) {
            return false
          }
        }
        
        return t.ApprovedNot === true;
      });
      
      // Sort by ApprovalId to get the most recent first
      const sortedApproved = approved.sort((a, b) => b.ApprovalId - a.ApprovalId);
      
      // Remove duplicates based on Identifier
      const uniqueApproved = [];
      const seenIdentifiers = new Set();
      
      for (const item of sortedApproved) {
        if (!seenIdentifiers.has(item.Identifier)) {
          seenIdentifiers.add(item.Identifier);
          uniqueApproved.push(item);
          console.log(`Added latest approved version for ${item.Identifier} (ApprovalId: ${item.ApprovalId})`);
        } else {
          console.log(`Skipping older approved version of ${item.Identifier} (ApprovalId: ${item.ApprovalId})`);
        }
      }
      
      console.log(`MyTasksApproved deduplication: ${approved.length} total -> ${uniqueApproved.length} unique`);
      return uniqueApproved;
    },
    myTasksRejected() {
      // Apply deduplication logic to show only the latest version of each rejected item
      // FIXED: Use the ApprovedNot field as the source of truth for approval status
      const rejected = this.myTasks.filter(t => {
        // Framework filtering - use FrameworkId directly from the ComplianceApproval record
        if (this.selectedFramework) {
          const taskFrameworkId = t.FrameworkId_id || t.FrameworkId
          if (taskFrameworkId && taskFrameworkId.toString() !== this.selectedFramework.toString()) {
            return false
          }
        }
        
        return t.ApprovedNot === false;
      });
      
      // Sort by ApprovalId to get the most recent first
      const sortedRejected = rejected.sort((a, b) => b.ApprovalId - a.ApprovalId);
      
      // Remove duplicates based on Identifier
      const uniqueRejected = [];
      const seenIdentifiers = new Set();
      
      for (const item of sortedRejected) {
        if (!seenIdentifiers.has(item.Identifier)) {
          seenIdentifiers.add(item.Identifier);
          uniqueRejected.push(item);
          console.log(`Added latest rejected version for ${item.Identifier} (ApprovalId: ${item.ApprovalId})`);
        } else {
          console.log(`Skipping older rejected version of ${item.Identifier} (ApprovalId: ${item.ApprovalId})`);
        }
      }
      
      console.log(`MyTasksRejected deduplication: ${rejected.length} total -> ${uniqueRejected.length} unique`);
      return uniqueRejected;
    },
    reviewerTasksPending() {
      // Apply deduplication logic to show only the latest version of each pending item
      // FIXED: Use the ApprovedNot field as the source of truth for approval status
      const pending = this.reviewerTasks.filter(t => {
        // Framework filtering - use FrameworkId directly from the ComplianceApproval record
        if (this.selectedFramework) {
          const taskFrameworkId = t.FrameworkId_id || t.FrameworkId
          if (taskFrameworkId && taskFrameworkId.toString() !== this.selectedFramework.toString()) {
            return false
          }
        }
        
        const isPending = t.ApprovedNot === null || t.ApprovedNot === undefined;
        const isApproved = t.ApprovedNot === true;
        const complianceApproval = t.ExtractedData?.compliance_approval || {};
        const isResubmitted = complianceApproval.inResubmission === true;
        
        // CRITICAL: Exclude approved items even if they have resubmission flag
        if (isApproved) {
          console.log(`Excluding approved compliance from reviewer pending: ${t.Identifier} (ApprovalId: ${t.ApprovalId})`);
          return false;
        }
        
        // CRITICAL: Check if this compliance exists as approved in raw data (both my and reviewer tasks)
        // If the same compliance is approved elsewhere, don't show it in pending
        const allRawTasks = [...(this.myTasks || []), ...(this.reviewerTasks || [])];
        const isApprovedElsewhere = allRawTasks.some(rawTask => 
          rawTask.Identifier === t.Identifier && rawTask.ApprovedNot === true && rawTask.ApprovalId !== t.ApprovalId
        );
        
        if (isApprovedElsewhere) {
          console.log(`Excluding reviewer pending compliance that is approved elsewhere: ${t.Identifier} (ApprovalId: ${t.ApprovalId})`);
          return false;
        }
        
        const shouldInclude = isPending || (isResubmitted && !isApproved);
        
        console.log(`ReviewerTasksPending filter check for ${t.Identifier}:`, {
          approvalId: t.ApprovalId,
          ApprovedNot: t.ApprovedNot,
          isPending: isPending,
          isApproved: isApproved,
          isResubmitted: isResubmitted,
          isApprovedElsewhere: isApprovedElsewhere,
          shouldInclude: shouldInclude
        });
        
        // Resubmitted items should appear in reviewer's pending tasks for review (but not if approved)
        if (isResubmitted && !isApproved) {
          console.log(`✅ Including resubmitted compliance in reviewer pending: ${t.Identifier}`);
        }
        
        return shouldInclude;
      });
      
      // Sort by ApprovalId to get the most recent first
      const sortedPending = pending.sort((a, b) => b.ApprovalId - a.ApprovalId);
      
      // Remove duplicates based on Identifier
      const uniquePending = [];
      const seenIdentifiers = new Set();
      
      for (const item of sortedPending) {
        if (!seenIdentifiers.has(item.Identifier)) {
          seenIdentifiers.add(item.Identifier);
          uniquePending.push(item);
          console.log(`Added latest reviewer pending version for ${item.Identifier} (ApprovalId: ${item.ApprovalId})`);
        } else {
          console.log(`Skipping older reviewer pending version of ${item.Identifier} (ApprovalId: ${item.ApprovalId})`);
        }
      }
      
      console.log(`ReviewerTasksPending deduplication: ${pending.length} total -> ${uniquePending.length} unique`);
      return uniquePending;
    },
    reviewerTasksApproved() {
      // Apply deduplication logic to show only the latest version of each approved item
      // FIXED: Use the ApprovedNot field as the source of truth for approval status
      const approved = this.reviewerTasks.filter(t => {
        // Framework filtering - use FrameworkId directly from the ComplianceApproval record
        if (this.selectedFramework) {
          const taskFrameworkId = t.FrameworkId_id || t.FrameworkId
          if (taskFrameworkId && taskFrameworkId.toString() !== this.selectedFramework.toString()) {
            return false
          }
        }
        
        const isApproved = t.ApprovedNot === true;
        console.log(`ReviewerTasksApproved filter check for ${t.Identifier}:`, {
          approvalId: t.ApprovalId,
          ApprovedNot: t.ApprovedNot,
          isApproved: isApproved
        });
        return isApproved;
      });
      
      // Sort by ApprovalId to get the most recent first
      const sortedApproved = approved.sort((a, b) => b.ApprovalId - a.ApprovalId);
      
      // Remove duplicates based on Identifier
      const uniqueApproved = [];
      const seenIdentifiers = new Set();
      
      for (const item of sortedApproved) {
        if (!seenIdentifiers.has(item.Identifier)) {
          seenIdentifiers.add(item.Identifier);
          uniqueApproved.push(item);
          console.log(`Added latest reviewer approved version for ${item.Identifier} (ApprovalId: ${item.ApprovalId})`);
        } else {
          console.log(`Skipping older reviewer approved version of ${item.Identifier} (ApprovalId: ${item.ApprovalId})`);
        }
      }
      
      console.log(`ReviewerTasksApproved deduplication: ${approved.length} total -> ${uniqueApproved.length} unique`);
      return uniqueApproved;
    },
    reviewerTasksRejected() {
      // Apply deduplication logic to show only the latest version of each rejected item
      // FIXED: Use the ApprovedNot field as the source of truth for approval status
      const rejected = this.reviewerTasks.filter(t => {
        // Framework filtering - use FrameworkId directly from the ComplianceApproval record
        if (this.selectedFramework) {
          const taskFrameworkId = t.FrameworkId_id || t.FrameworkId
          if (taskFrameworkId && taskFrameworkId.toString() !== this.selectedFramework.toString()) {
            return false
          }
        }
        
        const isRejected = t.ApprovedNot === false;
        console.log(`ReviewerTasksRejected filter check for ${t.Identifier}:`, {
          approvalId: t.ApprovalId,
          ApprovedNot: t.ApprovedNot,
          isRejected: isRejected
        });
        return isRejected;
      });
      
      // Sort by ApprovalId to get the most recent first
      const sortedRejected = rejected.sort((a, b) => b.ApprovalId - a.ApprovalId);
      
      // Remove duplicates based on Identifier
      const uniqueRejected = [];
      const seenIdentifiers = new Set();
      
      for (const item of sortedRejected) {
        if (!seenIdentifiers.has(item.Identifier)) {
          seenIdentifiers.add(item.Identifier);
          uniqueRejected.push(item);
          console.log(`Added latest rejected version for ${item.Identifier} (ApprovalId: ${item.ApprovalId})`);
        } else {
          console.log(`Skipping older rejected version of ${item.Identifier} (ApprovalId: ${item.ApprovalId})`);
        }
      }
      
      console.log(`ReviewerTasksRejected deduplication: ${rejected.length} total -> ${uniqueRejected.length} unique`);
      return uniqueRejected;
    },
    myTasksPendingPaged() {
      const { currentPage, pageSize } = this.myTasksPagination.Pending;
      const start = (currentPage - 1) * pageSize;
      return this.myTasksPending.slice(start, start + pageSize);
    },
    myTasksApprovedPaged() {
      const { currentPage, pageSize } = this.myTasksPagination.Approved;
      const start = (currentPage - 1) * pageSize;
      return this.myTasksApproved.slice(start, start + pageSize);
    },
    myTasksRejectedPaged() {
      const { currentPage, pageSize } = this.myTasksPagination.Rejected;
      const start = (currentPage - 1) * pageSize;
      return this.myTasksRejected.slice(start, start + pageSize);
    },
    reviewerTasksPendingPaged() {
      const { currentPage, pageSize } = this.reviewerTasksPagination.Pending;
      const start = (currentPage - 1) * pageSize;
      return this.reviewerTasksPending.slice(start, start + pageSize);
    },
    reviewerTasksApprovedPaged() {
      const { currentPage, pageSize } = this.reviewerTasksPagination.Approved;
      const start = (currentPage - 1) * pageSize;
      return this.reviewerTasksApproved.slice(start, start + pageSize);
    },
    reviewerTasksRejectedPaged() {
      const { currentPage, pageSize } = this.reviewerTasksPagination.Rejected;
      const start = (currentPage - 1) * pageSize;
      return this.reviewerTasksRejected.slice(start, start + pageSize);
    },
    rejectedCompliances() {
      // Combine all rejected items
      const allRejected = [...this.myTasksRejected, ...this.reviewerTasksRejected];
      
      // FIXED: Smart filtering for resubmitted items
      // - Creators should see rejected items (including resubmitted ones) to edit/resubmit
      // - Reviewers should NOT see resubmitted items in rejected list (they see them in pending)
      const filteredRejected = allRejected.filter(item => {
        const complianceApproval = item.ExtractedData?.compliance_approval || {};
        const isResubmitted = complianceApproval.inResubmission === true;
        const isMyTask = this.myTasksRejected.includes(item);
        const isReviewerTask = this.reviewerTasksRejected.includes(item);
        
        if (isResubmitted) {
          if (isMyTask) {
            console.log(`✅ Keeping resubmitted compliance in rejected list for creator: ${item.Identifier} (ApprovalId: ${item.ApprovalId})`);
            console.log(`Creator can still see and edit this item`);
            return true; // Show to creator
          } else if (isReviewerTask) {
            console.log(`🔄 Filtering out resubmitted compliance from reviewer's rejected list: ${item.Identifier} (ApprovalId: ${item.ApprovalId})`);
            console.log(`This item should now appear in reviewer's pending tasks`);
            return false; // Hide from reviewer's rejected list
          }
        }
        
        // Show all non-resubmitted rejected items to everyone
        return true;
      });
      
      console.log(`Filtered out resubmitted items: ${allRejected.length} -> ${filteredRejected.length}`);
      
      // Group by compliance content to find duplicates
      const complianceGroups = new Map();
      
      filteredRejected.forEach(item => {
        const extractedData = item.ExtractedData || {};
        
        // Create a unique key based on compliance content
        const contentKey = this.createComplianceContentKey(item);
        
        if (!complianceGroups.has(contentKey)) {
          complianceGroups.set(contentKey, []);
        }
        complianceGroups.get(contentKey).push(item);
        
        // Debug logging for content key generation
        console.log('Content key for item:', {
          approvalId: item.ApprovalId,
          contentKey: contentKey,
          identifier: item.Identifier || extractedData.Identifier,
          description: extractedData.ComplianceItemDescription || extractedData.description
        });
      });
      
      // For each group, keep only the latest item (highest ApprovalId)
      const uniqueRejected = [];
      complianceGroups.forEach((items, contentKey) => {
        if (items.length > 1) {
          console.log(`Found ${items.length} duplicate items for content key: ${contentKey}`, items.map(i => i.ApprovalId));
        }
        
        // Sort by ApprovalId descending and take the first (latest) one
        const latestItem = items.sort((a, b) => (b.ApprovalId || 0) - (a.ApprovalId || 0))[0];
        uniqueRejected.push(latestItem);
      });
      
      console.log(`Deduplication: ${filteredRejected.length} total items -> ${uniqueRejected.length} unique items`);
      
      // Apply mapping to ensure proper data structure
      const mappedRejected = uniqueRejected.map(item => this.mapApprovalToRow(item));
      
      // Debug logging to see what's being returned
      console.log('Rejected compliances after mapping:', mappedRejected.map(item => ({
        ApprovalId: item.ApprovalId,
        Identifier: item.Identifier,
        Description: item.Description,
        Criticality: item.Criticality,
        CreatedBy: item.CreatedBy
      })));
      
      return mappedRejected;
    },
    isMitigationObject() {
      return this.editingCompliance && this.editingCompliance.ExtractedData && typeof this.editingCompliance.ExtractedData.mitigation === 'object';
    },
    rejectionReason() {
      if (!this.editingCompliance || !this.editingCompliance.ExtractedData) return '';
      const ca = this.editingCompliance.ExtractedData.compliance_approval || {};
      // Check multiple possible locations for rejection reason
      return ca.remarks || 
             ca.rejection_reason || 
             ca.reason || 
             this.editingCompliance.ExtractedData.rejection_remarks || 
             '';
    },
  }
}
</script>
 
<style scoped>
.error-message {
  background-color: #fee;
  color: #c00;
  padding: 1rem;
  margin: 1rem 0;
  border-radius: 4px;
  border: 1px solid #fcc;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
 
.retry-btn {
  background: #c00;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}
 
.loading-state {
  text-align: center;
  padding: 2rem;
  color: #666;
}
 
.no-data-state {
  text-align: center;
  padding: 2rem;
  color: #666;
  background: #f9f9f9;
  border-radius: 4px;
  margin: 1rem 0;
}
 
.no-data-state i {
  font-size: 2rem;
  color: #999;
  margin-bottom: 1rem;
}
 
.approval-details {
  margin: 0.5rem 0;
}
 
.description {
  margin: 0.5rem 0;
  color: #666;
}
 
.meta-info {
  display: flex;
  gap: 1rem;
  font-size: 0.9rem;
  color: #666;
}
 
.criticality {
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  font-weight: 500;
}
 
.criticality.high {
  background: #fee;
  color: #c00;
}
 
.criticality.medium {
  background: #ffd;
  color: #960;
}
 
.criticality.low {
  background: #efe;
  color: #060;
}
 
.created-by {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
 
.version {
  color: #999;
}
 
.approval-status.approved {
  color: #28a745;
  font-weight: 500;
}
 
.approved-list {
  margin-top: 2rem;
  background-color: #f8fff8;
  padding: 1rem;
  border-radius: 4px;
  border: 1px solid #d0e9d0;
}
 
.approved-list h3 {
  color: #28a745;
  border-bottom: 1px solid #d0e9d0;
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}
 
.approved-list li {
  background-color: white;
  border: 1px solid #e0e0e0;
  margin-bottom: 1rem;
  padding: 1rem;
  border-radius: 4px;
  position: relative;
}
 
.status-badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  font-size: 0.8rem;
  font-weight: 500;
  margin-left: 0.5rem;
}
 
.status-badge.approved {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}
 
.approval-date {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  color: #28a745;
}
 
.approval-date i {
  font-size: 0.9rem;
}
 
.rejection-reason {
  margin-top: 8px;
  padding: 8px 12px;
  background-color: #fff0f0;
  border-left: 3px solid #ff3333;
  border-radius: 0 4px 4px 0;
  color: #c00;
  font-size: 0.9rem;
  font-style: italic;
  max-width: 300px;
  word-wrap: break-word;
}

.badge.rejected {
  background-color: #ffebee;
  color: #d32f2f;
  border: 1px solid #ffcdd2;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.rejected-approvals-list {
  margin-top: 2rem;
  background-color: #fff8f8;
  padding: 1.5rem;
  border-radius: 8px;
  border: 2px solid #e6d0d0;
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.1);
}

.rejected-approvals-list h3 {
  color: #c00;
  border-bottom: 1px solid #e6d0d0;
  padding-bottom: 0.8rem;
  margin-bottom: 1.5rem;
  font-size: 1.2rem;
  font-weight: 600;
}

.rejected-approvals-list li {
  background-color: white;
  border: 1px solid #e0e0e0;
  margin-bottom: 1rem;
  padding: 1rem;
  border-radius: 4px;
  position: relative;
}

.rejected-item-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.rejected-item-details {
  padding-left: 0.5rem;
  border-left: 2px solid #f0f0f0;
}

.rejected-date {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  color: #d32f2f;
}

.rejected-date i {
  font-size: 0.9rem;
}

.edit-rejected-btn {
  margin-top: 1rem;
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.edit-rejected-btn:hover {
  background-color: #eeeeee;
  border-color: #ccc;
}

.edit-rejected-btn i {
  font-size: 0.9rem;
  color: #555;
}

.rejected-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e6d0d0;
  padding-bottom: 0.8rem;
  margin-bottom: 1.5rem;
}

.refresh-rejected-btn {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  border: 1px solid #dc3545;
  background-color: #fff;
  color: #dc3545;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.refresh-rejected-btn:hover {
  background-color: #dc3545;
  color: white;
}

@import './ComplianceApprover.css';

/* Add styles for the deactivation badge */
.deactivation-badge {
  display: inline-block;
  background-color: #ffe0b2;
  color: #e65100;
  border: 1px solid #ffcc80;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  margin-left: 0.5rem;
}

/* Add styles for the warning message */
.warning-message {
  margin-top: 15px;
  padding: 10px 15px;
  background-color: #fff3e0;
  border-left: 4px solid #ff9800;
  border-radius: 0 4px 4px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.warning-message i {
  color: #ff9800;
  font-size: 1.2rem;
}

.deactivation-request-details {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff8e1;
  border-radius: 4px;
}

.compliance-details-section {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  padding: 2rem;
  margin: 2rem auto;
  max-width: 900px;
  position: relative;
  animation: fadeIn 0.3s;
}
.back-btn {
  background: #f5f5f5;
  border: none;
  color: #333;
  font-size: 1rem;
  padding: 0.5rem 1.2rem;
  border-radius: 6px;
  margin-bottom: 1.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  transition: background 0.2s;
}
.back-btn:hover {
  background: #e0e0e0;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(30px);}
  to { opacity: 1; transform: translateY(0);}
}

.rejected-table-wrapper {
  overflow-x: auto;
}

.rejected-table {
  width: 100%;
  border-collapse: collapse;
}

.rejected-table th, .rejected-table td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.rejected-table th {
  background-color: #f8f9fa;
}

.badge-rejected {
  background-color: #ffdddd;
  color: #d32f2f;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.action-btn {
  margin-right: 10px;
  padding: 5px 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.action-btn:hover {
  background-color: #e0e0e0;
}

.view-btn {
  background: transparent !important;
  color: #3b82f6 !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 8px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 0 !important;
  transition: all 0.2s ease !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  white-space: nowrap !important;
  min-width: auto !important;
  width: auto !important;
  height: auto !important;
  box-shadow: none !important;
  margin: 0 auto !important;
  visibility: visible !important;
  opacity: 1 !important;
  z-index: 1 !important;
  position: relative !important;
}

.edit-btn {
  background: transparent !important;
  color: #3b82f6 !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 8px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 0 !important;
  transition: all 0.2s ease !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  white-space: nowrap !important;
  min-width: auto !important;
  width: auto !important;
  height: auto !important;
  box-shadow: none !important;
  margin: 0 auto !important;
  visibility: visible !important;
  opacity: 1 !important;
  z-index: 1 !important;
  position: relative !important;
}

.view-btn:hover {
  background: transparent !important;
  color: #1d4ed8 !important;
  transform: scale(1.1) !important;
  box-shadow: none !important;
}

.edit-btn:hover {
  background: transparent !important;
  color: #1d4ed8 !important;
  transform: scale(1.1) !important;
  box-shadow: none !important;
}

.view-btn i {
  font-size: 18px !important;
}

.edit-btn i {
  font-size: 18px !important;
}

/* Ensure both buttons are always visible in actions cell */
.actions-cell .view-btn,
.actions-cell .edit-btn {
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  border: none !important;
  border-color: transparent !important;
  border-width: 0 !important;
  border-style: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  outline: none !important;
  padding: 8px !important;
  cursor: pointer !important;
  align-items: center !important;
  justify-content: center !important;
  min-width: 32px !important;
  height: 32px !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  white-space: nowrap !important;
  width: auto !important;
  max-width: none !important;
  max-height: none !important;
}

.actions-cell .view-btn {
  color: #3b82f6 !important;
}

.actions-cell .edit-btn {
  color: #3b82f6 !important;
}

.actions-cell .view-btn:hover {
  color: #1d4ed8 !important;
  transform: scale(1.1) !important;
}

.actions-cell .edit-btn:hover {
  color: #1d4ed8 !important;
  transform: scale(1.1) !important;
}

/* Override any other CSS files that might be affecting these buttons */
.rejected-approvals-section .actions-cell .view-btn,
.rejected-approvals-section .actions-cell .edit-btn,
.frameworks-table .actions-cell .view-btn,
.frameworks-table .actions-cell .edit-btn,
table .actions-cell .view-btn,
table .actions-cell .edit-btn {
  background: transparent !important;
  background-color: transparent !important;
  background-image: none !important;
  border: none !important;
  border-color: transparent !important;
  border-width: 0 !important;
  border-style: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  outline: none !important;
  padding: 8px !important;
  cursor: pointer !important;
  align-items: center !important;
  justify-content: center !important;
  min-width: 32px !important;
  height: 32px !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  white-space: nowrap !important;
  width: auto !important;
  max-width: none !important;
  max-height: none !important;
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.rejected-approvals-section .actions-cell .view-btn,
.frameworks-table .actions-cell .view-btn,
table .actions-cell .view-btn {
  color: #3b82f6 !important;
}

.rejected-approvals-section .actions-cell .edit-btn,
.frameworks-table .actions-cell .edit-btn,
table .actions-cell .edit-btn {
  color: #3b82f6 !important;
}

.status-badge.rejected {
  background-color: #ffdddd;
  color: #d32f2f;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.actions-cell {
  display: flex;
  gap: 10px;
  justify-content: center;
  align-items: center;
  padding: 8px;
}

.severity-rating {
  font-weight: 500;
  color: #333;
}

.probability-value {
  font-weight: 500;
  color: #333;
}

.severity-rating small,
.probability-value small {
  display: block;
  margin-top: 4px;
  font-size: 0.8rem;
  color: #999;
  font-style: italic;
}

.compliance-detail-row {
  margin-bottom: 1rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.compliance-detail-row:last-child {
  border-bottom: none;
}

.compliance-detail-row strong {
  display: inline-block;
  min-width: 120px;
  color: #555;
  font-weight: 600;
}

.compliance-detail-row strong i {
  margin-right: 0.5rem;
  color: #666;
}

.creator-message, .admin-message {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.95rem;
  line-height: 1.4;
}

.creator-message {
  background-color: #fff3e0;
  border: 1px solid #ffcc80;
  color: #e65100;
}

.admin-message {
  background-color: #e3f2fd;
  border: 1px solid #90caf9;
  color: #1565c0;
}

.creator-message i {
  font-size: 1.1rem;
  color: #ff9800;
}

.admin-message i {
  font-size: 1.1rem;
  color: #2196f3;
}

.debug-message {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.95rem;
  line-height: 1.4;
  background-color: #fff3cd;
  border: 1px solid #ffeaa7;
  color: #856404;
}

.debug-message i {
  font-size: 1.1rem;
  color: #f39c12;
}

/* Edit Compliance Modal Styles */
.edit-compliance-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
}

.edit-compliance-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalSlideIn 0.3s ease-out;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #212529;
}

.modal-body {
  padding: 32px;
}

.form-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.form-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-field.full-width {
  grid-column: 1 / -1;
}

.form-field label {
  font-size: 14px;
  font-weight: 600;
  color: #495057;
  display: flex;
  align-items: center;
  gap: 4px;
}

.form-field .required {
  color: #dc3545;
  font-size: 16px;
}

.form-field input,
.form-field select,
.form-field textarea {
  padding: 10px 14px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  background: white;
  color: #212529;
  transition: all 0.2s ease;
  width: 100%;
  box-sizing: border-box;
}

.form-field input:focus,
.form-field select:focus,
.form-field textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.form-field input:read-only {
  background: #f8f9fa;
  cursor: not-allowed;
}

.description-input {
  resize: vertical;
  min-height: 80px;
}

.text-input,
.select-input {
  height: 40px;
}

.field-error {
  color: #dc3545;
  font-size: 12px;
  margin-top: 4px;
}

.rejection-reason-box {
  padding: 16px;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-left: 4px solid #dc3545;
  border-radius: 6px;
  color: #495057;
  font-size: 14px;
  line-height: 1.5;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 24px 32px;
  border-top: 1px solid #e0e0e0;
}

.cancel-button,
.resubmit-button {
  padding: 12px 24px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  border: none;
}

.cancel-button {
  background: #f8f9fa;
  color: #495057;
  border: 1px solid #dee2e6;
}

.cancel-button:hover {
  background: #e9ecef;
  border-color: #ced4da;
}

.resubmit-button {
  background: #3b82f6;
  color: white;
  position: relative;
}

.resubmit-button:hover:not(:disabled):not(.submitting) {
  background: #2563eb;
}

.resubmit-button:disabled,
.resubmit-button.submitting {
  opacity: 0.6;
  cursor: not-allowed;
  pointer-events: none;
}

.resubmit-button.submitting {
  background: #60a5fa;
}

.resubmit-button i {
  font-size: 16px;
  margin-right: 4px;
}

.resubmit-button .fa-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
  .form-columns {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .edit-compliance-content {
    width: 95%;
    max-height: 95vh;
  }
  
  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 20px;
  }
}

.reviewer-empty-wrapper {
  text-align: center;
  padding: 2rem;
  color: #666;
 
  border-radius: 4px;
  margin: 1rem 0;
}

.reviewer-empty-wrapper i {
  font-size: 2rem;
  color: #999;
  margin-bottom: 1rem;
}
</style>