<template>
  <div class="risk-kpi-dashboard">
    <!-- Header Section -->
    <div class="risk-kpi-header">
      <h2 class="risk-kpi-heading">Risk KPI</h2>
    </div>
    <!-- Category Filter Dropdown -->
    <div class="category-filter-container">
      <label for="category-filter">Filter by Category:</label>
      <select id="category-filter" v-model="selectedCategory" @change="filterKpiCards">
        <option value="all">All Categories</option>
        <option value="risk-profile">Risk Profile</option>
        <option value="risk-exposure">Risk Exposure</option>
        <option value="risk-mitigation">Risk Mitigation</option>
      </select>
    </div>
    
    <!-- First Row: 5 specific KPIs -->
    <div class="first-row">
      <!-- Number of Active Risks -->
      <div class="kpi-box" v-show="isVisible('active-risks')">
        <div class="kpi-title">NUMBER OF ACTIVE RISKS</div>
        <div class="kpi-number">
          {{ activeRisksData.current || '48' }}
          <span class="trend-indicator" :class="{ 'up': (activeRisksData.percentageChange > 0), 'down': (activeRisksData.percentageChange < 0) }">
            {{ activeRisksData.percentageChange > 0 ? '↑' : '↓' }} {{ Math.abs(activeRisksData.percentageChange || 0) }}%
          </span>
          </div>
        <div class="sparkline-chart">
          <div class="line-chart" v-if="activeRisksData.trendData && activeRisksData.trendData.length > 0">
            <svg width="100%" height="100%" preserveAspectRatio="none" viewBox="0 0 100 30">
              <path :d="generateSmoothCurvePath(activeRisksData.trendData, activeRisksData.minValue, activeRisksData.maxValue)" class="line-path"></path>
              <path :d="generateSmoothAreaPath(activeRisksData.trendData, activeRisksData.minValue, activeRisksData.maxValue)" class="chart-area"></path>
            </svg>
            <div v-for="(value, index) in activeRisksData.trendData" :key="'ar-point-'+index"
                 class="data-point"
                 :style="{ left: `${(index / (activeRisksData.trendData.length - 1)) * 100}%`, 
                           top: `${calculatePointPosition(value, activeRisksData.minValue, activeRisksData.maxValue)}%` }">
          </div>
            <div v-for="(value, index) in activeRisksData.trendData" :key="'ar-tooltip-'+index"
                 class="data-tooltip"
                 :style="{ left: `${(index / (activeRisksData.trendData.length - 1)) * 100}%`, top: `${calculatePointPosition(value, activeRisksData.minValue, activeRisksData.maxValue)}%` }">
              {{ activeRisksData.months[index] }}: {{ value }} risks
        </div>
          </div>
          <div class="month-labels" v-if="activeRisksData.months">
            <span v-for="(month, index) in activeRisksData.months" :key="'ar-month-'+index">{{ month }}</span>
          </div>
        </div>
        </div>

      <!-- High Criticality Risks -->
      <div class="kpi-box high-criticality" v-show="isVisible('high-criticality')">
        <div class="kpi-title">HIGH CRITICALITY RISKS</div>
        <div class="kpi-number">
          {{ criticalityData.count || '6.5' }}
          <span class="criticality-badge">HIGH</span>
          </div>
        <div class="criticality-breakdown">
          <div class="breakdown-item">
            <div class="item-dot critical"></div>
            <div class="item-label">Critical</div>
            <div class="item-value">{{ criticalityData.criticalCount || '2' }}</div>
            </div>
          <div class="breakdown-item">
            <div class="item-dot high"></div>
            <div class="item-label">High</div>
            <div class="item-value">{{ criticalityData.highCount || '4' }}</div>
            </div>
          </div>
        <div class="criticality-trend">
          <svg width="100%" height="15" viewBox="0 0 100 15" preserveAspectRatio="none">
            <path 
              v-if="criticalityData.trendData && criticalityData.trendData.length > 0"
              :d="generateCriticalityPath(criticalityData.trendData)" 
              class="criticality-path" 
            />
          </svg>
        </div>
      </div>

      <!-- FREQUENCY OF RISK REGISTER UPDATE - Moved to first row -->
      <div class="kpi-box" v-show="isVisible('register-update')">
        <div class="kpi-title">FREQUENCY OF RISK REGISTER UPDATE</div>
        <div class="kpi-number">
          {{ registerUpdateData.avgUpdateFrequency || '10' }}<span class="unit">days</span>
        </div>
        
        <div class="register-update-chart">
          <svg width="100%" height="50" viewBox="0 0 100 50" preserveAspectRatio="none">
            <!-- Update frequency line -->
            <path 
              v-if="registerUpdateData.monthlyUpdates && registerUpdateData.monthlyUpdates.length > 0"
              :d="generateRegisterUpdatePath(registerUpdateData.monthlyUpdates)" 
              fill="none"
              stroke="#4f46e5" 
              stroke-width="2"
              stroke-linejoin="round"
              stroke-linecap="round"
            />
            <!-- Data points -->
            <circle 
              v-for="(value, index) in registerUpdateData.monthlyUpdates" 
              :key="'update-point-'+index"
              :cx="(index / (registerUpdateData.monthlyUpdates.length - 1)) * 100" 
              :cy="calculateUpdateY(value)" 
              r="2" 
              fill="#4f46e5"
              stroke="#fff"
              stroke-width="1"
            />
          </svg>
          <div class="month-labels" v-if="registerUpdateData.months">
            <span v-for="(month, index) in registerUpdateData.months" :key="'update-month-'+index">{{ month }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Second Row and onwards: 4 KPIs per row -->
    <div class="kpi-grid">
      <!-- Average Time to Remediate Critical Risks -->
      <div class="kpi-box" v-show="isVisible('avg-remediation')">
        <div class="kpi-title">AVERAGE TIME TO REMEDIATE CRITICAL RISKS</div>
        <div class="kpi-number">
          {{ remediationData.current || kpiData.avgRemediationTime || '35' }}<span class="unit">days</span>
          <span class="trend-indicator" :class="{ 'up': (remediationData.percentageChange > 0), 'down': (remediationData.percentageChange < 0) }">
            {{ remediationData.percentageChange > 0 ? '↑' : '↓' }} {{ Math.abs(remediationData.percentageChange || 0) }}%
          </span>
        </div>
        <div class="remediation-chart">
          <svg width="100%" height="50" viewBox="0 0 100 50" preserveAspectRatio="none">
            <!-- Chart background grid -->
            <rect x="0" y="0" width="100" height="40" fill="#f8fafc" rx="2" ry="2" />
            
            <!-- SLA threshold line -->
            <line 
              x1="0" y1="20" 
              x2="100" y2="20" 
              stroke="#f59e0b" 
              stroke-width="1.5" 
              stroke-dasharray="3,2"
            />
            <!-- SLA text label -->
            <text x="2" y="18" font-size="3" fill="#f59e0b">SLA: {{ remediationData.slaThreshold || '30' }} days</text>
            
            <!-- Remediation time trend line -->
            <path 
              v-if="remediationData.trendData && remediationData.trendData.length > 0"
              :d="generateRemediationPath(remediationData.trendData)" 
              fill="none"
              stroke="#3b82f6" 
              stroke-width="2"
              stroke-linejoin="round"
              stroke-linecap="round"
            />
            
            <!-- Data points -->
            <circle 
              v-for="(value, index) in remediationData.trendData" 
              :key="'rem-point-'+index"
              :cx="(index / (remediationData.trendData.length - 1)) * 100" 
              :cy="calculateRemediationY(value)" 
              r="2.5" 
              fill="#3b82f6"
              stroke="#fff"
              stroke-width="1"
            />
          </svg>
          
          <!-- Month labels -->
          <div class="month-labels" v-if="remediationData.months">
            <span v-for="(month, index) in remediationData.months" :key="'rem-month-'+index">
              {{ month }}
            </span>
          </div>
        </div>
        
        <!-- Overdue info -->
        <div class="overdue-info" v-if="remediationData.overdueCount">
          <div class="overdue-container">
            <div class="risk-count">
              Overdue Critical Risks: <span>{{ remediationData.overdueCount }}</span>
            </div>
            <div class="risk-percentage">
              {{ remediationData.overduePercentage }}% of active critical risks
            </div>
          </div>
        </div>
      </div>

      <!-- Rate of Recurrence -->
      <div class="kpi-box" v-show="isVisible('rate-recurrence')">
        <div class="kpi-title">RATE OF RECURRENCE</div>
        <div class="kpi-number">
          {{ recurrenceData.recurrenceRate || kpiData.recurrenceRate || '6.5' }}<span class="percent">%</span>
          <span class="trend-indicator" :class="{ 'up': (recurrenceData.percentageChange > 0), 'down': (recurrenceData.percentageChange < 0) }">
            {{ recurrenceData.percentageChange > 0 ? '↑' : '↓' }} {{ Math.abs(recurrenceData.percentageChange || 0) }}%
          </span>
        </div>
        
        <!-- Bar chart showing one-time vs recurring risks with improved layout -->
        <div class="recurrence-bars-container">
          <div class="recurrence-labels">
            <span class="one-time-label">One-time</span>
            <span class="recurring-label">Recurring</span>
          </div>
          <div class="recurrence-values">
            <span class="one-time-value">{{ recurrenceData.oneTimeRate || 93.5 }}%</span>
            <span class="recurring-value">{{ recurrenceData.recurrenceRate || 6.5 }}%</span>
          </div>
          <div class="recurrence-bars">
            <div class="recurrence-bar one-time" :style="{ width: `${recurrenceData.oneTimeRate || 93.5}%` }"></div>
            <div class="recurrence-bar recurring" :style="{ width: `${recurrenceData.recurrenceRate || 6.5}%` }"></div>
          </div>
        </div>
        
        <!-- Trend line chart with clean layout -->
        <div class="recurrence-trend">
          <svg width="100%" height="50" viewBox="0 0 100 50" preserveAspectRatio="none">
            <!-- Background -->
            <rect x="0" y="0" width="100" height="50" fill="#f8fafc" rx="2" ry="2" />
            
            <!-- Trend line -->
            <path 
              v-if="recurrenceData.trendData && recurrenceData.trendData.length > 0"
              :d="generateRecurrencePath(recurrenceData.trendData)" 
              fill="none"
              stroke="#ef4444" 
              stroke-width="2"
              stroke-linejoin="round"
              stroke-linecap="round"
            />
            
            <!-- Data points -->
            <circle 
              v-for="(value, index) in recurrenceData.trendData" 
              :key="'rec-point-'+index"
              :cx="(index / (recurrenceData.trendData.length - 1)) * 100" 
              :cy="calculateRecurrenceY(value)" 
              r="2.5" 
              fill="#ef4444"
              stroke="#fff"
              stroke-width="1"
            />
          </svg>
          
          <!-- Month labels -->
          <div class="month-labels">
            <span v-for="(month, index) in recurrenceData.months" :key="'rec-month-'+index">
              {{ month }}
            </span>
          </div>
        </div>
      </div>

      <!-- Average Time to Incident Response -->
      <div class="kpi-box" v-show="isVisible('avg-response')">
        <div class="kpi-title">AVERAGE TIME TO INCIDENT RESPONSE</div>
        <div class="kpi-number">
          {{ formatResponseTime(responseData.current) }}<span class="unit">{{ responseData.current > 72 ? '' : 'hours' }}</span>
          <span class="trend-indicator" :class="{ 'up': (responseData.percentageChange > 0), 'down': (responseData.percentageChange < 0) }">
            {{ responseData.percentageChange > 0 ? '↑' : '↓' }} {{ Math.abs(responseData.percentageChange || 0) }}%
          </span>
        </div>
        
        <div class="response-gauge">
          <svg width="100%" height="80" viewBox="0 0 200 80">
            <!-- Gauge background arc -->
            <path 
              d="M 30 70 A 70 70 0 0 1 170 70" 
              stroke="#e5e7eb" 
              stroke-width="8" 
              fill="none" 
              stroke-linecap="round"
            />
            
            <!-- Target zone (green) -->
            <path 
              d="M 30 70 A 70 70 0 0 1 80 25" 
              stroke="#10b981" 
              stroke-width="8" 
              fill="none" 
              stroke-linecap="round"
            />
            
            <!-- Warning zone (amber) -->
            <path 
              d="M 80 25 A 70 70 0 0 1 120 25" 
              stroke="#f59e0b" 
              stroke-width="8" 
              fill="none" 
              stroke-linecap="round"
            />
            
            <!-- Danger zone (red) -->
            <path 
              d="M 120 25 A 70 70 0 0 1 170 70" 
              stroke="#ef4444" 
              stroke-width="8" 
              fill="none" 
              stroke-linecap="round"
            />
            
            <!-- Gauge needle -->
            <line 
              x1="100" y1="70" 
              :x2="calculateGaugeNeedleX(responseData.current || 6)" 
              :y2="calculateGaugeNeedleY(responseData.current || 6)" 
              stroke="#0f172a" 
              stroke-width="3"
              stroke-linecap="round"
            />
            
            <!-- Needle pivot point -->
            <circle cx="100" cy="70" r="4" fill="#0f172a" />
            
            <!-- Labels -->
            <text x="30" y="80" font-size="8" fill="#10b981" text-anchor="start">Target: {{ responseData.target || '4' }}h</text>
            <text x="170" y="80" font-size="8" fill="#ef4444" text-anchor="end">SLA: {{ responseData.sla || '8' }}h</text>
          </svg>
        </div>
        
        <div v-if="responseData.current > 72" class="response-warning">
          Response time significantly exceeds SLA threshold
        </div>
        
        <div class="response-trend">
          <svg width="100%" height="40" viewBox="0 0 100 40" preserveAspectRatio="none">
            <!-- Background for better visibility -->
            <rect x="0" y="0" width="100" height="40" fill="#f8fafc" rx="2" ry="2" />
            
            <!-- Trend line -->
            <path 
              v-if="responseData.trendData && responseData.trendData.length > 0"
              :d="generateResponsePath(responseData.trendData)" 
              fill="none"
              stroke="#ef4444" 
              stroke-width="2"
              stroke-linejoin="round"
              stroke-linecap="round"
            />
            
            <!-- Data points -->
            <circle 
              v-for="(value, index) in responseData.trendData" 
              :key="'resp-point-'+index"
              :cx="(index / (responseData.trendData.length - 1)) * 100" 
              :cy="calculateResponseY(value)" 
              r="2" 
              fill="#ef4444"
              stroke="#fff"
              stroke-width="0.5"
            />
          </svg>
          
          <!-- Month labels -->
          <div class="month-labels">
            <span v-for="(month, index) in responseData.months" :key="'resp-month-'+index">
              {{ month }}
            </span>
          </div>
        </div>
      </div>

      <!-- Cost of Mitigation -->
      <div class="kpi-box" v-show="isVisible('cost-mitigation')">
        <div class="kpi-header">
          <div class="kpi-title">COST OF MITIGATION</div>
          <div class="kpi-period-selector">
            <select v-model="mitigationCostPeriod" @change="fetchMitigationCostData">
              <option value="30days">Last 30 days</option>
              <option value="90days">Last 90 days</option>
              <option value="6months">Last 6 months</option>
              <option value="1year">Last 1 year</option>
            </select>
          </div>
        </div>
        <div class="kpi-number">
          ₹{{ mitigationCostData.totalCost || kpiData.mitigationCost || '184' }}K
          <span class="trend-indicator" :class="{ 'up': (mitigationCostData.percentageChange > 0), 'down': (mitigationCostData.percentageChange < 0) }">
            {{ mitigationCostData.percentageChange > 0 ? '↑' : '↓' }} {{ Math.abs(mitigationCostData.percentageChange || 0) }}%
          </span>
        </div>
        <div class="cost-chart">
          <div class="cost-bars" v-if="mitigationCostData.monthlyData && mitigationCostData.monthlyData.length > 0">
            <div 
              v-for="(item, index) in mitigationCostData.monthlyData" 
              :key="'cost-bar-'+index"
              class="cost-bar"
              :style="{ height: calculateCostBarHeight(item.cost) + '%' }"
            >
              <div class="cost-value">₹{{ item.cost }}K</div>
      </div>
          </div>
          <div class="cost-labels">
            <span v-for="(item, index) in mitigationCostData.monthlyData" :key="'cost-month-'+index">
              {{ item.month }}
            </span>
          </div>
          <div class="cost-breakdown">
            <div class="cost-metric">
              <div class="metric-label">Avg Cost</div>
              <div class="metric-value">₹{{ mitigationCostData.avgCost || '31' }}K</div>
            </div>
            <div class="cost-metric">
              <div class="metric-label">Highest</div>
              <div class="metric-value high-cost">₹{{ mitigationCostData.highestCost || '42' }}K</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Risk Identification Rate -->
      <div class="kpi-box" v-show="isVisible('identification-rate')">
        <div class="kpi-title">Risk Identification Rate</div>
        <div class="kpi-number">
          {{ identificationRate !== null ? identificationRate : '--' }}%
          <span class="percent" :class="{'up': identificationChange > 0, 'down': identificationChange < 0}">
            {{ identificationChange > 0 ? '+' : '' }}{{ identificationChange !== null ? identificationChange : '--' }}%
          </span>
        </div>
        <div class="kpi-note">
          Avg. Daily <b>{{ avgDailyRisks !== null ? avgDailyRisks : '--' }}</b> risks/day
        </div>
        <!-- Line Chart for Identification Rate -->
        <div class="kpi-chart">
          <svg v-if="identificationTrend && identificationTrend.length > 1" width="100%" height="60" viewBox="0 0 120 60">
            <!-- Area under the line -->
            <polygon
              :points="generateAreaPoints(identificationTrend, 120, 60)"
              class="identification-area"
            />
            <!-- Line path -->
            <polyline
              :points="generateLinePoints(identificationTrend, 120, 60)"
              class="identification-path"
              fill="none"
              stroke="#3b82f6"
              stroke-width="2"
            />
            <!-- Data points -->
            <circle
              v-for="(val, idx) in identificationTrend"
              :key="'identification-point-'+idx"
              :cx="getX(idx, identificationTrend.length, 120)"
              :cy="getY(val, identificationTrend, 60)"
              r="2"
              class="identification-point"
            />
          </svg>
          <div class="month-labels" v-if="identificationMonths && identificationMonths.length">
            <span v-for="(month, idx) in identificationMonths" :key="'identification-month-'+idx">{{ month }}</span>
          </div>
        </div>
      </div>

      <!-- Percentage of Due Mitigation Actions -->
      <div class="kpi-box" v-show="isVisible('due-mitigation')">
        <div class="kpi-header">
          <div class="kpi-title">PERCENTAGE OF DUE MITIGATION ACTIONS</div>
          <div class="kpi-period-selector">
            <select v-model="dueMitigationPeriod" @change="fetchDueMitigationData">
              <option value="30days">Last 30 days</option>
              <option value="90days">Last 90 days</option>
              <option value="6months">Last 6 months</option>
              <option value="1year">Last 1 year</option>
            </select>
          </div>
        </div>
        <div class="kpi-number">
          {{ dueMitigationData.overduePercentage || kpiData.dueMitigation || '22' }}<span class="percent">%</span>
          <span class="trend-indicator" :class="{ 'up': (dueMitigationData.percentageChange < 0), 'down': (dueMitigationData.percentageChange > 0) }">
            {{ dueMitigationData.percentageChange > 0 ? '↑' : '↓' }} {{ Math.abs(dueMitigationData.percentageChange || 0) }}%
          </span>
        </div>
        <div class="mitigation-chart">
          <div class="pie-chart">
            <!-- Simple donut chart with colored segments -->
            <svg width="70" height="70">
              <!-- Grey background ring -->
              <circle cx="35" cy="35" r="30" fill="#f5f7fa" stroke="none" />
              
              <!-- Colored segments as individual arcs -->
              <path :d="generatePieSegment(35, 35, 30, 20, 0, dueMitigationData.completedPercentage || 50)" fill="#10b981" />
              <path :d="generatePieSegment(35, 35, 30, 20, dueMitigationData.completedPercentage || 50, 
                      (dueMitigationData.completedPercentage || 50) + (dueMitigationData.pendingPercentage || 28))" fill="#3b82f6" />
              <path :d="generatePieSegment(35, 35, 30, 20, 
                      (dueMitigationData.completedPercentage || 50) + (dueMitigationData.pendingPercentage || 28), 100)" fill="#ef4444" />
              
              <!-- Inner white circle to create donut -->
              <circle cx="35" cy="35" r="15" fill="white" stroke="none" />
            </svg>
          </div>
          <div class="pie-legend">
            <div class="legend-item">
              <div class="legend-color completed"></div>
              <div class="legend-label">Completed</div>
              <div class="legend-value">{{ dueMitigationData.completedPercentage || '50' }}%</div>
            </div>
            <div class="legend-item">
              <div class="legend-color pending"></div>
              <div class="legend-label">Pending</div>
              <div class="legend-value">{{ dueMitigationData.pendingPercentage || '28' }}%</div>
            </div>
            <div class="legend-item">
              <div class="legend-color overdue"></div>
              <div class="legend-label">Overdue</div>
              <div class="legend-value">{{ dueMitigationData.overduePercentage || '22' }}%</div>
            </div>
          </div>
        </div>
        <div class="mitigation-detail">
          <div class="detail-count">{{ dueMitigationData.overdueCount || '8' }} mitigation tasks overdue</div>
        </div>
      </div>

      <!-- Completion of Improvement Initiatives -->
      <div class="kpi-box" v-show="isVisible('improvement-initiatives')">
        <div class="kpi-title">COMPLETION OF IMPROVEMENT INITIATIVES</div>
        <div class="initiative-progress">
          <svg width="120" height="120">
            <!-- Progress circle background -->
            <circle cx="60" cy="60" r="50" fill="transparent" stroke="#e5e7eb" stroke-width="10" />
            
            <!-- Progress circle fill - adjust stroke-dasharray to show progress -->
            <circle 
              cx="60" cy="60" r="50" 
              fill="transparent" 
              stroke="#4f46e5" 
              stroke-width="10"
              stroke-linecap="round"
              :stroke-dasharray="`${initiativeData.completionPercentage * 3.14} 314`"
              stroke-dashoffset="0"
              transform="rotate(-90 60 60)"
            />
            
            <!-- Center text -->
            <text x="60" y="60" text-anchor="middle" dominant-baseline="middle" 
                  class="circle-text">{{ initiativeData.completionPercentage || '76' }}%</text>
          </svg>
          
          <div class="initiative-counts">
            <div class="count-item">
              <div class="count-label">Completed</div>
              <div class="count-value">{{ initiativeData.completedCount || '19' }}</div>
            </div>
            <div class="count-item">
              <div class="count-label">Total</div>
              <div class="count-value">{{ initiativeData.totalCount || '25' }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Risk Impact on Operations and Finances -->
      <div class="kpi-box" v-show="isVisible('risk-impact')">
        <div class="kpi-title">RISK IMPACT ON OPERATIONS AND FINANCES</div>
        <div class="kpi-number">
          {{ Number(impactData.overallScore || 5.7).toFixed(1) }}<span class="unit">/10</span>
        </div>
        
        <div class="impact-meter">
          <div class="impact-gradient"></div>
          <div class="impact-pointer" :style="{ left: `${(Number(impactData.overallScore || 5.7) * 10).toFixed(1)}%` }"></div>
          <div class="impact-scale">
              <span>0</span>
          <span>5</span>
              <span>10</span>
            </div>
        </div>
        
        <div class="impact-chart">
          <div class="chart-header">
            <span class="axis-label op">Operational Impact</span>
            <span class="axis-label fin">Financial Impact</span>
          </div>
          <div class="impact-bubbles">
            <div v-for="(risk, index) in impactData.topRisks || defaultTopRisks" 
                 :key="'impact-'+index"
                 class="impact-bubble"
                 :class="risk.category ? risk.category.toLowerCase() : 'default'"
                 :style="{ 
                   left: `${(risk.operational_impact || 0) * 10}%`, 
                   bottom: `${(risk.financial_impact || 0) * 9}%`,
                   width: `${Math.min(10, Math.max(risk.operational_impact || 0, risk.financial_impact || 0) * 2.5)}px`,
                   height: `${Math.min(10, Math.max(risk.operational_impact || 0, risk.financial_impact || 0) * 2.5)}px`
                 }"
                 :title="`${risk.title || 'Unknown'}: Op Impact ${risk.operational_impact || 0}, Fin Impact ${risk.financial_impact || 0}`">
            </div>
          </div>
          <div class="impact-grid-lines">
            <div class="grid-line vertical"></div>
            <div class="grid-line horizontal"></div>
          </div>
          </div>
      </div>

      <!-- Risk Severity Based on Potential -->
      <div class="kpi-box" v-show="isVisible('risk-severity')">
        <div class="kpi-title">Risk Severity Based on Potential</div>
        <div class="kpi-number">{{ averageSeverity }}<span class="unit">/10</span></div>
        <div class="kpi-note">Most Severe: {{ mostSevereRisk }}</div>
        
        <div class="severity-categories">
          <div class="severity-category">
            <span class="category-label">Low</span>
            <span class="category-value">{{ severityPercentages.Low }}%</span>
          </div>
          <div class="severity-category">
            <span class="category-label">Medium</span>
            <span class="category-value">{{ severityPercentages.Medium }}%</span>
          </div>
          <div class="severity-category">
            <span class="category-label">High</span>
            <span class="category-value">{{ severityPercentages.High }}%</span>
          </div>
          <div class="severity-category">
            <span class="category-label">Critical</span>
            <span class="category-value">{{ severityPercentages.Critical }}%</span>
          </div>
        </div>
        
        <div class="severity-chart-container">
          <div class="severity-semi-circle">
            <div class="severity-segment low" :style="severitySegmentStyles.low"></div>
            <div class="severity-segment medium" :style="severitySegmentStyles.medium"></div>
            <div class="severity-segment high" :style="severitySegmentStyles.high"></div>
            <div class="severity-segment critical" :style="severitySegmentStyles.critical"></div>
          </div>
        </div>
      </div>

      <!-- Risk Exposure Score -->
      <div class="kpi-box" v-show="isVisible('exposure-score')">
        <div class="kpi-title">RISK EXPOSURE SCORE</div>
        <div class="kpi-number">
          {{ exposureScoreData.overallScore || kpiData.exposureScore || '75' }}<span class="percent">%</span>
          </div>
        
        <div class="exposure-chart">
          <div class="scatter-container">
            <!-- Top risks by exposure (scatter plot) -->
            <div v-for="(risk, index) in exposureScoreData.riskPoints || []" 
                 :key="'exp-'+index"
                 class="exposure-point"
                 :class="getCategoryClass(risk.category)"
                 :style="{ 
                   left: `${(risk.likelihood / 10) * 100}%`, 
                   bottom: `${(risk.impact / 10) * 100}%`,
                   width: `${Math.min(12, risk.exposure * 1.2)}px`,
                   height: `${Math.min(12, risk.exposure * 1.2)}px`
                 }"
                 :title="`${risk.title}: Impact ${risk.impact.toFixed(1)}, Likelihood ${risk.likelihood.toFixed(1)}, Exposure ${risk.exposure}`">
          </div>
            
            <!-- Grid lines -->
            <div class="grid-line vertical" style="left: 33%"></div>
            <div class="grid-line vertical" style="left: 67%"></div>
            <div class="grid-line horizontal" style="bottom: 33%"></div>
            <div class="grid-line horizontal" style="bottom: 67%"></div>
            
            <!-- Labels -->
            <div class="axis-label x-label">Likelihood</div>
            <div class="axis-label y-label">Impact</div>
        </div>

          <!-- Top risks legend -->
          <div class="exposure-legend">
            <div class="exposure-header">Top Risks by Exposure</div>
            <div class="exposure-risk-list">
              <div v-for="(risk, index) in getTopRisks(exposureScoreData.riskPoints || [])" 
                   :key="'top-'+index"
                   class="exposure-risk-item">
                <div class="risk-dot" :class="getCategoryClass(risk.category)"></div>
                <div class="risk-name">{{ risk.title }}</div>
                <div class="risk-score">{{ risk.exposure }}</div>
              </div>
            </div>
          </div>
        </div>
        </div>

      <!-- Risk Resilience to Absorb Shocks -->
      <div class="kpi-box" v-show="isVisible('risk-resilience')">
        <div class="kpi-title">RISK RESILIENCE TO ABSORB SHOCKS</div>
        <div class="kpi-number">{{ resilienceData.avgDowntime || kpiData.resilienceHours || '4.6' }}<span class="unit">hrs</span></div>
        
        <div class="resilience-chart">
          <!-- Horizontal bar chart showing downtime vs recovery -->
          <div class="resilience-bars">
            <div v-for="(item, index) in resilienceData.categoryData || defaultResilienceData" 
                 :key="'res-'+index"
                 class="resilience-category">
              <div class="category-name">{{ item.category }}</div>
              <div class="time-bars">
                <div class="time-bar downtime" :style="{ width: `${item.downtime * 10}%` }">
                  <span class="time-value">{{ item.downtime }}h</span>
                </div>
                <div class="time-bar recovery" :style="{ width: `${item.recovery * 10}%` }">
                  <span class="time-value">{{ item.recovery }}h</span>
                </div>
              </div>
            </div>
          </div>

          <div class="resilience-legend">
            <div class="legend-item">
              <div class="legend-color downtime"></div>
              <div class="legend-label">Expected Downtime</div>
            </div>
            <div class="legend-item">
              <div class="legend-color recovery"></div>
              <div class="legend-label">Recovery Time</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Add this to the kpi-grid div -->
      <div class="kpi-box" v-show="isVisible('assessment-review')">
        <div class="kpi-title">FREQUENCY OF RISK ASSESSMENT REVIEW</div>
        <div class="kpi-number">
          {{ assessmentData.avgReviewFrequency || '60' }}<span class="unit">days</span>
          <span class="criticality-badge" v-if="assessmentData.overdueCount">{{ assessmentData.overdueCount || '3' }} overdue</span>
          </div>
        
        <div class="assessment-chart">
          <!-- Monthly review frequency bar chart -->
          <div class="assessment-bars">
            <div v-for="(count, index) in assessmentData.monthlyReviews || [15, 18, 22, 17, 20, 23]" 
                 :key="'assess-'+index"
                 class="assessment-bar"
                 :style="{ height: `${calculateAssessmentBarHeight(count)}%` }">
              <div class="bar-value">{{ count }}</div>
          </div>
      </div>
          <div class="month-labels" v-if="assessmentData.months">
            <span v-for="(month, index) in assessmentData.months" :key="'assess-month-'+index">{{ month }}</span>
      </div>

          <div class="assessment-breakdown">
            <div class="breakdown-title">By Category (Average Days)</div>
            <div class="category-bars" v-if="assessmentData.categoryFrequencies">
              <div v-for="(days, category) in assessmentData.categoryFrequencies" 
                   :key="'cat-'+category"
                   class="category-bar-container">
                <div class="category-label">{{ category }}</div>
                <div class="category-bar-bg">
                  <div class="category-bar" :style="{ width: calculateCategoryBarWidth(days) + '%' }"></div>
        </div>
                <div class="category-value">{{ days }}</div>
              </div>
            </div>
          </div>
          </div>
        </div>

      <!-- Add this KPI card to the kpi-grid div -->
      <div class="kpi-box" v-show="isVisible('assessment-consensus')">
        <div class="kpi-title">RISK ASSESSMENT CONSENSUS</div>
        <div class="kpi-number">
          {{ consensusData.consensusPercentage || '75' }}<span class="percent">%</span>
          <span class="consensus-label">agreement</span>
            </div>
        
        <div class="consensus-chart">
          <div class="consensus-pie">
            <svg width="70" height="70" viewBox="0 0 70 70">
              <!-- Background circle -->
              <circle cx="35" cy="35" r="30" fill="#f8fafc" stroke="#e5e7eb" stroke-width="1" />
              
              <!-- Consensus segment (blue) -->
              <path 
                :d="generateArcPath(35, 35, 30, 0, consensusData.consensusPercentage || 75)" 
                fill="#3b82f6" 
              />
              
              <!-- No consensus segment (red) -->
              <path 
                :d="generateArcPath(35, 35, 30, consensusData.consensusPercentage || 75, 100)" 
                fill="#ef4444" 
              />
              
              <!-- Inner white circle for donut effect -->
              <circle cx="35" cy="35" r="15" fill="white" />
            </svg>
            </div>
          
          <div class="consensus-legend">
            <div class="legend-item">
              <div class="legend-color consensus"></div>
              <div class="legend-label">Consensus</div>
              <div class="legend-value">{{ consensusData.consensusCount || '90' }}</div>
          </div>
            <div class="legend-item">
              <div class="legend-color no-consensus"></div>
              <div class="legend-label">No Consensus</div>
              <div class="legend-value">{{ consensusData.noConsensusCount || '30' }}</div>
            </div>
          </div>
        </div>
        
        <div class="investigation-section">
          <div class="investigation-title">Needs Investigation</div>
          <div class="investigation-risks" v-if="consensusData.lowConsensusRisks && consensusData.lowConsensusRisks.length > 0">
            <div class="risk-item">
              <div class="risk-title">{{ consensusData.lowConsensusRisks[0].title }}</div>
              <div class="risk-agreement">{{ consensusData.lowConsensusRisks[0].agreement }} agreed</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Old Risk Assessment Consensus (hidden) -->
      <div class="kpi-box" v-show="false">
        <div class="kpi-title">RISK ASSESSMENT CONSENSUS</div>
      </div>

      <!-- Risk Approval Rate and Cycle -->
      <div class="kpi-box" v-show="isVisible('approval-rate-cycle')">
        <div class="kpi-title">RISK APPROVAL RATE AND CYCLE</div>
        <div class="kpi-number">
          {{ approvalRateData.approvalRate || '81' }}<span class="percent">%</span>
          <span class="approval-label">approval rate</span>
        </div>
        
        <div class="key-metrics">
          <!-- Average Review Cycles -->
          <div class="metric-box">
            <div class="metric-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" fill="#3b82f6">
                <path d="M12 12.75c1.148 0 2.278.08 3.383.237 1.037.146 1.866.966 1.866 2.013 0 3.728-2.35 6.75-5.25 6.75S6.75 18.728 6.75 15c0-1.046.83-1.867 1.866-2.013A24.204 24.204 0 0 1 12 12.75Z" />
                <path d="M12 8.25a2.25 2.25 0 0 0 0-4.5 2.25 2.25 0 0 0 0 4.5Z" />
              </svg>
            </div>
            <div class="metric-number">{{ approvalRateData.avgReviewCycles || '3.2' }}</div>
            <div class="metric-label">Avg. Review Cycles</div>
          </div>
          
          <!-- Max Review Cycles -->
          <div class="metric-box">
            <div class="metric-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" fill="#3b82f6">
                <path d="M18.375 2.25c-1.035 0-1.875.84-1.875 1.875v15.75c0 1.035.84 1.875 1.875 1.875h.75c1.035 0 1.875-.84 1.875-1.875V4.125c0-1.036-.84-1.875-1.875-1.875h-.75ZM9.75 8.625c0-1.036.84-1.875 1.875-1.875h.75c1.036 0 1.875.84 1.875 1.875v11.25c0 1.035-.84 1.875-1.875 1.875h-.75a1.875 1.875 0 0 1-1.875-1.875V8.625ZM3 13.125c0-1.036.84-1.875 1.875-1.875h.75c1.036 0 1.875.84 1.875 1.875v6.75c0 1.035-.84 1.875-1.875 1.875h-.75A1.875 1.875 0 0 1 3 19.875v-6.75Z" />
              </svg>
            </div>
            <div class="metric-number">{{ approvalRateData.maxReviewCycles || '4' }}</div>
            <div class="metric-label">Max Review Cycles</div>
          </div>
        </div>
      </div>

      <!-- Risk Reduction Trend -->
      <div class="kpi-box" v-show="isVisible('risk-reduction-trend')">
        <div class="kpi-title">RISK REDUCTION TREND</div>
        <div class="kpi-number">
          {{ reductionData.reductionPercentage || '25' }}<span class="percent">%</span>
          <span class="reduction-label">reduction</span>
          </div>
            <div class="waterfall-chart">
          <div class="waterfall-bar start" :style="{ height: calculateWaterfallBarHeight(reductionData.startCount) }">
            <div class="bar-value">{{ reductionData.startCount }}</div>
            </div>
          <div class="connector-line"></div>
          <div class="waterfall-bar new" :style="{ height: calculateWaterfallBarHeight(reductionData.newCount) }">
            <div class="bar-value">+{{ reductionData.newCount }}</div>
          </div>
          <div class="connector-line"></div>
          <div class="waterfall-bar mitigated" :style="{ height: calculateWaterfallBarHeight(reductionData.mitigatedCount) }">
            <div class="bar-value">-{{ reductionData.mitigatedCount }}</div>
        </div>
          <div class="connector-line"></div>
          <div class="waterfall-bar end" :style="{ height: calculateWaterfallBarHeight(reductionData.endCount) }">
            <div class="bar-value">{{ reductionData.endCount }}</div>
          </div>
          <div class="waterfall-labels">
            <span>Start</span>
            <span>New</span>
            <span>Mitigated</span>
            <span>End</span>
          </div>
      </div>
    </div>

      <!-- Risk Mitigation Completion Rate -->
      <div class="kpi-box" v-show="isVisible('mitigation-completion')">
        <div class="kpi-title">RISK MITIGATION COMPLETION RATE</div>
        <div class="kpi-number">{{ kpiData.mitigationCompletionRate || '76' }}<span class="percent">%</span></div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: (kpiData.mitigationCompletionRate || 76) + '%' }"></div>
          </div>
        <div class="avg-time-metrics">
          <div class="avg-time-label">Avg. Time to Mitigation: <span class="avg-time-value">{{ mitigationData.avgDays || '14' }} days</span></div>
          <div class="sla-indicator" :class="{ 'sla-warning': mitigationData.avgDays > mitigationData.slaDays }">
            SLA: {{ mitigationData.slaDays || '21' }} days
          </div>
        </div>
      </div>

      <!-- Probability of Risk Recurrence -->
      <div class="kpi-box" v-show="isVisible('recurrence-probability')">
        <div class="kpi-title">PROBABILITY OF RISK RECURRENCE</div>
        <div class="kpi-number">
          {{ recurrenceProbabilityData.averageProbability || '38' }}<span class="percent">%</span>
          <span class="trend-indicator" :class="{ 'up': (recurrenceProbabilityData.percentageChange > 0), 'down': (recurrenceProbabilityData.percentageChange < 0) }">
            {{ recurrenceProbabilityData.percentageChange > 0 ? '↑' : '↓' }} {{ Math.abs(recurrenceProbabilityData.percentageChange || 0) }}%
          </span>
        </div>
        
        <div class="probability-histogram">
          <div class="histogram-chart">
            <div 
              v-for="(item, index) in recurrenceProbabilityData.probabilityRanges || defaultProbabilityRanges" 
              :key="'prob-'+index"
              class="histogram-bar"
              :class="getBarClass(item.range)"
              :style="{ height: calculateHistogramBarHeight(item.count) + '%' }"
            >
              <div class="count-label">{{ item.count }}</div>
            </div>
          </div>
          <div class="range-labels">
            <span 
              v-for="(item, index) in recurrenceProbabilityData.probabilityRanges || defaultProbabilityRanges" 
              :key="'label-'+index"
              class="range-label"
            >
              {{ item.range }}
            </span>
          </div>
        </div>
        
        <div class="high-probability-risks" v-if="recurrenceProbabilityData.highRecurrenceRisks && recurrenceProbabilityData.highRecurrenceRisks.length > 0">
          <div class="high-prob-title">Highest Probability Risk</div>
          <div class="high-prob-item">
            <div class="high-prob-name">{{ recurrenceProbabilityData.highRecurrenceRisks[0].title }}</div>
            <div class="high-prob-value">{{ recurrenceProbabilityData.highRecurrenceRisks[0].probability }}%</div>
          </div>
        </div>
      </div>

      <!-- Risk Exposure -->
      <!-- <div class="kpi-box" v-show="isVisible('risk-exposure')">
        <div class="kpi-title">RISK EXPOSURE</div>
        <div class="kpi-number">
          {{ exposureData.current || kpiData.riskExposure || '872' }}
          <span class="trend-indicator" :class="{ 'up': (exposureData.percentageChange > 0), 'down': (exposureData.percentageChange < 0) }">
            {{ exposureData.percentageChange > 0 ? '↑' : '↓' }} {{ Math.abs(exposureData.percentageChange || 0) }}%
          </span>
        </div>
        <div class="sparkline-chart">
          <div class="line-chart" v-if="exposureData.trendData && exposureData.trendData.length > 0">
            <svg width="100%" height="100%" preserveAspectRatio="none" viewBox="0 0 100 30">
              <path :d="generateSmoothCurvePath(exposureData.trendData, exposureData.minValue, exposureData.maxValue)" class="line-path"></path>
              <path :d="generateSmoothAreaPath(exposureData.trendData, exposureData.minValue, exposureData.maxValue)" class="chart-area"></path>
            </svg>
            <div v-for="(value, index) in exposureData.trendData" :key="'exp-point-'+index"
                 class="data-point"
                 :style="{ left: `${(index / (exposureData.trendData.length - 1)) * 100}%`, 
                           top: `${calculatePointPosition(value, exposureData.minValue, exposureData.maxValue)}%` }">
            </div>
            <div v-for="(value, index) in exposureData.trendData" :key="'exp-tooltip-'+index"
                 class="data-tooltip"
                 :style="{ left: `${(index / (exposureData.trendData.length - 1)) * 100}%`, top: `${calculatePointPosition(value, exposureData.minValue, exposureData.maxValue)}%` }">
              {{ exposureData.months[index] }}: {{ value }}
            </div>
          </div>
          <div class="month-labels" v-if="exposureData.months">
            <span v-for="(month, index) in exposureData.months" :key="'exp-month-'+index">{{ month }}</span>
          </div>
        </div>
      </div> -->

      <!-- Risk Tolerance Thresholds -->
      <div class="kpi-box" v-show="isVisible('tolerance-thresholds')">
        <div class="kpi-title">RISK TOLERANCE THRESHOLDS</div>
        <div class="kpi-number tolerance-status-container">
          <span class="tolerance-status" :class="getToleranceStatusClass(toleranceData.overallStatus)">
            {{ toleranceData.overallStatus || 'Near Limits' }}
          </span>
        </div>
        
        <!-- Tolerance thresholds by category -->
        <div class="tolerance-thresholds">
          <div v-for="(data, category) in toleranceData.toleranceThresholds || defaultToleranceThresholds" 
               :key="'tolerance-'+category"
               class="tolerance-category">
            <div class="category-header">
              <div class="category-name">{{ category }}</div>
              <div class="category-status" :class="getCategoryStatusClass(data.status)">{{ data.status }}</div>
            </div>
            <div class="tolerance-bar-bg">
              <div class="tolerance-bar" 
                   :class="'status-' + (data.status ? data.status.toLowerCase() : 'unknown')"
                   :style="{ width: Math.min(100, data.percentage || 0) + '%' }">
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Risk Appetite Based on Tolerance Level -->
      <div class="kpi-box" v-show="isVisible('risk-appetite')">
        <div class="kpi-title">RISK APPETITE BASED ON TOLERANCE LEVEL</div>
        <div class="kpi-number centered-number">
          <div class="big-number">{{ appetiteData.currentLevel || 6 }}</div>
          <div class="unit-label">/10</div>
          <div class="appetite-description">{{ appetiteData.description || 'Balanced risk approach' }}</div>
        </div>
        
        <div class="appetite-chart">
          <div class="appetite-slider-container">
            <div class="appetite-gradient-bar"></div>
            <div class="appetite-marker" :style="{ left: ((appetiteData.currentLevel || 6) * 10) + '%' }"></div>
          </div>
          <div class="appetite-labels">
            <span class="label-left">Risk Averse</span>
            <span class="label-center">Balanced</span>
            <span class="label-right">Risk Seeking</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { AccessUtils } from '@/utils/accessUtils';
