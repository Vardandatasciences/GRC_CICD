/**
 * Integrations Service - Centralized Data Management
 * 
 * This service handles:
 * 1. Fetching all integration-related data on login
 * 2. Caching data in memory for instant access
 * 3. Providing cached data to components
 */

import { axiosInstance } from '@/config/api.js';
import { API_ENDPOINTS } from '@/config/api.js';

class IntegrationsService {
  constructor() {
    // Centralized data store
    this.dataStore = {
      applications: [],
      jiraStoredData: null,
      bamboohrStoredData: null,
      gmailStoredData: null,
      sentinelStoredData: null,
      lastFetchTime: null,
      isFetching: false,
      fetchError: null
    };
  }

  /**
   * Fetch all integration data and cache it
   */
  async fetchAllIntegrationData() {
    if (this.dataStore.isFetching) {
      console.log('[Integrations Service] Already fetching, skipping duplicate request');
      return this.dataStore;
    }

    this.dataStore.isFetching = true;
    console.log('[Integrations Service] 🚀 Starting integrations data prefetch...');

    try {
      // Get user ID
      const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1;

      // Fetch all integration-related datasets
      await Promise.all([
        this.fetchApplications(userId),
        this.fetchJiraStoredData(userId),
        this.fetchBambooHRStoredData(userId),
        // Add more integrations as needed
      ]);

      this.dataStore.lastFetchTime = new Date();
      this.dataStore.fetchError = null;
      
      console.log(`[Integrations Service] ✅ Prefetch complete - Total applications: ${this.dataStore.applications.length}`);
      
      return this.dataStore;
    } catch (error) {
      console.error('[Integrations Service] ❌ Prefetch failed:', error);
      this.dataStore.fetchError = error.message;
      throw error;
    } finally {
      this.dataStore.isFetching = false;
    }
  }

  /**
   * Fetch external applications from API
   */
  async fetchApplications(userId) {
    try {
      const response = await axiosInstance.get(`${API_ENDPOINTS.EXTERNAL_APPLICATIONS}?user_id=${userId}`, {
        timeout: 60000
      });

      if (response.data.success) {
        this.dataStore.applications = response.data.applications.map(app => ({
          ...app,
          connecting: false,
          disconnecting: false,
          hasProjectsData: false
        }));
        console.log(`[Integrations Service] Fetched ${this.dataStore.applications.length} applications`);
      } else {
        this.dataStore.applications = [];
      }
    } catch (error) {
      console.error('[Integrations Service] Error fetching applications:', error);
      this.dataStore.applications = [];
      throw error;
    }
  }

  /**
   * Fetch Jira stored data from API
   */
  async fetchJiraStoredData(userId) {
    try {
      const response = await axiosInstance.get(`${API_ENDPOINTS.JIRA_STORED_DATA}?user_id=${userId}`, {
        timeout: 60000
      });

      if (response.data.success && response.data.data) {
        this.dataStore.jiraStoredData = response.data.data;
        
        // Update application with project count
        const jiraApp = this.dataStore.applications.find(app => app.name === 'Jira');
        if (jiraApp && this.dataStore.jiraStoredData.projects) {
          jiraApp.hasProjectsData = true;
          jiraApp.projectsCount = this.dataStore.jiraStoredData.projects.length;
        }
        
        console.log(`[Integrations Service] Fetched Jira stored data: ${this.dataStore.jiraStoredData.projects?.length || 0} projects`);
      } else {
        this.dataStore.jiraStoredData = null;
      }
    } catch (error) {
      console.log('[Integrations Service] No Jira stored data found:', error.message);
      this.dataStore.jiraStoredData = null;
    }
  }

  /**
   * Fetch BambooHR stored data from API
   */
  async fetchBambooHRStoredData(userId) {
    try {
      const response = await axiosInstance.get(`${API_ENDPOINTS.BAMBOOHR_STORED_DATA}?user_id=${userId}`, {
        timeout: 60000
      });

      if (response.data.success && response.data.data) {
        this.dataStore.bamboohrStoredData = response.data.data;
        
        // Update application with employee count
        const bamboohrApp = this.dataStore.applications.find(app => app.name === 'BambooHR');
        if (bamboohrApp && this.dataStore.bamboohrStoredData.employees) {
          bamboohrApp.hasProjectsData = true;
          bamboohrApp.employeeCount = this.dataStore.bamboohrStoredData.employees.length;
          bamboohrApp.departmentCount = this.dataStore.bamboohrStoredData.departments?.length || 0;
        }
        
        console.log(`[Integrations Service] Fetched BambooHR stored data: ${this.dataStore.bamboohrStoredData.employees?.length || 0} employees`);
      } else {
        this.dataStore.bamboohrStoredData = null;
      }
    } catch (error) {
      console.log('[Integrations Service] No BambooHR stored data found:', error.message);
      this.dataStore.bamboohrStoredData = null;
    }
  }

  /**
   * Get cached data
   * @param {string} key - The data key to retrieve
   * @returns {any} The cached data
   */
  getData(key) {
    return this.dataStore[key];
  }

  /**
   * Set cached data
   * @param {string} key - The data key to set
   * @param {any} value - The value to set
   */
  setData(key, value) {
    if (Object.prototype.hasOwnProperty.call(this.dataStore, key)) {
      this.dataStore[key] = value;
      if (key !== 'lastFetchTime' && key !== 'isFetching' && key !== 'fetchError') {
        this.dataStore.lastFetchTime = new Date();
      }
    }
  }

  /**
   * Check if data is cached and fresh
   * @returns {boolean}
   */
  hasValidCache() {
    return this.dataStore.applications.length > 0 && this.dataStore.lastFetchTime !== null;
  }

  /**
   * Update application status
   * @param {number} applicationId - The application ID
   * @param {object} updates - The updates to apply
   */
  updateApplication(applicationId, updates) {
    const app = this.dataStore.applications.find(a => a.id === applicationId);
    if (app) {
      Object.assign(app, updates);
      this.dataStore.lastFetchTime = new Date();
    }
  }

  /**
   * Clear all cached data
   */
  clearCache() {
    this.dataStore.applications = [];
    this.dataStore.jiraStoredData = null;
    this.dataStore.bamboohrStoredData = null;
    this.dataStore.gmailStoredData = null;
    this.dataStore.sentinelStoredData = null;
    this.dataStore.lastFetchTime = null;
    this.dataStore.fetchError = null;
    console.log('[Integrations Service] Cache cleared');
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      applicationsCount: this.dataStore.applications.length,
      connectedApplications: this.dataStore.applications.filter(app => app.status === 'connected').length,
      hasJiraData: !!this.dataStore.jiraStoredData,
      hasBambooHRData: !!this.dataStore.bamboohrStoredData,
      lastFetchTime: this.dataStore.lastFetchTime,
      isFetching: this.dataStore.isFetching,
      hasError: !!this.dataStore.fetchError
    };
  }
}

// Export singleton instance
const integrationsDataService = new IntegrationsService();
export default integrationsDataService;

