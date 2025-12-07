<template>
  <div class="create-user-modal" v-if="showModal">
    <div class="modal-overlay" @click="closeModal"></div>
    <div class="modal-content fullscreen">
      <div class="modal-header">
        <h3>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
            <circle cx="8.5" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
            <line x1="20" y1="8" x2="20" y2="14" stroke="currentColor" stroke-width="2"/>
            <line x1="23" y1="11" x2="17" y2="11" stroke="currentColor" stroke-width="2"/>
          </svg>
          Create New User
        </h3>
        <button class="close-button" @click="closeModal">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
            <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
          </svg>
        </button>
      </div>
      
      <div class="modal-body">
        <div class="step-content">
          <p class="step-description">
            Create a new user account with the required information.
          </p>
          
          <form @submit.prevent="createUser" class="create-user-form">
            <div class="form-grid">
              <div class="input-group">
                <label for="username">Username *</label>
                <div class="input-wrapper">
                  <div class="input-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                      <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <input 
                    type="text" 
                    id="username" 
                    v-model="formData.username" 
                    placeholder="Enter username"
                    required
                    :disabled="isLoading"
                  >
                </div>
              </div>
              
              <div class="input-group">
                <label for="password">Password *</label>
                <div class="input-wrapper">
                  <div class="input-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                      <circle cx="12" cy="16" r="1" stroke="currentColor" stroke-width="2"/>
                      <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <input 
                    :type="passwordFieldType" 
                    id="password" 
                    v-model="formData.password" 
                    placeholder="Enter password"
                    required
                    :disabled="isLoading"
                  >
                  <button 
                    type="button"
                    @click="togglePasswordVisibility" 
                    class="password-toggle"
                    tabindex="-1"
                    :title="passwordFieldType === 'password' ? 'Show password' : 'Hide password'"
                  >
                    <svg v-if="passwordFieldType === 'password'" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2"/>
                      <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" stroke="currentColor" stroke-width="2"/>
                      <line x1="1" y1="1" x2="23" y2="23" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </button>
                </div>
              </div>
              
              <div class="input-group">
                <label for="email">Email *</label>
                <div class="input-wrapper">
                  <div class="input-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="2"/>
                      <polyline points="22,6 12,13 2,6" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <input 
                    type="email" 
                    id="email" 
                    v-model="formData.email" 
                    placeholder="Enter email address"
                    required
                    :disabled="isLoading"
                  >
                </div>
              </div>
              
              <div class="input-group">
                <label for="firstName">First Name *</label>
                <div class="input-wrapper">
                  <div class="input-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                      <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <input 
                    type="text" 
                    id="firstName" 
                    v-model="formData.firstName" 
                    placeholder="Enter first name"
                    required
                    :disabled="isLoading"
                  >
                </div>
              </div>
              
              <div class="input-group">
                <label for="lastName">Last Name *</label>
                <div class="input-wrapper">
                  <div class="input-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                      <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <input 
                    type="text" 
                    id="lastName" 
                    v-model="formData.lastName" 
                    placeholder="Enter last name"
                    required
                    :disabled="isLoading"
                  >
                </div>
              </div>
              
              <div class="input-group">
                <label for="department">Department *</label>
                <div class="input-wrapper">
                  <div class="input-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" stroke-width="2"/>
                      <polyline points="9 22 9 12 15 12 15 22" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <select 
                    id="department" 
                    v-model="formData.departmentId" 
                    required
                    :disabled="isLoading"
                  >
                    <option value="">Select a department</option>
                    <option v-for="dept in departments" :key="dept.id" :value="dept.id">
                      {{ dept.name }}
                    </option>
                  </select>
                </div>
              </div>
              
              <div class="input-group">
                <label for="role">Role *</label>
                <div class="input-wrapper">
                  <div class="input-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <div class="role-select-container">
                    <select 
                      id="role" 
                      v-model="formData.role" 
                      required
                      :disabled="isLoading"
                      @change="onRoleChange"
                    >
                      <option value="">Select a role</option>
                      <option v-for="role in availableRoles" :key="role" :value="role">
                        {{ role }}
                      </option>
                      <option value="__custom__">+ Add New Role</option>
                    </select>
                    <input 
                      v-if="showCustomRoleInput"
                      type="text" 
                      v-model="customRole"
                      placeholder="Enter new role name"
                      class="custom-role-input"
                      @keyup.enter="addCustomRole"
                      @blur="addCustomRole"
                    >
                  </div>
                </div>
              </div>
              
              <!-- Permissions Checklist -->
              <div v-if="formData.role && formData.role !== '__custom__'" class="permissions-section">
                <h4 class="permissions-title">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M9 11H1l8-8 8 8h-8z" stroke="currentColor" stroke-width="2"/>
                    <path d="M3 21h18" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  Permissions for {{ formData.role }}
                </h4>
                
                <!-- Global Select All -->
                <div class="global-select-all">
                  <label class="select-all-item">
                    <input 
                      type="checkbox" 
                      v-model="selectAllPermissions"
                      @change="toggleAllPermissions"
                      :disabled="isLoading"
                    >
                    <span class="select-all-label">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2"/>
                        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                      </svg>
                      Select All Permissions
                    </span>
                  </label>
                </div>
                
                <div class="permissions-grid">
                  <div v-for="module in rbacModules" :key="module.name" class="module-section">
                    <div class="module-header">
                      <h5 class="module-title">{{ module.displayName }}</h5>
                      <label class="module-select-all">
                        <input 
                          type="checkbox" 
                          v-model="moduleSelectAll[module.name]"
                          @change="toggleModulePermissions(module.name)"
                          :disabled="isLoading"
                        >
                        <span class="module-select-all-label">Select All</span>
                      </label>
                    </div>
                    <div class="permissions-list">
                      <label v-for="permission in module.permissions" :key="permission.field" class="permission-item">
                        <input 
                          type="checkbox" 
                          v-model="selectedPermissions[permission.field]"
                          @change="updateModuleSelectAll(module.name)"
                          :disabled="isLoading"
                        >
                        <span class="permission-label">{{ permission.label }}</span>
                      </label>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="input-group">
                <label for="isActive">Is Active</label>
                <div class="input-wrapper">
                  <div class="input-icon">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2"/>
                      <polyline points="22 4 12 14.01 9 11.01" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <select 
                    id="isActive" 
                    v-model="formData.isActive" 
                    :disabled="isLoading"
                  >
                    <option value="Y">Yes</option>
                    <option value="N">No</option>
                  </select>
                </div>
              </div>
            </div>
            
            <button 
              type="submit" 
              class="action-button" 
              :disabled="isLoading || !isFormValid"
            >
              <span v-if="!isLoading" class="button-text">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                  <circle cx="8.5" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                  <line x1="20" y1="8" x2="20" y2="14" stroke="currentColor" stroke-width="2"/>
                  <line x1="23" y1="11" x2="17" y2="11" stroke="currentColor" stroke-width="2"/>
                </svg>
                Create User
              </span>
              <span v-else class="loading-content">
                <div class="spinner"></div>
                <span>Creating User...</span>
              </span>
            </button>
            
            <div v-if="errorMessage" class="error-alert">
              <div class="error-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2"/>
                  <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <span>{{ errorMessage }}</span>
              <div class="error-close" @click="errorMessage = ''">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
                  <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
            </div>
            
            <div v-if="successMessage" class="success-alert">
              <div class="success-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <span>{{ successMessage }}</span>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { API_BASE_URL, API_ENDPOINTS } from '../../config/api.js'

