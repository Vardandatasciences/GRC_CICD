/**
 * RBAC Service for Frontend
 * Handles permission checks and user role management using JWT tokens
 */

import axios from 'axios';
import { API_BASE_URL } from '../config/api.js';

class RBACService {
    constructor() {
        this.baseURL = API_BASE_URL;
        this.userPermissions = null;
        this.userRole = null;
        this.userId = null;
    }

    /**
     * Initialize RBAC service with user data from JWT
     */
    async initialize() {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                console.log('[RBAC_SERVICE] No access token found');
                return false;
            }

            // Decode JWT to get user info
            const payload = this.decodeJWT(token);
            if (!payload) {
                console.log('[RBAC_SERVICE] Invalid JWT token');
                return false;
            }

            this.userId = payload.user_id || payload.UserId;
            this.userRole = payload.role || 'user';

            // Fetch user permissions from backend
            await this.fetchUserPermissions();
            
            console.log('[RBAC_SERVICE] RBAC service initialized for user:', this.userId);
            return true;
        } catch (error) {
            console.error('[RBAC_SERVICE] Error initializing RBAC service:', error);
            return false;
        }
    }

    /**
     * Decode JWT token to extract payload
     */
    decodeJWT(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            return JSON.parse(jsonPayload);
        } catch (error) {
            console.error('[RBAC_SERVICE] Error decoding JWT:', error);
            return null;
        }
    }

    /**
     * Fetch user permissions from backend
     */
    async fetchUserPermissions() {
        try {
            // Create axios instance with JWT token
            const api = axios.create({
                baseURL: this.baseURL,
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            // Add request interceptor to include JWT token
            api.interceptors.request.use((config) => {
                const token = localStorage.getItem('access_token') || localStorage.getItem('token');
                if (token) {
                    config.headers.Authorization = `Bearer ${token}`;
                }
                return config;
            });
            
            const response = await api.get(`${this.baseURL}/api/rbac/user-permissions/`);
            this.userPermissions = response.data.permissions || {};
            console.log('[RBAC_SERVICE] User permissions fetched:', this.userPermissions);
        } catch (error) {
            console.error('[RBAC_SERVICE] Error fetching user permissions:', error);
            // Provide fallback permissions for better user experience
            this.userPermissions = {
                policy: {
                    view_all_policy: true,
                    create_policy: false,
                    edit_policy: false,
                    approve_policy: false,
                    create_framework: false,
                    approve_framework: false,
                    policy_performance_analytics: false
                },
                compliance: {
                    view_all_compliance: true,
                    create_compliance: false,
                    edit_compliance: false,
                    approve_compliance: false,
                    compliance_performance_analytics: false
                },
                audit: {
                    view_audit_reports: true,
                    conduct_audit: false,
                    review_audit: false,
                    assign_audit: false,
                    audit_performance_analytics: false
                },
                risk: {
                    view_all_risk: true,
                    create_risk: false,
                    edit_risk: false,
                    approve_risk: false,
                    assign_risk: false,
                    evaluate_assigned_risk: false,
                    risk_performance_analytics: false
                },
                incident: {
                    view_all_incident: true,
                    create_incident: false,
                    edit_incident: false,
                    assign_incident: false,
                    evaluate_assigned_incident: false,
                    escalate_to_risk: false,
                    incident_performance_analytics: false
                }
            };
            console.log('[RBAC_SERVICE] Using fallback permissions due to API error');
        }
    }

    /**
     * Check if user has a specific permission
     * @param {string} module - Module name (e.g., 'policy', 'compliance', 'audit', 'risk', 'incident')
     * @param {string} permission - Permission name (e.g., 'view_all_policy', 'create_policy')
     * @returns {boolean} True if user has permission
     */
    hasPermission(module, permission) {
        if (!this.userPermissions) {
            console.warn('[RBAC_SERVICE] User permissions not loaded');
            return false;
        }

        const modulePermissions = this.userPermissions[module] || {};
        const hasPermission = modulePermissions[permission] === true;
        
        console.log(`[RBAC_SERVICE] Checking permission: ${module}.${permission} = ${hasPermission}`);
        return hasPermission;
    }

    /**
     * Check if user has a specific permission (async version for router guards)
     * @param {string} module - Module name (e.g., 'policy', 'compliance', 'audit', 'risk', 'incident')
     * @param {string} permission - Permission name (e.g., 'view_all_policy', 'create_policy')
     * @returns {Promise<boolean>} Promise that resolves to true if user has permission
     */
    async checkPermission(module, permission) {
        // Initialize if not already done
        if (!this.userPermissions) {
            await this.initialize();
        }
        
        return this.hasPermission(module, permission);
    }

    /**
     * Check if user has any of the specified permissions
     * @param {string} module - Module name
     * @param {Array} permissions - Array of permission names
     * @returns {boolean} True if user has any of the permissions
     */
    hasAnyPermission(module, permissions) {
        return permissions.some(permission => this.hasPermission(module, permission));
    }

    /**
     * Check if user has all of the specified permissions
     * @param {string} module - Module name
     * @param {Array} permissions - Array of permission names
     * @returns {boolean} True if user has all permissions
     */
    hasAllPermissions(module, permissions) {
        return permissions.every(permission => this.hasPermission(module, permission));
    }

    /**
     * Check if user is a system admin
     * @returns {boolean} True if user is admin
     */
    isAdmin() {
        return this.userRole === 'admin' || this.userRole === 'system_admin';
    }

    /**
     * Get user role
     * @returns {string} User role
     */
    getUserRole() {
        return this.userRole;
    }

    /**
     * Get user ID
     * @returns {string} User ID
     */
    getUserId() {
        return this.userId;
    }

    /**
     * Get all user permissions
     * @returns {Object} User permissions object
     */
    getUserPermissions() {
        return this.userPermissions;
    }

    /**
     * Check policy permissions
     */
    canViewPolicy() {
        return this.hasPermission('policy', 'view_all_policy');
    }

    canCreatePolicy() {
        return this.hasPermission('policy', 'create_policy');
    }

    canEditPolicy() {
        return this.hasPermission('policy', 'edit_policy');
    }

    canApprovePolicy() {
        return this.hasPermission('policy', 'approve_policy');
    }

    canDeletePolicy() {
        return this.hasPermission('policy', 'edit_policy'); // Uses edit permission
    }

    canCreateFramework() {
        return this.hasPermission('policy', 'create_framework');
    }

    canApproveFramework() {
        return this.hasPermission('policy', 'approve_framework');
    }

    canViewPolicyAnalytics() {
        return this.hasPermission('policy', 'policy_performance_analytics');
    }

    /**
     * Check compliance permissions
     */
    canViewCompliance() {
        return this.hasPermission('compliance', 'view_all_compliance');
    }

    canCreateCompliance() {
        return this.hasPermission('compliance', 'create_compliance');
    }

    canEditCompliance() {
        return this.hasPermission('compliance', 'edit_compliance');
    }

    canApproveCompliance() {
        return this.hasPermission('compliance', 'approve_compliance');
    }

    canAccessComplianceAnalytics() {
        return this.hasPermission('compliance', 'compliance_performance_analytics');
    }

    /**
     * Check audit permissions
     */
    canViewAudit() {
        return this.hasPermission('audit', 'view_audit_reports');
    }

    canConductAudit() {
        return this.hasPermission('audit', 'conduct_audit');
    }

    canReviewAudit() {
        return this.hasPermission('audit', 'review_audit');
    }

    canAssignAudit() {
        return this.hasPermission('audit', 'assign_audit');
    }

    canAccessAuditAnalytics() {
        return this.hasPermission('audit', 'audit_performance_analytics');
    }

    /**
     * Check risk permissions
     */
    canViewRisk() {
        return this.hasPermission('risk', 'view_all_risk');
    }

    canCreateRisk() {
        return this.hasPermission('risk', 'create_risk');
    }

    canEditRisk() {
        return this.hasPermission('risk', 'edit_risk');
    }

    canApproveRisk() {
        return this.hasPermission('risk', 'approve_risk');
    }

    canAssignRisk() {
        return this.hasPermission('risk', 'assign_risk');
    }

    canEvaluateAssignedRisk() {
        return this.hasPermission('risk', 'evaluate_assigned_risk');
    }

    canAccessRiskAnalytics() {
        return this.hasPermission('risk', 'risk_performance_analytics');
    }

    /**
     * Check incident permissions
     */
    canViewIncident() {
        return this.hasPermission('incident', 'view_all_incident');
    }

    canCreateIncident() {
        return this.hasPermission('incident', 'create_incident');
    }

    canEditIncident() {
        return this.hasPermission('incident', 'edit_incident');
    }

    canAssignIncident() {
        return this.hasPermission('incident', 'assign_incident');
    }

    canEvaluateAssignedIncident() {
        return this.hasPermission('incident', 'evaluate_assigned_incident');
    }

    canEscalateToRisk() {
        return this.hasPermission('incident', 'escalate_to_risk');
    }

    canAccessIncidentAnalytics() {
        return this.hasPermission('incident', 'incident_performance_analytics');
    }

    /**
     * Clear user data (for logout)
     */
    clearUserData() {
        this.userPermissions = null;
        this.userRole = null;
        this.userId = null;
        console.log('[RBAC_SERVICE] User data cleared');
    }

    /**
     * Refresh user permissions
     */
    async refreshPermissions() {
        await this.fetchUserPermissions();
    }
}

// Create singleton instance
const rbacService = new RBACService();

export default rbacService;
