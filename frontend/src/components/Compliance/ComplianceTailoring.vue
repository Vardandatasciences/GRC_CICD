<template>
  <div class="compliance-versioning-container">
    <div class="compliance-heading">
      <div class="heading-content">
        <div class="heading-text">
          <h1>Compliance Tailoring & Templating</h1>
          <!-- <div class="compliance-heading-underline"></div> -->
        </div>
      </div>
    </div>
    
    <!-- Static Content Section -->
    <div class="static-content-section">
      <div class="content-wrapper">
        <p class="content-description">
          Select a framework, policy, and sub-policy to view and manage compliances. 
          Use this page to create reusable compliance templates that can be tailored to specific organizational needs.
        </p>
        <div class="feature-badge">
          <i class="fas fa-edit"></i>
          <span>Edit existing compliances</span>
        </div>
        <div class="feature-badge">
          <i class="fas fa-copy"></i>
          <span>Copy compliances as templates</span>
        </div>
        <div class="feature-badge">
          <i class="fas fa-filter"></i>
          <span>Filter by framework hierarchy</span>
        </div>
      </div>
    </div>

    <div class="compliance-selection-row">
      <div class="compliance-selection-group">
        <CustomDropdown
          :config="frameworkDropdownConfig"
          v-model="selectedFrameworkId"
          :disabled="loading"
          @change="onFrameworkChange"
        />
      </div>
      <div class="compliance-selection-group">
        <CustomDropdown
          :config="policyDropdownConfig"
          v-model="selectedPolicyId"
          :disabled="!selectedFrameworkId || loading"
          @change="onPolicyChange"
        />
      </div>
      <div class="compliance-selection-group">
        <CustomDropdown
          :config="subPolicyDropdownConfig"
          v-model="selectedSubPolicyId"
          :disabled="!selectedPolicyId || loading"
          @change="onSubPolicyChange"
        />
      </div>
  
    </div>

    
    <div v-if="error" class="compliance-error-message">
      <i class="fas fa-exclamation-triangle"></i> {{ error }}
      <button @click="refreshCurrentData" class="compliance-retry-btn">Retry</button>
    </div>

    <div v-if="selectedSubPolicy" class="compliance-table-container">
      <h3>Compliances for Selected Subpolicy</h3>
      <div v-if="loading" class="loading">Loading compliances...</div>
      <div v-else-if="error" class="error-message">{{ error }}</div>
      <div v-else-if="complianceList.length === 0" class="no-compliances">No approved compliances found for this subpolicy.</div>
      <DynamicTable
        v-else
        :data="complianceList"
        :columns="tableColumns"
        :showActions="true"
      >
        <template #actions="{ row }">
          <div class="compliance-action-btn-group">
            <button @click="navigateToEdit(row)" title="Edit" class="compliance-action-btn compliance-edit-btnn">
              <i class="fas fa-edit"></i>
            </button>
            <button @click="startCopy(row)" title="Copy" class="compliance-action-btn compliance-copy-btnn">
              <i class="fas fa-copy"></i>
            </button>
          </div>
        </template>
      </DynamicTable>
    </div>

    <!-- Modal removed - CopyCompliance is now a separate page -->

    <!-- Add PopupModal component at the end -->
    <PopupModal />
  </div>
</template>

