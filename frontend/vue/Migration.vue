<template>
  <div class="M_migration-container">
    <!-- Navigation Breadcrumb -->
    <!-- Header -->
    <div class="M_migration-header">
      <div class="M_header-content">
        <h1 class="M_migration-title">Migration Gap Analysis</h1>
        <p class="M_migration-subtitle">Step-by-step migration from ISO 27001:2013 to 2022</p>
      </div>
      <button @click="navigateTo('/framework-migration')" class="M_back-button">
        <i class="fas fa-arrow-left"></i>
          Back to Overview
        </button>
    </div>

    <!-- Tabs -->
    <div class="M_tabs-container">
      <div class="M_tabs-list">
        <button 
          v-for="tab in tabs" 
          :key="tab.value"
          :class="['M_tab-button', { 'M_active': activeTab === tab.value }]"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Step 1: Latest Regulation -->
      <div v-if="activeTab === 'step1'" class="M_tab-content">
        <h3 class="M_section-title">
          Compliance Amendments in the latest regulation
          <span class="M_status-badge">ISO 27001:2022</span>
        </h3>
        <p class="M_section-description">
          Review all amendments and changes in the latest framework version
        </p>
            
            <!-- Compliance Table -->
            <div class="M_compliance-table-container">
              <div class="M_table-header">
                <div class="M_table-row">
                  <div class="M_table-cell">Policy</div>
                  <div class="M_table-cell">Sub-Policy</div>
                  <div class="M_table-cell">Compliance Item</div>
                  <div class="M_table-cell">Description</div>
                  <div class="M_table-cell">Status</div>
                </div>
              </div>
              
              <div class="M_table-body">
                <div 
                  v-for="policy in iso27001_2022.policies" 
                  :key="policy.id" 
                  class="M_policy-table-group"
                >
                  <!-- Policy Row -->
                  <div class="M_table-row M_policy-row">
                    <div class="M_table-cell M_policy-cell">
                      <div class="M_policy-info">
                        <span class="M_policy-id">{{ policy.id }}</span>
                        <span class="M_policy-name">{{ policy.name }}</span>
                      </div>
                    </div>
                    <div class="M_table-cell M_sub-policy-cell">
                      <span class="M_policy-description">{{ policy.description }}</span>
                    </div>
                    <div class="M_table-cell M_compliance-cell">
                      <span class="M_policy-count">{{ getPolicyComplianceCount(policy) }} items</span>
                    </div>
                    <div class="M_table-cell M_description-cell">
                      <span class="M_policy-summary">Policy overview</span>
                    </div>
                    <div class="M_table-cell M_status-cell">
                      <span class="M_status-badge M_status-badge-policy">Policy</span>
                    </div>
                  </div>
                  
                  <!-- Sub-Policy Rows -->
                  <div 
                    v-for="subPolicy in policy.subPolicies" 
                    :key="subPolicy.id" 
                    class="M_sub-policy-table-group"
                  >
                    <div class="M_table-row M_sub-policy-row">
                      <div class="M_table-cell M_policy-cell">
                        <div class="M_sub-policy-indent">
                          <span class="M_sub-policy-id">{{ subPolicy.id }}</span>
                        </div>
                      </div>
                      <div class="M_table-cell M_sub-policy-cell">
                        <span class="M_sub-policy-name">{{ subPolicy.name }}</span>
                      </div>
                      <div class="M_table-cell M_compliance-cell">
                        <span class="M_sub-policy-count">{{ subPolicy.compliances.length }} items</span>
                      </div>
                      <div class="M_table-cell M_description-cell">
                        <span class="M_sub-policy-description">{{ subPolicy.description }}</span>
                      </div>
                      <div class="M_table-cell M_status-cell">
                        <span class="M_status-badge M_status-badge-sub-policy">Sub-Policy</span>
                      </div>
                    </div>
                    
                    <!-- Compliance Item Rows -->
                    <div 
                      v-for="compliance in subPolicy.compliances" 
                      :key="compliance.id" 
                      class="M_compliance-table-row"
                    >
                      <div class="M_table-row M_compliance-row">
                        <div class="M_table-cell M_policy-cell">
                          <div class="M_compliance-indent">
                            <span class="M_compliance-id">{{ compliance.id }}</span>
                          </div>
                        </div>
                        <div class="M_table-cell M_sub-policy-cell">
                          <span class="M_compliance-name">{{ compliance.name }}</span>
                        </div>
                        <div class="M_table-cell M_compliance-cell">
                          <span class="M_compliance-type">{{ getComplianceType(compliance) }}</span>
                        </div>
                        <div class="M_table-cell M_description-cell">
                          <span class="M_compliance-description">{{ compliance.description }}</span>
                        </div>
                        <div class="M_table-cell M_status-cell">
                          <span :class="`M_status-badge M_status-badge-${compliance.changeType || 'unchanged'}`">
                            {{ getChangeLabel(compliance.changeType) }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
        <div v-if="iso27001_2022.policies.length === 0" class="M_empty-state">
          <p>No compliance data found in the selected framework version.</p>
        </div>
      </div>

      <!-- Step 2: Gap Assessment -->
      <div v-if="activeTab === 'step2'" class="M_tab-content">
        <h3 class="M_section-title">
          Please Select the Currently Uncomplied Regulation
          <span class="M_status-badge">ISO 27001:2013</span>
        </h3>
        
        <div class="M_upload-section">
          <button class="M_upload-button">
            <i class="fas fa-upload"></i>
            Upload Existing Compliance Checklist
          </button>
        </div>
            
            <div class="M_search-section">
              <div class="M_search-input-wrapper">
              <input
                v-model="searchTerm"
                placeholder="Search by policy or sub-policy name..."
                  class="M_search-input"
              />
              </div>
            </div>
            
            <p class="M_assessment-description">
              Check the items that are currently non-compliant in your organization:
            </p>
            
            <div class="M_policies-list">
              <div 
                v-for="policy in filteredPolicies" 
                :key="policy.id" 
                class="M_policy-item"
              >
                <div 
                  class="M_policy-header"
                  @click="togglePolicy(policy.id)"
                >
                  <i v-if="isPolicyExpanded(policy.id)" class="fas fa-chevron-down M_toggle-icon"></i>
                  <i v-else class="fas fa-chevron-right M_toggle-icon"></i>
                  <div class="M_policy-info">
                    <span class="M_policy-name">{{ policy.id }} - {{ policy.name }}</span>
                    <p class="M_policy-description">{{ policy.description }}</p>
                  </div>
                </div>
                
                <div v-if="isPolicyExpanded(policy.id)" class="M_policy-content">
                  <div 
                    v-for="subPolicy in policy.subPolicies" 
                    :key="subPolicy.id" 
                    class="M_sub-policy-item"
                  >
                    <div 
                      class="M_sub-policy-header"
                      @click="toggleSubPolicy(subPolicy.id)"
                    >
                      <i v-if="isSubPolicyExpanded(subPolicy.id)" class="fas fa-chevron-down M_toggle-icon"></i>
                      <i v-else class="fas fa-chevron-right M_toggle-icon"></i>
                      <span class="M_sub-policy-name">{{ subPolicy.name }}</span>
                    </div>
                    
                    <div v-if="isSubPolicyExpanded(subPolicy.id)" class="M_sub-policy-content">
                      <p class="M_sub-policy-description">{{ subPolicy.description }}</p>
                      <div 
                        v-for="compliance in subPolicy.compliances" 
                        :key="compliance.id" 
                        class="M_compliance-checkbox"
                      >
                        <input
                          :id="compliance.id"
                          type="checkbox"
                          :checked="selectedNonCompliant.has(compliance.id)"
                          @change="handleNonCompliantChange(compliance.id, $event.target.checked)"
                          class="M_checkbox-input"
                        />
                        <label :for="compliance.id" class="M_checkbox-label">
                          {{ compliance.name }}
                        </label>
                        <span class="M_checkbox-hint">Check if non-compliant</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
      </div>

      <!-- Step 3: Gap Analysis -->
      <div v-if="activeTab === 'step3'" class="M_tab-content">
        <h3 class="M_section-title">Gap Analysis Results</h3>
        
        <div class="M_analysis-header">
          <p class="M_analysis-description">
            Comprehensive list of all items requiring attention based on your gap assessment
          </p>
          <div class="M_analysis-stats">
            <span class="M_stat-badge">
              {{ gapAnalysisItems.length + getNewRequirementsWithMapping().length }} Total Items
            </span>
          </div>
        </div>
              
              <!-- Summary Cards -->
            <div class="M_summary-cards-grid">
              <div class="M_summary-card M_summary-card-partial">
                <div class="M_summary-card-content">
                  <div class="M_summary-card-info">
                    <p class="M_summary-card-label">Non-Compliant (2013)</p>
                    <p class="M_summary-card-number">{{ gapAnalysisItems.length }}</p>
                      </div>
                  <i class="fas fa-times-circle M_summary-card-icon"></i>
                  </div>
                </div>
                
              <div class="M_summary-card M_summary-card-new">
                <div class="M_summary-card-content">
                  <div class="M_summary-card-info">
                    <p class="M_summary-card-label">New Requirements (2022)</p>
                    <p class="M_summary-card-number">{{ getNewRequirementsWithMapping().length }}</p>
                      </div>
                  <i class="fas fa-check-circle M_summary-card-icon"></i>
                  </div>
                </div>
                
              <div class="M_summary-card M_summary-card-total">
                <div class="M_summary-card-content">
                  <div class="M_summary-card-info">
                    <p class="M_summary-card-label">Total Action Items</p>
                    <p class="M_summary-card-number">{{ gapAnalysisItems.length + getNewRequirementsWithMapping().length }}</p>
                      </div>
                  <i class="fas fa-search M_summary-card-icon"></i>
                  </div>
                </div>
              </div>
              
            <!-- Gap Items Table -->
            <div class="M_gap-items-section">
              <h3 class="M_section-title">Identified Gaps & Requirements</h3>
              
              <div class="M_gap-table-container">
                <div class="M_table-header">
                  <div class="M_table-row">
                    <div class="M_table-cell">Policy</div>
                    <div class="M_table-cell">Sub-Policy</div>
                    <div class="M_table-cell">Requirement</div>
                    <div class="M_table-cell">Description</div>
                    <div class="M_table-cell">Action Required</div>
                    <div class="M_table-cell">Priority</div>
                    <div class="M_table-cell">Status</div>
                  </div>
                </div>
                
                <div class="M_table-body">
                  <!-- Items from 2013 non-compliance -->
                  <div 
                    v-for="item in gapAnalysisItems" 
                    :key="item.id" 
                    class="M_table-row M_gap-item-row"
                  >
                    <div class="M_table-cell M_policy-cell">
                      <div class="M_policy-info">
                        <span class="M_policy-id">{{ item.policyId }}</span>
                        <span class="M_policy-name">{{ item.policy }}</span>
                      </div>
                    </div>
                    <div class="M_table-cell M_sub-policy-cell">
                      <div class="M_sub-policy-info">
                        <span class="M_sub-policy-id">{{ item.subPolicyId }}</span>
                        <span class="M_sub-policy-name">{{ item.subPolicy }}</span>
                      </div>
                    </div>
                    <div class="M_table-cell M_requirement-cell">
                      <span class="M_requirement-name">{{ item.policyName }}</span>
                    </div>
                    <div class="M_table-cell M_description-cell">
                      <span class="M_requirement-description">{{ item.description }}</span>
                    </div>
                    <div class="M_table-cell M_action-cell">
                      <span class="M_action-required">{{ item.requirementAction }}</span>
                    </div>
                    <div class="M_table-cell M_priority-cell">
                      <span class="M_priority-badge M_priority-high">{{ item.priority }}</span>
                    </div>
                    <div class="M_table-cell M_status-cell">
                      <span class="M_status-badge M_status-non-compliant">
                        <i class="fas fa-times-circle"></i>
                        {{ item.status }}
                      </span>
                    </div>
                  </div>
                  
                  <!-- New 2022 requirements -->
                  <div 
                    v-for="requirement in getNewRequirementsWithMapping()" 
                    :key="requirement.id" 
                    class="M_table-row M_gap-item-row M_new-requirement"
                  >
                    <div class="M_table-cell M_policy-cell">
                      <div class="M_policy-info">
                        <span class="M_policy-id">{{ requirement.policyId }}</span>
                        <span class="M_policy-name">{{ requirement.policyName }}</span>
                      </div>
                    </div>
                    <div class="M_table-cell M_sub-policy-cell">
                      <div class="M_sub-policy-info">
                        <span class="M_sub-policy-id">{{ requirement.subPolicyId }}</span>
                        <span class="M_sub-policy-name">{{ requirement.subPolicyName }}</span>
                      </div>
                    </div>
                    <div class="M_table-cell M_requirement-cell">
                      <span class="M_requirement-name">{{ requirement.name }}</span>
                    </div>
                    <div class="M_table-cell M_description-cell">
                      <span class="M_requirement-description">{{ requirement.description }}</span>
                    </div>
                    <div class="M_table-cell M_action-cell">
                      <span class="M_action-required">{{ getRequirementAction(requirement) }}</span>
                    </div>
                    <div class="M_table-cell M_priority-cell">
                      <span class="M_priority-badge" :class="getPriorityClass(requirement)">{{ getPriority(requirement) }}</span>
                    </div>
                    <div class="M_table-cell M_status-cell">
                      <span class="M_status-badge M_status-new">
                        <i class="fas fa-check-circle"></i>
                        New
                      </span>
                    </div>
                  </div>
                  
                  <div v-if="gapAnalysisItems.length === 0 && getNewRequirementsWithMapping().length === 0" class="M_empty-state">
                    <i class="fas fa-search M_empty-icon"></i>
                    <h3 class="M_empty-title">No Gaps Identified</h3>
                    <p class="M_empty-description">
                          Complete Step 2 (Gap Assessment) to identify compliance gaps and see analysis results here.
                        </p>
                    <button class="M_empty-action" @click="activeTab = 'step2'">
                          Go to Gap Assessment
                        </button>
                  </div>
                </div>
              </div>
            </div>
      </div>
    </div>
  </div>
</template>

<script>
import { iso27001_2013, iso27001_2022 } from './iso27001Data.js'

export default {
  name: 'FrameworkMigrationProcess',
  data() {
    return {
      activeTab: 'step1',
      expandedPolicies: new Set(),
      expandedSubPolicies: new Set(),
      searchTerm: '',

      selectedNonCompliant: new Set(),
      gapAnalysisItems: [],
      iso27001_2013,
      iso27001_2022,
      tabs: [
        { value: 'step1', label: 'Step 1: Amendments in latest regulation' },
        { value: 'step2', label: 'Step 2: Compliance Checklist' },
        { value: 'step3', label: 'Step 3: Gap Analysis' }
      ]
    }
  },
  computed: {
    newRequirements() {
      return this.iso27001_2022.policies.flatMap(policy =>
        policy.subPolicies.flatMap(subPolicy =>
          subPolicy.compliances.filter(compliance => compliance.changeType === 'new')
        )
      )
    },
    filteredPolicies() {
      return this.iso27001_2013.policies.filter(policy => 
        policy.name.toLowerCase().includes(this.searchTerm.toLowerCase())
      )
    }
  },
  methods: {
    navigateTo(path) {
      this.$router.push(path)
    },
    togglePolicy(policyId) {
      if (this.expandedPolicies.has(policyId)) {
        this.expandedPolicies.delete(policyId)
      } else {
        this.expandedPolicies.add(policyId)
      }
    },
    toggleSubPolicy(subPolicyId) {
      if (this.expandedSubPolicies.has(subPolicyId)) {
        this.expandedSubPolicies.delete(subPolicyId)
      } else {
        this.expandedSubPolicies.add(subPolicyId)
      }
    },
    isPolicyExpanded(policyId) {
      return this.expandedPolicies.has(policyId)
    },
    isSubPolicyExpanded(subPolicyId) {
      return this.expandedSubPolicies.has(subPolicyId)
    },
    handleNonCompliantChange(complianceId, checked) {
      if (checked) {
        this.selectedNonCompliant.add(complianceId)
      } else {
        this.selectedNonCompliant.delete(complianceId)
      }
      
      // Update gap analysis items
      this.gapAnalysisItems = Array.from(this.selectedNonCompliant).map(id => {
        const allCompliances = this.iso27001_2013.policies.flatMap(p => 
          p.subPolicies.flatMap(sp => sp.compliances)
        )
        const compliance = allCompliances.find(c => c.id === id)
        
        // Find the parent policy and subpolicy
        let parentPolicy = null
        let parentSubPolicy = null
        
        for (const policy of this.iso27001_2013.policies) {
          for (const subPolicy of policy.subPolicies) {
            if (subPolicy.compliances.some(c => c.id === id)) {
              parentPolicy = policy
              parentSubPolicy = subPolicy
              break
            }
          }
          if (parentPolicy) break
        }
        
        return {
          id,
          policyName: compliance?.name || '',
          description: compliance?.description || '',
          source: '2013 non-compliance',
          policy: parentPolicy?.name || '',
          policyId: parentPolicy?.id || '',
          subPolicy: parentSubPolicy?.name || '',
          subPolicyId: parentSubPolicy?.id || '',
          requirementAction: compliance?.requirementAction || 'Review and implement',
          priority: compliance?.priority || 'High',
          status: 'Non-Compliant'
        }
      })
    },
    getPolicyComplianceCount(policy) {
      return policy.subPolicies.reduce((total, subPolicy) => {
        return total + subPolicy.compliances.length
      }, 0)
    },
    getComplianceType(compliance) {
      return compliance.changeType || 'unchanged'
    },
    getChangeLabel(changeType) {
      const labels = {
        new: 'New',
        modified: 'Modified',
        removed: 'Removed',
        unchanged: 'Unchanged'
      }
      return labels[changeType] || 'Unchanged'
    },
    getNewRequirementsWithMapping() {
      return this.iso27001_2022.policies.flatMap(policy =>
        policy.subPolicies.flatMap(subPolicy =>
          subPolicy.compliances.filter(compliance => compliance.changeType === 'new').map(compliance => ({
            ...compliance,
            policyId: policy.id,
            policyName: policy.name,
            subPolicyId: subPolicy.id,
            subPolicyName: subPolicy.name
          }))
        )
      )
    },
    getRequirementAction(requirement) {
      // Map requirement actions based on the requirement type
      const actionMap = {
        'Information Security Roles and Responsibilities': 'Define and document information security roles and responsibilities',
        'Segregation of Duties': 'Review and update segregation of duties matrix',
        'Management Responsibilities': 'Establish management oversight and accountability framework',
        'Contact with Authorities': 'Maintain appropriate contacts with authorities',
        'Contact with Special Interest Groups': 'Establish relationships with security forums and professional associations',
        'Threat Intelligence': 'Implement threat intelligence collection and analysis capabilities',
        'Information Security in Project Management': 'Integrate security requirements into project management methodology',
        'Inventory of Information and Other Associated Assets': 'Complete asset inventory and establish maintenance procedures',
        'Acceptable Use of Information and Other Associated Assets': 'Update acceptable use policies and procedures',
        'Return of Assets': 'Review and update asset return procedures',
        'Classification of Information': 'Review and update information classification scheme',
        'Labelling of Information': 'Implement information labeling procedures',
        'Information Transfer': 'Establish secure information transfer procedures',
        'Access Control': 'Review and update access control policies',
        'Identity Verification': 'Enhance user registration and de-registration processes',
        'Access Rights and Access Management': 'Implement formal access provisioning and revocation processes',
        'Information Security in Supplier Relationships': 'Establish supplier security requirements and agreements',
        'ICT Supply Chain Security': 'Implement ICT supply chain security controls',
        'Monitoring, Review and Change Management of Supplier Services': 'Establish supplier service monitoring and review processes',
        'Information Security for Use of Cloud Services': 'Develop cloud service security framework',
        'Information Security Incident Management': 'Enhance incident detection and assessment capabilities',
        'Information Security Incident Management Process': 'Establish comprehensive incident management process',
        'Incident Reporting': 'Implement incident reporting procedures and channels',
        'Incident Learning': 'Establish incident learning and improvement processes',
        'Collection of Evidence': 'Implement evidence collection and preservation procedures',
        'Information Security During Disruption': 'Develop business continuity security procedures',
        'ICT Readiness for Business Continuity': 'Establish ICT continuity planning and testing',
        'Legal, Statutory, Regulatory and Contractual Requirements': 'Conduct comprehensive compliance assessment',
        'Protection of Records': 'Review and update records protection procedures',
        'Privacy and Protection of PII': 'Implement PII protection controls and procedures',
        'Protection of Information in Cloud Services': 'Implement cloud information protection controls',
        'Independent Review of Information Security': 'Establish independent security review program',
        'Compliance with Policies, Rules and Standards': 'Implement compliance monitoring and review processes',
        'Documented Operating Procedures': 'Review and update operating procedures',
        'Change Management': 'Enhance change management processes',
        'Capacity Management': 'Implement capacity monitoring and planning',
        'Separation of Development, Test and Production Environments': 'Review environment separation controls'
      }
      
      return actionMap[requirement.name] || 'Implement new requirement'
    },
    getPriority(requirement) {
      // Map priorities based on the requirement
      const priorityMap = {
        'Information Security Roles and Responsibilities': 'High',
        'Segregation of Duties': 'High',
        'Management Responsibilities': 'High',
        'Contact with Authorities': 'Medium',
        'Contact with Special Interest Groups': 'Medium',
        'Threat Intelligence': 'High',
        'Information Security in Project Management': 'Medium',
        'Inventory of Information and Other Associated Assets': 'Medium',
        'Acceptable Use of Information and Other Associated Assets': 'Medium',
        'Return of Assets': 'Low',
        'Classification of Information': 'Low',
        'Labelling of Information': 'Medium',
        'Information Transfer': 'High',
        'Access Control': 'Low',
        'Identity Verification': 'Low',
        'Access Rights and Access Management': 'High',
        'Information Security in Supplier Relationships': 'High',
        'ICT Supply Chain Security': 'High',
        'Monitoring, Review and Change Management of Supplier Services': 'Medium',
        'Information Security for Use of Cloud Services': 'High',
        'Information Security Incident Management': 'High',
        'Information Security Incident Management Process': 'High',
        'Incident Reporting': 'Medium',
        'Incident Learning': 'Medium',
        'Collection of Evidence': 'Medium',
        'Information Security During Disruption': 'High',
        'ICT Readiness for Business Continuity': 'High',
        'Legal, Statutory, Regulatory and Contractual Requirements': 'High',
        'Protection of Records': 'Low',
        'Privacy and Protection of PII': 'High',
        'Protection of Information in Cloud Services': 'High',
        'Independent Review of Information Security': 'Medium',
        'Compliance with Policies, Rules and Standards': 'Medium',
        'Documented Operating Procedures': 'Low',
        'Change Management': 'Medium',
        'Capacity Management': 'Medium',
        'Separation of Development, Test and Production Environments': 'Low'
      }
      
      return priorityMap[requirement.name] || 'Medium'
    },
    getPriorityClass(requirement) {
      const priority = this.getPriority(requirement)
      return `priority-${priority.toLowerCase()}`
    }
  }
}
</script>

<style scoped>
.M_migration-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  margin-left: 280px;
}

