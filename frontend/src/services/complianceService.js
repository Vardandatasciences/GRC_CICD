/**
 * Compliance Service - Centralized Data Management
 * 
 * This service handles:
 * 1. Fetching all compliance-related data on login
 * 2. Caching data in memory for instant access
 * 3. Providing cached data to components
 */

import { axiosInstance } from '@/config/api.js';
import { API_ENDPOINTS } from '@/config/api.js';

class ComplianceService {
  constructor() {
    // Centralized data store
    this.dataStore = {
      frameworks: [],
      policies: [],
      subpolicies: [],
      compliances: [],
      lastFetchTime: null,
      isFetching: false,
      fetchError: null
    };
  }

  /**
   * Fetch all compliance data and cache it
   */
  async fetchAllComplianceData() {
    if (this.dataStore.isFetching) {
      console.log('[Compliance Service] Already fetching, skipping duplicate request');
      return this.dataStore;
    }

    this.dataStore.isFetching = true;
    console.log('[Compliance Service] 🚀 Starting compliance data prefetch...');

    try {
      // Fetch all compliance-related datasets
      await Promise.all([
        this.fetchFrameworks(),
        this.fetchAllCompliances()
      ]);

      this.dataStore.lastFetchTime = new Date();
      this.dataStore.fetchError = null;
      
      console.log(`[Compliance Service] ✅ Prefetch complete - Total frameworks: ${this.dataStore.frameworks.length}`);
      console.log(`[Compliance Service] ✅ Prefetch complete - Total compliances: ${this.dataStore.compliances.length}`);
      
      return this.dataStore;
    } catch (error) {
      console.error('[Compliance Service] ❌ Prefetch failed:', error);
      this.dataStore.fetchError = error.message;
      throw error;
    } finally {
      this.dataStore.isFetching = false;
    }
  }

  /**
   * Fetch frameworks from API
   */
  async fetchFrameworks() {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_FRAMEWORKS, {
        timeout: 60000
      });

      // Handle both old and new response formats
      if (Array.isArray(response.data)) {
        this.dataStore.frameworks = response.data;
      } else if (response.data.success && response.data.frameworks) {
        this.dataStore.frameworks = response.data.frameworks;
      } else {
        this.dataStore.frameworks = [];
      }

      console.log(`[Compliance Service] Fetched ${this.dataStore.frameworks.length} frameworks`);
    } catch (error) {
      console.error('[Compliance Service] Error fetching frameworks:', error);
      this.dataStore.frameworks = [];
      throw error;
    }
  }

  /**
   * Fetch all compliances from API (across all frameworks/policies/subpolicies)
   */
  async fetchAllCompliances() {
    try {
      // Get all compliances using the audit management endpoint (which returns all compliances)
      const response = await axiosInstance.get('/api/compliance/all-for-audit-management/public/', {
        timeout: 60000
      });

      if (response.data.success && Array.isArray(response.data.compliances)) {
        this.dataStore.compliances = response.data.compliances;
      } else if (Array.isArray(response.data)) {
        this.dataStore.compliances = response.data;
      } else {
        this.dataStore.compliances = [];
      }

      console.log(`[Compliance Service] Fetched ${this.dataStore.compliances.length} compliances`);
    } catch (error) {
      console.error('[Compliance Service] Error fetching compliances:', error);
      this.dataStore.compliances = [];
      throw error;
    }
  }

  /**
   * Fetch policies for a specific framework
   */
  async fetchPolicies(frameworkId) {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.COMPLIANCE_POLICIES(frameworkId), {
        timeout: 60000
      });

      let policies = [];
      if (response.data.success && response.data.policies) {
        policies = response.data.policies;
      } else if (Array.isArray(response.data)) {
        policies = response.data;
      }

      // Update the cached policies array
      // Remove old policies from this framework
      this.dataStore.policies = this.dataStore.policies.filter(p => p.FrameworkId !== frameworkId);
      // Add new policies
      this.dataStore.policies = [...this.dataStore.policies, ...policies];

      console.log(`[Compliance Service] Fetched ${policies.length} policies for framework ${frameworkId}`);
      return policies;
    } catch (error) {
      console.error('[Compliance Service] Error fetching policies:', error);
      throw error;
    }
  }

  /**
   * Fetch subpolicies for a specific policy
   */
  async fetchSubpolicies(policyId) {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.COMPLIANCE_SUBPOLICIES(policyId), {
        timeout: 60000
      });

      let subpolicies = [];
      if (response.data.success && response.data.subpolicies) {
        subpolicies = response.data.subpolicies;
      } else if (Array.isArray(response.data)) {
        subpolicies = response.data;
      }

      // Update the cached subpolicies array
      // Remove old subpolicies from this policy
      this.dataStore.subpolicies = this.dataStore.subpolicies.filter(sp => sp.PolicyId !== policyId);
      // Add new subpolicies
      this.dataStore.subpolicies = [...this.dataStore.subpolicies, ...subpolicies];

      console.log(`[Compliance Service] Fetched ${subpolicies.length} subpolicies for policy ${policyId}`);
      return subpolicies;
    } catch (error) {
      console.error('[Compliance Service] Error fetching subpolicies:', error);
      throw error;
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
    return this.dataStore.frameworks.length > 0 && this.dataStore.lastFetchTime !== null;
  }

  /**
   * Check if compliances are cached
   * @returns {boolean}
   */
  hasCompliancesCache() {
    return Array.isArray(this.dataStore.compliances) && this.dataStore.compliances.length > 0;
  }

  /**
   * Check if frameworks are cached
   * @returns {boolean}
   */
  hasFrameworksCache() {
    return Array.isArray(this.dataStore.frameworks) && this.dataStore.frameworks.length > 0;
  }

  /**
   * Clear all cached data
   */
  clearCache() {
    this.dataStore.frameworks = [];
    this.dataStore.policies = [];
    this.dataStore.subpolicies = [];
    this.dataStore.compliances = [];
    this.dataStore.lastFetchTime = null;
    this.dataStore.fetchError = null;
    console.log('[Compliance Service] Cache cleared');
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      frameworksCount: this.dataStore.frameworks.length,
      policiesCount: this.dataStore.policies.length,
      subpoliciesCount: this.dataStore.subpolicies.length,
      compliancesCount: this.dataStore.compliances.length,
      lastFetchTime: this.dataStore.lastFetchTime,
      isFetching: this.dataStore.isFetching,
      hasError: !!this.dataStore.fetchError
    };
  }
}

// Export singleton instance
const complianceDataService = new ComplianceService();
export default complianceDataService;

