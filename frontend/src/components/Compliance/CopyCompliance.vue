<template>
  <div class="copy-compliance-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-main">
          <div class="header-text">
            <h1>Copy Compliance Record</h1>
            <p>Create a new compliance item based on the selected one. Target location is auto-populated from current context.</p>
          </div>
          <div class="header-actions">
            <button @click="goBack" class="back-button">
              <i class="fas fa-arrow-left"></i>
              Back
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content with Scroll -->
    <div class="page-content">
      <div class="content-container">

    <!-- Message display -->
    <div v-if="successMessage" class="message success-message">
      {{ successMessage }}
    </div>

    <!-- Loading indicator - Removed as requested -->
    <!-- <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <div class="loading-text">Loading compliance data...</div>
    </div> -->

    <!-- Error message -->
    <div v-if="error" class="message error-message">
      <i class="fas fa-exclamation-circle"></i>
      {{ error }}
    </div>

    <!-- Target selection -->
    <div class="field-group selection-fields">
      <div class="field-group-title">Target Location</div>
      <div class="selection-info">
        <i class="fas fa-info-circle"></i>
        Framework is auto-selected from your current context. You can choose different Policy and Sub Policy as the target location.
      </div>
      <div class="row-fields">
        <div class="compliance-field">
          <label for="framework">
            Framework
            <span class="required">*</span>
            <span class="field-status auto-selected">Auto-selected</span>
          </label>
          <select 
            id="framework" 
            v-model="targetFrameworkId" 
            class="compliance-select"
            :class="{ 'error': validationErrors.targetFrameworkId }"
            :ref="'field_targetFrameworkId'"
            required 
            title="Target framework (auto-selected)"
            disabled
          >
            <option value="" disabled>Select Framework</option>
            <option v-for="fw in frameworks" :key="fw.id" :value="fw.id">{{ fw.name }}</option>
          </select>
          <div v-if="validationErrors.targetFrameworkId" class="field-error-message">
            {{ validationErrors.targetFrameworkId }}
          </div>
        </div>
        
        <div class="compliance-field">
          <label for="policy">
            Policy
            <span class="required">*</span>
            <span class="field-status selectable">Selectable</span>
          </label>
          <select 
            id="policy" 
            v-model="targetPolicyId" 
            class="compliance-select"
            :class="{ 'error': validationErrors.targetPolicyId }"
            :ref="'field_targetPolicyId'"
            required 
            title="Select target policy"
            :disabled="!targetFrameworkId"
          >
            <option value="" disabled>Select Policy</option>
            <option v-for="p in policies" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
          <div v-if="validationErrors.targetPolicyId" class="field-error-message">
            {{ validationErrors.targetPolicyId }}
          </div>
        </div>
        
        <div class="compliance-field">
          <label for="subpolicy">
            Sub Policy
            <span class="required">*</span>
            <span class="field-status selectable">Selectable</span>
          </label>
          <select 
            id="subpolicy" 
            v-model="targetSubPolicyId" 
            class="compliance-select"
            :class="{ 'error': validationErrors.targetSubPolicyId }"
            :ref="'field_targetSubPolicyId'"
            required 
            title="Select target sub-policy"
            :disabled="!targetPolicyId"
          >
            <option value="" disabled>Select Sub Policy</option>
            <option v-for="sp in subPolicies" :key="sp.id" :value="sp.id">{{ sp.name }}</option>
          </select>
          <div v-if="validationErrors.targetSubPolicyId" class="field-error-message">
            {{ validationErrors.targetSubPolicyId }}
          </div>
        </div>
      </div>
    </div>

    <!-- Copy form -->
    <div v-if="compliance" class="compliance-item-form">
      <!-- Basic compliance information -->
      <div class="field-group">
        <div class="field-group-title">Basic Information</div>
        
        <!-- Compliance Title and Type in one row -->
        <div class="row-fields">
          <div class="compliance-field">
            <label>
              Compliance Title
              <span class="required">*</span>
              <span class="field-requirements">(Minimum 5 characters)</span>
            </label>
            <input 
              v-model="compliance.ComplianceTitle" 
              class="compliance-input"
              :class="{ 'error': validationErrors.ComplianceTitle }"
              :ref="'field_ComplianceTitle'"
              placeholder="Enter compliance title"
              @input="validateFieldRealTime('ComplianceTitle')"
              @blur="validateField('ComplianceTitle')"
              required 
            />
            <div v-if="validationErrors.ComplianceTitle" class="field-error-message">
              {{ validationErrors.ComplianceTitle }}
            </div>
          </div>
          
          <div class="compliance-field">
            <label>Compliance Type</label>
            <input 
              v-model="compliance.ComplianceType" 
              class="compliance-input" 
              placeholder="Enter compliance type"
              title="Type of compliance (e.g. Regulatory, Internal, Security)"
            />
          </div>
        </div>
        
        <div class="compliance-field full-width">
          <label>
            Description
            <span class="required">*</span>
            <span class="field-requirements">(Minimum 20 characters)</span>
          </label>
          <textarea 
            v-model="compliance.ComplianceItemDescription" 
            class="compliance-input"
            :class="{ 'error': validationErrors.ComplianceItemDescription }"
            :ref="'field_ComplianceItemDescription'"
            placeholder="Detailed description of the compliance requirement"
            @input="validateFieldRealTime('ComplianceItemDescription')"
            @blur="validateField('ComplianceItemDescription')"
            rows="3"
            required 
          ></textarea>
          <div class="char-count" :class="{ 'error': validationErrors.ComplianceItemDescription }">
            {{ compliance.ComplianceItemDescription?.length || 0 }}/20 min characters
          </div>
          <div v-if="validationErrors.ComplianceItemDescription" class="field-error-message">
            {{ validationErrors.ComplianceItemDescription }}
          </div>
        </div>
        
        <div class="compliance-field full-width">
          <label>
            Scope
            <span class="required">*</span>
            <span class="field-requirements">(Minimum 15 characters)</span>
          </label>
          <textarea 
            v-model="compliance.Scope" 
            class="compliance-input"
            :class="{ 'error': validationErrors.Scope }"
            :ref="'field_Scope'"
            placeholder="Define the boundaries and extent of the compliance requirement"
            @input="validateFieldRealTime('Scope')"
            @blur="validateField('Scope')"
            rows="3"
            required
          ></textarea>
          <div class="char-count" :class="{ 'error': validationErrors.Scope }">
            {{ compliance.Scope?.length || 0 }}/15 min characters
          </div>
          <div v-if="validationErrors.Scope" class="field-error-message">
            {{ validationErrors.Scope }}
          </div>
        </div>
        
        <div class="compliance-field full-width">
          <label>
            Objective
            <span class="required">*</span>
            <span class="field-requirements">(Minimum 15 characters)</span>
          </label>
          <textarea 
            v-model="compliance.Objective" 
            class="compliance-input"
            :class="{ 'error': validationErrors.Objective }"
            :ref="'field_Objective'"
            placeholder="Define the goal or purpose of this compliance requirement"
            @input="validateFieldRealTime('Objective')"
            @blur="validateField('Objective')"
            rows="3"
            required
          ></textarea>
          <div class="char-count" :class="{ 'error': validationErrors.Objective }">
            {{ compliance.Objective?.length || 0 }}/15 min characters
          </div>
          <div v-if="validationErrors.Objective" class="field-error-message">
            {{ validationErrors.Objective }}
          </div>
        </div>
        
        <!-- Business Units, Identifier and IsRisk in one row -->
        <div class="row-fields">
          <div class="compliance-field">
            <label>Business Units Covered</label>
            <div class="searchable-dropdown">
              <input 
                v-model="businessUnitSearch" 
                class="compliance-input" 
                placeholder="Search or add business units"
                title="Departments or business units affected by this compliance"
                @focus="showDropdown('BusinessUnitsCovered')"
                @input="filterOptions('BusinessUnitsCovered')"
              />
              <div v-show="activeDropdown === 'BusinessUnitsCovered'" class="dropdown-options">
                <div v-if="filteredOptions.BusinessUnitsCovered.length === 0 && businessUnitSearch" class="dropdown-add-option">
                  <span>No matches found. Add new:</span>
                  <button @click="addNewOption('BusinessUnitsCovered', businessUnitSearch)" class="dropdown-add-btn">
                    + Add "{{ businessUnitSearch }}"
                  </button>
                </div>
                <div 
                  v-for="option in filteredOptions.BusinessUnitsCovered" 
                  :key="option.id" 
                  class="dropdown-option"
                  @click="selectOption('BusinessUnitsCovered', option.value)"
                >
                  {{ option.value }}
                </div>
              </div>
            </div>
          </div>
          
          <div class="compliance-field">
            <label>Identifier</label>
            <input 
              v-model="compliance.Identifier" 
              class="compliance-input" 
              placeholder="Auto-generated if left empty"
              title="A new identifier will be generated"
              disabled
            />
            <small>A new identifier will be generated</small>
          </div>

          <div class="compliance-field checkbox-container">
            <label style="font-weight: 500; font-size: 1rem; display: flex; align-items: center; gap: 8px;" title="Check if this compliance item represents a risk">
              <input type="checkbox" v-model="compliance.IsRisk" style="margin-right: 8px; width: auto;" />
              Is Risk
            </label>
          </div>
        </div>
      </div>

      <!-- Risk related fields - grouped together -->
      <div class="field-group risk-fields" v-if="compliance.IsRisk">
        <div class="field-group-title">Risk Information</div>
        <div class="compliance-field full-width">
          <label>
            Possible Impact
            <span class="required">*</span>
            <span class="field-requirements">(Minimum 20 characters)</span>
          </label>
          <textarea 
            v-model="compliance.PossibleDamage" 
            class="compliance-input"
            :class="{ 'error': validationErrors.PossibleDamage }"
            :ref="'field_PossibleDamage'"
            placeholder="Describe potential damage that could occur if this risk materializes"
            @input="validateFieldRealTime('PossibleDamage')"
            @blur="validateField('PossibleDamage')"
            rows="3"
            required
          ></textarea>
          <div class="char-count" :class="{ 'error': validationErrors.PossibleDamage }">
            {{ compliance.PossibleDamage?.length || 0 }}/20 min characters
          </div>
          <div v-if="validationErrors.PossibleDamage" class="field-error-message">
            {{ validationErrors.PossibleDamage }}
          </div>
        </div>
        
        <div class="compliance-field full-width">
          <label>
            Mitigation Steps
            <span v-if="compliance.IsRisk" class="required">*</span>
          </label>
          <div class="mitigation-steps">
            <div v-for="(step, stepIndex) in mitigationSteps" :key="stepIndex" class="mitigation-step">
              <div class="step-header">
                <span class="step-numberr">Step {{ stepIndex + 1 }}</span>
                <button type="button" class="remove-step-btn" @click="removeStep(stepIndex)" title="Remove this step">
                  <i class="fas fa-times"></i>
                </button>
              </div>
              <textarea
                v-model="step.description"
                @input="onMitigationStepChange"
                @blur="onMitigationStepChange"
                class="compliance-input"
                :class="{
                  'error': validationErrors.mitigation,
                  'valid': isFieldValid('mitigation')
                }"
                placeholder="Describe this mitigation step"
                rows="2"
                required
                :maxlength="validationRules.maxLengths.mitigation"
              ></textarea>
            </div>
            <button type="button" class="add-step-btn" @click="addStep" title="Add new mitigation step">
              <i class="fas fa-plus"></i> Add Step
            </button>
          </div>
          <div v-if="validationErrors.mitigation" class="field-error-message">
            {{ validationErrors.mitigation }}
          </div>
        </div>
        
        <div class="compliance-field full-width">
          <label>
            Potential Risk Scenarios
            <span class="required">*</span>
            <span class="field-requirements">(Minimum 20 characters)</span>
          </label>
          <textarea 
            v-model="compliance.PotentialRiskScenarios" 
            class="compliance-input"
            :class="{ 'error': validationErrors.PotentialRiskScenarios }"
            :ref="'field_PotentialRiskScenarios'"
            placeholder="Describe scenarios where this risk could materialize"
            @input="validateFieldRealTime('PotentialRiskScenarios')"
            @blur="validateField('PotentialRiskScenarios')"
            rows="3"
            required
          ></textarea>
          <div class="char-count" :class="{ 'error': validationErrors.PotentialRiskScenarios }">
            {{ compliance.PotentialRiskScenarios?.length || 0 }}/20 min characters
          </div>
          <div v-if="validationErrors.PotentialRiskScenarios" class="field-error-message">
            {{ validationErrors.PotentialRiskScenarios }}
          </div>
        </div>
        
        <div class="row-fields">
          <div class="compliance-field">
            <label>Risk Type</label>
            <select 
              v-model="compliance.RiskType" 
              class="compliance-select"
              :class="{ 'error': validationErrors.RiskType }"
              :ref="'field_RiskType'"
              title="Type of risk"
              @change="validateFieldRealTime('RiskType')"
              @blur="validateField('RiskType')"
            >
              <option value="">Select Risk Type</option>
              <option value="Current">Current</option>
              <option value="Residual">Residual</option>
              <option value="Inherent">Inherent</option>
              <option value="Emerging">Emerging</option>
              <option value="Accepted">Accepted</option>
            </select>
            <div v-if="validationErrors.RiskType" class="field-error-message">
              {{ validationErrors.RiskType }}
            </div>
          </div>
          
          <div class="compliance-field">
            <label>Risk Category</label>
            <div class="searchable-dropdown">
              <input 
                v-model="riskCategorySearch" 
                class="compliance-input" 
                placeholder="Search or add risk category"
                title="Category of risk (e.g. People, Process, Technology)"
                @focus="showDropdown('RiskCategory')"
                @input="filterOptions('RiskCategory')"
              />
              <div v-show="activeDropdown === 'RiskCategory'" class="dropdown-options">
                <div v-if="filteredOptions.RiskCategory.length === 0 && riskCategorySearch" class="dropdown-add-option">
                  <span>No matches found. Add new:</span>
                  <button @click="addNewOption('RiskCategory', riskCategorySearch)" class="dropdown-add-btn">
                    + Add "{{ riskCategorySearch }}"
                  </button>
                </div>
                <div 
                  v-for="option in filteredOptions.RiskCategory" 
                  :key="option.id" 
                  class="dropdown-option"
                  @click="selectOption('RiskCategory', option.value)"
                >
                  {{ option.value }}
                </div>
              </div>
            </div>
          </div>
          
          <div class="compliance-field">
            <label>Risk Business Impact</label>
            <div class="searchable-dropdown">
              <input 
                v-model="riskBusinessImpactSearch" 
                class="compliance-input" 
                placeholder="Search or add business impact"
                title="How this risk impacts business operations"
                @focus="showDropdown('RiskBusinessImpact')"
                @input="filterOptions('RiskBusinessImpact')"
              />
              <div v-show="activeDropdown === 'RiskBusinessImpact'" class="dropdown-options">
                <div v-if="filteredOptions.RiskBusinessImpact.length === 0 && riskBusinessImpactSearch" class="dropdown-add-option">
                  <span>No matches found. Add new:</span>
                  <button @click="addNewOption('RiskBusinessImpact', riskBusinessImpactSearch)" class="dropdown-add-btn">
                    + Add "{{ riskBusinessImpactSearch }}"
                  </button>
                </div>
                <div 
                  v-for="option in filteredOptions.RiskBusinessImpact" 
                  :key="option.id" 
                  class="dropdown-option"
                  @click="selectOption('RiskBusinessImpact', option.value)"
                >
                  {{ option.value }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Compliance classification fields - grouped together -->
      <div class="field-group classification-fields">
        <div class="field-group-title">Classification</div>
        <div class="row-fields">
          <div class="compliance-field">
            <label>Criticality</label>
            <select 
              v-model="compliance.Criticality" 
              class="compliance-select" 
              required
              title="How critical this compliance item is to the organization"
            >
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>
          
          <div class="compliance-field">
            <label>Mandatory/Optional</label>
            <select 
              v-model="compliance.MandatoryOptional" 
              class="compliance-select" 
              required
              title="Whether this compliance item is mandatory or optional"
            >
              <option value="Mandatory">Mandatory</option>
              <option value="Optional">Optional</option>
            </select>
          </div>
        </div>
        
        <div class="row-fields">
          <div class="compliance-field">
            <label>Manual/Automatic</label>
            <select 
              v-model="compliance.ManualAutomatic" 
              class="compliance-select" 
              required
              title="Whether this compliance is checked manually or automatically"
            >
              <option value="Manual">Manual</option>
              <option value="Automatic">Automatic</option>
            </select>
          </div>
          
          <div class="compliance-field">
            <label>Applicability</label>
            <input 
              v-model="compliance.Applicability" 
              class="compliance-input" 
              placeholder="Applicability from policy"
              title="Describes where this compliance item applies"
            />
          </div>
        </div>
        
        <div class="row-fields">
          <div class="compliance-field">
            <label>Severity Rating (1-10)</label>
            <input 
              type="number" 
              v-model.number="compliance.Impact" 
              @input="validateImpact"
              class="compliance-input" 
              step="0.1" 
              min="1" 
              max="10"
              title="Rate the Severity Rating from 1 (lowest) to 10 (highest)"
            />
            <span v-if="impactError" class="validation-error">
              Severity Rating must be between 1 and 10
            </span>
          </div>
          
          <div class="compliance-field">
            <label>Probability (1-10)</label>
            <input 
              type="number" 
              v-model.number="compliance.Probability" 
              @input="validateProbability"
              class="compliance-input" 
              step="0.1" 
              min="1" 
              max="10"
              title="Rate the probability from 1 (lowest) to 10 (highest)"
            />
            <span v-if="probabilityError" class="validation-error">
              Probability must be between 1 and 10
            </span>
          </div>
        </div>
        
        <div class="row-fields">
          <div class="compliance-field">
            <label>Maturity Level</label>
            <select 
              v-model="compliance.MaturityLevel" 
              class="compliance-select"
              title="Current maturity level of this compliance item"
            >
              <option>Initial</option>
              <option>Developing</option>
              <option>Defined</option>
              <option>Managed</option>
              <option>Optimizing</option>
            </select>
          </div>
        </div>
      </div>
      
      <!-- Approval section -->
      <div class="field-group approval-fields">
        <div class="field-group-title">Approval Information</div>
        <div class="reviewer-warning-box" v-if="compliance.reviewer_id">
          <i class="fas fa-info-circle"></i>
          <span>
            <strong>Important:</strong> The compliance approval task will be assigned to <strong>{{ users.find(u => u.UserId === compliance.reviewer_id)?.UserName || 'Selected Reviewer' }}</strong>.
            Make sure this is the correct person who should review this compliance.
          </span>
        </div>
        <!-- Approver and Approval Due Date in the same row -->
        <div class="row-fields">
          <!-- Assign Reviewer -->
          <div class="compliance-field">
            <label>
              Assign Reviewer
              <span class="required">*</span>
              <span class="field-requirements">(Required - This person will see the task in their Reviewer Tasks)</span>
            </label>
            <select 
              v-model="compliance.reviewer_id" 
              class="compliance-select" 
              required
              title="Person responsible for reviewing this compliance item"
            >
              <option value="" disabled>Select Reviewer</option>
              <option v-for="user in users" :key="user.UserId" :value="user.UserId">
                {{ user.UserName }} {{ user.email ? `(${user.email})` : '' }}
              </option>
            </select>
            <span v-if="!users.length" class="validation-error">No reviewers available</span>
          </div>
          <!-- Approval Due Date -->

        </div>
      </div>
    </div>
    
        <div class="compliance-submit-container">
                <button 
        class="compliance-submit-btn" 
        @click="validateAndSubmit"
        :disabled="loading || !canSaveCopy"
      >
        <span v-if="loading">Saving...</span>
        <span v-else>Save Copy</span>
      </button>
          <button 
            class="compliance-cancel-btn" 
            @click="cancelCopy"
            :disabled="loading"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { complianceService } from '@/services/api';
import complianceDataService from '@/services/complianceService'; // NEW: Use cached compliance data
import { CompliancePopups } from './utils/popupUtils';

export default {
  name: 'CopyCompliance',
  data() {
    return {
      compliance: null,
      users: [],
      frameworks: [],
      policies: [],
      subPolicies: [],
      targetFrameworkId: '',
      targetPolicyId: '',
      targetSubPolicyId: '',
      loading: false,
      error: null,
      successMessage: null,
      impactError: false,
      probabilityError: false,
      originalComplianceId: null,
      localSourceSubPolicyId: null,
      categoryOptions: {
        BusinessUnitsCovered: [],
        RiskCategory: [],
        RiskBusinessImpact: []
      },
      filteredOptions: {
        BusinessUnitsCovered: [],
        RiskCategory: [],
        RiskBusinessImpact: []
      },
      businessUnitSearch: '',
      riskCategorySearch: '',
      riskBusinessImpactSearch: '',
      activeDropdown: null,
      validationErrors: {},
      mitigationSteps: [{ description: '' }],
      validationRules: {
        // Character set patterns
        textPattern: /^[a-zA-Z0-9\s.,!?\-_()[\]{}:;'"&%$#@+=\n\r\t]*$/,
        alphanumericPattern: /^[a-zA-Z0-9\s.\-_]*$/,
        identifierPattern: /^[a-zA-Z0-9\-_]*$/,
        
        // Field length limits
        maxLengths: {
          ComplianceTitle: 145,
          ComplianceItemDescription: 5000,
          ComplianceType: 100,
          Scope: 5000,
          Objective: 5000,
          BusinessUnitsCovered: 225,
          Identifier: 45,
          PossibleDamage: 5000,
          mitigation: 5000,
          PotentialRiskScenarios: 5000,
          RiskType: 45,
          RiskCategory: 45,
          RiskBusinessImpact: 45,
          Applicability: 45
        },
        
        // Field minimum length requirements
        minLengths: {
          ComplianceTitle: 3,
          ComplianceItemDescription: 10,
          ComplianceType: 3,
          Scope: 15,
          Objective: 10,
          BusinessUnitsCovered: 3,
          mitigation: 10,
          PossibleDamage: 10,
          PotentialRiskScenarios: 10,
          RiskType: 3,
          RiskCategory: 3,
          RiskBusinessImpact: 3
        },
        
        // Allowed choice values
        allowedChoices: {
          Criticality: ['High', 'Medium', 'Low'],
          MandatoryOptional: ['Mandatory', 'Optional'],
          ManualAutomatic: ['Manual', 'Automatic']
        },
        
        // Numeric field ranges
        numericRanges: {
          Impact: { min: 1, max: 10 },
          Probability: { min: 1, max: 10 }
        }
      },
      fieldStates: {}
    }
  },
  computed: {
    canSaveCopy() {
      // Validate all required fields are filled
      let isValid = this.compliance && 
        this.compliance.ComplianceItemDescription &&
        this.targetFrameworkId &&
        this.targetPolicyId &&
        this.targetSubPolicyId &&
        this.compliance.Criticality &&
        this.compliance.MandatoryOptional &&
        this.compliance.ManualAutomatic &&
        this.compliance.Impact && 
        this.compliance.Probability && 
        this.compliance.MaturityLevel &&
        this.compliance.reviewer_id;
      
      // If IsRisk is checked, also validate risk fields
      if (isValid && this.compliance && this.compliance.IsRisk) {
        isValid = isValid &&
          this.compliance.PossibleDamage &&
          this.compliance.RiskType &&
          this.compliance.RiskCategory &&
          this.compliance.RiskBusinessImpact;
      }
        
      // Only log every 10th check to avoid spam
      if (Math.random() < 0.1) {
        console.log('🔍 canSaveCopy check:', {
          isValid,
          targetFrameworkId: this.targetFrameworkId,
          targetPolicyId: this.targetPolicyId,
          targetSubPolicyId: this.targetSubPolicyId,
          hasCompliance: !!this.compliance,
          hasDescription: !!this.compliance?.ComplianceItemDescription,
          hasCriticality: !!this.compliance?.Criticality,
          hasReviewer: !!this.compliance?.reviewer_id,
          isRisk: !!this.compliance?.IsRisk
        });
      }
      
      return isValid;
    }
  },
  async created() {
    // Get the compliance ID from the route params
    const complianceId = this.$route.params.id;
    if (!complianceId) {
      this.error = 'No compliance ID provided';
      return;
    }
    
    this.originalComplianceId = complianceId;
    await this.loadComplianceData(complianceId);
    
    await this.loadUsers();
    await this.loadCategoryOptions();
    
    // Use passed context from route query or load frameworks
    await this.initializeFromContext();
    
    // Set default reviewer if not present
    if (this.compliance && !this.compliance.reviewer_id && this.users.length > 0) {
      this.compliance.reviewer_id = this.users[0].UserId;
      console.log('⚠️ DEFAULT REVIEWER ASSIGNED: User ID', this.users[0].UserId, '(' + this.users[0].UserName + ')');
      console.log('💡 TIP: Make sure to select the correct reviewer from the dropdown before submitting!');
    }
    
    // Add click event listener to close dropdowns when clicking outside
    document.addEventListener('click', this.handleClickOutside);
  },
  beforeUnmount() {
    // Remove event listener when component is unmounted
    document.removeEventListener('click', this.handleClickOutside);
  },
  watch: {
    targetFrameworkId(newValue) {
      if (newValue) {
        console.log('Framework changed to:', newValue); // Debug log
        this.validationErrors.targetFrameworkId = ''; // Clear validation error
        this.loadPolicies(newValue);
        this.targetPolicyId = '';
        this.targetSubPolicyId = '';
        this.policies = [];
        this.subPolicies = [];
      }
    },
    targetPolicyId(newValue) {
      if (newValue) {
        console.log('Policy changed to:', newValue); // Debug log
        this.validationErrors.targetPolicyId = ''; // Clear validation error
        this.loadSubPolicies(newValue);
        this.targetSubPolicyId = '';
        this.subPolicies = [];
        
        // Update applicability from the selected policy
        const selectedPolicy = this.policies.find(p => p.id === newValue);
        if (selectedPolicy && selectedPolicy.applicability && this.compliance) {
          this.compliance.Applicability = selectedPolicy.applicability;
          console.log('Updated applicability:', this.compliance.Applicability); // Debug log
        }
      }
    },
    targetSubPolicyId(newValue) {
      if (newValue) {
        console.log('Sub-policy changed to:', newValue); // Debug log
        this.validationErrors.targetSubPolicyId = ''; // Clear validation error
      }
    }
  },
  methods: {
    async loadComplianceData(complianceId) {
      try {
        this.loading = true;
        const response = await complianceService.getComplianceById(complianceId);
        
        if (response.data && response.data.success) {
          this.compliance = response.data.data;
          this.localSourceSubPolicyId = this.compliance.SubPolicy;

          console.log('Loaded compliance data:', this.compliance); // Debug log

          // Store framework and policy information for auto-population
          this.compliance.FrameworkId = response.data.data.FrameworkId;
          this.compliance.PolicyId = response.data.data.PolicyId;
          
          console.log('Framework ID:', this.compliance.FrameworkId, 'Policy ID:', this.compliance.PolicyId); // Debug log
          
          // Set default reviewer if not present
          if (!this.compliance.reviewer_id && this.users.length > 0) {
            this.compliance.reviewer_id = this.users[0].UserId;
            console.log('⚠️ DEFAULT REVIEWER ASSIGNED in loadComplianceData: User ID', this.users[0].UserId, '(' + this.users[0].UserName + ')');
          }
          
          // Clear identifier since a new one will be generated
          this.compliance.Identifier = '';

          // Format mitigation data if needed
          this.compliance.mitigation = this.formatMitigationData(this.compliance.mitigation);
          
          // --- Always parse mitigation steps on load ---
          this.mitigationSteps = this.parseMitigationSteps(this.compliance.mitigation);
          console.log('[loadComplianceData] Loaded mitigation:', this.compliance.mitigation);
          console.log('[loadComplianceData] Parsed steps:', this.mitigationSteps);
          
          // Initialize search fields with existing values
          this.initializeSearchFields();
        } else {
          this.error = 'Failed to load compliance data';
        }
      } catch (error) {
        console.error('Error loading compliance data:', error);
        this.error = 'Failed to load compliance data. Please try again.';
      } finally {
        this.loading = false;
      }
    },
    
    // Initialize search fields with existing compliance data
    initializeSearchFields() {
      if (this.compliance) {
        // Initialize business unit search
        if (this.compliance.BusinessUnitsCovered) {
          this.businessUnitSearch = this.compliance.BusinessUnitsCovered;
        }
        
        // Initialize risk category search
        if (this.compliance.RiskCategory) {
          this.riskCategorySearch = this.compliance.RiskCategory;
        }
        
        // Initialize risk business impact search
        if (this.compliance.RiskBusinessImpact) {
          this.riskBusinessImpactSearch = this.compliance.RiskBusinessImpact;
        }
        
        console.log('[initializeSearchFields] Initialized search fields:', {
          businessUnitSearch: this.businessUnitSearch,
          riskCategorySearch: this.riskCategorySearch,
          riskBusinessImpactSearch: this.riskBusinessImpactSearch
        });
        
        // Also update the filtered options to show the current values
        this.updateFilteredOptions();
      }
    },
    
    // Update filtered options to include current values
    updateFilteredOptions() {
      // Update filtered options for each field to ensure current values are shown
      if (this.compliance) {
        if (this.compliance.BusinessUnitsCovered && this.categoryOptions.BusinessUnitsCovered) {
          this.filteredOptions.BusinessUnitsCovered = this.categoryOptions.BusinessUnitsCovered.filter(option => 
            option.value.toLowerCase().includes(this.businessUnitSearch.toLowerCase())
          );
        }
        
        if (this.compliance.RiskCategory && this.categoryOptions.RiskCategory) {
          this.filteredOptions.RiskCategory = this.categoryOptions.RiskCategory.filter(option => 
            option.value.toLowerCase().includes(this.riskCategorySearch.toLowerCase())
          );
        }
        
        if (this.compliance.RiskBusinessImpact && this.categoryOptions.RiskBusinessImpact) {
          this.filteredOptions.RiskBusinessImpact = this.categoryOptions.RiskBusinessImpact.filter(option => 
            option.value.toLowerCase().includes(this.riskBusinessImpactSearch.toLowerCase())
          );
        }
      }
    },
    
    // Format mitigation data to ensure it's in the expected JSON format
    formatMitigationData(mitigation) {
      console.log('Formatting mitigation data:', mitigation, typeof mitigation);
      
      // If empty, return empty object
      if (!mitigation) return {};
      
      // If already an object, format it properly
      if (typeof mitigation === 'object' && mitigation !== null) {
        // Check if it's already in the numbered format
        if (Object.keys(mitigation).some(key => !isNaN(parseInt(key)))) {
          console.log('Mitigation is already in numbered format');
          return mitigation;
        }
        
        // Convert to numbered format
        const formattedMitigation = {};
        // Use Object.values instead since we only need the values
        Object.values(mitigation).forEach((value, index) => {
          formattedMitigation[(index + 1).toString()] = value;
        });
        
        console.log('Converted object mitigation to numbered format:', formattedMitigation);
        return formattedMitigation;
      }
      
      // If it's a string, try to parse as JSON first
      if (typeof mitigation === 'string') {
        try {
          if (mitigation.trim().startsWith('{')) {
            const parsedMitigation = JSON.parse(mitigation);
            console.log('Parsed mitigation JSON:', parsedMitigation);
            
            // If parsed successfully and it's an object, format it
            if (typeof parsedMitigation === 'object' && parsedMitigation !== null) {
              return this.formatMitigationData(parsedMitigation);
            }
          }
        } catch (e) {
          console.log('Failed to parse mitigation as JSON:', e);
        }
        
        // If parsing failed or it's not JSON, use as single step
        if (mitigation.trim()) {
          console.log('Using mitigation string as single step');
          return { "1": mitigation.trim() };
        }
      }
      
      // Default empty object
      return {};
    },
    
    // --- Mitigation Steps Logic ---
    parseMitigationSteps(mitigation) {
      console.log("[parseMitigationSteps] Input:", mitigation, typeof mitigation);
      if (!mitigation || (typeof mitigation === 'object' && Object.keys(mitigation).length === 0)) {
        return [{ description: '' }];
      }
      if (typeof mitigation === 'string') {
        try { 
          mitigation = JSON.parse(mitigation); 
        } catch { 
          return [{ description: '' }]; 
        }
      }
      if (typeof mitigation === 'object') {
        const sortedKeys = Object.keys(mitigation).sort((a, b) => parseInt(a) - parseInt(b));
        const steps = sortedKeys.map(key => ({ description: mitigation[key] || '' }));
        return steps.length ? steps : [{ description: '' }];
      }
      return [{ description: '' }];
    },
    
    onMitigationStepChange() {
      // Build mitigation JSON object in the exact format {"1": "qwertyuiolkjhgfdsa"}
      const mitigationJson = {};
      this.mitigationSteps.forEach((step, idx) => {
        if (step.description && step.description.trim()) {
          // Use string key format: "1", "2", "3" etc.
          mitigationJson[`${idx + 1}`] = step.description.trim();
        }
      });
      
      // Store as object, not string
      this.compliance.mitigation = mitigationJson;
      
      console.log('[onMitigationStepChange] Final mitigation format:', JSON.stringify(this.compliance.mitigation));
      this.validateField('mitigation');
    },
    
    addStep() {
      this.mitigationSteps.push({ description: '' });
      console.log("addStep - Added new step, total steps:", this.mitigationSteps.length);
      this.onMitigationStepChange();
    },
    
    removeStep(index) {
      if (this.mitigationSteps.length > 1) {
        this.mitigationSteps.splice(index, 1);
        console.log("removeStep - Removed step at index", index, ", remaining steps:", this.mitigationSteps.length);
        this.onMitigationStepChange();
      }
    },
    async initializeFromContext() {
      try {
        const query = this.$route.query;
        console.log('=== INITIALIZING FROM CONTEXT ==='); // Debug log
        console.log('Route query:', query); // Debug log
        console.log('Current route params:', this.$route.params); // Debug log
        
        // Check if we have context from the parent page
        if (query.frameworkId && query.frameworkName) {
          console.log('✓ Using context from parent page'); // Debug log
          console.log('Framework context:', {
            id: query.frameworkId,
            name: query.frameworkName
          }); // Debug log
          
          // Set up frameworks array with the current framework
          this.frameworks = [{
            id: parseInt(query.frameworkId),
            name: query.frameworkName
          }];
          
          // Set target framework
          this.targetFrameworkId = parseInt(query.frameworkId);
          console.log('Set targetFrameworkId:', this.targetFrameworkId, typeof this.targetFrameworkId);
          
          // Load policies for this framework
          await this.loadPolicies(parseInt(query.frameworkId));
          
          // Set target policy if available
          if (query.policyId && query.policyName) {
            this.targetPolicyId = parseInt(query.policyId);
            console.log('Set targetPolicyId:', this.targetPolicyId, typeof this.targetPolicyId);
          }
          
          // Load sub-policies if we have a policy
          if (query.policyId) {
            await this.loadSubPolicies(parseInt(query.policyId));
            
            // Set target sub-policy if available
            if (query.subPolicyId && query.subPolicyName) {
              this.targetSubPolicyId = parseInt(query.subPolicyId);
              console.log('Set targetSubPolicyId:', this.targetSubPolicyId, typeof this.targetSubPolicyId);
            }
          }
          
          console.log('Context initialized:', {
            framework: this.targetFrameworkId,
            policy: this.targetPolicyId,
            subPolicy: this.targetSubPolicyId
          });
          
          // Force reactivity update
          this.$forceUpdate();
          
          // Clear any validation errors for target fields
          this.validationErrors.targetFrameworkId = '';
          this.validationErrors.targetPolicyId = '';
          this.validationErrors.targetSubPolicyId = '';
          
          console.log('Cleared validation errors for target fields');
          
        } else {
          // Fall back to loading all frameworks
          console.log('✗ No context provided, loading all frameworks'); // Debug log
          console.log('Missing context items:', {
            frameworkId: !!query.frameworkId,
            frameworkName: !!query.frameworkName,
            policyId: !!query.policyId,
            subPolicyId: !!query.subPolicyId
          }); // Debug log
          await this.loadFrameworks();
          await this.autoPopulateTargetFields();
        }
      } catch (error) {
        console.error('Error initializing from context:', error);
        this.error = 'Failed to initialize page context. Please try again.';
      }
    },
    
    async autoPopulateTargetFields() {
      if (!this.compliance) return;
      
      try {
        console.log('Auto-populating target fields...'); // Debug log
        
        // Auto-select framework from source compliance
        if (this.compliance.FrameworkId) {
          this.targetFrameworkId = this.compliance.FrameworkId;
          console.log('Set target framework ID:', this.targetFrameworkId); // Debug log
          
          await this.loadPolicies(this.compliance.FrameworkId);
          
          // Pre-populate policy but don't force it - user can change
          if (this.compliance.PolicyId) {
            this.targetPolicyId = this.compliance.PolicyId;
            console.log('Set target policy ID:', this.targetPolicyId); // Debug log
            
            await this.loadSubPolicies(this.compliance.PolicyId);
            
            // Pre-populate sub-policy but don't force it - user can change
            if (this.compliance.SubPolicy) {
              this.targetSubPolicyId = this.compliance.SubPolicy;
              console.log('Set target sub-policy ID:', this.targetSubPolicyId); // Debug log
            }
          }
        }
      } catch (error) {
        console.error('Error auto-populating target fields:', error);
        this.error = 'Failed to auto-populate target fields. Please select manually.';
      }
    },
    async loadUsers() {
      try {
        this.loading = true;
        const response = await complianceService.getUsers();
        
        if (response.data.success && Array.isArray(response.data.users)) {
          this.users = response.data.users;
          console.log('✅ Loaded users for reviewer selection:', this.users.map(u => ({ id: u.UserId, name: u.UserName })));
        } else {
          console.error('Invalid users data received:', response.data);
          this.error = 'Failed to load approvers';
        }
      } catch (error) {
        console.error('Failed to load users:', error);
        this.error = 'Failed to load approvers. Please try again.';
      } finally {
        this.loading = false;
      }
    },
    async loadFrameworks() {
      try {
        this.loading = true;
        this.error = null; // Clear any previous errors
        console.log('🔍 [CopyCompliance] Checking for cached framework data...');
        
        // FIRST: Try to get data from cache
        if (complianceDataService.hasFrameworksCache()) {
          console.log('✅ [CopyCompliance] Using cached framework data');
          const cachedFrameworks = complianceDataService.getData('frameworks') || [];
          
          this.frameworks = cachedFrameworks.map(fw => ({
            id: fw.FrameworkId || fw.id,
            name: fw.FrameworkName || fw.name
          }));
          
          console.log(`[CopyCompliance] Loaded ${this.frameworks.length} frameworks from cache (prefetched on Home page)`);
          
          if (this.frameworks.length === 0) {
            console.warn('No frameworks found in cache');
            this.error = 'No frameworks available';
          }
        } else {
          // FALLBACK: Fetch from API if cache is empty
          console.log('⚠️ [CopyCompliance] No cached data found, fetching from API...');
          const response = await complianceService.getComplianceFrameworks();
          
          console.log('Frameworks API URL: /api/compliance/frameworks/'); // Debug log
          console.log('Frameworks response:', response.data); // Debug log
          
          // Handle both response formats: direct array or success wrapper
          let frameworksData;
          if (response.data.success && response.data.frameworks) {
            frameworksData = response.data.frameworks;
          } else if (Array.isArray(response.data)) {
            frameworksData = response.data;
          } else {
            console.error('Unexpected response format:', response.data);
            this.error = 'Failed to load frameworks - invalid response format';
            this.frameworks = [];
            return;
          }
          
          this.frameworks = frameworksData.map(fw => ({
            id: fw.id || fw.FrameworkId,
            name: fw.name || fw.FrameworkName
          }));
          
          console.log(`[CopyCompliance] Loaded ${this.frameworks.length} frameworks directly from API (cache unavailable)`);
          
          // Update cache so subsequent pages benefit
          if (frameworksData.length > 0) {
            complianceDataService.setData('frameworks', frameworksData);
            console.log('ℹ️ [CopyCompliance] Cache updated after direct API fetch');
          }
          
          if (this.frameworks.length === 0) {
            console.warn('No frameworks found');
            this.error = 'No frameworks available';
          }
        }
      } catch (error) {
        this.error = `Failed to load frameworks: ${error.response?.data?.message || error.message || 'Unknown error'}`;
        console.error('Framework loading error:', error);
        console.error('Error response:', error.response);
        this.frameworks = [];
      } finally {
        this.loading = false;
      }
    },
    async loadPolicies(frameworkId) {
      try {
        this.loading = true;
        this.error = null; // Clear any previous errors
        
        const response = await complianceService.getCompliancePolicies(frameworkId);
        
        console.log(`Policies API URL: /api/compliance/frameworks/${frameworkId}/policies/list/`); // Debug log
        console.log('Policies response for framework', frameworkId, ':', response.data); // Debug log
        
        let policiesData;
        if (response.data.success && response.data.policies) {
          policiesData = response.data.policies;
        } else if (Array.isArray(response.data)) {
          policiesData = response.data;
        } else {
          console.error('Error in response:', response.data);
          this.error = 'Failed to load policies for the selected framework';
          this.policies = [];
          return;
        }
        
        this.policies = policiesData.map(p => ({
          id: p.id || p.PolicyId,
          name: p.name || p.PolicyName,
          applicability: p.applicability || p.scope || p.Applicability || '' // Store the Applicability field
        }));
        
        console.log('Processed policies:', this.policies); // Debug log
        
        if (this.policies.length === 0) {
          console.warn('No policies found for framework:', frameworkId);
        }
      } catch (error) {
        this.error = `Failed to load policies: ${error.response?.data?.message || error.message || 'Unknown error'}`;
        console.error('Policy loading error:', error);
        console.error('Error response:', error.response);
        this.policies = [];
      } finally {
        this.loading = false;
      }
    },
    async loadSubPolicies(policyId) {
      try {
        this.loading = true;
        this.error = null; // Clear any previous errors
        
        const response = await complianceService.getComplianceSubPolicies(policyId);
        
        console.log(`Sub-policies API URL: /api/compliance/policies/${policyId}/subpolicies/`); // Debug log
        console.log('Sub-policies response for policy', policyId, ':', response.data); // Debug log
        
        let subpoliciesData;
        if (response.data.success && response.data.subpolicies) {
          subpoliciesData = response.data.subpolicies;
        } else if (Array.isArray(response.data)) {
          subpoliciesData = response.data;
        } else {
          console.error('Error in response:', response.data);
          this.error = 'Failed to load sub-policies for the selected policy';
          this.subPolicies = [];
          return;
        }
        
        this.subPolicies = subpoliciesData.map(sp => ({
          id: sp.id || sp.SubPolicyId,
          name: sp.name || sp.SubPolicyName
        }));
        
        console.log('Processed sub-policies:', this.subPolicies); // Debug log
        
        if (this.subPolicies.length === 0) {
          console.warn('No sub-policies found for policy:', policyId);
        }
      } catch (error) {
        this.error = `Failed to load sub-policies: ${error.response?.data?.message || error.message || 'Unknown error'}`;
        console.error('Sub-policy loading error:', error);
        console.error('Error response:', error.response);
        this.subPolicies = [];
      } finally {
        this.loading = false;
      }
    },
    validateImpact(event) {
      const value = parseFloat(event.target.value);
      this.impactError = value < 1 || value > 10;
    },
    validateProbability(event) {
      const value = parseFloat(event.target.value);
      this.probabilityError = value < 1 || value > 10;
    },
    
    getDefaultDueDate() {
      const date = new Date();
      date.setDate(date.getDate() + 7); // 7 days from now
      return date.toISOString().split('T')[0]; // Format as YYYY-MM-DD
    },
    async submitCopy() {
      if (this.loading) return; // Prevent double submission
      if (!this.canSaveCopy) {
        this.error = 'Please fill all required fields and select a destination.';
        return;
      }
      try {
        this.loading = true;
        this.error = null;
        this.successMessage = null;
        
        console.log('🚀 Preparing clone data...');
        console.log('Original compliance:', this.compliance);
        console.log('Target SubPolicy ID:', this.targetSubPolicyId);
        
        // Use the mitigation data directly from compliance.mitigation (already in correct format)
        let mitigationData = this.compliance.mitigation || {};
        
        // If it's a string, parse it
        if (typeof mitigationData === 'string') {
          try {
            mitigationData = JSON.parse(mitigationData);
          } catch (e) {
            mitigationData = {};
          }
        }
        
        console.log("Final mitigation format for submission:", JSON.stringify(mitigationData));
        
        const cloneData = {
          // Basic compliance fields
          ComplianceTitle: this.compliance.ComplianceTitle || '',
          ComplianceItemDescription: this.compliance.ComplianceItemDescription || '',
          ComplianceType: this.compliance.ComplianceType || '',
          Scope: this.compliance.Scope || '',
          Objective: this.compliance.Objective || '',
          BusinessUnitsCovered: this.compliance.BusinessUnitsCovered || '',
          // Risk fields
          IsRisk: Boolean(this.compliance.IsRisk),
          PossibleDamage: this.compliance.PossibleDamage || '',
          mitigation: mitigationData, // Using the processed mitigation data
          PotentialRiskScenarios: this.compliance.PotentialRiskScenarios || '',
          RiskType: this.compliance.RiskType || '',
          RiskCategory: this.compliance.RiskCategory || '',
          RiskBusinessImpact: this.compliance.RiskBusinessImpact || '',
          // Classification fields
          Criticality: this.compliance.Criticality || 'Medium',
          MandatoryOptional: this.compliance.MandatoryOptional || 'Mandatory',
          ManualAutomatic: this.compliance.ManualAutomatic || 'Manual',
          Impact: String(this.compliance.Impact || 5.0),
          Probability: String(this.compliance.Probability || 5.0),
          MaturityLevel: this.compliance.MaturityLevel || 'Initial',
          // Target location - CRITICAL: Make sure both field names are included
          SubPolicy: this.targetSubPolicyId,
          target_subpolicy_id: this.targetSubPolicyId,
          // Status fields
          Status: 'Under Review',
          ActiveInactive: 'Inactive',
          ComplianceVersion: '1.0',
          PermanentTemporary: this.compliance.PermanentTemporary || 'Permanent',
          // Reviewer
          reviewer_id: this.compliance.reviewer_id, // Only use the selected dropdown value
          reviewer: this.compliance.reviewer_id, // Only use the selected dropdown value
          // Other fields
          Applicability: this.compliance.Applicability || '',
          Identifier: '', // Will be auto-generated
          CreatedByName: '', // Do not set user id by default
          UserId: this.getCurrentUserId(), // Set the logged-in user id
          // Ensure all dates are properly formatted
          ApprovalDueDate: this.getDefaultDueDate(),
          // Add any missing fields that might be required by backend
          ComplianceId: null, // Will be auto-generated
          FrameworkId: null, // Not needed for clone
          PolicyId: null // Not needed for clone
        };

        console.log('📦 Clone data prepared:', cloneData);
        console.log('🔑 Key fields check:');
        console.log('- SubPolicy:', cloneData.SubPolicy);
        console.log('- target_subpolicy_id:', cloneData.target_subpolicy_id);
        console.log('- reviewer_id:', cloneData.reviewer_id, '(', this.users.find(u => u.UserId === cloneData.reviewer_id)?.UserName || 'Unknown', ')');
        console.log('- creator UserId:', cloneData.UserId);
        console.log('- ApprovalDueDate:', cloneData.ApprovalDueDate);
        console.log('Final mitigation format being sent:', JSON.stringify(cloneData.mitigation));

        const response = await complianceService.cloneCompliance(
          this.originalComplianceId,
          cloneData
        );

        console.log('📬 Clone response:', response.data);

        if (response.data.success) {
          // Show success popup with the correct data structure
          CompliancePopups.complianceCloned({
            ComplianceId: response.data.compliance_id
          });
          this.successMessage = 'Compliance copied successfully!';
          
          // Navigate back to the tailoring page after a short delay
          setTimeout(() => {
            this.$router.push('/compliance/tailoring');
          }, 1500);
        } else {
          this.error = response.data.message || 'Failed to copy compliance';
        }
      } catch (error) {
        console.error('Copy error:', error);
        console.error('Error response:', error.response);
        this.error = 'Failed to copy compliance: ' + (error.response?.data?.message || error.message);
      } finally {
        this.loading = false;
      }
    },
    cancelCopy() {
      // Navigate back to tailoring page
      this.$router.push('/compliance/tailoring');
    },
    
    goBack() {
      // Navigate back to tailoring page with current context
      const query = this.$route.query;
      if (query.frameworkId && query.policyId && query.subPolicyId) {
        // Go back to tailoring page (it will handle context restoration)
        this.$router.push('/compliance/tailoring');
      } else {
        // Generic back navigation
        if (window.history.length > 1) {
          this.$router.go(-1);
        } else {
          this.$router.push('/compliance/tailoring');
        }
      }
    },
    async loadCategoryOptions() {
      try {
        this.loading = true;
        
        // Load business units
        const buResponse = await complianceService.getCategoryBusinessUnits('BusinessUnitsCovered');
        console.log('BusinessUnitsCovered API response:', buResponse);
        if (buResponse.data.success && buResponse.data.data && Array.isArray(buResponse.data.data) && buResponse.data.data.length > 0) {
          // Validate that each item has the expected structure
          const validData = buResponse.data.data.filter(item => item && typeof item === 'object' && item.value && item.value.trim());
          console.log('Valid BusinessUnitsCovered data:', validData);
          
          if (validData.length > 0) {
            this.categoryOptions.BusinessUnitsCovered = validData;
            this.filteredOptions.BusinessUnitsCovered = [...validData];
          } else {
            console.warn('No valid BusinessUnitsCovered data found, using fallback');
            this.useFallbackBusinessUnits();
          }
        } else {
          console.warn('BusinessUnitsCovered API response invalid, using fallback');
          this.useFallbackBusinessUnits();
        }
        
        // Load risk categories
        const rcResponse = await complianceService.getCategoryBusinessUnits('RiskCategory');
        console.log('RiskCategory API response:', rcResponse);
        if (rcResponse.data.success && rcResponse.data.data && Array.isArray(rcResponse.data.data) && rcResponse.data.data.length > 0) {
          // Validate that each item has the expected structure
          const validData = rcResponse.data.data.filter(item => item && typeof item === 'object' && item.value && item.value.trim());
          console.log('Valid RiskCategory data:', validData);
          
          if (validData.length > 0) {
            this.categoryOptions.RiskCategory = validData;
            this.filteredOptions.RiskCategory = [...validData];
          } else {
            console.warn('No valid RiskCategory data found, using fallback');
            this.useFallbackRiskCategories();
          }
        } else {
          console.warn('RiskCategory API response invalid, using fallback');
          this.useFallbackRiskCategories();
        }
        
        // Load risk business impacts
        const rbiResponse = await complianceService.getCategoryBusinessUnits('RiskBusinessImpact');
        console.log('RiskBusinessImpact API response:', rbiResponse);
        if (rbiResponse.data.success && rbiResponse.data.data && Array.isArray(rbiResponse.data.data) && rbiResponse.data.data.length > 0) {
          // Validate that each item has the expected structure
          const validData = rbiResponse.data.data.filter(item => item && typeof item === 'object' && item.value && item.value.trim());
          console.log('Valid RiskBusinessImpact data:', validData);
          
          if (validData.length > 0) {
            this.categoryOptions.RiskBusinessImpact = validData;
            this.filteredOptions.RiskBusinessImpact = [...validData];
          } else {
            console.warn('No valid RiskBusinessImpact data found, using fallback');
            this.useFallbackRiskBusinessImpacts();
          }
        } else {
          console.warn('RiskBusinessImpact API response invalid, using fallback');
          this.useFallbackRiskBusinessImpacts();
        }
        
        console.log('All category options loaded successfully');
        
        // Re-initialize search fields after loading category options
        // This ensures search fields are properly set even if compliance data was loaded first
        this.initializeSearchFields();
      } catch (error) {
        console.error('Failed to load category options:', error);
        CompliancePopups.error('Failed to load dropdown options. Some features may be limited.');
      } finally {
        this.loading = false;
      }
    },
    
    // Fallback methods for when API data is invalid
    useFallbackBusinessUnits() {
      const fallbackData = [
        { id: 1, value: 'Sales & Marketing' },
        { id: 2, value: 'Finance & Accounting' },
        { id: 3, value: 'Human Resources' },
        { id: 4, value: 'Information Technology' },
        { id: 5, value: 'Operations' },
        { id: 6, value: 'Legal & Compliance' },
        { id: 7, value: 'Customer Service' },
        { id: 8, value: 'Research & Development' },
        { id: 9, value: 'Procurement' },
        { id: 10, value: 'Risk Management' }
      ];
      this.categoryOptions.BusinessUnitsCovered = fallbackData;
      this.filteredOptions.BusinessUnitsCovered = [...fallbackData];
      console.log('Using fallback BusinessUnitsCovered options:', fallbackData);
    },
    
    useFallbackRiskCategories() {
      const fallbackData = [
        { id: 1, value: 'People Risk' },
        { id: 2, value: 'Process Risk' },
        { id: 3, value: 'Technology Risk' },
        { id: 4, value: 'External Risk' },
        { id: 5, value: 'Information Risk' },
        { id: 6, value: 'Physical Risk' },
        { id: 7, value: 'Systems Risk' },
        { id: 8, value: 'Vendor Risk' },
        { id: 9, value: 'Regulatory Risk' },
        { id: 10, value: 'Fraud Risk' }
      ];
      this.categoryOptions.RiskCategory = fallbackData;
      this.filteredOptions.RiskCategory = [...fallbackData];
      console.log('Using fallback RiskCategory options:', fallbackData);
    },
    
    useFallbackRiskBusinessImpacts() {
      const fallbackData = [
        { id: 1, value: 'Revenue Loss' },
        { id: 2, value: 'Customer Impact' },
        { id: 3, value: 'Operational Disruption' },
        { id: 4, value: 'Brand Damage' },
        { id: 5, value: 'Regulatory Penalties' },
        { id: 6, value: 'Legal Costs' },
        { id: 7, value: 'Data Loss' },
        { id: 8, value: 'Service Downtime' },
        { id: 9, value: 'Productivity Loss' },
        { id: 10, value: 'Compliance Violations' }
      ];
      this.categoryOptions.RiskBusinessImpact = fallbackData;
      this.filteredOptions.RiskBusinessImpact = [...fallbackData];
      console.log('Using fallback RiskBusinessImpact options:', fallbackData);
          },
      
      // Refresh category options manually
      async refreshCategoryOptions() {
        try {
          console.log('Manually refreshing category options...');
          this.loading = true;
          this.error = null;
          
          // Clear existing options
          this.categoryOptions = {
            BusinessUnitsCovered: [],
            RiskCategory: [],
            RiskBusinessImpact: []
          };
          this.filteredOptions = {
            BusinessUnitsCovered: [],
            RiskCategory: [],
            RiskBusinessImpact: []
          };
          
          // Reload all category options
          await this.loadCategoryOptions();
          
          this.successMessage = 'Category options refreshed successfully!';
          setTimeout(() => {
            this.successMessage = null;
          }, 3000);
          
        } catch (error) {
          console.error('Failed to refresh category options:', error);
          this.error = 'Failed to refresh category options. Please try again.';
        } finally {
          this.loading = false;
        }
      },
      
      // Show dropdown for a specific field
      showDropdown(field) {
      // Close any open dropdown
      this.activeDropdown = field;
      
      // Set initial filtered options based on current search term
      this.filterOptions(field);
      
      // Prevent event from bubbling up
      event.stopPropagation();
    },
    
    // Handle clicking outside of dropdowns
    handleClickOutside(event) {
      // Check if click is outside any dropdown
      const dropdowns = document.querySelectorAll('.searchable-dropdown');
      let clickedOutside = true;
      
      dropdowns.forEach(dropdown => {
        if (dropdown.contains(event.target)) {
          clickedOutside = false;
        }
      });
      
      if (clickedOutside) {
        this.activeDropdown = null;
      }
    },
    
    // Filter dropdown options based on search term
    filterOptions(field) {
      let searchTerm = '';
      
      switch (field) {
        case 'BusinessUnitsCovered':
          searchTerm = this.businessUnitSearch || '';
          break;
        case 'RiskCategory':
          searchTerm = this.riskCategorySearch || '';
          break;
        case 'RiskBusinessImpact':
          searchTerm = this.riskBusinessImpactSearch || '';
          break;
      }
      
      // Filter options based on search term (case-insensitive)
      const lowerSearchTerm = searchTerm.toLowerCase();
      this.filteredOptions[field] = this.categoryOptions[field].filter(option => 
        option.value.toLowerCase().includes(lowerSearchTerm)
      );
    },
    
    // Select an option from the dropdown
    selectOption(field, value) {
      // Update the compliance item with the selected value
      this.compliance[field] = value;
      
      // Update the search field to show the selected value
      switch (field) {
        case 'BusinessUnitsCovered':
          this.businessUnitSearch = value;
          break;
        case 'RiskCategory':
          this.riskCategorySearch = value;
          break;
        case 'RiskBusinessImpact':
          this.riskBusinessImpactSearch = value;
          break;
      }
      
      // Close the dropdown
      this.activeDropdown = null;
    },
    
    // Add a new option to the category options
    async addNewOption(field, value) {
      try {
        const response = await complianceService.addCategoryBusinessUnit({
          source: field,
          value: value
        });
        
        if (response.data.success) {
          // Add the new option to the category options
          this.categoryOptions[field].push(response.data.data);
          
          // Select the new option
          this.selectOption(field, value);
          
          CompliancePopups.success(`Added new ${field} option: ${value}`);
        }
      } catch (error) {
        console.error(`Failed to add new ${field} option:`, error);
        CompliancePopups.error(`Failed to add new option: ${error.message || error}`);
      }
    },
    scrollToError() {
      const errorFields = Object.keys(this.validationErrors).filter(field => this.validationErrors[field]);
      console.log('📍 Scrolling to error for fields:', errorFields);
      
      if (errorFields.length > 0) {
        const firstErrorField = errorFields[0];
        console.log('🎯 First error field:', firstErrorField);
        
        // Handle target fields differently since they don't have refs with field_ prefix
        let errorElement;
        if (firstErrorField.startsWith('target')) {
          const fieldMap = {
            'targetFrameworkId': 'framework',
            'targetPolicyId': 'policy', 
            'targetSubPolicyId': 'subpolicy'
          };
          errorElement = document.getElementById(fieldMap[firstErrorField]);
        } else {
          errorElement = this.$refs[`field_${firstErrorField}`];
        }
        
        if (errorElement) {
          console.log('✅ Found error element, scrolling...');
          errorElement.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
          });
          if (errorElement.focus) {
            errorElement.focus();
          }
        } else {
          console.log('❌ Error element not found for:', firstErrorField);
          // Fallback: scroll to target location section
          const targetSection = document.querySelector('.selection-fields');
          if (targetSection) {
            targetSection.scrollIntoView({
              behavior: 'smooth',
              block: 'center'
            });
          }
        }
      }
    },
    validateFieldRealTime(fieldName) {
      // Skip validation for risk-related fields if IsRisk is false or not set
      const riskFields = ['PossibleDamage', 'mitigation', 'PotentialRiskScenarios', 'RiskType', 
                         'RiskCategory', 'RiskBusinessImpact'];
      
      if (riskFields.includes(fieldName) && (!this.compliance || this.compliance.IsRisk !== true)) {
        // Clear any existing validation errors for this field
        this.validationErrors[fieldName] = '';
        if (!this.fieldStates[fieldName]) {
          this.fieldStates[fieldName] = { valid: true, warning: false, dirty: false };
        } else {
          this.fieldStates[fieldName].valid = true;
          this.fieldStates[fieldName].warning = false;
        }
        return true;
      }

      const value = this.compliance[fieldName];
      const rules = this.validationRules;
      
      // Initialize field state if not exists
      if (!this.fieldStates[fieldName]) {
        this.fieldStates[fieldName] = {
          dirty: false,
          valid: false,
          warning: false
        };
      }
      
      this.fieldStates[fieldName].dirty = true;
      
      let isValid = true;
      let showWarning = false;
      let errorMessage = '';
      
      // Validate required fields
      let requiredFields = [
        'ComplianceTitle', 'ComplianceItemDescription', 'ComplianceType', 'Scope', 'Objective',
        'BusinessUnitsCovered', 'Criticality', 'MandatoryOptional', 'ManualAutomatic',
        'Impact', 'Probability', 'MaturityLevel', 'reviewer_id'
      ];
      
      // Only add risk fields to required if IsRisk is explicitly checked (true)
      if (this.compliance && this.compliance.IsRisk === true) {
        requiredFields.push('PossibleDamage', 'PotentialRiskScenarios', 'RiskType',
                           'RiskCategory', 'RiskBusinessImpact', 'mitigation');
      }
      
      if (requiredFields.includes(fieldName)) {
        if (!value || value.toString().trim() === '') {
          isValid = false;
          errorMessage = `${fieldName} is required`;
        }
      }
      
      // Validate minimum lengths
      if (rules.minLengths && rules.minLengths[fieldName] && value) {
        const minLength = rules.minLengths[fieldName];
        if (value.toString().length < minLength) {
          isValid = false;
          if (value.toString().length > 0) {
            showWarning = true;
            errorMessage = `Need ${minLength - value.toString().length} more characters`;
          }
        }
      }
      
      // Validate maximum lengths
      if (rules.maxLengths && rules.maxLengths[fieldName] && value) {
        const maxLength = rules.maxLengths[fieldName];
        if (value.length > maxLength) {
          isValid = false;
          errorMessage = `Must not exceed ${maxLength} characters`;
        }
      }
      
      // Validate choice fields
      if (rules.allowedChoices && rules.allowedChoices[fieldName] && value) {
        const allowedChoices = rules.allowedChoices[fieldName];
        if (!allowedChoices.includes(value)) {
          isValid = false;
          errorMessage = `${fieldName} must be one of: ${allowedChoices.join(', ')}`;
        }
      }
      
      // Validate numeric fields
      if (rules.numericRanges && rules.numericRanges[fieldName] && value !== '') {
        const numValue = parseFloat(value);
        const range = rules.numericRanges[fieldName];
        
        if (isNaN(numValue)) {
          isValid = false;
          errorMessage = 'Must be a valid number';
        } else if (numValue < range.min || numValue > range.max) {
          isValid = false;
          errorMessage = `Must be between ${range.min} and ${range.max}`;
        }
      }
      
      // Special validation for mitigation steps (only if IsRisk is checked)
      if (fieldName === 'mitigation' && this.compliance.IsRisk) {
        if (!this.mitigationSteps || this.mitigationSteps.length === 0) {
          isValid = false;
          errorMessage = 'At least one mitigation step is required';
        } else {
          // Check if all steps have descriptions and meet minimum length
          const invalidSteps = this.mitigationSteps.filter(step => {
            const description = step.description ? step.description.trim() : '';
            return !description || description.length < 10;
          });
          
          if (invalidSteps.length > 0) {
            isValid = false;
            errorMessage = 'Each mitigation step must have at least 10 characters';
          }
        }
      }
      
      this.fieldStates[fieldName].valid = isValid;
      this.fieldStates[fieldName].warning = showWarning;
      
      if (isValid) {
        this.validationErrors[fieldName] = '';
      } else {
        this.validationErrors[fieldName] = errorMessage;
      }
      
      return isValid;
    },
    
    isFieldValid(fieldName) {
      return this.fieldStates[fieldName]?.valid || false;
    },
    
    validateField(fieldName) {
      // Skip validation for risk fields if IsRisk is not checked
      const riskFields = ['PossibleDamage', 'mitigation', 'PotentialRiskScenarios', 'RiskType', 
                         'RiskCategory', 'RiskBusinessImpact'];
      
      if (riskFields.includes(fieldName) && (!this.compliance || this.compliance.IsRisk !== true)) {
        // Don't validate, just return true
        return true;
      }
      
      const isValid = this.validateFieldRealTime(fieldName);
      if (!isValid) {
        this.$nextTick(() => {
          this.scrollToError();
        });
      }
      return isValid;
    },
    validateAndSubmit() {
      console.log('🚀 Starting validation and submit');
      console.log('📋 IsRisk checkbox state:', this.compliance.IsRisk);
      console.log('Current target values:', {
        framework: this.targetFrameworkId,
        policy: this.targetPolicyId,
        subPolicy: this.targetSubPolicyId,
        isRisk: this.compliance.IsRisk
      });
      
      this.validationErrors = {};
      let isValid = true;

      // Validate target fields first - these don't use the standard validation rules
      if (!this.targetFrameworkId) {
        this.validationErrors.targetFrameworkId = 'Framework is required';
        isValid = false;
      }
      
      if (!this.targetPolicyId) {
        this.validationErrors.targetPolicyId = 'Policy is required';
        isValid = false;
      }
      
      if (!this.targetSubPolicyId) {
        this.validationErrors.targetSubPolicyId = 'Sub Policy is required';
        isValid = false;
      }

      // Validate other fields using the standard validation rules
      let fieldsToValidate = [
        'ComplianceTitle', 'ComplianceItemDescription', 'ComplianceType', 'Scope', 'Objective',
        'BusinessUnitsCovered', 'Criticality', 'MandatoryOptional', 'ManualAutomatic',
        'Impact', 'Probability', 'MaturityLevel', 'reviewer_id'
      ];
      
      // Only validate risk fields if IsRisk is checked
      if (this.compliance && this.compliance.IsRisk === true) {
        console.log('✅ IsRisk is checked - validating risk fields');
        fieldsToValidate.push('PossibleDamage', 'PotentialRiskScenarios', 'RiskType', 
                               'RiskCategory', 'RiskBusinessImpact', 'mitigation');
      } else {
        console.log('⏭️ IsRisk is NOT checked - skipping risk field validation');
        // Clear any existing risk field errors
        ['PossibleDamage', 'PotentialRiskScenarios', 'RiskType', 
         'RiskCategory', 'RiskBusinessImpact', 'mitigation'].forEach(field => {
          this.validationErrors[field] = '';
          if (this.fieldStates[field]) {
            this.fieldStates[field].valid = true;
          }
        });
      }
      
      fieldsToValidate.forEach(field => {
        if (!this.validateField(field)) {
          isValid = false;
        }
      });

      console.log('📋 Validation result:', {
        isValid,
        validationErrors: this.validationErrors
      });

      if (!isValid) {
        console.log('❌ Validation failed, scrolling to error');
        this.$nextTick(() => {
          this.scrollToError();
        });
        return;
      }

      console.log('✅ Validation passed, submitting...');
      // If valid, proceed with submission
      this.submitCopy();
    },
    getCurrentUserId() {
      let userId = localStorage.getItem('user_id');
      if (userId) return userId;
      userId = sessionStorage.getItem('userId');
      if (userId) return userId;
      const userObj = localStorage.getItem('user') || sessionStorage.getItem('user');
      if (userObj) {
        try {
          const parsed = JSON.parse(userObj);
          return parsed.UserId || parsed.user_id || parsed.id;
        } catch (e) { /* intentionally empty: ignore JSON parse errors */ }
      }
      return null;
    }
  }
}
</script>

