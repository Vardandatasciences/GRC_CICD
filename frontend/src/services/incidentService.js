/**
 * Incident Service - Centralized Data Management
 * 
 * This service handles:
 * 1. Batch fetching of all incident-related data on login
 * 2. Caching data in memory for instant access
 * 3. Providing cached data to components
 * 
 * Usage:
 * - Call fetchAllIncidentData() on login/home page load
 * - Use getData(key) in components to get cached data
 * - Components should check for cached data before making API calls
 */

import { axiosInstance } from '@/config/api.js';
import { API_ENDPOINTS } from '@/config/api.js';

class IncidentService {
  constructor() {
    // Centralized data store
    this.dataStore = {
      // Main data arrays
      incidents: [],
      auditFindings: [],
      incidentUsers: [],
      incidentBusinessUnits: [],
      incidentCategories: [],
      incidentFrameworks: [],
      
      // Cached KPI data
      kpiData: {},
      kpiDataCacheTime: null,
      
      // Metadata
      lastFetchTime: null,
      isFetching: false,
      fetchErrors: {}
    };
  }
  
  /**
   * Main method to fetch ALL incident-related data in parallel
   * Called from HomeView.vue on login
   */
  async fetchAllIncidentData() {
    if (this.dataStore.isFetching) {
      return {
        success: true,
        total: this.dataStore.incidents.length,
        auditFindingsTotal: this.dataStore.auditFindings.length
      };
    }
    
    this.dataStore.isFetching = true;
    this.dataStore.fetchErrors = {};
    this.dataStore.auditFindings = [];
    this.dataStore.incidentUsers = [];
    this.dataStore.incidentBusinessUnits = [];
    this.dataStore.incidentCategories = [];
    this.dataStore.incidentFrameworks = [];
    
    try {
      console.log('🚀 [IncidentService] Starting comprehensive data prefetch...');
      
      // Fetch incidents, audit findings, and users in parallel
      const [incidents, auditFindings, users] = await Promise.all([
        this.fetchIncidents(),
        this.fetchAuditFindings(),
        this.fetchIncidentUsers().catch(err => {
          console.warn('Failed to fetch users during prefetch:', err);
          return [];
        })
      ]);
      
      this.dataStore.incidents = incidents || [];
      this.dataStore.auditFindings = auditFindings || [];
      this.dataStore.incidentUsers = users || [];
      this.dataStore.lastFetchTime = Date.now();
      
      const total = this.dataStore.incidents.length;
      const auditFindingsTotal = this.dataStore.auditFindings.length;
      console.log(`✅ [IncidentService] Incidents fetched: ${total}`);
      console.log(`✅ [IncidentService] Audit Findings fetched: ${auditFindingsTotal}`);
      
      // Also prefetch basic KPI data in background (non-blocking)
      this.prefetchBasicKPIs().catch(err => {
        console.warn('⚠️ [IncidentService] Failed to prefetch KPI data:', err);
      });
      
      return {
        success: true,
        total,
        auditFindingsTotal
      };
    } catch (error) {
      this.dataStore.fetchErrors.incidents = error.message;
      return {
        success: false,
        error: error.message
      };
    } finally {
      this.dataStore.isFetching = false;
    }
  }

