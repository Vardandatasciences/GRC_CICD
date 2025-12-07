// PopupMixin.js
// A mixin to standardize popup usage in Compliance components

import { PopupService } from '../../../modules/popup';

export default {
  methods: {
    /**
     * Show a success popup
     * @param {string} message - The message to display
     * @param {string} heading - The popup heading (optional)
     */
    showSuccessPopup(message, heading = 'Success') {
      PopupService.success(message, heading);
    },

    /**
     * Show an error popup
     * @param {string} message - The error message to display
     * @param {string} heading - The popup heading (optional)
     */
    showErrorPopup(message, heading = 'Error') {
      PopupService.error(message, heading);
    },

    /**
     * Show a warning popup
     * @param {string} message - The warning message to display
     * @param {string} heading - The popup heading (optional)
     */
    showWarningPopup(message, heading = 'Warning') {
      PopupService.warning(message, heading);
    },

    /**
     * Show an info popup
     * @param {string} message - The information message to display
     * @param {string} heading - The popup heading (optional)
     */
    showInfoPopup(message, heading = 'Information') {
      PopupService.show({
        type: 'info',
        heading: heading,
        message: message,
        buttons: [{ label: 'OK', action: 'ok' }]
      });
    },

    /**
     * Show a confirmation popup
     * @param {string} message - The confirmation message
     * @param {string} heading - The popup heading (optional)
     * @param {Function} onConfirm - Callback when user confirms
     * @param {Function} onCancel - Callback when user cancels (optional)
     */
    showConfirmPopup(message, heading = 'Confirm', onConfirm, onCancel) {
      PopupService.confirm(message, heading, onConfirm, onCancel);
    },

    /**
     * Show a comment popup for gathering user input
     * @param {string} message - The prompt message
     * @param {string} heading - The popup heading (optional)
     * @param {Function} onSubmit - Callback when user submits comment
     */
    showCommentPopup(message, heading = 'Comment', onSubmit) {
      PopupService.comment(message, heading, onSubmit);
    },

    /**
     * Show a custom popup with auto-close feature
     * @param {string} message - The message to display
     * @param {string} heading - The popup heading
     * @param {string} type - Popup type (success, error, warning, info)
     * @param {number} autoCloseTime - Time in ms before auto-closing
     */
    showAutoClosePopup(message, heading, type = 'info', autoCloseTime = 3000) {
      PopupService.show({
        type: type,
        heading: heading,
        message: message,
        buttons: [{ label: 'OK', action: 'ok' }],
        autoClose: autoCloseTime
      });
    },

    /**
     * Compliance-specific confirmation for deactivation
     * @param {Object} compliance - The compliance to deactivate
     * @param {Function} onConfirm - Callback when user confirms
     */
    confirmDeactivateCompliance(compliance, onConfirm) {
      const message = `Are you sure you want to deactivate "${compliance.ComplianceItemDescription || 'this compliance'}"?`;
      this.showConfirmPopup(message, 'Deactivate Compliance', onConfirm);
    },

    /**
     * Compliance-specific confirmation for editing
     * @param {Object} compliance - The compliance to edit
     * @param {Function} onConfirm - Callback when user confirms
     */
    confirmEditCompliance(compliance, onConfirm) {
      const message = `Are you sure you want to edit "${compliance.ComplianceItemDescription || 'this compliance'}"? This will create a new version.`;
      this.showConfirmPopup(message, 'Edit Compliance', onConfirm);
    },

    /**
     * Compliance-specific confirmation for cloning
     * @param {Object} compliance - The compliance to clone
     * @param {Function} onConfirm - Callback when user confirms
     */
    confirmCloneCompliance(compliance, onConfirm) {
      const message = `Are you sure you want to clone "${compliance.ComplianceItemDescription || 'this compliance'}"?`;
      this.showConfirmPopup(message, 'Clone Compliance', onConfirm);
    },

    /**
     * Compliance-specific confirmation for deleting
     * @param {Object} compliance - The compliance to delete
     * @param {Function} onConfirm - Callback when user confirms
     */
    confirmDeleteCompliance(compliance, onConfirm) {
      const message = `Are you sure you want to delete "${compliance.ComplianceItemDescription || 'this compliance'}"? This action cannot be undone.`;
      this.showConfirmPopup(message, 'Delete Compliance', onConfirm);
    },

    /**
     * Compliance-specific confirmation for version activation
     * @param {Object} compliance - The compliance to activate
     * @param {Function} onConfirm - Callback when user confirms
     */
    confirmActivateVersion(compliance, onConfirm) {
      const message = `Are you sure you want to activate version ${compliance.ComplianceVersion || 'this version'} of this compliance?`;
      this.showConfirmPopup(message, 'Activate Version', onConfirm);
    },

    /**
     * Get comments for rejecting a compliance
     * @param {Object} compliance - The compliance being rejected
     * @param {Function} onSubmit - Callback when user submits comments
     */
    getRejectComments(compliance, onSubmit) {
      const message = `Please provide a reason for rejecting "${compliance.ComplianceItemDescription || 'this compliance'}":`;
      this.showCommentPopup(message, 'Reject Compliance', onSubmit);
    },

    /**
     * Get comments for deactivation
     * @param {Object} compliance - The compliance being deactivated
     * @param {Function} onSubmit - Callback when user submits comments
     */
    getDeactivationReason(compliance, onSubmit) {
      const message = `Please provide a reason for deactivating "${compliance.ComplianceItemDescription || 'this compliance'}":`;
      this.showCommentPopup(message, 'Deactivation Reason', onSubmit);
    },

    /**
     * Show status information for a compliance
     * @param {Object} compliance - The compliance to show info for
     */
    showComplianceInfo(compliance) {
      const description = compliance.ComplianceItemDescription || 'No description available';
      const status = compliance.Status || 'Unknown';
      const version = compliance.ComplianceVersion || 'Unknown';
      const message = `Status: ${status}\nVersion: ${version}\nDescription: ${description}`;
      
      this.showInfoPopup(message, 'Compliance Information');
    },

    /**
     * Show audit information for a compliance
     * @param {Object} auditInfo - The audit information
     */
    showAuditInfo(auditInfo) {
      if (!auditInfo) {
        this.showInfoPopup('No audit information available for this compliance.', 'Audit Information');
        return;
      }

      const performer = auditInfo.audit_performer_name || 'Unknown';
      const approver = auditInfo.audit_approver_name || 'Unknown';
      const date = auditInfo.audit_date || 'Unknown';
      const status = auditInfo.audit_findings_status || 'Unknown';
      
      const message = `Performed by: ${performer}\nApproved by: ${approver}\nDate: ${date}\nStatus: ${status}`;
      
      this.showInfoPopup(message, 'Audit Information');
    }
  }
}; 