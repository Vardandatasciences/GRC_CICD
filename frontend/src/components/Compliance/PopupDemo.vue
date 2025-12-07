<template>
  <div class="popup-demo-container">
    <h1>Popup System Demo</h1>
    <p class="demo-description">
      This page demonstrates all the popup types available in the Compliance module.
      Click on the buttons below to see each popup type in action.
    </p>

    <div class="popup-categories">
      <!-- Basic Popup Types -->
      <div class="popup-category">
        <h2>Basic Popup Types</h2>
        <div class="demo-buttons">
          <button @click="showSuccessPopup('Operation completed successfully!')" class="success-btn">
            Success Popup
          </button>
          <button @click="showErrorPopup('An error occurred while processing your request.')" class="error-btn">
            Error Popup
          </button>
          <button @click="showWarningPopup('This action may have consequences.')" class="warning-btn">
            Warning Popup
          </button>
          <button @click="showInfoPopup('This is some helpful information.')" class="info-btn">
            Info Popup
          </button>
          <button @click="showAutoClosePopup('This popup will close automatically in 3 seconds.', 'Auto-Close Demo', 'info', 3000)" class="auto-close-btn">
            Auto-Close Popup
          </button>
        </div>
      </div>

      <!-- Interactive Popups -->
      <div class="popup-category">
        <h2>Interactive Popups</h2>
        <div class="demo-buttons">
          <button @click="showConfirmationDemo()" class="confirm-btn">
            Confirmation Popup
          </button>
          <button @click="showCommentDemo()" class="comment-btn">
            Comment Popup
          </button>
        </div>
      </div>

      <!-- Compliance-Specific Popups -->
      <div class="popup-category">
        <h2>Compliance-Specific Popups</h2>
        <div class="demo-buttons">
          <button @click="showComplianceCreated()" class="compliance-btn">
            Compliance Created
          </button>
          <button @click="showComplianceUpdated()" class="compliance-btn">
            Compliance Updated
          </button>
          <button @click="showComplianceCloned()" class="compliance-btn">
            Compliance Cloned
          </button>
          <button @click="showComplianceStatusChanged()" class="compliance-btn">
            Status Changed
          </button>
          <button @click="showReviewSubmitted()" class="compliance-btn">
            Review Submitted
          </button>
          <button @click="showOperationFailed()" class="compliance-btn">
            Operation Failed
          </button>
          <button @click="showValidationFailed()" class="compliance-btn">
            Validation Failed
          </button>
        </div>
      </div>

      <!-- Compliance Confirmation Popups -->
      <div class="popup-category">
        <h2>Compliance Confirmation Popups</h2>
        <div class="demo-buttons">
          <button @click="showDeactivationConfirm()" class="compliance-btn">
            Confirm Deactivation
          </button>
          <button @click="showEditConfirm()" class="compliance-btn">
            Confirm Edit
          </button>
          <button @click="showCloneConfirm()" class="compliance-btn">
            Confirm Clone
          </button>
          <button @click="showDeleteConfirm()" class="compliance-btn">
            Confirm Delete
          </button>
          <button @click="showActivateVersionConfirm()" class="compliance-btn">
            Confirm Activate Version
          </button>
        </div>
      </div>

      <!-- Compliance Info Popups -->
      <div class="popup-category">
        <h2>Compliance Info Popups</h2>
        <div class="demo-buttons">
          <button @click="showComplianceInfo()" class="compliance-btn">
            Compliance Info
          </button>
          <button @click="showAuditInfo()" class="compliance-btn">
            Audit Info
          </button>
          <button @click="showExportCompleted()" class="compliance-btn">
            Export Completed
          </button>
          <button @click="showSessionTimeout()" class="compliance-btn">
            Session Timeout
          </button>
        </div>
      </div>
    </div>

    <!-- Include the PopupModal component -->
    <PopupModal />
  </div>
</template>

<script>
import { PopupModal } from '../../modules/popup';
import PopupMixin from './mixins/PopupMixin';
import { CompliancePopups } from './utils/popupUtils';

