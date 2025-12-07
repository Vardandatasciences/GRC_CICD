/**
 * Access Control Utilities
 * Utility functions for handling access control and permission errors
 */

import { PopupService } from '@/modules/popup/popupService';

// Session Management Utilities
export const SessionUtils = {
  /**
   * Set user session data
   * @param {Object} userData - User data from login response
   */
  setUserSession(userData) {
    console.log('[SESSION_UTILS] Setting user session:', userData);
    if (userData.user_id) {
      localStorage.setItem('user_id', userData.user_id.toString());
    }
    if (userData.email) {
      localStorage.setItem('user_email', userData.email);
    }
    if (userData.name) {
      localStorage.setItem('user_name', userData.name);
    }
    // Set a flag to indicate user is logged in
    localStorage.setItem('is_logged_in', 'true');
  },

  /**
   * Get user session data
   * @returns {Object} User session data
   */
  getUserSession() {
    return {
      user_id: localStorage.getItem('user_id'),
      email: localStorage.getItem('user_email'),
      name: localStorage.getItem('user_name'),
      is_logged_in: localStorage.getItem('is_logged_in') === 'true'
    };
  },

  /**
   * Clear user session
   */
  clearUserSession() {
    console.log('[SESSION_UTILS] Clearing user session');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_name');
    localStorage.removeItem('is_logged_in');
  },

  /**
   * Check if user is logged in
   * @returns {boolean} True if user is logged in
   */
  isLoggedIn() {
    return localStorage.getItem('is_logged_in') === 'true';
  },

  /**
   * Get user ID for API requests
   * @returns {string|null} User ID or null if not logged in
   */
  getUserId() {
    return localStorage.getItem('user_id');
  }
};

