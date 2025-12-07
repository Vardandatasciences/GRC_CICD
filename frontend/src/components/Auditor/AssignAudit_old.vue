<template>
  <div class="assign-audit-page">
    <div class="audit-content">
      <h1 class="audit-title">Audit Assignment</h1>

      <!-- Tab Navigation -->
      <div class="audit-tabs">
        <button 
          v-for="(tab, index) in tabs" 
          :key="index"
          :class="['tab-button', { active: currentTab === index }]"
          @click="currentTab = index"
        >
          {{ tab.name }}
          <span class="tab-number">{{ index + 1 }}</span>
      </button>
      </div>

      <!-- Framework Selection Tab -->
      <div v-if="currentTab === 0" class="tab-content">
        <h2>Framework Selection</h2>
        <div class="dynamic-fields-row">
          <div class="dynamic-field-col">
            <label class="dynamic-label">Framework</label>
            <div class="dynamic-desc">Select the framework under which this audit is being conducted.</div>
            <SelectInput
              v-model="auditData.framework"
              :options="frameworks.map(fw => ({ value: fw.FrameworkId, label: fw.FrameworkName }))"
              label="Framework"
              placeholder="Select Framework"
              :error="getFieldError('framework')"
              @change="onFrameworkChange"
            />
            <div v-if="auditData.framework && !auditData.policy" class="compliance-scope-desc">
              Will include permanent compliances from all policies and subpolicies under this framework
            </div>
          </div>
        </div>
      </div>

      <!-- Team Creation Tab -->
      <div v-if="currentTab === 1" class="tab-content">
        <h2>Team Creation</h2>
        
        <!-- Add Team Member Button -->
        <button class="add-member-btn" @click="addTeamMember">
          <span class="plus-icon">+</span> Add Team Member
        </button>

        <!-- Team Members List -->
        <div v-for="(member, index) in teamMembers" :key="index" class="team-member-card">
          <div class="dynamic-fields-row">
            <div class="dynamic-field-col">
              <label class="dynamic-label">Auditor</label>
              <div class="dynamic-desc">Select the auditor responsible for this audit.</div>
              <SelectInput
                v-model="member.auditor"
                :options="users.map(user => ({ value: user.UserId, label: user.UserName }))"
                label="Auditor"
                placeholder="Select Auditor"
                :error="getFieldError('auditor', index)"
              />
            </div>
            <div class="dynamic-field-col">
              <label class="dynamic-label">Role</label>
              <div class="dynamic-desc">Select the role of the auditor in this audit.</div>
              <SelectInput
                v-model="member.role"
                :options="roles.map(role => ({ value: role, label: role }))"
                label="Role"
                placeholder="Select Role"
                :error="getFieldError('role', index)"
              />
            </div>
            <div class="dynamic-field-col">
              <label class="dynamic-label">Primary Responsibilities</label>
              <div class="dynamic-desc">Describe the main responsibilities for this team member.</div>
              <TextareaInput
                v-model="member.responsibilities"
                label="Primary Responsibilities"
                placeholder="Enter responsibilities..."
                :error="getFieldError('responsibilities', index)"
                rows="3"
              />
            </div>
          </div>

          <!-- Remove Member Button -->
          <button v-if="index > 0" class="remove-member-btn" @click="removeTeamMember(index)">
            Remove
          </button>
        </div>
      </div>

      <!-- Policy Assignment Tab -->
      <div v-if="currentTab === 2" class="tab-content">
        <h2>Policy Assignment & Audit Details</h2>

        <!-- Team Assignments Section -->
        <div class="team-assignments-section">
          <div v-for="(member, index) in teamMembers" :key="index" class="team-assignment-card">
            <div class="member-header">
              <h4>{{ getUserName(member.auditor) || 'Team Member' }} - {{ member.role }}</h4>
            </div>
            
            <!-- Policy Assignment Section -->
            <div class="collapsible-section">
              <div class="section-header" @click="toggleSection(member, 'policyAssignment')">
                <h5>Policy Assignment</h5>
                <i :class="['fas', member.isPolicyAssignmentExpanded ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
              </div>
              
              <div class="section-content" :class="{ 'collapsed': !member.isPolicyAssignmentExpanded }">
                <div class="dynamic-fields-row">
                  <div class="dynamic-field-col">
                    <label class="dynamic-label">Assigned Policy</label>
                    <div class="dynamic-desc">Select the policy to be audited by this team member.</div>
                    <SelectInput
                      v-model="member.assignedPolicy"
                      :options="policies.map(p => ({ value: p.PolicyId, label: p.PolicyName }))"
                      label="Assigned Policy"
                      placeholder="Select Policy"
                      :error="getFieldError('assignedPolicy', index)"
                      @change="onMemberPolicyChange(index)"
                    />
                  </div>
                  <div class="dynamic-field-col">
                    <label class="dynamic-label">Sub Policy</label>
                    <div class="dynamic-desc">Select specific sub policy if applicable.</div>
                    <SelectInput
                      v-model="member.assignedSubPolicy"
                      :options="getMemberSubpolicies(index).map(sp => ({ value: sp.SubPolicyId, label: sp.SubPolicyName }))"
                      label="Sub Policy"
                      placeholder="Select Sub Policy"
                      @change="onSubPolicyChange(index)"
                    />
                  </div>
                  <div class="dynamic-field-col">
                    <label class="dynamic-label">Reviewer</label>
                    <div class="dynamic-desc">Choose the reviewer who will review this audit.</div>
                    <SelectInput
                      v-model="member.reviewer"
                      :options="users.map(user => ({ value: user.UserId, label: user.UserName }))"
                      label="Reviewer"
                      placeholder="Select Reviewer"
                      :error="getFieldError('reviewer', index)"
                    />
                  </div>
                </div>

                <!-- Reports Section -->
                <div class="reports-section">
                  <div class="reports-row">
                    <div class="reports-col">
                      <button class="reports-btn" @click="showReportsModal(member)">
                        <i class="fas fa-file-alt"></i> Attach Reports
                      </button>
                    </div>
                  </div>
                  
                  <!-- Display Selected Reports -->
                  <div v-if="getSelectedReportsForMember(member).length > 0" class="selected-reports">
                    <h6>Selected Reports:</h6>
                    <div class="selected-reports-list">
                      <div v-for="report in getSelectedReportsForMember(member)" 
                           :key="report.ReportId" 
                           class="selected-report-item">
                        <span class="report-title">Report #{{ report.ReportId }}</span>
                        <span class="report-info">
                          {{ report.AuditorName }} - {{ formatDate(report.CompletionDate) }}
                        </span>
                        <button class="remove-report-btn" @click="removeReport(member, report.ReportId)">
                          <i class="fas fa-times"></i>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Audit Details Section -->
            <div class="collapsible-section">
              <div class="section-header" @click="toggleSection(member, 'auditDetails')">
                <h5>Audit Details</h5>
                <i :class="['fas', member.isAuditDetailsExpanded ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
              </div>
              
              <div class="section-content" :class="{ 'collapsed': !member.isAuditDetailsExpanded }">
                <div class="dynamic-fields-row">
                  <div class="dynamic-field-col">
                    <label class="dynamic-label">Audit Title</label>
                    <div class="dynamic-desc">Enter a concise title for this audit assignment.</div>
                    <!-- <TextInput
                      v-model="member.auditTitle"
                      label="Audit Title"
                      placeholder="Enter audit title..."
                      
                    />   -->
                    <input type="text" v-model="member.auditTitle" class="dynamic-input" placeholder="Enter audit title..." />
                  </div>
                  <div class="dynamic-field-col">
                    <label class="dynamic-label">Business Unit</label>
                    <div class="dynamic-desc">Mention the business unit or process area being audited.</div>
                    <!-- <TextInput
                      v-model="member.businessUnit"
                      label="Business Unit"
                      placeholder="Enter business unit..."
                    /> -->
                    <input type="text" v-model="member.businessUnit" class="dynamic-input" placeholder="Enter business unit..." />

                  </div>
                </div>

                <div class="dynamic-fields-row">
                  <div class="dynamic-field-col">
                    <label class="dynamic-label">Scope</label>
                    <div class="dynamic-desc">Specify the boundaries and extent of the audit.</div>
                    <TextareaInput
                      v-model="member.scope"
                      label="Scope"
                      placeholder="Enter scope..."
                      :error="getFieldError('scope', index)"
                      rows="3"
                    />
                  </div>
                  <div class="dynamic-field-col">
                    <label class="dynamic-label">Objective</label>
                    <div class="dynamic-desc">State the main goals or objectives of the audit.</div>
                    <TextareaInput
                      v-model="member.objective"
                      label="Objective"
                      placeholder="Enter objective..."
                      :error="getFieldError('objective', index)"
                      rows="3"
                    />
                  </div>
                </div>
                <div class="dynamic-fields-row">
                  <div class="dynamic-field-col">
                    <label class="dynamic-label">Type</label>
                    <div class="dynamic-desc">Select whether the audit is Internal or External.</div>
                    <SelectInput
                      v-model="member.type"
                      :options="[
                        { value: 'I', label: 'Internal' },
                        { value: 'E', label: 'External' },
                        { value: 'S', label: 'Self-Audit' }
                      ]"
                      label="Type"
                      placeholder="Select Type"
                      :error="getFieldError('type', index)"
                    />
                  </div>
                  <div class="dynamic-field-col">
                    <label class="dynamic-label">Frequency</label>
                    <div class="dynamic-desc">How often should this audit occur?</div>
                    <SelectInput
                      v-model="member.frequency"
                      :options="[
                        { value: '0', label: 'Only Once' },
                        { value: '1', label: 'Daily' },
                        { value: '60', label: 'Every 2 Months' },
                        { value: '120', label: 'Every 4 Months' },
                        { value: '182', label: 'Half Yearly' },
                        { value: '365', label: 'Yearly' },
                        { value: '365a', label: 'Annually' }
                      ]"
                      label="Frequency"
                      placeholder="Select Frequency"
                      :error="getFieldError('frequency', index)"
                    />
                  </div>
                  <div class="dynamic-field-col">
                    <label class="dynamic-label">Due Date</label>
                    <div class="dynamic-desc">Select the due date for this audit.</div>
                    <DateInput
                      v-model="member.dueDate"
                      label="Due Date"
                      placeholder="Select due date"
                      :error="getFieldError('dueDate', index)"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div class="compliance-preview" v-if="member.assignedPolicy">
              <div class="preview-header">Compliance Items to be Audited:</div>
              <div class="preview-content">
                <div class="compliance-count" :class="{ 'loading': complianceCountLoading[`${member.assignedPolicy}-loading`] }">
                  <span v-if="complianceCountLoading[`${member.assignedPolicy}-loading`]">Loading...</span>
                  <span v-else>{{ getComplianceCount(member.assignedPolicy, member.assignedSubPolicy) }} items</span>
                </div>
                <div class="compliance-scope-desc" v-if="!member.assignedSubPolicy">
                  Will include permanent compliances from all subpolicies under this policy
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Review & Assign Tab -->
      <div v-if="currentTab === 3" class="tab-content">
        <h2>Review & Assign</h2>
        
        <!-- Summary of Assignments with Edit Capability -->
        <div class="assignments-summary">
          <h3>Assignment Summary</h3>
          <div v-for="(member, index) in teamMembers" :key="index" class="summary-card">
            <div class="summary-header">
              <span class="member-name">{{ getUserName(member.auditor) }}</span>
              <span class="member-role">{{ member.role }}</span>
            </div>
            
            <!-- Expandable Policy Assignment Section -->
            <div class="review-section">
              <div class="review-section-header" @click="member.isReviewPolicyExpanded = !member.isReviewPolicyExpanded">
                <h4>Policy Assignment</h4>
                <div class="review-controls">
                  <button class="edit-btn" @click.stop="togglePolicyEditMode(member)">
                    <i :class="['fas', member.isPolicyEditMode ? 'fa-check' : 'fa-edit']"></i>
                    {{ member.isPolicyEditMode ? 'Save' : 'Edit' }}
                  </button>
                  <i :class="['fas', member.isReviewPolicyExpanded ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
                </div>
              </div>
              
              <div class="review-section-content" :class="{ 'collapsed': !member.isReviewPolicyExpanded }">
                <!-- Always show dynamic input components -->
                <div class="edit-view">
                  <div class="dynamic-fields-row">
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Assigned Policy</label>
                      <SelectInput
                        v-model="member.assignedPolicy"
                        :options="policies.map(p => ({ value: p.PolicyId, label: p.PolicyName }))"
                        label="Assigned Policy"
                        placeholder="Select Policy"
                        @change="onMemberPolicyChange(index)"
                      />
                    </div>
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Sub Policy</label>
                      <SelectInput
                        v-model="member.assignedSubPolicy"
                        :options="getMemberSubpolicies(index).map(sp => ({ value: sp.SubPolicyId, label: sp.SubPolicyName }))"
                        label="Sub Policy"
                        placeholder="Select Sub Policy"
                        @change="onSubPolicyChange(index)"
                      />
                    </div>
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Reviewer</label>
                      <SelectInput
                        v-model="member.reviewer"
                        :options="users.map(user => ({ value: user.UserId, label: user.UserName }))"
                        label="Reviewer"
                        placeholder="Select Reviewer"
                      />
                    </div>
                  </div>
                  <div class="compliance-preview" v-if="member.assignedPolicy">
                    <div class="preview-content">
                      <div class="compliance-count" :class="{ 'loading': complianceCountLoading[`${member.assignedPolicy}-loading`] }">
                        <span v-if="complianceCountLoading[`${member.assignedPolicy}-loading`]">Loading...</span>
                        <span v-else>Compliance Items: {{ getComplianceCount(member.assignedPolicy, member.assignedSubPolicy) }}</span>
                      </div>
                    </div>
                  </div>
                  <!-- Reports Section -->
                  <div class="reports-section">
                    <div class="reports-row">
                      <div class="reports-col">
                        <button class="reports-btn" @click="showReportsModal(member)">
                          <i class="fas fa-file-alt"></i> Manage Reports
                        </button>
                      </div>
                    </div>
                    <!-- Display Selected Reports in edit mode -->
                    <div v-if="getSelectedReportsForMember(member).length > 0" class="selected-reports">
                      <h6>Selected Reports:</h6>
                      <div class="selected-reports-list">
                        <div v-for="report in getSelectedReportsForMember(member)" 
                             :key="report.ReportId" 
                             class="selected-report-item">
                          <span class="report-title">Report #{{ report.ReportId }}</span>
                          <span class="report-info">
                            {{ report.AuditorName }} - {{ formatDate(report.CompletionDate) }}
                          </span>
                          <button class="remove-report-btn" @click="removeReport(member, report.ReportId)">
                            <i class="fas fa-times"></i>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Expandable Audit Details Section -->
            <div class="review-section">
              <div class="review-section-header" @click="member.isReviewDetailsExpanded = !member.isReviewDetailsExpanded">
                <h4>Audit Details</h4>
                <div class="review-controls">
                  <button class="edit-btn" @click.stop="toggleDetailsEditMode(member)">
                    <i :class="['fas', member.isDetailsEditMode ? 'fa-check' : 'fa-edit']"></i>
                    {{ member.isDetailsEditMode ? 'Save' : 'Edit' }}
                  </button>
                  <i :class="['fas', member.isReviewDetailsExpanded ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
                </div>
              </div>
              
              <div class="review-section-content" :class="{ 'collapsed': !member.isReviewDetailsExpanded }">
                <!-- Always show dynamic input components -->
                <div class="edit-view">
                  <div class="dynamic-fields-row">
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Audit Title</label>
                      <!-- <TextInput
                        v-model="member.auditTitle"
                        label="Audit Title"
                        placeholder="Enter audit title..."
                      /> -->
                      <input type="text" v-model="member.auditTitle" class="dynamic-input" placeholder="Enter audit title..." />

                    </div>
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Business Unit</label>
                      <div class="dynamic-desc">Mention the business unit or process area being audited.</div>
                        <!-- <TextInput
                          v-model="member.businessUnit"
                          label="Business Unit"
                          placeholder="Enter business unit..."
                        /> -->
                        <input type="text" v-model="member.businessUnit" class="dynamic-input" placeholder="Enter business unit..." />

                    </div>
                  </div>
                  <div class="dynamic-fields-row">
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Scope</label>
                      <TextareaInput
                        v-model="member.scope"
                        label="Scope"
                        placeholder="Enter scope..."
                        rows="3"
                      />
                    </div>
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Objective</label>
                      <TextareaInput
                        v-model="member.objective"
                        label="Objective"
                        placeholder="Enter objective..."
                        rows="3"
                      />
                    </div>
                  </div>
                  <div class="dynamic-fields-row">
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Type</label>
                      <SelectInput
                        v-model="member.type"
                        :options="[
                          { value: 'I', label: 'Internal' },
                          { value: 'E', label: 'External' },
                          { value: 'S', label: 'Self-Audit' }
                        ]"
                        label="Type"
                        placeholder="Select Type"
                      />
                    </div>
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Frequency</label>
                      <SelectInput
                        v-model="member.frequency"
                        :options="[
                          { value: '0', label: 'Only Once' },
                          { value: '1', label: 'Daily' },
                          { value: '60', label: 'Every 2 Months' },
                          { value: '120', label: 'Every 4 Months' },
                          { value: '182', label: 'Half Yearly' },
                          { value: '365', label: 'Yearly' },
                          { value: '365a', label: 'Annually' }
                        ]"
                        label="Frequency"
                        placeholder="Select Frequency"
                      />
                    </div>
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Due Date</label>
                      <DateInput
                        v-model="member.dueDate"
                        label="Due Date"
                        placeholder="Select due date"
                      />
                    </div>
                  </div>
                  <div class="dynamic-fields-row">
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Role</label>
                      <SelectInput
                        v-model="member.role"
                        :options="roles.map(role => ({ value: role, label: role }))"
                        label="Role"
                        placeholder="Select Role"
                      />
                    </div>
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Responsibilities</label>
                      <TextareaInput
                        v-model="member.responsibilities"
                        label="Responsibilities"
                        placeholder="Enter responsibilities..."
                        rows="3"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Navigation Buttons -->
      <div class="tab-navigation">
        <button 
          v-if="currentTab > 0" 
          class="nav-button prev" 
          @click="currentTab--"
        >
          Previous
    </button>
        <button 
          v-if="currentTab < tabs.length - 1" 
          class="nav-button next" 
          @click="currentTab++"
          :disabled="!canProceed"
        >
          Next
        </button>
          <button 
          v-if="currentTab === tabs.length - 1" 
          class="nav-button assign" 
          @click="submitAudit"
          :disabled="!canAssign || assigning"
        >
          {{ assigning ? 'Assigning...' : 'Assign Audit' }}
        </button>
      </div>
    </div>

    <!-- Reports Modal -->
    <div v-if="showingReportsModal" class="modal-overlay">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Select Reports</h2>
          <button class="close-btn" @click="closeReportsModal">&times;</button>
        </div>
        
        <div class="modal-body">
          <div v-if="loadingReports" class="loading">
            Loading reports...
          </div>
          <div v-else-if="reportsError" class="error-message">
            {{ reportsError }}
          </div>
          <div v-else-if="availableReports.length === 0" class="no-reports">
            No reports available for this selection.
          </div>
          <div v-else class="reports-list">
            <div v-for="report in availableReports" :key="report.ReportId" class="report-item">
              <label class="report-label">
                <input 
                  type="checkbox" 
                  :value="report.ReportId" 
                  v-model="selectedReports"
                >
                <div class="report-info">
                  <div class="report-title">Report #{{ report.ReportId }}</div>
                  <div class="report-details">
                    <span>{{ report.AuditorName }}</span>
                    <span>{{ formatDate(report.CompletionDate) }}</span>
                  </div>
                </div>
              </label>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="cancel-btn" @click="closeReportsModal">Cancel</button>
          <button 
            class="save-btn" 
            @click="saveSelectedReports"
            :disabled="selectedReports.length === 0"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import ValidationMixin from '@/mixins/ValidationMixin';
