<template>
  <div class="consent-integration-example">
    <h2>Consent Integration Example</h2>
    <p>This component demonstrates how to integrate consent management into your components</p>

    <!-- Example 1: Create Policy with Consent -->
    <div class="example-section">
      <h3>Example 1: Create Policy</h3>
      <button @click="handleCreatePolicy" class="btn-primary">
        Create Policy (with Consent Check)
      </button>
    </div>

    <!-- Example 2: Upload Document with Consent -->
    <div class="example-section">
      <h3>Example 2: Upload Document</h3>
      <input type="file" @change="handleFileSelect" />
      <button @click="handleUploadDocument" class="btn-primary" :disabled="!selectedFile">
        Upload Document (with Consent Check)
      </button>
    </div>

    <!-- Example 3: Create Incident with Consent -->
    <div class="example-section">
      <h3>Example 3: Create Incident</h3>
      <button @click="handleCreateIncident" class="btn-primary">
        Create Incident (with Consent Check)
      </button>
    </div>

    <!-- Status Messages -->
    <div v-if="statusMessage" class="status-message" :class="statusType">
      {{ statusMessage }}
    </div>

    <!-- Consent Modal -->
    <ConsentModal
      ref="consentModalRef"
      v-if="showConsentModal"
    />
  </div>
</template>

<script>
import { ref } from 'vue';
import ConsentModal from './ConsentModal.vue';
import { checkConsentRequired, recordConsentAcceptance, CONSENT_ACTIONS } from '@/utils/consentManager.js';
import axios from 'axios';
import { API_BASE_URL } from '@/config/api.js';

