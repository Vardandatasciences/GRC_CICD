<template>
  <div class="consent-management-admin">
    <div class="header">
      <h1>Consent Management</h1>
      <p>Configure which actions require user consent</p>
    </div>

    <!-- Framework Selector -->
    <div class="framework-selector">
      <label>Framework:</label>
      <select v-model="selectedFrameworkId" @change="loadConfigurations">
        <option value="">Select Framework</option>
        <option v-for="framework in frameworks" :key="framework.id" :value="framework.id">
          {{ framework.name }}
        </option>
      </select>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <i class="fas fa-spinner fa-spin"></i> Loading configurations...
    </div>

    <!-- Configurations Table -->
    <div v-else-if="configurations.length > 0" class="configurations-table">
      <table>
        <thead>
          <tr>
            <th>Action</th>
            <th>Enabled</th>
            <th>Consent Text</th>
            <th>Last Updated</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="config in configurations" :key="config.config_id">
            <td>
              <div class="action-label">
                <i :class="getActionIcon(config.action_type)"></i>
                <strong>{{ config.action_label }}</strong>
                <span class="action-type">{{ config.action_type }}</span>
              </div>
            </td>
            <td>
              <label class="toggle-switch">
                <input
                  type="checkbox"
                  :checked="config.is_enabled"
                  @change="toggleEnabled(config)"
                />
                <span class="slider"></span>
              </label>
            </td>
            <td>
              <div class="consent-text-preview">
                {{ truncateText(config.consent_text, 100) }}
              </div>
            </td>
            <td>
              <div class="update-info">
                <div>{{ formatDate(config.updated_at) }}</div>
                <small v-if="config.updated_by">by {{ config.updated_by }}</small>
              </div>
            </td>
            <td>
              <button @click="editConfig(config)" class="btn-edit">
                <i class="fas fa-edit"></i> Edit
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Bulk Actions -->
      <div class="bulk-actions">
        <button @click="enableAll" class="btn-secondary">
          <i class="fas fa-check-circle"></i> Enable All
        </button>
        <button @click="disableAll" class="btn-secondary">
          <i class="fas fa-times-circle"></i> Disable All
        </button>
        <button @click="saveChanges" class="btn-primary" :disabled="!hasChanges">
          <i class="fas fa-save"></i> Save Changes
        </button>
      </div>
    </div>

    <!-- No Data State -->
    <div v-else class="no-data">
      <i class="fas fa-info-circle"></i>
      <p>No configurations found. Please select a framework.</p>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-container">
        <div class="modal-header">
          <h2>Edit Consent Configuration</h2>
          <button @click="closeEditModal" class="close-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label>Action:</label>
            <input
              type="text"
              :value="editingConfig.action_label"
              disabled
              class="form-control"
            />
          </div>

          <div class="form-group">
            <label>Enabled:</label>
            <label class="toggle-switch">
              <input
                type="checkbox"
                v-model="editingConfig.is_enabled"
              />
              <span class="slider"></span>
            </label>
          </div>

          <div class="form-group">
            <label>Consent Text:</label>
            <textarea
              v-model="editingConfig.consent_text"
              class="form-control"
              rows="6"
              placeholder="Enter the consent text that users will need to accept..."
            ></textarea>
            <small>Character count: {{ editingConfig.consent_text?.length || 0 }}</small>
          </div>

          <div class="form-group">
            <label>Preview:</label>
            <div class="consent-preview">
              <div class="preview-header">
                <i class="fas fa-shield-check"></i>
                Consent Required
              </div>
              <div class="preview-body">
                <h3>{{ editingConfig.action_label }}</h3>
                <p>{{ editingConfig.consent_text }}</p>
                <label>
                  <input type="checkbox" disabled />
                  I have read and agree to the above consent statement
                </label>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeEditModal" class="btn-secondary">Cancel</button>
          <button @click="saveEdit" class="btn-primary">
            <i class="fas fa-save"></i> Save
          </button>
        </div>
      </div>
    </div>

    <!-- Status Message -->
    <div v-if="statusMessage" class="status-message" :class="statusType">
      <i :class="statusIcon"></i>
      {{ statusMessage }}
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { API_BASE_URL } from '@/config/api.js';

