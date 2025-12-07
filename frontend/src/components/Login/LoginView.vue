<template>
  <div class="login-page">
    <!-- Background Elements -->
    <div class="background-overlay"></div>
    <div class="background-shapes">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>
    
    <!-- Main Content -->
    <div class="login-content">
      <!-- Left Section - Branding -->
      <div class="branding-section">
        <div class="branding-content">
          <div class="logo-section">
            <div>
              <img :src="logo" alt="RiskaVaire Logo" class="logo-image" />
            </div>
          </div>
          
          <div class="hero-content">
            <h2 class="hero-title">Advanced Governance, Risk & Compliance</h2>
            <p class="hero-description">
              Empower your organization with cutting-edge governance, risk management, and compliance tools designed for the modern enterprise. Our comprehensive platform delivers unparalleled control, real-time visibility, and AI-powered automation—aligning IT with business objectives and helping you stay ahead of regulatory change.
            </p>
            
            <div class="features-list">
              <div class="feature-item">
                <div class="feature-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="2"/>
                    <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  <div class="feature-tick">
                    <svg width="8" height="8" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="3"/>
                    </svg>
                  </div>
                </div>
                <div class="feature-content">
                  <span>Enterprise-grade security with multi-layer protection</span>
                </div>
              </div>
              
              <div class="feature-item">
                <div class="feature-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
                    <polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="2"/>
                    <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2"/>
                    <path d="m9 16 2 2 4-4" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  <div class="feature-tick">
                    <svg width="8" height="8" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="3"/>
                    </svg>
                  </div>
                </div>
                <div class="feature-content">
                  <span>Automated compliance reporting and real-time monitoring</span>
                </div>
              </div>
              
              <div class="feature-item">
                <div class="feature-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <line x1="18" y1="20" x2="18" y2="10" stroke="currentColor" stroke-width="2"/>
                    <line x1="12" y1="20" x2="12" y2="4" stroke="currentColor" stroke-width="2"/>
                    <line x1="6" y1="20" x2="6" y2="14" stroke="currentColor" stroke-width="2"/>
                    <circle cx="18" cy="8" r="2" stroke="currentColor" stroke-width="2"/>
                    <circle cx="12" cy="2" r="2" stroke="currentColor" stroke-width="2"/>
                    <circle cx="6" cy="12" r="2" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  <div class="feature-tick">
                    <svg width="8" height="8" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="3"/>
                    </svg>
                  </div>
                </div>
                <div class="feature-content">
                  <span>Advanced risk analytics with predictive insights</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="trust-badges">
            <div class="badge">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                <circle cx="12" cy="16" r="1" stroke="currentColor" stroke-width="2"/>
                <path d="m8 16 2-2 4 2" stroke="currentColor" stroke-width="2"/>
              </svg>
              <span>AES-256 Encryption</span>
            </div>
            <div class="badge">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2"/>
                <circle cx="18" cy="6" r="2" fill="currentColor"/>
              </svg>
              <span>24/7 Monitoring</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Right Section - Login Form -->
      <div class="form-section">
        <div class="form-container">
          <div class="form-header">
            <h3>
              
              Welcome Back
            </h3>
            <p>Sign in to your GRC dashboard</p>
          </div>
          
          <form @submit.prevent="login" class="login-form">
            <!-- Login Type Selector -->
            <div class="login-type-selector">
              <!-- Username Option -->
              <div class="radio-wrapper" :class="{ checked: loginType === 'username' }" @click="loginType = 'username'">
                <input type="radio" v-model="loginType" value="username" name="loginType" style="display: none;">
                <span class="radio-mark">
                  <svg v-if="loginType === 'username'" width="8" height="8" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="4" fill="currentColor"/>
                  </svg>
                </span>
                <span class="radio-text">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                    <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  Username
                </span>
              </div>
              
              <!-- User ID Option -->
              <div class="radio-wrapper" :class="{ checked: loginType === 'userid' }" @click="loginType = 'userid'">
                <input type="radio" v-model="loginType" value="userid" name="loginType" style="display: none;">
                <span class="radio-mark">
                  <svg v-if="loginType === 'userid'" width="8" height="8" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="4" fill="currentColor"/>
                  </svg>
                </span>
                <span class="radio-text">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" stroke="currentColor" stroke-width="2"/>
                    <rect x="8" y="2" width="8" height="4" rx="1" ry="1" stroke="currentColor" stroke-width="2"/>
                    <path d="M9 14h6M9 18h6" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  User ID
                </span>
              </div>
            </div>
            
            <div class="input-group" :class="{ success: loginIdentifier && loginIdentifier.length > 0 }">
              <label for="loginIdentifier">
                {{ loginType === 'username' ? 'Username' : 'User ID' }}
              </label>
              <div class="input-wrapper" :class="{ success: loginIdentifier && loginIdentifier.length > 0 }">
                <div class="input-icon">
                  <svg v-if="loginType === 'username'" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2"/>
                    <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" stroke="currentColor" stroke-width="2"/>
                    <rect x="8" y="2" width="8" height="4" rx="1" ry="1" stroke="currentColor" stroke-width="2"/>
                    <path d="M9 14h6M9 18h6" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
                <input 
                  type="text" 
                  id="loginIdentifier" 
                  v-model="loginIdentifier" 
                  :placeholder="loginType === 'username' ? 'Enter your username' : 'Enter your user ID'"
                  required
                  :autocomplete="loginType === 'username' ? 'username' : 'off'"
                  :class="{ 'has-success': loginIdentifier && loginIdentifier.length > 0 }"
                >
                <div v-if="loginIdentifier && loginIdentifier.length > 0" class="input-success-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
              </div>
            </div>
            
            <div class="input-group" :class="{ success: password && password.length > 0 }">
              <label for="password">
                Password
              </label>
              <div class="input-wrapper" :class="{ success: password && password.length > 0 }">
                <div class="input-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                    <circle cx="12" cy="16" r="1" stroke="currentColor" stroke-width="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
                <input 
                  :type="passwordFieldType" 
                  id="password" 
                  v-model="password" 
                  placeholder="Enter your password"
                  required
                  autocomplete="current-password"
                  :class="{ 'has-success': password && password.length > 0 }"
                >
                <div v-if="password && password.length > 0" class="input-success-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </div>
                <button 
                  type="button"
                  @click="togglePasswordVisibility" 
                  class="password-toggle"
                  tabindex="-1"
                  :title="passwordFieldType === 'password' ? 'Show password' : 'Hide password'"
                >
                  <svg v-if="passwordFieldType === 'password'" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2"/>
                    <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" stroke="currentColor" stroke-width="2"/>
                    <line x1="1" y1="1" x2="23" y2="23" stroke="currentColor" stroke-width="2"/>
                  </svg>
                </button>
              </div>
            </div>
            
            <div class="form-options">
              <div class="form-options-row">
                <button type="button" @click="showForgotPasswordModal = true" class="forgot-password">
                  Forgot password ?
                </button>
              </div>
            </div>
            
            <button type="submit" class="login-button" :disabled="isLoading" :class="{ active: !isLoading }">
              <span v-if="!isLoading" class="button-text">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" stroke="currentColor" stroke-width="2"/>
                </svg>
                Sign In to Dashboard
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="m9 18 6-6-6-6" stroke="currentColor" stroke-width="2"/>
                </svg>
              </span>
              <span v-else class="loading-content">
                <div class="spinner">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" opacity="0.25"/>
                    <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </div>
                <span>Signing you in</span>
                <span class="loading-dots"></span>
              </span>
            </button>
            
            <div v-if="errorMessage" class="error-alert">
              <button class="error-close" @click="errorMessage = ''" type="button">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
                  <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
                </svg>
              </button>
              <span>{{ errorMessage }}</span>
            </div>
          </form>
            
          <!-- License Verification Notice -->
          <div class="license-notice">
            <div class="notice-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="2"/>
                <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <span>License verification will be performed during login</span>
          </div>

          <!-- Contact Section -->
          <div class="contact-section">
            <div class="contact-header">
              <h4>CONTACT US</h4>
            </div>
            <div class="contact-info">
              <div class="contact-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="2"/>
                  <polyline points="22,6 12,13 2,6" stroke="currentColor" stroke-width="2"/>
                </svg>
                <a href="mailto:info@vardaanglobal.com">info@vardaanglobal.com</a>
              </div>
              <div class="contact-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" stroke="currentColor" stroke-width="2"/>
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" stroke="currentColor" stroke-width="2"/>
                </svg>
                <a href="https://vardaanglobal.com/grc" target="_blank" rel="noopener noreferrer">vardaanglobal.com/grc</a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Forgot Password Modal -->
    <ForgotPassword 
      :showModal="showForgotPasswordModal" 
      :username="loginIdentifier"
      @close="showForgotPasswordModal = false" 
    />
    
    <!-- Consent Form Modal -->
    <ConsentForm 
      :showConsent="showConsentForm"
      @consent-accepted="handleConsentAccepted"
      @consent-declined="handleConsentDeclined"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import authService from '../../services/authService.js'
