import axios from 'axios';
import { API_BASE_URL, API_ENDPOINTS, axiosInstance } from '../config/api.js';

// API base URL WITHOUT /api
const API_URL = API_BASE_URL;
console.log(`Using API URL: ${API_URL}`);

// Use the authenticated axios instance from config/api.js
// This ensures we use the same interceptors set up for JWT authentication

// API Functions
export const api = {
  // Framework
  getFrameworks: () => axiosInstance.get('/api/frameworks/'),
  getFrameworkDetails: (id) => axiosInstance.get(`/api/frameworks/${id}/`),
  getFrameworkDetailsForTree: (id) => axiosInstance.get(`/api/frameworks/${id}/tree/`),

  // Policies
  getPolicies: () => axiosInstance.get('/api/policies/'),
  getPoliciesByFramework: (frameworkId) => axiosInstance.get(`/api/frameworks/${frameworkId}/policies/list/`),

  // SubPolicies
  getSubPolicies: (policyId) => axiosInstance.get(`/api/policies/${policyId}/subpolicies/`),

  // Users
  getUsers: () => axiosInstance.get('/api/users/'),
  getUserProfile: (userId) => axiosInstance.get(API_ENDPOINTS.USER_PROFILE(userId)),
  getUserBusinessInfo: (userId) => axiosInstance.get(API_ENDPOINTS.USER_BUSINESS_INFO(userId)),
  getUserPermissions: (userId) => axiosInstance.get(API_ENDPOINTS.USER_PERMISSIONS(userId)),

  // Assignment
  getAssignData: () => axiosInstance.get('/assign-data/'),
  allocatePolicy: (data) => axiosInstance.post('/allocate-policy/', data),

  // Incidents
  getIncidents: () => axiosInstance.get('/api/incident-incidents/'),


  // Audits
  getAllAudits: () => axiosInstance.get('/api/audits/'),
  getMyAudits: () => axiosInstance.get('/api/my-audits/'),
  getMyReviews: () => axiosInstance.get(API_ENDPOINTS.MY_REVIEWS),
  getAuditDetails: (id) => axiosInstance.get(`/api/audits/${id}/`),
  updateAuditStatus: (id, data) => axiosInstance.post(API_ENDPOINTS.AUDIT_STATUS(id), data),
  updateAuditReviewStatus: (id, data) => axiosInstance.post(API_ENDPOINTS.UPDATE_AUDIT_REVIEW_STATUS(id), data),
  updateReviewStatus: (id, data) => axiosInstance.post(API_ENDPOINTS.UPDATE_AUDIT_REVIEW_STATUS(id), data),
  saveReviewProgress: (id, data) => axiosInstance.post(`/api/audits/${id}/save-review-progress/`, data),
  getAuditStatus: (id) => axiosInstance.get(`/api/audits/${id}/get-status/`),
  getAuditCompliances: (id) => axiosInstance.get(`/api/audits/${id}/compliances/`),
  addComplianceToAudit: (id, data) => axiosInstance.post(`/api/audits/${id}/add-compliance/`, data),
  updateComplianceStatus: (complianceId, data) => axiosInstance.post(`/api/audit-findings/${complianceId}/`, data),
  submitAuditFindings: (id, data = {}) => axiosInstance.post(`/api/audits/${id}/submit/`, data),
  loadLatestReviewVersion: (id) => axiosInstance.get(`/api/audits/${id}/load-latest-review-version/`),
  loadAuditContinuingData: (id) => axiosInstance.get(`/api/audits/${id}/load-audit-continuing-data/`),
  saveAuditVersion: (id, auditData) => axiosInstance.post(`/api/audits/${id}/save-audit-version/`, { audit_data: auditData }),

  // Task Views
  getAuditTaskDetails: (id) => axiosInstance.get(`/api/audits/${id}/task-details/`),
  saveVersion: (id, data) => axiosInstance.post(`/api/audits/${id}/save-version/`, data),
  sendForReview: (id, data) => axiosInstance.post(`/api/audits/${id}/send-for-review/`, data),

  // Audit Reports
  checkAuditReports: (params) => axiosInstance.get('/api/audit-reports/check/', { params }),
  getReportDetails: (ids) => axiosInstance.get('/api/audit-reports/details/', { params: { report_ids: ids } }),

  // Versions
  getAuditVersions: (id) => axiosInstance.get(`/api/audits/${id}/versions/`),
  getAuditVersionDetails: (id, version) => axiosInstance.get(`/api/audits/${id}/versions/${version}/`),
  checkAuditVersion: (id) => axiosInstance.get(`/api/audits/${id}/check-version/`),


  // Evidence Upload
  uploadEvidence: (complianceId, formData) =>
    axiosInstance.post(`/api/upload-evidence/${complianceId}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),

  // S3 Upload
  uploadFile: (formData, onUploadProgress) =>
    axios.post('http://localhost:3001/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress
    }),

  // Compliance Service
  // createCompliance: (data) => axiosInstance.post('/api/compliance/create/', data),
  editCompliance: (id, data) => axiosInstance.put(`/api/compliance_edit/${id}/edit/`, data),
  cloneCompliance: (id) => axiosInstance.post(`/api/compliance/${id}/clone/`),
  getComplianceDashboard: () => axiosInstance.get('/api/compliance/dashboard/'),

  // Audit Report Download
  downloadAuditReport: (id) => axiosInstance.get(`/api/generate-audit-report/${id}/`, {
    responseType: 'blob',
    headers: {
      'Accept': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
  }),

  fetchExtractedContent: (id) => axiosInstance.get(`/api/get-upload-sections/${id}/`),

  // Debug
  debugPrintAuditData: (id) => {
    console.log(`===== DEBUG PRINT AUDIT DATA FOR AUDIT ID: ${id} =====`);
    return Promise.all([
      axiosInstance.get(`/api/audits/${id}/`),
      axiosInstance.get(`/api/audits/${id}/check-version/`),
      axiosInstance.get(`/api/audits/${id}/compliances/`)
    ]).then(([auditDetails, versionCheck, compliances]) => {
      console.log('1. AUDIT DETAILS:', auditDetails.data);
      console.log('2. VERSION INFO:', versionCheck.data);
      console.log('3. COMPLIANCES STRUCTURE:', compliances.data);
      return { auditDetails: auditDetails.data, versionCheck: versionCheck.data, compliances: compliances.data };
    });
  },
};

// RBAC Service Functions
export const rbacService = {
  // Check if user is authenticated
  async checkAuthStatus() {
    console.log('🔐 RBAC: Bypassing authentication check...');
    return { is_authenticated: true };
  },

  // Get user permissions (only if authenticated)
  async getUserPermissions() {
    console.log('🔐 RBAC: Returning full permissions...');
    return {
      permissions: {
        incident: {
          create: true,
          edit: true,
          view: true,
          assign: true,
          approve: true,
          delete: true,
          escalate: true,
          analytics: true
        },
        audit: {
          view: true,
          conduct: true,
          review: true,
          assign: true,
          analytics: true
        }
      },
      role: 'admin',
      department: 'IT',
      entity: 'Organization',
      user_id: '1',
      email: 'admin@example.com'
    };
  },

  // Get user role (only if authenticated)
  async getUserRole() {
    console.log('🔐 RBAC: Returning admin role...');
    return { role: 'admin' };
  },

  // Test RBAC auth
  async testRbacAuth() {
    console.log('🔐 RBAC: Auth test bypassed...');
    return { success: true };
  },

  // Login (always succeeds)
  async login() {
    console.log('🔐 RBAC: Login bypassed...');
    return { success: true };
  },

  // Logout (always succeeds)
  async logout() {
    console.log('🔐 RBAC: Logout bypassed...');
    return { success: true };
  },

  // Generic HTTP methods
  get: (url, config = {}) => axiosInstance.get(url, config),
  post: (url, data = {}, config = {}) => axiosInstance.post(url, data, config),
  put: (url, data = {}, config = {}) => axiosInstance.put(url, data, config),
  delete: (url, config = {}) => axiosInstance.delete(url, config),
  patch: (url, data = {}, config = {}) => axiosInstance.patch(url, data, config)
};

export default api;
