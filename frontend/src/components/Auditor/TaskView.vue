<template>
  <div class="audit_task-view">
    <div v-if="error" class="audit_error-message">
      {{ error }}
      <button @click="retryFetch" class="audit_retry-button">Retry</button>
    </div>
    <div v-else-if="loading" class="audit_loading">
      Loading audit details...
    </div>
    <div v-else-if="auditDetails" class="audit_content">
      <div class="audit-details">
        <div class="audit-details-header">
          <button class="policy-dashboard-back-btn" @click="$router.back()" aria-label="Back">
            <i class="fas fa-arrow-left"></i>
          </button>
          
          <h1>Audit Details</h1>
        </div>
        
        <!-- Read-Only Mode Banner -->
        <div v-if="isViewOnly" class="audit_readonly-banner">
          <i class="fas fa-eye"></i>
          <span>Viewing audit report in read-only mode</span>
        </div>
        <div class="audit_details-container">
          <div class="audit_detail-item">
            <h3>Title</h3>
            <p>{{ auditDetails.title }}</p>
          </div>
          <div class="audit_detail-item">
            <h3>Scope</h3>
            <p>{{ auditDetails.scope }}</p>
          </div>
          <div class="audit_detail-item">
            <h3>Objective</h3>
            <p>{{ auditDetails.objective }}</p>
          </div>
          <div class="audit_detail-item">
            <h3>Business Unit</h3>
            <p>{{ auditDetails.business_unit }}</p>
          </div>
        </div>

        <!-- Framework, Policy, Subpolicy Section -->
        <div class="audit_hierarchy-details">
          <div class="audit_hierarchy-item">
            <h3>Framework</h3>
            <p>{{ auditDetails.framework_name }}</p>
          </div>
          <div class="audit_hierarchy-arrow">→</div>
          <div class="audit_hierarchy-item">
            <h3>Policy</h3>
            <p>{{ auditDetails.policy_name }}</p>
          </div>
          <div class="audit_hierarchy-arrow">→</div>
          <div class="audit_hierarchy-item">
            <h3>Subpolicy</h3>
            <p>{{ auditDetails.subpolicy_name }}</p>
          </div>
        </div>

        <!-- Compliance Tabs -->
        <div class="audit_compliance-section">
          <div class="audit_compliance-header-row">
            <h2>Compliance Items</h2>
            <!-- <button @click="showAddComplianceModal = true" class="audit_add-compliance-button">
              <span class="audit_add-icon">+</span> Add Compliance
            </button> -->
          </div>
          <div class="audit_compliance-tabs">
            <button 
              v-for="(compliance, index) in auditDetails.compliances" 
              :key="compliance.id"
              :class="['audit_tab-button', { active: selectedComplianceIndex === index }]"
              @click="selectCompliance(compliance, index)"
            >
              Compliance {{ index + 1 }}
            </button>
          </div>

          <!-- Selected Compliance Details -->
          <div v-if="selectedCompliance" class="audit_compliance-details">
            <div class="audit_compliance-header">
              <h3>{{ selectedCompliance.description }}</h3>
            </div>
            
            <!-- Row 1 -->
            <div class="audit_compliance-row">
              <div class="audit_form-group">
                <label>Compliance Status</label>
                <select v-model="selectedCompliance.status" @change="onFieldChange" class="audit_form-control" :disabled="isViewOnly">
                  <option value="2">Fully Compliant</option>
                  <option value="1">Partially Compliant</option>
                  <option value="0">Not Compliant</option>
                  <option value="3">Not Applicable</option>
                </select>
                <div v-if="getFieldError('status', selectedComplianceIndex)" class="audit_error-message">
                  {{ getFieldError('status', selectedComplianceIndex) }}
                </div>
              </div>
              <div class="audit_form-group">
                <label>Type of Findings</label>
                <select v-model="selectedCompliance.major_minor" @change="onFieldChange" class="audit_form-control" :disabled="isViewOnly">
                  <option value="">Select Type</option>
                  <option value="0">Minor</option>
                  <option value="1">Major</option>
                </select>
              </div>
              <div class="audit_form-group">
                <label>Severity Rating (1-10)</label>
                <input 
                  type="number" 
                  v-model="selectedCompliance.severity_rating"
                  @input="onFieldChange"
                  min="1"
                  max="10"
                  class="audit_form-control"
                  :disabled="isViewOnly"
                >
                <div v-if="getFieldError('severity_rating', selectedComplianceIndex)" class="audit_error-message">
                  {{ getFieldError('severity_rating', selectedComplianceIndex) }}
                </div>
              </div>
            </div>

            <!-- Row 2 -->
            <div class="audit_compliance-row">
              <div class="audit_form-group">
                <label>What to Verify</label>
                <textarea v-model="selectedCompliance.what_to_verify" @input="onFieldChange" class="audit_form-control" :disabled="isViewOnly"></textarea>
              </div>
              <div class="audit_form-group">
                <label>How to Verify</label>
                <textarea v-model="selectedCompliance.how_to_verify" @input="onFieldChange" class="audit_form-control" :disabled="isViewOnly"></textarea>
              </div>
              <div class="audit_form-group">
                <label>Impact</label>
                <textarea v-model="selectedCompliance.impact" @input="onFieldChange" class="audit_form-control" :disabled="isViewOnly"></textarea>
              </div>
            </div>

            <!-- Row 3 -->
            <div class="audit_compliance-row">
              <div class="audit_form-group">
                <label>Why to Verify</label>
                <textarea v-model="selectedCompliance.why_to_verify" @input="onFieldChange" class="audit_form-control" :disabled="isViewOnly"></textarea>
              </div>
              <div class="audit_form-group">
                <label>Details of Findings</label>
                <textarea v-model="selectedCompliance.details_of_finding" @input="onFieldChange" class="audit_form-control" :disabled="isViewOnly"></textarea>
              </div>
              <div class="audit_form-group">
                <label>Underlying Cause</label>
                <textarea v-model="selectedCompliance.underlying_cause" @input="onFieldChange" class="audit_form-control" :disabled="isViewOnly"></textarea>
              </div>
            </div>

            <!-- Row 4 -->
            <div class="audit_compliance-row">
              <div class="audit_form-group">
                <label>Predictive Risks</label>
                <select v-model="selectedCompliance.selected_risks" class="audit_form-control" multiple @change="updateCorrectiveActions" :disabled="isViewOnly">
                  <option v-for="risk in selectedCompliance.risks" 
                          :key="risk.id" 
                          :value="risk">
                    {{ risk.title }} ({{ risk.category }})
                  </option>
                </select>
              </div>
              <div class="audit_form-group">
                <label>Corrective Actions</label>
                <div v-if="selectedCompliance.selected_risks && selectedCompliance.selected_risks.length > 0"
                     class="audit_corrective-actions-container">
                  <div v-for="risk in selectedCompliance.selected_risks" 
                       :key="risk.id" 
                       class="audit_risk-mitigation">
                    <div class="audit_risk-header">
                      <strong>{{ risk.title }}</strong>
                    </div>
                    <div class="audit_mitigation-actions">
                      <label class="audit_mitigation-checkbox">
                        <input type="checkbox" 
                               v-model="selectedCompliance.selected_mitigations" 
                               :value="{ risk_id: risk.id, mitigation: risk.mitigation }"
                               @change="handleMitigationChange"
                               :disabled="isViewOnly">
                        <span class="audit_mitigation-text">{{ risk.mitigation }}</span>
                      </label>
                    </div>
                  </div>
                </div>
                <div v-else class="audit_no-actions">
                  Select risks to view corrective actions
                </div>
              </div>
            </div>

            <!-- Row 5 -->
            <div class="audit_compliance-row">
              <div class="audit_form-group">
                <label>Suggested Action Plan</label>
                <textarea v-model="selectedCompliance.suggested_action_plan" @input="onFieldChange" class="audit_form-control" :disabled="isViewOnly"></textarea>
              </div>
              <div class="audit_form-group small-input">
                <label>Responsible for Plan</label>
                <input type="text" v-model="selectedCompliance.responsible_for_plan" @input="onFieldChange" class="audit_form-control" :disabled="isViewOnly">
              </div>
              <div class="audit_form-group">
                <label>Mitigation Date</label>
                <input type="date" v-model="selectedCompliance.mitigation_date" @change="onFieldChange" class="audit_form-control" :disabled="isViewOnly">
              </div>
            </div>

            <!-- Row 6 -->
            <div class="audit_compliance-row">
              <div class="audit_form-group checkbox-group">
                <label>
                  <input type="checkbox" v-model="selectedCompliance.re_audit" @change="onFieldChange" :disabled="isViewOnly">
                  Re-audit Required
                </label>
              </div>
              <div class="audit_form-group" v-if="selectedCompliance.re_audit">
                <label>Re-audit Date</label>
                <input type="date" v-model="selectedCompliance.re_audit_date" @change="onFieldChange" class="audit_form-control" :disabled="isViewOnly">
              </div>
              <div class="audit_form-group">
                <label>Comments</label>
                <textarea v-model="selectedCompliance.comments" @input="onFieldChange" class="audit_form-control" :disabled="isViewOnly"></textarea>
              </div>
            </div>

            <!-- Review Row -->
            <div class="audit_compliance-row">
              <div class="audit_form-group">
                <label>Review Status</label>
                <select v-model="selectedCompliance.review_status" disabled class="audit_form-control disabled">
                  <option value="in_review">In Review</option>
                  <option value="accept">Accept</option>
                  <option value="reject">Reject</option>
                </select>
              </div>
              <div class="audit_form-group">
                <label>Review Comments</label>
                <textarea v-model="selectedCompliance.review_comments" disabled class="audit_form-control disabled" placeholder="Review comments will appear here..."></textarea>
              </div>
            </div>

            <!-- Evidence Upload Footer -->
            <div class="audit_evidence-footer">
              <div class="audit_form-group">
                <label>Compliance Evidence</label>
                <div class="audit_upload-container">
                  <input 
                    type="file" 
                    @change="handleComplianceFileUpload" 
                    ref="complianceFileInput"
                    multiple
                    style="display: none"
                  >
                  <button @click="$refs.complianceFileInput.click()" class="audit_upload-button" :disabled="isViewOnly">
                    Upload Compliance Evidence
                  </button>
                  <div v-if="selectedCompliance.evidence_files && selectedCompliance.evidence_files.length > 0" class="audit_uploaded-files">
                    <div v-for="(file, index) in selectedCompliance.evidence_files" :key="index" class="audit_file-item" :class="{ 'from-version': file.fromVersion }">
                      <span class="audit_file-name">{{ file.name }}</span>
                      <span v-if="file.fromVersion" class="audit_version-badge-small">From Version</span>
                      <a v-if="file.url" :href="file.url" target="_blank" class="audit_view-file-btn" title="View File"><i class="fas fa-eye"></i></a>
                      <button @click="removeComplianceFile(index)" class="audit_remove-file-btn" :disabled="isViewOnly">×</button>
                    </div>
                  </div>
                  <div v-if="complianceUploadProgress > 0 && complianceUploadProgress < 100" class="audit_upload-progress">
                    <div class="audit_progress-bar">
                      <div class="audit_progress-fill" :style="{ width: complianceUploadProgress + '%' }"></div>
                    </div>
                    <span>{{ complianceUploadProgress }}%</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Audit Evidence Section -->
            <div class="audit_evidence-section">
              <h3>Audit Evidence</h3>
              <div class="audit_upload-container">
                <input 
                  type="file" 
                  @change="handleAuditFileUpload" 
                  ref="auditFileInput"
                  multiple
                  style="display: none"
                >
                <button @click="$refs.auditFileInput.click()" class="audit_upload-button audit_audit-upload" :disabled="isViewOnly">
                  Upload Audit Evidence
                </button>
                <div v-if="auditEvidenceFiles && auditEvidenceFiles.length > 0" class="audit_uploaded-files">
                  <div v-for="(file, index) in auditEvidenceFiles" :key="index" class="audit_file-item" :class="{ 'from-version': file.fromVersion }">
                    <span class="audit_file-name">{{ file.name }}</span>
                    <span v-if="file.fromVersion" class="audit_version-badge-small">From Version</span>
                    <a v-if="file.url" :href="file.url" target="_blank" class="audit_view-file-btn" title="View File"><i class="fas fa-eye"></i></a>
                    <button @click="removeAuditFile(index)" class="audit_remove-file-btn" :disabled="isViewOnly">×</button>
                  </div>
                </div>
                <div v-if="auditUploadProgress > 0 && auditUploadProgress < 100" class="audit_upload-progress">
                  <div class="audit_progress-bar">
                    <div class="audit_progress-fill" :style="{ width: auditUploadProgress + '%' }"></div>
                  </div>
                  <span>{{ auditUploadProgress }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Overall Audit Comments Section -->
      <div class="audit_overall-comments-section">
        <h3>Overall Audit Comments</h3>
        <div class="audit_form-group">
          <textarea 
            v-model="overallAuditComments" 
            @input="onFieldChange"
            class="audit_form-control audit_overall-comments-textarea"
            placeholder="Enter overall comments about this audit..."
            rows="4"
            :disabled="isViewOnly"
          ></textarea>
        </div>
      </div>

      <!-- Overall Review Comments Section -->
      <div class="audit_overall-review-comments-section">
        <h3>Overall Review Comments</h3>
        <textarea
          v-model="overallReviewComments"
          :disabled="isAuditFrozen || isViewOnly"
          class="audit_form-control audit_overall-comments-textarea"
          placeholder="Enter overall review comments..."
          rows="4"
        ></textarea>
      </div>

      <!-- Version Information -->
      <div class="audit_version-info" v-if="currentVersion">
        <div class="audit_version-badge">
          <span class="audit_version-label">Current Version:</span>
          <span class="audit_version-number">{{ currentVersion }}</span>
          <span class="audit_version-type">{{ getVersionType(currentVersion) }}</span>
        </div>
        <div class="audit_last-saved" v-if="lastSavedTime">
          <span class="audit_saved-label">Last Saved:</span>
          <span class="audit_saved-time">{{ formatDateTime(lastSavedTime) }}</span>
        </div>
      </div>
      <div class="audit_version-info" v-else>
        <div class="audit_version-badge">
          <span class="audit_version-label">Status:</span>
          <span class="audit_version-number new-audit">New Audit</span>
          <span class="audit_version-type">No versions saved yet</span>
        </div>
      </div>

      <!-- Save Changes Button - only show when not in view-only mode -->
      <div v-if="!isViewOnly" class="audit_floating-save-container">
        <button @click="saveCompliance" class="audit_floating-save-button" :disabled="isSaving">
          <span class="audit_save-text">
            {{ isSaving ? 'Saving Version...' : 'Save Changes' }}
          </span>
        </button>
      </div>
    </div>

    <!-- Review Modal -->
    <div v-if="showReviewModal" class="audit_modal-overlay" @click="closeReviewModal">
      <div class="audit_modal-content" @click.stop>
        <div class="audit_modal-header">
          <h3>Update Audit Status</h3>
          <button @click="closeReviewModal" class="audit_close-button">×</button>
        </div>
        <div class="audit_modal-body">
          <div class="audit_success-message">
            <h4>Changes Saved Successfully</h4>
            <p>You have saved the following changes:</p>
          </div>
          <div class="audit_review-question">
            <h4>Do you want to send this audit for review?</h4>
            <p class="audit_review-note">
              <em>This will change the audit status from "Work In Progress" to "Under Review"</em>
            </p>
          </div>
        </div>
        <div class="audit_modal-footer">
          <button @click="keepEditing" class="audit_btn-secondary">No, Keep Editing</button>
          <button @click="sendForReview" class="audit_btn-primary" :disabled="isSendingForReview">
            {{ isSendingForReview ? 'Sending...' : 'Yes, Send for Review' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- Add Compliance Modal -->
    <div v-if="showAddComplianceModal" class="audit_modal-overlay" @click="closeAddComplianceModal">
      <div class="audit_modal-content audit_add-compliance-modal" @click.stop>
        <div class="audit_modal-header">
          <h3>Add New Compliance</h3>
          <button @click="closeAddComplianceModal" class="audit_close-button">×</button>
        </div>
        <div class="audit_modal-body">
          <form @submit.prevent="submitNewCompliance">
            <div class="audit_form-row">
              <div class="audit_form-group">
                <label>Identifier*</label>
                <input type="text" v-model="newCompliance.identifier" required class="audit_form-control">
                <div v-if="getFieldError('identifier')" class="audit_error-message">
                  {{ getFieldError('identifier') }}
                </div>
              </div>
              <div class="audit_form-group">
                <label>Compliance Title*</label>
                <input type="text" v-model="newCompliance.complianceTitle" required class="audit_form-control">
                <div v-if="getFieldError('complianceTitle')" class="audit_error-message">
                  {{ getFieldError('complianceTitle') }}
                </div>
              </div>
            </div>
            
            <div class="audit_form-group">
              <label>Compliance Description*</label>
              <textarea v-model="newCompliance.complianceItemDescription" required class="audit_form-control" rows="3"></textarea>
            </div>
            
            <div class="audit_form-row">
              <div class="audit_form-group">
                <label>Compliance Type*</label>
                <input type="text" v-model="newCompliance.complianceType" required class="audit_form-control">
              </div>
              <div class="audit_form-group">
                <label>Scope*</label>
                <input type="text" v-model="newCompliance.scope" required class="audit_form-control">
              </div>
            </div>
            
            <div class="audit_form-row">
              <div class="audit_form-group">
                <label>Objective*</label>
                <textarea v-model="newCompliance.objective" required class="audit_form-control" rows="2"></textarea>
              </div>
              <div class="audit_form-group">
                <label>Impact</label>
                <textarea v-model="newCompliance.impact" class="audit_form-control" rows="2"></textarea>
              </div>
            </div>
            
            <div class="audit_form-row">
              <div class="audit_form-group">
                <label>Is Risk?</label>
                <div class="audit_radio-group">
                  <label class="audit_radio-label">
                    <input type="radio" v-model="newCompliance.isRisk" :value="1"> Yes
                  </label>
                  <label class="audit_radio-label">
                    <input type="radio" v-model="newCompliance.isRisk" :value="0"> No
                  </label>
                </div>
              </div>
              <div class="audit_form-group">
                <label>Criticality</label>
                <select v-model="newCompliance.criticality" class="audit_form-control">
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
              <div class="audit_form-group">
                <label>Probability</label>
                <select v-model="newCompliance.probability" class="audit_form-control">
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>
            
            <div class="audit_form-row">
              <div class="audit_form-group">
                <label>Possible Damage</label>
                <textarea v-model="newCompliance.possibleDamage" class="audit_form-control" rows="2"></textarea>
              </div>
              <div class="audit_form-group">
                <label>Mitigation</label>
                <textarea v-model="newCompliance.mitigation" class="audit_form-control" rows="2"></textarea>
              </div>
            </div>
            
            <div class="audit_form-note">
              <p><strong>Note:</strong> Fields marked with * are required</p>
              <p>This compliance will be added as "Temporary" and associated with the current audit.</p>
            </div>
          </form>
        </div>
        <div class="audit_modal-footer">
          <button @click="closeAddComplianceModal" class="audit_btn-secondary">Cancel</button>
          <button @click="submitNewCompliance" class="audit_btn-primary" :disabled="isAddingCompliance">
            {{ isAddingCompliance ? 'Adding...' : 'Add Compliance' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '../../data/api';
import ValidationMixin from '@/mixins/ValidationMixin';
import { AccessUtils } from '@/utils/accessUtils';
import { API_ENDPOINTS } from '../../config/api.js';

export default {
  name: 'TaskView',
  mixins: [ValidationMixin],
  data() {
    return {
      auditDetails: null,
      error: null,
      loading: true,
      selectedComplianceIndex: null,
      auditEvidenceFiles: [],
      complianceUploadProgress: 0,
      auditUploadProgress: 0,
      currentVersion: null,
      lastSavedTime: null,
      isSaving: false,

      hasUnsavedChanges: false,
      overallAuditComments: '',
      showReviewModal: false,
      isSendingForReview: false,
      savedVersionData: null,
      showAddComplianceModal: false,
      isAddingCompliance: false,
      newCompliance: {
        identifier: '',
        complianceTitle: '',
        complianceItemDescription: '',
        complianceType: '',
        scope: '',
        objective: '',
        impact: '',
        isRisk: 0,
        possibleDamage: '',
        mitigation: '',
        criticality: 'medium',
        probability: 'medium'
      },
      isAuditFrozen: false,
      overallReviewComments: '',
      validationErrors: {},
      fieldErrors: {},
      isReadOnlyMode: false
    }
  },
  computed: {
    selectedCompliance() {
      if (!this.auditDetails?.compliances) return null;
      return this.auditDetails.compliances[this.selectedComplianceIndex];
    },
    isViewOnly() {
      return this.isReadOnlyMode;
    }
  },
  watch: {
    // Watch for changes in audit details
    auditDetails: {
      handler(newVal, oldVal) {
        if (oldVal && newVal) {
          this.hasUnsavedChanges = true;
        }
      },
      deep: true
    },
    
    // Watch for changes in audit evidence files
    auditEvidenceFiles: {
      handler() {
        this.hasUnsavedChanges = true;
      },
      deep: true
    }
  },
  methods: {
    formatDateTime(dateTime) {
      if (!dateTime) return '';
      return new Date(dateTime).toLocaleString();
    },

    getVersionType(version) {
      if (!version) return '';
      if (version.startsWith('A')) return 'Auditor Version';
      if (version.startsWith('R')) return 'Reviewer Version';
      return 'Unknown Version';
    },

    extractFilenameFromUrl(url) {
      if (!url) return null;
      try {
        // Extract filename from S3 URL or any URL
        const urlParts = url.split('/');
        const filename = urlParts[urlParts.length - 1];
        // Decode URL encoding if present
        return decodeURIComponent(filename);
      } catch (error) {
        console.warn('Error extracting filename from URL:', url, error);
        return null;
      }
    },

    async handleComplianceFileUpload(event) {
      const files = Array.from(event.target.files);
      if (files.length === 0) return;

      this.complianceUploadProgress = 0;
      this.onFieldChange();

      const uploadedUrls = [];

      try {
        for (let i = 0; i < files.length; i++) {
          const file = files[i];
          const formData = new FormData();
          formData.append('file', file);
          formData.append('userId', 'current-user'); // Replace with actual user ID
          formData.append('documentType', 'evidence');
          formData.append('compliance_id', this.selectedCompliance.id);
          formData.append('audit_id', this.$route.params.auditId);
          formData.append('fileName', file.name);

          // Use S3 upload endpoint with JWT token
          const token = localStorage.getItem('access_token');
          const headers = {};
          if (token) {
            headers['Authorization'] = `Bearer ${token}`;
          }
          
          const response = await fetch(API_ENDPOINTS.UPLOAD_EVIDENCE_S3, {
            method: 'POST',
            body: formData,
            credentials: 'include',
            headers: headers
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Upload failed');
          }

          const responseData = await response.json();
          
          if (responseData.success) {
            uploadedUrls.push(responseData.file.url);
            this.selectedCompliance.evidence_files.push({
              name: file.name,
              url: responseData.file.url,
              uploadedAt: new Date().toISOString(),
              fromVersion: false
            });
          }
          
          // Update progress
          this.complianceUploadProgress = Math.round(((i + 1) * 100) / files.length);
        }

        // Get existing evidence URLs
        const existingUrls = this.selectedCompliance.evidence ? 
          this.selectedCompliance.evidence.split(',').filter(url => url.trim()) : 
          [];
        
        // Combine existing and new URLs (avoiding duplicates)
        const allUrls = [...existingUrls];
        uploadedUrls.forEach(url => {
          if (!allUrls.includes(url)) {
            allUrls.push(url);
          }
        });
        
        // Update evidence URLs as comma-separated string
        this.selectedCompliance.evidence_urls = allUrls.join(',');
        this.selectedCompliance.evidence = this.selectedCompliance.evidence_urls;
        
        console.log('Updated evidence URLs:', this.selectedCompliance.evidence);
        
        this.complianceUploadProgress = 100;
        this.hasUnsavedChanges = true;
        
        // Clear progress after 2 seconds
        setTimeout(() => {
          this.complianceUploadProgress = 0;
        }, 2000);

        this.$toast?.success(`${files.length} compliance evidence file(s) uploaded successfully`);
        await this.sendPushNotification({
          title: 'Compliance Evidence Uploaded',
          message: `${files.length} compliance evidence file(s) uploaded for compliance: ${this.selectedCompliance.description}`,
          category: 'compliance',
          priority: 'medium',
          user_id: 'current-user'
        });
      } catch (error) {
        console.error('Error uploading compliance files:', error);
        // Handle access denied errors
        if (AccessUtils.handleApiError(error, 'compliance file upload')) {
          this.complianceUploadProgress = 0;
          return;
        }
        this.$toast?.error('Failed to upload compliance evidence files');
        this.complianceUploadProgress = 0;
        await this.sendPushNotification({
          title: 'Compliance Evidence Upload Failed',
          message: `Failed to upload compliance evidence file(s) for compliance: ${this.selectedCompliance?.description || ''}`,
          category: 'compliance',
          priority: 'high',
          user_id: 'current-user'
        });
      }

      // Clear the input
      event.target.value = '';
    },

    async handleAuditFileUpload(event) {
      const files = Array.from(event.target.files);
      if (files.length === 0) return;

      this.auditUploadProgress = 0;
      this.onFieldChange();

      const uploadedUrls = [];

      try {
        for (let i = 0; i < files.length; i++) {
          const file = files[i];
          const formData = new FormData();
          formData.append('file', file);
          formData.append('userId', 'current-user'); // Replace with actual user ID
          formData.append('documentType', 'audit_evidence');
          formData.append('audit_id', this.$route.params.auditId);
          formData.append('fileName', file.name);

          // Use S3 upload endpoint with JWT token
          const token = localStorage.getItem('access_token');
          const headers = {};
          if (token) {
            headers['Authorization'] = `Bearer ${token}`;
          }
          
          const response = await fetch(API_ENDPOINTS.UPLOAD_EVIDENCE_S3, {
            method: 'POST',
            body: formData,
            credentials: 'include',
            headers: headers
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Upload failed');
          }

          const responseData = await response.json();
          
          if (responseData.success) {
            uploadedUrls.push(responseData.file.url);
            this.auditEvidenceFiles.push({
              name: file.name,
              url: responseData.file.url,
              uploadedAt: new Date().toISOString(),
              fromVersion: false
            });
          }
          
          // Update progress
          this.auditUploadProgress = Math.round(((i + 1) * 100) / files.length);
        }

        // Get existing evidence URLs
        const existingUrls = this.auditDetails.evidence_urls ? 
          this.auditDetails.evidence_urls.split(',').filter(url => url.trim()) : 
          [];
        
        // Combine existing and new URLs (avoiding duplicates)
        const allUrls = [...existingUrls];
        uploadedUrls.forEach(url => {
          if (!allUrls.includes(url)) {
            allUrls.push(url);
          }
        });
        
        // Store audit evidence URLs
        this.auditDetails.evidence_urls = allUrls.join(',');
        
        console.log('Updated audit evidence URLs:', this.auditDetails.evidence_urls);
        
        this.auditUploadProgress = 100;
        this.hasUnsavedChanges = true;
        
        // Clear progress after 2 seconds
        setTimeout(() => {
          this.auditUploadProgress = 0;
        }, 2000);

        this.$toast?.success(`${files.length} audit evidence file(s) uploaded successfully`);
        await this.sendPushNotification({
          title: 'Audit Evidence Uploaded',
          message: `${files.length} audit evidence file(s) uploaded for audit: ${this.auditDetails?.title || ''}`,
          category: 'audit',
          priority: 'medium',
          user_id: 'current-user'
        });
      } catch (error) {
        console.error('Error uploading audit files:', error);
        this.$toast?.error('Failed to upload audit evidence files');
        this.auditUploadProgress = 0;
        await this.sendPushNotification({
          title: 'Audit Evidence Upload Failed',
          message: `Failed to upload audit evidence file(s) for audit: ${this.auditDetails?.title || ''}`,
          category: 'audit',
          priority: 'high',
          user_id: 'current-user'
        });
      }

      // Clear the input
      event.target.value = '';
    },

    removeComplianceFile(index) {
      // Get the URL of the file to remove
      const fileToRemove = this.selectedCompliance.evidence_files[index];
      
      // Remove the file from the files array
      this.selectedCompliance.evidence_files.splice(index, 1);
      
      // Update the evidence URLs string by removing this URL
      if (fileToRemove && fileToRemove.url) {
        const urls = this.selectedCompliance.evidence.split(',').filter(url => url.trim());
        const updatedUrls = urls.filter(url => url !== fileToRemove.url);
        this.selectedCompliance.evidence = updatedUrls.join(',');
        this.selectedCompliance.evidence_urls = this.selectedCompliance.evidence;
        console.log('Updated evidence URLs after removal:', this.selectedCompliance.evidence);
      }
      
      this.onFieldChange();
    },

    removeAuditFile(index) {
      // Get the URL of the file to remove
      const fileToRemove = this.auditEvidenceFiles[index];
      
      // Remove the file from the files array
      this.auditEvidenceFiles.splice(index, 1);
      
      // Update the evidence URLs string by removing this URL
      if (fileToRemove && fileToRemove.url) {
        const urls = this.auditDetails.evidence_urls.split(',').filter(url => url.trim());
        const updatedUrls = urls.filter(url => url !== fileToRemove.url);
        this.auditDetails.evidence_urls = updatedUrls.join(',');
        console.log('Updated audit evidence URLs after removal:', this.auditDetails.evidence_urls);
      }
      
      this.onFieldChange();
    },

    async fetchAuditDetails() {
      this.loading = true;
      this.error = null;
      try {
        this.error = null;
        const auditId = this.$route.params.auditId;
        if (!auditId) {
          this.error = 'No audit ID provided';
          return;
        }
        console.log('Fetching details for audit:', auditId);
        const taskResponse = await api.getAuditTaskDetails(auditId);
        this.auditDetails = taskResponse.data;
        
        // Initialize selected_risks and selected_mitigations for each compliance
        this.auditDetails.compliances.forEach(compliance => {
          compliance.selected_risks = compliance.selected_risks || [];
          compliance.selected_mitigations = compliance.selected_mitigations || [];
          compliance.risks = compliance.risks || [];
          compliance.evidence_files = [];
          compliance.evidence_urls = compliance.evidence || '';
          
          // Parse existing evidence URLs if they exist
          if (compliance.evidence) {
            const urls = compliance.evidence.split(',').filter(url => url.trim());
            compliance.evidence_files = urls.map((url, index) => {
              const filename = this.extractFilenameFromUrl(url) || `Evidence ${index + 1}`;
              return {
                name: filename,
                url: url.trim(),
                uploadedAt: null,
                fromVersion: this.auditDetails.loaded_from_version || false
              };
            });
          }
        });

        // Initialize audit evidence files from version data or audit details
        this.auditEvidenceFiles = [];
        if (this.auditDetails.evidence_urls) {
          const urls = this.auditDetails.evidence_urls.split(',').filter(url => url.trim());
          this.auditEvidenceFiles = urls.map((url, index) => {
            // Extract filename from URL or use default name
            const filename = this.extractFilenameFromUrl(url) || `Audit Evidence ${index + 1}`;
            return {
              name: filename,
              url: url.trim(),
              uploadedAt: null,
              fromVersion: this.auditDetails.loaded_from_version || false
            };
          });
        }

        // Set version information if available
        if (this.auditDetails.current_version) {
          this.currentVersion = this.auditDetails.current_version;
          this.lastSavedTime = this.auditDetails.version_date;
          console.log(`Loaded version: ${this.currentVersion} from ${this.lastSavedTime}`);
          
          // Show notification that data was loaded from a version
          if (this.auditDetails.loaded_from_version) {
            this.$toast?.info(`Loaded data from ${this.getVersionType(this.currentVersion)} ${this.currentVersion}`);
          } else if (this.currentVersion === 'A1') {
            // Show notification that initial version was created
            this.$toast?.success(`Initial version ${this.currentVersion} created successfully`);
          }
        }

        // Load overall audit comments if available
        this.overallAuditComments = this.auditDetails.overall_audit_comments || '';
        
        // Load overall review comments if available (read-only for auditor)
        this.overallReviewComments = this.auditDetails.overall_review_comments || '';

        // Set hasUnsavedChanges to true so save button is active
        this.hasUnsavedChanges = true;
        
        // If we have compliances, select the first one by default (if none is selected)
        if (this.auditDetails.compliances && this.auditDetails.compliances.length > 0 && this.selectedComplianceIndex === null) {
          this.selectCompliance(this.auditDetails.compliances[0], 0);
        }
        
        console.log(`Loaded ${this.auditDetails.compliances ? this.auditDetails.compliances.length : 0} compliances`);
      } catch (error) {
        console.error('Error fetching audit details:', error);
        // Handle access denied errors
        if (AccessUtils.handleApiError(error, 'audit task details access')) {
          this.error = 'Access denied';
        } else {
          this.error = error.response?.data?.error || 'Failed to load audit details';
        }
      } finally {
        this.loading = false;
      }
    },

    retryFetch() {
      this.fetchAuditDetails();
    },

    getStatusClass(status) {
      switch(status) {
        case '2': return 'status-completed';
        case '1': return 'status-progress';
        case '0': return 'status-pending';
        default: return 'status-pending';
      }
    },

    getStatusText(status) {
      switch(status) {
        case '2': return 'Completed';
        case '1': return 'In Progress';
        case '0': return 'Not Started';
        default: return 'Not Started';
      }
    },

    updateCorrectiveActions() {
      // Clear previously selected mitigations when risks change
      this.selectedCompliance.selected_mitigations = [];
      this.hasUnsavedChanges = true;
      this.onFieldChange();
    },

    handleMitigationChange() {
      this.hasUnsavedChanges = true;
    },

    // Method to handle any form field change with validation
    onFieldChange() {
      this.hasUnsavedChanges = true;
      
      // Validate the current compliance field if we have a selected compliance
      if (this.selectedCompliance && this.selectedComplianceIndex !== null) {
        // Clear previous errors for this compliance
        if (this.fieldErrors[this.selectedComplianceIndex]) {
          this.fieldErrors[this.selectedComplianceIndex] = {};
        }
        
        // Re-validate current compliance
        this.validateComplianceField('status', this.selectedCompliance.status, this.selectedComplianceIndex);
        this.validateComplianceField('severity_rating', this.selectedCompliance.severity_rating, this.selectedComplianceIndex);
        this.validateComplianceField('major_minor', this.selectedCompliance.major_minor, this.selectedComplianceIndex);
      }
    },

    async saveCompliance() {
      console.log('Save button clicked!');
      console.log('isSaving state:', this.isSaving);
      if (this.isSaving) return;
      
            // Re-enable validation but make it less strict
      const isValid = this.validateAuditData();
      console.log('Validation result:', isValid);
      console.log('Field errors:', this.fieldErrors);
      console.log('Validation errors:', this.validationErrors);
      
      if (!isValid) {
        console.log('Validation failed - showing specific errors');
        // Show specific errors instead of generic message
        let errorMsg = 'Validation errors found:';
        if (Object.keys(this.validationErrors).length > 0) {
          errorMsg += ' ' + Object.values(this.validationErrors).join(', ');
        }
        for (const index in this.fieldErrors) {
          if (Object.keys(this.fieldErrors[index]).length > 0) {
            errorMsg += ` Compliance ${parseInt(index) + 1}: ` + Object.values(this.fieldErrors[index]).join(', ');
          }
        }
        this.$toast?.error(errorMsg);
        await this.sendPushNotification({
          title: 'Audit Save Validation Error',
          message: errorMsg,
          category: 'audit',
          priority: 'high',
          user_id: 'current-user'
        });
        return;
      }
      
      console.log('Starting save operation...');
      
      try {
        this.isSaving = true;
        
        // Helper function to format dates consistently
        const formatDateForBackend = (dateValue) => {
          if (!dateValue) return '';
          
          // If it's already in YYYY-MM-DD format, return as is
          if (/^\d{4}-\d{2}-\d{2}$/.test(dateValue)) {
            return dateValue;
          }
          
          // Try to parse and convert to YYYY-MM-DD
          try {
            const date = new Date(dateValue);
            if (!isNaN(date.getTime())) {
              return date.toISOString().split('T')[0]; // YYYY-MM-DD format
            }
          } catch (e) {
            console.warn('Could not parse date:', dateValue);
          }
          
          return dateValue; // Return original if can't parse
        };

        // Collect all compliance data
        const compliancesData = {};
        console.log('Processing compliances:', this.auditDetails.compliances.length);
        this.auditDetails.compliances.forEach(compliance => {
          console.log('Processing compliance:', compliance.id, 'mitigation_date:', compliance.mitigation_date);
          compliancesData[compliance.id] = {
            description: compliance.description,
            status: compliance.status,
            evidence: compliance.evidence || '',
            comments: compliance.comments || '',
            how_to_verify: compliance.how_to_verify || '',
            impact: compliance.impact || '',
            recommendation: compliance.recommendation || '',
            details_of_finding: compliance.details_of_finding || '',
            major_minor: compliance.major_minor || '',
            severity_rating: compliance.severity_rating || '',
            why_to_verify: compliance.why_to_verify || '',
            what_to_verify: compliance.what_to_verify || '',
            underlying_cause: compliance.underlying_cause || '',
            suggested_action_plan: compliance.suggested_action_plan || '',
            responsible_for_plan: compliance.responsible_for_plan || '',
            mitigation_date: formatDateForBackend(compliance.mitigation_date),
            re_audit: compliance.re_audit || false,
            re_audit_date: formatDateForBackend(compliance.re_audit_date),
            selected_risks: compliance.selected_risks || [],
            selected_mitigations: compliance.selected_mitigations || [],
            review_status: compliance.review_status || 'in_review',
            review_comments: compliance.review_comments || ''
          };
          console.log('Formatted mitigation_date for compliance', compliance.id, ':', compliancesData[compliance.id].mitigation_date);
        });

        // Collect audit evidence URLs from uploaded files
        const auditEvidenceUrls = this.auditEvidenceFiles.map(file => file.url).join(',');
        console.log('Audit evidence URLs being saved:', auditEvidenceUrls);
        
        const payload = {
          user_id: 1050, // Default auditor ID - should be replaced with actual logged-in user ID
          compliances: compliancesData,
          audit_evidence_urls: auditEvidenceUrls || this.auditDetails.evidence_urls || '',
          audit_title: this.auditDetails.title || '',
          audit_scope: this.auditDetails.scope || '',
          audit_objective: this.auditDetails.objective || '',
          business_unit: this.auditDetails.business_unit || '',
          overall_comments: this.overallAuditComments || '' // This is for audit comments only, review comments are stored separately
        };
        
        console.log('Payload to be sent:', JSON.stringify(payload, null, 2));
        const auditId = this.$route.params.auditId;
        console.log('Calling api.saveVersion with auditId:', auditId);

        // Call the new versioning endpoint
        const saveResponse = await api.saveVersion(auditId, payload);
        console.log('Save response received:', saveResponse);
        
        if (saveResponse.data.success) {
          // Store the saved version data
          this.savedVersionData = {
            version: saveResponse.data.version,
            data: saveResponse.data.data
          };
          
          this.hasUnsavedChanges = false;
          this.currentVersion = saveResponse.data.version;
          this.lastSavedTime = new Date().toISOString();
          
          // Clear validation errors on successful save
          this.validationErrors = {};
          this.fieldErrors = {};
          
          // Show version information to user
          console.log('Saved version:', saveResponse.data.version);
          console.log('Version data:', saveResponse.data.data);
          
          // Show the review modal
          this.showReviewModal = true;
          this.$toast?.success(`Audit version ${this.currentVersion} saved successfully`);
          await this.sendPushNotification({
            title: 'Audit Version Saved',
            message: `Audit version ${this.currentVersion} saved successfully for audit: ${this.auditDetails?.title || ''}`,
            category: 'audit',
            priority: 'medium',
            user_id: 'current-user'
          });
        } else {
          throw new Error('Failed to save audit version');
        }
      } catch (error) {
        console.error('Error saving audit version:', error);
        
        // Handle validation errors from backend
        if (error.response?.status === 400 && error.response?.data?.error) {
          if (error.response.data.error.includes('Validation error')) {
            this.$toast?.error('Validation error: ' + error.response.data.error);
            await this.sendPushNotification({
              title: 'Audit Save Validation Error',
              message: 'Validation error: ' + error.response.data.error,
              category: 'audit',
              priority: 'high',
              user_id: 'current-user'
            });
          } else {
            this.$toast?.error(error.response.data.error);
            await this.sendPushNotification({
              title: 'Audit Save Error',
              message: error.response.data.error,
              category: 'audit',
              priority: 'high',
              user_id: 'current-user'
            });
          }
        } else {
        this.$toast?.error('Failed to save audit version: ' + (error.response?.data?.error || error.message));
        await this.sendPushNotification({
          title: 'Audit Save Error',
          message: 'Failed to save audit version: ' + (error.response?.data?.error || error.message),
          category: 'audit',
          priority: 'high',
          user_id: 'current-user'
        });
        }
      } finally {
        this.isSaving = false;
      }
    },

    selectCompliance(compliance, index) {
      console.log('Selecting compliance:', compliance.id, 'at index:', index);
      this.selectedComplianceIndex = index;
      this.onFieldChange(); // Ensure save button is active when switching tabs
      console.log('Selected compliance is now:', this.selectedCompliance?.id);
    },

    closeReviewModal() {
      this.showReviewModal = false;
      this.savedVersionData = null;
    },

    keepEditing() {
      this.closeReviewModal();
      this.$toast?.success(`Audit version ${this.currentVersion} saved successfully`);
    },

    async sendForReview() {
      if (this.isSendingForReview) return;
      
      try {
        this.isSendingForReview = true;
        const auditId = this.$route.params.auditId;
        
        // Call backend to update audit status to "Under Review"
        const reviewResponse = await api.sendForReview(auditId, {
          version: this.currentVersion
        });
        
        if (reviewResponse.data.success) {
          this.closeReviewModal();
          this.$toast?.success('Audit sent for review successfully');
          await this.sendPushNotification({
            title: 'Audit Sent for Review',
            message: `Audit "${this.auditDetails?.title || ''}" sent for review (version: ${this.currentVersion})`,
            category: 'audit',
            priority: 'high',
            user_id: 'current-user'
          });
          
          // Optionally redirect to audits list or show different UI
          // this.$router.push('/audits');
        } else {
          throw new Error('Failed to send audit for review');
        }
      } catch (error) {
        console.error('Error sending audit for review:', error);
        // Handle access denied errors
        if (AccessUtils.handleApiError(error, 'audit review submission')) {
          return;
        }
        this.$toast?.error('Failed to send audit for review: ' + (error.response?.data?.error || error.message));
        await this.sendPushNotification({
          title: 'Audit Review Send Failed',
          message: 'Failed to send audit for review: ' + (error.response?.data?.error || error.message),
          category: 'audit',
          priority: 'high',
          user_id: 'current-user'
        });
      } finally {
        this.isSendingForReview = false;
      }
    },
    
    closeAddComplianceModal() {
      this.showAddComplianceModal = false;
      // Reset form fields
      this.newCompliance = {
        identifier: '',
        complianceTitle: '',
        complianceItemDescription: '',
        complianceType: '',
        scope: '',
        objective: '',
        impact: '',
        isRisk: 0,
        possibleDamage: '',
        mitigation: '',
        criticality: 'medium',
        probability: 'medium'
      };
    },
    
    async submitNewCompliance() {
      if (this.isAddingCompliance) return;
      
      // Validate before submission
      if (!this.validateNewComplianceForm()) {
        this.$toast?.error('Please fix validation errors before submitting');
        await this.sendPushNotification({
          title: 'Compliance Add Validation Error',
          message: 'Please fix validation errors before submitting',
          category: 'compliance',
          priority: 'high',
          user_id: 'current-user'
        });
        return;
      }
      
      try {
        this.isAddingCompliance = true;
        const auditId = this.$route.params.auditId;
        
        // Prepare data for API - ensure all fields are properly formatted
        const complianceData = {
          identifier: this.newCompliance.identifier,
          complianceTitle: this.newCompliance.complianceTitle,
          complianceItemDescription: this.newCompliance.complianceItemDescription,
          complianceType: this.newCompliance.complianceType,
          scope: this.newCompliance.scope,
          objective: this.newCompliance.objective,
          impact: this.newCompliance.impact || '',
          isRisk: Number(this.newCompliance.isRisk || 0),
          possibleDamage: this.newCompliance.possibleDamage || '',
          mitigation: this.newCompliance.mitigation || '',
          criticality: this.newCompliance.criticality || 'medium',
          probability: this.newCompliance.probability || 'medium',
          permanentTemporary: 'Temporary',
          createdByName: '1050', // Default user ID or get from session
          createdByDate: new Date().toISOString().split('T')[0] // Current date in YYYY-MM-DD format
        };
        
        console.log('Submitting compliance data:', complianceData);
        
        // Call backend API to add compliance
        const response = await api.addComplianceToAudit(auditId, complianceData);
        
        if (response.data.success) {
          this.$toast?.success('Compliance added successfully');
          this.closeAddComplianceModal();
          
          // Instead of manually adding the compliance to the local list,
          // refresh the entire audit details to get the most up-to-date data
          console.log('Refreshing audit details with the latest data including the new compliance');
          await this.fetchAuditDetails();
          
          // If we have compliances after refresh, select the newly added one (should be the last one)
          if (this.auditDetails && this.auditDetails.compliances && this.auditDetails.compliances.length > 0) {
            // Select the last compliance (which should be the newly added one)
            const lastIndex = this.auditDetails.compliances.length - 1;
            this.selectCompliance(this.auditDetails.compliances[lastIndex], lastIndex);
            
            // Show notification about the new version if available
            if (this.currentVersion) {
              this.$toast?.info(`Updated to version ${this.currentVersion} with the added compliance`);
              await this.sendPushNotification({
                title: 'Audit Version Updated',
                message: `Updated to version ${this.currentVersion} with the added compliance`,
                category: 'audit',
                priority: 'medium',
                user_id: 'current-user'
              });
            }
          }
          await this.sendPushNotification({
            title: 'Compliance Added',
            message: `Compliance "${this.newCompliance.complianceTitle}" added to audit: ${this.auditDetails?.title || ''}`,
            category: 'compliance',
            priority: 'medium',
            user_id: 'current-user'
          });
        } else {
          throw new Error(response.data.error || 'Failed to add compliance');
        }
      } catch (error) {
        console.error('Error adding compliance:', error);
        
        // Handle access denied errors
        if (AccessUtils.handleApiError(error, 'compliance addition')) {
          return;
        }
        
        // Extract detailed error information
        let errorMessage = 'Failed to add compliance';
        
        if (error.response?.status === 400 && error.response?.data?.error) {
          if (error.response.data.error.includes('Validation error')) {
            errorMessage = 'Validation error: ' + error.response.data.error;
          } else {
            errorMessage = error.response.data.error;
          }
        } else if (error.response?.data?.error) {
          errorMessage += ': ' + error.response.data.error;
          console.error('Server error details:', error.response.data);
        } else if (error.message) {
          errorMessage += ': ' + error.message;
        }
        
        this.$toast?.error(errorMessage);
        await this.sendPushNotification({
          title: 'Compliance Add Error',
          message: errorMessage,
          category: 'compliance',
          priority: 'high',
          user_id: 'current-user'
        });
      } finally {
        this.isAddingCompliance = false;
      }
    },

    validateComplianceField(field, value, complianceIndex = null) {
      const errors = {};
      
      switch (field) {
        case 'status': {
          const statusError = this.validateComplianceStatus(value);
          if (statusError) errors.status = statusError;
          break;
        }
          
        case 'severity_rating':
          if (value !== null && value !== '') {
            const rating = parseInt(value);
            if (isNaN(rating) || rating < 1 || rating > 10) {
              errors.severity_rating = 'Severity rating must be between 1 and 10';
            }
          }
          break;
          
        case 'major_minor':
          if (value && !['0', '1'].includes(value)) {
            errors.major_minor = 'Invalid finding type';
          }
          break;
          
        case 'comments':
        case 'how_to_verify':
        case 'impact':
        case 'details_of_finding':
        case 'underlying_cause':
        case 'suggested_action_plan':
        case 'why_to_verify':
        case 'what_to_verify': {
          const stringError = this.validateString(value, {
            required: false,
            minLength: 0,
            maxLength: field === 'comments' || field === 'details_of_finding' || field === 'suggested_action_plan' ? 2000 : 1000,
            fieldName: field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
          });
          if (stringError) errors[field] = stringError;
          break;
        }
          
        case 'responsible_for_plan': {
          const planError = this.validateString(value, {
            required: false,
            minLength: 0,
            maxLength: 200,
            fieldName: 'Responsible for Plan'
          });
          if (planError) errors[field] = planError;
          break;
        }
          
        case 'mitigation_date':
        case 're_audit_date': {
          if (value) {
            const dateError = this.validateDate(value, field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()));
            if (dateError) errors[field] = dateError;
          }
          break;
        }
      }
      
      if (complianceIndex !== null) {
        if (!this.fieldErrors[complianceIndex]) {
          this.fieldErrors[complianceIndex] = {};
        }
        if (Object.keys(errors).length > 0) {
          this.fieldErrors[complianceIndex] = { ...this.fieldErrors[complianceIndex], ...errors };
        } else {
          delete this.fieldErrors[complianceIndex][field];
        }
      }
      
      return Object.keys(errors).length === 0;
    },

    validateComplianceStatus(value) {
      const validStatuses = ['0', '1', '2', '3']; // Not Compliant, Partially Compliant, Fully Compliant, Not Applicable
      if (!validStatuses.includes(value)) {
        return 'Invalid compliance status';
      }
      return null;
    },

    validateNewComplianceForm() {
      const errors = {};
      
      // Required fields
      const requiredFields = ['identifier', 'complianceTitle', 'complianceItemDescription', 'complianceType', 'scope', 'objective'];
      
      requiredFields.forEach(field => {
        const value = this.newCompliance[field];
        if (!value || value.trim() === '') {
          errors[field] = `${field.replace(/([A-Z])/g, ' $1').toLowerCase()} is required`;
        }
      });
      
      // Validate string lengths
      const identifierError = this.validateString(this.newCompliance.identifier, {
        fieldName: 'Identifier',
        minLength: 1,
        maxLength: 100
      });
      if (identifierError) errors.identifier = identifierError;
      
      const titleError = this.validateString(this.newCompliance.complianceTitle, {
        fieldName: 'Compliance Title',
        minLength: 1,
        maxLength: 200
      });
      if (titleError) errors.complianceTitle = titleError;
      
      const descError = this.validateString(this.newCompliance.complianceItemDescription, {
        fieldName: 'Compliance Description',
        minLength: 1,
        maxLength: 2000
      });
      if (descError) errors.complianceItemDescription = descError;
      
      const typeError = this.validateString(this.newCompliance.complianceType, {
        fieldName: 'Compliance Type',
        minLength: 1,
        maxLength: 100
      });
      if (typeError) errors.complianceType = typeError;
      
      const scopeError = this.validateString(this.newCompliance.scope, {
        fieldName: 'Scope',
        minLength: 1,
        maxLength: 500
      });
      if (scopeError) errors.scope = scopeError;
      
      const objectiveError = this.validateString(this.newCompliance.objective, {
        fieldName: 'Objective',
        minLength: 1,
        maxLength: 1000
      });
      if (objectiveError) errors.objective = objectiveError;
      
      // Validate optional fields if provided
      if (this.newCompliance.impact) {
        const impactError = this.validateString(this.newCompliance.impact, {
          fieldName: 'Impact',
          required: false,
          maxLength: 1000
        });
        if (impactError) errors.impact = impactError;
      }
      
      if (this.newCompliance.possibleDamage) {
        const damageError = this.validateString(this.newCompliance.possibleDamage, {
          fieldName: 'Possible Damage',
          required: false,
          maxLength: 1000
        });
        if (damageError) errors.possibleDamage = damageError;
      }
      
      if (this.newCompliance.mitigation) {
        const mitigationError = this.validateString(this.newCompliance.mitigation, {
          fieldName: 'Mitigation',
          required: false,
          maxLength: 1000
        });
        if (mitigationError) errors.mitigation = mitigationError;
      }
      
      // Validate criticality and probability
      const validLevels = ['high', 'medium', 'low'];
      if (!validLevels.includes(this.newCompliance.criticality)) {
        errors.criticality = 'Criticality must be high, medium, or low';
      }
      
      if (!validLevels.includes(this.newCompliance.probability)) {
        errors.probability = 'Probability must be high, medium, or low';
      }
      
      // Validate isRisk
      if (this.newCompliance.isRisk !== 0 && this.newCompliance.isRisk !== 1) {
        errors.isRisk = 'Is Risk must be yes or no';
      }
      
      this.validationErrors = errors;
      return Object.keys(errors).length === 0;
    },

    validateAuditData() {
      const errors = {};
      
      // Validate overall audit comments
      if (this.overallAuditComments) {
        const commentsError = this.validateString(this.overallAuditComments, {
          fieldName: 'Overall Audit Comments',
          required: false,
          maxLength: 5000
        });
        if (commentsError) errors.overallAuditComments = commentsError;
      }
      
      // Validate audit evidence files
      if (this.auditEvidenceFiles && this.auditEvidenceFiles.length > 20) {
        errors.auditEvidenceFiles = 'Too many audit evidence files (maximum 20)';
      }
      
      // Reset field errors before validation
      this.fieldErrors = {};
      
      // Validate compliance data - only check for critical errors
      if (this.auditDetails && this.auditDetails.compliances) {
        this.auditDetails.compliances.forEach((compliance, index) => {
          // Only validate fields that have values and could cause backend errors
          if (compliance.severity_rating && compliance.severity_rating !== '') {
            this.validateComplianceField('severity_rating', compliance.severity_rating, index);
          }
          if (compliance.status) {
            this.validateComplianceField('status', compliance.status, index);
          }
          if (compliance.major_minor) {
            this.validateComplianceField('major_minor', compliance.major_minor, index);
          }
        });
      }
      
      // Count actual field errors (ignoring empty nested objects)
      let hasFieldErrors = false;
      for (const index in this.fieldErrors) {
        if (Object.keys(this.fieldErrors[index]).length > 0) {
          hasFieldErrors = true;
          break;
        }
      }
      
      console.log('Basic validation errors:', errors);
      console.log('Has field errors:', hasFieldErrors);
      
      return Object.keys(errors).length === 0 && !hasFieldErrors;
    },

    getFieldError(fieldName, complianceIndex = null) {
      if (complianceIndex !== null && this.fieldErrors[complianceIndex]) {
        return this.fieldErrors[complianceIndex][fieldName];
      }
      return this.validationErrors[fieldName];
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
  },
  mounted() {
    // Check if we're coming from reports page (read-only mode)
    const fromReports = this.$route.query.from === 'reports';
    if (fromReports) {
      this.isReadOnlyMode = true;
      console.log('TaskView opened in read-only mode from reports page');
    }
    
    this.fetchAuditDetails();
  }
}
</script>

<style scoped>
.audit_task-view {
  padding: 20px;
  max-width: 1200px;
  margin-left: 280px !important;
  font-size: 0.9rem;
}

.audit_readonly-banner {
  background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
  border: 1px solid #b3d9ff;
  border-radius: 6px;
  padding: 8px 16px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #4a90e2;
  font-weight: 500;
  font-size: 0.875rem;
  box-shadow: 0 1px 3px rgba(74, 144, 226, 0.1);
}

.audit_readonly-banner i {
  font-size: 14px;
  color: #4a90e2;
}

.audit_content {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.audit_details-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-top: 20px;
}

.audit_detail-item {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
}

.audit_hierarchy-details {
  margin-top: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
}

.audit_hierarchy-item {
  text-align: center;
  background: white;
  padding: 15px;
  border-radius: 6px;
  min-width: 200px;
}

.audit_hierarchy-arrow {
  color: #666;
  font-size: 24px;
}

.audit_compliance-section {
  margin-top: 30px;
  padding-top: 30px;
  border-top: 1px solid #e0e0e0;
}

.audit_compliance-tabs {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding: 10px 0;
  margin-top: -50px;
  margin-bottom: 20px;
}

.audit_tab-button {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  background: #f0f0f0;
  cursor: pointer;
  white-space: nowrap;
}

.audit_tab-button.active {
  background: #4a69bd;
  color: white;
}

.audit_compliance-details {
  background: white;
  padding: 20px;
  border-radius: 8px;
}

.audit_compliance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.audit_status-badge {
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 0.9em;
}

.audit_status-completed { background: #badc58; color: #2f3640; }
.audit_status-progress { background: #7ed6df; color: #2f3640; }
.audit_status-pending { background: #ff7979; color: white; }

.audit_compliance-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.audit_compliance-item {
  background: white;
  padding: 15px;
  border-radius: 6px;
}

.audit_compliance-item h4 {
  color: #2f3640;
  margin-bottom: 8px;
}

.audit_compliance-item p {
  color: #666;
  margin: 0;
  line-height: 1.5;
}

.audit_loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.audit_error-message {
  background: #fff3f3;
  color: #d63031;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.audit_retry-button {
  background: #2d3436;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.audit_retry-button:hover {
  background: #636e72;
}

/* Audit Details Header Layout */
.audit-details-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

h1 {
  color: #2c3e50;
  margin: 0;
}

.audit_compliance-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.audit_form-group {
  flex: 1;
}

.audit_form-group label {
  display: block;
  margin-bottom: 8px;
}

.audit_form-group.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 0;
  cursor: pointer;
}

.audit_form-group.checkbox-group input[type="checkbox"] {
  width: auto;
  min-width: 16px;
  width: 16px;
  height: 16px;
  margin: 0;
  padding: 0;
  cursor: pointer;
  flex-shrink: 0;
}

.audit_form-group select,
.audit_form-group input,
.audit_form-group textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.audit_form-group input[type="checkbox"] {
  width: auto;
}

/* Reduce spinner arrow size for number inputs */
.audit_form-group input[type="number"]::-webkit-outer-spin-button,
.audit_form-group input[type="number"]::-webkit-inner-spin-button {
  height: 15px;
  width: 7px;
  margin: 4px;
}

.audit_evidence-footer {
  margin-top: 20px;
  padding-top: 20px;
}

.audit_upload-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.audit_evidence-section h3 {
  position: relative;
  top: -6px;
  margin-bottom: 0;
}

.audit_upload-button {
  background: #4a69bd;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  align-self: flex-start;
  margin-top: 3px;
}

.audit_upload-button:hover {
  background: #636e72;
}

.audit_file-name {
  color: #666;
}

.audit_floating-save-container {
  margin-top: 30px;
  display: block;
  opacity: 1;
  transition: all 0.3s ease;
}

.audit_floating-save-button {
  background:  #3a57d9 ;
  color: white;
  border: none;
  padding: 15px 25px;
  border-radius: 8px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
  min-width: 200px;
  justify-content: center;
}

.audit_floating-save-button:hover {
  background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.audit_floating-save-button:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.audit_floating-save-button.saving {
  background-color: #ffc107;
  color: #212529;
}

.audit_save-icon {
  font-size: 16px;
}

.audit_save-text {
  font-size: 14px;
  white-space: nowrap;
}

.audit_corrective-actions-container {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 8px;
}

.audit_risk-mitigation {
  background: #f8f9fa;
  padding: 12px;
  margin-bottom: 12px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.audit_risk-header {
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e9ecef;
}

.audit_risk-header strong {
  color: #2c3e50;
  font-size: 0.95em;
}

.audit_mitigation-actions {
  padding-left: 4px;
}

.audit_mitigation-checkbox {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  cursor: pointer;
  padding: 4px 0;
}

.audit_mitigation-checkbox input[type="checkbox"] {
  margin-top: 4px;
}

.audit_mitigation-text {
  color: #666;
  font-size: 0.9em;
  line-height: 1.4;
  flex: 1;
}

.audit_no-actions {
  color: #666;
  font-style: italic;
  padding: 12px;
  text-align: center;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

/* Add new styles for multiple file uploads */
.audit_evidence-section {
  margin-top: 24px;
  padding: 20px;
  border-radius: 8px;
  margin-left: -16px;
  margin-right: -16px;
}

.audit_evidence-section h3 {
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 5px;
}

.audit_uploaded-files {
  margin-top: 10px;
  max-height: 200px;
  overflow-y: auto;
}

.audit_file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 5px;
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  gap: 8px;
}

.audit_file-item.from-version {
  background: #f8f9fa;
}

.audit_file-name {
  flex: 1;
  font-size: 0.9em;
  color: #666;
}

.audit_version-badge-small {
  background: #4a69bd;
  color: white;
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 0.7em;
  font-weight: bold;
}

.audit_view-file-btn {
  background: #cdcece;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
}

.audit_view-file-btn:hover {
  background: #656665;
}

.audit_remove-file-btn {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.audit_remove-file-btn:hover {
  background: #c82333;
}

.audit_upload-progress {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.audit_progress-bar {
  flex: 1;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.audit_progress-fill {
  height: 100%;
  background: #4a69bd;
  transition: width 0.3s ease;
}

.audit_audit-upload {
  background: #28a745;
}

.audit_audit-upload:hover {
  background: #218838;
}

/* Add new styles for version information */
.audit_version-info {
  margin-top: 20px;
  padding: 15px;
  background: #e8f4fd;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.audit_version-badge {
  display: flex;
  align-items: center;
  gap: 8px;
}

.audit_version-label {
  font-weight: 500;
  color: #2c3e50;
}

.audit_version-number {
  background: #4a69bd;
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: bold;
  font-size: 0.9em;
}

.audit_version-number.new-audit {
  background: #28a745;
}

.audit_version-type {
  font-size: 0.8em;
  color: #666;
  font-style: italic;
  margin-left: 8px;
}

.audit_last-saved {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9em;
  color: #666;
}

.audit_saved-label {
  font-weight: 500;
}

.audit_saved-time {
  color: #4a69bd;
}

/* Add new styles for overall comments section */
.audit_overall-comments-section {
  margin-top: 30px;
  padding: 20px;
  background: white;
  border-radius: 8px;
}

.audit_overall-comments-textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

/* Overall Review Comments Section */
.audit_overall-review-comments-section {
  margin-top: -20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
}

/* Modal styles */
.audit_modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.audit_modal-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.audit_modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e9ecef;
}

.audit_modal-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.25rem;
}

.audit_close-button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.audit_close-button:hover {
  background-color: #f8f9fa;
}

.audit_modal-body {
  padding: 24px;
}

.audit_success-message {
  margin-bottom: 20px;
  padding: 16px;
  background: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 6px;
  color: #155724;
}

.audit_success-message h4 {
  margin: 0 0 8px 0;
  color: #155724;
}

.audit_success-message p {
  margin: 0;
}

.audit_review-question {
  text-align: center;
}

.audit_review-question h4 {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.audit_review-note {
  color: #666;
  font-style: italic;
  margin: 0;
}

.audit_modal-footer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #e9ecef;
}

.audit_btn-secondary {
  background: #6c757d;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s;
  flex: 1;
}

.audit_btn-secondary:hover {
  background: #5a6268;
}

.audit_btn-primary {
  background: #007bff;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s;
  flex: 1;
}

.audit_btn-primary:hover {
  background: #0056b3;
}

.audit_btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* Add Compliance Button Styles */
.audit_compliance-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.audit_add-compliance-button {
  background: #28a745;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.audit_add-compliance-button:hover {
  background: #218838;
}

.audit_add-icon {
  font-size: 16px;
  font-weight: bold;
}

/* Add Compliance Modal Styles */
.audit_add-compliance-modal {
  max-width: 700px;
  width: 90%;
}

.audit_form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.audit_form-row .audit_form-group {
  flex: 1;
}

.audit_form-note {
  margin-top: 20px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 4px solid #17a2b8;
}

.audit_form-note p {
  margin: 0;
  color: #666;
  font-size: 0.9em;
}

.audit_form-note p:first-child {
  margin-bottom: 8px;
}

.audit_radio-group {
  display: flex;
  gap: 20px;
}

.audit_radio-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

/* Add styles for disabled fields */
.audit_form-control.disabled {
  background-color: white;
  cursor: not-allowed;
  opacity: 0.8;
  border: 1px solid #ced4da;
}

.audit_form-control {
  background-color: #ffffff !important;
  background: #ffffff !important;
  background-image: none !important;
}

.audit_form-control option {
  background-color: #ffffff;
  color: #333;
}

.audit_form-control.disabled:focus {
  outline: none;
  box-shadow: none;
}

textarea.disabled::placeholder {
  color: #6c757d;
}

/* Additional disabled styles for read-only mode */
.audit_form-control:disabled {
  background-color: #ffffff !important;
  background: #ffffff !important;
  background-image: none !important;
  color: #666;
  cursor: not-allowed;
  opacity: 0.7;
}

.audit_upload-button:disabled,
.audit_floating-save-button:disabled {
  background-color: #e0e0e0 !important;
  color: #999 !important;
  cursor: not-allowed !important;
  opacity: 0.6;
}

.audit_remove-file-btn:disabled {
  background-color: #f5f5f5 !important;
  color: #999 !important;
  cursor: not-allowed !important;
  opacity: 0.5;
}

/* Validation Error Styles */
.audit_error-message {
  color: #dc3545;
  font-size: 0.875rem;
  margin-top: 4px;
  font-weight: 500;
}

.audit_form-control.has-error {
  border-color: #dc3545;
  box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
}

.audit_validation-summary {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 16px;
}

.audit_validation-summary h4 {
  margin: 0 0 8px 0;
  font-size: 1rem;
}

.audit_validation-summary ul {
  margin: 0;
  padding-left: 20px;
}

.audit_validation-summary li {
  margin-bottom: 4px;
}

.policy-dashboard-back-btn {
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  padding: 6px 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #4f6cff;
  font-size: 14px;
  font-weight: 600;
  min-width: 0;
  width: fit-content;
  height: 40px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  gap: 8px;
}

.policy-dashboard-back-btn:hover {
  background: #4f6cff;
  color: white;
  transform: translateX(-3px);
  box-shadow: 0 8px 25px rgba(79, 108, 255, 0.3);
  border-color: #4f6cff;
}

.policy-dashboard-back-btn:active {
  transform: translateX(-1px);
  box-shadow: 0 4px 12px rgba(79, 108, 255, 0.2);
}
</style> 