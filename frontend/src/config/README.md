# API Configuration System

This directory contains the centralized API configuration system that allows you to easily switch between different backend environments without manually changing URLs throughout the codebase.

## How to Use

### 1. Environment Configuration

In `api.js`, you can change the environment by modifying the `ENVIRONMENT` variable:

```javascript
const ENVIRONMENT = 'aws'; // Options: 'aws', 'local', 'development'
```

### 2. Available Environments

- **aws**: `http://15.207.108.158:8000` (Production AWS EC2)
- **local**: `http://localhost:8000` (Local development)
- **development**: `http://127.0.0.1:8000` (Alternative local development)

### 3. Using the Configuration

Instead of hardcoding URLs, import and use the centralized endpoints:

```javascript
import { API_ENDPOINTS } from '../../config/api.js'

// Instead of:
// axios.post('http://15.207.108.158:8000/api/login/', data)

// Use:
axios.post(API_ENDPOINTS.LOGIN, data)
```

### 4. Available Endpoints

The configuration includes endpoints for:

- **Authentication**: LOGIN, LOGOUT, SEND_OTP, VERIFY_OTP, RESET_PASSWORD
- **User Management**: USER_PROFILE, USER_BUSINESS_INFO, USER_PERMISSIONS, USER_ROLE
- **Notifications**: GET_NOTIFICATIONS, MARK_AS_READ, PUSH_NOTIFICATION
- **Policy Management**: POLICIES, POLICY, POLICY_VERSION, etc.
- **Framework Management**: FRAMEWORK_EXPLORER, UPLOAD_FRAMEWORK, etc.
- **Risk Management**: RISK_INSTANCES, RISKS, etc.
- **Incident Management**: INCIDENTS, INCIDENT, etc.
- **Audit Management**: AUDITS, AUDIT_TASK_DETAILS, etc.

### 5. Adding New Endpoints

To add a new endpoint, simply add it to the `API_ENDPOINTS` object in `api.js`:

```javascript
export const API_ENDPOINTS = {
  // ... existing endpoints
  NEW_ENDPOINT: `${API_BASE_URL}/api/new-endpoint/`,
  NEW_ENDPOINT_WITH_PARAM: (param) => `${API_BASE_URL}/api/new-endpoint/${param}/`,
}
```

### 6. Benefits

- **Single Point of Control**: Change environment by modifying one variable
- **Consistency**: All components use the same base URL
- **Maintainability**: Easy to add new environments or endpoints
- **Debugging**: Console logs show which environment is being used

### 7. Migration Status

The following components have been updated to use the centralized configuration:

✅ **Login Module**:
- LoginView.vue
- HomeView.vue
- ForgotPassword.vue
- UserProfile.vue

✅ **Policy Module**:
- CreatePolicy.vue (partially updated)
- incidents.js store module

🔄 **In Progress**:
- Other Policy components
- Risk components
- Incident components
- Audit components

### 8. Console Output

When the application starts, you'll see:
```
🔧 API Configuration: Using aws environment
🌐 Base URL: http://15.207.108.158:8000
```

This helps you verify which environment is currently active.
