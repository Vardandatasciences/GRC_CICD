// API Configuration - Centralized URL Management
// Change this variable to switch between different environments
 
// Environment Configuration
const ENVIRONMENT = 'development'; 
// Options: 'aws', 'local', 'development'
 
// API Base URLs for different environments
const API_URLS = {
  // aws: 'https://grc-backend.vardaands.com',
  aws: 'https://grc-backend.vardaands.com',
  local: 'http://localhost:8000',
  development: 'http://127.0.0.1:8000'
};
 
// Get the current API base URL based on environment
export const API_BASE_URL = API_URLS[ENVIRONMENT] || API_URLS.aws;
 
// API endpoints with base URL
export const API_ENDPOINTS = {
  // Authentication
  LOGIN: `${API_BASE_URL}/api/login/`,
  LOGOUT: `${API_BASE_URL}/api/logout/`,
  SEND_OTP: `${API_BASE_URL}/api/send-otp/`,
  VERIFY_OTP: `${API_BASE_URL}/api/verify-otp/`,
  RESET_PASSWORD: `${API_BASE_URL}/api/reset-password/`,
  GET_USER_EMAIL: `${API_BASE_URL}/api/get-user-email/`,
  TEST_SESSION_AUTH: `${API_BASE_URL}/api/test-session-auth/`,
 
  // User Management
  USER_PROFILE: (userId) => `${API_BASE_URL}/api/user-profile/${userId}/`,
  USER_BUSINESS_INFO: (userId) => `${API_BASE_URL}/api/user-business-info/${userId}/`,
  USER_PERMISSIONS: (userId) => `${API_BASE_URL}/api/user-permissions/${userId}/`,
  USER_ROLE: `${API_BASE_URL}/api/user-role/`,
  USERS_FOR_DROPDOWN: `${API_BASE_URL}/api/rbac/users-for-dropdown/`,
  USERS_FOR_REVIEWER_SELECTION: `${API_BASE_URL}/api/users-for-reviewer-selection/`,
 
  // Notifications - FIXED: Proper function implementation
  GET_NOTIFICATIONS: (userId = null) => {
    const user = userId || localStorage.getItem('user_id') || 'default_user';
    return `${API_BASE_URL}/api/get-notifications/?user_id=${user}`;
  },
  MARK_AS_READ: `${API_BASE_URL}/api/mark-as-read/`,
  MARK_ALL_AS_READ: `${API_BASE_URL}/api/mark-all-as-read/`,
  PUSH_NOTIFICATION: `${API_BASE_URL}/api/push-notification/`,
 
  // Policy Management
  POLICIES: `${API_BASE_URL}/api/policies/`,
  POLICY: (policyId) => `${API_BASE_URL}/api/policies/${policyId}/`,
  HOME_POLICIES_BY_STATUS: `${API_BASE_URL}/api/home/policies-by-status/`,
  HOME_POLICIES_BY_STATUS_PUBLIC: () => `${API_BASE_URL}/api/home/policies-by-status-public/`,
  HOME_POLICY_DETAILS: (policyId) => `${API_BASE_URL}/api/home/policy-details/${policyId}/`,
  HOMEPAGE_DATA: (frameworkId = null) => `${API_BASE_URL}/api/homepage/${frameworkId ? `?frameworkId=${frameworkId}` : ''}`,
  HOMEPAGE_ALL_FRAMEWORKS: `${API_BASE_URL}/api/homepage/all-frameworks/`,
  POLICY_CATEGORIES_SAVE: `${API_BASE_URL}/api/policy-categories/save/`,
  POLICY_VERSION: (policyId) => `${API_BASE_URL}/api/policies/${policyId}/version/`,
  POLICY_REVIEWER_VERSION: (policyId) => `${API_BASE_URL}/api/policies/${policyId}/reviewer-version/`,
  POLICY_APPROVALS: `${API_BASE_URL}/api/policy-approvals/`,
  POLICY_APPROVALS_USER: (userId) => `${API_BASE_URL}/api/policy-approvals/user/${userId}/`,
  POLICY_APPROVALS_REVIEWER: (userId) => `${API_BASE_URL}/api/policy-approvals/reviewer/${userId}/`,
  POLICY_APPROVALS_REJECTED: (userId) => `${API_BASE_URL}/api/policy-approvals/rejected/${userId}/`,
  POLICY_APPROVALS_LATEST: (policyId) => `${API_BASE_URL}/api/policy-approvals/latest/${policyId}/`,
  POLICY_SUBMIT_REVIEW: (policyId) => `${API_BASE_URL}/api/policies/${policyId}/submit-review/`,
  POLICY_RESUBMIT_APPROVAL: (policyId) => `${API_BASE_URL}/api/policies/${policyId}/resubmit-approval/`,
  POLICY_DEBUG_STATUS: (policyId) => `${API_BASE_URL}/api/policies/${policyId}/debug-status/`,
  POLICY_REVIEW_HISTORY: (policyId) => `${API_BASE_URL}/api/policies/${policyId}/review-history/`,
  ACKNOWLEDGE_POLICY: (policyId) => `${API_BASE_URL}/api/acknowledge-policy/${policyId}/`,
  POLICY_COMPLIANCE_STATS: (policyId) => `${API_BASE_URL}/api/policies/${policyId}/compliance-stats/`,
  FRAMEWORK_COMPLIANCE_STATS: (frameworkId) => `${API_BASE_URL}/api/frameworks/${frameworkId}/compliance-stats/`,

  // Policy Acknowledgement System
  CREATE_ACKNOWLEDGEMENT_REQUEST: `${API_BASE_URL}/api/policy-acknowledgements/create/`,
  GET_POLICY_ACKNOWLEDGEMENT_REQUESTS: (policyId) => `${API_BASE_URL}/api/policy-acknowledgements/policy/${policyId}/`,
  GET_USER_PENDING_ACKNOWLEDGEMENTS: `${API_BASE_URL}/api/policy-acknowledgements/user/pending/`,
  ACKNOWLEDGE_POLICY_NEW: (acknowledgementUserId) => `${API_BASE_URL}/api/policy-acknowledgements/acknowledge/${acknowledgementUserId}/`,
  GET_ACKNOWLEDGEMENT_REPORT: (acknowledgementRequestId) => `${API_BASE_URL}/api/policy-acknowledgements/report/${acknowledgementRequestId}/`,
  GET_USERS_FOR_ACKNOWLEDGEMENT: `${API_BASE_URL}/api/policy-acknowledgements/users/`,
  CANCEL_ACKNOWLEDGEMENT_REQUEST: (acknowledgementRequestId) => `${API_BASE_URL}/api/policy-acknowledgements/cancel/${acknowledgementRequestId}/`,
  
  // Public Policy Acknowledgement (no authentication required)
  GET_ACKNOWLEDGEMENT_BY_TOKEN: (token) => `${API_BASE_URL}/api/policy-acknowledgements/public/${token}/`,
  ACKNOWLEDGE_POLICY_BY_TOKEN: (token) => `${API_BASE_URL}/api/policy-acknowledgements/public/${token}/acknowledge/`,
  GET_POLICY_DOCUMENT_BY_TOKEN: (token) => `${API_BASE_URL}/api/policy-acknowledgements/public/${token}/document/`,
 
  // Subpolicies
  SUBPOLICIES: (subpolicyId) => `${API_BASE_URL}/api/subpolicies/${subpolicyId}/`,
  SUBPOLICY_VERSION: (subpolicyId) => `${API_BASE_URL}/api/subpolicies/${subpolicyId}/version/`,
  SUBPOLICY_REVIEWER_VERSION: (subpolicyId) => `${API_BASE_URL}/api/subpolicies/${subpolicyId}/reviewer-version/`,
  SUBPOLICY_REJECT: (subpolicyId) => `${API_BASE_URL}/api/subpolicies/${subpolicyId}/reject/`,
  SUBPOLICY_RESUBMIT: (subpolicyId) => `${API_BASE_URL}/api/subpolicies/${subpolicyId}/resubmit/`,
  SUBPOLICY_REVIEW: (subpolicyId) => `${API_BASE_URL}/api/subpolicies/${subpolicyId}/review/`,
 
  // Framework Management
  FRAMEWORK_EXPLORER: `${API_BASE_URL}/api/framework-explorer/`,
  FRAMEWORK_DETAILS: (frameworkId) => `${API_BASE_URL}/api/frameworks/${frameworkId}/details/`,
  FRAMEWORK_POLICY_COUNTS: (frameworkId) => `${API_BASE_URL}/api/frameworks/${frameworkId}/policy-counts/`,
  FRAMEWORK_TOGGLE_STATUS: (frameworkId) => `${API_BASE_URL}/api/frameworks/${frameworkId}/toggle-status/`,
  FRAMEWORK_REQUEST_STATUS_CHANGE: (frameworkId) => `${API_BASE_URL}/api/frameworks/${frameworkId}/request-status-change/`,
  FRAMEWORKS_EXPORT_ALL: `${API_BASE_URL}/api/frameworks/export-all/`,
  POLICY_ALL_POLICIES_FRAMEWORKS: `${API_BASE_URL}/api/all-policies/frameworks/`,
  POLICY_FRAMEWORK_VERSIONS: (frameworkId) => `${API_BASE_URL}/api/all-policies/frameworks/${frameworkId}/versions/`,
  POLICY_FRAMEWORK_VERSION_POLICIES: (versionId) => `${API_BASE_URL}/api/all-policies/framework-versions/${versionId}/policies/`,
  FRAMEWORK_ADD_POLICIES: (frameworkId) => `${API_BASE_URL}/api/frameworks/${frameworkId}/policies/`,
  POLICY_VERSION_SUBPOLICIES: (versionId) => `${API_BASE_URL}/api/all-policies/policy-versions/${versionId}/subpolicies/`,
 
  UPLOAD_FRAMEWORK: `${API_BASE_URL}/api/upload-framework/`,
  CREATE_CHECKED_STRUCTURE: `${API_BASE_URL}/api/create-checked-structure/`,
  SAVE_SINGLE_POLICY: `${API_BASE_URL}/api/save-single-policy/`,
  SAVE_POLICIES: `${API_BASE_URL}/api/save-policies/`,
  SAVE_COMPLETE_POLICY_PACKAGE: `${API_BASE_URL}/api/save-complete-policy-package/`,
  SAVE_FRAMEWORK_TO_DATABASE: `${API_BASE_URL}/api/save-framework-to-database/`,
  SAVE_CHECKED_SECTIONS_JSON: `${API_BASE_URL}/api/save-checked-sections-json/`,
  GENERATE_COMPLIANCES_FOR_CHECKED_SECTIONS: `${API_BASE_URL}/api/generate-compliances-for-checked-sections/`,
  GET_CHECKED_SECTIONS_WITH_COMPLIANCE: `${API_BASE_URL}/api/get-checked-sections-with-compliance/`,
  SAVE_EDITED_FRAMEWORK_TO_DATABASE: `${API_BASE_URL}/api/save-edited-framework-to-database/`,
 
  // ========================================================================
  // AI-POWERED UPLOAD FRAMEWORK - NEW API (Primary - Use These)
  // ========================================================================
  AI_UPLOAD_PDF: `${API_BASE_URL}/api/ai-upload/upload-pdf/`,
  AI_START_PROCESSING: `${API_BASE_URL}/api/ai-upload/start-processing/`,
  AI_GET_STATUS: (taskId) => `${API_BASE_URL}/api/ai-upload/status/${taskId}/`,
  AI_GET_DATA: (userid) => `${API_BASE_URL}/api/ai-upload/data/${userid}/`,
  AI_LIST_FOLDERS: `${API_BASE_URL}/api/ai-upload/list-folders/`,
  
  // Default data loader from TEMP_MEDIA_ROOT
  AI_LOAD_DEFAULT_DATA: `${API_BASE_URL}/api/ai-upload/load-default-data/`,
  AI_DEFAULT_SECTIONS: (userId) => `${API_BASE_URL}/api/ai-upload/default-sections/${userId}/`,
  AI_DEFAULT_PDF: (sectionFolder, controlId) => `${API_BASE_URL}/api/ai-upload/default-pdf/${sectionFolder}/${controlId}/`,
  AI_GET_POLICIES_FOR_SECTION: (sectionFolder) => `${API_BASE_URL}/api/ai-upload/policies/${sectionFolder}/`,
  AI_GET_SUBPOLICIES_FOR_POLICY: (sectionFolder, policyId) => `${API_BASE_URL}/api/ai-upload/subpolicies/${sectionFolder}/${policyId}/`,
  
  // ========================================================================
  // Framework Upload and Processing (Legacy - Kept for backward compatibility)
  // ========================================================================
  FRAMEWORK_UPLOAD: `${API_BASE_URL}/api/upload-framework/`,
  FRAMEWORK_LOAD_DEFAULT_DATA: `${API_BASE_URL}/api/load-default-data/`,
  FRAMEWORK_PROCESSING_STATUS: (taskId) => `${API_BASE_URL}/api/processing-status/${taskId}/`,
  FRAMEWORK_GET_SECTIONS: (taskId) => `${API_BASE_URL}/api/get-sections/${taskId}/`,
  FRAMEWORK_GET_SECTIONS_BY_USER: (userid) => `${API_BASE_URL}/api/get-sections-by-user/${userid}/`,
  FRAMEWORK_LIST_USER_FOLDERS: `${API_BASE_URL}/api/list-user-folders/`,
  
  // Checked Sections Management
  CHECKED_SECTIONS_SAVE: `${API_BASE_URL}/api/checked-sections/save-selected-sections/`,
  CHECKED_SECTIONS_GET: (userId) => `${API_BASE_URL}/api/checked-sections/get-checked-sections/${userId}/`,
  CHECKED_SECTIONS_DELETE: (userId) => `${API_BASE_URL}/api/checked-sections/delete-checked-sections/${userId}/`,
  CHECKED_SECTIONS_PROCESS_PDFS: `${API_BASE_URL}/api/checked-sections/process-pdfs/`,
  CHECKED_SECTIONS_GET_FORM_DATA: `${API_BASE_URL}/api/checked-sections/get-extracted-policies-form-data/`,
  CHECKED_SECTIONS_PDF: (userId, sectionFolder, controlId) => `${API_BASE_URL}/api/checked-sections/pdf/${userId}/${sectionFolder}/${controlId}/`,
 
  // Policy Documents
  UPLOAD_POLICY_DOCUMENT: `${API_BASE_URL}/api/upload-policy-document/`,
 
  // Status Change Requests
  FRAMEWORK_STATUS_CHANGE_REQUESTS: `${API_BASE_URL}/api/framework-status-change-requests/`,
  FRAMEWORK_STATUS_CHANGE_REQUESTS_USER: (userId) => `${API_BASE_URL}/api/framework-status-change-requests/user/${userId}/`,
  FRAMEWORK_STATUS_CHANGE_REQUESTS_REVIEWER: (userId) => `${API_BASE_URL}/api/framework-status-change-requests/reviewer/${userId}/`,
  POLICY_STATUS_CHANGE_REQUESTS: `${API_BASE_URL}/api/policy-status-change-requests/`,
  POLICY_STATUS_CHANGE_REQUESTS_USER: (userId) => `${API_BASE_URL}/api/policy-status-change-requests/user/${userId}/`,
  POLICY_STATUS_CHANGE_REQUESTS_REVIEWER: (userId) => `${API_BASE_URL}/api/policy-status-change-requests/reviewer/${userId}/`,
 
  // Policy Categories
  POLICY_CATEGORIES: `${API_BASE_URL}/api/policy-categories/`,
  
  // Tailoring & Templating
  TAILORING_CREATE_FRAMEWORK: `${API_BASE_URL}/api/tailoring/create-framework/`,
  TAILORING_CREATE_POLICY: `${API_BASE_URL}/api/tailoring/create-policy/`,
 
  // Frameworks
  FRAMEWORKS: `${API_BASE_URL}/api/frameworks/`,
  FRAMEWORK_GET_POLICIES: (frameworkId) => `${API_BASE_URL}/api/frameworks/${frameworkId}/get-policies/`,
  FRAMEWORK_GET_POLICIES_LIST: (frameworkId) => `${API_BASE_URL}/api/frameworks/${frameworkId}/policies-list/`,
  FRAMEWORKS_APPROVED_ACTIVE: `${API_BASE_URL}/api/frameworks/approved-active/`,
  FRAMEWORK_SET_SELECTED: `${API_BASE_URL}/api/frameworks/set-selected/`,
  FRAMEWORK_GET_SELECTED: `${API_BASE_URL}/api/frameworks/get-selected/`,
  
  // Audit Frameworks (for audit assignment)
  AUDIT_FRAMEWORKS: `${API_BASE_URL}/api/audit/frameworks/`,
  AUDIT_POLICIES: `${API_BASE_URL}/api/audit/policies/`,
  AUDIT_SUBPOLICIES: `${API_BASE_URL}/api/audit/subpolicies/`,
  FRAMEWORK_SUBMIT_REVIEW: (frameworkId) => `${API_BASE_URL}/api/frameworks/${frameworkId}/submit-review/`,
  FRAMEWORK_RESUBMIT_APPROVAL: (frameworkId) => `${API_BASE_URL}/api/frameworks/${frameworkId}/resubmit-approval/`,
  FRAMEWORK_APPROVE_FINAL: (frameworkId) => `${API_BASE_URL}/api/frameworks/${frameworkId}/approve-final/`,
  FRAMEWORKS_REJECTED: `${API_BASE_URL}/api/frameworks/rejected/`,
 
  // Framework Approvals
  FRAMEWORK_APPROVALS: `${API_BASE_URL}/api/frameworks/approvals/`,  // Get all framework approvals
  FRAMEWORK_APPROVALS_USER: (userId) => `${API_BASE_URL}/api/framework-approvals/user/${userId}/`,  // Frameworks created by user
  FRAMEWORK_APPROVALS_REVIEWER: (userId) => `${API_BASE_URL}/api/framework-approvals/reviewer/${userId}/`,  // Frameworks where user is reviewer
  FRAMEWORK_APPROVALS_LATEST: (frameworkId) => `${API_BASE_URL}/api/framework-approvals/latest/${frameworkId}/`,
 
  // Framework Policy Approvals
  FRAMEWORK_POLICY_APPROVE_REJECT: (frameworkId, policyId) => `${API_BASE_URL}/api/frameworks/${frameworkId}/policies/${policyId}/approve-reject/`,
  FRAMEWORK_POLICY_SUBPOLICY_APPROVE_REJECT: (frameworkId, policyId, subpolicyId) => `${API_BASE_URL}/api/frameworks/${frameworkId}/policies/${policyId}/subpolicies/${subpolicyId}/approve-reject/`,
 
  // Policy Subpolicies
  POLICY_GET_SUBPOLICIES: (policyId) => `${API_BASE_URL}/api/policies/${policyId}/get-subpolicies/`,
  POLICY_DETAILS: (policyId) => `${API_BASE_URL}/api/policies/${policyId}/details/`,
 
  // Policy Users
  POLICY_USERS: `${API_BASE_URL}/api/policy-users/`,
 
  // Departments
  DEPARTMENTS: `${API_BASE_URL}/api/departments/`,
 
  // Compliance
  // Correct paths for compliance approvals (match backend routes in grc.urls)
  COMPLIANCE_APPROVALS: (approvalId) => `${API_BASE_URL}/api/compliance/compliance-approvals/${approvalId}/review/`,
  COMPLIANCE_APPROVALS_RESUBMIT: (approvalId) => `${API_BASE_URL}/api/compliance/compliance-approvals/resubmit/${approvalId}/`,
 
  // Compliance Management - Complete set of endpoints
  COMPLIANCE_FRAMEWORKS: `${API_BASE_URL}/api/compliance/frameworks/`,
  COMPLIANCE_POLICIES: (frameworkId) => `${API_BASE_URL}/api/compliance/frameworks/${frameworkId}/policies/list/`,
  COMPLIANCE_SUBPOLICIES: (policyId) => `${API_BASE_URL}/api/compliance/policies/${policyId}/subpolicies/`,
  COMPLIANCE_SUBPOLICY_COMPLIANCES: (subpolicyId) => `${API_BASE_URL}/api/compliance/all-policies/subpolicies/${subpolicyId}/compliances/`,
  COMPLIANCE_VIEW_BY_TYPE: (type, id) => `${API_BASE_URL}/api/compliance/view/${type}/${id}/`,
 
  // Compliance CRUD operations
  COMPLIANCE_CREATE: `${API_BASE_URL}/api/compliance-create/`,
  COMPLIANCE_GET: (complianceId) => `${API_BASE_URL}/api/compliance/${complianceId}/`,
  COMPLIANCE_UPDATE: (complianceId) => `${API_BASE_URL}/api/compliance_edit/${complianceId}/edit/`,
  COMPLIANCE_CLONE: (complianceId) => `${API_BASE_URL}/api/clone-compliance/${complianceId}/clone/`,
  COMPLIANCE_DELETE: (complianceId) => `${API_BASE_URL}/api/compliance/${complianceId}/`,
 
  // Compliance versioning and status
  // Use the canonical toggle-version endpoint exposed by the backend
  COMPLIANCE_TOGGLE_VERSION: (complianceId) => `${API_BASE_URL}/api/compliance/${complianceId}/toggle-version/`,
  COMPLIANCE_DEACTIVATE: (complianceId) => `${API_BASE_URL}/api/compliance/${complianceId}/deactivate/`,
  COMPLIANCE_DEACTIVATION_APPROVE: (approvalId) => `${API_BASE_URL}/api/compliance/deactivation/${approvalId}/approve/`,
  COMPLIANCE_DEACTIVATION_REJECT: (approvalId) => `${API_BASE_URL}/api/compliance/deactivation/${approvalId}/reject/`,
 
  // Compliance dashboard and analytics
  COMPLIANCE_USER_DASHBOARD: `${API_BASE_URL}/api/compliance/dashboard-with-filters/`,
  COMPLIANCE_KPI_DASHBOARD: `${API_BASE_URL}/api/compliance/kpi-dashboard/`,
  COMPLIANCE_KPI_ANALYTICS: `${API_BASE_URL}/api/compliance/kpi-dashboard/analytics/`,
  COMPLIANCE_MATURITY_LEVEL_KPI: `${API_BASE_URL}/api/compliance/kpi-dashboard/analytics/maturity-level/`,
  COMPLIANCE_NON_COMPLIANCE_COUNT: `${API_BASE_URL}/api/compliance/kpi-dashboard/analytics/non-compliance-count/`,
  COMPLIANCE_MITIGATED_RISKS_COUNT: `${API_BASE_URL}/api/compliance/kpi-dashboard/analytics/mitigated-risks-count/`,
  COMPLIANCE_AUTOMATED_CONTROLS_COUNT: `${API_BASE_URL}/api/compliance/kpi-dashboard/analytics/automated-controls-count/`,
  COMPLIANCE_NON_COMPLIANCE_REPETITIONS: `${API_BASE_URL}/api/compliance/kpi-dashboard/analytics/non-compliance-repetitions/`,
  COMPLIANCE_STATUS_OVERVIEW: `${API_BASE_URL}/api/compliance/kpi-dashboard/analytics/status-overview/`,
  COMPLIANCE_REPUTATIONAL_IMPACT: `${API_BASE_URL}/api/compliance/kpi-dashboard/analytics/reputational-impact/`,
  COMPLIANCE_REMEDIATION_COST: `${API_BASE_URL}/api/compliance/kpi-dashboard/analytics/remediation-cost/`,
  COMPLIANCE_NON_COMPLIANT_INCIDENTS: `${API_BASE_URL}/api/compliance/kpi-dashboard/analytics/non-compliant-incidents/`,
  COMPLIANCE_ONTIME_MITIGATION_PERCENTAGE: `${API_BASE_URL}/api/compliance/kpi-dashboard/analytics/ontime-mitigation/`,
 
  // Compliance approvals
  COMPLIANCE_POLICY_APPROVALS_REVIEWER: `${API_BASE_URL}/api/compliance/policy-approvals-compliance/reviewer/`,
  COMPLIANCE_REJECTED_APPROVALS: (reviewerId) => `${API_BASE_URL}/api/compliance/policy-approvals-compliance/rejected/${reviewerId}/`,
  COMPLIANCE_APPROVALS_USER: (userId) => `${API_BASE_URL}/api/compliance-approvals/user/${userId}/`,
  COMPLIANCE_APPROVALS_REVIEWER: (userId) => `${API_BASE_URL}/api/compliance-approvals/reviewer/${userId}/`,
 
  // Compliance audit
  COMPLIANCE_AUDIT_INFO: (complianceId) => `${API_BASE_URL}/api/compliance/compliance/${complianceId}/audit-info/`,
 
  // Compliance export
  COMPLIANCE_EXPORT: `${API_BASE_URL}/api/compliance/export/`,
  // EXPORT_COMPLIANCE_MANAGEMENT: `${API_BASE_URL}/api/export/compliance-management/`,
  EXPORT_COMPLIANCE_MANAGEMENT: `${API_BASE_URL}/api/export-compliance-register/`,
 
  // Category Business Units
  CATEGORY_BUSINESS_UNITS: `${API_BASE_URL}/api/category-business-units/`,
  CATEGORY_BUSINESS_UNITS_ADD: `${API_BASE_URL}/api/category-business-units/add/`,
 
  // Compliance users
  COMPLIANCE_USERS: `${API_BASE_URL}/api/compliance-users/`,
 
  // Legacy endpoints (keeping for backward compatibility)
  COMPLIANCE_EDIT: (id) => `${API_BASE_URL}/compliance_edit/${id}/edit/`,
  COMPLIANCE_CLONE_LEGACY: (id) => `${API_BASE_URL}/compliance/${id}/clone/`,
  COMPLIANCE_DASHBOARD_LEGACY: `${API_BASE_URL}/compliance/dashboard/`,
  COMPLIANCE_ALL_POLICIES_FRAMEWORKS: `${API_BASE_URL}/api/compliance/all-policies/frameworks/`,
  COMPLIANCE_ALL_POLICIES_POLICIES: `${API_BASE_URL}/api/compliance/all-policies/policies/`,
  COMPLIANCE_ALL_POLICIES_SUBPOLICIES: `${API_BASE_URL}/api/compliance/all-policies/subpolicies/`,
 
  // Audit Reports (corrected paths)
  AUDIT_REPORTS_CHECK: `${API_BASE_URL}/api/audit-reports/check/`,
  AUDIT_REPORTS_DETAILS: `${API_BASE_URL}/api/audit-reports/details/`,
 
  // Entities
  ENTITIES: `${API_BASE_URL}/api/entities/`,
  DEPARTMENTS_SAVE: `${API_BASE_URL}/api/departments/save/`,
 
  // KPI and Dashboard
  POLICY_KPIS: `${API_BASE_URL}/api/policy-kpis/`,
 
  // Risk Management
  RISK_INSTANCES: `${API_BASE_URL}/api/risk-instances/`,
  RISK_INSTANCE: (instanceId) => `${API_BASE_URL}/api/risk-instances/${instanceId}/`,
  CREATE_RISK_INSTANCE: `${API_BASE_URL}/api/create-risk-instance/`,
  RISKS: `${API_BASE_URL}/api/risks/`,
  RISKS_FOR_DROPDOWN: `${API_BASE_URL}/api/risks-for-dropdown/`,
  RISK: (riskId) => `${API_BASE_URL}/api/risks/${riskId}/`,
  RISK_VERSION: (riskId, version) => `${API_BASE_URL}/api/risk/${riskId}/version/${version}/`,
  RISK_VERSIONS: (riskId) => `${API_BASE_URL}/api/risk/${riskId}/versions/`,
  RISK_MITIGATIONS: (riskId) => `${API_BASE_URL}/api/risk-mitigations/${riskId}/`,
  RISK_FORM_DETAILS: (riskId) => `${API_BASE_URL}/api/risk-form-details/${riskId}/`,
  RISK_ASSIGN: `${API_BASE_URL}/api/risk-assign/`,
  ASSIGN_REVIEWER: `${API_BASE_URL}/api/assign-reviewer/`,
  COMPLETE_REVIEW: `${API_BASE_URL}/api/complete-review/`,
  REVIEWER_COMMENTS: (riskId) => `${API_BASE_URL}/api/reviewer-comments/${riskId}/`,
  GET_ASSIGNED_REVIEWER: (riskId) => `${API_BASE_URL}/api/get-assigned-reviewer/${riskId}/`,
  LATEST_REVIEW: (riskId) => `${API_BASE_URL}/api/latest-review/${riskId}/`,
  UPDATE_MITIGATION_STATUS: `${API_BASE_URL}/api/update-mitigation-status/`,
  USER_RISKS: (userId) => `${API_BASE_URL}/api/user-risks/${userId}/`,
  REVIEWER_TASKS: (userId) => `${API_BASE_URL}/api/reviewer-tasks/${userId}/`,
  BUSINESS_IMPACTS: `${API_BASE_URL}/api/business-impacts/`,
  ADD_BUSINESS_IMPACT: `${API_BASE_URL}/api/business-impacts/add/`,
  RISK_CATEGORIES: `${API_BASE_URL}/api/risk-categories/`,
  ADD_RISK_CATEGORY: `${API_BASE_URL}/api/risk-categories/add/`,
  CUSTOM_USERS: `${API_BASE_URL}/api/custom-users/`,
  ANALYZE_INCIDENT: `${API_BASE_URL}/api/analyze-incident/`,
  COMPLIANCES_FOR_DROPDOWN: (query = '') => `${API_BASE_URL}/api/compliances-for-dropdown/${query}`,
  ALL_COMPLIANCES_FOR_DROPDOWN: `${API_BASE_URL}/api/compliances-for-dropdown/`,
 
  // Risk Dashboard and Analytics
  RISK_METRICS: (params = '') => `${API_BASE_URL}/api/risk/metrics${params ? `?${params}` : ''}`,
  RISK_CATEGORIES_DROPDOWN: `${API_BASE_URL}/api/risk/categories-for-dropdown/`,
  RISK_METRICS_BY_CATEGORY: (params = '') => `${API_BASE_URL}/api/risk/metrics-by-category${params ? `?${params}` : ''}`,
  RISK_TREND_OVER_TIME: (params = '') => `${API_BASE_URL}/api/risk/trend-over-time/${params ? `?${params}` : ''}`,
  RISK_IDENTIFICATION_RATE: (params = '') => `${API_BASE_URL}/api/risk/identification-rate${params ? `?${params}` : ''}`,
  RISK_MITIGATION_COMPLETION_RATE: (params = '') => `${API_BASE_URL}/api/risk/mitigation-completion-rate${params ? `?${params}` : ''}`,
  RISK_HEATMAP: `${API_BASE_URL}/api/risk/heatmap/`,
  RISK_BY_HEATMAP_COORDINATES: (impact, likelihood) => `${API_BASE_URL}/api/risk/heatmap/coordinates/${impact}/${likelihood}/`,
  RISK_CUSTOM_ANALYSIS: (params = '') => `${API_BASE_URL}/api/risk/custom-analysis/${params ? `?${params}` : ''}`,
  RISK_BY_CATEGORY: (category, params = '') => `${API_BASE_URL}/api/risk/by-category/${category}${params ? `?${params}` : ''}`,
 
  // Risk KPI and Performance
  RISK_KPI_DATA: `${API_BASE_URL}/api/risk/kpi-data/`,
  RISK_ACTIVE_RISKS_KPI: `${API_BASE_URL}/api/risk/active-risks-kpi/`,
  RISK_EXPOSURE_TREND: `${API_BASE_URL}/api/risk/exposure-trend/`,
  RISK_REDUCTION_TREND: `${API_BASE_URL}/api/risk/reduction-trend/`,
  RISK_HIGH_CRITICALITY: `${API_BASE_URL}/api/risk/high-criticality/`,
  RISK_MITIGATION_COMPLETION_RATE_KPI: `${API_BASE_URL}/api/risk/mitigation-completion-rate/`,
  RISK_AVG_REMEDIATION_TIME: `${API_BASE_URL}/api/risk/avg-remediation-time/`,
  RISK_RECURRENCE_RATE: `${API_BASE_URL}/api/risk/recurrence-rate/`,
  RISK_AVG_INCIDENT_RESPONSE_TIME: `${API_BASE_URL}/api/risk/avg-incident-response-time/`,
  RISK_CLASSIFICATION_ACCURACY: `${API_BASE_URL}/api/risk/classification-accuracy/`,
  RISK_SEVERITY: `${API_BASE_URL}/api/risk/severity/`,
  RISK_EXPOSURE_SCORE: `${API_BASE_URL}/api/risk/exposure-score/`,
  RISK_ASSESSMENT_FREQUENCY: `${API_BASE_URL}/api/risk/assessment-frequency/`,
  RISK_ASSESSMENT_CONSENSUS: `${API_BASE_URL}/api/risk/assessment-consensus/`,
  RISK_IDENTIFICATION_RATE_KPI: (params = '') => `${API_BASE_URL}/api/risk/identification-rate/${params ? `?${params}` : ''}`,
 
  // Risk Workflow and Evidence
  UPLOAD_RISK_EVIDENCE: `${API_BASE_URL}/api/upload-risk-evidence/`,
  DELETE_RISK_EVIDENCE: (fileId) => `${API_BASE_URL}/api/delete-risk-evidence/${fileId}/`,
 
  // Risk Export
  EXPORT_RISK_REGISTER: `${API_BASE_URL}/api/export-risk-register/`,
  
  // Risk Departments and Business Units
  RISK_DEPARTMENTS: `${API_BASE_URL}/api/risk-departments/`,
  RISK_BUSINESS_UNITS: `${API_BASE_URL}/api/risk-business-units/`,
  
  // Risk Scoring endpoints
  RISK_SCORING_INCIDENT_NAMES: `${API_BASE_URL}/api/risk-scoring/incident-names/`,
  RISK_SCORING_COMPLIANCE_NAMES: `${API_BASE_URL}/api/risk-scoring/compliance-names/`,
  RISK_SCORING_BUSINESS_UNITS: `${API_BASE_URL}/api/risk-scoring/business-units/`,
  RISK_SCORING_INSTANCES_WITH_NAMES: `${API_BASE_URL}/api/risk-scoring/instances-with-names/`,

  // Risk AI Document Ingestion (SIMPLIFIED URLS)
  RISK_AI_UPLOAD: `${API_BASE_URL}/api/ai-risk-doc-upload/`,
  RISK_AI_SAVE: `${API_BASE_URL}/api/ai-risk-save/`,
  RISK_AI_TEST_OLLAMA: `${API_BASE_URL}/api/ai-risk-test/`,
  RISK_AI_TEST_UPLOAD: `${API_BASE_URL}/api/ai-risk-test-upload/`,

  // Risk Instance AI Document Ingestion
  RISK_INSTANCE_AI_UPLOAD: `${API_BASE_URL}/api/ai-risk-instance-upload/`,
  RISK_INSTANCE_AI_SAVE: `${API_BASE_URL}/api/ai-risk-instance-save/`,
  RISK_INSTANCE_AI_TEST: `${API_BASE_URL}/api/ai-risk-instance-test/`,

  // Incident AI Document Ingestion
  INCIDENT_AI_UPLOAD: `${API_BASE_URL}/api/ai-incident-upload/`,
  INCIDENT_AI_SAVE: `${API_BASE_URL}/api/ai-incident-save/`,
  INCIDENT_AI_TEST: `${API_BASE_URL}/api/ai-incident-test/`,

  // Tree/Data Workflow API endpoints
  TREE_GET_FRAMEWORKS: `${API_BASE_URL}/api/tree/frameworks/`,
  TREE_GET_POLICIES: (frameworkId) => `${API_BASE_URL}/api/tree/frameworks/${frameworkId}/policies/`,
  TREE_GET_SUBPOLICIES: (policyId) => `${API_BASE_URL}/api/tree/policies/${policyId}/subpolicies/`,
  TREE_GET_COMPLIANCES: (subpolicyId) => `${API_BASE_URL}/api/tree/subpolicies/${subpolicyId}/compliances/`,
  TREE_GET_RISKS: (complianceId) => `${API_BASE_URL}/api/tree/compliances/${complianceId}/risks/`,
  TREE_GET_HIERARCHY: `${API_BASE_URL}/api/tree/hierarchy/`,
  // Metadata endpoints for hover tooltips
  TREE_GET_FRAMEWORK_METADATA: (frameworkId) => `${API_BASE_URL}/api/tree/frameworks/${frameworkId}/metadata/`,
  TREE_GET_POLICY_METADATA: (policyId) => `${API_BASE_URL}/api/tree/policies/${policyId}/metadata/`,
  TREE_GET_SUBPOLICY_METADATA: (subpolicyId) => `${API_BASE_URL}/api/tree/subpolicies/${subpolicyId}/metadata/`,
  TREE_GET_COMPLIANCE_METADATA: (complianceId) => `${API_BASE_URL}/api/tree/compliances/${complianceId}/metadata/`,
  TREE_GET_RISK_METADATA: (riskId) => `${API_BASE_URL}/api/tree/risks/${riskId}/metadata/`,

  // Current User
  CURRENT_USER: `${API_BASE_URL}/api/current-user/`,
 
  // Incidents
  INCIDENTS: `${API_BASE_URL}/api/incidents/`,
  INCIDENT: (incidentId) => `${API_BASE_URL}/api/incidents/${incidentId}/`,
  INCIDENT_ASSIGN: (incidentId) => `${API_BASE_URL}/api/incidents/${incidentId}/assign/`,
  INCIDENT_STATUS: (incidentId) => `${API_BASE_URL}/api/incidents/${incidentId}/status/`,
  INCIDENT_INCIDENTS: `${API_BASE_URL}/api/incident-incidents/`,
  INCIDENTS_USERS: `${API_BASE_URL}/api/incidents-users/`,
  INCIDENTS_EXPORT: `${API_BASE_URL}/api/incidents/export/`,
  SUBMIT_INCIDENT_ASSESSMENT: `${API_BASE_URL}/api/submit-incident-assessment/`,
  SUBMIT_AUDIT_FINDING_ASSESSMENT: `${API_BASE_URL}/api/submit-audit-finding-assessment/`,
 
  // Incident Management
  INCIDENT_CREATE: `${API_BASE_URL}/api/incidents/create/`,
  INCIDENT_COMPLIANCES: `${API_BASE_URL}/api/incident-compliances/`,
  INCIDENT_COUNTS: `${API_BASE_URL}/api/incidents/counts/`,
 
  // Incident Dashboard and Analytics
  INCIDENT_MTTD: `${API_BASE_URL}/api/incident/mttd/`,
  INCIDENT_MTTR: `${API_BASE_URL}/api/incident/mttr/`,
  INCIDENT_MTTC: `${API_BASE_URL}/api/incident/mttc/`,
  INCIDENT_MTTRV: `${API_BASE_URL}/api/incident/mttrv/`,
  INCIDENT_FALSE_POSITIVE_RATE: `${API_BASE_URL}/api/incident/false-positive-rate/`,
  INCIDENT_DETECTION_ACCURACY: `${API_BASE_URL}/api/incident/detection-accuracy/`,
  INCIDENT_CLOSURE_RATE: `${API_BASE_URL}/api/incident/incident-closure-rate/`,
  INCIDENT_REOPENED_COUNT: `${API_BASE_URL}/api/incident/reopened-count/`,
  INCIDENT_FIRST_RESPONSE_TIME: `${API_BASE_URL}/api/incident/first-response-time/`,
  INCIDENT_COUNT: `${API_BASE_URL}/api/incident/count/`,
  INCIDENT_BY_SEVERITY: `${API_BASE_URL}/api/incident/by-severity/`,
  INCIDENT_ROOT_CAUSES: `${API_BASE_URL}/api/incident/root-causes/`,
  INCIDENT_ORIGINS: `${API_BASE_URL}/api/incident/origins/`,
  INCIDENT_TYPES: `${API_BASE_URL}/api/incident/types/`,
  INCIDENT_VOLUME: `${API_BASE_URL}/api/incident/incident-volume/`,
  INCIDENT_ESCALATION_RATE: `${API_BASE_URL}/api/incident/escalation-rate/`,
  INCIDENT_COST: `${API_BASE_URL}/api/incident/cost/`,
  INCIDENT_REPEAT_RATE: `${API_BASE_URL}/api/incident/repeat-rate/`,
 
  // Incident User Tasks
  USER_INCIDENTS: (userId) => `${API_BASE_URL}/api/user-incidents/${userId}/`,
  USER_AUDIT_FINDINGS: (userId) => `${API_BASE_URL}/api/user-audit-findings/${userId}/`,
  INCIDENT_REVIEWER_TASKS: (userId) => `${API_BASE_URL}/api/incident-reviewer-tasks/${userId}/`,
  AUDIT_FINDING_REVIEWER_TASKS: (userId) => `${API_BASE_URL}/api/audit-finding-reviewer-tasks/${userId}/`,
  INCIDENT_MITIGATIONS: (id) => `${API_BASE_URL}/api/incident-mitigations/${id}/`,
  AUDIT_FINDING_MITIGATIONS: (id) => `${API_BASE_URL}/api/audit-finding-mitigations/${id}/`,
  INCIDENT_REVIEW_DATA: (id) => `${API_BASE_URL}/api/incident-review-data/${id}/`,
  AUDIT_FINDING_REVIEW_DATA: (id) => `${API_BASE_URL}/api/audit-finding-review-data/${id}/`,
  COMPLETE_INCIDENT_REVIEW: `${API_BASE_URL}/api/complete-incident-review/`,
  COMPLETE_AUDIT_FINDING_REVIEW: `${API_BASE_URL}/api/complete-audit-finding-review/`,
  UPLOAD_FILE: `${API_BASE_URL}/api/upload-file/`,
 
  // Audit Findings
  AUDIT_FINDINGS: `${API_BASE_URL}/api/audit-findings/`,
  AUDIT_FINDINGS_EXPORT: `${API_BASE_URL}/api/audit-findings/export/`,
  AUDIT_FINDINGS_INCIDENT: (incidentId) => `${API_BASE_URL}/api/audit-findings/incident/${incidentId}/`,
 
  // Categories and Business Units
  CATEGORIES: `${API_BASE_URL}/api/categories/`,
  CATEGORIES_ADD: `${API_BASE_URL}/api/categories/add/`,
  INCIDENT_CATEGORIES: `${API_BASE_URL}/api/incident-categories/`,
  INCIDENT_CATEGORIES_ADD: `${API_BASE_URL}/api/incident-categories/add/`,
  BUSINESS_UNITS_ADD: `${API_BASE_URL}/api/business-units/add/`,
 
  // Users
  USERS: `${API_BASE_URL}/api/users/`,

  // External Applications Integration
  EXTERNAL_APPLICATIONS: `${API_BASE_URL}/api/external-applications/`,
  EXTERNAL_APPLICATIONS_CONNECT: `${API_BASE_URL}/api/external-applications/connect/`,
  EXTERNAL_APPLICATIONS_DISCONNECT: `${API_BASE_URL}/api/external-applications/disconnect/`,
  EXTERNAL_APPLICATION_DETAILS: (applicationId) => `${API_BASE_URL}/api/external-applications/${applicationId}/`,
  EXTERNAL_APPLICATIONS_REFRESH_STATUS: `${API_BASE_URL}/api/external-applications/refresh-status/`,
  EXTERNAL_APPLICATION_SYNC_LOGS: (applicationId) => `${API_BASE_URL}/api/external-applications/${applicationId}/sync-logs/`,
  
  // BambooHR Integration
  BAMBOOHR_OAUTH: `${API_BASE_URL}/api/bamboohr/oauth/`,
  BAMBOOHR_OAUTH_CALLBACK: `${API_BASE_URL}/api/bamboohr/oauth-callback/`,
  BAMBOOHR_EMPLOYEES: `${API_BASE_URL}/api/bamboohr/employees/`,
  BAMBOOHR_DEPARTMENTS: `${API_BASE_URL}/api/bamboohr/departments/`,
  BAMBOOHR_TIME_OFF: `${API_BASE_URL}/api/bamboohr/time-off/`,
  BAMBOOHR_REPORTS: `${API_BASE_URL}/api/bamboohr/reports/`,
  BAMBOOHR_SYNC_DATA: `${API_BASE_URL}/api/bamboohr/sync-data/`,
  BAMBOOHR_STORED_DATA: `${API_BASE_URL}/api/bamboohr/stored-data/`,
  BAMBOOHR_ADD_USER: `${API_BASE_URL}/api/bamboohr/add-user/`,
  
// Jira Integration
  // Jira Integration - Updated for Python backend
  JIRA_OAUTH: `${API_BASE_URL}/api/jira/oauth/`,
  JIRA_OAUTH_CALLBACK: `${API_BASE_URL}/api/jira/oauth-callback/`,
  JIRA_PROJECTS: `${API_BASE_URL}/api/jira/projects/`,
  JIRA_PROJECT_DETAILS: `${API_BASE_URL}/api/jira/project-details/`,
  JIRA_RESOURCES: `${API_BASE_URL}/api/jira/resources/`,
  JIRA_STORED_DATA: `${API_BASE_URL}/api/jira/stored-data/`,
  
  // Legacy Jira endpoints (for backward compatibility)
  JIRA_DISCONNECT: `${API_BASE_URL}/api/jira/disconnect/`,
  JIRA_CONNECTION_STATUS: `${API_BASE_URL}/api/jira/connection-status/`,
  JIRA_DATA: `${API_BASE_URL}/api/jira/data/`,
  JIRA_STORED_PROJECTS_DATA: `${API_BASE_URL}/api/jira/stored-data/`,
  JIRA_PROJECT_DETAILS_FROM_DB: `${API_BASE_URL}/api/jira/project-details/`,
  JIRA_GET_ALL_USERS: `${API_BASE_URL}/api/jira/users/`,
  JIRA_ASSIGN_PROJECT: `${API_BASE_URL}/api/jira/assign-project/`,
  JIRA_PROJECT_ASSIGNMENTS: `${API_BASE_URL}/api/jira/project-assignments/`,

  // Streamline endpoints
  STREAMLINE_USER_PROJECTS: `${API_BASE_URL}/api/streamline/user-projects/`,
  STREAMLINE_PROJECT_DETAILS: `${API_BASE_URL}/api/streamline/project-details/`,
  STREAMLINE_USER_STATISTICS: `${API_BASE_URL}/api/streamline/user-statistics/`,
  STREAMLINE_SAVE_TASK_ACTION: `${API_BASE_URL}/api/streamline/save-task-action/`,
  STREAMLINE_USER_TASK_ACTIONS: `${API_BASE_URL}/api/streamline/user-task-actions/`,

  // Audit Finding Mitigations and Review Data
  // AUDIT_FINDING_MITIGATIONS: (id) => `${API_BASE_URL}/api/audit-finding-mitigations/${id}/`,
  // AUDIT_FINDING_REVIEW_DATA: (id) => `${API_BASE_URL}/api/audit-finding-review-data/${id}/`,
 
  // Complete Review Endpoints
  // COMPLETE_AUDIT_FINDING_REVIEW: `${API_BASE_URL}/api/complete-audit-finding-review/`,
 
  // Upload File
  // UPLOAD_FILE: `${API_BASE_URL}/api/upload-file/`,
 
  // Audit
  AUDITS: (auditId) => `${API_BASE_URL}/api/audits/${auditId}/`,
  AUDIT_TASK_DETAILS: (auditId) => `${API_BASE_URL}/api/audits/${auditId}/task-details/`,
  AUDIT_SAVE_VERSION: (auditId) => `${API_BASE_URL}/api/audits/${auditId}/save-version/`,
  AUDIT_SEND_FOR_REVIEW: (auditId) => `${API_BASE_URL}/api/audits/${auditId}/send-for-review/`,
  AUDIT_SUBMIT_FINDINGS: (auditId) => `${API_BASE_URL}/api/audits/${auditId}/submit/`,
  AUDIT_LOAD_LATEST_REVIEW_VERSION: (auditId) => `${API_BASE_URL}/api/audits/${auditId}/load-latest-review-version/`,
  AUDIT_LOAD_CONTINUING_DATA: (auditId) => `${API_BASE_URL}/api/audits/${auditId}/load-continuing-data/`,
  AUDIT_SAVE_AUDIT_VERSION: (auditId) => `${API_BASE_URL}/api/audits/${auditId}/save-audit-version/`,
  AUDIT_VERSIONS: (auditId) => `${API_BASE_URL}/api/audits/${auditId}/versions/`,
  AUDIT_VERSION_DETAILS: (auditId, version) => `${API_BASE_URL}/api/audits/${auditId}/versions/${version}/`,
  AUDIT_CHECK_VERSION: (auditId) => `${API_BASE_URL}/api/audits/${auditId}/check-version/`,

  // Audit Review Management
  MY_REVIEWS: `${API_BASE_URL}/api/my-reviews/`,
  // AUDIT_STATUS: (auditId) => `${API_BASE_URL}/audits/${auditId}/status/`,
  UPDATE_AUDIT_REVIEW_STATUS: (auditId) => `${API_BASE_URL}/api/audits/${auditId}/update-audit-review-status/`,
  GENERATE_AUDIT_REPORT: (auditId) => `${API_BASE_URL}/api/generate-audit-report/${auditId}/`,

  
  // Compliance

  //COMPLIANCE_CLONE: (id) => `${API_BASE_URL}/compliance/${id}/clone/`,
  COMPLIANCE_DASHBOARD: `${API_BASE_URL}/compliance/dashboard/`,




 
  // Auditor Dashboard and Analytics
  AUDIT_COMPLETION_RATE: `${API_BASE_URL}/api/dashboard/audit-completion-rate/`,
  AUDIT_TOTAL_AUDITS: `${API_BASE_URL}/api/dashboard/total-audits/`,
  AUDIT_OPEN_AUDITS: `${API_BASE_URL}/api/dashboard/open-audits/`,
  AUDIT_COMPLETED_AUDITS: `${API_BASE_URL}/api/dashboard/completed-audits/`,
  AUDIT_COMPLETION_TREND: `${API_BASE_URL}/api/dashboard/audit-completion-trend/`,
  AUDIT_COMPLIANCE_TREND: `${API_BASE_URL}/api/dashboard/audit-compliance-trend/`,
  AUDIT_FINDING_TREND: `${API_BASE_URL}/api/dashboard/audit-finding-trend/`,
  AUDIT_FRAMEWORK_PERFORMANCE: `${API_BASE_URL}/api/dashboard/framework-performance/`,
  AUDIT_CATEGORY_PERFORMANCE: `${API_BASE_URL}/api/dashboard/category-performance/`,
  AUDIT_CATEGORY_DISTRIBUTION: `${API_BASE_URL}/api/dashboard/category-distribution/`,
  AUDIT_STATUS_DISTRIBUTION: `${API_BASE_URL}/api/dashboard/status-distribution/`,
  AUDIT_RECENT_ACTIVITIES: `${API_BASE_URL}/api/dashboard/recent-audit-activities/`,
 
  // Auditor Management
  AUDIT_MY_AUDITS: `${API_BASE_URL}/api/my-audits/`,
  AUDIT_STATUS: (auditId) => `${API_BASE_URL}/api/audits/${auditId}/status/`,
  AUDIT_COMPLIANCES: (auditId) => `${API_BASE_URL}/api/audit-compliances/${auditId}/`,
  AUDIT_FINDINGS_BULK_UPDATE: `${API_BASE_URL}/api/audit-findings/bulk-update/`,
  AUDIT_FINDINGS_DETAILS: (auditFindingId) => `${API_BASE_URL}/audit-findings-details/${auditFindingId}/`,
  AUDIT_REPORT: (auditId) => `${API_BASE_URL}/api/audit-report/${auditId}/`,
 
  // Audit Reports Management
  AUDIT_REPORTS: `${API_BASE_URL}/api/audit-reports/`,
  AUDIT_REPORT_VERSIONS: (auditId) => `${API_BASE_URL}/api/audit-reports/${auditId}/versions/`,
  AUDIT_REPORT_VERSION_DELETE: (auditId, version) => `${API_BASE_URL}/api/audit-reports/${auditId}/versions/${version}/delete/`,
  AUDIT_REPORT_VERSION_S3_LINK: (auditId, version) => `${API_BASE_URL}/api/audit-reports/${auditId}/versions/${version}/s3-link/`,
 
  // Audit Creation and Assignment
  AUDIT_CREATE: `${API_BASE_URL}/api/create-audit/`,
  AUDIT_COMPLIANCE_COUNT: `${API_BASE_URL}/api/compliance-count/`,
 
  // Evidence Upload
  UPLOAD_EVIDENCE_S3: `${API_BASE_URL}/api/upload-evidence-s3/`,
 
  // Business Units
  BUSINESS_UNITS: `${API_BASE_URL}/api/business-units/`,
 
  // Evidence Upload
  UPLOAD_EVIDENCE: (complianceId) => `${API_BASE_URL}/upload-evidence/${complianceId}/`,
 
  // S3 Upload (separate service)
  S3_UPLOAD: 'http://localhost:3001/api/upload',
 
  // KPI and Performance Analysis
  KPI_AUDIT_COMPLETION: (period) => `${API_BASE_URL}/api/kpi/audit-completion/?period=${period}`,
  KPI_AUDIT_CYCLE_TIME: (frameworkId = '') => `${API_BASE_URL}/api/kpi/audit-cycle-time/${frameworkId ? `?framework_id=${frameworkId}` : ''}`,
  KPI_FINDING_RATE: (period) => `${API_BASE_URL}/api/kpi/finding-rate/?period=${period}`,
  KPI_TIME_TO_CLOSE: (period) => `${API_BASE_URL}/api/kpi/time-to-close/?period=${period}`,
  KPI_CLOSURE_RATE: (period) => `${API_BASE_URL}/api/kpi/closure-rate/?period=${period}`,
  KPI_NON_COMPLIANCE_ISSUES: (period, severity) => `${API_BASE_URL}/api/kpi/non-compliance-issues/?period=${period}&severity=${severity}`,
  KPI_SEVERITY_DISTRIBUTION: (period) => `${API_BASE_URL}/api/kpi/severity-distribution/?period=${period}`,
  KPI_EVIDENCE_COMPLETION: (auditId = '') => `${API_BASE_URL}/api/kpi/evidence-completion/${auditId ? `?audit_id=${auditId}` : ''}`,
  KPI_REPORT_TIMELINESS: (period) => `${API_BASE_URL}/api/kpi/report-timeliness/?period=${period}`,
  KPI_COMPLIANCE_READINESS: (frameworkId = '', policyId = '') => {
    const params = [];
    if (frameworkId) params.push(`framework_id=${frameworkId}`);
    if (policyId) params.push(`policy_id=${policyId}`);
    return `${API_BASE_URL}/api/kpi/compliance-readiness/${params.length > 0 ? `?${params.join('&')}` : ''}`;
  },

  // Event Handling
  EVENTS_FRAMEWORKS: `${API_BASE_URL}/api/events/frameworks/`,
  EVENTS_RECORDS: `${API_BASE_URL}/api/events/records/`,
  EVENTS_TEMPLATES: `${API_BASE_URL}/api/events/templates/`,
  EVENTS_CREATE: `${API_BASE_URL}/api/events/create/`,
  EVENTS_LIST: `${API_BASE_URL}/api/events/list/`,
  EVENTS_CALENDAR: `${API_BASE_URL}/api/events/calendar/`,
  EVENTS_DASHBOARD: `${API_BASE_URL}/api/events/dashboard/`,
  EVENT_DETAILS: (eventId) => `${API_BASE_URL}/api/events/${eventId}/`,

  // Document Handling
  DOCUMENTS_LIST: `${API_BASE_URL}/api/documents/list/`,
  DOCUMENTS_COUNTS: `${API_BASE_URL}/api/documents/counts/`,
  DOCUMENTS_UPLOAD: `${API_BASE_URL}/api/documents/upload/`,

  // Microsoft Sentinel Integration
  SENTINEL_STATUS: `${API_BASE_URL}/api/sentinel/status/`,
  SENTINEL_INCIDENTS: `${API_BASE_URL}/api/sentinel/incidents/`,
  SENTINEL_ALERTS: `${API_BASE_URL}/api/sentinel/alerts/`,
  SENTINEL_STATS: `${API_BASE_URL}/api/sentinel/stats/`,
  SENTINEL_INCIDENT_DETAIL: (incidentId) => `${API_BASE_URL}/api/sentinel/incident/${incidentId}/`,
  SENTINEL_CONNECT: `${API_BASE_URL}/auth/sentinel/`,
  SENTINEL_DISCONNECT: `${API_BASE_URL}/auth/sentinel/disconnect/`,
  SENTINEL_CALLBACK: `${API_BASE_URL}/auth/sentinel/callback/`,
  SENTINEL_SAVE_INCIDENT: `${API_BASE_URL}/api/sentinel/save-incident/`,
  SENTINEL_SAVED_INCIDENTS: `${API_BASE_URL}/api/sentinel/saved-incidents/`,

  // KPI Management
  KPIS_ALL: `${API_BASE_URL}/api/kpis/`,
  KPI_BY_ID: (kpiId) => `${API_BASE_URL}/api/kpis/${kpiId}/`,
  KPIS_BY_MODULE: (module) => `${API_BASE_URL}/api/kpis/module/${module}/`,
  KPIS_FRAMEWORKS: `${API_BASE_URL}/api/kpis/frameworks/`,
  KPIS_MODULES: `${API_BASE_URL}/api/kpis/modules/`,

  // ========================================================================
  // FRAMEWORK COMPARISON - CHANGE MANAGEMENT
  // ========================================================================
  CHANGE_MGMT_FRAMEWORKS_WITH_AMENDMENTS: `${API_BASE_URL}/api/change-management/frameworks-with-amendments/`,
  CHANGE_MGMT_FRAMEWORK_AMENDMENTS: (frameworkId) => `${API_BASE_URL}/api/change-management/framework/${frameworkId}/amendments/`,
  CHANGE_MGMT_FRAMEWORK_ORIGIN: (frameworkId) => `${API_BASE_URL}/api/change-management/framework/${frameworkId}/origin/`,
  CHANGE_MGMT_FRAMEWORK_TARGET: (frameworkId, amendmentId = null) => 
    amendmentId 
      ? `${API_BASE_URL}/api/change-management/framework/${frameworkId}/target/${amendmentId}/`
      : `${API_BASE_URL}/api/change-management/framework/${frameworkId}/target/`,
  CHANGE_MGMT_FRAMEWORK_SUMMARY: (frameworkId) => `${API_BASE_URL}/api/change-management/framework/${frameworkId}/summary/`,
  CHANGE_MGMT_FIND_MATCHES: (frameworkId) => `${API_BASE_URL}/api/change-management/framework/${frameworkId}/find-matches/`,
  CHANGE_MGMT_BATCH_MATCH: (frameworkId) => `${API_BASE_URL}/api/change-management/framework/${frameworkId}/batch-match/`,
  CHANGE_MGMT_MIGRATION_OVERVIEW: (frameworkId) => `${API_BASE_URL}/api/change-management/framework/${frameworkId}/migration-overview/`,
   CHANGE_MGMT_GAP_ANALYSIS: (frameworkId) => `${API_BASE_URL}/api/change-management/framework/${frameworkId}/gap-analysis/`,
  CHANGE_MGMT_MATCH_COMPLIANCES: (frameworkId) => `${API_BASE_URL}/api/change-management/framework/${frameworkId}/match-compliances/`,
  CHANGE_MGMT_ADD_COMPLIANCE: (frameworkId) => `${API_BASE_URL}/api/change-management/framework/${frameworkId}/add-compliance/`,
  CHANGE_MGMT_CHECK_UPDATES: (frameworkId) => `${API_BASE_URL}/api/change-management/framework/${frameworkId}/check-updates/`,
  CHANGE_MGMT_SCAN_DOWNLOADS: `${API_BASE_URL}/api/change-management/scan-downloads/`,
  CHANGE_MGMT_DOCUMENT_INFO: (frameworkId) => `${API_BASE_URL}/api/change-management/framework/${frameworkId}/document-info/`,
  CHANGE_MGMT_START_ANALYSIS: (frameworkId) => `${API_BASE_URL}/api/change-management/framework/${frameworkId}/start-analysis/`
};
 
// Axios instance configuration with JWT authentication
export const createAxiosInstance = (baseURL = API_BASE_URL) => {
  const axios = require('axios');
  const instance = axios.create({
    baseURL,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    },
    timeout: 30000,
    withCredentials: true,  // Send cookies for CSRF protection
    xsrfCookieName: 'csrftoken',
    xsrfHeaderName: 'X-CSRFToken'
  });

  // Add JWT token to requests
  instance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
        console.log(`🔐 [API] Adding JWT token to request: ${config.method.toUpperCase()} ${config.url}`);
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  return instance;
};
 
// Default axios instance
export const axiosInstance = createAxiosInstance();
 
// Console log for debugging
console.log(`🔧 API Configuration: Using ${ENVIRONMENT} environment`);
console.log(`🌐 Base URL: ${API_BASE_URL}`);
 
export default {
  API_BASE_URL,
  API_ENDPOINTS,
  ENVIRONMENT,
  createAxiosInstance,
  axiosInstance
};