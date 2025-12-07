<template>
  <div class="bamboohr-container">
    <div class="page-header">
      <button @click="goBack" class="back-button">
        <i class="fas fa-arrow-left"></i>
        Back to Integrations
      </button>
      <h1>Connect to BambooHR</h1>
    </div>
    
    <!-- Domain Input Section -->
    <div v-if="!accessToken && !showOAuthFlow" class="domain-input-section">
      <div class="domain-form">
        <h3>
          <i class="fas fa-building"></i>
          Enter Your BambooHR Domain
        </h3>
        <div class="form-group">
          <label for="domain-input">Company Domain</label>
          <div class="domain-input-wrapper">
            <input 
              v-model="companyDomain" 
              type="text" 
              id="domain-input"
              placeholder="yourcompany" 
              class="domain-input"
              @keyup.enter="initiateOAuth"
            >
            <span class="domain-suffix">.bamboohr.com</span>
          </div>
          <small class="form-help">Enter your BambooHR subdomain (e.g., "acme" for acme.bamboohr.com)</small>
        </div>
        <button 
          @click="initiateOAuth" 
          class="btn btn-primary btn-large" 
          :disabled="!companyDomain || loading"
        >
          <i class="fas fa-external-link-alt"></i>
          Connect to BambooHR
        </button>
      </div>
    </div>

    <!-- OAuth Flow Section -->
    <div v-if="showOAuthFlow" class="oauth-section">
      <div class="oauth-info">
        <i class="fas fa-spinner fa-spin"></i>
        <h3>Connecting to {{ companyDomain }}.bamboohr.com</h3>
        <p>You will be redirected to BambooHR for authentication...</p>
      </div>
    </div>
    
    <!-- Connection Status -->
    <div v-if="accessToken" class="connection-section">
      <div class="connection-status">
        <i class="fas fa-check-circle"></i>
        <span>Connected to BambooHR!</span>
        <div v-if="companyInfo" class="company-info">
          <strong>Company:</strong> {{ companyInfo.name || companyDomain + '.bamboohr.com' }}
        </div>
      </div>
      <div class="action-buttons">
        <button 
          @click="handleFetchEmployees" 
          class="btn btn-secondary"
          :disabled="loading"
        >
          <i class="fas fa-users" :class="{ 'fa-spin': loading }"></i>
          {{ loading ? 'Fetching...' : 'Fetch Employee Data' }}
        </button>
        <button 
          @click="handleDisconnect" 
          class="btn btn-outline"
          :disabled="loading"
        >
          <i class="fas fa-unlink"></i>
          Disconnect
        </button>
      </div>
    </div>
    
    <!-- Connected Status -->
    <div v-else class="connection-section">
      <div class="connection-status">
        <i class="fas fa-check-circle"></i>
        <span>✅ Connected to BambooHR!</span>
        <div v-if="companyInfo" class="company-info">
          <strong>Company:</strong> {{ companyInfo.name || 'BambooHR' }}
        </div>
      </div>
      <div class="action-buttons">
        <button 
          @click="handleFetchEmployees" 
          class="btn btn-secondary"
          :disabled="loading"
        >
          <i class="fas fa-users" :class="{ 'fa-spin': loading }"></i>
          {{ loading ? 'Fetching...' : 'Fetch Employee Data' }}
        </button>
        <button 
          @click="handleDisconnect" 
          class="btn btn-outline"
          :disabled="loading"
        >
          <i class="fas fa-unlink"></i>
          Disconnect
        </button>
      </div>
    </div>
    
    <!-- Loading State -->
    <div v-if="loading" class="loading-section">
      <i class="fas fa-spinner fa-spin"></i>
      <span>{{ loadingMessage }}</span>
    </div>
    
    <!-- Error Display -->
    <div v-if="error" class="error-section">
      <i class="fas fa-exclamation-triangle"></i>
      <strong>Error:</strong> {{ error }}
      <button @click="clearError" class="error-close">
        <i class="fas fa-times"></i>
      </button>
    </div>
    
    <!-- Employee Data Display -->
    <div v-if="employeeData && Object.keys(employeeData).length > 0" class="data-section">
      <!-- Statistics Cards -->
      <div class="stats-section">
        <h3>
          <i class="fas fa-chart-bar"></i>
          Company Statistics
        </h3>
        <div class="stats-grid">
          <div class="stat-card employees">
            <div class="stat-icon">
              <i class="fas fa-users"></i>
            </div>
            <div class="stat-content">
              <h4>{{ (employeeData.employees?.employees || employeeData.employees || []).length }}</h4>
              <p>Total Employees</p>
            </div>
          </div>
          
          <div class="stat-card departments">
            <div class="stat-icon">
              <i class="fas fa-building"></i>
            </div>
            <div class="stat-content">
              <h4>{{ uniqueDepartments.length }}</h4>
              <p>Departments</p>
            </div>
          </div>
          
          <div class="stat-card active">
            <div class="stat-icon">
              <i class="fas fa-user-check"></i>
            </div>
            <div class="stat-content">
              <h4>{{ (employeeData.employees?.employees || employeeData.employees || []).length }}</h4>
              <p>Active Employees</p>
            </div>
          </div>
          
          <div class="stat-card recent">
            <div class="stat-icon">
              <i class="fas fa-user-plus"></i>
            </div>
            <div class="stat-content">
              <h4>0</h4>
              <p>Recent Hires</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Current User Profile
      <div v-if="currentUser" class="user-profile-section">
        <h3>
          <i class="fas fa-user"></i>
          Your Profile
        </h3>
        <div class="user-profile-card">
          <div class="user-info">
            <div class="user-name">{{ currentUser.displayName || `${currentUser.firstName} ${currentUser.lastName}` }}</div>
            <div class="user-title">{{ currentUser.jobTitle || 'N/A' }}</div>
            <div class="user-department">{{ currentUser.department || 'N/A' }}</div>
            <div class="user-email">{{ currentUser.workEmail || 'N/A' }}</div>
          </div>
          <div class="user-details">
            <div class="detail-item">
              <span class="detail-label">Employee ID:</span>
              <span class="detail-value">{{ currentUser.id || 'N/A' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Hire Date:</span>
              <span class="detail-value">{{ formatDate(currentUser.hireDate) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Status:</span>
              <span class="detail-value">{{ currentUser.status || 'Active' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Location:</span>
              <span class="detail-value">{{ currentUser.location || 'N/A' }}</span>
            </div>
          </div>
        </div>
      </div>
 -->
      <!-- Departments List -->
      <div v-if="employeeData.departments && employeeData.departments.length > 0" class="departments-section">
        <h3>
          <i class="fas fa-sitemap"></i>
          Departments ({{ employeeData.departments.length }})
        </h3>
        <div class="departments-grid">
          <div 
            v-for="dept in employeeData.departments" 
            :key="dept.name"
            class="department-card"
          >
            <div class="dept-header">
              <h4>{{ dept.name }}</h4>
              <span class="employee-count">{{ dept.employeeCount || 0 }} employees</span>
            </div>
            <div v-if="dept.manager" class="dept-manager">
              <i class="fas fa-user-tie"></i>
              <span>Manager: {{ dept.manager }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Employee Directory -->
      <div v-if="filteredEmployees && filteredEmployees.length > 0" class="employees-section">
        <h3>
          <i class="fas fa-address-book"></i>
          Employee Directory ({{ filteredEmployees.length }})
        </h3>
        
        <!-- Search and Filter -->
        <div class="directory-controls">
          <div class="search-box">
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Search employees..." 
              class="search-input"
            >
            <i class="fas fa-search search-icon"></i>
          </div>
          <div class="filter-controls">
            <select v-model="departmentFilter" class="filter-select">
              <option value="">All Departments</option>
              <option v-for="dept in uniqueDepartments" :key="dept" :value="dept">
                {{ dept }}
              </option>
            </select>
          </div>
        </div>

        <!-- Employee List View (Similar to Jira) -->
        <div class="employees-list-view">
          <div class="employees-table-wrapper">
            <table class="employees-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>ID</th>
                  <th>Job Title</th>
                  <th>Department</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Location</th>
                  <th>Supervisor</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="employee in filteredEmployees" 
                  :key="employee.id"
                  class="clickable-row"
                >
                  <td class="employee-name" data-label="Name">
                    <div class="employee-name-content">
                      <div class="employee-photo">
                        <img 
                          v-if="employee.photoUrl" 
                          :src="employee.photoUrl" 
                          :alt="employee.displayName || `${employee.firstName} ${employee.lastName}`"
                          class="employee-avatar"
                        >
                        <div v-else class="employee-avatar-placeholder">
                          <i class="fas fa-user"></i>
                        </div>
                      </div>
                      <div class="employee-name-text">
                        {{ employee.displayName || `${employee.firstName} ${employee.lastName}` }}
                      </div>
                    </div>
                  </td>
                  <td data-label="ID">
                    <span class="employee-id-badge">#{{ employee.id }}</span>
                  </td>
                  <td data-label="Job Title">{{ employee.jobTitle || 'N/A' }}</td>
                  <td data-label="Department">{{ employee.department || 'N/A' }}</td>
                  <td data-label="Email">
                    <a v-if="employee.workEmail" :href="`mailto:${employee.workEmail}`" class="employee-email-link">
                      {{ employee.workEmail }}
                    </a>
                    <span v-else>N/A</span>
                  </td>
                  <td data-label="Phone">{{ employee.workPhone || 'N/A' }}</td>
                  <td data-label="Location">{{ employee.location || 'N/A' }}</td>
                  <td data-label="Supervisor">{{ employee.supervisor || 'N/A' }}</td>
                  <td data-label="Action" class="action-cell">
                    <button 
                      @click="handleAddUser(employee)" 
                      :disabled="addedUsers.has(employee.id)"
                      :class="['add-user-btn', addedUsers.has(employee.id) ? 'added' : '']"
                      :title="addedUsers.has(employee.id) ? 'Already Added' : 'Add to Users Database'"
                    >
                      <i :class="addedUsers.has(employee.id) ? 'fas fa-check' : 'fas fa-plus'"></i>
                      {{ addedUsers.has(employee.id) ? 'Added' : 'Add' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Empty State -->
    <div v-if="accessToken && !loading && !employeeData" class="empty-state">
      <i class="fas fa-users"></i>
      <p>No employee data found. Click "Fetch Employee Data" to load information.</p>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { API_ENDPOINTS } from '../../../config/api.js'

export default {
  name: 'BambooHRIntegration',
  setup() {
    // Reactive state
    const accessToken = ref(null)
    const loading = ref(false)
    const loadingMessage = ref('Loading...')
    const error = ref(null)
    const employeeData = ref({})
    const currentUser = ref(null)
    const companyInfo = ref(null)
    const searchQuery = ref('')
    const departmentFilter = ref('')
    const companyDomain = ref('')
    const showOAuthFlow = ref(false)
    const addedUsers = ref(new Set()) // Track added users by ID

    // Get current user ID
    const getCurrentUserId = () => {
      return localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
    }

    const uniqueDepartments = computed(() => {
      // Handle the JSON structure: employeeData.value.employees.employees
      const employees = employeeData.value?.employees?.employees || employeeData.value?.employees || []
      if (!Array.isArray(employees)) return []
      const departments = [...new Set(employees.map(emp => emp.department).filter(Boolean))]
      return departments.sort()
    })

    const filteredEmployees = computed(() => {
      // Handle the JSON structure: employeeData.value.employees.employees
      const employees = employeeData.value?.employees?.employees || employeeData.value?.employees || []
      if (!Array.isArray(employees)) return []
      
      let filtered = employees
      
      // Filter by search query
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(emp => 
          (emp.displayName || `${emp.firstName} ${emp.lastName}`).toLowerCase().includes(query) ||
          (emp.workEmail || '').toLowerCase().includes(query) ||
          (emp.jobTitle || '').toLowerCase().includes(query) ||
          (emp.department || '').toLowerCase().includes(query)
        )
      }
      
      // Filter by department
      if (departmentFilter.value) {
        filtered = filtered.filter(emp => emp.department === departmentFilter.value)
      }
      
      return filtered
    })

    // API call helper
    const apiCall = async (url, options = {}) => {
      const token = localStorage.getItem('jwt_token') || sessionStorage.getItem('jwt_token')
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

    // Initiate OAuth flow with domain
    const initiateOAuth = async () => {
      if (!companyDomain.value) {
        error.value = 'Please enter your company domain'
        return
      }

      showOAuthFlow.value = true
      loading.value = true
      error.value = null

      try {
        console.log('🔌 Initiating BambooHR OAuth flow for domain:', companyDomain.value)
        
        // Store domain for later use
        localStorage.setItem('bamboohr_domain', companyDomain.value)
        
        // Redirect to Django backend OAuth endpoint with domain
        const bamboohrOAuthUrl = `${API_ENDPOINTS.BAMBOOHR_OAUTH}?user_id=${getCurrentUserId()}&subdomain=${companyDomain.value}`
        
        console.log('🔗 Redirecting to Django OAuth endpoint:', bamboohrOAuthUrl)
        // Use window.location.href instead of window.open to avoid popup
        window.location.href = bamboohrOAuthUrl
        
      } catch (err) {
        console.error('❌ Error initiating OAuth:', err)
        error.value = `Failed to initiate OAuth: ${err.message}`
        showOAuthFlow.value = false
        loading.value = false
      }
    }

    // Handle connection to BambooHR (legacy method)
    const handleConnectClick = async () => {
      console.log('🔌 Connect to BambooHR button clicked!')
      
      if (!companyDomain.value) {
        error.value = 'Please enter your company domain first'
        return
      }
      
      await initiateOAuth()
    }

    // Fetch employee data
    const handleFetchEmployees = async () => {
      if (!accessToken.value) {
        error.value = 'Not connected to BambooHR'
        return
      }

      loading.value = true
      loadingMessage.value = 'Fetching employee data...'
      error.value = null

      try {
        console.log('📡 Fetching employee data from BambooHR...')
        
        const response = await apiCall(`${API_ENDPOINTS.BAMBOOHR_EMPLOYEES}`, {
          method: 'POST',
          body: JSON.stringify({
            user_id: getCurrentUserId(),
            access_token: accessToken.value,
            action: 'fetch_employees'
          })
        })

        if (response.success) {
          employeeData.value = response.data
          currentUser.value = response.current_user
          console.log('✅ Employee data fetched successfully')
          console.log('📊 Data:', response.data)
          
          // Save data to database
          await saveEmployeeDataToDatabase(response.data)
        } else {
          throw new Error(response.error || 'Failed to fetch employee data')
        }
      } catch (err) {
        console.error('❌ Error fetching employee data:', err)
        error.value = `Failed to fetch data: ${err.message}`
      } finally {
        loading.value = false
      }
    }

    // Save employee data to database
    const saveEmployeeDataToDatabase = async (data) => {
      try {
        console.log('💾 Saving employee data to database...')
        
        const response = await apiCall(`${API_ENDPOINTS.BAMBOOHR_SYNC_DATA}`, {
          method: 'POST',
          body: JSON.stringify({
            user_id: getCurrentUserId(),
            employee_data: data,
            current_user: currentUser.value,
            access_token: accessToken.value
          })
        })

        if (response.success) {
          console.log('✅ Employee data saved to database')
        } else {
          console.error('❌ Failed to save employee data:', response.error)
        }
      } catch (err) {
        console.error('❌ Error saving employee data:', err)
      }
    }

    // Handle disconnect
    const handleDisconnect = () => {
      accessToken.value = null
      employeeData.value = {}
      currentUser.value = null
      companyInfo.value = null
      searchQuery.value = ''
      departmentFilter.value = ''
      error.value = null
      console.log('🔌 Disconnected from BambooHR')
    }
    
    // Handle add user to database
    const handleAddUser = async (employee) => {
      if (addedUsers.value.has(employee.id)) {
        console.log('ℹ️ User already added:', employee.displayName)
        return
      }
      
      try {
        console.log('➕ Adding user to database:', employee.displayName)
        
        const response = await apiCall(`${API_ENDPOINTS.BAMBOOHR_ADD_USER}`, {
          method: 'POST',
          body: JSON.stringify({
            employee: employee,
            framework_id: 1, // Default framework
            user_id: getCurrentUserId() // Send current user ID
          })
        })
        
        if (response.success) {
          addedUsers.value.add(employee.id)
          console.log('✅ User added successfully:', response.message)
          error.value = null
        } else if (response.already_exists) {
          addedUsers.value.add(employee.id)
          console.log('ℹ️ User already exists in database')
          error.value = 'User already exists in database'
        } else {
          console.error('❌ Failed to add user:', response.error)
          error.value = `Failed to add user: ${response.error}`
        }
      } catch (err) {
        console.error('❌ Error adding user:', err)
        error.value = `Error adding user: ${err.message}`
      }
    }

    // Clear error
    const clearError = () => {
      error.value = null
    }

    // Format date helper
    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      try {
        return new Date(dateString).toLocaleDateString()
      } catch {
        return dateString
      }
    }

    // Go back to external integrations
    const goBack = () => {
      window.location.href = '/integration/external'
    }

    // Load stored data on mount
    onMounted(async () => {
      console.log('BambooHR Integration component mounted')
      
      const urlParams = new URLSearchParams(window.location.search)
      const token = urlParams.get('token')
      const success = urlParams.get('success')
      const loadStoredDataParam = urlParams.get('loadStoredData')
      const subdomainParam = urlParams.get('subdomain')
      const errorParam = urlParams.get('error')
      
      // Handle OAuth errors
      if (errorParam) {
        console.error('❌ OAuth error received:', errorParam)
        error.value = `OAuth failed: ${errorParam}`
        showOAuthFlow.value = false
        loading.value = false
        
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname)
        return
      }
      
      // Restore company domain from localStorage or URL param
      const storedDomain = localStorage.getItem('bamboohr_domain')
      if (subdomainParam) {
        companyDomain.value = subdomainParam
        localStorage.setItem('bamboohr_domain', subdomainParam)
      } else if (storedDomain) {
        companyDomain.value = storedDomain
      }
      
      // Handle OAuth success - load stored data from database
      if (success === 'true') {
        console.log('🎉 OAuth successful! Loading stored BambooHR data from database...')
        accessToken.value = 'bamboohr_connected' // Set a flag to indicate OAuth was successful
        showOAuthFlow.value = false
        
        // Set company info
        if (companyDomain.value) {
          companyInfo.value = { name: companyDomain.value + '.bamboohr.com' }
        }
        
        // Load stored data from database
        await loadStoredData()
        
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname)
        console.log('✅ OAuth success handled and URL cleaned up')
      } else if (token) {
        // Legacy support for token in URL (for backward compatibility)
        console.log('🎉 Access token found in URL from BambooHR OAuth redirect:', token.substring(0, 20) + '...')
        accessToken.value = token
        showOAuthFlow.value = false
        
        // Save OAuth connection to backend
        await saveBambooHRConnection(token)
        
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname)
        console.log('✅ Token set and URL cleaned up')
        
        // Set company info
        if (companyDomain.value) {
          companyInfo.value = { name: companyDomain.value + '.bamboohr.com' }
        }
        
        // Fetch employee data after successful connection
        await handleFetchEmployees()
      } else if (loadStoredDataParam === 'true') {
        console.log('📊 Loading stored employee data from database...')
        await loadStoredData()
      } else {
        console.log('ℹ️ No access token found in URL, checking for stored data...')
        await loadStoredData()
      }
    })

    // Save BambooHR connection to backend
    const saveBambooHRConnection = async (token) => {
      try {
        console.log('💾 Saving BambooHR connection to backend...')
        
        const response = await apiCall(`${API_ENDPOINTS.BAMBOOHR_OAUTH_CALLBACK}`, {
          method: 'POST',
          body: JSON.stringify({
            access_token: token,
            user_id: getCurrentUserId(),
            account_info: {
              account_id: 'bamboohr_account_' + Date.now(),
              account_type: 'bamboohr',
              name: 'BambooHR User'
            }
          })
        })

        if (response.success) {
          console.log('✅ BambooHR connection saved to backend:', response)
        } else {
          console.error('❌ Failed to save BambooHR connection:', response.error)
        }
      } catch (error) {
        console.error('❌ Error saving BambooHR connection:', error)
      }
    }

    // Load stored data
    const loadStoredData = async () => {
      try {
        console.log('📊 Loading stored BambooHR data...')
        
        const response = await apiCall(`${API_ENDPOINTS.BAMBOOHR_STORED_DATA}?user_id=${getCurrentUserId()}`)
        
        if (response.success && response.has_data) {
          accessToken.value = 'bamboohr_connected'
          employeeData.value = response.employee_data || {}
          currentUser.value = response.current_user
          companyInfo.value = response.company_info
          
          // Populate addedUsers from projects_data
          if (response.added_users && Array.isArray(response.added_users)) {
            addedUsers.value = new Set(response.added_users)
            console.log('✅ Loaded added users:', Array.from(addedUsers.value))
          }
          
          // Log the structure for debugging
          console.log('✅ Loaded stored BambooHR data:', {
            employeeData: employeeData.value,
            employeeCount: (employeeData.value?.employees?.employees || employeeData.value?.employees || []).length,
            totalEmployees: response.total_employees,
            addedUsers: Array.from(addedUsers.value)
          })
        } else {
          console.log('ℹ️ No stored BambooHR data found')
        }
      } catch (err) {
        console.error('❌ Error loading stored data:', err)
      }
    }

    return {
      accessToken,
      loading,
      loadingMessage,
      error,
      employeeData,
      currentUser,
      companyInfo,
      searchQuery,
      departmentFilter,
      companyDomain,
      showOAuthFlow,
      addedUsers,
      uniqueDepartments,
      filteredEmployees,
      initiateOAuth,
      handleConnectClick,
      handleFetchEmployees,
      handleDisconnect,
      handleAddUser,
      clearError,
      formatDate,
      goBack
    }
  }
}
</script>

<style scoped>
@import './bamboohr.css';
</style>