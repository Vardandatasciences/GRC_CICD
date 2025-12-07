<template>
  <div class="audit_task-view">
    <button class="audit_back-button" @click="$router.back()">Go back</button>
    <div v-if="error" class="audit_error-message">
      {{ error }}
      <button @click="retryFetch" class="audit_retry-button">Retry</button>
    </div>
    <div v-else-if="loading" class="audit_loading">
      Loading audit details...
    </div>
    <div v-else-if="auditDetails" class="audit_content">
      <!-- Same audit details section as TaskView -->
      <div class="audit_audit-details">
        <h1>Audit Review</h1>
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
                <select v-model="selectedCompliance.status" disabled class="audit_form-control">
                  <option value="2">Fully Compliant</option>
                  <option value="1">Partially Compliant</option>
                  <option value="0">Not Compliant</option>
                  <option value="3">Not Applicable</option>
                </select>
              </div>
              <div class="audit_form-group">
                <label>Type of Findings</label>
                <select v-model="selectedCompliance.major_minor" disabled class="audit_form-control">
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
                  disabled
                  min="1"
                  max="10"
                  class="audit_form-control"
                >
              </div>
            </div>

            <!-- Row 2 -->
            <div class="audit_compliance-row">
              <div class="audit_form-group">
                <label>What to Verify</label>
                <textarea v-model="selectedCompliance.what_to_verify" disabled class="audit_form-control"></textarea>
              </div>
              <div class="audit_form-group">
                <label>How to Verify</label>
                <textarea v-model="selectedCompliance.how_to_verify" disabled class="audit_form-control"></textarea>
              </div>
              <div class="audit_form-group">
                <label>Impact</label>
                <textarea v-model="selectedCompliance.impact" disabled class="audit_form-control"></textarea>
              </div>
            </div>

            <!-- Row 3 -->
            <div class="audit_compliance-row">
              <div class="audit_form-group">
                <label>Why to Verify</label>
                <textarea v-model="selectedCompliance.why_to_verify" disabled class="audit_form-control"></textarea>
              </div>
              <div class="audit_form-group">
                <label>Details of Findings</label>
                <textarea v-model="selectedCompliance.details_of_finding" disabled class="audit_form-control"></textarea>
              </div>
              <div class="audit_form-group">
                <label>Underlying Cause</label>
                <textarea v-model="selectedCompliance.underlying_cause" disabled class="audit_form-control"></textarea>
              </div>
            </div>

            <!-- Row 4 -->
            <div class="audit_compliance-row">
              <div class="audit_form-group">
                <label>Predictive Risks</label>
                <select v-model="selectedCompliance.selected_risks" class="audit_form-control" multiple disabled>
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
                               disabled>
                        <span class="audit_mitigation-text">{{ risk.mitigation }}</span>
                      </label>
                    </div>
                  </div>
                </div>
                <div v-else class="audit_no-actions">
                  No risks selected
                </div>
              </div>
            </div>

            <!-- Row 5 -->
            <div class="audit_compliance-row">
              <div class="audit_form-group">
                <label>Suggested Action Plan</label>
                <textarea v-model="selectedCompliance.suggested_action_plan" disabled class="audit_form-control"></textarea>
              </div>
              <div class="audit_form-group audit_small-input">
                <label>Responsible for Plan</label>
                <input type="text" v-model="selectedCompliance.responsible_for_plan" disabled class="audit_form-control">
              </div>
              <div class="audit_form-group">
                <label>Mitigation Date</label>
                <input type="date" v-model="selectedCompliance.mitigation_date" disabled class="audit_form-control">
              </div>
            </div>

            <!-- Row 6 -->
            <div class="audit_compliance-row">
              <div class="audit_form-group audit_checkbox-group">
                <label>
                  <input type="checkbox" v-model="selectedCompliance.re_audit" disabled>
                  Re-audit Required
                </label>
              </div>
              <div class="audit_form-group" v-if="selectedCompliance.re_audit">
                <label>Re-audit Date</label>
                <input type="date" v-model="selectedCompliance.re_audit_date" disabled class="audit_form-control">
              </div>
              <div class="audit_form-group">
                <label>Comments</label>
                <textarea v-model="selectedCompliance.comments" disabled class="audit_form-control"></textarea>
              </div>
            </div>

            <!-- Review Status and Comments -->
            <div class="audit_compliance-row audit_review-section">
              <div class="audit_form-group">
                <label>Review Status</label>
                <select v-model="selectedCompliance.review_status" class="audit_form-control">
                  <option value="in_review">In Review</option>
                  <option value="accept">Accept</option>
                  <option value="reject">Reject</option>
                </select>
              </div>
              <div class="audit_form-group">
                <label>Review Comments</label>
                <textarea v-model="selectedCompliance.review_comments" class="audit_form-control"></textarea>
              </div>
            </div>

            <!-- Evidence Section -->
            <div class="audit_evidence-footer">
              <div class="audit_form-group">
                <label>Compliance Evidence</label>
                <div v-if="selectedCompliance.evidence_files && selectedCompliance.evidence_files.length > 0" class="audit_uploaded-files">
                  <div v-for="(file, index) in selectedCompliance.evidence_files" :key="index" class="audit_file-item" :class="{ 'audit_from-version': file.fromVersion }">
                    <span class="audit_file-name">{{ file.name }}</span>
                    <span v-if="file.fromVersion" class="audit_version-badge-small">From Version</span>
                    <a v-if="file.url" :href="file.url" target="_blank" class="audit_view-file-btn" title="View File"><i class="fas fa-eye"></i></a>
                  </div>
                </div>
                <div v-else class="audit_no-evidence">
                  No evidence files uploaded
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Audit Evidence Section -->
      <div class="audit_audit-evidence-section">
        <h3>Audit Evidence</h3>
        <div v-if="auditEvidenceFiles && auditEvidenceFiles.length > 0" class="audit_uploaded-files">
          <div v-for="(file, index) in auditEvidenceFiles" :key="index" class="audit_file-item" :class="{ 'audit_from-version': file.fromVersion }">
            <span class="audit_file-name">{{ file.name }}</span>
            <span v-if="file.fromVersion" class="audit_version-badge-small">From Version</span>
            <a v-if="file.url" :href="file.url" target="_blank" class="audit_view-file-btn" title="View File"><i class="fas fa-eye"></i></a>
          </div>
        </div>
        <div v-else class="audit_no-evidence">
          No audit evidence files uploaded
        </div>
      </div>

      <!-- Overall Audit Comments Section -->
      <div class="audit_overall-comments-section">
        <h3>Overall Audit Comments</h3>
        <div class="audit_form-group">
          <textarea 
            v-model="overallAuditComments" 
            disabled
            class="audit_form-control audit_overall-comments-textarea"
            placeholder="No overall audit comments available"
            rows="4"
          ></textarea>
        </div>
      </div>

      <!-- Overall Review Comments Section -->
      <div class="audit_overall-review-comments-section">
        <h3>Overall Review Comments</h3>
        <textarea
          v-model="overallReviewComments"
          class="audit_form-control"
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

      <!-- Floating Save Button -->
      <div class="audit_floating-save-container">
        <button @click="saveReview" class="audit_floating-save-button" :disabled="isSavingReview">
          <span class="audit_save-text">
            {{ isSavingReview ? 'Saving Review...' : 'Save Review' }}
          </span>
        </button>
      </div>
    </div>

    <!-- Modals -->
    <div v-if="showRejectModal" class="audit_modal-overlay" @click="keepEditing">
      <div class="audit_modal-content" @click.stop>
        <div class="audit_modal-header">
          <h3>Confirm Rejection</h3>
          <button @click="keepEditing" class="audit_close-button">&times;</button>
        </div>
        <div class="audit_modal-body">
          <div class="audit_warning-message">
            <h4>Review Rejection Detected</h4>
            <p>You have rejected one or more compliance items. This will send the audit back for revision.</p>
            <p class="audit_status-note">
              <em>This will change the audit status from "Under Review" to "Needs Revision"</em>
            </p>
          </div>
        </div>
        <div class="audit_modal-footer">
          <button @click="keepEditing" class="audit_btn-secondary">Keep Editing</button>
          <button @click="confirmReject" class="audit_btn-danger">
            Yes, Reject and Return
          </button>
        </div>
      </div>
    </div>

    <div v-if="showAcceptModal" class="audit_modal-overlay" @click="keepEditing">
      <div class="audit_modal-content" @click.stop>
        <div class="audit_modal-header">
          <h3>Confirm Acceptance</h3>
          <button @click="keepEditing" class="audit_close-button">&times;</button>
        </div>
        <div class="audit_modal-body">
          <div class="audit_success-message">
            <h4>All Items Accepted</h4>
            <p>You have accepted all compliance items. This will complete the audit review.</p>
            <p class="audit_status-note">
              <em>This will change the audit status to "Completed"</em>
            </p>
          </div>
        </div>
        <div class="audit_modal-footer">
          <button @click="keepEditing" class="audit_btn-secondary">Keep Editing</button>
          <button @click="confirmAccept" class="audit_btn-primary">
            Yes, Complete Review
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '../../data/api';
import { AccessUtils } from '@/utils/accessUtils';
import { API_ENDPOINTS } from '../../config/api.js';

