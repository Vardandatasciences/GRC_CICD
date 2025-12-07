<template>
  <div class="events-dashboard-container">
    <!-- Header Section -->
    <div class="events-dashboard-header">
      <h1 class="events-dashboard-title">Events Dashboard</h1>
      <!-- <p class="events-dashboard-subtitle">High-level overview and insights</p> -->
    </div>

    <!-- Filters Section -->
    <div class="events-dashboard-filters">
      <EventFilters @export="handleExport" @filter-change="handleFilterChange" :show-advanced="false" />
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="events-dashboard-loading">
      <div class="events-dashboard-loading-content">
        <div class="events-dashboard-loading-spinner"></div>
        <p class="events-dashboard-loading-text">Loading dashboard data...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="events-dashboard-error">
      <div class="events-dashboard-error-content">
        <div class="events-dashboard-error-icon">
          <svg class="events-dashboard-error-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
        <div class="events-dashboard-error-details">
          <h3 class="events-dashboard-error-title">Error loading dashboard</h3>
          <p class="events-dashboard-error-message">{{ error }}</p>
          <button @click="fetchDashboardData" class="events-dashboard-error-retry">
            Try Again
          </button>
        </div>
      </div>
    </div>

    <!-- Dashboard Content -->
    <div v-else-if="dashboardData" class="events-dashboard-content">
      <!-- KPI Cards -->
      <div class="events-dashboard-kpi-grid">
        <div class="events-dashboard-kpi-card">
          <div class="events-dashboard-kpi-card-content">
            <div class="events-dashboard-kpi-card-info">
              <p class="events-dashboard-kpi-card-label">Total Events</p>
              <p class="events-dashboard-kpi-card-value">{{ dashboardData.kpis.total_events }}</p>
            </div>
            <div class="events-dashboard-kpi-card-icon">
              <component :is="FileTextIcon" class="events-dashboard-kpi-card-icon-svg" />
            </div>
          </div>
          <div class="events-dashboard-kpi-card-trend events-dashboard-kpi-card-trend-positive">
            <svg class="events-dashboard-kpi-card-trend-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 17l9.2-9.2M17 17V7H7"></path>
            </svg>
            <span class="events-dashboard-kpi-card-trend-text">
              {{ dashboardData.kpis.trend_percentage }}% vs last month
            </span>
          </div>
        </div>

        <div class="events-dashboard-kpi-card">
          <div class="events-dashboard-kpi-card-content">
            <div class="events-dashboard-kpi-card-info">
              <p class="events-dashboard-kpi-card-label">Upcoming Events</p>
              <p class="events-dashboard-kpi-card-value">{{ dashboardData.kpis.upcoming_events }}</p>
            </div>
            <div class="events-dashboard-kpi-card-icon">
              <component :is="CalendarIcon" class="events-dashboard-kpi-card-icon-svg" />
            </div>
          </div>
          <div class="events-dashboard-kpi-card-trend events-dashboard-kpi-card-trend-negative">
            <svg class="events-dashboard-kpi-card-trend-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 7l-9.2 9.2M7 7v10h10"></path>
            </svg>
            <span class="events-dashboard-kpi-card-trend-text">2% vs last month</span>
          </div>
        </div>

        <div class="events-dashboard-kpi-card">
          <div class="events-dashboard-kpi-card-content">
            <div class="events-dashboard-kpi-card-info">
              <p class="events-dashboard-kpi-card-label">Overdue Events</p>
              <p class="events-dashboard-kpi-card-value">{{ dashboardData.kpis.overdue_events }}</p>
            </div>
            <div class="events-dashboard-kpi-card-icon">
              <component :is="AlertCircleIcon" class="events-dashboard-kpi-card-icon-svg" />
            </div>
          </div>
          <div class="events-dashboard-kpi-card-trend events-dashboard-kpi-card-trend-negative">
            <svg class="events-dashboard-kpi-card-trend-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 7l-9.2 9.2M7 7v10h10"></path>
            </svg>
            <span class="events-dashboard-kpi-card-trend-text">1% vs last month</span>
          </div>
        </div>

        <div class="events-dashboard-kpi-card">
          <div class="events-dashboard-kpi-card-content">
            <div class="events-dashboard-kpi-card-info">
              <p class="events-dashboard-kpi-card-label">Pending Approvals</p>
              <p class="events-dashboard-kpi-card-value">{{ dashboardData.kpis.pending_approvals }}</p>
            </div>
            <div class="events-dashboard-kpi-card-icon">
              <component :is="ClockIcon" class="events-dashboard-kpi-card-icon-svg" />
            </div>
          </div>
          <div class="events-dashboard-kpi-card-trend events-dashboard-kpi-card-trend-positive">
            <svg class="events-dashboard-kpi-card-trend-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 17l9.2-9.2M17 17V7H7"></path>
            </svg>
            <span class="events-dashboard-kpi-card-trend-text">3% vs last month</span>
          </div>
        </div>
      </div>

      <!-- Charts Row 1 -->
      <div class="events-dashboard-charts-grid">
        <!-- Events by Category -->
        <div class="events-dashboard-chart-container">
          <div class="events-dashboard-chart-header">
            <h3 class="events-dashboard-chart-title">Events by Category</h3>
          </div>
          <div class="events-dashboard-chart-content">
            <canvas ref="eventsByCategoryChart" class="events-dashboard-chart-canvas" width="400" height="300"></canvas>
          </div>
        </div>

        <!-- Events by Framework -->
        <div class="events-dashboard-chart-container">
          <div class="events-dashboard-chart-header">
            <h3 class="events-dashboard-chart-title">Events by Framework</h3>
          </div>
          <div class="events-dashboard-chart-content">
            <canvas ref="eventsByFrameworkChart" class="events-dashboard-chart-canvas" width="400" height="300"></canvas>
          </div>
        </div>
      </div>

      <!-- Charts Row 2 -->
      <div class="events-dashboard-charts-grid">
        <!-- Events by Status -->
        <div class="events-dashboard-chart-container">
          <div class="events-dashboard-chart-header">
            <h3 class="events-dashboard-chart-title">Events by Status</h3>
          </div>
          <div class="events-dashboard-chart-content">
            <canvas ref="eventsByStatusChart" class="events-dashboard-chart-canvas" width="400" height="300"></canvas>
          </div>
        </div>

        <!-- Events by Priority -->
        <div class="events-dashboard-chart-container">
          <div class="events-dashboard-chart-header">
            <h3 class="events-dashboard-chart-title">Events by Priority</h3>
          </div>
          <div class="events-dashboard-chart-content">
            <canvas ref="eventsByPriorityChart" class="events-dashboard-chart-canvas" width="400" height="300"></canvas>
          </div>
        </div>
      </div>

      <!-- Trend Charts Row -->
      <div class="events-dashboard-charts-grid">
        <!-- Event Trend Over Time -->
        <div class="events-dashboard-chart-container">
          <div class="events-dashboard-chart-header">
            <h3 class="events-dashboard-chart-title">Event Trend Over Time</h3>
          </div>
          <div class="events-dashboard-chart-content">
            <canvas ref="trendOverTimeChart" class="events-dashboard-chart-canvas" width="400" height="300"></canvas>
          </div>
        </div>

        <!-- Completion Rate Trend -->
        <div class="events-dashboard-chart-container">
          <div class="events-dashboard-chart-header">
            <h3 class="events-dashboard-chart-title">Completion Rate Trend</h3>
          </div>
          <div class="events-dashboard-chart-content">
            <canvas ref="completionRateChart" class="events-dashboard-chart-canvas" width="400" height="300"></canvas>
          </div>
        </div>
      </div>

      <!-- Recent Events -->
      <div class="events-dashboard-recent-events">
        <div class="events-dashboard-recent-events-header">
          <h3 class="events-dashboard-recent-events-title">Recent Events</h3>
          <span class="events-dashboard-recent-events-subtitle">Last 3 events</span>
        </div>
        <div v-if="dashboardData.recent_events.length > 0" class="events-dashboard-recent-events-list">
          <div v-for="event in dashboardData.recent_events" :key="event.id" class="events-dashboard-recent-event-item">
            <p class="events-dashboard-recent-event-title">{{ event.title }}</p>
            <p class="events-dashboard-recent-event-meta">{{ event.event_id }} • {{ event.category }}</p>
            <div class="events-dashboard-recent-event-footer">
              <span class="events-dashboard-recent-event-date">{{ event.created_at }}</span>
              <div class="events-dashboard-recent-event-status">
                <span :class="`events-dashboard-status-dot ${getStatusColorClass(event.status)}`"></span>
                <span :class="`events-dashboard-status-text ${getStatusColorClass(event.status)}`">
                  {{ event.status }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="events-dashboard-recent-events-empty">
          <div class="events-dashboard-recent-events-empty-icon">
            <svg class="events-dashboard-recent-events-empty-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
            </svg>
          </div>
          <p class="events-dashboard-recent-events-empty-title">No recent events found</p>
          <p class="events-dashboard-recent-events-empty-subtitle">Events from the last 7 days will appear here</p>
        </div>
      </div>
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { eventService } from '../../services/api'
import EventFilters from './EventFilters.vue'
import { Chart, registerables } from 'chart.js'
import PopupModal from '../../modules/popus/PopupModal.vue'
import AccessUtils from '../../utils/accessUtils'
import axios from 'axios'
import eventDataService from '../../services/eventService' // NEW: Centralized event data service

// Ensure Chart.js is properly loaded
if (typeof Chart === 'undefined') {
  console.error('Chart.js is not loaded properly')
}

export default {
  name: 'EventsDashboard',
  components: {
    EventFilters,
    PopupModal
  },
  setup() {
    const dashboardData = ref(null)
    const loading = ref(false)
    const error = ref(null)
    
    // Filter state
    const currentFilters = ref({
      framework: '',
      module: '',
      category: '',
      owner: ''
    })
    
    // Framework selection from session
    const selectedFrameworkFromSession = ref(null)
    
    // Chart refs
    const eventsByCategoryChart = ref(null)
    const eventsByFrameworkChart = ref(null)
    const eventsByStatusChart = ref(null)
    const eventsByPriorityChart = ref(null)
    const trendOverTimeChart = ref(null)
    const completionRateChart = ref(null)
    
    // Chart instances
    let eventsByCategoryChartInstance = null
    let eventsByFrameworkChartInstance = null
    let eventsByStatusChartInstance = null
    let eventsByPriorityChartInstance = null
    let trendOverTimeChartInstance = null
    let completionRateChartInstance = null

    const handleExport = (format) => {
      console.log(`Exporting dashboard data as ${format}`)
    }

    const handleFilterChange = (filterData) => {
      console.log('Filter changed:', filterData)
      currentFilters.value = { ...filterData }
      // Refresh dashboard data with new filters
      fetchDashboardData()
    }

    const getIcon = (index) => {
      const IconMap = {
        0: 'FileTextIcon',
        1: 'CalendarIcon',
        2: 'AlertCircleIcon',
        3: 'ClockIcon'
      }
      return IconMap[index] || 'FileTextIcon'
    }

    // Icon components - you can replace these with actual icon components
    const FileTextIcon = {
      template: '<svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>'
    }

    const CalendarIcon = {
      template: '<svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>'
    }

    const AlertCircleIcon = {
      template: '<svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
    }

    const ClockIcon = {
      template: '<svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
    }

    const getStatusColorClass = (status) => {
      switch (status) {
        case 'Approved': return 'events-dashboard-status-approved'
        case 'Pending Review': return 'events-dashboard-status-pending-review'
        case 'Rejected': return 'events-dashboard-status-rejected'
        case 'Draft': return 'events-dashboard-status-draft'
        case 'Under Review': return 'events-dashboard-status-under-review'
        case 'Completed': return 'events-dashboard-status-completed'
        case 'Cancelled': return 'events-dashboard-status-cancelled'
        default: return 'events-dashboard-status-default'
      }
    }

    // Check for selected framework from session (similar to other modules)
    const checkSelectedFrameworkFromSession = async () => {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in EventsDashboard...')
        const response = await axios.get('/api/frameworks/get-selected/', {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        })
        
        console.log('🔍 DEBUG: Framework response in EventsDashboard:', response.data)
        
        if (response.data && response.data.frameworkId) {
          const frameworkIdFromSession = response.data.frameworkId.toString()
          console.log('✅ DEBUG: Found selected framework in session for EventsDashboard:', frameworkIdFromSession)
          
          // Set the selected framework from session
          selectedFrameworkFromSession.value = frameworkIdFromSession
          console.log('📊 DEBUG: Events are now filtered by framework:', frameworkIdFromSession)
          console.log('📊 DEBUG: selectedFrameworkFromSession.value set to:', selectedFrameworkFromSession.value)
        } else {
          console.log('ℹ️ DEBUG: No framework filter active - showing all events')
          selectedFrameworkFromSession.value = null
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework in EventsDashboard:', error)
        selectedFrameworkFromSession.value = null
      }
    }

    const fetchDashboardData = async () => {
      try {
        loading.value = true
        error.value = null
        
        console.log('[EventsDashboard] Checking for cached event data...')
        
        // ==========================================
        // NEW: Check if data is already cached from HomeView prefetch
        // ==========================================
        // Note: Dashboard still needs to fetch dashboard-specific analytics from API
        // But we can check if basic event data is available for initial state
        if (eventDataService.hasValidCache()) {
          console.log('[EventsDashboard] ✅ Event cache available from HomeView prefetch')
          const cachedEvents = eventDataService.getData('events') || []
          console.log('[EventsDashboard] Cached events count:', cachedEvents.length)
        } else if (window.eventDataFetchPromise) {
          console.log('[EventsDashboard] ⏳ Waiting for ongoing prefetch to complete...')
          await window.eventDataFetchPromise
          const cachedEvents = eventDataService.getData('events') || []
          console.log('[EventsDashboard] Cached events count:', cachedEvents.length)
        }
        
        // Dashboard needs specific analytics data, so we still fetch from dashboard API
        // Build query parameters from current filters
        const params = new URLSearchParams()
        if (currentFilters.value.framework) {
          params.append('framework', currentFilters.value.framework)
        }
        if (currentFilters.value.module) {
          params.append('module', currentFilters.value.module)
        }
        if (currentFilters.value.category) {
          params.append('category', currentFilters.value.category)
        }
        if (currentFilters.value.owner) {
          params.append('owner', currentFilters.value.owner)
        }
        
        const queryString = params.toString()
        const url = queryString ? `/api/events/dashboard/?${queryString}` : '/api/events/dashboard/'
        
        console.log('[EventsDashboard] Fetching dashboard analytics with filters:', currentFilters.value)
        console.log('Request URL:', url)
        
        const response = await eventService.getEventsDashboard(queryString)
        if (response.data.success) {
          dashboardData.value = response.data
          // Create charts after data is loaded
          await nextTick()
          // Add a small delay to ensure DOM is fully rendered
          setTimeout(() => {
            createCharts()
          }, 100)
        } else {
          console.error('Dashboard API returned error:', response.data)
          error.value = response.data.message || 'Failed to fetch dashboard data'
        }
      } catch (err) {
        console.error('Error fetching dashboard data:', err)
        
        // Check if it's an access denied error (403)
        if (err.response && err.response.status === 403) {
          AccessUtils.showAccessDenied('Event Management - Dashboard', 'You don\'t have permission to view the events dashboard. Required permission: event.view_all_event or event.view_module_event')
        } else {
          error.value = 'Failed to fetch dashboard data. Please try again.'
        }
      } finally {
        loading.value = false
      }
    }

    const createCharts = async () => {
      await nextTick()
      
      console.log('Creating charts with data:', dashboardData.value)
      console.log('Chart.js available:', typeof Chart !== 'undefined')
      
      // Register Chart.js components
      Chart.register(...registerables)
      
      createEventsByCategoryChart()
      createEventsByFrameworkChart()
      createEventsByStatusChart()
      createEventsByPriorityChart()
      createTrendOverTimeChart()
      createCompletionRateChart()
    }

    const createEventsByCategoryChart = () => {
      console.log('Creating Events by Category chart, canvas ref:', eventsByCategoryChart.value)
      if (!eventsByCategoryChart.value) {
        console.log('Events by Category chart canvas not found')
        return
      }
      
      // Destroy existing chart
      if (eventsByCategoryChartInstance) {
        eventsByCategoryChartInstance.destroy()
      }
      
      try {
        const ctx = eventsByCategoryChart.value.getContext('2d')
        console.log('Canvas context:', ctx)
        
        // Use real data from backend
        const categoryData = dashboardData.value?.charts?.events_by_category || []
        console.log('Category data from backend:', categoryData)
        
        // Prepare data for the chart
        const labels = categoryData.map(item => item.Category || 'Uncategorized')
        const data = categoryData.map(item => item.count || 0)
        
        // Balanced color palette for different categories
        const colors = ['#60A5FA', '#F87171', '#A78BFA', '#34D399', '#FBBF24', '#F472B6', '#A3E635', '#FB923C']
        
        eventsByCategoryChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Events',
            data: data,
            backgroundColor: colors.slice(0, labels.length),
            borderRadius: 4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  return `${context.label}: ${context.raw} events`
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                display: false
              }
            },
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Number of Events'
              }
            }
          }
        }
      })
      console.log('Events by Category chart created successfully')
      } catch (error) {
        console.error('Error creating Events by Category chart:', error)
      }
    }

    const createEventsByFrameworkChart = () => {
      console.log('Creating Events by Framework chart, canvas ref:', eventsByFrameworkChart.value)
      if (!eventsByFrameworkChart.value) {
        console.log('Events by Framework chart canvas not found')
        return
      }
      
      // Destroy existing chart
      if (eventsByFrameworkChartInstance) {
        eventsByFrameworkChartInstance.destroy()
      }
      
      try {
        const ctx = eventsByFrameworkChart.value.getContext('2d')
        
        // Use real data from backend
        const frameworkData = dashboardData.value?.charts?.events_by_framework || []
        console.log('Framework data from backend:', frameworkData)
        
        // Prepare data for the chart
        const labels = frameworkData.map(item => item.FrameworkName || 'Unknown Framework')
        const data = frameworkData.map(item => item.count || 0)
        
        // Balanced color palette for different frameworks
        const colors = ['#60A5FA', '#F87171', '#FBBF24', '#34D399', '#A78BFA', '#F472B6', '#A3E635', '#FB923C']
        
        eventsByFrameworkChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: labels,
          datasets: [{
            data: data,
            backgroundColor: colors.slice(0, labels.length),
            borderWidth: 0,
            borderRadius: 3
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '60%',
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                usePointStyle: true,
                padding: 20,
                generateLabels: function(chart) {
                  const data = chart.data
                  if (data.labels.length && data.datasets.length) {
                    return data.labels.map((label, i) => {
                      const value = data.datasets[0].data[i]
                      return {
                        text: `${label}: ${value} events`,
                        fillStyle: data.datasets[0].backgroundColor[i],
                        strokeStyle: data.datasets[0].backgroundColor[i],
                        lineWidth: 0,
                        pointStyle: 'circle',
                        hidden: false,
                        index: i
                      }
                    })
                  }
                  return []
                }
              }
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  return `${context.label}: ${context.raw} events`
                }
              }
            }
          }
        }
      })
      } catch (error) {
        console.error('Error creating Events by Framework chart:', error)
      }
    }

    const createTrendOverTimeChart = () => {
      console.log('Creating Trend Over Time chart, canvas ref:', trendOverTimeChart.value)
      if (!trendOverTimeChart.value) {
        console.log('Trend Over Time chart canvas not found')
        return
      }
      
      // Destroy existing chart
      if (trendOverTimeChartInstance) {
        trendOverTimeChartInstance.destroy()
      }
      
      try {
        const ctx = trendOverTimeChart.value.getContext('2d')
        
        // Use real monthly trend data from backend
        const monthlyTrends = dashboardData.value?.charts?.monthly_trends || []
        console.log('Monthly trends data from backend:', monthlyTrends)
        
        let months, trendData, currentMonthIndex
        
        if (monthlyTrends.length > 0) {
          // Extract months and counts from backend data
          months = monthlyTrends.map(trend => trend.month)
          trendData = monthlyTrends.map(trend => trend.count)
          
          // Find current month index for highlighting
          const currentMonthName = new Date().toLocaleDateString('en-US', { month: 'short' })
          currentMonthIndex = months.indexOf(currentMonthName)
        } else {
          // Fallback to default months if no data
          months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
          trendData = [0, 0, 0, 0, 0, 0]
          currentMonthIndex = -1
        }
        
        console.log('Months:', months)
        console.log('Trend data:', trendData)
        console.log('Current month index:', currentMonthIndex)
        
        trendOverTimeChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: months,
          datasets: [{
            label: 'Events',
            data: trendData,
            borderColor: '#60A5FA',
            backgroundColor: 'rgba(96, 165, 250, 0.1)',
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            pointRadius: months.map((_, index) => index === currentMonthIndex ? 6 : 4),
            pointHoverRadius: 8,
            pointBackgroundColor: months.map((_, index) => index === currentMonthIndex ? '#60A5FA' : '#60A5FA'),
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              mode: 'index',
              intersect: false,
              callbacks: {
                title: (context) => {
                  return context[0].label
                },
                label: (context) => {
                  const isCurrentMonth = context.dataIndex === currentMonthIndex
                  const monthLabel = isCurrentMonth ? ' (Current Month)' : ''
                  return `Events: ${context.raw}${monthLabel}`
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                display: false
              }
            },
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Number of Events'
              }
            }
          }
        }
      })
      } catch (error) {
        console.error('Error creating Trend Over Time chart:', error)
      }
    }

    const createEventsByStatusChart = () => {
      console.log('Creating Events by Status chart, canvas ref:', eventsByStatusChart.value)
      if (!eventsByStatusChart.value) {
        console.log('Events by Status chart canvas not found')
        return
      }
      
      // Destroy existing chart
      if (eventsByStatusChartInstance) {
        eventsByStatusChartInstance.destroy()
      }
      
      try {
        const ctx = eventsByStatusChart.value.getContext('2d')
        
        // Use real data from backend
        const statusData = dashboardData.value?.charts?.events_by_status || []
        console.log('Status data from backend:', statusData)
        
        // Prepare data for the chart
        const labels = statusData.map(item => item.Status || 'Unknown')
        const data = statusData.map(item => item.count || 0)
        
        // Balanced color palette for different statuses
        const statusColors = {
          'Completed': '#34D399',
          'Approved': '#34D399',
          'Pending Review': '#FBBF24',
          'Under Review': '#60A5FA',
          'Draft': '#9CA3AF',
          'Rejected': '#F87171',
          'Cancelled': '#9CA3AF'
        }
        
        const colors = labels.map(status => statusColors[status] || '#F1F5F9')
        
        eventsByStatusChartInstance = new Chart(ctx, {
          type: 'pie',
          data: {
            labels: labels,
            datasets: [{
              data: data,
              backgroundColor: colors,
              borderWidth: 2,
              borderColor: '#ffffff'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'bottom',
                labels: {
                  usePointStyle: true,
                  padding: 15
                }
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    return `${context.label}: ${context.raw} events`
                  }
                }
              }
            }
          }
        })
      } catch (error) {
        console.error('Error creating Events by Status chart:', error)
      }
    }

    const createEventsByPriorityChart = () => {
      console.log('Creating Events by Priority chart, canvas ref:', eventsByPriorityChart.value)
      if (!eventsByPriorityChart.value) {
        console.log('Events by Priority chart canvas not found')
        return
      }
      
      // Destroy existing chart
      if (eventsByPriorityChartInstance) {
        eventsByPriorityChartInstance.destroy()
      }
      
      try {
        const ctx = eventsByPriorityChart.value.getContext('2d')
        
        // Use real data from backend
        const priorityData = dashboardData.value?.charts?.events_by_priority || []
        console.log('Priority data from backend:', priorityData)
        
        // Prepare data for the chart
        const labels = priorityData.map(item => item.Priority || 'Unknown')
        const data = priorityData.map(item => item.count || 0)
        
        // Balanced color palette for different priorities
        const priorityColors = {
          'Critical': '#F87171',
          'High': '#FB923C',
          'Medium': '#FBBF24',
          'Low': '#34D399'
        }
        
        const colors = labels.map(priority => priorityColors[priority] || '#F1F5F9')
        
        eventsByPriorityChartInstance = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [{
              label: 'Events',
              data: data,
              backgroundColor: colors,
              borderRadius: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: false
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    return `${context.label}: ${context.raw} events`
                  }
                }
              }
            },
            scales: {
              x: {
                grid: {
                  display: false
                }
              },
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: 'Number of Events'
                }
              }
            }
          }
        })
      } catch (error) {
        console.error('Error creating Events by Priority chart:', error)
      }
    }


    const createCompletionRateChart = () => {
      console.log('Creating Completion Rate chart, canvas ref:', completionRateChart.value)
      if (!completionRateChart.value) {
        console.log('Completion Rate chart canvas not found')
        return
      }
      
      // Destroy existing chart
      if (completionRateChartInstance) {
        completionRateChartInstance.destroy()
      }
      
      try {
        const ctx = completionRateChart.value.getContext('2d')
        
        // Use real data from backend
        const completionData = dashboardData.value?.charts?.completion_trends || []
        console.log('Completion data from backend:', completionData)
        
        let months, completionRates, totalEvents, completedEvents
        
        if (completionData.length > 0) {
          // Extract months and completion rates from backend data
          months = completionData.map(trend => trend.month)
          completionRates = completionData.map(trend => trend.completion_rate)
          totalEvents = completionData.map(trend => trend.total_events)
          completedEvents = completionData.map(trend => trend.completed_events)
        } else {
          // Fallback to default months if no data
          months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
          completionRates = [0, 0, 0, 0, 0, 0]
          totalEvents = [0, 0, 0, 0, 0, 0]
          completedEvents = [0, 0, 0, 0, 0, 0]
        }
        
        console.log('Months:', months)
        console.log('Completion rates:', completionRates)
        
        completionRateChartInstance = new Chart(ctx, {
          type: 'line',
          data: {
            labels: months,
            datasets: [{
              label: 'Completion Rate (%)',
              data: completionRates,
            borderColor: '#34D399',
            backgroundColor: 'rgba(52, 211, 153, 0.1)',
              borderWidth: 3,
              tension: 0.4,
              fill: true,
              pointRadius: 5,
              pointHoverRadius: 8,
              pointBackgroundColor: '#34D399',
              pointBorderColor: '#ffffff',
              pointBorderWidth: 2
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: false
              },
              tooltip: {
                mode: 'index',
                intersect: false,
                callbacks: {
                  title: (context) => {
                    return context[0].label
                  },
                  label: (context) => {
                    const index = context.dataIndex
                    return [
                      `Completion Rate: ${context.raw}%`,
                      `Total Events: ${totalEvents[index]}`,
                      `Completed Events: ${completedEvents[index]}`
                    ]
                  }
                }
              }
            },
            scales: {
              x: {
                grid: {
                  display: false
                }
              },
              y: {
                beginAtZero: true,
                max: 100,
                title: {
                  display: true,
                  text: 'Completion Rate (%)'
                },
                ticks: {
                  callback: function(value) {
                    return value + '%'
                  }
                }
              }
            }
          }
        })
      } catch (error) {
        console.error('Error creating Completion Rate chart:', error)
      }
    }

    onMounted(async () => {
      // Check for framework selection from session
      await checkSelectedFrameworkFromSession()
      
      // Then fetch dashboard data
      await fetchDashboardData()
    })

    onUnmounted(() => {
      // Clean up chart instances
      if (eventsByCategoryChartInstance) {
        eventsByCategoryChartInstance.destroy()
      }
      if (eventsByFrameworkChartInstance) {
        eventsByFrameworkChartInstance.destroy()
      }
      if (eventsByStatusChartInstance) {
        eventsByStatusChartInstance.destroy()
      }
      if (eventsByPriorityChartInstance) {
        eventsByPriorityChartInstance.destroy()
      }
      if (trendOverTimeChartInstance) {
        trendOverTimeChartInstance.destroy()
      }
      if (completionRateChartInstance) {
        completionRateChartInstance.destroy()
      }
    })

    return {
      dashboardData,
      loading,
      error,
      selectedFrameworkFromSession,
      handleExport,
      handleFilterChange,
      getIcon,
      getStatusColorClass,
      FileTextIcon,
      CalendarIcon,
      AlertCircleIcon,
      ClockIcon,
      fetchDashboardData,
      eventsByCategoryChart,
      eventsByFrameworkChart,
      eventsByStatusChart,
      eventsByPriorityChart,
      trendOverTimeChart,
      completionRateChart
    }
  }
}
</script>

