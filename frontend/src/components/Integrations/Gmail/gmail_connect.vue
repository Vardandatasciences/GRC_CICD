<template>
  <div class="gmail-connect-container">
    <div class="gmail-card">
      <div class="gmail-header">
        <h1>
          <i class="fas fa-envelope"></i>
          Connect to Gmail
        </h1>
      </div>
    <main class="connect-main">
      <div class="welcome-section">
        
        <div class="features">
          <div class="feature-item">
            <i class="fas fa-check-circle"></i>
            <span>View recent emails with attachments</span>
          </div>
          <div class="feature-item">
            <i class="fas fa-check-circle"></i>
            <span>Access upcoming calendar events</span>
          </div>
          <div class="feature-item">
            <i class="fas fa-check-circle"></i>
            <span>Download email attachments</span>
          </div>
          <div class="feature-item">
            <i class="fas fa-check-circle"></i>
            <span>Secure OAuth authentication</span>
          </div>
         </div>
         
         <p class="description">
           Connect your Gmail account to access your emails and calendar events directly in your GRC dashboard
         </p>
       </div>

      <!-- Connection Status -->
      <div v-if="connectionStatus" class="status-section">
        <div class="status-card" :class="connectionStatus.status">
           <div class="status-icon">
             <i v-if="connectionStatus.status === 'connected'" class="fas fa-check-circle"></i>
             <i v-else-if="connectionStatus.status === 'connecting'" class="fas fa-spinner fa-spin"></i>
           </div>
          <div class="status-content">
            <h3>{{ connectionStatus.title }}</h3>
            <p>{{ connectionStatus.message }}</p>
          </div>
        </div>
      </div>

      <!-- Connection Actions -->
      <div class="actions-section">
        <button 
          v-if="!isConnected && !isConnecting"
          @click="connectToGmail" 
          class="connect-btn"
        >
          <i class="fas fa-plug"></i>
          Connect to Gmail (OAuth)
        </button>
        
        <button 
          v-if="isConnecting"
          class="connect-btn connecting"
          disabled
        >
          <i class="fas fa-spinner fa-spin"></i>
          Connecting...
        </button>

        <div v-if="isConnected" class="connected-actions">
          <button @click="goToGmailData" class="btn btn-primary">
            <i class="fas fa-envelope"></i>
            View Gmail Data
          </button>
          <button @click="disconnectGmail" class="btn btn-secondary">
            <i class="fas fa-unlink"></i>
            Disconnect
          </button>
        </div>

        <div class="info-message">
          <i class="fas fa-info-circle"></i>
          <span>This will redirect you to Gmail for authentication</span>
        </div>
      </div>

      <!-- Gmail Data Display Section -->
      <div v-if="isConnected && showDataView" class="data-section">
        <div class="data-header">
          <h3>
            <i class="fas fa-envelope"></i>
            Gmail Data
          </h3>
          <div class="data-actions">
            <button @click="fetchGmailMessages" :disabled="gmailLoading" class="btn btn-primary btn-sm">
              <i class="fas fa-sync-alt" :class="{ 'fa-spin': gmailLoading }"></i>
              {{ gmailLoading ? 'Loading...' : 'Refresh' }}
            </button>
            <button @click="hideDataView" class="btn btn-secondary btn-sm">
              <i class="fas fa-times"></i>
              Hide Data
            </button>
          </div>
        </div>

        <!-- Gmail Messages -->
        <div v-if="gmailLoading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading your emails...</p>
        </div>
        
        <div v-else-if="gmailError" class="error-state">
          <p>❌ {{ gmailError }}</p>
          <button @click="fetchGmailMessages" class="retry-btn">Try Again</button>
        </div>
        
        <div v-else-if="gmailMessages.length === 0" class="empty-state">
          <p>No messages found</p>
        </div>
        
        <div v-else class="messages-list">
          <div v-for="message in gmailMessages" :key="message.id" class="message-item">
            <div class="message-header">
              <div class="message-info">
                <h4 class="message-subject">{{ message.subject || 'No Subject' }}</h4>
                <p class="message-from">{{ message.from }}</p>
              </div>
              <div class="message-meta">
                <span class="message-date">{{ formatMessageDate(message.date) }}</span>
                <span v-if="message.has_attachments" class="attachment-indicator">
                  📎 {{ message.attachment_count }} attachment{{ message.attachment_count !== 1 ? 's' : '' }}
                </span>
              </div>
            </div>
            <div class="message-content">
              <p class="message-snippet">{{ message.snippet }}</p>
              
              <!-- Attachments Section -->
              <div v-if="message.has_attachments && message.attachments" class="attachments-section">
                <div class="attachments-grid">
                  <div v-for="attachment in message.attachments" :key="attachment.id" class="attachment-item">
                    <div class="attachment-icon">
                      <span v-if="attachment.is_image">🖼️</span>
                      <span v-else-if="attachment.is_pdf">📄</span>
                      <span v-else-if="attachment.is_document">📝</span>
                      <span v-else>📎</span>
                    </div>
                    <div class="attachment-info">
                      <div class="attachment-name">{{ attachment.filename }}</div>
                      <div class="attachment-details">
                        {{ formatFileSize(attachment.size) }} • {{ attachment.mime_type }}
                      </div>
                    </div>
                    <div class="attachment-actions">
                      <button 
                        @click="downloadAttachment(message.id, attachment.id, attachment.filename)"
                        class="download-btn"
                        :disabled="downloadingAttachments.includes(attachment.id)"
                      >
                        {{ downloadingAttachments.includes(attachment.id) ? '⏳' : '⬇️' }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Error Display -->
      <div v-if="error" class="error-section">
        <div class="error-card">
          <i class="fas fa-exclamation-triangle"></i>
          <div class="error-content">
            <h4>Connection Error</h4>
            <p>{{ error }}</p>
            <button @click="clearError" class="retry-btn">
              <i class="fas fa-redo"></i>
              Try Again
            </button>
          </div>
        </div>
       </div>
     </main>
     </div>
   </div>
</template>

<script>
import axios from 'axios'
import { API_BASE_URL } from '../../../config/api.js'

export default {
  name: 'GmailConnect',
  data() {
    return {
      isConnected: false,
      isConnecting: false,
      error: '',
      connectionStatus: null,
      userInfo: null,
      showDataView: false,
      gmailMessages: [],
      gmailLoading: false,
      gmailError: '',
      downloadingAttachments: []
    }
  },
  async mounted() {
    // Check if this is an OAuth success redirect or error
    const urlParams = new URLSearchParams(window.location.search)
    const oauthSuccess = urlParams.get('oauth_success')
    const oauthError = urlParams.get('oauth_error')
    const viewData = urlParams.get('viewData')
    
    if (oauthSuccess === 'true') {
      // OAuth was successful, redirect to main Gmail integration page
      this.connectionStatus = {
        status: 'connected',
        title: 'Gmail Connected Successfully!',
        message: 'Redirecting to Gmail integration...'
      }
      this.isConnected = true
      
      // Redirect to main Gmail integration page after a short delay
      setTimeout(() => {
        this.$router.push('/integrations/gmail?oauth_success=true')
      }, 2000)
    } else if (oauthError) {
      // Handle OAuth error
      this.error = decodeURIComponent(oauthError)
      this.connectionStatus = {
        status: 'error',
        title: 'OAuth Error',
        message: this.error
      }
      this.isConnected = false
      this.isConnecting = false
      
      // Clean up URL parameters
      window.history.replaceState({}, document.title, window.location.pathname)
    } else {
      await this.checkConnectionStatus()
    }
    
    // If viewData parameter is present and Gmail is connected, show data view
    if (viewData === 'true' && this.isConnected) {
      this.showDataView = true
      await this.fetchGmailMessages()
    }
    
    // Clean up URL parameters
    if (viewData || oauthError) {
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  },
  methods: {
    async checkConnectionStatus() {
      try {
        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
        const response = await axios.get(`${API_BASE_URL}/api/gmail/connection-status/`, {
          params: { user_id: userId },
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token') || sessionStorage.getItem('access_token')}`
          }
        })
        
        if (response.data.success && response.data.connected) {
          this.isConnected = true
          this.userInfo = response.data.user_info || { name: 'Gmail User' }
          
          // Show stored data info if available
          let statusMessage = `Connected as ${this.userInfo.name || 'Gmail User'}`
          if (response.data.has_stored_data) {
            statusMessage += ` (${response.data.messages_count} messages, ${response.data.attachments_count} attachments stored)`
          }
          
          this.connectionStatus = {
            status: 'connected',
            title: 'Gmail Already Connected',
            message: statusMessage
          }
         } else {
           this.isConnected = false
           this.connectionStatus = null
         }
       } catch (error) {
         console.error('Connection check failed:', error)
         
         // Handle authentication errors
         if (error.response?.status === 401) {
           this.error = 'Authentication failed. Please log in again.'
         } else {
           this.error = 'Failed to check Gmail connection status.'
         }
         
         this.isConnected = false
         this.connectionStatus = null
       }
    },

    async connectToGmail() {
      this.isConnecting = true
      this.error = ''
      this.connectionStatus = {
        status: 'connecting',
        title: 'Connecting to Gmail...',
        message: 'Redirecting to Gmail for authentication'
      }
      
      try {
        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
        
        // Clear any existing OAuth state to ensure fresh connection
        localStorage.removeItem('gmail_oauth_state')
        
        // Get OAuth URL from backend
        const response = await axios.get(`${API_BASE_URL}/api/gmail/oauth-initiate/`, {
          params: { user_id: userId },
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token') || sessionStorage.getItem('access_token')}`
          }
        })
        
        if (response.data.success) {
          // Store state for callback handling
          localStorage.setItem('gmail_oauth_state', response.data.state)
          
          // Redirect to OAuth URL
          window.location.href = response.data.auth_url
        } else {
          throw new Error(response.data.error || 'Failed to initiate Gmail OAuth')
        }
      } catch (error) {
        console.error('Failed to initiate Gmail OAuth:', error)
        this.error = error.response?.data?.error || error.message || 'Failed to connect to Gmail'
         this.isConnecting = false
         this.connectionStatus = null
      }
    },

    async disconnectGmail() {
      try {
        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
        const response = await axios.post(`${API_BASE_URL}/api/gmail/disconnect/`, {
          user_id: userId
        }, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token') || sessionStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        })
        
        if (response.data.success) {
          this.isConnected = false
          this.connectionStatus = {
            status: 'disconnected',
            title: 'Gmail Disconnected',
            message: 'Your Gmail account has been disconnected successfully'
          }
        } else {
          throw new Error(response.data.error || 'Failed to disconnect Gmail')
        }
      } catch (error) {
        console.error('Failed to disconnect Gmail:', error)
        this.error = error.response?.data?.error || error.message || 'Failed to disconnect Gmail'
      }
    },

    goToGmailData() {
      // Navigate to Gmail data page
      this.$router.push('/integrations/gmail')
    },

    clearError() {
      this.error = ''
      this.connectionStatus = null
    },

    // Gmail data display methods
    async fetchGmailMessages() {
      this.gmailLoading = true
      this.gmailError = ''
      
      try {
        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
        const response = await axios.get(`${API_BASE_URL}/api/gmail/messages/`, {
          params: { 
            user_id: userId,
            include_attachments: true
          },
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token') || sessionStorage.getItem('access_token')}`
          }
        })
        
        if (response.data.success) {
          this.gmailMessages = response.data.messages || []
          console.log(`Fetched ${this.gmailMessages.length} Gmail messages`)
        } else {
          throw new Error(response.data.error || 'Failed to fetch Gmail messages')
        }
      } catch (error) {
        console.error('Error fetching Gmail messages:', error)
        this.gmailError = error.response?.data?.error || error.message || 'Failed to fetch Gmail messages'
      } finally {
        this.gmailLoading = false
      }
    },

    async downloadAttachment(messageId, attachmentId, filename) {
      if (this.downloadingAttachments.includes(attachmentId)) {
        return
      }
      
      this.downloadingAttachments.push(attachmentId)
      
      try {
        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
        const response = await axios.get(`${API_BASE_URL}/api/gmail/download-attachment/`, {
          params: { 
            user_id: userId,
            message_id: messageId,
            attachment_id: attachmentId
          },
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token') || sessionStorage.getItem('access_token')}`
          }
        })
        
        if (response.data.success) {
          // Create download link
          const link = document.createElement('a')
          link.href = `data:${response.data.mime_type};base64,${response.data.data}`
          link.download = filename
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
        } else {
          throw new Error(response.data.error || 'Failed to download attachment')
        }
      } catch (error) {
        console.error('Error downloading attachment:', error)
        alert(`Failed to download ${filename}: ${error.message}`)
      } finally {
        this.downloadingAttachments = this.downloadingAttachments.filter(id => id !== attachmentId)
      }
    },

    formatMessageDate(dateString) {
      if (!dateString) return 'Unknown date'
      try {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      } catch (error) {
        return 'Invalid date'
      }
    },

    formatFileSize(bytes) {
      if (!bytes) return '0 B'
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(1024))
      return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
    },

    hideDataView() {
      this.showDataView = false
      this.gmailMessages = []
      this.gmailError = ''
    },

    async loadStoredData() {
      this.gmailLoading = true
      this.gmailError = ''
      
      try {
        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
        const response = await axios.get(`${API_BASE_URL}/api/gmail/stored-data/`, {
          params: { user_id: userId },
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token') || sessionStorage.getItem('access_token')}`
          }
        })
        
        if (response.data.success) {
          const structuredData = response.data.data
          if (structuredData.messages && structuredData.messages.length > 0) {
            // Convert structured data back to the format expected by the UI
            this.gmailMessages = structuredData.messages.map(msg => ({
              id: msg.gmail_message_id || msg.message_id,
              subject: msg.subject,
              from: msg.from,
              date: msg.date,
              snippet: msg.snippet,
              has_attachments: msg.has_attachments,
              attachment_count: msg.attachment_count,
              attachments: msg.attachments.map(att => ({
                id: att.gmail_attachment_id || att.attachment_id,
                filename: att.filename,
                mime_type: att.mime_type,
                size: att.size,
                file_extension: att.file_extension,
                is_image: att.is_image,
                is_pdf: att.is_pdf,
                is_document: att.is_document,
                data: att.data
              }))
            }))
            
            // Show data view automatically
            this.showDataView = true
            console.log(`Loaded ${this.gmailMessages.length} structured Gmail messages with metadata:`, structuredData.metadata)
          } else {
            throw new Error('No stored messages found')
          }
        } else {
          throw new Error(response.data.error || 'Failed to load stored data')
        }
      } catch (error) {
        console.error('Error loading stored data:', error)
        this.gmailError = error.message || 'Failed to load stored data'
      } finally {
        this.gmailLoading = false
      }
    },

    async saveToDatabase() {
      if (this.gmailMessages.length === 0) {
        alert('No messages to save')
        return
      }
      
      try {
        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
        const response = await axios.post(`${API_BASE_URL}/api/gmail/save-to-db/`, {
          user_id: userId,
          messages: this.gmailMessages
        }, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token') || sessionStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        })
        
        if (response.data.success) {
          console.log('✅ Gmail data saved to database successfully')
          console.log(`Messages saved: ${response.data.messages_saved}`)
          console.log(`Attachments saved: ${response.data.attachments_saved}`)
          alert(`✅ Successfully saved ${response.data.messages_saved} messages with ${response.data.attachments_saved} attachments to database!`)
        } else {
          throw new Error(response.data.error || 'Failed to save to database')
        }
      } catch (error) {
        console.error('Error saving to database:', error)
        alert(`❌ Failed to save to database: ${error.message}`)
      }
    }
  }
}
</script>

