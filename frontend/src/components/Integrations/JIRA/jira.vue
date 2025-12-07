<template>
  <div class="jira-container">
    <div class="page-header">
      <button @click="goBack" class="back-button">
        <i class="fas fa-arrow-left"></i>
        Back to Integrations
      </button>
      <h1>Connect to Jira</h1>
    </div>
    
    <!-- Connection Status -->
      <div v-if="!accessToken" class="connection-section">
        <button @click="handleConnectClick" class="btn btn-primary" :disabled="loading">
          <i class="fas fa-external-link-alt"></i>
          Connect to Jira (OAuth)
        </button>
        <button @click="handleLoadStoredData" class="btn btn-secondary" :disabled="loading" style="margin-left: 10px;">
          <i class="fas fa-database"></i>
          Load Previous Connection
        </button>
        <p class="connection-info">
          <i class="fas fa-info-circle"></i>
          Click "Connect to Jira" for new authentication or "Load Previous Connection" to restore saved data
        </p>
      </div>
    
    <!-- Account Selection (only show if manual selection needed) -->
    <div v-if="accessToken && jiraResources && jiraResources.length > 1 && !selectedCloudId && !loading" class="account-selection-section">
      <h3>
        <i class="fas fa-users"></i>
        Select Jira Account
      </h3>
      <p class="selection-info">
        Multiple Jira accounts found. Please select which account you want to connect to:
      </p>
      <div class="accounts-list">
        <div 
          v-for="resource in jiraResources" 
          :key="resource.id"
          @click="handleAccountSelect(resource)"
          class="account-item"
        >
          <div class="account-info">
            <div class="account-name">{{ resource.name }}</div>
            <div class="account-url">{{ resource.url }}</div>
            <div class="account-scopes">
              <span v-for="scope in resource.scopes" :key="scope" class="scope-badge">
                {{ scope }}
              </span>
            </div>
          </div>
          <div class="account-actions">
            <i class="fas fa-chevron-right"></i>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else-if="accessToken && (selectedCloudId || (jiraResources && jiraResources.length <= 1))" class="connection-section">
      <div class="connection-status">
        <i class="fas fa-check-circle"></i>
        <span>Connected to Jira!</span>
        <div v-if="selectedAccount" class="selected-account-info">
          <strong>Account:</strong> {{ selectedAccount.name }}
          <br>
          <small>{{ selectedAccount.url }}</small>
        </div>
      </div>
      <button 
        v-if="!selectedProject" 
        @click="handleFetchProjects" 
        class="btn btn-secondary"
        :disabled="loading"
      >
        <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
        {{ loading ? 'Fetching...' : 'Fetch Projects' }}
      </button>
      <button 
        v-if="jiraResources && jiraResources.length > 1"
        @click="handleChangeAccount" 
        class="btn btn-outline"
        :disabled="loading"
      >
        <i class="fas fa-exchange-alt"></i>
        Change Account
      </button>
    </div>
    
    <!-- Loading State -->
    <div v-if="loading" class="loading-section">
      <i class="fas fa-spinner fa-spin"></i>
      <span>Loading projects...</span>
    </div>
    
    <!-- Error Display -->
    <div v-if="error" class="error-section">
      <i class="fas fa-exclamation-triangle"></i>
      <strong>Error:</strong> {{ error }}
    </div>
    
    <!-- Projects List View -->
    <div v-if="projects && projects.length > 0 && !selectedProject" class="projects-section">
      <h3>Available Projects:</h3>
      <div class="projects-list-view">
        <div class="projects-table-wrapper">
          <table class="projects-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Key</th>
                <th>Type</th>
                <th>Description</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="project in projects" 
                :key="project.id" 
                @click="handleProjectClick(project)"
                class="clickable-row"
              >
                <td class="project-name" data-label="Name">{{ project.name }}</td>
                <td data-label="Key">
                  <span class="project-key-badge">{{ project.key }}</span>
                </td>
                <td data-label="Type">{{ project.projectTypeKey }}</td>
                <td class="project-description" data-label="Description">{{ truncateDescription(project.description) }}</td>
                <td data-label="Actions">
                  <button class="project-action-btn" @click.stop="handleAddProject(project)">
                    <i class="fas fa-plus"></i>
                  </button>
                  <button class="project-action-btn" @click.stop="handleProjectClick(project)">
                    <i class="fas fa-eye"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    
    <!-- Project Details View -->
    <div v-if="selectedProject" class="project-details-section">
      <div class="back-button">
        <button @click="handleBackToProjects" class="btn btn-secondary">
          <i class="fas fa-arrow-left"></i>
          Back to Projects
        </button>
      </div>
      
      <div v-if="loadingDetails" class="loading-section">
        <i class="fas fa-spinner fa-spin"></i>
        <span>Loading project details...</span>
      </div>
      
      <div v-else-if="projectDetails" class="project-details-content">
        <h2>{{ selectedProject.name }} - Project Details</h2>
        
        <!-- Basic Project Info -->
        <div class="info-card">
          <h3>
            <i class="fas fa-info-circle"></i>
            Project Information
          </h3>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">Key:</span>
              <span class="info-value">{{ projectDetails.project.key }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Name:</span>
              <span class="info-value">{{ projectDetails.project.name }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Type:</span>
              <span class="info-value">{{ projectDetails.project.projectTypeKey }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Lead:</span>
              <span class="info-value">{{ projectDetails.project.lead?.displayName || 'N/A' }}</span>
            </div>
            <div v-if="projectDetails.project.description" class="info-item">
              <span class="info-label">Description:</span>
              <span class="info-value">{{ projectDetails.project.description }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">URL:</span>
              <a :href="projectDetails.project.self" target="_blank" rel="noopener noreferrer" class="info-link">
                <i class="fas fa-external-link-alt"></i>
                View in Jira
              </a>
            </div>
          </div>
        </div>

        <!-- Components -->
        <div v-if="projectDetails.components && projectDetails.components.length > 0" class="info-card">
          <h3>
            <i class="fas fa-puzzle-piece"></i>
            Components ({{ projectDetails.components.length }})
          </h3>
          <div class="components-list">
            <div 
              v-for="component in projectDetails.components" 
              :key="component.id"
              class="component-item"
            >
              <div class="component-name">{{ component.name }}</div>
              <div v-if="component.description" class="component-description">
                {{ component.description }}
              </div>
            </div>
          </div>
        </div>

        <!-- Versions -->
        <div v-if="projectDetails.versions && projectDetails.versions.length > 0" class="info-card">
          <h3>
            <i class="fas fa-tags"></i>
            Versions ({{ projectDetails.versions.length }})
          </h3>
          <div class="versions-list">
            <div 
              v-for="version in projectDetails.versions" 
              :key="version.id"
              class="version-item"
            >
              <div class="version-header">
                <span class="version-name">{{ version.name }}</span>
                <span 
                  class="version-status"
                  :class="{ 'released': version.released, 'unreleased': !version.released }"
                >
                  {{ version.released ? 'Released' : 'Unreleased' }}
                </span>
              </div>
              <div v-if="version.description" class="version-description">
                {{ version.description }}
              </div>
            </div>
          </div>
        </div>

        <!-- Issues -->
        <div v-if="projectDetails.issues && projectDetails.issues.issues && projectDetails.issues.issues.length > 0" class="info-card">
          <h3>
            <i class="fas fa-tasks"></i>
            Recent Issues ({{ projectDetails.issues.total }} total, showing {{ projectDetails.issues.issues.length }})
          </h3>
          <div class="issues-list">
            <div 
              v-for="issue in projectDetails.issues.issues" 
              :key="issue.id"
              class="issue-item"
            >
              <div class="issue-header">
                <span class="issue-key">{{ issue.key }}</span>
                <span class="issue-summary">{{ issue.fields.summary }}</span>
              </div>
              <div class="issue-details">
                <span class="issue-detail">
                  <strong>Status:</strong> {{ issue.fields.status.name }}
                </span>
                <span class="issue-detail">
                  <strong>Type:</strong> {{ issue.fields.issuetype.name }}
                </span>
                <span class="issue-detail">
                  <strong>Priority:</strong> {{ issue.fields.priority?.name || 'N/A' }}
                </span>
                <span class="issue-detail">
                  <strong>Assignee:</strong> {{ issue.fields.assignee?.displayName || 'Unassigned' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Empty State -->
    <div v-if="projects && projects.length === 0 && !loading && accessToken && !error && !selectedProject" class="empty-state">
      <i class="fas fa-folder-open"></i>
      <p>No projects found or click "Fetch Projects" to load them.</p>
    </div>

    <!-- User Selection Dialog -->
    <div v-if="showUserDialog" class="dialog-overlay" @click="closeUserDialog">
      <div class="dialog-content" @click.stop>
        <div class="dialog-header">
          <h3>
            <i class="fas fa-users"></i>
            Assign Project to Users
          </h3>
          <button @click="closeUserDialog" class="close-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="dialog-body">
          <div class="project-info">
            <h4>{{ selectedProjectForAssignment?.name }}</h4>
            <p><strong>Key:</strong> {{ selectedProjectForAssignment?.key }}</p>
            <p><strong>Type:</strong> {{ selectedProjectForAssignment?.projectTypeKey }}</p>
          </div>
          
          <div class="users-section">
            <h4>Select Users to Assign:</h4>
            <div class="users-search">
              <input 
                v-model="userSearchQuery" 
                type="text" 
                placeholder="Search users..." 
                class="search-input"
              >
            </div>
            
            <div class="users-list">
              <div v-if="loadingUsers" class="loading-users">
                <i class="fas fa-spinner fa-spin"></i>
                <span>Loading users...</span>
              </div>
              
              <div v-else-if="filteredUsers.length === 0" class="no-users">
                <i class="fas fa-user-slash"></i>
                <span>No users found</span>
              </div>
              
              <div v-else class="users-grid">
                <div 
                  v-for="user in filteredUsers" 
                  :key="user.id"
                  class="user-item"
                  :class="{ 'selected': selectedUsers.includes(user.id) }"
                >
                  <div class="user-checkbox" @click.stop="toggleUserSelection(user.id)">
                    <input 
                      type="checkbox" 
                      :checked="selectedUsers.includes(user.id)"
                      @click.stop="toggleUserSelection(user.id)"
                      @change="toggleUserSelection(user.id)"
                    >
                  </div>
                  <div class="user-info" @click="toggleUserSelection(user.id)">
                    <div class="user-name">{{ user.full_name }}</div>
                    <div class="user-email">{{ user.email }}</div>
                    <div class="user-username">@{{ user.username }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="dialog-footer">
          <div class="selected-count">
            {{ selectedUsers.length }} user(s) selected
          </div>
          <div class="dialog-actions">
            <button @click="closeUserDialog" class="btn btn-secondary">
              Cancel
            </button>
            <button 
              @click="submitProjectAssignment" 
              class="btn btn-primary"
              :disabled="selectedUsers.length === 0 || assigningProject"
            >
              <i v-if="assigningProject" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-check"></i>
              {{ assigningProject ? 'Assigning...' : 'Assign Project' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { API_ENDPOINTS } from '../../../config/api.js'

export default {
  name: 'JiraIntegration',
  setup() {
    // Reactive state
    const projects = ref([])
    const loading = ref(false)
    const accessToken = ref(null)
    const error = ref(null)
    const selectedProject = ref(null)
    const projectDetails = ref(null)
    const loadingDetails = ref(false)
    const jiraResources = ref([])
    const selectedCloudId = ref(null)
    const selectedAccount = ref(null)
    
    // User selection dialog state
    const showUserDialog = ref(false)
    const selectedProjectForAssignment = ref(null)
    const allUsers = ref([])
    const selectedUsers = ref([])
    const userSearchQuery = ref('')
    const loadingUsers = ref(false)
    const assigningProject = ref(false)

    // Get current user ID
    const getCurrentUserId = () => {
      return localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
    }

    // Computed property for filtered users
    const filteredUsers = computed(() => {
      if (!userSearchQuery.value) {
        return allUsers.value
      }
      
      const query = userSearchQuery.value.toLowerCase()
      return allUsers.value.filter(user => 
        user.full_name.toLowerCase().includes(query) ||
        user.email.toLowerCase().includes(query) ||
        user.username.toLowerCase().includes(query)
      )
    })

    // Check for OAuth success or error in URL params after OAuth redirect
    onMounted(async () => {
      const urlParams = new URLSearchParams(window.location.search)
      const success = urlParams.get('success')
      const loadStoredData = urlParams.get('loadStoredData')
      const errorParam = urlParams.get('error')
      
      // Handle OAuth errors
      if (errorParam) {
        console.error('❌ OAuth error received:', errorParam)
        error.value = `OAuth failed: ${errorParam}`
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname)
        return
      }
      
      // Handle OAuth success - load stored data from database
      if (success === 'true') {
        console.log('🎉 OAuth successful! Loading stored Jira data from database...')
        
        // Load stored data first (this will set accessToken and resources)
        await loadStoredProjectsData()
        
        // If resources were loaded, auto-select the first one
        if (jiraResources.value && jiraResources.value.length > 0) {
          // If only one resource, it's already auto-selected by loadStoredProjectsData
          // If multiple, fetchJiraResourcesAndAutoConnect will handle it
          if (jiraResources.value.length > 1) {
            await fetchJiraResourcesAndAutoConnect()
          }
        } else {
          // If no resources in stored data, fetch them fresh
          await fetchJiraResourcesAndAutoConnect()
        }
        
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname)
        console.log('✅ OAuth success handled and URL cleaned up')
      } else if (loadStoredData === 'true') {
        console.log('📊 Loading stored Jira data from database...')
        await loadStoredProjectsData()
      }
      // Removed automatic loading of stored data - user must click Connect button
    })


    // Load stored projects data from database
    const loadStoredProjectsData = async () => {
      try {
        console.log('📊 Loading stored Jira data from database...')
        
        const response = await fetch(`${API_ENDPOINTS.JIRA_STORED_DATA}?user_id=${getCurrentUserId()}`)
        
        if (response.ok) {
          const data = await response.json()
          console.log('✅ Stored Jira data response:', data)
          
          if (data.success && data.has_data) {
            // Set access token to indicate we're connected
            accessToken.value = 'stored_data_token'
            
            // Load resources if available
            if (data.resources && data.resources.length > 0) {
              jiraResources.value = data.resources
              console.log(`📊 Loaded ${data.resources.length} stored resources`)
              
              // Auto-select if only one resource
              if (data.resources.length === 1) {
                handleAccountSelect(data.resources[0])
              }
            }
            
            // Load projects if available
            if (data.projects && data.projects.length > 0) {
              projects.value = data.projects
              console.log(`📊 Loaded ${data.projects.length} stored projects`)
            }
            
            // Load project details if available
            if (data.project_details) {
              // Store project details for later use
              window.storedProjectDetails = data.project_details
              console.log(`📊 Loaded ${Object.keys(data.project_details).length} stored project details`)
            }
            
            console.log('✅ Successfully loaded stored Jira data')
          } else {
            console.log('ℹ️ No stored Jira data found')
          }
        } else {
          console.error('❌ Failed to load stored Jira data:', response.statusText)
        }
      } catch (error) {
        console.error('❌ Error loading stored Jira data:', error)
      }
    }

    // Fetch available Jira resources for account selection
    const fetchJiraResources = async () => {
      try {
        console.log('🔍 Fetching available Jira resources from Django backend...')
        
        const response = await fetch(`${API_ENDPOINTS.JIRA_RESOURCES}?user_id=${getCurrentUserId()}`)
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        console.log('✅ Jira resources response:', data)
        
        if (data.success && data.resources && data.resources.length > 0) {
          jiraResources.value = data.resources
          
          // If only one account, auto-select it
          if (data.resources.length === 1) {
            handleAccountSelect(data.resources[0])
          }
          // If multiple accounts, let user choose (UI will show selection)
        } else {
          console.error('No Jira resources found')
          error.value = data.error || 'No Jira resources found'
        }
      } catch (err) {
        console.error('❌ Error fetching Jira resources:', err)
        error.value = `Error fetching Jira resources: ${err.message}`
      }
    }

    // Fetch Jira resources and automatically connect + load data
    const fetchJiraResourcesAndAutoConnect = async () => {
      try {
        console.log('🚀 Auto-connecting to Jira after OAuth...')
        
        const response = await fetch(`${API_ENDPOINTS.JIRA_RESOURCES}?user_id=${getCurrentUserId()}`)
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        console.log('✅ Jira resources response:', data)
        
        if (data.success && data.resources && data.resources.length > 0) {
          jiraResources.value = data.resources
          
          // Auto-select the first resource (most common case)
          const firstResource = data.resources[0]
          console.log('🎯 Auto-selecting first Jira resource:', firstResource.name)
          handleAccountSelect(firstResource)
          
          // Automatically fetch projects after account selection
          setTimeout(async () => {
            console.log('📡 Auto-fetching projects after account selection...')
            await handleFetchProjects()
          }, 1000) // Small delay to ensure account selection is processed
          
        } else {
          console.error('No Jira resources found')
          error.value = data.error || 'No Jira resources found'
        }
      } catch (err) {
        console.error('❌ Error auto-connecting to Jira:', err)
        error.value = `Error connecting to Jira: ${err.message}`
      }
    }

    // Handle account selection
    const handleAccountSelect = (resource) => {
      console.log('🎯 Account selected:', resource.name)
      selectedCloudId.value = resource.id
      selectedAccount.value = resource
      
      // Clear any existing projects and project details
      projects.value = []
      selectedProject.value = null
      projectDetails.value = null
    }

    // Handle changing account
    const handleChangeAccount = () => {
      console.log('🔄 Changing account...')
      selectedCloudId.value = null
      selectedAccount.value = null
      projects.value = []
      selectedProject.value = null
      projectDetails.value = null
    }

    // Save Jira connection to backend
    const saveJiraConnection = async (token) => {
      try {
        console.log('💾 Saving Jira connection to backend...')
        
        const response = await fetch(API_ENDPOINTS.JIRA_OAUTH_CALLBACK, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            access_token: token,
            refresh_token: `refresh_${token}`,
            expires_in: 3600,
            user_id: getCurrentUserId(),
            account_info: {
              account_id: 'jira_account_' + Date.now(),
              account_type: 'atlassian',
              email: 'user@example.com',
              name: 'Jira User'
            }
          })
        })

        if (response.ok) {
          const data = await response.json()
          console.log('✅ Jira connection saved to backend:', data)
        } else {
          console.error('❌ Failed to save Jira connection:', response.statusText)
        }
      } catch (error) {
        console.error('❌ Error saving Jira connection:', error)
      }
    }

    // Handle the click event to connect to Jira
    const handleConnectClick = async () => {
      console.log('🔌 Connect to Jira button clicked!')
      console.log('🚀 Redirecting to Django Jira OAuth endpoint...')
      
      // Redirect to Django backend OAuth endpoint
      const jiraOAuthUrl = `${API_ENDPOINTS.JIRA_OAUTH}?user_id=${getCurrentUserId()}`
      console.log('🔗 Redirecting to Django OAuth endpoint:', jiraOAuthUrl)
      console.log('🔗 Expected redirect URI:', API_ENDPOINTS.JIRA_OAUTH_CALLBACK)
      window.location.href = jiraOAuthUrl
    }

    // Handle loading stored data
    const handleLoadStoredData = async () => {
      console.log('📊 Load Previous Connection button clicked!')
      loading.value = true
      error.value = null
      
      try {
        await loadStoredProjectsData()
      } catch (err) {
        console.error('❌ Error loading stored data:', err)
        error.value = `Error loading stored data: ${err.message}`
      } finally {
        loading.value = false
      }
    }

    // After authentication, fetch the projects from Jira API
    const handleFetchProjects = async () => {
      if (!selectedCloudId.value) {
        console.error('No cloud ID selected')
        error.value = 'Please select a Jira account first'
        return
      }

      loading.value = true
      error.value = null
      selectedProject.value = null
      projectDetails.value = null
      
      try {
        console.log('📡 Fetching projects from Django backend...')
        console.log('Cloud ID:', selectedCloudId.value)
        
        // Prepare request body - only include access_token if it's a real token (not a flag)
        const requestBody = {
          user_id: getCurrentUserId(),
          cloud_id: selectedCloudId.value,
          action: 'fetch_projects'
        }
        
        // Only include access_token if it's a real token (not a flag like 'stored_data_token' or 'oauth_success')
        if (accessToken.value && 
            accessToken.value !== 'stored_data_token' && 
            accessToken.value !== 'oauth_success' &&
            accessToken.value.length > 20) {
          requestBody.access_token = accessToken.value
          console.log('Using access token from frontend')
        } else {
          console.log('No valid access token in frontend, backend will use stored connection token')
        }
        
        // Call Django backend to fetch Jira projects
        const response = await fetch(API_ENDPOINTS.JIRA_PROJECTS, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody)
        })
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        console.log('✅ Projects response from Django:', data)
        
        if (data.success && data.data) {
          projects.value = data.data
          console.log(`🎉 Successfully loaded ${data.data.length} projects`)
          
          // Save projects to backend
          await saveProjectsToBackend(data.data)
        } else {
          console.error('Failed to fetch projects:', data.error)
          projects.value = []
          error.value = data.error || 'Failed to fetch projects'
        }
      } catch (err) {
        console.error('❌ Error fetching Jira projects:', err)
        projects.value = []
        error.value = `Error fetching projects: ${err.message}`
      } finally {
        loading.value = false
      }
    }

    // Save projects to backend
    const saveProjectsToBackend = async (projectsData) => {
      try {
        console.log('💾 Saving projects to backend...')
        
        const response = await fetch(API_ENDPOINTS.JIRA_PROJECTS, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: getCurrentUserId(),
            projects: projectsData
          })
        })

        if (response.ok) {
          const data = await response.json()
          console.log('✅ Projects saved to backend:', data)
        } else {
          console.error('❌ Failed to save projects to backend:', response.statusText)
        }
      } catch (error) {
        console.error('❌ Error saving projects to backend:', error)
      }
    }

    // Handle project click to fetch detailed information
    const handleProjectClick = async (project) => {
      if (!accessToken.value) {
        console.error('No access token available')
        error.value = 'No access token available'
        return
      }

      console.log('🔍 Project clicked:', project)
      console.log('🔍 Project ID:', project.id)
      console.log('🔍 Access token available:', !!accessToken.value)

      selectedProject.value = project
      loadingDetails.value = true
      error.value = null
      
      try {
        // First, try to get project details from database
        console.log('📊 Fetching project details from database...')
        const userId = getCurrentUserId()
        const response = await fetch(`${API_ENDPOINTS.JIRA_PROJECT_DETAILS_FROM_DB}?user_id=${userId}&project_id=${project.id}`)
        
        if (response.ok) {
          const data = await response.json()
          if (data.success && data.project_details) {
            console.log('✅ Found project details in database:', data.project_details)
            projectDetails.value = data.project_details.data
            loadingDetails.value = false
            return
          }
        }
        
        // If not found in database, check if we have stored project details in memory
        if (window.storedProjectDetails && window.storedProjectDetails[project.id]) {
          console.log('📊 Using stored project details from memory for project:', project.id)
          const storedDetails = window.storedProjectDetails[project.id]
          projectDetails.value = storedDetails.data
          loadingDetails.value = false
          
          // Save to database for future use
          await saveProjectDetailsToBackend(project.id, storedDetails.data)
          return
        }
        
        // If no stored details anywhere, try to fetch from Django backend
        console.log('📡 Fetching project details from Django backend...')
        console.log('Project ID:', project.id)
        console.log('Cloud ID:', selectedCloudId.value)
        
        // Call Django backend to fetch project details
        const projectResponse = await fetch(API_ENDPOINTS.JIRA_PROJECT_DETAILS, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: getCurrentUserId(),
            project_id: project.id,
            access_token: accessToken.value,
            cloud_id: selectedCloudId.value
          })
        })
        
        if (!projectResponse.ok) {
          throw new Error(`HTTP error! status: ${projectResponse.status}`)
        }
        
        const data = await projectResponse.json()
        console.log('✅ Project details response from Django:', data)
        
        if (data.success && data.data) {
          projectDetails.value = data.data
          
          // Save project details to backend
          await saveProjectDetailsToBackend(project.id, data.data)
        } else {
          throw new Error(data.error || 'Failed to fetch project details')
        }
      } catch (err) {
        console.error('❌ Error fetching project details:', err)
        error.value = `Error fetching project details: ${err.message}`
      } finally {
        loadingDetails.value = false
      }
    }

    // Save project details to backend
    const saveProjectDetailsToBackend = async (projectId, projectDetailsData) => {
      try {
        console.log('💾 Saving project details to backend...')
        
        const response = await fetch(API_ENDPOINTS.JIRA_PROJECT_DETAILS, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: getCurrentUserId(),
            project_id: projectId,
            project_details: projectDetailsData
          })
        })

        if (response.ok) {
          const data = await response.json()
          console.log('✅ Project details saved to backend:', data)
        } else {
          console.error('❌ Failed to save project details to backend:', response.statusText)
        }
      } catch (error) {
        console.error('❌ Error saving project details to backend:', error)
      }
    }

    // Go back to projects list
    const handleBackToProjects = () => {
      selectedProject.value = null
      projectDetails.value = null
    }

    // Handle adding a project - show user selection dialog
    const handleAddProject = async (project) => {
      console.log('➕ Adding project:', project)
      selectedProjectForAssignment.value = project
      selectedUsers.value = []
      userSearchQuery.value = ''
      showUserDialog.value = true
      
      // Load users if not already loaded
      if (allUsers.value.length === 0) {
        await loadAllUsers()
      }
    }

    // Load all users from the database
    const loadAllUsers = async () => {
      try {
        loadingUsers.value = true
        console.log('👥 Loading all users...')
        
        const response = await fetch(API_ENDPOINTS.JIRA_GET_ALL_USERS)
        
        if (response.ok) {
          const data = await response.json()
          console.log('✅ Users loaded:', data)
          
          if (data.success) {
            allUsers.value = data.users
            console.log(`👥 Loaded ${data.count} users`)
          } else {
            console.error('❌ Failed to load users:', data.error)
            error.value = `Failed to load users: ${data.error}`
          }
        } else {
          console.error('❌ Failed to load users:', response.statusText)
          error.value = `Failed to load users: ${response.statusText}`
        }
      } catch (err) {
        console.error('❌ Error loading users:', err)
        error.value = `Error loading users: ${err.message}`
      } finally {
        loadingUsers.value = false
      }
    }

    // Toggle user selection
    const toggleUserSelection = (userId) => {
      console.log('🔄 Toggling user selection for ID:', userId)
      console.log('📋 Current selected users:', selectedUsers.value)
      
      const index = selectedUsers.value.indexOf(userId)
      if (index > -1) {
        selectedUsers.value.splice(index, 1)
        console.log('❌ Removed user from selection')
      } else {
        selectedUsers.value.push(userId)
        console.log('✅ Added user to selection')
      }
      
      console.log('📋 Updated selected users:', selectedUsers.value)
    }

    // Close user dialog
    const closeUserDialog = () => {
      showUserDialog.value = false
      selectedProjectForAssignment.value = null
      selectedUsers.value = []
      userSearchQuery.value = ''
    }

    // Submit project assignment
    const submitProjectAssignment = async () => {
      if (selectedUsers.value.length === 0) {
        alert('Please select at least one user to assign the project to.')
        return
      }

      try {
        assigningProject.value = true
        console.log('📤 Assigning project to users...')
        
        const response = await fetch(API_ENDPOINTS.JIRA_ASSIGN_PROJECT, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            assigned_by_user_id: getCurrentUserId(),
            project_data: selectedProjectForAssignment.value,
            selected_users: selectedUsers.value
          })
        })

        if (response.ok) {
          const data = await response.json()
          console.log('✅ Project assignment successful:', data)
          
          if (data.success) {
            alert(`✅ Project "${data.project_name}" successfully assigned to ${data.assigned_users.length} user(s)!`)
            closeUserDialog()
          } else {
            console.error('❌ Project assignment failed:', data.error)
            alert(`❌ Failed to assign project: ${data.error}`)
          }
        } else {
          console.error('❌ Failed to assign project:', response.statusText)
          alert(`❌ Failed to assign project: ${response.statusText}`)
        }
      } catch (err) {
        console.error('❌ Error assigning project:', err)
        alert(`❌ Error assigning project: ${err.message}`)
      } finally {
        assigningProject.value = false
      }
    }

    // Truncate description for table display
    const truncateDescription = (desc) => {
      if (!desc) return ''
      const maxLen = 80
      return desc.length > maxLen ? desc.slice(0, maxLen) + '...' : desc
    }

    // Go back to external integrations
    const goBack = () => {
      window.location.href = '/integration/external'
    }

    return {
      projects,
      loading,
      accessToken,
      error,
      selectedProject,
      projectDetails,
      loadingDetails,
      jiraResources,
      selectedCloudId,
      selectedAccount,
      showUserDialog,
      selectedProjectForAssignment,
      allUsers,
      selectedUsers,
      userSearchQuery,
      loadingUsers,
      assigningProject,
      filteredUsers,
      handleConnectClick,
      handleLoadStoredData,
      handleFetchProjects,
      handleProjectClick,
      handleBackToProjects,
      handleAddProject,
      handleAccountSelect,
      handleChangeAccount,
      fetchJiraResources,
      fetchJiraResourcesAndAutoConnect,
      loadAllUsers,
      toggleUserSelection,
      closeUserDialog,
      submitProjectAssignment,
      truncateDescription,
      saveJiraConnection,
      saveProjectsToBackend,
      saveProjectDetailsToBackend,
      loadStoredProjectsData,
      goBack
    }
  }
}
</script>

