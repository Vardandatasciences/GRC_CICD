<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <div class="dashboard-header-left">
        <h1>Compliance Dashboard</h1>
      </div>
      <div class="header-actions">
        <button class="refresh-btn" @click="refreshData">
          <i class="fas fa-sync-alt"></i>
          Refresh
        </button>
        <button 
          class="export-btn" 
          @click="exportDashboardAsPDF" 
          :disabled="isExporting"
          :class="{ 'exporting': isExporting, 'success': exportSuccess }"
          title="Export Dashboard as PDF"
        >
          <i v-if="!isExporting" class="fas fa-download"></i>
          <i v-else class="fas fa-spinner fa-spin"></i>
          {{ isExporting ? 'Exporting...' : 'Export' }}
        </button>
      </div>
    </div>

    <!-- Framework Filter -->
    <div class="framework-filter" style="margin-bottom: 4px;">
      <!-- Single Row: All Four Filters -->
      <div class="filter-row" style="display: flex; align-items: flex-end; gap: 24px; flex-wrap: nowrap; width: 100%;">
        <label style="font-size: 11px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 4px;">Framework Selection:</label>
        <select v-model="selectedFramework" @change="handleFrameworkChange" :disabled="loadingFrameworks || loadingDashboard" :class="{ 'filter-active': selectedFramework, 'filter-loading': loadingDashboard }" style="padding: 12px 32px 12px 14px; border: 2px solid #e2e8f0; border-radius: 8px; background: transparent; color: #374151; font-size: 14px; font-weight: 500; outline: none; transition: all 0.2s ease; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); width: auto; min-width: 150px;">
          <option value="">All Frameworks</option>
          <option v-if="loadingFrameworks" value="" disabled>Loading frameworks...</option>
          <option v-else v-for="framework in filteredFrameworks" :key="framework.id" :value="framework.id">
            {{ framework.name }}
          </option>
        </select>
        <div v-if="loadingDashboard" class="filter-loading-indicator" style="position: absolute; right: 16px; top: 50%; transform: translateY(-50%); color: #4CAF50; font-size: 14px;">
          <i class="fas fa-spinner fa-spin"></i>
        </div>
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

    <!-- Filter Summary -->
    <div v-if="hasActiveFilters" class="filter-summary" style="background: transparent; color: #475569; padding: 16px 20px; border-radius: 12px; margin-bottom: 24px;">
      <div style="display: flex; align-items: center; gap: 12px;">
        <!-- <span style="font-weight: 600; font-size: 14px;">Active Filters:</span> -->
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <span v-if="selectedTimeRange !== 'Last 6 Months'" class="filter-tag" style="background: rgba(76, 175, 80, 0.1); color: #4CAF50; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 500;">
            Time: {{ selectedTimeRange }}
          </span>
          <span v-if="selectedCategory !== 'All Categories'" class="filter-tag" style="background: rgba(76, 175, 80, 0.1); color: #4CAF50; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 500;">
            Category: {{ selectedCategory }}
          </span>
          <span v-if="selectedPriority !== 'All Priorities'" class="filter-tag" style="background: rgba(76, 175, 80, 0.1); color: #4CAF50; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 500;">
            Priority: {{ selectedPriority }}
          </span>
        </div>
      </div>
    </div>

    <!-- Dashboard Content -->
    <div class="dashboard-content">
    <div class="metrics-grid">
      <!-- Approval Rate Card -->
      <div class="metric-card">
        <div class="metric-icon approval-icon">
          <i class="fas fa-check-circle"></i>
        </div>
        <div class="metric-content">
          <h3>Approval Rate</h3>
          <div class="metric-value">
            <span class="percentage">{{ dashboardData.approval_rate }}%</span>
          </div>
          <div class="metric-change">
            Based on {{ dashboardData.total_count }} compliances
          </div>
        </div>
      </div>

      <!-- Active Compliances Card -->
      <div class="metric-card">
        <div class="metric-icon policies-icon">
          <i class="fas fa-file-alt"></i>
        </div>
        <div class="metric-content">
          <h3>Active Compliances</h3>
          <div class="metric-value">
            <span class="number">{{ dashboardData.status_counts.active_compliance || 0 }}</span>
          </div>
          <div class="metric-change">
            Active and Approved
          </div>
        </div>
      </div>

      <!-- Total Findings Card -->
      <div class="metric-card">
        <div class="metric-icon risk-icon">
          <i class="fas fa-list"></i>
        </div>
        <div class="metric-content">
          <h3>Total Findings</h3>
          <div class="metric-value">
            <span class="number">{{ dashboardData.total_findings }}</span>
          </div>
          <div class="metric-change">
            Across all compliances
          </div>
        </div>
      </div>

      <!-- Under Review Card -->
      <div class="metric-card">
        <div class="metric-icon review-icon">
          <i class="fas fa-clock"></i>
        </div>
        <div class="metric-content">
          <h3>Under Review</h3>
          <div class="metric-value">
            <span class="number">{{ dashboardData.status_counts.under_review }}</span>
          </div>
          <div class="metric-change">
            Pending review
          </div>
        </div>
      </div>
    </div>

    <!-- Charts Grid - 2x2 Layout with 5th chart in new row -->
    <div class="charts-grid">
      <!-- Chart 1: Compliance vs Criticality (Bar Chart) -->
      <div class="chart-card">
        <div class="chart-header">
          <h2>Compliance vs Criticality</h2>
          <div class="chart-icon">
            <i class="fas fa-chart-bar"></i>
          </div>
        </div>
        <div class="chart-container">
          <canvas id="criticalityChart"></canvas>
        </div>
      </div>
      
      <!-- Chart 2: Compliance vs Status (Donut Chart) -->
      <div class="chart-card">
        <div class="chart-header">
          <h2>Compliance vs Status</h2>
          <div class="chart-icon">
            <i class="fas fa-chart-pie"></i>
          </div>
        </div>
        <div class="chart-container">
          <canvas id="statusChart"></canvas>
        </div>
      </div>
      
      <!-- Chart 3: Compliance vs Active/Inactive (Bar Chart) -->
      <div class="chart-card">
        <div class="chart-header">
          <h2>Compliance vs Active/Inactive</h2>
          <div class="chart-icon">
            <i class="fas fa-chart-bar"></i>
          </div>
        </div>
        <div class="chart-container">
          <canvas id="activeInactiveChart"></canvas>
        </div>
      </div>
      
      <!-- Chart 4: Compliance vs Manual/Automatic (Donut Chart) -->
      <div class="chart-card">
        <div class="chart-header">
          <h2>Compliance vs Manual/Automatic</h2>
          <div class="chart-icon">
            <i class="fas fa-chart-pie"></i>
          </div>
        </div>
        <div class="chart-container">
          <canvas id="manualAutomaticChart"></canvas>
        </div>
      </div>
    </div>

    <!-- Chart 5: Compliance vs Maturity Level (Bar Chart) - Full Width -->
    <div class="chart-row-single">
      <div class="chart-card">
        <div class="chart-header">
          <h2>Compliance vs Maturity Level</h2>
          <div class="chart-icon">
            <i class="fas fa-chart-bar"></i>
          </div>
        </div>
        <div class="chart-container">
          <canvas id="maturityLevelChart"></canvas>
        </div>
      </div>
    </div>

    <!-- Recent Activity Section -->
    <div class="recent-section">
      <div class="recent-activity">
        <div class="activity-header">
          <h2>Recent Activity</h2>
          <button class="more-options" @click="refreshRecentActivities">
            <i class="fas fa-sync" :class="{ 'fa-spin': loadingActivities }"></i>
          </button>
        </div>
        <div class="activity-list">
          <div v-if="loadingActivities && recentActivities.length === 0" class="activity-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <span>Loading recent activities...</span>
          </div>
          <div v-else-if="!loadingActivities && recentActivities.length === 0" class="activity-empty">
            <i class="fas fa-inbox"></i>
            <span>No recent activities found</span>
          </div>
          <template v-else>
            <div v-for="(activity, index) in recentActivities" :key="index" class="activity-item">
              <div class="activity-icon" :class="activity.type">
                <i :class="activity.icon" class="fontawesome-icon"></i>
                <span class="activity-icon-fallback">{{ getActivityIconFallback(activity.type) }}</span>
              </div>
              <div class="activity-details">
                <h4>{{ activity.title }}</h4>
                <p>{{ activity.description }}</p>
                <span class="activity-time">{{ activity.time }}</span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
    </div> <!-- Close dashboard-content div -->
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
import { mapState, mapActions } from 'vuex'
import '@fortawesome/fontawesome-free/css/all.min.css'
import { complianceService } from '@/services/api'
import complianceDataService from '@/services/complianceService' // NEW: Use cached compliance data
import axios from 'axios'
import { API_ENDPOINTS } from '../../config/api.js'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

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
  name: 'ComplianceDashboard',
  data() {
    return {
      selectedFramework: '',
      selectedTimeRange: 'Last 6 Months',
      selectedCategory: 'All Categories',
      selectedPriority: 'All Priorities',
      frameworks: [],
      loadingFrameworks: false,
      
      // Framework session filtering properties
      sessionFrameworkId: null,
      api: {
        complianceService
      },
      dashboardData: {
        status_counts: {
          approved: 0,
          active: 0,
          under_review: 0
        },
        total_count: 0,
        total_findings: 0,
        approval_rate: 0
      },
      charts: {
        criticalityChart: null,
        statusChart: null,
        activeInactiveChart: null,
        manualAutomaticChart: null,
        maturityLevelChart: null
      },
      chartData: {
        criticality: null,
        status: null,
        activeInactive: null,
        manualAutomatic: null,
        maturityLevel: null
      },
      recentActivities: [],
      loadingActivities: false,
      activityRefreshInterval: null,
      loadingDashboard: false, // Start without loading state
      isExporting: false,
      exportSuccess: false
    }
  },
  computed: {
    // Vuex store computed properties
    ...mapState('framework', {
      storeFrameworkId: state => state.selectedFrameworkId,
      storeFrameworkName: state => state.selectedFrameworkName
    }),
    
    // Framework filtering computed properties
    filteredFrameworks() {
      if (this.sessionFrameworkId) {
        // If there's a session framework ID, show only that framework
        return this.frameworks.filter(fw => fw.id.toString() === this.sessionFrameworkId.toString())
      }
      // If no session framework ID, show all frameworks
      return this.frameworks
    },
    
    hasActiveFilters() {
      return this.selectedFramework || 
             this.selectedTimeRange !== 'Last 6 Months' || 
             this.selectedCategory !== 'All Categories' || 
             this.selectedPriority !== 'All Priorities'
    }
  },
  async mounted() {
    console.log('🚀 ComplianceDashboard mounted - starting instant loading...')
    
    // Check if FontAwesome is loaded (non-blocking)
    this.checkFontAwesome()
    
    // Load framework from Vuex store
    if (this.storeFrameworkId && this.storeFrameworkId !== 'all') {
      this.selectedFramework = this.storeFrameworkId
      console.log('🔄 ComplianceDashboard: Loaded framework from Vuex store:', this.storeFrameworkId)
    }
    
    // Start all data loading immediately without waiting
    console.log('📊 Starting instant data loading...')
    
    // Load all data in parallel including recent activities
    Promise.all([
      this.fetchFrameworks(),
      this.fetchDashboardData(),
      this.fetchRecentActivities() // Load activities with charts
    ]).then(() => {
      // Check for selected framework from session after loading
      this.checkSelectedFrameworkFromSession()
    })
    
    // Auto-refresh activities every 5 minutes
    this.activityRefreshInterval = setInterval(() => {
      this.fetchRecentActivities()
    }, 300000) // 5 minutes
    
    console.log('✅ ComplianceDashboard initialization started instantly!')
  },
  beforeUnmount() {
    this.destroyAllCharts()
    if (this.activityRefreshInterval) {
      clearInterval(this.activityRefreshInterval)
    }
  },
  beforeRouteLeave(to, from, next) {
    this.destroyAllCharts()
    if (this.activityRefreshInterval) {
      clearInterval(this.activityRefreshInterval)
    }
    next()
  },
  watch: {
    // Watch for Vuex store framework changes
    storeFrameworkId(newFrameworkId, oldFrameworkId) {
      // Only update if value actually changed
      if (newFrameworkId === oldFrameworkId) return
      
      console.log('🔄 ComplianceDashboard: Vuex store framework changed to:', newFrameworkId)
      console.log('🔄 ComplianceDashboard: Old framework was:', oldFrameworkId)
      
      // Update local selectedFramework to match store
      if (newFrameworkId === 'all' || !newFrameworkId) {
        this.selectedFramework = ''
      } else {
        this.selectedFramework = newFrameworkId
      }
      
      // Reload dashboard data with new framework
      console.log('🔄 ComplianceDashboard: Fetching data for framework:', this.selectedFramework)
      this.fetchDashboardData()
    }
  },
  methods: {
    ...mapActions('framework', ['setFramework']),
    // FontAwesome check method
    checkFontAwesome() {
      // Add FontAwesome class immediately to prevent blocking
      document.body.classList.add('fontawesome-loaded')
      console.log('✅ FontAwesome class added immediately')
      
      try {
        // Check if FontAwesome is loaded by testing if a FontAwesome icon is rendered
        const testElement = document.createElement('i')
        testElement.className = 'fas fa-check'
        testElement.style.position = 'absolute'
        testElement.style.left = '-9999px'
        testElement.style.visibility = 'hidden'
        document.body.appendChild(testElement)
        
        // Check if the FontAwesome CSS is applied (the icon should have a font-family)
        const computedStyle = window.getComputedStyle(testElement)
        const fontFamily = computedStyle.getPropertyValue('font-family')
        
        // Clean up test element
        document.body.removeChild(testElement)
        
        // If FontAwesome is loaded, confirm it's working
        if (fontFamily && fontFamily.includes('Font Awesome')) {
          console.log('✅ FontAwesome is loaded and working')
        } else {
          console.warn('⚠️ FontAwesome may not be loaded properly, but continuing anyway')
          // Don't try to load fallback since we already added the class
        }
      } catch (error) {
        console.error('Error checking FontAwesome:', error)
        // Continue anyway since we already added the class
      }
    },
    
    loadFontAwesomeFallback() {
      // Check if FontAwesome is already loaded via CDN
      if (!document.querySelector('link[href*="font-awesome"]')) {
        console.log('Loading FontAwesome from CDN as fallback...')
        const link = document.createElement('link')
        link.rel = 'stylesheet'
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css'
        link.onload = () => {
          console.log('✅ FontAwesome loaded from CDN')
          document.body.classList.add('fontawesome-loaded')
        }
        link.onerror = () => {
          console.error('❌ Failed to load FontAwesome from CDN')
          // Add class anyway to prevent blocking
          document.body.classList.add('fontawesome-loaded')
        }
        document.head.appendChild(link)
      } else {
        // FontAwesome link exists, add the class immediately
        document.body.classList.add('fontawesome-loaded')
      }
    },
    
    // Helper method to get fallback icon text for activities
    getActivityIconFallback(type) {
      const fallbackIcons = {
        'approved': '✓',
        'rejected': '✗',
        'created': '+',
        'updated': '✎',
        'deactivation': '⏻',
        'version': '↗',
        'error': '!'
      }
      return fallbackIcons[type] || '•'
    },
    
    // Framework session management methods
    async checkSelectedFrameworkFromSession() {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in ComplianceDashboard...')
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
        console.log('📊 DEBUG: Selected framework response:', response.data)
        
        if (response.data && response.data.success && response.data.frameworkId) {
          const frameworkIdFromSession = response.data.frameworkId
          console.log('✅ DEBUG: Found selected framework in session:', frameworkIdFromSession)
          
          // Store the session framework ID for filtering
          this.sessionFrameworkId = frameworkIdFromSession
          
          // Check if this framework exists in our loaded frameworks
          const frameworkExists = this.frameworks.find(f => f.id.toString() === frameworkIdFromSession.toString())
          
          if (frameworkExists) {
            console.log('✅ DEBUG: Framework exists in loaded frameworks:', frameworkExists.name)
            // Automatically select the framework from session
            this.selectedFramework = frameworkExists.id.toString()
            console.log('✅ DEBUG: Auto-selected framework from session:', this.selectedFramework)
            // Refresh dashboard data with the selected framework
            await this.fetchDashboardData()
          } else {
            console.log('⚠️ DEBUG: Framework from session (ID:', frameworkIdFromSession, ') not found in loaded frameworks')
            console.log('📋 DEBUG: Available frameworks:', this.frameworks.map(f => ({ id: f.id, name: f.name })))
            // Clear the session framework ID since it doesn't exist
            this.sessionFrameworkId = null
          }
        } else {
          console.log('ℹ️ DEBUG: No framework found in session - All Frameworks selected')
          this.sessionFrameworkId = null
          // Ensure selectedFramework is empty for "All Frameworks"
          this.selectedFramework = ''
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework from session:', error)
        this.sessionFrameworkId = null
      }
    },
    
    async saveFrameworkToSession(frameworkId) {
      try {
        console.log('💾 DEBUG: Saving framework to session:', frameworkId)
        const userId = localStorage.getItem('user_id') || 'default_user'
        await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, { 
          frameworkId,
          userId
        })
        console.log('✅ DEBUG: Framework saved to session successfully')
      } catch (error) {
        console.error('❌ DEBUG: Error saving framework to session:', error)
      }
    },
    
    async clearFrameworkFromSession() {
      try {
        console.log('🧹 DEBUG: Clearing framework from session')
        const userId = localStorage.getItem('user_id') || 'default_user'
        await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, { 
          frameworkId: null,
          userId
        })
        console.log('✅ DEBUG: Framework cleared from session successfully')
      } catch (error) {
        console.error('❌ DEBUG: Error clearing framework from session:', error)
      }
    },
    
    async handleFrameworkChange() {
      console.log('🔍 DEBUG: handleFrameworkChange called with:', this.selectedFramework)
      
      // Find the framework name from the frameworks list
      const frameworkName = this.frameworks.find(f => f.id === this.selectedFramework)?.name || 'All Frameworks'
      
      // Update Vuex store (this will also save to backend session)
      await this.setFramework({
        id: this.selectedFramework || 'all',
        name: frameworkName
      })
      
      console.log('✅ DEBUG: Framework saved to Vuex store:', this.selectedFramework)
      
      // Note: Data refresh will be triggered by the watcher
    },
    
    destroyAllCharts() {
      Object.values(this.charts).forEach(chart => {
        if (chart) {
          chart.destroy()
        }
      })
      this.charts = {
        criticalityChart: null,
        statusChart: null,
        activeInactiveChart: null,
        manualAutomaticChart: null,
        maturityLevelChart: null
      }
    },
    
    async fetchFrameworks() {
      try {
        this.loadingFrameworks = true
        console.log('🔍 [ComplianceDashboard] Checking for cached framework data...')
        
        // Check if prefetch was never started (user came directly to this page)
        if (!window.complianceDataFetchPromise && !complianceDataService.hasFrameworksCache()) {
          console.log('🚀 [ComplianceDashboard] Starting prefetch now (user came directly to this page)...')
          window.complianceDataFetchPromise = complianceDataService.fetchAllComplianceData()
        }
        
        // Wait for prefetch if it's running
        if (window.complianceDataFetchPromise) {
          console.log('⏳ [ComplianceDashboard] Waiting for prefetch to complete...')
          try {
            await window.complianceDataFetchPromise
            console.log('✅ [ComplianceDashboard] Prefetch completed')
          } catch (error) {
            console.warn('⚠️ [ComplianceDashboard] Prefetch failed, will fetch directly')
          }
        }
        
        // FIRST: Try to get data from cache
        if (complianceDataService.hasFrameworksCache()) {
          console.log('✅ [ComplianceDashboard] Using cached framework data')
          const cachedFrameworks = complianceDataService.getData('frameworks') || []
          
          this.frameworks = cachedFrameworks.map(framework => ({
            id: framework.FrameworkId || framework.id,
            name: framework.FrameworkName || framework.name || 'Unknown Framework'
          }))
          console.log(`[ComplianceDashboard] Loaded ${this.frameworks.length} frameworks from cache (prefetched on Home page)`)
        } else {
          // FALLBACK: Fetch from API if cache is empty
          console.log('⚠️ [ComplianceDashboard] No cached data found, fetching from API...')
          const response = await this.api.complianceService.getComplianceFrameworks()
          console.log('Frameworks API response:', response.data)
          
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
          
          console.log(`[ComplianceDashboard] Loaded ${this.frameworks.length} frameworks directly from API (cache unavailable)`)
          
          // Update cache so subsequent pages benefit
          complianceDataService.setData('frameworks', frameworksData)
          console.log('ℹ️ [ComplianceDashboard] Cache updated after direct API fetch')
        }
        
        console.log('Processed frameworks:', this.frameworks)
      } catch (error) {
        console.error('Error fetching frameworks:', error)
        this.frameworks = []
      } finally {
        this.loadingFrameworks = false
      }
    },
    
    async fetchRecentActivities() {
      try {
        // Only show loading if we don't have any activities yet
        if (this.recentActivities.length === 0) {
          this.loadingActivities = true
        }
        console.log('Fetching recent activities...')
        
        // Get current user ID for reviewer
        const currentUserId = localStorage.getItem('user_id') || sessionStorage.getItem('userId') || 2
        const reviewerId = parseInt(currentUserId) || 2
        
        // Fetch activities with timeout to prevent hanging
        // Only fetch approvals - frameworks fetch is not needed for activities
        let approvalsResponse = null
        try {
          approvalsResponse = await Promise.race([
            this.api.complianceService.getCompliancePolicyApprovals({ reviewer_id: reviewerId }),
            new Promise((_, reject) => setTimeout(() => reject(new Error('Approvals API timeout')), 10000))
          ])
        } catch (error) {
          console.warn('Error fetching approvals for activities (non-critical):', error)
          // Continue without approvals data - activities will be empty but page won't hang
        }
        
        let activities = []
        
        // Process policy approvals for recent activities
        if (approvalsResponse && approvalsResponse.data && approvalsResponse.data.success && approvalsResponse.data.data) {
          const approvals = approvalsResponse.data.data
          
          // Sort approvals by most recent first
          const sortedApprovals = approvals.sort((a, b) => {
            const dateA = new Date(a.ApprovedDate || a.ExtractedData?.CreatedByDate || '1970-01-01')
            const dateB = new Date(b.ApprovedDate || b.ExtractedData?.CreatedByDate || '1970-01-01')
            return dateB - dateA
          })
          
          // Process different types of activities
          sortedApprovals.slice(0, 10).forEach(approval => {
            const extractedData = approval.ExtractedData || {}
            const complianceTitle = extractedData.ComplianceTitle || extractedData.ComplianceItemDescription || 'Unknown Compliance'
            const createdBy = extractedData.CreatedByName || 'Unknown User'
            const version = extractedData.ComplianceVersion || '1.0'
            
            // Determine activity type based on approval status and data
            if (approval.ApprovedNot === true) {
              // Approved compliance
              activities.push({
                type: 'approved',
                icon: 'fas fa-check-circle',
                title: 'Compliance Approved',
                description: `"${this.truncateText(complianceTitle, 50)}" approved by reviewer`,
                time: this.formatRelativeTime(approval.ApprovedDate),
                metadata: {
                  complianceId: extractedData.compliance_id,
                  version: version,
                  approver: 'Reviewer'
                }
              })
            } else if (approval.ApprovedNot === false) {
              // Rejected compliance
              activities.push({
                type: 'rejected',
                icon: 'fas fa-times-circle',
                title: 'Compliance Rejected',
                description: `"${this.truncateText(complianceTitle, 50)}" needs revision`,
                time: this.formatRelativeTime(approval.ApprovedDate),
                metadata: {
                  complianceId: extractedData.compliance_id,
                  version: version,
                  reviewer: 'Reviewer'
                }
              })
            } else if (approval.ApprovedNot === null) {
              // Check if it's a deactivation request
              if (extractedData.type === 'compliance_deactivation' || extractedData.RequestType === 'Change Status to Inactive') {
                activities.push({
                  type: 'deactivation',
                  icon: 'fas fa-power-off',
                  title: 'Deactivation Request',
                  description: `Deactivation requested for compliance ID ${extractedData.compliance_id}`,
                  time: this.formatRelativeTime(extractedData.CreatedByDate),
                  metadata: {
                    complianceId: extractedData.compliance_id,
                    reason: extractedData.reason || 'No reason provided'
                  }
                })
              } else {
                // Check if it's a new version (higher version number)
                if (parseFloat(version) > 1.0) {
                  activities.push({
                    type: 'version',
                    icon: 'fas fa-code-branch',
                    title: 'New Version Created',
                    description: `Version ${version} of "${this.truncateText(complianceTitle, 40)}" by ${createdBy}`,
                    time: this.formatRelativeTime(extractedData.CreatedByDate),
                    metadata: {
                      complianceId: extractedData.compliance_id,
                      version: version,
                      creator: createdBy
                    }
                  })
                } else {
                  // New compliance under review
                  activities.push({
                    type: 'created',
                    icon: 'fas fa-plus-circle',
                    title: 'New Compliance Created',
                    description: `"${this.truncateText(complianceTitle, 50)}" created by ${createdBy}`,
                    time: this.formatRelativeTime(extractedData.CreatedByDate),
                    metadata: {
                      complianceId: extractedData.compliance_id,
                      version: version,
                      creator: createdBy
                    }
                  })
                }
              }
            }
          })
        }
        
        // Skip the slow nested API calls - they're too slow and not essential
        // The approvals data should be sufficient for recent activities
        // If we need more data, we can add a dedicated API endpoint later
        
        // Sort all activities by time (most recent first) and limit to top 10
        activities.sort((a, b) => {
          const timeA = this.parseRelativeTime(a.time)
          const timeB = this.parseRelativeTime(b.time)
          return timeA - timeB // Sort by actual time difference (smaller = more recent)
        })
        
        // Remove duplicates based on description and limit to latest 3 items
        const uniqueActivities = activities.filter((activity, index, self) => 
          index === self.findIndex(a => a.description === activity.description)
        ).slice(0, 3)
        
        this.recentActivities = uniqueActivities
        console.log(`Loaded ${this.recentActivities.length} recent activities`)
        
        // If no activities found, log a warning but don't show error message
        if (this.recentActivities.length === 0) {
          console.warn('⚠️ No recent compliance activities found. This is normal if there are no recent compliance actions.')
        }
        
      } catch (error) {
        console.error('Error fetching recent activities:', error)
        // Don't set error activity - just leave empty array
        // This prevents showing error message when there are simply no activities
        this.recentActivities = []
      } finally {
        this.loadingActivities = false
      }
    },
    
    truncateText(text, maxLength) {
      if (!text) return 'Unknown'
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
    },
    
    formatRelativeTime(dateString) {
      if (!dateString) return 'Unknown time'
      
      try {
        const date = new Date(dateString)
        const now = new Date()
        const diffInSeconds = Math.floor((now - date) / 1000)
        
        if (diffInSeconds < 60) {
          return 'Just now'
        } else if (diffInSeconds < 3600) {
          const minutes = Math.floor(diffInSeconds / 60)
          return `${minutes} minute${minutes === 1 ? '' : 's'} ago`
        } else if (diffInSeconds < 86400) {
          const hours = Math.floor(diffInSeconds / 3600)
          return `${hours} hour${hours === 1 ? '' : 's'} ago`
        } else if (diffInSeconds < 604800) {
          const days = Math.floor(diffInSeconds / 86400)
          return `${days} day${days === 1 ? '' : 's'} ago`
        } else {
          const weeks = Math.floor(diffInSeconds / 604800)
          return `${weeks} week${weeks === 1 ? '' : 's'} ago`
        }
      } catch (error) {
        console.error('Error formatting date:', error)
        return 'Unknown time'
      }
    },
    
    parseRelativeTime(timeString) {
      // Convert relative time back to seconds for sorting
      if (timeString === 'Just now') return 0
      
      const match = timeString.match(/(\d+)\s+(minute|hour|day|week)s?\s+ago/)
      if (match) {
        const value = parseInt(match[1])
        const unit = match[2]
        
        switch (unit) {
          case 'minute': return value * 60
          case 'hour': return value * 3600
          case 'day': return value * 86400
          case 'week': return value * 604800
          default: return 999999
        }
      }
      
      return 999999 // Unknown time goes to end
    },
    
    refreshRecentActivities() {
      // Don't set loadingActivities = true here to allow background refresh
      // Existing activities will remain visible while new data loads
      this.fetchRecentActivities()
    },

    async fetchDashboardData() {
      try {
        console.log('Starting fetchDashboardData for compliance...')
        console.log('Current filters - Framework:', this.selectedFramework, 'Time:', this.selectedTimeRange, 'Category:', this.selectedCategory, 'Priority:', this.selectedPriority)

        // Fetch dashboard summary data
        let dashboardResponse
        try {
          const dashboardRequest = {}
          
          // Add framework filter if selected
          if (this.selectedFramework && this.selectedFramework !== '') {
            dashboardRequest.framework_id = this.selectedFramework
            console.log('Applying framework filter to dashboard:', this.selectedFramework)
          } else {
            console.log('No framework filter applied')
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
          console.log('Making API call to:', this.api.complianceService.getComplianceDashboard.toString())
          dashboardResponse = await this.api.complianceService.getComplianceDashboard(dashboardRequest)
          console.log('Compliance Dashboard API Response:', dashboardResponse.data)
        } catch (err) {
          console.error('Error fetching dashboard data:', err)
          console.error('Error details:', err.response?.data || err.message)
          throw new Error(`Dashboard fetch failed: ${err.message}`)
        }

        // Fetch data for each chart
        const chartPromises = [
          this.fetchChartData('Criticality', 'bar'),
          this.fetchChartData('Status', 'doughnut'),
          this.fetchChartData('ActiveInactive', 'bar'),
          this.fetchChartData('ManualAutomatic', 'doughnut'),
          this.fetchChartData('MaturityLevel', 'bar')
        ]

        const [criticalityData, statusData, activeInactiveData, manualAutomaticData, maturityLevelData] = await Promise.all(chartPromises)

        if (dashboardResponse.data && dashboardResponse.data.success) {
          const summary = dashboardResponse.data.data?.summary || {}
          console.log('Dashboard summary data:', summary)
          
          this.dashboardData = {
            status_counts: summary.status_counts || {},
            total_count: summary.total_count || 0,
            total_findings: summary.total_findings || 0,
            approval_rate: summary.approval_rate || 0
          }
          
          // Update chart data
          this.chartData = {
            criticality: criticalityData,
            status: statusData,
            activeInactive: activeInactiveData,
            manualAutomatic: manualAutomaticData,
            maturityLevel: maturityLevelData
          }
          
          console.log('Updated chart data:', this.chartData)
          
          // Render charts immediately after data is loaded
          await this.renderChartsAfterDataLoad()
        } else {
          const errorMessage = dashboardResponse.data?.message || 'API request failed'
          console.error('API Error:', errorMessage)
          throw new Error(errorMessage)
        }
      } catch (error) {
        console.error('Error in fetchDashboardData:', error)
        
        // Set default values on error
        this.dashboardData = {
          status_counts: { approved: 0, active: 0, under_review: 0 },
          total_count: 0,
          total_findings: 0,
          approval_rate: 0
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
          criticality: defaultChartData,
          status: defaultChartData,
          activeInactive: defaultChartData,
          manualAutomatic: defaultChartData,
          maturityLevel: defaultChartData
        }
        
        await this.renderChartsAfterDataLoad()
      }
    },
    async fetchChartData(yAxis, chartType) {
      try {
        const requestData = {
          xAxis: 'Compliance',
          yAxis: yAxis
        }
        
        // Add framework filter if selected
        if (this.selectedFramework && this.selectedFramework !== '') {
          requestData.frameworkId = this.selectedFramework
          console.log(`Applying framework filter for ${yAxis} chart:`, this.selectedFramework)
        } else {
          console.log(`No framework filter applied for ${yAxis} chart`)
        }
        
        // Add other filters
        if (this.selectedTimeRange && this.selectedTimeRange !== 'Last 6 Months') {
          requestData.timeRange = this.selectedTimeRange
        }
        
        if (this.selectedCategory && this.selectedCategory !== 'All Categories') {
          requestData.category = this.selectedCategory
        }
        
        if (this.selectedPriority && this.selectedPriority !== 'All Priorities') {
          requestData.priority = this.selectedPriority
        }
        
        console.log(`Fetching ${yAxis} chart data with request:`, requestData)
        console.log('Making analytics API call to:', this.api.complianceService.getComplianceAnalytics.toString())
        const response = await this.api.complianceService.getComplianceAnalytics(requestData)
        
        console.log(`${yAxis} chart response:`, response.data)
        
        if (response.data && response.data.success && response.data.chartData) {
          return response.data.chartData
        } else {
          console.warn(`No data received for ${yAxis} chart`)
          return this.getDefaultChartData(chartType)
        }
      } catch (error) {
        console.error(`Error fetching ${yAxis} chart data:`, error)
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
      
      if (chartType === 'doughnut') {
        defaultData.datasets[0].backgroundColor = [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 206, 86, 0.8)'
        ]
        defaultData.datasets[0].borderColor = [
          'rgb(255, 99, 132)',
          'rgb(54, 162, 235)',
          'rgb(255, 206, 86)'
        ]
      }
      
      return defaultData
    },
    
    async renderChartsAfterDataLoad() {
      console.log('🎨 Rendering charts instantly...')
      
      // Ensure all canvas elements exist
      const chartIds = ['criticalityChart', 'statusChart', 'activeInactiveChart', 'manualAutomaticChart', 'maturityLevelChart']
      const existingCanvases = chartIds.filter(id => document.getElementById(id))
      
      if (existingCanvases.length === chartIds.length) {
        console.log('✅ All canvas elements found, rendering charts instantly...')
        await this.updateAllCharts()
      } else {
        console.log('⏳ Canvas elements not ready, retrying instantly...')
        // Retry immediately without delay
        this.$nextTick(() => {
          this.renderChartsAfterDataLoad()
        })
      }
    },
    
    async updateAllCharts() {
      console.log('🔄 DEBUG: Updating all charts instantly...')
      console.log('📊 DEBUG: Chart data available:', {
        criticality: !!this.chartData.criticality,
        status: !!this.chartData.status,
        activeInactive: !!this.chartData.activeInactive,
        manualAutomatic: !!this.chartData.manualAutomatic,
        maturityLevel: !!this.chartData.maturityLevel
      })
      
      // Check if all canvas elements exist
      const chartIds = ['criticalityChart', 'statusChart', 'activeInactiveChart', 'manualAutomaticChart', 'maturityLevelChart']
      const missingCanvases = chartIds.filter(id => !document.getElementById(id))
      
      if (missingCanvases.length > 0) {
        console.warn('⚠️ DEBUG: Some canvas elements not found:', missingCanvases)
        console.log('🔄 DEBUG: Retrying chart update instantly...')
        // Retry immediately without delay
        this.$nextTick(() => {
          this.updateAllCharts()
        })
        return
      }
      
      console.log('✅ DEBUG: All canvas elements found, proceeding with instant chart updates')
      
      // Update charts with error handling
      try {
        this.updateChart('criticalityChart', 'bar', this.chartData.criticality)
        this.updateChart('statusChart', 'doughnut', this.chartData.status)
        this.updateChart('activeInactiveChart', 'bar', this.chartData.activeInactive)
        this.updateChart('manualAutomaticChart', 'doughnut', this.chartData.manualAutomatic)
        this.updateChart('maturityLevelChart', 'bar', this.chartData.maturityLevel)
        console.log('✅ DEBUG: All charts updated instantly')
      } catch (error) {
        console.error('❌ DEBUG: Error updating charts:', error)
      }
    },
    updateChart(chartId, chartType, chartData) {
      try {
        console.log(`🔄 DEBUG: Updating chart ${chartId} with type ${chartType}`)
        
        // Destroy existing chart if it exists
        if (this.charts[chartId]) {
          this.charts[chartId].destroy()
        }

        // Get the canvas element
        const canvas = document.getElementById(chartId)
        if (!canvas) {
          console.error(`❌ DEBUG: Chart canvas not found: ${chartId}`)
          return
        }
        
        console.log(`✅ DEBUG: Canvas found for ${chartId}:`, canvas)

        // Create the chart configuration with chartId for proper color mapping
        const config = this.createChartConfig(chartType, chartData, chartId)

        // Create new chart instance
        this.charts[chartId] = new ChartJS(canvas, config)
        console.log(`✅ DEBUG: Chart ${chartId} created successfully`)
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

      // Create dataset with proper colors
      const dataset = {
        label: chartData.datasets[0]?.label || `Compliance Data`,
        data: chartData.datasets[0]?.data || [],
        backgroundColor: this.getBackgroundColors(chartType, chartData.labels, chartId),
        borderColor: this.getBorderColors(chartType, chartData.labels, chartId),
        borderWidth: 1
      }

      // Add pie/doughnut specific properties
      if (['pie', 'doughnut'].includes(chartType)) {
        dataset.backgroundColor = this.getBackgroundColors(chartType, chartData.labels, chartId).map(color => 
          color.replace('0.6', '0.8') // Make pie/doughnut colors more opaque
        )
      }

      return {
        type: chartType,
        data: {
          labels: chartData.labels,
          datasets: [dataset]
        },
        options: this.getChartOptions(chartType)
      }
    },
    getChartOptions(chartType) {
      const options = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 800,
          easing: 'easeInOutQuad'
        },
        plugins: {
          legend: {
            display: ['pie', 'doughnut'].includes(chartType),
            position: ['pie', 'doughnut'].includes(chartType) ? 'right' : 'top',
            labels: {
              padding: 20,
              usePointStyle: false,
              font: {
                size: 12
              }
            }
          },
          tooltip: {
            enabled: true,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: 'white',
            bodyColor: 'white',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 1,
            cornerRadius: 6,
            displayColors: true,
            callbacks: {
              label: (context) => {
                if (['pie', 'doughnut'].includes(chartType)) {
                  const label = context.label || ''
                  const value = context.raw || 0
                  const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0)
                  const percentage = ((value / total) * 100).toFixed(1)
                  return `${label}: ${value} (${percentage}%)`
                }
                return `${context.dataset.label}: ${context.raw}`
              }
            }
          }
        },
        layout: {
          padding: {
            top: 10,
            bottom: 10,
            left: 10,
            right: 10
          }
        }
      }

      // Add scales for bar and line charts
      if (['bar', 'line'].includes(chartType)) {
        options.scales = {
          x: {
            grid: {
              display: false
            },
            ticks: {
              font: {
                size: 11
              }
            }
          },
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            },
            ticks: {
              stepSize: 1,
              precision: 0,
              font: {
                size: 11
              }
            }
          }
        }
      }

      // Special options for doughnut charts
      if (chartType === 'doughnut') {
        options.cutout = '60%'
      }

      return options
    },

    getBackgroundColors(chartType, labels, chartId = '') {
      const colorMaps = {
        Criticality: {
          'High': 'rgba(244, 67, 54, 0.6)',
          'Medium': 'rgba(255, 152, 0, 0.6)',
          'Low': 'rgba(76, 175, 80, 0.6)'
        },
        Status: {
          'Approved': 'rgba(76, 175, 80, 0.6)',
          'Under Review': 'rgba(255, 152, 0, 0.6)',
          'Rejected': 'rgba(244, 67, 54, 0.6)',
          'Active': 'rgba(33, 150, 243, 0.6)'
        },
        ActiveInactive: {
          'Active': 'rgba(76, 175, 80, 0.6)',
          'Inactive': 'rgba(244, 67, 54, 0.6)'
        },
        ManualAutomatic: {
          'Manual': 'rgba(33, 150, 243, 0.6)',
          'Automatic': 'rgba(156, 39, 176, 0.6)'
        },
        MaturityLevel: {
          'Initial': 'rgba(244, 67, 54, 0.6)',
          'Developing': 'rgba(255, 152, 0, 0.6)',
          'Defined': 'rgba(255, 235, 59, 0.6)',
          'Managed': 'rgba(76, 175, 80, 0.6)',
          'Optimizing': 'rgba(33, 150, 243, 0.6)'
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

      // Determine the category based on chartId
      let category = 'Criticality'
      if (chartId.includes('status')) {
        category = 'Status'
      } else if (chartId.includes('activeInactive')) {
        category = 'ActiveInactive'
      } else if (chartId.includes('manualAutomatic')) {
        category = 'ManualAutomatic'
      } else if (chartId.includes('maturityLevel')) {
        category = 'MaturityLevel'
      }

      // For bar charts, map colors based on labels
      return labels?.map(label => {
        return colorMaps[category]?.[label] || 'rgba(158, 158, 158, 0.6)'
      }) || []
    },
    getBorderColors(chartType, labels, chartId = '') {
      const colorMaps = {
        Criticality: {
          'High': '#F44336',
          'Medium': '#FF9800',
          'Low': '#4CAF50'
        },
        Status: {
          'Approved': '#4CAF50',
          'Under Review': '#FF9800',
          'Rejected': '#F44336',
          'Active': '#2196F3'
        },
        ActiveInactive: {
          'Active': '#4CAF50',
          'Inactive': '#F44336'
        },
        ManualAutomatic: {
          'Manual': '#2196F3',
          'Automatic': '#9C27B0'
        },
        MaturityLevel: {
          'Initial': '#F44336',
          'Developing': '#FF9800',
          'Defined': '#FFEB3B',
          'Managed': '#4CAF50',
          'Optimizing': '#2196F3'
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

      // Determine the category based on chartId
      let category = 'Criticality'
      if (chartId.includes('status')) {
        category = 'Status'
      } else if (chartId.includes('activeInactive')) {
        category = 'ActiveInactive'
      } else if (chartId.includes('manualAutomatic')) {
        category = 'ManualAutomatic'
      } else if (chartId.includes('maturityLevel')) {
        category = 'MaturityLevel'
      }

      // For bar charts, map colors based on labels
      return labels?.map(label => {
        return colorMaps[category]?.[label] || '#9E9E9E'
      }) || []
    },
    async refreshData() {
      console.log('🔄 Manual refresh triggered')
      try {
        // Fetch fresh data in parallel for faster loading
        await Promise.all([
          this.fetchFrameworks(),
          this.fetchDashboardData()
        ])
        this.fetchRecentActivities()
        
        console.log('✅ Manual refresh completed successfully')
      } catch (error) {
        console.error('❌ Error during manual refresh:', error)
      }
    },
    
    async clearFilters() {
      this.selectedFramework = ''
      this.selectedTimeRange = 'Last 6 Months'
      this.selectedCategory = 'All Categories'
      this.selectedPriority = 'All Priorities'
      
      // Clear session framework ID when clearing filters
      this.sessionFrameworkId = null
      await this.clearFrameworkFromSession()
      
      this.fetchDashboardData()
    },
    
    // Navigation function to go back to AuditManagementView
    goBackToAuditManagement() {
      this.$router.push({ name: 'AuditManagement' })
    },
    
    // Helper method to get framework name by ID
    getFrameworkName(frameworkId) {
      const framework = this.frameworks.find(f => f.id == frameworkId)
      return framework ? framework.name : 'Unknown Framework'
    },

    // Export dashboard as PDF
    async exportDashboardAsPDF() {
      this.isExporting = true
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
        const filename = `Compliance-Dashboard-${timestamp}.pdf`

        // Download the PDF
        pdf.save(filename)

        console.log('PDF downloaded successfully')
        
        // Show success feedback
        this.exportSuccess = true
        setTimeout(() => {
          this.exportSuccess = false
        }, 2000)
      } catch (error) {
        console.error('Error generating PDF:', error)
        alert('Failed to generate PDF. Please try again.')
      } finally {
        this.isExporting = false
      }
    }
  }
}
</script>

<style>
@import './ComplianceDashboard.css';
</style> 