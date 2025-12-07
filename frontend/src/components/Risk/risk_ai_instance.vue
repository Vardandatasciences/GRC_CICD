<template>
  <div class="risk-instance-ai-container" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <h1><i class="fas fa-robot"></i> AI-Powered Risk Instance Document Ingestion</h1>
        <p class="subtitle">Upload documents and let AI extract and predict risk instance information automatically</p>
      </div>
    </div>

    <!-- Upload Section -->
    <div v-if="currentStep === 'upload'" class="upload-section">
      <div class="upload-card">
        <h2>Upload Risk Instance Document</h2>
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
          <label for="fileUpload" class="file-label" title="Click to select a file">
            <input 
              type="file" 
              ref="fileInput" 
              @change="handleFileSelect" 
              accept=".pdf,.docx,.xlsx,.xls,.txt"
              id="fileUpload"
            />
            <i class="fas fa-file-upload"></i>
            <span class="file-label-text">{{ selectedFile ? selectedFile.name : 'Choose File' }}</span>
          </label>
          
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
        <h2><i class="fas fa-edit"></i> Review Extracted Risk Instances</h2>
        <p>{{ extractedRiskInstances.length }} risk instance(s) found. Review and edit before saving.</p>
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

      <div class="risks-container">
        <div v-for="(riskInstance, index) in extractedRiskInstances" :key="index" class="risk-card">
          <div class="risk-card-header">
            <h3>Risk Instance #{{ index + 1 }}</h3>
            <button @click="removeRiskInstance(index)" class="btn-remove">
              <i class="fas fa-trash"></i>
            </button>
          </div>

          <div class="risk-form">
            <div class="form-row">
              <div class="form-group">
                <label>
                  Risk Title <span class="required">*</span>
                  <span v-if="isAIGenerated(riskInstance, 'RiskTitle')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskTitle')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskTitle') }}%
                  </span>
                </label>
                <input 
                  v-model="riskInstance.RiskTitle" 
                  type="text" 
                  placeholder="Enter risk instance title"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskTitle') }]"
                />
              </div>
              <div class="form-group">
                <label>
                  Category
                  <span v-if="isAIGenerated(riskInstance, 'Category')" class="ai-indicator" :title="getAITooltip(riskInstance, 'Category')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'Category') }}%
                  </span>
                </label>
                <input 
                  v-model="riskInstance.Category" 
                  type="text" 
                  placeholder="e.g., Operational, Financial"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'Category') }]"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Criticality
                  <span v-if="isAIGenerated(riskInstance, 'Criticality')" class="ai-indicator" :title="getAITooltip(riskInstance, 'Criticality')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'Criticality') }}%
                  </span>
                </label>
                <select v-model="riskInstance.Criticality" :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'Criticality') }]">
                  <option value="">Select Criticality</option>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
              <div class="form-group">
                <label>
                  Risk Priority
                  <span v-if="isAIGenerated(riskInstance, 'RiskPriority')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskPriority')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskPriority') }}%
                  </span>
                </label>
                <select v-model="riskInstance.RiskPriority" :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskPriority') }]">
                  <option value="">Select Priority</option>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Origin
                  <span v-if="isAIGenerated(riskInstance, 'Origin')" class="ai-indicator" :title="getAITooltip(riskInstance, 'Origin')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'Origin') }}%
                  </span>
                </label>
                <select v-model="riskInstance.Origin" :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'Origin') }]">
                  <option value="">Select Origin</option>
                  <option value="Internal">Internal</option>
                  <option value="External">External</option>
                  <option value="Third-Party">Third-Party</option>
                  <option value="Regulatory">Regulatory</option>
                  <option value="Market">Market</option>
                  <option value="Operational">Operational</option>
                </select>
              </div>
              <div class="form-group">
                <label>
                  Risk Owner
                  <span v-if="isAIGenerated(riskInstance, 'RiskOwner')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskOwner')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskOwner') }}%
                  </span>
                </label>
                <input 
                  v-model="riskInstance.RiskOwner" 
                  type="text" 
                  placeholder="e.g., Risk Manager, IT Department"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskOwner') }]"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Risk Description
                  <span v-if="isAIGenerated(riskInstance, 'RiskDescription')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskDescription')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskDescription') }}%
                  </span>
                </label>
                <textarea 
                  v-model="riskInstance.RiskDescription" 
                  placeholder="Detailed description of the risk instance"
                  rows="3"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskDescription') }]"
                ></textarea>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Possible Damage
                  <span v-if="isAIGenerated(riskInstance, 'PossibleDamage')" class="ai-indicator" :title="getAITooltip(riskInstance, 'PossibleDamage')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'PossibleDamage') }}%
                  </span>
                </label>
                <textarea 
                  v-model="riskInstance.PossibleDamage" 
                  placeholder="What damage could this risk instance cause?"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'PossibleDamage') }]"
                ></textarea>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Business Impact
                  <span v-if="isAIGenerated(riskInstance, 'BusinessImpact')" class="ai-indicator" :title="getAITooltip(riskInstance, 'BusinessImpact')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'BusinessImpact') }}%
                  </span>
                </label>
                <textarea 
                  v-model="riskInstance.BusinessImpact" 
                  placeholder="Business impact description"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'BusinessImpact') }]"
                ></textarea>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Risk Likelihood (1-10)
                  <span v-if="isAIGenerated(riskInstance, 'RiskLikelihood')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskLikelihood')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskLikelihood') }}%
                  </span>
                </label>
                <input 
                  v-model.number="riskInstance.RiskLikelihood" 
                  type="number" 
                  min="1" 
                  max="10"
                  placeholder="1-10"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskLikelihood') }]"
                />
              </div>
              <div class="form-group">
                <label>
                  Risk Impact (1-10)
                  <span v-if="isAIGenerated(riskInstance, 'RiskImpact')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskImpact')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskImpact') }}%
                  </span>
                </label>
                <input 
                  v-model.number="riskInstance.RiskImpact" 
                  type="number" 
                  min="1" 
                  max="10"
                  placeholder="1-10"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskImpact') }]"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Risk Exposure Rating (0-100)
                  <span v-if="isAIGenerated(riskInstance, 'RiskExposureRating')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskExposureRating')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskExposureRating') }}%
                  </span>
                </label>
                <input 
                  v-model.number="riskInstance.RiskExposureRating" 
                  type="number" 
                  step="0.01"
                  min="0" 
                  max="100"
                  placeholder="0-100"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskExposureRating') }]"
                  readonly
                />
              </div>
              <div class="form-group">
                <label>
                  Appetite
                  <span v-if="isAIGenerated(riskInstance, 'Appetite')" class="ai-indicator" :title="getAITooltip(riskInstance, 'Appetite')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'Appetite') }}%
                  </span>
                </label>
                <select v-model="riskInstance.Appetite" :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'Appetite') }]">
                  <option value="">Select Appetite</option>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Risk Multiplier X
                  <span v-if="isAIGenerated(riskInstance, 'RiskMultiplierX')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskMultiplierX')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskMultiplierX') }}%
                  </span>
                </label>
                <input 
                  v-model.number="riskInstance.RiskMultiplierX" 
                  type="number" 
                  step="0.1"
                  min="0.1" 
                  max="2.0"
                  placeholder="0.1-2.0"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskMultiplierX') }]"
                />
              </div>
              <div class="form-group">
                <label>
                  Risk Multiplier Y
                  <span v-if="isAIGenerated(riskInstance, 'RiskMultiplierY')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskMultiplierY')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskMultiplierY') }}%
                  </span>
                </label>
                <input 
                  v-model.number="riskInstance.RiskMultiplierY" 
                  type="number" 
                  step="0.1"
                  min="0.1" 
                  max="2.0"
                  placeholder="0.1-2.0"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskMultiplierY') }]"
                />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Risk Type
                  <span v-if="isAIGenerated(riskInstance, 'RiskType')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskType')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskType') }}%
                  </span>
                </label>
                <select v-model="riskInstance.RiskType" :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskType') }]">
                  <option value="">Select Risk Type</option>
                  <option value="Current">Current</option>
                  <option value="Residual">Residual</option>
                  <option value="Inherent">Inherent</option>
                  <option value="Emerging">Emerging</option>
                  <option value="Accepted">Accepted</option>
                </select>
              </div>
              <div class="form-group">
                <label>
                  Risk Response Type
                  <span v-if="isAIGenerated(riskInstance, 'RiskResponseType')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskResponseType')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskResponseType') }}%
                  </span>
                </label>
                <select v-model="riskInstance.RiskResponseType" :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskResponseType') }]">
                  <option value="">Select Response Type</option>
                  <option value="Avoid">Avoid</option>
                  <option value="Mitigate">Mitigate</option>
                  <option value="Transfer">Transfer</option>
                  <option value="Accept">Accept</option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Risk Response Description
                  <span v-if="isAIGenerated(riskInstance, 'RiskResponseDescription')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskResponseDescription')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskResponseDescription') }}%
                  </span>
                </label>
                <textarea 
                  v-model="riskInstance.RiskResponseDescription" 
                  placeholder="Detailed description of risk response strategy"
                  rows="2"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskResponseDescription') }]"
                ></textarea>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>
                  Risk Status
                  <span v-if="isAIGenerated(riskInstance, 'RiskStatus')" class="ai-indicator" :title="getAITooltip(riskInstance, 'RiskStatus')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'RiskStatus') }}%
                  </span>
                </label>
                <select v-model="riskInstance.RiskStatus" :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'RiskStatus') }]">
                  <option value="">Select Status</option>
                  <option value="Not Assigned">Not Assigned</option>
                  <option value="Assigned">Assigned</option>
                  <option value="Approved">Approved</option>
                  <option value="Rejected">Rejected</option>
                </select>
              </div>
              <div class="form-group">
                <label>
                  Mitigation Status
                  <span v-if="isAIGenerated(riskInstance, 'MitigationStatus')" class="ai-indicator" :title="getAITooltip(riskInstance, 'MitigationStatus')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'MitigationStatus') }}%
                  </span>
                </label>
                <select v-model="riskInstance.MitigationStatus" :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'MitigationStatus') }]">
                  <option value="">Select Status</option>
                  <option value="Pending">Pending</option>
                  <option value="Yet to Start">Yet to Start</option>
                  <option value="Work In Progress">Work In Progress</option>
                  <option value="Revision Required by Reviewer">Revision Required by Reviewer</option>
                  <option value="Revision Required by User">Revision Required by User</option>
                  <option value="Completed">Completed</option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group full-width">
                <label>
                  Reviewer
                  <span v-if="isAIGenerated(riskInstance, 'Reviewer')" class="ai-indicator" :title="getAITooltip(riskInstance, 'Reviewer')">
                    <i class="fas fa-robot"></i> AI {{ getConfidencePercent(riskInstance, 'Reviewer') }}%
                  </span>
                </label>
                <input 
                  v-model="riskInstance.Reviewer" 
                  type="text" 
                  placeholder="Name or role of reviewer"
                  :class="['form-control', { 'ai-generated-field': isAIGenerated(riskInstance, 'Reviewer') }]"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="action-buttons">
        <button @click="cancelReview" class="btn-secondary">
          <i class="fas fa-times"></i> Cancel
        </button>
        <button @click="saveAllRiskInstances" :disabled="isSaving" class="btn-primary">
          <i class="fas fa-save"></i> {{ isSaving ? 'Saving...' : 'Save All Risk Instances' }}
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
        <p>{{ savedCount }} risk instance(s) have been successfully saved to the database.</p>
        <div class="action-buttons">
          <button @click="resetForm" class="btn-secondary">
            <i class="fas fa-plus"></i> Upload Another
          </button>
          <button @click="viewRiskInstances" class="btn-primary">
            <i class="fas fa-list"></i> View All Risk Instances
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { API_ENDPOINTS } from '../../config/api.js';

