<template>
  <div class="FM_framework-migration-container">
    <!-- Header -->
    <div class="FM_framework-migration-header">
      <h1 class="FM_framework-migration-title">Migration Gap Analysis</h1>
      <p class="FM_framework-migration-subtitle">
        Streamline your compliance migration process with comprehensive gap analysis and step-by-step migration tools
      </p>
    </div>

    <!-- Framework Selection -->
    <div v-if="!selectedFrameworkId && !noFrameworksAvailable" class="FM_framework-selection-card">
      <h3 class="FM_section-title">Select Framework for Migration Analysis</h3>
      <select v-model="selectedFrameworkId" @change="onFrameworkChange" class="FM_framework-select">
        <option value="">Select a framework...</option>
        <option v-for="framework in frameworkOptions" :key="framework.FrameworkId" :value="framework.FrameworkId">
          {{ framework.FrameworkName }} ({{ framework.amendment_count }} amendments)
        </option>
      </select>
    </div>

    <div v-if="noFrameworksAvailable && !loading" class="FM_info-state">
      <i class="fas fa-info-circle"></i>
      <p>No frameworks with amendments were found. Please generate amendments first to use migration gap analysis.</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="FM_loading-state">
      <i class="fas fa-spinner fa-spin"></i>
      <p>Loading migration data...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="FM_error-state">
      <i class="fas fa-exclamation-circle"></i>
      <p>{{ error }}</p>
      <button @click="retryLoad" class="FM_retry-button">Retry</button>
    </div>

    <!-- Main Content (when framework is selected and loaded) -->
    <div v-if="selectedFrameworkId && !loading && !error && migrationData">
      <!-- Action Cards -->
      <div class="FM_action-cards-grid">
        <div class="FM_action-card" @click="navigateTo('/framework-migration/comparison')">
          <div class="FM_action-card-icon">
            <i class="fas fa-exchange-alt"></i>
          </div>
          <div class="FM_action-card-content">
            <h3 class="FM_action-card-title">Compare Frameworks</h3>
            <p class="FM_action-card-description">
              Side-by-side framework comparison with detailed change analysis and visual indicators
            </p>
            <button class="FM_action-card-button">
              Compare Frameworks
            </button>
          </div>
        </div>

        <div class="FM_action-card" @click="navigateTo('/framework-migration/migration')">
          <div class="FM_action-card-icon">
            <i class="fas fa-route"></i>
          </div>
          <div class="FM_action-card-content">
            <h3 class="FM_action-card-title">Start Migration</h3>
            <p class="FM_action-card-description">
              Step-by-step migration process with gap analysis and action planning
            </p>
            <button class="FM_action-card-button">
              Start Migration Process
            </button>
          </div>
        </div>

        <div class="FM_action-card">
          <div class="FM_action-card-icon">
            <i class="fas fa-chart-bar"></i>
          </div>
          <div class="FM_action-card-content">
            <h3 class="FM_action-card-title">View Reports</h3>
            <p class="FM_action-card-description">
              Analytics and insights into your compliance journey and migration progress
            </p>
            <button class="FM_action-card-button FM_action-card-button-outline">
              View Reports
            </button>
          </div>
        </div>
      </div>

      <!-- Migration Overview -->
      <div class="FM_migration-overview-card">
        <div class="FM_migration-overview-header">
          <h3 class="FM_migration-overview-title">
            <span class="FM_migration-status-badge">{{ migrationData.migration_status }}</span>
            {{ migrationData.framework.name }} Migration Progress
          </h3>
          <button @click="selectedFrameworkId = null" class="FM_change-framework-button">
            <i class="fas fa-sync-alt"></i>
            Change Framework
          </button>
        </div>
        <div class="FM_migration-overview-content">
          <div class="FM_progress-section">
            <div class="FM_progress-info">
              <span class="FM_progress-label">Migration Progress</span>
              <span class="FM_progress-percentage">{{ migrationData.progress_percentage }}% Complete</span>
            </div>
            <div class="FM_progress-bar">
              <div class="FM_progress-fill" :style="{ width: migrationData.progress_percentage + '%' }"></div>
            </div>
          </div>
          
          <div class="FM_migration-stats-grid">
            <div class="FM_migration-stat-card FM_migration-stat-new">
              <p class="FM_migration-stat-number">{{ migrationData.statistics.new_controls }}</p>
              <p class="FM_migration-stat-label">New Controls to Implement</p>
            </div>
            <div class="FM_migration-stat-card FM_migration-stat-modified">
              <p class="FM_migration-stat-number">{{ migrationData.statistics.modified_controls }}</p>
              <p class="FM_migration-stat-label">Modified Controls to Review</p>
            </div>
            <div class="FM_migration-stat-card FM_migration-stat-removed">
              <p class="FM_migration-stat-number">{{ migrationData.statistics.removed_controls }}</p>
              <p class="FM_migration-stat-label">Controls Removed</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Activity Feed -->
      <div class="FM_activity-feed-card">
        <div class="FM_activity-feed-header">
          <h3 class="FM_activity-feed-title">Recent Activity</h3>
        </div>
        <div class="FM_activity-feed-content">
          <div v-if="migrationData.recent_activities && migrationData.recent_activities.length > 0" class="FM_activity-list">
            <div 
              v-for="activity in migrationData.recent_activities" 
              :key="activity.id" 
              class="FM_activity-item"
            >
              <div :class="`FM_activity-icon ${getStatusClass(activity.status)}`">
                <i :class="getStatusIcon(activity.status)"></i>
              </div>
              <div class="FM_activity-content">
                <p class="FM_activity-action">{{ activity.action }}</p>
                <p class="FM_activity-time">{{ activity.time }}</p>
              </div>
            </div>
          </div>
          <div v-else class="FM_empty-state">
            <p>No recent activities found</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import frameworkComparisonService from '@/services/frameworkComparisonService'

