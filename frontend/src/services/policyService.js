/**
 * Policy Service - Centralized Data Management
 *
 * This service handles:
 * 1. Prefetching and caching common policy datasets (frameworks, summaries, etc.)
 * 2. Providing cached data to policy-related components for instant loading
 * 3. Offering helpers to update or clear cached data when mutations occur
 */

import { axiosInstance, API_ENDPOINTS } from '@/config/api.js';

class PolicyService {
  constructor() {
    this.dataStore = {
      frameworksList: [],      // From FRAMEWORKS endpoint (lightweight list)
      policyFrameworks: [],    // From all-policies frameworks endpoint (detailed)
      explorerFrameworks: [],  // From framework explorer endpoint
      explorerSummary: null,
      lastFetchTime: null,
      isFetching: false,
      fetchError: null
    };
  }

  /**
   * Prefetch all major policy data sets
   */
  async fetchAllPolicyData() {
    if (this.dataStore.isFetching) {
      console.log('[Policy Service] Already fetching, skipping duplicate request');
      return this.dataStore;
    }

    this.dataStore.isFetching = true;
    console.log('[Policy Service] 🚀 Starting policy data prefetch...');

    try {
      await Promise.all([
        this.fetchFrameworksList(),
        this.fetchAllPoliciesFrameworks(),
        this.fetchFrameworkExplorerData()
      ]);

      this.dataStore.lastFetchTime = new Date();
      this.dataStore.fetchError = null;

      console.log('[Policy Service] ✅ Prefetch complete', {
        frameworksList: this.dataStore.frameworksList.length,
        policyFrameworks: this.dataStore.policyFrameworks.length,
        explorerFrameworks: this.dataStore.explorerFrameworks.length
      });

      return this.dataStore;
    } catch (error) {
      console.error('[Policy Service] ❌ Prefetch failed:', error);
      this.dataStore.fetchError = error.message;
      throw error;
    } finally {
      this.dataStore.isFetching = false;
    }
  }

  /**
   * Fetch frameworks list (lightweight) from FRAMEWORKS endpoint
   */
  async fetchFrameworksList() {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.FRAMEWORKS, {
        timeout: 60000
      });

      if (Array.isArray(response.data)) {
        this.dataStore.frameworksList = response.data;
      } else if (Array.isArray(response.data?.frameworks)) {
        this.dataStore.frameworksList = response.data.frameworks;
      } else {
        this.dataStore.frameworksList = [];
      }

      console.log(`[Policy Service] Fetched ${this.dataStore.frameworksList.length} frameworks (list)`);
    } catch (error) {
      console.error('[Policy Service] Error fetching frameworks list:', error);
      this.dataStore.frameworksList = [];
      throw error;
    }
  }

  /**
   * Fetch detailed frameworks used in All Policies view
   */
  async fetchAllPoliciesFrameworks() {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.POLICY_ALL_POLICIES_FRAMEWORKS, {
        timeout: 60000
      });

      if (Array.isArray(response.data)) {
        this.dataStore.policyFrameworks = response.data;
      } else if (Array.isArray(response.data?.frameworks)) {
        this.dataStore.policyFrameworks = response.data.frameworks;
      } else {
        this.dataStore.policyFrameworks = [];
      }

      console.log(`[Policy Service] Fetched ${this.dataStore.policyFrameworks.length} policy frameworks`);
    } catch (error) {
      console.error('[Policy Service] Error fetching policy frameworks:', error);
      this.dataStore.policyFrameworks = [];
      throw error;
    }
  }

  /**
   * Fetch framework explorer data (frameworks + summary)
   * @param {object} params Optional query parameters (for filters)
   */
  async fetchFrameworkExplorerData(params = {}) {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.FRAMEWORK_EXPLORER, {
        params,
        timeout: 60000
      });

      if (response.data) {
        this.dataStore.explorerFrameworks = response.data.frameworks || [];
        this.dataStore.explorerSummary = response.data.summary || null;
      } else {
        this.dataStore.explorerFrameworks = [];
        this.dataStore.explorerSummary = null;
      }

      console.log(`[Policy Service] Fetched ${this.dataStore.explorerFrameworks.length} explorer frameworks`);
    } catch (error) {
      console.error('[Policy Service] Error fetching framework explorer data:', error);
      this.dataStore.explorerFrameworks = [];
      this.dataStore.explorerSummary = null;
      throw error;
    }
  }

  // ===== Getters =====

  getFrameworksList() {
    return this.dataStore.frameworksList;
  }

  getAllPoliciesFrameworks() {
    return this.dataStore.policyFrameworks;
  }

  getFrameworkExplorerFrameworks() {
    return this.dataStore.explorerFrameworks;
  }

  getFrameworkExplorerSummary() {
    return this.dataStore.explorerSummary;
  }

  // ===== Setters =====

  setFrameworksList(frameworks = []) {
    this.dataStore.frameworksList = frameworks;
    this.dataStore.lastFetchTime = new Date();
  }

  setAllPoliciesFrameworks(frameworks = []) {
    this.dataStore.policyFrameworks = frameworks;
    this.dataStore.lastFetchTime = new Date();
  }

  setFrameworkExplorerData(frameworks = [], summary = null) {
    this.dataStore.explorerFrameworks = frameworks;
    this.dataStore.explorerSummary = summary;
    this.dataStore.lastFetchTime = new Date();
  }

  // ===== Cache Checks =====

  hasFrameworksListCache() {
    return Array.isArray(this.dataStore.frameworksList) && this.dataStore.frameworksList.length > 0;
  }

  hasAllPoliciesFrameworksCache() {
    return Array.isArray(this.dataStore.policyFrameworks) && this.dataStore.policyFrameworks.length > 0;
  }

  hasFrameworkExplorerCache() {
    return Array.isArray(this.dataStore.explorerFrameworks) && this.dataStore.explorerFrameworks.length > 0;
  }

  // ===== Maintenance Helpers =====

  clearCache() {
    this.dataStore.frameworksList = [];
    this.dataStore.policyFrameworks = [];
    this.dataStore.explorerFrameworks = [];
    this.dataStore.explorerSummary = null;
    this.dataStore.lastFetchTime = null;
    this.dataStore.fetchError = null;
    console.log('[Policy Service] Cache cleared');
  }

  getCacheStats() {
    return {
      frameworksListCount: this.dataStore.frameworksList.length,
      policyFrameworksCount: this.dataStore.policyFrameworks.length,
      explorerFrameworksCount: this.dataStore.explorerFrameworks.length,
      hasSummary: !!this.dataStore.explorerSummary,
      lastFetchTime: this.dataStore.lastFetchTime,
      isFetching: this.dataStore.isFetching,
      hasError: !!this.dataStore.fetchError
    };
  }
}

const policyDataService = new PolicyService();
export default policyDataService;


