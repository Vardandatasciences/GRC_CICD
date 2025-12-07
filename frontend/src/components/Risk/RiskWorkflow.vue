<template>
  <div class="risk-workflow-container">
    <!-- Show tasks view when not viewing any workflows -->
    <div v-if="!showMitigationWorkflow && !showReviewerWorkflow">
      <!-- Toggle buttons for Risk Resolution and Risk Workflow -->
      <div class="risk-workflow-toggle-buttons">
        <button 
          class="risk-workflow-toggle-button" 
          @click="navigateTo('resolution')"
        >
          Risk Resolution
        </button>
        <button 
          class="risk-workflow-toggle-button active" 
          @click="navigateTo('workflow')"
        >
          Risk Workflow
        </button>
      </div>
      <p
        v-if="dataSourceMessage"
        class="risk-workflow-data-source"
      >
        {{ dataSourceMessage }}
      </p>
      
      <!-- Search and Filter Bar -->
      <div class="risk-workflow-filters-wrapper">
        <Dynamicalsearch 
          v-model="searchQuery" 
          placeholder="Search risks..."
          @input="filterRisks"
        />
      </div>
      
      <!-- Dropdowns Below Search -->
      <div class="risk-workflow-dropdowns-wrapper">
        <CustomDropdown 
          :config="criticalityDropdownConfig"
          v-model="criticalityFilter"
          @change="filterRisks"
        />
        <CustomDropdown 
          :config="statusDropdownConfig"
          v-model="statusFilter"
          @change="filterRisks"
        />
        <CustomDropdown 
          :config="assignedToDropdownConfig"
          v-model="assignedToFilter"
          @change="filterRisks"
        />
        <CustomDropdown 
          :config="reviewerDropdownConfig"
          v-model="reviewerFilter"
          @change="filterRisks"
        />
      </div>

      <div class="risk-workflow-user-filter">
  <!-- Show loading state while fetching user info -->
  <div v-if="isLoadingUser" class="risk-workflow-loading-indicator">
    Loading user information...
  </div>
  
  <!-- Show dropdown only for GRC Administrator -->
  <div v-else-if="isGRCAdministrator">
    <div v-if="loading && users.length === 0" class="risk-workflow-loading-indicator">
      Loading users...
    </div>
    <CustomDropdown
      v-else
      v-model="selectedUserId"
      :config="userDropdownConfig"
      @change="fetchData"
    />
  </div>
  
  <!-- Show logged-in user info for non-GRC administrators -->
  <div v-else class="risk-workflow-logged-user-info">
    <div class="user-info-display">
      <i class="fas fa-user"></i>
      <span>{{ loggedInUser ? loggedInUser.UserName : 'Unknown User' }}</span>
      <span v-if="loggedInUser && loggedInUser.department" class="user-department">
        ({{ loggedInUser.department }})
      </span>
    </div>
  </div>
