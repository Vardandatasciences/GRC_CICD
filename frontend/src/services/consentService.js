/**
 * Global Consent Service
 * Provides centralized consent checking and enforcement
 */

import { checkConsentRequired, CONSENT_ACTIONS } from '@/utils/consentManager.js';

class ConsentService {
  constructor() {
    this.modalComponent = null;
  }

  /**
   * Register the global consent modal component
   * Should be called from App.vue or main.js
   */
  registerModal(modalComponent) {
    this.modalComponent = modalComponent;
  }

  /**
   * Check if consent is required and show modal if needed
   * @param {string} actionType - The action type from CONSENT_ACTIONS
   * @param {Function} callback - The callback to execute after consent (optional)
   * @returns {Promise<boolean>} - Returns true if action can proceed, false if cancelled
   */
  async checkAndRequestConsent(actionType, callback = null) {
    try {
      // Check if consent is required
      const { required, config } = await checkConsentRequired(actionType);

      // If consent not required, execute immediately
      if (!required || !config) {
        console.log(`[Consent] No consent required for action: ${actionType}`);
        if (callback) {
          await callback();
        }
        return true;
      }

      // Consent is required - show modal
      console.log(`[Consent] Consent required for action: ${actionType}`, config);
      
      if (!this.modalComponent) {
        console.error('[Consent] Modal component not registered. Cannot show consent prompt.');
        // Allow action to proceed even if modal is not available
        if (callback) {
          await callback();
        }
        return true;
      }

      // Show the consent modal and wait for user response
      try {
        console.log('[Consent] Attempting to show modal. Modal component:', this.modalComponent);
        console.log('[Consent] Modal component type:', typeof this.modalComponent);
        console.log('[Consent] Modal component show method:', typeof this.modalComponent?.show);
        
        if (typeof this.modalComponent?.show !== 'function') {
          console.error('[Consent] Modal component does not have a show method!');
          console.error('[Consent] Modal component:', this.modalComponent);
          // Allow action to proceed if modal is not properly set up
          if (callback) {
            await callback();
          }
          return true;
        }
        
        const accepted = await this.modalComponent.show(actionType, config);
        console.log('[Consent] Modal returned:', accepted);
        
        if (accepted && callback) {
          await callback();
        }
        
        return accepted;
      } catch (error) {
        // User cancelled the consent or error occurred
        console.error('[Consent] Error showing modal:', error);
        console.log('[Consent] User cancelled consent or error occurred');
        return false;
      }

    } catch (error) {
      console.error('[Consent] Error checking consent:', error);
      // On error, allow the action to proceed
      if (callback) {
        await callback();
      }
      return true;
    }
  }

  /**
   * Wrap an async function with consent checking
   * @param {string} actionType - The action type from CONSENT_ACTIONS
   * @param {Function} fn - The async function to wrap
   * @returns {Function} - Wrapped function
   */
  withConsent(actionType, fn) {
    return async (...args) => {
      const canProceed = await this.checkAndRequestConsent(actionType);
      
      if (canProceed) {
        return await fn(...args);
      } else {
        throw new Error('User declined consent');
      }
    };
  }
}

// Create singleton instance
const consentService = new ConsentService();

// Export both the instance and the class
export default consentService;
export { ConsentService, CONSENT_ACTIONS };

