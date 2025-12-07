<template>
  <div class="forgot-password-modal" v-if="showModal">
    <div class="modal-overlay" @click="closeModal"></div>
    <div class="modal-content">
      <div class="modal-header">
        <h3>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="2"/>
            <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
          </svg>
          Forgot Password
        </h3>
        <button class="close-button" @click="closeModal">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
            <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
          </svg>
        </button>
      </div>
      
      <div class="modal-body">
        <!-- Step 1: Enter Email -->
        <div v-if="currentStep === 1" class="step-content">
          <p class="step-description">
            Enter your email address to receive a One-Time Password (OTP) for password reset.
          </p>
          
          <div class="input-group">
            <label for="email">Email Address</label>
            <div class="input-wrapper">
              <div class="input-icon">
                <svg v-if="!isLoading" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" stroke="currentColor" stroke-width="2"/>
                  <polyline points="22,6 12,13 2,6" stroke="currentColor" stroke-width="2"/>
                </svg>
                <div v-else class="spinner-small"></div>
              </div>
              <input 
                type="email" 
                id="email" 
                v-model="email" 
                :placeholder="isLoading ? 'Fetching email...' : 'Enter your email address'"
                required
                :disabled="isLoading"
              >
            </div>
          </div>
          
          <button 
            @click="sendOTP" 
            class="action-button" 
            :disabled="isLoading || !email"
          >
            <span v-if="!isLoading" class="button-text">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 2H2v16h20V2zM2 22l4-4h16" stroke="currentColor" stroke-width="2"/>
              </svg>
              Send OTP
            </span>
            <span v-else class="loading-content">
              <div class="spinner"></div>
              <span>Sending OTP...</span>
            </span>
          </button>
        </div>
        
        <!-- Step 2: Enter OTP -->
        <div v-if="currentStep === 2" class="step-content">
          <p class="step-description">
            We've sent a 6-digit OTP to <strong>{{ email }}</strong>. Please enter it below.
          </p>
          
          <div class="input-group">
            <label for="otp">Enter OTP</label>
            <div class="input-wrapper">
              <div class="input-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                  <circle cx="12" cy="16" r="1" stroke="currentColor" stroke-width="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <input 
                type="text" 
                id="otp" 
                v-model="otp" 
                placeholder="Enter 6-digit OTP"
                maxlength="6"
                required
                :disabled="isLoading"
                @input="formatOTP"
              >
            </div>
          </div>
          
          <div class="otp-actions">
            <button 
              @click="verifyOTP" 
              class="action-button primary" 
              :disabled="isLoading || otp.length !== 6"
            >
              <span v-if="!isLoading" class="button-text">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
                </svg>
                Verify OTP
              </span>
              <span v-else class="loading-content">
                <div class="spinner"></div>
                <span>Verifying...</span>
              </span>
            </button>
            
            <button 
              @click="resendOTP" 
              class="action-button secondary" 
              :disabled="isLoading || resendCooldown > 0"
            >
              <span v-if="resendCooldown === 0" class="button-text">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" stroke="currentColor" stroke-width="2"/>
                  <path d="M21 3v5h-5" stroke="currentColor" stroke-width="2"/>
                </svg>
                Resend OTP
              </span>
              <span v-else class="button-text">
                Resend in {{ resendCooldown }}s
              </span>
            </button>
          </div>
        </div>
        
        <!-- Step 3: New Password -->
        <div v-if="currentStep === 3" class="step-content">
          <p class="step-description">
            OTP verified successfully! Please enter your new password.
          </p>
          
          <div class="input-group">
            <label for="newPassword">New Password</label>
            <div class="input-wrapper">
              <div class="input-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                  <circle cx="12" cy="16" r="1" stroke="currentColor" stroke-width="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <input 
                :type="showNewPassword ? 'text' : 'password'" 
                id="newPassword" 
                v-model="newPassword" 
                placeholder="Enter new password"
                required
                :disabled="isLoading"
              >
              <button 
                type="button"
                @click="toggleNewPasswordVisibility" 
                class="password-toggle"
                :title="showNewPassword ? 'Hide password' : 'Show password'"
              >
                <svg v-if="showNewPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" stroke="currentColor" stroke-width="2"/>
                  <line x1="1" y1="1" x2="23" y2="23" stroke="currentColor" stroke-width="2"/>
                </svg>
                <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2"/>
                  <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                </svg>
              </button>
            </div>
          </div>
          
          <div class="input-group">
            <label for="confirmPassword">Confirm Password</label>
            <div class="input-wrapper">
              <div class="input-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
                  <circle cx="12" cy="16" r="1" stroke="currentColor" stroke-width="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <input 
                :type="showConfirmPassword ? 'text' : 'password'" 
                id="confirmPassword" 
                v-model="confirmPassword" 
                placeholder="Confirm new password"
                required
                :disabled="isLoading"
              >
              <button 
                type="button"
                @click="toggleConfirmPasswordVisibility" 
                class="password-toggle"
                :title="showConfirmPassword ? 'Hide password' : 'Show password'"
              >
                <svg v-if="showConfirmPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" stroke="currentColor" stroke-width="2"/>
                  <line x1="1" y1="1" x2="23" y2="23" stroke="currentColor" stroke-width="2"/>
                </svg>
                <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2"/>
                  <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2"/>
                </svg>
              </button>
            </div>
          </div>
          
          <div class="password-requirements" v-if="newPassword">
            <h4>Password Requirements:</h4>
            <ul>
              <li :class="{ valid: newPassword.length >= 8 }">
                <svg v-if="newPassword.length >= 8" width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
                </svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                </svg>
                At least 8 characters
              </li>
              <li :class="{ valid: /[A-Z]/.test(newPassword) }">
                <svg v-if="/[A-Z]/.test(newPassword)" width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
                </svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                </svg>
                One uppercase letter
              </li>
              <li :class="{ valid: /[a-z]/.test(newPassword) }">
                <svg v-if="/[a-z]/.test(newPassword)" width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
                </svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                </svg>
                One lowercase letter
              </li>
              <li :class="{ valid: /[0-9]/.test(newPassword) }">
                <svg v-if="/[0-9]/.test(newPassword)" width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
                </svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                </svg>
                One number
              </li>
            </ul>
          </div>
          
          <button 
            @click="resetPassword" 
            class="action-button primary" 
            :disabled="isLoading || !isPasswordValid || newPassword !== confirmPassword"
          >
            <span v-if="!isLoading" class="button-text">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke="currentColor" stroke-width="2"/>
                <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
              </svg>
              Reset Password
            </span>
            <span v-else class="loading-content">
              <div class="spinner"></div>
              <span>Resetting Password...</span>
            </span>
          </button>
        </div>
        
        <!-- Success Step -->
        <div v-if="currentStep === 4" class="step-content success-step">
          <div class="success-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="m9 12 2 2 4-4" stroke="currentColor" stroke-width="2"/>
            </svg>
          </div>
          <h3>Password Reset Successful!</h3>
          <p>Your password has been successfully reset. You can now log in with your new password.</p>
          
          <button @click="closeModal" class="action-button primary">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" stroke="currentColor" stroke-width="2"/>
            </svg>
            Back to Login
          </button>
        </div>
      </div>
      
      <!-- Error Message -->
      <div v-if="errorMessage" class="error-alert">
        <div class="error-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2"/>
            <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2"/>
          </svg>
        </div>
        <span>{{ errorMessage }}</span>
        <button @click="errorMessage = ''" class="error-close">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
            <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted, watch } from 'vue'
