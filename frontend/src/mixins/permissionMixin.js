import { rbacService } from '@/data/api.js';

export const permissionMixin = {
  data() {
    return {
      userPermissions: {},
      userRole: null,
      userDepartment: null,
      userEntity: null,
      userId: null,
      userEmail: null,
      permissionsLoaded: false,
      permissionsError: null,
      isAuthenticated: false
    }
  },

  async created() {
    console.log('🔐 Permission Mixin: Checking authentication status...');
    await this.checkAuthenticationStatus();
  },

  methods: {
    async checkAuthenticationStatus() {
      try {
        console.log('🔐 Permission Mixin: Checking authentication...');
        const authStatus = await rbacService.checkAuthStatus();
        
        this.isAuthenticated = authStatus.is_authenticated || false;
        
        if (this.isAuthenticated) {
          console.log('🔐 Permission Mixin: User is authenticated, loading permissions...');
          await this.loadUserPermissions();
        } else {
          console.log('🔐 Permission Mixin: User not authenticated, using default permissions');
          this.setDefaultPermissions();
        }
      } catch (error) {
        console.error('❌ Permission Mixin: Error checking authentication:', error);
        this.isAuthenticated = false;
        this.setDefaultPermissions();
      }
    },

    async loadUserPermissions() {
      try {
        console.log('🔐 Permission Mixin: Fetching permissions from API...');
        const response = await rbacService.getUserPermissions();
        
        // Check if we got a valid response or an auth error
        if (response.message === 'User not authenticated') {
          console.log('🔐 Permission Mixin: User not authenticated, using default permissions');
          this.isAuthenticated = false;
          this.setDefaultPermissions();
          return;
        }
        
        this.userPermissions = response.permissions || {};
        this.userRole = response.role;
        this.userDepartment = response.department;
        this.userEntity = response.entity;
        this.userId = response.user_id;
        this.userEmail = response.email;
        this.permissionsLoaded = true;
        this.isAuthenticated = true;
        this.permissionsError = null;
        
        // Debug logging
        console.log('🔐 Permission Mixin: Permissions loaded successfully');
        console.log('   👤 User ID:', this.userId);
        console.log('   👤 User Role:', this.userRole);
        console.log('   📧 Email:', this.userEmail);
        console.log('   🏢 Department:', this.userDepartment);
        console.log('   🏭 Entity:', this.userEntity);
        console.log('   🔑 Permissions:', this.userPermissions);
        
      } catch (error) {
        console.error('❌ Permission Mixin: Error loading permissions:', error);
        this.permissionsError = error.message || 'Failed to load permissions';
        this.isAuthenticated = false;
        this.setDefaultPermissions();
      }
    },

    setDefaultPermissions() {
      this.userPermissions = {
        incident: {
          create: false,
          edit: false,
          view: false,
          assign: false,
          approve: false,
          delete: false
        },
        audit: {
          view: false,
          conduct: false,
          review: false,
          assign: false,
          analytics: false
        }
      };
      this.userRole = null;
      this.userDepartment = null;
      this.userEntity = null;
      this.userId = null;
      this.userEmail = null;
      this.permissionsLoaded = true;
      console.log('🔐 Permission Mixin: Default permissions set');
    },

    // Method to manually reload permissions after login
    async reloadPermissions() {
      console.log('🔐 Permission Mixin: Manually reloading permissions...');
      this.permissionsLoaded = false;
      this.permissionsError = null;
      await this.checkAuthenticationStatus();
    },

    // Core permission checking method
    hasPermission(module, permission) {
      // TEMPORARILY DISABLED: Frontend permission checks are bypassed for development
      // TODO: Re-enable frontend permission checks when needed for production
      console.log(`🔐 FRONTEND RBAC DISABLED - Permission granted: ${module}.${permission}`);
      return true; // Always return true
    },

    // Incident-specific permission methods
    canCreateIncident() {
      return this.hasPermission('incident', 'create');
    },

    canEditIncident() {
      return this.hasPermission('incident', 'edit');
    },

    canViewIncident() {
      return this.hasPermission('incident', 'view');
    },

    canAssignIncident() {
      return this.hasPermission('incident', 'assign');
    },

    canEscalateIncident() {
      return this.hasPermission('incident', 'escalate');
    },

    canViewIncidentAnalytics() {
      return this.hasPermission('incident', 'analytics');
    },

    // Audit-specific permission methods
    canViewAudit() {
      return this.hasPermission('audit', 'view');
    },

    canConductAudit() {
      return this.hasPermission('audit', 'conduct');
    },

    canReviewAudit() {
      return this.hasPermission('audit', 'review');
    },

    canAssignAudit() {
      return this.hasPermission('audit', 'assign');
    },

    canViewAuditAnalytics() {
      return this.hasPermission('audit', 'analytics');
    },

    // General analytics permission
    canViewAnalytics() {
      return this.canViewIncidentAnalytics() || this.canViewAuditAnalytics();
    },

    // Debug method to log user access attempt
    logUserAction(action, resourceType = null, resourceId = null) {
      console.log('🎯 User Action Logged:');
      console.log('   👤 User Role:', this.userRole);
      console.log('   🏢 Department:', this.userDepartment);
      console.log('   🏭 Entity:', this.userEntity);
      console.log('   🎯 Action:', action);
      console.log('   📊 Resource:', resourceType, resourceId);
      console.log('   ⏰ Timestamp:', new Date().toISOString());
    },

    // Method to check if user has any permissions at all
    hasAnyPermissions() {
      if (!this.permissionsLoaded) return false;
      
      for (const module in this.userPermissions) {
        for (const permission in this.userPermissions[module]) {
          if (this.userPermissions[module][permission]) {
            return true;
          }
        }
      }
      return false;
    },

    // Method to get all allowed actions for current user
    getAllowedActions() {
      const allowedActions = [];
      
      for (const module in this.userPermissions) {
        for (const permission in this.userPermissions[module]) {
          if (this.userPermissions[module][permission]) {
            allowedActions.push(`${module}.${permission}`);
          }
        }
      }
      
      console.log('🔑 User Allowed Actions:', allowedActions);
      return allowedActions;
    }
  },

  computed: {
    // Computed property for reactive permission checking
    permissionStatus() {
      return {
        loaded: this.permissionsLoaded,
        error: this.permissionsError,
        authenticated: this.isAuthenticated,
        hasPermissions: this.hasAnyPermissions(),
        userId: this.userId,
        email: this.userEmail,
        role: this.userRole,
        department: this.userDepartment,
        entity: this.userEntity
      };
    }
  }
}; 