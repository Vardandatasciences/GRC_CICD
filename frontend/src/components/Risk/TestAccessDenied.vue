<template>
  <div class="test-access-denied">
    <h3>🧪 Test Access Denied Popup</h3>
    <p>Use these buttons to test the access denied popup functionality:</p>
    
    <div class="test-buttons">
      <button @click="testDirectPopup" class="test-btn primary">
        Test Direct Popup
      </button>
      
      <button @click="testRiskCreate" class="test-btn secondary">
        Test Risk Create API Call
      </button>
      
      <button @click="testRiskView" class="test-btn info">
        Test Risk View API Call
      </button>
      
      <button @click="testAccessUtils" class="test-btn warning">
        Test AccessUtils Direct Call
      </button>
    </div>
    
    <div class="test-logs">
      <h4>Console Logs:</h4>
      <p>Check your browser console for detailed logs starting with:</p>
      <ul>
        <li><code>[ACCESS_UTILS]</code> - Access utility logs</li>
        <li><code>[POPUP_SERVICE]</code> - Popup service logs</li>
        <li><code>[HTTP_INTERCEPTOR]</code> - HTTP interceptor logs</li>
      </ul>
    </div>
    
    <!-- Include the PopupModal component -->
    <PopupModal />
  </div>
</template>

<script>
import axios from 'axios'
import AccessUtils from '@/utils/accessUtils'
import PopupModal from '@/modules/popup/PopupModal.vue'
import { PopupService } from '@/modules/popup/popupService'
import { API_ENDPOINTS } from '../../config/api.js'

export default {
  name: 'TestAccessDenied',
  components: {
    PopupModal
  },
  methods: {
    testDirectPopup() {
      console.log('[TEST] Testing direct popup call');
      try {
        PopupService.accessDenied(
          'This is a test access denied message. You are not authorized to perform this action.',
          'Test Access Denied'
        );
      } catch (error) {
        console.error('[TEST] Error calling direct popup:', error);
      }
    },
    
    async testRiskCreate() {
      console.log('[TEST] Testing risk create API call (should trigger 401)');
      try {
        const response = await axios.post(API_ENDPOINTS.RISKS, {
          RiskTitle: 'Test Risk',
          RiskDescription: 'Test Description'
        });
        console.log('[TEST] Unexpected success:', response);
      } catch (error) {
        console.log('[TEST] Expected error caught:', error.response?.status);
      }
    },
    
    async testRiskView() {
      console.log('[TEST] Testing risk view API call (should trigger 401)');
      try {
        const response = await axios.get(API_ENDPOINTS.RISKS);
        console.log('[TEST] Unexpected success:', response);
      } catch (error) {
        console.log('[TEST] Expected error caught:', error.response?.status);
      }
    },
    
    testAccessUtils() {
      console.log('[TEST] Testing AccessUtils direct call');
      try {
        AccessUtils.showRiskAccessDenied('create');
      } catch (error) {
        console.error('[TEST] Error calling AccessUtils:', error);
      }
    }
  }
}
</script>

<style scoped>
.test-access-denied {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
  font-family: Arial, sans-serif;
}

.test-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin: 20px 0;
}

.test-btn {
  padding: 12px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.test-btn.primary {
  background-color: #007bff;
  color: white;
}

.test-btn.secondary {
  background-color: #6c757d;
  color: white;
}

.test-btn.info {
  background-color: #17a2b8;
  color: white;
}

.test-btn.warning {
  background-color: #ffc107;
  color: #212529;
}

.test-btn:hover {
  opacity: 0.8;
  transform: translateY(-1px);
}

.test-logs {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  margin-top: 20px;
}

.test-logs h4 {
  margin-top: 0;
  color: #495057;
}

.test-logs code {
  background-color: #e9ecef;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

.test-logs ul {
  margin-bottom: 0;
}
</style> 