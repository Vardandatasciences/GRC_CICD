<template>
  <div class="tailoring-risk-container">
    <!-- Add PopupModal component -->
    <PopupModal />
    
    <h2 class="tailoring-risk-title">Tailoring Risk</h2>
    
    
    <form @submit.prevent="saveRisk" class="tailoring-risk-form">
      <!-- Risk Selection Dropdown -->
      <div class="tailoring-risk-form-group tailoring-risk-id-container">
        <label><i class="fas fa-hashtag"></i> Select Existing Risk (Optional):</label>
        <div class="tailoring-risk-dropdown-container">
          <select v-model="selectedRiskId" @change="onRiskSelected" class="tailoring-risk-form-control">
            <option value="">Select a risk to edit...</option>
            <option 
              v-for="riskItem in allRisks" 
              :key="riskItem.RiskId" 
              :value="riskItem.RiskId"
            >
              ID: {{ riskItem.RiskId }} - {{ riskItem.RiskTitle }} ({{ riskItem.Criticality }})
            </option>
          </select>
        </div>
        <div class="tailoring-risk-helper-text">Choose an existing risk to use as a template for creating a new one</div>
      </div>
      
      <!-- Basic Risk Information -->
      <div class="tailoring-risk-form-row">
        <div class="tailoring-risk-form-group">
          <label><i class="fas fa-heading"></i> Risk Title:</label>
          <input type="text" v-model="risk.RiskTitle" class="tailoring-risk-form-control" />
          <div class="tailoring-risk-helper-text">Provide a brief, descriptive title for this risk</div>
        </div>
        
        <div class="tailoring-risk-form-group">
          <label><i class="fas fa-clipboard-check"></i> Compliance ID:</label>
          <input type="number" v-model="risk.ComplianceId" class="tailoring-risk-form-control" />
          <div class="tailoring-risk-helper-text">Enter the compliance framework identifier for this risk</div>
        </div>
      </div>
      
      <div class="tailoring-risk-form-row">
        <div class="tailoring-risk-form-group">
          <label><i class="fas fa-exclamation-triangle"></i> Criticality:</label>
          <select v-model="risk.Criticality" class="tailoring-risk-form-control">
            <option value="">Select Criticality</option>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
            <option value="Critical">Critical</option>
          </select>
          <div class="tailoring-risk-helper-text">Choose the severity level of this risk</div>
        </div>
        
        <div class="tailoring-risk-form-group">
          <label><i class="fas fa-tag"></i> Category:</label>
          <div class="tailoring-risk-category-container">
            <div class="tailoring-risk-category-dropdown">
              <div class="tailoring-risk-selected-category" @click="toggleCategoryDropdown">
                <span v-if="!selectedCategory">Select Category</span>
                <span v-else>{{ selectedCategory }}</span>
                <i class="fas fa-chevron-down"></i>
              </div>
              <div v-if="showCategoryDropdown" class="tailoring-risk-category-options">
                <div class="tailoring-risk-category-search">
                  <input 
                    type="text" 
                    v-model="categorySearch" 
                    placeholder="Search categories..."
                    @click.stop
                  >
                  <button type="button" class="tailoring-risk-add-category-btn" @click.stop.prevent="showAddCategoryModal = true">
                    <i class="fas fa-plus"></i> Add New
                  </button>
                </div>
                <div class="tailoring-risk-category-list">
                  <div 
                    v-for="category in filteredCategories" 
                    :key="category.id" 
                    class="tailoring-risk-category-item"
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
          <div class="tailoring-risk-helper-text">Categorize this risk for better organization and management</div>
        </div>
      </div>
      
      <div class="tailoring-risk-form-row">
        <div class="tailoring-risk-form-group">
          <label><i class="fas fa-list"></i> Risk Type:</label>
          <select v-model="risk.RiskType" class="tailoring-risk-form-control">
            <option value="">Select Risk Type</option>
            <option value="Current">Current</option>
            <option value="Residual">Residual</option>
            <option value="Inherent">Inherent</option>
            <option value="Emerging">Emerging</option>
            <option value="Accept">Accept</option>
          </select>
          <div class="tailoring-risk-helper-text">Classify the nature and timing of this risk</div>
        </div>
        
        <div class="tailoring-risk-form-group">
          <label><i class="fas fa-flag"></i> Risk Priority:</label>
          <select v-model="risk.RiskPriority" class="tailoring-risk-form-control">
            <option value="">Select Priority</option>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </select>
          <div class="tailoring-risk-helper-text">Set the priority level for risk treatment and response</div>
        </div>
      </div>
      
      <!-- Risk Assessment -->
      <div class="tailoring-risk-form-row">
        <div class="tailoring-risk-form-group">
          <label><i class="fas fa-bomb"></i> Risk Impact (1-10):</label>
          <input type="number" v-model.number="risk.RiskImpact" min="1" max="10" class="tailoring-risk-form-control" />
          <div class="tailoring-risk-helper-text">Rate the potential impact if this risk occurs (1=Minimal, 10=Severe)</div>
        </div>
        
        <div class="tailoring-risk-form-group">
          <label><i class="fas fa-chart-line"></i> Risk Likelihood (1-10):</label>
          <input type="number" v-model.number="risk.RiskLikelihood" min="1" max="10" class="tailoring-risk-form-control" />
          <div class="tailoring-risk-helper-text">Rate how likely this risk is to occur (1=Very Unlikely, 10=Very Likely)</div>
        </div>
      </div>
      
      <div class="tailoring-risk-form-row">
        <div class="tailoring-risk-form-group">
          <label><i class="fas fa-times"></i> Impact Multiplier (X) (1-10):</label>
          <input type="number" v-model.number="risk.RiskMultiplierX" min="1" max="10" class="tailoring-risk-form-control" />
          <div class="tailoring-risk-helper-text">Impact multiplier factor (default: 1)</div>
        </div>
        
        <div class="tailoring-risk-form-group">
          <label><i class="fas fa-times"></i> Likelihood Multiplier (Y) (1-10):</label>
          <input type="number" v-model.number="risk.RiskMultiplierY" min="1" max="10" class="tailoring-risk-form-control" />
          <div class="tailoring-risk-helper-text">Likelihood multiplier factor (default: 1)</div>
        </div>
      </div>
      
      <div class="tailoring-risk-form-row">
        <div class="tailoring-risk-form-group">
          <label><i class="fas fa-tachometer-alt"></i> Risk Exposure Rating:</label>
          <input type="number" v-model.number="risk.RiskExposureRating" class="tailoring-risk-form-control" readonly />
          <div class="tailoring-risk-helper-text">Automatically calculated as Impact × (X/10) × Likelihood × (Y/10)</div>
        </div>

        <div class="tailoring-risk-form-group">
          <label><i class="fas fa-building"></i> Business Impact:</label>
          <div class="tailoring-risk-business-impact-container">
            <div class="tailoring-risk-business-impact-dropdown">
              <div class="tailoring-risk-selected-impacts" @click="toggleBusinessImpactDropdown">
                <span v-if="selectedBusinessImpacts.length === 0">Select Business Impacts</span>
                <span v-else>{{ selectedBusinessImpacts.length }} impact(s) selected</span>
                <i class="fas fa-chevron-down"></i>
              </div>
              <div v-if="showBusinessImpactDropdown" class="tailoring-risk-business-impact-options">
                <div class="tailoring-risk-business-impact-search">
                  <input 
                    type="text" 
                    v-model="businessImpactSearch" 
                    placeholder="Search impacts..."
                    @click.stop
                  >
                  <button type="button" class="tailoring-risk-add-impact-btn" @click.stop.prevent="showAddImpactModal = true">
                    <i class="fas fa-plus"></i> Add New
                  </button>
                </div>
                <div class="tailoring-risk-business-impact-list">
                  <div 
                    v-for="impact in filteredBusinessImpacts" 
                    :key="impact.id" 
                    class="tailoring-risk-business-impact-item"
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
            <div class="tailoring-risk-selected-impacts-display">
              <div 
                v-for="impact in selectedBusinessImpacts" 
                :key="impact.id" 
                class="tailoring-risk-selected-impact-tag"
              >
                {{ impact.value }}
                <i class="fas fa-times" @click="toggleBusinessImpact(impact)"></i>
              </div>
            </div>
          </div>
          <div class="tailoring-risk-helper-text">Select the business areas that would be affected by this risk</div>
        </div>
      </div>
      
      <!-- Add Business Impact Modal -->
      <div v-if="showAddImpactModal" class="tailoring-risk-modal-overlay" @click.self="showAddImpactModal = false">
        <div class="tailoring-risk-modal-content" @click.stop>
          <h3>Add New Business Impact</h3>
          <form @submit.prevent="addNewBusinessImpact" class="tailoring-risk-modal-form">
            <div class="tailoring-risk-modal-form-group">
              <label>Impact Description</label>
              <input 
                type="text" 
                v-model="newBusinessImpact" 
                placeholder="Enter new business impact"
                @keyup.enter.prevent="addNewBusinessImpact"
                autofocus
              >
            </div>
            <div class="tailoring-risk-modal-actions">
              <button type="button" class="tailoring-risk-cancel-btn" @click.prevent="showAddImpactModal = false">Cancel</button>
              <button type="submit" class="tailoring-risk-add-btn" :disabled="!newBusinessImpact.trim()">
                Add Impact
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Add Category Modal -->
      <div v-if="showAddCategoryModal" class="tailoring-risk-modal-overlay" @click.self="showAddCategoryModal = false">
        <div class="tailoring-risk-modal-content" @click.stop>
          <h3>Add New Category</h3>
          <form @submit.prevent="addNewCategory" class="tailoring-risk-modal-form">
            <div class="tailoring-risk-modal-form-group">
              <label>Category Name</label>
              <input 
                type="text" 
                v-model="newCategory" 
                placeholder="Enter new category"
                @keyup.enter.prevent="addNewCategory"
                autofocus
              >
            </div>
            <div class="tailoring-risk-modal-actions">
              <button type="button" class="tailoring-risk-cancel-btn" @click.prevent="showAddCategoryModal = false">Cancel</button>
              <button type="submit" class="tailoring-risk-add-btn" :disabled="!newCategory.trim()">
                Add Category
              </button>
            </div>
          </form>
        </div>
      </div>
        
      <div class="tailoring-risk-form-row">
        <div class="tailoring-risk-form-group">
          <label><i class="fas fa-exclamation-circle"></i> Possible Damage:</label>
          <textarea v-model="risk.PossibleDamage" rows="4" class="tailoring-risk-form-control"></textarea>
          <div class="tailoring-risk-helper-text">Describe the potential damage or consequences if this risk materializes</div>
        </div>

        <div class="tailoring-risk-form-group">
          <label><i class="fas fa-align-left"></i> Risk Description:</label>
          <textarea v-model="risk.RiskDescription" rows="4" class="tailoring-risk-form-control"></textarea>
          <div class="tailoring-risk-helper-text">Provide a detailed description of the risk, its context, and contributing factors</div>
        </div>

        <div class="tailoring-risk-form-group">
          <label><i class="fas fa-shield-alt"></i> Risk Mitigation:</label>
          <div class="tailoring-risk-mitigation-form">
            <div class="tailoring-risk-mitigation-input-group">
              <label>Actions</label>
              <div v-for="(action, index) in mitigationForm.actions" :key="index" class="tailoring-risk-mitigation-action-item">
                <input 
                  type="text" 
                  v-model="mitigationForm.actions[index]" 
                  class="tailoring-risk-form-input"
                  @input="updateMitigationJson"
                >
                <button 
                  type="button" 
                  class="tailoring-risk-remove-action" 
                  @click="removeAction(index)"
                >
                  <i class="fas fa-times"></i>
                </button>
              </div>
              <button 
                type="button" 
                class="tailoring-risk-add-action" 
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
          <div class="tailoring-risk-helper-text">Add specific actions to mitigate or eliminate this risk</div>
        </div>
      </div>
      
      
      
      <!-- Form Actions -->
      <div class="tailoring-risk-form-actions">
        <button type="button" @click="resetForm" class="tailoring-risk-btn-secondary">
          <i class="fas fa-undo"></i> Reset
        </button>
        <button type="submit" class="tailoring-risk-btn-primary">
          <i class="fas fa-save"></i> Save Risk
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue';
import axios from 'axios';
import './TailoringRisk.css';
import { useRoute } from 'vue-router';
import { PopupModal } from '@/modules/popup';
import { popupService } from '@/modules/popup';
import { API_ENDPOINTS } from '@/config/api';