import { API_ENDPOINTS } from '../../config/api.js';
import apiService from '@/services/apiService.js';

export default {
  name: 'RiskKPI',
  data() {
    return {
      // Add the category filter selection and mappings
      selectedCategory: 'risk-profile',
      kpiCategories: {
        // A. Risk Status & Volume KPIs (Risk Profile)
        'risk-profile': [
          'active-risks',         // 1. Number of Active Risks
          'high-criticality',     // 2. High-Criticality Risks
          'identification-rate',  // 3. Risk Identification Rate
          'rate-recurrence',      // 4. Rate of Recurrence
          // Remove 'due-mitigation' from here
          'improvement-initiatives', // 6. Completion of Improvement Initiatives
          'assessment-review',    // 7. Frequency of Risk Assessment Review
          'register-update',      // 8. Frequency of Risk Register Update
          'approval-rate-cycle'   // 9. Risk Approval Rate and Cycle
        ],
        // B. Risk Impact & Exposure KPIs
        'risk-exposure': [
          'risk-exposure',        // 10. Risk Exposure
          'risk-severity',        // 11. Risk Severity Based on Potential Consequences
          'risk-impact',          // 12. Risk Impact on Operations and Finances
          'exposure-score',       // 13. Risk Exposure Score
          'tolerance-thresholds', // 14. Risk Tolerance Thresholds
          'risk-appetite',        // 15. Risk Appetite Based on Tolerance Level
          'risk-resilience',      // 16. Risk Resilience to Absorb Shocks
          'risk-reduction-trend'  // 17. Risk Reduction Trend
        ],
        // C. Risk Process & Performance KPIs (Risk Mitigation)
        'risk-mitigation': [
          'avg-remediation',      // 18. Average Time to Mitigation
          'mitigation-completion',// 19. Risk Mitigation Completion Rate
          'avg-remediation',      // 20. Average Time to Remediate Critical Risks (duplicate, both point to same card)
          'avg-response',         // 21. Average Time to Incident Response
          'cost-mitigation',      // 22. Cost of Mitigation
          'recurrence-probability',// 23. Probability of Risk Recurrence
          'due-mitigation'        // Add it here - Percentage of Due Mitigation Actions
        ]
      },
      kpiData: {},
      activeRisksData: {
        current: 0,
        months: [],
        trendData: [],
        percentageChange: 0
      },
      exposureData: {
        current: 0,
        months: [],
        trendData: [],
        percentageChange: 0
      },
      reductionData: {
        startCount: 0,
        newCount: 0,
        mitigatedCount: 0,
        endCount: 0,
        reductionPercentage: 0
      },
      criticalityData: {
        count: 0,
        highCount: 0,
        criticalCount: 0,
        percentage: 0,
        months: [],
        trendData: []
      },
      mitigationData: {
        avgDays: 0,
        slaDays: 0,
        trendData: [],
        months: []
      },
      remediationData: {
        current: 0,
        slaThreshold: 30,
        trendData: [],
        months: [],
        percentageChange: 0
      },
      recurrenceData: {
        recurrenceRate: 0,
        oneTimeRate: 0,
        percentageChange: 0,
        trendData: [],
        months: [],
        breakdown: null
      },
      responseData: {
        current: 0,
        target: 4,
        sla: 8,
        percentageChange: 0,
        trendData: [],
        months: [],
        delayedResponses: 0
      },
      mitigationCostData: {
        totalCost: 0,
        avgCost: 0,
        highestCost: 0,
        highestCategory: '',
        percentageChange: 0,
        monthlyData: []
      },
      identificationData: {
        current: 0,
        dailyAverage: 0,
        percentageChange: 0,
        trendData: [],
        months: [],
        minValue: 0,
        maxValue: 0
      },
      dueMitigationData: {
        overduePercentage: 0,
        completedPercentage: 0,
        pendingPercentage: 0,
        overdueCount: 0,
        totalCount: 0,
        percentageChange: 0
      },
      classificationData: {
        accuracy: 0,
        percentageChange: 0,
        categoryAccuracy: null,
        timeSeriesData: []
      },
      initiativeData: {
        completionPercentage: 0,
        totalCount: 0,
        completedCount: 0,
        pendingCount: 0,
        categoryBreakdown: null
      },
      impactData: {
        overallScore: 0,
        impactDistribution: null,
        topRisks: null
      },
      severityData: {
        severityDistribution: null,
        severityPercentages: null,
        averageSeverity: 0,
        trendData: [],
        topSevereRisks: []
      },
      defaultTopRisks: [
        {
          id: 1,
          title: 'Service Outage',
          operational_impact: 8.5,
          financial_impact: 9.2,
          category: 'Operational'
        },
        {
          id: 2,
          title: 'Data Breach',
          operational_impact: 7.2,
          financial_impact: 9.5,
          category: 'Security'
        },
        {
          id: 3,
          title: 'Compliance Violation',
          operational_impact: 6.8,
          financial_impact: 8.1,
          category: 'Compliance'
        },
        {
          id: 4,
          title: 'Supply Chain Disruption',
          operational_impact: 9.1,
          financial_impact: 7.4,
          category: 'Operational'
        },
        {
          id: 5,
          title: 'Market Volatility',
          operational_impact: 5.6,
          financial_impact: 8.7,
          category: 'Financial'
        }
      ],
      exposureScoreData: {
        overallScore: 0,
        riskPoints: [],
        categoryDistribution: {}
      },
      resilienceData: {
        avgDowntime: 0,
        avgRecovery: 0,
        categoryData: [],
        trendData: [],
        months: []
      },
      defaultResilienceData: [
        {
          category: 'Infrastructure',
          downtime: 6,
          recovery: 8
        },
        {
          category: 'Application',
          downtime: 3,
          recovery: 5
        },
        {
          category: 'Network',
          downtime: 5,
          recovery: 7
        },
        {
          category: 'Security',
          downtime: 7,
          recovery: 9
        }
      ],
      assessmentData: {
        avgReviewFrequency: 0,
        categoryFrequencies: {},
        mostReviewed: [],
        overdueReviews: [],
        months: [],
        monthlyReviews: [],
        overdueCount: 0,
        totalRisks: 0
      },
      consensusData: {
        consensusPercentage: 0,
        totalAssessments: 0,
        consensusCount: 0,
        noConsensusCount: 0,
        categoryConsensus: {},
        lowConsensusRisks: [],
        months: [],
        monthlyConsensus: []
      },
      registerUpdateData: {
        avgUpdateFrequency: 0,
        months: [],
        monthlyUpdates: [],
        stagnantRisks: [],
        categoryFrequencies: {},
        dailyUpdates: [],
        stagnantCount: 0
      },
      recurrenceProbabilityData: {
        averageProbability: 0,
        probabilityRanges: [],
        highRecurrenceRisks: [],
        trendData: [],
        months: [],
        percentageChange: 0,
        totalRisks: 0
      },
      defaultProbabilityRanges: [
        {range: '0-20%', count: 20, label: 'Very Low', percentage: 20},
        {range: '21-40%', count: 30, label: 'Low', percentage: 30},
        {range: '41-60%', count: 25, label: 'Medium', percentage: 25},
        {range: '61-80%', count: 15, label: 'High', percentage: 15},
        {range: '81-100%', count: 10, label: 'Very High', percentage: 10}
      ],
      toleranceData: {
        overallStatus: '',
        toleranceThresholds: {},
        alerts: [],
        historicalData: {},
        months: []
      },
      defaultToleranceThresholds: {
        'Security': {
          'max_exposure': 80,
          'current_exposure': 75,
          'unit': 'score',
          'percentage': 93.8,
          'status': 'Warning'
        },
        'Compliance': {
          'max_exposure': 75,
          'current_exposure': 62,
          'unit': 'score',
          'percentage': 82.7,
          'status': 'Normal'
        },
        'Operational': {
          'max_exposure': 70,
          'current_exposure': 75,
          'unit': 'score',
          'percentage': 107.1,
          'status': 'Exceeded'
        }
      },
      appetiteData: {
        currentLevel: 6,
        description: '',
        historicalLevels: [],
        dates: [],
        lastUpdated: '',
        approvedBy: '',
        levelDescriptions: {}
      },
      identificationPeriod: '30days',
      dueMitigationPeriod: '30days',
      mitigationCostPeriod: '30days',
      // Risk severity data
      severityDistribution: {
        Low: 0,
        Medium: 0,
        High: 0,
        Critical: 0
      },
      severityPercentages: {
        Low: 0,
        Medium: 0,
        High: 0,
        Critical: 0
      },
      averageSeverity: 0,
      trendData: [],
      topSevereRisks: [],
      mostSevereRisk: 'Loading...',
      approvalRateData: {
        approvalRate: 0,
        avgReviewerCount: 0,
        avgCycleDays: 0,
        totalRisks: 0,
        approvedRisks: 0,
        pendingRisks: 0,
        months: [],
        monthlyApprovalRates: [],
        monthlyCycleDays: [],
        pendingApprovalRisks: []
      },
      identificationRate: null,
      identificationChange: null,
      avgDailyRisks: null,
      identificationTrend: null,
      identificationMonths: null,
    }
  },
  mounted() {
    // Check authentication status first
    const token = localStorage.getItem('access_token');
    const isLoggedIn = localStorage.getItem('is_logged_in') === 'true';
    console.log('Authentication status:', { isLoggedIn, hasToken: !!token });
    
    if (!token) {
      console.warn('No authentication token found. KPI data may not load properly.');
    }
    
    // Fetch all required data when component mounts
    this.fetchKpiData();
    this.fetchActiveRisksTrend(); // This is already calling active-risks-kpi endpoint
    this.fetchExposureTrend();
    this.fetchReductionTrend();
    this.fetchCriticalityData();
    this.fetchMitigationData();
    this.fetchRemediationData(); // Already added, make sure it's uncommented
    this.fetchRecurrenceData(); // Added recurrence rate data fetch
    this.fetchResponseData(); // Added incident response time data fetch
    this.fetchIdentificationData();
    this.fetchDueMitigationData();
    this.fetchClassificationData();
    this.fetchInitiativeData();
    this.fetchImpactData();
    this.fetchSeverityData();
    this.fetchExposureScoreData();
    this.fetchResilienceData();
    this.fetchAssessmentFrequencyData();
    this.fetchAssessmentConsensusData();
    this.fetchRegisterUpdateFrequency();
    this.fetchRecurrenceProbability();
    this.fetchToleranceThresholds();
    this.fetchRiskAppetite();
    this.fetchRiskSeverity();
    this.fetchIdentificationRate(); // <-- ADD THIS LINE
  },
  methods: {
    async fetchKpiData() {
      try {
        console.log('✅ Fetching KPI data with JWT token from:', API_ENDPOINTS.RISK_KPI_DATA);
        
        const response = await apiService.get(API_ENDPOINTS.RISK_KPI_DATA);
        
        console.log('KPI data response status:', response.status);
        console.log('KPI data received:', response.data);
        this.kpiData = response.data;
      } catch (error) {
        console.error('Error fetching KPI data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackData();
      }
    },
    async fetchActiveRisksTrend() {
      try {
        console.log("✅ Fetching active risks data with JWT token from:", API_ENDPOINTS.RISK_ACTIVE_RISKS_KPI);
        
        const response = await apiService.get(API_ENDPOINTS.RISK_ACTIVE_RISKS_KPI);
        
        console.log("Response status:", response.status);
        console.log("Response headers:", Object.fromEntries([...response.headers.entries()]));
        
        const data = response.data;
          console.log("Active risks data received:", data);
          this.activeRisksData = data;
          
          // Update the KPI data
          this.kpiData = {
            ...this.kpiData,
            activeRisks: data.current
          };
          
          console.log("Updated KPI data with active risks:", this.kpiData.activeRisks);
        
      } catch (error) {
        console.error('Error fetching active risks trend:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackActiveRisksTrend();
      }
    },
    async fetchExposureTrend() {
      try {
        console.log("Fetching risk exposure data from backend...");
        const response = await apiService.get(API_ENDPOINTS.RISK_EXPOSURE_TREND);
        console.log("Exposure trend response status:", response.status);
        
        const data = response.data;
          console.log("Risk exposure data received:", data);
          this.exposureData = data;
          
          // Update the KPI data for risk exposure
          this.kpiData = {
            ...this.kpiData,
            riskExposure: data.current
          };
          
          console.log("Updated KPI data with risk exposure:", this.kpiData.riskExposure);
        
      } catch (error) {
        console.error('Error fetching exposure trend:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackExposureTrend();
      }
    },
    async fetchReductionTrend() {
      try {
        console.log("Fetching risk reduction trend data from backend...");
        const response = await apiService.get(API_ENDPOINTS.RISK_REDUCTION_TREND);
        console.log("Risk reduction trend response status:", response.status);
        
        const data = response.data;
          console.log("Risk reduction trend data received:", data);
          this.reductionData = data;
          
          // Optional: Update any other components that might need this data
          console.log("Updated reduction trend data with startCount:", data.startCount, 
                      "newCount:", data.newCount, 
                      "mitigatedCount:", data.mitigatedCount, 
                      "endCount:", data.endCount, 
                      "reductionPercentage:", data.reductionPercentage);
        
      } catch (error) {
        console.error('Error fetching reduction trend:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackReductionTrend();
      }
    },
    async fetchCriticalityData() {
      try {
        console.log("Fetching high criticality risks data from backend...");
        const response = await apiService.get(API_ENDPOINTS.RISK_HIGH_CRITICALITY);
        console.log("High criticality risks response status:", response.status);
        
        const data = response.data;
          console.log("High criticality risks data received:", data);
          this.criticalityData = data;
          
          // Update the UI with real data
          this.kpiData = {
            ...this.kpiData,
            highCriticalityRisks: data.count,
            highCount: data.highCount,
            criticalCount: data.criticalCount
          };
          
          console.log("Updated KPI data with high criticality risks:", this.kpiData.highCriticalityRisks);
        
      } catch (error) {
        console.error('Error fetching criticality data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackCriticalityData();
      }
    },
    async fetchMitigationData() {
      try {
        console.log("Fetching mitigation completion rate data from backend...");
        const response = await apiService.get(API_ENDPOINTS.RISK_MITIGATION_COMPLETION_RATE_KPI);
        console.log("Mitigation completion rate response status:", response.status);
        
        const data = response.data;
          console.log("Mitigation completion rate data received:", data);
          
          this.mitigationData = {
            avgDays: data.avgDays,
            slaDays: data.slaDays,
            trendData: data.trendData,
            months: data.months
          };
          
          // Update the KPI data
          this.kpiData = {
            ...this.kpiData,
            mitigationCompletionRate: data.completionRate
          };
          
          console.log("Updated KPI data with mitigation completion rate:", this.kpiData.mitigationCompletionRate);
        
      } catch (error) {
        console.error('Error fetching mitigation completion rate data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackMitigationData();
      }
    },
    async fetchRemediationData() {
      try {
        console.log("Fetching average remediation time data from backend...");
        const response = await apiService.get(API_ENDPOINTS.RISK_AVG_REMEDIATION_TIME);
        console.log("Remediation time response status:", response.status);
        
        const data = response.data;
          console.log("Average remediation time data received:", data);
          this.remediationData = {
            current: data.current,
            slaThreshold: data.slaDays,
            trendData: data.trendData,
            months: data.months,
            percentageChange: data.percentageChange,
            overdueCount: data.overdueCount,
            overduePercentage: data.overduePercentage,
            totalActive: data.totalActive,
            minValue: data.minValue,
            maxValue: data.maxValue
          };
          
          // Update the KPI data
          this.kpiData = {
            ...this.kpiData,
            avgRemediationTime: data.current
          };
          
          console.log("Updated KPI data with avg remediation time:", this.kpiData.avgRemediationTime);
        
      } catch (error) {
        console.error('Error fetching remediation time data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackRemediationData();
      }
    },
    async fetchRecurrenceData() {
      try {
        console.log("Fetching recurrence rate data from backend...");
        const response = await apiService.get(API_ENDPOINTS.RISK_RECURRENCE_RATE);
        console.log("Recurrence rate response status:", response.status);
        
        const data = response.data;
          console.log("Recurrence rate data received:", data);
          
          this.recurrenceData = {
            recurrenceRate: data.recurrenceRate,
            oneTimeRate: data.oneTimeRate,
            percentageChange: data.percentageChange,
            trendData: data.trendData,
            months: data.months,
            breakdown: data.breakdown,
            totalRisks: data.totalRisks,
            recurringRisks: data.recurringRisks,
            oneTimeRisks: data.oneTimeRisks,
            topRecurringRisks: data.topRecurringRisks
          };
          
          // Update the KPI data
          this.kpiData = {
            ...this.kpiData,
            recurrenceRate: data.recurrenceRate
          };
          
          console.log("Updated KPI data with recurrence rate:", this.kpiData.recurrenceRate);
        
      } catch (error) {
        console.error('Error fetching recurrence data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackRecurrenceData();
      }
    },
    async fetchResponseData() {
      try {
        console.log("Fetching incident response time data from backend...");
        const response = await apiService.get(API_ENDPOINTS.RISK_AVG_INCIDENT_RESPONSE_TIME);
        console.log("Incident response time response status:", response.status);
        
        const data = response.data;
          console.log("Incident response time data received:", data);
          
          this.responseData = {
            current: data.current,
            target: data.target,
            sla: data.sla,
            percentageChange: data.percentageChange,
            trendData: data.trendData,
            months: data.months,
            delayedCount: data.delayedCount,
            delayedPercentage: data.delayedPercentage,
            totalIncidents: data.totalIncidents
          };
          
          // Update the KPI data
          this.kpiData = {
            ...this.kpiData,
            avgResponseTime: data.current
          };
          
          console.log("Updated KPI data with avg response time:", this.kpiData.avgResponseTime);
        
      } catch (error) {
        console.error('Error fetching incident response time data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackResponseData();
      }
    },
    async fetchMitigationCostData() {
      try {
        console.log("Fetching mitigation cost data...");
        const response = await apiService.get(`/api/risk/mitigation-cost/?timeRange=${this.mitigationCostPeriod}`);
        
        this.mitigationCostData = response.data;
        console.log("Data received:", this.mitigationCostData);
      } catch (error) {
        console.error('Error fetching mitigation cost data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackMitigationCostData();
      }
    },
    async fetchIdentificationData() {
      try {
        console.log("Fetching risk identification rate data...");
        const response = await apiService.get(`/api/risk/identification-rate/?timeRange=${this.identificationPeriod}`);
        
        this.identificationData = response.data;
        console.log("Data received:", this.identificationData);
      } catch (error) {
        console.error('Error fetching identification rate data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackIdentificationData();
      }
    },
    async fetchDueMitigationData() {
      try {
        console.log("Fetching due mitigation data...");
        const response = await apiService.get(`/api/risk/due-mitigation/?timeRange=${this.dueMitigationPeriod}`);
        
        this.dueMitigationData = response.data;
        console.log("Data received:", this.dueMitigationData);
      } catch (error) {
        console.error('Error fetching due mitigation data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackDueMitigationData();
      }
    },
    async fetchClassificationData() {
      try {
        const response = await apiService.get(API_ENDPOINTS.RISK_CLASSIFICATION_ACCURACY);
        this.classificationData = response.data;
      } catch (error) {
        console.error('Error fetching classification accuracy data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackClassificationData();
      }
    },
    async fetchInitiativeData() {
      try {
        console.log("============================================");
        console.log("Fetching improvement initiatives data from backend...");
        
        // Make sure this URL points to where your Django server is running
        const baseUrl = window.location.hostname === 'localhost' 
          ? 'http://localhost:8000' 
          : '';
        console.log("Base URL for API calls:", baseUrl);
        
        const url = `${baseUrl}/api/risk/improvement-initiatives/`;
        console.log("Full URL for improvement initiatives API:", url);
        
        const response = await apiService.get(url);
        console.log("Improvement initiatives response status:", response.status);
        console.log("Improvement initiatives response headers:", response.headers);
        
        const data = response.data;
          console.log("Improvement initiatives data received:", data);
          console.log("Received completionPercentage:", data.completionPercentage);
          console.log("Received completedCount:", data.completedCount);
          console.log("Received totalCount:", data.totalCount);
          
          this.initiativeData = data;
          
          // Log the state after assignment
          console.log("Component state after assignment:", this.initiativeData);
          console.log("============================================");
        
      } catch (error) {
        console.error('Error fetching initiative data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackInitiativeData();
      }
    },
    async fetchImpactData() {
      try {
        console.log("============================================");
        console.log("Fetching risk impact data from backend...");
        
        // Make sure this URL points to where your Django server is running
        const baseUrl = window.location.hostname === 'localhost' 
          ? 'http://localhost:8000' 
          : '';
        console.log("Base URL for API calls:", baseUrl);
        
        const url = `${baseUrl}/api/risk/impact/`;
        console.log("Full URL for risk impact API:", url);
        
        const response = await apiService.get(url);
        console.log("Risk impact response status:", response.status);
        console.log("Risk impact response headers:", response.headers);
        
        const data = response.data;
          console.log("Risk impact data received:", data);
          console.log("Received overallScore:", data.overallScore);
          console.log("Received top risks:", data.topRisks?.length || 0);
          console.log("Received total risks:", data.total_risks);
          
          this.impactData = data;
          
          // Log the state after assignment
          console.log("Component state after assignment:", this.impactData);
          console.log("============================================");
        
      } catch (error) {
        console.error('Error fetching impact data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackImpactData();
      }
    },
    async fetchSeverityData() {
      try {
        const response = await apiService.get(API_ENDPOINTS.RISK_SEVERITY);
        this.severityData = response.data;
      } catch (error) {
        console.error('Error fetching severity data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackSeverityData();
      }
    },
    async fetchExposureScoreData() {
      try {
        const response = await apiService.get(API_ENDPOINTS.RISK_EXPOSURE_SCORE);
        this.exposureScoreData = response.data;
      } catch (error) {
        console.error('Error fetching exposure score data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackExposureScoreData();
      }
    },
    async fetchResilienceData() {
      try {
        console.log("Fetching risk resilience data from backend...");
        const baseUrl = window.location.hostname === 'localhost' 
          ? 'http://localhost:8000' 
          : '';
        const response = await apiService.get(`${baseUrl}/api/risk/resilience/`);
        console.log("Risk resilience response status:", response.status);
        
        const data = response.data;
          console.log("Risk resilience data received:", data);
          this.resilienceData = data;
          
          // Log the values after assignment
          console.log("Resilience data in component:", this.resilienceData);
        
      } catch (error) {
        console.error('Error fetching resilience data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackResilienceData();
      }
    },
    async fetchAssessmentFrequencyData() {
      try {
        const response = await apiService.get(API_ENDPOINTS.RISK_ASSESSMENT_FREQUENCY);
        this.assessmentData = response.data;
      } catch (error) {
        console.error('Error fetching assessment frequency data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackAssessmentData();
      }
    },
    async fetchAssessmentConsensusData() {
      try {
        // Temporarily keep the old endpoint for backward compatibility
        const response = await apiService.get(API_ENDPOINTS.RISK_ASSESSMENT_CONSENSUS);
        this.consensusData = response.data;
      } catch (error) {
        console.error('Error fetching assessment consensus data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackConsensusData();
      }
      
      // Fetch the new approval rate data
      await this.fetchApprovalRateData();
    },
    async fetchApprovalRateData() {
      try {
        console.log("Fetching risk approval rate and cycle data...");
        const baseUrl = window.location.hostname === 'localhost' 
          ? 'http://localhost:8000' 
          : '';
        const response = await apiService.get(`${baseUrl}/api/risk/approval-rate-cycle/`);
        console.log("Approval rate cycle response status:", response.status);
        
        const data = response.data;
          console.log("Risk approval rate and cycle data received:", data);
          this.approvalRateData = data;
        
      } catch (error) {
        console.error('Error fetching approval rate data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackApprovalRateData();
      }
    },
    setFallbackApprovalRateData() {
      this.approvalRateData = {
        approvalRate: 81,
        avgReviewCycles: 3.2,
        maxReviewCycles: 4
      };
    },
    async fetchRegisterUpdateFrequency() {
      try {
        console.log("Fetching risk register update frequency data from backend...");
        const baseUrl = window.location.hostname === 'localhost' 
          ? 'http://localhost:8000' 
          : '';
        const response = await apiService.get(`${baseUrl}/api/risk/register-update-frequency/`);
        console.log("Register update frequency response status:", response.status);
        
        const data = response.data;
          console.log("Risk register update frequency data received:", data);
          this.registerUpdateData = data;
        
      } catch (error) {
        console.error('Error fetching register update frequency data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.setFallbackRegisterUpdateData();
      }
    },
    async fetchRecurrenceProbability() {
      try {
        console.log("Fetching risk recurrence probability data from backend...");
        const baseUrl = window.location.hostname === 'localhost' 
          ? 'http://localhost:8000' 
          : '';
        const response = await apiService.get(`${baseUrl}/api/risk/recurrence-probability/`);
        console.log("Risk recurrence probability response status:", response.status);
        
        const data = response.data;
          console.log("Risk recurrence probability data received:", data);
          console.log("Received averageProbability:", data.averageProbability);
          console.log("Received percentageChange:", data.percentageChange);
          console.log("Received probabilityRanges:", data.probabilityRanges);
          console.log("Received highRecurrenceRisks:", data.highRecurrenceRisks);
          
          this.recurrenceProbabilityData = data;
          
          // Log the state after assignment
          console.log("Component state after assignment:", this.recurrenceProbabilityData);
        
      } catch (error) {
        console.error('Error fetching recurrence probability data:', error);
        this.setFallbackRecurrenceProbabilityData();
      }
    },
    async fetchToleranceThresholds() {
      try {
        console.log('Fetching risk tolerance thresholds data...');
        // Use the correct URL format and handle both localhost and production
        const baseUrl = window.location.hostname === 'localhost' 
          ? 'http://localhost:8000' 
          : '';
        const response = await apiService.get(`${baseUrl}/api/risk/tolerance-thresholds/`);
        console.log('Risk tolerance thresholds API response status:', response.status);
        
        const data = response.data;
          console.log('Risk tolerance thresholds data received:', data);
          this.toleranceData = data;
        
      } catch (error) {
        console.error('Error fetching tolerance thresholds data:', error);
        this.setFallbackToleranceData();
      }
    },
    async fetchRiskAppetite() {
      try {
        console.log('Fetching risk appetite data...');
        // Use the correct URL format and handle both localhost and production
        const baseUrl = window.location.hostname === 'localhost' 
          ? 'http://localhost:8000' 
          : '';
        const response = await apiService.get(`${baseUrl}/api/risk/appetite/`);
        console.log('Risk appetite API response status:', response.status);
        
        const data = response.data;
          console.log('Risk appetite data received:', data);
          this.appetiteData = data;
        
      } catch (error) {
        console.error('Error fetching risk appetite data:', error);
        this.setFallbackAppetiteData();
      }
    },
    async fetchRiskSeverity() {
      try {
        console.log('Fetching risk severity data...');
        // Use the correct URL format and handle both localhost and production
        const baseUrl = window.location.hostname === 'localhost' 
          ? 'http://localhost:8000' 
          : '';
        const response = await axios.get(`${baseUrl}/api/risk/severity/`);
        console.log('Risk severity API response:', response);
        
        if (response.status === 200 && response.data) {
          console.log('Risk severity data received:', response.data);
          
          // Update data properties with received data or defaults
          this.severityDistribution = response.data.severityDistribution || {
            Low: 20,
            Medium: 40,
            High: 25,
            Critical: 15
          };
          this.severityPercentages = response.data.severityPercentages || {
            Low: 20,
            Medium: 40,
            High: 25,
            Critical: 15
          };
          this.averageSeverity = response.data.averageSeverity || 6.8;
          this.trendData = response.data.trendData || [];
          this.topSevereRisks = response.data.topSevereRisks || [];
          
          // Set most severe risk
          if (this.topSevereRisks && this.topSevereRisks.length > 0) {
            const topRisk = this.topSevereRisks[0];
            this.mostSevereRisk = `${topRisk.title} (${topRisk.severity})`;
          } else {
            this.mostSevereRisk = 'No data';
          }
        } else {
          console.error('Invalid response from risk severity API');
          this.setFallbackSeverityData();
        }
      } catch (error) {
        console.error('Error fetching risk severity data:', error);
        this.setFallbackSeverityData();
      }
    },
    setFallbackData() {
      this.kpiData = {
        activeRisks: 48,
        riskExposure: 872,
        riskRecurrence: 6.5,
        mitigationCompletionRate: 76,
        avgRemediationTime: 35,
        recurrenceRate: 6.5,
        avgResponseTime: 6,
        mitigationCost: 184,
        identificationRate: 88,
        dueMitigation: 22,
        classificationAccuracy: 88,
        exposureScore: 75,
        resilienceHours: 5,
        months: ['J', 'F', 'M', 'A', 'M', 'J'],
        riskReductionTrend: {
          start: 45,
          new: 15,
          end: 35
        }
      };
    },
    setFallbackActiveRisksTrend() {
      const trendData = [41, 45, 43, 48, 45, 48];
      this.activeRisksData = {
        current: 48,
        months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        trendData: trendData,
        percentageChange: 4.3,
        minValue: Math.min(...trendData),
        maxValue: Math.max(...trendData),
        range: Math.max(...trendData) - Math.min(...trendData)
      };
    },
    setFallbackExposureTrend() {
      const trendData = [820, 845, 860, 880, 865, 872];
      this.exposureData = {
        current: 872,
        months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        trendData: trendData,
        percentageChange: 0.8,
        minValue: Math.min(...trendData),
        maxValue: Math.max(...trendData),
        range: Math.max(...trendData) - Math.min(...trendData)
      };
    },
    setFallbackReductionTrend() {
      this.reductionData = {
        startCount: 45,
        newCount: 15,
        mitigatedCount: 25,
        endCount: 35,
        reductionPercentage: 25.0
      };
    },
    setFallbackCriticalityData() {
      this.criticalityData = {
        count: 6,
        highCount: 4,
        criticalCount: 2,
        percentage: 8.5,
        months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        trendData: [5, 4, 6, 7, 5, 6]
      };
      
      // Update the UI with fallback data
      this.kpiData = {
        ...this.kpiData,
        highCriticalityRisks: this.criticalityData.count
      };
    },
    setFallbackMitigationData() {
      this.mitigationData = {
        avgDays: 14,
        slaDays: 21,
        trendData: [18, 16, 14, 15, 13, 14],
        months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
      };
      
      // Also set the fallback value for kpiData
      this.kpiData = {
        ...this.kpiData,
        mitigationCompletionRate: 76
      };
    },
    setFallbackRemediationData() {
      const trendData = [38, 36, 35, 37, 34, 35];
      this.remediationData = {
        current: 35,
        slaThreshold: 30,
        trendData: trendData,
        months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        percentageChange: 2.5,
        overdueCount: 12,
        overduePercentage: 15,
        totalActive: 80,
        minValue: Math.min(...trendData),
        maxValue: Math.max(...trendData)
      };
    },
    setFallbackRecurrenceData() {
      const trendData = [5.8, 6.2, 6.7, 6.3, 6.8, 6.5];
      this.recurrenceData = {
        recurrenceRate: 6.5,
        oneTimeRate: 93.5,
        totalRisks: 200,
        recurringRisks: 13,
        oneTimeRisks: 187,
        percentageChange: -0.3,
        trendData: trendData,
        months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        breakdown: {
          'Security': 8.4,
          'Compliance': 5.2,
          'Operational': 7.3,
          'Financial': 4.8
        },
        topRecurringRisks: [
          {id: 1, title: 'System Outage', category: 'Operational', count: 4, owner: 'IT Department'},
          {id: 2, title: 'Data Quality Issues', category: 'Technology', count: 3, owner: 'Data Team'},
          {id: 3, title: 'Vendor Delivery Delays', category: 'Supply Chain', count: 3, owner: 'Procurement'},
          {id: 4, title: 'Staff Turnover', category: 'HR', count: 2, owner: 'HR Department'},
          {id: 5, title: 'Security Breach', category: 'Security', count: 2, owner: 'Security Team'}
        ]
      };
    },
    setFallbackResponseData() {
      const trendData = [7.2, 6.8, 6.5, 6.3, 6.1, 6.0];
      this.responseData = {
        current: 6,
        target: 4,
        sla: 8,
        percentageChange: -1.6,
        trendData: trendData,
        months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        delayedCount: 8,
        delayedPercentage: 12.5,
        totalIncidents: 64,
        minValue: Math.min(...trendData),
        maxValue: Math.max(...trendData)
      };
      
      // Also update the KPI data
      this.kpiData = {
        ...this.kpiData,
        avgResponseTime: 6
      };
    },
    setFallbackMitigationCostData() {
      this.mitigationCostData = {
        totalCost: 184,
        avgCost: 31,
        highestCost: 42,
        highestCategory: 'Security',
        percentageChange: 5.7,
        monthlyData: [
          { month: 'Jan', cost: 35 },
          { month: 'Feb', cost: 28 },
          { month: 'Mar', cost: 42 },
          { month: 'Apr', cost: 31 },
          { month: 'May', cost: 25 },
          { month: 'Jun', cost: 23 }
        ]
      };
    },
    setFallbackIdentificationData() {
      const trendData = [75, 82, 88, 92, 85, 88];
      this.identificationData = {
        current: 88,
        dailyAverage: 4.2,
        percentageChange: 3.5,
        trendData: trendData,
        months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        minValue: Math.min(...trendData),
        maxValue: Math.max(...trendData)
      };
    },
    setFallbackDueMitigationData() {
      this.dueMitigationData = {
        overduePercentage: 22,
        completedPercentage: 50,
        pendingPercentage: 28,
        overdueCount: 8,
        totalCount: 36,
        percentageChange: 2.8
      };
    },
    setFallbackClassificationData() {
      this.classificationData = {
        accuracy: 88,
        percentageChange: 2.3,
        categoryAccuracy: {
          'Compliance': 92,
          'Operational': 87,
          'Security': 85,
          'Financial': 90
        },
        timeSeriesData: [
          { month: 'Jan', value: 84 },
          { month: 'Feb', value: 85 },
          { month: 'Mar', value: 86 },
          { month: 'Apr', value: 87 },
          { month: 'May', value: 86 },
          { month: 'Jun', value: 88 }
        ]
      };
    },
    setFallbackInitiativeData() {
      this.initiativeData = {
        completionPercentage: 76,
        totalCount: 25,
        completedCount: 19,
        pendingCount: 6,
        categoryBreakdown: {
          'Security': {
            'total': 10,
            'completed': 8
          },
          'Compliance': {
            'total': 8,
            'completed': 6
          },
          'Process': {
            'total': 7,
            'completed': 5
          }
        }
      };
    },
    setFallbackImpactData() {
      // Create more realistic fallback data that matches what would come from the database
      this.impactData = {
        overallScore: 5.7,  // Updated to match the SQL query result
        impactDistribution: {
          operational: {
            low: 15,
            medium: 30,
            high: 20,
            critical: 10
          },
          financial: {
            low: 20,
            medium: 25,
            high: 20,
            critical: 10
          }
        },
        topRisks: [
          {
            id: 1,
            title: 'Service Outage',
            operational_impact: 8.5,
            financial_impact: 9.2,
            category: 'Operational'
          },
          {
            id: 2,
            title: 'Data Breach',
            operational_impact: 7.2,
            financial_impact: 9.5,
            category: 'Security'
          },
          {
            id: 3,
            title: 'Compliance Violation',
            operational_impact: 6.8,
            financial_impact: 8.1,
            category: 'Compliance'
          },
          {
            id: 4,
            title: 'Supply Chain Disruption',
            operational_impact: 9.1,
            financial_impact: 7.4,
            category: 'Operational'
          },
          {
            id: 5,
            title: 'Market Volatility',
            operational_impact: 5.6,
            financial_impact: 8.7,
            category: 'Financial'
          }
        ],
        total_risks: 25
      };
    },
    setFallbackSeverityData() {
      this.severityDistribution = {
        Low: 20,
        Medium: 40,
        High: 25,
        Critical: 15
      };
      this.severityPercentages = {
        Low: 20,
        Medium: 40,
        High: 25,
        Critical: 15
      };
      this.averageSeverity = 6.8;
      this.topSevereRisks = [
        {id: 1, title: 'Data Center Failure', severity: 9.5, category: 'Infrastructure'},
        {id: 2, title: 'Critical Data Breach', severity: 9.2, category: 'Security'},
        {id: 3, title: 'Regulatory Non-Compliance', severity: 8.7, category: 'Compliance'},
        {id: 4, title: 'Key Supplier Failure', severity: 8.4, category: 'Supply Chain'},
        {id: 5, title: 'Critical System Outage', severity: 8.1, category: 'Technology'}
      ];
      this.mostSevereRisk = 'Data Center Failure (9.5)';
    },
    setFallbackExposureScoreData() {
      this.exposureScoreData = {
        overallScore: 75,
        riskPoints: [
          {
            id: 1,
            title: 'Data Center Outage',
            impact: 8.7,
            likelihood: 7.2,
            category: 'Infrastructure',
            exposure: 6.3
          },
          {
            id: 2,
            title: 'Sensitive Data Breach',
            impact: 9.1,
            likelihood: 6.5,
            category: 'Security',
            exposure: 5.9
          },
          {
            id: 3,
            title: 'Regulatory Non-Compliance',
            impact: 8.4,
            likelihood: 5.8,
            category: 'Compliance',
            exposure: 4.9
          },
          {
            id: 4,
            title: 'Critical System Failure',
            impact: 8.2,
            likelihood: 5.5,
            category: 'Technology',
            exposure: 4.5
          },
          {
            id: 5,
            title: 'Supply Chain Disruption',
            impact: 7.9,
            likelihood: 6.8,
            category: 'Operational',
            exposure: 5.4
          },
          {
            id: 6,
            title: 'Financial Fraud',
            impact: 7.6,
            likelihood: 4.2,
            category: 'Financial',
            exposure: 3.2
          }
        ],
        categoryDistribution: {
          'Infrastructure': 1,
          'Security': 1,
          'Compliance': 1,
          'Technology': 1,
          'Operational': 1,
          'Financial': 1
        }
      };
    },
    setFallbackResilienceData() {
      // Create fallback data that matches the structure from the backend
      this.resilienceData = {
        avgDowntime: 4.6, // Match the actual SQL query result showing 4.6
        avgRecovery: 3.9, // Set a reasonable value for recovery time average
        categoryData: [
          // Match the actual SQL query categories from the second image
          { category: 'Security', downtime: 4.8, recovery: 5.0 },
          { category: 'Operational', downtime: 4.0, recovery: 3.5 },
          { category: 'Financial', downtime: 5.0, recovery: 4.1 },
          { category: 'Compliance', downtime: 5.3, recovery: 2.8 }
        ],
        months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        trendData: [] // Empty as we don't have historical data yet
      };
    },
    setFallbackAssessmentData() {
      this.assessmentData = {
        avgReviewFrequency: 60,
        categoryFrequencies: {
          'Security': 45,
          'Operational': 55,
          'Compliance': 35,
          'Financial': 65,
          'Strategic': 75
        },
        mostReviewed: [
          {id: 1, title: 'Data Breach', reviews: 7, last_review: '2023-06-10', category: 'Security'},
          {id: 2, title: 'Regulatory Non-Compliance', reviews: 6, last_review: '2023-06-05', category: 'Compliance'},
          {id: 3, title: 'System Outage', reviews: 5, last_review: '2023-05-28', category: 'Operational'}
        ],
        overdueReviews: [
          {id: 6, title: 'Market Volatility', last_review: '2023-03-10', days_overdue: 45, category: 'Financial'},
          {id: 7, title: 'Talent Shortage', last_review: '2023-02-15', days_overdue: 60, category: 'Strategic'},
          {id: 8, title: 'Legacy System Failure', last_review: '2023-04-05', days_overdue: 30, category: 'Technology'}
        ],
        months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        monthlyReviews: [15, 18, 22, 17, 20, 23],
        overdueCount: 3,
        totalRisks: 65
      };
    },
    setFallbackConsensusData() {
      this.consensusData = {
        consensusPercentage: 75,
        totalAssessments: 120,
        consensusCount: 90,
        noConsensusCount: 30,
        categoryConsensus: {
          'Security': 80,
          'Operational': 70,
          'Compliance': 85,
          'Financial': 75,
          'Strategic': 65
        },
        lowConsensusRisks: [
          {id: 1, title: 'Cloud Migration Security', category: 'Security', reviewers: 4, agreement: '2/4'},
          {id: 2, title: 'Third-party Vendor Assessment', category: 'Operational', reviewers: 3, agreement: '1/3'},
          {id: 3, title: 'New Regulatory Requirements', category: 'Compliance', reviewers: 5, agreement: '3/5'}
        ],
        months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        monthlyConsensus: [70, 72, 68, 75, 78, 75]
      };
    },
    setFallbackRegisterUpdateData() {
      this.registerUpdateData = {
        avgUpdateFrequency: 10,
        months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        monthlyUpdates: [28, 32, 38, 35, 42, 40],
        categoryFrequencies: {
          'Security': 7,
          'Compliance': 12,
          'Operational': 10,
          'Financial': 18,
          'Technology': 9
        },
        dailyUpdates: [2, 1, 3, 0, 2, 4, 1, 3, 2, 1, 0, 2, 3, 5, 2, 1, 3, 4, 2, 1, 0, 2, 3, 1, 2, 3, 1, 4, 2, 3]
      };
    },
    setFallbackRecurrenceProbabilityData() {
      this.recurrenceProbabilityData = {
        averageProbability: 38,
        probabilityRanges: this.defaultProbabilityRanges,
        highRecurrenceRisks: [
          {id: 1, title: 'Service Outage', probability: 85, category: 'Operational'},
          {id: 2, title: 'Data Quality Issues', probability: 78, category: 'Technology'},
          {id: 3, title: 'Staff Turnover', probability: 72, category: 'HR'},
          {id: 4, title: 'Minor Security Breaches', probability: 68, category: 'Security'},
          {id: 5, title: 'Vendor Delivery Delays', probability: 65, category: 'Supply Chain'}
        ],
        trendData: [
          {month: 'Jan', probability: 52.0},
          {month: 'Feb', probability: 49.5},
          {month: 'Mar', probability: 46.2},
          {month: 'Apr', probability: 43.8},
          {month: 'May', probability: 40.5},
          {month: 'Jun', probability: 38.0}
        ],
        months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        percentageChange: -6.2,
        totalRisks: 100
      };
    },
    setFallbackToleranceData() {
      this.toleranceData = {
        overallStatus: 'Near Limits',
        toleranceThresholds: this.defaultToleranceThresholds,
        alerts: [
          {
            category: 'Operational',
            message: 'Operational risks exceeding defined tolerance threshold by 7.1%',
            date: '2023-06-12'
          }
        ],
        historicalData: {
          'Security': [
            {month: 'Jan', percentage: 85},
            {month: 'Feb', percentage: 88},
            {month: 'Mar', percentage: 90},
            {month: 'Apr', percentage: 92},
            {month: 'May', percentage: 95},
            {month: 'Jun', percentage: 94}
          ],
          'Compliance': [
            {month: 'Jan', percentage: 70},
            {month: 'Feb', percentage: 75},
            {month: 'Mar', percentage: 78},
            {month: 'Apr', percentage: 85},
            {month: 'May', percentage: 80},
            {month: 'Jun', percentage: 83}
          ],
          'Operational': [
            {month: 'Jan', percentage: 90},
            {month: 'Feb', percentage: 95},
            {month: 'Mar', percentage: 100},
            {month: 'Apr', percentage: 105},
            {month: 'May', percentage: 110},
            {month: 'Jun', percentage: 107}
          ]
        },
        months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
      };
    },
    setFallbackAppetiteData() {
      this.appetiteData = {
        currentLevel: 6,
        description: 'Balanced risk approach',
        historicalLevels: [4, 5, 5, 6, 6, 6],
        dates: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        levelDescriptions: {
          low: 'Risk Averse (1-3)',
          medium: 'Balanced (4-7)',
          high: 'Risk Seeking (8-10)'
        }
      };
    },
    getToleranceStatusClass(status) {
      if (!status) return 'status-warning';
      
      if (status === 'Within Limits') return 'status-normal';
      if (status === 'Near Limits') return 'status-warning';
      if (status === 'Exceeding Limits') return 'status-exceeded';
      
      return 'status-warning';
    },
    getCategoryStatusClass(status) {
      if (!status) return 'status-normal';
      
      if (status === 'Normal') return 'status-normal';
      if (status === 'Warning') return 'status-warning';
      if (status === 'Exceeded') return 'status-exceeded';
      
      return 'status-normal';
    },
    calculateBarHeight(value, dataArray) {
      if (!dataArray || dataArray.length === 0) return 0;
      
      const min = Math.min(...dataArray);
      const max = Math.max(...dataArray);
      
      if (min === max) return 50;
      
      return 20 + (((value - min) / (max - min)) * 80);
    },
    calculatePointPosition(value, minValue, maxValue) {
      if (minValue === undefined || maxValue === undefined) {
        // Fallback to calculating from array if not provided
        const dataArray = this.activeRisksData.trendData || [];
        minValue = Math.min(...dataArray);
        maxValue = Math.max(...dataArray);
      }
      
      const range = maxValue - minValue || 1;
      
      // Calculate percentage from top (0% is top, 100% is bottom)
      // Use 70% of height for chart visibility with padding
      return 100 * (1 - (((value - minValue) / range) * 0.7 + 0.15));
    },
    generateSmoothCurvePath(dataArray, minValue, maxValue) {
      if (!dataArray || dataArray.length < 2) return '';
      
      if (minValue === undefined || maxValue === undefined) {
        // Fallback to calculating from array if not provided
        minValue = Math.min(...dataArray);
        maxValue = Math.max(...dataArray);
      }
      
      const width = 100;
      const height = 30;
      const range = maxValue - minValue || 1;
      
      // Create points array with coordinates
      const points = dataArray.map((value, index) => {
        const x = (index / (dataArray.length - 1)) * width;
        // Use 70% of height for better visibility
        const y = height - (((value - minValue) / range) * 21 + 4.5);
        return { x, y };
      });
      
      // Create a smoother curve with more tension
      let path = `M ${points[0].x},${points[0].y}`;
      
      // Use cubic bezier curves for smoother lines
      for (let i = 0; i < points.length - 1; i++) {
        const cp1x = points[i].x + (points[i+1].x - points[i].x) / 3;
        const cp1y = points[i].y;
        const cp2x = points[i].x + 2 * (points[i+1].x - points[i].x) / 3;
        const cp2y = points[i+1].y;
        
        path += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${points[i+1].x},${points[i+1].y}`;
      }
      
      return path;
    },
    generateSmoothAreaPath(dataArray, minValue, maxValue) {
      if (!dataArray || dataArray.length < 2) return '';
      
      if (minValue === undefined || maxValue === undefined) {
        // Fallback to calculating from array if not provided
        minValue = Math.min(...dataArray);
        maxValue = Math.max(...dataArray);
      }
      
      const width = 100;
      const height = 30;
      const range = maxValue - minValue || 1;
      
      // Create points array with coordinates
      const points = dataArray.map((value, index) => {
        const x = (index / (dataArray.length - 1)) * width;
        // Use 70% of height for better visibility
        const y = height - (((value - minValue) / range) * 21 + 4.5);
        return { x, y };
      });
      
      // Create the path with the same curve algorithm
      let path = `M ${points[0].x},${points[0].y}`;
      
      // Use cubic bezier curves for smoother lines
      for (let i = 0; i < points.length - 1; i++) {
        const cp1x = points[i].x + (points[i+1].x - points[i].x) / 3;
        const cp1y = points[i].y;
        const cp2x = points[i].x + 2 * (points[i+1].x - points[i].x) / 3;
        const cp2y = points[i+1].y;
        
        path += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${points[i+1].x},${points[i+1].y}`;
      }
      
      // Complete the area by drawing down to the bottom right, then bottom left, then closing
      path += ` L ${width},${height} L 0,${height} Z`;
      
      return path;
    },
    calculateWaterfallBarHeight(value) {
      // Maximum value for scaling
      const maxPossibleValue = Math.max(
        this.reductionData.startCount,
        this.reductionData.newCount,
        this.reductionData.mitigatedCount,
        this.reductionData.endCount,
        60 // Fallback max
      );
      
      // Calculate height as percentage of maximum (25% minimum height)
      const heightPercentage = 25 + ((value / maxPossibleValue) * 75);
      return `${heightPercentage}%`;
    },
    generateCriticalityPath(dataArray) {
      if (!dataArray || dataArray.length < 2) return '';
      
      const width = 100;
      const height = 15;
      
      // Find min and max for scaling
      const min = Math.min(...dataArray);
      const max = Math.max(...dataArray);
      const range = max - min || 1;
      
      // Create points
      const points = dataArray.map((value, index) => {
        const x = (index / (dataArray.length - 1)) * width;
        const y = height - (((value - min) / range) * 10 + 2.5);
        return { x, y };
      });
      
      // Create path string
      let path = `M ${points[0].x},${points[0].y}`;
      
      for (let i = 1; i < points.length; i++) {
        // Just use line segments instead of unused curve calculations
        path += ` L ${points[i].x},${points[i].y}`;
      }
      
      return path;
    },
    calculateRemediationY(value) {
      // Map remediation days to y-coordinate for our new SVG viewBox (0-50)
      // Get trend data values or use defaults
      const trendData = this.remediationData.trendData || [30, 35, 32, 38, 33, 35];
      const slaThreshold = this.remediationData.slaThreshold || 30;
      
      // Use max of actual max value or SLA+10 to ensure SLA line is visible
      const maxValue = Math.max(...trendData, slaThreshold + 10);
      const minValue = Math.min(...trendData, slaThreshold - 5);
      const range = maxValue - minValue || 1;
      
      // Calculate position (higher value = higher on chart = smaller y value)
      // Map to 5-35 range within our 0-50 viewBox to keep within visible area
      return 35 - ((value - minValue) / range * 25) + 5;
    },
    generateRemediationPath(dataArray) {
      if (!dataArray || dataArray.length < 2) return '';
      
      const width = 100;
      const points = dataArray.map((value, index) => {
        const x = (index / (dataArray.length - 1)) * width;
        const y = this.calculateRemediationY(value);
        return { x, y };
      });
      
      let path = `M ${points[0].x},${points[0].y}`;
      
      for (let i = 1; i < points.length; i++) {
        // Create smooth curve between points
        const cpx1 = points[i-1].x + (points[i].x - points[i-1].x) / 3;
        const cpy1 = points[i-1].y;
        const cpx2 = points[i].x - (points[i].x - points[i-1].x) / 3;
        const cpy2 = points[i].y;
        path += ` C ${cpx1},${cpy1} ${cpx2},${cpy2} ${points[i].x},${points[i].y}`;
      }
      
      return path;
    },
    calculateRecurrenceY(value) {
      if (!this.recurrenceData.trendData || this.recurrenceData.trendData.length === 0) {
        return 25; // Default middle position for 50px height SVG
      }
      
      const maxValue = Math.max(...this.recurrenceData.trendData) * 1.1; // Add 10% padding
      const minValue = Math.min(...this.recurrenceData.trendData) * 0.9; // Subtract 10% padding
      
      // Invert Y axis (lower values = higher Y position)
      // Map to 10-40 range within our 0-50 viewBox to keep within visible area
      return 40 - ((value - minValue) / (maxValue - minValue || 1) * 30) + 10;
    },
    generateRecurrencePath(dataArray) {
      if (!dataArray || dataArray.length < 2) return '';
      
      const width = 100;
      const points = dataArray.map((value, index) => {
        const x = (index / (dataArray.length - 1)) * width;
        const y = this.calculateRecurrenceY(value);
        return { x, y };
      });
      
      let path = `M ${points[0].x},${points[0].y}`;
      
      for (let i = 1; i < points.length; i++) {
        // Create smooth curve between points
        const cpx1 = points[i-1].x + (points[i].x - points[i-1].x) / 3;
        const cpy1 = points[i-1].y;
        const cpx2 = points[i].x - (points[i].x - points[i-1].x) / 3;
        const cpy2 = points[i].y;
        path += ` C ${cpx1},${cpy1} ${cpx2},${cpy2} ${points[i].x},${points[i].y}`;
      }
      
      return path;
    },
    calculateNeedleEnd(value) {
      // Calculate position for gauge needle
      // Map the value to an angle between 0 (leftmost, 4h or less) and 180 (rightmost, 12h or more)
      const minValue = this.responseData.target / 2 || 2; // half of target is best
      const maxValue = this.responseData.sla * 1.5 || 12; // 1.5x SLA is worst
      
      // Clamp value between min and max
      const clampedValue = Math.max(minValue, Math.min(value, maxValue));
      
      // Map to angle (0 to 180 degrees)
      const angle = ((clampedValue - minValue) / (maxValue - minValue)) * 180;
      
      // Convert angle to radians
      const radians = (angle - 90) * (Math.PI / 180);
      
      // Calculate endpoint (needle length is 25)
      const x = 30 + Math.cos(radians) * 25;
      const y = 35 + Math.sin(radians) * 25;
      
      return { x, y };
    },
    calculateResponseY(value) {
      if (!this.responseData.trendData || this.responseData.trendData.length === 0) {
        return 20; // Default middle position for 40px height SVG
      }
      
      // Cap values for visualization purposes
      const cappedValue = Math.min(value, 50); // Cap at 50 hours for visualization
      
      // Get min and max from capped values
      const cappedTrendData = this.responseData.trendData.map(v => Math.min(v, 50));
      const maxValue = Math.max(...cappedTrendData) * 1.1; // Add 10% padding
      const minValue = Math.min(...cappedTrendData) * 0.9; // Subtract 10% padding
      
      // Invert Y axis (lower values = higher Y position)
      // Map to 5-35 range within our 0-40 viewBox to keep within visible area
      return 35 - ((cappedValue - minValue) / (maxValue - minValue || 1) * 30) + 5;
    },
    generateResponsePath(dataArray) {
      if (!dataArray || dataArray.length < 2) return '';
      
      // Use capped values for visualization
      const cappedData = dataArray.map(v => Math.min(v, 50));
      
      const width = 100;
      const points = cappedData.map((value, index) => {
        const x = (index / (cappedData.length - 1)) * width;
        const y = this.calculateResponseY(value);
        return { x, y };
      });
      
      let path = `M ${points[0].x},${points[0].y}`;
      
      for (let i = 1; i < points.length; i++) {
        // Create smooth curve between points
        const cpx1 = points[i-1].x + (points[i].x - points[i-1].x) / 3;
        const cpy1 = points[i-1].y;
        const cpx2 = points[i].x - (points[i].x - points[i-1].x) / 3;
        const cpy2 = points[i].y;
        path += ` C ${cpx1},${cpy1} ${cpx2},${cpy2} ${points[i].x},${points[i].y}`;
      }
      
      return path;
    },
    getResponseStrokeColor(value) {
      const target = this.responseData.target || 4;
      const sla = this.responseData.sla || 8;
      
      if (value <= target) return '#10b981'; // Green - good
      if (value <= sla) return '#f59e0b'; // Yellow/Orange - warning
      return '#ef4444'; // Red - bad
    },
    getResponsePointColor(value) {
      const target = this.responseData.target || 4;
      const sla = this.responseData.sla || 8;
      
      if (value <= target) return '#10b981'; // Green - good
      if (value <= sla) return '#f59e0b'; // Yellow/Orange - warning
      return '#ef4444'; // Red - bad
    },
    calculateCostBarHeight(cost) {
      if (!this.mitigationCostData.monthlyData || this.mitigationCostData.monthlyData.length === 0) {
        return 50; // Default height
      }
      
      // Find the highest cost to scale the bars
      const costs = this.mitigationCostData.monthlyData.map(item => item.cost);
      const maxCost = Math.max(...costs);
      
      // Scale to percentage height (max 85%)
      return (cost / maxCost) * 85;
    },
    generatePieSegment(cx, cy, r, width, startPercent, endPercent) {
      // Convert percentages to degrees (0-360)
      const startAngle = (startPercent / 100) * 360 - 90; // Start from top (-90 degrees)
      const endAngle = (endPercent / 100) * 360 - 90;
      
      // Calculate outer and inner radius for donut
      const outerRadius = r;
      const innerRadius = r - width;
      
      // Calculate start and end points
      const startOuterX = cx + outerRadius * Math.cos(startAngle * Math.PI / 180);
      const startOuterY = cy + outerRadius * Math.sin(startAngle * Math.PI / 180);
      const endOuterX = cx + outerRadius * Math.cos(endAngle * Math.PI / 180);
      const endOuterY = cy + outerRadius * Math.sin(endAngle * Math.PI / 180);
      
      const startInnerX = cx + innerRadius * Math.cos(endAngle * Math.PI / 180);
      const startInnerY = cy + innerRadius * Math.sin(endAngle * Math.PI / 180);
      const endInnerX = cx + innerRadius * Math.cos(startAngle * Math.PI / 180);
      const endInnerY = cy + innerRadius * Math.sin(startAngle * Math.PI / 180);
      
      // Determine which arc to draw (large or small)
      const largeArcFlag = endPercent - startPercent > 50 ? 1 : 0;
      
      // Create SVG path
      return `M ${startOuterX} ${startOuterY} 
              A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${endOuterX} ${endOuterY}
              L ${startInnerX} ${startInnerY} 
              A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${endInnerX} ${endInnerY}
              Z`;
    },
    generateArcPath(cx, cy, radius, startPercent, endPercent) {
      // Convert percentages to radians
      const startAngle = (startPercent / 100) * Math.PI * 2 - Math.PI/2;
      const endAngle = (endPercent / 100) * Math.PI * 2 - Math.PI/2;
      
      // Calculate start and end points
      const startX = cx + radius * Math.cos(startAngle);
      const startY = cy + radius * Math.sin(startAngle);
      const endX = cx + radius * Math.cos(endAngle);
      const endY = cy + radius * Math.sin(endAngle);
      
      // Determine if we need a large arc (more than 180 degrees)
      const largeArcFlag = endPercent - startPercent > 50 ? 1 : 0;
      
      // Create SVG path
      return `M ${cx} ${cy} L ${startX} ${startY} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${endX} ${endY} Z`;
    },
    getCategoryClass(category) {
      if (!category) return '';
      return category.toLowerCase();
    },
    getTopRisks(risks) {
      if (!risks || risks.length === 0) return [];
      // Return top 4 risks by exposure
      return risks.slice(0, 4);
    },
    calculateAssessmentBarHeight(count) {
      // Calculate percentage height based on max count value
      const maxCount = Math.max(...(this.assessmentData.monthlyReviews || [25]));
      return (count / maxCount) * 85; // Max 85% height
    },
    calculateCategoryBarWidth(days) {
      // Find the maximum days value to scale the bars
      const values = Object.values(this.assessmentData.categoryFrequencies || {});
      const maxDays = Math.max(...values, 90); // Fallback max of 90 days
      
      // Scale as percentage (longer bars = worse)
      return (days / maxDays) * 100;
    },
    calculateUpdateY(value) {
      if (!this.registerUpdateData.monthlyUpdates || this.registerUpdateData.monthlyUpdates.length === 0) {
        return 25; // Default middle position
      }
      
      const maxValue = Math.max(...this.registerUpdateData.monthlyUpdates) * 1.1; // Add 10% padding
      const minValue = Math.min(...this.registerUpdateData.monthlyUpdates) * 0.9; // Subtract 10% padding
      
      // Invert Y axis (higher values = lower Y position)
      return 45 - ((value - minValue) / (maxValue - minValue) * 40);
    },
    generateRegisterUpdatePath(dataArray) {
      if (!dataArray || dataArray.length < 2) return '';
      
      const width = 100;
      const points = dataArray.map((value, index) => {
        const x = (index / (dataArray.length - 1)) * width;
        const y = this.calculateUpdateY(value);
        return { x, y };
      });
      
      let path = `M ${points[0].x},${points[0].y}`;
      
      for (let i = 1; i < points.length; i++) {
        // Create smooth curve between points
        const cpx1 = points[i-1].x + (points[i].x - points[i-1].x) / 3;
        const cpy1 = points[i-1].y;
        const cpx2 = points[i].x - (points[i].x - points[i-1].x) / 3;
        const cpy2 = points[i].y;
        path += ` C ${cpx1},${cpy1} ${cpx2},${cpy2} ${points[i].x},${points[i].y}`;
      }
      
      return path;
    },
    calculateHistogramBarHeight(count) {
      // Calculate height based on maximum count in the histogram
      const counts = this.recurrenceProbabilityData.probabilityRanges?.map(item => item.count) || 
                    this.defaultProbabilityRanges.map(item => item.count);
      const maxCount = Math.max(...counts);
      
      // Scale to percentage height (min 10%, max 90%)
      return 10 + (count / maxCount) * 80;
    },
    getBarClass(range) {
      // Return CSS class based on probability range
      if (range === '0-20%') return 'very-low-prob';
      if (range === '21-40%') return 'low-prob';
      if (range === '41-60%') return 'med-prob';
      if (range === '61-80%') return 'high-prob';
      if (range === '81-100%') return 'very-high-prob';
      return '';
    },
    calculateAppetitePosition(level) {
      // Convert 1-10 scale to 0-100% position
      if (!level) return 60; // Default position
      
      return ((level - 1) / 9) * 100;
    },
    calculateAppetiteY(value) {
      if (!this.appetiteData.historicalLevels || this.appetiteData.historicalLevels.length === 0) {
        return 15; // Default middle position
      }
      
      // Scale based on 1-10 range (flip the Y axis - lower values higher in chart)
      return 30 - (value * 3);
    },
    getAppetiteDescription(level) {
      if (!level) return 'Balanced';
      
      if (level <= 3) return 'Risk Averse';
      if (level <= 7) return 'Balanced';
      return 'Risk Seeking';
    },
    generateAppetitePath(dataArray) {
      if (!dataArray || dataArray.length < 2) return '';
      
      const width = 100;
      const points = dataArray.map((value, index) => {
        const x = (index / (dataArray.length - 1)) * width;
        const y = this.calculateAppetiteY(value);
        return { x, y };
      });
      
      let path = `M ${points[0].x},${points[0].y}`;
      
      for (let i = 1; i < points.length; i++) {
        // Create smooth curve between points
        const cpx1 = points[i-1].x + (points[i].x - points[i-1].x) / 3;
        const cpy1 = points[i-1].y;
        const cpx2 = points[i].x - (points[i].x - points[i-1].x) / 3;
        const cpy2 = points[i].y;
        path += ` C ${cpx1},${cpy1} ${cpx2},${cpy2} ${points[i].x},${points[i].y}`;
      }
      
      return path;
    },
    calculateGaugeNeedleX(current) {
      // Map the current value to an angle between -Math.PI/2 (left) and Math.PI/2 (right)
      // Cap at maximum display value to prevent gauge from breaking with extreme values
      const maxDisplayHours = 12;
      const clampedValue = Math.min(current, maxDisplayHours);
      
      // Calculate angle (from -90 to +90 degrees in radians)
      const angle = (Math.PI * ((clampedValue / maxDisplayHours) - 0.5));
      
      // Calculate the end point of the needle (70 is the radius of the gauge)
      const radius = 70;
      const length = radius * 0.8; // 80% of radius for needle length
      
      return 100 + Math.cos(angle) * length;
    },
    calculateGaugeNeedleY(current) {
      // Map the current value to an angle between -Math.PI/2 (left) and Math.PI/2 (right)
      // Cap at maximum display value to prevent gauge from breaking with extreme values
      const maxDisplayHours = 12;
      const clampedValue = Math.min(current, maxDisplayHours);
      
      // Calculate angle (from -90 to +90 degrees in radians)
      const angle = (Math.PI * ((clampedValue / maxDisplayHours) - 0.5));
      
      // Calculate the end point of the needle (70 is the radius of the gauge)
      const radius = 70;
      const length = radius * 0.8; // 80% of radius for needle length
      
      return 70 - Math.sin(angle) * length;
    },
    formatResponseTime(value) {
      if (!value) return '0';
      
      // For very large values (over 72 hours), convert to days
      if (value >= 72) {
        const days = Math.floor(value / 24);
        const hours = Math.floor(value % 24);
        return `${days}d ${hours}h`;
      }
      
      // Regular hour display for values under 72 hours
      return value;
    },
    // Add this new method to filter KPI cards
    filterKpiCards() {
      console.log('Filtering KPIs by category:', this.selectedCategory);
      // The actual filtering is done via v-show in the template
    },
    
    // Add this method to check if a KPI should be visible
    isVisible(kpiId) {
      // If 'all' is selected, show all cards
      if (this.selectedCategory === 'all') {
        return true;
      }
      
      // Otherwise, check if the KPI is in the selected category
      return this.kpiCategories[this.selectedCategory].includes(kpiId);
    },
    calculateCycleTimeY(days) {
      // Get all cycle time data
      const cycleTimes = this.approvalRateData.monthlyCycleDays || [10, 12, 14, 16, 18, 20];
      
      // Find min and max for scaling
      const maxDays = Math.max(...cycleTimes, 30); // Cap at 30 days to keep chart readable
      const minDays = Math.min(...cycleTimes, 0);
      const range = maxDays - minDays || 1;
      
      // Map to 0-100 range, invert for SVG coordinates (0 is top)
      return 100 - (((days - minDays) / range) * 80);
    },
    generateCycleTimePath(dataArray) {
      if (!dataArray || dataArray.length < 2) return '';
      
      const width = 100;
      const points = dataArray.map((value, index) => {
        const x = (index / (dataArray.length - 1)) * width;
        const y = this.calculateCycleTimeY(value);
        return { x, y };
      });
      
      let path = `M ${points[0].x},${points[0].y}`;
      
      for (let i = 1; i < points.length; i++) {
        // Create smooth curve between points
        const cpx1 = points[i-1].x + (points[i].x - points[i-1].x) / 3;
        const cpy1 = points[i-1].y;
        const cpx2 = points[i].x - (points[i].x - points[i-1].x) / 3;
        const cpy2 = points[i].y;
        path += ` C ${cpx1},${cpy1} ${cpx2},${cpy2} ${points[i].x},${points[i].y}`;
      }
      
      return path;
    },
    calculateCycleBarHeight(days) {
      // Calculate percentage height based on max cycle time
      const maxCycleTime = Math.max(...(this.approvalRateData.monthlyCycleDays || [20]));
      return (days / maxCycleTime) * 80; // Max 80% height
    },
    
    // Add new method for calculating review cycle distribution bar heights
    calculateDistributionHeight(count) {
      // Calculate percentage height based on max count
      const counts = Object.values(this.approvalRateData.reviewCyclesDistribution || {'1': 20, '2': 15, '3+': 10});
      const maxCount = Math.max(...counts);
      
      // Calculate height (min 10px, max 60px)
      return 10 + ((count / maxCount) * 50);
    },
    getMaxReviewCycles() {
      if (!this.approvalRateData.monthlyCycleDays || this.approvalRateData.monthlyCycleDays.length === 0) {
        return 4; // Default value
      }
      
      // Find the maximum cycle days value
      const maxCycleDays = Math.max(...this.approvalRateData.monthlyCycleDays);
      
      // Estimate review cycles based on days (assuming each cycle takes about 5-7 days)
      // Using 6 days as an average cycle duration
      return Math.ceil(maxCycleDays / 6);
    },
    async fetchIdentificationRate() {
      try {
        // Adjust the URL if your API prefix is different
        const res = await axios.get(API_ENDPOINTS.RISK_IDENTIFICATION_RATE_KPI(), {
          params: { timeRange: '30days' }
        });
        this.identificationRate = res.data.current;
        this.identificationChange = res.data.percentageChange;
        this.avgDailyRisks = res.data.dailyAverage;
        this.identificationTrend = res.data.trendData;
        this.identificationMonths = res.data.months;
      } catch (err) {
        console.error('Failed to fetch identification rate', err);
      }
    },
    getX(idx, total, width) {
      if (total <= 1) return width / 2;
      return (idx / (total - 1)) * (width - 10) + 5; // 5px padding
    },
    getY(val, arr, height) {
      const min = Math.min(...arr);
      const max = Math.max(...arr);
      if (max === min) return height / 2;
      // Invert Y for SVG (0 at top)
      return ((max - val) / (max - min)) * (height - 20) + 10;
    },
    generateAreaPoints(arr, width, height) {
      if (!arr.length) return '';
      let points = arr.map((val, idx) => `${this.getX(idx, arr.length, width)},${this.getY(val, arr, height)}`).join(' ');
      // Close the area polygon
      points += ` ${this.getX(arr.length - 1, arr.length, width)},${height - 5}`;
      points += ` ${this.getX(0, arr.length, width)},${height - 5}`;
      return points;
    },
    generateLinePoints(arr, width, height) {
      return arr.map((val, idx) => `${this.getX(idx, arr.length, width)},${this.getY(val, arr, height)}`).join(' ');
    }
  },
  computed: {
    // Calculate positions for severity segments
    severitySegmentStyles() {
      const low = this.severityPercentages.Low || 0;
      const medium = this.severityPercentages.Medium || 0;
      const high = this.severityPercentages.High || 0;
      const critical = this.severityPercentages.Critical || 0;
      
      return {
        low: { width: `${low}%`, left: '0%' },
        medium: { width: `${medium}%`, left: `${low}%` },
        high: { width: `${high}%`, left: `${low + medium}%` },
        critical: { width: `${critical}%`, left: `${low + medium + high}%` }
      };
    }
  }
}
</script>

<style scoped>
@import './RiskKPI.css';

/* Category filter styles */
.category-filter-container {
  margin: 20px 0;
  padding: 0 20px;
  display: flex;
  align-items: center;
}

.category-filter-container label {
  margin-right: 10px;
  font-weight: bold;
}

.category-filter-container select {
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  background-color: #f8fafc;
  font-size: 14px;
  min-width: 250px;
}

.category-filter-container select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.register-update-chart {
  margin-top: 8px;
}

.probability-histogram {
  margin-top: 8px;
  height: 80px;
}

.histogram-chart {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  height: 60px;
  padding-bottom: 5px;
  border-bottom: 1px solid #e5e7eb;
}

.histogram-bar {
  width: 19%;
  border-radius: 3px 3px 0 0;
  position: relative;
  min-height: 4px;
}

.histogram-bar.very-low-prob {
  background-color: #3b82f6;
}

.histogram-bar.low-prob {
  background-color: #0ea5e9;
}

.histogram-bar.med-prob {
  background-color: #f59e0b;
}

.histogram-bar.high-prob {
  background-color: #f97316;
}

.histogram-bar.very-high-prob {
  background-color: #ef4444;
}

.count-label {
  position: absolute;
  top: -15px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 9px;
  color: #64748b;
  font-weight: 500;
}

.range-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 5px;
}

.range-label {
  width: 19%;
  font-size: 8px;
  color: #64748b;
  text-align: center;
}

.high-probability-risks {
  margin-top: 8px;
  border-top: 1px dashed #e5e7eb;
  padding-top: 5px;
}

.high-prob-title {
  font-size: 9px;
  color: #64748b;
  font-weight: 600;
  margin-bottom: 3px;
}

.high-prob-item {
  display: flex;
  justify-content: space-between;
  font-size: 9px;
  margin-top: 2px;
}

.high-prob-name {
  color: #0a192f;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 70%;
}

.high-prob-value {
  color: #ef4444;
  font-weight: 600;
}

.tolerance-status {
  font-size: 16px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.status-normal {
  color: #10b981;
  background-color: rgba(16, 185, 129, 0.1);
}

.status-warning {
  color: #f59e0b;
  background-color: rgba(245, 158, 11, 0.1);
}

.status-exceeded {
  color: #ef4444;
  background-color: rgba(239, 68, 68, 0.1);
}

.tolerance-chart {
  margin-top: 8px;
}

.tolerance-category {
  margin-bottom: 10px;
}

.category-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2px;
}

.category-name {
  font-size: 10px;
  color: #64748b;
  font-weight: 500;
}

.category-status {
  font-size: 8px;
  font-weight: 600;
  padding: 1px 4px;
  border-radius: 3px;
}

.tolerance-bar-container {
  height: 8px;
  background-color: #e5e7eb;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

.tolerance-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.tolerance-threshold {
  position: absolute;
  top: 0;
  height: 100%;
  width: 2px;
  background-color: #0a192f;
}

.tolerance-percentage {
  position: absolute;
  right: 0;
  top: -14px;
  font-size: 8px;
  color: #64748b;
  font-weight: 500;
}

.tolerance-alerts {
  margin-top: 8px;
  border-top: 1px dashed #e5e7eb;
  padding-top: 5px;
}

.alerts-title {
  font-size: 9px;
  color: #64748b;
  font-weight: 600;
  margin-bottom: 3px;
}

.alert-item {
  display: flex;
  flex-direction: column;
}

.alert-category {
  font-size: 9px;
  font-weight: 600;
  color: #ef4444;
}

.alert-message {
  font-size: 8px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.appetite-slider {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.slider-track {
  width: 100%;
  height: 4px;
  background-color: #e5e7eb;
  border-radius: 2px;
  position: relative;
}

.slider-segments {
  display: flex;
  justify-content: space-between;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
}

.segment {
  width: 25%;
  height: 100%;
  border-radius: 2px;
}

.segment.low {
  background-color: #3b82f6;
}

.segment.medium {
  background-color: #f59e0b;
}

.segment.high {
  background-color: #ef4444;
}

.slider-pointer {
  width: 12px;
  height: 12px;
  background-color: #fff;
  border-radius: 50%;
  border: 2px solid #0a192f;
  position: absolute;
  top: -4px;
  transform: translateX(-50%);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 5px;
}

.appetite-trend {
  margin-top: 10px;
}

.trend-title {
  font-size: 9px;
  color: #64748b;
  font-weight: 600;
  margin-bottom: 3px;
}

.appetite-dates {
  font-size: 8px;
  color: #64748b;
  margin-top: 3px;
}

.appetite-context {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
}

.context-item {
  display: flex;
  flex-direction: column;
}

.context-label {
  font-size: 9px;
  color: #64748b;
  font-weight: 500;
}

.context-value {
  font-size: 8px;
  color: #0a192f;
  font-weight: 600;
}

.appetite-slider-container {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.appetite-gradient-bar {
  width: 100%;
  height: 4px;
  background: linear-gradient(to right, #3b82f6, #f59e0b, #ef4444);
  border-radius: 2px;
  position: relative;
}

.appetite-marker {
  width: 12px;
  height: 12px;
  background-color: #fff;
  border-radius: 50%;
  border: 2px solid #0a192f;
  position: absolute;
  top: -4px;
  transform: translateX(-50%);
}

.appetite-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 5px;
  width: 100%;
}

.label-left, .label-center, .label-right {
  flex: 1;
  text-align: center;
  font-size: 9px;
  color: #64748b;
  font-weight: 500;
}

.historical-section {
  margin-top: 10px;
}

.section-title {
  font-size: 9px;
  color: #64748b;
  font-weight: 600;
  margin-bottom: 3px;
}

.appetite-trend-chart {
  height: 20px;
  position: relative;
}

.appetite-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
}

.appetite-detail {
  display: flex;
  flex-direction: column;
}

.detail-label {
  font-size: 9px;
  color: #64748b;
  font-weight: 500;
}

.detail-value {
  font-size: 8px;
  color: #0a192f;
  font-weight: 600;
}

.recurrence-bars-container {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.recurrence-bar-row {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.bar-label {
  font-size: 9px;
  color: #64748b;
  font-weight: 600;
  margin-bottom: 5px;
}

.bar-value {
  font-size: 8px;
  color: #0a192f;
  font-weight: 600;
}

.recurrence-trend {
  margin-top: 10px;
}

.recurrence-counts {
  margin-top: 10px;
}

.count-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.count-label {
  font-size: 9px;
  color: #64748b;
  font-weight: 600;
}

.count-value {
  font-size: 8px;
  color: #0a192f;
  font-weight: 600;
}

.count-value.highlight {
  color: #ef4444;
}

.response-warning {
  font-size: 10px;
  color: #ef4444;
  margin: 5px 0;
  text-align: center;
  font-weight: 500;
  background-color: rgba(239, 68, 68, 0.1);
  padding: 3px 5px;
  border-radius: 4px;
}

.kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kpi-period-selector select {
  font-size: 9px;
  padding: 2px 4px;
  border-radius: 3px;
  border: 1px solid #e2e8f0;
  background-color: #f8fafc;
  color: #64748b;
  cursor: pointer;
}

.identification-metrics {
  display: flex;
  justify-content: space-between;
  margin: 5px 0;
  font-size: 10px;
  color: #64748b;
}

.metric-item {
  display: flex;
  flex-direction: column;
}

.metric-label {
  font-size: 9px;
  color: #64748b;
}

.metric-value {
  font-weight: 600;
  color: #0a192f;
}

.severity-pie-container {
  margin-top: 10px;
}

.severity-pie {
  width: 100%;
  height: 20px;
}

.legend-color {
  width: 100%;
  height: 100%;
  border-radius: 3px;
}

.legend-label {
  font-size: 8px;
  color: #64748b;
  margin-top: 2px;
}

.legend-value {
  font-size: 10px;
  color: #0a192f;
  font-weight: 600;
}

.severity-legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
}

.legend-item {
  flex: 1;
  text-align: center;
  margin-bottom: 5px;
}

.severity-categories {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
}

.severity-category {
  flex: 1;
  text-align: center;
}

.category-label {
  font-size: 9px;
  color: #64748b;
  font-weight: 600;
}

.category-value {
  font-size: 8px;
  color: #0a192f;
  font-weight: 600;
}

.severity-chart-container {
  margin-top: 10px;
}

.severity-semi-circle {
  width: 100%;
  height: 20px;
  position: relative;
}

.severity-segment {
  height: 100%;
  position: absolute;
}

.severity-segment.low {
  background-color: #3b82f6;
}

.severity-segment.medium {
  background-color: #f59e0b;
}

.severity-segment.high {
  background-color: #f97316;
}

.severity-segment.critical {
  background-color: #ef4444;
}

/* Add these styles to the existing <style scoped> section */

.approval-label {
  font-size: 11px;
  margin-left: 5px;
  color: #64748b;
  font-weight: 500;
}

.approval-metrics {
  display: flex;
  justify-content: space-around;
  margin: 10px 0;
}

.metric-item {
  display: flex;
  align-items: center;
  padding: 5px;
  background-color: #f8fafc;
  border-radius: 4px;
  flex: 1;
  margin: 0 5px;
}

.metric-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #dbeafe;
  border-radius: 50%;
  margin-right: 8px;
  color: #3b82f6;
  font-size: 12px;
}

.metric-details {
  flex: 1;
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.metric-label {
  font-size: 10px;
  color: #64748b;
}

.dual-chart {
  margin-top: 10px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.chart-title {
  font-size: 10px;
  color: #64748b;
  font-weight: 600;
}

.combo-chart {
  position: relative;
  height: 160px;
}

.chart-legend {
  display: flex;
  justify-content: center;
  margin-top: 5px;
}

.legend-item {
  display: flex;
  align-items: center;
  margin: 0 10px;
}

.legend-color {
  width: 12px;
  height: 6px;
  margin-right: 5px;
}

.legend-color.approval-bar {
  background-color: #3b82f6;
}

.legend-color.cycle-line {
  background-color: #ef4444;
  height: 2px;
}

.legend-label {
  font-size: 9px;
  color: #64748b;
}

.section-title {
  font-size: 10px;
  color: #64748b;
  font-weight: 600;
  margin-top: 10px;
  margin-bottom: 5px;
  border-top: 1px dashed #e5e7eb;
  padding-top: 5px;
}

.pending-risk {
  background-color: #fef2f2;
  border-left: 3px solid #ef4444;
  padding: 5px 8px;
  border-radius: 3px;
}

.risk-title {
  font-size: 10px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.risk-details {
  display: flex;
  justify-content: space-between;
  font-size: 9px;
  color: #64748b;
}

.reviewer-count, .days-pending {
  background-color: rgba(239, 68, 68, 0.1);
  padding: 1px 4px;
  border-radius: 3px;
  color: #ef4444;
}

.approval-chart {
  margin-top: 10px;
}

.bar-chart-container {
  width: 100%;
  position: relative;
  margin-bottom: 10px;
}

.cycle-time-chart {
  margin-top: 15px;
  border-top: 1px dashed #e5e7eb;
  padding-top: 10px;
}

.chart-title {
  font-size: 11px;
  color: #64748b;
  font-weight: 600;
  margin-bottom: 5px;
  text-align: center;
}

/* New styles for the chart sections and review cycles distribution */
.chart-section {
  margin-top: 15px;
  padding-top: 10px;
  border-top: 1px dashed #e5e7eb;
}

.chart-section:first-of-type {
  border-top: none;
  margin-top: 10px;
  padding-top: 0;
}

.review-cycles-chart {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 100px;
  padding: 10px 0;
}

.cycle-bar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 30%;
}

.cycle-count {
  font-size: 12px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 5px;
}

.cycle-bar {
  width: 40px;
  background-color: #3b82f6;
  border-radius: 4px 4px 0 0;
  transition: height 0.3s ease;
}

.cycle-label {
  margin-top: 5px;
  font-size: 10px;
  color: #64748b;
  text-align: center;
}

/* New styles for the simplified key metrics */
.key-metrics {
  display: flex;
  justify-content: space-around;
  margin-top: 20px;
}

.metric-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: #f1f5f9;
  padding: 15px;
  border-radius: 8px;
  width: 45%;
}

.metric-icon {
  background-color: #dbeafe;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 10px;
}

.metric-number {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 5px;
}

.metric-label {
  font-size: 12px;
  color: #64748b;
  text-align: center;
}

.kpi-chart {
  margin-top: 10px;
  margin-bottom: 0;
  width: 100%;
  min-height: 60px;
  position: relative;
}

.identification-path {
  stroke: #3b82f6;
  stroke-width: 2;
  fill: none;
}

.identification-area {
  fill: rgba(59, 130, 246, 0.08);
}

.identification-point {
  fill: #3b82f6;
  stroke: #fff;
  stroke-width: 1;
  cursor: pointer;
  transition: r 0.2s;
}

.identification-point:hover {
  r: 4;
}

.month-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
  padding: 0 5px;
}
</style> 
