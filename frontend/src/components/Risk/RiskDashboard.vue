8<template>
  <div class="risk-dashboard-container">
    <!-- Header Section -->
    <div class="risk-dashboard-header">
      <div class="risk-dashboard-header-left">
        <button class="back-arrow-btn" @click="goBackToRiskRegister" title="Back to Risk Register">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h2 class="risk-dashboard-heading">Risk Dashboard</h2>
      </div>
      <div class="risk-dashboard-actions">
        <button class="risk-action-btn refresh"><i class="fas fa-sync-alt"></i> Refresh</button>
        <button 
          class="risk-action-btn export" 
          @click="exportDashboardAsPDF"
          :disabled="isExporting"
          :class="{ 'exporting': isExporting }"
        >
          <i v-if="!isExporting" class="fas fa-download"></i>
          <i v-else class="fas fa-spinner fa-spin"></i>
          {{ isExporting ? 'Exporting...' : 'Export' }}
        </button>
      </div>
    </div>
    
    <!-- Filters Section -->
    <div class="risk-filters-section">
    <div class="risk-dashboard-filters" style="position: relative;">
      <!-- Filter Loading Indicator -->
      <div v-if="isApplyingFilters" class="risk-filter-loading-indicator">
        <div class="loading-spinner"></div>
        <span>Applying filters...</span>
      </div>
      <div class="risk-filter-group">
        <label>Framework</label>
        <select v-model="filters.framework" @change="onFrameworkChange" class="risk-filter-select" :disabled="loadingFrameworks">
          <option value="all">All Frameworks</option>
          <option v-for="framework in frameworks" :key="framework.FrameworkId" :value="framework.FrameworkId">
            {{ framework.FrameworkName }}
          </option>
        </select>
        <div v-if="loadingFrameworks" class="risk-filter-loading">Loading frameworks...</div>
        <div v-if="!loadingFrameworks && frameworks.length === 0" class="risk-filter-error">No frameworks available</div>
        <div v-if="!loadingFrameworks && frameworks.length > 0" class="risk-filter-success">{{ frameworks.length }} frameworks loaded</div>
      </div>
      
      <div class="risk-filter-group">
        <label>Policy</label>
        <select v-model="filters.policy" @change="onPolicyChange" class="risk-filter-select" :disabled="loadingPolicies">
          <option value="all">All Policies</option>
          <option v-for="policy in policies" :key="policy.PolicyId" :value="policy.PolicyId">
            {{ policy.PolicyName }}
          </option>
        </select>
        <div v-if="loadingPolicies" class="risk-filter-loading">Loading policies...</div>
        <div v-if="!loadingPolicies && policies.length === 0" class="risk-filter-error">No policies available</div>
        <div v-if="!loadingPolicies && policies.length > 0" class="risk-filter-success">{{ policies.length }} policies loaded</div>
      </div>
      
      <div class="risk-filter-group">
        <label>Time Range</label>
        <select v-model="filters.timeRange" class="risk-filter-select" @change="handleFilterChange">
          <option v-for="option in timeRangeOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>
      
      <div class="risk-filter-group">
        <label>Category</label>
        <select v-model="filters.category" class="risk-filter-select" @change="handleFilterChange">
          <option v-for="option in categoryOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>
      
      <div class="risk-filter-group">
        <label>Priority</label>
        <select v-model="filters.priority" class="risk-filter-select" @change="handleFilterChange">
          <option value="all">All Priorities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>
      </div>
    </div>
    
    <!-- Metrics Cards Section -->
    <div class="risk-metrics-section">
    <div class="risk-performance-summary">
      <!-- Always show cards, individual cards will display "No data found" if metric is 0 -->
        <div class="risk-summary-card">
            <div class="risk-summary-icon total"><i class="fas fa-exclamation-triangle"></i></div>
          <div class="risk-summary-content">
            <div class="risk-summary-label">Total Risks</div>
            <div v-if="metrics.total > 0" class="risk-summary-value">{{ metrics.total }}</div>
            <div v-else class="risk-summary-value empty">No data found</div>
            <div v-if="metrics.total > 0" class="risk-summary-trend positive">+12 this month</div>
          </div>
        </div>
        
        <div class="risk-summary-card">
            <div class="risk-summary-icon accepted"><i class="fas fa-check-circle"></i></div>
          <div class="risk-summary-content">
            <div class="risk-summary-label">Accepted Risks</div>
            <div v-if="metrics.accepted > 0" class="risk-summary-value">{{ metrics.accepted }}</div>
            <div v-else class="risk-summary-value empty">No data found</div>
            <div v-if="metrics.accepted > 0" class="risk-summary-trend positive">+5 this month</div>
          </div>
        </div>
        
        <div class="risk-summary-card">
            <div class="risk-summary-icon rejected"><i class="fas fa-times-circle"></i></div>
          <div class="risk-summary-content">
            <div class="risk-summary-label">Rejected Risks</div>
            <div v-if="metrics.rejected > 0" class="risk-summary-value">{{ metrics.rejected }}</div>
            <div v-else class="risk-summary-value empty">No data found</div>
            <div v-if="metrics.rejected > 0" class="risk-summary-trend negative">+3 this week</div>
          </div>
        </div>
        
        <div class="risk-summary-card">
            <div class="risk-summary-icon mitigated"><i class="fas fa-shield-alt"></i></div>
          <div class="risk-summary-content">
            <div class="risk-summary-label">Mitigated Risks</div>
            <div v-if="metrics.mitigated > 0" class="risk-summary-value">{{ metrics.mitigated }}</div>
            <div v-else class="risk-summary-value empty">No data found</div>
            <div v-if="metrics.mitigated > 0" class="risk-summary-trend positive">+8 this month</div>
          </div>
        </div>
        
        <div class="risk-summary-card">
            <div class="risk-summary-icon inprogress"><i class="fas fa-spinner"></i></div>
          <div class="risk-summary-content">
            <div class="risk-summary-label">In Progress Risks</div>
            <div v-if="metrics.inProgress > 0" class="risk-summary-value">{{ metrics.inProgress }}</div>
            <div v-else class="risk-summary-value empty">No data found</div>
            <div v-if="metrics.inProgress > 0" class="risk-summary-trend positive">+6 this week</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Row 1: Pie Chart, Bar Chart, and Heatmap Chart in one row -->
    <div class="risk-charts-row risk-charts-row-three">
      <!-- Chart 1: Risk Distribution by Category (Pie Chart) -->
      <div class="risk-chart-card">
        <div class="risk-card-header">
          <h3>Risk Distribution by Category</h3>
        </div>
        <div class="risk-chart-container">
          <div v-if="!categoryDistributionData.labels.length || !categoryDistributionData.datasets[0].data.length" style="text-align:center; color:#aaa; padding:40px;">
            No category data to display.
          </div>
          <Doughnut 
            v-else 
            :key="`category-donut-${categoryChartKey}`" 
            :data="categoryDistributionData" 
            :options="donutChartOptions" 
          />
        </div>
        <!-- Add custom legend container -->
        <div class="risk-chart-legend">
          <div v-for="category in filteredCategories" 
               :key="category.label" 
               class="risk-legend-item"
               @click="handleLegendClick(category.label)"
               :class="{ 'clickable': true }">
            <span class="risk-legend-color" :style="{ backgroundColor: category.color }"></span>
            <span class="risk-legend-label">{{ category.label }}</span>
            <span class="risk-legend-value">{{ category.value }}</span>
          </div>
        </div>
        <div class="risk-chart-insights">
          <div class="risk-insight-item">
            <span class="risk-insight-label">Highest Category:</span>
            <span class="risk-insight-value">{{ highestCategory.name }} ({{ highestCategory.percent }}%)</span>
          </div>
        </div>
      </div>
      <!-- Chart 3: Risk Heatmap -->
      <div class="risk-chart-card risk-heatmap-card">
        <div class="risk-card-header">
          <h3>Risk Matrix Heatmap</h3>
          <div class="risk-heatmap-hint">
            <i class="fas fa-info-circle"></i>
            <span>Click on data points to view risks</span>
          </div>
        </div>
        <div class="risk-heatmap-container">
          <canvas ref="heatmapCanvas"></canvas>
        </div>
      </div>
    </div>
    
    <!-- Row 2: Line Chart and Dynamic Chart -->
    <div class="risk-charts-row-uneven">
      <!-- Chart 3: Risk Trend Over Time (Line Chart) -->
      <div class="risk-chart-card risk-trend">
          <div class="risk-card-header">
          <h3>Risk Trend Over Time</h3>
          </div>
        <div class="risk-chart-container">
          <div v-if="!riskTrendData.labels.length" class="no-chart-data">
            No trend data available
          </div>
          <LineChart v-else :data="riskTrendData" :options="riskTrendOptions" />
        </div>
        <div class="risk-chart-insights">
          <div class="risk-insight-item">
            <span class="risk-insight-label">Trend:</span>
            <span class="risk-insight-value" :class="getTrendClass()">{{ getTrendText() }}</span>
          </div>
        </div>
      </div>
      
      <!-- Chart 4: Dynamic Chart (X and Y Axis Selectable) -->
      <div class="risk-chart-card risk-dynamic-chart">
        <div class="risk-card-header">
          <h3>Custom Risk Analysis</h3>
          <div class="risk-axis-controls">
            <div class="risk-axis-control">
              <label>X-Axis</label>
              <select v-model="selectedXAxis" class="risk-axis-select" @change="fetchCustomAnalysisData">
                <option value="time">Time</option>
                <option value="category">Category</option>
                <option value="priority">Risk Priority</option>
                <option value="criticality">Criticality</option>
                <option value="status">Status</option>
                <option value="appetite">Risk Appetite</option>
                <option value="mitigation">Mitigation Status</option>
              </select>
              </div>
            
            <div class="risk-axis-control">
              <label>Y-Axis</label>
              <select v-model="selectedYAxis" class="risk-axis-select" @change="fetchCustomAnalysisData">
                <option v-for="option in yAxisOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>
          </div>
        </div>
        <div class="risk-chart-container">
          <div class="risk-chart-tabs">
            <button 
              v-for="chartType in ['line', 'bar', 'doughnut']" 
              :key="chartType"
              :class="['risk-chart-tab-btn', { active: activeChart === chartType }]"
              @click="activeChart = chartType"
            >
              <i :class="getChartIcon(chartType)"></i>
            </button>
          </div>
          
          <div class="risk-chart-content">
            <div v-if="isLoadingCustomChart" class="risk-chart-loading">
              <div class="loading-spinner"></div>
              <span>Loading chart data...</span>
            </div>
            <div v-else-if="!hasCustomChartData" class="no-chart-data">
              No data available for selected parameters
            </div>
            <template v-else>
              <LineChart v-if="activeChart === 'line'" :data="lineChartData" :options="customChartOptions" />
              <Bar v-if="activeChart === 'bar'" :data="barChartData" :options="customChartOptions" />
              <Doughnut v-if="activeChart === 'doughnut'" :data="donutChartData" :options="customDonutOptions" />
            </template>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Category Risks Popup -->
    <div v-if="showCategoryPopup" class="risk-category-popup-overlay" @click="closeCategoryPopup">
      <div class="risk-category-popup" @click.stop>
        <div class="risk-category-popup-header">
          <h3>Risks in {{ selectedCategory }}</h3>
          <button class="risk-category-popup-close" @click="closeCategoryPopup">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="risk-category-popup-content">
          <div v-if="isLoadingCategoryRisks" class="risk-category-popup-loading">
            <div class="loading-spinner"></div>
            <span>Loading risks...</span>
          </div>
          
          <div v-else-if="categoryRisks.length === 0" class="risk-category-popup-empty">
            <i class="fas fa-info-circle"></i>
            <span>No risks found for this category</span>
          </div>
          
          <div v-else class="risk-category-popup-list">
            <div v-for="(risk, index) in categoryRisks" :key="risk.RiskInstanceId" class="risk-category-popup-item">
              <div class="risk-category-popup-item-header">
                <div class="risk-category-popup-item-number">{{ index + 1 }}.</div>
                <h4>{{ risk.RiskTitle || 'Untitled Risk' }}</h4>
                <span class="risk-category-popup-item-priority" :class="getPriorityClass(risk.RiskPriority)">
                  {{ risk.RiskPriority || 'N/A' }}
                </span>
              </div>
              
              <div class="risk-category-popup-item-details">
                <div class="risk-category-popup-item-detail">
                  <span class="detail-label">Status:</span>
                  <span class="detail-value" :class="getStatusClass(risk.RiskStatus)">
                    {{ risk.RiskStatus || 'N/A' }}
                  </span>
                </div>
              </div>
              
              <div v-if="risk.RiskDescription" class="risk-category-popup-item-description">
                <span class="detail-label">Description:</span>
                <p>{{ risk.RiskDescription }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <div class="risk-category-popup-footer">
          <span class="risk-category-popup-count">
            Total: {{ categoryRisks.length }} risk{{ categoryRisks.length !== 1 ? 's' : '' }}
          </span>
          <button class="risk-category-popup-close-btn" @click="closeCategoryPopup">
            Close
          </button>
        </div>
      </div>
    </div>
    
    <!-- Heatmap Risks Popup -->
    <div v-if="showHeatmapPopup" class="risk-heatmap-popup-overlay" @click="closeHeatmapPopup">
      <div class="risk-heatmap-popup" @click.stop>
        <div class="risk-heatmap-popup-header">
          <h3>Risks at Impact {{ selectedHeatmapCoordinates.impact }}, Likelihood {{ selectedHeatmapCoordinates.likelihood }}</h3>
          <button class="risk-heatmap-popup-close" @click="closeHeatmapPopup">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="risk-heatmap-popup-content">
          <div v-if="isLoadingHeatmapRisks" class="risk-heatmap-popup-loading">
            <div class="loading-spinner"></div>
            <span>Loading risks...</span>
          </div>
          
          <div v-else-if="heatmapRisks.length === 0" class="risk-heatmap-popup-empty">
            <i class="fas fa-info-circle"></i>
            <span>No risks found for these coordinates</span>
          </div>
          
          <div v-else class="risk-heatmap-popup-list">
            <div v-for="(risk, index) in heatmapRisks" :key="risk.RiskInstanceId" class="risk-heatmap-popup-item">
              <div class="risk-heatmap-popup-item-header">
                <div class="risk-heatmap-popup-item-number">{{ index + 1 }}.</div>
                <h4>{{ risk.RiskTitle || 'Untitled Risk' }}</h4>
                <span class="risk-heatmap-popup-item-priority" :class="getPriorityClass(risk.RiskPriority)">
                  {{ risk.RiskPriority || 'N/A' }}
                </span>
              </div>
              
              <div class="risk-heatmap-popup-item-details">
                <div class="risk-heatmap-popup-item-detail">
                  <span class="detail-label">Status:</span>
                  <span class="detail-value" :class="getStatusClass(risk.RiskStatus)">
                    {{ risk.RiskStatus || 'N/A' }}
                  </span>
                </div>
                <div class="risk-heatmap-popup-item-detail">
                  <span class="detail-label">Impact:</span>
                  <span class="detail-value">{{ risk.RiskImpact || 'N/A' }}</span>
                </div>
                <div class="risk-heatmap-popup-item-detail">
                  <span class="detail-label">Likelihood:</span>
                  <span class="detail-value">{{ risk.RiskLikelihood || 'N/A' }}</span>
                </div>
              </div>
              
              <div v-if="risk.RiskDescription" class="risk-heatmap-popup-item-description">
                <span class="detail-label">Description:</span>
                <p>{{ risk.RiskDescription }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <div class="risk-heatmap-popup-footer">
          <span class="risk-heatmap-popup-count">
            Total: {{ heatmapRisks.length }} risk{{ heatmapRisks.length !== 1 ? 's' : '' }}
          </span>
          <button class="risk-heatmap-popup-close-btn" @click="closeHeatmapPopup">
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, watch, onMounted, onActivated, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { Chart, ArcElement, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from 'chart.js'
import { Doughnut, Bar, Line as LineChart } from 'vue-chartjs'
import '@fortawesome/fontawesome-free/css/all.min.css'
import axios from 'axios'
import AccessUtils from '@/utils/accessUtils'
import { API_ENDPOINTS } from '../../config/api.js'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

Chart.register(ArcElement, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

export default {
  name: 'RiskDashboard',
  components: {
    Doughnut,
    Bar,
    LineChart
  },
  setup() {
    console.log('=== RiskDashboard Component Debug ===')

    const router = useRouter()
    const store = useStore()
    const showRiskDetails = ref(true)
    const selectedXAxis = ref('time')
    const selectedYAxis = ref('performance')
    const categoryChartKey = ref(0)
    
    // Popup state
    const showCategoryPopup = ref(false)
    const selectedCategory = ref('')
    const categoryRisks = ref([])
    const isLoadingCategoryRisks = ref(false)
    
    // Heatmap popup state
    const showHeatmapPopup = ref(false)
    const selectedHeatmapCoordinates = ref({ impact: 0, likelihood: 0 })
    const heatmapRisks = ref([])
    const isLoadingHeatmapRisks = ref(false)
    
    // Watch for axis changes and update chart data accordingly
    watch([selectedXAxis, selectedYAxis], ([newXAxis, newYAxis]) => {
      // Update chart data based on selected axes
      updateChartData(newXAxis, newYAxis)
    })

    // --- CATEGORY DATA FOR ACTIVE/INACTIVE/ON HOLD ---
    const categoryStatusData = {
      Operational: { active: 12, inactive: 3, onhold: 2 },
      Compliance: { active: 10, inactive: 4, onhold: 1 },
      'IT Security': { active: 8, inactive: 6, onhold: 2 },
      Financial: { active: 14, inactive: 2, onhold: 1 },
      Strategic: { active: 9, inactive: 5, onhold: 3 }
    }

    const updateChartData = (xAxis, yAxis) => {
      const labels = getLabelsForXAxis(xAxis)
      let data = getDataForYAxis(yAxis)
      
      // If categories, use status split
      if (xAxis === 'categories') {
        // For donut: sum all active/inactive/onhold
        const active = Object.values(categoryStatusData).reduce((a, c) => a + c.active, 0)
        const inactive = Object.values(categoryStatusData).reduce((a, c) => a + c.inactive, 0)
        const onhold = Object.values(categoryStatusData).reduce((a, c) => a + c.onhold, 0)
        donutChartData.labels = ['Active', 'Inactive', 'On Hold']
        donutChartData.datasets[0].data = [active, inactive, onhold]
        donutChartData.datasets[0].backgroundColor = ['#4ade80', '#f87171', '#fbbf24']

        // For bar/horizontal bar: show each category split
        barChartData.labels = labels
        barChartData.datasets = [
          {
            label: 'Active',
            data: labels.map(l => categoryStatusData[l]?.active || 0),
            backgroundColor: '#4ade80',
            stack: 'Stack 0',
            borderRadius: 4
          },
          {
            label: 'Inactive',
            data: labels.map(l => categoryStatusData[l]?.inactive || 0),
            backgroundColor: '#f87171',
            stack: 'Stack 0',
            borderRadius: 4
          },
          {
            label: 'On Hold',
            data: labels.map(l => categoryStatusData[l]?.onhold || 0),
            backgroundColor: '#fbbf24',
            stack: 'Stack 0',
            borderRadius: 4
          }
        ]
        // For line: show only active for demo
        lineChartData.labels = labels
        lineChartData.datasets[0].data = labels.map(l => categoryStatusData[l]?.active || 0)
        lineChartData.datasets[0].label = 'Active'
        return
      }
      // If status, show Active/Inactive/On Hold as X axis
      if (xAxis === 'status') {
        const statusLabels = ['Active', 'Inactive', 'On Hold']
        // Sum for each status across all categories
        const active = Object.values(categoryStatusData).reduce((a, c) => a + c.active, 0)
        const inactive = Object.values(categoryStatusData).reduce((a, c) => a + c.inactive, 0)
        const onhold = Object.values(categoryStatusData).reduce((a, c) => a + c.onhold, 0)
        const statusData = [active, inactive, onhold]
        // Donut
        donutChartData.labels = statusLabels
        donutChartData.datasets[0].data = statusData
        donutChartData.datasets[0].backgroundColor = ['#4ade80', '#f87171', '#fbbf24']
        // Bar
        barChartData.labels = statusLabels
        barChartData.datasets = [
          {
            label: getYAxisLabel(yAxis),
            data: statusData,
            backgroundColor: ['#4ade80', '#f87171', '#fbbf24'],
            borderRadius: 4
          }
        ]
        // Line
        lineChartData.labels = statusLabels
        lineChartData.datasets[0].data = statusData
        lineChartData.datasets[0].label = getYAxisLabel(yAxis)
        return
      }
      // Default (non-category, non-status) logic
      // Update Line Chart
      lineChartData.labels = labels
      lineChartData.datasets[0].data = data
      lineChartData.datasets[0].label = getYAxisLabel(yAxis)

      // Update Bar Chart
      barChartData.labels = labels
      barChartData.datasets = getBarChartDatasets(yAxis)

      // Update Donut Chart
      donutChartData.labels = labels
      donutChartData.datasets[0].data = data
    }

    const getYAxisLabel = (yAxis) => {
      const labelMap = {
        'count': 'Count',
        'exposure': 'Risk Exposure Rating',
        'impact': 'Risk Impact',
        'likelihood': 'Risk Likelihood',
        'avgExposure': 'Average Exposure',
        'maxExposure': 'Maximum Exposure',
        'mitigated': 'Mitigated Risks',
        'avgImpact': 'Average Impact',
        'avgLikelihood': 'Average Likelihood',
        'responseTime': 'Response Time (days)',
        'mitigationTime': 'Mitigation Time (days)',
        'openRisks': 'Open Risks',
        'reviewCount': 'Review Count',
        'daysInStatus': 'Days in Status',
        'exposureByStatus': 'Exposure by Status',
        'acceptedRisks': 'Accepted Risks',
        'rejectedRisks': 'Rejected Risks',
        'mitigationCost': 'Mitigation Cost',
        'completedMitigations': 'Completed Mitigations',
        'pendingMitigations': 'Pending Mitigations'
      };
      return labelMap[yAxis] || 'Value';
    }

    const getBarChartDatasets = (yAxis) => {
      const baseData = getDataForYAxis(yAxis)
      return [
        {
          label: 'High',
          data: baseData.map(val => Math.round(val * 0.4)),
          backgroundColor: '#4ade80',
          stack: 'Stack 0',
          borderRadius: 4
        },
        {
          label: 'Medium',
          data: baseData.map(val => Math.round(val * 0.35)),
          backgroundColor: '#fbbf24',
          stack: 'Stack 0',
          borderRadius: 4
        },
        {
          label: 'Low',
          data: baseData.map(val => Math.round(val * 0.25)),
          backgroundColor: '#f87171',
          stack: 'Stack 0',
          borderRadius: 4
        }
      ]
    }

    const getLabelsForXAxis = (xAxis) => {
      switch(xAxis) {
        case 'time':
          return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        case 'risks':
          return ['Data Breach', 'Operational', 'Compliance', 'Financial', 'Strategic']
        case 'categories':
          return ['Operational', 'Compliance', 'IT Security', 'Financial', 'Strategic']
        case 'status':
          return ['Active', 'Inactive', 'On Hold']
        default:
          return []
      }
    }

    const getDataForYAxis = (yAxis) => {
      switch(yAxis) {
        case 'performance':
          return [85, 88, 92, 87, 90, 95, 89]
        case 'compliance':
          return [92, 95, 88, 90, 93, 96, 91]
        case 'risk':
          return [65, 70, 68, 72, 75, 80, 78]
        default:
          return []
      }
    }

    // Chart tab logic
    const chartTypes = [
      { type: 'line', icon: 'fas fa-chart-line', label: 'Line' },
      { type: 'bar', icon: 'fas fa-chart-bar', label: 'Bar' },
      { type: 'doughnut', icon: 'fas fa-dot-circle', label: 'Donut' },
    ];
    const activeChart = ref('line');
    
    // Line Chart Data
    const lineChartData = reactive({
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      datasets: [{
        label: 'Risk Performance',
        data: [42, 38, 35, 40, 56, 75, 82],
        fill: false,
        borderColor: '#4f6cff',
        tension: 0.4,
        pointBackgroundColor: '#4f6cff',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    })
    
    // Line Chart Options
    const lineChartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            display: true,
            color: 'rgba(0,0,0,0.05)'
          },
          ticks: {
            font: { size: 10 },
            padding: 5
          }
        },
        x: {
          grid: {
            display: false
          },
          ticks: {
            font: { size: 10 },
            padding: 5
          }
        }
      },
      animation: {
        duration: 1000,
        easing: 'easeOutQuart'
      },
      layout: {
        padding: 0
      }
    }
    
    // Donut Chart Data
    const donutChartData = reactive({
      labels: ['Active', 'Inactive', 'On Hold'],
          datasets: [{
        data: [60, 25, 15],
        backgroundColor: ['#4ade80', '#f87171', '#fbbf24'],
        borderWidth: 0,
        hoverOffset: 5
      }]
    })
    
    // Add computed property for category percentages
    const categoryPercentages = computed(() => {
      const total = categoryDistributionData.datasets[0].data.reduce((sum, value) => sum + value, 0);
      return categoryDistributionData.datasets[0].data.map(value => 
        total > 0 ? Math.round((value / total) * 100) : 0
      );
    });

    // Update Donut Chart Options
    const donutChartOptions = {
      cutout: '65%',
      onClick: (event, elements) => {
        console.log('Chart clicked, elements:', elements);
        if (elements.length > 0) {
          const element = elements[0];
          const categoryIndex = element.index;
          const category = categoryDistributionData.labels[categoryIndex];
          
          console.log('Category index:', categoryIndex, 'Category:', category);
          
          if (category) {
            selectedCategory.value = category;
            showCategoryPopup.value = true;
            fetchRisksByCategory(category);
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              const label = categoryDistributionData.labels[context.dataIndex];
              const value = categoryDistributionData.datasets[0].data[context.dataIndex];
              const percentage = categoryPercentages.value[context.dataIndex];
              return `${label}: ${value} (${percentage}%)`;
            }
          }
        },
        percentageLabels: {
          id: 'percentageLabels',
          afterDraw: (chart) => {
            const ctx = chart.ctx;
            const total = chart.data.datasets[0].data.reduce((sum, value) => sum + value, 0);
            
            chart.data.datasets[0].data.forEach((value, i) => {
              if (value > 0) { // Only draw labels for non-zero values
                const percentage = Math.round((value / total) * 100);
                
                // Get the center point and radius
                const centerX = chart.getDatasetMeta(0).data[i].x;
                const centerY = chart.getDatasetMeta(0).data[i].y;
                const radius = chart.getDatasetMeta(0).data[i].outerRadius;
                
                // Calculate angle for text placement
                const startAngle = chart.getDatasetMeta(0).data[i].startAngle;
                const endAngle = chart.getDatasetMeta(0).data[i].endAngle;
                const angle = startAngle + (endAngle - startAngle) / 2;
                
                // Position the text slightly outside the middle of the arc
                const offsetRadius = radius * 0.7; // Adjust this value to move label in/out
                const x = centerX + Math.cos(angle) * offsetRadius;
                const y = centerY + Math.sin(angle) * offsetRadius;
                
                // Draw percentage text
                ctx.save();
                ctx.translate(x, y);
                ctx.rotate(angle + Math.PI / 2); // Rotate text to align with segment
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = '#ffffff'; // White text
                ctx.font = '12px Arial';
                ctx.fillText(`${percentage}%`, 0, 0);
                ctx.restore();
              }
            });
          }
        }
      },
      maintainAspectRatio: false,
      animation: {
        animateRotate: true,
        animateScale: true,
        duration: 800,
        easing: 'easeOutCubic'
      },
      layout: {
        padding: 0
      }
    };
    
    // Bar Chart Data
    const barChartData = reactive({
      labels: ['Operational', 'Compliance'],
      datasets: [
        {
          label: 'Active',
          data: [8, 5],
          backgroundColor: '#4ade80',
          stack: 'Stack 0',
          borderRadius: 4
        },
        {
          label: 'Inactive',
          data: [6, 7],
          backgroundColor: '#f87171',
          stack: 'Stack 0',
          borderRadius: 4
        },
        {
          label: 'On Hold',
          data: [3, 0],
          backgroundColor: '#fbbf24',
          stack: 'Stack 0',
          borderRadius: 4
        }
      ]
    })
    
    // Bar Chart Options
    const barChartOptions = {
      plugins: { legend: { display: false } },
          responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { 
          stacked: true, 
          grid: { display: false },
          ticks: { color: '#222', font: { size: 9 }, padding: 5 }
        },
        y: { 
          stacked: true, 
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { color: '#222', font: { size: 9 }, padding: 5 }
        }
      },
      animation: {
        duration: 800,
        easing: 'easeInOutQuart'
      },
      layout: {
        padding: 0
      }
    }

    const toggleRiskDetails = () => {
      showRiskDetails.value = !showRiskDetails.value
    }

    const metrics = reactive({
      total: 0,
      accepted: 0,
      rejected: 0,
      mitigated: 0,
      inProgress: 0
    })
    
    // Update fetchRiskMetrics function to be called on filter change
    const fetchRiskMetrics = async () => {
      try {
        console.log('Fetching risk metrics with filters:', filters)
        const params = new URLSearchParams({
          framework_id: filters.framework,
          policy_id: filters.policy,
          timeRange: filters.timeRange,
          category: filters.category,
          priority: filters.priority
        })
        const response = await axios.get(`/api/risk/dashboard-with-filters/?${params}`)
        console.log('Received metrics data:', response.data)
        
        if (response.data && response.data.success && response.data.data) {
          const summary = response.data.data.summary
        
          // Update metrics (cards will show "No data found" if values are 0)
          metrics.total = summary.total_count
          metrics.accepted = summary.accepted_count
          metrics.rejected = summary.rejected_count
          metrics.mitigated = summary.mitigated_count
          metrics.inProgress = summary.in_progress_count
        
        // Update category distribution from the same response
        if (response.data.data.category_distribution) {
          categoryDistributionData.labels = response.data.data.category_distribution.map(cat => cat.Category)
          categoryDistributionData.datasets[0].data = response.data.data.category_distribution.map(cat => cat.count)
          categoryDistributionData.datasets[0].backgroundColor = generateChartColors(response.data.data.category_distribution.length)
          categoryChartKey.value += 1
        }
        
        // Update status distribution
        if (response.data.data.status_distribution) {
          // Update any status-based charts here
          console.log('Status distribution updated:', response.data.data.status_distribution)
        }
        
        // Update priority distribution
        if (response.data.data.priority_distribution) {
          // Update any priority-based charts here
          console.log('Priority distribution updated:', response.data.data.priority_distribution)
        }
        }
      } catch (error) {
        console.error('Error fetching risk metrics:', error)
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        // Set default values if API fails (cards will show "No data found")
        Object.assign(metrics, { 
          total: 0, 
          accepted: 0, 
          rejected: 0, 
          mitigated: 0, 
          inProgress: 0 
        })
        categoryDistributionData.labels = []
        categoryDistributionData.datasets[0].data = []
        categoryDistributionData.datasets[0].backgroundColor = []
        categoryChartKey.value += 1
      }
    }

    // Reactive data for filters
    const filters = reactive({
      framework: 'all',
      policy: 'all',
      timeRange: 'all',
      category: 'all',
      priority: 'all'
    })

    // Time range options
    const timeRangeOptions = ref([
      { value: 'all', label: 'All Time' },
      { value: '30days', label: 'Last 30 Days' },
      { value: '90days', label: 'Last 90 Days' },
      { value: '6months', label: 'Last 6 Months' },
      { value: '1year', label: 'Last 1 Year' }
    ])

    // Framework and policy data
    const frameworks = ref([])
    const policies = ref([])
    const loadingFrameworks = ref(false)
    const loadingPolicies = ref(false)

    // Update the categoryOptions ref to be empty initially
    const categoryOptions = ref([
      { value: 'all', label: 'All Categories' }
    ])

    // Y-axis options for the dynamic chart
    const yAxisOptions = ref([
      { value: 'count', label: 'Risk Count' },
      { value: 'exposure', label: 'Risk Exposure Rating' },
      { value: 'impact', label: 'Risk Impact' },
      { value: 'likelihood', label: 'Risk Likelihood' }
    ])

    // Fetch frameworks for dropdown
    const fetchFrameworks = async () => {
      try {
        loadingFrameworks.value = true
        const response = await axios.get('/api/risk/frameworks-for-filter/')
        
        if (response.data && response.data.success && response.data.data) {
          frameworks.value = response.data.data
          return true
        } else {
          console.error('Invalid framework response format:', response.data)
          frameworks.value = []
          return false
        }
      } catch (error) {
        console.error('Error fetching frameworks:', error)
        AccessUtils.handleApiError(error, 'view frameworks')
        frameworks.value = []
        return false
      } finally {
        loadingFrameworks.value = false
      }
    }

    // Check for selected framework from session and set it as default
    const checkSelectedFrameworkFromSession = async () => {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in RiskDashboard...')
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
        console.log('📊 DEBUG: Selected framework response:', response.data)
        
        if (response.data && response.data.success) {
          // Check if a framework is selected (not null)
          if (response.data.frameworkId) {
            const sessionFrameworkId = response.data.frameworkId
            console.log('✅ DEBUG: Found selected framework in session:', sessionFrameworkId)
            
            // Check if this framework exists in our loaded frameworks
            const frameworkExists = frameworks.value.find(f => f.FrameworkId == sessionFrameworkId)
            
            if (frameworkExists) {
              filters.framework = sessionFrameworkId
              console.log('✅ DEBUG: Set framework filter from session:', frameworkExists.FrameworkName)
              console.log('🔍 DEBUG: Framework ID being used:', sessionFrameworkId)
              console.log('🔍 DEBUG: Framework object:', frameworkExists)
              
              // Fetch policies for this framework and update all data
              await fetchPolicies(sessionFrameworkId)
              await fetchRiskMetrics()
              await fetchRiskTrendData()
              await fetchCategoryDistribution()
              await fetchCustomAnalysisData()
              await fetchHeatmapData()
            } else {
              console.log('⚠️ DEBUG: Framework from session not found in available frameworks')
              console.log('🔍 DEBUG: Session framework ID:', sessionFrameworkId)
              console.log('🔍 DEBUG: Available frameworks:', frameworks.value.map(f => ({ FrameworkId: f.FrameworkId, FrameworkName: f.FrameworkName })))
              
              // Framework not found, default to "All Frameworks" and fetch data
              filters.framework = 'all'
              console.log('🔄 DEBUG: Defaulting to All Frameworks and fetching data...')
              await fetchPolicies()
              await fetchRiskMetrics()
              await fetchRiskTrendData()
              await fetchCategoryDistribution()
              await fetchCustomAnalysisData()
              await fetchHeatmapData()
              fetchCategoryOptions()
            }
          } else {
            // "All Frameworks" is selected (frameworkId is null)
            console.log('ℹ️ DEBUG: No framework selected in session (All Frameworks selected)')
            console.log('🌐 DEBUG: Setting framework filter to "all"')
            filters.framework = 'all'
            
            // Fetch all data for "All Frameworks" view
            console.log('🔄 DEBUG: Fetching data for All Frameworks...')
            await fetchPolicies()
            await fetchRiskMetrics()
            await fetchRiskTrendData()
            await fetchCategoryDistribution()
            await fetchCustomAnalysisData()
            await fetchHeatmapData()
            fetchCategoryOptions()
          }
        } else {
          console.log('ℹ️ DEBUG: No framework found in session')
          filters.framework = 'all'
          
          // Fetch all data for "All Frameworks" view
          console.log('🔄 DEBUG: Fetching data for All Frameworks (no session)...')
          await fetchPolicies()
          await fetchRiskMetrics()
          await fetchRiskTrendData()
          await fetchCategoryDistribution()
          await fetchCustomAnalysisData()
          await fetchHeatmapData()
          fetchCategoryOptions()
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework from session:', error)
        // Default to 'all' on error
        filters.framework = 'all'
        
        // Fetch all data even on error (default to All Frameworks)
        console.log('🔄 DEBUG: Fetching data for All Frameworks (after error)...')
        await fetchPolicies()
        await fetchRiskMetrics()
        await fetchRiskTrendData()
        await fetchCategoryDistribution()
        await fetchCustomAnalysisData()
        await fetchHeatmapData()
        fetchCategoryOptions()
      }
    }

    // Fetch policies for dropdown
    const fetchPolicies = async (frameworkId = null) => {
      try {
        loadingPolicies.value = true
        
        let response
        if (frameworkId && frameworkId !== 'all') {
          response = await axios.get(`/api/risk/policies-for-filter/?framework_id=${frameworkId}`)
        } else {
          response = await axios.get('/api/risk/policies-for-filter/')
        }
        
        if (response.data && response.data.success && response.data.data) {
          policies.value = response.data.data
          return true
        } else {
          console.error('Invalid policy response format:', response.data)
          policies.value = []
          return false
        }
      } catch (error) {
        console.error('Error fetching policies:', error)
        AccessUtils.handleApiError(error, 'view policies')
        policies.value = []
        return false
      } finally {
        loadingPolicies.value = false
      }
    }

    // Handle framework selection
    const onFrameworkChange = async () => {
      console.log('🔍 DEBUG: Framework changed to:', filters.framework)
      console.log('🔍 DEBUG: Available frameworks:', frameworks.value.map(f => ({ FrameworkId: f.FrameworkId, FrameworkName: f.FrameworkName })))
      
      // Find the framework name from the frameworks list
      const frameworkName = frameworks.value.find(f => f.FrameworkId === filters.framework)?.FrameworkName || 'All Frameworks'
      
      // Update Vuex store (this will also save to backend session)
      await store.dispatch('framework/setFramework', {
        id: filters.framework !== 'all' ? filters.framework : 'all',
        name: frameworkName
      })
      
      console.log('✅ DEBUG: Framework saved to Vuex store in RiskDashboard:', filters.framework)
      
      filters.policy = 'all'
      policies.value = []
      
      if (filters.framework && filters.framework !== 'all') {
        fetchPolicies(filters.framework)
      } else {
        fetchPolicies()
      }
      
      console.log('🔄 DEBUG: Updating all data with framework:', filters.framework)
      // Update all data when framework changes
      fetchRiskMetrics()
      fetchRiskTrendData()
      fetchCategoryDistribution()
      fetchCustomAnalysisData()
      fetchHeatmapData()
    }

    // Handle policy selection
    const onPolicyChange = () => {
      console.log('Policy changed to:', filters.policy)
      // Update all data when policy changes
      fetchRiskMetrics()
      fetchRiskTrendData()
      fetchCategoryDistribution()
      fetchCustomAnalysisData()
      fetchHeatmapData()
    }

    // Add function to fetch category options for dropdown
    const fetchCategoryOptions = async () => {
      try {
        console.log('Fetching category options for dropdown...')
        const response = await axios.get(API_ENDPOINTS.RISK_CATEGORIES_DROPDOWN)
        
        if (response.data && response.data.status === 'success' && response.data.data) {
          // Keep the "All Categories" option and add the fetched categories
          categoryOptions.value = [
            { value: 'all', label: 'All Categories' },
            ...response.data.data.map(category => ({
              value: category.id,
              label: category.value
            }))
          ]
          console.log('Fetched category options:', categoryOptions.value)
        }
      } catch (error) {
        console.error('Error fetching category options:', error)
        
        // Check if it's an access denied error
        AccessUtils.handleApiError(error, 'view risk categories')
      }
    }

    // Fetch category distribution data
    // NOTE: To keep charts in sync with the metric cards, we now derive
    // categoryDistributionData from the same dashboard endpoint used by
    // fetchRiskMetrics(). This ensures the donut chart always reflects the
    // exact same filters (framework, policy, timeRange, category, priority)
    // and counts as the summary cards.
    const fetchCategoryDistribution = async () => {
      console.log('🔄 Fetching category distribution via fetchRiskMetrics to keep cards and chart in sync')
      await fetchRiskMetrics()
    }

    // Fetch on mount and when filters change
    onMounted(async () => {
      // Load framework from Vuex store
      const storeFrameworkId = store.state.framework.selectedFrameworkId
      if (storeFrameworkId && storeFrameworkId !== 'all') {
        filters.framework = storeFrameworkId
        console.log('🔄 RiskDashboard: Loaded framework from Vuex store:', storeFrameworkId)
      }
      
      // Fetch frameworks first
      const frameworksLoaded = await fetchFrameworks()
      
      if (frameworksLoaded) {
        // Check for selected framework from session and set it
        await checkSelectedFrameworkFromSession()
        } else {
          // Still try to fetch policies even if frameworks fail
        await fetchPolicies()
      // Fetch other data
      fetchRiskTrendData();
      fetchCategoryDistribution();
      fetchRiskMetrics();
      fetchCustomAnalysisData();
      fetchCategoryOptions();
      }
    })

    // Watch filters and update chart
    watch([
      () => filters.timeRange,
      () => filters.category,
      () => filters.priority
    ], fetchCategoryDistribution)

    // Risk Trend Chart Configuration
    const riskTrendData = reactive({
      labels: [],
      datasets: [
        {
          label: 'Risk Count',
          data: [],
          borderColor: '#f87171',
          backgroundColor: 'rgba(248, 113, 113, 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 4,
          pointHoverRadius: 6
        }
      ]
    })

    const riskTrendOptions = {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.1)'
          },
          ticks: {
            stepSize: 1
          }
        },
        x: {
          grid: {
            display: false
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          titleColor: '#000',
          bodyColor: '#666',
          borderColor: '#ddd',
          borderWidth: 1
        }
      },
      interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false
      }
    }

    // Fetch risk trend data
    const fetchRiskTrendData = async () => {
      try {
        console.log('Fetching risk trend data with filters:', filters);
        
        // Add query parameters for all filters
        const params = new URLSearchParams({
          framework_id: filters.framework,
          policy_id: filters.policy,
          timeRange: filters.timeRange,
          category: filters.category,
          priority: filters.priority
        });
        
        const response = await axios.get(`/api/risk/trend-over-time/?${params}`);
        console.log('Risk trend API response:', response.data);
        
        // Check if we have valid data
        if (response.data) {
          // Handle different response formats
          if (response.data.months && Array.isArray(response.data.months)) {
            riskTrendData.labels = response.data.months;
            
            // Check which data format we received
            if (response.data.trendData && Array.isArray(response.data.trendData)) {
              // Direct trend data array
              riskTrendData.datasets[0].data = response.data.trendData;
              console.log('Using trendData array:', response.data.trendData);
            } 
            else if (response.data.newRisks && response.data.newRisks.data) {
              // Object with newRisks.data array
              riskTrendData.datasets[0].data = response.data.newRisks.data;
              console.log('Using newRisks.data array:', response.data.newRisks.data);
            }
            else {
              console.warn('No valid trend data found in response');
              riskTrendData.datasets[0].data = [];
            }
          } else {
            console.warn('No valid months array found in response');
            riskTrendData.labels = [];
            riskTrendData.datasets[0].data = [];
          }
        }
      } catch (error) {
        console.error('Error fetching risk trend data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        // Clear data on error
        riskTrendData.labels = [];
        riskTrendData.datasets[0].data = [];
      }
    };

    // Watch for filter changes
    watch([() => filters.timeRange, () => filters.category, () => filters.framework, () => filters.policy], () => {
      console.log('\n=== Filter Change Detected ===')
      console.log('New filter values:', {
        timeRange: filters.timeRange,
        category: filters.category,
        framework: filters.framework,
        policy: filters.policy
      })
      // Update all data when filters change
      fetchRiskMetrics();
      fetchRiskTrendData();
      fetchCategoryDistribution();
      fetchCustomAnalysisData();
      fetchSpecializedChartData();
      fetchMitigationCostData();
      fetchHeatmapData();
    })

    // Helper functions for insights
    const highestCategory = computed(() => {
      const data = categoryDistributionData.datasets[0].data;
      const labels = categoryDistributionData.labels;
      if (!data.length) return { name: '', percent: 0 };
      const max = Math.max(...data);
      const idx = data.indexOf(max);
      const total = data.reduce((a, b) => a + b, 0);
      const percent = total > 0 ? Math.round((max / total) * 100) : 0;
      return { name: labels[idx] || '', percent };
    })
    
    const getTrendText = () => {
      const newRisks = riskTrendData.datasets[0]?.data || [];
      if (!newRisks.length) return 'No data';
      
      const lastIndex = newRisks.length - 1;
      const previousIndex = lastIndex > 0 ? lastIndex - 1 : 0;
      
      if (newRisks[lastIndex] > newRisks[previousIndex]) {
        return 'Increasing ↑';
      } else if (newRisks[lastIndex] < newRisks[previousIndex]) {
        return 'Decreasing ↓';
      }
      return 'Stable →';
    }
    
    const getTrendClass = () => {
      if (!riskTrendData.datasets[0]?.data?.length) return '';
      
      const trend = getTrendText();
      if (trend.includes('Increasing')) return 'positive';
      if (trend.includes('Decreasing')) return 'negative';
      return '';
    }

    // Fetch data for specialized charts (trend and other metrics)
    // NOTE: We no longer modify categoryDistributionData here because that
    // conflicts with the main dashboard metrics and caused the donut chart
    // to look the same across frameworks. Category distribution is now
    // driven exclusively by fetchRiskMetrics() so it always matches the
    // summary cards.
    const fetchSpecializedChartData = async () => {
      try {
        const params = new URLSearchParams({
          framework_id: filters.framework,
          policy_id: filters.policy,
          timeRange: filters.timeRange,
          category: filters.category,
          priority: filters.priority
        });
        
        // Fetch risk trend data
        const trendRes = await axios.get(`/api/risk/identification-rate/?${params}`);
        if (trendRes.data && trendRes.data.months && trendRes.data.trendData) {
          riskTrendData.labels = trendRes.data.months;
          riskTrendData.datasets[0].data = trendRes.data.trendData;
          
          // For mitigated, use a formula based on identification rate
          const mitigationRes = await axios.get(`/api/risk/mitigation-completion-rate/?${params}`);
          if (mitigationRes.data && mitigationRes.data.trendData) {
            riskTrendData.datasets[0].data = mitigationRes.data.trendData;
          }
        }
        
      } catch (error) {
        console.error('Error fetching specialized chart data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
      }
    };
    
    // Call this initially and when filters change
    fetchSpecializedChartData();
    
    // Update when filters change
    watch([() => filters.timeRange, () => filters.category, () => filters.priority], 
      () => {
        fetchSpecializedChartData();
      }
    );

    const getChartIcon = (chartType) => {
      switch(chartType) {
        case 'line': return 'fas fa-chart-line';
        case 'bar': return 'fas fa-chart-bar';
        case 'doughnut': return 'fas fa-chart-pie';
        default: return 'fas fa-chart-line';
      }
    };

    const mitigationCostData = ref(null);

    const fetchMitigationCostData = async () => {
      try {
        const timeRange = filters.timeRange || '30days';
        console.log(`Fetching mitigation cost data with period: ${timeRange}`);
        
        const baseUrl = window.location.hostname === 'localhost' 
          ? 'http://localhost:8000' 
          : '';
        
        // Include all filters
        const params = new URLSearchParams({
          framework_id: filters.framework,
          policy_id: filters.policy,
          timeRange: timeRange,
          category: filters.category || 'all',
          priority: filters.priority || 'all'
        });
        
        const response = await axios.get(`${baseUrl}/api/risk/mitigation-cost/?${params}`);
        
        if (response.status === 200) {
          console.log("Raw mitigation cost API response:", response.data);
          mitigationCostData.value = response.data;
          
          // Update any charts that use this data
          updateMitigationCostCharts();
        } else {
          console.error('Failed to fetch mitigation cost data:', response.status);
        }
      } catch (error) {
        console.error('Error fetching mitigation cost data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
      }
    };

    const updateMitigationCostCharts = () => {
      // Update any charts that use mitigation cost data
      if (activeChart.value === 'bar' && selectedYAxis.value === 'mitigationCost') {
        barChartData.labels = mitigationCostData.value.monthlyData.map(item => item.month);
        barChartData.datasets[0].data = mitigationCostData.value.monthlyData.map(item => item.cost);
      }
    };

    // Make sure we fetch mitigation cost data when filters change
    watch(
      [
        () => filters.timeRange,
        () => filters.category, 
        () => filters.priority
      ], 
      () => {
        console.log("Filters changed, updating data");
        fetchMitigationCostData();
        fetchSpecializedChartData();
      }
    );

    // Custom options for the dynamic chart
    const customChartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            display: true,
            color: 'rgba(0,0,0,0.05)'
          },
          ticks: {
            font: { size: 10 },
            padding: 5
          }
        },
        x: {
          grid: {
            display: false
          },
          ticks: {
            font: { size: 10 },
            padding: 5
          }
        }
      },
      animation: {
        duration: 800,
        easing: 'easeOutQuart'
      },
      layout: {
        padding: {
          top: 30,
          right: 8,
          bottom: 8,
          left: 8
        }
      }
    }
    
    // Custom options for donut chart in dynamic chart
    const customDonutOptions = {
      cutout: '65%',
      plugins: {
        legend: { display: false }
      },
      maintainAspectRatio: false,
      animation: {
        animateRotate: true,
        animateScale: true,
        duration: 800,
        easing: 'easeOutCubic'
      },
      layout: {
        padding: {
          top: 30,
          right: 0,
          bottom: 0,
          left: 0
        }
      }
    }

    const heatmapCanvas = ref(null)
    const heatmapChart = ref(null)
    const heatmapData = ref([])

    const fetchHeatmapData = async () => {
      try {
        console.log('Fetching heatmap data with filters:', filters)
        const params = new URLSearchParams({
          framework_id: filters.framework,
          policy_id: filters.policy,
          timeRange: filters.timeRange,
          category: filters.category,
          priority: filters.priority
        })
        const response = await axios.get(`${API_ENDPOINTS.RISK_HEATMAP}?${params}`)
        console.log('Received heatmap data:', response.data)
        heatmapData.value = response.data.heatmap_data
        console.log('Total risks:', response.data.total_risks)
      } catch (error) {
        console.error('Error fetching heatmap data:', error)
      }
    }

    const getColor = (value) => {
      // Use RdYlGn_r color scheme (red for high values, yellow for medium, green for low)
      if (value === 0) return 'rgba(0, 104, 55, 0.7)'      // Dark green
      if (value === 1) return 'rgba(26, 152, 80, 0.7)'     // Green
      if (value === 2) return 'rgba(145, 207, 96, 0.7)'    // Light green
      if (value === 3) return 'rgba(217, 239, 139, 0.7)'   // Yellow-green
      if (value === 4) return 'rgba(254, 224, 139, 0.7)'   // Light yellow
      return 'rgba(215, 48, 39, 0.7)'                      // Red for highest values
    }

    const initializeHeatmap = () => {
      if (!heatmapCanvas.value) {
        console.error('Canvas element not found')
        return
      }

      // Get the canvas context
      const ctx = heatmapCanvas.value.getContext('2d')
      if (!ctx) {
        console.error('Could not get canvas context')
        return
      }
      
      // Destroy existing chart if it exists
      if (heatmapChart.value) {
        heatmapChart.value.destroy()
        heatmapChart.value = null
      }

      // Wait for next tick to ensure DOM is updated
      nextTick(() => {
        // Transform the data for scatter plot
        const datasets = []
        const uniqueValues = new Set()
        
        if (!heatmapData.value || !Array.isArray(heatmapData.value)) {
          console.error('Invalid heatmap data:', heatmapData.value)
          return
        }
        
        heatmapData.value.forEach((row) => {
          row.forEach((value) => {
            if (value > 0) {
              uniqueValues.add(value)
            }
          })
        })
        
        console.log('Unique values found:', Array.from(uniqueValues))

        // Create datasets for each unique value
        Array.from(uniqueValues).sort((a, b) => a - b).forEach(value => {
          datasets.push({
            label: `Count: ${value}`,
            data: [],
            backgroundColor: getColor(value),
            pointStyle: 'square',
            pointRadius: 15,
            pointHoverRadius: 18
          })
        })

        // Populate datasets
        if (heatmapData.value && Array.isArray(heatmapData.value)) {
          heatmapData.value.forEach((row, rowIndex) => {
            if (row && Array.isArray(row)) {
              row.forEach((value, colIndex) => {
                if (value > 0) {
                  const datasetIndex = Array.from(uniqueValues).sort((a, b) => a - b).indexOf(value)
                  if (datasetIndex >= 0 && datasets[datasetIndex]) {
                    datasets[datasetIndex].data.push({
                      x: colIndex + 1,
                      y: 10 - rowIndex
                    })
                  }
                }
              })
            }
          })
        }

        console.log('Prepared datasets:', datasets)
        console.log('Chart data structure:', {
          datasets: datasets,
          totalDatasets: datasets.length,
          totalPoints: datasets.reduce((sum, ds) => sum + ds.data.length, 0)
        })
        
        // Debug: Log each dataset and its points
        datasets.forEach((dataset, index) => {
          console.log(`Dataset ${index}:`, {
            label: dataset.label,
            dataPoints: dataset.data.length,
            samplePoints: dataset.data.slice(0, 3)
          })
        })

        // Configure and create the chart
        try {
          heatmapChart.value = new Chart(ctx, {
            type: 'scatter',
            data: {
              datasets: datasets
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              interaction: {
                mode: 'point',
                intersect: true
              },
              onClick: (event, elements) => {
                console.log('Chart clicked - elements:', elements);
                console.log('Event:', event);
                console.log('Canvas position:', event.native);
                
                if (elements.length > 0) {
                  const element = elements[0];
                  console.log('Element:', element);
                  console.log('Element raw:', element.raw);
                  console.log('Element dataset index:', element.datasetIndex);
                  console.log('Element index:', element.index);
                  
                  // Check if element.raw exists and has valid coordinates
                  if (element.raw && typeof element.raw.x !== 'undefined' && typeof element.raw.y !== 'undefined') {
                    const impact = 11 - Math.round(element.raw.y);
                    const likelihood = Math.round(element.raw.x);
                    
                    console.log('Calculated coordinates - Impact:', impact, 'Likelihood:', likelihood);
                    
                    // Validate coordinates are within valid range
                    if (impact >= 1 && impact <= 10 && likelihood >= 1 && likelihood <= 10) {
                      console.log('Valid coordinates - Impact:', impact, 'Likelihood:', likelihood);
                      
                      selectedHeatmapCoordinates.value = { impact, likelihood };
                      showHeatmapPopup.value = true;
                      fetchRisksByHeatmapCoordinates(impact, likelihood);
                    } else {
                      console.log('Invalid coordinates - Impact:', impact, 'Likelihood:', likelihood);
                    }
                  } else {
                    console.log('No valid data point clicked - element.raw is invalid');
                    console.log('Element raw type:', typeof element.raw);
                    console.log('Element raw value:', element.raw);
                    
                    // Try alternative approach - get coordinates from event
                    const rect = event.native.target.getBoundingClientRect();
                    const x = event.native.clientX - rect.left;
                    const y = event.native.clientY - rect.top;
                    console.log('Mouse coordinates:', { x, y });
                    
                    // Convert to chart coordinates
                    const chart = heatmapChart.value;
                    if (chart) {
                      const chartArea = chart.chartArea;
                      const xScale = chart.scales.x;
                      const yScale = chart.scales.y;
                      
                      if (chartArea && xScale && yScale) {
                        const chartX = xScale.getValueForPixel(x);
                        const chartY = yScale.getValueForPixel(y);
                        console.log('Chart coordinates from mouse:', { chartX, chartY });
                        
                        const impact = 11 - Math.round(chartY);
                        const likelihood = Math.round(chartX);
                        
                        if (impact >= 1 && impact <= 10 && likelihood >= 1 && likelihood <= 10) {
                          console.log('Valid coordinates from mouse - Impact:', impact, 'Likelihood:', likelihood);
                          selectedHeatmapCoordinates.value = { impact, likelihood };
                          showHeatmapPopup.value = true;
                          fetchRisksByHeatmapCoordinates(impact, likelihood);
                        }
                      }
                    }
                  }
                } else {
                  console.log('No elements found in click event');
                }
              },
              plugins: {
                legend: {
                  display: true,
                  position: 'bottom',
                  align: 'center',
                  labels: {
                    usePointStyle: true,
                    pointStyle: 'square',
                    boxWidth: 12,
                    boxHeight: 12,
                    padding: 15,
                    font: {
                      size: 12
                    }
                  }
                },
                tooltip: {
                  callbacks: {
                    label: (context) => {
                      return `Impact: ${11 - context.raw.y}, Likelihood: ${context.raw.x}, ${context.dataset.label}`
                    }
                  }
                }
              },
              scales: {
                x: {
                  type: 'linear',
                  position: 'bottom',
                  min: 0.5,
                  max: 10.5,
                  title: {
                    display: true,
                    text: 'Likelihood',
                    font: {
                      weight: 'bold'
                    }
                  },
                  ticks: {
                    stepSize: 1
                  },
                  grid: {
                    display: true,
                    color: '#ddd'
                  }
                },
                y: {
                  type: 'linear',
                  min: 0.5,
                  max: 10.5,
                  title: {
                    display: true,
                    text: 'Impact',
                    font: {
                      weight: 'bold'
                    }
                  },
                  ticks: {
                    stepSize: 1,
                    callback: (value) => 11 - Math.round(value)
                  },
                  grid: {
                    display: true,
                    color: '#ddd'
                  }
                }
              }
            }
          })
        } catch (error) {
          console.error('Error creating chart:', error)
        }
      })
    }

    onMounted(async () => {
      console.log('Component mounted')
      await fetchHeatmapData()
      initializeHeatmap()
    })

    // Ensure framework filter reflects latest session when returning to this view
    onActivated(async () => {
      try {
        await checkSelectedFrameworkFromSession()
        if (filters.framework && filters.framework !== 'all') {
          await fetchPolicies(filters.framework)
        } else {
          await fetchPolicies()
        }
        fetchRiskMetrics()
        fetchRiskTrendData()
        fetchCategoryDistribution()
        fetchCustomAnalysisData()
        fetchHeatmapData()
      } catch (e) {
        console.error('Error refreshing framework context on activation:', e)
      }
    })

    // Watch for changes in heatmap data
    watch(heatmapData, () => {
      console.log('Heatmap data changed, reinitializing chart')
      initializeHeatmap()
    })

    // Watch for filter changes to update heatmap
    watch([
      () => filters.framework,
      () => filters.policy,
      () => filters.timeRange,
      () => filters.category,
      () => filters.priority
    ], () => {
      console.log('Filters changed, updating heatmap data')
      fetchHeatmapData()
    })

    // Dynamic colors for chart based on number of categories
    const generateChartColors = (count) => {
      const baseColors = [
        '#4ade80', '#f87171', '#fbbf24', '#60a5fa', '#818cf8',
        '#f472b6', '#a78bfa', '#34d399', '#fbbf24', '#fb7185',
        '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'
      ]
      
      // If we have more categories than base colors, cycle through them
      const colors = []
      for (let i = 0; i < count; i++) {
        colors.push(baseColors[i % baseColors.length])
      }
      return colors
    }

    // Category Distribution Chart (dynamic, from backend)
    const categoryDistributionData = reactive({
      labels: [],
      datasets: [{
        data: [],
        backgroundColor: [],
        borderWidth: 0,
        hoverOffset: 5
      }]
    })

    const isLoadingCustomChart = ref(false);
    const hasCustomChartData = ref(false);
    const isApplyingFilters = ref(false);
    const isExporting = ref(false);

    const fetchCustomAnalysisData = async () => {
      try {
        isLoadingCustomChart.value = true;
        hasCustomChartData.value = false;

        console.log('Fetching custom analysis data...');
        console.log(`Parameters: x_axis=${selectedXAxis.value}, y_axis=${selectedYAxis.value}`);

        const requestData = {
          xAxis: selectedXAxis.value,
          yAxis: selectedYAxis.value,
          frameworkId: filters.framework,
          policyId: filters.policy,
          timeRange: filters.timeRange,
          category: filters.category,
          priority: filters.priority
        };

        const response = await axios.post('/api/risk/analytics-with-filters/', requestData);
        console.log('Received custom analysis data:', response.data);

        if (response.data && response.data.success && response.data.chartData) {
          const chartData = response.data.chartData;
          
          // Update all chart types with the same data
          const labels = chartData.labels;
          const datasets = chartData.datasets;
          
          // Update line chart
          lineChartData.labels = labels;
          lineChartData.datasets = datasets.map(ds => ({
            ...ds,
            fill: false,
            tension: 0.4,
            pointBackgroundColor: ds.backgroundColor,
            pointBorderColor: '#fff',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
          }));
          
          // Update bar chart
          barChartData.labels = labels;
          barChartData.datasets = datasets.map(ds => ({
            ...ds,
            barPercentage: 0.7,
            categoryPercentage: 0.8
          }));
          
          // Update donut chart - use only first dataset for donut
          donutChartData.labels = labels;
          if (datasets.length === 1) {
            donutChartData.datasets[0].data = datasets[0].data;
            donutChartData.datasets[0].backgroundColor = 
              datasets[0].data.map((_, i) => generateChartColors(datasets[0].data.length)[i]);
          } else {
            // For stacked datasets, combine them into one for donut chart
            const combinedData = [];
            for (let i = 0; i < labels.length; i++) {
              let sum = 0;
              for (const ds of datasets) {
                sum += ds.data[i] || 0;
              }
              combinedData.push(sum);
            }
            donutChartData.datasets[0].data = combinedData;
            donutChartData.datasets[0].backgroundColor = generateChartColors(labels.length);
          }
          
          hasCustomChartData.value = true;
        } else {
          console.warn('No valid custom analysis data found in response');
          hasCustomChartData.value = false;
        }
      } catch (error) {
        console.error('Error fetching custom analysis data:', error);
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        hasCustomChartData.value = false;
      } finally {
        isLoadingCustomChart.value = false;
      }
    };

    // Watch for filter changes to update custom chart
    watch([() => filters.timeRange, () => filters.category, () => filters.priority, () => filters.framework, () => filters.policy], () => {
      fetchCustomAnalysisData();
    })

    // Watch for chart type changes
    watch(activeChart, () => {
      nextTick(() => {
        console.log('Chart type changed to:', activeChart.value);
      });
    });

    // Add the computed property for filtered categories
    const filteredCategories = computed(() => {
      return categoryDistributionData.labels.map((label, index) => ({
        label,
        value: categoryDistributionData.datasets[0].data[index],
        color: categoryDistributionData.datasets[0].backgroundColor[index]
      })).filter(category => category.value > 0);
    });

    // Navigation function to go back to Risk Register
    const goBackToRiskRegister = () => {
      router.push('/risk/riskregister-list')
    }

    // Export dashboard as PDF
    const exportDashboardAsPDF = async () => {
      isExporting.value = true
      try {
        await nextTick() // Ensure all components are rendered
        
        const dashboardElement = document.querySelector('.risk-dashboard-container')
        if (!dashboardElement) {
          throw new Error('Dashboard element not found')
        }

        // Temporarily hide any popups
        const popups = dashboardElement.querySelectorAll('.risk-category-popup-overlay, .risk-heatmap-popup-overlay')
        popups.forEach(el => el.style.display = 'none')

        // Wait a bit to ensure all charts are fully rendered
        await new Promise(resolve => setTimeout(resolve, 500))

        // Capture the entire dashboard as it appears on the webpage
        const canvas = await html2canvas(dashboardElement, {
          scale: 2.5, // Higher quality for better chart visibility
          useCORS: true,
          allowTaint: true,
          logging: false,
          backgroundColor: '#ffffff', // White background for better visibility
          windowWidth: dashboardElement.scrollWidth,
          windowHeight: dashboardElement.scrollHeight,
          scrollY: -window.scrollY,
          scrollX: -window.scrollX,
          // Ensure canvas elements (charts) are captured
          onclone: (clonedDoc) => {
            const clonedDashboard = clonedDoc.querySelector('.risk-dashboard-container')
            if (clonedDashboard) {
              clonedDashboard.style.transform = 'none'
              clonedDashboard.style.position = 'relative'
              clonedDashboard.style.left = '0'
              clonedDashboard.style.top = '0'
              clonedDashboard.style.marginLeft = '0'
              clonedDashboard.style.maxWidth = '100%'
              clonedDashboard.style.background = '#ffffff'
            }
            
            // Force all canvas elements to be visible with better rendering
            const canvases = clonedDoc.querySelectorAll('canvas')
            canvases.forEach(canvas => {
              canvas.style.display = 'block'
              canvas.style.visibility = 'visible'
              canvas.style.opacity = '1'
              canvas.style.imageRendering = 'crisp-edges'
              // Ensure canvas has proper dimensions
              if (canvas.width === 0 || canvas.height === 0) {
                canvas.width = canvas.offsetWidth * 2.5
                canvas.height = canvas.offsetHeight * 2.5
              }
            })

            // Ensure chart containers are visible with proper dimensions
            const chartContainers = clonedDoc.querySelectorAll('.risk-chart-container, .risk-heatmap-container')
            chartContainers.forEach(container => {
              container.style.display = 'block'
              container.style.visibility = 'visible'
              container.style.opacity = '1'
              container.style.minHeight = '250px'
              container.style.background = '#ffffff'
            })

            // Ensure all chart cards are visible
            const chartCards = clonedDoc.querySelectorAll('.risk-chart-card')
            chartCards.forEach(card => {
              card.style.display = 'flex'
              card.style.visibility = 'visible'
              card.style.opacity = '1'
              card.style.background = '#ffffff'
            })

            // Hide popups in clone
            const clonedPopups = clonedDoc.querySelectorAll('.risk-category-popup-overlay, .risk-heatmap-popup-overlay')
            clonedPopups.forEach(el => el.style.display = 'none')
          }
        })

        // Restore popups
        popups.forEach(el => el.style.display = '')

        const imgData = canvas.toDataURL('image/png', 1.0)
        
        // Calculate PDF dimensions based on captured content
        const imgWidth = canvas.width
        const imgHeight = canvas.height
        
        // Create PDF with custom dimensions to fit the entire dashboard
        // Use landscape orientation and custom size to match dashboard width
        const pdfWidth = 297 // A4 width in mm (landscape)
        const pdfHeight = (imgHeight * pdfWidth) / imgWidth // Calculate proportional height
        
        const pdf = new jsPDF({
          orientation: pdfHeight > pdfWidth ? 'portrait' : 'landscape',
          unit: 'mm',
          format: [pdfWidth, pdfHeight]
        })

        // Add the entire dashboard as one image
        pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight, '', 'FAST')

        // Generate filename with timestamp
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
        const filename = `Risk-Dashboard-${timestamp}.pdf`

        // Download the PDF
        pdf.save(filename)

        console.log('PDF downloaded successfully')
        
        // Show success feedback
        const exportBtn = document.querySelector('.risk-action-btn.export')
        if (exportBtn) {
          exportBtn.classList.add('success')
          setTimeout(() => {
            exportBtn.classList.remove('success')
          }, 600)
        }
      } catch (error) {
        console.error('Error generating PDF:', error)
        alert('Failed to generate PDF. Please try again.')
      } finally {
        isExporting.value = false
      }
    }



    const fetchRisksByCategory = async (category) => {
      try {
        isLoadingCategoryRisks.value = true
        categoryRisks.value = []
        
        console.log('Fetching risks for category:', category)
        
        // Build URL with filters
        const params = new URLSearchParams({ category })
        if (filters.framework && filters.framework !== 'all') {
          params.append('framework_id', filters.framework)
        }
        if (filters.policy && filters.policy !== 'all') {
          params.append('policy_id', filters.policy)
        }
        
        const url = `${API_ENDPOINTS.RISK_BY_CATEGORY(category)}?${params}`
        console.log('API endpoint:', url)
        
        const response = await axios.get(url)
        
        console.log('Response received:', response.data)
        
        if (response.data && response.data.status === 'success') {
          categoryRisks.value = response.data.risks || []
          console.log('Risks loaded:', categoryRisks.value.length)
        } else {
          console.error('Error fetching risks by category:', response.data)
          categoryRisks.value = []
        }
      } catch (error) {
        console.error('Error fetching risks by category:', error)
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        categoryRisks.value = []
      } finally {
        isLoadingCategoryRisks.value = false
      }
    }

    const closeCategoryPopup = () => {
      showCategoryPopup.value = false
      selectedCategory.value = ''
      categoryRisks.value = []
    }

    const fetchRisksByHeatmapCoordinates = async (impact, likelihood) => {
      try {
        isLoadingHeatmapRisks.value = true
        heatmapRisks.value = []
        
        console.log('Fetching risks for heatmap coordinates - Impact:', impact, 'Likelihood:', likelihood)
        
        // Build URL with filters
        const params = new URLSearchParams()
        if (filters.framework && filters.framework !== 'all') {
          params.append('framework_id', filters.framework)
        }
        if (filters.policy && filters.policy !== 'all') {
          params.append('policy_id', filters.policy)
        }
        
        const url = params.toString() 
          ? `${API_ENDPOINTS.RISK_BY_HEATMAP_COORDINATES(impact, likelihood)}&${params}` 
          : API_ENDPOINTS.RISK_BY_HEATMAP_COORDINATES(impact, likelihood)
        console.log('API endpoint:', url)
        
        const response = await axios.get(url)
        
        console.log('Response received:', response.data)
        
        if (response.data && response.data.status === 'success') {
          heatmapRisks.value = response.data.risks || []
          console.log('Heatmap risks loaded:', heatmapRisks.value.length)
        } else {
          console.error('Error fetching risks by heatmap coordinates:', response.data)
          heatmapRisks.value = []
        }
      } catch (error) {
        console.error('Error fetching risks by heatmap coordinates:', error)
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        // Handle specific error cases
        if (error.response && error.response.status === 404) {
          console.log('No risks found for these coordinates')
          heatmapRisks.value = []
        } else if (error.response && error.response.status >= 500) {
          console.error('Server error occurred')
          heatmapRisks.value = []
        } else {
          console.error('Network or other error occurred')
          heatmapRisks.value = []
        }
      } finally {
        isLoadingHeatmapRisks.value = false
      }
    }

    const closeHeatmapPopup = () => {
      showHeatmapPopup.value = false
      selectedHeatmapCoordinates.value = { impact: 0, likelihood: 0 }
      heatmapRisks.value = []
    }

    const handleLegendClick = (category) => {
      console.log('Legend clicked for category:', category)
      selectedCategory.value = category
      showCategoryPopup.value = true
      fetchRisksByCategory(category)
    }

    const getPriorityClass = (priority) => {
      switch (priority?.toLowerCase()) {
        case 'critical': return 'priority-critical'
        case 'high': return 'priority-high'
        case 'medium': return 'priority-medium'
        case 'low': return 'priority-low'
        default: return 'priority-unknown'
      }
    }

    const getStatusClass = (status) => {
      switch (status?.toLowerCase()) {
        case 'active': return 'status-active'
        case 'mitigated': return 'status-mitigated'
        case 'accepted': return 'status-accepted'
        case 'rejected': return 'status-rejected'
        case 'in progress': return 'status-in-progress'
        default: return 'status-unknown'
      }
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      try {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        })
      } catch (error) {
        return 'Invalid Date'
      }
    }

    // Watch for filter changes and update all data
    watch([
      () => filters.timeRange,
      () => filters.category, 
      () => filters.priority,
      () => filters.framework,
      () => filters.policy
    ], () => {
      console.log("Filters changed, updating all data");
      // Update all charts and metrics when any filter changes
      fetchRiskMetrics();
      fetchRiskTrendData();
      fetchCategoryDistribution();
      fetchCustomAnalysisData();
      fetchSpecializedChartData();
      fetchMitigationCostData();
      fetchHeatmapData();
    });

    // Add a comprehensive filter change handler
    const handleFilterChange = async () => {
      console.log('=== Filter Change Handler Triggered ===')
      console.log('Current filter values:', filters)
      
      isApplyingFilters.value = true
      
      try {
        // Update all data sources when any filter changes
        await Promise.all([
          fetchRiskMetrics(),
          fetchRiskTrendData(),
          fetchCategoryDistribution(),
          fetchCustomAnalysisData(),
          fetchSpecializedChartData(),
          fetchMitigationCostData(),
          fetchHeatmapData()
        ])
      } catch (error) {
        console.error('Error applying filters:', error)
      } finally {
        isApplyingFilters.value = false
      }
    }

    // Watch all filter properties and trigger comprehensive update
    watch(filters, handleFilterChange, { deep: true })
    
    // Watch for Vuex store framework changes
    watch(
      () => store.state.framework.selectedFrameworkId,
      async (newFrameworkId, oldFrameworkId) => {
        // Only update if value actually changed
        if (newFrameworkId === oldFrameworkId) return
        
        console.log('🔄 RiskDashboard: Vuex store framework changed to:', newFrameworkId)
        // Update local filter to match store
        const oldFramework = filters.framework
        if (newFrameworkId === 'all' || !newFrameworkId) {
          filters.framework = 'all'
        } else {
          filters.framework = newFrameworkId
        }
        
        // Force data refresh if framework actually changed
        if (oldFramework !== filters.framework) {
          // Fetch policies for the new framework
          if (filters.framework !== 'all') {
            await fetchPolicies(filters.framework)
          } else {
            policies.value = []
          }
          
          // Update all data
          fetchRiskMetrics()
          fetchRiskTrendData()
          fetchCategoryDistribution()
          fetchCustomAnalysisData()
          fetchHeatmapData()
        }
      }
    )

    return {
      lineChartData,
      lineChartOptions,
      donutChartData,
      donutChartOptions,
      barChartData,
      barChartOptions,
      showRiskDetails,
      toggleRiskDetails,
      chartTypes,
      activeChart,
      selectedXAxis,
      selectedYAxis,
      metrics,
      filters,
      fetchRiskMetrics,
      categoryOptions,
      fetchCategoryOptions,
      fetchCategoryDistribution,
      categoryDistributionData,
      riskTrendData,
      highestCategory,
      getTrendText,
      getTrendClass,
      getChartIcon,
      fetchMitigationCostData,
      updateMitigationCostCharts,
      customChartOptions,
      customDonutOptions,
      heatmapCanvas,
      heatmapData,
      fetchHeatmapData,
      initializeHeatmap,
      generateChartColors,
      yAxisOptions,
      riskTrendOptions,
      fetchRiskTrendData,
      timeRangeOptions,
      isLoadingCustomChart,
      hasCustomChartData,
      isApplyingFilters,
      fetchCustomAnalysisData,
      filteredCategories,
      categoryPercentages,
      goBackToRiskRegister,
      categoryChartKey,
      // Framework and policy filtering
      frameworks,
      policies,
      loadingFrameworks,
      loadingPolicies,
      fetchFrameworks,
      fetchPolicies,
      onFrameworkChange,
      onPolicyChange,
      // Filter change handling
      handleFilterChange,
      // Popup functionality
      showCategoryPopup,
      selectedCategory,
      categoryRisks,
      isLoadingCategoryRisks,
      closeCategoryPopup,
      handleLegendClick,
      getPriorityClass,
      getStatusClass,
      formatDate,
      // Heatmap popup functionality
      showHeatmapPopup,
      selectedHeatmapCoordinates,
      heatmapRisks,
      isLoadingHeatmapRisks,
      closeHeatmapPopup,
      fetchRisksByHeatmapCoordinates,
      // Export functionality
      exportDashboardAsPDF,
      isExporting
    }
  }
}
</script>

