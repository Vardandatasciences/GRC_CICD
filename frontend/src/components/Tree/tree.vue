<template>
  <div class="tree-container">
    <!-- Header elements displayed directly on screen -->
    <h1 class="main-title">Data Workflow - Hierarchical View</h1>
    <p class="main-subtitle">Explore your framework hierarchy interactively</p>
    
    <!-- Framework Selector with Controls -->
    <div class="framework-selector">
      <label for="framework-select">Select Framework:</label>
      <select 
        id="framework-select" 
        v-model="selectedFramework" 
        @change="onFrameworkChange"
        class="framework-dropdown"
      >
        <option value="">-- Choose a Framework --</option>
        <option 
          v-for="framework in frameworks" 
          :key="framework.FrameworkId" 
          :value="framework.FrameworkId"
        >
          {{ framework.FrameworkName }}
        </option>
      </select>
      
      <!-- Control Buttons -->
      <div class="control-buttons">
        <button @click="expandAll" class="control-btn expand-all-btn">EXPAND ALL</button>
        <button @click="collapseAll" class="control-btn collapse-btn">COLLAPSE</button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <i class="fas fa-spinner fa-spin"></i>
      <p>Loading data...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="error-container">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
      <button @click="loadFrameworks" class="retry-button">Retry</button>
    </div>

    <!-- Tree Visualization - Hierarchical Tree Layout -->
    <div v-if="!loading && !error && selectedFramework" class="tree-visualization" ref="treeVisualization">
      <!-- SVG Container for Curved Connection Lines -->
      <svg class="connection-lines-container" ref="connectionsSvg">
        <path
          v-for="(connection, index) in connectionPaths"
          :key="`connection-${index}`"
          :d="connection.path"
          :stroke="connection.color"
          stroke-width="2"
          fill="none"
          :stroke-dasharray="connection.dashed ? '5,5' : '0'"
          opacity="0.7"
        />
      </svg>
      
      <div class="tree-diagram">
        <div class="tree-table">
          <!-- Table Header Row -->
          <div class="tree-row header-row">
            <div class="tree-cell framework-header">Framework</div>
            <div class="tree-cell policies-header">Policies</div>
            <div class="tree-cell subpolicies-header">Sub Policies</div>
            <div class="tree-cell compliances-header">Compliances</div>
            <div class="tree-cell risks-header">Risks</div>
          </div>

          <!-- Framework Row -->
          <div class="tree-row">
            <div class="tree-cell framework-cell" :class="{ 'expanded': frameworkExpanded }">
              <div class="tree-node root-node" @click="toggleFrameworkExpansion">
                <div 
                  class="framework-icon-container"
                  @mouseenter="handleNodeHover('framework', selectedFramework, { FrameworkId: selectedFramework, FrameworkName: selectedFrameworkName }, $event)"
                  @mouseleave="handleNodeLeave"
                >
                  <i class="fas fa-sitemap framework-icon" :class="{ 'expanded': frameworkExpanded }"></i>
                  <div class="framework-name">{{ selectedFrameworkName }}</div>
                  <div class="framework-tooltip">{{ selectedFrameworkName }}</div>
                  <Teleport to="body">
                    <div 
                      v-if="hoveredNode === `framework-${selectedFramework}`"
                      class="metadata-tooltip"
                      :ref="`tooltip-framework-${selectedFramework}`"
                      @mouseenter.stop
                      @mouseleave.stop="handleNodeLeave"
                    >
                      <div class="metadata-header">
                        <h3>{{ hoveredNodeMetadata?.FrameworkName || selectedFrameworkName }}</h3>
                        <span class="metadata-type-badge">framework</span>
                      </div>
                      <div class="metadata-content">
                        <div v-if="metadataLoading" class="metadata-loading">Loading metadata...</div>
                        <template v-else>
                          <div v-if="Object.keys(getFilteredMetadata(hoveredNodeMetadata || { FrameworkId: selectedFramework, FrameworkName: selectedFrameworkName }, 'framework')).length === 0" class="metadata-empty">
                            No additional metadata available
                          </div>
                          <div v-for="(value, key) in getFilteredMetadata(hoveredNodeMetadata || { FrameworkId: selectedFramework, FrameworkName: selectedFrameworkName }, 'framework')" :key="key" class="metadata-item">
                            <span class="metadata-label">{{ formatLabel(key) }}:</span>
                            <span class="metadata-value">{{ formatValue(value) }}</span>
                          </div>
                        </template>
                      </div>
                    </div>
                  </Teleport>
                </div>
              </div>
            </div>
            <div class="tree-cell policies-cell">
              <div class="vertical-nodes">
                <div 
                  v-for="(policy, index) in treeData" 
                  :key="policy.id"
                  :data-node-id="`policy-${policy.id}`"
                  class="tree-node policy-node"
                  :class="{ 'expanded': expandedPolicies[policy.id] }"
                  :style="{ '--node-index': index }"
                  @click="togglePolicy(policy)"
                >
                  <div 
                    class="node-content"
                    @mouseenter="handleNodeHover('policy', policy.id, policy, $event)"
                    @mouseleave="handleNodeLeave"
                  >
                    <span class="node-label">{{ policy.PolicyName }}</span>
                    <i class="fas fa-chevron-right expand-icon" :class="{ 'rotated': expandedPolicies[policy.id] }"></i>
                    <div class="node-tooltip">{{ policy.PolicyName }}</div>
                    <Teleport to="body">
                      <div 
                        v-if="hoveredNode === `policy-${policy.id}`"
                        class="metadata-tooltip"
                        :ref="`tooltip-policy-${policy.id}`"
                        @mouseenter.stop
                        @mouseleave.stop="handleNodeLeave"
                      >
                        <div class="metadata-header">
                          <h3>{{ hoveredNodeMetadata?.PolicyName || policy.PolicyName }}</h3>
                          <span class="metadata-type-badge">policy</span>
                        </div>
                        <div class="metadata-content">
                          <div v-if="metadataLoading" class="metadata-loading">Loading metadata...</div>
                          <template v-else>
                            <div v-if="Object.keys(getFilteredMetadata(hoveredNodeMetadata || policy, 'policy')).length === 0" class="metadata-empty">
                              No additional metadata available
                            </div>
                            <div v-for="(value, key) in getFilteredMetadata(hoveredNodeMetadata || policy, 'policy')" :key="key" class="metadata-item">
                              <span class="metadata-label">{{ formatLabel(key) }}:</span>
                              <span class="metadata-value">{{ formatValue(value) }}</span>
                            </div>
                          </template>
                        </div>
                      </div>
                    </Teleport>
                  </div>
                </div>
              </div>
            </div>
            <div class="tree-cell subpolicies-cell">
              <div class="vertical-nodes">
                <template v-for="policy in treeData" :key="`sub-${policy.id}`">
                  <template v-if="expandedPolicies[policy.id] && subPoliciesData[policy.id]">
                    <div 
                      v-for="(subpolicy, subIndex) in subPoliciesData[policy.id]" 
                      :key="subpolicy.id"
                      :data-node-id="`subpolicy-${subpolicy.id}`"
                      :data-parent-id="`policy-${policy.id}`"
                      class="tree-node subpolicy-node"
                      :class="getSubPolicyClasses(subpolicy)"
                      :style="{ '--node-index': subIndex }"
                      @click="toggleSubPolicy(subpolicy)"
                    >
                      <div 
                        class="node-content"
                        @mouseenter="handleNodeHover('subpolicy', subpolicy.id, subpolicy, $event)"
                        @mouseleave="handleNodeLeave"
                      >
                        <span class="node-label">{{ subpolicy.SubPolicyName }}</span>
                        <i class="fas fa-chevron-right expand-icon" :class="{ 'rotated': expandedSubPolicies[subpolicy.id] }"></i>
                        <div class="node-tooltip">{{ subpolicy.SubPolicyName }}</div>
                        <Teleport to="body">
                          <div 
                            v-if="hoveredNode === `subpolicy-${subpolicy.id}`"
                            class="metadata-tooltip"
                            :ref="`tooltip-subpolicy-${subpolicy.id}`"
                            @mouseenter.stop
                            @mouseleave.stop="handleNodeLeave"
                          >
                            <div class="metadata-header">
                              <h3>{{ hoveredNodeMetadata?.SubPolicyName || subpolicy.SubPolicyName }}</h3>
                              <span class="metadata-type-badge">subpolicy</span>
                            </div>
                            <div class="metadata-content">
                              <div v-if="metadataLoading" class="metadata-loading">Loading metadata...</div>
                              <template v-else>
                                <div v-if="Object.keys(getFilteredMetadata(hoveredNodeMetadata || subpolicy, 'subpolicy')).length === 0" class="metadata-empty">
                                  No additional metadata available
                                </div>
                                <div v-for="(value, key) in getFilteredMetadata(hoveredNodeMetadata || subpolicy, 'subpolicy')" :key="key" class="metadata-item">
                                  <span class="metadata-label">{{ formatLabel(key) }}:</span>
                                  <span class="metadata-value">{{ formatValue(value) }}</span>
                                </div>
                              </template>
                            </div>
                          </div>
                        </Teleport>
                      </div>
                    </div>
                  </template>
                </template>
              </div>
            </div>
            <div class="tree-cell compliances-cell">
              <div class="vertical-nodes">
                <template v-for="policy in treeData" :key="`comp-${policy.id}`">
                  <template v-if="subPoliciesData[policy.id]">
                    <template v-for="subpolicy in subPoliciesData[policy.id]" :key="`comp-sub-${subpolicy.id}`">
                      <template v-if="expandedSubPolicies[subpolicy.id] && compliancesData[subpolicy.id]">
                        <div 
                          v-for="(compliance, compIndex) in compliancesData[subpolicy.id]" 
                          :key="compliance.id"
                          :data-node-id="`compliance-${compliance.id}`"
                          :data-parent-id="`subpolicy-${subpolicy.id}`"
                          class="tree-node compliance-node"
                          :class="getComplianceClasses(compliance)"
                          :style="{ '--node-index': compIndex }"
                          @click="toggleCompliance(compliance)"
                        >
                          <div 
                            class="node-content"
                            @mouseenter="handleNodeHover('compliance', compliance.id, compliance, $event)"
                            @mouseleave="handleNodeLeave"
                          >
                            <span class="node-label">{{ compliance.ComplianceTitle || 'Compliance' }}</span>
                            <i class="fas fa-chevron-right expand-icon" :class="{ 'rotated': expandedCompliances[compliance.id] }"></i>
                            <div class="node-tooltip">{{ compliance.ComplianceTitle || 'Compliance' }}</div>
                            <Teleport to="body">
                              <div 
                                v-if="hoveredNode === `compliance-${compliance.id}`"
                                class="metadata-tooltip"
                                :ref="`tooltip-compliance-${compliance.id}`"
                                @mouseenter.stop
                                @mouseleave.stop="handleNodeLeave"
                              >
                                <div class="metadata-header">
                                  <h3>{{ hoveredNodeMetadata?.ComplianceTitle || compliance.ComplianceTitle || 'Compliance' }}</h3>
                                  <span class="metadata-type-badge">compliance</span>
                                </div>
                                <div class="metadata-content">
                                  <div v-if="metadataLoading" class="metadata-loading">Loading metadata...</div>
                                  <template v-else>
                                    <div v-if="Object.keys(getFilteredMetadata(hoveredNodeMetadata || compliance, 'compliance')).length === 0" class="metadata-empty">
                                      No additional metadata available
                                    </div>
                                    <div v-for="(value, key) in getFilteredMetadata(hoveredNodeMetadata || compliance, 'compliance')" :key="key" class="metadata-item">
                                      <span class="metadata-label">{{ formatLabel(key) }}:</span>
                                      <span class="metadata-value">{{ formatValue(value) }}</span>
                                    </div>
                                  </template>
                                </div>
                              </div>
                            </Teleport>
                          </div>
                        </div>
                      </template>
                    </template>
                  </template>
                </template>
              </div>
            </div>
            <div class="tree-cell risks-cell">
              <div class="vertical-nodes">
                <template v-for="policy in treeData" :key="`risk-${policy.id}`">
                  <template v-if="subPoliciesData[policy.id]">
                    <template v-for="subpolicy in subPoliciesData[policy.id]" :key="`risk-sub-${subpolicy.id}`">
                      <template v-if="compliancesData[subpolicy.id]">
                        <template v-for="compliance in compliancesData[subpolicy.id]" :key="`risk-comp-${compliance.id}`">
                          <template v-if="expandedCompliances[compliance.id] && risksData[compliance.id]">
                            <div 
                              v-for="(risk, riskIndex) in risksData[compliance.id]" 
                              :key="risk.id"
                              :data-node-id="`risk-${risk.id}`"
                              :data-parent-id="`compliance-${compliance.id}`"
                              class="tree-node risk-node"
                              :style="{ '--node-index': riskIndex }"
                            >
                              <div 
                                class="node-content"
                                @mouseenter="handleNodeHover('risk', risk.id, risk, $event)"
                                @mouseleave="handleNodeLeave"
                              >
                                <span class="node-label">{{ risk.RiskTitle || 'Risk' }}</span>
                                <div class="node-tooltip">{{ risk.RiskTitle || 'Risk' }}</div>
                                <Teleport to="body">
                                  <div 
                                    v-if="hoveredNode === `risk-${risk.id}`"
                                    class="metadata-tooltip"
                                    :ref="`tooltip-risk-${risk.id}`"
                                    @mouseenter.stop
                                    @mouseleave.stop="handleNodeLeave"
                                  >
                                    <div class="metadata-header">
                                      <h3>{{ hoveredNodeMetadata?.RiskTitle || risk.RiskTitle || 'Risk' }}</h3>
                                      <span class="metadata-type-badge">risk</span>
                                    </div>
                                    <div class="metadata-content">
                                      <div v-if="metadataLoading" class="metadata-loading">Loading metadata...</div>
                                      <template v-else>
                                        <div v-if="Object.keys(getFilteredMetadata(hoveredNodeMetadata || risk, 'risk')).length === 0" class="metadata-empty">
                                          No additional metadata available
                                        </div>
                                        <div v-for="(value, key) in getFilteredMetadata(hoveredNodeMetadata || risk, 'risk')" :key="key" class="metadata-item">
                                          <span class="metadata-label">{{ formatLabel(key) }}:</span>
                                          <span class="metadata-value">{{ formatValue(value) }}</span>
                                        </div>
                                      </template>
                                    </div>
                                  </div>
                                </Teleport>
                              </div>
                            </div>
                          </template>
                        </template>
                      </template>
                    </template>
                  </template>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Initial State -->
    <div v-if="!loading && !error && !selectedFramework" class="initial-state">
      <i class="fas fa-sitemap"></i>
      <p>Please select a framework from the dropdown above to view the hierarchical structure</p>
    </div>
  </div>
