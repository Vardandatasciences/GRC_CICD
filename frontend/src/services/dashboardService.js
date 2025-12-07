import axios from 'axios';
import { API_BASE_URL } from '../config/api.js';

const API_BASE = `${API_BASE_URL}/api`; // Use centralized API configuration

// Configure axios to include JWT token in requests
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add request interceptor to include JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default {
    async getDashboardSummary(params = {}) {
        try {
            const queryString = new URLSearchParams(params).toString();
            const url = queryString ? `${API_BASE}/policy-dashboard/?${queryString}` : `${API_BASE}/policy-dashboard/`;
            const summaryRes = await api.get(url);
            return {
                data: {
                    ...summaryRes.data,
                    policies: Array.isArray(summaryRes.data.policies) ? summaryRes.data.policies : []
                }
            };
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
            return {
                data: {
                    total_policies: 0,
                    active_policies: 0,
                    inactive_policies: 0,
                    total_subpolicies: 0,
                    active_subpolicies: 0,
                    approval_rate: 0,
                    policies: []
                }
            };
        }
    },
    getPolicyAnalytics(params) {
        return api.get(`${API_BASE}/policy-analytics/`, {
            params: params
        });
    },
    getPolicyStatusDistribution(params = {}) {
      const queryString = new URLSearchParams(params).toString();
      const url = queryString ? `${API_BASE}/policy-status-distribution/?${queryString}` : `${API_BASE}/policy-status-distribution/`;
      return api.get(url);
    },
    getReviewerWorkload(params = {}) {
      const queryString = new URLSearchParams(params).toString();
      const url = queryString ? `${API_BASE}/reviewer-workload/?${queryString}` : `${API_BASE}/reviewer-workload/`;
      return api.get(url);
    },
    getRecentPolicyActivity(params = {}) {
      const queryString = new URLSearchParams(params).toString();
      const url = queryString ? `${API_BASE}/recent-policy-activity/?${queryString}` : `${API_BASE}/recent-policy-activity/`;
      return api.get(url);
    },
    getAvgApprovalTime(params = {}) {
      const queryString = new URLSearchParams(params).toString();
      const url = queryString ? `${API_BASE}/avg-policy-approval-time/?${queryString}` : `${API_BASE}/avg-policy-approval-time/`;
      return api.get(url);
    },
    getAllPolicies() {
        return api.get(`${API_BASE}/policies/`);
    },
    // Get all frameworks
    getAllFrameworks() {
        return api.get(`${API_BASE}/frameworks/?include_all_status=true`);
    },
    // New: Get policies by framework
    getPoliciesByFramework(frameworkId) {
        return api.get(`${API_BASE}/frameworks/${frameworkId}/policies/list/`);
    },
    // New: Get framework status distribution
    getFrameworkStatusDistribution(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${API_BASE}/framework-status-distribution/?${queryString}` : `${API_BASE}/framework-status-distribution/`;
        return api.get(url);
    },
    // Get recent policies (last 5 created)
    getRecentPolicies() {
        return api.get(`${API_BASE}/policies/?limit=5&ordering=-CreatedByDate`);
    }
  };
  