# Consent Management System - Integration Guide

## Overview

The Consent Management System is a common module that allows GRC Administrators to enable/disable consent requirements for specific actions. When consent is enabled for an action, users must explicitly accept before performing that action.

## Supported Actions

The following actions support consent management:

### Create Actions:
- `create_policy` - Creating a new policy
- `create_compliance` - Creating a new compliance item
- `create_audit` - Creating a new audit
- `create_incident` - Creating a new incident
- `create_risk` - Creating a new risk
- `create_event` - Creating a new event

### Upload Actions:
- `upload_policy` - Uploading policy documents
- `upload_audit` - Uploading audit documents
- `upload_incident` - Uploading incident evidence
- `upload_risk` - Uploading risk evidence
- `upload_event` - Uploading event evidence

## How It Works

1. **GRC Administrator Configuration**: The GRC Administrator enables/disables consent requirements and configures consent text through the admin interface.

2. **User Action**: When a user attempts to perform an action (e.g., create a policy), the frontend checks if consent is required.

3. **Consent Modal**: If consent is required, a modal appears with the consent text. The user must read and explicitly accept.

4. **Backend Validation**: The backend validates that consent was provided before processing the request.

5. **Audit Trail**: All consent acceptances are logged in the database with timestamp, IP address, and user agent.

## Frontend Integration

### Method 1: Using the Consent Composable (Vue 3 Composition API)

```vue
<template>
  <div>
    <!-- Your component UI -->
    <button @click="handleCreatePolicy">Create Policy</button>
    
    <!-- Consent Modal -->
    <ConsentModal
      ref="consentModalRef"
      v-if="showConsentModal"
      @consent-accepted="onConsentAccepted"
      @consent-rejected="onConsentRejected"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import ConsentModal from '@/components/Consent/ConsentModal.vue';
import { checkConsentRequired, recordConsentAcceptance, CONSENT_ACTIONS } from '@/utils/consentManager.js';
import axios from 'axios';
import { API_BASE_URL } from '@/config/api.js';

const consentModalRef = ref(null);
const showConsentModal = ref(false);
const pendingAction = ref(null);
const consentConfig = ref(null);

const handleCreatePolicy = async () => {
  // Check if consent is required
  const { required, config } = await checkConsentRequired(CONSENT_ACTIONS.CREATE_POLICY);
  
  if (required) {
    // Store config and show modal
    consentConfig.value = config;
    showConsentModal.value = true;
    await consentModalRef.value.show(CONSENT_ACTIONS.CREATE_POLICY, config);
  } else {
    // No consent required, proceed directly
    await createPolicy();
  }
};

const onConsentAccepted = async () => {
  showConsentModal.value = false;
  await createPolicy();
};

const onConsentRejected = () => {
  showConsentModal.value = false;
  // Handle rejection (e.g., show message)
  console.log('User rejected consent');
};

const createPolicy = async () => {
  try {
    const policyData = {
      // Your policy data...
      PolicyName: 'My Policy',
      PolicyDescription: 'Description',
      // ... other fields
    };
    
    // If consent was required, include consent acceptance
    if (consentConfig.value) {
      policyData.consent_accepted = true;
      policyData.consent_config_id = consentConfig.value.config_id;
    }
    
    const response = await axios.post(
      `${API_BASE_URL}/api/frameworks/${frameworkId}/policies/`,
      policyData,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    // Handle success
    console.log('Policy created successfully:', response.data);
    
  } catch (error) {
    // Check if error is due to consent requirement
    if (error.response?.data?.error === 'CONSENT_REQUIRED') {
      // Show consent modal with config from error response
      consentConfig.value = error.response.data.consent_config;
      showConsentModal.value = true;
      await consentModalRef.value.show(
        error.response.data.consent_config.action_type,
        error.response.data.consent_config
      );
    } else {
      console.error('Error creating policy:', error);
    }
  }
};
</script>
```

### Method 2: Using the Consent Mixin (Vue 2 / Options API)

```vue
<template>
  <div>
    <button @click="handleCreatePolicy">Create Policy</button>
    
    <ConsentModal
      ref="consentModal"
      v-if="showConsentModal"
      @consent-accepted="onConsentAccepted"
      @consent-rejected="onConsentRejected"
    />
  </div>
</template>

<script>
import ConsentModal from '@/components/Consent/ConsentModal.vue';
import { checkConsentRequired, recordConsentAcceptance, CONSENT_ACTIONS } from '@/utils/consentManager.js';
import axios from 'axios';
import { API_BASE_URL } from '@/config/api.js';

export default {
  name: 'PolicyComponent',
  components: {
    ConsentModal
  },
  data() {
    return {
      showConsentModal: false,
      consentConfig: null
    };
  },
  methods: {
    async handleCreatePolicy() {
      const { required, config } = await checkConsentRequired(CONSENT_ACTIONS.CREATE_POLICY);
      
      if (required) {
        this.consentConfig = config;
        this.showConsentModal = true;
        await this.$refs.consentModal.show(CONSENT_ACTIONS.CREATE_POLICY, config);
      } else {
        await this.createPolicy();
      }
    },
    
    async onConsentAccepted() {
      this.showConsentModal = false;
      await this.createPolicy();
    },
    
    onConsentRejected() {
      this.showConsentModal = false;
      this.$message.warning('You must accept consent to proceed with this action.');
    },
    
    async createPolicy() {
      try {
        const policyData = {
          PolicyName: this.formData.policyName,
          PolicyDescription: this.formData.description,
          // ... other fields
        };
        
        if (this.consentConfig) {
          policyData.consent_accepted = true;
          policyData.consent_config_id = this.consentConfig.config_id;
        }
        
        const response = await axios.post(
          `${API_BASE_URL}/api/frameworks/${this.frameworkId}/policies/`,
          policyData
        );
        
        this.$message.success('Policy created successfully');
        
      } catch (error) {
        if (error.response?.data?.error === 'CONSENT_REQUIRED') {
          this.consentConfig = error.response.data.consent_config;
          this.showConsentModal = true;
          await this.$refs.consentModal.show(
            error.response.data.consent_config.action_type,
            error.response.data.consent_config
          );
        } else {
          this.$message.error('Error creating policy');
          console.error(error);
        }
      }
    }
  }
};
</script>
```

