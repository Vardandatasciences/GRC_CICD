/**
 * Homepage Service - Centralized Data Management
 * 
 * This service handles:
 * 1. Fetching all homepage-related data on login
 * 2. Caching data in memory for instant access
 * 3. Providing cached data to components
 */
import { axiosInstance } from '@/config/api.js';
import { API_ENDPOINTS } from '../config/api.js';

class HomepageService {
  constructor() {
    // Centralized data store
    this.dataStore = {
      approvedFrameworks: [],
      homepageDataByFramework: {}, // { frameworkId: homepageData } or 'all': homepageData
      
      // Module metrics cache (for fallback endpoints)
      policyMetrics: null,
      complianceMetrics: null,
      riskMetrics: null,
      incidentMetrics: null,
      auditorMetrics: null,
      
      // Policy data cache
      policyData: null,
      
      lastFetchTime: null,
      lastMetricsFetchTime: null,
      isFetching: false,
      fetchError: null
    };
    
    // Cache validity duration (5 minutes)
    this.CACHE_VALIDITY_MS = 5 * 60 * 1000;
  }

  /**
   * Fetch all homepage data and cache it
   */
  async fetchAllHomepageData() {
    if (this.dataStore.isFetching) {
      console.log('[Homepage Service] Already fetching, skipping duplicate request');
      return this.dataStore;
    }

    this.dataStore.isFetching = true;
    console.log('[Homepage Service] 🚀 Starting homepage data prefetch...');

    try {
      // Fetch approved frameworks
      await this.fetchApprovedFrameworks();

      this.dataStore.lastFetchTime = new Date();
      this.dataStore.fetchError = null;
      
      console.log(`[Homepage Service] ✅ Prefetch complete - Approved frameworks: ${this.dataStore.approvedFrameworks.length}`);
      
      return this.dataStore;
    } catch (error) {
      console.error('[Homepage Service] ❌ Prefetch failed:', error);
      this.dataStore.fetchError = error.message;
      throw error;
    } finally {
      this.dataStore.isFetching = false;
    }
  }

  /**
   * Fetch approved frameworks from API
   */
  async fetchApprovedFrameworks() {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.FRAMEWORKS_APPROVED_ACTIVE, {
        timeout: 60000
      });

      if (response.data && response.data.success && response.data.data) {
        this.dataStore.approvedFrameworks = response.data.data;
      } else if (Array.isArray(response.data)) {
        this.dataStore.approvedFrameworks = response.data;
      } else {
        this.dataStore.approvedFrameworks = [];
      }

