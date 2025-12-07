<template>
  <!-- Only show main content if reject modal is NOT open -->
  <div v-if="!showRejectModal">
    <div class="policy_main_container">
      <!-- Professional Header Section -->
      <div class="policy_header">
        <div class="policy_title_section">
          <h1 class="policy_title">Policy Approval</h1>
          <p class="policy_subtitle">Review and manage policy approval requests</p>
        </div>
      </div>
      
      <!-- User Selection and Filter Row -->
      <div class="policy_filters_row">
        <!-- User Selection for Administrators -->
        <div v-if="isAdministrator" class="policy_user_selection">
          <div class="policy_user_card">
            <div class="policy_user_header">
              <i class="fas fa-user-cog"></i>
              <span>USER SELECTION</span>
            </div>
            <select 
              id="userSelect" 
              v-model="selectedUserId" 
              @change="onUserChange" 
              class="policy_user_dropdown"
            >
              <option v-for="user in availableUsers" :key="user.UserId" :value="user.UserId">
                {{ user.UserName }} ({{ user.Role }}) - ID: {{ user.UserId }}
              </option>
            </select>
            <small v-if="!selectedUserId" class="policy_user_help">
              Please select a user to view their tasks
            </small>
          </div>
        </div>
        
        <!-- Filter Section -->
        <div class="policy_filter_section">
          <div class="policy_filter_block">
            <label class="policy_filter_label">
              <i class="fas fa-filter"></i>
              FILTER
            </label>
            <select 
              id="framework-filter" 
              v-model="selectedFrameworkId" 
              @change="onFrameworkChange"
              class="policy_filter_dropdown"
            >
              <option value="">All Frameworks</option>
              <option 
                v-for="framework in filteredFrameworks" 
                :key="framework.id" 
                :value="framework.id"
              >
                {{ framework.name }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- Summary Cards -->
      <div class="policy_summary_section">
        <div class="policy_summary_item">
          <div class="policy_summary_icon"><i class="fas fa-clock"></i></div>
          <div class="policy_summary_content">
            <div class="policy_summary_number">{{ pendingApprovalsCount }}</div>
            <div class="policy_summary_label">Pending Review</div>
          </div>
        </div>
        
        <div class="policy_summary_item clickable" @click="navigateToAllPolicies">
          <div class="policy_summary_icon"><i class="fas fa-check-circle"></i></div>
          <div class="policy_summary_content">
            <div class="policy_summary_number">{{ approvedApprovalsCount }}</div>
            <div class="policy_summary_label">Approved</div>
          </div>
        </div>
        
        <div class="policy_summary_item clickable" @click="navigateToAllPolicies">
          <div class="policy_summary_icon"><i class="fas fa-times-circle"></i></div>
          <div class="policy_summary_content">
            <div class="policy_summary_number">{{ rejectedApprovalsCount }}</div>
            <div class="policy_summary_label">Rejected</div>
          </div>
        </div>
      </div>

      <!-- Task Navigation -->
      <div class="policy_task_navigation">
        <div class="policy_nav_tabs">
          <button 
            class="policy_nav_tab"
            :class="{ active: activeTab === 'myTasks' }"
            @click="switchTab('myTasks')"
          >
            <i class="fas fa-user"></i>
            My Tasks
            <span class="policy_tab_badge">{{ myTasksCount }}</span>
          </button>
          <button 
            class="policy_nav_tab"
            :class="{ active: activeTab === 'reviewerTasks' }"
            @click="switchTab('reviewerTasks')"
          >
            <i class="fas fa-users"></i>
            Reviewer Tasks
            <span class="policy_tab_badge">{{ reviewerTasksCount }}</span>
          </button>
          </div>
        </div>
        
      <!-- Tab Content -->
      <div class="policy_tasks_container">
        <!-- My Tasks Tab -->
        <div v-if="activeTab === 'myTasks'">
          <!-- Collapsible Table for My Tasks -->
          <CollapsibleTable
            v-for="section in myTasksCollapsibleSections"
            :key="section.name"
            :section-config="section"
            :table-headers="tableHeaders"
            :is-expanded="expandedSections[section.name.toLowerCase()]"
            :pagination="section.pagination"
            @toggle="toggleSection(section.name)"
            @task-click="handleTaskClick"
            @editTask="(task) => openRejectedItem(task.originalApproval || task.originalData)"
          />
          
          <!-- Rejected Policies (Edit & Resubmit) Section -->
          <CollapsibleTable
            v-if="rejectedPolicies.length"
            :section-config="{
              name: 'Rejected Policies (Edit & Resubmit)',
              statusClass: 'rejected',
              tasks: rejectedPolicies.map(mapPolicyToTableRow)
            }"
            :table-headers="tableHeaders"
            :is-expanded="expandedSections['Rejected Policies (Edit & Resubmit)']"
            @toggle="toggleSection('Rejected Policies (Edit & Resubmit)')"
            @task-click="handleTaskClick"
            @editTask="(task) => openRejectedItem(task.originalData)"
          />

          <!-- Empty state when no tasks -->
          <div v-if="myTasksCollapsibleSections.length === 0" class="policy_no_tasks">
            <div class="policy_no_tasks_icon">
              <i class="fas fa-clipboard-check"></i>
            </div>
            <h4>No My Tasks</h4>
            <p v-if="selectedFrameworkId">
              {{ selectedUserInfo && isAdministrator ? `${selectedUserInfo.UserName} doesn't have` : 'You don\'t have' }} any tasks for the selected framework 
              <strong>{{ frameworks.find(f => f.id.toString() === selectedFrameworkId.toString())?.name || 'Unknown Framework' }}</strong>.
              <br><br>
              <small style="color: #6b7280;">
                Try selecting a different framework or clearing the filter to see all tasks.
              </small>
            </p>
            <p v-else>
              {{ selectedUserInfo && isAdministrator ? `${selectedUserInfo.UserName} doesn't have` : 'You don\'t have' }} any tasks at the moment.
            </p>
          </div>
        </div>

        <!-- Reviewer Tasks Tab -->
        <div v-if="activeTab === 'reviewerTasks'">
          <!-- Collapsible Table for Reviewer Tasks -->
          <CollapsibleTable
            v-for="section in reviewerTasksCollapsibleSections"
            :key="section.name"
            :section-config="section"
            :table-headers="tableHeaders"
            :is-expanded="expandedSections[section.name.toLowerCase()]"
            :pagination="section.pagination"
            @toggle="toggleSection(section.name)"
            @task-click="handleTaskClick"
            @editTask="(task) => openRejectedItem(task.originalApproval || task.originalData)"
          />
        
        <!-- Empty state when no tasks -->
          <div v-if="reviewerTasksCollapsibleSections.length === 0" class="policy_no_tasks">
            <div class="policy_no_tasks_icon">
              <i class="fas fa-clipboard-check"></i>
            </div>
            <h4>No Reviewer Tasks</h4>
            <p v-if="selectedFrameworkId">
              {{ selectedUserInfo && isAdministrator ? `${selectedUserInfo.UserName} doesn't have` : 'You don\'t have' }} any reviewer tasks for the selected framework 
              <strong>{{ frameworks.find(f => f.id.toString() === selectedFrameworkId.toString())?.name || 'Unknown Framework' }}</strong>.
              <br><br>
              <small style="color: #6b7280;">
                Try selecting a different framework or clearing the filter to see all reviewer tasks.
              </small>
            </p>
            <p v-else>
              {{ selectedUserInfo && isAdministrator ? `${selectedUserInfo.UserName} doesn't have` : 'You don\'t have' }} any reviewer tasks at the moment.
            </p>
          </div>
        </div>
      </div>

      <!-- Policy/Compliance Details Modal/Section -->
      <div v-if="showDetails && selectedApproval && !showRejectModal" class="policy-details-modal-overlay">
        <div class="policy-details-modal">
          <div class="policy-details-content">
            <!-- Show different header based on user type -->
            <h3 v-if="isUserViewingReviewHistory">
              <span class="detail-type-indicator">
                <i class="fas fa-clock"></i>
                Review Status
              </span>
              {{ getPolicyId(selectedApproval) }}
              <span class="status-pill" :class="getPolicyStatusClass(selectedApproval)">
                {{ getApprovalStatus(selectedApproval) === 'pending' ? 'Under Review' : 
                   getApprovalStatus(selectedApproval) === 'approved' ? 'Approved' : 'Rejected' }}
              </span>
            </h3>
            
            <!-- Regular details header for reviewers -->
            <h3 v-else>
              <span class="detail-type-indicator">
                {{ isComplianceApproval ? 'Compliance' : 'Policy' }}
              </span>
              Details: {{ getPolicyId(selectedApproval) }}
              <span class="version-pill">Version: {{ selectedApproval.version || 'u1' }}</span>
              <span v-if="selectedApproval.showingApprovedOnly" class="approved-only-badge">
                Showing Approved Only
              </span>
            </h3>

            <!-- 2. Version history section -->
            <div class="version-history" v-if="selectedApproval.ExtractedData">
              <div class="version-info">
                <div class="version-label">Current Version:</div>
                <div class="version-value">{{ selectedApproval.version || 'u1' }}</div>
              </div>
              <div v-if="selectedApproval.ExtractedData.subpolicies && selectedApproval.ExtractedData.subpolicies.length > 0" 
                   class="subpolicies-versions">
                <h4>Subpolicies Versions:</h4>
                <ul class="version-list">
                  <li v-for="sub in selectedApproval.ExtractedData.subpolicies" :key="sub.SubPolicyId">
                    <span class="subpolicy-name">{{ sub.SubPolicyName }}</span>
                    <span class="version-tag">v{{ sub.version || 'u1' }}</span>
                    <span v-if="sub.resubmitted" class="resubmitted-tag">Resubmitted</span>
                  </li>
                </ul>
              </div>
            </div>
            
            <button class="close-btn" @click="closeApprovalDetails">&times;</button>
            
            <!-- Show different content based on user type -->
            <div v-if="isUserViewingReviewHistory" class="review-status-section">
              <h4><i class="fas fa-clock"></i> Review Status</h4>
              
              <!-- Policy status indicator -->
              <div class="policy-status-indicator">
                <span class="status-label">Current Status:</span>
                <span class="status-value" :class="getPolicyStatusClass(selectedApproval)">
                  {{ getApprovalStatus(selectedApproval) === 'pending' ? 'Under Review' : 
                     getApprovalStatus(selectedApproval) === 'approved' ? 'Approved' : 'Rejected' }}
                </span>
              </div>
              
              <!-- Review progress message -->
              <div class="review-progress-message">
                <div class="progress-icon">
                  <i class="fas fa-info-circle"></i>
                </div>
                <div class="progress-text">
                  <p><strong>Your policy is currently under review.</strong></p>
                  <p>The reviewer will either approve or reject your policy. Once a decision is made, you'll receive a notification with the outcome.</p>
                  <p>Click the <strong>"View Review History"</strong> button below to see detailed review progress and any reviewer actions.</p>
                </div>
              </div>
              
              <!-- Action button to view full review history -->
              <div class="review-action-section">
                <button class="review-history-btn" @click="showReviewHistory(getPolicyId(selectedApproval), selectedApproval.ExtractedData?.PolicyName || getPolicyId(selectedApproval), getApprovalStatus(selectedApproval))">
                  <i class="fas fa-history"></i>
                  View Review History
                </button>
              </div>
            </div>
            
            <!-- Regular Policy/Compliance Approval Section for reviewers -->
            <div v-else class="policy-approval-section">
              <h4>{{ isComplianceApproval ? 'Compliance' : 'Policy' }} Approval</h4>
              
              <!-- Add policy status indicator -->
              <div class="policy-status-indicator">
                <span class="status-label">Status:</span>
                <span class="status-value" :class="{
                  'status-approved': selectedApproval.dbStatus === 'Approved' || selectedApproval.ApprovedNot === true || selectedApproval.ExtractedData?.Status === 'Approved',
                  'status-rejected': selectedApproval.dbStatus === 'Rejected' || selectedApproval.ApprovedNot === false || selectedApproval.ExtractedData?.Status === 'Rejected',
                  'status-pending': !(['Approved', 'Rejected'].includes(selectedApproval.dbStatus)) && selectedApproval.ApprovedNot === null && !(['Approved', 'Rejected'].includes(selectedApproval.ExtractedData?.Status))
                }">
                  {{ selectedApproval.dbStatus === 'Approved' || selectedApproval.ApprovedNot === true || selectedApproval.ExtractedData?.Status === 'Approved' ? 'Approved' : 
                     selectedApproval.dbStatus === 'Rejected' || selectedApproval.ApprovedNot === false || selectedApproval.ExtractedData?.Status === 'Rejected' ? 'Rejected' : 
                     'Under Review' }}
                </span>
              </div>
              
              <div class="policy-actions">
                <!-- Show pending rejections indicator if any exist -->
                <div v-if="hasPendingRejections" class="pending-rejections-indicator">
                  <i class="fas fa-exclamation-triangle"></i>
                  <span>You have pending rejections. Click "Submit Review" to save all decisions.</span>
                </div>
                <!-- Only show submit button if policy is not already approved or rejected -->
                <button 
                  v-if="!(selectedApproval.dbStatus === 'Approved' || selectedApproval.ApprovedNot === true || selectedApproval.ExtractedData?.Status === 'Approved' || selectedApproval.dbStatus === 'Rejected' || selectedApproval.ApprovedNot === false || selectedApproval.ExtractedData?.Status === 'Rejected')"
                  class="submit-btn" 
                  @click="submitReview()" 
                  :disabled="isSubmittingReview" 
                  data-action="submit-policy-review"
                >
                  <i class="fas fa-paper-plane"></i> {{ isSubmittingReview ? 'Submitting...' : 'Submit Review' }}
                </button>
              </div>
              
              <!-- Add this section to show policy approval status - hide when already showing in the indicator -->
              <div v-if="approvalStatus && 
                        !(selectedApproval.ApprovedNot === true || selectedApproval.ExtractedData?.Status === 'Approved') && 
                        !(selectedApproval.ApprovedNot === false || selectedApproval.ExtractedData?.Status === 'Rejected')" 
                   class="policy-approval-status">
                <div class="status-container">
                  <div class="status-label">Status:</div>
                  <div class="status-value" :class="{
                    'approved': approvalStatus.approved === true,
                    'rejected': approvalStatus.approved === false,
                    'pending': approvalStatus.approved === null
                  }">
                    {{ approvalStatus.approved === true ? 'Approved' : 
                       approvalStatus.approved === false ? 'Rejected' : 'Pending' }}
                  </div>
                </div>
                
                <!-- Show approved date if approved -->
                <div v-if="approvalStatus.approved === true && selectedApproval.ApprovedDate" class="policy-approved-date">
                  <div class="date-label">Approved Date:</div>
                  <div class="date-value">{{ formatDate(selectedApproval.ApprovedDate) }}</div>
                </div>
                
                <!-- Show remarks if rejected -->
                <div v-if="approvalStatus.approved === false && 
                          approvalStatus.remarks" class="policy-rejection-remarks">
                  <div class="remarks-label">Rejection Reason:</div>
                  <div class="remarks-value">{{ approvalStatus.remarks }}</div>
                </div>
              </div>
            </div>
            
            <!-- Display details based on type -->
            <div v-if="selectedApproval.ExtractedData">
              <!-- For compliance approvals -->
              <div v-if="isComplianceApproval" class="compliance-details">
                <div class="compliance-detail-row">
                  <strong>Description:</strong> <span>{{ selectedApproval.ExtractedData.ComplianceItemDescription }}</span>
                </div>
                <div class="compliance-detail-row">
                  <strong>Criticality:</strong> <span>{{ selectedApproval.ExtractedData.Criticality }}</span>
                </div>
                <div class="compliance-detail-row">
                  <strong>Impact:</strong> <span>{{ selectedApproval.ExtractedData.Impact }}</span>
                </div>
                <div class="compliance-detail-row">
                  <strong>Probability:</strong> <span>{{ selectedApproval.ExtractedData.Probability }}</span>
                </div>
                <div class="compliance-detail-row">
                  <strong>Mitigation:</strong> <span>{{ selectedApproval.ExtractedData.mitigation }}</span>
                </div>
                <div class="policy-actions">
                  <!-- Show approve/reject buttons only for assigned reviewers -->
                  <button class="approve-btn" @click="approveCompliance()" v-if="canPerformReviewActions(selectedApproval) && selectedApproval.ApprovedNot === null">
                    <i class="fas fa-check"></i> Approve
                  </button>
                  <button class="reject-btn" @click="rejectCompliance()" v-if="canPerformReviewActions(selectedApproval) && selectedApproval.ApprovedNot === null">
                    <i class="fas fa-times"></i> Reject
                  </button>
                  
                  <!-- Show message for policy creators -->
                  <div v-if="isCurrentUserCreator(selectedApproval) && selectedApproval.ApprovedNot === null" class="creator-message">
                    <i class="fas fa-info-circle"></i>
                    <span>This compliance item is under review. You cannot approve or reject your own submission.</span>
                  </div>
                  
                  <!-- Show message for administrators who are not assigned as reviewers -->
                  <div v-if="isAdministrator && !canPerformReviewActions(selectedApproval) && selectedApproval.ApprovedNot === null" class="admin-message">
                    <i class="fas fa-eye"></i>
                    <span>Viewing compliance item. You are not assigned as the reviewer for this item.</span>
                  </div>
                </div>
              </div>
              
              <!-- For policy approvals (existing code) -->
              <div v-else v-for="(value, key) in selectedApproval.ExtractedData" :key="key" class="policy-detail-row">
                <template v-if="key !== 'subpolicies' && key !== 'policy_approval'">
                  <strong>{{ key }}:</strong> <span>{{ value }}</span>
                </template>
                
                <!-- Subpolicies Section -->
                <template v-if="key === 'subpolicies' && Array.isArray(value)">
                  <h4>Subpolicies</h4>
                  <ul v-if="value && value.length">
                    <li v-for="sub in value" :key="sub.Identifier" class="subpolicy-status">
                      <div>
                        <span class="subpolicy-id">{{ sub.Identifier }}</span> :
                        <span class="subpolicy-name">{{ sub.SubPolicyName }}</span>
                        <span class="item-type-badge subpolicy-badge">Subpolicy</span>
                        <span
                          class="badge"
                          :class="{
                            approved: sub.approval?.approved === true || (selectedApproval.ApprovedNot === true || selectedApproval.ExtractedData?.Status === 'Approved'),
                            rejected: sub.approval?.approved === false && !(selectedApproval.ApprovedNot === true || selectedApproval.ExtractedData?.Status === 'Approved'),
                            pending: sub.approval?.approved === null && !sub.resubmitted && !(selectedApproval.ApprovedNot === true || selectedApproval.ExtractedData?.Status === 'Approved'),
                            resubmitted: sub.approval?.approved === null && sub.resubmitted && !(selectedApproval.ApprovedNot === true || selectedApproval.ExtractedData?.Status === 'Approved')
                          }"
                        >
                          {{
                            (sub.approval?.approved === true || (selectedApproval.ApprovedNot === true || selectedApproval.ExtractedData?.Status === 'Approved'))
                              ? 'Approved'
                              : sub.approval?.approved === false
                              ? 'Rejected'
                              : sub.resubmitted
                              ? 'Resubmitted'
                              : 'Pending'
                          }}
                        </span>
                      </div>
                      <div><strong>Description:</strong> {{ sub.Description }}</div>
                      <div><strong>Control:</strong> {{ sub.Control }}</div>
                      <div v-if="sub.approval?.approved === false">
                        <strong>Reason:</strong> {{ sub.approval?.remarks }}
                      </div>
                      <!-- Add these buttons inside the subpolicies view, under the approval buttons -->
                      <div class="subpolicy-actions">
                        <!-- Show approve/reject buttons only for assigned reviewers -->
                        <template v-if="canPerformReviewActions(selectedApproval) && (sub.Status === 'Under Review' || !sub.Status)">
                          <button 
                            @click="approveSubpolicy(sub)" 
                            class="approve-button"
                          >
                            <i class="fas fa-check"></i> Approve
                          </button>
                          <button 
                            @click="rejectSubpolicy(sub)" 
                            class="reject-button"
                            :class="{ 'has-pending-rejection': sub.pendingRejection }"
                          >
                            <i class="fas fa-times"></i> 
                            {{ sub.pendingRejection ? 'Rejection Pending' : 'Reject' }}
                          </button>
                        </template>
                        
                        <!-- For users (not reviewers), add edit button for rejected subpolicies -->
                        <template v-else-if="!canPerformReviewActions(selectedApproval) && sub.Status === 'Rejected'">
                          <button 
                            @click="openEditSubpolicyModal(sub)" 
                            class="edit-button"
                          >
                            <i class="fas fa-edit"></i> Edit & Resubmit
                          </button>
                        </template>
                        
                        <!-- Show message for policy creators -->
                        <template v-if="isCurrentUserCreator(selectedApproval) && (sub.Status === 'Under Review' || !sub.Status)">
                          <div class="creator-message-small">
                            <i class="fas fa-info-circle"></i>
                            <span>Under review</span>
                          </div>
                        </template>
                      </div>
                    </li>
                  </ul>
                </template>
              </div>
            </div>

            <!-- Add this inside the policy-details-content div -->
            <div v-if="selectedApproval && selectedApproval.PolicyId" class="policy-detail-row">
              <strong>Policy ID:</strong> <span>{{ getPolicyId(selectedApproval) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Edit Modal for Rejected Compliance -->
      <div v-if="showEditComplianceModal && editingCompliance" class="edit-policy-modal">
        <div class="edit-policy-content">
          <h3>Edit & Resubmit Compliance: {{ getPolicyId(editingCompliance) }}</h3>
          <button class="close-btn" @click="closeEditComplianceModal">&times;</button>
          
          <!-- Compliance fields -->
          <div>
            <label>Description:</label>
            <input v-model="editingCompliance.ExtractedData.ComplianceItemDescription" />
          </div>
          <div>
            <label>Criticality:</label>
            <select v-model="editingCompliance.ExtractedData.Criticality">
              <option>High</option>
              <option>Medium</option>
              <option>Low</option>
            </select>
          </div>
          <div>
            <label>Impact:</label>
            <input v-model="editingCompliance.ExtractedData.Impact" />
          </div>
          <div>
            <label>Probability:</label>
            <input v-model="editingCompliance.ExtractedData.Probability" />
          </div>
          <div>
            <label>Mitigation:</label>
            <textarea v-model="editingCompliance.ExtractedData.mitigation"></textarea>
          </div>
          <!-- Show rejection reason -->
          <div>
            <label>Rejection Reason:</label>
            <div class="rejection-reason">{{ editingCompliance.ExtractedData.compliance_approval?.remarks }}</div>
          </div>
          
          <button class="resubmit-btn" @click="resubmitCompliance(editingCompliance)">Resubmit for Review</button>
        </div>
      </div>

      <!-- Edit Modal for Rejected Policy -->
      <div v-if="showEditModal && editingPolicy" class="edit-policy-modal">
        <div class="edit-policy-content">
          <h3>Edit & Resubmit Policy: {{ getPolicyId(editingPolicy) }}</h3>
          <button class="close-btn" @click="closeEditModal">&times;</button>
          
          <!-- Show policy rejection reason if it exists -->
          <div v-if="getPolicyRejectionReason(editingPolicy)" class="rejection-reason-container">
            <div class="rejection-reason-header">
              <i class="fas fa-exclamation-triangle"></i> Policy Rejection Reason
            </div>
            <div class="rejection-reason-content">
              {{ getPolicyRejectionReason(editingPolicy) }}
            </div>
          </div>
          
          
          <!-- Main policy fields -->
          <div>
            <label>Scope:</label>
            <input v-model="editingPolicy.ExtractedData.Scope" />
          </div>
          <div>
            <label>Objective:</label>
            <input v-model="editingPolicy.ExtractedData.Objective" />
          </div>
          
          <!-- Policy Category fields -->
          <div>
            <label>Policy Type:</label>
            <select v-model="editingPolicy.ExtractedData.PolicyType" class="form-control" @change="handlePolicyTypeChange(editingPolicy)">
              <option value="">Select Type</option>
              <option v-for="type in policyTypeOptions" :key="type" :value="type">{{ type }}</option>
            </select>
          </div>
          <div>
            <label>Policy Category:</label>
            <select v-model="editingPolicy.ExtractedData.PolicyCategory" class="form-control" @change="handlePolicyCategoryChange(editingPolicy)">
              <option value="">Select Category</option>
              <option v-for="category in filteredPolicyCategories(editingPolicy.ExtractedData.PolicyType)" :key="category" :value="category">{{ category }}</option>
            </select>
          </div>
          <div>
            <label>Policy Sub Category:</label>
            <select v-model="editingPolicy.ExtractedData.PolicySubCategory" class="form-control">
              <option value="">Select Sub Category</option>
              <option v-for="subCategory in filteredPolicySubCategories(editingPolicy.ExtractedData.PolicyType, editingPolicy.ExtractedData.PolicyCategory)" :key="subCategory" :value="subCategory">{{ subCategory }}</option>
            </select>
          </div>
          
          <!-- Rejected Subpolicies Section -->
          <div class="edit-subpolicy-section" v-if="hasRejectedSubpolicies">
            <h4>Rejected Subpolicies</h4>
            
            <div v-for="sub in rejectedSubpoliciesInPolicy" :key="sub.Identifier" class="subpolicy-edit-item">
              <div class="subpolicy-edit-header">
                <span>{{ sub.Identifier }}: {{ sub.SubPolicyName }}</span>
                <span class="subpolicy-badge">Rejected</span>
              </div>
              
              <div class="subpolicy-edit-field">
                <label>Name:</label>
                <input v-model="sub.SubPolicyName" />
              </div>
              
              <div class="subpolicy-edit-field">
                <label>Description:</label>
                <textarea v-model="sub.Description"></textarea>
              </div>
              
              <div class="subpolicy-edit-field">
                <label>Control:</label>
                <textarea v-model="sub.Control"></textarea>
              </div>
              
              <div class="subpolicy-edit-field">
                <label>Rejection Reason:</label>
                <div class="rejection-reason">{{ sub.approval?.remarks }}</div>
              </div>
            </div>
          </div>
          
          <!-- Warning message for no changes -->
          <div v-if="!hasPolicyChanges" class="no-changes-warning">
            <div class="warning-icon">⚠️</div>
            <div class="warning-message">
              <strong>No Changes Detected</strong>
              <p>Please modify the policy before resubmitting for review.</p>
            </div>
          </div>
          
          <button 
            class="resubmit-btn" 
            :class="{ 'disabled': !hasPolicyChanges }"
            @click="resubmitPolicy(editingPolicy)"
            :disabled="!hasPolicyChanges">
            Resubmit for Review
          </button>
        </div>
      </div>

      <!-- Edit Modal for Rejected Subpolicy -->
      <div v-if="showEditSubpolicyModal" class="modal">
        <div class="modal-content edit-modal">
          <span class="close" @click="closeEditSubpolicyModal">&times;</span>
          <h2>Edit Rejected Subpolicy
            <span v-if="editingSubpolicy && (editingSubpolicy.Status === 'Rejected' || editingSubpolicy.approval?.approved === false)" 
                  class="version-tag reviewer-version">
              Version: {{ editingSubpolicy.reviewerVersion || 'R1' }}
            </span>
          </h2>
          <div v-if="editingSubpolicy">
            <div class="form-group">
              <label>Subpolicy Name:</label>
              <input type="text" v-model="editingSubpolicy.SubPolicyName" disabled />
            </div>
            <div class="form-group">
              <label>Identifier:</label>
              <input type="text" v-model="editingSubpolicy.Identifier" disabled />
            </div>
            
            <!-- Add this prominent rejection reason section -->
            <div v-if="editingSubpolicy.approval && editingSubpolicy.approval.remarks" class="rejection-reason-container">
              <div class="rejection-reason-header">
                <i class="fas fa-exclamation-triangle"></i> Rejection Reason
              </div>
              <div class="rejection-reason-content">
                {{ editingSubpolicy.approval.remarks }}
              </div>
            </div>
            
            <div class="form-group">
              <label>Description:</label>
              <textarea v-model="editingSubpolicy.Description" @input="trackChanges"></textarea>
            </div>
            <div class="form-group">
              <label>Control:</label>
              <textarea v-model="editingSubpolicy.Control" @input="trackChanges"></textarea>
            </div>
            
            <div v-if="hasChanges" class="changes-summary">
              <div class="changes-header">
                <i class="fas fa-exclamation-circle"></i> Changes detected
              </div>
              <div class="changes-content">
                <div v-if="editingSubpolicy.Description !== editingSubpolicy.originalDescription" class="change-item">
                  Description has been modified
                </div>
                <div v-if="editingSubpolicy.Control !== editingSubpolicy.originalControl" class="change-item">
                  Control has been modified
                </div>
              </div>
            </div>
            
            <div class="form-actions">
              <button 
                class="resubmit-btn" 
                @click="resubmitSubpolicy()" 
                :disabled="!hasChanges"
              >
                {{ hasChanges ? 'Resubmit with Changes' : 'Make changes to resubmit' }}
              </button>
              <button class="cancel-btn" @click="closeEditSubpolicyModal">Cancel</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Subpolicies Modal -->
      <div v-if="showSubpoliciesModal && selectedPolicyForSubpolicies" class="subpolicies-modal">
          <div class="subpolicies-modal-content">
            <h3>
              <span v-if="isReviewer">Subpolicies for {{ getPolicyId(selectedPolicyForSubpolicies) }}</span>
              <span v-else>Edit Rejected Subpolicies for {{ getPolicyId(selectedPolicyForSubpolicies) }}</span>
              
              <!-- Show appropriate version based on status -->
              <span v-if="selectedPolicyForSubpolicies.ApprovedNot === false || selectedPolicyForSubpolicies.ExtractedData?.Status === 'Rejected'"
                    class="version-pill reviewer-version">
                Version: {{ selectedPolicyForSubpolicies.reviewerVersion || 'R1' }}
              </span>
              <span v-else class="version-pill">
                Version: {{ selectedPolicyForSubpolicies.version || 'u1' }}
              </span>
            </h3>
            <button class="close-btn" @click="closeSubpoliciesModal">&times;</button>
            
            <!-- Filter to only show rejected subpolicies in user mode -->
            <div v-for="sub in filteredSubpolicies" :key="sub.Identifier" class="subpolicy-status" :class="{'resubmitted-item': sub.resubmitted}">
              <div class="subpolicy-header">
                <span class="subpolicy-id">{{ sub.Identifier }}</span>
                <span class="subpolicy-name">{{ sub.SubPolicyName }}</span>
                
                <!-- Show R version for rejected items, u version otherwise -->
                <span v-if="sub.Status === 'Rejected' || (sub.approval && sub.approval.approved === false)" 
                      class="version-tag reviewer-version">
                  Version: {{ sub.reviewerVersion || 'R1' }}
                </span>
                <span v-else class="version-tag">
                  Version: {{ sub.version || 'u1' }}
                </span>
              </div>

              <div class="subpolicy-content">
                <div><strong>Description:</strong> {{ sub.Description }}</div>
                <div><strong>Control:</strong> {{ sub.Control }}</div>
                
                <!-- Show rejection reason for rejected items -->
                <div v-if="sub.approval?.approved === false">
                  <strong>Rejection Reason:</strong> {{ sub.approval?.remarks }}
                </div>
                
                <!-- Show edit history for resubmitted items -->
                <div v-if="sub.resubmitted && isReviewer" class="edit-history">
                  <div class="edit-history-header">
                    <i class="fas fa-history"></i> Resubmitted with Changes
                  </div>
                  <div class="edit-history-content">
                    <div class="edit-field">
                      <div v-if="sub.previousVersion">
                        <div class="field-label">Original Description:</div>
                        <div class="field-previous">{{ sub.previousVersion.Description || 'Not available' }}</div>
                      </div>
                      <div class="field-current">
                        <div class="field-label">Updated Description:</div>
                        <div class="field-value">{{ sub.Description }}</div>
                      </div>
                    </div>
                    <div class="edit-field">
                      <div v-if="sub.previousVersion">
                        <div class="field-label">Original Control:</div>
                        <div class="field-previous">{{ sub.previousVersion.Control || 'Not available' }}</div>
                      </div>
                      <div class="field-current">
                        <div class="field-label">Updated Control:</div>
                        <div class="field-value">{{ sub.Control }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Show Approve/Reject buttons only for assigned reviewers -->
              <div v-if="canPerformReviewActions(selectedApproval) && (sub.approval?.approved === null || sub.approval?.approved === undefined)" class="subpolicy-actions">
                <button class="approve-btn" @click="approveSubpolicyFromModal(sub)">
                  <i class="fas fa-check"></i> Approve
                </button>
                <button 
                  class="reject-btn" 
                  @click="rejectSubpolicyFromModal(sub)"
                  :class="{ 'has-pending-rejection': sub.pendingRejection }"
                >
                  <i class="fas fa-times"></i> 
                  {{ sub.pendingRejection ? 'Rejection Pending' : 'Reject' }}
                </button>
              </div>
              
              <!-- Show message for policy creators -->
              <div v-if="isCurrentUserCreator(selectedApproval) && (sub.approval?.approved === null || sub.approval?.approved === undefined)" class="creator-message-small">
                <i class="fas fa-info-circle"></i>
                <span>Under review</span>
              </div>
              
              <!-- Edit form for rejected subpolicies -->
              <div v-if="sub.approval?.approved === false || sub.Status === 'Rejected'">
                <div v-if="sub.showEditForm">
                  <!-- Inline edit form -->
                  <div class="subpolicy-inline-edit">
                    <h4>Edit Rejected Subpolicy
                      <span class="version-tag reviewer-version">Version: {{ sub.reviewerVersion || 'R1' }}</span>
                    </h4>
                    <div>
                      <label>Name:</label>
                      <input v-model="sub.SubPolicyName" disabled />
                    </div>
                    <div>
                      <label>Description:</label>
                      <textarea v-model="sub.Description"></textarea>
                    </div>
                    <div>
                      <label>Control:</label>
                      <textarea v-model="sub.Control"></textarea>
                    </div>
                    <div>
                      <label>Rejection Reason:</label>
                      <div class="rejection-reason">
                        {{ sub.approval && sub.approval.remarks ? sub.approval.remarks : 'No rejection reason provided' }}
                      </div>
                    </div>
                    <div class="subpolicy-edit-actions">
                      <button class="resubmit-btn" @click="resubmitSubpolicyDirect(sub)">Resubmit for Review</button>
                      <button v-if="isReviewer" class="cancel-btn" @click="hideEditFormInline(sub)">Cancel</button>
                    </div>
                  </div>
                </div>
                <button v-else class="edit-btn" @click="showEditFormInline(sub)">Edit & Resubmit</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      

      <!-- Popup Modal -->
      <PopupModal />
    </div>

  <!-- Show only the reject modal when open -->
  <div v-if="showRejectModal" class="reject-modal">
    <div class="reject-modal-content">
      <h4>Rejection Reason</h4>
      <p>Please provide a reason for rejecting {{ rejectingType === 'policy' ? 'the policy' : 'subpolicy ' + rejectingSubpolicy?.Identifier }}</p>
      <textarea 
        v-model="rejectionComment" 
        class="rejection-comment" 
        placeholder="Enter your comments here..."></textarea>
      <div class="reject-modal-actions">
        <button class="cancel-btn" @click="cancelRejection">Cancel</button>
        <button class="confirm-btn" @click="confirmRejection">Confirm Rejection</button>
      </div>
    </div>
  </div>

  <!-- Review History Modal -->
  <ReviewHistoryModal
    v-if="showReviewHistoryModal"
    :policy-id="selectedPolicyId"
    :policy-name="selectedPolicyName"
    :current-status="selectedPolicyStatus"
    @close="closeReviewHistoryModal"
  />
</template>

<script>
import { API_ENDPOINTS } from '../../config/api.js'
import axios from 'axios'
import { PopupService } from '@/modules/popus/popupService'
import PopupModal from '@/modules/popus/PopupModal.vue'
import CollapsibleTable from '@/components/CollapsibleTable.vue'
import policyDataService from '@/services/policyService'
import ReviewHistoryModal from './ReviewHistoryModal.vue'

export default {
  name: 'PolicyApprover',
  components: {
    PopupModal,
    CollapsibleTable,
    ReviewHistoryModal
  },
  data() {
    return {
      approvals: [],
      selectedApproval: null,
      showDetails: false,
      showRejectModal: false,
      rejectingSubpolicy: null,
      rejectingType: '', // 'policy' or 'subpolicy'
      rejectionComment: '',
      rejectedPolicies: [],
      rejectedSubpolicies: [],
      showEditModal: false,
      editingPolicy: null,
      originalPolicyData: null, // Store original data for change detection
      showEditSubpolicyModal: false,
      editingSubpolicy: null,
      editingSubpolicyParent: null,
      showSubpoliciesModal: false,
      selectedPolicyForSubpolicies: null,
      showEditComplianceModal: false,
      editingCompliance: null,
      isReviewer: true, // Set based on user role, for testing
      isSubmittingReview: false, // Add loading state to prevent double submission
      reviewDecision: null, // Track whether user chose to approve or reject
      
      // Review History Modal
      showReviewHistoryModal: false,
      selectedPolicyId: null,
      selectedPolicyName: '',
      selectedPolicyStatus: '',
      
      // New RBAC and tab functionality
      activeTab: 'myTasks', // Default to My Tasks tab
      isAdministrator: false, // Will be set based on user role
      availableUsers: [], // List of users for administrator dropdown
      selectedUserId: null, // Currently selected user (for administrators)
      selectedUserInfo: null, // Information about selected user
      currentUserId: 2, // Current logged-in user ID
      currentUserName: '', // Current logged-in user name
      
      // Framework functionality
        frameworks: [], // List of frameworks
        selectedFrameworkId: '', // Currently selected framework
        sessionFrameworkId: null, // Framework ID from session (set from home page)
      myTasks: [], // Tasks assigned to user
      reviewerTasks: [], // Tasks where user is reviewer
      
      policyCategories: [], // Store all policy categories
      policyCategoriesMap: {}, // Structured map of policy categories
            // Collapsible Table Data
      tableHeaders: [     
        { key: 'policyName', label: 'Policy Name', sortable: true, width: '20%' },
        { key: 'type', label: 'Type', sortable: true, width: '10%' },
        { key: 'scope', label: 'Scope', sortable: true, width: '25%' },
        { key: 'createdBy', label: 'Created By', sortable: true, width: '15%' },
        { key: 'createdDate', label: 'Created Date', sortable: true, width: '15%' },
        { key: 'actions', label: 'Actions', sortable: false, width: '15%' }
      ],
      expandedSections: {
        pending: true,
        approved: true,
        rejected: true,
        'Rejected Policies (Edit & Resubmit)': true
      },
      collapsiblePagination: {
        pending: { currentPage: 1, pageSize: 6 },
        approved: { currentPage: 1, pageSize: 6 },
        rejected: { currentPage: 1, pageSize: 6 }
      },
      paginationUpdateTrigger: 0 // Reactive trigger for pagination updates
    }
  },
  async mounted() {
    console.log('PolicyApprover component mounted');
    console.log('Initial data state:', {
      isAdministrator: this.isAdministrator,
      currentUserId: this.currentUserId,
      selectedUserId: this.selectedUserId,
      availableUsers: this.availableUsers
    });
    
    // Clear framework selection from session on mount to show all frameworks by default
    // This ensures fresh login always shows all frameworks
    await this.clearFrameworkSelection();
    
    // First fetch frameworks
    await this.fetchFrameworks();
    
    // Then initialize user (which will load tasks without framework filter)
    await this.initializeUser();
  },
  watch: {
    // Watch for changes in isReviewer and fetch appropriate data
    isReviewer(newVal) {
      if (newVal) {
        // If switched to reviewer mode
        this.fetchPolicies();
        this.fetchRejectedPolicies();
      } else {
        // If switched to user mode
        this.fetchRejectedSubpolicies();
      }
    }
  },
  methods: {
    // Push notification method
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

    // Initialize user and check role
    async initializeUser() {
      try {
        console.log('Initializing user and checking role...');
        
        // Try to get user info from storage first for faster loading
        await this.loadUserFromStorage();
        
        // Get current user role
        const response = await axios.get(API_ENDPOINTS.USER_ROLE);
        console.log('User role API response:', response.data);
        
        if (response.data.success) {
          this.currentUserId = response.data.user_id;
          this.currentUserName = response.data.username || response.data.user_name || '';
          
          // Store user info for fallback
          this.storeUserInfo(response.data);
          
          // Check specifically for "GRC Administrator" role
          const userRole = response.data.role;
          console.log('User role received:', userRole);
          
          // Only GRC Administrator should see the user dropdown
          this.isAdministrator = userRole === 'GRC Administrator';
          
          console.log('Is GRC Administrator:', this.isAdministrator);
          
          if (this.isAdministrator) {
            console.log('User is GRC Administrator, fetching all users for dropdown...');
            // Fetch all users for dropdown
            await this.fetchUsers();
            
            // Set default user to current logged-in administrator
            this.selectedUserId = this.currentUserId;
            this.selectedUserInfo = {
              UserId: this.currentUserId,
              UserName: this.currentUserName,
              Role: userRole
            };
            console.log('Setting default user for administrator to current user:', this.currentUserName);
            // Load tasks for the current administrator
            await this.loadUserTasks();
          } else {
            console.log('User is not GRC Administrator, setting selected user to current user');
            // Set selected user to current user for non-administrators
            this.selectedUserId = this.currentUserId;
            
            // Load tasks for the current user
            await this.loadUserTasks();
          }
          
          this.fetchRejectedPolicies();
          this.fetchPolicyTypes();
        } else {
          console.error('User role API did not return success:', response.data);
          // Use fallback user data if available
          if (this.currentUserId && this.currentUserName) {
            console.log('Using fallback user data due to API error');
            this.isAdministrator = false; // Default to non-admin for safety
            this.selectedUserId = this.currentUserId;
            await this.loadUserTasks();
          } else {
            PopupService.error('Could not determine user role. Please contact administrator.', 'User Role Error');
          }
        }
      } catch (error) {
        console.error('Error initializing user:', error);
        
        // Use fallback user data if available
        if (this.currentUserId && this.currentUserName) {
          console.log('Using fallback user data due to initialization error');
          this.isAdministrator = false; // Default to non-admin for safety
          this.selectedUserId = this.currentUserId;
          await this.loadUserTasks();
        } else {
          PopupService.error('Could not initialize user. Please refresh the page and try again.', 'User Initialization Error');
        }
      }
    },

    // Load user info from storage for faster loading
    async loadUserFromStorage() {
      try {
        const storedUser = localStorage.getItem('user') || sessionStorage.getItem('user');
        if (storedUser) {
          const userData = JSON.parse(storedUser);
          this.currentUserId = userData.UserId || userData.user_id;
          this.currentUserName = userData.UserName || userData.username || userData.user_name;
          console.log('Loaded user from storage:', { userId: this.currentUserId, userName: this.currentUserName });
        }
      } catch (error) {
        console.error('Error loading user from storage:', error);
      }
    },

    // Store user info for fallback
    storeUserInfo(userData) {
      try {
        const userInfo = {
          UserId: userData.user_id,
          UserName: userData.username || userData.user_name,
          Role: userData.role
        };
        localStorage.setItem('user', JSON.stringify(userInfo));
        sessionStorage.setItem('user', JSON.stringify(userInfo));
      } catch (error) {
        console.error('Error storing user info:', error);
      }
    },

    // Fetch all users for administrator dropdown
    async fetchUsers() {
      try {
        console.log('Fetching users for dropdown from RBAC...');
        const response = await axios.get(API_ENDPOINTS.USERS_FOR_DROPDOWN);
        console.log('Users API response:', response.data);
        
        if (Array.isArray(response.data)) {
          this.availableUsers = response.data;
        } else if (response.data && response.data.success && Array.isArray(response.data.data)) {
          this.availableUsers = response.data.data;
        } else {
          this.availableUsers = response.data || [];
        }
        
        console.log('Available users loaded:', this.availableUsers.length, 'users');
        console.log('Users:', this.availableUsers);
        
        // If no users found, try fallback mechanism
        if (this.availableUsers.length === 0) {
          console.warn('No users found in RBAC table, trying fallback...');
          await this.fetchUsersFallback();
        }
      } catch (error) {
        console.error('Error fetching users:', error);
        console.log('Trying fallback mechanism...');
        await this.fetchUsersFallback();
      }
    },

    // Fallback method for fetching users
    async fetchUsersFallback() {
      try {
        console.log('Using fallback method to fetch users...');
        
        // Try to get current user info from localStorage or sessionStorage
        const storedUser = localStorage.getItem('user') || sessionStorage.getItem('user');
        let fallbackUsers = [];
        
        if (storedUser) {
          try {
            const userData = JSON.parse(storedUser);
            fallbackUsers = [{
              UserId: userData.UserId || this.currentUserId,
              UserName: userData.UserName || this.currentUserName,
              Role: userData.Role || 'User'
            }];
          } catch (e) {
            console.error('Error parsing stored user data:', e);
          }
        }
        
        // If still no users, create a default user entry
        if (fallbackUsers.length === 0 && this.currentUserId && this.currentUserName) {
          fallbackUsers = [{
            UserId: this.currentUserId,
            UserName: this.currentUserName,
            Role: 'User'
          }];
        }
        
        this.availableUsers = fallbackUsers;
        console.log('Fallback users loaded:', this.availableUsers);
        
        if (this.availableUsers.length === 0) {
          console.error('No users available even with fallback');
          PopupService.error('Could not load users list. Please refresh the page and try again.', 'Users Error');
        } else {
          PopupService.warning('Using limited user data due to API issues. Some features may be restricted.', 'Limited Data');
        }
      } catch (fallbackError) {
        console.error('Error in fallback method:', fallbackError);
        this.availableUsers = [];
        PopupService.error('Could not load users list. Please contact administrator.', 'Users Error');
      }
    },

    // Handle user selection change (for administrators)
    async onUserChange() {
      console.log('User selection changed to:', this.selectedUserId);
      console.log('Available users:', this.availableUsers);
      
      if (this.selectedUserId) {
        // Find user info
        this.selectedUserInfo = this.availableUsers.find(u => u.UserId == this.selectedUserId);
        console.log('Selected user info:', this.selectedUserInfo);
        
        if (this.selectedUserInfo) {
          console.log(`Loading tasks for user: ${this.selectedUserInfo.UserName} (ID: ${this.selectedUserId})`);
          // Load tasks for selected user
          await this.loadUserTasks();
          // Also fetch rejected policies for the selected user
          await this.fetchRejectedPolicies();
        } else {
          console.warn('Could not find user info for selected user ID:', this.selectedUserId);
        }
      } else {
        console.log('No user selected, clearing user info and tasks');
        this.selectedUserInfo = null;
        this.myTasks = [];
        this.reviewerTasks = [];
        this.rejectedPolicies = [];
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

    // Framework-related methods
    async fetchFrameworks() {
      try {
        console.log('🔍 DEBUG: Checking for cached frameworks in PolicyApprover...')

        if (!window.policyDataFetchPromise && !policyDataService.hasFrameworksListCache()) {
          console.log('🚀 DEBUG: Starting policy prefetch from PolicyApprover (user navigated directly)...')
          window.policyDataFetchPromise = policyDataService.fetchAllPolicyData()
        }

        if (window.policyDataFetchPromise) {
          console.log('⏳ DEBUG: Waiting for policy prefetch to complete in PolicyApprover...')
          try {
            await window.policyDataFetchPromise
            console.log('✅ DEBUG: Policy prefetch completed for PolicyApprover')
          } catch (prefetchError) {
            console.warn('⚠️ DEBUG: Policy prefetch failed in PolicyApprover, will fetch directly', prefetchError)
          }
        }

        if (policyDataService.hasFrameworksListCache()) {
          console.log('✅ DEBUG: Using cached frameworks in PolicyApprover')
          const cachedFrameworks = policyDataService.getFrameworksList() || []
          this.frameworks = cachedFrameworks.map(fw => ({
            id: fw.FrameworkId || fw.id,
            name: fw.FrameworkName || fw.name
          }))

          // Framework selection is cleared on mount, so we don't restore it here
          return
        }

        console.log('⚠️ DEBUG: No cached frameworks, fetching via API in PolicyApprover...')
        const response = await axios.get(API_ENDPOINTS.FRAMEWORKS)
        this.frameworks = response.data.map(fw => ({
          id: fw.FrameworkId,
          name: fw.FrameworkName
        }))

        // Update cache for future loads
        policyDataService.setFrameworksList(response.data)
        
        console.log('✅ DEBUG: Frameworks loaded:', this.frameworks)
        // Framework selection is cleared on mount, so we don't restore it here
      } catch (error) {
        console.error('❌ DEBUG: Error fetching frameworks:', error)
      }
    },

    // Clear framework selection from session (called on mount to ensure fresh start)
    async clearFrameworkSelection() {
      try {
        console.log('🧹 DEBUG: Clearing framework selection from session on mount...')
        // Clear local state
        this.selectedFrameworkId = ''
        this.sessionFrameworkId = null
        
        // Clear from session storage
        await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
          frameworkId: null
        })
        console.log('✅ DEBUG: Framework selection cleared from session successfully')
      } catch (error) {
        console.error('❌ DEBUG: Error clearing framework selection from session:', error)
        // Even if clearing fails, ensure local state is cleared
        this.selectedFrameworkId = ''
        this.sessionFrameworkId = null
      }
    },
    
    // Check for selected framework from session and set it as default
    // NOTE: This method is kept for backward compatibility but is not called on mount
    // Framework selection is now cleared on mount to show all frameworks by default
    async checkSelectedFrameworkFromSession() {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in PolicyApprover...')
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
        console.log('📊 DEBUG: Selected framework response:', response.data)
        
        if (response.data && response.data.success) {
          // Check if a framework is selected (not null)
          if (response.data.frameworkId) {
          const sessionFrameworkId = response.data.frameworkId
          console.log('✅ DEBUG: Found selected framework in session:', sessionFrameworkId)
          
          // Check if this framework exists in our loaded frameworks
          const frameworkExists = this.frameworks.find(f => f.id.toString() === sessionFrameworkId.toString())
          
            if (frameworkExists) {
              // Store the session framework ID for filtering
              this.sessionFrameworkId = sessionFrameworkId
              this.selectedFrameworkId = sessionFrameworkId.toString()
              console.log('✅ DEBUG: Set sessionFrameworkId from session:', this.sessionFrameworkId)
              console.log('✅ DEBUG: Set selectedFrameworkId from session:', this.selectedFrameworkId)
              console.log('✅ DEBUG: Framework exists in loaded frameworks:', frameworkExists.name)
            } else {
              console.log('⚠️ DEBUG: Framework from session not found in loaded frameworks')
              console.log('📋 DEBUG: Available frameworks:', this.frameworks.map(f => ({ id: f.id, name: f.name })))
              // Clear the session framework ID since it doesn't exist
              this.sessionFrameworkId = null
            }
          } else {
            // "All Frameworks" is selected (frameworkId is null)
            console.log('ℹ️ DEBUG: No framework selected in session (All Frameworks selected)')
            console.log('🌐 DEBUG: Clearing framework selection to show all frameworks')
            this.sessionFrameworkId = null
            this.selectedFrameworkId = null
            }
        } else {
          console.log('ℹ️ DEBUG: No framework found in session')
          this.sessionFrameworkId = null
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework from session:', error)
        this.sessionFrameworkId = null
      }
    },

    // Handle framework selection change
    async onFrameworkChange() {
      if (this.selectedFrameworkId) {
        // Save the selected framework to session
        try {
          const userId = localStorage.getItem('user_id') || 'default_user'
          console.log('🔍 DEBUG: Saving framework to session in PolicyApprover:', this.selectedFrameworkId)
          
          const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
            frameworkId: this.selectedFrameworkId,
            userId: userId
          })
          
          if (response.data && response.data.success) {
            console.log('✅ DEBUG: Framework saved to session successfully in PolicyApprover')
            console.log('🔑 DEBUG: Session key:', response.data.sessionKey)
          } else {
            console.error('❌ DEBUG: Failed to save framework to session in PolicyApprover')
          }
        } catch (error) {
          console.error('❌ DEBUG: Error saving framework to session in PolicyApprover:', error)
        }
        
        // Refresh data with the selected framework
        await this.refreshData()
      }
    },

    // Get selected framework name for display
    getSelectedFrameworkName() {
      if (!this.selectedFrameworkId) return '';
      
      const selectedFramework = this.frameworks.find(f => f.id.toString() === this.selectedFrameworkId.toString());
      return selectedFramework ? selectedFramework.name : `Framework ${this.selectedFrameworkId}`;
    },

    // Clear all filters
    async clearFilters() {
      console.log('🧹 Clearing all filters in PolicyApprover...')
      console.log('  Before clear - selectedFrameworkId:', this.selectedFrameworkId)
      console.log('  Before clear - sessionFrameworkId:', this.sessionFrameworkId)
      
      this.selectedFrameworkId = ''
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
      
      console.log('  After clear - selectedFrameworkId:', this.selectedFrameworkId)
      console.log('  After clear - sessionFrameworkId:', this.sessionFrameworkId)
      console.log('✅ All filters cleared')
      
      // Reload tasks without framework filter
      await this.loadUserTasks()
      
      // Force Vue to re-render
      this.$forceUpdate()
    },

    // Switch between tabs
    switchTab(tab) {
      this.activeTab = tab;
    },
    
    // Navigate to All Policies page
    navigateToAllPolicies() {
      this.$router.push('/policies-list/all');
    },

    // Review History Modal methods
    showReviewHistory(policyId, policyName, currentStatus) {
      this.selectedPolicyId = policyId;
      this.selectedPolicyName = policyName;
      this.selectedPolicyStatus = currentStatus;
      this.showReviewHistoryModal = true;
    },

    closeReviewHistoryModal() {
      this.showReviewHistoryModal = false;
      this.selectedPolicyId = null;
      this.selectedPolicyName = '';
      this.selectedPolicyStatus = '';
    },

    // Load tasks for the selected user
    async loadUserTasks() {
      const targetUserId = this.selectedUserId || this.currentUserId;
      
      console.log('Loading user tasks for user ID:', targetUserId);
      console.log('Selected user ID:', this.selectedUserId);
      console.log('Current user ID:', this.currentUserId);
      console.log('Is Administrator:', this.isAdministrator);
      
      // If administrator and no user selected, don't load any tasks
      if (this.isAdministrator && !this.selectedUserId) {
        console.log('Administrator with no user selected - clearing tasks');
        this.myTasks = [];
        this.reviewerTasks = [];
        return;
      }
      
      try {
        // Fetch My Tasks (where user is the creator/owner)
        await this.fetchMyTasks(targetUserId);
        
        // Fetch Reviewer Tasks (where user is the reviewer)
        await this.fetchReviewerTasks(targetUserId);
      } catch (error) {
        console.error('Error loading user tasks:', error);
        this.myTasks = [];
        this.reviewerTasks = [];
      }
    },

    // Fetch My Tasks (created by user)
    async fetchMyTasks(userId) {
      try {
        // Add framework filtering parameter if a framework is selected (use sessionFrameworkId if available)
        const params = {};
        const frameworkToFilter = this.sessionFrameworkId || this.selectedFrameworkId;
        
        console.log('🔍 DEBUG: fetchMyTasks called with userId:', userId);
        console.log('🔍 DEBUG: sessionFrameworkId:', this.sessionFrameworkId);
        console.log('🔍 DEBUG: selectedFrameworkId:', this.selectedFrameworkId);
        console.log('🔍 DEBUG: frameworkToFilter:', frameworkToFilter);
        
        if (frameworkToFilter) {
          params.framework_id = frameworkToFilter;
          console.log('🔍 Adding framework filter to policy my tasks:', frameworkToFilter);
          console.log('🔍 Framework filter type:', typeof frameworkToFilter);
          console.log('🔍 Full params object:', params);
        } else {
          console.log('⚠️ DEBUG: No framework filter applied - frameworkToFilter is:', frameworkToFilter);
        }
        
        // Add a note about which framework we're filtering by
        if (frameworkToFilter) {
          const frameworkName = this.frameworks.find(f => f.id.toString() === frameworkToFilter.toString())?.name || `Framework ${frameworkToFilter}`;
          console.log(`🔍 DEBUG: Filtering by framework: ${frameworkName} (ID: ${frameworkToFilter})`);
        }
        
        // Fetch policy approvals where user is the creator
        const response = await axios.get(API_ENDPOINTS.POLICY_APPROVALS_USER(userId), { params });
        
        let approvalsData;
        if (response.data.success && response.data.data) {
          approvalsData = response.data.data;
        } else if (Array.isArray(response.data)) {
          approvalsData = response.data;
        } else {
          approvalsData = [];
        }
        
        console.log('🔍 DEBUG: My Tasks API Response:', {
          frameworkToFilter,
          responseData: response.data,
          approvalsDataLength: approvalsData.length,
          firstFewApprovals: approvalsData.slice(0, 3),
          url: API_ENDPOINTS.POLICY_APPROVALS_USER(userId),
          params: params
        });

        this.myTasks = approvalsData.map(approval => {
          // Extract rejection reason from approval data (kept for potential future use)
          let rejectionReason = null;
          if (approval.ExtractedData) {
            if (approval.ExtractedData.rejection_reason) {
              rejectionReason = approval.ExtractedData.rejection_reason;
            } else if (approval.ExtractedData.policy_approval?.remarks) {
              rejectionReason = approval.ExtractedData.policy_approval.remarks;
            } else if (approval.ExtractedData.cascading_rejection) {
              rejectionReason = `Cascading rejection due to ${approval.ExtractedData.rejected_subpolicy_name || 'subpolicy'} rejection`;
            } else if (approval.ExtractedData.subpolicies && Array.isArray(approval.ExtractedData.subpolicies)) {
              // Check for subpolicy rejection reasons
              for (const subpolicy of approval.ExtractedData.subpolicies) {
                if (subpolicy.approval?.remarks && subpolicy.approval.remarks.trim() !== '') {
                  rejectionReason = `Subpolicy ${subpolicy.Identifier || subpolicy.SubPolicyId} rejection: ${subpolicy.approval.remarks}`;
                  break;
                }
              }
            }
          }
          
          return {
            ApprovalId: approval.ApprovalId,
            PolicyId: approval.PolicyId,
            ExtractedData: approval.ExtractedData,
            ApprovedNot: approval.ApprovedNot,
            ApprovedDate: approval.ApprovedDate,
            version: approval.Version,
            UserId: approval.UserId,
            ReviewerId: approval.ReviewerId,
            dbStatus: null,
            rejectionReason: rejectionReason
          };
        });

        // Get policy status from database
        await this.updateTasksWithPolicyStatus(this.myTasks);
      } catch (error) {
        console.error('Error fetching my tasks:', error);
        this.myTasks = [];
      }
    },

    // Fetch Reviewer Tasks (where user is reviewer)
    async fetchReviewerTasks(userId) {
      try {
        // Add framework filtering parameter if a framework is selected (use sessionFrameworkId if available)
        const params = {};
        const frameworkToFilter = this.sessionFrameworkId || this.selectedFrameworkId;
        
        console.log('🔍 DEBUG: fetchReviewerTasks called with userId:', userId);
        console.log('🔍 DEBUG: sessionFrameworkId:', this.sessionFrameworkId);
        console.log('🔍 DEBUG: selectedFrameworkId:', this.selectedFrameworkId);
        console.log('🔍 DEBUG: frameworkToFilter:', frameworkToFilter);
        
        if (frameworkToFilter) {
          params.framework_id = frameworkToFilter;
          console.log('🔍 Adding framework filter to policy reviewer tasks:', frameworkToFilter);
          console.log('🔍 Framework filter type:', typeof frameworkToFilter);
          console.log('🔍 Full params object:', params);
        } else {
          console.log('⚠️ DEBUG: No framework filter applied to reviewer tasks - frameworkToFilter is:', frameworkToFilter);
        }
        
        // Add a note about which framework we're filtering by
        if (frameworkToFilter) {
          const frameworkName = this.frameworks.find(f => f.id.toString() === frameworkToFilter.toString())?.name || `Framework ${frameworkToFilter}`;
          console.log(`🔍 DEBUG: Filtering reviewer tasks by framework: ${frameworkName} (ID: ${frameworkToFilter})`);
        }
        
        // Fetch policy approvals where user is the reviewer
        const response = await axios.get(API_ENDPOINTS.POLICY_APPROVALS_REVIEWER(userId), { params });
        
        let approvalsData;
        if (response.data.success && response.data.data) {
          approvalsData = response.data.data;
        } else if (Array.isArray(response.data)) {
          approvalsData = response.data;
        } else {
          approvalsData = [];
        }
        
        console.log('🔍 DEBUG: Reviewer Tasks API Response:', {
          frameworkToFilter,
          responseData: response.data,
          approvalsDataLength: approvalsData.length,
          firstFewApprovals: approvalsData.slice(0, 3)
        });

        this.reviewerTasks = approvalsData.map(approval => {
          // Extract rejection reason from approval data (kept for potential future use)
          let rejectionReason = null;
          if (approval.ExtractedData) {
            if (approval.ExtractedData.rejection_reason) {
              rejectionReason = approval.ExtractedData.rejection_reason;
            } else if (approval.ExtractedData.policy_approval?.remarks) {
              rejectionReason = approval.ExtractedData.policy_approval.remarks;
            } else if (approval.ExtractedData.cascading_rejection) {
              rejectionReason = `Cascading rejection due to ${approval.ExtractedData.rejected_subpolicy_name || 'subpolicy'} rejection`;
            } else if (approval.ExtractedData.subpolicies && Array.isArray(approval.ExtractedData.subpolicies)) {
              // Check for subpolicy rejection reasons
              for (const subpolicy of approval.ExtractedData.subpolicies) {
                if (subpolicy.approval?.remarks && subpolicy.approval.remarks.trim() !== '') {
                  rejectionReason = `Subpolicy ${subpolicy.Identifier || subpolicy.SubPolicyId} rejection: ${subpolicy.approval.remarks}`;
                  break;
                }
              }
            }
          }
          
          return {
            ApprovalId: approval.ApprovalId,
            PolicyId: approval.PolicyId,
            ExtractedData: approval.ExtractedData,
            ApprovedNot: approval.ApprovedNot,
            ApprovedDate: approval.ApprovedDate,
            version: approval.Version,
            UserId: approval.UserId,
            ReviewerId: approval.ReviewerId,
            dbStatus: null,
            rejectionReason: rejectionReason
          };
        });

        // Get policy status from database
        await this.updateTasksWithPolicyStatus(this.reviewerTasks);
      } catch (error) {
        console.error('Error fetching reviewer tasks:', error);
        // Fallback to existing behavior for backwards compatibility
        this.fetchPolicies();
      }
    },

    // Helper method to update tasks with policy status
    async updateTasksWithPolicyStatus(tasks) {
      const policyIds = tasks
        .filter(task => task.PolicyId)
        .map(task => typeof task.PolicyId === 'object' ? task.PolicyId.PolicyId : task.PolicyId);
      
      if (policyIds.length > 0) {
                    const fetchPromises = policyIds.map(policyId => 
              axios.get(API_ENDPOINTS.POLICY(policyId))
                .then(policyResponse => {
              return {
                policyId: policyId,
                status: policyResponse.data.Status
              };
            })
            .catch(error => {
              console.error(`Error fetching policy ${policyId}:`, error);
              return { policyId: policyId, status: null };
            })
        );
        
        const policyStatuses = await Promise.all(fetchPromises);
        
        // Update tasks with database status
        policyStatuses.forEach(policyStatus => {
          const task = tasks.find(t => {
            const taskPolicyId = typeof t.PolicyId === 'object' ? t.PolicyId.PolicyId : t.PolicyId;
            return taskPolicyId === policyStatus.policyId;
          });
          
          if (task) {
            task.dbStatus = policyStatus.status;
          }
        });
      }
    },

    // Update the method to fetch policies and policy approvals
    fetchPolicies() {
      console.log('Fetching policy approvals for reviewer...');
      axios.get(API_ENDPOINTS.POLICY_APPROVALS_REVIEWER())
        .then(response => {
          console.log('Policy approvals response:', response.data);
          
          // Handle both response formats: direct array or success wrapper
          let approvalsData;
          if (response.data.success && response.data.data) {
            approvalsData = response.data.data;
          } else if (Array.isArray(response.data)) {
            approvalsData = response.data;
          } else {
            console.error('Unexpected response format:', response.data);
            return;
          }
          
          // Create initial approvals array from policy approvals data
          const approvals = approvalsData.map(approval => {
            // Extract rejection reason from approval data
            let rejectionReason = null;
            if (approval.ExtractedData) {
              if (approval.ExtractedData.rejection_reason) {
                rejectionReason = approval.ExtractedData.rejection_reason;
              } else if (approval.ExtractedData.policy_approval?.remarks) {
                rejectionReason = approval.ExtractedData.policy_approval.remarks;
              } else if (approval.ExtractedData.cascading_rejection) {
                rejectionReason = `Cascading rejection due to ${approval.ExtractedData.rejected_subpolicy_name || 'subpolicy'} rejection`;
              } else if (approval.ExtractedData.subpolicies && Array.isArray(approval.ExtractedData.subpolicies)) {
                // Check for subpolicy rejection reasons
                for (const subpolicy of approval.ExtractedData.subpolicies) {
                  if (subpolicy.approval?.remarks && subpolicy.approval.remarks.trim() !== '') {
                    rejectionReason = `Subpolicy ${subpolicy.Identifier || subpolicy.SubPolicyId} rejection: ${subpolicy.approval.remarks}`;
                    break;
                  }
                }
              }
            }
            
            return {
              ApprovalId: approval.ApprovalId,
              PolicyId: approval.PolicyId,
              ExtractedData: approval.ExtractedData,
              ApprovedNot: approval.ApprovedNot,
              ApprovedDate: approval.ApprovedDate,
              version: approval.Version,
              UserId: approval.UserId,
              ReviewerId: approval.ReviewerId,
              dbStatus: null, // Will be populated from database table
              rejectionReason: rejectionReason
            };
          });
          
          // Get policy IDs to fetch their direct status from database
          const policyIds = approvals
            .filter(approval => approval.PolicyId)
            .map(approval => typeof approval.PolicyId === 'object' ? approval.PolicyId.PolicyId : approval.PolicyId);
          
          if (policyIds.length > 0) {
            // Fetch the actual policy status from the database table for all policies
            const fetchPromises = policyIds.map(policyId => 
              axios.get(API_ENDPOINTS.POLICY(policyId))
                .then(policyResponse => {
                  return {
                    policyId: policyId,
                    status: policyResponse.data.Status
                  };
                })
                .catch(error => {
                  console.error(`Error fetching policy ${policyId}:`, error);
                  return { policyId: policyId, status: null };
                })
            );
            
            Promise.all(fetchPromises)
              .then(policyStatuses => {
                // Update the approvals with database status
                policyStatuses.forEach(policyStatus => {
                  const approval = approvals.find(a => {
                    const approvalPolicyId = typeof a.PolicyId === 'object' ? a.PolicyId.PolicyId : a.PolicyId;
                    return approvalPolicyId === policyStatus.policyId;
                  });
                  
                  if (approval) {
                    approval.dbStatus = policyStatus.status;
                    
                    // Update ExtractedData Status as well to ensure consistency
                    if (approval.ExtractedData && policyStatus.status) {
                      approval.ExtractedData.Status = policyStatus.status;
                    }
                  }
                });
                
                this.approvals = approvals;
                console.log('Updated approvals with database status:', this.approvals);
              })
              .catch(error => {
                console.error('Error updating policy statuses:', error);
                this.approvals = approvals;
              });
          } else {
            this.approvals = approvals;
          }
        })
        .catch(error => {
          console.error('Error fetching policy approvals:', error);
        });
    },
    // Remove the fetchLatestApprovalForPolicy method as it's causing errors
    
    openApprovalDetails(approval) {
      // Get the policy ID
      const policyId = this.getPolicyId(approval);

      // First, fetch the policy's current database status to determine which version to fetch
          axios.get(API_ENDPOINTS.POLICY(policyId))
            .then(policyResponse => {
              const dbStatus = policyResponse.data.Status;
              console.log(`Policy database status: ${dbStatus}`);
          
          // Determine which version to fetch based on policy status
          let versionEndpoint;
          if (dbStatus === 'Rejected') {
            // For rejected policies, fetch the latest reviewer version (r1, r2, etc.)
            versionEndpoint = API_ENDPOINTS.POLICY_REVIEWER_VERSION(policyId);
            console.log('Policy is rejected, fetching latest reviewer version...');
          } else {
            // For other statuses, fetch the latest user version (u1, u2, etc.)
            versionEndpoint = API_ENDPOINTS.POLICY_VERSION(policyId);
            console.log('Policy is not rejected, fetching latest user version...');
          }
          
          // Fetch the appropriate version
          axios.get(versionEndpoint)
            .then(versionResponse => {
              const policyVersion = versionResponse.data.version || 'u1';
              console.log(`Fetched policy version: ${policyVersion} for status: ${dbStatus}`);
              
              // Now fetch the latest policy approval with this version
              axios.get(API_ENDPOINTS.POLICY_APPROVALS_LATEST(policyId))
                .then(approvalResponse => {
                  console.log('Latest policy approval:', approvalResponse.data);
                  
                  // If we got data and it has ExtractedData, use it
                  if (approvalResponse.data && approvalResponse.data.ExtractedData) {
                    const latestApproval = approvalResponse.data;
                    
                    // Create a complete approval object with the latest data
                    const updatedApproval = {
                      ...approval,
                      ...latestApproval,
                      dbStatus: dbStatus,
                      version: policyVersion,
                      ExtractedData: latestApproval.ExtractedData
                    };
                    
                    // Update ExtractedData Status to match database status for consistency
                    if (updatedApproval.ExtractedData && dbStatus) {
                      updatedApproval.ExtractedData.Status = dbStatus;
                    }
                    
                    // Now get subpolicy versions if there are any
                    if (updatedApproval.ExtractedData && updatedApproval.ExtractedData.subpolicies && updatedApproval.ExtractedData.subpolicies.length > 0) {
                      console.log('Fetching versions for', updatedApproval.ExtractedData.subpolicies.length, 'subpolicies');
                      
                      const promises = updatedApproval.ExtractedData.subpolicies.map(sub => {
                        if (sub.SubPolicyId) {
                          // First fetch subpolicy status to determine which version endpoint to use
                          return axios.get(API_ENDPOINTS.SUBPOLICIES(sub.SubPolicyId))
                            .then(subpolicyResponse => {
                              const subStatus = subpolicyResponse.data.Status;
                              sub.Status = subStatus;
                              
                              // Determine which version endpoint to use based on subpolicy status
                              let subVersionEndpoint;
                              if (subStatus === 'Rejected') {
                                // For rejected subpolicies, fetch the latest reviewer version
                                subVersionEndpoint = API_ENDPOINTS.SUBPOLICY_REVIEWER_VERSION(sub.SubPolicyId);
                                console.log(`Subpolicy ${sub.SubPolicyId} is rejected, fetching reviewer version...`);
                              } else {
                                // For other statuses, fetch the latest user version
                                subVersionEndpoint = API_ENDPOINTS.SUBPOLICY_VERSION(sub.SubPolicyId);
                                console.log(`Subpolicy ${sub.SubPolicyId} is not rejected, fetching user version...`);
                              }
                              
                              // Fetch the appropriate version
                              return axios.get(subVersionEndpoint)
                            .then(subVersionResponse => {
                                  const subVersion = subVersionResponse.data.version || 'u1';
                                  console.log(`Subpolicy ${sub.SubPolicyId} version: ${subVersion} for status: ${subStatus}`);
                                  sub.version = subVersion;
                              return sub;
                            })
                            .catch(err => {
                              console.error(`Error fetching version for subpolicy ${sub.SubPolicyId}:`, err);
                                  sub.version = 'u1'; // Default fallback
                                  return sub;
                                });
                            })
                            .catch(err => {
                              console.error(`Error fetching subpolicy status for ${sub.SubPolicyId}:`, err);
                              sub.version = 'u1'; // Default fallback
                              return sub;
                            });
                        } else {
                          sub.version = 'u1'; // Default for subpolicies without ID
                          return Promise.resolve(sub);
                        }
                      });
                      
                      // Wait for all version fetching to complete
                      Promise.all(promises)
                        .then(updatedSubpolicies => {
                          updatedApproval.ExtractedData.subpolicies = updatedSubpolicies;
                          this.completeApprovalSelection(updatedApproval);
                        })
                        .catch(error => {
                          console.error('Error updating subpolicy versions:', error);
                          this.completeApprovalSelection(updatedApproval);
                        });
                    } else {
                      // No subpolicies to process
                      this.completeApprovalSelection(updatedApproval);
                    }
                  } else {
                    // If we couldn't get the latest approval data, fall back to using existing data with just the version updated
                    const updatedApproval = JSON.parse(JSON.stringify(approval));
                    updatedApproval.version = policyVersion;
                    updatedApproval.dbStatus = dbStatus;
                    
                    // Update ExtractedData Status to match database status for consistency
                    if (updatedApproval.ExtractedData && dbStatus) {
                      updatedApproval.ExtractedData.Status = dbStatus;
                    }
                    
                    this.processSubpolicyVersions(updatedApproval);
                  }
                })
                .catch(approvalError => {
                  console.error('Error fetching latest approval:', approvalError);
                  
                  // Fall back to just updating the version
                  const updatedApproval = JSON.parse(JSON.stringify(approval));
                  updatedApproval.version = policyVersion;
                  updatedApproval.dbStatus = dbStatus;
                  
                  // Update ExtractedData Status to match database status for consistency
                  if (updatedApproval.ExtractedData && dbStatus) {
                    updatedApproval.ExtractedData.Status = dbStatus;
                  }
                  
                  this.processSubpolicyVersions(updatedApproval);
                });
            })
            .catch(error => {
              console.error('Error fetching policy status:', error);
              
              // Fall back to just updating with version
              const updatedApproval = JSON.parse(JSON.stringify(approval));
              updatedApproval.version = approval.version || 'u1'; // Use approval's version or default
              
              this.processSubpolicyVersions(updatedApproval);
            });
        })
        .catch(error => {
          console.error('Error fetching policy version:', error);
          // Fall back to using the approval as-is
          this.completeApprovalSelection(approval);
        });
    },
    
    // Helper method to process subpolicy versions
    processSubpolicyVersions(approval) {
      // Get subpolicy versions if there are any
      if (approval.ExtractedData && approval.ExtractedData.subpolicies && approval.ExtractedData.subpolicies.length > 0) {
        console.log('Fetching versions for', approval.ExtractedData.subpolicies.length, 'subpolicies');
        
        const promises = approval.ExtractedData.subpolicies.map(sub => {
          if (sub.SubPolicyId) {
            // First fetch subpolicy status to determine which version endpoint to use
                return axios.get(API_ENDPOINTS.SUBPOLICIES(sub.SubPolicyId))
                  .then(subpolicyResponse => {
                const subStatus = subpolicyResponse.data.Status;
                sub.Status = subStatus;
                
                // Determine which version endpoint to use based on subpolicy status
                let subVersionEndpoint;
                if (subStatus === 'Rejected') {
                  // For rejected subpolicies, fetch the latest reviewer version
                  subVersionEndpoint = API_ENDPOINTS.SUBPOLICY_REVIEWER_VERSION(sub.SubPolicyId);
                  console.log(`Subpolicy ${sub.SubPolicyId} is rejected, fetching reviewer version...`);
                } else {
                  // For other statuses, fetch the latest user version
                  subVersionEndpoint = API_ENDPOINTS.SUBPOLICY_VERSION(sub.SubPolicyId);
                  console.log(`Subpolicy ${sub.SubPolicyId} is not rejected, fetching user version...`);
                }
                
                // Fetch the appropriate version
                return axios.get(subVersionEndpoint)
                  .then(subVersionResponse => {
                    const subVersion = subVersionResponse.data.version || 'u1';
                    console.log(`Subpolicy ${sub.SubPolicyId} version: ${subVersion} for status: ${subStatus}`);
                    sub.version = subVersion;
                    return sub;
                  })
                  .catch(err => {
                    console.error(`Error fetching version for subpolicy ${sub.SubPolicyId}:`, err);
                    sub.version = 'u1'; // Default fallback
                    return sub;
                  });
              })
              .catch(err => {
                console.error(`Error fetching subpolicy status for ${sub.SubPolicyId}:`, err);
                sub.version = 'u1'; // Default fallback
                return sub;
              });
          } else {
            sub.version = 'u1'; // Default for subpolicies without ID
            return Promise.resolve(sub);
          }
        });
        
        // Wait for all version fetching to complete
        Promise.all(promises)
          .then(updatedSubpolicies => {
            approval.ExtractedData.subpolicies = updatedSubpolicies;
            this.completeApprovalSelection(approval);
          })
          .catch(error => {
            console.error('Error updating subpolicy versions:', error);
            this.completeApprovalSelection(approval);
          });
      } else {
        // No subpolicies to process
        this.completeApprovalSelection(approval);
      }
    },
    
    // Helper method to finish the approval selection process
    completeApprovalSelection(approval) {
      this.selectedApproval = approval;
      
      // Log the version information being displayed
      console.log('Displaying policy details:', {
        policyId: approval.PolicyId,
        version: approval.version,
        dbStatus: approval.dbStatus,
        approvedNot: approval.ApprovedNot,
        extractedDataStatus: approval.ExtractedData?.Status
      });
      
      // If policy is approved, filter subpolicies to only show approved ones
      if (this.selectedApproval.ExtractedData && 
          (this.selectedApproval.ApprovedNot === true || this.selectedApproval.ExtractedData.Status === 'Approved') && 
          this.selectedApproval.ExtractedData.subpolicies) {
        
        // When a policy is approved, all its subpolicies should be treated as approved
        this.selectedApproval.ExtractedData.subpolicies = this.selectedApproval.ExtractedData.subpolicies.map(sub => {
          // Mark all subpolicies as approved when parent policy is approved
          if (!sub.approval) {
            sub.approval = {};
          }
          sub.approval.approved = true;
          sub.Status = 'Approved';
          return sub;
        });
        
        // Add a flag to indicate this is showing only accepted items
        this.selectedApproval.showingApprovedOnly = true;
      }
      
      // If policy is rejected, ensure rejection details are properly displayed
      if (this.selectedApproval.ExtractedData && 
          (this.selectedApproval.ApprovedNot === false || this.selectedApproval.ExtractedData.Status === 'Rejected')) {
        
        console.log('Displaying rejected policy with rejection details:', {
          rejectionReason: this.selectedApproval.ExtractedData.rejection_reason,
          cascadingRejection: this.selectedApproval.ExtractedData.cascading_rejection,
          rejectedSubpolicyNames: this.selectedApproval.ExtractedData.rejected_subpolicy_names
        });
        
        // Add a flag to indicate this is showing rejected items
        this.selectedApproval.showingRejectedDetails = true;
      }
      
      this.showDetails = true;
    },
    // Update the refresh method
    refreshData() {
      // Refresh tasks for the current user
      this.loadUserTasks();
      
      // If there's a selected approval, refresh it with latest data
      if (this.selectedApproval && this.selectedApproval.PolicyId) {
        this.openApprovalDetails(this.selectedApproval);
      }
      
      // If there's a selected policy for subpolicies, refresh it
      if (this.selectedPolicyForSubpolicies && this.selectedPolicyForSubpolicies.PolicyId) {
        const policyId = this.selectedPolicyForSubpolicies.PolicyId;
        
        // Fetch latest data for this policy
        axios.get(API_ENDPOINTS.POLICY(policyId))
          .then(response => {
            if (response.data) {
              // Get the version for policy and subpolicies
              axios.get(API_ENDPOINTS.POLICY_VERSION(policyId))
                .then(versionResponse => {
                  const policyVersion = versionResponse.data.version || 'u1';
                  
                  // Create a new object with the policy data
                  const policyData = {
                    ...response.data,
                    version: policyVersion
                  };
                  
                  // If this policy has subpolicies, fetch their version information
                  if (response.data.ExtractedData && response.data.ExtractedData.subpolicies) {
                    const subpolicyPromises = response.data.ExtractedData.subpolicies.map(subpolicy => {
                      return axios.get(API_ENDPOINTS.SUBPOLICY_VERSION(subpolicy.SubPolicyId))
                        .then(subVersionResponse => {
                          return {
                            subpolicyId: subpolicy.SubPolicyId,
                            version: subVersionResponse.data.version || 'u1'
                          };
                        })
                        .catch(() => {
                          return {
                            subpolicyId: subpolicy.SubPolicyId,
                            version: 'u1'
                          };
                        });
                    });
                    
                    Promise.all(subpolicyPromises)
                      .then(subpolicyVersions => {
                        // Update subpolicy versions
                        if (policyData.ExtractedData && policyData.ExtractedData.subpolicies) {
                          policyData.ExtractedData.subpolicies.forEach(subpolicy => {
                            const versionInfo = subpolicyVersions.find(v => v.subpolicyId === subpolicy.SubPolicyId);
                            if (versionInfo) {
                              subpolicy.version = versionInfo.version;
                            }
                          });
                        }
                        
                        // Update the selected policy
                        this.selectedPolicyForSubpolicies = policyData;
                      });
      } else {
                    // No subpolicies, just update the policy
                    this.selectedPolicyForSubpolicies = policyData;
                  }
                })
                .catch(error => {
                  console.error("Error fetching policy version:", error);
                });
            }
          })
          .catch(error => {
            console.error("Error refreshing policy data:", error);
          });
      }
      
      // Refresh rejected subpolicies list if it's being displayed
      if (this.showRejectedSubpolicies) {
        this.fetchRejectedSubpolicies();
      }
    },
    // Update the refresh approvals method
    refreshApprovals() {
      this.fetchPolicies();
    },
    // Update fetchRejectedPolicies to fetch properly from policy approval table
    fetchRejectedPolicies() {
      console.log('Fetching rejected policies...');
      
      // Determine which user ID to use for API calls
      const userIdForAPI = this.selectedUserId || this.currentUserId;
      console.log('Using user ID for rejected policies:', userIdForAPI);
      
      if (!userIdForAPI) {
        console.warn('No user ID available for fetching rejected policies');
        this.rejectedPolicies = [];
        return Promise.resolve();
      }
      
      // Fetch rejected policy approvals for the selected user or current user
      return axios.get(API_ENDPOINTS.POLICY_APPROVALS_REJECTED(userIdForAPI))
        .then(response => {
          console.log('Rejected policy approvals response:', response.data);
          
          if (response.data && Array.isArray(response.data) && response.data.length > 0) {
            // Process each rejected policy approval
            const processedPolicies = response.data.map(approval => {
              console.log('Processing rejected approval:', approval);
              
              // Use the comprehensive getPolicyRejectionReason method to extract rejection reason
              let rejectionReason = 'No rejection reason provided';
              const extractedReason = this.getPolicyRejectionReason(approval);
              if (extractedReason) {
                rejectionReason = extractedReason;
              }
              
              // Get policy name and description
              const policyName = approval.ExtractedData?.PolicyName || `Policy ${approval.PolicyId?.PolicyId || approval.PolicyId}`;
              const policyScope = approval.ExtractedData?.Scope || 'No Scope';
              
              const processedPolicy = {
                policyId: approval.PolicyId?.PolicyId || approval.PolicyId,
                type: 'POLICY',
                description: policyName,
                rejectionReason: rejectionReason,
                createdDate: approval.ExtractedData?.CreatedByDate || new Date().toISOString().split('T')[0],
                originalPolicy: approval,
                rejectedVersion: approval.Version, // This should be r1, r2, etc.
                cascadingRejection: approval.ExtractedData?.cascading_rejection || false,
                rejectedSubpolicies: approval.ExtractedData?.rejected_subpolicy_names || [],
                // Make sure ExtractedData has the right structure for the edit modal
                ExtractedData: {
                  ...approval.ExtractedData,
                  PolicyName: policyName,
                  Scope: policyScope,
                  rejection_reason: rejectionReason
                }
              };
              
              console.log('Processed policy for table:', processedPolicy);
              return processedPolicy;
            });
            
            // Filter out duplicates based on policyId and keep only the most recent rejection
            const uniquePolicies = new Map();
            
            processedPolicies.forEach(policy => {
              const policyId = policy.policyId;
              const existingPolicy = uniquePolicies.get(policyId);
              
              if (!existingPolicy) {
                // First occurrence of this policy
                uniquePolicies.set(policyId, policy);
              } else {
                // Check if current policy has a rejection reason and existing doesn't
                const currentHasReason = policy.rejectionReason && policy.rejectionReason !== 'No rejection reason provided';
                const existingHasReason = existingPolicy.rejectionReason && existingPolicy.rejectionReason !== 'No rejection reason provided';
                
                // Keep the one with rejection reason, or the more recent one if both have/don't have reasons
                if (currentHasReason && !existingHasReason) {
                  uniquePolicies.set(policyId, policy);
                } else if (currentHasReason === existingHasReason) {
                  // Both have or both don't have reasons, keep the more recent one
                  const currentDate = new Date(policy.createdDate);
                  const existingDate = new Date(existingPolicy.createdDate);
                  if (currentDate > existingDate) {
                    uniquePolicies.set(policyId, policy);
                  }
                }
              }
            });
            
            this.rejectedPolicies = Array.from(uniquePolicies.values());
            console.log('All processed rejected policies (after deduplication):', this.rejectedPolicies);
            
          } else {
            console.log('No rejected policy approvals found for user');
            this.rejectedPolicies = [];
          }
        })
        .catch(error => {
          console.error('Error fetching rejected policy approvals:', error);
          // Fallback to old method
          this.fetchRejectedPoliciesFallback();
        });
    },
    
    // Fallback method for fetching rejected policies
    fetchRejectedPoliciesFallback() {
      console.log('Using fallback method to fetch rejected policies...');
      axios.get(API_ENDPOINTS.POLICIES)
        .then(response => {
          console.log('All policies response:', response.data);
          
          let policiesData = response.data;
          if (response.data.success && response.data.data) {
            policiesData = response.data.data;
          }
          
          if (Array.isArray(policiesData)) {
            // Filter for rejected policies or policies with rejected subpolicies
            const rejectedPolicies = policiesData.filter(policy => 
              policy.Status === 'Rejected' || 
              (policy.subpolicies && policy.subpolicies.some(sub => sub.Status === 'Rejected'))
            );
            
            console.log('Found rejected policies (fallback):', rejectedPolicies.length);
            
            this.rejectedPolicies = rejectedPolicies.map(policy => ({
              policyId: policy.PolicyId,
              type: 'POLICY',
              description: policy.PolicyName || `Policy ${policy.PolicyId}`,
              rejectionReason: 'Policy or subpolicies rejected',
              createdDate: policy.CreatedByDate || new Date().toISOString().split('T')[0],
              originalPolicy: {
              PolicyId: policy.PolicyId,
              ExtractedData: {
                PolicyName: policy.PolicyName,
                CreatedByName: policy.CreatedByName,
                CreatedByDate: policy.CreatedByDate,
                Scope: policy.Scope,
                Status: policy.Status,
                Objective: policy.Objective,
                subpolicies: policy.subpolicies || []
              },
                ApprovedNot: false
              }
            }));
          }
        })
        .catch(error => {
          console.error('Error in fallback method:', error);
          this.rejectedPolicies = [];
        });
    },
    // Add a method to fetch policies that have rejected subpolicies
    fetchPoliciesWithRejectedSubpolicies() {
      console.log('Fetching policies with rejected subpolicies...');
      axios.get(API_ENDPOINTS.POLICIES)
        .then(response => {
          console.log('All policies response:', response.data);
          
          // Handle both response formats: direct array or success wrapper
          let policiesData;
          if (response.data.success && response.data.data) {
            policiesData = response.data.data;
          } else if (Array.isArray(response.data)) {
            policiesData = response.data;
          } else {
            console.error('Unexpected response format:', response.data);
            return;
          }
          
          console.log('Policies data length:', policiesData.length);
          if (Array.isArray(policiesData)) {
            // Filter policies that have at least one rejected subpolicy
            const policiesWithRejected = policiesData.filter(policy => 
              policy.subpolicies && 
              policy.subpolicies.some(sub => sub.Status === 'Rejected')
            );
            
            console.log('Found policies with rejected subpolicies:', policiesWithRejected.length);
            
            if (policiesWithRejected.length > 0) {
              this.rejectedPolicies = policiesWithRejected.map(policy => ({
                PolicyId: policy.PolicyId,
                ExtractedData: {
                  type: 'policy',
                  PolicyName: policy.PolicyName,
                  CreatedByName: policy.CreatedByName,
                  CreatedByDate: policy.CreatedByDate,
                  Scope: policy.Scope,
                  Status: policy.Status,
                  Objective: policy.Objective,
                  subpolicies: policy.subpolicies || []
                },
                ApprovedNot: policy.Status === 'Rejected' ? false : null,
                main_policy_rejected: policy.Status === 'Rejected'
              }));
            }
          }
      })
      .catch(error => {
          console.error('Error fetching policies with rejected subpolicies:', error);
      });
    },
    // Modify submitReview to update policy status and handle pending rejections
    submitReview() {
      // Prevent double submission
      if (this.isSubmittingReview) {
        console.log('Review already in progress, preventing duplicate submission');
        return;
      }
      
      this.isSubmittingReview = true;
      
      if (!this.isComplianceApproval) {
        const policyId = this.selectedApproval.PolicyId;
        
        // Check for pending rejections that need to be saved
        const pendingRejections = [];
        if (this.selectedApproval.ExtractedData && this.selectedApproval.ExtractedData.subpolicies) {
          this.selectedApproval.ExtractedData.subpolicies.forEach(subpolicy => {
            if (subpolicy.pendingRejection) {
              pendingRejections.push({
                subpolicyId: subpolicy.SubPolicyId,
                rejectionData: subpolicy.pendingRejection
              });
            }
          });
        }
        
        // If there are pending rejections, handle them through the main approval workflow
        if (pendingRejections.length > 0) {
          console.log('Processing pending rejections through main approval workflow:', pendingRejections);
          
          // Update the ExtractedData to reflect subpolicy rejections
              pendingRejections.forEach(pending => {
                const subpolicy = this.selectedApproval.ExtractedData.subpolicies.find(
                  sub => sub.SubPolicyId === pending.subpolicyId
                );
                if (subpolicy) {
              // Update subpolicy status to rejected
              subpolicy.Status = 'Rejected';
              if (!subpolicy.approval) {
                subpolicy.approval = {};
              }
              subpolicy.approval.approved = false;
              subpolicy.approval.remarks = pending.rejectionData.remarks;
              
              // Clear pending rejection since we're handling it properly now
                  delete subpolicy.pendingRejection;
                }
              });
              
          // Set review decision to reject since we have rejected subpolicies
          this.reviewDecision = 'reject';
          
          // Continue with normal submission - the rejections will be handled properly
          this.continueWithPolicySubmission(policyId);
        } else {
          // No pending rejections, proceed normally
          this.continueWithPolicySubmission(policyId);
        }
        
        return;
      }
      
      // For compliance reviews
      const reviewData = {
        ExtractedData: JSON.parse(JSON.stringify(this.selectedApproval.ExtractedData)),
        ApprovedNot: this.selectedApproval.ApprovedNot
      };
      
      axios.put(
        API_ENDPOINTS.COMPLIANCE_APPROVALS(this.selectedApproval.ApprovalId),
        reviewData
      )
      .then(response => {
        console.log('Response:', response.data);
        if (response.data.ApprovalId) {
          this.selectedApproval.ApprovalId = response.data.ApprovalId;
          this.selectedApproval.Version = response.data.Version;
          // Update approved date if provided
          if (response.data.ApprovedDate) {
            this.selectedApproval.ApprovedDate = response.data.ApprovedDate;
          }
          // Show different messages based on whether it's an approval or rejection
          const isApproved = this.selectedApproval.ApprovedNot === true;
          const message = isApproved ? 
            'Compliance review accepted successfully!' : 
            'Compliance review rejected successfully!';
          const title = isApproved ? 'Review Accepted' : 'Review Rejected';
          
          PopupService.success(message, title);
          this.sendPushNotification({
            title: isApproved ? 'Compliance Review Accepted' : 'Compliance Review Rejected',
            message: isApproved ? 
              'Compliance review has been accepted successfully.' :
              'Compliance review has been rejected successfully.',
            category: 'compliance',
            priority: 'medium',
            user_id: this.currentUserId || 'default_user'
          });
          
          // Reset loading state
          this.isSubmittingReview = false;
          
          // First close the details view
          this.closeApprovalDetails();
          
          // Then refresh the approvals list to update the UI
          this.refreshApprovals();
        }
      })
      .catch(error => {
        console.error('Error submitting compliance review:', error);
                  PopupService.error('Error submitting review: ' + (error.response?.data?.error || error.message), 'Review Error');
          this.sendPushNotification({
            title: 'Compliance Review Error',
            message: `Failed to submit compliance review: ${error.response?.data?.error || error.message}`,
            category: 'compliance',
            priority: 'high',
            user_id: this.currentUserId || 'default_user'
          });
      });
    },
    // Helper method to continue with policy submission after handling pending rejections
    continueWithPolicySubmission(policyId) {
      // Check if the policy itself has a pending rejection
      if (this.selectedApproval.pendingRejection) {
        console.log('Policy has pending rejection, processing it through approval workflow');
        
        // Instead of trying to update policy status directly, 
        // we'll handle the rejection through the proper approval workflow
        // by setting the review decision to reject and proceeding with submission
        
        // Set the review decision to reject
        this.reviewDecision = 'reject';
        
        // Update the ExtractedData to reflect the rejection
        if (!this.selectedApproval.ExtractedData.policy_approval) {
          this.selectedApproval.ExtractedData.policy_approval = {};
        }
        this.selectedApproval.ExtractedData.policy_approval.approved = false;
        this.selectedApproval.ExtractedData.policy_approval.remarks = this.selectedApproval.pendingRejection.remarks || '';
        this.selectedApproval.ExtractedData.Status = 'Rejected';
        
        // Clear pending rejection since we're handling it properly now
          delete this.selectedApproval.pendingRejection;
          
        // Continue with normal submission - the rejection will be handled properly
          this.continueWithPolicySubmissionAfterRejections(policyId);
        
        return;
      }
      
      // No pending policy rejection, continue normally
      this.continueWithPolicySubmissionAfterRejections(policyId);
    },

    // Helper method to continue with policy submission after all rejections are handled
    continueWithPolicySubmissionAfterRejections(policyId) {
      // Create the policy approval data
      const reviewData = {
        ExtractedData: JSON.parse(JSON.stringify(this.selectedApproval.ExtractedData)),
        ApprovedNot: this.selectedApproval.ApprovedNot,
        UserId: this.selectedApproval.UserId, // Use the original user's ID from the approval
        ReviewerId: this.currentUserId // Set reviewer ID to current user (reviewer), not the original user
      };
      
      // First get the current version
      axios.get(API_ENDPOINTS.POLICY_VERSION(policyId))
        .then(versionResponse => {
          const currentVersion = versionResponse.data.version;
          console.log('Current version before submission:', currentVersion);
          
          // Add logic to check if any subpolicies are rejected
          const hasRejectedSubpolicies = this.selectedApproval.ExtractedData.subpolicies &&
            this.selectedApproval.ExtractedData.subpolicies.some(subpolicy => 
              subpolicy.Status === 'Rejected');
          
          if (this.reviewDecision === 'approve' && hasRejectedSubpolicies) {
            // Show warning
            this.$swal({
              title: 'Warning',
              text: 'One or more subpolicies are rejected. The policy will still be marked as rejected regardless of approval.',
              icon: 'warning',
              confirmButtonText: 'Continue'
            }).then(() => {
              // Continue with submission after warning
              this.submitPolicyReview(policyId, reviewData, currentVersion);
            });
            this.sendPushNotification({
              title: 'Policy Review Warning',
              message: 'One or more subpolicies are rejected. The policy will still be marked as rejected regardless of approval.',
              category: 'policy',
              priority: 'medium',
              user_id: this.currentUserId || 'default_user'
            });
          } else {
            // No rejected subpolicies, proceed normally
            this.submitPolicyReview(policyId, reviewData, currentVersion);
          }
        })
        .catch(error => {
          console.error('Error getting policy version:', error);
          PopupService.error('Error getting policy version: ' + (error.response?.data?.error || error.message), 'Policy Version Error');
          this.sendPushNotification({
            title: 'Policy Version Error',
            message: `Failed to get policy version: ${error.response?.data?.error || error.message}`,
            category: 'policy',
            priority: 'high',
            user_id: this.currentUserId || 'default_user'
          });
          
          // Reset loading state on error
          this.isSubmittingReview = false;
        });
    },

    // Add this helper method to handle the actual submission
    submitPolicyReview(policyId, reviewData, currentVersion) {
      // Prevent duplicate submission
      if (this.isSubmittingReview) {
        console.log('Review submission already in progress, preventing duplicate call');
        return;
      }
      
      this.isSubmittingReview = true;
      
      // Submit policy review with current version info
      axios.post(API_ENDPOINTS.POLICY_SUBMIT_REVIEW(policyId), {
        ...reviewData,
        currentVersion: currentVersion,
        approved: this.reviewDecision === 'approve'
      })
      .then(response => {
        console.log('Policy review submitted successfully:', response.data);
        
        // Update the local approval with the returned data
        this.selectedApproval.Version = response.data.Version;
        
        if (response.data.ApprovedDate) {
          this.selectedApproval.ApprovedDate = response.data.ApprovedDate;
        }
        
        // Show different messages based on whether it's an approval or rejection
        const isApproved = this.reviewDecision === 'approve';
        const message = isApproved ? 
          'Policy review accepted successfully!' : 
          'Policy review rejected successfully!';
        const title = isApproved ? 'Review Accepted' : 'Review Rejected';
        
        PopupService.success(message, title);
        this.sendPushNotification({
          title: isApproved ? 'Policy Review Accepted' : 'Policy Review Rejected',
          message: isApproved ? 
            'Policy review has been accepted successfully.' :
            'Policy review has been rejected successfully.',
          category: 'policy',
          priority: 'medium',
          user_id: this.currentUserId || 'default_user'
        });
        
        // Close the details view
        this.closeApprovalDetails();
        
        // Refresh the policies list
        this.refreshApprovals();
        
        // Reset loading state
        this.isSubmittingReview = false;
      })
      .catch(error => {
        console.error('Error submitting review:', error);
        PopupService.error('Error submitting review: ' + (error.response?.data?.error || error.message), 'Submission Error');
        this.sendPushNotification({
          title: 'Policy Review Error',
          message: `Failed to submit policy review: ${error.response?.data?.error || error.message}`,
          category: 'policy',
          priority: 'high',
          user_id: this.currentUserId || 'default_user'
        });
        
        // Reset loading state on error
        this.isSubmittingReview = false;
      });
    },
    // Update resubmitPolicy to change status back to "Under Review"
    resubmitPolicy(policy) {
      const policyId = this.getPolicyId(policy);
      console.log('=== RESUBMIT POLICY DEBUG ===');
      console.log('Resubmitting policy with ID:', policyId);
      console.log('Full policy object:', policy);
      console.log('Policy ExtractedData:', policy.ExtractedData);
      console.log('Original policy in policy object:', policy.originalPolicy);
      
      // Use original policy if available (from rejected policies table)
      const actualPolicy = policy.originalPolicy || policy;
      const actualPolicyId = this.getPolicyId(actualPolicy);
      console.log('Using actual policy:', actualPolicy);
      console.log('Using actual policy ID:', actualPolicyId);
      
      // Check if any changes were made to the policy
      const hasChanges = this.checkPolicyChanges(actualPolicy);
      if (!hasChanges) {
        // Don't show popup since we have inline warning now
        return;
      }
      
      // First, check the policy status via debug endpoint
      console.log('Checking policy status before resubmission...');
      axios.get(API_ENDPOINTS.POLICY_DEBUG_STATUS(actualPolicyId))
        .then(debugResponse => {
          console.log('Policy debug status:', debugResponse.data);
      
      // Validate policy data
          const validationErrors = this.validatePolicyData(actualPolicy);
      if (validationErrors.length > 0) {
        PopupService.warning(`Please fix the following errors before resubmitting:\n${validationErrors.join('\n')}`, 'Validation Errors');
        this.sendPushNotification({
          title: 'Policy Validation Errors',
          message: `Policy validation failed: ${validationErrors.join(', ')}`,
          category: 'policy',
          priority: 'medium',
          user_id: this.currentUserId || 'default_user'
        });
        return;
      }
      
          // Continue with resubmission logic
          this.performPolicyResubmission(actualPolicy, actualPolicyId);
        })
        .catch(debugError => {
          console.error('Error checking policy status:', debugError);
          PopupService.warning('Error checking policy status. Proceeding with resubmission attempt.', 'Warning');
          this.sendPushNotification({
            title: 'Policy Status Check Warning',
            message: 'Error checking policy status. Proceeding with resubmission attempt.',
            category: 'policy',
            priority: 'medium',
            user_id: this.currentUserId || 'default_user'
          });
          
          // Still try to proceed with resubmission
          const validationErrors = this.validatePolicyData(actualPolicy);
          if (validationErrors.length > 0) {
            PopupService.warning(`Please fix the following errors before resubmitting:\n${validationErrors.join('\n')}`, 'Validation Errors');
          this.sendPushNotification({
            title: 'Policy Validation Errors',
            message: `Policy validation failed: ${validationErrors.join(', ')}`,
            category: 'policy',
            priority: 'medium',
            user_id: this.currentUserId || 'default_user'
          });
            return;
          }
          
          this.performPolicyResubmission(actualPolicy, actualPolicyId);
        });
    },
    
          performPolicyResubmission(actualPolicy, actualPolicyId) {
      // Check if subpolicies exist and have proper structure
        if (actualPolicy.ExtractedData && actualPolicy.ExtractedData.subpolicies && actualPolicy.ExtractedData.subpolicies.length > 0) {
        // Ensure each subpolicy has the correct fields
          actualPolicy.ExtractedData.subpolicies.forEach((subpolicy, index) => {
          console.log(`Checking subpolicy ${index} with ID: ${subpolicy.SubPolicyId}`);
          
          // Make sure required fields exist
          if (!subpolicy.SubPolicyName) {
            console.warn(`SubPolicyName is missing for subpolicy ${index}`);
          }
          if (!subpolicy.Description) {
            console.warn(`Description is missing for subpolicy ${index}`);
          }
        });
      } else {
        console.warn('No subpolicies found in policy data or subpolicies array is not properly structured');
      }
      
        // Prepare data for resubmission using actual policy data
      const resubmitData = {
          PolicyName: actualPolicy.ExtractedData?.PolicyName || actualPolicy.PolicyName,
          PolicyDescription: actualPolicy.ExtractedData?.PolicyDescription || actualPolicy.PolicyDescription,
          Scope: actualPolicy.ExtractedData?.Scope || actualPolicy.Scope,
          Objective: actualPolicy.ExtractedData?.Objective || actualPolicy.Objective,
          Department: actualPolicy.ExtractedData?.Department || actualPolicy.Department,
          Applicability: actualPolicy.ExtractedData?.Applicability || actualPolicy.Applicability,
          subpolicies: actualPolicy.ExtractedData?.subpolicies || [],
          // Add policy status information to help backend validation
          currentStatus: 'Rejected',
          rejectionReason: actualPolicy.ExtractedData?.rejection_reason || actualPolicy.rejectionReason,
          // Include version information if available
          currentVersion: actualPolicy.Version || actualPolicy.rejectedVersion
      };
      
      console.log('Prepared resubmission data:', resubmitData);
      console.log('Subpolicies in resubmission data:', resubmitData.subpolicies);
      console.log('Number of subpolicies:', resubmitData.subpolicies.length);
      
        // First check the current policy status to ensure it can be resubmitted
        console.log(`Checking current status for policy ${actualPolicyId}`);
        axios.get(API_ENDPOINTS.POLICY(actualPolicyId))
          .then(policyResponse => {
            const policyStatus = policyResponse.data.Status;
            console.log(`Current policy status: ${policyStatus}`);
            
            // Check if policy can be resubmitted
            if (policyStatus === 'Approved') {
              throw new Error('Cannot resubmit an approved policy. The policy has already been approved.');
            }
            
            if (policyStatus !== 'Rejected' && policyStatus !== 'Under Review') {
              throw new Error(`Cannot resubmit a policy with status '${policyStatus}'. Only rejected or under review policies can be resubmitted.`);
            }
            
            // If we reach here, the policy can be resubmitted
            // Use the existing endpoint but wrap the data properly
            const wrappedData = {
              ExtractedData: resubmitData
            };
            
            console.log(`Making request to: /api/policies/${actualPolicyId}/resubmit-approval/`);
            return axios.put(API_ENDPOINTS.POLICY_RESUBMIT_APPROVAL(actualPolicyId), wrappedData);
          })
        .then(response => {
          console.log('Policy resubmitted successfully:', response.data);
          
          // Show version information in the alert
          let successMessage = 'Policy resubmitted for review!';
          if (response.data.UserId) {
            successMessage += ` (UserId: ${response.data.UserId})`;
          }
          if (response.data.reviewer_assigned) {
            successMessage += ` (Assigned to ReviewerId: ${response.data.ReviewerId})`;
          }
          
          PopupService.success(successMessage, 'Policy Resubmitted');
          this.sendPushNotification({
            title: 'Policy Resubmitted',
            message: successMessage,
            category: 'policy',
            priority: 'medium',
            user_id: this.currentUserId || 'default_user'
          });
          
          this.closeEditModal();
          // Refresh both rejected policies and current policies to ensure UI is in sync
          this.fetchRejectedPolicies();
          this.fetchPolicies();
          // Also refresh user tasks if we're in that view
          if (this.selectedUserId || this.currentUserId) {
            this.loadUserTasks();
          }
        })
        .catch(error => {
          console.error('Error data:', error.response ? error.response.data : 'No response data');
          this.handleError(error, 'resubmitting policy');
        });
    },
    
    // Helper method to validate policy data before submission
    validatePolicyData(policy) {
      const validationErrors = [];
      
      // Check required policy fields - handle different data structures
      const policyName = policy.ExtractedData?.PolicyName || policy.PolicyName;
      const policyDescription = policy.ExtractedData?.PolicyDescription || policy.PolicyDescription;
      const subpolicies = policy.ExtractedData?.subpolicies || [];
      
      if (!policyName) {
        validationErrors.push('Policy Name is required');
      }
      
      if (!policyDescription) {
        validationErrors.push('Policy Description is required');
      }
      
      // Check subpolicies if they exist
      if (subpolicies && subpolicies.length > 0) {
        subpolicies.forEach((subpolicy, index) => {
          if (!subpolicy.SubPolicyName) {
            validationErrors.push(`Subpolicy #${index + 1} is missing a name`);
          }
          
          if (!subpolicy.Description) {
            validationErrors.push(`Subpolicy #${index + 1} is missing a description`);
          }
        });
      }
      
      return validationErrors;
    },
    
    // Helper method to handle and display errors
    handleError(error, context) {
      console.error(`Error ${context}:`, error);
      let errorMessage = 'An unexpected error occurred';
      
      if (error.response) {
        // The server responded with a status code outside of 2xx range
        if (error.response.data && error.response.data.error) {
          errorMessage = error.response.data.error;
        } else if (error.response.data && typeof error.response.data === 'string') {
          errorMessage = error.response.data;
        } else {
          errorMessage = `Server error: ${error.response.status}`;
        }
      } else if (error.request) {
        // The request was made but no response was received
        errorMessage = 'No response from server. Please check your connection.';
      } else {
        // Something happened in setting up the request
        errorMessage = error.message || errorMessage;
      }
      
      PopupService.error(`Error ${context}: ${errorMessage}`, 'Error');
      this.sendPushNotification({
        title: 'Policy Error',
        message: `Error ${context}: ${errorMessage}`,
        category: 'policy',
        priority: 'high',
        user_id: this.currentUserId || 'default_user'
      });
      return errorMessage;
    },
    
    // Role checking methods for policy approval
    // Check if current user is the reviewer for this policy
    isCurrentUserReviewer(policy) {
      if (!policy || !this.currentUserId) return false;
      
      console.log('Checking if current user is reviewer for policy:', {
        policyId: policy.PolicyId,
        currentUserId: this.currentUserId,
        reviewer: policy.ExtractedData?.Reviewer,
        reviewerId: policy.ReviewerId,
        isAdministrator: this.isAdministrator
      });
      
      // For GRC Administrators, they can only review policies specifically assigned to them
      if (this.isAdministrator) {
        // Check if they are specifically assigned as the reviewer for this policy
        const reviewerId = policy.ReviewerId || policy.ExtractedData?.Reviewer;
        if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
          console.log('GRC Administrator is specifically assigned as reviewer for this policy');
          return true;
        }
        console.log('GRC Administrator is not assigned as reviewer for this policy');
        return false;
      }
      
      // Check if current user is the reviewer for this policy
      const reviewerId = policy.ReviewerId || policy.ExtractedData?.Reviewer;
      
      console.log('Reviewer check details:', {
        reviewerId: reviewerId,
        currentUserId: this.currentUserId,
        policyReviewerId: policy.ReviewerId,
        extractedDataReviewer: policy.ExtractedData?.Reviewer
      });
      
      // Check by ID
      if (reviewerId && String(reviewerId) === String(this.currentUserId)) {
        console.log('Current user is the assigned reviewer');
        return true;
      }
      
      // Check if the policy was created by the current user (they shouldn't review their own policies)
      if (this.isCurrentUserCreator(policy)) {
        console.log('Current user is the creator - not the reviewer');
        return false;
      }
      
      console.log('Current user is not the reviewer');
      return false;
    },

    // Check if current user can perform review actions (approve/reject)
    canPerformReviewActions(policy) {
      if (!policy || !this.currentUserId) return false;
      
      // Only allow review actions if the user is specifically assigned as the reviewer
      // AND is not the creator of the policy
      return this.isCurrentUserReviewer(policy) && !this.isCurrentUserCreator(policy);
    },

    // Check if current user is the creator of this policy
    isCurrentUserCreator(policy) {
      if (!policy || !this.currentUserId) return false;
      
      const createdBy = policy.ExtractedData?.CreatedByName || policy.CreatedByName;
      const createdById = policy.ExtractedData?.CreatedBy || policy.CreatedBy;
      const userId = policy.ExtractedData?.UserID || policy.UserID;
      
      console.log('Creator check details:', {
        createdBy: createdBy,
        createdById: createdById,
        userId: userId,
        currentUserId: this.currentUserId,
        currentUserName: this.getCurrentUserName(),
        policyData: policy.ExtractedData
      });
      
      // Check by ID first (most reliable)
      if (createdById && String(createdById) === String(this.currentUserId)) {
        console.log('Current user is creator (by ID)');
        return true;
      }
      
      // Check by UserID (from approval record)
      if (userId && String(userId) === String(this.currentUserId)) {
        console.log('Current user is creator (by UserID)');
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
    
    // Update approveSubpolicy to handle subpolicy approval
    approveSubpolicy(subpolicy) {
      // Set subpolicy approval status
      if (!subpolicy.approval) {
        subpolicy.approval = {};
      }
      subpolicy.approval.approved = true;
      subpolicy.approval.remarks = '';
      
      // Set review decision for policy reviews
      this.reviewDecision = 'approve';
      
      // Submit subpolicy review directly (this handles both status update and approval)
      axios.put(API_ENDPOINTS.SUBPOLICY_REVIEW(subpolicy.SubPolicyId), {
        Status: 'Approved'
      })
      .then(response => {
        console.log('Subpolicy approval submitted successfully:', response.data);
        
        // Update the subpolicy status in the UI
        subpolicy.Status = 'Approved';
        
        // Check if parent policy status was updated (all subpolicies approved)
        if (response.data.PolicyUpdated) {
          console.log(`Policy status updated to: ${response.data.PolicyStatus}`);
          
          // If parent policy was updated, refresh the policies list
          this.fetchPolicies();
          
          // Also update the UI to show policy is now approved
          if (this.selectedApproval && this.selectedApproval.ExtractedData) {
            this.selectedApproval.ExtractedData.Status = response.data.PolicyStatus;
          }
        }
        
        // Check if all subpolicies are now approved
        this.checkAllSubpoliciesApproved();
        
        // Show success message
        PopupService.success('Subpolicy approved successfully!', 'Approval Success');
      })
      .catch(error => {
        console.error('Error approving subpolicy:', error);
        PopupService.error('Error approving subpolicy. Please try again.', 'Approval Error');
        this.sendPushNotification({
          title: 'Subpolicy Approval Error',
          message: 'Error approving subpolicy. Please try again.',
          category: 'policy',
          priority: 'high',
          user_id: this.currentUserId || 'default_user'
        });
      });
    },
    
    // Add a method to check if all subpolicies are approved
    checkAllSubpoliciesApproved() {
      if (!this.selectedApproval || 
          !this.selectedApproval.ExtractedData || 
          !this.selectedApproval.ExtractedData.subpolicies ||
          this.selectedApproval.ExtractedData.subpolicies.length === 0) {
        return;
      }
      
      const subpolicies = this.selectedApproval.ExtractedData.subpolicies;
      const allApproved = subpolicies.every(sub => sub.approval?.approved === true);
      
      if (allApproved) {
        console.log('All subpolicies are approved! The policy should be automatically approved');
        
        // Automatically set policy approval to true
        if (!this.selectedApproval.ExtractedData.policy_approval) {
          this.selectedApproval.ExtractedData.policy_approval = {};
        }
        this.selectedApproval.ExtractedData.policy_approval.approved = true;
        this.selectedApproval.ApprovedNot = true;
        
        // Show notification to user
        PopupService.success('All subpolicies are approved! The policy has been automatically approved.', 'Auto-Approval');
        this.sendPushNotification({
          title: 'All Subpolicies Approved',
          message: 'All subpolicies are approved! The policy has been automatically approved.',
          category: 'policy',
          priority: 'medium',
          user_id: this.currentUserId || 'default_user'
        });
      }
    },
    // Add the missing rejectSubpolicy method
    rejectSubpolicy(subpolicy) {
      // Open rejection modal for subpolicy
      this.rejectingType = 'subpolicy';
      this.rejectingSubpolicy = subpolicy;
      this.showRejectModal = true;
    },
    // Add the missing cancelRejection method
    cancelRejection() {
      this.showRejectModal = false;
      this.rejectingSubpolicy = null;
      this.rejectingType = '';
      this.rejectionComment = '';
    },
    // Update rejectSubpolicy via confirmRejection
    confirmRejection() {
      if (this.rejectingType === 'policy' && this.rejectingPolicy) {
        // Handle policy rejection - store locally, don't save to DB yet
        console.log('Storing policy rejection locally:', this.rejectingPolicy.PolicyId);
        
        // Store rejection decision locally
        if (!this.rejectingPolicy.pendingRejection) {
          this.rejectingPolicy.pendingRejection = {};
        }
        this.rejectingPolicy.pendingRejection.approved = false;
        this.rejectingPolicy.pendingRejection.remarks = this.rejectionComment;
        
        // Update local state for display
        this.rejectingPolicy.ExtractedData.Status = 'Rejected';
        
        // Set review decision for policy reviews
        this.reviewDecision = 'reject';
        
        // Close modal
        this.showRejectModal = false;
        this.rejectingPolicy = null;
        this.rejectingType = '';
        this.rejectionComment = '';
        
        PopupService.success('Policy rejection stored. Click "Submit Review" to save the decision.', 'Rejection Stored');
      } 
      else if (this.rejectingType === 'subpolicy' && this.rejectingSubpolicy) {
        if (!this.rejectingSubpolicy.SubPolicyId) {
          console.error('Missing SubPolicyId, cannot reject subpolicy', this.rejectingSubpolicy);
          PopupService.error('Error: Cannot reject subpolicy - missing SubPolicyId', 'Missing ID Error');
          this.sendPushNotification({
            title: 'Subpolicy Rejection Error',
            message: 'Cannot reject subpolicy - missing SubPolicyId',
            category: 'policy',
            priority: 'high',
            user_id: this.currentUserId || 'default_user'
          });
          this.showRejectModal = false;
          this.rejectingSubpolicy = null;
          this.rejectingType = '';
          this.rejectionComment = '';
          return;
        }
        
        console.log('Storing subpolicy rejection locally:', this.rejectingSubpolicy.SubPolicyId);
        
        // Store rejection decision locally instead of calling API
        if (!this.rejectingSubpolicy.pendingRejection) {
          this.rejectingSubpolicy.pendingRejection = {};
        }
        this.rejectingSubpolicy.pendingRejection.approved = false;
        this.rejectingSubpolicy.pendingRejection.remarks = this.rejectionComment;
        
        // Update local state for display
        if (!this.rejectingSubpolicy.approval) {
          this.rejectingSubpolicy.approval = {};
        }
        this.rejectingSubpolicy.Status = 'Rejected';
        this.rejectingSubpolicy.approval.approved = false;
        this.rejectingSubpolicy.approval.remarks = this.rejectionComment;
        
        // Set review decision for policy reviews
        this.reviewDecision = 'reject';
        
        // Close modal
        this.showRejectModal = false;
        this.rejectingSubpolicy = null;
        this.rejectingType = '';
        this.rejectionComment = '';
        
        PopupService.success('Subpolicy rejection stored. Click "Submit Review" to save the decision.', 'Rejection Stored');
      }
      else if (this.rejectingType === 'compliance') {
        // Handle compliance rejection
        console.log('Storing compliance rejection locally');
        
        // Initialize compliance approval if doesn't exist
        if (!this.selectedApproval.ExtractedData.compliance_approval) {
          this.selectedApproval.ExtractedData.compliance_approval = {};
        }
        this.selectedApproval.ExtractedData.compliance_approval.approved = false;
        this.selectedApproval.ExtractedData.compliance_approval.remarks = this.rejectionComment;
        
        // Update the overall approval status
        this.selectedApproval.ApprovedNot = false;
        
        // Set review decision for policy reviews
        this.reviewDecision = 'reject';
        
        // Close modal
        this.showRejectModal = false;
        this.rejectingType = '';
        this.rejectionComment = '';
        
        PopupService.success('Compliance rejection stored. Click "Submit Review" to save the decision.', 'Rejection Stored');
      }
    },
    getPolicyId(policy) {
      // Handle different policy structure formats
      if (policy.policyId) {
        return policy.policyId; // For processed rejected policies
      }
      if (policy.PolicyId) {
        return typeof policy.PolicyId === 'object' ? policy.PolicyId.PolicyId : policy.PolicyId;
      }
      if (policy.ApprovalId) {
      return policy.ApprovalId;
      }
      if (policy.id) {
        return policy.id; // For table data
      }
      return 'Unknown';
    },
    closeApprovalDetails() {
      this.selectedApproval = null;
      this.showDetails = false;
    },
    approveCompliance() {
      // Initialize compliance approval if doesn't exist
      if (!this.selectedApproval.ExtractedData.compliance_approval) {
        this.selectedApproval.ExtractedData.compliance_approval = {};
      }
      this.selectedApproval.ExtractedData.compliance_approval.approved = true;
      this.selectedApproval.ExtractedData.compliance_approval.remarks = '';
      
      // Update the overall approval status
      this.selectedApproval.ApprovedNot = true;
      
      // Set review decision for policy reviews
      this.reviewDecision = 'approve';
    },
    rejectCompliance() {
      this.rejectingType = 'compliance';
      this.showRejectModal = true;
    },
    openRejectedItem(item) {
      if (item.is_compliance) {
        // For compliance items
        this.editingCompliance = JSON.parse(JSON.stringify(item)); // Deep copy
        this.showEditComplianceModal = true;
      } else {
        // For rejected policy items, open the edit modal
        console.log('Opening rejected policy item for editing:', item);
        
        if (item.originalPolicy) {
          // Use the original policy data to open edit modal
          this.openRejectedPolicy(item.originalPolicy);
        } else {
          // If no original policy, try to use the item directly
          this.openRejectedPolicy(item);
        }
      }
    },
    closeEditComplianceModal() {
      this.showEditComplianceModal = false;
      this.editingCompliance = null;
    },
    resubmitCompliance(compliance) {
      // Reset approval status
      if (compliance.ExtractedData.compliance_approval) {
        compliance.ExtractedData.compliance_approval.approved = null;
        compliance.ExtractedData.compliance_approval.remarks = '';
      }
      
      axios.put(API_ENDPOINTS.COMPLIANCE_APPROVALS_RESUBMIT(compliance.ApprovalId), {
        ExtractedData: compliance.ExtractedData
      })
      .then(() => {
        PopupService.success('Compliance resubmitted for review!', 'Compliance Resubmitted');
        this.showEditComplianceModal = false;
        this.fetchRejectedPolicies();
        // Force reload to update UI
        setTimeout(() => {
          window.location.reload();
        }, 500);
        this.sendPushNotification({
          title: 'Compliance Resubmitted',
          message: 'Compliance has been resubmitted for review.',
          category: 'compliance',
          priority: 'medium',
          user_id: this.currentUserId || 'default_user'
        });
      })
      .catch(error => {
        PopupService.error('Error resubmitting compliance', 'Resubmission Error');
        console.error(error);
        this.sendPushNotification({
          title: 'Compliance Resubmission Error',
          message: 'Error resubmitting compliance. Please try again.',
          category: 'compliance',
          priority: 'high',
          user_id: this.currentUserId || 'default_user'
        });
      });
    },
    showEditFormInline(subpolicy) {
      console.log('Opening inline edit form for subpolicy:', subpolicy.SubPolicyId);
      
      // Store original values before editing
      subpolicy.originalDescription = subpolicy.Description;
      subpolicy.originalControl = subpolicy.Control;
      
      // Make sure approval object exists before accessing it
      if (!subpolicy.approval) {
        subpolicy.approval = { remarks: '', approved: false };
      }
      
      // If this is a rejected subpolicy, fetch the latest reviewer version
      if (subpolicy.Status === 'Rejected' || (subpolicy.approval && subpolicy.approval.approved === false)) {
        axios.get(API_ENDPOINTS.SUBPOLICY_REVIEWER_VERSION(subpolicy.SubPolicyId))
          .then(versionResponse => {
            const rVersion = versionResponse.data.version || 'R1';
            console.log(`Using reviewer version ${rVersion} for rejected subpolicy ${subpolicy.SubPolicyId}`);
            subpolicy.reviewerVersion = rVersion;
            
            // If we have approval data with this subpolicy, use it
            if (versionResponse.data.approval_data && 
                versionResponse.data.approval_data.ExtractedData && 
                versionResponse.data.approval_data.ExtractedData.subpolicies) {
              
              const approvalData = versionResponse.data.approval_data;
              
              // Find this subpolicy in the ExtractedData
              const subpolicyData = approvalData.ExtractedData.subpolicies.find(
                s => s.SubPolicyId === subpolicy.SubPolicyId
              );
              
              if (subpolicyData) {
                // Keep original values for comparison
                const originalDescription = subpolicy.originalDescription;
                const originalControl = subpolicy.originalControl;
                
                // Update this subpolicy with the R version data
                Object.assign(subpolicy, subpolicyData);
                
                // Restore original values for comparison
                subpolicy.originalDescription = originalDescription;
                subpolicy.originalControl = originalControl;
                
                // Make sure approval object exists
                if (!subpolicy.approval) {
                  subpolicy.approval = { remarks: '', approved: false };
                }
                
                console.log(`Updated subpolicy ${subpolicy.SubPolicyId} with R version data for inline edit`);
              }
            }
          })
          .catch(error => {
            console.error('Error fetching reviewer version:', error);
            subpolicy.reviewerVersion = 'R1'; // Default fallback
          });
      }
      
      // Show the edit modal
      subpolicy.showEditForm = true;
    },
    hideEditFormInline(subpolicy) {
      subpolicy.showEditForm = false;
    },
    resubmitSubpolicy() {
      if (!this.editingSubpolicy || !this.editingSubpolicy.SubPolicyId) {
        console.error('Missing SubPolicyId, cannot resubmit subpolicy', this.editingSubpolicy);
        PopupService.error('Error: Cannot resubmit subpolicy - missing SubPolicyId', 'Missing ID Error');
        this.sendPushNotification({
          title: 'Subpolicy Resubmission Error',
          message: 'Cannot resubmit subpolicy - missing SubPolicyId',
          category: 'policy',
          priority: 'high',
          user_id: this.currentUserId || 'default_user'
        });
        return;
      }
      
      // Check if any changes were made
      if (!this.hasChanges) {
        PopupService.warning('No changes detected. Please modify the subpolicy before resubmitting.', 'No Changes');
        this.sendPushNotification({
          title: 'No Changes Detected',
          message: 'No changes detected. Please modify the subpolicy before resubmitting.',
          category: 'policy',
          priority: 'medium',
          user_id: this.currentUserId || 'default_user'
        });
        return;
      }
      
      const updateData = {
        Control: this.editingSubpolicy.Control,
        Description: this.editingSubpolicy.Description,
        SubPolicyId: this.editingSubpolicy.SubPolicyId
      };
      
      // Send the resubmit request
      axios.put(API_ENDPOINTS.SUBPOLICY_RESUBMIT(this.editingSubpolicy.SubPolicyId), updateData)
          .then(response => {
              console.log('Subpolicy resubmitted successfully:', response.data);
              
              // Update the UI with new version
              const newVersion = response.data.version;
              this.editingSubpolicy.Status = 'Under Review';
              this.editingSubpolicy.version = newVersion;
              
              if (!this.editingSubpolicy.approval) {
                  this.editingSubpolicy.approval = {};
              }
              this.editingSubpolicy.approval.approved = null;
              this.editingSubpolicy.resubmitted = true;
              
              // Show success message with new version
                      PopupService.success(`Subpolicy "${this.editingSubpolicy.SubPolicyName}" resubmitted successfully!`, 'Subpolicy Resubmitted');
        this.sendPushNotification({
          title: 'Subpolicy Resubmitted',
          message: `Subpolicy "${this.editingSubpolicy.SubPolicyName}" resubmitted successfully!`,
                category: 'policy',
                priority: 'medium',
                user_id: this.currentUserId || 'default_user'
              });
              
              // Close the edit modal
              this.closeEditSubpolicyModal();
              
              // Refresh data
              this.fetchRejectedSubpolicies();
              this.refreshData();
          })
          .catch(error => {
              console.error('Error resubmitting subpolicy:', error.response || error);
              PopupService.error(`Error resubmitting subpolicy: ${error.response?.data?.error || error.message}`, 'Resubmission Error');
              this.sendPushNotification({
                title: 'Subpolicy Resubmission Error',
                message: `Error resubmitting subpolicy: ${error.response?.data?.error || error.message}`,
                category: 'policy',
                priority: 'high',
                user_id: this.currentUserId || 'default_user'
              });
          });
    },
    
    // Check if any changes were made to the policy
    checkPolicyChanges(policy) {
      console.log('Checking for policy changes...');
      
      // Get the original rejected version for comparison
      // We need to compare against the original rejected data, not the current data
      const originalData = this.originalPolicyData || policy.ExtractedData || {};
      // const rejectionReason = this.getRejectionReason(policy); // Temporarily disabled
      
      // Check if any main policy fields have been modified
      const mainFieldsChanged = (
        originalData.PolicyName !== policy.ExtractedData?.PolicyName ||
        originalData.PolicyDescription !== policy.ExtractedData?.PolicyDescription ||
        originalData.Scope !== policy.ExtractedData?.Scope ||
        originalData.Objective !== policy.ExtractedData?.Objective ||
        originalData.Department !== policy.ExtractedData?.Department ||
        originalData.Applicability !== policy.ExtractedData?.Applicability
      );
      
      // Check if any subpolicies have been modified
      let subpoliciesChanged = false;
      if (originalData.subpolicies && Array.isArray(originalData.subpolicies)) {
        for (let i = 0; i < originalData.subpolicies.length; i++) {
          const originalSubpolicy = originalData.subpolicies[i];
          const currentSubpolicy = policy.ExtractedData?.subpolicies?.[i];
          
          if (currentSubpolicy) {
            if (originalSubpolicy.Description !== currentSubpolicy.Description ||
                originalSubpolicy.Control !== currentSubpolicy.Control ||
                originalSubpolicy.SubPolicyName !== currentSubpolicy.SubPolicyName) {
              subpoliciesChanged = true;
              break;
            }
          }
        }
      }
      
      // Check if rejection reason has been addressed (this counts as a change)
      // Only count as change if user has actually addressed the rejection reason
      const rejectionAddressed = false; // We'll implement this later if needed
      
      const hasChanges = mainFieldsChanged || subpoliciesChanged || rejectionAddressed;
      
      console.log('Policy change detection results:', {
        mainFieldsChanged,
        subpoliciesChanged,
        rejectionAddressed,
        hasChanges,
        originalData: {
          PolicyName: originalData.PolicyName,
          PolicyDescription: originalData.PolicyDescription,
          Scope: originalData.Scope,
          Objective: originalData.Objective,
          Department: originalData.Department,
          Applicability: originalData.Applicability
        },
        currentData: {
          PolicyName: policy.ExtractedData?.PolicyName,
          PolicyDescription: policy.ExtractedData?.PolicyDescription,
          Scope: policy.ExtractedData?.Scope,
          Objective: policy.ExtractedData?.Objective,
          Department: policy.ExtractedData?.Department,
          Applicability: policy.ExtractedData?.Applicability
        }
      });
      
      return hasChanges;
    },
    
    // Get rejection reason for policy
    getRejectionReason(policy) {
      // Check all possible locations for rejection reason
      if (policy.rejectionReason && policy.rejectionReason !== 'No rejection reason provided') {
        return policy.rejectionReason;
      }
      
      if (policy.ExtractedData?.rejection_reason) {
        return policy.ExtractedData.rejection_reason;
      }
      
      if (policy.ExtractedData?.policy_approval?.remarks) {
        return policy.ExtractedData.policy_approval.remarks;
      }
      
      if (policy.ExtractedData?.cascading_rejection) {
        return `Cascading rejection due to ${policy.ExtractedData.rejected_subpolicy_name || 'subpolicy'} rejection`;
      }
      
      // Check for subpolicy rejection reasons in ExtractedData
      if (policy.ExtractedData?.subpolicies && Array.isArray(policy.ExtractedData.subpolicies)) {
        for (const subpolicy of policy.ExtractedData.subpolicies) {
          if (subpolicy.approval?.remarks && subpolicy.approval.remarks.trim() !== '') {
            return `Subpolicy ${subpolicy.Identifier || subpolicy.SubPolicyId} rejection: ${subpolicy.approval.remarks}`;
          }
        }
      }
      
      // Also check in the direct subpolicies array if it exists
      if (policy.subpolicies && Array.isArray(policy.subpolicies)) {
        for (const subpolicy of policy.subpolicies) {
          if (subpolicy.approval?.remarks && subpolicy.approval.remarks.trim() !== '') {
            return `Subpolicy ${subpolicy.Identifier || subpolicy.SubPolicyId} rejection: ${subpolicy.approval.remarks}`;
          }
        }
      }
      
      return '';
    },
    
    // Add a helper method to update subpolicy references across the UI
    updateSubpolicyReferences(subpolicyId, updates) {
      // Update in selectedApproval if applicable
      if (this.selectedApproval?.ExtractedData?.subpolicies) {
        const subpolicy = this.selectedApproval.ExtractedData.subpolicies.find(
          sub => sub.SubPolicyId === subpolicyId
        );
        if (subpolicy) {
          Object.assign(subpolicy, updates);
        }
      }
      
      // Update in selectedPolicyForSubpolicies if applicable
      if (this.selectedPolicyForSubpolicies?.ExtractedData?.subpolicies) {
        const subpolicy = this.selectedPolicyForSubpolicies.ExtractedData.subpolicies.find(
          sub => sub.SubPolicyId === subpolicyId
        );
        if (subpolicy) {
          Object.assign(subpolicy, updates);
        }
      }
      
      // Update in rejectedSubpolicies if applicable
      const rejectedSubpolicy = this.rejectedSubpolicies.find(
        sub => sub.SubPolicyId === subpolicyId
      );
      if (rejectedSubpolicy) {
        Object.assign(rejectedSubpolicy, updates);
      }
    },
    resubmitSubpolicyDirect(subpolicy) {
      if (!subpolicy.SubPolicyId) {
        console.error('Missing SubPolicyId, cannot resubmit subpolicy', subpolicy);
        PopupService.error('Error: Cannot resubmit subpolicy - missing SubPolicyId', 'Missing ID Error');
        this.sendPushNotification({
          title: 'Subpolicy Resubmission Error',
          message: 'Cannot resubmit subpolicy - missing SubPolicyId',
          category: 'policy',
          priority: 'high',
          user_id: this.currentUserId || 'default_user'
        });
        return;
      }
      
      // Check if any changes were made
      const hasChanges = (
        subpolicy.Description !== subpolicy.originalDescription ||
        subpolicy.Control !== subpolicy.originalControl
      );
      
      if (!hasChanges) {
        PopupService.warning('No changes detected. Please modify the subpolicy before resubmitting.', 'No Changes');
        this.sendPushNotification({
          title: 'No Changes Detected',
          message: 'No changes detected. Please modify the subpolicy before resubmitting.',
          category: 'policy',
          priority: 'medium',
          user_id: this.currentUserId || 'default_user'
        });
        return;
      }
      
      console.log('Resubmitting subpolicy with ID:', subpolicy.SubPolicyId);
      console.log('Changes detected in inline edit form');
      
      // Store original values before resubmitting
      const previousVersion = {
        Description: subpolicy.originalDescription,
        Control: subpolicy.originalControl
      };
      
      // Mark as resubmitted
      subpolicy.resubmitted = true;
      
      // Prepare data to send to the backend
      const updateData = {
        Control: subpolicy.Control,
        Description: subpolicy.Description,
        previousVersion: previousVersion,
        SubPolicyId: subpolicy.SubPolicyId
      };
      
      // Send the updated subpolicy data to the resubmit endpoint
      axios.put(API_ENDPOINTS.SUBPOLICY_RESUBMIT(subpolicy.SubPolicyId), updateData)
      .then(response => {
          console.log('Subpolicy resubmitted successfully:', response.data);
          
          // Update the UI to show resubmitted status
          subpolicy.Status = 'Under Review';
          if (!subpolicy.approval) {
            subpolicy.approval = {};
          }
          subpolicy.approval.approved = null;
          subpolicy.previousVersion = previousVersion;
          
          if (response.data.Version) {
            subpolicy.version = response.data.Version;
          }
          
          // Show success message
                  PopupService.success(`Subpolicy "${subpolicy.SubPolicyName}" resubmitted successfully!`, 'Subpolicy Resubmitted');
        this.sendPushNotification({
          title: 'Subpolicy Resubmitted',
          message: `Subpolicy "${subpolicy.SubPolicyName}" resubmitted successfully!`,
            category: 'policy',
            priority: 'medium',
            user_id: this.currentUserId || 'default_user'
          });
          
          // Hide the edit form
        this.hideEditFormInline(subpolicy);
        
          // Close the modal after successful resubmission
          this.closeSubpoliciesModal();
          
          // Refresh the data
          this.fetchRejectedSubpolicies();
          this.fetchPolicies();
      })
      .catch(error => {
          console.error('Error resubmitting subpolicy:', error.response || error);
          PopupService.error(`Error resubmitting subpolicy: ${error.response?.data?.error || error.message}`, 'Resubmission Error');
          this.sendPushNotification({
            title: 'Subpolicy Resubmission Error',
            message: `Error resubmitting subpolicy: ${error.response?.data?.error || error.message}`,
            category: 'policy',
            priority: 'high',
            user_id: this.currentUserId || 'default_user'
          });
      });
    },
    getSubpolicyVersion(subpolicy) {
      if (subpolicy.version) {
        return subpolicy.version;
      } else if (subpolicy.approval && subpolicy.approval.version) {
        return subpolicy.approval.version;
      } else {
        return 'u1'; // Default version
      }
    },
    openSubpoliciesModal(policy) {
      this.selectedPolicyForSubpolicies = policy;
      
      // If policy is already approved, mark all subpolicies as approved
      if (policy.ExtractedData && 
          (policy.ApprovedNot === true || policy.ExtractedData.Status === 'Approved') && 
          policy.ExtractedData.subpolicies) {
        
        // Make a deep copy to avoid modifying the original data
        this.selectedPolicyForSubpolicies = JSON.parse(JSON.stringify(policy));
        
        // When a policy is approved, mark all subpolicies as approved too
        this.selectedPolicyForSubpolicies.ExtractedData.subpolicies = 
          this.selectedPolicyForSubpolicies.ExtractedData.subpolicies.map(sub => {
            if (!sub.approval) {
              sub.approval = {};
            }
            sub.approval.approved = true;
            sub.Status = 'Approved';
            return sub;
          });
      } else if (policy.ExtractedData && 
          (policy.ApprovedNot === false || policy.ExtractedData.Status === 'Rejected') && 
          policy.ExtractedData.subpolicies) {
        
        // Make a deep copy for rejected policies
        this.selectedPolicyForSubpolicies = JSON.parse(JSON.stringify(policy));
        
        // For rejected policies, fetch the latest reviewer version (R1, R2, etc.) with full data
        const policyId = this.getPolicyId(policy);
        
        // Fetch the latest R version for the policy with its approval data
        axios.get(API_ENDPOINTS.POLICY_REVIEWER_VERSION(policyId))
          .then(versionResponse => {
            const rVersion = versionResponse.data.version || 'R1';
            console.log(`Using reviewer version: ${rVersion} for policy ${policyId}`);
            
            // If we have approval data, use it to replace the current data
            if (versionResponse.data.approval_data) {
              const approvalData = versionResponse.data.approval_data;
              console.log('Found R version approval data:', approvalData);
              
              // Use the ExtractedData from the R version instead of the current data
              if (approvalData.ExtractedData) {
                // Keep reference to original policy for ID, etc.
                const originalPolicy = this.selectedPolicyForSubpolicies;
                
                // Replace the extracted data with the R version data
                this.selectedPolicyForSubpolicies = {
                  ...originalPolicy,
                  ExtractedData: approvalData.ExtractedData,
                  reviewerVersion: rVersion,
                  ApprovalId: approvalData.ApprovalId,
                  Version: approvalData.Version
                };
                
                console.log('Updated policy data with R version data:', this.selectedPolicyForSubpolicies);
              }
            } else {
              // Just update the version info if we don't have approval data
              this.selectedPolicyForSubpolicies.reviewerVersion = rVersion;
              
              // Now fetch R versions for each subpolicy
              this.fetchSubpolicyVersions();
            }
          })
          .catch(error => {
            console.error('Error fetching policy reviewer version:', error);
            // Try to fetch subpolicy versions anyway
            this.fetchSubpolicyVersions();
          });
      }
      
      this.showSubpoliciesModal = true;

      // If in user mode, ensure rejected subpolicies show edit options immediately
      if (!this.isReviewer) {
        // Process each subpolicy to ensure rejected ones can be edited
        setTimeout(() => {
          if (this.selectedPolicyForSubpolicies && 
              this.selectedPolicyForSubpolicies.ExtractedData && 
              this.selectedPolicyForSubpolicies.ExtractedData.subpolicies) {
            
            this.selectedPolicyForSubpolicies.ExtractedData.subpolicies.forEach(sub => {
              if (sub.Status === 'Rejected' || 
                 (sub.approval && sub.approval.approved === false)) {
                // Pre-populate the edit form for rejected subpolicies
                sub.showEditForm = true;
              }
            });
          }
        }, 100); // Small delay to ensure DOM is updated
      }
    },
    
    // Helper method to fetch subpolicy versions
    fetchSubpolicyVersions() {
      if (this.selectedPolicyForSubpolicies && 
          this.selectedPolicyForSubpolicies.ExtractedData && 
          this.selectedPolicyForSubpolicies.ExtractedData.subpolicies) {
        
        const promises = this.selectedPolicyForSubpolicies.ExtractedData.subpolicies.map(sub => {
          if (sub.SubPolicyId) {
            return axios.get(API_ENDPOINTS.SUBPOLICY_REVIEWER_VERSION(sub.SubPolicyId))
              .then(subVersionResponse => {
                const subRVersion = subVersionResponse.data.version || 'R1';
                console.log(`Subpolicy ${sub.SubPolicyId} reviewer version: ${subRVersion}`);
                
                // Store reviewer version
                sub.reviewerVersion = subRVersion;
                
                // If we have approval data for this subpolicy, update its data
                if (subVersionResponse.data.approval_data && 
                    subVersionResponse.data.approval_data.ExtractedData && 
                    subVersionResponse.data.approval_data.ExtractedData.subpolicies) {
                  
                  const approvalData = subVersionResponse.data.approval_data;
                  
                  // Find this subpolicy in the ExtractedData
                  const subpolicyData = approvalData.ExtractedData.subpolicies.find(
                    s => s.SubPolicyId === sub.SubPolicyId
                  );
                  
                  if (subpolicyData) {
                    // Update this subpolicy with the R version data
                    Object.assign(sub, subpolicyData);
                    console.log(`Updated subpolicy ${sub.SubPolicyId} with R version data`);
                  }
                }
                
                return sub;
              })
              .catch(err => {
                console.error(`Error fetching reviewer version for subpolicy ${sub.SubPolicyId}:`, err);
                sub.reviewerVersion = 'R1'; // Default fallback
                return sub;
              });
          } else {
            sub.reviewerVersion = 'R1'; // Default for subpolicies without ID
            return Promise.resolve(sub);
          }
        });
        
        Promise.all(promises).then(() => {
          console.log('All reviewer versions fetched for subpolicies');
        });
      }
    },
    closeSubpoliciesModal() {
      this.selectedPolicyForSubpolicies = null;
      this.showSubpoliciesModal = false;
    },
    approveSubpolicyFromModal(subpolicy) {
      // Set subpolicy approval status in UI
      if (!subpolicy.approval) {
        subpolicy.approval = {};
      }
      subpolicy.approval.approved = true;
      subpolicy.approval.remarks = '';
      
      // Set review decision for policy reviews
      this.reviewDecision = 'approve';
      
      // Submit subpolicy review directly (this handles both status update and approval)
      axios.put(API_ENDPOINTS.SUBPOLICY_REVIEW(subpolicy.SubPolicyId), {
        Status: 'Approved'
      })
      .then(response => {
        console.log('Subpolicy approval submitted successfully:', response.data);
        
        // Update the subpolicy status in the UI
        subpolicy.Status = 'Approved';
        
        // Check if parent policy status was updated (all subpolicies approved)
        if (response.data.PolicyUpdated) {
          console.log(`Policy status updated to: ${response.data.PolicyStatus}`);
          
          // If parent policy was updated, refresh the policies list
          this.fetchPolicies();
          
          // Update the UI to show the policy is now approved
          if (this.selectedPolicyForSubpolicies && 
              this.selectedPolicyForSubpolicies.ExtractedData) {
            this.selectedPolicyForSubpolicies.ExtractedData.Status = response.data.PolicyStatus;
          }
        }
        
        // Check if all subpolicies in the modal are approved
        this.checkAllModalSubpoliciesApproved();
        
        // Show success message
        PopupService.success('Subpolicy approved successfully!', 'Approval Success');
      })
      .catch(error => {
        console.error('Error approving subpolicy:', error);
        PopupService.error('Error approving subpolicy. Please try again.', 'Approval Error');
        this.sendPushNotification({
          title: 'Subpolicy Approval Error',
          message: 'Error approving subpolicy. Please try again.',
          category: 'policy',
          priority: 'high',
          user_id: this.currentUserId || 'default_user'
        });
      });
    },
    
    // Add a method to check if all subpolicies in the modal view are approved
    checkAllModalSubpoliciesApproved() {
      if (!this.selectedPolicyForSubpolicies || 
          !this.selectedPolicyForSubpolicies.ExtractedData || 
          !this.selectedPolicyForSubpolicies.ExtractedData.subpolicies ||
          this.selectedPolicyForSubpolicies.ExtractedData.subpolicies.length === 0) {
        return;
      }
      
      const subpolicies = this.selectedPolicyForSubpolicies.ExtractedData.subpolicies;
      const allApproved = subpolicies.every(sub => sub.approval?.approved === true);
      
      if (allApproved) {
        console.log('All subpolicies in the modal are approved! The policy should be automatically approved');
        
        // Automatically set policy approval to true
        if (!this.selectedPolicyForSubpolicies.ExtractedData.policy_approval) {
          this.selectedPolicyForSubpolicies.ExtractedData.policy_approval = {};
        }
        this.selectedPolicyForSubpolicies.ExtractedData.policy_approval.approved = true;
        this.selectedPolicyForSubpolicies.ApprovedNot = true;
        
        // Show notification to user
        PopupService.success('All subpolicies are approved! The policy has been automatically approved.', 'Auto-Approval');
        this.sendPushNotification({
          title: 'All Subpolicies Approved',
          message: 'All subpolicies are approved! The policy has been automatically approved.',
          category: 'policy',
          priority: 'medium',
          user_id: this.currentUserId || 'default_user'
        });
      }
    },
    rejectSubpolicyFromModal(subpolicy) {
      // Open rejection modal for subpolicy
      this.rejectingType = 'subpolicy';
      this.rejectingSubpolicy = subpolicy;
      this.showRejectModal = true;
    },
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return ''; // Invalid date
      
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    },
    isNewPolicy(policy) {
      const createdDate = policy.ExtractedData?.CreatedByDate || policy.created_at;
      if (!createdDate) return false;
      
      const date = new Date(createdDate);
      if (isNaN(date.getTime())) return false; // Invalid date
      
      const threeDaysAgo = new Date();
      threeDaysAgo.setDate(threeDaysAgo.getDate() - 3); // Show new badge for 3 days
      
      return date > threeDaysAgo;
    },
    // Add a new method for opening the edit modal for a rejected subpolicy
    openEditSubpolicyModal(subpolicy) {
      // Create a deep copy of the subpolicy to edit
      this.editingSubpolicy = JSON.parse(JSON.stringify(subpolicy));
      
      // Store original values for comparison
      this.editingSubpolicy.originalDescription = subpolicy.Description;
      this.editingSubpolicy.originalControl = subpolicy.Control;
      
      // Fetch the latest reviewer version for this rejected subpolicy with complete data
      if (subpolicy.SubPolicyId) {
        axios.get(API_ENDPOINTS.SUBPOLICY_REVIEWER_VERSION(subpolicy.SubPolicyId))
          .then(versionResponse => {
            const rVersion = versionResponse.data.version || 'R1';
            console.log(`Fetched reviewer version for edit modal: ${rVersion}`);
            this.editingSubpolicy.reviewerVersion = rVersion;
            
            // If we have approval data with this subpolicy, use it
            if (versionResponse.data.approval_data && 
                versionResponse.data.approval_data.ExtractedData && 
                versionResponse.data.approval_data.ExtractedData.subpolicies) {
              
              const approvalData = versionResponse.data.approval_data;
              
              // Find this subpolicy in the ExtractedData
              const subpolicyData = approvalData.ExtractedData.subpolicies.find(
                s => s.SubPolicyId === subpolicy.SubPolicyId
              );
              
              if (subpolicyData) {
                // Keep original values for comparison
                const originalDescription = this.editingSubpolicy.originalDescription;
                const originalControl = this.editingSubpolicy.originalControl;
                
                // Update this subpolicy with the R version data
                Object.assign(this.editingSubpolicy, subpolicyData);
                
                // Restore original values for comparison
                this.editingSubpolicy.originalDescription = originalDescription;
                this.editingSubpolicy.originalControl = originalControl;
                
                console.log(`Updated subpolicy ${subpolicy.SubPolicyId} with R version data for edit modal`);
              }
            }
          })
          .catch(err => {
            console.error('Error fetching reviewer version:', err);
            this.editingSubpolicy.reviewerVersion = 'R1'; // Default
          });
      }
      
      // Show the edit modal
      this.showEditSubpolicyModal = true;
      
      console.log('Edit modal opened with subpolicy:', this.editingSubpolicy);
    },
    
    // Add a method to close the edit subpolicy modal
    closeEditSubpolicyModal() {
      this.showEditSubpolicyModal = false;
      this.editingSubpolicy = null;
    },
    
    // Helper method to find a subpolicy by ID
    findSubpolicyById(subpolicyId) {
      if (!this.selectedPolicyForSubpolicies || !this.selectedPolicyForSubpolicies.ExtractedData || !this.selectedPolicyForSubpolicies.ExtractedData.subpolicies) {
        return null;
      }
      
      return this.selectedPolicyForSubpolicies.ExtractedData.subpolicies.find(
        sub => sub.SubPolicyId === subpolicyId
      );
    },
    // Add method to fetch rejected subpolicies
    fetchRejectedSubpolicies() {
      console.log('Fetching rejected subpolicies...');
      // For now, we'll fetch all policies and filter for rejected subpolicies
      axios.get(API_ENDPOINTS.POLICIES)
        .then(response => {
          console.log('Received policies for subpolicy check:', response.data.length);
          const allPolicies = response.data;
          let rejectedSubs = [];
          
          // Go through each policy and collect rejected subpolicies
          allPolicies.forEach(policy => {
            if (policy.subpolicies && policy.subpolicies.length > 0) {
              console.log(`Policy ${policy.PolicyId} has ${policy.subpolicies.length} subpolicies`);
              const rejected = policy.subpolicies.filter(sub => sub.Status === 'Rejected');
              console.log(`Policy ${policy.PolicyId} has ${rejected.length} rejected subpolicies`);
              
              // Add policy info to each subpolicy for context
              rejected.forEach(sub => {
                sub.PolicyName = policy.PolicyName;
                sub.PolicyId = policy.PolicyId;
              });
              
              rejectedSubs = [...rejectedSubs, ...rejected];
            }
          });
          
          console.log('Total rejected subpolicies found:', rejectedSubs.length);
          this.rejectedSubpolicies = rejectedSubs;
          
          // If we're in user mode and there are rejected subpolicies, update the view
          if (!this.isReviewer && rejectedSubs.length > 0) {
            this.updateRejectedSubpoliciesView();
          }
        })
        .catch(error => {
          console.error('Error fetching rejected subpolicies:', error);
        });
    },
    // Add a method to update the rejected subpolicies view in user mode
    updateRejectedSubpoliciesView() {
      // Set the active tab to rejected if we have rejected subpolicies
      if (this.rejectedSubpolicies.length > 0) {
        this.activeTab = 'rejected';
      }
    },
    // Method to track changes in the edit form
    trackChanges() {
      // No need for complex logic here - Vue's reactivity will handle updates to the model
      // We just need this method to trigger when input happens
      console.log('Changes detected in form');
    },
    // Add helper method to increment version
    incrementVersion(currentVersion) {
      if (!currentVersion) return 'u1';
      const match = currentVersion.match(/u(\d+)/);
      if (!match) return 'u1';
      const num = parseInt(match[1]) + 1;
      return `u${num}`;
    },
    // Add this helper method
    getSubpolicyRemarks(sub) {
      return sub && sub.approval && sub.approval.remarks ? sub.approval.remarks : 'No reason provided';
    },
    // Add a method to fetch policy categories
    fetchPolicyCategories() {
      axios.get(API_ENDPOINTS.POLICY_CATEGORIES)
        .then(response => {
          // Handle both response formats: direct array or success wrapper
          if (response.data.success && response.data.data) {
            this.policyCategories = response.data.data;
          } else if (Array.isArray(response.data)) {
            this.policyCategories = response.data;
          } else {
            console.error('Unexpected response format:', response.data);
          }
        })
        .catch(error => {
          console.error('Error fetching policy categories:', error);
        });
    },
    fetchPolicyTypes() {
      console.log('Fetching policy categories...');
      axios.get(API_ENDPOINTS.POLICY_CATEGORIES)
        .then(response => {
          console.log('Policy categories response:', response.data);
          
          // Handle both response formats: direct array or success wrapper
          let categoriesData;
          if (response.data.success && response.data.data) {
            categoriesData = response.data.data;
          } else if (Array.isArray(response.data)) {
            categoriesData = response.data;
          } else {
            console.error('Unexpected response format:', response.data);
            return;
          }
          
          // Store the raw categories data
          this.policyCategories = categoriesData;
          
          // Create a structured map for easier filtering
          const typeMap = {};
          
          // Process the categories into a nested structure
          categoriesData.forEach(category => {
            if (!typeMap[category.PolicyType]) {
              typeMap[category.PolicyType] = {
                categories: {}
              };
            }
            
            if (!typeMap[category.PolicyType].categories[category.PolicyCategory]) {
              typeMap[category.PolicyType].categories[category.PolicyCategory] = {
                subCategories: []
              };
            }
            
            typeMap[category.PolicyType].categories[category.PolicyCategory].subCategories.push(
              category.PolicySubCategory
            );
          });
          
          this.policyCategoriesMap = typeMap;
          console.log('Processed policy categories map:', this.policyCategoriesMap);
        })
        .catch(error => {
          console.error('Error fetching policy categories:', error);
        });
    },
    // Helper method to initialize or update policy category fields
    initializePolicyCategoryFields(policy) {
      console.log(`Initializing policy category fields for policy: ${policy.PolicyId || 'New Policy'}`);
      
      // Initialize policy category fields if they don't exist
      if (!policy.ExtractedData.PolicyType) policy.ExtractedData.PolicyType = '';
      if (!policy.ExtractedData.PolicyCategory) policy.ExtractedData.PolicyCategory = '';
      if (!policy.ExtractedData.PolicySubCategory) policy.ExtractedData.PolicySubCategory = '';
      
      // Log current values
      console.log('Current policy category fields:', {
        PolicyType: policy.ExtractedData.PolicyType,
        PolicyCategory: policy.ExtractedData.PolicyCategory,
        PolicySubCategory: policy.ExtractedData.PolicySubCategory
      });
      
      return policy;
    },
    
    // Get policy rejection reason from multiple possible sources
    getPolicyRejectionReason(policy) {
      if (!policy) return null;
      
      console.log('Checking rejection reason for policy:', policy);
      
      // Check all possible locations for rejection reason
      if (policy.rejectionReason && policy.rejectionReason !== 'No rejection reason provided') {
        console.log('Found rejection reason in policy.rejectionReason:', policy.rejectionReason);
        return policy.rejectionReason;
      }
      
      if (policy.ExtractedData?.rejection_reason) {
        console.log('Found rejection reason in policy.ExtractedData.rejection_reason:', policy.ExtractedData.rejection_reason);
        return policy.ExtractedData.rejection_reason;
      }
      
      if (policy.ExtractedData?.policy_approval?.remarks) {
        console.log('Found rejection reason in policy.ExtractedData.policy_approval.remarks:', policy.ExtractedData.policy_approval.remarks);
        return policy.ExtractedData.policy_approval.remarks;
      }
      
      if (policy.ExtractedData?.cascading_rejection) {
        console.log('Found cascading rejection reason');
        return `Cascading rejection due to ${policy.ExtractedData.rejected_subpolicy_name || 'subpolicy'} rejection`;
      }
      
      // Check for subpolicy rejection reasons in ExtractedData
      if (policy.ExtractedData?.subpolicies && Array.isArray(policy.ExtractedData.subpolicies)) {
        console.log('Checking subpolicies in ExtractedData:', policy.ExtractedData.subpolicies);
        for (const subpolicy of policy.ExtractedData.subpolicies) {
          if (subpolicy.approval?.remarks && subpolicy.approval.remarks.trim() !== '') {
            console.log('Found subpolicy rejection reason in ExtractedData:', subpolicy.approval.remarks);
            return `Subpolicy ${subpolicy.Identifier || subpolicy.SubPolicyId} rejection: ${subpolicy.approval.remarks}`;
          }
        }
      }
      
      // Also check in the direct subpolicies array if it exists
      if (policy.subpolicies && Array.isArray(policy.subpolicies)) {
        console.log('Checking direct subpolicies:', policy.subpolicies);
        for (const subpolicy of policy.subpolicies) {
          if (subpolicy.approval?.remarks && subpolicy.approval.remarks.trim() !== '') {
            console.log('Found subpolicy rejection reason in direct subpolicies:', subpolicy.approval.remarks);
            return `Subpolicy ${subpolicy.Identifier || subpolicy.SubPolicyId} rejection: ${subpolicy.approval.remarks}`;
          }
        }
      }
      
      console.log('No rejection reason found');
      return null;
    },
    
    openRejectedPolicy(policy) {
      console.log('Opening rejected policy for editing:', policy);
      
      // Check if the policy can actually be resubmitted
      const policyId = this.getPolicyId(policy);
      console.log(`Checking if policy ${policyId} can be resubmitted...`);
      
      // First check the current policy status
              axios.get(API_ENDPOINTS.POLICY(policyId))
        .then(policyResponse => {
          const policyStatus = policyResponse.data.Status;
          console.log(`Current policy status: ${policyStatus}`);
          
          // Check if policy can be resubmitted
          if (policyStatus === 'Approved') {
            PopupService.warning('This policy has already been approved and cannot be resubmitted.', 'Policy Already Approved');
            this.sendPushNotification({
              title: 'Policy Already Approved',
              message: 'This policy has already been approved and cannot be resubmitted.',
              category: 'policy',
              priority: 'medium',
              user_id: this.currentUserId || 'default_user'
            });
            return;
          }
          
          if (policyStatus !== 'Rejected' && policyStatus !== 'Under Review') {
            PopupService.warning(`Cannot resubmit a policy with status '${policyStatus}'. Only rejected or under review policies can be resubmitted.`, 'Invalid Policy Status');
            this.sendPushNotification({
              title: 'Invalid Policy Status',
              message: `Cannot resubmit a policy with status '${policyStatus}'. Only rejected or under review policies can be resubmitted.`,
              category: 'policy',
              priority: 'medium',
              user_id: this.currentUserId || 'default_user'
            });
            return;
          }
          
          // If we reach here, the policy can be resubmitted
          this.editingPolicy = JSON.parse(JSON.stringify(policy)); // Deep copy
          
          // Store the original data for change detection
          this.originalPolicyData = JSON.parse(JSON.stringify(policy.ExtractedData || {}));
          
          // Log the editing policy data structure for debugging
          console.log('Editing policy data structure:', this.editingPolicy);
          console.log('Subpolicies in editing policy:', this.editingPolicy.subpolicies);
          console.log('ExtractedData in editing policy:', this.editingPolicy.ExtractedData);
          
          // Initialize policy category fields
          this.initializePolicyCategoryFields(this.editingPolicy);
          
          this.showEditModal = true;
        })
        .catch(error => {
          console.error('Error checking policy status:', error);
          PopupService.error('Error checking policy status. Please try again.', 'Status Check Error');
          this.sendPushNotification({
            title: 'Policy Status Check Error',
            message: 'Error checking policy status. Please try again.',
            category: 'policy',
            priority: 'high',
            user_id: this.currentUserId || 'default_user'
          });
        });
    },
    
    // Close the edit modal
    closeEditModal() {
      this.showEditModal = false;
      this.editingPolicy = null;
      this.originalPolicyData = null; // Clear original data
    },
    // Handle policy type change
    handlePolicyTypeChange(policy) {
      console.log(`Policy type changed to: ${policy.ExtractedData.PolicyType}`);
      // Reset dependent fields when type changes
      policy.ExtractedData.PolicyCategory = '';
      policy.ExtractedData.PolicySubCategory = '';
    },
    
    // Handle policy category change
    handlePolicyCategoryChange(policy) {
      console.log(`Policy category changed to: ${policy.ExtractedData.PolicyCategory}`);
      // Reset subcategory when category changes
      policy.ExtractedData.PolicySubCategory = '';
    },
    // Collapsible Table Methods
    transformApprovalToTask(approval) {
      if (!approval) {
        return {
          incidentId: 'N/A',
          policyName: 'Unknown',
          type: 'Policy',
          scope: 'No Scope',
          createdBy: 'System',
          createdDate: 'N/A',
          originalApproval: null
        };
      }
      
      const policyId = this.getPolicyId(approval);
      
      return {
        incidentId: policyId, // Using policyId as incidentId for compatibility
        policyName: approval.ExtractedData?.PolicyName || policyId,
        type: approval.ExtractedData?.type === 'subpolicy' ? 'Subpolicy' : 'Policy',
        scope: approval.ExtractedData?.Scope || 'No Scope',
        createdBy: approval.ExtractedData?.CreatedByName || 'System',
        createdDate: this.formatDate(approval.ExtractedData?.CreatedByDate || approval.created_at),
        originalApproval: approval, // Keep reference to original data
        originalData: approval // Also include originalData for compatibility with editTask handler
      };
    },
    
    mapPolicyToTableRow(policy) {
      if (!policy) {
        return {
          incidentId: 'N/A',
          policyName: 'Unknown',
          type: 'Policy',
          scope: 'No Scope',
          createdBy: 'System',
          createdDate: 'N/A',
          originalData: null
        };
      }
      
      // Use originalPolicy if available (from rejectedPolicies array), otherwise use policy directly
      const policyData = policy.originalPolicy || policy;
      const policyId = policy.policyId || this.getPolicyId(policyData);
      
      return {
        incidentId: policyId, // Using policyId as incidentId for compatibility
        policyName: policy.ExtractedData?.PolicyName || policy.description || policyId,
        type: policy.ExtractedData?.type === 'subpolicy' ? 'Subpolicy' : (policy.type === 'POLICY' ? 'Policy' : 'Policy'),
        scope: policy.ExtractedData?.Scope || 'No Scope',
        createdBy: policy.ExtractedData?.CreatedByName || 'System',
        createdDate: this.formatDate(policy.ExtractedData?.CreatedByDate || policy.createdDate),
        originalData: policyData // Store original policy/approval data for edit handler
      };
    },
    
    getApprovalStatus(approval) {
      if (!approval) {
        return 'pending';
      }
      
      if (approval.dbStatus === 'Approved' || approval.ApprovedNot === true || approval.ExtractedData?.Status === 'Approved') {
        return 'approved';
      } else if (approval.dbStatus === 'Rejected' || approval.ApprovedNot === false || approval.ExtractedData?.Status === 'Rejected') {
        return 'rejected';
      } else {
        return 'pending';
      }
    },
    
    getStatusBadge(status) {
      const statusConfig = {
        pending: '<span class="status-badge status-pending">Pending</span>',
        approved: '<span class="status-badge status-approved">Approved</span>',
        rejected: '<span class="status-badge status-rejected">Rejected</span>'
      };
      return statusConfig[status] || statusConfig.pending;
    },
    
    toggleSection(sectionName) {
      this.expandedSections[sectionName.toLowerCase()] = !this.expandedSections[sectionName.toLowerCase()];
    },
    
    handleTaskClick(task) {
      // Find the original approval data
      const approval = task.originalApproval;
      if (!approval) return;
      
      // Get policy information
      const policyId = this.getPolicyId(approval);
      
      // Store the policy data in sessionStorage for the PolicyDetails page
      sessionStorage.setItem('policyData', JSON.stringify(approval));
      
      // Navigate to PolicyDetails page
      this.$router.push({
        name: 'PolicyDetails',
        params: { policyId: policyId }
      });
    },
    
    // Determine if user should see review history instead of details
    shouldShowReviewHistory(approval, currentStatus) {
      // Show review history only if:
      // 1. Policy has been reviewed (approved or rejected) AND
      // 2. Current user is the policy creator
      // This ensures we only show review history when there's actually history to show
      
      const isPolicyCreator = approval.UserId === this.currentUserId;
      const hasBeenReviewed = currentStatus === 'approved' || currentStatus === 'rejected';
      
      // Show review history for creators viewing their reviewed policies
      // Show regular details for all other cases (pending policies, reviewers, etc.)
      return isPolicyCreator && hasBeenReviewed;
    },

    // Get CSS class for policy status pill
    getPolicyStatusClass(approval) {
      const status = this.getApprovalStatus(approval);
      switch (status) {
        case 'approved':
          return 'status-approved';
        case 'rejected':
          return 'status-rejected';
        case 'pending':
        default:
          return 'status-pending';
      }
    },
    
    // Generate collapsible sections for any task array
    generateCollapsibleSections(tasks) {
      console.log('generateCollapsibleSections called with tasks:', tasks?.length);
      if (!tasks || !Array.isArray(tasks)) {
        return [];
      }
      
      const sections = [];
      const sectionNames = [
        { key: 'pending', label: 'Pending' },
        { key: 'approved', label: 'Approved' },
        { key: 'rejected', label: 'Rejected' }
      ];
      
      sectionNames.forEach(({ key, label }) => {
        const allTasks = tasks
          .filter(a => {
            const status = this.getApprovalStatus(a);
            if (key === 'pending') return status === 'pending';
            if (key === 'approved') return status === 'approved';
            if (key === 'rejected') return status === 'rejected';
          })
          .map(this.transformApprovalToTask);
        
        const pageSize = this.collapsiblePagination[key].pageSize;
        const currentPage = this.collapsiblePagination[key].currentPage;
        const totalPages = Math.max(1, Math.ceil(allTasks.length / pageSize));
        const pagedTasks = allTasks.slice((currentPage - 1) * pageSize, currentPage * pageSize);
        
        console.log(`Section ${key}:`, {
          totalTasks: allTasks.length,
          pageSize,
          currentPage,
          totalPages,
          pagedTasksCount: pagedTasks.length
        });
        
        if (allTasks.length > 0) {
          sections.push({
            name: label,
            statusClass: key,
            tasks: pagedTasks,
            pagination: {
              currentPage,
              totalPages,
              pageSize,
              totalCount: allTasks.length,
              pageSizeOptions: [6, 15, 30, 50],
              onPageSizeChange: (size) => {
                console.log(`Page size change for ${key}:`, size);
                this.collapsiblePagination[key].pageSize = size;
                this.collapsiblePagination[key].currentPage = 1;
                // Trigger reactivity by incrementing the trigger
                this.paginationUpdateTrigger++;
              },
              onPageChange: (page) => {
                console.log(`Page change for ${key}:`, page);
                this.collapsiblePagination[key].currentPage = page;
                // Trigger reactivity by incrementing the trigger
                this.paginationUpdateTrigger++;
              }
            }
          });
        }
      });
      
      return sections;
    },

    // Dynamic Table Methods
  },
  computed: {
    policyApprovals() {
      // Return all approvals since we're now directly using the policies data
      return this.approvals;
    },
    
    // Combined tasks for overall counts
    allTasks() {
      const myTasks = this.myTasks || [];
      const reviewerTasks = this.reviewerTasks || [];
      return [...myTasks, ...reviewerTasks];
    },
    
    pendingApprovalsCount() {
      return this.allTasks.filter(a => a.ApprovedNot === null).length;
    },
    approvedApprovalsCount() {
      return this.allTasks.filter(a => a.ApprovedNot === true).length;
    },
    rejectedApprovalsCount() {
      return this.allTasks.filter(a => a.ApprovedNot === false).length;
    },
    
    // Tab-specific counts
    myTasksCount() {
      return this.myTasks ? this.myTasks.length : 0;
    },
    reviewerTasksCount() {
      return this.reviewerTasks ? this.reviewerTasks.length : 0;
    },
    sortedPolicies() {
      return [...this.approvals].sort((a, b) => {
        const dateA = new Date(a.ExtractedData?.CreatedByDate || 0);
        const dateB = new Date(b.ExtractedData?.CreatedByDate || 0);
        return dateB - dateA; // Most recent first
      });
    },
    
    // Collapsible Table Computed Properties for My Tasks
    myTasksCollapsibleSections() {
      // Include paginationUpdateTrigger to ensure reactivity
      this.paginationUpdateTrigger;
      if (!this.myTasks || !Array.isArray(this.myTasks)) {
        return [];
      }
      return this.generateCollapsibleSections(this.myTasks);
    },
    
    // Collapsible Table Computed Properties for Reviewer Tasks
    reviewerTasksCollapsibleSections() {
      // Include paginationUpdateTrigger to ensure reactivity
      this.paginationUpdateTrigger;
      if (!this.reviewerTasks || !Array.isArray(this.reviewerTasks)) {
        return [];
      }
      return this.generateCollapsibleSections(this.reviewerTasks);
    },
    
    // Legacy computed property for backwards compatibility
    collapsibleTableSections() {
      return this.generateCollapsibleSections(this.approvals);
    },
    
    policyTypeOptions() {
      // Get unique policy types from the structured map
      return Object.keys(this.policyCategoriesMap);
    },
    filteredPolicyCategories() {
      return (policyType) => {
        if (!policyType || !this.policyCategoriesMap[policyType]) return [];
        // Get categories for the selected policy type
        return Object.keys(this.policyCategoriesMap[policyType].categories);
      };
    },
    filteredPolicySubCategories() {
      return (policyType, policyCategory) => {
        if (!policyType || !policyCategory || 
            !this.policyCategoriesMap[policyType] || 
            !this.policyCategoriesMap[policyType].categories[policyCategory]) {
          return [];
        }
        // Get subcategories for the selected policy type and category
        return this.policyCategoriesMap[policyType].categories[policyCategory].subCategories;
      };
    },
    hasUnreviewedSubpolicies() {
      if (!this.selectedApproval || !this.selectedApproval.ExtractedData || 
          !this.selectedApproval.ExtractedData.subpolicies) {
        return true;
      }
      
      const subpolicies = this.selectedApproval.ExtractedData.subpolicies;
      return subpolicies.some(sub => {
        return sub.approval?.approved === null || sub.approval?.approved === undefined;
      });
    },
    hasPolicyChanges() {
      if (!this.editingPolicy) return false;
      return this.checkPolicyChanges(this.editingPolicy);
    },
    hasRejectedSubpolicies() {
      console.log('Checking hasRejectedSubpolicies:', {
        editingPolicy: this.editingPolicy,
        hasExtractedData: this.editingPolicy?.ExtractedData,
        hasSubpolicies: this.editingPolicy?.ExtractedData?.subpolicies,
        subpoliciesCount: this.editingPolicy?.ExtractedData?.subpolicies?.length
      });
      
      if (!this.editingPolicy || !this.editingPolicy.ExtractedData || !this.editingPolicy.ExtractedData.subpolicies) {
        console.log('No subpolicies found in editingPolicy');
        return false;
      }
      
      const rejectedSubpolicies = this.editingPolicy.ExtractedData.subpolicies.filter(sub => 
        sub.approval?.approved === false || sub.Status === 'Rejected'
      );
      
      console.log('Rejected subpolicies found:', rejectedSubpolicies);
      console.log('All subpolicies:', this.editingPolicy.ExtractedData.subpolicies);
      
      return rejectedSubpolicies.length > 0;
    },
    
    // Check if there are any pending rejections (stored locally but not saved to DB)
    hasPendingRejections() {
      if (!this.selectedApproval) return false;
      
      // Check if policy itself has pending rejection
      if (this.selectedApproval.pendingRejection) {
        return true;
      }
      
      // Check if any subpolicies have pending rejections
      if (this.selectedApproval.ExtractedData && this.selectedApproval.ExtractedData.subpolicies) {
        return this.selectedApproval.ExtractedData.subpolicies.some(subpolicy => 
          subpolicy.pendingRejection
        );
      }
      
      return false;
    },
    hasChanges() {
      if (!this.editingSubpolicy) return false;
      
      // Check if Description or Control have changed from their original values
      const descriptionChanged = this.editingSubpolicy.Description !== this.editingSubpolicy.originalDescription;
      const controlChanged = this.editingSubpolicy.Control !== this.editingSubpolicy.originalControl;
      
      return descriptionChanged || controlChanged;
    },
    rejectedSubpoliciesInPolicy() {
      console.log('Getting rejectedSubpoliciesInPolicy:', {
        editingPolicy: this.editingPolicy,
        hasExtractedData: this.editingPolicy?.ExtractedData,
        hasSubpolicies: this.editingPolicy?.ExtractedData?.subpolicies
      });
      
      if (!this.editingPolicy || !this.editingPolicy.ExtractedData || !this.editingPolicy.ExtractedData.subpolicies) {
        console.log('No subpolicies found in editingPolicy for rejectedSubpoliciesInPolicy');
        return [];
      }
      
      const rejectedSubpolicies = this.editingPolicy.ExtractedData.subpolicies.filter(sub => 
        sub.approval?.approved === false || sub.Status === 'Rejected'
      );
      
      console.log('Filtered rejected subpolicies:', rejectedSubpolicies);
      return rejectedSubpolicies;
    },
    isComplianceApproval() {
      return this.selectedApproval?.ExtractedData?.type === 'compliance';
    },
    
    // Determine if user is viewing review history in the details modal
    isUserViewingReviewHistory() {
      if (!this.selectedApproval) return false;
      
      const currentStatus = this.getApprovalStatus(this.selectedApproval);
      return this.shouldShowReviewHistory(this.selectedApproval, currentStatus);
    },
    approvalStatus() {
      if (!this.selectedApproval || !this.selectedApproval.ExtractedData) return null;
      
      if (this.isComplianceApproval) {
        return this.selectedApproval.ExtractedData.compliance_approval || { approved: null, remarks: '' };
      } else {
        return this.selectedApproval.ExtractedData.policy_approval || { approved: null, remarks: '' };
      }
    },
    allSubpoliciesApproved() {
      if (!this.selectedApproval || 
          !this.selectedApproval.ExtractedData || 
          !this.selectedApproval.ExtractedData.subpolicies ||
          this.selectedApproval.ExtractedData.subpolicies.length === 0) {
        return false;
      }
      
      const subpolicies = this.selectedApproval.ExtractedData.subpolicies;
      return subpolicies.every(sub => sub.approval?.approved === true);
    },
    filteredSubpolicies() {
      if (!this.selectedPolicyForSubpolicies || 
          !this.selectedPolicyForSubpolicies.ExtractedData || 
          !this.selectedPolicyForSubpolicies.ExtractedData.subpolicies) {
        return [];
      }
      
      // If in reviewer mode, show all subpolicies
      if (this.isReviewer) {
        return this.selectedPolicyForSubpolicies.ExtractedData.subpolicies;
      }
      
      // In user mode, only show rejected subpolicies
      return this.selectedPolicyForSubpolicies.ExtractedData.subpolicies.filter(sub => 
        sub.Status === 'Rejected' || 
        (sub.approval && sub.approval.approved === false)
      );
    },
    
    // Computed property to filter frameworks - show only the selected framework from session
    filteredFrameworks() {
      if (this.sessionFrameworkId) {
        // If there's a session framework ID, show only that framework
        return this.frameworks.filter(fw => fw.id.toString() === this.sessionFrameworkId.toString())
      }
      // If no session framework ID, show all frameworks
      return this.frameworks
    }
  }
}
</script>

<style scoped>
@import './PolicyApprover.css';

/* Framework selection dropdown styles */
.framework-selection-dropdown {
  margin-bottom: 15px;
  padding: 12px;
  background: #f8faff;
  border-radius: 8px;
  border: 1px solid #e8edfa;
}

.framework-selection-dropdown label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.9rem;
}