export default {
  name: 'TailoringRisk',
  components: {
    PopupModal
  },
  setup() {
    const route = useRoute();

    // Reactive data
    const risk = ref({
      RiskTitle: '',
      ComplianceId: '',
      Criticality: '',
      Category: '',
      RiskType: '',
      RiskPriority: '',
      RiskImpact: 1,
      RiskLikelihood: 1,
      RiskExposureRating: 1,
      RiskMultiplierX: 1, // Default to 1 (0.1)
      RiskMultiplierY: 1, // Default to 1 (0.1)
      BusinessImpact: '',
      PossibleDamage: '',
      RiskDescription: '',
      RiskMitigation: ''
    });
    
    const allRisks = ref([]);
    const selectedRiskId = ref('');

    // Business Impact related data
    const businessImpacts = ref([]);
    const selectedBusinessImpacts = ref([]);
    const showBusinessImpactDropdown = ref(false);
    const businessImpactSearch = ref('');
    const showAddImpactModal = ref(false);
    const newBusinessImpact = ref('');

    // Category dropdown properties
    const categories = ref([]);
    const selectedCategory = ref('');
    const showCategoryDropdown = ref(false);
    const categorySearch = ref('');
    const showAddCategoryModal = ref(false);
    const newCategory = ref('');

    // Mitigation form data
    const mitigationForm = ref({
      actions: ['']
    });
    const riskMitigationJson = ref('');

    // Computed properties
    const pageTitle = computed(() => selectedRiskId.value ? 'Create Risk Based on Existing Risk' : 'Create New Risk');
    
    const filteredBusinessImpacts = computed(() => {
      if (!businessImpactSearch.value) {
        return businessImpacts.value;
      }
      const search = businessImpactSearch.value.toLowerCase();
      return businessImpacts.value.filter(impact => 
        impact.value.toLowerCase().includes(search)
      );
    });

    const filteredCategories = computed(() => {
      if (!categorySearch.value) {
        return categories.value;
      }
      const search = categorySearch.value.toLowerCase();
      return categories.value.filter(category => 
        category.value.toLowerCase().includes(search)
      );
    });

    // Watch for risk impact, likelihood, and multiplier changes to calculate exposure rating
    watch([() => risk.value.RiskImpact, () => risk.value.RiskLikelihood, () => risk.value.RiskMultiplierX, () => risk.value.RiskMultiplierY], () => {
      const impact = risk.value.RiskImpact || 1;
      const likelihood = risk.value.RiskLikelihood || 1;
      const multiplierX = risk.value.RiskMultiplierX !== null && risk.value.RiskMultiplierX !== undefined && risk.value.RiskMultiplierX !== '' 
        ? risk.value.RiskMultiplierX : 1; // Default to 1 (0.1) only if not provided
      const multiplierY = risk.value.RiskMultiplierY !== null && risk.value.RiskMultiplierY !== undefined && risk.value.RiskMultiplierY !== '' 
        ? risk.value.RiskMultiplierY : 1; // Default to 1 (0.1) only if not provided
      
      // Calculate the Risk Exposure Rating using the new formula
      // Risk Impact * (X/10) * Risk Likelihood * (Y/10) = Risk Exposure Rating
      const calculatedValue = impact * (multiplierX / 10) * likelihood * (multiplierY / 10);
      risk.value.RiskExposureRating = Math.round(calculatedValue * 100) / 100; // Round to 2 decimal places
    });

    // Methods
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

    const onRiskSelected = () => {
      if (selectedRiskId.value) {
        const selectedRisk = allRisks.value.find(r => r.RiskId == selectedRiskId.value);
        if (selectedRisk) {
          // Populate all fields with selected risk data
          Object.assign(risk.value, {
            RiskTitle: selectedRisk.RiskTitle || '',
            ComplianceId: selectedRisk.ComplianceId || '',
            Criticality: selectedRisk.Criticality || '',
            Category: selectedRisk.Category || '',
            RiskType: selectedRisk.RiskType || '',
            RiskPriority: selectedRisk.RiskPriority || '',
            RiskImpact: selectedRisk.RiskImpact || 1,
            RiskLikelihood: selectedRisk.RiskLikelihood || 1,
            RiskExposureRating: selectedRisk.RiskExposureRating || 1,
            // Convert multiplier values from 0.1-1.0 range (stored in DB) to 1-10 range (frontend expects)
            RiskMultiplierX: selectedRisk.RiskMultiplierX ? Math.round(selectedRisk.RiskMultiplierX * 10) : 1,
            RiskMultiplierY: selectedRisk.RiskMultiplierY ? Math.round(selectedRisk.RiskMultiplierY * 10) : 1,
            BusinessImpact: selectedRisk.BusinessImpact || '',
            PossibleDamage: selectedRisk.PossibleDamage || '',
            RiskDescription: selectedRisk.RiskDescription || '',
            RiskMitigation: selectedRisk.RiskMitigation || ''
          });
          
          // Parse business impacts if they exist
          if (selectedRisk.BusinessImpact) {
            parseBusinessImpacts(selectedRisk.BusinessImpact);
          }

          // Set selected category if it exists
          if (selectedRisk.Category) {
            selectedCategory.value = selectedRisk.Category;
          }

          // Parse mitigation actions if they exist
          if (selectedRisk.RiskMitigation) {
            try {
              // Check if it's already a JSON string
              if (typeof selectedRisk.RiskMitigation === 'string') {
                // Try to parse as JSON first
                try {
                  const parsed = JSON.parse(selectedRisk.RiskMitigation);
                  if (typeof parsed === 'object' && !Array.isArray(parsed)) {
                    // It's a numbered object, convert to array
                    const keys = Object.keys(parsed).filter(k => /^\d+$/.test(k));
                    mitigationForm.value.actions = keys.sort((a, b) => parseInt(a) - parseInt(b)).map(k => parsed[k]);
                  } else if (Array.isArray(parsed)) {
                    // It's already an array
                    mitigationForm.value.actions = parsed;
                  } else {
                    // It's a simple string, split by sentences or newlines
                    mitigationForm.value.actions = selectedRisk.RiskMitigation.split(/[.\n]/).filter(s => s.trim() !== '');
                  }
                } catch (jsonError) {
                  // If JSON parsing fails, treat as plain text and split by sentences or newlines
                  mitigationForm.value.actions = selectedRisk.RiskMitigation.split(/[.\n]/).filter(s => s.trim() !== '');
                }
              } else if (typeof selectedRisk.RiskMitigation === 'object') {
                // It's already an object, convert to array
                if (Array.isArray(selectedRisk.RiskMitigation)) {
                  mitigationForm.value.actions = selectedRisk.RiskMitigation;
                } else {
                  // It's a numbered object
                  const keys = Object.keys(selectedRisk.RiskMitigation).filter(k => /^\d+$/.test(k));
                  mitigationForm.value.actions = keys.sort((a, b) => parseInt(a) - parseInt(b)).map(k => selectedRisk.RiskMitigation[k]);
                }
              }
              
              // Ensure we have at least one action field
              if (mitigationForm.value.actions.length === 0) {
                mitigationForm.value.actions = [''];
              }
              
              updateMitigationJson();
            } catch (error) {
              console.error('Error parsing mitigation data:', error);
              mitigationForm.value.actions = [''];
              updateMitigationJson();
            }
          }
        }
      }
    };

    const parseBusinessImpacts = (impactString) => {
      if (!impactString) return;
      
      // Clear existing selected impacts
      selectedBusinessImpacts.value = [];
      
      // Split the string by commas and trim each value
      const impacts = impactString.split(',').map(impact => impact.trim());
      
      // For each impact, find it in the businessImpacts array or create a new one
      impacts.forEach(impactValue => {
        if (!impactValue) return;
        
        // Find existing impact
        const existingImpact = businessImpacts.value.find(
          impact => impact.value.toLowerCase() === impactValue.toLowerCase()
        );
        
        if (existingImpact) {
          // Add to selected if it exists
          selectedBusinessImpacts.value.push(existingImpact);
        } else {
          // Create a new impact with a temporary ID
          const newImpact = {
            id: `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            value: impactValue
          };
          businessImpacts.value.push(newImpact);
          selectedBusinessImpacts.value.push(newImpact);
        }
      });
    };

    const loadRisks = async () => {
      try {
        const response = await axios.get(API_ENDPOINTS.RISKS_FOR_DROPDOWN);
        allRisks.value = response.data?.risks || [];
        
        // If there's an ID in the route, select that risk
        if (route.params.id && route.params.id !== 'new') {
          selectedRiskId.value = route.params.id;
          onRiskSelected();
        }
      } catch (error) {
        console.error('Error loading risks:', error);
        // Use popup service instead of alert
        // Note: In Composition API, we need to access popup service through getCurrentInstance
        popupService.error('Failed to load risks. Please try again.');
        
        // Send push notification for risk loading failure
        sendPushNotification({
          title: 'Risk Loading Failed',
          message: 'Failed to load risks from the database. Please check your connection and try again.',
          category: 'risk',
          priority: 'high',
          user_id: 'default_user'
        });
      }
    };

    const fetchBusinessImpacts = async () => {
      try {
        const response = await axios.get(API_ENDPOINTS.BUSINESS_IMPACTS);
        if (response.data.status === 'success') {
          businessImpacts.value = response.data.data;
        }
      } catch (error) {
        console.error('Error fetching business impacts:', error);
      }
    };

    const toggleBusinessImpactDropdown = () => {
      showBusinessImpactDropdown.value = !showBusinessImpactDropdown.value;
      if (showBusinessImpactDropdown.value) {
        businessImpactSearch.value = '';
      }
    };

    const toggleBusinessImpact = (impact) => {
      const index = selectedBusinessImpacts.value.findIndex(i => i.id === impact.id);
      if (index === -1) {
        selectedBusinessImpacts.value.push(impact);
      } else {
        selectedBusinessImpacts.value.splice(index, 1);
      }
      risk.value.BusinessImpact = selectedBusinessImpacts.value.map(i => i.value).join(', ');
    };

    const isBusinessImpactSelected = (impact) => {
      return selectedBusinessImpacts.value.some(i => i.id === impact.id);
    };

    const addNewBusinessImpact = async () => {
      // Don't proceed if input is empty
      if (!newBusinessImpact.value.trim()) {
        return;
      }
      
      try {
        const response = await axios.post(API_ENDPOINTS.ADD_BUSINESS_IMPACT, {
          value: newBusinessImpact.value.trim()
        });
        
        if (response.data.status === 'success') {
          businessImpacts.value.push(response.data.data);
          toggleBusinessImpact(response.data.data);
          showAddImpactModal.value = false;
          newBusinessImpact.value = '';
        } else {
          throw new Error('Failed to add business impact: ' + (response.data.message || 'Unknown error'));
        }
      } catch (error) {
        console.error('Error adding new business impact:', error);
        popupService.error('Failed to add new business impact: ' + (error.response?.data?.message || error.message));
        
        // Send push notification for business impact addition failure
        sendPushNotification({
          title: 'Business Impact Addition Failed',
          message: `Failed to add new business impact: ${error.response?.data?.message || error.message}`,
          category: 'risk',
          priority: 'medium',
          user_id: 'default_user'
        });
      }
    };

    // Category Methods
    const fetchCategories = async () => {
      try {
        const response = await axios.get(API_ENDPOINTS.RISK_CATEGORIES);
        if (response.data.status === 'success') {
          categories.value = response.data.data;
        }
      } catch (error) {
        console.error('Error fetching categories:', error);
      }
    };

    const toggleCategoryDropdown = () => {
      showCategoryDropdown.value = !showCategoryDropdown.value;
      if (showCategoryDropdown.value) {
        categorySearch.value = '';
      }
    };

    const selectCategory = (category) => {
      selectedCategory.value = category.value;
      risk.value.Category = category.value;
      showCategoryDropdown.value = false;
    };

    const addNewCategory = async (event) => {
      // Prevent default form submission
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      
      // Don't proceed if input is empty
      if (!newCategory.value.trim()) {
        return;
      }
      
      try {
        console.log('Adding new category:', newCategory.value);
        
        const response = await axios.post(API_ENDPOINTS.ADD_RISK_CATEGORY, {
          value: newCategory.value.trim()
        });
        
        if (response.data.status === 'success') {
          console.log('Successfully added category:', response.data.data);
          categories.value.push(response.data.data);
          selectCategory(response.data.data);
          showAddCategoryModal.value = false;
          newCategory.value = '';
        } else {
          throw new Error('Failed to add category: ' + (response.data.message || 'Unknown error'));
        }
      } catch (error) {
        console.error('Error adding new category:', error);
        popupService.error('Failed to add new category: ' + (error.response?.data?.message || error.message));
        
        // Send push notification for category addition failure
        sendPushNotification({
          title: 'Category Addition Failed',
          message: `Failed to add new category: ${error.response?.data?.message || error.message}`,
          category: 'risk',
          priority: 'medium',
          user_id: 'default_user'
        });
      }
    };

    const addAction = () => {
      mitigationForm.value.actions.push('');
      updateMitigationJson();
    };

    const removeAction = (index) => {
      mitigationForm.value.actions.splice(index, 1);
      updateMitigationJson();
    };

    const updateMitigationJson = () => {
      // Convert actions array to numbered object
      const actionsObj = {};
      mitigationForm.value.actions.forEach((action, idx) => {
        if (action.trim() !== '') {
          actionsObj[(idx + 1).toString()] = action;
        }
      });
      riskMitigationJson.value = JSON.stringify(actionsObj, null, 2);
      // Update the risk object with the string format for the Risk model (TextField)
      risk.value.RiskMitigation = Object.values(actionsObj).join('\n');
    };

    const resetForm = () => {
      selectedRiskId.value = '';
      selectedBusinessImpacts.value = [];
      selectedCategory.value = '';
      mitigationForm.value.actions = [''];
      riskMitigationJson.value = '';
      Object.assign(risk.value, {
        RiskTitle: '',
        ComplianceId: '',
        Criticality: '',
        Category: '',
        RiskType: '',
        RiskPriority: '',
        RiskImpact: 1,
        RiskLikelihood: 1,
        RiskExposureRating: 1,
        RiskMultiplierX: 1, // Default to 1 (0.1)
        RiskMultiplierY: 1, // Default to 1 (0.1)
        BusinessImpact: '',
        PossibleDamage: '',
        RiskDescription: '',
        RiskMitigation: ''
      });
    };

    const validateRiskData = () => {
      const errors = {};

      // Criticality validation
      const allowedCriticality = ['Critical', 'High', 'Medium', 'Low'];
      if (!risk.value.Criticality || !allowedCriticality.includes(risk.value.Criticality)) {
        errors.Criticality = `Invalid Criticality. Must be one of: ${allowedCriticality.join(', ')}`;
      }

      // RiskPriority validation
      const allowedPriority = ['High', 'Medium', 'Low'];
      if (!risk.value.RiskPriority || !allowedPriority.includes(risk.value.RiskPriority)) {
        errors.RiskPriority = `Invalid Risk Priority. Must be one of: ${allowedPriority.join(', ')}`;
      }

      // RiskType validation
      const allowedRiskType = ['Current', 'Residual', 'Inherent', 'Emerging', 'Accept'];
      if (!risk.value.RiskType || !allowedRiskType.includes(risk.value.RiskType)) {
        errors.RiskType = `Invalid Risk Type. Must be one of: ${allowedRiskType.join(', ')}`;
      }

      // RiskImpact validation (1-10)
      const riskImpact = parseInt(risk.value.RiskImpact);
      if (isNaN(riskImpact) || riskImpact < 1 || riskImpact > 10) {
        errors.RiskImpact = 'Risk Impact must be between 1 and 10';
      }

      // RiskLikelihood validation (1-10)
      const riskLikelihood = parseInt(risk.value.RiskLikelihood);
      if (isNaN(riskLikelihood) || riskLikelihood < 1 || riskLikelihood > 10) {
        errors.RiskLikelihood = 'Risk Likelihood must be between 1 and 10';
      }

      // Text field pattern validation
      const textPattern = /^[A-Za-z0-9\s.,;:!?'"()\-_[\]]{0,}$/;
      const textFields = ['RiskTitle', 'RiskDescription', 'PossibleDamage', 'RiskMitigation'];
      
      textFields.forEach(field => {
        if (risk.value[field] && !textPattern.test(risk.value[field])) {
          errors[field] = `${field} contains invalid characters`;
        }
      });

      return errors;
    };

    const saveRisk = async () => {
      try {
        // Validate data before submission
        const validationErrors = validateRiskData();
        if (Object.keys(validationErrors).length > 0) {
          // Show validation errors to user
          const errorMessages = Object.entries(validationErrors)
            .map(([field, error]) => `${field}: ${error}`)
            .join('\n');
          popupService.error('Please fix the following validation errors:\n\n' + errorMessages);
          
          // Send push notification for validation errors
          sendPushNotification({
            title: 'Risk Validation Errors',
            message: `Please fix the following validation errors: ${Object.keys(validationErrors).join(', ')}`,
            category: 'risk',
            priority: 'medium',
            user_id: 'default_user'
          });
          return;
        }

        const riskData = { 
          ...risk.value,
          // Convert numeric fields to integers
          RiskLikelihood: parseInt(risk.value.RiskLikelihood) || 1,
          RiskImpact: parseInt(risk.value.RiskImpact) || 1,
          RiskExposureRating: parseFloat(risk.value.RiskExposureRating) || 1,
          BusinessImpact: selectedBusinessImpacts.value.map(i => i.value).join(', '),
          // Use the string format for RiskMitigation (Risk model uses TextField)
          RiskMitigation: risk.value.RiskMitigation || ''
        };
        
        // Always create a new risk, even when editing an existing one
        await axios.post(API_ENDPOINTS.RISKS, riskData);
        popupService.success('Risk created successfully!');
        
        // Send push notification for successful risk creation
        sendPushNotification({
          title: 'New Risk Instance Created',
          message: `A new risk instance "${riskData.RiskTitle || 'Untitled Risk'}" has been created in the Risk module.`,
          category: 'risk',
          priority: 'high',
          user_id: 'default_user'
        });
        
        // Reset the form after successful save
        resetForm();
      } catch (error) {
        console.error('Error saving risk:', error);
        if (error.response?.data?.detail) {
          popupService.error('Server validation error: ' + error.response.data.detail);
          
          // Send push notification for server validation error
          sendPushNotification({
            title: 'Risk Creation Failed - Server Error',
            message: `Server validation error: ${error.response.data.detail}`,
            category: 'risk',
            priority: 'high',
            user_id: 'default_user'
          });
        } else {
          popupService.error('Failed to save risk: ' + error.message);
          
          // Send push notification for general save error
          sendPushNotification({
            title: 'Risk Creation Failed',
            message: `Failed to save risk: ${error.message}`,
            category: 'risk',
            priority: 'high',
            user_id: 'default_user'
          });
        }
      }
    };

    // Close dropdown when clicking outside
    const setupClickOutsideListener = () => {
      document.addEventListener('click', (event) => {
        const businessImpactDropdown = document.querySelector('.tailoring-risk-business-impact-dropdown');
        if (businessImpactDropdown && !businessImpactDropdown.contains(event.target)) {
          showBusinessImpactDropdown.value = false;
        }
        
        const categoryDropdown = document.querySelector('.tailoring-risk-category-dropdown');
        if (categoryDropdown && !categoryDropdown.contains(event.target)) {
          showCategoryDropdown.value = false;
        }
      });
    };

    // Lifecycle
    onMounted(() => {
      loadRisks();
      fetchBusinessImpacts();
      fetchCategories();
      setupClickOutsideListener();
    });
    
    return {
      risk,
      allRisks,
      selectedRiskId,
      pageTitle,
      businessImpacts,
      selectedBusinessImpacts,
      showBusinessImpactDropdown,
      businessImpactSearch,
      showAddImpactModal,
      newBusinessImpact,
      filteredBusinessImpacts,
      categories,
      selectedCategory,
      showCategoryDropdown,
      categorySearch,
      showAddCategoryModal,
      newCategory,
      filteredCategories,
      mitigationForm,
      riskMitigationJson,
      onRiskSelected,
      toggleBusinessImpactDropdown,
      toggleBusinessImpact,
      isBusinessImpactSelected,
      addNewBusinessImpact,
      toggleCategoryDropdown,
      selectCategory,
      addNewCategory,
      addAction,
      removeAction,
      updateMitigationJson,
      resetForm,
      saveRisk,
      sendPushNotification
    };
  }
};
</script> 