<style scoped>
@import './jira.css';

/* Page header styles */
.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  margin-right: 20px;
  transition: background-color 0.2s ease;
}

.back-button:hover {
  background-color: #5a6268;
}

.back-button i {
  font-size: 12px;
}

.page-header h1 {
  margin: 0;
  color: #333;
  font-size: 24px;
  font-weight: 600;
}

.connection-info {
  margin-top: 10px;
  padding: 10px;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  color: #6c757d;
  font-size: 14px;
}

.connection-info i {
  margin-right: 5px;
  color: #007bff;
}

/* Account Selection Styles */
.account-selection-section {
  margin: 20px 0;
  padding: 20px;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 8px;
}

.account-selection-section h3 {
  margin-bottom: 15px;
  color: #495057;
  display: flex;
  align-items: center;
  gap: 10px;
}

.selection-info {
  margin-bottom: 20px;
  color: #6c757d;
  font-size: 14px;
}

.accounts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.account-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background-color: white;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.account-item:hover {
  border-color: #007bff;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.1);
  transform: translateY(-1px);
}

.account-info {
  flex: 1;
}

.account-name {
  font-weight: 600;
  color: #495057;
  margin-bottom: 4px;
}

.account-url {
  color: #6c757d;
  font-size: 14px;
  margin-bottom: 8px;
}