.framework-selection-dropdown select {
  width: 100%;
  padding: 8px 12px;
  border: 1.5px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.9rem;
  background: white;
  color: #2c3e50;
  transition: border-color 0.2s ease;
}

.framework-selection-dropdown select:focus {
  outline: none;
  border-color: #4f6cff;
  box-shadow: 0 0 0 3px rgba(79, 108, 255, 0.1);
}

.framework-help-text {
  display: block;
  margin-top: 6px;
  font-size: 0.8rem;
  color: #64748b;
  font-style: italic;
}

/* Force white background for dashboard */
.dashboard-container {
  background-color: #ffffff !important;
  background: #ffffff !important;
}

/* Remove all blue colors from tabs */
.tab-button.active {
  color: var(--text-primary) !important;
  background: transparent !important;
}

.tab-button.active::after {
  background: transparent !important;
}

.tab-count {
  background: #9ca3af !important;
  box-shadow: 0 2px 4px rgba(156, 163, 175, 0.2) !important;
}

/* Completely remove tabs-container card appearance */
.tabs-container {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}

.tabs {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}

.tab-content {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* Remove all card styling from tab-related elements */
.tab-content * {
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
  border-radius: 0 !important;
}

/* EXCEPT for buttons - they should be visible */
.tab-content button,
.tab-content .view-details-btn,
.view-details-btn,
button.view-details-btn {
  background: #465add !important;
  box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2) !important;
  border-radius: 6px !important;
}

