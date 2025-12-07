import axios from 'axios'
import { API_BASE_URL } from '../config/api.js'
import eventBus, { LOGOUT_EVENT, LOGIN_EVENT } from '../utils/eventBus.js'
 
class AuthService {
    constructor() {
        this.baseURL = API_BASE_URL
        this.accessToken = localStorage.getItem('access_token')
        this.refreshToken = localStorage.getItem('refresh_token')
        this.isLoggingOut = false // Flag to prevent refresh during logout
        this.isRefreshing = false // Flag to prevent multiple simultaneous refresh attempts
        this.failedRefreshAttempts = 0 // Track failed refresh attempts
        this.maxRefreshAttempts = 3 // Maximum number of refresh attempts
        this.refreshInterval = null // Periodic refresh interval
        this.setupAxiosInterceptors()
        this.startPeriodicTokenRefresh()
    }
 
    setupAxiosInterceptors() {
        // Request interceptor to add JWT token
        axios.interceptors.request.use(
            async (config) => {
                // Don't add token if we're in the process of logging out
                if (this.isLoggingOut) {
                    return Promise.reject(new Error('Logging out'))
                }
               
                // Skip auth check for login/refresh endpoints
                const isAuthEndpoint = config.url && (
                    config.url.includes('/api/jwt/login/') ||
                    config.url.includes('/api/jwt/refresh/') ||
                    config.url.includes('/api/login/') ||
                    config.url.includes('/api/logout/')
                )
               
                if (!isAuthEndpoint) {
                    const token = localStorage.getItem('access_token')
                    if (token) {
                        // Only check and refresh token if it's close to expiring (not on every request)
                        // This prevents unnecessary refresh attempts that could cause logout loops
                        const accessTokenExpires = localStorage.getItem('access_token_expires')
                        if (accessTokenExpires) {
                            const expirationTime = new Date(accessTokenExpires)
                            const currentTime = new Date()
                            const timeUntilExpiration = expirationTime.getTime() - currentTime.getTime()
                            
                            // Only refresh if token expires in less than 10 minutes
                            if (timeUntilExpiration < 10 * 60 * 1000 && timeUntilExpiration > 0) {
                                // Token is close to expiring, try to refresh (but don't block the request if it fails)
                                this.checkAndRefreshToken().catch(err => {
                                    console.warn('⚠️ Token refresh check failed (non-blocking):', err.message)
                                })
                            }
                        }
                        
                        config.headers.Authorization = `Bearer ${token}`
                        // Reduced logging - only log for important requests
                        if (config.url.includes('/jwt/') || config.url.includes('/api/risk/')) {
                            console.log(`🔐 [AuthService] Adding JWT token to request: ${config.method.toUpperCase()} ${config.url}`)
                        }
                    } else {
                        // No token available - but don't block the request, let it go through
                        // The backend will return 401 if auth is required, and the response interceptor will handle it
                        console.warn(`⚠️ [AuthService] No JWT token found for request: ${config.method.toUpperCase()} ${config.url}`)
                    }
                }
                return config
            },
            (error) => {
                return Promise.reject(error)
            }
        )
 
        // Response interceptor to handle 401 errors and refresh tokens
        axios.interceptors.response.use(
            (response) => {
                return response
            },
            async (error) => {
                const originalRequest = error.config
               
                // CRITICAL: Don't try to refresh if the refresh endpoint itself failed
                // This prevents infinite loops when refresh token is invalid
                if (originalRequest.url && originalRequest.url.includes('/api/jwt/refresh/')) {
                    console.error('❌ Refresh endpoint returned 401 - refresh token is invalid/expired')
                    // Don't try to refresh again, just reject
                    return Promise.reject(error)
                }
               
                // Handle 401 errors (token expired)
                if (error.response && error.response.status === 401 && !originalRequest._retry) {
                    // Don't try to refresh if we're already refreshing or logging out
                    if (this.isRefreshing || this.isLoggingOut) {
                        console.warn('⚠️ Refresh already in progress or logging out - skipping refresh attempt')
                        return Promise.reject(error)
                    }
                    
                    console.log('🔄 401 error detected - attempting token refresh...')
                   
                    // Mark this request as retried to prevent infinite loops
                    originalRequest._retry = true
                   
                    try {
                        // Attempt to refresh the token
                        const refreshSuccess = await this.refreshAccessToken()
                       
                        if (refreshSuccess) {
                            console.log('✅ Token refreshed successfully, retrying original request')
                           
                            // Update the authorization header with new token
                            const newToken = localStorage.getItem('access_token')
                            if (newToken) {
                                originalRequest.headers.Authorization = `Bearer ${newToken}`
                            }
                           
                            // Retry the original request
                            return axios(originalRequest)
                        } else {
                            console.warn('❌ Token refresh failed - user will need to login again')
                            // Don't force logout immediately - let the user continue with limited access
                            // Only clear tokens if we've exceeded max attempts (handled in refreshAccessToken)
                            return Promise.reject(error)
                        }
                    } catch (refreshError) {
                        console.error('❌ Error during token refresh:', refreshError)
                        // Don't force logout immediately - let the user continue with limited access
                        return Promise.reject(error)
                    }
                }
               
                return Promise.reject(error)
            }
        )
    }
 
