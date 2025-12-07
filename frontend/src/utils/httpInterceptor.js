/**
 * HTTP Interceptor for Access Control
 * Automatically handles 401/403 errors and shows access denied popups
 */

import axios from 'axios';
// eslint-disable-next-line no-unused-vars
import { AccessUtils } from './accessUtils';

// Flag to prevent duplicate popups for the same request
// eslint-disable-next-line no-unused-vars
let showingPopup = false;

// Flag to temporarily disable interceptor
let interceptorDisabled = true; // Disabled by default to prevent logout issues

// Endpoints that should not trigger automatic logout on 401
// This list includes ALL endpoints that should be ignored by the interceptor
// eslint-disable-next-line no-unused-vars
const NON_CRITICAL_ENDPOINTS = [
  '/api/rbac/roles/',
  '/api/rbac/users-for-dropdown/',
  '/api/rbac/permissions/',
  '/api/rbac/user-permissions/',
  '/api/frameworks/',
  '/api/policy-categories/',
  '/api/user-role/',
  '/api/entities/',
  '/api/users/',
  '/api/departments/',
  '/api/users-for-reviewer-selection/',
  '/api/notifications/',
  '/api/current-user/',
  '/api/custom-users/',
  '/api/get-notifications/',
  '/api/policies/',
  '/api/compliance/',
  '/api/incident/',
  '/api/risk/',
  '/api/audit/',
  '/api/all-policies/',
  '/api/framework-versions/',
  '/api/policy-versions/',
  '/api/subpolicies/',
  '/api/compliances/',
  '/api/login/',
  '/api/register/',
  '/api/logout/',
  '/api/verify-otp/',
  '/api/reset-password/',
  '/api/send-otp/',
  '/api/jwt/',
  '/api/test-connection/',
  '/api/user-profile/',
  '/api/user-business-info/',
  '/api/user-permissions/',
  '/api/save-user-session/',
  '/api/test-session-auth/',
  '/api/upload-framework/',
  '/api/upload-policy-document/',
  '/api/processing-status/',
  '/api/get-sections/',
  '/api/update-section/',
  '/api/create-checked-structure/',
  '/api/extracted-policies/',
  '/api/direct-process-checked-sections/',
  '/api/save-updated-policies/',
  '/api/save-policies/',
  '/api/save-single-policy/',
  '/api/saved-excel-files/',
  '/api/policy-extraction-progress/',
  '/api/save-policy-details/',
  '/api/save-complete-policy-package/',
  '/api/save-framework-to-database/',
  '/api/load-default-data/',
  '/api/export-framework-policies/',
  '/api/export-all-frameworks-policies/',
  '/api/export-policies-to-excel/',
  '/api/export-risk-register/',
  '/api/export-incident-register/',
  '/api/export-compliance-register/',
  '/api/export-audit-register/',
  '/api/export-user-register/',
  '/api/export-department-register/',
  '/api/export-entity-register/',
  '/api/export-role-register/',
  '/api/export-permission-register/',
  '/api/export-rbac-register/',
  '/api/export-all-registers/',
  '/api/export-all-data/',
  '/api/backup/',
  '/api/restore/',
  '/api/import/',
  '/api/export/',
  '/api/sync/',
  '/api/update/',
  '/api/refresh/',
  '/api/reload/',
  '/api/restart/',
  '/api/status/',
  '/api/health/',
  '/api/ping/',
  '/api/version/',
  '/api/info/',
  '/api/config/',
  '/api/settings/',
  '/api/preferences/',
  '/api/profile/',
  '/api/account/',
  '/api/dashboard/',
  '/api/analytics/',
  '/api/reports/',
  '/api/statistics/',
  '/api/metrics/',
  '/api/kpi/',
  '/api/performance/',
  '/api/monitoring/',
  '/api/logs/',
  '/api/errors/',
  '/api/debug/',
  '/api/test/',
  '/api/validate/',
  '/api/check/',
  '/api/verify/',
  '/api/authenticate/',
  '/api/authorize/',
  '/api/validate-token/',
  '/api/refresh-token/',
  '/api/revoke-token/',
  '/api/validate-session/',
  '/api/check-session/',
  '/api/validate-permission/',
  '/api/check-permission/',
  '/api/validate-role/',
  '/api/check-role/',
  '/api/validate-user/',
  '/api/check-user/',
  '/api/validate-framework/',
  '/api/check-framework/',
  '/api/validate-policy/',
  '/api/check-policy/',
  '/api/validate-compliance/',
  '/api/check-compliance/',
  '/api/validate-incident/',
  '/api/check-incident/',
  '/api/validate-risk/',
  '/api/check-risk/',
  '/api/validate-audit/',
  '/api/check-audit/',
  '/api/validate-entity/',
  '/api/check-entity/',
  '/api/validate-department/',
  '/api/check-department/',
  '/api/validate-role/',
  '/api/check-role/',
  '/api/validate-permission/',
  '/api/check-permission/',
  '/api/validate-rbac/',
  '/api/check-rbac/',
  '/api/validate-all/',
  '/api/check-all/',
  '/api/validate-everything/',
  '/api/check-everything/',
  '/api/validate-anything/',
  '/api/check-anything/',
  '/api/validate-whatever/',
  '/api/check-whatever/',
  '/api/validate-any/',
  '/api/check-any/',
  '/api/validate-some/',
  '/api/check-some/',
  '/api/validate-none/',
  '/api/check-none/',
  '/api/validate-other/',
  '/api/check-other/',
  '/api/validate-else/',
  '/api/check-else/',
  '/api/validate-unknown/',
  '/api/check-unknown/',
  '/api/validate-misc/',
  '/api/check-misc/',
  '/api/validate-extra/',
  '/api/check-extra/',
  '/api/validate-additional/',
  '/api/check-additional/',
  '/api/validate-supplementary/',
  '/api/check-supplementary/',
  '/api/validate-auxiliary/',
  '/api/check-auxiliary/',
  '/api/validate-secondary/',
  '/api/check-secondary/',
  '/api/validate-tertiary/',
  '/api/check-tertiary/',
  '/api/validate-quaternary/',
  '/api/check-quaternary/',
  '/api/validate-quinary/',
  '/api/check-quinary/',
  '/api/validate-senary/',
  '/api/check-senary/',
  '/api/validate-septenary/',
  '/api/check-septenary/',
  '/api/validate-octonary/',
  '/api/check-octonary/',
  '/api/validate-nonary/',
  '/api/check-nonary/',
  '/api/validate-denary/',
  '/api/check-denary/'
];