export default {
  name: 'ReviewTaskView',
  data() {
    return {
      auditDetails: null,
      error: null,
      loading: true,
      selectedComplianceIndex: null,
      auditEvidenceFiles: [],
      currentVersion: null,
      lastSavedTime: null,
      isSavingReview: false,
      selectedCompliance: null,
      hasUnsavedChanges: false,
      overallAuditComments: '',
      overallReviewComments: '',
      savedVersionData: null,
      showRejectModal: false,
      showAcceptModal: false
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

    async fetchAuditDetails() {
      this.loading = true;
      this.error = null;
      try {
        const auditId = this.$route.params.auditId;
        if (!auditId) {
          this.error = 'No audit ID provided';
          return;
        }
        console.log('Fetching details for audit:', auditId);
        const taskResponse = await api.getAuditTaskDetails(auditId);
        this.auditDetails = taskResponse.data;
        
        // Initialize review fields if not present
        this.auditDetails.compliances.forEach(compliance => {
          if (!compliance.review_status) compliance.review_status = 'in_review';
          if (!compliance.review_comments) compliance.review_comments = '';
          
          // Initialize evidence files array
          compliance.evidence_files = [];
          if (compliance.evidence) {
            const urls = compliance.evidence.split(',').filter(url => url.trim());
            compliance.evidence_files = urls.map(url => ({
              name: this.extractFilenameFromUrl(url) || 'Evidence File',
              url: url.trim(),
              fromVersion: this.auditDetails.loaded_from_version || false
            }));
          }
        });

        // Initialize audit evidence files
        this.auditEvidenceFiles = [];
        if (this.auditDetails.evidence_urls) {
          const urls = this.auditDetails.evidence_urls.split(',').filter(url => url.trim());
          this.auditEvidenceFiles = urls.map(url => ({
            name: this.extractFilenameFromUrl(url) || 'Audit Evidence File',
            url: url.trim(),
            fromVersion: this.auditDetails.loaded_from_version || false
          }));
        }

        // Set version information
        if (this.auditDetails.current_version) {
          this.currentVersion = this.auditDetails.current_version;
          this.lastSavedTime = this.auditDetails.version_date;
        }

        // Load comments - distinguish between audit and review comments
        this.overallAuditComments = this.auditDetails.overall_audit_comments || '';
        this.overallReviewComments = this.auditDetails.overall_review_comments || '';

        // Select first compliance by default
        if (this.auditDetails.compliances?.length > 0) {
          this.selectCompliance(this.auditDetails.compliances[0], 0);
        }

      } catch (error) {
        console.error('Error fetching audit details:', error);
        // Handle access denied errors
        if (AccessUtils.handleApiError(error, 'audit review details access')) {
          this.error = 'Access denied';
        } else {
          this.error = error.response?.data?.error || 'Failed to load audit details';
        }
      } finally {
        this.loading = false;
      }
    },

    extractFilenameFromUrl(url) {
      if (!url) return null;
      try {
        const urlParts = url.split('/');
        return decodeURIComponent(urlParts[urlParts.length - 1]);
      } catch (error) {
        console.warn('Error extracting filename from URL:', error);
        return null;
      }
    },

    selectCompliance(compliance, index) {
      this.selectedCompliance = compliance;
      this.selectedComplianceIndex = index;
    },

    async saveReview() {
      if (this.isSavingReview) return;

      try {
        this.isSavingReview = true;
        const auditId = this.$route.params.auditId;

        // Check if all compliances have review status selected
        const allCompliances = this.auditDetails.compliances;
        const unreviewed = allCompliances.filter(comp => !comp.review_status || comp.review_status === 'in_review');
        
        // Prepare the review data
        const complianceReviews = allCompliances.map(comp => ({
          compliance_id: comp.id,
          review_status: comp.review_status || 'in_review',
          review_comments: comp.review_comments || ''
        }));

        const payload = {
          compliance_reviews: complianceReviews,
          review_comments: this.overallReviewComments || '',
          overall_audit_comments: this.overallAuditComments || '', // Preserve audit comments
          save_only: true // Don't update status yet
        };

        // Check if all compliances have been reviewed (not in 'in_review' status)
        if (unreviewed.length === 0) {
          // All compliances have been reviewed, check for rejections/acceptances
          const hasRejection = allCompliances.some(comp => comp.review_status === 'reject');
          const allAccepted = allCompliances.every(comp => comp.review_status === 'accept');

          if (hasRejection) {
            // Show rejection modal
            this.showRejectModal = true;
            this.savedVersionData = payload; // Store for later use
            return;
          } else if (allAccepted) {
            // Show acceptance modal
            this.showAcceptModal = true;
            this.savedVersionData = payload; // Store for later use
            return;
          }
        }

        // Save as work in progress if not all compliances are reviewed
        const response = await api.saveReviewProgress(auditId, payload);
        if (response.data.message) {
          this.currentVersion = response.data.review_version;
          this.lastSavedTime = new Date().toISOString();
          this.hasUnsavedChanges = false;
          
          if (unreviewed.length > 0) {
            this.$toast?.info(`Saved progress. ${unreviewed.length} compliance(s) still need review.`);
            this.sendPushNotification({
              title: 'Review Progress Saved',
              message: `Saved progress. ${unreviewed.length} compliance(s) still need review for audit "${this.auditDetails?.title || ''}"`,
              category: 'review',
              priority: 'info',
              user_id: 'default_user'
            });
          } else {
            this.$toast?.success(`Review version ${this.currentVersion} saved successfully`);
            this.sendPushNotification({
              title: 'Review Version Saved',
              message: `Review version ${this.currentVersion} saved successfully for audit "${this.auditDetails?.title || ''}"`,
              category: 'review',
              priority: 'success',
              user_id: 'default_user'
            });
          }
        } else {
          throw new Error('Failed to save review version');
        }

      } catch (error) {
        console.error('Error in saveReview:', error);
        this.$toast?.error('Failed to save review: ' + (error.response?.data?.error || error.message));
        this.sendPushNotification({
          title: 'Review Save Failed',
          message: 'Failed to save review: ' + (error.response?.data?.error || error.message),
          category: 'review',
          priority: 'error',
          user_id: 'default_user'
        });
      } finally {
        this.isSavingReview = false;
      }
    },

    async confirmReject() {
      try {
        if (this.savedVersionData) {
          const auditId = this.$route.params.auditId;
          
          // First save the review version with rejection status
          const saveResponse = await api.saveReviewProgress(auditId, {
            compliance_reviews: this.savedVersionData.compliance_reviews,
            review_comments: this.overallReviewComments,
            overall_audit_comments: this.overallAuditComments, // Preserve audit comments
            save_only: false,
            is_rejected: true
          });

          if (saveResponse.data.message) {
            // Then update the review status
            await api.updateReviewStatus(auditId, {
              review_status: 'Reject',  // This maps to '3' in backend
              status: 'Work In Progress',
              review_comments: this.overallReviewComments,
              overall_audit_comments: this.overallAuditComments, // Preserve audit comments
              compliance_reviews: this.savedVersionData.compliance_reviews
            });

            this.$toast?.success('Audit has been rejected and returned for revision');
            this.sendPushNotification({
              title: 'Audit Rejected',
              message: 'Audit has been rejected and returned for revision for audit "' + (this.auditDetails?.title || '') + '"',
              category: 'review',
              priority: 'warning',
              user_id: 'default_user'
            });
            this.showRejectModal = false;
            this.$router.push('/reviewer'); // Redirect to reviews list
          } else {
            throw new Error('Failed to save review version');
          }
        }
      } catch (error) {
        console.error('Error confirming rejection:', error);
        // Handle access denied errors
        if (AccessUtils.handleApiError(error, 'audit review rejection')) {
          return;
        }
        this.$toast?.error('Failed to process rejection: ' + (error.response?.data?.error || error.message));
        this.sendPushNotification({
          title: 'Review Rejection Failed',
          message: 'Failed to process rejection: ' + (error.response?.data?.error || error.message),
          category: 'review',
          priority: 'error',
          user_id: 'default_user'
        });
      }
    },

    async confirmAccept() {
      try {
        if (this.savedVersionData) {
          const auditId = this.$route.params.auditId;
          
          // Prepare detailed compliance data
          const complianceData = this.auditDetails.compliances.map(comp => ({
            compliance_id: comp.id,
            review_status: comp.review_status || 'accept',
            review_comments: comp.review_comments || '',
            evidence: comp.evidence || '',
            how_to_verify: comp.how_to_verify || '',
            impact: comp.impact || '',
            details_of_finding: comp.details_of_finding || '',
            comments: comp.comments || '',
            major_minor: comp.major_minor || '',
            severity_rating: comp.severity_rating || 0,
            predictive_risks: comp.selected_risks || [],
            corrective_actions: comp.selected_mitigations || [],
            underlying_cause: comp.underlying_cause || '',
            why_to_verify: comp.why_to_verify || '',
            what_to_verify: comp.what_to_verify || '',
            suggested_action_plan: comp.suggested_action_plan || '',
            mitigation_date: comp.mitigation_date || null,
            responsible_for_plan: comp.responsible_for_plan || '',
            re_audit: comp.re_audit ? 1 : 0,
            re_audit_date: comp.re_audit_date || null,
            compliance_status: comp.status
          }));

          // First save the review data with complete compliance information
          const saveResponse = await api.saveReviewProgress(auditId, {
            ...this.savedVersionData,
            compliance_data: complianceData,
            overall_audit_comments: this.overallAuditComments, // Preserve audit comments
            save_only: false // Allow status update
          });

          if (saveResponse.data.message) {
            // Then update the review status with complete compliance data
            await api.updateReviewStatus(auditId, {
              status: 'accept',
              review_comments: this.overallReviewComments,
              overall_audit_comments: this.overallAuditComments, // Preserve audit comments
              compliance_reviews: complianceData
            });

            this.showAcceptModal = false;
            this.$router.push('/reviewer'); // Redirect to reviews list
          } else {
            throw new Error('Failed to save review version');
          }
        }
      } catch (error) {
        console.error('Error confirming acceptance:', error);
        // Handle access denied errors
        if (AccessUtils.handleApiError(error, 'audit review acceptance')) {
          return;
        }
        this.$toast?.error('Failed to process acceptance: ' + (error.response?.data?.error || error.message));
        this.sendPushNotification({
          title: 'Review Acceptance Failed',
          message: 'Failed to process acceptance: ' + (error.response?.data?.error || error.message),
          category: 'review',
          priority: 'error',
          user_id: 'default_user'
        });
      }
    },

    keepEditing() {
      // Just close the modal without any status updates
      this.showRejectModal = false;
      this.showAcceptModal = false;
      
      // Save the version without any status updates if there's pending data
      if (this.savedVersionData) {
        const auditId = this.$route.params.auditId;
        api.saveReviewProgress(auditId, {
          ...this.savedVersionData,
          overall_audit_comments: this.overallAuditComments, // Preserve audit comments
          review_comments: this.overallReviewComments, // Use review comments
          save_only: true,  // Don't update any status
          is_rejected: false  // Don't mark as rejected
        }).then(response => {
          if (response.data.message) {
            this.currentVersion = response.data.review_version;
            this.lastSavedTime = new Date().toISOString();
            this.$toast?.success(`Review version ${this.currentVersion} saved successfully`);
            this.sendPushNotification({
              title: 'Review Version Saved',
              message: `Review version ${this.currentVersion} saved successfully for audit "${this.auditDetails?.title || ''}"`,
              category: 'review',
              priority: 'success',
              user_id: 'default_user'
            });
          }
        }).catch(error => {
          console.error('Error saving review:', error);
          // Handle access denied errors
          if (AccessUtils.handleApiError(error, 'audit review save')) {
            return;
          }
          this.$toast?.error('Failed to save review: ' + (error.response?.data?.error || error.message));
          this.sendPushNotification({
            title: 'Review Save Failed',
            message: 'Failed to save review: ' + (error.response?.data?.error || error.message),
            category: 'review',
            priority: 'error',
            user_id: 'default_user'
          });
        });
      }
      
      this.savedVersionData = null;
    },

    retryFetch() {
      this.fetchAuditDetails();
    }
  },
  mounted() {
    this.fetchAuditDetails();
  }
}
</script>

<style scoped>
/* Reuse existing styles from TaskView.vue */
.audit_task-view {
  padding: 20px;
  max-width: 1200px;
  margin-left: 280px !important;
}

/* Add review-specific styles */
.audit_review-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
  border-left: 4px solid #4a69bd;
}