    async login(username, password, loginType = 'username') {
        console.log('🔥🔥🔥 [AuthService] LOGIN FUNCTION CALLED - NEW VERSION WITH INCIDENT FETCH 🔥🔥🔥');
        try {
            // Reset flags on login
            this.isLoggingOut = false
            this.isRefreshing = false
            this.failedRefreshAttempts = 0
           
            // ========================================
            // LICENSE VALIDATION PROCESS - AUTH SERVICE
            // ========================================
            // Step 1: Send login request to backend which will validate license
            console.log('🔐 LICENSE VALIDATION: Sending login request to backend for license validation...')
            const response = await axios.post(`${this.baseURL}/api/jwt/login/`, {
                username,
                password,
                login_type: loginType
            })
 
            if (response.data.status === 'success') {
                const { access_token, refresh_token, access_token_expires, refresh_token_expires, user, license_verified } = response.data
               
                // Step 2: Check if license validation was successful from backend response
                console.log('🔐 LICENSE VALIDATION: Backend response received:', {
                    license_verified: license_verified,
                    has_license_key: !!user.license_key,
                    license_key_preview: user.license_key ? `${user.license_key.substring(0, 10)}...` : 'None'
                })
               
                // Store tokens
                localStorage.setItem('access_token', access_token)
                localStorage.setItem('refresh_token', refresh_token)
                localStorage.setItem('access_token_expires', access_token_expires)
                localStorage.setItem('refresh_token_expires', refresh_token_expires)
               
                // Store user info
                localStorage.setItem('user', JSON.stringify(user))
                localStorage.setItem('user_id', user.UserId.toString())
                localStorage.setItem('user_email', user.Email)
                localStorage.setItem('user_name', user.UserName)
                localStorage.setItem('user_full_name', `${user.FirstName} ${user.LastName}`)
                localStorage.setItem('isAuthenticated', 'true')
                localStorage.setItem('is_logged_in', 'true')
               
                // Update axios default headers
                axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
               
                // Initialize RBAC service
                try {
                    const { default: rbacService } = await import('./rbacService.js')
                    await rbacService.initialize()
                    console.log('🔐 RBAC service initialized after login')
                } catch (error) {
                    console.error('❌ Error initializing RBAC service:', error)
                }
                
                // ========================================
                // PREFETCH ALL DATA AFTER LOGIN (NON-BLOCKING)
                // ========================================
                // Start data prefetch asynchronously AFTER login completes
                // This ensures documents don't load during sign-in click
                console.log('🚀 [AuthService] Scheduling data prefetch after login...')
                
                // Use setTimeout to defer data fetching until after login completes
                setTimeout(async () => {
                    // Verify user is still authenticated before fetching
                    if (!this.isAuthenticated()) {
                        console.log('⚠️ [AuthService] User not authenticated, skipping data prefetch')
                        return
                    }
                    
                    console.log('🚀 [AuthService] Starting data prefetch for all services...')
                    const startTime = Date.now()
                    
                    try {
                        // Import all services (documents are loaded when DocumentHandling component mounts)
                        const [
                            { default: incidentService },
                            { default: riskDataService },
                            { default: integrationsDataService },
                            { default: treeDataService }
                        ] = await Promise.all([
                            import('./incidentService.js'),
                            import('./riskService.js'),
                            import('./integrationsService.js'),
                            import('./treeService.js')
                        ])
                        
                        console.log('✅ [AuthService] All services imported successfully')
                        
                        // Fetch all data in parallel (except documents - they load when component mounts)
                        const fetchPromises = {
                            incidents: incidentService.fetchAllIncidentData(user.UserId)
                                .then(result => {
                                    console.log(`✅ [AuthService] Incident data: ${incidentService.getData('incidents')?.length || 0} incidents`)
                                    localStorage.setItem('incident_data_fetched', 'true')
                                    return result
                                })
                                .catch(error => {
                                    console.error('❌ [AuthService] Incident fetch error:', error.message)
                                    return { success: false, error: error.message }
                                }),
                            
                            risks: riskDataService.fetchAllRiskData()
                                .then(() => {
                                    const stats = riskDataService.getCacheStats()
                                    console.log(`✅ [AuthService] Risk data: ${stats.risksCount} risks, ${stats.riskInstancesCount} instances`)
                                    localStorage.setItem('risk_data_fetched', 'true')
                                    return { success: true }
                                })
                                .catch(error => {
                                    console.error('❌ [AuthService] Risk fetch error:', error.message)
                                    return { success: false, error: error.message }
                                }),
                            
                            integrations: integrationsDataService.fetchAllIntegrationData()
                                .then(() => {
                                    const stats = integrationsDataService.getCacheStats()
                                    console.log(`✅ [AuthService] Integration data: ${stats.applicationsCount} applications, ${stats.connectedApplications} connected`)
                                    localStorage.setItem('integrations_data_fetched', 'true')
                                    return { success: true }
                                })
                                .catch(error => {
                                    console.error('❌ [AuthService] Integrations fetch error:', error.message)
                                    return { success: false, error: error.message }
                                }),
                            
                            // Documents will be loaded when DocumentHandling component mounts
                            // Don't fetch here to avoid loading on sign-in click
                            documents: Promise.resolve({ success: true, skipped: true })
                                .then(() => {
                                    console.log('⏭️ [AuthService] Documents will be loaded when DocumentHandling component mounts')
                                    return { success: true, skipped: true }
                                }),
                            
                            tree: treeDataService.fetchAllTreeData()
                                .then(() => {
                                    const stats = treeDataService.getCacheStats()
                                    console.log(`✅ [AuthService] Tree data: ${stats.frameworksCount} frameworks`)
                                    localStorage.setItem('tree_data_fetched', 'true')
                                    return { success: true }
                                })
                                .catch(error => {
                                    console.error('❌ [AuthService] Tree fetch error:', error.message)
                                    return { success: false, error: error.message }
                                })
                        }
                        
                        // Wait for all fetches to complete
                        const results = await Promise.allSettled([
                            fetchPromises.incidents,
                            fetchPromises.risks,
                            fetchPromises.integrations,
                            fetchPromises.documents,
                            fetchPromises.tree
                        ])
                        
                        const duration = Date.now() - startTime
                        const successCount = results.filter(r => r.status === 'fulfilled' && r.value?.success !== false).length
                        
                        console.log(`🎉 [AuthService] Data prefetch complete in ${duration}ms`)
                        console.log(`✅ [AuthService] ${successCount}/5 services fetched successfully`)
                        
                        // Store fetch completion time
                        localStorage.setItem('all_data_fetched', 'true')
                        localStorage.setItem('data_fetch_time', new Date().toISOString())
                        localStorage.setItem('data_fetch_duration', duration.toString())
                        
                        // Store promise globally for components
                        window.dataFetchPromise = Promise.resolve(results)
                        
                    } catch (error) {
                        console.error('❌ [AuthService] CRITICAL ERROR during data prefetch:', error)
                        console.error('❌ [AuthService] Error details:', error.stack)
                        localStorage.setItem('all_data_fetched', 'false')
                    }
                }, 100) // Small delay to ensure login completes first
                
                // Start periodic token refresh
                this.startPeriodicTokenRefresh()
                
                // Emit login event
                eventBus.emit(LOGIN_EVENT, { user })
               
                console.log('🔐 JWT Login successful!', {
                    user_id: user.UserId,
                    email: user.Email,
                    username: user.UserName
                })
               
                // Step 3: Return success with license validation status
                console.log('✅ LICENSE VALIDATION: Returning successful login with license verification status')
                return {
                    success: true,
                    user,
                    license_verified: license_verified, // Include license validation status
                    tokens: {
                        access: access_token,
                        refresh: refresh_token,
                        access_token_expires: access_token_expires,
                        refresh_token_expires: refresh_token_expires
                    }
                }
            } else {
                throw new Error(response.data.message || 'Login failed')
            }
        } catch (error) {
            console.error('❌ JWT Login error:', error)
            throw error
        }
    }
 