</div>
      
      <!-- Tabs for User Tasks and Reviewer Tasks -->
      <div class="risk-workflow-tabs">
        <div 
          class="risk-workflow-tab" 
          :class="{ 'active': activeTab === 'user' }" 
          @click="activeTab = 'user'"
        >
          My Tasks
        </div>
        <div 
          class="risk-workflow-tab" 
          :class="{ 'active': activeTab === 'reviewer' }" 
          @click="activeTab = 'reviewer'"
        >
          Reviewer Tasks
        </div>
      </div>
      
      <div v-if="loading" class="risk-workflow-loading">
        Loading data...
      </div>
      
      <div v-else-if="error" class="risk-workflow-error-message">
        {{ error }}
      </div>
      
      <!-- User Tasks Section -->
      <div v-if="activeTab === 'user'">
        <!-- Debug Information (can be removed in production) -->
        <div style="background: #f0f0f0; padding: 1rem; margin: 1rem; border-radius: 4px; font-size: 12px;" v-if="false">
          <strong>Debug Info:</strong><br>
          Selected User ID: {{ selectedUserId }}<br>
          User Risks Length: {{ userRisks.length }}<br>
          Loading: {{ loading }}<br>
          Error: {{ error }}<br>
          Approved Risks: {{ approvedRisks.length }}<br>
          Rejected Risks: {{ rejectedRisks.length }}<br>
          Pending Review Risks: {{ pendingReviewRisks.length }}<br>
          Assigned Risks: {{ assignedRisks.length }}<br>
          User Task Sections Length: {{ userTaskSections.length }}
        </div>
        
        <div v-if="!selectedUserId" class="risk-workflow-no-data">
          <p>Please select a user to view their assigned risks.</p>
        </div>
        <div v-else-if="loading" class="risk-workflow-loading">
          <p>Loading user risks...</p>
        </div>
        <div v-else-if="error" class="risk-workflow-error-message">
          <p>{{ error }}</p>
        </div>
        <div v-else-if="userRisks.length === 0" class="risk-workflow-no-data">
          <p>No risks assigned to this user.</p>
        </div>
        <div v-else class="risk-workflow-collapsible-container">
          <div v-if="userTaskSections && userTaskSections.length > 0">
            <CollapsibleTable
              v-for="section in userTaskSections"
              :key="section.name"
              :section-config="section"
              :table-headers="userTaskTableHeaders"
              :is-expanded="expandedSections[section.statusKey]"
              @toggle="toggleSection(section.statusKey)"
              @taskClick="handleUserTaskClick"
            />
          </div>
          <div v-else class="risk-workflow-no-data">
            <p>No task sections available.</p>
          </div>
        </div>
      </div>
      
      <!-- Reviewer Tasks Section -->
      <div v-if="activeTab === 'reviewer'">
        <!-- Debug Information (can be removed in production) -->
        <div style="background: #f0f0f0; padding: 1rem; margin: 1rem; border-radius: 4px; font-size: 12px;" v-if="false">
          <strong>Reviewer Debug Info:</strong><br>
          Selected User ID: {{ selectedUserId }}<br>
          Reviewer Tasks Length: {{ reviewerTasks.length }}<br>
          Approved Reviewer Tasks: {{ approvedReviewerTasks.length }}<br>
          Pending Reviewer Tasks: {{ pendingReviewerTasks.length }}<br>
          Reviewer Task Sections Length: {{ reviewerTaskSections.length }}
        </div>
        
        <div v-if="!selectedUserId" class="risk-workflow-no-data">
          <p>Please select a user to view their reviewer tasks.</p>
        </div>
        <div v-else-if="loading" class="risk-workflow-loading">
          <p>Loading reviewer tasks...</p>
        </div>
        <div v-else-if="error" class="risk-workflow-error-message">
          <p>{{ error }}</p>
        </div>
        <div v-else-if="reviewerTasks.length === 0" class="risk-workflow-no-data">
          <p>No review tasks assigned to this user.</p>
        </div>
        <div v-else class="risk-workflow-collapsible-container">
          <div v-if="reviewerTaskSections && reviewerTaskSections.length > 0">
            <CollapsibleTable
              v-for="section in reviewerTaskSections"
              :key="section.name"
              :section-config="section"
              :table-headers="reviewerTaskTableHeaders"
              :is-expanded="expandedSections[section.statusKey]"
              @toggle="toggleSection(section.statusKey)"
              @taskClick="handleReviewerTaskClick"
            />
          </div>
          <div v-else class="risk-workflow-no-data">
            <p>No reviewer task sections available.</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Risk Mitigation Workflow view (Full screen instead of modal) -->
    <div v-if="showMitigationWorkflow" class="risk-workflow-fullscreen">
      <div class="risk-workflow-header-section">
        <button @click="closeMitigationModal" class="risk-workflow-back-btn" title="Back to tasks">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h1>Mitigation Steps</h1>
      </div>
      
      <div v-if="loadingMitigations" class="risk-workflow-loading">
        <div class="risk-workflow-spinner"></div>
        <span>Loading mitigation steps...</span>
      </div>
      <div v-else-if="!mitigationSteps.length" class="risk-workflow-no-data">
        No mitigation steps found for this risk.
      </div>
      <div v-else class="risk-workflow-simplified-workflow">
        <!-- Professional Step Navigation Header -->
        <div class="risk-workflow-steps-header">
          <div class="steps-count-indicator">
            <span class="steps-count">{{ mitigationSteps.length }}</span>
            <span class="steps-label">Mitigation Steps</span>
          </div>
          <div class="steps-numbers">
          <div 
            v-for="(step, index) in mitigationSteps" 
            :key="index" 
              class="step-number-item"
            :class="{
              'completed': step.status === 'Completed',
              'active': isStepActive(index),
              'locked': isStepLocked(index),
              'approved': step.approved === true,
              'rejected': step.approved === false,
              'selected': activeStepIndex === index && !showQuestionnaireSection
            }"
            @click="selectStep(index)"
          >
              <div class="step-number-circle">
              <span v-if="step.status === 'Completed'"><i class="fas fa-check"></i></span>
                <span v-else>{{ index + 1 }}</span>
              </div>
              <div class="step-number-label">{{ step.description }}</div>
            </div>
          </div>
          
          <!-- Questionnaire Card -->
          <div 
            class="step-number-item questionnaire-card"
            :class="{
              'selected': showQuestionnaireSection
            }"
            @click="selectQuestionnaire"
          >
            <div class="step-number-circle">
              <i class="fas fa-clipboard-list"></i>
            </div>
            <div class="step-number-label">Questionnaire</div>
          </div>
            </div>
            
        <!-- Step Details Content -->
        <div class="risk-workflow-steps-details">
          <div 
            v-for="(step, index) in mitigationSteps" 
            :key="index" 
            class="risk-workflow-step-detail"
            :class="{
              'completed': step.status === 'Completed',
              'active': isStepActive(index),
              'locked': isStepLocked(index),
              'approved': step.approved === true,
              'rejected': step.approved === false,
              'visible': activeStepIndex === index && !showQuestionnaireSection
            }"
            v-show="activeStepIndex === index && !showQuestionnaireSection"
          >
            <!-- Step Header -->
            <div class="step-detail-header">
              <div class="step-detail-number">
                <span class="step-number">{{ index + 1 }}</span>
              </div>
              <div class="step-detail-title">
              <h3>{{ step.description }}</h3>
              </div>
              </div>
              
            <!-- Step Content -->
            <div class="step-detail-content">
              <!-- Status indicators -->
              <div class="step-status-indicator">
              <div v-if="step.approved === true" class="status-tag approved">
                <i class="fas fa-check-circle"></i> Approved
              </div>
              <div v-else-if="step.approved === false" class="status-tag rejected">
                <i class="fas fa-times-circle"></i> Rejected
                <div v-if="step.remarks" class="remarks">
                  <strong>Feedback:</strong> {{ step.remarks }}
                </div>
              </div>
              <div v-else-if="step.status === 'Completed'" class="status-tag completed">
                <i class="fas fa-check"></i> Completed
              </div>
              <div v-else-if="isStepActive(index)" class="status-tag active">
                <i class="fas fa-circle-notch fa-spin"></i> In Progress
              </div>
              <div v-else class="status-tag locked">
                <i class="fas fa-lock"></i> Locked
                </div>
              </div>

              <!-- Submission dates -->
              <div class="step-dates" v-if="step.user_submitted_date || step.reviewer_submitted_date">
                <div v-if="step.user_submitted_date" class="submission-date user-date">
                  <i class="fas fa-clock"></i> Submitted: {{ formatDateTime(step.user_submitted_date) }}
                </div>
                <div v-if="step.reviewer_submitted_date" class="submission-date reviewer-date">
                  <i class="fas fa-clock"></i> Reviewed: {{ formatDateTime(step.reviewer_submitted_date) }}
                </div>
              </div>
              
              <!-- Display existing comments if available -->
              <div v-if="step.comments" class="step-comments-display">
                <h4><i class="fas fa-comment-alt"></i> Your Comments</h4>
                <p>{{ step.comments }}</p>
              </div>
              
              <!-- Display uploaded files if available -->
              <div v-if="step.files && step.files.length > 0" class="files-display">
                <h4><i class="fas fa-file-alt"></i> Uploaded Evidence</h4>
                <div class="files-list">
                  <div v-for="(file, fileIndex) in step.files" :key="fileIndex" class="file-item">
                    <!-- Linked Evidence -->
                    <div v-if="file.type === 'linked_evidence'" class="linked-evidence-item">
                      <i class="fas fa-link"></i>
                      <div class="linked-evidence-details">
                        <div class="evidence-title">{{ file.fileName }}</div>
                        <div class="evidence-source">Source: {{ file.linkedEvent?.source || 'Unknown' }}</div>
                        <div class="evidence-meta">
                          <span v-if="file.linkedEvent?.framework">{{ file.linkedEvent.framework }}</span>
                          <span v-if="file.linkedEvent?.status" class="evidence-status">Status: {{ file.linkedEvent.status }}</span>
                        </div>
                        <div v-if="file.linkedEvent?.description" class="evidence-description">
                          {{ file.linkedEvent.description.length > 100 ? file.linkedEvent.description.substring(0, 100) + '...' : file.linkedEvent.description }}
                        </div>
                        <!-- Documents Section -->
                        <div v-if="file.linkedEvent?.documents && file.linkedEvent.documents.length > 0" class="linked-documents">
                          <h4>Attached Documents:</h4>
                          <div class="document-list">
                            <div v-for="(document, docIndex) in file.linkedEvent.documents" :key="docIndex" class="document-item">
                              <div class="document-info">
                                <i class="fas fa-file-alt document-icon"></i>
                                <div class="document-details">
                                  <span class="document-name">{{ document.filename }}</span>
                                  <span class="document-source">{{ document.source }}</span>
                                  <span v-if="document.file_size" class="document-size">({{ formatFileSize(document.file_size) }})</span>
                                </div>
                              </div>
                              <div class="document-actions">
                                <button v-if="document.downloadable" @click.stop="downloadLinkedDocument(file.linkedEvent.id, docIndex, document)" class="download-btn" title="Download Document">
                                  <i class="fas fa-download"></i>
                                </button>
                                <span v-else class="not-downloadable" title="Document not available for download">
                                  <i class="fas fa-ban"></i>
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        <div class="evidence-actions">
                          <!-- Only show View Details when documents are NOT loaded -->
                          <button v-if="!file.linkedEvent?.documents || file.linkedEvent.documents.length === 0" @click="showLinkedEventDetails(file.linkedEvent)" class="view-details-btn">
                            <i class="fas fa-info-circle"></i> View Details
                          </button>
                          <!-- Only show Refresh Docs when documents are loaded -->
                          
                        </div>
                      </div>
                      <span class="linked-evidence-badge">Linked Event</span>
                    </div>
                    
                    <!-- Regular File -->
                    <a v-else :href="file['aws-file_link']" :download="file.fileName" target="_blank" class="downloadable-file">
                      <i class="fas fa-download"></i> {{ file.fileName }}
                      <span v-if="file.size" class="file-size">({{ formatFileSize(file.size) }})</span>
                      <span v-if="file.upload_type === 's3'" class="s3-indicator" title="Stored in S3">
                        <i class="fas fa-cloud"></i>
                      </span>
                    </a>
                  </div>
                </div>
              </div>
              
              <!-- Legacy file display for backward compatibility -->
              <div v-else-if="step.fileData" class="file-display">
                <h4><i class="fas fa-file-alt"></i> Uploaded Evidence</h4>
                <a :href="step.s3Url || step.fileData" download :filename="step.fileName || 'evidence'">
                  <i class="fas fa-download"></i> {{ step.fileName || 'Download file' }}
                </a>
                <div v-if="step.s3FileInfo" class="file-info-details">
                  <span class="file-upload-date">Uploaded: {{ formatDateTime(step.s3FileInfo.uploadedAt) }}</span>
                </div>
              </div>
              
                <!-- Add status control with complete button and comments -->
  <div v-if="!step.approved && !isStepLocked(index)" class="risk-workflow-status-control">
    <!-- Add comments text box -->
    <div class="step-comments">
      <label for="step-comments-input"><i class="fas fa-comment"></i> Comments:</label>
      <textarea 
        :id="'step-comments-input-' + index" 
        v-model="step.comments" 
        placeholder="Enter your comments for this mitigation step..."
        class="step-comments-input"
      ></textarea>
    </div>
    
    <!-- Evidence Attachment -->
    <div class="evidence-upload-container">
      <label></label>
      <EvidenceAttachment 
        :risk-instance-id="selectedRiskId"
        :user-id="selectedUserId"
        :step-index="index"
        @filesUploaded="(files) => handleFilesUploaded(files, index)"
      />
    </div>
    
    <button 
      @click="completeStep(index)" 
      class="risk-workflow-complete-btn"
      :class="{ 'active': step.status === 'Completed' }"
      v-if="step.status !== 'Completed'"
    >
      <i class="fas fa-check"></i> Mark as Complete
    </button>
    <button 
      @click="resetStep(index)" 
      class="risk-workflow-reset-btn"
      v-else
    >
      <i class="fas fa-undo"></i> Reset
    </button>
  </div>
            </div>
          </div>
        </div>
        
        <!-- Update the mitigation-questionnaire div in the mitigation modal -->
        <div 
          class="mitigation-questionnaire"
          :class="{ 'visible': showQuestionnaireSection }"
          v-show="showQuestionnaireSection"
        >
          <h3>Risk Mitigation Questionnaire</h3>
          
          <!-- Add questionnaire status indicator -->
          <div v-if="questionnaireReviewed" class="questionnaire-status" :class="{ 'approved': questionnaireApproved, 'rejected': !questionnaireApproved }">
            <i class="fas" :class="questionnaireApproved ? 'fa-check-circle' : 'fa-times-circle'"></i>
            {{ questionnaireApproved ? 'Approved' : 'Revision Required' }}
            
            <!-- Add submission dates when available -->
            <div v-if="formDetails.user_submitted_date" class="submission-date user-date">
              <i class="fas fa-clock"></i> Submitted: {{ formatDateTime(formDetails.user_submitted_date) }}
            </div>
            <div v-if="formDetails.reviewer_submitted_date" class="submission-date reviewer-date">
              <i class="fas fa-clock"></i> Reviewed: {{ formatDateTime(formDetails.reviewer_submitted_date) }}
            </div>
          </div>
          
          <p class="questionnaire-note">Please complete all fields to proceed with submission</p>
          
          <div class="question-group">
            <label for="cost-input"><span class="question-number">1</span> What is the cost for this mitigation?</label>
            <div class="cost-input-group">
              <input id="cost-input" type="number" v-model="formDetails.cost" :disabled="questionnaireApproved" min="0" placeholder="Enter the cost..." />
              <select v-model="formDetails.costCurrency" :disabled="questionnaireApproved" class="currency-select">
                <option value="USD">USD</option>
                <option value="INR">INR</option>
                <option value="AED">AED</option>
                <option value="MUR">MUR</option>
              </select>
            </div>
          </div>
          <div class="question-group">
            <label for="impact-input"><span class="question-number">2</span> What is the impact for this mitigation?</label>
            <input id="impact-input" type="number" v-model="formDetails.impact" :disabled="questionnaireApproved" min="0" placeholder="Enter the impact..." />
          </div>
          <div class="question-group">
            <label for="financial-impact-input"><span class="question-number">3</span> What is the financial impact for this mitigation?</label>
            <input id="financial-impact-input" type="number" v-model="formDetails.financialImpact" :disabled="questionnaireApproved" min="0" placeholder="Enter the financial impact..." />
          </div>
          <div class="question-group">
            <label for="reputational-impact-input"><span class="question-number">4</span> What is the reputational impact for this mitigation?</label>
            <textarea id="reputational-impact-input" v-model="formDetails.reputationalImpact" :disabled="questionnaireApproved" placeholder="Describe the reputational impact..."></textarea>
          </div>
          <div class="question-group">
            <label for="operational-impact-input"><span class="question-number">5</span> What is the Operational Impact for this mitigation?</label>
            <input id="operational-impact-input" type="number" v-model="formDetails.operationalImpact" :disabled="questionnaireApproved" min="0" placeholder="Enter the operational impact..." />
          </div>
          <div class="question-group">
            <label for="financial-loss-input"><span class="question-number">6</span> What is the Financial Loss for this mitigation?</label>
            <div class="cost-input-group">
              <input id="financial-loss-input" type="number" v-model="formDetails.financialLoss" :disabled="questionnaireApproved" min="0" placeholder="Enter the financial loss..." />
              <select v-model="formDetails.financialLossCurrency" :disabled="questionnaireApproved" class="currency-select">
                <option value="USD">USD</option>
                <option value="INR">INR</option>
                <option value="AED">AED</option>
                <option value="MUR">MUR</option>
              </select>
            </div>
          </div>
          <div class="question-group">
            <label for="system-downtime-input"><span class="question-number">7</span> What is the expected system downtime (hrs) if this risk occurs?</label>
            <input id="system-downtime-input" type="number" v-model="formDetails.systemDowntime" :disabled="questionnaireApproved" min="0" placeholder="Enter expected downtime in hours..." />
          </div>
          <div class="question-group">
            <label for="recovery-time-input"><span class="question-number">8</span> How long did it take to recover last time (hrs)?</label>
            <input id="recovery-time-input" type="number" v-model="formDetails.recoveryTime" :disabled="questionnaireApproved" min="0" placeholder="Enter recovery time in hours..." />
          </div>
          <div class="question-group">
            <label for="recurrence-possible-input"><span class="question-number">9</span> Is it possible that this risk will recur again?</label>
            <select id="recurrence-possible-input" v-model="formDetails.recurrencePossible" :disabled="questionnaireApproved">
              <option value="">Select</option>
              <option value="Yes">Yes</option>
              <option value="No">No</option>
              <option value="Unknown">Unknown</option>
            </select>
          </div>
          <div class="question-group">
            <label for="improvement-initiative-input"><span class="question-number">10</span> Is this an Improvement Initiative which will prevent the future recurrence of said risk?</label>
            <select id="improvement-initiative-input" v-model="formDetails.improvementInitiative" :disabled="questionnaireApproved">
              <option value="">Select</option>
              <option value="Yes">Yes</option>
              <option value="No">No</option>
              <option value="Unknown">Unknown</option>
            </select>
          </div>
          
          <!-- Add to the mitigation-questionnaire div, after the questionnaire fields -->
          <div v-if="questionnaireRejected" class="questionnaire-feedback">
            <h4><i class="fas fa-exclamation-circle"></i> Reviewer Feedback</h4>
            <p>{{ questionnaireRemarks }}</p>
          </div>
        </div>
        
        <!-- Update the submission-area div to check for questionnaire completion -->
        <div class="submission-area" :class="{ 'ready': canSubmit }">
          <h3>Submit Mitigation</h3>
          
          <div v-if="selectedReviewer" class="reviewer-info">
            <p><strong>Assigned Reviewer:</strong> {{ getUserName(selectedReviewer) }}</p>
          </div>
          
          <button 
            @click="submitForReview" 
            class="submit-btn" 
          >
            <i class="fas fa-paper-plane"></i> Submit for Review
          </button>
          
          <!-- Hidden warning messages -->
          <div v-if="false" class="submit-message">
            <i class="fas fa-info-circle"></i>
            Complete all mitigation steps before submitting
          </div>
          
          <div v-if="false" class="submit-message">
            <i class="fas fa-info-circle"></i>
            Complete the questionnaire before submitting
          </div>
        </div>
      </div>
    </div>
    
    <!-- Reviewer Workflow view (Full screen instead of modal) -->
    <div v-if="showReviewerWorkflow" class="reviewer-workflow-fullscreen">
      <div class="back-to-tasks">
        <button @click="closeReviewerModal" class="back-btn" title="Back to tasks">
          <i class="fas fa-arrow-left"></i>
        </button>
      </div>
      
      <h1>Review Risk Mitigations</h1>
      
      <div v-if="loadingMitigations" class="loading">
        <div class="spinner"></div>
        <span>Loading mitigation data...</span>
      </div>
      <div v-else>
        <div class="risk-summary">
          <h3>{{ currentReviewTask?.RiskDescription || 'Risk #' + currentReviewTask?.RiskInstanceId }}</h3>
          <p><strong>ID:</strong> {{ currentReviewTask?.RiskInstanceId }}</p>
          <p><strong>Submitted By:</strong> {{ getUserName(currentReviewTask?.UserId) }}</p>
        </div>
        
        <div v-if="reviewCompleted" class="review-status-banner" :class="{ 'approved': reviewApproved, 'rejected': !reviewApproved }">
          <div v-if="reviewApproved" class="status-message">
            <i class="fas fa-check-circle"></i> This risk has been approved
          </div>
          <div v-else class="status-message">
            <i class="fas fa-times-circle"></i> Feedback sent to user for revision
          </div>
        </div>
        
        <!-- Mitigation review list with split view design -->
        <div class="mitigation-review-list">
          <!-- Add version dropdown above mitigation items -->
          <div class="global-version-dropdown" :class="{ 'loading': loadingVersions }">
            <label for="global-version-select">Select Version to Compare:</label>
            <select 
              id="global-version-select" 
              v-model="globalSelectedVersion" 
              @change="onGlobalVersionChange"
              class="global-version-select"
              :disabled="loadingVersions || allVersionNames.length === 0"
            >
              <option value="">Select a version</option>
              <option 
                v-for="version in allVersionNames" 
                :key="version" 
                :value="version"
              >
                {{ version }}
              </option>
            </select>
            <div v-if="allVersionNames.length === 0 && !loadingVersions" class="no-versions-message">
              <i class="fas fa-info-circle"></i> No previous versions available
            </div>
          </div>

          <div 
            v-for="(mitigation, id) in mitigationReviewData" 
            :key="id" 
            class="mitigation-review-item"
            :data-id="id"
          >
            <!-- Mitigation header with status badge -->
            <div class="mitigation-heading">
              <h4>Mitigation #{{ id }}</h4>
              
              <!-- Status badge -->
              <div v-if="mitigation.approved !== undefined" 
                  class="mitigation-status-badge" 
                  :class="{ 
                    'approved': mitigation.approved === true, 
                    'rejected': mitigation.approved === false,
                    'pending': mitigation.approved === undefined
                  }">
                <i class="fas" :class="{
                  'fa-check-circle': mitigation.approved === true,
                  'fa-times-circle': mitigation.approved === false,
                  'fa-clock': mitigation.approved === undefined
                }"></i>
                {{ mitigation.approved === true ? 'Approved' : 
                   mitigation.approved === false ? 'Rejected' : 'Pending Review' }}
              </div>
            </div>
            
            <!-- Split view container -->
            <div class="mitigation-split-content">
              <!-- Previous version (left side) -->
              <div class="mitigation-previous">
                <div class="version-label">
                  Previous Versions
                  <!-- Debug info -->
                  <div style="font-size: 10px; color: #999; margin-top: 2px;">
                    Total Versions: {{ allVersions.length }}, Selected: {{ selectedVersions[id] || 'None' }}
                  </div>
                </div>
                
                <!-- Show selected version data from dropdown -->
                <div v-if="selectedVersions[id] && getSelectedVersionData(id, selectedVersions[id])" class="mitigation-content">
                  <h5>Description</h5>
                  <p>{{ getSelectedVersionData(id, selectedVersions[id]).description || 'No description available' }}</p>
                  
                  <!-- Version metadata section -->
                  <div class="metadata-section">
                    <h5>Metadata</h5>
                    <div class="metadata-item">
                      <div class="metadata-label">Version:</div>
                      <div class="metadata-value">{{ selectedVersions[id] }}</div>
                    </div>
                    <div class="metadata-item">
                      <div class="metadata-label">Status:</div>
                      <div class="metadata-value">{{ getSelectedVersionData(id, selectedVersions[id]).status || 'Not specified' }}</div>
                    </div>
                    <div v-if="getSelectedVersionData(id, selectedVersions[id]).user_submitted_date" class="metadata-item">
                      <div class="metadata-label">Submitted:</div>
                      <div class="metadata-value">{{ formatDateTime(getSelectedVersionData(id, selectedVersions[id]).user_submitted_date) }}</div>
                    </div>
                    <div v-if="getSelectedVersionData(id, selectedVersions[id]).approved !== undefined" class="metadata-item">
                      <div class="metadata-label">Review Status:</div>
                      <div class="metadata-value">
                        <span :class="{ 'text-success': getSelectedVersionData(id, selectedVersions[id]).approved, 'text-danger': getSelectedVersionData(id, selectedVersions[id]).approved === false }">
                          {{ getSelectedVersionData(id, selectedVersions[id]).approved === true ? 'Approved' : 
                             getSelectedVersionData(id, selectedVersions[id]).approved === false ? 'Rejected' : 'Pending' }}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Version comments -->
                  <div v-if="getSelectedVersionData(id, selectedVersions[id]).comments" class="comments-section">
                    <h5><i class="fas fa-comment-alt"></i> User Comments</h5>
                    <p class="comments-text">{{ getSelectedVersionData(id, selectedVersions[id]).comments }}</p>
                  </div>
                  
                  <!-- Version evidence -->
                  <div v-if="getSelectedVersionData(id, selectedVersions[id]).fileData" class="evidence-section">
                    <h5><i class="fas fa-file-alt"></i> Evidence</h5>
                    <a :href="getSelectedVersionData(id, selectedVersions[id]).fileData" download :filename="getSelectedVersionData(id, selectedVersions[id]).fileName" class="evidence-link">
                      <i class="fas fa-download"></i> {{ getSelectedVersionData(id, selectedVersions[id]).fileName }}
                    </a>
                  </div>
                  
                  <!-- Version decision -->
                  <div v-if="getSelectedVersionData(id, selectedVersions[id]).approved !== undefined" class="decision-tag" 
                       :class="{ 
                         'approved': getSelectedVersionData(id, selectedVersions[id]).approved === true, 
                         'rejected': getSelectedVersionData(id, selectedVersions[id]).approved === false 
                       }">
                    <i class="fas" :class="{
                      'fa-check-circle': getSelectedVersionData(id, selectedVersions[id]).approved === true,
                      'fa-times-circle': getSelectedVersionData(id, selectedVersions[id]).approved === false
                    }"></i>
                    {{ getSelectedVersionData(id, selectedVersions[id]).approved ? 'Approved' : 'Rejected' }}
                  </div>
                  
                  <!-- Show reviewer remarks if rejected -->
                  <div v-if="getSelectedVersionData(id, selectedVersions[id]).approved === false && getSelectedVersionData(id, selectedVersions[id]).remarks" class="remarks-section">
                    <h5><i class="fas fa-exclamation-triangle"></i> Reviewer Feedback</h5>
                    <p class="remarks-text">{{ getSelectedVersionData(id, selectedVersions[id]).remarks }}</p>
                  </div>
                  
                  <!-- Add reviewer feedback section - always show if available -->
                  <div v-if="getSelectedVersionData(id, selectedVersions[id]).reviewer_feedback" class="reviewer-feedback-section">
                    <h5><i class="fas fa-comment-dots"></i> Reviewer Feedback</h5>
                    <p class="reviewer-feedback-text">{{ getSelectedVersionData(id, selectedVersions[id]).reviewer_feedback }}</p>
                  </div>
                </div>
                
                <!-- Empty state for no version selected -->
                <div v-else class="mitigation-empty">
                  <i class="fas fa-history"></i>
                  <p>Select a version from the dropdown above to compare</p>
                </div>
              </div>
              
              <!-- Current version (right side) - This should show the LATEST version -->
              <div class="mitigation-current">
                <div class="version-label">
                  Latest Version
                  <div style="font-size: 10px; color: #666; margin-top: 2px;">
                    {{ getCurrentVersionLabel() }}
                  </div>
                </div>
                
                <div class="mitigation-content">
                  <h5>Description</h5>
                  <p>{{ mitigation.description || 'No description available' }}</p>
                  
                  <!-- Current metadata -->
                  <div class="metadata-section">
                    <h5>Metadata</h5>
                    <div class="metadata-item">
                      <div class="metadata-label">Version:</div>
                      <div class="metadata-value">{{ currentReviewTask?.version || 'Current' }}</div>
                    </div>
                    <div class="metadata-item">
                      <div class="metadata-label">Status:</div>
                      <div class="metadata-value">{{ mitigation.status || 'Not specified' }}</div>
                    </div>
                    <div v-if="mitigation.user_submitted_date" class="metadata-item">
                      <div class="metadata-label">Submitted:</div>
                      <div class="metadata-value">{{ formatDateTime(mitigation.user_submitted_date) }}</div>
                    </div>
                    <div v-if="mitigation.reviewer_submitted_date" class="metadata-item">
                      <div class="metadata-label">Reviewed:</div>
                      <div class="metadata-value">{{ formatDateTime(mitigation.reviewer_submitted_date) }}</div>
                    </div>
                    <div v-if="mitigation.approved !== undefined" class="metadata-item">
                      <div class="metadata-label">Review Status:</div>
                      <div class="metadata-value">
                        <span :class="{ 'text-success': mitigation.approved, 'text-danger': mitigation.approved === false }">
                          {{ mitigation.approved === true ? 'Approved' : 
                             mitigation.approved === false ? 'Rejected' : 'Pending' }}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Current comments -->
                  <div v-if="mitigation.comments" class="comments-section">
                    <h5><i class="fas fa-comment-alt"></i> User Comments</h5>
                    <p class="comments-text">{{ mitigation.comments }}</p>
                  </div>
                  
                  <!-- Current evidence -->
                  <div v-if="mitigation.files && mitigation.files.length > 0" class="evidence-section">
                    <h5><i class="fas fa-file-alt"></i> Evidence</h5>
                    <div class="files-list">
                      <div v-for="(file, fileIndex) in mitigation.files" :key="fileIndex" class="file-item">
                        <!-- Linked Evidence -->
                        <div v-if="file.type === 'linked_evidence'" class="linked-evidence-item">
                          <i class="fas fa-link"></i>
                          <div class="linked-evidence-details">
                            <div class="evidence-title">{{ file.fileName }}</div>
                            <div class="evidence-source">Source: {{ file.linkedEvent?.source || 'Unknown' }}</div>
                            <div class="evidence-meta">
                              <span v-if="file.linkedEvent?.framework">{{ file.linkedEvent.framework }}</span>
                              <span v-if="file.linkedEvent?.status" class="evidence-status">Status: {{ file.linkedEvent.status }}</span>
                            </div>
                            <div v-if="file.linkedEvent?.description" class="evidence-description">
                              {{ file.linkedEvent.description.length > 100 ? file.linkedEvent.description.substring(0, 100) + '...' : file.linkedEvent.description }}
                            </div>
                            <!-- Documents Section -->
                            <div v-if="file.linkedEvent?.documents && file.linkedEvent.documents.length > 0" class="linked-documents">
                              <h4>Attached Documents:</h4>
                              <div class="document-list">
                                <div v-for="(document, docIndex) in file.linkedEvent.documents" :key="docIndex" class="document-item">
                                  <div class="document-info">
                                    <i class="fas fa-file-alt document-icon"></i>
                                    <div class="document-details">
                                      <span class="document-name">{{ document.filename }}</span>
                                      <span class="document-source">{{ document.source }}</span>
                                      <span v-if="document.file_size" class="document-size">({{ formatFileSize(document.file_size) }})</span>
                                    </div>
                                  </div>
                                  <div class="document-actions">
                                    <button v-if="document.downloadable" @click.stop="downloadLinkedDocument(file.linkedEvent.id, docIndex, document)" class="download-btn" title="Download Document">
                                      <i class="fas fa-download"></i>
                                    </button>
                                    <span v-else class="not-downloadable" title="Document not available for download">
                                      <i class="fas fa-ban"></i>
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                            
                            <div class="evidence-actions">
                              <!-- Only show View Details when documents are NOT loaded -->
                              <button v-if="!file.linkedEvent?.documents || file.linkedEvent.documents.length === 0" @click="showLinkedEventDetails(file.linkedEvent)" class="view-details-btn">
                                <i class="fas fa-info-circle"></i> View Details
                              </button>
                              <!-- Only show Refresh Docs when documents are loaded -->
                              
                            </div>
                          </div>
                          <span class="linked-evidence-badge">Linked Event</span>
                        </div>
                        
                        <!-- Regular File -->
                        <a v-else :href="file['aws-file_link']" :download="file.fileName" target="_blank" class="evidence-link">
                          <i class="fas fa-download"></i> {{ file.fileName }}
                          <span v-if="file.size" class="file-size">({{ formatFileSize(file.size) }})</span>
                          <span v-if="file.upload_type === 's3'" class="s3-indicator" title="Stored in S3">
                            <i class="fas fa-cloud"></i>
                          </span>
                        </a>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Legacy evidence display for backward compatibility -->
                  <div v-else-if="mitigation.fileData" class="evidence-section">
                    <h5><i class="fas fa-file-alt"></i> Evidence</h5>
                    <a :href="mitigation.fileData" download :filename="mitigation.fileName" class="evidence-link">
                      <i class="fas fa-download"></i> {{ mitigation.fileName }}
                    </a>
                  </div>
                  
                  <!-- Current decision -->
                  <div v-if="mitigation.approved !== undefined" class="decision-tag" 
                       :class="{ 
                         'approved': mitigation.approved === true, 
                         'rejected': mitigation.approved === false 
                       }">
                    <i class="fas" :class="{
                      'fa-check-circle': mitigation.approved === true,
                      'fa-times-circle': mitigation.approved === false
                    }"></i>
                    {{ mitigation.approved ? 'Approved' : 'Rejected' }}
                  </div>
                  
                  <!-- Show current reviewer remarks if rejected -->
                  <div v-if="mitigation.approved === false && mitigation.remarks" class="remarks-section">
                    <h5><i class="fas fa-exclamation-triangle"></i> Reviewer Feedback</h5>
                    <p class="remarks-text">{{ mitigation.remarks }}</p>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Approval controls section -->
            <div class="approval-controls">
              <!-- Only show approval buttons if not yet approved or rejected -->
              <div v-if="mitigation.approved !== true && mitigation.approved !== false && !reviewCompleted" class="approval-buttons">
                <button 
                  @click="approveMitigation(id, true)" 
                  class="approve-btn"
                >
                  <i class="fas fa-check"></i> Approve
                </button>
                <button 
                  @click="approveMitigation(id, false)" 
                  class="reject-btn"
                >
                  <i class="fas fa-times"></i> Reject
                </button>
              </div>
              
              <!-- Show remarks field only when rejected -->
              <div v-if="mitigation.approved === false && !reviewCompleted" class="remarks-field">
                <label for="remarks">Feedback (required for rejection):</label>
                <textarea 
                  id="remarks" 
                  v-model="mitigation.remarks" 
                  class="remarks-input" 
                  placeholder="Provide feedback explaining why this mitigation was rejected..."
                ></textarea>
                
                <!-- Add a button to save remarks -->
                <button @click="updateRemarks(id)" class="save-remarks-btn">
                  <i class="fas fa-save"></i> Save Feedback
                </button>
                
                <!-- Allow changing decision -->
                <button @click="approveMitigation(id, true)" class="change-decision-btn">
                  <i class="fas fa-exchange-alt"></i> Change to Approve
                </button>
              </div>
              
              <!-- Show status and action buttons for approved items -->
              <div v-if="mitigation.approved === true && !reviewCompleted" class="approved-actions">
                <button @click="approveMitigation(id, false)" class="change-decision-btn">
                  <i class="fas fa-exchange-alt"></i> Change to Reject
                </button>
              </div>
              
              <!-- Show remarks if already rejected and submitted -->
              <div v-if="mitigation.approved === false && reviewCompleted && mitigation.remarks" class="reviewer-remarks-display">
                <h5><i class="fas fa-comment-exclamation"></i> Rejection Feedback</h5>
                <p>{{ mitigation.remarks }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Form details review section -->
        <div class="form-details-review">
          <h4>Risk Mitigation Questionnaire</h4>
          
          <!-- Add status badge at the top -->
          <div v-if="formDetails.approved !== undefined" class="approval-status" :class="{ 
            'approved': formDetails.approved, 
            'rejected': formDetails.approved === false 
          }">
            <i class="fas" :class="formDetails.approved ? 'fa-check-circle' : 'fa-times-circle'"></i>
            {{ formDetails.approved ? 'Questionnaire Approved' : 'Revisions Requested' }}
          </div>
          
          <!-- Add submission dates when available -->
          <div class="submission-dates">
            <div v-if="formDetails.user_submitted_date" class="submission-date user-date">
              <i class="fas fa-clock"></i> Submitted: {{ formatDateTime(formDetails.user_submitted_date) }}
            </div>
            <div v-if="formDetails.reviewer_submitted_date" class="submission-date reviewer-date">
              <i class="fas fa-check-circle"></i> Reviewed: {{ formatDateTime(formDetails.reviewer_submitted_date) }}
            </div>
          </div>
          

          
          <!-- Modified form-split-content sections to include edit functionality -->
          <div class="form-split-content">
            <div class="form-field-label"><h5>1. What is the cost for this mitigation?</h5></div>
            <div class="form-field-split">
              <div class="form-field-previous" v-if="previousFormDetails">
                <div class="version-label">Previous Version</div>
                <p>{{ getPreviousFormDetail('cost') }} {{ getPreviousFormDetail('costCurrency') || 'USD' }}</p>
              </div>
              <div class="form-field-current" :class="{ 'highlight-changed': hasFormFieldChanged('cost') }">
                <div class="version-label">Current Version</div>
                <p>{{ formDetails.cost || 'Not specified' }} {{ formDetails.costCurrency || 'USD' }}</p>
              </div>
            </div>
          </div>

          <!-- Repeat similar pattern for other questions -->
          <div class="form-split-content">
            <div class="form-field-label"><h5>2. What is the impact for this mitigation?</h5></div>
            <div class="form-field-split">
              <div class="form-field-previous" v-if="previousFormDetails">
                <div class="version-label">Previous Version</div>
                <p>{{ getPreviousFormDetail('impact') }}</p>
              </div>
              <div class="form-field-current" :class="{ 'highlight-changed': hasFormFieldChanged('impact') }">
                <div class="version-label">Current Version</div>
                <p>{{ formDetails.impact || 'Not specified' }}</p>
              </div>
            </div>
          </div>

          <div class="form-split-content">
            <div class="form-field-label"><h5>3. What is the financial impact for this mitigation?</h5></div>
            <div class="form-field-split">
              <div class="form-field-previous" v-if="previousFormDetails">
                <div class="version-label">Previous Version</div>
                <p>{{ getPreviousFormDetail('financialImpact') }}</p>
              </div>
              <div class="form-field-current" :class="{ 'highlight-changed': hasFormFieldChanged('financialImpact') }">
                <div class="version-label">Current Version</div>
                <p>{{ formDetails.financialImpact || 'Not specified' }}</p>
              </div>
            </div>
          </div>

          <div class="form-split-content">
            <div class="form-field-label"><h5>4. What is the reputational impact for this mitigation?</h5></div>
            <div class="form-field-split">
              <div class="form-field-previous" v-if="previousFormDetails">
                <div class="version-label">Previous Version</div>
                <p>{{ getPreviousFormDetail('reputationalImpact') }}</p>
              </div>
              <div class="form-field-current" :class="{ 'highlight-changed': hasFormFieldChanged('reputationalImpact') }">
                <div class="version-label">Current Version</div>
                <p>{{ formDetails.reputationalImpact || 'Not specified' }}</p>
              </div>
            </div>
          </div>

          <div class="form-split-content">
            <div class="form-field-label"><h5>5. What is the Operational Impact for this mitigation?</h5></div>
            <div class="form-field-split">
              <div class="form-field-previous" v-if="previousFormDetails">
                <div class="version-label">Previous Version</div>
                <p>{{ getPreviousFormDetail('operationalImpact') }}</p>
              </div>
              <div class="form-field-current" :class="{ 'highlight-changed': hasFormFieldChanged('operationalImpact') }">
                <div class="version-label">Current Version</div>
                <p>{{ formDetails.operationalImpact || 'Not specified' }}</p>
              </div>
            </div>
          </div>

          <div class="form-split-content">
            <div class="form-field-label"><h5>6. What is the Financial Loss for this mitigation?</h5></div>
            <div class="form-field-split">
              <div class="form-field-previous" v-if="previousFormDetails">
                <div class="version-label">Previous Version</div>
                <p>{{ getPreviousFormDetail('financialLoss') }} {{ getPreviousFormDetail('financialLossCurrency') || 'USD' }}</p>
              </div>
              <div class="form-field-current" :class="{ 'highlight-changed': hasFormFieldChanged('financialLoss') }">
                <div class="version-label">Current Version</div>
                <p>{{ formDetails.financialLoss || 'Not specified' }} {{ formDetails.financialLossCurrency || 'USD' }}</p>
              </div>
            </div>
          </div>

          <div class="form-split-content">
            <div class="form-field-label"><h5>7. What is the expected system downtime (hrs) if this risk occurs?</h5></div>
            <div class="form-field-split">
              <div class="form-field-previous" v-if="previousFormDetails">
                <div class="version-label">Previous Version</div>
                <p>{{ getPreviousFormDetail('systemDowntime') }}</p>
              </div>
              <div class="form-field-current" :class="{ 'highlight-changed': hasFormFieldChanged('systemDowntime') }">
                <div class="version-label">Current Version</div>
                <p>{{ formDetails.systemDowntime || 'Not specified' }}</p>
              </div>
            </div>
          </div>
          <div class="form-split-content">
            <div class="form-field-label"><h5>8. How long did it take to recover last time (hrs)?</h5></div>
            <div class="form-field-split">
              <div class="form-field-previous" v-if="previousFormDetails">
                <div class="version-label">Previous Version</div>
                <p>{{ getPreviousFormDetail('recoveryTime') }}</p>
              </div>
              <div class="form-field-current" :class="{ 'highlight-changed': hasFormFieldChanged('recoveryTime') }">
                <div class="version-label">Current Version</div>
                <p>{{ formDetails.recoveryTime || 'Not specified' }}</p>
              </div>
            </div>
          </div>
          <div class="form-split-content">
            <div class="form-field-label"><h5>9. Is it possible that this risk will recur again?</h5></div>
            <div class="form-field-split">
              <div class="form-field-previous" v-if="previousFormDetails">
                <div class="version-label">Previous Version</div>
                <p>{{ getPreviousFormDetail('recurrencePossible') }}</p>
              </div>
              <div class="form-field-current" :class="{ 'highlight-changed': hasFormFieldChanged('recurrencePossible') }">
                <div class="version-label">Current Version</div>
                <p>{{ formDetails.recurrencePossible || 'Not specified' }}</p>
              </div>
            </div>
          </div>
          <div class="form-split-content">
            <div class="form-field-label"><h5>10. Is this an Improvement Initiative which will prevent the future recurrence of said risk?</h5></div>
            <div class="form-field-split">
              <div class="form-field-previous" v-if="previousFormDetails">
                <div class="version-label">Previous Version</div>
                <p>{{ getPreviousFormDetail('improvementInitiative') }}</p>
              </div>
              <div class="form-field-current" :class="{ 'highlight-changed': hasFormFieldChanged('improvementInitiative') }">
                <div class="version-label">Current Version</div>
                <p>{{ formDetails.improvementInitiative || 'Not specified' }}</p>
              </div>
            </div>
          </div>
          
          <!-- Add questionnaire approval controls -->
          <div class="questionnaire-approval" v-if="!reviewCompleted">
            <div v-if="formDetails.approved === undefined" class="approval-buttons">
              <button @click="approveQuestionnaire(true)" class="approve-btn">
                <i class="fas fa-check"></i> Approve Questionnaire
              </button>
              <button @click="approveQuestionnaire(false)" class="reject-btn">
                <i class="fas fa-times"></i> Request Revisions
              </button>
            </div>
            
            <div v-if="formDetails.approved === true" class="approval-status approved">
              <i class="fas fa-check-circle"></i> Questionnaire Approved
              <button @click="approveQuestionnaire(false)" class="change-decision-btn">
                <i class="fas fa-exchange-alt"></i> Change to Reject
              </button>
            </div>
            
            <div v-if="formDetails.approved === false" class="approval-status rejected">
              <i class="fas fa-times-circle"></i> Revisions Requested
              
              <div class="remarks-field">
                <label for="questionnaire-remarks">Feedback (required):</label>
                <textarea 
                  id="questionnaire-remarks" 
                  v-model="formDetails.remarks" 
                  class="remarks-input" 
                  placeholder="Provide feedback on the questionnaire..."
                ></textarea>
                
                <div class="approval-actions">
                  <button @click="saveQuestionnaireRemarks" class="save-remarks-btn">
                    <i class="fas fa-save"></i> Save Feedback
                  </button>
                  
                  <button @click="approveQuestionnaire(true)" class="change-decision-btn">
                    <i class="fas fa-exchange-alt"></i> Change to Approve
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="review-actions">
          <button 
            class="submit-review-btn" 
            :disabled="reviewCompleted" 
            @click="submitReview(true)"
          >
            <i class="fas fa-check-double"></i> Approve Risk
          </button>
          <button 
            class="reject-review-btn" 
            :disabled="reviewCompleted" 
            @click="submitReview(false)"
          >
            <i class="fas fa-comment-dots"></i> Send Feedback to User
          </button>
          
          <div v-if="reviewCompleted" class="review-complete-notice">
            This review has been completed
          </div>
          
          <div v-else-if="false" class="review-warning">
            <i class="fas fa-exclamation-circle"></i>
            You must approve or reject each mitigation before submitting
          </div>
        </div>
      </div>
    </div>
    
    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import { axiosInstance as axios } from '../../config/api.js';