import SelectInput from '@/components/inputs/SelectInput.vue';
// import TextInput from '@/components/inputs/TextInput.vue';
import TextareaInput from '@/components/inputs/TextareaInput.vue';
import DateInput from '@/components/inputs/DateInput.vue';
import { API_ENDPOINTS } from '../../config/api.js';

export default {
  name: 'AssignAudit',
  mixins: [ValidationMixin],
  components: {
    SelectInput,
    // TextInput,
    TextareaInput,
    DateInput,
  },
  data() {
    return {
      currentTab: 0,
      tabs: [
        { name: 'Framework Selection', required: ['framework'] },
        { name: 'Team Creation', required: [] },
        { name: 'Policy Assignment', required: [] },
        { name: 'Review & Assign', required: ['scope', 'objective', 'type', 'frequency', 'dueDate'] }
      ],
      auditData: {
        framework: '',
        policy: '',
        subPolicy: '',
        auditor: '',
        role: '',
        reviewer: '',
        auditTitle: '',
        scope: '',
        objective: '',
        businessUnit: '',
        type: '',
        frequency: '',
        dueDate: '',
        responsibilities: ''
      },
      frameworks: [],
      policies: [],
      subpolicies: [],
      users: [],
      roles: [
        'Chief Audit Executive (CAE) / Audit Director',
        'Audit Manager',
        'Senior Audit Manager',
        'IT Audit Manager',
        'Operational Audit Manager',
        'Compliance Audit Manager',
        'Senior Auditor',
        'Lead Auditor',
        'Financial Auditor',
        'Operational Auditor',
        'IT Systems Auditor',
        'Staff Auditor',
        'Junior Auditor',
        'Audit Reviewer',
        'Quality Assurance Reviewer',
        'Forensic Auditor',
        'Regulatory Compliance Auditor',
        'Risk Auditor',
        'External Audit Coordinator',
        'Regulatory Examiner Liaison',
        'Audit Technology Specialist',
        'Continuous Auditing Specialist',
        'Audit Committee Secretary',
        'Board Reporting Specialist'
      ],
      assigning: false,
      teamMembers: [{
        auditor: '',
        role: '',
        responsibilities: '',
        assignedPolicy: '',
        assignedSubPolicy: '',
        memberSubpolicies: [],
        reviewer: '',
        auditTitle: '',
        scope: '',
        objective: '',
        businessUnit: '',
        type: '',
        frequency: '',
        dueDate: '',
        reports: '',
        isPolicyAssignmentExpanded: true,
        isAuditDetailsExpanded: true,
        isReviewPolicyExpanded: true,
        isReviewDetailsExpanded: true,
        isPolicyEditMode: false,
        isDetailsEditMode: false,
      }],
      memberComplianceCounts: {},
      complianceCountLoading: {},
      showingReportsModal: false,
      loadingReports: false,
      reportsError: null,
      availableReports: [],
      selectedReports: [],
      currentMember: null,
      validationErrors: {},
      fieldErrors: {},
    };
  },
  computed: {
    canProceed() {
      if (this.currentTab === 0) {
        return !!this.auditData.framework;
      }
      
      if (this.currentTab === 1) {
        return this.teamMembers.some(member => 
          member.auditor && 
          member.role && 
          member.responsibilities
        );
      }
      
      if (this.currentTab === 2) {
        return this.teamMembers.every(member =>
          member.assignedPolicy &&
          member.reviewer &&
          member.scope &&
          member.objective &&
          member.type &&
          member.frequency &&
          member.dueDate
        );
      }
      
      return true;
    },
    
    canAssign() {
      // Check if framework is selected
      if (!this.auditData.framework) {
        return false;
      }

      // Check if at least one team member exists and has all required fields
      const hasValidTeamMember = this.teamMembers.some(member => {
        const hasBasicInfo = member.auditor && 
                           member.role && 
                           member.responsibilities;
                           
        const hasAssignmentInfo = member.assignedPolicy && 
                                member.reviewer;
                                
        const hasAuditDetails = member.scope && 
                              member.objective && 
                              member.type && 
                              member.frequency && 
                              member.dueDate;
                              
        return hasBasicInfo && hasAssignmentInfo && hasAuditDetails;
      });

      return hasValidTeamMember;
    },
    getFieldError() {
      return (fieldName, memberIndex = null) => {
        if (memberIndex !== null && this.validationErrors.teamMembers) {
          return this.validationErrors.teamMembers[memberIndex]?.[fieldName];
        }
        return this.validationErrors[fieldName];
      };
    }
  },
  methods: {
    async fetchFrameworks() {
      try {
        const res = await axios.get('http://15.207.108.158:8000/api/frameworks/');
        this.frameworks = res.data;
      } catch (e) {
        console.error('Error fetching frameworks:', e);
        this.frameworks = [];
      }
    },
    async fetchUsers() {
      try {
        const res = await axios.get('http://15.207.108.158:8000/api/users/');
        this.users = res.data;
      } catch (e) {
        console.error('Error fetching users:', e);
        this.users = [];
      }
    },
    async onFrameworkChange() {
      this.auditData.policy = '';
      this.auditData.subPolicy = '';
      this.policies = [];
      this.subpolicies = [];
      if (this.auditData.framework) {
      try {
          const res = await axios.get('http://15.207.108.158:8000/api/policies/', { 
            params: { framework_id: this.auditData.framework } 
          });
          this.policies = res.data;
      } catch (e) {
          console.error('Error fetching policies:', e);
          this.policies = [];
        }
      }
    },
    async onPolicyChange() {
      this.auditData.subPolicy = '';
      this.subpolicies = [];
      if (this.auditData.policy) {
      try {
          const res = await axios.get('http://15.207.108.158:8000/api/subpolicies/', { 
            params: { policy_id: this.auditData.policy } 
        });
          this.subpolicies = res.data;
        } catch (e) {
          console.error('Error fetching subpolicies:', e);
          this.subpolicies = [];
        }
      }
    },
    addTeamMember() {
      this.teamMembers.push({
        auditor: '',
        role: '',
        responsibilities: '',
        assignedPolicy: '',
        assignedSubPolicy: '',
        memberSubpolicies: [],
        reviewer: '',
        auditTitle: '',
        scope: '',
        objective: '',
        businessUnit: '',
        type: '',
        frequency: '',
        dueDate: '',
        reports: '',
        isPolicyAssignmentExpanded: true,
        isAuditDetailsExpanded: true,
        isReviewPolicyExpanded: true,
        isReviewDetailsExpanded: true,
        isPolicyEditMode: false,
        isDetailsEditMode: false,
      });
    },
    removeTeamMember(index) {
      this.teamMembers.splice(index, 1);
    },
    validateForm() {
      this.validationErrors = {};
      this.fieldErrors = {};
      
      // Framework validation
      const frameworkError = this.validateId(this.auditData.framework, 'Framework');
      if (frameworkError) {
        this.validationErrors.framework = frameworkError;
      }

      // Team members validation
      const teamErrors = [];
      this.teamMembers.forEach((member, index) => {
        const memberErrors = this.validateTeamMember(member);
        if (memberErrors) {
          teamErrors[index] = memberErrors;
        }
      });

      if (teamErrors.length > 0) {
        this.validationErrors.teamMembers = teamErrors;
      }

      return Object.keys(this.validationErrors).length === 0;
    },
    async submitAudit() {
      if (this.assigning) return;
      
      // Validate form before submission
      // if (!this.validateForm()) {
      //   // Show error message
      //   this.$popup.error('Please fix the validation errors before submitting.');
      //   return;
      // }
      
      try {
        this.assigning = true;
        
        // Get the first team member to use as template for common fields
        const templateMember = this.teamMembers[0];
        
        // Create payload with team member IDs and common fields
        const payload = {
          title: templateMember.auditTitle,
          scope: templateMember.scope,
          objective: templateMember.objective,
          business_unit: templateMember.businessUnit,
          role: templateMember.role,
          responsibility: templateMember.responsibilities,
          team_members: this.teamMembers.map(member => member.auditor),
          reviewer: templateMember.reviewer,
          framework_id: this.auditData.framework,
          policy_id: templateMember.assignedPolicy || null,
          subpolicy_id: templateMember.assignedSubPolicy || null,
          due_date: templateMember.dueDate,
          frequency: templateMember.frequency,
          audit_type: templateMember.type,
          reports: templateMember.reports || ''
        };

        const response = await axios.post('http://15.207.108.158:8000/api/create-audit/', payload);
        
        if (response.data.audits_created > 0) {
          this.$popup.success(`Successfully created ${response.data.audits_created} audit(s)`);
          this.resetForm();
        } else {
          throw new Error('No audits were created');
        }
        
      } catch (error) {
        const errorMessage = error.response?.data?.error || 'Please try again.';
        if (error.response?.data?.details) {
          // Handle validation errors from backend
          this.handleBackendValidationErrors(error.response.data.details);
        }
        this.$popup.error('Error assigning audits: ' + errorMessage);
        console.error('Error in submitAudit:', error);
      } finally {
        this.assigning = false;
      }
    },
    handleBackendValidationErrors(details) {
      try {
        const errors = JSON.parse(details);
        this.validationErrors = errors;
      } catch (e) {
        // If not JSON, show as general error
        this.validationErrors.general = details;
      }
    },
    resetForm() {
      this.auditData = {
        framework: '',
      };
      this.teamMembers = [{
        auditor: '',
        role: '',
        responsibilities: '',
        assignedPolicy: '',
        assignedSubPolicy: '',
        memberSubpolicies: [],
        reviewer: '',
        auditTitle: '',
        scope: '',
        objective: '',
        businessUnit: '',
        type: '',
        frequency: '',
        dueDate: '',
        reports: '',
        isPolicyAssignmentExpanded: true,
        isAuditDetailsExpanded: true,
        isReviewPolicyExpanded: true,
        isReviewDetailsExpanded: true,
        isPolicyEditMode: false,
        isDetailsEditMode: false,
      }];
      this.currentTab = 0;
    },
    getUserName(userId) {
      const user = this.users.find(u => u.UserId === userId);
      return user ? user.UserName : '';
    },
    getPolicyName(policyId) {
      const policy = this.policies.find(p => p.PolicyId === policyId);
      return policy ? policy.PolicyName : 'Not Assigned';
    },
    getSubPolicyName(subPolicyId) {
      const member = this.teamMembers.find(m => m.memberSubpolicies.some(sp => sp.SubPolicyId === subPolicyId));
      if (member) {
        const subPolicy = member.memberSubpolicies.find(sp => sp.SubPolicyId === subPolicyId);
        return subPolicy ? subPolicy.SubPolicyName : 'Not Assigned';
      }
      return 'Not Assigned';
    },
    async onMemberPolicyChange(memberIndex) {
      const member = this.teamMembers[memberIndex];
      member.assignedSubPolicy = '';
      member.memberSubpolicies = [];

      if (member.assignedPolicy) {
        try {
          this.complianceCountLoading = {
            ...this.complianceCountLoading,
            [`${member.assignedPolicy}-loading`]: true
          };

          const response = await axios.get('http://15.207.108.158:8000/api/subpolicies/', {
            params: { policy_id: member.assignedPolicy }
          });
          
          member.memberSubpolicies = response.data;
          await this.fetchComplianceCount(memberIndex);
          
        } catch (error) {
          console.error('Error in onMemberPolicyChange:', error);
        } finally {
          this.complianceCountLoading = {
            ...this.complianceCountLoading,
            [`${member.assignedPolicy}-loading`]: false
          };
        }
      }
    },
    async fetchComplianceCount(memberIndex) {
      const member = this.teamMembers[memberIndex];
      if (!member || !member.assignedPolicy) return;

      try {
        const countResponse = await axios.get('http://15.207.108.158:8000/api/compliance-count/', {
          params: {
            policy_id: member.assignedPolicy,
            subpolicy_id: member.assignedSubPolicy || ''
          }
        });
        
        const key = `${member.assignedPolicy}-${member.assignedSubPolicy || ''}`;
        this.memberComplianceCounts = {
          ...this.memberComplianceCounts,
          [key]: countResponse.data.count || 0
        };
        
      } catch (error) {
        console.error('Error fetching compliance count:', error);
        const key = `${member.assignedPolicy}-${member.assignedSubPolicy || ''}`;
        this.memberComplianceCounts = {
          ...this.memberComplianceCounts,
          [key]: 0
        };
      }
    },
    async onSubPolicyChange(memberIndex) {
      const member = this.teamMembers[memberIndex];
      if (!member || !member.assignedPolicy) return;

      try {
        this.complianceCountLoading = {
          ...this.complianceCountLoading,
          [`${member.assignedPolicy}-loading`]: true
        };

        await this.fetchComplianceCount(memberIndex);
      } catch (error) {
        console.error('Error in onSubPolicyChange:', error);
      } finally {
        this.complianceCountLoading = {
          ...this.complianceCountLoading,
          [`${member.assignedPolicy}-loading`]: false
        };
      }
    },
    getMemberSubpolicies(memberIndex) {
      return this.teamMembers[memberIndex].memberSubpolicies;
    },
    getComplianceCount(policyId, subPolicyId) {
      if (!policyId) return 0;
      const key = `${policyId}-${subPolicyId || ''}`;
      return this.memberComplianceCounts[key] || 0;
    },
    async showReportsModal(member) {
      this.currentMember = member;
      this.showingReportsModal = true;
      this.loadingReports = true;
      this.reportsError = null;
      this.selectedReports = [];
      
      try {
        const params = new URLSearchParams({
          framework_id: this.auditData.framework,
          policy_id: member.assignedPolicy || '',
          subpolicy_id: member.assignedSubPolicy || ''
        });
        
        const response = await axios.get('http://15.207.108.158:8000/api/audit-reports/check/', { params });
        this.availableReports = response.data.reports || [];
      } catch (error) {
        console.error('Error fetching reports:', error);
        this.reportsError = 'Failed to load reports. Please try again.';
      } finally {
        this.loadingReports = false;
      }
    },
    
    closeReportsModal() {
      this.showingReportsModal = false;
      this.currentMember = null;
      this.selectedReports = [];
      this.availableReports = [];
      this.reportsError = null;
    },
    
    async saveSelectedReports() {
      try {
        if (this.selectedReports.length === 0) return;

        const params = new URLSearchParams();
        params.append('report_ids', this.selectedReports.join(','));
        
        const response = await axios.get('http://15.207.108.158:8000/api/audit-reports/details/', { params });
        const reportDetails = response.data.reports;

        const reportsData = {
          reports: reportDetails.map((report, index) => ({
            [`Report_${index + 1}`]: {
              ReportId: report.report_id,
              Report: report.report,
              AuditorName: report.auditor_name,
              CompletionDate: report.completion_date,
              PolicyId: this.currentMember.assignedPolicy || null,
              SubPolicyId: this.currentMember.assignedSubPolicy || null,
              FrameworkId: this.auditData.framework
            }
          }))
        };

        this.currentMember.reports = JSON.stringify(reportsData);
        this.closeReportsModal();
      } catch (error) {
        console.error('Error saving reports:', error);
        this.$popup.error('Error saving reports. Please try again.');
      }
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      return date.toLocaleDateString();
    },

    getSelectedReportsForMember(member) {
      if (!member.reports) return [];
      try {
        const reportsData = JSON.parse(member.reports);
        return reportsData.reports.map((reportObj, index) => {
          const reportKey = `Report_${index + 1}`;
          return {
            ReportId: reportObj[reportKey].ReportId,
            Report: reportObj[reportKey].Report,
            AuditorName: reportObj[reportKey].AuditorName || 'Unknown',
            CompletionDate: reportObj[reportKey].CompletionDate
          };
        });
      } catch (error) {
        console.error('Error parsing reports:', error);
        return [];
      }
    },

    removeReport(member, reportId) {
      try {
        if (!member.reports) return;
        
        const reportsData = JSON.parse(member.reports);
        const updatedReports = reportsData.reports.filter(reportObj => {
          const reportKey = Object.keys(reportObj)[0];
          return reportObj[reportKey].ReportId !== reportId;
        });
        
        reportsData.reports = updatedReports;
        member.reports = JSON.stringify(reportsData);
      } catch (error) {
        console.error('Error removing report:', error);
      }
    },

    toggleSection(member, section) {
      if (section === 'policyAssignment') {
        member.isPolicyAssignmentExpanded = !member.isPolicyAssignmentExpanded;
      } else if (section === 'auditDetails') {
        member.isAuditDetailsExpanded = !member.isAuditDetailsExpanded;
      }
    },
    
    // New methods for toggling edit modes
    togglePolicyEditMode(member) {
      member.isPolicyEditMode = !member.isPolicyEditMode;
    },
    
    toggleDetailsEditMode(member) {
      member.isDetailsEditMode = !member.isDetailsEditMode;
    },
    
    // Helper methods for read-only display
    getAuditTypeLabel(type) {
      switch(type) {
        case 'I': return 'Internal';
        case 'E': return 'External';
        case 'S': return 'Self-Audit';
        default: return type || 'Not specified';
      }
    },
    
    getFrequencyLabel(frequency) {
      switch(frequency) {
        case '0': return 'Only Once';
        case '1': return 'Daily';
        case '60': return 'Every 2 Months';
        case '120': return 'Every 4 Months';
        case '182': return 'Half Yearly';
        case '365': return 'Yearly';
        case '365a': return 'Annually';
        default: return frequency || 'Not specified';
      }
    },
  },
  watch: {
    'teamMembers': {
      deep: true,
      handler(newVal) {
        newVal.forEach((member, index) => {
          if (member.assignedSubPolicy) {
            this.onSubPolicyChange(index);
          }
        });
      }
    }
  },
  mounted() {
    this.fetchFrameworks();
    this.fetchUsers();
  }
};
</script>