<style scoped>
.gmail-connect-container {
  min-height: calc(100vh - 100px);
  background: #f8f9fa;
  margin-left: 220px;
  margin-right: 0;
  margin-top: -60px;
  margin-bottom: 0;
  padding: 20px;
  box-sizing: border-box;
  width: calc(100vw - 280px);
}

.gmail-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.gmail-header {
  background: #f8f9fa;
  border-bottom: 1px solid #e5e7eb;
  padding: 20px 30px;
}

.gmail-header h1 {
  color: #2c3e50;
  margin: 0;
  font-weight: 600;
  font-size: 1.8rem;
  display: flex;
  align-items: center;
  gap: 12px;
}

.gmail-header h1 i {
  color: #ea4335;
  font-size: 1.5rem;
}

.connect-main {
  max-width: 800px;
  margin: 0;
  padding: 40px 20px;
  width: 100%;
  min-height: calc(100vh - 200px);
}

.welcome-section {
  text-align: left;
  margin-bottom: 40px;
  color: #333;
}


.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
  max-width: 100%;
  justify-content: start;
}

.description {
  font-size: 18px;
  color: #666;
  margin-bottom: 30px;
  line-height: 1.6;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  font-size: 14px;
  color: #000000 !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.feature-item i {
  color: #34a853;
  font-size: 16px;
}

