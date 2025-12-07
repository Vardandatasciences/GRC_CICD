<template>
  <div class="incident-ai-container" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <h1><i class="fas fa-robot"></i> AI-Powered Incident Document Ingestion</h1>
        <p class="subtitle">Upload documents and let AI extract and predict incident information automatically</p>
      </div>
    </div>

    <!-- Upload Section -->
    <div v-if="currentStep === 'upload'" class="upload-section">
      <div class="upload-card">
        <div class="upload-icon">
          <i class="fas fa-cloud-upload-alt"></i>
        </div>
        <h2>Upload Incident Document</h2>
        <p class="upload-subtext">Supported formats: PDF, DOCX, Excel (XLSX, XLS), TXT</p>
        <div class="upload-guidelines" aria-hidden="true">
          <div class="guide-item">
            <i class="fas fa-shield-alt"></i>
            <span>Secure & private</span>
          </div>
          <div class="guide-item">
            <i class="fas fa-file-medical"></i>
            <span>Clean text extraction</span>
          </div>
          <div class="guide-item">
            <i class="fas fa-magic"></i>
            <span>AI-assisted fields</span>
          </div>
        </div>
        
        <div class="file-input-wrapper">
          <input 
            type="file" 
            ref="fileInput" 
            @change="handleFileSelect" 
            accept=".pdf,.docx,.xlsx,.xls,.txt"
            id="fileUpload"
          />
          <label for="fileUpload" class="file-label" title="Click to select a file">
            <i class="fas fa-file-upload"></i>
            <span class="file-label-text">{{ selectedFile ? selectedFile.name : 'Choose File' }}</span>
          </label>
        </div>

        <button 
          @click="uploadAndProcess" 
          :disabled="!selectedFile || isProcessing"
          class="btn-primary"
        >
          <i class="fas fa-magic"></i>
          Process with AI
        </button>
      </div>
    </div>

    <!-- Processing Section -->
    <div v-if="currentStep === 'processing'" class="processing-section">
      <div class="processing-card">
        <div class="spinner-container">
          <div class="spinner"></div>
        </div>
        <h2>Processing Document...</h2>
        <p class="processing-text">{{ processingStatus }}</p>
        
        <div class="progress-container">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: processingProgress + '%' }"></div>
          </div>
          <span class="progress-text">{{ processingProgress }}%</span>
        </div>

        <div class="processing-steps">
          <div class="step" :class="{ active: currentProcessingStep >= 1, completed: currentProcessingStep > 1 }">
            <i class="fas fa-file-upload"></i>
            <span>Uploading</span>
          </div>
          <div class="step" :class="{ active: currentProcessingStep >= 2, completed: currentProcessingStep > 2 }">
            <i class="fas fa-search"></i>
            <span>Extracting</span>
          </div>
          <div class="step" :class="{ active: currentProcessingStep >= 3, completed: currentProcessingStep > 3 }">
            <i class="fas fa-brain"></i>
            <span>AI Processing</span>
          </div>
          <div class="step" :class="{ active: currentProcessingStep >= 4, completed: currentProcessingStep > 4 }">
            <i class="fas fa-check-circle"></i>
            <span>Complete</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Review Section -->
    <div v-if="currentStep === 'review'" class="review-section">
      <div class="review-header">
        <h2><i class="fas fa-edit"></i> Review Extracted Incidents</h2>
        <p>{{ extractedIncidents.length }} incident(s) found. Review and edit before saving.</p>
        <div class="ai-stats-panel">
          <div class="ai-stat-item">
            <i class="fas fa-robot"></i>
            <span class="stat-value">{{ getTotalAIFields() }}</span>
            <span class="stat-label">AI-Generated Fields</span>
          </div>
          <div class="ai-stat-item">
            <i class="fas fa-percentage"></i>
            <span class="stat-value">{{ getAverageConfidence() }}%</span>
            <span class="stat-label">Avg Confidence</span>
          </div>
          <div class="ai-stat-item legend">
            <i class="fas fa-robot"></i>
            <span class="stat-label">= AI Predicted with Confidence %</span>
          </div>
        </div>
      </div>

      <div class="incidents-container">
        <div v-for="(incident, index) in extractedIncidents" :key="index" class="incident-card">
          <div class="incident-card-header">
            <h3>Incident #{{ index + 1 }}</h3>
            <button @click="removeIncident(index)" class="btn-remove">
              <i class="fas fa-trash"></i>
            </button>
          </div>

          <div class="incident-form">
            <!-- Row 1: Title -->
            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Incident Title <span class="required">*</span>
                  <span v-if="isAIGenerated(incident, 'IncidentTitle')" class="ai-indicator" :title="getAITooltip(incident, 'IncidentTitle')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'IncidentTitle') }}%
                  </span>
                </label>
                <input 
                  v-model="incident.IncidentTitle" 
                  type="text" 
                  placeholder="Brief incident title" 
                  maxlength="255"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'IncidentTitle') }]"
                  required
                />
              </div>
            </div>

            <!-- Row 2: Description -->
            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Description
                  <span v-if="isAIGenerated(incident, 'Description')" class="ai-indicator" :title="getAITooltip(incident, 'Description')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'Description') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.Description" 
                  placeholder="Detailed incident description"
                  rows="4"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'Description') }]"
                ></textarea>
              </div>
            </div>

            <!-- Row 3: Category and Status -->
            <div class="form-row">
              <div class="form-group">
                <label>
                  Incident Category
                  <span v-if="isAIGenerated(incident, 'IncidentCategory')" class="ai-indicator" :title="getAITooltip(incident, 'IncidentCategory')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'IncidentCategory') }}%
                  </span>
                </label>
                <select v-model="incident.IncidentCategory" :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'IncidentCategory') }]">
                  <option value="">Select Category</option>
                  <option value="Security Breach">Security Breach</option>
                  <option value="Data Loss">Data Loss</option>
                  <option value="System Outage">System Outage</option>
                  <option value="Compliance Violation">Compliance Violation</option>
                  <option value="Operational Failure">Operational Failure</option>
                  <option value="Third-Party Issue">Third-Party Issue</option>
                  <option value="Human Error">Human Error</option>
                  <option value="Natural Disaster">Natural Disaster</option>
                  <option value="Cyber Attack">Cyber Attack</option>
                  <option value="Privacy Incident">Privacy Incident</option>
                  <option value="Safety Incident">Safety Incident</option>
                  <option value="Financial Loss">Financial Loss</option>
                </select>
              </div>

              <div class="form-group">
                <label>
                  Status
                  <span v-if="isAIGenerated(incident, 'Status')" class="ai-indicator" :title="getAITooltip(incident, 'Status')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'Status') }}%
                  </span>
                </label>
                <select v-model="incident.Status" :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'Status') }]">
                  <option value="New">New</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Under Investigation">Under Investigation</option>
                  <option value="Resolved">Resolved</option>
                  <option value="Closed">Closed</option>
                  <option value="Escalated">Escalated</option>
                  <option value="Risk Mitigated">Risk Mitigated</option>
                </select>
              </div>
            </div>

            <!-- Row 4: Criticality and Priority -->
            <div class="form-row">
              <div class="form-group">
                <label>
                  Criticality
                  <span v-if="isAIGenerated(incident, 'Criticality')" class="ai-indicator" :title="getAITooltip(incident, 'Criticality')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'Criticality') }}%
                  </span>
                </label>
                <select v-model="incident.Criticality" :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'Criticality') }]">
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>

              <div class="form-group">
                <label>
                  Risk Priority
                  <span v-if="isAIGenerated(incident, 'RiskPriority')" class="ai-indicator" :title="getAITooltip(incident, 'RiskPriority')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'RiskPriority') }}%
                  </span>
                </label>
                <select v-model="incident.RiskPriority" :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'RiskPriority') }]">
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
            </div>

            <!-- Row 5: Origin and Risk Category -->
            <div class="form-row">
              <div class="form-group">
                <label>
                  Origin
                  <span v-if="isAIGenerated(incident, 'Origin')" class="ai-indicator" :title="getAITooltip(incident, 'Origin')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'Origin') }}%
                  </span>
                </label>
                <select v-model="incident.Origin" :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'Origin') }]">
                  <option value="MANUAL">Manual</option>
                  <option value="AUDIT_FINDING">Audit Finding</option>
                  <option value="AUTOMATED">Automated</option>
                  <option value="EXTERNAL_REPORT">External Report</option>
                  <option value="INTERNAL_DETECTION">Internal Detection</option>
                </select>
              </div>

              <div class="form-group">
                <label>
                  Risk Category
                  <span v-if="isAIGenerated(incident, 'RiskCategory')" class="ai-indicator" :title="getAITooltip(incident, 'RiskCategory')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'RiskCategory') }}%
                  </span>
                </label>
                <select v-model="incident.RiskCategory" :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'RiskCategory') }]">
                  <option value="">Select Category</option>
                  <option value="Operational">Operational</option>
                  <option value="Financial">Financial</option>
                  <option value="Strategic">Strategic</option>
                  <option value="Compliance">Compliance</option>
                  <option value="Technical">Technical</option>
                  <option value="Reputational">Reputational</option>
                  <option value="Information Security">Information Security</option>
                  <option value="Process Risk">Process Risk</option>
                  <option value="Third-Party">Third-Party</option>
                  <option value="Regulatory">Regulatory</option>
                  <option value="Governance">Governance</option>
                </select>
              </div>
            </div>

            <!-- Row 6: Affected Business Unit and Geographic Location -->
            <div class="form-row">
              <div class="form-group">
                <label>
                  Affected Business Unit
                  <span v-if="isAIGenerated(incident, 'AffectedBusinessUnit')" class="ai-indicator" :title="getAITooltip(incident, 'AffectedBusinessUnit')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'AffectedBusinessUnit') }}%
                  </span>
                </label>
                <input 
                  v-model="incident.AffectedBusinessUnit" 
                  type="text" 
                  placeholder="Business unit impacted"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'AffectedBusinessUnit') }]"
                />
              </div>

              <div class="form-group">
                <label>
                  Geographic Location
                  <span v-if="isAIGenerated(incident, 'GeographicLocation')" class="ai-indicator" :title="getAITooltip(incident, 'GeographicLocation')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'GeographicLocation') }}%
                  </span>
                </label>
                <input 
                  v-model="incident.GeographicLocation" 
                  type="text" 
                  placeholder="Location where incident occurred"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'GeographicLocation') }]"
                />
              </div>
            </div>

            <!-- Row 7: Systems and Cost -->
            <div class="form-row">
              <div class="form-group">
                <label>
                  Systems/Assets Involved
                  <span v-if="isAIGenerated(incident, 'SystemsAssetsInvolved')" class="ai-indicator" :title="getAITooltip(incident, 'SystemsAssetsInvolved')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'SystemsAssetsInvolved') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.SystemsAssetsInvolved" 
                  placeholder="Systems and assets affected"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'SystemsAssetsInvolved') }]"
                ></textarea>
              </div>

              <div class="form-group">
                <label>
                  Cost of Incident
                  <span v-if="isAIGenerated(incident, 'CostOfIncident')" class="ai-indicator" :title="getAITooltip(incident, 'CostOfIncident')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'CostOfIncident') }}%
                  </span>
                </label>
                <input 
                  v-model="incident.CostOfIncident" 
                  type="text" 
                  placeholder="$0 or Not assessed"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'CostOfIncident') }]"
                />
              </div>
            </div>

            <!-- Row 8: Initial Impact Assessment -->
            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Initial Impact Assessment
                  <span v-if="isAIGenerated(incident, 'InitialImpactAssessment')" class="ai-indicator" :title="getAITooltip(incident, 'InitialImpactAssessment')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'InitialImpactAssessment') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.InitialImpactAssessment" 
                  placeholder="Initial assessment of impact"
                  rows="3"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'InitialImpactAssessment') }]"
                ></textarea>
              </div>
            </div>

            <!-- Row 9: Possible Damage -->
            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Possible Damage
                  <span v-if="isAIGenerated(incident, 'PossibleDamage')" class="ai-indicator" :title="getAITooltip(incident, 'PossibleDamage')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'PossibleDamage') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.PossibleDamage" 
                  placeholder="Potential damages and consequences"
                  rows="3"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'PossibleDamage') }]"
                ></textarea>
              </div>
            </div>

            <!-- Row 10: Contacts -->
            <div class="form-row">
              <div class="form-group">
                <label>
                  Internal Contacts
                  <span v-if="isAIGenerated(incident, 'InternalContacts')" class="ai-indicator" :title="getAITooltip(incident, 'InternalContacts')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'InternalContacts') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.InternalContacts" 
                  placeholder="Internal personnel involved"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'InternalContacts') }]"
                ></textarea>
              </div>

              <div class="form-group">
                <label>
                  External Parties Involved
                  <span v-if="isAIGenerated(incident, 'ExternalPartiesInvolved')" class="ai-indicator" :title="getAITooltip(incident, 'ExternalPartiesInvolved')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'ExternalPartiesInvolved') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.ExternalPartiesInvolved" 
                  placeholder="External organizations involved"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'ExternalPartiesInvolved') }]"
                ></textarea>
              </div>
            </div>

            <!-- Row 11: Policies Violated -->
            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Policies/Procedures Violated
                  <span v-if="isAIGenerated(incident, 'RelevantPoliciesProceduresViolated')" class="ai-indicator" :title="getAITooltip(incident, 'RelevantPoliciesProceduresViolated')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'RelevantPoliciesProceduresViolated') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.RelevantPoliciesProceduresViolated" 
                  placeholder="Policies or procedures violated"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'RelevantPoliciesProceduresViolated') }]"
                ></textarea>
              </div>
            </div>

            <!-- Row 12: Control Failures -->
            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Control Failures
                  <span v-if="isAIGenerated(incident, 'ControlFailures')" class="ai-indicator" :title="getAITooltip(incident, 'ControlFailures')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'ControlFailures') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.ControlFailures" 
                  placeholder="Controls that failed or were bypassed"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'ControlFailures') }]"
                ></textarea>
              </div>
            </div>

            <!-- Row 13: Lessons Learned and Classification -->
            <div class="form-row">
              <div class="form-group">
                <label>
                  Lessons Learned
                  <span v-if="isAIGenerated(incident, 'LessonsLearned')" class="ai-indicator" :title="getAITooltip(incident, 'LessonsLearned')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'LessonsLearned') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.LessonsLearned" 
                  placeholder="Key insights and learnings"
                  rows="3"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'LessonsLearned') }]"
                ></textarea>
              </div>

              <div class="form-group">
                <label>
                  Incident Classification
                  <span v-if="isAIGenerated(incident, 'IncidentClassification')" class="ai-indicator" :title="getAITooltip(incident, 'IncidentClassification')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'IncidentClassification') }}%
                  </span>
                </label>
                <input 
                  v-model="incident.IncidentClassification" 
                  type="text" 
                  placeholder="Classification code or category"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'IncidentClassification') }]"
                />
              </div>
            </div>

            <!-- Row 14: Comments -->
            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Comments
                  <span v-if="isAIGenerated(incident, 'Comments')" class="ai-indicator" :title="getAITooltip(incident, 'Comments')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(incident, 'Comments') }}%
                  </span>
                </label>
                <textarea 
                  v-model="incident.Comments" 
                  placeholder="Additional notes or observations"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(incident, 'Comments') }]"
                ></textarea>
              </div>
            </div>

            <!-- Row 15: Boolean Flags -->
            <div class="form-row">
              <div class="form-group checkbox-group">
                <label>
                  <input type="checkbox" v-model="incident.RepeatedNot" />
                  <span>Repeated Incident</span>
                  <span v-if="isAIGenerated(incident, 'RepeatedNot')" class="ai-indicator" :title="getAITooltip(incident, 'RepeatedNot')">
                    <i class="fas fa-robot"></i> AI
                  </span>
                </label>
              </div>

              <div class="form-group checkbox-group">
                <label>
                  <input type="checkbox" v-model="incident.ReopenedNot" />
                  <span>Reopened Incident</span>
                  <span v-if="isAIGenerated(incident, 'ReopenedNot')" class="ai-indicator" :title="getAITooltip(incident, 'ReopenedNot')">
                    <i class="fas fa-robot"></i> AI
                  </span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="review-actions">
        <button @click="currentStep = 'upload'" class="btn-secondary">
          <i class="fas fa-arrow-left"></i>
          Back to Upload
        </button>
        <button @click="saveAllIncidents" :disabled="isSaving" class="btn-primary">
          <i class="fas fa-save"></i>
          {{ isSaving ? 'Saving...' : 'Save All Incidents' }}
        </button>
      </div>
    </div>

    <!-- Success Section -->
    <div v-if="currentStep === 'success'" class="success-section">
      <div class="success-card">
        <div class="success-icon">
          <i class="fas fa-check-circle"></i>
        </div>
        <h2>Success!</h2>
        <p>{{ savedCount }} incident(s) have been successfully saved to the database.</p>
        
        <div class="success-actions">
          <button @click="resetToUpload" class="btn-secondary">
            <i class="fas fa-plus"></i>
            Upload Another
          </button>
          <button @click="navigateToIncidents" class="btn-primary">
            <i class="fas fa-list"></i>
            View Incidents
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { API_ENDPOINTS } from '@/config/api';