<style>
/* Events Dashboard Container */
.events-dashboard-container {
  padding: 24px;
  padding-top: 40px;
  background: white;
  min-height: 100vh;
  margin-left: -30px;
}

/* Events Dashboard Header */
.events-dashboard-header {
  margin-bottom: 32px;
}

.events-dashboard-title {
  font-size: 1.7rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.events-dashboard-subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
  font-weight: 500;
}

.events-dashboard-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.events-dashboard-export-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.events-dashboard-export-btn:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

.events-dashboard-export-icon {
  width: 16px;
  height: 16px;
}

.events-dashboard-export-text {
  font-weight: 600;
}

/* Filters Section */
.events-dashboard-filters {
  margin-bottom: 32px;
}

/* Loading State */
.events-dashboard-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
}

.events-dashboard-loading-content {
  text-align: center;
}

.events-dashboard-loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: events-dashboard-spin 1s linear infinite;
  margin: 0 auto 16px;
}

.events-dashboard-loading-text {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
}

/* Error State */
.events-dashboard-error {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fecaca;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.events-dashboard-error-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.events-dashboard-error-icon {
  flex-shrink: 0;
}

.events-dashboard-error-svg {
  width: 24px;
  height: 24px;
  color: #ef4444;
}

.events-dashboard-error-details {
  flex: 1;
}

.events-dashboard-error-title {
  font-size: 1rem;
  font-weight: 600;
  color: #dc2626;
  margin: 0 0 8px 0;
}

.events-dashboard-error-message {
  font-size: 0.9rem;
  color: #991b1b;
  margin: 0 0 16px 0;
}

.events-dashboard-error-retry {
  padding: 12px 24px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.events-dashboard-error-retry:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

/* Dashboard Content */
.events-dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* KPI Cards Grid */
.events-dashboard-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

/* KPI Cards */
.events-dashboard-kpi-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.events-dashboard-kpi-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}


.events-dashboard-kpi-card-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.events-dashboard-kpi-card-info {
  flex: 1;
}

.events-dashboard-kpi-card-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #6b7280;
  margin: 0 0 8px 0;
  letter-spacing: 0.5px;
}

