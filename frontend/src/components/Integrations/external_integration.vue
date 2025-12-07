<template>
  <div class="external-integration-container">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <i class="fas fa-plug"></i>
          External Integrations
        </h1>
        <p class="page-description">
          Manage connections to external platforms and services to enhance your GRC capabilities
        </p>
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="error-message">
      <div class="error-content">
        <i class="fas fa-exclamation-triangle"></i>
        <span>{{ error }}</span>
        <button @click="loadExternalApplications" class="retry-btn">
          <i class="fas fa-redo"></i>
          Retry
        </button>
      </div>
    </div>

    <!-- Statistics Section -->
    <div class="statistics-section">
      <div class="stats-grid">
        <div class="stat-card total">
          <div class="stat-icon">
            <i class="fas fa-layer-group"></i>
          </div>
          <div class="stat-content">
            <h3 class="stat-number">{{ totalPlatforms }}</h3>
            <p class="stat-label">Total Platforms</p>
          </div>
        </div>
        
        <div class="stat-card connected">
          <div class="stat-icon">
            <i class="fas fa-check-circle"></i>
          </div>
          <div class="stat-content">
            <h3 class="stat-number">{{ connectedPlatforms }}</h3>
            <p class="stat-label">Connected</p>
          </div>
        </div>
        
        <div class="stat-card disconnected">
          <div class="stat-icon">
            <i class="fas fa-times-circle"></i>
          </div>
          <div class="stat-content">
            <h3 class="stat-number">{{ disconnectedPlatforms }}</h3>
            <p class="stat-label">Disconnected</p>
          </div>
        </div>
        
        <div class="stat-card data">
          <div class="stat-icon">
            <i class="fas fa-database"></i>
          </div>
          <div class="stat-content">
            <h3 class="stat-number">{{ platformsWithData }}</h3>
            <p class="stat-label">With Stored Data</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading Indicator -->
    <div v-if="loading" class="loading-indicator">
      <div class="loading-content">
        <i class="fas fa-spinner fa-spin"></i>
        <span>Loading external applications...</span>
      </div>
    </div>

    <!-- Platform Management Section -->
    <div class="platforms-section">
      <div class="section-header">
        <h2 class="section-title">
          <i class="fas fa-cogs"></i>
          Platform Management
        </h2>
        <div class="section-actions">
          <button class="btn btn-primary" @click="refreshPlatforms">
            <i class="fas fa-sync-alt"></i>
            Refresh Status
          </button>
          <button class="btn btn-info" @click="checkStoredProjectsData">
            <i class="fas fa-database"></i>
            Check Stored Data
          </button>
        </div>
      </div>

      <!-- Platform List View -->
      <div class="platforms-list-view">
        <table class="platforms-table">
          <thead>
            <tr>
              <th>Platform</th>
              <th>Category</th>
              <th>Type</th>
              <th>Description</th>
              <th>Version</th>
              <th>Last Sync</th>
              <th>Status</th>
              <th>Projects Data</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="platform in platforms" 
              :key="platform.id"
            >
              <td data-label="Platform" class="platform-name">
                <i :class="platform.icon" style="margin-right: 8px; color: #4f8cff;"></i>
                {{ platform.name }}
              </td>
              <td data-label="Category" class="platform-category">{{ platform.category }}</td>
              <td data-label="Type" class="platform-type">{{ platform.type }}</td>
              <td data-label="Description" class="platform-description">{{ platform.description }}</td>
              <td data-label="Version" class="platform-version">{{ platform.version || 'N/A' }}</td>
              <td data-label="Last Sync" class="platform-last-sync">{{ formatDate(platform.lastSync) }}</td>
              <td data-label="Status" class="platform-status">
                <span 
                  class="status-badge" 
                  :class="platform.status"
                >
                  <i :class="platform.status === 'connected' ? 'fas fa-check' : 'fas fa-times'"></i>
                  {{ platform.status === 'connected' ? 'Connected' : 'Disconnected' }}
                </span>
              </td>
              <td data-label="Projects Data" class="platform-projects-data">
                <button 
                  v-if="platform.status === 'connected'"
                  class="btn btn-info btn-sm"
                  @click="viewProjectsData(platform)"
                  :disabled="!platform.hasProjectsData"
                >
                  <i class="fas fa-database"></i>
                  {{ platform.hasProjectsData ? (platform.name === 'BambooHR' ? `View Data (${platform.employeeCount || 0} employees)` : `View Data (${platform.projectsCount || 0})`) : 'No Data' }}
                </button>
                <span v-else class="text-muted">-</span>
              </td>
              <td data-label="Actions" class="platform-actions">
                <button 
                  v-if="platform.status === 'disconnected'"
                  class="btn btn-success btn-sm"
                  @click="connectPlatform(platform)"
                  :disabled="platform.connecting"
                >
                  <i class="fas fa-plug" v-if="!platform.connecting"></i>
                  <i class="fas fa-spinner fa-spin" v-if="platform.connecting"></i>
                  {{ platform.connecting ? 'Connecting...' : (platform.name === 'Jira' ? 'Open Jira' : 'Connect') }}
                </button>
                
                <button 
                  v-if="platform.status === 'connected'"
                  class="btn btn-danger btn-sm"
                  @click="disconnectPlatform(platform)"
                  :disabled="platform.disconnecting"
                >
                  <i class="fas fa-unlink" v-if="!platform.disconnecting"></i>
                  <i class="fas fa-spinner fa-spin" v-if="platform.disconnecting"></i>
                  {{ platform.disconnecting ? 'Disconnecting...' : 'Disconnect' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Platform Details Modal -->
    <div v-if="selectedPlatform" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">
            <i :class="selectedPlatform.icon"></i>
            {{ selectedPlatform.name }} Details
          </h3>
          <button class="modal-close" @click="closeModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <!-- BambooHR Connection Form -->
          <div v-if="selectedPlatform.showConnectionForm" class="connection-form-section">
            <h4>
              <i class="fas fa-plug"></i>
              Connect to BambooHR
            </h4>
            <div class="form-group">
              <label for="company-domain">Company Domain</label>
              <input 
                type="text" 
                id="company-domain"
                v-model="selectedPlatform.connectionForm.company_domain" 
                placeholder="yourcompany"
                class="form-control"
              >
              <small class="form-text">Enter your BambooHR company domain (e.g., "yourcompany" from yourcompany.bamboohr.com)</small>
            </div>
            <div class="form-group">
              <label for="api-key">API Key</label>
              <input 
                type="password" 
                id="api-key"
                v-model="selectedPlatform.connectionForm.api_key" 
                placeholder="Enter your BambooHR API key"
                class="form-control"
              >
              <small class="form-text">Get your API key from BambooHR Settings > API Keys</small>
            </div>
            <div class="form-group">
              <label for="sync-frequency">Sync Frequency</label>
              <select id="sync-frequency" v-model="selectedPlatform.connectionForm.sync_frequency" class="form-control">
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="manual">Manual Only</option>
              </select>
            </div>
          </div>

          <!-- BambooHR Data Viewer -->
          <div v-else-if="selectedPlatform.showDataViewer && selectedPlatform.projectsData" class="data-viewer-section">
            <h4>
              <i class="fas fa-database"></i>
              BambooHR Data Overview
            </h4>
            
            <!-- Employee Statistics -->
            <div class="data-stats-grid">
              <div class="data-stat-card">
                <div class="stat-icon">
                  <i class="fas fa-users"></i>
                </div>
                <div class="stat-content">
                  <h3>{{ selectedPlatform.employeeCount || 0 }}</h3>
                  <p>Total Employees</p>
                </div>
              </div>
              
              <div class="data-stat-card">
                <div class="stat-icon">
                  <i class="fas fa-building"></i>
                </div>
                <div class="stat-content">
                  <h3>{{ selectedPlatform.departmentCount || 0 }}</h3>
                  <p>Departments</p>
                </div>
              </div>
              
              <div class="data-stat-card">
                <div class="stat-icon">
                  <i class="fas fa-calendar-check"></i>
                </div>
                <div class="stat-content">
                  <h3>{{ selectedPlatform.projectsData?.time_off?.total_requests || 0 }}</h3>
                  <p>Time Off Requests</p>
                </div>
              </div>
              
              <div class="data-stat-card">
                <div class="stat-icon">
                  <i class="fas fa-star"></i>
                </div>
                <div class="stat-content">
                  <h3>{{ selectedPlatform.projectsData?.performance?.average_rating || 'N/A' }}</h3>
                  <p>Avg Performance Rating</p>
                </div>
              </div>
            </div>

            <!-- Departments List -->
            <div class="departments-section">
              <h5>Departments</h5>
              <div class="departments-list">
                <div 
                  v-for="dept in selectedPlatform.projectsData?.employees?.departments" 
                  :key="dept.id"
                  class="department-item"
                >
                  <div class="department-info">
                    <h6>{{ dept.name }}</h6>
                    <span class="employee-count">{{ dept.employee_count }} employees</span>
                  </div>
                  <div class="department-manager">
                    <i class="fas fa-user-tie"></i>
                    {{ dept.manager }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Recent Activity -->
            <div class="recent-activity-section">
              <h5>Recent Activity</h5>
              <div class="activity-list">
                <div class="activity-item">
                  <i class="fas fa-user-plus text-success"></i>
                  <span>{{ selectedPlatform.projectsData?.employees?.recent_hires?.length || 0 }} new hires this month</span>
                </div>
                <div class="activity-item">
                  <i class="fas fa-user-minus text-warning"></i>
                  <span>{{ selectedPlatform.projectsData?.employees?.terminations?.length || 0 }} terminations this month</span>
                </div>
                <div class="activity-item">
                  <i class="fas fa-clock text-info"></i>
                  <span>{{ selectedPlatform.projectsData?.time_off?.pending_approvals || 0 }} pending time off approvals</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Default Platform Information -->
          <div v-else>
            <div class="detail-section">
              <h4>Platform Information</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="detail-label">Name:</span>
                  <span class="detail-value">{{ selectedPlatform.name }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Category:</span>
                  <span class="detail-value">{{ selectedPlatform.category }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Type:</span>
                  <span class="detail-value">{{ selectedPlatform.type }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Status:</span>
                  <span class="detail-value">
                    <span class="status-badge" :class="selectedPlatform.status">
                      {{ selectedPlatform.status === 'connected' ? 'Connected' : 'Disconnected' }}
                    </span>
                  </span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <h4>Description</h4>
              <p>{{ selectedPlatform.description }}</p>
            </div>

            <div class="detail-section" v-if="selectedPlatform.features">
              <h4>Features</h4>
              <ul class="features-list">
                <li v-for="feature in selectedPlatform.features" :key="feature">
                  <i class="fas fa-check"></i>
                  {{ feature }}
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModal">Close</button>
          
          <!-- BambooHR Connection Form Actions -->
          <template v-if="selectedPlatform.showConnectionForm">
            <button 
              class="btn btn-success"
              @click="connectBambooHR"
            >
              <i class="fas fa-plug"></i>
              Connect to BambooHR
            </button>
          </template>
          
          <!-- Default Actions -->
          <template v-else>
            <button 
              v-if="selectedPlatform.status === 'disconnected'"
              class="btn btn-success"
              @click="connectPlatform(selectedPlatform)"
            >
              <i class="fas fa-plug"></i>
              {{ selectedPlatform.name === 'Jira' ? 'Open Jira Integration' : 'Connect' }}
            </button>
            <button 
              v-if="selectedPlatform.status === 'connected'"
              class="btn btn-danger"
              @click="disconnectPlatform(selectedPlatform)"
            >
              <i class="fas fa-unlink"></i>
              Disconnect
            </button>
            <button 
              v-if="selectedPlatform.status === 'connected' && selectedPlatform.hasProjectsData"
              class="btn btn-info"
              @click="viewProjectsData(selectedPlatform)"
            >
              <i class="fas fa-database"></i>
              {{ selectedPlatform.name === 'BambooHR' ? `View HR Data (${selectedPlatform.employeeCount || 0} employees)` : `View Projects Data (${selectedPlatform.projectsCount || 0})` }}
            </button>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { API_ENDPOINTS } from '../../config/api.js'
import integrationsDataService from '../../services/integrationsService.js' // NEW: Centralized integrations data service

export default {
  name: 'ExternalIntegration',
  setup() {
    const router = useRouter()
    const platforms = ref([])
    const selectedPlatform = ref(null)
    const loading = ref(false)
    const error = ref(null)

    // Computed properties for statistics
    const totalPlatforms = computed(() => platforms.value.length)
    const connectedPlatforms = computed(() => 
      platforms.value.filter(p => p.status === 'connected').length
    )
    const disconnectedPlatforms = computed(() => 
      platforms.value.filter(p => p.status === 'disconnected').length
    )
    const platformsWithData = computed(() => 
      platforms.value.filter(p => p.status === 'connected' && p.hasProjectsData).length
    )

    // Get JWT token from localStorage
    const getAuthToken = () => {
      return localStorage.getItem('jwt_token') || sessionStorage.getItem('jwt_token')
    }

    // Get current user ID
    const getCurrentUserId = () => {
      // This function is used in other parts of the code
      return localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
    }

    // API call helper
    const apiCall = async (url, options = {}) => {
      const token = getAuthToken()
      const defaultOptions = {
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        }
      }
      
      const response = await fetch(url, {
        ...defaultOptions,
        ...options,
        headers: { ...defaultOptions.headers, ...options.headers }
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return response.json()
    }

    // Load external applications from database
    const loadExternalApplications = async () => {
      loading.value = true
      error.value = null
      
      try {
        console.log('[Integrations] Checking for cached integration data...')
        
        // ==========================================
        // NEW: Check if data is already cached from HomeView prefetch
        // ==========================================
        if (integrationsDataService.hasValidCache()) {
          console.log('[Integrations] ✅ Using cached integration data from HomeView prefetch')
          const cachedApplications = integrationsDataService.getData('applications') || []
          
          platforms.value = cachedApplications.map(app => ({
            ...app,
            connecting: false,
            disconnecting: false,
            hasProjectsData: app.hasProjectsData || false
          }));
          
          console.log('Loaded platforms from cache:', platforms.value.length);
          
          // Check for stored projects data for each connected platform
          await checkStoredProjectsData();
          
          loading.value = false
          return
        }
        
        // ==========================================
        // Fallback: If cache is empty, wait for prefetch or fetch directly
        // ==========================================
        console.log('[Integrations] No cache found, checking for ongoing prefetch...')
        
        if (window.integrationsDataFetchPromise) {
          console.log('[Integrations] ⏳ Waiting for ongoing prefetch to complete...')
          await window.integrationsDataFetchPromise
          
          const cachedApplications = integrationsDataService.getData('applications') || []
          platforms.value = cachedApplications.map(app => ({
            ...app,
            connecting: false,
            disconnecting: false,
            hasProjectsData: app.hasProjectsData || false
          }));
          
          console.log('Loaded platforms from prefetch:', platforms.value.length);
          await checkStoredProjectsData();
          
          loading.value = false
          return
        }
        
        // Last resort: Fetch directly from API
        console.log('[Integrations] 🔄 Fetching integration data from API (cache miss)...')
        console.log('API Endpoint:', API_ENDPOINTS.EXTERNAL_APPLICATIONS)
        console.log('Auth Token:', getAuthToken() ? 'Present' : 'Missing')
        
        // Get current user ID
        const userId = getCurrentUserId()
        console.log('User ID:', userId)
        
        // Call the real API endpoint
        const response = await apiCall(`${API_ENDPOINTS.EXTERNAL_APPLICATIONS}?user_id=${userId}`)
        
        if (response.success) {
          console.log('✅ Successfully loaded external applications from database')
          console.log('Applications:', response.applications.length)
          console.log('Statistics:', response.statistics)
          
          platforms.value = response.applications.map(app => ({
            ...app,
            connecting: false,
            disconnecting: false,
            hasProjectsData: false // Will be updated when we check for stored data
          }));
          
          // Cache the fetched data for future use
          integrationsDataService.setData('applications', platforms.value)
          console.log('✅ Cached', platforms.value.length, 'applications')
          
          console.log('Loaded platforms from database:', platforms.value.length);
          
          // Check for stored projects data for each connected platform
          await checkStoredProjectsData();
        } else {
          throw new Error(response.error || 'Failed to load external applications')
        }
      } catch (err) {
        console.error('Error loading external applications:', err)
        error.value = `Failed to load external applications: ${err.message}`
        
        // Fallback to empty array if API fails
        platforms.value = []
      } finally {
        loading.value = false
      }
    }

    // Connect to external application
    const connectPlatform = async (platform) => {
      // Special handling for Jira - navigate in same tab
      if (platform.name === 'Jira') {
        const jiraUrl = '/integration/jira'
        window.location.href = jiraUrl
        
        console.log('✅ Jira connection opened in same tab')
        return
      }
// Special handling for Microsoft Sentinel - open in same tab
      if (platform.name === 'Microsoft Sentinel' || platform.name === 'Sentinel') {        
        const sentinelUrl = '/integration/sentinel'
        window.location.href = sentinelUrl
        console.log('✅ Navigating to Microsoft Sentinel integration')
        return
      }
      // Special handling for BambooHR - navigate in same tab
      if (platform.name === 'BambooHR') {
        const bamboohrUrl = '/integration/bamboohr'
        window.location.href = bamboohrUrl
        
        console.log('✅ BambooHR integration opened in same tab')
        return
      }

      // Special handling for Gmail - navigate to Gmail connect page
      if (platform.name === 'Gmail') {
      platform.connecting = true
      try {
        // Navigate to Gmail connect page
          router.push('/integrations/gmail/connect')
         
          // Update platform status to connected (simplified for demo)
          setTimeout(() => {
            platform.status = 'connected'
            platform.lastSync = new Date().toISOString()
            platform.connecting = false
            console.log('✅ Gmail connection initiated')
          }, 1000)
        } catch (err) {
          console.error('❌ Failed to navigate to Gmail integration:', err)
          error.value = 'Failed to open Gmail integration. Please try again.'
          platform.connecting = false
        }
       
        return
      }
 
      platform.connecting = true
      try {
        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
        const response = await apiCall(API_ENDPOINTS.EXTERNAL_APPLICATIONS_CONNECT, {
          method: 'POST',
          body: JSON.stringify({
            application_id: platform.id,
            user_id: userId,
            connection_token: 'mock_token_' + Date.now(), // Mock token for demo
            refresh_token: 'mock_refresh_' + Date.now(),
            token_expires_at: new Date(Date.now() + 3600000).toISOString() // 1 hour from now
          })
        })

        if (response.success) {
          platform.status = 'connected'
          platform.lastSync = new Date().toISOString()
          // Show success message
          console.log(response.message)
        } else {
          throw new Error(response.error || 'Failed to connect')
        }
      } catch (err) {
        console.error('Failed to connect platform:', err)
        error.value = err.message
      } finally {
        platform.connecting = false
      }
    }

    // Disconnect from external application
    const disconnectPlatform = async (platform) => {
      platform.disconnecting = true
      try {
        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
        const response = await apiCall(API_ENDPOINTS.EXTERNAL_APPLICATIONS_DISCONNECT, {
          method: 'POST',
          body: JSON.stringify({
            application_id: platform.id,
            user_id: userId
          })
        })

        if (response.success) {
          platform.status = 'disconnected'
          platform.lastSync = null
          // Show success message
          console.log(response.message)
        } else {
          throw new Error(response.error || 'Failed to disconnect')
        }
      } catch (err) {
        console.error('Failed to disconnect platform:', err)
        error.value = err.message
      } finally {
        platform.disconnecting = false
      }
    }

    // View platform details
    const viewPlatformDetails = async (platform) => {
      try {
        const response = await apiCall(API_ENDPOINTS.EXTERNAL_APPLICATION_DETAILS(platform.id))
        
        if (response.success) {
          selectedPlatform.value = {
            ...response.application,
            connecting: false,
            disconnecting: false
          }
        } else {
          throw new Error(response.error || 'Failed to load platform details')
        }
      } catch (err) {
        console.error('Error loading platform details:', err)
        error.value = err.message
      }
    }

    // Close modal
    const closeModal = () => {
      selectedPlatform.value = null
    }

    // Handle BambooHR connection
    const connectBambooHR = async () => {
      if (!selectedPlatform.value || !selectedPlatform.value.connectionForm) {
        return
      }

      const form = selectedPlatform.value.connectionForm
      if (!form.company_domain || !form.api_key) {
        error.value = 'Please fill in company domain and API key'
        return
      }

      try {
        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
        const response = await apiCall(API_ENDPOINTS.EXTERNAL_APPLICATIONS_CONNECT, {
          method: 'POST',
          body: JSON.stringify({
            application_id: selectedPlatform.value.id,
            user_id: userId,
            connection_token: form.api_key,
            company_domain: form.company_domain,
            employee_fields: form.employee_fields,
            department_fields: form.department_fields,
            sync_frequency: form.sync_frequency,
            token_expires_at: new Date(Date.now() + 365 * 24 * 3600000).toISOString() // 1 year from now
          })
        })

        if (response.success) {
          selectedPlatform.value.status = 'connected'
          selectedPlatform.value.lastSync = new Date().toISOString()
          selectedPlatform.value.showConnectionForm = false
          console.log('✅ BambooHR connected successfully')
          
          // Find the platform in the list and update it
          const platformIndex = platforms.value.findIndex(p => p.id === selectedPlatform.value.id)
          if (platformIndex !== -1) {
            platforms.value[platformIndex].status = 'connected'
            platforms.value[platformIndex].lastSync = new Date().toISOString()
          }
          
          // Check for stored data after connection
          setTimeout(async () => {
            await checkStoredProjectsData()
          }, 2000)
        } else {
          throw new Error(response.error || 'Failed to connect to BambooHR')
        }
      } catch (err) {
        console.error('Failed to connect to BambooHR:', err)
        error.value = err.message
      }
    }

    // Check for stored projects data
    const checkStoredProjectsData = async () => {
      try {
        console.log('🔍 Checking stored projects data for all platforms...')
        
        // Get current user ID for logging purposes
        const userId = getCurrentUserId();
        console.log(`🔑 Checking data for user ID: ${userId}`);
        
        for (const platform of platforms.value) {
          platform.hasProjectsData = false;
          
          // For connected platforms, check for stored data
          if (platform.status === 'connected') {
            console.log(`📊 Platform ${platform.name} is connected, checking for stored data`);
            
            try {
              // Check for stored data based on platform type
              if (platform.name === 'Jira') {
                // Check JIRA stored data
                const jiraResponse = await apiCall(`${API_ENDPOINTS.JIRA_STORED_DATA}?user_id=${userId}`);
                if (jiraResponse.success && jiraResponse.data && jiraResponse.data.projects) {
                  platform.hasProjectsData = true;
                  platform.projectsCount = jiraResponse.data.projects.length;
                  platform.lastDataUpdate = new Date().toISOString();
                  console.log(`✅ JIRA stored data found: ${platform.projectsCount} projects`);
                }
              } else if (platform.name === 'BambooHR') {
                // Check BambooHR stored data
                const bamboohrResponse = await apiCall(`${API_ENDPOINTS.BAMBOOHR_STORED_DATA}?user_id=${userId}`);
                if (bamboohrResponse.success && bamboohrResponse.data) {
                  platform.hasProjectsData = true;
                  platform.employeeCount = bamboohrResponse.data.employees?.length || 0;
                  platform.departmentCount = bamboohrResponse.data.departments?.length || 0;
                  platform.lastDataUpdate = new Date().toISOString();
                  console.log(`✅ BambooHR stored data found: ${platform.employeeCount} employees`);
                }
              }
            } catch (err) {
              console.log(`ℹ️ No stored data found for ${platform.name}:`, err.message);
              platform.hasProjectsData = false;
            }
          } else {
            // For disconnected platforms
            platform.hasProjectsData = false;
            console.log(`ℹ️ Platform ${platform.name} is disconnected`);
          }
        }
        
        console.log('📊 Final platforms data:', platforms.value.map(p => ({
          name: p.name,
          status: p.status,
          hasProjectsData: p.hasProjectsData,
          projectsCount: p.projectsCount || 0,
          employeeCount: p.employeeCount || 0,
          departmentCount: p.departmentCount || 0
        })));
      } catch (err) {
        console.error('Error checking stored projects data:', err);
      }
    }

    // View projects data
    const viewProjectsData = async (platform) => {
      try {
        if (platform.name === 'Jira') {
          // Open Jira integration page with stored data
          const jiraUrl = '/integration/jira?loadStoredData=true'
          window.open(jiraUrl, '_blank')
        } else if (platform.name === 'BambooHR') {
          // Navigate to BambooHR integration page with stored data in same tab
          const bamboohrUrl = '/integration/bamboohr?loadStoredData=true'
          window.location.href = bamboohrUrl
          } else if (platform.name === 'Gmail') {
          // Navigate to Gmail integration page with stored data
          const gmailUrl = '/integrations/gmail?loadStoredData=true'
          router.push(gmailUrl)
        } else {
          // For other platforms, show a message
          alert(`Projects data viewing for ${platform.name} is not yet implemented.`)
        }
      } catch (err) {
        console.error('Error viewing projects data:', err)
        error.value = 'Error viewing projects data'
      }
    }

    // Refresh platform status
    const refreshPlatforms = async () => {
      try {
        console.log('Refreshing platform status from database...');
        
        // Call the refresh API endpoint
        const response = await apiCall(API_ENDPOINTS.EXTERNAL_APPLICATIONS_REFRESH_STATUS, {
          method: 'POST'
        });
        
        if (response.success) {
          console.log('✅ Platform status refreshed:', response.message);
          
          // Reload applications from database
          await loadExternalApplications();
        } else {
          throw new Error(response.error || 'Failed to refresh status');
        }
      } catch (err) {
        console.error('Error refreshing platform status:', err);
        error.value = `Failed to refresh status: ${err.message}`;
      }
    }

    // Format date helper
    const formatDate = (date) => {
      if (!date) return 'Never'
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(new Date(date))
    }

    // Load data on component mount
    onMounted(() => {
      console.log('External Integration component mounted')
      loadExternalApplications()
    })

    return {
      platforms,
      selectedPlatform,
      loading,
      error,
      totalPlatforms,
      connectedPlatforms,
      disconnectedPlatforms,
      platformsWithData,
      connectPlatform,
      disconnectPlatform,
      viewPlatformDetails,
      closeModal,
      refreshPlatforms,
      formatDate,
      checkStoredProjectsData,
      viewProjectsData,
      connectBambooHR
    }
  }
}
</script>

<style scoped>
@import './external_integration.css';

.stat-card.data {
  background: #ffffff;
  color: #1f2937;
}

.stat-card.data .stat-icon {
  background: #f3f4f6;
  color: #6b7280;
}

.btn-info {
  background-color: #4f8cff;
  border-color: #4f8cff;
}

.btn-info:hover {
  background-color: #3d7aff;
  border-color: #3d7aff;
}

/* BambooHR specific styles */
.connection-form-section {
  padding: 20px 0;
}

.connection-form-section h4 {
  color: #333;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  color: #333;
}

.form-control {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-control:focus {
  outline: none;
  border-color: #4f8cff;
  box-shadow: 0 0 0 2px rgba(79, 140, 255, 0.2);
}

.form-text {
  display: block;
  margin-top: 5px;
  font-size: 12px;
  color: #666;
}

.data-viewer-section {
  padding: 20px 0;
}

.data-viewer-section h4 {
  color: #333;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.data-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 25px;
}

.data-stat-card {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  border: 1px solid #dee2e6;
}

.data-stat-card .stat-icon {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #4f8cff 0%, #3a73d9 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.data-stat-card .stat-content h3 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #333;
}

.data-stat-card .stat-content p {
  margin: 5px 0 0 0;
  color: #666;
  font-size: 14px;
}

.departments-section {
  margin-bottom: 25px;
}

.departments-section h5 {
  color: #333;
  margin-bottom: 15px;
  font-size: 16px;
}

.departments-list {
  display: grid;
  gap: 10px;
}

.department-item {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.department-info h6 {
  margin: 0 0 5px 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

.employee-count {
  font-size: 12px;
  color: #666;
}

.department-manager {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.recent-activity-section h5 {
  color: #333;
  margin-bottom: 15px;
  font-size: 16px;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 14px;
}

.activity-item i {
  width: 16px;
  text-align: center;
}

.text-success {
  color: #4f8cff !important;
}

.text-warning {
  color: #4f8cff !important;
}

.text-info {
  color: #4f8cff !important;
}
</style>