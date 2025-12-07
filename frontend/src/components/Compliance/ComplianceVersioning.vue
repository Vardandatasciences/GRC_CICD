<template>
  <div class="version-list-container">
    <div class="version-list-header">
      <h2 class="version-list-heading">Compliance Version List</h2>
    </div>

    <!-- Static Content Section -->
    <div class="static-content-section">
      <div class="content-wrapper">
        <p class="content-description">
          Select a framework, policy, and sub-policy to view and manage compliance versions. 
          Use this page to track version history and toggle active/inactive status of compliance items.
        </p>
        <div class="feature-badge">
          <i class="fas fa-history"></i>
          <span>View version history</span>
        </div>
        <div class="feature-badge">
          <i class="fas fa-toggle-on"></i>
          <span>Toggle active status</span>
        </div>
        <div class="feature-badge">
          <i class="fas fa-list"></i>
          <span>Group by compliance ID</span>
        </div>
      </div>
    </div>

    <!-- Filter Section -->
    <div class="filter-section">
      <div class="filter-group">
        <CustomDropdown
          :config="frameworkDropdownConfig"
          v-model="selectedFramework"
          @change="onFrameworkChange"
        />
      </div>

      <div class="filter-group">
        <CustomDropdown
          :config="policyDropdownConfig"
          v-model="selectedPolicy"
          @change="onPolicyChange"
          :disabled="!selectedFramework"
        />
      </div>

      <div class="filter-group">
        <CustomDropdown
          :config="subPolicyDropdownConfig"
          v-model="selectedSubPolicy"
          @change="onSubPolicyChange"
          :disabled="!selectedPolicy"
        />
      </div>

    </div>

    <!-- Grouped Compliance Table using DynamicTable -->
    <div class="table-container" v-if="groupedCompliances.length > 0">
      <div v-for="(group, groupIndex) in groupedCompliances" :key="groupIndex" class="compliance-group">
        <div class="group-header">
          <h3>Compliance ID: {{ group[0].Identifier }}</h3>
          <div class="group-description">{{ group[0].ComplianceItemDescription }}</div>
        </div>
        <div class="table-wrapper">
          <DynamicTable
            :data="group"
            :columns="tableColumns"
            :showPagination="false"
          >
            <template #cell-ActiveInactive="{ row }">
              <div class="toggle-switch">
                <input
                  type="checkbox"
                  :id="'toggle-' + row.ComplianceId"
                  :checked="row.ActiveInactive === 'Active'"
                  @change="toggleActiveStatus(row)"
                  :disabled="row.Status !== 'Approved'"
                >
                <label :for="'toggle-' + row.ComplianceId"></label>
              </div>
            </template>
            <template #cell-CreatedByDate="{ row }">
              {{ formatDate(row.CreatedByDate) }}
            </template>
            <template #cell-PreviousComplianceVersionId="{ row }">
              {{ getPreviousVersionDisplay(row) }}
            </template>
          </DynamicTable>
        </div>
      </div>
    </div>
    <div v-else-if="selectedSubPolicy" class="no-data">
      No compliances found for the selected criteria
    </div>
    
    <!-- Error Message Display -->
    <div v-if="error" class="error-message">
      <div class="error-icon">⚠️</div>
      <div class="error-text">{{ error }}</div>
      <button @click="refreshCurrentData" class="retry-button">Retry</button>
    </div>
    
    <!-- Deactivation Dialog -->
    <div v-if="showDeactivationDialog" class="deactivation-dialog-overlay">
      <div class="deactivation-dialog">
        <h3>Deactivate Compliance</h3>
        <p>Please provide a reason for deactivating this compliance:</p>
        <textarea 
          v-model="deactivationReason" 
          class="deactivation-reason-input"
          placeholder="Enter reason for deactivation">
        </textarea>
        <div class="deactivation-options">
          <label>
            <input type="checkbox" v-model="cascadeToPolicies">
            Apply to related policies
          </label>
          <div class="affected-count" v-if="cascadeToPolicies">
            {{ affectedPoliciesCount || 0 }} policies will be affected
          </div>
        </div>
        <div class="deactivation-options">
          <label for="reviewer-dropdown">Select Reviewer:</label>
          <CustomDropdown
            :config="reviewerDropdownConfig"
            v-model="selectedReviewer"
            id="reviewer-dropdown"
          />
        </div>
        <div class="deactivation-actions">
          <button @click="cancelDeactivation" class="cancel-btn">Cancel</button>
          <button @click="submitDeactivation" class="submit-btn">OK</button>
        </div>
      </div>
    </div>
    
    <!-- Deactivation Confirmation Dialog -->
    <div v-if="showDeactivationConfirmation" class="deactivation-dialog-overlay">
      <div class="deactivation-dialog">
        <h3>Deactivation Request Submitted</h3>
        <p>Your request to deactivate this compliance item has been submitted successfully and is awaiting approval.</p>
        <p>The compliance will remain active until an approver reviews and accepts this request.</p>
        <div class="approval-info">
          <i class="fas fa-info-circle"></i>
          <span>You can check the status of this request in the Compliance Approver interface.</span>
        </div>
        <div class="deactivation-actions">
          <button @click="closeDeactivationConfirmation" class="submit-btn">OK</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { complianceService } from '@/services/api';
