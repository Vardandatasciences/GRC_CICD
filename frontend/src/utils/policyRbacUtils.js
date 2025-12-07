/**
 * Policy RBAC (Role-Based Access Control) Utilities
 * Comprehensive access control system for Policy module
 */

// RBAC is disabled for AllPolicies.vue. Permission checks are bypassed on that page.
import { PopupService } from '@/modules/popup/popupService';
import { SessionUtils } from './accessUtils';
import axios from 'axios';

// RBAC State Management
let rbacState = {
  permissions: null,
  userRole: null,
  isLoaded: false,
  isLoading: false,
  lastFetch: null,
  error: null
};

// Cache expiration time (5 minutes)
const CACHE_EXPIRY = 5 * 60 * 1000;

/**
 * Policy RBAC Utilities
 */
export const PolicyRbacUtils = {
  /**
   * Initialize RBAC system and fetch user permissions
   */
  async init() {
    console.log('[POLICY_RBAC] Initializing RBAC system...');
    
    // Check if data is already cached and not expired
    if (rbacState.isLoaded && rbacState.lastFetch && 
        (Date.now() - rbacState.lastFetch) < CACHE_EXPIRY) {
      console.log('[POLICY_RBAC] Using cached permissions');
      return rbacState;
    }

    // Prevent multiple simultaneous initializations
    if (rbacState.isLoading) {
      console.log('[POLICY_RBAC] Already loading, waiting...');
      return await this.waitForLoad();
    }

    rbacState.isLoading = true;
    rbacState.error = null;

    try {
      // Check if user is logged in
      if (!SessionUtils.isLoggedIn()) {
        throw new Error('User not logged in');
      }

      // Fetch user permissions and role in parallel
      const [permissionsResponse, roleResponse] = await Promise.all([
        this.fetchUserPermissions(),
        this.fetchUserRole()
      ]);

      rbacState.permissions = permissionsResponse;
      rbacState.userRole = roleResponse;
      rbacState.isLoaded = true;
      rbacState.lastFetch = Date.now();

      console.log('[POLICY_RBAC] RBAC initialized successfully:', rbacState);
      return rbacState;

    } catch (error) {
      console.error('[POLICY_RBAC] Failed to initialize RBAC:', error);
      rbacState.error = error.message;
      throw error;
    } finally {
      rbacState.isLoading = false;
    }
  },

  /**
   * Wait for initialization to complete
   */
  async waitForLoad() {
    return new Promise((resolve) => {
      const checkLoaded = () => {
        if (!rbacState.isLoading) {
          resolve(rbacState);
        } else {
          setTimeout(checkLoaded, 100);
        }
      };
      checkLoaded();
    });
  },

  /**
   * Fetch user permissions from backend
   */
  async fetchUserPermissions() {
    try {
      // First try the specific API endpoint
      try {
        const response = await axios.get('http://15.207.108.158:8000/api/user-permissions/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        });
        console.log('[POLICY_RBAC] Permissions fetched:', response.data);
        return response.data;
      } catch (specificError) {
        console.warn('[POLICY_RBAC] Specific permissions endpoint failed, trying fallback:', specificError);
        
        // Fallback to the debug endpoint
        const fallbackResponse = await axios.get('http://15.207.108.158:8000/api/debug-permissions/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        });
        console.log('[POLICY_RBAC] Permissions fetched from fallback:', fallbackResponse.data);
        return fallbackResponse.data;
      }
    } catch (error) {
      console.error('[POLICY_RBAC] All permission endpoints failed:', error);
      // Return default permissions to avoid breaking the UI
      return {
        permissions: ['policy.view', 'policy.list', 'policy.view_all'],
        message: 'Default permissions applied due to endpoint failure'
      };
    }
  },

  /**
   * Fetch user role from backend
   */
  async fetchUserRole() {
    try {
      // First try the specific API endpoint
      try {
        const response = await axios.get('http://15.207.108.158:8000/api/user-role/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        });
        console.log('[POLICY_RBAC] Role fetched:', response.data);
        return response.data;
      } catch (specificError) {
        console.warn('[POLICY_RBAC] Specific role endpoint failed, trying fallback:', specificError);
        
        // Fallback to the debug endpoint
        const fallbackResponse = await axios.get('http://15.207.108.158:8000/api/debug-user-permissions/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        });
        console.log('[POLICY_RBAC] Role fetched from fallback:', fallbackResponse.data);
        
        // Extract role information from debug data
        return {
          role: fallbackResponse.data.role || 'User',
          is_superuser: fallbackResponse.data.is_superuser || false
        };
      }
    } catch (error) {
      console.error('[POLICY_RBAC] All role endpoints failed:', error);
      // Return default role to avoid breaking the UI
      return {
        role: 'User',
        is_superuser: false,
        message: 'Default role applied due to endpoint failure'
      };
    }
  },

  /**
   * Check if user has a specific permission
   */
  hasPermission(permission) {
    try {
      // Normal flow
      if (!rbacState.isLoaded || !rbacState.permissions) {
        console.warn('[POLICY_RBAC] RBAC not loaded, denying permission:', permission);
        return false;
      }

      const hasPermission = rbacState.permissions.permissions?.includes(permission) || false;
      console.log(`[POLICY_RBAC] Permission check: ${permission} = ${hasPermission}`);
      return hasPermission;
    } catch (error) {
      console.error(`[POLICY_RBAC] Error checking permission ${permission}:`, error);
      return false;
    }
  },

  /**
   * Check if user has any of the specified permissions
   */
  hasAnyPermission(permissions) {
    return permissions.some(permission => this.hasPermission(permission));
  },

  /**
   * Check if user has all of the specified permissions
   */
  hasAllPermissions(permissions) {
    return permissions.every(permission => this.hasPermission(permission));
  },

  /**
   * Get user role information
   */
  getUserRole() {
    return rbacState.userRole;
  },

  /**
   * Get user permissions
   */
  getUserPermissions() {
    return rbacState.permissions;
  },

  /**
   * Check if user is admin
   */
  isAdmin() {
    return rbacState.userRole?.role === 'admin' || 
           rbacState.userRole?.is_superuser === true;
  },

  /**
   * Policy-specific permission checks
   */
  canViewPolicies() {
    return this.hasAnyPermission(['policy.view', 'policy.view_all', 'policy.list']);
  },

  canCreatePolicies() {
    return this.hasPermission('policy.create');
  },

  canEditPolicies() {
    return this.hasPermission('policy.edit');
  },

  canDeletePolicies() {
    return this.hasPermission('policy.delete');
  },

  canApprovePolicies() {
    return this.hasPermission('policy.approve');
  },

  canViewFrameworks() {
    return this.hasAnyPermission(['policy.view_framework', 'policy.view']);
  },

  canCreateFrameworks() {
    return this.hasPermission('policy.create_framework');
  },

  canUploadFrameworks() {
    return this.hasPermission('policy.upload_framework');
  },

  canViewAnalytics() {
    return this.hasPermission('policy.analytics');
  },

  canViewKPIs() {
    return this.hasPermission('policy.kpi');
  },

  canViewDashboard() {
    return this.hasPermission('policy.dashboard');
  },

  canExportData() {
    return this.hasPermission('policy.export');
  },

  canManageVersions() {
    return this.hasPermission('policy.versioning');
  },

  canTailorPolicies() {
    return this.hasPermission('policy.tailoring');
  },

  canManageApprovalWorkflow() {
    return this.hasPermission('policy.approval_workflow');
  },

  /**
   * Component-specific access control
   */
  getPolicyComponentAccess() {
    try {
      // If RBAC is not loaded but we have errors, use fallback permissions
      if (!rbacState.isLoaded) {
        // Check if we're in development mode
        const isDevelopment = window.location.hostname === 'localhost' || 
                             window.location.hostname === '127.0.0.1';
        
        // In development, provide full access by default for easier testing
        if (isDevelopment) {
          console.warn('[POLICY_RBAC] RBAC not loaded, but in development mode. Granting all permissions.');
          return {
            canViewAllPolicies: true,
            canCreatePolicy: true,
            canEditPolicy: true,
            canDeletePolicy: true,
            canApprovePolicy: true,
            canViewFrameworks: true,
            canCreateFramework: true,
            canUploadFramework: true,
            canViewAnalytics: true,
            canViewKPIs: true,
            canViewDashboard: true,
            canExportData: true,
            canManageVersions: true,
            canTailorPolicies: true,
            canManageApprovalWorkflow: true,
            isAdmin: true
          };
        }
        
        // In production, provide minimal access - just viewing
        console.warn('[POLICY_RBAC] RBAC not loaded, providing minimal access');
        return {
          canViewAllPolicies: true, // Allow viewing as a fallback
          canCreatePolicy: false,
          canEditPolicy: false,
          canDeletePolicy: false,
          canApprovePolicy: false,
          canViewFrameworks: true, // Allow viewing as a fallback
          canCreateFramework: false,
          canUploadFramework: false,
          canViewAnalytics: false,
          canViewKPIs: false,
          canViewDashboard: false,
          canExportData: false,
          canManageVersions: false,
          canTailorPolicies: false,
          canManageApprovalWorkflow: false,
          isAdmin: false
        };
      }

      // Normal flow when RBAC is loaded
      return {
        canViewAllPolicies: this.canViewPolicies(),
        canCreatePolicy: this.canCreatePolicies(),
        canEditPolicy: this.canEditPolicies(),
        canDeletePolicy: this.canDeletePolicies(),
        canApprovePolicy: this.canApprovePolicies(),
        canViewFrameworks: this.canViewFrameworks(),
        canCreateFramework: this.canCreateFrameworks(),
        canUploadFramework: this.canUploadFrameworks(),
        canViewAnalytics: this.canViewAnalytics(),
        canViewKPIs: this.canViewKPIs(),
        canViewDashboard: this.canViewDashboard(),
        canExportData: this.canExportData(),
        canManageVersions: this.canManageVersions(),
        canTailorPolicies: this.canTailorPolicies(),
        canManageApprovalWorkflow: this.canManageApprovalWorkflow(),
        isAdmin: this.isAdmin()
      };
    } catch (error) {
      console.error('[POLICY_RBAC] Error getting component access:', error);
      // Provide fallback permissions in case of error
      return {
        canViewAllPolicies: true, // Always allow viewing as a fallback
        canCreatePolicy: false,
        canEditPolicy: false,
        canDeletePolicy: false,
        canApprovePolicy: false,
        canViewFrameworks: true,
        canCreateFramework: false,
        canUploadFramework: false,
        canViewAnalytics: false,
        canViewKPIs: false,
        canViewDashboard: false,
        canExportData: false,
        canManageVersions: false,
        canTailorPolicies: false,
        canManageApprovalWorkflow: false,
        isAdmin: false
      };
    }
  },

  /**
   * Route access control
   */
  canAccessRoute(routeName) {
    const routePermissions = {
      'AllPolicies': ['policy.view', 'policy.list'],
      'CreatePolicy': ['policy.create'],
      'EditPolicy': ['policy.edit'],
      'PolicyApprover': ['policy.approve'],
      'PolicyDashboard': ['policy.dashboard'],
      'UploadFramework': ['policy.upload_framework'],
      'FrameworkExplorer': ['policy.view_framework'],
      'FrameworkPolicies': ['policy.view_framework'],
      'KPIDashboard': ['policy.kpi'],
      'PerformancePage': ['policy.analytics'],
      'StatusChangeRequests': ['policy.approval_workflow'],
      'TT': ['policy.tailoring'],
      'VV': ['policy.versioning']
    };

    const requiredPermissions = routePermissions[routeName];
    if (!requiredPermissions) {
      console.warn(`[POLICY_RBAC] No permissions defined for route: ${routeName}`);
      return true; // Default to allow if no permissions defined
    }

    return this.hasAnyPermission(requiredPermissions);
  },

  /**
   * Button/Action access control
   */
  getButtonPermissions() {
    return {
      canShowCreateButton: this.canCreatePolicies(),
      canShowEditButton: this.canEditPolicies(),
      canShowDeleteButton: this.canDeletePolicies(),
      canShowApproveButton: this.canApprovePolicies(),
      canShowExportButton: this.canExportData(),
      canShowUploadButton: this.canUploadFrameworks(),
      canShowVersioningButton: this.canManageVersions(),
      canShowTailoringButton: this.canTailorPolicies(),
      canShowAnalyticsButton: this.canViewAnalytics(),
      canShowKPIButton: this.canViewKPIs(),
      canShowDashboardButton: this.canViewDashboard()
    };
  },

  /**
   * Access denied handlers using existing popup system
   */
  showPolicyAccessDenied(operation = 'access', onContactAdmin = null) {
    // TEMPORARILY DISABLED: Frontend permission checks are bypassed for development
    // TODO: Re-enable frontend permission checks when needed for production
    console.log('[POLICY_RBAC] FRONTEND RBAC DISABLED - Policy access granted for:', operation);
    return; // Don't show any popup, just return
  },

  /**
   * Specific access denied methods for different policy operations
   */
  showViewPolicyDenied(onContactAdmin = null) {
    this.showPolicyAccessDenied('view', onContactAdmin);
  },

  showCreatePolicyDenied(onContactAdmin = null) {
    this.showPolicyAccessDenied('create', onContactAdmin);
  },

  showEditPolicyDenied(onContactAdmin = null) {
    this.showPolicyAccessDenied('edit', onContactAdmin);
  },

  showDeletePolicyDenied(onContactAdmin = null) {
    this.showPolicyAccessDenied('delete', onContactAdmin);
  },

  showApprovePolicyDenied(onContactAdmin = null) {
    this.showPolicyAccessDenied('approve', onContactAdmin);
  },

  showFrameworkAccessDenied(onContactAdmin = null) {
    this.showPolicyAccessDenied('framework', onContactAdmin);
  },

  showUploadFrameworkDenied(onContactAdmin = null) {
    this.showPolicyAccessDenied('upload', onContactAdmin);
  },

  showAnalyticsDenied(onContactAdmin = null) {
    this.showPolicyAccessDenied('analytics', onContactAdmin);
  },

  showKPIDenied(onContactAdmin = null) {
    this.showPolicyAccessDenied('kpi', onContactAdmin);
  },

  showDashboardDenied(onContactAdmin = null) {
    this.showPolicyAccessDenied('dashboard', onContactAdmin);
  },

  showExportDenied(onContactAdmin = null) {
    this.showPolicyAccessDenied('export', onContactAdmin);
  },

  showVersioningDenied(onContactAdmin = null) {
    this.showPolicyAccessDenied('versioning', onContactAdmin);
  },

  showTailoringDenied(onContactAdmin = null) {
    this.showPolicyAccessDenied('tailoring', onContactAdmin);
  },

  showApprovalWorkflowDenied(onContactAdmin = null) {
    this.showPolicyAccessDenied('approval_workflow', onContactAdmin);
  },

  /**
   * Default contact admin handler
   */
  defaultContactAdmin() {
    console.log('[POLICY_RBAC] Contact admin requested');
    PopupService.info(
      'Please contact your system administrator to request access to policy management features.',
      'Contact Administrator'
    );
  },

  /**
   * Utility method to check access and execute function or show access denied
   */
  checkAccessAndExecute(permissionCheck, callback, operation = 'access') {
    if (typeof permissionCheck === 'function' ? permissionCheck() : permissionCheck) {
      if (callback) callback();
      return true;
    } else {
      this.showPolicyAccessDenied(operation);
      return false;
    }
  },

  /**
   * Clear cached permissions (useful for logout)
   */
  clearCache() {
    console.log('[POLICY_RBAC] Clearing RBAC cache');
    rbacState = {
      permissions: null,
      userRole: null,
      isLoaded: false,
      isLoading: false,
      lastFetch: null,
      error: null
    };
  },

  /**
   * Get current RBAC state (for debugging)
   */
  getState() {
    return { ....rbacState };
  },

  /**
   * Check if RBAC is loaded
   */
  isLoaded() {
    return rbacState.isLoaded;
  },

  /**
   * Check if RBAC is loading
   */
  isLoading() {
    return rbacState.isLoading;
  },

  /**
   * Get last error
   */
  getError() {
    return rbacState.error;
  }
};

// Export as default
export default PolicyRbacUtils; 