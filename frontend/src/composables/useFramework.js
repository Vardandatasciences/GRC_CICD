import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useStore } from 'vuex'

/**
 * Composable for managing framework selection across all pages
 * This ensures all pages respect the selected framework from the home screen
 */
export function useFramework() {
  const store = useStore()
  
  // Get selected framework from store
  const selectedFramework = computed(() => store.getters['framework/selectedFramework'])
  const selectedFrameworkId = computed(() => store.state.framework.selectedFrameworkId)
  const selectedFrameworkName = computed(() => store.state.framework.selectedFrameworkName)
  const isAllFrameworks = computed(() => store.getters['framework/isAllFrameworks'])
  
  // Load framework from session on mount
  const loadFrameworkFromSession = async () => {
    try {
      await store.dispatch('framework/loadFrameworkFromSession')
    } catch (error) {
      console.error('Error loading framework from session:', error)
    }
  }
  
  // Set framework
  const setFramework = async (id, name) => {
    await store.dispatch('framework/setFramework', { id, name })
  }
  
  // Reset to all frameworks
  const resetFramework = async () => {
    await store.dispatch('framework/resetFramework')
  }
  
  // Watch for framework changes and emit event
  const onFrameworkChange = (callback) => {
    const handleFrameworkChange = (event) => {
      callback(event.detail)
    }
    
    window.addEventListener('framework-changed', handleFrameworkChange)
    
    // Return cleanup function
    return () => {
      window.removeEventListener('framework-changed', handleFrameworkChange)
    }
  }
  
  return {
    selectedFramework,
    selectedFrameworkId,
    selectedFrameworkName,
    isAllFrameworks,
    loadFrameworkFromSession,
    setFramework,
    resetFramework,
    onFrameworkChange
  }
}

/**
 * Composable that automatically loads framework on mount and watches for changes
 * Use this in components that need to react to framework changes
 */
export function useFrameworkWatcher(callback) {
  const { loadFrameworkFromSession, selectedFrameworkId, isAllFrameworks } = useFramework()
  
  let cleanup = null
  
  onMounted(async () => {
    // Load framework from session
    await loadFrameworkFromSession()
    
    // Set up listener for framework changes
    if (callback) {
      cleanup = watch(
        [selectedFrameworkId, isAllFrameworks],
        ([newId, newIsAll]) => {
          callback({
            frameworkId: newIsAll ? null : newId,
            isAllFrameworks: newIsAll
          })
        },
        { immediate: true }
      )
    }
  })
  
  onUnmounted(() => {
    if (cleanup) {
      cleanup()
    }
  })
  
  return {
    selectedFrameworkId,
    isAllFrameworks
  }
}