.feature-item span {
  color: #000000 !important;
  font-weight: 500;
  visibility: visible !important;
  opacity: 1 !important;
}

.status-section {
  margin-bottom: 30px;
}

.status-card {
  display: flex;
  align-items: center;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  gap: 15px;
}

.status-card.connected {
  background: linear-gradient(135deg, #34a853 0%, #2d8f47 100%);
  color: white;
}

.status-card.connecting {
  background: linear-gradient(135deg, #4285f4 0%, #3367d6 100%);
  color: white;
}


.status-icon {
  font-size: 24px;
}

.status-content h3 {
  margin: 0 0 5px 0;
  font-size: 18px;
  font-weight: 600;
}

.status-content p {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
}

.actions-section {
  text-align: left;
  margin-bottom: 30px;
}

.connect-btn {
  background: #ea4335;
  color: white;
  border: none;
  padding: 15px 30px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(234, 67, 53, 0.3);
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.connect-btn:hover:not(:disabled) {
  background: #d33b2c;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(234, 67, 53, 0.4);
}

.connect-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.connect-btn.connecting {
  background: #4285f4;
}

.connected-actions {
  display: flex;
  gap: 15px;
  justify-content: flex-start;
  flex-wrap: wrap;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
}

.btn-primary {
  background: #4285f4;
  color: white;
}

.btn-primary:hover {
  background: #3367d6;
  transform: translateY(-1px);
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
  transform: translateY(-1px);
}

.btn-info {
  background: #17a2b8;
  color: white;
}

.btn-info:hover:not(:disabled) {
  background: #138496;
  transform: translateY(-1px);
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #218838;
  transform: translateY(-1px);
}

.info-message {
  margin-top: 20px;
  padding: 12px 20px;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 6px;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
  margin-left: 0;
}

.error-section {
  margin-top: 20px;
}

.error-card {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 20px;
  background: #ffebee;
  border: 1px solid #ffcdd2;
  border-radius: 8px;
  color: #c62828;
}

.error-card i {
  font-size: 20px;
  margin-top: 2px;
}

.error-content h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
}

.error-content p {
  margin: 0 0 12px 0;
  font-size: 14px;
}

.retry-btn {
  background: #c62828;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.retry-btn:hover {
  background: #b71c1c;
}

@media (max-width: 768px) {
  .gmail-connect-container {
    margin-left: 0;
    margin-top: 80px;
    width: 100vw;
    padding: 10px;
  }
  
  .connect-main {
    padding: 20px 10px;
    min-height: calc(100vh - 150px);
  }
  
  .gmail-header {
    padding: 15px 20px;
  }
  
  .gmail-header h1 {
    font-size: 1.5rem;
  }
  
  .description {
    font-size: 16px;
  }
  
  .features {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .connected-actions {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .btn {
    width: 100%;
    max-width: 250px;
    justify-content: center;
  }
}

/* Gmail Data Display Styles */
.data-section {
  margin-top: 30px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.data-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  background: #f8f9fa;
  border-bottom: 1px solid #e5e7eb;
}

.data-header h3 {
  color: #2c3e50;
  margin: 0;
  font-weight: 600;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  gap: 12px;
}

.data-header h3 i {
  color: #ea4335;
  font-size: 1.2rem;
}

.data-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.btn-sm {
  padding: 8px 16px;
  font-size: 14px;
  border-radius: 6px;
}

.loading-state, .error-state, .empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #ea4335;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.retry-btn {
  background: #ea4335;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  margin-top: 10px;
}

.retry-btn:hover {
  background: #d33b2c;
}

.messages-list {
  max-height: 600px;
  overflow-y: auto;
}

.message-item {
  padding: 20px 30px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s ease;
}

.message-item:hover {
  background-color: #f8f9fa;
}

.message-item:last-child {
  border-bottom: none;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.message-info {
  flex: 1;
  min-width: 0;
}

.message-subject {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 5px 0;
  word-wrap: break-word;
}

.message-from {
  font-size: 14px;
  color: #666;
  margin: 0;
  word-wrap: break-word;
}

.message-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 5px;
  min-width: 120px;
}

.message-date {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
}

.attachment-indicator {
  font-size: 12px;
  color: #ea4335;
  background: #fff5f5;
  padding: 2px 8px;
  border-radius: 12px;
  white-space: nowrap;
}

.message-content {
  margin-top: 10px;
}

.message-snippet {
  font-size: 14px;
  color: #555;
  line-height: 1.5;
  margin: 0;
  word-wrap: break-word;
}

.attachments-section {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #f0f0f0;
}

.attachments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 10px;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.attachment-icon {
  font-size: 20px;
  min-width: 24px;
}

.attachment-info {
  flex: 1;
  min-width: 0;
}

.attachment-name {
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
  word-wrap: break-word;
  margin-bottom: 2px;
}

.attachment-details {
  font-size: 12px;
  color: #666;
  word-wrap: break-word;
}

.attachment-actions {
  display: flex;
  gap: 5px;
}

.download-btn {
  background: #4285f4;
  color: white;
  border: none;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.download-btn:hover:not(:disabled) {
  background: #3367d6;
}

.download-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .data-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .data-actions {
    justify-content: center;
  }
  
  .message-header {
    flex-direction: column;
    gap: 10px;
  }
  
  .message-meta {
    align-items: flex-start;
  }
  
  .attachments-grid {
    grid-template-columns: 1fr;
  }
}
</style>