/* Ensure buttons are visible and styled */
.tab-content .view-details-btn,
.tab-content button,
.view-details-btn {
  background: #465add !important;
  color: white !important;
  border: none !important;
  border-radius: 6px !important;
  padding: 8px 16px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important;
  gap: 6px !important;
  transition: all 0.2s ease !important;
  text-transform: uppercase !important;
  letter-spacing: 0.3px !important;
  box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2) !important;
  white-space: nowrap !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.tab-content .approvals-list {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}

.tab-content .task-table {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 0 !important;
}

/* Completely revised modal layering with much higher z-indices */
.subpolicies-modal {
  z-index: 9000 !important;
}

.edit-subpolicy-modal {
  z-index: 10000 !important; /* Dramatically higher z-index */
  position: fixed;
  top: 0; 
  left: 0; 
  right: 0; 
  bottom: 0;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: auto !important; /* Force pointer events */
}

.edit-policy-content {
  background: white;
  border-radius: 12px;
  padding: 32px;
  width: 90%;
  max-width: 600px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2), 0 0 0 1000px rgba(0, 0, 0, 0.3);
  position: relative;
  max-height: 80vh;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  animation: fadeIn 0.3s ease-in-out;
  z-index: 150001 !important; /* Higher than modal container */
}

.reject-modal {
  z-index: 11000 !important; /* Highest z-index to appear on top */
}

