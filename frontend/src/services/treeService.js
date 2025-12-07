/**
 * Tree Service - Centralized Data Management
 * 
 * This service handles:
 * 1. Fetching all tree/hierarchy-related data on login
 * 2. Caching data in memory for instant access
 * 3. Providing cached data to components
 */

import { axiosInstance } from '@/config/api.js';
import { API_ENDPOINTS } from '@/config/api.js';

class TreeService {
  constructor() {
    // Centralized data store
    this.dataStore = {
      frameworks: [],
      policiesByFramework: {}, // { frameworkId: [policies] }
      subpoliciesByPolicy: {}, // { policyId: [subpolicies] }
      compliancesBySubpolicy: {}, // { subpolicyId: [compliances] }
      risksByCompliance: {}, // { complianceId: [risks] }
      selectedFrameworkId: null,
      lastFetchTime: null,
      isFetching: false,
      fetchError: null
    };
  }

  /**
   * Fetch all tree data and cache it
   */
  async fetchAllTreeData() {
    if (this.dataStore.isFetching) {
      console.log('[Tree Service] Already fetching, skipping duplicate request');
      return this.dataStore;
    }

    this.dataStore.isFetching = true;
    console.log('[Tree Service] 🚀 Starting tree data prefetch...');

    try {
      // Fetch frameworks first
      await this.fetchFrameworks();
      
      // Get selected framework from session or localStorage
      const selectedFrameworkId = await this.getSelectedFramework();
      if (selectedFrameworkId) {
        this.dataStore.selectedFrameworkId = selectedFrameworkId;
        // Fetch policies for the selected framework
        await this.fetchPolicies(selectedFrameworkId);
      }

      this.dataStore.lastFetchTime = new Date();
      this.dataStore.fetchError = null;
      
      console.log(`[Tree Service] ✅ Prefetch complete - Total frameworks: ${this.dataStore.frameworks.length}`);
      if (selectedFrameworkId) {
        console.log(`[Tree Service] ✅ Prefetch complete - Policies for framework ${selectedFrameworkId}: ${this.dataStore.policiesByFramework[selectedFrameworkId]?.length || 0}`);
      }
      
      return this.dataStore;
    } catch (error) {
      console.error('[Tree Service] ❌ Prefetch failed:', error);
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
      const response = await axiosInstance.get(API_ENDPOINTS.TREE_GET_FRAMEWORKS, {
        timeout: 60000
      });

      if (response.data.status === 'success') {
        this.dataStore.frameworks = response.data.data;
        console.log(`[Tree Service] Fetched ${this.dataStore.frameworks.length} frameworks`);
      } else {
        this.dataStore.frameworks = [];
      }
    } catch (error) {
      console.error('[Tree Service] Error fetching frameworks:', error);
      this.dataStore.frameworks = [];
      throw error;
    }
  }

  /**
   * Get selected framework from session or localStorage
   */
  async getSelectedFramework() {
    try {
      // Try to get from backend session first
      const response = await axiosInstance.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED);
      const frameworkIdFromSession = response?.data?.frameworkId;
      if (frameworkIdFromSession) {
        return parseInt(frameworkIdFromSession);
      }
    } catch (error) {
      console.log('[Tree Service] Could not get selected framework from session:', error.message);
    }

    // Fallback to localStorage
    try {
      const stored = localStorage.getItem('selectedFrameworkId') || localStorage.getItem('frameworkId');
      if (stored && stored !== '' && stored !== 'null') {
        return parseInt(stored);
      }
    } catch (error) {
      console.log('[Tree Service] Could not read framework selection from localStorage:', error.message);
    }

