<template>
  <div class="audit-kpi-container">
    <h1 class="audit-kpi-heading">Audit KPI Dashboard</h1>
    <!-- First Row: 2 Cards -->
    <div class="audit-kpi-row">
      <!-- Left Section: Non-Compliance Issues -->
      <div class="audit-kpi-section-left">
        <div class="audit-kpi-card-wrapper">
          <v-card 
            :loading="issuesLoading" 
            class="audit-kpi-card audit-kpi-non-compliance-card"
            elevation="2"
          >
            <v-card-item>
              <div class="d-flex">
                <!-- Left Side: Filters and Text -->
                <div class="audit-kpi-non-compliance-left">
                  <!-- Period Selector -->
                  <div class="audit-kpi-period-selector">
                    <button 
                      v-for="p in ['month', 'quarter', 'year']" 
                      :key="p"
                      class="audit-kpi-period-button"
                      :class="{ active: issuesPeriod === p }"
                      @click="changeIssuesPeriod(p)"
                    >
                      {{ p.charAt(0).toUpperCase() + p.slice(1) }}
                    </button>
                  </div>

                  <!-- Severity Filter -->
                  <div class="audit-kpi-severity-filter">
                    <button 
                      v-for="s in ['all', 'major', 'minor', 'none']" 
                      :key="s"
                      class="audit-kpi-severity-button"
                      :class="{ active: issuesSeverity === s }"
                      @click="changeIssuesSeverity(s)"
                    >
                      {{ s.charAt(0).toUpperCase() + s.slice(1) }}
                    </button>
                  </div>
                  
                  <!-- Issues Count Badge -->
                  <div class="audit-kpi-issues-badge" :class="getIssuesTrendClass">
                    {{ issuesMetrics.total_count || 0 }}
                    <span v-if="issuesMetrics.trend_direction !== 'stable'" class="audit-kpi-trend-indicator">
                      <v-icon size="small" :color="getIssuesTrendColor">
                        {{ issuesMetrics.trend_direction === 'up' ? 'mdi-arrow-up' : 'mdi-arrow-down' }}
                      </v-icon>
                      {{ Math.abs(issuesMetrics.trend_percentage) }}%
                    </span>
                  </div>
                  
                  <!-- Title -->
                  <div class="audit-kpi-text-h6 mt-3 text-center">Non-Compliance Issues</div>
                  
                  <!-- Severity Breakdown -->
                  <div class="audit-kpi-severity-breakdown">
                    <div class="audit-kpi-severity-item">
                      <div class="audit-kpi-severity-name">Major:</div>
                      <div class="audit-kpi-severity-count">{{ getSeverityCount('Major') }}</div>
                    </div>
                    <div class="audit-kpi-severity-item">
                      <div class="audit-kpi-severity-name">Minor:</div>
                      <div class="audit-kpi-severity-count">{{ getSeverityCount('Minor') }}</div>
                    </div>
                    <div class="audit-kpi-severity-item">
                      <div class="audit-kpi-severity-name">None:</div>
                      <div class="audit-kpi-severity-count">{{ getSeverityCount('None') }}</div>
                    </div>
                  </div>
                  
                  <!-- Top impacted area if available -->
                  <div class="audit-kpi-text-body-2 mt-1 text-center" v-if="issuesMetrics.top_areas && issuesMetrics.top_areas.length">
                    Top area: {{ issuesMetrics.top_areas[0].compliance_name }} ({{ issuesMetrics.top_areas[0].count }} issues)
                  </div>
                  <div class="audit-kpi-text-body-2 mt-1 text-center" v-else>
                    No top areas identified
                  </div>
                </div>

                <!-- Right Side: Bar Chart -->
                <div class="audit-kpi-non-compliance-right">
                  <div v-if="issuesMetrics.severity_breakdown && issuesMetrics.severity_breakdown.length" class="audit-kpi-issues-bar-chart">
                    <div class="audit-kpi-chart-title">Severity Distribution</div>
                    <div class="audit-kpi-chart-container">
                      <Bar :data="issuesChartData" :options="issuesChartOptions" />
                    </div>
                  </div>
                  <div v-else class="audit-kpi-text-body-2 text-center">
                    No severity data available
                  </div>
                </div>
              </div>
            </v-card-item>

            <!-- Error message -->
            <v-card-text v-if="issuesError" class="audit-kpi-error-text">
              <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>
              {{ issuesError }}
            </v-card-text>
          </v-card>
        </div>
      </div>

      <!-- Right Section: Audit Cycle Time -->
      <div class="audit-kpi-section-right">
        <div class="audit-kpi-card-wrapper">
          <v-card 
            :loading="cycleTimeLoading" 
            class="audit-kpi-card audit-kpi-cycle-time-card"
            elevation="2"
          >
            <v-card-item>
              <div class="d-flex">
                <!-- Left Side: Main Content -->
                <div class="audit-kpi-cycle-time-left">
                  <!-- Framework Selector -->
                  <div class="audit-kpi-filter-dropdown">
                    <select 
                      v-model="selectedCycleFrameworkId" 
                      @change="changeCycleFramework"
                      class="audit-kpi-filter-select"
                    >
                      <option value="">All Frameworks</option>
                      <option 
                        v-for="framework in cycleFrameworks" 
                        :key="framework.id" 
                        :value="framework.id"
                      >
                        {{ framework.name }}
                      </option>
                    </select>
                  </div>

                  <!-- Time Badge -->
                  <div class="audit-kpi-time-badge" :class="getEfficiencyClass">
                    {{ cycleTimeMetrics.overall_avg_days || 0 }}
                    <span class="audit-kpi-time-unit">days</span>
                  </div>
                  
                  <!-- Title -->
                  <div class="audit-kpi-text-h6 mt-4 text-center">Audit Cycle Time</div>
                  
                  <!-- Target info -->
                  <div class="audit-kpi-target-info">
                    <div class="audit-kpi-target-label">Target: {{ cycleTimeMetrics.target_days || 30 }} days</div>
                    <div class="audit-kpi-efficiency-badge" :class="getEfficiencyClass">
                      {{ cycleTimeMetrics.efficiency || 'N/A' }}
                    </div>
                  </div>
                </div>

                <!-- Right Side: Enhanced Chart Section -->
                <div class="audit-kpi-cycle-time-right">
                  <!-- Cycle Time Distribution -->
                  <div v-if="cycleTimeDistribution.length > 0" class="audit-kpi-cycle-distribution">
                    <div class="audit-kpi-cycle-distribution-title">Cycle Time Distribution</div>
                    <div class="audit-kpi-cycle-distribution-chart">
                      <Doughnut 
                        :data="cycleTimeDistributionData" 
                        :options="cycleTimeDistributionOptions" 
                      />
                    </div>
                    <div class="audit-kpi-cycle-distribution-legend">
                      <div 
                        v-for="(item, index) in cycleTimeDistribution" 
                        :key="index"
                        class="audit-kpi-cycle-legend-item"
                      >
                        <div class="audit-kpi-cycle-legend-color" :style="{ backgroundColor: getCycleTimeColor(item.range) }"></div>
                        <div class="audit-kpi-cycle-legend-text">
                          <div class="audit-kpi-cycle-legend-label">{{ item.range }}</div>
                          <div class="audit-kpi-cycle-legend-count">{{ item.count }} audits</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Performance Metrics -->
                  <div v-else-if="cycleTimeMetrics" class="audit-kpi-cycle-performance">
                    <div class="audit-kpi-cycle-performance-title">Performance Metrics</div>
                    <div class="audit-kpi-cycle-performance-grid">
                      <div class="audit-kpi-cycle-performance-item">
                        <div class="audit-kpi-cycle-performance-value">{{ cycleTimeMetrics.average_cycle_time || 0 }}</div>
                        <div class="audit-kpi-cycle-performance-label">Average</div>
                      </div>
                      <div class="audit-kpi-cycle-performance-item">
                        <div class="audit-kpi-cycle-performance-value">{{ cycleTimeMetrics.fastest_cycle_time || 0 }}</div>
                        <div class="audit-kpi-cycle-performance-label">Fastest</div>
                      </div>
                      <div class="audit-kpi-cycle-performance-item">
                        <div class="audit-kpi-cycle-performance-value">{{ cycleTimeMetrics.slowest_cycle_time || 0 }}</div>
                        <div class="audit-kpi-cycle-performance-label">Slowest</div>
                      </div>
                      <div class="audit-kpi-cycle-performance-item">
                        <div class="audit-kpi-cycle-performance-value">{{ cycleTimeMetrics.total_audits || 0 }}</div>
                        <div class="audit-kpi-cycle-performance-label">Total Audits</div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- No data state -->
                  <div v-else class="audit-kpi-no-data">
                    <div class="audit-kpi-no-data-icon">
                      <v-icon size="48" color="grey">mdi-clock-outline</v-icon>
                    </div>
                    <div class="audit-kpi-no-data-text">No cycle time data available</div>
                  </div>
                </div>
              </div>
            </v-card-item>

            <!-- Error message -->
            <v-card-text v-if="cycleTimeError" class="audit-kpi-error-text">
              <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>
              {{ cycleTimeError }}
            </v-card-text>
          </v-card>
        </div>
      </div>
    </div>

    <!-- Second Row: 2 Cards -->
    <div class="audit-kpi-row">
      <!-- Left Section: Time to Close -->
      <div class="audit-kpi-section-left">
        <div class="audit-kpi-card-wrapper">
          <v-card 
            :loading="timeToCloseLoading" 
            class="audit-kpi-card audit-kpi-time-to-close-card"
            elevation="2"
          >
            <v-card-item>
              <div class="d-flex pa-4">
                <!-- Left Side: Content -->
                <div class="audit-kpi-card-content-left">
                  <!-- Period Selector -->
                  <div class="audit-kpi-period-selector">
                    <button 
                      v-for="p in ['month', 'quarter', 'year']" 
                      :key="p"
                      class="audit-kpi-period-button"
                      :class="{ active: timeToClosePeriod === p }"
                      @click="changeTimeToClosePeriod(p)"
                    >
                      {{ p.charAt(0).toUpperCase() + p.slice(1) }}
                    </button>
                  </div>

                  <!-- Toggle for Number/Percentage View -->
                  <div class="audit-kpi-view-toggle-container mt-2">
                    <button 
                      class="audit-kpi-view-toggle-button"
                      :class="{ active: timeToCloseViewMode === 'number' }"
                      @click="timeToCloseViewMode = 'number'"
                    >
                      Days
                    </button>
                    <button 
                      class="audit-kpi-view-toggle-button"
                      :class="{ active: timeToCloseViewMode === 'percentage' }"
                      @click="timeToCloseViewMode = 'percentage'"
                    >
                      Percentage
                    </button>
                  </div>

                  <!-- Close Time Badge -->
                  <div class="audit-kpi-time-badge" :class="getCloseTimeClass">
                    <template v-if="timeToCloseViewMode === 'number'">
                      {{ timeToCloseMetrics.avg_close_days || 0 }}
                      <span class="audit-kpi-time-unit">days</span>
                    </template>
                    <template v-else>
                      {{ getTimeToClosePercentage }}%
                    </template>
                  </div>
                  
                  <!-- Title -->
                  <div class="audit-kpi-text-h6 mt-3 text-center">Time to Close</div>
                  
                  <!-- Target info -->
                  <div class="audit-kpi-target-info">
                    <div class="audit-kpi-target-label">Target: {{ timeToCloseMetrics.target_days || 14 }} days</div>
                    <div class="audit-kpi-efficiency-badge" :class="getCloseTimeClass">
                      {{ timeToCloseMetrics.efficiency || 'N/A' }}
                    </div>
                  </div>
                </div>

                <!-- Right Side: Graph -->
                <div class="audit-kpi-card-graph-right">
                  <div v-if="timeToCloseMonthlyTrend.length > 0" class="audit-kpi-close-time-chart-container">
                    <div class="audit-kpi-chart-title">Monthly Trend</div>
                    <div class="audit-kpi-chart-container">
                      <LineChart :data="timeToCloseChartData" :options="timeToCloseChartOptions" />
                    </div>
                  </div>
                </div>
              </div>
            </v-card-item>

            <!-- Error message -->
            <v-card-text v-if="timeToCloseError" class="audit-kpi-error-text">
              <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>
              {{ timeToCloseError }}
            </v-card-text>
          </v-card>
        </div>
      </div>

      <!-- Right Section: Compliance Readiness -->
      <div class="audit-kpi-section-right">
        <div class="audit-kpi-card-wrapper">
          <v-card 
            :loading="readinessLoading" 
            class="audit-kpi-card audit-kpi-readiness-card"
            elevation="2"
          >
            <v-card-item>
              <div class="d-flex">
                <!-- Left Side: Main Content -->
                <div class="audit-kpi-readiness-left">
                  <!-- Filter controls -->
                  <div class="audit-kpi-filter-controls" v-if="readinessFrameworks.length > 0 || readinessPolicies.length > 0">
                    <div class="audit-kpi-filter-selectors">
                      <div class="audit-kpi-filter-dropdown" v-if="readinessFrameworks.length > 0">
                        <select 
                          v-model="selectedFrameworkId" 
                          @change="changeFramework(selectedFrameworkId)"
                          class="audit-kpi-filter-select"
                        >
                          <option value="">All Frameworks</option>
                          <option 
                            v-for="framework in readinessFrameworks" 
                            :key="framework.framework_id" 
                            :value="framework.framework_id"
                          >
                            {{ framework.name }}
                          </option>
                        </select>
                      </div>
                      
                      <div class="audit-kpi-filter-dropdown" v-if="readinessPolicies.length > 0">
                        <select 
                          v-model="selectedPolicyId" 
                          @change="changePolicy(selectedPolicyId)"
                          class="audit-kpi-filter-select"
                        >
                          <option value="">All Policies</option>
                          <option 
                            v-for="policy in readinessPolicies" 
                            :key="policy.policy_id" 
                            :value="policy.policy_id"
                          >
                            {{ policy.name }}
                          </option>
                        </select>
                      </div>
                    </div>
                    
                    <button 
                      v-if="selectedFrameworkId || selectedPolicyId"
                      @click="resetFilters" 
                      class="audit-kpi-reset-filter-button"
                    >
                      Reset Filters
                    </button>
                  </div>
                  
                  <!-- Gauge Chart -->
                  <div class="audit-kpi-gauge-container">
                    <v-progress-circular
                      :model-value="readinessMetrics.readiness_percentage || 0"
                      :size="120"
                      :width="12"
                      :color="readinessMetrics.color || 'info'"
                      class="audit-kpi-gauge-chart"
                    >
                      {{ readinessMetrics.readiness_percentage || 0 }}%
                    </v-progress-circular>
                  </div>
                  
                  <!-- Title -->
                  <div class="audit-kpi-text-h6 mt-4 text-center">Compliance Readiness</div>
                  
                  <!-- Description -->
                  <div class="audit-kpi-target-info">
                    <div class="audit-kpi-target-label">
                      {{ readinessMetrics.implemented_count || 0 }} of {{ readinessMetrics.total_defined || 0 }} controls implemented
                    </div>
                    <div class="audit-kpi-efficiency-badge" :class="getReadinessClass">
                      {{ readinessMetrics.rating || 'N/A' }}
                    </div>
                  </div>
                  
                  <!-- Framework/Policy info if filtered -->
                  <div v-if="selectedFrameworkId || selectedPolicyId" class="audit-kpi-filter-info">
                    <div class="audit-kpi-filter-name">
                      {{ selectedFrameworkId ? 
                         'Framework: ' + (readinessFrameworks.find(f => f.framework_id == selectedFrameworkId)?.name || '') : 
                         'Policy: ' + (readinessPolicies.find(p => p.policy_id == selectedPolicyId)?.name || '') }}
                    </div>
                  </div>
                  
                  <!-- View breakdown button -->
                  <button 
                    v-if="!selectedFrameworkId && !selectedPolicyId && readinessFrameworks.length > 0"
                    class="audit-kpi-view-breakdown-button"
                    @click="showFrameworksModal = true"
                  >
                    View Framework Breakdown
                  </button>
                </div>

                <!-- Right Side: Criticality Breakdown -->
                <div class="audit-kpi-readiness-right">
                  <div v-if="readinessCriticality.length > 0" class="audit-kpi-criticality-breakdown">
                    <div class="audit-kpi-breakdown-title">Breakdown by Criticality</div>
                    <div class="audit-kpi-criticality-bars">
                      <div 
                        v-for="(item, index) in readinessCriticality" 
                        :key="index"
                        class="audit-kpi-criticality-bar-item"
                      >
                        <div class="audit-kpi-criticality-header">
                          <div class="audit-kpi-criticality-label">{{ item.criticality }}</div>
                          <div class="audit-kpi-criticality-counts">
                            {{ item.implemented_count }} / {{ item.total_defined }}
                          </div>
                        </div>
                        <div class="audit-kpi-progress-bar-container">
                          <div 
                            class="audit-kpi-progress-bar-fill"
                            :style="{ 
                              width: `${item.readiness_percentage}%`, 
                              backgroundColor: getCriticalityColor(item.criticality) 
                            }"
                          ></div>
                          <span class="audit-kpi-progress-text">{{ item.readiness_percentage }}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Alternative: Framework Distribution Chart -->
                  <div v-else-if="readinessFrameworks.length > 0" class="audit-kpi-framework-distribution">
                    <div class="audit-kpi-breakdown-title">Framework Distribution</div>
                    <div class="audit-kpi-framework-chart-container">
                      <Doughnut :data="readinessChartData" :options="readinessChartOptions" />
                    </div>
                  </div>
                  
                  <!-- No data state -->
                  <div v-else class="audit-kpi-no-data">
                    <div class="audit-kpi-no-data-icon">
                      <v-icon size="48" color="grey">mdi-chart-donut</v-icon>
                    </div>
                    <div class="audit-kpi-no-data-text">No breakdown data available</div>
                  </div>
                </div>
              </div>
            </v-card-item>

            <!-- Error message -->
            <v-card-text v-if="readinessError" class="audit-kpi-error-text">
              <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>
              {{ readinessError }}
            </v-card-text>
          </v-card>
        </div>
      </div>
    </div>

    <!-- Third Row: 2 Cards -->
    <!-- <div class="audit-kpi-row"> -->
      <!-- Left Section: S24 Open Basel Audit Findings -->
      <!-- <div class="audit-kpi-section-left">
        <div class="audit-kpi-card-wrapper"> -->
          <!-- <v-card 
            :loading="baselFindingsLoading" 
            class="audit-kpi-card audit-kpi-basel-findings-card"
            elevation="2"
          > -->
            <!-- <v-card-item>
              <div class="d-flex pa-4"> -->
                <!-- Left Side: Content -->
                <!-- <div class="audit-kpi-card-content-left"> -->
                  <!-- Count Badge -->
                  <!-- <div class="audit-kpi-findings-badge" :class="getBaselFindingsClass">
                    {{ baselFindingsMetrics.open_count || 0 }}
                    <span class="audit-kpi-findings-unit">findings</span>
                  </div> -->
                  
                  <!-- Title -->
                  <!-- <div class="audit-kpi-text-h6 mt-3 text-center">Open Basel Audit Findings</div> -->
                  
                  <!-- Target info -->
                  <!-- <div class="audit-kpi-target-info">
                    <div class="audit-kpi-target-label">Target: 90% closed within 90 days</div>
                    <div class="audit-kpi-efficiency-badge" :class="getBaselFindingsClass">
                      {{ baselFindingsMetrics.compliance_rate || 0 }}% Within Target
                    </div>
                  </div> -->
                  
                  <!-- Stats Grid -->
                  <!-- <div class="audit-kpi-metrics-grid mt-3">
                    <div class="audit-kpi-metric-item">
                      <div class="audit-kpi-metric-value">{{ baselFindingsMetrics.total_findings || 0 }}</div>
                      <div class="audit-kpi-metric-label">Total</div>
                    </div>
                    <div class="audit-kpi-metric-item">
                      <div class="audit-kpi-metric-value">{{ baselFindingsMetrics.closed_count || 0 }}</div>
                      <div class="audit-kpi-metric-label">Closed</div>
                    </div>
                  </div>
                </div> -->

                <!-- Right Side: Aging Buckets -->
                <!-- <div class="audit-kpi-card-graph-right">
                  <div class="audit-kpi-aging-buckets">
                    <div class="audit-kpi-aging-title">Aging Buckets</div>
                    <div class="audit-kpi-aging-bars">
                      <div 
                        v-for="(bucket, index) in baselAgingBuckets" 
                        :key="index"
                        class="audit-kpi-aging-bar-item"
                      >
                        <div class="audit-kpi-aging-header">
                          <div class="audit-kpi-aging-label">{{ bucket.label }}</div>
                          <div class="audit-kpi-aging-count">{{ bucket.count }}</div>
                        </div>
                        <div class="audit-kpi-progress-bar-container">
                          <div 
                            class="audit-kpi-progress-bar-fill"
                            :style="{ 
                              width: `${bucket.percentage}%`, 
                              backgroundColor: getAgingColor(bucket.label) 
                            }"
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </v-card-item> -->

            <!-- Error message -->
            <!-- <v-card-text v-if="baselFindingsError" class="audit-kpi-error-text">
              <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>
              {{ baselFindingsError }}
            </v-card-text>
          </v-card>
        </div>
      </div> -->

      <!-- Right Section: S25 Time to Remediate Basel Findings -->
      <!-- <div class="audit-kpi-section-right">
        <div class="audit-kpi-card-wrapper">
          <v-card 
            :loading="remediationTimeLoading" 
            class="audit-kpi-card audit-kpi-remediation-time-card"
            elevation="2"
          >
            <v-card-item>
              <div class="d-flex pa-4"> -->
                <!-- Left Side: Content -->
                <!-- <div class="audit-kpi-card-content-left"> -->
                  <!-- Time Badge -->
                  <!-- <div class="audit-kpi-time-badge" :class="getRemediationTimeClass">
                    {{ remediationTimeMetrics.avg_days || 0 }}
                    <span class="audit-kpi-time-unit">days</span>
                  </div> -->
                  
                  <!-- Title -->
                  <!-- <div class="audit-kpi-text-h6 mt-3 text-center">Time to Remediate Basel Findings</div> -->
                  
                  <!-- Target info -->
                  <!-- <div class="audit-kpi-target-info">
                    <div class="audit-kpi-target-label">Target: ≤ 45 days</div>
                    <div class="audit-kpi-efficiency-badge" :class="getRemediationTimeClass">
                      {{ remediationTimeMetrics.efficiency || 'N/A' }}
                    </div>
                  </div> -->
                  
                  <!-- Boxplot Stats -->
                  <!-- <div class="audit-kpi-boxplot-stats">
                    <div class="audit-kpi-boxplot-item">
                      <span class="audit-kpi-boxplot-label">Min:</span>
                      <span class="audit-kpi-boxplot-value">{{ remediationTimeMetrics.min_days || 0 }} days</span>
                    </div>
                    <div class="audit-kpi-boxplot-item">
                      <span class="audit-kpi-boxplot-label">Median:</span>
                      <span class="audit-kpi-boxplot-value">{{ remediationTimeMetrics.median_days || 0 }} days</span>
                    </div>
                    <div class="audit-kpi-boxplot-item">
                      <span class="audit-kpi-boxplot-label">Max:</span>
                      <span class="audit-kpi-boxplot-value">{{ remediationTimeMetrics.max_days || 0 }} days</span>
                    </div>
                  </div>
                </div> -->

                <!-- Right Side: Trend Chart -->
                <!-- <div class="audit-kpi-card-graph-right">
                  <div v-if="remediationTrendData.length > 0" class="audit-kpi-remediation-trend-container">
                    <div class="audit-kpi-chart-title">Monthly Trend</div>
                    <div class="audit-kpi-chart-container">
                      <LineChart :data="remediationChartData" :options="remediationChartOptions" />
                    </div>
                  </div>
                  <div v-else class="audit-kpi-no-data">
                    <div class="audit-kpi-no-data-icon">
                      <v-icon size="48" color="grey">mdi-chart-line</v-icon>
                    </div>
                    <div class="audit-kpi-no-data-text">No trend data available</div>
                  </div>
                </div>
              </div>
            </v-card-item> -->

            <!-- Error message -->
            <!-- <v-card-text v-if="remediationTimeError" class="audit-kpi-error-text">
              <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>
              {{ remediationTimeError }}
            </v-card-text>
          </v-card>
        </div>
      </div>
    </div> -->

    <!-- Fourth Row: 2 Cards -->
    <div class="audit-kpi-row">
      <!-- Left Section: Evidence Collection -->
      <div class="audit-kpi-section-left">
        <div class="audit-kpi-card-wrapper">
          <v-card 
            :loading="evidenceLoading" 
            class="audit-kpi-card audit-kpi-evidence-card"
            elevation="2"
          >
            <v-card-item>
              <div class="d-flex">
                <!-- Left Side: Main Content -->
                <div class="audit-kpi-evidence-left">
                  <!-- Audit selector if needed -->
                  <div v-if="auditOptions.length > 0" class="audit-kpi-audit-selector">
                    <select 
                      v-model="selectedAuditId" 
                      class="audit-kpi-audit-select"
                      @change="changeSelectedAudit"
                    >
                      <option value="">All Audits</option>
                      <option 
                        v-for="audit in auditOptions" 
                        :key="audit.id" 
                        :value="audit.id"
                      >
                        Audit #{{ audit.id }} - {{ audit.name }}
                      </option>
                    </select>
                  </div>
                  
                  <!-- Circular Progress for Evidence Completion -->
                  <div class="audit-kpi-gauge-container">
                    <v-progress-circular
                      :model-value="evidenceMetrics.completion_percentage || 0"
                      :size="90"
                      :width="10"
                      :color="getEvidenceColor"
                      class="audit-kpi-gauge-chart"
                    >
                      {{ evidenceMetrics.completion_percentage || 0 }}%
                    </v-progress-circular>
                  </div>
                  
                  <!-- Title -->
                  <div class="audit-kpi-text-h6 mt-3 text-center">Evidence Collection</div>
                  
                  <!-- Count info -->
                  <div class="audit-kpi-target-info">
                    <div class="audit-kpi-target-label">{{ evidenceMetrics.evidence_collected || 0 }} of {{ evidenceMetrics.total_findings || 0 }} findings have evidence</div>
                    <div class="audit-kpi-efficiency-badge" :class="getEvidenceClass">
                      {{ evidenceMetrics.rating || 'N/A' }}
                    </div>
                  </div>
                </div>

                <!-- Right Side: Top Audits or Evidence Details -->
                <div class="audit-kpi-evidence-right">
                  <!-- Top Audits with Evidence if not filtered -->
                  <div v-if="!selectedAuditId && evidenceBreakdown.length > 0" class="audit-kpi-evidence-audits">
                    <div class="audit-kpi-evidence-audits-title">Top Audits by Evidence Completion</div>
                    <div class="audit-kpi-evidence-audit-list">
                      <div 
                        v-for="(audit, index) in evidenceBreakdown.slice(0, 3)" 
                        :key="index"
                        class="audit-kpi-evidence-audit-item"
                        @click="selectedAuditId = audit.audit_id; changeSelectedAudit()"
                      >
                        <div class="audit-kpi-evidence-audit-header">
                          <div class="audit-kpi-evidence-audit-name">Audit #{{ audit.audit_id }}</div>
                          <div class="audit-kpi-evidence-audit-percentage">{{ audit.completion_percentage }}%</div>
                        </div>
                        <div class="audit-kpi-evidence-audit-framework">{{ audit.framework_name || 'Unknown Framework' }}</div>
                        <div class="audit-kpi-evidence-audit-progress">
                          <div class="audit-kpi-progress-bar-container">
                            <div 
                              class="audit-kpi-progress-bar-fill"
                              :style="{ width: `${audit.completion_percentage}%`, backgroundColor: getProgressColor(audit.completion_percentage) }"
                            ></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Evidence Details if filtered by audit -->
                  <div v-else-if="selectedAuditId && evidenceDetails.length > 0" class="audit-kpi-evidence-details">
                    <div class="audit-kpi-evidence-details-title">Evidence Details</div>
                    <div class="audit-kpi-evidence-detail-summary">
                      <div class="audit-kpi-evidence-detail-count">{{ getEvidenceDetailStats.withEvidence }} with evidence</div>
                      <div class="audit-kpi-evidence-detail-count">{{ getEvidenceDetailStats.withoutEvidence }} without evidence</div>
                    </div>
                    <button class="audit-kpi-view-all-button" @click="showEvidenceModal = true">
                      View All Evidence
                    </button>
                  </div>
                  
                  <!-- No data state -->
                  <div v-else class="audit-kpi-no-data">
                    <div class="audit-kpi-no-data-icon">
                      <v-icon size="48" color="grey">mdi-file-document-outline</v-icon>
                    </div>
                    <div class="audit-kpi-no-data-text">No evidence data available</div>
                  </div>
                </div>
              </div>
            </v-card-item>

            <!-- Error message -->
            <v-card-text v-if="evidenceError" class="audit-kpi-error-text">
              <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>
              {{ evidenceError }}
            </v-card-text>
          </v-card>
        </div>
      </div>

      <!-- Right Section: Audit Completion -->
      <div class="audit-kpi-section-right">
        <div class="audit-kpi-card-wrapper">
          <v-card 
            :loading="auditLoading" 
            class="audit-kpi-card audit-kpi-audit-completion-card"
            elevation="2"
          >
            <v-card-item>
              <div class="d-flex pa-4">
                <!-- Left Side: Content -->
                <div class="audit-kpi-card-content-left">
                  <!-- Period Selector -->
                  <div class="audit-kpi-period-selector">
                    <button 
                      v-for="p in ['day', 'week', 'month', 'year']" 
                      :key="p"
                      class="audit-kpi-period-button"
                      :class="{ active: period === p }"
                      @click="changePeriod(p)"
                    >
                      {{ p.charAt(0).toUpperCase() + p.slice(1) }}
                    </button>
                  </div>
                  
                  <!-- Gauge Chart -->
                  <div class="audit-kpi-gauge-container">
                    <v-progress-circular
                      :model-value="auditMetrics.completion_percentage || 0"
                      :size="100"
                      :width="12"
                      :color="getCompletionColor"
                      class="audit-kpi-gauge-chart"
                    >
                      {{ auditMetrics.completion_percentage || 0 }}%
                    </v-progress-circular>
                  </div>
                  
                  <!-- Title -->
                  <div class="audit-kpi-text-h6 mt-3 text-center">Audit Completion</div>
                  
                  <!-- Metrics Grid -->
                  <div class="audit-kpi-metrics-grid">
                    <div class="audit-kpi-metric-item">
                      <div class="audit-kpi-metric-value">{{ auditMetrics.total_audits || 0 }}</div>
                      <div class="audit-kpi-metric-label">Planned</div>
                    </div>
                    <div class="audit-kpi-metric-item">
                      <div class="audit-kpi-metric-value">{{ auditMetrics.completed_audits || 0 }}</div>
                      <div class="audit-kpi-metric-label">Completed</div>
                    </div>
                  </div>
                </div>

                <!-- Right Side: Graph -->
                <div class="audit-kpi-card-graph-right">
                  <!-- Bar Chart for Monthly Comparison -->
                  <div v-if="auditMonthlyData.length > 0" class="audit-kpi-bar-chart-container">
                    <div class="audit-kpi-chart-title">Monthly Audit Completion</div>
                    <div class="audit-kpi-chart-container">
                      <Bar :data="auditChartData" :options="auditChartOptions" />
                    </div>
                  </div>
                </div>
              </div>
            </v-card-item>

            <!-- Error message -->
            <v-card-text v-if="auditError" class="audit-kpi-error-text">
              <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>
              {{ auditError }}
            </v-card-text>
          </v-card>
        </div>
      </div>
    </div>

    <!-- Modals and other components remain unchanged -->
    <!-- Evidence Details Modal -->
    <v-dialog
      v-model="showEvidenceModal"
      max-width="800px"
    >
      <v-card>
        <v-card-title class="audit-kpi-modal-title">
          Evidence Details for Audit #{{ selectedAuditId }}
          <v-spacer></v-spacer>
          <v-btn
            icon
            @click="showEvidenceModal = false"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <div class="evidence-modal-content">
            <div class="evidence-filter">
              <label class="filter-label">Show:</label>
              <div class="filter-buttons">
                <button 
                  class="filter-button" 
                  :class="{ active: evidenceFilter === 'all' }"
                  @click="evidenceFilter = 'all'"
                >
                  All
                </button>
                <button 
                  class="filter-button" 
                  :class="{ active: evidenceFilter === 'with' }"
                  @click="evidenceFilter = 'with'"
                >
                  With Evidence
                </button>
                <button 
                  class="filter-button" 
                  :class="{ active: evidenceFilter === 'without' }"
                  @click="evidenceFilter = 'without'"
                >
                  Without Evidence
                </button>
              </div>
            </div>
            
            <div class="evidence-list">
              <div 
                v-for="(item, index) in filteredEvidenceDetails" 
                :key="index"
                class="evidence-item"
                :class="{ 'has-evidence': item.has_evidence }"
              >
                <div class="evidence-item-header">
                  <div class="evidence-item-id">Finding #{{ item.finding_id }} (Compliance #{{ item.compliance_id }})</div>
                  <div class="evidence-status" :class="{ 'status-positive': item.has_evidence, 'status-negative': !item.has_evidence }">
                    {{ item.has_evidence ? 'Evidence Provided' : 'No Evidence' }}
                  </div>
                </div>
                <div v-if="item.has_evidence" class="evidence-content">
                  <div class="evidence-text">{{ item.evidence }}</div>
                </div>
              </div>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Frameworks Breakdown Modal -->
    <v-dialog
      v-model="showFrameworksModal"
      max-width="800px"
    >
      <v-card>
        <v-card-title class="audit-kpi-modal-title">
          Framework Compliance Readiness
          <v-spacer></v-spacer>
          <v-btn
            icon
            @click="showFrameworksModal = false"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <div class="frameworks-modal-content">
            <div class="frameworks-list">
              <div 
                v-for="(framework, index) in readinessFrameworks" 
                :key="index"
                class="framework-item"
                @click="changeFramework(framework.framework_id); showFrameworksModal = false"
              >
                <div class="framework-item-header">
                  <div class="framework-name">{{ framework.name }}</div>
                  <div class="framework-percentage">
                    {{ framework.readiness_percentage }}%
                  </div>
                </div>
                <div class="framework-progress">
                  <div class="audit-kpi-progress-bar-container">
                    <div 
                      class="audit-kpi-progress-bar-fill"
                      :style="{ 
                        width: `${framework.readiness_percentage}%`, 
                        backgroundColor: getReadinessColor(framework.readiness_percentage) 
                      }"
                    ></div>
                  </div>
                </div>
                <div class="framework-counts">
                  {{ framework.implemented_count }} of {{ framework.total_defined }} controls implemented
                </div>
              </div>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue';