export default {
  name: 'FrameworkMigration',
  data() {
    return {
      // Framework selection
      frameworkOptions: [],
      selectedFrameworkId: null,
      noFrameworksAvailable: false,
      
      // Data
      migrationData: null,
      
      // UI State
      loading: false,
      error: null
    }
  },
  
  async mounted() {
    await this.loadFrameworks()
  },
  
  methods: {
    async loadFrameworks() {
      try {
        this.loading = true
        this.error = null
        this.noFrameworksAvailable = false
        
        const response = await frameworkComparisonService.getFrameworksWithAmendments()
        
        if (response.success) {
          const frameworks = Array.isArray(response.data) ? response.data : []
          const frameworksWithAmendments = frameworks.filter(
            (framework) => Number(framework.amendment_count || 0) > 0
          )

          this.frameworkOptions = frameworksWithAmendments

          if (this.frameworkOptions.length === 0) {
            this.noFrameworksAvailable = true
            this.migrationData = null
            this.selectedFrameworkId = null
            return
          }

          // Auto-select (or re-align selection) to a framework that still has amendments
          const currentSelectionStillValid = this.frameworkOptions.some(
            (framework) => framework.FrameworkId === this.selectedFrameworkId
          )

          if (!currentSelectionStillValid) {
            this.selectedFrameworkId = this.frameworkOptions[0].FrameworkId
          }

          await this.loadMigrationData()
        } else {
          this.error = response.error || 'Failed to load frameworks'
        }
      } catch (error) {
        this.error = 'Error loading frameworks: ' + error.message
        console.error('Error loading frameworks:', error)
      } finally {
        this.loading = false
      }
    },
    
    async onFrameworkChange() {
      if (this.selectedFrameworkId) {
        await this.loadMigrationData()
      } else {
        this.migrationData = null
      }
    },
    
    async loadMigrationData() {
      try {
        this.loading = true
        this.error = null
        
        const response = await frameworkComparisonService.getMigrationOverview(this.selectedFrameworkId)
        
        if (response.success) {
          this.migrationData = response
        } else {
          this.error = response.error || 'Failed to load migration data'
        }
      } catch (error) {
        this.error = 'Error loading migration data: ' + error.message
        console.error('Error loading migration data:', error)
      } finally {
        this.loading = false
      }
    },
    
    async retryLoad() {
      if (this.selectedFrameworkId) {
        await this.loadMigrationData()
      } else {
        await this.loadFrameworks()
      }
    },
    
    navigateTo(path) {
      this.$router.push(path)
    },
    
    getStatusClass(status) {
      const statusClasses = {
        completed: "FM_activity-icon-completed",
        warning: "FM_activity-icon-warning",
        info: "FM_activity-icon-info"
      }
      return statusClasses[status] || "FM_activity-icon-info"
    },
    
    getStatusIcon(status) {
      const statusIcons = {
        completed: "fas fa-check-circle",
        warning: "fas fa-exclamation-triangle",
        info: "fas fa-clock"
      }
      return statusIcons[status] || "fas fa-clock"
    }
  }
}
</script>

<style scoped>
.FM_framework-migration-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  margin-left: 280px;
}

.FM_framework-migration-header {
  margin-bottom: 32px;
}