.account-scopes {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.scope-badge {
  background-color: #e3f2fd;
  color: #1976d2;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.account-actions {
  color: #6c757d;
  font-size: 16px;
}

.selected-account-info {
  margin-top: 10px;
  padding: 10px;
  background-color: #e8f5e8;
  border: 1px solid #c3e6c3;
  border-radius: 4px;
  color: #2d5a2d;
  font-size: 14px;
}

.btn-outline {
  background-color: transparent;
  border: 1px solid #6c757d;
  color: #6c757d;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.btn-outline:hover {
  background-color: #6c757d;
  color: white;
}

.btn-outline:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Dialog Styles */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.dialog-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dialog-header {
  padding: 20px;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f8f9fa;
}

.dialog-header h3 {
  margin: 0;
  color: #495057;
  display: flex;
  align-items: center;
  gap: 10px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  color: #6c757d;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background-color: #e9ecef;
  color: #495057;
}

.dialog-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.project-info {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
  border-left: 4px solid #007bff;
}

.project-info h4 {
  margin: 0 0 10px 0;
  color: #495057;
}

.project-info p {
  margin: 5px 0;
  color: #6c757d;
  font-size: 14px;
}

.users-section h4 {
  margin: 0 0 15px 0;
  color: #495057;
}

.users-search {
  margin-bottom: 20px;
}

.search-input {
  width: 100%;
  padding: 10px 15px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s ease;
}

.search-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.users-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #dee2e6;
  border-radius: 6px;
}