.events-dashboard-kpi-card-value {
  font-size: 1.7rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  line-height: 1;
}

.events-dashboard-kpi-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  flex-shrink: 0;
}

.events-dashboard-kpi-card-icon {
  background: transparent;
  color: #6b7280;
}

.events-dashboard-kpi-card-icon-svg {
  width: 24px;
  height: 24px;
}

.events-dashboard-kpi-card-trend {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  font-weight: 600;
}

.events-dashboard-kpi-card-trend-positive {
  color: #059669;
}

.events-dashboard-kpi-card-trend-negative {
  color: #dc2626;
}

.events-dashboard-kpi-card-trend-icon {
  width: 16px;
  height: 16px;
}

.events-dashboard-kpi-card-trend-text {
  font-weight: 600;
}

/* Charts Grid */
.events-dashboard-charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}

/* Chart Containers */
.events-dashboard-chart-container {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  overflow: hidden;
  transition: all 0.3s ease;
}

.events-dashboard-chart-container:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.events-dashboard-chart-header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #f3f4f6;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
}

.events-dashboard-chart-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.events-dashboard-chart-content {
  padding: 20px 24px 24px;
  height: 300px;
  position: relative;
}

.events-dashboard-chart-canvas {
  width: 100% !important;
  height: 100% !important;
}