    return null;
  }

  /**
   * Fetch policies for a framework
   * @param {number} frameworkId - The framework ID
   */
  async fetchPolicies(frameworkId) {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.TREE_GET_POLICIES(frameworkId), {
        timeout: 60000
      });

      if (response.data.status === 'success') {
        this.dataStore.policiesByFramework[frameworkId] = response.data.data.map(item => ({
          ...item,
          type: 'policy',
          id: item.PolicyId
        }));
        console.log(`[Tree Service] Fetched ${this.dataStore.policiesByFramework[frameworkId].length} policies for framework ${frameworkId}`);
      } else {
        this.dataStore.policiesByFramework[frameworkId] = [];
      }
    } catch (error) {
      console.error(`[Tree Service] Error fetching policies for framework ${frameworkId}:`, error);
      this.dataStore.policiesByFramework[frameworkId] = [];
      throw error;
    }
  }

  /**
   * Fetch subpolicies for a policy
   * @param {number} policyId - The policy ID
   */
  async fetchSubpolicies(policyId) {
    try {
      // Check if already cached
      if (this.dataStore.subpoliciesByPolicy[policyId]) {
        console.log(`[Tree Service] Using cached subpolicies for policy ${policyId}`);
        return this.dataStore.subpoliciesByPolicy[policyId];
      }

      const response = await axiosInstance.get(API_ENDPOINTS.TREE_GET_SUBPOLICIES(policyId), {
        timeout: 60000
      });

      if (response.data.status === 'success') {
        this.dataStore.subpoliciesByPolicy[policyId] = response.data.data.map(item => ({
          ...item,
          type: 'subpolicy',
          id: item.SubPolicyId,
          parentPolicyId: policyId
        }));
        console.log(`[Tree Service] Fetched ${this.dataStore.subpoliciesByPolicy[policyId].length} subpolicies for policy ${policyId}`);
      } else {
        this.dataStore.subpoliciesByPolicy[policyId] = [];
      }

      return this.dataStore.subpoliciesByPolicy[policyId];
    } catch (error) {
      console.error(`[Tree Service] Error fetching subpolicies for policy ${policyId}:`, error);
      this.dataStore.subpoliciesByPolicy[policyId] = [];
      throw error;
    }
  }

  /**
   * Fetch compliances for a subpolicy
   * @param {number} subpolicyId - The subpolicy ID
   */
  async fetchCompliances(subpolicyId) {
    try {
      // Check if already cached
      if (this.dataStore.compliancesBySubpolicy[subpolicyId]) {
        console.log(`[Tree Service] Using cached compliances for subpolicy ${subpolicyId}`);
        return this.dataStore.compliancesBySubpolicy[subpolicyId];
      }

      const response = await axiosInstance.get(API_ENDPOINTS.TREE_GET_COMPLIANCES(subpolicyId), {
        timeout: 60000
      });

      if (response.data.status === 'success') {
        this.dataStore.compliancesBySubpolicy[subpolicyId] = response.data.data.map(item => ({
          ...item,
          type: 'compliance',
          id: item.ComplianceId,
          parentSubPolicyId: subpolicyId
        }));
        console.log(`[Tree Service] Fetched ${this.dataStore.compliancesBySubpolicy[subpolicyId].length} compliances for subpolicy ${subpolicyId}`);
      } else {
        this.dataStore.compliancesBySubpolicy[subpolicyId] = [];
      }

      return this.dataStore.compliancesBySubpolicy[subpolicyId];
    } catch (error) {
      console.error(`[Tree Service] Error fetching compliances for subpolicy ${subpolicyId}:`, error);
      this.dataStore.compliancesBySubpolicy[subpolicyId] = [];
      throw error;
    }
  }

  /**
   * Fetch risks for a compliance
   * @param {number} complianceId - The compliance ID
   */
  async fetchRisks(complianceId) {
    try {
      // Check if already cached
      if (this.dataStore.risksByCompliance[complianceId]) {
        console.log(`[Tree Service] Using cached risks for compliance ${complianceId}`);
        return this.dataStore.risksByCompliance[complianceId];
      }

      const response = await axiosInstance.get(API_ENDPOINTS.TREE_GET_RISKS(complianceId), {
        timeout: 60000
      });

      if (response.data.status === 'success') {
        this.dataStore.risksByCompliance[complianceId] = response.data.data.map(item => ({
          ...item,
          type: 'risk',
          id: item.RiskId,
          parentComplianceId: complianceId
        }));
        console.log(`[Tree Service] Fetched ${this.dataStore.risksByCompliance[complianceId].length} risks for compliance ${complianceId}`);
      } else {
        this.dataStore.risksByCompliance[complianceId] = [];
      }

      return this.dataStore.risksByCompliance[complianceId];
    } catch (error) {
      console.error(`[Tree Service] Error fetching risks for compliance ${complianceId}:`, error);
      this.dataStore.risksByCompliance[complianceId] = [];
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
   * Check if frameworks are cached
   * @returns {boolean}
   */
  hasValidCache() {
    return this.dataStore.frameworks.length > 0 && this.dataStore.lastFetchTime !== null;
  }

  /**
   * Get policies for a framework
   * @param {number} frameworkId - The framework ID
   * @returns {Array} Policies for the framework
   */
  getPolicies(frameworkId) {
    return this.dataStore.policiesByFramework[frameworkId] || [];
  }

  /**
   * Get subpolicies for a policy
   * @param {number} policyId - The policy ID
   * @returns {Array} Subpolicies for the policy
   */
  getSubpolicies(policyId) {
    return this.dataStore.subpoliciesByPolicy[policyId] || [];
  }

  /**
   * Get compliances for a subpolicy
   * @param {number} subpolicyId - The subpolicy ID
   * @returns {Array} Compliances for the subpolicy
   */
  getCompliances(subpolicyId) {
    return this.dataStore.compliancesBySubpolicy[subpolicyId] || [];
  }

  /**
   * Get risks for a compliance
   * @param {number} complianceId - The compliance ID
   * @returns {Array} Risks for the compliance
   */
  getRisks(complianceId) {
    return this.dataStore.risksByCompliance[complianceId] || [];
  }

  /**
   * Clear all cached data
   */
  clearCache() {
    this.dataStore.frameworks = [];
    this.dataStore.policiesByFramework = {};
    this.dataStore.subpoliciesByPolicy = {};
    this.dataStore.compliancesBySubpolicy = {};
    this.dataStore.risksByCompliance = {};
    this.dataStore.selectedFrameworkId = null;
    this.dataStore.lastFetchTime = null;
    this.dataStore.fetchError = null;
    console.log('[Tree Service] Cache cleared');
  }

  /**
   * Clear cached data for a specific framework
   * @param {number} frameworkId - The framework ID
   */
  clearFrameworkCache(frameworkId) {
    delete this.dataStore.policiesByFramework[frameworkId];
    
    // Clear all related subpolicies, compliances, and risks
    Object.keys(this.dataStore.subpoliciesByPolicy).forEach(policyId => {
      const policies = this.dataStore.policiesByFramework[frameworkId] || [];
      if (policies.some(p => p.id === parseInt(policyId))) {
        delete this.dataStore.subpoliciesByPolicy[policyId];
      }
    });
    
    console.log(`[Tree Service] Cache cleared for framework ${frameworkId}`);
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      frameworksCount: this.dataStore.frameworks.length,
      policiesCached: Object.keys(this.dataStore.policiesByFramework).length,
      subpoliciesCached: Object.keys(this.dataStore.subpoliciesByPolicy).length,
      compliancesCached: Object.keys(this.dataStore.compliancesBySubpolicy).length,
      risksCached: Object.keys(this.dataStore.risksByCompliance).length,
      selectedFrameworkId: this.dataStore.selectedFrameworkId,
      lastFetchTime: this.dataStore.lastFetchTime,
      isFetching: this.dataStore.isFetching,
      hasError: !!this.dataStore.fetchError
    };
  }
}

// Export singleton instance
const treeDataService = new TreeService();
export default treeDataService;