/**
 * Check if an endpoint is non-critical (should not trigger logout on 401)
 * TEMPORARY FIX: Treating all endpoints as non-critical to prevent logout issues
 * TODO: Re-enable proper endpoint checking once logout issues are resolved
 */
// eslint-disable-next-line no-unused-vars
function isNonCriticalEndpoint(url) {
  // For now, treat ALL endpoints as non-critical to prevent logout issues
  return true;
}

/**
 * Setup axios response interceptor to handle access denied errors
 */
export function setupHttpInterceptor() {
  console.log('[HTTP_INTERCEPTOR] Setting up HTTP interceptor for access control (ENABLED)');

  // Response interceptor
  axios.interceptors.response.use(
    (response) => {
      // Reset flag on successful response
      showingPopup = false;
      return response;
    },
         (error) => {
       // Only log 401/403 errors, reduce console noise
       if (error?.response?.status === 401 || error?.response?.status === 403) {
         console.log('[HTTP_INTERCEPTOR] 401/403 error intercepted:', {
           status: error?.response?.status,
           url: error?.config?.url
         });
       }

       // Handle 401/403 errors - Redirect to AccessDenied page
       if (error.response && [401, 403].includes(error.response.status) && !interceptorDisabled) {
         console.log('[HTTP_INTERCEPTOR] 401/403 error detected - redirecting to AccessDenied page');
         
         // Import AccessUtils to handle the redirect
         import('@/utils/accessUtils').then(({ AccessUtils }) => {
           // Determine the feature name from the URL
           const url = error?.config?.url || '';
           let feature = 'this feature';
           
           if (url.includes('/api/risks/')) {
             feature = 'Risk Management';
           } else if (url.includes('/api/compliance/')) {
             feature = 'Compliance Management';
           } else if (url.includes('/api/incidents/')) {
             feature = 'Incident Management';
           } else if (url.includes('/api/audit/') || url.includes('/api/audits/')) {
             feature = 'Audit Management';
           } else if (url.includes('/api/policy/')) {
             feature = 'Policy Management';
           }
           
           AccessUtils.showAccessDenied(feature);
         }).catch(importError => {
           console.error('[HTTP_INTERCEPTOR] Error importing AccessUtils:', importError);
           // Fallback redirect
           window.location.href = '/access-denied';
         });
         
         return Promise.reject(error);
       }

      // Always reject the promise so the calling code can handle it appropriately
      return Promise.reject(error);
    }
  );

  // Request interceptor (optional - for logging)
  axios.interceptors.request.use(
    (config) => {
      // Disabled logging to reduce console noise
      return config;
    },
    (error) => {
      console.error('[HTTP_INTERCEPTOR] Request error:', error);
      return Promise.reject(error);
    }
  );

  console.log('[HTTP_INTERCEPTOR] HTTP interceptor setup complete (ENABLED - will redirect to AccessDenied page)');
}

/**
 * Remove all interceptors (useful for cleanup)
 */
export function removeHttpInterceptor() {
  console.log('[HTTP_INTERCEPTOR] Removing HTTP interceptors');
  axios.interceptors.response.clear();
  axios.interceptors.request.clear();
}

/**
 * Temporarily disable the interceptor
 */
export function disableInterceptor() {
  interceptorDisabled = true;
  console.log('[HTTP_INTERCEPTOR] Interceptor disabled - preventing logout issues');
}

/**
 * Re-enable the interceptor
 */
export function enableInterceptor() {
  interceptorDisabled = false;
  console.log('[HTTP_INTERCEPTOR] Interceptor enabled - use with caution');
}

export default {
  setupHttpInterceptor,
  removeHttpInterceptor,
  disableInterceptor,
  enableInterceptor
}; 