<script>
import { PopupModal, PopupService } from '../../modules/popup';
import PopupMixin from './mixins/PopupMixin';
import { CompliancePopups } from './utils/popupUtils';
import { complianceService } from '@/services/api';
import complianceDataService from '@/services/complianceService'; // NEW: Use cached compliance data
import CustomDropdown from '../CustomDropdown.vue';
import DynamicTable from '../DynamicTable.vue';
import axios from 'axios';
import { API_ENDPOINTS } from '../../config/api.js';
export default {
  name: 'ComplianceTailoring',
  components: {
    PopupModal,
    CustomDropdown,
    DynamicTable
  },
  mixins: [PopupMixin],
  data() {
    return {
      frameworks: [],
      selectedFramework: '',
      selectedFrameworkId: '',
      policies: [],
      selectedPolicy: '',
      selectedPolicyId: '',
      complianceSubPolicies: [],
      selectedSubPolicy: '',
      selectedSubPolicyId: '',
      complianceList: [],
      loading: false,
      error: null,
      
      // Framework session filtering properties
      sessionFrameworkId: null,
      frameworkDropdownConfig: {
        label: 'Framework',
        values: []
      },
      policyDropdownConfig: {
        label: 'Policy',
        values: []
      },
      subPolicyDropdownConfig: {
        label: 'Sub Policy',
        values: []
      },
      categoryOptions: {
        RiskCategory: [],
        RiskType: [],
        BusinessUnitsCovered: [],
        RiskBusinessImpact: []
      },
      filteredOptions: {
        RiskCategory: [],
        RiskType: [],
        BusinessUnitsCovered: [],
        RiskBusinessImpact: []
      },
      businessUnitSearch: '',
      riskTypeSearch: '',
      riskCategorySearch: '',
      riskBusinessImpactSearch: '',
      activeDropdown: null,
      tableColumns: [
        { key: 'ComplianceTitle', label: 'Title' },
        { key: 'ComplianceItemDescription', label: 'Description' },
        { key: 'Status', label: 'Status' },
        { key: 'ComplianceVersion', label: 'Version' }
      ]
    }
  },
  async created() {
    // First, load frameworks
    await this.loadFrameworks();
    
    // Check for selected framework from session after loading frameworks
    await this.checkSelectedFrameworkFromSession();
    
    // Load other data
    await this.loadUsers();
    await this.loadCategoryOptions();
    
    document.addEventListener('click', this.handleClickOutside);
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside);
  },
  watch: {
    // Watch for filteredFrameworks changes to update dropdown config
    filteredFrameworks: {
      handler() {
        this.updateFrameworkConfig();
      },
      immediate: true
    },
    
    selectedFrameworkId(newId) {
      const fw = this.frameworks.find(fw => fw.id === newId);
      this.selectedFramework = fw || '';
      if (fw) {
        this.loadPolicies(fw.id);
        this.selectedPolicy = '';
        this.selectedPolicyId = '';
        this.selectedSubPolicy = '';
        this.selectedSubPolicyId = '';
        this.policies = [];
        this.complianceSubPolicies = [];
        this.complianceList = [];
      }
    },
    selectedPolicyId(newId) {
      const p = this.policies.find(p => p.id === newId);
      this.selectedPolicy = p || '';
      if (p) {
        this.loadSubPolicies(p.id);
        this.selectedSubPolicy = '';
        this.selectedSubPolicyId = '';
        this.complianceSubPolicies = [];
        this.complianceList = [];
      }
    },
    selectedSubPolicyId(newId) {
      const sp = this.complianceSubPolicies.find(sp => sp.id === newId);
      this.selectedSubPolicy = sp || '';
      if (sp) {
        this.loadCompliances();
      } else {
        this.complianceList = [];
      }
    },
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
  },
  methods: {
    // Framework session management methods
    async checkSelectedFrameworkFromSession() {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in ComplianceTailoring...')
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
            this.selectedFrameworkId = frameworkExists.id.toString()
            this.selectedFramework = frameworkExists
            console.log('✅ DEBUG: Auto-selected framework from session:', this.selectedFrameworkId)
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
        await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, { frameworkId })
        console.log('✅ DEBUG: Framework saved to session successfully')
      } catch (error) {
        console.error('❌ DEBUG: Error saving framework to session:', error)
      }
    },
    
    handleFrameworkChange(option) {
      this.selectedFrameworkId = option.value
      if (option.value) {
        // Save the selected framework to session
        this.saveFrameworkToSession(option.value)
      }
    },
    
    clearFilters() {
      this.sessionFrameworkId = null
      this.selectedFrameworkId = ''
      this.selectedFramework = ''
      this.selectedPolicyId = ''
      this.selectedPolicy = ''
      this.selectedSubPolicyId = ''
      this.selectedSubPolicy = ''
      this.policies = []
      this.complianceSubPolicies = []
      this.complianceList = []
      this.policyDropdownConfig.values = []
      this.subPolicyDropdownConfig.values = []
    },
    
    updateFrameworkConfig() {
      this.frameworkDropdownConfig.values = this.filteredFrameworks.map(fw => ({
        value: fw.id,
        label: fw.name
      }))
    },
    
    async loadFrameworks() {
      try {
        this.loading = true;
        console.log('🔍 [ComplianceTailoring] Checking for cached framework data...');
        
        // ==========================================
        // NEW: Ensure compliance prefetch is running
        // ==========================================
        if (!window.complianceDataFetchPromise && !complianceDataService.hasFrameworksCache()) {
          console.log('🚀 [ComplianceTailoring] Starting compliance prefetch (user navigated directly)...');
          window.complianceDataFetchPromise = complianceDataService.fetchAllComplianceData();
        }

        if (window.complianceDataFetchPromise) {
          console.log('⏳ [ComplianceTailoring] Waiting for compliance prefetch to complete...');
          try {
            await window.complianceDataFetchPromise;
            console.log('✅ [ComplianceTailoring] Prefetch completed');
          } catch (prefetchError) {
            console.warn('⚠️ [ComplianceTailoring] Prefetch failed, will fetch directly from API', prefetchError);
          }
        }
        
        // FIRST: Try to get data from cache
        if (complianceDataService.hasFrameworksCache()) {
          console.log('✅ [ComplianceTailoring] Using cached framework data');
          const cachedFrameworks = complianceDataService.getData('frameworks') || [];
          
          this.frameworks = cachedFrameworks.map(fw => ({
            id: fw.FrameworkId || fw.id,
            name: fw.FrameworkName || fw.name
          }));
          
          console.log(`[ComplianceTailoring] Loaded ${this.frameworks.length} frameworks from cache (prefetched on Home page)`);
          
          // Update framework config with filtered frameworks
          this.updateFrameworkConfig();
        } else {
          // FALLBACK: Fetch from API if cache is empty
          console.log('⚠️ [ComplianceTailoring] No cached data found, fetching from API...');
          // Add active_only=true parameter to only fetch active frameworks
          const response = await complianceService.getComplianceFrameworks({ active_only: 'true' });
          console.log('Frameworks response:', response.data);
          
          let frameworksData;
          if (response.data.success && response.data.frameworks) {
            frameworksData = response.data.frameworks;
          } else if (Array.isArray(response.data)) {
            frameworksData = response.data;
          } else {
            console.error('Unexpected response format:', response.data);
            this.error = 'Failed to load frameworks';
            return;
          }
          
          this.frameworks = frameworksData.map(fw => ({
            id: fw.id || fw.FrameworkId,
            name: fw.name || fw.FrameworkName
          }));
          
          console.log(`[ComplianceTailoring] Loaded ${this.frameworks.length} frameworks directly from API (cache unavailable)`);
          
          // Update cache so subsequent pages benefit
          if (frameworksData.length > 0) {
            complianceDataService.setData('frameworks', frameworksData);
            console.log('ℹ️ [ComplianceTailoring] Cache updated after direct API fetch');
          }
          
          // Update framework config with filtered frameworks
          this.updateFrameworkConfig();
        }
      } catch (error) {
        this.error = 'Failed to load frameworks';
        console.error('Error loading frameworks:', error);
      } finally {
        this.loading = false;
      }
    },
    async loadPolicies(frameworkId) {
      try {
        this.loading = true;
        const response = await complianceService.getCompliancePolicies(frameworkId);
        console.log('Policies response:', response.data);
        
        let policiesData;
        if (response.data.success && response.data.policies) {
          policiesData = response.data.policies;
        } else if (Array.isArray(response.data)) {
          policiesData = response.data;
        } else {
          console.error('Error in response:', response.data);
          this.error = 'Failed to load policies';
          return;
        }
        
        this.policies = policiesData.map(p => ({
          id: p.id || p.PolicyId,
          name: p.name || p.PolicyName,
          applicability: p.applicability || p.scope || p.Applicability || ''
        }));
        
        this.policyDropdownConfig.values = this.policies.map(p => ({
          value: p.id,
          label: p.name
        }));
      } catch (error) {
        this.error = 'Failed to load policies';
        console.error(error);
      } finally {
        this.loading = false;
      }
    },
    async loadSubPolicies(policyId) {
      try {
        this.loading = true;
        const response = await complianceService.getComplianceSubPolicies(policyId);
        console.log('SubPolicies response:', response);
        
        let subpoliciesData;
        if (response.data.success && response.data.subpolicies) {
          subpoliciesData = response.data.subpolicies;
        } else if (Array.isArray(response.data)) {
          subpoliciesData = response.data;
        } else {
          console.error('Error in response:', response.data);
          this.error = 'Failed to load sub-policies';
          return;
        }
        
        console.log('SubPolicies data:', subpoliciesData);
        this.complianceSubPolicies = subpoliciesData.map(sp => ({
          id: sp.id || sp.SubPolicyId,
          name: sp.name || sp.SubPolicyName
        }));
        console.log('Mapped complianceSubPolicies:', this.complianceSubPolicies);
        this.subPolicyDropdownConfig.values = this.complianceSubPolicies.map(sp => ({
          value: sp.id,
          label: sp.name
        }));
      } catch (error) {
        this.error = 'Failed to load sub-policies';
        console.error('SubPolicies error:', error);
      } finally {
        this.loading = false;
      }
    },
    async loadUsers() {
      try {
        this.loading = true;
        const response = await complianceService.getUsers();
        console.log('Users API response:', response);
        
        if (response.data.success && Array.isArray(response.data.users)) {
          this.users = response.data.users;
          console.log('Loaded users:', this.users);
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
    async loadCategoryOptions() {
      try {
        this.loading = true;
        
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
        
        const rtResponse = await complianceService.getCategoryBusinessUnits('RiskType');
        console.log('RiskType API response:', rtResponse);
        if (rtResponse.data.success && rtResponse.data.data && Array.isArray(rtResponse.data.data) && rtResponse.data.data.length > 0) {
          // Validate that each item has the expected structure
          const validData = rtResponse.data.data.filter(item => item && typeof item === 'object' && item.value && item.value.trim());
          console.log('Valid RiskType data:', validData);
          
          if (validData.length > 0) {
            this.categoryOptions.RiskType = validData;
            this.filteredOptions.RiskType = [...validData];
          } else {
            console.warn('No valid RiskType data found, using fallback');
            this.useFallbackRiskTypes();
          }
        } else {
          console.warn('RiskType API response invalid, using fallback');
          this.useFallbackRiskTypes();
        }
        
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
        
        const rbiResponse = await complianceService.getCategoryBusinessUnits('RiskBusinessImpact');
        console.log('RiskBusinessImpact API response:', rbiResponse);
        if (rbiResponse.data.success && rbiResponse.data.data && Array.isArray(rbiResponse.data.data) && rbiResponse.data.data.length > 0) {
          // Validate that each item has the expected structure
          const validData = rbiResponse.data.data.filter(item => item && typeof item === 'object' && item.value && item.value.trim());
          console.log('Valid RiskBusinessImpact data:', validData);
          
          if (validData.length > 0) {
            this.categoryOptions.RiskBusinessImpact = rbiResponse.data.data;
            this.filteredOptions.RiskBusinessImpact = [...rbiResponse.data.data];
          } else {
            console.warn('No valid RiskBusinessImpact data found, using fallback');
            this.useFallbackRiskBusinessImpacts();
          }
        } else {
          console.warn('RiskBusinessImpact API response invalid, using fallback');
          this.useFallbackRiskBusinessImpacts();
        }
              } catch (error) {
          console.error('Failed to load category options:', error);
          PopupService.error('Failed to load dropdown options. Some features may be limited.');
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
      
      
      showDropdown(field) {
      this.activeDropdown = field;
      
      this.filterOptions(field);
      
      event.stopPropagation();
    },
    handleClickOutside(event) {
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
      
      const lowerSearchTerm = searchTerm.toLowerCase();
      this.filteredOptions[field] = this.categoryOptions[field].filter(option => 
        option.value.toLowerCase().includes(lowerSearchTerm)
      );
    },
    selectOption(field, value) {
      this.editRow[field] = value;
      
      switch (field) {
        case 'BusinessUnitsCovered':
          this.businessUnitSearch = value;
          break;
        case 'RiskType':
          this.riskTypeSearch = value;
          break;
        case 'RiskCategory':
          this.riskCategorySearch = value;
          break;
        case 'RiskBusinessImpact':
          this.riskBusinessImpactSearch = value;
          break;
      }
      
      this.activeDropdown = null;
    },
    async addNewOption(field, value) {
      if (!value || !value.trim()) return;
      
      try {
        this.loading = true;
        
        const response = await complianceService.addCategoryBusinessUnit({
          source: field,
          value: value.trim()
        });
        
        if (response.data.success) {
          const newOption = {
            id: response.data.data.id,
            value: response.data.data.value
          };
          
          this.categoryOptions[field] = [...this.categoryOptions[field], newOption];
          this.filteredOptions[field] = [...this.filteredOptions[field], newOption];
          
          this.selectOption(field, newOption.value);
          
          this.editRow[field] = newOption.value;
          
          CompliancePopups.complianceCreated({
            message: `Added new ${field} option: ${newOption.value}`
          });
          
          await this.loadCategoryOptions();
        } else {
          throw new Error(response.data.error || 'Failed to add new option');
        }
      } catch (error) {
        console.error(`Failed to add new ${field} option:`, error);
        this.error = `Failed to add new option: ${error.message || error}`;
      } finally {
        this.loading = false;
      }
    },
    async loadCompliances() {
      if (!this.selectedSubPolicy) return;
      
      try {
        this.loading = true;
        this.error = null; // Clear any previous errors
        const response = await complianceService.getCompliancesBySubPolicy(this.selectedSubPolicy.id);
        console.log('Compliances response:', response);
        
        if (response.data.success && response.data.compliances) {
          // Initialize mitigationSteps for each compliance
          this.complianceList = response.data.compliances.map(compliance => {
            // Handle case where mitigation field might not be present
            const mitigationSteps = compliance.mitigation ? 
              this.parseMitigationSteps(compliance.mitigation) : 
              [{ description: '' }];
            return {
              ...compliance,
              mitigationSteps
            };
          });
          console.log('Loaded compliances with mitigation steps:', this.complianceList);
        } else {
          console.error('Error in response:', response.data);
          this.error = 'Failed to load compliances';
        }
      } catch (error) {
        if (error.response && error.response.status === 403) {
          this.error = 'Access denied. You do not have permission to view compliances.';
        } else if (error.response && error.response.status === 404) {
          this.error = 'Subpolicy not found or access denied.';
        } else {
          this.error = 'Failed to load compliances: ' + (error.message || 'Unknown error');
        }
        console.error('Compliances error:', error);
      } finally {
        this.loading = false;
      }
    },
    formatDate(dateString) {
      if (!dateString) return '';
      
      try {
        let date;
        if (typeof dateString === 'string') {
          if (dateString.includes('T')) {
            date = new Date(dateString);
          } else if (dateString.includes('-')) {
            const parts = dateString.split(' ')[0].split('-');
            date = new Date(parts[0], parts[1] - 1, parts[2]);
          } else if (dateString.includes('/')) {
            const parts = dateString.split(' ')[0].split('/');
            date = new Date(parts[2], parts[0] - 1, parts[1]);
          } else {
            date = new Date(dateString);
          }
        } else {
          date = new Date(dateString);
        }
        
        return date.toLocaleString();
      } catch (e) {
        console.error('Error formatting date:', e);
        return dateString;
      }
    },
    viewComplianceDetails(compliance) { 
      CompliancePopups.showComplianceInfo(compliance);
    },
    getDefaultDueDate() {
      const date = new Date();
      date.setDate(date.getDate() + 7);
      return date.toISOString().split('T')[0];
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
          return parsed.UserId || parsed.user_id || parsed.id || '1';
        } catch (e) {
          // intentionally empty
        }
      }
      return '1';
    },
    navigateToEdit(compliance) {
      // Initialize the mitigation steps before navigation using the same parsing logic
      if (compliance.mitigation) {
        console.log('Original mitigation data:', compliance.mitigation);
        compliance.mitigationSteps = this.parseMitigationSteps(compliance.mitigation);
      } else {
        compliance.mitigationSteps = [{ description: '' }];
      }
      // --- Ensure reviewer_id is set for editing ---
      if (compliance.ReviewerId) {
        compliance.reviewer_id = compliance.ReviewerId;
      }
      // Do not set UserId or reviewer_id to any default value here
      this.$router.push(`/compliance/edit/${compliance.ComplianceId}`);
    },
    parseMitigationSteps(mitigation) {
      console.log('Parsing mitigation:', mitigation);
      if (!mitigation) return [{ description: '' }];
      
      try {
        if (typeof mitigation === 'string') {
          return [{ description: mitigation }];
        } else if (Array.isArray(mitigation)) {
          return mitigation.map(step => ({
            description: typeof step === 'string' ? step : step.description || ''
          }));
        } else if (typeof mitigation === 'object') {
          // Handle numbered object format: {"1": "Step 1", "2": "Step 2"}
          const sortedKeys = Object.keys(mitigation).sort((a, b) => parseInt(a) - parseInt(b));
          return sortedKeys.map(key => ({
            description: mitigation[key] && typeof mitigation[key] === 'string' ? mitigation[key].trim() : ''
          }));
        }
      } catch (error) {
        console.error('Error parsing mitigation steps:', error);
      }
      
      return [{ description: '' }];
    },
    addStep(row) {
      console.log('Adding step to row:', row);
      if (!row.mitigationSteps) {
        row.mitigationSteps = [];
      }
      row.mitigationSteps.push({ description: '' });
      this.onMitigationStepChange(row);
    },
    removeStep(row, index) {
      console.log('Removing step at index:', index, 'from row:', row);
      row.mitigationSteps.splice(index, 1);
      if (row.mitigationSteps.length === 0) {
        row.mitigationSteps.push({ description: '' });
      }
      this.onMitigationStepChange(row);
    },
    onMitigationStepChange(row) {
      console.log('Mitigation step change triggered for row:', row);
      console.log('Current mitigation steps:', row.mitigationSteps);
      
      // Format mitigation steps into the required structure with numeric keys
      const formattedSteps = {};
      row.mitigationSteps.forEach((step, index) => {
        // Include all steps, including empty ones, to maintain step order
        formattedSteps[`${index + 1}`] = step.description ? step.description.trim() : '';
      });
      
      // Update the mitigation property with formatted steps
      row.mitigation = formattedSteps;
      console.log('Updated mitigation data:', row.mitigation);
    },
    startCopy(compliance) {
      // Navigate to the copy compliance page with the compliance ID and current context
      this.$router.push({
        name: 'CopyCompliance',
        params: { id: compliance.ComplianceId },
        query: {
          frameworkId: this.selectedFramework?.id || '',
          frameworkName: this.selectedFramework?.name || '',
          policyId: this.selectedPolicy?.id || '',
          policyName: this.selectedPolicy?.name || '',
          subPolicyId: this.selectedSubPolicy?.id || '',
          subPolicyName: this.selectedSubPolicy?.name || ''
        }
      });
    },
    async handleCopySuccess() {
      await this.loadCompliances();
      CompliancePopups.complianceCreated({
        message: 'Compliance copied successfully'
      });
    },
    onFrameworkChange(option) {
      this.handleFrameworkChange(option);
    },
    onPolicyChange(option) {
      this.selectedPolicyId = option.value;
    },
    onSubPolicyChange(option) {
      this.selectedSubPolicyId = option.value;
    },
    async handleSubmit(formData) {
      try {
        // Ensure mitigation data is properly formatted before submission
        if (formData.mitigationSteps && formData.mitigationSteps.length > 0) {
          const formattedMitigation = {};
          formData.mitigationSteps.forEach((step, index) => {
            // Include all steps, including empty ones, to maintain step order
            formattedMitigation[`${index + 1}`] = step.description ? step.description.trim() : '';
          });
          formData.mitigation = formattedMitigation;
        }
        
        console.log('Submitting form data with mitigation:', formData.mitigation);
        
        await complianceService.updateCompliance(formData);
        CompliancePopups.complianceUpdated(formData);
      } catch (error) {
        console.error('Error submitting form:', error);
        CompliancePopups.error({
          message: `Failed to update compliance: ${error.message || error}`
        });
      }
    },
  }
}
</script>

<style scoped>
@import './ComplianceTailoring.css';

.heading-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.heading-text {
  flex: 1;
}


.rejected-compliances-section {
  margin: 2rem 24px;
  background-color: #fff8f8;
  padding: 1.5rem;
  border-radius: 8px;
  border: 2px solid #e6d0d0;
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.1);
  position: relative;
}