export default {
  name: 'PopupDemo',
  components: {
    PopupModal
  },
  mixins: [PopupMixin],
  data() {
    return {
      demoCompliance: {
        ComplianceId: 12345,
        ComplianceItemDescription: 'Sample Compliance Item',
        ComplianceVersion: '2.0',
        Status: 'Approved',
        Criticality: 'High',
        CreatedByName: 'John Doe',
        CreatedByDate: '2023-06-15'
      },
      demoAuditInfo: {
        audit_performer_name: 'Jane Smith',
        audit_approver_name: 'Robert Johnson',
        audit_date: '2023-06-20',
        audit_time: '14:30:00',
        audit_findings_status: 'Fully Compliant',
        comments: 'All criteria successfully met.'
      }
    };
  },
  methods: {
    // Basic Popup Demos
    showConfirmationDemo() {
      this.showConfirmPopup(
        'Are you sure you want to proceed with this action?',
        'Confirmation Required',
        () => {
          this.showSuccessPopup('Action confirmed!', 'Success');
        },
        () => {
          this.showInfoPopup('Action cancelled.', 'Cancelled');
        }
      );
    },
    
    showCommentDemo() {
      this.showCommentPopup(
        'Please provide your feedback:',
        'Feedback Requested',
        (comment) => {
          this.showSuccessPopup(`Thank you for your feedback: "${comment}"`, 'Feedback Received');
        }
      );
    },

    // Compliance-Specific Popups
    showComplianceCreated() {
      CompliancePopups.complianceCreated(this.demoCompliance);
    },
    
    showComplianceUpdated() {
      CompliancePopups.complianceUpdated(this.demoCompliance);
    },
    
    showComplianceCloned() {
      CompliancePopups.complianceCloned(this.demoCompliance);
    },
    
    showComplianceStatusChanged() {
      CompliancePopups.complianceStatusChanged('Active', this.demoCompliance.ComplianceVersion);
    },
    
    showReviewSubmitted() {
      const approvalState = Math.random() > 0.5;
      CompliancePopups.reviewSubmitted(approvalState);
    },
    
    showOperationFailed() {
      CompliancePopups.operationFailed('save compliance', 'Server returned a 500 error');
    },
    
    showValidationFailed() {
      CompliancePopups.validationFailed({
        'ComplianceItemDescription': 'Description is required',
        'Criticality': 'Criticality must be High, Medium, or Low'
      });
    },

    // Compliance Confirmation Popups
    showDeactivationConfirm() {
      this.confirmDeactivateCompliance(this.demoCompliance, () => {
        this.showSuccessPopup('Compliance deactivated successfully!', 'Deactivation Complete');
      });
    },
    
    showEditConfirm() {
      this.confirmEditCompliance(this.demoCompliance, () => {
        this.showSuccessPopup('New compliance version created successfully!', 'Edit Complete');
      });
    },
    
    showCloneConfirm() {
      this.confirmCloneCompliance(this.demoCompliance, () => {
        this.showSuccessPopup('Compliance cloned successfully!', 'Clone Complete');
      });
    },
    
    showDeleteConfirm() {
      this.confirmDeleteCompliance(this.demoCompliance, () => {
        this.showSuccessPopup('Compliance deleted successfully!', 'Deletion Complete');
      });
    },
    
    showActivateVersionConfirm() {
      this.confirmActivateVersion(this.demoCompliance, () => {
        this.showSuccessPopup(`Version ${this.demoCompliance.ComplianceVersion} activated successfully!`, 'Activation Complete');
      });
    },

    // Compliance Info Popups
    showComplianceInfo() {
      CompliancePopups.showComplianceInfo(this.demoCompliance);
    },
    
    showAuditInfo() {
      CompliancePopups.showAuditInfo(this.demoAuditInfo);
    },
    
    showExportCompleted() {
      const formats = ['xlsx', 'csv', 'pdf', 'json', 'xml'];
      const randomFormat = formats[Math.floor(Math.random() * formats.length)];
      CompliancePopups.exportCompleted(randomFormat);
    },
    
    showSessionTimeout() {
      CompliancePopups.sessionTimeout(
        () => {
          this.showSuccessPopup('Session extended successfully!', 'Session Extended');
        },
        () => {
          this.showInfoPopup('You have been logged out.', 'Session Ended');
        }
      );
    }
  }
};
</script>

<style scoped>
.popup-demo-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  font-size: 2rem;
  color: #1a202c;
  margin-bottom: 0.5rem;
  text-align: center;
}

.demo-description {
  text-align: center;
  color: #4a5568;
  margin-bottom: 2rem;
}

.popup-categories {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.popup-category {
  background-color: #f8fafc;
  border-radius: 10px;
  padding: 1.5rem;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

h2 {
  font-size: 1.5rem;
  color: #2d3748;
  margin-bottom: 1rem;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 0.5rem;
}

.demo-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

button {
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  white-space: nowrap;
}

button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.success-btn {
  background-color: #10b981;
  color: white;
}

.error-btn {
  background-color: #ef4444;
  color: white;
}

.warning-btn {
  background-color: #f59e0b;
  color: white;
}

.info-btn {
  background-color: #3b82f6;
  color: white;
}

.confirm-btn {
  background-color: #8b5cf6;
  color: white;
}

.comment-btn {
  background-color: #8b5cf6;
  color: white;
}

.auto-close-btn {
  background-color: #6b7280;
  color: white;
}

.compliance-btn {
  background-color: #0ea5e9;
  color: white;
}

@media (max-width: 768px) {
  .popup-demo-container {
    padding: 10px;
  }
  
  .demo-buttons {
    flex-direction: column;
  }
  
  button {
    width: 100%;
  }
}
</style>