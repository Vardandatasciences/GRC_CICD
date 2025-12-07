<template>
  <div class="create-compliance-container">
    <div class="compliance-headers">
      <span>Create Compliance</span>
      <!-- <div class="compliance-headers-underline"></div> -->
    </div>
    <!-- Popup Modal -->
    <PopupModal />
    <!-- Selection controls -->
    <div class="field-group selection-fields">
      <div class="field-group-title">Select Policy Framework</div>
      <div class="row-fields">
        <div class="compliance-field">
          <label for="framework">Framework</label>
          <CustomDropdown
            :config="frameworkConfig"
            v-model="selectedFramework"
            @change="onFrameworkChange"
          />
        </div>
        <div class="compliance-field">
          <label for="policy">Policy</label>
          <CustomDropdown
            :config="policyConfig"
            v-model="selectedPolicy"
            @change="onPolicyChange"
          />
        </div>
        <div class="compliance-field">
          <label for="subpolicy">Sub Policy</label>
          <CustomDropdown
            :config="subPolicyConfig"
            v-model="selectedSubPolicy"
            @change="onSubPolicyChange"
          />
        </div>
      </div>
    </div>
    <!-- Compliance items list with tabs -->
    <div class="compliance-list">
      <!-- Tabs navigation -->
      <div class="compliance-tabs">
        <div 
          v-for="(compliance, idx) in complianceList" 
          :key="idx" 
          class="compliance-tab" 
          :class="{ 'active-tab': activeTab === idx }"
          @click="activeTab = idx"
        >
          <span>Item #{{ idx + 1 }}</span>
          <button 
            v-if="complianceList.length > 1" 
            class="tab-remove-btn" 
            @click.stop="removeCompliance(idx)" 
            title="Remove this compliance item"
          >
            <span class="btn-icon">×</span>
          </button>
        </div>
        <button 
          class="add-tab-btn" 
          @click="addCompliance" 
          title="Add new compliance item"
        >
          <span class="btn-icon">+</span>
        </button>
      </div>
      <!-- Tab content - only show active tab -->
      <div 
        v-for="(compliance, idx) in complianceList" 
        :key="idx" 
        class="compliance-item-form"
        v-show="activeTab === idx"
      >
        <!-- Header for each compliance item -->
        <div class="item-header">
          <span class="item-number">Compliance Item #{{ idx + 1 }}</span>
        </div>

        <!-- Basic compliance information -->
        <div class="field-group">
          <div class="field-group-title">Basic Information</div>
          
          <!-- Identifier and IsRisk in one row -->
          <div class="row-fields">
            <div class="compliance-field">
              <label>Identifier</label>
              <input 
                v-model="compliance.Identifier" 
                class="compliance-input" 
                placeholder="Auto-generated if left empty"
                title="Unique identifier for this compliance item (auto-generated if left blank)"
              />
              <small>Leave empty for auto-generated identifier</small>
            </div>

            <div class="compliance-field checkbox-container">
              <label style="font-weight: 500; font-size: 0.9rem; display: flex; align-items: center; gap: 6px;" title="Check if this compliance item represents a risk">
                <input type="checkbox" v-model="compliance.IsRisk" @change="onFieldChange(idx, 'IsRisk', $event)" style="margin-right: 6px; width: auto;" />
                Is Risk
              </label>
            </div>
          </div>
          
          <!-- Compliance Title and Type in one row -->
          <div class="row-fields">
            <div class="compliance-field">
              <label>Compliance Title</label>
              <input 
                v-model="compliance.ComplianceTitle" 
                @input="onFieldChange(idx, 'ComplianceTitle', $event)"
                @blur="checkDuplicateTitles(idx)"
                @keyup="onComplianceTitleKeyup(idx, $event)"
                class="compliance-input" 
                :class="{ 'error-input': compliance.validationErrors && compliance.validationErrors.ComplianceTitle }"
                placeholder="Enter compliance title"
                required 
                :maxlength="validationRules.maxLengths.ComplianceTitle"
                title="Enter the title of the compliance item"
              />
              <small>Enter a clear, descriptive title for this compliance requirement (3-145 characters)</small>
              
                    <!-- Computed property error display -->
              <div v-if="complianceValidationErrors[idx] && complianceValidationErrors[idx].hasComplianceTitleErrors" 
                   style="color: #dc3545; font-weight: 500; margin-top: 4px; background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 8px; border-radius: 4px; display: block !important;">
                <strong>⚠️ Error:</strong> {{ complianceValidationErrors[idx].complianceTitleErrorMessage }}
              </div>             
            </div>
            
            <div class="compliance-field">
              <label>Compliance Type</label>
              <input 
                v-model="compliance.ComplianceType" 
                @input="onFieldChange(idx, 'ComplianceType', $event)"
                class="compliance-input" 
                placeholder="Enter compliance type"
                required
                :maxlength="validationRules.maxLengths.ComplianceType"
                title="Type of compliance (e.g. Regulatory, Internal, Security)"
              />
              <small>Specify the type of compliance (e.g., Regulatory, Internal, Security, Operational)</small>
              <div v-if="compliance.validationErrors && compliance.validationErrors.ComplianceType" 
                   class="validation-error">
                {{ compliance.validationErrors.ComplianceType.join(', ') }}
              </div>
            </div>
          </div>
          
          <div class="compliance-field full-width">
            <label>Compliance Description</label>
            <textarea
              v-model="compliance.ComplianceItemDescription" 
              @input="onFieldChange(idx, 'ComplianceItemDescription', $event)"
              class="compliance-input" 
              :placeholder="`Compliance Description ${idx+1}`"
              required 
              rows="3"
              :maxlength="validationRules.maxLengths.ComplianceItemDescription"
              title="Detailed description of the compliance requirement"
            ></textarea>
            <small>Provide a detailed description of the compliance requirement and what it entails</small>
            <div v-if="compliance.validationErrors && compliance.validationErrors.ComplianceItemDescription" 
                 class="validation-error">
              {{ compliance.validationErrors.ComplianceItemDescription.join(', ') }}
            </div>
          </div>
          
          <div class="compliance-field full-width">
            <label>Scope</label>
            <textarea 
              v-model="compliance.Scope" 
              @input="onFieldChange(idx, 'Scope', $event)"
              class="compliance-input" 
              placeholder="Enter scope information"
              rows="3"
              required
              :maxlength="validationRules.maxLengths.Scope"
              title="Define the boundaries and extent of the compliance requirement"
            ></textarea>
            <small>Define the boundaries, systems, processes, and areas covered by this compliance requirement</small>
            <div v-if="compliance.validationErrors && compliance.validationErrors.Scope" 
                 class="validation-error">
              {{ compliance.validationErrors.Scope.join(', ') }}
            </div>
          </div>
          
          <div class="compliance-field full-width">
            <label>Objective</label>
            <textarea 
              v-model="compliance.Objective" 
              @input="onFieldChange(idx, 'Objective', $event)"
              class="compliance-input" 
              placeholder="Enter objective information"
              rows="3"
              required
              :maxlength="validationRules.maxLengths.Objective"
              title="The goal or purpose of this compliance requirement"
            ></textarea>
            <small>Describe the goal, purpose, and intended outcome of this compliance requirement</small>
            <div v-if="compliance.validationErrors && compliance.validationErrors.Objective" 
                 class="validation-error">
              {{ compliance.validationErrors.Objective.join(', ') }}
            </div>
          </div>
          
          <!-- Business Units Covered -->
          <div class="row-fields">
            <div class="compliance-field full-width">
              <label>Business Units Covered</label>
              <div class="searchable-dropdown">
                <input 
                  v-model="businessUnitSearch[idx]" 
                  class="compliance-input" 
                  placeholder="Search or add business units"
                  title="Departments or business units affected by this compliance"
                  @focus="showDropdown(idx, 'BusinessUnitsCovered')"
                  @input="filterOptions(idx, 'BusinessUnitsCovered')"
                />
                <div v-show="activeDropdown.index === idx && activeDropdown.field === 'BusinessUnitsCovered'" class="dropdown-options">
                  <div v-if="filteredOptions.BusinessUnitsCovered.length === 0 && businessUnitSearch[idx]" class="dropdown-add-option">
                    <span>No matches found. Add new:</span>
                    <button @click="addNewOption(idx, 'BusinessUnitsCovered', businessUnitSearch[idx])" class="dropdown-add-btn">
                      + Add "{{ businessUnitSearch[idx] }}"
                    </button>
                  </div>
                  <div v-else-if="filteredOptions.BusinessUnitsCovered.length === 0 && !businessUnitSearch[idx]" class="dropdown-add-option">
                    <span>No options available. Type to add new:</span>
                  </div>
                  <div 
                    v-for="option in filteredOptions.BusinessUnitsCovered" 
                    :key="option.id" 
                    class="dropdown-option"
                    @click="selectOption(idx, 'BusinessUnitsCovered', option.value)"
                  >
                    {{ option.value }}
                  </div>
                </div>
              </div>
              <small>Select or add the departments, teams, or business units affected by this compliance requirement</small>
              <div v-if="compliance.validationErrors && compliance.validationErrors.BusinessUnitsCovered" 
                   class="validation-error">
                {{ compliance.validationErrors.BusinessUnitsCovered.join(', ') }}
              </div>
            </div>
          </div>
        </div>

        <!-- Risk related fields - grouped together -->
        <div class="field-group risk-fields">
          <div class="field-group-title">Risk Information</div>
          <div class="compliance-field full-width">
            <label>Possible Impact</label>
            <textarea
              v-model="compliance.PossibleDamage" 
              @input="onFieldChange(idx, 'PossibleDamage', $event)"
              class="compliance-input" 
              placeholder="Possible Damage"
              rows="3"
              required
              :maxlength="validationRules.maxLengths.PossibleDamage"
              title="Potential damage that could occur if this risk materializes" 
            ></textarea>
            <small>Describe the potential damage, losses, or negative impacts that could occur if this risk materializes</small>
            <div v-if="compliance.validationErrors && compliance.validationErrors.PossibleDamage" 
                 class="validation-error">
              {{ compliance.validationErrors.PossibleDamage.join(', ') }}
            </div>
          </div>
          
          <div class="compliance-field full-width">
            <label>Mitigation Steps</label>
            <div class="mitigation-steps">
              <div v-for="(step, stepIndex) in compliance.mitigationSteps" :key="stepIndex" class="mitigation-step">
                <div class="step-header">
                  <span class="step-numberr">Step {{ stepIndex + 1 }}</span>
                  <button type="button" class="remove-step-btn" @click="removeStep(idx, stepIndex)" title="Remove this step">
                    <span class="btn-icon">×</span>
                  </button>
                </div>
                <textarea
                  v-model="step.description"
                  @input="onMitigationStepChange(idx)"
                  class="compliance-input"
                  placeholder="Describe this mitigation step (minimum 10 characters)"
                  rows="2"
                  required
                ></textarea>
              </div>
              <div class="add-step-container">
                <button type="button" class="add-step-btn" @click="addStep(idx)" title="Add new mitigation step">
                  <span class="btn-icon">+</span> Add Step
                </button>
              </div>
            </div>
            <small>Define specific steps or actions to reduce, control, or eliminate the identified risk (minimum 10 characters per step)</small>
            <div v-if="compliance.validationErrors && compliance.validationErrors.mitigation" 
                 class="validation-error">
              {{ compliance.validationErrors.mitigation.join(', ') }}
            </div>
          </div>
          
          <div class="compliance-field full-width">
            <label>Potential Risk Scenarios</label>
            <textarea 
              v-model="compliance.PotentialRiskScenarios" 
              @input="onFieldChange(idx, 'PotentialRiskScenarios', $event)"
              class="compliance-input" 
              placeholder="Describe potential risk scenarios"
              rows="3"
              required
              :maxlength="validationRules.maxLengths.PotentialRiskScenarios"
              title="Describe scenarios where this risk could materialize"
            ></textarea>
            <small>Describe specific scenarios or conditions under which this risk could materialize</small>
            <div v-if="compliance.validationErrors && compliance.validationErrors.PotentialRiskScenarios" 
                 class="validation-error">
              {{ compliance.validationErrors.PotentialRiskScenarios.join(', ') }}
            </div>
          </div>
          
          <div class="row-fields">
            <div class="compliance-field">
              <label>Risk Type</label>
              <select 
                v-model="compliance.RiskType"
                class="compliance-input"
                required
                :maxlength="validationRules.maxLengths.RiskType"
                title="Type of risk"
                @change="validateComplianceField(compliance, 'RiskType', $event.target.value)"
              >
                <option value="">Select Risk Type</option>
                <option value="Current">Current</option>
                <option value="Residual">Residual</option>
                <option value="Inherent">Inherent</option>
                <option value="Emerging">Emerging</option>
                <option value="Accepted">Accepted</option>
              </select>
              <small>Select the type of risk: Current (existing), Residual (remaining after controls), Inherent (before controls), Emerging (new), or Accepted (tolerated)</small>
              <div v-if="compliance.validationErrors && compliance.validationErrors.RiskType" 
                   class="validation-error">
                {{ compliance.validationErrors.RiskType.join(', ') }}
              </div>
            </div>
            
            <div class="compliance-field">
              <label>Risk Category</label>
              <div class="searchable-dropdown">
                <input 
                  v-model="riskCategorySearch[idx]" 
                  class="compliance-input" 
                  placeholder="Search or add risk category"
                  required
                  :maxlength="validationRules.maxLengths.RiskCategory"
                  title="Category of risk (e.g. People, Process, Technology, External)"
                  @focus="showDropdown(idx, 'RiskCategory')"
                  @input="filterOptions(idx, 'RiskCategory')"
                />
                <div v-show="activeDropdown.index === idx && activeDropdown.field === 'RiskCategory'" class="dropdown-options">
                  <div v-if="filteredOptions.RiskCategory.length === 0 && riskCategorySearch[idx]" class="dropdown-add-option">
                    <span>No matches found. Add new:</span>
                    <button @click="addNewOption(idx, 'RiskCategory', riskCategorySearch[idx])" class="dropdown-add-btn">
                      + Add "{{ riskCategorySearch[idx] }}"
                    </button>
                  </div>
                  <div v-else-if="filteredOptions.RiskCategory.length === 0 && !riskCategorySearch[idx]" class="dropdown-add-option">
                    <span>No options available. Type to add new:</span>
                  </div>
                  <div 
                    v-for="option in filteredOptions.RiskCategory" 
                    :key="option.id" 
                    class="dropdown-option"
                    @click="selectOption(idx, 'RiskCategory', option.value)"
                  >
                    {{ option.value }}
                  </div>
                </div>
              </div>
              <small>Select or add the category of risk (e.g., People, Process, Technology, External, Financial)</small>
              <div v-if="compliance.validationErrors && compliance.validationErrors.RiskCategory" 
                   class="validation-error">
                {{ compliance.validationErrors.RiskCategory.join(', ') }}
              </div>
            </div>
            
            <div class="compliance-field">
              <label>Risk Business Impact</label>
              <div class="searchable-dropdown">
                <input 
                  v-model="riskBusinessImpactSearch[idx]" 
                  class="compliance-input" 
                  placeholder="Search or add business impact"
                  required
                  :maxlength="validationRules.maxLengths.RiskBusinessImpact"
                  title="How this risk impacts business operations"
                  @focus="showDropdown(idx, 'RiskBusinessImpact')"
                  @input="filterOptions(idx, 'RiskBusinessImpact')"
                />
                <div v-show="activeDropdown.index === idx && activeDropdown.field === 'RiskBusinessImpact'" class="dropdown-options">
                  <div v-if="filteredOptions.RiskBusinessImpact.length === 0 && riskBusinessImpactSearch[idx]" class="dropdown-add-option">
                    <span>No matches found. Add new:</span>
                    <button @click="addNewOption(idx, 'RiskBusinessImpact', riskBusinessImpactSearch[idx])" class="dropdown-add-btn">
                      + Add "{{ riskBusinessImpactSearch[idx] }}"
                    </button>
                  </div>
                  <div v-else-if="filteredOptions.RiskBusinessImpact.length === 0 && !riskBusinessImpactSearch[idx]" class="dropdown-add-option">
                    <span>No options available. Type to add new:</span>
                  </div>
                  <div 
                    v-for="option in filteredOptions.RiskBusinessImpact" 
                    :key="option.id" 
                    class="dropdown-option"
                    @click="selectOption(idx, 'RiskBusinessImpact', option.value)"
                  >
                    {{ option.value }}
                  </div>
                </div>
              </div>
              <small>Select or add how this risk impacts business operations (e.g., Operational Disruption, Financial Loss, Reputation Damage)</small>
              <div v-if="compliance.validationErrors && compliance.validationErrors.RiskBusinessImpact" 
                   class="validation-error">
                {{ compliance.validationErrors.RiskBusinessImpact.join(', ') }}
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
              <small>Select the criticality level based on the importance and impact of this compliance requirement</small>
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
              <small>Indicate whether this compliance requirement is mandatory (required) or optional (recommended)</small>
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
              <small>Specify whether this compliance is monitored manually (human review) or automatically (system/tool)</small>
            </div>
            
            <div class="compliance-field">
              <label>Applicability</label>
              <input 
                v-model="compliance.Applicability" 
                class="compliance-input" 
                placeholder="Applicability from policy"
                title="Describes where this compliance item applies"
              />
              <small>Describe where, when, and under what conditions this compliance requirement applies</small>
            </div>
          </div>
          
          <div class="row-fields">
            <div class="compliance-field">
              <label>Severity Rating (1-10)</label>
              <input 
                type="number" 
                v-model.number="compliance.Impact" 
                @input="onFieldChange(idx, 'Impact', $event)"
                class="compliance-input" 
                step="0.1" 
                min="1" 
                max="10"
                required
                title="Rate the Severity Rating from 1 (lowest) to 10 (highest)"
              />
              <small>Rate the severity of non-compliance from 1 (minimal impact) to 10 (critical impact)</small>
              <div v-if="compliance.validationErrors && compliance.validationErrors.Impact" 
                   class="validation-error">
                {{ compliance.validationErrors.Impact.join(', ') }}
              </div>
            </div>
            
            <div class="compliance-field">
              <label>Probability (1-10)</label>
              <input 
                type="number" 
                v-model.number="compliance.Probability" 
                @input="onFieldChange(idx, 'Probability', $event)"
                class="compliance-input" 
                step="0.1" 
                min="1" 
                max="10"
                required
                title="Rate the probability from 1 (lowest) to 10 (highest)"
              />
              <small>Rate the likelihood of non-compliance from 1 (very unlikely) to 10 (very likely)</small>
              <div v-if="compliance.validationErrors && compliance.validationErrors.Probability" 
                   class="validation-error">
                {{ compliance.validationErrors.Probability.join(', ') }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- Approval section -->
        <div class="field-group approval-fields">
          <div class="field-group-title">Approval Information</div>
          <!-- Approver row -->
          <div class="row-fields">
            <!-- Assign Reviewer -->
            <div class="compliance-field">
              <label>Assign Reviewer</label>
              <CustomDropdown
                :config="reviewerConfig"
                v-model="compliance.reviewer_id"
                @change="onReviewerChange"
              />
              <small>Select the person responsible for reviewing and approving this compliance item</small>
              <span v-if="!users.length" class="validation-error">No reviewers available</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Submit button container with better alignment -->
    <div class="compliance-submit-container">
      <button 
        class="compliance-submit-btn" 
        @click="submitCompliance"
        :disabled="loading"
      >
        <span v-if="loading" class="btn-icon">⏳</span>
        <span v-if="loading">Saving...</span>
        <span v-else>Submit Compliance</span>
      </button>
    </div>
  </div>
</template>
<script>
import { complianceService } from '@/services/api';
  import complianceDataService from '@/services/complianceService'; // NEW: Use cached compliance data
  import { PopupService, PopupModal } from '@/modules/popup';
  import { CompliancePopups } from './utils/popupUtils';
  import CustomDropdown from '@/components/CustomDropdown.vue';
  import AccessUtils from '@/utils/accessUtils';
  import axios from 'axios';
  import { API_ENDPOINTS } from '../../config/api.js';

export default {
  name: 'CreateCompliance',
  components: {
    PopupModal,
    CustomDropdown // Registered CustomDropdown component
  },
  data() {
    return {
      selectedFramework: '',
      selectedPolicy: '',
      selectedSubPolicy: '',
      frameworks: [],
      policies: [],
      subPolicies: [],
      users: [],
      
      // Framework session filtering properties
      sessionFrameworkId: null,
      // Dropdown options
      categoryOptions: {
        BusinessUnitsCovered: [],
        RiskType: [],
        RiskCategory: [],
        RiskBusinessImpact: []
      },
      // Filtered options for dropdowns
      filteredOptions: {
        BusinessUnitsCovered: [],
        RiskType: [],
        RiskCategory: [],
        RiskBusinessImpact: []
      },
      // Search terms for each dropdown
      businessUnitSearch: [],
      riskTypeSearch: [],
      riskCategorySearch: [],
      riskBusinessImpactSearch: [],
      // Active dropdown tracking
      activeDropdown: {
        index: null,
        field: null
      },
      complianceList: [
        {
          ComplianceTitle: '',
          ComplianceItemDescription: '',
          ComplianceType: '',
          Scope: '',
          Objective: '',
          BusinessUnitsCovered: '',
          Identifier: '',
          IsRisk: false,
          PossibleDamage: '',
          mitigation: '',
          PotentialRiskScenarios: '',
          RiskType: '',
          RiskCategory: '',
          RiskBusinessImpact: '',
          Criticality: 'Medium',
          MandatoryOptional: 'Mandatory',
          ManualAutomatic: 'Manual',
          Impact: 5.0,
          Probability: 5.0,
          Status: 'Under Review',
          reviewer_id: '', // No default reviewer
          CreatedByName: '', // No default creator
          Applicability: '',
          MaturityLevel: 'Initial',
          ActiveInactive: 'Active',
          PermanentTemporary: 'Permanent',
          mitigationSteps: [{ stepNumber: 1, description: '' }],
          validationErrors: {}
        }
      ],
      loading: false,
      activeTab: 0,
      existingComplianceTitles: [], // Store existing compliance titles for duplicate checking
      duplicateCheckTimeout: null, // Timeout for duplicate title checking
      // Centralized validation patterns (allow-list approach)
      validationRules: {
        // Character set patterns - includes special characters like <, >, $, /, *, |, etc.
        textPattern: /^[a-zA-Z0-9\s.,!?\-_()[\]{}:;'"&%$#@+=<>/\\|*^~`\n\r\t]*$/,
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
          Applicability: 450
        },
        
        // Field minimum length requirements
        minLengths: {
          ComplianceTitle: 3,
          ComplianceItemDescription: 10,
          ComplianceType: 3,
          Scope: 10,
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
             // Configuration for CustomDropdown components
       frameworkConfig: {
         name: 'Framework',
         label: 'Framework',
         values: [],
         defaultValue: 'Select Framework'
       },
       policyConfig: {
         name: 'Policy',
         label: 'Policy',
         values: [],
         defaultValue: 'Select Policy'
       },
       subPolicyConfig: {
         name: 'Sub Policy',
         label: 'Sub Policy',
         values: [],
         defaultValue: 'Select Sub Policy'
       },
       reviewerConfig: {
         name: 'Reviewer',
         label: 'Reviewer',
         values: [],
         defaultValue: 'Select Reviewer'
       }
    }
  },
  computed: {
    // Framework filtering computed properties
    filteredFrameworks() {
      if (this.sessionFrameworkId) {
        // If there's a session framework ID, show only that framework
        return this.frameworks.filter(fw => fw.id.toString() === this.sessionFrameworkId.toString())
      }
      // If no session framework ID, show all frameworks
      return this.frameworks
    },
    
    minDate() {
      // Get today's date in YYYY-MM-DD format for setting minimum date
      const today = new Date();
      return today.toISOString().split('T')[0];
    },
    
    // Computed property to get validation errors for each compliance item
    complianceValidationErrors() {
      return this.complianceList.map(compliance => ({
        hasComplianceTitleErrors: this.hasComplianceTitleErrors(compliance),
        complianceTitleErrorMessage: this.getComplianceTitleErrorMessage(compliance),
        validationErrors: compliance.validationErrors
      }));
    }
  },
  
  watch: {
    'complianceList': {
      handler(newVal) {
        // Force update when compliance list changes
        this.$forceUpdate();
        
        // Check if validation errors changed
        newVal.forEach((compliance, index) => {
          if (compliance.validationErrors && 
              compliance.validationErrors.ComplianceTitle && 
              compliance.validationErrors.ComplianceTitle.length > 0) {
            console.log('Validation errors detected for index:', index, compliance.validationErrors.ComplianceTitle);
            // Force update for this specific compliance item
            this.$nextTick(() => {
              this.$forceUpdate();
            });
          }
        });
      },
      deep: true
    },
    
    // Watch for changes in filteredFrameworks to update the dropdown config
    filteredFrameworks: {
      handler() {
        this.updateFrameworkConfig();
      },
      immediate: true
    }
  },
  async created() {
    try {
      await this.loadFrameworks();
      
      // Check for selected framework from session after loading frameworks
      await this.checkSelectedFrameworkFromSession();
      
      await this.loadUsers();
      await this.loadCategoryOptions();
      
      // Initialize search arrays with empty strings for the first compliance item
      this.businessUnitSearch = [''];
      this.riskTypeSearch = [''];
      this.riskCategorySearch = [''];
      this.riskBusinessImpactSearch = [''];
      
      // Add click event listener to close dropdowns when clicking outside
      document.addEventListener('click', this.handleClickOutside);
      
      // Initialize mitigation data for the initial compliance item
      this.onMitigationStepChange(0);
    } catch (error) {
      // If there's an overall access error during component initialization
      if (AccessUtils.handleApiError(error, 'create compliance')) {
        return;
      }
      console.error('Error initializing CreateCompliance component:', error);
    }
  },
  
  beforeUnmount() {
    // Remove event listener when component is unmounted
    document.removeEventListener('click', this.handleClickOutside);
    
    // Clear any pending timeout
    if (this.duplicateCheckTimeout) {
      clearTimeout(this.duplicateCheckTimeout);
    }
  },

  methods: {
    // Framework session management methods
    async checkSelectedFrameworkFromSession() {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in CreateCompliance...')
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
        console.log('📊 DEBUG: Selected framework response:', response.data)
        
        if (response.data && response.data.success && response.data.frameworkId) {
          const frameworkIdFromSession = response.data.frameworkId
          console.log('✅ DEBUG: Found selected framework in session:', frameworkIdFromSession)
          
          // Store the session framework ID for filtering
          this.sessionFrameworkId = frameworkIdFromSession
          
          // Check if this framework exists in our loaded frameworks
          const frameworkExists = this.frameworks.find(f => f.id.toString() === frameworkIdFromSession.toString())
          
          if (frameworkExists) {
            console.log('✅ DEBUG: Framework exists in loaded frameworks:', frameworkExists.name)
            // Automatically select the framework from session
            this.selectedFramework = frameworkExists
            console.log('✅ DEBUG: Auto-selected framework from session:', this.selectedFramework)
            
            // Load policies for the selected framework
            if (frameworkExists.id) {
              await this.loadPolicies(frameworkExists.id)
            }
          } else {
            console.log('⚠️ DEBUG: Framework from session (ID:', frameworkIdFromSession, ') not found in loaded frameworks')
            console.log('📋 DEBUG: Available frameworks:', this.frameworks.map(f => ({ id: f.id, name: f.name })))
            // Clear the session framework ID since it doesn't exist
            this.sessionFrameworkId = null
          }
        } else {
          console.log('ℹ️ DEBUG: No framework found in session')
          this.sessionFrameworkId = null
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework from session:', error)
        this.sessionFrameworkId = null
      }
    },
    
    async saveFrameworkToSession(frameworkId) {
      try {
        console.log('💾 DEBUG: Saving framework to session:', frameworkId)
        const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
          frameworkId: frameworkId
        })
        console.log('💾 DEBUG: Save framework response:', response.data)
        
        if (response.data && response.data.success) {
          this.sessionFrameworkId = frameworkId
          console.log('✅ DEBUG: Framework saved to session successfully')
        } else {
          console.error('❌ DEBUG: Failed to save framework to session:', response.data)
        }
      } catch (error) {
        console.error('❌ DEBUG: Error saving framework to session:', error)
      }
    },
    
    updateFrameworkConfig() {
      // Update framework config with filtered frameworks
      this.frameworkConfig.values = this.filteredFrameworks.map(fw => ({
        value: fw,
        label: fw.name
      }))
      console.log('📋 DEBUG: Updated framework config with', this.frameworkConfig.values.length, 'frameworks')
    },
    
    // Centralized validation methods using allow-list approach
    sanitizeString(value) {
      if (typeof value !== 'string') return String(value || '');
      // Remove control characters except newline, tab, carriage return
      // eslint-disable-next-line no-control-regex
      return value.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');
    },
    
    sanitizeStringForSubmission(value) {
      if (typeof value !== 'string') return String(value || '');
      // Remove control characters and trim for final submission
      // eslint-disable-next-line no-control-regex
      return value.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '').trim();
    },
    
    validateRequiredString(value, fieldName, maxLength = null, minLength = null, pattern = null) {
      const sanitized = this.sanitizeString(value);
      const trimmedValue = sanitized.trim();
      const errors = [];
      
      if (!trimmedValue || trimmedValue.length === 0) {
        errors.push(`${fieldName} is required and cannot be empty`);
      }
      
      if (minLength && trimmedValue.length > 0 && trimmedValue.length < minLength) {
        errors.push(`${fieldName} must be at least ${minLength} characters long`);
      }
      
      if (maxLength && sanitized.length > maxLength) {
        errors.push(`${fieldName} must not exceed ${maxLength} characters`);
      }
      
      if (pattern && sanitized && !pattern.test(sanitized)) {
        errors.push(`${fieldName} contains invalid characters`);
      }
      
      return { value: sanitized, errors };
    },
    
    validateOptionalString(value, fieldName, maxLength = null, pattern = null) {
      const sanitized = this.sanitizeString(value);
      const errors = [];
      
      if (maxLength && sanitized.length > maxLength) {
        errors.push(`${fieldName} must not exceed ${maxLength} characters`);
      }
      
      if (pattern && sanitized && !pattern.test(sanitized)) {
        errors.push(`${fieldName} contains invalid characters`);
      }
      
      return { value: sanitized, errors };
    },
    
    validateChoiceField(value, fieldName, allowedChoices) {
      const errors = [];
      
      if (!value || value === '') {
        errors.push(`${fieldName} is required`);
      } else if (!allowedChoices.includes(value)) {
        errors.push(`${fieldName} must be one of: ${allowedChoices.join(', ')}`);
      }
      
      return { value, errors };
    },
    
    validateNumericField(value, fieldName, min = null, max = null) {
      const errors = [];
      const numValue = parseFloat(value);
      
      if (isNaN(numValue)) {
        errors.push(`${fieldName} must be a valid number`);
      } else {
        if (min !== null && numValue < min) {
          errors.push(`${fieldName} must be at least ${min}`);
        }
        if (max !== null && numValue > max) {
          errors.push(`${fieldName} must not exceed ${max}`);
        }
      }
      
      return { value: numValue, errors };
    },
    
    validateDateField(value, fieldName) {
      const errors = [];
      
      if (!value || value === '') {
        errors.push(`${fieldName} is required`);
      } else {
        const datePattern = /^\d{4}-\d{2}-\d{2}$/;
        if (!datePattern.test(value)) {
          errors.push(`${fieldName} must be in YYYY-MM-DD format`);
        } else {
          const date = new Date(value);
          if (isNaN(date.getTime())) {
            errors.push(`${fieldName} must be a valid date`);
          } else {
            // Check if date is in the future (for approval due dates)
            const today = new Date();
            today.setHours(0, 0, 0, 0); // Reset time to compare only dates
            if (date < today) {
              errors.push(`${fieldName} must be a future date`);
            }
          }
        }
      }
      
      return { value, errors };
    },
    
    validateComplianceField(compliance, fieldName, value) {
      const rules = this.validationRules;
      let result = { value, errors: [] };
      
      switch (fieldName) {
        case 'ComplianceTitle':
          result = this.validateRequiredString(
            value, 'Compliance Title', 
            rules.maxLengths.ComplianceTitle,
            rules.minLengths.ComplianceTitle,
            rules.textPattern
          );
          break;
          
        case 'ComplianceItemDescription':
          result = this.validateRequiredString(
            value, 'Compliance Description', 
            rules.maxLengths.ComplianceItemDescription,
            rules.minLengths.ComplianceItemDescription,
            rules.textPattern
          );
          break;
          
        case 'ComplianceType':
          result = this.validateRequiredString(
            value, 'Compliance Type', 
            rules.maxLengths.ComplianceType,
            rules.minLengths.ComplianceType,
            rules.textPattern
          );
          break;
          
        case 'Scope':
          result = this.validateRequiredString(
            value, 'Scope', 
            rules.maxLengths.Scope,
            rules.minLengths.Scope,
            rules.textPattern
          );
          break;
          
        case 'Objective':
          result = this.validateRequiredString(
            value, 'Objective', 
            rules.maxLengths.Objective,
            rules.minLengths.Objective,
            rules.textPattern
          );
          break;
          
        case 'BusinessUnitsCovered':
          result = this.validateRequiredString(
            value, 'Business Units Covered', 
            rules.maxLengths.BusinessUnitsCovered,
            rules.minLengths.BusinessUnitsCovered,
            rules.textPattern
          );
          break;
          
        case 'Identifier':
          if (value && value.trim()) {
            result = this.validateOptionalString(
              value, 'Identifier', 
              rules.maxLengths.Identifier, 
              rules.identifierPattern
            );
          }
          break;
          
        case 'PossibleDamage':
          result = this.validateRequiredString(
            value, 'Possible Damage', 
            rules.maxLengths.PossibleDamage,
            rules.minLengths.PossibleDamage,
            rules.textPattern
          );
          break;
          
        case 'PotentialRiskScenarios':
          result = this.validateRequiredString(
            value, 'Potential Risk Scenarios', 
            rules.maxLengths.PotentialRiskScenarios,
            rules.minLengths.PotentialRiskScenarios,
            rules.textPattern
          );
          break;
          
        case 'RiskType':
          result = this.validateRequiredString(
            value, 'Risk Type', 
            rules.maxLengths.RiskType,
            rules.minLengths.RiskType,
            rules.textPattern
          );
          break;
          
        case 'RiskCategory':
          result = this.validateRequiredString(
            value, 'Risk Category', 
            rules.maxLengths.RiskCategory,
            rules.minLengths.RiskCategory,
            rules.textPattern
          );
          break;
          
        case 'RiskBusinessImpact':
          result = this.validateRequiredString(
            value, 'Risk Business Impact', 
            rules.maxLengths.RiskBusinessImpact,
            rules.minLengths.RiskBusinessImpact,
            rules.textPattern
          );
          break;
          
        case 'mitigation':
          // Always validate mitigation steps regardless of IsRisk status
          if (!compliance.mitigationSteps || compliance.mitigationSteps.length === 0) {
            result.errors.push('At least one mitigation step is required');
          } else {
            // Check if all steps have descriptions and meet minimum length
            const invalidSteps = compliance.mitigationSteps.filter(step => {
              const description = step.description ? step.description.trim() : '';
              return !description || description.length < 10;
            });
            
            if (invalidSteps.length > 0) {
              result.errors.push('Each mitigation step must have at least 10 characters');
            }
          }
          break;
          
        case 'Applicability':
          result = this.validateOptionalString(
            value, 'Applicability', 
            rules.maxLengths.Applicability, 
            rules.textPattern
          );
          break;
          
        case 'Criticality':
          result = this.validateChoiceField(
            value, 'Criticality', 
            rules.allowedChoices.Criticality
          );
          break;
          
        case 'MandatoryOptional':
          result = this.validateChoiceField(
            value, 'Mandatory/Optional', 
            rules.allowedChoices.MandatoryOptional
          );
          break;
          
        case 'ManualAutomatic':
          result = this.validateChoiceField(
            value, 'Manual/Automatic', 
            rules.allowedChoices.ManualAutomatic
          );
          break;
          
        case 'Impact':
          result = this.validateNumericField(
            value, 'Severity Rating', 
            rules.numericRanges.Impact.min, 
            rules.numericRanges.Impact.max
          );
          break;
          
        case 'Probability':
          result = this.validateNumericField(
            value, 'Probability', 
            rules.numericRanges.Probability.min, 
            rules.numericRanges.Probability.max
          );
          break;
          

      }
      
      // Update validation errors for the field
      if (!compliance.validationErrors) {
        compliance.validationErrors = {};
      }
      
      if (result.errors.length > 0) {
        compliance.validationErrors[fieldName] = result.errors;
      } else {
        delete compliance.validationErrors[fieldName];
      }
      
      return result;
    },
    
    // Real-time validation on input
    onFieldChange(complianceIndex, fieldName, event) {
      const compliance = this.complianceList[complianceIndex];
      let value;
      
      // Handle different input types
      if (fieldName === 'IsRisk') {
        value = event.target.checked;
        compliance[fieldName] = value;
      } else {
        value = event.target.value;
        // Update the field value directly without sanitization during typing
        compliance[fieldName] = value;
        
        // For ComplianceTitle, we handle validation differently to preserve duplicate checks
        if (fieldName === 'ComplianceTitle') {
          // Only do basic validation (required, length, pattern) but don't clear duplicate errors
          const basicValidation = this.validateRequiredString(
            value, 'Compliance Title', 
            this.validationRules.maxLengths.ComplianceTitle,
            this.validationRules.minLengths.ComplianceTitle,
            this.validationRules.textPattern
          );
          
          // Initialize validation errors if needed
          if (!compliance.validationErrors) {
            compliance.validationErrors = {};
          }
          
          // Update basic validation errors
          if (basicValidation.errors.length > 0) {
            compliance.validationErrors[fieldName] = basicValidation.errors;
          } else {
            // Only clear basic validation errors, preserve duplicate errors
            if (compliance.validationErrors[fieldName]) {
              const duplicateErrors = compliance.validationErrors[fieldName].filter(
                error => error.includes('already used by another compliance item') || 
                         error.includes('already exists in this subpolicy')
              );
              if (duplicateErrors.length > 0) {
                compliance.validationErrors[fieldName] = duplicateErrors;
              } else {
                delete compliance.validationErrors[fieldName];
              }
            }
          }
          
          // Ensure the validation state is properly maintained
          if (compliance.validationErrors[fieldName] && compliance.validationErrors[fieldName].length > 0) {
            console.log('Updated validation errors for', fieldName, ':', compliance.validationErrors[fieldName]);
          }
          
          // Force reactivity for validation errors
          compliance.validationErrors = { ...compliance.validationErrors };
          
          // Check for duplicate titles in real-time with a small delay to avoid too frequent checks
          // Clear any existing timeout for this field
          if (this.duplicateCheckTimeout) {
            clearTimeout(this.duplicateCheckTimeout);
          }
          // Set a timeout to check for duplicates after user stops typing
          this.duplicateCheckTimeout = setTimeout(() => {
            this.checkDuplicateTitles(complianceIndex);
          }, 300); // 300ms delay for faster response
          
          // Also check immediately if the title is long enough
          if (value && value.trim().length >= 3) {
            this.checkDuplicateTitles(complianceIndex);
          }
          
          // Force immediate update to ensure UI reflects changes
          this.$nextTick(() => {
            this.$forceUpdate();
          });
          
          // Force reactivity update for the specific compliance item
          this.complianceList[complianceIndex] = { ...this.complianceList[complianceIndex] };
        } else {
          // For other fields, use the standard validation
          this.validateComplianceField(compliance, fieldName, value);
        }
      }
      
      // Force reactivity update
      this.$forceUpdate();
    },
    
    // Check for duplicate compliance titles
    checkDuplicateTitles(currentIndex) {
      const currentTitle = this.complianceList[currentIndex].ComplianceTitle?.trim().toLowerCase();
      console.log('Checking duplicates for index:', currentIndex, 'title:', currentTitle);
      console.log('Existing titles loaded:', this.existingComplianceTitles);
      
      if (!currentTitle) {
        // Clear any existing duplicate errors if title is empty
        if (this.complianceList[currentIndex].validationErrors && 
            this.complianceList[currentIndex].validationErrors.ComplianceTitle) {
          const errors = this.complianceList[currentIndex].validationErrors.ComplianceTitle.filter(
            error => !error.includes('already used by another compliance item') && 
                     !error.includes('already exists in this subpolicy')
          );
          if (errors.length === 0) {
            delete this.complianceList[currentIndex].validationErrors.ComplianceTitle;
          } else {
            this.complianceList[currentIndex].validationErrors.ComplianceTitle = errors;
          }
        }
        return;
      }
      
      // Check for duplicates within the current submission
      const duplicateIndex = this.complianceList.findIndex((compliance, index) => {
        if (index === currentIndex) return false;
        return compliance.ComplianceTitle?.trim().toLowerCase() === currentTitle;
      });
      
      // Check for duplicates with existing compliance items in the database
      const existingDuplicate = this.existingComplianceTitles.includes(currentTitle);
      console.log('Duplicate index:', duplicateIndex, 'Existing duplicate:', existingDuplicate);
      
      // Initialize validation errors object if it doesn't exist
      if (!this.complianceList[currentIndex].validationErrors) {
        this.complianceList[currentIndex].validationErrors = {};
      }
      
      if (duplicateIndex !== -1) {
        // Add duplicate title error to current compliance
        const existingErrors = this.complianceList[currentIndex].validationErrors.ComplianceTitle || [];
        const basicErrors = existingErrors.filter(
          error => !error.includes('already used by another compliance item') && 
                   !error.includes('already exists in this subpolicy')
        );
        this.complianceList[currentIndex].validationErrors.ComplianceTitle = [
          ...basicErrors,
          'This title is already used by another compliance item in this submission. Please choose a unique title.'
        ];
        console.log('Setting duplicate error for index:', currentIndex);
      } else if (existingDuplicate) {
        // Add existing title error to current compliance
        const existingErrors = this.complianceList[currentIndex].validationErrors.ComplianceTitle || [];
        const basicErrors = existingErrors.filter(
          error => !error.includes('already used by another compliance item') && 
                   !error.includes('already exists in this subpolicy')
        );
        this.complianceList[currentIndex].validationErrors.ComplianceTitle = [
          ...basicErrors,
          'This title already exists in this subpolicy. Please choose a different title.'
        ];
        console.log('Setting existing duplicate error for index:', currentIndex);
      } else {
        // Remove duplicate title errors if they exist
        if (this.complianceList[currentIndex].validationErrors.ComplianceTitle) {
          const errors = this.complianceList[currentIndex].validationErrors.ComplianceTitle.filter(
            error => !error.includes('already used by another compliance item') && 
                     !error.includes('already exists in this subpolicy')
          );
          if (errors.length === 0) {
            delete this.complianceList[currentIndex].validationErrors.ComplianceTitle;
          } else {
            this.complianceList[currentIndex].validationErrors.ComplianceTitle = errors;
          }
        }
      }
      
      // Ensure the validation errors are properly set
      if (this.complianceList[currentIndex].validationErrors.ComplianceTitle && 
          this.complianceList[currentIndex].validationErrors.ComplianceTitle.length > 0) {
        console.log('Final validation errors for ComplianceTitle:', this.complianceList[currentIndex].validationErrors.ComplianceTitle);
      }
      
      // Force reactivity by using Vue.set or direct assignment
      this.complianceList[currentIndex].validationErrors = { ...this.complianceList[currentIndex].validationErrors };
      
      // Force immediate display of error
      this.$nextTick(() => {
        console.log('Forcing immediate display of validation errors');
        this.$forceUpdate();
      });
      
      console.log('Final validation errors for index:', currentIndex, this.complianceList[currentIndex].validationErrors);
      
      // Also trigger a next tick update to ensure the UI reflects the changes
      this.$nextTick(() => {
        this.$forceUpdate();
      });
      
      // Force reactivity update for the specific compliance item
      this.complianceList[currentIndex] = { ...this.complianceList[currentIndex] };
    },
    
    // Handle keyup events for compliance title to check duplicates immediately
    onComplianceTitleKeyup(complianceIndex, event) {
      const value = event.target.value;
      if (value && value.trim().length >= 3) {
        // Check for duplicates immediately on keyup
        this.checkDuplicateTitles(complianceIndex);
      }
    },
    
    // Force set error for testing
    forceSetError(index) {
      console.log('Force setting error for index:', index);
      if (!this.complianceList[index].validationErrors) {
        this.complianceList[index].validationErrors = {};
      }
      this.complianceList[index].validationErrors.ComplianceTitle = [
        'FORCE ERROR: This is a test error message'
      ];
      this.$nextTick(() => {
        this.$forceUpdate();
      });
    },
    
    // Direct set error for testing
    directSetError(index) {
      console.log('Direct setting error for index:', index);
      this.complianceList[index].validationErrors = {
        ComplianceTitle: ['DIRECT ERROR: This is a direct test error message']
      };
      console.log('Set validation errors:', this.complianceList[index].validationErrors);
      this.$forceUpdate();
    },
    
    // Debug validation state
    debugValidationState(index) {
      const compliance = this.complianceList[index];
      console.log('Debug validation state for index:', index);
      console.log('Compliance title:', compliance.ComplianceTitle);
      console.log('Validation errors:', compliance.validationErrors);
      console.log('ComplianceTitle errors:', compliance.validationErrors?.ComplianceTitle);
      console.log('Existing titles:', this.existingComplianceTitles);
      console.log('Current title in existing titles:', this.existingComplianceTitles.includes(compliance.ComplianceTitle?.trim().toLowerCase()));
    },
    
    // Check if ComplianceTitle errors should be displayed
    hasComplianceTitleErrors(compliance) {
      return compliance.validationErrors && 
             compliance.validationErrors.ComplianceTitle && 
             compliance.validationErrors.ComplianceTitle.length > 0;
    },
    
    // Get ComplianceTitle error message
    getComplianceTitleErrorMessage(compliance) {
      if (!this.hasComplianceTitleErrors(compliance)) return '';
      const errors = compliance.validationErrors.ComplianceTitle;
      return Array.isArray(errors) ? errors.join(', ') : errors;
    },
    
    // Comprehensive form validation before submission
    validateAllFields() {
      let isValid = true;
      const errors = [];
      
      // Validate framework selection
      if (!this.selectedFramework || !this.selectedFramework.id) {
        errors.push('Please select a framework');
        isValid = false;
      }
      
      // Validate policy selection
      if (!this.selectedPolicy || !this.selectedPolicy.id) {
        errors.push('Please select a policy');
        isValid = false;
      }
      
      // Validate sub-policy selection
      if (!this.selectedSubPolicy || !this.selectedSubPolicy.id) {
        errors.push('Please select a sub-policy');
        isValid = false;
      }
      
      // Check for duplicate compliance titles within the same submission
      const titles = this.complianceList.map(compliance => compliance.ComplianceTitle?.trim().toLowerCase()).filter(title => title);
      const duplicateTitles = titles.filter((title, index) => titles.indexOf(title) !== index);
      
      if (duplicateTitles.length > 0) {
        errors.push(`Duplicate compliance titles found: ${[...new Set(duplicateTitles)].join(', ')}. Each compliance item must have a unique title.`);
        isValid = false;
      }
      
      // Validate each compliance item
      this.complianceList.forEach((compliance, index) => {
        // Reset validation errors
        compliance.validationErrors = {};
        
        // Required fields validation - all fields are mandatory including risk fields
        const requiredFields = [
          'ComplianceTitle',
          'ComplianceItemDescription', 
          'ComplianceType',
          'Scope',
          'Objective',
          'BusinessUnitsCovered',
          'mitigation',
          'PossibleDamage',
          'PotentialRiskScenarios',
          'RiskType',
          'RiskCategory',
          'RiskBusinessImpact',
          'Criticality',
          'MandatoryOptional',
          'ManualAutomatic',
          'Impact',
          'Probability'
        ];
        
        // Validate reviewer selection
        if (!compliance.reviewer_id || compliance.reviewer_id === '') {
          compliance.validationErrors.reviewer_id = ['Please select a reviewer'];
          errors.push(`Please select a reviewer for item ${index + 1}`);
          isValid = false;
        }
        
        // Validate all required fields
        requiredFields.forEach(fieldName => {
          const result = this.validateComplianceField(compliance, fieldName, compliance[fieldName]);
          if (result.errors.length > 0) {
            errors.push(`Item ${index + 1}: ${result.errors.join(', ')}`);
            isValid = false;
          }
        });
        
        // Validate optional fields that have values
        const optionalFields = ['Identifier', 'Applicability'];
        optionalFields.forEach(fieldName => {
          if (compliance[fieldName] && compliance[fieldName].trim()) {
            const result = this.validateComplianceField(compliance, fieldName, compliance[fieldName]);
            if (result.errors.length > 0) {
              errors.push(`Item ${index + 1}: ${result.errors.join(', ')}`);
              isValid = false;
            }
          }
        });
      });
      
      return { isValid, errors };
    },

    async loadFrameworks() {
      try {
        this.loading = true;
        console.log('🔍 [CreateCompliance] Checking for cached framework data...');
        
        // FIRST: Try to get data from cache
        if (complianceDataService.hasFrameworksCache()) {
          console.log('✅ [CreateCompliance] Using cached framework data');
          const cachedFrameworks = complianceDataService.getData('frameworks') || [];
          
          this.frameworks = cachedFrameworks.map(fw => ({
            id: fw.FrameworkId || fw.id,
            name: fw.FrameworkName || fw.name
          }));
          console.log(`[CreateCompliance] Loaded ${this.frameworks.length} frameworks from cache (prefetched on Home page)`);
          this.updateFrameworkConfig();
        } else {
          // FALLBACK: Fetch from API if cache is empty
          console.log('⚠️ [CreateCompliance] No cached data found, fetching from API...');
          const response = await complianceService.getComplianceFrameworks();
          
          // Handle the response data with success wrapper
          if (response.data.success && Array.isArray(response.data.frameworks)) {
            this.frameworks = response.data.frameworks.map(fw => ({
              id: fw.id || fw.FrameworkId,
              name: fw.name || fw.FrameworkName
            }));
            this.updateFrameworkConfig();
            
            // Update cache so subsequent pages benefit
            complianceDataService.setData('frameworks', response.data.frameworks);
            console.log('ℹ️ [CreateCompliance] Cache updated after direct API fetch');
          } else if (Array.isArray(response.data)) {
            this.frameworks = response.data.map(fw => ({
              id: fw.id || fw.FrameworkId,
              name: fw.name || fw.FrameworkName
            }));
            this.updateFrameworkConfig();
            
            // Update cache
            complianceDataService.setData('frameworks', response.data);
            console.log('ℹ️ [CreateCompliance] Cache updated after direct API fetch');
          } else {
            console.error('Unexpected response format:', response.data);
            PopupService.error('Failed to load frameworks. Please refresh the page and try again.');
          }
          console.log(`[CreateCompliance] Loaded ${this.frameworks.length} frameworks directly from API (cache unavailable)`);
        }
      } catch (error) {
        console.error('Error loading frameworks:', error);
        
        // Check if it's an access control error
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showComplianceFrameworkDenied();
          return;
        }
        
        PopupService.error('Failed to load frameworks. Please refresh the page and try again.');
      } finally {
        this.loading = false;
      }
    },
    async loadPolicies(frameworkId) {
      try {
        this.loading = true;
        const response = await complianceService.getCompliancePolicies(frameworkId);
        console.log('Policies response:', response.data);
        
        if (response.data.success && Array.isArray(response.data.policies)) {
          this.policies = response.data.policies.map(p => ({
            id: p.id || p.PolicyId,
            name: p.name || p.PolicyName,
            applicability: p.applicability || p.scope || p.Applicability || ''
          }));
          this.policyConfig.values = this.policies.map(p => ({
            value: p,
            label: p.name
          }));
        } else if (Array.isArray(response.data)) {
          this.policies = response.data.map(p => ({
            id: p.id || p.PolicyId,
            name: p.name || p.PolicyName,
            applicability: p.applicability || p.scope || p.Applicability || ''
          }));
          this.policyConfig.values = this.policies.map(p => ({
            value: p,
            label: p.name
          }));
        } else {
          console.error('Error in response:', response.data);
          PopupService.error('Failed to load policies. Please try selecting a different framework.');
        }
      } catch (error) {
        console.error('Error loading policies:', error);
        
        // Check if it's an access control error
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showCompliancePolicyDenied();
          return;
        }
        
        PopupService.error('Failed to load policies. Please try selecting a different framework.');
      } finally {
        this.loading = false;
      }
    },
    async loadSubPolicies(policyId) {
      try {
        this.loading = true;
        const response = await complianceService.getComplianceSubPolicies(policyId);
        console.log('SubPolicies response:', response.data);
        
        if (response.data.success && Array.isArray(response.data.subpolicies)) {
          this.subPolicies = response.data.subpolicies.map(sp => ({
            id: sp.id || sp.SubPolicyId,
            name: sp.name || sp.SubPolicyName
          }));
          this.subPolicyConfig.values = this.subPolicies.map(sp => ({
            value: sp,
            label: sp.name
          }));
        } else if (Array.isArray(response.data)) {
          this.subPolicies = response.data.map(sp => ({
            id: sp.id || sp.SubPolicyId,
            name: sp.name || sp.SubPolicyName
          }));
          this.subPolicyConfig.values = this.subPolicies.map(sp => ({
            value: sp,
            label: sp.name
          }));
        } else {
          console.error('Error in response:', response.data);
          PopupService.error('Failed to load sub-policies. Please try selecting a different policy.');
        }
      } catch (error) {
        console.error('Error loading sub-policies:', error);
        
        // Check if it's an access control error
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showComplianceSubpolicyDenied();
          return;
        }
        
        PopupService.error('Failed to load sub-policies. Please try selecting a different policy.');
      } finally {
        this.loading = false;
      }
    },
    async loadUsers() {
      try {
        this.loading = true;
        const response = await complianceService.getUsers();
        console.log('Users API response:', response); // Debug log
        
        if (response.data.success && Array.isArray(response.data.users)) {
          // Resolve current logged-in user id from storage (fallbacks included)
          const storedUserId =
            localStorage.getItem('user_id') ||
            sessionStorage.getItem('userId') ||
            (localStorage.getItem('user') ? (() => { try { return JSON.parse(localStorage.getItem('user')).UserId; } catch(e) { return null; } })() : null) ||
            (sessionStorage.getItem('user') ? (() => { try { return JSON.parse(sessionStorage.getItem('user')).UserId; } catch(e) { return null; } })() : null);
          const currentUserId = storedUserId ? Number(storedUserId) : null;

          // Normalize and filter: exclude the currently logged-in user from reviewer list
          const allUsers = response.data.users.map(user => ({
            UserId: user.UserId,
            UserName: user.UserName || `User ${user.UserId}`,
            email: user.email || user.Email || ''
          }));

          this.users = currentUserId
            ? allUsers.filter(u => Number(u.UserId) !== Number(currentUserId))
            : allUsers;

          // Update reviewer config with filtered user values
          this.reviewerConfig.values = this.users.map(user => ({
            value: user.UserId,
            label: `${user.UserName}${user.email ? ` (${user.email})` : ''}`
          }));

          // Ensure currently selected reviewer is cleared if it was the logged-in user
          if (currentUserId && this.complianceList[0] && Number(this.complianceList[0].reviewer_id) === Number(currentUserId)) {
            this.complianceList.forEach(c => { c.reviewer_id = ''; });
          }
        } else {
          throw new Error('Invalid users data received');
        }
      } catch (error) {
        console.error('Failed to load users:', error);
        PopupService.error('Failed to load reviewers. Please refresh the page and try again.');
      } finally {
        this.loading = false;
      }
    },
    // Load category options from the server
    async loadCategoryOptions() {
      try {
        this.loading = true;
        
        console.log('Loading category options from server...');
        
        // Load business units
        const buResponse = await complianceService.getCategoryBusinessUnits('BusinessUnitsCovered');
        if (buResponse.data.success) {
          this.categoryOptions.BusinessUnitsCovered = buResponse.data.data;
          this.filteredOptions.BusinessUnitsCovered = [...buResponse.data.data];
          console.log('Loaded BusinessUnitsCovered:', this.categoryOptions.BusinessUnitsCovered);
        }
        
        // Load risk types
        const rtResponse = await complianceService.getCategoryBusinessUnits('RiskType');
        if (rtResponse.data.success) {
          this.categoryOptions.RiskType = rtResponse.data.data;
          this.filteredOptions.RiskType = [...rtResponse.data.data];
          console.log('Loaded RiskType:', this.categoryOptions.RiskType);
        }
        
        // Load risk categories
        const rcResponse = await complianceService.getCategoryBusinessUnits('RiskCategory');
        if (rcResponse.data.success) {
          this.categoryOptions.RiskCategory = rcResponse.data.data;
          this.filteredOptions.RiskCategory = [...rcResponse.data.data];
          console.log('Loaded RiskCategory:', this.categoryOptions.RiskCategory);
        }
        
        // Load risk business impacts
        const rbiResponse = await complianceService.getCategoryBusinessUnits('RiskBusinessImpact');
        if (rbiResponse.data.success) {
          this.categoryOptions.RiskBusinessImpact = rbiResponse.data.data;
          this.filteredOptions.RiskBusinessImpact = [...rbiResponse.data.data];
          console.log('Loaded RiskBusinessImpact:', this.categoryOptions.RiskBusinessImpact);
        }
        
        console.log('All category options loaded successfully');
      } catch (error) {
        console.error('Failed to load category options:', error);
        PopupService.error('Failed to load dropdown options. Some features may be limited.');
      } finally {
        this.loading = false;
      }
    },
    
    // Refresh category options from server
    async refreshCategoryOptions() {
      try {
        console.log('Refreshing category options...');
        await this.loadCategoryOptions();
        console.log('Category options refreshed successfully');
      } catch (error) {
        console.error('Failed to refresh category options:', error);
      }
    },
    
    // Handle dropdown refresh button click
    async handleDropdownRefresh(field) {
      try {
        this.loading = true;
        await this.refreshCategoryOptions();
        PopupService.success(`${field} options refreshed successfully`);
      } catch (error) {
        console.error(`Failed to refresh ${field} options:`, error);
        PopupService.error(`Failed to refresh ${field} options`);
      } finally {
        this.loading = false;
      }
    },
    
    // Show dropdown for a specific field
    showDropdown(index, field) {
      // Close any open dropdown
      this.activeDropdown = { index, field };
      
      // Initialize filtered options if not already set
      if (!this.filteredOptions[field] || this.filteredOptions[field].length === 0) {
        this.filteredOptions[field] = [...(this.categoryOptions[field] || [])];
      }
      
      // Set initial filtered options based on current search term
      this.filterOptions(index, field);
      
      console.log(`Showing dropdown for ${field} at index ${index}:`, this.filteredOptions[field]);
      
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
        this.activeDropdown = { index: null, field: null };
      }
    },
    
    // Clear search field and reset filtered options
    clearSearchField(index, field) {
      switch (field) {
        case 'BusinessUnitsCovered':
          this.businessUnitSearch[index] = '';
          break;
        case 'RiskType':
          this.riskTypeSearch[index] = '';
          break;
        case 'RiskCategory':
          this.riskCategorySearch[index] = '';
          break;
        case 'RiskBusinessImpact':
          this.riskBusinessImpactSearch[index] = '';
          break;
      }
      
      // Reset filtered options to show all options
      this.filteredOptions[field] = [...(this.categoryOptions[field] || [])];
    },
    
    // Filter dropdown options based on search term
    filterOptions(index, field, searchTerm = '') {
      let optionsToFilter = [];
      
      switch (field) {
        case 'Framework':
          optionsToFilter = this.frameworks;
          break;
        case 'Policy':
          optionsToFilter = this.policies;
          break;
        case 'SubPolicy':
          optionsToFilter = this.subPolicies;
          break;
        case 'BusinessUnitsCovered':
          optionsToFilter = this.categoryOptions.BusinessUnitsCovered || [];
          break;
        case 'RiskType':
          optionsToFilter = this.categoryOptions.RiskType || [];
          break;
        case 'RiskCategory':
          optionsToFilter = this.categoryOptions.RiskCategory || [];
          break;
        case 'RiskBusinessImpact':
          optionsToFilter = this.categoryOptions.RiskBusinessImpact || [];
          break;
      }
      
      // Get the current search term for this specific field and index
      let currentSearchTerm = '';
      switch (field) {
        case 'BusinessUnitsCovered':
          currentSearchTerm = this.businessUnitSearch[index] || '';
          break;
        case 'RiskType':
          currentSearchTerm = this.riskTypeSearch[index] || '';
          break;
        case 'RiskCategory':
          currentSearchTerm = this.riskCategorySearch[index] || '';
          break;
        case 'RiskBusinessImpact':
          currentSearchTerm = this.riskBusinessImpactSearch[index] || '';
          break;
        default:
          currentSearchTerm = searchTerm;
      }
      
      // Filter options based on search term (case-insensitive)
      const lowerSearchTerm = currentSearchTerm.toLowerCase();
      this.filteredOptions[field] = optionsToFilter.filter(option => 
        option.value.toLowerCase().includes(lowerSearchTerm)
      );
      
      console.log(`Filtered ${field} options:`, this.filteredOptions[field]);
    },
    
    // Select an option from the dropdown
    selectOption(index, field, value) {
      // Update the compliance item with the selected value
      this.complianceList[index][field] = value;
      
      // Update the search field to show the selected value
      switch (field) {
        case 'Framework':
          this.frameworkConfig.selectedValue = value;
          break;
        case 'Policy':
          this.policyConfig.selectedValue = value;
          break;
        case 'SubPolicy':
          this.subPolicyConfig.selectedValue = value;
          break;
        case 'BusinessUnitsCovered':
          this.businessUnitSearch[index] = value;
          break;
        case 'RiskType':
          this.riskTypeSearch[index] = value;
          break;
        case 'RiskCategory':
          this.riskCategorySearch[index] = value;
          break;
        case 'RiskBusinessImpact':
          this.riskBusinessImpactSearch[index] = value;
          break;
      }
      
      // Close the dropdown
      this.activeDropdown = { index: null, field: null };
      
      // Validate the field
      this.validateComplianceField(this.complianceList[index], field, value);
    },
    
    // Add a new option to the category options
    async addNewOption(index, field, value) {
      if (!value || !value.trim()) return;
      
      try {
        this.loading = true;
        
        console.log(`Adding new ${field} option:`, value);
        
        // Add the new option to the server
        const response = await complianceService.addCategoryBusinessUnit({
          source: field,
          value: value.trim()
        });
        
        console.log('Server response:', response);
        
        if (response.data.success) {
          // Add the new option to the local options
          const newOption = response.data.data;
          this.categoryOptions[field].push({
            id: newOption.id,
            value: newOption.value
          });
          
          // Update filtered options to include the new option
          this.filteredOptions[field].push({
            id: newOption.id,
            value: newOption.value
          });
          
          // Select the new option
          this.selectOption(index, field, newOption.value);
          
          PopupService.success(`Added new ${field} option: ${newOption.value}`);
          
          console.log(`Successfully added ${field} option:`, newOption);
        } else {
          throw new Error(response.data.error || 'Failed to add new option');
        }
      } catch (error) {
        console.error(`Failed to add new ${field} option:`, error);
        
        // Check if it's a duplicate error
        if (error.response && error.response.data && error.response.data.error && 
            error.response.data.error.includes('already exists')) {
          PopupService.warning(`"${value}" already exists. Please select it from the dropdown.`);
        } else {
          PopupService.error(`Failed to add new option: ${error.message || error}`);
        }
      } finally {
        this.loading = false;
      }
    },
    
    addCompliance() {
      const policyApplicability = this.selectedPolicy ? this.selectedPolicy.applicability || '' : '';
      this.complianceList.push({
        ComplianceTitle: '',
        ComplianceItemDescription: '',
        ComplianceType: '',
        Scope: '',
        Objective: '',
        BusinessUnitsCovered: '',
        Identifier: '',
        IsRisk: false,
        PossibleDamage: '',
        mitigation: '',
        PotentialRiskScenarios: '',
        RiskType: '',
        RiskCategory: '',
        RiskBusinessImpact: '',
        Criticality: 'Medium',
        MandatoryOptional: 'Mandatory',
        ManualAutomatic: 'Manual',
        Impact: 5.0,
        Probability: 5.0,
        Status: 'Under Review',
        reviewer_id: '', // No default reviewer
        CreatedByName: '', // No default creator
        Applicability: policyApplicability,
        MaturityLevel: 'Initial',
        ActiveInactive: 'Active',
        PermanentTemporary: 'Permanent',
        mitigationSteps: [{ stepNumber: 1, description: '' }],
        validationErrors: {}
      });
      this.businessUnitSearch.push('');
      this.riskTypeSearch.push('');
      this.riskCategorySearch.push('');
      this.riskBusinessImpactSearch.push('');
      this.activeTab = this.complianceList.length - 1;
      this.onMitigationStepChange(this.activeTab);
      
      // Check for duplicate titles after adding new compliance
      this.checkDuplicateTitles(this.activeTab);
    },
    removeCompliance(idx) {
      if (this.complianceList.length > 1) {
        // If removing the active tab or a tab before it, adjust the active tab
        if (idx <= this.activeTab) {
          // If removing the last tab and it's active, go to previous tab
          if (idx === this.complianceList.length - 1 && idx === this.activeTab) {
            this.activeTab = Math.max(0, idx - 1);
          } 
          // If removing a tab before the active one, decrement active tab index
          else if (idx < this.activeTab) {
            this.activeTab--;
          }
        }
        
        // Remove the compliance item
        this.complianceList.splice(idx, 1);
        
        // Remove the search terms for this item
        this.businessUnitSearch.splice(idx, 1);
        this.riskTypeSearch.splice(idx, 1);
        this.riskCategorySearch.splice(idx, 1);
        this.riskBusinessImpactSearch.splice(idx, 1);
        
        // Close any open dropdown
        this.activeDropdown = { index: null, field: null };
      }
    },

    async submitCompliance() {
      try {
        // Check consent before proceeding
        const consentService = (await import('@/services/consentService.js')).default;
        const { CONSENT_ACTIONS } = await import('@/utils/consentManager.js');
        
        const canProceed = await consentService.checkAndRequestConsent(
          CONSENT_ACTIONS.CREATE_COMPLIANCE
        );
        
        // If user declined consent, stop here
        if (!canProceed) {
          console.log('Compliance creation cancelled by user (consent declined)');
          return;
        }
        
        const validation = this.validateAllFields();
        if (!validation.isValid) {
          PopupService.error(`Validation failed: ${validation.errors.join(', ')}`);
          return;
        }
        this.loading = true;
        const loggedInUserId = localStorage.getItem('user_id') || '';
        const createdCompliances = [];
        const errors = [];
        if (this.complianceList.length > 1) {
          PopupService.info(`Creating ${this.complianceList.length} compliance items. Please wait...`, 'Processing');
        }
        for (let idx = 0; idx < this.complianceList.length; idx++) {
          const compliance = this.complianceList[idx];
          // Only set CreatedByName if user is logged in
          compliance.CreatedByName = loggedInUserId || '';
          try {
            this.onMitigationStepChange(idx);
            if (!this.selectedSubPolicy?.id) {
              throw new Error('SubPolicy is required');
            }
            let mitigationToSend = compliance.mitigation;
            if (typeof mitigationToSend === 'object' && mitigationToSend !== null) {
              mitigationToSend = JSON.stringify(mitigationToSend);
            } else if (typeof mitigationToSend !== 'string') {
              mitigationToSend = '';
            }
            const complianceData = {
              SubPolicy: this.selectedSubPolicy.id,
              ComplianceTitle: compliance.ComplianceTitle?.trim(),
              ComplianceItemDescription: compliance.ComplianceItemDescription?.trim(),
              ComplianceType: compliance.ComplianceType?.trim(),
              Scope: compliance.Scope?.trim(),
              Objective: compliance.Objective?.trim(),
              BusinessUnitsCovered: compliance.BusinessUnitsCovered?.trim(),
              Identifier: compliance.Identifier?.trim() || '',
              IsRisk: Boolean(compliance.IsRisk),
              PossibleDamage: compliance.PossibleDamage?.trim(),
              mitigation: mitigationToSend,
              PotentialRiskScenarios: compliance.PotentialRiskScenarios?.trim(),
              RiskType: compliance.RiskType?.trim(),
              RiskCategory: compliance.RiskCategory?.trim(),
              RiskBusinessImpact: compliance.RiskBusinessImpact?.trim(),
              MandatoryOptional: compliance.MandatoryOptional || 'Mandatory',
              ManualAutomatic: compliance.ManualAutomatic || 'Manual',
              Impact: parseFloat(compliance.Impact) || 5.0,
              Probability: parseFloat(compliance.Probability) || 5.0,
              Status: 'Under Review',
              ComplianceVersion: "1.0",
              reviewer: compliance.reviewer_id, // Must be explicitly set
              CreatedByName: compliance.CreatedByName, // Must be explicitly set
              Applicability: compliance.Applicability?.trim(),
              MaturityLevel: compliance.MaturityLevel || 'Initial',
              ActiveInactive: compliance.ActiveInactive || 'Active',
              PermanentTemporary: compliance.PermanentTemporary || 'Permanent',
              ApprovalDueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
            };
            
            const requiredFields = ['SubPolicy', 'ComplianceTitle', 'ComplianceItemDescription', 'reviewer'];
            const missingFields = requiredFields.filter(field => !complianceData[field]);
            if (missingFields.length > 0) {
              throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
            }
            const timeoutPromise = new Promise((_, reject) => 
              setTimeout(() => reject(new Error('Request timeout')), 30000)
            );
            const response = await Promise.race([
              complianceService.createCompliance(complianceData),
              timeoutPromise
            ]);
            if (!response.data.success) {
              throw new Error(response.data.message || 'Failed to create compliance');
            }
            createdCompliances.push({
              ComplianceId: response.data.compliance_id,
              ComplianceItemDescription: complianceData.ComplianceItemDescription,
              Identifier: response.data.Identifier,
              itemNumber: idx + 1
            });
            if (idx < this.complianceList.length - 1) {
              await new Promise(resolve => setTimeout(resolve, 100));
            }
          } catch (error) {
            // Handle specific backend validation errors
            if (error.response && error.response.data && error.response.data.errors) {
              const backendErrors = error.response.data.errors;
              if (backendErrors.ComplianceTitle) {
                errors.push(`Item ${idx + 1}: ${backendErrors.ComplianceTitle.join(', ')}`);
              } else {
                errors.push(`Item ${idx + 1}: ${error.response.data.message || 'Failed to create compliance'}`);
              }
            } else {
              errors.push(`Item ${idx + 1}: ${error.message || 'Failed to create compliance'}`);
            }
          }
        }
        if (createdCompliances.length > 0) {
          if (createdCompliances.length === this.complianceList.length) {
            PopupService.success(`Successfully created ${createdCompliances.length} compliance item(s)!`);
          } else {
            PopupService.warning(`Created ${createdCompliances.length} out of ${this.complianceList.length} compliance items. Some items failed to create.`);
          }
          createdCompliances.forEach(compliance => {
            const popupData = {
              ComplianceId: compliance.ComplianceId,
              ComplianceItemDescription: compliance.ComplianceItemDescription,
              Identifier: compliance.Identifier
            };
            CompliancePopups.complianceCreated(popupData);
          });
        }
        if (errors.length > 0) {
          PopupService.error(`Failed to create some compliance items: ${errors.join(', ')}`);
        }
        if (createdCompliances.length > 0) {
          this.resetForm();
        } else {
          PopupService.error('Failed to create any compliance items. Please check your input and try again.');
        }
      } catch (error) {
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showComplianceCreateDenied();
          return;
        }
        this.$toast?.error(error.response?.data?.message || error.message || 'Failed to create compliance items');
      } finally {
        this.loading = false;
      }
    },
    addStep(complianceIndex) {
      this.complianceList[complianceIndex].mitigationSteps.push({
        stepNumber: this.complianceList[complianceIndex].mitigationSteps.length + 1,
        description: ''
      });
      // Force Vue to update the component
      this.$forceUpdate();
    },
    
    removeStep(complianceIndex, stepIndex) {
      this.complianceList[complianceIndex].mitigationSteps.splice(stepIndex, 1);
      // Renumber remaining steps
      this.complianceList[complianceIndex].mitigationSteps.forEach((step, idx) => {
        step.stepNumber = idx + 1;
      });
      this.onMitigationStepChange(complianceIndex);
    },
    
    onMitigationStepChange(complianceIndex) {
      const compliance = this.complianceList[complianceIndex];
      let mitigationData = {};
      
      compliance.mitigationSteps.forEach((step, idx) => {
        const stepText = step.description.trim();
        if (stepText) {
          mitigationData[idx + 1] = stepText;
        }
      });
      
      compliance.mitigation = mitigationData;
      
      // Validate the field
      this.validateComplianceField(compliance, 'mitigation', compliance.mitigation);
    },

    resetForm() {
      this.complianceList = [{
        ComplianceTitle: '',
        ComplianceItemDescription: '',
        ComplianceType: '',
        Scope: '',
        Objective: '',
        BusinessUnitsCovered: '',
        Identifier: '',
        IsRisk: false,
        PossibleDamage: '',
        mitigation: '',
        PotentialRiskScenarios: '',
        RiskType: '',
        RiskCategory: '',
        RiskBusinessImpact: '',
        Criticality: 'Medium',
        MandatoryOptional: 'Mandatory',
        ManualAutomatic: 'Manual',
        Impact: 5.0,
        Probability: 5.0,
        Status: 'Under Review',
        reviewer_id: '', // No default reviewer
        CreatedByName: '', // No default creator
        Applicability: '',
        MaturityLevel: 'Initial',
        ActiveInactive: 'Active',
        PermanentTemporary: 'Permanent',
        mitigationSteps: [{ stepNumber: 1, description: '' }],
        validationErrors: {}
      }];
      this.selectedFramework = '';
      this.selectedPolicy = '';
      this.selectedSubPolicy = '';
      this.policies = [];
      this.subPolicies = [];
      this.businessUnitSearch = [''];
      this.riskTypeSearch = [''];
      this.riskCategorySearch = [''];
      this.riskBusinessImpactSearch = [''];
      this.activeTab = 0;
      this.error = null;
      this.loading = false;
      this.existingComplianceTitles = []; // Clear existing compliance titles
      
      // Clear any pending timeout
      if (this.duplicateCheckTimeout) {
        clearTimeout(this.duplicateCheckTimeout);
        this.duplicateCheckTimeout = null;
      }
      
      this.onMitigationStepChange(0);
    },
         onFrameworkChange(option) {
       this.selectedFramework = option.value;
       if (option.value && option.value.id) {
         // Save the selected framework to session
         this.saveFrameworkToSession(option.value.id);
         
         this.loadPolicies(option.value.id);
         this.selectedPolicy = '';
         this.selectedSubPolicy = '';
         this.policies = [];
         this.subPolicies = [];
       }
     },
     onPolicyChange(option) {
       this.selectedPolicy = option.value;
       if (option.value && option.value.id) {
         this.loadSubPolicies(option.value.id);
         this.selectedSubPolicy = '';
         this.subPolicies = [];
         
         // Set the applicability for all compliance items from the selected policy
         if (option.value.applicability) {
           this.complianceList.forEach(compliance => {
             compliance.Applicability = option.value.applicability;
           });
         }
       }
     },
           onSubPolicyChange(option) {
        this.selectedSubPolicy = option.value;
        
        // Set the applicability for all compliance items from the selected sub-policy
        if (option.value && option.value.applicability) {
          this.complianceList.forEach(compliance => {
            compliance.Applicability = option.value.applicability;
          });
        }
        
        // Load existing compliance titles for this subpolicy to help with duplicate detection
        if (option.value && option.value.id) {
          this.loadExistingComplianceTitles(option.value.id);
          
          // Check for duplicates in existing compliance items after loading
          setTimeout(() => {
            this.complianceList.forEach((compliance, index) => {
              if (compliance.ComplianceTitle) {
                this.checkDuplicateTitles(index);
              }
            });
          }, 1000); // Give time for the API call to complete
        }
      },
      
      // Load existing compliance titles for the selected subpolicy
      async loadExistingComplianceTitles(subpolicyId) {
        try {
          console.log('Loading existing compliance titles for subpolicy:', subpolicyId);
          const response = await complianceService.getCompliancesBySubPolicy(subpolicyId);
          console.log('Response:', response.data);
          
          if (response.data.success && Array.isArray(response.data.data)) {
            // Extract all compliance titles from the grouped structure
            const allTitles = [];
            response.data.data.forEach(group => {
              if (Array.isArray(group)) {
                group.forEach(compliance => {
                  if (compliance.ComplianceTitle) {
                    allTitles.push(compliance.ComplianceTitle.trim().toLowerCase());
                  }
                });
              }
            });
            this.existingComplianceTitles = allTitles;
            console.log('Loaded existing titles:', this.existingComplianceTitles);
          } else {
            this.existingComplianceTitles = [];
            console.log('No existing titles found');
          }
        } catch (error) {
          console.error('Failed to load existing compliance titles:', error);
          this.existingComplianceTitles = [];
        }
      },
      onReviewerChange(option) {
        // The reviewer_id is already updated via v-model
        // Additional logic can be added here if needed
        console.log('Reviewer changed to:', option.value);
      },
      // Test error display
      testErrorDisplay(index) {
        console.log('Testing error display for index:', index);
        const compliance = this.complianceList[index];
        console.log('Current validation errors:', compliance.validationErrors);
        console.log('Has ComplianceTitle errors:', this.hasComplianceTitleErrors(compliance));
        console.log('Error message:', this.getComplianceTitleErrorMessage(compliance));
        
        // Force set an error for testing
        if (!compliance.validationErrors) {
          compliance.validationErrors = {};
        }
        compliance.validationErrors.ComplianceTitle = ['TEST ERROR: This is a test error message'];
        
        // Force update
        this.$nextTick(() => {
          this.$forceUpdate();
        });
      },
      // Force display error message
      forceDisplayError(index) {
        const compliance = this.complianceList[index];
        if (!compliance.validationErrors) {
          compliance.validationErrors = {};
        }
        
        // Set the error message
        compliance.validationErrors.ComplianceTitle = ['This title already exists in this subpolicy. Please choose a different title.'];
        
        // Force reactivity
        this.complianceList[index] = { ...compliance };
        
        // Force update
        this.$nextTick(() => {
          this.$forceUpdate();
        });
        
        console.log('Forced error display for index:', index);
      },
      // Enhanced error display method
      enhancedErrorDisplay(index) {
        const compliance = this.complianceList[index];
        
        // Create a new validation errors object
        const newValidationErrors = {
          ...compliance.validationErrors,
          ComplianceTitle: ['This title already exists in this subpolicy. Please choose a different title.']
        };
        
        // Update the compliance object
        const updatedCompliance = {
          ...compliance,
          validationErrors: newValidationErrors
        };
        
        // Update the compliance list
        this.complianceList.splice(index, 1, updatedCompliance);
        
        // Force update
        this.$nextTick(() => {
          this.$forceUpdate();
        });
        
        console.log('Enhanced error display for index:', index);
      }
  }
}
</script>