    async checkAndRefreshToken() {
        try {
            // Don't refresh if we're already refreshing or logging out
            if (this.isRefreshing || this.isLoggingOut) {
                return false
            }
            
            // First check if we have an access token at all
            const accessToken = localStorage.getItem('access_token')
            if (!accessToken) {
                // No token available, can't refresh
                return false
            }
            
            const accessTokenExpires = localStorage.getItem('access_token_expires')
            if (!accessTokenExpires) {
                // Token exists but no expiration info - don't try to refresh automatically
                // This prevents unnecessary refresh attempts that could cause logout loops
                // The token will be validated by the backend, and if it's invalid, the response interceptor will handle it
                console.warn('⚠️ No access token expiration found - skipping automatic refresh')
                return false
            }

            const expirationTime = new Date(accessTokenExpires)
            const currentTime = new Date()
            const timeUntilExpiration = expirationTime.getTime() - currentTime.getTime()
           
            // Only refresh if token expires in less than 10 minutes AND is not already expired
            if (timeUntilExpiration < 10 * 60 * 1000 && timeUntilExpiration > 0) {
                console.log('🔄 Access token expires soon, refreshing...')
                return await this.refreshAccessToken()
            }
           
            return false
        } catch (error) {
            console.error('❌ Error checking token expiration:', error)
            return false
        }
    }
 
