/**
 * Framework Context Composable
 * 
 * This composable provides framework context functionality for all modules.
 * It fetches the currently selected framework from the backend session
 * and provides it to components.
 */

import { ref, onMounted } from 'vue'
import axios from 'axios'
import { API_ENDPOINTS } from '@/config/api.js'

export function useFrameworkContext() {
  const currentFrameworkId = ref(null)
  const currentFramework = ref(null)
  const isFrameworkFiltered = ref(false)
  const frameworkLoading = ref(false)
  const frameworkError = ref(null)

  /**
   * Fetch the currently selected framework from session
   */
  const fetchCurrentFramework = async () => {
    try {
      frameworkLoading.value = true
      frameworkError.value = null
      
      console.log('[Framework Context] Fetching current framework from session...')
      
      const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED, {
        params: {
          userId: localStorage.getItem('user_id') || 'default_user'
        }
      })
      
      if (response.data && response.data.success) {
        currentFrameworkId.value = response.data.frameworkId
        isFrameworkFiltered.value = response.data.hasFramework
        
        if (currentFrameworkId.value) {
          console.log(`[Framework Context] ✅ Framework filter active: ${currentFrameworkId.value}`)
          
          // Fetch framework details if available
          try {
            const frameworkResponse = await axios.get(
              API_ENDPOINTS.FRAMEWORK_GET_BY_ID(currentFrameworkId.value)
            )
            if (frameworkResponse.data) {
              currentFramework.value = frameworkResponse.data
              console.log(`[Framework Context] Framework details loaded: ${currentFramework.value.FrameworkName}`)
            }
          } catch (error) {
            console.warn('[Framework Context] Could not fetch framework details:', error)
          }
        } else {
          console.log('[Framework Context] ℹ️ No framework filter (viewing all data)')
        }
        
        return {
          frameworkId: currentFrameworkId.value,
          framework: currentFramework.value,
          isFiltered: isFrameworkFiltered.value
        }
      } else {
        console.warn('[Framework Context] ⚠️ Failed to get framework from session')
        return null
      }
    } catch (error) {
      console.error('[Framework Context] ❌ Error fetching framework context:', error)
      frameworkError.value = error.message
      return null
    } finally {
      frameworkLoading.value = false
    }
  }

  /**
   * Get framework filter info for display
   */
  const getFrameworkFilterInfo = () => {
    if (!isFrameworkFiltered.value) {
      return {
        message: 'Viewing all frameworks',
        type: 'all',
        frameworkId: null
      }
    }
    
    return {
      message: currentFramework.value 
        ? `Filtered by: ${currentFramework.value.FrameworkName}`
        : `Filtered by framework: ${currentFrameworkId.value}`,
      type: 'filtered',
      frameworkId: currentFrameworkId.value,
      framework: currentFramework.value
    }
  }

  /**
   * Auto-fetch on component mount
   */
  onMounted(() => {
    fetchCurrentFramework()
  })

  return {
    currentFrameworkId,
    currentFramework,
    isFrameworkFiltered,
    frameworkLoading,
    frameworkError,
    fetchCurrentFramework,
    getFrameworkFilterInfo
  }
}


