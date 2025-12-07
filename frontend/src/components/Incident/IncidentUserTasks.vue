<template>
  <div class="incident-tasks-page">
    <div class="incident-content">
      <h1 class="incident-title">Incident Task Management</h1>

      <!-- User Filter -->
      <div class="user-filter-section">
        <CustomDropdown 
          v-model="selectedUserId"
          :config="userFilterConfig"
          @change="fetchData"
        />
      </div>

      <!-- Task Type Tabs -->
      <div class="task-type-tabs">
        <button 
          :class="['task-type-button', { active: activeTab === 'user' }]" 
          @click="activeTab = 'user'"
        >
          My Tasks
          <span class="task-count">{{ userIncidents.length }}</span>
        </button>
        <button 
          :class="['task-type-button', { active: activeTab === 'reviewer' }]" 
          @click="switchToReviewerTab"
        >
          Reviewer Tasks
          <span class="task-count">{{ reviewerTasks.length }}</span>
        </button>
      </div>

      <!-- Loading and Error States -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <span>Loading data...</span>
      </div>
      
      <div v-else-if="error" class="error-state">
        {{ error }}
      </div>

      <!-- User Tasks View -->
      <div v-else-if="activeTab === 'user' && !showMitigationWorkflow && !showReviewerWorkflow">
        <div v-if="!selectedUserId" class="no-data-state">
          <p>Please select a user to view their assigned tasks.</p>
        </div>
        <div v-else-if="userIncidents.length === 0" class="no-data-state">
          <p>No tasks assigned to this user.</p>
        </div>
        <div v-else>
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
      </div>

      <!-- Reviewer Tasks View -->
      <div v-else-if="activeTab === 'reviewer' && !showMitigationWorkflow && !showReviewerWorkflow">
        <div v-if="!selectedUserId" class="no-data-state">
          <p>Please select a user to view their reviewer tasks.</p>
        </div>
        <div v-else-if="reviewerTasks.length === 0" class="no-data-state">
          <p>No review tasks assigned to this user.</p>
        </div>
        <div v-else>
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
      </div>
    </div>

    <!-- Incident Mitigation Workflow -->
    <div v-if="showMitigationWorkflow" class="workflow-overlay">
      <div class="workflow-container">
        <!-- Back Button -->
        <div class="workflow-header">
          <button @click="closeMitigationModal" class="back-button">
            <i class="fas fa-arrow-left"></i>
            Back to Tasks
          </button>
          <h2>{{ isAuditFinding ? 'Audit Finding' : 'Incident' }} Mitigation Workflow</h2>
        </div>

        <!-- Rejection Banner -->
        <div v-if="isIncidentRejected" class="rejection-banner">
          <div class="rejection-content">
            <div class="rejection-icon">⚠️</div>
            <div class="rejection-text">
              <h3>This incident has been rejected and requires resubmission</h3>
              <p>The reviewer has rejected your submission. Please review the feedback below, update the required information, and resubmit for review.</p>
            </div>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loadingMitigations" class="loading-state">
          <div class="spinner"></div>
          <span>Loading mitigation steps...</span>
        </div>

        <!-- No Data State -->
        <div v-else-if="!mitigationSteps.length" class="no-data-state">
          No mitigation steps found for this incident.
        </div>

        <!-- Workflow Steps -->
        <div v-else class="workflow-steps">
          <!-- Enhanced Horizontal Steps Navigation -->
          <div class="audit-tabs steps-navigation">
            <button 
              v-for="(step, index) in mitigationSteps" 
              :key="index"
              :class="['tab-button step-button', { 
                active: currentStep === index,
                completed: step.status === 'Completed',
                approved: step.approved === true,
                rejected: step.approved === false
              }]"
              @click="currentStep = index"
            >
              <div class="tab-number step-number">{{ index + 1 }}</div>
              <div class="step-content">
                <span class="step-title">{{ step.description }}</span>
                <span v-if="step.status === 'Completed'" class="step-status-indicator">
                  <i class="fas fa-check-circle"></i>
                </span>
                <span v-else-if="step.approved === true" class="step-status-indicator approved">
                  <i class="fas fa-check-circle"></i>
                </span>
                <span v-else-if="step.approved === false" class="step-status-indicator rejected">
                  <i class="fas fa-times-circle"></i>
                </span>
              </div>
            </button>
            
            <!-- Questionnaire Step -->
            <button 
              v-if="allStepsCompleted"
              :class="['tab-button step-button', { active: currentStep === mitigationSteps.length }]"
              @click="currentStep = mitigationSteps.length"
            >
              <div class="tab-number step-number">{{ mitigationSteps.length + 1 }}</div>
              <div class="step-content">
                <span class="step-title">Assessment Questionnaire</span>
              </div>
            </button>
          </div>

          <!-- Step Content -->
          <div class="step-content">
            <!-- Mitigation Step Content -->
            <div v-if="currentStep < mitigationSteps.length" class="mitigation-step-content">
              <div class="step-header">
                <h3>Step {{ currentStep + 1 }}: {{ mitigationSteps[currentStep].description }}</h3>
                <div class="step-status-indicator">
                  <span v-if="mitigationSteps[currentStep].approved === true" class="status-approved">
                    <i class="fas fa-check-circle"></i> Approved
                  </span>
                  <span v-else-if="mitigationSteps[currentStep].approved === false" class="status-rejected">
                    <i class="fas fa-times-circle"></i> Rejected
                  </span>
                  <span v-else-if="mitigationSteps[currentStep].status === 'Completed'" class="status-pending">
                    <i class="fas fa-clock"></i> Pending Review
                  </span>
                  <span v-else class="status-not-started">
                    <i class="fas fa-circle"></i> Not Started
                  </span>
                </div>
              </div>

              <!-- Approval Status Display -->
              <div v-if="mitigationSteps[currentStep].approved === true" class="approval-status">
                <div class="approval-message">
                  <i class="fas fa-lock"></i>
                  This step has been approved by the reviewer and is locked for editing
                </div>
                <div v-if="mitigationSteps[currentStep].comments" class="comments-display">
                  <h4>Comments</h4>
                  <p>{{ mitigationSteps[currentStep].comments }}</p>
                </div>
                <div v-if="mitigationSteps[currentStep].fileName || (mitigationSteps[currentStep].files && mitigationSteps[currentStep].files.length > 0)" class="file-display">
                  <h4>Evidence</h4>
                  <!-- Multiple files display (preferred) -->
                  <div v-if="mitigationSteps[currentStep].files && mitigationSteps[currentStep].files.length > 0" class="evidence-files-list">
                    <div v-for="(file, fileIndex) in mitigationSteps[currentStep].files" :key="fileIndex" class="evidence-file">
                      <!-- Linked Evidence (with documents support) -->
                      <div v-if="file.type === 'linked_evidence'" class="linked-evidence-item">
                        <i class="fas fa-link"></i>
                        <div class="linked-evidence-details">
                          <div class="evidence-title">{{ file.fileName }}</div>
                          <div class="evidence-source">Source: {{ file.linkedEvent?.source || 'Unknown' }}</div>
                          <div class="evidence-meta">
                            <span v-if="file.linkedEvent?.framework">{{ file.linkedEvent.framework }}</span>
                            <span v-if="file.linkedEvent?.status" class="evidence-status">Status: {{ file.linkedEvent.status }}</span>
                            <span v-if="file.linkedEvent?.document_count > 0" class="document-count">{{ file.linkedEvent.document_count }} Document(s)</span>
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
                            <button @click="showLinkedEventDetails(file.linkedEvent)" class="view-details-btn">
                              <i class="fas fa-info-circle"></i> View Details
                            </button>
                            <button v-if="file.linkedEvent?.documents && file.linkedEvent.documents.length > 0" @click="refreshLinkedEvidence()" class="refresh-docs-btn" title="Refresh Documents">
                              <i class="fas fa-sync-alt"></i> Refresh Docs
                            </button>
                          </div>
                        </div>
                        <span class="linked-evidence-badge">Linked Event</span>
                      </div>
                      
                      <!-- Regular File (downloadable) -->
                      <a v-else :href="file['aws-file_link']" :download="file.fileName" target="_blank" class="downloadable-file">
                        <i class="fas fa-download"></i> {{ file.fileName }}
                        <span v-if="file.size" class="file-size">({{ formatFileSize(file.size) }})</span>
                        <span v-if="file.upload_type === 's3'" class="s3-indicator" title="Stored in S3">
                          <i class="fas fa-cloud"></i>
                        </span>
                      </a>
                    </div>
                  </div>
                  <!-- Legacy single file display (fallback when no files array) -->
                  <div v-else-if="mitigationSteps[currentStep].fileName && mitigationSteps[currentStep]['aws-file_link']" class="evidence-file">
                    <!-- Check if it's a linked event (placeholder URL) -->
                    <div v-if="mitigationSteps[currentStep]['aws-file_link'].startsWith('#linked-event-')" class="linked-evidence-item" @click="showLinkedEventDetailsFromStep(currentStep)" role="button" tabindex="0">
                      <i class="fas fa-link"></i>
                      <div class="linked-evidence-details">
                        <div class="evidence-title">{{ mitigationSteps[currentStep].fileName }}</div>
                        <div class="evidence-source">Source: Linked Event</div>
                        <div class="evidence-meta">
                          <span>Click to view details</span>
                        </div>
                      </div>
                      <span class="linked-evidence-badge">Linked Event</span>
                    </div>
                    
                    <!-- Regular downloadable file -->
                    <a v-else :href="mitigationSteps[currentStep]['aws-file_link']" :download="mitigationSteps[currentStep].fileName" target="_blank" class="downloadable-file">
                      <i class="fas fa-download"></i> {{ mitigationSteps[currentStep].fileName }}
                    </a>
                  </div>
                </div>
              </div>

              <!-- Rejection Status Display -->
              <div v-else-if="mitigationSteps[currentStep].approved === false" class="rejection-status">
                <div class="rejection-message">
                  <i class="fas fa-exclamation-triangle"></i>
                  This step was rejected by the reviewer and needs to be updated
                </div>
                <div v-if="mitigationSteps[currentStep].remarks" class="rejection-feedback">
                  <h4>Reviewer Feedback</h4>
                  <p>{{ mitigationSteps[currentStep].remarks }}</p>
                </div>
              </div>

              <!-- Step Input Form -->
              <div v-if="mitigationSteps[currentStep].approved === false || mitigationSteps[currentStep].approved === null" class="step-form">
                <!-- Previous Comments -->
                <div v-if="mitigationSteps[currentStep].previousComments && mitigationSteps[currentStep].previousComments.trim()" class="previous-comments">
                  <h4>Previous Comments</h4>
                  <div class="previous-comments-content">
                    {{ mitigationSteps[currentStep].previousComments }}
                  </div>
                </div>

                <!-- Comments Input -->
                <div class="form-group">
                  <label for="comments">
                    {{ mitigationSteps[currentStep].previousComments && mitigationSteps[currentStep].previousComments.trim() ? 'Add New Comments:' : 'Comments:' }}
                  </label>
                  <textarea 
                    id="comments" 
                    v-model="mitigationSteps[currentStep].comments" 
                    :placeholder="mitigationSteps[currentStep].previousComments && mitigationSteps[currentStep].previousComments.trim() ? 'Add additional comments about this mitigation step...' : 'Add your comments about this mitigation step...'"
                    rows="4"
                  ></textarea>
                </div>

                <!-- Evidence Attachment Section -->
                <div class="form-group evidence-section">
                  <div class="evidence-header">
                    <h4>Evidence Documents</h4>
                    <p class="evidence-instruction">Upload supporting documents for this mitigation step</p>
                  </div>
                  
                  <!-- Current Evidence Display -->
                  <div v-if="mitigationSteps[currentStep].files && mitigationSteps[currentStep].files.length > 0" class="current-evidence">
                    <h5>Current Documents ({{ mitigationSteps[currentStep].files.length }})</h5>
                    <div class="evidence-files-list">
                      <div v-for="(file, fileIndex) in mitigationSteps[currentStep].files" :key="fileIndex" class="evidence-file-item">
                        <div class="file-info">
                          <i class="fas fa-file-alt file-icon"></i>
                          <div class="file-details">
                            <div class="file-name">{{ file.fileName }}</div>
                            <div class="file-size" v-if="file.size">{{ formatFileSize(file.size) }}</div>
                          </div>
                        </div>
                        <div class="file-actions">
                          <a :href="file['aws-file_link']" target="_blank" class="view-file-btn" title="View File">
                            <i class="fas fa-eye"></i> View
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Upload New Evidence -->
                  <div class="upload-evidence">
                    <h5>Upload New Evidence</h5>
                    <EvidenceAttachment 
                      :incident-id="selectedIncidentId"
                      :user-id="selectedUserId"
                      @filesUploaded="handleFilesUploaded"
                    />
                  </div>
                </div>

                <!-- Complete Button -->
                <div class="form-actions">
                  <button 
                    @click="updateStepStatus(currentStep, 'Completed')" 
                    class="complete-button"
                    :class="{ active: mitigationSteps[currentStep].status === 'Completed' }"
                  >
                    <i class="fas fa-check"></i> Mark as Complete
                  </button>
                </div>
              </div>
            </div>

            <!-- Questionnaire Content -->
            <div v-else-if="currentStep === mitigationSteps.length && allStepsCompleted" class="questionnaire-content">
              <div class="questionnaire-header">
                <h3>Incident Assessment Questionnaire</h3>
                <p>Please complete the assessment questionnaire to finalize your submission.</p>
              </div>

              <div class="questionnaire-form">
                <!-- Question 1: Cost -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">1</span>
                    What is the total cost for implementing this mitigation? (Optional)
                  </label>
                  <div class="input-with-prefix">
                    <span class="currency-prefix">$</span>
                    <input 
                      type="number" 
                      v-model="questionnaireData.cost" 
                      placeholder="Enter amount (e.g., 5000.50)"
                      class="question-input currency-input"
                      min="0"
                      step="0.01"
                      @input="validateCurrencyInput('cost', $event)"
                    />
                  </div>
                  <small class="field-hint">Include labor, materials, technology, and any third-party costs</small>
                </div>

                <!-- Question 2: Impact -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">2</span>
                    What is the overall impact level of this incident? (Optional)
                  </label>
                  <select v-model="questionnaireData.impact" class="question-select">
                    <option value="">Select impact level...</option>
                    <option value="Very Low">Very Low - Minimal disruption, easily contained</option>
                    <option value="Low">Low - Minor disruption, limited scope</option>
                    <option value="Medium">Medium - Moderate disruption, manageable impact</option>
                    <option value="High">High - Significant disruption, widespread impact</option>
                    <option value="Very High">Very High - Severe disruption, critical impact</option>
                  </select>
                  <small class="field-hint">Consider operational, business, and stakeholder impact</small>
                </div>

                <!-- Question 3: Financial Impact -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">3</span>
                    What is the financial impact scale of this incident? (Optional)
                  </label>
                  <select v-model="questionnaireData.financialImpact" class="question-select">
                    <option value="">Select financial impact level...</option>
                    <option value="Very Low">Very Low - Under $1,000 in losses/costs</option>
                    <option value="Low">Low - $1,000 - $10,000 in losses/costs</option>
                    <option value="Medium">Medium - $10,000 - $100,000 in losses/costs</option>
                    <option value="High">High - $100,000 - $1,000,000 in losses/costs</option>
                    <option value="Very High">Very High - Over $1,000,000 in losses/costs</option>
                  </select>
                  <small class="field-hint">Include direct losses, opportunity costs, and recovery expenses</small>
                </div>

                <!-- Question 4: Reputational Impact -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">4</span>
                    What is the reputational impact scale of this incident? (Optional)
                  </label>
                  <select v-model="questionnaireData.reputationalImpact" class="question-select">
                    <option value="">Select reputational impact level...</option>
                    <option value="Very Low">Very Low - Minimal or no reputational damage</option>
                    <option value="Low">Low - Minor reputational concerns, limited visibility</option>
                    <option value="Medium">Medium - Moderate reputational impact, some stakeholder concern</option>
                    <option value="High">High - Significant reputational damage, widespread attention</option>
                    <option value="Very High">Very High - Severe reputational crisis, major media coverage</option>
                  </select>
                  <small class="field-hint">Consider impact on brand, customer trust, media coverage, and stakeholder confidence</small>
                </div>

                <!-- Question 5: Operational Impact -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">5</span>
                    What is the operational impact scale of this incident? (Optional)
                  </label>
                  <select v-model="questionnaireData.operationalImpact" class="question-select">
                    <option value="">Select operational impact level...</option>
                    <option value="Very Low">Very Low - Minimal disruption, normal operations maintained</option>
                    <option value="Low">Low - Minor disruption, limited service impact</option>
                    <option value="Medium">Medium - Moderate disruption, some services affected</option>
                    <option value="High">High - Significant disruption, major service interruption</option>
                    <option value="Very High">Very High - Severe disruption, critical systems down</option>
                  </select>
                  <small class="field-hint">Consider disruptions to processes, services, productivity, and normal operations</small>
                </div>

                <!-- Question 6: Financial Loss -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">6</span>
                    What is the estimated financial loss from this incident? (Optional)
                  </label>
                  <div class="input-with-prefix">
                    <span class="currency-prefix">$</span>
                    <input 
                      type="number" 
                      v-model="questionnaireData.financialLoss" 
                      placeholder="Enter total loss amount (e.g., 25000.00)"
                      class="question-input currency-input"
                      min="0"
                      step="0.01"
                      @input="validateCurrencyInput('financialLoss', $event)"
                    />
                  </div>
                  <small class="field-hint">Include revenue loss, regulatory fines, penalties, legal costs, and recovery expenses</small>
                </div>

                <!-- Question 7: System Downtime -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">7</span>
                    What is the expected system downtime if this incident occurs again? (Optional)
                  </label>
                  <div class="input-with-suffix">
                    <input 
                      type="number" 
                      v-model="questionnaireData.systemDowntime" 
                      placeholder="Enter hours (e.g., 8.5)"
                      class="question-input hours-input"
                      min="0"
                      step="0.5"
                      @input="validateHoursInput('systemDowntime', $event)"
                    />
                    <span class="hours-suffix">hours</span>
                  </div>
                  <small class="field-hint">Estimate total time systems/services would be unavailable (decimals allowed, e.g., 2.5 hours)</small>
                </div>

                <!-- Question 8: Recovery Time -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">8</span>
                    How long did it take to recover from this incident? (Optional)
                  </label>
                  <div class="input-with-suffix">
                    <input 
                      type="number" 
                      v-model="questionnaireData.recoveryTime" 
                      placeholder="Enter hours (e.g., 12.0)"
                      class="question-input hours-input"
                      min="0"
                      step="0.5"
                      @input="validateHoursInput('recoveryTime', $event)"
                    />
                    <span class="hours-suffix">hours</span>
                  </div>
                  <small class="field-hint">Time from incident detection to complete restoration of normal operations (decimals allowed)</small>
                </div>

                <!-- Question 9: Risk Recurrence -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">9</span>
                    Is it possible that this incident will recur again? (Optional)
                  </label>
                  <select v-model="questionnaireData.riskRecurrence" class="question-select">
                    <option value="">Select likelihood...</option>
                    <option value="yes">Yes - High likelihood of recurrence</option>
                    <option value="maybe">Maybe - Possible but uncertain recurrence</option>
                    <option value="no">No - Very unlikely to recur</option>
                  </select>
                  <small class="field-hint">Consider if root causes have been addressed and preventive measures are in place</small>
                </div>

                <!-- Question 10: Improvement Initiative -->
                <div class="question-group">
                  <label class="question-label">
                    <span class="question-number">10</span>
                    Is this mitigation an improvement initiative that will prevent future recurrence? (Optional)
                  </label>
                  <select v-model="questionnaireData.improvementInitiative" class="question-select">
                    <option value="">Select prevention level...</option>
                    <option value="yes">Yes - Completely prevents recurrence</option>
                    <option value="partially">Partially - Reduces likelihood of recurrence</option>
                    <option value="no">No - Does not prevent recurrence</option>
                  </select>
                  <small class="field-hint">Assess whether this mitigation addresses root causes and prevents similar incidents</small>
                </div>
              </div>

              <div class="questionnaire-actions">
                <button @click="closeMitigationModal" class="cancel-button">
                  <i class="fas fa-times"></i> Cancel
                </button>
                <button 
                  @click="submitIncidentAssessment" 
                  class="submit-button"
                  :disabled="!isQuestionnaireValid"
                >
                  <i class="fas fa-check-circle"></i> Submit Assessment
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Reviewer Workflow -->
    <div v-if="showReviewerWorkflow" class="workflow-overlay">
      <div class="workflow-container">
        <!-- Back Button -->
        <div class="workflow-header">
          <button @click="closeReviewerModal" class="back-button">
            <i class="fas fa-arrow-left"></i>
            Back to Tasks
          </button>
          <h2>Review Incident Mitigations</h2>
        </div>

        <!-- Loading State -->
        <div v-if="loadingMitigations" class="loading-state">
          <div class="spinner"></div>
          <span>Loading mitigation data...</span>
        </div>

        <!-- Reviewer Content -->
        <div v-else class="reviewer-content">
          <div class="incident-summary">
            <h3>{{ currentReviewTask?.Title || 'Incident #' + currentReviewTask?.id }}</h3>
            <p><strong>ID:</strong> {{ currentReviewTask?.id }}</p>
            <p><strong>Submitted By:</strong> {{ getUserName(currentReviewTask?.AssignerId) }}</p>
          </div>

          <!-- Questionnaire Review -->
          <div v-if="questionnaireReviewData" class="questionnaire-review">
            <h3>Assessment Questionnaire</h3>
            <div class="questionnaire-grid">
              <div class="questionnaire-item" v-if="questionnaireReviewData.cost">
                <label>Cost for Mitigation:</label>
                <p>{{ questionnaireReviewData.cost }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.impact">
                <label>Impact:</label>
                <p>{{ questionnaireReviewData.impact }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.financialImpact">
                <label>Financial Impact:</label>
                <p>{{ questionnaireReviewData.financialImpact }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.reputationalImpact">
                <label>Reputational Impact Scale:</label>
                <p>{{ questionnaireReviewData.reputationalImpact }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.operationalImpact">
                <label>Operational Impact Scale:</label>
                <p>{{ questionnaireReviewData.operationalImpact }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.financialLoss">
                <label>Financial Loss:</label>
                <p>{{ questionnaireReviewData.financialLoss }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.systemDowntime">
                <label>Expected System Downtime (hrs):</label>
                <p>{{ questionnaireReviewData.systemDowntime }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.recoveryTime">
                <label>Recovery Time (hrs):</label>
                <p>{{ questionnaireReviewData.recoveryTime }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.riskRecurrence">
                <label>Risk Recurrence Possibility:</label>
                <p>{{ questionnaireReviewData.riskRecurrence }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.improvementInitiative">
                <label>Improvement Initiative:</label>
                <p>{{ questionnaireReviewData.improvementInitiative }}</p>
              </div>
              
              <div class="questionnaire-item" v-if="questionnaireReviewData.submittedAt">
                <label>Submitted At:</label>
                <p>{{ formatDateTime(questionnaireReviewData.submittedAt) }}</p>
              </div>
            </div>

            <!-- Assessment Approval -->
            <div v-if="!reviewCompleted" class="assessment-approval">
              <h4>Assessment Review</h4>
              <div class="approval-controls">
                <button 
                  @click="approveAssessment(true)" 
                  class="approve-button"
                  :class="{ active: assessmentFeedback.approved === true }"
                >
                  <i class="fas fa-check-circle"></i> Approve Assessment
                </button>
                <button 
                  @click="approveAssessment(false)" 
                  class="reject-button"
                  :class="{ active: assessmentFeedback.approved === false }"
                >
                  <i class="fas fa-times-circle"></i> Reject Assessment
                </button>
              </div>
              
              <div v-if="assessmentFeedback.approved === false" class="feedback-section">
                <label for="assessment-feedback">Assessment Feedback (required for rejection):</label>
                <textarea 
                  id="assessment-feedback"
                  v-model="assessmentFeedback.remarks" 
                  placeholder="Provide detailed feedback about why the assessment was rejected..."
                  rows="4"
                ></textarea>
              </div>
            </div>
          </div>

          <!-- Mitigation Review -->
          <div class="mitigation-review">
            <h3>Mitigation Review</h3>
            <div class="mitigation-list">
              <div 
                v-for="(mitigation, id) in mitigationReviewData" 
                :key="id" 
                class="mitigation-item"
              >
                <div class="mitigation-header">
                  <h4>Mitigation #{{ id }}</h4>
                  <div class="mitigation-status" :class="{ 
                    approved: mitigation.approved === true, 
                    rejected: mitigation.approved === false,
                    pending: mitigation.approved === undefined
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
                
                <div class="mitigation-content">
                  <div class="mitigation-description">
                    <h5>Description</h5>
                    <p>{{ mitigation.description }}</p>
                  </div>
                  
                  <div v-if="mitigation.comments" class="mitigation-comments">
                    <h5>User Comments</h5>
                    <p>{{ mitigation.comments }}</p>
                  </div>
                  
                  <div v-if="mitigation['aws-file_link'] || (mitigation.files && mitigation.files.length > 0)" class="mitigation-evidence">
                    <h5>Evidence</h5>
                    <!-- Multiple files display (preferred) -->
                    <div v-if="mitigation.files && mitigation.files.length > 0" class="evidence-files-list">
                      <div v-for="(file, fileIndex) in mitigation.files" :key="fileIndex" class="evidence-file">
                        <!-- Linked Evidence (with documents support) -->
                        <div v-if="file.type === 'linked_evidence'" class="linked-evidence-item">
                          <i class="fas fa-link"></i>
                          <div class="linked-evidence-details">
                            <div class="evidence-title">{{ file.fileName }}</div>
                            <div class="evidence-source">Source: {{ file.linkedEvent?.source || 'Unknown' }}</div>
                            <div class="evidence-meta">
                              <span v-if="file.linkedEvent?.framework">{{ file.linkedEvent.framework }}</span>
                              <span v-if="file.linkedEvent?.status" class="evidence-status">Status: {{ file.linkedEvent.status }}</span>
                              <span v-if="file.linkedEvent?.document_count > 0" class="document-count">{{ file.linkedEvent.document_count }} Document(s)</span>
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
                              <button @click="showLinkedEventDetails(file.linkedEvent)" class="view-details-btn">
                                <i class="fas fa-info-circle"></i> View Details
                              </button>
                              <button v-if="file.linkedEvent?.documents && file.linkedEvent.documents.length > 0" @click="refreshLinkedEvidence()" class="refresh-docs-btn" title="Refresh Documents">
                                <i class="fas fa-sync-alt"></i> Refresh Docs
                              </button>
                            </div>
                          </div>
                          <span class="linked-evidence-badge">Linked Event</span>
                        </div>
                        
                        <!-- Regular File (downloadable) -->
                        <a v-else :href="file['aws-file_link']" download :filename="file.fileName" class="evidence-link">
                          <i class="fas fa-download"></i> {{ file.fileName }}
                          <span v-if="file.size" class="file-size">({{ formatFileSize(file.size) }})</span>
                          <span v-if="file.upload_type === 's3'" class="s3-indicator" title="Stored in S3">
                            <i class="fas fa-cloud"></i>
                          </span>
                        </a>
                      </div>
                    </div>
                    <!-- Legacy single file display (fallback when no files array) -->
                    <div v-else-if="mitigation['aws-file_link'] && mitigation.fileName" class="evidence-file">
                      <!-- Check if it's a linked event (placeholder URL) -->
                      <div v-if="mitigation['aws-file_link'].startsWith('#linked-event-')" class="linked-evidence-item" @click="showLinkedEventDetailsFromMitigation(mitigation)" role="button" tabindex="0">
                        <i class="fas fa-link"></i>
                        <div class="linked-evidence-details">
                          <div class="evidence-title">{{ mitigation.fileName }}</div>
                          <div class="evidence-source">Source: Linked Event</div>
                          <div class="evidence-meta">
                            <span>Click to view details</span>
                          </div>
                        </div>
                        <span class="linked-evidence-badge">Linked Event</span>
                      </div>
                      
                      <!-- Regular downloadable file -->
                      <a v-else :href="mitigation['aws-file_link']" download :filename="mitigation.fileName" class="evidence-link">
                        <i class="fas fa-download"></i> {{ mitigation.fileName }}
                      </a>
                    </div>
                  </div>
                </div>
                
                <div class="mitigation-actions">
                  <div v-if="mitigation.approved !== true && mitigation.approved !== false && !reviewCompleted" class="approval-buttons">
                    <button @click="approveMitigation(id, true)" class="approve-button">
                      <i class="fas fa-check-double"></i> Approve
                    </button>
                    <button @click="approveMitigation(id, false)" class="reject-button">
                      <i class="fas fa-ban"></i> Reject
                    </button>
                  </div>
                  
                  <div v-if="mitigation.approved === false && !reviewCompleted" class="feedback-section">
                    <label for="remarks">Feedback (required for rejection):</label>
                    <textarea 
                      id="remarks" 
                      v-model="mitigation.remarks" 
                      placeholder="Provide feedback explaining why this mitigation was rejected..."
                    ></textarea>
                    <button @click="updateRemarks(id)" class="save-button">
                      <i class="fas fa-save"></i> Save Feedback
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Review Actions -->
          <div class="review-actions">
            <button 
              class="submit-review-button" 
              :disabled="!canSubmitReview || reviewCompleted" 
              @click="submitReview(true)"
            >
              <i class="fas fa-check-double"></i> Approve Incident
            </button>
            <button 
              class="reject-review-button" 
              :disabled="!canSubmitReview || reviewCompleted" 
              @click="submitReview(false)"
            >
              <i class="fas fa-ban"></i> Reject Incident
            </button>
            
            <div v-if="reviewCompleted" class="review-complete">
              This review has been completed
            </div>
            
            <div v-else-if="!canSubmitReview" class="review-warning">
              <i class="fas fa-exclamation-circle"></i>
              You must approve or reject each mitigation and the assessment before submitting
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import axios from 'axios';
import { API_ENDPOINTS } from '../../config/api.js';
import { PopupService, PopupModal } from '@/modules/popup';
import CustomDropdown from '@/components/CustomDropdown.vue';
import CollapsibleTable from '@/components/CollapsibleTable.vue';
import EvidenceAttachment from '@/components/EventHandling/EvidenceAttachment.vue';
import incidentService from '../../services/incidentService.js';
import './IncidentUserTask.css'; // Import the CSS file

export default {
  name: 'IncidentUserTasks',
  components: {
    PopupModal,
    CustomDropdown,
    CollapsibleTable,
    EvidenceAttachment
  },
  data() {
    return {
      // Add incidentService to data so it's available in methods
      incidentService,
      userIncidents: [],
      reviewerTasks: [],
      users: [],
      selectedUserId: '',
      selectedFramework: '',
      userFilterConfig: {
        name: 'User',
        label: 'User',
        defaultLabel: 'All Users',
        values: []
      },
      loading: true,
      error: null,
      showMitigationWorkflow: false,
      showReviewerWorkflow: false,
      loadingMitigations: false,
      mitigationSteps: [],
      selectedIncidentId: null,
      activeTab: 'user',
      mitigationReviewData: {},
      currentReviewTask: null,
      reviewCompleted: false,
      reviewApproved: false,
      previousVersions: {},
      showQuestionnaire: false,
      questionnaireReviewData: {},
      assessmentFeedback: {},
      assessmentFeedbackForUser: null,
      questionnaireData: {
        cost: '',
        impact: '',
        financialImpact: '',
        reputationalImpact: '',
        operationalImpact: '',
        financialLoss: '',
        systemDowntime: '',
        recoveryTime: '',
        riskRecurrence: '',
        improvementInitiative: ''
      },
      expandedSections: {
        approved: true,
        rejected: true,
        pendingReview: true,
        assigned: true,
        reviewerPending: true,
        reviewerApproved: true
      },
      approvedIncidents: [],
      rejectedIncidents: [],
      pendingReviewIncidents: [],
      assignedIncidents: [],
      pendingReviewerTasks: [],
      approvedReviewerTasks: [],
      currentStep: 0
    }
  },
  computed: {
    allStepsCompleted() {
      // Only check rejected or unreviewed steps, ignore approved ones
      const stepsToCheck = this.mitigationSteps.filter(step => step.approved === false || step.approved === null);
      return stepsToCheck.length > 0 && 
             stepsToCheck.every(step => step.status === 'Completed');
    },
    canSubmitReview() {
      const mitigationsValid = Object.values(this.mitigationReviewData).every(m => 
        m.approved === true || (m.approved === false && m.remarks && m.remarks.trim() !== '')
      );
      
      const assessmentValid = this.assessmentFeedback.approved !== undefined && 
        (this.assessmentFeedback.approved === true || 
         (this.assessmentFeedback.approved === false && this.assessmentFeedback.remarks && this.assessmentFeedback.remarks.trim() !== ''));
      
      return mitigationsValid && assessmentValid;
    },
    hasRejectedOrNewSteps() {
      return this.mitigationSteps.some(step => step.approved === false || step.approved === null);
    },
    rejectedStepsCompleted() {
      const rejectedOrNewSteps = this.mitigationSteps.filter(step => step.approved === false || step.approved === null);
      return rejectedOrNewSteps.length > 0 && 
             rejectedOrNewSteps.every(step => step.status === 'Completed');
    },
    isQuestionnaireValid() {
      // All fields are optional, so always return true
      return true;
    },
    isAuditFinding() {
      if (!this.userIncidents || !Array.isArray(this.userIncidents)) return false;
      const task = this.userIncidents.find(t => t.id === this.selectedIncidentId);
      return task && task.itemType === 'audit_finding';
    },
    isIncidentRejected() {
      if (!this.userIncidents || !Array.isArray(this.userIncidents)) return false;
      const task = this.userIncidents.find(t => t.id === this.selectedIncidentId);
      return task && task.Status === 'Rejected';
    },
    currentIncidentDetails() {
      if (!this.userIncidents || !Array.isArray(this.userIncidents)) return {};
      return this.userIncidents.find(t => t.id === this.selectedIncidentId) || {};
    },
    userTaskTableHeaders() {
      return [
        { key: 'id', label: 'ID', sortable: true, width: '8%' },
        { key: 'Title', label: 'Title', sortable: true, width: '30%' },
        { key: 'Origin', label: 'Origin', sortable: true, width: '15%' },
        { key: 'Priority', label: 'Priority', sortable: true, width: '15%' },
        { key: 'MitigationDueDate', label: 'Due Date', sortable: true, width: '15%' },
        { key: 'actions', label: 'Actions', sortable: false, width: '17%' }
      ];
    },
    reviewerTaskTableHeaders() {
      return [
        { key: 'id', label: 'ID', sortable: true, width: '8%' },
        { key: 'Title', label: 'Title', sortable: true, width: '30%' },
        { key: 'Origin', label: 'Origin', sortable: true, width: '15%' },
        { key: 'Priority', label: 'Priority', sortable: true, width: '15%' },
        { key: 'AssignerId', label: 'Assigned By', sortable: true, width: '15%' },
        { key: 'actions', label: 'Actions', sortable: false, width: '17%' }
      ];
    },
    userTaskSections() {
      return [
        {
          name: 'Approved',
          statusKey: 'approved',
          statusClass: 'approved',
          tasks: this.approvedIncidents.map(i => ({ ...i, actions: 'view' }))
        },
        {
          name: 'Rejected',
          statusKey: 'rejected',
          statusClass: 'rejected',
          tasks: this.rejectedIncidents.map(i => ({ ...i, actions: 'resubmit' }))
        },
        {
          name: 'Pending Review',
          statusKey: 'pendingReview',
          statusClass: 'pending-review',
          tasks: this.pendingReviewIncidents.map(i => ({ ...i, actions: 'view' }))
        },
        {
          name: 'Assigned',
          statusKey: 'assigned',
          statusClass: 'assigned',
          tasks: this.assignedIncidents.map(i => ({ ...i, actions: 'view' }))
        }
      ];
    },
    reviewerTaskSections() {
      return [
        {
          name: 'Pending Review',
          statusKey: 'reviewerPending',
          statusClass: 'pending-review',
          tasks: this.pendingReviewerTasks.map(i => ({ ...i, actions: 'review' }))
        },
        {
          name: 'Approved',
          statusKey: 'reviewerApproved',
          statusClass: 'approved',
          tasks: this.approvedReviewerTasks.map(i => ({ ...i, actions: 'view' }))
        }
      ];
    }
  },
    watch: {
    selectedIncidentId(newId, oldId) {
      if (newId && newId !== oldId) {
        this.$nextTick(() => {
          this.fetchLinkedEvidenceDocuments();
        });
      }
    }
  },
  async mounted() {
    console.log('🚀 [IncidentUserTasks] Component mounted');
    
    // Wait for incident data fetch if still in progress
    if (window.incidentDataFetchPromise) {
      console.log('⏳ [IncidentUserTasks] Waiting for incident data fetch...');
      try {
        await window.incidentDataFetchPromise;
        console.log('✅ [IncidentUserTasks] Incident data fetch completed');
      } catch (error) {
        console.warn('⚠️ [IncidentUserTasks] Incident data fetch failed:', error);
      }
    }
    
    // Fetch selected framework from home page first
    await this.fetchSelectedFramework();
    
    // Load users with three-tier fallback pattern
    await this.loadUsers();
    
    this.initializeFromQuery();
    this.setDefaultUser();
    
    // Ensure evidence documents are fetched when component loads
    this.$nextTick(() => {
      if (this.selectedIncidentId) {
        this.fetchLinkedEvidenceDocuments();
      }
    });
  },
  methods: {
    async fetchSelectedFramework() {
      try {
        console.log('🔍 Fetching selected framework for incident user tasks...');
        const frameworkResponse = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED);
        console.log('Framework response:', frameworkResponse.data);
        
        if (frameworkResponse.data && frameworkResponse.data.frameworkId) {
          const frameworkId = parseInt(frameworkResponse.data.frameworkId);
          // If frameworkId is empty, null, undefined, or 0, set it to empty string (All Frameworks)
          this.selectedFramework = frameworkId || '';
          console.log('✅ Set selectedFramework for incident user tasks:', this.selectedFramework);
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
    async loadUsers() {
      try {
        console.log('🔍 [IncidentUserTasks] Checking for cached users...');

        // Check if prefetch is in progress or cache is available
        if (!window.incidentDataFetchPromise && !incidentService.hasValidUsersCache()) {
          console.log('🚀 [IncidentUserTasks] Starting incident prefetch for users (user navigated directly)...');
          window.incidentDataFetchPromise = incidentService.fetchAllIncidentData();
        }

        // Wait for prefetch if it's in progress
        if (window.incidentDataFetchPromise) {
          console.log('⏳ [IncidentUserTasks] Waiting for incident prefetch to complete...');
          try {
            await window.incidentDataFetchPromise;
            console.log('✅ [IncidentUserTasks] Incident prefetch completed');
          } catch (prefetchError) {
            console.warn('⚠️ [IncidentUserTasks] Incident prefetch failed, will fetch users directly', prefetchError);
          }
        }

        // Use cached data if available
        if (incidentService.hasValidUsersCache()) {
          console.log('✅ [IncidentUserTasks] Using cached users');
          const cachedUsers = incidentService.getData('incidentUsers') || [];
          this.users = cachedUsers.map(user => ({ ...user }));
          this.userFilterConfig.values = [
            { value: '', label: 'All Users' },
            ...this.users.map(user => ({
              value: user.UserId,
              label: `${user.UserName} (${user.role || user.Role || 'User'})`
            }))
          ];
          this.loading = false;
          this.setDefaultUser();
          return;
        }

        // Fallback: Fetch directly from API
        console.log('⚠️ [IncidentUserTasks] No cached users found, fetching from API...');
        this.fetchUsers();
      } catch (error) {
        console.error('❌ [IncidentUserTasks] Error loading users:', error);
        this.fetchUsers();
      }
    },
    fetchUsers() {
      console.log('🔄 [IncidentUserTasks] Fetching users from API...');
      axios.get(API_ENDPOINTS.CUSTOM_USERS, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json'
        }
      })
        .then(response => {
          console.log('✅ [IncidentUserTasks] Users API response:', response.data);
          console.log('✅ [IncidentUserTasks] Response status:', response.status);
          console.log('✅ [IncidentUserTasks] Response data type:', typeof response.data);
          
          // Handle multiple response formats
          let users = [];
          if (response.data && response.data.success && response.data.users) {
            users = response.data.users;
            console.log('✅ [IncidentUserTasks] Parsed users from success.users format:', users.length);
          } else if (Array.isArray(response.data)) {
            users = response.data;
            console.log('✅ [IncidentUserTasks] Parsed users from direct array format:', users.length);
          } else if (response.data && Array.isArray(response.data.data)) {
            users = response.data.data;
            console.log('✅ [IncidentUserTasks] Parsed users from data.data format:', users.length);
          } else {
            console.warn('⚠️ [IncidentUserTasks] Unexpected response format:', response.data);
          }
          
          // Ensure users have required fields and normalize data
          users = users.map(user => ({
            UserId: user.UserId || user.id || user.userId,
            UserName: user.UserName || user.name || user.username || 'Unknown',
            Role: user.Role || user.role || '',
            Email: user.Email || user.email || '',
            ...user
          })).filter(user => user.UserId); // Filter out invalid users
          
          console.log('✅ [IncidentUserTasks] Users processed successfully:', users.length, 'users');
          console.log('🔍 [IncidentUserTasks] Sample users:', users.slice(0, 3));
          
          this.users = users;
          
          // Update cache for subsequent loads
          incidentService.setData('incidentUsers', users);
          
          // Update the userFilterConfig values
          this.userFilterConfig.values = [
            { value: '', label: 'All Users' },
            ...users.map(user => ({
              value: user.UserId,
              label: `${user.UserName} (${user.role || user.Role || 'User'})`
            }))
          ];
          
          if (users.length === 0) {
            console.warn('⚠️ [IncidentUserTasks] No users found. This might indicate an API issue or empty database.');
          }
          
          this.loading = false;
          // Set default user after users are loaded
          this.setDefaultUser();
        })
        .catch(error => {
          console.error('❌ [IncidentUserTasks] Error fetching users:', error);
          console.error('❌ [IncidentUserTasks] Error details:', error.response?.data);
          console.error('❌ [IncidentUserTasks] Error status:', error.response?.status);
          console.error('❌ [IncidentUserTasks] Error message:', error.message);
          
          // Try fallback endpoint
          console.log('🔄 [IncidentUserTasks] Trying fallback endpoint: /api/users/');
          axios.get('/api/users/', {
            withCredentials: true,
            headers: {
              'Content-Type': 'application/json'
            }
          })
          .then(fallbackResponse => {
            console.log('✅ [IncidentUserTasks] Fallback endpoint response:', fallbackResponse.data);
            
            let users = [];
            if (fallbackResponse.data && fallbackResponse.data.success && fallbackResponse.data.users) {
              users = fallbackResponse.data.users;
            } else if (Array.isArray(fallbackResponse.data)) {
              users = fallbackResponse.data;
            } else if (fallbackResponse.data && Array.isArray(fallbackResponse.data.data)) {
              users = fallbackResponse.data.data;
            }
            
            // Normalize users
            users = users.map(user => ({
              UserId: user.UserId || user.id || user.userId,
              UserName: user.UserName || user.name || user.username || 'Unknown',
              Role: user.Role || user.role || '',
              Email: user.Email || user.email || '',
              ...user
            })).filter(user => user.UserId);
            
            this.users = users;
            incidentService.setData('incidentUsers', users);
            
            this.userFilterConfig.values = [
              { value: '', label: 'All Users' },
              ...users.map(user => ({
                value: user.UserId,
                label: `${user.UserName} (${user.role || user.Role || 'User'})`
              }))
            ];
            
            this.loading = false;
            this.setDefaultUser();
            console.log('✅ [IncidentUserTasks] Fallback endpoint succeeded:', users.length, 'users');
          })
          .catch(fallbackError => {
            console.error('❌ [IncidentUserTasks] Fallback endpoint also failed:', fallbackError);
            this.error = `Failed to fetch users: ${error.message}`;
            this.loading = false;
            this.users = [];
            PopupService.error('Failed to load reviewers. Please refresh the page and try again.');
          });
        });
    },
    setDefaultUser() {
      // Get current user from localStorage using the correct keys per memory
      const currentUser = localStorage.getItem('user_name') || localStorage.getItem('user');
      if (currentUser && this.users.length > 0) {
        // Try to find the user by name
        let userData;
        try {
          // Handle if user is stored as JSON object
          userData = JSON.parse(currentUser);
        } catch (e) {
          // Handle if user is stored as plain string
          userData = { UserName: currentUser };
        }
        
        const userName = userData.UserName || userData.username || userData.name || currentUser;
        const foundUser = this.users.find(user => 
          user.UserName === userName || 
          user.username === userName ||
          user.UserName.toLowerCase() === userName.toLowerCase()
        );
        
        if (foundUser) {
          this.selectedUserId = foundUser.UserId;
          // Add a small delay to ensure UI updates properly
          this.$nextTick(() => {
            this.fetchData();
          });
        }
      }
    },
    switchToReviewerTab() {
      this.activeTab = 'reviewer';
      if (this.selectedUserId) {
        this.fetchData();
        
        // Ensure sections are expanded properly
        this.$nextTick(() => {
          // Expand all reviewer sections by default
          this.expandedSections.reviewerPending = true;
          this.expandedSections.reviewerApproved = true;
        });
      }
    },
    async fetchData() {
      console.log('🔄 [IncidentUserTasks] fetchData called');
      console.log('🔍 [IncidentUserTasks] selectedUserId:', this.selectedUserId);
      console.log('🔍 [IncidentUserTasks] activeTab:', this.activeTab);
      
      if (!this.selectedUserId) {
        console.error('❌ [IncidentUserTasks] No user selected, skipping data fetch');
        this.userIncidents = [];
        this.reviewerTasks = [];
        return;
      }
      
      console.log('✅ [IncidentUserTasks] User selected, fetching data for userId:', this.selectedUserId);
      
      this.loading = true;
      
      // Check if we have filters active
      const hasFrameworkFilter = this.selectedFramework;
      
      // Three-tier fallback pattern: Check cache, wait for prefetch, fall back to API
      if (!hasFrameworkFilter) {
        console.log('🔍 [IncidentUserTasks] Checking for cached incident data...');

        // Check if prefetch is in progress or cache is available
        if (!window.incidentDataFetchPromise && !incidentService.hasValidIncidentsCache()) {
          console.log('🚀 [IncidentUserTasks] Starting incident prefetch (user navigated directly)...');
          window.incidentDataFetchPromise = incidentService.fetchAllIncidentData();
        }

        // Wait for prefetch if it's in progress
        if (window.incidentDataFetchPromise) {
          console.log('⏳ [IncidentUserTasks] Waiting for incident prefetch to complete...');
          try {
            await window.incidentDataFetchPromise;
            console.log('✅ [IncidentUserTasks] Incident prefetch completed');
          } catch (prefetchError) {
            console.warn('⚠️ [IncidentUserTasks] Incident prefetch failed, will fetch directly from API', prefetchError);
          }
        }

        // Use cached data if available - filter general incidents/audit findings by user client-side
        if (incidentService.hasValidIncidentsCache() || incidentService.hasValidAuditFindingsCache()) {
          console.log('✅ [IncidentUserTasks] Using cached incident data - filtering by user client-side');
          
          // Get general incidents and audit findings from cache
          const cachedIncidents = incidentService.getData('incidents') || [];
          const cachedAuditFindings = incidentService.getData('auditFindings') || [];
          
          // Mark each item with its type
          const markedIncidents = Array.isArray(cachedIncidents) 
            ? cachedIncidents.map(item => ({ ...item, itemType: 'incident' })) 
            : [];
          const markedAuditFindings = Array.isArray(cachedAuditFindings) 
            ? cachedAuditFindings.map(item => ({ ...item, itemType: 'audit_finding' })) 
            : [];
          
          // Combine and filter by selected user for user tasks (MY TASKS tab)
          // IMPORTANT: For "My Tasks" we show incidents where the user is the AssignerId
          // AssignerId = the person WHO assigned the task to someone else (for tracking)
          // ReviewerId = the person assigned TO work on the task (shown in Reviewer Tasks tab)
          const combinedTasks = [...markedIncidents, ...markedAuditFindings];
          console.log('🔍 [IncidentUserTasks] Filtering tasks for user:', this.selectedUserId);
          console.log('🔍 [IncidentUserTasks] Total tasks before filter:', combinedTasks.length);
          console.log('🔍 [IncidentUserTasks] Sample task fields:', combinedTasks[0] ? Object.keys(combinedTasks[0]) : 'No tasks');
          if (combinedTasks.length > 0) {
            console.log('🔍 [IncidentUserTasks] Sample task data:', {
              id: combinedTasks[0].id,
              AssignerId: combinedTasks[0].AssignerId,
              ReviewerId: combinedTasks[0].ReviewerId,
              assigned_to_id: combinedTasks[0].assigned_to_id,
              AssignedTo: combinedTasks[0].AssignedTo,
              assigned_to: combinedTasks[0].assigned_to
            });
          }
          
          this.userIncidents = combinedTasks.filter(task => {
            // Normalize user IDs to integers for comparison
            const userId = parseInt(this.selectedUserId);
            
            // For "My Tasks" tab, we want incidents where user is the AssignerId
            // (tasks they assigned to others for tracking)
            const taskAssignerId = task.AssignerId ? parseInt(task.AssignerId) : null;
            const taskAssignerId2 = task.assigner_id ? parseInt(task.assigner_id) : null;
            const taskAssigner = task.Assigner ? parseInt(task.Assigner) : null;
            
            // Check multiple possible field names for assigner
            const matches = (
              taskAssignerId === userId ||  // Primary field: AssignerId
              taskAssignerId2 === userId || // Alternative field: assigner_id
              taskAssigner === userId       // Alternative field: Assigner
            );
            
            if (matches) {
              console.log('✅ [IncidentUserTasks] Task matched (user is assigner):', task.id, {
                AssignerId: task.AssignerId,
                ReviewerId: task.ReviewerId,
                Status: task.Status,
                matchedField: (
                  taskAssignerId === userId ? 'AssignerId' :
                  taskAssignerId2 === userId ? 'assigner_id' :
                  taskAssigner === userId ? 'Assigner' : 'unknown'
                )
              });
            }
            return matches;
          });
          
          // IMPORTANT: Transform cached data field names to match API response format
          // Cached data has: IncidentId, IncidentTitle, RiskPriority
          // API response has: id, Title, Priority
          this.userIncidents = this.userIncidents.map(task => ({
            ...task,
            id: task.id || task.IncidentId,
            Title: task.Title || task.IncidentTitle,
            Priority: task.Priority || task.RiskPriority,
            Origin: task.Origin,
            Status: task.Status,
            MitigationDueDate: task.MitigationDueDate,
            AssignerId: task.AssignerId,
            ReviewerId: task.ReviewerId,
            itemType: task.itemType
          }));
          
          console.log('✅ [IncidentUserTasks] Filtered user tasks:', this.userIncidents.length);
          if (this.userIncidents.length > 0) {
            console.log('✅ [IncidentUserTasks] Sample transformed task:', {
              id: this.userIncidents[0].id,
              Title: this.userIncidents[0].Title,
              Priority: this.userIncidents[0].Priority
            });
          }
          
          // Filter incidents by status
          this.approvedIncidents = this.userIncidents.filter(incident => incident.Status === 'Approved');
          this.rejectedIncidents = this.userIncidents.filter(incident => incident.Status === 'Rejected');
          this.pendingReviewIncidents = this.userIncidents.filter(incident => 
            incident.Status === 'Pending Review' || incident.Status === 'Under Review'
          );
          this.assignedIncidents = this.userIncidents.filter(incident => 
            !['Approved', 'Rejected', 'Pending Review', 'Under Review'].includes(incident.Status)
          );
          
          // Set user task sections
          this.expandedSections = {
            approved: true,
            rejected: true,
            pendingReview: true,
            assigned: true,
            reviewerPending: true,
            reviewerApproved: true
          };
          
          // Reviewer tasks are user-specific and need to be fetched from API
          // Fetch reviewer tasks separately (they're not in general cache)
          // Always fetch them since the count is shown on both tabs
          console.log('📋 [IncidentUserTasks] Fetching reviewer tasks from API (user-specific)...');
          const params = this.selectedFramework ? { framework_id: this.selectedFramework } : {};
          Promise.all([
            axios.get(API_ENDPOINTS.INCIDENT_REVIEWER_TASKS(this.selectedUserId), { params }),
            axios.get(API_ENDPOINTS.AUDIT_FINDING_REVIEWER_TASKS(this.selectedUserId), { params })
          ])
          .then(([incidentReviewerResponse, auditReviewerResponse]) => {
            // Combine reviewer tasks
            const incidentReviewerTasks = incidentReviewerResponse.data || [];
            const auditReviewerTasks = auditReviewerResponse.data || [];
            
            const markedIncidentReviewerTasks = incidentReviewerTasks.map(item => ({ ...item, itemType: 'incident' }));
            const markedAuditReviewerTasks = auditReviewerTasks.map(item => ({ ...item, itemType: 'audit_finding' }));
            
            // Combine and deduplicate reviewer tasks by ID
            const combinedReviewerTasks = [...markedIncidentReviewerTasks, ...markedAuditReviewerTasks];
            this.reviewerTasks = combinedReviewerTasks.filter((task, index, array) => 
              index === array.findIndex(t => t.id === task.id)
            );
            
            // Filter reviewer tasks
            this.approvedReviewerTasks = this.reviewerTasks.filter(task => task.Status === 'Approved');
            this.pendingReviewerTasks = this.reviewerTasks.filter(task => task.Status !== 'Approved');
            
            this.expandedSections.reviewerPending = true;
            this.expandedSections.reviewerApproved = true;
            
            this.loading = false;
            this.error = null;
            console.log(`✅ [IncidentUserTasks] Loaded ${this.userIncidents.length} user tasks from cache and ${this.reviewerTasks.length} reviewer tasks from API`);
          })
          .catch(error => {
            console.error('❌ [IncidentUserTasks] Error fetching reviewer tasks:', error);
            this.reviewerTasks = [];
            this.loading = false;
            this.error = null;
            console.log(`✅ [IncidentUserTasks] Loaded ${this.userIncidents.length} user tasks from cache (reviewer tasks failed)`);
          });
          
          return;
        }
      }
      
      // If framework filter or no cached data, fetch everything from API
      console.log(hasFrameworkFilter ? '🔍 [IncidentUserTasks] Framework filter active, fetching from API' : '⚠️ [IncidentUserTasks] No cached data, fetching from API');
      
      // Build query parameters for framework filtering
      const params = {};
      if (this.selectedFramework) {
        params.framework_id = this.selectedFramework;
        console.log('🔍 Adding framework filter to user tasks:', this.selectedFramework);
      }
      
      // Fetch both incidents and audit findings for the user with framework filter
      Promise.all([
        axios.get(API_ENDPOINTS.USER_INCIDENTS(this.selectedUserId), { params }),
        axios.get(API_ENDPOINTS.USER_AUDIT_FINDINGS(this.selectedUserId), { params }),
        axios.get(API_ENDPOINTS.INCIDENT_REVIEWER_TASKS(this.selectedUserId), { params }),
        axios.get(API_ENDPOINTS.AUDIT_FINDING_REVIEWER_TASKS(this.selectedUserId), { params })
      ])
      .then(([incidentsResponse, auditFindingsResponse, incidentReviewerResponse, auditReviewerResponse]) => {
        // Combine incidents and audit findings
        const incidents = incidentsResponse.data || [];
        const auditFindings = auditFindingsResponse.data || [];
        
        console.log('🔍 [IncidentUserTasks] API Response - Incidents:', incidents.length);
        console.log('🔍 [IncidentUserTasks] API Response - Audit Findings:', auditFindings.length);
        if (incidents.length > 0) {
          console.log('🔍 [IncidentUserTasks] Sample incident:', {
            id: incidents[0].id,
            Title: incidents[0].Title,
            Status: incidents[0].Status,
            AssignerId: incidents[0].AssignerId,
            ReviewerId: incidents[0].ReviewerId
          });
        }
        
        // Mark each item with its type and ensure field name consistency
        const markedIncidents = incidents.map(item => ({ 
          ...item, 
          itemType: 'incident',
          id: item.id || item.IncidentId,
          Title: item.Title || item.IncidentTitle,
          Priority: item.Priority || item.RiskPriority
        }));
        const markedAuditFindings = auditFindings.map(item => ({ 
          ...item, 
          itemType: 'audit_finding',
          id: item.id || item.IncidentId,
          Title: item.Title || item.IncidentTitle,
          Priority: item.Priority || item.RiskPriority
        }));
        
        // Combine and deduplicate by ID
        const combinedUserTasks = [...markedIncidents, ...markedAuditFindings];
        const uniqueUserTasks = combinedUserTasks.filter((task, index, array) => 
          index === array.findIndex(t => t.id === task.id)
        );
        this.userIncidents = uniqueUserTasks;
        
        console.log('✅ [IncidentUserTasks] Total user incidents after deduplication:', this.userIncidents.length);
        console.log('🔍 [IncidentUserTasks] Status breakdown:', {
          all: this.userIncidents.length,
          byStatus: this.userIncidents.reduce((acc, inc) => {
            const status = inc.Status || 'No Status';
            acc[status] = (acc[status] || 0) + 1;
            return acc;
          }, {})
        });
        
        // Filter incidents by status
        // Log all statuses first to debug
        console.log('🔍 [IncidentUserTasks] All incident statuses:', 
          this.userIncidents.map(inc => ({ id: inc.id, Status: inc.Status, Title: inc.Title }))
        );
        
        this.approvedIncidents = this.userIncidents.filter(incident => {
          const matches = incident.Status === 'Approved';
          if (matches) console.log('✅ Approved:', incident.id, incident.Title);
          return matches;
        });
        
        this.rejectedIncidents = this.userIncidents.filter(incident => {
          const matches = incident.Status === 'Rejected';
          if (matches) console.log('✅ Rejected:', incident.id, incident.Title);
          return matches;
        });
        
        this.pendingReviewIncidents = this.userIncidents.filter(incident => {
          const matches = incident.Status === 'Pending Review' || incident.Status === 'Under Review';
          if (matches) console.log('✅ Pending Review:', incident.id, incident.Title, 'Status:', incident.Status);
          return matches;
        });
        
        this.assignedIncidents = this.userIncidents.filter(incident => {
          const status = incident.Status;
          // Include NULL, undefined, empty string, or any status not in the specific categories
          const isAssigned = !['Approved', 'Rejected', 'Pending Review', 'Under Review'].includes(status);
          if (isAssigned) {
            console.log('✅ [IncidentUserTasks] Assigned incident found:', {
              id: incident.id,
              Title: incident.Title,
              Status: status,
              StatusType: typeof status,
              StatusIsNull: status === null,
              StatusIsUndefined: status === undefined,
              ReviewerId: incident.ReviewerId,
              AssignerId: incident.AssignerId
            });
          }
          return isAssigned;
        });
        
        console.log('✅ [IncidentUserTasks] Filtered counts:', {
          approved: this.approvedIncidents.length,
          rejected: this.rejectedIncidents.length,
          pendingReview: this.pendingReviewIncidents.length,
          assigned: this.assignedIncidents.length
        });
        
        // Set all sections to be expanded by default
        this.expandedSections = {
          approved: true,
          rejected: true,
          pendingReview: true,
          assigned: true
        };
        
        // Combine reviewer tasks
        const incidentReviewerTasks = incidentReviewerResponse.data || [];
        const auditReviewerTasks = auditReviewerResponse.data || [];
        
        const markedIncidentReviewerTasks = incidentReviewerTasks.map(item => ({ ...item, itemType: 'incident' }));
        const markedAuditReviewerTasks = auditReviewerTasks.map(item => ({ ...item, itemType: 'audit_finding' }));
        
        // Combine and deduplicate reviewer tasks by ID
        const combinedReviewerTasks = [...markedIncidentReviewerTasks, ...markedAuditReviewerTasks];
        const uniqueReviewerTasks = combinedReviewerTasks.filter((task, index, array) => 
          index === array.findIndex(t => t.id === task.id)
        );
        this.reviewerTasks = uniqueReviewerTasks;
        
        // Filter reviewer tasks
        this.approvedReviewerTasks = this.reviewerTasks.filter(task => task.Status === 'Approved');
        this.pendingReviewerTasks = this.reviewerTasks.filter(task => task.Status !== 'Approved');
        
        // Set reviewer sections to be expanded by default
        this.expandedSections.reviewerPending = true;
        this.expandedSections.reviewerApproved = true;
        
        console.log(`✅ [IncidentUserTasks] Loaded ${this.userIncidents.length} user tasks and ${this.reviewerTasks.length} reviewer tasks from API`);
        
        this.loading = false;
        this.error = null;
      })
      .catch(error => {
        this.error = `Failed to fetch data: ${error.message}`;
        this.loading = false;
      });
    },
    getUserName(userId) {
      const user = this.users.find(u => u.UserId == userId);
      return user ? user.UserName : 'Unknown';
    },
    viewMitigations(incidentId) {
      // Convert incidentId to number if it's a string
      const id = typeof incidentId === 'string' ? parseInt(incidentId, 10) : incidentId;
      
      // Safety check for userIncidents array
      if (!this.userIncidents || !Array.isArray(this.userIncidents)) {
        PopupService.error('Task data not loaded. Please refresh the page and try again.');
        return;
      }

      // Find the task to determine if it's an audit finding or incident
      const task = this.userIncidents.find(t => t.id === id);
      
      if (!task) {
        PopupService.error(`Error: Task not found for ID ${id}`);
        return;
      }
      const isAuditFinding = task && task.itemType === 'audit_finding';
      
      // Set these first to ensure UI updates
      this.selectedIncidentId = id;
      this.showMitigationWorkflow = true;
      this.loadingMitigations = true;
      this.assessmentFeedbackForUser = null;
      
      // Force a UI update
      this.$nextTick(() => {
        // Use appropriate endpoints based on task type
        const mitigationsEndpoint = isAuditFinding
          ? API_ENDPOINTS.AUDIT_FINDING_MITIGATIONS(id)
          : API_ENDPOINTS.INCIDENT_MITIGATIONS(id);
        
        const reviewEndpoint = isAuditFinding
          ? API_ENDPOINTS.AUDIT_FINDING_REVIEW_DATA(id)
          : API_ENDPOINTS.INCIDENT_REVIEW_DATA(id);
        
        // Get the mitigation steps and assessment feedback
        Promise.all([
          axios.get(mitigationsEndpoint),
          axios.get(reviewEndpoint)
        ])
        .then(([mitigationsResponse, reviewResponse]) => {
          this.mitigationSteps = this.parseMitigations(mitigationsResponse.data);
          
          // Fetch enhanced linked evidence data with documents
          this.fetchLinkedEvidenceDocuments();
          
          // Check for assessment feedback from reviewer
          if (reviewResponse.data && reviewResponse.data.assessment_feedback) {
            this.assessmentFeedbackForUser = reviewResponse.data.assessment_feedback;
          }
          
          // Pre-fill questionnaire data if previous data exists
          if (mitigationsResponse.data.previous_assessment_data && 
              Object.keys(mitigationsResponse.data.previous_assessment_data).length > 0) {
            this.questionnaireData = {
              ...this.questionnaireData,
              ...mitigationsResponse.data.previous_assessment_data
            };
          }
          
          this.loadingMitigations = false;
        })
        .catch(error => {
          PopupService.error(`Error loading data: ${error.message}`);
          this.mitigationSteps = [];
          this.assessmentFeedbackForUser = null;
          this.loadingMitigations = false;
        });
      });
    },
    parseMitigations(response) {
      // Handle the new enhanced response format
      if (response && response.mitigations) {
        const mitigations = response.mitigations;
        const keys = Object.keys(mitigations);
        const steps = [];
        
        // Sort keys numerically
        keys.sort((a, b) => Number(a) - Number(b));
        
        for (const key of keys) {
          const mitigation = mitigations[key];
          
          // Handle both old and new format
          let description, approved, remarks, status;
          if (typeof mitigation === 'string') {
            // Old format - just a string description
            description = mitigation;
            approved = null;
            remarks = null;
            status = 'Not Started';
          } else {
            // New format - object with feedback
            description = mitigation.description || mitigation;
            approved = mitigation.approved;
            remarks = mitigation.remarks;
            status = mitigation.status || 'Not Started';
          }
          
          
          steps.push({
            title: `Step ${key}`,
            description: description,
            status: status,
            approved: approved,
            remarks: remarks,
            previousComments: mitigation.comments || '',
            comments: '', // Start with empty for new comments
            'aws-file_link': mitigation['aws-file_link'] || null,
            fileName: mitigation.fileName || null,
            files: mitigation.files || [] // Support multiple files
          });
        }
        return steps;
      }
      
      // Handle legacy format or direct mitigation data
      const data = response.mitigations || response;
      
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
              status: 'Not Started',
              approved: null,
              remarks: null,
              comments: '',
              'aws-file_link': null,
              fileName: null,
              files: [] // Support multiple files
            });
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
          if (parsedData && typeof parsedData === 'object' && !Array.isArray(parsedData)) {
            return this.parseMitigations({ mitigations: parsedData });
          }
          return Array.isArray(parsedData) ? parsedData : [parsedData];
        } catch (e) {
          return [{ title: 'Mitigation', description: data, approved: null, remarks: null }];
        }
      }
      
      // Default fallback
      return [{ title: 'Mitigation', description: 'No detailed mitigation steps available', approved: null, remarks: null, files: [] }];
    },
    closeMitigationModal() {
      this.showMitigationWorkflow = false;
      this.mitigationSteps = [];
      this.selectedIncidentId = null;
      this.showQuestionnaire = false;
      this.currentStep = 0;
      
      // Reset questionnaire data
      this.questionnaireData = {
        cost: '',
        impact: '',
        financialImpact: '',
        reputationalImpact: '',
        operationalImpact: '',
        financialLoss: '',
        systemDowntime: '',
        recoveryTime: '',
        riskRecurrence: '',
        improvementInitiative: ''
      };
    },
    updateStepStatus(index, status) {
      // Prevent editing of approved steps
      if (this.mitigationSteps[index].approved === true) {
        PopupService.warning('This mitigation step has been approved by the reviewer and cannot be modified.');
        return;
      }
      
      // Only allow updates to rejected or unreviewed steps
      if (this.mitigationSteps[index].approved === false || this.mitigationSteps[index].approved === null) {
        this.mitigationSteps[index].status = status;
      }
    },
    submitIncidentAssessment() {
      // Safety check for userIncidents array
      if (!this.userIncidents || !Array.isArray(this.userIncidents)) {
        PopupService.error('Task data not loaded. Please refresh the page and try again.');
        return;
      }

      // Find the task to determine if it's an audit finding or incident
      const task = this.userIncidents.find(t => t.id === this.selectedIncidentId);
      const isAuditFinding = task && task.itemType === 'audit_finding';
      
      this.loading = true;
      
      // Prepare the mitigation data
      const mitigationData = {};
      this.mitigationSteps.forEach((step, index) => {
        const stepNumber = (index + 1).toString();
        
        // Combine previous comments with new comments
        let combinedComments = '';
        const hasPreviousComments = step.previousComments && step.previousComments.trim();
        const hasNewComments = step.comments && step.comments.trim();
        
        if (hasPreviousComments && hasNewComments) {
          combinedComments = `Previous: ${step.previousComments.trim()}\n\nNew: ${step.comments.trim()}`;
        } else if (hasPreviousComments) {
          combinedComments = step.previousComments.trim();
        } else if (hasNewComments) {
          combinedComments = step.comments.trim();
        }
        
        mitigationData[stepNumber] = {
          description: step.description,
          status: step.status || 'Completed',
          comments: combinedComments,
          "aws-file_link": step['aws-file_link'],
          fileName: step.fileName,
          files: step.files || [], // Include multiple files
          approved: step.approved, // Include approval status
          remarks: step.remarks    // Include reviewer remarks
        };
        
      });
      
      // Prepare questionnaire data for assessment
      const extractedInfo = {
        cost: this.questionnaireData.cost || '',
        impact: this.questionnaireData.impact || '',
        financialImpact: this.questionnaireData.financialImpact || '',
        reputationalImpact: this.questionnaireData.reputationalImpact || '',
        operationalImpact: this.questionnaireData.operationalImpact || '',
        financialLoss: this.questionnaireData.financialLoss || '',
        systemDowntime: this.questionnaireData.systemDowntime || '',
        recoveryTime: this.questionnaireData.recoveryTime || '',
        riskRecurrence: this.questionnaireData.riskRecurrence || '',
        improvementInitiative: this.questionnaireData.improvementInitiative || '',
        mitigations: mitigationData,
        submittedAt: new Date().toISOString()
      };
      
      // Use appropriate endpoint based on task type
      const submitEndpoint = isAuditFinding
        ? API_ENDPOINTS.SUBMIT_AUDIT_FINDING_ASSESSMENT
        : API_ENDPOINTS.SUBMIT_INCIDENT_ASSESSMENT;
      
      axios.post(submitEndpoint, {
        incident_id: this.selectedIncidentId,
        user_id: this.selectedUserId,
        extracted_info: extractedInfo
      })
      .then(() => {
        this.loading = false;
        this.closeMitigationModal();
        PopupService.success(`${isAuditFinding ? 'Audit finding' : 'Incident'} assessment submitted for review successfully!`);
        
        // Refresh the tasks list
        this.fetchData();
      })
      .catch(() => {
        this.loading = false;
        PopupService.error('Failed to submit assessment. Please try again.');
      });
    },
    closeReviewerModal() {
      this.showReviewerWorkflow = false;
      this.currentReviewTask = null;
      this.mitigationReviewData = {};
      this.previousVersions = {};
      this.reviewCompleted = false;
      this.reviewApproved = false;
    },
    approveMitigation(id, approved) {
      const updatedMitigation = {
        ...this.mitigationReviewData[id],
        approved: approved,
        reviewer_submitted_date: new Date().toISOString()
      };
      
      if (approved) {
        updatedMitigation.remarks = '';
      }
      
      this.mitigationReviewData = {
        ...this.mitigationReviewData,
        [id]: updatedMitigation
      };
    },
    approveAssessment(approved) {
      this.assessmentFeedback = {
        approved: approved,
        remarks: approved ? '' : this.assessmentFeedback.remarks || ''
      };
    },
    submitReview(approved) {
      if (!this.canSubmitReview) {
        PopupService.warning('Please complete the review of all mitigations');
        return;
      }
      
      const isAuditFinding = this.currentReviewTask && this.currentReviewTask.itemType === 'audit_finding';
      this.loading = true;
      
      // Prepare mitigation feedback for backend
      const mitigationFeedback = {};
      Object.keys(this.mitigationReviewData).forEach(id => {
        const mitigation = this.mitigationReviewData[id];
        mitigationFeedback[id] = {
          approved: mitigation.approved,
          remarks: mitigation.remarks || null
        };
      });
      
      const reviewData = {
        incident_id: this.currentReviewTask.id,
        approved: approved,
        reviewer_id: this.selectedUserId, // This is the reviewer performing the review
        mitigation_feedback: mitigationFeedback,
        assessment_feedback: this.assessmentFeedback
      };
      
      // For audit findings, add overall_decision parameter
      if (isAuditFinding) {
        reviewData.overall_decision = approved ? 'approved' : 'rejected';
      }
      
      
      // Use appropriate endpoint based on task type
      const reviewEndpoint = isAuditFinding
        ? API_ENDPOINTS.COMPLETE_AUDIT_FINDING_REVIEW
        : API_ENDPOINTS.COMPLETE_INCIDENT_REVIEW;
      
      axios.post(reviewEndpoint, reviewData)
        .then(() => {
          this.loading = false;
          
          // Remove this task from the list
          const index = this.reviewerTasks.findIndex(t => t.id === this.currentReviewTask.id);
          if (index !== -1) {
            this.reviewerTasks.splice(index, 1);
          }
          
          this.reviewCompleted = true;
          this.reviewApproved = approved;
          
          PopupService.success(`${isAuditFinding ? 'Audit finding' : 'Incident'} ${approved ? 'approved' : 'rejected'} successfully!`);
          
          setTimeout(() => {
            this.closeReviewerModal();
          }, 2500);
        })
        .catch(() => {
          this.loading = false;
          PopupService.error('Failed to submit review. Please try again.');
        });
    },
    updateRemarks(id) {
      if (!this.mitigationReviewData[id].remarks.trim()) {
        PopupService.warning('Please provide remarks for rejection');
        return;
      }
      
      this.mitigationReviewData = {
        ...this.mitigationReviewData
      };
    },
    reviewMitigations(task) {
      const isAuditFinding = task && task.itemType === 'audit_finding';
      
      this.currentReviewTask = task;
      this.selectedIncidentId = task.id;
      this.loadingMitigations = true;
      this.showReviewerWorkflow = true;
      this.previousVersions = {};
      this.assessmentFeedback = {};
      
      // Use appropriate endpoint based on task type
      const reviewEndpoint = isAuditFinding
        ? API_ENDPOINTS.AUDIT_FINDING_REVIEW_DATA(task.id)
        : API_ENDPOINTS.INCIDENT_REVIEW_DATA(task.id);
      
      // Get review data (includes questionnaire, previous versions, and assessment feedback)
      axios.get(reviewEndpoint)
        .then(response => {
          
          if (response.data) {
            this.mitigationReviewData = response.data.mitigations || {};
            this.questionnaireReviewData = response.data.questionnaire_data || {};
            this.previousVersions = response.data.previous_versions || {};
            
            // Load existing assessment feedback if review is completed
            if (response.data.assessment_feedback) {
              this.assessmentFeedback = response.data.assessment_feedback;
            }
            
            const isCompleted = response.data.approval_entry?.review_completed;
            this.reviewCompleted = isCompleted;
            this.reviewApproved = response.data.approval_entry?.approved_rejected === 'Approved';
            
            this.loadingMitigations = false;
          } else {
            this.mitigationReviewData = {};
            this.questionnaireReviewData = {};
            this.previousVersions = {};
            this.assessmentFeedback = {};
            this.loadingMitigations = false;
          }
        })
        .catch(() => {
          this.mitigationReviewData = {};
          this.questionnaireReviewData = {};
          this.previousVersions = {};
          this.assessmentFeedback = {};
          this.loadingMitigations = false;
        });
    },
    formatDateTime(dateString) {
      if (!dateString) return '';
      
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
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
      
      dueDate.setHours(0, 0, 0, 0);
      today.setHours(0, 0, 0, 0);
      
      const daysLeft = Math.floor((dueDate - today) / (1000 * 60 * 60 * 24));
      
      if (daysLeft < 0) return 'overdue';
      if (daysLeft <= 3) return 'urgent';
      if (daysLeft <= 7) return 'warning';
      return 'on-track';
    },
    getDueStatusText(dateString) {
      if (!dateString) return '';
      
      const dueDate = new Date(dateString);
      const today = new Date();
      
      dueDate.setHours(0, 0, 0, 0);
      today.setHours(0, 0, 0, 0);
      
      const daysLeft = Math.floor((dueDate - today) / (1000 * 60 * 60 * 24));
      
      if (daysLeft < 0) return `(Delayed by ${Math.abs(daysLeft)} days)`;
      if (daysLeft === 0) return '(Due today)';
      if (daysLeft === 1) return '(Due tomorrow)';
      return `(${daysLeft} days left)`;
    },
    getPreviousMitigation(id) {
      if (!this.previousVersions || typeof this.previousVersions !== 'object') {
        return null;
      }
      
      if (!this.previousVersions[id]) {
        return null;
      }
      
      return this.previousVersions[id];
    },
    isStepActive(index) {
      const step = this.mitigationSteps[index];
      return step.approved === false || step.approved === null;
    },
    
    isStepLocked(index) {
      const step = this.mitigationSteps[index];
      return step.approved === true;
    },
    isOverdue(dateString) {
      if (!dateString) return false;
      const dueDate = new Date(dateString);
      const today = new Date();
      dueDate.setHours(0, 0, 0, 0);
      today.setHours(0, 0, 0, 0);
      return dueDate < today;
    },
    initializeFromQuery() {
      // Initialize from query parameters if provided
      const query = this.$route.query;
      if (query.userId) {
        this.selectedUserId = query.userId;
      }
      if (query.taskId) {
        this.viewMitigations(query.taskId);
      }
      if (query.mode === 'reviewer' && query.taskId) {
        // Switch to reviewer tab and open reviewer workflow
        this.activeTab = 'reviewer';
        this.$nextTick(() => {
          const task = { id: query.taskId };
          this.reviewMitigations(task);
        });
      }
    },
    
    // Client-side validation methods for questionnaire
    validateCurrencyInput(fieldName, event) {
      const value = event.target.value;
      
      // Allow empty values (optional fields)
      if (!value || value === '') return;
      
      // Remove any non-numeric characters except decimal point
      const numericValue = value.replace(/[^0-9.]/g, '');
      
      // Validate format
      const currencyPattern = /^[0-9]+(\.[0-9]{0,2})?$/;
      if (!currencyPattern.test(numericValue)) {
        event.target.setCustomValidity('Please enter a valid amount (e.g., 1000.50)');
      } else {
        const amount = parseFloat(numericValue);
        if (amount < 0) {
          event.target.setCustomValidity('Amount cannot be negative');
        } else if (amount > 999999999.99) {
          event.target.setCustomValidity('Amount exceeds maximum allowed value');
        } else {
          event.target.setCustomValidity('');
        }
      }
      
      // Update the model with cleaned value
      this.questionnaireData[fieldName] = numericValue;
    },
    
    validateHoursInput(fieldName, event) {
      const value = event.target.value;
      
      // Allow empty values (optional fields)
      if (!value || value === '') return;
      
      // Validate format
      const hoursPattern = /^[0-9]+(\.[0-9]{0,2})?$/;
      if (!hoursPattern.test(value)) {
        event.target.setCustomValidity('Please enter a valid number of hours (e.g., 8.5)');
      } else {
        const hours = parseFloat(value);
        if (hours < 0) {
          event.target.setCustomValidity('Hours cannot be negative');
        } else if (hours > 8760) {
          event.target.setCustomValidity('Hours exceeds reasonable maximum (8760 = 1 year)');
        } else {
          event.target.setCustomValidity('');
        }
      }
    },
    toggleSection(section) {
      this.expandedSections[section] = !this.expandedSections[section];
    },
    testEndpoints() {
      // Safety check for userIncidents array
      if (!this.userIncidents || !Array.isArray(this.userIncidents) || this.userIncidents.length === 0) {
        PopupService.error('No incidents available for testing');
        return;
      }
      
      const testId = this.userIncidents[0].id;
      const isAuditFinding = this.userIncidents[0].itemType === 'audit_finding';
      
      
      // Test endpoints
      const mitigationsEndpoint = isAuditFinding
        ? API_ENDPOINTS.AUDIT_FINDING_MITIGATIONS(testId)
        : API_ENDPOINTS.INCIDENT_MITIGATIONS(testId);
      
      const reviewEndpoint = isAuditFinding
        ? API_ENDPOINTS.AUDIT_FINDING_REVIEW_DATA(testId)
        : API_ENDPOINTS.INCIDENT_REVIEW_DATA(testId);
      
      // Test the mitigations endpoint
      axios.get(mitigationsEndpoint)
        .then(() => {
          PopupService.success('Mitigations endpoint test successful');
        })
        .catch(error => {
          PopupService.error(`Mitigations endpoint test failed: ${error.message}`);
        });
      
      // Test the review endpoint
      axios.get(reviewEndpoint)
        .then(() => {
          PopupService.success('Review endpoint test successful');
        })
        .catch(error => {
          PopupService.error(`Review endpoint test failed: ${error.message}`);
        });
    },
    handleFilesUploaded(uploadedFiles) {
      // Add uploaded files to the current mitigation step
      if (this.mitigationSteps[this.currentStep]) {
        if (!this.mitigationSteps[this.currentStep].files) {
          this.mitigationSteps[this.currentStep].files = [];
        }
        
        // Add uploaded files to the current mitigation step
        this.mitigationSteps[this.currentStep].files.push(...uploadedFiles);
        
        // Also update legacy fields for backward compatibility
        if (uploadedFiles.length > 0) {
          const firstFile = uploadedFiles[0];
          this.mitigationSteps[this.currentStep]['aws-file_link'] = firstFile['aws-file_link'];
          this.mitigationSteps[this.currentStep].fileName = firstFile.fileName;
        }
        
        // Force Vue to recognize the change by creating a new array
        this.mitigationSteps = [...this.mitigationSteps];
        
        // Update the status to completed if files are uploaded
        this.updateStepStatus(this.currentStep, 'Completed');
        
        console.log('Files uploaded successfully:', uploadedFiles);
        console.log('Updated mitigation steps:', this.mitigationSteps);
        
        // Show success message
        if (uploadedFiles.length > 0) {
          const message = uploadedFiles.length === 1 
            ? `File "${uploadedFiles[0].fileName}" uploaded successfully` 
            : `${uploadedFiles.length} files uploaded successfully`;
          
          // Use PopupService if available
          if (window.PopupService) {
            window.PopupService.success(message);
          } else {
            alert(message);
          }
        }
      }
    },
    formatFileSize(bytes) {
      if (!bytes) return '';
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    handleUserTaskClick(task) {
      if (task.actions === 'view') this.viewMitigations(task.id);
      else if (task.actions === 'resubmit') this.viewMitigations(task.id); // Could be a resubmit modal if needed
    },
    handleReviewerTaskClick(task) {
      if (task.actions === 'review') this.reviewMitigations(task);
      else if (task.actions === 'view') this.reviewMitigations(task);
    },
    async showLinkedEventDetails(linkedEvent) {
      if (linkedEvent) {
        // First, try to fetch enhanced document data for this specific linked event
        try {
          
          // Fetch enhanced linked evidence data
          const response = await axios.get(`/api/incidents/${this.selectedIncidentId}/linked-evidence/`);
          
          if (response.data && response.data.success && response.data.linked_evidence) {
            const enhancedLinkedEvidence = response.data.linked_evidence;
            
            // Find the matching evidence for this linked event
            const matchingEvidence = enhancedLinkedEvidence.find(evidence => {
              return evidence.id === linkedEvent.id || 
                     evidence.title === linkedEvent.title ||
                     (evidence.linkedRecordId && linkedEvent.linkedRecordId && 
                      evidence.linkedRecordId.toString() === linkedEvent.linkedRecordId.toString());
            });
            
            if (matchingEvidence && matchingEvidence.documents && matchingEvidence.documents.length > 0) {
              // Update the linkedEvent with enhanced document data
              linkedEvent.documents = matchingEvidence.documents;
              linkedEvent.document_count = matchingEvidence.documents.length;
              
              
              // Force Vue reactivity update to show documents in UI
              this.$forceUpdate();
              
              // Show success message that documents are now loaded
              PopupService.success(`Documents loaded successfully! ${matchingEvidence.documents.length} document(s) are now available for download.`);
            } else {
              // No enhanced documents found
              PopupService.info('No additional documents found for this linked event.');
            }
          } else {
            // Fallback if API call fails
            PopupService.warning('Unable to fetch document details. Please try refreshing.');
          }
        } catch (error) {
          PopupService.error('Error loading documents. Please try again.');
        }
      }
    },
    async showLinkedEventDetailsFromStep(stepKey) {
      // Try to get linked event details from the files array first
      const step = this.mitigationSteps[stepKey];
      if (step && step.files && step.files.length > 0) {
        const linkedFile = step.files.find(file => file.type === 'linked_evidence');
        if (linkedFile && linkedFile.linkedEvent) {
          await this.showLinkedEventDetails(linkedFile.linkedEvent);
          return;
        }
      }
      
      // Fallback: show basic info from the step itself
      alert(`Linked Event: ${step.fileName}\n\nThis is a linked event from another system. Full details may not be available in legacy format.`);
    },
    async showLinkedEventDetailsFromMitigation(mitigation) {
      // Try to get linked event details from the files array first
      if (mitigation.files && mitigation.files.length > 0) {
        const linkedFile = mitigation.files.find(file => file.type === 'linked_evidence');
        if (linkedFile && linkedFile.linkedEvent) {
          await this.showLinkedEventDetails(linkedFile.linkedEvent);
          return;
        }
      }
      
      // Fallback: show basic info from the mitigation itself
      alert(`Linked Event: ${mitigation.fileName}\n\nThis is a linked event from another system. Full details may not be available in legacy format.`);
    },
    
    async fetchLinkedEvidenceDocuments() {
      if (!this.selectedIncidentId) return;
      
      try {
        
        const response = await axios.get(`/api/incidents/${this.selectedIncidentId}/linked-evidence/`);
        
        if (response.data && response.data.success && response.data.linked_evidence) {
          const enhancedLinkedEvidence = response.data.linked_evidence;
          
          // Update the mitigation steps with enhanced linked evidence data
          this.mitigationSteps.forEach(step => {
            if (step.files && step.files.length > 0) {
              step.files.forEach(file => {
                if (file.type === 'linked_evidence' && file.linkedEvent) {
                  // Find the enhanced data for this linked event using multiple matching criteria
                  let enhancedData = enhancedLinkedEvidence.find(evidence => {
                    // Try multiple matching strategies
                    const idMatch = evidence.id === file.linkedEvent.id;
                    const titleMatch = evidence.title === file.linkedEvent.title;
                    const recordIdMatch = evidence.linkedRecordId && file.linkedEvent.linkedRecordId && 
                                        evidence.linkedRecordId.toString() === file.linkedEvent.linkedRecordId.toString();
                    const stringIdMatch = evidence.id && file.linkedEvent.id && 
                                        evidence.id.toString() === file.linkedEvent.id.toString();
                    
                    
                    return idMatch || titleMatch || recordIdMatch || stringIdMatch;
                  });
                  
                  
                  // Force matching for Document Handling System events by ID pattern
                  if (!enhancedData && file.linkedEvent.source === 'Document Handling System') {
                    
                    // Try exact ID match first
                    enhancedData = enhancedLinkedEvidence.find(e => e.id === file.linkedEvent.id);
                    if (!enhancedData) {
                      // Try linkedRecordId match
                      enhancedData = enhancedLinkedEvidence.find(e => 
                        e.linkedRecordId && file.linkedEvent.linkedRecordId && 
                        e.linkedRecordId.toString() === file.linkedEvent.linkedRecordId.toString()
                      );
                    }
                    if (!enhancedData) {
                      // Try title match
                      enhancedData = enhancedLinkedEvidence.find(e => 
                        e.title === file.linkedEvent.title
                      );
                    }
                    if (!enhancedData) {
                      // Try partial title match for Document Handling
                      enhancedData = enhancedLinkedEvidence.find(e => 
                        e.source === 'Document Handling System' &&
                        e.title?.toLowerCase().includes(file.linkedEvent.title?.toLowerCase().split(' ').slice(-1)[0])
                      );
                    }
                    
                  }
                  
                  if (enhancedData) {
                    
                    // Update the linkedEvent with enhanced data including documents
                    const updatedLinkedEvent = {
                      ...file.linkedEvent,
                      ...enhancedData,
                      documents: enhancedData.documents || [],
                      document_count: enhancedData.document_count || enhancedData.documents?.length || 0
                    };
                    
                    // Replace the entire linkedEvent object to trigger Vue reactivity
                    file.linkedEvent = updatedLinkedEvent;
                    
                    // Also update the file object properties to ensure UI updates
                    if (enhancedData.documents && enhancedData.documents.length > 0) {
                      file.hasDocuments = true;
                      file.documentCount = enhancedData.documents.length;
                    }
                    
                    
                    // CRITICAL: Update the mitigation step itself to trigger Vue reactivity
                    const stepIndex = this.mitigationSteps.findIndex(s => s === step);
                    if (stepIndex !== -1) {
                      // Create new step object
                      const updatedStep = {
                        ...step,
                        files: step.files.map(f => f === file ? { ...file } : f)
                      };
                      
                      // Replace the step in the array
                      this.mitigationSteps.splice(stepIndex, 1, updatedStep);
                    }
                    
                  } else {
                    // Fallback: Ensure basic document structure exists
                    if (!file.linkedEvent.documents || file.linkedEvent.documents.length === 0) {
                      
                      // Create a basic document structure based on the file name
                      const fileName = file.linkedEvent.title || file.fileName || 'Unknown File';
                      const fallbackDocument = {
                        id: `fallback_${file.linkedEvent.id}`,
                        name: fileName,
                        fileName: fileName,
                        type: 'document',
                        size: 'Unknown',
                        url: '#',
                        isFallback: true
                      };
                      
                      // Update the linked event with fallback document
                      file.linkedEvent = {
                        ...file.linkedEvent,
                        documents: [fallbackDocument],
                        document_count: 1
                      };
                      
                      // Update file properties
                      file.hasDocuments = true;
                      file.documentCount = 1;
                      
                    }
                  }
                }
              });
            }
          });
          
          
          // Aggressive Vue reactivity - create completely new objects
          this.mitigationSteps = this.mitigationSteps.map(step => ({
            ...step,
            files: step.files ? step.files.map(file => ({ ...file })) : []
          }));
          
          // Multiple force updates
          this.$forceUpdate();
          this.$nextTick(() => {
            this.$forceUpdate();
            this.$nextTick(() => {
              this.$forceUpdate();
            });
          });
        }
      } catch (error) {
        // Error fetching enhanced linked evidence
      }
    },
    
    downloadLinkedDocument(evidenceId, documentIndex, docData) {
      try {
        // If document has direct s3_url, use that
        if (docData && docData.s3_url) {
          const link = document.createElement('a');
          link.href = docData.s3_url;
          link.download = docData.filename || 'document';
          link.target = '_blank';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          return;
        }
        
        // Otherwise, use backend download endpoint
        const userId = localStorage.getItem('user_id') || '1';
        const incidentId = this.selectedIncidentId;
        
        // Create download URL
        const downloadUrl = `/api/incidents/${incidentId}/linked-evidence/${evidenceId}/documents/${documentIndex}/download/?user_id=${userId}`;
        
        // Create a temporary link and click it to trigger download
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = docData.filename || 'document';
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
      } catch (error) {
        
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
      
      // Fetch fresh data from backend
      this.fetchLinkedEvidenceDocuments();
    },
    
    async forceUpdateDocuments(file) {
      
      try {
        // Fetch fresh evidence data from backend
        const response = await fetch(`/api/incidents/${this.selectedIncidentId}/linked-evidence/`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
          credentials: 'include', // Include cookies for session authentication
        });

        if (response.ok) {
          const data = await response.json();
          if (data.success && data.linked_evidence) {
            // Find the matching evidence item
            const matchingEvidence = data.linked_evidence.find(evidence => 
              evidence.id === file.linkedEvent.id || 
              evidence.title === file.linkedEvent.title
            );
            
            if (matchingEvidence && matchingEvidence.documents) {
              // Update the linkedEvent with fresh documents
              const updatedLinkedEvent = {
                ...file.linkedEvent,
                documents: matchingEvidence.documents,
                document_count: matchingEvidence.documents.length
              };
              
              // Replace the entire linkedEvent object
              file.linkedEvent = updatedLinkedEvent;
              
              // Force Vue update
              this.$forceUpdate();
              
              alert(`Force updated ${file.linkedEvent.title} with ${matchingEvidence.documents.length} documents from backend`);
            } else {
              alert('No matching evidence found for force update');
            }
          } else {
            alert('Failed to fetch evidence data from backend');
          }
        } else {
          alert('Failed to fetch evidence data from backend');
        }
      } catch (error) {
        alert('Error force updating documents: ' + error.message);
      }
    }
  }
}
</script>

<style scoped>
@import './IncidentUserTask.css';
</style> 