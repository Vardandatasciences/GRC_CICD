import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import axios from 'axios'
import '@fortawesome/fontawesome-free/css/all.min.css'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import Popup from './modules/popup';
import './styles/theme.css'
import { API_BASE_URL } from './config/api.js'

// Create Vuetify instance
const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
  },
})

// Configure axios defaults for JWT authentication
axios.defaults.baseURL = API_BASE_URL  // Use centralized API configuration
axios.defaults.headers.common['Content-Type'] = 'application/json'
// axios.defaults.timeout = 30000  // Removed timeout to prevent request timeouts

// CRITICAL: Enable credentials (cookies) for session management
axios.defaults.withCredentials = true
console.log('🍪 Axios configured to send cookies with requests (withCredentials: true)')

// Initialize JWT authentication service - import will set up axios interceptors automatically
import './services/authService.js'

console.log('🔐 Axios configured with JWT authentication')

// Track page load time for interceptor
sessionStorage.setItem('pageLoadTime', Date.now().toString())

// Setup HTTP interceptor for access control
console.log('🛡️ Setting up HTTP interceptor for access control')

// Add response interceptor to handle 403 (Forbidden) responses
// COMMENTED OUT: Disabled to allow home page to be accessible to all users
// axios.interceptors.response.use(
//   (response) => {
//     return response;
//   },
//   (error) => {
//     if (error.response && error.response.status === 403) {
//       console.log('🚫 Access denied (403) - redirecting to access denied page');
//       
//       // Store access denied information
//       const accessDeniedInfo = {
//         feature: 'API endpoint',
//         message: error.response.data?.message || 'You do not have permission to access this resource.',
//         timestamp: new Date().toISOString(),
//         url: error.config?.url || 'Unknown',
//         requiredPermission: error.response.data?.required_permission || 'Unknown'
//       };
//       sessionStorage.setItem('accessDeniedInfo', JSON.stringify(accessDeniedInfo));
//       
//       // Redirect to access denied page
//       if (window.router) {
//         window.router.push('/access-denied');
//       }
//     }
//     return Promise.reject(error);
//   }
// );

const app = createApp(App)
app.config.compilerOptions.isCustomElement = tag => tag.includes('-')
app.config.performance = true
app.config.warnHandler = () => null 
app.use(router)
app.use(store)
app.use(ElementPlus)
app.use(vuetify)
app.use(Popup)

// Make router and store available globally for AccessUtils
window.router = router
window.store = store

app.mount('#app')
