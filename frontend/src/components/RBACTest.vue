<template>
  <div class="rbac-test-container">
    <div class="rbac-test-card">
      <h1>RBAC Permission Test</h1>
      
      <div class="user-info">
        <h3>User Information</h3>
        <p><strong>User ID:</strong> {{ userInfo.userId || 'Not available' }}</p>
        <p><strong>Role:</strong> {{ userInfo.role || 'Not available' }}</p>
        <p><strong>Permissions:</strong></p>
        <pre>{{ JSON.stringify(userInfo.permissions, null, 2) }}</pre>
      </div>
      
      <div class="test-section">
        <h3>Test Endpoints</h3>
        
        <div class="test-buttons">
          <button 
            @click="testEndpoint('public')" 
            class="btn btn-success"
            :disabled="loading"
          >
            Test Public Endpoint
          </button>
          
          <button 
            @click="testEndpoint('policy-view')" 
            class="btn btn-primary"
            :disabled="loading"
          >
            Test Policy View Permission
          </button>
          
          <button 
            @click="testEndpoint('policy-create')" 
            class="btn btn-warning"
            :disabled="loading"
          >
            Test Policy Create Permission
          </button>
          
          <button 
            @click="testEndpoint('policy-edit')" 
            class="btn btn-info"
            :disabled="loading"
          >
            Test Policy Edit Permission
          </button>
          
          <button 
            @click="testEndpoint('audit-view')" 
            class="btn btn-secondary"
            :disabled="loading"
          >
            Test Audit View Permission
          </button>
          
          <button 
            @click="testEndpoint('audit-conduct')" 
            class="btn btn-dark"
            :disabled="loading"
          >
            Test Audit Conduct Permission
          </button>
          
          <button 
            @click="testEndpoint('audit-review')" 
            class="btn btn-danger"
            :disabled="loading"
          >
            Test Audit Review Permission
          </button>
        </div>
        
        <div v-if="loading" class="loading">
          <p>Testing endpoint...</p>
        </div>
        
        <div v-if="testResult" class="test-result">
          <h4>Test Result:</h4>
          <div :class="['result-box', testResult.success ? 'success' : 'error']">
            <p><strong>Status:</strong> {{ testResult.success ? 'SUCCESS' : 'FAILED' }}</p>
            <p><strong>Message:</strong> {{ testResult.message }}</p>
            <p v-if="testResult.data"><strong>Response:</strong></p>
            <pre v-if="testResult.data">{{ JSON.stringify(testResult.data, null, 2) }}</pre>
          </div>
        </div>
      </div>
      
      <div class="actions">
        <button @click="goHome" class="btn btn-outline">
          <i class="fas fa-home"></i>
          Go Home
        </button>
        
        <button @click="refreshPermissions" class="btn btn-outline">
          <i class="fas fa-sync"></i>
          Refresh Permissions
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import rbacService from '@/services/rbacService.js'
import { API_BASE_URL } from '@/config/api.js'

export default {
  name: 'RBACTest',
  data() {
    return {
      userInfo: {
        userId: null,
        role: null,
        permissions: {}
      },
      loading: false,
      testResult: null
    }
  },
  
  async mounted() {
    await this.loadUserInfo()
  },
  
  methods: {
    async loadUserInfo() {
      try {
        // Initialize RBAC service
        await rbacService.initialize()
        
        this.userInfo.userId = rbacService.getUserId()
        this.userInfo.role = rbacService.getUserRole()
        this.userInfo.permissions = rbacService.getUserPermissions()
        
        console.log('User info loaded:', this.userInfo)
      } catch (error) {
        console.error('Error loading user info:', error)
      }
    },
    
    async testEndpoint(endpoint) {
      this.loading = true
      this.testResult = null
      
      try {
        const token = localStorage.getItem('access_token')
        if (!token) {
          throw new Error('No access token found')
        }
        
        const config = {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
        
        let response
        const url = `${API_BASE_URL}/api/rbac/test/${endpoint}/`
        
        switch (endpoint) {
          case 'public':
            response = await axios.get(url, config)
            break
          case 'policy-view':
            response = await axios.get(url, config)
            break
          case 'policy-create':
            response = await axios.post(url, {}, config)
            break
          case 'policy-edit':
            response = await axios.put(url, {}, config)
            break
          case 'audit-view':
            response = await axios.get(url, config)
            break
          case 'audit-conduct':
            response = await axios.post(url, {}, config)
            break
          case 'audit-review':
            response = await axios.post(url, {}, config)
            break
          default:
            throw new Error(`Unknown endpoint: ${endpoint}`)
        }
        
        this.testResult = {
          success: true,
          message: 'Endpoint test successful',
          data: response.data
        }
        
        console.log(`✅ ${endpoint} test successful:`, response.data)
        
      } catch (error) {
        console.error(`❌ ${endpoint} test failed:`, error)
        
        this.testResult = {
          success: false,
          message: error.response?.data?.message || error.message,
          data: error.response?.data || null
        }
        
        // If it's a 403 error, the access denied interceptor should handle it
        if (error.response?.status === 403) {
          console.log('Access denied - should redirect to access denied page')
        }
      } finally {
        this.loading = false
      }
    },
    
    goHome() {
      this.$router.push('/home')
    },
    
    async refreshPermissions() {
      await this.loadUserInfo()
      this.testResult = null
    }
  }
}
</script>

<style scoped>
.rbac-test-container {
  min-height: 100vh;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.rbac-test-card {
  background: white;
  border-radius: 16px;
  padding: 32px;
  max-width: 800px;
  margin: 0 auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.rbac-test-card h1 {
  text-align: center;
  color: #1f2937;
  margin-bottom: 32px;
}

.user-info {
  background: #f9fafb;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 32px;
}

.user-info h3 {
  color: #1f2937;
  margin-bottom: 16px;
}

.user-info pre {
  background: #1f2937;
  color: #f9fafb;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
}

.test-section {
  margin-bottom: 32px;
}

.test-section h3 {
  color: #1f2937;
  margin-bottom: 16px;
}

.test-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.btn {
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 500;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  font-size: 14px;
  justify-content: center;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-success {
  background: #10b981;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #059669;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-warning {
  background: #f59e0b;
  color: white;
}

.btn-warning:hover:not(:disabled) {
  background: #d97706;
}

.btn-info {
  background: #06b6d4;
  color: white;
}

.btn-info:hover:not(:disabled) {
  background: #0891b2;
}

.btn-secondary {
  background: #6b7280;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #4b5563;
}

.btn-dark {
  background: #374151;
  color: white;
}

.btn-dark:hover:not(:disabled) {
  background: #1f2937;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.btn-outline {
  background: transparent;
  color: #3b82f6;
  border: 2px solid #3b82f6;
}

.btn-outline:hover {
  background: #3b82f6;
  color: white;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #6b7280;
}

.test-result {
  margin-top: 24px;
}

.test-result h4 {
  color: #1f2937;
  margin-bottom: 12px;
}

.result-box {
  padding: 16px;
  border-radius: 8px;
  border: 2px solid;
}

.result-box.success {
  background: #f0fdf4;
  border-color: #10b981;
  color: #065f46;
}

.result-box.error {
  background: #fef2f2;
  border-color: #ef4444;
  color: #991b1b;
}

.result-box pre {
  background: rgba(0, 0, 0, 0.1);
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  margin-top: 8px;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

@media (max-width: 640px) {
  .rbac-test-card {
    padding: 20px;
  }
  
  .test-buttons {
    grid-template-columns: 1fr;
  }
  
  .actions {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
}
</style>