    async refreshAccessToken() {
        try {
            // Don't refresh if we're logging out or already refreshing
            if (this.isLoggingOut || this.isRefreshing) {
                console.log('🛑 Refresh blocked: isLoggingOut=' + this.isLoggingOut + ', isRefreshing=' + this.isRefreshing)
                return false
            }

            // Check if we've exceeded max refresh attempts
            if (this.failedRefreshAttempts >= this.maxRefreshAttempts) {
                console.error('❌ Max refresh attempts exceeded. Clearing tokens to force re-login.')
                this.clearAuthData(true) // Redirect to login
                return false
            }

            this.isRefreshing = true

            const refreshToken = localStorage.getItem('refresh_token')
            if (!refreshToken) {
                console.error('❌ No refresh token available')
                this.failedRefreshAttempts++
                throw new Error('No refresh token available')
            }
 
            const response = await axios.post(`${this.baseURL}/api/jwt/refresh/`, {
                refresh_token: refreshToken
            })
 
            if (response.data.status === 'success') {
                const { access_token, refresh_token, access_token_expires, refresh_token_expires } = response.data
               
                // Update stored tokens - CRITICAL: Also update refresh token (token rotation)
                localStorage.setItem('access_token', access_token)
                localStorage.setItem('access_token_expires', access_token_expires)
                
                // BUGFIX: Save new refresh token to prevent 401 loop
                // Backend rotates refresh tokens for security, so we must save the new one
                if (refresh_token) {
                    localStorage.setItem('refresh_token', refresh_token)
                    console.log('🔄 Refresh token updated (token rotation)')
                }
                if (refresh_token_expires) {
                    localStorage.setItem('refresh_token_expires', refresh_token_expires)
                }
               
                // Update axios default headers
                axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
               
                // Reset failed attempts counter on success
                this.failedRefreshAttempts = 0
                
                console.log('🔄 JWT token refreshed successfully')
                return true
            } else {
                this.failedRefreshAttempts++
                throw new Error(response.data.message || 'Token refresh failed')
            }
        } catch (error) {
            console.error('❌ JWT token refresh error:', error)
            this.failedRefreshAttempts++
            
            // If we've failed too many times, clear auth data to force re-login
            if (this.failedRefreshAttempts >= this.maxRefreshAttempts) {
                console.error('❌ Too many failed refresh attempts. User needs to re-login.')
                this.clearAuthData(true) // Redirect to login
            }
            
            return false
        } finally {
            this.isRefreshing = false
        }
    }
 
