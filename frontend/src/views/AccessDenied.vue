<template>
  <div class="access-denied-container">
    <div class="illustration-wrapper">
      <!-- Background 403 with door as 0 -->
      <div class="error-code-bg">
        <span class="digit digit-4">4</span>
        <div class="digit-0-container">
          <span class="digit digit-0">0</span>
          <div class="door-illustration">
            <div class="door-frame">
              <div class="door-window-circle"></div>
              <div class="door-handle-circle"></div>
              <div class="door-close-sign">CLOSE</div>
            </div>
          </div>
        </div>
        <span class="digit digit-3">3</span>
      </div>

      <!-- Ground line -->
      <div class="ground-line"></div>

      <!-- Paper airplane -->
      <div class="paper-airplane">
        <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
          <path d="M5 5 L20 20 L5 35" stroke="#B0C4D8" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M8 8 L15 15" stroke="#B0C4D8" stroke-width="1.5" fill="none" stroke-linecap="round"/>
        </svg>
      </div>

      <!-- Decorative elements -->
      <div class="deco-elements">
        <div class="deco-box deco-1"></div>
        <div class="deco-box deco-2"></div>
        <div class="deco-box deco-3"></div>
      </div>

      <!-- Plant/Leaf decoration -->
      <div class="plant-decoration">
        <svg width="80" height="100" viewBox="0 0 80 100" xmlns="http://www.w3.org/2000/svg">
          <path d="M40 80 Q30 60 35 40 Q38 20 40 10" stroke="#A8C5D8" stroke-width="2" fill="none"/>
          <ellipse cx="50" cy="35" rx="15" ry="25" fill="#B8D5E8" opacity="0.6" transform="rotate(30 50 35)"/>
          <ellipse cx="30" cy="50" rx="12" ry="20" fill="#B8D5E8" opacity="0.6" transform="rotate(-20 30 50)"/>
        </svg>
      </div>

      <!-- Characters -->
      <div class="character-left">
        <div class="character-head"></div>
        <div class="character-body teal-shirt"></div>
        <div class="character-legs dark-legs"></div>
        <div class="laptop-device"></div>
      </div>

      <div class="character-right">
        <div class="character-head"></div>
        <div class="character-body coral-shirt"></div>
        <div class="character-legs red-pants"></div>
        <div class="character-shoes"></div>
      </div>
    </div>

    <!-- Content Section -->
    <div class="content-section">
      <h1 class="main-heading">We are Sorry...</h1>
      <p class="description-text">
        The page you're trying to access has restricted access.
      </p>
      <p class="sub-description">
        Please refer to your system administrator
      </p>

      <div class="primary-actions">
        <button @click="goBack" class="back-button">Go Back</button>
        <button @click="showDetails = !showDetails" class="details-toggle-btn">
          <i :class="showDetails ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
          {{ showDetails ? 'Hide' : 'Show' }} Details
        </button>
      </div>

      <transition name="fade-slide">
        <div v-if="showDetails" class="details-box">
            <div class="detail-row">
              <span class="detail-label">Feature:</span>
              <span class="detail-value">{{ accessDeniedInfo.feature }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">User ID:</span>
              <span class="detail-value">{{ userInfo.userId || 'Not available' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Role:</span>
              <span class="detail-value">{{ userInfo.role || 'Not available' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">URL:</span>
              <span class="detail-value">{{ accessDeniedInfo.url || requestedUrl }}</span>
            </div>
            <div v-if="accessDeniedInfo.timestamp" class="detail-row">
              <span class="detail-label">Time:</span>
              <span class="detail-value">{{ new Date(accessDeniedInfo.timestamp).toLocaleString() }}</span>
            </div>

            <div class="details-actions">
              <button @click="goHome" class="detail-action-btn">
                <i class="fas fa-home"></i> Go Home
              </button>
              <button @click="contactAdmin" class="detail-action-btn">
                <i class="fas fa-envelope"></i> Contact Admin
              </button>
            </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script>
import rbacService from '@/services/rbacService.js'

export default {
  name: 'AccessDenied',
  data() {
    return {
      showDetails: false,
      userInfo: {
        userId: null,
        role: null
      },
      requestedUrl: '',
      accessDeniedInfo: {
        feature: 'this feature',
        message: 'You don\'t have permission to access this page. Please contact your administrator if you believe this is an error.',
        timestamp: null,
        url: ''
      }
    }
  },
  
  async mounted() {
    try {
      this.userInfo.userId = rbacService.getUserId()
      this.userInfo.role = rbacService.getUserRole()
    } catch (error) {
      console.error('Error getting user info:', error)
    }
    
    this.requestedUrl = this.$route.fullPath
    
    try {
      const accessDeniedData = sessionStorage.getItem('accessDeniedInfo')
      if (accessDeniedData) {
        this.accessDeniedInfo = JSON.parse(accessDeniedData)
        sessionStorage.removeItem('accessDeniedInfo')
      }
    } catch (error) {
      console.error('Error parsing access denied info:', error)
    }
  },
  
  methods: {
    goBack() {
      this.$router.go(-1)
    },
    
    goHome() {
      this.$router.push('/home')
    },
    
    contactAdmin() {
      import('@/utils/accessUtils').then(({ AccessUtils }) => {
        AccessUtils.defaultContactAdmin()
      }).catch(error => {
        console.error('Error showing contact admin popup:', error)
        window.location.href = 'mailto:admin@company.com?subject=Access Denied - Need Permission'
      })
    }
  }
}
</script>

<style scoped>
.access-denied-container {
  height: 100vh;
  width: 100%;
  background: #FAFBFC;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 20px;
}

/* Illustration Wrapper */
.illustration-wrapper {
  position: relative;
  width: 100%;
  max-width: 900px;
  height: 280px;
  margin-bottom: 40px;
  flex-shrink: 0;
}

/* Error Code Background - 403 */
.error-code-bg {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  z-index: 1;
}

.digit {
  font-size: 200px;
  font-weight: 700;
  color: #E5EBF1;
  line-height: 1;
  font-family: 'Arial', 'Helvetica', sans-serif;
  user-select: none;
}

/* Digit 0 Container with Door */
.digit-0-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.digit-0 {
  position: relative;
  z-index: 1;
}

.door-illustration {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
}

.door-frame {
  width: 90px;
  height: 140px;
  background: white;
  border: 3px solid #5A7A99;
  border-radius: 45px 45px 0 0;
  position: relative;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.door-window-circle {
  position: absolute;
  top: 30px;
  left: 50%;
  transform: translateX(-50%);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #E8EFF5;
  border: 2px solid #8FA3B8;
}

.door-handle-circle {
  position: absolute;
  top: 50%;
  left: 20px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #8FA3B8;
  border: 2px solid #5A7A99;
}

.door-close-sign {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  background: #E8EFF5;
  color: #5A7A99;
  padding: 4px 12px;
  border-radius: 3px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

/* Ground Line */
.ground-line {
  position: absolute;
  bottom: 40px;
  left: 0;
  right: 0;
  height: 2px;
  background: #C8D6E5;
  z-index: 2;
}

/* Paper Airplane */
.paper-airplane {
  position: absolute;
  top: 20px;
  left: 15%;
  animation: fly-around 4s ease-in-out infinite;
  z-index: 3;
}

@keyframes fly-around {
  0%, 100% {
    transform: translate(0, 0) rotate(-5deg);
  }
  50% {
    transform: translate(40px, -15px) rotate(5deg);
  }
}

/* Decorative Elements */
.deco-elements {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
}

.deco-box {
  position: absolute;
  background: #E5EBF1;
  opacity: 0.4;
}

.deco-1 {
  width: 50px;
  height: 12px;
  top: 30px;
  left: 10%;
  border-radius: 6px;
}

.deco-2 {
  width: 35px;
  height: 35px;
  top: 60px;
  left: 25%;
  border-radius: 4px;
}

.deco-3 {
  width: 60px;
  height: 10px;
  top: 40px;
  right: 15%;
  border-radius: 5px;
}

/* Plant Decoration */
.plant-decoration {
  position: absolute;
  bottom: 40px;
  right: 8%;
  z-index: 3;
}

/* Characters */
.character-left {
  position: absolute;
  bottom: 40px;
  left: 20%;
  z-index: 4;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.character-right {
  position: absolute;
  bottom: 40px;
  right: 20%;
  z-index: 4;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.character-head {
  width: 36px;
  height: 36px;
  background: #FFD4BC;
  border-radius: 50%;
  margin-bottom: 5px;
  position: relative;
  z-index: 2;
}

.character-body {
  width: 50px;
  height: 55px;
  border-radius: 10px 10px 6px 6px;
  position: relative;
  z-index: 1;
}

.teal-shirt {
  background: linear-gradient(180deg, #2DBFB4 0%, #26A99F 100%);
}

.coral-shirt {
  background: linear-gradient(180deg, #3D4A7C 0%, #2C3656 100%);
}

.character-legs {
  width: 48px;
  height: 40px;
  border-radius: 6px 6px 8px 8px;
  margin-top: -5px;
}

.dark-legs {
  background: #2C3E5C;
}

.red-pants {
  background: #F76D6D;
}

.character-shoes {
  width: 50px;
  height: 8px;
  background: #1E2A3C;
  border-radius: 4px;
  margin-top: 2px;
}

.laptop-device {
  position: absolute;
  bottom: 15px;
  left: 15px;
  width: 30px;
  height: 20px;
  background: #5A7A99;
  border-radius: 2px;
  border: 2px solid #3D5468;
}

/* Content Section */
.content-section {
  text-align: center;
  max-width: 600px;
  z-index: 5;
  flex-shrink: 0;
}

.primary-actions {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 10px;
}

.main-heading {
  font-size: 42px;
  font-weight: 700;
  color: #3D4A7C;
  margin: 0 0 20px;
  letter-spacing: -0.5px;
}

.description-text {
  font-size: 17px;
  color: #5A6A85;
  line-height: 1.6;
  margin: 0 0 8px;
}

.sub-description {
  font-size: 15px;
  color: #7A8AA0;
  line-height: 1.6;
  margin: 0 0 32px;
}

/* Back Button */
.back-button {
  background: linear-gradient(135deg, #2DBFB4 0%, #1FA39A 100%);
  color: white;
  border: none;
  padding: 14px 45px;
  border-radius: 50px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 8px 20px rgba(45, 191, 180, 0.3);
}

.back-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(45, 191, 180, 0.4);
}

.back-button:active {
  transform: translateY(0);
}

/* Details Toggle Section */
/* no longer used; spacing handled by .primary-actions */
.details-toggle-section { display: none; }

.details-toggle-btn {
  background: transparent;
  border: 2px solid #D5E0EB;
  color: #3D4A7C;
  padding: 10px 26px;
  border-radius: 50px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.details-toggle-btn:hover {
  border-color: #2DBFB4;
  color: #2DBFB4;
  background: #F0FFFE;
}

/* Transition */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Details Box */
.details-box {
  margin-top: 20px;
  padding: 20px 24px;
  background: #F7F9FB;
  border-radius: 12px;
  border: 1px solid #E5EBF1;
  text-align: left;
  max-height: 220px;
  overflow-y: auto;
}

.detail-row {
  display: flex;
  margin: 12px 0;
  font-size: 13px;
  line-height: 1.5;
  flex-wrap: wrap;
  gap: 8px;
}

.detail-label {
  color: #3D4A7C;
  font-weight: 600;
  min-width: 100px;
  flex-shrink: 0;
}

.detail-value {
  color: #5A6A85;
  flex: 1;
  word-break: break-word;
}

.details-actions {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid #D5E0EB;
  display: flex;
  gap: 10px;
}

.detail-action-btn {
  flex: 1;
  background: white;
  border: 2px solid #D5E0EB;
  color: #3D4A7C;
  padding: 9px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.detail-action-btn:hover {
  transform: translateY(-1px);
  border-color: #2DBFB4;
  color: #2DBFB4;
  background: #F0FFFE;
}

/* Scrollbar */
.details-box::-webkit-scrollbar {
  width: 6px;
}

.details-box::-webkit-scrollbar-track {
  background: #E5EBF1;
  border-radius: 3px;
}

.details-box::-webkit-scrollbar-thumb {
  background: #C8D6E5;
  border-radius: 3px;
}

/* Responsive Design */
@media (max-width: 968px) {
  .illustration-wrapper {
    height: 220px;
    margin-bottom: 30px;
  }

  .digit {
    font-size: 150px;
  }

  .door-frame {
    width: 75px;
    height: 120px;
  }

  .character-left {
    left: 15%;
  }

  .character-right {
    right: 15%;
  }

  .main-heading {
    font-size: 36px;
  }
}

@media (max-width: 640px) {
  .illustration-wrapper {
    height: 180px;
    margin-bottom: 25px;
  }

  .digit {
    font-size: 110px;
  }

  .door-frame {
    width: 60px;
    height: 100px;
  }

  .door-window-circle {
    width: 22px;
    height: 22px;
    top: 20px;
  }

  .character-head {
    width: 30px;
    height: 30px;
  }

  .character-body {
    width: 42px;
    height: 48px;
  }

  .character-legs {
    width: 40px;
    height: 35px;
  }

  .plant-decoration {
    transform: scale(0.7);
  }

  .main-heading {
    font-size: 30px;
  }

  .description-text {
    font-size: 16px;
  }

  .sub-description {
    font-size: 14px;
    margin-bottom: 24px;
  }

  .back-button {
    padding: 12px 36px;
    font-size: 15px;
  }

  .details-actions, .primary-actions {
    flex-direction: column;
  }

  .detail-action-btn, .primary-actions .back-button, .primary-actions .details-toggle-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .illustration-wrapper {
    height: 150px;
  }

  .digit {
    font-size: 85px;
  }

  .door-frame {
    width: 50px;
    height: 85px;
  }

  .character-head {
    width: 26px;
    height: 26px;
  }

  .character-body {
    width: 38px;
    height: 42px;
  }

  .character-legs {
    width: 36px;
    height: 30px;
  }

  .main-heading {
    font-size: 26px;
  }

  .description-text {
    font-size: 15px;
  }

  .sub-description {
    font-size: 13px;
  }

  .back-button {
    padding: 11px 32px;
    font-size: 14px;
  }
}
</style>