<style scoped>
@import './AssignAudit.css';
.dynamic-row-block {
  margin-bottom: 2.5rem;
  padding: 1.2rem 1.2rem 1.5rem 1.2rem;
  background: #f9fafe;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(37,99,235,0.04);
}
.dynamic-desc {
  font-size: 0.92rem;
  color: #888;
  margin-bottom: 0.2rem;
  margin-top: -0.2rem;
  line-height: 1.3;
}
.dynamic-textarea {
  min-height: 60px;
  resize: vertical;
  font-size: 1rem;
  padding: 10px;
}
.assign-audit-btn {
  margin-top: 1rem;
  padding: 0.8rem 1.5rem;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}
.assign-audit-btn:hover {
  background: #1741a6;
}
.additional-fields {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}
.compliance-scope-desc {
  font-size: 0.8rem;
  color: #888;
  margin-top: 0.5rem;
  line-height: 1.3;
}
.reports-row {
  display: flex;
  justify-content: flex-start;
  margin: 1rem 0;
  padding-top: 0.5rem;
}
.reports-btn {
  padding: 0.6rem 2rem;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  height: 40px;
  white-space: nowrap;
}
.reports-btn:hover {
  background: #1d4ed8;
  transform: translateY(-1px);
}
.reports-btn:active {
  transform: translateY(0);
}
.reports-col {
  flex: 0 0 auto;
  min-width: auto;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  margin-bottom: 8px;
}
.reports-btn {
  padding: 0.5rem 1.5rem;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  height: 38px;
  white-space: nowrap;
}
.reports-btn:hover {
  background: #1d4ed8;
  transform: translateY(-1px);
}
.reports-btn:active {
  transform: translateY(0);
}
@media (max-width: 900px) {
  .reports-col {
    margin-top: 1rem;
    align-items: flex-start;
  }
  
  .reports-btn {
    width: 100%;
  }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
}

