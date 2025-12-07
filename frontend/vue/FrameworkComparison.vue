<template>
  <div class="FC_framework-comparison-container">
    <!-- Header -->
    <div class="FC_framework-comparison-header">
      <div class="FC_header-content">
        <h1 class="FC_framework-comparison-title">Framework Comparison</h1>
        <p class="FC_framework-comparison-subtitle">Compare compliance frameworks side-by-side</p>
      </div>
      <button class="FC_export-button">
        <i class="fas fa-download"></i>
        Export Comparison
      </button>
    </div>

    <!-- Framework Selection -->
    <div class="FC_framework-selection-card">
      <div class="FC_framework-selection-content">
        <div class="FC_framework-selector">
          <label class="FC_framework-label">Framework:</label>
          <select v-model="selectedFramework" class="FC_framework-select">
            <option v-for="option in frameworkOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Summary Statistics -->
    <div class="FC_summary-stats-grid">
      <div class="FC_summary-stat-card">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-new">11</p>
          <p class="FC_summary-stat-label">New Controls</p>
        </div>
      </div>
      <div class="FC_summary-stat-card">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-modified">24</p>
          <p class="FC_summary-stat-label">Modified</p>
        </div>
      </div>
      <div class="FC_summary-stat-card">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-removed">3</p>
          <p class="FC_summary-stat-label">Removed</p>
        </div>
      </div>
      <div class="FC_summary-stat-card">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-unchanged">58</p>
          <p class="FC_summary-stat-label">Unchanged</p>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="FC_filters-card">
      <div class="FC_filters-content">
        
          <div class="FC_search-input-wrapper">
            
            <input
              v-model="searchTerm"
              placeholder="Search policies, controls..."
              class="FC_search-input"
            />
          </div>
        
        <select v-model="filter" class="FC_filter-select">
          <option value="all">Show All</option>
          <option value="changes">Show Only Changes</option>
          <option value="gaps">Show Only Gaps</option>
        </select>
      </div>
    </div>

    <!-- Comparison View -->
    <div class="FC_comparison-view">
      <!-- Left Side Framework -->
      <div class="FC_framework-side">
        <div class="FC_framework-side-header">
          <h3 class="FC_framework-side-title">
            <span class="FC_framework-badge FC_framework-badge-current">ORIGIN</span>
            <select v-if="selectedFramework === 'iso27001'" v-model="leftVersion" class="FC_version-select">
              <option v-for="option in versionOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </h3>
        </div>
        <div class="FC_framework-side-content">
          <div 
            v-for="policy in filteredPolicies2013" 
            :key="policy.id" 
            class="FC_policy-item"
          >
            <div 
              class="FC_policy-header"
              @click="togglePolicy(policy.id, '2013')"
            >
              <i v-if="isPolicyExpanded(policy.id, '2013')" class="fas fa-chevron-down FC_toggle-icon"></i>
              <i v-else class="fas fa-chevron-right FC_toggle-icon"></i>
              <div class="FC_policy-info">
                <div class="FC_policy-title">
                  <span class="FC_policy-name">{{ policy.id }} - {{ policy.name }}</span>
                  <span v-if="policy.changeType" :class="`FC_change-badge FC_change-badge-${policy.changeType}`">
                    {{ getChangeLabel(policy.changeType) }}
                  </span>
                </div>
                <p class="FC_policy-description">{{ policy.description }}</p>
              </div>
            </div>
            
            <div v-if="isPolicyExpanded(policy.id, '2013')" class="FC_policy-content">
              <div 
                v-for="subPolicy in filteredSubPolicies(policy.subPolicies)" 
                :key="subPolicy.id" 
                class="FC_sub-policy-item"
              >
                <div 
                  class="FC_sub-policy-header"
                  @click="toggleSubPolicy(subPolicy.id, '2013')"
                >
                  <i v-if="isSubPolicyExpanded(subPolicy.id, '2013')" class="fas fa-chevron-down FC_toggle-icon"></i>
                  <i v-else class="fas fa-chevron-right FC_toggle-icon"></i>
                  <span class="FC_sub-policy-name">{{ subPolicy.name }}</span>
                  <span v-if="subPolicy.changeType" :class="`FC_change-badge FC_change-badge-${subPolicy.changeType}`">
                    {{ getChangeLabel(subPolicy.changeType) }}
                  </span>
                </div>
                
                <div v-if="isSubPolicyExpanded(subPolicy.id, '2013')" class="FC_sub-policy-content">
                  <p class="FC_sub-policy-description">{{ subPolicy.description }}</p>
                  <div 
                    v-for="compliance in filteredCompliances(subPolicy.compliances)" 
                    :key="compliance.id" 
                    class="FC_compliance-item"
                  >
                    <div class="FC_compliance-info">
                      <div class="FC_compliance-title">
                        <span class="FC_compliance-name">{{ compliance.name }}</span>
                        <span v-if="compliance.changeType" :class="`FC_change-badge FC_change-badge-${compliance.changeType}`">
                          {{ getChangeLabel(compliance.changeType) }}
                        </span>
                      </div>
                      <p class="FC_compliance-description">{{ compliance.description }}</p>
                    </div>
                    <span :class="`FC_status-badge FC_status-badge-${compliance.status}`">
                      {{ getStatusLabel(compliance.status) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Side Framework -->
      <div class="FC_framework-side">
        <div class="FC_framework-side-header">
          <h3 class="FC_framework-side-title">
            <span class="FC_framework-badge FC_framework-badge-target">TARGET</span>
            <select v-if="selectedFramework === 'iso27001'" v-model="rightVersion" class="FC_version-select">
              <option v-for="option in versionOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </h3>
        </div>
        <div class="FC_framework-side-content">
          <div 
            v-for="policy in filteredPolicies2022" 
            :key="policy.id" 
            class="FC_policy-item"
          >
            <div 
              class="FC_policy-header"
              @click="togglePolicy(policy.id, '2022')"
            >
              <i v-if="isPolicyExpanded(policy.id, '2022')" class="fas fa-chevron-down FC_toggle-icon"></i>
              <i v-else class="fas fa-chevron-right FC_toggle-icon"></i>
              <div class="FC_policy-info">
                <div class="FC_policy-title">
                  <span class="FC_policy-name">{{ policy.id }} - {{ policy.name }}</span>
                  <span v-if="policy.changeType" :class="`FC_change-badge FC_change-badge-${policy.changeType}`">
                    {{ getChangeLabel(policy.changeType) }}
                  </span>
                </div>
                <p class="FC_policy-description">{{ policy.description }}</p>
              </div>
            </div>
            
            <div v-if="isPolicyExpanded(policy.id, '2022')" class="FC_policy-content">
              <div 
                v-for="subPolicy in filteredSubPolicies(policy.subPolicies)" 
                :key="subPolicy.id" 
                class="FC_sub-policy-item"
              >
                <div 
                  class="FC_sub-policy-header"
                  @click="toggleSubPolicy(subPolicy.id, '2022')"
                >
                  <i v-if="isSubPolicyExpanded(subPolicy.id, '2022')" class="fas fa-chevron-down FC_toggle-icon"></i>
                  <i v-else class="fas fa-chevron-right FC_toggle-icon"></i>
                  <span class="FC_sub-policy-name">{{ subPolicy.name }}</span>
                  <span v-if="subPolicy.changeType" :class="`FC_change-badge FC_change-badge-${subPolicy.changeType}`">
                    {{ getChangeLabel(subPolicy.changeType) }}
                  </span>
                </div>
                
                <div v-if="isSubPolicyExpanded(subPolicy.id, '2022')" class="FC_sub-policy-content">
                  <p class="FC_sub-policy-description">{{ subPolicy.description }}</p>
                  <div 
                    v-for="compliance in filteredCompliances(subPolicy.compliances)" 
                    :key="compliance.id" 
                    class="FC_compliance-item"
                  >
                    <div class="FC_compliance-info">
                      <div class="FC_compliance-title">
                        <span class="FC_compliance-name">{{ compliance.name }}</span>
                        <span v-if="compliance.changeType" :class="`FC_change-badge FC_change-badge-${compliance.changeType}`">
                          {{ getChangeLabel(compliance.changeType) }}
                        </span>
                      </div>
                      <p class="FC_compliance-description">{{ compliance.description }}</p>
                    </div>
                    <span :class="`FC_status-badge FC_status-badge-${compliance.status}`">
                      {{ getStatusLabel(compliance.status) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="FC_legend-card">
      <div class="FC_legend-header">
        <h3 class="FC_legend-title">Legend</h3>
      </div>
      <div class="FC_legend-content">
        <div class="FC_legend-grid">
          <div class="FC_legend-section">
            <h4 class="FC_legend-section-title">Compliance Status</h4>
            <div class="FC_legend-items">
              <div class="FC_legend-item">
                <div class="FC_status-badge FC_status-badge-compliant">
                  <i class="fas fa-check-circle"></i>
                  <span>Compliant</span>
                </div>
                <span class="FC_legend-description">Fully compliant</span>
              </div>
              <div class="FC_legend-item">
                <div class="FC_status-badge FC_status-badge-partial">
                  <i class="fas fa-exclamation-circle"></i>
                  <span>Partially Compliant</span>
                </div>
                <span class="FC_legend-description">Partially compliant</span>
              </div>
              <div class="FC_legend-item">
                <div class="FC_status-badge FC_status-badge-non-compliant">
                  <i class="fas fa-times-circle"></i>
                  <span>Non-compliant</span>
                </div>
                <span class="FC_legend-description">Non-compliant</span>
              </div>
              <div class="FC_legend-item">
                <div class="FC_status-badge FC_status-badge-gap">
                  <i class="fas fa-circle"></i>
                  <span>Gap</span>
                </div>
                <span class="FC_legend-description">Gap identified</span>
              </div>
              <div class="FC_legend-item">
                <div class="FC_status-badge FC_status-badge-audit">
                  <i class="fas fa-clock"></i>
                  <span>Yet to Audit</span>
                </div>
                <span class="FC_legend-description">Yet to audit</span>
              </div>
            </div>
          </div>
          <div class="FC_legend-section">
            <h4 class="FC_legend-section-title">Change Types</h4>
            <div class="FC_legend-items">
              <div class="FC_legend-item">
                <div class="FC_change-badge FC_change-badge-new">
                  <i class="fas fa-plus"></i>
                  <span>New</span>
                </div>
                <span class="FC_legend-description">New in 2022</span>
              </div>
              <div class="FC_legend-item">
                <div class="FC_change-badge FC_change-badge-modified">
                  <i class="fas fa-edit"></i>
                  <span>Modified</span>
                </div>
                <span class="FC_legend-description">Modified from 2013</span>
              </div>
              <div class="FC_legend-item">
                <div class="FC_change-badge FC_change-badge-removed">
                  <i class="fas fa-minus"></i>
                  <span>Removed</span>
                </div>
                <span class="FC_legend-description">Removed in 2022</span>
              </div>
              <div class="FC_legend-item">
                <div class="FC_change-badge FC_change-badge-unchanged">
                  <i class="fas fa-equals"></i>
                  <span>Unchanged</span>
                </div>
                <span class="FC_legend-description">No changes</span>
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
  name: 'FrameworkComparison',
  data() {
    return {
      expandedPolicies2013: new Set(),
      expandedPolicies2022: new Set(),
      expandedSubPolicies2013: new Set(),
      expandedSubPolicies2022: new Set(),
      searchTerm: '',
      filter: 'all',
      selectedFramework: 'iso27001',
      leftVersion: '2013',
      rightVersion: '2022',
      iso27001_2013,
      iso27001_2022
    }
  },
  computed: {
    frameworkOptions() {
      return [
        { value: 'iso27001', label: 'ISO 27001' }
      ]
    },
    versionOptions() {
      return this.selectedFramework === 'iso27001' 
        ? [
            { value: '2013', label: 'ISO 27001:2013' },
            { value: '2022', label: 'ISO 27001:2022' }
          ]
        : []
    },
    filteredPolicies2013() {
      return this.iso27001_2013.policies.filter(policy => this.shouldShowItem(policy))
    },
    filteredPolicies2022() {
      return this.iso27001_2022.policies.filter(policy => this.shouldShowItem(policy))
    }
  },
  methods: {
    togglePolicy(policyId, version) {
      if (version === '2013') {
        if (this.expandedPolicies2013.has(policyId)) {
          this.expandedPolicies2013.delete(policyId)
        } else {
          this.expandedPolicies2013.add(policyId)
        }
      } else {
        if (this.expandedPolicies2022.has(policyId)) {
          this.expandedPolicies2022.delete(policyId)
        } else {
          this.expandedPolicies2022.add(policyId)
        }
      }
    },
    toggleSubPolicy(subPolicyId, version) {
      if (version === '2013') {
        if (this.expandedSubPolicies2013.has(subPolicyId)) {
          this.expandedSubPolicies2013.delete(subPolicyId)
        } else {
          this.expandedSubPolicies2013.add(subPolicyId)
        }
      } else {
        if (this.expandedSubPolicies2022.has(subPolicyId)) {
          this.expandedSubPolicies2022.delete(subPolicyId)
        } else {
          this.expandedSubPolicies2022.add(subPolicyId)
        }
      }
    },
    isPolicyExpanded(policyId, version) {
      return version === '2013' 
        ? this.expandedPolicies2013.has(policyId)
        : this.expandedPolicies2022.has(policyId)
    },
    isSubPolicyExpanded(subPolicyId, version) {
      return version === '2013' 
        ? this.expandedSubPolicies2013.has(subPolicyId)
        : this.expandedSubPolicies2022.has(subPolicyId)
    },
    shouldShowItem(item) {
      if (this.searchTerm && !item.name.toLowerCase().includes(this.searchTerm.toLowerCase())) {
        return false
      }
      
      if (this.filter === 'all') return true
      if (this.filter === 'changes') {
        return item.changeType !== 'unchanged'
      }
      if (this.filter === 'gaps') {
        return 'status' in item && (item.status === 'gap' || item.status === 'non-compliant')
      }
      
      return true
    },
    filteredSubPolicies(subPolicies) {
      return subPolicies.filter(subPolicy => this.shouldShowItem(subPolicy))
    },
    filteredCompliances(compliances) {
      return compliances.filter(compliance => this.shouldShowItem(compliance))
    },
    getChangeLabel(changeType) {
      const labels = {
        new: 'New',
        modified: 'Modified',
        removed: 'Removed',
        unchanged: 'Unchanged'
      }
      return labels[changeType] || changeType
    },
    getStatusLabel(status) {
      const labels = {
        compliant: 'Compliant',
        'non-compliant': 'Non-Compliant',
        partial: 'Partially Compliant',
        gap: 'Gap',
        audit: 'Yet to Audit'
      }
      return labels[status] || status
    }
  }
}
</script>

<style scoped>
.FC_framework-comparison-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  margin-left: 280px;
  max-width: 100%;
}

.FC_framework-comparison-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.FC_header-content h1 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.FC_framework-comparison-subtitle {
  color: var(--text-secondary);
  font-size: 1rem;
}

.FC_export-button {
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

.FC_export-button:hover {
  background: var(--secondary-color);
}

.FC_framework-selection-card,
.FC_filters-card,
.FC_legend-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.FC_framework-selection-content,
.FC_filters-content {
  display: flex;
  gap: 20px;
  align-items: center;
  justify-content: space-between;
}

.FC_framework-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.FC_framework-label {
  font-weight: 500;
  color: var(--text-primary);
}

.FC_framework-select,
.FC_version-select,
.FC_filter-select {
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 14px;
  transition: all 0.2s ease;
  cursor: pointer;
  min-width: 120px;
}

.FC_framework-select:focus,
.FC_version-select:focus,
.FC_filter-select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.FC_search-container {
  flex: 1;
  max-width: 400px;
}

.FC_search-input-wrapper {
  position: relative;
  width: 50%;
}

.FC_search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-secondary);
  font-size: 14px;
  z-index: 1;
}

.FC_search-input {
  width: 100%;
  padding: 10px 12px 10px 36px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 14px;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.FC_search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.FC_search-input::placeholder {
  color: var(--text-secondary);
  font-size: 14px;
}

.FC_summary-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.FC_summary-stat-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.FC_summary-stat-number {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.FC_summary-stat-new { color: #22c55e; }
.FC_summary-stat-modified { color: var(--primary-color); }
.FC_summary-stat-removed { color: #ef4444; }
.FC_summary-stat-unchanged { color: #6b7280; }

.FC_summary-stat-label {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.FC_comparison-view {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.FC_framework-side {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
}

.FC_framework-side-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  background: var(--secondary-color);
}

.FC_framework-side-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
}

.FC_framework-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.FC_framework-badge-current {
  background: var(--secondary-color);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.FC_framework-badge-target {
  background: var(--primary-color);
  color: white;
}

.FC_framework-side-content {
  max-height: 600px;
  overflow-y: auto;
  padding: 16px;
}

.FC_policy-item {
  border: 1px solid var(--border-color);
  border-radius: 6px;
  margin-bottom: 16px;
}

.FC_policy-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.FC_policy-header:hover {
  background: var(--secondary-color);
}

.FC_toggle-icon {
  color: var(--text-secondary);
  font-size: 0.875rem;
  transition: transform 0.2s ease;
  flex-shrink: 0;
  margin-top: 2px;
  width: 16px;
  text-align: center;
}

.FC_policy-header:hover .FC_toggle-icon,
.FC_sub-policy-header:hover .FC_toggle-icon {
  color: var(--primary-color);
}

.FC_policy-info {
  flex: 1;
  min-width: 0;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.FC_policy-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.FC_policy-name {
  font-weight: 600;
  color: var(--text-primary);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.FC_policy-description {
  color: var(--text-secondary);
  font-size: 0.875rem;
  word-wrap: break-word;
  overflow-wrap: break-word;
  line-height: 1.4;
}

.FC_policy-content {
  padding: 0 16px 16px 16px;
  border-top: 1px solid var(--border-color);
  margin-top: 8px;
}

.FC_sub-policy-item {
  margin-bottom: 8px;
}

.FC_sub-policy-header {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  cursor: pointer;
  border-radius: 6px;
  transition: background-color 0.2s ease;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  margin-bottom: 8px;
}

.FC_sub-policy-header:hover {
  background: var(--secondary-color);
}

.FC_sub-policy-name {
  font-weight: 500;
  color: var(--text-primary);
  flex: 1;
  min-width: 0;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.FC_sub-policy-content {
  margin-top: 8px;
  padding: 12px;
  background: var(--secondary-color);
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.FC_sub-policy-description {
  color: var(--text-secondary);
  font-size: 0.75rem;
  margin-bottom: 12px;
  word-wrap: break-word;
  overflow-wrap: break-word;
  line-height: 1.4;
}

.FC_compliance-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  margin-bottom: 8px;
}

.FC_compliance-info {
  flex: 1;
  min-width: 0;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.FC_compliance-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.FC_compliance-name {
  font-weight: 500;
  color: var(--text-primary);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.FC_compliance-description {
  color: var(--text-secondary);
  font-size: 0.75rem;
  word-wrap: break-word;
  overflow-wrap: break-word;
  line-height: 1.4;
}

.FC_change-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.625rem;
  font-weight: 600;
  border: 1px solid;
  transition: all 0.2s ease;
}

.FC_change-badge-new {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  border-color: rgba(34, 197, 94, 0.3);
}

.FC_change-badge-modified {
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary-color);
  border-color: rgba(59, 130, 246, 0.3);
}

.FC_change-badge-removed {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.3);
}

.FC_change-badge-unchanged {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
  border-color: rgba(107, 114, 128, 0.3);
}

.FC_status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  transition: all 0.2s ease;
  flex-shrink: 0;
  white-space: nowrap;
}

.FC_status-badge-compliant {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.FC_status-badge-non-compliant {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.FC_status-badge-partial {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.FC_status-badge-gap {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
}

.FC_status-badge-audit {
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary-color);
}

.FC_legend-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.FC_legend-header {
  margin-bottom: 24px;
}

.FC_legend-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.FC_legend-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

.FC_legend-section-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  font-size: 1rem;
}

.FC_legend-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.FC_legend-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
}

.FC_legend-description {
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  flex: 1;
}

@media (max-width: 1024px) {
  .FC_comparison-view {
    grid-template-columns: 1fr;
  }
  
  .FC_legend-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .FC_framework-comparison-container {
    padding: 16px;
  }
  
  .FC_framework-comparison-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .FC_summary-stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .FC_framework-selection-content,
  .FC_filters-content {
    flex-direction: column;
    align-items: stretch;
  }
  
  .FC_policy-header,
  .FC_sub-policy-header {
    padding: 12px;
  }
  
  .FC_compliance-item {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .FC_status-badge {
    align-self: flex-start;
  }
}
</style>