### Method 3: Simplified Integration Pattern

For simpler integration, you can use this pattern:

```javascript
import { checkConsentRequired, CONSENT_ACTIONS } from '@/utils/consentManager.js';

async function createPolicyWithConsent() {
  // 1. Check consent
  const { required, config } = await checkConsentRequired(CONSENT_ACTIONS.CREATE_POLICY);
  
  // 2. Prepare data
  const policyData = {
    PolicyName: 'My Policy',
    // ... other fields
  };
  
  // 3. Add consent fields if required
  if (required) {
    policyData.consent_accepted = true;
    policyData.consent_config_id = config.config_id;
  }
  
  // 4. Make API call
  const response = await axios.post('/api/policies/', policyData);
  
  return response.data;
}
```

## Backend Integration

The backend uses a decorator pattern. Example:

```python
from ...routes.Consent import require_consent

@api_view(['POST'])
@permission_classes([PolicyCreatePermission])
@require_consent('create_policy')
def create_policy(request):
    # Your view logic
    pass
```

The `@require_consent` decorator automatically:
1. Checks if consent is enabled for the action
2. Validates that consent was provided in the request
3. Returns a 403 error with consent config if consent is required but not provided

## Administrator Configuration

Administrators can manage consent settings through:
- **Path**: `/admin/consent-management`
- **Features**:
  - Enable/disable consent per action
  - Customize consent text
  - View consent acceptance history
  - Export consent logs for compliance

## Database Schema

### consent_configuration
- Stores consent settings per action and framework
- Fields: config_id, action_type, action_label, is_enabled, consent_text, framework_id

### consent_acceptance
- Audit trail of all consent acceptances
- Fields: acceptance_id, user_id, config_id, action_type, accepted_at, ip_address, user_agent, framework_id

## API Endpoints

### Check Consent Requirement
```
POST /api/consent/check/
Body: { "action_type": "create_policy", "framework_id": 1 }
Response: { "status": "success", "required": true/false, "config": {...} }
```

### Record Consent Acceptance
```
POST /api/consent/accept/
Body: {
  "user_id": 1,
  "config_id": 1,
  "action_type": "create_policy",
  "framework_id": 1,
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
```

### Get Consent Configurations (Admin)
```
GET /api/consent/configurations/?framework_id=1
Response: { "status": "success", "data": [...] }
```

### Update Consent Configuration (Admin)
```
PUT /api/consent/configurations/:config_id/
Body: { "is_enabled": true, "consent_text": "...", "updated_by": 1 }
```

## Best Practices

1. **Always check consent before critical actions**: Use `checkConsentRequired()` before any action that creates, modifies, or uploads data.

2. **Handle consent rejection gracefully**: Provide clear feedback to users when they reject consent.

3. **Include consent fields in API calls**: Always include `consent_accepted` and `consent_config_id` when consent is required.

4. **Error handling**: Always check for `CONSENT_REQUIRED` error and show the consent modal.

5. **User experience**: The consent modal should appear smoothly and not block the user unnecessarily.

## Testing

To test consent functionality:

1. **Enable Consent** (as GRC Administrator):
   - Navigate to Consent Management
   - Enable consent for an action (e.g., Create Policy)
   - Set consent text

2. **Test User Flow** (as regular user):
   - Attempt to create a policy
   - Consent modal should appear
   - Accept consent
   - Policy should be created successfully

3. **Verify Audit Trail**:
   - Check `consent_acceptance` table for the entry
   - Verify user_id, timestamp, IP address are recorded

## Troubleshooting

### Consent modal not appearing
- Check if framework_id is set in localStorage
- Verify consent is enabled for the action in the database
- Check browser console for errors

### Backend returns 403 CONSENT_REQUIRED
- This is expected when consent is not provided
- Show the consent modal with the config from the error response

### Consent not being recorded
- Check API endpoint `/api/consent/accept/` is working
- Verify user_id and config_id are correct
- Check network tab for failed requests

## Support

For issues or questions about consent management, contact the development team.