import { axiosInstance } from '@/config/api.js'
import { API_ENDPOINTS } from '@/config/api.js'

const props = defineProps({
  showModal: {
    type: Boolean,
    default: false
  },
  username: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close'])

// Reactive data
const currentStep = ref(1)
const email = ref('')
const otp = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)
const resendCooldown = ref(0)
let cooldownTimer = null

// Watch for modal opening and username changes
watch(() => props.showModal, (newVal) => {
  if (newVal && props.username) {
    fetchUserEmail()
  }
})

// Function to fetch user email by username
const fetchUserEmail = async () => {
  if (!props.username) return
  
  try {
    isLoading.value = true
    errorMessage.value = ''
    
    const response = await axiosInstance.get(API_ENDPOINTS.GET_USER_EMAIL, {
      params: { username: props.username }
    })
    
    if (response.data.success) {
      email.value = response.data.email
    } else {
      errorMessage.value = response.data.message || 'Could not find user with this username'
    }
  } catch (error) {
    if (error.response && error.response.data) {
      errorMessage.value = error.response.data.message || 'Failed to fetch user email'
    } else {
      errorMessage.value = 'Network error. Please try again.'
    }
    console.error('Fetch user email error:', error)
  } finally {
    isLoading.value = false
  }
}

// Computed properties
const isPasswordValid = computed(() => {
  return newPassword.value.length >= 8 && 
         /[A-Z]/.test(newPassword.value) && 
         /[a-z]/.test(newPassword.value) && 
         /[0-9]/.test(newPassword.value)
})

// Methods
const closeModal = () => {
  resetForm()
  emit('close')
}

const resetForm = () => {
  currentStep.value = 1
  email.value = ''
  otp.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
  errorMessage.value = ''
  showNewPassword.value = false
  showConfirmPassword.value = false
  resendCooldown.value = 0
  if (cooldownTimer) {
    clearInterval(cooldownTimer)
    cooldownTimer = null
  }
}

const formatOTP = (event) => {
  // Only allow numbers and limit to 6 digits
  const value = event.target.value.replace(/\D/g, '').slice(0, 6)
  otp.value = value
}

const sendOTP = async () => {
  if (!email.value) {
    errorMessage.value = 'Please enter your email address'
    return
  }
  
  try {
    isLoading.value = true
    errorMessage.value = ''
    
    const response = await axiosInstance.post(API_ENDPOINTS.SEND_OTP, {
      Email: email.value
    })
    
    if (response.data.success) {
      currentStep.value = 2
      startResendCooldown()
    } else {
      errorMessage.value = response.data.message || 'Failed to send OTP'
    }
  } catch (error) {
    if (error.response && error.response.data) {
      errorMessage.value = error.response.data.message || 'Failed to send OTP'
    } else {
      errorMessage.value = 'Network error. Please try again.'
    }
    console.error('Send OTP error:', error)
  } finally {
    isLoading.value = false
  }
}

const verifyOTP = async () => {
  if (!otp.value || otp.value.length !== 6) {
    errorMessage.value = 'Please enter a valid 6-digit OTP'
    return
  }
  
  try {
    isLoading.value = true
    errorMessage.value = ''
    
    const response = await axiosInstance.post(API_ENDPOINTS.VERIFY_OTP, {
      Email: email.value,
      otp: otp.value
    })
    
    if (response.data.success) {
      currentStep.value = 3
    } else {
      errorMessage.value = response.data.message || 'Invalid OTP'
    }
  } catch (error) {
    if (error.response && error.response.data) {
      errorMessage.value = error.response.data.message || 'Failed to verify OTP'
    } else {
      errorMessage.value = 'Network error. Please try again.'
    }
    console.error('Verify OTP error:', error)
  } finally {
    isLoading.value = false
  }
}

const resetPassword = async () => {
  if (!isPasswordValid.value) {
    errorMessage.value = 'Please ensure your password meets all requirements'
    return
  }
  
  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match'
    return
  }
  
  try {
    isLoading.value = true
    errorMessage.value = ''
    
    const response = await axiosInstance.post(API_ENDPOINTS.RESET_PASSWORD, {
      Email: email.value,
      new_password: newPassword.value
    })
    
    if (response.data.success) {
      currentStep.value = 4
    } else {
      errorMessage.value = response.data.message || 'Failed to reset password'
    }
  } catch (error) {
    if (error.response && error.response.data) {
      errorMessage.value = error.response.data.message || 'Failed to reset password'
    } else {
      errorMessage.value = 'Network error. Please try again.'
    }
    console.error('Reset password error:', error)
  } finally {
    isLoading.value = false
  }
}

