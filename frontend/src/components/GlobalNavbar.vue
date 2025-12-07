<template>
  <header class="main-header" :class="{ 'scrolled': isScrolled }">
    <div class="header-content">
      <div class="logo">
      </div>
      
      <nav class="main-nav">
        <router-link :to="{ name: 'home' }" class="nav-link" :class="{ active: isRouteActive('home') }">Dashboard</router-link>
        <router-link :to="{ name: 'PolicyDashboard' }" class="nav-link" :class="{ active: isRouteActive('PolicyDashboard') }">Policies</router-link>
        <router-link :to="{ name: 'ComplianceDashboard' }" class="nav-link" :class="{ active: isRouteActive('ComplianceDashboard') }">Compliance</router-link>
        <router-link :to="{ name: 'RiskDashboard' }" class="nav-link" :class="{ active: isRouteActive('RiskDashboard') }">Risk</router-link>
        <router-link :to="{ name: 'AuditorUserDashboard' }" class="nav-link" :class="{ active: isRouteActive('AuditorUserDashboard') }">Audits</router-link>
        <router-link :to="{ name: 'IncidentPerformanceDashboard' }" class="nav-link" :class="{ active: isRouteActive('IncidentPerformanceDashboard') }">Incidents</router-link>
      </nav>
      
      <div class="header-actions">
        
        <!-- Notification Bell -->
        <div class="notification-bell" @click="navigateToNotifications">
          <i class="fas fa-bell"></i>
          <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount }}</span>
        </div>
        
        <button @click="logout" class="logout-btn">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>
          </svg>
          Logout
        </button>
      </div>
    </div>
  </header>
</template>

<script>
import logo from '../assets/RiskaVaire.png'
import axios from 'axios'
import { API_ENDPOINTS } from '../config/api.js'

export default {
  name: 'GlobalNavbar',
  data() {
    return {
      isScrolled: false,
      userName: '',
      userInitials: '',
      logo,
      unreadCount: 0,
      pollInterval: null
    }
  },
  mounted() {
    this.setupScrollListener()
    this.loadUserData()
    this.startNotificationPolling()
  },
  beforeUnmount() {
    window.removeEventListener('scroll', this.handleScroll)
    if (this.pollInterval) {
      clearInterval(this.pollInterval)
    }
  },
  methods: {
    setupScrollListener() {
      window.addEventListener('scroll', this.handleScroll)
    },
    handleScroll() {
      this.isScrolled = window.scrollY > 10
    },
    loadUserData() {
      const userName = localStorage.getItem('user_name') || 'User'
      this.userName = userName
      this.userInitials = userName.split(' ').map(name => name.charAt(0)).join('').toUpperCase()
    },
    isRouteActive(routeName) {
      return this.$route.name === routeName
    },
    navigateToNotifications() {
      this.$router.push('/notifications')
    },
    async fetchUnreadCount() {
      try {
        const accessToken = localStorage.getItem('access_token')
        const userId = localStorage.getItem('user_id')
        
        if (!accessToken || !userId) {
          return
        }
        
        const response = await axios.get(API_ENDPOINTS.GET_NOTIFICATIONS(userId), {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          },
          timeout: 5000
        })
        
        if (response.data && response.data.status === 'success') {
          const count = (response.data.notifications || []).filter(n => n.status && !n.status.isRead).length
          this.unreadCount = count
        }
      } catch (error) {
        console.log('Error fetching notifications:', error.message)
      }
    },
    startNotificationPolling() {
      this.fetchUnreadCount()
      this.pollInterval = setInterval(this.fetchUnreadCount, 30000) // Poll every 30 seconds instead of 10
    },
    logout() {
      // Clear authentication data
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_id')
      localStorage.removeItem('is_logged_in')
      localStorage.removeItem('user_email')
      localStorage.removeItem('user_name')
      
      // Stop notification polling
      if (this.pollInterval) {
        clearInterval(this.pollInterval)
      }
      
      // Dispatch auth change event
      window.dispatchEvent(new CustomEvent('authChanged'))
      
      // Navigate to login
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
/* Header Styles */
.main-header {
  position: fixed;
  top: 0px;
  left: 280px; /* Reduced sidebar width */
  right: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 0.5px solid rgb(234, 223, 223); /* Remove bottom border */
  transition: all 0.3s ease;
  padding: 1rem 1rem;
}

.main-header.scrolled {
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 4px 32px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 2rem;
  max-width: 1400px;
  margin-top: 0 auto;
  margin-left:-120px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 0;
  overflow: visible;
  background: transparent;
  border: none;
  box-shadow: none;
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 0;
  background: transparent;
  border: none;
  box-shadow: none;
}

.logo-text {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
}

.main-nav {
  display: flex;
  align-items: center;
  padding-top: -20px;
  gap: 2rem;
}

.nav-link {
  text-decoration: none;
  color: #6b7280;
  font-weight: 500;
  font-size: 0.95rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  transition: all 0.2s ease;
  position: relative;
}

.nav-link:hover {
  color: #1e40af;
  background: rgba(30, 64, 175, 0.05);
}

.nav-link.active {
  color: #1e40af;
  background: rgba(30, 64, 175, 0.1);
}

.header-actions {
  display: flex;
  align-items: center;
  margin-right: -50px;
  gap: 1rem;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.02);
}

.user-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #1e40af, #3b82f6);
  border-radius: 50%;
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
}

.user-name {
  font-weight: 500;
  color: #374151;
  font-size: 0.875rem;
}

/* Notification Bell Styles */
.notification-bell {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #6b7280;
}

.notification-bell:hover {
  background: rgba(30, 64, 175, 0.05);
  color: #1e40af;
  transform: translateY(-1px);
}

.notification-bell i {
  font-size: 1.1rem;
}

.notification-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  background: #dc2626;
  color: white;
  border-radius: 100%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 600;
  border: 2px solid white;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.logout-btn svg {
  position: relative;
  top: -1px; /* nudge icon upward */
}

.logout-btn:hover {
  background: #b91c1c;
  transform: translateY(-1px);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .main-header {
    left: 0;
  }
  
  .header-content {
    padding: 1rem;
  }
  
  .main-nav {
    gap: 1rem;
  }
  
  .nav-link {
    padding: 0.5rem;
    font-size: 0.875rem;
  }
  
  .logo-text {
    display: none;
  }
  
  .notification-bell {
    width: 36px;
    height: 36px;
  }
  
  .notification-badge {
    width: 16px;
    height: 16px;
    font-size: 0.65rem;
  }
}
</style>
