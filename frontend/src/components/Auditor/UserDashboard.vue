<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <div class="dashboard-header-left">
        <button class="auditor-dashboard-back-btn" @click="goBackToAuditorDashboard" title="Back to Auditor Dashboard">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h1>Auditor Dashboard</h1>
      </div>
      <div class="header-actions">
        <button class="refresh-btn" @click="refreshData">
          <i class="fas fa-sync-alt"></i>
          Refresh
        </button>
        <button 
          class="export-btn" 
          @click="downloadDashboardPDF" 
          :disabled="isDownloading"
          :class="{ 'exporting': isDownloading, 'success': exportSuccess }"
          title="Export Dashboard as PDF"
        >
          <i v-if="!isDownloading" class="fas fa-download"></i>
          <i v-else class="fas fa-spinner fa-spin"></i>
          {{ isDownloading ? 'Exporting...' : 'Export' }}
        </button>
      </div>
    </div>
    
    <!-- Performance Summary Cards -->


    <!-- Filter Dropdowns -->
    <div class="filter-dropdowns">
      <div class="filter-dropdown">
        <label class="filter-label">FRAMEWORK:</label>
        <select v-model="selectedFramework" @change="onFrameworkChange" class="dropdown-select">
          <option value="all">All Frameworks</option>
          <option v-for="framework in frameworks" :key="framework.id" :value="framework.id">
            {{ framework.name || framework.framework_name }}
          </option>
        </select>
      </div>
      
      <div class="filter-dropdown">
        <label class="filter-label">POLICY:</label>
        <select v-model="selectedPolicy" @change="onPolicyChange" class="dropdown-select">
          <option value="all">All Policies</option>
          <option v-for="policy in policies" :key="policy.id" :value="policy.id">
            {{ policy.name || policy.policy_name }}
          </option>
        </select>
      </div>
    </div>
                
    <!-- Charts Grid -->
    <div class="charts-grid">
      <!-- Category Distribution Line Chart -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">Category Distribution</h3>
          <div class="chart-icon">
            <i class="fas fa-chart-line"></i>
          </div>
        </div>
        <div class="chart-container">
          <div v-if="isLoading" class="chart-loading">
            <div class="spinner"></div>
            <span>Loading...</span>
          </div>
          <div v-else-if="error" class="chart-error">
            <i class="fas fa-exclamation-triangle"></i>
            <span>{{ error }}</span>
          </div>
          <div v-else>
            <LineChart :data="categoryData" :options="lineChartOptions" />
          </div>
                </div>
              </div>
              
      <!-- Status Distribution Donut Chart -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">Status Distribution</h3>
          <div class="chart-icon">
            <i class="fas fa-dot-circle"></i>
              </div>
        </div>
        <div class="chart-container">
          <div v-if="isLoading" class="chart-loading">
            <div class="spinner"></div>
            <span>Loading...</span>
          </div>
          <div v-else-if="error" class="chart-error">
            <i class="fas fa-exclamation-triangle"></i>
            <span>{{ error }}</span>
          </div>
          <div v-else>
            <Doughnut :data="statusData" :options="donutChartOptions" class="donut-chart" />
          </div>
        </div>
      </div>

      <!-- Completion Rate Bar Chart -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">Completion Rate</h3>
          <div class="chart-icon">
            <i class="fas fa-chart-bar"></i>
            </div>
          </div>
          <div class="chart-container">
            <div v-if="isLoading" class="chart-loading">
            <div class="spinner"></div>
            <span>Loading...</span>
            </div>
          <div v-else-if="error" class="chart-error">
            <i class="fas fa-exclamation-triangle"></i>
            <span>{{ error }}</span>
          </div>
          <div v-else>
            <Bar :data="completionData" :options="barChartOptions" />
          </div>
        </div>
      </div>

      <!-- Findings Distribution Horizontal Bar Chart -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">Findings Distribution</h3>
          <div class="chart-icon">
            <i class="fas fa-chart-bar"></i>
          </div>
        </div>
        <div class="chart-container">
          <div v-if="isLoading" class="chart-loading">
            <div class="spinner"></div>
            <span>Loading...</span>
          </div>
          <div v-else-if="error" class="chart-error">
            <i class="fas fa-exclamation-triangle"></i>
            <span>{{ error }}</span>
          </div>
          <div v-else>
            <Bar :data="findingsData" :options="horizontalBarChartOptions" />
          </div>
        </div>
      </div>

      <!-- Compliance Trend Line Chart -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">Compliance Trend</h3>
          <div class="chart-icon">
            <i class="fas fa-chart-line"></i>
          </div>
        </div>
        <div class="chart-container">
          <div v-if="isLoading" class="chart-loading">
            <div class="spinner"></div>
            <span>Loading...</span>
          </div>
          <div v-else-if="error" class="chart-error">
            <i class="fas fa-exclamation-triangle"></i>
            <span>{{ error }}</span>
          </div>
          <div v-else>
            <LineChart :data="complianceTrendData" :options="lineChartOptions" />
          </div>
        </div>
      </div>

      <!-- Department Performance Bar Chart -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">Department Performance</h3>
          <div class="chart-icon">
            <i class="fas fa-chart-bar"></i>
          </div>
        </div>
        <div class="chart-container">
          <div v-if="isLoading" class="chart-loading">
            <div class="spinner"></div>
            <span>Loading...</span>
          </div>
          <div v-else-if="error" class="chart-error">
            <i class="fas fa-exclamation-triangle"></i>
            <span>{{ error }}</span>
          </div>
          <div v-else>
            <Bar :data="departmentData" :options="barChartOptions" />
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Activity Section -->
    <div class="recent-activity-section">
        <div class="activity-card">
          <div class="activity-header">
            <h2>Recent Activity</h2>
            <button class="more-options" @click="fetchRecentActivities">
              <i class="fas fa-sync"></i>
            </button>
          </div>
          <div v-if="isLoadingActivities && isEmpty(recentActivities)" class="activity-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <span>Loading activities...</span>
          </div>
          <div v-else-if="isEmpty(filteredActivities)" class="activity-empty">
            <p>No recent activities found</p>
          </div>
          <div v-else class="activity-list">
            <div 
              v-for="(activity, index) in filteredActivities" 
              :key="index" 
              class="activity-item"
            >
              <div :class="['activity-icon', getActivityIconClass(activity.type || 'completed')]">
                <i :class="getActivityIcon(activity.type || 'completed')"></i>
              </div>
              <div class="activity-content">
                <div class="activity-title">{{ activity.title || 'Activity' }}</div>
                <div class="activity-desc">{{ activity.description || 'No description available' }}</div>
                <div class="activity-time">{{ activity.time_ago || 'Recently' }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, watch, onMounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { Chart, ArcElement, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from 'chart.js'
import { Doughnut, Bar, Line } from 'vue-chartjs'
import '@fortawesome/fontawesome-free/css/all.min.css'
import axios from 'axios'
import { AccessUtils } from '@/utils/accessUtils'
import { API_ENDPOINTS } from '../../config/api.js'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

Chart.register(ArcElement, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

export default {
  name: 'AuditorDashboard',
  components: {
    Doughnut,
    Bar,
    LineChart: Line
  },
  setup() {
    const router = useRouter()
    const store = useStore()
    // Loading state
    const isLoading = ref(false)
    const isLoadingActivities = ref(false)
    const isDownloading = ref(false)
    const error = ref(null)

    // Filter data
    const frameworks = ref([])
    const policies = ref([])
    const selectedFramework = ref('all')
    const selectedPolicy = ref('all')

    // Audit Completion Rate data
    const auditCompletionData = reactive({
      current_month_rate: 0,
      previous_month_rate: 0,
      change_in_rate: 0,
      is_positive_change: true
    })

    // Total Audits data
    const totalAuditsData = reactive({
      total_current_month: 0,
      total_previous_month: 0,
      change_in_total: 0,
      is_positive_change: true
    })

    // Open Audits data
    const openAuditsData = reactive({
      open_this_week: 0,
      open_last_week: 0,
      change_in_open: 0,
      percent_change: 0,
      is_improvement: true
    })

    // Completed Audits data
    const completedAuditsData = reactive({
      this_week_count: 0,
      last_week_count: 0,
      change_in_completed: 0,
      percent_change: 0,
      is_improvement: true
    })

    // Chart Data Objects
    const categoryData = reactive({
      labels: ['Information Security', 'Data Protection', 'Risk Assessment', 'Access Control', 'Change Management'],
      datasets: [{
        label: 'Category Distribution',
        data: [86, 92, 78, 84, 73],
        fill: false,
        borderColor: '#4f6cff',
        backgroundColor: 'rgba(79, 108, 255, 0.1)',
        tension: 0.4,
        pointBackgroundColor: '#4f6cff',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    })

    const statusData = reactive({
      labels: ['Completed', 'In Progress', 'Yet To Start', 'On Hold'],
      datasets: [{
        data: [53, 32, 15, 8],
        backgroundColor: ['#4ade80', '#fbbf24', '#f87171', '#8b5cf6'],
        borderWidth: 0,
        hoverOffset: 5
      }]
    })

    const completionData = reactive({
      labels: ['ISO 27001', 'NIST 800-53', 'GDPR', 'PCI DSS', 'HIPAA'],
      datasets: [{
        label: 'Completion Rate (%)',
        data: [85, 78, 92, 88, 76],
        backgroundColor: ['#4ade80', '#60a5fa', '#fbbf24', '#f87171', '#8b5cf6'],
        borderColor: ['#4ade80', '#60a5fa', '#fbbf24', '#f87171', '#8b5cf6'],
        borderWidth: 1,
        borderRadius: 4
      }]
    })

    const findingsData = reactive({
      labels: ['Critical', 'High', 'Medium', 'Low', 'Info'],
      datasets: [{
        label: 'Findings Count',
        data: [5, 12, 25, 18, 8],
        backgroundColor: ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6'],
        borderColor: ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6'],
        borderWidth: 1,
        borderRadius: 6,
        barPercentage: 0.5,
        categoryPercentage: 0.7
      }]
    })

    const complianceTrendData = reactive({
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
      datasets: [{
        label: 'Compliance Rate (%)',
        data: [92, 90, 88, 86, 89, 91, 93],
        fill: false,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        pointBackgroundColor: '#10b981',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    })

    const departmentData = reactive({
      labels: ['IT', 'HR', 'Finance', 'Operations', 'Legal'],
      datasets: [{
        label: 'Audit Score',
        data: [88, 75, 82, 79, 91],
        backgroundColor: ['#4f6cff', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'],
        borderColor: ['#4f6cff', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'],
        borderWidth: 1,
        borderRadius: 4
      }]
    })

    // Recent activities data
    const recentActivities = ref([])

    // Fetch Audit Completion Rate data
    const fetchAuditCompletionRate = async () => {
      try {
        const params = new URLSearchParams()
        if (selectedFramework.value && selectedFramework.value !== 'all') {
          params.append('framework_id', selectedFramework.value)
        }
        if (selectedPolicy.value && selectedPolicy.value !== 'all') {
          params.append('policy_id', selectedPolicy.value)
        }
        
        const url = params.toString() ? `${API_ENDPOINTS.AUDIT_COMPLETION_RATE}?${params}` : API_ENDPOINTS.AUDIT_COMPLETION_RATE
        const response = await axios.get(url)
        if (response.data) {
          auditCompletionData.current_month_rate = response.data.current_month_rate
          auditCompletionData.previous_month_rate = response.data.previous_month_rate
          auditCompletionData.change_in_rate = response.data.change_in_rate
          auditCompletionData.is_positive_change = response.data.is_positive_change
        }
      } catch (error) {
        console.error('Error fetching audit completion rate:', error)
        if (AccessUtils.handleApiError(error, 'audit completion rate access')) {
          return
        }
      }
    }

    // Fetch Total Audits data
    const fetchTotalAudits = async () => {
      try {
        const params = new URLSearchParams()
        if (selectedFramework.value && selectedFramework.value !== 'all') {
          params.append('framework_id', selectedFramework.value)
        }
        if (selectedPolicy.value && selectedPolicy.value !== 'all') {
          params.append('policy_id', selectedPolicy.value)
        }
        
        const url = params.toString() ? `${API_ENDPOINTS.AUDIT_TOTAL_AUDITS}?${params}` : API_ENDPOINTS.AUDIT_TOTAL_AUDITS
        const response = await axios.get(url)
        if (response.data) {
          totalAuditsData.total_current_month = response.data.total_current_month
          totalAuditsData.total_previous_month = response.data.total_previous_month
          totalAuditsData.change_in_total = response.data.change_in_total
          totalAuditsData.is_positive_change = response.data.is_positive_change
        }
      } catch (error) {
        console.error('Error fetching total audits:', error)
        if (AccessUtils.handleApiError(error, 'audit total audits access')) {
          return
        }
      }
    }

    // Fetch Open Audits data
    const fetchOpenAudits = async () => {
      try {
        const params = new URLSearchParams()
        if (selectedFramework.value && selectedFramework.value !== 'all') {
          params.append('framework_id', selectedFramework.value)
        }
        if (selectedPolicy.value && selectedPolicy.value !== 'all') {
          params.append('policy_id', selectedPolicy.value)
        }
        
        const url = params.toString() ? `${API_ENDPOINTS.AUDIT_OPEN_AUDITS}?${params}` : API_ENDPOINTS.AUDIT_OPEN_AUDITS
        const response = await axios.get(url)
        if (response.data) {
          openAuditsData.open_this_week = response.data.open_this_week
          openAuditsData.open_last_week = response.data.open_last_week
          openAuditsData.change_in_open = response.data.change_in_open
          openAuditsData.percent_change = response.data.percent_change
          openAuditsData.is_improvement = response.data.is_improvement
        }
      } catch (error) {
        console.error('Error fetching open audits:', error)
        if (AccessUtils.handleApiError(error, 'audit open audits access')) {
          return
        }
      }
    }

    // Fetch Completed Audits data
    const fetchCompletedAudits = async () => {
      try {
        const params = new URLSearchParams()
        if (selectedFramework.value && selectedFramework.value !== 'all') {
          params.append('framework_id', selectedFramework.value)
        }
        if (selectedPolicy.value && selectedPolicy.value !== 'all') {
          params.append('policy_id', selectedPolicy.value)
        }
        
        const url = params.toString() ? `${API_ENDPOINTS.AUDIT_COMPLETED_AUDITS}?${params}` : API_ENDPOINTS.AUDIT_COMPLETED_AUDITS
        const response = await axios.get(url)
        if (response.data) {
          completedAuditsData.this_week_count = response.data.this_week_count
          completedAuditsData.last_week_count = response.data.last_week_count
          completedAuditsData.change_in_completed = response.data.change_in_completed
          completedAuditsData.percent_change = response.data.percent_change
          completedAuditsData.is_improvement = response.data.is_improvement
        }
      } catch (error) {
        console.error('Error fetching completed audits:', error)
        if (AccessUtils.handleApiError(error, 'audit completed audits access')) {
          return
        }
      }
    }

    // Fetch frameworks for dropdown
    const fetchFrameworks = async () => {
      try {
        console.log('Fetching frameworks...')
        const response = await axios.get(API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_FRAMEWORKS)
        console.log('Frameworks response:', response.data)
        if (response.data && Array.isArray(response.data)) {
          frameworks.value = response.data
          console.log('Frameworks loaded:', frameworks.value)
          return true
        } else {
          frameworks.value = []
          console.log('No frameworks data or invalid format')
          return false
        }
      } catch (error) {
        console.error('Error fetching frameworks:', error)
        // Add fallback data for testing
        frameworks.value = [
          { id: 1, name: 'ISO 27001', framework_name: 'ISO 27001' },
          { id: 2, name: 'NIST 800-53', framework_name: 'NIST 800-53' },
          { id: 3, name: 'GDPR', framework_name: 'GDPR' },
          { id: 4, name: 'PCI DSS', framework_name: 'PCI DSS' },
          { id: 5, name: 'HIPAA', framework_name: 'HIPAA' }
        ]
        console.log('Using fallback frameworks data')
        return true
      }
    }

    // Check for selected framework from session and set it as default
    const checkSelectedFrameworkFromSession = async () => {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in Auditor Dashboard...')
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
        console.log('📊 DEBUG: Selected framework response:', response.data)
        
        if (response.data && response.data.success) {
          // Check if a framework is selected (not null)
          if (response.data.frameworkId) {
            const sessionFrameworkId = response.data.frameworkId
            console.log('✅ DEBUG: Found selected framework in session:', sessionFrameworkId)
            
            // Check if this framework exists in our loaded frameworks
            const frameworkExists = frameworks.value.find(f => 
              f.id == sessionFrameworkId || f.framework_id == sessionFrameworkId
            )
            
            if (frameworkExists) {
              selectedFramework.value = frameworkExists.id || frameworkExists.framework_id
              console.log('✅ DEBUG: Set framework filter from session:', frameworkExists.name || frameworkExists.framework_name)
              console.log('🔍 DEBUG: Framework ID being used:', selectedFramework.value)
              console.log('🔍 DEBUG: Framework object:', frameworkExists)
              
              // Fetch policies for this framework and update all charts
              await fetchPolicies(selectedFramework.value)
              await updateAllCharts()
            } else {
              console.log('⚠️ DEBUG: Framework from session not found in available frameworks')
              console.log('🔍 DEBUG: Session framework ID:', sessionFrameworkId)
              console.log('🔍 DEBUG: Available frameworks:', frameworks.value.map(f => ({ id: f.id, framework_id: f.framework_id, name: f.name, framework_name: f.framework_name })))
            }
          } else {
            // "All Frameworks" is selected (frameworkId is null)
            console.log('ℹ️ DEBUG: No framework selected in session (All Frameworks selected)')
            console.log('🌐 DEBUG: Setting framework filter to "all"')
            selectedFramework.value = 'all'
          }
        } else {
          console.log('ℹ️ DEBUG: No framework found in session')
          selectedFramework.value = 'all'
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework from session:', error)
        // Default to 'all' on error
        selectedFramework.value = 'all'
      }
    }

    // Fetch policies for selected framework
    const fetchPolicies = async (frameworkId) => {
      try {
        console.log('Fetching policies for framework:', frameworkId)
        const response = await axios.get(API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_POLICIES, {
          params: { framework_id: frameworkId }
        })
        console.log('Policies response:', response.data)
        if (response.data && Array.isArray(response.data)) {
          policies.value = response.data
          console.log('Policies loaded:', policies.value)
        } else {
          policies.value = []
          console.log('No policies data or invalid format')
        }
      } catch (error) {
        console.error('Error fetching policies:', error)
        // Add fallback data for testing
        policies.value = [
          { id: 1, name: 'Information Security Policy', policy_name: 'Information Security Policy' },
          { id: 2, name: 'Incident Response Policy', policy_name: 'Incident Response Policy' },
          { id: 3, name: 'Access Control Policy', policy_name: 'Access Control Policy' },
          { id: 4, name: 'Data Protection Policy', policy_name: 'Data Protection Policy' },
          { id: 5, name: 'Risk Management Policy', policy_name: 'Risk Management Policy' }
        ]
        console.log('Using fallback policies data')
      }
    }

    // Handle framework selection
    const onFrameworkChange = async () => {
      console.log('🔍 DEBUG: Framework changed to:', selectedFramework.value)
      console.log('🔍 DEBUG: Available frameworks:', frameworks.value.map(f => ({ id: f.id, framework_id: f.framework_id, name: f.name, framework_name: f.framework_name })))
      
      // Find the framework name from the frameworks list
      const frameworkName = frameworks.value.find(f => f.id === selectedFramework.value)?.name || 
                           frameworks.value.find(f => f.framework_id === selectedFramework.value)?.framework_name || 
                           'All Frameworks'
      
      // Update Vuex store (this will also save to backend session)
      await store.dispatch('framework/setFramework', {
        id: selectedFramework.value !== 'all' ? selectedFramework.value : 'all',
        name: frameworkName
      })
      
      console.log('✅ DEBUG: Framework saved to Vuex store in Auditor Dashboard:', selectedFramework.value)
      
      selectedPolicy.value = 'all'
      
      if (selectedFramework.value && selectedFramework.value !== 'all') {
        await fetchPolicies(selectedFramework.value)
        } else {
        policies.value = []
      }
      
      console.log('🔄 DEBUG: Updating all charts with framework:', selectedFramework.value)
      updateAllCharts()
    }

    // Handle policy selection
    const onPolicyChange = () => {
      console.log('Policy changed to:', selectedPolicy.value)
      updateAllCharts()
    }

    // Update all charts with current filters
    const updateAllCharts = async () => {
      try {
        console.log('🔄 DEBUG: Starting to update all charts...')
        console.log('🔍 DEBUG: Current framework:', selectedFramework.value)
        console.log('🔍 DEBUG: Current policy:', selectedPolicy.value)
        
      isLoading.value = true
      
        // Update Category Chart
        console.log('📊 DEBUG: Updating category chart...')
        await updateCategoryChart()
        
        // Update Status Chart
        console.log('📊 DEBUG: Updating status chart...')
        await updateStatusChart()
        
        // Update Completion Chart
        console.log('📊 DEBUG: Updating completion chart...')
        await updateCompletionChart()
        
        // Update Findings Chart
        console.log('📊 DEBUG: Updating findings chart...')
        await updateFindingsChart()
        
        // Update Compliance Trend Chart
        console.log('📊 DEBUG: Updating compliance trend chart...')
        await updateComplianceTrendChart()
        
        // Update Department Chart
        console.log('📊 DEBUG: Updating department chart...')
        await updateDepartmentChart()
        
        console.log('✅ DEBUG: All charts updated successfully')
        
      } catch (err) {
        console.error('❌ DEBUG: Error updating charts:', err)
        error.value = 'Failed to update charts'
      } finally {
        isLoading.value = false
      }
    }

    // Update Category Chart
    const updateCategoryChart = async () => {
      try {
        console.log('🔍 DEBUG: Updating category chart with framework:', selectedFramework.value)
        
        // Use actual API call with framework filter
        const params = new URLSearchParams()
        if (selectedFramework.value && selectedFramework.value !== 'all') {
          params.append('framework_id', selectedFramework.value)
        }
        if (selectedPolicy.value && selectedPolicy.value !== 'all') {
          params.append('policy_id', selectedPolicy.value)
        }
        
        const url = params.toString() ? `${API_ENDPOINTS.AUDIT_CATEGORY_DISTRIBUTION}?${params}` : API_ENDPOINTS.AUDIT_CATEGORY_DISTRIBUTION
        console.log('📡 DEBUG: Category chart API URL:', url)
        
        const response = await axios.get(url)
        console.log('📊 DEBUG: Category chart response:', response.data)
        
        if (response.data && response.data.categories) {
          categoryData.labels = response.data.categories.map(cat => cat.name)
          categoryData.datasets[0].data = response.data.categories.map(cat => cat.count)
          console.log('✅ DEBUG: Category chart updated with real data')
        } else {
          // Fallback to mock data if API fails
          console.log('⚠️ DEBUG: Using fallback mock data for category chart')
        const mockData = {
          'all': [86, 92, 78, 84, 73],
            '353': [90, 95, 82, 88, 78], // Global Reporting Initiative (GRI) Standards
            'default': [86, 92, 78, 84, 73]
          }
        const data = mockData[selectedFramework.value] || mockData['all']
        categoryData.datasets[0].data = data
          console.log('📊 DEBUG: Category chart updated with mock data:', data)
        }
        
      } catch (err) {
        console.error('❌ DEBUG: Error updating category chart:', err)
        // Fallback to mock data on error
        const mockData = {
          'all': [86, 92, 78, 84, 73],
          '353': [90, 95, 82, 88, 78], // Global Reporting Initiative (GRI) Standards
          'default': [86, 92, 78, 84, 73]
        }
        const data = mockData[selectedFramework.value] || mockData['all']
        categoryData.datasets[0].data = data
        console.log('📊 DEBUG: Category chart updated with error fallback data:', data)
      }
    }

    // Update Status Chart
    const updateStatusChart = async () => {
      try {
        console.log('🔍 DEBUG: Updating status chart with framework:', selectedFramework.value)
        
        // Use actual API call with framework filter
        const params = new URLSearchParams()
        if (selectedFramework.value && selectedFramework.value !== 'all') {
          params.append('framework_id', selectedFramework.value)
        }
        if (selectedPolicy.value && selectedPolicy.value !== 'all') {
          params.append('policy_id', selectedPolicy.value)
        }
        
        const url = params.toString() ? `${API_ENDPOINTS.AUDIT_STATUS_DISTRIBUTION}?${params}` : API_ENDPOINTS.AUDIT_STATUS_DISTRIBUTION
        console.log('📡 DEBUG: Status chart API URL:', url)
        
        const response = await axios.get(url)
        console.log('📊 DEBUG: Status chart response:', response.data)
        
        if (response.data && response.data.statuses) {
          statusData.datasets[0].data = response.data.statuses.map(status => status.count)
          console.log('✅ DEBUG: Status chart updated with real data')
        } else {
          // Fallback to mock data if API fails
          console.log('⚠️ DEBUG: Using fallback mock data for status chart')
        const mockData = {
          'all': [53, 32, 15, 8],
            '353': [60, 25, 12, 3], // Global Reporting Initiative (GRI) Standards
            'default': [53, 32, 15, 8]
          }
        const data = mockData[selectedFramework.value] || mockData['all']
        statusData.datasets[0].data = data
          console.log('📊 DEBUG: Status chart updated with mock data:', data)
        }
        
      } catch (err) {
        console.error('❌ DEBUG: Error updating status chart:', err)
        // Fallback to mock data on error
        const mockData = {
          'all': [53, 32, 15, 8],
          '353': [60, 25, 12, 3], // Global Reporting Initiative (GRI) Standards
          'default': [53, 32, 15, 8]
        }
        const data = mockData[selectedFramework.value] || mockData['all']
        statusData.datasets[0].data = data
        console.log('📊 DEBUG: Status chart updated with error fallback data:', data)
      }
    }

    // Update Completion Chart
    const updateCompletionChart = async () => {
      try {
        console.log('🔍 DEBUG: Updating completion chart with framework:', selectedFramework.value)
        
        // Simulate API call with filters
        const mockData = {
          'all': [85, 78, 92, 88, 76],
          '353': [88, 82, 95, 90, 80], // Global Reporting Initiative (GRI) Standards
          'default': [85, 78, 92, 88, 76]
        }
        
        const data = mockData[selectedFramework.value] || mockData['all']
        completionData.datasets[0].data = data
        console.log('📊 DEBUG: Completion chart updated with data:', data)
        
      } catch (err) {
        console.error('❌ DEBUG: Error updating completion chart:', err)
      }
    }

    // Update Findings Chart
    const updateFindingsChart = async () => {
      try {
        console.log('🔍 DEBUG: Updating findings chart with framework:', selectedFramework.value)
        
        // Simulate API call with filters
        const mockData = {
          'all': [5, 12, 25, 18, 8],
          '353': [3, 8, 20, 15, 6], // Global Reporting Initiative (GRI) Standards
          'default': [5, 12, 25, 18, 8]
        }
        
        const data = mockData[selectedFramework.value] || mockData['all']
        findingsData.datasets[0].data = data
        console.log('📊 DEBUG: Findings chart updated with data:', data)
        
      } catch (err) {
        console.error('❌ DEBUG: Error updating findings chart:', err)
      }
    }

    // Update Compliance Trend Chart
    const updateComplianceTrendChart = async () => {
      try {
        console.log('🔍 DEBUG: Updating compliance trend chart with framework:', selectedFramework.value)
        
        // Simulate API call with filters
        const mockData = {
          'all': [92, 90, 88, 86, 89, 91, 93],
          '353': [94, 92, 90, 88, 91, 93, 95], // Global Reporting Initiative (GRI) Standards
          'default': [92, 90, 88, 86, 89, 91, 93]
        }
        
        const data = mockData[selectedFramework.value] || mockData['all']
        complianceTrendData.datasets[0].data = data
        console.log('📊 DEBUG: Compliance trend chart updated with data:', data)
        
      } catch (err) {
        console.error('❌ DEBUG: Error updating compliance trend chart:', err)
      }
    }

    // Update Department Chart
    const updateDepartmentChart = async () => {
      try {
        console.log('🔍 DEBUG: Updating department chart with framework:', selectedFramework.value)
        
        // Simulate API call with filters
        const mockData = {
          'all': [88, 75, 82, 79, 91],
          '353': [90, 78, 85, 82, 93], // Global Reporting Initiative (GRI) Standards
          'default': [88, 75, 82, 79, 91]
        }
        
        const data = mockData[selectedFramework.value] || mockData['all']
        departmentData.datasets[0].data = data
        console.log('📊 DEBUG: Department chart updated with data:', data)
        
      } catch (err) {
        console.error('❌ DEBUG: Error updating department chart:', err)
      }
    }

    // Fetch recent activities
    const fetchRecentActivities = async () => {
      isLoadingActivities.value = true
      try {
        const params = new URLSearchParams()
        if (selectedFramework.value && selectedFramework.value !== 'all') {
          params.append('framework_id', selectedFramework.value)
        }
        if (selectedPolicy.value && selectedPolicy.value !== 'all') {
          params.append('policy_id', selectedPolicy.value)
        }
        
        const url = params.toString() ? `${API_ENDPOINTS.AUDIT_RECENT_ACTIVITIES}?${params}` : API_ENDPOINTS.AUDIT_RECENT_ACTIVITIES
        const response = await axios.get(url)
        if (response.data) {
          // Process activities to ensure they have proper types and icons
          recentActivities.value = response.data.map(activity => {
            // Determine activity type based on title or description
            let activityType = 'completed' // default
            const title = (activity.title || '').toLowerCase()
            const description = (activity.description || '').toLowerCase()
            
            if (title.includes('review') || title.includes('received') || description.includes('review')) {
              activityType = 'review'
            } else if (title.includes('due') || title.includes('deadline') || description.includes('due')) {
              activityType = 'due'
            } else if (title.includes('completed') || title.includes('finished') || description.includes('completed')) {
              activityType = 'completed'
            } else if (title.includes('audit') || description.includes('audit')) {
              activityType = 'audit'
            } else if (title.includes('approval') || title.includes('approved') || description.includes('approval')) {
              activityType = 'approval'
            } else if (title.includes('rejection') || title.includes('rejected') || description.includes('rejection')) {
              activityType = 'rejection'
            } else if (title.includes('update') || title.includes('updated') || description.includes('update')) {
              activityType = 'update'
            } else if (title.includes('create') || title.includes('created') || description.includes('create')) {
              activityType = 'create'
            }
            
            const processedActivity = {
              ...activity,
              type: activityType
            }
            console.log('Processed activity:', processedActivity)
            return processedActivity
          })
        } else {
          recentActivities.value = []
        }
      } catch (error) {
        console.error('Error fetching recent activities:', error)
        
        // Add default activities for better user experience even when API fails
        recentActivities.value = [
          {
            type: 'completed',
            audit_id: 0,
            title: 'Audit Completed',
            description: 'ISO 27001:2022 audit has been completed',
            time_ago: 'Recently'
          },
          {
            type: 'review',
            audit_id: 0,
            title: 'Review Received',
            description: 'ISO 27001:2022 I - Review received',
            time_ago: 'Recently'
          },
          {
            type: 'review',
            audit_id: 0,
            title: 'Review Received',
            description: 'NIST 800-53 I - Review received',
            time_ago: 'Recently'
          },
          {
            type: 'review',
            audit_id: 0,
            title: 'Review Received',
            description: 'Payment Card Industry Data Security Stand - Review received',
            time_ago: 'Recently'
          },
          {
            type: 'due',
            audit_id: 0,
            title: 'Due Date Approaching',
            description: 'Sample upcoming deadline',
            time_ago: 'Soon'
          }
        ]
      } finally {
        isLoadingActivities.value = false
      }
    }

    // Refresh all dashboard data
    const refreshData = async () => {
      isLoading.value = true
      try {
        await Promise.all([
          fetchAuditCompletionRate(),
          fetchTotalAudits(),
          fetchOpenAudits(),
          fetchCompletedAudits(),
          updateAllCharts(),
          fetchRecentActivities()
        ])
      } catch (error) {
        console.error('Error refreshing dashboard data:', error)
      } finally {
        isLoading.value = false
      }
    }

    // Fetch data on component mount
    onMounted(async () => {
      // Load framework from Vuex store
      const storeFrameworkId = store.state.framework.selectedFrameworkId
      if (storeFrameworkId && storeFrameworkId !== 'all') {
        selectedFramework.value = storeFrameworkId
        console.log('🔄 UserDashboard: Loaded framework from Vuex store:', storeFrameworkId)
      }
      
      refreshData()
      
      // Fetch frameworks first, then check for selected framework from session
      const frameworksLoaded = await fetchFrameworks()
      
      if (frameworksLoaded) {
        // Check for selected framework from session and set it
        await checkSelectedFrameworkFromSession()
      }
    })

    // Watch for filter changes
    watch([selectedFramework, selectedPolicy], () => {
      updateAllCharts()
    })
    
    // Watch for Vuex store framework changes
    watch(
      () => store.state.framework.selectedFrameworkId,
      async (newFrameworkId, oldFrameworkId) => {
        // Only update if value actually changed
        if (newFrameworkId === oldFrameworkId) return
        
        console.log('🔄 UserDashboard: Vuex store framework changed to:', newFrameworkId)
        // Update local filter to match store
        if (newFrameworkId === 'all' || !newFrameworkId) {
          selectedFramework.value = 'all'
        } else {
          selectedFramework.value = newFrameworkId
        }
        
        // Force data refresh
        await fetchPolicies(newFrameworkId !== 'all' ? newFrameworkId : null)
        updateAllCharts()
      }
    )

    // Chart options
    const lineChartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { 
          display: false
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          titleColor: '#1f2937',
          bodyColor: '#4b5563',
          borderColor: '#d1d5db',
          borderWidth: 1,
          padding: 12,
          boxPadding: 6,
          bodyFont: { size: 12 },
          titleFont: { size: 13, weight: 'bold' },
          cornerRadius: 8
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            display: true,
            color: '#e5e7eb',
            lineWidth: 1
          },
          border: {
            display: true,
            color: '#d1d5db',
            width: 1
          },
          ticks: {
            font: { size: 11 },
            color: '#374151',
            padding: 8
          }
        },
        x: {
          grid: {
            display: false
          },
          border: {
            display: true,
            color: '#d1d5db',
            width: 1
          },
          ticks: {
            font: { size: 11 },
            color: '#374151',
            maxRotation: 45,
            minRotation: 0,
            padding: 8
          }
        }
      },
      animation: {
        duration: 1000,
        easing: 'easeOutQuart'
      },
      elements: {
        point: {
          radius: 4,
          hoverRadius: 6,
          borderWidth: 2,
          borderColor: '#ffffff'
        },
        line: {
          borderWidth: 2,
          tension: 0.4
        }
      }
    }
    
    const donutChartOptions = {
      cutout: '50%',
      responsive: true,
      maintainAspectRatio: false,
      aspectRatio: 1,
      layout: {
        padding: {
          top: 15,
          bottom: 15,
          left: 15,
          right: 15
        }
      },
      plugins: {
        legend: { 
          display: false
        },
        tooltip: {
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          titleColor: '#1f2937',
          bodyColor: '#4b5563',
          borderColor: '#d1d5db',
          borderWidth: 1,
          padding: 12,
          boxPadding: 6,
          bodyFont: { size: 12 },
          titleFont: { size: 13, weight: 'bold' },
          cornerRadius: 8
        }
      },
      animation: {
        animateRotate: true,
        animateScale: true,
        duration: 1000,
        easing: 'easeOutCubic'
      }
    }
    
    const barChartOptions = {
      plugins: { 
        legend: { 
          display: false
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          titleColor: '#1f2937',
          bodyColor: '#4b5563',
          borderColor: '#d1d5db',
          borderWidth: 1,
          padding: 12,
          boxPadding: 6,
          bodyFont: { size: 12 },
          titleFont: { size: 13, weight: 'bold' },
          cornerRadius: 8
        }
      },
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { 
          stacked: false, 
          grid: { 
            display: false 
          },
          border: {
            display: true,
            color: '#d1d5db',
            width: 1
          },
          ticks: { 
            color: '#374151', 
            font: { size: 11 },
            maxRotation: 45,
            minRotation: 0,
            padding: 8
          }
        },
        y: { 
          stacked: false, 
          grid: { 
            color: '#e5e7eb',
            lineWidth: 1
          },
          border: {
            display: true,
            color: '#d1d5db',
            width: 1
          },
          ticks: { 
            color: '#374151', 
            font: { size: 11 },
            padding: 8
          },
          beginAtZero: true
        }
      },
      animation: {
        duration: 1000,
        easing: 'easeInOutQuart'
      },
      elements: {
        bar: {
          borderRadius: 4,
          borderSkipped: false
        }
      }
    }
    
    const horizontalBarChartOptions = {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { 
          display: false
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          titleColor: '#1f2937',
          bodyColor: '#4b5563',
          borderColor: '#d1d5db',
          borderWidth: 1,
          padding: 12,
          boxPadding: 6,
          bodyFont: { size: 12 },
          titleFont: { size: 13, weight: 'bold' },
          cornerRadius: 8
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          grid: { 
            color: '#e5e7eb',
            lineWidth: 1
          },
          border: {
            display: true,
            color: '#d1d5db',
            width: 1
          },
          ticks: { 
            color: '#374151', 
            font: { size: 11 },
            padding: 8
          },
          stacked: false
        },
        y: {
          grid: { 
            display: false 
          },
          border: {
            display: true,
            color: '#d1d5db',
            width: 1
          },
          ticks: { 
            color: '#374151', 
            font: { size: 11 },
            padding: 8
          },
          stacked: false
        }
      },
      animation: {
        duration: 1000,
        easing: 'easeInOutQuart'
      },
      elements: {
        bar: {
          borderRadius: 4,
          borderSkipped: false
        }
      }
    }

    // Helper function to get activity icon
    const getActivityIcon = (type) => {
      const icon = (() => {
        switch(type) {
          case 'completed': return 'fas fa-check-circle'
          case 'review': return 'fas fa-eye'
          case 'due': return 'fas fa-clock'
          case 'audit': return 'fas fa-clipboard-check'
          case 'approval': return 'fas fa-thumbs-up'
          case 'rejection': return 'fas fa-times-circle'
          case 'update': return 'fas fa-edit'
          case 'create': return 'fas fa-plus-circle'
          default: return 'fas fa-info-circle'
        }
      })()
      console.log(`Icon for type "${type}":`, icon)
      return icon
    }

    // Helper function to get activity icon class
    const getActivityIconClass = (type) => {
      switch(type) {
        case 'completed': return 'approved'
        case 'review': return 'update'
        case 'due': return 'alert'
        case 'audit': return 'create'
        case 'approval': return 'approved'
        case 'rejection': return 'alert'
        case 'update': return 'update'
        case 'create': return 'create'
        default: return ''
      }
    }

    // Helper function to safely check if an array is empty
    const isEmpty = (arr) => {
      return !arr || !Array.isArray(arr) || arr.length === 0;
    }

    // Computed property for filtered activities
    const filteredActivities = computed(() => {
      if (!recentActivities.value || !Array.isArray(recentActivities.value)) {
        return [];
      }
      return recentActivities.value.filter(activity => activity !== null && activity !== undefined);
    })

    // Navigation function to go back to AuditorDashboard
    const goBackToAuditorDashboard = () => {
      router.push({ name: 'AuditorDashboard' })
    }

    // Download dashboard as PDF
    const downloadDashboardPDF = async () => {
      isDownloading.value = true
      try {
        await nextTick() // Ensure all components are rendered
        
        const dashboardElement = document.querySelector('.dashboard-container')
        if (!dashboardElement) {
          throw new Error('Dashboard element not found')
        }

        // Wait a bit to ensure all charts are fully rendered
        await new Promise(resolve => setTimeout(resolve, 300))

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
        const filename = `Auditor-Dashboard-${timestamp}.pdf`

        // Download the PDF
        pdf.save(filename)

        // Show success notification
        console.log('PDF downloaded successfully')
        showNotification('Success', 'Dashboard PDF has been downloaded successfully!', 'success')
      } catch (error) {
        console.error('Error generating PDF:', error)
        showNotification('Error', 'Failed to generate PDF. Please try again.', 'error')
      } finally {
        isDownloading.value = false
      }
    }

    // Helper function for notifications
    const showNotification = (title, text, icon) => {
      // Simple notification fallback
      if (icon === 'success') {
        console.log(`✓ ${title}: ${text}`)
      } else {
        console.error(`✗ ${title}: ${text}`)
      }
    }

    return {
      isLoading,
      isLoadingActivities,
      isDownloading,
      error,
      auditCompletionData,
      totalAuditsData,
      openAuditsData,
      completedAuditsData,
      recentActivities,
      refreshData,
      fetchRecentActivities,
      getActivityIcon,
      getActivityIconClass,
      isEmpty,
      categoryData,
      statusData,
      completionData,
      findingsData,
      complianceTrendData,
      departmentData,
      lineChartOptions,
      donutChartOptions,
      barChartOptions,
      horizontalBarChartOptions,
      filteredActivities,
      frameworks,
      policies,
      selectedFramework,
      selectedPolicy,
      onFrameworkChange,
      onPolicyChange,
      goBackToAuditorDashboard,
      downloadDashboardPDF
    }
  }
}
</script>

<style scoped>
@import './UserDashboard.css';

.loading-overlay {
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
  z-index: 1000;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #4f6cff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  background-color: #fee2e2;
  border: 1px solid #ef4444;
  color: #b91c1c;
  padding: 1rem;
  margin: 1rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.retry-btn {
  background-color: #b91c1c;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.retry-btn:hover {
  background-color: #991b1b;
}

.activity-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #666;
  margin-top: 0.25rem;
}

.activity-author {
  color: #4f6cff;
  font-weight: 500;
}
</style> 