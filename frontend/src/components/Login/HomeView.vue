<template>
  <div class="home-container" :style="homeContainerStyle">
    <main class="main-content">
      <!-- Approved Frameworks Section -->
      <section class="approved-frameworks-section">
        <div class="frameworks-container">
          <div class="frameworks-header" data-aos="fade-right">
            <h3 class="frameworks-title">Select Framework</h3>
          </div>
          <div class="framework-dropdown-wrapper" data-aos="fade-up">
            <select 
              class="framework-dropdown"
              :value="selectedFrameworkId || 'all'"
              @change="handleFrameworkDropdownChange"
            >
              <option value="all">All Frameworks</option>
              <option 
              v-for="framework in approvedFrameworks" 
              :key="framework.FrameworkId"
                :value="framework.FrameworkId"
              >
                {{ framework.FrameworkName }}
              </option>
            </select>
            <div v-if="approvedFrameworks.length === 0" class="no-frameworks">
              <p>No approved frameworks available at this time.</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Hero Section -->
      <section class="hero-section">
        <div class="hero-background">
          <div class="hero-gradient"></div>
          <div class="floating-elements">
            <div class="floating-element" v-for="n in 6" :key="n" :style="getFloatingStyle(n)"></div>
          </div>
        </div>
        
        <div class="hero-content">
          <div class="hero-text" data-aos="fade-up">
            <div class="hero-badge">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                <path d="M9 12l2 2 4-4"/>
              </svg>
              {{ currentFrameworkContent.hero.badge }}
            </div>
            
          <h1 class="hero-title">
            <span class="gradient-text" v-for="(titlePart, index) in currentFrameworkContent.hero.title" :key="index">{{ titlePart }}</span>
          </h1>
          
          <p class="hero-description">
            {{ currentFrameworkContent.hero.description }}
          </p>
            
            <div class="hero-stats">
              <div class="stat-item" v-for="(stat, index) in heroStats" :key="index" data-aos="fade-up" :data-aos-delay="index * 100">
                <div class="stat-number">{{ stat.number }}</div>
                <div class="stat-label">{{ stat.label }}</div>
              </div>
            </div>
          </div>

          <div class="hero-visual" data-aos="fade-left" data-aos-delay="200">
            <div class="dashboard-preview">
              <div class="preview-header">
                <div class="preview-controls">
                  <div class="control red"></div>
                  <div class="control yellow"></div>
                  <div class="control green"></div>
                </div>
                <div class="preview-title">GRC Compliance Dashboard</div>
              </div>
              <div class="preview-content">
                <div class="compliance-overview">
                  <div class="compliance-progress-section">
                    <div class="progress-header">
                      <h3>{{ previewCard.title }}</h3>
                      <div class="progress-percentage">{{ previewCard.percentage }} Complete</div>
                    </div>
                    <div class="progress-bar-container">
                      <div class="progress-bar">
                        <div class="progress-fill" :style="{ width: previewCard.percentage }"></div>
                      </div>
                      <!-- <div class="progress-labels">
                        <span>0%</span>
                        <span>100%</span>
                      </div> -->
                    </div>
                    <div class="compliance-details-grid">
                      <div class="detail-item">
                        <span class="detail-label">Remaining Controls:</span>
                        <span class="detail-value">{{ previewCard.remainingControls }}</span>
                      </div>
                      <div class="detail-item">
                        <span class="detail-label">Next Audit:</span>
                        <span class="detail-value">{{ previewCard.nextAudit }}</span>
                      </div>
                      <div class="detail-item">
                        <span class="detail-label">{{ previewCard.policiesLabel }}:</span>
                        <span class="detail-value">{{ previewCard.policiesValue }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="preview-metrics-grid">
                  <div class="metric-card" v-for="metric in previewMetrics" :key="metric.title">
                    <div class="metric-icon" :class="metric.color">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path v-if="metric.type === 'shield'" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        <path v-if="metric.type === 'check'" d="M9 12l2 2 4-4"/>
                        <path v-if="metric.type === 'alert'" d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                        <path v-if="metric.type === 'document'" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                      </svg>
                    </div>
                    <div class="metric-data">
                      <div class="metric-value">{{ metric.value }}</div>
                      <div class="metric-title">{{ metric.title }}</div>
                      <div class="metric-change" :class="metric.trend">{{ metric.change }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- GRC Compliance Section -->
      <section class="iso-compliance-section">
        <div class="section-header" data-aos="fade-up">
          <!-- <div class="section-badge">GRC Implementation</div> -->
          <h2 class="section-title">{{ currentFrameworkContent.compliance.title }}</h2>
          <p class="section-description">
            {{ currentFrameworkContent.compliance.description }}
          </p>
        </div>
        
        <div class="compliance-overview-grid">
          <div class="compliance-chart" data-aos="fade-up">
            <h3>Overall Compliance Progress</h3>
            <div class="chart-container">
              <Doughnut :key="selectedFrameworkId" :data="overallComplianceData" :options="doughnutOptions" />
            </div>
            
            <!-- Policy Popup -->
            <div v-if="showPolicyPopup" class="popup-backdrop" @click="showPolicyPopup = false">
              <div class="policy-popup" @click.stop>
                <div class="popup-header">
                  <h4>{{ popupData.title }} ({{ popupData.percentage }}%) - {{ popupData.policies?.length || 0 }} Policies</h4>
                  <button class="popup-close" @click="showPolicyPopup = false">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                  </button>
                </div>
                <div class="popup-content">
                  <div v-if="popupData.policies.length === 0" class="no-policies">
                    <p>No policies found in this category.</p>
                  </div>
                  <div v-else class="policies-list">
                    <div v-for="policy in popupData.policies" :key="policy.PolicyId" class="policy-item">
                      <div class="policy-info">
                        <h5 class="policy-name">{{ policy.PolicyName }}</h5>
                        <p class="policy-description">{{ getPolicyDescription(policy.PolicyName) }}</p>
                        <div class="policy-status-badge" :class="policy.Status ? policy.Status.toLowerCase().replace(' ', '-') : ''">
                          {{ policy.Status || 'N/A' }}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="chart-legend">
              <div class="legend-item" @click="showLegendPopup('applied', $event)">
                <div class="legend-color applied"></div>
                <span>Applied ({{ policyData.applied.percentage }}%)</span>
              </div>
              <div class="legend-item" @click="showLegendPopup('in_progress', $event)">
                <div class="legend-color in-progress"></div>
                <span>In Progress ({{ policyData.in_progress.percentage }}%)</span>
              </div>
              <div class="legend-item" @click="showLegendPopup('rejected', $event)">
                <div class="legend-color rejected"></div>
                <span>Rejected ({{ policyData.rejected.percentage }}%)</span>
              </div>
            </div>
          </div>

          <div class="compliance-features" data-aos="fade-up" data-aos-delay="200">
            <h3>Key Implementation Features</h3>
            <div class="features-grid">
              <div class="feature-item" v-for="(feature, index) in implementationFeatures" :key="index">
                <div class="feature-icon" :class="feature.color">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path v-if="feature.type === 'automation'" d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83"/>
                    <path v-if="feature.type === 'monitoring'" d="M3 3v18h18"/>
                    <path v-if="feature.type === 'assessment'" d="M9 12l2 2 4-4"/>
                    <path v-if="feature.type === 'reporting'" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  </svg>
                </div>
                <div class="feature-content">
                  <h4 class="feature-title">{{ feature.title }}</h4>
                  <p class="feature-description">{{ feature.description }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Module Dashboards Section -->
      <section class="module-dashboards-section">
        <div class="section-header" data-aos="fade-up">
          <h2 class="section-title">Module Dashboards</h2>
          <p class="section-description">
            Get a quick overview of all your GRC modules performance and key metrics at a glance.
          </p>
        </div>

        <div class="dashboard-cards-grid">
          <!-- Policy Dashboard Card -->
          <div class="dashboard-card" data-aos="fade-up" data-aos-delay="100">
            <div class="dashboard-card-header">
              <div class="dashboard-icon policy">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14,2 14,8 20,8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10,9 9,9 8,9"/>
                </svg>
              </div>
              <div class="dashboard-info">
                <h3 class="dashboard-title">Policy Management</h3>
                <div class="dashboard-status">
                  <span class="status-indicator active"></span>
                  <span class="status-text">Active</span>
              </div>
              </div>
              </div>
            
            <div class="dashboard-metrics">
              <div class="metric-row">
                <div class="metric-item">
                  <span class="metric-label">Active Policies</span>
                  <span class="metric-value">{{ policyMetrics.activePolicies || 0 }}</span>
            </div>
                <div class="metric-item">
                  <span class="metric-label">Approval Rate</span>
                  <span class="metric-value">{{ policyMetrics.approvalRate || 0 }}%</span>
                </div>
              </div>
              <div class="metric-row">
                <div class="metric-item">
                  <span class="metric-label">Total Policies</span>
                  <span class="metric-value">{{ policyMetrics.totalPolicies || 0 }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Avg. Approval Time</span>
                  <span class="metric-value">{{ policyMetrics.avgApprovalTime || 0 }} days</span>
                </div>
              </div>
            </div>
            
            <div class="dashboard-actions">
              <button class="btn-primary" @click="navigateToModule('PolicyDashboard')">
                View Dashboard
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Compliance Dashboard Card -->
          <div class="dashboard-card" data-aos="fade-up" data-aos-delay="200">
            <div class="dashboard-card-header">
              <div class="dashboard-icon compliance">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                  <path d="M9 12l2 2 4-4"/>
                </svg>
              </div>
              <div class="dashboard-info">
                <h3 class="dashboard-title">Compliance Management</h3>
                <div class="dashboard-status">
                  <span class="status-indicator active"></span>
                  <span class="status-text">Active</span>
                </div>
              </div>
            </div>
            
            <div class="dashboard-metrics">
              <div class="metric-row">
                <div class="metric-item">
                  <span class="metric-label">Active Compliances</span>
                  <span class="metric-value">{{ complianceMetrics.activeCompliances || 0 }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Approval Rate</span>
                  <span class="metric-value">{{ complianceMetrics.approvalRate || 0 }}%</span>
                </div>
              </div>
              <div class="metric-row">
                <div class="metric-item">
                  <span class="metric-label">Total Findings</span>
                  <span class="metric-value">{{ complianceMetrics.totalFindings || 0 }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Under Review</span>
                  <span class="metric-value">{{ complianceMetrics.underReview || 0 }}</span>
                </div>
              </div>
            </div>
            
            <div class="dashboard-actions">
              <button class="btn-primary" @click="navigateToModule('ComplianceDashboard')">
                View Dashboard
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Risk Dashboard Card -->
          <div class="dashboard-card" data-aos="fade-up" data-aos-delay="300">
            <div class="dashboard-card-header">
              <div class="dashboard-icon risk">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
              </div>
              <div class="dashboard-info">
                <h3 class="dashboard-title">Risk Management</h3>
                <div class="dashboard-status">
                  <span class="status-indicator active"></span>
                  <span class="status-text">Active</span>
                </div>
              </div>
            </div>
            
            <div class="dashboard-metrics">
              <div class="metric-row">
                <div class="metric-item">
                  <span class="metric-label">Total Risks</span>
                  <span class="metric-value">{{ riskMetrics.totalRisks || 0 }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Accepted Risks</span>
                  <span class="metric-value">{{ riskMetrics.acceptedRisks || 0 }}</span>
                </div>
              </div>
              <div class="metric-row">
                <div class="metric-item">
                  <span class="metric-label">Mitigated Risks</span>
                  <span class="metric-value">{{ riskMetrics.mitigatedRisks || 0 }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">In Progress</span>
                  <span class="metric-value">{{ riskMetrics.inProgressRisks || 0 }}</span>
                </div>
              </div>
            </div>
            
            <div class="dashboard-actions">
              <button class="btn-primary" @click="navigateToModule('RiskDashboard')">
                View Dashboard
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Incident Dashboard Card -->
          <div class="dashboard-card" data-aos="fade-up" data-aos-delay="400">
            <div class="dashboard-card-header">
              <div class="dashboard-icon incident">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="12"/>
                  <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
              </div>
              <div class="dashboard-info">
                <h3 class="dashboard-title">Incident Management</h3>
                <div class="dashboard-status">
                  <span class="status-indicator active"></span>
                  <span class="status-text">Active</span>
                </div>
              </div>
            </div>
            
            <div class="dashboard-metrics">
              <div class="metric-row">
                <div class="metric-item">
                  <span class="metric-label">Total Incidents</span>
                  <span class="metric-value">{{ incidentMetrics.totalIncidents || 0 }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">MTTD</span>
                  <span class="metric-value">{{ incidentMetrics.mttd || 0 }}h</span>
                </div>
              </div>
              <div class="metric-row">
                <div class="metric-item">
                  <span class="metric-label">MTTR</span>
                  <span class="metric-value">{{ incidentMetrics.mttr || 0 }}h</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Closure Rate</span>
                  <span class="metric-value">{{ incidentMetrics.closureRate || 0 }}%</span>
                </div>
              </div>
            </div>
            
            <div class="dashboard-actions">
              <button class="btn-primary" @click="navigateToModule('IncidentPerformanceDashboard')">
                View Dashboard
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Auditor Dashboard Card -->
          <div class="dashboard-card" data-aos="fade-up" data-aos-delay="500">
            <div class="dashboard-card-header">
              <div class="dashboard-icon auditor">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <div class="dashboard-info">
                <h3 class="dashboard-title">Audit Management</h3>
                <div class="dashboard-status">
                  <span class="status-indicator active"></span>
                  <span class="status-text">Active</span>
                </div>
              </div>
            </div>
            
            <div class="dashboard-metrics">
              <div class="metric-row">
                <div class="metric-item">
                  <span class="metric-label">Completion Rate</span>
                  <span class="metric-value">{{ auditorMetrics.completionRate || 0 }}%</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Total Audits</span>
                  <span class="metric-value">{{ auditorMetrics.totalAudits || 0 }}</span>
                </div>
              </div>
              <div class="metric-row">
                <div class="metric-item">
                  <span class="metric-label">Open Audits</span>
                  <span class="metric-value">{{ auditorMetrics.openAudits || 0 }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Completed</span>
                  <span class="metric-value">{{ auditorMetrics.completedAudits || 0 }}</span>
                </div>
              </div>
            </div>
            
            <div class="dashboard-actions">
              <button class="btn-primary" @click="navigateToModule('AuditorUserDashboard')">
                View Dashboard
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- GRC Control Domains Section -->
      <section class="control-domains-section">
        <div class="section-header" data-aos="fade-up">
          <h2 class="section-title">{{ currentFrameworkContent.frameworkName }} Control Domains</h2>
            <p class="section-description">
            <span v-if="selectedFrameworkId === 'all'">
              Overall compliance percentage across all frameworks.
            </span>
            <span v-else>
            Comprehensive coverage of {{ currentFrameworkContent.frameworkName }} control domains with detailed implementation status and metrics.
            </span>
          </p>
        </div>

        <!-- All Frameworks View: Show Framework Cards -->
        <div v-if="selectedFrameworkId === 'all' && allFrameworksList.length > 0" class="frameworks-cards">
          <div 
            v-for="(framework, index) in allFrameworksList" 
            :key="framework.id"
            class="framework-card"
            :class="{ 'active': false }"
            data-aos="fade-up" 
            :data-aos-delay="index * 50"
            @click="selectFrameworkById(framework.id)"
          >
            <div class="framework-card-content">
              <div class="framework-card-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 12l2 2 4-4"/>
                  <path d="M21 12c-1 0-3-1-3-3s2-3 3-3 3 1 3 3-2 3-3 3"/>
                  <path d="M3 12c1 0 3-1 3-3s-2-3-3-3-3 1-3 3 2 3 3 3"/>
                  <path d="M12 21c0-1-1-3-3-3s-3 2-3 3 1 3 3 3 3-2 3-3"/>
                  <path d="M12 3c0 1-1 3-3 3s-3-2-3-3 1-3 3-3 3 2 3 3"/>
                </svg>
              </div>
              <div class="framework-card-info">
                <h3 class="framework-card-title">{{ framework.name }}</h3>
                <p class="framework-card-description">{{ framework.description || 'No description available' }}</p>
                <div class="framework-card-stats">
                  <div class="framework-card-stats-row">
                    <span class="framework-card-stats-label">Compliance:</span>
                    <span class="framework-card-stats-value compliance">{{ framework.compliancePercentage }}%</span>
                  </div>
                  <div class="framework-card-stats-row">
                    <span class="framework-card-stats-label">Policies:</span>
                    <span class="framework-card-stats-value">{{ framework.stats?.activePolicies || 0 }}</span>
                  </div>
                  <div class="framework-card-stats-row">
                    <span class="framework-card-stats-label">Controls:</span>
                    <span class="framework-card-stats-value">{{ framework.compliantCompliances || 0 }}/{{ framework.totalCompliances || 0 }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- All Frameworks View: Show Percentage Only if no frameworks available -->
        <div v-else-if="selectedFrameworkId === 'all' && allFrameworksCompliancePercentage !== null" class="all-frameworks-compliance">
          <div class="compliance-summary-card">
            <div class="compliance-summary-header">
              <h3 class="compliance-summary-title">Overall Compliance</h3>
            </div>
            <div class="compliance-summary-content">
              <div class="compliance-percentage-large">
                <span class="percentage-value">{{ allFrameworksCompliancePercentage }}%</span>
                <span class="percentage-label">Compliant</span>
              </div>
              <div class="compliance-stats-summary">
                <div class="stat-item">
                  <span class="stat-label">Total Compliances</span>
                  <span class="stat-value">{{ homepageData?.hero?.stats?.totalCompliancesAll || 0 }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Compliant</span>
                  <span class="stat-value">{{ homepageData?.hero?.stats?.compliantCompliances || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Single Framework View: Show Policies as Performance Indicator Cards -->
        <div v-else-if="controlDomainPolicies.length > 0" class="performance-indicator-grid">
          <div class="performance-indicator-card" v-for="(policy, index) in controlDomainPolicies" :key="policy.PolicyId" 
               data-aos="fade-up" :data-aos-delay="index * 50"
               @mouseenter="handleCardHover"
               @mouseleave="handleCardLeave">
            <div class="performance-card-header">
              <h3 class="performance-card-title">{{ policy.PolicyName }}</h3>
              <span class="performance-status-badge" :class="getStatusClass(policy.implementationPercentage)">
                {{ getStatusText(policy.implementationPercentage) }}
              </span>
            </div>
            
            <div class="performance-main-metric">
              <div class="performance-percentage">{{ policy.implementationPercentage || 0 }}%</div>
              <div class="performance-label">CONTROLS IMPLEMENTED</div>
            </div>
            
            <div class="performance-breakdown">
              {{ policy.totalCompliances || 0 }} controls: {{ policy.implementedCompliances || 0 }} implemented, {{ (policy.totalCompliances || 0) - (policy.implementedCompliances || 0) }} remaining
            </div>
          </div>
        </div>

        <!-- Fallback: Show original domains if no policies available -->
        <div v-else class="domains-grid">
          <div class="domain-card" v-for="(domain, index) in esgDomains" :key="index" 
               data-aos="fade-up" :data-aos-delay="index * 100">
            <div class="domain-header">
              <div class="domain-icon" :class="domain.status">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path v-if="domain.status === 'completed'" d="M9 12l2 2 4-4"/>
                  <path v-if="domain.status === 'in-progress'" d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83"/>
                  <path v-if="domain.status === 'pending'" d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83"/>
                  </svg>
            </div>
              <div class="domain-info">
                <h3 class="domain-title">{{ domain.title }}</h3>
                <div class="domain-progress">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: domain.compliance + '%' }"></div>
          </div>
                  <span class="progress-text">{{ domain.compliance }}%</span>
        </div>
            </div>
          </div>
              <div class="domain-details">
              <div class="domain-stats">
                <div class="stat">
                  <span class="stat-label">Controls</span>
                  <span class="stat-value">{{ domain.controls }}</span>
                </div>
                <div class="stat">
                  <span class="stat-label">Implemented</span>
                  <span class="stat-value">{{ domain.implemented }}</span>
                </div>
                <div class="stat">
                  <span class="stat-label">Framework</span>
                  <span class="stat-value">{{ domain.framework }}</span>
                </div>
              </div>
              <div class="domain-description">{{ domain.description }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Basel KPIs - Homepage Insights (Only show for Basel framework) -->
      <section v-if="currentFrameworkContent.kpis.showBaselKPIs" class="basel-home-section">
        <div class="section-header" data-aos="fade-up">
          <h2 class="section-title">Basel KPIs - Strategic Insights</h2>
          <p class="section-description">Live alerts and competitive benchmarking to support capital planning decisions.</p>
        </div>

        <div class="basel-home-grid">
          <!-- S36 Management Action Triggers -->
          <div class="alert-panel" data-aos="fade-up">
            <div class="alert-header">
              <h3>Management Action Triggers</h3>
              <div class="counters">
                <span class="ctr critical">Critical: {{ alertSummary.critical }}</span>
                <span class="ctr high">High: {{ alertSummary.high }}</span>
                <span class="ctr medium">Medium: {{ alertSummary.medium }}</span>
              </div>
            </div>
            <div class="alert-list">
              <div class="alert-item" v-for="(a, i) in alerts" :key="i" :class="a.severity">
                <div class="alert-badge">{{ a.severity.toUpperCase() }}</div>
                <div class="alert-content">
                  <div class="alert-title">{{ a.title }}</div>
                  <div class="alert-desc">{{ a.description }}</div>
                </div>
                <div class="alert-kpi">{{ a.kpi }}</div>
              </div>
            </div>
          </div>

          <!-- S38 Competitive Position vs Capital Efficiency -->
          <div class="benchmark-card" data-aos="fade-up" data-aos-delay="150">
            <h3>Capital Efficiency Benchmark</h3>
            <div class="benchmark-table">
              <div class="bench-row bench-head">
                <span>Peer</span><span>Risk-Adj ROE</span><span>Trend</span>
              </div>
              <div class="bench-row" v-for="(p, i) in peers" :key="i">
                <span>{{ p.name }}</span>
                <span :class="{ up: p.roe > ourPeer.roe, down: p.roe < ourPeer.roe }">{{ p.roe }}%</span>
                <svg viewBox="0 0 80 20" class="spark">
                  <polyline :points="p.spark" fill="none" stroke="#3b82f6" stroke-width="2" />
                </svg>
              </div>
            </div>
          </div>

          <!-- S34 Profitability vs Risk-Adjusted Capital by BU (Bubble) -->
          <div class="bubble-card" data-aos="fade-up" data-aos-delay="300">
            <h3>Profitability vs Risk-Adjusted Capital (BU)</h3>
            <svg viewBox="0 0 300 160" class="bubble-canvas">
              <circle v-for="(b, i) in buBubbles" :key="i" :cx="b.x" :cy="b.y" :r="b.r" :fill="b.color" opacity="0.85" />
            </svg>
            <div class="bubble-legend">
              <span v-for="(b, i) in buBubbles" :key="'b-'+i" class="legend-item"><span class="legend-color-dot" :style="{background: b.color}"></span>{{ b.name }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Additional Risk & Incident KPIs (Only show for Basel framework) -->
      <section v-if="currentFrameworkContent.kpis.showBaselKPIs" class="additional-kpis-section">
        <div class="section-header" data-aos="fade-up">
          <h2 class="section-title">Advanced Risk & Incident Analytics</h2>
          <p class="section-description">Comprehensive risk metrics and operational incident tracking for enhanced decision making.</p>
        </div>

        <div class="additional-kpis-grid">
          <!-- S29 Liquidity Stress Test Results -->
          <div class="kpi-card" data-aos="fade-up">
            <h3>Liquidity Stress Test Results</h3>
            <div class="kpi-metric">
              <div class="metric-value">{{ liquidityStress.current }}%</div>
              <div class="metric-label">Current LCR</div>
            </div>
            <div class="kpi-chart">
              <svg viewBox="0 0 200 60" class="mini-waterfall">
                <rect v-for="(bar, i) in liquidityStress.waterfall" :key="i" 
                      :x="bar.x" :y="bar.y" :width="bar.width" :height="bar.height" 
                      :fill="bar.color" opacity="0.8"/>
              </svg>
            </div>
            <div class="kpi-status" :class="liquidityStress.status">
              {{ liquidityStress.status.toUpperCase() }}
            </div>
          </div>

          <!-- S30 Large Exposure Limits -->
          <div class="kpi-card" data-aos="fade-up" data-aos-delay="100">
            <h3>Large Exposure Limits</h3>
            <div class="kpi-metric">
              <div class="metric-value">{{ largeExposure.topExposure }}%</div>
              <div class="metric-label">Top Exposure (% of Tier1)</div>
            </div>
            <div class="kpi-chart">
              <svg viewBox="0 0 200 60" class="mini-bars">
                <rect v-for="(bar, i) in largeExposure.bars" :key="i" 
                      :x="bar.x" :y="bar.y" :width="bar.width" :height="bar.height" 
                      :fill="bar.color" opacity="0.8"/>
              </svg>
            </div>
            <div class="kpi-status" :class="largeExposure.status">
              {{ largeExposure.status.toUpperCase() }}
            </div>
          </div>

          <!-- S31 Funding Concentration Risk -->
          <div class="kpi-card" data-aos="fade-up" data-aos-delay="200">
            <h3>Funding Concentration Risk</h3>
            <div class="kpi-metric">
              <div class="metric-value">{{ fundingConcentration.top3 }}%</div>
              <div class="metric-label">Top 3 Counterparties</div>
            </div>
            <div class="kpi-chart">
              <div class="mini-heatmap">
                <div v-for="(item, i) in fundingConcentration.heatmap" :key="i" 
                     class="heatmap-cell" :style="{backgroundColor: item.color}">
                  <span class="heatmap-label">{{ item.name }}</span>
                  <span class="heatmap-value">{{ item.value }}%</span>
                </div>
              </div>
            </div>
            <div class="kpi-status" :class="fundingConcentration.status">
              {{ fundingConcentration.status.toUpperCase() }}
            </div>
          </div>

          <!-- S32 Recovery Plan Viability -->
          <div class="kpi-card" data-aos="fade-up" data-aos-delay="300">
            <h3>Recovery Plan Viability</h3>
            <div class="kpi-metric">
              <div class="metric-value">{{ recoveryPlan.score }}/100</div>
              <div class="metric-label">Viability Score</div>
            </div>
            <div class="kpi-chart">
              <svg viewBox="0 0 200 60" class="mini-radar">
                <polygon :points="recoveryPlan.radarPoints" fill="rgba(59, 130, 246, 0.3)" stroke="#3b82f6" stroke-width="2"/>
                <circle v-for="(point, i) in recoveryPlan.radarPoints.split(' ')" :key="i" 
                        :cx="point.split(',')[0]" :cy="point.split(',')[1]" r="3" fill="#3b82f6"/>
              </svg>
            </div>
            <div class="kpi-status" :class="recoveryPlan.status">
              {{ recoveryPlan.status.toUpperCase() }}
            </div>
          </div>

          <!-- S33 Capital Planning Forecast Accuracy -->
          <div class="kpi-card" data-aos="fade-up" data-aos-delay="400">
            <h3>Capital Planning Forecast Accuracy</h3>
            <div class="kpi-metric">
              <div class="metric-value">{{ forecastAccuracy.mape }}%</div>
              <div class="metric-label">MAPE</div>
            </div>
            <div class="kpi-chart">
              <svg viewBox="0 0 200 60" class="mini-scatter">
                <circle v-for="(point, i) in forecastAccuracy.points" :key="i" 
                        :cx="point.x" :cy="point.y" r="2" fill="#10b981" opacity="0.7"/>
                <line x1="0" y1="60" x2="200" y2="0" stroke="#ef4444" stroke-width="1" stroke-dasharray="2,2"/>
              </svg>
            </div>
            <div class="kpi-status" :class="forecastAccuracy.status">
              {{ forecastAccuracy.status.toUpperCase() }}
            </div>
          </div>

          <!-- S39 Capital Shortfall under Stress -->
          <div class="kpi-card" data-aos="fade-up" data-aos-delay="500">
            <h3>Capital Shortfall under Stress</h3>
            <div class="kpi-metric">
              <div class="metric-value">{{ capitalShortfall.amount }}M</div>
              <div class="metric-label">Shortfall Amount</div>
            </div>
            <div class="kpi-chart">
              <svg viewBox="0 0 200 60" class="mini-waterfall">
                <rect v-for="(bar, i) in capitalShortfall.waterfall" :key="i" 
                      :x="bar.x" :y="bar.y" :width="bar.width" :height="bar.height" 
                      :fill="bar.color" opacity="0.8"/>
              </svg>
            </div>
            <div class="kpi-status" :class="capitalShortfall.status">
              {{ capitalShortfall.status.toUpperCase() }}
            </div>
          </div>

          <!-- S40 Top 10 Counterparty Exposures -->
          <div class="kpi-card" data-aos="fade-up" data-aos-delay="600">
            <h3>Top Counterparty Exposures</h3>
            <div class="kpi-metric">
              <div class="metric-value">{{ counterpartyExposures.topCount }}</div>
              <div class="metric-label">Exposures > 5% of Tier1</div>
            </div>
            <div class="kpi-chart">
              <svg viewBox="0 0 200 60" class="mini-bars">
                <rect v-for="(bar, i) in counterpartyExposures.bars" :key="i" 
                      :x="bar.x" :y="bar.y" :width="bar.width" :height="bar.height" 
                      :fill="bar.color" opacity="0.8"/>
              </svg>
            </div>
            <div class="kpi-status" :class="counterpartyExposures.status">
              {{ counterpartyExposures.status.toUpperCase() }}
            </div>
          </div>

          <!-- S21 Operational Risk Losses -->
          <div class="kpi-card" data-aos="fade-up" data-aos-delay="700">
            <h3>Operational Risk Losses</h3>
            <div class="kpi-metric">
              <div class="metric-value">{{ opRiskLosses.total }}K</div>
              <div class="metric-label">Total Losses (6M)</div>
            </div>
            <div class="kpi-chart">
              <svg viewBox="0 0 200 60" class="mini-bars">
                <rect v-for="(bar, i) in opRiskLosses.bars" :key="i" 
                      :x="bar.x" :y="bar.y" :width="bar.width" :height="bar.height" 
                      :fill="bar.color" opacity="0.8"/>
              </svg>
            </div>
            <div class="kpi-status" :class="opRiskLosses.status">
              {{ opRiskLosses.status.toUpperCase() }}
            </div>
          </div>

          <!-- S37 Basel-related Incidents -->
          <div class="kpi-card" data-aos="fade-up" data-aos-delay="800">
            <h3>Basel-related Incidents</h3>
            <div class="kpi-metric">
              <div class="metric-value">{{ baselIncidents.total }}</div>
              <div class="metric-label">Total Incidents (12M)</div>
            </div>
            <div class="kpi-chart">
              <svg viewBox="0 0 200 60" class="mini-trend">
                <path :d="baselIncidents.trendPath" stroke="#ef4444" stroke-width="2" fill="none"/>
                <circle v-for="(point, i) in baselIncidents.points" :key="i" 
                        :cx="point.x" :cy="point.y" r="2" fill="#ef4444"/>
              </svg>
            </div>
            <div class="kpi-status" :class="baselIncidents.status">
              {{ baselIncidents.status.toUpperCase() }}
            </div>
          </div>

          <!-- S22 Control Effectiveness Score -->
          <div class="kpi-card" data-aos="fade-up" data-aos-delay="900">
            <h3>Control Effectiveness Score</h3>
            <div class="kpi-metric">
              <div class="metric-value">{{ controlEffectiveness.score }}%</div>
              <div class="metric-label">Basel Controls</div>
            </div>
            <div class="kpi-chart">
              <svg viewBox="0 0 200 60" class="mini-radar">
                <polygon :points="controlEffectiveness.radarPoints" fill="rgba(16, 185, 129, 0.3)" stroke="#10b981" stroke-width="2"/>
                <circle v-for="(point, i) in controlEffectiveness.radarPoints.split(' ')" :key="i" 
                        :cx="point.split(',')[0]" :cy="point.split(',')[1]" r="3" fill="#10b981"/>
              </svg>
            </div>
            <div class="kpi-status" :class="controlEffectiveness.status">
              {{ controlEffectiveness.status.toUpperCase() }}
            </div>
          </div>

          <!-- S23 Basel Control Coverage -->
          <div class="kpi-card" data-aos="fade-up" data-aos-delay="1000">
            <h3>Basel Control Coverage</h3>
            <div class="kpi-metric">
              <div class="metric-value">{{ controlCoverage.percentage }}%</div>
              <div class="metric-label">Requirements Covered</div>
            </div>
            <div class="kpi-chart">
              <svg viewBox="0 0 200 60" class="mini-donut">
                <circle cx="100" cy="30" r="20" fill="none" stroke="#e5e7eb" stroke-width="8"/>
                <circle cx="100" cy="30" r="20" fill="none" stroke="#3b82f6" stroke-width="8" 
                        :stroke-dasharray="controlCoverage.dashArray" stroke-dashoffset="0" 
                        transform="rotate(-90 100 30)"/>
              </svg>
            </div>
            <div class="kpi-status" :class="controlCoverage.status">
              {{ controlCoverage.status.toUpperCase() }}
            </div>
          </div>

          <!-- S24 Open Basel Audit Findings -->
          <div class="kpi-card" data-aos="fade-up" data-aos-delay="1100">
            <h3>Open Basel Audit Findings</h3>
            <div class="kpi-metric">
              <div class="metric-value">{{ auditFindings.open }}</div>
              <div class="metric-label">Open Findings</div>
            </div>
            <div class="kpi-chart">
              <svg viewBox="0 0 200 60" class="mini-bars">
                <rect v-for="(bar, i) in auditFindings.bars" :key="i" 
                      :x="bar.x" :y="bar.y" :width="bar.width" :height="bar.height" 
                      :fill="bar.color" opacity="0.8"/>
              </svg>
            </div>
            <div class="kpi-status" :class="auditFindings.status">
              {{ auditFindings.status.toUpperCase() }}
            </div>
          </div>

          <!-- S26 Policy Attestation Rate -->
          <div class="kpi-card" data-aos="fade-up" data-aos-delay="1200">
            <h3>Policy Attestation Rate</h3>
            <div class="kpi-metric">
              <div class="metric-value">{{ policyAttestation.rate }}%</div>
              <div class="metric-label">Basel Policies</div>
            </div>
            <div class="kpi-chart">
              <svg viewBox="0 0 200 60" class="mini-gauge">
                <circle cx="100" cy="30" r="20" fill="none" stroke="#e5e7eb" stroke-width="8"/>
                <circle cx="100" cy="30" r="20" fill="none" stroke="#10b981" stroke-width="8" 
                        :stroke-dasharray="policyAttestation.dashArray" stroke-dashoffset="0" 
                        transform="rotate(-90 100 30)"/>
              </svg>
            </div>
            <div class="kpi-status" :class="policyAttestation.status">
              {{ policyAttestation.status.toUpperCase() }}
            </div>
          </div>

          <!-- S27 Basel Policy Coverage -->
          <div class="kpi-card" data-aos="fade-up" data-aos-delay="1300">
            <h3>Basel Policy Coverage</h3>
            <div class="kpi-metric">
              <div class="metric-value">{{ policyCoverage.implemented }}/{{ policyCoverage.required }}</div>
              <div class="metric-label">Implemented vs Required</div>
            </div>
            <div class="kpi-chart">
              <svg viewBox="0 0 200 60" class="mini-stacked">
                <rect x="20" y="20" width="160" height="20" fill="#e5e7eb" rx="4"/>
                <rect x="20" y="20" :width="policyCoverage.implementedWidth" height="20" fill="#10b981" rx="4"/>
                <rect x="20" y="40" width="160" height="10" fill="#f59e0b" rx="2"/>
              </svg>
            </div>
            <div class="kpi-status" :class="policyCoverage.status">
              {{ policyCoverage.status.toUpperCase() }}
            </div>
          </div>

          <!-- S35 Pillar 3 Regulatory Disclosure Completeness -->
          <div class="kpi-card" data-aos="fade-up" data-aos-delay="1400">
            <h3>Pillar 3 Disclosure Completeness</h3>
            <div class="kpi-metric">
              <div class="metric-value">{{ pillar3Disclosure.completeness }}%</div>
              <div class="metric-label">Regulatory Disclosure</div>
            </div>
            <div class="kpi-chart">
              <svg viewBox="0 0 200 60" class="mini-gauge">
                <circle cx="100" cy="30" r="20" fill="none" stroke="#e5e7eb" stroke-width="8"/>
                <circle cx="100" cy="30" r="20" fill="none" stroke="#3b82f6" stroke-width="8" 
                        :stroke-dasharray="pillar3Disclosure.dashArray" stroke-dashoffset="0" 
                        transform="rotate(-90 100 30)"/>
              </svg>
            </div>
            <div class="kpi-status" :class="pillar3Disclosure.status">
              {{ pillar3Disclosure.status.toUpperCase() }}
            </div>
          </div>
        </div>
      </section>

      <!-- Framework-Specific KPIs (For non-Basel frameworks) -->
      <section v-if="currentFrameworkContent.kpis.showKPIs && !currentFrameworkContent.kpis.showBaselKPIs" class="framework-kpis-section">
        <div class="section-header" data-aos="fade-up">
          <h2 class="section-title">{{ currentFrameworkContent.frameworkName }} Key Performance Indicators</h2>
          <p class="section-description">Real-time metrics and performance indicators for {{ currentFrameworkContent.frameworkName }} compliance monitoring.</p>
        </div>

        <div class="kpis-grid">
          <div class="kpi-card" v-for="(kpi, index) in currentFrameworkContent.kpis.kpiSections" :key="index" data-aos="fade-up" :data-aos-delay="index * 50">
            <div class="kpi-header">
              <h3>{{ kpi.title }}</h3>
              <div class="kpi-status-badge" :class="kpi.status">
                {{ kpi.status.toUpperCase() }}
              </div>
            </div>
            <div class="kpi-value-section">
              <div class="kpi-main-value">{{ kpi.value }}</div>
              <div class="kpi-label">{{ kpi.label }}</div>
            </div>
            <div class="kpi-description">{{ kpi.description }}</div>
            <div class="kpi-trend-section">
              <div class="kpi-trend" :class="kpi.trend">
                <svg v-if="kpi.trend === 'up'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 15l-6-6-6 6"/>
                </svg>
                <svg v-if="kpi.trend === 'down'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M6 9l6 6 6-6"/>
                </svg>
                <svg v-if="kpi.trend === 'stable'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14"/>
                </svg>
                <span>{{ kpi.change }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Benefits Section -->
      <section class="benefits-section">
        <div class="section-header" data-aos="fade-up">
          <h2 class="section-title">Why Choose Our GRC Platform?</h2>
          <p class="section-description">
            Experience the advantages of our comprehensive GRC compliance solution.
          </p>
        </div>

        <div class="benefits-grid">
          <div class="benefit-card" v-for="(benefit, index) in benefits" :key="index" 
               data-aos="fade-up" :data-aos-delay="index * 100">
            <div class="benefit-icon" :class="benefit.color">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path v-if="benefit.type === 'clock'" d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83"/>
                <path v-if="benefit.type === 'shield'" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path v-if="benefit.type === 'chart'" d="M3 3v18h18"/>
                <path v-if="benefit.type === 'users'" d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle v-if="benefit.type === 'users'" cx="9" cy="7" r="4"/>
                <path v-if="benefit.type === 'users'" d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path v-if="benefit.type === 'users'" d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
              </div>
            <h3 class="benefit-title">{{ benefit.title }}</h3>
            <p class="benefit-description">{{ benefit.description }}</p>
          </div>
        </div>
      </section>

      <!-- CTA Section -->
      <section class="cta-section">
        <div class="cta-background">
          <div class="cta-gradient"></div>
        </div>
        <div class="cta-content" data-aos="fade-up">
          <h2 class="cta-title">{{ currentFrameworkContent.cta.title }}</h2>
          <p class="cta-description">
            {{ currentFrameworkContent.cta.description }}
          </p>
                     <div class="cta-actions">
             <button class="cta-primary" @click="navigateToCompliance">
              {{ currentFrameworkContent.cta.primaryButton }}
               <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                 <path d="M5 12h14M12 5l7 7-7 7"/>
               </svg>
             </button>
             <button class="cta-secondary" @click="navigateToCompliance">
              {{ currentFrameworkContent.cta.secondaryButton }}
             </button>
           </div>
        </div>
      </section>

      <!-- Footer Section -->
      <footer class="footer-section">
        <div class="footer-background">
          <div class="footer-gradient"></div>
        </div>
        <div class="footer-content">
          <!-- Main Footer -->
          <div class="footer-main" data-aos="fade-up">
            <div class="footer-brand">
              <div class="footer-logo">
                <div class="logo-circle">
                  <img src="../../assets/RiskaVaire.png" alt="RiskaVaire Logo" class="logo-image" />
                </div>
              </div>
              <p class="footer-description">
                Leading Financial Risk Management platform with {{ currentFrameworkContent.frameworkName }} compliance. 
                Drive regulatory alignment and risk management excellence with our comprehensive {{ currentFrameworkContent.frameworkName }} suite.
              </p>
            </div>

            <div class="footer-links">
              <div class="footer-column">
                <h4>{{ currentFrameworkContent.frameworkName }} Framework</h4>
                <ul>
                  <li v-for="domain in currentFrameworkContent.domains.slice(0, 5)" :key="domain.title">
                    <a href="#" @click="navigateToCompliance">{{ domain.title }}</a>
                  </li>
                </ul>
              </div>

              <div class="footer-column">
                <h4>Platform</h4>
                <ul>
                  <li v-for="feature in platformFeatures" :key="feature">
                    <a href="#" @click="navigateToCompliance">{{ feature }}</a>
                  </li>
                </ul>
              </div>

              <div class="footer-column">
                <h4>Resources</h4>
                <ul>
                  <li v-for="resource in resourceFeatures" :key="resource">
                    <a href="#" @click="navigateToCompliance">{{ resource }}</a>
                  </li>
                </ul>
              </div>

              <div class="footer-column">
                <h4>Company</h4>
                <ul>
                  <li><a href="#" @click="navigateToCompliance">About Us</a></li>
                  <li><a href="#" @click="navigateToCompliance">Careers</a></li>
                  <li><a href="#" @click="navigateToCompliance">Contact</a></li>
                  <li><a href="#" @click="navigateToCompliance">Privacy Policy</a></li>
                  <li><a href="#" @click="navigateToCompliance">Terms of Service</a></li>
                </ul>
              </div>
            </div>

            <div class="footer-contact">
              <div class="contact-header">
                <h4>CONTACT US</h4>
              </div>
              <div class="contact-info">
                <div class="contact-item">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="2"/>
                    <polyline points="22,6 12,13 2,6" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  <a href="mailto:info@vardaanglobal.com" class="contact-link">info@vardaanglobal.com</a>
                </div>
                <div class="contact-item">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l1.72 1.71" stroke="currentColor" stroke-width="2"/>
                    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  <a href="https://vardaanglobal.com/grc" target="_blank" rel="noopener noreferrer" class="contact-link">vardaanglobal.com/grc</a>
                </div>
              </div>
            </div>
          </div>

          <!-- Footer Bottom -->
          <div class="footer-bottom" data-aos="fade-up" data-aos-delay="200">
            <div class="footer-bottom-content">
              <div class="footer-copyright">
                <p>&copy; {{ new Date().getFullYear() }} RiskaVaire. All rights reserved.</p>
              </div>
              <div class="footer-certifications">
                <div class="certification-badge">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                    <path d="m9 12 2 2 4-4"/>
                  </svg>
                  <span>{{ currentFrameworkContent.frameworkName }} Compliant</span>
                </div>
                <div class="certification-badge">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                    <path d="m9 12 2 2 4-4"/>
                  </svg>
                  <span>{{ currentFrameworkContent.frameworkName }} Certified</span>
                </div>
                <div class="certification-badge">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                    <path d="m9 12 2 2 4-4"/>
                  </svg>
                  <span>Risk Management Certified</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { Doughnut } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, PointElement, LineElement, ArcElement } from 'chart.js';
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';
import AOS from 'aos';
import 'aos/dist/aos.css';
import dashboardService from '@/services/dashboardService';
import { complianceService, incidentService } from '@/services/api';
import homepageDataService from '@/services/homepageService'; // NEW: Centralized homepage data service (updated to class-based)
import incidentDataService from '@/services/incidentService'; // NEW: Centralized incident data service
import riskDataService from '@/services/riskService'; // NEW: Centralized risk data service
import complianceDataService from '@/services/complianceService'; // NEW: Centralized compliance data service
import auditorDataService from '@/services/auditorService'; // NEW: Centralized auditor data service
import eventDataService from '@/services/eventService'; // NEW: Centralized event data service
import policyDataService from '@/services/policyService'; // NEW: Centralized policy data service
import treeDataService from '@/services/treeService'; // NEW: Centralized tree data service
import documentDataService from '@/services/documentService'; // NEW: Centralized document data service
import integrationsDataService from '@/services/integrationsService'; // NEW: Centralized integrations data service
import axios from 'axios';
import { API_ENDPOINTS } from '@/config/api.js';
import { getFrameworkContent } from '@/config/frameworkContent.js';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, PointElement, LineElement, ArcElement);

const router = useRouter();
const store = useStore();
const user = ref(null);

const SIDEBAR_OFFSET = 240;
const SIDEBAR_OFFSET_ALL = 200;
const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1440);

const isAllFrameworksSelected = computed(() => {
  return !selectedFrameworkId.value || selectedFrameworkId.value === 'all';
});

const homeContainerStyle = computed(() => {
  if (windowWidth.value <= 1024) {
    return {
      marginLeft: '0px',
      width: '100%',
      maxWidth: '100vw',
      paddingLeft: '1.5rem',
      paddingRight: '1.5rem'
    };
  }

  const offset = isAllFrameworksSelected.value ? SIDEBAR_OFFSET_ALL : SIDEBAR_OFFSET;

  return {
    marginLeft: `${offset}px`,
    width: `calc(100% - ${offset}px)`,
    maxWidth: `calc(100vw - ${offset}px)`,
    paddingLeft: '1.5rem',
    paddingRight: isAllFrameworksSelected.value ? '0rem' : '1.5rem'
  };
});

const handleResize = () => {
  if (typeof window !== 'undefined') {
    windowWidth.value = window.innerWidth;
  }
};

// Approved Frameworks
const approvedFrameworks = ref([]);
const selectedFrameworkId = ref(null);

// Homepage data from API
const homepageData = ref(null);
// Cached incidents data and summary
const incidentsData = ref([]);
const incidentCount = ref(0);

// Cached risks data and summary
const risksData = ref([]);
const riskCount = ref(0);
// Current framework content (computed based on selected framework)
const currentFrameworkContent = computed(() => {
  console.log('🔄 currentFrameworkContent computed - selectedFrameworkId:', selectedFrameworkId.value);
  
  // Get the selected framework object to access the name
  const selectedFramework = approvedFrameworks.value.find(f => f.FrameworkId === selectedFrameworkId.value);
  const frameworkName = selectedFramework?.FrameworkName || selectedFrameworkId.value;
  
  console.log('📝 Using framework name for content lookup:', frameworkName);
  return getFrameworkContent(frameworkName);
});

// Hero statistics - Always use dynamic API data, never fallback to static
const heroStats = computed(() => {
  // Only use dynamic homepage data - no fallback to static content
  if (!homepageData.value?.hero?.stats) {
    // Return empty array if no data available yet (will show loading/empty state)
    return [];
  }
  
  const stats = homepageData.value.hero.stats;
  
  // Handle "All Frameworks" case
  if (selectedFrameworkId.value === 'all') {
    // Calculate overall compliance percentage
    const totalCompliances = stats.totalCompliancesAll || stats.totalCompliances || 0;
    const compliantCompliances = stats.compliantCompliances || 0;
    const compliancePercentage = totalCompliances > 0 
      ? Math.round((compliantCompliances / totalCompliances) * 100) 
      : 0;
    
    // Get aggregated counts
    const policiesCount = stats.totalPoliciesAll || stats.totalPolicies || stats.activePolicies || 0;
    const controlsCount = stats.totalCompliancesAll || stats.totalCompliances || 0;
    
    return [
      { 
        number: `${compliancePercentage}%`, 
        label: 'Average Compliance' 
      },
      { 
        number: `${policiesCount}`, 
        label: 'Total Policies' 
      },
      { 
        number: `${controlsCount}`, 
        label: 'Total Controls' 
      }
    ];
  }
  
  // Handle specific framework case (or null/undefined selectedFrameworkId - use dynamic data anyway)
  const frameworkName = currentFrameworkContent.value?.frameworkName || 'Framework';
  
  // Calculate compliance percentage
  const totalCompliances = stats.totalCompliancesAll || stats.totalCompliances || 0;
  const compliantCompliances = stats.compliantCompliances || 0;
  const compliancePercentage = totalCompliances > 0 
    ? Math.round((compliantCompliances / totalCompliances) * 100) 
    : 0;
  
  // Get policies count (prefer activePolicies, fallback to totalPoliciesAll)
  const policiesCount = stats.activePolicies || stats.totalPoliciesAll || stats.totalPolicies || 0;
  
  // Get controls count
  const controlsCount = stats.totalCompliancesAll || stats.totalCompliances || 0;
  
  // Build dynamic stats array
  return [
    { 
      number: `${compliancePercentage}%`, 
      label: `${frameworkName} Compliance` 
    },
    { 
      number: `${policiesCount}`, 
      label: 'Security Policies' 
    },
    { 
      number: `${controlsCount}`, 
      label: 'Security Controls' 
    }
  ];
});

// Preview card data - Always use dynamic API data, never fallback to static
const previewCard = computed(() => {
  // Only use dynamic homepage data - no fallback to static content
  if (!homepageData.value?.hero?.previewMetrics) {
    // Return empty/default values if no data available yet
    const frameworkName = currentFrameworkContent.value?.frameworkName || 'Framework';
    return {
      title: `${frameworkName} Implementation Progress`,
      percentage: '0%',
      remainingControls: '0%',
      nextAudit: 'TBD',
      policiesLabel: 'Security Policies',
      policiesValue: '0 Total'
    };
  }
  
  const previewMetricsData = homepageData.value.hero.previewMetrics;
  const stats = homepageData.value.hero.stats;
  const frameworkName = currentFrameworkContent.value?.frameworkName || 'Framework';
  
  // Use compliance percentage from previewMetrics if available, otherwise calculate from stats
  const compliancePercentage = previewMetricsData.compliancePercentage !== undefined
    ? Math.round(previewMetricsData.compliancePercentage)
    : (() => {
        const totalCompliances = stats.totalCompliancesAll || stats.totalCompliances || 0;
        const compliantCompliances = stats.compliantCompliances || 0;
        return totalCompliances > 0 
          ? Math.round((compliantCompliances / totalCompliances) * 100) 
          : 0;
      })();
  
  // Calculate remaining controls percentage
  // Backend returns remainingControls as count, so calculate percentage
  const totalCompliances = stats.totalCompliancesAll || stats.totalCompliances || 0;
  const remainingControlsCount = previewMetricsData.remainingControls !== undefined
    ? previewMetricsData.remainingControls
    : (totalCompliances - (stats.compliantCompliances || 0));
  const remainingControlsPercentage = totalCompliances > 0 
    ? Math.round((remainingControlsCount / totalCompliances) * 100) 
    : 0;
  
  // Format next audit date
  let nextAuditDisplay = 'TBD';
  if (previewMetricsData.nextAudit) {
    try {
      const auditDate = new Date(previewMetricsData.nextAudit);
      const options = { year: 'numeric', month: 'short', day: 'numeric' };
      nextAuditDisplay = auditDate.toLocaleDateString('en-US', options);
    } catch (e) {
      nextAuditDisplay = previewMetricsData.nextAudit;
    }
  }
  
  // Get policies count from previewMetrics or stats
  const policiesCount = previewMetricsData.policiesValue !== undefined
    ? previewMetricsData.policiesValue
    : (stats.activePolicies || stats.totalPoliciesAll || stats.totalPolicies || 0);
  
  return {
    title: `${frameworkName} Implementation Progress`,
    percentage: `${compliancePercentage}%`,
    remainingControls: `${remainingControlsPercentage}% (${frameworkName})`,
    nextAudit: nextAuditDisplay,
    policiesLabel: 'Security Policies',
    policiesValue: `${policiesCount} Total`
  };
});

// Preview metrics for hero visual - Always use dynamic API data
const previewMetrics = computed(() => {
  // Only use dynamic homepage data - no fallback to static content
  if (!homepageData.value?.hero?.previewMetrics || !homepageData.value?.hero?.stats) {
    // Return empty array if no data available yet
    return [];
  }
  
  const stats = homepageData.value.hero.stats;
  
  // Calculate compliance percentage
  const totalCompliances = stats.totalCompliancesAll || stats.totalCompliances || 0;
  const compliantCompliances = stats.compliantCompliances || 0;
  const compliancePercentage = totalCompliances > 0 
    ? Math.round((compliantCompliances / totalCompliances) * 100) 
    : 0;
  
  // Get active policies count
  const activePolicies = stats.activePolicies || stats.totalPoliciesAll || stats.totalPolicies || 0;
  
  // Calculate risk coverage (mitigated risks / total risks)
  const totalRisks = stats.totalRisks || 0;
  const mitigatedRisks = stats.mitigatedRisks || 0;
  const riskCoveragePercentage = totalRisks > 0 
    ? Math.round((mitigatedRisks / totalRisks) * 100) 
    : 0;
  
  // Build dynamic metrics array
  return [
    {
      title: 'Overall Compliance',
      value: `${compliancePercentage}%`,
      change: '+0%', // Could be calculated from historical data if available
      trend: 'positive',
      color: 'green',
      type: 'shield'
    },
    {
      title: 'Active Policies',
      value: `${activePolicies}`,
      change: '+0', // Could be calculated from historical data if available
      trend: 'positive',
      color: 'blue',
      type: 'check'
    },
    {
      title: 'Risk Coverage',
      value: `${riskCoveragePercentage}%`,
      change: '+0%', // Could be calculated from historical data if available
      trend: 'positive',
      color: 'orange',
      type: 'alert'
    }
  ];
});

// Control Domains (now computed from framework content)
const esgDomains = computed(() => {
  return currentFrameworkContent.value?.domains || [];
});

// Helper functions for performance indicator cards
const getStatusClass = (percentage) => {
  if (percentage === 100) return 'status-pass';
  if (percentage > 0) return 'status-in-progress';
  return 'status-pending';
};

const getStatusText = (percentage) => {
  if (percentage === 100) return 'PASS';
  if (percentage > 0) return 'IN PROGRESS';
  return 'PENDING';
};

// Handle card hover to ensure icon stays visible
const handleCardHover = (event) => {
  const card = event.currentTarget;
  const icon = card.querySelector('.performance-card-icon');
  if (icon) {
    icon.style.opacity = '1';
    icon.style.visibility = 'visible';
    icon.style.display = 'flex';
    const svg = icon.querySelector('svg');
    if (svg) {
      svg.style.opacity = '1';
      svg.style.visibility = 'visible';
      svg.style.display = 'block';
    }
  }
};

const handleCardLeave = (event) => {
  const card = event.currentTarget;
  const icon = card.querySelector('.performance-card-icon');
  if (icon) {
    icon.style.opacity = '1';
    icon.style.visibility = 'visible';
    icon.style.display = 'flex';
    const svg = icon.querySelector('svg');
    if (svg) {
      svg.style.opacity = '1';
      svg.style.visibility = 'visible';
      svg.style.display = 'block';
    }
  }
};

// Policies with compliance data for control domains section
const controlDomainPolicies = computed(() => {
  console.log('');
  console.log('🎯 ========================================');
  console.log('🎯 CONTROL DOMAIN POLICIES COMPUTED');
  console.log('🎯 ========================================');
  console.log('📊 Selected Framework ID:', selectedFrameworkId.value);
  console.log('📦 Homepage Data Available:', !!homepageData.value);
  
  // If all frameworks selected, return empty array (will show percentage instead)
  if (selectedFrameworkId.value === 'all' || !homepageData.value) {
    console.log('⏭️ Skipping - All frameworks selected or no data');
    console.log('🎯 ========================================');
    console.log('');
    return [];
  }
  
  // Get all policies from applied category (Status='Approved')
  const policies = homepageData.value?.policies?.applied?.policies || [];
  console.log('📋 Total Policies Found:', policies.length);
  console.log('📋 Policies Data:', policies);
  
  // Filter policies by selected framework if frameworkId is available in policy data
  // Note: Policies should already be filtered by framework in the backend response
  const filteredPolicies = policies;
  console.log('📋 Filtered Policies Count:', filteredPolicies.length);
  
  // Return policies with compliance data
  const result = filteredPolicies.map(policy => {
    const totalCompliances = policy.totalCompliances || 0;
    const implementedCompliances = policy.implementedCompliances || 0;
    const implementationPercentage = totalCompliances > 0 
      ? Math.round((implementedCompliances / totalCompliances) * 100) 
      : 0;
    
    return {
      PolicyId: policy.PolicyId,
      PolicyName: policy.PolicyName,
      Status: policy.Status,
      totalCompliances: totalCompliances,
      implementedCompliances: implementedCompliances,
      implementationPercentage: implementationPercentage
    };
  });
  
  console.log('✅ Final Control Domain Policies:', result);
  console.log('📊 Sample Policy Data:', result[0] || 'No policies');
  console.log('🎯 ========================================');
  console.log('');
  
  return result;
});

// Compliance percentage for all frameworks view
const allFrameworksCompliancePercentage = computed(() => {
  if (selectedFrameworkId.value !== 'all' || !homepageData.value) {
    return null;
  }
  
  const stats = homepageData.value?.hero?.stats;
  if (!stats) return null;
  
  const total = stats.totalCompliancesAll || 0;
  const compliant = stats.compliantCompliances || 0;
  
  // Use compliant compliances (based on audit findings) instead of just active
  return total > 0 ? Math.round((compliant / total) * 100) : 0;
});

// All frameworks list for "All Frameworks" view
const allFrameworksList = computed(() => {
  if (selectedFrameworkId.value !== 'all' || !homepageData.value) {
    return [];
  }
  
  const frameworks = homepageData.value?.frameworks || [];
  
  // Calculate compliance percentage for each framework based on compliant controls (audited)
  return frameworks.map(framework => {
    const stats = framework.stats || {};
    const totalCompliances = stats.totalCompliancesAll || 0;
    const compliantCompliances = stats.compliantCompliances || 0;
    // Use compliant compliances (based on audit findings) instead of just active
    const compliancePercentage = totalCompliances > 0 
      ? Math.round((compliantCompliances / totalCompliances) * 100) 
      : 0;
    
    return {
      ...framework,
      compliancePercentage,
      totalCompliances,
      compliantCompliances,
      activeCompliances: stats.activeCompliances || 0
    };
  });
});

// Module Dashboard Metrics
const policyMetrics = ref({
  activePolicies: 0,
  approvalRate: 0,
  totalPolicies: 0,
  avgApprovalTime: 0
});

const complianceMetrics = ref({
  activeCompliances: 0,
  approvalRate: 0,
  totalFindings: 0,
  underReview: 0
});

const riskMetrics = ref({
  totalRisks: 0,
  total: 0,
  active: 0,
  inactive: 0,
  acceptedRisks: 0,
  accepted: 0,
  mitigatedRisks: 0,
  mitigated: 0,
  inProgressRisks: 0,
  inProgress: 0
});

const incidentMetrics = ref({
  totalIncidents: 0,
  total: 0,
  active: 0,
  inactive: 0,
  resolved: 0,
  mttd: 0,
  mttr: 0,
  closureRate: 0
});

const auditorMetrics = ref({
  completionRate: 0,
  totalAudits: 0,
  active: 0,
  inactive: 0,
  openAudits: 0,
  completedAudits: 0
});

// Implementation Features (now computed from framework content)
const implementationFeatures = computed(() => {
  return currentFrameworkContent.value?.compliance?.features || [];
});

// Benefits (now computed from framework content)
const benefits = computed(() => {
  return currentFrameworkContent.value?.benefits || [];
});

// Platform features for footer (computed from framework content)
const platformFeatures = computed(() => {
  const frameworkName = currentFrameworkContent.value?.frameworkName || 'Framework';
  const baseFeatures = [
    `${frameworkName} Dashboard`,
    'Risk Monitoring',
    'Compliance Management',
    'Regulatory Reporting',
    'Audit Management'
  ];
  
  // Add framework-specific features only if frameworkName is a string
  if (typeof frameworkName === 'string') {
    if (frameworkName.includes('Basel')) {
      return [
        `${frameworkName} Dashboard`,
        'Capital Management',
        'Liquidity Management',
        'Risk Monitoring',
        'Regulatory Reporting'
      ];
    } else if (frameworkName.includes('ISO')) {
      return [
        `${frameworkName} Dashboard`,
        'Security Monitoring',
        'Incident Management',
        'Risk Assessment',
        'Audit Management'
      ];
    } else if (frameworkName.includes('NIST')) {
      return [
        `${frameworkName} Dashboard`,
        'Control Assessment',
        'Continuous Monitoring',
        'Authorization Management',
        'FedRAMP Support'
      ];
    } else if (frameworkName.includes('PCI')) {
      return [
        `${frameworkName} Dashboard`,
        'Cardholder Data Monitoring',
        'Vulnerability Management',
        'Security Testing',
        'QSA Reporting'
      ];
    } else if (frameworkName.includes('TCFD')) {
      return [
        `${frameworkName} Dashboard`,
        'Climate Risk Assessment',
        'Scenario Analysis',
        'Metrics Tracking',
        'Disclosure Reporting'
      ];
    }
  }
  
  return baseFeatures;
});

// Resources for footer (computed from framework content)
const resourceFeatures = computed(() => {
  const frameworkName = (currentFrameworkContent.value?.frameworkName && typeof currentFrameworkContent.value?.frameworkName === 'string') 
    ? currentFrameworkContent.value.frameworkName 
    : 'Framework';
  return [
    `${frameworkName} Documentation`,
    'Risk Management Best Practices',
    'Compliance Case Studies',
    `${frameworkName} Webinars`,
    `${frameworkName} Support`
  ];
});

// Basel KPIs (homepage)
const alertSummary = ref({ critical: 1, high: 2, medium: 3 });
const alerts = ref([
  { severity: 'critical', title: 'CET1 below internal buffer', description: 'Current CET1 10.8% vs target 12%', kpi: 'CET1' },
  { severity: 'high', title: 'LCR under severe stress < 100%', description: 'Projected LCR 92% under severe', kpi: 'LCR' },
  { severity: 'medium', title: 'Single-name exposure near limit', description: 'Counterparty X at 24% of Tier1', kpi: 'Large Exposure' }
]);

const ourPeer = ref({ name: 'Our Bank', roe: 12.4, spark: '5,15 20,12 35,10 50,11 65,8 80,7' });
const peers = ref([
  { name: 'Our Bank', roe: 12.4, spark: '5,15 20,12 35,10 50,11 65,8 80,7' },
  { name: 'Peer A', roe: 10.8, spark: '5,14 20,13 35,12 50,12 65,11 80,10' },
  { name: 'Peer B', roe: 13.2, spark: '5,16 20,14 35,13 50,12 65,11 80,9' },
  { name: 'Peer C', roe: 11.1, spark: '5,13 20,12 35,12 50,11 65,10 80,10' }
]);

const buBubbles = ref([
  { name: 'Retail', x: 60, y: 120, r: 14, color: '#60a5fa' },
  { name: 'Corporate', x: 120, y: 90, r: 18, color: '#34d399' },
  { name: 'Markets', x: 180, y: 70, r: 16, color: '#f59e0b' },
  { name: 'Wealth', x: 230, y: 80, r: 12, color: '#a78bfa' }
]);

// Additional KPIs data
const liquidityStress = ref({
  current: 125,
  status: 'pass',
  waterfall: [
    { x: 10, y: 20, width: 30, height: 40, color: '#10b981' },
    { x: 50, y: 15, width: 30, height: 45, color: '#3b82f6' },
    { x: 90, y: 25, width: 30, height: 35, color: '#f59e0b' },
    { x: 130, y: 10, width: 30, height: 50, color: '#ef4444' },
    { x: 170, y: 20, width: 30, height: 40, color: '#8b5cf6' }
  ]
});

const largeExposure = ref({
  topExposure: 18.5,
  status: 'monitor',
  bars: [
    { x: 20, y: 30, width: 25, height: 30, color: '#ef4444' },
    { x: 55, y: 40, width: 25, height: 20, color: '#f59e0b' },
    { x: 90, y: 45, width: 25, height: 15, color: '#10b981' },
    { x: 125, y: 50, width: 25, height: 10, color: '#3b82f6' },
    { x: 160, y: 52, width: 25, height: 8, color: '#8b5cf6' }
  ]
});

const fundingConcentration = ref({
  top3: 42,
  status: 'alert',
  heatmap: [
    { name: 'Bank A', value: 18, color: 'rgba(239, 68, 68, 0.8)' },
    { name: 'Bank B', value: 15, color: 'rgba(245, 158, 11, 0.8)' },
    { name: 'Bank C', value: 9, color: 'rgba(59, 130, 246, 0.8)' }
  ]
});

const recoveryPlan = ref({
  score: 78,
  status: 'pass',
  radarPoints: '100,30 80,50 60,40 70,20 90,10'
});

const forecastAccuracy = ref({
  mape: 1.8,
  status: 'pass',
  points: [
    { x: 20, y: 45 }, { x: 40, y: 42 }, { x: 60, y: 38 }, { x: 80, y: 35 },
    { x: 100, y: 32 }, { x: 120, y: 28 }, { x: 140, y: 25 }, { x: 160, y: 22 }
  ]
});

const capitalShortfall = ref({
  amount: 45,
  status: 'monitor',
  waterfall: [
    { x: 10, y: 20, width: 30, height: 40, color: '#10b981' },
    { x: 50, y: 25, width: 30, height: 35, color: '#3b82f6' },
    { x: 90, y: 30, width: 30, height: 30, color: '#f59e0b' },
    { x: 130, y: 35, width: 30, height: 25, color: '#ef4444' },
    { x: 170, y: 40, width: 30, height: 20, color: '#8b5cf6' }
  ]
});

const counterpartyExposures = ref({
  topCount: 3,
  status: 'monitor',
  bars: [
    { x: 20, y: 25, width: 25, height: 35, color: '#ef4444' },
    { x: 55, y: 35, width: 25, height: 25, color: '#f59e0b' },
    { x: 90, y: 40, width: 25, height: 20, color: '#10b981' },
    { x: 125, y: 45, width: 25, height: 15, color: '#3b82f6' },
    { x: 160, y: 50, width: 25, height: 10, color: '#8b5cf6' }
  ]
});

const opRiskLosses = ref({
  total: 1420,
  status: 'monitor',
  bars: [
    { x: 20, y: 30, width: 25, height: 30, color: '#ef4444' },
    { x: 55, y: 40, width: 25, height: 20, color: '#f59e0b' },
    { x: 90, y: 35, width: 25, height: 25, color: '#10b981' },
    { x: 125, y: 45, width: 25, height: 15, color: '#3b82f6' },
    { x: 160, y: 50, width: 25, height: 10, color: '#8b5cf6' }
  ]
});

const baselIncidents = ref({
  total: 12,
  status: 'improving',
  trendPath: 'M 10,50 Q 30,40 50,35 T 90,30 T 130,25 T 170,20',
  points: [
    { x: 10, y: 50 }, { x: 30, y: 40 }, { x: 50, y: 35 }, { x: 70, y: 32 },
    { x: 90, y: 30 }, { x: 110, y: 28 }, { x: 130, y: 25 }, { x: 150, y: 22 },
    { x: 170, y: 20 }
  ]
});

// Additional Basel KPIs data
const controlEffectiveness = ref({
  score: 85,
  status: 'pass',
  radarPoints: '100,10 120,30 110,50 90,50 80,30'
});

const controlCoverage = ref({
  percentage: 92,
  status: 'monitor',
  dashArray: '58 125' // 92% of 125.6 circumference
});

const auditFindings = ref({
  open: 7,
  status: 'monitor',
  bars: [
    { x: 20, y: 30, width: 25, height: 30, color: '#ef4444' },
    { x: 55, y: 40, width: 25, height: 20, color: '#f59e0b' },
    { x: 90, y: 45, width: 25, height: 15, color: '#10b981' },
    { x: 125, y: 50, width: 25, height: 10, color: '#3b82f6' },
    { x: 160, y: 52, width: 25, height: 8, color: '#8b5cf6' }
  ]
});

const policyAttestation = ref({
  rate: 96,
  status: 'pass',
  dashArray: '60 125' // 96% of 125.6 circumference
});

const policyCoverage = ref({
  implemented: 6,
  required: 7,
  status: 'monitor',
  implementedWidth: 137 // 6/7 * 160 = 137px
});

const pillar3Disclosure = ref({
  completeness: 88,
  status: 'monitor',
  dashArray: '55 125' // 88% of 125.6 circumference
});

// Chart data (now computed from policy data)
const overallComplianceData = computed(() => {
  const policies = policyData.value;
  return {
    labels: ['Applied', 'In Progress', 'Rejected'],
    datasets: [
      {
        data: [
          Number(policies.applied?.percentage || 0),
          Number(policies.in_progress?.percentage || 0),
          Number(policies.rejected?.percentage || 0)
        ],
        backgroundColor: [
          '#10b981', // Green for applied
          '#f59e0b', // Orange for in progress
          '#ef4444'  // Red for rejected
        ],
        borderWidth: 0,
        cutout: '75%',
        hoverOffset: 4
      }
    ]
  };
});

// Policy data (reactive ref for dynamic updates from API)
const policyData = ref({
  applied: { policies: [], count: 0, percentage: 0 },
  in_progress: { policies: [], count: 0, percentage: 0 },
  pending: { policies: [], count: 0, percentage: 0 },
  rejected: { policies: [], count: 0, percentage: 0 }
});

// Popup state
const showPolicyPopup = ref(false);
const popupData = ref({ policies: [], title: '', color: '' });



const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: 'white',
      bodyColor: 'white',
      borderColor: '#3b82f6',
      borderWidth: 1,
      cornerRadius: 8,
      callbacks: {
        label: function(context) {
          return context.label + ': ' + context.parsed + '%';
        }
      }
    }
  },
  elements: {
    arc: {
      borderWidth: 0,
      borderRadius: 4
    }
  },
  onClick: (event, elements) => {
    console.log('');
    console.log('🎯 ================================================');
    console.log('🎯 DONUT CHART CLICKED');
    console.log('🎯 ================================================');
    console.log('🎯 Event:', event);
    console.log('🎯 Elements:', elements);
    
    if (elements.length > 0) {
      const index = elements[0].index;
      const labels = ['Applied', 'In Progress', 'Rejected'];
      const colors = ['#3b82f6', '#f59e0b', '#ef4444'];
      const statusKeys = ['applied', 'in_progress', 'rejected'];
      
      const status = statusKeys[index];
      const data = policyData.value[status];
      
      console.log('');
      console.log('🎯 ================================================');
      console.log('🎯 DONUT CHART SEGMENT CLICKED');
      console.log('🎯 ================================================');
      console.log('🎯 Selected Framework ID:', selectedFrameworkId.value);
      console.log('🎯 Clicked segment index:', index);
      console.log('🎯 Status key:', status);
      console.log('🎯 Status label:', labels[index]);
      console.log('');
      console.log('📋 Current policyData structure:');
      console.log('   - policyData.value:', policyData.value);
      console.log(`   - policyData.value[${status}]:`, data);
      console.log('');
      
      if (!data) {
        console.error('❌ ERROR: No data found for status:', status);
        console.error('❌ Available keys in policyData.value:', Object.keys(policyData.value));
        return;
      }
      
      console.log('📋 Data details for', status, ':');
      console.log('   - Count:', data.count || 0);
      console.log('   - Percentage:', data.percentage || 0);
      console.log('   - Policies count:', data?.policies?.length || 0);
      console.log('   - Policies array:', data?.policies);
      
      if (data.policies && data.policies.length > 0) {
        console.log('   - Sample policy:', data.policies[0]);
        console.log('   - Policy structure check:');
        console.log('     * Has PolicyId:', 'PolicyId' in data.policies[0]);
        console.log('     * Has PolicyName:', 'PolicyName' in data.policies[0]);
        console.log('     * Has Status:', 'Status' in data.policies[0]);
      } else {
        console.warn('⚠️ WARNING: No policies found in data.policies array');
      }
      
      popupData.value = {
        policies: data.policies || [],
        title: labels[index],
        color: colors[index],
        percentage: data.percentage || 0
      };
      
      console.log('');
      console.log('🎪 ================================================');
      console.log('🎪 POPUP DATA SET');
      console.log('🎪 ================================================');
      console.log('🎪 Title:', popupData.value.title);
      console.log('🎪 Color:', popupData.value.color);
      console.log('🎪 Percentage:', popupData.value.percentage);
      console.log('🎪 Policies count:', popupData.value.policies.length);
      console.log('🎪 Policies:', popupData.value.policies);
      if (popupData.value.policies.length > 0) {
        console.log('🎪 First policy in popup:', popupData.value.policies[0]);
      }
      console.log('🎪 ================================================');
      console.log('');
      
      showPolicyPopup.value = true;
    } else {
      console.log('⚠️ No elements clicked');
      console.log('🎯 ================================================');
      console.log('');
    }
  }
};

// Floating elements positioning
const getFloatingStyle = (index) => {
  const positions = [
    { top: '10%', left: '10%', animationDelay: '0s' },
    { top: '20%', right: '15%', animationDelay: '2s' },
    { top: '60%', left: '5%', animationDelay: '4s' },
    { top: '70%', right: '10%', animationDelay: '1s' },
    { top: '40%', left: '80%', animationDelay: '3s' },
    { top: '85%', left: '60%', animationDelay: '5s' },
  ];
  
  return positions[index - 1] || {};
};

// Navigation functions
const navigateToCompliance = () => {
  router.push({ name: 'ComplianceDashboard' });
};

const navigateToModule = (moduleName) => {
  router.push({ name: moduleName });
};

// Fetch dashboard metrics from actual API endpoints (with framework filtering)
// NOTE: These are fallback functions - unified endpoint data takes priority
const fetchPolicyMetrics = async () => {
  try {
    // Skip if data already loaded from unified endpoint
    if (homepageData.value && homepageData.value.moduleMetrics && homepageData.value.moduleMetrics.policy) {
      console.log('⏭️ Skipping fetchPolicyMetrics - data already loaded from unified endpoint');
      return;
    }
    
    // Check cache first
    const cachedMetrics = homepageDataService.getModuleMetrics('policyMetrics');
    if (cachedMetrics) {
      console.log('✅ [HomeView] Using cached policy metrics');
      policyMetrics.value = cachedMetrics;
      return;
    }
    
    // Build URL with framework filter if specific framework is selected
    let apiUrl = '';
    const frameworkId = selectedFrameworkId.value && selectedFrameworkId.value !== 'all' ? selectedFrameworkId.value : null;
    
    if (frameworkId) {
      // Use framework-specific endpoint if available
      apiUrl = `${API_ENDPOINTS.HOME_POLICIES_BY_STATUS()}?frameworkId=${frameworkId}`;
      const response = await axios.get(apiUrl);
      if (response.data && response.data.success && response.data.data) {
        const data = response.data.data;
        policyMetrics.value = {
          activePolicies: data.applied?.count || 0,
          approvalRate: Math.round((data.applied?.count || 0) / ((data.applied?.count || 0) + (data.in_progress?.count || 0) + (data.pending?.count || 0)) * 100) || 0,
          totalPolicies: (data.applied?.count || 0) + (data.in_progress?.count || 0) + (data.pending?.count || 0),
          avgApprovalTime: 3.2
        };
        // Cache the result
        homepageDataService.setModuleMetrics('policyMetrics', policyMetrics.value);
      }
    } else {
      // Get all policies if no framework selected
      const response = await dashboardService.getDashboardSummary();
      if (response.data) {
        policyMetrics.value = {
          activePolicies: response.data.active_policies || 0,
          approvalRate: response.data.approval_rate || 0,
          totalPolicies: response.data.total_policies || 0,
          avgApprovalTime: response.data.avg_approval_time || 3.2
        };
        // Cache the result
        homepageDataService.setModuleMetrics('policyMetrics', policyMetrics.value);
      }
    }
  } catch (error) {
    console.error('Error fetching policy metrics:', error);
    // Only set default values if no data exists from unified endpoint
    if (!homepageData.value || !homepageData.value.moduleMetrics || !homepageData.value.moduleMetrics.policy) {
    policyMetrics.value = {
      activePolicies: 7,
      approvalRate: 78,
      totalPolicies: 7,
      avgApprovalTime: 14
    };
    }
  }
};

const fetchComplianceMetrics = async () => {
  try {
    // Skip if data already loaded from unified endpoint
    if (homepageData.value && homepageData.value.moduleMetrics && homepageData.value.moduleMetrics.compliance) {
      console.log('⏭️ Skipping fetchComplianceMetrics - data already loaded from unified endpoint');
      return;
    }
    
    // Check cache first
    const cachedMetrics = homepageDataService.getModuleMetrics('complianceMetrics');
    if (cachedMetrics) {
      console.log('✅ [HomeView] Using cached compliance metrics');
      complianceMetrics.value = cachedMetrics;
      return;
    }
    
    const frameworkId = selectedFrameworkId.value && selectedFrameworkId.value !== 'all' ? selectedFrameworkId.value : null;
    const params = frameworkId ? { frameworkId } : {};
    
    const response = await complianceService.getComplianceDashboard(params);
    if (response.data && response.data.success) {
      const summary = response.data.data?.summary || {};
      complianceMetrics.value = {
        activeCompliances: summary.status_counts?.active_compliance || 0,
        approvalRate: summary.approval_rate || 0,
        totalFindings: summary.total_findings || 0,
        underReview: summary.status_counts?.under_review || 1
      };
      // Cache the result
      homepageDataService.setModuleMetrics('complianceMetrics', complianceMetrics.value);
    }
  } catch (error) {
    console.error('Error fetching compliance metrics:', error);
    // Only set default values if no data exists from unified endpoint
    if (!homepageData.value || !homepageData.value.moduleMetrics || !homepageData.value.moduleMetrics.compliance) {
    complianceMetrics.value = {
      activeCompliances: 22,
      approvalRate: 82,
      totalFindings: 15,
      underReview: 3
    };
    }
  }
};

const fetchRiskMetrics = async () => {
  try {
    // Skip if data already loaded from unified endpoint
    if (homepageData.value && homepageData.value.moduleMetrics && homepageData.value.moduleMetrics.risk) {
      console.log('⏭️ Skipping fetchRiskMetrics - data already loaded from unified endpoint');
      return;
    }
    
    // Check cache first
    const cachedMetrics = homepageDataService.getModuleMetrics('riskMetrics');
    if (cachedMetrics) {
      console.log('✅ [HomeView] Using cached risk metrics');
      riskMetrics.value = cachedMetrics;
      return;
    }
    
    const frameworkId = selectedFrameworkId.value && selectedFrameworkId.value !== 'all' ? selectedFrameworkId.value : null;
    let apiUrl = API_ENDPOINTS.RISK_METRICS();
    
    if (frameworkId) {
      apiUrl += `?frameworkId=${frameworkId}`;
    }
    
    const response = await axios.get(apiUrl);
    if (response.data) {
      riskMetrics.value = {
        totalRisks: response.data.total || 0,
        acceptedRisks: response.data.accepted || 0,
        mitigatedRisks: response.data.mitigated || 0,
        inProgressRisks: response.data.inProgress || 0,
        total: response.data.total || 0,
        active: response.data.active || 0,
        inactive: response.data.inactive || 0,
        accepted: response.data.accepted || 0,
        mitigated: response.data.mitigated || 0,
        inProgress: response.data.inProgress || 0
      };
      // Cache the result
      homepageDataService.setModuleMetrics('riskMetrics', riskMetrics.value);
    }
  } catch (error) {
    console.error('Error fetching risk metrics:', error);
    // Only set default values if no data exists from unified endpoint
    if (!homepageData.value || !homepageData.value.moduleMetrics || !homepageData.value.moduleMetrics.risk) {
    riskMetrics.value = {
      totalRisks: 18,
      acceptedRisks: 8,
      mitigatedRisks: 6,
        inProgressRisks: 4,
        total: 18,
        active: 18,
        inactive: 0,
        accepted: 8,
        mitigated: 6,
        inProgress: 4
      };
    }
  }
};

const fetchIncidentMetrics = async () => {
  try {
    // Skip if data already loaded from unified endpoint
    if (homepageData.value && homepageData.value.moduleMetrics && homepageData.value.moduleMetrics.incident) {
      console.log('⏭️ Skipping fetchIncidentMetrics - data already loaded from unified endpoint');
      return;
    }
    
    // Check cache first
    const cachedMetrics = homepageDataService.getModuleMetrics('incidentMetrics');
    if (cachedMetrics) {
      console.log('✅ [HomeView] Using cached incident metrics');
      incidentMetrics.value = cachedMetrics;
      return;
    }
    
    const frameworkId = selectedFrameworkId.value && selectedFrameworkId.value !== 'all' ? selectedFrameworkId.value : null;
    const params = frameworkId ? { frameworkId } : {};
    
    const response = await incidentService.getIncidentDashboard(params);
    if (response.data && response.data.success) {
      const summary = response.data.data?.summary || {};
      incidentMetrics.value = {
        totalIncidents: summary.total_count || 0,
        total: summary.total_count || 0,
        active: summary.active || 0,
        inactive: summary.inactive || 0,
        resolved: summary.resolved || 0,
        mttd: summary.mttd || 4.8,
        mttr: summary.mttr || 2.4,
        closureRate: summary.resolution_rate || 0
      };
      // Cache the result
      homepageDataService.setModuleMetrics('incidentMetrics', incidentMetrics.value);
    }
  } catch (error) {
    console.error('Error fetching incident metrics:', error);
    // Only set default values if no data exists from unified endpoint
    if (!homepageData.value || !homepageData.value.moduleMetrics || !homepageData.value.moduleMetrics.incident) {
    incidentMetrics.value = {
      totalIncidents: 12,
        total: 12,
        active: 12,
        inactive: 0,
        resolved: 0,
      mttd: 3.2,
      mttr: 8.5,
      closureRate: 85
    };
    }
  }
};

const fetchAuditorMetrics = async () => {
  try {
    // Skip if data already loaded from unified endpoint
    if (homepageData.value && homepageData.value.moduleMetrics && homepageData.value.moduleMetrics.audit) {
      console.log('⏭️ Skipping fetchAuditorMetrics - data already loaded from unified endpoint');
      return;
    }
    
    // Check cache first
    const cachedMetrics = homepageDataService.getModuleMetrics('auditorMetrics');
    if (cachedMetrics) {
      console.log('✅ [HomeView] Using cached auditor metrics');
      auditorMetrics.value = cachedMetrics;
      return;
    }
    
    const frameworkId = selectedFrameworkId.value && selectedFrameworkId.value !== 'all' ? selectedFrameworkId.value : null;
    let apiUrl = API_ENDPOINTS.AUDIT_COMPLETION_RATE;
    
    if (frameworkId) {
      apiUrl += `?frameworkId=${frameworkId}`;
    }
    
    const response = await axios.get(apiUrl);
    if (response.data) {
      auditorMetrics.value = {
        completionRate: response.data.current_month_rate || 0,
        totalAudits: response.data.total_current_month || 43,
        active: response.data.active || 0,
        inactive: response.data.inactive || 0,
        openAudits: response.data.open_this_week || 4,
        completedAudits: response.data.this_week_count || 25
      };
      // Cache the result
      homepageDataService.setModuleMetrics('auditorMetrics', auditorMetrics.value);
    }
  } catch (error) {
    console.error('Error fetching auditor metrics:', error);
    // Only set default values if no data exists from unified endpoint
    if (!homepageData.value || !homepageData.value.moduleMetrics || !homepageData.value.moduleMetrics.audit) {
    auditorMetrics.value = {
      completionRate: 78,
      totalAudits: 15,
        active: 15,
        inactive: 0,
      openAudits: 3,
      completedAudits: 12
    };
    }
  }
};

// Show popup for legend items
const showLegendPopup = (status, event) => {
  console.log('');
  console.log('🎯 ================================================');
  console.log('🎯 LEGEND CLICKED');
  console.log('🎯 ================================================');
  console.log('🎯 Status:', status);
  console.log('🎯 Event:', event);
  
  const labels = ['Applied', 'In Progress', 'Rejected'];
  const colors = ['#3b82f6', '#f59e0b', '#ef4444'];
  const statusKeys = ['applied', 'in_progress', 'rejected'];
  
  const index = statusKeys.indexOf(status);
  const data = policyData.value[status];
  
  console.log('📋 Clicked status:', status);
  console.log('📋 Status index:', index);
  console.log('📋 Status label:', labels[index]);
  console.log('📋 Data for this status:', data);
  console.log('📋 Policies count:', data?.policies?.length || 0);
  console.log('📋 Policies array:', data?.policies);
  
  popupData.value = {
    policies: data.policies || [],
    title: labels[index],
    color: colors[index],
    percentage: data.percentage || 0
  };

  
  
  console.log('🎪 ================================================');
  console.log('🎪 LEGEND POPUP DATA SET');
  console.log('🎪 ================================================');
  console.log('🎪 Title:', popupData.value.title);
  console.log('🎪 Color:', popupData.value.color);
  console.log('🎪 Percentage:', popupData.value.percentage);
  console.log('🎪 Policies count:', popupData.value.policies.length);
  console.log('🎪 Policies:', popupData.value.policies);
  console.log('🎪 ================================================');
  console.log('');
  
  showPolicyPopup.value = true;
};

// Get policy description based on policy name
const getPolicyDescription = (policyName) => {
  const descriptions = {
    'Capital Adequacy Policy': 'Establishes guidelines for maintaining sufficient capital levels to cover potential losses and meet Basel 3 regulatory requirements.',
    'Liquidity Risk Management Policy': 'Ensures adequate liquidity to meet short and long-term obligations and withstand periods of financial stress as per Basel 3.',
    'Leverage Ratio Policy': 'Maintains leverage ratio requirements to limit excessive leverage and ensure financial stability under Basel 3 framework.',
    'Risk Disclosure & Transparency Policy': 'Ensures comprehensive risk disclosure and transparency in financial reporting and regulatory submissions.',
    'Stress Testing & Risk Management Policy': 'Outlines procedures for testing financial resilience under various adverse economic scenarios and risk management.',
    'Counterparty Credit Risk Policy': 'Establishes guidelines for assessing and mitigating risks associated with business counterparties and credit exposure.'
  };
  
  return descriptions[policyName] || 'Policy description not available.';
};


// ====================================================================
// NEW: Fetch dynamic homepage data from unified endpoint
// ====================================================================
const fetchDynamicHomepageData = async () => {
  try {
    console.log('🏠 ========================================');
    console.log('🏠 FETCHING DYNAMIC HOMEPAGE DATA');
    console.log('🏠 ========================================');
    console.log('🏠 Selected Framework ID:', selectedFrameworkId.value);
    
    let response;
    
    // Check cache first
    const cacheKey = selectedFrameworkId.value === 'all' ? 'all' : selectedFrameworkId.value;
    
    if (homepageDataService.hasHomepageDataCache(cacheKey)) {
      console.log(`🏠 [HomeView] Using cached homepage data for framework: ${cacheKey}`);
      response = homepageDataService.getHomepageData(cacheKey);
    } else {
      // If "All Frameworks" is selected, use getAllFrameworksData
      if (selectedFrameworkId.value === 'all') {
        console.log('🏠 "All Frameworks" selected - calling getAllFrameworksData...');
        response = await homepageDataService.getAllFrameworksData();
      } else {
        // Get framework ID (null for "all")
        const frameworkId = (selectedFrameworkId.value && selectedFrameworkId.value !== 'all') 
          ? selectedFrameworkId.value 
          : null;
        
        console.log('🏠 Framework ID to send to API:', frameworkId);
        console.log('🏠 Calling homepageDataService.getHomeContent...');
        
        response = await homepageDataService.getHomeContent(frameworkId);
      }
    }
    
    console.log('🏠 ========================================');
    console.log('🏠 API RESPONSE RECEIVED');
    console.log('🏠 ========================================');
    console.log('📊 Full Response:', JSON.stringify(response, null, 2));
    console.log('📊 Response.success:', response?.success);
    console.log('📊 Response.framework:', response?.framework);
    console.log('📊 Response.policies:', response?.policies);
    console.log('📊 Response.moduleMetrics:', response?.moduleMetrics);
    
    // Log active/inactive breakdown
    if (response?.hero?.stats) {
      console.log('');
      console.log('📊 ========================================');
      console.log('📊 FRAMEWORK STATUS BREAKDOWN');
      console.log('📊 ========================================');
      console.log('📋 Framework:', response.framework?.name || 'Unknown');
      console.log('📋 POLICIES:');
      console.log(`   Total (All): ${response.hero.stats.totalPoliciesAll || response.hero.stats.totalPolicies || 0}`);
      console.log(`   Active: ${response.hero.stats.activePolicies || 0}`);
      console.log(`   Inactive: ${response.hero.stats.inactivePolicies || 0}`);
      if (response.policies?.rejected) {
        console.log(`   Rejected: ${response.policies.rejected.count || 0} policies (${response.policies.rejected.percentage || 0}%)`);
      }
      console.log('✅ COMPLIANCES:');
      console.log(`   Total (All): ${response.hero.stats.totalCompliancesAll || response.hero.stats.totalCompliances || 0}`);
      console.log(`   Active: ${response.hero.stats.activeCompliances || 0}`);
      console.log(`   Inactive: ${response.hero.stats.inactiveCompliances || 0}`);
      console.log('⚠️ RISKS:');
      console.log(`   Total: ${response.hero.stats.totalRisks || 0}`);
      console.log(`   Active: ${response.hero.stats.activeRisks || 0}`);
      console.log(`   Inactive: ${response.hero.stats.inactiveRisks || 0}`);
      console.log(`   Mitigated: ${response.hero.stats.mitigatedRisks || 0}`);
      console.log('🚨 INCIDENTS:');
      console.log(`   Total: ${response.hero.stats.totalIncidents || 0}`);
      console.log(`   Active: ${response.hero.stats.activeIncidents || 0}`);
      console.log(`   Inactive: ${response.hero.stats.inactiveIncidents || 0}`);
      console.log(`   Resolved: ${response.hero.stats.resolvedIncidents || 0}`);
      console.log('🔍 AUDITS:');
      console.log(`   Total: ${response.hero.stats.totalAudits || 0}`);
      console.log(`   Active: ${response.hero.stats.activeAudits || 0}`);
      console.log(`   Inactive: ${response.hero.stats.inactiveAudits || 0}`);
      console.log(`   Completed: ${response.hero.stats.completedAudits || 0}`);
      console.log('📊 ========================================');
      console.log('');
    }
    
    if (response && response.success) {
      console.log('✅ SUCCESS - Updating data...');
      
      // Store homepage data for use in control domains section and module dashboards
      homepageData.value = response;
      console.log('📦 Stored homepage data in homepageData.value');
      console.log('📦 Module metrics stored:', response.moduleMetrics);
      
      // Update policy donut data with real policies from database
      const oldPolicyData = JSON.parse(JSON.stringify(policyData.value));
      
      // Ensure response.policies has the correct structure
      if (response.policies) {
        console.log('');
        console.log('🔄 ========================================');
        console.log('🔄 PROCESSING POLICY DATA FROM API');
        console.log('🔄 ========================================');
        console.log('📦 Raw response.policies:', response.policies);
        console.log('📦 response.policies.applied:', response.policies.applied);
        console.log('📦 response.policies.in_progress:', response.policies.in_progress);
        console.log('📦 response.policies.pending:', response.policies.pending);
        console.log('📦 response.policies.rejected:', response.policies.rejected);
        
        policyData.value = {
          applied: {
            policies: response.policies.applied?.policies || [],
            count: response.policies.applied?.count || 0,
            percentage: response.policies.applied?.percentage || 0
          },
          in_progress: {
            policies: response.policies.in_progress?.policies || [],
            count: response.policies.in_progress?.count || 0,
            percentage: response.policies.in_progress?.percentage || 0
          },
          pending: {
            policies: response.policies.pending?.policies || [],
            count: response.policies.pending?.count || 0,
            percentage: response.policies.pending?.percentage || 0
          },
          rejected: {
            policies: response.policies.rejected?.policies || [],
            count: response.policies.rejected?.count || 0,
            percentage: response.policies.rejected?.percentage || 0
          }
        };
        
        // Cache the result
        homepageDataService.setPolicyData(policyData.value);
        
        console.log('');
        console.log('✅ UPDATED policyData.value:');
        console.log('   - Applied policies:', policyData.value.applied.policies?.length || 0);
        console.log('   - Applied count:', policyData.value.applied.count);
        console.log('   - Applied percentage:', policyData.value.applied.percentage);
        if (policyData.value.applied.policies?.length > 0) {
          console.log('   - Sample applied policy:', policyData.value.applied.policies[0]);
        }
        console.log('   - In Progress policies:', policyData.value.in_progress.policies?.length || 0);
        console.log('   - In Progress count:', policyData.value.in_progress.count);
        console.log('   - In Progress percentage:', policyData.value.in_progress.percentage);
        if (policyData.value.in_progress.policies?.length > 0) {
          console.log('   - Sample in_progress policy:', policyData.value.in_progress.policies[0]);
        }
        console.log('   - Pending policies:', policyData.value.pending.policies?.length || 0);
        console.log('   - Pending count:', policyData.value.pending.count);
        console.log('   - Pending percentage:', policyData.value.pending.percentage);
        if (policyData.value.pending.policies?.length > 0) {
          console.log('   - Sample pending policy:', policyData.value.pending.policies[0]);
        }
        console.log('   - Rejected policies:', policyData.value.rejected.policies?.length || 0);
        console.log('   - Rejected count:', policyData.value.rejected.count);
        console.log('   - Rejected percentage:', policyData.value.rejected.percentage);
        if (policyData.value.rejected.policies?.length > 0) {
          console.log('   - Sample rejected policy:', policyData.value.rejected.policies[0]);
        }
        console.log('🔄 ========================================');
        console.log('');
        
        // Log compliance data for applied policies
        console.log('');
        console.log('📊 ========================================');
        console.log('📊 COMPLIANCE DATA IN RESPONSE');
        console.log('📊 ========================================');
        const appliedPolicies = policyData.value.applied.policies || [];
        console.log(`📋 Applied Policies with Compliance Data: ${appliedPolicies.length}`);
        if (appliedPolicies.length > 0) {
          console.log('📋 Sample Compliance Data (first 5 policies):');
          appliedPolicies.slice(0, 5).forEach((policy, index) => {
            console.log(`   ${index + 1}. ${policy.PolicyName || 'N/A'}`);
            console.log(`      - Total Compliances (Controls): ${policy.totalCompliances || 0}`);
            console.log(`      - Compliant Compliances (Implemented): ${policy.implementedCompliances || 0}`);
            if (policy.totalCompliances > 0) {
              const compliantPct = Math.round((policy.implementedCompliances / policy.totalCompliances) * 100);
              console.log(`      - Compliance %: ${compliantPct}%`);
            }
          });
          if (appliedPolicies.length > 5) {
            console.log(`   ... and ${appliedPolicies.length - 5} more policies with compliance data`);
          }
        }
        console.log('');
        console.log('📊 Full Response Structure:');
        console.log('   - response.policies.applied.policies[*].totalCompliances');
        console.log('   - response.policies.applied.policies[*].implementedCompliances');
        console.log('   - response.policies.in_progress.policies[*].totalCompliances');
        console.log('   - response.policies.in_progress.policies[*].implementedCompliances');
        console.log('   - response.policies.pending.policies[*].totalCompliances');
        console.log('   - response.policies.pending.policies[*].implementedCompliances');
        console.log('   - response.policies.rejected.policies[*].totalCompliances');
        console.log('   - response.policies.rejected.policies[*].implementedCompliances');
        console.log('');
        console.log('📊 Module Metrics Data Structure:');
        console.log('   - response.moduleMetrics.policy (activePolicies, totalPolicies, approvalRate, avgApprovalTime)');
        console.log('   - response.moduleMetrics.compliance (activeCompliances, totalFindings, approvalRate, underReview)');
        console.log('   - response.moduleMetrics.risk (totalRisks, acceptedRisks, mitigatedRisks, inProgressRisks)');
        console.log('   - response.moduleMetrics.incident (totalIncidents, mttd, mttr, closureRate, resolved)');
        console.log('   - response.moduleMetrics.audit (totalAudits, completedAudits, openAudits, completionRate)');
        console.log('📊 ========================================');
        console.log('');
      }
      
      console.log('🔄 POLICY DATA UPDATE:');
      console.log('  📉 OLD policyData:', oldPolicyData);
      console.log('  📈 NEW policyData:', policyData.value);
      console.log('  ✅ Applied:', policyData.value.applied);
      console.log('  ✅ Applied Policies Count:', policyData.value.applied.policies?.length || 0);
      console.log('  ✅ Applied Policies:', policyData.value.applied.policies);
      console.log('  ✅ In Progress:', policyData.value.in_progress);
      console.log('  ✅ In Progress Policies Count:', policyData.value.in_progress.policies?.length || 0);
      console.log('  ✅ In Progress Policies:', policyData.value.in_progress.policies);
      console.log('  ✅ Pending:', policyData.value.pending);
      console.log('  ✅ Pending Policies Count:', policyData.value.pending.policies?.length || 0);
      console.log('  ✅ Pending Policies:', policyData.value.pending.policies);
      
      console.log('📊 CHART DATA (computed automatically):');
      console.log('  📈 Chart percentages:', overallComplianceData.value.datasets[0].data);
      console.log('  📈 Chart labels:', overallComplianceData.value.labels);
      console.log('  ✅ Applied percentage:', overallComplianceData.value.datasets[0].data[0], '%');
      console.log('  ✅ In Progress percentage:', overallComplianceData.value.datasets[0].data[1], '%');
      console.log('  ✅ Rejected percentage:', overallComplianceData.value.datasets[0].data[2], '%');
      
      // Verify chart data matches policyData
      const chartApplied = overallComplianceData.value.datasets[0].data[0];
      const chartInProgress = overallComplianceData.value.datasets[0].data[1];
      const chartRejected = overallComplianceData.value.datasets[0].data[2];
      
      if (Math.abs(chartApplied - policyData.value.applied.percentage) > 0.1) {
        console.warn('⚠️ WARNING: Chart Applied percentage does not match policyData!');
        console.warn(`   Chart: ${chartApplied}%, policyData: ${policyData.value.applied.percentage}%`);
      }
      if (Math.abs(chartInProgress - policyData.value.in_progress.percentage) > 0.1) {
        console.warn('⚠️ WARNING: Chart In Progress percentage does not match policyData!');
        console.warn(`   Chart: ${chartInProgress}%, policyData: ${policyData.value.in_progress.percentage}%`);
      }
      if (Math.abs(chartRejected - policyData.value.rejected.percentage) > 0.1) {
        console.warn('⚠️ WARNING: Chart Rejected percentage does not match policyData!');
        console.warn(`   Chart: ${chartRejected}%, policyData: ${policyData.value.rejected.percentage}%`);
      }
      
      // Update module metrics from database
      console.log('');
      console.log('🔧 ========================================');
      console.log('🔧 UPDATING MODULE METRICS FROM DATABASE');
      console.log('🔧 ========================================');
      console.log('📊 response.moduleMetrics exists:', !!response.moduleMetrics);
      console.log('📊 response.moduleMetrics:', response.moduleMetrics ? JSON.stringify(response.moduleMetrics, null, 2) : 'undefined');
      
      let metricsUpdated = false;
      
      if (response.moduleMetrics && response.moduleMetrics.policy) {
        policyMetrics.value = {
          activePolicies: response.moduleMetrics.policy.activePolicies || 0,
          approvalRate: response.moduleMetrics.policy.approvalRate || 0,
          totalPolicies: response.moduleMetrics.policy.totalPolicies || 0,
          avgApprovalTime: response.moduleMetrics.policy.avgApprovalTime || 0
        };
        console.log('  ✅ Policy metrics updated:', policyMetrics.value);
        metricsUpdated = true;
      } else {
        console.warn('  ⚠️ Policy metrics not found in response.moduleMetrics');
      }
      
      if (response.moduleMetrics && response.moduleMetrics.compliance) {
        complianceMetrics.value = {
          activeCompliances: response.moduleMetrics.compliance.activeCompliances || 0,
          approvalRate: response.moduleMetrics.compliance.approvalRate || 0,
          totalFindings: response.moduleMetrics.compliance.totalFindings || 0,
          underReview: response.moduleMetrics.compliance.underReview || 0
        };
        console.log('  ✅ Compliance metrics updated:', complianceMetrics.value);
        metricsUpdated = true;
      } else {
        console.warn('  ⚠️ Compliance metrics not found in response.moduleMetrics');
      }
      
      if (response.moduleMetrics && response.moduleMetrics.risk) {
        riskMetrics.value = {
          totalRisks: response.moduleMetrics.risk.totalRisks || response.moduleMetrics.risk.total || 0,
          acceptedRisks: response.moduleMetrics.risk.acceptedRisks || response.moduleMetrics.risk.accepted || 0,
          mitigatedRisks: response.moduleMetrics.risk.mitigatedRisks || response.moduleMetrics.risk.mitigated || 0,
          inProgressRisks: response.moduleMetrics.risk.inProgressRisks || response.moduleMetrics.risk.inProgress || 0,
          total: response.moduleMetrics.risk.total || response.moduleMetrics.risk.totalRisks || 0,
          active: response.moduleMetrics.risk.active || 0,
          inactive: response.moduleMetrics.risk.inactive || 0,
          accepted: response.moduleMetrics.risk.accepted || response.moduleMetrics.risk.acceptedRisks || 0,
          mitigated: response.moduleMetrics.risk.mitigated || response.moduleMetrics.risk.mitigatedRisks || 0,
          inProgress: response.moduleMetrics.risk.inProgress || response.moduleMetrics.risk.inProgressRisks || 0
        };
        console.log('  ✅ Risk metrics updated:', riskMetrics.value);
        metricsUpdated = true;
      } else {
        console.warn('  ⚠️ Risk metrics not found in response.moduleMetrics');
      }
      
      if (response.moduleMetrics && response.moduleMetrics.incident) {
        incidentMetrics.value = {
          totalIncidents: response.moduleMetrics.incident.totalIncidents || response.moduleMetrics.incident.total || 0,
          total: response.moduleMetrics.incident.total || response.moduleMetrics.incident.totalIncidents || 0,
          active: response.moduleMetrics.incident.active || 0,
          inactive: response.moduleMetrics.incident.inactive || 0,
          resolved: response.moduleMetrics.incident.resolved || 0,
          mttd: response.moduleMetrics.incident.mttd || 0,
          mttr: response.moduleMetrics.incident.mttr || 0,
          closureRate: response.moduleMetrics.incident.closureRate || 0
        };
        console.log('  ✅ Incident metrics updated:', incidentMetrics.value);
        metricsUpdated = true;
      } else {
        console.warn('  ⚠️ Incident metrics not found in response.moduleMetrics');
      }
      
      if (response.moduleMetrics && response.moduleMetrics.audit) {
        auditorMetrics.value = {
          completionRate: response.moduleMetrics.audit.completionRate || 0,
          totalAudits: response.moduleMetrics.audit.totalAudits || 0,
          active: response.moduleMetrics.audit.active || 0,
          inactive: response.moduleMetrics.audit.inactive || 0,
          openAudits: response.moduleMetrics.audit.openAudits || 0,
          completedAudits: response.moduleMetrics.audit.completedAudits || 0
        };
        console.log('  ✅ Audit metrics updated:', auditorMetrics.value);
        metricsUpdated = true;
      } else {
        console.warn('  ⚠️ Audit metrics not found in response.moduleMetrics');
      }
      
      // Check if moduleMetrics exists in response
      const hasModuleMetrics = response.moduleMetrics && Object.keys(response.moduleMetrics).length > 0;
      
      if (!metricsUpdated) {
        console.warn('⚠️ WARNING: No module metrics were updated from unified endpoint!');
        console.warn('⚠️ This may indicate the API response structure has changed or moduleMetrics is missing.');
        if (!hasModuleMetrics) {
          console.warn('⚠️ moduleMetrics object is missing or empty in response.');
        } else {
          console.warn('⚠️ moduleMetrics exists but some/all metrics are missing or have wrong structure.');
        }
        console.warn('⚠️ The fallback mechanism will try individual endpoints.');
      }
      
      console.log('🔧 ========================================');
      console.log('');
      
      // Return false if moduleMetrics is missing or no metrics were updated
      // This will trigger the fallback to individual endpoints
      if (!hasModuleMetrics || !metricsUpdated) {
        console.log('🏠 ========================================');
        console.warn('⚠️ Module metrics missing or incomplete - returning false to trigger fallback');
        console.warn('⚠️ hasModuleMetrics:', hasModuleMetrics);
        console.warn('⚠️ metricsUpdated:', metricsUpdated);
        console.log('🏠 ========================================');
        return false;
      }
      
      console.log('🏠 ========================================');
      console.log('✅ ALL DATA SUCCESSFULLY UPDATED!');
      console.log('🏠 ========================================');
      return true;
    } else {
      console.log('🏠 ========================================');
      console.warn('⚠️ FAILED - Response not successful');
      console.log('🏠 ========================================');
      console.warn('⚠️ Response:', response);
      return false;
    }
  } catch (error) {
    console.log('🏠 ========================================');
    console.error('❌ ERROR FETCHING HOMEPAGE DATA');
    console.log('🏠 ========================================');
    console.error('❌ Error:', error);
    console.error('❌ Error message:', error.message);
    console.error('❌ Error stack:', error.stack);
    return false;
  }
};

// Fetch policy data for donut chart popup (LEGACY - kept as fallback)
const fetchPolicyData = async () => {
  try {
    console.log('🔍 Fetching policy data for framework:', selectedFrameworkId.value);
    
    // Check cache first
    const cachedPolicyData = homepageDataService.getPolicyData();
    if (cachedPolicyData) {
      console.log('✅ [HomeView] Using cached policy data');
      policyData.value = cachedPolicyData;
      return;
    }
    
    // Build API URL with framework ID parameter if a specific framework is selected
    let apiUrl = API_ENDPOINTS.HOME_POLICIES_BY_STATUS_PUBLIC();
    if (selectedFrameworkId.value && selectedFrameworkId.value !== 'all') {
      apiUrl += `?frameworkId=${selectedFrameworkId.value}`;
    }
    
    const response = await axios.get(apiUrl);
    console.log('📊 API Response:', response.data);
    
    if (response.data && response.data.success) {
      // Ensure response.data.data has the correct structure
      if (response.data.data) {
        policyData.value = {
          applied: {
            policies: response.data.data.applied?.policies || [],
            count: response.data.data.applied?.count || 0,
            percentage: response.data.data.applied?.percentage || 0
          },
          in_progress: {
            policies: response.data.data.in_progress?.policies || [],
            count: response.data.data.in_progress?.count || 0,
            percentage: response.data.data.in_progress?.percentage || 0
          },
          pending: {
            policies: response.data.data.pending?.policies || [],
            count: response.data.data.pending?.count || 0,
            percentage: response.data.data.pending?.percentage || 0
          },
          rejected: {
            policies: response.data.data.rejected?.policies || [],
            count: response.data.data.rejected?.count || 0,
            percentage: response.data.data.rejected?.percentage || 0
          }
        };
        // Cache the result
        homepageDataService.setPolicyData(policyData.value);
      }
      console.log('✅ Policy data updated:', policyData.value);
      console.log('📊 Chart data (computed automatically):', overallComplianceData.value.datasets[0].data);
    } else {
      console.log('❌ API response not successful:', response.data);
    }
  } catch (error) {
    console.error('❌ Error fetching policy data:', error);
    console.error('Error details:', error.response?.data || error.message);
    // Keep default values if API fails
  }
};

// Fetch approved and active frameworks
const fetchApprovedFrameworks = async () => {
  try {
    console.log('🔍 [HomeView] Checking for cached approved frameworks...');

    // Check if prefetch is in progress or cache is available
    if (!window.homepageDataFetchPromise && !homepageDataService.hasApprovedFrameworksCache()) {
      console.log('🚀 [HomeView] Starting homepage prefetch (user navigated directly)...');
      window.homepageDataFetchPromise = homepageDataService.fetchAllHomepageData();
    }

    // Wait for prefetch if it's in progress
    if (window.homepageDataFetchPromise) {
      console.log('⏳ [HomeView] Waiting for homepage prefetch to complete...');
      try {
        await window.homepageDataFetchPromise;
        console.log('✅ [HomeView] Homepage prefetch completed');
      } catch (prefetchError) {
        console.warn('⚠️ [HomeView] Homepage prefetch failed, will fetch directly from API', prefetchError);
      }
    }

    // Use cached data if available
    if (homepageDataService.hasApprovedFrameworksCache()) {
      console.log('✅ [HomeView] Using cached approved frameworks');
      const cachedFrameworks = homepageDataService.getData('approvedFrameworks') || [];
      approvedFrameworks.value = cachedFrameworks.map(fw => ({ ...fw }));
      console.log('✅ DEBUG: Approved frameworks loaded:', approvedFrameworks.value.length);
      console.log('📝 DEBUG: Available frameworks:', approvedFrameworks.value.map(f => `${f.FrameworkName} (ID: ${f.FrameworkId})`));
      return;
    }

    // Fallback: Fetch directly from API
    console.log('⚠️ [HomeView] No cached data found, fetching approved frameworks from API...');
    const response = await axios.get(API_ENDPOINTS.FRAMEWORKS_APPROVED_ACTIVE);
    console.log('📊 DEBUG: Approved frameworks response:', response.data);
    
    if (response.data && response.data.success) {
      approvedFrameworks.value = response.data.data;
      // Update cache for subsequent loads
      homepageDataService.setData('approvedFrameworks', response.data.data);
      console.log('✅ DEBUG: Approved frameworks loaded:', approvedFrameworks.value.length);
      console.log('📝 DEBUG: Available frameworks:', approvedFrameworks.value.map(f => `${f.FrameworkName} (ID: ${f.FrameworkId})`));
    } else {
      console.log('❌ DEBUG: No approved frameworks found');
      approvedFrameworks.value = [];
    }
  } catch (error) {
    console.error('❌ DEBUG: Error fetching approved frameworks:', error);
    // Set empty array on error
    approvedFrameworks.value = [];
  }
};

// Check currently selected framework from session
const checkSelectedFramework = async () => {
  try {
    console.log('🔍 DEBUG: Checking currently selected framework...');
    const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED);
    console.log('📊 DEBUG: Selected framework response:', response.data);
    
    if (response.data && response.data.success && response.data.frameworkId) {
      selectedFrameworkId.value = response.data.frameworkId;
      console.log('✅ DEBUG: Previously selected framework found:', response.data.frameworkId);
      console.log('👤 DEBUG: Associated user ID:', response.data.userId);
    } else {
      console.log('ℹ️ DEBUG: No previously selected framework found - showing "All" as active');
      selectedFrameworkId.value = 'all';
    }
  } catch (error) {
    console.error('❌ DEBUG: Error checking selected framework:', error);
    selectedFrameworkId.value = 'all';
  }
};

// Handle dropdown change
const handleFrameworkDropdownChange = async (event) => {
  const selectedValue = event.target.value;
  
  if (selectedValue === 'all') {
    await selectAllFrameworks();
  } else {
    const framework = approvedFrameworks.value.find(f => 
      String(f.FrameworkId) === String(selectedValue) || 
      f.FrameworkId === parseInt(selectedValue)
    );
    if (framework) {
      await selectFramework(framework);
    }
  }
};

// Handle framework selection
const selectFramework = async (framework) => {
  console.log('');
  console.log('🎯 ================================================');
  console.log('🎯 FRAMEWORK SELECTION CLICKED');
  console.log('🎯 ================================================');
  console.log('📊 Selected framework object:', framework);
  console.log('🆔 Framework ID:', framework.FrameworkId);
  console.log('📝 Framework Name:', framework.FrameworkName);
  console.log('📄 Framework Description:', framework.FrameworkDescription);
  
  try {
    // Set selected framework in local UI state
    selectedFrameworkId.value = framework.FrameworkId;
    console.log('✅ DEBUG: Framework set in UI state - selectedFrameworkId.value:', selectedFrameworkId.value);
    
    // Persist selection for cross-page use (kept for backward compatibility)
    try {
      localStorage.setItem('selectedFrameworkId', String(framework.FrameworkId));
      localStorage.setItem('frameworkId', String(framework.FrameworkId));
      if (framework.FrameworkName) {
        localStorage.setItem('framework_name', framework.FrameworkName);
      }
    } catch (e) {
      console.warn('⚠️ Unable to write framework selection to localStorage:', e);
    }
    
    // Test the content lookup immediately
    const testContent = getFrameworkContent(framework.FrameworkName);
    console.log('🧪 DEBUG: Test content lookup result:', testContent.frameworkName);
    
    // Update Vuex store (this will also save to backend session)
    await store.dispatch('framework/setFramework', {
      id: framework.FrameworkId,
      name: framework.FrameworkName
    });
    
    console.log('✅ Framework successfully stored in Vuex store and backend session');
    console.log('🎉 Framework selection completed successfully');
    console.log('🎯 ================================================');
    console.log('');
    
    // The watch() will automatically trigger and fetch data
    console.log('⏳ Waiting for watch() to trigger data fetch...');
    
  } catch (error) {
    console.error('❌ Error selecting framework:', error);
    console.error('📝 Error details:', error.response?.data || error.message);
    console.log('🎯 ================================================');
    
    // Reset UI state on error
    selectedFrameworkId.value = null;
  }
};

// Handle framework selection by ID (for framework cards)
const selectFrameworkById = async (frameworkId) => {
  console.log('🎯 Selecting framework by ID:', frameworkId);
  
  // First try to find in approvedFrameworks
  let framework = approvedFrameworks.value.find(f => 
    f.FrameworkId === frameworkId || 
    String(f.FrameworkId) === String(frameworkId)
  );
  
  // If not found, try to find in allFrameworksList
  if (!framework && allFrameworksList.value.length > 0) {
    const frameworkData = allFrameworksList.value.find(f => 
      f.id === frameworkId || 
      String(f.id) === String(frameworkId)
    );
    
    // Convert framework data to match the expected format
    if (frameworkData) {
      framework = {
        FrameworkId: frameworkData.id,
        FrameworkName: frameworkData.name,
        FrameworkDescription: frameworkData.description
      };
    }
  }
  
  if (framework) {
    await selectFramework(framework);
  } else {
    console.error('❌ Framework not found with ID:', frameworkId);
  }
};

// Watch for framework changes and update content
watch(selectedFrameworkId, async (newFrameworkId, oldFrameworkId) => {
  if (newFrameworkId !== oldFrameworkId) {
    console.log('');
    console.log('🔄 ================================================');
    console.log('🔄 WATCH TRIGGERED - FRAMEWORK CHANGED');
    console.log('🔄 ================================================');
    console.log('🔄 Old Framework ID:', oldFrameworkId);
    console.log('🔄 New Framework ID:', newFrameworkId);
    console.log('📦 Current framework content:', currentFrameworkContent.value.frameworkName);
    console.log('🔄 ================================================');
    console.log('');
    
    // Try to refresh data from unified endpoint first
    console.log('🔄 Calling fetchDynamicHomepageData()...');
    const success = await fetchDynamicHomepageData();
    
    console.log('');
    console.log('🔄 ================================================');
    console.log('🔄 WATCH RESULT');
    console.log('🔄 ================================================');
    console.log('✅ Success:', success);
    
    // If unified endpoint fails, fall back to individual endpoint
    if (!success) {
      console.log('⚠️ Unified endpoint failed - falling back to individual policy endpoint');
      await fetchPolicyData();
    }
    
    console.log('🔄 ================================================');
    console.log('');
    
    // Reinitialize AOS animations for smooth transitions
    setTimeout(() => {
      AOS.refresh();
    }, 100);
  }
});

// Handle "All Frameworks" selection
const selectAllFrameworks = async () => {
  console.log('🎯 DEBUG: All frameworks selection started');
  
  try {
    // Set "all" as selected framework in UI
    selectedFrameworkId.value = 'all';
    console.log('✅ DEBUG: All frameworks set in UI state');
    
    // Clear any persisted framework selection to avoid stale re-selection
    try {
      localStorage.removeItem('selectedFrameworkId');
      localStorage.removeItem('frameworkId');
      localStorage.removeItem('framework_name');
      // For safety, also blank potential sessionStorage leftovers
      sessionStorage.removeItem('selectedFrameworkId');
      sessionStorage.removeItem('frameworkId');
    } catch (e) {
      console.warn('⚠️ Unable to clear framework selection from storage:', e);
    }
    
    // Reset Vuex store (this will clear backend session)
    await store.dispatch('framework/resetFramework');
    
    console.log('✅ DEBUG: All frameworks set in Vuex store and backend session cleared');
    console.log('⏳ Waiting for watch() to trigger data fetch...');
    console.log('🎉 DEBUG: All frameworks selection completed successfully');
    
  } catch (error) {
    console.error('❌ DEBUG: Error selecting all frameworks:', error);
    console.error('📝 DEBUG: Error details:', error.response?.data || error.message);
    
    // Reset UI state on error
    selectedFrameworkId.value = null;
  }
};

// Fetch all dashboard metrics
const fetchAllDashboardMetrics = async () => {
  try {
    // Check if user is authenticated
    const accessToken = localStorage.getItem('access_token');
    const userId = localStorage.getItem('user_id');
    const isLoggedIn = localStorage.getItem('is_logged_in') === 'true';
    const isAuthenticated = !!(accessToken && userId && isLoggedIn);
   
    console.log('🚀 DEBUG: Starting to fetch all dashboard metrics...', { isAuthenticated });
   
    // First, fetch frameworks and check selected framework
    await Promise.all([
      fetchApprovedFrameworks(),
      checkSelectedFramework()
    ]);
    
    // ====================================================================
    // PHASE 1: Try the new unified homepage endpoint first
    // ====================================================================
    console.log('🆕 Attempting to fetch from unified homepage endpoint...');
    const success = await fetchDynamicHomepageData();
    
    if (success) {
      console.log('✅ Successfully loaded data from unified homepage endpoint');
      console.log('✅ Module metrics should be available now');
      // All data (donut + module cards) loaded from unified endpoint
      // If moduleMetrics were missing, fetchDynamicHomepageData would have returned false
      return;
    }
    
    // ====================================================================
    // FALLBACK: Use individual endpoints if unified endpoint fails or metrics are missing
    // ====================================================================
    console.log('⚠️ Unified endpoint failed or moduleMetrics missing, falling back to individual endpoints...');
   
    if (isAuthenticated) {
      // User is authenticated - fetch all real data
      await Promise.all([
        fetchPolicyMetrics(),
        fetchComplianceMetrics(),
        fetchRiskMetrics(),
        fetchIncidentMetrics(),
        fetchAuditorMetrics(),
        fetchPolicyData(),
        fetchApprovedFrameworks(),
        checkSelectedFramework()
      ]);
      console.log('✅ DEBUG: All dashboard metrics fetched successfully (fallback mode)');
    } else {
      // User is NOT authenticated - only fetch public data
      console.log('ℹ️ DEBUG: User not authenticated - fetching only public data');
      await Promise.all([
        fetchPolicyData(),
        fetchApprovedFrameworks(),
        checkSelectedFramework()
      ]);
      
      console.log('✅ DEBUG: Public dashboard metrics fetched successfully (fallback mode)');
    }
  } catch (error) {
    console.error('❌ DEBUG: Error fetching dashboard metrics:', error);
  }
};
 

onMounted(() => {
  handleResize();
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', handleResize);
  }

  // Initialize AOS
  AOS.init({
    duration: 800,
    easing: 'ease-out-cubic',
    once: true,
    offset: 100,
  });
  
  // Get user data
  const userData = localStorage.getItem('user');
  if (userData) {
    user.value = JSON.parse(userData);
  }
  
  // Fetch dashboard metrics
  fetchAllDashboardMetrics();
  
  // Load framework selection from Vuex store
  const storeFramework = store.state.framework.selectedFrameworkId;
  if (storeFramework && storeFramework !== 'all') {
    selectedFrameworkId.value = storeFramework;
    console.log('🔄 HomeView: Loaded framework from Vuex store:', storeFramework);
  }
  // ==========================================
  // NEW FEATURE: Prefetch ALL Incident Data on Home Page Load
  // ==========================================
  // This will fetch and cache all incident-related data in the background
  // so that when the user navigates to incident pages, data loads instantly!
  console.log('🚀 [HomeView] Starting incident data prefetch...');
  
  // Store the promise globally so other components can wait for it
  const incidentPrefetchPromise = incidentDataService.fetchAllIncidentData()
    .then((result) => {
      incidentsData.value = incidentDataService.getData('incidents') || [];
      incidentCount.value = incidentsData.value.length;
      const auditFindingsCount = result.auditFindingsTotal || 0;
      console.log(`✅ [HomeView] Incident prefetch complete: ${incidentCount.value} incidents, ${auditFindingsCount} audit findings`);
    })
    .catch(() => {
      incidentsData.value = [];
      incidentCount.value = 0;
      console.log('❌ [HomeView] Incident prefetch failed');
    });

  window.incidentDataFetchPromise = incidentPrefetchPromise;
  
  // ==========================================
  // NEW FEATURE: Prefetch ALL Risk Data on Home Page Load
  // ==========================================
  // This will fetch and cache all risk-related data in the background
  // so that when the user navigates to risk pages, data loads instantly!
  console.log('🚀 [HomeView] Starting risk data prefetch...');
  
  // Store the promise globally so other components can wait for it
  const riskPrefetchPromise = riskDataService.fetchAllRiskData()
    .then(() => {
      risksData.value = riskDataService.getData('risks') || [];
      riskCount.value = risksData.value.length;
      console.log(`✅ [HomeView] Risk data prefetch complete - Total risks: ${riskCount.value}`);
    })
    .catch((error) => {
      console.error('❌ [HomeView] Risk data prefetch failed:', error);
      risksData.value = [];
      riskCount.value = 0;
    });

  window.riskDataFetchPromise = riskPrefetchPromise;
  
  // ==========================================
  // NEW FEATURE: Prefetch ALL Compliance Data on Home Page Load
  // ==========================================
  // This will fetch and cache all compliance-related data in the background
  // so that when the user navigates to compliance pages, data loads instantly!
  console.log('🚀 [HomeView] Starting compliance data prefetch...');
  
  // Store the promise globally so other components can wait for it
  const compliancePrefetchPromise = complianceDataService.fetchAllComplianceData()
    .then(() => {
      const frameworks = complianceDataService.getData('frameworks') || [];
      const compliances = complianceDataService.getData('compliances') || [];
      console.log(`✅ [HomeView] Compliance data prefetch complete - Total frameworks: ${frameworks.length}, Total compliances: ${compliances.length}`);
    })
    .catch((error) => {
      console.error('❌ [HomeView] Compliance data prefetch failed:', error);
    });

  window.complianceDataFetchPromise = compliancePrefetchPromise;
  
  // ==========================================
  // NEW FEATURE: Prefetch ALL Auditor Data on Home Page Load
  // ==========================================
  // This will fetch and cache all auditor-related data in the background
  // so that when the user navigates to auditor pages, data loads instantly!
  console.log('🚀 [HomeView] Starting auditor data prefetch...');
  
  // Store the promise globally so other components can wait for it
  const auditorPrefetchPromise = auditorDataService.fetchAllAuditorData()
    .then(() => {
      const audits = auditorDataService.getData('audits') || [];
      const businessUnits = auditorDataService.getData('businessUnits') || [];
      console.log(`✅ [HomeView] Auditor data prefetch complete - Total audits: ${audits.length}, Total business units: ${businessUnits.length}`);
    })
    .catch((error) => {
      console.error('❌ [HomeView] Auditor data prefetch failed:', error);
    });

  window.auditorDataFetchPromise = auditorPrefetchPromise;
  
  // ==========================================
  // NEW FEATURE: Prefetch ALL Event Data on Home Page Load
  // ==========================================
  // This will fetch and cache all event-related data in the background
  // so that when the user navigates to event pages, data loads instantly!
  console.log('🚀 [HomeView] Starting event data prefetch...');
  
  // Store the promise globally so other components can wait for it
  const eventPrefetchPromise = eventDataService.fetchAllEventData()
    .then(() => {
      const events = eventDataService.getData('events') || [];
      console.log(`✅ [HomeView] Event data prefetch complete - Total events: ${events.length}`);
    })
    .catch((error) => {
      console.error('❌ [HomeView] Event data prefetch failed:', error);
    });

  window.eventDataFetchPromise = eventPrefetchPromise;
  
  // ==========================================
  // NEW FEATURE: Prefetch ALL Policy Data on Home Page Load
  // ==========================================
  console.log('🚀 [HomeView] Starting policy data prefetch...');

  const policyPrefetchPromise = policyDataService.fetchAllPolicyData()
    .then(() => {
      const policyFrameworks = policyDataService.getAllPoliciesFrameworks() || [];
      console.log(`✅ [HomeView] Policy data prefetch complete - Total policy frameworks: ${policyFrameworks.length}`);
    })
    .catch((error) => {
      console.error('❌ [HomeView] Policy data prefetch failed:', error);
    });

  window.policyDataFetchPromise = policyPrefetchPromise;
  
  // ==========================================
  // NEW FEATURE: Prefetch ALL Tree Data on Home Page Load
  // ==========================================
  console.log('🚀 [HomeView] Starting tree data prefetch...');
  
  const treePrefetchPromise = treeDataService.fetchAllTreeData()
    .then(() => {
      const frameworks = treeDataService.getData('frameworks') || [];
      console.log(`✅ [HomeView] Tree data prefetch complete - Total frameworks: ${frameworks.length}`);
    })
    .catch((error) => {
      console.error('❌ [HomeView] Tree data prefetch failed:', error);
    });

  window.treeDataFetchPromise = treePrefetchPromise;
  
  // ==========================================
  // NEW FEATURE: Prefetch ALL Document Data on Home Page Load
  // ==========================================
  console.log('🚀 [HomeView] Starting document data prefetch...');
  
  const documentPrefetchPromise = documentDataService.fetchAllDocumentData()
    .then(() => {
      const documents = documentDataService.getData('documents') || [];
      console.log(`✅ [HomeView] Document data prefetch complete - Total documents: ${documents.length}`);
    })
    .catch((error) => {
      console.error('❌ [HomeView] Document data prefetch failed:', error);
    });

  window.documentDataFetchPromise = documentPrefetchPromise;
  
  // ==========================================
  // NEW FEATURE: Prefetch ALL Integrations Data on Home Page Load
  // ==========================================
  console.log('🚀 [HomeView] Starting integrations data prefetch...');
  
  const integrationsPrefetchPromise = integrationsDataService.fetchAllIntegrationData()
    .then(() => {
      const applications = integrationsDataService.getData('applications') || [];
      console.log(`✅ [HomeView] Integrations data prefetch complete - Total applications: ${applications.length}`);
    })
    .catch((error) => {
      console.error('❌ [HomeView] Integrations data prefetch failed:', error);
    });

  window.integrationsDataFetchPromise = integrationsPrefetchPromise;
  
  // ==========================================
  // NEW FEATURE: Prefetch ALL Homepage Data on Home Page Load
  // ==========================================
  console.log('🚀 [HomeView] Starting homepage data prefetch...');

  const homepagePrefetchPromise = homepageDataService.fetchAllHomepageData()
    .then(() => {
      const approvedFrameworks = homepageDataService.getData('approvedFrameworks') || [];
      console.log(`✅ [HomeView] Homepage data prefetch complete - Total approved frameworks: ${approvedFrameworks.length}`);
    })
    .catch((error) => {
      console.error('❌ [HomeView] Homepage data prefetch failed:', error);
    });

  window.homepageDataFetchPromise = homepagePrefetchPromise;
  
  // Add click outside handler for popup
  document.addEventListener('click', (event) => {
    if (showPolicyPopup.value && !event.target.closest('.policy-popup')) {
      showPolicyPopup.value = false;
    }
  });
});

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', handleResize);
  }
});

// Watch for Vuex store framework changes
watch(
  () => store.state.framework.selectedFrameworkId,
  (newFrameworkId) => {
    if (newFrameworkId !== selectedFrameworkId.value) {
      console.log('🔄 HomeView: Vuex store framework changed to:', newFrameworkId);
      selectedFrameworkId.value = newFrameworkId || 'all';
    }
  }
);
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* Global Styles */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.home-container {
  font-family: 'Inter', sans-serif;
  background: white;
  overflow-x: hidden;
  position: relative;
  margin-bottom: -39px;
  z-index: 1;
  box-sizing: border-box;
}

/* Main Content */
.main-content {
  padding-top: 0;
  width: 95%;
  box-sizing: border-box;
}

/* Hero Text Container */
.hero-text {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  min-width: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  flex: 0 1 50%;
  position: relative;
  contain: layout style;
}

/* Hero Section */
.hero-section {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
  left: 0;
  right: 0;
  margin-left: 0;
  margin-right: 0;
}

.hero-background {
  position: absolute;
  inset: 0;
  background: #ffffff;
}

.hero-gradient {
  position: absolute;
  inset: 0;
  background: transparent;
}

.floating-elements {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.floating-element {
  position: absolute;
  width: 60px;
  height: 60px;
  background: rgba(30, 64, 175, 0.08);
  border-radius: 50%;
  animation: float 6s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(180deg); }
}

.hero-content {
  position: relative;
  z-index: 10;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4rem;
  align-items: start;
  justify-items: start;
  max-width: 1400px;
  margin-left: 0;
  margin-right: auto;
  padding-left: 1rem;
  padding-right: 2rem;
  padding-top: 2rem;
  padding-bottom: 2rem;
  width: 100%;
  box-sizing: border-box;
  grid-auto-flow: row;
  grid-template-rows: auto;
  left: 0;
  right: 0;
  contain: layout;
}

.hero-content > * {
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
  position: relative;
  justify-self: stretch;
  align-self: start;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(30, 64, 175, 0.1);
  border: 1px solid rgba(30, 64, 175, 0.2);
  color: #1e40af;
  padding: 0.5rem 1rem;
  border-radius: 50px;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 1.5rem;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 800;
  line-height: 1.1;
  color: #1f2937;
  margin-bottom: 1.5rem;
  margin-left: 0;
  margin-right: 0;
  padding-left: 0;
  padding-right: 0;
  letter-spacing: -0.02em;
  word-wrap: break-word;
  overflow-wrap: anywhere;
  max-width: 100%;
  width: 100%;
  box-sizing: border-box;
  display: block;
  hyphens: auto;
  overflow: hidden;
  position: relative;
  flex-shrink: 1;
  contain: layout style;
}

.hero-title .gradient-text {
  display: inline;
  word-wrap: break-word;
  overflow-wrap: anywhere;
  max-width: 100%;
  white-space: normal;
}

.gradient-text {
  background: linear-gradient(135deg, #1e40af, #3b82f6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-description {
  font-size: 1.25rem;
  color: #000000 !important;
  line-height: 1.6;
  margin-bottom: 2rem;
  max-width: 100%;
  width: 100%;
  word-wrap: break-word;
  overflow-wrap: anywhere;
  box-sizing: border-box;
  overflow: hidden;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2rem;
  margin-bottom: 2.5rem;
}

.stat-item {
  text-align: center;
  padding: 1.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: #1e40af;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

/* Hero Visual */
.hero-visual {
  position: relative;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  min-width: 0;
  flex: 0 1 50%;
  align-self: start;
  overflow: hidden;
  contain: layout style;
}

.dashboard-preview {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: #f8fafc;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.preview-controls {
  display: flex;
  gap: 0.5rem;
}

.control {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.control.red { background: #ef4444; }
.control.yellow { background: #f59e0b; }
.control.green { background: #10b981; }

.preview-title {
  font-weight: 600;
  color: #374151;
}

.preview-content {
  padding: 1.5rem;
}

.compliance-overview {
  margin-bottom: 1.5rem;
}



.compliance-progress-section {
  margin-bottom: 1.5rem;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.progress-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.progress-percentage {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e40af;
}

.progress-bar-container {
  margin-bottom: 1.5rem;
}

.progress-bar {
  width: 100%;
  height: 12px;
  background: #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #1e40af);
  border-radius: 6px;
  transition: width 0.5s ease-in-out;
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

.compliance-details-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.detail-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.detail-value {
  font-size: 0.875rem;
  color: #1f2937;
  font-weight: 600;
}

.preview-metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.metric-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.metric-icon.blue { background: #1e40af; }
.metric-icon.green { background: #10b981; }
.metric-icon.orange { background: #f59e0b; }

.metric-data {
  flex: 1;
}

.metric-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
}

.metric-title {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
  margin-top: 0.25rem;
}

.metric-change {
  font-size: 0.75rem;
  font-weight: 600;
}

.metric-change.positive { color: #10b981; }
.metric-change.negative { color: #ef4444; }

/* ISO Compliance Section */
.iso-compliance-section {
  padding: 2rem 2rem 2rem 1rem;
  max-width: 1400px;
  margin-left: 0;
  margin-right: auto;
  width: 100%;
  box-sizing: border-box;
}

.section-header {
  display: block;
  text-align: left;
  margin-bottom: 1rem;
}

.section-badge {
  display: inline-block;
  background: rgba(30, 64, 175, 0.1);
  color: #1e40af;
  padding: 0.5rem 1rem;
  border-radius: 50px;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.section-title {
  display: block;
  font-size: 2.5rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.5rem;
  letter-spacing: -0.02em;
  border-bottom: none;
  text-decoration: none;
  background: none;
  position: relative;
}

.section-title::after {
  content: none;
  display: none;
}

.section-description {
  display: block;
  font-size: 1.125rem;
  color: #6b7280;
  line-height: 1.6;
  max-width: none;
  margin: 0;
  border-top: none;
  text-decoration: none;
  text-align: left;
}

.compliance-overview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: stretch;
}

.compliance-chart {
  background: white;
  padding: 1.5rem;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  z-index: 2;
}

.compliance-chart h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1rem;
  text-align: left;
}

.chart-container {
  flex: 1;
  min-height: 200px;
  max-height: 250px;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-legend {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 1.5rem;
  margin-top: 1rem;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: #374151;
  padding: 0.25rem 0.5rem;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: all 0.2s ease;
}

.legend-item:hover {
  background: rgba(255, 255, 255, 1);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}

.legend-color.applied { background: #3b82f6; }
.legend-color.in-progress { background: #f59e0b; }
.legend-color.pending { background: #ef4444; }
.legend-color.rejected { background: #ef4444; }

.compliance-features {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.compliance-features h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1.5rem;
  text-align: left;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  flex: 1;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.feature-icon.blue { background: #1e40af; }
.feature-icon.green { background: #10b981; }
.feature-icon.purple { background: #7c3aed; }
.feature-icon.orange { background: #f59e0b; }

.feature-content {
  flex: 1;
}

.feature-title {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.feature-description {
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.5;
}

/* Control Domains Section */
.control-domains-section {
  padding: 2rem 2rem 2rem 1rem;
  max-width: 1400px;
  margin-left: 0;
  margin-right: auto;
  width: 100%;
  box-sizing: border-box;
}

.domains-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

/* All Frameworks Compliance Summary */
.all-frameworks-compliance {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem 0;
}

.compliance-summary-card {
  background: white;
  padding: 3rem;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.05);
  max-width: 600px;
  width: 100%;
  text-align: center;
}

.compliance-summary-header {
  margin-bottom: 2rem;
}

.compliance-summary-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.compliance-summary-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.compliance-percentage-large {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.percentage-value {
  font-size: 4rem;
  font-weight: 700;
  color: #10b981;
  line-height: 1;
}

.percentage-label {
  font-size: 1.25rem;
  color: #6b7280;
  font-weight: 500;
}

.compliance-stats-summary {
  display: flex;
  justify-content: space-around;
  gap: 2rem;
  padding-top: 2rem;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.stat-item .stat-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.stat-item .stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
}

/* Policy Card Styles */
.policy-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.policy-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.12);
}

.domain-card {
  background: white;
  padding: 2rem;
  border-radius: 0;
  box-shadow: none;
  border: none;
  border-right: 1px solid rgba(0, 0, 0, 0.08);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

/* Remove right border from every 4th card (last in row) */
.domains-grid .domain-card:nth-child(4n) {
  border-right: none;
}

/* Remove bottom border from last row */
.domains-grid .domain-card:nth-last-child(-n+4) {
  border-bottom: none;
}

/* Ensure last card in grid has no right border */
.domains-grid .domain-card:last-child {
  border-right: none;
  border-bottom: none;
}

.domain-card:hover {
  background: #f8fafc;
  z-index: 1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.domain-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.domain-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.domain-icon.completed {
  background: #3b82f6;
}

.domain-icon.in-progress {
  background: #f59e0b;
}

.domain-icon.pending {
  background: #6b7280;
}

.domain-info {
  flex: 1;
}

.domain-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.75rem;
}

.domain-progress {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #1e40af);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1e40af;
  min-width: 40px;
}

.domain-details {
  border-top: 1px solid #e5e7eb;
  padding-top: 1.5rem;
  margin-top: auto;
}

.domain-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}

.stat {
  text-align: center;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 8px;
}

.stat-label {
  display: block;
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.stat-value {
  display: block;
  font-size: 1.125rem;
  font-weight: 700;
  color: #1f2937;
}

.domain-description {
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.5;
}

/* Remaining Controls Section */
.remaining-controls-section {
  padding: 2rem 2rem 2rem 1rem;
  max-width: 1400px;
  margin-left: 0;
  margin-right: auto;
  width: 100%;
  box-sizing: border-box;
}

.controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 2rem;
}

.control-card {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.control-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.12);
}

.control-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.control-priority {
  padding: 0.25rem 0.75rem;
  border-radius: 50px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.control-priority.High {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.control-priority.Medium {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
}

.control-domain {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.control-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.75rem;
}

.control-description {
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.5;
  margin-bottom: 1.5rem;
}

.control-metrics {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.metric:last-child {
  border-bottom: none;
}

.metric-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.metric-value {
  font-size: 0.875rem;
  color: #1f2937;
  font-weight: 600;
}

.control-actions {
  display: flex;
  gap: 1rem;
}

.btn-primary {
  flex: 1;
  background: #1e40af;
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  background: #1d4ed8;
  transform: translateY(-1px);
}

.btn-secondary {
  flex: 1;
  background: white;
  color: #1e40af;
  border: 1px solid #1e40af;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: #1e40af;
  color: white;
}

/* Benefits Section */
.benefits-section {
  padding: 2rem 2rem 2rem 1rem;
  max-width: 1400px;
  margin-left: 0;
  margin-right: auto;
  width: 100%;
  box-sizing: border-box;
}

.benefits-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.benefit-card {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  text-align: left;
}

.benefit-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.12);
}

.benefit-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin: 0 auto 1.5rem;
}

.benefit-icon.blue { background: #1e40af; }
.benefit-icon.green { background: #10b981; }
.benefit-icon.purple { background: #7c3aed; }
.benefit-icon.orange { background: #f59e0b; }

.benefit-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.75rem;
}

.benefit-description {
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.5;
}

/* CTA Section */
.cta-section {
  position: relative;
  padding: 2rem 2rem 2rem 1rem;
  overflow: hidden;
  width: 100%;
  box-sizing: border-box;
}

.cta-background {
  position: absolute;
  inset: 0;
  background: #ffffff;
}

.cta-gradient {
  position: absolute;
  inset: 0;
  background: transparent;
}

.cta-content {
  position: relative;
  z-index: 10;
  text-align: left;
  max-width: none;
  margin: 0;
}

.cta-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 1rem;
  line-height: 1.2;
  white-space: normal;
  border-bottom: none;
  background: none;
  position: relative;
}

.cta-title::after {
  content: none;
  display: none;
}

.cta-description {
  font-size: 1.125rem;
  color: #64748b;
  line-height: 1.6;
  margin-bottom: 2.5rem;
  max-width: none;
  width: 100%;
}

.cta-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.cta-primary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: white;
  color: #1e40af;
  border: none;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cta-primary:hover {
  background: #f8fafc;
  transform: translateY(-2px);
  box-shadow: 0 10px 40px rgba(255, 255, 255, 0.3);
}

.cta-secondary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: transparent;
  color: #1e40af;
  border: 2px solid #1e40af;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cta-secondary:hover {
  background: #1e40af;
  color: white;
  transform: translateY(-2px);
}

/* Footer Section */
.footer-section {
  position: relative;
  padding: 2rem 2rem 2rem 1rem;
  overflow: hidden;
  width: 250%;
  box-sizing: border-box;
}

.footer-background {
  position: absolute;
  inset: 0;
  background: #f8fafc;
}

.footer-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, 
    rgba(248, 250, 252, 0.9) 0%, 
    rgba(241, 245, 249, 0.8) 100%);
}

.footer-content {
  position: relative;
  z-index: 10;
  max-width: 1400px;
  width: 100%;
  margin-left: 0;
  margin-right: auto;
  box-sizing: border-box;
}

.footer-main {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  margin-bottom: 4rem;
  align-items: flex-start;
}

.footer-brand {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  align-items: flex-start;
  text-align: left;
  max-width: 520px;
}

.footer-logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-circle {
  width: 200px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
  overflow: visible;
  padding: 0;
  margin: 0 0 20px 0;
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: transparent;
  border: none;
  box-shadow: none;
  border-radius: 0;
  display: block;
  margin: 0;
  padding: 0;
  line-height: 0;
}

.logo-text h3 {
  font-size: 1.875rem;
  font-weight: 800;
  color: #1f2937;
  line-height: 1;
}

.logo-text span {
  font-size: 0.875rem;
  color: rgba(31, 41, 55, 0.8);
}

.footer-description {
  font-size: 1rem;
  color: rgba(31, 41, 55, 0.8);
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.footer-social {
  display: flex;
  gap: 1rem;
}

.social-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  transition: all 0.3s ease;
}

.social-link:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(4, minmax(90px, 1fr));
  gap: 1rem;
  width: 100%;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.footer-links .footer-column:first-child {
  margin-left: 2.5rem;
}

.footer-links .footer-column:nth-child(2) {
  margin-left: -2rem;
}

.footer-links .footer-column:nth-child(3) {
  margin-left: -5rem;
}

.footer-links .footer-column:nth-child(4) {
  margin-left: -5rem;
}

.footer-column h4 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 1.5rem;
}

.footer-column ul {
  list-style: none;
}

.footer-column li {
  margin-bottom: 0.75rem;
}

.footer-column a {
  color: rgba(31, 41, 55, 0.7);
  text-decoration: none;
  font-size: 0.85rem;
  transition: color 0.3s ease;
}

.footer-column a:hover {
  color: #1f2937;
}

@media (max-width: 1200px) {
  .footer-links {
    grid-template-columns: repeat(3, minmax(180px, 1fr));
  }
}

.footer-bottom {
  border-top: 1px solid rgba(31, 41, 55, 0.1);
  padding-top: 2rem;
  text-align: left;
}

.footer-bottom-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.footer-copyright {
  font-size: 0.875rem;
  color: rgba(31, 41, 55, 0.7);
}

.footer-certifications {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.certification-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(31, 41, 55, 0.1);
  color: #1f2937;
  padding: 0.5rem 1rem;
  border-radius: 50px;
  font-size: 0.75rem;
  font-weight: 500;
}

.certification-badge svg {
  width: 16px;
  height: 16px;
  color: #10b981; /* Green color for certifications */
}

/* Contact Section */
.footer-contact {
  width: 100%;
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 1px solid rgba(31, 41, 55, 0.1);
  text-align: left;
}

.footer-contact .contact-header h4 {
  font-size: 1rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 1rem;
  letter-spacing: 0.05em;
}

.footer-contact .contact-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: flex-start;
}

.footer-contact .contact-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  transition: all 0.3s ease;
  cursor: pointer;
}

.footer-contact .contact-item:hover {
  transform: translateX(5px);
}

.footer-contact .contact-item svg {
  color: rgba(31, 41, 55, 0.8);
  flex-shrink: 0;
}

.footer-contact .contact-link {
  color: rgba(31, 41, 55, 0.8);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: color 0.3s ease;
}

.footer-contact .contact-link:hover {
  color: #1f2937;
  text-decoration: underline;
}

/* Module Dashboards Section */
.module-dashboards-section {
  padding: 2rem 2rem 2rem 1rem;
  max-width: 1400px;
  margin-left: 0;
  margin-right: auto;
  width: 100%;
  box-sizing: border-box;
}

.module-dashboards-section .section-header {
  display: block;
  text-align: left;
  margin-bottom: 1rem;
}

.module-dashboards-section .section-title {
  display: block;
  margin-bottom: 0.5rem;
}

.module-dashboards-section .section-description {
  display: block;
  font-size: 1.125rem;
  color: #6b7280;
  line-height: 1.6;
  max-width: none;
  margin: 0;
  border-top: none;
  text-decoration: none;
  text-align: left;
}

  /* Basel Home KPIs */
  .basel-home-section { padding: 2rem 2rem 2rem 1rem; max-width: 1400px; margin-left: 0; margin-right: auto; width: 100%; box-sizing: border-box; }
  .basel-home-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 2rem; }
  .alert-panel { background: white; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.05); padding: 1.5rem; }
  .alert-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
  .counters .ctr { margin-left: 0.5rem; font-size: 0.8rem; font-weight: 700; }
  .ctr.critical { color: #ef4444; }
  .ctr.high { color: #f59e0b; }
  .ctr.medium { color: #3b82f6; }
  .alert-list { display: flex; flex-direction: column; gap: 0.75rem; }
  .alert-item { display: grid; grid-template-columns: 100px 1fr 80px; gap: 0.75rem; align-items: center; padding: 0.75rem; border: 1px solid #eef2f7; border-radius: 8px; }
  .alert-item .alert-badge { font-weight: 800; font-size: 0.75rem; padding: 0.25rem 0.5rem; border-radius: 6px; text-align: left; }
  .alert-item.critical .alert-badge { background: rgba(239,68,68,.15); color: #ef4444; }
  .alert-item.high .alert-badge { background: rgba(245,158,11,.15); color: #d97706; }
  .alert-item.medium .alert-badge { background: rgba(59,130,246,.15); color: #2563eb; }
  .alert-title { font-weight: 700; color: #1f2937; }
  .alert-desc { font-size: 0.8rem; color: #6b7280; }
  .alert-kpi { font-weight: 700; color: #1e40af; text-align: right; }
  .benchmark-card, .bubble-card { background: white; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.05); padding: 1.5rem; }
  .benchmark-table { margin-top: 0.5rem; }
  .bench-row { display: grid; grid-template-columns: 1fr 120px 1fr; padding: 0.5rem 0; border-bottom: 1px solid #eef2f7; font-size: 0.9rem; align-items: center; }
  .bench-head { background: #f8fafc; font-weight: 700; }
  .bench-row .up { color: #10b981; font-weight: 700; }
  .bench-row .down { color: #ef4444; font-weight: 700; }
  .spark { width: 100%; height: 20px; }
  .bubble-canvas { width: 100%; height: 160px; }
  .bubble-legend { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 6px; }
  .legend-color-dot { width: 10px; height: 10px; border-radius: 3px; display: inline-block; margin-right: 4px; }

  /* Additional KPIs Section */
  .additional-kpis-section { padding: 2rem 2rem 2rem 1rem; max-width: 1400px; margin-left: 0; margin-right: auto; width: 100%; box-sizing: border-box; }
  .additional-kpis-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }
  .kpi-card { background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.05); padding: 1.25rem; transition: all 0.3s ease; }
  .kpi-card:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,0,0,0.1); }
  .kpi-card h3 { font-size: 0.9rem; font-weight: 600; color: #1f2937; margin-bottom: 0.75rem; }
  .kpi-metric { text-align: left; margin-bottom: 0.75rem; }
  .kpi-metric .metric-value { font-size: 1.5rem; font-weight: 700; color: #1e40af; line-height: 1; }
  .kpi-metric .metric-label { font-size: 0.7rem; color: #6b7280; font-weight: 500; margin-top: 0.25rem; }
  .kpi-chart { height: 60px; margin-bottom: 0.75rem; }
  .kpi-chart svg { width: 100%; height: 100%; }
  .kpi-status { text-align: left; font-size: 0.7rem; font-weight: 700; padding: 0.25rem 0.5rem; border-radius: 12px; text-transform: uppercase; }
  .kpi-status.pass { background: rgba(16, 185, 129, 0.1); color: #10b981; }
  .kpi-status.monitor { background: rgba(245, 158, 11, 0.1); color: #d97706; }
  .kpi-status.alert { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
  .kpi-status.improving { background: rgba(59, 130, 246, 0.1); color: #2563eb; }

  /* Mini chart styles */
  .mini-waterfall, .mini-bars, .mini-radar, .mini-scatter, .mini-trend, .mini-donut, .mini-gauge, .mini-stacked { width: 100%; height: 100%; }
  .mini-heatmap { display: flex; gap: 4px; height: 100%; align-items: center; }
  .heatmap-cell { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 4px; padding: 4px; min-height: 40px; }
  .heatmap-label { font-size: 0.6rem; font-weight: 600; color: white; margin-bottom: 2px; }
  .heatmap-value { font-size: 0.7rem; font-weight: 700; color: white; }

.dashboard-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 2rem;
}

/* Performance Indicator Cards Grid - 4 columns */
.performance-indicator-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  align-items: stretch;
}

.performance-indicator-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.3s ease, transform 0.3s ease;
  position: relative;
  min-height: 200px;
  overflow: visible;
}

.performance-indicator-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.performance-indicator-card:hover .performance-card-icon,
.performance-indicator-card .performance-card-icon {
  opacity: 1 !important;
  visibility: visible !important;
  display: flex !important;
  transform: none !important;
}

.performance-indicator-card:hover .performance-card-icon svg,
.performance-indicator-card .performance-card-icon svg {
  opacity: 1 !important;
  visibility: visible !important;
  display: block !important;
}

.performance-indicator-card:hover .performance-card-icon svg path,
.performance-indicator-card .performance-card-icon svg path {
  opacity: 1 !important;
  visibility: visible !important;
  display: block !important;
}

.performance-card-header {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.performance-card-icon-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
  position: relative;
  z-index: 1;
}

.performance-card-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex !important;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  opacity: 1 !important;
  visibility: visible !important;
  transition: opacity 0.2s ease, visibility 0.2s ease, transform 0.2s ease;
  position: relative;
  z-index: 2;
  pointer-events: auto;
}

.performance-card-icon svg {
  opacity: 1 !important;
  visibility: visible !important;
  display: block !important;
  width: 24px;
  height: 24px;
  transition: opacity 0.2s ease, visibility 0.2s ease;
  pointer-events: none;
}

.performance-card-icon.status-pass {
  background: #10b981;
}

.performance-card-icon.status-in-progress {
  background: #f59e0b;
}

.performance-card-icon.status-pending {
  background: #6b7280;
}

.performance-card-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  flex: 1;
  line-height: 1.4;
}

.performance-status-badge {
  padding: 0.375rem 0.75rem;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  align-self: flex-start;
}

.performance-status-badge.status-pass {
  color: #065f46;
}

.performance-status-badge.status-in-progress {
  color: #92400e;
  background: none;
}

.performance-status-badge.status-pending {
  color: #e22f2f !important;
  font-size: 0.6rem;
}

.performance-status-badge.status-pending::before {
  content: none;
  display: none;
}

.performance-main-metric {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.performance-percentage {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1e40af;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.performance-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.performance-breakdown {
  font-size: 0.875rem;
  color: #4b5563;
  line-height: 1.5;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

/* Control Domains using dashboard cards style - 4 columns (kept for backward compatibility) */
.control-domains-section .dashboard-cards-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.05);
  align-items: stretch;
  grid-auto-rows: 1fr;
}

.control-domains-section .dashboard-cards-grid > * {
  min-height: 0;
}

.control-domains-section .dashboard-card {
  border-radius: 0;
  box-shadow: none;
  border: none;
  border-right: 1px solid rgba(0, 0, 0, 0.08);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  height: 100%;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  align-self: stretch;
}

.control-domains-section .dashboard-card-header {
  flex-shrink: 0;
  min-height: 80px;
  display: flex;
  align-items: center;
}

.control-domains-section .dashboard-metrics {
  flex: 1 1 auto;
  min-height: 0;
}

.control-domains-section .dashboard-card:hover {
  transform: none;
  box-shadow: none;
  background: #f8fafc;
  z-index: 1;
}

/* Remove right border from every 4th card (last in row) */
.control-domains-section .dashboard-card:nth-child(4n) {
  border-right: none;
}

/* Remove bottom border from last row */
.control-domains-section .dashboard-card:nth-last-child(-n+4) {
  border-bottom: none;
}

/* Ensure last card in grid has no right border */
.control-domains-section .dashboard-card:last-child {
  border-right: none;
  border-bottom: none;
}

.dashboard-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  height: 100%;
  transition: all 0.3s ease;
  position: relative;
  z-index: 2;
}

.dashboard-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.12);
}

.dashboard-card-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: #f8fafc;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.dashboard-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.dashboard-icon.policy { background: #1e40af; }
.dashboard-icon.compliance { background: #f59e0b; }
.dashboard-icon.risk { background: #10b981; }
.dashboard-icon.incident { background: #ef4444; }
.dashboard-icon.auditor { background: #7c3aed; }
.dashboard-icon.completed { background: #10b981; }
.dashboard-icon.in-progress { background: #f59e0b; }
.dashboard-icon.pending { background: #6b7280; }

.dashboard-info {
  flex: 1;
}

.dashboard-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
  line-height: 1.4;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.control-domains-section .dashboard-title {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  min-height: 2.8em;
  margin-bottom: 0.5rem;
}

.dashboard-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-indicator.active {
  background: #10b981;
}

.status-indicator.in-progress {
  background: #f59e0b;
}

.status-indicator.pending {
  background: #6b7280;
}

.dashboard-metrics {
  padding: 1.5rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
  flex-shrink: 0;
}

.metric-row:last-child {
  margin-bottom: 0;
}

.control-domains-section .metric-row {
  flex: 0 0 auto;
}

.metric-item {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
}

.metric-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metric-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
}

.dashboard-actions {
  padding: 1.5rem;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  background: #f8fafc;
}

.dashboard-actions .btn-primary {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: #1e40af;
  color: white;
  border: none;
  padding: 0.875rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.dashboard-actions .btn-primary:hover {
  background: #1d4ed8;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(30, 64, 175, 0.3);
}

/* Responsive Design */
@media (max-width: 1024px) {
  .home-container {
    margin-left: 0;
  }
  
  .domains-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .performance-indicator-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 1.25rem;
  }
  
  .performance-indicator-card {
    padding: 1.25rem;
    min-height: 180px;
  }
  
  .performance-percentage {
    font-size: 2.25rem;
  }
  
  .control-domains-section .dashboard-cards-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  /* Remove right border from every 3rd card on tablets */
  .domains-grid .domain-card:nth-child(3n),
  .control-domains-section .dashboard-card:nth-child(3n) {
    border-right: none;
  }
  
  /* Remove right border from 4n selector on tablets */
  .domains-grid .domain-card:nth-child(4n),
  .control-domains-section .dashboard-card:nth-child(4n) {
    border-right: 1px solid rgba(0, 0, 0, 0.08);
  }
  
  .hero-content {
    grid-template-columns: 1fr;
    text-align: left;
  }
  
  .compliance-overview-grid {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .chart-legend {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .legend-item {
    padding: 0.2rem 0.4rem;
    font-size: 0.75rem;
  }
  
  .footer-main {
    grid-template-columns: 1fr 2fr;
    gap: 3rem;
  }
  
  .footer-links {
    grid-template-columns: repeat(4, 1fr);
    gap: 2rem;
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2rem;
  }
  
  .hero-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  .cta-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .section-title {
    font-size: 2rem;
  }
  
  .cta-title {
    font-size: 2rem;
  }
  
  .footer-main {
    grid-template-columns: 1fr 1fr;
    gap: 3rem;
  }
  
  .footer-links {
    grid-template-columns: repeat(2, 1fr);
    gap: 2rem;
  }
  
  .footer-bottom-content {
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .domains-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .performance-indicator-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  .performance-indicator-card {
    padding: 1rem;
    min-height: 160px;
  }
  
  .performance-percentage {
    font-size: 2rem;
  }
  
  .performance-card-title {
    font-size: 0.875rem;
  }
  
  .control-domains-section .dashboard-cards-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  /* Remove right border from every 2nd card on mobile */
  .domains-grid .domain-card:nth-child(2n),
  .control-domains-section .dashboard-card:nth-child(2n) {
    border-right: none;
  }
  
  /* Remove right border from 3n and 4n selectors on mobile */
  .domains-grid .domain-card:nth-child(3n),
  .domains-grid .domain-card:nth-child(4n),
  .control-domains-section .dashboard-card:nth-child(3n),
  .control-domains-section .dashboard-card:nth-child(4n) {
    border-right: 1px solid rgba(0, 0, 0, 0.08);
  }
  
  .controls-grid {
    grid-template-columns: 1fr;
  }
  
  .dashboard-cards-grid {
    grid-template-columns: 1fr;
  }
  
  .footer-contact {
    text-align: left;
    margin-left: 0;
    margin-right: 0;
  }
  
  .contact-info {
    align-items: center;
  }
}

@media (max-width: 480px) {
  .domains-grid {
    grid-template-columns: 1fr;
  }
  
  .performance-indicator-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .performance-indicator-card {
    padding: 1rem;
    min-height: 150px;
  }
  
  .performance-percentage {
    font-size: 1.875rem;
  }
  
  .control-domains-section .dashboard-cards-grid {
    grid-template-columns: 1fr;
  }
  
  /* Remove all side borders on small mobile - only keep bottom */
  .domains-grid .domain-card,
  .control-domains-section .dashboard-card {
    border-right: none;
    border-left: none;
  }
  
  /* Remove bottom border from last card */
  .domains-grid .domain-card:last-child,
  .control-domains-section .dashboard-card:last-child {
    border-bottom: none;
  }
  
  .hero-content,
  .iso-compliance-section,
  .control-domains-section,
  .remaining-controls-section,
  .benefits-section,
  .cta-section,
  .footer-section,
  .module-dashboards-section {
    padding: 1.5rem 1rem;
  }
  
  .hero-title {
    font-size: 1.75rem;
  }
  
  .preview-metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .compliance-details-grid {
    grid-template-columns: 1fr;
  }
  
  .domain-card,
  .control-card,
  .benefit-card,
  .dashboard-card {
    padding: 1.5rem;
  }
  
  .footer-main {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  
  .footer-links {
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }
  
  .footer-certifications {
    flex-direction: column;
    align-items: center;
  }
  
  .footer-bottom-content {
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .footer-contact {
    text-align: left;
    margin-left: 0;
    margin-right: 0;
  }
  
  .contact-info {
    align-items: center;
  }
}

/* Policy Popup Styles */
.popup-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  z-index: 9999 !important;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(2px);
}

.policy-popup {
  position: relative !important;
  z-index: 10000 !important;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  border: 1px solid #e5e7eb;
  min-width: 700px;
  max-width: 900px;
  max-height: 600px;
  overflow: hidden;
  animation: popupSlideIn 0.3s ease-out;
  margin: auto;
}

@keyframes popupSlideIn {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  background: #f8fafc;
  border-bottom: 1px solid #e5e7eb;
  color: #1f2937;
}



.popup-header h4 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.popup-close {
  background: #e5e7eb;
  border: none;
  color: #6b7280;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.popup-close:hover {
  background: #d1d5db;
  color: #374151;
}

.popup-content {
  padding: 2rem;
  max-height: 450px;
  overflow-y: auto;
  background: white;
}

.popup-content::-webkit-scrollbar {
  width: 6px;
}

.popup-content::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.popup-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.popup-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.no-policies {
  text-align: center;
  color: #6b7280;
  padding: 3rem 2rem;
  font-size: 1.1rem;
}

.policies-list {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.policy-item {
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
  margin-bottom: 1rem;
}

.policy-item:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}



.policy-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.policy-name {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.3;
}

.policy-description {
  margin: 0;
  font-size: 0.9rem;
  color: #6b7280;
  line-height: 1.5;
}

.policy-status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 0.5rem;
}

.policy-status-badge.approved {
  background-color: #d1fae5;
  color: #065f46;
}

.policy-status-badge.active {
  background-color: #dbeafe;
  color: #1e40af;
}

.policy-status-badge.under-review {
  background-color: #fef3c7;
  color: #92400e;
}

.policy-status-badge.draft {
  background-color: #e5e7eb;
  color: #374151;
}

.policy-status-badge.pending {
  background-color: #fee2e2;
  color: #991b1b;
}

.policy-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  font-size: 0.875rem;
  align-items: center;
}

.policy-status {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  padding: 0.375rem 0.75rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
}

.policy-version {
  background: linear-gradient(135deg, #3b82f6, #1e40af);
  color: white;
  padding: 0.375rem 0.75rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.8rem;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.policy-date {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
  padding: 0.375rem 0.75rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.8rem;
  box-shadow: 0 2px 4px rgba(245, 158, 11, 0.2);
}

/* Responsive popup */
@media (max-width: 768px) {
  .policy-popup {
    min-width: 320px;
    max-width: 95vw;
    max-height: 80vh;
  }
  
  .popup-header {
    padding: 1rem 1.5rem;
  }
  
  .popup-header h4 {
    font-size: 1.1rem;
  }
  
  .popup-content {
    padding: 1.5rem;
    max-height: 60vh;
  }
  
  .policy-item {
    padding: 1rem;
  }
}

/* Approved Frameworks Section */
.approved-frameworks-section {
  background: #ffffff;
  padding: 1.5rem 2rem 0.4rem 1rem;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 999;
  backdrop-filter: blur(10px);
  margin-top: 0;
  border-top: none;
  width: 100%;
  box-sizing: border-box;
}

.frameworks-container {
  max-width: 1400px;
  margin-left: 0;
  margin-right: auto;
  width: 100%;
  box-sizing: border-box;
}

.frameworks-header {
  margin-bottom: 0.5rem;
}

.frameworks-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding-left: 0.5rem;
}

.frameworks-subtitle {
  font-size: 1rem;
  color: #6b7280;
  font-weight: 400;
}

.framework-dropdown-wrapper {
  margin-top: 1rem;
  position: relative;
}

.framework-dropdown {
  width: 100%;
  padding: 0.875rem 1rem;
  font-size: 0.95rem;
  font-weight: 500;
  color: #1e293b;
  background: #ffffff;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%233b82f6' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 1rem center;
  background-size: 12px;
  padding-right: 2.5rem;
}

.framework-dropdown:hover {
  border-color: #6366f1;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
}

.framework-dropdown:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.framework-dropdown option {
  padding: 0.75rem 1rem;
  font-size: 0.95rem;
  color: #1e293b;
}

.frameworks-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.framework-card {
  background: #ffffff;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.framework-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: #3b82f6;
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.framework-card:hover {
  border-color: #6366f1;
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.15);
  transform: translateY(-2px);
}

.framework-card:hover::before {
  transform: scaleX(0);
}

.framework-card.active {
  border-color: #e2e8f0;
  background: #ffffff;
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.2);
}

.framework-card.active::before {
  transform: scaleX(1);
}

.framework-card-content {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.framework-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: #6366f1;
  border-radius: 12px;
  color: white;
  font-size: 1.1rem;
  flex-shrink: 0;
}

.framework-card-info {
  flex: 1;
}

.framework-card-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 0.4rem 0;
  line-height: 1.3;
}

.framework-card-description {
  font-size: 0.8rem;
  color: #64748b;
  margin: 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.all-frameworks-card .framework-card-icon {
  background: #059669;
}

.framework-card.active .framework-card-icon {
  background: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.framework-card-stats {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #e2e8f0;
}

.framework-card-stats-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.framework-card-stats-row:last-child {
  margin-bottom: 0;
}

.framework-card-stats-label {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 500;
}

.framework-card-stats-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1e293b;
}

.framework-card-stats-value.compliance {
  color: #3b82f6;
}






.no-frameworks {
  width: 100%;
  text-align: center;
  padding: 1rem;
  color: #9ca3af;
  font-size: 0.875rem;
  font-style: italic;
}

.no-frameworks p {
  color: #9ca3af;
  font-size: 0.875rem;
  margin: 0;
}

/* Responsive Design for Frameworks Section */
@media (max-width: 768px) {
  .approved-frameworks-section {
    padding: 1rem 1rem 1rem;
  }
  
  .frameworks-header {
    margin-bottom: 0.75rem;
  }
  
  .frameworks-title {
    font-size: 1rem;
  }
  
  .framework-dropdown {
    padding: 0.75rem 0.875rem;
    font-size: 0.9rem;
    padding-right: 2.25rem;
  }
  
  .frameworks-cards {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 0.75rem;
  }
  
  .framework-card {
    padding: 0.8rem;
  }
  
  .framework-card-icon {
    width: 36px;
    height: 36px;
    font-size: 1rem;
  }
  
  .framework-card-title {
    font-size: 0.9rem;
  }
  
  .framework-card-description {
    font-size: 0.75rem;
  }
}

@media (max-width: 480px) {
  .approved-frameworks-section {
    padding: 1rem 1rem 0.875rem;
  }
  
  .frameworks-cards {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
  
  .framework-card {
    padding: 0.7rem;
  }
  
  .framework-card-icon {
    width: 32px;
    height: 32px;
    font-size: 0.9rem;
  }
  
  .framework-card-title {
    font-size: 0.85rem;
  }
  
  .framework-card-description {
    font-size: 0.7rem;
    -webkit-line-clamp: 2;
  }
}

/* Framework-Specific KPIs Section */
.framework-kpis-section {
  padding: 2rem 2rem 2rem 1rem;
  max-width: 1400px;
  margin-left: 0;
  margin-right: auto;
  width: 100%;
  box-sizing: border-box;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
}

.kpis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 2rem;
}

.kpi-card {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.kpi-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.12);
}

.kpi-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(135deg, #3b82f6, #1e40af);
}

.kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.kpi-header h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  line-height: 1.4;
  flex: 1;
  padding-right: 1rem;
}

.kpi-status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 50px;
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.kpi-status-badge.pass {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.kpi-status-badge.monitor {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
}

.kpi-status-badge.alert {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.kpi-status-badge.improving {
  background: rgba(59, 130, 246, 0.1);
  color: #2563eb;
}

.kpi-value-section {
  margin-bottom: 1rem;
}

.kpi-main-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1e40af;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.kpi-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.kpi-description {
  font-size: 0.875rem;
  color: #4b5563;
  line-height: 1.5;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f3f4f6;
}

.kpi-trend-section {
  display: flex;
  justify-content: flex-end;
}

.kpi-trend {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
}

.kpi-trend.up {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.kpi-trend.down {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.kpi-trend.stable {
  background: rgba(107, 114, 128, 0.1);
  color: #6b7280;
}

.kpi-trend svg {
  flex-shrink: 0;
}

/* Responsive design for KPI cards */
@media (max-width: 1024px) {
  .kpis-grid {
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
  }
}

@media (max-width: 768px) {
  .framework-kpis-section {
    padding: 1.5rem 1rem;
  }
  
  .kpis-grid {
    grid-template-columns: 1fr;
  }
  
  .kpi-main-value {
    font-size: 2rem;
  }
}
</style> 