import axios from 'axios';
import { Chart, ArcElement, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from 'chart.js';
import { Doughnut, Bar, Line as LineChart } from 'vue-chartjs';
import './KpiAnalysis.css';
import { API_ENDPOINTS } from '../../config/api.js';

Chart.register(ArcElement, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

// Audit completion state
const auditLoading = ref(false);
const auditError = ref(null);
const period = ref('month');
const auditMetrics = ref({
  total_audits: 0,
  completed_audits: 0,
  completion_percentage: 0,
  monthly_breakdown: []
});
const auditMonthlyData = ref([]);

// Chart data and options for all charts
const issuesChartData = reactive({
  labels: [],
  datasets: [{
    label: 'Issues Count',
    data: [],
    backgroundColor: ['#dc2626', '#ea580c', '#d97706', '#16a34a'],
    borderColor: ['#dc2626', '#ea580c', '#d97706', '#16a34a'],
    borderWidth: 1,
    borderRadius: 4
  }]
});

const issuesChartOptions = reactive({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      titleColor: '#1f2937',
      bodyColor: '#4b5563',
      borderColor: '#d1d5db',
      borderWidth: 1,
      padding: 12,
      bodyFont: { size: 12 },
      titleFont: { size: 13, weight: 'bold' },
      cornerRadius: 8
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: { color: '#e5e7eb', lineWidth: 1 },
      border: { color: '#d1d5db', width: 1 },
      ticks: { font: { size: 11 }, color: '#374151', padding: 8 }
    },
    x: {
      grid: { display: false },
      border: { color: '#d1d5db', width: 1 },
      ticks: { font: { size: 11 }, color: '#374151', padding: 8 }
    }
  },
  animation: { duration: 1000, easing: 'easeOutQuart' }
});



