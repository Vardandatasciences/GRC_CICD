<template>
  <div class="sentinel-container">

    <!-- Integrations Grid -->
    <div class="sentinel-integrations-grid">
      <!-- Microsoft Sentinel Integration Card -->
      <div class="sentinel-integration-card">
        <div class="sentinel-card-header">
          <div class="sentinel-service-icon">
            <i class="fas fa-shield-alt"></i>
          </div>
          <div class="sentinel-service-info">
            <h3>Microsoft Sentinel</h3>
            <p>Cloud-native SIEM and SOAR platform</p>
          </div>
        </div>
        
        <div class="sentinel-card-body">
          <div class="sentinel-features">
            <span class="sentinel-feature-tag">SIEM</span>
            <span class="sentinel-feature-tag">SOAR</span>
            <span class="sentinel-feature-tag">Threat Detection</span>
          </div>
          
          <div class="sentinel-connection-status">
            <div v-if="isSentinelConnected" class="sentinel-status connected">
              <i class="fas fa-check-circle"></i>
              <span>Connected</span>
            </div>
            <div v-else class="sentinel-status disconnected">
              <i class="fas fa-times-circle"></i>
              <span>Not Connected</span>
            </div>
            
            <div v-if="isSentinelConnected && userInfo" class="sentinel-user-info">
              <i class="fas fa-user"></i>
              <span>{{ userInfo.displayName || userInfo.userPrincipalName }}</span>
            </div>
          </div>
        </div>
        
        <div class="sentinel-card-footer">
          <button 
            v-if="isSentinelConnected" 
            @click="disconnectSentinel"
            class="sentinel-btn sentinel-btn-secondary"
          >
            <i class="fas fa-unlink"></i>
            Disconnect
          </button>
          <button 
            v-else 
            @click="connectSentinel"
            class="sentinel-btn sentinel-btn-primary"
          >
            <i class="fas fa-sign-in-alt"></i>
            Connect with Microsoft
          </button>
        </div>
      </div>
    </div>

    <!-- Success/Error Messages -->
    <div v-if="alertMessage.show" :class="['sentinel-alert', alertMessage.type]">
      <i :class="alertMessage.icon"></i>
      {{ alertMessage.text }}
    </div>

    <!-- Microsoft Sentinel Incidents Section -->
    <div v-if="isSentinelConnected" class="sentinel-incidents-section">
      <div class="sentinel-section-header">
        <div>
          <h2><i class="fas fa-exclamation-triangle"></i> Microsoft Defender Incidents</h2>
        </div>
      </div>

      <!-- Incident Statistics -->
      <div class="sentinel-stats-grid">
        <div class="sentinel-stat-card">
          <div class="sentinel-stat-number">{{ stats.total }}</div>
          <div class="sentinel-stat-label">Total Incidents</div>
        </div>
        <div class="sentinel-stat-card sentinel-stat-critical">
          <div class="sentinel-stat-number">{{ stats.critical }}</div>
          <div class="sentinel-stat-label">Critical</div>
        </div>
        <div class="sentinel-stat-card sentinel-stat-high">
          <div class="sentinel-stat-number">{{ stats.high }}</div>
          <div class="sentinel-stat-label">High</div>
        </div>
        <div class="sentinel-stat-card sentinel-stat-medium">
          <div class="sentinel-stat-number">{{ stats.medium }}</div>
          <div class="sentinel-stat-label">Medium</div>
        </div>
        <div class="sentinel-stat-card sentinel-stat-low">
          <div class="sentinel-stat-number">{{ stats.low }}</div>
          <div class="sentinel-stat-label">Low</div>
        </div>
      </div>

      <!-- Incident Filters -->
      <div class="sentinel-filters">
        <select v-model="filters.timeRange" class="sentinel-filter-select" @change="onTimeRangeChange">
          <option value="1">Last 1 Day</option>
          <option value="7">Last 1 Week</option>
          <option value="30">Last 30 Days</option>
          <option value="90">Last 90 Days</option>
        </select>
        <select v-model="filters.severity" class="sentinel-filter-select">
          <option value="">All Severities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
          <option value="Informational">Informational</option>
        </select>
        <select v-model="filters.status" class="sentinel-filter-select">
          <option value="">Active Only (New + Active)</option>
          <option value="All">All Statuses</option>
          <option value="New">New</option>
          <option value="Active">Active</option>
          <option value="Closed">Closed</option>
        </select>
        <input 
          type="text" 
          v-model="filters.search" 
          placeholder="Search incidents..."
          class="sentinel-filter-input"
        >
      </div>

      <!-- Incidents Loading Indicator -->
      <div v-if="loading" class="sentinel-loading">
        <i class="fas fa-spinner fa-spin"></i>
        Loading incidents from Microsoft Defender...
      </div>

      <!-- Incidents List -->
      <div v-else-if="filteredIncidents.length > 0" class="sentinel-incidents-container">
        <table class="sentinel-incidents-table">
          <thead>
            <tr>
              <th>INCIDENT ID</th>
              <th>TITLE</th>
              <th>SEVERITY</th>
              <th>STATUS</th>
              <th>CREATED TIME</th>
              <th>ACTIVE ALERTS</th>
              <th>ACTIONS</th>
              <th style="text-align: center;">SAVE</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="incident in filteredIncidents" 
              :key="incident.id"
              class="sentinel-incident-row"
            >
              <td @click="viewIncidentDetails(incident)">{{ incident.incidentNumber || incident.id }}</td>
              <td @click="viewIncidentDetails(incident)">
                {{ incident.title || incident.displayName }}
                <span 
                  v-if="incident.isPlaybookTriggered" 
                  class="sentinel-playbook-badge"
                >
                  Playbook
                </span>
              </td>
              <td @click="viewIncidentDetails(incident)">
                <span :class="['sentinel-severity-badge', `sentinel-severity-${(incident.severity || '').toLowerCase()}`]">
                  {{ incident.severity }}
                </span>
              </td>
              <td @click="viewIncidentDetails(incident)">
                <span :class="['sentinel-status-badge', `sentinel-status-${(incident.status || '').toLowerCase()}`]">
                  {{ incident.status }}
                </span>
              </td>
              <td @click="viewIncidentDetails(incident)">{{ formatDate(incident.createdDateTime || incident.createdTime) }}</td>
              <td @click="viewIncidentDetails(incident)">
                <span class="sentinel-alert-count" :class="{ 'sentinel-high-count': (incident.alertsCount || 0) > 5 }">
                  {{ incident.activeAlertsRatio || incident.alertsCount || 0 }}
                </span>
              </td>
              <td>
                <button class="sentinel-btn sentinel-btn-sm sentinel-btn-outline" @click.stop="viewIncidentDetails(incident)">
                  <i class="fas fa-list"></i> View Alerts
                </button>
              </td>
              <td style="text-align: center;">
                <button 
                  class="sentinel-btn sentinel-btn-sm sentinel-btn-save" 
                  @click.stop="saveIncidentToDatabase(incident)"
                  :disabled="incident.saving"
                  :title="incident.saved ? 'Already saved' : 'Save to database'"
                >
                  <i :class="['fas', incident.saving ? 'fa-spinner fa-spin' : incident.saved ? 'fa-check' : 'fa-plus']"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- No Incidents Message -->
      <div v-else class="sentinel-no-incidents">
        <i class="fas fa-shield-alt"></i>
        <h3>No incidents found</h3>
        <p>No security incidents found in Microsoft Defender.</p>
      </div>
    </div>

    <!-- Incident Details Modal -->
    <div v-if="selectedIncident" class="sentinel-modal-overlay" @click="closeModal">
      <div class="sentinel-modal-content sentinel-incident-details-modal" @click.stop>
        <div class="sentinel-modal-header">
          <h3>
            <i class="fas fa-exclamation-triangle"></i>
            Incident Details - #{{ selectedIncident.incidentNumber || selectedIncident.id }}
          </h3>
          <span class="sentinel-modal-close" @click="closeModal">&times;</span>
        </div>
        <div class="sentinel-modal-body">
          <!-- Incident Banner -->
          <div class="incident-banner">
            <div class="banner-content">
              <i class="fas fa-info-circle"></i>
              <span><strong>Source:</strong> Microsoft Defender for Endpoint</span>
            </div>
            <div v-if="selectedIncident.isPlaybookTriggered" class="banner-content">
              <span class="sentinel-source-indicator playbook">
                <i class="fas fa-robot"></i> Playbook Triggered
              </span>
            </div>
          </div>

          <!-- Two Column Layout -->
          <div class="sentinel-two-column-layout">
            <!-- Left Column: Alert Details -->
            <div class="sentinel-alert-details">

              <!-- Alerts Table -->
              <div v-if="selectedIncident.loading" class="sentinel-alerts-table-container">
                <div class="sentinel-loading">
                  <i class="fas fa-spinner fa-spin"></i>
                  Loading detailed alerts...
                </div>
              </div>
              <div v-else-if="selectedIncident.alerts && selectedIncident.alerts.length > 0" class="sentinel-alerts-table-container">
                <div class="sentinel-alerts-table-header">
                  <h4>
                    <i class="fas fa-list"></i>
                    Alert Details
                  </h4>
                  <span class="sentinel-alert-count-badge">{{ selectedIncident.alerts.length }} alert{{ selectedIncident.alerts.length !== 1 ? 's' : '' }}</span>
                </div>
                <table class="sentinel-alerts-table">
                  <thead>
                    <tr>
                      <th style="width: 40px;"></th>
                      <th>Time Generated</th>
                      <th>Actions Performed</th>
                      <th>Alert Description</th>
                      <th style="text-align: center;">Suspicious Activity Count</th>
                      <th>User</th>
                    </tr>
                  </thead>
                  <tbody>
                    <template v-for="(alert, index) in selectedIncident.alerts" :key="index">
                      <tr class="sentinel-alert-row" @click="toggleAlertExpand(alert.id)">
                        <td style="text-align: center;">
                          <button class="sentinel-expand-alert-btn" @click.stop="toggleAlertExpand(alert.id)">
                            <i :class="['fas', expandedAlerts[alert.id] ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
                          </button>
                        </td>
                        <td class="sentinel-alert-table-time">
                          <i class="fas fa-clock"></i>
                          {{ formatDate(alert.timeGenerated || alert.createdDateTime) }}
                        </td>
                        <td>
                          <div v-if="alert.actionsPerformed && alert.actionsPerformed.length > 0" class="sentinel-alert-table-actions">
                            <span v-for="(action, idx) in alert.actionsPerformed" :key="idx" class="sentinel-action-tag-blue">
                              {{ action }}
                            </span>
                          </div>
                          <span v-else class="sentinel-text-muted">-</span>
                        </td>
                        <td class="sentinel-alert-table-description">
                          {{ alert.alertDescription || alert.description || alert.title || 'No description' }}
                        </td>
                        <td style="text-align: center;">
                          <span class="sentinel-activity-count-badge" :class="{ 'sentinel-high-count': (alert.suspiciousActivityCount || 0) > 1 }">
                            {{ alert.suspiciousActivityCount || 1 }}
                          </span>
                        </td>
                        <td>
                          <div class="sentinel-alert-user-cell">
                            <i class="fas fa-user"></i>
                            <span class="sentinel-user-email-text">{{ alert.user || 'N/A' }}</span>
                          </div>
                        </td>
                      </tr>
                      <tr v-if="expandedAlerts[alert.id]" class="sentinel-expanded-alert-row">
                        <td colspan="6">
                          <div class="sentinel-expanded-alert-content">
                            <div class="sentinel-expanded-alert-grid">
                              <div class="sentinel-expanded-section">
                                <h5>Alert Details</h5>
                                <div class="sentinel-info-row">
                                  <span class="sentinel-info-label">Severity:</span>
                                  <span :class="['sentinel-severity-badge', `sentinel-severity-${(alert.severity || '').toLowerCase()}`]">
                          {{ alert.severity }}
                        </span>
                                </div>
                                <div class="sentinel-info-row">
                                  <span class="sentinel-info-label">Status:</span>
                                  <span class="sentinel-info-value">{{ alert.status }}</span>
                                </div>
                                <div class="sentinel-info-row">
                                  <span class="sentinel-info-label">Category:</span>
                                  <span class="sentinel-info-value">{{ alert.category || 'N/A' }}</span>
                                </div>
                              </div>
                              <div class="sentinel-expanded-section">
                                <h5>Full Alert Title</h5>
                                <p class="sentinel-full-title">{{ alert.title }}</p>
                              </div>
                            </div>
                          </div>
                      </td>
                    </tr>
                    </template>
                  </tbody>
                </table>
              </div>
              <div v-else class="sentinel-alerts-table-container">
                <div class="sentinel-no-alerts-message">
                  <i class="fas fa-inbox"></i>
                  <h4>No Alerts Found</h4>
                  <p>This incident doesn't have any associated alerts.</p>
                </div>
              </div>
            </div>

            <!-- Right Column: Incident Summary -->
            <div class="sentinel-incident-summary-details">
              <div class="sentinel-incident-summary">
                <h4><i class="fas fa-info-circle"></i> Incident Summary</h4>
                <div class="sentinel-summary-grid">
                  <div class="sentinel-summary-item">
                    <span class="sentinel-summary-label">Incident ID</span>
                    <span class="sentinel-summary-value">{{ selectedIncident.incidentNumber || selectedIncident.id }}</span>
                  </div>
                  <div class="sentinel-summary-item">
                    <span class="sentinel-summary-label">Severity</span>
                    <span :class="['sentinel-summary-value', 'sentinel-severity-badge', `sentinel-severity-${(selectedIncident.severity || '').toLowerCase()}`]">
                      {{ selectedIncident.severity }}
                    </span>
                  </div>
                  <div class="sentinel-summary-item">
                    <span class="sentinel-summary-label">Status</span>
                    <span :class="['sentinel-summary-value', 'sentinel-status-badge', `sentinel-status-${(selectedIncident.status || '').toLowerCase()}`]">
                      {{ selectedIncident.status }}
                    </span>
                  </div>
                  <div class="sentinel-summary-item">
                    <span class="sentinel-summary-label">Created</span>
                    <span class="sentinel-summary-value">{{ formatDate(selectedIncident.createdDateTime || selectedIncident.createdTime) }}</span>
                    </div>
                  <div class="sentinel-summary-item">
                    <span class="sentinel-summary-label">Total Alerts</span>
                    <span class="sentinel-summary-value">{{ selectedIncident.alerts?.length || selectedIncident.alertsCount || 0 }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { API_ENDPOINTS } from '../../../config/api.js';

export default {
  name: 'SentinelIntegration',
  
  data() {
    return {
      isSentinelConnected: false,
      userInfo: null,
      incidents: [],
      selectedIncident: null,
      loading: false,
      expandedAlerts: {},
      filters: {
        severity: '',
        status: '',
        search: '',
        timeRange: '30' // Default to 30 days
      },
      alertMessage: {
        show: false,
        type: '',
        text: '',
        icon: ''
      },
      axiosInstance: null
    };
  },
  
  created() {
    // Configure axios instance for session-based authentication (no JWT tokens)
    this.axiosInstance = axios.create({
      baseURL: 'http://localhost:8000',
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // Important for session-based authentication
    });
  },

  computed: {
    stats() {
      return {
        total: this.incidents.length,
        critical: this.incidents.filter(i => i.severity === 'Critical').length,
        high: this.incidents.filter(i => i.severity === 'High').length,
        medium: this.incidents.filter(i => i.severity === 'Medium').length,
        low: this.incidents.filter(i => i.severity === 'Low').length
      };
    },

    filteredIncidents() {
      // Calculate date based on selected time range
      const timeRangeDays = parseInt(this.filters.timeRange) || 30;
      const timeThreshold = new Date();
      timeThreshold.setDate(timeThreshold.getDate() - timeRangeDays);

      return this.incidents.filter(incident => {
        // Date filter - only show incidents within selected time range
        const incidentDate = new Date(incident.createdDateTime || incident.createdTime);
        if (incidentDate < timeThreshold) {
          return false;
        }

        // Severity filter
        if (this.filters.severity && incident.severity !== this.filters.severity) {
          return false;
        }

        // Status filter
        if (this.filters.status) {
          if (this.filters.status === 'All') {
            // Show all
          } else if (this.filters.status === '') {
            // Active only (New + Active)
            if (incident.status !== 'New' && incident.status !== 'Active') {
              return false;
            }
          } else if (incident.status !== this.filters.status) {
            return false;
          }
        } else {
          // Default: Active only (New + Active)
          if (incident.status !== 'New' && incident.status !== 'Active') {
            return false;
          }
        }

        // Search filter
        if (this.filters.search) {
          const searchLower = this.filters.search.toLowerCase();
          const title = (incident.title || incident.displayName || '').toLowerCase();
          const id = (incident.incidentNumber || incident.id || '').toString().toLowerCase();
          
          if (!title.includes(searchLower) && !id.includes(searchLower)) {
            return false;
          }
        }

        return true;
      });
    }
  },

  watch: {
    // Watch for filter changes to reload incidents
    'filters.timeRange'() {
      this.loadIncidents();
    }
  },

  mounted() {
    this.checkConnectionStatus();
    this.handleQueryParams();
  },

  methods: {
    async checkConnectionStatus() {
      try {
        const response = await this.axiosInstance.get(API_ENDPOINTS.SENTINEL_STATUS);
        this.isSentinelConnected = response.data.connected;
        this.userInfo = response.data.userInfo;
        
        if (this.isSentinelConnected) {
          this.loadIncidents();
        }
      } catch (error) {
        console.error('Error checking connection status:', error);
      }
    },

    async loadIncidents() {
      this.loading = true;
      try {
        // Include timeRange in the API call
        const timeRangeDays = this.filters.timeRange || '30';
        const response = await this.axiosInstance.get(`${API_ENDPOINTS.SENTINEL_INCIDENTS}?days=${timeRangeDays}`);
        console.log('[SENTINEL] Raw response:', response.data);
        const incidentsData = response.data.alerts || response.data.incidents || [];
        
        // Initialize incidents with reactive properties for Vue 3
        this.incidents = incidentsData.map(incident => ({
          ...incident,
          saving: false,
          saved: false
        }));
        
        console.log('[SENTINEL] Processed incidents:', this.incidents);
        if (this.incidents.length > 0) {
          console.log('[SENTINEL] Sample incident:', this.incidents[0]);
        }
      } catch (error) {
        console.error('Error loading incidents:', error);
        this.showAlert('alert-danger', 'Failed to load incidents', 'fas fa-exclamation-triangle');
      } finally {
        this.loading = false;
      }
    },

    onTimeRangeChange() {
      // Reload incidents when time range changes
      console.log(`[SENTINEL] Time range changed to ${this.filters.timeRange} days`);
      this.loadIncidents();
    },

    async connectSentinel() {
      try {
        console.log('[SENTINEL] Initiating connection...');
        console.log('[SENTINEL] Redirect URL:', API_ENDPOINTS.SENTINEL_CONNECT);
        
        // Direct navigation to OAuth endpoint
        const oauthUrl = API_ENDPOINTS.SENTINEL_CONNECT;
        console.log('[SENTINEL] Navigating to:', oauthUrl);
        
        window.location.href = oauthUrl;
      } catch (error) {
        console.error('[SENTINEL] Error connecting to Sentinel:', error);
        this.showAlert('alert-danger', 'Failed to initiate connection', 'fas fa-exclamation-triangle');
      }
    },

    async disconnectSentinel() {
      try {
        await this.axiosInstance.get(API_ENDPOINTS.SENTINEL_DISCONNECT);
        this.isSentinelConnected = false;
        this.userInfo = null;
        this.incidents = [];
        this.showAlert('alert-info', 'Disconnected from Microsoft Sentinel', 'fas fa-info-circle');
      } catch (error) {
        console.error('Error disconnecting from Sentinel:', error);
        this.showAlert('alert-danger', 'Failed to disconnect', 'fas fa-exclamation-triangle');
      }
    },

    async viewIncidentDetails(incident) {
      try {
        console.log('[SENTINEL] Fetching detailed alerts for incident:', incident.id);
        
        // Show loading modal
        this.selectedIncident = { ...incident, loading: true };
        
        // Fetch detailed alerts from API
        const response = await this.axiosInstance.get(API_ENDPOINTS.SENTINEL_INCIDENT_DETAIL(incident.id));
        console.log('[SENTINEL] Detailed alerts response:', response.data);
        
        // Update selected incident with detailed alerts
        this.selectedIncident = {
          ...incident,
          ...response.data.incident,
          alerts: response.data.alerts || [],
          loading: false
        };
        
        console.log('[SENTINEL] Updated incident with alerts:', this.selectedIncident);
      } catch (error) {
        console.error('[SENTINEL] Error fetching incident details:', error);
        // Still show the incident with available data
        this.selectedIncident = { ...incident, loading: false };
        this.showAlert('alert-danger', 'Failed to load detailed alerts', 'fas fa-exclamation-triangle');
      }
    },

    closeModal() {
      this.selectedIncident = null;
      this.expandedAlerts = {};
    },

    toggleAlertExpand(alertId) {
      this.expandedAlerts = {
        ...this.expandedAlerts,
        [alertId]: !this.expandedAlerts[alertId]
      };
    },

    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    },

    showAlert(type, text, icon) {
      this.alertMessage = {
        show: true,
        type,
        text,
        icon
      };
      
      setTimeout(() => {
        this.alertMessage.show = false;
      }, 5000);
    },

    async handleQueryParams() {
      const urlParams = new URLSearchParams(window.location.search);
      
      if (urlParams.get('connected') === 'sentinel') {
        this.showAlert('alert-success', 'Successfully connected to Microsoft Sentinel!', 'fas fa-check-circle');
        // Refresh connection status and load incidents after successful OAuth
        await this.checkConnectionStatus();
      } else if (urlParams.get('disconnected') === 'sentinel') {
        this.showAlert('alert-info', 'Disconnected from Microsoft Sentinel.', 'fas fa-info-circle');
        // Update connection status after disconnect
        await this.checkConnectionStatus();
      } else if (urlParams.get('error')) {
        this.showAlert('alert-danger', `Authentication failed: ${urlParams.get('error')}`, 'fas fa-exclamation-triangle');
      }
    },

    async saveIncidentToDatabase(incident) {
      try {
        // Check if already saving
        if (incident.saving) {
          console.log('[SENTINEL] Already saving, skipping...');
          return;
        }

        // Set saving state - Vue 3 way
        incident.saving = true;
        
        console.log('[SENTINEL] Saving incident to database:', incident);
        console.log('[SENTINEL] API endpoint:', API_ENDPOINTS.SENTINEL_SAVE_INCIDENT);
        
        // Get user_id from localStorage
        const userId = localStorage.getItem('user_id');
        console.log('[SENTINEL] User ID from localStorage:', userId);
        
        // Call API to save incident
        const response = await this.axiosInstance.post(API_ENDPOINTS.SENTINEL_SAVE_INCIDENT, {
          incident: incident,
          user_id: userId
        });
        
        console.log('[SENTINEL] Save response:', response.data);
        
        if (response.data.success) {
          // Mark as saved
          incident.saved = true;
          incident.saving = false;
          
          // Show success message
          this.showAlert('alert-success', response.data.message || 'Incident saved successfully!', 'fas fa-check-circle');
          
          // Reset saved state after 3 seconds
          setTimeout(() => {
            incident.saved = false;
          }, 3000);
        } else {
          incident.saving = false;
          this.showAlert('alert-danger', response.data.error || 'Failed to save incident', 'fas fa-exclamation-triangle');
        }
        
      } catch (error) {
        console.error('[SENTINEL] Error saving incident:', error);
        console.error('[SENTINEL] Error details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          statusText: error.response?.statusText
        });
        
        incident.saving = false;
        
        let errorMessage = 'Failed to save incident to database';
        if (error.response && error.response.data && error.response.data.error) {
          errorMessage = error.response.data.error;
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        this.showAlert('alert-danger', errorMessage, 'fas fa-exclamation-triangle');
      }
    }
  }
};
</script>

<style src="./Sentinel.css"></style>

