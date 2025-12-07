import axios from 'axios';
import { API_BASE_URL, API_ENDPOINTS } from '../config/api.js';
 
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  // timeout: 15000, // Removed timeout to prevent request timeouts
  withCredentials: true // Include cookies in requests for session handling
});
 
// Add response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error);
   
    // Add more detailed logging for network errors
    if (error.code === 'ERR_NETWORK') {
      console.error('Network error details:', {
        message: error.message,
        config: {
          url: error.config?.url,
          method: error.config?.method,
          timeout: error.config?.timeout
        }
      });
    }
   
    return Promise.reject(error);
  }
);
// Add request interceptor to include JWT token
api.interceptors.request.use((config) => {
  // Get JWT token from localStorage (authService stores it as 'access_token')
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    console.log(`🔐 [API] Adding JWT token to request: ${config.method?.toUpperCase()} ${config.url}`);
  } else {
    console.log(`⚠️ [API] No JWT token found for request: ${config.method?.toUpperCase()} ${config.url}`);
  }
 
  // Add user_id to request if available (for backward compatibility)
  const userId = localStorage.getItem('user_id');
  if (userId && !config.url.includes('api/incidents/recent/')) {
    // Add user_id to query params for GET requests
    if (config.method === 'get') {
      config.params = config.params || {};
      config.params.user_id = userId;
    }
    // Add user_id to request body for POST/PUT requests
    else if (config.method === 'post' || config.method === 'put') {
      if (config.data && typeof config.data === 'object') {
        config.data.user_id = userId;
      }
    }
  }
 
  // Log outgoing requests
  console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`, {
    data: config.data,
    params: config.params
  });
 
  return config;
});
 
// Policy document upload service
export const policyService = {
  // Upload policy document to S3
  uploadPolicyDocument: (file, userId, policyName, docType = 'policy') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('userId', userId);
    formData.append('fileName', file.name);
    formData.append('type', docType);
    formData.append('policyName', policyName);
   
    // Use multipart/form-data for file uploads
    return api.post('/upload-policy-document/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }
};
 
export const incidentService = {
  // Incident main endpoints
  getIncidents: (params) => api.get('api/incidents/', { params }),
  createIncident: (data) => api.post('api/incidents/create/', data),
  updateIncidentStatus: (incidentId, data) => api.put(`api/incidents/${incidentId}/status/`, data),
 
  // Incident analytics endpoints
  getIncidentMetrics: (params) => api.get('api/incidents/metrics/', { params }),
  getIncidentMTTD: (params) => api.get('api/incidents/metrics/mttd/', { params }),
  getIncidentMTTR: (params) => api.get('api/incidents/metrics/mttr/', { params }),
  getIncidentMTTC: (params) => api.get('api/incidents/metrics/mttc/', { params }),
  getIncidentMTTRV: (params) => api.get('api/incidents/metrics/mttrv/', { params }),
  getIncidentVolume: (params) => api.get('api/incidents/metrics/volume/', { params }),
  getIncidentsBySeverity: (params) => api.get('api/incidents/metrics/by-severity/', { params }),
  getIncidentRootCauses: (params) => api.get('api/incidents/metrics/root-causes/', { params }),
  getIncidentTypes: (params) => api.get('api/incidents/metrics/types/', { params }),
  getIncidentOrigins: (params) => api.get('api/incidents/metrics/origins/', { params }),
  getIncidentCost: (params) => api.get('api/incidents/metrics/cost/', { params }),
  getIncidentClosureRate: (params) => api.get('api/incidents/metrics/closure-rate/', { params }),
  getIncidentReopenedCount: (params) => api.get('api/incidents/metrics/reopened-count/', { params }),
  getIncidentCount: (params) => api.get('api/incidents/metrics/count/', { params }),
 
  // Incident analytics for dashboard
  getIncidentDashboard: (params) => api.get('api/incidents/dashboard/', { params }),
  getIncidentAnalytics: (data) => api.post('api/incidents/dashboard/analytics/', data),
 
  // Recent incidents for dashboard
  getRecentIncidents: (limit = 3) => api.get('api/incidents/recent/', { params: { limit } }),
 
  // Framework endpoints for incident filtering
  getIncidentFrameworks: () => api.get('api/compliance/frameworks/public/'),
  getSelectedFramework: () => api.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED),

  // Other incident-related endpoints
  getIncidentCountsByStatus: () => api.get('api/incidents/counts-by-status/')
};
 
export const auditService = {
  // Audit findings related endpoints
  getAuditFindings: (params) => api.get('api/audit-findings/', { params }),
  getAuditFindingsDetail: (complianceId) => api.get(`api/audit-findings/${complianceId}/details/`),
 
  // Get data from lastchecklistitemverified table
  getChecklistVerified: (params = {}) => {
    const url = new URL(`${api.defaults.baseURL}/api/lastchecklistitemverified/`);
   
    // Add complied parameters if present
    if (params.complied && Array.isArray(params.complied)) {
      params.complied.forEach(value => {
        url.searchParams.append('complied[]', value);
      });
    } else {
      // Default to showing only non-compliant (0) and partially compliant (1)
      url.searchParams.append('complied[]', '0');
      url.searchParams.append('complied[]', '1');
    }
   
    return api.get(url.toString());
  },
 
  // Get specific audit finding details
  getAuditDetail: (auditId) => api.get(`api/audits/${auditId}/`),
 
  // Get audit findings by compliance id
  getAuditFindingsByCompliance: (complianceId) => api.get(`api/audit-findings/compliance/${complianceId}/`),
  getUsers: () => api.get('api/users/'),
 
  getOntimeMitigationPercentage: () => api.get('api/compliance/kpi-dashboard/analytics/ontime-mitigation/'),
 
  // Get compliance audit information
  getComplianceAuditInfo: (complianceId) => api.get(API_ENDPOINTS.COMPLIANCE_AUDIT_INFO(complianceId)),
};
 
export const complianceService = {
  // Framework endpoints
  getFrameworks: () => api.get('api/compliance/frameworks/public/'),
  getComplianceFrameworks: (params = {}) => api.get('api/compliance/frameworks/public/', { params }),
 
  // Policy endpoints
  getPolicies: (frameworkId) => api.get(API_ENDPOINTS.COMPLIANCE_POLICIES(frameworkId)),
  getCompliancePolicies: (frameworkId) => api.get(API_ENDPOINTS.COMPLIANCE_POLICIES(frameworkId)),
 
  // SubPolicy endpoints
  getSubPolicies: (policyId) => api.get(API_ENDPOINTS.COMPLIANCE_SUBPOLICIES(policyId)),
  getComplianceSubPolicies: (policyId) => api.get(API_ENDPOINTS.COMPLIANCE_SUBPOLICIES(policyId)),
 
  // View all compliances by type (framework, policy, subpolicy)
  getCompliancesByType: (type, id) => api.get(API_ENDPOINTS.COMPLIANCE_VIEW_BY_TYPE(type, id)),
 
  // CategoryBusinessUnit endpoints
  getCategoryBusinessUnits: (source) => api.get(API_ENDPOINTS.CATEGORY_BUSINESS_UNITS, { params: { source } }),
  getCategoryBusinessPolicies: (source) => api.get(API_ENDPOINTS.CATEGORY_BUSINESS_UNITS, { params: { source } }),
  addCategoryBusinessUnit: (data) => api.post(API_ENDPOINTS.CATEGORY_BUSINESS_UNITS_ADD, data),
 
  // Compliance endpoints
  createCompliance: (data) => {
    // Add default values for required fields
    const defaultData = {
      ApprovalDueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 7 days from now
      Status: 'Under Review',
      ActiveInactive: 'Active',
      ComplianceVersion: '1.0',
      ...data
    };
   
    // Ensure all required fields are present and properly formatted
    const formattedData = {
      SubPolicy: defaultData.SubPolicy,
      ComplianceTitle: defaultData.ComplianceTitle || '',
      ComplianceItemDescription: defaultData.ComplianceItemDescription || '',
      ComplianceType: defaultData.ComplianceType || '',
      Scope: defaultData.Scope || '',
      Objective: defaultData.Objective || '',
      BusinessUnitsCovered: defaultData.BusinessUnitsCovered || '',
      Identifier: defaultData.Identifier || '', // Add the missing Identifier field
      IsRisk: Boolean(defaultData.IsRisk),
      PossibleDamage: defaultData.PossibleDamage || '',
      mitigation: defaultData.mitigation || '',
      PotentialRiskScenarios: defaultData.PotentialRiskScenarios || '',
      RiskType: defaultData.RiskType || '',
      RiskCategory: defaultData.RiskCategory || '',
      RiskBusinessImpact: defaultData.RiskBusinessImpact || '',
      Criticality: defaultData.Criticality || 'Medium',
      MandatoryOptional: defaultData.MandatoryOptional || 'Mandatory',
      ManualAutomatic: defaultData.ManualAutomatic || 'Manual',
      Impact: defaultData.Impact || 5.0,
      Probability: defaultData.Probability || 5.0,
      Status: defaultData.Status,
      ComplianceVersion: defaultData.ComplianceVersion,
      reviewer: defaultData.reviewer_id || defaultData.reviewer, // Support both field names
      CreatedByName: defaultData.CreatedByName || (defaultData.reviewer_id || defaultData.reviewer).toString(),
      Applicability: defaultData.Applicability || '',
      MaturityLevel: defaultData.MaturityLevel || 'Initial',
      ActiveInactive: defaultData.ActiveInactive,
      PermanentTemporary: defaultData.PermanentTemporary || 'Permanent',
      ApprovalDueDate: defaultData.ApprovalDueDate
    };
 
    // Debug log
    console.log('Sending compliance data:', formattedData);
   
    return api.post(API_ENDPOINTS.COMPLIANCE_CREATE, formattedData).then(response => {
      console.log('Compliance create response:', response.data);
      return {
        data: {
          success: response.data.success,
          ComplianceId: response.data.compliance_id,
          Identifier: response.data.Identifier,
          version: response.data.version
        }
      };
    }).catch(error => {
      console.error('Compliance create error:', error.response?.data);
      throw error;
    });
  },
 
  // Add updateCompliance function
  updateCompliance: (complianceId, data) => {
    // Format the data similar to createCompliance
        // Always get user_id from localStorage/session and set as UserId
    let userId = localStorage.getItem('user_id') || sessionStorage.getItem('userId');
    if (!userId) {
      const userObj = localStorage.getItem('user') || sessionStorage.getItem('user');
      if (userObj) {
        try {
          const parsed = JSON.parse(userObj);
          userId = parsed.UserId || parsed.user_id || parsed.id;
        } catch (e) { /* intentionally empty */ }
      }
    }
    // Always get reviewer id from data (reviewer_id or ReviewerId)
    let reviewerId = data.reviewer_id || data.ReviewerId || data.reviewer;
    // Build mitigation object if mitigationSteps is present
    let mitigation = data.mitigation;
    if (data.mitigationSteps && Array.isArray(data.mitigationSteps)) {
      mitigation = {};
      data.mitigationSteps.forEach((step, idx) => {
        if (step.description && step.description.trim()) {
          mitigation[`${idx + 1}`] = step.description.trim();
        }
      });
    }
    // Build the payload
    const formattedData = {
      ...data,
      UserId: userId,
      ReviewerId: reviewerId,
      ComplianceTitle: data.ComplianceTitle || '',
      ComplianceItemDescription: data.ComplianceItemDescription || '',
      ComplianceType: data.ComplianceType || '',
      Scope: data.Scope || '',
      Objective: data.Objective || '',
      BusinessUnitsCovered: data.BusinessUnitsCovered || '',
      IsRisk: Boolean(data.IsRisk),
      PossibleDamage: data.PossibleDamage || '',
      mitigation: data.mitigationSteps ? data.mitigationSteps.reduce((obj, step, index) => {
        if (step.description.trim()) {
          obj[`step${index + 1}`] = step.description.trim();
        }
        return obj;
      }, {}) : {},
      PotentialRiskScenarios: data.PotentialRiskScenarios || '',
      RiskType: data.RiskType || '',
      RiskCategory: data.RiskCategory || '',
      RiskBusinessImpact: data.RiskBusinessImpact || '',
      Criticality: data.Criticality || 'Medium',
      MandatoryOptional: data.MandatoryOptional || 'Mandatory',
      ManualAutomatic: data.ManualAutomatic || 'Manual',
      Impact: data.Impact || '5.0',
      Probability: data.Probability || '5.0',
      Status: 'Under Review',
      ComplianceVersion: data.ComplianceVersion,
      reviewer: data.reviewer_id || data.reviewer,
      Applicability: data.Applicability || '',
      MaturityLevel: data.MaturityLevel || 'Initial',
      ActiveInactive: 'Active',
      PermanentTemporary: data.PermanentTemporary || 'Permanent',
      // Ensure versionType is properly capitalized (must be 'Major' or 'Minor')
      versionType: data.versionType ? 
                   (data.versionType === 'Major' || data.versionType === 'Minor' ? data.versionType :
                    data.versionType.toLowerCase() === 'major' ? 'Major' :
                    data.versionType.toLowerCase() === 'minor' ? 'Minor' : 'Minor') : 
                   'Minor', // Default to Minor if not provided
      PreviousComplianceVersionId: data.PreviousComplianceVersionId
    };
 
    // Debug log
    console.log('Updating compliance data:', formattedData);
   
    return api.put(API_ENDPOINTS.COMPLIANCE_UPDATE(complianceId), formattedData)
      .then(response => {
        console.log('Compliance update response:', response.data);
        return response;
      })
      .catch(error => {
        console.error('Compliance update error:', error.response?.data);
        throw error;
      });
  },
 
  editCompliance: (complianceId, data) => api.put(API_ENDPOINTS.COMPLIANCE_UPDATE(complianceId), data),
  cloneCompliance: (complianceId, data) => {
    console.log('Cloning compliance with ID:', complianceId, 'Data:', data);
   
    // Ensure SubPolicy is set correctly (it might be called target_subpolicy_id in the UI)
    const cloneData = { ...data };
    if (cloneData.target_subpolicy_id && !cloneData.SubPolicy) {
      cloneData.SubPolicy = cloneData.target_subpolicy_id;
    }
   
    return api.post(API_ENDPOINTS.COMPLIANCE_CLONE(complianceId), cloneData)
      .then(response => {
        console.log('Compliance clone response:', response.data);
        return response;
      })
      .catch(error => {
        console.error('Compliance clone error:', error.response?.data);
        throw error;
      });
  },
  getComplianceDashboard: (filters) => api.get(API_ENDPOINTS.COMPLIANCE_USER_DASHBOARD, { params: filters }),
  getComplianceAnalytics: (data) => api.post(API_ENDPOINTS.COMPLIANCE_KPI_ANALYTICS, data),
  getCompliancesBySubPolicy: (subPolicyId) => api.get(API_ENDPOINTS.COMPLIANCE_SUBPOLICY_COMPLIANCES(subPolicyId)),
  getComplianceById: (complianceId) => api.get(API_ENDPOINTS.COMPLIANCE_GET(complianceId)),
  toggleComplianceVersion: (complianceId) => api.post(API_ENDPOINTS.COMPLIANCE_TOGGLE_VERSION(complianceId)),
  deactivateCompliance: (complianceId, data) => api.post(API_ENDPOINTS.COMPLIANCE_DEACTIVATE(complianceId), data),
  approveComplianceDeactivation: (approvalId, data) => api.post(API_ENDPOINTS.COMPLIANCE_DEACTIVATION_APPROVE(approvalId), data),
  rejectComplianceDeactivation: (approvalId, data) => api.post(API_ENDPOINTS.COMPLIANCE_DEACTIVATION_REJECT(approvalId), data),
 
  // KPI endpoints
  getMaturityLevelKPI: (params) => api.get(API_ENDPOINTS.COMPLIANCE_MATURITY_LEVEL_KPI, { params }),
  getNonComplianceCount: (params) => api.get(API_ENDPOINTS.COMPLIANCE_NON_COMPLIANCE_COUNT, { params }),
  getMitigatedRisksCount: (params) => api.get(API_ENDPOINTS.COMPLIANCE_MITIGATED_RISKS_COUNT, { params }),
  getAutomatedControlsCount: (params) => api.get(API_ENDPOINTS.COMPLIANCE_AUTOMATED_CONTROLS_COUNT, { params }),
  getNonComplianceRepetitions: (params) => api.get(API_ENDPOINTS.COMPLIANCE_NON_COMPLIANCE_REPETITIONS, { params }),
  getComplianceKPI: (params) => api.get(API_ENDPOINTS.COMPLIANCE_KPI_DASHBOARD, { params }),
  getComplianceStatusOverview: (params) => api.get(API_ENDPOINTS.COMPLIANCE_STATUS_OVERVIEW, { params }),
  getReputationalImpact: (params) => api.get(API_ENDPOINTS.COMPLIANCE_REPUTATIONAL_IMPACT, { params }),
  getRemediationCost: (params) => api.get(API_ENDPOINTS.COMPLIANCE_REMEDIATION_COST, { params }),
  getNonCompliantIncidents: (period, params) => api.get(API_ENDPOINTS.COMPLIANCE_NON_COMPLIANT_INCIDENTS, { params: { period, ...params } }),
 
  // Compliance approval endpoints with more robust error handling
  getCompliancePolicyApprovals: (params) => api.get(API_ENDPOINTS.COMPLIANCE_POLICY_APPROVALS_REVIEWER, { params }),
  getComplianceRejectedApprovals: (reviewerId) => api.get(API_ENDPOINTS.COMPLIANCE_REJECTED_APPROVALS(reviewerId)),
  submitComplianceReview: (approvalId, data) => {
    console.log(`🚀 Submitting compliance review for approval ID ${approvalId}:`, data);
    // Use a more explicit timeout for this critical endpoint
    return api.put(API_ENDPOINTS.COMPLIANCE_APPROVALS(approvalId), data, { timeout: 20000 })
      .then(response => {
        console.log(`✅ Compliance review submission successful for approval ID ${approvalId}:`, response.data);
        return response;
      })
      .catch(error => {
        console.error(`❌ Compliance review submission failed for approval ID ${approvalId}:`, error.response?.data || error.message);
        throw error;
      });
  },
  resubmitComplianceApproval: (approvalId, data) => api.put(API_ENDPOINTS.COMPLIANCE_APPROVALS_RESUBMIT(approvalId), data),
 
  // User endpoints
  getUsers: () => api.get(API_ENDPOINTS.COMPLIANCE_USERS),
 
  getOntimeMitigationPercentage: (params) => api.get(API_ENDPOINTS.COMPLIANCE_ONTIME_MITIGATION_PERCENTAGE, { params }),
  
  // New KPI endpoints for compliance status
  getIsoFrameworkComplianceStatus: () => api.get('/compliance/kpi-dashboard/analytics/iso-framework-status/'),
  getPolicyComplianceStatus: (policyId) => api.get('/compliance/kpi-dashboard/analytics/policy-compliance-status/', { params: { policy_id: policyId } }),
};

// Event Handling Service
export const eventService = {
  // Get frameworks for event creation
  getFrameworks: () => api.get(API_ENDPOINTS.EVENTS_FRAMEWORKS),
  
  // Get modules for event creation
  getModules: () => api.get('api/events/modules/'),
  
  // Get event types by framework
  getEventTypesByFramework: (frameworkName) => api.get('api/events/event-types-by-framework/', {
    params: { framework_name: frameworkName }
  }),
  
  // Get dynamic fields for event creation based on framework and event type
  getDynamicFieldsForEvent: (frameworkName, eventTypeId, subEventTypeId = null) => api.get('api/events/dynamic-fields/', {
    params: { 
      framework_name: frameworkName,
      event_type_id: eventTypeId,
      sub_event_type_id: subEventTypeId
    }
  }),
  
  // Create new event type
  createEventType: (frameworkName, eventTypeName, eventSubtypes = null) => api.post('api/events/create-event-type/', {
    framework_name: frameworkName,
    event_type_name: eventTypeName,
    event_subtypes: eventSubtypes
  }),
  
  // Update event type sub-types
  updateEventTypeSubtypes: (eventTypeId, eventSubtypes) => api.put(`api/events/update-event-type-subtypes/${eventTypeId}/`, {
    event_subtypes: eventSubtypes
  }),
  
  // Create new module
  createModule: (moduleName) => api.post('api/events/create-module/', {
    module_name: moduleName
  }),
  
  // Get records by module type
  getRecordsByModule: (frameworkId, module) => api.get(API_ENDPOINTS.EVENTS_RECORDS, {
    params: { framework_id: frameworkId, module: module }
  }),
  
  // Get event templates
  getTemplates: () => api.get(API_ENDPOINTS.EVENTS_TEMPLATES),
  
  // Create new event
  createEvent: (eventData) => api.post(API_ENDPOINTS.EVENTS_CREATE, eventData),
  
  // Get events list
  getEventsList: () => api.get(API_ENDPOINTS.EVENTS_LIST),
  
  // Get user event permissions
  getUserEventPermissions: () => api.get('api/events/permissions/'),
  
  // Get event details
  getEventDetails: (eventId) => api.get(API_ENDPOINTS.EVENT_DETAILS(eventId)),
  
  // Get current user information
  getCurrentUser: (userId) => api.get('api/events/current-user/', {
    params: { user_id: userId }
  }),
  
  // Get users for reviewer selection (all users except current user)
  getUsersForReviewer: (userId) => api.get('api/events/users-for-reviewer/', {
    params: { user_id: userId }
  }),
  
  // Get all users from database
  getUsers: () => api.get('api/users/'),
  
  // Get events for calendar (recurring events only)
  getEventsForCalendar: () => api.get(API_ENDPOINTS.EVENTS_CALENDAR),
  
  // Get events dashboard data
  getEventsDashboard: (queryString = '') => {
    const url = queryString ? `${API_ENDPOINTS.EVENTS_DASHBOARD}?${queryString}` : API_ENDPOINTS.EVENTS_DASHBOARD
    return api.get(url)
  },
  
  // Approve event
  approveEvent: (eventId, data) => api.post(`api/events/${eventId}/approve/`, data),
  
  // Reject event
  rejectEvent: (eventId, data) => api.post(`api/events/${eventId}/reject/`, data),
  
  // Create events table if it doesn't exist
  createEventsTable: () => api.post('api/events/create-table/'),
  
  // Get RiskaVaire events for the queue
  getRiskaVaireEvents: () => api.get('api/riskavaire/events/'),
  
  // Update event
  updateEvent: (eventId, data) => api.put(`api/events/${eventId}/update/`, data),
  
  // Archive event
  archiveEvent: (eventId, data) => api.post(`api/events/${eventId}/archive/`, data),
  
  // Attach evidence to event
  attachEvidence: (eventId, formData) => api.post(`api/events/${eventId}/attach-evidence/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }),
  
  // Get archived events
  getArchivedEvents: () => api.get('api/events/archived/'),
  
  // Get archived queue items (integration and Riskavaire events)
  getArchivedQueueItems: () => api.get('api/events/archived-queue-items/'),
  
  // Unarchive an event
  unarchiveEvent: (eventId, userId) => api.post(`api/events/${eventId}/unarchive/`, { user_id: userId }),
  
  // Delete an event permanently
  deleteEventPermanently: (eventId, userId) => api.post(`api/events/${eventId}/delete-permanently/`, { user_id: userId }),
  
  // Get integration events (Jira, etc.)
  getIntegrationEvents: () => api.get('api/events/integration-events/'),
  
  // Create event from integration item
  createEventFromIntegration: (data) => api.post('api/events/create-from-integration/', data),
  
  // Get file operations for document handling
  getFileOperations: (params = {}) => api.get('api/file-operations/', { params }),
  
  // Get all events (general method)
  getEvents: (params = {}) => api.get('api/events/', { params }),
  
  // Get document handling events
  getDocumentHandlingEvents: (params = {}) => api.get('api/events/document-handling/', { params })
};

// S3 Upload Service
export const s3Service = {
  // Upload file to S3 via microservice
  uploadFile: (file, userId, customFileName = null) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);
    if (customFileName) {
      formData.append('custom_file_name', customFileName);
    }
    
    return api.post('/api/s3/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 60000 // 60 seconds timeout for file uploads
    });
  },
  
  // Download file from S3
  downloadFile: (s3Key, fileName, userId) => {
    return api.get(`/api/s3/download/${s3Key}/${fileName}/`, {
      params: { user_id: userId },
      responseType: 'blob'
    });
  },
  
  // Test S3 connection
  testConnection: () => api.get('/api/s3/test-connection/')
};
 
export default api;