// Cycle Time Distribution Chart Data
const cycleTimeDistributionData = reactive({
  labels: [],
  datasets: [{
    data: [],
    backgroundColor: ['#dc2626', '#ea580c', '#d97706', '#16a34a', '#2563eb'],
    borderColor: ['#dc2626', '#ea580c', '#d97706', '#16a34a', '#2563eb'],
    borderWidth: 2,
    hoverOffset: 4
  }]
});

const cycleTimeDistributionOptions = reactive({
  responsive: true,
  maintainAspectRatio: false,
  cutout: '70%',
  plugins: {
    legend: { 
      display: false // We'll use custom legend
    },
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      titleColor: '#1f2937',
      bodyColor: '#4b5563',
      borderColor: '#d1d5db',
      borderWidth: 1,
      padding: 12,
      bodyFont: { size: 12 },
      titleFont: { size: 13, weight: 'bold' },
      cornerRadius: 8
    }
  },
  animation: { duration: 1000, easing: 'easeOutCubic' }
});

const timeToCloseChartData = reactive({
  labels: [],
  datasets: [{
    label: 'Time to Close (days)',
    data: [],
    fill: false,
    borderColor: '#059669',
    backgroundColor: 'rgba(5, 150, 105, 0.1)',
    tension: 0.4,
    pointBackgroundColor: '#059669',
    pointBorderColor: '#fff',
    pointBorderWidth: 2,
    pointRadius: 4,
    pointHoverRadius: 6
  }]
});

