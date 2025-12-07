<template>
  <div class="access-denied-example">
    <h3>Access Denied Example</h3>
    <p>This component demonstrates how to use the access denied popup in risk components.</p>
    
    <div class="example-buttons">
      <button @click="showRiskViewAccess" class="btn btn-primary">
        Test Risk View Access
      </button>
      
      <button @click="showRiskCreateAccess" class="btn btn-secondary">
        Test Risk Create Access
      </button>
      
      <button @click="showRiskEditAccess" class="btn btn-warning">
        Test Risk Edit Access
      </button>
      
      <button @click="showCustomAccess" class="btn btn-danger">
        Test Custom Access Message
      </button>
    </div>
    
    <!-- Include the PopupModal component -->
    <PopupModal />
  </div>
</template>

<script>
import AccessUtils from '@/utils/accessUtils'
import PopupModal from '@/modules/popup/PopupModal.vue'

export default {
  name: 'AccessDeniedExample',
  components: {
    PopupModal
  },
  methods: {
    showRiskViewAccess() {
      AccessUtils.showRiskAccessDenied('view')
    },
    
    showRiskCreateAccess() {
      AccessUtils.showRiskAccessDenied('create')
    },
    
    showRiskEditAccess() {
      AccessUtils.showRiskAccessDenied('edit')
    },
    
    showCustomAccess() {
      AccessUtils.showAccessDenied(
        'Risk Analytics Dashboard',
        'You need administrator privileges to access the Risk Analytics Dashboard. Please contact your system administrator to request elevated permissions.',
        this.contactAdmin
      )
    },
    
    contactAdmin() {
      // Custom callback when user clicks "Contact Admin"
      console.log('Contact admin clicked')
      // You can implement your own logic here, such as:
      // - Opening email client
      // - Redirecting to support page
      // - Showing additional contact information
      alert('Please contact admin@company.com for access requests')
    }
  }
}
</script>

<style scoped>
.access-denied-example {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.example-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 20px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-warning {
  background-color: #ffc107;
  color: #212529;
}

.btn-danger {
  background-color: #dc3545;
  color: white;
}

.btn:hover {
  opacity: 0.8;
}
</style> 