<style scoped>
/* Page Layout */
.copy-compliance-page {
  min-height: 100vh;
  background-color: #f8fafc;
  display: flex;
  flex-direction: column;
  margin-left: 280px;
}

/* Header Styles */
.page-header {
  background-color: white;
  color: #1f2937;
  padding: 1.5rem 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid #e5e7eb;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.refresh-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background-color: #3b82f6;
  color: white;
  border: 1px solid #2563eb;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  white-space: nowrap;
}

.refresh-button:hover:not(:disabled) {
  background-color: #2563eb;
  color: white;
  border-color: #1d4ed8;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.refresh-button:disabled {
  background-color: #9ca3af;
  border-color: #6b7280;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.refresh-button i {
  font-size: 0.875rem;
}

.header-text h1 {
  margin: 0 0 0.5rem 0;
  font-size: 1.8rem;
  font-weight: 700;
  color: #111827;
}

.header-text p {
  margin: 0;
  font-size: 1rem;
  color: #6b7280;
}

.back-button {
  background-color: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 2px;
}

.back-button:hover {
  background-color: #e5e7eb;
  color: #111827;
  transform: translateY(-1px);
}

/* Main Content */
.page-content {
  flex: 1;
  padding: 2rem 0;
  overflow-y: auto;
  max-height: calc(100vh - 120px);
}