const props = defineProps({
  showModal: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

// Reactive data
const formData = ref({
  username: '',
  password: '',
  email: '',
  firstName: '',
  lastName: '',
  departmentId: '',
  role: '',
  isActive: 'Y'
})

const departments = ref([])
const availableRoles = ref([])
const isLoading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const passwordFieldType = ref('password')
const showCustomRoleInput = ref(false)
const customRole = ref('')

// RBAC permissions structure
const rbacModules = ref([
  {
    name: 'compliance',
    displayName: 'Compliance Module',
    permissions: [
      { field: 'create_compliance', label: 'Create Compliance' },
      { field: 'edit_compliance', label: 'Edit Compliance' },
      { field: 'approve_compliance', label: 'Approve Compliance' },
      { field: 'view_all_compliance', label: 'View All Compliance' },
      { field: 'compliance_performance_analytics', label: 'Compliance Performance Analytics' }
    ]
  },
  {
    name: 'policy',
    displayName: 'Policy Module',
    permissions: [
      { field: 'create_policy', label: 'Create Policy' },
      { field: 'edit_policy', label: 'Edit Policy' },
      { field: 'approve_policy', label: 'Approve Policy' },
      { field: 'create_framework', label: 'Create Framework' },
      { field: 'approve_framework', label: 'Approve Framework' },
      { field: 'view_all_policy', label: 'View All Policy' },
      { field: 'policy_performance_analytics', label: 'Policy Performance Analytics' }
    ]
  },
  {
    name: 'audit',
    displayName: 'Audit Module',
    permissions: [
      { field: 'assign_audit', label: 'Assign Audit' },
      { field: 'conduct_audit', label: 'Conduct Audit' },
      { field: 'review_audit', label: 'Review Audit' },
      { field: 'view_audit_reports', label: 'View Audit Reports' },
      { field: 'audit_performance_analytics', label: 'Audit Performance Analytics' }
    ]
  },
  {
    name: 'risk',
    displayName: 'Risk Module',
    permissions: [
      { field: 'create_risk', label: 'Create Risk' },
      { field: 'edit_risk', label: 'Edit Risk' },
      { field: 'approve_risk', label: 'Approve Risk' },
      { field: 'assign_risk', label: 'Assign Risk' },
      { field: 'evaluate_assigned_risk', label: 'Evaluate Assigned Risk' },
      { field: 'view_all_risk', label: 'View All Risk' },
      { field: 'risk_performance_analytics', label: 'Risk Performance Analytics' }
    ]
  },
  {
    name: 'incident',
    displayName: 'Incident Module',
    permissions: [
      { field: 'create_incident', label: 'Create Incident' },
      { field: 'edit_incident', label: 'Edit Incident' },
      { field: 'assign_incident', label: 'Assign Incident' },
      { field: 'evaluate_assigned_incident', label: 'Evaluate Assigned Incident' },
      { field: 'escalate_to_risk', label: 'Escalate to Risk' },
      { field: 'view_all_incident', label: 'View All Incident' },
      { field: 'incident_performance_analytics', label: 'Incident Performance Analytics' }
    ]
  }
])

const selectedPermissions = ref({})
const selectAllPermissions = ref(false)
const moduleSelectAll = ref({})

// Computed properties
const isFormValid = computed(() => {
  return formData.value.username && 
         formData.value.password && 
         formData.value.email && 
         formData.value.firstName && 
         formData.value.lastName && 
         formData.value.departmentId &&
         formData.value.role
})

// Methods
const closeModal = () => {
  resetForm()
  emit('close')
}

const resetForm = () => {
  formData.value = {
    username: '',
    password: '',
    email: '',
    firstName: '',
    lastName: '',
    departmentId: '',
    role: '',
    isActive: 'Y'
  }
  errorMessage.value = ''
  successMessage.value = ''
  showCustomRoleInput.value = false
  customRole.value = ''
  selectedPermissions.value = {}
  selectAllPermissions.value = false
  moduleSelectAll.value = {}
}

const togglePasswordVisibility = () => {
  passwordFieldType.value = passwordFieldType.value === 'password' ? 'text' : 'password'
}

const onRoleChange = () => {
  if (formData.value.role === '__custom__') {
    showCustomRoleInput.value = true
    formData.value.role = ''
    selectedPermissions.value = {}
  } else if (formData.value.role) {
    showCustomRoleInput.value = false
    customRole.value = ''
    // Load default permissions for the selected role
    loadDefaultPermissionsForRole(formData.value.role)
  } else {
    showCustomRoleInput.value = false
    customRole.value = ''
    selectedPermissions.value = {}
  }
}

const loadDefaultPermissionsForRole = async (role) => {
  try {
    // Fetch default permissions for this role from the backend
    const response = await axios.get(`/api/rbac/role-permissions/${encodeURIComponent(role)}/`)
    if (response.data && response.data.success) {
      selectedPermissions.value = response.data.permissions
    } else {
      // Set default permissions based on role
      setDefaultPermissionsForRole(role)
    }
  } catch (error) {
    console.error('Error loading role permissions:', error)
    // Set default permissions based on role
    setDefaultPermissionsForRole(role)
  }
}

const setDefaultPermissionsForRole = (role) => {
  // Initialize all permissions as false
  const permissions = {}
  rbacModules.value.forEach(module => {
    module.permissions.forEach(permission => {
      permissions[permission.field] = false
    })
  })
  
  // Set default permissions based on role
  switch (role) {
    case 'GRC Administrator':
      Object.keys(permissions).forEach(key => {
        permissions[key] = true
      })
      break
    case 'Compliance Manager':
      permissions.create_compliance = true
      permissions.edit_compliance = true
      permissions.approve_compliance = true
      permissions.view_all_compliance = true
      permissions.compliance_performance_analytics = true
      break
    case 'Policy Manager':
      permissions.create_policy = true
      permissions.edit_policy = true
      permissions.approve_policy = true
      permissions.create_framework = true
      permissions.approve_framework = true
      permissions.view_all_policy = true
      permissions.policy_performance_analytics = true
      break
    case 'Risk Manager':
      permissions.create_risk = true
      permissions.edit_risk = true
      permissions.approve_risk = true
      permissions.assign_risk = true
      permissions.view_all_risk = true
      permissions.risk_performance_analytics = true
      break
    case 'Incident Response Manager':
      permissions.create_incident = true
      permissions.edit_incident = true
      permissions.assign_incident = true
      permissions.view_all_incident = true
      permissions.incident_performance_analytics = true
      break
    case 'End User':
      // Minimal permissions for end users
      break
    default:
      // For custom roles, start with no permissions
      break
  }
  
  selectedPermissions.value = permissions
  
  // Initialize module select all states
  rbacModules.value.forEach(module => {
    moduleSelectAll.value[module.name] = false
  })
  
  // Update global select all state
  updateGlobalSelectAll()
}

const toggleAllPermissions = () => {
  const allPermissions = {}
  rbacModules.value.forEach(module => {
    module.permissions.forEach(permission => {
      allPermissions[permission.field] = selectAllPermissions.value
    })
  })
  selectedPermissions.value = allPermissions
  
  // Update module select all states
  rbacModules.value.forEach(module => {
    moduleSelectAll.value[module.name] = selectAllPermissions.value
  })
}

const toggleModulePermissions = (moduleName) => {
  const module = rbacModules.value.find(m => m.name === moduleName)
  if (module) {
    module.permissions.forEach(permission => {
      selectedPermissions.value[permission.field] = moduleSelectAll.value[moduleName]
    })
  }
  
  // Update global select all state
  updateGlobalSelectAll()
}

const updateModuleSelectAll = (moduleName) => {
  const module = rbacModules.value.find(m => m.name === moduleName)
  if (module) {
    const allChecked = module.permissions.every(permission => 
      selectedPermissions.value[permission.field]
    )
    moduleSelectAll.value[moduleName] = allChecked
  }
  
  // Update global select all state
  updateGlobalSelectAll()
}

const updateGlobalSelectAll = () => {
  const allPermissions = rbacModules.value.flatMap(module => 
    module.permissions.map(permission => permission.field)
  )
  const allChecked = allPermissions.every(field => 
    selectedPermissions.value[field]
  )
  selectAllPermissions.value = allChecked
}

const addCustomRole = () => {
  if (customRole.value.trim()) {
    const newRole = customRole.value.trim()
    if (!availableRoles.value.includes(newRole)) {
      availableRoles.value.push(newRole)
    }
    formData.value.role = newRole
    showCustomRoleInput.value = false
    customRole.value = ''
  }
}

const fetchDepartments = async () => {
  try {
    const response = await axios.get(`${API_ENDPOINTS.DEPARTMENTS}`, {
      headers: {
        'Content-Type': 'application/json'
      }
    })
    if (response.data && response.data.success) {
      departments.value = response.data.departments
    }
  } catch (error) {
    console.error('Error fetching departments:', error)
    // Set some default departments for testing if API fails
    departments.value = [
      { id: 1, name: 'Information Technology' },
      { id: 2, name: 'Human Resources' },
      { id: 3, name: 'Finance' },
      { id: 4, name: 'Legal' },
      { id: 5, name: 'Operations' },
      { id: 6, name: 'Marketing' },
      { id: 7, name: 'Sales' },
      { id: 8, name: 'Customer Support' }
    ]
    console.log('Using fallback departments due to API error')
  }
}

const fetchRoles = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/rbac/roles/`, {
      headers: {
        'Content-Type': 'application/json'
      }
    })
    if (response.data && response.data.success) {
      availableRoles.value = response.data.roles
    }
  } catch (error) {
    console.error('Error fetching roles:', error)
    // Set default roles from RBAC model
    availableRoles.value = [
      'GRC Administrator',
      'Compliance Manager',
      'Compliance Officer',
      'Compliance Approver',
      'Executive/Senior Management',
      'Policy Manager',
      'Policy Approver',
      'Audit Manager',
      'Internal Auditor',
      'External Auditor',
      'Audit Reviewer',
      'Risk Manager',
      'Risk Analyst',
      'Risk Reviewer',
      'Incident Response Manager',
      'Incident Analyst',
      'Department Manager',
      'End User'
    ]
    console.log('Using fallback roles due to API error')
  }
}

const createUser = async () => {
  try {
    isLoading.value = true
    errorMessage.value = ''
    successMessage.value = ''
    
    console.log('Form validation check:', {
      username: formData.value.username,
      password: formData.value.password,
      email: formData.value.email,
      firstName: formData.value.firstName,
      lastName: formData.value.lastName,
      departmentId: formData.value.departmentId,
      role: formData.value.role,
      isFormValid: isFormValid.value
    })
    
    if (!isFormValid.value) {
      errorMessage.value = 'Please fill in all required fields'
      return
    }
    
    // Get current timestamp in ISO format
    const currentTime = new Date().toISOString()
    
    const requestData = {
      username: formData.value.username,
      password: formData.value.password,
      email: formData.value.email,
      firstName: formData.value.firstName,
      lastName: formData.value.lastName,
      departmentId: formData.value.departmentId,
      role: formData.value.role,
      isActive: formData.value.isActive,
      permissions: selectedPermissions.value,
      createdAt: currentTime,
      updatedAt: currentTime
    }
    
    console.log('Sending registration data:', requestData)
    console.log('API_BASE_URL:', API_BASE_URL)
    console.log('Full URL:', `${API_BASE_URL}/api/register/`)
    
    const response = await axios.post(`${API_BASE_URL}/api/register/`, requestData, {
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.data && response.data.success) {
      successMessage.value = 'User created successfully!'
      setTimeout(() => {
        closeModal()
      }, 2000)
    } else {
      errorMessage.value = response.data.message || 'Failed to create user'
    }
  } catch (error) {
    if (error.response && error.response.data) {
      errorMessage.value = error.response.data.message || 'An error occurred while creating the user'
    } else {
      errorMessage.value = 'Unable to connect to server. Please check your connection.'
    }
    console.error('❌ Create user error:', error)
  } finally {
    isLoading.value = false
  }
}

// Lifecycle - only fetch data when modal is shown
watch(() => props.showModal, (newValue) => {
  if (newValue) {
    // Only fetch data when modal is opened
    fetchDepartments()
    fetchRoles()
  }
})
</script>

<style scoped>
.create-user-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal-content {
  position: relative;
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  animation: modalSlideIn 0.3s ease-out;
}

.modal-content.fullscreen {
  width: 100%;
  max-width: 100%;
  height: 100vh;
  max-height: 100vh;
  margin: 0;
  border-radius: 0;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 24px 16px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.modal-header h3 svg {
  color: #3b82f6;
}

.close-button {
  background: none;
  border: none;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s;
}

.close-button:hover {
  background: #f3f4f6;
  color: #374151;
}

.modal-body {
  padding: 32px;
  height: calc(100% - 80px);
  overflow-y: auto;
}

.step-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.step-description {
  margin: 0 0 16px 0;
  color: #6b7280;
  font-size: 14px;
  line-height: 1.5;
}

.create-user-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
  margin-bottom: 20px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-group label {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #f9fafb;
  transition: all 0.2s;
  min-height: 56px;
}

.input-wrapper:focus-within {
  border-color: #3b82f6;
  background: white;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  color: #6b7280;
}

.input-wrapper input,
.input-wrapper select {
  flex: 1;
  border: none;
  background: transparent;
  padding: 16px 20px;
  font-size: 16px;
  color: #111827;
  outline: none;
}

.input-wrapper input::placeholder {
  color: #9ca3af;
}

.input-wrapper select {
  cursor: pointer;
}

.role-select-container {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.custom-role-input {
  margin-top: 8px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 14px;
  background: white;
}

.password-toggle {
  background: none;
  border: none;
  padding: 12px;
  color: #6b7280;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.password-toggle:hover {
  background: #f3f4f6;
  color: #374151;
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 18px 32px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 16px;
}

.action-button:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.action-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.button-text {
  display: flex;
  align-items: center;
  gap: 8px;
}

.loading-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-alert,
.success-alert {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  margin-top: 16px;
}

.error-alert {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
}

.success-alert {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #16a34a;
}

.error-icon,
.success-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.error-close {
  margin-left: auto;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
}

.error-close:hover {
  background: rgba(220, 38, 38, 0.1);
}

/* Permissions Section Styles */
.permissions-section {
  margin-top: 24px;
  padding: 24px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.permissions-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.permissions-title svg {
  color: #3b82f6;
}

.permissions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.module-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #e2e8f0;
}

.module-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  border-bottom: 2px solid #3b82f6;
  padding-bottom: 8px;
}

.permissions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.permission-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.permission-item:hover {
  background: #f1f5f9;
}

.permission-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: #3b82f6;
}

.permission-label {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}

/* Select All Styles */
.global-select-all {
  margin-bottom: 24px;
  padding: 16px;
  background: #3b82f6;
  border-radius: 8px;
  border: 2px solid #2563eb;
}

.select-all-item {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.select-all-item input[type="checkbox"] {
  width: 20px;
  height: 20px;
  accent-color: white;
}

.select-all-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: white;
}

.select-all-label svg {
  color: white;
}

.module-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #3b82f6;
}

.module-select-all {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.module-select-all:hover {
  background: #f1f5f9;
}

.module-select-all input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #3b82f6;
}

.module-select-all-label {
  font-size: 12px;
  font-weight: 600;
  color: #3b82f6;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Responsive design */
@media (max-width: 768px) {
  .modal-content.fullscreen {
    width: 100%;
    height: 100vh;
    max-width: 100%;
    max-height: 100vh;
    margin: 0;
    border-radius: 0;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .modal-body {
    padding: 16px;
  }
}
</style> 