export default {
  name: 'ConsentManagementAdmin',
  setup() {
    const frameworks = ref([]);
    const selectedFrameworkId = ref('');
    const configurations = ref([]);
    const loading = ref(false);
    const hasChanges = ref(false);
    const showEditModal = ref(false);
    const editingConfig = ref(null);
    const statusMessage = ref('');
    const statusType = ref('');

    const statusIcon = computed(() => {
      switch (statusType.value) {
        case 'success': return 'fas fa-check-circle';
        case 'error': return 'fas fa-exclamation-circle';
        case 'warning': return 'fas fa-exclamation-triangle';
        default: return 'fas fa-info-circle';
      }
    });

    // Load frameworks on mount
    onMounted(async () => {
      await loadFrameworks();
      // Auto-select if framework_id in localStorage
      const savedFrameworkId = localStorage.getItem('framework_id');
      if (savedFrameworkId) {
        selectedFrameworkId.value = savedFrameworkId;
        await loadConfigurations();
      }
    });

    const loadFrameworks = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/frameworks/`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });
        frameworks.value = response.data.map(f => ({
          id: f.FrameworkId,
          name: f.FrameworkName
        }));
      } catch (error) {
        console.error('Error loading frameworks:', error);
        setStatus('Error loading frameworks', 'error');
      }
    };

    const loadConfigurations = async () => {
      if (!selectedFrameworkId.value) return;

      loading.value = true;
      try {
        const response = await axios.get(
          `${API_BASE_URL}/api/consent/configurations/`,
          {
            params: { framework_id: selectedFrameworkId.value },
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );
        configurations.value = response.data.data;
        hasChanges.value = false;
      } catch (error) {
        console.error('Error loading configurations:', error);
        setStatus('Error loading configurations', 'error');
      } finally {
        loading.value = false;
      }
    };

    const toggleEnabled = (config) => {
      config.is_enabled = !config.is_enabled;
      hasChanges.value = true;
    };

    const editConfig = (config) => {
      editingConfig.value = { ...config };
      showEditModal.value = true;
    };

    const closeEditModal = () => {
      showEditModal.value = false;
      editingConfig.value = null;
    };

    const saveEdit = async () => {
      try {
        const userId = localStorage.getItem('user_id');
        await axios.put(
          `${API_BASE_URL}/api/consent/configurations/${editingConfig.value.config_id}/`,
          {
            is_enabled: editingConfig.value.is_enabled,
            consent_text: editingConfig.value.consent_text,
            updated_by: userId
          },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );

        // Update local config
        const index = configurations.value.findIndex(
          c => c.config_id === editingConfig.value.config_id
        );
        if (index !== -1) {
          configurations.value[index] = { ...editingConfig.value };
        }

        setStatus('Configuration updated successfully', 'success');
        closeEditModal();
      } catch (error) {
        console.error('Error saving configuration:', error);
        setStatus('Error saving configuration', 'error');
      }
    };

    const enableAll = () => {
      configurations.value.forEach(config => {
        config.is_enabled = true;
      });
      hasChanges.value = true;
    };

    const disableAll = () => {
      configurations.value.forEach(config => {
        config.is_enabled = false;
      });
      hasChanges.value = true;
    };

    const saveChanges = async () => {
      try {
        const userId = localStorage.getItem('user_id');
        const updates = configurations.value.map(config => ({
          config_id: config.config_id,
          is_enabled: config.is_enabled,
          consent_text: config.consent_text
        }));

        await axios.put(
          `${API_BASE_URL}/api/consent/configurations/bulk/`,
          {
            configs: updates,
            updated_by: userId
          },
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          }
        );

        hasChanges.value = false;
        setStatus('Changes saved successfully', 'success');
        await loadConfigurations();
      } catch (error) {
        console.error('Error saving changes:', error);
        setStatus('Error saving changes', 'error');
      }
    };

    const getActionIcon = (actionType) => {
      const icons = {
        'create_policy': 'fas fa-file-alt',
        'create_compliance': 'fas fa-tasks',
        'create_audit': 'fas fa-clipboard-check',
        'create_incident': 'fas fa-exclamation-triangle',
        'create_risk': 'fas fa-shield-alt',
        'create_event': 'fas fa-calendar-alt',
        'upload_policy': 'fas fa-upload',
        'upload_audit': 'fas fa-upload',
        'upload_incident': 'fas fa-upload',
        'upload_risk': 'fas fa-upload',
        'upload_event': 'fas fa-upload'
      };
      return icons[actionType] || 'fas fa-cog';
    };

    const truncateText = (text, maxLength) => {
      if (!text) return '';
      return text.length > maxLength
        ? text.substring(0, maxLength) + '...'
        : text;
    };

    const formatDate = (dateString) => {
      if (!dateString) return 'Never';
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    };

    const setStatus = (message, type) => {
      statusMessage.value = message;
      statusType.value = type;
      setTimeout(() => {
        statusMessage.value = '';
        statusType.value = '';
      }, 5000);
    };

    return {
      frameworks,
      selectedFrameworkId,
      configurations,
      loading,
      hasChanges,
      showEditModal,
      editingConfig,
      statusMessage,
      statusType,
      statusIcon,
      loadConfigurations,
      toggleEnabled,
      editConfig,
      closeEditModal,
      saveEdit,
      enableAll,
      disableAll,
      saveChanges,
      getActionIcon,
      truncateText,
      formatDate
    };
  }
};
</script>

<style scoped>
.consent-management-admin {
  padding: 30px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  margin-bottom: 30px;
}

.header h1 {
  font-size: 28px;
  color: #2c3e50;
  margin-bottom: 8px;
}

.header p {
  color: #7f8c8d;
  font-size: 14px;
}

.framework-selector {
  margin-bottom: 30px;
  display: flex;
  align-items: center;
  gap: 15px;
}

.framework-selector label {
  font-weight: 600;
  color: #2c3e50;
}

.framework-selector select {
  padding: 10px 15px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  min-width: 250px;
  cursor: pointer;
}

.loading {
  text-align: center;
  padding: 50px;
  color: #7f8c8d;
  font-size: 16px;
}

.configurations-table {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

th {
  padding: 16px;
  text-align: left;
  font-weight: 600;
  font-size: 14px;
}

tbody tr {
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}

tbody tr:hover {
  background: #f9f9f9;
}

td {
  padding: 16px;
}

.action-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.action-label i {
  font-size: 18px;
  color: #667eea;
  margin-right: 8px;
}

.action-type {
  font-size: 12px;
  color: #95a5a6;
  font-family: monospace;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #667eea;
}

input:checked + .slider:before {
  transform: translateX(26px);
}

.consent-text-preview {
  max-width: 400px;
  font-size: 13px;
  color: #555;
  line-height: 1.5;
}

.update-info {
  font-size: 13px;
  color: #7f8c8d;
}

.update-info small {
  display: block;
  margin-top: 2px;
  font-size: 11px;
}

.btn-edit,
.btn-primary,
.btn-secondary {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-edit {
  background: #ecf0f1;
  color: #2c3e50;
}

.btn-edit:hover {
  background: #d5dbdb;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
}

.btn-secondary:hover {
  background: #f8f9fe;
}

.bulk-actions {
  padding: 20px;
  background: #f9f9f9;
  border-top: 1px solid #e0e0e0;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.no-data {
  text-align: center;
  padding: 60px 20px;
  color: #95a5a6;
}

.no-data i {
  font-size: 48px;
  margin-bottom: 16px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.modal-container {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 700px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #e0e0e0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #2c3e50;
}

.form-control {
  width: 100%;
  padding: 10px 12px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
}

.form-control:focus {
  outline: none;
  border-color: #667eea;
}

.form-control:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.consent-preview {
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.preview-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-body {
  padding: 16px;
  background: #f9f9f9;
}

.preview-body h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #2c3e50;
}

.preview-body p {
  margin: 0 0 16px 0;
  line-height: 1.6;
  color: #555;
}

.modal-footer {
  padding: 20px 24px;
  border-top: 1px solid #e0e0e0;
  background: #f9f9f9;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.status-message {
  position: fixed;
  bottom: 30px;
  right: 30px;
  padding: 16px 20px;
  border-radius: 8px;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 10px;
  z-index: 10001;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.status-message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.status-message.warning {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}
</style>