  /**
   * Prefetch ALL dashboard and chart data (runs in background after main data is loaded)
   */
  async prefetchBasicKPIs() {
    try {
      console.log('🔄 [IncidentService] Prefetching ALL dashboard and chart data...');
      
      // Fetch dashboard data AND all chart data
      const kpiPromises = {
        counts: this.fetchIncidentCounts(),
        origins: this.fetchIncidentOrigins(),
        dashboardSummary: this.fetchDashboardSummary(),
        statusChart: this.fetchChartData('Status'),
        originChart: this.fetchChartData('Origin'),
        categoryChart: this.fetchChartData('RiskCategory'),
        priorityChart: this.fetchChartData('RiskPriority')
      };
      
      const results = await Promise.allSettled(Object.values(kpiPromises));
      const keys = Object.keys(kpiPromises);
      
      results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          this.setKPIData(keys[index], result.value);
          console.log(`✅ [IncidentService] Cached: ${keys[index]}`);
        } else {
          console.warn(`⚠️ [IncidentService] Failed to cache: ${keys[index]}`, result.reason);
        }
      });
      
      console.log('✅ [IncidentService] ALL dashboard and chart data prefetch complete');
    } catch (error) {
      console.error('❌ [IncidentService] Error prefetching dashboard data:', error);
    }
  }

  /**
   * Fetch dashboard summary data
   */
  async fetchDashboardSummary() {
    try {
      const response = await axiosInstance.get(`${API_ENDPOINTS.INCIDENTS}dashboard/`, {
        timeout: 15000
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard summary:', error);
      throw error;
    }
  }

  /**
   * Fetch chart data for a specific dimension
   */
  async fetchChartData(yAxis) {
    try {
      const response = await axiosInstance.post(`${API_ENDPOINTS.INCIDENTS}dashboard/analytics/`, {
        xAxis: 'Time',
        yAxis: yAxis
      }, {
        timeout: 15000
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching chart data for ${yAxis}:`, error);
      throw error;
    }
  }

  /**
   * Fetch incident counts KPI
   */
  async fetchIncidentCounts() {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.INCIDENT_COUNTS, {
        timeout: 15000
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching incident counts:', error);
      throw error;
    }
  }

  /**
   * Fetch incident origins KPI
   */
  async fetchIncidentOrigins() {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.INCIDENT_ORIGINS, {
        timeout: 15000
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching incident origins:', error);
      throw error;
    }
  }
  
  /**
   * Fetch all incidents with pagination handling
   */
  async fetchIncidents() {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.INCIDENT_INCIDENTS, {
        timeout: 60000
      });
      
      if (response.data?.incidents && Array.isArray(response.data.incidents)) {
        return response.data.incidents;
      }
      
      if (Array.isArray(response.data)) {
        return response.data;
      }
      
      if (response.data?.data && Array.isArray(response.data.data)) {
        return response.data.data;
      }
      
      return [];
    } catch (error) {
      console.error('❌ Error fetching incidents:', error);
      throw error;
    }
  }
  
  /**
   * Fetch all audit findings
   */
  async fetchAuditFindings() {
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.AUDIT_FINDINGS, {
        params: {
          limit: 10000
        },
        timeout: 30000
      });
      
      if (response.data && response.data.success) {
        return response.data.data || [];
      } else if (Array.isArray(response.data)) {
        return response.data;
      }
      
      return [];
    } catch (error) {
      console.error('❌ Error fetching audit findings:', error);
      throw error;
    }
  }
  
  /**
   * Get a specific audit finding by ID from cache
   * @param {number|string} incidentId - The incident ID
   * @returns {Object|null} The audit finding or null
   */
  getAuditFindingById(incidentId) {
    const finding = this.dataStore.auditFindings.find(
      f => f.IncidentId === parseInt(incidentId) || f.IncidentId === incidentId
    );
    return finding || null;
  }
  
  /**
   * Check if audit findings cache is valid
   */
  hasValidAuditFindingsCache() {
    return this.dataStore.auditFindings.length > 0 && this.isCached();
  }
  
  /**
   * Fetch incident users
   */
  async fetchIncidentUsers() {
    console.log('🔄 Fetching incident users...');
    
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.INCIDENTS_USERS, {
        timeout: 10000
      });
      
      const users = Array.isArray(response.data) ? response.data : [];
      this.dataStore.incidentUsers = users;
      return users;
    } catch (error) {
      console.error('❌ Error fetching users:', error);
      throw error;
    }
  }
  
  /**
   * Fetch business units
   */
  async fetchBusinessUnits() {
    console.log('🔄 Fetching business units...');
    
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.BUSINESS_UNITS, {
        timeout: 10000
      });
      
      if (Array.isArray(response.data)) {
        return response.data;
      } else if (response.data && response.data.success && Array.isArray(response.data.data)) {
        return response.data.data;
      }
      
      return [];
    } catch (error) {
      console.error('❌ Error fetching business units:', error);
      throw error;
    }
  }
  
  /**
   * Fetch categories
   */
  async fetchCategories() {
    console.log('🔄 Fetching categories...');
    
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.CATEGORIES, {
        timeout: 10000
      });
      
      if (Array.isArray(response.data)) {
        return response.data;
      } else if (response.data && response.data.success && Array.isArray(response.data.data)) {
        return response.data.data;
      }
      
      return [];
    } catch (error) {
      console.error('❌ Error fetching categories:', error);
      throw error;
    }
  }
  
  /**
   * Fetch frameworks
   */
  async fetchFrameworks() {
    console.log('🔄 Fetching frameworks...');
    
    try {
      const response = await axiosInstance.get(API_ENDPOINTS.COMPLIANCE_ALL_POLICIES_FRAMEWORKS, {
        timeout: 10000
      });
      
      if (Array.isArray(response.data)) {
        return response.data;
      } else if (response.data && Array.isArray(response.data.frameworks)) {
        return response.data.frameworks;
      } else if (response.data && response.data.success && Array.isArray(response.data.data)) {
        return response.data.data;
      }
      
      return [];
    } catch (error) {
      console.error('❌ Error fetching frameworks:', error);
      throw error;
    }
  }
  
  /**
   * Get cached data by key
   * Components should use this instead of making API calls
   * 
   * @param {string} key - The data key (e.g., 'incidents', 'auditFindings')
   * @returns {Array} The cached data or empty array
   */
  getData(key) {
    if (this.dataStore[key]) {
      console.log(`✅ Returning cached ${key}:`, this.dataStore[key].length, 'items');
      return this.dataStore[key];
    }
    
    console.warn(`⚠️ No cached data for key: ${key}`);
    return [];
  }
  
  /**
   * Set data manually (useful for testing or manual updates)
   */
  setData(key, data) {
    this.dataStore[key] = data;
    console.log(`💾 Set ${key}:`, data.length, 'items');
  }
  
  /**
   * Get all cached data
   */
  getAllData() {
    return {
      ...this.dataStore
    };
  }
  
  /**
   * Check if data is cached and fresh
   * @param {number} maxAgeMs - Maximum age in milliseconds (default: 5 minutes)
   */
  isCached(maxAgeMs = 300000) {
    if (!this.dataStore.lastFetchTime) {
      return false;
    }
    
    const age = Date.now() - this.dataStore.lastFetchTime;
    return age < maxAgeMs;
  }

  /**
   * Check if incidents cache is valid
   */
  hasValidIncidentsCache() {
    return this.dataStore.incidents.length > 0 && this.isCached();
  }

  /**
   * Check if incident users cache is valid
   */
  hasValidUsersCache() {
    return Array.isArray(this.dataStore.incidentUsers) && this.dataStore.incidentUsers.length > 0;
  }

  /**
   * Get cached KPI data
   * @param {string} kpiKey - The KPI key (e.g., 'mttd', 'mttr', 'counts')
   * @returns {Object|null} Cached KPI data or null
   */
  getKPIData(kpiKey) {
    if (this.dataStore.kpiData && this.dataStore.kpiData[kpiKey]) {
      // Check if cache is fresh (5 minutes)
      const cacheAge = Date.now() - (this.dataStore.kpiDataCacheTime || 0);
      if (cacheAge < 300000) { // 5 minutes
        console.log(`✅ Returning cached KPI data for: ${kpiKey}`);
        return this.dataStore.kpiData[kpiKey];
      }
    }
    return null;
  }

  /**
   * Set cached KPI data
   * @param {string} kpiKey - The KPI key
   * @param {Object} data - The KPI data to cache
   */
  setKPIData(kpiKey, data) {
    if (!this.dataStore.kpiData) {
      this.dataStore.kpiData = {};
    }
    this.dataStore.kpiData[kpiKey] = data;
    this.dataStore.kpiDataCacheTime = Date.now();
    console.log(`💾 Cached KPI data for: ${kpiKey}`);
  }

  /**
   * Compute basic KPIs from cached incidents
   * @param {Object} filters - Optional filters (frameworkId, category, priority)
   * @returns {Object} Basic KPI data computed from cache
   */
  computeBasicKPIsFromCache(filters = {}) {
    let incidents = this.dataStore.incidents || [];
    let auditFindings = this.dataStore.auditFindings || [];
    let allItems = [...incidents, ...auditFindings];

    // Apply filters if provided
    if (filters.frameworkId) {
      const frameworkIdStr = String(filters.frameworkId);
      const initialCount = allItems.length;
      allItems = allItems.filter(item => {
        // Check multiple possible field names for framework ID (prioritize framework_id as used in other components)
        const itemFrameworkId = item.framework_id || item.FrameworkId || item.Framework?.id || item.framework?.id;
        if (!itemFrameworkId) {
          return false; // No framework ID found, exclude from results
        }
        // Use string comparison to handle string/number mismatches
        return String(itemFrameworkId) === frameworkIdStr;
      });
      console.log(`🔍 [incidentService] Filtered by framework ${filters.frameworkId}: ${allItems.length} items from ${initialCount} total`);
    }

    if (filters.category && filters.category !== 'All Categories') {
      allItems = allItems.filter(item => {
        const itemCategory = item.RiskCategory || item.Category || item.risk_category || '';
        return itemCategory === filters.category;
      });
    }

    if (filters.priority && filters.priority !== 'All Priorities') {
      allItems = allItems.filter(item => {
        const itemPriority = item.RiskPriority || item.Priority || '';
        return itemPriority.toLowerCase().includes(filters.priority.toLowerCase());
      });
    }

    // Compute status counts
    const statusCounts = {
      scheduled: allItems.filter(i => (i.Status === 'Scheduled' || i.Status === 'scheduled')).length,
      approved: allItems.filter(i => (i.Status === 'Approved' || i.Status === 'approved')).length,
      rejected: allItems.filter(i => (i.Status === 'Rejected' || i.Status === 'rejected')).length,
      resolved: allItems.filter(i => (i.Status === 'Resolved' || i.Status === 'resolved')).length,
      'Pending Review': allItems.filter(i => 
        (i.Status === 'Pending Review' || i.Status === 'pending review' || 
         i.Status === 'Under Review' || i.Status === 'under review')
      ).length
    };

    // Compute total count
    const totalCount = allItems.length;

    // Compute by severity
    const severityCounts = {
      high: allItems.filter(i => {
        const priority = i.RiskPriority || i.Priority || '';
        return priority.toLowerCase().includes('high');
      }).length,
      medium: allItems.filter(i => {
        const priority = i.RiskPriority || i.Priority || '';
        return priority.toLowerCase().includes('medium');
      }).length,
      low: allItems.filter(i => {
        const priority = i.RiskPriority || i.Priority || '';
        return priority.toLowerCase().includes('low');
      }).length
    };
    
    // Convert to percentages for display
    const incidentsBySeverity = {
      high: totalCount > 0 ? Math.round((severityCounts.high / totalCount) * 100) : 0,
      medium: totalCount > 0 ? Math.round((severityCounts.medium / totalCount) * 100) : 0,
      low: totalCount > 0 ? Math.round((severityCounts.low / totalCount) * 100) : 0
    };

    // Compute by origin
    const originCounts = {};
    allItems.forEach(item => {
      const origin = item.Origin || item.origin || 'Unknown';
      originCounts[origin] = (originCounts[origin] || 0) + 1;
    });
    const incidentOrigins = Object.keys(originCounts).map(origin => ({
      origin: origin,
      count: originCounts[origin],
      percentage: totalCount > 0 ? Math.round((originCounts[origin] / totalCount) * 100) : 0
    })).sort((a, b) => b.count - a.count); // Sort by count descending

    // Compute by category
    const categoryCounts = {};
    allItems.forEach(item => {
      const category = item.RiskCategory || item.Category || item.risk_category || 'Unknown';
      categoryCounts[category] = (categoryCounts[category] || 0) + 1;
    });
    const incidentCategories = Object.keys(categoryCounts).map(category => ({
      category: category,
      count: categoryCounts[category]
    })).sort((a, b) => b.count - a.count);

    // Compute incident counts
    const incidentCounts = {
      total: totalCount,
      pending: statusCounts['Pending Review'] || 0,
      accepted: statusCounts.approved || 0,
      rejected: statusCounts.rejected || 0,
      resolved: statusCounts.resolved || 0
    };

    return {
      statusCounts,
      totalCount,
      incidentsBySeverity,
      incidentOrigins,
      incidentCategories,
      incidentCounts,
      change_percentage: 0, // Would need historical data
      resolution_rate: statusCounts.resolved > 0 ? 
        Math.round((statusCounts.resolved / totalCount) * 100) : 0
    };
  }

  /**
   * Compute chart data from cached incidents
   * @param {string} yAxis - The y-axis dimension (Status, Origin, RiskCategory, RiskPriority)
   * @param {Object} filters - Optional filters (frameworkId, category, priority)
   * @returns {Object} Chart data object with labels and datasets
   */
  computeChartDataFromCache(yAxis, filters = {}) {
    let incidents = this.dataStore.incidents || [];
    let auditFindings = this.dataStore.auditFindings || [];
    let allItems = [...incidents, ...auditFindings];

    // Apply filters if provided
    if (filters.frameworkId) {
      const frameworkIdStr = String(filters.frameworkId);
      allItems = allItems.filter(item => {
        // Check multiple possible field names for framework ID (prioritize framework_id as used in other components)
        const itemFrameworkId = item.framework_id || item.FrameworkId || item.Framework?.id || item.framework?.id;
        if (!itemFrameworkId) {
          return false; // No framework ID found, exclude from results
        }
        // Use string comparison to handle string/number mismatches
        return String(itemFrameworkId) === frameworkIdStr;
      });
    }

    if (filters.category && filters.category !== 'All Categories') {
      allItems = allItems.filter(item => {
        const itemCategory = item.RiskCategory || item.Category || item.risk_category || '';
        return itemCategory === filters.category;
      });
    }

    if (filters.priority && filters.priority !== 'All Priorities') {
      allItems = allItems.filter(item => {
        const itemPriority = item.RiskPriority || item.Priority || '';
        return itemPriority.toLowerCase().includes(filters.priority.toLowerCase());
      });
    }

    if (allItems.length === 0) {
      return {
        labels: ['No Data'],
        datasets: [{
          label: 'No Data',
          data: [0],
          backgroundColor: 'rgba(158, 158, 158, 0.6)',
          borderColor: '#9E9E9E',
          borderWidth: 1
        }]
      };
    }

    let labels = [];
    let data = [];
    let counts = {};

    switch (yAxis) {
      case 'Status':
        counts = {
          'Scheduled': allItems.filter(i => (i.Status === 'Scheduled' || i.Status === 'scheduled')).length,
          'Approved': allItems.filter(i => (i.Status === 'Approved' || i.Status === 'approved')).length,
          'Rejected': allItems.filter(i => (i.Status === 'Rejected' || i.Status === 'rejected')).length,
          'Resolved': allItems.filter(i => (i.Status === 'Resolved' || i.Status === 'resolved')).length,
          'Pending Review': allItems.filter(i => 
            (i.Status === 'Pending Review' || i.Status === 'pending review' || 
             i.Status === 'Under Review' || i.Status === 'under review')
          ).length
        };
        labels = Object.keys(counts).filter(key => counts[key] > 0);
        data = labels.map(label => counts[label]);
        break;

      case 'Origin': {
        // First, collect all unique origin values for debugging
        const uniqueOrigins = new Set();
        allItems.forEach(item => {
          const origin = item.Origin || item.origin || 'Unknown';
          uniqueOrigins.add(origin);
        });
        console.log('🔍 [IncidentService] Unique origin values in cache:', Array.from(uniqueOrigins));
        
        // Normalize origin values to match backend format
        const normalizeOrigin = (origin) => {
          if (!origin || origin === 'Unknown' || origin === '' || origin === 'null' || origin === 'undefined') {
            return 'Other';
          }
          
          // Convert to string and trim whitespace
          const normalized = String(origin).trim();
          
          // Return early if empty after trim
          if (normalized === '') return 'Other';
          
          const lowerOrigin = normalized.toLowerCase();
          // Remove underscores and spaces for comparison
          const cleanedOrigin = lowerOrigin.replace(/[_\s-]/g, '');
          
          // Map all variations to standard format (case-insensitive and flexible)
          
          // Manual variations: "Manual", "MANUAL", "manual", etc.
          if (cleanedOrigin === 'manual') {
            return 'Manual';
          }
          
          // SIEM variations: "SIEM", "siem", etc.
          if (cleanedOrigin === 'siem') {
            return 'SIEM';
          }
          
          // Audit Finding variations: "Audit Finding", "AuditFinding", "audit_finding", "AUDIT_FINDING", etc.
          // Check for both "audit" and "finding" or just "auditfinding" as one word
          if ((cleanedOrigin.includes('audit') && cleanedOrigin.includes('finding')) || 
              cleanedOrigin === 'auditfinding') {
            return 'Audit Finding';
          }
          
          // Compliance Gap variations: "Compliance Gap", "ComplianceGap", "compliance_gap", etc.
          if ((cleanedOrigin.includes('compliance') && cleanedOrigin.includes('gap')) ||
              cleanedOrigin === 'compliancegap') {
            return 'Compliance Gap';
          }
          
          // Log unknown origins for debugging
          console.warn(`[IncidentService] Unknown origin value: "${normalized}" - categorizing as "Other"`);
          return 'Other';
        };
        
        const originCounts = {
          'Manual': 0,
          'SIEM': 0,
          'Audit Finding': 0,
          'Other': 0
        };
        
        allItems.forEach(item => {
          const origin = item.Origin || item.origin || 'Unknown';
          const normalizedOrigin = normalizeOrigin(origin);
          originCounts[normalizedOrigin] = (originCounts[normalizedOrigin] || 0) + 1;
        });
        
        console.log('🔍 [IncidentService] Origin counts after normalization:', originCounts);
        
        // Remove 'Other' category if it's empty
        if (originCounts['Other'] === 0) {
          delete originCounts['Other'];
        }
        
        labels = Object.keys(originCounts).sort((a, b) => originCounts[b] - originCounts[a]);
        data = labels.map(origin => originCounts[origin]);
        break;
      }

      case 'RiskCategory': {
        const categoryCounts = {};
        allItems.forEach(item => {
          const category = item.RiskCategory || item.Category || item.risk_category || 'Unknown';
          categoryCounts[category] = (categoryCounts[category] || 0) + 1;
        });
        labels = Object.keys(categoryCounts).sort((a, b) => categoryCounts[b] - categoryCounts[a]);
        data = labels.map(category => categoryCounts[category]);
        break;
      }

      case 'RiskPriority': {
        const priorityCounts = {
          'High': allItems.filter(i => {
            const priority = i.RiskPriority || i.Priority || '';
            return priority.toLowerCase().includes('high');
          }).length,
          'Medium': allItems.filter(i => {
            const priority = i.RiskPriority || i.Priority || '';
            return priority.toLowerCase().includes('medium');
          }).length,
          'Low': allItems.filter(i => {
            const priority = i.RiskPriority || i.Priority || '';
            return priority.toLowerCase().includes('low');
          }).length
        };
        labels = Object.keys(priorityCounts).filter(key => priorityCounts[key] > 0);
        data = labels.map(priority => priorityCounts[priority]);
        break;
      }

      default:
        return {
          labels: ['No Data'],
          datasets: [{
            label: 'No Data',
            data: [0],
            backgroundColor: 'rgba(158, 158, 158, 0.6)',
            borderColor: '#9E9E9E',
            borderWidth: 1
          }]
        };
    }

    // Return chart data in the format expected by Chart.js
    return {
      labels: labels.length > 0 ? labels : ['No Data'],
      datasets: [{
        label: yAxis,
        data: data.length > 0 ? data : [0],
        backgroundColor: this.getChartColors(yAxis, labels),
        borderColor: this.getChartBorderColors(yAxis, labels),
        borderWidth: 1
      }]
    };
  }

  /**
   * Get chart colors for a given dimension
   * @param {string} yAxis - The y-axis dimension
   * @param {Array} labels - The chart labels
   * @returns {Array|string} Color array or single color
   */
  getChartColors(yAxis, labels) {
    const colorMaps = {
      Status: {
        'Scheduled': 'rgba(255, 152, 0, 0.6)',
        'Approved': 'rgba(76, 175, 80, 0.6)',
        'Rejected': 'rgba(244, 67, 54, 0.6)',
        'Resolved': 'rgba(33, 150, 243, 0.6)',
        'Pending Review': 'rgba(156, 39, 176, 0.6)'
      },
      Origin: {
        'Manual': 'rgba(33, 150, 243, 0.6)',
        'SIEM': 'rgba(156, 39, 176, 0.6)',
        'Audit Finding': 'rgba(255, 193, 7, 0.6)',
        'Compliance Gap': 'rgba(255, 87, 34, 0.6)',
        'Unknown': 'rgba(121, 85, 72, 0.6)'
      },
      RiskCategory: {
        'Security': 'rgba(244, 67, 54, 0.6)',
        'Compliance': 'rgba(156, 39, 176, 0.6)',
        'Operational': 'rgba(255, 152, 0, 0.6)',
        'Financial': 'rgba(33, 150, 243, 0.6)',
        'Strategic': 'rgba(76, 175, 80, 0.6)',
        'Reputational': 'rgba(121, 85, 72, 0.6)',
        'Unknown': 'rgba(158, 158, 158, 0.6)'
      },
      RiskPriority: {
        'High': 'rgba(244, 67, 54, 0.6)',
        'Medium': 'rgba(255, 152, 0, 0.6)',
        'Low': 'rgba(76, 175, 80, 0.6)'
      }
    };

    const colorMap = colorMaps[yAxis] || {};
    const defaultColors = [
      'rgba(255, 99, 132, 0.6)',
      'rgba(54, 162, 235, 0.6)',
      'rgba(255, 206, 86, 0.6)',
      'rgba(75, 192, 192, 0.6)',
      'rgba(153, 102, 255, 0.6)',
      'rgba(255, 159, 64, 0.6)'
    ];

    return labels.map((label, index) => colorMap[label] || defaultColors[index % defaultColors.length]);
  }

  /**
   * Get chart border colors for a given dimension
   * @param {string} yAxis - The y-axis dimension
   * @param {Array} labels - The chart labels
   * @returns {Array|string} Border color array or single color
   */
  getChartBorderColors(yAxis, labels) {
    const colorMaps = {
      Status: {
        'Scheduled': '#FF9800',
        'Approved': '#4CAF50',
        'Rejected': '#F44336',
        'Resolved': '#2196F3',
        'Pending Review': '#9C27B0'
      },
      Origin: {
        'Manual': '#2196F3',
        'SIEM': '#9C27B0',
        'Audit Finding': '#FFC107',
        'Compliance Gap': '#FF5722',
        'Unknown': '#795548'
      },
      RiskCategory: {
        'Security': '#F44336',
        'Compliance': '#9C27B0',
        'Operational': '#FF9800',
        'Financial': '#2196F3',
        'Strategic': '#4CAF50',
        'Reputational': '#795548',
        'Unknown': '#9E9E9E'
      },
      RiskPriority: {
        'High': '#F44336',
        'Medium': '#FF9800',
        'Low': '#4CAF50'
      }
    };

    const colorMap = colorMaps[yAxis] || {};
    const defaultColors = [
      'rgb(255, 99, 132)',
      'rgb(54, 162, 235)',
      'rgb(255, 206, 86)',
      'rgb(75, 192, 192)',
      'rgb(153, 102, 255)',
      'rgb(255, 159, 64)'
    ];

    return labels.map((label, index) => colorMap[label] || defaultColors[index % defaultColors.length]);
  }

  /**
   * Check if KPI cache is valid
   * @param {number} maxAgeMs - Maximum age in milliseconds (default: 5 minutes)
   * @returns {boolean} True if cache is valid
   */
  hasValidKPICache(maxAgeMs = 300000) {
    if (!this.dataStore.kpiDataCacheTime) {
      return false;
    }
    const cacheAge = Date.now() - this.dataStore.kpiDataCacheTime;
    return cacheAge < maxAgeMs && Object.keys(this.dataStore.kpiData || {}).length > 0;
  }
  
  /**
   * Clear all cached data
   */
  clearCache() {
    console.log('🗑️ Clearing incident data cache...');
    this.dataStore = {
      incidents: [],
      auditFindings: [],
      incidentUsers: [],
      incidentBusinessUnits: [],
      incidentCategories: [],
      incidentFrameworks: [],
      kpiData: {},
      kpiDataCacheTime: null,
      lastFetchTime: null,
      isFetching: false,
      fetchErrors: {}
    };
  }
  
  /**
   * Refresh data (clears cache and fetches new data)
   */
  async refreshData() {
    console.log('🔄 Refreshing incident data...');
    this.clearCache();
    return await this.fetchAllIncidentData();
  }
}

// Export singleton instance
const incidentService = new IncidentService();
export default incidentService;