/* Override any potential conflicting styles in the base CSS */
.policy-details-modal {
  position: fixed !important;
  z-index: 9999 !important;
}

.reject-modal {
  position: fixed !important;
  z-index: 11000 !important;
}

.edit-policy-modal {
  position: fixed !important;
  z-index: 150000 !important; /* Higher than all other modals */
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: auto;
}

.subpolicies-modal,
.edit-subpolicy-modal {
  position: fixed !important;
  z-index: 10000 !important;
}

/* Pending rejections indicator styling */
.pending-rejections-indicator {
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #92400e;
  font-weight: 500;
}

.pending-rejections-indicator i {
  color: #f59e0b;
  font-size: 16px;
}

/* Pending rejection button styling */
.reject-button.has-pending-rejection {
  background: #fef3c7;
  border-color: #f59e0b;
  color: #92400e;
  font-weight: 600;
}

.reject-button.has-pending-rejection:hover {
  background: #fde68a;
  border-color: #d97706;
}

/* Pending rejection styling for reject-btn class */
.reject-btn.has-pending-rejection {
  background: #fef3c7;
  border-color: #f59e0b;
  color: #92400e;
  font-weight: 600;
}

.reject-btn.has-pending-rejection:hover {
  background: #fde68a;
  border-color: #d97706;
}