.M_breadcrumb-nav {
  margin-bottom: 24px;
}

.M_breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.M_breadcrumb-link {
  color: var(--primary-color);
  cursor: pointer;
  text-decoration: none;
}

.M_breadcrumb-link:hover {
  text-decoration: underline;
}

.M_breadcrumb-separator {
  color: var(--text-secondary);
}

.M_breadcrumb-page {
  color: var(--text-primary);
  font-weight: 500;
}

.M_migration-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
}

.M_migration-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.M_migration-subtitle {
  color: var(--text-secondary);
  font-size: 1rem;
}

.M_back-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.M_back-button:hover {
  background: var(--secondary-color);
}

.M_tabs-container {
  margin-bottom: 24px;
}

.M_tabs-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  background: var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.M_tab-button {
  padding: 12px 16px;
  background: var(--card-bg);
  border: none;
  color: var(--text-secondary);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.M_tab-button:hover {
  background: var(--secondary-color);
  color: var(--text-primary);
}

.M_tab-button.M_active {
  background: var(--primary-color);
  color: white;
}

.M_tab-content {
  margin-top: 24px;
  padding: 24px 0;
}

.M_status-badge {
  background: var(--secondary-color);
  color: var(--text-primary);
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid var(--border-color);
}

.M_compliance-table-container {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  margin-top: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.M_table-header {
  background: var(--secondary-color);
  border-bottom: 1px solid var(--border-color);
}

.M_table-header .M_table-row {
  font-weight: 600;
  color: var(--text-primary);
  background: var(--secondary-color);
}

.M_table-body {
  max-height: 600px;
  overflow-y: auto;
}

.M_policy-table-group {
  border-bottom: 2px solid var(--border-color);
}

.M_policy-row {
  background: var(--card-bg);
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);
}

.M_sub-policy-table-group {
  border-bottom: 1px solid var(--border-color);
}

.M_sub-policy-row {
  background: rgba(0, 0, 0, 0.02);
  font-weight: 500;
  border-bottom: 1px solid var(--border-color);
}

.M_compliance-row {
  background: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
}

.M_compliance-row:hover {
  background: var(--secondary-color);
}

.M_table-row {
  display: grid;
  grid-template-columns: 1fr 1.5fr 1fr 2fr 1fr;
  gap: 16px;
  padding: 12px 16px;
  align-items: center;
  min-height: 48px;
}

.M_table-cell {
  font-size: 0.875rem;
  color: var(--text-primary);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.M_policy-cell {
  font-weight: 500;
}

.M_sub-policy-indent {
  padding-left: 16px;
  border-left: 2px solid var(--border-color);
}

.M_compliance-indent {
  padding-left: 32px;
  border-left: 2px solid var(--border-color);
}

.M_policy-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.M_policy-id {
  font-weight: 600;
  color: var(--primary-color);
  font-size: 0.875rem;
}

.M_policy-name {
  font-weight: 600;
  color: var(--text-primary);
}

.M_policy-description {
  color: var(--text-secondary);
  font-size: 0.75rem;
  line-height: 1.4;
}

.M_sub-policy-id {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 0.875rem;
}

.M_sub-policy-name {
  font-weight: 500;
  color: var(--text-primary);
}

.M_sub-policy-description {
  color: var(--text-secondary);
  font-size: 0.75rem;
  line-height: 1.4;
}

.M_compliance-id {
  font-weight: 400;
  color: var(--text-secondary);
  font-size: 0.75rem;
}

.M_compliance-name {
  font-weight: 500;
  color: var(--text-primary);
}

.M_compliance-type {
  color: var(--text-secondary);
  font-size: 0.75rem;
}

.M_compliance-description {
  color: var(--text-secondary);
  font-size: 0.75rem;
  line-height: 1.4;
}

.M_policy-count,
.M_sub-policy-count {
  color: var(--text-secondary);
  font-size: 0.75rem;
  font-weight: 500;
}

.M_policy-summary {
  color: var(--text-secondary);
  font-size: 0.75rem;
  font-style: italic;
}

.M_status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.M_status-badge-policy {
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary-color);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.M_status-badge-sub-policy {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
  border: 1px solid rgba(107, 114, 128, 0.3);
}

.M_status-badge-new {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.M_status-badge-modified {
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary-color);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.M_status-badge-removed {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.M_status-badge-unchanged {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
  border: 1px solid rgba(107, 114, 128, 0.3);
}

.M_change-badge {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.625rem;
  font-weight: 600;
  border: 1px solid;
}

.M_change-badge-new {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  border-color: rgba(34, 197, 94, 0.3);
}

.M_upload-section {
  margin-bottom: 16px;
}

.M_upload-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.M_upload-button:hover {
  background: var(--secondary-color);
}

.M_search-section {
  margin-bottom: 16px;
  max-width: 300px !important;
}

.M_search-input-wrapper {
  position: relative;
  max-width: 400px;
}

.M_search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-secondary);
}

.M_search-input {
  width: 100%;
  padding: 8px 12px 8px 36px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--input-bg);
  color: var(--text-primary);
}

.M_assessment-description {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-bottom: 16px;
}

.M_policies-list {
  max-height: 500px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 24px;
}

.M_policy-item {
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--card-bg);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.M_policy-item:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.M_policy-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.M_policy-header:hover {
  background: var(--secondary-color);
}

.M_toggle-icon {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.M_policy-info {
  flex: 1;
}

.M_policy-name {
  font-weight: 600;
  color: var(--text-primary);
  display: block;
  margin-bottom: 4px;
}

.M_policy-description {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.M_policy-content {
  padding: 0 16px 16px 16px;
}

.M_sub-policy-item {
  border-left: 2px solid var(--border-color);
  margin-left: 16px;
  padding-left: 16px;
}

.M_sub-policy-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.M_sub-policy-header:hover {
  background: var(--secondary-color);
}

.M_sub-policy-name {
  font-weight: 500;
  color: var(--text-primary);
}

.M_sub-policy-content {
  margin-left: 24px;
  margin-top: 8px;
}

.M_sub-policy-description {
  color: var(--text-secondary);
  font-size: 0.75rem;
  margin-bottom: 12px;
}

.M_compliance-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: var(--secondary-color);
  border-radius: 6px;
  margin-bottom: 8px;
}

.M_checkbox-input {
  width: 16px;
  height: 16px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
}

.M_checkbox-label {
  font-weight: 500;
  color: var(--text-primary);
  cursor: pointer;
  flex: 1;
}

.M_checkbox-hint {
  color: var(--text-secondary);
  font-size: 0.75rem;
}

.M_analysis-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.M_analysis-description {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.M_stat-badge {
  background: var(--secondary-color);
  color: var(--text-primary);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid var(--border-color);
}

.M_summary-cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin: 32px 0;
}

.M_summary-card {
  border-left: 4px solid;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.M_summary-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.M_summary-card-partial {
  border-left-color: #f59e0b;
}

.M_summary-card-new {
  border-left-color: #22c55e;
}

.M_summary-card-total {
  border-left-color: var(--primary-color);
}

.M_summary-card-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.M_summary-card-label {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-bottom: 4px;
}

.M_summary-card-number {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.M_summary-card-icon {
  font-size: 2rem;
}

.M_summary-card-partial .M_summary-card-icon {
  color: #f59e0b;
}

.M_summary-card-new .M_summary-card-icon {
  color: #22c55e;
}

.M_summary-card-total .M_summary-card-icon {
  color: var(--primary-color);
}

.M_section-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.M_section-description {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin-bottom: 24px;
  line-height: 1.6;
}

.M_gap-items-section {
  margin-top: 32px;
}

.M_gap-table-container {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.M_gap-table-container .M_table-header {
  background: var(--background-secondary);
  border-bottom: 1px solid var(--border-color);
}

.M_gap-table-container .M_table-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1.5fr 2fr 1.5fr 1fr 1fr;
  gap: 16px;
  padding: 12px 16px;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
}

.M_gap-table-container .M_table-row:last-child {
  border-bottom: none;
}

.M_gap-item-row {
  transition: background-color 0.2s ease;
}

.M_gap-item-row:hover {
  background: #f9fafb;
}

.M_gap-item-row.M_new-requirement {
  background: transparent;
}

.M_gap-item-row.M_new-requirement:hover {
  background: #f9fafb;
}

.M_policy-info,
.M_sub-policy-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.M_policy-id,
.M_sub-policy-id {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.M_policy-name,
.M_sub-policy-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

.M_requirement-name {
  font-weight: 500;
  color: var(--text-primary);
}

.M_requirement-description {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.M_action-required {
  font-size: 0.875rem;
  color: var(--text-primary);
  font-weight: 500;
}

.M_priority-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.M_priority-high {
  background: #fef2f2;
  color: #dc2626;
}

.M_priority-medium {
  background: #fffbeb;
  color: #d97706;
}

.M_priority-low {
  background: #f0fdf4;
  color: #16a34a;
}

.M_status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.M_status-non-compliant {
  background: #fef2f2;
  color: #dc2626;
}

.M_status-new {
  background: #f0fdf4;
  color: #16a34a;
}

.M_status-compliant {
  background: #f0fdf4;
  color: #16a34a;
}

.M_empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--text-secondary);
}

.M_empty-icon {
  font-size: 3rem;
  margin-bottom: 16px;
  opacity: 0.5;
}

.M_empty-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.M_empty-description {
  font-size: 0.875rem;
  margin-bottom: 16px;
}

.M_empty-action {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.M_empty-action:hover {
  background: var(--secondary-color);
}



.M_table-header {
  background: var(--secondary-color);
  border-bottom: 1px solid var(--border-color);
}

.M_table-row {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr 1fr;
  gap: 16px;
  padding: 12px;
  align-items: center;
}

.M_table-header .M_table-row {
  font-weight: 600;
  color: var(--text-primary);
}

.M_table-body .M_table-row {
  border-bottom: 1px solid var(--border-color);
  transition: background-color 0.2s ease;
}

.M_table-body .M_table-row:hover {
  background: var(--secondary-color);
}

.M_table-body .M_table-row:last-child {
  border-bottom: none;
}

.M_cell-text {
  font-size: 0.875rem;
  color: var(--text-primary);
}

.M_status-select {
  padding: 4px 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 0.875rem;
}



@media (max-width: 768px) {
  .M_migration-container {
    padding: 16px;
  }
  
  .M_migration-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .M_tabs-list {
    grid-template-columns: 1fr;
  }
  
  .M_summary-cards-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .M_table-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .M_compliance-table-container .M_table-row {
    grid-template-columns: 1fr;
    gap: 8px;
    padding: 8px;
  }
  
  .M_gap-table-container .M_table-row {
    grid-template-columns: 1fr;
    gap: 8px;
    padding: 8px;
  }
  
  .M_table-cell {
    padding: 4px 0;
  }
  
  .M_policy-cell,
  .M_sub-policy-cell,
  .M_compliance-cell,
  .M_description-cell,
  .M_status-cell,
  .M_requirement-cell,
  .M_action-cell,
  .M_priority-cell {
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 8px;
  }
  

}
</style>
