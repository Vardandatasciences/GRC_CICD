<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <div class="dashboard-header-left">
        <button class="back-arrow-btn" @click="goBackToIncident" title="Back to Incident Management">
          <i class="fas fa-arrow-left"></i>
        </button>
        <div>
          <h1>Incident Dashboard</h1>
          <p v-if="dataSourceMessage" class="data-source-message">{{ dataSourceMessage }}</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="refresh-btn" @click="refreshData"><i class="fas fa-sync"></i></button>
        <button class="download-btn" @click="downloadDashboardPDF" :disabled="isDownloading">
          <i class="fas fa-download" :class="{ 'fa-spin': isDownloading }"></i>
        </button>
      </div>
    </div>
    
    <div class="metrics-grid">
      <!-- Total Incidents Card -->
      <div class="metric-card">
        <div class="metric-icon incident-icon">
          <i class="fas fa-exclamation-circle"></i>
        </div>
        <div class="metric-content">
          <h3>Total Incidents</h3>
          <div class="metric-value">
            <span class="number">{{ dashboardData.total_count || 0 }}</span>
          </div>
          <div class="metric-change">
            {{ dashboardData.change_percentage > 0 ? '+' : '' }}{{ dashboardData.change_percentage }}% from last period
          </div>
        </div>
      </div>
    
      <!-- Open Incidents Card -->
      <div class="metric-card">
        <div class="metric-icon open-icon">
          <i class="fas fa-clipboard-list"></i>
        </div>
        <div class="metric-content">
          <h3>Open Incidents</h3>
          <div class="metric-value">
            <span class="number">{{ dashboardData.status_counts.scheduled || 0 }}</span>
          </div>
          <div class="metric-change">
            Awaiting resolution
          </div>
        </div>
      </div>
        
      <!-- Rejected Card -->
      <div class="metric-card">
        <div class="metric-icon rejected-icon">
          <i class="fas fa-ban"></i>
        </div>
        <div class="metric-content">
          <h3>Rejected</h3>
          <div class="metric-value">
            <span class="number">{{ dashboardData.status_counts.rejected || 0 }}</span>
          </div>
          <div class="metric-change">
            Rejected incidents
          </div>
        </div>
      </div>
    
      <!-- Approved Card -->
      <div class="metric-card">
        <div class="metric-icon approved-icon">
          <i class="fas fa-check-circle"></i>
        </div>
        <div class="metric-content">
          <h3>Approved</h3>
          <div class="metric-value">
            <span class="number">{{ dashboardData.status_counts.approved || 0 }}</span>
          </div>
          <div class="metric-change">
            Approved incidents
          </div>
        </div>
      </div>
    </div>
    
    <!-- Framework Filter -->
    <div class="framework-filter" style="margin-bottom: 4px;">
      <!-- Single Row: All Four Filters -->
      <div class="filter-row" style="display: flex; align-items: flex-end; gap: 24px; flex-wrap: nowrap; width: 100%;">
        <label style="font-size: 11px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 4px;">Framework Selection:</label>
        <select v-model="selectedFramework" @change="onFrameworkChange" :disabled="loadingFrameworks" :class="{ 'filter-active': selectedFramework }" style="padding: 12px 32px 12px 14px; border: 2px solid #e2e8f0; border-radius: 8px; background: transparent; color: #374151; font-size: 14px; font-weight: 500; outline: none; transition: all 0.2s ease; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); width: auto; min-width: 150px;">
          <option value="">All Frameworks</option>
          <option v-if="loadingFrameworks" value="" disabled>Loading frameworks...</option>
          <option v-else v-for="framework in frameworks" :key="framework.id" :value="framework.id">
            {{ framework.name }}
          </option>
        </select>
        <label style="font-size: 11px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 4px;">Time Range:</label>
        <select v-model="selectedTimeRange" @change="fetchDashboardData" style="padding: 12px 32px 12px 14px; border: 2px solid #e2e8f0; border-radius: 8px; background: transparent url('data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2212%22 height=%2212%22 viewBox=%220 0 12 12%22%3E%3Cpath fill=%22%2364748b%22 d=%22M6 9L1 4h10z%22/%3E%3C/svg%3E') no-repeat right 12px center; color: #374151; font-size: 14px; font-weight: 500; outline: none; width: 100%; transition: all 0.2s ease; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); appearance: none; -webkit-appearance: none; -moz-appearance: none;">
          <option value="Last 6 Months">Last 6 Months</option>
          <option value="Last 3 Months">Last 3 Months</option>
          <option value="Last Month">Last Month</option>
          <option value="Last Week">Last Week</option>
        </select>
        <label style="font-size: 11px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 4px;">Category:</label>
        <select v-model="selectedCategory" @change="fetchDashboardData" style="padding: 12px 32px 12px 14px; border: 2px solid #e2e8f0; border-radius: 8px; background: transparent url('data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2212%22 height=%2212%22 viewBox=%220 0 12 12%22%3E%3Cpath fill=%22%2364748b%22 d=%22M6 9L1 4h10z%22/%3E%3C/svg%3E') no-repeat right 12px center; color: #374151; font-size: 14px; font-weight: 500; outline: none; width: 100%; transition: all 0.2s ease; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); appearance: none; -webkit-appearance: none; -moz-appearance: none;">
          <option value="All Categories">All Categories</option>
          <option value="Security">Security</option>
          <option value="Compliance">Compliance</option>
          <option value="Operational">Operational</option>
        </select>
        <label style="font-size: 11px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 4px;">Priority:</label>
        <select v-model="selectedPriority" @change="fetchDashboardData" style="padding: 12px 32px 12px 14px; border: 2px solid #e2e8f0; border-radius: 8px; background: transparent url('data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2212%22 height=%2212%22 viewBox=%220 0 12 12%22%3E%3Cpath fill=%22%2364748b%22 d=%22M6 9L1 4h10z%22/%3E%3C/svg%3E') no-repeat right 12px center; color: #374151; font-size: 14px; font-weight: 500; outline: none; width: 100%; transition: all 0.2s ease; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); appearance: none; -webkit-appearance: none; -moz-appearance: none;">
          <option value="All Priorities">All Priorities</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
      </div>
    </div>
    
    <!-- Charts Grid - 2x2 Layout -->
    <div class="charts-grid">
      <!-- Chart 1: Incident vs Status (Donut Chart) -->
      <div class="chart-card">
        <div class="chart-header">
          <h2>Incident vs Status</h2>
          <div class="chart-icon">
            <i class="fas fa-chart-pie"></i>
          </div>
        </div>
        <div class="chart-container">
          <canvas id="statusChart"></canvas>
        </div>
      </div>
      
      <!-- Chart 2: Incident vs Origin (Bar Chart) -->
      <div class="chart-card">
        <div class="chart-header">
          <h2>Incident vs Origin</h2>
          <div class="chart-icon">
            <i class="fas fa-chart-bar"></i>
          </div>
        </div>
        <div class="chart-container">
          <canvas id="originChart"></canvas>
        </div>
      </div>
      
      <!-- Chart 3: Incident vs Risk Category (Line Chart) -->
      <div class="chart-card">
        <div class="chart-header">
          <h2>Incident vs Risk Category</h2>
          <div class="chart-icon">
            <i class="fas fa-chart-line"></i>
          </div>
        </div>
        <div class="chart-container">
          <canvas id="categoryChart"></canvas>
        </div>
      </div>
      
      <!-- Chart 4: Incident vs Risk Priority (Bar Chart) -->
      <div class="chart-card">
        <div class="chart-header">
          <h2>Incident vs Risk Priority</h2>
          <div class="chart-icon">
            <i class="fas fa-chart-bar"></i>
          </div>
        </div>
        <div class="chart-container">
          <canvas id="priorityChart"></canvas>
        </div>
      </div>
    </div>
    
    <!-- Recent Incidents Section -->
    <div class="recent-section">
      <div class="recent-activity">
        <div class="activity-header">
          <h2>Recent Incidents</h2>
        </div>
        <div class="activity-list">
          <div v-for="(incident, index) in recentIncidents" :key="index" class="activity-item">
            <div class="activity-icon" :class="incident.priority_class">
              <i :class="incident.icon"></i>
            </div>
            <div class="activity-details">
              <h4>{{ incident.IncidentTitle }}</h4>
              <p>{{ truncateDescription(incident.Description, 100) }}</p>
              <div class="activity-meta">
                <span class="activity-tag origin-tag">{{ incident.origin_text }}</span>
                <span v-if="incident.status_class" class="activity-tag status-tag" :class="incident.status_class">{{ incident.Status }}</span>
                <span class="activity-time">{{ formatDate(incident.CreatedAt) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import '@fortawesome/fontawesome-free/css/all.min.css'
import { incidentService } from '@/services/api'
import { PopupModal } from '@/modules/popup'
import { AccessUtils } from '@/utils/accessUtils'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import incidentDataService from '../../services/incidentService.js' // Updated: Use consistent naming

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend
)

export default {
  name: 'IncidentPerformanceDashboard',
  components: {
    PopupModal
  },
  data() {
    return {
      selectedFramework: '',
      selectedTimeRange: 'Last 6 Months',
      selectedCategory: 'All Categories',
      selectedPriority: 'All Priorities',
      frameworks: [],
      loadingFrameworks: false,
      isDownloading: false,
      dataSourceMessage: '', // Data source indicator
      api: {
        incidentService
      },
      dashboardData: {
        status_counts: {
          scheduled: 0,
          approved: 0,
          resolved: 0,
          rejected: 0
        },
        total_count: 0,
        change_percentage: 0,
        resolution_rate: 0
      },
      charts: {
        statusChart: null,
        originChart: null,
        categoryChart: null,
        priorityChart: null
      },
      chartData: {
        status: null,
        origin: null,
        category: null,
        priority: null
      },
      recentIncidents: []
    }
  },
  async mounted() {
    console.log('🚀 [IncidentPerformanceDashboard] Component mounted');

    // Load dashboard and recent incidents immediately (do not block on framework/API calls)
    this.fetchDashboardData()
    this.fetchRecentIncidents()

    // Load frameworks and selected framework in parallel without blocking initial render
    this.fetchFrameworks()
    this.fetchSelectedFramework()
  },
  beforeUnmount() {
    this.destroyAllCharts()
  },
  beforeRouteLeave(to, from, next) {
    this.destroyAllCharts()
    next()
  },
  methods: {
    destroyAllCharts() {
      Object.values(this.charts).forEach(chart => {
        if (chart) {
          chart.destroy()
        }
      })
      this.charts = {
        statusChart: null,
        originChart: null,
        categoryChart: null,
        priorityChart: null
      }
    },
    
    async fetchFrameworks() {
      try {
        this.loadingFrameworks = true
        console.log('🔍 Fetching frameworks...')
        const response = await this.api.incidentService.getIncidentFrameworks()
        console.log('✅ Frameworks API response:', response.data)
        
        // Handle the API response format
        let frameworksData = []
        if (response.data.success && response.data.frameworks) {
          frameworksData = response.data.frameworks
        } else if (response.data.success && Array.isArray(response.data.data)) {
          frameworksData = response.data.data
        } else if (Array.isArray(response.data)) {
          frameworksData = response.data
        } else {
          console.error('Unexpected frameworks response format:', response.data)
          this.frameworks = []
          return
        }
        
        this.frameworks = frameworksData.map(framework => ({
          id: framework.id || framework.FrameworkId,
          name: framework.name || framework.FrameworkName || 'Unknown Framework'
        }))
        
        console.log('✅ Processed frameworks:', this.frameworks)
        
        // After frameworks are loaded, try to set the selected framework
        await this.setSelectedFrameworkIfAvailable()
      } catch (error) {
        console.error('❌ Error fetching frameworks:', error)
        console.error('❌ Error details:', error.response?.data || error.message)
        this.frameworks = []
      } finally {
        this.loadingFrameworks = false
      }
    },

    async fetchSelectedFramework() {
      try {
        console.log('🔍 Fetching selected framework from home page...')
        const response = await this.api.incidentService.getSelectedFramework()
        console.log('✅ Selected framework API response:', response.data)
        
        if (response.data && response.data.frameworkId) {
          this.selectedFramework = response.data.frameworkId
          console.log('✅ Set selected framework ID:', this.selectedFramework)
          
          // Wait for frameworks to be loaded before refreshing data
          if (this.frameworks.length > 0) {
            await this.setSelectedFrameworkIfAvailable()
            await this.fetchDashboardData()
          } else {
            console.log('⚠️ Frameworks not loaded yet, will refresh data after frameworks are loaded')
          }
        } else {
          console.log('⚠️ No framework selected or frameworkId not found in response')
          // Try localStorage fallback
          const storedFrameworkId = localStorage.getItem('selectedFrameworkId') || localStorage.getItem('frameworkId')
          if (storedFrameworkId) {
            this.selectedFramework = storedFrameworkId
            console.log('✅ Using framework ID from localStorage:', this.selectedFramework)
            
            // Wait for frameworks to be loaded before refreshing data
            if (this.frameworks.length > 0) {
              await this.setSelectedFrameworkIfAvailable()
              await this.fetchDashboardData()
            }
          }
        }
      } catch (error) {
        console.warn('⚠️ Could not fetch selected framework:', error)
        // Try localStorage fallback
        const storedFrameworkId = localStorage.getItem('selectedFrameworkId') || localStorage.getItem('frameworkId')
        if (storedFrameworkId) {
          this.selectedFramework = storedFrameworkId
          console.log('✅ Using framework ID from localStorage as fallback:', this.selectedFramework)
          
          // Wait for frameworks to be loaded before refreshing data
          if (this.frameworks.length > 0) {
            await this.setSelectedFrameworkIfAvailable()
            await this.fetchDashboardData()
          }
        }
      }
    },

    async setSelectedFrameworkIfAvailable() {
      // If we already have a selected framework, make sure it exists in the frameworks list
      if (this.selectedFramework && this.frameworks.length > 0) {
        const frameworkExists = this.frameworks.some(f => f.id == this.selectedFramework)
        if (!frameworkExists) {
          console.warn('⚠️ Selected framework not found in frameworks list, clearing selection')
          this.selectedFramework = ''
          // Load data for all frameworks since the selected one doesn't exist
          await this.fetchDashboardData()
        } else {
          const selectedFrameworkName = this.frameworks.find(f => f.id == this.selectedFramework)?.name
          console.log('✅ Selected framework confirmed in frameworks list:', this.selectedFramework, '-', selectedFrameworkName)
          // Refresh dashboard data with the confirmed framework
          await this.fetchDashboardData()
        }
      } else if (!this.selectedFramework && this.frameworks.length > 0) {
        console.log('ℹ️ No framework selected, will load data for all frameworks')
      }
    },
    
    async fetchRecentIncidents() {
      try {
        console.log('🔍 [IncidentPerformanceDashboard] Checking for cached recent incidents...');

        // Check if prefetch is in progress or cache is available
        if (!window.incidentDataFetchPromise && !incidentDataService.hasValidIncidentsCache()) {
          console.log('🚀 [IncidentPerformanceDashboard] Starting incident prefetch (user navigated directly)...');
          window.incidentDataFetchPromise = incidentDataService.fetchAllIncidentData();
        }

        // Wait for prefetch if it's in progress
        if (window.incidentDataFetchPromise) {
          console.log('⏳ [IncidentPerformanceDashboard] Waiting for incident prefetch to complete...');
          try {
            await window.incidentDataFetchPromise;
            console.log('✅ [IncidentPerformanceDashboard] Incident prefetch completed');
          } catch (prefetchError) {
            console.warn('⚠️ [IncidentPerformanceDashboard] Incident prefetch failed, will fetch directly from API', prefetchError);
          }
        }

        // Use cached incidents if available - get most recent from cache
        if (incidentDataService.hasValidIncidentsCache()) {
          console.log('✅ [IncidentPerformanceDashboard] Using cached incidents for recent incidents');
          const cachedIncidents = incidentDataService.getData('incidents') || [];
          
          // Sort by date (most recent first) and take first 3
          const recentIncidents = cachedIncidents
            .sort((a, b) => {
              const dateA = new Date(a.CreatedAt || a.created_at || 0);
              const dateB = new Date(b.CreatedAt || b.created_at || 0);
              return dateB - dateA;
            })
            .slice(0, 3);
          
          this.recentIncidents = recentIncidents.map(incident => {
            // Add priority class and icon based on severity
            let priorityClass = 'medium'
            let icon = 'fas fa-exclamation-triangle'
            
            if (incident.RiskPriority) {
              const priority = incident.RiskPriority.toLowerCase();
              if (priority.includes('high')) {
                priorityClass = 'high'
                icon = 'fas fa-radiation'
              } else if (priority.includes('low')) {
                priorityClass = 'low'
                icon = 'fas fa-info-circle'
              }
            }
            
            // Add status class
            let statusClass = '';
            if (incident.Status) {
              const status = incident.Status.toLowerCase();
              if (status.includes('rejected')) {
                statusClass = 'rejected';
              } else if (status.includes('approved')) {
                statusClass = 'approved';
              } else if (status.includes('scheduled')) {
                statusClass = 'scheduled';
              }
            }
            
            // Add origin info
            let originText = incident.Origin || 'Unknown';
            
            return {
              ...incident,
              priority_class: priorityClass,
              status_class: statusClass,
              icon: icon,
              origin_text: originText
            }
          });
          return;
        }
        
        // Fallback: Fetch directly from API
        console.log('⚠️ [IncidentPerformanceDashboard] No cached incidents, fetching recent incidents from API...');
        const response = await this.api.incidentService.getRecentIncidents(3)
        if (response.data && response.data.success) {
          this.recentIncidents = response.data.incidents.map(incident => {
            // Add priority class and icon based on severity
            let priorityClass = 'medium'
            let icon = 'fas fa-exclamation-triangle'
            
            if (incident.RiskPriority) {
              const priority = incident.RiskPriority.toLowerCase();
              if (priority.includes('high')) {
                priorityClass = 'high'
                icon = 'fas fa-radiation'
              } else if (priority.includes('low')) {
                priorityClass = 'low'
                icon = 'fas fa-info-circle'
              }
            }
            
            // Add status class
            let statusClass = '';
            if (incident.Status) {
              const status = incident.Status.toLowerCase();
              if (status.includes('rejected')) {
                statusClass = 'rejected';
              } else if (status.includes('approved')) {
                statusClass = 'approved';
              } else if (status.includes('scheduled')) {
                statusClass = 'scheduled';
              }
            }
            
            // Add origin info
            let originText = incident.Origin || 'Unknown';
            
            return {
              ...incident,
              priority_class: priorityClass,
              status_class: statusClass,
              icon: icon,
              origin_text: originText
            }
          })
        } else {
          console.error('Failed to fetch recent incidents')
          this.recentIncidents = []
        }
      } catch (error) {
        console.error('Error fetching recent incidents:', error)
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.recentIncidents = []
      }
    },
         async fetchDashboardData() {
      // Start timing
      const startTime = performance.now();
      
      // Helper function to format time taken (defined outside try/catch for scope access)
      const getTimeTaken = () => {
        const elapsed = performance.now() - startTime;
        if (elapsed < 100) {
          return `${elapsed.toFixed(0)}ms`;
        } else {
          return `${(elapsed / 1000).toFixed(2)}s`;
        }
      };
      
      try {
        console.log('🔄 [IncidentPerformanceDashboard] fetchDashboardData called')

        // Check which filters are active
        const hasFrameworkFilter = this.selectedFramework && this.selectedFramework !== '';
        const hasTimeRangeFilter = this.selectedTimeRange && this.selectedTimeRange !== 'Last 6 Months';
        const hasCategoryFilter = this.selectedCategory && this.selectedCategory !== 'All Categories';
        const hasPriorityFilter = this.selectedPriority && this.selectedPriority !== 'All Priorities';
        
        // Complex filters that require API calls (time range requires server-side date filtering)
        const hasComplexFilters = hasTimeRangeFilter;
        
        // Check if prefetch is in progress or cache is available
        if (!window.incidentDataFetchPromise && !incidentDataService.hasValidIncidentsCache()) {
          console.log('🚀 [IncidentPerformanceDashboard] Starting incident prefetch (user navigated directly)...');
          window.incidentDataFetchPromise = incidentDataService.fetchAllIncidentData();
        }

        // Wait for prefetch if it's in progress (but don't block too long)
        if (window.incidentDataFetchPromise) {
          console.log('⏳ [IncidentPerformanceDashboard] Waiting for incident prefetch to complete...');
          try {
            await Promise.race([
              window.incidentDataFetchPromise,
              new Promise(resolve => setTimeout(resolve, 2000)) // Max 2 seconds wait
            ]);
            console.log('✅ [IncidentPerformanceDashboard] Incident prefetch completed or timeout');
          } catch (prefetchError) {
            console.warn('⚠️ [IncidentPerformanceDashboard] Incident prefetch failed, will use cache or API', prefetchError);
          }
        }

        // PRIORITY 1: Try to load from prefetched dashboard cache (no filters or simple filters)
        if (!hasComplexFilters) {
          // Check if we have cached dashboard summary data
          const cachedDashboard = incidentDataService.getKPIData('dashboardSummary');
          const cachedStatusChart = incidentDataService.getKPIData('statusChart');
          const cachedOriginChart = incidentDataService.getKPIData('originChart');
          const cachedCategoryChart = incidentDataService.getKPIData('categoryChart');
          const cachedPriorityChart = incidentDataService.getKPIData('priorityChart');
          
          // If ALL dashboard and chart data is cached, use it immediately
          if (cachedDashboard && cachedStatusChart && cachedOriginChart && cachedCategoryChart && cachedPriorityChart) {
            console.log('⚡⚡⚡ [IncidentPerformanceDashboard] ALL dashboard & chart data in cache - INSTANT LOAD!');
            
            // Apply filters if needed
            const filters = {};
            if (hasFrameworkFilter) filters.frameworkId = this.selectedFramework;
            if (hasCategoryFilter) filters.category = this.selectedCategory;
            if (hasPriorityFilter) filters.priority = this.selectedPriority;
            
            // If filters are applied, filter the cached data
            let dashboardData = cachedDashboard;
            let statusChart = cachedStatusChart;
            let originChart = cachedOriginChart;
            let categoryChart = cachedCategoryChart;
            let priorityChart = cachedPriorityChart;
            
            if (hasFrameworkFilter || hasCategoryFilter || hasPriorityFilter) {
              console.log('🔍 Applying filters to cached data:', filters);
              // Recompute from cached incidents with filters
              const basicKPIs = incidentDataService.computeBasicKPIsFromCache(filters);
              dashboardData = {
                data: {
                  summary: {
                    status_counts: basicKPIs.statusCounts,
                    total_count: basicKPIs.totalCount,
                    change_percentage: basicKPIs.change_percentage,
                    resolution_rate: basicKPIs.resolution_rate
                  }
                },
                success: true
              };
              
              statusChart = { chartData: incidentDataService.computeChartDataFromCache('Status', filters), success: true };
              originChart = { chartData: incidentDataService.computeChartDataFromCache('Origin', filters), success: true };
              categoryChart = { chartData: incidentDataService.computeChartDataFromCache('RiskCategory', filters), success: true };
              priorityChart = { chartData: incidentDataService.computeChartDataFromCache('RiskPriority', filters), success: true };
            }
            
            // Set dashboard data
            const summary = dashboardData.data?.summary || {};
            this.dashboardData = {
              status_counts: summary.status_counts || {},
              total_count: summary.total_count || 0,
              change_percentage: summary.change_percentage || 0,
              resolution_rate: summary.resolution_rate || 0
            };
            
            // Set chart data
            this.chartData = {
              status: statusChart.chartData || statusChart,
              origin: originChart.chartData || originChart,
              category: categoryChart.chartData || categoryChart,
              priority: priorityChart.chartData || priorityChart
            };
            
            // Set data source message with timing
            const timeTaken = getTimeTaken();
            this.dataSourceMessage = '';
            
            // Update charts
            await this.$nextTick();
            this.updateAllCharts();
            
            console.log(`✅✅✅ [IncidentPerformanceDashboard] Dashboard loaded from cache - ${timeTaken}`);
            return;
          }
        }
        
        // PRIORITY 2: Check if we can compute dashboard data from cached incidents
        // We can use cache if: no complex filters (time range) AND we have cached incidents
        if (!hasComplexFilters && incidentDataService.hasValidIncidentsCache()) {
          console.log('⚡ [IncidentPerformanceDashboard] Computing dashboard data from cached incidents - INSTANT!');
          
          // Prepare filters for client-side filtering
          const filters = {};
          if (hasFrameworkFilter) {
            filters.frameworkId = this.selectedFramework;
            console.log('🔍 [IncidentPerformanceDashboard] Applying framework filter to cache:', this.selectedFramework);
          }
          if (hasCategoryFilter) {
            filters.category = this.selectedCategory;
            console.log('🔍 [IncidentPerformanceDashboard] Applying category filter to cache:', this.selectedCategory);
          }
          if (hasPriorityFilter) {
            filters.priority = this.selectedPriority;
            console.log('🔍 [IncidentPerformanceDashboard] Applying priority filter to cache:', this.selectedPriority);
          }
          
          // Compute dashboard metrics from cached incidents with filters
          const basicKPIs = incidentDataService.computeBasicKPIsFromCache(filters);
          
          this.dashboardData = {
            status_counts: basicKPIs.statusCounts,
            total_count: basicKPIs.totalCount,
            change_percentage: basicKPIs.change_percentage,
            resolution_rate: basicKPIs.resolution_rate
          };
          
          // Set data source message
          this.dataSourceMessage = '';
          
          // Compute chart data from cache INSTANTLY with filters (no API calls needed!)
          console.log('⚡ [IncidentPerformanceDashboard] Computing chart data from cache with filters - INSTANT!');
          const statusData = incidentDataService.computeChartDataFromCache('Status', filters);
          const originData = incidentDataService.computeChartDataFromCache('Origin', filters);
          const categoryData = incidentDataService.computeChartDataFromCache('RiskCategory', filters);
          const priorityData = incidentDataService.computeChartDataFromCache('RiskPriority', filters);
          
          this.chartData = {
            status: statusData,
            origin: originData,
            category: categoryData,
            priority: priorityData
          };
          
          // Update charts immediately (no loading spinner!)
          await this.$nextTick();
          this.updateAllCharts();
          
          const timeTaken2 = getTimeTaken();
          console.log(`✅ [IncidentPerformanceDashboard] Dashboard and charts loaded from cache - ${timeTaken2}`, {
            totalCount: basicKPIs.totalCount,
            filters: filters,
            chartData: {
              status: statusData.labels.length,
              origin: originData.labels.length,
              category: categoryData.labels.length,
              priority: priorityData.labels.length
            }
          });
          return;
        }
        
        // If complex filters (time range) or no cached data, fetch from API
        console.log(hasComplexFilters ? '🔍 [IncidentPerformanceDashboard] Complex filters (time range) active, fetching from API' : '⚠️ [IncidentPerformanceDashboard] No cached data, fetching from API');

        // Fetch dashboard summary data
        let dashboardResponse
        try {
          const dashboardRequest = {}
          
          // Add framework filter if selected
          if (this.selectedFramework) {
            dashboardRequest.framework_id = this.selectedFramework
            console.log('Applying framework filter to dashboard:', this.selectedFramework)
          }
          
          // Add other filters
          if (this.selectedTimeRange && this.selectedTimeRange !== 'Last 6 Months') {
            dashboardRequest.timeRange = this.selectedTimeRange
          }
          
          if (this.selectedCategory && this.selectedCategory !== 'All Categories') {
            dashboardRequest.category = this.selectedCategory
          }
          
          if (this.selectedPriority && this.selectedPriority !== 'All Priorities') {
            dashboardRequest.priority = this.selectedPriority
          }
          
          console.log('Dashboard request with filters:', dashboardRequest)
          dashboardResponse = await this.api.incidentService.getIncidentDashboard(dashboardRequest)
          console.log('Incident Dashboard API Response:', dashboardResponse.data)
        } catch (err) {
          console.error('Error fetching dashboard data:', err)
          if (AccessUtils.handleApiError(err)) {
            return
          }
          throw new Error(`Dashboard fetch failed: ${err.message}`)
        }

        // Fetch data for each chart
        const chartPromises = [
          this.fetchChartData('Status', 'doughnut'),
          this.fetchChartData('Origin', 'bar'),
          this.fetchChartData('RiskCategory', 'line'),
          this.fetchChartData('RiskPriority', 'bar')
        ]

        const [statusData, originData, categoryData, priorityData] = await Promise.all(chartPromises)

        if (dashboardResponse.data && dashboardResponse.data.success) {
          const summary = dashboardResponse.data.data?.summary || {}
          console.log('Dashboard summary data:', summary)
          
          this.dashboardData = {
            status_counts: summary.status_counts || {},
            total_count: summary.total_count || 0,
            change_percentage: summary.change_percentage || 0,
            resolution_rate: summary.resolution_rate || 0
          }
          
          // Set data source message for API fetch
          this.dataSourceMessage = '';
          
          // Update chart data
          this.chartData = {
            status: statusData,
            origin: originData,
            category: categoryData,
            priority: priorityData
          }
          
          const timeTaken3 = getTimeTaken();
          console.log(`✅ [IncidentPerformanceDashboard] Dashboard loaded from API - ${timeTaken3}`)
          console.log('Updated chart data:', this.chartData)
          
          // Wait for the next tick to ensure DOM is updated
          await this.$nextTick()
          this.updateAllCharts()
        } else {
          const errorMessage = dashboardResponse.data?.message || 'API request failed'
          const timeTakenError = getTimeTaken();
          console.error(`❌ API Error after ${timeTakenError}:`, errorMessage)
          throw new Error(errorMessage)
        }
      } catch (error) {
        const timeTakenError2 = getTimeTaken();
        console.error(`❌ Error in fetchDashboardData after ${timeTakenError2}:`, error)
        
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        // Set default values on error with timing message
        this.dashboardData = {
          status_counts: { scheduled: 0, approved: 0, rejected: 0 },
          total_count: 0,
          change_percentage: 0,
          resolution_rate: 0
        }
        
        const defaultChartData = {
          labels: ['No Data'],
          datasets: [{
            label: 'Error Loading Data',
            data: [0],
            backgroundColor: 'rgba(244, 67, 54, 0.6)',
            borderColor: '#F44336',
            borderWidth: 1
          }]
        }
        
        this.chartData = {
          status: defaultChartData,
          origin: defaultChartData,
          category: defaultChartData,
          priority: defaultChartData
        }
        
        // Set error message with timing
        this.dataSourceMessage = `❌ Error loading data - ${timeTakenError2}`;
        
        await this.$nextTick()
        this.updateAllCharts()
      }
    },
    async fetchChartData(yAxis, chartType) {
      try {
        // Check which filters are active
        const hasTimeRangeFilter = this.selectedTimeRange && this.selectedTimeRange !== 'Last 6 Months';
        
        // If no time range filter and we have cached incidents, compute from cache
        // (framework, category, priority filters are applied in computeChartDataFromCache)
        if (!hasTimeRangeFilter && incidentDataService.hasValidIncidentsCache()) {
          // Prepare filters for client-side filtering
          const filters = {};
          if (this.selectedFramework) {
            filters.frameworkId = this.selectedFramework;
          }
          if (this.selectedCategory && this.selectedCategory !== 'All Categories') {
            filters.category = this.selectedCategory;
          }
          if (this.selectedPriority && this.selectedPriority !== 'All Priorities') {
            filters.priority = this.selectedPriority;
          }
          
          console.log(`⚡ [IncidentPerformanceDashboard] Computing ${yAxis} chart data from cache with filters - INSTANT!`, filters);
          return incidentDataService.computeChartDataFromCache(yAxis, filters);
        }
        
        // If time range filter is active or no cache, fetch from API
        const requestData = {
          xAxis: 'Time',
          yAxis: yAxis
        }
        
        // Add framework filter if selected
        if (this.selectedFramework) {
          requestData.frameworkId = this.selectedFramework
          console.log(`Applying framework filter for ${yAxis} chart:`, this.selectedFramework)
        }
        
        // Add other filters with proper time range mapping
        if (this.selectedTimeRange && this.selectedTimeRange !== 'Last 6 Months') {
          // Map frontend time range values to backend format
          const timeRangeMap = {
            'Last Week': '7days',
            'Last Month': '30days',
            'Last 3 Months': '90days',
            'Last 6 Months': 'all' // This shouldn't be sent but just in case
          }
          requestData.timeRange = timeRangeMap[this.selectedTimeRange] || this.selectedTimeRange
        }
        
        if (this.selectedCategory && this.selectedCategory !== 'All Categories') {
          requestData.category = this.selectedCategory
        }
        
        if (this.selectedPriority && this.selectedPriority !== 'All Priorities') {
          requestData.priority = this.selectedPriority
        }
        
        console.log(`🔍 [IncidentPerformanceDashboard] Fetching ${yAxis} chart data from API (time range filter active or no cache)...`)
        const response = await this.api.incidentService.getIncidentAnalytics(requestData)
        
        if (response.data && response.data.success && response.data.chartData) {
          return response.data.chartData
        } else {
          console.warn(`No data received for ${yAxis} chart`)
          return this.getDefaultChartData(chartType)
        }
      } catch (error) {
        console.error(`Error fetching ${yAxis} chart data:`, error)
        // Fallback to cache if API fails and we have cache
        if (incidentDataService.hasValidIncidentsCache()) {
          console.log(`⚠️ [IncidentPerformanceDashboard] API failed for ${yAxis}, falling back to cache...`);
          const filters = {};
          if (this.selectedFramework) filters.frameworkId = this.selectedFramework;
          if (this.selectedCategory && this.selectedCategory !== 'All Categories') filters.category = this.selectedCategory;
          if (this.selectedPriority && this.selectedPriority !== 'All Priorities') filters.priority = this.selectedPriority;
          return incidentDataService.computeChartDataFromCache(yAxis, filters);
        }
        return this.getDefaultChartData(chartType)
      }
    },
    getDefaultChartData(chartType) {
      const defaultData = {
        labels: ['No Data Available'],
        datasets: [{
          label: 'No Data',
          data: [1],
          backgroundColor: 'rgba(158, 158, 158, 0.6)',
          borderColor: '#9E9E9E',
          borderWidth: 1
        }]
      }
      
      if (chartType === 'line') {
        defaultData.datasets[0].tension = 0.1
        defaultData.datasets[0].fill = false
      }
      
      return defaultData
    },
    updateAllCharts() {
      this.updateChart('statusChart', 'doughnut', this.chartData.status, 'statusChart')
      this.updateChart('originChart', 'bar', this.chartData.origin, 'originChart')
      this.updateChart('categoryChart', 'line', this.chartData.category, 'categoryChart')
      this.updateChart('priorityChart', 'bar', this.chartData.priority, 'priorityChart')
    },
    updateChart(chartId, chartType, chartData, chartIdForColors = '') {
      try {
        // Destroy existing chart if it exists
        if (this.charts[chartId]) {
          this.charts[chartId].destroy()
        }

        // Get the canvas element
        const canvas = document.getElementById(chartId)
        if (!canvas) {
          console.error(`Chart canvas not found: ${chartId}`)
          return
        }

        // Create the chart configuration
        const config = this.createChartConfig(chartType, chartData, chartIdForColors)

        // Create new chart instance
        this.charts[chartId] = new ChartJS(canvas, config)
      } catch (error) {
        console.error(`Error in updateChart for ${chartId}:`, error)
        this.charts[chartId] = null
      }
    },
    createChartConfig(chartType, chartData, chartId = '') {
      if (!chartData) {
        return {
          type: chartType,
          data: {
            labels: ['No Data'],
            datasets: [{
              label: 'No Data',
              data: [0],
              backgroundColor: 'rgba(200, 200, 200, 0.5)',
              borderColor: '#ccc',
              borderWidth: 1
            }]
          },
          options: this.getChartOptions(chartType)
        }
      }

      // Check if we have multiple datasets
      const hasMultipleDatasets = Array.isArray(chartData.datasets) && chartData.datasets.length > 1;
      
      let datasets;
      
      if (hasMultipleDatasets) {
        // Use the datasets as provided by the backend
        datasets = chartData.datasets.map((dataset, index) => {
          const colors = this.getColorForIndex(index);
          return {
            ...dataset,
            backgroundColor: colors.backgroundColor,
            borderColor: colors.borderColor,
            borderWidth: 1,
            tension: chartType === 'line' ? 0.1 : undefined,
            fill: chartType === 'line' ? false : undefined
          };
        });
      } else {
        // Single dataset with custom colors
        const dataset = {
          ...chartData.datasets[0],
          backgroundColor: this.getBackgroundColors(chartType, chartData.labels, chartId),
          borderColor: this.getBorderColors(chartType, chartData.labels, chartId),
          borderWidth: 1
        };

        if (chartType === 'line') {
          dataset.tension = 0.1;
          dataset.fill = false;
        }
        
        datasets = [dataset];
      }

      return {
        type: chartType,
        data: {
          labels: chartData.labels,
          datasets: datasets
        },
        options: this.getChartOptions(chartType)
      }
    },
    
    // Helper method to get color for multiple datasets
    getColorForIndex(index) {
      const colors = [
        { backgroundColor: 'rgba(255, 99, 132, 0.6)', borderColor: 'rgb(255, 99, 132)' },
        { backgroundColor: 'rgba(54, 162, 235, 0.6)', borderColor: 'rgb(54, 162, 235)' },
        { backgroundColor: 'rgba(255, 206, 86, 0.6)', borderColor: 'rgb(255, 206, 86)' },
        { backgroundColor: 'rgba(75, 192, 192, 0.6)', borderColor: 'rgb(75, 192, 192)' },
        { backgroundColor: 'rgba(153, 102, 255, 0.6)', borderColor: 'rgb(153, 102, 255)' },
        { backgroundColor: 'rgba(255, 159, 64, 0.6)', borderColor: 'rgb(255, 159, 64)' },
        { backgroundColor: 'rgba(199, 199, 199, 0.6)', borderColor: 'rgb(199, 199, 199)' }
      ];
      
      // Use modulo to cycle through colors if we have more datasets than colors
      return colors[index % colors.length];
    },
    getChartOptions(chartType) {
      const options = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 500,
          easing: 'easeInOutQuad'
        },
        plugins: {
          legend: {
            display: true,
            position: 'bottom'
          },
          tooltip: {
            enabled: true,
            callbacks: {
              label: (context) => {
                if (['pie', 'doughnut'].includes(chartType)) {
                  const label = context.label || ''
                  const value = context.raw || 0
                  const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0)
                  const percentage = ((value / total) * 100).toFixed(1)
                  return `${label}: ${value} (${percentage}%)`
                }
                return `Count: ${context.raw}`
              }
            }
          }
        }
      }

             if (['bar', 'line'].includes(chartType)) {
         options.scales = {
           y: {
             beginAtZero: true,
             ticks: {
               stepSize: 1,
               precision: 0
             }
           }
         }
       }

      return options
    },

    getBackgroundColors(chartType, labels, chartId = '') {
      const colorMaps = {
        Status: {
          'Scheduled': 'rgba(255, 152, 0, 0.6)',
          'Approved': 'rgba(76, 175, 80, 0.6)',
          'Rejected': 'rgba(244, 67, 54, 0.6)',
          'Resolved': 'rgba(33, 150, 243, 0.6)'
        },
        Origin: {
          'Manual': 'rgba(33, 150, 243, 0.6)',
          'SIEM': 'rgba(156, 39, 176, 0.6)',
          'Audit Finding': 'rgba(255, 193, 7, 0.6)',
          'Compliance Gap': 'rgba(255, 87, 34, 0.6)',
          'Other': 'rgba(121, 85, 72, 0.6)'
        },
        RiskCategory: {
          'Security': 'rgba(244, 67, 54, 0.6)',
          'Compliance': 'rgba(156, 39, 176, 0.6)',
          'Operational': 'rgba(255, 152, 0, 0.6)',
          'Financial': 'rgba(33, 150, 243, 0.6)',
          'Strategic': 'rgba(76, 175, 80, 0.6)',
          'Reputational': 'rgba(121, 85, 72, 0.6)'
        },
        RiskPriority: {
          'High': 'rgba(244, 67, 54, 0.6)',
          'Medium': 'rgba(255, 152, 0, 0.6)',
          'Low': 'rgba(76, 175, 80, 0.6)'
        }
      }

      // For doughnut charts, use a predefined color palette
      if (chartType === 'doughnut') {
        return [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 206, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
          'rgba(153, 102, 255, 0.8)',
          'rgba(255, 159, 64, 0.8)'
        ]
      }

      // For line charts, use a single color
      if (chartType === 'line') {
        return 'rgba(54, 162, 235, 0.6)'
      }

      // For bar charts, map colors based on labels
      return labels?.map(label => {
        // Determine the category based on chartId
        let category = 'Origin'
        if (chartId.includes('priority')) {
          category = 'RiskPriority'
        } else if (chartId.includes('status')) {
          category = 'Status'
        } else if (chartId.includes('category')) {
          category = 'RiskCategory'
        } else if (chartId.includes('origin')) {
          category = 'Origin'
        }
        
        return colorMaps[category]?.[label] || 'rgba(158, 158, 158, 0.6)'
      }) || []
    },
    getBorderColors(chartType, labels, chartId = '') {
      const colorMaps = {
        Status: {
          'Scheduled': '#FF9800',
          'Approved': '#4CAF50',
          'Rejected': '#F44336',
          'Resolved': '#2196F3'
        },
        Origin: {
          'Manual': '#2196F3',
          'SIEM': '#9C27B0',
          'Audit Finding': '#FFC107',
          'Compliance Gap': '#FF5722',
          'Other': '#795548'
        },
        RiskCategory: {
          'Security': '#F44336',
          'Compliance': '#9C27B0',
          'Operational': '#FF9800',
          'Financial': '#2196F3',
          'Strategic': '#4CAF50',
          'Reputational': '#795548'
        },
        RiskPriority: {
          'High': '#F44336',
          'Medium': '#FF9800',
          'Low': '#4CAF50'
        }
      }

      // For doughnut charts, use a predefined color palette
      if (chartType === 'doughnut') {
        return [
          'rgb(255, 99, 132)',
          'rgb(54, 162, 235)',
          'rgb(255, 206, 86)',
          'rgb(75, 192, 192)',
          'rgb(153, 102, 255)',
          'rgb(255, 159, 64)'
        ]
      }

      // For line charts, use a single color
      if (chartType === 'line') {
        return 'rgb(54, 162, 235)'
      }

      // For bar charts, map colors based on labels
      return labels?.map(label => {
        // Determine the category based on chartId
        let category = 'Origin'
        if (chartId.includes('priority')) {
          category = 'RiskPriority'
        } else if (chartId.includes('status')) {
          category = 'Status'
        } else if (chartId.includes('category')) {
          category = 'RiskCategory'
        } else if (chartId.includes('origin')) {
          category = 'Origin'
        }
        
        return colorMaps[category]?.[label] || '#9E9E9E'
      }) || []
    },
    onFrameworkChange() {
      console.log('🔄 Framework selection changed to:', this.selectedFramework || 'All Frameworks')
      
      if (this.selectedFramework) {
        const selectedFrameworkName = this.frameworks.find(f => f.id == this.selectedFramework)?.name
        console.log('Selected framework name:', selectedFrameworkName)
      } else {
        console.log('Loading data for all frameworks')
      }
      
      this.fetchDashboardData()
    },

    debugFramework() {
      console.log('=== FRAMEWORK DEBUG ===')
      console.log('Current selectedFramework:', this.selectedFramework)
      console.log('Available frameworks:', this.frameworks)
      console.log('localStorage selectedFrameworkId:', localStorage.getItem('selectedFrameworkId'))
      console.log('localStorage frameworkId:', localStorage.getItem('frameworkId'))
      console.log('sessionStorage selectedFrameworkId:', sessionStorage.getItem('selectedFrameworkId'))
      console.log('sessionStorage frameworkId:', sessionStorage.getItem('frameworkId'))
      
      // Test API call
      this.api.incidentService.getSelectedFramework()
        .then(response => {
          console.log('API Response:', response.data)
        })
        .catch(error => {
          console.error('API Error:', error)
        })
      
      // Test setting a framework manually
      if (this.frameworks.length > 0) {
        const firstFramework = this.frameworks[0]
        console.log('Testing with first framework:', firstFramework)
        this.selectedFramework = firstFramework.id
        this.fetchDashboardData()
      }
      
      alert('Framework debug info logged to console. Check browser console for details.')
    },

    refreshData() {
      this.fetchFrameworks()
      this.fetchDashboardData()
      this.fetchRecentIncidents()
    },
    
    clearFilters() {
      this.selectedFramework = ''
      this.selectedTimeRange = 'Last 6 Months'
      this.selectedCategory = 'All Categories'
      this.selectedPriority = 'All Priorities'
      this.fetchDashboardData()
    },
    
    // Download dashboard as PDF
    async downloadDashboardPDF() {
      this.isDownloading = true
      try {
        await this.$nextTick() // Ensure all components are rendered
        
        const dashboardElement = document.querySelector('.dashboard-container')
        if (!dashboardElement) {
          throw new Error('Dashboard element not found')
        }

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
            const clonedDashboard = clonedDoc.querySelector('.dashboard-container')
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
            const chartContainers = clonedDoc.querySelectorAll('.chart-container')
            chartContainers.forEach(container => {
              container.style.display = 'block'
              container.style.visibility = 'visible'
              container.style.opacity = '1'
              container.style.minHeight = '300px'
              container.style.background = '#ffffff'
            })

            // Ensure all chart cards are visible
            const chartCards = clonedDoc.querySelectorAll('.chart-card')
            chartCards.forEach(card => {
              card.style.display = 'flex'
              card.style.visibility = 'visible'
              card.style.opacity = '1'
              card.style.background = '#ffffff'
            })
          }
        })

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
        const filename = `Incident-Dashboard-${timestamp}.pdf`

        // Download the PDF
        pdf.save(filename)

        console.log('PDF downloaded successfully')
      } catch (error) {
        console.error('Error generating PDF:', error)
        alert('Failed to generate PDF. Please try again.')
      } finally {
        this.isDownloading = false
      }
    },
    
    // Navigation function to go back to Incident Management
    goBackToIncident() {
      this.$router.push({ name: 'Incident' })
    },
    
    truncateDescription(text, maxLength) {
      if (!text) return '';
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      
      // Check if it's today
      const today = new Date();
      if (date.toDateString() === today.toDateString()) {
        return 'Today, ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
      }
      
      // Check if it's yesterday
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      if (date.toDateString() === yesterday.toDateString()) {
        return 'Yesterday, ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
      }
      
      // Otherwise return relative time
      const diffTime = Math.abs(today - date);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays < 7) {
        return diffDays + ' days ago';
      } else {
        return date.toLocaleDateString();
      }
    }
  }
}
</script>

<style>
@import './IncidentPerformanceDashboard.css';
</style>

<style scoped>
.data-source-message {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #2563eb;
  font-weight: 500;
}
</style>