export default {
  name: 'IncidentAIImport',
  
  data() {
    return {
      selectedFile: null,
      isProcessing: false,
      isSaving: false,
      currentStep: 'upload', // 'upload', 'processing', 'review', 'success'
      extractedIncidents: [],
      savedCount: 0,
      processingStatus: 'Initializing...',
      processingProgress: 0,
      currentProcessingStep: 0,
      isSidebarCollapsed: false
    };
  },

  mounted() {
    this.checkSidebarState();
    
    document.addEventListener('click', (event) => {
      if (event.target.closest('.toggle') || event.target.closest('.expand-button')) {
        setTimeout(() => {
          this.checkSidebarState();
        }, 300);
      }
    });

    // Load processing state on component mount
    this.loadProcessingState();
    this.resumeProcessingIfNeeded();
  },

  methods: {
    // Persistent state management
    saveProcessingState() {
      const state = {
        currentStep: this.currentStep,
        isProcessing: this.isProcessing,
        processingStatus: this.processingStatus,
        processingProgress: this.processingProgress,
        currentProcessingStep: this.currentProcessingStep,
        extractedIncidents: this.extractedIncidents,
        selectedFile: this.selectedFile ? { name: this.selectedFile.name, size: this.selectedFile.size } : null,
        timestamp: Date.now()
      };
      try {
        sessionStorage.setItem('incident_ai_processing_state', JSON.stringify(state));
        console.log('💾 Incident AI processing state saved:', state);
      } catch (error) {
        console.error('❌ Failed to save incident AI processing state:', error);
      }
    },

    loadProcessingState() {
      try {
        const savedState = sessionStorage.getItem('incident_ai_processing_state');
        if (!savedState) {
          console.log('❌ No saved incident AI state found');
          return false;
        }

        const state = JSON.parse(savedState);

        // Check if state is not too old (24 hours max)
        const maxAge = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
        if (Date.now() - state.timestamp > maxAge) {
          console.log('❌ Saved incident AI state is too old, clearing');
          sessionStorage.removeItem('incident_ai_processing_state');
          return false;
        }

        // Restore state
        this.currentStep = state.currentStep || 'upload';
        this.isProcessing = state.isProcessing || false;
        this.processingStatus = state.processingStatus || 'Initializing...';
        this.processingProgress = state.processingProgress || 0;
        this.currentProcessingStep = state.currentProcessingStep || 0;
        this.extractedIncidents = state.extractedIncidents || [];
        this.selectedFile = null; // Don't restore file object, just clear it

        console.log('✅ Incident AI processing state restored:', state);
        return true;
      } catch (error) {
        console.error('❌ Failed to load incident AI processing state:', error);
        sessionStorage.removeItem('incident_ai_processing_state');
        return false;
      }
    },

    clearProcessingState() {
      try {
        sessionStorage.removeItem('incident_ai_processing_state');
        console.log('🗑️ Incident AI processing state cleared');
      } catch (error) {
        console.error('❌ Failed to clear incident AI processing state:', error);
      }
    },

    resumeProcessingIfNeeded() {
      if (this.currentStep === 'processing' && this.isProcessing) {
        console.log('🔄 Resuming incident AI processing from step:', this.currentProcessingStep);
        // Continue from where it left off - progress will update naturally
        this.$notify({
          type: 'info',
          title: 'Resuming',
          text: `Resuming incident processing from ${this.processingProgress}%`
        });
      } else if (this.currentStep === 'review' && this.extractedIncidents.length > 0) {
        console.log('🔄 Incident AI review data restored');
        this.$notify({
          type: 'info',
          title: 'Data Restored',
          text: `Restored ${this.extractedIncidents.length} incident(s) for review`
        });
      }
    },

    handleFileSelect(event) {
      const file = event.target.files[0];
      if (file) {
        const validTypes = [
          'application/pdf',
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          'application/msword',
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          'application/vnd.ms-excel',
          'text/plain'
        ];
        
        if (validTypes.includes(file.type) || 
            file.name.match(/\.(pdf|docx|doc|xlsx|xls|txt)$/i)) {
          this.selectedFile = file;
        } else {
          this.$notify({
            type: 'error',
            title: 'Invalid File Type',
            text: 'Please upload a PDF, DOCX, Excel, or TXT file.'
          });
          event.target.value = '';
        }
      }
    },

    async uploadAndProcess() {
      if (!this.selectedFile) {
        this.$notify({
          type: 'error',
          title: 'No File Selected',
          text: 'Please select a file to upload.'
        });
        return;
      }

      this.isProcessing = true;
      this.currentStep = 'processing';
      this.processingProgress = 0;
      this.currentProcessingStep = 1;
      this.processingStatus = 'Uploading document...';
      this.saveProcessingState();

      const formData = new FormData();
      formData.append('file', this.selectedFile);
      formData.append('user_id', localStorage.getItem('user_id') || '1');

      try {
        this.updateProgress(20, 'Document uploaded successfully...');
        this.currentProcessingStep = 2;
        this.saveProcessingState();

        const response = await axios.post(
          API_ENDPOINTS.INCIDENT_AI_UPLOAD,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            timeout: 300000
          }
        );

        this.updateProgress(50, 'Extracting text from document...');
        this.currentProcessingStep = 3;
        this.saveProcessingState();

        await this.delay(1000);
        this.updateProgress(75, 'AI is analyzing and generating incident data...');
        this.saveProcessingState();

        await this.delay(1500);
        this.updateProgress(100, 'Processing complete!');
        this.currentProcessingStep = 4;
        this.saveProcessingState();

        if (response.data.status === 'success') {
          const incidents = response.data.incidents || [];
          
          console.log('🔍 DEBUG: Raw incidents from backend:', JSON.stringify(incidents[0]?._meta, null, 2));
          
          this.extractedIncidents = incidents.map((incident, idx) => {
            const meta = incident._meta || {};
            const perField = meta.per_field || {};
            
            const aiFieldsList = Object.keys(perField).filter(k => perField[k]?.source === 'AI_GENERATED');
            const extractedFieldsList = Object.keys(perField).filter(k => perField[k]?.source === 'EXTRACTED');
            
            console.log(`📋 Incident ${idx + 1} Metadata Summary:`);
            console.log(`   ✓ Total fields with metadata: ${Object.keys(perField).length}`);
            console.log(`   🤖 AI Generated: ${aiFieldsList.length} fields`);
            console.log(`   📄 Extracted: ${extractedFieldsList.length} fields`);
            console.log(`   🎯 Sample AI fields:`, aiFieldsList.slice(0, 5));
            
            if (aiFieldsList.length === 0) {
              console.error('❌ CRITICAL: No AI-generated fields found! Check backend metadata generation.');
            }
            
            // Create mapped incident with proper structure
            const mappedIncident = {
              ...incident,
              _meta: meta,
              _perField: perField
            };
            
            // Log sample field to verify structure
            if (perField['IncidentTitle']) {
              console.log(`   📝 Sample: IncidentTitle metadata:`, perField['IncidentTitle']);
            }
            
            return mappedIncident;
          });

          // Enable debug mode for first render
          window.aiDebugMode = true;
          setTimeout(() => { window.aiDebugMode = false; }, 5000);

          console.log('✅ Extracted incidents ready for display');

          await this.delay(500);
          this.currentStep = 'review';
          this.isProcessing = false;
          this.saveProcessingState();

          // Count AI-generated fields
          const aiFieldsCount = this.extractedIncidents.reduce((count, inc) => {
            const aiFields = Object.keys(inc._perField || {}).filter(
              k => inc._perField[k]?.source === 'AI_GENERATED'
            );
            return count + aiFields.length;
          }, 0);

          console.log(`🤖 Total AI-generated fields across all incidents: ${aiFieldsCount}`);

          this.$notify({
            type: 'success',
            title: 'AI Processing Complete',
            text: `Extracted ${this.extractedIncidents.length} incident(s) with ${aiFieldsCount} AI-generated fields. Look for 🤖 icons showing AI predictions with confidence scores!`
          });
        } else {
          throw new Error(response.data.message || 'Processing failed');
        }
      } catch (error) {
        console.error('Error processing document:', error);
        this.isProcessing = false;
        this.currentStep = 'upload';
        this.clearProcessingState();
        
        this.$notify({
          type: 'error',
          title: 'Processing Failed',
          text: error.response?.data?.message || error.message || 'Failed to process document. Please try again.'
        });
      }
    },

    isAIGenerated(incident, fieldName) {
      // Robust check for AI-generated fields
      const perField = incident._perField || {};
      const fieldInfo = perField[fieldName];
      
      if (!fieldInfo) {
        console.warn(`⚠️  No metadata for field '${fieldName}' - check backend response`);
        return false;
      }
      
      const isAI = fieldInfo.source === 'AI_GENERATED';
      
      // Debug log for every field to ensure we catch issues
      if (window.aiDebugMode || !window.aiFieldsLogged) {
        console.log(`🔍 AI Check '${fieldName}':`, {
          source: fieldInfo.source,
          isAI: isAI,
          confidence: fieldInfo.confidence,
          hasValue: !!incident[fieldName]
        });
      }
      
      return isAI;
    },

    getAITooltip(incident, fieldName) {
      const perField = incident._perField || {};
      const fieldInfo = perField[fieldName];
      if (fieldInfo && fieldInfo.source === 'AI_GENERATED') {
        const confidence = Math.round((fieldInfo.confidence || 0.75) * 100);
        const rationale = fieldInfo.rationale || 'AI analyzed the document and predicted this value';
        
        // Create rich tooltip
        let tooltip = `🤖 AI GENERATED FIELD\n`;
        tooltip += `━━━━━━━━━━━━━━━━━━━━\n\n`;
        tooltip += `✓ Confidence Score: ${confidence}%\n\n`;
        tooltip += `📝 Reasoning:\n${rationale}\n\n`;
        tooltip += `━━━━━━━━━━━━━━━━━━━━\n`;
        tooltip += `💡 Tip: You can edit this value if needed before saving.`;
        
        return tooltip;
      }
      return '';
    },

    getConfidencePercent(incident, fieldName) {
      const perField = incident._perField || {};
      const fieldInfo = perField[fieldName];
      if (fieldInfo && fieldInfo.source === 'AI_GENERATED') {
        const confidence = fieldInfo.confidence || 0.75;
        return Math.round(confidence * 100);
      }
      return 75; // Default if metadata missing but field is AI-generated
    },

    updateProgress(percent, status) {
      this.processingProgress = percent;
      this.processingStatus = status;
    },

    delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    },

    removeIncident(index) {
      if (confirm('Are you sure you want to remove this incident?')) {
        this.extractedIncidents.splice(index, 1);
      }
    },

    async saveAllIncidents() {
      const invalidIncidents = this.extractedIncidents.filter(inc => !inc.IncidentTitle);
      if (invalidIncidents.length > 0) {
        this.$notify({
          type: 'error',
          title: 'Validation Error',
          text: 'All incidents must have a title.'
        });
        return;
      }

      this.isSaving = true;
      this.saveProcessingState();

      try {
        const cleanIncidents = this.extractedIncidents.map(inc => {
          // eslint-disable-next-line no-unused-vars
          const { _meta, _perField, ...cleanInc } = inc;
          return cleanInc;
        });

        const response = await axios.post(
          API_ENDPOINTS.INCIDENT_AI_SAVE,
          {
            incidents: cleanIncidents,
            user_id: localStorage.getItem('user_id') || '1'
          },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
              'Content-Type': 'application/json'
            }
          }
        );

        if (response.data.status === 'success') {
          this.savedCount = response.data.saved?.length || this.extractedIncidents.length;
          this.currentStep = 'success';
          this.clearProcessingState();
          
          this.$notify({
            type: 'success',
            title: 'Success',
            text: `Successfully saved ${this.savedCount} incident(s) to the database.`
          });
        } else {
          throw new Error(response.data.message || 'Save failed');
        }
      } catch (error) {
        console.error('Error saving incidents:', error);
        this.$notify({
          type: 'error',
          title: 'Save Failed',
          text: error.response?.data?.message || error.message || 'Failed to save incidents. Please try again.'
        });
      } finally {
        this.isSaving = false;
      }
    },

    resetToUpload() {
      this.selectedFile = null;
      this.extractedIncidents = [];
      this.savedCount = 0;
      this.processingProgress = 0;
      this.currentProcessingStep = 0;
      this.currentStep = 'upload';
      this.clearProcessingState();
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = '';
      }
    },

    navigateToIncidents() {
      this.$router.push('/incident/incident');
    },

    checkSidebarState() {
      const sidebar = document.querySelector('.sidebar');
      if (sidebar) {
        this.isSidebarCollapsed = sidebar.classList.contains('collapsed');
      }
    },

    getTotalAIFields() {
      let total = 0;
      this.extractedIncidents.forEach(incident => {
        const perField = incident._perField || {};
        const aiFields = Object.keys(perField).filter(k => perField[k]?.source === 'AI_GENERATED');
        total += aiFields.length;
      });
      return total;
    },

    getAverageConfidence() {
      let sum = 0;
      let count = 0;
      this.extractedIncidents.forEach(incident => {
        const perField = incident._perField || {};
        Object.keys(perField).forEach(fieldName => {
          const fieldInfo = perField[fieldName];
          if (fieldInfo?.source === 'AI_GENERATED' && fieldInfo.confidence) {
            sum += fieldInfo.confidence;
            count++;
          }
        });
      });
      return count > 0 ? Math.round((sum / count) * 100) : 0;
    }
  }
};
</script>

<style scoped src="./incident_ai_import.css"></style>