.loading-users, .no-users {
  padding: 40px 20px;
  text-align: center;
  color: #6c757d;
}

.loading-users i, .no-users i {
  font-size: 24px;
  margin-bottom: 10px;
  display: block;
}

.users-grid {
  display: flex;
  flex-direction: column;
}

.user-item {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  border-bottom: 1px solid #f1f3f4;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.user-item:last-child {
  border-bottom: none;
}

.user-item:hover {
  background-color: #f8f9fa;
}

.user-item.selected {
  background-color: #e3f2fd;
  border-left: 3px solid #1976d2;
}

.user-checkbox {
  margin-right: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  min-height: 20px;
}

.user-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  margin: 0;
  accent-color: #007bff;
  transform: scale(1.2);
  border: 2px solid #dee2e6;
  border-radius: 3px;
  background-color: white;
}

.user-checkbox input[type="checkbox"]:checked {
  background-color: #007bff;
  border-color: #007bff;
}

.user-checkbox input[type="checkbox"]:hover {
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.user-info {
  flex: 1;
  cursor: pointer;
  padding: 2px 0;
}

.user-name {
  font-weight: 600;
  color: #495057;
  margin-bottom: 2px;
}

.user-email {
  color: #6c757d;
  font-size: 13px;
  margin-bottom: 2px;
}

.user-username {
  color: #adb5bd;
  font-size: 12px;
  font-style: italic;
}

.dialog-footer {
  padding: 20px;
  border-top: 1px solid #dee2e6;
  background-color: #f8f9fa;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selected-count {
  color: #6c757d;
  font-size: 14px;
  font-weight: 500;
}

.dialog-actions {
  display: flex;
  gap: 10px;
}

.dialog-actions .btn {
  padding: 8px 16px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.dialog-actions .btn-secondary {
  background-color: #6c757d;
  color: white;
}

.dialog-actions .btn-secondary:hover {
  background-color: #5a6268;
}

.dialog-actions .btn-primary {
  background-color: #007bff;
  color: white;
}

.dialog-actions .btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.dialog-actions .btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>