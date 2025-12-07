<!--
  EXAMPLE: Consent Integration in Existing Components
  
  This is an example showing how to integrate the consent management system
  into existing create/upload components.
  
  DO NOT USE THIS FILE DIRECTLY - Copy the relevant parts to your actual components
-->

<template>
  <div class="example-component">
    <!-- Example 1: Create Policy Button with Consent -->
    <button @click="handleCreatePolicy" class="btn-create">
      <i class="fas fa-file-alt"></i>
      Create Policy
    </button>

    <!-- Example 2: Upload Button with Consent -->
    <button @click="handleUpload" class="btn-upload">
      <i class="fas fa-upload"></i>
      Upload Documents
    </button>

    <!-- Consent Modal -->
    <ConsentModal
      :show="showConsentModal"
      :action-type="consentConfig?.action_type || ''"
      :action-label="consentConfig?.action_label || ''"
      :consent-text="consentConfig?.consent_text || ''"
      :config-id="consentConfig?.config_id || 0"
      @accepted="onConsentAccepted"
      @close="handleConsentClose"
    />
  </div>
</template>

<script>
import ConsentModal from './ConsentModal.vue';
import { checkConsentRequired, CONSENT_ACTIONS } from '@/utils/consentManager.js';

export default {
  name: 'ExampleIntegration',
  components: {
    ConsentModal
  },
  data() {
    return {
      showConsentModal: false,
      consentConfig: null,
      pendingAction: null,
      pendingActionData: null
    };
  },
  methods: {
    /**
     * Example 1: Create Policy with Consent Check
     * Replace this with your actual create policy method
     */
    async handleCreatePolicy() {
      try {
        // Step 1: Check if consent is required
        const { required, config } = await checkConsentRequired(CONSENT_ACTIONS.CREATE_POLICY);
        
        if (required && config) {
          // Step 2: If consent required, show modal
          this.consentConfig = config;
          this.pendingAction = 'createPolicy';
          this.showConsentModal = true;
        } else {
          // Step 3: If no consent required, proceed directly
          await this.createPolicy();
        }
      } catch (error) {
        console.error('Error in handleCreatePolicy:', error);
        this.$toast.error('Failed to check consent requirements');
      }
    },

    /**
     * Example 2: Upload with Consent Check
     * Replace this with your actual upload method
     */
    async handleUpload() {
      try {
        // Step 1: Check if consent is required
        // Change CONSENT_ACTIONS.UPLOAD_POLICY to match your module
        const { required, config } = await checkConsentRequired(CONSENT_ACTIONS.UPLOAD_POLICY);
        
        if (required && config) {
          // Step 2: If consent required, show modal
          this.consentConfig = config;
          this.pendingAction = 'uploadDocuments';
          this.showConsentModal = true;
        } else {
          // Step 3: If no consent required, proceed directly
          await this.uploadDocuments();
        }
      } catch (error) {
        console.error('Error in handleUpload:', error);
        this.$toast.error('Failed to check consent requirements');
      }
    },

    /**
     * Handle consent acceptance
     * This is called when user accepts the consent
     */
    async onConsentAccepted() {
      try {
        this.showConsentModal = false;
        
        // Execute the pending action based on what was stored
        if (this.pendingAction === 'createPolicy') {
          await this.createPolicy();
        } else if (this.pendingAction === 'uploadDocuments') {
          await this.uploadDocuments();
        }
        
        // Clear pending action
        this.pendingAction = null;
        this.pendingActionData = null;
      } catch (error) {
        console.error('Error executing action after consent:', error);
      }
    },

    /**
     * Handle consent modal close (user cancelled)
     */
    handleConsentClose() {
      this.showConsentModal = false;
      this.pendingAction = null;
      this.pendingActionData = null;
      this.$toast.info('Action cancelled - consent not accepted');
    },

    /**
     * Your actual create policy logic here
     * Replace with your real implementation
     */
    async createPolicy() {
      console.log('Creating policy...');
      // Your actual policy creation code here
      // Example:
      // const response = await axios.post('/api/policies/', policyData);
      // this.$toast.success('Policy created successfully');
    },

    /**
     * Your actual upload logic here
     * Replace with your real implementation
     */
    async uploadDocuments() {
      console.log('Uploading documents...');
      // Your actual upload code here
      // Example:
      // const formData = new FormData();
      // formData.append('file', this.selectedFile);
      // const response = await axios.post('/api/upload/', formData);
      // this.$toast.success('Upload completed successfully');
    }
  }
};
</script>

<style scoped>
.example-component {
  padding: 2rem;
}

.btn-create,
.btn-upload {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0.5rem;
}

.btn-create {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-upload {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.btn-create:hover,
.btn-upload:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
</style>

<!--
  INTEGRATION CHECKLIST:
  
  1. Import required modules:
     - ConsentModal component
     - checkConsentRequired function
     - CONSENT_ACTIONS constants
  
  2. Add ConsentModal to your component's components section
  
  3. Add data properties:
     - showConsentModal
     - consentConfig
     - pendingAction
  
  4. Wrap your action handlers with consent check:
     - Call checkConsentRequired before the action
     - Show modal if consent required
     - Execute action if no consent required
  
  5. Implement consent acceptance handler:
     - Execute pending action
     - Clear pending state
  
  6. Add ConsentModal to your template
  
  7. Test the integration:
     - Enable consent in admin settings
     - Verify modal appears
     - Verify action executes after acceptance
     - Verify action is cancelled if modal is closed
-->