const timeToCloseChartOptions = reactive({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      titleColor: '#1f2937',
      bodyColor: '#4b5563',
      borderColor: '#d1d5db',
      borderWidth: 1,
      padding: 12,
      bodyFont: { size: 12 },
      titleFont: { size: 13, weight: 'bold' },
      cornerRadius: 8
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: { color: '#e5e7eb', lineWidth: 1 },
      border: { color: '#d1d5db', width: 1 },
      ticks: { font: { size: 11 }, color: '#374151', padding: 8 }
    },
    x: {
      grid: { display: false },
      border: { color: '#d1d5db', width: 1 },
      ticks: { font: { size: 11 }, color: '#374151', padding: 8 }
    }
  },
  animation: { duration: 1000, easing: 'easeOutQuart' }
});

const auditChartData = reactive({
  labels: [],
  datasets: [
    {
      label: 'Planned',
      data: [],
      backgroundColor: '#e2e8f0',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      borderRadius: 4
    },
    {
      label: 'Completed',
      data: [],
      backgroundColor: '#2563eb',
      borderColor: '#2563eb',
      borderWidth: 1,
      borderRadius: 4
    }
  ]
});

const auditChartOptions = reactive({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { 
      display: true,
      position: 'top',
      labels: { 
        font: { size: 11 },
        color: '#374151',
        usePointStyle: true,
        padding: 15
      }
    },
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      titleColor: '#1f2937',
      bodyColor: '#4b5563',
      borderColor: '#d1d5db',
      borderWidth: 1,
      padding: 12,
      bodyFont: { size: 12 },
      titleFont: { size: 13, weight: 'bold' },
      cornerRadius: 8
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: { color: '#e5e7eb', lineWidth: 1 },
      border: { color: '#d1d5db', width: 1 },
      ticks: { font: { size: 11 }, color: '#374151', padding: 8 }
    },
    x: {
      grid: { display: false },
      border: { color: '#d1d5db', width: 1 },
      ticks: { font: { size: 11 }, color: '#374151', padding: 8 }
    }
  },
  animation: { duration: 1000, easing: 'easeInOutQuart' }
});