import complianceDataService from '@/services/complianceService'; // NEW: Use cached compliance data
import axios from 'axios';
import CustomDropdown from '@/components/CustomDropdown.vue';
import DynamicTable from '@/components/DynamicTable.vue';
import AccessUtils from '@/utils/accessUtils';
import { API_ENDPOINTS } from '../../config/api.js';

export default {
  name: 'ComplianceVersionList',
  components: {
    CustomDropdown,
    DynamicTable
  },
  data() {
    return {
      frameworks: [],
      policies: [],
      subPolicies: [],
      compliances: [],
      selectedFramework: '',
      selectedPolicy: '',
      selectedSubPolicy: '',
      loading: false,
      searchQuery: '',
      
      // Framework session filtering properties
      sessionFrameworkId: null,
      showDeactivationDialog: false,
      deactivationReason: '',
      cascadeToPolicies: true,
      affectedPoliciesCount: 0,
      complianceToDeactivate: null,
      showDeactivationConfirmation: false,
      error: null,
      frameworkDropdownConfig: {
        values: [],
        defaultLabel: 'Select Framework',
        name: 'Framework'
      },
      policyDropdownConfig: {
        values: [],
        defaultLabel: 'Select Policy',
        name: 'Policy'
      },
      subPolicyDropdownConfig: {
        values: [],
        defaultLabel: 'Select Sub Policy',
        name: 'Sub Policy'
      },
      reviewerDropdownConfig: {
        values: [],
        defaultLabel: 'Select Reviewer',
        name: 'Reviewer'
      },
      selectedReviewer: '',
      users: [],
      tableColumns: [
        { key: 'ComplianceVersion', label: 'Version' },
        { key: 'Status', label: 'Status' },
        { key: 'ActiveInactive', label: 'Active/Inactive', slot: true },
        { key: 'CreatedByName', label: 'Created By' },
        { key: 'CreatedByDate', label: 'Created Date', slot: true },
        { key: 'PreviousComplianceVersionId', label: 'Previous Version', slot: true }
      ],
    }
  },
  computed: {
    // Framework filtering computed properties
    filteredFrameworks() {
      if (this.sessionFrameworkId) {
        // If there's a session framework ID, show only that framework
        return this.frameworks.filter(fw => fw.FrameworkId.toString() === this.sessionFrameworkId.toString())
      }
      // If no session framework ID, show all frameworks
      return this.frameworks
    },
    
    groupedCompliances() {
      let filtered = this.compliances;
      if (this.searchQuery) {
        const q = this.searchQuery.toLowerCase();
        filtered = filtered.filter(c =>
          (c.Identifier && c.Identifier.toLowerCase().includes(q)) ||
          (c.ComplianceItemDescription && c.ComplianceItemDescription.toLowerCase().includes(q))
        );
      }
      const groups = {};
      filtered.forEach(compliance => {
        if (!groups[compliance.Identifier]) {
          groups[compliance.Identifier] = [];
        }
        groups[compliance.Identifier].push(compliance);
      });
      // Sort each group by version number (descending)
      return Object.values(groups).map(group => {
        return group.sort((a, b) => {
          const versionA = parseFloat(a.ComplianceVersion);
          const versionB = parseFloat(b.ComplianceVersion);
          return versionB - versionA;
        });
      });
    }
  },
  watch: {
    // Watch for filteredFrameworks changes to update dropdown config
    filteredFrameworks: {
      handler() {
        this.updateFrameworkConfig();
      },
      immediate: true
    }
  },
  async mounted() {
    try {
      // First, load frameworks
      await this.loadFrameworks();
      
      // Check for selected framework from session after loading frameworks
      await this.checkSelectedFrameworkFromSession();
      
      // Load other data
      this.loadUsers();
      // Set selectedReviewer to empty on mount
      this.selectedReviewer = '';
    } catch (error) {
      if (error.response && [401, 403].includes(error.response.status)) {
        AccessUtils.showComplianceVersioningDenied();
        return;
      }
      throw error;
    }
  },
  methods: {
    // Framework session management methods
    async checkSelectedFrameworkFromSession() {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in ComplianceVersioning...')
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
        console.log('📊 DEBUG: Selected framework response:', response.data)
        
        if (response.data && response.data.success && response.data.frameworkId) {
          const frameworkIdFromSession = response.data.frameworkId
          console.log('✅ DEBUG: Found selected framework in session:', frameworkIdFromSession)
          
          // Store the session framework ID for filtering
          this.sessionFrameworkId = frameworkIdFromSession
          
          // Check if this framework exists in our loaded frameworks
          const frameworkExists = this.frameworks.find(f => f.FrameworkId.toString() === frameworkIdFromSession.toString())
          
          if (frameworkExists) {
            console.log('✅ DEBUG: Framework exists in loaded frameworks:', frameworkExists.FrameworkName)
            // Automatically select the framework from session
            this.selectedFramework = frameworkExists.FrameworkId
            console.log('✅ DEBUG: Auto-selected framework from session:', this.selectedFramework)
            // Load policies for the selected framework
            await this.loadPolicies()
          } else {
            console.log('⚠️ DEBUG: Framework from session (ID:', frameworkIdFromSession, ') not found in loaded frameworks')
            console.log('📋 DEBUG: Available frameworks:', this.frameworks.map(f => ({ id: f.FrameworkId, name: f.FrameworkName })))
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
      this.selectedFramework = option.value
      if (option.value) {
        // Save the selected framework to session
        this.saveFrameworkToSession(option.value)
      }
      this.loadPolicies()
    },
    
    clearFilters() {
      this.sessionFrameworkId = null
      this.selectedFramework = ''
      this.selectedPolicy = ''
      this.selectedSubPolicy = ''
      this.policies = []
      this.subPolicies = []
      this.compliances = []
      this.policyDropdownConfig.values = []
      this.subPolicyDropdownConfig.values = []
    },
    
    updateFrameworkConfig() {
      this.frameworkDropdownConfig.values = this.filteredFrameworks.map(fw => ({
        value: fw.FrameworkId,
        label: fw.FrameworkName
      }))
    },
    
    async loadFrameworks() {
      try {
        this.loading = true;
        console.log('🔍 [ComplianceVersioning] Checking for cached framework data...');
        
        // FIRST: Try to get data from cache
        if (complianceDataService.hasFrameworksCache()) {
          console.log('✅ [ComplianceVersioning] Using cached framework data');
          const cachedFrameworks = complianceDataService.getData('frameworks') || [];
          
          // Map the data to match the expected format in the component
          this.frameworks = cachedFrameworks.map(fw => ({
            FrameworkId: fw.FrameworkId || fw.id,
            FrameworkName: fw.FrameworkName || fw.name,
            Category: fw.Category || fw.category || '',
            Status: fw.ActiveInactive || fw.status || '',
            Description: fw.FrameworkDescription || fw.description || ''
          }));
          
          console.log(`[ComplianceVersioning] Loaded ${this.frameworks.length} frameworks from cache (prefetched on Home page)`);
          
          // Update framework config with filtered frameworks
          this.updateFrameworkConfig();
        } else {
          // FALLBACK: Fetch from API if cache is empty
          console.log('⚠️ [ComplianceVersioning] No cached data found, fetching from API...');
          // Add active_only=true parameter to only fetch active frameworks
          const response = await complianceService.getComplianceFrameworks({ active_only: 'true' });
          console.log('Frameworks API response:', response.data);
          
          // Handle both response formats: direct array or success wrapper
          let frameworksData = [];
          if (response.data.success && response.data.frameworks) {
            frameworksData = response.data.frameworks;
          } else if (response.data.success && Array.isArray(response.data.data)) {
            frameworksData = response.data.data;
          } else if (Array.isArray(response.data)) {
            frameworksData = response.data;
          } else {
            console.error('Unexpected response format:', response.data);
          }
          
          // Map the data to match the expected format in the component
          this.frameworks = frameworksData.map(fw => ({
            FrameworkId: fw.id || fw.FrameworkId,
            FrameworkName: fw.name || fw.FrameworkName,
            Category: fw.category || fw.Category || '',
            Status: fw.status || fw.ActiveInactive || '',
            Description: fw.description || fw.FrameworkDescription || ''
          }));
          
          console.log(`[ComplianceVersioning] Loaded ${this.frameworks.length} frameworks directly from API (cache unavailable)`);
          
          // Update cache so subsequent pages benefit
          if (frameworksData.length > 0) {
            complianceDataService.setData('frameworks', frameworksData);
            console.log('ℹ️ [ComplianceVersioning] Cache updated after direct API fetch');
          }
          
          // Update framework config with filtered frameworks
          this.updateFrameworkConfig();
        }
      } catch (error) {
        console.error('Error loading frameworks:', error);
        // Check if it's an access control error
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showComplianceFrameworkDenied();
          return;
        }
        this.error = 'Failed to load frameworks';
      } finally {
        this.loading = false;
      }
    },
    async loadPolicies() {
      if (!this.selectedFramework) {
        this.policies = [];
        this.selectedPolicy = '';
        return;
      }
      console.log('Calling getCompliancePolicies with ID:', this.selectedFramework);
      try {
        this.loading = true;
        const response = await complianceService.getCompliancePolicies(this.selectedFramework);
        console.log('Policies API response:', response.data);
        
        let policiesData = [];
        if (response.data.success && response.data.policies) {
          policiesData = response.data.policies;
        } else if (response.data.success && Array.isArray(response.data.data)) {
          policiesData = response.data.data;
        } else if (Array.isArray(response.data)) {
          policiesData = response.data;
        } else {
          console.error('Unexpected response format:', response.data);
        }
        
        // Map the data to match the expected format in the component
        this.policies = policiesData.map(p => ({
          PolicyId: p.id || p.PolicyId,
          PolicyName: p.name || p.PolicyName,
          Applicability: p.applicability || p.scope || p.Applicability || '',
          Status: p.status || p.ActiveInactive || ''
        }));
        
        console.log('Mapped policies:', this.policies);
        this.policyDropdownConfig.values = this.policies.map(p => ({
          value: p.PolicyId,
          label: p.PolicyName
        }));
        this.selectedPolicy = '';
        this.selectedSubPolicy = '';
      } catch (error) {
        console.error('Error loading policies:', error);
        // Check if it's an access control error
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showCompliancePolicyDenied();
          return;
        }
        this.error = 'Failed to load policies';
      } finally {
        this.loading = false;
      }
    },
    async loadSubPolicies() {
      if (!this.selectedPolicy) {
        this.subPolicies = [];
        this.selectedSubPolicy = '';
        return;
      }
      try {
        this.loading = true;
        const response = await complianceService.getComplianceSubPolicies(this.selectedPolicy);
        console.log('SubPolicies API response:', response.data);
        
        let subpoliciesData = [];
        if (response.data.success && response.data.subpolicies) {
          subpoliciesData = response.data.subpolicies;
        } else if (response.data.success && Array.isArray(response.data.data)) {
          subpoliciesData = response.data.data;
        } else if (Array.isArray(response.data)) {
          subpoliciesData = response.data;
        } else {
          console.error('Unexpected response format:', response.data);
        }
        
        // Map the data to match the expected format in the component
        this.subPolicies = subpoliciesData.map(sp => ({
          SubPolicyId: sp.id || sp.SubPolicyId,
          SubPolicyName: sp.name || sp.SubPolicyName,
          Status: sp.status || sp.Status || '',
          Description: sp.description || sp.Description || '',
          Control: sp.control || sp.Control || '',
          Identifier: sp.identifier || sp.Identifier || ''
        }));
        
        console.log('Mapped subpolicies:', this.subPolicies);
        this.subPolicyDropdownConfig.values = this.subPolicies.map(sp => ({
          value: sp.SubPolicyId,
          label: sp.SubPolicyName
        }));
        this.selectedSubPolicy = '';
      } catch (error) {
        console.error('Error loading subpolicies:', error);
        // Check if it's an access control error
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showComplianceSubpolicyDenied();
          return;
        }
        this.error = 'Failed to load subpolicies';
      } finally {
        this.loading = false;
      }
    },
    async loadCompliances() {
      if (!this.selectedSubPolicy) {
        this.compliances = [];
        return;
      }
      try {
        this.loading = true;
        console.log(`Loading compliances for subpolicy ID: ${this.selectedSubPolicy}`);
        
        // Use the compliance service instead of direct axios
        const response = await complianceService.getCompliancesBySubPolicy(this.selectedSubPolicy);
        console.log('Compliance API response:', response.data);
        
        if (response.data.success) {
          // Check the structure of the response data
          if (Array.isArray(response.data.data)) {
            // If it's a direct array or nested array - flatten it in case it's nested
            this.compliances = response.data.data.flat();
          } else if (response.data.compliances && Array.isArray(response.data.compliances)) {
            // If it's stored in a 'compliances' field
            this.compliances = response.data.compliances;
          } else {
            console.error('Unexpected data structure:', response.data);
            this.compliances = [];
          }
          
          // Debug: Check if PreviousComplianceVersionId is present in any compliance records
          if (this.compliances.length > 0) {
            console.log('First compliance record:', this.compliances[0]);
            console.log('PreviousComplianceVersionId exists:', 
              this.compliances.some(c => c.PreviousComplianceVersionId !== undefined));
            
            // Log all compliance keys to verify what's available
            console.log('Compliance record keys:', Object.keys(this.compliances[0]));
            
            // Adapt the previous version property if needed
            this.compliances = this.compliances.map(c => {
              // If PreviousVersionId exists but PreviousComplianceVersionId doesn't
              if (c.PreviousVersionId !== undefined && c.PreviousComplianceVersionId === undefined) {
                return {
                  ...c,
                  PreviousComplianceVersionId: c.PreviousVersionId
                };
              }
              return c;
            });
          } else {
            console.log('No compliances returned from API');
          }
        } else {
          console.error('Error in response:', response.data);
          this.error = response.data.message || 'Failed to load compliances';
        }
      } catch (error) {
        console.error('Error loading compliances:', error);
        
        // Check if it's an access control error
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showComplianceViewDenied();
          return;
        }
        
        // Check if it's a 500 error
        if (error.response && error.response.status === 500) {
          console.error('Server error (500):', error.response.data);
          this.error = 'Server error: The compliance data could not be loaded. Please try again later or contact support.';
          
          // Try to use the alternative endpoint
          try {
            console.log('Attempting to use alternative endpoint...');
            const altResponse = await complianceService.getCompliancesByType('subpolicy', this.selectedSubPolicy);
            if (altResponse.data.success && altResponse.data.compliances) {
              this.compliances = altResponse.data.compliances;
              this.error = null;
              console.log('Successfully loaded compliances from alternative endpoint');
            }
          } catch (altError) {
            console.error('Alternative endpoint also failed:', altError);
            // Check access control for alternative endpoint too
            if (altError.response && [401, 403].includes(altError.response.status)) {
              AccessUtils.showComplianceViewDenied();
              return;
            }
          }
        } else {
          this.error = error.message || 'Failed to load compliances';
        }
      } finally {
        this.loading = false;
      }
    },
    async toggleActiveStatus(compliance) {
      if (compliance.Status !== 'Approved') {
        alert('Only approved compliances can be toggled');
        return;
      }
      
      // If trying to deactivate, show the deactivation dialog
      if (compliance.ActiveInactive === 'Active') {
        this.complianceToDeactivate = compliance;
        this.deactivationReason = '';
        this.cascadeToPolicies = true;
        this.showDeactivationDialog = true;
        // Reset the checkbox state to maintain consistency with actual status
        document.getElementById(`toggle-${compliance.ComplianceId}`).checked = true;
        return;
      }
      
      // Otherwise proceed with normal toggle for activation
      try {
        this.loading = true;
        this.error = null;
        
        console.log(`Toggling compliance ${compliance.ComplianceId} to Active`);
        
        let response;
        
        try {
          // Try the primary endpoint first
          response = await complianceService.toggleComplianceVersion(compliance.ComplianceId);
          console.log('Toggle response from primary endpoint:', response.data);
        } catch (primaryError) {
          console.error('Primary endpoint failed:', primaryError);
          
          // If the primary endpoint fails with a 404, try the alternative endpoint
          if (primaryError.response && primaryError.response.status === 404) {
            console.log('Trying alternative toggle endpoint...');
            
            // Create a simple toggle request payload
            const toggleData = {
              compliance_id: compliance.ComplianceId,
              new_status: compliance.ActiveInactive === 'Active' ? 'Inactive' : 'Active'
            };
            
            // Try alternative endpoint
            try {
              response = await axios.post(API_ENDPOINTS.COMPLIANCE_TOGGLE_VERSION(compliance.ComplianceId), toggleData);
              console.log('Toggle response from alternative endpoint:', response.data);
            } catch (altError) {
              console.error('Alternative endpoint also failed:', altError);
              throw altError; // Re-throw to be caught by the outer catch
            }
          } else {
            throw primaryError; // Re-throw to be caught by the outer catch
          }
        }
        
        if (response && response.data && response.data.success) {
          console.log(`Successfully toggled compliance to ${response.data.new_status}`);
          // Refresh the data
          await this.loadCompliances();
        } else {
          const errorMsg = (response && response.data && response.data.message) || 'Error toggling compliance status';
          console.error('Error in toggle response:', errorMsg);
          this.error = `Failed to toggle compliance status: ${errorMsg}`;
          
          // Reset the checkbox state to match the actual status
          const checkbox = document.getElementById(`toggle-${compliance.ComplianceId}`);
          if (checkbox) {
            checkbox.checked = compliance.ActiveInactive === 'Active';
          }
        }
      } catch (error) {
        console.error('Error toggling compliance status:', error);
        
        // Check if it's an access control error
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showComplianceToggleDenied();
          // Reset the checkbox state to match the actual status
          const checkbox = document.getElementById(`toggle-${compliance.ComplianceId}`);
          if (checkbox) {
            checkbox.checked = compliance.ActiveInactive === 'Active';
          }
          return;
        }
        
        // Show detailed error information
        let errorMsg = 'Error toggling compliance status';
        if (error.response) {
          console.error('Error response:', error.response.data);
          errorMsg += `: ${error.response.data.message || error.response.statusText}`;
        } else if (error.request) {
          console.error('Error request:', error.request);
          errorMsg += ' - No response received from server';
        } else {
          errorMsg += `: ${error.message}`;
        }
        
        this.error = errorMsg;
        
        // Reset the checkbox state to match the actual status
        const checkbox = document.getElementById(`toggle-${compliance.ComplianceId}`);
        if (checkbox) {
          checkbox.checked = compliance.ActiveInactive === 'Active';
        }
      } finally {
        this.loading = false;
      }
    },
    async submitDeactivation() {
      if (!this.complianceToDeactivate) return;
      if (!this.deactivationReason.trim()) {
        alert('Please provide a reason for deactivation');
        return;
      }
      if (!this.selectedReviewer) {
        alert('Please select a reviewer');
        return;
      }
      // Get logged-in user_id from localStorage
      const userId = localStorage.getItem('user_id');
      if (!userId) {
        alert('User not logged in. Please log in again.');
        return;
      }
      try {
        this.loading = true;
        console.log('Submitting deactivation request for compliance:', this.complianceToDeactivate.ComplianceId);
        const response = await complianceService.deactivateCompliance(
          this.complianceToDeactivate.ComplianceId, 
          {
            reason: this.deactivationReason,
            cascade_to_policies: this.cascadeToPolicies,
            user_id: userId,
            reviewer_id: this.selectedReviewer
          }
        );
        if (response.data.success) {
          this.showDeactivationDialog = false;
          this.showDeactivationConfirmation = true;
          await this.loadCompliances();
          console.log('Deactivation request submitted successfully with approval ID:', response.data.approval_id);
        } else {
          alert(response.data.message || 'Error submitting deactivation request');
        }
      } catch (error) {
        console.error('Error submitting deactivation request:', error);
        if (error.response && [401, 403].includes(error.response.status)) {
          AccessUtils.showComplianceDeactivateDenied();
          this.showDeactivationDialog = false;
          this.complianceToDeactivate = null;
          return;
        }
        const errorMessage = error.response?.data?.message || error.message || 'Error submitting deactivation request';
        alert(`Error: ${errorMessage}`);
      } finally {
        this.loading = false;
      }
    },
    cancelDeactivation() {
      this.showDeactivationDialog = false;
      this.complianceToDeactivate = null;
    },
    closeDeactivationConfirmation() {
      this.showDeactivationConfirmation = false;
    },
    formatDate(date) {
      if (!date) return 'N/A';
      return new Date(date).toLocaleDateString();
    },
    getPreviousVersionDisplay(compliance) {
      if (!compliance.PreviousComplianceVersionId) return 'None';
      
      // Find the previous version in all compliances to get its version number
      const prevVersion = this.compliances.find(c => 
        c.ComplianceId === compliance.PreviousComplianceVersionId);
      
      if (prevVersion) {
        return `v${prevVersion.ComplianceVersion}`;
      }
      
      // If we can't find the previous version in the loaded compliances,
      // at least show the ID
      return `ID: ${compliance.PreviousComplianceVersionId}`;
    },
    handleSearch() {
      // Filtering is handled reactively in computed property
    },
    refreshCurrentData() {
      this.error = null;
      if (this.selectedSubPolicy) {
        this.loadCompliances();
      } else if (this.selectedPolicy) {
        this.loadSubPolicies();
      } else if (this.selectedFramework) {
        this.loadPolicies();
      } else {
        this.loadFrameworks();
      }
    },
    onFrameworkChange(option) {
      this.handleFrameworkChange(option);
    },
    onPolicyChange(option) {
      this.selectedPolicy = option.value;
      this.loadSubPolicies();
    },
    onSubPolicyChange(option) {
      this.selectedSubPolicy = option.value;
      this.loadCompliances();
    },
    async loadUsers() {
      try {
        const response = await complianceService.getUsers();
        if (response.data.success && Array.isArray(response.data.users)) {
          this.users = response.data.users;
          this.reviewerDropdownConfig.values = this.users.map(u => ({
            value: u.UserId,
            label: u.UserName
          }));
        } else {
          this.users = [];
          this.reviewerDropdownConfig.values = [];
        }
      } catch (error) {
        console.error('Error loading users:', error);
        this.users = [];
        this.reviewerDropdownConfig.values = [];
      }
    }
  }
}
</script>