<style scoped>
@import './CreateCompliance.css';

.create-compliance-container {
  font-size: 14px;  /* Base font size for the component */
}

.compliance-header h2 {
  font-size: 1.5rem;
}

.compliance-header p {
  font-size: 0.9rem;
}

.compliance-field label {
  font-size: 0.85rem;
}

.compliance-input,
.compliance-select {
  font-size: 0.9rem !important;
}

.item-number {
  font-size: 1.5rem;
}

.compliance-submit-btn {
  font-size: 0.9rem;
}

.validation-error {
  font-size: 0.75rem;
}

.compliance-field small {
  font-size: 0.75rem;
}

.mitigation-steps {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.mitigation-step {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 1rem;
  background: #f9f9f9;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.step-numberr {
  font-weight: 500 !important;
  color: #666 !important;
}

.remove-step-btn {
  background: none;
  border: none;
  color: #dc3545;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
}

.remove-step-btn:hover {
  background: #fee;
}

.add-step-btn {
  background: #f8f9fa;
  border: 1px dashed #ddd;
  color: #666;
  padding: 0.5rem;
  border-radius: 4px;
  cursor: pointer;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.add-step-btn:hover {
  background: #fff;
  border-color: #999;
  color: #333;
}

.error-input {
  border-color: #dc3545 !important;
  box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25) !important;
}

.error-input:focus {
  border-color: #dc3545 !important;
  box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25) !important;
}
</style> 