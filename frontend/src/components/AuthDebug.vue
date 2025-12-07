<template>
    <div class="auth-debug" v-if="showDebug">
      <div class="debug-panel">
        <h4>🔐 Authentication Debug Panel</h4>
        <div class="debug-info">
          <p><strong>Is Authenticated:</strong> {{ isAuthenticated }}</p>
          <p><strong>Has Token:</strong> {{ hasToken }}</p>
          <p><strong>Has User ID:</strong> {{ hasUserId }}</p>
          <p><strong>Is Logged In:</strong> {{ isLoggedIn }}</p>
          <p><strong>Token Valid:</strong> {{ isTokenValid }}</p>
          <p><strong>Token Expired:</strong> {{ tokenExpired }}</p>
          <p><strong>Token Expires At:</strong> {{ tokenExpiresAt }}</p>
          <p><strong>Has Explicitly Logged In:</strong> {{ hasExplicitlyLoggedIn }}</p>
          <p><strong>Sidebar Will Render:</strong> {{ sidebarWillRender }}</p>
          <p><strong>Periodic Refresh:</strong> {{ periodicRefreshStatus }}</p>
        </div>
        <div class="debug-actions">
          <button @click="forceAuthCheck" class="debug-btn">Force Auth Check</button>
          <button @click="refreshToken" class="debug-btn" :disabled="!hasToken">Refresh Token</button>
          <button @click="togglePeriodicRefresh" class="debug-btn">{{ periodicRefreshButtonText }}</button>
          <button @click="toggleDebug" class="debug-btn">Hide Debug</button>
        </div>
      </div>
    </div>
    <div v-else class="debug-toggle">
      <button @click="toggleDebug" class="debug-btn-small">🔐 Debug</button>
    </div>
  </template>
   
  <script>
  export default {
    name: 'AuthDebug',
    data() {
      return {
        showDebug: false,
        isAuthenticated: false,
        hasToken: false,
        hasUserId: false,
        isLoggedIn: false,
        isTokenValid: false,
        tokenExpired: false,
        tokenExpiresAt: 'N/A',
        hasExplicitlyLoggedIn: false,
        sidebarWillRender: false,
        periodicRefreshStatus: 'Unknown',
        periodicRefreshButtonText: 'Start Periodic Refresh'
      }
    },
    mounted() {
      this.updateDebugInfo()
      // Update debug info every 2 seconds
      this.debugInterval = setInterval(this.updateDebugInfo, 2000)
    },
    beforeUnmount() {
      if (this.debugInterval) {
        clearInterval(this.debugInterval)
      }
    },
    methods: {
      toggleDebug() {
        this.showDebug = !this.showDebug
        if (this.showDebug) {
          this.updateDebugInfo()
        }
      },
      updateDebugInfo() {
        const accessToken = localStorage.getItem('access_token')
        const userId = localStorage.getItem('user_id')
        const isLoggedIn = localStorage.getItem('is_logged_in') === 'true'
       
        let isTokenValid = true
        let tokenExpired = false
        let tokenExpiresAt = 'N/A'
       
        if (accessToken) {
          try {
            const tokenPayload = JSON.parse(atob(accessToken.split('.')[1]))
            const currentTime = Math.floor(Date.now() / 1000)
            isTokenValid = tokenPayload.exp && tokenPayload.exp > currentTime
            tokenExpired = !isTokenValid
           
            if (tokenPayload.exp) {
              const expirationDate = new Date(tokenPayload.exp * 1000)
              tokenExpiresAt = expirationDate.toLocaleString()
            }
          } catch (error) {
            isTokenValid = false
            tokenExpired = true
          }
        }
       
        this.hasToken = !!accessToken
        this.hasUserId = !!userId
        this.isLoggedIn = isLoggedIn
        this.isTokenValid = isTokenValid
        this.tokenExpired = tokenExpired
        this.tokenExpiresAt = tokenExpiresAt
       
        // Match the same logic as App.vue
        const hasAuthData = !!(accessToken && userId && isLoggedIn)
        this.isAuthenticated = hasAuthData && (isTokenValid || tokenExpired)
        this.sidebarWillRender = this.isAuthenticated
       
        // Try to get hasExplicitlyLoggedIn from the app component
        if (window.appComponent) {
          this.hasExplicitlyLoggedIn = window.appComponent.hasExplicitlyLoggedIn
        }
       
        // Check periodic refresh status
        this.checkPeriodicRefreshStatus()
       
        // Update button text based on status
        this.updatePeriodicRefreshButtonText()
      },
      forceAuthCheck() {
        if (window.forceAuthCheck) {
          window.forceAuthCheck()
        }
        this.updateDebugInfo()
      },
      async refreshToken() {
        try {
          console.log('🔄 Manual token refresh triggered')
          if (window.appComponent && window.appComponent.attemptTokenRefresh) {
            const success = await window.appComponent.attemptTokenRefresh()
            if (success) {
              console.log('✅ Manual token refresh successful')
              alert('Token refreshed successfully!')
            } else {
              console.log('❌ Manual token refresh failed')
              alert('Token refresh failed. Please log in again.')
            }
          }
          this.updateDebugInfo()
        } catch (error) {
          console.error('❌ Error during manual token refresh:', error)
          alert('Error refreshing token. Please log in again.')
        }
      },
      async checkPeriodicRefreshStatus() {
        try {
          // Check if authService has periodic refresh running
          const { default: authService } = await import('../services/authService.js')
          if (authService && authService.refreshInterval) {
            this.periodicRefreshStatus = 'Running (Every 2 min)'
          } else if (authService && authService.isAuthenticated()) {
            this.periodicRefreshStatus = 'Stopped (Should be running)'
          } else {
            this.periodicRefreshStatus = 'Stopped (Not authenticated)'
          }
        } catch (error) {
          this.periodicRefreshStatus = 'Unknown'
        }
      },
      async togglePeriodicRefresh() {
        try {
          const { default: authService } = await import('../services/authService.js')
          if (authService.refreshInterval) {
            // Stop periodic refresh
            authService.stopPeriodicTokenRefresh()
            this.periodicRefreshButtonText = 'Start Periodic Refresh'
            alert('Periodic token refresh stopped')
          } else {
            // Start periodic refresh
            authService.startPeriodicTokenRefresh()
            this.periodicRefreshButtonText = 'Stop Periodic Refresh'
            alert('Periodic token refresh started')
          }
          this.updateDebugInfo()
        } catch (error) {
          console.error('❌ Error toggling periodic refresh:', error)
          alert('Error toggling periodic refresh')
        }
      },
      updatePeriodicRefreshButtonText() {
        if (this.periodicRefreshStatus.includes('Running')) {
          this.periodicRefreshButtonText = 'Stop Periodic Refresh'
        } else {
          this.periodicRefreshButtonText = 'Start Periodic Refresh'
        }
      }
    }
  }
  </script>
   
  <style scoped>
  .auth-debug {
    position: fixed;
    top: 10px;
    right: 10px;
    z-index: 10000;
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 15px;
    border-radius: 8px;
    font-family: monospace;
    font-size: 12px;
    max-width: 300px;
  }
   
  .debug-panel h4 {
    margin: 0 0 10px 0;
    color: #00ff00;
  }
   
  .debug-info p {
    margin: 5px 0;
    font-size: 11px;
  }
   
  .debug-actions {
    margin-top: 10px;
    display: flex;
    gap: 5px;
  }
   
  .debug-btn {
    background: #007bff;
    color: white;
    border: none;
    padding: 5px 10px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 10px;
  }
   
  .debug-btn:hover {
    background: #0056b3;
  }
   
  .debug-btn:disabled {
    background: #6c757d;
    cursor: not-allowed;
  }
   
  .debug-btn:disabled:hover {
    background: #6c757d;
  }
   
  .debug-toggle {
    position: fixed;
    top: 10px;
    right: 10px;
    z-index: 10000;
  }
   
  .debug-btn-small {
    background: rgba(0, 0, 0, 0.7);
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
  }
   
  .debug-btn-small:hover {
    background: rgba(0, 0, 0, 0.9);
  }
  </style>
   