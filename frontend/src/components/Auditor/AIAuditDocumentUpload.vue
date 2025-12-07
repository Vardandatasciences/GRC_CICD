<template>
  <div class="ai-audit-document-upload-page">
    <div class="audit-content">
      <h1 class="audit-title">Audit Document Upload</h1>
      <p class="audit-subtitle">Upload documents for Automated audit processing</p>

    <!-- Audit Selection Only -->
    <div class="audit-selection-section">
      <h3>Select Assigned Audit</h3>
      <div class="audit-switcher">
        <div class="custom-dropdown-container" :class="{ 'is-open': isDropdownOpen, 'has-selection': selectedExistingAuditId }">
          <div class="dropdown-trigger" @click="toggleDropdown" @blur="closeDropdown">
            <div class="dropdown-selected">
              <div class="selected-content">
                <i class="fas fa-clipboard-list dropdown-icon"></i>
                <div class="selected-text">
                  <span v-if="selectedExistingAuditId" class="selected-title">
                    {{ getSelectedAuditTitle() }}
                  </span>
                  <span v-else class="placeholder-text">Select Assigned AI Audit...</span>
                </div>
              </div>
              <i class="fas fa-chevron-down dropdown-arrow" :class="{ 'is-open': isDropdownOpen }"></i>
            </div>
          </div>
          
          <div class="dropdown-options" v-show="isDropdownOpen">
            <div class="dropdown-search" v-if="availableAIAudits.length > 5">
              <input 
                type="text" 
                v-model="searchQuery" 
                placeholder="Search audits..." 
                class="search-input"
                @click.stop
              >
              <i class="fas fa-search search-icon"></i>
            </div>
            
            <div class="options-list">
              <div 
                v-for="audit in filteredAudits" 
                :key="audit.audit_id" 
                class="dropdown-option"
                :class="{ 'is-selected': selectedExistingAuditId === audit.audit_id }"
                @click="selectAudit(audit)"
              >
                <div class="option-content">
                  <div class="option-header">
                    <span class="option-title">{{ audit.title || audit.policy || 'Audit' }}</span>
                    <span class="option-id">ID: {{ audit.audit_id }}</span>
                  </div>
                  <div class="option-meta">
                    <span class="option-due-date">
                      <i class="fas fa-calendar-alt"></i>
                      Due: {{ audit.duedate || audit.due_date || 'N/A' }}
                    </span>
                    <span class="option-type" :class="audit.audit_type?.toLowerCase()">
                      {{ audit.audit_type || 'AI' }}
                    </span>
                  </div>
                </div>
                <i v-if="selectedExistingAuditId === audit.audit_id" class="fas fa-check option-check"></i>
              </div>
              
              <div v-if="filteredAudits.length === 0" class="no-options">
                <i class="fas fa-search"></i>
                <span>No audits found matching "{{ searchQuery }}"</span>
              </div>
              
              <div v-if="!isLoadingAudits && availableAIAudits.length === 0" class="no-options">
                <i class="fas fa-exclamation-triangle"></i>
                <span>No assigned AI audits found</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <p v-if="!hasSelectedAudit" class="hint-text">Choose an assigned AI audit to start uploading documents.</p>
      <p v-if="auditLoadError" class="error-text">{{ auditLoadError }}</p>
    </div>

    <!-- Audit Information (Only shown after selection) -->
    <div v-if="hasSelectedAudit" class="audit-info-section">
      <h3>{{ auditInfo.title || 'Audit Information' }}</h3>
      <div class="audit-meta">
        <span class="audit-id">Audit ID: {{ currentAuditId }}</span>
        <span class="audit-type">{{ auditInfo.type || 'AI Audit' }}</span>
        <span class="framework">{{ auditInfo.framework || 'Framework' }}</span>
      </div>
    </div>

    <!-- Document Upload Section -->
    <div v-if="hasSelectedAudit" class="upload-section">
      <h3>Upload Documents</h3>
      <p class="upload-description">
        Upload documents related to the selected policy. AI will analyze these documents 
        and map them to compliance requirements.
      </p>

      <!-- Assigned Policy/Sub-policy Display -->
      <div class="policy-selection">
        <label>Assigned Policy/Sub-policy</label>
        <div class="policy-display">
          <div class="policy-info">
            <div class="policy-item">
              <span class="policy-label">Policy:</span>
              <span class="policy-value">{{ selectedPolicyName }}</span>
            </div>
            <div class="policy-item">
              <span class="policy-label">Sub-policy:</span>
              <span class="policy-value">{{ selectedSubPolicyName }}</span>
            </div>
          </div>
        </div>
        
        <!-- Compliance Requirements Display (disabled) -->
        <div class="compliance-requirements" v-if="false">
          <h4>Compliance Requirements</h4>
          <div v-if="complianceRequirements.length > 0" class="requirements-list">
            <div v-for="req in complianceRequirements" :key="req.compliance_id" class="requirement-item">
              <div class="requirement-header">
                <span class="requirement-title">{{ req.compliance_title }}</span>
                <span class="requirement-type" :class="req.compliance_type.toLowerCase()">
                  {{ req.compliance_type }}
                </span>
              </div>
              <p class="requirement-description">{{ req.compliance_description }}</p>
              <div class="requirement-meta">
                <span class="risk-level" :class="req.risk_level.toLowerCase()">
                  {{ req.risk_level }} Risk
                </span>
                <span v-if="req.mandatory" class="mandatory">Mandatory</span>
              </div>
            </div>
          </div>
          <div v-else class="no-requirements">
            <p v-if="complianceRequirements.length === 0">
              No compliance requirements configured for this policy yet.
            </p>
          </div>
        </div>
      </div>

      <!-- File Upload Area -->
      <div class="file-upload-area" @click="triggerFileUpload" @dragover.prevent @drop.prevent="handleDrop">
        <input 
          ref="fileInput" 
          type="file" 
          multiple 
          @change="handleFileSelect" 
          accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.json"
          style="display: none;"
        >
        <div class="upload-content" :class="{ 'dragover': isDragOver }">
          <i class="fas fa-cloud-upload-alt upload-icon"></i>
          <h4>Drop files here or click to browse</h4>
          <p>Supported formats: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, CSV, JSON</p>
          <p class="file-limit">Maximum file size: 100MB per file</p>
        </div>
      </div>

      <!-- Selected Files Preview -->
      <div v-if="selectedFiles.length > 0" class="selected-files">
        <h4>Selected Files ({{ selectedFiles.length }})</h4>
        <div class="file-list">
          <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
            <div class="file-info">
              <i class="fas fa-file file-icon"></i>
              <div class="file-details">
                <span class="file-name">{{ file.name }}</span>
                <span class="file-size">{{ formatFileSize(file.size) }}</span>
              </div>
            </div>
            <button @click="removeFile(index)" class="remove-btn">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- Upload Progress -->
      <div v-if="uploading" class="upload-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
        </div>
        <p class="progress-text">Uploading... {{ uploadProgress }}%</p>
      </div>

      <!-- Upload Actions -->
      <div class="upload-actions">
        <button 
          @click="uploadFiles" 
          :disabled="selectedFiles.length === 0 || uploading || !hasRequiredMapping"
          class="btn btn-primary upload-btn"
          @mousedown="console.log('🔍 Upload button mousedown')"
        >
          <i class="fas fa-upload"></i>
          Upload {{ selectedFiles.length }} File(s)
        </button>
        <button @click="clearFiles" class="btn btn-secondary" :disabled="selectedFiles.length === 0">
          Clear All
        </button>
      </div>
    </div>

    <!-- Smart Compliance Selection Interface (disabled) -->
    <div v-if="false && showComplianceSelection" class="compliance-selection-section">
      <h3>📋 Smart Compliance Analysis</h3>
      <p class="selection-description">
        AI has analyzed your uploaded documents and suggests the most relevant compliance requirements to check. 
        Select which compliance requirements you want to process for AI audit:
      </p>
      
      <div v-for="mapping in documentComplianceMapping" :key="mapping.document_id" class="document-mapping">
        <h4>📄 {{ mapping.document_name }}</h4>
        
        <!-- High Relevance Suggestions -->
        <div v-if="mapping.suggested_compliances.filter(s => s.relevance_score >= 0.6).length > 0" class="suggestions high-relevance">
          <h5>🎯 Highly Relevant (Recommended)</h5>
          <div class="compliance-suggestions">
            <div v-for="suggestion in mapping.suggested_compliances.filter(s => s.relevance_score >= 0.6)" 
                 :key="suggestion.compliance_id" 
                 class="suggestion-item high">
              <label class="suggestion-checkbox">
                <input type="checkbox" 
                       :value="suggestion.compliance_id" 
                       v-model="selectedComplianceIds"
                       :id="`compliance-${suggestion.compliance_id}`">
                <span class="checkmark"></span>
                <div class="suggestion-content">
                  <span class="compliance-title">{{ suggestion.compliance_title }}</span>
                  <span class="relevance-score">{{ Math.round(suggestion.relevance_score * 100) }}% match</span>
                  <span class="relevance-reason">{{ suggestion.relevance_reason }}</span>
                </div>
              </label>
            </div>
          </div>
        </div>
        
        <!-- Medium Relevance Suggestions -->
        <div v-if="mapping.suggested_compliances.filter(s => s.relevance_score >= 0.4 && s.relevance_score < 0.6).length > 0" class="suggestions medium-relevance">
          <h5>⚠️ Possibly Relevant</h5>
          <div class="compliance-suggestions">
            <div v-for="suggestion in mapping.suggested_compliances.filter(s => s.relevance_score >= 0.4 && s.relevance_score < 0.6)" 
                 :key="suggestion.compliance_id" 
                 class="suggestion-item medium">
              <label class="suggestion-checkbox">
                <input type="checkbox" 
                       :value="suggestion.compliance_id" 
                       v-model="selectedComplianceIds"
                       :id="`compliance-${suggestion.compliance_id}`">
                <span class="checkmark"></span>
                <div class="suggestion-content">
                  <span class="compliance-title">{{ suggestion.compliance_title }}</span>
                  <span class="relevance-score">{{ Math.round(suggestion.relevance_score * 100) }}% match</span>
                  <span class="relevance-reason">{{ suggestion.relevance_reason }}</span>
                </div>
              </label>
            </div>
          </div>
        </div>
        
        <!-- No Suggestions -->
        <div v-if="mapping.suggested_compliances.length === 0" class="no-suggestions">
          <p>🤔 No highly relevant compliance requirements found for this document. You may need to upload a different document or manually select compliance requirements.</p>
        </div>
      </div>
      
      <!-- Action Buttons -->
      <div class="selection-actions">
        <button @click="proceedWithSelectedCompliances" 
                :disabled="selectedComplianceIds.length === 0"
                class="btn btn-primary">
          📊 Start AI Processing ({{ selectedComplianceIds.length }} selected)
        </button>
        <button @click="selectAllCompliances" class="btn btn-outline">
          ✅ Select All Compliance Requirements
        </button>
        <button @click="cancelSelection" class="btn btn-outline">
          ❌ Cancel Selection
        </button>
      </div>
      
      <!-- Selected Count Summary -->
      <div v-if="selectedComplianceIds.length > 0" class="selection-summary">
        <p><strong>Selected:</strong> {{ selectedComplianceIds.length }} compliance requirement(s) for AI processing</p>
      </div>
    </div>

    <!-- Uploaded Documents List -->
    <div v-if="uploadedDocuments.length > 0" class="uploaded-documents">
      <h3>Uploaded Documents</h3>
      <div class="documents-grid">
        <div v-for="doc in uploadedDocuments" :key="doc.document_id" class="document-card">
          <div class="document-content">
            <div class="document-main">
              <i class="fas fa-file document-icon"></i>
              <div class="document-info">
                <h4>{{ doc.document_name }}</h4>
                <p class="document-meta">
                  {{ formatFileSize(doc.file_size) }} • {{ doc.uploaded_date }}
                </p>
              </div>
            </div>
            
            <div class="document-type">
              <span><strong>Type:</strong> {{ doc.document_type }}</span>
              <div v-if="doc.mapped_policy || doc.mapped_subpolicy" style="font-size:12px;color:#6c757d;">
                <div v-if="doc.mapped_policy"><strong>Policy:</strong> {{ doc.mapped_policy }}</div>
                <div v-if="doc.mapped_subpolicy"><strong>Sub-policy:</strong> {{ doc.mapped_subpolicy }}</div>
              </div>
              <div v-else style="font-size:12px;color:#a94442;">
                Unmapped
              </div>
            </div>
            
            <div class="document-status">
              <span :class="['status-badge', doc.processing_status]">
                {{ doc.processing_status }}
              </span>
              <span v-if="doc.compliance_status" :class="['status-badge', 'compliance', doc.compliance_status]" style="margin-left:6px;">
                {{ doc.compliance_status }} <span v-if="doc.confidence_score">({{ Math.round((doc.confidence_score||0)*100) }}%)</span>
              </span>
            </div>
            
            <div class="document-actions">
              <!-- <button @click="viewDocument(doc)" class="btn btn-sm btn-outline">
                <i class="fas fa-eye"></i> View
              </button> -->
              <button @click="deleteDocument(doc.document_id)" class="btn btn-sm btn-danger">
                <i class="fas fa-trash"></i> Delete
              </button>
              <button @click="checkDocumentCompliance(doc)" class="btn btn-sm btn-primary" :disabled="doc._checking === true">
                <i v-if="doc._checking" class="fas fa-spinner fa-spin"></i>
                <i v-else class="fas fa-robot"></i>
                {{ doc._checking ? 'Checking...' : 'Check' }}
              </button>
              <button v-if="doc.compliance_analyses && doc.compliance_analyses.length" @click="showDocumentDetails(doc)" class="btn btn-sm btn-outline">
                <i class="fas fa-list"></i> Details
              </button>
            </div>
            
          </div>
        </div>
      </div>
      </div>
    </div>

    <!-- AI Processing Status (disabled) -->
    <div v-if="false && hasSelectedAudit && processingStatus" class="ai-processing-status">
      <h3>🤖 AI Processing Status</h3>
      <div class="processing-card">
        <div class="processing-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: processingStatus.progress_percentage + '%' }"></div>
          </div>
          <p class="progress-text">
            {{ processingStatus.completed }} of {{ processingStatus.total_documents }} documents processed
            ({{ processingStatus.progress_percentage }}%)
          </p>
        </div>
        
        <div class="processing-details">
          <div class="status-item">
            <span class="status-label">Pending:</span>
            <span class="status-value">{{ processingStatus.pending }}</span>
          </div>
          <div class="status-item">
            <span class="status-label">Processing:</span>
            <span class="status-value">{{ processingStatus.processing }}</span>
          </div>
          <div class="status-item">
            <span class="status-label">Completed:</span>
            <span class="status-value">{{ processingStatus.completed }}</span>
          </div>
          <div class="status-item">
            <span class="status-label">Failed:</span>
            <span class="status-value">{{ processingStatus.failed }}</span>
          </div>
        </div>
        
        <div class="ai-info">
          <p class="ai-note">
            <i class="fas fa-robot"></i>
            Using Ollama (local AI) for intelligent document analysis and compliance assessment
            <span class="ai-benefits">• Private • Free • No API limits • Offline capable</span>
          </p>
        </div>
      </div>
    </div>

    <!-- AI Processing Results (disabled) -->
    <div v-if="false && hasSelectedAudit && aiProcessingResults.length > 0" class="ai-processing-results">
      <h3>🤖 AI Processing Results</h3>
      <div class="results-grid">
        <div v-for="result in aiProcessingResults" :key="result.document_id" class="result-card">
          <div class="result-header">
            <h4>{{ result.document_name || 'Unknown Document' }}</h4>
            <span :class="['compliance-status', result.compliance_status || 'unknown']">
              {{ (result.compliance_status || 'unknown').replace('_', ' ').toUpperCase() }}
            </span>
          </div>
          
          <div class="result-details">
            <div class="ai-metrics">
              <div class="metric-item">
                <span class="metric-label">AI Confidence:</span>
                <span class="metric-value">{{ Math.round((result.confidence_score || 0) * 100) }}%</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">Risk Level:</span>
                <span :class="['risk-level', result.risk_level || 'medium']">{{ (result.risk_level || 'medium').toUpperCase() }}</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">Text Length:</span>
                <span class="metric-value">{{ result.processing_results?.text_length || 0 }} chars</span>
              </div>
            </div>
            
            <div class="ai-analysis">
              <h5>📊 AI Analysis</h5>
              <p><strong>Document Type:</strong> {{ result.compliance_mapping?.document_type_detected || 'Unknown' }}</p>
              <p><strong>Found Keywords:</strong> {{ result.compliance_mapping?.found_keywords ? result.compliance_mapping.found_keywords.join(', ') : 'None detected' }}</p>
              <p><strong>Analysis Time:</strong> {{ result.compliance_mapping?.analysis_timestamp ? new Date(result.compliance_mapping.analysis_timestamp).toLocaleString() : 'Unknown' }}</p>
            </div>
            
            <div class="ai-recommendations">
              <h5>💡 AI Recommendations</h5>
              <p>{{ result.ai_recommendations || 'No recommendations available' }}</p>
            </div>
            
            <div class="extracted-text" v-if="result.extracted_text">
              <h5>📄 Extracted Text Preview</h5>
              <div class="text-preview">
                {{ result.extracted_text }}
              </div>
            </div>
          </div>
          
          <div class="result-actions">
            <button @click="reviewAIResult(result)" class="btn btn-sm btn-primary">
              <i class="fas fa-eye"></i> Review Details
            </button>
            <button @click="downloadAIReport(result)" class="btn btn-sm btn-secondary">
              <i class="fas fa-download"></i> Download Report
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Enhanced Details Section - At Bottom of Page -->
    <div v-if="selectedDocumentForDetails" class="compliance-details-expanded">
      <!-- Close Button -->
      <div class="details-header">
        <h3><i class="fas fa-list-alt"></i> Compliance Analysis Details</h3>
        <div class="details-actions">
          <button @click="downloadAuditReport()" class="btn btn-sm btn-secondary">
            <i class="fas fa-download"></i> Download Report
          </button>
          <button @click="selectedDocumentForDetails = null" class="btn btn-sm btn-outline">
            <i class="fas fa-times"></i> Close
          </button>
        </div>
      </div>
      
      <!-- Overall Status Card -->
      <div class="overall-status-card">
        <div class="status-header">
          <h4><i class="fas fa-shield-alt"></i> Overall Compliance Status</h4>
          <div class="status-badges">
            <span :class="['compliance-status-badge', selectedDocumentForDetails.compliance_status || 'unknown']">
              {{ (selectedDocumentForDetails.compliance_status || 'unknown').replace('_',' ').toUpperCase() }}
            </span>
            <span v-if="selectedDocumentForDetails.confidence_score" class="confidence-badge">
              <i class="fas fa-chart-line"></i> {{ Math.round((selectedDocumentForDetails.confidence_score||0)*100) }}% Confidence
            </span>
          </div>
        </div>
        
        <div class="status-summary">
          <div class="summary-item">
            <i class="fas fa-file-alt"></i>
            <span>Document: {{ selectedDocumentForDetails.document_name }}</span>
          </div>
          <div class="summary-item" v-if="selectedDocumentForDetails.mapped_policy">
            <i class="fas fa-gavel"></i>
            <span>Policy: {{ selectedDocumentForDetails.mapped_policy }}</span>
          </div>
          <div class="summary-item" v-if="selectedDocumentForDetails.mapped_subpolicy">
            <i class="fas fa-list"></i>
            <span>Sub-policy: {{ selectedDocumentForDetails.mapped_subpolicy }}</span>
          </div>
        </div>
      </div>

      <!-- Detailed Analysis Section -->
      <div v-if="selectedDocumentForDetails.compliance_analyses && selectedDocumentForDetails.compliance_analyses.length" class="detailed-analysis">
        <div class="analysis-header">
          <h4><i class="fas fa-search"></i> Detailed Compliance Analysis</h4>
          <span class="analysis-count">{{ selectedDocumentForDetails.compliance_analyses.length }} Requirements Analyzed</span>
        </div>
        
        <div class="requirements-grid">
          <div v-for="(analysis, idx) in selectedDocumentForDetails.compliance_analyses" :key="idx" class="requirement-card">
            <div class="requirement-header">
              <div class="requirement-number">
                <span class="req-idx">{{ analysis.requirement_title || `Requirement ${analysis.index}` }}</span>
                <div class="compliance-status">
                  <div class="meter-label">Compliance</div>
                  <div class="status-line">
                    <span class="status-pill" :class="(analysis.status || complianceStatusFromScore(analysis.compliance_score ?? analysis.relevance ?? 0))">
                      {{ (analysis.status || complianceStatusFromScore(analysis.compliance_score ?? analysis.relevance ?? 0)).replace('_',' ') }}
                    </span>
                    <span class="percent">{{ Math.round(((analysis.compliance_score ?? analysis.relevance ?? 0) * 100)) }}%</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Evidence Section -->
            <div v-if="analysis.evidence && analysis.evidence.length" class="evidence-section">
              <div class="section-header">
                <i class="fas fa-check-circle text-success"></i>
                <span>Evidence Found</span>
              </div>
              <div class="evidence-list">
                <div v-for="(evidence, eIdx) in analysis.evidence" :key="eIdx" class="evidence-item">
                  <span>{{ typeof evidence === 'string' ? evidence : ((evidence && (evidence.text || evidence.reason)) || JSON.stringify(evidence)) }}</span>
                </div>
              </div>
            </div>
            
            <!-- Missing Elements Section -->
            <div v-if="analysis.missing && analysis.missing.length" class="missing-section">
              <div class="section-header">
                <i class="fas fa-exclamation-triangle text-warning"></i>
                <span>Missing Elements</span>
              </div>
              <div class="missing-list">
                <div v-for="(missing, mIdx) in analysis.missing" :key="mIdx" class="missing-item">
                  <span>{{ typeof missing === 'string' ? missing : ((missing && (missing.text || missing.reason)) || JSON.stringify(missing)) }}</span>
                </div>
              </div>
            </div>
            
            <!-- No Evidence/Missing -->
            <div v-if="(!analysis.evidence || !analysis.evidence.length) && (!analysis.missing || !analysis.missing.length)" class="no-analysis">
              <i class="fas fa-info-circle"></i>
              <span>No specific evidence or missing elements identified</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- No Analysis Available -->
      <div v-else class="no-analysis-available">
        <i class="fas fa-info-circle"></i>
        <span>No detailed analysis available for this document</span>
      </div>
    </div>

    <!-- Action Buttons (AI disabled) -->
    <div v-if="hasSelectedAudit" class="action-buttons">
      <button v-if="false" @click="startAIProcessing" class="btn btn-success" :disabled="uploadedDocuments.length === 0 || isProcessingAI" :class="{ 'processing': isProcessingAI }">
        <i v-if="!isProcessingAI" class="fas fa-robot"></i>
        <i v-else class="fas fa-spinner fa-spin"></i>
        {{ isProcessingAI ? 'AI Analyzing Documents...' : 'Start AI Analysis' }}
      </button>
      <button @click="goToReviews" class="btn btn-primary">
        <i class="fas fa-list-check"></i> Go to Reviews
      </button>
    </div>
    
    <!-- Bottom spacing for scrolling -->
    <div style="height: 50px;"></div>
  </div>