import './RiskWorkflow.css'; // Import the CSS file
import CustomDropdown from '../CustomDropdown.vue';
import CollapsibleTable from '../CollapsibleTable.vue';
import Dynamicalsearch from '../Dynamicalsearch.vue';
import PopupModal from '../../modules/popus/PopupModal.vue';
import { PopupService } from '../../modules/popus/popupService';
import { API_ENDPOINTS } from '../../config/api.js';
import EvidenceAttachment from '../EventHandling/EvidenceAttachment.vue';
import riskDataService from '@/services/riskService';

export default {
  name: 'UserTasks',
  components: {
    CustomDropdown,
    CollapsibleTable,
    Dynamicalsearch,
    PopupModal,
    EvidenceAttachment,
  },
  data() {
    return {
      userRisks: [],
      reviewerTasks: [],
      users: [],
      selectedUserId: '',
      loading: true,
      error: null,
      dataSourceMessage: '',
      // Search and filter properties
      searchQuery: '',
      criticalityFilter: '',
      statusFilter: '',
      assignedToFilter: '',
      reviewerFilter: '',
      showMitigationWorkflow: false,
      showReviewerWorkflow: false,
      loadingMitigations: false,
      mitigationSteps: [],
      selectedRiskId: null,
      selectedReviewer: '',
      reviewerCheckAttempts: 0, // Track reviewer check attempts to prevent infinite loops
      activeTab: 'user',
      showReviewerModal: false,
      mitigationReviewData: {},
      currentReviewTask: null,
      userNotifications: [],
      reviewCompleted: false,
      reviewApproved: false,
      loggedInUser: null,
      isLoadingUser: true,
      formDetails: {
        cost: '',
        costCurrency: 'USD',
        impact: '',
        financialImpact: '',
        reputationalImpact: '',
        operationalImpact: '',
        financialLoss: '',
        financialLossCurrency: 'USD',
        systemDowntime: '',
        recoveryTime: '',
        recurrencePossible: '',
        improvementInitiative: '',
        approved: undefined,
        remarks: '',
        user_submitted_date: null,
        reviewer_submitted_date: null
      },
      previousVersions: {},
      previousFormDetails: null,
      showQuestionnaire: false,
      questionnaireDetails: null,
      // New data properties for version management
      allVersions: [],
      selectedVersions: {},
      loadingVersions: false,
      versionData: {},
      showVersionDropdowns: true,
      globalSelectedVersion: '',
      allVersionNames: [],
      userDropdownConfig: {
        name: 'Select User',
        values: [],
      },
      criticalityDropdownConfig: {
        name: 'Criticality',
        values: [
          { value: '', label: 'All Criticality' },
          { value: 'Critical', label: 'Critical' },
          { value: 'High', label: 'High' },
          { value: 'Medium', label: 'Medium' },
          { value: 'Low', label: 'Low' }
        ],
      },
      statusDropdownConfig: {
        name: 'Status',
        values: [
          { value: '', label: 'All Status' },
          { value: 'Approved', label: 'Approved' },
          { value: 'Rejected', label: 'Rejected' },
          { value: 'Pending Review', label: 'Pending Review' },
          { value: 'Under Review', label: 'Under Review' },
          { value: 'Revision Required by User', label: 'Revision Required by User' },
          { value: 'Revision Required by Reviewer', label: 'Revision Required by Reviewer' }
        ],
      },
      assignedToDropdownConfig: {
        name: 'Assigned To',
        values: [],
      },
      reviewerDropdownConfig: {
        name: 'Reviewer',
        values: [],
      },
      expandedSections: {
        approved: true,
        rejected: true,
        pendingReview: true,
        assigned: true,
        reviewerPending: true,
        reviewerApproved: true
      },
      approvedRisks: [],
      rejectedRisks: [],
      pendingReviewRisks: [],
      assignedRisks: [],
      pendingReviewerTasks: [],
      approvedReviewerTasks: [],
      // Data properties for selective visibility
      activeStepIndex: 0,
      showQuestionnaireSection: false
    }
  },
  computed: {
    isGRCAdministrator() {
    return this.loggedInUser && this.loggedInUser.role === 'GRC Administrator';
  },
    userCount() {
      console.log('Current users in data:', this.users.length, this.users);
      return this.users.length;
    },
    allStepsCompleted() {
      const stepsToCheck = this.mitigationSteps.filter(step => Boolean(step.approved) !== true);
      return stepsToCheck.length > 0 && 
             stepsToCheck.every(step => step.status === 'Completed');
    },
    canSubmit() {
      // Always return true to enable the submission button
      return true;
    },
    canSubmitReview() {
      // Always return true to enable the review submission buttons
      return true;
    },
    questionnaireReviewed() {
      return this.latestReview && 
             this.latestReview.risk_form_details && 
             (this.latestReview.risk_form_details.approved === true || 
              this.latestReview.risk_form_details.approved === false);
    },
    questionnaireApproved() {
      return this.latestReview && 
             this.latestReview.risk_form_details && 
             this.latestReview.risk_form_details.approved === true;
    },
    questionnaireRejected() {
      return this.latestReview && 
             this.latestReview.risk_form_details && 
             this.latestReview.risk_form_details.approved === false;
    },
    questionnaireRemarks() {
      if (this.latestReview && 
          this.latestReview.risk_form_details && 
          this.latestReview.risk_form_details.remarks) {
        return this.latestReview.risk_form_details.remarks;
      }
      return '';
    },
    filteredVersions() {
      // Filter out the current review task version
      return this.allVersions.filter(version => 
        version.version !== this.currentReviewTask?.version
      );
    },
    userTaskTableHeaders() {
      return [
        { key: 'RiskInstanceId', label: 'RISK ID', sortable: true, width: '10%' },
        { key: 'RiskDescription', label: 'RISK TITLE', sortable: true, width: '35%' },
        { key: 'Category', label: 'CATEGORY', sortable: true, width: '15%' },
        { key: 'criticality', label: 'CRITICALITY', sortable: true, width: '12%' },
        { key: 'AssignedTo', label: 'ASSIGNED TO', sortable: true, width: '15%' },
        { key: 'Reviewer', label: 'REVIEWER', sortable: true, width: '13%' },
        { key: 'ReviewCount', label: 'REVIEW COUNT', sortable: true, width: '10%' },
        { key: 'actions', label: 'ACTION', sortable: false, width: '10%' }
      ];
    },
    reviewerTaskTableHeaders() {
      return [
        { key: 'RiskInstanceId', label: 'RISK ID', sortable: true, width: '10%' },
        { key: 'RiskDescription', label: 'RISK TITLE', sortable: true, width: '35%' },
        { key: 'Category', label: 'CATEGORY', sortable: true, width: '15%' },
        { key: 'criticality', label: 'CRITICALITY', sortable: true, width: '12%' },
        { key: 'AssignedTo', label: 'ASSIGNED TO', sortable: true, width: '15%' },
        { key: 'Reviewer', label: 'REVIEWER', sortable: true, width: '13%' },
        { key: 'ReviewCount', label: 'REVIEW COUNT', sortable: true, width: '10%' },
        { key: 'actions', label: 'ACTION', sortable: false, width: '10%' }
      ];
    },
    userTaskSections() {
      const sections = [
        {
          name: 'Approved',
          statusKey: 'approved',
          statusClass: 'approved',
          tasks: this.approvedRisks.map(r => ({ ...r, actions: 'view' }))
        },
        {
          name: 'Rejected',
          statusKey: 'rejected',
          statusClass: 'rejected',
          tasks: this.rejectedRisks.map(r => ({ ...r, actions: 'resubmit' }))
        },
        {
          name: 'Pending Review',
          statusKey: 'pendingReview',
          statusClass: 'pending-review',
          tasks: this.pendingReviewRisks.map(r => ({ ...r, actions: 'view' }))
        },
        {
          name: 'Assigned',
          statusKey: 'assigned',
          statusClass: 'assigned',
          tasks: this.assignedRisks.map(r => ({ ...r, actions: 'view' }))
        }
      ];
      
      // Debug logging
      console.log('Computing user task sections:', sections);
      return sections;
    },
    reviewerTaskSections() {
      const sections = [
        {
          name: 'Pending Review',
          statusKey: 'reviewerPending',
          statusClass: 'pending-review',
          tasks: this.pendingReviewerTasks.map(r => ({ ...r, actions: 'review' }))
        },
        {
          name: 'Approved',
          statusKey: 'reviewerApproved',
          statusClass: 'approved',
          tasks: this.approvedReviewerTasks.map(r => ({ ...r, actions: 'view' }))
        }
      ];
      
      // Debug logging
      console.log('Computing reviewer task sections:', sections);
      return sections;
    }
  },
  watch: {
    users: {
      immediate: true,
      handler(newUsers) {
        this.userDropdownConfig.values = [
          { value: '', label: 'All Users' },
          ...newUsers.map(user => ({
            value: user.UserId,
            label: `${user.UserName}${user.department ? ` (${user.department})` : ''}`
          }))
        ];
      }
    }
  },
  mounted() {
    console.log('RiskWorkflow component mounted');
    
    // Fetch users immediately when component mounts
    this.fetchUsers();
    this.fetchLoggedInUser();
    
    // Set a small delay to ensure the DOM is fully rendered
    setTimeout(() => {
      // Force a re-render of the dropdown
      if (this.users.length === 0) {
        this.fetchUsers();
      }
      
      // If selectedUserId is already set, fetch data
      if (this.selectedUserId) {
        console.log('Selected user ID found, fetching data:', this.selectedUserId);
        this.fetchData();
      }
    }, 500);
  },
  methods: {
    // Filter risks based on search query and filters
    filterRisks() {
      // This method will be called when filters change
      // The actual filtering logic will be handled in computed properties
      console.log('Filtering risks with:', {
        searchQuery: this.searchQuery,
        criticalityFilter: this.criticalityFilter,
        statusFilter: this.statusFilter,
        assignedToFilter: this.assignedToFilter,
        reviewerFilter: this.reviewerFilter
      });
    },
    // Task organization and section management methods
    organizeRisksByStatus() {
      console.log('Organizing risks by status. User risks:', this.userRisks);
      
      // Check if userRisks is an array
      if (!Array.isArray(this.userRisks)) {
        console.error('userRisks is not an array:', this.userRisks);
        this.approvedRisks = [];
        this.rejectedRisks = [];
        this.pendingReviewRisks = [];
        this.assignedRisks = [];
        return;
      }
      
      this.approvedRisks = this.userRisks.filter(risk => risk.RiskStatus === 'Approved');
      this.rejectedRisks = this.userRisks.filter(risk => 
        risk.RiskStatus === 'Rejected' || risk.RiskStatus === 'Revision Required by User'
      );
      this.pendingReviewRisks = this.userRisks.filter(risk => 
        risk.RiskStatus === 'Pending Review' || 
        risk.RiskStatus === 'Under Review' ||
        risk.RiskStatus === 'Revision Required by Reviewer'
      );
      this.assignedRisks = this.userRisks.filter(risk => 
        !['Approved', 'Rejected', 'Pending Review', 'Under Review', 'Revision Required by User', 'Revision Required by Reviewer'].includes(risk.RiskStatus)
      );
      
      console.log('Organized user risks by status:', {
        approved: this.approvedRisks.length,
        rejected: this.rejectedRisks.length,
        pendingReview: this.pendingReviewRisks.length,
        assigned: this.assignedRisks.length
      });

      // Add formatted fields for display
      [this.approvedRisks, this.rejectedRisks, this.pendingReviewRisks, this.assignedRisks].forEach(riskArray => {
        riskArray.forEach(risk => {
          // Ensure Origin field exists
          if (!risk.Origin) {
            risk.Origin = 'MANUAL';
          }
          
          // Ensure RiskDescription exists
          if (!risk.RiskDescription) {
            risk.RiskDescription = risk.RiskTitle || 'No description available';
          }
          
          // Format criticality with HTML
          risk.criticality = `<span class="risk-workflow-criticality-badge ${risk.Criticality?.toLowerCase() || 'unknown'}">${risk.Criticality || 'Unknown'}</span>`;
          
          // Format status with HTML
          risk.status = this.formatRiskStatus(risk);
        });
      });

      // Check if reviewerTasks is an array
      if (!Array.isArray(this.reviewerTasks)) {
        console.error('reviewerTasks is not an array:', this.reviewerTasks);
        this.approvedReviewerTasks = [];
        this.pendingReviewerTasks = [];
        return;
      }

      // Organize reviewer tasks
      this.approvedReviewerTasks = this.reviewerTasks.filter(task => task.RiskStatus === 'Approved');
      this.pendingReviewerTasks = this.reviewerTasks.filter(task => task.RiskStatus !== 'Approved');

      // Add formatted fields for reviewer tasks
      [this.approvedReviewerTasks, this.pendingReviewerTasks].forEach(taskArray => {
        taskArray.forEach(task => {
          // Ensure Origin field exists
          if (!task.Origin) {
            task.Origin = 'MANUAL';
          }
          
          // Ensure Category exists
          if (!task.Category) {
            task.Category = 'Unknown';
          }
          
          // Ensure RiskDescription exists
          if (!task.RiskDescription) {
            task.RiskDescription = task.RiskTitle || 'No description available';
          }
          
          // Format criticality with HTML
          task.criticality = `<span class="risk-workflow-criticality-badge ${task.Criticality?.toLowerCase() || 'unknown'}">${task.Criticality || 'Unknown'}</span>`;
          
          // Format status with HTML
          task.status = this.formatReviewerTaskStatus(task);
        });
      });

      // Set default expanded sections
      this.expandedSections = {
        approved: this.approvedRisks.length > 0,
        rejected: this.rejectedRisks.length > 0,
        pendingReview: this.pendingReviewRisks.length > 0,
        assigned: this.assignedRisks.length === 0 ? true : this.assignedRisks.length < 5,
        reviewerPending: this.pendingReviewerTasks.length > 0,
        reviewerApproved: this.approvedReviewerTasks.length > 0 && this.pendingReviewerTasks.length === 0
      };
      
      console.log('Set expanded sections:', this.expandedSections);
      console.log('User task sections computed:', this.userTaskSections);
      
      // Force reactivity update
      this.$forceUpdate();
    },

    formatRiskStatus(risk) {
      let statusText = risk.RiskStatus === 'Revision Required by Reviewer' ? 'Waiting for Reviewer' : 
                      risk.RiskStatus === 'Revision Required by User' ? 'Action Required' : 
                      risk.RiskStatus || 'Not Assigned';
      
      let statusClass = 'risk-workflow-status-' + (risk.RiskStatus?.toLowerCase().replace(/\s+/g, '-') || 'not-assigned');
      
      let statusHtml = `<span class="${statusClass}">${statusText}</span>`;
      
      if (risk.MitigationStatus) {
        statusHtml += `<br><span class="risk-workflow-mitigation-status ${this.getMitigationStatusClass(risk.MitigationStatus)}">${risk.MitigationStatus}</span>`;
      }
      
      if (risk.MitigationDueDate) {
        statusHtml += `<br><span class="risk-workflow-due-status ${this.getDueStatusClass(risk.MitigationDueDate)}">${this.getDueStatusText(risk.MitigationDueDate)}</span>`;
      }
      
      return statusHtml;
    },

    formatReviewerTaskStatus(task) {
      let statusText = task.RiskStatus === 'Revision Required by Reviewer' ? 'Review Required' : 
                      task.RiskStatus === 'Revision Required by User' ? 'Feedback Sent' : 
                      task.RiskStatus || 'Unknown';
      
      let statusHtml = `<span>${statusText}</span>`;
      
      if (task.MitigationStatus) {
        statusHtml += `<br><span class="risk-workflow-mitigation-status ${this.getMitigationStatusClass(task.MitigationStatus)}">${task.MitigationStatus}</span>`;
      }
      
      if (this.getUserName(task.UserId)) {
        statusHtml += `<br><div style="font-size:12px;color:#888;">By: ${this.getUserName(task.UserId)}</div>`;
      }
      
      return statusHtml;
    },

    toggleSection(section) {
      this.expandedSections[section] = !this.expandedSections[section];
    },

    handleUserTaskClick(risk) {
      if (risk.actions === 'view' || risk.actions === 'resubmit') {
        this.viewMitigations(risk.RiskInstanceId);
      }
    },

    handleReviewerTaskClick(task) {
      if (task.actions === 'review') {
        this.reviewMitigations(task);
      } else if (task.actions === 'view') {
        this.reviewMitigations(task);
      }
    },

        // Add the sendPushNotification method at the beginning of methods
    async sendPushNotification(notificationData) {
      try {
        await axios.post(API_ENDPOINTS.PUSH_NOTIFICATION, notificationData);
        console.log('Push notification sent successfully');
      } catch (error) {
        console.error('Error sending push notification:', error);
      }
    },
    async fetchLoggedInUser() {
    this.isLoadingUser = true;
    try {
      // Call your backend API to get logged-in user details
              const response = await axios.get(API_ENDPOINTS.CURRENT_USER);
      this.loggedInUser = response.data;
      
      console.log('Logged in user:', this.loggedInUser);
      
      // ALWAYS set the logged-in user as default, even for GRC Administrator
      this.selectedUserId = this.loggedInUser.UserId;
      console.log('Auto-selected logged-in user ID:', this.selectedUserId);
      
      // Now fetch users list (only if GRC Administrator)
      if (this.isGRCAdministrator) {
        await this.fetchUsers();
      } else {
        // For non-GRC administrators, create a single-user array
        this.users = [this.loggedInUser];
        this.loading = false;
      }
      
      // Fetch data after user is loaded
      this.fetchData();
      
    } catch (error) {
      console.error('Error fetching logged-in user:', error);
      this.error = `Failed to fetch user details: ${error.message}`;
    } finally {
      this.isLoadingUser = false;
    }
  },
    fetchUsers() {
      console.log('Fetching users...');
      this.loading = true;

        // ADD THIS CHECK AT THE BEGINNING:
      if (!this.isGRCAdministrator) {
        console.log('Not GRC Administrator, skipping user list fetch');
        this.loading = false;
        return;
      }
      
      // Try both endpoints to ensure we get users data
              axios.get(API_ENDPOINTS.CUSTOM_USERS)
        .then(response => {
          console.log('User data received:', response.data);
          if (Array.isArray(response.data) && response.data.length > 0) {
            this.users = response.data;
            this.loading = false;
            
            // Ensure the logged-in user is selected if not already set
            if (!this.selectedUserId && this.loggedInUser) {
              this.selectedUserId = this.loggedInUser.UserId;
              console.log('Setting default user after users loaded:', this.selectedUserId);
            }
            
            // Update dropdown configuration
            this.updateUserDropdownConfig();
          } else {
            // If custom-users returns empty, try the users-for-dropdown endpoint
            return axios.get(API_ENDPOINTS.USERS_FOR_DROPDOWN);
          }
        })
        .then(response => {
          if (response && response.data) {
            console.log('User data from dropdown endpoint:', response.data);
            this.users = response.data;
            
            // Ensure the logged-in user is selected if not already set
            if (!this.selectedUserId && this.loggedInUser) {
              this.selectedUserId = this.loggedInUser.UserId;
              console.log('Setting default user after fallback users loaded:', this.selectedUserId);
            }
            
            // Update dropdown configuration
            this.updateUserDropdownConfig();
          }
          this.loading = false;
        })
        .catch(error => {
          console.error('Error fetching users:', error);
          this.error = `Failed to fetch users: ${error.message}`;
          this.loading = false;
        });
    },
    
    updateUserDropdownConfig() {
      if (this.users && this.users.length > 0) {
        this.userDropdownConfig = {
          name: 'Select User',
          values: this.users.map(user => ({
            value: user.UserId,
            text: user.UserName
          }))
        };
        
        console.log('Updated user dropdown config:', this.userDropdownConfig);
      }
    },
    
    fetchData() {
      if (!this.selectedUserId) {
        this.userRisks = [];
        this.reviewerTasks = [];
        this.dataSourceMessage = 'Select a user to load tasks';
        return;
      }
      
      this.loading = true;
      this.dataSourceMessage = 'Loading tasks...';
      
      if (riskDataService.hasRiskInstancesCache()) {
        this.dataSourceMessage = '';
      } else {
        this.dataSourceMessage = '';
      }
      
      // Only fetch user risks and reviewer tasks, not notifications
      Promise.all([
        axios.get(API_ENDPOINTS.USER_RISKS(this.selectedUserId)),
        axios.get(API_ENDPOINTS.REVIEWER_TASKS(this.selectedUserId))
      ])
      .then(([userResponse, reviewerResponse]) => {
        // Handle new response structure with risks/tasks and filter_info
        this.userRisks = (userResponse.data && userResponse.data.risks) || userResponse.data || [];
        this.reviewerTasks = (reviewerResponse.data && reviewerResponse.data.tasks) || reviewerResponse.data || [];
        
        console.log('API responses received:', {
          userRisks: this.userRisks,
          reviewerTasks: this.reviewerTasks
        });
        
        // Log framework filter info if available
        if (userResponse.data && userResponse.data.filter_info) {
          console.log('Framework filter info:', userResponse.data.filter_info);
        }
        
        // Add last submitted date to user risks by fetching latest review
        if (Array.isArray(this.userRisks)) {
        this.userRisks.forEach((risk, index) => {
          axios.get(API_ENDPOINTS.LATEST_REVIEW(risk.RiskInstanceId))
            .then(response => {
              if (response.data && response.data.user_submitted_date) {
                // Create a new array with the updated risk object
                const updatedRisks = [...this.userRisks];
                updatedRisks[index] = {
                  ...risk,
                  last_submitted: response.data.user_submitted_date
                };
                this.userRisks = updatedRisks;
              } else if (response.data && response.data.submission_date) {
                // Create a new array with the updated risk object
                const updatedRisks = [...this.userRisks];
                updatedRisks[index] = {
                  ...risk,
                  last_submitted: response.data.submission_date
                };
                this.userRisks = updatedRisks;
              }
            })
            .catch(error => {
              console.error(`Error fetching latest review for risk ${risk.RiskInstanceId}:`, error);
            });
        });
        
        console.log('User risks:', this.userRisks); // Log to verify data
        
        // Add notification icons based on risk status directly
        this.userRisks.forEach(risk => {
          if (risk.RiskStatus === 'Revision Required') {
            risk.hasNotification = true;
            risk.approved = false;
          } else if (risk.RiskStatus === 'Approved') {
            risk.hasNotification = true;
            risk.approved = true;
          }
        });
        } else {
          console.error('userRisks is not an array:', this.userRisks);
          this.userRisks = [];
        }
        
        this.loading = false;
        this.error = null;
        this.dataSourceMessage = '';
        
        // Debug logging
        console.log('User risks fetched:', this.userRisks);
        console.log('Reviewer tasks fetched:', this.reviewerTasks);
        
        // Organize risks by status for collapsible sections
        this.organizeRisksByStatus();
        
        // Debug logging after organization
        console.log('Organized risks:', {
          approved: this.approvedRisks,
          rejected: this.rejectedRisks,
          pendingReview: this.pendingReviewRisks,
          assigned: this.assignedRisks
        });
      })
      .catch(error => {
        console.error('Error fetching data:', error);
        this.error = `Failed to fetch data: ${error.message}`;
        this.loading = false;
        this.dataSourceMessage = 'Failed to load tasks';
      });
    },
    getUserName(userId) {
      const user = this.users.find(u => u.UserId == userId);
      return user ? user.UserName : 'Unknown';
    },
    startWork(riskId) {
      this.loading = true;
      console.log(`Starting work on risk ID: ${riskId}`);
      
      // Ensure we're sending the correct data format
      const requestData = {
        risk_id: riskId,
        status: 'Work In Progress'
      };
      
      console.log('Sending request data:', requestData);
      
      // Update mitigation status instead of risk status
              axios.post(API_ENDPOINTS.UPDATE_MITIGATION_STATUS, requestData)
        .then(response => {
          console.log('Status updated:', response.data);
          // Update the local risk status
          const index = this.userRisks.findIndex(r => r.RiskInstanceId === riskId);
          if (index !== -1) {
            this.userRisks[index].MitigationStatus = 'Work In Progress';
          }
          this.loading = false;
        })
        .catch(error => {
          console.error('Error updating status:', error);
          console.error('Error response:', error.response ? error.response.data : 'No response data');
          this.error = `Failed to update status: ${error.message}`;
          this.loading = false;
        });
    },
    completeMitigation(riskId) {
      this.loading = true;
              axios.post(API_ENDPOINTS.UPDATE_MITIGATION_STATUS, {
        risk_id: riskId,
        status: 'Completed'
      })
      .then(response => {
        console.log('Status updated:', response.data);
        // Update the local risk status
        const index = this.userRisks.findIndex(r => r.RiskInstanceId === riskId);
        if (index !== -1) {
          this.userRisks[index].MitigationStatus = 'Completed';
          this.userRisks[index].RiskStatus = 'Approved'; // Also update risk status
        }
        this.loading = false;
        // Send push notification for mitigation completion
        this.sendPushNotification({
          title: 'Mitigation Completed',
          message: `Mitigation for risk ${riskId} has been marked as completed successfully.`,
          category: 'risk',
          priority: 'medium',
          user_id: this.selectedUserId || 'default_user'
        });
        PopupService.success('Mitigation marked as completed!', 'Success');
      })
      .catch(error => {
        console.error('Error updating status:', error);
        // Send push notification for mitigation completion error
        this.sendPushNotification({
          title: 'Mitigation Completion Failed',
          message: `Failed to mark mitigation for risk ${riskId} as completed: ${error.message}`,
          category: 'risk',
          priority: 'high',
          user_id: this.selectedUserId || 'default_user'
        });
        this.error = `Failed to update status: ${error.message}`;
        this.loading = false;
      });
    },
    viewMitigations(riskId) {
      this.selectedRiskId = riskId;
      this.loadingMitigations = true;
      this.showMitigationWorkflow = true; // Show workflow in full screen
      // Initialize visibility states
      this.activeStepIndex = 0;
      this.showQuestionnaireSection = false;
      
      // First, get the basic mitigation steps
              axios.get(API_ENDPOINTS.RISK_MITIGATIONS(riskId))
        .then(response => {
          console.log('Mitigations received:', response.data);
          this.mitigationSteps = this.parseMitigations(response.data);
          
          // Get the risk form details
          axios.get(API_ENDPOINTS.RISK_FORM_DETAILS(riskId))
            .then(formResponse => {
              console.log('Form details received:', formResponse.data);
              // Ensure all form values are strings
              this.formDetails = {
                cost: String(formResponse.data.cost || ''),
                costCurrency: formResponse.data.costCurrency || 'USD',
                impact: String(formResponse.data.impact || ''),
                financialImpact: String(formResponse.data.financialImpact || ''),
                reputationalImpact: String(formResponse.data.reputationalImpact || ''),
                operationalImpact: String(formResponse.data.operationalImpact || ''),
                financialLoss: String(formResponse.data.financialLoss || ''),
                financialLossCurrency: formResponse.data.financialLossCurrency || 'USD',
                systemDowntime: String(formResponse.data.systemDowntime || ''),
                recoveryTime: String(formResponse.data.recoveryTime || ''),
                recurrencePossible: formResponse.data.recurrencePossible || '',
                improvementInitiative: formResponse.data.improvementInitiative || '',
                approved: formResponse.data.approved,
                remarks: formResponse.data.remarks || '',
                user_submitted_date: formResponse.data.user_submitted_date || formResponse.data.submission_date,
                reviewer_submitted_date: formResponse.data.reviewer_submitted_date
              };
              
              // Get the latest R version from risk_approval table to get approval status
              axios.get(API_ENDPOINTS.LATEST_REVIEW(riskId))
                .then(reviewResponse => {
                  const reviewData = reviewResponse.data;
                  console.log('Latest review data:', reviewData);
                  
                  // Store the latest review
                  this.latestReview = reviewData;
                  
                  // Update form details with submission dates from the review data
                  if (reviewData && reviewData.risk_form_details) {
                    this.formDetails = {
                      ...this.formDetails,
                      approved: reviewData.risk_form_details.approved,
                      remarks: reviewData.risk_form_details.remarks || '',
                      user_submitted_date: reviewData.user_submitted_date || reviewData.submission_date,
                      reviewer_submitted_date: reviewData.reviewer_submitted_date || reviewData.review_date
                    };
                  }
                  
                  if (reviewData && reviewData.mitigations) {
                    // Create new steps array with proper boolean values for approved
                    const updatedSteps = [];
                    
                    // Process each mitigation from the review data
                    Object.keys(reviewData.mitigations).forEach(stepId => {
                      const mitigation = reviewData.mitigations[stepId];
                      
                      // Ensure approved is a proper boolean value if it exists, otherwise leave it undefined
                      let isApproved = undefined;
                      if ('approved' in mitigation) {
                        isApproved = mitigation.approved === true || mitigation.approved === "true";
                      }
                      
                      updatedSteps.push({
                        title: `Step ${stepId}`,
                        description: mitigation.description,
                        status: mitigation.status || 'Completed',
                        approved: isApproved,  // This could be undefined, true, or false
                        remarks: mitigation.remarks || '',
                        comments: mitigation.comments || '',
                        fileData: mitigation.fileData,
                        fileName: mitigation.fileName,
                        user_submitted_date: mitigation.user_submitted_date,  // Add user submission date
                        reviewer_submitted_date: mitigation.reviewer_submitted_date  // Add reviewer submission date
                      });
                    });
                    
                    // Replace the mitigation steps with the properly formatted data
                    this.mitigationSteps = updatedSteps;
                  }
                  
                  // First, check if reviewer info is already available in the risk object from the table
                  const riskFromTable = this.userRisks.find(r => r.RiskInstanceId === riskId);
                  let reviewerFound = false;
                  
                  if (riskFromTable) {
                    // Check for reviewer in different possible field names
                    if (riskFromTable.ReviewerId) {
                      this.selectedReviewer = riskFromTable.ReviewerId;
                      console.log(`Using reviewer ID from risk object: ${this.selectedReviewer}`);
                      reviewerFound = true;
                    } else if (riskFromTable.Reviewer) {
                      // If we have reviewer name, try to find the ID from users array
                      const reviewerUser = this.users.find(u => u.UserName === riskFromTable.Reviewer);
                      if (reviewerUser) {
                        this.selectedReviewer = reviewerUser.UserId;
                        console.log(`Using reviewer ID from reviewer name: ${this.selectedReviewer}`);
                      } else {
                        this.selectedReviewer = riskFromTable.Reviewer;
                        console.log(`Using reviewer name from risk object: ${this.selectedReviewer}`);
                      }
                      reviewerFound = true;
                    } else if (riskFromTable.ReviewerName) {
                      // If we have ReviewerName, try to find the ID from users array
                      const reviewerUser = this.users.find(u => u.UserName === riskFromTable.ReviewerName);
                      if (reviewerUser) {
                        this.selectedReviewer = reviewerUser.UserId;
                        console.log(`Using reviewer ID from ReviewerName: ${this.selectedReviewer}`);
                      } else {
                        this.selectedReviewer = riskFromTable.ReviewerName;
                        console.log(`Using ReviewerName from risk object: ${this.selectedReviewer}`);
                      }
                      reviewerFound = true;
                    }
                  }
                  
                  // Only make API call if reviewer not found in risk object
                  if (!reviewerFound) {
                    // Check if a reviewer is already assigned
                    axios.get(API_ENDPOINTS.GET_ASSIGNED_REVIEWER(riskId))
                    .then(reviewerResponse => {
                      console.log('Reviewer response:', reviewerResponse.data);
                      
                      // Check if we have reviewer data
                      if (reviewerResponse.data && (reviewerResponse.data.reviewer_name || reviewerResponse.data.reviewer_id)) {
                        // Always use reviewer_id if available
                        if (reviewerResponse.data.reviewer_id) {
                          this.selectedReviewer = reviewerResponse.data.reviewer_id;
                          console.log(`Using reviewer ID: ${this.selectedReviewer}`);
                        } else {
                          this.selectedReviewer = reviewerResponse.data.reviewer_name;
                          console.log(`No reviewer ID available, using name: ${this.selectedReviewer}`);
                        }
                      } else if (reviewerResponse.data && reviewerResponse.data.error) {
                        // Handle specific error cases
                        console.log('Reviewer assignment error:', reviewerResponse.data.message);
                        
                        // Only show popup if it's a "no reviewer assigned" error, not a database error
                        // But first check if reviewer exists in risk object
                        const riskFromTable = this.userRisks.find(r => r.RiskInstanceId === riskId);
                        const hasReviewerInTable = riskFromTable && (riskFromTable.ReviewerId || riskFromTable.Reviewer || riskFromTable.ReviewerName);
                        
                        if (reviewerResponse.data.error === 'No reviewer assigned' && !hasReviewerInTable) {
                          this.sendPushNotification({
                            title: 'No Reviewer Assigned',
                            message: `No reviewer has been assigned to risk ${this.selectedRiskId}. Please contact your administrator.`,
                            category: 'risk',
                            priority: 'high',
                            user_id: this.selectedUserId || 'default_user'
                          });
                          PopupService.warning('No reviewer has been assigned to this risk yet. Please contact your administrator.', 'No Reviewer Assigned');
                          this.selectedReviewer = '';
                        } else if (reviewerResponse.data.error === 'No reviewer assigned' && hasReviewerInTable) {
                          // Reviewer exists in table but API returned error - use table data
                          if (riskFromTable.ReviewerId) {
                            this.selectedReviewer = riskFromTable.ReviewerId;
                          } else if (riskFromTable.Reviewer) {
                            const reviewerUser = this.users.find(u => u.UserName === riskFromTable.Reviewer);
                            this.selectedReviewer = reviewerUser ? reviewerUser.UserId : riskFromTable.Reviewer;
                          } else if (riskFromTable.ReviewerName) {
                            const reviewerUser = this.users.find(u => u.UserName === riskFromTable.ReviewerName);
                            this.selectedReviewer = reviewerUser ? reviewerUser.UserId : riskFromTable.ReviewerName;
                          }
                        } else {
                          // Database error - show error popup
                          PopupService.error(`Database error: ${reviewerResponse.data.message}`, 'Error');
                          this.selectedReviewer = '';
                        }
                      } else {
                        // Empty response or unexpected format - don't show error popup, just log
                        console.log('Empty or unexpected reviewer response from API');
                        this.selectedReviewer = '';
                      }
                      this.loadingMitigations = false;
                      
                      // Show the questionnaire section by default
                      this.showQuestionnaire = true;
                    })
                    .catch(error => {
                      console.error('Error fetching assigned reviewer:', error);
                      // Don't show error popup, just log the error
                      this.selectedReviewer = '';
                      this.loadingMitigations = false;
                      
                      // Show the questionnaire section by default even if reviewer fetch fails
                      this.showQuestionnaire = true;
                    });
                  } else {
                    // Reviewer found in risk object, skip API call
                    this.loadingMitigations = false;
                    
                    // Show the questionnaire section by default
                    this.showQuestionnaire = true;
                  }
                })
                .catch(error => {
                  console.error('Error fetching latest review:', error);
                  this.loadingMitigations = false;
                  
                  // Show the questionnaire section by default
                  this.showQuestionnaire = true;
                });
            })
            .catch(error => {
              console.error('Error fetching form details:', error);
              // Continue with default empty form details
              this.formDetails = {
                cost: '',
                costCurrency: 'USD',
                impact: '',
                financialImpact: '',
                reputationalImpact: '',
                operationalImpact: '',
                financialLoss: '',
                financialLossCurrency: 'USD',
                systemDowntime: '',
                recoveryTime: '',
                recurrencePossible: '',
                improvementInitiative: '',
                approved: undefined,
                remarks: ''
              };
              this.loadingMitigations = false;
              
              // Show the questionnaire section by default
              this.showQuestionnaire = true;
            });
        })
        .catch(error => {
          console.error('Error fetching mitigations:', error);
          this.mitigationSteps = [];
          this.loadingMitigations = false;
          
          // Show the questionnaire section by default
          this.showQuestionnaire = true;
        });
    },
    fetchLatestReviewerData(riskId) {
              axios.get(API_ENDPOINTS.LATEST_REVIEW(riskId))
        .then(response => {
          console.log('Latest review data:', response.data);
          
          if (response.data && response.data.mitigations) {
            // Update our mitigation steps with approval status and remarks
            const reviewData = response.data;
            
            this.mitigationSteps.forEach((step, index) => {
              const stepNumber = step.title.replace('Step ', '') || (index + 1).toString();
              if (reviewData.mitigations[stepNumber]) {
                const reviewInfo = reviewData.mitigations[stepNumber];
                step.approved = reviewInfo.approved;
                step.remarks = reviewInfo.remarks || '';
                
                // If this mitigation was already reviewed and had attached data
                if (reviewInfo.comments) step.comments = reviewInfo.comments;
                if (reviewInfo.fileData) {
                  step.fileData = reviewInfo.fileData;
                  step.fileName = reviewInfo.fileName;
                }
              }
            });
          }
          
          this.loadingMitigations = false;
        })
        .catch(error => {
          console.error('Error fetching review data:', error);
          this.loadingMitigations = false;
        });
    },
    parseMitigations(data) {
      // Handle the numbered object format like {"1": "Step 1 text", "2": "Step 2 text", ...}
      if (data && typeof data === 'object' && !Array.isArray(data)) {
        // Check if it's a numbered format
        const keys = Object.keys(data);
        if (keys.length > 0 && !isNaN(Number(keys[0]))) {
          const steps = [];
          // Sort keys numerically
          keys.sort((a, b) => Number(a) - Number(b));
          
          for (const key of keys) {
            steps.push({
              title: `Step ${key}`,
              description: data[key],
              status: 'Not Started'
            });
          }
          
          // Add these lines after creating steps
          for (const step of steps) {
            step.comments = step.comments || '';
            step.fileData = step.fileData || null;
            step.fileName = step.fileName || null;
          }
          return steps;
        }
      }
      
      // If it's already an array, return it
      if (Array.isArray(data)) {
        return data;
      }
      
      // If data is a string, try to parse it as JSON
      if (typeof data === 'string') {
        try {
          const parsedData = JSON.parse(data);
          // Check if the parsed data matches the numbered format
          if (parsedData && typeof parsedData === 'object' && !Array.isArray(parsedData)) {
            return this.parseMitigations(parsedData); // Recursively call to handle the parsed object
          }
          return Array.isArray(parsedData) ? parsedData : [parsedData];
        } catch (e) {
          console.error('Error parsing mitigation JSON:', e);
          return [{ title: 'Mitigation', description: data }];
        }
      }
      
      // Default fallback - create a single step with the data
      return [{ title: 'Mitigation', description: 'No detailed mitigation steps available' }];
    },
    closeMitigationModal() {
      this.showMitigationWorkflow = false;
      this.mitigationSteps = [];
      this.selectedRiskId = null;
      // Reset visibility states
      this.activeStepIndex = 0;
      this.showQuestionnaireSection = false;
    },
    selectStep(stepIndex) {
      this.activeStepIndex = stepIndex;
      this.showQuestionnaireSection = false;
    },
    selectQuestionnaire() {
      this.showQuestionnaireSection = true;
    },
    updateStepStatus(index, status) {
      console.log(`Updating step ${index + 1} status to ${status}`);
      
      // Update the step status locally
      this.mitigationSteps[index].status = status;
      
      // If all steps are completed, we don't need to update the backend yet
      // It will be sent when the user submits for review
    },
    submitForReview() {
      // Remove the canSubmit check to always allow submission
      
      // Validate questionnaire is complete
      if (!this.isQuestionnaireComplete()) {
         // Send push notification for incomplete questionnaire
        this.sendPushNotification({
          title: 'Incomplete Questionnaire',
          message: `Please complete all questionnaire fields for risk ${this.selectedRiskId} before submitting.`,
          category: 'risk',
          priority: 'medium',
          user_id: this.selectedUserId || 'default_user'
        });
        PopupService.warning('Please complete all questionnaire fields before submitting', 'Incomplete Form');
        return;
      }
      
      // Validate reviewer is assigned - first check risk object, then API
      if (!this.selectedReviewer || this.selectedReviewer === '') {
        // First check if reviewer exists in the risk object from the table
        const riskFromTable = this.userRisks.find(r => r.RiskInstanceId === this.selectedRiskId);
        
        if (riskFromTable) {
          if (riskFromTable.ReviewerId) {
            this.selectedReviewer = riskFromTable.ReviewerId;
          } else if (riskFromTable.Reviewer) {
            const reviewerUser = this.users.find(u => u.UserName === riskFromTable.Reviewer);
            this.selectedReviewer = reviewerUser ? reviewerUser.UserId : riskFromTable.Reviewer;
          } else if (riskFromTable.ReviewerName) {
            const reviewerUser = this.users.find(u => u.UserName === riskFromTable.ReviewerName);
            this.selectedReviewer = reviewerUser ? reviewerUser.UserId : riskFromTable.ReviewerName;
          }
        }
        
        // If still no reviewer, try API
        if (!this.selectedReviewer || this.selectedReviewer === '') {
          // Prevent infinite loops - only retry once
          if (this.reviewerCheckAttempts >= 1) {
            this.sendPushNotification({
              title: 'No Reviewer Assigned',
              message: `No reviewer has been assigned to risk ${this.selectedRiskId}. Please contact your administrator.`,
              category: 'risk',
              priority: 'high',
              user_id: this.selectedUserId || 'default_user'
            });
            PopupService.warning('No reviewer has been assigned to this risk yet. Please contact your administrator.', 'No Reviewer Assigned');
            this.reviewerCheckAttempts = 0; // Reset for next attempt
            return;
          }
          
          // Try to fetch reviewer one more time before showing error
          this.reviewerCheckAttempts++;
          axios.get(API_ENDPOINTS.GET_ASSIGNED_REVIEWER(this.selectedRiskId))
            .then(reviewerResponse => {
              if (reviewerResponse.data && (reviewerResponse.data.reviewer_name || reviewerResponse.data.reviewer_id)) {
                // Reviewer found, update and retry submission
                if (reviewerResponse.data.reviewer_id) {
                  this.selectedReviewer = reviewerResponse.data.reviewer_id;
                } else {
                  this.selectedReviewer = reviewerResponse.data.reviewer_name;
                }
                this.reviewerCheckAttempts = 0; // Reset before retry
                // Retry submission
                this.submitForReview();
              } else {
                // No reviewer found, show error
                this.reviewerCheckAttempts = 0; // Reset
                this.sendPushNotification({
                  title: 'No Reviewer Assigned',
                  message: `No reviewer has been assigned to risk ${this.selectedRiskId}. Please contact your administrator.`,
                  category: 'risk',
                  priority: 'high',
                  user_id: this.selectedUserId || 'default_user'
                });
                PopupService.warning('No reviewer has been assigned to this risk yet. Please contact your administrator.', 'No Reviewer Assigned');
              }
            })
            .catch(error => {
              console.error('Error fetching assigned reviewer:', error);
              this.reviewerCheckAttempts = 0; // Reset
              this.sendPushNotification({
                title: 'No Reviewer Assigned',
                message: `No reviewer has been assigned to risk ${this.selectedRiskId}. Please contact your administrator.`,
                category: 'risk',
                priority: 'high',
                user_id: this.selectedUserId || 'default_user'
              });
              PopupService.warning('No reviewer has been assigned to this risk yet. Please contact your administrator.', 'No Reviewer Assigned');
            });
          return;
        }
      }
      
      // Reset reviewer check attempts on successful validation
      this.reviewerCheckAttempts = 0;
      
      this.loading = true;
      
      // Prepare the mitigation data
      const mitigationData = {};
      this.mitigationSteps.forEach((step, index) => {
        // Extract step number from title or use index+1
        const stepNumber = step.title.replace('Step ', '') || (index + 1).toString();
        
        // If this step was previously approved, keep its approval
        if (step.approved === true) {
          mitigationData[stepNumber] = {
            description: step.description,
            status: step.status || 'Completed',
            approved: true,
            remarks: "",
            comments: step.comments || "",
            fileData: step.fileData,
            fileName: step.fileName,
            files: step.files || [] // Include files array
          };
        } else {
          // For rejected or new mitigations, include the updated data
          // but don't set 'approved' for new submissions
          const mitigationInfo = {
            description: step.description,
            status: step.status || 'Completed',
            comments: step.comments || "",
            fileData: step.fileData,
            fileName: step.fileName,
            files: step.files || [] // Include files array
          };
          
          // Only include approved and remarks if they were previously set
          if (step.approved === false) {
            mitigationInfo.approved = false;
            mitigationInfo.remarks = step.remarks || "";
          }
          
          mitigationData[stepNumber] = mitigationInfo;
        }
      });
      
      // Add timestamp to form details
      const formDetailsWithTimestamp = {
        ...this.formDetails,
        user_submitted_date: new Date().toISOString()
      };
      
      // Use the pre-assigned reviewer (already set in selectedReviewer)
      console.log(`Submitting for review with reviewer ID: ${this.selectedReviewer}, type: ${typeof this.selectedReviewer}`);
      
              axios.post(API_ENDPOINTS.ASSIGN_REVIEWER, {
        risk_id: this.selectedRiskId,
        reviewer_id: this.selectedReviewer,
        user_id: this.selectedUserId,
        mitigations: mitigationData,
        risk_form_details: formDetailsWithTimestamp,
        create_approval_record: true // Explicitly set to true to create version entry in risk_approval table
      })
      .then(response => {
        console.log('Submission response:', response.data);
        // Update the local risk data to show the new status
        const index = this.userRisks.findIndex(r => r.RiskInstanceId === this.selectedRiskId);
        if (index !== -1) {
          this.userRisks[index].MitigationStatus = 'Under Review';
          this.userRisks[index].RiskStatus = 'Revision Required by Reviewer';
        }
        this.loading = false;
        // Close the workflow view
        this.closeMitigationModal();
        // Send push notification for successful submission
        this.sendPushNotification({
          title: 'Risk Submitted for Review',
          message: `Risk ${this.selectedRiskId} has been submitted for review successfully.`,
          category: 'risk',
          priority: 'medium',
          user_id: this.selectedUserId || 'default_user'
        });
        // Show success message
        PopupService.success('Risk submitted for review successfully!', 'Success');
      })
      .catch(error => {
        console.error('Error submitting for review:', error);
        this.loading = false;
        // Send push notification for failed submission
        this.sendPushNotification({
          title: 'Risk Submission Failed',
          message: `Failed to submit risk ${this.selectedRiskId} for review: ${error.message}`,
          category: 'risk',
          priority: 'high',
          user_id: this.selectedUserId || 'default_user'
        });
        PopupService.error('Failed to submit for review. Please try again.', 'Submission Failed');
      });
    },
    closeReviewerModal() {
      this.showReviewerWorkflow = false;
      this.currentReviewTask = null;
      this.mitigationReviewData = {};
      this.previousVersions = {};
      this.previousFormDetails = null;
      this.reviewCompleted = false;
      this.reviewApproved = false;
      // Reset version-related data
      this.allVersions = [];
      this.selectedVersions = {};
      this.versionData = {};
      this.loadingVersions = false;
    },
    approveMitigation(id, approved) {
      // Don't use this.$set directly - modify the object properly for Vue reactivity
      
      // Create a new object with all existing properties
      const updatedMitigation = {
        ...this.mitigationReviewData[id],
        approved: approved,
        reviewer_submitted_date: new Date().toISOString()
      };
      
      // If approved, clear any existing remarks
      if (approved) {
        updatedMitigation.remarks = '';
      }
      
      // Update the entire object at once (Vue will detect this change)
      this.mitigationReviewData = {
        ...this.mitigationReviewData,
        [id]: updatedMitigation
      };
      
      // Find the mitigation element and update visual feedback
      const mitigationElement = document.querySelector(`.mitigation-review-item[data-id="${id}"]`);
      if (mitigationElement) {
        // Update visual feedback
        const statusBadge = mitigationElement.querySelector('.mitigation-status-badge');
        if (statusBadge) {
          statusBadge.className = `mitigation-status-badge ${approved ? 'approved' : 'rejected'}`;
          statusBadge.innerHTML = approved ? 
            '<i class="fas fa-check-circle"></i> Approved' : 
            '<i class="fas fa-times-circle"></i> Rejected';
        }
      }
    },
    submitReview(approved) {
      // Remove validation check to always allow submission
      
      this.loading = true;
      
      // Prepare the final data with all mitigations and questionnaire
      const reviewData = {
        approval_id: this.currentReviewTask.RiskInstanceId,
        risk_id: this.currentReviewTask.RiskInstanceId,
        approved: approved,
        mitigations: this.mitigationReviewData,
        risk_form_details: {
          ...this.formDetails,
          approved: this.formDetails.approved,
          remarks: this.formDetails.remarks || ''
        }
      };
      
      // Print the complete review data for debugging
      console.log('SUBMITTING REVIEW DATA:', JSON.stringify(reviewData, null, 2));
      
      // Send the complete review with all mitigations and questionnaire in one request
              axios.post(API_ENDPOINTS.COMPLETE_REVIEW, reviewData)
        .then(response => {
          console.log('Review completed:', response.data);
          this.loading = false;
          
          // Remove this task from the list
          const index = this.reviewerTasks.findIndex(t => t.RiskInstanceId === this.currentReviewTask.RiskInstanceId);
          if (index !== -1) {
            this.reviewerTasks.splice(index, 1);
          }
          
          // Set review as completed for UI
          this.reviewCompleted = true;
          this.reviewApproved = approved;
          
          // Update the current review task with the new status
          if (index !== -1) {
            const newStatus = approved ? 'Approved' : 'Revision Required by User';
            this.currentReviewTask.RiskStatus = newStatus;
            this.currentReviewTask.MitigationStatus = approved ? 'Completed' : 'Revision Required';
          }
          // Send push notification for review completion
          this.sendPushNotification({
            title: `Risk ${approved ? 'Approved' : 'Rejected'}`,
            message: `Risk ${this.currentReviewTask.RiskInstanceId} has been ${approved ? 'approved' : 'rejected'} by reviewer.`,
            category: 'risk',
            priority: 'high',
            user_id: this.currentReviewTask.UserId || 'default_user'
          });
          
          // Show success message
          PopupService.success(`Risk ${approved ? 'approved' : 'rejected'} successfully!`, 'Review Complete');
          
          // After a short delay, close the workflow view and return to tasks
          setTimeout(() => {
            this.closeReviewerModal();
          }, 2500);
        })
        .catch(error => {
          console.error('Error completing review:', error);
          this.loading = false;
          // Send push notification for review failure
          this.sendPushNotification({
            title: 'Review Submission Failed',
            message: `Failed to submit review for risk ${this.currentReviewTask.RiskInstanceId}: ${error.message}`,
            category: 'risk',
            priority: 'high',
            user_id: this.currentReviewTask.UserId || 'default_user'
          });
          PopupService.error('Failed to submit review. Please try again.', 'Review Failed');
        });
    },
    updateRemarks(id) {
      if (!this.mitigationReviewData[id].remarks.trim()) {
        // Send push notification for missing remarks
        this.sendPushNotification({
          title: 'Missing Remarks',
          message: `Please provide remarks for rejection of mitigation ${id} in risk ${this.currentReviewTask?.RiskInstanceId || this.selectedRiskId}.`,
          category: 'risk',
          priority: 'medium',
          user_id: this.selectedUserId || 'default_user'
        });
        PopupService.warning('Please provide remarks for rejection', 'Missing Remarks');
        return;
      }
      
      // Create a new object with spread operator to trigger reactivity
      this.mitigationReviewData = {
        ...this.mitigationReviewData
      };
      
      // Show visual confirmation
      console.log(`Mitigation ${id} remarks updated successfully`);
    },
    handleFileUpload(event, index) {
      const file = event.target.files[0];
      if (!file) return;
      
      // Safety check: ensure mitigationSteps array and index exist
      if (!this.mitigationSteps || !this.mitigationSteps[index]) {
        console.error('MitigationSteps array or index not found:', { index, mitigationSteps: this.mitigationSteps });
        PopupService.error('Invalid mitigation step. Please refresh and try again.', 'Upload Failed');
        event.target.value = '';
        return;
      }
      
      // Safety check: ensure selectedRiskId is available
      if (!this.selectedRiskId) {
        console.error('SelectedRiskId not found:', this.selectedRiskId);
        PopupService.error('No risk selected. Please refresh and try again.', 'Upload Failed');
        event.target.value = '';
        return;
      }
      
      // Check file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        // Send push notification for file size limit
        this.sendPushNotification({
          title: 'File Size Limit Exceeded',
          message: `File "${file.name}" exceeds the 5MB size limit for risk ${this.selectedRiskId}.`,
          category: 'risk',
          priority: 'medium',
          user_id: this.selectedUserId || 'default_user'
        });
        PopupService.warning('File size exceeds 5MB limit', 'File Size Limit');
        event.target.value = '';
        return;
      }
      
      const reader = new FileReader();
      reader.onload = (e) => {
        // Store file data as base64 string for preview
        this.mitigationSteps[index].fileData = e.target.result;
        this.mitigationSteps[index].fileName = file.name;
        
        // Create form data for file upload
        const formData = new FormData();
        formData.append('file', file);
        formData.append('userId', this.selectedUserId || 'default-user');
        formData.append('fileName', file.name);
        formData.append('riskId', this.selectedRiskId);
        formData.append('category', this.userRisks.find(r => r.RiskInstanceId === this.selectedRiskId)?.Category || 'general');
        formData.append('mitigationNumber', index + 1);
        
        // Upload using Django backend with S3 integration
        axios.post(API_ENDPOINTS.UPLOAD_RISK_EVIDENCE, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        .then(response => {
          console.log('File uploaded successfully using Django backend:', response.data);
          console.log('Response structure check:', {
            hasData: !!response.data,
            hasSuccess: response.data?.success,
            hasFile: !!response.data?.file,
            fileStructure: response.data?.file
          });
          
          if (response.data && response.data.success && response.data.file) {
            // Safety check: ensure mitigationSteps array and index still exist
            if (!this.mitigationSteps || !this.mitigationSteps[index]) {
              console.error('MitigationSteps array or index not found after upload:', { index, mitigationSteps: this.mitigationSteps });
              PopupService.error('Error saving file information. Please refresh and try again.', 'Upload Failed');
              return;
            }
            
            // Store the file information from Django backend
            this.mitigationSteps[index].savedFileName = response.data.file.fileName;
            this.mitigationSteps[index].s3FileInfo = response.data.file;
            this.mitigationSteps[index].s3Url = response.data.file.url;
            // Send push notification for successful file upload
            this.sendPushNotification({
              title: 'File Upload Successful',
              message: `File "${file.name}" has been uploaded successfully for risk ${this.selectedRiskId}.`,
              category: 'risk',
              priority: 'medium',
              user_id: this.selectedUserId || 'default_user'
            });
            
            // Optional: Add alert or notification
            PopupService.success('File uploaded successfully', 'Success');
          } else {
            console.error('S3 upload returned error:', response.data);
            const errorMessage = response.data?.error || 'Unknown upload error';
            // Send push notification for file upload error
            this.sendPushNotification({
              title: 'File Upload Failed',
              message: `Failed to upload file "${file.name}" for risk ${this.selectedRiskId}: ${errorMessage}`,
              category: 'risk',
              priority: 'high',
              user_id: this.selectedUserId || 'default_user'
            });
            PopupService.error(`Error uploading file: ${errorMessage}`, 'Upload Failed');
          }
        })
        .catch(error => {
          console.error('Error uploading file using Django backend:', error);
          
          // Extract error message from different possible sources
          let errorMessage = 'Unknown error occurred';
          if (error.response && error.response.data && error.response.data.error) {
            errorMessage = error.response.data.error;
          } else if (error.message) {
            errorMessage = error.message;
          } else if (error.response && error.response.statusText) {
            errorMessage = error.response.statusText;
          }
          
          // Send push notification for file upload error
          this.sendPushNotification({
            title: 'File Upload Failed',
            message: `Failed to upload file "${file.name}" for risk ${this.selectedRiskId}: ${errorMessage}`,
            category: 'risk',
            priority: 'high',
            user_id: this.selectedUserId || 'default_user'
          });
          PopupService.error(`Error uploading file: ${errorMessage}`, 'Upload Failed');
        });
      };
      reader.readAsDataURL(file);
    },
    removeFile(index) {
      // If we have S3 file info, delete from S3 first
      if (this.mitigationSteps[index].s3FileInfo && this.mitigationSteps[index].s3FileInfo.id) {
        const fileId = this.mitigationSteps[index].s3FileInfo.id;
        
        // Call Django backend to delete the file
        axios.delete(API_ENDPOINTS.DELETE_RISK_EVIDENCE(fileId))
                      .then(response => {
              console.log('File deleted using Django backend:', response.data);
            // Send push notification for successful file deletion
            this.sendPushNotification({
              title: 'File Removed Successfully',
              message: `File has been removed successfully from risk ${this.selectedRiskId}.`,
              category: 'risk',
              priority: 'low',
              user_id: this.selectedUserId || 'default_user'
            });
            
            // Clear file data from the step
            this.mitigationSteps[index].fileData = null;
            this.mitigationSteps[index].fileName = null;
            this.mitigationSteps[index].s3FileInfo = null;
            this.mitigationSteps[index].s3Url = null;
            
            // Reset the file input
            document.getElementById(`file-upload-${index}`).value = '';
          })
                      .catch(error => {
              console.error('Error deleting file using Django backend:', error);
            // Send push notification for file deletion error
            this.sendPushNotification({
              title: 'File Removal Warning',
              message: `File preview cleared but file may still exist on server for risk ${this.selectedRiskId}.`,
              category: 'risk',
              priority: 'medium',
              user_id: this.selectedUserId || 'default_user'
            });
            PopupService.warning('Error removing file. The file preview will be cleared, but the file may still exist on the server.', 'File Removal Warning');
            
            // Clear file data anyway
            this.mitigationSteps[index].fileData = null;
            this.mitigationSteps[index].fileName = null;
            this.mitigationSteps[index].s3FileInfo = null;
            this.mitigationSteps[index].s3Url = null;
            
            // Reset the file input
            document.getElementById(`file-upload-${index}`).value = '';
          });
      } else {
        // If no S3 info, just clear the local data
        this.mitigationSteps[index].fileData = null;
        this.mitigationSteps[index].fileName = null;
        this.mitigationSteps[index].s3FileInfo = null;
        this.mitigationSteps[index].s3Url = null;
        
        // Reset the file input
        document.getElementById(`file-upload-${index}`).value = '';
      }
    },

    // Handle files uploaded from RiskEvidenceAttachment component
    handleFilesUploaded(uploadedFiles, stepIndex) {
      console.log('Files uploaded:', uploadedFiles, 'for step index:', stepIndex);
      
      // Store uploaded files in the specified mitigation step
      if (this.mitigationSteps && this.mitigationSteps[stepIndex] !== undefined) {
        // Initialize files array if it doesn't exist
        if (!this.mitigationSteps[stepIndex].files) {
          this.mitigationSteps[stepIndex].files = [];
        }
        
        // Add uploaded files to the specified step
        this.mitigationSteps[stepIndex].files.push(...uploadedFiles);
        
        // Send push notification for successful upload
        this.sendPushNotification({
          title: 'Evidence Uploaded Successfully',
          message: `${uploadedFiles.length} file(s) uploaded successfully for risk mitigation step ${stepIndex + 1}.`,
          category: 'risk',
          priority: 'low',
          user_id: this.selectedUserId || 'default_user'
        });
        
        PopupService.success(`Successfully uploaded ${uploadedFiles.length} file(s) to step ${stepIndex + 1}`, 'Upload Complete');
      } else {
        console.error('Invalid mitigation step index for file upload:', stepIndex, 'Available steps:', this.mitigationSteps?.length);
        PopupService.error('Unable to attach files. Please try again.', 'Upload Error');
      }
    },
    fetchReviewerComments(riskId) {
              axios.get(API_ENDPOINTS.REVIEWER_COMMENTS(riskId))
        .then(response => {
          // Find the risk in the userRisks array and add the reviewer comments
          const riskIndex = this.userRisks.findIndex(r => r.RiskInstanceId === riskId);
          if (riskIndex !== -1) {
            // Create a new array with the updated risk object
            const updatedRisks = [...this.userRisks];
            updatedRisks[riskIndex] = {
              ...this.userRisks[riskIndex],
              reviewerComments: response.data
            };
            this.userRisks = updatedRisks;
          }
        })
        .catch(error => {
          console.error('Error fetching reviewer comments:', error);
        });
    },
    getStatusClass(status) {
      if (!status) return '';
      const statusLower = status.toLowerCase();
      if (statusLower.includes('approved')) return 'status-approved';
      if (statusLower.includes('revision required by user')) return 'status-revision-user';
      if (statusLower.includes('revision required by reviewer')) return 'status-revision-reviewer';
      if (statusLower.includes('revision')) return 'status-revision';
      if (statusLower.includes('under review')) return 'status-review';
      if (statusLower.includes('progress')) return 'status-progress';
      return '';
    },
    // Complete a step
    completeStep(index) {
      // Remove locking check so any step can be completed anytime
      this.mitigationSteps[index].status = 'Completed';
      // Animate the timeline progress
      this.$nextTick(() => {
        setTimeout(() => {
          const timelineEl = document.querySelector('.timeline');
          if (timelineEl) {
            timelineEl.classList.add('step-completed');
            setTimeout(() => {
              timelineEl.classList.remove('step-completed');
            }, 1000);
          }
        }, 50);
      });
    },
    
    // Reset a step to not completed
    resetStep(index) {
      this.mitigationSteps[index].status = 'In Progress';
    },
    isStepActive(index) {
      // A step is active if it is not completed or is rejected
      if (this.mitigationSteps[index].approved === false) return true;
      return this.mitigationSteps[index].status !== 'Completed';
    },
    isStepLocked() {
      // Always return false so no step is locked
      return false;
    },
    formatDate(dateString) {
      if (!dateString) return 'Not set';
      
      const date = new Date(dateString);
      return date.toLocaleDateString();
    },
    getDueStatusClass(dateString) {
      if (!dateString) return '';
      
      const dueDate = new Date(dateString);
      const today = new Date();
      
      // Reset the time part for accurate day comparison
      dueDate.setHours(0, 0, 0, 0);
      today.setHours(0, 0, 0, 0);
      
      const daysLeft = Math.floor((dueDate - today) / (1000 * 60 * 60 * 24));
      
      if (daysLeft < 0) return 'risk-workflow-overdue';
      if (daysLeft <= 3) return 'risk-workflow-urgent';
      if (daysLeft <= 7) return 'risk-workflow-warning';
      return 'risk-workflow-on-track';
    },
    getDueStatusText(dateString) {
      if (!dateString) return '';
      
      const dueDate = new Date(dateString);
      const today = new Date();
      
      // Reset the time part for accurate day comparison
      dueDate.setHours(0, 0, 0, 0);
      today.setHours(0, 0, 0, 0);
      
      const daysLeft = Math.floor((dueDate - today) / (1000 * 60 * 60 * 24));
      
      if (daysLeft < 0) return `(Delayed by ${Math.abs(daysLeft)} days)`;
      if (daysLeft === 0) return '(Due today)';
      if (daysLeft === 1) return '(Due tomorrow)';
      return `(${daysLeft} days left)`;
    },
    getMitigationStatusClass(status) {
      if (!status) return '';
      
      const statusLower = status.toLowerCase();
      if (statusLower.includes('completed')) return 'risk-workflow-status-completed';
      if (statusLower.includes('progress')) return 'risk-workflow-status-progress';
      if (statusLower.includes('revision')) return 'risk-workflow-status-revision';
      if (statusLower.includes('yet to start')) return 'risk-workflow-status-not-started';
      return '';
    },
    hasApprovalVersion(task) {
      // Check if we have extracted info, which means there's a version
      try {
        if (task.ExtractedInfo) {
          const extractedInfo = JSON.parse(task.ExtractedInfo);
          return extractedInfo && extractedInfo.version;
        }
      } catch (error) {
        console.error('Error checking approval version:', error);
      }
      return false;
    },
    isQuestionnaireComplete() {
      // Always return true to enable the submission
      return true;
    },
    validateQuestionnaire() {
      // This will be called on each input to ensure sequential completion
    },
    async reviewMitigations(task) {
      this.currentReviewTask = task;
      this.selectedRiskId = task.RiskInstanceId;
      this.loadingMitigations = true;
      this.showReviewerWorkflow = true; // Show the reviewer workflow in full screen
      this.previousVersions = {}; // Initialize empty object for previous versions
      
      try {
        // Extract the mitigations from the ExtractedInfo JSON
        const extractedInfo = JSON.parse(task.ExtractedInfo);
        console.log('Extracted info:', extractedInfo);
        
        if (extractedInfo && extractedInfo.mitigations) {
          this.mitigationReviewData = extractedInfo.mitigations;
          
          // Also get form details if available
          if (extractedInfo.risk_form_details) {
            const d = extractedInfo.risk_form_details;
            this.formDetails = {
              cost: String(d.cost ?? ''),
              costCurrency: d.costCurrency ?? 'USD',
              impact: String(d.impact ?? ''),
              financialImpact: String(d.financialImpact ?? d.financialimpact ?? ''),
              reputationalImpact: String(d.reputationalImpact ?? d.reputationalimpact ?? ''),
              operationalImpact: String(d.operationalImpact ?? d.operationalimpact ?? ''),
              financialLoss: String(d.financialLoss ?? d.financialloss ?? ''),
              financialLossCurrency: d.financialLossCurrency ?? 'USD',
              systemDowntime: String(d.systemDowntime ?? d.expecteddowntime ?? ''),
              recoveryTime: String(d.recoveryTime ?? d.recoverytime ?? ''),
              recurrencePossible: d.recurrencePossible ?? d.riskrecurrence ?? '',
              improvementInitiative: d.improvementInitiative ?? d.improvementinitiative ?? '',
              approved: d.approved,
              remarks: d.remarks || '',
              user_submitted_date: d.user_submitted_date || extractedInfo.user_submitted_date,
              reviewer_submitted_date: d.reviewer_submitted_date
            };
          } else {
            // Reset form details to empty
            this.formDetails = {
              cost: '',
              costCurrency: 'USD',
              impact: '',
              financialImpact: '',
              reputationalImpact: '',
              operationalImpact: '',
              financialLoss: '',
              financialLossCurrency: 'USD',
              systemDowntime: '',
              recoveryTime: '',
              recurrencePossible: '',
              improvementInitiative: '',
              approved: undefined,
              remarks: ''
            };
          }
          
          // Get previous versions from the task data that now includes it
          if (task.PreviousVersion && task.PreviousVersion.mitigations) {
            this.previousVersions = task.PreviousVersion.mitigations;
            
            // If there are previous form details, save them for comparison
            if (task.PreviousVersion.risk_form_details) {
              this.previousFormDetails = task.PreviousVersion.risk_form_details;
            }
          }
          
          // Add task status info for completed tasks
          const isCompleted = task.RiskStatus === 'Approved' || task.RiskStatus === 'Revision Required';
          this.reviewCompleted = isCompleted;
          this.reviewApproved = task.RiskStatus === 'Approved';
          
          // Fetch all versions for this risk
          await this.fetchAllVersions();
          
          this.loadingMitigations = false;
        } else {
          this.mitigationReviewData = {};
          console.error('No mitigations found in ExtractedInfo');
          this.loadingMitigations = false;
        }
      } catch (error) {
        console.error('Error parsing ExtractedInfo:', error);
        this.mitigationReviewData = {};
        this.loadingMitigations = false;
      }
    },
    approveQuestionnaire(approved) {
      // Update approval status
      this.formDetails.approved = approved;
      
      // Add timestamp for reviewer
      this.formDetails.reviewer_submitted_date = new Date().toISOString();
      
      // If rejecting, ensure there's a remarks field
      if (!approved && !this.formDetails.remarks) {
        this.formDetails.remarks = '';
      }
      
      // If approving, clear any remarks
      if (approved) {
        this.formDetails.remarks = '';
      }
    },
    saveQuestionnaireRemarks() {
      // Validate that remarks are provided when rejecting
      if (this.formDetails.approved === false && !this.formDetails.remarks.trim()) {
        // Send push notification for missing questionnaire feedback
        this.sendPushNotification({
          title: 'Missing Questionnaire Feedback',
          message: `Please provide feedback for the questionnaire in risk ${this.currentReviewTask?.RiskInstanceId || this.selectedRiskId}.`,
          category: 'risk',
          priority: 'medium',
          user_id: this.selectedUserId || 'default_user'
        });
        PopupService.warning('Please provide feedback for the questionnaire', 'Missing Feedback');
        return;
      }
      // Send push notification for questionnaire feedback saved
      this.sendPushNotification({
        title: 'Questionnaire Feedback Saved',
        message: `Questionnaire feedback has been saved for risk ${this.currentReviewTask?.RiskInstanceId || this.selectedRiskId}.`,
        category: 'risk',
        priority: 'medium',
        user_id: this.selectedUserId || 'default_user'
      });
      
      // Show confirmation to the user
      PopupService.success('Questionnaire feedback saved', 'Success');
    },
    // Format date and time
    formatDateTime(dateString) {
      if (!dateString) return 'N/A';
      try {
        const date = new Date(dateString);
        return date.toLocaleString();
      } catch (error) {
        return 'Invalid Date';
      }
    },
    // Extract submission date from task
    getSubmissionDate(task) {
      try {
        if (task.ExtractedInfo) {
          const extractedInfo = JSON.parse(task.ExtractedInfo);
          return extractedInfo.user_submitted_date || extractedInfo.submission_date;
        }
      } catch (error) {
        console.error('Error parsing submission date:', error);
      }
      return null;
    },
    getPreviousMitigation(id) {
      // Check if we have previous versions stored
      if (!this.previousVersions || !this.previousVersions[id]) {
        return null;
      }
      return this.previousVersions[id];
    },
    getPreviousFormDetail(field) {
      if (!this.previousFormDetails) {
        return null;
      }
      return this.previousFormDetails[field] || 'Not specified';
    },
    // Add this method to check if form field has changed
    hasFormFieldChanged(field) {
      if (!this.previousFormDetails) {
        return false;
      }
      
      const prevValue = this.previousFormDetails[field] || '';
      const currentValue = this.formDetails[field] || '';
      
      // For cost and financialLoss fields, also check currency changes
      if (field === 'cost') {
        const prevCurrency = this.previousFormDetails.costCurrency || 'USD';
        const currentCurrency = this.formDetails.costCurrency || 'USD';
        return prevValue !== currentValue || prevCurrency !== currentCurrency;
      }
      
      if (field === 'financialLoss') {
        const prevCurrency = this.previousFormDetails.financialLossCurrency || 'USD';
        const currentCurrency = this.formDetails.financialLossCurrency || 'USD';
        return prevValue !== currentValue || prevCurrency !== currentCurrency;
      }
      
      return prevValue !== currentValue;
    },
    getFieldLabel(field) {
      const labels = {
        'cost': 'Cost for Mitigation',
        'impact': 'Impact for Mitigation',
        'financialImpact': 'Financial Impact',
        'reputationalImpact': 'Reputational Impact'
      };
      return labels[field] || field;
    },
    fetchQuestionnaire(riskInstanceId) {
              axios.get(API_ENDPOINTS.RISK_INSTANCE(riskInstanceId))
        .then(response => {
          let details = response.data.RiskFormDetails;
          if (typeof details === 'string') {
            try { details = JSON.parse(details); } catch { details = {}; }
          }
          this.questionnaireDetails = this.mapRiskFormDetails(details);
          this.showQuestionnaire = true;
        });
    },
    mapRiskFormDetails(details) {
      if (!details) return {
        cost: '', costCurrency: 'USD', impact: '', financialImpact: '', reputationalImpact: '', operationalImpact: '', financialLoss: '', financialLossCurrency: 'USD', systemDowntime: '', recoveryTime: '', recurrencePossible: '', improvementInitiative: ''
      };
      function normalizeYN(val) {
        if (!val) return '';
        if (typeof val === 'string') {
          if (val.toLowerCase() === 'yes') return 'Yes';
          if (val.toLowerCase() === 'no') return 'No';
          if (val.toLowerCase() === 'unknown') return 'Unknown';
        }
        return val;
      }
      return {
        cost: details.cost ?? '',
        costCurrency: details.costCurrency ?? 'USD',
        impact: details.impact ?? '',
        financialImpact: details.financialImpact ?? details.financialimpact ?? '',
        reputationalImpact: details.reputationalImpact ?? details.reputationalimpact ?? '',
        operationalImpact: details.operationalImpact ?? details.operationalimpact ?? '',
        financialLoss: details.financialLoss ?? details.financialloss ?? '',
        financialLossCurrency: details.financialLossCurrency ?? 'USD',
        systemDowntime: details.systemDowntime ?? details.expecteddowntime ?? '',
        recoveryTime: details.recoveryTime ?? details.recoverytime ?? '',
        recurrencePossible: normalizeYN(details.recurrencePossible ?? details.riskrecurrence),
        improvementInitiative: normalizeYN(details.improvementInitiative ?? details.improvementinitiative)
      };
    },
    navigateTo(screen) {
      // Remove active class from all buttons
      const buttons = document.querySelectorAll('.toggle-button');
      buttons.forEach(button => button.classList.remove('active'));
      
      // Add active class to the clicked button
      const clickedButton = Array.from(buttons).find(button => 
        button.textContent.trim().toLowerCase().includes(screen)
      );
      if (clickedButton) clickedButton.classList.add('active');
      
      // Navigate to the appropriate screen
      switch(screen) {
        case 'resolution':
          this.$router.push('/risk/resolution');
          break;
        case 'workflow':
          // Already on workflow page
          break;
      }
    },
    
    // Helper methods for evidence display
    async showLinkedEventDetails(linkedEvent) {
      if (linkedEvent) {
        try {
          // For Document Handling System events, fetch from file operations
          if (linkedEvent.source === 'Document Handling System') {
            const response = await axios.get('/api/file-operations/');
            
            if (response.data && response.data.success && response.data.events) {
              const fileOperations = response.data.events;
              
              // Find the matching file operation
              const matchingOperation = fileOperations.find(op => {
                return op.linkedRecordId === linkedEvent.linkedRecordId ||
                       op.title === linkedEvent.title ||
                       (op.file_data && op.file_data.stored_name === linkedEvent.linkedRecordName) ||
                       (op.linkedRecordName === linkedEvent.linkedRecordName) ||
                       (op.file_data && op.file_data.original_name === linkedEvent.linkedRecordName);
              });
              
              if (matchingOperation && matchingOperation.file_data) {
                console.log('Found matching file operation with S3 URL:', matchingOperation.file_data.s3_url);
                
                // Create documents array from file operation data
                const documents = [{
                  filename: matchingOperation.file_data.original_name || matchingOperation.file_data.file_name,
                  source: 'Document Handling System',
                  file_size: matchingOperation.file_data.file_size,
                  s3_url: matchingOperation.file_data.s3_url,
                  downloadable: !!matchingOperation.file_data.s3_url
                }];
                
                // Update the linkedEvent with document data
                linkedEvent.documents = documents;
                linkedEvent.document_count = documents.length;
                
                // Force Vue reactivity update
                this.$forceUpdate();
                
                PopupService.success(`Document loaded successfully! ${documents.length} document(s) are now available for download.`);
              } else {
                PopupService.info('No file operation data found for this linked event.');
              }
            } else {
              PopupService.warning('Unable to fetch file operations data.');
            }
          } else {
            // For other types of linked events, try the incident approach
            const riskInstanceResponse = await axios.get(API_ENDPOINTS.RISK_INSTANCE(this.selectedRiskId));
            
            if (riskInstanceResponse.data && riskInstanceResponse.data.IncidentId) {
              const incidentId = riskInstanceResponse.data.IncidentId;
              const response = await axios.get(`/api/incidents/${incidentId}/linked-evidence/`);
              
              if (response.data && response.data.success && response.data.linked_evidence) {
                const enhancedLinkedEvidence = response.data.linked_evidence;
                
                const matchingEvidence = enhancedLinkedEvidence.find(evidence => {
                  return evidence.id === linkedEvent.id || 
                         evidence.title === linkedEvent.title ||
                         (evidence.linkedRecordId && linkedEvent.linkedRecordId && 
                          evidence.linkedRecordId.toString() === linkedEvent.linkedRecordId.toString());
                });
                
                if (matchingEvidence && matchingEvidence.documents && matchingEvidence.documents.length > 0) {
                  linkedEvent.documents = matchingEvidence.documents;
                  linkedEvent.document_count = matchingEvidence.documents.length;
                  this.$forceUpdate();
                  PopupService.success(`Documents loaded successfully! ${matchingEvidence.documents.length} document(s) are now available for download.`);
                } else {
                  PopupService.info('No additional documents found for this linked event.');
                }
              } else {
                PopupService.warning('Unable to fetch document details. Please try refreshing.');
              }
            } else {
              PopupService.warning('Unable to find associated incident for this risk.');
            }
          }
        } catch (error) {
          PopupService.error('Error loading documents. Please try again.');
        }
      }
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    downloadLinkedDocument(evidenceId, documentIndex, docData) {
      try {
        // If document has direct s3_url, use that (for Document Handling System files)
        if (docData && docData.s3_url) {
          console.log('Opening S3 file:', docData.filename, 'URL:', docData.s3_url);
          
          // Open the file in a new tab (browser will decide whether to view or download)
          const link = document.createElement('a');
          link.href = docData.s3_url;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          // Don't set download attribute - let browser decide based on file type
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          return;
        }
        
        // For Document Handling System files, try to get the S3 URL from file operations
        if (docData && docData.source === 'Document Handling System') {
          axios.get('/api/file-operations/')
            .then(response => {
              if (response.data && response.data.success && response.data.events) {
                const fileOperations = response.data.events;
                const matchingOperation = fileOperations.find(op => {
                  return op.linkedRecordId === evidenceId ||
                         (op.file_data && op.file_data.original_name === docData.filename);
                });
                
                if (matchingOperation && matchingOperation.file_data && matchingOperation.file_data.s3_url) {
                  console.log('Opening file from operations:', docData.filename, 'URL:', matchingOperation.file_data.s3_url);
                  const link = document.createElement('a');
                  link.href = matchingOperation.file_data.s3_url;
                  link.target = '_blank';
                  link.rel = 'noopener noreferrer';
                  // Don't set download attribute - let browser decide based on file type
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                } else {
                  alert('File not available for download');
                }
              } else {
                alert('Unable to fetch file operations data');
              }
            })
            .catch(error => {
              console.error('Error fetching file operations:', error);
              alert('Failed to download document');
            });
          return;
        }
        
        // For other types of evidence, use the incident approach
        const userId = localStorage.getItem('user_id') || '1';
        
        axios.get(API_ENDPOINTS.RISK_INSTANCE(this.selectedRiskId))
          .then(riskInstanceResponse => {
            if (riskInstanceResponse.data && riskInstanceResponse.data.IncidentId) {
              const incidentId = riskInstanceResponse.data.IncidentId;
              
              // Create download URL using the incident ID
              const downloadUrl = `/api/incidents/${incidentId}/linked-evidence/${evidenceId}/documents/${documentIndex}/download/?user_id=${userId}`;
              
              // Create a temporary link and click it to trigger download
              const link = document.createElement('a');
              link.href = downloadUrl;
              link.target = '_blank';
              link.rel = 'noopener noreferrer';
              // Don't set download attribute - let browser decide based on file type
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
            } else {
              alert('Unable to find associated incident for download');
            }
          })
          .catch(error => {
            console.error('Error getting incident ID:', error);
            alert('Failed to download document');
          });
        
      } catch (error) {
        console.error('Download error:', error);
        // Safe error handling
        try {
          if (this.$toast && this.$toast.error) {
            this.$toast.error('Failed to download document');
          } else {
            alert('Failed to download document: ' + (error.message || 'Unknown error'));
          }
        } catch (toastError) {
          alert('Failed to download document');
        }
      }
    },
    
    refreshLinkedEvidence() {
      // Clear any existing test data from linked events
      this.mitigationSteps.forEach(step => {
        if (step.files && step.files.length > 0) {
          step.files.forEach(file => {
            if (file.type === 'linked_evidence' && file.linkedEvent && file.linkedEvent.source === 'Document Handling System') {
              // Reset documents to empty to get fresh data from backend
              file.linkedEvent.documents = [];
              file.linkedEvent.document_count = 0;
            }
          });
        }
      });
      
      // Also clear from mitigation review data
      Object.values(this.mitigationReviewData).forEach(mitigation => {
        if (mitigation.files && mitigation.files.length > 0) {
          mitigation.files.forEach(file => {
            if (file.type === 'linked_evidence' && file.linkedEvent && file.linkedEvent.source === 'Document Handling System') {
              file.linkedEvent.documents = [];
              file.linkedEvent.document_count = 0;
            }
          });
        }
      });
      
      // Fetch fresh data from backend
      this.fetchLinkedEvidenceDocuments();
    },
    
    async fetchLinkedEvidenceDocuments() {
      if (!this.selectedRiskId) return;
      
      try {
        // Fetch file operations for Document Handling System events
        const fileOpsResponse = await axios.get('/api/file-operations/');
        
        if (fileOpsResponse.data && fileOpsResponse.data.success && fileOpsResponse.data.events) {
          const fileOperations = fileOpsResponse.data.events;
          
          // Update mitigation steps with file operation data
          this.mitigationSteps.forEach(step => {
            if (step.files && step.files.length > 0) {
              step.files.forEach(file => {
                if (file.type === 'linked_evidence' && file.linkedEvent && file.linkedEvent.source === 'Document Handling System') {
                  const matchingOperation = fileOperations.find(op => {
                    return op.linkedRecordId === file.linkedEvent.linkedRecordId ||
                           op.title === file.linkedEvent.title ||
                           (op.file_data && op.file_data.stored_name === file.linkedEvent.linkedRecordName) ||
                           (op.linkedRecordName === file.linkedEvent.linkedRecordName);
                  });
                  
                  if (matchingOperation && matchingOperation.file_data) {
                    const documents = [{
                      filename: matchingOperation.file_data.original_name || matchingOperation.file_data.file_name,
                      source: 'Document Handling System',
                      file_size: matchingOperation.file_data.file_size,
                      s3_url: matchingOperation.file_data.s3_url,
                      downloadable: !!matchingOperation.file_data.s3_url
                    }];
                    
                    file.linkedEvent.documents = documents;
                    file.linkedEvent.document_count = documents.length;
                  }
                }
              });
            }
          });
          
          // Update mitigation review data as well
          Object.values(this.mitigationReviewData).forEach(mitigation => {
            if (mitigation.files && mitigation.files.length > 0) {
              mitigation.files.forEach(file => {
                if (file.type === 'linked_evidence' && file.linkedEvent && file.linkedEvent.source === 'Document Handling System') {
                  const matchingOperation = fileOperations.find(op => {
                    return op.linkedRecordId === file.linkedEvent.linkedRecordId ||
                           op.title === file.linkedEvent.title ||
                           (op.file_data && op.file_data.stored_name === file.linkedEvent.linkedRecordName) ||
                           (op.linkedRecordName === file.linkedEvent.linkedRecordName);
                  });
                  
                  if (matchingOperation && matchingOperation.file_data) {
                    const documents = [{
                      filename: matchingOperation.file_data.original_name || matchingOperation.file_data.file_name,
                      source: 'Document Handling System',
                      file_size: matchingOperation.file_data.file_size,
                      s3_url: matchingOperation.file_data.s3_url,
                      downloadable: !!matchingOperation.file_data.s3_url
                    }];
                    
                    file.linkedEvent.documents = documents;
                    file.linkedEvent.document_count = documents.length;
                  }
                }
              });
            }
          });
          
          // Force Vue reactivity update
          this.$forceUpdate();
        }
        
        // Also try incident approach for non-Document Handling System events
        const riskInstanceResponse = await axios.get(API_ENDPOINTS.RISK_INSTANCE(this.selectedRiskId));
        
        if (riskInstanceResponse.data && riskInstanceResponse.data.IncidentId) {
          const incidentId = riskInstanceResponse.data.IncidentId;
          const response = await axios.get(`/api/incidents/${incidentId}/linked-evidence/`);
          
          if (response.data && response.data.success && response.data.linked_evidence) {
            const enhancedLinkedEvidence = response.data.linked_evidence;
            
            // Update non-Document Handling System events
            this.mitigationSteps.forEach(step => {
              if (step.files && step.files.length > 0) {
                step.files.forEach(file => {
                  if (file.type === 'linked_evidence' && file.linkedEvent && file.linkedEvent.source !== 'Document Handling System') {
                    const matchingEvidence = enhancedLinkedEvidence.find(evidence => {
                      return evidence.id === file.linkedEvent.id || 
                             evidence.title === file.linkedEvent.title ||
                             (evidence.linkedRecordId && file.linkedEvent.linkedRecordId && 
                              evidence.linkedRecordId.toString() === file.linkedEvent.linkedRecordId.toString());
                    });
                    
                    if (matchingEvidence && matchingEvidence.documents && matchingEvidence.documents.length > 0) {
                      file.linkedEvent.documents = matchingEvidence.documents;
                      file.linkedEvent.document_count = matchingEvidence.documents.length;
                    }
                  }
                });
              }
            });
          }
        }
      } catch (error) {
        // Error fetching enhanced linked evidence
      }
    },
    // New methods for version management
    async onGlobalVersionChange() {
      // Apply the selected version to all mitigations
      console.log('Global version changed to:', this.globalSelectedVersion);
      
      if (!this.globalSelectedVersion) {
        console.log('No version selected, clearing selections');
        // Clear all selections
        this.selectedVersions = {};
        return;
      }
      
      // Show loading state
      this.loadingVersions = true;
      
      try {
        // Update all mitigation items with the selected version
        const riskId = this.currentReviewTask?.RiskInstanceId || this.selectedRiskId;
        
        // Fetch version details once for all mitigations
        console.log('Fetching version details for:', this.globalSelectedVersion);
        const { data: versionDetails } = await axios.get(API_ENDPOINTS.RISK_VERSION(riskId, this.globalSelectedVersion));
        console.log('Received version details:', versionDetails);
        
        if (versionDetails.success && versionDetails.version_data && versionDetails.version_data.ExtractedInfo) {
          let extractedInfo;
          try {
            extractedInfo = typeof versionDetails.version_data.ExtractedInfo === 'string' 
              ? JSON.parse(versionDetails.version_data.ExtractedInfo) 
              : versionDetails.version_data.ExtractedInfo;
          } catch (error) {
            console.error('Error parsing ExtractedInfo:', error);
            extractedInfo = { mitigations: {}, risk_form_details: {} };
          }
          
          // Process each mitigation
          Object.keys(this.mitigationReviewData).forEach(id => {
            // Update the selected version
            this.selectedVersions = {
              ...this.selectedVersions,
              [id]: this.globalSelectedVersion
            };
            
            // Get the mitigation data for this specific ID
            const mitigationData = extractedInfo.mitigations?.[id] || {};
            
            // Extract reviewer feedback from remarks or other fields
            let reviewerFeedback = '';
            
            // Check for remarks field first
            if (mitigationData.remarks) {
              reviewerFeedback = mitigationData.remarks;
            } 
            // Check for reviewer_feedback field if exists
            else if (mitigationData.reviewer_feedback) {
              reviewerFeedback = mitigationData.reviewer_feedback;
            }
            // Check if there's feedback in the version data itself
            else if (versionDetails.version_data.ReviewerFeedback) {
              reviewerFeedback = versionDetails.version_data.ReviewerFeedback;
            }
            // Check if there's feedback in the ExtractedInfo
            else if (extractedInfo.reviewer_feedback) {
              reviewerFeedback = extractedInfo.reviewer_feedback;
            }
            
            // Store the version data
            const versionKey = `${id}_${this.globalSelectedVersion}`;
            this.versionData = {
              ...this.versionData,
              [versionKey]: {
                ...mitigationData,
                version: this.globalSelectedVersion,
                RiskInstanceId: versionDetails.version_data.RiskInstanceId,
                UserId: versionDetails.version_data.UserId,
                ApproverId: versionDetails.version_data.ApproverId,
                Date: versionDetails.version_data.Date,
                formatted_date: versionDetails.version_data.formatted_date,
                approved: versionDetails.version_data.ApprovedRejected === 'Approved' ? true : 
                         versionDetails.version_data.ApprovedRejected === 'Rejected' ? false : undefined,
                reviewer_feedback: reviewerFeedback
              }
            };
          });
          
          console.log('Updated version data for all mitigations');
        }
      } catch (error) {
        console.error('Error in global version change:', error);
        // Send push notification for version loading error
        this.sendPushNotification({
          title: 'Version Data Loading Failed',
          message: `Failed to load version data for risk ${this.currentReviewTask?.RiskInstanceId || this.selectedRiskId}. Please try again.`,
          category: 'risk',
          priority: 'medium',
          user_id: this.selectedUserId || 'default_user'
        });
        PopupService.error('Failed to load version data. Please try again.', 'Version Loading Failed');
      } finally {
        this.loadingVersions = false;
      }
    },
    
    async fetchAllVersions() {
      // Only fetch versions for reviewer workflow, not for user mitigation workflow
      if (!this.showReviewerWorkflow) {
        console.log('Not in reviewer workflow, skipping version fetch');
        return;
      }
      
      const riskId = this.currentReviewTask?.RiskInstanceId || this.selectedRiskId;
      
      if (!riskId) {
        console.log('No risk ID available for fetching versions');
        return;
      }
      
      console.log(`\n=== FETCHING ALL VERSIONS ===`);
      console.log(`Risk ID: ${riskId}`);
      console.log(`API URL: ${API_ENDPOINTS.RISK_VERSIONS(riskId)}`);
      console.log(`Current mitigation review data keys:`, Object.keys(this.mitigationReviewData));
      
      this.loadingVersions = true;
      
      try {
        console.log('Making API call...');
        const { data: responseData } = await axios.get(API_ENDPOINTS.RISK_VERSIONS(riskId));
        console.log(`Full API Response:`, responseData);
        console.log(`Response type:`, typeof responseData);
        console.log(`Response keys:`, Object.keys(responseData || {}));
        
        // Handle the response structure properly
        const versions = responseData.versions || responseData || [];
        console.log(`Extracted versions:`, versions);
        console.log(`Total versions received:`, versions.length);
        console.log(`Versions array type:`, Array.isArray(versions));
        
        // Extract version names directly from the response if available
        if (responseData.version_names && Array.isArray(responseData.version_names)) {
          // Filter only R versions
          this.allVersionNames = responseData.version_names.filter(version => 
            version && version.toString().startsWith('R')
          );
          console.log(`Using filtered R version_names from API response:`, this.allVersionNames);
        } else {
          // Fall back to extracting from versions array
          this.allVersionNames = versions
            .map(v => v.version)
            .filter(version => version && version.toString().startsWith('R'));
          console.log(`Extracted filtered R version names from versions array:`, this.allVersionNames);
        }
        
        if (versions && versions.length > 0) {
          this.allVersions = versions;
          console.log(`Set allVersions to:`, this.allVersions);
          
          // Log details for each version
          versions.forEach((version, index) => {
            console.log(`Version ${index + 1}:`, {
              version: version.version,
              RiskInstanceId: version.RiskInstanceId,
              UserId: version.UserId,
              ApproverId: version.ApproverId,
              Date: version.Date,
              ApprovedRejected: version.ApprovedRejected,
              mitigationCount: version.mitigations ? Object.keys(version.mitigations).length : 0,
              formDetailsCount: version.risk_form_details ? Object.keys(version.risk_form_details).length : 0
            });
          });
          
          // Initialize selectedVersions for each mitigation (don't auto-select any version)
          Object.keys(this.mitigationReviewData).forEach(mitigationId => {
            if (!this.selectedVersions[mitigationId]) {
              // Replace this.$set with direct assignment
              this.selectedVersions = {
                ...this.selectedVersions,
                [mitigationId]: ''
              };
            }
          });
          
          console.log('Final selectedVersions state:', this.selectedVersions);
          console.log('Final allVersions length:', this.allVersions.length);
          console.log('Final allVersionNames:', this.allVersionNames);
          
        } else {
          console.log('No versions found or empty array');
          console.log('Setting allVersions to empty array');
          this.allVersions = [];
          this.allVersionNames = [];
        }
        
      } catch (error) {
        console.error('ERROR fetching versions:', error);
        console.error('Error type:', error.constructor.name);
        console.error('Error message:', error.message);
        console.error('Error stack:', error.stack);
        if (error.response) {
          console.error('Response data:', error.response.data);
          console.error('Response status:', error.response.status);
        }
        this.allVersions = [];
        this.allVersionNames = [];
      } finally {
        this.loadingVersions = false;
        console.log('fetchAllVersions completed. Final allVersions length:', this.allVersions.length);
        console.log('Final allVersionNames:', this.allVersionNames);
      }
    },
    async fetchVersionDetails(riskId, version) {
      console.log(`\n=== FETCH VERSION DETAILS ===`);
      console.log(`Risk ID: ${riskId}`);
      console.log(`Version: ${version}`);
      
      try {
        const response = await axios.get(API_ENDPOINTS.RISK_VERSION(riskId, version));
        console.log('API Response:', response.data);
        
        if (response.data.success) {
          console.log('Version data successfully retrieved');
          console.log('Version data keys:', Object.keys(response.data.version_data));
          
          if (response.data.version_data.ExtractedInfo) {
            console.log('ExtractedInfo keys:', Object.keys(response.data.version_data.ExtractedInfo));
            if (response.data.version_data.ExtractedInfo.mitigations) {
              console.log('Available mitigations:', Object.keys(response.data.version_data.ExtractedInfo.mitigations));
            }
          }
          
          return response.data.version_data.ExtractedInfo || response.data.version_data;
        } else {
          console.log('API returned success: false');
          return null;
        }
      } catch (error) {
        console.error(`Error fetching version ${version}:`, error);
        console.error('Error response:', error.response?.data);
        return null;
      }
    },
    async onVersionChange(mitigationId, selectedVersion) {
      console.log('Version changed for mitigation:', mitigationId, 'to version:', selectedVersion);
      
      if (!selectedVersion) {
        console.log('No version selected, clearing data');
        return;
      }
      
      // Check if we already have the data for this version
      const versionKey = `${mitigationId}_${selectedVersion}`;
      if (this.versionData[versionKey]) {
        console.log('Version data already loaded for:', versionKey);
        return;
      }
      
      try {
        const riskId = this.currentReviewTask?.RiskInstanceId || this.selectedRiskId;
        console.log('Fetching version details for:', selectedVersion, 'with risk ID:', riskId);
        const { data: versionDetails } = await axios.get(API_ENDPOINTS.RISK_VERSION(riskId, selectedVersion));
        console.log('Received version details:', versionDetails);
        
        // Parse the version data and store it
        if (versionDetails.success && versionDetails.version_data && versionDetails.version_data.ExtractedInfo) {
          let extractedInfo;
          try {
            extractedInfo = typeof versionDetails.version_data.ExtractedInfo === 'string' 
              ? JSON.parse(versionDetails.version_data.ExtractedInfo) 
              : versionDetails.version_data.ExtractedInfo;
          } catch (error) {
            console.error('Error parsing ExtractedInfo:', error);
            extractedInfo = { mitigations: {}, risk_form_details: {} };
          }
          
          // Find the mitigation data for this specific mitigation ID
          const mitigationData = extractedInfo.mitigations[mitigationId] || {};
          console.log('Mitigation data for', mitigationId, ':', mitigationData);
          
          // Extract reviewer feedback from remarks or other fields
          let reviewerFeedback = '';
          
          // Check for remarks field first
          if (mitigationData.remarks) {
            reviewerFeedback = mitigationData.remarks;
          } 
          // Check for reviewer_feedback field if exists
          else if (mitigationData.reviewer_feedback) {
            reviewerFeedback = mitigationData.reviewer_feedback;
          }
          // Check if there's feedback in the version data itself
          else if (versionDetails.version_data.ReviewerFeedback) {
            reviewerFeedback = versionDetails.version_data.ReviewerFeedback;
          }
          // Check if there's feedback in the ExtractedInfo
          else if (extractedInfo.reviewer_feedback) {
            reviewerFeedback = extractedInfo.reviewer_feedback;
          }
          
          console.log('Extracted reviewer feedback:', reviewerFeedback);
          
          // Store the version data using the correct field names
          this.versionData = {
            ...this.versionData,
            [versionKey]: {
              ...mitigationData,
              version: selectedVersion,
              RiskInstanceId: versionDetails.version_data.RiskInstanceId,
              UserId: versionDetails.version_data.UserId,
              ApproverId: versionDetails.version_data.ApproverId,
              Date: versionDetails.version_data.Date,
              formatted_date: versionDetails.version_data.formatted_date,
              approved: versionDetails.version_data.ApprovedRejected === 'Approved' ? true : 
                       versionDetails.version_data.ApprovedRejected === 'Rejected' ? false : undefined,
              reviewer_feedback: reviewerFeedback
            }
          };
          
          console.log('Stored version data:', this.versionData[versionKey]);
        }
        
      } catch (error) {
        console.error('Error fetching version details:', error);
        // Show user-friendly error message if toast is available
        if (this.$toast) {
          this.$toast.error('Failed to load version details. Please try again.');
        } else {
          console.error('Failed to load version details. Please try again.');
        }
      }
    },
    getVersionDisplayData(mitigationId, selectedVersion) {
      if (selectedVersion === 'current') {
        return this.mitigationReviewData[mitigationId];
      }
      return this.versionData[`${mitigationId}_${selectedVersion}`] || {};
    },
    getVersionOptions() {
      const options = [{ value: 'current', label: 'Current Version' }];
      
      // Add all available versions (excluding the current one)
      this.allVersions.forEach(version => {
        if (version.version !== this.currentReviewTask?.version) {
          options.push({
            value: version.version,
            label: `Version ${version.version} (${this.formatDateTime(version.formatted_date)})`
          });
        }
      });
      
      return options;
    },
    getAllVersionsExceptCurrent() {
      if (!this.allVersions || this.allVersions.length === 0) {
        return [];
      }
      
      // Get the current version from the review task
      let currentVersion = null;
      
      // Try to determine current version from the review task
      if (this.currentReviewTask && this.currentReviewTask.ExtractedInfo) {
        try {
          const extractedInfo = typeof this.currentReviewTask.ExtractedInfo === 'string' 
            ? JSON.parse(this.currentReviewTask.ExtractedInfo)
            : this.currentReviewTask.ExtractedInfo;
          
          if (extractedInfo.version) {
            currentVersion = extractedInfo.version;
          }
        } catch (error) {
          console.error('Error parsing current task ExtractedInfo:', error);
        }
      }
      
      // If we couldn't determine the current version, assume it's the latest one
      if (!currentVersion && this.allVersions.length > 0) {
        // Sort versions and take the latest
        const sortedVersions = [...this.allVersions].sort((a, b) => {
          // Extract numeric part from version (e.g., "R1" -> 1, "U2" -> 2)
          const getVersionNumber = (version) => {
            const match = version.match(/\d+/);
            return match ? parseInt(match[0]) : 0;
          };
          return getVersionNumber(b.version) - getVersionNumber(a.version);
        });
        currentVersion = sortedVersions[0].version;
      }
      
      console.log('Current version identified as:', currentVersion);
      console.log('All versions:', this.allVersions.map(v => v.version));
      
      // Filter out the current version
      const filteredVersions = this.allVersions.filter(version => version.version !== currentVersion);
      console.log('Filtered versions (excluding current):', filteredVersions.map(v => v.version));
      
      return filteredVersions;
    },
    getSelectedVersionData(id, selectedVersion) {
      return this.versionData[`${id}_${selectedVersion}`] || {};
    },
    getCurrentVersionLabel() {
      if (!this.allVersions || this.allVersions.length === 0) {
        return 'Current';
      }
      
      // Get the current version from the review task
      let currentVersion = null;
      
      // Try to determine current version from the review task
      if (this.currentReviewTask && this.currentReviewTask.ExtractedInfo) {
        try {
          const extractedInfo = typeof this.currentReviewTask.ExtractedInfo === 'string' 
            ? JSON.parse(this.currentReviewTask.ExtractedInfo)
            : this.currentReviewTask.ExtractedInfo;
          
          if (extractedInfo.version) {
            currentVersion = extractedInfo.version;
          }
        } catch (error) {
          console.error('Error parsing current task ExtractedInfo:', error);
        }
      }
      
      // If we couldn't determine the current version, assume it's the latest one
      if (!currentVersion && this.allVersions.length > 0) {
        // Sort versions and take the latest
        const sortedVersions = [...this.allVersions].sort((a, b) => {
          // Extract numeric part from version (e.g., "R1" -> 1, "U2" -> 2)
          const getVersionNumber = (version) => {
            const match = version.match(/\d+/);
            return match ? parseInt(match[0]) : 0;
          };
          return getVersionNumber(b.version) - getVersionNumber(a.version);
        });
        currentVersion = sortedVersions[0].version;
      }
      
      // Find the current version data
      const currentVersionData = this.allVersions.find(version => version.version === currentVersion);
      
      if (currentVersionData && currentVersionData.formatted_date) {
        return `Version ${currentVersion} (${this.formatDateTime(currentVersionData.formatted_date)})`;
      } else if (currentVersionData && currentVersionData.Date) {
        return `Version ${currentVersion} (${this.formatDateTime(currentVersionData.Date)})`;
      } else {
        return `Version ${currentVersion || 'Current'}`;
      }
    },
    getVersionStatus(version) {
      // Determine status based on version data
      if (version.ApprovedRejected === 'Approved') {
        return 'Approved';
      } else if (version.ApprovedRejected === 'Rejected') {
        return 'Rejected';
      } else if (version.approved === true) {
        return 'Approved';
      } else if (version.approved === false) {
        return 'Rejected';
      } else {
        return 'Pending';
      }
    },
  }
}
</script>

<style scoped>
@import './RiskWorkflow.css';
.risk-workflow-data-source {
  margin: 0 0 12px 0;
  font-size: 0.85rem;
  color: #2563eb;
  font-weight: 600;
}

/* Add additional styles for the section title */
.section-title {
  margin: 20px 0;
  color: #333;
  font-size: 1.8rem;
  font-weight: 600;
  text-align: center;
}

/* Enhance the toggle buttons styling */
.toggle-buttons {
  display: flex;
  background: #f8f9fa;
  border-radius: 50px;
  overflow: hidden;
  width: fit-content;
  border: 1px solid #e0e0e0;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
  margin: 30px auto;
}

.toggle-button {
  padding: 12px 30px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  color: #555;
  transition: all 0.3s ease;
  position: relative;
  outline: none;
  min-width: 180px;
  text-align: center;
}

.toggle-button:not(:last-child) {
  border-right: 1px solid #eee;
}

.toggle-button:hover {
  background-color: rgba(52, 152, 219, 0.1);
  color: #3498db;
}

.toggle-button.active {
  background: linear-gradient(135deg, #3498db, #2980b9);
  color: white;
  box-shadow: 0 2px 10px rgba(52, 152, 219, 0.3);
}

/* Update due status styling to be more visible */
.due-status {
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
  display: inline-block;
}

.due-status.overdue {
  background-color: #fff1f0;
  color: #f5222d;
  border: 1px solid #ffa39e;
}

.due-status.urgent {
  background-color: #fff7e6;
  color: #fa8c16;
  border: 1px solid #ffd591;
}

.due-status.warning {
  background-color: #fffbe6;
  color: #faad14;
  border: 1px solid #ffe58f;
}

.due-status.on-track {
  background-color: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.mitigation-status {
  margin-left: 10px;
  font-size: 12px;
  color: #606266;
  padding: 2px 8px;
  background-color: #f5f5f5;
  border-radius: 10px;
}

/* Add styles for mitigation status badges */
.mitigation-status.status-completed {
  background-color: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.mitigation-status.status-progress {
  background-color: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
}

.mitigation-status.status-revision {
  background-color: #fff1f0;
  color: #f5222d;
  border: 1px solid #ffa39e;
}

.mitigation-status.status-not-started {
  background-color: #f5f5f5;
  color: #8c8c8c;
  border: 1px solid #d9d9d9;
}

.complete-btn {
  background-color: #52c41a;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.complete-btn:hover {
  background-color: #73d13d;
}

/* Add these new styles for submission dates */
.submission-date {
  font-size: 12px;
  margin-top: 5px;
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  border-radius: 4px;
  width: fit-content;
}

.submission-date.user-date {
  background-color: #e6f7ff;
  color: #1890ff;
}

.submission-date.reviewer-date {
  background-color: #f6ffed;
  color: #52c41a;
}

.edit-questionnaire-section {
  margin-bottom: 20px;
}

.edit-questionnaire-btn {
  background-color: #4CAF50;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.edit-questionnaire-btn:hover {
  background-color: #45a049;
}

.edit-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-top: 5px;
}

.edit-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.save-changes-btn {
  background-color: #4CAF50;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.cancel-edit-btn {
  background-color: #f44336;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* Add these new styles for status badges */
.status-revision-user, .status-revision-reviewer, .status-approved, .status-review, .status-revision, .status-progress {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  display: inline-block;
  margin-right: 5px;
}

/* Add these new styles for status badges */
.status-revision-user {
  background-color: #fff2e8;
  color: #fa541c;
  border: 1px solid #ffbb96;
}

.status-revision-reviewer {
  background-color: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
}

.status-approved {
  background-color: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.status-review {
  background-color: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
}

.status-revision {
  background-color: #fff2e8;
  color: #fa541c;
  border: 1px solid #ffbb96;
}

.status-progress {
  background-color: #f4f4f5;
  color: #909399;
  border: 1px solid #d3d4d6;
}

/* Version dropdown styles */
.version-dropdown {
  margin-top: 8px;
  margin-bottom: 8px;
}

.version-select {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: white;
  font-size: 12px;
  color: #666;
  cursor: pointer;
}

.version-select:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.version-label {
  display: flex;
  flex-direction: column;
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
}

.version-label .version-dropdown {
  font-weight: normal;
}

/* Loading state for version dropdown */
.version-select:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
  opacity: 0.6;
}

/* Enhanced mitigation content styling for better version comparison */
.mitigation-content {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Version comparison highlighting */
.version-changed {
  background-color: #fff7e6;
  border-left: 3px solid #faad14;
  padding-left: 8px;
  margin-left: -8px;
}

.version-added {
  background-color: #f6ffed;
  border-left: 3px solid #52c41a;
  padding-left: 8px;
  margin-left: -8px;
}

.version-removed {
  background-color: #fff1f0;
  border-left: 3px solid #f5222d;
  padding-left: 8px;
  margin-left: -8px;
  opacity: 0.7;
}

/* Version comparison styles */
.version-dropdown {
  margin-top: 8px;
}

.version-select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: white;
  font-size: 14px;
  color: #333;
}

.version-select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.version-label {
  font-weight: 600;
  color: #495057;
  margin-bottom: 8px;
  font-size: 16px;
}

.metadata-section {
  margin: 16px 0;
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #007bff;
}

.metadata-item {
  display: flex;
  margin-bottom: 8px;
}

.metadata-item:last-child {
  margin-bottom: 0;
}

.metadata-label {
  font-weight: 600;
  min-width: 120px;
  color: #6c757d;
  font-size: 14px;
}

.metadata-value {
  color: #495057;
  font-size: 14px;
}

.comments-section, .evidence-section, .remarks-section {
  margin: 16px 0;
  padding: 12px;
  border-radius: 6px;
}

.comments-section {
  background-color: #e3f2fd;
  border-left: 4px solid #2196f3;
}

.evidence-section {
  background-color: #f3e5f5;
  border-left: 4px solid #9c27b0;
}

.remarks-section {
  background-color: #ffebee;
  border-left: 4px solid #f44336;
}

.comments-text, .remarks-text {
  margin: 8px 0 0 0;
  font-style: italic;
  color: #495057;
}

.evidence-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
  margin-top: 8px;
}

.evidence-link:hover {
  text-decoration: underline;
}

.decision-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 14px;
  margin: 16px 0;
}

.decision-tag.approved {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.decision-tag.rejected {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.mitigation-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #6c757d;
  text-align: center;
}

.mitigation-empty i {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.mitigation-empty p {
  margin: 0;
  font-style: italic;
}

.text-success {
  color: #28a745 !important;
}

.text-danger {
  color: #dc3545 !important;
}

.global-version-dropdown {
  margin: 0 0 20px 0;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
}

.global-version-dropdown label {
  font-weight: 600;
  color: #495057;
  min-width: 180px;
}

.global-version-select {
  flex: 1;
  min-width: 250px;
  padding: 10px 15px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  background-color: white;
  font-size: 14px;
  color: #495057;
  cursor: pointer;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.global-version-select:focus {
  outline: none;
  border-color: #80bdff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.global-version-select:disabled {
  background-color: #e9ecef;
  cursor: not-allowed;
}

/* Add loading indicator for version dropdown */
.global-version-dropdown.loading::after {
  content: "Loading...";
  margin-left: 10px;
  font-style: italic;
  color: #6c757d;
}

/* Add version badge styling */
.version-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  background-color: #e9ecef;
  color: #495057;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  margin-left: 10px;
}

.version-badge i {
  margin-right: 5px;
  font-size: 10px;
}

.no-versions-message {
  margin-left: 15px;
  color: #6c757d;
  font-style: italic;
  display: flex;
  align-items: center;
  gap: 8px;
}

.no-versions-message i {
  color: #17a2b8;
}

.reviewer-feedback-section {
  margin: 16px 0;
  padding: 12px;
  border-radius: 6px;
  background-color: #fff3e0;
  border-left: 4px solid #ff9800;
}

.reviewer-feedback-section h5 {
  color: #e65100;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.reviewer-feedback-section h5 i {
  font-size: 16px;
}

.reviewer-feedback-text {
  margin: 8px 0 0 0;
  font-style: italic;
  color: #5d4037;
  line-height: 1.5;
}

.risk-workflow-user-filter {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  width: 100%;
  margin-top:10px;
  padding-left: 5px;
  padding-top:10px;
}

.risk-workflow-user-filter :deep(.filter-btn) {
  min-width: 200px;
  width: auto;
  max-width: 250px;
}

.risk-workflow-user-filter :deep(.dropdown-menu) {
  min-width: 150px;
  width: auto;
  max-width: 200px;
}

/* Hide the label since it's already shown in the dropdown */
.risk-workflow-user-filter label {
  display: none;
}
</style>