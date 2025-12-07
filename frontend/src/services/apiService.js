/**
 * Centralized API Service
 * All API calls should use this service to ensure JWT tokens are attached
 */

import axios from 'axios';
import { API_BASE_URL } from '../config/api.js';

/**
 * Create axios instance with JWT authentication
 */
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  timeout: 30000,
  withCredentials: true,  // Send cookies for CSRF protection
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken'
});

/**
 * Request Interceptor - Add JWT token to all requests
 */
apiClient.interceptors.request.use(
  (config) => {
    // Get JWT token from localStorage
    const token = localStorage.getItem('access_token');
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log(`🔐 [API Service] Adding JWT token to ${config.method?.toUpperCase()} ${config.url}`);
    } else {
      console.warn(`⚠️ [API Service] No JWT token found for ${config.method?.toUpperCase()} ${config.url}`);
    }
    
    // Add user_id to params if not already present (for RBAC fallback)
    const userId = localStorage.getItem('user_id');
    if (userId && !config.params?.user_id) {
      config.params = {
        ...config.params,
        user_id: userId
      };
    }
    
    return config;
  },
  (error) => {
    console.error('❌ [API Service] Request error:', error);
    return Promise.reject(error);
  }
);

/**
 * Response Interceptor - Handle token refresh and errors
 */
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // If 401 and we haven't retried yet, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (refreshToken) {
          console.log('🔄 [API Service] Attempting token refresh...');
          
          const response = await axios.post(`${API_BASE_URL}/api/jwt/refresh/`, {
            refresh_token: refreshToken
          });
          
          if (response.data.status === 'success') {
            const newAccessToken = response.data.access_token;
            const newRefreshToken = response.data.refresh_token;
            
            // Update tokens
            localStorage.setItem('access_token', newAccessToken);
            localStorage.setItem('refresh_token', newRefreshToken);
            
            console.log('✅ [API Service] Token refreshed successfully');
            
            // Retry original request with new token
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return apiClient(originalRequest);
          }
        }
      } catch (refreshError) {
        console.error('❌ [API Service] Token refresh failed:', refreshError);
        
        // Clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_id');
        localStorage.removeItem('user_name');
        
        // Redirect to login
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    // Log 401/403 errors
    if (error.response?.status === 401 || error.response?.status === 403) {
      console.error(`❌ [API Service] ${error.response.status} error:`, {
        url: error.config?.url,
        method: error.config?.method,
        message: error.response?.data?.message || error.message
      });
    }
    
    return Promise.reject(error);
  }
);

/**
 * API Service Methods
 */
export const apiService = {
  /**
   * GET request
   */
  get(url, config = {}) {
    return apiClient.get(url, config);
  },
  
  /**
   * POST request
   */
  post(url, data, config = {}) {
    return apiClient.post(url, data, config);
  },
  
  /**
   * PUT request
   */
  put(url, data, config = {}) {
    return apiClient.put(url, data, config);
  },
  
  /**
   * PATCH request
   */
  patch(url, data, config = {}) {
    return apiClient.patch(url, data, config);
  },
  
  /**
   * DELETE request
   */
  delete(url, config = {}) {
    return apiClient.delete(url, config);
  },
  
  /**
   * Get the axios instance for advanced usage
   */
  getInstance() {
    return apiClient;
  }
};

export default apiService;

