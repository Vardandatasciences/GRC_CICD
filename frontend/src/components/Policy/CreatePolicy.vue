<template>
  <div class="create-policy-container" @click="closeAllEntityDropdowns">
    <!-- Loading Overlay -->


    <!-- Error Message -->
    <div v-if="error" class="error-message">
      {{ error }}
      <button class="close-btn" @click="error = null">✕</button>
    </div>

    <!-- Policy Form Section -->
      <div v-if="!showApprovalForm">
        <div class="policy-creation-header">
          <div class="policy-intro">
            <h2>Create New Policy</h2>
            <p>Establish comprehensive policies to ensure compliance and governance across your organization.</p>
            
            <!-- Framework Selection - Moved up to reduce white space -->
            <div class="framework-container-top">
              <label>Framework <span class="required-star">*</span></label>
              <CustomDropdown :config="frameworkDropdownConfig" v-model="selectedFramework" />
              <div class="tooltip-container">
                <span class="info-icon">🛈</span>
                <div class="tooltip-text">Select an existing framework or create a new one to associate with your policy.</div>
              </div>
            </div>
            
            <!-- Framework Creation Form - Insert directly after the dropdown -->
            <div v-if="showFrameworkForm" class="framework-form-inline">
              <div class="framework-form">
                <div class="framework-header">
                  <h3>Create New Framework</h3>
                  <div class="framework-note">
                    <i class="fas fa-info-circle"></i>
                    <span>After creating the framework, you can add policies and subpolicies. You can also return to this form later to make corrections.</span>
                  </div>
                </div>
                
                <div class="form-group policy-name">
                  <label>Framework Name <span class="required-star">*</span></label>
                  <input
                    type="text"
                    placeholder="Enter Framework name"
                    v-model="newFramework.FrameworkName"
                    @blur="validateFrameworkName"
                    @input="clearFrameworkNameError"
                    :class="{ 'error-field': frameworkNameError }"
                    title="Enter a descriptive name for your framework"
                  />
                  <div v-if="frameworkNameError" class="error-message">{{ frameworkNameError }}</div>
                  <div v-else class="helper-text">Enter a descriptive name for your framework</div>
                </div>
                
                <div class="form-row single-column">
                  <div class="form-group description">
                    <label>Description <span class="required-star">*</span></label>
                    <div class="textarea-container">
                      <textarea
                        placeholder="Enter framework description"
                        v-model="newFramework.FrameworkDescription"
                        rows="3"
                        title="Describe the purpose, scope, and objectives of this framework"
                        maxlength="1000"
                      ></textarea>
                      <div class="character-counter" :class="getCharacterCounterClass(newFramework.FrameworkDescription, 1000)">
                        {{ (newFramework.FrameworkDescription || '').length }}/1000
                      </div>
                    </div>
                    <div class="helper-text">Describe the purpose, scope, and objectives of this framework</div>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group internal-external">
                    <label>Internal/External <span class="required-star">*</span></label>
                    <select
                      v-model="newFramework.InternalExternal"
                      @change="handleInternalExternalChange"
                      title="Select whether this framework is for internal or external use"
                    >
                      <option value="">Select Type</option>
                      <option value="Internal">Internal</option>
                      <option value="External">External</option>
                    </select>
                    <div class="helper-text">Select whether this framework is for internal or external use</div>
                  </div>
                  <div class="form-group version">
                    <label>Identifier <span class="required-star">*</span>
                      <span v-if="newFramework.InternalExternal === 'Internal'" class="auto-generated-label">
                        (Auto-generated)
                      </span>
                      <span v-else-if="newFramework.InternalExternal === 'External'" class="manual-entry-label">
                        (Manual entry)
                      </span>
                    </label>
                    <input
                      type="text"
                      placeholder="Enter Identifier"
                      v-model="newFramework.Identifier"
                      :readonly="newFramework.InternalExternal === 'Internal'"
                      :class="{ 'readonly-field': newFramework.InternalExternal === 'Internal' }"
                      title="Use a unique code like 'FW-001' or 'ISO-27001'"
                    />
                    <div class="helper-text">
                      <span v-if="newFramework.InternalExternal === 'Internal'">Auto-generated identifier for internal frameworks</span>
                      <span v-else-if="newFramework.InternalExternal === 'External'">Enter a unique identifier for external frameworks</span>
                      <span v-else>Use a unique code like 'FW-001' or 'ISO-27001'</span>
                    </div>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group category">
                    <label>Category <span class="required-star">*</span></label>
                    <input
                      type="text"
                      placeholder="Enter category"
                      v-model="newFramework.Category"
                      title="e.g., Security, Compliance, Risk Management, etc."
                    />
                    <div class="helper-text">e.g., Security, Compliance, Risk Management, etc.</div>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group upload">
                    <label>Upload Document</label>
                    <div class="upload-controls">
                      <span>{{ newFramework.DocURL ? newFramework.DocURL.name : 'Choose File' }}</span>
                      <button class="browse-btn" type="button" @click="() => handleFrameworkFileUpload()" title="Browse and select a document file">Browse</button>
                    </div>
                    <input type="file" ref="frameworkFileInput" style="display:none" @change="onFrameworkFileChange" />
                    <div class="helper-text">Upload a supporting document for this framework (optional)</div>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group date">
                    <label>Effective Start Date <span class="required-star">*</span></label>
                    <input
                      type="date"
                      v-model="newFramework.StartDate"
                      title="Date when the framework implementation begins"
                    />
                    <div class="helper-text">Date when the framework implementation begins</div>
                  </div>
                  <div class="form-group date">
                    <label>Effective End Date</label>
                    <input
                      type="date"
                      v-model="newFramework.EndDate"
                      title="Date when the framework expires or requires review"
                    />
                    <div class="helper-text">Date when the framework expires or requires review</div>
                  </div>
                </div>
                <div class="form-actions">
                  <button class="submitt-btn" @click="handleCreateFramework">
                    <i class="fas fa-arrow-right"></i>
                    Continue to Policies
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="enterprise-card" v-if="!selectedFramework && !showFrameworkForm">
            <h3>Enterprise-Grade Policy Management</h3>
            <p>Streamline your compliance efforts with our comprehensive policy management system. Built for teams that need to maintain rigorous standards while moving fast.</p>
          </div>
        </div>
      
      <!-- Policy Best Practices Section -->
      <div class="policy-best-practices-section" v-if="!selectedFramework && !showFrameworkForm">
        <div class="policy-best-practices">
          <h3>Policy Creation Best Practices</h3>
          <ul class="best-practices-list">
            <li><span class="check-icon">✓</span> Align policies with your organization's risk appetite and business objectives</li>
            <li><span class="check-icon">✓</span> Ensure policies are clear, concise, and easy to understand for all stakeholders</li>
            <li><span class="check-icon">✓</span> Review and update policies regularly to maintain compliance with evolving regulations</li>
            <li><span class="check-icon">✓</span> Include roles and responsibilities for policy implementation and enforcement</li>
            <li><span class="check-icon">✓</span> Document exceptions and approval processes for special circumstances</li>
          </ul>
        </div>
      </div>
      
      <div class="key-features-section" v-if="!selectedFramework && !showFrameworkForm">
        <h3>Key Features</h3>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon document-icon">📄</div>
            <div class="feature-content">
              <h4>Automated Compliance</h4>
              <p>Automatically map policies to compliance requirements and track adherence in real-time.</p>
            </div>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon clock-icon">🕒</div>
            <div class="feature-content">
              <h4>Version Control</h4>
              <p>Maintain complete audit trails with automatic versioning and change tracking.</p>
            </div>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon people-icon">👥</div>
            <div class="feature-content">
              <h4>Collaborative Workflows</h4>
              <p>Enable team collaboration with review processes, approvals, and stakeholder notifications.</p>
            </div>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon lock-icon">🔒</div>
            <div class="feature-content">
              <h4>Secure by Design</h4>
              <p>Enterprise-grade security with role-based access control and encrypted storage.</p>
            </div>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon bolt-icon">⚡</div>
            <div class="feature-content">
              <h4>Quick Deployment</h4>
              <p>Deploy policies organization-wide instantly with customizable distribution rules.</p>
            </div>
          </div>
        </div>
        
      </div>

      <!-- Original framework form container - now hidden -->
      <div v-if="false" class="framework-form-container">
        <div class="framework-form">
          <div class="framework-header">
            <h3>Create New Framework</h3>
            <div class="framework-note">
              <i class="fas fa-info-circle"></i>
              <span>After creating the framework, you can add policies and subpolicies. You can also return to this form later to make corrections.</span>
            </div>
          </div>
          
              <div class="form-group policy-name">
              <label>Framework Name <span class="required-star">*</span></label>
                <input
                  type="text"
                  placeholder="Enter Framework name"
                  v-model="newFramework.FrameworkName"
                  @blur="validateFrameworkName"
                  @input="clearFrameworkNameError"
                  :class="{ 'error-field': frameworkNameError }"
                  title="Enter a descriptive name for your framework"
                />
              <div v-if="frameworkNameError" class="error-message">{{ frameworkNameError }}</div>
              <div v-else class="helper-text">Enter a descriptive name for your framework</div>
              </div>
          
          <div class="form-row single-column">
            <div class="form-group description">
              <label>Description <span class="required-star">*</span></label>
              <div class="textarea-container">
                <textarea
                  placeholder="Enter framework description"
                  v-model="newFramework.FrameworkDescription"
                  rows="3"
                  title="Describe the purpose, scope, and objectives of this framework"
                  maxlength="1000"
                ></textarea>
                <div class="character-counter" :class="getCharacterCounterClass(newFramework.FrameworkDescription, 1000)">
                  {{ (newFramework.FrameworkDescription || '').length }}/1000
                </div>
              </div>
              <div class="helper-text">Describe the purpose, scope, and objectives of this framework</div>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group internal-external">
              <label>Internal/External <span class="required-star">*</span></label>
              <select
                v-model="newFramework.InternalExternal"
                @change="handleInternalExternalChange"
                title="Select whether this framework is for internal or external use"
              >
                <option value="">Select Type</option>
                <option value="Internal">Internal</option>
                <option value="External">External</option>
              </select>
              <div class="helper-text">Select whether this framework is for internal or external use</div>
            </div>
            <div class="form-group version">
              <label>Identifier <span class="required-star">*</span>
                <span v-if="newFramework.InternalExternal === 'Internal'" class="auto-generated-label">
                  (Auto-generated)
                </span>
                <span v-else-if="newFramework.InternalExternal === 'External'" class="manual-entry-label">
                  (Manual entry)
                </span>
              </label>
              <input
                type="text"
                placeholder="Enter Identifier"
                v-model="newFramework.Identifier"
                :readonly="newFramework.InternalExternal === 'Internal'"
                :class="{ 'readonly-field': newFramework.InternalExternal === 'Internal' }"
                title="Use a unique code like 'FW-001' or 'ISO-27001'"
              />
              <div class="helper-text">
                <span v-if="newFramework.InternalExternal === 'Internal'">Auto-generated identifier for internal frameworks</span>
                <span v-else-if="newFramework.InternalExternal === 'External'">Enter a unique identifier for external frameworks</span>
                <span v-else>Use a unique code like 'FW-001' or 'ISO-27001'</span>
              </div>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group category">
              <label>Category <span class="required-star">*</span></label>
              <input
                type="text"
                placeholder="Enter category"
                v-model="newFramework.Category"
                title="e.g., Security, Compliance, Risk Management, etc."
              />
              <div class="helper-text">e.g., Security, Compliance, Risk Management, etc.</div>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group upload">
              <label>Upload Document</label>
              <div class="upload-controls">
                <span>{{ newFramework.DocURL ? newFramework.DocURL.name : 'Choose File' }}</span>
                <button class="browse-btn" type="button" @click="() => handleFrameworkFileUpload()" title="Browse and select a document file">Browse</button>
              </div>
              <input type="file" ref="frameworkFileInput" style="display:none" @change="onFrameworkFileChange" />
              <div class="helper-text">Upload a supporting document for this framework (optional)</div>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group date">
              <label>Effective Start Date <span class="required-star">*</span></label>
              <input
                type="date"
                v-model="newFramework.StartDate"
                title="Date when the framework implementation begins"
              />
              <div class="helper-text">Date when the framework implementation begins</div>
            </div>
            <div class="form-group date">
              <label>Effective End Date</label>
              <input
                type="date"
                v-model="newFramework.EndDate"
                title="Date when the framework expires or requires review"
              />
              <div class="helper-text">Date when the framework expires or requires review</div>
            </div>
          </div>
          <div class="form-actions">
            <button class="submitt-btn" @click="handleCreateFramework">
              <i class="fas fa-arrow-right"></i>
              Continue to Policies
            </button>
          </div>
        </div>
      </div>

      <!-- Policy Actions - Show when framework is selected -->
      <!-- (Removed selected framework info and change button) -->

      <!-- Policy Stepper and Policy Form: Only show after framework is selected -->
      <div v-if="selectedFramework && !showFrameworkForm">
        <div class="policy-header-section">
          <h3 style="margin: 0;">Policy Creation</h3>
          <button 
            v-if="selectedFramework === '__new__'" 
            class="back-to-framework-btn" 
            @click="goBackToFramework"
            title="Return to framework form to make corrections"
          >
            <i class="fas fa-arrow-left"></i> Back to Framework
          </button>
        </div>
        <div class="subpolicy-stepper">
          
          <div
            v-for="(policy, idx) in policiesForm"
            :key="idx"
            class="subpolicy-step"
            :class="{ active: selectedPolicyIdx === idx }"
            @click="selectedPolicyIdx = idx"
          >
            {{ policy.PolicyName || `Policy ${idx + 1}` }}
            <button class="remove-btn" @click.stop="handleRemovePolicy(idx)" title="Remove Policy">✕</button>
        </div>
          <button class="add-subpolicy-step-btn" @click="handleAddPolicy">
            + Add Policy
        </button>
      </div>
      <!-- Policies and Subpolicies Grid -->
        <div class="policy-rows full-width-policy-rows" v-if="selectedPolicyIdx !== null && policiesForm[selectedPolicyIdx]">
          <div class="policy-row">
            <div 
              class="policy-card full-width-policy-card selected-policy"
              style="cursor: pointer;"
            >
            <div class="policy-card-header">
                <b style="font-size: 0.95rem">{{ policiesForm[selectedPolicyIdx].PolicyName || `Policy ${selectedPolicyIdx + 1}` }}</b>
                <button class="remove-btn" @click.stop="handleRemovePolicy(selectedPolicyIdx)" title="Remove Policy">✕</button>
            </div>
              <!-- Policy Card Fields (now using policiesForm[selectedPolicyIdx]) -->
            <div class="policy-form-row">
              <div class="form-group">
                <label>Policy Name <span class="required-star">*</span></label>
                <div class="input-with-icon">
                  <input
                    type="text"
                    placeholder="Enter policy name"
                    v-model="policiesForm[selectedPolicyIdx].PolicyName"
                    @input="handlePolicyChange(selectedPolicyIdx, 'PolicyName', $event.target.value)"
                    title="Use a clear, descriptive name that identifies the policy's purpose"
                  />
                </div>
                <div class="helper-text">Use a clear, descriptive name that identifies the policy's purpose</div>
              </div>
              <div class="form-group">
                <label>Policy Identifier <span class="required-star">*</span>
                  <span v-if="isInternalFramework()" class="auto-generated-label">
                    (Auto-generated)
                  </span>
                  <span v-else class="manual-entry-label">
                    (Manual entry)
                  </span>
                </label>
                <div class="input-with-icon">
                  <input
                    type="text"
                    placeholder="Enter policy identifier"
                    v-model="policiesForm[selectedPolicyIdx].Identifier"
                    :readonly="isInternalFramework()"
                    :class="{ 'readonly-field': isInternalFramework() }"
                    title="Use a unique code like 'POL-001' or 'SEC-AUTH-01'"
                  />
                </div>
                <div class="helper-text">Use a unique code like 'POL-001' or 'SEC-AUTH-01'</div>
              </div>
            </div>
            <div class="form-group description">
              <label>Description <span class="required-star">*</span></label>
              <div class="textarea-container">
                <textarea
                  placeholder="Enter policy description"
                  v-model="policiesForm[selectedPolicyIdx].PolicyDescription"
                  @input="handlePolicyChange(selectedPolicyIdx, 'PolicyDescription', $event.target.value)"
                  rows="3"
                  title="Describe the policy's purpose, requirements, and key provisions"
                  maxlength="1000"
                ></textarea>
                <div class="character-counter" :class="getCharacterCounterClass(policiesForm[selectedPolicyIdx].PolicyDescription, 1000)">
                  {{ (policiesForm[selectedPolicyIdx].PolicyDescription || '').length }}/1000
                </div>
              </div>
              <div class="helper-text">Describe the policy's purpose, requirements, and key provisions</div>
            </div>
            <div class="policy-form-row">
              <div class="form-group">
                <label>Scope <span class="required-star">*</span></label>
                <div class="input-with-icon">
                  <input
                    type="text"
                    placeholder="Enter policy scope"
                    v-model="policiesForm[selectedPolicyIdx].Scope"
                    @input="handlePolicyChange(selectedPolicyIdx, 'Scope', $event.target.value)"
                    title="Specify what areas, processes, or systems this policy applies to"
                  />
                </div>
                <div class="helper-text">Specify what areas, processes, or systems this policy applies to</div>
              </div>
              <div class="form-group">
                <label>Department <span class="required-star">*</span></label>
                <div class="department-multi-select" @click.stop>
                  <div class="department-dropdown">
                    <div   
                      class="selected-departments" 
                      :class="{ active: policiesForm[selectedPolicyIdx].showDepartmentsDropdown }"
                      @click="toggleDepartmentsDropdown(selectedPolicyIdx)"
                    >
                      <div class="department-content">
                        <span v-if="isAllDepartmentsSelected(selectedPolicyIdx)" class="department-tag all-tag">
                          All Departments
                        </span>
                        <span v-else-if="getSelectedDepartmentsCount(selectedPolicyIdx) === 0" class="placeholder">
                          Select departments...
                        </span>
                        <span v-else class="department-count">
                          {{ getSelectedDepartmentsCount(selectedPolicyIdx) }} department(s) selected
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policiesForm[selectedPolicyIdx].showDepartmentsDropdown" class="departments-options">
                      <div 
                        v-for="department in departments" 
                        :key="department.id" 
                        :class="['department-option', { 'all-option': department.id === 'all' }]"
                        @click="selectDepartment(selectedPolicyIdx, department.id)"
                      >
                        <input 
                          type="checkbox" 
                          :checked="department.id === 'all' ? isAllDepartmentsSelected(selectedPolicyIdx) : getSelectedDepartmentIds(selectedPolicyIdx).includes(department.id)"
                          @change="handleDepartmentSelection(selectedPolicyIdx, department.id, $event.target.checked)"
                          @click.stop
                        />
                        <span class="department-label">{{ department.name }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="helper-text">Select the departments this policy applies to</div>
              </div>
            </div>
            <div class="policy-form-row objective-applicability-row">
              <div class="form-group description">
                <label>Objective <span class="required-star">*</span></label>
                <div class="textarea-container">
                  <textarea
                    placeholder="Enter policy objective"
                    v-model="policiesForm[selectedPolicyIdx].Objective"
                    @input="handlePolicyChange(selectedPolicyIdx, 'Objective', $event.target.value)"
                    rows="3"
                    title="Explain what this policy is designed to accomplish and its expected outcomes"
                    maxlength="1000"
                  ></textarea>
                  <div class="character-counter" :class="getCharacterCounterClass(policiesForm[selectedPolicyIdx].Objective, 1000)">
                    {{ (policiesForm[selectedPolicyIdx].Objective || '').length }}/1000
                  </div>
                </div>
                <div class="helper-text">Explain what this policy is designed to accomplish and its expected outcomes</div>
              </div>
              
            </div>
            <div class="policy-form-row date-row">
              <div class="form-group">
                <label>Coverage Rate (%) <span class="required-star">*</span></label>
                <div class="input-with-icon">
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="0.01"
                    placeholder="Enter coverage rate"
                    v-model="policiesForm[selectedPolicyIdx].CoverageRate"
                    @input="handlePolicyChange(selectedPolicyIdx, 'CoverageRate', $event.target.value)"
                    title="Specify how much of the target area this policy covers (0-100%)"
                  />
                </div>
                <div class="helper-text">Specify how much of the target area this policy covers (0-100%)</div>
              </div>
              <div class="form-group">
                <label>Applicability <span class="required-star">*</span></label>
                <div class="input-with-icon">
                  <input
                    type="text"
                    placeholder="Enter applicability"
                    v-model="policiesForm[selectedPolicyIdx].Applicability"
                    @input="handlePolicyChange(selectedPolicyIdx, 'Applicability', $event.target.value)"
                    title="Define the target audience, roles, or entities this policy affects"
                  />
                </div>
                <div class="helper-text">Define the target audience, roles, or entities this policy affects</div>
              </div>
            </div>
            <div class="policy-form-row">
              <div class="form-group">
                <label>Policy Type <span class="required-star">*</span></label>
                <div class="policy-type-multi-select" @click.stop>
                  <div class="policy-type-dropdown">
                    <div   
                      class="selected-policy-type" 
                      :class="{ active: policiesForm[selectedPolicyIdx].showPolicyTypeDropdown }"
                      @click="togglePolicyTypeDropdown(selectedPolicyIdx)"
                    >
                      <div class="policy-type-content">
                        <span v-if="policiesForm[selectedPolicyIdx].PolicyType" class="policy-type-value">
                          {{ policiesForm[selectedPolicyIdx].PolicyType }}
                        </span>
                        <span v-else class="placeholder">
                          Search or enter new policy type
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policiesForm[selectedPolicyIdx].showPolicyTypeDropdown" class="policy-type-options">
                      <!-- Search Input -->
                      <div class="search-input-container">
                        <input
                          v-model="policiesForm[selectedPolicyIdx].policyTypeSearch"
                          type="text"
                          placeholder="Search or type new policy type..."
                          class="search-input"
                          @input="filterPolicyTypes()"
                          @keyup.enter="createNewPolicyType(selectedPolicyIdx)"
                        />
                      </div>
                      <!-- Existing Options -->
                      <div 
                        v-for="type in getFilteredPolicyTypes(selectedPolicyIdx)" 
                        :key="type" 
                        class="policy-type-option"
                        @click="selectPolicyType(selectedPolicyIdx, type)"
                      >
                        <span class="policy-type-label">{{ type }}</span>
                      </div>
                      <!-- Create New Option -->
                      <div 
                        v-if="policiesForm[selectedPolicyIdx].policyTypeSearch && !getFilteredPolicyTypes(selectedPolicyIdx).includes(policiesForm[selectedPolicyIdx].policyTypeSearch)"
                        class="policy-type-option create-new-option"
                        @click="createNewPolicyType(selectedPolicyIdx)"
                      >
                        <i class="fas fa-plus"></i>
                        <span class="policy-type-label">Create "{{ policiesForm[selectedPolicyIdx].policyTypeSearch }}"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="helper-text">e.g., Security Policy, HR Policy, Financial Policy, etc.</div>
              </div>
              <div class="form-group">
                <label>Policy Category <span class="required-star">*</span></label>
                <div class="policy-category-multi-select" @click.stop>
                  <div class="policy-category-dropdown">
                    <div   
                      class="selected-policy-category" 
                      :class="{ active: policiesForm[selectedPolicyIdx].showPolicyCategoryDropdown }"
                      @click="togglePolicyCategoryDropdown(selectedPolicyIdx)"
                    >
                      <div class="policy-category-content">
                        <span v-if="policiesForm[selectedPolicyIdx].PolicyCategory" class="policy-category-value">
                          {{ policiesForm[selectedPolicyIdx].PolicyCategory }}
                        </span>
                        <span v-else class="placeholder">
                          Search or enter new category
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policiesForm[selectedPolicyIdx].showPolicyCategoryDropdown" class="policy-category-options">
                      <!-- Search Input -->
                      <div class="search-input-container">
                        <input
                          v-model="policiesForm[selectedPolicyIdx].policyCategorySearch"
                          type="text"
                          placeholder="Search or type new category..."
                          class="search-input"
                          @input="filterPolicyCategories()"
                          @keyup.enter="createNewPolicyCategory(selectedPolicyIdx)"
                        />
                      </div>
                      <!-- Existing Options -->
                      <div 
                        v-for="category in getFilteredPolicyCategories(selectedPolicyIdx)" 
                        :key="category" 
                        class="policy-category-option"
                        @click="selectPolicyCategory(selectedPolicyIdx, category)"
                      >
                        <span class="policy-category-label">{{ category }}</span>
                      </div>
                      <!-- Create New Option -->
                      <div 
                        v-if="policiesForm[selectedPolicyIdx].policyCategorySearch && !getFilteredPolicyCategories(selectedPolicyIdx).includes(policiesForm[selectedPolicyIdx].policyCategorySearch)"
                        class="policy-category-option create-new-option"
                        @click="createNewPolicyCategory(selectedPolicyIdx)"
                      >
                        <i class="fas fa-plus"></i>
                        <span class="policy-category-label">Create "{{ policiesForm[selectedPolicyIdx].policyCategorySearch }}"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="helper-text">Choose a category that best describes this policy's focus area</div>
              </div>
            </div>
            <div class="policy-form-row date-row">
              <div class="form-group">
                <label>Policy Sub Category <span class="required-star">*</span></label>
                <div class="policy-subcategory-multi-select" @click.stop>
                  <div class="policy-subcategory-dropdown">
                    <div   
                      class="selected-policy-subcategory" 
                      :class="{ active: policiesForm[selectedPolicyIdx].showPolicySubCategoryDropdown }"
                      @click="togglePolicySubCategoryDropdown(selectedPolicyIdx)"
                    >
                      <div class="policy-subcategory-content">
                        <span v-if="policiesForm[selectedPolicyIdx].PolicySubCategory" class="policy-subcategory-value">
                          {{ policiesForm[selectedPolicyIdx].PolicySubCategory }}
                        </span>
                        <span v-else class="placeholder">
                          Search or enter new sub category
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policiesForm[selectedPolicyIdx].showPolicySubCategoryDropdown" class="policy-subcategory-options">
                      <!-- Search Input -->
                      <div class="search-input-container">
                        <input
                          v-model="policiesForm[selectedPolicyIdx].policySubCategorySearch"
                          type="text"
                          placeholder="Search or type new sub category..."
                          class="search-input"
                          @input="filterPolicySubCategories()"
                          @keyup.enter="createNewPolicySubCategory(selectedPolicyIdx)"
                        />
                      </div>
                      <!-- Existing Options -->
                      <div 
                        v-for="subCategory in getFilteredPolicySubCategories(selectedPolicyIdx)" 
                        :key="subCategory" 
                        class="policy-subcategory-option"
                        @click="selectPolicySubCategory(selectedPolicyIdx, subCategory)"
                      >
                        <span class="policy-subcategory-label">{{ subCategory }}</span>
                      </div>
                      <!-- Create New Option -->
                      <div 
                        v-if="policiesForm[selectedPolicyIdx].policySubCategorySearch && !getFilteredPolicySubCategories(selectedPolicyIdx).includes(policiesForm[selectedPolicyIdx].policySubCategorySearch)"
                        class="policy-subcategory-option create-new-option"
                        @click="createNewPolicySubCategory(selectedPolicyIdx)"
                      >
                        <i class="fas fa-plus"></i>
                        <span class="policy-subcategory-label">Create "{{ policiesForm[selectedPolicyIdx].policySubCategorySearch }}"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="helper-text">Provide more specific classification within the selected category</div>
              </div>
              <div class="form-group entities-group">
                <label>Applicable Entities <span class="required-star">*</span></label>
                <div class="entities-multi-select" @click.stop>
                  <div class="entities-dropdown">
                    <div   
                      class="selected-entities" 
                      :class="{ active: policiesForm[selectedPolicyIdx].showEntitiesDropdown }"
                      @click="toggleEntitiesDropdown(selectedPolicyIdx)"
                    >
                      <div class="entity-content">
                        <span v-if="isAllEntitiesSelected(selectedPolicyIdx)" class="entity-tag all-tag">
                          All Locations
                        </span>
                        <span v-else-if="getSelectedEntitiesCount(selectedPolicyIdx) === 0" class="placeholder">
                          Select entities...
                        </span>
                        <span v-else class="entity-count">
                          {{ getSelectedEntitiesCount(selectedPolicyIdx) }} location(s) selected
                        </span>
                      </div>
                      <i class="fas fa-chevron-down dropdown-arrow"></i>
                    </div>
                    <div v-if="policiesForm[selectedPolicyIdx].showEntitiesDropdown" class="entities-options">
                      <div 
                        v-for="entity in entities" 
                        :key="entity.id" 
                        :class="['entity-option', { 'all-option': entity.id === 'all' }]"
                        @click="selectEntity(selectedPolicyIdx, entity.id)"
                      >
                        <input 
                          type="checkbox" 
                          :checked="entity.id === 'all' ? isAllEntitiesSelected(selectedPolicyIdx) : getSelectedEntityIds(selectedPolicyIdx).includes(entity.id)"
                          @change="handleEntitySelection(selectedPolicyIdx, entity.id, $event.target.checked)"
                          @click.stop
                        />
                        <span class="entity-label">{{ entity.label }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="helper-text">Select the locations/entities this policy applies to</div>
              </div>
            </div>
            <div class="policy-form-row date-row">
              <div class="form-group">
                <label>Start Date <span class="required-star">*</span></label>
                <div class="input-with-icon">
                  <input
                    type="date"
                    v-model="policiesForm[selectedPolicyIdx].StartDate"
                    @input="handlePolicyChange(selectedPolicyIdx, 'StartDate', $event.target.value)"
                    title="Date when this policy takes effect and becomes enforceable"
                  />
                </div>
                <div class="helper-text">Date when this policy takes effect and becomes enforceable</div>
              </div>
              <div class="form-group">
                <label>End Date</label>
                <div class="input-with-icon">
                  <input
                    type="date"
                    v-model="policiesForm[selectedPolicyIdx].EndDate"
                    @input="handlePolicyChange(selectedPolicyIdx, 'EndDate', $event.target.value)"
                    title="Date when this policy expires or requires review/renewal"
                  />
                </div>
                <div class="helper-text">Date when this policy expires or requires review/renewal</div>
              </div>
            </div>
              <button class="upload-btn" type="button" @click="() => handlePolicyFileUpload(selectedPolicyIdx)" title="Upload supporting documentation for this policy">
              <i class="fas fa-plus"></i> Upload Document
            </button>
              <span v-if="policiesForm[selectedPolicyIdx].DocURL" class="selected-file-name">{{ policiesForm[selectedPolicyIdx].DocURL.name }}</span>
              <input type="file" :ref="el => setPolicyFileInputRef(el, selectedPolicyIdx)" style="display:none" @change="e => onPolicyFileChange(e, selectedPolicyIdx)" />
            </div>
          </div>
        </div>
          </div>
 
      <!-- Subpolicy Creation Section -->
      <div v-if="selectedPolicyIdx !== null && policiesForm[selectedPolicyIdx] && !showFrameworkForm" class="subpolicy-creation-section">
        <div class="subpolicy-header-row" style="display: flex; align-items: center; justify-content: space-between;">
          <h3 style="margin: 0;">Subpolicy Creation</h3>
        </div>
        <!-- Subpolicy Stepper -->
        <div class="subpolicy-stepper">
          <div
            v-for="(sub, subIdx) in policiesForm[selectedPolicyIdx].subpolicies"
            :key="subIdx"
            class="subpolicy-step"
            :class="{ active: selectedSubPolicyIdx[selectedPolicyIdx] === subIdx }"
            @click="selectedSubPolicyIdx[selectedPolicyIdx] = subIdx"
          >
            {{ sub.SubPolicyName || `Subpolicy ${subIdx + 1}` }}
            <button class="remove-btn" @click.stop="handleRemoveSubPolicy(selectedPolicyIdx, subIdx)" title="Remove Sub Policy">✕</button>
          </div>
          <button class="add-subpolicy-step-btn" @click="handleAddSubPolicy(selectedPolicyIdx)">
            + Add Sub Policy
          </button>
        </div>
        <!-- Subpolicy Form -->
        <div v-if="selectedSubPolicyIdx[selectedPolicyIdx] !== null && policiesForm[selectedPolicyIdx].subpolicies[selectedSubPolicyIdx[selectedPolicyIdx]]" class="subpolicy-card">
              <div class="policy-card-header">
            <b style="font-size: 0.9rem">{{ policiesForm[selectedPolicyIdx].subpolicies[selectedSubPolicyIdx[selectedPolicyIdx]].SubPolicyName || `Sub Policy ${selectedSubPolicyIdx[selectedPolicyIdx] + 1}` }}</b>
            <button class="remove-btn" @click="handleRemoveSubPolicy(selectedPolicyIdx, selectedSubPolicyIdx[selectedPolicyIdx])" title="Remove Sub Policy">✕</button>
              </div>
              <div class="form-group">
                <label>Sub Policy Name <span class="required-star">*</span></label>
                <div class="input-with-icon">
                  <input
                    type="text"
                    placeholder="Enter sub policy name"
                    v-model="policiesForm[selectedPolicyIdx].subpolicies[selectedSubPolicyIdx[selectedPolicyIdx]].SubPolicyName"
                    @input="handleSubPolicyChange(selectedPolicyIdx, selectedSubPolicyIdx[selectedPolicyIdx], 'SubPolicyName', $event.target.value)"
                    title="Use a clear name that describes this sub-policy's specific focus"
                  />
                </div>
                <div class="helper-text">Use a clear name that describes this sub-policy's specific focus</div>
              </div>
              <div class="form-group">
                <label>Identifier <span class="required-star">*</span>
                  <span v-if="isInternalFramework()" class="auto-generated-label">
                    (Auto-generated)
                  </span>
                  <span v-else class="manual-entry-label">
                    (Manual entry)
                  </span>
                </label>
                <div class="input-with-icon">
                  <input
                    type="text"
                    placeholder="Enter identifier"
                    v-model="policiesForm[selectedPolicyIdx].subpolicies[selectedSubPolicyIdx[selectedPolicyIdx]].Identifier"
                    :readonly="isInternalFramework()"
                    :class="{ 'readonly-field': isInternalFramework() }"
                    title="Use a unique code like 'SUB-001' or append to parent policy ID"
                  />
                </div>
                <div class="helper-text">Use a unique code like 'SUB-001' or append to parent policy ID</div>
              </div>
              <div class="form-group">
                <label>Control <span class="required-star">*</span></label>
                <div class="textarea-container">
                  <textarea
                    type="text"
                    placeholder="Enter control"
                    v-model="policiesForm[selectedPolicyIdx].subpolicies[selectedSubPolicyIdx[selectedPolicyIdx]].Control"
                    @input="handleSubPolicyChange(selectedPolicyIdx, selectedSubPolicyIdx[selectedPolicyIdx], 'Control', $event.target.value)"
                    rows="3"
                    title="Specify the control mechanisms, procedures, or safeguards to be implemented"
                    maxlength="1000"
                  ></textarea>
                  <div class="character-counter" :class="getCharacterCounterClass(policiesForm[selectedPolicyIdx].subpolicies[selectedSubPolicyIdx[selectedPolicyIdx]].Control, 1000)">
                    {{ (policiesForm[selectedPolicyIdx].subpolicies[selectedSubPolicyIdx[selectedPolicyIdx]].Control || '').length }}/1000
                  </div>
                </div>
                <div class="helper-text">Specify the control mechanisms, procedures, or safeguards to be implemented</div>
              </div>
              <div class="form-group">
                <label>Description <span class="required-star">*</span></label>
                <div class="textarea-container">
                  <textarea
                    placeholder="Enter description"
                    v-model="policiesForm[selectedPolicyIdx].subpolicies[selectedSubPolicyIdx[selectedPolicyIdx]].Description"
                    @input="handleSubPolicyChange(selectedPolicyIdx, selectedSubPolicyIdx[selectedPolicyIdx], 'Description', $event.target.value)"
                    rows="3"
                    title="Explain the purpose, scope, and specific requirements of this sub-policy"
                    maxlength="1000"
                  ></textarea>
                  <div class="character-counter" :class="getCharacterCounterClass(policiesForm[selectedPolicyIdx].subpolicies[selectedSubPolicyIdx[selectedPolicyIdx]].Description, 1000)">
                    {{ (policiesForm[selectedPolicyIdx].subpolicies[selectedSubPolicyIdx[selectedPolicyIdx]].Description || '').length }}/1000
                  </div>
                </div>
                <div class="helper-text">Explain the purpose, scope, and specific requirements of this sub-policy</div>
              </div>
            </div>
            </div>

      <div class="form-actions" v-if="policiesForm.length > 0">
        <button 
          class="create-btn" 
          @click="handleSubmitPolicy" 
          :disabled="loading"
          style="font-size: 1rem; margin-top: 6px"
        >
          {{ loading ? 'Submitting...' : 'Submit' }}
        </button>
      </div>
    </div>

    <!-- Approval Form Section -->
    <div v-else class="approval-section">
      <div class="approval-header">
        <h2>Request Approvals</h2>
        <button class="back-btn" @click="showApprovalForm = false">
          <i class="fas fa-arrow-left"></i> Back to Policy Form
        </button>
      </div>
     
      <div class="approval-form-container">
        <div class="approval-form">
          <div class="form-group">
            <label>Created By <span class="required-star">*</span></label>
            <div class="created-by-field">
            <div class="user-icon">
                <i class="fas fa-user"></i>
              </div>
            

            <input
              type="text"
              v-model="approvalForm.createdByName"
              readonly
              :disabled="loading"
                :placeholder="currentUser.UserName || 'Loading user...'"
              title="This policy will be created under your username"
            />
            </div>
            <div class="helper-text">This policy will be created under your username.</div>
          </div>
          <div class="form-group">
            <label>Reviewer <span class="required-star">*</span></label>
            <select
              v-model="approvalForm.reviewer"
              :disabled="loading"
              title="Select the person who will review and approve this framework/policy"
            >
              <option value="">Select Reviewer</option>
              <option v-for="user in users" :key="user.UserId" :value="user.UserId">
                {{ user.UserName }}
              </option>
            </select>
            <div class="helper-text">Select the person who will review and approve this framework/policy. This person will receive notification to review the submitted content.</div>
            <div v-if="isCreatorReviewerSame" class="error-message" style="margin-top: 8px; color: #dc3545; font-size: 14px;">
              <i class="fas fa-exclamation-triangle"></i>
              Creator and reviewer cannot be the same person. Please select a different reviewer.
            </div>
          </div>
          <div class="approval-info">
            <div class="info-box">
              <h4>Approval Process</h4>
              <ul>
                <li>The selected reviewer will be notified to review your framework and policies</li>
                <li>Once approved, the framework and policies will be activated in the system</li>
                <li>You can track the approval status in the Policies List page</li>
                <li>If changes are needed, the reviewer will provide feedback for updates</li>
              </ul>
            </div>
          </div>
          <button 
            class="create-btn" 
            @click="handleFinalSubmit"
            :disabled="loading || !approvalForm.reviewer || isCreatorReviewerSame"
            title="Submit the framework/policy for review and approval"
          >
            {{ loading ? 'Submitting...' : 'Submit for Review' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>
 
<script>

import { ref, watch, onMounted, onActivated, nextTick, computed } from 'vue'
import axios from 'axios'
import { useRouter, useRoute } from 'vue-router'
import { PopupService, PopupModal } from '@/modules/popus'
import CustomDropdown from '@/components/CustomDropdown.vue'

import { API_ENDPOINTS } from '../../config/api.js'
 
export default {
  name: 'CreatePolicy',
  components: {
    PopupModal,
    CustomDropdown
  },
  setup() {
    const selectedSubPolicyIdx = ref([]) // <-- Declare this at the very top!
    const router = useRouter()
    const route = useRoute()
    const selectedFramework = ref('')
    const policiesForm = ref([])
    const selectedPolicyIdx = ref(null)
    const showApprovalForm = ref(false)
    const showFrameworkForm = ref(false)
    const approvalForm = ref({
      createdBy: '',
      createdByName: localStorage.getItem('username') || '', // Initialize with logged-in username
      reviewer: ''
    })

    // Add reactive ref for current user info
    const currentUser = ref({
      UserId: null,
      UserName: localStorage.getItem('username') || '',
      Role: null
    })
    const frameworks = ref([])
    const loading = ref(false)
    const error = ref(null)
    const users = ref([])
    const frameworkFormData = ref(null)
    const policyCategories = ref([])
    const policyTypes = ref([])
    const entities = ref([])
    const departments = ref([])
    
    // Flag to prevent auto-save during programmatic framework updates
    const isLoadingFramework = ref(false)

    // Add new reactive ref for tracking existing framework identifiers
    const existingFrameworkIdentifiers = ref([])
    
    // Add reactive ref for framework name validation
    const frameworkNameError = ref('')
    const existingFrameworkNames = ref([])

    const newFramework = ref({
      FrameworkName: '',
      Identifier: '',
      FrameworkDescription: '',
      Category: '',
      StartDate: '',
      EndDate: '',
      DocURL: '',
      InternalExternal: ''
    })

    // Add identifier generation functions
    const generateFrameworkIdentifier = async (frameworkName) => {
      if (!frameworkName || frameworkName.length < 4) return ''
      
      const prefix = frameworkName.substring(0, 4).toUpperCase()
      let counter = 1
      let identifier = `${prefix}${counter}`
      
      // Check against existing identifiers
      while (existingFrameworkIdentifiers.value.includes(identifier)) {
        counter++
        identifier = `${prefix}${counter}`
      }
      
      return identifier
    }

    const generatePolicyIdentifier = (policyName) => {
      if (!policyName) return ''
      
      // Split by spaces and take first letter of each word
      const words = policyName.split(' ').filter(word => word.length > 0)
      return words.map(word => word.charAt(0).toUpperCase()).join('')
    }

    const generateSubPolicyIdentifier = (policyIdentifier, subPolicyIndex) => {
      if (!policyIdentifier) return ''
      return `${policyIdentifier}-${subPolicyIndex + 1}`
    }

    // Fetch existing framework identifiers
    const fetchExistingFrameworkIdentifiers = async () => {
      try {
        // Use include_all_for_identifiers parameter to get ALL frameworks regardless of status
        // This ensures truly unique identifier generation
        const response = await axios.get(`${API_ENDPOINTS.FRAMEWORK_EXPLORER}`, {
          params: { include_all_for_identifiers: 'true' }
        })
        
        // Check if response.data is an array (direct response) or has frameworks property (wrapped response)
        const frameworksData = Array.isArray(response.data) ? response.data : response.data.frameworks || []
        
        existingFrameworkIdentifiers.value = frameworksData.map(fw => fw.Identifier || fw.identifier).filter(id => id)
        existingFrameworkNames.value = frameworksData.map(fw => fw.FrameworkName || fw.name).filter(name => name)
        console.log('Fetched existing framework identifiers:', existingFrameworkIdentifiers.value)
        console.log('Fetched existing framework names:', existingFrameworkNames.value)
      } catch (err) {
        console.error('Error fetching existing framework identifiers:', err)
      }
    }

    // Validate framework name in real-time
    const validateFrameworkName = () => {
      const frameworkName = newFramework.value.FrameworkName.trim()
      
      if (!frameworkName) {
        frameworkNameError.value = ''
        return true
      }
      
      // Check if framework name already exists (case-insensitive)
      const exists = existingFrameworkNames.value.some(
        existingName => existingName.toLowerCase() === frameworkName.toLowerCase()
      )
      
      if (exists) {
        frameworkNameError.value = `Framework with name "${frameworkName}" already exists. Please choose a different name.`
        return false
      }
      
      frameworkNameError.value = ''
      return true
    }

    // Clear framework name error when user starts typing
    const clearFrameworkNameError = () => {
      frameworkNameError.value = ''
    }

    // Handle Internal/External selection change
    const handleInternalExternalChange = async () => {
      if (newFramework.value.InternalExternal === 'Internal') {
        // Auto-generate identifier for internal frameworks
        if (newFramework.value.FrameworkName) {
          const generatedId = await generateFrameworkIdentifier(newFramework.value.FrameworkName)
          newFramework.value.Identifier = generatedId
        }
      } else if (newFramework.value.InternalExternal === 'External') {
        // Clear identifier for external frameworks to allow manual entry
        newFramework.value.Identifier = ''
      }
    }

    // Auto-generate framework identifier when framework name changes (only for internal frameworks)
    const autoGenerateFrameworkIdentifier = async () => {
      if (newFramework.value.FrameworkName && newFramework.value.InternalExternal === 'Internal') {
        const generatedId = await generateFrameworkIdentifier(newFramework.value.FrameworkName)
        newFramework.value.Identifier = generatedId
      }
    }

    // Auto-generate policy identifiers (only for internal frameworks)
    const autoGeneratePolicyIdentifiers = (policyIndex) => {
      const policy = policiesForm.value[policyIndex]
      if (!policy) return

      // Only auto-generate for internal frameworks
      if (!isInternalFramework()) return

      if (policy.PolicyName) {
        const generatedId = generatePolicyIdentifier(policy.PolicyName)
        policy.Identifier = generatedId

        // Auto-generate subpolicy identifiers
        policy.subpolicies.forEach((subpolicy, subIndex) => {
          if (subpolicy.SubPolicyName) {
            subpolicy.Identifier = generateSubPolicyIdentifier(generatedId, subIndex)
          }
        })
      }
    }

    // Auto-generate subpolicy identifier when subpolicy name changes (only for internal frameworks)
    const autoGenerateSubPolicyIdentifier = (policyIndex, subPolicyIndex) => {
      const policy = policiesForm.value[policyIndex]
      const subpolicy = policy?.subpolicies[subPolicyIndex]
      if (!policy || !subpolicy) return

      // Only auto-generate for internal frameworks
      if (!isInternalFramework()) return

      if (subpolicy.SubPolicyName && policy.Identifier) {
        subpolicy.Identifier = generateSubPolicyIdentifier(policy.Identifier, subPolicyIndex)
      }
    }

    // Helper function to check if current context is for internal framework
    const isInternalFramework = () => {
      return (selectedFramework.value === '__new__' && frameworkFormData.value?.InternalExternal === 'Internal') ||
             (selectedFramework.value !== '__new__' && selectedFramework.value !== '' && 
              frameworks.value.find(f => f.id === selectedFramework.value)?.InternalExternal === 'Internal')
    }

    // Watch for changes to auto-generate identifiers
    watch(() => newFramework.value.FrameworkName, autoGenerateFrameworkIdentifier)
    
    // Watch for InternalExternal changes to handle identifier generation
    watch(() => newFramework.value.InternalExternal, (newValue, oldValue) => {
      if (newValue === 'Internal' && oldValue === 'External') {
        // User changed from External to Internal, auto-generate identifier
        if (newFramework.value.FrameworkName) {
          autoGenerateFrameworkIdentifier()
        }
      } else if (newValue === 'External' && oldValue === 'Internal') {
        // User changed from Internal to External, clear identifier for manual entry
        newFramework.value.Identifier = ''
      }
    })

    // Watch for policy name changes to validate uniqueness
    watch(() => policiesForm.value, (newPolicies) => {
      newPolicies.forEach((policy, index) => {
        if (policy.PolicyName) {
          validatePolicyName(policy.PolicyName, index)
        }
      })
    }, { deep: true })

    // Fetch all frameworks on component mount
    async function fetchFrameworks() {
      try {
        loading.value = true
        console.log('🔍 DEBUG: Fetching frameworks for CreatePolicy...')
        
        // Add active_only=true parameter to only fetch active frameworks
        const response = await axios.get(`${API_ENDPOINTS.FRAMEWORK_EXPLORER}?active_only=true`)
        
        // Check if response.data is an array (direct response) or has frameworks property (wrapped response)
        const frameworksData = Array.isArray(response.data) ? response.data : response.data.frameworks || []
        
        frameworks.value = frameworksData.map(fw => ({
          id: fw.FrameworkId || fw.id,
          name: fw.FrameworkName || fw.name,
          InternalExternal: fw.InternalExternal || fw.internalExternal
        }))
        
        console.log('✅ DEBUG: Frameworks loaded:', frameworks.value.length)
        console.log('📝 DEBUG: Available frameworks:', frameworks.value.map(f => `${f.name} (ID: ${f.id})`))
        
        // After loading frameworks, check for selected framework from session
        await checkSelectedFrameworkFromSession()
        
      } catch (err) {
        console.error('❌ DEBUG: Error fetching frameworks:', err)
        PopupService.error('Failed to fetch frameworks', 'Loading Error')
        sendPushNotification({
          title: 'Framework Loading Failed',
          message: 'Failed to fetch frameworks. Please try again.',
          category: 'framework',
          priority: 'medium',
          user_id: currentUser.value?.UserId || 'default_user'
        });
      } finally {
        loading.value = false
      }
    }

    // Check for selected framework from session and set it as default
    async function checkSelectedFrameworkFromSession() {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session...')
        
        // Set flag to prevent watcher from saving during load
        isLoadingFramework.value = true
        
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
        console.log('📊 DEBUG: Selected framework response:', response.data)
        
        if (response.data && response.data.success) {
          // Check if a framework is selected (not null)
          if (response.data.frameworkId) {
          const sessionFrameworkId = response.data.frameworkId
          console.log('✅ DEBUG: Found selected framework in session:', sessionFrameworkId)
          
          // Check if this framework exists in our loaded frameworks
          const frameworkExists = frameworks.value.find(f => f.id == sessionFrameworkId)
          
          if (frameworkExists) {
            selectedFramework.value = sessionFrameworkId
            console.log('🎯 DEBUG: Set selected framework from session:', frameworkExists.name)
            console.log('📝 DEBUG: Framework details:', frameworkExists)
            
            // If this is the first load and no policies exist, add the first policy
            if (policiesForm.value.length === 0) {
              handleAddPolicy();
              selectedPolicyIdx.value = 0;
            }
          } else {
            console.log('⚠️ DEBUG: Framework from session not found in available frameworks')
            console.log('🔍 DEBUG: Session framework ID:', sessionFrameworkId)
            console.log('📝 DEBUG: Available framework IDs:', frameworks.value.map(f => f.id))
            selectedFramework.value = ''  // Empty string for dropdown reset
          }
        } else {
          // "All Frameworks" is selected (frameworkId is null)
          console.log('ℹ️ DEBUG: No framework selected in session (All Frameworks selected)')
          console.log('🌐 DEBUG: Clearing framework selection to show all frameworks')
          selectedFramework.value = ''  // Empty string for dropdown reset
        }
      } else {
        console.log('ℹ️ DEBUG: No valid response from session')
        selectedFramework.value = ''  // Empty string for dropdown reset
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework from session:', error)
        // Don't show error to user as this is not critical
        selectedFramework.value = ''  // Empty string for dropdown reset
      } finally {
        // Reset flag after a short delay to allow Vue to update
        setTimeout(() => {
          isLoadingFramework.value = false
          console.log('✅ DEBUG: Framework loading complete, watcher re-enabled')
        }, 100)
      }
    }

    // Watch for framework selection changes
    watch(selectedFramework, async (newValue, oldValue) => {
      // Skip if we're loading from backend to prevent circular updates
      if (isLoadingFramework.value) {
        console.log('🔄 DEBUG: Skipping auto-save - loading framework from backend')
        return
      }
      
      if (newValue === 'create') {
        showFrameworkForm.value = true
        selectedFramework.value = ''
      } else if (newValue && newValue !== '__new__' && !showFrameworkForm.value) {
        // Only save if user actually changed it (not programmatic load)
        if (oldValue !== undefined && oldValue !== newValue) {
          // Save the selected framework to session
          try {
            const userId = currentUser.value.UserId || localStorage.getItem('user_id') || 'default_user'
            console.log('💾 DEBUG: User changed framework, saving to backend:', newValue)
            
            const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
              frameworkId: newValue,
              userId: userId
            })
            
            if (response.data && response.data.success) {
              console.log('✅ DEBUG: Framework saved to session successfully')
            } else {
              console.error('❌ DEBUG: Failed to save framework to session')
            }
          } catch (error) {
            console.error('❌ DEBUG: Error saving framework to session:', error)
          }
        } else {
          console.log('🔄 DEBUG: Framework set programmatically (oldValue:', oldValue, '), skipping save')
        }
        
        // If a framework is selected and no policies exist, add the first policy and select it
        if (policiesForm.value.length === 0) {
          handleAddPolicy();
          selectedPolicyIdx.value = 0;
        }
      }
    })

    const handleCreateFramework = async () => {
      // Validate framework name using the real-time validation
      if (!validateFrameworkName()) {
        return
      }
      
      // Only store framework details in memory and move to add policy
      error.value = null
      frameworkFormData.value = { ...newFramework.value }
      showFrameworkForm.value = false
      // Add an initial empty policy
      handleAddPolicy()
      // Set selectedFramework to a dummy value to show the policy form
      selectedFramework.value = '__new__'
      // Reset the framework form
      newFramework.value = {
        FrameworkName: '',
        Identifier: '',
        FrameworkDescription: '',
        Category: '',
        StartDate: '',
        EndDate: '',
        DocURL: '',
        InternalExternal: ''
      }
      // Refresh existing identifiers after framework creation
      fetchExistingFrameworkIdentifiers()
    }

    const goBackToFramework = () => {
      // Restore the framework data to the form
      newFramework.value = { ...frameworkFormData.value }
      // Show the framework form again
      showFrameworkForm.value = true
      // Clear the selected framework to hide policy form
      selectedFramework.value = ''
      // Clear any existing policies
      policiesForm.value = []
      selectedPolicyIdx.value = null
      selectedSubPolicyIdx.value = []
    }

    // Policy form handlers
    const handleAddPolicy = () => {
      const newPolicy = {
        PolicyName: '',
        Identifier: '',
        PolicyDescription: '',
        Scope: '',
        Objective: '',
        Department: [],
        Applicability: '',
        StartDate: '',
        EndDate: '',
        CreatedByName: '',
        DocURL: '',
        PolicyType: '',
        PolicyCategory: '',
        PolicySubCategory: '',
        Entities: [],
        subpolicies: [],
        // Search properties for enhanced dropdowns
        policyTypeSearch: '',
        policyCategorySearch: '',
        policySubCategorySearch: '',
        // Dropdown visibility properties
        showPolicyTypeDropdown: false,
        showPolicyCategoryDropdown: false,
        showPolicySubCategoryDropdown: false
      }
      policiesForm.value.push(newPolicy)
      selectedPolicyIdx.value = policiesForm.value.length - 1
      selectedSubPolicyIdx.value.push(null) // No subpolicy selected initially
      // Only auto-generate identifiers for internal frameworks
      if (isInternalFramework()) {
        setTimeout(() => {
          autoGeneratePolicyIdentifiers(policiesForm.value.length - 1)
        }, 100)
      }
    }

    // Validate policy name uniqueness within the framework
    const validatePolicyName = (policyName, currentIndex) => {
      if (!policyName) return true // Allow empty names during typing
      
      const duplicateIndex = policiesForm.value.findIndex((policy, index) => 
        index !== currentIndex && 
        policy.PolicyName.toLowerCase() === policyName.toLowerCase()
      )
      
      if (duplicateIndex !== -1) {
        error.value = `Policy name "${policyName}" already exists in this framework. Policy names must be unique within a framework.`
        return false
      }
      
      error.value = null
      return true
    }

    // Validate subpolicy name uniqueness within the policy
    const validateSubPolicyName = (subPolicyName, policyIdx, currentSubIdx) => {
      if (!subPolicyName) return true // Allow empty names during typing
      
      const currentPolicy = policiesForm.value[policyIdx]
      if (!currentPolicy || !currentPolicy.subpolicies) return true
      
      const duplicateIndex = currentPolicy.subpolicies.findIndex((subpolicy, index) => 
        index !== currentSubIdx && 
        subpolicy.SubPolicyName.toLowerCase() === subPolicyName.toLowerCase()
      )
      
      if (duplicateIndex !== -1) {
        error.value = `Subpolicy name "${subPolicyName}" already exists in this policy. Subpolicy names must be unique within a policy.`
        return false
      }
      
      error.value = null
      return true
    }

    const handleRemovePolicy = (idx) => {
      policiesForm.value = policiesForm.value.filter((_, i) => i !== idx);
      selectedSubPolicyIdx.value = selectedSubPolicyIdx.value.filter((_, i) => i !== idx);
      if (policiesForm.value.length > 0) {
        if (selectedPolicyIdx.value > idx) {
          selectedPolicyIdx.value = selectedPolicyIdx.value - 1;
        } else if (selectedPolicyIdx.value === idx) {
          selectedPolicyIdx.value = Math.max(0, idx - 1);
        }
      } else {
        selectedPolicyIdx.value = null;
      }
    };

    const handlePolicyChange = (idx, field, value) => {
      policiesForm.value[idx][field] = value
      
      // Auto-generate identifiers when PolicyName changes (only for internal frameworks)
      if (field === 'PolicyName') {
        autoGeneratePolicyIdentifiers(idx)
      }
    }

    const handleAddSubPolicy = (policyIdx) => {
      policiesForm.value[policyIdx].subpolicies.push({
        SubPolicyName: '',
        Identifier: '',
        Control: '',
        Description: '',
        CreatedByName: '',
        PermanentTemporary: ''
      })
      const newSubPolicyIndex = policiesForm.value[policyIdx].subpolicies.length - 1
      // Only auto-generate identifier for internal frameworks
      if (isInternalFramework()) {
        autoGenerateSubPolicyIdentifier(policyIdx, newSubPolicyIndex)
      }
      selectedSubPolicyIdx.value[policyIdx] = newSubPolicyIndex // Select the new subpolicy
    }

    const handleRemoveSubPolicy = (policyIdx, subIdx) => {
      policiesForm.value[policyIdx].subpolicies =
        policiesForm.value[policyIdx].subpolicies.filter((_, j) => j !== subIdx)
      // Adjust selected subpolicy index
      if (selectedSubPolicyIdx.value[policyIdx] === subIdx) {
        selectedSubPolicyIdx.value[policyIdx] = Math.max(0, subIdx - 1)
      } else if (selectedSubPolicyIdx.value[policyIdx] > subIdx) {
        selectedSubPolicyIdx.value[policyIdx]--
      }
    }

    const handleSubPolicyChange = (policyIdx, subIdx, field, value) => {
      policiesForm.value[policyIdx].subpolicies[subIdx][field] = value
      
      // Auto-generate identifier when SubPolicyName changes (only for internal frameworks)
      if (field === 'SubPolicyName') {
        autoGenerateSubPolicyIdentifier(policyIdx, subIdx)
        // Validate subpolicy name uniqueness
        validateSubPolicyName(value, policyIdx, subIdx)
      }
    }

    const handleSubmitPolicy = () => {
      showApprovalForm.value = true
    }

    // Fetch current logged-in user information
    async function fetchCurrentUser() {
      try {
        const response = await axios.get(API_ENDPOINTS.USER_ROLE)
        if (response.data.success) {
          currentUser.value = {
            UserId: response.data.user_id,
            UserName: response.data.username || response.data.user_name || localStorage.getItem('username') || '',
            Role: response.data.role
          }
          // Update approval form with current user name
          approvalForm.value.createdByName = currentUser.value.UserName
          approvalForm.value.createdBy = currentUser.value.UserId
          
          console.log('Current user loaded:', currentUser.value)
        }
      } catch (err) {
        console.error('Error fetching current user:', err)
        // Fallback to localStorage if API fails
        const storedUsername = localStorage.getItem('username')
        if (storedUsername) {
          currentUser.value.UserName = storedUsername
          approvalForm.value.createdByName = storedUsername
        }
      }
    }

    // Add this function to fetch users
    async function fetchUsers() {
      try {
        loading.value = true
        const response = await axios.get(`${API_ENDPOINTS.USERS_FOR_DROPDOWN}`)        
        users.value = response.data
      } catch (err) {
        console.error('Error fetching users:', err)
        PopupService.error('Failed to fetch users', 'Loading Error')
        sendPushNotification({
          title: 'Users Loading Failed',
          message: 'Failed to fetch users. Please try again.',
          category: 'policy',
          priority: 'medium',
          user_id: currentUser.value?.UserId || 'default_user'
        });
      } finally {
        loading.value = false
      }
    }

    // Fetch policy categories
    async function fetchPolicyCategories() {
      try {
        loading.value = true
        const response = await axios.get(`${API_ENDPOINTS.POLICY_CATEGORIES}`)
        policyCategories.value = response.data
        // Extract unique policy types
        policyTypes.value = [...new Set(policyCategories.value.map(cat => cat.PolicyType).filter(Boolean))]
      } catch (err) {
        console.error('Error fetching policy categories:', err)
        PopupService.error('Failed to fetch policy categories', 'Loading Error')
        sendPushNotification({
          title: 'Policy Categories Loading Failed',
          message: 'Failed to fetch policy categories. Please try again.',
          category: 'policy',
          priority: 'medium',
          user_id: currentUser.value?.UserId || 'default_user'
        });
      } finally {
        loading.value = false
      }
    }

    // Fetch entities
    async function fetchEntities() {
      try {
        const response = await axios.get(`${API_ENDPOINTS.ENTITIES}`)
        entities.value = response.data.entities || []
      } catch (err) {
        console.error('Error fetching entities:', err)
        PopupService.error('Failed to fetch entities', 'Loading Error')
        sendPushNotification({
          title: 'Entities Loading Failed',
          message: 'Failed to fetch entities. Please try again.',
          category: 'policy',
          priority: 'medium',
          user_id: currentUser.value?.UserId || 'default_user'
        });
      }
    }

    // Fetch departments
    async function fetchDepartments() {
      try {
        console.log('Fetching departments from:', `${API_ENDPOINTS.DEPARTMENTS}`)
        const response = await axios.get(`${API_ENDPOINTS.DEPARTMENTS}`)
        console.log('Departments API response:', response.data)
        const departmentsData = response.data.departments || []
        console.log('Departments data:', departmentsData)
        
        // Add "All Departments" option at the beginning
        departments.value = [
          { id: 'all', name: 'All Departments' },
          ...departmentsData
        ]
        console.log('Final departments value:', departments.value)
      } catch (err) {
        console.error('Error fetching departments:', err)
        console.error('Error details:', err.response?.data || err.message)
        // Provide fallback departments for better user experience
        departments.value = [
          { id: 'all', name: 'All Departments' },
          { id: 1, name: 'Information Technology' },
          { id: 2, name: 'Human Resources' },
          { id: 3, name: 'Finance' },
          { id: 4, name: 'Legal' },
          { id: 5, name: 'Operations' },
          { id: 6, name: 'Marketing' },
          { id: 7, name: 'Sales' },
          { id: 8, name: 'Customer Support' }
        ]
        console.log('Using fallback departments due to API error')
        // Don't show error popup for non-critical API failures
      }
    }

    // Get categories for a specific policy type
    const getCategoriesForType = (policyType) => {
      if (!policyType) return []
      return [...new Set(
        policyCategories.value
          .filter(cat => cat.PolicyType === policyType)
          .map(cat => cat.PolicyCategory)
          .filter(Boolean)
      )]
    }

    // Get sub categories for a specific policy type and category
    const getSubCategoriesForCategory = (policyType, policyCategory) => {
      if (!policyType || !policyCategory) return []
      return [...new Set(
        policyCategories.value
          .filter(cat => cat.PolicyType === policyType && cat.PolicyCategory === policyCategory)
          .map(cat => cat.PolicySubCategory)
          .filter(Boolean)
      )]
    }

    // Handle policy type change
    const handlePolicyTypeChange = async (idx, value) => {
      policiesForm.value[idx].PolicyType = value
      policiesForm.value[idx].PolicyCategory = ''
      policiesForm.value[idx].PolicySubCategory = ''
      
      // Force Vue to re-render the datalist by triggering reactivity
      await nextTick()
    }

    // Handle policy category change
    const handlePolicyCategoryChange = async (idx, value) => {
      policiesForm.value[idx].PolicyCategory = value
      policiesForm.value[idx].PolicySubCategory = ''
    }

    // Add new function to handle subcategory changes
    const handlePolicySubCategoryChange = (idx, value) => {
      policiesForm.value[idx].PolicySubCategory = value
      // Remove immediate API call - will save during form submission
    }

    // Handle entity selection changes
    const handleEntityChange = (idx, selectedEntities) => {
      if (selectedEntities.includes('all')) {
        // If 'all' is selected, set entities to "all" string
        policiesForm.value[idx].Entities = 'all'
      } else {
        // Set to array of selected entity IDs
        policiesForm.value[idx].Entities = selectedEntities.filter(id => id !== 'all')
      }
    }

    // Check if 'All' is selected for entities
    const isAllEntitiesSelected = (idx) => {
      return policiesForm.value[idx].Entities === 'all'
    }

    // Get selected entity IDs for display
    const getSelectedEntityIds = (idx) => {
      const entities = policiesForm.value[idx].Entities
      if (entities === 'all') {
        return ['all']
      }
      return Array.isArray(entities) ? entities.filter(id => id !== 'all') : []
    }

    // Get count of selected entities (excluding 'all')
    const getSelectedEntitiesCount = (idx) => {
      const entities = policiesForm.value[idx].Entities
      if (entities === 'all') {
        return 0 // Don't count when 'all' is selected
      }
      return Array.isArray(entities) ? entities.filter(id => id !== 'all').length : 0
    }

    // Toggle entities dropdown visibility
    const toggleEntitiesDropdown = (idx) => {
      // Close all other dropdowns first
      policiesForm.value.forEach((policy, index) => {
        if (index !== idx) {
          policy.showEntitiesDropdown = false
        }
      })
      
      // Initialize showEntitiesDropdown if it doesn't exist
      if (policiesForm.value[idx].showEntitiesDropdown === undefined) {
        policiesForm.value[idx].showEntitiesDropdown = false
      }
      policiesForm.value[idx].showEntitiesDropdown = !policiesForm.value[idx].showEntitiesDropdown
    }

    // Close all entity dropdowns
    const closeAllEntityDropdowns = () => {
      policiesForm.value.forEach(policy => {
        policy.showEntitiesDropdown = false
        policy.showDepartmentsDropdown = false
      })
    }

    // Handle individual entity selection
    const handleEntitySelection = (idx, entityId, isChecked) => {
      console.log('handleEntitySelection called:', { idx, entityId, isChecked })
      let selectedEntities = getSelectedEntityIds(idx)
      console.log('Current selected entities:', selectedEntities)
      
      if (entityId === 'all') {
        if (isChecked) {
          // If 'All' is selected, clear other selections and set to 'all'
          policiesForm.value[idx].Entities = 'all'
          console.log('Set entities to "all"')
        } else {
          // If 'All' is unchecked, clear selection
          policiesForm.value[idx].Entities = []
          console.log('Cleared entities')
        }
      } else {
        // If a specific entity is selected
        if (isChecked) {
          // Remove 'all' if it was selected and add the specific entity
          if (selectedEntities.includes('all')) {
            selectedEntities = []
          }
          if (!selectedEntities.includes(entityId)) {
            selectedEntities.push(entityId)
          }
        } else {
          // Remove the entity from selection
          selectedEntities = selectedEntities.filter(id => id !== entityId && id !== 'all')
        }
        policiesForm.value[idx].Entities = selectedEntities
        console.log('Updated entities to:', selectedEntities)
      }
      
      console.log('Final policy entities:', policiesForm.value[idx].Entities)
    }

    // Select entity (for clicking on the option)
    const selectEntity = (idx, entityId) => {
      const currentEntities = policiesForm.value[idx].Entities
      
      let isSelected = false
      if (entityId === 'all') {
        isSelected = currentEntities === 'all'
      } else {
        isSelected = Array.isArray(currentEntities) && currentEntities.includes(entityId)
      }
      
      handleEntitySelection(idx, entityId, !isSelected)
    }

    // Policy Type dropdown functions
    const togglePolicyTypeDropdown = (idx) => {
      // Close all other dropdowns first
      policiesForm.value.forEach((policy, index) => {
        if (index !== idx) {
          policy.showPolicyTypeDropdown = false
          policy.showPolicyCategoryDropdown = false
          policy.showPolicySubCategoryDropdown = false
          policy.showEntitiesDropdown = false
          policy.showDepartmentsDropdown = false
        }
      })
      
      // Initialize showPolicyTypeDropdown if it doesn't exist
      if (policiesForm.value[idx].showPolicyTypeDropdown === undefined) {
        policiesForm.value[idx].showPolicyTypeDropdown = false
      }
      policiesForm.value[idx].showPolicyTypeDropdown = !policiesForm.value[idx].showPolicyTypeDropdown
    }

    const selectPolicyType = (idx, type) => {
      policiesForm.value[idx].PolicyType = type
      policiesForm.value[idx].PolicyCategory = ''
      policiesForm.value[idx].PolicySubCategory = ''
      policiesForm.value[idx].showPolicyTypeDropdown = false
    }

    // Policy Category dropdown functions
    const togglePolicyCategoryDropdown = (idx) => {
      // Close all other dropdowns first
      policiesForm.value.forEach((policy, index) => {
        if (index !== idx) {
          policy.showPolicyTypeDropdown = false
          policy.showPolicyCategoryDropdown = false
          policy.showPolicySubCategoryDropdown = false
          policy.showEntitiesDropdown = false
          policy.showDepartmentsDropdown = false
        }
      })
      
      // Initialize showPolicyCategoryDropdown if it doesn't exist
      if (policiesForm.value[idx].showPolicyCategoryDropdown === undefined) {
        policiesForm.value[idx].showPolicyCategoryDropdown = false
      }
      policiesForm.value[idx].showPolicyCategoryDropdown = !policiesForm.value[idx].showPolicyCategoryDropdown
    }

    const selectPolicyCategory = (idx, category) => {
      policiesForm.value[idx].PolicyCategory = category
      policiesForm.value[idx].PolicySubCategory = ''
      policiesForm.value[idx].showPolicyCategoryDropdown = false
    }

    // Policy Sub Category dropdown functions
    const togglePolicySubCategoryDropdown = (idx) => {
      // Close all other dropdowns first
      policiesForm.value.forEach((policy, index) => {
        if (index !== idx) {
          policy.showPolicyTypeDropdown = false
          policy.showPolicyCategoryDropdown = false
          policy.showPolicySubCategoryDropdown = false
          policy.showEntitiesDropdown = false
          policy.showDepartmentsDropdown = false
        }
      })
      
      // Initialize showPolicySubCategoryDropdown if it doesn't exist
      if (policiesForm.value[idx].showPolicySubCategoryDropdown === undefined) {
        policiesForm.value[idx].showPolicySubCategoryDropdown = false
      }
      policiesForm.value[idx].showPolicySubCategoryDropdown = !policiesForm.value[idx].showPolicySubCategoryDropdown
    }

    const selectPolicySubCategory = (idx, subCategory) => {
      policiesForm.value[idx].PolicySubCategory = subCategory
      policiesForm.value[idx].showPolicySubCategoryDropdown = false
    }

    // Enhanced dropdown functions with search and create capabilities
    const filterPolicyTypes = () => {
      // This function is called on input to filter policy types
      // The filtering is handled in getFilteredPolicyTypes
    }

    const getFilteredPolicyTypes = (idx) => {
      const searchQuery = policiesForm.value[idx].policyTypeSearch || ''
      if (!searchQuery) return policyTypes.value
      
      return policyTypes.value.filter(type => 
        type.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    const createNewPolicyType = async (idx) => {
      const newType = policiesForm.value[idx].policyTypeSearch?.trim()
      if (!newType) return
      
      try {
        // Add to local array first for immediate UI update
        if (!policyTypes.value.includes(newType)) {
          policyTypes.value.push(newType)
        }
        
        // Select the new type
        selectPolicyType(idx, newType)
        
        // Clear search
        policiesForm.value[idx].policyTypeSearch = ''
        
        PopupService.success(`Policy type "${newType}" added successfully!`, 'Success')
      } catch (err) {
        console.error('Error creating policy type:', err)
        PopupService.error('Failed to create policy type. Please try again.', 'Error')
      }
    }

    const filterPolicyCategories = () => {
      // This function is called on input to filter policy categories
      // The filtering is handled in getFilteredPolicyCategories
    }

    const getFilteredPolicyCategories = (idx) => {
      const searchQuery = policiesForm.value[idx].policyCategorySearch || ''
      const policyType = policiesForm.value[idx].PolicyType
      
      if (!policyType) return []
      
      const categories = getCategoriesForType(policyType)
      
      if (!searchQuery) return categories
      
      return categories.filter(category => 
        category.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    const createNewPolicyCategory = async (idx) => {
      const newCategory = policiesForm.value[idx].policyCategorySearch?.trim()
      const policyType = policiesForm.value[idx].PolicyType
      
      if (!newCategory || !policyType) {
        PopupService.error('Please select a policy type first.', 'Error')
        return
      }
      
      try {
        // Add to local array first for immediate UI update
        const categories = getCategoriesForType(policyType)
        if (!categories.includes(newCategory)) {
          // Add to policyCategories array
          policyCategories.value.push({
            PolicyType: policyType,
            PolicyCategory: newCategory,
            PolicySubCategory: 'Default'
          })
        }
        
        // Select the new category
        selectPolicyCategory(idx, newCategory)
        
        // Clear search
        policiesForm.value[idx].policyCategorySearch = ''
        
        PopupService.success(`Policy category "${newCategory}" added successfully!`, 'Success')
      } catch (err) {
        console.error('Error creating policy category:', err)
        PopupService.error('Failed to create policy category. Please try again.', 'Error')
      }
    }

    const filterPolicySubCategories = () => {
      // This function is called on input to filter policy subcategories
      // The filtering is handled in getFilteredPolicySubCategories
    }

    const getFilteredPolicySubCategories = (idx) => {
      const searchQuery = policiesForm.value[idx].policySubCategorySearch || ''
      const policyType = policiesForm.value[idx].PolicyType
      const policyCategory = policiesForm.value[idx].PolicyCategory
      
      if (!policyType || !policyCategory) return []
      
      const subCategories = getSubCategoriesForCategory(policyType, policyCategory)
      
      if (!searchQuery) return subCategories
      
      return subCategories.filter(subCategory => 
        subCategory.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    const createNewPolicySubCategory = async (idx) => {
      const newSubCategory = policiesForm.value[idx].policySubCategorySearch?.trim()
      const policyType = policiesForm.value[idx].PolicyType
      const policyCategory = policiesForm.value[idx].PolicyCategory
      
      if (!newSubCategory || !policyType || !policyCategory) {
        PopupService.error('Please select a policy type and category first.', 'Error')
        return
      }
      
      try {
        // Add to local array first for immediate UI update
        const subCategories = getSubCategoriesForCategory(policyType, policyCategory)
        if (!subCategories.includes(newSubCategory)) {
          // Add to policyCategories array
          policyCategories.value.push({
            PolicyType: policyType,
            PolicyCategory: policyCategory,
            PolicySubCategory: newSubCategory
          })
          
          // Save to database immediately if we have a selected framework
          if (selectedFramework.value && selectedFramework.value !== '__new__') {
            console.log('🔍 DEBUG: Saving new policy subcategory combination to database immediately')
            console.log('🔍 DEBUG: Data:', { policyType, policyCategory, newSubCategory, framework: selectedFramework.value })
            try {
              const response = await axios.post(API_ENDPOINTS.POLICY_CATEGORIES_SAVE, {
                PolicyType: policyType,
                PolicyCategory: policyCategory,
                PolicySubCategory: newSubCategory,
                frameworkId: selectedFramework.value
              })
              console.log('✅ DEBUG: Policy category combination saved to database:', response.data)
              
              // Refresh policy categories after saving
              await fetchPolicyCategories()
            } catch (apiError) {
              console.error('❌ DEBUG: Failed to save policy category combination to database:', apiError)
              console.error('❌ DEBUG: Error response:', apiError.response?.data)
              console.error('❌ DEBUG: Error status:', apiError.response?.status)
            }
          } else {
            console.warn('⚠️ DEBUG: No framework selected, policy category will not be saved to database')
          }
        }
        
        // Select the new subcategory
        selectPolicySubCategory(idx, newSubCategory)
        
        // Clear search
        policiesForm.value[idx].policySubCategorySearch = ''
        
        PopupService.success(`Policy subcategory "${newSubCategory}" added successfully!`, 'Success')
      } catch (err) {
        console.error('Error creating policy subcategory:', err)
        PopupService.error('Failed to create policy subcategory. Please try again.', 'Error')
      }
    }

    // Department selection functions
    // Check if 'All' is selected for departments
    const isAllDepartmentsSelected = (idx) => {
      return policiesForm.value[idx].Department === 'all'
    }

    // Get selected department IDs for display
    const getSelectedDepartmentIds = (idx) => {
      const departments = policiesForm.value[idx].Department
      if (departments === 'all') {
        return ['all']
      }
      return Array.isArray(departments) ? departments.filter(id => id !== 'all') : []
    }

    // Get count of selected departments (excluding 'all')
    const getSelectedDepartmentsCount = (idx) => {
      const departments = policiesForm.value[idx].Department
      if (departments === 'all') {
        return 0 // Don't count when 'all' is selected
      }
      return Array.isArray(departments) ? departments.filter(id => id !== 'all').length : 0
    }

    // Toggle departments dropdown visibility
    const toggleDepartmentsDropdown = (idx) => {
      // Close all other dropdowns first
      policiesForm.value.forEach((policy, index) => {
        if (index !== idx) {
          policy.showDepartmentsDropdown = false
        }
      })
      
      // Initialize showDepartmentsDropdown if it doesn't exist
      if (policiesForm.value[idx].showDepartmentsDropdown === undefined) {
        policiesForm.value[idx].showDepartmentsDropdown = false
      }
      policiesForm.value[idx].showDepartmentsDropdown = !policiesForm.value[idx].showDepartmentsDropdown
    }

    // Close all department dropdowns
    // const closeAllDepartmentDropdowns = () => {
    //   policiesForm.value.forEach(policy => {
    //     policy.showDepartmentsDropdown = false
    //   })
    // }

    // Handle individual department selection
    const handleDepartmentSelection = (idx, departmentId, isChecked) => {
      console.log('handleDepartmentSelection called:', { idx, departmentId, isChecked })
      let selectedDepartments = getSelectedDepartmentIds(idx)
      console.log('Current selected departments:', selectedDepartments)
      
      if (departmentId === 'all') {
        if (isChecked) {
          // If 'All' is selected, clear other selections and set to 'all'
          policiesForm.value[idx].Department = 'all'
          console.log('Set departments to "all"')
        } else {
          // If 'All' is unchecked, clear selection
          policiesForm.value[idx].Department = []
          console.log('Cleared departments')
        }
      } else {
        // If a specific department is selected
        if (isChecked) {
          // Remove 'all' if it was selected and add the specific department
          if (selectedDepartments.includes('all')) {
            selectedDepartments = []
          }
          if (!selectedDepartments.includes(departmentId)) {
            selectedDepartments.push(departmentId)
          }
        } else {
          // Remove the department from selection
          selectedDepartments = selectedDepartments.filter(id => id !== departmentId && id !== 'all')
        }
        policiesForm.value[idx].Department = selectedDepartments
        console.log('Updated departments to:', selectedDepartments)
      }
      
      console.log('Final policy departments:', policiesForm.value[idx].Department)
    }

    // Select department (for clicking on the option)
    const selectDepartment = (idx, departmentId) => {
      const currentDepartments = policiesForm.value[idx].Department
      
      let isSelected = false
      if (departmentId === 'all') {
        isSelected = currentDepartments === 'all'
      } else {
        isSelected = Array.isArray(currentDepartments) && currentDepartments.includes(departmentId)
      }
      
      handleDepartmentSelection(idx, departmentId, !isSelected)
    }
    
    // Add function to save new policy categories before form submission
    const saveNewPolicyCategories = async () => {
      try {
        console.log('Checking for new policy categories to save...');
        const newCombinations = [];
        
        // Process all policies to find new category combinations
        for (const policy of policiesForm.value) {
          const type = policy.PolicyType?.trim();
          const category = policy.PolicyCategory?.trim();
          const subcategory = policy.PolicySubCategory?.trim();
          
          // Skip if any part of the combination is missing
          if (!type || !category || !subcategory) {
            continue;
          }
          
          // Check if this combination exists in our local data
          const exists = policyCategories.value.some(pc => 
            pc.PolicyType === type && 
            pc.PolicyCategory === category && 
            pc.PolicySubCategory === subcategory
          );
          
          if (!exists) {
            console.log(`Found new combination: ${type} > ${category} > ${subcategory}`);
            newCombinations.push({
              PolicyType: type,
              PolicyCategory: category,
              PolicySubCategory: subcategory
            });
          }
        }
        
        // Save new combinations to the database
        if (newCombinations.length > 0) {
          console.log(`Saving ${newCombinations.length} new policy category combinations...`);
          
          for (const combination of newCombinations) {
            // Include framework context when saving policy categories
            const combinationWithFramework = {
              ...combination,
              frameworkId: selectedFramework.value
            };
            console.log('Saving policy category with framework:', combinationWithFramework);
            await axios.post(`${API_ENDPOINTS.POLICY_CATEGORIES}save/`, combinationWithFramework);
          }
          
          // Refresh policy categories after saving
          await fetchPolicyCategories();
          console.log('Policy categories refreshed');
        } else {
          console.log('No new policy category combinations to save');
        }
      } catch (err) {
        console.error('Error saving policy categories:', err);
      }
    };

    // Add push notification method
    const sendPushNotification = async (notificationData) => {
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
    };

    const handleFinalSubmit = async () => {
      try {
        // Check consent before proceeding
        const consentService = (await import('@/services/consentService.js')).default;
        const { CONSENT_ACTIONS } = await import('@/utils/consentManager.js');
        
        const canProceed = await consentService.checkAndRequestConsent(
          CONSENT_ACTIONS.CREATE_POLICY
        );
        
        // If user declined consent, stop here
        if (!canProceed) {
          console.log('Policy creation cancelled by user (consent declined)');
          return;
        }

        loading.value = true
        error.value = null

        // Save any new policy categories first
        await saveNewPolicyCategories();

        // Only check framework fields if creating a new framework
        const isCreatingNewFramework = selectedFramework.value === '__new__';
        if (isCreatingNewFramework) {
                  if (!frameworkFormData.value || !frameworkFormData.value.FrameworkName) {
          PopupService.error('Please fill in all required framework fields.', 'Validation Error')
          sendPushNotification({
            title: 'Framework Creation Failed',
            message: 'Please fill in all required framework fields.',
            category: 'framework',
            priority: 'high',
            user_id: currentUser.value?.UserId || 'default_user'
          });
          loading.value = false
          return
        }
        }

        // Find the selected creator and reviewer users
        const creatorUser = users.value.find(u => u.UserName === approvalForm.value.createdByName) || 
                           currentUser.value // Use current user as fallback
        const reviewerUser = users.value.find(u => u.UserId === approvalForm.value.reviewer)

        if (!approvalForm.value.createdByName) {
          PopupService.error('Creator name not found. Please try logging in again.', 'Validation Error')
          sendPushNotification({
            title: 'Policy Creation Failed',
            message: 'Creator name not found. Please try logging in again.',
            category: 'policy',
            priority: 'high',
            user_id: currentUser.value?.UserId || 'default_user'
          });
          loading.value = false
          return
        }

        // Validate that creator and reviewer are not the same person
        if (creatorUser && reviewerUser && creatorUser.UserId === reviewerUser.UserId) {
          PopupService.error('Creator and reviewer cannot be the same person. Please select a different reviewer.', 'Validation Error')
          sendPushNotification({
            title: 'Policy Creation Failed',
            message: 'Creator and reviewer cannot be the same person. Please select a different reviewer.',
            category: 'policy',
            priority: 'high',
            user_id: creatorUser?.UserId || 'default_user'
          });
          loading.value = false
          return
        }

        // Validate required fields for each policy
        for (const policy of policiesForm.value) {
          if (!policy.PolicyName || !policy.Identifier || !policy.StartDate) {
            PopupService.error('Please fill in all required fields (Policy Name, Identifier, and Start Date) for all policies', 'Validation Error')
            sendPushNotification({
              title: 'Policy Creation Failed',
              message: 'Please fill in all required fields (Policy Name, Identifier, and Start Date) for all policies',
              category: 'policy',
              priority: 'high',
              user_id: creatorUser?.UserId || 'default_user'
            });
            loading.value = false
            return
          }
        }

        // Validate policy name uniqueness within the framework
        const policyNames = policiesForm.value.map(p => p.PolicyName.toLowerCase())
        const duplicatePolicyNames = []
        
        for (let i = 0; i < policyNames.length; i++) {
          for (let j = i + 1; j < policyNames.length; j++) {
            if (policyNames[i] === policyNames[j] && policyNames[i] !== '') {
              const originalName = policiesForm.value[i].PolicyName
              if (!duplicatePolicyNames.includes(originalName)) {
                duplicatePolicyNames.push(originalName)
              }
            }
          }
        }
        
        if (duplicatePolicyNames.length > 0) {
          PopupService.error(`Duplicate policy names found: ${duplicatePolicyNames.join(', ')}. Policy names must be unique within a framework.`, 'Validation Error')
          sendPushNotification({
            title: 'Policy Creation Failed',
            message: `Duplicate policy names found: ${duplicatePolicyNames.join(', ')}. Policy names must be unique within a framework.`,
            category: 'policy',
            priority: 'high',
            user_id: creatorUser?.UserId || 'default_user'
          });
          loading.value = false
          return
        }

        // Validate subpolicy name uniqueness within each policy
        for (let policyIdx = 0; policyIdx < policiesForm.value.length; policyIdx++) {
          const policy = policiesForm.value[policyIdx]
          const subpolicyNames = policy.subpolicies.map(s => s.SubPolicyName.toLowerCase())
          const duplicateSubpolicyNames = []
          
          for (let i = 0; i < subpolicyNames.length; i++) {
            for (let j = i + 1; j < subpolicyNames.length; j++) {
              if (subpolicyNames[i] === subpolicyNames[j] && subpolicyNames[i] !== '') {
                const originalName = policy.subpolicies[i].SubPolicyName
                if (!duplicateSubpolicyNames.includes(originalName)) {
                  duplicateSubpolicyNames.push(originalName)
                }
              }
            }
          }
          
          if (duplicateSubpolicyNames.length > 0) {
            PopupService.error(`Duplicate subpolicy names found in policy "${policy.PolicyName}": ${duplicateSubpolicyNames.join(', ')}. Subpolicy names must be unique within a policy.`, 'Validation Error')
            sendPushNotification({
              title: 'Policy Creation Failed',
              message: `Duplicate subpolicy names found in policy "${policy.PolicyName}": ${duplicateSubpolicyNames.join(', ')}. Subpolicy names must be unique within a policy.`,
              category: 'policy',
              priority: 'high',
              user_id: creatorUser?.UserId || 'default_user'
            });
            loading.value = false
            return
          }
        }

        for (const policy of policiesForm.value) {

          // New validation: must have at least one subpolicy
          if (!policy.subpolicies || policy.subpolicies.length === 0) {
            PopupService.error('Each policy must have at least one subpolicy.', 'Validation Error');
            sendPushNotification({
              title: 'Policy Creation Failed',
              message: 'Each policy must have at least one subpolicy.',
              category: 'policy',
              priority: 'high',
              user_id: creatorUser?.UserId || 'default_user'
            });
            loading.value = false;
            return;
          }

          // Set default values for optional fields
          policy.Status = policy.Status || 'Under Review'
          policy.ActiveInactive = policy.ActiveInactive || 'Inactive'
          policy.CreatedByName = creatorUser.UserName
          policy.Reviewer = reviewerUser ? reviewerUser.UserName : null
          
          // Convert Department from array or 'all' to string format
          if (policy.Department === 'all') {
            policy.Department = 'All Departments';
          } else if (Array.isArray(policy.Department)) {
            // Convert array of department IDs to comma-separated string
            policy.Department = policy.Department.join(',');
          }

          // Validate subpolicies
          for (const sub of policy.subpolicies) {
            if (!sub.SubPolicyName || !sub.Identifier) {
              PopupService.error('Please fill in all required fields (Name and Identifier) for all subpolicies', 'Validation Error')
              sendPushNotification({
                title: 'Policy Creation Failed',
                message: 'Please fill in all required fields (Name and Identifier) for all subpolicies',
                category: 'policy',
                priority: 'high',
                user_id: creatorUser?.UserId || 'default_user'
              });
              loading.value = false
              return
            }
            // Set default values for subpolicies
            sub.Status = sub.Status || 'Under Review'
            sub.CreatedByName = creatorUser.UserName
          }
        }

        // Debug: Check entities after validation
        console.log('DEBUG: Policies after validation:', policiesForm.value.map(p => ({ PolicyName: p.PolicyName, Entities: p.Entities })))

        if (isCreatingNewFramework) {
          // Upload framework document if exists
          if (frameworkFormData.value.DocURL && frameworkFormData.value.DocURL instanceof File) {
            const formData = new FormData()
            formData.append('file', frameworkFormData.value.DocURL)
            formData.append('userId', creatorUser.UserId)
            formData.append('fileName', frameworkFormData.value.DocURL.name)
            formData.append('type', 'framework')
            formData.append('frameworkName', frameworkFormData.value.FrameworkName)

            try {
             const uploadResponse = await axios.post(API_ENDPOINTS.UPLOAD_POLICY_DOCUMENT, formData, {
                headers: {
                  'Content-Type': 'multipart/form-data'
                },
                timeout: 1000000 // Increase timeout for large files
              })
              if (uploadResponse.data.success) {
                frameworkFormData.value.DocURL = uploadResponse.data.file.url
              } else {
                throw new Error(uploadResponse.data.error || 'Upload failed')
              }
            } catch (uploadError) {
              console.error('Error uploading framework document:', uploadError)
              PopupService.error('Failed to upload framework document: ' + (uploadError.response?.data?.error || uploadError.message), 'Upload Error')
              sendPushNotification({
                title: 'Framework Document Upload Failed',
                message: `Failed to upload framework document: ${uploadError.response?.data?.error || uploadError.message}`,
                category: 'framework',
                priority: 'high',
                user_id: creatorUser?.UserId || 'default_user'
              });
              loading.value = false
              return
            }
          }

          // Upload all policy documents before building the payload
          for (const policy of policiesForm.value) {
            if (policy.DocURL && policy.DocURL instanceof File) {
              const formData = new FormData()
              formData.append('file', policy.DocURL)
              formData.append('userId', creatorUser.UserId)
              formData.append('fileName', policy.DocURL.name)
              formData.append('type', 'policy')
              formData.append('policyName', policy.PolicyName)

              try {
                const uploadResponse = await axios.post(API_ENDPOINTS.UPLOAD_POLICY_DOCUMENT, formData, {
                  headers: {
                    'Content-Type': 'multipart/form-data'
                  },
                timeout: 1000000
                })
                if (uploadResponse.data.success) {
                  policy.DocURL = uploadResponse.data.file.url
                } else {
                  throw new Error(uploadResponse.data.error || 'Upload failed')
                }
              } catch (uploadError) {
                console.error('Error uploading policy document:', uploadError)
                PopupService.error('Failed to upload policy document: ' + (uploadError.response?.data?.error || uploadError.message), 'Upload Error')
                sendPushNotification({
                  title: 'Policy Document Upload Failed',
                  message: `Failed to upload policy document: ${uploadError.response?.data?.error || uploadError.message}`,
                  category: 'policy',
                  priority: 'high',
                  user_id: creatorUser?.UserId || 'default_user'
                });
                loading.value = false
                return
              }
            }
          }

          // Debug: Log policies form data before creating payload
          console.log('Policies form data before payload creation:', JSON.stringify(policiesForm.value, null, 2))
          
          // Prepare the full payload for new framework
          const payload = {
            ...frameworkFormData.value,
            CreatedByName: creatorUser.UserName,
            CreatedById: creatorUser.UserId,
            Reviewer: reviewerUser ? reviewerUser.UserId : null,
            policies: policiesForm.value.map((policy, index) => {
              console.log(`DEBUG: Processing policy ${index}, Entities before mapping:`, policy.Entities)
              
              const mappedPolicy = {
                ...policy,
                CoverageRate: policy.CoverageRate !== '' && policy.CoverageRate !== null && policy.CoverageRate !== undefined ? Number(policy.CoverageRate) : null,
                CreatedByName: creatorUser.UserName,
                CreatedById: creatorUser.UserId,
                Reviewer: reviewerUser ? reviewerUser.UserId : null,
                Entities: policy.Entities, // Explicitly set Entities
                subpolicies: policy.subpolicies.map(sub => ({
                  ...sub,
                  CreatedByName: creatorUser.UserName,
                  CreatedByDate: new Date().toISOString().split('T')[0],
                  Status: 'Under Review',
                  PermanentTemporary: ''
                }))
              }
              
              console.log(`DEBUG: Policy ${index} after mapping, Entities:`, mappedPolicy.Entities)
              return mappedPolicy
            })
          }
          
          // Debug: Log final payload
          console.log('Final payload being sent:', JSON.stringify(payload, null, 2))

          // Send a single API call to create the framework with policies and subpolicies
          const response = await axios.post(API_ENDPOINTS.FRAMEWORKS, payload)
          if (response.data.error) {
            throw new Error(response.data.error)
          }
          PopupService.success(
            'Successfully created new framework and policies! Redirecting to All Policies page...',
            'Framework Created'
          );
          sendPushNotification({
            title: 'Framework and Policies Created Successfully',
            message: `New framework "${frameworkFormData.value.FrameworkName}" with ${policiesForm.value.length} policies has been created successfully.`,
            category: 'framework',
            priority: 'medium',
            user_id: creatorUser?.UserId || 'default_user'
          });
        } else {
          // Add policies to existing framework (batch mode)
          const frameworkId = selectedFramework.value;

          // Upload all policy documents before building the payload
          for (const policy of policiesForm.value) {
            if (policy.DocURL && policy.DocURL instanceof File) {
              const formData = new FormData()
              formData.append('file', policy.DocURL)
              formData.append('userId', creatorUser.UserId)
              formData.append('fileName', policy.DocURL.name)
              formData.append('type', 'policy')
              formData.append('policyName', policy.PolicyName)

              try {
                const uploadResponse = await axios.post(API_ENDPOINTS.UPLOAD_POLICY_DOCUMENT, formData, {
                  headers: {
                    'Content-Type': 'multipart/form-data'
                  },
                timeout: 1000000
                })
                if (uploadResponse.data.success) {
                  policy.DocURL = uploadResponse.data.file.url
                } else {
                  throw new Error(uploadResponse.data.error || 'Upload failed')
                }
              } catch (uploadError) {
                console.error('Error uploading policy document:', uploadError)
                PopupService.error('Failed to upload policy document: ' + (uploadError.response?.data?.error || uploadError.message), 'Upload Error')
                sendPushNotification({
                  title: 'Policy Document Upload Failed',
                  message: `Failed to upload policy document: ${uploadError.response?.data?.error || uploadError.message}`,
                  category: 'policy',
                  priority: 'high',
                  user_id: creatorUser?.UserId || 'default_user'
                });
                loading.value = false
                return
              }
            }
          }

          // Build the batch payload
          const policiesPayload = policiesForm.value.map(policy => ({
            ...policy,
            CoverageRate: policy.CoverageRate !== '' && policy.CoverageRate !== null && policy.CoverageRate !== undefined ? Number(policy.CoverageRate) : null,
            CreatedByName: creatorUser.UserName,
            CreatedById: creatorUser.UserId,
            Reviewer: reviewerUser ? reviewerUser.UserId : null,
            subpolicies: policy.subpolicies.map(sub => ({
              ...sub,
              CreatedByName: creatorUser.UserName,
              CreatedByDate: new Date().toISOString().split('T')[0],
              Status: 'Under Review',
              PermanentTemporary: ''
            }))
          }));

          try {
            const response = await axios.post(API_ENDPOINTS.FRAMEWORK_ADD_POLICIES(frameworkId), { policies: policiesPayload });
            if (response.data.error) {
              throw new Error(response.data.error)
            }
            PopupService.success(
              'Successfully added policies! Redirecting to All Policies page...',
              'Policies Added'
            );
            sendPushNotification({
              title: 'Policies Added Successfully',
              message: `Successfully added ${policiesForm.value.length} policies to the existing framework.`,
              category: 'policy',
              priority: 'medium',
              user_id: creatorUser?.UserId || 'default_user'
            });
          } catch (err) {
            console.error('Error submitting policies:', err);
            const errorMessage = err.response?.data?.details || err.response?.data?.error || 'Failed to submit policies';
            PopupService.error(typeof errorMessage === 'object' ? JSON.stringify(errorMessage) : errorMessage, 'Submission Error');
            sendPushNotification({
              title: 'Policy Submission Failed',
              message: typeof errorMessage === 'object' ? JSON.stringify(errorMessage) : errorMessage,
              category: 'policy',
              priority: 'high',
              user_id: creatorUser?.UserId || 'default_user'
            });
            loading.value = false;
            return;
          }
        }

        // Reset forms
        policiesForm.value = []
        approvalForm.value = {
          createdBy: currentUser.value.UserId || '',
          createdByName: currentUser.value.UserName || localStorage.getItem('username') || '',
          reviewer: ''
        }
        selectedFramework.value = ''
        showApprovalForm.value = false
        frameworkFormData.value = null

        // Redirect to AllPolicies page after successful creation
        setTimeout(() => {
          router.push('/policies-list/all')
        }, 1500) // Wait 1.5 seconds to allow user to see the success message

      } catch (err) {
        console.error('Error submitting policies:', err)
        const errorMessage = err.response?.data?.details || err.response?.data?.error || 'Failed to submit policies';
        PopupService.error(typeof errorMessage === 'object' ? JSON.stringify(errorMessage) : errorMessage, 'Submission Error');
        sendPushNotification({
          title: 'Policy Submission Failed',
          message: typeof errorMessage === 'object' ? JSON.stringify(errorMessage) : errorMessage,
          category: 'policy',
          priority: 'high',
          user_id: currentUser.value?.UserId || 'default_user'
        });
      } finally {
        loading.value = false
      }
    }

    const getSelectedFrameworkName = () => {
      const framework = frameworks.value.find(f => f.id === selectedFramework.value)
      return framework ? framework.name : ''
    }

    const handleChangeFramework = () => {
      selectedFramework.value = ''
      policiesForm.value = []
    }

    // File input handlers
    const frameworkFileInput = ref(null)
    const policyFileInputRefs = ref({})
    
    const setPolicyFileInputRef = (el, idx) => {
      if (el) {
        policyFileInputRefs.value[idx] = el
      }
    }
    
    const handleFrameworkFileUpload = () => {
      if (frameworkFileInput.value) {
        frameworkFileInput.value.click()
      }
    }
    
    const handlePolicyFileUpload = async (idx) => {
      // Check consent before allowing file selection for policy upload
      try {
        const consentService = (await import('@/services/consentService.js')).default;
        const { CONSENT_ACTIONS } = await import('@/utils/consentManager.js');
        
        const canProceed = await consentService.checkAndRequestConsent(
          CONSENT_ACTIONS.UPLOAD_POLICY
        );
        
        // If user declined consent, stop here
        if (!canProceed) {
          console.log('Policy document upload cancelled by user (consent declined)');
          return;
        }
      } catch (consentError) {
        console.error('Error checking consent:', consentError);
        // Continue with file selection if consent check fails
      }

      if (policyFileInputRefs.value[idx]) {
        policyFileInputRefs.value[idx].click()
      }
    }
    
    const onFrameworkFileChange = async (e) => {
      // Check consent before allowing file selection for framework upload (which is part of policy creation)
      // Framework uploads are covered by create_policy consent, but we can also check upload_policy
      try {
        const consentService = (await import('@/services/consentService.js')).default;
        const { CONSENT_ACTIONS } = await import('@/utils/consentManager.js');
        
        const canProceed = await consentService.checkAndRequestConsent(
          CONSENT_ACTIONS.UPLOAD_POLICY
        );
        
        // If user declined consent, stop here
        if (!canProceed) {
          console.log('Framework document upload cancelled by user (consent declined)');
          e.target.value = ''; // Clear the file input
          return;
        }
      } catch (consentError) {
        console.error('Error checking consent:', consentError);
        // Continue with file selection if consent check fails
      }

      const file = e.target.files[0]
      if (file) newFramework.value.DocURL = file
    }
    const onPolicyFileChange = async (e, idx) => {
      // Check consent before storing the selected file
      try {
        const consentService = (await import('@/services/consentService.js')).default;
        const { CONSENT_ACTIONS } = await import('@/utils/consentManager.js');
        
        const canProceed = await consentService.checkAndRequestConsent(
          CONSENT_ACTIONS.UPLOAD_POLICY
        );
        
        // If user declined consent, stop here and clear the file input
        if (!canProceed) {
          console.log('Policy document upload cancelled by user (consent declined)');
          e.target.value = ''; // Clear the file input
          return;
        }
      } catch (consentError) {
        console.error('Error checking consent:', consentError);
        // Continue with file selection if consent check fails
      }

      const file = e.target.files[0]
      if (file) policiesForm.value[idx].DocURL = file
    }

    // Fetch frameworks and users on mount
    onMounted(async () => {
      // Fetch current user first to ensure we have the logged-in user's name
      await fetchCurrentUser()
      
      // Then fetch other data
      fetchFrameworks()
      fetchUsers()
      fetchPolicyCategories()
      fetchExistingFrameworkIdentifiers()
      fetchEntities()
      fetchDepartments()
      // Initialize selectedSubPolicyIdx
      selectedSubPolicyIdx.value = policiesForm.value.map(() => null)
    })

    // Also check framework selection when component is activated (navigating back to page)
    onActivated(async () => {
      console.log('🔄 DEBUG: CreatePolicy component activated - re-checking framework selection')
      await checkSelectedFrameworkFromSession()
    })

    // Watch for route changes to refresh framework selection
    watch(() => route.path, async (newPath, oldPath) => {
      // Only refresh if we're navigating TO this page (not away from it)
      if (newPath.includes('create-policy') && oldPath && !oldPath.includes('create-policy')) {
        console.log('🔄 DEBUG: Navigated to CreatePolicy - refreshing framework selection')
        await checkSelectedFrameworkFromSession()
      }
    }, { immediate: false })

    const showAddSubPolicyForm = ref(false)
    const newSubPolicy = ref({
      SubPolicyName: '',
      Identifier: '',
      Control: '',
      Description: ''
    })
    const addNewSubPolicy = () => {
      if (!newSubPolicy.value.SubPolicyName) return;
      policiesForm.value[selectedPolicyIdx.value].subpolicies.push({ ...newSubPolicy.value })
      newSubPolicy.value = { SubPolicyName: '', Identifier: '', Control: '', Description: '' }
      showAddSubPolicyForm.value = false
    }

    const frameworkDropdownConfig = computed(() => {
      // Only show the user's stored framework in the dropdown if it exists
      const sessionFrameworkId = selectedFramework.value;
      const sessionFramework = frameworks.value.find(f => f.id == sessionFrameworkId);
      
      // Create options array based on whether we have a stored framework
      let options = [];
      
      if (sessionFramework) {
        // If we have a stored framework, only show that one and the create option
        options = [
          { label: sessionFramework.name, value: sessionFramework.id },
          { label: '+ Create New Framework', value: 'create' }
        ];
      } else {
        // If no stored framework, show all frameworks
        options = [
          { label: 'Select', value: '' },
          { label: '+ Create New Framework', value: 'create' },
          ...frameworks.value.map(f => ({ label: f.name, value: f.id }))
        ];
      }
      
      return {
        label: 'Framework',
        options: options
      };
    })

    // Check if creator and reviewer are the same person
    const isCreatorReviewerSame = computed(() => {
      if (!approvalForm.value.reviewer || !approvalForm.value.createdByName) return false
      const creatorUser = users.value.find(u => u.UserName === approvalForm.value.createdByName) || currentUser.value
      const reviewerUser = users.value.find(u => u.UserId === approvalForm.value.reviewer)
      return creatorUser && reviewerUser && creatorUser.UserId === reviewerUser.UserId
    })

    // Character counter function
    const getCharacterCounterClass = (text, maxLength) => {
      if (!text) return ''
      const length = text.length
      const percentage = (length / maxLength) * 100
      
      if (percentage >= 90) return 'error'
      if (percentage >= 75) return 'warning'
      return ''
    }

    return {
      selectedFramework,
      policiesForm,
      selectedPolicyIdx,
      frameworks,
      showApprovalForm,
      showFrameworkForm,
      approvalForm,
      newFramework,
      loading,
      error,
      frameworkNameError,
      existingFrameworkNames,
      users,
      currentUser,
      policyCategories,
      policyTypes,
      entities,
      departments,
      handleAddPolicy,
      handleRemovePolicy,
      handlePolicyChange,
      validatePolicyName,
      validateSubPolicyName,
      handleAddSubPolicy,
      handleRemoveSubPolicy,
      handleSubPolicyChange,
      handleSubmitPolicy,
      handleFinalSubmit,
      handleCreateFramework,
      handleInternalExternalChange,
      goBackToFramework,
      getSelectedFrameworkName,
      handleChangeFramework,
      checkSelectedFrameworkFromSession,
      frameworkFormData,
      frameworkFileInput,
      policyFileInputRefs,
      setPolicyFileInputRef,
      handleFrameworkFileUpload,
      handlePolicyFileUpload,
      onFrameworkFileChange,
      onPolicyFileChange,
      getCategoriesForType,
      getSubCategoriesForCategory,
      handlePolicyTypeChange,
      handlePolicyCategoryChange,
      handlePolicySubCategoryChange,
      handleEntityChange,
      isAllEntitiesSelected,
      getSelectedEntityIds,
      getSelectedEntitiesCount,
      toggleEntitiesDropdown,
      closeAllEntityDropdowns,
      handleEntitySelection,
      selectEntity,
      isAllDepartmentsSelected,
      getSelectedDepartmentIds,
      getSelectedDepartmentsCount,
      toggleDepartmentsDropdown,
      handleDepartmentSelection,
      selectDepartment,
      togglePolicyTypeDropdown,
      selectPolicyType,
      togglePolicyCategoryDropdown,
      selectPolicyCategory,
      togglePolicySubCategoryDropdown,
      selectPolicySubCategory,
      filterPolicyTypes,
      getFilteredPolicyTypes,
      createNewPolicyType,
      filterPolicyCategories,
      getFilteredPolicyCategories,
      createNewPolicyCategory,
      filterPolicySubCategories,
      getFilteredPolicySubCategories,
      createNewPolicySubCategory,
      generateFrameworkIdentifier,
      fetchExistingFrameworkIdentifiers,
      validateFrameworkName,
      clearFrameworkNameError,
      generatePolicyIdentifier,
      generateSubPolicyIdentifier,
      isCreatorReviewerSame,
      autoGenerateFrameworkIdentifier,
      autoGeneratePolicyIdentifiers,
      autoGenerateSubPolicyIdentifier,
      isInternalFramework,
      showAddSubPolicyForm,
      newSubPolicy,
      addNewSubPolicy,
      selectedSubPolicyIdx,
      frameworkDropdownConfig,
      sendPushNotification,
      getCharacterCounterClass,
    }
  }
}
</script>
 
<style scoped>
@import './CreatePolicy.css';
@import '@/modules/popus/styles.css';

.required-star {
  color: #e53e3e;
  margin-left: 2px;
  font-size: 1.1em;
}
.helper-text {
  color: #6b7280;
  font-size: 0.97em;
  margin-top: 2px;
  margin-bottom: 8px;
  line-height: 1.3;
}

/* .loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e2e8f0;
  border-top: 4px solid #4299e1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-overlay p {
  margin-top: 16px;
  color: #4a5568;
  font-size: 1rem;
  font-weight: 500;
} */

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  position: fixed;
  top: 20px;
  right: 20px;
  background: linear-gradient(135deg, #fc8181, #f56565);
  color: white;
  padding: 16px 24px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 1000;
  box-shadow: 0 6px 16px rgba(245, 101, 101, 0.2);
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.close-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 1.2rem;
  padding: 4px;
  opacity: 0.8;
  transition: all 0.2s ease;
}

.close-btn:hover {
  opacity: 1;
  transform: scale(1.1);
}

/* Form Animations */
.policy-card, .subpolicy-card {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Enhanced Button States */
button {
  position: relative;
  overflow: hidden;
}

button::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 5px;
  height: 5px;
  background: rgba(255, 255, 255, 0.5);
  opacity: 0;
  border-radius: 100%;
  transform: scale(1, 1) translate(-50%);
  transform-origin: 50% 50%;
}

button:focus:not(:active)::after {
  animation: ripple 1s ease-out;
}

@keyframes ripple {
  0% {
    transform: scale(0, 0);
    opacity: 0.5;
  }
  100% {
    transform: scale(100, 100);
    opacity: 0;
  }
}

/* Enhanced Form Field Focus States */
input:focus, select:focus, textarea:focus {
  transform: translateY(-1px);
}

/* Card Hover Effects */
.policy-card:hover, .subpolicy-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
}

/* Framework Form Field Styling */
.framework-form-container {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-top: 20px;
}

.framework-form {
  max-width: 100%;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.form-group {
  position: relative;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #4a5568;
  margin-bottom: 8px;
}

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}

.input-with-icon i {
  position: absolute;
  left: 16px;
  color: #718096;
  font-size: 16px;
}

.form-group input,
.form-group select {
  width: 100%;
  height: 45px;
  padding: 8px 16px 8px 45px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  color: #2d3748;
  background: white;
}

/* Colored borders */
.blue-border .input-with-icon input,
.blue-border .input-with-icon select {
  border-left: 3px solid #4299e1;
}

.green-border .input-with-icon input,
.green-border .input-with-icon select {
  border-left: 3px solid #48bb78;
}

.orange-border .input-with-icon input,
.orange-border .input-with-icon select {
  border-left: 3px solid #ed8936;
}

.red-border .input-with-icon input,
.red-border .input-with-icon select {
  border-left: 3px solid #f56565;
}

/* Upload field styling */
.upload-field {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: white;
  height: 45px;
}

.upload-field span {
  margin-left: 30px;
  color: #718096;
  font-size: 14px;
}

.browse-btn {
  margin-left: auto;
  padding: 4px 12px;
  background: #4299e1;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

/* Date input styling */
input[type="date"] {
  padding-right: 16px;
}

input[type="date"]::-webkit-calendar-picker-indicator {
  position: absolute;
  right: 8px;
  cursor: pointer;
}

/* Select styling */
select {
  appearance: none;
  padding-right: 30px;
  background-image: url("data:image/svg+xml,...");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 16px;
  cursor: pointer;
}

/* Framework selection styling */
.framework-policy-row {
  margin-bottom: 24px;
}

.framework-policy-selects {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 8px;
}

.framework-policy-selects > div {
  flex: 0 0 300px; /* Fixed width for the select container */
}

.framework-policy-selects label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #4a5568;
  margin-bottom: 12px;
}

.framework-policy-selects select {
  width: 100%;
  height: 40px;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
  color: #2d3748;
  background: white;
  cursor: pointer;
  outline: none;
  transition: all 0.2s ease;
}

.framework-policy-selects select:focus {
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.framework-policy-selects select:hover {
  border-color: #cbd5e0;
}

/* Approval Form Transitions */
.approval-section {
  animation: fadeScale 0.4s ease-out;
}

@keyframes fadeScale {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Enhanced Scrollbar Styling */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

/* Tooltip Styles */
[title] {
  position: relative;
  cursor: help;
}

[title]:hover::after {
  content: attr(title);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(45, 55, 72, 0.95);
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.4;
  white-space: nowrap;
  max-width: 250px;
  white-space: normal;
  text-align: center;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: tooltipFadeIn 0.2s ease-out;
  pointer-events: none;
}

[title]:hover::before {
  content: '';
  position: absolute;
  bottom: 94%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: rgba(45, 55, 72, 0.95);
  z-index: 1001;
  animation: tooltipFadeIn 0.2s ease-out;
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

/* Tooltip positioning adjustments for specific elements */
.input-with-icon[title]:hover::after {
  bottom: 120%;
  max-width: 200px;
}

.input-with-icon[title]:hover::before {
  bottom: 114%;
}

/* Button tooltip positioning */
button[title]:hover::after {
  bottom: 120%;
  max-width: 180px;
}

button[title]:hover::before {
  bottom: 114%;
}

/* Select tooltip positioning */
select[title]:hover::after {
  bottom: 120%;
  max-width: 200px;
}

select[title]:hover::before {
  bottom: 114%;
}

/* Textarea tooltip positioning */
textarea[title]:hover::after {
  bottom: 105%;
  max-width: 220px;
}

textarea[title]:hover::before {
  bottom: 99%;
}

/* Enhanced tooltip for form groups */
.form-group [title]:hover::after {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  letter-spacing: 0.3px;
}

/* Policy Actions Container */
.policy-actions-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 16px 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.selected-framework-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.selected-framework-info span {
  font-size: 0.95rem;
  color: #2d3748;
  font-weight: 500;
}

.change-framework-btn {
  background: none;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 16px;
  color: #4a5568;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.change-framework-btn:hover {
  background: #f7fafc;
  border-color: #cbd5e0;
  color: #2d3748;
}

/* Update these specific styles */

.policy-card {
  width: 320px; /* Reduced padding */
  padding: 16px; /* Reduced padding */
  box-sizing: border-box; /* Important: include padding in width calculation */
}

/* Base styles for all inputs in policy card */
.policy-card input,
.policy-card textarea {
  width: 100%;
  max-width: 100%; /* Changed from fixed width to 100% */
  padding: 6px 8px;
  height: 32px;
  font-size: 12px;
  box-sizing: border-box; /* Important: include padding in width calculation */
}

/* Form row styling */
.policy-form-row {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  width: 100%; /* Ensure row takes full width */
}

/* Description field specific styling */
.policy-card .form-group.description {
  width: 70%; /* Decreased from 80% to 70% */
  margin: 0 auto;
  max-width: 280px; /* Add max-width to prevent overflow */
}

.policy-card .form-group.description textarea {
  width: 100%;
  min-height: 80px;
  max-width: 100%; /* Ensure textarea doesn't overflow its container */
  box-sizing: border-box;
  overflow-x: hidden; /* Prevent horizontal scrolling */
}

/* Date fields row styling */
.policy-card .date-row {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  width: 100%;
}

.policy-card .date-row .form-group {
  flex: 1;
  min-width: 0;
}

.policy-card .date-row input {
  width: 100%;
}

/* Objective and Applicability row */
.policy-card .objective-applicability-row {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  width: 100%;
}

.policy-card .objective-applicability-row .form-group {
  flex: 1;
  min-width: 0;
}

.policy-card .objective-applicability-row textarea,
.policy-card .objective-applicability-row input {
  width: 100%;
  height: 32px;
}

/* Form groups in a row */
.policy-form-row .form-group {
  flex: 1; /* Changed to flex: 1 to ensure equal width */
  min-width: 0; /* Prevent flex items from overflowing */
  width: calc(50% - 4px); /* Ensure exact half width minus gap */
}

/* Date input specific styling */
.policy-form-row input[type="date"] {
  width: 100%; /* Changed from fixed width to 100% */
  min-width: 0; /* Allow shrinking */
  padding-right: 20px; /* Space for calendar icon */
}

/* Single form groups (not in a row) */
.policy-card .form-group:not(.policy-form-row .form-group) {
  width: 100%;
}

/* Textarea specific styling */
.policy-card textarea {
  height: auto;
  min-height: 50px;
  width: 100%;
  resize: vertical;
}

/* Remove any fixed max-width constraints */
.policy-form-row input,
.policy-form-row .form-group input {
  max-width: none;
}

/* Add these new styles for subpolicy card */
.subpolicy-card {
  width: 300px; /* Smaller than policy card */
  padding: 16px;
  box-sizing: border-box;
}

.subpolicy-card .form-group {
  margin-bottom: 10px;
}

.subpolicy-card input,
.subpolicy-card textarea {
  width: 100%;
  max-width: 100%;
  padding: 6px 8px;
  height: 32px;
  font-size: 12px;
  box-sizing: border-box;
}

.subpolicy-card textarea {
  height: auto;
  min-height: 50px;
  resize: vertical;
}

.subpolicy-card label {
  font-size: 13px;
  margin-bottom: 4px;
}

/* Form row styling for subpolicy */
.subpolicy-card .policy-form-row {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  width: 100%;
}

.subpolicy-card .policy-form-row .form-group {
  flex: 1;
  min-width: 0;
  width: calc(50% - 4px);
}

/* Ensure all inputs stay within boundaries */
.subpolicy-card .form-group input,
.subpolicy-card .form-group textarea {
  width: 100%;
  max-width: none;
}

/* Adjust the subpolicies row spacing */
.subpolicies-row {
  margin-top: 16px;
  gap: 16px;
}

/* Add new styles for searchable select */
.searchable-select {
  position: relative;
  width: 100%;
}

.searchable-select input {
  width: 100%;
  padding: 8px 12px 8px 40px;
  border: 1px solid #e2e8f0;
  border-left: 3px solid #805AD5;
  border-radius: 6px;
  font-size: 13px;
  color: #2d3748;
  background: white;
  transition: all 0.2s ease;
  position: relative;
}

.searchable-select::before {
  content: '\f002';
  font-family: 'Font Awesome 5 Free';
  font-weight: 900;
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #805AD5;
  font-size: 14px;
  z-index: 2;
  pointer-events: none;
}

.searchable-select input:focus {
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
  outline: none;
}

.searchable-select input:hover {
  border-color: #cbd5e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.searchable-select input:disabled {
  background-color: #f7fafc;
  cursor: not-allowed;
  opacity: 0.6;
}

.searchable-select input:disabled:hover {
  border-color: #e2e8f0;
  box-shadow: none;
}

.searchable-select datalist {
  position: absolute;
  top: calc(100% + 2px);
  left: 0;
  right: 0;
  max-height: 180px;
  overflow-y: auto;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  animation: slideDown 0.15s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.searchable-select option {
  padding: 8px 12px;
  cursor: pointer;
  transition: all 0.15s ease;
  border-bottom: 1px solid #f7fafc;
  font-size: 13px;
  color: #2d3748;
}

.searchable-select option:first-child {
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
}

.searchable-select option:last-child {
  border-bottom: none;
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 6px;
}

.searchable-select option:hover {
  background: #f7fafc;
  transform: translateX(1px);
}

/* Custom scrollbar for searchable select datalist */
.searchable-select datalist::-webkit-scrollbar {
  width: 4px;
}

.searchable-select datalist::-webkit-scrollbar-track {
  background: #f8fafc;
  border-radius: 2px;
}

.searchable-select datalist::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 2px;
}

.searchable-select datalist::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* Focus states for accessibility */
.searchable-select input:focus {
  outline: 2px solid #4299e1;
  outline-offset: 2px;
}

/* Mobile responsive adjustments */
@media (max-width: 768px) {
  .searchable-select input {
    padding: 10px 12px 10px 40px;
    font-size: 14px;
  }
  
  .searchable-select::before {
    font-size: 16px;
    left: 14px;
  }
}

/* Entities Multi-Select Styles */
.entities-group {
  width: 100%;
}

.entities-multi-select {
  position: relative;
  width: 100%;
}

.entities-dropdown {
  position: relative;
  width: 100%;
}

.selected-entities {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-left: 3px solid #805AD5;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  min-height: 36px;
  transition: all 0.2s ease;
  font-size: 13px;
  position: relative;
}

.selected-entities::before {
  content: '\f3c5';
  font-family: 'Font Awesome 5 Free';
  font-weight: 900;
  position: absolute;
  left: 10px;
  color: #805AD5;
  font-size: 14px;
}

.selected-entities .entity-content {
  margin-left: 26px;
  flex: 1;
  display: flex;
  align-items: center;
}

.selected-entities:hover {
  border-color: #cbd5e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.selected-entities:focus-within,
.selected-entities.active {
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.entity-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.2px;
}

.all-tag {
  background: linear-gradient(135deg, #4299e1, #3182ce);
  color: white;
  box-shadow: 0 2px 8px rgba(66, 153, 225, 0.3);
}

.entity-count {
  color: #4a5568;
  font-weight: 500;
  font-size: 13px;
}

.placeholder {
  color: #a0aec0;
  font-style: italic;
  font-size: 13px;
}

.dropdown-arrow {
  color: #718096;
  font-size: 12px;
  transition: transform 0.2s ease;
  margin-left: 8px;
}

.selected-entities.active .dropdown-arrow {
  transform: rotate(180deg);
}

.entities-options {
  position: absolute;
  top: calc(100% + 2px);
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  max-height: 180px;
  overflow-y: auto;
  z-index: 1000;
  animation: slideDown 0.15s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.entity-option {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: all 0.15s ease;
  border-bottom: 1px solid #f7fafc;
  position: relative;
}

.entity-option:first-child {
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
}

.entity-option:last-child {
  border-bottom: none;
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 6px;
}

.entity-option:hover {
  background: #f7fafc;
  transform: translateX(1px);
}

.entity-option.all-option {
  background: #ebf8ff;
  border-bottom: 1px solid #90cdf4;
  font-weight: 600;
}

.entity-option.all-option:hover {
  background: #bee3f8;
}

.entity-option input[type="checkbox"] {
  margin-right: 8px;
  cursor: pointer;
  width: 14px;
  height: 14px;
  accent-color: #4299e1;
  border-radius: 3px;
  border: 1px solid #d1d5db;
  background: white;
  transition: all 0.2s ease;
}

.entity-option input[type="checkbox"]:checked {
  background: #4299e1;
  border-color: #4299e1;
}

.entity-option input[type="checkbox"]:hover {
  border-color: #4299e1;
}

.entity-label {
  flex: 1;
  font-size: 13px;
  color: #2d3748;
  font-weight: 500;
  line-height: 1.3;
}

.entity-option.all-option .entity-label {
  color: #2b6cb0;
  font-weight: 600;
  font-size: 13px;
}

/* Custom scrollbar for entities options */
.entities-options::-webkit-scrollbar {
  width: 4px;
}

.entities-options::-webkit-scrollbar-track {
  background: #f8fafc;
  border-radius: 2px;
}

.entities-options::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 2px;
}

.entities-options::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* Mobile responsive adjustments */
@media (max-width: 768px) {
  .entities-multi-select {
    width: 100%;
  }
  
  .entities-options {
    max-height: 160px;
    border-radius: 6px;
  }
  
  .entity-option {
    padding: 10px 12px;
  }
  
  .selected-entities {
    padding: 10px 12px;
    min-height: 38px;
  }
}

/* Focus states for accessibility */
.entity-option:focus {
  outline: 2px solid #4299e1;
  outline-offset: -2px;
  background: #ebf8ff;
}

.selected-entities:focus {
  outline: 2px solid #4299e1;
  outline-offset: 2px;
}

/* Disabled state */
.entities-multi-select.disabled .selected-entities {
  background: #f7fafc;
  cursor: not-allowed;
  opacity: 0.6;
}

.entities-multi-select.disabled .selected-entities:hover {
  border-color: #e2e8f0;
  box-shadow: none;
  transform: none;
}

/* Policy Type Multi-Select Styles */
.policy-type-multi-select {
  position: relative;
  width: 100%;
}

.policy-type-dropdown {
  position: relative;
  width: 100%;
}

.selected-policy-type {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-left: 3px solid #805AD5;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  min-height: 36px;
  transition: all 0.2s ease;
  font-size: 13px;
  position: relative;
}

.selected-policy-type::before {
  content: '\f002';
  font-family: 'Font Awesome 5 Free';
  font-weight: 900;
  position: absolute;
  left: 10px;
  color: #805AD5;
  font-size: 14px;
}

.selected-policy-type .policy-type-content {
  margin-left: 26px;
  flex: 1;
  display: flex;
  align-items: center;
}

.selected-policy-type:hover {
  border-color: #cbd5e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.selected-policy-type:focus-within,
.selected-policy-type.active {
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.policy-type-value {
  color: #2d3748;
  font-weight: 500;
  font-size: 13px;
}

.placeholder {
  color: #a0aec0;
  font-style: italic;
  font-size: 13px;
}

.dropdown-arrow {
  color: #718096;
  font-size: 12px;
  transition: transform 0.2s ease;
  margin-left: 8px;
}

.selected-policy-type.active .dropdown-arrow {
  transform: rotate(180deg);
}

.policy-type-options {
  position: absolute;
  top: calc(100% + 2px);
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  max-height: 180px;
  overflow-y: auto;
  z-index: 1000;
  animation: slideDown 0.15s ease-out;
}

.policy-type-option {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: all 0.15s ease;
  border-bottom: 1px solid #f7fafc;
  position: relative;
}

.policy-type-option:first-child {
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
}

.policy-type-option:last-child {
  border-bottom: none;
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 6px;
}

.policy-type-option:hover {
  background: #f7fafc;
  transform: translateX(1px);
}

.policy-type-label {
  flex: 1;
  font-size: 13px;
  color: #2d3748;
  font-weight: 500;
  line-height: 1.3;
}

/* Policy Category Multi-Select Styles */
.policy-category-multi-select {
  position: relative;
  width: 100%;
}

.policy-category-dropdown {
  position: relative;
  width: 100%;
}

.selected-policy-category {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-left: 3px solid #805AD5;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  min-height: 36px;
  transition: all 0.2s ease;
  font-size: 13px;
  position: relative;
}

.selected-policy-category::before {
  content: '\f002';
  font-family: 'Font Awesome 5 Free';
  font-weight: 900;
  position: absolute;
  left: 10px;
  color: #805AD5;
  font-size: 14px;
}

.selected-policy-category .policy-category-content {
  margin-left: 26px;
  flex: 1;
  display: flex;
  align-items: center;
}

.selected-policy-category:hover {
  border-color: #cbd5e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.selected-policy-category:focus-within,
.selected-policy-category.active {
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.policy-category-value {
  color: #2d3748;
  font-weight: 500;
  font-size: 13px;
}

.policy-category-options {
  position: absolute;
  top: calc(100% + 2px);
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  max-height: 180px;
  overflow-y: auto;
  z-index: 1000;
  animation: slideDown 0.15s ease-out;
}

.policy-category-option {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: all 0.15s ease;
  border-bottom: 1px solid #f7fafc;
  position: relative;
}

.policy-category-option:first-child {
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
}

.policy-category-option:last-child {
  border-bottom: none;
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 6px;
}

.policy-category-option:hover {
  background: #f7fafc;
  transform: translateX(1px);
}

.policy-category-label {
  flex: 1;
  font-size: 13px;
  color: #2d3748;
  font-weight: 500;
  line-height: 1.3;
}

/* Policy Sub Category Multi-Select Styles */
.policy-subcategory-multi-select {
  position: relative;
  width: 100%;
}

.policy-subcategory-dropdown {
  position: relative;
  width: 100%;
}

.selected-policy-subcategory {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-left: 3px solid #805AD5;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  min-height: 36px;
  transition: all 0.2s ease;
  font-size: 13px;
  position: relative;
}

.selected-policy-subcategory::before {
  content: '\f002';
  font-family: 'Font Awesome 5 Free';
  font-weight: 900;
  position: absolute;
  left: 10px;
  color: #805AD5;
  font-size: 14px;
}

.selected-policy-subcategory .policy-subcategory-content {
  margin-left: 26px;
  flex: 1;
  display: flex;
  align-items: center;
}

.selected-policy-subcategory:hover {
  border-color: #cbd5e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.selected-policy-subcategory:focus-within,
.selected-policy-subcategory.active {
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.policy-subcategory-value {
  color: #2d3748;
  font-weight: 500;
  font-size: 13px;
}

.policy-subcategory-options {
  position: absolute;
  top: calc(100% + 2px);
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  max-height: 180px;
  overflow-y: auto;
  z-index: 1000;
  animation: slideDown 0.15s ease-out;
}

.policy-subcategory-option {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: all 0.15s ease;
  border-bottom: 1px solid #f7fafc;
  position: relative;
}

.policy-subcategory-option:first-child {
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
}

.policy-subcategory-option:last-child {
  border-bottom: none;
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 6px;
}

.policy-subcategory-option:hover {
  background: #f7fafc;
  transform: translateX(1px);
}

.policy-subcategory-label {
  flex: 1;
  font-size: 13px;
  color: #2d3748;
  font-weight: 500;
  line-height: 1.3;
}

/* Custom scrollbar for all policy dropdowns */
.policy-type-options::-webkit-scrollbar,
.policy-category-options::-webkit-scrollbar,
.policy-subcategory-options::-webkit-scrollbar {
  width: 4px;
}

.policy-type-options::-webkit-scrollbar-track,
.policy-category-options::-webkit-scrollbar-track,
.policy-subcategory-options::-webkit-scrollbar-track {
  background: #f8fafc;
  border-radius: 2px;
}

.policy-type-options::-webkit-scrollbar-thumb,
.policy-category-options::-webkit-scrollbar-thumb,
.policy-subcategory-options::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 2px;
}

.policy-type-options::-webkit-scrollbar-thumb:hover,
.policy-category-options::-webkit-scrollbar-thumb:hover,
.policy-subcategory-options::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* Focus states for accessibility */
.policy-type-option:focus,
.policy-category-option:focus,
.policy-subcategory-option:focus {
  outline: 2px solid #4299e1;
  outline-offset: -2px;
  background: #ebf8ff;
}

.selected-policy-type:focus,
.selected-policy-category:focus,
.selected-policy-subcategory:focus {
  outline: 2px solid #4299e1;
  outline-offset: 2px;
}

/* Mobile responsive adjustments */
@media (max-width: 768px) {
  .policy-type-multi-select,
  .policy-category-multi-select,
  .policy-subcategory-multi-select {
    width: 100%;
  }
  
  .policy-type-options,
  .policy-category-options,
  .policy-subcategory-options {
    max-height: 160px;
    border-radius: 6px;
  }
  
  .policy-type-option,
  .policy-category-option,
  .policy-subcategory-option {
    padding: 10px 12px;
  }
  
  .selected-policy-type,
  .selected-policy-category,
  .selected-policy-subcategory {
    padding: 10px 12px;
    min-height: 38px;
  }
}

/* Department Multi-Select Styles */
.department-multi-select {
  position: relative;
  width: 100%;
}

.department-dropdown {
  position: relative;
  width: 100%;
}

.selected-departments {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-left: 3px solid #805AD5;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  min-height: 36px;
  transition: all 0.2s ease;
  font-size: 13px;
  position: relative;
}

.selected-departments::before {
  content: '\f3c5';
  font-family: 'Font Awesome 5 Free';
  font-weight: 900;
  position: absolute;
  left: 10px;
  color: #805AD5;
  font-size: 14px;
}

.selected-departments .department-content {
  margin-left: 26px;
  flex: 1;
  display: flex;
  align-items: center;
}

.selected-departments:hover {
  border-color: #cbd5e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.selected-departments:focus-within,
.selected-departments.active {
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.department-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.2px;
}

.all-tag {
  background: linear-gradient(135deg, #4299e1, #3182ce);
  color: white;
  box-shadow: 0 2px 8px rgba(66, 153, 225, 0.3);
}

.department-count {
  color: #4a5568;
  font-weight: 500;
  font-size: 13px;
}

.placeholder {
  color: #a0aec0;
  font-style: italic;
  font-size: 13px;
}

.dropdown-arrow {
  color: #718096;
  font-size: 12px;
  transition: transform 0.2s ease;
  margin-left: 8px;
}

.selected-departments.active .dropdown-arrow {
  transform: rotate(180deg);
}

.departments-options {
  position: absolute;
  top: calc(100% + 2px);
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  max-height: 180px;
  overflow-y: auto;
  z-index: 1000;
  animation: slideDown 0.15s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.department-option {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: all 0.15s ease;
  border-bottom: 1px solid #f7fafc;
  position: relative;
}

.department-option:first-child {
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
}

.department-option:last-child {
  border-bottom: none;
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 6px;
}

.department-option:hover {
  background: #f7fafc;
  transform: translateX(1px);
}

.department-option.all-option {
  background: #ebf8ff;
  border-bottom: 1px solid #90cdf4;
  font-weight: 600;
}

.department-option.all-option:hover {
  background: #bee3f8;
}

.department-option input[type="checkbox"] {
  margin-right: 8px;
  cursor: pointer;
  width: 14px;
  height: 14px;
  accent-color: #4299e1;
  border-radius: 3px;
  border: 1px solid #d1d5db;
  background: white;
  transition: all 0.2s ease;
}

.department-option input[type="checkbox"]:checked {
  background: #4299e1;
  border-color: #4299e1;
}

.department-option input[type="checkbox"]:hover {
  border-color: #4299e1;
}

.department-label {
  flex: 1;
  font-size: 13px;
  color: #2d3748;
  font-weight: 500;
  line-height: 1.3;
}

.department-option.all-option .department-label {
  color: #2b6cb0;
  font-weight: 600;
  font-size: 13px;
}

/* Custom scrollbar for departments options */
.departments-options::-webkit-scrollbar {
  width: 4px;
}

.departments-options::-webkit-scrollbar-track {
  background: #f8fafc;
  border-radius: 2px;
}

.departments-options::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 2px;
}

.departments-options::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* Mobile responsive adjustments for departments */
@media (max-width: 768px) {
  .department-multi-select {
    width: 100%;
  }
  
  .departments-options {
    max-height: 160px;
    border-radius: 6px;
  }
  
  .department-option {
    padding: 10px 12px;
  }
  
  .selected-departments {
    padding: 10px 12px;
    min-height: 38px;
  }
}

/* Focus states for accessibility */
.department-option:focus {
  outline: 2px solid #4299e1;
  outline-offset: -2px;
  background: #ebf8ff;
}

.selected-departments:focus {
  outline: 2px solid #4299e1;
  outline-offset: 2px;
}

/* Disabled state */
.department-multi-select.disabled .selected-departments {
  background: #f7fafc;
  cursor: not-allowed;
  opacity: 0.6;
}

.department-multi-select.disabled .selected-departments:hover {
  border-color: #e2e8f0;
  box-shadow: none;
  transform: none;
}

.full-width-policy-rows {
  width: 100%;
  max-width: 100%;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}
.full-width-policy-card {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}
.policy-form-row,
.policy-card .form-group.description,
.policy-card .date-row,
.policy-card .objective-applicability-row {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.policy-row .policy-card.full-width-policy-card {
  flex: 1 1 100%;
  min-width: 0;
  max-width: 100%;
}

/* Policy Stepper Styles */
.subpolicy-stepper {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  margin-bottom: 12px;
  padding: 16px;
  background: #f7fafc !important;
  border-radius: 8px;
  gap: 16px;
}

.subpolicy-step {
  font-size: 0.85rem;
  color: #2d3748;
  font-weight: 500;
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
}

.subpolicy-step.active {
  background: #4299e1;
  color: white;
  border-radius: 4px;
}


.add-sub-policy-btn.small {
  padding: 6px 16px;
  font-size: 0.95rem;
  border: 1.5px dashed #28a745;
  background: #e6f7ea;
  color: #28a745;
  border-radius: 8px;
  margin: 0;
  transition: background 0.2s, color 0.2s;
}
.add-sub-policy-btn.small:hover {
  background: #d4f5e3;
  color: #20c997;
}

/* Subpolicy Stepper Styles */
.subpolicy-stepper {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  margin-bottom: 12px;
  padding: 16px;
  background: #f7fafc;
  border-radius: 8px;
  gap: 16px;
}

.subpolicy-step {
  font-size: 0.85rem;
  color: #2d3748;
  font-weight: 500;
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
}

.subpolicy-step.active {
  background: #4299e1;
  color: white;
  border-radius: 4px;
}

.add-subpolicy-step-btn {
  background: none;
  border: none;
  color: #4a5568;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.add-subpolicy-step-btn:hover {
  color: #4299e1;
}

.remove-btn {
  background: none;
  border: none;
  color: #718096;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.remove-btn:hover {
  color: #f56565;
}

/* Dropdown button styling - reduce padding and white background */
:deep(.framework-container-top .dropdown-container .filter-btn),
:deep(.policy-form-container .dropdown-container .filter-btn) {
  background: white !important;
  padding: 3px 6px !important;
  border: 1px solid #ddd !important;
  border-radius: 6px !important;
  box-shadow: none !important;
}

:deep(.framework-container-top .dropdown-container .filter-btn:hover),
:deep(.policy-form-container .dropdown-container .filter-btn:hover) {
  background: white !important;
  border-color: #ddd !important;
  box-shadow: none !important;
}

/* Dropdown menu container with single border */
:deep(.framework-container-top .dropdown-container .dropdown-menu),
:deep(.policy-form-container .dropdown-container .dropdown-menu) {
  background: white !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
  padding: 4px !important;
}

/* Dropdown items without individual borders */
:deep(.framework-container-top .dropdown-container .dropdown-item),
:deep(.policy-form-container .dropdown-container .dropdown-item) {
  background: white !important;
  border: none !important;
  border-radius: 4px !important;
  margin-bottom: 2px !important;
  white-space: normal !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  font-size: 0.8em !important;
  font-weight: normal !important;
  line-height: 1.3 !important;
  padding: 6px 10px !important;
  max-width: 100% !important;
}

:deep(.framework-container-top .dropdown-container .dropdown-item:hover),
:deep(.policy-form-container .dropdown-container .dropdown-item:hover) {
  background: #f8f9fa !important;
}
</style>