    async logout() {
        try {
            // Set logout flag to prevent refresh attempts
            this.isLoggingOut = true
            this.isRefreshing = false
           
            // Emit logout event before clearing data
            eventBus.emit(LOGOUT_EVENT, {})
           
            const token = localStorage.getItem('access_token')
            if (token) {
                // Call logout endpoint
                await axios.post(`${this.baseURL}/api/jwt/logout/`, {}, {
                    headers: { Authorization: `Bearer ${token}` }
                })
            }
        } catch (error) {
            console.warn('Logout API call failed, but continuing with local cleanup:', error)
        } finally {
            // Clear all stored data (don't auto-redirect, let logout flow handle it)
            this.clearAuthData(false)
            // Reset flags
            this.isLoggingOut = false
            this.isRefreshing = false
            this.failedRefreshAttempts = 0
        }
    }
 
    forceLogout() {
        // COMPLETELY DISABLED: No automatic logout
        console.log('🛡️ Force logout disabled - user will not be logged out automatically')
        // Do nothing - user stays logged in
    }
 
    clearAuthData(shouldRedirect = true) {
        // Stop periodic refresh
        this.stopPeriodicTokenRefresh()
       
        // Clear tokens
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('access_token_expires')
        localStorage.removeItem('refresh_token_expires')
       
        // Clear user data
        localStorage.removeItem('user')
        localStorage.removeItem('user_id')
        localStorage.removeItem('user_email')
        localStorage.removeItem('user_name')
        localStorage.removeItem('user_full_name')
        localStorage.removeItem('isAuthenticated')
        localStorage.removeItem('is_logged_in')
        localStorage.removeItem('remember_me')
       
        // Clear axios headers
        delete axios.defaults.headers.common['Authorization']
       
        // Clear RBAC service data
        try {
            const { default: rbacService } = require('./rbacService.js')
            rbacService.clearUserData()
        } catch (error) {
            console.error('❌ Error clearing RBAC data:', error)
        }
       
        // Clear all service data
        try {
            const { default: incidentService } = require('./incidentService.js')
            incidentService.clearCache()
            console.log('🧹 Incident service data cleared')
        } catch (error) {
            console.error('❌ Error clearing Incident data:', error)
        }
        
        try {
            const { default: riskDataService } = require('./riskService.js')
            riskDataService.clearCache()
            console.log('🧹 Risk service data cleared')
        } catch (error) {
            console.error('❌ Error clearing Risk data:', error)
        }
        
        try {
            const { default: integrationsDataService } = require('./integrationsService.js')
            integrationsDataService.clearCache()
            console.log('🧹 Integrations service data cleared')
        } catch (error) {
            console.error('❌ Error clearing Integrations data:', error)
        }
        
        try {
            const { default: documentDataService } = require('./documentService.js')
            documentDataService.clearCache()
            console.log('🧹 Document service data cleared')
        } catch (error) {
            console.error('❌ Error clearing Document data:', error)
        }
        
        try {
            const { default: treeDataService } = require('./treeService.js')
            treeDataService.clearCache()
            console.log('🧹 Tree service data cleared')
        } catch (error) {
            console.error('❌ Error clearing Tree data:', error)
        }
       
        console.log('🧹 Auth data cleared')
        
        // Redirect to login if requested (default: true)
        // Only redirect if not already on login page and not during explicit logout
        // Also check if we're in the middle of a form submission to avoid interrupting user work
        if (shouldRedirect && 
            window.location.pathname !== '/login' && 
            window.location.pathname !== '/' &&
            !this.isLoggingOut) {
            console.log('🔄 Redirecting to login page...')
            // Use setTimeout to allow cleanup to complete first
            setTimeout(() => {
                // Double-check we're still not logged in before redirecting
                if (!localStorage.getItem('access_token')) {
                    window.location.href = '/login'
                }
            }, 100)
        }
    }
   
