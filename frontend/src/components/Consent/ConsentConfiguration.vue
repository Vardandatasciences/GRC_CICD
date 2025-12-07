<template>
  <div class="consent-configuration">
    <div class="page-header">
      <h1>Consent Management Configuration</h1>
      <p class="subtitle">Configure which actions require user consent</p>
    </div>

    <!-- Access Denied for Non-Admins -->
    <div v-if="!isGRCAdministrator && !checkingRole" class="access-denied-container">
      <div class="access-denied-content">
        <i class="fas fa-lock"></i>
        <h2>Access Denied</h2>
        <p>Only GRC Administrators can access Consent Management Configuration.</p>
        <p class="role-info">Your current role: <strong>{{ userRole || 'Unknown' }}</strong></p>
        <button @click="$router.push('/user-profile')" class="btn-back">
          <i class="fas fa-arrow-left"></i> Back to Profile
        </button>
      </div>
    </div>

    <!-- Framework Selector -->
    <div v-else-if="showFrameworkSelector && isGRCAdministrator" class="framework-selector-container">
      <div class="framework-selector-card">
        <h2><i class="fas fa-layer-group"></i> Select Framework</h2>
        <p>Please select a framework to configure consent settings:</p>
        <div class="framework-select-wrapper">
          <select v-model="frameworkId" @change="onFrameworkChange" class="framework-select" :disabled="loadingFrameworks">
            <option value="">-- Select Framework --</option>
            <option v-for="framework in frameworks" :key="framework.FrameworkId" :value="framework.FrameworkId">
              {{ framework.FrameworkName }}
            </option>
          </select>
          <div v-if="loadingFrameworks" class="loading-small">
            <div class="spinner-small"></div>
            <span>Loading frameworks...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-else-if="loading || checkingRole" class="loading-container">
      <div class="spinner"></div>
      <p>{{ checkingRole ? 'Checking permissions...' : 'Loading consent configurations...' }}</p>
    </div>

    <!-- Main Content -->
    <div v-else-if="isGRCAdministrator && frameworkId" class="content-container">
      <!-- Info Card -->
      <div class="info-card">
        <i class="fas fa-info-circle"></i>
        <div>
          <strong>About Consent Management</strong>
          <p>Enable or disable consent requirements for different actions. When enabled, users will need to accept consent before performing these actions. All consents are tracked and stored in the database.</p>
        </div>
      </div>

      <!-- Framework Info -->
      <div v-if="frameworks.length > 0" class="framework-info">
        <i class="fas fa-info-circle"></i>
        <span>Configuring consent for: <strong>{{ frameworks.find(f => f.FrameworkId == frameworkId)?.FrameworkName || 'Selected Framework' }}</strong></span>
        <button @click="showFrameworkSelector = true" class="btn-change-framework">
          <i class="fas fa-exchange-alt"></i> Change Framework
        </button>
      </div>

      <!-- Consent Configurations Table -->
      <div class="configurations-card">
        <div class="card-header">
          <h2><i class="fas fa-cog"></i> Action Consent Settings</h2>
          <button @click="saveAllConfigurations" class="btn-save" :disabled="saving">
            <i class="fas fa-save"></i>
            {{ saving ? 'Saving...' : 'Save All Changes' }}
          </button>
        </div>

        <div class="table-container">
          <table class="configurations-table">
            <thead>
              <tr>
                <th>Action</th>
                <th class="text-center">Consent Required</th>
                <th>Consent Text</th>
                <th>Last Updated</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="config in configurations" :key="config.config_id" class="config-row">
                <td>
                  <div class="action-info">
                    <i :class="getActionIcon(config.action_type)"></i>
                    <span class="action-label">{{ config.action_label }}</span>
                  </div>
                </td>
                <td class="text-center">
                  <label class="toggle-switch">
                    <input 
                      type="checkbox" 
                      v-model="config.is_enabled"
                      @change="markAsModified(config)"
                    >
                    <span class="toggle-slider"></span>
                  </label>
                </td>
                <td>
                  <textarea
                    v-model="config.consent_text"
                    @input="markAsModified(config)"
                    :disabled="!config.is_enabled"
                    class="consent-text-input"
                    rows="2"
                    placeholder="Enter consent text that users will see..."
                  ></textarea>
                </td>
                <td class="text-muted">
                  <span v-if="config.updated_at">
                    {{ formatDate(config.updated_at) }}
                    <br>
                    <small>by {{ config.updated_by_name || 'System' }}</small>
                  </span>
                  <span v-else>Never</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Consent History -->
      <div class="history-card">
        <div class="card-header">
          <h2><i class="fas fa-history"></i> Recent Consent Acceptances</h2>
          <button @click="loadConsentHistory" class="btn-secondary">
            <i class="fas fa-sync-alt"></i> Refresh
          </button>
        </div>

        <div v-if="loadingHistory" class="loading-small">
          <div class="spinner-small"></div>
          <span>Loading history...</span>
        </div>

        <div v-else-if="consentHistory.length === 0" class="empty-state">
          <i class="fas fa-inbox"></i>
          <p>No consent acceptances recorded yet</p>
        </div>

        <div v-else class="table-container">
          <table class="history-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Action</th>
                <th>Accepted At</th>
                <th>IP Address</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="acceptance in consentHistory" :key="acceptance.acceptance_id">
                <td>{{ acceptance.user_name }}</td>
                <td>
                  <span class="action-badge">{{ acceptance.action_label }}</span>
                </td>
                <td>{{ formatDateTime(acceptance.accepted_at) }}</td>
                <td class="text-muted">{{ acceptance.ip_address || 'N/A' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Success/Error Messages -->
    <transition name="fade">
      <div v-if="message" class="alert" :class="messageType">
        <i :class="messageType === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
        {{ message }}
      </div>
    </transition>
  </div>
</template>

<script>
import axios from 'axios';
import { API_BASE_URL, API_ENDPOINTS } from '../../config/api.js';

export default {
  name: 'ConsentConfiguration',
  data() {
    return {
      configurations: [],
      consentHistory: [],
      loading: true,
      loadingHistory: false,
      saving: false,
      message: '',
      messageType: 'success',
      modifiedConfigs: new Set(),
      frameworkId: null,
      userId: null,
      isGRCAdministrator: false,
      checkingRole: true,
      userRole: null,
      frameworks: [],
      loadingFrameworks: false,
      showFrameworkSelector: false
    };
  },
  async mounted() {
    this.userId = localStorage.getItem('user_id');
    await this.checkUserRole();
    if (this.isGRCAdministrator) {
      await this.initializeFramework();
      if (this.frameworkId) {
        this.loadConfigurations();
        this.loadConsentHistory();
      } else {
        await this.loadFrameworks();
        this.showFrameworkSelector = true;
        this.loading = false;
      }
    } else {
      this.loading = false;
    }
  },
  methods: {
    async initializeFramework() {
      // Try multiple sources for framework ID
      this.frameworkId = localStorage.getItem('framework_id') || 
                        localStorage.getItem('selectedFrameworkId') ||
                        sessionStorage.getItem('framework_id');
      
      // Convert to integer if it's a string
      if (this.frameworkId) {
        this.frameworkId = parseInt(this.frameworkId);
        if (isNaN(this.frameworkId)) {
          this.frameworkId = null;
        }
      }
      
      // If still no framework ID, try to get from API
      if (!this.frameworkId) {
        try {
          // Try to get selected framework from session
          const response = await axios.get(`${API_BASE_URL}/api/frameworks/get-selected/`, {
            headers: this.getAuthHeaders()
          });
          if (response.data && response.data.frameworkId) {
            this.frameworkId = parseInt(response.data.frameworkId);
            localStorage.setItem('framework_id', this.frameworkId);
          }
        } catch (error) {
          console.warn('Could not fetch selected framework from session:', error);
          // If that fails, try to get first available framework
          try {
            const frameworksResponse = await axios.get(`${API_BASE_URL}/api/frameworks/`, {
              headers: this.getAuthHeaders()
            });
            if (frameworksResponse.data && Array.isArray(frameworksResponse.data)) {
              const activeFrameworks = frameworksResponse.data.filter(
                f => f.Status === 'Approved' && f.ActiveInactive === 'Active'
              );
              if (activeFrameworks.length > 0) {
                this.frameworkId = activeFrameworks[0].FrameworkId;
                localStorage.setItem('framework_id', this.frameworkId);
              }
            }
          } catch (frameworksError) {
            console.warn('Could not fetch frameworks:', frameworksError);
          }
        }
      }
    },

    async loadFrameworks() {
      try {
        this.loadingFrameworks = true;
        const response = await axios.get(`${API_BASE_URL}/api/frameworks/`, {
          headers: this.getAuthHeaders()
        });
        
        if (response.data && Array.isArray(response.data)) {
          this.frameworks = response.data.filter(f => f.Status === 'Approved' && f.ActiveInactive === 'Active');
          // If we have frameworks and no selected one, use the first one
          if (this.frameworks.length > 0 && !this.frameworkId) {
            this.frameworkId = this.frameworks[0].FrameworkId;
            localStorage.setItem('framework_id', this.frameworkId);
            this.showFrameworkSelector = false;
            this.loadConfigurations();
            this.loadConsentHistory();
          }
        }
      } catch (error) {
        console.error('Error loading frameworks:', error);
        this.showMessage('Failed to load frameworks. Please select a framework manually.', 'error');
      } finally {
        this.loadingFrameworks = false;
      }
    },

    onFrameworkChange() {
      if (this.frameworkId) {
        localStorage.setItem('framework_id', this.frameworkId);
        this.showFrameworkSelector = false;
        this.loadConfigurations();
        this.loadConsentHistory();
      }
    },

    async checkUserRole() {
      try {
        this.checkingRole = true;
        const response = await axios.get(API_ENDPOINTS.USER_ROLE, {
          headers: this.getAuthHeaders()
        });

        if (response.data && response.data.success) {
          this.userRole = response.data.role;
          this.isGRCAdministrator = response.data.role === 'GRC Administrator';
        } else {
          // Fallback: check localStorage or session
          const storedRole = localStorage.getItem('user_role');
          this.userRole = storedRole || 'Unknown';
          this.isGRCAdministrator = storedRole === 'GRC Administrator';
        }
      } catch (error) {
        console.error('Error checking user role:', error);
        // Fallback check
        const storedRole = localStorage.getItem('user_role');
        this.userRole = storedRole || 'Unknown';
        this.isGRCAdministrator = storedRole === 'GRC Administrator';
      } finally {
        this.checkingRole = false;
      }
    },

    async loadConfigurations() {
      if (!this.frameworkId) {
        this.showMessage('Please select a framework first', 'error');
        await this.loadFrameworks();
        this.showFrameworkSelector = true;
        this.loading = false;
        return;
      }

      try {
        this.loading = true;
        const response = await axios.get(`${API_BASE_URL}/api/consent/configurations/`, {
          params: { framework_id: this.frameworkId },
          headers: this.getAuthHeaders()
        });

        if (response.data.status === 'success') {
          this.configurations = response.data.data;
          // Sort configurations by action label
          this.configurations.sort((a, b) => a.action_label.localeCompare(b.action_label));
        } else {
          this.showMessage(response.data.message || 'Failed to load consent configurations', 'error');
        }
      } catch (error) {
        console.error('Error loading consent configurations:', error);
        const errorMsg = error.response?.data?.message || 'Failed to load consent configurations';
        this.showMessage(errorMsg, 'error');
        
        // If framework_id is missing, show framework selector
        if (error.response?.status === 400 && errorMsg.includes('framework_id')) {
          await this.loadFrameworks();
          this.showFrameworkSelector = true;
        }
      } finally {
        this.loading = false;
      }
    },

    async loadConsentHistory() {
      try {
        this.loadingHistory = true;
        const response = await axios.get(`${API_BASE_URL}/api/consent/acceptances/`, {
          params: { framework_id: this.frameworkId },
          headers: this.getAuthHeaders()
        });

        if (response.data.status === 'success') {
          // Get last 20 acceptances
          this.consentHistory = response.data.data.slice(0, 20);
        }
      } catch (error) {
        console.error('Error loading consent history:', error);
      } finally {
        this.loadingHistory = false;
      }
    },

    markAsModified(config) {
      this.modifiedConfigs.add(config.config_id);
    },

    async saveAllConfigurations() {
      if (this.modifiedConfigs.size === 0) {
        this.showMessage('No changes to save', 'info');
        return;
      }

      try {
        this.saving = true;
        
        // Prepare modified configs
        const configsToUpdate = this.configurations
          .filter(c => this.modifiedConfigs.has(c.config_id))
          .map(c => ({
            config_id: c.config_id,
            is_enabled: c.is_enabled,
            consent_text: c.consent_text
          }));

        const response = await axios.put(
          `${API_BASE_URL}/api/consent/configurations/bulk-update/`,
          {
            configs: configsToUpdate,
            updated_by: this.userId
          },
          { headers: this.getAuthHeaders() }
        );

        if (response.data.status === 'success') {
          this.showMessage('Consent configurations saved successfully', 'success');
          this.modifiedConfigs.clear();
          this.loadConfigurations();
        } else {
          throw new Error(response.data.message || 'Failed to save configurations');
        }
      } catch (error) {
        console.error('Error saving consent configurations:', error);
        const errorMessage = error.response?.data?.message || 
                            error.response?.data?.error ||
                            error.message || 
                            'Failed to save consent configurations. Please try again.';
        this.showMessage(errorMessage, 'error');
      } finally {
        this.saving = false;
      }
    },

    getActionIcon(actionType) {
      const iconMap = {
        'create_policy': 'fas fa-file-alt',
        'create_compliance': 'fas fa-clipboard-check',
        'create_audit': 'fas fa-search',
        'create_incident': 'fas fa-exclamation-triangle',
        'create_risk': 'fas fa-shield-alt',
        'create_event': 'fas fa-calendar-alt',
        'upload_policy': 'fas fa-upload',
        'upload_audit': 'fas fa-upload',
        'upload_incident': 'fas fa-upload',
        'upload_risk': 'fas fa-upload',
        'upload_event': 'fas fa-upload'
      };
      return iconMap[actionType] || 'fas fa-cog';
    },

    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    },

    formatDateTime(dateString) {
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

    showMessage(msg, type = 'success') {
      this.message = msg;
      this.messageType = type;
      setTimeout(() => {
        this.message = '';
      }, 5000);
    },

    getAuthHeaders() {
      const token = localStorage.getItem('access_token');
      return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
    }
  }
};
</script>

<style scoped>
.consent-configuration {
  margin-left: 260px; /* Account for sidebar width */
  padding: 40px 30px;
  padding-top: 40px;
  position: relative;
  min-height: calc(100vh - 80px);
  background: #f5f7fa;
  box-sizing: border-box;
  width: calc(100% - 260px); /* Subtract sidebar width */
  transition: margin-left 0.3s ease, width 0.3s ease;
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .consent-configuration {
    margin-left: 0;
    width: 100%;
    padding: 20px 15px;
  }
}

.page-header {
  background: white;
  border-radius: 12px;
  padding: 32px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 12px;
  letter-spacing: -0.5px;
}

.page-header h1 i {
  color: #3b82f6;
  font-size: 32px;
}

.subtitle {
  color: #6b7280;
  font-size: 16px;
  margin: 0;
  font-weight: 400;
}

.loading-container {
  text-align: center;
  padding: 80px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 20px;
}

.loading-container p {
  color: #6b7280;
  font-size: 15px;
  margin: 0;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.content-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.info-card {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  padding: 24px 32px;
  border-radius: 12px;
  display: flex;
  gap: 16px;
  align-items: flex-start;
  box-shadow: 0 4px 6px rgba(59, 130, 246, 0.2);
  margin-bottom: 24px;
}

.info-card i {
  font-size: 24px;
  opacity: 0.95;
  margin-top: 2px;
  flex-shrink: 0;
}

.info-card strong {
  display: block;
  margin-bottom: 8px;
  font-size: 18px;
  font-weight: 600;
}

.info-card p {
  margin: 0;
  opacity: 0.95;
  line-height: 1.6;
  font-size: 15px;
}

.configurations-card,
.history-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 24px;
  border: 1px solid #e5e7eb;
}

.card-header {
  padding: 24px 32px;
  border-bottom: 2px solid #f3f4f6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #ffffff;
}

.card-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  letter-spacing: -0.3px;
}

.card-header h2 i {
  color: #3b82f6;
  font-size: 22px;
}

.btn-save,
.btn-secondary {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-save {
  background: #3b82f6;
  color: white;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.btn-save:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #e5e7eb;
}

.btn-secondary:hover {
  background: #e5e7eb;
  border-color: #d1d5db;
}

.table-container {
  overflow-x: auto;
}

.configurations-table,
.history-table {
  width: 100%;
  border-collapse: collapse;
}

.configurations-table thead,
.history-table thead {
  background: #f8f9fa;
}

.configurations-table th,
.history-table th {
  padding: 16px 24px;
  text-align: left;
  font-weight: 600;
  color: #111827;
  border-bottom: 2px solid #e5e7eb;
  font-size: 14px;
  background: #f9fafb;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 12px;
}

.configurations-table td,
.history-table td {
  padding: 20px 24px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 14px;
}

.config-row:hover {
  background: #f9fafb;
  transition: background 0.2s;
}

.action-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-info i {
  color: #3b82f6;
  font-size: 20px;
  width: 24px;
  text-align: center;
}

.action-label {
  font-weight: 600;
  color: #111827;
  font-size: 14px;
}

.text-center {
  text-align: center !important;
}

.text-muted {
  color: #6b7280;
  font-size: 13px;
  line-height: 1.5;
}

/* Toggle Switch */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 26px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.3s;
  border-radius: 26px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

.toggle-switch input:checked + .toggle-slider {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.toggle-switch input:checked + .toggle-slider:before {
  transform: translateX(24px);
}

.consent-text-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  transition: all 0.2s;
  background: white;
  color: #111827;
  line-height: 1.5;
}

.consent-text-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
}

.consent-text-input:hover:not(:disabled) {
  border-color: #d1d5db;
}

.consent-text-input:disabled {
  background: #f9fafb;
  cursor: not-allowed;
  color: #9ca3af;
}

.loading-small {
  padding: 2rem;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.spinner-small {
  width: 20px;
  height: 20px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
  background: #f9fafb;
  border-radius: 8px;
  margin: 20px 0;
}

.empty-state i {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.4;
  color: #9ca3af;
}

.empty-state p {
  font-size: 15px;
  margin: 0;
  color: #6b7280;
}

.action-badge {
  display: inline-block;
  padding: 6px 12px;
  background: #eff6ff;
  color: #1e40af;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  border: 1px solid #bfdbfe;
}

.alert {
  position: fixed;
  top: 2rem;
  right: 2rem;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  z-index: 9999;
  max-width: 400px;
}

.alert.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.alert.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

  .alert.info {
    background: #d1ecf1;
    color: #0c5460;
    border: 1px solid #bee5eb;
  }

  .framework-selector-container {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 50vh;
    padding: 2rem;
  }

  .framework-selector-card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    padding: 3rem;
    max-width: 600px;
    width: 100%;
    text-align: center;
  }

  .framework-selector-card h2 {
    font-size: 1.75rem;
    color: #2c3e50;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
  }

  .framework-selector-card h2 i {
    color: #3498db;
  }

  .framework-selector-card p {
    color: #7f8c8d;
    margin-bottom: 2rem;
  }

  .framework-select-wrapper {
    position: relative;
  }

  .framework-select {
    width: 100%;
    padding: 1rem;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 1rem;
    background: white;
    cursor: pointer;
    transition: border-color 0.3s;
  }

  .framework-select:focus {
    outline: none;
    border-color: #3498db;
  }

  .framework-select:disabled {
    background: #f5f5f5;
    cursor: not-allowed;
  }

.framework-info {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  padding: 16px 24px;
  border-radius: 8px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #1e40af;
  border: 1px solid #bfdbfe;
}

.framework-info i {
  font-size: 20px;
  color: #3b82f6;
}

.framework-info strong {
  color: #1e3a8a;
  font-weight: 600;
}

.btn-change-framework {
  margin-left: auto;
  padding: 8px 16px;
  background: white;
  color: #3b82f6;
  border: 1px solid #3b82f6;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-change-framework:hover {
  background: #3b82f6;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.access-denied-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  padding: 2rem;
}

.access-denied-content {
  text-align: center;
  max-width: 500px;
  padding: 3rem;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.access-denied-content i {
  font-size: 4rem;
  color: #e74c3c;
  margin-bottom: 1.5rem;
}

.access-denied-content h2 {
  font-size: 2rem;
  color: #2c3e50;
  margin-bottom: 1rem;
}

.access-denied-content p {
  color: #7f8c8d;
  margin-bottom: 1rem;
  line-height: 1.6;
}

.role-info {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 8px;
  margin: 1.5rem 0;
}

.role-info strong {
  color: #2c3e50;
}

.btn-back {
  margin-top: 1.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-back:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

@media (max-width: 1024px) {
  .consent-configuration {
    margin-left: 0;
    width: 100%;
    padding: 20px 15px;
  }
}

@media (max-width: 768px) {
  .consent-configuration {
    padding: 15px 10px;
  }

  .page-header {
    padding: 24px 20px;
  }

  .page-header h1 {
    font-size: 24px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .table-container {
    overflow-x: auto;
  }

  .configurations-table th,
  .configurations-table td,
  .history-table th,
  .history-table td {
    padding: 12px 16px;
    font-size: 13px;
  }

  .alert {
    top: 1rem;
    right: 1rem;
    left: 1rem;
    max-width: none;
  }

  .access-denied-content {
    padding: 2rem 1.5rem;
  }

  .access-denied-content h2 {
    font-size: 1.5rem;
  }

  .framework-info {
    flex-direction: column;
    align-items: flex-start;
  }

  .btn-change-framework {
    margin-left: 0;
    width: 100%;
    justify-content: center;
  }
}
</style>

