/**
 * Policy RBAC Mixin
 * Vue mixin for easy integration of Policy RBAC into components
 */

import { ref, computed, onMounted } from 'vue';
import { PolicyRbacUtils } from '@/utils/policyRbacUtils';

export const policyRbacMixin = {
  setup() {
    // Reactive state
    const rbacLoading = ref(true);
    const rbacError = ref(null);
    const rbacState = ref(null);

    // Computed properties for permissions
    const canViewPolicies = computed(() => rbacState.value?.canViewAllPolicies || false);
    const canCreatePolicies = computed(() => rbacState.value?.canCreatePolicy || false);
    const canEditPolicies = computed(() => rbacState.value?.canEditPolicy || false);
    const canDeletePolicies = computed(() => rbacState.value?.canDeletePolicy || false);
    const canApprovePolicies = computed(() => rbacState.value?.canApprovePolicy || false);
    const canViewFrameworks = computed(() => rbacState.value?.canViewFrameworks || false);
    const canCreateFrameworks = computed(() => rbacState.value?.canCreateFramework || false);
    const canUploadFrameworks = computed(() => rbacState.value?.canUploadFramework || false);
    const canViewAnalytics = computed(() => rbacState.value?.canViewAnalytics || false);
    const canViewKPIs = computed(() => rbacState.value?.canViewKPIs || false);
    const canViewDashboard = computed(() => rbacState.value?.canViewDashboard || false);
    const canExportData = computed(() => rbacState.value?.canExportData || false);
    const canManageVersions = computed(() => rbacState.value?.canManageVersions || false);
    const canTailorPolicies = computed(() => rbacState.value?.canTailorPolicies || false);
    const canManageApprovalWorkflow = computed(() => rbacState.value?.canManageApprovalWorkflow || false);
    const isAdmin = computed(() => rbacState.value?.isAdmin || false);
    const userRole = computed(() => PolicyRbacUtils.getUserRole()?.role || 'Not assigned');

    // Initialize RBAC
    const initializeRBAC = async () => {
      try {
        rbacLoading.value = true;
        rbacError.value = null;

        // Initialize RBAC system
        await PolicyRbacUtils.init();

        // Get component access permissions
        rbacState.value = PolicyRbacUtils.getPolicyComponentAccess();
        
        console.log('[POLICY_RBAC_MIXIN] RBAC initialized:', rbacState.value);
        
      } catch (error) {
        console.error('[POLICY_RBAC_MIXIN] Failed to initialize RBAC:', error);
        rbacError.value = error.message;
        
        // Set default denied state
        rbacState.value = {
          canViewAllPolicies: false,
          canCreatePolicy: false,
          canEditPolicy: false,
          canDeletePolicy: false,
          canApprovePolicy: false,
          canViewFrameworks: false,
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
      } finally {
        rbacLoading.value = false;
      }
    };

    // Helper methods
    const checkAndExecute = (permissionCheck, callback, operation = 'access') => {
      return PolicyRbacUtils.checkAccessAndExecute(permissionCheck, callback, operation);
    };

    const navigateWithPermissionCheck = (routeName, router, callback = null) => {
      if (PolicyRbacUtils.canAccessRoute(routeName)) {
        if (callback) {
          callback();
        } else if (router) {
          router.push({ name: routeName });
        }
      } else {
        PolicyRbacUtils.showPolicyAccessDenied('access');
      }
    };

    const showAccessDenied = (operation = 'access') => {
      PolicyRbacUtils.showPolicyAccessDenied(operation);
    };

    const handleUnauthorizedAccess = (error, operation = 'access') => {
      console.error('[POLICY_RBAC_MIXIN] Unauthorized access:', error);
      if (error.response?.status === 403) {
        PolicyRbacUtils.showPolicyAccessDenied(operation);
      }
    };

    // Return reactive properties and methods
    return {
      // Loading states
      rbacLoading,
      rbacError,
      rbacState,

      // Permission checks
      canViewPolicies,
      canCreatePolicies,
      canEditPolicies,
      canDeletePolicies,
      canApprovePolicies,
      canViewFrameworks,
      canCreateFrameworks,
      canUploadFrameworks,
      canViewAnalytics,
      canViewKPIs,
      canViewDashboard,
      canExportData,
      canManageVersions,
      canTailorPolicies,
      canManageApprovalWorkflow,
      isAdmin,
      userRole,

      // Methods
      initializeRBAC,
      checkAndExecute,
      navigateWithPermissionCheck,
      showAccessDenied,
      handleUnauthorizedAccess
    };
  }
};

// Composition API version for script setup
export const usePolicyRbac = () => {
  // Reactive state
  const rbacLoading = ref(true);
  const rbacError = ref(null);
  const rbacState = ref(null);

  // Computed properties for permissions
  const canViewPolicies = computed(() => rbacState.value?.canViewAllPolicies || false);
  const canCreatePolicies = computed(() => rbacState.value?.canCreatePolicy || false);
  const canEditPolicies = computed(() => rbacState.value?.canEditPolicy || false);
  const canDeletePolicies = computed(() => rbacState.value?.canDeletePolicy || false);
  const canApprovePolicies = computed(() => rbacState.value?.canApprovePolicy || false);
  const canViewFrameworks = computed(() => rbacState.value?.canViewFrameworks || false);
  const canCreateFrameworks = computed(() => rbacState.value?.canCreateFramework || false);
  const canUploadFrameworks = computed(() => rbacState.value?.canUploadFramework || false);
  const canViewAnalytics = computed(() => rbacState.value?.canViewAnalytics || false);
  const canViewKPIs = computed(() => rbacState.value?.canViewKPIs || false);
  const canViewDashboard = computed(() => rbacState.value?.canViewDashboard || false);
  const canExportData = computed(() => rbacState.value?.canExportData || false);
  const canManageVersions = computed(() => rbacState.value?.canManageVersions || false);
  const canTailorPolicies = computed(() => rbacState.value?.canTailorPolicies || false);
  const canManageApprovalWorkflow = computed(() => rbacState.value?.canManageApprovalWorkflow || false);
  const isAdmin = computed(() => rbacState.value?.isAdmin || false);
  const userRole = computed(() => PolicyRbacUtils.getUserRole()?.role || 'Not assigned');

  // Initialize RBAC
  const initializeRBAC = async () => {
    try {
      rbacLoading.value = true;
      rbacError.value = null;

      // Initialize RBAC system
      await PolicyRbacUtils.init();

      // Get component access permissions
      rbacState.value = PolicyRbacUtils.getPolicyComponentAccess();
      
      console.log('[POLICY_RBAC_COMPOSABLE] RBAC initialized:', rbacState.value);
      
    } catch (error) {
      console.error('[POLICY_RBAC_COMPOSABLE] Failed to initialize RBAC:', error);
      rbacError.value = error.message;
      
      // Set default denied state
      rbacState.value = {
        canViewAllPolicies: false,
        canCreatePolicy: false,
        canEditPolicy: false,
        canDeletePolicy: false,
        canApprovePolicy: false,
        canViewFrameworks: false,
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
    } finally {
      rbacLoading.value = false;
    }
  };

  // Helper methods
  const checkAndExecute = (permissionCheck, callback, operation = 'access') => {
    return PolicyRbacUtils.checkAccessAndExecute(permissionCheck, callback, operation);
  };

  const navigateWithPermissionCheck = (routeName, router, callback = null) => {
    if (PolicyRbacUtils.canAccessRoute(routeName)) {
      if (callback) {
        callback();
      } else if (router) {
        router.push({ name: routeName });
      }
    } else {
      PolicyRbacUtils.showPolicyAccessDenied('access');
    }
  };

  const showAccessDenied = (operation = 'access') => {
    PolicyRbacUtils.showPolicyAccessDenied(operation);
  };

  const handleUnauthorizedAccess = (error, operation = 'access') => {
    PolicyRbacUtils.handleUnauthorizedAccess(error, operation);
  };

  // Auto-initialize on mount
  onMounted(() => {
    initializeRBAC();
  });

  // Return reactive properties and methods
  return {
    // Loading states
    rbacLoading,
    rbacError,
    rbacState,

    // Permission checks
    canViewPolicies,
    canCreatePolicies,
    canEditPolicies,
    canDeletePolicies,
    canApprovePolicies,
    canViewFrameworks,
    canCreateFrameworks,
    canUploadFrameworks,
    canViewAnalytics,
    canViewKPIs,
    canViewDashboard,
    canExportData,
    canManageVersions,
    canTailorPolicies,
    canManageApprovalWorkflow,
    isAdmin,
    userRole,

    // Methods
    initializeRBAC,
    checkAndExecute,
    navigateWithPermissionCheck,
    showAccessDenied,
    handleUnauthorizedAccess
  };
};

export default policyRbacMixin; 