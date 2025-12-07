<template>
  <div id="app">
    <div v-if="isAuthenticated" class="app-container">
      <!-- Show Sidebar on all pages including home -->
      <Sidebar />
      <!-- Global Navbar for all authenticated pages -->
      <GlobalNavbar />
      <div class="main-content with-sidebar">
        <router-view></router-view>
      </div>
    </div>
    <div v-else class="login-container">
      <router-view></router-view>
    </div>
    <PopupModal />
    <!-- Global Consent Modal -->
    <ConsentModal ref="consentModal" />
    <!-- Debug component - remove in production -->
    <!-- <AuthDebug /> -->
  </div>
</template>
 
<script>
import Sidebar from './components/Policy/Sidebar.vue'
import GlobalNavbar from './components/GlobalNavbar.vue'
import PopupModal from './modules/popup/PopupModal.vue'
import ConsentModal from './components/Consent/ConsentModal.vue'
import consentService from './services/consentService.js'
// import AuthDebug from './components/AuthDebug.vue'
 
export default {
  name: 'App',
  components: {
    Sidebar,
    GlobalNavbar,
    PopupModal,
    ConsentModal
    // AuthDebug
  },
  data() {
    return {
      isAuthenticated: false,
      hasExplicitlyLoggedIn: false
    }
  },
  created() {
    // Clear any stale authentication data on app load
    this.clearStaleAuthData()
   
    // Check authentication status on app load
    this.checkAuthStatus()
    
    // Load framework selection from backend session into Vuex store
    this.$nextTick(() => {
      if (this.isAuthenticated) {
        this.loadFrameworkFromSession()
      }
    })
   
    // Listen for auth changes
    window.addEventListener('authChanged', this.checkAuthStatus)
   
    // Make login/logout methods available globally
    window.onSuccessfulLogin = this.onSuccessfulLogin
    window.onLogout = this.onLogout
    window.forceAuthCheck = this.forceAuthCheck
    window.appComponent = this
   
    // Additional check after a short delay to ensure sidebar is rendered
    this.$nextTick(() => {
      setTimeout(() => {
        this.checkAuthStatus()
      }, 100)
    })
  },
  mounted() {
    // Register consent modal with consent service
    // Use $nextTick to ensure the ref is available
    this.$nextTick(() => {
      if (this.$refs.consentModal) {
        console.log('🔍 [App] Consent modal ref:', this.$refs.consentModal);
        console.log('🔍 [App] Consent modal show method:', typeof this.$refs.consentModal?.show);
        consentService.registerModal(this.$refs.consentModal)
        console.log('✅ Consent modal registered globally')
      } else {
        console.error('❌ [App] Consent modal ref not found!');
      }
    });
  },
  beforeUnmount() {
    window.removeEventListener('authChanged', this.checkAuthStatus)
  },
  methods: {
    clearStaleAuthData() {
      // Clear any stale authentication data that might cause issues
      const hasValidToken = localStorage.getItem('access_token')
      const hasValidUserId = localStorage.getItem('user_id')
      const isLoggedIn = localStorage.getItem('is_logged_in') === 'true'
     
      // If we have partial auth data (incomplete), clear it
      if ((hasValidToken && !hasValidUserId) || (hasValidUserId && !hasValidToken) || (hasValidToken && !isLoggedIn)) {
        console.log('🧹 Clearing stale authentication data')
        localStorage.removeItem('access_token')
        localStorage.removeItem('user_id')
        localStorage.removeItem('is_logged_in')
        localStorage.removeItem('user_email')
        localStorage.removeItem('user_name')
      }
    },
   
    async checkAuthStatus() {
      // Check if user is authenticated by looking for JWT token and user data
      const accessToken = localStorage.getItem('access_token')
      const userId = localStorage.getItem('user_id')
      const isLoggedIn = localStorage.getItem('is_logged_in') === 'true'
     
      // Check if token is expired
      let isTokenValid = true
      let tokenExpired = false
      if (accessToken) {
        try {
          const tokenPayload = JSON.parse(atob(accessToken.split('.')[1]))
          const currentTime = Math.floor(Date.now() / 1000)
          isTokenValid = tokenPayload.exp && tokenPayload.exp > currentTime
          tokenExpired = !isTokenValid
         
          if (tokenExpired) {
            console.warn('⚠️ Token expired, attempting to refresh...')
            // Try to refresh the token
            try {
              const refreshSuccess = await this.attemptTokenRefresh()
              if (refreshSuccess) {
                isTokenValid = true
                console.log('✅ Token refreshed successfully')
              } else {
                console.warn('❌ Token refresh failed')
              }
            } catch (error) {
              console.error('❌ Error during token refresh:', error)
            }
          }
        } catch (error) {
          console.warn('⚠️ Invalid token format:', error)
          isTokenValid = false
        }
      }
     
      // User is authenticated if they have a valid token, user ID, and are marked as logged in
      // On page refresh, if we have valid auth data, consider the user authenticated
      // If token is expired but we have auth data, still show sidebar temporarily while refresh is attempted
      const hasAuthData = !!(accessToken && userId && isLoggedIn)
      this.isAuthenticated = hasAuthData && (isTokenValid || tokenExpired)
     
      // If user is authenticated on page refresh, set hasExplicitlyLoggedIn to true
      if (this.isAuthenticated && !this.hasExplicitlyLoggedIn) {
        this.hasExplicitlyLoggedIn = true
        // Start periodic token refresh for restored authentication
        this.startPeriodicTokenRefresh()
      }
     
      console.log('🔐 Authentication check:', {
        hasToken: !!accessToken,
        hasUserId: !!userId,
        isLoggedIn: isLoggedIn,
        isTokenValid: isTokenValid,
        tokenExpired: tokenExpired,
        hasExplicitlyLoggedIn: this.hasExplicitlyLoggedIn,
        isAuthenticated: this.isAuthenticated,
        sidebarWillRender: this.isAuthenticated
      })
    },
   
    // Load framework from backend session
    async loadFrameworkFromSession() {
      try {
        console.log('🔄 App.vue: Loading framework from backend session...')
        await this.$store.dispatch('framework/loadFrameworkFromSession')
      } catch (error) {
        console.error('❌ App.vue: Error loading framework from session:', error)
      }
    },
    
    // Method to be called when user successfully logs in
    onSuccessfulLogin() {
      this.hasExplicitlyLoggedIn = true
      this.checkAuthStatus()
      // Load framework after successful login
      this.loadFrameworkFromSession()
      this.startPeriodicTokenRefresh()
    },
   
    // Method to be called when user logs out
    async onLogout() {
      this.hasExplicitlyLoggedIn = false
      this.isAuthenticated = false
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_id')
      localStorage.removeItem('is_logged_in')
      localStorage.removeItem('user_email')
      localStorage.removeItem('user_name')
     
      // Stop periodic token refresh
      try {
        const { default: authService } = await import('./services/authService.js')
        authService.stopPeriodicTokenRefresh()
        console.log('🛑 Periodic token refresh stopped on logout')
      } catch (error) {
        console.error('❌ Error stopping periodic token refresh:', error)
      }
    },
   
    // Method to force authentication check (useful for debugging)
    forceAuthCheck() {
      console.log('🔄 Force authentication check triggered')
      this.checkAuthStatus()
    },
   
    // Method to attempt token refresh
    async attemptTokenRefresh() {
      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          console.warn('⚠️ No refresh token available')
          return false
        }
       
        // Import authService dynamically to avoid circular dependencies
        const { default: authService } = await import('./services/authService.js')
        const success = await authService.refreshAccessToken()
       
        if (success) {
          console.log('✅ Token refresh successful')
          return true
        } else {
          console.warn('❌ Token refresh failed')
          return false
        }
      } catch (error) {
        console.error('❌ Error during token refresh:', error)
        return false
      }
    },
   
    // Method to start periodic token refresh
    async startPeriodicTokenRefresh() {
      try {
        const { default: authService } = await import('./services/authService.js')
        authService.startPeriodicTokenRefresh()
        console.log('🔄 Periodic token refresh started from App.vue')
      } catch (error) {
        console.error('❌ Error starting periodic token refresh:', error)
      }
    }
  }
}
</script>
 
<style>
body {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
}
 
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
}
 
.app-container {
  display: flex;
  min-height: 100vh;
}
 
.main-content {
  flex: 1;
  background-color: #ffffff;
}
 
.main-content.with-sidebar {
  padding: 4rem 20px 20px;
  margin-left: 20px; /* Account for sidebar width */
}
 
.login-container {
  min-height: 100vh;
}
</style>
 