<style scoped>
@import './ComplianceVersioning.css';

/* Add styles for deactivation dialog */
.deactivation-dialog-overlay {
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

.deactivation-dialog {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  width: 500px;
  max-width: 90%;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.deactivation-dialog h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #333;
}

.deactivation-reason-input {
  width: 100%;
  min-height: 80px;
  padding: 10px;
  margin-bottom: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: vertical;
}

.deactivation-options {
  margin-bottom: 20px;
}

.affected-count {
  margin-top: 5px;
  font-size: 0.9em;
  color: #666;
}

.deactivation-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.cancel-btn {
  padding: 8px 15px;
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.submit-btn {
  padding: 8px 15px;
  background-color: #4285f4;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.approval-info {
  margin: 15px 0;
  padding: 10px 15px;
  background-color: #e8f0fe;
  border-left: 4px solid #4285f4;
  border-radius: 0 4px 4px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.approval-info i {
  color: #4285f4;
  font-size: 18px;
}

/* Error message styles */
.error-message {
  margin: 20px;
  padding: 15px;
  background-color: #fff1f0;
  border: 1px solid #ffccc7;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.error-icon {
  font-size: 24px;
}

.error-text {
  flex-grow: 1;
  color: #cf1322;
  font-size: 14px;
}

.retry-button {
  padding: 6px 12px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.retry-button:hover {
  background-color: #40a9ff;
}

</style> 