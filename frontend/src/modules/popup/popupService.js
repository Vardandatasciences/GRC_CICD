/**
 * Popup Service Module
 * A centralized service for managing popups throughout the application
 */

import { ref } from 'vue';

// Popup state management
const popupState = ref({
  visible: false,
  type: 'info',
  heading: '',
  message: '',
  buttons: [],
  autoClose: 0,
  inputPlaceholder: 'Enter your comment...'
});

// Callback management
const popupCallbacks = ref(new Map());

/**
 * Popup Service
 * Provides methods for showing different types of popups and handling user interactions
 */
export const PopupService = {
  /**
   * Show a popup with custom configuration
   * @param {Object} config - Popup configuration
   * @param {string} config.type - Type of popup (info, success, error, warning, confirm, comment)
   * @param {string} config.heading - Popup heading
   * @param {string} config.message - Popup message
   * @param {Array} config.buttons - Array of button configurations
   * @param {number} config.autoClose - Auto close timeout in milliseconds
   */
  show(config) {
    console.log('[POPUP_SERVICE] show() called with config:', config);
    console.log('[POPUP_SERVICE] Current popup state before update:', popupState.value);
    
    popupState.value = { ...popupState.value, ...config, visible: true };
    
    console.log('[POPUP_SERVICE] Popup state updated:', popupState.value);
    console.log('[POPUP_SERVICE] Popup should now be visible:', popupState.value.visible);
  },

  /**
   * Hide the current popup
   */
  hide() {
    popupState.value.visible = false;
  },

  /**
   * Get current popup state
   * @returns {Object} Current popup state
   */
  getState() {
    return popupState;
  },

  /**
   * Handle popup actions
   * @param {Object} params - Action parameters
   * @param {string} params.action - Action type
   * @param {string} params.comment - Comment text (for comment type popups)
   */
  handleAction({ action, comment }) {
    const callback = popupCallbacks.value.get(action);
    if (callback) {
      callback(comment);
      popupCallbacks.value.delete(action);
    }
    this.hide();
  },

  /**
   * Register callback for specific action
   * @param {string} action - Action type
   * @param {Function} callback - Callback function
   */
  onAction(action, callback) {
    popupCallbacks.value.set(action, callback);
  },

  /**
   * Show info popup
   * @param {string} message - Info message
   * @param {string} heading - Popup heading (default: 'Information')
   */
  info(message, heading = 'Information') {
    this.show({
      type: 'info',
      heading,
      message,
      buttons: [{ label: 'OK', action: 'ok', class: 'info' }]
    });
  },

  /**
   * Show success popup
   * @param {string} message - Success message
   * @param {string} heading - Popup heading (default: 'Success')
   */
  success(message, heading = 'Success') {
    this.show({
      type: 'success',
      heading,
      message,
      buttons: [{ label: 'OK', action: 'ok', class: 'success' }]
    });
  },

  /**
   * Show error popup
   * @param {string} message - Error message
   * @param {string} heading - Popup heading (default: 'Error')
   */
  error(message, heading = 'Error') {
    this.show({
      type: 'error',
      heading,
      message,
      buttons: [{ label: 'OK', action: 'ok', class: 'error' }]
    });
  },

  /**
   * Show warning popup
   * @param {string} message - Warning message
   * @param {string} heading - Popup heading (default: 'Warning')
   */
  warning(message, heading = 'Warning') {
    this.show({
      type: 'warning',
      heading,
      message,
      buttons: [{ label: 'OK', action: 'ok', class: 'warning' }]
    });
  },

  /**
   * Show confirmation popup
   * @param {string} message - Confirmation message
   * @param {string} heading - Popup heading (default: 'Confirm')
   * @param {Function} onConfirm - Callback for confirmation
   * @param {Function} onCancel - Callback for cancellation
   */
  confirm(message, heading = 'Confirm', onConfirm, onCancel) {
    this.show({
      type: 'confirm',
      heading,
      message,
      buttons: [
        { label: 'Yes', action: 'yes', class: 'success' },
        { label: 'No', action: 'no', class: 'error' }
      ]
    });

    if (onConfirm) this.onAction('yes', onConfirm);
    if (onCancel) this.onAction('no', onCancel);
  },

  /**
   * Show comment popup
   * @param {string} message - Comment prompt message
   * @param {string} heading - Popup heading (default: 'Comment')
   * @param {Function} onSubmit - Callback for submission
   */
  comment(message, heading = 'Comment', onSubmit) {
    this.show({
      type: 'comment',
      heading,
      message,
      buttons: [
        { label: 'Submit', action: 'submit', class: 'success' },
        { label: 'Cancel', action: 'cancel', class: 'error' }
      ]
    });

    if (onSubmit) this.onAction('submit', onSubmit);
  },

  /**
   * Show access denied popup
   * @param {string} message - Access denied message (default: 'You don't have permission to access this feature')
   * @param {string} heading - Popup heading (default: 'Access Denied')
   * @param {Function} onContactAdmin - Callback for contact admin action
   */
  accessDenied(message = 'You don\'t have permission to access this feature. Please contact your administrator to activate this feature.', heading = 'Access Denied', onContactAdmin) {
    console.log('[POPUP_SERVICE] accessDenied called with:', { message, heading, hasCallback: !!onContactAdmin });
    
    const config = {
      type: 'access-denied',
      heading,
      message,
      buttons: [
        { label: 'Contact Admin', action: 'contact-admin', class: 'warning' },
        { label: 'OK', action: 'ok', class: 'error' }
      ]
    };
    
    console.log('[POPUP_SERVICE] Popup config created:', config);
    
    try {
      this.show(config);
      console.log('[POPUP_SERVICE] show() method called successfully');
      console.log('[POPUP_SERVICE] Current popup state after show():', popupState.value);
      
      if (onContactAdmin) {
        this.onAction('contact-admin', onContactAdmin);
        console.log('[POPUP_SERVICE] Contact admin callback registered');
      }
    } catch (error) {
      console.error('[POPUP_SERVICE] Error in accessDenied method:', error);
    }
  }
};

export default PopupService; 