    startPeriodicTokenRefresh() {
        // Only start if user is authenticated
        if (!this.isAuthenticated()) {
            return
        }
       
        // Clear any existing interval
        this.stopPeriodicTokenRefresh()
       
        // Check token every 5 minutes (300 seconds) - less aggressive refresh
        this.refreshInterval = setInterval(async () => {
            try {
                // Reduced logging - only log when actually refreshing
                await this.checkAndRefreshToken()
            } catch (error) {
                console.error('❌ Error in periodic token refresh:', error)
            }
        }, 5 * 60 * 1000) // 5 minutes instead of 2 minutes
       
        console.log('🔄 Periodic token refresh started')
    }
   
    stopPeriodicTokenRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval)
            this.refreshInterval = null
            console.log('🛑 Periodic token refresh stopped')
        }
    }
 
    async verifyToken() {
        try {
            const token = localStorage.getItem('access_token')
            if (!token) {
                return false
            }
 
            const response = await axios.get(`${this.baseURL}/api/jwt/verify/`, {
                headers: { Authorization: `Bearer ${token}` }
            })
 
            return response.data.status === 'success'
        } catch (error) {
            console.error('❌ Token verification failed:', error)
            return false
        }
    }
 
    isAuthenticated() {
        // Check if user has valid authentication data
        const token = localStorage.getItem('access_token')
        const user = localStorage.getItem('user')
        const isLoggedIn = localStorage.getItem('is_logged_in')
       
        const isAuth = !!(token && user && isLoggedIn === 'true')
        console.log(`🔐 [AuthService] Authentication check: ${isAuth} (token: ${!!token}, user: ${!!user}, logged_in: ${isLoggedIn})`)
        return isAuth
    }
 
    getCurrentUser() {
        const userStr = localStorage.getItem('user')
        return userStr ? JSON.parse(userStr) : null
    }
 
    getAccessToken() {
        return localStorage.getItem('access_token')
    }
 
    getRefreshToken() {
        return localStorage.getItem('refresh_token')
    }
 
    isNonCriticalEndpoint(url) {
        // List of endpoints that should not trigger logout on 401 errors
        const nonCriticalEndpoints = [
            '/api/frameworks/',
            '/api/policy-categories/',
            '/api/user-role/',
            '/api/entities/',
            '/api/users/',
            '/api/departments/',
            '/api/users-for-reviewer-selection/',
            '/api/notifications/',
            '/api/current-user/',
            '/api/custom-users/',
            '/api/get-notifications/',
            '/api/policies/',
            '/api/compliance/',
            '/api/incident/',
            '/api/risk/',
            '/api/audit/',
            '/api/all-policies/',
            '/api/framework-versions/',
            '/api/policy-versions/',
            '/api/subpolicies/',
            '/api/compliances/',
            '/api/rbac/roles/',
            '/api/rbac/users-for-dropdown/',
            '/api/rbac/permissions/',
            '/api/rbac/user-permissions/'
        ]
       
        return nonCriticalEndpoints.some(endpoint => url.includes(endpoint))
    }
 
    // Legacy session-based authentication (for backward compatibility)
    async sessionLogin(username, password, loginType = 'username') {
        try {
            const response = await axios.post(`${this.baseURL}/api/login/`, {
                username,
                password,
                login_type: loginType
            })
 
            if (response.data && response.data.user) {
                localStorage.setItem('isAuthenticated', 'true')
                localStorage.setItem('user', JSON.stringify(response.data.user))
                localStorage.setItem('user_id', response.data.user.id.toString())
                localStorage.setItem('user_email', response.data.user.email)
                localStorage.setItem('user_name', response.data.user.username)
                localStorage.setItem('user_full_name', `${response.data.user.firstName} ${response.data.user.lastName}`)
                localStorage.setItem('is_logged_in', 'true')
               
                console.log('🔐 Session Login successful!', {
                    user_id: response.data.user.id,
                    email: response.data.user.email,
                    username: response.data.user.username
                })
               
                return {
                    success: true,
                    user: response.data.user
                }
            } else {
                throw new Error('Invalid response from server')
            }
        } catch (error) {
            console.error('❌ Session Login error:', error)
            throw error
        }
    }
 
    async sessionLogout() {
        try {
            await axios.post(`${this.baseURL}/api/logout/`)
        } catch (error) {
            console.warn('Session logout API call failed, but continuing with local cleanup:', error)
        } finally {
            this.clearAuthData(false) // Don't auto-redirect for explicit logout
        }
    }
}
 
// Create singleton instance
const authService = new AuthService()
 
export default authService