const resendOTP = async () => {
  if (resendCooldown.value > 0) return
  
  try {
    isLoading.value = true
    errorMessage.value = ''
    
    const response = await axiosInstance.post(API_ENDPOINTS.SEND_OTP, {
      Email: email.value
    })
    
    if (response.data.success) {
      startResendCooldown()
      errorMessage.value = 'OTP resent successfully'
      setTimeout(() => {
        errorMessage.value = ''
      }, 3000)
    } else {
      errorMessage.value = response.data.message || 'Failed to resend OTP'
    }
  } catch (error) {
    if (error.response && error.response.data) {
      errorMessage.value = error.response.data.message || 'Failed to resend OTP'
    } else {
      errorMessage.value = 'Network error. Please try again.'
    }
    console.error('Resend OTP error:', error)
  } finally {
    isLoading.value = false
  }
}

const startResendCooldown = () => {
  resendCooldown.value = 60 // 60 seconds
  cooldownTimer = setInterval(() => {
    resendCooldown.value--
    if (resendCooldown.value <= 0) {
      clearInterval(cooldownTimer)
      cooldownTimer = null
    }
  }, 1000)
}

const toggleNewPasswordVisibility = () => {
  showNewPassword.value = !showNewPassword.value
}

const toggleConfirmPasswordVisibility = () => {
  showConfirmPassword.value = !showConfirmPassword.value
}