</template>

<script>
import api from '@/services/api.js'
import auditorDataService from '@/services/auditorService' // NEW: Use cached auditor data

export default {
  name: 'AIAuditDocumentUpload',
  props: {
    auditId: {
      type: [String, Number],
      required: true
    }
  },
  data() {
    return {
      auditInfo: {
        title: 'Audit Information',
        type: 'AI Audit',
        framework: 'Selected Framework',
        policy: 'Not Specified',
        subpolicy: 'Not Specified'
      },
      selectedPolicyName: 'Not Specified',
      selectedSubPolicyName: 'Not Specified',
      policies: [],
      subpolicies: [],
      selectedPolicyId: '',
      selectedSubPolicyId: '',
      complianceRequirements: [],
      selectedFiles: [],
      uploadedDocuments: [],
      uploading: false,
      uploadProgress: 0,
      isDragOver: false,
      documentComplianceMapping: [], // Store document-to-compliance relevance mapping
      showComplianceSelection: false, // Show compliance selection modal
      selectedComplianceIds: [], // User-selected compliance requirements for processing
      processingStatus: null,
      complianceResults: [],
      aiProcessingResults: [],
      pollingInterval: null,
      isProcessingAI: false,
      availableAudits: [],
      availableAIAudits: [],
      selectedExistingAuditId: '',
      hasUserConfirmedSelection: false,
      isLoadingAudits: false,
      auditLoadError: '',
      selectedDocumentForDetails: null,
      isDropdownOpen: false,
      searchQuery: ''
    }
  },
  computed: {
    currentAuditId() {
      // Priority: selected dropdown audit > route params > props > fallback
      return this.selectedExistingAuditId || this.auditId || this.$route.params.auditId || this.$route.query.auditId || '1092'
    },
    hasSelectedAudit() {
      // Show details only after explicit user confirmation
      return this.hasUserConfirmedSelection === true
    },
    hasRequiredMapping() {
      // Must have either policy or subpolicy ID selected
      return Boolean(this.selectedPolicyId || this.selectedSubPolicyId)
    },
    filteredAudits() {
      if (!this.searchQuery) {
        return this.availableAIAudits
      }
      return this.availableAIAudits.filter(audit => {
        const searchLower = this.searchQuery.toLowerCase()
        const title = (audit.title || audit.policy || 'Audit').toLowerCase()
        const auditId = audit.audit_id.toString().toLowerCase()
        const dueDate = (audit.duedate || audit.due_date || '').toLowerCase()
        
        return title.includes(searchLower) || 
               auditId.includes(searchLower) || 
               dueDate.includes(searchLower)
      })
    }
  },
  mounted() {
    console.log('🔍 Component mounted')
    console.log('🔍 Props auditId:', this.auditId)
    console.log('🔍 Route params:', this.$route.params)
    console.log('🔍 Current audit ID (route):', this.currentAuditId)
    
    // Pre-select dropdown with route auditId if present, but do not load details yet
    const routeAuditId = this.$route.params.auditId || this.$route.query.auditId || this.auditId
    if (routeAuditId) {
      this.selectedExistingAuditId = String(routeAuditId)
    }

    this.loadAvailableAudits()
    
    // Add click outside listener for dropdown
    document.addEventListener('click', this.handleClickOutside)
  },
  beforeUnmount() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval)
    }
    // Remove click outside listener
    document.removeEventListener('click', this.handleClickOutside)
  },
  methods: {
    // Dropdown methods
    toggleDropdown() {
      this.isDropdownOpen = !this.isDropdownOpen
      if (this.isDropdownOpen) {
        this.searchQuery = ''
      }
    },
    
    closeDropdown() {
      // Delay closing to allow click events to register
      setTimeout(() => {
        this.isDropdownOpen = false
        this.searchQuery = ''
      }, 150)
    },
    
    selectAudit(audit) {
      this.selectedExistingAuditId = audit.audit_id
      this.isDropdownOpen = false
      this.searchQuery = ''
      this.onSelectExistingAudit()
    },
    
    getSelectedAuditTitle() {
      const selectedAudit = this.availableAIAudits.find(a => a.audit_id === this.selectedExistingAuditId)
      if (selectedAudit) {
        return selectedAudit.title || selectedAudit.policy || 'Audit'
      }
      return 'Select Assigned AI Audit...'
    },
    
    handleClickOutside(event) {
      const dropdown = this.$el.querySelector('.custom-dropdown-container')
      if (dropdown && !dropdown.contains(event.target)) {
        this.isDropdownOpen = false
        this.searchQuery = ''
      }
    },
    
    complianceStatusFromScore(score) {
      const s = Number(score || 0)
      if (s >= 0.7) return 'compliant'
      if (s >= 0.4) return 'partially_compliant'
      return 'non_compliant'
    },
    async downloadAuditReport() {
      try {
        const auditId = this.currentAuditId
        if (!auditId) return
        const url = `/api/ai-audit/${auditId}/download-report/`
        const response = await api.get(url, { responseType: 'blob' })
        const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
        const link = document.createElement('a')
        const fileURL = window.URL.createObjectURL(blob)
        link.href = fileURL
        link.download = `Audit_Report_${auditId}.docx`
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(fileURL)
      } catch (e) {
        console.error('Error downloading report:', e)
        this.$popup?.error('Failed to generate report')
      }
    },
    showDocumentDetails(doc) {
      this.selectedDocumentForDetails = doc
      console.log('Selected document for details:', doc)
      console.log('Compliance analyses:', doc.compliance_analyses)
      if (doc.compliance_analyses && doc.compliance_analyses.length > 0) {
        console.log('First analysis:', doc.compliance_analyses[0])
        console.log('Requirement title:', doc.compliance_analyses[0].requirement_title)
      }
      // Scroll to the details section with better positioning
      this.$nextTick(() => {
        const detailsElement = document.querySelector('.compliance-details-expanded')
        if (detailsElement) {
          // Scroll to show the details section with some offset from top
          const offset = 100
          const elementPosition = detailsElement.offsetTop - offset
          window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
          })
        }
      })
    },
    async loadAvailableAudits() {
      try {
        this.isLoadingAudits = true
        this.auditLoadError = ''
        
        console.log('🔍 [AIAuditUpload] Checking for cached audits data...')
        
        // Check if prefetch was never started (user came directly to this page)
        if (!window.auditorDataFetchPromise && !auditorDataService.hasAuditsCache()) {
          console.log('🚀 [AIAuditUpload] Starting prefetch now (user came directly to this page)...')
          window.auditorDataFetchPromise = auditorDataService.fetchAllAuditorData()
        }
        
        // Wait for prefetch if it's running
        if (window.auditorDataFetchPromise) {
          console.log('⏳ [AIAuditUpload] Waiting for prefetch to complete...')
          try {
            await window.auditorDataFetchPromise
            console.log('✅ [AIAuditUpload] Prefetch completed')
          } catch (error) {
            console.warn('⚠️ [AIAuditUpload] Prefetch failed, will fetch directly')
          }
        }
        
        let merged = []
        
        // Try to get data from cache first
        if (auditorDataService.hasAuditsCache()) {
          console.log('✅ [AIAuditUpload] Using cached audits data')
          const cachedAudits = auditorDataService.getData('audits') || []
          console.log(`[AIAuditUpload] Loaded ${cachedAudits.length} audits from cache`)
          merged = cachedAudits
        } else {
          // Fallback: Fetch auditor, reviewer and public audits in parallel and merge
          console.log('⚠️ [AIAuditUpload] No cached data found, fetching from API...')
          const results = await Promise.allSettled([
            api.get('/api/my-audits/'),
            api.get('/api/my-reviews/'),
            api.get('/api/audits/public/')
          ])

          const pushNormalized = (arr) => {
            if (!Array.isArray(arr)) return
            arr.forEach(item => merged.push(item))
          }

          results.forEach((res, idx) => {
            if (res.status === 'fulfilled') {
              const data = res.value?.data
              const list = Array.isArray(data?.audits) ? data.audits : (Array.isArray(data) ? data : [])
              console.log('🔎 Source', idx, 'count:', Array.isArray(list) ? list.length : 0)
              pushNormalized(list)
            } else {
              console.warn('Audit source failed:', idx, res.reason?.response?.status)
            }
          })
          
          // Update cache with fetched data
          if (merged.length > 0) {
            auditorDataService.setData('audits', merged)
            console.log('ℹ️ [AIAuditUpload] Cache updated after direct API fetch')
          }
        }

        // Deduplicate by AuditId/audit_id
        const seen = new Set()
        const deduped = merged.filter(a => {
          const id = a.audit_id || a.AuditId || a.id
          if (!id) return false
          if (seen.has(id)) return false
          seen.add(id)
          return true
        })

        this.availableAudits = deduped
        // Do not filter by audit type because some AI audits may be stored as 'I'.
        // Show all assigned audits and indicate type in the label.
        this.availableAIAudits = this.availableAudits.map(a => ({
          audit_id: a.audit_id || a.AuditId || a.id,
          title: a.title || a.Title || null,
          policy: a.policy || a.Policy || a.title || a.Title || 'Audit',
          duedate: a.duedate || a.due_date || a.DueDate || null,
          framework: a.framework || a.FrameworkName || null,
          audit_type: (a.audit_type || a.AuditType || '').toString().toUpperCase() || 'UNKNOWN'
        })).sort((a) => (a.audit_type === 'A' ? -1 : 1))
        console.log('🔍 Loaded AI audits:', this.availableAIAudits)
      } catch (e) {
        console.error('Error loading assigned audits:', e)
        this.auditLoadError = 'Unable to load assigned AI audits.'
        this.availableAIAudits = []
      } finally {
        this.isLoadingAudits = false
      }
    },
    onSelectExistingAudit() {
      if (!this.selectedExistingAuditId) return
      console.log('🔄 Switching to audit ID:', this.selectedExistingAuditId)
      console.log('🔄 Current computed audit ID:', this.currentAuditId)
      console.log('🔄 All audit ID sources:', {
        selectedExistingAuditId: this.selectedExistingAuditId,
        auditId: this.auditId,
        routeParams: this.$route.params.auditId,
        routeQuery: this.$route.query.auditId
      })
      
      // Clear existing data before loading new audit
      this.auditInfo = {}
      this.selectedPolicyName = ''
      this.selectedSubPolicyName = ''
      this.uploadedDocuments = []
      this.processingStatus = 'idle'
      this.processingResults = []
      
      // Now that user selected, mark confirmed and load data for the chosen audit inline
      this.hasUserConfirmedSelection = true
      this.$nextTick(async () => {
        await this.loadAuditInfo()
        await this.loadPolicies()
        await this.loadUploadedDocuments()
        this.startStatusPolling()
      })
    },
    async loadAuditInfo() {
      try {
        const auditId = this.currentAuditId
        console.log('🔄 Loading audit info for ID:', auditId)
        
        if (!auditId || auditId === 'Unknown') {
          console.warn('No audit ID available, using default audit')
          this.auditInfo = {
            title: 'AI Audit Document Upload',
            type: 'AI Audit',
            framework: 'Default Framework'
          }
          return
        }
        
        // Load audit details
        const response = await api.get(`/api/audits/${auditId}/task-details/`)
        console.log('🔍 API Response for audit', auditId, ':', response.data)
        console.log('🔍 Policy from API:', response.data?.policy_name)
        console.log('🔍 Sub-policy from API:', response.data?.subpolicy_name)
        console.log('🔍 Framework from API:', response.data?.framework_name)
        
        if (response.data && !response.data.error) {
          // Extract actual audit data from the API response
          this.auditInfo = {
            title: response.data.title || `Audit ${auditId}`,
            type: 'AI Audit', // Since this is the AI audit upload page
            framework: response.data.framework_name || 'Framework Not Set',
            policy: response.data.policy_name || 'Not Specified',
            subpolicy: response.data.subpolicy_name || 'Not Specified'
          }
          
          // Pre-populate the selected policy and sub-policy
          this.selectedPolicyName = response.data.policy_name || 'Not Specified'
          this.selectedSubPolicyName = response.data.subpolicy_name || 'Not Specified'
          
          console.log('✅ Updated selectedPolicyName to:', this.selectedPolicyName)
          console.log('✅ Updated selectedSubPolicyName to:', this.selectedSubPolicyName)
          
          // Load compliance requirements using policy and sub-policy names
          console.log('🔍 Loading compliance by policy and sub-policy names')
          console.log('🔍 Policy:', response.data.policy_name, 'Sub-policy:', response.data.subpolicy_name)
          await this.loadComplianceByPolicyNames(response.data.policy_name, response.data.subpolicy_name)

          // Also resolve and store IDs for mapping enforcement
          try {
            const policyId = await this.findPolicyIdByName(this.selectedPolicyName)
            if (policyId) {
              this.selectedPolicyId = policyId
              // Attempt to resolve subpolicy under this policy
              try {
                const spRes = await api.get(`/api/compliance/policies/${policyId}/subpolicies/`)
                const sp = spRes.data?.subpolicies?.find(sp => sp.SubPolicyName?.toLowerCase() === this.selectedSubPolicyName?.toLowerCase())
                if (sp) this.selectedSubPolicyId = sp.SubPolicyId || sp.id
              } catch (e) { /* ignore */ }
            }
          } catch (e) {
            console.log('ℹ️ Could not auto-resolve policy/subpolicy IDs')
          }
        } else {
          // Fallback data if API returns error
          console.warn('❌ API returned error or no data for audit', auditId)
          this.auditInfo = {
            title: `Audit ${auditId}`,
            type: 'AI Audit',
            framework: 'Framework Not Set',
            policy: 'Not Specified',
            subpolicy: 'Not Specified'
          }
          this.selectedPolicyName = 'Not Specified'
          this.selectedSubPolicyName = 'Not Specified'
        }
        console.log('🎯 Final audit info for', auditId, ':', this.auditInfo)
      } catch (error) {
        console.error('Error loading audit info:', error)
        // Set fallback data on error
        this.auditInfo = {
          title: `Audit ${this.currentAuditId}`,
          type: 'AI Audit',
          framework: 'Framework Not Set',
          policy: 'Not Specified',
          subpolicy: 'Not Specified'
        }
        this.selectedPolicyName = 'Not Specified'
        this.selectedSubPolicyName = 'Not Specified'
      }
    },
    
    async loadPolicies() {
      try {
        // Try to load policies, but don't fail if permission denied
        const response = await api.get('/api/policies/')
        this.policies = response.data || []
      } catch (error) {
        console.error('Error loading policies:', error)
        // Set empty array if policies can't be loaded
        this.policies = []
      }
    },
    
    async onPolicyChange() {
      this.selectedSubPolicyId = ''
      this.subpolicies = []
      this.complianceRequirements = []
      
      if (this.selectedPolicyId) {
        console.log('🔍 Policy changed to:', this.selectedPolicyId, 'Type:', typeof this.selectedPolicyId)
        try {
          // Get JWT token for authentication
          const token = localStorage.getItem('access_token')
          const headers = { 'Content-Type': 'application/json' }
          if (token) {
            headers['Authorization'] = `Bearer ${token}`
          }
          
          // Load subpolicies - using the correct API endpoint
          const response = await api.get(`/api/compliance/policies/${this.selectedPolicyId}/subpolicies/`, { headers })
          console.log('🔍 Subpolicies response:', response.data)
          if (response.data && response.data.success) {
            this.subpolicies = response.data.subpolicies || []
            console.log('🔍 Loaded subpolicies:', this.subpolicies.length)
          } else {
            this.subpolicies = []
            console.log('🔍 No subpolicies in response')
          }
          
          // Load compliance requirements
          await this.loadComplianceRequirements(this.selectedPolicyId);
        } catch (error) {
          console.error('Error loading subpolicies:', error)
          // If it's a 404, it means no subpolicies exist for this policy
          if (error.response && error.response.status === 404) {
            console.log('ℹ️ No subpolicies found for this policy')
            this.subpolicies = []
          }
        }
      }
    },
    
    async findPolicyIdByName(policyName) {
      try {
        if (!policyName || policyName === 'Not Specified') {
          return null;
        }
        
        // First check if policies are already loaded
        if (this.policies.length === 0) {
          console.log('🔍 Loading policies to find ID for:', policyName)
          await this.loadPolicies();
        }
        
        // Search for policy by name (case-insensitive)
        const policy = this.policies.find(p => 
          p.PolicyName?.toLowerCase() === policyName.toLowerCase() ||
          p.policy_name?.toLowerCase() === policyName.toLowerCase() ||
          p.name?.toLowerCase() === policyName.toLowerCase()
        );
        
        if (policy) {
          return policy.PolicyId || policy.policy_id || policy.id;
        }
        
        // If not found in loaded policies, try API search
        console.log('🔍 Policy not found in cache, searching via API')
        const response = await api.get('/api/policies/', {
          params: { search: policyName }
        });
        
        if (response.data && response.data.length > 0) {
          const foundPolicy = response.data.find(p => 
            p.PolicyName?.toLowerCase() === policyName.toLowerCase() ||
            p.policy_name?.toLowerCase() === policyName.toLowerCase()
          );
          return foundPolicy ? (foundPolicy.PolicyId || foundPolicy.policy_id || foundPolicy.id) : null;
        }
        
        return null;
      } catch (error) {
        console.error('❌ Error finding policy ID by name:', error);
        return null;
      }
    },

    async loadComplianceByPolicyNames(policyName, subPolicyName) {
      try {
        console.log('🔍 Loading compliance by names - Policy:', policyName, 'Sub-policy:', subPolicyName)
        
        // First, find the policy and sub-policy IDs, then get compliance requirements
        console.log('🔍 Step 1: Finding policy and sub-policy IDs')
        
        // Find policy ID by name
        let policyId = null;
        let subPolicyId = null;
        
        try {
          if (this.policies.length === 0) {
            await this.loadPolicies();
          }
          
          const policy = this.policies.find(p => 
            p.PolicyName?.toLowerCase() === policyName?.toLowerCase() ||
            p.policy_name?.toLowerCase() === policyName?.toLowerCase()
          );
          
          if (policy) {
            policyId = policy.PolicyId || policy.policy_id;
            console.log('✅ Found policy ID:', policyId, 'for policy:', policyName);
            
            // Now find sub-policy ID
            try {
              const subPolicyResponse = await api.get(`/api/compliance/policies/${policyId}/subpolicies/`);
              if (subPolicyResponse.data.success && subPolicyResponse.data.subpolicies) {
                const subPolicy = subPolicyResponse.data.subpolicies.find(sp => 
                  sp.SubPolicyName?.toLowerCase() === subPolicyName?.toLowerCase() ||
                  sp.name?.toLowerCase() === subPolicyName?.toLowerCase()
                );
                
                if (subPolicy) {
                  subPolicyId = subPolicy.SubPolicyId || subPolicy.id;
                  console.log('✅ Found sub-policy ID:', subPolicyId, 'for sub-policy:', subPolicyName);
                }
              }
            } catch (error) {
              console.log('❌ Error finding sub-policy ID:', error.response?.status);
            }
          }
        } catch (error) {
          console.log('❌ Error finding policy ID:', error.response?.status);
        }
        
        // Try different API endpoints using the IDs we found
        const endpoints = [];
        
        if (policyId) {
          endpoints.push(`/api/compliance/view/policy/${policyId}`);
          endpoints.push(`/compliances/policy/${policyId}/`);
        }
        
        if (subPolicyId) {
          endpoints.push(`/api/compliance/view/subpolicy/${subPolicyId}`);
          endpoints.push(`/api/subpolicies/${subPolicyId}/compliances/`);
          endpoints.push(`/compliances/subpolicy/${subPolicyId}/`);
        }
        
        // Also try the type-based endpoints
        if (policyId) {
          endpoints.push(`/compliance/view/policy/${policyId}`);
        }
        if (subPolicyId) {
          endpoints.push(`/compliance/view/subpolicy/${subPolicyId}`);
        }
        
        let foundCompliances = [];
        
        for (const endpoint of endpoints) {
          try {
            console.log('🔍 Trying endpoint:', endpoint)
            const response = await api.get(endpoint);
            console.log('🔍 Response from', endpoint, ':', response.data)
            
            if (response.data && Array.isArray(response.data)) {
              foundCompliances = response.data;
              console.log('✅ Found compliances via', endpoint, ':', foundCompliances.length, 'items')
              break;
            } else if (response.data && response.data.compliances && Array.isArray(response.data.compliances)) {
              foundCompliances = response.data.compliances;
              console.log('✅ Found compliances via', endpoint, ':', foundCompliances.length, 'items')
              break;
            }
          } catch (error) {
            console.log('❌ Endpoint', endpoint, 'failed:', error.response?.status)
            continue;
          }
        }
        
        // Format compliance data for display
        if (foundCompliances.length > 0) {
          this.complianceRequirements = foundCompliances.map(comp => ({
            compliance_id: comp.ComplianceId || comp.compliance_id || comp.id,
            compliance_title: comp.ComplianceTitle || comp.compliance_title || comp.title || comp.ComplianceItemDescription,
            compliance_description: comp.ComplianceItemDescription || comp.compliance_description || comp.description,
            compliance_type: comp.ComplianceType || comp.compliance_type || 'Mandatory',
            risk_level: comp.Criticality || comp.risk_level || 'Medium',
            mandatory: (comp.MandatoryOptional || comp.mandatory) === 'Mandatory' || comp.mandatory === true
          }));
          console.log('✅ Formatted compliance requirements:', this.complianceRequirements.length, 'items')
        } else {
          console.log('ℹ️ No compliance requirements found for this policy/sub-policy combination')
          this.complianceRequirements = [];
        }
        
      } catch (error) {
        console.error('❌ Error loading compliance by policy names:', error);
        this.complianceRequirements = [];
      }
    },

    async loadComplianceRequirements(policyId) {
      try {
        console.log('🔍 Loading compliance requirements for policy:', policyId)
        const response = await api.get(`/api/compliance-mapping/requirements/${policyId}/`);
        console.log('🔍 Compliance API response:', response.data)
        if (response.data.success) {
          this.complianceRequirements = response.data.requirements;
          console.log('✅ Loaded compliance requirements:', this.complianceRequirements.length, 'items')
        } else {
          console.warn('❌ Compliance API returned no success flag')
          this.complianceRequirements = [];
        }
      } catch (error) {
        console.error('❌ Error loading compliance requirements:', error);
        if (error.response?.status === 404) {
          console.log('ℹ️ No compliance requirements found for this policy (404)');
        } else {
          console.error('❌ Server error loading compliance requirements:', error.response?.status);
        }
        this.complianceRequirements = [];
      }
    },
    
    async analyzeDocumentRelevance() {
      try {
        console.log('🤖 Starting document relevance analysis...')
        console.log('📄 Uploaded documents:', this.uploadedDocuments.length)
        console.log('📋 Compliance requirements:', this.complianceRequirements.length)
        
        if (this.uploadedDocuments.length === 0 || this.complianceRequirements.length === 0) {
          console.log('❌ No documents or compliance requirements to analyze')
          return
        }
        
        // Analyze each uploaded document against compliance requirements
        const mappingResults = []
        
        for (const document of this.uploadedDocuments) {
          console.log(`🔍 Analyzing document: ${document.document_name}`)
          
          // Call AI endpoint to analyze document relevance
          try {
            console.log('🤖 AI Analysis - Using audit ID:', this.currentAuditId)
            console.log('🤖 AI Analysis - Document ID:', document.document_id)
            console.log('🤖 AI Analysis - Document name:', document.document_name)
            const response = await api.post(`/api/ai-audit/${this.currentAuditId}/analyze-document-relevance/`, {
              document_id: document.document_id,
              document_name: document.document_name,
              compliance_requirements: this.complianceRequirements
            })
            
            if (response.data.success) {
              mappingResults.push({
                document_id: document.document_id,
                document_name: document.document_name,
                relevance_scores: response.data.relevance_scores,
                suggested_compliances: response.data.suggested_compliances
              })
              
              console.log(`✅ Relevance analysis complete for: ${document.document_name}`)
              console.log('🎯 Suggested compliances:', response.data.suggested_compliances)
            }
          } catch (error) {
            console.error(`❌ Error analyzing ${document.document_name}:`, error)
            console.error('❌ AI endpoint not available - skipping document analysis')
            
            // Show error message instead of fallback
            this.$popup?.warning(`AI analysis failed for "${document.document_name}". Please ensure AI services are running.`)
          }
        }
        
        // Store mapping results and show selection interface
        this.documentComplianceMapping = mappingResults
        
        // Show compliance selection modal/interface
        this.showComplianceSelectionInterface()
        
      } catch (error) {
        console.error('❌ Error in document relevance analysis:', error)
      }
    },
    
    
    showComplianceSelectionInterface() {
      console.log('📋 Showing compliance selection interface')
      console.log('🗂️ Document compliance mapping:', this.documentComplianceMapping)
      
      // Set flag to show the compliance selection modal/section
      this.showComplianceSelection = true
      
      // Auto-select suggested compliance requirements with high relevance
      this.selectedComplianceIds = []
      for (const mapping of this.documentComplianceMapping) {
        for (const suggestion of mapping.suggested_compliances) {
          if (suggestion.relevance_score >= 0.6 && !this.selectedComplianceIds.includes(suggestion.compliance_id)) {
            this.selectedComplianceIds.push(suggestion.compliance_id)
          }
        }
      }
      
      console.log('✅ Auto-selected compliance IDs:', this.selectedComplianceIds)
    },
    
    proceedWithSelectedCompliances() {
      console.log('🚀 Proceeding with AI processing for selected compliance requirements')
      console.log('📋 Selected compliance IDs:', this.selectedComplianceIds)
      
      if (this.selectedComplianceIds.length === 0) {
        this.$popup?.warning('Please select at least one compliance requirement to process.')
        return
      }
      
      // Hide the selection interface
      this.showComplianceSelection = false
      
      // Start AI processing with selected compliance requirements
      this.startSelectiveAIProcessing()
    },
    
    selectAllCompliances() {
      console.log('✅ Selecting all compliance requirements')
      this.selectedComplianceIds = this.complianceRequirements.map(c => c.compliance_id)
      console.log('📋 All compliance IDs selected:', this.selectedComplianceIds)
    },
    
    cancelSelection() {
      console.log('❌ Cancelling compliance selection')
      this.showComplianceSelection = false
      this.selectedComplianceIds = []
      this.documentComplianceMapping = []
    },
    
    async startSelectiveAIProcessing() {
      console.log('🤖 Starting selective AI processing...')
      console.log('📋 Processing compliance IDs:', this.selectedComplianceIds)
      console.log('📄 Processing documents:', this.uploadedDocuments.length)
      
      try {
        // Call AI processing endpoint with selected compliance requirements
        const response = await api.post(`/api/ai-audit/${this.currentAuditId}/start-selective-processing/`, {
          selected_compliance_ids: this.selectedComplianceIds,
          document_compliance_mapping: this.documentComplianceMapping
        })
        
        if (response.data.success) {
          this.$popup?.success('AI processing started! Check the status below for progress.')
          
          // Start polling for results
          this.startStatusPolling()
        } else {
          this.$popup?.error('Failed to start AI processing: ' + response.data.error)
        }
        
      } catch (error) {
        console.error('❌ Error starting selective AI processing:', error)
        
        // Fallback: Use existing AI processing method
        console.log('🔄 Falling back to standard AI processing...')
        this.$popup?.info('Using standard AI processing method...')
        this.startAIProcessing()
      }
    },

    triggerFileUpload() {
      this.$refs.fileInput.click()
    },
    
    handleFileSelect(event) {
      console.log('🔍 File select event triggered')
      const files = Array.from(event.target.files)
      console.log('🔍 Selected files from input:', files)
      this.addFiles(files)
    },
    
    handleDrop(event) {
      this.isDragOver = false
      const files = Array.from(event.dataTransfer.files)
      this.addFiles(files)
    },
    
    addFiles(files) {
      console.log('🔍 addFiles called with:', files)
      const validFiles = files.filter(file => {
        const extension = '.' + file.name.split('.').pop().toLowerCase()
        const allowedExtensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv', '.json']
        return allowedExtensions.includes(extension) && file.size <= 100 * 1024 * 1024 // 100MB
      })
      
      console.log('🔍 Valid files after filtering:', validFiles)
      console.log('🔍 Current selectedFiles before adding:', this.selectedFiles)
      
      this.selectedFiles = [...this.selectedFiles, ...validFiles]
      
      console.log('🔍 selectedFiles after adding:', this.selectedFiles)
    },
    
    removeFile(index) {
      this.selectedFiles.splice(index, 1)
    },
    
    clearFiles() {
      this.selectedFiles = []
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    },
    
    async uploadFiles() {
      // Check consent before proceeding with audit document upload
      try {
        const consentService = (await import('@/services/consentService.js')).default;
        const { CONSENT_ACTIONS } = await import('@/utils/consentManager.js');
        
        const canProceed = await consentService.checkAndRequestConsent(
          CONSENT_ACTIONS.UPLOAD_AUDIT
        );
        
        // If user declined consent, stop here
        if (!canProceed) {
          console.log('Audit document upload cancelled by user (consent declined)');
          return;
        }
      } catch (consentError) {
        console.error('Error checking consent:', consentError);
        // Continue with upload if consent check fails
      }
      console.log('🔍 Upload button clicked!')
      console.log('🔍 Selected files:', this.selectedFiles)
      console.log('🔍 Selected files length:', this.selectedFiles.length)
      
      if (this.selectedFiles.length === 0) {
        console.warn('No files selected')
        return
      }
      
      const auditId = this.currentAuditId
      console.log('🔍 Current audit ID for upload:', auditId)
      console.log('🔍 Audit ID type:', typeof auditId)
      console.log('🔍 Selected existing audit ID:', this.selectedExistingAuditId)
      console.log('🔍 Props auditId:', this.auditId)
      console.log('🔍 Route params auditId:', this.$route.params.auditId)
      console.log('🔍 Route query auditId:', this.$route.query.auditId)
      
      if (!auditId || auditId === 'Unknown') {
        console.warn('No valid audit ID, cannot upload files')
        this.$popup?.error('No valid audit ID. Please refresh the page.')
        return
      }
      
      this.uploading = true
      this.uploadProgress = 0
      const totalFiles = this.selectedFiles.length
      
      try {
        for (let i = 0; i < this.selectedFiles.length; i++) {
          const file = this.selectedFiles[i]
          const formData = new FormData()
          
          formData.append('file', file)
          formData.append('policy_id', this.selectedPolicyId || '')
          formData.append('subpolicy_id', this.selectedSubPolicyId || '')
          formData.append('document_type', 'evidence')
          formData.append('external_source', 'manual')
          
          const response = await api.post(
            `/api/ai-audit/${auditId}/upload-document/`,
            formData,
            {
              headers: { 'Content-Type': 'multipart/form-data' },
              onUploadProgress: (progressEvent) => {
                const fileProgress = (progressEvent.loaded / progressEvent.total) * 100
                this.uploadProgress = Math.round(((i + fileProgress / 100) / this.selectedFiles.length) * 100)
              }
            }
          )
          
          if (response.data.success) {
            this.$popup?.success(`File "${file.name}" uploaded successfully`)
          }
        }
        
        this.selectedFiles = []
        this.uploadProgress = 100
        await this.loadUploadedDocuments()
        
        // Show success popup for all files uploaded
        this.$popup?.success(`Successfully uploaded ${totalFiles} file(s). Documents are now available in the Uploaded Documents section.`)
        // AI relevance analysis is disabled per request
        
      } catch (error) {
        console.error('❌ Upload error details:', error)
        console.error('❌ Error response:', error.response?.data)
        console.error('❌ Error status:', error.response?.status)
        console.error('❌ Error message:', error.message)
        
        let errorMessage = 'Error uploading files. Please try again.'
        if (error.response?.data?.error) {
          errorMessage = `Upload failed: ${error.response.data.error}`
        } else if (error.message) {
          errorMessage = `Upload failed: ${error.message}`
        }
        
        this.$popup?.error(errorMessage)
      } finally {
        this.uploading = false
        this.uploadProgress = 0
      }
    },
    
    async loadUploadedDocuments() {
      try {
        const auditId = this.currentAuditId
        if (!auditId || auditId === 'Unknown') {
          console.warn('No valid audit ID, skipping document load')
          return
        }
        console.log('📋 Loading documents for audit:', auditId)
        const response = await api.get(`/api/ai-audit/${auditId}/documents/`)
        console.log('📋 Documents response:', response.data)
        console.log('📋 Response success:', response.data.success)
        console.log('📋 Response documents array:', response.data.documents)
        console.log('📋 Raw response status:', response.status)
        if (response.data.success) {
          // Map API response fields to component expected fields
          this.uploadedDocuments = response.data.documents.map(doc => ({
            document_id: doc.document_id,
            document_name: doc.file_name,
            file_size: doc.file_size,
            uploaded_date: doc.uploaded_date,
            document_type: doc.file_type,
            processing_status: doc.processing_status || 'pending',
            upload_status: doc.upload_status || 'uploaded',
            mapped_policy: doc.policy_name || doc.mapped_policy || null,
            mapped_subpolicy: doc.subpolicy_name || doc.mapped_subpolicy || null,
            compliance_status: doc.compliance_status || null,
            confidence_score: doc.confidence_score || null,
            compliance_analyses: doc.compliance_analyses || null
          }))
          console.log('📋 Loaded documents:', this.uploadedDocuments.length)
          console.log('📋 Document details:', this.uploadedDocuments)
        } else {
          console.warn('📋 Failed to load documents:', response.data.error)
          this.uploadedDocuments = []
        }
      } catch (error) {
        console.error('Error loading uploaded documents:', error)
        this.uploadedDocuments = []
      }
    },
    
    async startAIProcessing() {
      try {
        console.log('🚀 startAIProcessing called!')
        console.log('🚀 uploadedDocuments.length:', this.uploadedDocuments.length)
        console.log('🚀 uploadedDocuments:', this.uploadedDocuments)
        
        const auditId = this.currentAuditId
        if (!auditId || auditId === 'Unknown') {
          console.warn('No valid audit ID, cannot start AI processing')
          this.$popup?.error('No valid audit ID. Please refresh the page.')
          return
        }
        
        if (this.uploadedDocuments.length === 0) {
          console.warn('No uploaded documents to process')
          this.$popup?.error('Please upload documents before starting AI processing.')
          return
        }
        
        // Check authentication status
        const token = localStorage.getItem('access_token')
        if (!token) {
          console.warn('No JWT token found, cannot start AI processing')
          this.$popup?.error('Authentication required. Please log in again.')
          return
        }
        
        // Set loading state
        this.isProcessingAI = true
        
        console.log('🚀 Starting AI processing request...')
        console.log('🚀 Audit ID:', auditId)
        console.log('🚀 Token available:', !!token)
        
        const response = await api.post(`/api/ai-audit/${auditId}/start-processing/`, {
          processing_options: {
            enable_compliance_mapping: true,
            enable_risk_assessment: true,
            enable_recommendations: true
          }
        }, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })
        
        console.log('🚀 AI processing response:', response.data)
        
        if (response.data && response.data.success) {
          this.$popup?.success('AI processing started successfully')
          
          // Wait a moment then refresh status manually
          setTimeout(() => {
            console.log('🔄 Manually refreshing status after AI processing start')
            this.loadAIStatus()
          }, 2000)
          
          this.startStatusPolling()
        } else {
          const errorMessage = response.data?.error || response.data?.message || 'Unknown error occurred'
          console.error('🚀 AI processing failed:', errorMessage)
          this.$popup?.error(`AI processing failed: ${errorMessage}`)
        }
      } catch (error) {
        console.error('Error starting AI processing:', error)
        
        // Provide more specific error messages
        let errorMessage = 'Error starting AI processing. Please try again.'
        
        if (error.response) {
          // Server responded with error status
          const status = error.response.status
          const data = error.response.data
          
          console.error('🚀 Server error response:', { status, data })
          
          if (status === 401) {
            errorMessage = 'Authentication failed. Please log in again.'
          } else if (status === 403) {
            errorMessage = 'You do not have permission to start AI processing.'
          } else if (status === 404) {
            errorMessage = 'Audit not found. Please refresh the page.'
          } else if (status === 400) {
            errorMessage = data?.error || data?.message || 'Invalid request. Please check your data.'
          } else if (status >= 500) {
            errorMessage = 'Server error. Please try again later.'
          } else {
            errorMessage = data?.error || data?.message || `Server error (${status}). Please try again.`
          }
        } else if (error.request) {
          // Network error
          console.error('🚀 Network error:', error.request)
          errorMessage = 'Network error. Please check your connection and try again.'
        } else {
          // Other error
          console.error('🚀 Other error:', error.message)
          errorMessage = error.message || 'An unexpected error occurred.'
        }
        
        this.$popup?.error(errorMessage)
      } finally {
        // Always reset loading state
        this.isProcessingAI = false
      }
    },
    
    async loadAIStatus() {
      try {
        const auditId = this.currentAuditId
        if (!auditId || auditId === 'Unknown') {
          console.warn('No valid audit ID, skipping AI status load')
          return
        }
        console.log('📊 Loading AI status for audit:', auditId)
        const response = await api.get(`/api/ai-audit/${auditId}/status/`)
        console.log('📊 AI status response:', response.data)
        if (response.data.success) {
          this.processingStatus = response.data.processing_status
          this.complianceResults = response.data.compliance_results || []
          console.log('📊 Updated processing status:', this.processingStatus)
        }
        
        // Load AI processing results from completed documents
        await this.loadAIProcessingResults()
      } catch (error) {
        console.error('Error loading AI status:', error)
      }
    },
    
    async loadAIProcessingResults() {
      try {
        const auditId = this.currentAuditId
        if (!auditId || auditId === 'Unknown') {
          return
        }
        
        console.log('🤖 Loading AI processing results for audit:', auditId)
        const response = await api.get(`/api/ai-audit/${auditId}/documents/`)
        
        if (response.data.success) {
          // Filter documents that have been processed by AI
          const processedDocs = response.data.documents.filter(doc => 
            doc.processing_status === 'completed' && doc.processing_results
          )
          
          this.aiProcessingResults = processedDocs.map(doc => {
            try {
              const processingResults = JSON.parse(doc.processing_results || '{}')
              const complianceMapping = JSON.parse(doc.compliance_mapping || '{}')
              
              return {
                document_id: doc.document_id,
                document_name: doc.file_name,
                compliance_status: doc.compliance_status || 'unknown',
                risk_level: doc.risk_level || 'medium',
                confidence_score: parseFloat(doc.confidence_score) || 0.0,
                ai_recommendations: doc.ai_recommendations || '',
                extracted_text: doc.extracted_text || '',
                processing_results: processingResults,
                compliance_mapping: complianceMapping
              }
            } catch (e) {
              console.error('Error parsing AI results for document:', doc.document_id, e)
              return null
            }
          }).filter(result => result !== null)
          
          console.log('🤖 Loaded AI processing results:', this.aiProcessingResults.length)
        }
      } catch (error) {
        console.error('Error loading AI processing results:', error)
      }
    },
    
    startStatusPolling() {
      // Disable continuous polling for now to prevent log spam
      console.log('🛑 Status polling disabled to prevent log spam')
      // this.pollingInterval = setInterval(() => {
      //   this.loadAIStatus()
      // }, 10000)
    },
    
    
    // eslint-disable-next-line no-unused-vars
    // viewDocument(doc) {
    //   // TODO: Implement document viewer
    //   this.$popup?.info('Document viewer coming soon!')
    // },
    
    // eslint-disable-next-line no-unused-vars
    async deleteDocument(documentId) {
      if (confirm('Are you sure you want to delete this document?')) {
        try {
          console.log('🗑️ Deleting document:', documentId)
          
          const auditId = this.currentAuditId
          if (!auditId || auditId === 'Unknown') {
            this.$popup?.error('No valid audit ID. Please refresh the page.')
            return
          }
          
          const response = await api.delete(`/api/ai-audit/${auditId}/documents/${documentId}/`)
          
          if (response.data.success) {
            console.log('✅ Document deleted successfully')
            this.$popup?.success('Document deleted successfully!')
            
            // Reload the documents list
            await this.loadUploadedDocuments()
          } else {
            console.error('❌ Delete failed:', response.data.error)
            this.$popup?.error(`Delete failed: ${response.data.error}`)
          }
        } catch (error) {
          console.error('❌ Error deleting document:', error)
          
          if (error.response?.status === 404) {
            this.$popup?.error('Document not found or already deleted.')
          } else if (error.response?.status === 401) {
            this.$popup?.error('Authentication required. Please log in again.')
          } else {
            this.$popup?.error(`Delete failed: ${error.response?.data?.error || error.message}`)
          }
        }
      }
    },
    
    // eslint-disable-next-line no-unused-vars
    reviewFinding(result) {
      // TODO: Implement finding review modal
      this.$popup?.info('Finding review coming soon!')
    },
    
    getPolicyName(policyId) {
      const policy = this.policies.find(p => p.PolicyId === policyId)
      return policy ? policy.PolicyName : 'Unknown Policy'
    },
    
    getSubPolicyName(subPolicyId) {
      const subpolicy = this.subpolicies.find(sp => sp.SubPolicyId === subPolicyId)
      return subpolicy ? subpolicy.SubPolicyName : 'Unknown Sub-policy'
    },
    
    goToReviews() {
      this.$router.push('/auditor/reviews')
    },
    
    reviewAIResult(result) {
      // Show detailed AI analysis in a modal or new page
      console.log('Reviewing AI result:', result)
      this.$popup?.info(`Reviewing AI analysis for: ${result.document_name}`)
    },
    
    async downloadAIReport(result) {
      // Generate and download comprehensive AI analysis report
      console.log('📊 Downloading comprehensive AI report for:', result)
      
      try {
        const auditId = this.currentAuditId
        console.log('📊 Generating comprehensive report for audit:', auditId)
        
        // Call the new comprehensive report endpoint
        const response = await api.get(`/api/ai-audit/${auditId}/download-report/`, {
          responseType: 'blob',
          timeout: 30000 // 30 second timeout
        })
        
        // Create blob from response
        const blob = new Blob([response.data], {
          type: 'application/json'
        })
        
        // Create download link
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `AI_Audit_Comprehensive_Report_${auditId}_${new Date().toISOString().slice(0,10)}.json`
        link.target = '_blank'
        
        // Trigger download
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        // Clean up
        window.URL.revokeObjectURL(url)
        
        console.log(`📊 Comprehensive AI audit report downloaded successfully for audit ${auditId}`)
        
        // Show success message
        this.$popup?.success(`Comprehensive AI audit report for Audit ID ${auditId} downloaded successfully!`)
        
        // Send push notification about successful download
        if (window.sendPushNotification) {
          window.sendPushNotification({
            title: 'AI Audit Report Downloaded',
            message: `Comprehensive AI audit report for Audit ID ${auditId} has been downloaded successfully.`,
            category: 'audit',
            priority: 'medium',
            user_id: 'default_user'
          })
        }
        
      } catch (error) {
        console.error('❌ Error downloading comprehensive AI report:', error)
        
        // Fallback to simple JSON report if comprehensive report fails
        console.log('📊 Falling back to simple report generation')
        
        const reportData = {
          document_name: result.document_name || 'Unknown Document',
          compliance_status: result.compliance_status || 'unknown',
          risk_level: result.risk_level || 'medium',
          confidence_score: result.confidence_score || 0,
          ai_recommendations: result.ai_recommendations || 'No recommendations available',
          analysis_timestamp: result.compliance_mapping?.analysis_timestamp || new Date().toISOString(),
          found_keywords: result.compliance_mapping?.found_keywords || [],
          extracted_text_preview: result.extracted_text || 'No text extracted',
          audit_id: this.currentAuditId,
          processing_details: {
            ai_model_used: 'llama3.2:3b',
            processing_method: 'Ollama AI/ML Analysis',
            compliance_checking: 'Structured Compliance Analysis'
          }
        }
        
        const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `AI_Analysis_Report_${(result.document_name || 'Unknown_Document').replace(/\.[^/.]+$/, '')}.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
        
        this.$popup?.success('AI analysis report downloaded successfully! (Fallback mode)')
      }
    }
    ,
    async checkDocumentCompliance(doc) {
      try {
        doc._checking = true
        const auditId = this.currentAuditId
        console.log('🧪 Checking compliance:', { auditId, document_id: doc.document_id })
        const res = await api.post(`/api/ai-audit/${auditId}/documents/${doc.document_id}/check/`)
        console.log('🧪 Check response:', res.status, res.data)
        if (res.data && res.data.success) {
          doc.compliance_status = res.data.status
          doc.confidence_score = res.data.confidence
          doc.compliance_analyses = res.data.analyses
          this.$popup?.success(`Compliance checked for "${doc.document_name}"`)
        } else {
          const msg = res.data?.error || 'Compliance check failed'
          console.warn('🧪 Check failed:', msg)
          this.$popup?.error(msg)
        }
      } catch (e) {
        const status = e?.response?.status
        const data = e?.response?.data
        console.error('🧪 Compliance check error:', { status, data, message: e?.message })
        this.$popup?.error(data?.error || e?.message || 'Compliance check error')
      } finally {
        doc._checking = false
      }
    }
  }
}
</script>

<style scoped>
@import './AssignAudit.css';

.ai-audit-document-upload-page {
  max-width: calc(100vw - 180px);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
  box-sizing: border-box;
  margin-left: 280px;
  font-family: var(--font-family, inherit);
  color: var(--text-primary);
  overflow-y: auto;
}

.audit-content {
  width: 100%;
  max-width: var(--form-container-max-width, 1400px);
  min-width: 0;
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.audit-title {
  font-size: 1.7rem;
  font-weight: 700;
  color: black;
  margin-bottom: 8px;
  margin-top: 22px;
  letter-spacing: 0.01em;
  position: relative;
  display: inline-block;
  padding-bottom: 6px;
  background: transparent;
  font-family: var(--font-family, inherit);
}

.audit-title::after {
  display: none;
}

.audit-subtitle {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 48px;
  margin-top: -10px;
  line-height: 1.5;
}

.audit-selection-section {
  margin-bottom: 2rem !important;
  margin-top: 0 !important;
}

.audit-selection-section h3 {
  color: #2c3e50;
  margin-bottom: 15px;
  font-size: 1rem;
  font-weight: 600;
}

/* Custom Dropdown Styles */
.custom-dropdown-container {
  position: relative;
  width: 100%;
  max-width: 600px;
}

.dropdown-trigger {
  width: 100%;
  cursor: pointer;
}

.dropdown-selected {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #ffffff;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.selected-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.dropdown-icon {
  color: #4f7cff;
  font-size: 16px;
  width: 18px;
  text-align: center;
}

.selected-text {
  flex: 1;
  min-width: 0;
}

.selected-title {
  color: #2c3e50;
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.placeholder-text {
  color: #9ca3af;
  font-size: 14px;
  font-style: italic;
}

.dropdown-arrow {
  color: #6b7280;
  font-size: 12px;
  transition: transform 0.3s ease;
  width: 18px;
  text-align: center;
}

.dropdown-arrow.is-open {
  transform: rotate(180deg);
  color: #4f7cff;
}

.dropdown-options {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #ffffff;
  border-top: none;
  border-radius: 0 0 12px 12px;
  z-index: 1000;
  max-height: 400px;
  overflow: hidden;
  animation: dropdownSlideDown 0.3s ease;
}

@keyframes dropdownSlideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dropdown-search {
  position: relative;
  padding: 8px 12px;
  border-bottom: 1px solid #e5e7eb;
  background: #f8f9fa;
}

.search-input {
  width: 100%;
  padding: 6px 20px 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 11px;
  background: #ffffff;
  transition: border-color 0.3s ease;
}

.search-input:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(79, 124, 255, 0.1);
}

.search-icon {
  position: absolute;
  right: 18px;
  top: 50%;
  transform: translateY(-50%);
  color: #6b7280;
  font-size: 11px;
}

.options-list {
  max-height: 300px;
  overflow-y: auto;
}

.dropdown-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.dropdown-option:hover {
  background: #f8f9ff;
}

.dropdown-option.is-selected {
  background: linear-gradient(135deg, #e3f2fd 0%, #f8f9ff 100%);
  border-left: 4px solid #4f7cff;
}

.dropdown-option:last-child {
  border-bottom: none;
}

.option-content {
  flex: 1;
  min-width: 0;
}

.option-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  gap: 12px;
}

.option-title {
  color: #2c3e50;
  font-weight: 600;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.option-id {
  color: #6b7280;
  font-size: 10px;
  font-weight: 500;
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 12px;
  white-space: nowrap;
}

.option-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 11px;
}

.option-due-date {
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 6px;
}

.option-due-date i {
  color: #9ca3af;
  font-size: 10px;
}

.option-type {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.option-type.ai {
  background: #e3f2fd;
  color: #1976d2;
}

.option-type.i {
  background: #f3e5f5;
  color: #7b1fa2;
}

.option-type.a {
  background: #e8f5e8;
  color: #2e7d32;
}

.option-check {
  color: #4f7cff;
  font-size: 14px;
  margin-left: 12px;
}

.no-options {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 24px 12px;
  color: #6b7280;
  font-style: italic;
  text-align: center;
  font-size: 12px;
}

.no-options i {
  font-size: 18px;
  color: #9ca3af;
}

.hint-text {
  color: #6b7280;
  font-size: 13px;
  margin-top: 8px;
  font-style: italic;
}

.error-text {
  color: #dc2626;
  font-size: 13px;
  margin-top: 8px;
  font-weight: 500;
}

.audit-info-section {
  margin-bottom: 2rem;
  margin-top: 0 !important;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.audit-info-section h3 {
  color: #2c3e50;
  margin-bottom: 15px;
}

.audit-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.audit-meta span {
  background: white;
  border: 1px solid #e5e7eb;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 14px;
}


.upload-section {
  margin-bottom: 2rem;
  width: 100%;
  padding-bottom: 1.5rem;
}

.upload-section h3 {
  color: #2c3e50;
  margin-bottom: 15px;
}

.upload-description {
  color: #6c757d;
  margin-bottom: 20px;
}

.policy-selection {
  margin-bottom: 25px;
}

.policy-display {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 15px;
}

.policy-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.policy-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.policy-label {
  font-weight: 600;
  color: #495057;
  font-size: 14px;
}

.policy-value {
  color: #212529;
  font-size: 16px;
  padding: 8px 12px;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.policy-dropdowns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.form-control {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.file-upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 20px;
}

.file-upload-area:hover,
.file-upload-area.dragover {
  border-color: #6b7280;
  background-color: white;
}

.upload-content {
  color: #6c757d;
}

.upload-icon {
  font-size: 48px;
  color: #6b7280;
  margin-bottom: 15px;
}

.upload-content h4 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.file-limit {
  font-size: 12px;
  color: #95a5a6;
  margin-top: 10px;
}

.selected-files {
  margin-bottom: 20px;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-icon {
  color: #6b7280;
}

.file-details {
  display: flex;
  flex-direction: column;
}

.file-name {
  font-weight: 500;
  color: #2c3e50;
}

.file-size {
  font-size: 12px;
  color: #6c757d;
}

.remove-btn {
  background: var(--btn-primary-bg, #4f7cff);
  color: var(--btn-primary-text, #fff);
  border: 1px solid var(--btn-primary-bg, #4f7cff);
  border-radius: 4px;
  padding: 5px 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.remove-btn:hover {
  background: var(--btn-primary-hover-bg, #3b5bcc);
  border-color: var(--btn-primary-hover-bg, #3b5bcc);
}

.upload-progress {
  margin-bottom: 20px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #f1f5f9;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: #6b7280;
  transition: width 0.3s ease;
}

.progress-text {
  text-align: center;
  color: #6c757d;
  font-size: 14px;
}

.upload-actions {
  display: flex;
  gap: 15px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--btn-primary-bg, #4f7cff);
  color: var(--btn-primary-text, #fff);
  border: 1px solid var(--btn-primary-bg, #4f7cff);
}

.btn-primary:hover:not(:disabled) {
  background: var(--btn-primary-hover-bg, #3b5bcc);
  border-color: var(--btn-primary-hover-bg, #3b5bcc);
}

.btn-secondary {
  background: var(--btn-primary-bg, #4f7cff);
  color: var(--btn-primary-text, #fff);
  border: 1px solid var(--btn-primary-bg, #4f7cff);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--btn-primary-hover-bg, #3b5bcc);
  border-color: var(--btn-primary-hover-bg, #3b5bcc);
}

.btn-success {
  background: var(--btn-primary-bg, #4f7cff);
  color: var(--btn-primary-text, #fff);
  border: 1px solid var(--btn-primary-bg, #4f7cff);
}

.btn-success:hover:not(:disabled) {
  background: var(--btn-primary-hover-bg, #3b5bcc);
  border-color: var(--btn-primary-hover-bg, #3b5bcc);
}

.btn.processing {
  opacity: 0.8;
  cursor: not-allowed;
}

.btn.processing i.fa-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.btn-danger {
  background: var(--btn-primary-bg, #4f7cff);
  color: var(--btn-primary-text, #fff);
  border: 1px solid var(--btn-primary-bg, #4f7cff);
}

.btn-danger:hover:not(:disabled) {
  background: var(--btn-primary-hover-bg, #3b5bcc);
  border-color: var(--btn-primary-hover-bg, #3b5bcc);
}

.btn-outline {
  background: var(--btn-primary-bg, #4f7cff);
  color: var(--btn-primary-text, #fff);
  border: 1px solid var(--btn-primary-bg, #4f7cff);
}

.btn-outline:hover:not(:disabled) {
  background: var(--btn-primary-hover-bg, #3b5bcc);
  border-color: var(--btn-primary-hover-bg, #3b5bcc);
}


.compliance-requirements {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.compliance-requirements h4 {
  margin: 0 0 1rem 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.requirements-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.requirement-item {
  background: white;
  padding: 16px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.requirement-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.requirement-title {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.requirement-type {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.requirement-type.mandatory {
  background: #fee2e2;
  color: #dc2626;
}

.requirement-type.optional {
  background: #f3f4f6;
  color: #6b7280;
}

.requirement-description {
  margin: 8px 0;
  color: #6b7280;
  font-size: 14px;
  line-height: 1.5;
}

.requirement-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}

.risk-level {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
}

.risk-level.high {
  background: #fee2e2;
  color: #dc2626;
}

.risk-level.medium {
  background: #fef3c7;
  color: #d97706;
}

.risk-level.low {
  background: #dcfce7;
  color: #16a34a;
}

.mandatory {
  padding: 2px 6px;
  background: #dbeafe;
  color: #2563eb;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
}

.no-requirements {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
  font-style: italic;
}

.uploaded-documents {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
 
}

.documents-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 20px;
}

.document-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px 16px;
  transition: all 0.3s ease;
}

.document-card:hover {
  background: #f8fafc;
  border-color: #d1d5db;
}

.document-content {
  display: flex;
  align-items: center;
  gap: 20px;
  width: 100%;
}

.document-main {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.document-icon {
  font-size: 20px;
  color: #6b7280;
  flex-shrink: 0;
}

.document-info {
  min-width: 0;
  flex: 1;
}

.document-info h4 {
  color: #2c3e50;
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.document-meta {
  color: #6c757d;
  font-size: 11px;
  margin: 0;
  white-space: nowrap;
}

.document-type {
  flex-shrink: 0;
  min-width: 120px;
}

.document-type span {
  font-size: 12px;
  color: #6c757d;
}

.document-status {
  flex-shrink: 0;
}

.status-badge {
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  white-space: nowrap;
}

.status-badge.pending {
  background: #fff3cd;
  color: #856404;
}

.status-badge.processing {
  background: #d1ecf1;
  color: #0c5460;
}

.status-badge.completed {
  background: #d4edda;
  color: #155724;
}

.status-badge.failed {
  background: #f8d7da;
  color: #721c24;
}

.document-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.ai-processing-status {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.processing-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 16px;
  margin-top: 16px;
}

.processing-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.status-label {
  color: #6c757d;
  font-weight: 500;
}

.status-value {
  color: #2c3e50;
  font-weight: 600;
}

.ai-info {
  margin-top: 15px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.ai-note {
  margin: 0;
  color: #495057;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-note i {
  color: #4f7cff;
}

.ai-benefits {
  font-size: 12px;
  color: #6c757d;
  font-style: italic;
  margin-left: 8px;
}

.compliance-results {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.result-card {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.result-header h4 {
  color: #2c3e50;
  margin: 0;
  flex: 1;
}

.compliance-status {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
}

.compliance-status.compliant {
  background: #d4edda;
  color: #155724;
}

.compliance-status.non_compliant {
  background: #f8d7da;
  color: #721c24;
}

.compliance-status.partially_compliant {
  background: #fff3cd;
  color: #856404;
}

.compliance-status.requires_review {
  background: #d1ecf1;
  color: #0c5460;
}

.result-details p {
  margin-bottom: 8px;
  font-size: 14px;
  color: #6c757d;
}

.result-actions {
  margin-top: 15px;
}

.action-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: -120px;
  border-top: none !important;
}

@media (max-width: 768px) {
  .custom-dropdown-container {
    max-width: 100%;
  }
  
  .dropdown-selected {
    padding: 14px 16px;
  }
  
  .selected-content {
    gap: 10px;
  }
  
  .dropdown-icon {
    font-size: 16px;
  }
  
  .selected-title,
  .placeholder-text {
    font-size: 15px;
  }
  
  .dropdown-options {
    max-height: 300px;
  }
  
  .dropdown-option {
    padding: 14px 16px;
  }
  
  .option-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .option-title {
    font-size: 14px;
  }
  
  .option-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .policy-dropdowns {
    grid-template-columns: 1fr;
  }
  
  .integration-options {
    flex-direction: column;
    gap: 0;
  }
  
  .integration-item {
    border-right: none;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .integration-item:last-child {
    border-bottom: none;
  }
  
  .document-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .document-main {
    width: 100%;
  }
  
  .document-type {
    min-width: auto;
  }
  
  .document-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .results-grid {
    grid-template-columns: 1fr;
  }
  
  .action-buttons {
    flex-direction: column;
  }
}

/* Compliance Requirements Styles */
.compliance-requirements {
  margin-top: 20px;
  padding: 20px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.compliance-requirements h4 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 16px;
}

.requirements-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.requirement-item {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 15px;
}

.requirement-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.requirement-title {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.requirement-type {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.requirement-type.security {
  background: #fef2f2;
  color: #dc2626;
}

.requirement-type.compliance {
  background: #f0f9ff;
  color: #0369a1;
}

.requirement-type.operational {
  background: #f0fdf4;
  color: #16a34a;
}

.requirement-description {
  margin: 0 0 10px 0;
  color: #666;
  font-size: 13px;
  line-height: 1.4;
}

.requirement-meta {
  display: flex;
  gap: 10px;
  align-items: center;
}

.risk-level {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
}

.risk-level.high {
  background: #fef2f2;
  color: #dc2626;
}

.risk-level.medium {
  background: #fef3c7;
  color: #d97706;
}

.risk-level.low {
  background: #f0fdf4;
  color: #16a34a;
}

.mandatory {
  background: #fef2f2;
  color: #dc2626;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
}

/* AI Processing Results Styles */
.ai-processing-results {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.ai-processing-results h3 {
  color: #2c3e50;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.result-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.result-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.result-header h4 {
  color: #2c3e50;
  margin: 0;
  flex: 1;
  font-size: 16px;
}

.compliance-status {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.compliance-status.compliant {
  background: #d4edda;
  color: #155724;
}

.compliance-status.partially_compliant {
  background: #fff3cd;
  color: #856404;
}

.compliance-status.non_compliant {
  background: #f8d7da;
  color: #721c24;
}

.compliance-status.unknown {
  background: #e2e3e5;
  color: #6c757d;
}

.ai-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.metric-label {
  font-size: 12px;
  color: #6c757d;
  font-weight: 500;
}

.metric-value {
  font-size: 14px;
  color: #2c3e50;
  font-weight: 600;
}

.risk-level {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.risk-level.low {
  background: #d4edda;
  color: #155724;
}

.risk-level.medium {
  background: #fff3cd;
  color: #856404;
}

.risk-level.high {
  background: #f8d7da;
  color: #721c24;
}

.ai-analysis, .ai-recommendations, .extracted-text {
  margin-bottom: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.ai-analysis h5, .ai-recommendations h5, .extracted-text h5 {
  margin: 0 0 10px 0;
  color: #2c3e50;
  font-size: 14px;
  font-weight: 600;
}

.ai-analysis p, .ai-recommendations p {
  margin: 5px 0;
  font-size: 13px;
  color: #495057;
  line-height: 1.4;
}

.text-preview {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 10px;
  max-height: 150px;
  overflow-y: auto;
  font-size: 12px;
  color: #495057;
  line-height: 1.4;
}

.result-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #f0f0f0;
}

.result-actions .btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

@media (max-width: 768px) {
  .results-grid {
    grid-template-columns: 1fr;
  }
  
  .ai-metrics {
    grid-template-columns: 1fr;
  }
  
  .result-actions {
    flex-direction: column;
  }
}
/* Force compact layout for compliance details */
.ai-audit-document-upload-page .compliance-details-expanded {
  max-height: 60vh !important;
  overflow-y: auto !important;
  padding: 15px !important;
  margin: 20px 0 !important;
}

.ai-audit-document-upload-page .compliance-details-expanded * {
  box-sizing: border-box !important;
}

/* Enhanced Compliance Details Styles */
.compliance-details-expanded {
  margin-top: 20px !important;
  margin-bottom: 20px !important;
  padding: 15px !important;
  background: #ffffff !important;
  border: 1px solid #e9ecef !important;
  border-radius: 8px !important;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1) !important;
  max-width: 100% !important;
  width: 100% !important;
  box-sizing: border-box !important;
  overflow-x: hidden !important;
  position: relative !important;
  z-index: 1 !important;
  max-height: 60vh !important;
  overflow-y: auto !important;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e9ecef;
}

.details-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.4rem;
  font-weight: 600;
}

.details-header h3 i {
  color: #007bff;
  margin-right: 8px;
}

.overall-status-card {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
  border-radius: 8px !important;
  padding: 12px !important;
  margin-bottom: 12px !important;
  border: 1px solid #dee2e6 !important;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  flex-wrap: wrap;
  gap: 10px;
}

.status-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-header h4 i {
  color: #007bff;
}

.status-badges {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.compliance-status-badge {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.compliance-status-badge.compliant {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.compliance-status-badge.non_compliant {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.compliance-status-badge.partially_compliant {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.compliance-status-badge.unknown {
  background: #e2e3e5;
  color: #6c757d;
  border: 1px solid #d6d8db;
}

.confidence-badge {
  background: #e3f2fd;
  color: #1976d2;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid #bbdefb;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  font-size: 14px;
  color: #495057;
}

.summary-item i {
  color: #007bff;
  width: 16px;
  text-align: center;
}

.detailed-analysis {
  margin-top: 20px;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e9ecef;
}

.analysis-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.analysis-header h4 i {
  color: #28a745;
}

.analysis-count {
  background: #007bff;
  color: white;
  padding: 6px 12px;
  border-radius: 15px;
  font-size: 12px;
  font-weight: 600;
}

.requirements-grid {
  display: grid !important;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)) !important;
  gap: 12px !important;
  margin-top: 12px !important;
}

.requirement-card {
  background: #ffffff !important;
  border: 1px solid #e9ecef !important;
  border-radius: 6px !important;
  padding: 10px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
  transition: all 0.3s ease !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
  margin-bottom: 8px !important;
}

.requirement-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.requirement-header {
  margin-bottom: 20px;
}

.requirement-number {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  flex-wrap: wrap;
  gap: 15px;
}

.req-idx {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
  background: #f8f9fa;
  padding: 6px 12px;
  border-radius: 15px;
  border: 1px solid #dee2e6;
  line-height: 1.3;
  word-wrap: break-word;
  hyphens: auto;
  display: block;
  max-width: 100%;
}

.relevance-meter {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 200px;
}

.meter-label {
  font-size: 12px;
  color: #6c757d;
  font-weight: 600;
  min-width: 60px;
}

.meter-bar {
  flex: 1;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

.meter-fill {
  height: 100%;
  background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.meter-value {
  font-size: 12px;
  font-weight: 700;
  color: #2c3e50;
  min-width: 35px;
  text-align: right;
}

.evidence-section, .missing-section {
  margin-bottom: 8px !important;
  padding: 8px !important;
  border-radius: 4px !important;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  font-size: 14px;
  color: #2c3e50;
}

.section-header i {
  font-size: 16px;
}

.text-success {
  color: #28a745 !important;
}

.text-warning {
  color: #ffc107 !important;
}

.evidence-list, .missing-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.evidence-item, .missing-item {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
}

.missing-item {
  background: #fffbf0;
}

.evidence-item i, .missing-item i {
  color: #6c757d;
  margin-top: 2px;
  font-size: 12px;
}

.no-analysis {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  color: #6c757d;
  font-style: italic;
  text-align: center;
  justify-content: center;
}

.no-analysis i {
  color: #6c757d;
}

.no-analysis-available {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 30px;
  background: #f8f9fa;
  border-radius: 10px;
  color: #6c757d;
  font-style: italic;
  margin-top: 20px;
}

.no-analysis-available i {
  font-size: 24px;
  color: #adb5bd;
}

/* Responsive Design */
@media (min-width: 1200px) {
  .requirements-grid {
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    max-width: 1200px;
    margin: 20px auto 0;
  }
}

@media (max-width: 768px) {
  .compliance-details-expanded {
    padding: 10px !important;
    max-height: 50vh !important;
    margin-top: 15px !important;
    margin-bottom: 15px !important;
  }
  
  .details-header {
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 6px !important;
    margin-bottom: 12px !important;
  }
  
  .details-header h3 {
    font-size: 1rem !important;
  }
  
  .requirements-grid {
    grid-template-columns: 1fr !important;
    gap: 8px !important;
  }
  
  .requirement-card {
    padding: 8px !important;
    margin-bottom: 6px !important;
  }
  
  .overall-status-card {
    padding: 10px !important;
    margin-bottom: 10px !important;
  }
  
  .status-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .status-badges {
    width: 100%;
    justify-content: flex-start;
  }
  
  .status-summary {
    grid-template-columns: 1fr;
  }
  
  .requirement-number {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .relevance-meter {
    width: 100%;
    min-width: auto;
  }
  
  .analysis-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>