export default {
  name: 'ConsentIntegrationExample',
  components: {
    ConsentModal
  },
  setup() {
    const consentModalRef = ref(null);
    const showConsentModal = ref(false);
    const consentConfig = ref(null);
    const currentAction = ref(null);
    const statusMessage = ref('');
    const statusType = ref('');
    const selectedFile = ref(null);

    // Generic function to execute action with consent check
    const executeWithConsent = async (actionType, actionFunction) => {
      console.log(`🔍 [Consent] Checking consent for: ${actionType}`);
      
      try {
        // Step 1: Check if consent is required
        const { required, config } = await checkConsentRequired(actionType);
        
        if (required && config) {
          console.log(`✅ [Consent] Consent required for ${actionType}`);
          console.log(`📋 [Consent] Config:`, config);
          
          // Step 2: Show consent modal
          consentConfig.value = config;
          currentAction.value = actionFunction;
          showConsentModal.value = true;
          
          // Wait for user response
          const accepted = await consentModalRef.value.show(actionType, config);
          
          if (accepted) {
            console.log(`✅ [Consent] User accepted consent for ${actionType}`);
            // Step 3: Execute action with consent data
            await actionFunction(config);
          } else {
            console.log(`❌ [Consent] User rejected consent for ${actionType}`);
            setStatus('Action cancelled - consent rejected', 'warning');
          }
        } else {
          console.log(`❌ [Consent] No consent required for ${actionType}`);
          // No consent required, execute directly
          await actionFunction(null);
        }
      } catch (error) {
        console.error(`❌ [Consent] Error in consent flow:`, error);
        
        // Check if the backend returned a CONSENT_REQUIRED error
        if (error.response?.data?.error === 'CONSENT_REQUIRED') {
          console.log(`🔄 [Consent] Backend requested consent`);
          const config = error.response.data.consent_config;
          consentConfig.value = config;
          currentAction.value = actionFunction;
          showConsentModal.value = true;
          
          const accepted = await consentModalRef.value.show(config.action_type, config);
          
          if (accepted) {
            await actionFunction(config);
          } else {
            setStatus('Action cancelled - consent rejected', 'warning');
          }
        } else {
          setStatus(`Error: ${error.message}`, 'error');
        }
      }
    };

    // Example 1: Create Policy
    const handleCreatePolicy = async () => {
      await executeWithConsent(
        CONSENT_ACTIONS.CREATE_POLICY,
        async (consentConfig) => {
          await createPolicy(consentConfig);
        }
      );
    };

    const createPolicy = async (consentConfig) => {
      try {
        const policyData = {
          PolicyName: 'Example Policy',
          PolicyDescription: 'This is an example policy created with consent',
          StartDate: new Date().toISOString().split('T')[0],
          Department: 'IT',
          Applicability: 'All',
          Scope: 'Example',
          Objective: 'Testing consent management',
          Identifier: `EX-${Date.now()}`,
          Status: 'Under Review',
          ActiveInactive: 'Inactive',
          // Add consent data if required
          ...(consentConfig && {
            consent_accepted: true,
            consent_config_id: consentConfig.config_id,
            framework_id: localStorage.getItem('framework_id')
          })
        };

        console.log('📤 [Create Policy] Sending request with data:', policyData);

        const response = await axios.post(
          `${API_BASE_URL}/api/frameworks/${localStorage.getItem('framework_id')}/policies/`,
          policyData,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
              'Content-Type': 'application/json'
            }
          }
        );

        console.log('✅ [Create Policy] Success:', response.data);
        setStatus('Policy created successfully!', 'success');

      } catch (error) {
        console.error('❌ [Create Policy] Error:', error);
        throw error; // Re-throw to be caught by executeWithConsent
      }
    };

    // Example 2: Upload Document
    const handleFileSelect = (event) => {
      selectedFile.value = event.target.files[0];
      console.log('📁 File selected:', selectedFile.value?.name);
    };

    const handleUploadDocument = async () => {
      if (!selectedFile.value) {
        setStatus('Please select a file first', 'warning');
        return;
      }

      await executeWithConsent(
        CONSENT_ACTIONS.UPLOAD_POLICY,
        async (consentConfig) => {
          await uploadDocument(consentConfig);
        }
      );
    };

    const uploadDocument = async (consentConfig) => {
      try {
        const formData = new FormData();
        formData.append('file', selectedFile.value);
        formData.append('userId', localStorage.getItem('user_id'));
        formData.append('type', 'policy');
        formData.append('policyName', 'Example Policy');

        // Add consent data if required
        if (consentConfig) {
          formData.append('consent_accepted', 'true');
          formData.append('consent_config_id', consentConfig.config_id);
          formData.append('framework_id', localStorage.getItem('framework_id'));
        }

        console.log('📤 [Upload] Sending file:', selectedFile.value.name);

        const response = await axios.post(
          `${API_BASE_URL}/api/upload-policy-document/`,
          formData,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
              'Content-Type': 'multipart/form-data'
            }
          }
        );

        console.log('✅ [Upload] Success:', response.data);
        setStatus('Document uploaded successfully!', 'success');
        selectedFile.value = null;

      } catch (error) {
        console.error('❌ [Upload] Error:', error);
        throw error;
      }
    };

    // Example 3: Create Incident
    const handleCreateIncident = async () => {
      await executeWithConsent(
        CONSENT_ACTIONS.CREATE_INCIDENT,
        async (consentConfig) => {
          await createIncident(consentConfig);
        }
      );
    };

    const createIncident = async (consentConfig) => {
      try {
        const incidentData = {
          IncidentTitle: 'Example Incident',
          IncidentDescription: 'This is an example incident created with consent',
          IncidentType: 'Security',
          Severity: 'Medium',
          Status: 'Open',
          DetectionMethod: 'Manual',
          Origin: 'Internal',
          UserId: localStorage.getItem('user_id'),
          // Add consent data if required
          ...(consentConfig && {
            consent_accepted: true,
            consent_config_id: consentConfig.config_id,
            framework_id: localStorage.getItem('framework_id')
          })
        };

        console.log('📤 [Create Incident] Sending request with data:', incidentData);

        const response = await axios.post(
          `${API_BASE_URL}/api/create-incident/`,
          incidentData,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
              'Content-Type': 'application/json'
            }
          }
        );

        console.log('✅ [Create Incident] Success:', response.data);
        setStatus('Incident created successfully!', 'success');

      } catch (error) {
        console.error('❌ [Create Incident] Error:', error);
        throw error;
      }
    };

    // Helper function to set status messages
    const setStatus = (message, type) => {
      statusMessage.value = message;
      statusType.value = type;
      setTimeout(() => {
        statusMessage.value = '';
        statusType.value = '';
      }, 5000);
    };

    return {
      consentModalRef,
      showConsentModal,
      handleCreatePolicy,
      handleFileSelect,
      handleUploadDocument,
      handleCreateIncident,
      selectedFile,
      statusMessage,
      statusType
    };
  }
};
</script>

<style scoped>
.consent-integration-example {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.example-section {
  margin: 30px 0;
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #f9f9f9;
}

.example-section h3 {
  margin-top: 0;
  color: #333;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

input[type="file"] {
  margin: 10px 0;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.status-message {
  margin-top: 20px;
  padding: 12px 16px;
  border-radius: 6px;
  font-weight: 500;
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