/* Recent Events */

.events-dashboard-recent-events-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #f3f4f6;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
}

.events-dashboard-recent-events-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.events-dashboard-recent-events-subtitle {
  font-size: 0.85rem;
  color: #6b7280;
  font-weight: 500;
}

.events-dashboard-recent-events-list {
  padding: 20px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.events-dashboard-recent-event-item {
  padding: 16px 0;
  border-bottom: 1px solid #e5e7eb;
  transition: all 0.3s ease;
}

.events-dashboard-recent-event-item:last-child {
  border-bottom: none;
}

.events-dashboard-recent-event-item:hover {
  background: rgba(248, 249, 250, 0.5);
  padding-left: 8px;
  border-radius: 8px;
}

.events-dashboard-recent-event-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  line-height: 1.4;
}

.events-dashboard-recent-event-meta {
  font-size: 0.8rem;
  color: #6b7280;
  margin: 0;
  font-weight: 500;
}

.events-dashboard-recent-event-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.events-dashboard-recent-event-date {
  font-size: 0.75rem;
  color: #9ca3af;
  font-weight: 500;
}

.events-dashboard-recent-event-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.events-dashboard-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.events-dashboard-status-text {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Status dot colors - solid dots */
.events-dashboard-status-dot.events-dashboard-status-approved {
  background-color: #10b981;
}

.events-dashboard-status-dot.events-dashboard-status-pending-review {
  background-color: #f59e0b;
}

.events-dashboard-status-dot.events-dashboard-status-rejected {
  background-color: #ef4444;
}

.events-dashboard-status-dot.events-dashboard-status-draft {
  background-color: #6b7280;
}

.events-dashboard-status-dot.events-dashboard-status-under-review {
  background-color: #3b82f6;
}

.events-dashboard-status-dot.events-dashboard-status-completed {
  background-color: #10b981;
}

.events-dashboard-status-dot.events-dashboard-status-cancelled {
  background-color: #6b7280;
}

.events-dashboard-status-dot.events-dashboard-status-default {
  background-color: #6b7280;
}

/* Status text colors - matching the dots */
.events-dashboard-status-text.events-dashboard-status-approved {
  color: #10b981;
}

.events-dashboard-status-text.events-dashboard-status-pending-review {
  color: #f59e0b;
}

.events-dashboard-status-text.events-dashboard-status-rejected {
  color: #ef4444;
}

.events-dashboard-status-text.events-dashboard-status-draft {
  color: #6b7280;
}

.events-dashboard-status-text.events-dashboard-status-under-review {
  color: #3b82f6;
}

.events-dashboard-status-text.events-dashboard-status-completed {
  color: #10b981;
}

.events-dashboard-status-text.events-dashboard-status-cancelled {
  color: #6b7280;
}

.events-dashboard-status-text.events-dashboard-status-default {
  color: #6b7280;
}

/* Empty State */
.events-dashboard-recent-events-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}