/* The rest of your styling remains the same */
.edit-subpolicy-modal label {
  display: block;
  font-weight: 600;
  margin-bottom: 5px;
  color: #4b5563;
}

.edit-subpolicy-modal input,
.edit-subpolicy-modal textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.edit-subpolicy-modal input:focus,
.edit-subpolicy-modal textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.edit-subpolicy-modal button.resubmit-btn {
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.2s;
}

.edit-subpolicy-modal button.resubmit-btn:hover {
  background: #4f46e5;
  transform: translateY(-2px);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Improved styles for subpolicy-inline-edit */
.subpolicy-inline-edit {
  background: #f8fafc;
  border: 2px solid #6366f1;
  border-radius: 8px;
  padding: 24px;
  margin: 15px 0;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
  animation: fadeIn 0.3s ease-out;
  transition: all 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.subpolicy-inline-edit h4 {
  margin-top: 0;
  color: #6366f1;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 10px;
  margin-bottom: 20px;
  font-size: 18px;
  font-weight: 600;
}

.subpolicy-inline-edit label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #4b5563;
  font-size: 14px;
}

.subpolicy-inline-edit input,
.subpolicy-inline-edit textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  transition: all 0.2s ease;
}

.subpolicy-inline-edit input:focus,
.subpolicy-inline-edit textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.subpolicy-inline-edit input:disabled {
  background-color: #f3f4f6;
  color: #6b7280;
  cursor: not-allowed;
}