// Audit cycle time state
const cycleTimeLoading = ref(false);
const cycleTimeError = ref(null);
const selectedCycleFrameworkId = ref('');
const cycleFrameworks = ref([]);
const cycleTimeMetrics = ref({
  overall_avg_days: 0,
  target_days: 30,
  efficiency: 'N/A',
  monthly_breakdown: []
});
const cycleTimeMonthlyData = ref([]);
const cycleTimeDistribution = ref([]);

// Finding rate state
const findingRateLoading = ref(false);
const findingRateError = ref(null);
const findingPeriod = ref('year');
const findingRateMetrics = ref({
  avg_findings_per_audit: 0,
  low_threshold: 2,
  high_threshold: 5,
  rating: 'N/A',
  top_audits: []
});

// Time to close findings state
const timeToCloseLoading = ref(false);
const timeToCloseError = ref(null);
const timeToClosePeriod = ref('year');
const timeToCloseViewMode = ref('number'); // 'number' or 'percentage'
const timeToCloseMetrics = ref({
  avg_close_days: 0,
  target_days: 14,
  efficiency: 'N/A',
  oldest_findings: [],
  monthly_trend: [],
  closed_count: 0, // Added from closure rate
  total_count: 0,  // Added from closure rate
  closure_rate: 0  // Added from closure rate
});
const timeToCloseMonthlyTrend = ref([]);

