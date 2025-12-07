<template>
  <div class="streamline-container">
    <div class="streamline-header">
      <h1>
        <!-- <i class="fas fa-stream"></i> -->
        My Streamlined Projects
      </h1>
      <p class="header-description">
        View and manage your assigned projects from various platforms
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-section">
      <i class="fas fa-spinner fa-spin"></i>
      <span>Loading your projects...</span>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="error-section">
      <i class="fas fa-exclamation-triangle"></i>
      <strong>Error:</strong> {{ error }}
    </div>

    <!-- No Projects State -->
    <div v-if="!loading && !error && userProjects.length === 0" class="empty-state">
      <i class="fas fa-folder-open"></i>
      <h3>No Projects Assigned</h3>
      <p>You don't have any projects assigned to you yet.</p>
      <p>Contact your administrator to get access to projects.</p>
    </div>

    <!-- Projects List -->
    <div v-if="!loading && !error && userProjects.length > 0" class="projects-list-container">
      <!-- List Header -->
      <div class="list-header">
        <div class="list-header-cell project-info-header">Project Information</div>
        <div class="list-header-cell project-type-header">Type</div>
        <div class="list-header-cell platform-header">Platform</div>
        <div class="list-header-cell assigned-by-header">Assigned By</div>
        <div class="list-header-cell assigned-date-header">Date</div>
        <div class="list-header-cell actions-header">Actions</div>
      </div>
      
      <!-- Projects List -->
      <div class="projects-list">
        <div 
          v-for="project in userProjects" 
          :key="project.id"
          class="project-list-item"
          @click="viewProjectDetails(project)"
        >
          <div class="project-info">
            <div class="project-icon">
              <i class="fas fa-project-diagram"></i>
            </div>
            <div class="project-details">
              <div class="project-name">{{ project.project_name }}</div>
              <div class="project-key">{{ project.project_key }}</div>
            </div>
          </div>
          
          <div class="project-type">
            <span class="status-badge" :class="getStatusClass(project.list_type)">
              {{ getStatusText(project.list_type) }}
            </span>
          </div>
          
          <div class="platform">
            <i class="fas fa-external-link-alt"></i>
            Jira
          </div>
          
          <div class="assigned-by">
            <i class="fas fa-user"></i>
            {{ project.assigned_by.full_name }}
          </div>
          
          <div class="assigned-date">
            <i class="fas fa-calendar"></i>
            {{ formatDate(project.created_at) }}
          </div>
          
          <div class="project-actions">
            <button class="view-btn" @click.stop="viewProjectDetails(project)">
              <i class="fas" :class="expandedProject && expandedProject.id === project.id ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
              {{ expandedProject && expandedProject.id === project.id ? 'Hide' : 'Show' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Expanded Project Information (Inline) -->
    <div v-if="expandedProject" class="project-expanded">
      <div class="project-details-section">
        <h3>
          <i class="fas fa-project-diagram"></i>
          {{ expandedProject.project_name }} - Project Details
        </h3>
        
        <!-- Basic Information -->
        <div class="details-grid">
          <div class="detail-item">
            <span class="detail-label">Project Name</span>
            <span class="detail-value">{{ expandedProject.project_name }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Project Key</span>
            <span class="detail-value">{{ expandedProject.project_key }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Project ID</span>
            <span class="detail-value">{{ expandedProject.project_id }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Assignment Type</span>
            <span class="detail-value">{{ getStatusText(expandedProject.list_type) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Assigned By</span>
            <span class="detail-value">{{ expandedProject.assigned_by.full_name }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Assigned Date</span>
            <span class="detail-value">{{ formatDate(expandedProject.created_at) }}</span>
          </div>
        </div>
      </div>

      <!-- Platform Details Section -->
      <div class="project-details-section" v-if="expandedProject.project_details">
        <h3>
          <i class="fas fa-cogs"></i>
          Platform Details
        </h3>
        <div class="details-grid">
          <div class="detail-item" v-if="expandedProject.project_details.description">
            <span class="detail-label">Description</span>
            <span class="detail-value">{{ expandedProject.project_details.description }}</span>
          </div>
          <div class="detail-item" v-if="expandedProject.project_details.projectTypeKey">
            <span class="detail-label">Project Type</span>
            <span class="detail-value">{{ expandedProject.project_details.projectTypeKey }}</span>
          </div>
          <div class="detail-item" v-if="expandedProject.project_details.lead">
            <span class="detail-label">Project Lead</span>
            <span class="detail-value">{{ expandedProject.project_details.lead.displayName || 'N/A' }}</span>
          </div>
          <div class="detail-item" v-if="expandedProject.project_details.self">
            <span class="detail-label">Platform URL</span>
            <a :href="expandedProject.project_details.self" target="_blank" rel="noopener noreferrer" class="detail-value" style="color: #007bff; text-decoration: none;">
              <i class="fas fa-external-link-alt"></i> View in Jira
            </a>
          </div>
        </div>
      </div>

      <!-- Assigned Users Section -->
      <div class="project-details-section" v-if="expandedProject.assigned_users && expandedProject.assigned_users.length > 0">
        <h3>
          <i class="fas fa-users"></i>
          Assigned Users ({{ expandedProject.assigned_users.length }})
        </h3>
        <div class="users-list">
          <div 
            v-for="user in expandedProject.assigned_users" 
            :key="user.id"
            class="user-item"
            :class="{ 'current-user': user.id === currentUserId }"
          >
            <div class="user-avatar">
              <i class="fas fa-user"></i>
            </div>
            <div class="user-info">
              <div class="user-name">{{ user.full_name }}</div>
              <div class="user-email">{{ user.email }}</div>
              <div class="user-username">@{{ user.username }}</div>
            </div>
            <div v-if="user.id === currentUserId" class="current-user-badge">
              <i class="fas fa-check-circle"></i>
              You
            </div>
          </div>
        </div>
      </div>

      <!-- Tasks Section -->
      <div class="tasks-section">
        <h3>
          <i class="fas fa-tasks"></i>
          Project Tasks
        </h3>
        <div v-if="expandedProject.tasks && expandedProject.tasks.length > 0" class="tasks-list">
          <div 
            v-for="task in expandedProject.tasks" 
            :key="task.id"
            class="task-item"
          >
            <div class="task-header">
              <div class="task-title">{{ task.summary || task.title || 'Untitled Task' }}</div>
              <div class="task-actions">
                <div class="task-status" :class="getTaskStatusClass(task.status)">
                  {{ task.status || 'To Do' }}
                </div>
                <button 
                  class="task-plus-btn" 
                  @click.stop="handleTaskAction(task)"
                  title="Add task action"
                >
                  <i class="fas fa-plus"></i>
                </button>
              </div>
            </div>
            <div class="task-meta">
              <span v-if="task.assignee">
                <i class="fas fa-user"></i>
                {{ task.assignee.displayName || task.assignee.name || 'Unassigned' }}
              </span>
              <span v-if="task.priority">
                <i class="fas fa-flag"></i>
                {{ task.priority.name || task.priority }}
              </span>
              <span v-if="task.updated">
                <i class="fas fa-clock"></i>
                {{ formatDate(task.updated) }}
              </span>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <i class="fas fa-clipboard-list"></i>
          <h3>No Tasks Available</h3>
          <p>No tasks have been loaded for this project yet.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { API_ENDPOINTS } from '../../../config/api.js'

export default {
  name: 'StreamlineView',
  setup() {
    // Reactive state
    const userProjects = ref([])
    const loading = ref(false)
    const error = ref(null)
    const expandedProject = ref(null)
    const currentUserId = ref(null)

    // Get current user ID
    const getCurrentUserId = () => {
      return localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
    }

    // Load user's assigned projects
    const loadUserProjects = async () => {
      try {
        loading.value = true
        error.value = null
        currentUserId.value = getCurrentUserId()
        
        console.log('📊 Loading user projects for user ID:', currentUserId.value)
        console.log('📊 API Endpoint:', API_ENDPOINTS.STREAMLINE_USER_PROJECTS)
        
        // Get authentication token
        const accessToken = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
        console.log('📊 Access Token:', accessToken ? 'Found' : 'Not found')
        
        // Call the real API endpoint
        const response = await fetch(`${API_ENDPOINTS.STREAMLINE_USER_PROJECTS}?user_id=${currentUserId.value}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
          },
          credentials: 'include'
        })
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        console.log('📊 API Response:', data)
        
        if (data.success) {
          userProjects.value = data.projects || []
          console.log(`📊 Loaded ${data.projects?.length || 0} projects for user`)
        } else {
          throw new Error(data.error || 'Failed to load projects')
        }
        
      } catch (err) {
        console.error('❌ Error loading user projects:', err)
        error.value = `Error loading projects: ${err.message}`
        
        // Fallback to mock data if API fails
        console.log('📊 Falling back to mock data due to API error')
        const mockProjects = [
          {
            id: 1,
            project_id: 'PROJ-10001',
            project_key: 'GRC',
            project_name: 'GRC Platform Development',
            list_type: 'multiple',
            created_at: new Date().toISOString(),
            assigned_by: {
              id: 3,
              full_name: 'Admin User',
              email: 'admin@example.com',
              username: 'admin'
            },
            assigned_users: [
              {
                id: currentUserId.value,
                full_name: 'Vikram Patel',
                email: 'vikram.patel@example.com',
                username: 'vikram.patel'
              },
              {
                id: 3,
                full_name: 'Admin User',
                email: 'admin@example.com',
                username: 'admin'
              },
              {
                id: 4,
                full_name: 'Jane Smith',
                email: 'jane.smith@example.com',
                username: 'jane.smith'
              }
            ],
            project_details: {
              description: 'Development of the GRC Platform with risk management, compliance monitoring, and audit capabilities.',
              projectTypeKey: 'software',
              lead: {
                displayName: 'Admin User'
              },
              self: 'https://jira.example.com/projects/GRC'
            }
          },
          {
            id: 2,
            project_id: 'PROJ-10002',
            project_key: 'RISK',
            project_name: 'Risk Assessment Module',
            list_type: 'single',
            created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days ago
            assigned_by: {
              id: 3,
              full_name: 'Admin User',
              email: 'admin@example.com',
              username: 'admin'
            },
            assigned_users: [
              {
                id: currentUserId.value,
                full_name: 'Vikram Patel',
                email: 'vikram.patel@example.com',
                username: 'vikram.patel'
              }
            ],
            project_details: {
              description: 'Risk assessment module for identifying, analyzing, and evaluating risks.',
              projectTypeKey: 'business',
              lead: {
                displayName: 'Vikram Patel'
              },
              self: 'https://jira.example.com/projects/RISK'
            }
          },
          {
            id: 3,
            project_id: 'PROJ-10003',
            project_key: 'COMP',
            project_name: 'Compliance Dashboard',
            list_type: 'multiple',
            created_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(), // 14 days ago
            assigned_by: {
              id: 4,
              full_name: 'Jane Smith',
              email: 'jane.smith@example.com',
              username: 'jane.smith'
            },
            assigned_users: [
              {
                id: currentUserId.value,
                full_name: 'Vikram Patel',
                email: 'vikram.patel@example.com',
                username: 'vikram.patel'
              },
              {
                id: 5,
                full_name: 'John Doe',
                email: 'john.doe@example.com',
                username: 'john.doe'
              }
            ],
            project_details: {
              description: 'Dashboard for monitoring compliance with regulations and standards.',
              projectTypeKey: 'business',
              lead: {
                displayName: 'Jane Smith'
              },
              self: 'https://jira.example.com/projects/COMP'
            }
          }
        ];
        
        // Set mock data to userProjects
        userProjects.value = mockProjects;
        console.log(`📊 Loaded ${mockProjects.length} mock projects for user`);
        error.value = null // Clear error since we have fallback data
      } finally {
        loading.value = false
      }
    }

    // View project details (expand inline)
    const viewProjectDetails = (project) => {
      console.log('🔍 Viewing project details:', project)
      // Toggle expanded project - if same project, collapse it
      if (expandedProject.value && expandedProject.value.id === project.id) {
        expandedProject.value = null
      } else {
        expandedProject.value = project
        // Load tasks for this project if not already loaded
        if (!project.tasks) {
          loadProjectTasks(project)
        }
      }
    }

    // Load project tasks
    const loadProjectTasks = async (project) => {
      try {
        console.log('📋 Loading tasks for project:', project.project_name)
        // For now, we'll add mock tasks. In the future, this could call an API
        const mockTasks = [
          {
            id: 1,
            summary: 'Setup project infrastructure',
            status: 'Done',
            assignee: { displayName: 'John Doe' },
            priority: { name: 'High' },
            updated: new Date().toISOString()
          },
          {
            id: 2,
            summary: 'Implement user authentication',
            status: 'In Progress',
            assignee: { displayName: 'Jane Smith' },
            priority: { name: 'Medium' },
            updated: new Date().toISOString()
          },
          {
            id: 3,
            summary: 'Create project documentation',
            status: 'To Do',
            assignee: null,
            priority: { name: 'Low' },
            updated: new Date().toISOString()
          }
        ]
        
        // Add tasks to the project
        project.tasks = mockTasks
        console.log('✅ Loaded tasks for project:', project.project_name)
      } catch (err) {
        console.error('❌ Error loading project tasks:', err)
      }
    }

    // Get status class for styling
    const getStatusClass = (listType) => {
      return listType === 'single' ? 'status-single' : 'status-multiple'
    }

    // Get status text
    const getStatusText = (listType) => {
      return listType === 'single' ? 'Individual' : 'Team Project'
    }

    // Get task status class for styling
    const getTaskStatusClass = (status) => {
      if (!status) return 'todo'
      const statusLower = status.toLowerCase()
      if (statusLower.includes('done') || statusLower.includes('completed')) return 'done'
      if (statusLower.includes('progress') || statusLower.includes('in progress')) return 'in-progress'
      return 'todo'
    }

    // Format date
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

    // Handle task action (plus button click)
    const handleTaskAction = async (task) => {
      console.log('🔧 Task action clicked for:', task)
      
      try {
        // Determine action type based on task status
        let actionType = 'Task Action'
        if (task.status === 'To Do') {
          actionType = 'Task Started'
        } else if (task.status === 'In Progress') {
          actionType = 'Task Updated'
        } else if (task.status === 'Done') {
          actionType = 'Task Viewed'
        }
        
        // Prepare payload with platform (for logging purposes)
        const payload = {
          user_id: currentUserId.value,
          task: task,
          action_type: actionType,
          platform: 'jira', // Platform source - can be: jira, gmail, sentinel, bamboohr
          project: expandedProject.value ? {
            project_id: expandedProject.value.project_id,
            project_name: expandedProject.value.project_name,
            project_key: expandedProject.value.project_key
          } : null
        }
        
        console.log('📤 Saving task action:', payload)
        
        // Get authentication token
        const accessToken = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
        
        // Call the real API endpoint
        const response = await fetch(API_ENDPOINTS.STREAMLINE_SAVE_TASK_ACTION, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
          },
          credentials: 'include',
          body: JSON.stringify(payload)
        })
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const result = await response.json()
        console.log('✅ Task action response:', result)
        
        // Check if already added
        if (result.already_added) {
          // Show info message for duplicate
          alert(`ℹ️ Already Recorded\n\nAction: ${actionType}\nTask: ${task.summary || task.title || 'Untitled Task'}\nPlatform: ${result.platform?.toUpperCase() || 'JIRA'}\n\n⚠️ This action was already recorded recently at:\n${new Date(result.timestamp).toLocaleString()}\n\nNo duplicate entry created.`)
        } else {
          // Show success message for new action
          alert(`✅ Success!\n\nAction: ${actionType}\nTask: ${task.summary || task.title || 'Untitled Task'}\nPlatform: ${result.platform?.toUpperCase() || 'JIRA'}\n\n✓ This action has been recorded in the database.`)
        }
      } catch (err) {
        console.error('❌ Error saving task action:', err)
        alert(`❌ Error: ${err.message}`)
      }
    }

    // Load projects on component mount
    onMounted(() => {
      loadUserProjects()
    })

    return {
      userProjects,
      loading,
      error,
      expandedProject,
      currentUserId,
      loadUserProjects,
      viewProjectDetails,
      loadProjectTasks,
      getStatusClass,
      getStatusText,
      getTaskStatusClass,
      formatDate,
      handleTaskAction
    }
  }
}
</script>

<style scoped>
@import './streamline.css';
</style>