.subpolicy-inline-edit textarea {
  min-height: 100px;
  resize: vertical;
}

.subpolicy-edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.resubmit-btn {
  background: #6366f1;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2);
}

.resubmit-btn:hover {
  background: #4f46e5;
  transform: translateY(-2px);
}

.cancel-btn {
  background: #e5e7eb;
  color: #4b5563;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}

.cancel-btn:hover {
  background: #d1d5db;
  transform: translateY(-2px);
}

.subpolicy-status {
  background: white;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
}

.subpolicy-status:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.badge.rejected {
  background-color: #ef4444;
  color: white;
  padding: 4px 12px;
  font-weight: 600;
  font-size: 12px;
  border-radius: 20px;
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.2);
}

.rejection-reason {
  background-color: #fee2e2;
  border-left: 4px solid #ef4444;
  padding: 12px;
  margin: 12px 0;
  color: #991b1b;
  font-size: 14px;
  border-radius: 0 4px 4px 0;
}

.badge.resubmitted {
  background-color: #3b82f6;
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 600;
  position: relative;
  animation: pulse-badge 2s infinite;
}

@keyframes pulse-badge {
  0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }
  70% { transform: scale(1.05); box-shadow: 0 0 0 5px rgba(59, 130, 246, 0); }
  100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
}

