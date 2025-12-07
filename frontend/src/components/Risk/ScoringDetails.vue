<template>
  <div class="risk-scoring-container">
    <!-- Add PopupModal component -->
    <PopupModal />
    
    <div class="risk-scoring-page-header">
      <button type="button" class="risk-scoring-back-button" @click="goBack">
        <i class="fas fa-arrow-left"></i>
      </button>
      <h1>Scoring Details</h1>
    </div>
    
    <div v-if="loading" class="risk-scoring-loading">
      <div class="risk-scoring-spinner"></div>
      <span>Loading risk instance data...</span>
    </div>
    
    <div v-else-if="error" class="risk-scoring-error-message" v-html="sanitize.sanitizeHtml(error)"></div>
    
    <div v-else-if="!riskInstance" class="risk-scoring-no-data">
      <p>No risk instance found.</p>
    </div>
    
    <div v-else class="risk-scoring-details">
      <div class="risk-scoring-detail-header">
        <h2>Risk Instance #{{ sanitize.escapeHtml(editedRiskInstance.RiskInstanceId) }}</h2>
        <div v-if="isCreateAction" class="risk-scoring-action-header-buttons">
          <button class="risk-scoring-map-btn" @click="mapScoringRisk">MAP SCORING RISK</button>
        </div>
      </div>
      
      <form @submit.prevent="submitForm" class="risk-scoring-detail-grid-container">
        <!-- Add validation error summary at the top -->
        <div v-if="activeValidationErrors.length > 0" class="risk-scoring-validation-summary">
          <h4>Please fix the following errors:</h4>
          <ul>
            <li v-for="item in activeValidationErrors" :key="item.field">
              {{ sanitize.escapeHtml(item.error) }}
            </li>
          </ul>
        </div>
        
        <!-- First section - Basic Risk Information -->
        <div class="risk-scoring-section-container">
          <h3 class="risk-scoring-section-title">Basic Risk Information</h3>
          <div class="risk-scoring-detail-row">
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Risk Instance Id</div>
              <div class="risk-scoring-detail-value">{{ sanitize.escapeHtml(editedRiskInstance.RiskInstanceId) }}</div>
              <div class="risk-scoring-helper-text">Unique identifier for this risk instance</div>
            </div>
            
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Incident Id</div>
              <input 
                type="text" 
                v-model="editedRiskInstance.IncidentId" 
                class="risk-scoring-form-input" 
                :readonly="isReadOnly"
                @input="e => editedRiskInstance.IncidentId = sanitize.escapeHtml(e.target.value)"
              >
              <div class="risk-scoring-helper-text">Reference to the related incident or event</div>
            </div>
            
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Compliance Id</div>
              <input 
                type="text" 
                v-model="editedRiskInstance.ComplianceId" 
                class="risk-scoring-form-input" 
                :readonly="isReadOnly"
                @input="e => editedRiskInstance.ComplianceId = sanitize.escapeHtml(e.target.value)"
              >
              <div class="risk-scoring-helper-text">Compliance framework identifier for this risk</div>
            </div>
          </div>
          
          <div class="risk-scoring-detail-row">
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Risk Title</div>
              <input 
                type="text" 
                v-model="editedRiskInstance.RiskTitle" 
                class="risk-scoring-form-input" 
                :class="{ 'invalid': validationErrors.RiskTitle }"
                :readonly="isReadOnly"
                @input="e => editedRiskInstance.RiskTitle = sanitize.escapeHtml(e.target.value)"
              >
              <span v-if="validationErrors.RiskTitle" class="validation-error">
                {{ sanitize.escapeHtml(validationErrors.RiskTitle) }}
              </span>
              <div class="risk-scoring-helper-text">Provide a brief, descriptive title for this risk</div>
            </div>
            
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Criticality</div>
              <select 
                v-model="editedRiskInstance.Criticality" 
                class="risk-scoring-form-select"
                :class="{ 'invalid': validationErrors.Criticality }"
                :disabled="isReadOnly"
              >
                <option value="">Select Criticality</option>
                <option v-for="value in validationRules.ALLOWED_CRITICALITY" :key="value" :value="value">
                  {{ value }}
                </option>
              </select>
              <span v-if="validationErrors.Criticality" class="validation-error">{{ validationErrors.Criticality }}</span>
              <div class="risk-scoring-helper-text">Choose the severity level of this risk</div>
            </div>
            
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Risk Status</div>
              <select v-model="editedRiskInstance.RiskStatus" class="risk-scoring-form-select" :disabled="isReadOnly">
                <option value="Not Assigned" selected>Not Assigned</option>
                <option value="Assigned">Assigned</option>
                <option value="Approved">Approved</option>
                <option value="Rejected">Rejected</option>
              </select>
              <div class="risk-scoring-helper-text">Current status of this risk in the assessment process</div>
            </div>
          </div>
          
          <div class="risk-scoring-detail-row">
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Category</div>
              <div class="risk-scoring-category-container" v-if="!isReadOnly">
                <div class="risk-scoring-category-dropdown">
                  <div class="risk-scoring-selected-category" @click="toggleCategoryDropdown">
                    <span v-if="!selectedCategory">Select Category</span>
                    <span v-else>{{ selectedCategory }}</span>
                    <i class="fas fa-chevron-down"></i>
                  </div>
                  <div v-if="showCategoryDropdown" class="risk-scoring-category-options">
                    <div class="risk-scoring-category-search">
                      <input 
                        type="text" 
                        v-model="categorySearch" 
                        placeholder="Search categories..."
                        @click.stop
                      >
                      <button type="button" class="risk-scoring-add-category-btn" @click.stop.prevent="showAddCategoryModal = true">
                        <i class="fas fa-plus"></i> Add New
                      </button>
                    </div>
                    <div class="risk-scoring-category-list">
                      <div 
                        v-for="category in filteredCategories" 
                        :key="category.id" 
                        class="risk-scoring-category-item"
                        @click.stop="selectCategory(category)"
                      >
                        <input 
                          type="radio" 
                          :checked="selectedCategory === category.value"
                          @click.stop="selectCategory(category)"
                        >
                        <span>{{ category.value }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <input v-else type="text" v-model="editedRiskInstance.Category" class="risk-scoring-form-input" readonly>
              <div class="risk-scoring-helper-text">Categorize this risk for better organization and management</div>
            </div>
            
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Possible Damage</div>
              <input type="text" v-model="editedRiskInstance.PossibleDamage" class="risk-scoring-form-input" :readonly="isReadOnly">
              <div class="risk-scoring-helper-text">Describe the potential damage or consequences if this risk occurs</div>
            </div>
            
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Risk Priority</div>
              <select 
                v-model="editedRiskInstance.RiskPriority" 
                class="risk-scoring-form-select"
                :class="{ 'invalid': validationErrors.RiskPriority }"
                :disabled="isReadOnly"
              >
                <option value="">Select Priority</option>
                <option v-for="value in validationRules.ALLOWED_RISK_PRIORITY" :key="value" :value="value">
                  {{ value }}
                </option>
              </select>
              <span v-if="validationErrors.RiskPriority" class="validation-error">{{ validationErrors.RiskPriority }}</span>
              <div class="risk-scoring-helper-text">Set the priority level for risk treatment and response</div>
            </div>
          </div>
          
          <div class="risk-scoring-detail-row">
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Reported By</div>
              <input type="text" v-model="editedRiskInstance.ReportedBy" class="risk-scoring-form-input" :readonly="isReadOnly">
              <div class="risk-scoring-helper-text">Name or identifier of the person who reported this risk</div>
            </div>
            
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Origin</div>
              <select 
                v-model="editedRiskInstance.Origin" 
                class="risk-scoring-form-select"
                :class="{ 'invalid': validationErrors.Origin }"
                :disabled="isReadOnly"
              >
                <option value="">Select Origin</option>
                <option v-for="value in validationRules.ALLOWED_ORIGIN" :key="value" :value="value">
                  {{ value }}
                </option>
              </select>
              <span v-if="validationErrors.Origin" class="validation-error">{{ validationErrors.Origin }}</span>
              <div class="risk-scoring-helper-text">Source or method through which this risk was identified</div>
            </div>
            
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Risk Description</div>
              <textarea v-model="editedRiskInstance.RiskDescription" class="risk-scoring-form-textarea" :readonly="isReadOnly"></textarea>
              <div class="risk-scoring-helper-text">Provide a detailed description of the risk, its context, and contributing factors</div>
            </div>
          </div>
        </div>
        
        <!-- Mapping Risks Section -->
        <div class="risk-scoring-section-container">
          <h3 class="risk-scoring-section-title">Mapped Risks</h3>
          <p class="risk-scoring-mapping-description">Select risks from Risk Register with matching Compliance ID: {{ editedRiskInstance.ComplianceId || 'None' }}</p>
          
          <div v-if="loadingMatchingRisks" class="risk-scoring-loading">
            <div class="risk-scoring-spinner"></div>
            <span>Loading matching risks...</span>
          </div>
          
          <div v-else-if="matchingRisks.length > 0" class="risk-scoring-mapping-risks-table">
            <table>
              <thead>
                <tr>
                  <th>Select</th>
                  <th>Risk ID</th>
                  <th>Compliance ID</th>
                  <th>Risk Title</th>
                  <th>Criticality</th>
                  <th>Category</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="risk in matchingRisks" :key="risk.RiskId">
                  <td>
                    <input 
                      type="checkbox" 
                      :id="'risk-' + risk.RiskId" 
                      :value="risk.RiskId" 
                      v-model="selectedRisks"
                      class="risk-scoring-risk-checkbox"
                    >
                  </td>
                  <td>{{ risk.RiskId }}</td>
                  <td>{{ risk.ComplianceId }}</td>
                  <td>{{ risk.RiskTitle }}</td>
                  <td>{{ risk.Criticality }}</td>
                  <td>{{ risk.Category }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="matchingRisks.length > 0" class="risk-scoring-selected-risks-actions">
            <div class="risk-scoring-selected-risks-info">
              <div v-if="selectedRisks.length > 0" class="risk-scoring-selected-risks-count">
                {{ selectedRisks.length }} risk(s) selected
              </div>
              <button 
                v-if="selectedRisks.length > 0" 
                type="button" 
                class="risk-scoring-fill-scoring-button" 
                @click="fillScoringFromSelectedRisk"
              >
                Fill Scoring
              </button>
            </div>
            <button type="button" class="risk-scoring-create-risk-btn" @click="createRisk">Create Risk</button>
          </div>
          
          <div v-else class="risk-scoring-no-matching-risks">
            <p>No matching risks found with Compliance ID: {{ editedRiskInstance.ComplianceId || 'None' }}</p>
            <button type="button" class="risk-scoring-create-risk-btn" @click="createRisk">Create Risk</button>
          </div>
        </div>
        
        <!-- Risk Assessment Section -->
        <div class="risk-scoring-section-container">
          <h3 class="risk-scoring-section-title">Risk Assessment</h3>
          <div class="risk-scoring-detail-row">
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Risk Id</div>
              <input type="text" v-model="editedRiskInstance.RiskId" class="risk-scoring-form-input" :readonly="isReadOnly">
              <div class="risk-scoring-helper-text">Reference to the base risk template from the risk register</div>
            </div>
            
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Risk Likelihood</div>
              <input 
                type="number" 
                v-model.number="editedRiskInstance.RiskLikelihood" 
                class="risk-scoring-form-input"
                :class="{ 'invalid': validationErrors.RiskLikelihood }"
                :min="validationRules.RISK_LIKELIHOOD_RANGE.min"
                :max="validationRules.RISK_LIKELIHOOD_RANGE.max"
                :readonly="isReadOnly"
                @input="calculateRiskExposureRating"
              >
              <span v-if="validationErrors.RiskLikelihood" class="validation-error">{{ validationErrors.RiskLikelihood }}</span>
              <div class="risk-scoring-helper-text">Rate how likely this risk is to occur (1=Very Unlikely, 10=Very Likely)</div>
            </div>
            
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Risk Impact</div>
              <input 
                type="number" 
                v-model.number="editedRiskInstance.RiskImpact" 
                class="risk-scoring-form-input"
                :class="{ 'invalid': validationErrors.RiskImpact }"
                :min="validationRules.RISK_IMPACT_RANGE.min"
                :max="validationRules.RISK_IMPACT_RANGE.max"
                :readonly="isReadOnly"
                @input="calculateRiskExposureRating"
              >
              <span v-if="validationErrors.RiskImpact" class="validation-error">{{ validationErrors.RiskImpact }}</span>
              <div class="risk-scoring-helper-text">Rate the potential impact if this risk occurs (1=Minimal, 10=Severe)</div>
            </div>
          </div>
          
          <div class="risk-scoring-detail-row">
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Impact Multiplier (X) (1-10)</div>
              <input 
                type="number" 
                v-model.number="editedRiskInstance.RiskMultiplierX" 
                class="risk-scoring-form-input"
                :class="{ 'invalid': validationErrors.RiskMultiplierX }"
                :min="validationRules.RISK_MULTIPLIER_X_RANGE.min"
                :max="validationRules.RISK_MULTIPLIER_X_RANGE.max"
                :readonly="isReadOnly"
                @input="calculateRiskExposureRating"
              >
              <span v-if="validationErrors.RiskMultiplierX" class="validation-error">{{ validationErrors.RiskMultiplierX }}</span>
              <div class="risk-scoring-helper-text">Impact multiplier factor (default: 1)</div>
            </div>
            
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Likelihood Multiplier (Y) (1-10)</div>
              <input 
                type="number" 
                v-model.number="editedRiskInstance.RiskMultiplierY" 
                class="risk-scoring-form-input"
                :class="{ 'invalid': validationErrors.RiskMultiplierY }"
                :min="validationRules.RISK_MULTIPLIER_Y_RANGE.min"
                :max="validationRules.RISK_MULTIPLIER_Y_RANGE.max"
                :readonly="isReadOnly"
                @input="calculateRiskExposureRating"
              >
              <span v-if="validationErrors.RiskMultiplierY" class="validation-error">{{ validationErrors.RiskMultiplierY }}</span>
              <div class="risk-scoring-helper-text">Likelihood multiplier factor (default: 1)</div>
            </div>
          </div>
          
          <div class="risk-scoring-detail-row">
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Risk Exposure Rating</div>
              <input type="number" readonly v-model.number="editedRiskInstance.RiskExposureRating" class="risk-scoring-form-input risk-scoring-readonly-input">
              <div class="risk-scoring-helper-text">Automatically calculated as Impact × (X/10) × Likelihood × (Y/10)</div>
            </div>
            
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Risk Type</div>
              <select 
                v-model="editedRiskInstance.RiskType" 
                class="risk-scoring-form-select"
                :class="{ 'invalid': validationErrors.RiskType }"
                :disabled="isReadOnly"
              >
                <option v-for="value in validationRules.ALLOWED_RISK_TYPE" :key="value" :value="value">
                  {{ value }}
                </option>
              </select>
              <span v-if="validationErrors.RiskType" class="validation-error">{{ validationErrors.RiskType }}</span>
              <div class="risk-scoring-helper-text">Classify the nature and timing of this risk</div>
            </div>
            
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Appetite</div>
              <select 
                v-model="editedRiskInstance.Appetite" 
                :class="['risk-scoring-form-select', { 'invalid': validationErrors.Appetite }]"
                :disabled="isReadOnly"
                @change="onAppetiteChange"
              >
                <option v-for="value in validationRules.ALLOWED_APPETITE" :key="value" :value="value">
                  {{ value }}
                </option>
              </select>
              <span v-if="validationErrors.Appetite" class="validation-error">{{ validationErrors.Appetite }}</span>
              <div class="risk-scoring-helper-text">Indicate if the organization accepts this risk level</div>
            </div>
          </div>
          
          <div class="risk-scoring-detail-row">
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label"><i class="fas fa-building"></i> Business Impact</div>
              <div 
                class="risk-scoring-business-impact-dropdown-header" 
                @click.stop="toggleBusinessImpactDropdown"
              >
                <span v-if="selectedBusinessImpacts.length === 0">Select Business Impacts</span>
                <span v-else>{{ selectedBusinessImpacts.length }} impact(s) selected</span>
                <i class="fas fa-chevron-down"></i>
              </div>
              
              <div v-if="showBusinessImpactDropdown" class="risk-scoring-business-impact-dropdown" @click.stop>
                <div class="risk-scoring-dropdown-search-container">
                  <input 
                    type="text" 
                    v-model="businessImpactSearch" 
                    placeholder="Search impacts..." 
                    class="risk-scoring-dropdown-search"
                    @click.stop
                  >
                  <button type="button" class="risk-scoring-add-impact-btn" @click.stop.prevent="showAddImpactModal = true">
                    <i class="fas fa-plus"></i> Add New
                  </button>
                </div>
                
                <div class="risk-scoring-dropdown-items">
                  <div 
                    v-for="impact in filteredBusinessImpacts" 
                    :key="impact.id" 
                    class="risk-scoring-dropdown-item"
                    @click.stop="toggleBusinessImpact(impact)"
                  >
                    <input 
                      type="checkbox" 
                      :id="'impact-' + impact.id" 
                      :checked="isBusinessImpactSelected(impact)"
                      @click.stop
                    >
                    <label :for="'impact-' + impact.id">{{ impact.value }}</label>
                  </div>
                </div>
              </div>
              
              <div class="risk-scoring-selected-items">
                <div 
                  v-for="impact in selectedBusinessImpacts" 
                  :key="impact.id" 
                  class="risk-scoring-selected-item"
                >
                  {{ sanitize.escapeHtml(impact.value) }}
                  <i class="fas fa-times" @click="toggleBusinessImpact(impact)"></i>
                </div>
              </div>
              <div class="risk-scoring-helper-text">Select the business areas that would be affected by this risk</div>
            </div>

            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Risk Response Type</div>
              <select 
                v-model="editedRiskInstance.RiskResponseType" 
                class="risk-scoring-form-select"
                :class="{ 'invalid': validationErrors.RiskResponseType }"
                :disabled="isReadOnly"
              >
                <option v-for="value in validationRules.ALLOWED_RISK_RESPONSE_TYPE" :key="value" :value="value">
                  {{ value }}
                </option>
              </select>
              <span v-if="validationErrors.RiskResponseType" class="validation-error">{{ validationErrors.RiskResponseType }}</span>
              <div class="risk-scoring-helper-text">Choose the strategy for addressing this risk</div>
            </div>
          </div>
          
          <div class="risk-scoring-detail-row">
            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Risk Response Description</div>
              <textarea v-model="editedRiskInstance.RiskResponseDescription" class="risk-scoring-form-textarea" :readonly="isReadOnly"></textarea>
              <div class="risk-scoring-helper-text">Provide details about the chosen risk response strategy</div>
            </div>

            <div class="risk-scoring-detail-item">
              <div class="risk-scoring-detail-label">Risk Mitigation</div>
              <div class="risk-scoring-mitigation-form">
                <div class="risk-scoring-mitigation-input-group">
                  <label>Actions</label>
                  <div v-for="(action, index) in mitigationForm.actions" :key="index" class="risk-scoring-action-item">
                    <input 
                      type="text" 
                      v-model="mitigationForm.actions[index]" 
                      class="risk-scoring-form-input"
                      :readonly="isReadOnly"
                      @input="e => {
                        mitigationForm.actions[index] = sanitize.escapeHtml(e.target.value);
                        updateMitigationJson();
                      }"
                    >
                    <button 
                      v-if="!isReadOnly" 
                      type="button" 
                      class="risk-scoring-remove-action" 
                      @click="removeAction(index)"
                    >
                      <i class="fas fa-times"></i>
                    </button>
                  </div>
                  <button 
                    v-if="!isReadOnly" 
                    type="button" 
                    class="risk-scoring-add-action" 
                    @click="addAction"
                  >
                    <i class="fas fa-plus"></i> Add Action
                  </button>
                </div>
                <!-- Hidden textarea to store the actual JSON -->
                <textarea 
                  v-model="riskMitigationJson" 
                  style="display: none;"
                ></textarea>
              </div>
            </div>
          </div>
        </div>
        
        <div class="risk-scoring-form-footer">
          <button type="submit" class="risk-scoring-submit-button" :disabled="submitting">
            <span v-if="submitting">Saving...</span>
            <span v-else>Save Changes</span>
          </button>
        </div>
        
        <!-- Add Business Impact Modal -->
        <div v-if="showAddImpactModal" class="risk-scoring-modal-overlay" @click.self="showAddImpactModal = false">
          <div class="risk-scoring-modal-content" @click.stop>
            <h3>Add New Business Impact</h3>
            <form @submit.prevent="addNewBusinessImpact" class="risk-scoring-modal-form">
              <div class="risk-scoring-modal-form-group">
                <label>Impact Description</label>
                <input 
                  type="text" 
                  v-model="newBusinessImpact" 
                  placeholder="Enter new business impact"
                  @keyup.enter.prevent="addNewBusinessImpact"
                  autofocus
                >
              </div>
              <div class="risk-scoring-modal-actions">
                <button type="button" class="risk-scoring-cancel-btn" @click.prevent="showAddImpactModal = false">Cancel</button>
                <button type="submit" class="risk-scoring-add-btn" :disabled="!newBusinessImpact.trim()">
                  Add Impact
                </button>
              </div>
            </form>
          </div>
        </div>

        <!-- Add Category Modal -->
        <div v-if="showAddCategoryModal" class="risk-scoring-modal-overlay" @click.self="showAddCategoryModal = false">
          <div class="risk-scoring-modal-content" @click.stop>
            <h3>Add New Category</h3>
            <form @submit.prevent="addNewCategory" class="risk-scoring-modal-form">
              <div class="risk-scoring-modal-form-group">
                <label>Category Name</label>
                <input 
                  type="text" 
                  v-model="newCategory" 
                  placeholder="Enter new category"
                  @keyup.enter.prevent="addNewCategory"
                  autofocus
                >
              </div>
              <div class="risk-scoring-modal-actions">
                <button type="button" class="risk-scoring-cancel-btn" @click.prevent="showAddCategoryModal = false">Cancel</button>
                <button type="submit" class="risk-scoring-add-btn" :disabled="!newCategory.trim()">
                  Add Category
                </button>
              </div>
            </form>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import './ScoringDetails.css';
import { PopupModal } from '@/modules/popup';
import { API_ENDPOINTS } from '@/config/api';

// Add sanitization utilities
const sanitizeUtils = {
  // HTML encoding function
  escapeHtml(unsafe) {
    // Handle null, undefined, and non-string values
    if (unsafe === null || unsafe === undefined) return '';
    // Convert to string if it's not already a string
    const str = String(unsafe);
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  },

  // JavaScript string encoding
  escapeJs(unsafe) {
    if (unsafe === null || unsafe === undefined) return '';
    return JSON.stringify(String(unsafe)).slice(1, -1);
  },

  // Simple HTML sanitizer
  sanitizeHtml(content) {
    if (content === null || content === undefined) return '';
    // First escape HTML special characters
    let escaped = this.escapeHtml(String(content));
    // Only allow specific HTML tags
    const allowedTags = ['b', 'i', 'em', 'strong', 'a', 'p', 'br'];
    allowedTags.forEach(tag => {
      const open = new RegExp(`&lt;${tag}( .*?)?&gt;`, 'g');
      const close = new RegExp(`&lt;/${tag}&gt;`, 'g');
      escaped = escaped
        .replace(open, `<${tag}>`)
        .replace(close, `</${tag}>`);
    });
    return escaped;
  },

  // Safe value display helper
  safeValue(value) {
    if (value === null || value === undefined) return '';
    if (typeof value === 'number') return value;
    return this.escapeHtml(String(value));
  }
};

export default {
  name: 'ScoringDetails',
  components: {
    PopupModal
  },
  props: {
    riskId: {
      type: [String, Number],
      required: true
    },
    action: {
      type: String,
      default: 'view'
    }
  },
  data() {
    return {
      riskInstance: null,
      editedRiskInstance: {
        RiskLikelihood: null,
        RiskImpact: null
      },
      riskMitigationJson: '',
      loading: true,
      error: null,
      submitting: false,
      submitSuccess: false,
      submitError: null,
      matchingRisks: [],
      selectedRisks: [],
      loadingMatchingRisks: false,
      defaultAppetite: "No",
      isReadOnly: false,
      
      // Business Impact related data
      businessImpacts: [],
      selectedBusinessImpacts: [],
      showBusinessImpactDropdown: false,
      businessImpactSearch: '',
      showAddImpactModal: false,
      newBusinessImpact: '',

      // Category dropdown properties
      categories: [],
      selectedCategory: '',
      showCategoryDropdown: false,
      categorySearch: '',
      showAddCategoryModal: false,
      newCategory: '',
      mitigationForm: {
        actions: []
      },
      
      // Add validation rules from risk_validation.py
      validationRules: {
        ALLOWED_CRITICALITY: ['Critical', 'High', 'Medium', 'Low'],
        ALLOWED_RISK_PRIORITY: ['High', 'Medium', 'Low'],
        ALLOWED_ORIGIN: ['Manual', 'SIEM', 'AuditFindings'],
        ALLOWED_RISK_TYPE: ['Current', 'Residual', 'Inherent', 'Emerging', 'Accept'],
        ALLOWED_APPETITE: ['Yes', 'No'],
        ALLOWED_RISK_RESPONSE_TYPE: ['Mitigate', 'Avoid', 'Accept', 'Transfer'],
        RISK_LIKELIHOOD_RANGE: { min: 1, max: 10 },
        RISK_IMPACT_RANGE: { min: 1, max: 10 },
        RISK_MULTIPLIER_X_RANGE: { min: 1, max: 10 },
        RISK_MULTIPLIER_Y_RANGE: { min: 1, max: 10 },
        TEXT_PATTERN: /^[A-Za-z0-9\s.,;:!?'"()\-_[\]]{0,}$/
      },
      validationErrors: {
        Criticality: '',
        RiskPriority: '',
        Origin: '',
        RiskType: '',
        Appetite: '',
        RiskResponseType: '',
        RiskLikelihood: '',
        RiskImpact: '',
        RiskMultiplierX: '',
        RiskMultiplierY: '',
        RiskTitle: '',
        RiskDescription: '',
        Category: '',
        BusinessImpact: '',
        RiskMitigation: ''
      },
      sanitize: sanitizeUtils
    }
  },
  computed: {
    isRejectedAction() {
      return this.$route.query.action === 'reject';
    },
    isViewAction() {
      return this.$route.query.action === 'view';
    },
    isCreateAction() {
      return this.$route.query.action === 'create';
    },
    filteredBusinessImpacts() {
      if (!this.businessImpactSearch) {
        return this.businessImpacts;
      }
      const searchTerm = this.businessImpactSearch.toLowerCase();
      return this.businessImpacts.filter(impact => 
        impact.value.toLowerCase().includes(searchTerm)
      );
    },
    filteredCategories() {
      if (!this.categorySearch) {
        return this.categories;
      }
      const search = this.categorySearch.toLowerCase();
      return this.categories.filter(category => 
        category.value.toLowerCase().includes(search)
      );
    },
    activeValidationErrors() {
      return Object.entries(this.validationErrors)
        .filter(([, error]) => error)  // Only include entries with error messages
        .map(([field, error]) => ({
          field,
          error
        }));
    }
  },
  mounted() {
    this.fetchRiskInstance();
    this.fetchBusinessImpacts();
    this.fetchCategories();
    
    // Add Font Awesome if not already present
    if (!document.querySelector('link[href*="font-awesome"]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css';
      document.head.appendChild(link);
    }
    
    // Log the action taken (accept or reject or view or create)
    const action = this.$route.query.action;
    if (action) {
      console.log(`Risk ${this.riskId} action: ${action}`);
      
      // If action is reject, set default Appetite to "NO"
      if (action === 'reject') {
        this.defaultAppetite = "NO";
      }
      
      // If action is view, set form to read-only mode
      if (action === 'view') {
        this.setReadOnlyMode();
      }
      
      // If action is create, we'll handle it in the fetchRiskInstance method
      if (action === 'create') {
        console.log('Create action detected - will prepare for risk creation');
      }
    }
  },
  methods: {
    // Add push notification method
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

    setReadOnlyMode() {
      this.isReadOnly = true;
      
      // Add a class to the container to indicate read-only mode
      setTimeout(() => {
        const container = document.querySelector('.risk-scoring-container');
        if (container) {
          container.classList.add('risk-scoring-read-only-mode');
        }
      }, 100);
    },
    calculateRiskExposureRating() {
      if (!this.editedRiskInstance) {
        this.editedRiskInstance = {
          RiskLikelihood: null,
          RiskImpact: null,
          RiskMultiplierX: 1, // Default to 1 (0.1)
          RiskMultiplierY: 1  // Default to 1 (0.1)
        };
        return;
      }
      
      // Only calculate if both values are present and valid numbers
      if (this.editedRiskInstance.RiskLikelihood && this.editedRiskInstance.RiskImpact) {
        const likelihood = parseInt(this.editedRiskInstance.RiskLikelihood);
        const impact = parseInt(this.editedRiskInstance.RiskImpact);
        const multiplierX = this.editedRiskInstance.RiskMultiplierX !== null && this.editedRiskInstance.RiskMultiplierX !== undefined && this.editedRiskInstance.RiskMultiplierX !== '' 
          ? parseInt(this.editedRiskInstance.RiskMultiplierX) : 1; // Default to 1 (0.1) only if not provided
        const multiplierY = this.editedRiskInstance.RiskMultiplierY !== null && this.editedRiskInstance.RiskMultiplierY !== undefined && this.editedRiskInstance.RiskMultiplierY !== '' 
          ? parseInt(this.editedRiskInstance.RiskMultiplierY) : 1; // Default to 1 (0.1) only if not provided
        
        if (!isNaN(likelihood) && !isNaN(impact)) {
          // Calculate the Risk Exposure Rating using the new formula
          // Risk Impact * (X/10) * Risk Likelihood * (Y/10) = Risk Exposure Rating
          const calculatedValue = impact * (multiplierX / 10) * likelihood * (multiplierY / 10);
          this.editedRiskInstance.RiskExposureRating = Math.round(calculatedValue * 100) / 100; // Round to 2 decimal places
        }
      }
    },
    fetchRiskInstance() {
      if (this.isCreateAction) {
        this.editedRiskInstance = this.getDefaultInstance();
        this.riskMitigationJson = JSON.stringify({}, null, 2);
        this.mitigationForm = { actions: [] };
        this.loading = false;
        return;
      }

      const safeRiskId = encodeURIComponent(this.riskId);
      
      axios.get(API_ENDPOINTS.RISK_INSTANCE(safeRiskId))
        .then(response => {
          // Sanitize received data
          const sanitizedData = {
            ...response.data,
            RiskTitle: this.sanitize.safeValue(response.data.RiskTitle),
            RiskDescription: this.sanitize.safeValue(response.data.RiskDescription),
            Category: this.sanitize.safeValue(response.data.Category),
            ReportedBy: this.sanitize.safeValue(response.data.ReportedBy),
            // Keep numeric values as is
            RiskLikelihood: response.data.RiskLikelihood,
            RiskImpact: response.data.RiskImpact,
            RiskExposureRating: response.data.RiskExposureRating
          };

          this.riskInstance = sanitizedData;
          this.editedRiskInstance = {
            ...this.getDefaultInstance(),
            ...JSON.parse(JSON.stringify(sanitizedData))
          };

          if (this.editedRiskInstance.RiskMitigation) {
            try {
              const mitigation = typeof this.editedRiskInstance.RiskMitigation === 'string' 
                ? JSON.parse(this.editedRiskInstance.RiskMitigation)
                : this.editedRiskInstance.RiskMitigation;
              // Convert numbered object to array for UI
              let actionsArr = [];
              if (mitigation && typeof mitigation === 'object' && !Array.isArray(mitigation)) {
                // Only use keys that are numbers (as strings)
                const keys = Object.keys(mitigation).filter(k => /^\d+$/.test(k));
                actionsArr = keys.sort((a, b) => parseInt(a) - parseInt(b)).map(k => this.sanitize.safeValue(mitigation[k]));
              }
              this.riskMitigationJson = JSON.stringify(mitigation, null, 2);
              this.mitigationForm = { actions: actionsArr };
            } catch (e) {
              this.riskMitigationJson = JSON.stringify({}, null, 2);
              this.mitigationForm = { actions: [] };
            }
          }

          this.loading = false;

          if (this.editedRiskInstance.ComplianceId) {
            this.fetchMatchingRisks(this.editedRiskInstance.ComplianceId);
          }

          if (this.businessImpacts.length > 0 && this.editedRiskInstance.BusinessImpact) {
            this.parseBusinessImpacts();
          }

          try {
            const mitigation = JSON.parse(this.riskMitigationJson);
            this.mitigationForm = {
              actions: Array.isArray(mitigation.actions) 
                ? mitigation.actions.map(action => this.sanitize.safeValue(action))
                : []
            };
          } catch (e) {
            this.mitigationForm = { actions: [] };
          }
        })
        .catch(error => {
          console.error('Error fetching risk instance:', error);
          this.error = this.sanitize.safeValue(`Failed to fetch risk instance: ${error.message}`);
          this.loading = false;
        });
    },
    fetchMatchingRisks(complianceId) {
      // Direct usage without validation
      if (!complianceId) return;
      
      this.loadingMatchingRisks = true;
      
      // Fetch risks from Risk Register with matching Compliance ID
              axios.get(API_ENDPOINTS.RISKS_FOR_DROPDOWN)
      .then(response => {
        console.log('All risks data received:', response.data);
        // Filter risks to only include those with matching Compliance ID
        const risksData = response.data?.risks || [];
        this.matchingRisks = risksData.filter(risk => 
          risk.ComplianceId && risk.ComplianceId.toString() === complianceId.toString()
        );
        console.log('Filtered matching risks:', this.matchingRisks);
        this.loadingMatchingRisks = false;
      })
      .catch(error => {
        console.error('Error fetching matching risks:', error);
        this.loadingMatchingRisks = false;
      });
    },
    submitForm() {
      if (!this.validateForm()) {
        const errorMessages = Object.entries(this.validationErrors)
          .filter(entry => entry[1])
          .map(entry => this.sanitize.escapeHtml(entry[1]))
          .join('\n');
        
        this.$popup.error('Please fix the following validation errors:\n' + errorMessages);
        
        // Send push notification for validation errors
        this.sendPushNotification({
          title: 'Risk Instance Validation Failed',
          message: `Validation errors found in risk instance "${this.editedRiskInstance.RiskTitle || 'Untitled Risk'}". Please fix the errors and try again.`,
          category: 'risk',
          priority: 'medium',
          user_id: 'default_user'
        });
        return;
      }

      this.submitting = true;

      // Parse and sanitize mitigation data
      let parsedMitigation = {};
      try {
        parsedMitigation = JSON.parse(this.riskMitigationJson);
        if (typeof parsedMitigation !== 'object' || Array.isArray(parsedMitigation)) {
          throw new Error('Risk mitigation must be a valid numbered object');
        }
        // Sanitize all values
        Object.keys(parsedMitigation).forEach(key => {
          parsedMitigation[key] = this.sanitize.escapeHtml(parsedMitigation[key]);
        });
      } catch (e) {
        this.$popup.error('Invalid Risk Mitigation JSON format. Please check the format and try again.');
        
        // Send push notification for JSON format error
        this.sendPushNotification({
          title: 'Risk Mitigation JSON Error',
          message: `Invalid JSON format in risk mitigation for risk "${this.editedRiskInstance.RiskTitle || 'Untitled Risk'}". Please check the format and try again.`,
          category: 'risk',
          priority: 'medium',
          user_id: 'default_user'
        });
        this.submitting = false;
        return;
      }

      // Prepare sanitized data for submission
      const submissionData = {
        ...this.editedRiskInstance,
        RiskTitle: this.sanitize.escapeHtml(this.editedRiskInstance.RiskTitle),
        RiskDescription: this.sanitize.escapeHtml(this.editedRiskInstance.RiskDescription),
        Category: this.sanitize.escapeHtml(this.editedRiskInstance.Category),
        // Don't sanitize ReportedBy as it should be an integer
        RiskMitigation: parsedMitigation,
        BusinessImpact: this.selectedBusinessImpacts
          .map(i => this.sanitize.escapeHtml(i.value))
          .join(', ')
      };

      // Encode URL parameters
      const safeRiskId = encodeURIComponent(this.riskId);
      
      // Use promise chain instead of async/await
      axios.put(API_ENDPOINTS.RISK_INSTANCE(safeRiskId), submissionData)
        .then(response => {
          this.riskInstance = response.data;
          this.editedRiskInstance = JSON.parse(JSON.stringify(response.data));
          
          if (response.data.RiskMitigation) {
            this.riskMitigationJson = JSON.stringify(response.data.RiskMitigation, null, 2);
          }
          
          this.submitting = false;
          this.submitSuccess = true;
          this.$popup.success('Risk instance updated successfully!');
          
          // Send push notification for successful update
          this.sendPushNotification({
            title: 'Risk Instance Updated Successfully',
            message: `Risk instance "${this.editedRiskInstance.RiskTitle || 'Untitled Risk'}" has been updated successfully in the Risk module.`,
            category: 'risk',
            priority: 'high',
            user_id: 'default_user'
          });
        })
        .catch(error => {
          console.error('Error updating risk instance:', error);
          this.submitting = false;
          this.$popup.error('Failed to update risk instance: ' + 
            this.sanitize.escapeHtml(error.response?.data?.message || error.message)
          );
          
          // Send push notification for failed update
          this.sendPushNotification({
            title: 'Risk Instance Update Failed',
            message: `Failed to update risk instance "${this.editedRiskInstance.RiskTitle || 'Untitled Risk'}": ${error.response?.data?.message || error.message}`,
            category: 'risk',
            priority: 'high',
            user_id: 'default_user'
          });
        });
    },
    formatLabel(key) {
      // Convert camelCase or PascalCase to space-separated words
      return key.replace(/([A-Z])/g, ' $1').trim();
    },
    onAppetiteChange() {
      // When Appetite changes, update RiskStatus accordingly
      // Use case-insensitive comparison
      const appetite = (this.editedRiskInstance.Appetite || '').toLowerCase();
      
      if (appetite === 'no') {
        this.editedRiskInstance.RiskStatus = 'Rejected';
        this.editedRiskInstance.Appetite = 'No'; // Ensure consistent casing
        console.log('Appetite set to No: Updated RiskStatus to Rejected');
      } else if (this.isRejectedAction && appetite === 'yes') {
        // If this was originally a rejection but user changed to Yes
        console.log('Warning: Appetite changed from No to Yes in a rejection action');
        // Still allow the change but make sure casing is consistent
        this.editedRiskInstance.Appetite = 'Yes';
      }
    },
    goBack() {
      // Navigate back to the risk scoring page
      this.$router.push('/risk/scoring');
      
      // If this was a rejection action, log it
      if (this.isRejectedAction) {
        console.log(`Returning to Risk Scoring after rejecting risk ${this.riskId}`);
      }
    },
    createRisk() {
      console.log(`Navigating to Create Risk page from risk ${this.riskId}`);
      // Navigate to Create Risk page with the current risk instance ID
      this.$router.push({
        path: '/risk/create-risk',
        query: { 
          source_risk_id: this.riskId,
          return_to: 'scoring-details',
          action: 'accept'
        }
      });
    },
    mapScoringRisk() {
      console.log(`Mapping scoring risk for risk ${this.riskId}`);
      // This method will be used to map scoring risk
      // For now, we'll just show an info popup
      this.$popup.info('Mapping scoring risk functionality will be implemented here.');
      
      // Send push notification for mapping functionality
      this.sendPushNotification({
        title: 'Risk Mapping Feature',
        message: `Risk mapping functionality will be implemented for risk "${this.editedRiskInstance.RiskTitle || 'Untitled Risk'}".`,
        category: 'risk',
        priority: 'low',
        user_id: 'default_user'
      });
    },
    fillScoringFromSelectedRisk() {
      if (this.selectedRisks.length > 0) {
        // Get the first selected risk ID (in case multiple are selected)
        const selectedRiskId = this.selectedRisks[0];
        
        // Find the corresponding risk from the matching risks array
        const selectedRisk = this.matchingRisks.find(risk => risk.RiskId === selectedRiskId);
        
        if (selectedRisk) {
          // Fill the form fields with data from the selected risk
          this.editedRiskInstance.RiskId = selectedRisk.RiskId;
          this.editedRiskInstance.RiskLikelihood = selectedRisk.RiskLikelihood ? parseInt(selectedRisk.RiskLikelihood) || 1 : 1;
          this.editedRiskInstance.RiskImpact = selectedRisk.RiskImpact ? parseInt(selectedRisk.RiskImpact) || 1 : 1;
          
          // Convert multiplier values from 0.1-1.0 range (stored in DB) to 1-10 range (frontend expects)
          if (selectedRisk.RiskMultiplierX) this.editedRiskInstance.RiskMultiplierX = Math.round(selectedRisk.RiskMultiplierX * 10);
          if (selectedRisk.RiskMultiplierY) this.editedRiskInstance.RiskMultiplierY = Math.round(selectedRisk.RiskMultiplierY * 10);
          
          // Calculate Risk Exposure Rating based on the filled values
          this.calculateRiskExposureRating();
          
          // Show success message
          this.$popup.success('Risk scoring data has been filled from the selected risk.');
          
          // Send push notification for successful scoring fill
          this.sendPushNotification({
            title: 'Risk Scoring Data Filled',
            message: `Risk scoring data has been filled from selected risk for "${this.editedRiskInstance.RiskTitle || 'Untitled Risk'}".`,
            category: 'risk',
            priority: 'medium',
            user_id: 'default_user'
          });
        } else {
          this.$popup.error('Could not find the selected risk data.');
          
          // Send push notification for error finding selected risk
          this.sendPushNotification({
            title: 'Risk Data Not Found',
            message: `Could not find the selected risk data for risk "${this.editedRiskInstance.RiskTitle || 'Untitled Risk'}".`,
            category: 'risk',
            priority: 'medium',
            user_id: 'default_user'
          });
        }
      } else {
        this.$popup.warning('Please select a risk first.');
        
        // Send push notification for no risk selection
        this.sendPushNotification({
          title: 'No Risk Selected',
          message: `Please select a risk first to fill scoring data for "${this.editedRiskInstance.RiskTitle || 'Untitled Risk'}".`,
          category: 'risk',
          priority: 'low',
          user_id: 'default_user'
        });
      }
    },
    validateField() {
      // Direct validation without checks
      return true;
    },
    validateAllFields() {
      // Direct validation without checks
      return true;
    },
    validateResponseData(data) {
      if (!Array.isArray(data)) {
        console.error('Expected array response, got:', typeof data);
        return [];
      }
      
      return data;
    },
    
    // Business Impact Methods
    async fetchBusinessImpacts() {
      try {
        const response = await axios.get(API_ENDPOINTS.BUSINESS_IMPACTS);
        if (response.data.status === 'success') {
          this.businessImpacts = response.data.data;
          
          // If we have business impacts in the risk instance, parse and set them
          if (this.editedRiskInstance && this.editedRiskInstance.BusinessImpact) {
            this.parseBusinessImpacts();
          }
        }
      } catch (error) {
        console.error('Error fetching business impacts:', error);
      }
    },
    
    parseBusinessImpacts() {
      if (!this.editedRiskInstance.BusinessImpact) return;
      
      // Split the comma-separated string into an array
      const impactValues = this.editedRiskInstance.BusinessImpact.split(',').map(val => val.trim());
      
      // Find matching impacts in the businessImpacts array
      impactValues.forEach(value => {
        const matchingImpact = this.businessImpacts.find(impact => 
          impact.value.toLowerCase() === value.toLowerCase()
        );
        
        if (matchingImpact && !this.selectedBusinessImpacts.some(i => i.id === matchingImpact.id)) {
          this.selectedBusinessImpacts.push(matchingImpact);
        }
      });
    },

    toggleBusinessImpactDropdown() {
      this.showBusinessImpactDropdown = !this.showBusinessImpactDropdown;
      if (this.showBusinessImpactDropdown) {
        this.businessImpactSearch = '';
        document.addEventListener('click', this.closeBusinessImpactDropdown);
      } else {
        document.removeEventListener('click', this.closeBusinessImpactDropdown);
      }
    },

    closeBusinessImpactDropdown(event) {
      const dropdown = document.querySelector('.risk-scoring-business-impact-dropdown');
      if (dropdown && !dropdown.contains(event.target)) {
        this.showBusinessImpactDropdown = false;
        document.removeEventListener('click', this.closeBusinessImpactDropdown);
      }
    },

    toggleBusinessImpact(impact) {
      const index = this.selectedBusinessImpacts.findIndex(i => i.id === impact.id);
      if (index === -1) {
        this.selectedBusinessImpacts.push(impact);
      } else {
        this.selectedBusinessImpacts.splice(index, 1);
      }
      this.editedRiskInstance.BusinessImpact = this.selectedBusinessImpacts.map(i => i.value).join(', ');
    },

    isBusinessImpactSelected(impact) {
      return this.selectedBusinessImpacts.some(i => i.id === impact.id);
    },

    async addNewBusinessImpact(event) {
      // Prevent default form submission
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      
      // Don't proceed if input is empty
      if (!this.newBusinessImpact.trim()) {
        return;
      }
      
      try {
        console.log('Adding new business impact:', this.newBusinessImpact);
        
        const response = await axios.post(API_ENDPOINTS.ADD_BUSINESS_IMPACT, {
          value: this.newBusinessImpact.trim()
        });
        
        if (response.data.status === 'success') {
          console.log('Successfully added business impact:', response.data.data);
          this.businessImpacts.push(response.data.data);
          this.toggleBusinessImpact(response.data.data);
          this.showAddImpactModal = false;
          this.newBusinessImpact = '';
        } else {
          throw new Error('Failed to add business impact: ' + (response.data.message || 'Unknown error'));
        }
      } catch (error) {
        console.error('Error adding new business impact:', error);
        this.$popup.error('Failed to add new business impact: ' + (error.response?.data?.message || error.message));
        
        // Send push notification for failed business impact addition
        this.sendPushNotification({
          title: 'Business Impact Addition Failed',
          message: `Failed to add new business impact "${this.newBusinessImpact}": ${error.response?.data?.message || error.message}`,
          category: 'risk',
          priority: 'medium',
          user_id: 'default_user'
        });
      }
    },

    // Category Methods
    async fetchCategories() {
      try {
        const response = await axios.get(API_ENDPOINTS.RISK_CATEGORIES);
        if (response.data.status === 'success') {
          this.categories = response.data.data;
          
          // If we have a category in the edited risk instance, set it as selected
          if (this.editedRiskInstance && this.editedRiskInstance.Category) {
            this.selectedCategory = this.editedRiskInstance.Category;
          }
        }
      } catch (error) {
        console.error('Error fetching categories:', error);
      }
    },

    toggleCategoryDropdown() {
      this.showCategoryDropdown = !this.showCategoryDropdown;
      if (this.showCategoryDropdown) {
        this.categorySearch = '';
      }
    },

    selectCategory(category) {
      this.selectedCategory = category.value;
      this.editedRiskInstance.Category = category.value;
      this.showCategoryDropdown = false;
    },

    async addNewCategory(event) {
      // Prevent default form submission
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      
      // Don't proceed if input is empty
      if (!this.newCategory.trim()) {
        return;
      }
      
      try {
        console.log('Adding new category:', this.newCategory);
        
        const response = await axios.post(API_ENDPOINTS.ADD_RISK_CATEGORY, {
          value: this.newCategory.trim()
        });
        
        if (response.data.status === 'success') {
          console.log('Successfully added category:', response.data.data);
          this.categories.push(response.data.data);
          this.selectCategory(response.data.data);
          this.showAddCategoryModal = false;
          this.newCategory = '';
        } else {
          throw new Error('Failed to add category: ' + (response.data.message || 'Unknown error'));
        }
      } catch (error) {
        console.error('Error adding new category:', error);
        this.$popup.error('Failed to add new category: ' + (error.response?.data?.message || error.message));
        
        // Send push notification for failed category addition
        this.sendPushNotification({
          title: 'Category Addition Failed',
          message: `Failed to add new category "${this.newCategory}": ${error.response?.data?.message || error.message}`,
          category: 'risk',
          priority: 'medium',
          user_id: 'default_user'
        });
      }
    },
    
    updateMitigationJson() {
      // Convert actions array to numbered object
      const actionsObj = {};
      this.mitigationForm.actions.forEach((action, idx) => {
        if (action.trim() !== '') {
          actionsObj[(idx + 1).toString()] = action;
        }
      });
      this.riskMitigationJson = JSON.stringify(actionsObj, null, 2);
    },
    
    addAction() {
      this.mitigationForm.actions.push('');
      this.updateMitigationJson();
    },
    
    removeAction(index) {
      this.mitigationForm.actions.splice(index, 1);
      this.updateMitigationJson();
    },

    // Add validation methods
    validateChoiceField(value, field, allowedValues) {
      if (!value) {
        return `${field} is required`;
      }
      if (!allowedValues.includes(value)) {
        return `Invalid ${field}. Must be one of: ${allowedValues.join(', ')}`;
      }
      return '';
    },

    validateNumericField(value, field, min, max) {
      const numValue = parseInt(value);
      if (isNaN(numValue)) {
        return `${field} must be a number`;
      }
      if (numValue < min || numValue > max) {
        return `${field} must be between ${min} and ${max}`;
      }
      return '';
    },

    validateTextField(value, field, required = false) {
      const sanitizedValue = this.sanitize.safeValue(value);
      if (!sanitizedValue && required) {
        return `${field} is required`;
      }
      if (sanitizedValue && !this.validationRules.TEXT_PATTERN.test(sanitizedValue)) {
        return `${field} contains invalid characters`;
      }
      return '';
    },

    validateForm() {
      // Reset validation errors
      Object.keys(this.validationErrors).forEach(key => {
        this.validationErrors[key] = '';
      });

      // Validate choice fields
      this.validationErrors.Criticality = this.validateChoiceField(
        this.editedRiskInstance.Criticality,
        'Criticality',
        this.validationRules.ALLOWED_CRITICALITY
      );

      this.validationErrors.RiskPriority = this.validateChoiceField(
        this.editedRiskInstance.RiskPriority,
        'Risk Priority',
        this.validationRules.ALLOWED_RISK_PRIORITY
      );

      this.validationErrors.Origin = this.validateChoiceField(
        this.editedRiskInstance.Origin,
        'Origin',
        this.validationRules.ALLOWED_ORIGIN
      );

      this.validationErrors.RiskType = this.validateChoiceField(
        this.editedRiskInstance.RiskType,
        'Risk Type',
        this.validationRules.ALLOWED_RISK_TYPE
      );

      this.validationErrors.Appetite = this.validateChoiceField(
        this.editedRiskInstance.Appetite,
        'Appetite',
        this.validationRules.ALLOWED_APPETITE
      );

      this.validationErrors.RiskResponseType = this.validateChoiceField(
        this.editedRiskInstance.RiskResponseType,
        'Risk Response Type',
        this.validationRules.ALLOWED_RISK_RESPONSE_TYPE
      );

      // Validate numeric fields
      this.validationErrors.RiskLikelihood = this.validateNumericField(
        this.editedRiskInstance.RiskLikelihood,
        'Risk Likelihood',
        this.validationRules.RISK_LIKELIHOOD_RANGE.min,
        this.validationRules.RISK_LIKELIHOOD_RANGE.max
      );

      this.validationErrors.RiskImpact = this.validateNumericField(
        this.editedRiskInstance.RiskImpact,
        'Risk Impact',
        this.validationRules.RISK_IMPACT_RANGE.min,
        this.validationRules.RISK_IMPACT_RANGE.max
      );

      // Validate text fields
      this.validationErrors.RiskTitle = this.validateTextField(
        this.editedRiskInstance.RiskTitle,
        'Risk Title',
        true
      );

      this.validationErrors.RiskDescription = this.validateTextField(
        this.editedRiskInstance.RiskDescription,
        'Risk Description',
        true
      );

      this.validationErrors.Category = this.validateTextField(
        this.editedRiskInstance.Category,
        'Category',
        true
      );

      // Return true if no errors, false otherwise
      return !Object.values(this.validationErrors).some(error => error !== '');
    },

    // Add helper method for default instance
    getDefaultInstance() {
      return {
        RiskLikelihood: null,
        RiskImpact: null,
        RiskStatus: 'Not Assigned',
        RiskType: 'Current',
        Appetite: this.isRejectedAction ? 'No' : 'Yes',
        RiskResponseType: 'Mitigate',
        RiskMitigation: {},
        BusinessImpact: '',
        ComplianceId: null,
        RiskTitle: '',
        RiskDescription: '',
        Category: '',
        Criticality: '',
        RiskPriority: '',
        Origin: '',
        ReportedBy: null
      };
    }
  },
  watch: {
    'editedRiskInstance.ComplianceId': function(newValue) {
      // When Compliance ID changes, fetch matching risks
      console.log('ComplianceId changed to:', newValue);
      this.selectedRisks = []; // Reset selected risks when Compliance ID changes
      if (newValue) {
        this.fetchMatchingRisks(newValue);
      } else {
        this.matchingRisks = [];
      }
    }
  }
}
</script> 