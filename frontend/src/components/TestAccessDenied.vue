<template>
  <div class="test-access-denied">
    <h2>Test Access Denied Functionality</h2>
    
    <div class="test-buttons">
      <button @click="testDirectRedirect" class="test-btn">
        Test Direct Redirect to Access Denied
      </button>
      
      <button @click="testApiError" class="test-btn">
        Test API Error (401/403)
      </button>
      
      <button @click="testAccessUtils" class="test-btn">
        Test AccessUtils.showAccessDenied()
      </button>
    </div>
    
    <div class="test-info">
      <h3>Test Instructions:</h3>
      <ul>
        <li><strong>Direct Redirect:</strong> Should immediately redirect to AccessDenied page</li>
        <li><strong>API Error:</strong> Should trigger HTTP interceptor and redirect to AccessDenied page</li>
        <li><strong>AccessUtils:</strong> Should use AccessUtils to redirect to AccessDenied page</li>
      </ul>
    </div>
  </div>
</template>

<script>
import { AccessUtils } from '@/utils/accessUtils'
import axios from 'axios'

export default {
  name: 'TestAccessDenied',
  methods: {
    testDirectRedirect() {
      console.log('Testing direct redirect to AccessDenied page')
      this.$router.push('/access-denied')
    },
    
    async testApiError() {
      console.log('Testing API error (401/403)')
      try {
        // Make a request to a protected endpoint that should return 401/403
        await axios.get('http://15.207.108.158:8000/api/protected-endpoint/')
      } catch (error) {
        console.log('API error caught:', error.response?.status)
        // The HTTP interceptor should handle this and redirect to AccessDenied
      }
    },
    
    testAccessUtils() {
      console.log('Testing AccessUtils.showAccessDenied()')
      AccessUtils.showAccessDenied('Test Feature', 'This is a test message for the AccessDenied page.')
    }
  }
}
</script>

<style scoped>
.test-access-denied {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.test-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 20px 0;
}

.test-btn {
  padding: 12px 20px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.test-btn:hover {
  background: #2563eb;
}

.test-info {
  background: #f9fafb;
  border-radius: 8px;
  padding: 20px;
  margin-top: 20px;
}

.test-info h3 {
  margin-top: 0;
  color: #1f2937;
}

.test-info ul {
  margin: 10px 0;
  padding-left: 20px;
}

.test-info li {
  margin: 5px 0;
  color: #4b5563;
}
</style>