export const AccessUtils = {
  /**
   * Show access denied page instead of popup
   * @param {string} feature - Feature name (e.g., 'Risk Management', 'Create Risk')
   * @param {string} customMessage - Custom message to display
   * @param {Function} onContactAdmin - Callback for contact admin action
   */
  // eslint-disable-next-line no-unused-vars
  showAccessDenied(feature = 'this feature', customMessage = null, onContactAdmin = null) {
    console.log('[ACCESS_UTILS] Redirecting to access denied page for:', feature);
    
    // Store the access denied information in sessionStorage for the AccessDenied page
    const accessDeniedInfo = {
      feature: feature,
      message: customMessage || `You don't have permission to access ${feature}. Please contact your administrator if you believe this is an error.`,
      timestamp: new Date().toISOString(),
      url: window.location.href
    };
    
    sessionStorage.setItem('accessDeniedInfo', JSON.stringify(accessDeniedInfo));
    
    // Redirect to access denied page
    if (window.router) {
      window.router.push('/access-denied');
    } else {
      // Fallback if router is not available
      window.location.href = '/access-denied';
    }
  },

  /**
   * Show access denied popup for specific risk operations
   * @param {string} operation - Operation type (e.g., 'create', 'edit', 'view', 'delete')
   * @param {Function} onContactAdmin - Callback for contact admin action
   */
  // eslint-disable-next-line no-unused-vars
  showRiskAccessDenied(operation = 'access', onContactAdmin = null) {
    console.log('[ACCESS_UTILS] Showing risk access denied popup for:', operation);
    
    const operationMap = {
      'create': 'create new risks',
      'edit': 'edit risks',
      'view': 'view risks',
      'delete': 'delete risks',
      'approve': 'approve risks',
      'assign': 'assign risks',
      'access': 'access risk management'
    };
    
    const feature = operationMap[operation] || operation;
    this.showAccessDenied(`Risk Management - ${feature}`, null, onContactAdmin);
  },

  /**
   * Show access denied popup for specific compliance operations (5 main features)
   * @param {string} operation - Operation type
   * @param {Function} onContactAdmin - Callback for contact admin action
   */
  // eslint-disable-next-line no-unused-vars
  showComplianceAccessDenied(operation = 'access', onContactAdmin = null) {
    console.log('[ACCESS_UTILS] Showing compliance access denied popup for:', operation);
    
    const operationMap = {
      'create': 'create compliance items',
      'edit': 'edit compliance items',
      'approve': 'approve compliance items',
      'view': 'view compliance items',
      'analytics': 'access compliance analytics',
      'access': 'access compliance management'
    };
    
    const feature = operationMap[operation] || operation;
    this.showAccessDenied(`Compliance Management - ${feature}`, null, onContactAdmin);
  },

  /**
   * Show access denied popup for specific main compliance features
   * @param {string} feature - Main feature name (CreateCompliance, EditCompliance, etc.)
   * @param {Function} onContactAdmin - Callback for contact admin action
   */
  // eslint-disable-next-line no-unused-vars
  showComplianceFeatureDenied(feature, _onContactAdmin = null) {
    // TEMPORARILY DISABLED: Frontend permission checks are bypassed for development
    // TODO: Re-enable frontend permission checks when needed for production
    console.log('[ACCESS_UTILS] FRONTEND RBAC DISABLED - Compliance feature access granted for:', feature);
    return; // Don't show any popup, just return
  },

  /**
   * Comprehensive compliance access control methods
   */
  
  // Compliance viewing methods
  showComplianceViewDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('view', onContactAdmin);
  },
  
  showComplianceDashboardDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('dashboard', onContactAdmin);
  },
  
  showComplianceVersioningDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('versioning', onContactAdmin);
  },
  
  // Compliance creation methods
  showComplianceCreateDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('create', onContactAdmin);
  },
  
  showComplianceCloneDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('clone', onContactAdmin);
  },
  
  // Compliance editing methods
  showComplianceEditDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('edit', onContactAdmin);
  },
  
  showComplianceToggleDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('toggle', onContactAdmin);
  },
  
  showComplianceDeactivateDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('deactivate', onContactAdmin);
  },
  
  // Compliance approval methods
  showComplianceApproveDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('approve', onContactAdmin);
  },
  
  showComplianceReviewDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('review', onContactAdmin);
  },
  
  // Compliance analytics methods
  showComplianceAnalyticsDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('analytics', onContactAdmin);
  },
  
  showComplianceKPIDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('kpi', onContactAdmin);
  },
  
  showCompliancePerformanceAnalyticsDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('analytics', onContactAdmin);
  },
  
  // 5 Main Compliance Features
  showCreateComplianceDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('create', onContactAdmin);
  },
  
  showEditComplianceDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('edit', onContactAdmin);
  },
  
  showApproveComplianceDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('approve', onContactAdmin);
  },
  
  showViewAllComplianceDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('view', onContactAdmin);
  },
  
  // Compliance export methods
  showComplianceExportDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('export', onContactAdmin);
  },
  
  // Compliance audit methods
  showComplianceAuditDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('audit', onContactAdmin);
  },
  
  // Compliance framework methods
  showComplianceFrameworkDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('framework', onContactAdmin);
  },
  
  showCompliancePolicyDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('policy', onContactAdmin);
  },
  
  showComplianceSubpolicyDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('subpolicy', onContactAdmin);
  },
  
  // Compliance category methods
  showComplianceCategoryDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('category', onContactAdmin);
  },
  
  showComplianceBusinessUnitDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('business-unit', onContactAdmin);
  },
  
  // Compliance notification methods
  showComplianceNotificationDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('notification', onContactAdmin);
  },
  
  // Compliance assignment methods
  showComplianceAssignDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('assign', onContactAdmin);
  },
  
  // Compliance deletion methods
  showComplianceDeleteDenied(onContactAdmin = null) {
    this.showComplianceAccessDenied('delete', onContactAdmin);
  },

  /**
   * Show access denied popup for specific incident operations
   * @param {string} operation - Operation type
   * @param {Function} onContactAdmin - Callback for contact admin action
   */
  // eslint-disable-next-line no-unused-vars
  showIncidentAccessDenied(operation = 'access', _onContactAdmin = null) {
    // TEMPORARILY DISABLED: Frontend permission checks are bypassed for development
    // TODO: Re-enable frontend permission checks when needed for production
    console.log('[ACCESS_UTILS] FRONTEND RBAC DISABLED - Incident access granted for:', operation);
    return; // Don't show any popup, just return
  },

  /**
   * Show access denied popup for specific audit operations (6 main audit permissions)
   * @param {string} operation - Operation type
   * @param {Function} onContactAdmin - Callback for contact admin action
   */
  // eslint-disable-next-line no-unused-vars
  showAuditAccessDenied(operation = 'access', _onContactAdmin = null) {
    // TEMPORARILY DISABLED: Frontend permission checks are bypassed for development
    // TODO: Re-enable frontend permission checks when needed for production
    console.log('[ACCESS_UTILS] FRONTEND RBAC DISABLED - Audit access granted for:', operation);
    return; // Don't show any popup, just return
  },

  /**
   * Show access denied popup for specific main audit features
   * @param {string} feature - Main audit feature name (AssignAudit, ConductAudit, etc.)
   * @param {Function} onContactAdmin - Callback for contact admin action
   */
  // eslint-disable-next-line no-unused-vars
  showAuditFeatureDenied(feature, _onContactAdmin = null) {
    // TEMPORARILY DISABLED: Frontend permission checks are bypassed for development
    // TODO: Re-enable frontend permission checks when needed for production
    console.log('[ACCESS_UTILS] FRONTEND RBAC DISABLED - Audit feature access granted for:', feature);
    return; // Don't show any popup, just return
  },

  /**
   * Comprehensive audit access control methods
   */
  
  // Main audit feature access methods
  showAuditViewDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('view', onContactAdmin);
  },
  
  showAuditDashboardDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('dashboard', onContactAdmin);
  },
  
  showAuditListDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('list', onContactAdmin);
  },
  
  // Audit assignment methods
  showAuditAssignDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('assign', onContactAdmin);
  },
  
  showAuditCreateDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('create', onContactAdmin);
  },
  
  showCreateAuditDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('create-audit', onContactAdmin);
  },
  
  // Audit conduct methods
  showAuditConductDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('conduct', onContactAdmin);
  },
  
  showAuditPerformDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('perform', onContactAdmin);
  },
  
  showAuditTaskUpdateDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('update-task', onContactAdmin);
  },
  
  showAuditChecklistDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('checklist', onContactAdmin);
  },
  
  // Audit review methods
  showAuditReviewDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('review', onContactAdmin);
  },
  
  showAuditApproveDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('approve', onContactAdmin);
  },
  
  // Audit reports methods
  showAuditReportsDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('reports', onContactAdmin);
  },
  
  showAuditViewReportsDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('view-reports', onContactAdmin);
  },
  
  showAuditGenerateReportsDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('generate-reports', onContactAdmin);
  },
  
  showAuditDownloadReportsDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('download-reports', onContactAdmin);
  },
  
  // Audit analytics methods
  showAuditAnalyticsDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('analytics', onContactAdmin);
  },
  
  showAuditKPIDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('kpi', onContactAdmin);
  },
  
  showAuditMetricsDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('metrics', onContactAdmin);
  },
  
  showAuditPerformanceAnalyticsDenied(onContactAdmin = null) {
    this.showAuditAccessDenied('performance', onContactAdmin);
  },
  
  // Main audit permission methods
  showAssignAuditDenied(onContactAdmin = null) {
    this.showAuditFeatureDenied('AssignAudit', onContactAdmin);
  },
  
  showConductAuditDenied(onContactAdmin = null) {
    this.showAuditFeatureDenied('ConductAudit', onContactAdmin);
  },
  
  showReviewAuditDenied(onContactAdmin = null) {
    this.showAuditFeatureDenied('ReviewAudit', onContactAdmin);
  },
  
  showViewAuditReportsDenied(onContactAdmin = null) {
    this.showAuditFeatureDenied('ViewAuditReports', onContactAdmin);
  },
  
  showAuditPerformanceAnalyticsPermissionDenied(onContactAdmin = null) {
    this.showAuditFeatureDenied('AuditPerformanceAnalytics', onContactAdmin);
  },
  
  showViewAllAuditsDenied(onContactAdmin = null) {
    this.showAuditFeatureDenied('ViewAllAudits', onContactAdmin);
  },

  /**
   * Default contact admin callback - can be customized per application
   */
  defaultContactAdmin() {
    console.log('[ACCESS_UTILS] defaultContactAdmin callback triggered');
    
    // You can customize this based on your application's admin contact method
    console.log('Contact admin action triggered');
    
    // Example: Open email client
    // window.location.href = 'mailto:admin@company.com?subject=Access Request&body=I need access to additional features in the GRC system.';
    
    // Example: Show additional instructions
    try {
      PopupService.info(
        'Please contact your system administrator via email or support ticket to request access to this feature.',
        'Contact Administrator'
      );
    } catch (error) {
      console.error('[ACCESS_UTILS] Error showing contact admin popup:', error);
    }
  },

  /**
   * Handle API error responses and redirect to access denied page
   * @param {Object} error - Error object from API response
   * @param {string} defaultFeature - Default feature name if not specified in error
   */
  handleApiError(error, defaultFeature = 'this feature') {
    console.log('[ACCESS_UTILS] Handling API error for:', defaultFeature);
    
    if (error.response && [401, 403].includes(error.response.status)) {
      this.showAccessDenied(defaultFeature);
      return true; // Error was handled
    }
    
    return false; // Error was not handled
  },

  /**
   * Handle API errors based on URL patterns
   * @param {Object} error - Error object from API response
   * @param {string} url - The API URL that failed
   */
  handleApiErrorByUrl(error, url) {
    console.log('[ACCESS_UTILS] handleApiErrorByUrl called:', { 
      status: error?.response?.status, 
      url,
      method: error?.config?.method?.toUpperCase()
    });

    if (!error.response || ![401, 403].includes(error.response.status)) {
      console.log('[ACCESS_UTILS] Not an access error, ignoring');
      return false;
    }

    const method = error?.config?.method?.toUpperCase() || 'GET';
    
    // Risk-related URLs
    if (url.includes('http://15.207.108.158:8000/api/risks/')) {
      console.log('[ACCESS_UTILS] Risk API access denied detected');
      
      if (method === 'POST') {
        this.showRiskAccessDenied('create');
      } else if (method === 'PUT' || method === 'PATCH') {
        this.showRiskAccessDenied('edit');
      } else if (method === 'DELETE') {
        this.showRiskAccessDenied('delete');
      } else {
        this.showRiskAccessDenied('view');
      }
      return true;
    }
    
    // Risk instances URLs
    if (url.includes('http://15.207.108.158:8000/api/risk-instances/')) {
      console.log('[ACCESS_UTILS] Risk instances API access denied detected');
      
      if (method === 'POST') {
        this.showRiskAccessDenied('create');
      } else if (method === 'PUT' || method === 'PATCH') {
        this.showRiskAccessDenied('edit');
      } else {
        this.showRiskAccessDenied('view');
      }
      return true;
    }
    
    // Risk analytics/metrics URLs
    if (url.includes('http://15.207.108.158:8000/api/risk/metrics') || url.includes('http://15.207.108.158:8000/api/risk/analytics')) {
      console.log('[ACCESS_UTILS] Risk analytics API access denied detected');
      this.showRiskAccessDenied('analytics');
      return true;
    }
    
    // Compliance URLs
    if (url.includes('http://15.207.108.158:8000/api/compliance/')) {
      console.log('[ACCESS_UTILS] Compliance API access denied detected');
      
      if (method === 'POST') {
        this.showComplianceAccessDenied('create');
      } else if (method === 'PUT' || method === 'PATCH') {
        this.showComplianceAccessDenied('edit');
      } else {
        this.showComplianceAccessDenied('view');
      }
      return true;
    }
    
    // Incident URLs
    if (url.includes('http://15.207.108.158:8000/api/incidents/')) {
      console.log('[ACCESS_UTILS] Incident API access denied detected');
      
      if (method === 'POST') {
        this.showIncidentAccessDenied('create');
      } else if (method === 'PUT' || method === 'PATCH') {
        this.showIncidentAccessDenied('edit');
      } else {
        this.showIncidentAccessDenied('view');
      }
      return true;
    }
    
    // Audit URLs
    if (url.includes('http://15.207.108.158:8000/api/audit/') || url.includes('http://15.207.108.158:8000/api/audits/')) {
      console.log('[ACCESS_UTILS] Audit API access denied detected');
      
      // Audit assignment URLs
      if (url.includes('/assign') || url.includes('/create')) {
        this.showAuditAccessDenied('assign');
        return true;
      }
      
      // Audit conduct URLs
      if (url.includes('/conduct') || url.includes('/tasks/') || url.includes('/checklist')) {
        this.showAuditAccessDenied('conduct');
        return true;
      }
      
      // Audit review URLs
      if (url.includes('/review') || url.includes('/approve')) {
        this.showAuditAccessDenied('review');
        return true;
      }
      
      // Audit reports URLs
      if (url.includes('/reports') || url.includes('/generate') || url.includes('/download')) {
        this.showAuditAccessDenied('view-reports');
        return true;
      }
      
      // Audit analytics URLs
      if (url.includes('/analytics') || url.includes('/kpi') || url.includes('/metrics')) {
        this.showAuditAccessDenied('analytics');
        return true;
      }
      
      // General audit operations based on HTTP method
      if (method === 'POST') {
        this.showAuditAccessDenied('create');
      } else if (method === 'PUT' || method === 'PATCH') {
        this.showAuditAccessDenied('conduct');
      } else {
        this.showAuditAccessDenied('view');
      }
      return true;
    }
    
    // Generic fallback
    console.log('[ACCESS_UTILS] Generic API access denied detected for URL:', url);
    this.showAccessDenied('this feature');
    return true;
  }
};

export default AccessUtils; 