.modal-body {
  padding: 1rem;
  overflow-y: auto;
  flex: 1;
}

.reports-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.report-item {
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  transition: all 0.2s;
}

.report-item:hover {
  background: #f9fafb;
}

.report-label {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  cursor: pointer;
}

.report-info {
  flex: 1;
}

.report-title {
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.report-details {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.modal-footer {
  padding: 1rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.cancel-btn, .save-btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  color: #374151;
}

.save-btn {
  background: #2563eb;
  border: none;
  color: white;
}

.save-btn:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}

.loading, .no-reports {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.compliance-count {
  font-size: 1.1rem;
  font-weight: 500;
  color: #2563eb;
}

.compliance-count.loading {
  color: #6b7280;
  font-style: italic;
}

.loading-spinner {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #2563eb;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 0.5rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.selected-reports {
  margin-top: 1rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.selected-reports h6 {
  margin: 0 0 0.75rem 0;
  color: #1e293b;
  font-size: 0.9rem;
  font-weight: 600;
}

.selected-reports-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.selected-report-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
}

.report-title {
  font-weight: 500;
  color: #1e293b;
}

.report-info {
  color: #64748b;
  font-size: 0.9rem;
}

.remove-report-btn {
  background: none;
  border: none;
  color: #ef4444;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.remove-report-btn:hover {
  background: #fee2e2;
}

.collapsible-section {
  margin-bottom: 1.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.section-header:hover {
  background: #f1f5f9;
}

.section-header h5 {
  margin: 0;
  font-size: 1.1rem;
  color: #1e293b;
}

.section-header i {
  color: #64748b;
  transition: transform 0.2s ease;
}

.section-content {
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-top: none;
  border-radius: 0 0 8px 8px;
  transition: all 0.3s ease;
  overflow: hidden;
  max-height: 2000px; /* Adjust based on your content */
}

.section-content.collapsed {
  max-height: 0;
  padding: 0;
  border: none;
  opacity: 0;
}

.team-assignment-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.member-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.member-header h4 {
  margin: 0;
  color: #1e293b;
  font-size: 1.2rem;
}

.error-message {
  color: #dc2626;
  font-size: 0.875rem;
  margin-top: 0.25rem;
  margin-bottom: 0.5rem;
}

.dynamic-input.has-error {
  border-color: #dc2626;
}

.validation-summary {
  margin: 1rem 0;
  padding: 1rem;
  background-color: #fee2e2;
  border: 1px solid #ef4444;
  border-radius: 0.375rem;
}

.validation-summary h3 {
  color: #dc2626;
  margin-top: 0;
  margin-bottom: 0.5rem;
}

.validation-summary ul {
  margin: 0;
  padding-left: 1.5rem;
}

.validation-summary li {
  color: #b91c1c;
  margin-bottom: 0.25rem;
}
</style>