// Cleanup on unmount
onUnmounted(() => {
  if (cooldownTimer) {
    clearInterval(cooldownTimer)
  }
})
</script>

<style scoped>
.spinner-small {
  width: 18px;
  height: 18px;
  border: 2px solid #e5e7eb;
  border-top: 2px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.forgot-password-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal-content {
  position: relative;
  background: white;
  border-radius: 16px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  animation: slideInUp 0.3s ease-out;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.close-button {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.close-button:hover {
  background: #f3f4f6;
  color: #374151;
}

.modal-body {
  padding: 2rem;
}

.step-content {
  text-align: center;
}

.step-description {
  color: #6b7280;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.input-group {
  margin-bottom: 1.5rem;
  text-align: left;
}

.input-group label {
  display: block;
  font-size: 0.95rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  z-index: 2;
}

.input-wrapper input {
  width: 100%;
  height: 48px;
  padding: 0 3rem 0 2.5rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.input-wrapper input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.password-toggle {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.password-toggle:hover {
  color: #6b7280;
  background: #f3f4f6;
}

.action-button {
  width: 100%;
  padding: 0.875rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.action-button.primary {
  background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
  color: white;
}

.action-button.secondary {
  background: #f8fafc;
  color: #374151;
  border: 2px solid #e5e7eb;
}

.action-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.button-text {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.loading-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.otp-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.otp-actions .action-button {
  flex: 1;
  margin-bottom: 0;
}

.password-requirements {
  text-align: left;
  margin: 1.5rem 0;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.password-requirements h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.password-requirements ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.password-requirements li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.password-requirements li.valid {
  color: #059669;
}

.password-requirements li svg {
  flex-shrink: 0;
}

.success-step {
  text-align: center;
}

.success-icon {
  margin-bottom: 1.5rem;
  color: #059669;
}

.success-step h3 {
  color: #059669;
  margin-bottom: 1rem;
}

.success-step p {
  color: #6b7280;
  margin-bottom: 2rem;
}

.error-alert {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fca5a5;
  color: #dc2626;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  margin-top: 1rem;
  position: relative;
}

.error-close {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #dc2626;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.error-close:hover {
  background: rgba(220, 38, 38, 0.1);
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 640px) {
  .modal-content {
    margin: 1rem;
    max-height: calc(100vh - 2rem);
  }
  
  .modal-header {
    padding: 1rem 1.5rem;
  }
  
  .modal-body {
    padding: 1.5rem;
  }
  
  .otp-actions {
    flex-direction: column;
  }
}
</style> 