      console.log(`[Homepage Service] Fetched ${this.dataStore.approvedFrameworks.length} approved frameworks`);
    } catch (error) {
      console.error('[Homepage Service] Error fetching approved frameworks:', error);
      this.dataStore.approvedFrameworks = [];
      throw error;
    }
  }

  /**
   * Get comprehensive homepage data
   * @param {number|null} frameworkId - Optional framework ID to filter data
   * @returns {Promise} Homepage data including policies, metrics, etc.
   */
  async getHomeContent(frameworkId = null) {
    try {
      console.log('');
      console.log('🌐 ================================================');
      console.log('🌐 HOMEPAGE SERVICE - API CALL');
      console.log('🌐 ================================================');
      console.log('📥 Input frameworkId:', frameworkId);
      
      const url = API_ENDPOINTS.HOMEPAGE_DATA(frameworkId);
      console.log('🔗 Full API URL:', url);
      console.log('🔐 withCredentials: true');
      console.log('🌐 ================================================');
      console.log('🌐 Sending GET request...');
      
      const response = await axiosInstance.get(url, {
        withCredentials: true,
        timeout: 60000
      });
      
      console.log('🌐 ================================================');
      console.log('🌐 RESPONSE RECEIVED');
      console.log('🌐 ================================================');
      console.log('📊 Status:', response.status);
      console.log('📊 Status Text:', response.statusText);
      console.log('📊 Response data:', response.data);
      console.log('🌐 ================================================');
      console.log('');
      
      // Cache the response by framework ID
      const cacheKey = frameworkId ? frameworkId : 'all';
      if (response.data && response.data.success) {
        this.dataStore.homepageDataByFramework[cacheKey] = response.data;
      }
      
      return response.data;
    } catch (error) {
      console.log('');
      console.log('🌐 ================================================');
      console.error('❌ ERROR IN HOMEPAGE SERVICE');
      console.log('🌐 ================================================');
      console.error('❌ Error:', error);
      console.error('❌ Error message:', error.message);
      console.error('❌ Error response:', error.response);
      console.error('❌ Error response data:', error.response?.data);
      console.error('❌ Error response status:', error.response?.status);
      console.log('🌐 ================================================');
      console.log('');
      throw error;
    }
  }

  /**
   * Get all frameworks data
   * @returns {Promise} Aggregated data for all frameworks
   */
  async getAllFrameworksData() {
    try {
      console.log('');
      console.log('🌐 ================================================');
      console.log('🌐 HOMEPAGE SERVICE - ALL FRAMEWORKS API CALL');
      console.log('🌐 ================================================');
      
      const url = API_ENDPOINTS.HOMEPAGE_ALL_FRAMEWORKS;
      console.log('🔗 Full API URL:', url);
      console.log('🔐 withCredentials: true');
      console.log('🌐 ================================================');
      console.log('🌐 Sending GET request...');
      
      const response = await axiosInstance.get(url, {
        withCredentials: true,
        timeout: 60000
      });
      
      console.log('🌐 ================================================');
      console.log('🌐 ALL FRAMEWORKS RESPONSE RECEIVED');
      console.log('🌐 ================================================');
      console.log('📊 Status:', response.status);
      console.log('📊 Status Text:', response.statusText);
      console.log('📊 Response data:', JSON.stringify(response.data, null, 2));
      
      if (response.data?.frameworks) {
        console.log(`📊 Total Frameworks: ${response.data.frameworks.length}`);
        console.log('📊 Frameworks Breakdown:');
        response.data.frameworks.forEach((fw, idx) => {
          console.log(`   ${idx + 1}. ${fw.name} (ID: ${fw.id})`);
          console.log(`      Policies - Active: ${fw.stats?.activePolicies || 0}, Inactive: ${fw.stats?.inactivePolicies || 0}`);
          console.log(`      Compliances - Active: ${fw.stats?.activeCompliances || 0}, Inactive: ${fw.stats?.inactiveCompliances || 0}`);
          console.log(`      Risks - Active: ${fw.stats?.activeRisks || 0}, Inactive: ${fw.stats?.inactiveRisks || 0}`);
          console.log(`      Incidents - Active: ${fw.stats?.activeIncidents || 0}, Inactive: ${fw.stats?.inactiveIncidents || 0}`);
          console.log(`      Audits - Active: ${fw.stats?.activeAudits || 0}, Inactive: ${fw.stats?.inactiveAudits || 0}`);
        });
      }
      
      if (response.data?.hero?.stats) {
        console.log('');
        console.log('📊 ========================================');
        console.log('📊 ALL FRAMEWORKS AGGREGATED DATA');
        console.log('📊 ========================================');
        console.log('📋 POLICIES:');
        console.log(`   Total (All): ${response.data.hero.stats.totalPoliciesAll || 0}`);
        console.log(`   Active: ${response.data.hero.stats.activePolicies || 0}`);
        console.log(`   Inactive: ${response.data.hero.stats.inactivePolicies || 0}`);
        console.log('✅ COMPLIANCES:');
        console.log(`   Total (All): ${response.data.hero.stats.totalCompliancesAll || 0}`);
        console.log(`   Active: ${response.data.hero.stats.activeCompliances || 0}`);
        console.log(`   Inactive: ${response.data.hero.stats.inactiveCompliances || 0}`);
        console.log('⚠️ RISKS:');
        console.log(`   Total: ${response.data.hero.stats.totalRisks || 0}`);
        console.log(`   Active: ${response.data.hero.stats.activeRisks || 0}`);
        console.log(`   Inactive: ${response.data.hero.stats.inactiveRisks || 0}`);
        console.log(`   Mitigated: ${response.data.hero.stats.mitigatedRisks || 0}`);
        console.log('🚨 INCIDENTS:');
        console.log(`   Total: ${response.data.hero.stats.totalIncidents || 0}`);
        console.log(`   Active: ${response.data.hero.stats.activeIncidents || 0}`);
        console.log(`   Inactive: ${response.data.hero.stats.inactiveIncidents || 0}`);
        console.log(`   Resolved: ${response.data.hero.stats.resolvedIncidents || 0}`);
        console.log('🔍 AUDITS:');
        console.log(`   Total: ${response.data.hero.stats.totalAudits || 0}`);
        console.log(`   Active: ${response.data.hero.stats.activeAudits || 0}`);
        console.log(`   Inactive: ${response.data.hero.stats.inactiveAudits || 0}`);
        console.log(`   Completed: ${response.data.hero.stats.completedAudits || 0}`);
        console.log('📊 ========================================');
      }
      
      console.log('🌐 ================================================');
      console.log('');
      
      // Cache the all frameworks response
      if (response.data && response.data.success) {
        this.dataStore.homepageDataByFramework['all'] = response.data;
      }
      
      return response.data;
    } catch (error) {
      console.log('');
      console.log('🌐 ================================================');
      console.error('❌ ERROR IN ALL FRAMEWORKS SERVICE');
      console.log('🌐 ================================================');
      console.error('❌ Error:', error);
      console.error('❌ Error message:', error.message);
      console.error('❌ Error response:', error.response);
      console.error('❌ Error response data:', error.response?.data);
      console.error('❌ Error response status:', error.response?.status);
      console.log('🌐 ================================================');
      console.log('');
      throw error;
    }
  }

  /**
   * Get policy details for popup
   * @param {number} policyId - Policy ID
   * @returns {Promise} Policy details
   */
  async getPolicyDetails(policyId) {
    try {
      const url = API_ENDPOINTS.HOME_POLICY_DETAILS(policyId);
      const response = await axiosInstance.get(url, {
        withCredentials: true,
        timeout: 60000
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching policy details:', error);
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
   * Check if approved frameworks are cached
   * @returns {boolean}
   */
  hasApprovedFrameworksCache() {
    return Array.isArray(this.dataStore.approvedFrameworks) && this.dataStore.approvedFrameworks.length > 0;
  }

  /**
   * Check if homepage data is cached for a specific framework
   * @param {number|null|string} frameworkId - Framework ID or 'all'
   * @returns {boolean}
   */
  hasHomepageDataCache(frameworkId = null) {
    const cacheKey = frameworkId ? frameworkId : 'all';
    return !!this.dataStore.homepageDataByFramework[cacheKey];
  }

  /**
   * Get homepage data from cache
   * @param {number|null|string} frameworkId - Framework ID or 'all'
   * @returns {any|null} Cached homepage data
   */
  getHomepageData(frameworkId = null) {
    const cacheKey = frameworkId ? frameworkId : 'all';
    return this.dataStore.homepageDataByFramework[cacheKey] || null;
  }

  /**
   * Check if data is cached and fresh
   * @returns {boolean}
   */
  hasValidCache() {
    return this.dataStore.approvedFrameworks.length > 0 && this.dataStore.lastFetchTime !== null;
  }

  /**
   * Check if cache is fresh (within validity period)
   * @param {number|null} timestamp - Timestamp to check, or null to check lastFetchTime
   * @returns {boolean}
   */
  isCacheFresh(timestamp = null) {
    const checkTime = timestamp || this.dataStore.lastFetchTime;
    if (!checkTime) return false;
    
    const now = new Date().getTime();
    const cacheTime = checkTime instanceof Date ? checkTime.getTime() : checkTime;
    return (now - cacheTime) < this.CACHE_VALIDITY_MS;
  }

  /**
   * Set module metrics cache
   * @param {string} metricType - Type of metric (policyMetrics, complianceMetrics, etc.)
   * @param {any} data - Metric data
   */
  setModuleMetrics(metricType, data) {
    if (Object.prototype.hasOwnProperty.call(this.dataStore, metricType)) {
      this.dataStore[metricType] = data;
      this.dataStore.lastMetricsFetchTime = new Date();
      console.log(`[Homepage Service] Cached ${metricType}`);
    }
  }

  /**
   * Get module metrics from cache
   * @param {string} metricType - Type of metric
   * @returns {any|null} Cached metric data or null
   */
  getModuleMetrics(metricType) {
    if (!this.isCacheFresh(this.dataStore.lastMetricsFetchTime)) {
      return null;
    }
    return this.dataStore[metricType] || null;
  }

  /**
   * Check if module metrics are cached and fresh
   * @returns {boolean}
   */
  hasValidModuleMetricsCache() {
    return this.isCacheFresh(this.dataStore.lastMetricsFetchTime) &&
           (this.dataStore.policyMetrics !== null ||
            this.dataStore.complianceMetrics !== null ||
            this.dataStore.riskMetrics !== null ||
            this.dataStore.incidentMetrics !== null ||
            this.dataStore.auditorMetrics !== null);
  }

  /**
   * Set policy data cache
   * @param {any} data - Policy data
   */
  setPolicyData(data) {
    this.dataStore.policyData = data;
    this.dataStore.lastFetchTime = new Date();
    console.log('[Homepage Service] Cached policy data');
  }

  /**
   * Get policy data from cache
   * @returns {any|null} Cached policy data or null
   */
  getPolicyData() {
    if (!this.isCacheFresh()) {
      return null;
    }
    return this.dataStore.policyData;
  }

  /**
   * Clear all cached data
   */
  clearCache() {
    this.dataStore.approvedFrameworks = [];
    this.dataStore.homepageDataByFramework = {};
    this.dataStore.policyMetrics = null;
    this.dataStore.complianceMetrics = null;
    this.dataStore.riskMetrics = null;
    this.dataStore.incidentMetrics = null;
    this.dataStore.auditorMetrics = null;
    this.dataStore.policyData = null;
    this.dataStore.lastFetchTime = null;
    this.dataStore.lastMetricsFetchTime = null;
    this.dataStore.fetchError = null;
    console.log('[Homepage Service] Cache cleared');
  }

  /**
   * Clear homepage data cache for a specific framework
   * @param {number|null|string} frameworkId - Framework ID or 'all'
   */
  clearHomepageDataCache(frameworkId = null) {
    const cacheKey = frameworkId ? frameworkId : 'all';
    delete this.dataStore.homepageDataByFramework[cacheKey];
    console.log(`[Homepage Service] Cleared homepage data cache for framework: ${cacheKey}`);
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      approvedFrameworksCount: this.dataStore.approvedFrameworks.length,
      homepageDataCachedCount: Object.keys(this.dataStore.homepageDataByFramework).length,
      lastFetchTime: this.dataStore.lastFetchTime,
      isFetching: this.dataStore.isFetching,
      hasError: !!this.dataStore.fetchError
    };
  }
}

// Export singleton instance
const homepageDataService = new HomepageService();
export default homepageDataService;