.audit_no-evidence {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  color: #666;
  font-style: italic;
  text-align: center;
}

/* Disabled form controls */
.audit_form-control[disabled] {
  background-color: #e9ecef;
  cursor: not-allowed;
  opacity: 0.8;
}

/* Review status colors */
.audit_review-status-accept {
  color: #28a745;
}

.audit_review-status-reject {
  color: #dc3545;
}

.audit_review-status-in-review {
  color: #ffc107;
}

/* Rest of the styles from TaskView.vue */
/* ... */

/* Audit Details Section */
.audit_audit-details {
  background: white;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 30px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.audit_details-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.audit_detail-item {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
}

.audit_detail-item h3 {
  color: #2c3e50;
  margin: 0 0 8px 0;
  font-size: 1rem;
  font-weight: 600;
}

.audit_detail-item p {
  margin: 0;
  color: #666;
}

/* Framework Policy Section */
.audit_hierarchy-details {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 30px;
}

.audit_hierarchy-item {
  background: white;
  padding: 15px 25px;
  border-radius: 6px;
  text-align: center;
  min-width: 180px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.audit_hierarchy-arrow {
  color: #4a69bd;
  font-size: 24px;
}

/* Compliance Section */
.audit_compliance-section {
  background: white;
  border-radius: 8px;
  padding: 24px;
  margin-top: 30px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.audit_compliance-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.audit_compliance-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  overflow-x: auto;
  padding: 10px 0;
}

.audit_tab-button {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  background: #f0f0f0;
  cursor: pointer;
  font-weight: 500;
  color: #666;
  transition: all 0.2s;
}

.audit_tab-button.active {
  background: #4a69bd;
  color: white;
}

/* Compliance Details */
.audit_compliance-details {
  background: #f8f9fa;
  padding: 24px;
  border-radius: 8px;
}

.audit_compliance-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.audit_form-group {
  margin-bottom: 15px;
}

.audit_form-group label {
  display: block;
  margin-bottom: 8px;
  color: #2c3e50;
  font-weight: 500;
}

.audit_form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
  background-color: #ffffff !important;
  background: #ffffff !important;
  background-image: none !important;
}

.audit_form-control option {
  background-color: #ffffff;
  color: #333;
}

.audit_form-control:focus {
  border-color: #4a69bd;
  outline: none;
}

.audit_form-control[disabled] {
  background-color: #ffffff !important;
  background: #ffffff !important;
  background-image: none !important;
  cursor: not-allowed;
}

/* Review Section Specific */
.audit_review-section {
  background: #fff;
  border: 1px solid #e9ecef;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
  border-left: 4px solid #4a69bd;
}

.audit_review-section select {
  font-weight: 500;
}

.audit_review-section textarea {
  min-height: 100px;
}

/* Evidence Section */
.audit_evidence-section {
  margin-top: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.audit_uploaded-files {
  margin-top: 10px;
  max-height: 200px;
  overflow-y: auto;
}

.audit_file-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  margin-bottom: 8px;
}

.audit_file-name {
  flex: 1;
  margin-right: 10px;
  color: #2c3e50;
}

.audit_view-file-btn {
  padding: 4px 8px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  text-decoration: none;
  font-size: 12px;
}

/* Version Info */
.audit_version-info {
  margin-top: 30px;
  padding: 15px;
  background: #e8f4fd;
  border-radius: 8px;
  border-left: 4px solid #4a69bd;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.audit_version-badge {
  display: flex;
  align-items: center;
  gap: 8px;
}

.audit_version-number {
  background: #4a69bd;
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: bold;
}

/* Save Button */
.audit_floating-save-button {
  position: fixed;
  bottom: 30px;
  right: 30px;
  background: #4e6bea ;
  color: white;
  border: none;
  padding: 15px 30px;
  border-radius: 50px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
}

.audit_floating-save-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}