<style scoped>
@import './RiskDashboard.css';
.risk-chart-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}
.risk-chart-tab-btn {
  background: none;
  border: none;
  font-size: 1rem;
  color: #888;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s, color 0.2s;
}
.risk-chart-tab-btn.active, .risk-chart-tab-btn:hover {
  background: #eef2ff;
  color: #4f6cff;
}
.risk-tabbed-chart-card {
  max-width: 900px;
  min-width: 480px;
  min-height: 280px;
  margin: 0 auto 24px auto;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.04);
  background: #fff;
}
.risk-chart-performance-summary {
  margin-top: 16px;
  font-size: 0.9rem;
}
.risk-dashboard-main-row {
  margin-top: 24px;
}
.risk-no-data-message {
  width: 100%;
  padding: 20px;
  text-align: center;
  background: white;
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  font-size: 15px;
  color: var(--text-secondary);
  grid-column: 1 / -1;
}
.risk-summary-value.empty {
  font-size: 14px;
  color: #9ca3af;
  font-style: italic;
}

/* Chart container specific styles */
.risk-chart-container {
  position: relative;
  width: 100%;
  height: 220px;
  min-height: 200px;
  max-height: 220px;
}

/* New styles for enhanced dashboard */
.risk-dashboard-charts {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.risk-chart-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
}

.risk-card-header {
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
}

.risk-card-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.risk-chart-insights {
  margin-top: 15px;
  padding-top: 12px;
  border-top: 1px solid rgba(0,0,0,0.05);
}

.risk-insight-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.risk-insight-label {
  font-weight: 500;
  color: var(--text-secondary);
}

.risk-insight-value {
  font-weight: 600;
}

.risk-insight-value.positive {
  color: var(--success-color);
}

.risk-insight-value.negative {
  color: var(--danger-color);
}

/* Loading spinner styles */
.risk-chart-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(79, 108, 255, 0.1);
  border-radius: 50%;
  border-top-color: var(--primary-color);
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 10px;
}

/* Filter loading indicator styles */
.risk-filter-loading-indicator {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
  border-radius: 12px;
}

.risk-filter-loading-indicator span {
  margin-top: 10px;
  color: var(--primary-color);
  font-weight: 500;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media screen and (max-width: 1200px) {
  .risk-dashboard-charts {
    grid-template-columns: 1fr;
  }
}
</style>