.events-dashboard-recent-events-empty-icon {
  margin-bottom: 16px;
}

.events-dashboard-recent-events-empty-svg {
  width: 48px;
  height: 48px;
  color: #9ca3af;
}

.events-dashboard-recent-events-empty-title {
  font-size: 1rem;
  color: #6b7280;
  margin: 0 0 8px 0;
  font-weight: 600;
}

.events-dashboard-recent-events-empty-subtitle {
  font-size: 0.85rem;
  color: #9ca3af;
  margin: 0;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .events-dashboard-kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .events-dashboard-container {
    margin-left: 0;
    padding: 16px;
  }
  
  .events-dashboard-title {
    font-size: 1.5rem;
  }
  
  .events-dashboard-kpi-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .events-dashboard-kpi-card {
    padding: 20px;
  }
  
  .events-dashboard-kpi-card-value {
    font-size: 2rem;
  }
  
  .events-dashboard-charts-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .events-dashboard-chart-content {
    height: 250px;
    padding: 16px 20px 20px;
  }
  
  .events-dashboard-recent-events-header {
    padding: 16px 20px 12px;
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
  
  .events-dashboard-recent-events-list {
    padding: 16px 20px 20px;
  }
  
  .events-dashboard-recent-event-footer {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
}

/* Animations */
@keyframes events-dashboard-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes events-dashboard-fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.events-dashboard-kpi-card,
.events-dashboard-chart-container,
.events-dashboard-recent-events {
  animation: events-dashboard-fadeIn 0.5s ease-out;
}

/* Focus states for accessibility */
.events-dashboard-export-btn:focus,
.events-dashboard-error-retry:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}
</style>
