import axios from 'axios'
import { API_ENDPOINTS } from '../../config/api.js'

export default {
  namespaced: true,
  
  state: {
    selectedFrameworkId: null,  // null means "All Frameworks"
    selectedFrameworkName: 'All Frameworks',
    frameworks: [],
    isLoading: false
  },
  
  getters: {
    selectedFramework: (state) => {
      if (!state.selectedFrameworkId || state.selectedFrameworkId === 'all') {
        return {
          id: 'all',
          name: 'All Frameworks'
        }
      }
      return {
        id: state.selectedFrameworkId, 
        name: state.selectedFrameworkName
      }
    },
    isAllFrameworks: (state) => {
      return !state.selectedFrameworkId || state.selectedFrameworkId === 'all'
    }
  },
  
  mutations: {
    SET_SELECTED_FRAMEWORK(state, { id, name }) {
      state.selectedFrameworkId = id
      state.selectedFrameworkName = name || 'All Frameworks'
      console.log('📦 Vuex: Framework set to:', { id, name })
    },
    SET_FRAMEWORKS(state, frameworks) {
      state.frameworks = frameworks
    },
    SET_LOADING(state, isLoading) {
      state.isLoading = isLoading
    },
    RESET_FRAMEWORK(state) {
      state.selectedFrameworkId = null
      state.selectedFrameworkName = 'All Frameworks'
      console.log('📦 Vuex: Framework reset to All Frameworks')
    }
  },
  
  actions: {
    async setFramework({ commit, state }, { id, name }) {
      console.log('🎯 Vuex Action: Setting framework to:', { id, name })
      
      // Update local state immediately for instant UI feedback
      commit('SET_SELECTED_FRAMEWORK', { id, name })
      
      // Save to backend session
      try {
        const userId = localStorage.getItem('user_id') || 'default_user'
        const frameworkId = (id === 'all' || !id) ? null : id
        
        console.log('💾 Saving framework to backend session:', { frameworkId, userId })
        
        const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
          frameworkId: frameworkId,
          userId: userId
        })
        
        if (response.data && response.data.success) {
          console.log('✅ Framework saved to backend session successfully')
          
          // Emit a custom event for components that need to react immediately
          window.dispatchEvent(new CustomEvent('framework-changed', { 
            detail: { 
              id: state.selectedFrameworkId, 
              name: state.selectedFrameworkName 
            } 
          }))
        } else {
          console.error('❌ Failed to save framework to backend session')
        }
      } catch (error) {
        console.error('❌ Error saving framework to backend session:', error)
      }
    },
    
    async loadFrameworkFromSession({ commit }) {
      try {
        const userId = localStorage.getItem('user_id') || 'default_user'
        console.log('🔄 Loading framework from session for user:', userId)
        
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED, {
          params: { userId }
        })
        
        console.log('📥 Backend response:', response.data)
        
        if (response.data && response.data.success) {
          if (response.data.frameworkId) {
            commit('SET_SELECTED_FRAMEWORK', {
              id: response.data.frameworkId,
              name: response.data.frameworkName || 'Selected Framework'
            })
            console.log('✅ Loaded framework from session:', {
              id: response.data.frameworkId,
              name: response.data.frameworkName
            })
            
            // Emit event for immediate UI update
            window.dispatchEvent(new CustomEvent('framework-changed', { 
              detail: { 
                id: response.data.frameworkId, 
                name: response.data.frameworkName 
              } 
            }))
          } else {
            commit('RESET_FRAMEWORK')
            console.log('ℹ️ No framework in session, defaulting to All Frameworks')
          }
        } else {
          commit('RESET_FRAMEWORK')
          console.log('ℹ️ No framework in session, defaulting to All Frameworks')
        }
      } catch (error) {
        console.error('❌ Error loading framework from session:', error)
        commit('RESET_FRAMEWORK')
      }
    },
    
    async resetFramework({ commit }) {
      commit('RESET_FRAMEWORK')
      
      // Save "All Frameworks" (null) to backend session
      try {
        const userId = localStorage.getItem('user_id') || 'default_user'
        console.log('🔄 Clearing framework from backend session (All Frameworks selected)')
        
        const response = await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, {
          frameworkId: null,
          userId: userId
        })
        
        if (response.data && response.data.success) {
          console.log('✅ Framework cleared from backend session successfully')
        }
      } catch (error) {
        console.error('❌ Error clearing framework from backend session:', error)
      }
      
      // Emit event
      window.dispatchEvent(new CustomEvent('framework-changed', { 
        detail: { 
          id: null, 
          name: 'All Frameworks' 
        } 
      }))
    },
    
    setFrameworks({ commit }, frameworks) {
      commit('SET_FRAMEWORKS', frameworks)
    }
  }
}

