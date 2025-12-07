/**
 * Auditor Service - Centralized Data Management
 * 
 * This service handles:
 * 1. Fetching all auditor-related data on login
 * 2. Caching data in memory for instant access
 * 3. Providing cached data to components
 */

import { axiosInstance } from '@/config/api.js';
import { API_ENDPOINTS } from '@/config/api.js';

class AuditorService {
  constructor() {
    // Centralized data store
    this.dataStore = {
      audits: [],
      businessUnits: [],
      lastFetchTime: null,
      isFetching: false,
      fetchError: null
    };
  }

  /**
   * Fetch all auditor data and cache it
   */
  async fetchAllAuditorData() {
    if (this.dataStore.isFetching) {
      console.log('[Auditor Service] Already fetching, skipping duplicate request');
      return this.dataStore;
    }

    this.dataStore.isFetching = true;
    console.log('[Auditor Service] 🚀 Starting auditor data prefetch...');

    try {
      // Fetch all auditor-related datasets
      await Promise.all([
        this.fetchAudits(),
        this.fetchBusinessUnits()
      ]);

      this.dataStore.lastFetchTime = new Date();
      this.dataStore.fetchError = null;
      
      console.log(`[Auditor Service] ✅ Prefetch complete - Total audits: ${this.dataStore.audits.length}`);
      console.log(`[Auditor Service] ✅ Prefetch complete - Total business units: ${this.dataStore.businessUnits.length}`);
      
      return this.dataStore;
    } catch (error) {
      console.error('[Auditor Service] ❌ Prefetch failed:', error);
      this.dataStore.fetchError = error.message;
      throw error;
    } finally {
      this.dataStore.isFetching = false;
    }
  }

  /**
   * Fetch audits from API
   */
  async fetchAudits() {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.AUDIT_MY_AUDITS, {
        timeout: 60000
      });

      // Handle both old and new response formats
      if (Array.isArray(response.data)) {
        this.dataStore.audits = response.data;
      } else if (response.data?.success && Array.isArray(response.data?.audits)) {
        this.dataStore.audits = response.data.audits;
      } else if (response.data?.success && Array.isArray(response.data?.data)) {
        this.dataStore.audits = response.data.data;
      } else {
        this.dataStore.audits = [];
      }

      console.log(`[Auditor Service] Fetched ${this.dataStore.audits.length} audits`);
    } catch (error) {
      console.error('[Auditor Service] Error fetching audits:', error);
      this.dataStore.audits = [];
      throw error;
    }
  }

  /**
   * Fetch business units from API
   */
  async fetchBusinessUnits() {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.BUSINESS_UNITS, {
        timeout: 60000
      });

      if (Array.isArray(response.data)) {
        this.dataStore.businessUnits = response.data;
      } else if (response.data?.success && Array.isArray(response.data?.data)) {
        this.dataStore.businessUnits = response.data.data;
      } else if (response.data?.success && Array.isArray(response.data?.businessUnits)) {
        this.dataStore.businessUnits = response.data.businessUnits;
      } else {
        this.dataStore.businessUnits = [];
      }

      console.log(`[Auditor Service] Fetched ${this.dataStore.businessUnits.length} business units`);
    } catch (error) {
      console.error('[Auditor Service] Error fetching business units:', error);
      this.dataStore.businessUnits = [];
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
    return this.dataStore.audits.length > 0 && this.dataStore.lastFetchTime !== null;
  }

  /**
   * Check if audits are cached
   * @returns {boolean}
   */
  hasAuditsCache() {
    return Array.isArray(this.dataStore.audits) && this.dataStore.audits.length > 0;
  }

  /**
   * Check if business units are cached
   * @returns {boolean}
   */
  hasBusinessUnitsCache() {
    return Array.isArray(this.dataStore.businessUnits) && this.dataStore.businessUnits.length > 0;
  }

  /**
   * Clear all cached data
   */
  clearCache() {
    this.dataStore.audits = [];
    this.dataStore.businessUnits = [];
    this.dataStore.lastFetchTime = null;
    this.dataStore.fetchError = null;
    console.log('[Auditor Service] Cache cleared');
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      auditsCount: this.dataStore.audits.length,
      businessUnitsCount: this.dataStore.businessUnits.length,
      lastFetchTime: this.dataStore.lastFetchTime,
      isFetching: this.dataStore.isFetching,
      hasError: !!this.dataStore.fetchError
    };
  }
}

// Export singleton instance
const auditorDataService = new AuditorService();
export default auditorDataService;

