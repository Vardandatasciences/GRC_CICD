/**
 * Risk Service - Centralized Data Management
 * 
 * This service handles:
 * 1. Fetching all risk-related data on login
 * 2. Caching data in memory for instant access
 * 3. Providing cached data to components
 */

import { axiosInstance } from '@/config/api.js';
import { API_ENDPOINTS } from '@/config/api.js';

class RiskService {
  constructor() {
    // Centralized data store
    this.dataStore = {
      risks: [],
      riskInstances: [],
      lastFetchTime: null,
      isFetching: false,
      fetchError: null
    };
  }

  /**
   * Fetch all risk data and cache it
   */
  async fetchAllRiskData() {
    if (this.dataStore.isFetching) {
      console.log('[Risk Service] Already fetching, skipping duplicate request');
      return this.dataStore;
    }

    this.dataStore.isFetching = true;
    console.log('[Risk Service] 🚀 Starting risk data prefetch...');

    try {
      // Fetch all risk-related datasets
      await Promise.all([
        this.fetchRisks(),
        this.fetchRiskInstances()
      ]);

      this.dataStore.lastFetchTime = new Date();
      this.dataStore.fetchError = null;
      
      console.log(`[Risk Service] ✅ Prefetch complete - Total risks: ${this.dataStore.risks.length}`);
      console.log(`[Risk Service] ✅ Prefetch complete - Total risk instances: ${this.dataStore.riskInstances.length}`);
      
      return this.dataStore;
    } catch (error) {
      console.error('[Risk Service] ❌ Prefetch failed:', error);
      this.dataStore.fetchError = error.message;
      throw error;
    } finally {
      this.dataStore.isFetching = false;
    }
  }

  /**
   * Fetch risks from API
   */
  async fetchRisks() {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.RISKS_FOR_DROPDOWN, {
        timeout: 60000
      });

      // Handle both old and new response formats
      if (response.data.success && response.data.risks) {
        this.dataStore.risks = response.data.risks;
      } else if (Array.isArray(response.data)) {
        this.dataStore.risks = response.data;
      } else {
        this.dataStore.risks = [];
      }

      console.log(`[Risk Service] Fetched ${this.dataStore.risks.length} risks`);
    } catch (error) {
      console.error('[Risk Service] Error fetching risks:', error);
      this.dataStore.risks = [];
      throw error;
    }
  }

  /**
   * Fetch risk instances from API
   */
  async fetchRiskInstances() {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.RISK_INSTANCES, {
        timeout: 60000
      });

      if (Array.isArray(response.data)) {
        this.dataStore.riskInstances = response.data;
      } else if (response.data?.success && Array.isArray(response.data?.data)) {
        this.dataStore.riskInstances = response.data.data;
      } else {
        this.dataStore.riskInstances = [];
      }

      console.log(`[Risk Service] Fetched ${this.dataStore.riskInstances.length} risk instances`);
    } catch (error) {
      console.error('[Risk Service] Error fetching risk instances:', error);
      this.dataStore.riskInstances = [];
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
    return this.dataStore.risks.length > 0 && this.dataStore.lastFetchTime !== null;
  }

  /**
   * Check if risk instances are cached
   * @returns {boolean}
   */
  hasRiskInstancesCache() {
    return Array.isArray(this.dataStore.riskInstances) && this.dataStore.riskInstances.length > 0;
  }

  /**
   * Clear all cached data
   */
  clearCache() {
    this.dataStore.risks = [];
    this.dataStore.riskInstances = [];
    this.dataStore.lastFetchTime = null;
    this.dataStore.fetchError = null;
    console.log('[Risk Service] Cache cleared');
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      risksCount: this.dataStore.risks.length,
      riskInstancesCount: this.dataStore.riskInstances.length,
      lastFetchTime: this.dataStore.lastFetchTime,
      isFetching: this.dataStore.isFetching,
      hasError: !!this.dataStore.fetchError
    };
  }
}

// Export singleton instance
const riskDataService = new RiskService();
export default riskDataService;

