/**
 * Consent Debug Utility
 * Use this in browser console to debug consent issues
 */

import { checkConsentRequired, CONSENT_ACTIONS } from './consentManager.js';

/**
 * Debug consent check for a specific action
 * Usage in browser console:
 *   import('./utils/consentDebug.js').then(m => m.debugConsent('create_incident'))
 */
export async function debugConsent(actionType = 'create_incident') {
  console.log('🔍 ========== CONSENT DEBUG ==========');
  console.log('Action Type:', actionType);
  
  // Check localStorage
  console.log('\n📦 LocalStorage:');
  console.log('  framework_id:', localStorage.getItem('framework_id'));
  console.log('  user_id:', localStorage.getItem('user_id'));
  console.log('  access_token:', localStorage.getItem('access_token') ? 'EXISTS' : 'MISSING');
  
  // Check sessionStorage
  console.log('\n📦 SessionStorage:');
  console.log('  framework_id:', sessionStorage.getItem('framework_id'));
  console.log('  selectedFrameworkId:', sessionStorage.getItem('selectedFrameworkId'));
  
  // Check consent
  console.log('\n🔍 Checking consent...');
  try {
    const result = await checkConsentRequired(actionType);
    console.log('\n✅ Consent Check Result:');
    console.log('  required:', result.required);
    console.log('  config:', result.config);
    
    if (result.required && result.config) {
      console.log('\n✅ Consent IS REQUIRED');
      console.log('  Config ID:', result.config.config_id);
      console.log('  Action Label:', result.config.action_label);
      console.log('  Consent Text:', result.config.consent_text);
      console.log('  Is Enabled:', result.config.is_enabled);
    } else {
      console.log('\n❌ Consent NOT REQUIRED');
      if (!result.required) {
        console.log('  Reason: is_enabled is false or config not found');
      }
      if (!result.config) {
        console.log('  Reason: config is null');
      }
    }
  } catch (error) {
    console.error('\n❌ Error checking consent:', error);
  }
  
  console.log('\n🔍 ========== END DEBUG ==========');
}

// Make it available globally for easy console access
if (typeof window !== 'undefined') {
  window.debugConsent = debugConsent;
}

