// Test file to verify API configuration
import { API_BASE_URL, API_ENDPOINTS, ENVIRONMENT } from './api.js'

console.log('🧪 Testing API Configuration...')
console.log('Environment:', ENVIRONMENT)
console.log('Base URL:', API_BASE_URL)
console.log('Login endpoint:', API_ENDPOINTS.LOGIN)
console.log('User profile endpoint (with ID 1):', API_ENDPOINTS.USER_PROFILE(1))

// Test that all endpoints are properly formatted
const testEndpoints = [
  'LOGIN',
  'LOGOUT', 
  'SEND_OTP',
  'VERIFY_OTP',
  'RESET_PASSWORD',
  'USER_ROLE',
  'POLICIES',
  'FRAMEWORK_EXPLORER'
]

console.log('✅ Testing endpoint formatting...')
testEndpoints.forEach(endpoint => {
  const url = API_ENDPOINTS[endpoint]
  if (url && url.includes(API_BASE_URL)) {
    console.log(`✅ ${endpoint}: ${url}`)
  } else {
    console.error(`❌ ${endpoint}: Invalid URL format`)
  }
})

console.log('✅ API Configuration test completed!')
