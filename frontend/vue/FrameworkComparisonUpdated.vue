<template>
  <div class="FC_framework-comparison-container">
    <!-- Header -->
    <div class="FC_framework-comparison-header">
      <div class="FC_header-content">
        <h1 class="FC_framework-comparison-title">Framework Comparison</h1>
        <p class="FC_framework-comparison-subtitle">Analyze framework amendments and find matches</p>
      </div>
      <div class="FC_header-actions">
        <button
          class="FC_check-updates-button"
          @click="checkWithUpdates"
          :disabled="checkingUpdates || !selectedFrameworkId"
        >
          <i v-if="!checkingUpdates" class="fas fa-clipboard-check"></i>
          <i v-else class="fas fa-spinner fa-spin"></i>
          {{ checkingUpdates ? 'Checking...' : 'Check the updates' }}
        </button>
        <button class="FC_export-button" @click="exportComparison">
          <i class="fas fa-download"></i>
          Export Comparison
        </button>
      </div>
    </div>

    <!-- Framework Selection -->
    <div class="FC_framework-selection-card">
      <div class="FC_framework-selection-content">
        <div class="FC_framework-selector">
          <label class="FC_framework-label">Framework:</label>
          <select v-model="selectedFrameworkId" @change="onFrameworkChange" class="FC_framework-select">
            <option value="">Select Framework</option>
            <option v-for="framework in frameworkOptions" :key="framework.FrameworkId" :value="framework.FrameworkId">
              {{ framework.FrameworkName }} ({{ framework.amendment_count }} amendments)
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Document Viewer Section -->
    <div v-if="selectedFrameworkId && documentInfo && documentInfo.has_document" class="FC_document-viewer-card">
      <div class="FC_document-viewer-content">
        <div class="FC_document-info">
          <div class="FC_document-icon">
            <i class="fas fa-file-pdf"></i>
          </div>
          <div class="FC_document-details">
            <h3 class="FC_document-name">{{ documentInfo.document.name }}</h3>
            <p class="FC_document-meta">
              Amendment Date: {{ documentInfo.document.amendment_date }} | 
              Downloaded: {{ formatDate(documentInfo.document.downloaded_date) }}
            </p>
            <div v-if="documentInfo.document.processed" class="FC_document-status FC_document-processed">
              <i class="fas fa-check-circle"></i>
              Processed on {{ formatDate(documentInfo.document.processed_date) }}
            </div>
            <div v-else class="FC_document-status FC_document-pending">
              <i class="fas fa-clock"></i>
              Awaiting Analysis
            </div>
          </div>
        </div>
        <div class="FC_document-actions">
          <button 
            @click="viewDocument" 
            class="FC_view-document-button"
            title="View document in new tab"
          >
            <i class="fas fa-eye"></i>
            View Document
          </button>
          <button 
            v-if="!documentInfo.document.processed"
            @click="startAnalysis" 
            :disabled="analyzingDocument"
            class="FC_start-analysis-button"
            title="Start AI processing of the document"
          >
            <i v-if="!analyzingDocument" class="fas fa-brain"></i>
            <i v-else class="fas fa-spinner fa-spin"></i>
            {{ analyzingDocument ? 'Analyzing...' : 'Start Analysis' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="FC_loading-state">
      <i class="fas fa-spinner fa-spin"></i>
      <p>Loading framework data...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="FC_error-state">
      <i class="fas fa-exclamation-circle"></i>
      <p>{{ error }}</p>
    </div>

    <!-- Summary Statistics -->
    <div v-if="selectedFrameworkId && !loading && summaryStats" class="FC_summary-stats-grid">
      <div class="FC_summary-stat-card">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-new">{{ summaryStats.new_controls }}</p>
          <p class="FC_summary-stat-label">New Controls</p>
        </div>
      </div>
      <div class="FC_summary-stat-card">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-modified">{{ summaryStats.modified_controls }}</p>
          <p class="FC_summary-stat-label">Modified</p>
        </div>
      </div>
      <div class="FC_summary-stat-card">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-removed">{{ summaryStats.deprecated_controls }}</p>
          <p class="FC_summary-stat-label">Deprecated</p>
        </div>
      </div>
      <div class="FC_summary-stat-card">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-unchanged">{{ summaryStats.sub_policies_affected }}</p>
          <p class="FC_summary-stat-label">Sub-Policies Affected</p>
        </div>
      </div>
    </div>
    <div 
      v-if="selectedFrameworkId && !loading && extractionSummary" 
      class="FC_summary-stats-grid FC_structured-summary-grid"
    >
      <div class="FC_summary-stat-card">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-structured">
            {{ extractionSummary.total_policies || 0 }}
          </p>
          <p class="FC_summary-stat-label">Extracted Policies</p>
        </div>
      </div>
      <div class="FC_summary-stat-card">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-structured">
            {{ extractionSummary.total_subpolicies || 0 }}
          </p>
          <p class="FC_summary-stat-label">Extracted Sub-Policies</p>
        </div>
      </div>
      <div class="FC_summary-stat-card">
        <div class="FC_summary-stat-content">
          <p class="FC_summary-stat-number FC_summary-stat-structured">
            {{ extractionSummary.total_compliance_records || 0 }}
          </p>
          <p class="FC_summary-stat-label">Extracted Compliances</p>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div v-if="selectedFrameworkId && !loading" class="FC_filters-card">
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
        </select>
        <button 
          @click="toggleAIMatching" 
          :class="['FC_ai-toggle-button', { 'FC_ai-toggle-active': useAIMatching }]"
          title="AI Matching is more accurate but slower"
        >
          <i class="fas fa-brain"></i>
          {{ useAIMatching ? 'AI Matching ON' : 'AI Matching OFF' }}
        </button>
        <button 
          v-if="selectedControl"
          @click="clearMatches" 
          class="FC_clear-matches-button"
        >
          <i class="fas fa-times"></i>
          Clear Matches
        </button>
        <button 
          v-if="selectedFrameworkId && targetData"
          @click="matchCompliances" 
          :disabled="complianceMatchingInProgress"
          class="FC_match-compliances-button"
          title="Match all compliances from amendments"
        >
          <i v-if="!complianceMatchingInProgress" class="fas fa-check-circle"></i>
          <i v-else class="fas fa-spinner fa-spin"></i>
          {{ complianceMatchingInProgress ? 'Matching Compliances...' : 'Match Compliances' }}
        </button>
      </div>
    </div>
    
    <!-- Comparison View -->
    <div v-if="selectedFrameworkId && !loading && targetData" class="FC_comparison-view">
      <!-- Left Side - Target (Amendments) -->
      <div class="FC_framework-side">
        <div class="FC_framework-side-header">
          <h3 class="FC_framework-side-title">
            <span class="FC_framework-badge FC_framework-badge-target">TARGET</span>
            {{ targetData.amendment.amendment_name }}
          </h3>
        </div>
        <div class="FC_framework-side-content">
          <!-- Structured sections (policies / sub-policies / compliances) -->
          <div v-if="hasStructuredSections" class="FC_structured-sections">
            <div 
              v-for="(section, sectionIndex) in structuredSections" 
              :key="sectionIndex" 
              class="FC_structured-section"
            >
              <div class="FC_section-header-row">
                <h4 class="FC_structured-section-title">
                  {{ section.section_info?.title || section.section_info?.name || `Section ${sectionIndex + 1}` }}
                </h4>
                <span v-if="section.section_info?.start_page" class="FC_section-page-info">
                  Pages {{ section.section_info.start_page }}<span v-if="section.section_info.end_page"> - {{ section.section_info.end_page }}</span>
                </span>
              </div>
              <p 
                v-if="section.section_info?.summary" 
                class="FC_structured-section-summary"
              >
                {{ section.section_info.summary }}
              </p>
              
              <div 
                v-for="(policy, policyIndex) in section.policies || []"
                :key="`${sectionIndex}-policy-${policyIndex}`"
                class="FC_policy-card"
              >
                <div class="FC_policy-card-header">
                  <div>
                    <h5>{{ policy.policy_title || policy.policy_name || `Policy ${policyIndex + 1}` }}</h5>
                    <p v-if="policy.scope" class="FC_policy-scope">{{ policy.scope }}</p>
                  </div>
                  <span v-if="policy.policy_type" class="FC_policy-type-pill">{{ policy.policy_type }}</span>
                </div>
                <p class="FC_policy-card-description" v-if="policy.policy_description">{{ policy.policy_description }}</p>
                
                <div class="FC_subpolicy-list">
                  <div 
                    v-for="(subpolicy, subIndex) in policy.subpolicies || []"
                    :key="`${sectionIndex}-policy-${policyIndex}-sub-${subIndex}`"
                    class="FC_subpolicy-card"
                  >
                    <div class="FC_subpolicy-card-header">
                      <div>
                        <h6>{{ subpolicy.subpolicy_title || subpolicy.SubPolicyName || `Sub-Policy ${subIndex + 1}` }}</h6>
                        <p v-if="subpolicy.control" class="FC_subpolicy-control">{{ subpolicy.control }}</p>
                      </div>
                      <span v-if="subpolicy.subpolicy_id" class="FC_subpolicy-pill">{{ subpolicy.subpolicy_id }}</span>
                    </div>
                    <p class="FC_subpolicy-card-description" v-if="subpolicy.subpolicy_description">
                      {{ subpolicy.subpolicy_description }}
                    </p>
                    
                    <div 
                      v-if="subpolicy.compliance_records && subpolicy.compliance_records.length"
                      class="FC_compliance-chip-list"
                    >
                      <div 
                        v-for="(compliance, compIndex) in subpolicy.compliance_records"
                        :key="compIndex"
                        class="FC_compliance-chip"
                      >
                        <strong class="FC_compliance-chip-title">
                          {{
                            compliance.ComplianceTitle ||
                            compliance.compliance_title ||
                            compliance.title ||
                            `Compliance ${compIndex + 1}`
                          }}
                        </strong>
                        <p class="FC_compliance-chip-desc">
                          {{
                            compliance.ComplianceItemDescription ||
                            compliance.compliance_description ||
                            compliance.description ||
                            compliance.requirement ||
                            ''
                          }}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <template v-else>
            <!-- Modified Controls -->
            <div v-if="filteredTargetModifiedControls.length > 0">
            <h4 class="FC_section-header">Modified Controls</h4>
            <div 
              v-for="control in filteredTargetModifiedControls" 
              :key="'modified-' + control.control_id" 
              :class="['FC_policy-item', 'FC_clickable-control', { 'FC_selected-control': selectedControl && selectedControl.control_id === control.control_id }]"
            >
              <div 
                class="FC_policy-header"
                @click.stop="togglePolicy(control.control_id, 'target')"
              >
                <button 
                  @click.stop="findMatches(control)" 
                  class="FC_find-match-button"
                  :disabled="matchingInProgress"
                  title="Find matching items"
                >
                  <i v-if="!matchingInProgress" class="fas fa-search-plus"></i>
                  <i v-else class="fas fa-spinner fa-spin"></i>
                </button>
                <i v-if="isPolicyExpanded(control.control_id, 'target')" class="fas fa-chevron-down FC_toggle-icon"></i>
                <i v-else class="fas fa-chevron-right FC_toggle-icon"></i>
                <div class="FC_policy-info">
                  <div class="FC_policy-title">
                    <span class="FC_policy-name">{{ control.control_id }} - {{ control.control_name }}</span>
                    <span :class="`FC_change-badge FC_change-badge-${control.change_type}`">
                      {{ control.change_type }}
                    </span>
                  </div>
                  <p class="FC_policy-description">{{ control.change_description }}</p>
                </div>
              </div>
              
              <div v-if="isPolicyExpanded(control.control_id, 'target')" class="FC_policy-content">
                <!-- Enhancements -->
                <div v-if="control.enhancements && control.enhancements.length > 0" class="FC_enhancement-section">
                  <h5>Enhancements:</h5>
                  <ul>
                    <li v-for="(enhancement, idx) in control.enhancements" :key="idx">{{ enhancement }}</li>
                  </ul>
                </div>
                
                <!-- Related Controls -->
                <div v-if="control.related_controls && control.related_controls.length > 0" class="FC_related-section">
                  <h5>Related Controls:</h5>
                  <p>{{ control.related_controls.join(', ') }}</p>
                </div>
                
                <!-- Sub-policies -->
                <div v-if="control.sub_policies && control.sub_policies.length > 0">
                  <div 
                    v-for="subPolicy in control.sub_policies" 
                    :key="subPolicy.sub_policy_name" 
                    class="FC_sub-policy-item"
                  >
                    <div class="FC_sub-policy-header">
                      <span class="FC_sub-policy-name">{{ subPolicy.sub_policy_name }}</span>
                      <span :class="`FC_change-badge FC_change-badge-${subPolicy.change_type}`">
                        {{ subPolicy.change_type }}
                      </span>
                    </div>
                    <div class="FC_sub-policy-content">
                      <p class="FC_sub-policy-description">{{ subPolicy.change_description }}</p>
                      <div v-if="subPolicy.requirements && subPolicy.requirements.length > 0" class="FC_requirements-section">
                        <h6>Requirements:</h6>
                        <ul>
                          <li v-for="(req, idx) in subPolicy.requirements" :key="idx">{{ req }}</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            </div>
            
            <!-- New Additions -->
            <div v-if="filteredTargetNewAdditions.length > 0" class="FC_new-additions-section">
              <h4 class="FC_section-header">New Additions</h4>
              <div 
                v-for="addition in filteredTargetNewAdditions" 
                :key="'new-' + addition.control_id" 
                class="FC_policy-item FC_new-item"
              >
                <div class="FC_policy-header">
                  <div class="FC_policy-info">
                    <div class="FC_policy-title">
                      <span class="FC_policy-name">{{ addition.control_id }} - {{ addition.control_name }}</span>
                      <span class="FC_change-badge FC_change-badge-new">NEW</span>
                    </div>
                    <p class="FC_policy-description"><strong>Scope:</strong> {{ addition.scope }}</p>
                    <p class="FC_policy-description"><strong>Purpose:</strong> {{ addition.purpose }}</p>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- Right Side - Analysis (Matches Panel) -->
      <div class="FC_framework-side">
        <div class="FC_framework-side-header">
          <h3 class="FC_framework-side-title">
            <span class="FC_framework-badge FC_framework-badge-current">ANALYSIS</span>
            Control Matching
          </h3>
        </div>
        <div class="FC_framework-side-content">
          <div v-if="complianceMatches" class="FC_compliance-matches-panel">
            <div class="FC_matches-header">
              <h4>
                <i class="fas fa-check-circle"></i>
                Compliance Matching Results
              </h4>
              <span class="FC_match-badge">
                <i :class="useAIMatching ? 'fas fa-brain' : 'fas fa-text-width'"></i>
                {{ useAIMatching ? 'AI-Powered' : 'Text-Based' }}
              </span>
            </div>
            
            <!-- Summary -->
            <div class="FC_compliance-summary">
              <div class="FC_summary-stat">
                <span class="FC_summary-label">Total Compliances:</span>
                <span class="FC_summary-value">{{ complianceMatches.total_target || 0 }}</span>
              </div>
              <div class="FC_summary-stat FC_summary-matched">
                <span class="FC_summary-label">Matched:</span>
                <span class="FC_summary-value">{{ complianceMatches.matched_count || 0 }}</span>
              </div>
              <div class="FC_summary-stat FC_summary-unmatched">
                <span class="FC_summary-label">Not Following:</span>
                <span class="FC_summary-value">{{ complianceMatches.unmatched_count || 0 }}</span>
              </div>
            </div>
            
            <!-- Matched Compliances - Show only ONE match per target compliance -->
            <div v-if="complianceMatches.matched && complianceMatches.matched.length > 0" class="FC_compliance-section">
              <h5 class="FC_section-title FC_matched-title">
                <i class="fas fa-check-circle"></i>
                Matched Compliances
              </h5>
              <div class="FC_compliance-list">
                <div 
                  v-for="(match, index) in complianceMatches.matched" 
                  :key="'matched-' + index" 
                  :class="['FC_compliance-match-item', 'FC_matched-item', 'FC_expandable-item', { 'FC_expanded': expandedComplianceIndex === index }]"
                  @click="toggleComplianceDetails(index)"
                >
                  <div class="FC_compliance-match-header">
                    <div class="FC_match-status-icon FC_match-success">
                      <i class="fas fa-check"></i>
                    </div>
                    <div class="FC_compliance-match-info">
                      <h6 class="FC_target-compliance-title">
                        {{ match.target_compliance.compliance_title || 'Compliance' }}
                      </h6>
                      <p class="FC_target-compliance-desc">
                        {{ match.target_compliance.compliance_description || '' }}
                      </p>
                    </div>
                    <div class="FC_expand-icon">
                      <i :class="expandedComplianceIndex === index ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
                    </div>
                  </div>
                  
                  <!-- Matched Compliance Details - Expandable -->
                  <div v-if="expandedComplianceIndex === index" class="FC_matched-compliance-details">
                    <div class="FC_detail-section">
                      <label>Policy:</label>
                      <span>{{ match.matched_compliance.policy_identifier || '' }} - {{ match.matched_compliance.policy_name || '' }}</span>
                    </div>
                    <div class="FC_detail-section">
                      <label>Policy Description:</label>
                      <span>{{ match.matched_compliance.policy_description || '' }}</span>
                    </div>
                    <div class="FC_detail-section">
                      <label>Sub-Policy:</label>
                      <span>{{ match.matched_compliance.subpolicy_identifier || '' }} - {{ match.matched_compliance.subpolicy_name || '' }}</span>
                    </div>
                    <div class="FC_detail-section">
                      <label>Sub-Policy Description:</label>
                      <span>{{ match.matched_compliance.subpolicy_description || '' }}</span>
                    </div>
                    <div class="FC_detail-section">
                      <label>Compliance Title:</label>
                      <span>{{ match.matched_compliance.compliance_title || '' }}</span>
                    </div>
                    <div class="FC_detail-section">
                      <label>Compliance Description:</label>
                      <span>{{ match.matched_compliance.compliance_description || '' }}</span>
                    </div>
                    <div v-if="match.matched_compliance.compliance_type" class="FC_detail-section">
                      <label>Compliance Type:</label>
                      <span>{{ match.matched_compliance.compliance_type }}</span>
                    </div>
                    <div v-if="match.matched_compliance.status" class="FC_detail-section">
                      <label>Status:</label>
                      <span>{{ match.matched_compliance.status }}</span>
                    </div>
                    <div v-if="match.matched_compliance.criticality" class="FC_detail-section">
                      <label>Criticality:</label>
                      <span>{{ match.matched_compliance.criticality }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Unmatched Compliances -->
            <div v-if="complianceMatches.unmatched && complianceMatches.unmatched.length > 0" class="FC_compliance-section">
              <h5 class="FC_section-title FC_unmatched-title">
                <i class="fas fa-exclamation-triangle"></i>
                Not Following These Compliances
              </h5>
              <div class="FC_compliance-list">
                <div 
                  v-for="(unmatch, index) in complianceMatches.unmatched" 
                  :key="'unmatched-' + index" 
                  class="FC_compliance-match-item FC_unmatched-item"
                >
                  <div class="FC_compliance-match-header">
                    <div class="FC_match-status-icon FC_match-warning">
                      <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <div class="FC_compliance-match-info">
                      <h6 class="FC_target-compliance-title">
                        {{ unmatch.target_compliance.compliance_title || 'Compliance' }}
                      </h6>
                      <p class="FC_target-compliance-desc">
                        {{ unmatch.target_compliance.compliance_description || '' }}
                      </p>
                    </div>
                    <button 
                      class="FC_add-compliance-button" 
                      @click.stop="openComplianceModal(unmatch)"
                      title="Add this compliance to framework"
                    >
                      <i class="fas fa-plus"></i>
                    </button>
                  </div>
                  <div class="FC_unmatched-message">
                    <i class="fas fa-times-circle"></i>
                    <span>{{ unmatch.message || 'We are not following this compliance' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else-if="!selectedControl" class="FC_analysis-placeholder">
            <i class="fas fa-search"></i>
            <p>Select a control from the left panel and click the search button to find matches.</p>
          </div>
          <div v-else-if="selectedControl && !controlMatches" class="FC_analysis-placeholder">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Finding matches for: {{ selectedControl.control_id }}</p>
          </div>
          <div v-else class="FC_matches-panel">
            <div class="FC_matches-header">
              <h4>
                <i class="fas fa-link"></i>
                Best Matches for: {{ selectedControl.control_id }} - {{ selectedControl.control_name }}
              </h4>
              <span class="FC_match-badge">
                <i :class="useAIMatching ? 'fas fa-brain' : 'fas fa-text-width'"></i>
                {{ useAIMatching ? 'AI-Powered' : 'Text-Based' }}
              </span>
            </div>
            <div class="FC_matches-list">
              <div 
                v-for="(match, index) in controlMatches" 
                :key="index" 
                class="FC_match-item"
              >
                <div class="FC_match-rank">{{ index + 1 }}</div>
                <div class="FC_match-info">
                  <div class="FC_match-type-badge">
                    <i :class="match.type === 'policy' ? 'fas fa-folder' : match.type === 'subpolicy' ? 'fas fa-file' : 'fas fa-check-circle'"></i>
                    {{ match.type.toUpperCase() }}
                  </div>
                  <p class="FC_match-path">{{ match.path }}</p>
                </div>
                <div class="FC_match-score">
                  <div class="FC_score-bar">
                    <div class="FC_score-fill" :style="{ width: (match.score * 100) + '%' }"></div>
                  </div>
                  <span class="FC_score-text">{{ (match.score * 100).toFixed(1) }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div v-if="selectedFrameworkId && !loading" class="FC_legend-card">
      <div class="FC_legend-header">
        <h3 class="FC_legend-title">Legend</h3>
      </div>
      <div class="FC_legend-content">
        <div class="FC_legend-grid">
          <div class="FC_legend-section">
            <h4 class="FC_legend-section-title">Change Types</h4>
            <div class="FC_legend-items">
              <div class="FC_legend-item">
                <div class="FC_change-badge FC_change-badge-new">
                  <i class="fas fa-plus"></i>
                  <span>New</span>
                </div>
                <span class="FC_legend-description">New control added</span>
              </div>
              <div class="FC_legend-item">
                <div class="FC_change-badge FC_change-badge-modified">
                  <i class="fas fa-edit"></i>
                  <span>Modified</span>
                </div>
                <span class="FC_legend-description">Modified control</span>
              </div>
              <div class="FC_legend-item">
                <div class="FC_change-badge FC_change-badge-enhanced">
                  <i class="fas fa-arrow-up"></i>
                  <span>Enhanced</span>
                </div>
                <span class="FC_legend-description">Enhanced control</span>
              </div>
              <div class="FC_legend-item">
                <div class="FC_change-badge FC_change-badge-deprecated">
                  <i class="fas fa-minus"></i>
                  <span>Deprecated</span>
                </div>
                <span class="FC_legend-description">Deprecated control</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="showComplianceModal" class="FC_modal-backdrop">
      <div class="FC_modal">
        <div class="FC_modal-header">
          <h3>Add Compliance to Framework</h3>
          <button class="FC_modal-close" @click="closeComplianceModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="FC_modal-body">
          <div class="FC_modal-section">
            <h4>Policy Details</h4>
            <div class="FC_modal-field">
              <label>Policy Name</label>
              <input type="text" v-model="complianceForm.policy_name" />
            </div>
            <div class="FC_modal-field">
              <label>Policy Identifier</label>
              <input type="text" v-model="complianceForm.policy_identifier" />
            </div>
            <div class="FC_modal-field">
              <label>Policy Description</label>
              <textarea v-model="complianceForm.policy_description"></textarea>
            </div>
            <div class="FC_modal-grid">
              <div class="FC_modal-field">
                <label>Scope</label>
                <input type="text" v-model="complianceForm.policy_scope" />
              </div>
              <div class="FC_modal-field">
                <label>Objective</label>
                <input type="text" v-model="complianceForm.policy_objective" />
              </div>
            </div>
          </div>

          <div class="FC_modal-section">
            <h4>Sub-Policy Details</h4>
            <div class="FC_modal-field">
              <label>Sub-Policy Name</label>
              <input type="text" v-model="complianceForm.subpolicy_name" />
            </div>
            <div class="FC_modal-field">
              <label>Sub-Policy Identifier</label>
              <input type="text" v-model="complianceForm.subpolicy_identifier" />
            </div>
            <div class="FC_modal-field">
              <label>Description</label>
              <textarea v-model="complianceForm.subpolicy_description"></textarea>
            </div>
            <div class="FC_modal-field">
              <label>Control</label>
              <input type="text" v-model="complianceForm.subpolicy_control" />
            </div>
          </div>

          <div class="FC_modal-section">
            <h4>Compliance Details</h4>
            <div class="FC_modal-field">
              <label>Compliance Title</label>
              <input type="text" v-model="complianceForm.compliance_title" />
            </div>
            <div class="FC_modal-field">
              <label>Compliance Description</label>
              <textarea v-model="complianceForm.compliance_description"></textarea>
            </div>
            <div class="FC_modal-grid">
              <div class="FC_modal-field">
                <label>Compliance Type</label>
                <input type="text" v-model="complianceForm.compliance_type" />
              </div>
              <div class="FC_modal-field">
                <label>Criticality</label>
                <select v-model="complianceForm.criticality">
                  <option>Low</option>
                  <option>Medium</option>
                  <option>High</option>
                  <option>Critical</option>
                </select>
              </div>
            </div>
            <div class="FC_modal-grid">
              <div class="FC_modal-field">
                <label>Mandatory / Optional</label>
                <select v-model="complianceForm.mandatory">
                  <option>Mandatory</option>
                  <option>Optional</option>
                </select>
              </div>
              <div class="FC_modal-field">
                <label>Manual / Automatic</label>
                <select v-model="complianceForm.manual_automatic">
                  <option>Manual</option>
                  <option>Automatic</option>
                </select>
              </div>
            </div>
          </div>
          <p v-if="complianceSaveError" class="FC_modal-error">{{ complianceSaveError }}</p>
        </div>
        <div class="FC_modal-footer">
          <button class="FC_modal-secondary" @click="closeComplianceModal">Cancel</button>
          <button 
            class="FC_modal-primary"
            :disabled="submittingCompliance"
            @click="submitComplianceForm"
          >
            <span v-if="!submittingCompliance">Save Compliance</span>
            <span v-else><i class="fas fa-spinner fa-spin"></i> Saving...</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import frameworkComparisonService from '@/services/frameworkComparisonService'

export default {
  name: 'FrameworkComparison',
  data() {
    return {
      frameworkOptions: [],
      selectedFrameworkId: '',
      loading: false,
      error: null,
      
      // Data
      targetData: null,
      summaryStats: null,
      
      // UI State
      expandedPoliciesTarget: new Set(),
      expandedSubPoliciesTarget: new Set(),
      searchTerm: '',
      filter: 'all',
      
      // Similarity Matching
      selectedControl: null,
      controlMatches: null,
      matchingInProgress: false,
      useAIMatching: false,  // Toggle for AI-powered matching
      
      // Compliance Matching
      complianceMatches: null,
      complianceMatchingInProgress: false,
      expandedComplianceIndex: null,  // Track which compliance is expanded
      checkingUpdates: false,
      showComplianceModal: false,
      complianceModalData: null,
      
      // Document Viewer
      documentInfo: null,
      analyzingDocument: false,
      complianceForm: {
        policy_name: '',
        policy_identifier: '',
        policy_description: '',
        policy_scope: '',
        policy_objective: '',
        subpolicy_name: '',
        subpolicy_identifier: '',
        subpolicy_description: '',
        subpolicy_control: '',
        compliance_title: '',
        compliance_description: '',
        compliance_type: '',
        criticality: 'Medium',
        mandatory: 'Mandatory',
        manual_automatic: 'Manual'
      },
      complianceSaveError: '',
      submittingCompliance: false
    }
  },
  
  computed:{
    filteredTargetModifiedControls() {
      if (!this.targetData || !this.targetData.modified_controls) return []
      
      let controls = this.targetData.modified_controls
      
      // Apply search filter
      if (this.searchTerm) {
        const search = this.searchTerm.toLowerCase()
        controls = controls.filter(control => 
          (control.control_name && control.control_name.toLowerCase().includes(search)) ||
          (control.control_id && control.control_id.toLowerCase().includes(search)) ||
          (control.change_description && control.change_description.toLowerCase().includes(search))
        )
      }
      
      // Apply change filter
      if (this.filter === 'changes') {
        controls = controls.filter(control => control.change_type !== 'unchanged')
      }
      
      return controls
    },
    
    filteredTargetNewAdditions() {
      if (!this.targetData || !this.targetData.new_additions) return []
      
      let additions = this.targetData.new_additions
      
      // Apply search filter
      if (this.searchTerm) {
        const search = this.searchTerm.toLowerCase()
        additions = additions.filter(addition => 
          (addition.control_name && addition.control_name.toLowerCase().includes(search)) ||
          (addition.control_id && addition.control_id.toLowerCase().includes(search)) ||
          (addition.scope && addition.scope.toLowerCase().includes(search))
        )
      }
      
      return additions
    },
    
    structuredSections() {
      if (!this.targetData || !Array.isArray(this.targetData.sections)) return []
      return this.targetData.sections
    },
    
    hasStructuredSections() {
      return this.structuredSections.length > 0
    },
    
    extractionSummary() {
      if (!this.targetData || !this.targetData.extraction_summary) return null
      return this.targetData.extraction_summary
    }
  },
  
  async mounted() {
    await this.loadFrameworksWithAmendments()
    await this.applyFrameworkFromSession()
  },
  
  methods: {
    async loadFrameworksWithAmendments() {
      try {
        this.loading = true
        this.error = null
        
        const response = await frameworkComparisonService.getFrameworksWithAmendments()
        
        if (response.success) {
          this.frameworkOptions = response.data
        } else {
          this.error = response.error || 'Failed to load frameworks'
        }
      } catch (error) {
        this.error = 'Error loading frameworks: ' + error.message
        console.error('Error loading frameworks:', error)
      } finally {
        this.loading = false
      }
    },
    
    async applyFrameworkFromSession() {
      try {
        const response = await frameworkComparisonService.getSelectedFramework()
        
        if (response && response.success) {
          const selectedId = response.frameworkId
          
          if (selectedId) {
            const frameworkExists = this.frameworkOptions.find(
              framework => String(framework.FrameworkId) === String(selectedId)
            )
            
            if (frameworkExists) {
              this.selectedFrameworkId = frameworkExists.FrameworkId
              await this.onFrameworkChange()
              return
            } else {
              console.warn('Selected framework not found in options:', selectedId)
            }
          }
        }
        
        // No framework selected or not found - default to showing all frameworks
        this.selectedFrameworkId = ''
        await this.onFrameworkChange()
      } catch (error) {
        console.error('Error applying framework from session:', error)
      }
    },
    
    async onFrameworkChange() {
      if (!this.selectedFrameworkId) {
        this.targetData = null
        this.summaryStats = null
        this.selectedControl = null
        this.controlMatches = null
        this.complianceMatches = null
        this.expandedComplianceIndex = null
        this.documentInfo = null
        return
      }
      
      try {
        this.loading = true
        this.error = null
        
        // Load target data, summary, and document info in parallel
        const [targetResponse, summaryResponse] = await Promise.all([
          frameworkComparisonService.getFrameworkTargetData(this.selectedFrameworkId),
          frameworkComparisonService.getFrameworkComparisonSummary(this.selectedFrameworkId)
        ])
        
        // Fetch document info separately (it sets this.documentInfo internally)
        await this.fetchDocumentInfo()
        
        if (targetResponse.success) {
          this.targetData = targetResponse
        }
        
        if (summaryResponse.success) {
          this.summaryStats = summaryResponse.summary
        }
        
      } catch (error) {
        this.error = 'Error loading framework data: ' + error.message
        console.error('Error loading framework data:', error)
      } finally {
        this.loading = false
      }
    },
    
    togglePolicy(policyId, side) {
      if (side === 'target') {
        if (this.expandedPoliciesTarget.has(policyId)) {
          this.expandedPoliciesTarget.delete(policyId)
        } else {
          this.expandedPoliciesTarget.add(policyId)
        }
      }
    },
    
    toggleSubPolicy(subPolicyId, side) {
      if (side === 'target') {
        if (this.expandedSubPoliciesTarget.has(subPolicyId)) {
          this.expandedSubPoliciesTarget.delete(subPolicyId)
        } else {
          this.expandedSubPoliciesTarget.add(subPolicyId)
        }
      }
    },
    
    isPolicyExpanded(policyId, side) {
      return side === 'target' && this.expandedPoliciesTarget.has(policyId)
    },
    
    isSubPolicyExpanded(subPolicyId, side) {
      return side === 'target' && this.expandedSubPoliciesTarget.has(subPolicyId)
    },
    
    exportComparison() {
      // TODO: Implement export functionality
      alert('Export functionality coming soon!')
    },
    
    async checkWithUpdates() {
      if (!this.selectedFrameworkId) {
        alert('Please select a framework first.')
        return
      }

      try {
        this.checkingUpdates = true
        const response = await frameworkComparisonService.checkFrameworkUpdates(this.selectedFrameworkId)

          if (response && response.warning) {
            alert(response.warning)
            return
          }

          if (response && response.success) {
          const updateResult = response.result || {}
          const hasUpdate = !!updateResult.has_update
          let message = response.message ||
            (hasUpdate ? 'New amendment detected.' : 'No new amendments found.')

          if (updateResult.downloaded_path) {
            message += `\nFile saved to: ${updateResult.downloaded_path}`
          }

          // Always refresh document info to show the latest downloaded document
          await this.fetchDocumentInfo()
          
          if (hasUpdate) {
            await this.onFrameworkChange()
          }

          alert(message)
        } else {
          alert(response && response.error ? response.error : 'Unable to check updates.')
        }
      } catch (error) {
        console.error('Error checking updates:', error)
        alert(`Error checking updates: ${error.message}`)
      } finally {
        this.checkingUpdates = false
      }
    },
    
    async fetchDocumentInfo() {
      if (!this.selectedFrameworkId) {
        this.documentInfo = null
        return
      }
      
      try {
        const response = await frameworkComparisonService.getAmendmentDocumentInfo(this.selectedFrameworkId)
        
        if (response && response.success) {
          this.documentInfo = response
          console.log('Document info loaded:', this.documentInfo)
        } else {
          this.documentInfo = null
        }
      } catch (error) {
        console.error('Error fetching document info:', error)
        this.documentInfo = null
      }
    },
    
    viewDocument() {
      if (!this.documentInfo || !this.documentInfo.document || !this.documentInfo.document.url) {
        alert('Document URL not available')
        return
      }
      
      // Open document in new tab
      const documentUrl = this.documentInfo.document.url
      window.open(documentUrl, '_blank')
    },
    
    async startAnalysis() {
      if (!this.selectedFrameworkId) {
        alert('Please select a framework first.')
        return
      }
      
      if (!this.documentInfo || !this.documentInfo.has_document) {
        alert('No document available to analyze.')
        return
      }
      
      try {
        this.analyzingDocument = true
        
        const response = await frameworkComparisonService.startAmendmentAnalysis(this.selectedFrameworkId)
        
        if (response && response.success) {
          alert(`Analysis completed successfully!\n\n${response.message}`)
          
          // Refresh document info and framework data
          await this.fetchDocumentInfo()
          await this.onFrameworkChange()
        } else {
          alert(response && response.error ? `Analysis failed: ${response.error}` : 'Analysis failed.')
        }
      } catch (error) {
        console.error('Error starting analysis:', error)
        alert(`Error starting analysis: ${error.message}`)
      } finally {
        this.analyzingDocument = false
      }
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      
      try {
        const date = new Date(dateString)
        return date.toLocaleString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      } catch (error) {
        return dateString
      }
    },
    
    async findMatches(control) {
      if (!control || !this.selectedFrameworkId) return
      
      try {
        this.matchingInProgress = true
        this.selectedControl = control
        this.controlMatches = null
        
        console.log('Finding matches for control:', control)
        
        const response = await frameworkComparisonService.findControlMatches(
          this.selectedFrameworkId,
          control,
          this.useAIMatching,
          5
        )
        
        if (response.success) {
          this.controlMatches = response.matches
          this.$forceUpdate()
        } else {
          console.error('Error finding matches:', response.error)
          alert(`Error finding matches: ${response.error}`)
        }
      } catch (error) {
        console.error('Error finding matches:', error)
        alert(`Error: ${error.message}`)
      } finally {
        this.matchingInProgress = false
      }
    },
    
    clearMatches() {
      this.selectedControl = null
      this.controlMatches = null
      this.complianceMatches = null
      this.expandedComplianceIndex = null
      this.$forceUpdate()
    },
    
    toggleComplianceDetails(index) {
      // Toggle: if already expanded, collapse; otherwise expand this one
      if (this.expandedComplianceIndex === index) {
        this.expandedComplianceIndex = null
      } else {
        this.expandedComplianceIndex = index
      }
      this.$forceUpdate()
    },
    
    toggleAIMatching() {
      this.useAIMatching = !this.useAIMatching
      // If a control is already selected, re-run matching with new setting
      if (this.selectedControl) {
        this.findMatches(this.selectedControl)
      }
    },
    
    async matchCompliances() {
      if (!this.selectedFrameworkId || !this.targetData) return
      
      try {
        this.complianceMatchingInProgress = true
        this.complianceMatches = null
        this.expandedComplianceIndex = null
        
        console.log('Matching compliances for framework:', this.selectedFrameworkId)
        
        const response = await frameworkComparisonService.matchAmendmentsCompliances(
          this.selectedFrameworkId,
          this.useAIMatching,  // Use AI matching
          0.65  // Threshold for matching
        )
        
        if (response.success) {
          this.complianceMatches = response.results
          this.$forceUpdate()
          return response
        } else {
          console.error('Error matching compliances:', response.error)
          alert(`Error matching compliances: ${response.error}`)
        }
      } catch (error) {
        console.error('Error matching compliances:', error)
        alert(`Error: ${error.message}`)
      } finally {
        this.complianceMatchingInProgress = false
      }
    },

    openComplianceModal(unmatch) {
      const target = unmatch?.target_compliance || {}
      const policyInfo = target.policy_info || {}
      const subpolicyInfo = target.subpolicy_info || {}

      this.complianceForm = {
        policy_name: policyInfo.policy_name || '',
        policy_identifier: policyInfo.policy_identifier || '',
        policy_description: policyInfo.policy_description || '',
        policy_scope: policyInfo.scope || '',
        policy_objective: policyInfo.objective || '',
        subpolicy_name: subpolicyInfo.subpolicy_name || '',
        subpolicy_identifier: subpolicyInfo.subpolicy_identifier || '',
        subpolicy_description: subpolicyInfo.subpolicy_description || '',
        subpolicy_control: subpolicyInfo.control || '',
        compliance_title: target.compliance_title || '',
        compliance_description: target.compliance_description || '',
        compliance_type: target.compliance_type || '',
        criticality: target.criticality || 'Medium',
        mandatory: target.mandatory || 'Mandatory',
        manual_automatic: target.manual_automatic || 'Manual'
      }
      this.complianceModalData = unmatch
      this.complianceSaveError = ''
      this.showComplianceModal = true
    },

    closeComplianceModal() {
      if (this.submittingCompliance) return
      this.showComplianceModal = false
      this.complianceModalData = null
    },

    async submitComplianceForm() {
      if (!this.selectedFrameworkId) return
      try {
        this.submittingCompliance = true
        this.complianceSaveError = ''
        const payload = {
          policy: {
            name: this.complianceForm.policy_name,
            identifier: this.complianceForm.policy_identifier,
            description: this.complianceForm.policy_description,
            scope: this.complianceForm.policy_scope,
            objective: this.complianceForm.policy_objective
          },
          subpolicy: {
            name: this.complianceForm.subpolicy_name,
            identifier: this.complianceForm.subpolicy_identifier,
            description: this.complianceForm.subpolicy_description,
            control: this.complianceForm.subpolicy_control
          },
          compliance: {
            title: this.complianceForm.compliance_title,
            description: this.complianceForm.compliance_description,
            type: this.complianceForm.compliance_type,
            criticality: this.complianceForm.criticality,
            mandatory: this.complianceForm.mandatory,
            manual_automatic: this.complianceForm.manual_automatic
          }
        }
        await frameworkComparisonService.createComplianceFromAmendment(
          this.selectedFrameworkId,
          payload
        )
        this.showComplianceModal = false
        this.complianceModalData = null
        await this.matchCompliances()
      } catch (error) {
        this.complianceSaveError = error?.response?.data?.error || error.message || 'Failed to save compliance'
      } finally {
        this.submittingCompliance = false
      }
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

.FC_header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
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

.FC_check-updates-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--primary-color);
  border: 1px solid var(--primary-color);
  color: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.FC_check-updates-button:hover {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.FC_export-button:hover {
  background: var(--secondary-color);
}

.FC_framework-selection-card,
.FC_filters-card,
.FC_legend-card,
.FC_document-viewer-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.FC_document-viewer-card {
  background: transparent;
  border: 1px solid #e5e7eb;
  border-radius: 0;
  box-shadow: none;
  color: #1f2937;
}

.FC_document-viewer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.FC_document-info {
  display: flex;
  gap: 16px;
  align-items: center;
  flex: 1;
}

.FC_document-icon {
  font-size: 48px;
  color: #4f8cff;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border-radius: 0;
  padding: 16px;
  min-width: 80px;
  height: 80px;
}

.FC_document-details {
  flex: 1;
}

.FC_document-name {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #1f2937;
}

.FC_document-meta {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0 0 8px 0;
}

.FC_document-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  padding: 4px 12px;
  border-radius: 0;
  font-weight: 500;
  border: 1px solid transparent;
}

.FC_document-processed {
  background: transparent;
  color: #22c55e;
  border: 1px solid #22c55e;
}

.FC_document-pending {
  background: transparent;
  color: #f59e0b;
  border: 1px solid #f59e0b;
}

.FC_document-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.FC_view-document-button,
.FC_start-analysis-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 0;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid #d1d5db;
  font-size: 0.9375rem;
  background: transparent;
  color: #1f2937;
}

.FC_view-document-button {
  background: transparent;
  color: #1f2937;
  border: 1px solid #d1d5db;
}

.FC_view-document-button:hover {
  background: transparent;
  border-color: #4f8cff;
  color: #4f8cff;
  opacity: 0.8;
}

.FC_start-analysis-button {
  background: transparent;
  color: #1f2937;
  font-weight: 600;
  border: 1px solid #4f8cff;
  color: #4f8cff;
}

.FC_start-analysis-button:hover:not(:disabled) {
  background: transparent;
  border-color: #1d4ed8;
  color: #1d4ed8;
  opacity: 0.8;
  transform: none;
  box-shadow: none;
}

.FC_start-analysis-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  border-color: #d1d5db;
  color: #6b7280;
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
.FC_summary-stat-structured { color: #0ea5e9; }
.FC_structured-summary-grid {
  margin-top: 8px;
}

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

.FC_structured-sections {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.FC_structured-section {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  background: var(--card-bg);
}

.FC_section-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.FC_structured-section-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.FC_section-page-info {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.FC_structured-section-summary {
  margin: 0 0 12px 0;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.FC_policy-card {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  margin-top: 12px;
  background: var(--secondary-color);
}

.FC_policy-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.FC_policy-card-header h5 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.FC_policy-scope {
  margin: 4px 0 0 0;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.FC_policy-type-pill {
  background: rgba(59, 130, 246, 0.15);
  color: var(--primary-color);
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.FC_policy-card-description {
  margin: 12px 0;
  color: var(--text-secondary);
  line-height: 1.5;
}

.FC_subpolicy-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.FC_subpolicy-card {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px;
  background: var(--card-bg);
}

.FC_subpolicy-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.FC_subpolicy-card-header h6 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
}

.FC_subpolicy-control {
  margin: 4px 0 0 0;
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-style: italic;
}

.FC_subpolicy-pill {
  background: rgba(14, 165, 233, 0.15);
  color: #0ea5e9;
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
}

.FC_subpolicy-card-description {
  margin: 8px 0 0 0;
  color: var(--text-secondary);
  font-size: 0.875rem;
  line-height: 1.5;
}

.FC_compliance-chip-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.FC_compliance-chip {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px;
  background: rgba(34, 197, 94, 0.08);
}

.FC_compliance-chip-title {
  display: block;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.FC_compliance-chip-desc {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.85rem;
  line-height: 1.4;
}

.FC_framework-side-content .FC_matches-panel {
  padding: 0;
}

.FC_framework-side-content .FC_matches-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.FC_framework-side-content .FC_matches-list {
  gap: 12px;
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

.FC_change-badge-enhanced {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
  border-color: rgba(245, 158, 11, 0.3);
}

.FC_change-badge-deprecated {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.3);
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

.FC_loading-state, .FC_error-state {
  text-align: center;
  padding: 40px;
  background: var(--card-bg);
  border-radius: 12px;
  margin: 20px 0;
}

.FC_loading-state i, .FC_error-state i {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: var(--primary-color);
}

.FC_error-state i {
  color: #ef4444;
}

.FC_section-header {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 20px 0 10px 0;
  padding: 10px;
  background: var(--secondary-color);
  border-radius: 6px;
}

.FC_enhancement-section, .FC_related-section, .FC_requirements-section {
  margin-top: 12px;
  padding: 12px;
  background: var(--secondary-color);
  border-radius: 6px;
}

.FC_enhancement-section h5, .FC_related-section h5, .FC_requirements-section h6 {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.FC_enhancement-section ul, .FC_requirements-section ul {
  margin-left: 20px;
  color: var(--text-secondary);
}

.FC_new-item {
  border-left: 4px solid #22c55e;
}

/* AI Matching Styles */
.FC_ai-toggle-button,
.FC_clear-matches-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--card-bg);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 500;
}

.FC_ai-toggle-button:hover,
.FC_clear-matches-button:hover {
  background: var(--secondary-color);
  border-color: var(--primary-color);
}

.FC_ai-toggle-active {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.FC_ai-toggle-active:hover {
  background: var(--primary-color);
  opacity: 0.9;
}

.FC_clear-matches-button {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.FC_clear-matches-button:hover {
  background: rgba(239, 68, 68, 0.2);
}

/* Analysis Placeholder */
.FC_analysis-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: var(--text-secondary);
  min-height: 400px;
}

.FC_analysis-placeholder i {
  font-size: 3rem;
  margin-bottom: 16px;
  color: var(--primary-color);
  opacity: 0.5;
}

.FC_analysis-placeholder p {
  font-size: 0.95rem;
  line-height: 1.6;
  max-width: 400px;
}

/* Matches Panel */
.FC_matches-panel {
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 0;
  margin-bottom: 0;
  box-shadow: none;
}

.FC_matches-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.FC_matches-header h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.FC_match-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--primary-color);
  color: white;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.FC_matches-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.FC_match-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--secondary-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.FC_match-item:hover {
  border-color: var(--primary-color);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.FC_match-rank {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--primary-color);
  color: white;
  border-radius: 50%;
  font-weight: 700;
  font-size: 0.875rem;
  flex-shrink: 0;
}

.FC_match-info {
  flex: 1;
  min-width: 0;
}

.FC_match-type-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary-color);
  border-radius: 4px;
  font-size: 0.625rem;
  font-weight: 600;
  margin-bottom: 4px;
}

.FC_match-path {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin: 0;
  word-wrap: break-word;
}

.FC_match-score {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 120px;
}

.FC_score-bar {
  flex: 1;
  height: 8px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.FC_score-fill {
  height: 100%;
  background: linear-gradient(90deg, #22c55e 0%, var(--primary-color) 50%, #f59e0b 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.FC_score-text {
  font-weight: 600;
  color: var(--primary-color);
  font-size: 0.875rem;
  min-width: 45px;
  text-align: right;
}

/* Highlighting Styles */
.FC_highlighted {
  border: 2px solid var(--primary-color) !important;
  background: rgba(59, 130, 246, 0.05);
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.2);
}

.FC_match-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--primary-color);
  color: white;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-right: 8px;
  flex-shrink: 0;
}

.FC_match-indicator-small {
  font-size: 0.625rem;
  padding: 2px 6px;
  position: absolute;
  top: 8px;
  right: 8px;
}

/* Target Control Styles */
.FC_clickable-control {
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease;
}

.FC_clickable-control:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.FC_selected-control {
  border: 2px solid #22c55e !important;
  background: rgba(34, 197, 94, 0.05);
}

.FC_find-match-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
  margin-right: 8px;
}

.FC_find-match-button:hover:not(:disabled) {
  background: var(--primary-color);
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.FC_find-match-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .FC_matches-panel {
    padding: 16px;
  }
  
  .FC_matches-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .FC_match-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .FC_match-score {
    width: 100%;
  }
  
  .FC_compliance-summary {
    flex-direction: column;
    gap: 12px;
  }
}

/* Compliance Matching Styles */
.FC_match-compliances-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: #22c55e;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 500;
}

.FC_match-compliances-button:hover:not(:disabled) {
  background: #16a34a;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3);
}

.FC_match-compliances-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.FC_compliance-matches-panel {
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 0;
  margin-bottom: 0;
}

.FC_compliance-summary {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: var(--secondary-color);
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid var(--border-color);
}

.FC_summary-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.FC_summary-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.FC_summary-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.FC_summary-matched .FC_summary-value {
  color: #22c55e;
}

.FC_summary-unmatched .FC_summary-value {
  color: #ef4444;
}

.FC_compliance-section {
  margin-bottom: 24px;
}

.FC_section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border-color);
}

.FC_matched-title {
  color: #22c55e;
  border-bottom-color: #22c55e;
}

.FC_unmatched-title {
  color: #ef4444;
  border-bottom-color: #ef4444;
}

.FC_compliance-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.FC_compliance-match-item {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  background: var(--card-bg);
  transition: all 0.2s ease;
}

.FC_expandable-item {
  cursor: pointer;
}

.FC_expandable-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-color: var(--primary-color);
}

.FC_expanded {
  border-color: var(--primary-color);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}

.FC_matched-item {
  border-left: 4px solid #22c55e;
}

.FC_unmatched-item {
  border-left: 4px solid #ef4444;
}

.FC_compliance-match-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.FC_match-status-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
}

.FC_match-success {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.FC_match-warning {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.FC_compliance-match-info {
  flex: 1;
  min-width: 0;
}

.FC_add-compliance-button {
  border: none;
  background: rgba(34, 197, 94, 0.15);
  color: #16a34a;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.FC_add-compliance-button:hover {
  background: rgba(34, 197, 94, 0.25);
}

.FC_expand-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  color: var(--text-secondary);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.FC_expandable-item:hover .FC_expand-icon {
  color: var(--primary-color);
}

.FC_expanded .FC_expand-icon {
  color: var(--primary-color);
}

.FC_target-compliance-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
  word-wrap: break-word;
}

.FC_target-compliance-desc {
  font-size: 0.875rem;
  color: var(--text-secondary);
  word-wrap: break-word;
  line-height: 1.5;
}

.FC_matched-compliance-details {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.FC_detail-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.FC_detail-section label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.FC_detail-section span {
  font-size: 0.875rem;
  color: var(--text-primary);
  word-wrap: break-word;
  line-height: 1.5;
}

.FC_unmatched-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 6px;
  color: #ef4444;
  font-weight: 500;
  margin-top: 12px;
}

.FC_modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.FC_modal {
  width: 90%;
  max-width: 800px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.FC_modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.FC_modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
}

.FC_modal-close {
  border: none;
  background: transparent;
  font-size: 1.1rem;
  cursor: pointer;
  color: #6b7280;
}

.FC_modal-body {
  padding: 20px;
  overflow-y: auto;
}

.FC_modal-section {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
}

.FC_modal-section h4 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 1rem;
  color: #111827;
}

.FC_modal-field {
  display: flex;
  flex-direction: column;
  margin-bottom: 12px;
}

.FC_modal-field label {
  font-size: 0.85rem;
  margin-bottom: 6px;
  color: #4b5563;
}

.FC_modal-field input,
.FC_modal-field textarea,
.FC_modal-field select {
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.95rem;
  background: #fff;
}

.FC_modal-field textarea {
  min-height: 70px;
  resize: vertical;
}

.FC_modal-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.FC_modal-footer {
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.FC_modal-primary,
.FC_modal-secondary {
  padding: 10px 20px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 600;
}

.FC_modal-secondary {
  background: #f3f4f6;
  color: #374151;
}

.FC_modal-primary {
  background: var(--primary-color);
  color: white;
}

.FC_modal-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.FC_modal-error {
  color: #dc2626;
  font-weight: 500;
  margin-top: 8px;
}

@media (max-width: 640px) {
  .FC_modal {
    width: 95%;
    max-height: 95vh;
  }
}
</style>