.audit_floating-save-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* Overall Comments Section */
.audit_overall-comments-section,
.audit_overall-review-comments-section {
  background: white;
  border-radius: 8px;
  padding: 24px;
  margin-top: 30px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.audit_overall-comments-section h3,
.audit_overall-review-comments-section h3 {
  color: #2c3e50;
  margin: 0 0 15px 0;
}

.audit_overall-comments-textarea {
  width: 100%;
  min-height: 120px;
  padding: 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  resize: vertical;
}

/* Loading and Error States */
.audit_loading {
  text-align: center;
  padding: 40px;
  color: #666;
  font-size: 1.1em;
}

.audit_error-message {
  background: #fff3f3;
  color: #dc3545;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.audit_retry-button {
  background: #dc3545;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.audit_retry-button:hover {
  background: #c82333;
}

/* Responsive Design */
@media (max-width: 768px) {
  .details-container {
    grid-template-columns: 1fr;
  }
  
  .compliance-row {
    grid-template-columns: 1fr;
  }
  
  .hierarchy-details {
    flex-direction: column;
    gap: 10px;
  }
  
  .hierarchy-arrow {
    transform: rotate(90deg);
  }
  
  .floating-save-button {
    bottom: 20px;
    right: 20px;
    padding: 12px 20px;
  }
}

.audit_warning-message {
  background: #fff3cd;
  border: 1px solid #ffeeba;
  color: #856404;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.audit_success-message {
  background: #d4edda;
  border: 1px solid #c3e6cb;
  color: #155724;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.audit_status-note {
  margin-top: 12px;
  font-size: 0.9em;
  color: #666;
}

.audit_btn-danger {
  background: #dc3545;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
  flex: 1;
}

.audit_btn-danger:hover {
  background: #c82333;
}

/* Modal Styles */
.audit_modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.audit_modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.audit_modal-header {
  padding: 16px;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.audit_modal-header h3 {
  margin: 0;
  color: #2c3e50;
}

.audit_close-button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.audit_modal-body {
  padding: 20px;
}

.audit_modal-footer {
  padding: 16px;
  border-top: 1px solid #e9ecef;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.audit_btn-secondary {
  background: #6c757d;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.audit_btn-secondary:hover {
  background: #5a6268;
}

.audit_btn-primary {
  background: #4a69bd;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.audit_btn-primary:hover {
  background: #3f5aa9;
}

.audit_back-button {
  position: absolute;
  top: 24px;
  right: 32px;
  background: #c5c5c5;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 8px 20px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  z-index: 10;
  transition: background 0.2s;
}
.audit_back-button:hover {
  background: #898989;
}
</style>