.rejected-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid #e6d0d0;
}

.rejected-header h3 {
  color: #c00;
  font-size: 1.2rem;
  font-weight: 600;
}

.refresh-rejected-btn {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  border: 1px solid #dc3545;
  background-color: #fff;
  color: #dc3545;
  cursor: pointer;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.refresh-rejected-btn:hover {
  background-color: #dc3545;
  color: white;
}

.rejected-loading {
  margin-top: 1rem;
  text-align: center;
  color: #666;
}

.no-rejected {
  text-align: center;
  color: #666;
}

.rejected-compliances-list {
  margin-top: 1rem;
}

.rejected-compliance-item {
  background-color: white;
  border: 1px solid #e0e0e0;
  margin-bottom: 1rem;
  padding: 1rem;
  border-radius: 4px;
  position: relative;
}

.rejected-item-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.badge.rejected {
  background-color: #ffebee;
  color: #d32f2f;
  border: 1px solid #ffcdd2;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
}

.rejected-item-details {
  padding-left: 0.5rem;
  border-left: 2px solid #f0f0f0;
}

.meta-info {
  display: flex;
  gap: 1rem;
  font-size: 0.9rem;
  color: #666;
}

.criticality {
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  font-weight: 500;
}

.criticality.high {
  background: #fee;
  color: #c00;
}

.criticality.medium {
  background: #ffd;
  color: #960;
}

.criticality.low {
  background: #efe;
  color: #060;
}

.rejected-date {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  color: #d32f2f;
}

.rejection-reason {
  margin-top: 8px;
  padding: 8px 12px;
  background-color: #fff0f0;
  border-left: 3px solid #ff3333;
  border-radius: 0 4px 4px 0;
  color: #c00;
  font-size: 0.9rem;
}

.edit-rejected-btn {
  margin-top: 1rem;
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.edit-rejected-btn:hover {
  background-color: #eeeeee;
  border-color: #ccc;
}

.edit-rejected-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.edit-rejected-content {
  background-color: white;
  padding: 2rem;
  border-radius: 8px;
  max-width: 800px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.resubmit-btn {
  background-color: #4caf50;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  margin-top: 1rem;
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
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
  position: relative;
}

.step-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.step-number {
  font-weight: 600;
}

.remove-step-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #dc3545;
  font-size: 0.8rem;
}

.step-description {
  position: relative;
  margin-top: 0.5rem;
}

.step-description textarea {
  width: 100%;
  min-height: 60px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: vertical;
}

.step-description .char-count {
  position: absolute;
  bottom: 8px;
  right: 8px;
  font-size: 0.8rem;
  color: #666;
  background: rgba(255, 255, 255, 0.9);
  padding: 2px 6px;
  border-radius: 4px;
}

.step-description .char-count.invalid {
  color: #dc3545;
}

.mitigation-step-input {
  width: 100%;
  min-height: 60px;
  padding: 8px 8px 24px 8px; /* Added padding at bottom for character count */
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: vertical;
}

.mitigation-step-input:focus {
  outline: none;
  border-color: #80bdff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.compliance-copy-form-grid {
  display: grid;
  gap: 1rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.compliance-form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  align-items: start;
}

.compliance-form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.compliance-form-group label {
  font-weight: 600;
  color: #495057;
}

.compliance-input,
.compliance-select {
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 1rem;
  width: 100%;
}

.compliance-input:focus,
.compliance-select:focus {
  outline: none;
  border-color: #80bdff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.compliance-form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1rem;
}

.compliance-save-btn,
.compliance-cancel-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.compliance-save-btn {
  background-color: #28a745;
  color: white;
}

.compliance-save-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.compliance-cancel-btn {
  background-color: #dc3545;
  color: white;
}

.compliance-action-btn-group {
  display: flex;
  gap: 0.5rem;
}

.compliance-action-btn {
  padding: 0.25rem 0.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.compliance-edit-btnn {
  background-color: #ffffff !important;
  color: #000000 !important;
  background: #ffffff !important;
}

.compliance-copy-btnn {
  background-color: #ffffff !important;
  color: rgb(0, 0, 0) !important;
  background: #ffffff !important;
}

.compliance-action-btn:hover {
  opacity: 0.8;
}

.compliance-action-btn i {
  font-size: 1rem;
}

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
  border: 1px solid #ced4da;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 1000;
}

.dropdown-option {
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.dropdown-option:hover {
  background-color: #f8f9fa;
}

.dropdown-add-option {
  padding: 8px 12px;
  border-bottom: 1px solid #ced4da;
}

.dropdown-add-btn {
  display: block;
  width: 100%;
  padding: 4px 8px;
  margin-top: 4px;
  border: none;
  background: #e9ecef;
  color: #495057;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.dropdown-add-btn:hover {
  background: #dee2e6;
}

.compliance-input:focus {
  outline: none;
  border-color: #80bdff;
  box-shadow: 0 0 0 0.2rem rgba(0,123,255,0.25);
}

.compliance-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.error-message {
  color: #dc3545;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  padding: 12px;
  margin: 16px 0;
  text-align: center;
  font-weight: 500;
}
</style> 