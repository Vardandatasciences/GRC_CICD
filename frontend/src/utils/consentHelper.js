/**
 * Consent Helper Utility
 * Provides a reusable function to check and handle consent before API calls
 */

import { checkConsentRequired } from './consentManager.js';

/**
 * Check consent and return consent data to include in request
 * @param {string} actionType - The consent action type (e.g., 'create_incident')
 * @param {Function} showModalCallback - Callback to show consent modal (should return Promise<boolean>)
 * @returns {Promise<{consent_accepted: boolean, consent_config_id: number|null, framework_id: string|null}>}
 */
export async function checkAndGetConsentData(actionType, showModalCallback) {
  try {
    console.log(`🔍 [Consent] Checking consent requirement for ${actionType}`);
    
    // Check if consent is required from database
    const { required, config } = await checkConsentRequired(actionType);
    
    if (required && config) {
      console.log(`✅ [Consent] Consent required for ${actionType}`);
      
      // Show modal using callback
      if (showModalCallback) {
        try {
          const accepted = await showModalCallback(actionType, config);
          
          if (!accepted) {
            console.log(`❌ [Consent] User declined consent for ${actionType}`);
            return {
              consent_accepted: false,
              consent_config_id: null,
              framework_id: null,
              userDeclined: true
            };
          }
          
          console.log(`✅ [Consent] User accepted consent for ${actionType}`);
          
          // Return consent data to include in request
          return {
            consent_accepted: true,
            consent_config_id: config.config_id,
            framework_id: localStorage.getItem('framework_id'),
            userDeclined: false
          };
        } catch (error) {
          console.log(`❌ [Consent] User cancelled consent modal for ${actionType}`);
          return {
            consent_accepted: false,
            consent_config_id: null,
            framework_id: null,
            userDeclined: true
          };
        }
      } else {
        console.warn(`⚠️ [Consent] No modal callback provided for ${actionType}`);
        // If no callback, assume consent is not accepted
        return {
          consent_accepted: false,
          consent_config_id: null,
          framework_id: null,
          userDeclined: true
        };
      }
    } else {
      console.log(`❌ [Consent] No consent required for ${actionType}`);
      // No consent required
      return {
        consent_accepted: false,
        consent_config_id: null,
        framework_id: null,
        userDeclined: false
      };
    }
  } catch (error) {
    console.error(`❌ [Consent] Error checking consent for ${actionType}:`, error);
    // On error, don't block the action
    return {
      consent_accepted: false,
      consent_config_id: null,
      framework_id: null,
      userDeclined: false
    };
  }
}

/**
 * Add consent data to request payload if consent was required and accepted
 * @param {Object} payload - The request payload
 * @param {Object} consentData - The consent data from checkAndGetConsentData
 * @returns {Object} - Payload with consent data added
 */
export function addConsentToPayload(payload, consentData) {
  if (consentData && consentData.consent_accepted && consentData.consent_config_id) {
    return {
      ...payload,
      consent_accepted: true,
      consent_config_id: consentData.consent_config_id,
      framework_id: consentData.framework_id || localStorage.getItem('framework_id')
    };
  }
  return payload;
}

