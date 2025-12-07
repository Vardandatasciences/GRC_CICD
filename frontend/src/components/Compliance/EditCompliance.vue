<template>
  <div class="create-compliance-container">
    <!-- Header section -->
    <div class="compliance-header">
      <div class="header-content">
        <div class="header-actions">
          <button 
            class="back-button" 
            @click="goBack"
            title="Go back to previous page"
          >
            <i class="fas fa-arrow-left"></i>
          </button>
        </div>
        <div class="header-text">
          <h2>Edit Compliance Record</h2>
          <p>Update compliance item details</p>
        </div>
      </div>
    </div>

    <!-- Message display -->
    <div v-if="error" class="message error-message">
      {{ error }}
    </div>
    <div v-if="successMessage" class="message success-message">
      {{ successMessage }}
    </div>

    <!-- Loading indicator - Removed as requested -->
    <!-- <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <div class="loading-text">Loading data...</div>
    </div> -->

    <!-- Edit form -->
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
              <span class="field-requirements">({{ validationRules.minLengths.ComplianceTitle }}-{{ validationRules.maxLengths.ComplianceTitle }} characters)</span>
            </label>
            <div class="input-wrapper">
              <input 
                v-model="compliance.ComplianceTitle" 
                class="compliance-input" 
                :class="{
                  'error': validationErrors.ComplianceTitle,
                  'warning': showWarning('ComplianceTitle'),
                  'valid': isFieldValid('ComplianceTitle')
                }"
                placeholder="Enter compliance title"
                required 
                @input="onFieldChange('ComplianceTitle', $event)"
                @blur="validateField('ComplianceTitle')"
                title="Enter the title of the compliance item"
                :ref="'field_ComplianceTitle'"
                :maxlength="validationRules.maxLengths.ComplianceTitle"
              />
              <div class="validation-indicator" v-if="compliance.ComplianceTitle">
                <span v-if="isFieldValid('ComplianceTitle')" class="valid-icon">✓</span>
              </div>
            </div>
            <div v-if="validationErrors.ComplianceTitle" class="field-error-message">
              {{ validationErrors.ComplianceTitle.join(', ') }}
            </div>
          </div>
          
          <div class="compliance-field">
            <label>
              Compliance Type 
              <span class="required">*</span>
              <span class="field-requirements">({{ validationRules.minLengths.ComplianceType }}-{{ validationRules.maxLengths.ComplianceType }} characters)</span>
            </label>
            <div class="input-wrapper">
              <input 
                v-model="compliance.ComplianceType" 
                class="compliance-input" 
                :class="{
                  'error': validationErrors.ComplianceType,
                  'valid': isFieldValid('ComplianceType')
                }"
                placeholder="Enter compliance type"
                @input="onFieldChange('ComplianceType', $event)"
                @blur="validateField('ComplianceType')"
                title="Type of compliance (e.g. Regulatory, Internal, Security)"
                :ref="'field_ComplianceType'"
                :maxlength="validationRules.maxLengths.ComplianceType"
              />
              <div class="validation-indicator" v-if="compliance.ComplianceType">
                <span v-if="isFieldValid('ComplianceType')" class="valid-icon">✓</span>
              </div>
            </div>
            <div v-if="validationErrors.ComplianceType" class="field-error-message">
              {{ validationErrors.ComplianceType.join(', ') }}
            </div>
          </div>
        </div>
        
        <div class="compliance-field full-width">
          <label>
            Compliance Description 
            <span class="required">*</span>
            <span class="field-requirements">(Minimum {{ validationRules.minLengths.ComplianceItemDescription }} characters)</span>
          </label>
          <div class="input-wrapper">
            <textarea 
              v-model="compliance.ComplianceItemDescription" 
              class="compliance-input" 
              :class="{
                'error': validationErrors.ComplianceItemDescription,
                'warning': showWarning('ComplianceItemDescription'),
                'valid': isFieldValid('ComplianceItemDescription')
              }"
              placeholder="Compliance Description"
              @input="onFieldChange('ComplianceItemDescription', $event)"
              @blur="validateField('ComplianceItemDescription')"
              required 
              rows="3"
              title="Detailed description of the compliance requirement"
              :ref="'field_ComplianceItemDescription'"
              :maxlength="validationRules.maxLengths.ComplianceItemDescription"
            ></textarea>
            <div class="char-count" :class="{ 'error': validationErrors.ComplianceItemDescription }">
              {{ compliance.ComplianceItemDescription?.length || 0 }}/{{ validationRules.minLengths.ComplianceItemDescription }} min characters
            </div>
            <div v-if="validationErrors.ComplianceItemDescription" class="field-error-message">
              {{ validationErrors.ComplianceItemDescription.join(', ') }}
            </div>
          </div>
          <div class="validation-feedback" v-if="compliance.ComplianceItemDescription">
            <div class="validation-progress">
              <div 
                class="progress-bar"
                :style="{
                  width: getValidationProgress('ComplianceItemDescription') + '%',
                  backgroundColor: getValidationColor('ComplianceItemDescription')
                }"
              ></div>
            </div>
            <span 
              :class="[
                'validation-message',
                {
                  'warning': showWarning('ComplianceItemDescription'),
                  'error': validationErrors.ComplianceItemDescription,
                  'success': isFieldValid('ComplianceItemDescription')
                }
              ]"
            >
              {{ getValidationMessage('ComplianceItemDescription') }}
            </span>
          </div>
        </div>
        
        <div class="compliance-field full-width">
          <label>
            Scope
            <span class="required">*</span>
            <span class="field-requirements">(Minimum {{ validationRules.minLengths.Scope }} characters)</span>
          </label>
          <div class="input-wrapper">
            <textarea 
              v-model="compliance.Scope" 
              class="compliance-input" 
              :class="{
                'error': validationErrors.Scope,
                'warning': showWarning('Scope'),
                'valid': isFieldValid('Scope')
              }"
              placeholder="Define the scope of this compliance requirement"
              @input="onFieldChange('Scope', $event)"
              @blur="validateField('Scope')"
              rows="3"
              data-field="Scope"
              required
              :ref="'field_Scope'"
              :maxlength="validationRules.maxLengths.Scope"
            ></textarea>
            <div class="char-count" :class="{ 
              'error': validationErrors.Scope,
              'warning': showWarning('Scope')
            }">
              {{ compliance.Scope?.length || 0 }}/{{ validationRules.minLengths.Scope }} min characters
            </div>
            <div v-if="validationErrors.Scope" class="field-error-message">
              {{ validationErrors.Scope.join(', ') }}
            </div>
          </div>
          <div class="validation-feedback" v-if="compliance.Scope">
            <div class="validation-progress">
              <div 
                class="progress-bar"
                :style="{
                  width: getValidationProgress('Scope') + '%',
                  backgroundColor: getValidationColor('Scope')
                }"
              ></div>
            </div>
            <span 
              :class="[
                'validation-message',
                {
                  'warning': showWarning('Scope'),
                  'error': validationErrors.Scope,
                  'success': isFieldValid('Scope')
                }
              ]"
            >
              {{ getValidationMessage('Scope') }}
            </span>
          </div>
        </div>
        
        <div class="compliance-field full-width">
          <label>
            Objective
            <span class="required">*</span>
            <span class="field-requirements">(Minimum {{ validationRules.minLengths.Objective }} characters)</span>
          </label>
          <div class="input-wrapper">
            <textarea 
              v-model="compliance.Objective" 
              class="compliance-input" 
              :class="{
                'error': validationErrors.Objective,
                'warning': showWarning('Objective'),
                'valid': isFieldValid('Objective')
              }"
              placeholder="Define the objective of this compliance requirement"
              @input="onFieldChange('Objective', $event)"
              @blur="validateField('Objective')"
              rows="3"
              data-field="Objective"
              required
              :ref="'field_Objective'"
              :maxlength="validationRules.maxLengths.Objective"
            ></textarea>
            <div class="char-count" :class="{ 
              'error': validationErrors.Objective,
              'warning': showWarning('Objective')
            }">
              {{ compliance.Objective?.length || 0 }}/{{ validationRules.minLengths.Objective }} min characters
            </div>
            <div v-if="validationErrors.Objective" class="field-error-message">
              {{ validationErrors.Objective.join(', ') }}
            </div>
          </div>
          <div class="validation-feedback" v-if="compliance.Objective">
            <div class="validation-progress">
              <div 
                class="progress-bar"
                :style="{
                  width: getValidationProgress('Objective') + '%',
                  backgroundColor: getValidationColor('Objective')
                }"
              ></div>
            </div>
            <span 
              :class="[
                'validation-message',
                {
                  'warning': showWarning('Objective'),
                  'error': validationErrors.Objective,
                  'success': isFieldValid('Objective')
                }
              ]"
            >
              {{ getValidationMessage('Objective') }}
            </span>
          </div>
        </div>
        
        <!-- Business Units, Identifier and IsRisk in one row -->
        <div class="row-fields">
          <div class="compliance-field">
            <label>Business Units Covered</label>
            <div class="searchable-dropdown">
              <input 
                v-model="displayBusinessUnits" 
                class="compliance-input" 
                :placeholder="compliance.BusinessUnitsCovered ? compliance.BusinessUnitsCovered : 'Search or add business units'"
                title="Departments or business units affected by this compliance"
                @focus="showDropdown('BusinessUnitsCovered')"
                @input="onBusinessUnitInput"
                :ref="'field_BusinessUnitsCovered'"
                readonly
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
              <button 
                v-if="compliance.BusinessUnitsCovered" 
                @click="clearBusinessUnit" 
                class="clear-selection-btn" 
                title="Clear selection"
                type="button"
              >
                <i class="fas fa-times"></i>
              </button>
            </div>
            <div v-if="validationErrors.BusinessUnitsCovered" class="field-error-message">
              {{ validationErrors.BusinessUnitsCovered }}
            </div>
          </div>
          
          <div class="compliance-field">
            <label>Identifier</label>
            <input 
              v-model="compliance.Identifier" 
              class="compliance-input" 
              placeholder="Auto-generated if left empty"
              title="Unique identifier for this compliance item"
              disabled
              :ref="'field_Identifier'"
            />
            <div v-if="validationErrors.Identifier" class="field-error-message">
              {{ validationErrors.Identifier }}
            </div>
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
      <div class="field-group risk-fields">
        <div class="field-group-title">Risk Information</div>
        <div class="compliance-field full-width">
          <label>
            Possible Impact
            <span class="required">*</span>
            <span class="field-requirements">(Minimum {{ validationRules.minLengths.PossibleDamage }} characters)</span>
          </label>
          <div class="input-wrapper">
            <textarea 
              v-model="compliance.PossibleDamage" 
              class="compliance-input" 
              :class="{
                'error': validationErrors.PossibleDamage,
                'warning': showWarning('PossibleDamage'),
                'valid': isFieldValid('PossibleDamage')
              }"
              placeholder="Describe possible damage"
              @input="onFieldChange('PossibleDamage', $event)"
              @blur="validateField('PossibleDamage')"
              rows="3"
              :required="compliance.IsRisk"
              :ref="'field_PossibleDamage'"
              :maxlength="validationRules.maxLengths.PossibleDamage"
            ></textarea>
            <div class="char-count" :class="{ 'error': validationErrors.PossibleDamage }">
              {{ compliance.PossibleDamage?.length || 0 }}/{{ validationRules.minLengths.PossibleDamage }} min characters
            </div>
            <div v-if="validationErrors.PossibleDamage" class="field-error-message">
              {{ validationErrors.PossibleDamage.join(', ') }}
            </div>
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
            {{ validationErrors.mitigation.join(', ') }}
          </div>
        </div>
        
        <div class="compliance-field full-width">
          <label>
            Potential Risk Scenarios
            <span class="field-requirements">(Recommended: {{ validationRules.minLengths.PotentialRiskScenarios }}+ characters)</span>
          </label>
          <div class="input-wrapper">
            <textarea 
              v-model="compliance.PotentialRiskScenarios" 
              class="compliance-input" 
              :class="{
                'warning': showWarning('PotentialRiskScenarios'),
                'valid': isFieldValid('PotentialRiskScenarios')
              }"
              placeholder="Describe potential risk scenarios"
              @input="onFieldChange('PotentialRiskScenarios', $event)"
              @blur="validateField('PotentialRiskScenarios')"
              rows="3"
              :ref="'field_PotentialRiskScenarios'"
              :maxlength="validationRules.maxLengths.PotentialRiskScenarios"
            ></textarea>
            <div class="char-count">
              {{ compliance.PotentialRiskScenarios?.length || 0 }} characters
            </div>
            <div v-if="validationErrors.PotentialRiskScenarios" class="field-error-message">
              {{ validationErrors.PotentialRiskScenarios.join(', ') }}
            </div>
          </div>
        </div>
        
        <div class="row-fields">
          <div class="compliance-field">
            <label>
              Risk Type
              <span class="required">*</span>
            </label>
            <div class="input-wrapper">
              <select 
                v-model="compliance.RiskType"
                class="compliance-input"
                :class="{
                  'error': validationErrors.RiskType,
                  'valid': isFieldValid('RiskType')
                }"
                @change="onFieldChange('RiskType', $event)"
                @blur="validateField('RiskType')"
                :ref="'field_RiskType'"
              >
                <option value="">Select Risk Type</option>
                <option value="Current">Current</option>
                <option value="Residual">Residual</option>
                <option value="Inherent">Inherent</option>
                <option value="Emerging">Emerging</option>
                <option value="Accepted">Accepted</option>
              </select>
              <div class="validation-indicator" v-if="compliance.RiskType">
                <span v-if="isFieldValid('RiskType')" class="valid-icon">✓</span>
              </div>
            </div>
            <div v-if="validationErrors.RiskType" class="field-error-message">
              {{ validationErrors.RiskType.join(', ') }}
            </div>
          </div>
          
          <div class="compliance-field">
            <label>
              Risk Category
              <span class="required">*</span>
            </label>
            <div class="searchable-dropdown">
              <input 
                v-model="displayRiskCategory" 
                class="compliance-input" 
                :class="{
                  'error': validationErrors.RiskCategory,
                  'valid': isFieldValid('RiskCategory')
                }"
                :placeholder="compliance.RiskCategory ? compliance.RiskCategory : 'Search or add risk category'"
                @focus="showDropdown('RiskCategory')"
                @input="onRiskCategoryInput"
                :ref="'field_RiskCategory'"
                readonly
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
              <div class="validation-indicator" v-if="compliance.RiskCategory">
                <span v-if="isFieldValid('RiskCategory')" class="valid-icon">✓</span>
              </div>
              <button 
                v-if="compliance.RiskCategory" 
                @click="clearRiskCategory" 
                class="clear-selection-btn" 
                title="Clear selection"
                type="button"
              >
                <i class="fas fa-times"></i>
              </button>
            </div>
            <div v-if="validationErrors.RiskCategory" class="field-error-message">
              {{ validationErrors.RiskCategory }}
            </div>
          </div>
          
          <div class="compliance-field">
            <label>
              Risk Business Impact
              <span class="required">*</span>
            </label>
            <div class="searchable-dropdown">
              <input 
                v-model="displayRiskBusinessImpact" 
                class="compliance-input" 
                :class="{
                  'error': validationErrors.RiskBusinessImpact,
                  'valid': isFieldValid('RiskBusinessImpact')
                }"
                :placeholder="compliance.RiskBusinessImpact ? compliance.RiskBusinessImpact : 'Search or add business impact'"
                @focus="showDropdown('RiskBusinessImpact')"
                @input="onRiskBusinessImpactInput"
                :ref="'field_RiskBusinessImpact'"
                readonly
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
              <div class="validation-indicator" v-if="compliance.RiskBusinessImpact">
                <span v-if="isFieldValid('RiskBusinessImpact')" class="valid-icon">✓</span>
              </div>
              <button 
                v-if="compliance.RiskBusinessImpact" 
                @click="clearRiskBusinessImpact" 
                class="clear-selection-btn" 
                title="Clear selection"
                type="button"
              >
                <i class="fas fa-times"></i>
              </button>
            </div>
            <div v-if="validationErrors.RiskBusinessImpact" class="field-error-message">
              {{ validationErrors.RiskBusinessImpact }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- Compliance classification fields - grouped together -->
      <div class="field-group classification-fields">
        <div class="field-group-title">Classification</div>
        <div class="row-fields">
          <div class="compliance-field">
            <label>
              Criticality
              <span class="required">*</span>
            </label>
            <div class="input-wrapper">
              <select 
                v-model="compliance.Criticality" 
                class="compliance-select" 
                :class="{
                  'error': validationErrors.Criticality,
                  'valid': isFieldValid('Criticality')
                }"
                @change="onFieldChange('Criticality', $event)"
                @blur="validateField('Criticality')"
                required
                :ref="'field_Criticality'"
              >
                <option value="">Select Criticality</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
              <div class="validation-indicator" v-if="compliance.Criticality">
                <span v-if="isFieldValid('Criticality')" class="valid-icon">✓</span>
              </div>
            </div>
            <div v-if="validationErrors.Criticality" class="field-error-message">
              {{ validationErrors.Criticality.join(', ') }}
            </div>
          </div>
          
          <div class="compliance-field">
            <label>
              Mandatory/Optional
            </label>
            <select 
              v-model="compliance.MandatoryOptional" 
              class="compliance-select" 
              required
              title="Whether this compliance item is mandatory or optional"
              :ref="'field_MandatoryOptional'"
            >
              <option value="Mandatory">Mandatory</option>
              <option value="Optional">Optional</option>
            </select>
            <div v-if="validationErrors.MandatoryOptional" class="field-error-message">
              {{ validationErrors.MandatoryOptional }}
            </div>
          </div>
        </div>
        
        <div class="row-fields">
          <div class="compliance-field">
            <label>
              Manual/Automatic
            </label>
            <select 
              v-model="compliance.ManualAutomatic" 
              class="compliance-select" 
              required
              title="Whether this compliance is checked manually or automatically"
              :ref="'field_ManualAutomatic'"
            >
              <option value="Manual">Manual</option>
              <option value="Automatic">Automatic</option>
            </select>
            <div v-if="validationErrors.ManualAutomatic" class="field-error-message">
              {{ validationErrors.ManualAutomatic }}
            </div>
          </div>
          
          <div class="compliance-field">
            <label>
              Applicability
            </label>
            <input 
              v-model="compliance.Applicability" 
              class="compliance-input" 
              placeholder="Applicability from policy"
              title="Describes where this compliance item applies"
              :ref="'field_Applicability'"
            />
            <div v-if="validationErrors.Applicability" class="field-error-message">
              {{ validationErrors.Applicability }}
            </div>
          </div>
        </div>
        
        <div class="row-fields">
          <div class="compliance-field">
            <label>
              Impact
              <span class="required">*</span>
              <span class="field-requirements">({{ validationRules.numericRanges.Impact.min }}-{{ validationRules.numericRanges.Impact.max }})</span>
            </label>
            <input 
              type="number" 
              v-model="compliance.Impact"
              class="compliance-input"
              :class="{ 'error': validationErrors.Impact }"
              step="0.1"
              min="1"
              max="10"
              @input="onFieldChange('Impact', $event)"
              @blur="validateField('Impact')"
              required
              :ref="'field_Impact'"
            />
            <div v-if="validationErrors.Impact" class="field-error-message">
              {{ validationErrors.Impact.join(', ') }}
            </div>

          </div>
          
          <div class="compliance-field">
            <label>
              Probability
              <span class="required">*</span>
              <span class="field-requirements">({{ validationRules.numericRanges.Probability.min }}-{{ validationRules.numericRanges.Probability.max }})</span>
            </label>
            <input 
              type="number" 
              v-model="compliance.Probability"
              class="compliance-input"
              :class="{ 'error': validationErrors.Probability }"
              step="0.1"
              min="1"
              max="10"
              @input="onFieldChange('Probability', $event)"
              @blur="validateField('Probability')"
              required
              :ref="'field_Probability'"
            />
            <div v-if="validationErrors.Probability" class="field-error-message">
              {{ validationErrors.Probability.join(', ') }}
            </div>

          </div>
        </div>
        
        <div class="row-fields">
          <div class="compliance-field">
            <label>
              Maturity Level
            </label>
            <select 
              v-model="compliance.MaturityLevel" 
              class="compliance-select"
              title="Current maturity level of this compliance item"
              :ref="'field_MaturityLevel'"
            >
              <option>Initial</option>
              <option>Developing</option>
              <option>Defined</option>
              <option>Managed</option>
              <option>Optimizing</option>
            </select>
            <div v-if="validationErrors.MaturityLevel" class="field-error-message">
              {{ validationErrors.MaturityLevel }}
            </div>
          </div>
          <div class="compliance-field">
            <label>
              Version Type
            </label>
            <select 
              v-model="compliance.versionType" 
              class="compliance-select" 
              required
              title="Type of version change"
              :ref="'field_versionType'"
              @change="handleVersionTypeChange"
            >
              <option value="Major">Major</option>
              <option value="Minor">Minor</option>
            </select>
            <div v-if="validationErrors.versionType" class="field-error-message">
              {{ validationErrors.versionType }}
            </div>
            <div v-if="versionPreview" class="version-preview">
              {{ versionPreview }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- Approval section -->
      <div class="field-group approval-fields">
        <div class="field-group-title">Approval Information</div>
        <!-- Approver and Approval Due Date in the same row -->
        <div class="row-fields">
          <!-- Assign Reviewer -->
          <div class="compliance-field">
            <label>Assign Reviewer <span class="required">*</span></label>
            <select 
              v-model="compliance.reviewer_id" 
              class="compliance-select" 
              :class="{ 'error': validationErrors.reviewer_id }"
              @change="onFieldChange('reviewer_id', $event)"
              @blur="validateField('reviewer_id')"
              required
              title="Person responsible for reviewing this compliance item"
              :ref="'field_reviewer_id'"
            >
              <!-- Debug info -->
              <option v-if="!compliance.reviewer_id" value="" disabled>No reviewer assigned</option>
              <option value="">Select Reviewer</option>
              <option v-for="user in users" :key="user.UserId" :value="user.UserId">
                {{ user.UserName }} {{ user.email ? `(${user.email})` : '' }}
              </option>
            </select>
            <div v-if="validationErrors.reviewer_id" class="field-error-message">
              {{ validationErrors.reviewer_id.join(', ') }}
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="compliance-submit-container">
      <button 
        class="compliance-submit-btn" 
        @click="validateAndSubmit"
        :disabled="loading"
      >
        <span v-if="loading">Saving...</span>
        <span v-else>Save as New Version</span>
      </button>
      <button 
        class="compliance-cancel-btn" 
        @click="cancelEdit"
        :disabled="loading"
      >
        Cancel
      </button>
    </div>
  </div>
</template>

<script>
import { complianceService } from '@/services/api';
import { CompliancePopups } from './utils/popupUtils';
import AccessUtils from '@/utils/accessUtils';

export default {
  name: 'EditCompliance',
  data() {
    return {
      compliance: null,
      users: [],
      loading: false,
      error: null,
      successMessage: null,
      impactError: false,
      probabilityError: false,
      originalComplianceId: null,
      categoryOptions: {
        BusinessUnitsCovered: [],
        RiskType: [],
        RiskCategory: [],
        RiskBusinessImpact: []
      },
      filteredOptions: {
        BusinessUnitsCovered: [],
        RiskType: [],
        RiskCategory: [],
        RiskBusinessImpact: []
      },
      businessUnitSearch: '',
      riskTypeSearch: '',
      riskCategorySearch: '',
      riskBusinessImpactSearch: '',
      activeDropdown: null,
      validationErrors: {},
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
      fieldStates: {}, // Track real-time validation states
      mitigationSteps: [{ description: '' }],
      versionPreview: '', // Store version preview for display
      
      // Display properties for reactive field values
      displayRiskCategory: '',
      displayRiskBusinessImpact: '',
      displayBusinessUnits: '',
    }
  },
  watch: {
    'compliance.versionType': {
      handler(newValue) {
        console.log('Version type changed to:', newValue);
      },
      immediate: true
    },
    
    // Watch for changes in compliance data to update display properties
    'compliance.RiskCategory': {
      handler(newValue) {
        console.log('[watch] RiskCategory changed to:', newValue);
        this.displayRiskCategory = newValue || '';
      },
      immediate: true
    },
    
    'compliance.RiskBusinessImpact': {
      handler(newValue) {
        console.log('[watch] RiskBusinessImpact changed to:', newValue);
        this.displayRiskBusinessImpact = newValue || '';
      },
      immediate: true
    },
    
    'compliance.BusinessUnitsCovered': {
      handler(newValue) {
        console.log('[watch] BusinessUnitsCovered changed to:', newValue);
        this.displayBusinessUnits = newValue || '';
      },
      immediate: true
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
    await this.loadUsers();
    await this.loadComplianceData(complianceId);
    await this.loadCategoryOptions();
    
    // Add click event listener to close dropdowns when clicking outside
    document.addEventListener('click', this.handleClickOutside);
  },
  beforeUnmount() {
    // Remove event listener when component is unmounted
    document.removeEventListener('click', this.handleClickOutside);
  },
  methods: {
    handleVersionTypeChange(event) {
      const selectedType = event.target.value;
      console.log('Version type changed to:', selectedType);
      this.compliance.versionType = selectedType;
      
      // Preview the new version
      this.previewNewVersion();
    },
    
    // Preview the new version based on current selection
    previewNewVersion() {
      if (!this.compliance.versionType) return;
      
      const currentVersion = this.validateVersionFormat(this.compliance.ComplianceVersion);
      const versionParts = currentVersion.split('.');
      const currentMajor = parseInt(versionParts[0]) || 1;
      const currentMinor = parseInt(versionParts[1]) || 0;
      
      let newVersion;
      if (this.compliance.versionType === 'Major') {
        newVersion = `${currentMajor + 1}.0`;
      } else {
        newVersion = `${currentMajor}.${currentMinor + 1}`;
      }
      
      console.log(`Version preview: ${currentVersion} -> ${newVersion} (${this.compliance.versionType})`);
      
      // Store the preview for potential display
      this.versionPreview = `New version will be: ${newVersion}`;
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
      // Always build mitigation JSON from all steps (including empty)
      const mitigationJson = {};
      this.mitigationSteps.forEach((step, idx) => {
        if (step.description && step.description.trim()) {
          mitigationJson[`${idx + 1}`] = step.description.trim();
        }
      });
      this.compliance.mitigation = mitigationJson;
      console.log('[onMitigationStepChange] mitigationSteps:', this.mitigationSteps);
      console.log('[onMitigationStepChange] mitigation JSON:', mitigationJson);
      this.validateField('mitigation');
    },
    async loadComplianceData(complianceId) {
      try {
        this.loading = true;
        const response = await complianceService.getComplianceById(complianceId);
        if (response.data && response.data.success) {
          this.compliance = { ...response.data.data };

          // Normalize RiskCategory from possible alternate keys (case/format insensitive)
          if (!this.compliance.RiskCategory) {
            const canonicalize = key => String(key).replace(/[\s_]/g, '').toLowerCase();
            const target = 'riskcategory';
            const matchKey = Object.keys(this.compliance || {}).find(k => canonicalize(k) === target);
            if (matchKey) {
              this.compliance.RiskCategory = this.compliance[matchKey];
            }
            // Also check a nested ExtractedData shape if present
            if (!this.compliance.RiskCategory && this.compliance.ExtractedData) {
              const nestedKeys = Object.keys(this.compliance.ExtractedData);
              const nestedMatch = nestedKeys.find(k => canonicalize(k) === target);
              if (nestedMatch) {
                this.compliance.RiskCategory = this.compliance.ExtractedData[nestedMatch];
              }
            }
            // Final fallback to common alternates
            if (!this.compliance.RiskCategory) {
              this.compliance.RiskCategory =
                this.compliance.riskCategory ||
                this.compliance.Risk_Category ||
                this.compliance.Riskcategory ||
                '';
            }
          }
          
          // Debug logging for Impact and Probability fields
          console.log('[loadComplianceData] Full compliance data:', this.compliance);
          console.log('[loadComplianceData] Impact field:', this.compliance.Impact);
          console.log('[loadComplianceData] Impact field type:', typeof this.compliance.Impact);
          console.log('[loadComplianceData] Probability field:', this.compliance.Probability);
          console.log('[loadComplianceData] Probability field type:', typeof this.compliance.Probability);
          console.log('[loadComplianceData] RiskCategory field:', this.compliance.RiskCategory);
          console.log('[loadComplianceData] RiskCategory field type:', typeof this.compliance.RiskCategory);
          console.log('[loadComplianceData] RiskBusinessImpact field:', this.compliance.RiskBusinessImpact);
          console.log('[loadComplianceData] BusinessUnitsCovered field:', this.compliance.BusinessUnitsCovered);
          console.log('[loadComplianceData] reviewer_id field:', this.compliance.reviewer_id);
          
          // Convert Impact and Probability to numbers if they are strings
          if (this.compliance.Impact !== null && this.compliance.Impact !== undefined) {
            const impactNum = parseFloat(this.compliance.Impact);
            if (!isNaN(impactNum)) {
              this.compliance.Impact = impactNum;
              console.log('[loadComplianceData] Converted Impact to number:', this.compliance.Impact);
            }
          }
          
          if (this.compliance.Probability !== null && this.compliance.Probability !== undefined) {
            const probabilityNum = parseFloat(this.compliance.Probability);
            if (!isNaN(probabilityNum)) {
              this.compliance.Probability = probabilityNum;
              console.log('[loadComplianceData] Converted Probability to number:', this.compliance.Probability);
            }
          }
          
          // --- Always parse mitigation steps on load ---
          this.mitigationSteps = this.parseMitigationSteps(this.compliance.mitigation);
          console.log('[loadComplianceData] Loaded mitigation:', this.compliance.mitigation);
          console.log('[loadComplianceData] Parsed steps:', this.mitigationSteps);
          
          // Clear version preview initially
          this.versionPreview = '';
        } else {
          this.error = 'Failed to load compliance data';
        }
      } catch (error) {
        console.error('[loadComplianceData] Error:', error);
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
          this.displayBusinessUnits = this.compliance.BusinessUnitsCovered;
        }
        
        // Initialize risk category search
        // For RiskCategory, prefer the saved value; if not present yet, try to infer from available options
        console.log('[initializeSearchFields] Before RiskCategory init - compliance.RiskCategory:', this.compliance.RiskCategory);
        console.log('[initializeSearchFields] Before RiskCategory init - riskCategorySearch:', this.riskCategorySearch);
        
        if (this.compliance.RiskCategory) {
          this.riskCategorySearch = String(this.compliance.RiskCategory);
          this.displayRiskCategory = String(this.compliance.RiskCategory);
          console.log('[initializeSearchFields] Set riskCategorySearch from compliance.RiskCategory:', this.riskCategorySearch);
        } else if (this.categoryOptions.RiskCategory && this.categoryOptions.RiskCategory.length) {
          // Try to find a close match by case-insensitive compare among options
          console.log('[initializeSearchFields] No RiskCategory in compliance, searching in options:', this.categoryOptions.RiskCategory);
          const found = this.categoryOptions.RiskCategory.find(
            o => String(o.value).toLowerCase() === String(this.riskCategorySearch || '').toLowerCase()
          );
          if (found) {
            this.compliance.RiskCategory = found.value;
            this.riskCategorySearch = found.value;
            this.displayRiskCategory = found.value;
            console.log('[initializeSearchFields] Found and set RiskCategory from options:', found.value);
          }
        }
        
        console.log('[initializeSearchFields] After RiskCategory init - compliance.RiskCategory:', this.compliance.RiskCategory);
        console.log('[initializeSearchFields] After RiskCategory init - riskCategorySearch:', this.riskCategorySearch);
        
        // Initialize risk business impact search
        if (this.compliance.RiskBusinessImpact) {
          this.riskBusinessImpactSearch = this.compliance.RiskBusinessImpact;
          this.displayRiskBusinessImpact = this.compliance.RiskBusinessImpact;
        }
        
        // Initialize risk type search
        if (this.compliance.RiskType) {
          this.riskTypeSearch = this.compliance.RiskType;
        }
        
        console.log('[initializeSearchFields] Initialized search fields:', {
          businessUnitSearch: this.businessUnitSearch,
          riskCategorySearch: this.riskCategorySearch,
          riskBusinessImpactSearch: this.riskBusinessImpactSearch,
          riskTypeSearch: this.riskTypeSearch
        });
        console.log('[initializeSearchFields] Display properties:', {
          displayRiskCategory: this.displayRiskCategory,
          displayRiskBusinessImpact: this.displayRiskBusinessImpact,
          displayBusinessUnits: this.displayBusinessUnits
        });
        console.log('[initializeSearchFields] Compliance RiskCategory:', this.compliance.RiskCategory);
        console.log('[initializeSearchFields] Available RiskCategory options:', this.categoryOptions.RiskCategory);
        console.log('[initializeSearchFields] Filtered RiskCategory options:', this.filteredOptions.RiskCategory);
        
        // Also update the filtered options to show the current values
        this.updateFilteredOptions();
        
        // Force a reactivity update to ensure the UI reflects the changes
        this.$forceUpdate();
      }
    },
    
    // Validate and format version string
    validateVersionFormat(version) {
      if (!version) return '1.0';
      
      // Ensure version is in X.Y format
      const parts = version.toString().split('.');
      const major = parseInt(parts[0]) || 1;
      const minor = parseInt(parts[1]) || 0;
      
      return `${major}.${minor}`;
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
        
        if (this.categoryOptions.RiskCategory) {
          const search = (this.riskCategorySearch || this.compliance.RiskCategory || '').toString().toLowerCase();
          this.filteredOptions.RiskCategory = this.categoryOptions.RiskCategory.filter(option => 
            option.value.toLowerCase().includes(search)
          );
        }
        
        if (this.compliance.RiskBusinessImpact && this.categoryOptions.RiskBusinessImpact) {
          this.filteredOptions.RiskBusinessImpact = this.categoryOptions.RiskBusinessImpact.filter(option => 
            option.value.toLowerCase().includes(this.riskBusinessImpactSearch.toLowerCase())
          );
        }
        
        if (this.compliance.RiskType && this.categoryOptions.RiskType) {
          this.filteredOptions.RiskType = this.categoryOptions.RiskType.filter(option => 
            option.value.toLowerCase().includes(this.riskTypeSearch.toLowerCase())
          );
        }
      }
    },
    
    async loadUsers() {
      try {
        this.loading = true;
        const response = await complianceService.getUsers();
        
        if (response.data.success && Array.isArray(response.data.users)) {
          this.users = response.data.users;
          console.log('[loadUsers] Loaded users:', this.users);
        } else {
          console.error('Invalid users data received:', response.data);
          this.error = 'Failed to load approvers';
        }
      } catch (error) {
        // Check if it's an access control error
        if (AccessUtils.handleApiError(error, 'edit compliance')) {
          return;
        }
        
        console.error('Failed to load users:', error);
        this.error = 'Failed to load approvers. Please try again.';
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
      date.setDate(date.getDate() + 7);
      return date.toISOString().split('T')[0]; // Format as YYYY-MM-DD
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
          if (!this.mitigationSteps || this.mitigationSteps.length === 0) {
            result.errors.push('At least one mitigation step is required');
          } else {
            // Check if all steps have descriptions and meet minimum length
            const invalidSteps = this.mitigationSteps.filter(step => {
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
      if (!this.validationErrors) {
        this.validationErrors = {};
      }
      
      if (result.errors.length > 0) {
        this.validationErrors[fieldName] = result.errors;
      } else {
        delete this.validationErrors[fieldName];
      }
      
      return result;
    },

    validateField(fieldName) {
      // Skip validation if compliance data is not yet loaded
      if (!this.compliance) {
      return true;
      }

      const value = this.compliance[fieldName];
      const result = this.validateComplianceField(this.compliance, fieldName, value);
      
      return result.errors.length === 0;
    },

    validateAllFields() {
      let isValid = true;
      let firstErrorField = null;
      
      // Validate all fields
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
        'Probability',
        'reviewer_id'
      ];
      
      // Validate reviewer selection
      if (!this.compliance.reviewer_id || this.compliance.reviewer_id === '') {
        this.validationErrors.reviewer_id = ['Please select a reviewer'];
        isValid = false;
        if (!firstErrorField) {
          firstErrorField = 'reviewer_id';
        }
      }
      
      // Validate all required fields
      requiredFields.forEach(fieldName => {
        if (!this.validateField(fieldName)) {
          isValid = false;
          if (!firstErrorField) {
            firstErrorField = fieldName;
          }
        }
      });
      
      // Validate optional fields that have values
      const optionalFields = ['Identifier', 'Applicability'];
      optionalFields.forEach(fieldName => {
        if (this.compliance[fieldName] && this.compliance[fieldName].trim()) {
          if (!this.validateField(fieldName)) {
            isValid = false;
            if (!firstErrorField) {
              firstErrorField = fieldName;
            }
          }
        }
      });

      // If validation failed, scroll to the first error
      if (firstErrorField) {
        const element = document.querySelector(`[data-field="${firstErrorField}"]`);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }

      return isValid;
    },

    async submitEdit() {
      // Reset messages
      this.error = null;
      this.successMessage = null;

      // Validate all fields before submission
      if (!this.validateAllFields()) {
        this.error = 'Please fill in all required fields with valid information';
        return;
      }

      try {
        this.loading = true;
        const versionType = this.compliance.versionType;
        if (!versionType || !['Major', 'Minor'].includes(versionType)) {
          this.error = 'Please select a valid version type (Major or Minor)';
          return;
        }
        if (!this.compliance.ComplianceVersion) {
          this.compliance.ComplianceVersion = '1.0';
        }
        const currentVersion = this.validateVersionFormat(this.compliance.ComplianceVersion);
        let newVersion;
        const versionParts = currentVersion.split('.');
        const currentMajor = parseInt(versionParts[0]) || 1;
        const currentMinor = parseInt(versionParts[1]) || 0;
        if (versionType === 'Major') {
          newVersion = `${currentMajor + 1}.0`;
        } else {
          newVersion = `${currentMajor}.${currentMinor + 1}`;
        }
        const versionPattern = /^\d+\.\d+$/;
        if (!versionPattern.test(newVersion)) {
          this.error = 'Invalid version format. Version must be in X.Y format (e.g., 2.4, 3.0)';
          return;
        }
        let mitigationData = this.compliance.mitigation || {};
        if (!mitigationData || Object.keys(mitigationData).length === 0) {
          if (this.compliance.IsRisk && this.mitigationSteps && this.mitigationSteps.length > 0) {
            mitigationData = {};
            this.mitigationSteps.forEach((step, index) => {
              if (step.description && step.description.trim()) {
                mitigationData[`${index + 1}`] = step.description.trim();
              }
            });
          }
        }
        // --- Set correct UserId and ReviewerId ---
        const userId = this.getCurrentUserId();
        const reviewerId = this.users.find(u => u.UserId === this.compliance.reviewer_id)?.UserId || this.compliance.reviewer_id;
        // Prepare submission data
        const editData = {
          ...this.compliance,
          ComplianceVersion: newVersion,
          Status: 'Under Review',
          ActiveInactive: 'Active',
          PreviousComplianceVersionId: this.originalComplianceId,
          mitigation: mitigationData,
          UserId: userId, // Set correct user id
          ReviewerId: reviewerId, // Set correct reviewer id
          versionType: this.compliance.versionType
        };
        // Remove any old/hardcoded user_id/reviewer_id fields
        delete editData.user_id;
        delete editData.reviewer_id;
        // Use the complianceService to save the edit
        const response = await complianceService.updateCompliance(this.originalComplianceId, editData);
        if (response.data && response.data.success) {
          CompliancePopups.complianceUpdated({
            ComplianceId: response.data.compliance_id || this.originalComplianceId,
            ComplianceVersion: newVersion,
            ComplianceItemDescription: this.compliance.ComplianceItemDescription
          });
          setTimeout(() => {
            this.$router.push('/compliance/tailoring');
          }, 1500);
        } else {
          this.error = response.data.message || 'Failed to update compliance';
        }
      } catch (error) {
        console.error('Error updating compliance:', error);
        this.error = 'Failed to update compliance. Please try again.';
      } finally {
        this.loading = false;
      }
    },
    goBack() {
      // Navigate back to the previous page
      this.$router.go(-1);
    },
    cancelEdit() {
      // Show simple confirmation before canceling
      if (confirm('Are you sure you want to cancel editing? Any unsaved changes will be lost.')) {
        this.$router.push('/compliance/tailoring');
      }
    },
    async loadCategoryOptions() {
      try {
        this.loading = true;
        
        // Load business units
        const buResponse = await complianceService.getCategoryBusinessUnits('BusinessUnitsCovered');
        console.log('BusinessUnitsCovered API response:', buResponse);
        console.log('BusinessUnitsCovered response data structure:', {
          success: buResponse.data.success,
          hasData: !!buResponse.data.data,
          dataLength: buResponse.data.data?.length,
          dataType: typeof buResponse.data.data,
          isArray: Array.isArray(buResponse.data.data),
          dataContent: buResponse.data.data
        });
        
        if (buResponse.data.success && buResponse.data.data && Array.isArray(buResponse.data.data) && buResponse.data.data.length > 0) {
          // Validate that each item has the expected structure
          const validData = buResponse.data.data.filter(item => item && typeof item === 'object' && item.value && item.value.trim());
          console.log('Valid BusinessUnitsCovered data:', validData);
          
          if (validData.length > 0) {
            this.categoryOptions.BusinessUnitsCovered = validData;
            this.filteredOptions.BusinessUnitsCovered = [...validData];
            console.log('Loaded BusinessUnitsCovered options:', this.categoryOptions.BusinessUnitsCovered);
          } else {
            throw new Error('No valid BusinessUnitsCovered data found in API response');
          }
        } else {
          console.log('No BusinessUnitsCovered data found, attempting to initialize default categories...');
          try {
            // Try to initialize default categories
            const initResponse = await complianceService.initializeDefaultCategories();
            console.log('Initialize categories response:', initResponse);
            
            if (initResponse.data.success) {
              // Retry loading business units after initialization
              const retryResponse = await complianceService.getCategoryBusinessUnits('BusinessUnitsCovered');
              console.log('Retry BusinessUnitsCovered API response:', retryResponse);
              if (retryResponse.data.success && retryResponse.data.data) {
                this.categoryOptions.BusinessUnitsCovered = retryResponse.data.data;
                this.filteredOptions.BusinessUnitsCovered = [...retryResponse.data.data];
                console.log('Loaded BusinessUnitsCovered options after initialization:', this.categoryOptions.BusinessUnitsCovered);
              } else {
                throw new Error('Failed to load business units after initialization');
              }
            } else {
              throw new Error('Failed to initialize default categories');
            }
          } catch (initError) {
            console.error('Failed to initialize categories:', initError);
            // Fallback to default values
            this.categoryOptions.BusinessUnitsCovered = [
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
            this.filteredOptions.BusinessUnitsCovered = [...this.categoryOptions.BusinessUnitsCovered];
            console.log('Using fallback BusinessUnitsCovered options:', this.categoryOptions.BusinessUnitsCovered);
          }
        }
        
        // Load risk types
        const rtResponse = await complianceService.getCategoryBusinessUnits('RiskType');
        console.log('RiskType API response:', rtResponse);
        console.log('RiskType response data structure:', {
          success: rtResponse.data.success,
          hasData: !!rtResponse.data.data,
          dataLength: rtResponse.data.data?.length,
          dataType: typeof rtResponse.data.data,
          isArray: Array.isArray(rtResponse.data.data),
          dataContent: rtResponse.data.data
        });
        
        if (rtResponse.data.success && rtResponse.data.data && Array.isArray(rtResponse.data.data) && rtResponse.data.data.length > 0) {
          // Validate that each item has the expected structure
          const validData = rtResponse.data.data.filter(item => item && typeof item === 'object' && item.value && item.value.trim());
          console.log('Valid RiskType data:', validData);
          
          if (validData.length > 0) {
            this.categoryOptions.RiskType = validData;
            this.filteredOptions.RiskType = [...validData];
            console.log('Loaded RiskType options:', this.categoryOptions.RiskType);
          } else {
            throw new Error('No valid RiskType data found in API response');
          }
        } else {
          console.log('No RiskType data found, attempting to initialize default categories...');
          try {
            // Try to initialize default categories
            const initResponse = await complianceService.initializeDefaultCategories();
            console.log('Initialize categories response:', initResponse);
            
            if (initResponse.data.success) {
              // Retry loading risk types after initialization
              const retryResponse = await complianceService.getCategoryBusinessUnits('RiskType');
              console.log('Retry RiskType API response:', retryResponse);
              if (retryResponse.data.success && retryResponse.data.data) {
                this.categoryOptions.RiskType = retryResponse.data.data;
                this.filteredOptions.RiskType = [...retryResponse.data.data];
                console.log('Loaded RiskType options after initialization:', this.categoryOptions.RiskType);
              } else {
                throw new Error('Failed to load risk types after initialization');
              }
            } else {
              throw new Error('Failed to initialize default categories');
            }
          } catch (initError) {
            console.error('Failed to initialize categories:', initError);
            // Fallback to default values
            this.categoryOptions.RiskType = [
              { id: 1, value: 'Operational Risk' },
              { id: 2, value: 'Financial Risk' },
              { id: 3, value: 'Strategic Risk' },
              { id: 4, value: 'Compliance Risk' },
              { id: 5, value: 'Reputational Risk' },
              { id: 6, value: 'Technology Risk' },
              { id: 7, value: 'Market Risk' },
              { id: 8, value: 'Credit Risk' },
              { id: 9, value: 'Legal Risk' },
              { id: 10, value: 'Environmental Risk' }
            ];
            this.filteredOptions.RiskType = [...this.categoryOptions.RiskType];
            console.log('Using fallback RiskType options:', this.categoryOptions.RiskType);
          }
        }
        
        // Load risk categories
        const rcResponse = await complianceService.getCategoryBusinessUnits('RiskCategory');
        console.log('RiskCategory API response:', rcResponse);
        console.log('RiskCategory response data structure:', {
          success: rcResponse.data.success,
          hasData: !!rcResponse.data.data,
          dataLength: rcResponse.data.data?.length,
          dataType: typeof rcResponse.data.data,
          isArray: Array.isArray(rcResponse.data.data),
          dataContent: rcResponse.data.data
        });
        
        if (rcResponse.data.success && rcResponse.data.data && Array.isArray(rcResponse.data.data) && rcResponse.data.data.length > 0) {
          // Validate that each item has the expected structure
          const validData = rcResponse.data.data.filter(item => item && typeof item === 'object' && item.value && item.value.trim());
          console.log('Valid RiskCategory data:', validData);
          
          if (validData.length > 0) {
            this.categoryOptions.RiskCategory = validData;
            this.filteredOptions.RiskCategory = [...validData];
            console.log('Loaded RiskCategory options:', this.categoryOptions.RiskCategory);
          } else {
            throw new Error('No valid RiskCategory data found in API response');
          }
        } else {
          console.log('No RiskCategory data found, attempting to initialize default categories...');
          try {
            // Try to initialize default categories
            const initResponse = await complianceService.initializeDefaultCategories();
            console.log('Initialize categories response:', initResponse);
            
            if (initResponse.data.success) {
              // Retry loading risk categories after initialization
              const retryResponse = await complianceService.getCategoryBusinessUnits('RiskCategory');
              console.log('Retry RiskCategory API response:', retryResponse);
              if (retryResponse.data.success && retryResponse.data.data) {
                this.categoryOptions.RiskCategory = retryResponse.data.data;
                this.filteredOptions.RiskCategory = [...retryResponse.data.data];
                console.log('Loaded RiskCategory options after initialization:', this.categoryOptions.RiskCategory);
              } else {
                throw new Error('Failed to load categories after initialization');
              }
            } else {
              throw new Error('Failed to initialize default categories');
            }
          } catch (initError) {
            console.error('Failed to initialize categories:', initError);
            // Fallback to default values
            this.categoryOptions.RiskCategory = [
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
            this.filteredOptions.RiskCategory = [...this.categoryOptions.RiskCategory];
            console.log('Using fallback RiskCategory options:', this.categoryOptions.RiskCategory);
          }
        }
        
        // Load risk business impacts
        console.log('Loading RiskBusinessImpact data...');
        const rbiResponse = await complianceService.getCategoryBusinessUnits('RiskBusinessImpact');
        console.log('RiskBusinessImpact response:', rbiResponse);
        console.log('RiskBusinessImpact response data structure:', {
          success: rbiResponse.data.success,
          hasData: !!rbiResponse.data.data,
          dataLength: rbiResponse.data.data?.length,
          dataType: typeof rbiResponse.data.data,
          isArray: Array.isArray(rbiResponse.data.data),
          dataContent: rbiResponse.data.data
        });
        
        if (rbiResponse.data.success && rbiResponse.data.data && Array.isArray(rbiResponse.data.data) && rbiResponse.data.data.length > 0) {
          // Validate that each item has the expected structure
          const validData = rbiResponse.data.data.filter(item => item && typeof item === 'object' && item.value && item.value.trim());
          console.log('Valid RiskBusinessImpact data:', validData);
          
          if (validData.length > 0) {
            this.categoryOptions.RiskBusinessImpact = validData;
            this.filteredOptions.RiskBusinessImpact = [...validData];
            console.log('Loaded RiskBusinessImpact options:', this.categoryOptions.RiskBusinessImpact);
          } else {
            throw new Error('No valid RiskBusinessImpact data found in API response');
          }
        } else {
          console.log('No RiskBusinessImpact data found, attempting to initialize default categories...');
          try {
            // Try to initialize default categories
            const initResponse = await complianceService.initializeDefaultCategories();
            console.log('Initialize categories response:', initResponse);
            
            if (initResponse.data.success) {
              // Retry loading risk business impacts after initialization
              const retryResponse = await complianceService.getCategoryBusinessUnits('RiskBusinessImpact');
              console.log('Retry RiskBusinessImpact API response:', retryResponse);
              if (retryResponse.data.success && retryResponse.data.data) {
                this.categoryOptions.RiskBusinessImpact = retryResponse.data.data;
                this.filteredOptions.RiskBusinessImpact = [...retryResponse.data.data];
                console.log('Loaded RiskBusinessImpact options after initialization:', this.categoryOptions.RiskBusinessImpact);
              } else {
                throw new Error('Failed to load business impacts after initialization');
              }
            } else {
              throw new Error('Failed to initialize default categories');
            }
          } catch (initError) {
            console.error('Failed to initialize categories:', initError);
            // Fallback to default values
            this.categoryOptions.RiskBusinessImpact = [
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
            this.filteredOptions.RiskBusinessImpact = [...this.categoryOptions.RiskBusinessImpact];
            console.log('Using fallback RiskBusinessImpact options:', this.categoryOptions.RiskBusinessImpact);
          }
        }
        
        console.log('All category options loaded successfully');
        
        // Check if any category options are empty and use fallbacks if needed
        this.ensureCategoryOptionsArePopulated();
        
        // Re-initialize search fields after loading category options
        // This ensures search fields are properly set even if compliance data was loaded first
        this.initializeSearchFields();
      } catch (error) {
        console.error('Failed to load category options:', error);
        this.error = 'Failed to load dropdown options. Some features may be limited.';
      } finally {
        this.loading = false;
      }
    },
    
    // Ensure all category options are populated with fallback values if needed
    ensureCategoryOptionsArePopulated() {
      console.log('Ensuring category options are populated...');
      
      // Check BusinessUnitsCovered
      if (!this.categoryOptions.BusinessUnitsCovered || this.categoryOptions.BusinessUnitsCovered.length === 0) {
        console.log('BusinessUnitsCovered is empty, using fallback');
        this.useFallbackBusinessUnits();
      }
      
      // Check RiskType
      if (!this.categoryOptions.RiskType || this.categoryOptions.RiskType.length === 0) {
        console.log('RiskType is empty, using fallback');
        this.useFallbackRiskTypes();
      }
      
      // Check RiskCategory
      if (!this.categoryOptions.RiskCategory || this.categoryOptions.RiskCategory.length === 0) {
        console.log('RiskCategory is empty, using fallback');
        this.useFallbackRiskCategories();
      }
      
      // Check RiskBusinessImpact
      if (!this.categoryOptions.RiskBusinessImpact || this.categoryOptions.RiskBusinessImpact.length === 0) {
        console.log('RiskBusinessImpact is empty, using fallback');
        this.useFallbackRiskBusinessImpacts();
      }
      
      console.log('Category options check complete:', {
        BusinessUnitsCovered: this.categoryOptions.BusinessUnitsCovered?.length || 0,
        RiskType: this.categoryOptions.RiskType?.length || 0,
        RiskCategory: this.categoryOptions.RiskCategory?.length || 0,
        RiskBusinessImpact: this.categoryOptions.RiskBusinessImpact?.length || 0
      });
    },
    
    // Fallback methods for when API data is invalid or empty
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
    
          useFallbackRiskTypes() {
        const fallbackData = [
          { id: 1, value: 'Operational Risk' },
          { id: 2, value: 'Financial Risk' },
          { id: 3, value: 'Strategic Risk' },
          { id: 4, value: 'Compliance Risk' },
          { id: 5, value: 'Reputational Risk' },
          { id: 6, value: 'Technology Risk' },
          { id: 7, value: 'Market Risk' },
          { id: 8, value: 'Credit Risk' },
          { id: 9, value: 'Legal Risk' },
          { id: 10, value: 'Environmental Risk' }
        ];
        this.categoryOptions.RiskType = fallbackData;
        this.filteredOptions.RiskType = [...fallbackData];
        console.log('Using fallback RiskType options:', fallbackData);
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
      
      // Handle Risk Category input
      onRiskCategoryInput(event) {
        // When user starts typing, clear the current selection and show search
        this.compliance.RiskCategory = null;
        this.riskCategorySearch = event.target.value;
        this.displayRiskCategory = event.target.value;
        this.filterOptions('RiskCategory');
        this.showDropdown('RiskCategory');
      },
      
      // Clear Risk Category selection
      clearRiskCategory() {
        this.compliance.RiskCategory = null;
        this.riskCategorySearch = '';
        this.displayRiskCategory = '';
        this.filteredOptions.RiskCategory = [...this.categoryOptions.RiskCategory];
        this.$forceUpdate();
      },
      
      // Handle Risk Business Impact input
      onRiskBusinessImpactInput(event) {
        // When user starts typing, clear the current selection and show search
        this.compliance.RiskBusinessImpact = null;
        this.riskBusinessImpactSearch = event.target.value;
        this.displayRiskBusinessImpact = event.target.value;
        this.filterOptions('RiskBusinessImpact');
        this.showDropdown('RiskBusinessImpact');
      },
      
      // Clear Risk Business Impact selection
      clearRiskBusinessImpact() {
        this.compliance.RiskBusinessImpact = null;
        this.riskBusinessImpactSearch = '';
        this.displayRiskBusinessImpact = '';
        this.filteredOptions.RiskBusinessImpact = [...this.categoryOptions.RiskBusinessImpact];
        this.$forceUpdate();
      },
      
      // Handle Business Unit input
      onBusinessUnitInput(event) {
        // When user starts typing, clear the current selection and show search
        this.compliance.BusinessUnitsCovered = null;
        this.businessUnitSearch = event.target.value;
        this.displayBusinessUnits = event.target.value;
        this.filterOptions('BusinessUnitsCovered');
        this.showDropdown('BusinessUnitsCovered');
      },
      
      // Clear Business Unit selection
      clearBusinessUnit() {
        this.compliance.BusinessUnitsCovered = null;
        this.businessUnitSearch = '';
        this.displayBusinessUnits = '';
        this.filteredOptions.BusinessUnitsCovered = [...this.categoryOptions.BusinessUnitsCovered];
        this.$forceUpdate();
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
            RiskType: [],
            RiskCategory: [],
            RiskBusinessImpact: []
          };
          this.filteredOptions = {
            BusinessUnitsCovered: [],
            RiskType: [],
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
      console.log(`Showing dropdown for field: ${field}`);
      console.log(`Available options for ${field}:`, this.categoryOptions[field]);
      
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
        case 'RiskType':
          searchTerm = this.riskTypeSearch || '';
          break;
        case 'RiskCategory':
          searchTerm = this.riskCategorySearch || '';
          break;
        case 'RiskBusinessImpact':
          searchTerm = this.riskBusinessImpactSearch || '';
          break;
      }
      
      console.log(`Filtering ${field} options:`, {
        searchTerm,
        availableOptions: this.categoryOptions[field],
        searchField: field
      });
      
      // Filter options based on search term (case-insensitive)
      const lowerSearchTerm = searchTerm.toLowerCase();
      this.filteredOptions[field] = this.categoryOptions[field].filter(option => 
        option.value.toLowerCase().includes(lowerSearchTerm)
      );
      
      console.log(`Filtered ${field} options:`, this.filteredOptions[field]);
    },
    
    // Select an option from the dropdown
    selectOption(field, value) {
      // Update the compliance item with the selected value
      this.compliance[field] = value;
      
      // Update the search field to show the selected value
      switch (field) {
        case 'BusinessUnitsCovered':
          this.businessUnitSearch = value;
          this.displayBusinessUnits = value;
          break;
        case 'RiskType':
          this.riskTypeSearch = value;
          break;
        case 'RiskCategory':
          this.riskCategorySearch = value;
          this.displayRiskCategory = value;
          break;
        case 'RiskBusinessImpact':
          this.riskBusinessImpactSearch = value;
          this.displayRiskBusinessImpact = value;
          break;
      }
      
      // Close the dropdown
      this.activeDropdown = null;
    },
    
    // Add a new option to the category options
    async addNewOption(field, value) {
      if (!value || !value.trim()) return;
      
      try {
        const response = await complianceService.addCategoryBusinessUnit({
          source: field,
          value: value.trim()
        });
        
        if (response.data.success) {
          // Add the new option to the category options
          const newOption = response.data.data;
          this.categoryOptions[field].push({
            id: newOption.id,
            value: newOption.value
          });
          
          // Select the new option
          this.selectOption(field, value);
          
          // Show success message
          this.successMessage = `Added new ${field} option: ${value}`;
          
          // Refresh options to ensure sync with backend
          await this.loadCategoryOptions();
        } else {
          throw new Error(response.data.error || 'Failed to add new option');
        }
      } catch (error) {
        console.error(`Failed to add new ${field} option:`, error);
        this.error = `Failed to add new option: ${error.message || error}`;
      }
    },

    validateFieldRealTime(fieldName) {
      // Skip validation if compliance data is not yet loaded
      if (!this.compliance) {
        return true;
      }

      const value = this.compliance[fieldName];
      const result = this.validateComplianceField(this.compliance, fieldName, value);

      // Initialize field state if not exists
      if (!this.fieldStates[fieldName]) {
        this.fieldStates[fieldName] = {
          dirty: false,
          valid: false,
          warning: false
        };
      }
      
      this.fieldStates[fieldName].dirty = true;
      this.fieldStates[fieldName].valid = result.errors.length === 0;
        this.fieldStates[fieldName].warning = false;
      
      return result.errors.length === 0;
    },

    // Real-time validation on input
    onFieldChange(fieldName, event) {
      let value;
      
      // Handle different input types
      if (fieldName === 'IsRisk') {
        value = event.target.checked;
        this.compliance[fieldName] = value;
      } else {
        value = event.target.value;
        // Update the field value directly without sanitization during typing
        this.compliance[fieldName] = value;
        
        // Only validate for error display, don't replace the value
        this.validateComplianceField(this.compliance, fieldName, value);
      }
      
      // Force reactivity update
      this.$forceUpdate();
    },

    isFieldValid(fieldName) {
      return this.fieldStates[fieldName]?.valid || false;
    },

    showWarning(fieldName) {
      return this.fieldStates[fieldName]?.warning || false;
    },

    getValidationProgress(fieldName) {
      // Skip if compliance data is not yet loaded
      if (!this.compliance) {
        return 0;
      }

      const value = this.compliance[fieldName];
      const rules = this.validationRules[fieldName];
      
      if (!value || !rules || !Array.isArray(rules)) return 0;
      
      // For numeric fields (Impact, Probability)
      if (['Impact', 'Probability'].includes(fieldName)) {
        const numValue = parseFloat(value);
        if (!isNaN(numValue)) {
          return ((numValue - 1) / 9) * 100; // Scale 1-10 to 0-100%
        }
        return 0;
      }
      
      // For select fields
      if (['Criticality', 'MaturityLevel', 'MandatoryOptional', 'ManualAutomatic'].includes(fieldName)) {
        return value ? 100 : 0;
      }
      
      // For text fields with minLength
      const minLengthRule = rules.find(r => r.minLength);
      if (minLengthRule) {
        const progress = (value.length / minLengthRule.minLength) * 100;
        return Math.min(progress, 100);
      }
      
      return value ? 100 : 0;
    },

    getValidationColor(fieldName) {
      const progress = this.getValidationProgress(fieldName);
      if (progress < 50) return '#dc2626'; // Red
      if (progress < 100) return '#f59e0b'; // Yellow
      return '#10b981'; // Green
    },

    getValidationMessage(fieldName) {
      // Skip if compliance data is not yet loaded
      if (!this.compliance) {
        return '';
      }

      const value = this.compliance[fieldName];
      const rules = this.validationRules[fieldName];
      
      if (!rules || !Array.isArray(rules)) return '';
      
      if (!value) {
        const requiredRule = rules.find(r => r.required);
        return requiredRule ? requiredRule.message : '';
      }
      
      if (this.validationErrors[fieldName]) return this.validationErrors[fieldName];
      
      const minLengthRule = rules.find(r => r.minLength);
      if (minLengthRule && value.length < minLengthRule.minLength) {
        const remaining = minLengthRule.minLength - value.length;
        return `Need ${remaining} more character${remaining === 1 ? '' : 's'}`;
      }
      
      const maxLengthRule = rules.find(r => r.maxLength);
      if (maxLengthRule && value.length > maxLengthRule.maxLength) {
        const excess = value.length - maxLengthRule.maxLength;
        return `Exceeds maximum length by ${excess} character${excess === 1 ? '' : 's'}`;
      }
      
      const numericRule = rules.find(r => r.min !== undefined || r.max !== undefined);
      if (numericRule) {
        const numValue = parseFloat(value);
        if (isNaN(numValue)) {
          return 'Please enter a valid number';
        }
        if (numValue < numericRule.min) {
          return `Minimum value is ${numericRule.min}`;
        }
        if (numValue > numericRule.max) {
          return `Maximum value is ${numericRule.max}`;
        }
      }
      
      if (this.isFieldValid(fieldName)) return 'Looks good!';
      
      return '';
    },

    scrollToError() {
      // Get all fields with errors
      const errorFields = Object.keys(this.validationErrors);
      if (errorFields.length > 0) {
        // Get the first field with error
        const firstErrorField = errorFields[0];
        const errorElement = this.$refs[`field_${firstErrorField}`];
        
        if (errorElement) {
          // Scroll to the element with smooth behavior
          errorElement.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
          });
          // Focus the field
          errorElement.focus();
        }
      }
    },

    validateAndSubmit() {
      this.validationErrors = {};
      let isValid = true;

      // Validate all fields
      if (!this.validateAllFields()) {
          isValid = false;
        }

      if (!isValid) {
        // Scroll to the first error
        this.$nextTick(() => {
          this.scrollToError();
        });
        return;
      }

      // If valid, proceed with submission
      this.submitForm();
    },

    submitForm() {
      // Always build mitigation JSON from all steps (including empty)
      const mitigationJson = {};
      this.mitigationSteps.forEach((step, idx) => {
        if (step.description && step.description.trim()) {
          mitigationJson[`${idx + 1}`] = step.description.trim();
        }
      });
      this.compliance.mitigation = mitigationJson;
      console.log('[submitForm] mitigationSteps:', this.mitigationSteps);
      console.log('[submitForm] mitigation JSON:', mitigationJson);
      this.submitEdit();
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
    // Utility to get current user ID from session/localStorage
    getCurrentUserId() {
      // Only return the logged-in user id, do not fallback to '1'.
      let userId = localStorage.getItem('user_id');
      if (userId) return userId;
      userId = sessionStorage.getItem('userId');
      if (userId) return userId;
      const userObj = localStorage.getItem('user') || sessionStorage.getItem('user');
      if (userObj) {
        try {
          const parsed = JSON.parse(userObj);
          return parsed.UserId || parsed.user_id || parsed.id;
        } catch (e) {
          // intentionally empty
        }
      }
      return null;
    },
  }
}
</script>

<style scoped>
@import './CreateCompliance.css';

.compliance-cancel-btn {
  width: auto;
  min-width: 120px;
  padding: 0.875rem 1.75rem;
  background-color: #f1f5f9;
  color: #64748b;
  font-weight: 600;
  font-size: 0.9rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin: 2rem 0.5rem;
}

.compliance-cancel-btn:hover {
  background-color: #e2e8f0;
  color: #475569;
}

.compliance-submit-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  margin-top: 2rem;
}

.required {
  color: #dc2626;
  margin-left: 2px;
  cursor: help;
  position: relative;
}

.required:hover::after {
  content: 'This field is required';
  position: absolute;
  top: -30px;
  left: 50%;
  transform: translateX(-50%);
  background-color: #1f2937;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  white-space: nowrap;
  z-index: 10;
}

.error {
  border-color: #dc2626 !important;
}

.error-message {
  color: #dc2626;
  font-size: 0.875rem;
  margin-top: 0.25rem;
  display: block;
}

.compliance-input.error,
.compliance-select.error {
  border-color: #dc2626;
  background-color: #fef2f2;
}

.compliance-input.error:focus,
.compliance-select.error:focus {
  border-color: #dc2626;
  box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.2);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.validation-indicator {
  position: absolute;
  right: 10px;
  display: flex;
  align-items: center;
}

.valid-icon {
  color: #10b981;
  font-weight: bold;
}


.field-requirements {
  font-size: 0.75rem;
  color: #6b7280;
  margin-left: 0.5rem;
  font-style: italic;
}

.validation-feedback {
  margin-top: 0.25rem;
}

.validation-progress {
  height: 2px;
  background-color: #e5e7eb;
  border-radius: 2px;
  margin-bottom: 0.25rem;
}

.progress-bar {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease, background-color 0.3s ease;
}

.validation-message {
  font-size: 0.75rem;
  transition: color 0.3s ease;
}

.validation-message.warning {
  color: #f59e0b;
}

.validation-message.error {
  color: #dc2626;
}

.validation-message.success {
  color: #10b981;
}
.step-numberr {
  font-weight: 500 !important;
  color: #666 !important;
}
.step-numberr {
  color: #000 !important;
  background: #fff !important;
  border: none !important;
  font-weight: 700 !important;
  font-size: 0.95rem !important;
  padding: 0 !important;
  margin: 0 !important;
  box-shadow: none !important;
  display: inline-block !important;
}

.char-count {
  position: absolute;
  right: 10px;
  bottom: 10px;
  font-size: 0.75rem;
  color: #6b7280;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
}

.char-count.error {
  color: #dc2626;
  font-weight: 500;
}

.char-count.warning {
  color: #f59e0b;
  font-weight: 500;
}

.compliance-input.warning {
  border-color: #f59e0b;
  background-color: #fffbeb;
}

.compliance-input.valid {
  border-color: #10b981;
  background-color: #f0fdf4;
}

.compliance-input.warning:focus {
  border-color: #f59e0b;
  box-shadow: 0 0 0 1px #f59e0b;
}

.compliance-input.valid:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 1px #10b981;
}

.version-preview {
  font-size: 0.75rem;
  color: #059669;
  margin-top: 0.25rem;
  font-weight: 500;
  background-color: #ecfdf5;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  border-left: 3px solid #10b981;
}

.searchable-dropdown {
  position: relative;
  width: 100%;
}

.searchable-dropdown input {
  padding-right: 2.5rem; /* Make room for clear button */
}

.searchable-dropdown .validation-indicator {
  right: 30px; /* Adjust for dropdown arrow */
}

.clear-selection-btn {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.25rem;
  transition: all 0.2s ease;
  z-index: 10;
}

.clear-selection-btn:hover {
  color: #ef4444;
  background-color: #fef2f2;
}

.clear-selection-btn i {
  font-size: 0.75rem;
}

/* Add styles for select elements */
.compliance-select {
  padding-right: 30px; /* Make room for validation indicator */
}

.compliance-select.valid {
  background-color: #f0fdf4;
  border-color: #10b981;
}

.compliance-select.error {
  background-color: #fef2f2;
  border-color: #dc2626;
}

/* Numeric input specific styles */
input[type="number"].compliance-input {
  text-align: right;
  padding-right: 30px;
}

/* Progress bar variations */
.validation-progress .progress-bar.numeric {
  transition: width 0.2s ease;
}

.validation-progress .progress-bar.select {
  transition: width 0s;
}

.validation-summary {
  margin: 1rem 0;
  padding: 1rem;
  border-radius: 0.5rem;
  background-color: #fee2e2;
  color: #dc2626;
}

.validation-summary ul {
  margin: 0.5rem 0 0 1.5rem;
  padding: 0;
}

.validation-summary li {
  margin-bottom: 0.25rem;
}

/* Update numeric input styles */
input[type="number"] {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  transition: border-color 0.2s ease;
}

input[type="number"]:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

input[type="number"].error {
  border-color: #dc2626;
}

/* Remove arrows from number inputs */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

input[type="number"] {
  -moz-appearance: textfield;
}

.validation-message.error {
  color: #dc2626;
  font-size: 0.75rem;
  margin-top: 0.25rem;
}

.field-requirements {
  font-size: 0.75rem;
  color: #6b7280;
  margin-left: 0.5rem;
}

.field-error-message {
  color: #dc2626;
  font-size: 0.75rem;
  margin-top: 0.25rem;
  padding: 0.25rem 0;
}

.compliance-input.error {
  border-color: #dc2626;
  background-color: #fff5f5;
}

.compliance-input.error:focus {
  border-color: #dc2626;
  box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.2);
}

.input-wrapper {
  position: relative;
  width: 100%;
}

/* Highlight animation for error fields */
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

/* Make error messages more visible */
.field-error-message {
  background-color: #fee2e2;
  border-radius: 4px;
  padding: 0.5rem;
  margin-top: 0.25rem;
  font-weight: 500;
}

/* Add visual indicator for required fields */
.required {
  color: #dc2626;
  margin-left: 0.25rem;
}

/* Improve field requirements visibility */
.field-requirements {
  color: #6b7280;
  font-size: 0.75rem;
  margin-left: 0.5rem;
}

/* Add transition for smooth error state changes */
.compliance-input {
  transition: all 0.3s ease;
}

/* Header layout styles */
.compliance-header {
  margin-bottom: 2rem;
  background: transparent;
  border-bottom: none;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  width: 100%;
  background: transparent;
  border-bottom: none;
}

.header-text {
  flex: 1;
  background: transparent;
  border-bottom: none;
}

.header-text h2 {
  margin: 0 0 0.5rem 0;
  color: #1f2937;
  font-size: 1.875rem;
  font-weight: 700;
}

.header-text p {
  margin: 0;
  color: #6b7280;
  font-size: 1rem;
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

/* Back button styles */
.back-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  background-color: white;
  color: #39b669;
  border: 1px solid #c5c7ca;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  white-space: nowrap;
  margin-left: -20px;
  margin-bottom: 2px;
}

.back-button:hover {
  background-color: #e2e8f0;
  color: #1e293b;
  border-color: #94a3b8;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.back-button:active {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.back-button i {
  font-size: 0.875rem;
}

/* Responsive design for header */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
  }
  
  .back-button {
    align-self: flex-end;
    margin-left: 0;
  }
  
  .header-text h2 {
    font-size: 1.5rem;
  }
}
</style> 