// Audit Pass Rate state removed

// Non-Compliance Issues state
const issuesLoading = ref(false);
const issuesError = ref(null);
const issuesPeriod = ref('year');
const issuesSeverity = ref('all');
const issuesMetrics = ref({
  total_count: 0,
  trend_direction: 'stable',
  trend_percentage: 0,
  selected_severity: 'all',
  severity_breakdown: [],
  top_areas: [],
  monthly_trend: []
});

// Severity state
const severityLoading = ref(false);
const severityError = ref(null);
const severityPeriod = ref('year');
const severityMetrics = ref({
  severity_distribution: [],
  total_issues: 0,
  most_common: null,
  major_count: 0,
  minor_count: 0
});

// Closure Rate state removed - merged with Time to Close

// Evidence state
const evidenceLoading = ref(false);
const evidenceError = ref(null);
const evidenceMetrics = ref({
  completion_percentage: 0,
  evidence_collected: 0,
  total_findings: 0,
  rating: 'N/A',
  color: 'info'
});
const evidenceBreakdown = ref([]);
const evidenceDetails = ref([]);
const selectedAuditId = ref('');
const auditOptions = ref([]);
const evidenceFilter = ref('all');
const showEvidenceModal = ref(false);

// Report Timeliness state
const timelinessLoading = ref(false);
const timelinessError = ref(null);
const timelinessPeriod = ref('year');
const timelinessMetrics = ref({
  percent_on_time: 0,
  on_time_count: 0,
  total_reports: 0,
  avg_days_difference: 0
});
const timelinessHistogram = ref([]);

// Compliance Readiness state
const readinessLoading = ref(false);
const readinessError = ref(null);
const readinessMetrics = ref({
  total_defined: 0,
  implemented_count: 0,
  readiness_percentage: 0,
  rating: 'N/A',
  color: 'info'
});
const readinessFrameworks = ref([]);
const readinessPolicies = ref([]);
const readinessCriticality = ref([]);
const selectedFrameworkId = ref('');
const selectedPolicyId = ref('');
const showFrameworksModal = ref(false);

// Basel Audit Findings state (S24) - Removed (commented out in template)
// Time to Remediate Basel Findings state (S25) - Removed (commented out in template)

// Computed properties
const getCompletionColor = computed(() => {
  const percentage = auditMetrics.value.completion_percentage || 0;
  if (percentage >= 80) return 'success';
  if (percentage >= 50) return 'warning';
  return 'error';
});

const getEfficiencyClass = computed(() => {
  const avgDays = cycleTimeMetrics.value.overall_avg_days || 0;
  const targetDays = cycleTimeMetrics.value.target_days || 30;
  
  if (avgDays <= targetDays) return 'efficiency-good';
  if (avgDays <= targetDays * 1.5) return 'efficiency-warning';
  return 'efficiency-poor';
});

const getCloseTimeClass = computed(() => {
  const efficiency = timeToCloseMetrics.value.efficiency || '';
  
  if (efficiency === 'Good') return 'close-time-good';
  if (efficiency === 'Fair') return 'close-time-fair';
  return 'close-time-poor';
});

const getIssuesTrendClass = computed(() => {
  const direction = issuesMetrics.value.trend_direction || 'stable';
  
  if (direction === 'down') return 'issues-trend-good';
  if (direction === 'up') return 'issues-trend-bad';
  return 'issues-trend-neutral';
});

const getIssuesTrendColor = computed(() => {
  const direction = issuesMetrics.value.trend_direction || 'stable';
  
  if (direction === 'down') return 'success';
  if (direction === 'up') return 'error';
  return 'info';
});

const getEvidenceColor = computed(() => {
  const percentage = evidenceMetrics.value.completion_percentage || 0;
  if (percentage >= 80) return 'success';
  if (percentage >= 50) return 'warning';
  return 'error';
});

const getEvidenceClass = computed(() => {
  const rating = evidenceMetrics.value.rating || '';
  
  if (rating === 'Excellent') return 'evidence-excellent';
  if (rating === 'Good') return 'evidence-good';
  if (rating === 'Fair') return 'evidence-fair';
  return 'evidence-poor';
});

// Computed properties for evidence card
const getEvidenceDetailStats = computed(() => {
  const withEvidence = evidenceDetails.value.filter(item => item.has_evidence).length;
  const withoutEvidence = evidenceDetails.value.length - withEvidence;
  
  return {
    withEvidence,
    withoutEvidence
  };
});

const filteredEvidenceDetails = computed(() => {
  if (evidenceFilter.value === 'all') {
    return evidenceDetails.value;
  } else if (evidenceFilter.value === 'with') {
    return evidenceDetails.value.filter(item => item.has_evidence);
  } else { // 'without'
    return evidenceDetails.value.filter(item => !item.has_evidence);
  }
});