</template>

<script>
import { API_ENDPOINTS } from '../../config/api.js'
import axios from 'axios'

export default {
  name: 'TreeView',
  data() {
    return {
      loading: false,
      error: null,
      frameworks: [],
      selectedFramework: '',
      selectedFrameworkName: '',
      treeData: [],
      frameworkExpanded: false,
      expandedPolicies: {},
      expandedSubPolicies: {},
      expandedCompliances: {},
      subPoliciesData: {},
      compliancesData: {},
      risksData: {},
      connectionPaths: [],
      hoveredNode: null,
      hoveredNodeMetadata: null,
      metadataLoading: false,
      metadataCache: {}
    }
  },
  computed: {
    allSubPolicies() {
      const subPolicies = []
      Object.values(this.subPoliciesData).forEach(policySubPolicies => {
        if (policySubPolicies && Array.isArray(policySubPolicies)) {
          subPolicies.push(...policySubPolicies)
        }
      })
      return subPolicies
    },
    allCompliances() {
      const compliances = []
      Object.values(this.compliancesData).forEach(subPolicyCompliances => {
        if (subPolicyCompliances && Array.isArray(subPolicyCompliances)) {
          compliances.push(...subPolicyCompliances)
        }
      })
      return compliances
    },
    allRisks() {
      const risks = []
      Object.values(this.risksData).forEach(complianceRisks => {
        if (complianceRisks && Array.isArray(complianceRisks)) {
          risks.push(...complianceRisks)
        }
      })
      return risks
    },
    hasExpandedPolicies() {
      return Object.values(this.expandedPolicies).some(expanded => expanded)
    },
    hasExpandedSubPolicies() {
      return Object.values(this.expandedSubPolicies).some(expanded => expanded)
    },
    hasExpandedCompliances() {
      return Object.values(this.expandedCompliances).some(expanded => expanded)
    }
  },
  mounted() {
    console.log('🚀 Tree component mounted')
    this.loadFrameworks()
    // Attempt to apply selected framework from session/localStorage
    this.applySelectedFrameworkFromSession()
    
    // Add window resize listener to redraw connections
    window.addEventListener('resize', this.drawConnections)
    
    // Update tooltip positions on scroll and resize
    this.updateTooltipPositions = () => {
      this.$nextTick(() => {
        const tooltips = document.querySelectorAll('.metadata-tooltip')
        tooltips.forEach(tooltip => {
          const nodeContent = tooltip.parentElement?.closest('.node-content') || 
                             tooltip.parentElement?.closest('.framework-icon-container')
          if (nodeContent) {
            const rect = nodeContent.getBoundingClientRect()
            const tooltipRect = tooltip.getBoundingClientRect()
            
            let top = rect.top - tooltipRect.height - 15
            let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2)
            
            if (left < 10) left = 10
            if (left + tooltipRect.width > window.innerWidth - 10) {
              left = window.innerWidth - tooltipRect.width - 10
            }
            if (top < 10) {
              top = rect.bottom + 15
            }
            
            tooltip.style.top = `${top}px`
            tooltip.style.left = `${left}px`
          }
        })
      })
    }
    
    window.addEventListener('scroll', this.updateTooltipPositions, true)
    window.addEventListener('resize', this.updateTooltipPositions)
  },
  beforeUnmount() {
    // Clean up resize listener
    window.removeEventListener('resize', this.drawConnections)
    if (this.updateTooltipPositions) {
      window.removeEventListener('scroll', this.updateTooltipPositions, true)
      window.removeEventListener('resize', this.updateTooltipPositions)
    }
  },
  methods: {
    async applySelectedFrameworkFromSession() {
      try {
        // 1) Ask backend which framework is currently selected in session
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
        const frameworkIdFromSession = response?.data?.frameworkId
        if (frameworkIdFromSession) {
          this.selectedFramework = parseInt(frameworkIdFromSession)
          const fw = this.frameworks.find(f => f.FrameworkId === this.selectedFramework)
          this.selectedFrameworkName = fw ? fw.FrameworkName : ''
          await this.onFrameworkChange()
          return
        }
      } catch (e) {
        console.warn('⚠️ Could not get selected framework from session for Tree:', e?.response?.data || e.message)
      }

      // 2) Fallback to localStorage (set by Home selection)
      try {
        const stored = localStorage.getItem('selectedFrameworkId') || localStorage.getItem('frameworkId')
        if (stored && stored !== '' && stored !== 'null') {
          this.selectedFramework = parseInt(stored)
          const fw = this.frameworks.find(f => f.FrameworkId === this.selectedFramework)
          this.selectedFrameworkName = fw ? fw.FrameworkName : (localStorage.getItem('framework_name') || '')
          await this.onFrameworkChange()
        }
      } catch (e) {
        console.warn('⚠️ Could not read framework selection from localStorage for Tree:', e)
      }
    },
    async loadFrameworks() {
      console.log('🟢 Loading frameworks...')
      this.loading = true
      this.error = null
      try {
        const endpoint = API_ENDPOINTS.TREE_GET_FRAMEWORKS
        console.log('📡 Frameworks endpoint:', endpoint)
        
        const response = await axios.get(endpoint)
        console.log('✅ Frameworks API Response:', response.data)
        
        if (response.data.status === 'success') {
          this.frameworks = response.data.data
          console.log('✅ Frameworks loaded:', this.frameworks.length, 'items')
        } else {
          this.error = 'Failed to load frameworks'
          console.log('⚠️ API returned non-success status')
        }
      } catch (err) {
        this.error = err.response?.data?.message || 'Failed to load frameworks'
        console.error('❌ Error loading frameworks:', err)
      } finally {
        this.loading = false
      }
    },

    async onFrameworkChange() {
      console.log('🟢 Framework changed:', this.selectedFramework)
      
      if (!this.selectedFramework) {
        this.resetAllData()
        this.selectedFrameworkName = '' // Clear the name when no framework selected
        return
      }

      // Clear data first, BEFORE setting the framework name
      this.resetAllData()
      
      // Now set the framework name so it doesn't get cleared
      const framework = this.frameworks.find(f => f.FrameworkId === this.selectedFramework)
      this.selectedFrameworkName = framework ? framework.FrameworkName : ''
      console.log('✅ Framework name set to:', this.selectedFrameworkName)

      this.loading = true
      this.error = null
      try {
        const endpoint = API_ENDPOINTS.TREE_GET_POLICIES(this.selectedFramework)
        console.log('📡 Loading policies from:', endpoint)
        
        const response = await axios.get(endpoint)
        console.log('✅ Policies API Response:', response.data)
        
        if (response.data.status === 'success') {
          this.treeData = response.data.data.map(item => ({
            ...item,
            type: 'policy',
            id: item.PolicyId
          }))
          console.log('✅ Policies loaded:', this.treeData.length, 'items')
          
          // Draw connections after policies are loaded
          setTimeout(() => {
            this.drawConnections()
          }, 100)
        } else {
          this.error = 'Failed to load policies'
          this.treeData = []
        }
      } catch (err) {
        this.error = err.response?.data?.message || 'Failed to load policies'
        console.error('❌ Error loading policies:', err)
        this.treeData = []
      } finally {
        this.loading = false
      }
    },

    resetAllData() {
      this.treeData = []
      // Don't clear selectedFrameworkName here - it should persist when framework is selected
      // this.selectedFrameworkName = ''
      this.frameworkExpanded = false
      this.clearAllExpandedStates()
    },

    toggleFrameworkExpansion() {
      console.log('🟣 Framework node clicked!')
      
      if (this.treeData.length === 0) {
        console.log('⚠️ No policies loaded yet')
        return
      }
      
      const wasExpanded = this.frameworkExpanded
      this.frameworkExpanded = !wasExpanded
      console.log('🟣 Framework expanded:', this.frameworkExpanded)
      
      // If framework is being collapsed, clear all expanded states and data
      if (wasExpanded) {
        this.clearAllExpandedStates()
      }
      
      // Force reactivity update
      this.$forceUpdate()
    },

    async togglePolicy(policy) {
      console.log('🔵 Policy clicked:', policy)
      const wasExpanded = this.expandedPolicies[policy.id]
      this.expandedPolicies[policy.id] = !wasExpanded
      
      if (!wasExpanded && !this.subPoliciesData[policy.id]) {
        await this.loadSubPolicies(policy)
      } else if (wasExpanded) {
        // Clear sub-policies and their children when collapsing
        this.clearPolicyChildren(policy.id)
      }
      
      console.log('🔵 Policy expansion state:', this.expandedPolicies[policy.id])
      console.log('🔵 Has expanded policies:', this.hasExpandedPolicies)
      
      // Force reactivity update
      this.$forceUpdate()
      
      // Draw connections after DOM update
      setTimeout(() => {
        this.drawConnections()
      }, 100)
    },

    async loadSubPolicies(policy) {
      console.log('📡 Loading sub-policies for policy:', policy.PolicyId)
      try {
        const endpoint = API_ENDPOINTS.TREE_GET_SUBPOLICIES(policy.PolicyId)
        const response = await axios.get(endpoint)
        
        if (response.data.status === 'success') {
          const subPolicies = response.data.data.map(item => ({
            ...item,
            type: 'subpolicy',
            id: item.SubPolicyId,
            parentPolicyId: policy.id,
            PolicyId: policy.id // Ensure parent policy ID is stored
          }))
          this.subPoliciesData[policy.id] = subPolicies
          console.log(`✅ Sub-policies loaded for policy ${policy.PolicyName}:`, subPolicies.map(sp => sp.SubPolicyName))
        }
      } catch (err) {
        console.error('❌ Error loading sub-policies:', err)
      }
    },

    async toggleSubPolicy(subpolicy) {
      console.log('🔵 Sub-policy clicked:', subpolicy)
      const wasExpanded = this.expandedSubPolicies[subpolicy.id]
      this.expandedSubPolicies[subpolicy.id] = !wasExpanded
      
      if (!wasExpanded && !this.compliancesData[subpolicy.id]) {
        await this.loadCompliances(subpolicy)
      } else if (wasExpanded) {
        // Clear compliances and their children when collapsing
        this.clearSubPolicyChildren(subpolicy.id)
      }
      
      console.log('🔵 Sub-policy expansion state:', this.expandedSubPolicies[subpolicy.id])
      console.log('🔵 Has expanded sub-policies:', this.hasExpandedSubPolicies)
      
      // Force reactivity update
      this.$forceUpdate()
      
      // Draw connections after DOM update
      setTimeout(() => {
        this.drawConnections()
      }, 100)
    },

    async loadCompliances(subpolicy) {
      console.log('📡 Loading compliances for sub-policy:', subpolicy.SubPolicyId)
      try {
        const endpoint = API_ENDPOINTS.TREE_GET_COMPLIANCES(subpolicy.SubPolicyId)
        const response = await axios.get(endpoint)
        
        if (response.data.status === 'success') {
          const compliances = response.data.data.map(item => ({
            ...item,
            type: 'compliance',
            id: item.ComplianceId,
            parentSubPolicyId: subpolicy.id,
            SubPolicyId: subpolicy.id // Ensure parent sub-policy ID is stored
          }))
          this.compliancesData[subpolicy.id] = compliances
          console.log(`✅ Compliances loaded for sub-policy ${subpolicy.SubPolicyName}:`, compliances.map(c => c.ComplianceTitle || 'Compliance'))
        }
      } catch (err) {
        console.error('❌ Error loading compliances:', err)
      }
    },

    async toggleCompliance(compliance) {
      console.log('🔵 Compliance clicked:', compliance)
      const wasExpanded = this.expandedCompliances[compliance.id]
      this.expandedCompliances[compliance.id] = !wasExpanded
      
      if (!wasExpanded && !this.risksData[compliance.id]) {
        await this.loadRisks(compliance)
      } else if (wasExpanded) {
        // Clear risks when collapsing
        this.clearComplianceChildren(compliance.id)
      }
      
      console.log('🔵 Compliance expansion state:', this.expandedCompliances[compliance.id])
      console.log('🔵 Has expanded compliances:', this.hasExpandedCompliances)
      
      // Force reactivity update
      this.$forceUpdate()
      
      // Draw connections after DOM update
      setTimeout(() => {
        this.drawConnections()
      }, 100)
    },

    async loadRisks(compliance) {
      console.log('📡 Loading risks for compliance:', compliance.ComplianceId)
      try {
        const endpoint = API_ENDPOINTS.TREE_GET_RISKS(compliance.ComplianceId)
        const response = await axios.get(endpoint)
        
        if (response.data.status === 'success') {
          const risks = response.data.data.map(item => ({
            ...item,
            type: 'risk',
            id: item.RiskId,
            parentComplianceId: compliance.id,
            ComplianceId: compliance.id // Ensure parent compliance ID is stored
          }))
          this.risksData[compliance.id] = risks
          console.log(`✅ Risks loaded for compliance ${compliance.ComplianceTitle || 'Compliance'}:`, risks.map(r => r.RiskTitle || 'Risk'))
        }
      } catch (err) {
        console.error('❌ Error loading risks:', err)
      }
    },

    clearPolicyChildren(policyId) {
      // Clear sub-policies for this policy
      if (this.subPoliciesData[policyId] && Array.isArray(this.subPoliciesData[policyId])) {
        const subPolicies = this.subPoliciesData[policyId]
        // Clear compliances for each sub-policy
        subPolicies.forEach(subPolicy => {
          this.clearSubPolicyChildren(subPolicy.id)
        })
        // Clear the sub-policies themselves
        this.subPoliciesData[policyId] = null
      }
      // Redraw connections to remove any orphaned lines
      this.drawConnections()
    },

    clearSubPolicyChildren(subPolicyId) {
      // Clear compliances for this sub-policy
      if (this.compliancesData[subPolicyId] && Array.isArray(this.compliancesData[subPolicyId])) {
        const compliances = this.compliancesData[subPolicyId]
        // Clear risks for each compliance
        compliances.forEach(compliance => {
          this.clearComplianceChildren(compliance.id)
        })
        // Clear the compliances themselves
        this.compliancesData[subPolicyId] = null
      }
      // Redraw connections to remove any orphaned lines
      this.drawConnections()
    },

    clearComplianceChildren(complianceId) {
      // Clear risks for this compliance
      if (this.risksData[complianceId] && Array.isArray(this.risksData[complianceId])) {
        this.risksData[complianceId] = null
      }
      // Redraw connections to remove any orphaned lines
      this.drawConnections()
    },

    clearAllExpandedStates() {
      console.log('🧹 Clearing all expanded states and data')
      
      // Clear all expanded states
      this.expandedPolicies = {}
      this.expandedSubPolicies = {}
      this.expandedCompliances = {}
      
      // Clear all data
      this.subPoliciesData = {}
      this.compliancesData = {}
      this.risksData = {}
      
      // Clear all connections
      this.connectionPaths = []
      
      console.log('✅ All expanded states and data cleared')
    },

    async expandAll() {
      console.log('🟢 Expanding all nodes')
      
      // Expand framework if not already expanded
      if (!this.frameworkExpanded && this.treeData.length > 0) {
        this.frameworkExpanded = true
      }
      
      // Expand all policies
      for (const policy of this.treeData) {
        if (!this.expandedPolicies[policy.id]) {
          await this.togglePolicy(policy)
        }
        
        // Expand all sub-policies
        if (this.subPoliciesData[policy.id]) {
          for (const subpolicy of this.subPoliciesData[policy.id]) {
            if (!this.expandedSubPolicies[subpolicy.id]) {
              await this.toggleSubPolicy(subpolicy)
            }
            
            // Expand all compliances
            if (this.compliancesData[subpolicy.id]) {
              for (const compliance of this.compliancesData[subpolicy.id]) {
                if (!this.expandedCompliances[compliance.id]) {
                  await this.toggleCompliance(compliance)
                }
              }
            }
          }
        }
      }
      
      // Draw all connections after expansion
      setTimeout(() => {
        this.drawConnections()
      }, 200)
    },

    getSubPolicyClasses(subpolicy) {
      // Find which policy this sub-policy belongs to
      for (const policy of this.treeData) {
        if (this.subPoliciesData[policy.id] && 
            this.subPoliciesData[policy.id].some(sp => sp.id === subpolicy.id)) {
          return {
            'expanded': this.expandedSubPolicies[subpolicy.id],
            [`child-of-policy-${policy.id}`]: this.expandedPolicies[policy.id]
          }
        }
      }
      return { 'expanded': this.expandedSubPolicies[subpolicy.id] }
    },

    getComplianceClasses(compliance) {
      // Find which sub-policy this compliance belongs to
      for (const policy of this.treeData) {
        if (this.subPoliciesData[policy.id]) {
          for (const subpolicy of this.subPoliciesData[policy.id]) {
            if (this.compliancesData[subpolicy.id] && 
                this.compliancesData[subpolicy.id].some(c => c.id === compliance.id)) {
              return {
                'expanded': this.expandedCompliances[compliance.id],
                [`child-of-subpolicy-${subpolicy.id}`]: this.expandedSubPolicies[subpolicy.id]
              }
            }
          }
        }
      }
      return { 'expanded': this.expandedCompliances[compliance.id] }
    },

    drawConnections() {
      this.$nextTick(() => {
        this.connectionPaths = []
        
        if (!this.$refs.treeVisualization) return
        
        // Clear all existing connections first
        console.log('🎯 Drawing connections...')
        
        // Draw connections from framework icon to all policies
        const frameworkElement = document.querySelector('.framework-icon-container')
        
        if (frameworkElement && this.treeData.length > 0) {
          console.log('🔗 Connecting framework icon to all policies')
          
          this.treeData.forEach((policy) => {
            const policyElement = document.querySelector(`[data-node-id="policy-${policy.id}"]`)
            
            if (policyElement) {
              console.log(`✅ Connecting Framework → ${policy.PolicyName}`)
              
              const path = this.createCurvedPath(frameworkElement, policyElement)
              if (path) {
                this.connectionPaths.push({
                  path,
                  color: '#f59e0b',
                  dashed: false
                })
              }
            }
          })
        }
        
        // Draw connections for expanded policies
        this.treeData.forEach((policy) => {
          if (this.expandedPolicies[policy.id] && this.subPoliciesData[policy.id]) {
            console.log(`📋 Policy ${policy.PolicyName} is expanded, connecting to its children`)
            
            const policyElement = document.querySelector(`[data-node-id="policy-${policy.id}"]`)
            
            if (policyElement) {
              // Only connect to children of this specific policy
              this.subPoliciesData[policy.id].forEach((subpolicy) => {
                console.log(`🔗 Looking for subpolicy ${subpolicy.SubPolicyName} with parent ${policy.id}`)
                
                // Find the specific sub-policy element that belongs to this policy
                const subPolicyElement = document.querySelector(`[data-node-id="subpolicy-${subpolicy.id}"]`)
                
                if (subPolicyElement) {
                  // Verify this is actually a child of the current policy
                  const parentId = subPolicyElement.getAttribute('data-parent-id')
                  if (parentId === `policy-${policy.id}`) {
                    console.log(`✅ Connecting ${policy.PolicyName} → ${subpolicy.SubPolicyName}`)
                    
                    const path = this.createCurvedPath(policyElement, subPolicyElement)
                    if (path) {
                      this.connectionPaths.push({
                        path,
                        color: '#10b981',
                        dashed: false
                      })
                    }
                    
                    // Draw connections for expanded sub-policies
                    if (this.expandedSubPolicies[subpolicy.id] && this.compliancesData[subpolicy.id]) {
                      this.compliancesData[subpolicy.id].forEach((compliance) => {
                        const complianceElement = document.querySelector(`[data-node-id="compliance-${compliance.id}"]`)
                        
                        if (complianceElement) {
                          const parentId = complianceElement.getAttribute('data-parent-id')
                          if (parentId === `subpolicy-${subpolicy.id}`) {
                            const path = this.createCurvedPath(subPolicyElement, complianceElement)
                            if (path) {
                              this.connectionPaths.push({
                                path,
                                color: '#f59e0b',
                                dashed: false
                              })
                            }
                            
                            // Draw connections for expanded compliances
                            if (this.expandedCompliances[compliance.id] && this.risksData[compliance.id]) {
                              this.risksData[compliance.id].forEach((risk) => {
                                const riskElement = document.querySelector(`[data-node-id="risk-${risk.id}"]`)
                                
                                if (riskElement) {
                                  const parentId = riskElement.getAttribute('data-parent-id')
                                  if (parentId === `compliance-${compliance.id}`) {
                                    const path = this.createCurvedPath(complianceElement, riskElement)
                                    if (path) {
                                      this.connectionPaths.push({
                                        path,
                                        color: '#ef4444',
                                        dashed: false
                                      })
                                    }
                                  }
                                }
                              })
                            }
                          }
                        }
                      })
                    }
                  } else {
                    console.log(`❌ Skipping ${subpolicy.SubPolicyName} - belongs to different parent (${parentId})`)
                  }
                } else {
                  console.log(`❌ Sub-policy element not found: ${subpolicy.SubPolicyName}`)
                }
              })
            } else {
              console.log(`❌ Policy element not found: ${policy.PolicyName}`)
            }
          }
        })
        
        console.log(`🎯 Total connections drawn: ${this.connectionPaths.length}`)
      })
    },

    createCurvedPath(startElement, endElement) {
      if (!startElement || !endElement || !this.$refs.treeVisualization) return null
      
      const containerRect = this.$refs.treeVisualization.getBoundingClientRect()
      const startRect = startElement.getBoundingClientRect()
      const endRect = endElement.getBoundingClientRect()
      
      // Calculate relative positions with proper offset for padding
      let startX, startY
      
      // Check if start element is framework icon
      if (startElement.querySelector('.framework-icon-container')) {
        const iconContainer = startElement.querySelector('.framework-icon-container')
        const iconRect = iconContainer.getBoundingClientRect()
        startX = iconRect.right - containerRect.left - 10
        startY = iconRect.top + iconRect.height / 2 - containerRect.top
      } else {
        startX = startRect.right - containerRect.left - 10
        startY = startRect.top + startRect.height / 2 - containerRect.top
      }
      
      const endX = endRect.left - containerRect.left + 10 // Offset from edge
      const endY = endRect.top + endRect.height / 2 - containerRect.top
      
      // Calculate control points for smooth curve
      const distance = endX - startX
      const controlPointOffset = Math.max(distance * 0.3, 20) // Minimum curve distance
      
      const controlPoint1X = startX + controlPointOffset
      const controlPoint1Y = startY
      const controlPoint2X = endX - controlPointOffset
      const controlPoint2Y = endY
      
      // Create cubic Bezier curve path
      return `M ${startX} ${startY} C ${controlPoint1X} ${controlPoint1Y}, ${controlPoint2X} ${controlPoint2Y}, ${endX} ${endY}`
    },

    collapseAll() {
      console.log('🔴 Collapsing all nodes')
      this.frameworkExpanded = false
      this.clearAllExpandedStates()
      this.connectionPaths = [] // Clear all connections immediately
      this.$forceUpdate()
    },

    async handleNodeHover(nodeType, nodeId, nodeData, event) {
      console.log('🖱️ Hover detected:', nodeType, nodeId)
      const nodeKey = `${nodeType}-${nodeId}`
      this.hoveredNode = nodeKey
      
      // Set basic metadata immediately so tooltip shows right away
      this.hoveredNodeMetadata = nodeData
      this.metadataLoading = false
      
      // Position tooltip immediately after DOM update
      this.$nextTick(() => {
        setTimeout(() => {
          this.positionTooltip(event)
        }, 50) // Small delay to ensure DOM is ready
      })
      
      // Check cache first
      if (this.metadataCache[nodeKey]) {
        console.log('✅ Using cached metadata')
        this.hoveredNodeMetadata = this.metadataCache[nodeKey]
        this.$nextTick(() => {
          setTimeout(() => {
            this.positionTooltip(event)
          }, 50)
        })
        return
      }
      
      // Fetch metadata in background
      this.metadataLoading = true
      try {
        let endpoint
        switch (nodeType) {
          case 'framework':
            endpoint = API_ENDPOINTS.TREE_GET_FRAMEWORK_METADATA(nodeId)
            break
          case 'policy':
            endpoint = API_ENDPOINTS.TREE_GET_POLICY_METADATA(nodeId)
            break
          case 'subpolicy':
            endpoint = API_ENDPOINTS.TREE_GET_SUBPOLICY_METADATA(nodeId)
            break
          case 'compliance':
            endpoint = API_ENDPOINTS.TREE_GET_COMPLIANCE_METADATA(nodeId)
            break
          case 'risk':
            endpoint = API_ENDPOINTS.TREE_GET_RISK_METADATA(nodeId)
            break
          default:
            console.warn('⚠️ Unknown node type:', nodeType)
            this.metadataLoading = false
            return
        }
        
        console.log('📡 Fetching metadata from:', endpoint)
        const response = await axios.get(endpoint)
        console.log('📥 Metadata response:', response.data)
        
        if (response.data.status === 'success') {
          this.hoveredNodeMetadata = response.data.data
          // Cache the metadata
          this.metadataCache[nodeKey] = response.data.data
          console.log('✅ Metadata loaded and cached')
          this.$nextTick(() => {
            setTimeout(() => {
              this.positionTooltip(event)
            }, 50)
          })
        } else {
          console.warn('⚠️ API returned non-success status')
          // Keep basic data as fallback
        }
      } catch (err) {
        console.error('❌ Error fetching metadata:', err)
        console.error('Error details:', err.response?.data || err.message)
        // Keep basic data as fallback
      } finally {
        this.metadataLoading = false
      }
    },
    
    positionTooltip(event) {
      this.$nextTick(() => {
        // Wait a bit more for Teleport to render
        setTimeout(() => {
          // Find the currently visible tooltip
          const tooltip = document.querySelector('.metadata-tooltip')
          if (!tooltip) {
            console.warn('⚠️ Tooltip element not found in DOM')
            console.log('🔍 Searching for tooltip... hoveredNode:', this.hoveredNode)
            // Try again after a short delay
            setTimeout(() => {
              const retryTooltip = document.querySelector('.metadata-tooltip')
              if (retryTooltip) {
                console.log('✅ Tooltip found on retry')
                this.positionTooltip(event)
              } else {
                console.error('❌ Tooltip still not found after retry')
              }
            }, 100)
            return
          }
          
          console.log('✅ Tooltip found in DOM:', tooltip)
          console.log('📍 Tooltip parent:', tooltip.parentElement)
          
          // Ensure tooltip is visible with all necessary styles
          tooltip.style.display = 'block'
          tooltip.style.visibility = 'visible'
          tooltip.style.opacity = '1'
          tooltip.style.pointerEvents = 'auto'
          tooltip.style.position = 'fixed'
          tooltip.style.zIndex = '99999'
          
          let targetElement = event?.currentTarget || event?.target
          
          // If event doesn't have target, find it from hoveredNode
          if (!targetElement || !targetElement.classList) {
            if (this.hoveredNode) {
              const [nodeType] = this.hoveredNode.split('-')
              if (nodeType === 'framework') {
                targetElement = document.querySelector('.framework-icon-container')
              } else {
                const nodeElement = document.querySelector(`[data-node-id="${this.hoveredNode}"]`)
                if (nodeElement) {
                  targetElement = nodeElement.querySelector('.node-content') || nodeElement
                }
              }
            }
          }
          
          if (!targetElement) {
            console.warn('⚠️ Could not find target element for tooltip positioning')
            return
          }
          
          try {
            const rect = targetElement.getBoundingClientRect()
            console.log('📍 Target element rect:', rect)
            
            // Get tooltip dimensions (force reflow by temporarily positioning)
            tooltip.style.top = '-9999px'
            tooltip.style.left = '-9999px'
            const tooltipRect = tooltip.getBoundingClientRect()
            console.log('📏 Tooltip dimensions:', tooltipRect.width, 'x', tooltipRect.height)
            
            // Position above the node by default
            let top = rect.top - tooltipRect.height - 15
            let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2)
            
            // Adjust if tooltip goes off screen horizontally
            if (left < 10) left = 10
            if (left + tooltipRect.width > window.innerWidth - 10) {
              left = window.innerWidth - tooltipRect.width - 10
            }
            
            // Adjust if tooltip goes off screen vertically
            if (top < 10) {
              // Position below if not enough space above
              top = rect.bottom + 15
            }
            
            // Ensure tooltip doesn't go below viewport
            if (top + tooltipRect.height > window.innerHeight - 10) {
              top = window.innerHeight - tooltipRect.height - 10
            }
            
            tooltip.style.top = `${top}px`
            tooltip.style.left = `${left}px`
            
            // Verify final position
            const finalRect = tooltip.getBoundingClientRect()
            console.log('✅ Tooltip positioned at:', top, left)
            console.log('✅ Final tooltip rect:', finalRect)
            console.log('✅ Tooltip computed styles:', {
              display: window.getComputedStyle(tooltip).display,
              visibility: window.getComputedStyle(tooltip).visibility,
              opacity: window.getComputedStyle(tooltip).opacity,
              zIndex: window.getComputedStyle(tooltip).zIndex,
              position: window.getComputedStyle(tooltip).position
            })
          } catch (err) {
            console.error('❌ Error positioning tooltip:', err)
          }
        }, 100) // Delay to ensure Teleport has rendered
      })
    },

    handleNodeLeave(event) {
      // Check if mouse is moving to tooltip
      const relatedTarget = event.relatedTarget
      if (relatedTarget && relatedTarget.closest('.metadata-tooltip')) {
        return // Don't hide if moving to tooltip
      }
      
      // Small delay to allow moving to tooltip
      const timeoutId = setTimeout(() => {
        // Double check that we're not hovering over tooltip
        const tooltip = document.querySelector('.metadata-tooltip:hover')
        if (!tooltip) {
          this.hoveredNode = null
          this.hoveredNodeMetadata = null
        }
      }, 200)
      
      // Store timeout ID for potential cleanup
      this._tooltipTimeout = timeoutId
    },
    
    hideTooltip() {
      if (this._tooltipTimeout) {
        clearTimeout(this._tooltipTimeout)
        this._tooltipTimeout = null
      }
      this.hoveredNode = null
      this.hoveredNodeMetadata = null
    },
    
    getFilteredMetadata(metadata, nodeType) {
      if (!metadata) return {}
      
      const excludeFields = {
        framework: ['FrameworkId', 'FrameworkName'],
        policy: ['PolicyId', 'PolicyName'],
        subpolicy: ['SubPolicyId', 'SubPolicyName'],
        compliance: ['ComplianceId', 'ComplianceTitle'],
        risk: ['RiskId', 'RiskTitle']
      }
      
      const excluded = excludeFields[nodeType] || []
      const filtered = {}
      
      for (const [key, value] of Object.entries(metadata)) {
        if (!excluded.includes(key) && value && value !== 'N/A' && value !== '' && value !== null && value !== undefined) {
          filtered[key] = value
        }
      }
      
      return filtered
    },
    
    formatLabel(key) {
      // Convert camelCase/PascalCase to readable format
      return key
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, str => str.toUpperCase())
        .trim()
    },
    
    formatValue(value) {
      if (typeof value === 'string' && value.length > 100) {
        return value.substring(0, 100) + '...'
      }
      return value
    }
  },
  watch: {
    hoveredNode(newVal, oldVal) {
      if (newVal) {
        // Update tooltip position when hovered node changes
        this.$nextTick(() => {
          setTimeout(() => {
            const tooltip = document.querySelector('.metadata-tooltip')
            if (tooltip) {
              // Find the node that triggered this hover
              const nodeType = newVal.split('-')[0]
              
              // Find the actual node element
              let nodeElement = null
              if (nodeType === 'framework') {
                nodeElement = document.querySelector('.framework-icon-container')
              } else {
                const nodeContainer = document.querySelector(`[data-node-id="${newVal}"]`)
                if (nodeContainer) {
                  nodeElement = nodeContainer.querySelector('.node-content') || nodeContainer
                }
              }
              
              if (nodeElement) {
                this.positionTooltip({ currentTarget: nodeElement })
              } else {
                console.warn('⚠️ Could not find node element for positioning')
              }
            }
          }, 100) // Delay to ensure teleport has rendered
        })
      } else if (oldVal) {
        // Clean up tooltip when hover ends
        this.$nextTick(() => {
          const tooltips = document.querySelectorAll('.metadata-tooltip')
          tooltips.forEach(tooltip => {
            if (tooltip.parentNode) {
              tooltip.style.display = 'none'
            }
          })
        })
      }
    }
  }
}
</script>

<style>
@import './tree.css';
</style>