import ForgotPassword from './ForgotPassword.vue'
import ConsentForm from './ConsentForm.vue'
import logo from '../../assets/RiskaVaire.png'

const password = ref('')
const rememberMe = ref(false)
const errorMessage = ref('')
const isLoading = ref(false)
const router = useRouter()
const passwordFieldType = ref('password')
const loginType = ref('username') // 'username' or 'userid'
const loginIdentifier = ref('') // username or user_id
const showForgotPasswordModal = ref(false)
const showConsentForm = ref(false)

const login = async () => {
  try {
    isLoading.value = true
    errorMessage.value = ''
    
    if (!loginIdentifier.value || !password.value) {
      errorMessage.value = 'Please fill in all required fields'
      return
    }
    
    // Clear any existing data
    localStorage.clear()
    
    // Use JWT authentication
    const result = await authService.login(
      loginIdentifier.value, 
      password.value, 
      loginType.value
    )
    
    if (result.success) {
      if (rememberMe.value) {
        localStorage.setItem('remember_me', 'true')
      }
      
      console.log('🔐 JWT Login successful!', {
        user_id: result.user.UserId,
        email: result.user.Email,
        username: result.user.UserName,
        consent_required: result.user.consent_accepted !== '1'
      })
      
      // Check if consent is required (if user hasn't accepted consent yet)
      if (result.user.consent_accepted !== '1') {
        console.log('📋 Consent required - showing consent form')
        showConsentForm.value = true
      } else {
        console.log('✅ Consent already accepted - proceeding to home')
        // Call the global login success handler
        if (window.onSuccessfulLogin) {
          window.onSuccessfulLogin()
        }
        window.dispatchEvent(new Event('authChanged'))
        router.push('/home')
      }
    } else {
      errorMessage.value = 'Login failed. Please try again.'
    }
  } catch (error) {
    if (error.response && error.response.data) {
      errorMessage.value = error.response.data.message || 'Invalid credentials. Please try again.'
    } else {
      errorMessage.value = 'Unable to connect to server. Please check your connection.'
    }
    console.error('❌ JWT Login error:', error)
  } finally {
    isLoading.value = false
  }
}

const handleConsentAccepted = () => {
  console.log('✅ Consent accepted - proceeding to home')
  showConsentForm.value = false
  // Call the global login success handler
  if (window.onSuccessfulLogin) {
    window.onSuccessfulLogin()
  }
  window.dispatchEvent(new Event('authChanged'))
  router.push('/home')
}

const handleConsentDeclined = () => {
  console.log('❌ Consent declined - logging out')
  showConsentForm.value = false
  // Clear authentication data and stay on login page
  authService.clearAuthData()
  errorMessage.value = 'You must accept the terms and conditions to use the system.'
}

const togglePasswordVisibility = () => {
  passwordFieldType.value = passwordFieldType.value === 'password' ? 'text' : 'password'
}
</script>

<style scoped>
@import './login.css?v=2.0';
</style>