// Methods
const fetchAuditMetrics = async () => {
  auditLoading.value = true;
  auditError.value = null;
  
  try {
    const response = await axios.get(API_ENDPOINTS.KPI_AUDIT_COMPLETION(period.value));
    if (response.data.success && response.data.data) {
      auditMetrics.value = response.data.data.metrics;
      auditMonthlyData.value = response.data.data.monthly_breakdown || [];
      
      // Update chart data
      if (auditMonthlyData.value.length > 0) {
        auditChartData.labels = auditMonthlyData.value.map(item => item.month);
        auditChartData.datasets[0].data = auditMonthlyData.value.map(item => item.planned);
        auditChartData.datasets[1].data = auditMonthlyData.value.map(item => item.completed);
      } else {
        auditChartData.labels = ['No Data'];
        auditChartData.datasets[0].data = [0];
        auditChartData.datasets[1].data = [0];
      }
    } else {
      throw new Error(response.data.message || 'Failed to fetch audit metrics');
    }
  } catch (err) {
    console.error('Error fetching audit metrics:', err);
    auditError.value = 'Failed to load audit metrics';
  } finally {
    auditLoading.value = false;
  }
};

const fetchCycleTimeMetrics = async () => {
  cycleTimeLoading.value = true;
  cycleTimeError.value = null;
  
  try {
    const response = await axios.get(API_ENDPOINTS.KPI_AUDIT_CYCLE_TIME(selectedCycleFrameworkId.value));
    if (response.data.success && response.data.data) {
      cycleTimeMetrics.value = response.data.data.metrics;
      
      // Save frameworks for the dropdown
      cycleFrameworks.value = response.data.data.frameworks || [];
      
      // Process monthly data for chart
      cycleTimeMonthlyData.value = response.data.data.monthly_breakdown || [];
      
      // Process distribution data
      cycleTimeDistribution.value = response.data.data.distribution || [];
      

      
      // Update distribution chart data
      if (cycleTimeDistribution.value.length > 0) {
        cycleTimeDistributionData.labels = cycleTimeDistribution.value.map(item => item.range);
        cycleTimeDistributionData.datasets[0].data = cycleTimeDistribution.value.map(item => item.count);
      } else {
        cycleTimeDistributionData.labels = ['No Data'];
        cycleTimeDistributionData.datasets[0].data = [100];
      }
    } else {
      throw new Error(response.data.message || 'Failed to fetch cycle time metrics');
    }
  } catch (err) {
    console.error('Error fetching cycle time metrics:', err);
    cycleTimeError.value = 'Failed to load cycle time data';
  } finally {
    cycleTimeLoading.value = false;
  }
};

const fetchFindingRateMetrics = async () => {
  findingRateLoading.value = true;
  findingRateError.value = null;
  
  try {
    const response = await axios.get(API_ENDPOINTS.KPI_FINDING_RATE(findingPeriod.value));
    if (response.data.success && response.data.data) {
      findingRateMetrics.value = response.data.data.metrics;
      findingRateMetrics.value.top_audits = response.data.data.top_audits || [];
    } else {
      throw new Error(response.data.message || 'Failed to fetch finding rate metrics');
    }
  } catch (err) {
    console.error('Error fetching finding rate metrics:', err);
    findingRateError.value = 'Failed to load finding rate data';
  } finally {
    findingRateLoading.value = false;
  }
};

const fetchTimeToCloseMetrics = async () => {
  timeToCloseLoading.value = true;
  timeToCloseError.value = null;
  
  try {
    // Fetch both time to close and closure rate metrics in parallel
    const [timeToCloseResponse, closureRateResponse] = await Promise.all([
      axios.get(API_ENDPOINTS.KPI_TIME_TO_CLOSE(timeToClosePeriod.value)),
      axios.get(API_ENDPOINTS.KPI_CLOSURE_RATE(timeToClosePeriod.value))
    ]);
    
    if (timeToCloseResponse.data.success && timeToCloseResponse.data.data) {
      // Set time to close metrics
      timeToCloseMetrics.value = timeToCloseResponse.data.data.metrics;
      timeToCloseMetrics.value.oldest_findings = timeToCloseResponse.data.data.oldest_findings || [];
      
      // Process monthly trend data for chart
      timeToCloseMonthlyTrend.value = timeToCloseResponse.data.data.monthly_trend || [];
      
      // Update chart data
      if (timeToCloseMonthlyTrend.value.length > 0) {
        timeToCloseChartData.labels = timeToCloseMonthlyTrend.value.map(item => getShortMonth(item.month));
        timeToCloseChartData.datasets[0].data = timeToCloseMonthlyTrend.value.map(item => item.avg_close_days);
      } else {
        timeToCloseChartData.labels = ['No Data'];
        timeToCloseChartData.datasets[0].data = [0];
      }
      
      // Add closure rate data to the time to close metrics
      if (closureRateResponse.data.success && closureRateResponse.data.data) {
        const closureMetrics = closureRateResponse.data.data.metrics;
        timeToCloseMetrics.value.closed_count = closureMetrics.closed_count || 0;
        timeToCloseMetrics.value.total_count = closureMetrics.opened_count || 0;
        timeToCloseMetrics.value.closure_rate = closureMetrics.rate || 0;
        
        // Merge closure rate data into monthly trend
        const closureTrend = closureRateResponse.data.data.monthly_trend || [];
        
        // Map closure rate data into time to close monthly trend
        if (timeToCloseMonthlyTrend.value.length > 0 && closureTrend.length > 0) {
          timeToCloseMonthlyTrend.value = timeToCloseMonthlyTrend.value.map(item => {
            const matchingClosureItem = closureTrend.find(c => c.month === item.month);
            if (matchingClosureItem) {
              return {
                ...item,
                closed_count: matchingClosureItem.closed_count || 0,
                total_count: matchingClosureItem.opened_count || 0,
                closure_rate: matchingClosureItem.rate || 0
              };
            }
            return item;
          });
        }
      }
    } else {
      throw new Error(timeToCloseResponse.data.message || 'Failed to fetch time to close metrics');
    }
  } catch (err) {
    console.error('Error fetching time to close metrics:', err);
    timeToCloseError.value = 'Failed to load time to close data';
  } finally {
    timeToCloseLoading.value = false;
  }
};

const fetchIssuesMetrics = async () => {
  issuesLoading.value = true;
  issuesError.value = null;
  
  try {
    const response = await axios.get(API_ENDPOINTS.KPI_NON_COMPLIANCE_ISSUES(issuesPeriod.value, issuesSeverity.value));
    if (response.data.success && response.data.data) {
      issuesMetrics.value = response.data.data.metrics;
      issuesMetrics.value.severity_breakdown = response.data.data.severity_breakdown || [];
      issuesMetrics.value.top_areas = response.data.data.top_areas || [];
      issuesMetrics.value.monthly_trend = response.data.data.monthly_trend || [];
      
      // Update chart data
      if (issuesMetrics.value.severity_breakdown.length > 0) {
        issuesChartData.labels = issuesMetrics.value.severity_breakdown.map(item => item.severity);
        issuesChartData.datasets[0].data = issuesMetrics.value.severity_breakdown.map(item => item.count);
      } else {
        issuesChartData.labels = ['No Data'];
        issuesChartData.datasets[0].data = [0];
      }
    } else {
      throw new Error(response.data.message || 'Failed to fetch issues metrics');
    }
  } catch (err) {
    console.error('Error fetching issues metrics:', err);
    issuesError.value = 'Failed to load issues data';
  } finally {
    issuesLoading.value = false;
  }
};

const fetchSeverityMetrics = async () => {
  severityLoading.value = true;
  severityError.value = null;
  
  try {
    const response = await axios.get(API_ENDPOINTS.KPI_SEVERITY_DISTRIBUTION(severityPeriod.value));
    if (response.data.success && response.data.data) {
      severityMetrics.value = response.data.data.metrics;
      severityMetrics.value.severity_distribution = response.data.data.severity_distribution || [];
    } else {
      throw new Error(response.data.message || 'Failed to fetch severity metrics');
    }
  } catch (err) {
    console.error('Error fetching severity metrics:', err);
    severityError.value = 'Failed to load severity data';
  } finally {
    severityLoading.value = false;
  }
};

