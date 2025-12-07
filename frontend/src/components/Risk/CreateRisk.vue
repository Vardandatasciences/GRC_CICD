<template>
  <div class="risk-register-container create-risk">
    <!-- Add PopupModal component -->
    <PopupModal />
    
    <div class="risk-register-header-row">
      <h2 class="risk-register-title"> Create New Risk</h2>
      <div v-if="sourceRiskId" class="risk-source-badge">
        <span v-if="isLoadingSourceRisk">
          <i class="fas fa-spinner fa-spin"></i> Loading source risk data...
        </span>
        <span v-else>
          <i class="fas fa-link"></i> Creating from Risk #{{ sourceRiskId }}
        </span>
      </div>
    </div>
    
    <!-- Creation Mode Toggle -->
    <div class="risk-creation-mode-toggle">
      <div class="risk-toggle-container">
        <div 
          class="risk-toggle-option" 
          :class="{ active: creationMode === 'manual' }" 
          @click="setCreationMode('manual')"
        >
          <i class="fas fa-user"></i> Manual Creation
        </div>
        <div 
          class="risk-toggle-option" 
          :class="{ active: creationMode === 'ai' }" 
          @click="setCreationMode('ai')"
        >
          <i class="fas fa-robot"></i> AI Suggested
        </div>
        <div 
          class="risk-toggle-option" 
          :class="{ active: creationMode === 'tailoring' }" 
          @click="setCreationMode('tailoring')"
        >
          <i class="fas fa-edit"></i> Tailoring Risk
        </div>
        <div class="risk-toggle-slider" :class="{ 
          'slide-center': creationMode === 'ai',
          'slide-right': creationMode === 'tailoring'
        }"></div>
      </div>
    </div>
    
    <!-- AI Input Form (shown only in AI mode) -->
    <div v-if="creationMode === 'ai' && !aiSuggestionGenerated" class="risk-ai-input-form">
      <h3><i class="fas fa-robot"></i> AI Risk Analysis</h3>
      
      <!-- Loading state -->
      <div v-if="isGeneratingAi" class="risk-ai-loading-state">
        <div class="risk-ai-spinner">
          <i class="fas fa-spinner fa-spin"></i>
        </div>
        <p>Analyzing incident data with AI...</p>
      </div>
      
      <!-- Incident data display/input -->
      <div v-else>
        <div v-if="incidentId" class="risk-incident-info">
          <div class="risk-incident-badge">
            <i class="fas fa-exclamation-triangle"></i> 
            Incident #{{ incidentId }}
          </div>
        </div>
        
        <div class="risk-ai-form-group">
          <label>Title</label>
          <div v-if="incidentId" class="risk-incident-data-box">{{ aiInput.title || 'No title available' }}</div>
          <input v-else type="text" v-model="aiInput.title" placeholder="Enter incident title for AI analysis" class="risk-ai-input-field" />
        </div>
        
        <div class="risk-ai-form-group">
          <label>Description</label>
          <div v-if="incidentId" class="risk-incident-data-box description">{{ aiInput.description || 'No description available' }}</div>
          <textarea v-else v-model="aiInput.description" placeholder="Enter incident description for AI analysis" class="risk-ai-input-field description" rows="4"></textarea>
        </div>
        
        <div class="risk-ai-form-actions">
          <button 
            class="risk-generate-btn" 
            @click="generateAiSuggestion" 
            :disabled="isGeneratingAi || (!aiInput.title && !aiInput.description)"
          >
            <i class="fas fa-magic"></i>
            Generate Risk Analysis
          </button>
          <div v-if="riskJustifications.likelihood || riskJustifications.impact" class="risk-ai-justifications-available">
            <i class="fas fa-info-circle"></i>
            AI justifications available - hover over the AI badges next to Risk Likelihood and Risk Impact fields
          </div>
        </div>
      </div>
    </div>
    
    <!-- Add Risk Form -->
    <div class="risk-register-add-form" v-if="creationMode === 'manual' || (creationMode === 'ai' && aiSuggestionGenerated)">
      <form @submit.prevent="submitRisk" class="risk-register-form-grid">
        <!-- Compliance ID - Centered at top -->
        <div class="risk-register-form-group risk-compliance-id-container">
          <label>
            <span><i class="fas fa-hashtag"></i> Compliance ID</span>
          </label>
          <div class="risk-compliance-dropdown-container">
            <input 
              type="text" 
              v-model="selectedComplianceIdText" 
              placeholder="Enter or select compliance ID"
              @focus="showComplianceDropdown = true"
              readonly
            />
            <button type="button" class="risk-dropdown-toggle" @click.stop="toggleComplianceDropdown($event)">
              <i class="fas fa-chevron-down"></i>
            </button>
            
            <div v-if="showComplianceDropdown" class="risk-compliance-dropdown" @click.stop>
              <div class="risk-compliance-dropdown-search">
                <input 
                  type="text" 
                  v-model="complianceSearchQuery" 
                  placeholder="Search compliances..." 
                  @input="filterCompliances"
                  @click.stop
                >
              </div>
              <div class="risk-compliance-dropdown-list" v-if="loadingCompliances">
                <div class="risk-loading-spinner">Loading compliances...</div>
              </div>
              <div class="risk-compliance-dropdown-list" v-else-if="filteredCompliances.length === 0">
                <div class="risk-no-results">No compliances found</div>
              </div>
              <div class="risk-compliance-dropdown-list" v-else>
                <div 
                  v-for="compliance in filteredCompliances" 
                  :key="compliance.ComplianceId" 
                  class="risk-compliance-item"
                  @click="selectCompliance(compliance)"
                >
                  <div class="risk-compliance-item-content">
                    <div class="risk-compliance-item-header">
                      <div class="risk-compliance-id-wrapper">
                        <input 
                          type="checkbox" 
                          :id="'compliance-' + compliance.ComplianceId" 
                          :checked="newRisk.ComplianceId === compliance.ComplianceId"
                          @click.stop="selectCompliance(compliance)"
                          class="risk-compliance-item-checkbox"
                        >
                        <span class="risk-compliance-id">ID: {{ compliance.ComplianceId }}</span>
                      </div>
                      <span :class="'risk-compliance-criticality ' + (compliance.Criticality ? compliance.Criticality.toLowerCase() : '')">{{ compliance.Criticality || 'No Criticality' }}</span>
                    </div>
                    <div class="risk-compliance-item-description">{{ sanitizeHTML(truncateText(compliance.ComplianceItemDescription, 100)) || 'No description available' }}</div>
                    <div v-if="compliance.PossibleDamage" class="risk-compliance-item-damage">
                      <strong>Possible Damage:</strong> {{ sanitizeHTML(truncateText(compliance.PossibleDamage, 80)) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="risk-helper-text">Select the compliance requirement this risk is associated with</div>
        </div>
        
        <!-- First Row: Criticality, Category, RiskPriority -->
        <div class="form-row">
          <SelectInput
            id="criticality"
            v-model="newRisk.Criticality"
            label="Criticality"
            placeholder="Select Criticality"
            :options="criticalityOptions"
            name="Criticality"
            helper-text="Choose the severity level of this risk"
          />
          
          <div class="risk-register-form-group">
            <label>
              <span><i class="fas fa-tags"></i> Category</span>
            </label>
            <div class="risk-category-container">
              <div class="risk-category-dropdown">
                <div class="risk-selected-category" @click="toggleCategoryDropdown($event)">
                  <span v-if="!selectedCategory">Select Category</span>
                  <span v-else>{{ selectedCategory }}</span>
                  <i class="fas fa-chevron-down"></i>
                </div>
                <div v-if="showCategoryDropdown" class="risk-category-options" @click.stop>
                  <div class="risk-category-search">
                    <input 
                      type="text" 
                      v-model="categorySearch" 
                      placeholder="Search categories..."
                      @click.stop
                    >
                    <button type="button" class="risk-add-category-btn" @click.stop.prevent="showAddCategoryModal = true">
                      <i class="fas fa-plus"></i> Add New
                    </button>
                  </div>
                  <div class="risk-category-list">
                    <div 
                      v-for="category in filteredCategories" 
                      :key="category.id" 
                      class="risk-category-item"
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
            <div class="risk-helper-text">Categorize the risk for better organization and reporting</div>
          </div>
          
          <SelectInput
            id="riskPriority"
            v-model="newRisk.RiskPriority"
            label="Risk Priority"
            placeholder="Select Priority"
            :options="priorityOptions"
            required
            name="RiskPriority"
            helper-text="Set the priority level for risk treatment"
          />
        </div>
        
        <!-- Second Row: RiskLikelihood, RiskImpact, RiskExposureRating -->
        <div class="form-row">
          <div class="risk-register-form-group ai-enhanced">
            <label>
              <span><i class="fas fa-chart-line"></i> Risk Likelihood (1-10)</span>
              <div v-if="riskJustifications.likelihood" class="ai-justification-indicator">
                <div class="risk-ai-justification-tooltip" 
                     @mouseenter="handleTooltipInteraction($event)"
                     @mouseleave="handleTooltipLeave($event)">
                  <div class="ai-badge" title="Hover to see AI justification">
                    <i class="fas fa-robot"></i> AI
                  </div>
                  <div class="tooltip-content">
                    <div class="tooltip-header">AI Justification</div>
                    <div class="tooltip-text">{{ riskJustifications.likelihood }}</div>
                  </div>
                </div>
              </div>
            </label>
            <NumberInput
              id="riskLikelihood"
              v-model="newRisk.RiskLikelihood"
              placeholder="Enter likelihood"
              :min="1"
              :max="10"
              required
              @update:modelValue="calculateRiskExposureRating"
              name="RiskLikelihood"
              helper-text="Rate how likely this risk is to occur (1=Very Unlikely, 10=Very Likely)"
            />
          </div>
          
          <div class="risk-register-form-group ai-enhanced">
            <label>
              <span><i class="fas fa-exclamation-triangle"></i> Risk Impact (1-10)</span>
              <div v-if="riskJustifications.impact" class="ai-justification-indicator">
                <div class="risk-ai-justification-tooltip"
                     @mouseenter="handleTooltipInteraction($event)"
                     @mouseleave="handleTooltipLeave($event)">
                  <div class="ai-badge" title="Hover to see AI justification">
                    <i class="fas fa-robot"></i> AI
                  </div>
                  <div class="tooltip-content">
                    <div class="tooltip-header">AI Justification</div>
                    <div class="tooltip-text">{{ riskJustifications.impact }}</div>
                  </div>
                </div>
              </div>
            </label>
            <NumberInput
              id="riskImpact"
              v-model="newRisk.RiskImpact"
              placeholder="Enter impact"
              :min="1"
              :max="10"
              required
              @update:modelValue="calculateRiskExposureRating"
              name="RiskImpact"
              helper-text="Rate the potential impact if this risk occurs (1=Minimal, 10=Severe)"
            />
          </div>
          
          <!-- Multiplier Fields -->
          <div class="risk-register-form-group">
            <label><i class="fas fa-times"></i> Impact Multiplier (X) (1-10)</label>
            <NumberInput
              id="riskMultiplierX"
              v-model="newRisk.RiskMultiplierX"
              placeholder="Enter X multiplier"
              :min="1"
              :max="10"
              required
              @update:modelValue="calculateRiskExposureRating"
              name="RiskMultiplierX"
              helper-text="Impact multiplier factor (default: 1)"
            />
          </div>
          
          <div class="risk-register-form-group">
            <label><i class="fas fa-times"></i> Likelihood Multiplier (Y) (1-10)</label>
            <NumberInput
              id="riskMultiplierY"
              v-model="newRisk.RiskMultiplierY"
              placeholder="Enter Y multiplier"
              :min="1"
              :max="10"
              required
              @update:modelValue="calculateRiskExposureRating"
              name="RiskMultiplierY"
              helper-text="Likelihood multiplier factor (default: 1)"
            />
          </div>
          
          <NumberInput
            id="riskExposureRating"
            v-model="newRisk.RiskExposureRating"
            label="Risk Exposure Rating"
            placeholder="Calculated rating"
            readonly
            name="RiskExposureRating"
            helper-text="Automatically calculated as Risk Impact × (X/10) × Risk Likelihood × (Y/10)"
          />
        </div>
        
        <!-- Third Row: RiskType, BusinessImpact, RiskTitle -->
        <div class="form-row">
          <SelectInput
            id="riskType"
            v-model="newRisk.RiskType"
            label="Risk Type"
            placeholder="Select Risk Type"
            :options="riskTypeOptions"
            required
            name="RiskType"
            helper-text="Classify the nature and timing of this risk"
          />
          
          <div class="risk-register-form-group">
            <label>
              <span><i class="fas fa-building"></i> Business Impact</span>
            </label>
            <div class="risk-business-impact-container">
              <div class="risk-business-impact-dropdown">
                <div class="risk-selected-impacts" @click="toggleBusinessImpactDropdown($event)">
                  <span v-if="selectedBusinessImpacts.length === 0">Select Business Impacts</span>
                  <span v-else>{{ selectedBusinessImpacts.length }} impact(s) selected</span>
                  <i class="fas fa-chevron-down"></i>
                </div>
                <div v-if="showBusinessImpactDropdown" class="risk-business-impact-options" @click.stop>
                  <div class="risk-business-impact-search">
                    <input 
                      type="text" 
                      v-model="businessImpactSearch" 
                      placeholder="Search impacts..."
                      @click.stop
                    >
                    <button type="button" class="risk-add-impact-btn" @click.stop.prevent="showAddImpactModal = true">
                      <i class="fas fa-plus"></i> Add New
                    </button>
                  </div>
                  <div class="risk-business-impact-list">
                    <div 
                      v-for="impact in filteredBusinessImpacts" 
                      :key="impact.id" 
                      class="risk-business-impact-item"
                      @click.stop="toggleBusinessImpact(impact)"
                    >
                      <input 
                        type="checkbox" 
                        :checked="isBusinessImpactSelected(impact)"
                        @click.stop="toggleBusinessImpact(impact)"
                      >
                      <span>{{ impact.value }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="risk-selected-impacts-display">
                <div 
                  v-for="impact in selectedBusinessImpacts" 
                  :key="impact.id" 
                  class="risk-selected-impact-tag"
                >
                  {{ impact.value }}
                  <i class="fas fa-times" @click="toggleBusinessImpact(impact)"></i>
                </div>
              </div>
            </div>
            <div class="risk-helper-text">Select the business areas that would be affected by this risk</div>
          </div>
          
          <TextInput
            id="riskTitle"
            v-model="newRisk.RiskTitle"
            label="Risk Title"
            placeholder="Enter a clear, concise risk title"
            required
            :pattern="null"
            name="RiskTitle"
            helper-text="Provide a brief, descriptive title for this risk"
          />
        </div>
        
        <!-- Fourth Row: RiskDescription, PossibleDamage, RiskMitigation -->
        <div class="form-row">
          <TextareaInput
            id="riskDescription"
            v-model="newRisk.RiskDescription"
            label="Risk Description"
            placeholder="Provide a detailed description of the risk"
            required
            :rows="4"
            @update:modelValue="value => newRisk.RiskDescription = sanitizeInput(value)"
            name="RiskDescription"
            helper-text="Describe the risk scenario, causes, and potential triggers"
          />
          
          <TextareaInput
            id="possibleDamage"
            v-model="newRisk.PossibleDamage"
            label="Possible Damage"
            placeholder="Describe the potential damage or consequences"
            :rows="4"
            @update:modelValue="value => newRisk.PossibleDamage = sanitizeInput(value)"
            name="PossibleDamage"
            helper-text="Detail the potential consequences and damage if this risk materializes"
            style="min-height: 120px; height: 200px; resize: vertical;"

          />
          
          <div class="risk-register-form-group">
            <label>
              <span><i class="fas fa-shield-alt"></i> Risk Mitigation</span>
            </label>
            <div class="risk-mitigation-form">
              <div class="risk-mitigation-input-group">
                <label>Actions</label>
                <div v-for="(action, index) in mitigationForm.actions" :key="index" class="risk-mitigation-action-item">
                  <input 
                    type="text" 
                    v-model="mitigationForm.actions[index]" 
                    class="risk-form-input"
                    @input="e => {
                      mitigationForm.actions[index] = sanitizeInput(e.target.value);
                      updateMitigationJson();
                    }"
                  >
                  <button 
                    type="button" 
                    class="risk-remove-action" 
                    @click="removeAction(index)"
                  >
                    <i class="fas fa-times"></i>
                  </button>
                </div>
                <button 
                  type="button" 
                  class="risk-add-action" 
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
            <div class="risk-helper-text">Add specific actions to mitigate or eliminate this risk</div>
          </div>
        </div>
        
        <!-- Submit Button -->
        <div class="risk-register-form-actions">
          <button type="submit" class="risk-register-submit-btn">
            <i class="fas fa-save"></i> Create Risk
          </button>
          <button type="button" class="risk-register-reset-btn" @click="resetForm">
            <i class="fas fa-undo"></i> Reset Form
          </button>
        </div>
      </form>
    </div>
    
    <!-- Success Message -->
    <div v-if="showSuccessMessage" class="risk-success-message">
      <i class="fas fa-check-circle"></i>
      Risk has been successfully created!
    </div>
    
    <!-- Add Business Impact Modal -->
    <div v-if="showAddImpactModal" class="risk-modal-overlay" @click.self="showAddImpactModal = false">
      <div class="risk-modal-content" @click.stop>
        <h3>Add New Business Impact</h3>
        <form @submit.prevent="addNewBusinessImpact" class="risk-modal-form">
          <div class="risk-modal-form-group">
            <label>Impact Description</label>
            <input 
              type="text" 
              v-model="newBusinessImpact" 
              placeholder="Enter new business impact"
              @keyup.enter.prevent="addNewBusinessImpact"
              autofocus
            >
          </div>
          <div class="risk-modal-actions">
            <button type="button" class="risk-cancel-btn" @click.prevent="showAddImpactModal = false">Cancel</button>
            <button type="submit" class="risk-add-btn" :disabled="!newBusinessImpact.trim()">
              Add Impact
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Add Category Modal -->
    <div v-if="showAddCategoryModal" class="risk-modal-overlay" @click.self="showAddCategoryModal = false">
      <div class="risk-modal-content" @click.stop>
        <h3>Add New Category</h3>
        <form @submit.prevent="addNewCategory" class="risk-modal-form">
          <div class="risk-modal-form-group">
            <label>Category Name</label>
            <input 
              type="text" 
              v-model="newCategory" 
              placeholder="Enter new category"
              @keyup.enter.prevent="addNewCategory"
              autofocus
            >
          </div>
          <div class="risk-modal-actions">
            <button type="button" class="risk-cancel-btn" @click.prevent="showAddCategoryModal = false">Cancel</button>
            <button type="submit" class="risk-add-btn" :disabled="!newCategory.trim()">
              Add Category
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Tailoring Risk Form (shown only in tailoring mode) -->
    <div v-if="creationMode === 'tailoring'" class="risk-tailoring-container">
      <TailoringRisk />
    </div>
  </div>
</template>

<script>
import './CreateRisk.css'
import { useRouter, useRoute } from 'vue-router'
import { SelectInput, NumberInput, TextInput, TextareaInput } from '@/components/inputs'
import { PopupModal } from '@/modules/popup'
import TailoringRisk from '@/components/Risk/TailoringRisk.vue'
import { API_ENDPOINTS, axiosInstance } from '../../config/api.js'
import consentService from '@/services/consentService.js'
import { CONSENT_ACTIONS } from '@/utils/consentManager.js'
// import AccessUtils from '@/utils/accessUtils';







export default {
  name: 'CreateRisk',
  components: {
    SelectInput,
    NumberInput,
    TextInput,
    TextareaInput,
    PopupModal,
    TailoringRisk
  },
  data() {
    return {
      newRisk: {
        ComplianceId: null,
        Criticality: '',
        PossibleDamage: '',
        Category: '',
        RiskDescription: '',
        RiskLikelihood: 1,
        RiskImpact: 1,
        RiskExposureRating: 1,
        RiskPriority: '',
        RiskMitigation: '',
        RiskTitle: '',
        RiskType: 'Current',
        BusinessImpact: ''
      },
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

      // New properties for compliance dropdown
      compliances: [],
      filteredCompliances: [],
      complianceSearchQuery: '',
      showComplianceDropdown: false,
      loadingCompliances: false,
      selectedComplianceIdText: '',
      
      showSuccessMessage: false,
      sourceRiskId: null,
      isLoadingSourceRisk: false,
      creationMode: 'manual', // 'manual', 'ai', 'tailoring'
      aiInput: {
        title: '',
        description: ''
      },
      isGeneratingAi: false,
      aiSuggestionGenerated: false,
      incidentId: null,
      // Store justifications separately for tooltip display
      riskJustifications: {
        likelihood: '',
        impact: ''
      },
      
      // Risk Mitigation properties
      mitigationForm: {
        actions: ['']
      },
      riskMitigationJson: JSON.stringify({}),
      riskMitigationActions: [],
      
      // Options for select inputs
      criticalityOptions: [
        { value: 'Critical', label: 'Critical' },
        { value: 'High', label: 'High' },
        { value: 'Medium', label: 'Medium' },
        { value: 'Low', label: 'Low' }
      ],
      priorityOptions: [
        { value: 'High', label: 'High' },
        { value: 'Medium', label: 'Medium' },
        { value: 'Low', label: 'Low' }
      ],
      riskTypeOptions: [
        { value: 'Current', label: 'Current' },
        { value: 'Emerging', label: 'Emerging' },
        { value: 'Residual', label: 'Residual' },
        { value: 'Inherent', label: 'Inherent' },
        { value: 'Accepted', label: 'Accepted' }
      ]
    }
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    return { router, route }
  },
  computed: {
    filteredBusinessImpacts() {
      if (!this.businessImpactSearch) {
        return this.businessImpacts;
      }
      const search = this.businessImpactSearch.toLowerCase();
      return this.businessImpacts.filter(impact => 
        impact.value.toLowerCase().includes(search)
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
    }
  },
  mounted() {
    // Initialize Risk Exposure Rating
    this.calculateRiskExposureRating();
    
    // Check if we have a source risk ID from the query parameters
    if (this.route.query.source_risk_id) {
      this.sourceRiskId = this.route.query.source_risk_id
      this.loadSourceRiskData()
    }
    
    // Fetch business impacts
    this.fetchBusinessImpacts();
    
    // Fetch categories
    this.fetchCategories();
    
    // Check if a specific mode is requested via query parameter
    if (this.route.query.mode) {
      // Valid modes are 'manual', 'ai', and 'tailoring'
      const validModes = ['manual', 'ai', 'tailoring'];
      if (validModes.includes(this.route.query.mode)) {
        this.creationMode = this.route.query.mode;
        
        // If AI mode is requested and we have a source risk ID, fetch incident data for AI analysis
        if (this.creationMode === 'ai' && this.sourceRiskId) {
          this.fetchIncidentDataForAI();
        }
      }
    }
    
    // Fetch compliances for dropdown
    this.fetchCompliances();
    
    // Add click outside listener to close dropdowns
    document.addEventListener('click', this.handleClickOutside);
  },
  beforeUnmount() {
    // Remove click outside listener
    document.removeEventListener('click', this.handleClickOutside);
  },
  methods: {
    // Add sendPushNotification method
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

    // Security utility methods without external dependencies
    sanitizeHTML(html) {
      if (!html) return '';
      return html
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    },
    
    sanitizeInput(input) {
      if (!input) return '';
      return input.replace(/[<>]/g, '');
    },
    
    encodeQueryParam(param) {
      return param ? encodeURIComponent(param) : '';
    },

    // Modified fetchCompliances to use proper async/await
    async fetchCompliances() {
      this.loadingCompliances = true;
      
      try {
        const API_ENDPOINT = API_ENDPOINTS.COMPLIANCES_FOR_DROPDOWN(this.encodeQueryParam(this.complianceSearchQuery));
        
        const response = await axiosInstance.get(API_ENDPOINT, {
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        // Sanitize the received data
        this.compliances = response.data.map(compliance => ({
          ...compliance,
          ComplianceItemDescription: this.sanitizeHTML(compliance.ComplianceItemDescription),
          PossibleDamage: this.sanitizeHTML(compliance.PossibleDamage)
        }));
        
        this.filteredCompliances = [...this.compliances];
        this.loadingCompliances = false;
        
        if (this.newRisk.ComplianceId) {
          this.updateSelectedComplianceIdText();
        }
      } catch (error) {
        console.error('Error fetching compliances:', error);
        this.loadingCompliances = false;
        this.compliances = [];
        this.filteredCompliances = [];
        this.$popup.error('Failed to fetch compliances. Please try again.');
        
        // Send push notification for compliance fetch failure
        this.sendPushNotification({
          title: 'Compliance Data Fetch Failed',
          message: 'Failed to fetch compliance data for risk creation. Please try again.',
          category: 'risk',
          priority: 'medium',
          user_id: 'default_user'
        });
      }
    },

    filterCompliances() {
      if (!this.complianceSearchQuery) {
        this.filteredCompliances = [...this.compliances];
        return;
      }
      
      const query = this.complianceSearchQuery.toLowerCase();
      this.filteredCompliances = this.compliances.filter(compliance => 
        (compliance.ComplianceId && compliance.ComplianceId.toString().includes(query)) ||
        (compliance.ComplianceItemDescription && compliance.ComplianceItemDescription.toLowerCase().includes(query)) ||
        (compliance.Criticality && compliance.Criticality.toLowerCase().includes(query)) ||
        (compliance.PossibleDamage && compliance.PossibleDamage.toLowerCase().includes(query))
      );
    },

    selectCompliance(compliance) {
      this.newRisk.ComplianceId = compliance.ComplianceId;
      this.selectedComplianceIdText = `Compliance ID: ${compliance.ComplianceId}`;
      this.showComplianceDropdown = false;
      
      // Optionally pre-fill other fields based on the selected compliance
      if (compliance.Criticality) this.newRisk.Criticality = compliance.Criticality;
      if (compliance.PossibleDamage) this.newRisk.PossibleDamage = compliance.PossibleDamage;
    },

    toggleComplianceDropdown(event) {
      if (event) {
        event.stopPropagation();
      }
      this.showComplianceDropdown = !this.showComplianceDropdown;
      if (this.showComplianceDropdown) {
        this.complianceSearchQuery = '';
        this.filterCompliances();
        // Close other dropdowns
        this.showBusinessImpactDropdown = false;
        this.showCategoryDropdown = false;
      }
    },

    updateSelectedComplianceIdText() {
      if (this.newRisk.ComplianceId) {
        const selectedCompliance = this.compliances.find(compliance => compliance.ComplianceId === parseInt(this.newRisk.ComplianceId));
        if (selectedCompliance) {
          this.selectedComplianceIdText = `Compliance ID: ${selectedCompliance.ComplianceId}`;
        } else {
          this.selectedComplianceIdText = `Compliance ID: ${this.newRisk.ComplianceId}`;
        }
      } else {
        this.selectedComplianceIdText = '';
      }
    },

    truncateText(text, maxLength) {
      if (!text) return '';
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },

    calculateRiskExposureRating() {
      // Get the current values of RiskLikelihood, RiskImpact, and multipliers
      const likelihood = parseInt(this.newRisk.RiskLikelihood) || 1;
      const impact = parseInt(this.newRisk.RiskImpact) || 1;
      const multiplierX = this.newRisk.RiskMultiplierX !== null && this.newRisk.RiskMultiplierX !== undefined && this.newRisk.RiskMultiplierX !== '' 
        ? parseInt(this.newRisk.RiskMultiplierX) : 1; // Default to 1 (0.1) only if not provided
      const multiplierY = this.newRisk.RiskMultiplierY !== null && this.newRisk.RiskMultiplierY !== undefined && this.newRisk.RiskMultiplierY !== '' 
        ? parseInt(this.newRisk.RiskMultiplierY) : 1; // Default to 1 (0.1) only if not provided
      
      // Calculate the Risk Exposure Rating using the new formula
      // Risk Impact * (X/10) * Risk Likelihood * (Y/10) = Risk Exposure Rating
      const calculatedValue = impact * (multiplierX / 10) * likelihood * (multiplierY / 10);
      this.newRisk.RiskExposureRating = Math.round(calculatedValue * 100) / 100; // Round to 2 decimal places
    },

    loadSourceRiskData() {
      if (!this.sourceRiskId) return
      
      this.isLoadingSourceRisk = true
      
      // Fetch the source risk instance data
              axiosInstance.get(API_ENDPOINTS.RISK_INSTANCE(this.sourceRiskId))
        .then(response => {
          console.log('Source risk data loaded:', response.data)
          // Pre-fill form with relevant data from the source risk
          const sourceRisk = response.data
          
          // Store the incident ID for later use
          this.incidentId = sourceRisk.IncidentId
          
          // Map the fields from source risk to the new risk form
          // Only copy over fields that make sense to share between risks
          if (sourceRisk.ComplianceId) this.newRisk.ComplianceId = sourceRisk.ComplianceId
          if (sourceRisk.Category) this.newRisk.Category = sourceRisk.Category
          if (sourceRisk.RiskTitle) this.newRisk.RiskTitle = sourceRisk.RiskTitle
          if (sourceRisk.RiskDescription) this.newRisk.RiskDescription = sourceRisk.RiskDescription
          
          // Handle risk mitigation actions if available
          if (sourceRisk.RiskMitigation) {
            try {
              const mitigation = typeof sourceRisk.RiskMitigation === 'string'
                ? JSON.parse(sourceRisk.RiskMitigation)
                : sourceRisk.RiskMitigation;
              
              // Convert numbered object to array for UI
              let actionsArr = [];
              if (mitigation && typeof mitigation === 'object' && !Array.isArray(mitigation)) {
                // Only use keys that are numbers (as strings)
                const keys = Object.keys(mitigation).filter(k => /^\d+$/.test(k));
                actionsArr = keys.sort((a, b) => parseInt(a) - parseInt(b)).map(k => this.sanitizeInput(mitigation[k]));
              }
              
              this.mitigationForm.actions = actionsArr.length > 0 ? actionsArr : [''];
              this.updateMitigationJson();
            } catch (e) {
              console.error('Error parsing risk mitigation:', e);
              this.mitigationForm.actions = [''];
              this.riskMitigationJson = JSON.stringify({});
            }
          }
          
          // Don't copy over instance-specific fields like IDs, ratings, etc.
          
          this.isLoadingSourceRisk = false
          
          // If in AI mode, fetch incident data for AI analysis
          if (this.creationMode === 'ai' && this.incidentId) {
            this.fetchIncidentDataForAI()
          }
        })
        .catch(error => {
          console.error('Error loading source risk data:', error)
          this.isLoadingSourceRisk = false
          // Show an error message or handle the error as needed
        })
    },

    fetchIncidentDataForAI() {
      if (!this.incidentId) {
        console.error('No incident ID available for AI analysis')
        return
      }
      
      this.isGeneratingAi = true
      console.log(`Fetching incident data for ID: ${this.incidentId}`)
      
      // Fetch the incident data
              axiosInstance.get(API_ENDPOINTS.INCIDENT(this.incidentId), {
        timeout: 80000 // Increased timeout to 80000ms to prevent timeout errors
      })
        .then(response => {
          const incident = response.data
          console.log('Incident data loaded:', incident)
          
          // Set the AI input fields with incident data
          this.aiInput.title = incident.Title || ''
          this.aiInput.description = incident.Description || ''
          
          // Automatically generate AI suggestion if we have the data
          if (this.aiInput.title || this.aiInput.description) {
            this.generateAiSuggestion()
          } else {
            this.isGeneratingAi = false
            console.warn('Incident data missing title or description')
          }
        })
        .catch(error => {
          console.error('Error fetching incident data:', error)
          this.isGeneratingAi = false
        })
    },

    setCreationMode(mode) {
      this.creationMode = mode
      
      // Update URL query parameter to reflect the current mode
      this.router.replace({
        query: { 
          ...this.route.query,
          mode: mode
        }
      });
      
      if (mode === 'manual') {
        // Reset AI-related data when switching to manual mode
        this.aiSuggestionGenerated = false
        // Clear AI justifications when switching to manual mode
        this.riskJustifications = {
          likelihood: '',
          impact: ''
        }
      } else if (mode === 'ai' && this.incidentId) {
        // If switching to AI mode and we have an incident ID, fetch the data
        this.fetchIncidentDataForAI()
      }
    },

    generateAiSuggestion() {
      if (!this.aiInput.title && !this.aiInput.description) {
        this.$popup.warning('Please provide either a title or description for AI analysis.');
        
        // Send push notification for AI analysis warning
        this.sendPushNotification({
          title: 'AI Analysis Warning',
          message: 'Please provide either a title or description for AI analysis.',
          category: 'risk',
          priority: 'medium',
          user_id: 'default_user'
        });
        return;
      }
      
      this.isGeneratingAi = true
      
      // Prepare the data for analysis - use at least one field if the other is missing
      const analysisData = {
        title: this.aiInput.title || 'Untitled Incident',
        description: this.aiInput.description || this.aiInput.title || 'No description available'
      }
      
      console.log('Sending to AI analysis:', analysisData)
      
      // Call the backend API to analyze the incident
              axiosInstance.post(API_ENDPOINTS.ANALYZE_INCIDENT, analysisData, {
        timeout: 80000 // Increased timeout to 80000ms to prevent timeout errors
      })
        .then(response => {
          console.log('AI Analysis Response:', response.data)
          
          // Check if the response contains an error
          if (response.data.error) {
            throw new Error(response.data.error)
          }
          
          // Validate that we received AI-generated content
          if (response.data.riskLikelihoodJustification || response.data.riskImpactJustification) {
            console.log('✅ Using AI-generated justifications')
          } else {
            console.log('⚠️ No AI justifications found, might be using fallback')
          }
          
          // Map the AI response to the risk form fields
          this.mapAnalysisToForm(response.data)
          
          // Mark as generated so we show the form
          this.aiSuggestionGenerated = true
          this.isGeneratingAi = false
        })
        .catch(error => {
          console.error('Error analyzing incident:', error.response || error)
          
          this.isGeneratingAi = false
          
          // Show a more detailed error message
          let errorMessage = 'Failed to generate AI suggestion.'
          
          if (error.message) {
            errorMessage = error.message
          } else if (error.response && error.response.data) {
            if (error.response.data.error) {
              errorMessage = error.response.data.error
            } else if (typeof error.response.data === 'object') {
              errorMessage += ' Error: ' + JSON.stringify(error.response.data)
            } else {
              errorMessage += ' Error: ' + error.response.data
            }
          }
          
          // Send push notification for AI analysis failure
          this.sendPushNotification({
            title: 'AI Analysis Failed',
            message: `Failed to generate AI suggestion: ${errorMessage}`,
            category: 'risk',
            priority: 'high',
            user_id: 'default_user'
          });
          
          // Show error message with options
          this.$popup.confirm(
            errorMessage + '\n\nWould you like to try again with different input?',
            'AI Analysis Failed',
            () => {
              // User chose to try again - do nothing, let them modify input
            },
            () => {
              // User chose to switch to manual mode
              this.creationMode = 'manual'
              this.aiSuggestionGenerated = false
            }
          )
        })
    },

    mapAnalysisToForm(analysis) {
      console.log('Mapping analysis to form:', analysis)
      
      // Map criticality (convert from text to the dropdown values if needed)
      if (analysis.criticality) {
        const criticalityMap = {
          'Severe': 'Critical',
          'Significant': 'High',
          'Moderate': 'Medium',
          'Minor': 'Low'
        }
        this.newRisk.Criticality = criticalityMap[analysis.criticality] || analysis.criticality
      }
      
      // Map possible damage
      this.newRisk.PossibleDamage = analysis.possibleDamage || ''
      
      // Map category
      this.newRisk.Category = analysis.category || ''
      
      // Map risk description
      this.newRisk.RiskDescription = analysis.riskDescription || ''
      
      // Map risk title from AI input title
      this.newRisk.RiskTitle = this.aiInput.title || ''
      
      // Map risk likelihood (now expects integer 1-10)
      if (analysis.riskLikelihood) {
        this.newRisk.RiskLikelihood = analysis.riskLikelihood.toString()
        // Store the AI justification for likelihood
        this.riskJustifications.likelihood = analysis.riskLikelihoodJustification || ''
        console.log('AI Likelihood Justification:', this.riskJustifications.likelihood)
      }
      
      // Map risk impact (now expects integer 1-10)
      if (analysis.riskImpact) {
        this.newRisk.RiskImpact = analysis.riskImpact.toString()
        // Store the AI justification for impact
        this.riskJustifications.impact = analysis.riskImpactJustification || ''
        console.log('AI Impact Justification:', this.riskJustifications.impact)
      }
      
      // Map risk exposure rating - calculate as likelihood * impact
      const likelihood = parseFloat(this.newRisk.RiskLikelihood) || 5.0
      const impact = parseFloat(this.newRisk.RiskImpact) || 5.0
      this.newRisk.RiskExposureRating = (likelihood * impact).toFixed(1)
      
      console.log(`Risk Exposure Rating calculated: ${likelihood} × ${impact} = ${this.newRisk.RiskExposureRating}`)
      
      // Ensure the exposure rating is properly calculated
      this.calculateRiskExposureRating()
      
      // Map risk priority
      if (analysis.riskPriority) {
        const priorityMap = {
          'P0': 'Critical',
          'P1': 'High',
          'P2': 'Medium',
          'P3': 'Low'
        }
        this.newRisk.RiskPriority = priorityMap[analysis.riskPriority] || 'Medium'
      }
      
      // Map risk mitigation
      if (analysis.riskMitigation && Array.isArray(analysis.riskMitigation)) {
        // Convert array of mitigation actions to our actions array
        this.mitigationForm.actions = analysis.riskMitigation.filter(action => action && action.trim() !== '');
        
        // Ensure we have at least one action field (even if empty)
        if (this.mitigationForm.actions.length === 0) {
          this.mitigationForm.actions = [''];
        }
        
        // Update the JSON representation
        this.updateMitigationJson();
      }
      
      // Map business impact from the description
      this.newRisk.BusinessImpact = this.aiInput.description || ''
      
      // Map risk type based on category
      this.newRisk.RiskType = analysis.category || ''
      
      // Auto-generate a compliance ID if not already set
      if (!this.newRisk.ComplianceId && this.incidentId) {
        this.newRisk.ComplianceId = this.incidentId
      }
    },

    resetForm() {
      this.newRisk = {
        ComplianceId: null,
        Criticality: '',
        PossibleDamage: '',
        Category: '',
        RiskDescription: '',
        RiskLikelihood: 1,
        RiskImpact: 1,
        RiskExposureRating: 1,
        RiskMultiplierX: 1, // Default to 1 (0.1)
        RiskMultiplierY: 1, // Default to 1 (0.1)
        RiskPriority: '',
        RiskMitigation: '',
        RiskTitle: '',
        RiskType: 'Current',
        BusinessImpact: ''
      }
      
      // Reset selected compliance ID text
      this.selectedComplianceIdText = '';
      
      // Calculate initial Risk Exposure Rating
      this.calculateRiskExposureRating();
      
      // Reset creation mode to manual
      this.setCreationMode('manual');
      
      // Reset AI-related data
      this.aiSuggestionGenerated = false
      this.aiInput = {
        title: '',
        description: ''
      }
      
      // Reset justifications
      this.riskJustifications = {
        likelihood: '',
        impact: ''
      }
      
      // Clear any existing tooltips
      console.log('Reset AI justifications')
      
      // Reset category selection
      this.selectedCategory = ''

      // Reset Risk Mitigation form
      this.mitigationForm.actions = ['']
      this.riskMitigationJson = JSON.stringify({})
      this.riskMitigationActions = []
    },

    // Business Impact Methods
    async fetchBusinessImpacts() {
      try {
        const response = await axiosInstance.get(API_ENDPOINTS.BUSINESS_IMPACTS);
        if (response.data.status === 'success') {
          this.businessImpacts = response.data.data;
        }
      } catch (error) {
        console.error('Error fetching business impacts:', error);
      }
    },

    toggleBusinessImpactDropdown(event) {
      if (event) {
        event.stopPropagation();
      }
      this.showBusinessImpactDropdown = !this.showBusinessImpactDropdown;
      if (this.showBusinessImpactDropdown) {
        this.businessImpactSearch = '';
        // Close other dropdowns
        this.showCategoryDropdown = false;
        this.showComplianceDropdown = false;
      }
    },

    toggleBusinessImpact(impact) {
      const index = this.selectedBusinessImpacts.findIndex(i => i.id === impact.id);
      if (index === -1) {
        this.selectedBusinessImpacts.push(impact);
      } else {
        this.selectedBusinessImpacts.splice(index, 1);
      }
      this.newRisk.BusinessImpact = this.selectedBusinessImpacts.map(i => i.value).join(', ');
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
        
        const response = await axiosInstance.post(API_ENDPOINTS.ADD_BUSINESS_IMPACT, {
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
        
        // Send push notification for business impact addition failure
        this.sendPushNotification({
          title: 'Business Impact Addition Failed',
          message: `Failed to add new business impact: ${error.response?.data?.message || error.message}`,
          category: 'risk',
          priority: 'medium',
          user_id: 'default_user'
        });
      }
    },

    // Category Methods
    async fetchCategories() {
      try {
        const response = await axiosInstance.get(API_ENDPOINTS.RISK_CATEGORIES);
        if (response.data.status === 'success') {
          this.categories = response.data.data;
        }
      } catch (error) {
        console.error('Error fetching categories:', error);
      }
    },

    toggleCategoryDropdown(event) {
      if (event) {
        event.stopPropagation();
      }
      this.showCategoryDropdown = !this.showCategoryDropdown;
      if (this.showCategoryDropdown) {
        this.categorySearch = '';
        // Close other dropdowns
        this.showBusinessImpactDropdown = false;
        this.showComplianceDropdown = false;
      }
    },

    selectCategory(category) {
      this.selectedCategory = category.value;
      this.newRisk.Category = category.value;
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
        
        const response = await axiosInstance.post(API_ENDPOINTS.ADD_RISK_CATEGORY, {
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
        
        // Send push notification for category addition failure
        this.sendPushNotification({
          title: 'Category Addition Failed',
          message: `Failed to add new category: ${error.response?.data?.message || error.message}`,
          category: 'risk',
          priority: 'medium',
          user_id: 'default_user'
        });
      }
    },

    // Risk Mitigation Methods
    updateMitigationJson() {
      // Convert actions array to numbered object
      const actionsObj = {};
      this.mitigationForm.actions.forEach((action, idx) => {
        if (action.trim() !== '') {
          actionsObj[(idx + 1).toString()] = action;
        }
      });
      this.riskMitigationJson = JSON.stringify(actionsObj, null, 2);
      this.riskMitigationActions = [...this.mitigationForm.actions];
    },

    addAction() {
      this.mitigationForm.actions.push('');
      this.updateMitigationJson();
    },

    removeAction(index) {
      this.mitigationForm.actions.splice(index, 1);
      this.updateMitigationJson();
    },

    // Modified submitRisk to use proper async/await
    async submitRisk() {
      // Check consent before proceeding
      try {
        const canProceed = await consentService.checkAndRequestConsent(
          CONSENT_ACTIONS.CREATE_RISK
        );

        if (!canProceed) {
          console.log('Risk creation cancelled by user (consent declined)');
          this.$popup.warning('Risk creation cancelled - consent is required');
          return;
        }
      } catch (consentError) {
        console.error('Error checking consent:', consentError);
        // Continue with risk creation if consent check fails (fail-open)
      }

      // Update mitigation JSON before submission
      this.updateMitigationJson();
      
      // Validate data before submission
      const validationErrors = this.validateRiskData();
      if (Object.keys(validationErrors).length > 0) {
        Object.entries(validationErrors).forEach(([field, error]) => {
          this.$popup.error(`${field}: ${error}`);
          
          // Send push notification for validation errors
          this.sendPushNotification({
            title: 'Risk Validation Error',
            message: `Validation error in ${field}: ${error}`,
            category: 'risk',
            priority: 'high',
            user_id: 'default_user'
          });
        });
        return;
      }

      // Parse mitigation JSON
      let parsedMitigation = {};
      try {
        parsedMitigation = JSON.parse(this.riskMitigationJson);
      } catch (e) {
        this.$popup.error('Invalid Risk Mitigation format. Please try again.');
        return;
      }

      // Convert mitigation actions to a string format for the Risk model
      // The Risk model uses TextField for RiskMitigation, not JSONField
      const mitigationString = Object.values(parsedMitigation).join('\n');

      // Get consent config to include in request if consent was required
      let consentConfig = null;
      try {
        const { checkConsentRequired } = await import('@/utils/consentManager.js');
        const consentCheck = await checkConsentRequired(CONSENT_ACTIONS.CREATE_RISK);
        if (consentCheck.required && consentCheck.config) {
          consentConfig = consentCheck.config;
        }
      } catch (error) {
        console.error('Error getting consent config:', error);
      }

      // Sanitize data before submission
      const sanitizedRiskData = {
        ...this.newRisk,
        RiskTitle: this.sanitizeInput(this.newRisk.RiskTitle),
        RiskDescription: this.sanitizeInput(this.newRisk.RiskDescription),
        PossibleDamage: this.sanitizeInput(this.newRisk.PossibleDamage),
        RiskMitigation: mitigationString, // Use string format for Risk model
        BusinessImpact: this.selectedBusinessImpacts.map(i => this.sanitizeInput(i.value)).join(', '),
        RiskLikelihood: parseInt(this.newRisk.RiskLikelihood) || 1,
        RiskImpact: parseInt(this.newRisk.RiskImpact) || 1,
        RiskExposureRating: parseFloat(this.newRisk.RiskExposureRating) || 1,
      };

      // Include consent data if consent was required and accepted
      if (consentConfig) {
        sanitizedRiskData.consent_accepted = true;
        sanitizedRiskData.consent_config_id = consentConfig.config_id;
        sanitizedRiskData.framework_id = consentConfig.framework_id || localStorage.getItem('framework_id');
        console.log('📋 [Consent] Including consent data in request:', {
          consent_accepted: true,
          consent_config_id: consentConfig.config_id,
          framework_id: sanitizedRiskData.framework_id
        });
      }

      try {
        console.log('Submitting risk data:', sanitizedRiskData);
        
        const response = await axiosInstance.post(API_ENDPOINTS.RISKS, sanitizedRiskData, {
          headers: {
            'Content-Type': 'application/json'
          }
        });

        console.log('Risk created successfully:', response.data);
        this.resetForm();
        this.$popup.success('Risk created successfully!');
        
        // Send push notification for successful risk creation
        this.sendPushNotification({
          title: 'New Risk Created Successfully',
          message: `A new risk "${sanitizedRiskData.RiskTitle || 'Untitled Risk'}" has been created successfully.`,
          category: 'risk',
          priority: 'high',
          user_id: 'default_user'
        });
      } catch (error) {
        console.error('Error creating risk:', error);
        console.error('Error response data:', error.response?.data);
        console.error('Original risk data sent:', sanitizedRiskData);
        
        // Access denied errors are now handled globally by the HTTP interceptor
        // Only handle validation and other non-access errors here
        if (error.response && ![401, 403].includes(error.response.status)) {
          if (error.response.data.errors) {
            Object.entries(error.response.data.errors).forEach(([field, error]) => {
              this.$popup.error(`${field}: ${error}`);
              
              // Send push notification for field-specific errors
              this.sendPushNotification({
                title: 'Risk Creation Error',
                message: `Error in ${field}: ${error}`,
                category: 'risk',
                priority: 'high',
                user_id: 'default_user'
              });
            });
          } else {
            this.$popup.error('Failed to create risk. Please try again.');
            
            // Send push notification for general creation failure
            this.sendPushNotification({
              title: 'Risk Creation Failed',
              message: 'Failed to create risk. Please try again.',
              category: 'risk',
              priority: 'high',
              user_id: 'default_user'
            });
          }
        }
        // 401/403 errors are handled by the global interceptor
      }
    },

    validateRiskData() {
      const errors = {};
      
      // Validate Criticality
      if (this.newRisk.Criticality) {
        const allowedCriticality = ['Critical', 'High', 'Medium', 'Low'];
        if (!allowedCriticality.includes(this.newRisk.Criticality)) {
          errors.Criticality = `Must be one of: ${allowedCriticality.join(', ')}`;
        }
      }

      // Validate RiskPriority
      if (this.newRisk.RiskPriority) {
        const allowedPriority = ['High', 'Medium', 'Low'];
        if (!allowedPriority.includes(this.newRisk.RiskPriority)) {
          errors.RiskPriority = `Must be one of: ${allowedPriority.join(', ')}`;
        }
      }

      // Validate RiskType
      if (this.newRisk.RiskType) {
        const allowedRiskType = ['Current', 'Residual', 'Inherent', 'Emerging', 'Accept'];
        if (!allowedRiskType.includes(this.newRisk.RiskType)) {
          errors.RiskType = `Must be one of: ${allowedRiskType.join(', ')}`;
        }
      }

      // Validate RiskLikelihood
      const likelihood = parseInt(this.newRisk.RiskLikelihood);
      if (isNaN(likelihood) || likelihood < 1 || likelihood > 10) {
        errors.RiskLikelihood = 'Must be a number between 1 and 10';
      }

      // Validate RiskImpact
      const impact = parseInt(this.newRisk.RiskImpact);
      if (isNaN(impact) || impact < 1 || impact > 10) {
        errors.RiskImpact = 'Must be a number between 1 and 10';
      }

      // Validate required fields
      if (!this.newRisk.RiskTitle?.trim()) {
        errors.RiskTitle = 'Risk Title is required';
      }

      if (!this.newRisk.RiskDescription?.trim()) {
        errors.RiskDescription = 'Risk Description is required';
      }

      // Validate RiskMitigation (check if at least one non-empty action is present)
      const hasValidAction = this.mitigationForm.actions.some(action => action.trim() !== '');
      if (!hasValidAction) {
        errors.RiskMitigation = 'At least one mitigation action is required';
      }

      return errors;
    },

    // Handle click outside to close dropdowns
    handleClickOutside(event) {
      // Close business impact dropdown
      if (this.showBusinessImpactDropdown) {
        const businessImpactDropdown = document.querySelector('.risk-business-impact-dropdown');
        const businessImpactTrigger = document.querySelector('.risk-selected-impacts');
        if (businessImpactDropdown && 
            !businessImpactDropdown.contains(event.target) &&
            (!businessImpactTrigger || !businessImpactTrigger.contains(event.target))) {
          this.showBusinessImpactDropdown = false;
        }
      }
      
      // Close category dropdown
      if (this.showCategoryDropdown) {
        const categoryDropdown = document.querySelector('.risk-category-dropdown');
        const categoryTrigger = document.querySelector('.risk-selected-category');
        if (categoryDropdown && 
            !categoryDropdown.contains(event.target) &&
            (!categoryTrigger || !categoryTrigger.contains(event.target))) {
          this.showCategoryDropdown = false;
        }
      }
      
      // Close compliance dropdown
      if (this.showComplianceDropdown) {
        const complianceDropdown = document.querySelector('.risk-compliance-dropdown-container');
        if (complianceDropdown && 
            !complianceDropdown.contains(event.target)) {
          this.showComplianceDropdown = false;
        }
      }
    },

    // Handle tooltip interactions
    handleTooltipInteraction(event) {
      const tooltip = event.currentTarget.querySelector('.tooltip-content');
      if (tooltip) {
        // Add a small delay to prevent accidental triggers
        setTimeout(() => {
          tooltip.style.opacity = '1';
          tooltip.style.visibility = 'visible';
        }, 100);
      }
    },

    // Clear tooltip on mouse leave
    handleTooltipLeave(event) {
      const tooltip = event.currentTarget.querySelector('.tooltip-content');
      if (tooltip) {
        tooltip.style.opacity = '0';
        tooltip.style.visibility = 'hidden';
      }
    },
  }
}
</script>

<style lang="css" scoped>
/* Fix Compliance ID dropdown arrow */
.risk-compliance-dropdown-container .risk-dropdown-toggle {
  position: absolute !important;
  right: 8px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  height: 20px !important;
  width: 20px !important;
  font-size: 0.7rem !important;
  z-index: 2 !important;
}

.risk-compliance-dropdown-container .risk-dropdown-toggle i {
  font-size: 0.7rem !important;
  line-height: 1 !important;
}

.risk-compliance-dropdown-container input[type="text"] {
  padding-right: 32px !important;
}
</style>