.FM_framework-migration-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.FM_framework-migration-subtitle {
  color: var(--text-secondary);
  font-size: 0.875rem;
  line-height: 1.5;
}

/* Framework Selection */
.FM_framework-selection-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.FM_section-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.FM_framework-select {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 14px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.FM_framework-select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Loading and Error States */
.FM_loading-state,
.FM_error-state {
  text-align: center;
  padding: 48px 24px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  margin-bottom: 24px;
}

.FM_loading-state i {
  font-size: 3rem;
  color: var(--primary-color);
  margin-bottom: 16px;
}

.FM_error-state i {
  font-size: 3rem;
  color: #ef4444;
  margin-bottom: 16px;
}

.FM_loading-state p,
.FM_error-state p {
  color: var(--text-secondary);
  font-size: 1rem;
  margin-bottom: 16px;
}

.FM_retry-button {
  padding: 10px 20px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.FM_retry-button:hover {
  background: var(--primary-hover);
}

.FM_empty-state {
  text-align: center;
  padding: 24px;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.FM_info-state {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: var(--secondary-color);
  color: var(--text-secondary);
  margin-bottom: 24px;
}

.FM_info-state i {
  color: var(--primary-color);
  font-size: 1.25rem;
}

.FM_action-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 18px;
  margin-bottom: 24px;
}

.FM_action-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 18px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.FM_action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.FM_action-card-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.FM_action-card-icon i {
  font-size: 20px;
  color: white;
}

.FM_action-card-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.FM_action-card-description {
  color: var(--text-secondary);
  font-size: 0.8125rem;
  line-height: 1.5;
  margin-bottom: 12px;
}

.FM_action-card-button {
  width: 100%;
  padding: 8px 12px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.FM_action-card-button:hover {
  background: var(--primary-hover);
}

.FM_action-card-button-outline {
  background: transparent;
  color: var(--primary-color);
  border: 2px solid var(--primary-color);
}

.FM_action-card-button-outline:hover {
  background: var(--primary-color);
  color: white;
}

.FM_migration-overview-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 18px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.FM_migration-overview-header {
  margin-bottom: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.FM_migration-overview-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.FM_change-framework-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.FM_change-framework-button:hover {
  background: var(--secondary-color);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.FM_migration-status-badge {
  background: var(--primary-color);
  color: white;
  padding: 3px 10px;
  border-radius: 16px;
  font-size: 0.6875rem;
  font-weight: 600;
}

.FM_progress-section {
  margin-bottom: 18px;
}

.FM_progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.FM_progress-label {
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
}

.FM_progress-percentage {
  color: var(--primary-color);
  font-size: 0.875rem;
  font-weight: 600;
}

.FM_progress-bar {
  width: 100%;
  height: 12px;
  background: var(--secondary-color);
  border-radius: 6px;
  overflow: hidden;
}

.FM_progress-fill {
  height: 100%;
  background: var(--primary-color);
  transition: width 0.3s ease;
}

.FM_migration-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.FM_migration-stat-card {
  text-align: center;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.FM_migration-stat-new {
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.3);
}

.FM_migration-stat-modified {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.3);
}

.FM_migration-stat-removed {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
}

.FM_migration-stat-number {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.FM_migration-stat-new .FM_migration-stat-number {
  color: #22c55e;
}

.FM_migration-stat-modified .FM_migration-stat-number {
  color: var(--primary-color);
}

.FM_migration-stat-removed .FM_migration-stat-number {
  color: #ef4444;
}

.FM_migration-stat-label {
  color: var(--text-secondary);
  font-size: 0.8125rem;
  font-weight: 500;
}

.FM_activity-feed-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.FM_activity-feed-header {
  margin-bottom: 12px;
}

.FM_activity-feed-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
}

.FM_activity-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.FM_activity-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: var(--secondary-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  transition: border-color 0.2s ease;
}

.FM_activity-item:hover {
  border-color: var(--primary-color);
}

.FM_activity-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.FM_activity-icon-completed {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.FM_activity-icon-warning {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.FM_activity-icon-info {
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary-color);
}

.FM_activity-content {
  flex: 1;
  min-width: 0;
}

.FM_activity-action {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.FM_activity-time {
  color: var(--text-secondary);
  font-size: 0.8125rem;
  font-weight: 500;
}

@media (max-width: 768px) {
  .FM_framework-migration-container {
    padding: 16px;
  }
  
  .FM_action-cards-grid {
    grid-template-columns: 1fr;
  }
  
  .FM_migration-stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