const fetchEvidenceMetrics = async () => {
  evidenceLoading.value = true;
  evidenceError.value = null;
  
  try {
    const response = await axios.get(API_ENDPOINTS.KPI_EVIDENCE_COMPLETION(selectedAuditId.value));
    if (response.data.success && response.data.data) {
      evidenceMetrics.value = response.data.data.metrics;
      evidenceBreakdown.value = response.data.data.audit_breakdown || [];
      evidenceDetails.value = response.data.data.evidence_details || [];
      
      // Load audit options if not already loaded
      if (auditOptions.value.length === 0 && evidenceBreakdown.value.length > 0) {
        auditOptions.value = evidenceBreakdown.value.map(audit => ({
          id: audit.audit_id,
          name: audit.framework_name || 'Unknown Framework'
        }));
      }
    } else {
      throw new Error(response.data.message || 'Failed to fetch evidence metrics');
    }
  } catch (err) {
    console.error('Error fetching evidence metrics:', err);
    evidenceError.value = 'Failed to load evidence data';
  } finally {
    evidenceLoading.value = false;
  }
};

const getProgressColor = (percentage) => {
  if (percentage >= 90) return '#4CAF50'; // Green
  if (percentage >= 70) return '#3f51b5'; // Indigo
  if (percentage >= 50) return '#FF9800'; // Orange
  return '#f44336'; // Red
};

const changePeriod = async (newPeriod) => {
  period.value = newPeriod;
  await fetchAuditMetrics();
};

const changeCycleFramework = async () => {
  await fetchCycleTimeMetrics();
};

const changeTimeToClosePeriod = async (newPeriod) => {
  timeToClosePeriod.value = newPeriod;
  await fetchTimeToCloseMetrics();
};

const changeIssuesPeriod = async (newPeriod) => {
  issuesPeriod.value = newPeriod;
  await fetchIssuesMetrics();
};

const changeIssuesSeverity = async (newSeverity) => {
  issuesSeverity.value = newSeverity;
  await fetchIssuesMetrics();
};

const changeSelectedAudit = async () => {
  await fetchEvidenceMetrics();
};

const getShortMonth = (monthStr) => {
  // Extract just the month abbreviation from "Jan 2025" format
  return monthStr ? monthStr.split(' ')[0] : '';
};



const fetchTimelinessMetrics = async () => {
  timelinessLoading.value = true;
  timelinessError.value = null;
  
  try {
    const response = await axios.get(API_ENDPOINTS.KPI_REPORT_TIMELINESS(timelinessPeriod.value));
    if (response.data.success && response.data.data) {
      timelinessMetrics.value = response.data.data.metrics;
      timelinessHistogram.value = response.data.data.histogram || [];
    } else {
      throw new Error(response.data.message || 'Failed to fetch timeliness metrics');
    }
  } catch (err) {
    console.error('Error fetching timeliness metrics:', err);
    timelinessError.value = 'Failed to load timeliness data';
  } finally {
    timelinessLoading.value = false;
  }
};

const fetchReadinessMetrics = async () => {
  readinessLoading.value = true;
  readinessError.value = null;
  
  try {
    const response = await axios.get(API_ENDPOINTS.KPI_COMPLIANCE_READINESS(selectedFrameworkId.value, selectedPolicyId.value));
    if (response.data.success && response.data.data) {
      readinessMetrics.value = response.data.data.metrics;
      readinessFrameworks.value = response.data.data.frameworks || [];
      readinessPolicies.value = response.data.data.policies || [];
      readinessCriticality.value = response.data.data.criticality_breakdown || [];
      
      // Update chart data for framework distribution
      if (readinessFrameworks.value.length > 0) {
        readinessChartData.labels = readinessFrameworks.value.map(framework => framework.name);
        readinessChartData.datasets[0].data = readinessFrameworks.value.map(framework => framework.readiness_percentage);
      } else {
        readinessChartData.labels = ['No Data'];
        readinessChartData.datasets[0].data = [100];
      }
    } else {
      throw new Error(response.data.message || 'Failed to fetch readiness metrics');
    }
  } catch (err) {
    console.error('Error fetching readiness metrics:', err);
    readinessError.value = 'Failed to load readiness data';
  } finally {
    readinessLoading.value = false;
  }
};

const changeFramework = async (frameworkId) => {
  selectedFrameworkId.value = frameworkId;
  selectedPolicyId.value = ''; // Reset policy selection
  await fetchReadinessMetrics();
};

const changePolicy = async (policyId) => {
  selectedPolicyId.value = policyId;
  selectedFrameworkId.value = ''; // Reset framework selection
  await fetchReadinessMetrics();
};

const resetFilters = async () => {
  selectedFrameworkId.value = '';
  selectedPolicyId.value = '';
  await fetchReadinessMetrics();
};

const getReadinessClass = computed(() => {
  const rating = readinessMetrics.value.rating || '';
  
  if (rating === 'Excellent') return 'readiness-excellent';
  if (rating === 'Good') return 'readiness-good';
  if (rating === 'Fair') return 'readiness-fair';
  return 'readiness-poor';
});

const getReadinessColor = (percentage) => {
  if (percentage >= 90) return '#4CAF50';  // Green
  if (percentage >= 75) return '#3f51b5';  // Indigo
  if (percentage >= 50) return '#FF9800';  // Orange
  return '#f44336';  // Red
};

const getCriticalityColor = (criticality) => {
  switch (criticality) {
    case 'Critical': return '#d32f2f';  // Deep red
    case 'High': return '#f44336';      // Red
    case 'Medium': return '#FF9800';    // Orange
    case 'Low': return '#4caf50';       // Green
    default: return '#9e9e9e';          // Grey
  }
};

const getCycleTimeColor = (range) => {
  if (range.includes('0-5')) return '#16a34a';      // Green
  if (range.includes('6-10')) return '#2563eb';     // Blue
  if (range.includes('11-15')) return '#d97706';    // Yellow
  if (range.includes('16-20')) return '#ea580c';    // Orange
  if (range.includes('21+')) return '#dc2626';      // Red
  return '#6b7280';                                  // Grey
};



// Initialize data
onMounted(() => {
  fetchAuditMetrics();
  fetchCycleTimeMetrics();
  fetchFindingRateMetrics();
  fetchTimeToCloseMetrics();
  fetchIssuesMetrics();
  fetchSeverityMetrics();
  fetchEvidenceMetrics();
  fetchTimelinessMetrics();
  fetchReadinessMetrics();
});

const getTimeToClosePercentage = computed(() => {
  const avg = timeToCloseMetrics.value.avg_close_days || 0;
  const target = timeToCloseMetrics.value.target_days || 14;
  
  if (avg <= 0 || target <= 0) return 0;
  
  // Calculate percentage: lower is better, so we invert the ratio
  // If avg days is equal to target, that's 100%
  // If avg days is double the target, that's 50%
  const percentage = Math.min(200, Math.max(0, (target / avg) * 100));
  return Math.round(percentage);
});

const getSeverityCount = (severity) => {
  return issuesMetrics.value.severity_breakdown.find(item => item.severity === severity)?.count || 0;
};

// Chart data for readiness doughnut chart
const readinessChartData = reactive({
  labels: [],
  datasets: [{
    data: [],
    backgroundColor: ['#dc2626', '#ea580c', '#d97706', '#16a34a', '#2563eb'],
    borderColor: ['#dc2626', '#ea580c', '#d97706', '#16a34a', '#2563eb'],
    borderWidth: 2,
    hoverOffset: 4
  }]
});

const readinessChartOptions = reactive({
  responsive: true,
  maintainAspectRatio: false,
  cutout: '70%',
  plugins: {
    legend: { 
      display: true,
      position: 'bottom',
      labels: { 
        font: { size: 11 },
        color: '#374151',
        usePointStyle: true,
        padding: 15
      }
    },
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      titleColor: '#1f2937',
      bodyColor: '#4b5563',
      borderColor: '#d1d5db',
      borderWidth: 1,
      padding: 12,
      bodyFont: { size: 12 },
      titleFont: { size: 13, weight: 'bold' },
      cornerRadius: 8
    }
  },
  animation: { duration: 1000, easing: 'easeOutCubic' }
});
</script>