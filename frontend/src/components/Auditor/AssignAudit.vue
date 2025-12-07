<template>
  <div class="assign-audit-page">
    <div class="audit-content">
      <h1 class="audit-title">Audit Assignment</h1>

      <!-- Tab Navigation -->
      <div class="audit-tabs">
        <button 
          v-for="(tab, index) in tabs" 
          :key="index"
          :class="['tab-button', { active: currentTab === index, disabled: !isTabEnabled(index) }]"
          :disabled="!isTabEnabled(index)"
          @click="isTabEnabled(index) && (currentTab = index)"
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
            <div class="narrow-dropdown">
              <CustomDropdown
                v-model="auditData.framework"
                :config="{
                  name: 'Framework',
                  label: 'Framework',
                  values: frameworks.map(fw => ({ value: fw.FrameworkId, label: fw.FrameworkName })),
                  defaultValue: 'Select Framework'
                }"
                @change="onFrameworkChange"
              />
            </div>
            <div v-if="auditData.framework && !auditData.policy" class="compliance-scope-desc">
              Will include permanent compliances from all policies and subpolicies under this framework
            </div>
          </div>
          <div class="dynamic-field-col">
            <label class="dynamic-label">Audit Type</label>
            <div class="dynamic-desc">Select whether the audit is Internal, External, Self-Audit, or AI-powered Audit.</div>
            <SelectInput
              v-model="auditData.type"
              :options="[
                { value: 'I', label: 'Internal' },
                { value: 'E', label: 'External' },
                { value: 'S', label: 'Self-Audit' },
                { value: 'AI', label: 'AI Audit' }
              ]"
              label="Type"
              placeholder="Select Type"
              @change="onAuditTypeChange"
            />
          </div>
        </div>
        
      </div>


      <!-- Team Creation Tab (Internal/External/Self Audits Only) -->
      <div v-if="currentTab === 1 && auditData.type !== 'AI'" class="tab-content">
        <h2>Team Creation</h2>
        <p class="tab-description">Create your audit team by adding team members and defining their roles and responsibilities.</p>
        
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
              <div class="field-with-ai">
                <CustomDropdown
                  v-model="member.auditor"
                  :config="{
                    name: 'Auditor',
                    label: 'Auditor',
                    values: filteredUsers.map(user => ({ value: user.UserId, label: user.UserName })),
                    defaultValue: 'Select Auditor'
                  }"
                  :showSearchBar="true"
                  :error="getFieldError('auditor', index)"
                />
                <button 
                  type="button" 
                  class="ai-recommendation-btn" 
                  @click="getAIRecommendations('auditor', index)"
                  :disabled="isLoadingAuditorAI || !isAuditorAIEnabled(index)"
                  :title="isAuditorAIEnabled(index) ? 'Get AI Recommendations' : 'Please select a policy first'"
                  @mouseenter="checkAuditorButtonState(index)"
                  :style="{ 
                    opacity: (isLoadingAuditorAI || !isAuditorAIEnabled(index)) ? 0.5 : 1,
                    cursor: (isLoadingAuditorAI || !isAuditorAIEnabled(index)) ? 'not-allowed' : 'pointer'
                  }"
                >
                  <i class="fas fa-lightbulb"></i>
                  <i v-if="isLoadingAuditorAI" class="fas fa-spinner fa-spin"></i>
                </button>
              </div>
            </div>
            <div class="dynamic-field-col">
              <label class="dynamic-label">Role</label>
              <div class="dynamic-desc">Select the role of the auditor in this audit.</div>
              <CustomDropdown
                v-model="member.role"
                :config="{
                  name: 'Role',
                  label: 'Role',
                  values: roles.map(role => ({ value: role, label: role })),
                  defaultValue: 'Select Role'
                }"
                :showSearchBar="true"
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
            <i class="fas fa-trash"></i> Remove
          </button>
        </div>
      </div>

      <!-- Policy Selection Tab (AI Audits Only) -->
      <div v-if="currentTab === 1 && auditData.type === 'AI'" class="tab-content">
        <h2>Policy Selection</h2>
        <p class="tab-description">Select the policy that will be audited. This determines the compliance requirements and scope of the audit.</p>
        
        <div class="policy-selection-section">
          <div class="dynamic-fields-row">
            <div class="dynamic-field-col">
              <label class="dynamic-label">Select Policy</label>
              <div class="dynamic-desc">Choose the policy to be audited. This will determine the compliance requirements.</div>
              <CustomDropdown
                v-model="auditData.policy"
                :config="{
                  name: 'Policy',
                  label: 'Policy',
                  values: policies.map(p => ({ value: p.PolicyId, label: p.PolicyName })),
                  defaultValue: 'Select Policy'
                }"
                :showSearchBar="true"
                @change="onPolicyChange" 
              />
            </div>
            <div class="dynamic-field-col">
              <label class="dynamic-label">Sub Policy <span v-if="auditData.type === 'AI'" class="required-asterisk">*</span></label>
              <div class="dynamic-desc">
                <span v-if="auditData.type === 'AI'">Select a specific sub-policy for AI compliance analysis.</span>
                <span v-else>Select specific sub-policy if applicable.</span>
              </div>
              <CustomDropdown
                v-model="auditData.subPolicy"
                :config="{
                  name: 'Sub Policy',
                  label: 'Sub Policy',
                  values: subpolicies.map(sp => ({ 
                    value: sp.id, 
                    label: sp.name.replace(/\s*\(\d+\)$/, '') // Remove numbers in parentheses at the end
                  })),
                  defaultValue: 'Select Sub Policy'
                }"
                :disabled="!auditData.policy"
                @change="onMainSubPolicyChange"
              />
            </div>
          </div>
          
          <!-- Policy Information Display -->
          <div v-if="selectedPolicy" class="policy-info-card">
            <h4>{{ selectedPolicy.PolicyName }}</h4>
            <p class="policy-description">{{ selectedPolicy.PolicyDescription }}</p>
            <div class="policy-meta">
              <span class="policy-category">{{ selectedPolicy.PolicyCategory }}</span>
              <span class="policy-type">{{ selectedPolicy.PolicyType }}</span>
              <span class="policy-status">{{ selectedPolicy.Status }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Policy Assignment Tab (Internal/External/Self Audits Only) -->
      <div v-if="currentTab === 2 && auditData.type !== 'AI'" class="tab-content">
        <h2>Policy Assignment & Audit Details</h2>
        <p class="tab-description">Assign policies to team members and configure audit details.</p>

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
                    <CustomDropdown
                      v-model="member.assignedPolicy"
                      :config="{
                        name: 'Assigned Policy',
                        label: 'Assigned Policy',
                        values: policies.map(p => ({ value: p.PolicyId, label: p.PolicyName })),
                        defaultValue: 'Select Policy'
                      }"
                      :showSearchBar="true"
                      :error="getFieldError('assignedPolicy', index)"
                      @change="onMemberPolicyChange(index)"
                    />
                  </div>
                  <div class="dynamic-field-col">
                    <label class="dynamic-label">Sub Policy</label>
                    <div class="dynamic-desc">Select specific sub policy if applicable.</div>
                    <CustomDropdown
                      v-model="member.assignedSubPolicy"
                      :config="{
                        name: 'Sub Policy',
                        label: 'Sub Policy',
                        values: getMemberSubpolicies(index).map(sp => ({ value: sp.SubPolicyId, label: sp.SubPolicyName })),
                        defaultValue: 'Select Sub Policy'
                      }"
                      :showSearchBar="true"
                      @change="onSubPolicyChange(index)"
                    />
                  </div>
                  <div class="dynamic-field-col">
                    <label class="dynamic-label">Reviewer</label>
                    <div class="dynamic-desc">Choose the reviewer who will review this audit.</div>
                    <div class="field-with-ai">
                      <CustomDropdown
                        v-model="member.reviewer"
                        :config="{
                          name: 'Reviewer',
                          label: 'Reviewer',
                          values: filteredUsers.map(user => ({ value: user.UserId, label: user.UserName })),
                          defaultValue: 'Select Reviewer'
                        }"
                        :showSearchBar="true"
                        :error="getFieldError('reviewer', index)"
                      />
                      <button 
                        type="button" 
                        class="ai-recommendation-btn" 
                        @click="getAIRecommendations('reviewer', index)"
                        :disabled="isLoadingReviewerAI || !isReviewerAIEnabled(index)"
                        :title="isReviewerAIEnabled(index) ? 'Get AI Recommendations' : 'Please fill Audit Title, Business Unit, Scope, and Objective first'"
                        @mouseenter="checkReviewerButtonState(index)"
                        :style="{ 
                          opacity: (isLoadingReviewerAI || !isReviewerAIEnabled(index)) ? 0.5 : 1,
                          cursor: (isLoadingReviewerAI || !isReviewerAIEnabled(index)) ? 'not-allowed' : 'pointer'
                        }"
                      >
                        <i class="fas fa-lightbulb"></i>
                        <i v-if="isLoadingReviewerAI" class="fas fa-spinner fa-spin"></i>
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Reports Section -->
                <div class="reports-section">
                  <div class="reports-row">
                    <div class="reports-col">
                      <button class="reports-btn" @click="showReportsModal(member)">
                        <i class="fas fa-file-alt"></i> Report Access
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
                    <input type="text" v-model="member.auditTitle" class="dynamic-input" placeholder="Enter audit title..." />
                  </div>
                  <div class="dynamic-field-col">
                    <label class="dynamic-label">Business Unit</label>
                    <div class="dynamic-desc">Select one or more business units for this audit.</div>
                    <div class="multi-select-dropdown">
                      <div class="multi-select-input" @click="toggleBusinessUnitDropdown(member)">
                        <div class="selected-items">
                          <span v-if="member.businessUnits.length === 0" class="placeholder">
                            Select business units or type to add new...
                          </span>
                          <span v-for="unit in member.businessUnits" :key="unit" class="selected-item">
                            {{ unit }}
                            <i class="fas fa-times" @click.stop="removeBusinessUnit(member, unit)"></i>
                          </span>
                        </div>
                        <i class="fas fa-chevron-down dropdown-arrow" :class="{ 'rotated': member.showBusinessUnitDropdown }"></i>
                      </div>
                      <div v-if="member.showBusinessUnitDropdown" class="dropdown-panel">
                        <div class="search-box">
                          <input 
                            type="text" 
                            v-model="businessUnitSearchTerm" 
                            @input="filterBusinessUnits(member)"
                            placeholder="Search business units..."
                            class="search-input"
                          />
                        </div>
                        <div class="options-list">
                          <div v-if="member.filteredBusinessUnits && member.filteredBusinessUnits.length === 0 && !businessUnitSearchTerm" class="no-options">
                            No business units available
                          </div>
                          <div v-for="unit in member.filteredBusinessUnits || []" :key="unit" class="option-item" @click="toggleBusinessUnit(member, unit)">
                            <input type="checkbox" :checked="member.businessUnits.includes(unit)" />
                            <span>{{ unit }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
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

      <!-- Auditor Assignment Tab (AI Audits Only) -->
      <div v-if="currentTab === 2 && auditData.type === 'AI'" class="tab-content">
        <h2>Auditor Assignment & Audit Details</h2>

        <!-- Team Assignments Section -->
        <div class="team-assignments-section">
          <div v-for="(member, index) in teamMembers" :key="index" class="team-assignment-card">
            <div class="member-header">
              <h4 v-if="auditData.type === 'AI'">AI Audit - {{ member.role }}</h4>
              <h4 v-else>{{ getUserName(member.auditor) || 'Team Member' }} - {{ member.role }}</h4>
            </div>
            
            <!-- Policy Assignment Section -->
            <div class="collapsible-section">
              <div class="section-header" @click="toggleSection(member, 'policyAssignment')">
                <h5>Policy Assignment</h5>
                <i :class="['fas', member.isPolicyAssignmentExpanded ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
              </div>
              
              <div class="section-content" :class="{ 'collapsed': !member.isPolicyAssignmentExpanded }">
                <!-- Policy Information Display (Read-only) -->
                <div class="policy-info-display">
                  <h4>Selected Policy Information</h4>
                  <div class="policy-details">
                    <div class="policy-item">
                      <span class="policy-label">Policy:</span>
                      <span class="policy-value">{{ selectedPolicy?.PolicyName || 'No policy selected' }}</span>
                    </div>
                    <div class="policy-item" v-if="auditData.subPolicy">
                      <span class="policy-label">Sub Policy:</span>
                      <span class="policy-value">{{ selectedSubPolicy?.name || 'No sub-policy selected' }}</span>
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
                    <div class="dynamic-desc">Select one or more business units for this audit.</div>
                    <div class="multi-select-dropdown">
                      <div class="multi-select-input" @click="toggleBusinessUnitDropdown(member)">
                        <div class="selected-items">
                          <span v-if="member.businessUnits.length === 0" class="placeholder">
                            Select business units or type to add new...
                          </span>
                          <span v-for="unit in member.businessUnits" :key="unit" class="selected-item">
                            {{ unit }}
                            <i class="fas fa-times" @click.stop="removeBusinessUnit(member, unit)"></i>
                          </span>
                        </div>
                        <i class="fas fa-chevron-down dropdown-arrow" :class="{ 'rotated': member.showBusinessUnitDropdown }"></i>
                      </div>
                      <div v-if="member.showBusinessUnitDropdown" class="dropdown-panel">
                        <div class="search-box">
                          <input 
                            type="text" 
                            v-model="businessUnitSearchTerm" 
                            @input="filterBusinessUnits(member)"
                            placeholder="Search business units..."
                            class="search-input"
                          />
                        </div>
                        <div class="options-list">
                          <div v-if="member.filteredBusinessUnits && member.filteredBusinessUnits.length === 0 && !businessUnitSearchTerm" class="no-options">
                            No business units available
                          </div>
                          <div v-for="unit in member.filteredBusinessUnits || []" :key="unit" class="option-item" @click="toggleBusinessUnit(member, unit)">
                            <input type="checkbox" :checked="member.businessUnits.includes(unit)" />
                            <span>{{ unit }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
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
                        { value: 'S', label: 'Self-Audit' },
                        { value: 'AI', label: 'AI Audit' }
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

                <!-- Reviewer Selection -->
                <div class="dynamic-fields-row">
                  <div class="dynamic-field-col">
                    <label class="dynamic-label">Reviewer</label>
                    <div class="dynamic-desc">Choose the reviewer who will review this audit.</div>
                    <div class="field-with-ai">
                    <CustomDropdown
                      v-model="member.reviewer"
                      :config="{
                        name: 'Reviewer',
                        label: 'Reviewer',
                        values: users.map(user => ({ value: user.UserId, label: user.UserName })),
                        defaultValue: 'Select Reviewer'
                      }"
                      :showSearchBar="true"
                      :error="getFieldError('reviewer', index)"
                    />
                    <button 
                        type="button" 
                        class="ai-recommendation-btn" 
                        @click="getAIRecommendations('reviewer', index)"
                        :disabled="isLoadingReviewerAI || !isReviewerAIEnabled(index)"
                        :title="isReviewerAIEnabled(index) ? 'Get AI Recommendations' : 'Please fill Audit Title, Business Unit, Scope, and Objective first'"
                        @mouseenter="checkReviewerButtonState(index)"
                        :style="{ 
                          opacity: (isLoadingReviewerAI || !isReviewerAIEnabled(index)) ? 0.5 : 1,
                          cursor: (isLoadingReviewerAI || !isReviewerAIEnabled(index)) ? 'not-allowed' : 'pointer'
                        }"
                      >
                        <i class="fas fa-lightbulb"></i>
                        <i v-if="isLoadingReviewerAI" class="fas fa-spinner fa-spin"></i>
                      </button>
                    </div>
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
                    <h5>Selected Reports ({{ getSelectedReportsForMember(member).length }})</h5>
                    <div class="reports-list">
                      <div v-for="report in getSelectedReportsForMember(member)" 
                           :key="report.ReportId" 
                           class="report-item">
                        <div class="report-info">
                          <span class="report-title">Report #{{ report.ReportId }}</span>
                          <span class="report-auditor">{{ report.AuditorName }}</span>
                          <span class="report-date">{{ formatDate(report.CompletionDate) }}</span>
                        </div>
                        <button @click="removeReportFromMember(member, report.ReportId)" class="remove-report-btn">
                          <i class="fas fa-times"></i>
                        </button>
                      </div>
                    </div>
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
      <div v-if="isReviewTab" class="tab-content">
        <h2>Review & Assign</h2>
        
        <div class="review-actions">
          <button class="expand-all-btn" @click="expandAllSections">
            <i class="fas fa-expand-alt"></i> Expand All Sections
          </button>
        </div>
        
        <!-- Team Members Review -->
        <div class="team-review-section">
          <div v-for="(member, index) in teamMembers" :key="index" class="team-review-card">
            <div class="member-header">
              <h4 v-if="auditData.type === 'AI'">AI Audit - {{ member.role }}</h4>
              <h4 v-else>{{ getUserName(member.auditor) || 'Team Member' }} - {{ member.role }}</h4>
            </div>
            
            <!-- Policy Assignment Review Section -->
            <div class="collapsible-section">
              <div class="section-header" @click="toggleSection(member, 'reviewPolicy')">
                <h5>Policy Assignment</h5>
                <i :class="['fas', member.isReviewPolicyExpanded ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
              </div>
              
              <div class="section-content" :class="{ 'collapsed': !member.isReviewPolicyExpanded }">
                <div class="review-content" v-if="!member.isPolicyEditMode">
                  <div class="review-item">
                    <span class="review-label">Assigned Policy:</span>
                    <span class="review-value">{{ getPolicyName(member.assignedPolicy) }}</span>
                  </div>
                  <div class="review-item" v-if="member.assignedSubPolicy">
                    <span class="review-label">Sub Policy:</span>
                    <span class="review-value">{{ getSubPolicyName(member.assignedSubPolicy) }}</span>
                  </div>
                  <div class="review-item">
                    <span class="review-label">Reviewer:</span>
                    <span class="review-value">{{ getUserName(member.reviewer) }}</span>
                  </div>
                  
                  <!-- Selected Reports Display -->
                  <div class="review-item" v-if="getSelectedReportsForMember(member).length > 0">
                    <span class="review-label">Attached Reports:</span>
                    <div class="review-reports-list">
                      <div v-for="report in getSelectedReportsForMember(member)" 
                           :key="report.ReportId" 
                           class="review-report-item">
                        <span class="report-title">Report #{{ report.ReportId }}</span>
                        <span class="report-info">
                          {{ report.AuditorName }} - {{ formatDate(report.CompletionDate) }}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <button class="edit-section-btn" @click="togglePolicyEditMode(member)">
                    <i class="fas fa-edit"></i> Edit
                  </button>
                </div>
                
                <!-- Edit Mode for Policy Assignment -->
                <div class="edit-content" v-if="member.isPolicyEditMode">
                  <!-- Policy Information Display (Read-only) -->
                  <div class="policy-info-display">
                    <h4>Selected Policy Information</h4>
                    <div class="policy-details">
                      <div class="policy-item">
                        <span class="policy-label">Policy:</span>
                        <span class="policy-value">{{ getPolicyName(member.assignedPolicy) || 'No policy selected' }}</span>
                      </div>
                      <div class="policy-item" v-if="member.assignedSubPolicy">
                        <span class="policy-label">Sub Policy:</span>
                        <span class="policy-value">{{ getSubPolicyName(member.assignedSubPolicy) || 'No sub-policy selected' }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Note: Reviewer selection moved to Audit Details section -->
                  
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
                  
                  <button class="save-section-btn" @click="togglePolicyEditMode(member)">
                    <i class="fas fa-save"></i> Save
                  </button>
                </div>
              </div>
            </div>

            <!-- Audit Details Review Section -->
            <div class="collapsible-section">
              <div class="section-header" @click="toggleSection(member, 'reviewDetails')">
                <h5>Audit Details</h5>
                <i :class="['fas', member.isReviewDetailsExpanded ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
              </div>
              
              <div class="section-content" :class="{ 'collapsed': !member.isReviewDetailsExpanded }">
                <div class="review-content" v-if="!member.isDetailsEditMode">
                  <div class="review-item">
                    <span class="review-label">Audit Title:</span>
                    <span class="review-value">{{ member.auditTitle || 'Not specified' }}</span>
                  </div>
                  <div class="review-item">
                    <span class="review-label">Business Unit:</span>
                    <span class="review-value">{{ member.businessUnit || 'Not specified' }}</span>
                  </div>
                  <div class="review-item">
                    <span class="review-label">Scope:</span>
                    <span class="review-value">{{ member.scope }}</span>
                  </div>
                  <div class="review-item">
                    <span class="review-label">Objective:</span>
                    <span class="review-value">{{ member.objective }}</span>
                  </div>
                  <div class="review-item">
                    <span class="review-label">Type:</span>
                    <span class="review-value">{{ getAuditTypeLabel(member.type) }}</span>
                  </div>
                  <div class="review-item">
                    <span class="review-label">Frequency:</span>
                    <span class="review-value">{{ getFrequencyLabel(member.frequency) }}</span>
                  </div>
                  <div class="review-item">
                    <span class="review-label">Due Date:</span>
                    <span class="review-value">{{ formatDate(member.dueDate) }}</span>
                  </div>
                  
                  <button class="edit-section-btn" @click="toggleDetailsEditMode(member)">
                    <i class="fas fa-edit"></i> Edit
                  </button>
                </div>
                
                <!-- Edit Mode for Audit Details -->
                <div class="edit-content" v-if="member.isDetailsEditMode">
                  <div class="dynamic-fields-row">
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Audit Title</label>
                      <input type="text" v-model="member.auditTitle" class="dynamic-input" placeholder="Enter audit title..." />
                    </div>
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Business Unit</label>
                      <div class="dynamic-desc">Select one or more business units for this audit.</div>
                      <div class="multi-select-dropdown">
                        <div class="multi-select-input" @click="toggleBusinessUnitDropdown(member)">
                          <div class="selected-items">
                            <span v-if="member.businessUnits.length === 0" class="placeholder">
                              Select business units or type to add new...
                            </span>
                            <span v-for="unit in member.businessUnits" :key="unit" class="selected-item">
                              {{ unit }}
                              <i class="fas fa-times" @click.stop="removeBusinessUnit(member, unit)"></i>
                            </span>
                          </div>
                          <i class="fas fa-chevron-down dropdown-arrow" :class="{ 'rotated': member.showBusinessUnitDropdown }"></i>
                        </div>
                        <div v-if="member.showBusinessUnitDropdown" class="dropdown-panel">
                          <div class="search-box">
                            <input 
                              type="text" 
                              v-model="businessUnitSearchTerm" 
                              @input="filterBusinessUnits(member)"
                              placeholder="Search business units..."
                              class="search-input"
                            />
                          </div>
                          <div class="options-list">
                            <div v-if="member.filteredBusinessUnits && member.filteredBusinessUnits.length === 0 && !businessUnitSearchTerm" class="no-options">
                              No business units available
                            </div>
                            <div v-for="unit in member.filteredBusinessUnits || []" :key="unit" class="option-item" @click="toggleBusinessUnit(member, unit)">
                              <input type="checkbox" :checked="member.businessUnits.includes(unit)" />
                              <span>{{ unit }}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="dynamic-fields-row">
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Scope</label>
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
                      <SelectInput
                        v-model="member.type"
                        :options="[
                          { value: 'I', label: 'Internal' },
                          { value: 'E', label: 'External' },
                          { value: 'S', label: 'Self-Audit' },
                          { value: 'AI', label: 'AI Audit' }
                        ]"
                        label="Type"
                        placeholder="Select Type"
                        :error="getFieldError('type', index)"
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
                        :error="getFieldError('frequency', index)"
                      />
                    </div>
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Due Date</label>
                      <DateInput
                        v-model="member.dueDate"
                        label="Due Date"
                        placeholder="Select due date"
                        :error="getFieldError('dueDate', index)"
                      />
                    </div>
                  </div>
                  
                  <button class="save-section-btn" @click="toggleDetailsEditMode(member)">
                    <i class="fas fa-save"></i> Save
                  </button>
                </div>
              </div>
            </div>

            <!-- Team Member Details Review Section - Only show for non-AI audits -->
            <div v-if="auditData.type !== 'AI'" class="collapsible-section">
              <div class="section-header" @click="toggleSection(member, 'reviewTeam')">
                <h5>Team Member Details</h5>
                <i :class="['fas', member.isReviewTeamExpanded ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
              </div>
              
              <div class="section-content" :class="{ 'collapsed': !member.isReviewTeamExpanded }">
                <div class="review-content" v-if="!member.isTeamEditMode">
                  <div class="review-item">
                    <span class="review-label">Auditor:</span>
                    <span class="review-value">{{ getUserName(member.auditor) }}</span>
                  </div>
                  <div class="review-item">
                    <span class="review-label">Role:</span>
                    <span class="review-value">{{ member.role }}</span>
                  </div>
                  <div class="review-item">
                    <span class="review-label">Responsibilities:</span>
                    <span class="review-value">{{ member.responsibilities }}</span>
                  </div>
                  
                  <button class="edit-section-btn" @click="toggleTeamEditMode(member)">
                    <i class="fas fa-edit"></i> Edit
                  </button>
                </div>
                
                <!-- Edit Mode for Team Member Details -->
                <div class="edit-content" v-if="member.isTeamEditMode">
                  <div class="dynamic-fields-row">
                    <div class="dynamic-field-col">
                      <label class="dynamic-label">Auditor</label>
                      <CustomDropdown
                        v-model="member.auditor"
                        :config="{
                          name: 'Auditor',
                          label: 'Auditor',
                          values: users.map(user => ({ value: user.UserId, label: user.UserName })),
                          defaultValue: 'Select Auditor'
                        }"
                        :showSearchBar="true"
                        :error="getFieldError('auditor', index)"
                      />
                    </div>
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
                        :error="getFieldError('responsibilities', index)"
                        rows="3"
                      />
                    </div>
                  </div>
                  
                  <button class="save-section-btn" @click="toggleTeamEditMode(member)">
                    <i class="fas fa-save"></i> Save
                  </button>
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
          @click="nextTab"
          :disabled="!canProceed"
        >
          Next
        </button>
        <button 
          v-if="currentTab === tabs.length - 1" 
          class="nav-button assign" 
          @click.stop.prevent="handleAssignClick"
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

    <!-- AI Recommendations Sidebar -->
    <div v-if="showAIRecommendations" class="ai-recommendations-overlay" @click="onAIRecommendationsClose">
      <div class="ai-recommendations-sidebar" @click.stop>
      <div class="sidebar-header">
        <h3>
          Smart Recommendations
        </h3>
        <button @click="onAIRecommendationsClose" class="close-btn">
          <i class="fas fa-times"></i>
        </button>
      </div>
      
      <div class="sidebar-content">
        <div v-if="aiRecommendations && aiRecommendations.length > 0" class="recommendations-list">
          <div 
            v-for="(recommendation, index) in aiRecommendations" 
            :key="index"
            class="recommendation-card"
          >
            <div class="card-header">
              <div class="recommendation-rank">
                <span class="rank-number">{{ index + 1 }}</span>
                <div class="rank-info">
                  <h4>{{ recommendation.auditor_name || 'N/A' }}</h4>
                  <span class="confidence-badge">{{ formatPercent(recommendation.confidence_score) }} Match</span>
                </div>
              </div>
              <button @click="selectRecommendation(recommendation)" class="select-btn">
                <i class="fas fa-check"></i>
                {{ currentAIField === 'auditor' ? 'Select Auditor' : 'Select Reviewer' }}
              </button>
            </div>
            
            <div class="card-content">
              <div class="score-display">
                <div class="score-item">
                  <span class="score-label">Overall Score</span>
                  <span class="score-value">{{ Math.round((recommendation.total_score || 0) * 100) }}%</span>
                </div>
                <div class="score-item">
                  <span class="score-label">Skills Match</span>
                  <span class="score-value">{{ recommendation.skills_match || 'N/A' }}</span>
                </div>
              </div>
              
              <div class="reasoning-section">
                <h5>Why This Match?</h5>
                <p>{{ recommendation.reasoning || 'No reasoning provided' }}</p>
              </div>
              
              <div v-if="recommendation.metrics" class="metrics-section">
                <h5>Performance Metrics</h5>
                <div class="metrics-grid">
                  <div class="metric-item">
                    <span class="metric-label">Experience Match</span>
                    <span class="metric-value">{{ Math.round((recommendation.metrics.experience_match || 0) * 100) }}%</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">Skills Match</span>
                    <span class="metric-value">{{ Math.round((recommendation.metrics.skills_match || 0) * 100) }}%</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">Availability</span>
                    <span class="metric-value">{{ Math.round((recommendation.metrics.availability || 0) * 100) }}%</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">Domain Expertise</span>
                    <span class="metric-value">{{ Math.round((recommendation.metrics.domain_expertise || 0) * 100) }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else class="no-recommendations">
          <div class="empty-state">
            <h4>No Recommendations Available</h4>
            <p>Try providing more details about the audit requirements to get better recommendations.</p>
          </div>
        </div>
      </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import ValidationMixin from '@/mixins/ValidationMixin';
import SelectInput from '@/components/inputs/SelectInput.vue';
import CustomDropdown from '@/components/CustomDropdown.vue';
// import TextInput from '@/components/inputs/TextInput.vue';
import TextareaInput from '@/components/inputs/TextareaInput.vue';
import DateInput from '@/components/inputs/DateInput.vue';
import { AccessUtils } from '@/utils/accessUtils';
import { API_ENDPOINTS } from '../../config/api.js';
import aiRecommendationService from '@/services/aiRecommendationService';

export default {
  name: 'AssignAudit',
  mixins: [ValidationMixin],
  components: {
    SelectInput,
    CustomDropdown,
    // TextInput,
    TextareaInput,
    DateInput,
  },
  data() {
    return {
      currentTab: 0,
      tabs: [
        { name: 'Framework Selection', required: ['framework', 'type'] },
        { name: 'Policy Selection', required: ['policy'] }, // For AI audits
        { name: 'Team Creation', required: [] }, // For Internal/External/Self audits
        { name: 'Auditor Assignment', required: [] }, // For AI audits
        { name: 'Policy Assignment', required: [] }, // For Internal/External/Self audits
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
        role: 'Auditor',
        responsibilities: 'Conduct thorough audit review and provide recommendations',
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
        businessUnits: [], // <-- Add this for multi-select
        // Ensure all expansion states are properly initialized
        isPolicyAssignmentExpanded: true,
        isAuditDetailsExpanded: true,
        isReviewPolicyExpanded: true,
        isReviewDetailsExpanded: true,
        isReviewTeamExpanded: true,
        isPolicyEditMode: false,
        isDetailsEditMode: false,
        isTeamEditMode: false,
        showBusinessUnitDropdown: false,
        businessUnitSearchTerm: '',
        filteredBusinessUnits: [],
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
      // AI Recommendation properties
      showAIRecommendations: false,
      aiTaskData: null,
      aiRecommendations: null,
      isLoadingAI: false,
      isLoadingAuditorAI: false,
      isLoadingReviewerAI: false,
      currentAIField: null,
      currentAIMemberIndex: null
    };
  },
  computed: {
    canProceed() {
      if (this.currentTab === 0) {
        return !!(this.auditData.framework && this.auditData.type);
      }
      
      // For AI audits
      if (this.auditData.type === 'AI') {
        if (this.currentTab === 1) {
          return !!(this.auditData.policy);
        }
        if (this.currentTab === 2) {
          // All required fields for every team member, including at least one business unit and auditTitle
          const allValid = this.teamMembers.every((member, idx) => {
            const baseValid = !!(
              member.assignedPolicy &&
              member.assignedSubPolicy && // Sub-policy required for AI audits
              member.reviewer && // Reviewer required for all audit types including AI
              member.scope &&
              member.objective &&
              member.type &&
              member.frequency &&
              member.dueDate &&
              member.auditTitle &&
              Array.isArray(member.businessUnits) && member.businessUnits.length > 0
            );
            
            if (!baseValid) {
              // Debug log for missing fields
              const missing = [];
              if (!member.assignedPolicy) missing.push('assignedPolicy');
              if (!member.assignedSubPolicy) missing.push('assignedSubPolicy');
              if (!member.reviewer) missing.push('reviewer');
              if (!member.scope) missing.push('scope');
              if (!member.objective) missing.push('objective');
              if (!member.type) missing.push('type');
              if (!member.frequency) missing.push('frequency');
              if (!member.dueDate) missing.push('dueDate');
              if (!member.auditTitle) missing.push('auditTitle');
              if (!Array.isArray(member.businessUnits) || member.businessUnits.length === 0) missing.push('businessUnits');
              // eslint-disable-next-line no-console
              console.warn(`AI Audit Team member ${idx + 1} missing:`, missing);
            }
            return baseValid;
          });
          return allValid;
        }
      } 
      // For Internal/External/Self audits
      else {
        if (this.currentTab === 1) {
          // Team Creation validation
          return this.teamMembers.some(member =>
            member.auditor &&
            member.role &&
            member.responsibilities
          );
        }
        if (this.currentTab === 2) {
          // Step 3 (Policy Assignment) progression should not block on full details.
          // Enable Next when at least one team member has selected an Assigned Policy
          // (Subpolicy is optional for non-AI audits).
          const anyPolicySelected = this.teamMembers.some(member => !!member.assignedPolicy);
          return anyPolicySelected;
        }
      }
      
      return true;
    },
    
    isReviewTab() {
      // For AI audits: tab 3 (Framework -> Policy -> Auditor Assignment -> Review)
      // For Internal/External/Self: tab 3 (Framework -> Team -> Policy Assignment -> Review)
      return this.currentTab === 3;
    },
    
    canAssign() {
      // Check if framework is selected
      if (!this.auditData.framework) {
        console.log('❌ canAssign: No framework selected');
        return false;
      }

      // Check if at least one team member exists and has all required fields
      const hasValidTeamMember = this.teamMembers.some((member, index) => {
        console.log(`🔍 Validating team member ${index}:`, {
          assignedPolicy: member.assignedPolicy,
          assignedSubPolicy: member.assignedSubPolicy,
          reviewer: member.reviewer,
          auditor: member.auditor,
          scope: member.scope,
          objective: member.objective,
          type: member.type,
          frequency: member.frequency,
          dueDate: member.dueDate,
          role: member.role,
          responsibilities: member.responsibilities,
          auditType: this.auditData.type
        });

        // For AI audits, auditor is not required but reviewer is required, sub-policy is required for compliance accuracy
        const hasAssignmentInfo = member.assignedPolicy && 
                                (this.auditData.type === 'AI' ? member.assignedSubPolicy : true) && // Sub-policy required for AI audits
                                (member.reviewer && member.reviewer !== '') && // Reviewer required for all audit types
                                (this.auditData.type === 'AI' ? true : (member.auditor && member.auditor !== ''));
                                
        const hasAuditDetails = member.scope && 
                              member.objective && 
                              member.type && 
                              member.frequency && 
                              member.dueDate &&
                              (this.auditData.type === 'AI' ? true : (member.role && member.responsibilities));

        const isValid = hasAssignmentInfo && hasAuditDetails;
        console.log(`✅ Team member ${index} validation result:`, {
          hasAssignmentInfo,
          hasAuditDetails,
          isValid
        });
                              
        return isValid;
      });

      console.log('🎯 Final canAssign result:', hasValidTeamMember);
      return hasValidTeamMember;
    },
    selectedPolicy() {
      if (!this.auditData.policy) return null;
      return this.policies.find(p => p.PolicyId == this.auditData.policy);
    },
    selectedSubPolicy() {
      if (!this.auditData.subPolicy) return null;
      return this.subpolicies.find(sp => sp.id == this.auditData.subPolicy);
    },
    
    filteredUsers() {
      // Filter users based on audit type
      const type = this.auditData.type;
      console.log('🔍 Filtering users for audit type:', type);
      console.log('🔍 Total users available:', this.users.length);
      console.log('🔍 Sample user data:', this.users.slice(0, 2));
      
      if (!type) return this.users;
      
      let filtered = [];
      
      if (type === 'I') {
        // Internal: Internal Auditors + GRC Administrators + All users (for now)
        filtered = this.users.filter(u =>
          !u.Role || // Include users without role
          (u.Role && u.Role.toLowerCase().includes('internal')) ||
          (u.Role && u.Role.toLowerCase().includes('grc administrator')) ||
          (u.Role && u.Role.toLowerCase().includes('auditor')) ||
          (u.Role && u.Role.toLowerCase().includes('admin'))
        );
      } else if (type === 'E') {
        // External: External Auditors + GRC Administrators + All users (for now)
        filtered = this.users.filter(u =>
          !u.Role || // Include users without role
          (u.Role && u.Role.toLowerCase().includes('external')) ||
          (u.Role && u.Role.toLowerCase().includes('grc administrator')) ||
          (u.Role && u.Role.toLowerCase().includes('auditor')) ||
          (u.Role && u.Role.toLowerCase().includes('admin'))
        );
      } else if (type === 'S') {
        // Self-Audit: GRC Administrators + All users (for now)
        filtered = this.users.filter(u =>
          !u.Role || // Include users without role
          (u.Role && u.Role.toLowerCase().includes('grc administrator')) ||
          (u.Role && u.Role.toLowerCase().includes('admin')) ||
          (u.Role && u.Role.toLowerCase().includes('auditor'))
        );
      } else {
        filtered = this.users;
      }
      
      console.log('🔍 Filtered users count:', filtered.length);
      console.log('🔍 Filtered users sample:', filtered.slice(0, 2));
      
      // If no users match the filter, return all users to avoid empty dropdown
      if (filtered.length === 0) {
        console.log('⚠️ No users matched filter, returning all users');
        return this.users;
      }
      
      return filtered;
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
    handleAssignClick() {
      // Ensure any overlays are closed before submission
      if (this.showAIRecommendations) {
        this.onAIRecommendationsClose();
      }
      if (this.showingReportsModal) {
        this.closeReportsModal();
      }
      this.$nextTick(() => this.submitAudit());
    },
    // Sanitize long text fields to avoid DB length errors
    sanitizeField(value, maxLength) {
      if (value == null) return '';
      const str = String(value);
      if (str.length <= maxLength) return str;
      // Keep a small suffix to indicate truncation
      return str.slice(0, Math.max(0, maxLength - 3)) + '...';
    },
    // Check if auditor AI button should be enabled (requires policy only)
    isAuditorAIEnabled(memberIndex) {
      const member = this.teamMembers[memberIndex];
      const hasPolicy = member.assignedPolicy && member.assignedPolicy !== '' && member.assignedPolicy !== 'Select Policy';
      const isEnabled = !!hasPolicy;
      console.log(`🔍 Auditor AI Button Check for member ${memberIndex}:`, {
        assignedPolicy: member.assignedPolicy,
        hasPolicy: hasPolicy,
        isEnabled: isEnabled
      });
      return isEnabled;
    },
    
    // Check if reviewer AI button should be enabled (requires audit title, business unit, scope, objective, AND policy)
    isReviewerAIEnabled(memberIndex) {
      const member = this.teamMembers[memberIndex];
      const isEnabled = !!(
        member.auditTitle && 
        member.auditTitle.trim() !== '' &&
        Array.isArray(member.businessUnits) && 
        member.businessUnits.length > 0 &&
        member.scope && 
        member.scope.trim() !== '' &&
        member.objective && 
        member.objective.trim() !== ''
      );
      console.log(`🔍 Reviewer AI Button Check for member ${memberIndex}:`, {
        auditTitle: member.auditTitle,
        businessUnits: member.businessUnits,
        businessUnitsLength: member.businessUnits ? member.businessUnits.length : 0,
        scope: member.scope,
        objective: member.objective,
        isEnabled: isEnabled
      });
      return isEnabled;
    },
    
    // Debug methods to check button states
    checkAuditorButtonState(memberIndex) {
      const member = this.teamMembers[memberIndex];
      const isEnabled = this.isAuditorAIEnabled(memberIndex);
      console.log(`🔍 Debug Auditor Button State for member ${memberIndex}:`, {
        assignedPolicy: member.assignedPolicy,
        assignedPolicyType: typeof member.assignedPolicy,
        assignedPolicyTruthy: !!member.assignedPolicy,
        isEnabled: isEnabled,
        shouldBeDisabled: !isEnabled
      });
    },
    
    checkReviewerButtonState(memberIndex) {
      const member = this.teamMembers[memberIndex];
      const isEnabled = this.isReviewerAIEnabled(memberIndex);
      console.log(`🔍 Debug Reviewer Button State for member ${memberIndex}:`, {
        auditTitle: member.auditTitle,
        businessUnits: member.businessUnits,
        scope: member.scope,
        objective: member.objective,
        assignedPolicy: member.assignedPolicy,
        auditTitleTruthy: !!(member.auditTitle && member.auditTitle.trim() !== ''),
        businessUnitsTruthy: !!(Array.isArray(member.businessUnits) && member.businessUnits.length > 0),
        scopeTruthy: !!(member.scope && member.scope.trim() !== ''),
        objectiveTruthy: !!(member.objective && member.objective.trim() !== ''),
        policyTruthy: !!(member.assignedPolicy && member.assignedPolicy !== '' && member.assignedPolicy !== 'Select Policy'),
        isEnabled: isEnabled,
        shouldBeDisabled: !isEnabled
      });
    },
    
    // Permission check methods
    checkAssignAuditPermission() {
      // Show assign audit access denied popup if user doesn't have permission
      AccessUtils.showAssignAuditDenied();
    },
    
    // Handle assign audit button click with permission check
    handleAssignAuditClick() {
      // For now, proceed with audit assignment
      // In a full implementation, you would check user permissions here
      // and call checkAssignAuditPermission() if the user doesn't have permission
      this.submitAudit();
    },
    
    async fetchFrameworks() {
      try {
        console.log('🔄 [FRAMEWORK DROPDOWN] Fetching frameworks...');
        const token = localStorage.getItem('access_token');
        const res = await axios.get('/api/frameworks/', {
          withCredentials: true,
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        
        console.log('✅ [FRAMEWORK DROPDOWN] Received frameworks:', res.data);
        console.log('✅ [FRAMEWORK DROPDOWN] Framework count:', res.data.length);

        // 1) Default to server response
        let frameworks = Array.isArray(res.data) ? res.data : [];

        // 2) Ask backend which framework is currently selected in session
        try {
          const sel = await axios.get('/api/frameworks/get-selected/', {
            withCredentials: true,
            headers: token ? { Authorization: `Bearer ${token}` } : {},
            params: { userId: localStorage.getItem('user_id') || 'default_user' }
          });

          if (sel.data && sel.data.success && sel.data.hasFramework && sel.data.frameworkId) {
            const activeId = String(sel.data.frameworkId);
            console.log('✅ [FRAMEWORK DROPDOWN] Active framework in session:', activeId);
            // Guard on frontend: if a framework is active, show only that
            frameworks = frameworks.filter(f => String(f.FrameworkId) === activeId);
          } else {
            console.log('ℹ️ [FRAMEWORK DROPDOWN] No active framework (All Frameworks)');
          }
        } catch (err) {
          console.warn('⚠️ [FRAMEWORK DROPDOWN] Could not read selected framework; leaving server response as-is');
        }

        this.frameworks = frameworks;
        console.log('✅ [FRAMEWORK DROPDOWN] Final frameworks shown:', this.frameworks);
      } catch (e) {
        console.error('❌ [FRAMEWORK DROPDOWN] Error fetching frameworks:', e);
        // Handle access denied errors
        if (AccessUtils.handleApiError(e, 'audit framework access')) {
          return;
        }
        this.frameworks = [];
      }
    },
    async fetchUsers() {
      try {
        console.log('🔄 Fetching users...');
        const res = await axios.get('/api/users/', {
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json'
          }
        });
        console.log('✅ Users API response:', res.data);
        console.log('✅ Response status:', res.status);
        console.log('✅ Response data type:', typeof res.data);
        console.log('✅ Response data keys:', Object.keys(res.data || {}));
        
        // Handle the response format: { success: true, users: [...] }
        let users = [];
        if (res.data && res.data.success && res.data.users) {
          users = res.data.users;
          console.log('✅ Parsed users from success.users format:', users.length);
        } else if (Array.isArray(res.data)) {
          // Fallback for direct array response
          users = res.data;
          console.log('✅ Parsed users from direct array format:', users.length);
        } else if (res.data && Array.isArray(res.data.data)) {
          // Another fallback format
          users = res.data.data;
          console.log('✅ Parsed users from data.data format:', users.length);
        } else {
          console.warn('⚠️ Unexpected response format:', res.data);
        }
        
        // Ensure users have required fields
        users = users.map(user => ({
          UserId: user.UserId || user.id || user.userId,
          UserName: user.UserName || user.name || user.username || 'Unknown',
          Role: user.Role || user.role || '',
          Email: user.Email || user.email || '',
          ...user
        })).filter(user => user.UserId); // Filter out invalid users
        
        console.log('✅ Users processed successfully:', users.length, 'users');
        console.log('🔍 Sample users:', users.slice(0, 3));
        this.users = users;
        
        if (users.length === 0) {
          console.warn('⚠️ No users found. This might indicate an API issue or empty database.');
        }
      } catch (e) {
        console.error('❌ Error fetching users:', e);
        console.error('❌ Error details:', e.response?.data);
        console.error('❌ Error status:', e.response?.status);
        console.error('❌ Error message:', e.message);
        
        // Handle access denied errors
        if (AccessUtils.handleApiError(e, 'audit user access')) {
          return;
        }
        
        // Try fallback endpoint
        try {
          console.log('🔄 Trying fallback endpoint: /api/compliance-users/');
          const fallbackRes = await axios.get('/api/compliance-users/', {
            withCredentials: true
          });
          if (fallbackRes.data && fallbackRes.data.success && fallbackRes.data.users) {
            this.users = fallbackRes.data.users;
            console.log('✅ Fallback endpoint succeeded:', this.users.length, 'users');
            return;
          }
        } catch (fallbackError) {
          console.error('❌ Fallback endpoint also failed:', fallbackError);
        }
        
        this.users = [];
        this.$popup?.error('Failed to load reviewers. Please refresh the page and try again.');
      }
    },
    async onFrameworkChange() {
      this.auditData.policy = '';
      this.auditData.subPolicy = '';
      this.policies = [];
      this.subpolicies = [];
      if (this.auditData.framework) {
        try {
          const token = localStorage.getItem('access_token');
          const res = await axios.get('/api/policies/', { 
            params: { framework_id: this.auditData.framework },
            withCredentials: true,
            headers: token ? { Authorization: `Bearer ${token}` } : {}
          });
          this.policies = res.data.policies || res.data;
        } catch (e) {
          console.error('Error fetching policies:', e);
          // Handle access denied errors
          if (AccessUtils.handleApiError(e, 'audit policy access')) {
            return;
          }
          this.policies = [];
        }
      }
    },
    
    onAuditTypeChange() {
      // Reset team members and update workflow based on audit type
      if (this.auditData.type === 'AI') {
        // For AI audits, we only need one entry with reviewer, no team members
        this.teamMembers = [{
          auditor: '',
          role: 'AI Audit',
          responsibilities: 'AI will automatically conduct the audit based on selected policies',
          assignedPolicy: this.auditData.policy || '',
          assignedSubPolicy: this.auditData.subPolicy || '',
          memberSubpolicies: [],
          reviewer: '',
          auditTitle: '',
          scope: '',
          objective: '',
          businessUnit: '',
          type: 'AI',
          frequency: '',
          dueDate: '',
          reports: '',
          businessUnits: [],
          isPolicyAssignmentExpanded: true,
          isAuditDetailsExpanded: true,
          isReviewPolicyExpanded: true,
          isReviewDetailsExpanded: true,
          isReviewTeamExpanded: true,
          isPolicyEditMode: false,
          isDetailsEditMode: false,
          isTeamEditMode: false,
          showBusinessUnitDropdown: false,
          businessUnitSearchTerm: '',
          filteredBusinessUnits: [],
        }];
        // Update tabs for AI workflow
        this.tabs = [
          { name: 'Framework Selection', required: ['framework', 'type'] },
          { name: 'Policy Selection', required: ['policy'] },
          { name: 'Auditor Assignment', required: [] },
          { name: 'Review & Assign', required: ['scope', 'objective', 'type', 'frequency', 'dueDate'] }
        ];
      } else {
        // For Internal/External/Self audits, reset to basic team member structure
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
          type: this.auditData.type,
          frequency: '',
          dueDate: '',
          reports: '',
          businessUnits: [],
          isPolicyAssignmentExpanded: true,
          isAuditDetailsExpanded: true,
          isReviewPolicyExpanded: true,
          isReviewDetailsExpanded: true,
          isReviewTeamExpanded: true,
          isPolicyEditMode: false,
          isDetailsEditMode: false,
          isTeamEditMode: false,
          showBusinessUnitDropdown: false,
          businessUnitSearchTerm: '',
          filteredBusinessUnits: [],
        }];
        // Update tabs for Internal/External/Self audit workflow
        this.tabs = [
          { name: 'Framework Selection', required: ['framework', 'type'] },
          { name: 'Team Creation', required: [] },
          { name: 'Policy Assignment', required: [] },
          { name: 'Review & Assign', required: ['scope', 'objective', 'type', 'frequency', 'dueDate'] }
        ];
      }
      // Reset to first tab when audit type changes
      this.currentTab = 0;
    },
    async onPolicyChange() {
      this.auditData.subPolicy = '';
      this.subpolicies = [];
      if (this.auditData.policy) {
        try {
          // Get JWT token for authentication
          const token = localStorage.getItem('access_token');
          const headers = { 'Content-Type': 'application/json' };
          if (token) {
            headers['Authorization'] = `Bearer ${token}`;
          }
          
          const res = await axios.get(`/api/compliance/policies/${this.auditData.policy}/subpolicies/`, { headers });
          console.log('🔍 Main subpolicies API response:', res.data);
          if (res.data && res.data.success) {
            // Transform the response to match expected format
            this.subpolicies = (res.data.subpolicies || []).map(sp => ({
              id: sp.id,
              name: sp.name,
              description: sp.description,
              status: sp.status,
              createdBy: sp.createdBy,
              createdDate: sp.createdDate,
              identifier: sp.identifier,
              control: sp.control,
              permanentTemporary: sp.permanentTemporary
            }));
            console.log('✅ Main subpolicies loaded:', this.subpolicies);
          } else {
            this.subpolicies = [];
            console.log('❌ No main subpolicies found');
          }
        } catch (e) {
          console.error('Error fetching subpolicies:', e);
          this.subpolicies = [];
        }
        
        // Update team members with selected policy
        this.teamMembers.forEach(member => {
          member.assignedPolicy = this.auditData.policy;
          member.assignedSubPolicy = this.auditData.subPolicy || '';
        });

        // For AI audits, just log that policy is selected - workflow will start when user clicks Assign Audit
        if (this.auditData.type === 'AI') {
          console.log('🤖 AI Audit: Policy selected, ready for AI audit workflow...');
        }
      }
    },
    
    // Handle main sub-policy selection (Frame 2)
    onMainSubPolicyChange() {
      console.log('🔄 Main sub-policy changed:', this.auditData.subPolicy);
      
      // Update team members with selected sub-policy
      this.teamMembers.forEach(member => {
        member.assignedSubPolicy = this.auditData.subPolicy || '';
      });
      
      console.log('✅ Team members updated with sub-policy:', this.auditData.subPolicy);
    },
    
    // AI Audit Workflow Methods
    startAIAuditWorkflow() {
      console.log('🚀 Starting AI audit workflow...');
      
      // The submitAudit method already handles AI audit navigation
      // Just call it directly - it will navigate to document upload page
      this.submitAudit();
    },
    
    addTeamMember() {
      this.teamMembers.push({
        auditor: '',
        role: 'Auditor',
        responsibilities: 'Conduct thorough audit review and provide recommendations',
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
        businessUnits: [], // <-- Add this for multi-select
        // Ensure all expansion states are properly initialized
        isPolicyAssignmentExpanded: true,
        isAuditDetailsExpanded: true,
        isReviewPolicyExpanded: true,
        isReviewDetailsExpanded: true,
        isReviewTeamExpanded: true,
        isPolicyEditMode: false,
        isDetailsEditMode: false,
        isTeamEditMode: false,
        showBusinessUnitDropdown: false,
        businessUnitSearchTerm: '',
        filteredBusinessUnits: [],
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
      
      // Check consent before proceeding
      try {
        const consentService = (await import('@/services/consentService.js')).default;
        const { CONSENT_ACTIONS } = await import('@/utils/consentManager.js');
        
        const canProceed = await consentService.checkAndRequestConsent(
          CONSENT_ACTIONS.CREATE_AUDIT
        );
        
        // If user declined consent, stop here
        if (!canProceed) {
          console.log('Audit creation cancelled by user (consent declined)');
          return;
        }
      } catch (consentError) {
        console.error('Error checking consent:', consentError);
        // Continue with audit creation if consent check fails
      }
      
      // Validate form before submission
      // if (!this.validateForm()) {
      //   // Show error message
      //   this.$popup.error('Please fix the validation errors before submitting.');
      //   await this.sendPushNotification({
      //     title: 'Audit Assignment Failed',
      //     message: 'Validation errors occurred while assigning the audit. Please fix them and try again.',
      //     category: 'audit',
      //     priority: 'high',
      //     user_id: 'default_user'
      //   });
      //   return;
      // }
      
      try {
        this.assigning = true;
        
        // Get the first team member to use as template for common fields
        const templateMember = this.teamMembers[0];
        
        // Validate that reviewer is selected (required for all audit types)
        if (!templateMember.reviewer || templateMember.reviewer === '') {
          this.$popup.error('Please select a reviewer before assigning the audit.');
          return;
        }

        // For non-AI audits, validate that at least one team member is selected
        if (this.auditData.type !== 'AI') {
          const validTeamMembers = this.teamMembers.filter(member => 
            member.auditor && member.auditor !== '' && member.auditor !== 'Select Auditor'
          );
          
          if (validTeamMembers.length === 0) {
            this.$popup.error('Please select at least one auditor before assigning the audit.');
            return;
          }
        }

        // Create payload with team member IDs and common fields
        const validTeamMembers = this.teamMembers.filter(member => 
          member.auditor && member.auditor !== '' && member.auditor !== 'Select Auditor'
        );
        
        console.log('🔍 Valid team members for submission:', validTeamMembers.map(m => ({
          auditor: m.auditor,
          role: m.role,
          reviewer: m.reviewer
        })));

        const payload = {
          // DB limits: Title 255, Responsibility 255, BusinessUnit 255. Scope/Objective are Text but backend DB may be limited in practice.
          title: this.sanitizeField(templateMember.auditTitle, 255),
          scope: this.sanitizeField(templateMember.scope, 255),
          objective: this.sanitizeField(templateMember.objective, 255),
          business_unit: this.sanitizeField(templateMember.businessUnits.join(', '), 255),
          role: templateMember.role || 'Auditor', // Default role if not set
          responsibility: this.sanitizeField(templateMember.responsibilities || 'Audit responsibilities', 255), // Default responsibility if not set
          team_members: this.auditData.type === 'AI' ? [] : validTeamMembers.map(member => member.auditor),
          reviewer: templateMember.reviewer,
          framework_id: this.auditData.framework,
          policy_id: templateMember.assignedPolicy || null,
          subpolicy_id: templateMember.assignedSubPolicy || null,
          due_date: templateMember.dueDate,
          frequency: templateMember.frequency,
          audit_type: templateMember.type,
          reports: templateMember.reports || ''
        };

        console.log('🚀 Submitting audit with payload:', payload);
        console.log('🔍 Debug - team_members:', payload.team_members);
        console.log('🔍 Debug - reviewer:', payload.reviewer);
        console.log('🔍 Debug - audit_type:', payload.audit_type);
        console.log('🔍 Debug - framework_id:', payload.framework_id);
        console.log('🔍 Debug - policy_id:', payload.policy_id);
        console.log('🔍 Debug - due_date:', payload.due_date);
        console.log('🔍 Debug - frequency:', payload.frequency);
        const response = await axios.post(API_ENDPOINTS.AUDIT_CREATE, payload);
        console.log('✅ Audit submission response:', response.data);
        
        if (response.data.audits_created > 0) {
          // Show different messages based on audit type
          if (this.auditData.type === 'AI') {
            this.$popup.info('AI audit created successfully! You will be redirected to document upload page.');
          } else {
            this.$popup.success(`Successfully created ${response.data.audits_created} audit(s)`);
          }
          
          await this.sendPushNotification({
            title: 'Audit Assigned',
            message: `Successfully created ${response.data.audits_created} audit(s).`,
            category: 'audit',
            priority: 'high',
            user_id: 'default_user'
          });
          this.resetForm();
          
          // Navigate based on audit type
          console.log('🔄 Navigating after successful assignment in 2 seconds...');
          console.log('🔍 Debug - auditData.type:', this.auditData.type);
          console.log('🔍 Debug - templateMember.type:', templateMember.type);
          console.log('🔍 Debug - templateMember object:', templateMember);
          console.log('🔍 Debug - condition check:', this.auditData.type === 'AI', templateMember.type === 'AI');
          setTimeout(() => {
            if (this.auditData.type === 'AI' || templateMember.type === 'AI') {
              // For AI audits, go to document upload page
              console.log('🚀 Navigating to AI audit document upload');
              this.$router.push(`/auditor/ai-audit/${response.data.audit_ids[0]}/upload`);
            } else {
              // For regular audits, go to reviews page
              console.log('🚀 Navigating to /auditor/reviews');
              this.$router.push('/auditor/reviews');
            }
          }, 2000);
        } else {
          throw new Error('No audits were created');
        }
        
        return response; // Return the response for potential chaining
        
      } catch (error) {
        console.error('Error in submitAudit:', error);
        
        // Handle access denied errors
        if (AccessUtils.handleApiError(error, 'audit assignment')) {
          return;
        }
        
        const errorMessage = error.response?.data?.error || 'Please try again.';
        if (error.response?.data?.details) {
          // Handle validation errors from backend
          this.handleBackendValidationErrors(error.response.data.details);
        }
        this.$popup.error('Error assigning audits: ' + errorMessage);
        await this.sendPushNotification({
          title: 'Audit Assignment Failed',
          message: `Error assigning audits: ${errorMessage}`,
          category: 'audit',
          priority: 'high',
          user_id: 'default_user'
        });
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
        role: 'Auditor',
        responsibilities: 'Conduct thorough audit review and provide recommendations',
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
        businessUnits: [], // <-- Add this for multi-select
        // Ensure all expansion states are properly initialized
        isPolicyAssignmentExpanded: true,
        isAuditDetailsExpanded: true,
        isReviewPolicyExpanded: true,
        isReviewDetailsExpanded: true,
        isReviewTeamExpanded: true,
        isPolicyEditMode: false,
        isDetailsEditMode: false,
        isTeamEditMode: false,
        showBusinessUnitDropdown: false,
        businessUnitSearchTerm: '',
        filteredBusinessUnits: [],
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
      // For AI audits, look in the main subpolicies array
      if (this.auditData.type === 'AI') {
        const subPolicy = this.subpolicies.find(sp => sp.id == subPolicyId);
        return subPolicy ? subPolicy.name : 'Not Assigned';
      }
      
      // For regular audits, look in member's subpolicies
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

          // Get JWT token for authentication
          const token = localStorage.getItem('access_token');
          const headers = { 'Content-Type': 'application/json' };
          if (token) {
            headers['Authorization'] = `Bearer ${token}`;
          }
          
          const response = await axios.get(`/api/compliance/policies/${member.assignedPolicy}/subpolicies/`, { headers });
          console.log('🔍 Subpolicies API response:', response.data);
          
          if (response.data && response.data.success) {
            // Transform the response to match expected format
            member.memberSubpolicies = (response.data.subpolicies || []).map(sp => ({
              SubPolicyId: sp.id,
              SubPolicyName: sp.name,
              Description: sp.description,
              Status: sp.status,
              CreatedByName: sp.createdBy,
              CreatedByDate: sp.createdDate,
              Identifier: sp.identifier,
              Control: sp.control,
              PermanentTemporary: sp.permanentTemporary
            }));
            console.log('✅ Subpolicies loaded for member:', memberIndex, member.memberSubpolicies);
          } else {
            member.memberSubpolicies = [];
            console.log('❌ No subpolicies found for member:', memberIndex);
          }
          await this.fetchComplianceCount(memberIndex);
          
        } catch (error) {
          console.error('Error in onMemberPolicyChange:', error);
          
          // Handle access denied errors

          if (AccessUtils.handleApiError(error, 'audit subpolicy access')) {

return;

}
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
        const countResponse = await axios.get('/api/compliance-count/', {
          params: {
            policy_id: member.assignedPolicy,
            subpolicy_id: member.assignedSubPolicy || ''
          }
        });
        
        // Handle access denied errors
        const key = `${member.assignedPolicy}-${member.assignedSubPolicy || ''}`;
        this.memberComplianceCounts = {
          ...this.memberComplianceCounts,
          [key]: countResponse.data.count || 0
        };
        
      } catch (error) {
        console.error('Error fetching compliance count:', error);
        
        // Handle access denied errors
        if (AccessUtils.handleApiError(error, 'audit compliance count access')) {
          return;
        }
        
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
        
        const response = await axios.get(API_ENDPOINTS.AUDIT_REPORTS_CHECK, { params });
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
        
        const response = await axios.get(API_ENDPOINTS.AUDIT_REPORTS_DETAILS, { params });
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
        await this.sendPushNotification({
          title: 'Reports Attached',
          message: `Reports have been attached to the audit assignment.`,
          category: 'audit',
          priority: 'medium',
          user_id: 'default_user'
        });
        this.closeReportsModal();
      } catch (error) {
        console.error('Error saving reports:', error);
        this.$popup.error('Error saving reports. Please try again.');
        await this.sendPushNotification({
          title: 'Report Attachment Failed',
          message: 'Error saving reports. Please try again.',
          category: 'audit',
          priority: 'high',
          user_id: 'default_user'
        });
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
      console.log(`Toggling section: ${section}`, member);
      if (section === 'policyAssignment') {
        member.isPolicyAssignmentExpanded = !member.isPolicyAssignmentExpanded;
      } else if (section === 'auditDetails') {
        member.isAuditDetailsExpanded = !member.isAuditDetailsExpanded;
      } else if (section === 'reviewPolicy') {
        member.isReviewPolicyExpanded = !member.isReviewPolicyExpanded;
        console.log('Review Policy expanded:', member.isReviewPolicyExpanded);
      } else if (section === 'reviewDetails') {
        member.isReviewDetailsExpanded = !member.isReviewDetailsExpanded;
        console.log('Review Details expanded:', member.isReviewDetailsExpanded);
      } else if (section === 'reviewTeam') {
        member.isReviewTeamExpanded = !member.isReviewTeamExpanded;
        console.log('Review Team expanded:', member.isReviewTeamExpanded);
      }
    },
    
    // New methods for toggling edit modes
    togglePolicyEditMode(member) {
      member.isPolicyEditMode = !member.isPolicyEditMode;
    },
    
    toggleDetailsEditMode(member) {
      member.isDetailsEditMode = !member.isDetailsEditMode;
    },
    
    toggleTeamEditMode(member) {
      member.isTeamEditMode = !member.isTeamEditMode;
    },

    nextTab() {
      this.currentTab++;
      this.resetCollapsibleSections();
    },

    resetCollapsibleSections() {
      this.teamMembers.forEach(member => {
        member.isPolicyAssignmentExpanded = true;
        member.isAuditDetailsExpanded = true;
        member.isReviewPolicyExpanded = true;
        member.isReviewDetailsExpanded = true;
        member.isReviewTeamExpanded = true;
        member.isPolicyEditMode = false;
        member.isDetailsEditMode = false;
        member.isTeamEditMode = false;
        member.showBusinessUnitDropdown = false;
        member.businessUnitSearchTerm = '';
        member.filteredBusinessUnits = [];
      });
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
    getFrameworkName() {
      if (this.auditData.framework) {
        const framework = this.frameworks.find(f => f.FrameworkId === this.auditData.framework);
        return framework ? framework.FrameworkName : 'Selected Framework';
      }
      return 'Compliance';
    },  
    async sendPushNotification(notificationData) {
      try {
        const response = await fetch('http://localhost:8000/api/push-notification/', {
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
    expandAllSections() {
      this.teamMembers.forEach(member => {
        member.isPolicyAssignmentExpanded = true;
        member.isAuditDetailsExpanded = true;
        member.isReviewPolicyExpanded = true;
        member.isReviewDetailsExpanded = true;
        member.isReviewTeamExpanded = true;
        member.isPolicyEditMode = false;
        member.isDetailsEditMode = false;
        member.isTeamEditMode = false;
        member.showBusinessUnitDropdown = false;
        member.businessUnitSearchTerm = '';
        member.filteredBusinessUnits = [];
      });
    },
        // AI Recommendation methods
    async getAIRecommendations(fieldType, memberIndex) {
      console.log(`🔍 getAIRecommendations called with fieldType: ${fieldType}, memberIndex: ${memberIndex}`);
      
      // Check if the button should be enabled before proceeding
      if (fieldType === 'auditor') {
        const isEnabled = this.isAuditorAIEnabled(memberIndex);
        console.log(`🔍 Auditor button check: isEnabled = ${isEnabled}`);
        if (!isEnabled) {
          console.log('🚫 Auditor AI button clicked but should be disabled - ignoring');
          this.$popup.warning('Please select Policy first before getting AI recommendations');
          return;
        }
      }
      
      if (fieldType === 'reviewer') {
        const isEnabled = this.isReviewerAIEnabled(memberIndex);
        console.log(`🔍 Reviewer button check: isEnabled = ${isEnabled}`);
        if (!isEnabled) {
          console.log('🚫 Reviewer AI button clicked but should be disabled - ignoring');
          this.$popup.warning('Please fill Audit Title, Business Unit, Scope, and Objective first before getting AI recommendations');
          return;
        }
      }
      
      this.currentAIField = fieldType;
      this.currentAIMemberIndex = memberIndex;
      
      // Set the appropriate loading state
      if (fieldType === 'auditor') {
        this.isLoadingAuditorAI = true;
      } else if (fieldType === 'reviewer') {
        this.isLoadingReviewerAI = true;
      }
      
      try {
        // Prepare task data for AI analysis - use actual form data
        const member = this.teamMembers[memberIndex];
        
        // Smart data collection - prioritize filled fields from all pages
        let title = 'Audit Assignment';
        let description = 'Comprehensive audit review and assessment';
        let domain = 'General Audit';
        let objective = 'Evaluate compliance and identify improvement opportunities';
        let responsibilities = 'Conduct thorough audit review and provide recommendations';
        
        // Check if we have data from any page
        if (member.auditTitle && member.auditTitle.trim() !== '') {
          title = member.auditTitle;
        }
        if (member.scope && member.scope.trim() !== '') {
          description = member.scope;
        }
        if (Array.isArray(member.businessUnits) && member.businessUnits.length > 0) {
          domain = member.businessUnits.join(', ');
        }
        if (member.objective && member.objective.trim() !== '') {
          objective = member.objective;
        }
        if (member.responsibilities && member.responsibilities.trim() !== '') {
          responsibilities = member.responsibilities;
        }
        
        // If we still have generic defaults, enhance them based on context
        if (title === 'Audit Assignment') {
          title = `${this.getFrameworkName()} Audit Assignment`;
        }
        if (description === 'Comprehensive audit review and assessment') {
          description = `Review and assess ${this.getFrameworkName()} compliance requirements`;
        }
        if (domain === 'General Audit') {
          domain = this.getFrameworkName() || 'Compliance Audit';
        }
        
        
        // Add context based on current page
        let pageContext = '';
        if (this.currentTab === 0) {
          pageContext = 'Framework Selection';
        } else if (this.currentTab === 1) {
          if (this.auditData.type === 'AI') {
            pageContext = 'Policy Selection';
          } else {
            pageContext = 'Team Creation';
          }
        } else if (this.currentTab === 2) {
          if (this.auditData.type === 'AI') {
            pageContext = 'Auditor Assignment';
          } else {
            pageContext = 'Policy Assignment';
          }
        } else if (this.currentTab === 3) {
          pageContext = 'Review & Assign';
        }
        
        // Add policy and subpolicy context for better AI recommendations
        let policyContext = '';
        let subpolicyContext = '';
        let auditType = this.auditData.type || 'I';
        
        if (member.assignedPolicy) {
          const policy = this.policies.find(p => p.PolicyId === member.assignedPolicy);
          if (policy) {
            policyContext = policy.PolicyName;
            // Add policy description to domain if available
            if (policy.PolicyDescription) {
              domain = `${domain} - ${policy.PolicyDescription.substring(0, 100)}`;
            }
          }
        }
        
        if (member.assignedSubPolicy) {
          const subpolicy = member.memberSubpolicies.find(sp => sp.SubPolicyId === member.assignedSubPolicy);
          if (subpolicy) {
            subpolicyContext = subpolicy.SubPolicyName;
            // Add subpolicy details to description
            if (subpolicy.Description) {
              description = `${description} - Subpolicy: ${subpolicy.Description.substring(0, 150)}`;
            }
          }
        }
        
        // Create task data with policy context and audit type
        this.aiTaskData = {
          title: title,
          description: description,
          domain: domain,
          severity: 'Medium',
          departmentId: 1,
          reviewId: `audit_${Date.now()}_${memberIndex}_${this.currentTab}`,
          reviewType: 'audit',
          objective: objective,
          responsibilities: responsibilities,
          pageContext: pageContext,
          fieldType: fieldType,
          auditType: auditType,
          policyContext: policyContext,
          subpolicyContext: subpolicyContext,
          assignedPolicy: member.assignedPolicy,
          assignedSubPolicy: member.assignedSubPolicy
        };
        
        console.log(`AI Task Data being sent from Page ${this.currentTab + 1} (${pageContext}):`, JSON.stringify(this.aiTaskData, null, 2));
        
        // Call AI service to get recommendations
        const result = await aiRecommendationService.getRecommendations(this.aiTaskData);
        
        console.log('AI Service Response:', JSON.stringify(result, null, 2));
        
        if (result.success) {
          // Handle the correct response structure from backend
          const recommendations = result.data.data.recommendations;
          let relevantRecommendations = [];
          
          // Get recommendations based on field type
          if (fieldType === 'auditor' && recommendations && recommendations.auditor_recommendations) {
            relevantRecommendations = recommendations.auditor_recommendations;
            console.log('🔍 Found auditor recommendations:', relevantRecommendations.length);
          } else if (fieldType === 'reviewer' && recommendations && recommendations.reviewer_recommendations) {
            relevantRecommendations = recommendations.reviewer_recommendations;
            console.log('🔍 Found reviewer recommendations:', relevantRecommendations.length);
          }
          
          if (relevantRecommendations.length > 0) {
            // Convert backend format to frontend format
            this.aiRecommendations = relevantRecommendations.map(rec => ({
              auditor_id: rec.user_id,
              auditor_name: rec.user_name,
              // Convert score (0..1) to percentage 0..100 and preserve 0
              confidence_score: Math.round(((rec.score ?? 0) * 100)),
              reasoning: this.generateReasoningFromMetrics(rec.metrics, rec.score),
              skills_match: this.calculateSkillsMatch(rec.metrics),
              total_score: rec.score, // Use rec.score
              metrics: rec.metrics // Pass metrics directly
            }));
            console.log('🔍 Processed AI recommendations:', this.aiRecommendations.length);
          } else {
            this.aiRecommendations = [];
            console.log('🔍 No relevant recommendations found');
          }
          
          // If no recommendations, show empty state
          if (this.aiRecommendations.length === 0) {
            console.log('🔧 No recommendations received from AI service');
          }
          
          this.showAIRecommendations = true;
        } else {
          console.error('AI Service Error:', result.error);
          this.$popup.error('Failed to get AI recommendations: ' + result.error);
        }
      } catch (error) {
        console.error('Error getting AI recommendations:', error);
        this.$popup.error('Failed to get AI recommendations. Please try again.');
      } finally {
        // Reset the appropriate loading state
        if (fieldType === 'auditor') {
          this.isLoadingAuditorAI = false;
        } else if (fieldType === 'reviewer') {
          this.isLoadingReviewerAI = false;
        }
      }
    },
    
    onAuditorSelected(auditor) {
      if (this.currentAIMemberIndex !== null) {
        this.teamMembers[this.currentAIMemberIndex].auditor = auditor.user_id;
        this.$popup.success(`Selected ${auditor.user_name} as auditor`);
      }
      this.showAIRecommendations = false;
    },
    
    onReviewerSelected(reviewer) {
      if (this.currentAIMemberIndex !== null) {
        this.teamMembers[this.currentAIMemberIndex].reviewer = reviewer.user_id;
        this.$popup.success(`Selected ${reviewer.user_name} as reviewer`);
      }
      this.showAIRecommendations = false;
    },
    
    onAIRecommendationsClose() {
      this.showAIRecommendations = false;
      this.currentAIField = null;
      this.currentAIMemberIndex = null;
    },
    
    selectRecommendation(recommendation) {
      if (this.currentAIMemberIndex !== null && recommendation.auditor_id) {
        // Find the user by ID and set it in the appropriate dropdown based on field type
        const selectedUser = this.users.find(user => user.UserId === recommendation.auditor_id);
        if (selectedUser) {
          if (this.currentAIField === 'auditor') {
            this.teamMembers[this.currentAIMemberIndex].auditor = recommendation.auditor_id;
            this.$popup.success(`Selected ${recommendation.auditor_name} as auditor based on AI recommendation`);
          } else if (this.currentAIField === 'reviewer') {
            this.teamMembers[this.currentAIMemberIndex].reviewer = recommendation.auditor_id;
            this.$popup.success(`Selected ${recommendation.auditor_name} as reviewer based on AI recommendation`);
          }
        }
      }
      this.showAIRecommendations = false;
      this.currentAIField = null;
      this.currentAIMemberIndex = null;
    },
    
    
    generateReasoningFromMetrics(metrics, score) {
      if (!metrics) return 'No reasoning provided';
      
      const reasons = [];
      
      // Add reasoning based on ML metrics
      if (metrics.experience_match > 0.8) {
        reasons.push('High experience match');
      } else if (metrics.experience_match > 0.6) {
        reasons.push('Good experience match');
      }
      
      if (metrics.skills_match > 0.7) {
        reasons.push('Strong skills alignment');
      } else if (metrics.skills_match > 0.5) {
        reasons.push('Good skills match');
      }
      
      if (metrics.domain_expertise > 0.8) {
        reasons.push('Excellent domain expertise');
      } else if (metrics.domain_expertise > 0.6) {
        reasons.push('Good domain expertise');
      }
      
      if (metrics.availability > 0.8) {
        reasons.push('High availability');
      } else if (metrics.availability > 0.6) {
        reasons.push('Good availability');
      }
      
      // Add ML prediction reasoning
      if (metrics.ml_prediction > 0.3) {
        reasons.push('Strong ML prediction score');
      } else if (metrics.ml_prediction > 0.2) {
        reasons.push('Good ML prediction score');
      }
      
      // Add overall score reasoning
      if (score > 0.3) {
        reasons.push('High overall match score');
      } else if (score > 0.2) {
        reasons.push('Good overall match score');
      }
      
      return reasons.length > 0 ? reasons.join(', ') : 'Based on AI analysis';
    },
    
    calculateSkillsMatch(metrics) {
      if (!metrics) return 'N/A';
      
      // Use the skills_match from ML engine directly
      if (metrics.skills_match !== undefined) {
        return `${Math.round(metrics.skills_match * 100)}%`;
      }
      
      // Fallback calculation if skills_match not available
      const clarityWeight = 0.4;
      const resolutionWeight = 0.6;
      const skillsMatch = (metrics.clarity * clarityWeight + metrics.resolution * resolutionWeight);
      
      return `${Math.round(skillsMatch)}%`;
    },

    // Safely render percentages; shows 'N/A%' only when value is null/undefined/NaN
    formatPercent(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return 'N/A%';
      }
      return `${Number(value)}%`;
    },
    
    // Additional AI methods from mixin
    openAIRecommendations() {
      this.aiTaskData = this.prepareAITaskData();
      this.showAIRecommendations = true;
    },
    
    prepareAITaskData() {
      // Use the first team member's data as template
      const member = this.teamMembers[0] || {};
      return {
        title: member.auditTitle || 'Audit Assignment',
        description: member.scope || 'Audit scope and objectives',
        domain: member.businessUnit || 'General',
        severity: 'Medium',
        departmentId: 1,
        objective: member.objective || 'Audit objectives',
        responsibilities: member.responsibilities || 'Audit responsibilities'
      };
    },
    isTabEnabled(index) {
      // Only allow current tab and previous tabs
      if (index === 0) return true;
      if (index === this.currentTab) return true;
      // Only enable next tab if all previous are completed
      if (index === this.currentTab + 1 && this.canProceed) return true;
      // Otherwise, disable
      return false;
    },
    async fetchBusinessUnits() {
      try {
        const res = await axios.get(API_ENDPOINTS.BUSINESS_UNITS);
        this.availableBusinessUnits = res.data;
        this.filteredBusinessUnits = res.data;
      } catch (e) {
        console.error('Error fetching business units:', e);
        this.availableBusinessUnits = [];
        this.filteredBusinessUnits = [];
      }
    },
    toggleBusinessUnitDropdown(member) {
      member.showBusinessUnitDropdown = !member.showBusinessUnitDropdown;
      if (member.showBusinessUnitDropdown) {
        member.filteredBusinessUnits = this.availableBusinessUnits;
      }
    },
    filterBusinessUnits(member) {
      const searchTerm = this.businessUnitSearchTerm.toLowerCase();
      member.filteredBusinessUnits = this.availableBusinessUnits.filter(unit =>
        unit.toLowerCase().includes(searchTerm)
      );
    },
    toggleBusinessUnit(member, unit) {
      if (member.businessUnits.includes(unit)) {
        member.businessUnits = member.businessUnits.filter(u => u !== unit);
      } else {
        member.businessUnits.push(unit);
      }
    },
    removeBusinessUnit(member, unit) {
      member.businessUnits = member.businessUnits.filter(u => u !== unit);
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
    },
    'currentTab': function() {
      if (this.isReviewTab) { // Review & Assign tab
        this.$nextTick(() => {
          this.resetCollapsibleSections();
          console.log('Reset collapsible sections for Review & Assign tab');
        });
      }
    }
  },
  mounted() {
    this.fetchFrameworks();
    this.fetchUsers();
    this.fetchBusinessUnits();
    // Ensure team member type is set correctly based on audit type
    this.onAuditTypeChange();
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
.required-asterisk {
  color: #dc2626;
  font-weight: bold;
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
  transition: max-height 0.3s ease, opacity 0.3s ease, padding 0.3s ease;
  overflow: hidden;
  max-height: 2000px; /* Adjust based on your content */
  opacity: 1;
}

.section-content.collapsed {
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
  border: none;
  opacity: 0;
  /* Only disable pointer events inside the collapsed panel itself */
  pointer-events: none;
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
.narrow-dropdown {
  max-width: 500px;
  overflow: visible !important;
}
.narrow-dropdown .dropdown-container {
  width: 100% !important;
  min-width: 0 !important;
  max-width: 100% !important;
  overflow: visible !important;
}
.empty-review-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  background-color: #f9fafb;
  border-radius: 8px;
  border: 1px dashed #d1d5db;
  margin: 2rem 0;
}

.empty-review-page p {
  font-size: 1.2rem;
  color: #6b7280;
  text-align: center;
}
.team-review-section {
  margin-top: 1.5rem;
}

.team-review-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.review-content {
  padding: 1rem 0;
}

.review-item {
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
}

.review-label {
  font-weight: 500;
  color: #64748b;
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
}

.review-value {
  color: #1e293b;
  font-size: 1rem;
  line-height: 1.5;
}

.edit-section-btn, .save-section-btn {
  padding: 0.5rem 1.25rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;
}

.edit-section-btn {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  color: #1e293b;
}

.edit-section-btn:hover {
  background: #f1f5f9;
}

.save-section-btn {
  background: #2563eb;
  border: none;
  color: white;
}

.save-section-btn:hover {
  background: #1d4ed8;
}

.review-reports-list {
  margin-top: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.review-report-item {
  padding: 0.5rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.dynamic-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.dynamic-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
}
.review-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem;
}

.expand-all-btn {
  padding: 0.5rem 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #1e293b;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.expand-all-btn:hover {
  background: #f1f5f9;
  transform: translateY(-1px);
}
.tab-button.disabled {
  opacity: 0.5;
  pointer-events: none;
}

/* Ensure the bottom navigation is always clickable and above any collapsing content */
.tab-navigation {
  position: relative;
  z-index: 5;
}

.nav-button.assign {
  position: relative;
  z-index: 6; /* higher than collapsing sections or overlays in page flow */
}

/* Team Creation Styles */
.add-member-btn {
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
  transition: all 0.3s ease;
}

.add-member-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.plus-icon {
  font-size: 18px;
  font-weight: bold;
}

.team-member-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.team-member-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border-color: #cbd5e1;
}

.remove-member-btn {
  background: #ef4444;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 16px;
  transition: all 0.2s ease;
}

.remove-member-btn:hover {
  background: #dc2626;
  transform: translateY(-1px);
}

/* AI Recommendation Styles */
.field-with-ai {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  position: relative;
  z-index: 1;
}

.ai-recommendation-btn {
  background: #f1f5f9;
  color: #64748b;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s ease;
  min-width: 40px;
  height: 40px;
  justify-content: center;
}

.ai-recommendation-btn:hover:not(:disabled) {
  background: #e2e8f0;
  color: #475569;
  border-color: #cbd5e1;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Fix for reviewer field positioning to prevent overlap with policy dropdown */
.reviewer-field {
  position: relative;
  z-index: 1;
}

.reviewer-field .dropdown-container {
  position: relative;
  z-index: 1;
}

/* Ensure policy dropdown has higher z-index than reviewer field */
.dynamic-field-col:first-child .dropdown-container {
  position: relative;
  z-index: 10;
}

.dynamic-field-col:first-child .dropdown-menu {
  z-index: 1000 !important;
}

.ai-recommendation-btn:disabled {
  background: #f8fafc;
  color: #cbd5e1;
  border-color: #f1f5f9;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.ai-recommendation-btn i {
  font-size: 14px;
}

/* AI Recommendations Panel Styles */
.ai-recommendations-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.ai-recommendations-panel {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.ai-panel-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ai-panel-header h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.ai-panel-content {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.recommendation-item {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 15px;
  background: #f8fafc;
  transition: all 0.2s;
}

.recommendation-item:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}

.recommendation-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.recommendation-header i {
  color: #667eea;
  font-size: 16px;
}

.recommendation-title {
  font-weight: 600;
  color: #2d3748;
  font-size: 16px;
}

.recommendation-content {
  margin-bottom: 15px;
}

.recommendation-content p {
  margin: 5px 0;
  color: #4a5568;
  font-size: 14px;
}

.recommendation-content strong {
  color: #2d3748;
  font-weight: 600;
}

.breakdown-details {
  margin-top: 10px;
  padding: 10px;
  background: #f1f5f9;
  border-radius: 6px;
  border-left: 3px solid #667eea;
}

.breakdown-details p {
  margin: 0 0 8px 0;
  font-weight: 600;
  color: #2d3748;
}

.breakdown-details ul {
  margin: 0;
  padding-left: 20px;
}

.breakdown-details li {
  margin: 3px 0;
  color: #4a5568;
  font-size: 13px;
}

.recommendation-actions {
  display: flex;
  justify-content: flex-end;
}

.select-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.select-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.select-btn:active {
  transform: translateY(0);
}

.no-recommendations {
  text-align: center;
  padding: 40px 20px;
  color: #6b7280;
}

.no-recommendations i {
  font-size: 48px;
  margin-bottom: 15px;
  color: #d1d5db;
}

.no-recommendations p {
  margin: 0;
  font-size: 16px;
}

/* AI Recommendations Sidebar Styles */
.ai-recommendations-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.3);
  z-index: 999;
  display: flex;
  justify-content: flex-end;
}

.ai-recommendations-sidebar {
  position: relative;
  width: 400px;
  height: 100vh;
  background: var(--card-bg);
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  background: var(--primary-color);
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.recommendation-card {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--card-bg);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
  overflow: hidden;
  margin-bottom: 16px;
}

.recommendation-card:hover {
  border-color: var(--primary-color);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.1);
  transform: translateY(-2px);
}

.card-header {
  padding: 16px;
  background: var(--secondary-color);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recommendation-rank {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rank-number {
  background: var(--primary-color);
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.rank-info h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.confidence-badge {
  background: #e0f2fe;
  color: #0277bd;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.card-content {
  padding: 16px;
}

.score-display {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.score-item {
  flex: 1;
  text-align: center;
  padding: 8px;
  background: var(--secondary-color);
  border-radius: 6px;
}

.score-label {
  display: block;
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.score-value {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-top: 2px;
}

.reasoning-section {
  margin-bottom: 16px;
}

.reasoning-section h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.reasoning-section p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.metrics-section h5 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: var(--secondary-color);
  border-radius: 4px;
}

.metric-label {
  font-size: 11px;
  color: var(--text-secondary);
  font-weight: 500;
}

.metric-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.empty-state {
  text-align: center;
  color: var(--text-secondary);
  padding: 40px 20px;
}


.empty-state h4 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.empty-state p {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
}

/* AI Audit Styles */


/* Policy Selection Styles */
.tab-description {
  color: #666;
  margin-bottom: 20px;
  font-size: 14px;
}

.policy-selection-section {
  margin-top: 20px;
}

.policy-info-card {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  margin-top: 20px;
}

.policy-info-card h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.policy-description {
  color: #666;
  margin-bottom: 15px;
  line-height: 1.5;
}

.policy-meta {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.policy-meta span {
  background: #e9ecef;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #495057;
}

/* Policy Information Display Styles */
.policy-info-display {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.policy-info-display h4 {
  margin: 0 0 15px 0;
  color: #495057;
  font-size: 16px;
  font-weight: 600;
}

.policy-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.policy-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.policy-label {
  font-weight: 600;
  color: #495057;
  min-width: 80px;
}

.policy-value {
  color: #212529;
  font-weight: 500;
}

.ai-status {
  color: #28a745;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 5px;
}

.ai-status i {
  color: #28a745;
}

</style>
