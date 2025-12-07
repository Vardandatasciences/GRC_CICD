import { ref, computed } from 'vue'
import { eventService } from '../services/api'

// Global state for event permissions
const eventPermissions = ref({})
const accessibleModules = ref([])
const isLoading = ref(false)
const error = ref(null)

export function useEventPermissions() {
  // Fetch user event permissions from backend
  const fetchEventPermissions = async () => {
    try {
      isLoading.value = true
      error.value = null
      
      const response = await eventService.getUserEventPermissions()
      
      if (response.data.success) {
        eventPermissions.value = response.data.permissions
        accessibleModules.value = response.data.accessible_modules
        console.log('Event permissions loaded:', eventPermissions.value)
        console.log('Accessible modules:', accessibleModules.value)
      } else {
        error.value = response.data.message || 'Failed to fetch permissions'
      }
    } catch (err) {
      console.error('Error fetching event permissions:', err)
      console.error('Error details:', err.response?.data || err.message)
      error.value = 'Failed to fetch permissions'
      
      // Set default permissions for GRC Administrator as fallback
      // This ensures the user can still access the system even if permissions API fails
      eventPermissions.value = {
        view_all_event: true,
        view_module_event: true,
        create_event: true,
        edit_event: true,
        approve_event: true,
        reject_event: true,
        archive_event: true,
        event_performance_analytics: true,
        is_admin: true,
        role: 'GRC Administrator'
      }
      accessibleModules.value = ['Compliance Management', 'Policy Management', 'Audit Management', 'Risk Management', 'Incident Management']
    } finally {
      isLoading.value = false
    }
  }

  // Computed properties for permission checks
  const canViewAllEvents = computed(() => {
    return eventPermissions.value.view_all_event || eventPermissions.value.is_admin
  })

  const canViewModuleEvents = computed(() => {
    return eventPermissions.value.view_module_event || eventPermissions.value.is_admin
  })

  const canCreateEvents = computed(() => {
    return eventPermissions.value.create_event || eventPermissions.value.is_admin
  })

  const canEditEvents = computed(() => {
    return eventPermissions.value.edit_event || eventPermissions.value.is_admin
  })

  const canApproveEvents = computed(() => {
    return eventPermissions.value.approve_event || eventPermissions.value.is_admin
  })

  const canRejectEvents = computed(() => {
    return eventPermissions.value.reject_event || eventPermissions.value.is_admin
  })

  const canArchiveEvents = computed(() => {
    return eventPermissions.value.archive_event || eventPermissions.value.is_admin
  })

  const canViewEventAnalytics = computed(() => {
    return eventPermissions.value.event_performance_analytics || eventPermissions.value.is_admin
  })

  const isAdmin = computed(() => {
    return eventPermissions.value.is_admin
  })

  const userRole = computed(() => {
    return eventPermissions.value.role
  })

  // Check if user can view events from a specific module
  const canViewModule = (moduleName) => {
    if (canViewAllEvents.value) {
      return true
    }
    
    if (canViewModuleEvents.value) {
      // Check if the module name matches any of the accessible modules
      return accessibleModules.value.includes(moduleName)
    }
    
    return false
  }

  // Check if user has any event permissions
  const hasEventAccess = computed(() => {
    // If permissions haven't been loaded yet or there's an error, allow access temporarily
    // This prevents showing "Access Denied" while permissions are being fetched
    if (isLoading.value || error.value) {
      return true
    }
    
    // If permissions object is empty (API call failed), allow access as fallback
    if (Object.keys(eventPermissions.value).length === 0) {
      return true
    }
    
    return canViewAllEvents.value || canViewModuleEvents.value || canCreateEvents.value
  })

  // Get filtered modules based on user permissions
  const getFilteredModules = (allModules) => {
    if (canViewAllEvents.value) {
      return allModules
    }
    
    if (canViewModuleEvents.value) {
      return allModules.filter(module => 
        accessibleModules.value.includes(module)
      )
    }
    
    return []
  }

  // Check if user can perform action on event
  const canPerformAction = (action) => {
    switch (action) {
      case 'view':
        return canViewAllEvents.value || canViewModuleEvents.value
      case 'create':
        return canCreateEvents.value
      case 'edit':
        return canEditEvents.value
      case 'approve':
        return canApproveEvents.value
      case 'reject':
        return canRejectEvents.value
      case 'archive':
        return canArchiveEvents.value
      case 'analytics':
        return canViewEventAnalytics.value
      default:
        return false
    }
  }

  // Reset permissions (useful for logout)
  const resetPermissions = () => {
    eventPermissions.value = {}
    accessibleModules.value = []
    error.value = null
  }

  return {
    // State
    eventPermissions: computed(() => eventPermissions.value),
    accessibleModules: computed(() => accessibleModules.value),
    isLoading: computed(() => isLoading.value),
    error: computed(() => error.value),
    
    // Permission checks
    canViewAllEvents,
    canViewModuleEvents,
    canCreateEvents,
    canEditEvents,
    canApproveEvents,
    canRejectEvents,
    canArchiveEvents,
    canViewEventAnalytics,
    isAdmin,
    userRole,
    hasEventAccess,
    
    // Methods
    fetchEventPermissions,
    canViewModule,
    getFilteredModules,
    canPerformAction,
    resetPermissions
  }
}