export default {
  name: 'RiskInstanceAIDocumentUpload',
  data() {
    return {
      currentStep: 'upload', // upload, processing, review, success
      selectedFile: null,
      isProcessing: false,
      isSaving: false,
      processingStatus: 'Initializing...',
      processingProgress: 0,
      currentProcessingStep: 0,
      extractedRiskInstances: [],
      savedCount: 0,
      isSidebarCollapsed: false,
    };
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
        extractedRiskInstances: this.extractedRiskInstances,
        selectedFile: this.selectedFile ? { name: this.selectedFile.name, size: this.selectedFile.size } : null,
        timestamp: Date.now()
      };
      try {
        sessionStorage.setItem('risk_instance_ai_processing_state', JSON.stringify(state));
        console.log('💾 Risk Instance AI processing state saved:', state);
      } catch (error) {
        console.error('❌ Failed to save risk instance AI processing state:', error);
      }
    },

    loadProcessingState() {
      try {
        const savedState = sessionStorage.getItem('risk_instance_ai_processing_state');
        if (!savedState) {
          console.log('❌ No saved risk instance AI state found');
          return false;
        }

        const state = JSON.parse(savedState);

        // Check if state is not too old (24 hours max)
        const maxAge = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
        if (Date.now() - state.timestamp > maxAge) {
          console.log('❌ Saved risk instance AI state is too old, clearing');
          sessionStorage.removeItem('risk_instance_ai_processing_state');
          return false;
        }

        // Restore state
        this.currentStep = state.currentStep || 'upload';
        this.isProcessing = state.isProcessing || false;
        this.processingStatus = state.processingStatus || 'Initializing...';
        this.processingProgress = state.processingProgress || 0;
        this.currentProcessingStep = state.currentProcessingStep || 0;
        this.extractedRiskInstances = state.extractedRiskInstances || [];
        this.selectedFile = null; // Don't restore file object, just clear it

        console.log('✅ Risk Instance AI processing state restored:', state);
        return true;
      } catch (error) {
        console.error('❌ Failed to load risk instance AI processing state:', error);
        sessionStorage.removeItem('risk_instance_ai_processing_state');
        return false;
      }
    },

    clearProcessingState() {
      try {
        sessionStorage.removeItem('risk_instance_ai_processing_state');
        console.log('🗑️ Risk Instance AI processing state cleared');
      } catch (error) {
        console.error('❌ Failed to clear risk instance AI processing state:', error);
      }
    },

    resumeProcessingIfNeeded() {
      if (this.currentStep === 'processing' && this.isProcessing) {
        console.log('🔄 Resuming risk instance AI processing from step:', this.currentProcessingStep);
        // Continue from where it left off - progress will update naturally
        this.$notify({
          type: 'info',
          title: 'Resuming',
          text: `Resuming risk instance processing from ${this.processingProgress}%`
        });
      } else if (this.currentStep === 'review' && this.extractedRiskInstances.length > 0) {
        console.log('🔄 Risk Instance AI review data restored');
        this.$notify({
          type: 'info',
          title: 'Data Restored',
          text: `Restored ${this.extractedRiskInstances.length} risk instance(s) for review`
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
          'application/vnd.ms-excel'
        ];
        
        if (validTypes.includes(file.type) || 
            file.name.match(/\.(pdf|docx|doc|xlsx|xls)$/i)) {
          this.selectedFile = file;
        } else {
          this.$notify({
            type: 'error',
            title: 'Invalid File Type',
            text: 'Please upload a PDF, DOCX, or Excel file.'
          });
          event.target.value = '';
        }
      }
    },

    async uploadAndProcess() {
      if (!this.selectedFile) return;

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
          API_ENDPOINTS.RISK_INSTANCE_AI_UPLOAD,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            timeout: 300000, // 5 minutes
            withCredentials: false
          }
        );

        this.updateProgress(50, 'Extracting text from document...');
        this.currentProcessingStep = 3;
        this.saveProcessingState();

        await this.delay(1000);
        this.updateProgress(75, 'AI is analyzing and generating risk instance data...');
        this.saveProcessingState();

        await this.delay(1500);
        this.updateProgress(100, 'Processing complete!');
        this.currentProcessingStep = 4;
        this.saveProcessingState();

        if (response.data.status === 'success') {
          const riskInstances = response.data.risk_instances || [];
          
          console.log('🔍 DEBUG: Raw risk instances from backend:', JSON.stringify(riskInstances[0]?._meta, null, 2));
          
          this.extractedRiskInstances = riskInstances.map((ri, idx) => {
            const meta = ri._meta || {};
            const perField = meta.per_field || {};
            
            const aiFieldsList = Object.keys(perField).filter(k => perField[k]?.source === 'AI_GENERATED');
            const extractedFieldsList = Object.keys(perField).filter(k => perField[k]?.source === 'EXTRACTED');
            
            console.log(`📋 Risk Instance ${idx + 1} Metadata Summary:`);
            console.log(`   ✓ Total fields with metadata: ${Object.keys(perField).length}`);
            console.log(`   🤖 AI Generated: ${aiFieldsList.length} fields`);
            console.log(`   📄 Extracted: ${extractedFieldsList.length} fields`);
            console.log(`   🎯 Sample AI fields:`, aiFieldsList.slice(0, 5));
            
            if (aiFieldsList.length === 0) {
              console.error('❌ CRITICAL: No AI-generated fields found! Check backend metadata generation.');
            }
            
            // Create mapped risk instance with proper structure
            const mappedRI = {
              ...ri,
              _meta: meta,
              _perField: perField
            };
            
            // Log sample field to verify structure
            if (perField['RiskTitle']) {
              console.log(`   📝 Sample: RiskTitle metadata:`, perField['RiskTitle']);
            }
            
            return mappedRI;
          });

          // Enable debug mode for first render
          window.aiDebugMode = true;
          setTimeout(() => { window.aiDebugMode = false; }, 5000);

          console.log('✅ Extracted risk instances ready for display');

          await this.delay(500);
          this.currentStep = 'review';
          this.isProcessing = false;
          this.saveProcessingState();

          // Count AI-generated fields
          const aiFieldsCount = this.extractedRiskInstances.reduce((count, ri) => {
            const aiFields = Object.keys(ri._perField || {}).filter(
              k => ri._perField[k]?.source === 'AI_GENERATED'
            );
            return count + aiFields.length;
          }, 0);

          console.log(`🤖 Total AI-generated fields across all risk instances: ${aiFieldsCount}`);

          this.$notify({
            type: 'success',
            title: 'AI Processing Complete',
            text: `Extracted ${this.extractedRiskInstances.length} risk instance(s) with ${aiFieldsCount} AI-generated fields. Look for 🤖 icons showing AI predictions with confidence scores!`
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

    isAIGenerated(riskInstance, fieldName) {
      // Robust check for AI-generated fields
      const perField = riskInstance._perField || {};
      const fieldInfo = perField[fieldName];
      
      if (!fieldInfo) {
        if (window.aiDebugMode) {
          console.warn(`⚠️  No metadata for field '${fieldName}' - check backend response`);
        }
        return false;
      }
      
      const isAI = fieldInfo.source === 'AI_GENERATED';
      
      // Debug log for every field to ensure we catch issues
      if (window.aiDebugMode || !window.aiFieldsLogged) {
        console.log(`🔍 AI Check '${fieldName}':`, {
          source: fieldInfo.source,
          isAI: isAI,
          confidence: fieldInfo.confidence,
          hasValue: !!riskInstance[fieldName]
        });
      }
      
      return isAI;
    },

    getAITooltip(riskInstance, fieldName) {
      const perField = riskInstance._perField || {};
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

    getConfidencePercent(riskInstance, fieldName) {
      const perField = riskInstance._perField || {};
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

    removeRiskInstance(index) {
      if (confirm('Are you sure you want to remove this risk instance?')) {
        this.extractedRiskInstances.splice(index, 1);
      }
    },

    async saveAllRiskInstances() {
      const invalidRiskInstances = this.extractedRiskInstances.filter(ri => !ri.RiskTitle);
      if (invalidRiskInstances.length > 0) {
        this.$notify({
          type: 'error',
          title: 'Validation Error',
          text: 'All risk instances must have a title.'
        });
        return;
      }

      this.isSaving = true;
      this.saveProcessingState();

      try {
        const cleanRiskInstances = this.extractedRiskInstances.map(ri => {
          // eslint-disable-next-line no-unused-vars
          const { _meta, _perField, ...cleanRI } = ri;
          return cleanRI;
        });

        const response = await axios.post(
          API_ENDPOINTS.RISK_INSTANCE_AI_SAVE,
          {
            risk_instances: cleanRiskInstances,
            user_id: localStorage.getItem('user_id') || '1'
          },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );

        if (response.data.status === 'success') {
          this.savedCount = response.data.saved?.length || this.extractedRiskInstances.length;
          this.currentStep = 'success';
          this.clearProcessingState();
          
          this.$notify({
            type: 'success',
            title: 'Success',
            text: `Successfully saved ${this.savedCount} risk instance(s) to the database.`
          });
        } else {
          throw new Error(response.data.message || 'Failed to save risk instances');
        }
      } catch (error) {
        console.error('Error saving risk instances:', error);
        this.$notify({
          type: 'error',
          title: 'Save Failed',
          text: error.response?.data?.message || error.message || 'Failed to save risk instances. Please try again.'
        });
      } finally {
        this.isSaving = false;
      }
    },

    cancelReview() {
      if (confirm('Are you sure? All extracted data will be lost.')) {
        this.resetForm();
      }
    },

    resetForm() {
      this.currentStep = 'upload';
      this.selectedFile = null;
      this.extractedRiskInstances = [];
      this.processingProgress = 0;
      this.currentProcessingStep = 0;
      this.savedCount = 0;
      this.clearProcessingState();
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = '';
      }
    },

    viewRiskInstances() {
      this.$router.push('/risk/riskinstances-list');
    },

    checkSidebarState() {
      // Check if sidebar exists and is collapsed
      const sidebar = document.querySelector('.sidebar');
      if (sidebar) {
        this.isSidebarCollapsed = sidebar.classList.contains('collapsed');
        console.log('Sidebar state:', this.isSidebarCollapsed ? 'collapsed' : 'expanded');
      } else {
        console.log('Sidebar not found');
      }
    },

    getTotalAIFields() {
      let total = 0;
      this.extractedRiskInstances.forEach(riskInstance => {
        const perField = riskInstance._perField || {};
        const aiFields = Object.keys(perField).filter(k => perField[k]?.source === 'AI_GENERATED');
        total += aiFields.length;
      });
      return total;
    },

    getAverageConfidence() {
      let sum = 0;
      let count = 0;
      this.extractedRiskInstances.forEach(riskInstance => {
        const perField = riskInstance._perField || {};
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
  },
  mounted() {
    // Check sidebar state on mount
    this.checkSidebarState();
    
    // Listen for sidebar toggle events
    document.addEventListener('click', (event) => {
      if (event.target.closest('.toggle') || event.target.closest('.expand-button')) {
        // Wait for the sidebar animation to complete
        setTimeout(() => {
          this.checkSidebarState();
        }, 300);
      }
    });

    // Load processing state on component mount
    this.loadProcessingState();
    this.resumeProcessingIfNeeded();
  }
};
</script>

<style src="./risk_ai_instance.css" scoped></style>