.content-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 2rem;
}

/* Loading Overlay */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: white;
  font-size: 1.1rem;
  margin-top: 1rem;
}

/* Messages */
.message {
  padding: 1rem 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  font-weight: 500;
}

.success-message {
  background-color: #dcfce7;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.error-message {
  background-color: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.error-message i {
  margin-right: 0.5rem;
}

/* Field Groups */
.field-group {
  margin-bottom: 2rem;
  background-color: white;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #e5e7eb;
}

.field-group-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.selection-fields {
  background-color: white;
  border: 1px solid #e5e7eb;
}

.risk-fields {
  background-color: white;
  border: 1px solid #e5e7eb;
}

.classification-fields {
  background-color: white;
  border: 1px solid #e5e7eb;
}

.approval-fields {
  background-color: white;
  border: 1px solid #e5e7eb;
}

/* Reviewer Warning Box */
.reviewer-warning-box {
  background-color: #dbeafe;
  border: 2px solid #60a5fa;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.reviewer-warning-box i {
  color: #2563eb;
  font-size: 1.25rem;
  margin-top: 0.125rem;
  flex-shrink: 0;
}

.reviewer-warning-box span {
  color: #1e3a8a;
  font-size: 0.95rem;
  line-height: 1.5;
}

.reviewer-warning-box strong {
  color: #1e40af;
  font-weight: 600;
}

/* Form Fields */
.row-fields {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1rem;
}

.compliance-field {
  display: flex;
  flex-direction: column;
  position: relative;
}

.compliance-field label {
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.compliance-input,
.compliance-select {
  padding: 0.875rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.2s ease;
  background-color: white;
}

.compliance-input:focus,
.compliance-select:focus {
  outline: none;
  border-color: #374151;
  box-shadow: 0 0 0 3px rgba(55, 65, 81, 0.1);
}

.compliance-input:disabled,
.compliance-select:disabled {
  background-color: #f3f4f6;
  color: #9ca3af;
  cursor: not-allowed;
  border-color: #d1d5db;
  opacity: 0.7;
}

.compliance-select:not(:disabled) {
  background-color: white;
  cursor: pointer;
}

.full-width {
  grid-column: 1 / -1;
}

/* Character Count */
.char-count {
  position: absolute;
  right: 8px;
  bottom: 8px;
  font-size: 0.75rem;
  color: #6b7280;
  background-color: rgba(255, 255, 255, 0.9);
  padding: 2px 6px;
  border-radius: 4px;
}

.char-count.error {
  color: #dc2626;
}

/* Checkbox Container */
.checkbox-container {
  display: flex;
  align-items: center;
  padding-top: 1.75rem;
}

/* Selection Info */
.selection-info {
  background-color: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
  color: #374151;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.selection-info i {
  color: #6b7280;
  font-size: 1.25rem;
}

/* Searchable Dropdowns */
.searchable-dropdown {
  position: relative;
  width: 100%;
}

.dropdown-options {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-height: 200px;
  overflow-y: auto;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  margin-top: 4px;
}

.dropdown-option {
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid #f3f4f6;
}

.dropdown-option:hover {
  background-color: #f8fafc;
}

.dropdown-option:last-child {
  border-bottom: none;
}

.dropdown-add-option {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e5e7eb;
  background-color: #f9fafb;
}

.dropdown-add-btn {
  display: block;
  width: 100%;
  padding: 0.5rem;
  margin-top: 0.5rem;
  border: 1px dashed #9ca3af;
  background: white;
  color: #374151;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.dropdown-add-btn:hover {
  background: #f3f4f6;
  border-color: #374151;
  color: #374151;
}

/* Submit Container */
.compliance-submit-container {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  width: 100%;
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 1px solid #e5e7eb;
}

.compliance-submit-btn {
  background-color: #374151;
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.compliance-submit-btn:hover:not(:disabled) {
  background-color: #1f2937;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(55, 65, 81, 0.3);
}

.compliance-submit-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.compliance-cancel-btn {
  background-color: #f1f5f9;
  color: #64748b;
  border: 1px solid #cbd5e1;
  padding: 1rem 2rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.compliance-cancel-btn:hover {
  background-color: #e2e8f0;
  color: #475569;
  transform: translateY(-1px);
}

/* Error Styles */
.compliance-input.error,
.compliance-select.error {
  border-color: #dc2626;
  background-color: #fef2f2;
}

.compliance-input.error:focus,
.compliance-select.error:focus {
  border-color: #dc2626;
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1);
}

.field-error-message {
  color: #dc2626;
  font-size: 0.875rem;
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  background-color: #fef2f2;
  border-radius: 6px;
  font-weight: 500;
}

.required {
  color: #dc2626;
  margin-left: 0.25rem;
}

.field-requirements {
  color: #6b7280;
  font-size: 0.8rem;
  margin-left: 0.5rem;
  font-weight: 400;
}

.field-status {
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  margin-left: 0.5rem;
}

.field-status.auto-selected {
  background-color: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.field-status.selectable {
  background-color: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

/* Responsive Design */
@media (max-width: 768px) {
  .copy-compliance-page {
    margin-left: 0;
  }
  
  .page-header {
    padding: 1.5rem 0;
  }
  
  .header-content {
    padding: 0 1rem;
  }
  
  .header-main {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .header-text h1 {
    font-size: 1.5rem;
  }
  
  .content-container {
    margin: 0 1rem;
    padding: 1.5rem;
  }
  
  .row-fields {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .compliance-submit-container {
    flex-direction: column;
    gap: 1rem;
  }
  
  .compliance-submit-btn,
  .compliance-cancel-btn {
    width: 100%;
  }
}

/* Smooth Scrolling */
.page-content {
  scroll-behavior: smooth;
}

/* Custom Scrollbar */
.page-content::-webkit-scrollbar {
  width: 8px;
}

.page-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.page-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.page-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.validation-error {
  color: #dc2626;
  font-size: 0.875rem;
  margin-top: 0.25rem;
  font-weight: 500;
}

@keyframes highlightError {
  0% {
    background-color: rgba(220, 38, 38, 0.1);
  }
  100% {
    background-color: transparent;
  }
}

.compliance-field:target {
  animation: highlightError 2s ease-out;
}

/* Mitigation Steps Styles */
.mitigation-steps {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.mitigation-step {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  background-color: #f9fafb;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.step-numberr {
  font-weight: 600;
  color: #374151;
  font-size: 0.95rem;
}

.remove-step-btn {
  background: none;
  border: none;
  color: #dc2626;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.remove-step-btn:hover {
  background-color: #fee2e2;
}

.add-step-btn {
  background-color: #f3f4f6;
  color: #374151;
  border: 1px dashed #d1d5db;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.add-step-btn:hover {
  background-color: #e5e7eb;
  border-color: #9ca3af;
}

.add-step-btn i {
  font-size: 0.875rem;
}
</style>