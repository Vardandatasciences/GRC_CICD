<template>
  <div class="performance-page">
    <h2>Performance Dashboard</h2>
    
    <!-- RBAC Access Denied Message -->
    <div v-if="accessDenied" class="access-denied-message">
      <div class="access-denied-card">
        <i class="fas fa-shield-alt"></i>
        <h3>Access Denied</h3>
        <p>You don't have permission to view Policy KPIs and Performance Data.</p>
        <p>Required permission: <strong>policy_view</strong></p>
        <p>Contact your administrator to request access.</p>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !accessDenied" class="loading-message">
      <i class="fas fa-spinner fa-spin"></i>
      <span>Loading Performance Data...</span>
    </div>

    <!-- Error Message -->
    <div v-if="error && !accessDenied" class="error-message">
      <div class="error-card">
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Error Loading Data</h3>
        <p>{{ error }}</p>
        <button @click="loadPolicyKPIs" class="retry-button">Retry</button>
      </div>
    </div>

    <!-- Main Content - Only show if no access denied -->
    <div v-if="!accessDenied && !loading">
      <!-- Search Bar -->
      <div class="search-bar">
        <div class="search-container">
          <i class="fas fa-search search-icon"></i>
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="Search Policies..." 
          />
        </div>
      </div>

      <!-- KPI Summary Cards -->
      <div v-if="kpiData" class="kpi-summary">
        <div class="kpi-card">
          <div class="kpi-value">{{ kpiData.total_policies || 0 }}</div>
          <div class="kpi-label">Total Policies</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ kpiData.active_policies || 0 }}</div>
          <div class="kpi-label">Active Policies</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ kpiData.revision_rate || 0 }}%</div>
          <div class="kpi-label">Revision Rate</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-value">{{ kpiData.coverage_metrics?.overall_coverage_rate || 0 }}%</div>
          <div class="kpi-label">Coverage Rate</div>
        </div>
      </div>

      <!-- Policy Cards Grid -->
      <div class="policy-cards-grid">
        <div 
          v-for="(policy, index) in filteredPolicies" 
          :key="index"
          class="policy-card"
        >
          <div class="policy-card-header">
            <div class="policy-card-icon">
              {{ policy.category.charAt(0) }}
            </div>
            <div class="policy-card-title">{{ policy.name }}</div>
            <div class="policy-card-upload">
              <i class="fas fa-upload"></i>
            </div>
          </div>
          <div class="policy-card-progressbar">
            <div class="progress-bar-main">
              <div class="progress-bar-fill" :style="{ width: policy.progress }"></div>
            </div>
            <span class="policy-card-progress-label">{{ policy.progress }} Latest results</span>
          </div>
          <div class="policy-card-analytics">
            <span>Analytics</span>
            <span class="policy-card-analytics-arrow">▼</span>
          </div>
          <div class="policy-card-list">
            <div class="policy-card-list-header">
              <span>Performance</span>
            </div>
            <div 
              v-for="(item, idx) in policy.subpolicies" 
              :key="idx"
              class="policy-card-list-row"
            >
              <span class="policy-card-list-label">{{ item.name }}</span>
              <div class="policy-card-list-progress">
                <div class="progress-bar-sub">
                  <div 
                    class="progress-bar-fill-sub" 
                    :style="{ width: `${item.percent}%` }"
                  ></div>
                </div>
                <span 
                  :class="[
                    'policy-card-list-status',
                    item.status === 'Completed' ? 'completed' : 'inprogress'
                  ]"
                >
                  {{ item.status }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'  // Use regular axios with global configuration from main.js

export default {
  name: 'PerformancePage',
  setup() {
    const searchQuery = ref('')
    const loading = ref(false)
    const error = ref('')
    const accessDenied = ref(false)
    const kpiData = ref(null)

    // Sample data for policies (fallback/demo data)
    const policies = ref([
      {
        id: '1.1',
        name: 'Financial Policy',
        category: 'Financial',
        progress: '40%',
        subpolicies: [
          { name: 'Budget Management', status: 'Completed', percent: 95 },
          { name: 'Expense Tracking', status: 'Completed', percent: 88 },
          { name: 'Financial Reporting', status: 'In Progress', percent: 65 },
          { name: 'Audit Compliance', status: 'In Progress', percent: 70 },
          { name: 'Risk Assessment', status: 'In Progress', percent: 45 }
        ]
      },
      {
        id: '1.2',
        name: 'Service Policy',
        category: 'Service',
        progress: '50%',
        subpolicies: [
          { name: 'Customer Support', status: 'Completed', percent: 92 },
          { name: 'Service Delivery', status: 'In Progress', percent: 75 }
        ]
      },
      {
        id: '2.1',
        name: 'Loan Policy',
        category: 'Loan',
        progress: '80%',
        subpolicies: [
          { name: 'Loan Processing', status: 'Completed', percent: 90 },
          { name: 'Credit Assessment', status: 'Completed', percent: 85 },
          { name: 'Risk Evaluation', status: 'Completed', percent: 88 },
          { name: 'Documentation', status: 'Completed', percent: 92 },
          { name: 'Compliance Check', status: 'In Progress', percent: 60 }
        ]
      }
    ])

    // Function to load Policy KPIs with RBAC protection
    const loadPolicyKPIs = async () => {
      loading.value = true
      error.value = ''
      accessDenied.value = false

      try {
        console.log('[RBAC DEBUG] Attempting to load Policy KPIs...')
        
        // Make API call to RBAC-protected endpoint using global axios configuration
        const response = await axios.get('/policy-kpis/')

        console.log('[RBAC DEBUG] Policy KPIs loaded successfully:', response.data)
        kpiData.value = response.data

      } catch (err) {
        console.error('[RBAC DEBUG] Error loading Policy KPIs:', err)
        
        if (err.response) {
          const status = err.response.status
          console.log('[RBAC DEBUG] Response status:', status)
          console.log('[RBAC DEBUG] Response data:', err.response.data)
          
          if (status === 403) {
            // Permission denied
            accessDenied.value = true
            error.value = 'Access denied: You do not have permission to view Policy KPIs'
            console.log('[RBAC DEBUG] Access denied - user lacks policy_view permission')
          } else if (status === 401) {
            // Not authenticated
            accessDenied.value = true
            error.value = 'Authentication required: Please log in to access this page'
            console.log('[RBAC DEBUG] Authentication required')
          } else {
            error.value = `Server error (${status}): ${err.response.data?.error || 'Unknown error'}`
          }
        } else if (err.request) {
          error.value = 'Network error: Unable to connect to the server'
        } else {
          error.value = `Request error: ${err.message}`
        }
      } finally {
        loading.value = false
      }
    }

    // Filter policies based on search query
    const filteredPolicies = computed(() => {
      return policies.value.filter(policy => 
        policy.name.toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    })

    // Load data when component mounts
    onMounted(() => {
      console.log('[RBAC DEBUG] PerformancePage component mounted, loading Policy KPIs...')
      loadPolicyKPIs()
    })

    return {
      searchQuery,
      loading,
      error,
      accessDenied,
      kpiData,
      filteredPolicies,
      loadPolicyKPIs
    }
  }
}
</script>

<style scoped>
/* Styling for the main performance page */
.performance-page {
  padding: 20px;
  margin-left: 180px;
  background: #f7f9fa;
  min-height: 100vh;
}

.performance-page h2 {
  color: #2d3748;
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
  font-weight: 600;
}

/* RBAC Access Denied Styles */
.access-denied-message {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.access-denied-card {
  background: #fee2e2;
  border: 2px solid #f87171;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  max-width: 500px;
  box-shadow: 0 4px 12px rgba(248, 113, 113, 0.15);
}

.access-denied-card i {
  font-size: 3rem;
  color: #dc2626;
  margin-bottom: 20px;
}

.access-denied-card h3 {
  color: #dc2626;
  font-size: 1.5rem;
  margin-bottom: 15px;
  font-weight: 600;
}

.access-denied-card p {
  color: #991b1b;
  margin-bottom: 10px;
  line-height: 1.5;
}

/* Loading and Error Styles */
.loading-message {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
  font-size: 1.1rem;
  color: #4a5568;
}

.loading-message i {
  margin-right: 10px;
  font-size: 1.2rem;
}

.error-message {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.error-card {
  background: #fef2f2;
  border: 2px solid #fca5a5;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
  max-width: 500px;
}

.error-card i {
  font-size: 2.5rem;
  color: #dc2626;
  margin-bottom: 15px;
}

.error-card h3 {
  color: #dc2626;
  margin-bottom: 10px;
}

.retry-button {
  background: #dc2626;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 15px;
  font-weight: 500;
}

.retry-button:hover {
  background: #b91c1c;
}

/* KPI Summary Cards */
.kpi-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.kpi-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 2px solid #e2e8f0;
}

.kpi-value {
  font-size: 2.5rem;
  font-weight: bold;
  color: #2d3748;
  margin-bottom: 8px;
}

.kpi-label {
  font-size: 0.9rem;
  color: #718096;
  font-weight: 500;
}

.search-bar {
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-start;
}

.search-container {
  display: flex;
  align-items: center;
  border: 1px solid #e2e8f0;
  padding: 8px 12px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.search-container:focus-within {
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.search-container input {
  border: none;
  outline: none;
  padding: 4px 8px;
  font-size: 14px;
  width: 250px;
  color: #4a5568;
}

.search-icon {
  color: #a0aec0;
  margin-right: 8px;
}

/* Policy Cards Grid */
.policy-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  padding: 10px;
}

/* Policy Card Styles */
.policy-card {
  background: #f5f6fa;
  border-radius: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 260px;
  max-width: 420px;
  font-size: 0.97rem;
  border: 3px solid #a084e8;
}

.policy-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.policy-card-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f5f6fa;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: #7c3aed;
  border: 2px solid #a084e8;
}

.policy-card-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #7c3aed;
  flex: 1;
}

.policy-card-upload {
  background: #4f6cff;
  color: #fff;
  border-radius: 50%;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.12);
}

.policy-card-progressbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.progress-bar-main {
  background: #e5e7eb;
  width: 90px;
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  margin-right: 4px;
}

.progress-bar-fill {
  background: linear-gradient(90deg, #b6f7b0, #4f6cff);
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s;
}

.policy-card-progress-label {
  font-size: 0.95rem;
  color: #222;
  font-weight: 500;
}

.policy-card-analytics {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.95rem;
  color: #222;
  font-weight: 500;
  margin-bottom: 4px;
  cursor: pointer;
}

.policy-card-analytics-arrow {
  font-size: 1rem;
  margin-left: 2px;
}

.policy-card-list {
  background: #f5f6fa;
  border-radius: 8px;
  padding: 8px 6px 6px 6px;
  margin-top: 4px;
  font-size: 0.95rem;
}

.policy-card-list-header {
  font-size: 1rem;
  font-weight: 600;
  color: #222;
  margin-bottom: 4px;
}

.policy-card-list-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.policy-card-list-label {
  font-size: 0.95rem;
  color: #222;
  font-weight: 500;
  flex: 1;
}

.policy-card-list-progress {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 80px;
}

.progress-bar-sub {
  background: #e5e7eb;
  width: 40px;
  height: 6px;
  border-radius: 3px;
  overflow: hidden;
  margin-right: 2px;
}

.progress-bar-fill-sub {
  background: linear-gradient(90deg, #b6f7b0, #4f6cff);
  height: 100%;
  border-radius: 3px;
  transition: width 0.4s;
}

.policy-card-list-status {
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: 6px;
  padding: 1px 6px;
  margin-left: 2px;
}

.policy-card-list-status.completed {
  background: #b6f7b0;
  color: #222;
}

.policy-card-list-status.inprogress {
  background: #ffb3b3;
  color: #b91c1c;
}
</style> 