/* Styles for resubmitted items */
.resubmitted-item {
  border-left: 4px solid #3b82f6 !important;
  background-color: rgba(59, 130, 246, 0.05);
  position: relative;
}

.resubmitted-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -4px;
  height: 100%;
  width: 4px;
  background-color: #3b82f6;
  animation: pulse-border 2s infinite;
}

@keyframes pulse-border {
  0% { opacity: 0.6; }
  50% { opacity: 1; }
  100% { opacity: 0.6; }
}

/* Subpolicy header with better layout */
.subpolicy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

/* Version tag styling */
.subpolicy-version {
  margin-bottom: 10px;
}

.version-tag {
  background-color: #3b82f6;
  color: white;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
  font-weight: 600;
  margin-right: 10px;
}

/* Edit history styling */
.edit-history {
  margin-top: 15px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.edit-history-header {
  background-color: #3b82f6;
  color: white;
  padding: 10px 15px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.edit-history-content {
  padding: 15px;
  background-color: #f9fafb;
}

.edit-field {
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px dashed #e5e7eb;
}

.edit-field:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.field-label {
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 5px;
  font-size: 13px;
}

.field-previous {
  padding: 10px;
  background-color: #fee2e2;
  border-radius: 4px;
  margin-bottom: 10px;
  position: relative;
  text-decoration: line-through;
  color: #991b1b;
  font-size: 14px;
}

.field-value {
  padding: 10px;
  background-color: #dcfce7;
  border-radius: 4px;
  color: #166534;
  font-size: 14px;
}

/* Subpolicy content section */
.subpolicy-content {
  margin-bottom: 15px;
}

.view-button {
  background-color: #3b82f6;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-left: 10px;
}

.view-button:hover {
  background-color: #2563eb;
}

/* Add styles for approved date display */
.policy-approved-date {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  padding: 8px 12px;
  background-color: #f0f9ff;
  border-radius: 6px;
  border-left: 4px solid #22c55e;
}

.date-label {
  font-weight: 600;
  color: #065f46;
}

.date-value {
  color: #059669;
  font-family: 'Courier New', monospace;
}

.approval-status.approved {
  background-color: #dcfce7;
  color: #166534;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: 600;
}

/* Styles for changes summary in edit modal */
.changes-summary {
  margin: 15px 0;
  border: 1px solid #3b82f6;
  border-radius: 8px;
  overflow: hidden;
  background-color: rgba(59, 130, 246, 0.05);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.changes-header {
  background-color: #3b82f6;
  color: white;
  padding: 10px 15px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.changes-content {
  padding: 12px 15px;
}

.change-item {
  padding: 8px 0;
  color: #4b5563;
  font-size: 14px;
  border-bottom: 1px dashed #e5e7eb;
}

.change-item:last-child {
  border-bottom: none;
}

.form-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.form-actions .resubmit-btn {
  background-color: #6366f1;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.form-actions .resubmit-btn:hover:not(:disabled) {
  background-color: #4f46e5;
  transform: translateY(-2px);
}

.form-actions .resubmit-btn:disabled {
  background-color: #c7d2fe;
  cursor: not-allowed;
  color: #6366f1;
}

.form-actions .cancel-btn {
  background-color: #e5e7eb;
  color: #4b5563;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.form-actions .cancel-btn:hover {
  background-color: #d1d5db;
  transform: translateY(-2px);
}

/* Improve edit modal styling */
.edit-modal {
  width: 90%;
  max-width: 700px;
  padding: 30px;
  border-radius: 12px;
}

.edit-modal h2 {
  color: #4f46e5;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 2px solid #c7d2fe;
  font-size: 22px;
}

.edit-modal .form-group {
  margin-bottom: 20px;
}

.edit-modal label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #4b5563;
  font-size: 14px;
}

.edit-modal input,
.edit-modal textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s ease;
}

.edit-modal input:focus,
.edit-modal textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.edit-modal textarea {
  min-height: 120px;
  resize: vertical;
}

.edit-modal input:disabled {
  background-color: #f3f4f6;
  color: #6b7280;
  cursor: not-allowed;
}

/* Badge for approved-only view */
.approved-only-badge {
  background-color: #10b981;
  color: white;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 20px;
  margin-left: 10px;
  font-weight: 500;
  display: inline-block;
  vertical-align: middle;
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
}

/* Policy status indicator styles */
.policy-status-indicator {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  background: #f8fafc;
  padding: 10px 15px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.status-label {
  font-weight: 600;
  margin-right: 10px;
  color: #4b5563;
}

.status-value {
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 20px;
  text-align: center;
}

.status-approved {
  background-color: #10b981;
  color: white;
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
}

.status-rejected {
  background-color: #ef4444;
  color: white;
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.2);
}

.status-pending {
  background-color: #f59e0b;
  color: white;
  box-shadow: 0 2px 4px rgba(245, 158, 11, 0.2);
}

/* Add these styles to your component */
.rejection-reason-section {
  margin: 15px 0;
  padding: 15px;
  background-color: #fff5f5;
  border-left: 4px solid #ef4444;
  border-radius: 0 4px 4px 0;
}

.rejection-reason-section h4 {
  color: #b91c1c;
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 16px;
  font-weight: 600;
}

.rejection-message {
  color: #991b1b;
  font-size: 14px;
  line-height: 1.5;
}

/* Add these styles */
.rejected-subpolicy-details {
  margin: 15px 0;
  padding: 15px;
  background-color: #fff5f5;
  border-radius: 8px;
  border: 1px solid #fecaca;
}

.status-badge.rejected {
  background-color: #ef4444;
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.rejection-reason {
  margin-top: 12px;
  padding: 10px 15px;
  background-color: #fee2e2;
  border-radius: 6px;
}

.reason-header {
  font-weight: 600;
  color: #b91c1c;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.reason-content {
  color: #991b1b;
  font-size: 14px;
  line-height: 1.5;
}

/* Add these styles */
.policy-rejection-reason {
  margin-top: 8px;
  padding: 8px 12px;
  background-color: #fee2e2;
  border-radius: 4px;
  color: #991b1b;
  font-size: 14px;
}

/* Add these styles */
.rejection-reason-container {
  margin: 15px 0 20px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.rejection-reason-header {
  background-color: #ef4444;
  color: white;
  padding: 12px 15px;
  font-weight: 600;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.rejection-reason-content {
  padding: 15px;
  background-color: #fee2e2;
  color: #991b1b;
  font-size: 14px;
  line-height: 1.6;
}

/* Overlay for modal */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(30, 41, 59, 0.45); /* dark semi-transparent */
  z-index: 99998; /* below modal, above everything else */
  display: flex;
  align-items: center;
  justify-content: center;
  /* Optional: backdrop blur */
  backdrop-filter: blur(2px);
}

/* Modal itself */
.subpolicies-modal {
  z-index: 99999 !important;
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none; /* Only modal content should be interactive */
}

.subpolicies-modal-content {
  z-index: 100000 !important;
  position: relative;
  background: #fff;
  border-radius: 12px;
  padding: 32px;
  min-width: 400px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 32px rgba(0,0,0,0.18);
  pointer-events: auto; /* Make modal content interactive */
}

/* Creator message styles */
.creator-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: #e3f2fd;
  border: 1px solid #2196f3;
  border-radius: 6px;
  color: #1976d2;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.creator-message i {
  color: #2196f3;
  font-size: 1rem;
}

.creator-message span {
  font-weight: 500;
}

.creator-message-small {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background-color: #e3f2fd;
  border: 1px solid #2196f3;
  border-radius: 4px;
  color: #1976d2;
  font-size: 0.8rem;
  margin-left: 0.5rem;
}

.creator-message-small i {
  color: #2196f3;
  font-size: 0.8rem;
}

/* Admin message styles */
.admin-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background-color: #fff3e0;
  border: 1px solid #ff9800;
  border-radius: 6px;
  color: #e65100;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.admin-message i {
  color: #ff9800;
  font-size: 1rem;
}

.admin-message span {
  font-weight: 500;
}
</style> 