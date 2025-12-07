<template>
  <div class="events-filters-container">
    <!-- All filters and export button in one horizontal row -->
    <div class="events-filters-row">
      <!-- Dropdowns -->
      <div class="events-dropdowns-row">
        <div class="events-dropdown-container">
          <label class="events-dropdown-label">Framework</label>
           <CustomDropdown
             :options="[
               { value: '', label: loadingFrameworks ? 'Loading frameworks...' : 'All Frameworks' },
               ...frameworks.map(fw => ({ value: fw.FrameworkName || fw.name, label: fw.FrameworkName || fw.name }))
             ]"
             v-model="selectedFramework"
             :disabled="loadingFrameworks"
           />
          <div v-if="frameworksError" class="events-dropdown-error">
            {{ frameworksError }}
          </div>
        </div>

        <div class="events-dropdown-container">
          <label class="events-dropdown-label">Module</label>
           <CustomDropdown
             :options="[
               { value: '', label: loadingModules ? 'Loading modules...' : 'All Modules' },
               ...modules.map(mod => ({ value: mod.modulename || mod.name, label: mod.modulename || mod.name }))
             ]"
             v-model="selectedModule"
             :disabled="loadingModules"
           />
          <div v-if="modulesError" class="events-dropdown-error">
            {{ modulesError }}
          </div>
        </div>

        <div class="events-dropdown-container">
          <label class="events-dropdown-label">Category</label>
          <CustomDropdown
            :options="[
              { value: '', label: loadingCategories ? 'Loading categories...' : 'All Categories' },
              ...categories.map(cat => ({ value: cat, label: cat }))
            ]"
            v-model="selectedCategory"
            :disabled="loadingCategories"
          />
          <div v-if="categoriesError" class="events-dropdown-error">
            {{ categoriesError }}
          </div>
        </div>

        <div v-if="showAdvanced" class="events-dropdown-container">
          <label class="events-dropdown-label">Owner</label>
          <CustomDropdown
            :options="[
              { value: '', label: loadingOwners ? 'Loading owners...' : 'All Owners' },
              ...owners.map(owner => ({ value: owner, label: owner }))
            ]"
            v-model="selectedOwner"
            :disabled="loadingOwners"
          />
          <div v-if="ownersError" class="events-dropdown-error">
            {{ ownersError }}
          </div>
        </div>
      </div>

      <!-- Export Controls -->
      <div class="events-export-controls">
        <div class="relative export-dropdown-container">
          <button
            @click="toggleExportDropdown"
            class="events-export-btn"
          >
            <i class="fas fa-download"></i>
            <span>Export</span>
          </button>
          <div v-if="showExportDropdown" class="events-export-dropdown">
            <div class="events-export-header">
              Export Format
            </div>
            <button
              v-for="format in exportFormats"
              :key="format"
              @click="handleExport(format)"
              class="events-export-option"
            >
              <span class="events-export-format-text">{{ format }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { MODULES, CATEGORIES } from '../../utils/constants'
import { eventService } from '../../services/api'
import CustomDropdown from './CustomDropdown.vue'
import axios from 'axios'
import './EventFilters.css'
import '@fortawesome/fontawesome-free/css/all.min.css'

export default {
  name: 'EventFilters',
  components: {
    CustomDropdown
  },
  props: {
    onExport: {
      type: Function,
      required: true
    },
    showAdvanced: {
      type: Boolean,
      default: true
    },
    selectedFrameworkFromSession: {
      type: String,
      default: null
    }
  },
  emits: ['filter-change'],
  setup(props, { emit }) {
    const showExportDropdown = ref(false)
    const exportFormats = ['Excel', 'CSV', 'PDF', 'JSON', 'XML']
    
    // Filter data
    const frameworks = ref([])
    const modules = ref([])
    const categories = ref([])
    const owners = ref([])
    
    // Selected values
    const selectedFramework = ref('')
    const selectedModule = ref('')
    const selectedCategory = ref('')
    const selectedOwner = ref('')
    
    // Loading states
    const loadingFrameworks = ref(false)
    const loadingModules = ref(false)
    const loadingCategories = ref(false)
    const loadingOwners = ref(false)
    
    // Error states
    const frameworksError = ref(null)
    const modulesError = ref(null)
    const categoriesError = ref(null)
    const ownersError = ref(null)

    // Fetch frameworks from API (use same endpoint as Policy components)
    const fetchFrameworks = async () => {
      loadingFrameworks.value = true
      frameworksError.value = null
      
      try {
        console.log('🚀 DEBUG: EventFilters fetchFrameworks called - using /api/frameworks/ endpoint')
        
        // Use the same framework endpoint as Policy components to ensure consistency
        const response = await axios.get('/api/frameworks/', {
          params: {
            _t: Date.now() // Cache busting parameter
          }
        })
        console.log('🔍 DEBUG: Frameworks response in EventFilters:', response.data)
        
        // Map the response to match the expected format
        frameworks.value = response.data.map(fw => ({
          FrameworkId: fw.FrameworkId,
          FrameworkName: fw.FrameworkName
        }))
        
        console.log('✅ DEBUG: Frameworks loaded in EventFilters:', frameworks.value.length)
        console.log('📝 DEBUG: Available frameworks:', frameworks.value.map(f => `${f.FrameworkName} (ID: ${f.FrameworkId})`))
        
      } catch (error) {
        console.error('Error fetching frameworks:', error)
        frameworksError.value = 'Error loading frameworks'
        // Fallback to hardcoded frameworks if API fails
        // Note: Must match backend fallback frameworks in get_events_list
        frameworks.value = [
          { FrameworkId: 1, FrameworkName: 'Basel III Framework' }, // Match backend default
          { FrameworkId: 2, FrameworkName: 'NIST' },
          { FrameworkId: 3, FrameworkName: 'ISO 27001' },
          { FrameworkId: 4, FrameworkName: 'COBIT' },
          { FrameworkId: 5, FrameworkName: 'PCI DSS' },
          { FrameworkId: 6, FrameworkName: 'HIPAA' },
          { FrameworkId: 7, FrameworkName: 'SOX' },
          { FrameworkId: 8, FrameworkName: 'GDPR' }
        ]
      } finally {
        loadingFrameworks.value = false
      }
    }

    // Fetch modules from API (same as EventCreation)
    const fetchModules = async () => {
      loadingModules.value = true
      modulesError.value = null
      
      try {
        const response = await eventService.getModules()
        if (response.data.success) {
          modules.value = response.data.modules
        } else {
          modulesError.value = 'Failed to fetch modules'
        }
      } catch (error) {
        console.error('Error fetching modules:', error)
        modulesError.value = 'Error loading modules'
        // Fallback to hardcoded modules if API fails
        modules.value = [
          { moduleid: 1, modulename: 'Policy Management' },
          { moduleid: 2, modulename: 'Compliance Management' },
          { moduleid: 3, modulename: 'Audit Management' },
          { moduleid: 4, modulename: 'Incident Management' },
          { moduleid: 5, modulename: 'Risk Management' }
        ]
      } finally {
        loadingModules.value = false
      }
    }

    // Use categories from constants (same as EventCreation)
    const fetchCategories = async () => {
      loadingCategories.value = true
      categoriesError.value = null
      
      try {
        // Use the same CATEGORIES constant as EventCreation
        categories.value = CATEGORIES
      } catch (error) {
        console.error('Error loading categories:', error)
        categoriesError.value = 'Error loading categories'
        categories.value = CATEGORIES // Fallback to constants
      } finally {
        loadingCategories.value = false
      }
    }

    // Fetch all users from database
    const fetchOwners = async () => {
      loadingOwners.value = true
      ownersError.value = null
      
      try {
        console.log('🔄 DEBUG: Fetching users for owner dropdown...')
        const response = await eventService.getUsers()
        console.log('🔍 DEBUG: Users API response:', response.data)
        
        if (response.data.success) {
          console.log('✅ DEBUG: Users fetched successfully:', response.data.users)
          
          // Format users as "FirstName LastName" for display
          const formattedUsers = response.data.users.map(user => {
            const fullName = `${user.FirstName || ''} ${user.LastName || ''}`.trim()
            console.log('👤 DEBUG: Formatting user:', user, '-> Full name:', fullName)
            return fullName
          }).filter(Boolean)
          
          console.log('📝 DEBUG: Formatted users for dropdown:', formattedUsers)
          owners.value = formattedUsers
        } else {
          console.error('❌ DEBUG: API returned success: false:', response.data)
          ownersError.value = response.data.error || 'Failed to fetch users'
        }
      } catch (error) {
        console.error('❌ DEBUG: Error fetching owners:', error)
        console.error('❌ DEBUG: Error response:', error.response?.data)
        ownersError.value = `Error loading owners: ${error.message}`
        // Fallback to hardcoded owners
        owners.value = ['John Mathews', 'Rahul Khanna', 'Priya Sinha']
      } finally {
        loadingOwners.value = false
      }
    }

    const toggleExportDropdown = () => {
      showExportDropdown.value = !showExportDropdown.value
    }

    const handleExport = (format) => {
      props.onExport(format)
      showExportDropdown.value = false
    }

    // Close dropdown when clicking outside
    const handleClickOutside = (event) => {
      if (showExportDropdown.value && !event.target.closest('.export-dropdown-container')) {
        showExportDropdown.value = false
      }
    }

    onMounted(() => {
      document.addEventListener('click', handleClickOutside)
    })

    onUnmounted(() => {
      document.removeEventListener('click', handleClickOutside)
    })

    // Emit filter changes
    const emitFilterChange = () => {
      const filterData = {
        framework: selectedFramework.value,
        module: selectedModule.value,
        category: selectedCategory.value,
        owner: selectedOwner.value
      }
      emit('filter-change', filterData)
    }

    // Watch for filter changes and emit them
    watch([selectedFramework, selectedModule, selectedCategory, selectedOwner], () => {
      emitFilterChange()
    }, { immediate: true })

    // Watch for selected framework from session and update the dropdown
    watch(() => props.selectedFrameworkFromSession, (newFrameworkId) => {
      console.log('🔍 DEBUG: Framework watcher triggered with ID:', newFrameworkId)
      console.log('🔍 DEBUG: Available frameworks count:', frameworks.value.length)
      console.log('🔍 DEBUG: Available frameworks:', frameworks.value.map(f => `${f.FrameworkName} (ID: ${f.FrameworkId})`))
      
      if (newFrameworkId) {
        // Find the framework name from the frameworks list - try multiple matching approaches
        let framework = frameworks.value.find(fw => fw.FrameworkId == newFrameworkId)
        console.log('🔍 DEBUG: Looking for framework ID:', newFrameworkId, 'Type:', typeof newFrameworkId)
        console.log('🔍 DEBUG: Found framework (loose match):', framework)
        
        // If not found with loose match, try strict string comparison
        if (!framework) {
          framework = frameworks.value.find(fw => String(fw.FrameworkId) === String(newFrameworkId))
          console.log('🔍 DEBUG: Found framework (strict string match):', framework)
        }
        
        // If still not found, try number comparison
        if (!framework) {
          framework = frameworks.value.find(fw => Number(fw.FrameworkId) === Number(newFrameworkId))
          console.log('🔍 DEBUG: Found framework (number match):', framework)
        }
        
        if (framework) {
          selectedFramework.value = framework.FrameworkName
          console.log('✅ DEBUG: Updated framework dropdown to show selected framework:', framework.FrameworkName)
          console.log('✅ DEBUG: selectedFramework.value is now:', selectedFramework.value)
        } else {
          console.log('⚠️ DEBUG: Could not find framework with ID:', newFrameworkId)
          console.log('⚠️ DEBUG: Available framework IDs:', frameworks.value.map(fw => `${fw.FrameworkId} (type: ${typeof fw.FrameworkId})`))
          console.log('⚠️ DEBUG: Available framework names:', frameworks.value.map(fw => fw.FrameworkName))
          
          // If we can't find by ID, try to find by name (fallback)
          const frameworkByName = frameworks.value.find(fw => fw.FrameworkName === 'aaaaaaaaaaawerfg')
          if (frameworkByName) {
            console.log('🔄 DEBUG: Using fallback - found framework by name:', frameworkByName)
            selectedFramework.value = frameworkByName.FrameworkName
          }
        }
      } else {
        selectedFramework.value = ''
        console.log('ℹ️ DEBUG: Reset framework dropdown to "All Frameworks"')
      }
    }, { immediate: true })

    // Also watch for frameworks to be loaded and then set the selected framework
    watch(frameworks, (newFrameworks) => {
      console.log('🔍 DEBUG: Frameworks loaded, count:', newFrameworks.length)
      console.log('🔍 DEBUG: Available frameworks:', newFrameworks.map(f => `${f.FrameworkName} (ID: ${f.FrameworkId})`))
      console.log('🔍 DEBUG: Selected framework from session:', props.selectedFrameworkFromSession)
      
      if (newFrameworks.length > 0 && props.selectedFrameworkFromSession) {
        // Try multiple matching approaches
        let framework = newFrameworks.find(fw => fw.FrameworkId == props.selectedFrameworkFromSession)
        console.log('🔍 DEBUG: Looking for framework ID:', props.selectedFrameworkFromSession, 'in loaded frameworks')
        console.log('🔍 DEBUG: Found framework (loose match):', framework)
        
        // If not found with loose match, try strict string comparison
        if (!framework) {
          framework = newFrameworks.find(fw => String(fw.FrameworkId) === String(props.selectedFrameworkFromSession))
          console.log('🔍 DEBUG: Found framework (strict string match):', framework)
        }
        
        // If still not found, try number comparison
        if (!framework) {
          framework = newFrameworks.find(fw => Number(fw.FrameworkId) === Number(props.selectedFrameworkFromSession))
          console.log('🔍 DEBUG: Found framework (number match):', framework)
        }
        
        if (framework) {
          selectedFramework.value = framework.FrameworkName
          console.log('✅ DEBUG: Updated framework dropdown after frameworks loaded:', framework.FrameworkName)
          console.log('✅ DEBUG: selectedFramework.value is now:', selectedFramework.value)
        } else {
          console.log('⚠️ DEBUG: Could not find framework with ID:', props.selectedFrameworkFromSession)
          console.log('⚠️ DEBUG: Available framework IDs:', newFrameworks.map(fw => `${fw.FrameworkId} (type: ${typeof fw.FrameworkId})`))
          console.log('⚠️ DEBUG: Available framework names:', newFrameworks.map(fw => fw.FrameworkName))
          
          // If we can't find by ID, try to find by name (fallback)
          const frameworkByName = newFrameworks.find(fw => fw.FrameworkName === 'aaaaaaaaaaawerfg')
          if (frameworkByName) {
            console.log('🔄 DEBUG: Using fallback - found framework by name:', frameworkByName)
            selectedFramework.value = frameworkByName.FrameworkName
          }
        }
      }
    }, { immediate: true })

    // Fetch all filter data on component mount
    onMounted(async () => {
      await fetchFrameworks()
      fetchModules()
      fetchCategories()
      fetchOwners()
      
      // Force update the selected framework after frameworks are loaded
      if (props.selectedFrameworkFromSession) {
        console.log('🔄 DEBUG: Force updating framework selection on mount')
        const framework = frameworks.value.find(fw => fw.FrameworkId == props.selectedFrameworkFromSession)
        if (framework) {
          selectedFramework.value = framework.FrameworkName
          console.log('✅ DEBUG: Force updated framework dropdown on mount:', framework.FrameworkName)
        }
      }
    })

    return {
      showExportDropdown,
      exportFormats,
      frameworks,
      modules,
      categories,
      owners,
      selectedFramework,
      selectedModule,
      selectedCategory,
      selectedOwner,
      loadingFrameworks,
      loadingModules,
      loadingCategories,
      loadingOwners,
      frameworksError,
      modulesError,
      categoriesError,
      ownersError,
      MODULES,
      CATEGORIES,
      toggleExportDropdown,
      handleExport
    }
  }
}
</script>

