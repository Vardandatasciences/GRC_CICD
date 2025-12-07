<template>
  <div class="gmail-data-container">
    <div class="gmail-data-card">
      <div class="gmail-data-header">
        <div class="header-content">
          <h1>
            <i class="fas fa-envelope"></i>
            Gmail Data
          </h1>
          <p class="header-description">
            View your recent Gmail messages and attachments
          </p>
        </div>
        <div class="header-actions">
          <button @click="goBack" class="btn btn-secondary">
            <i class="fas fa-arrow-left"></i>
            Back to Integrations
          </button>
        </div>
      </div>

      <!-- Connection Status -->
      <div v-if="connectionStatus" class="status-section">
        <div class="status-card" :class="connectionStatus.status">
          <div class="status-icon">
            <i v-if="connectionStatus.status === 'connected'" class="fas fa-check-circle"></i>
            <i v-else-if="connectionStatus.status === 'loading'" class="fas fa-spinner fa-spin"></i>
          </div>
          <div class="status-content">
            <h3>{{ connectionStatus.title }}</h3>
            <p>{{ connectionStatus.message }}</p>
          </div>
        </div>
      </div>

      <!-- Data Actions -->
      <div class="data-actions-section">
        <div class="actions-left">
          <button @click="fetchGmailMessages" :disabled="gmailLoading" class="btn btn-primary">
            <i class="fas fa-sync-alt" :class="{ 'fa-spin': gmailLoading }"></i>
            {{ gmailLoading ? 'Loading...' : 'Refresh Messages' }}
          </button>
          <button @click="loadStoredData" :disabled="gmailLoading" class="btn btn-info">
            <i class="fas fa-database"></i>
            Load Stored Data
          </button>
          <button @click="saveToDatabase" :disabled="gmailLoading || gmailMessages.length === 0" class="btn btn-success">
            <i class="fas fa-save"></i>
            Save to Database
          </button>
        </div>
        <div class="actions-right">
          <div class="data-stats" v-if="gmailMessages.length > 0">
            <span class="stat-item">
              <i class="fas fa-envelope"></i>
              {{ gmailMessages.length }} messages
            </span>
            <span class="stat-item">
              <i class="fas fa-paperclip"></i>
              {{ totalAttachments }} attachments
            </span>
          </div>
        </div>
      </div>

      <!-- Gmail Messages Display -->
      <div class="messages-section">
        <div v-if="gmailLoading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading your emails...</p>
        </div>
        
        <div v-else-if="gmailError" class="error-state">
          <div class="error-content">
            <i class="fas fa-exclamation-triangle"></i>
            <div class="error-text">
              <h4>Error Loading Messages</h4>
              <p>{{ gmailError }}</p>
            </div>
            <button @click="fetchGmailMessages" class="retry-btn">
              <i class="fas fa-redo"></i>
              Try Again
            </button>
          </div>
        </div>
        
        <div v-else-if="gmailMessages.length === 0" class="empty-state">
          <div class="empty-content">
            <i class="fas fa-inbox"></i>
            <h3>No Messages Found</h3>
            <p>No Gmail messages were found. Try refreshing or check your connection.</p>
            <button @click="fetchGmailMessages" class="btn btn-primary">
              <i class="fas fa-sync-alt"></i>
              Refresh Messages
            </button>
          </div>
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
                <h5 class="attachments-title">
                  <i class="fas fa-paperclip"></i>
                  Attachments ({{ message.attachments.length }})
                </h5>
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
                        :title="`Download ${attachment.filename}`"
                      >
                        <i class="fas fa-download" v-if="!downloadingAttachments.includes(attachment.id)"></i>
                        <i class="fas fa-spinner fa-spin" v-else></i>
                      </button>
                      <button 
                        v-if="attachment.is_image"
                        @click="previewImage(attachment)"
                        class="preview-btn"
                        title="Preview image"
                      >
                        <i class="fas fa-eye"></i>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Image Preview Modal -->
    <div v-if="imagePreview" class="image-preview-modal" @click="closeImagePreview">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ imagePreview.filename }}</h3>
          <button @click="closeImagePreview" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <img :src="imagePreview.data" :alt="imagePreview.filename" class="preview-image" />
          <div class="image-info">
            <p>Size: {{ formatFileSize(imagePreview.size) }}</p>
            <p>Type: {{ imagePreview.mime_type }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { API_BASE_URL } from '../../../config/api.js'

export default {
  name: 'GmailData',
  data() {
    return {
      gmailMessages: [],
      gmailLoading: false,
      gmailError: '',
      connectionStatus: null,
      downloadingAttachments: [],
      imagePreview: null
    }
  },
  computed: {
    totalAttachments() {
      return this.gmailMessages.reduce((total, message) => {
        return total + (message.attachment_count || 0)
      }, 0)
    }
  },
  async mounted() {
    await this.checkConnectionStatus()
    if (this.connectionStatus && this.connectionStatus.status === 'connected') {
      await this.fetchGmailMessages()
    }
  },
  methods: {
    async checkConnectionStatus() {
      this.connectionStatus = {
        status: 'loading',
        title: 'Checking Gmail Connection...',
        message: 'Verifying your Gmail connection status'
      }

      try {
        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
        const response = await axios.get(`${API_BASE_URL}/api/gmail/connection-status/`, {
          params: { user_id: userId },
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token') || sessionStorage.getItem('access_token')}`
          }
        })
        
        if (response.data.success && response.data.connected) {
          this.connectionStatus = {
            status: 'connected',
            title: 'Gmail Connected',
            message: `Connected successfully. Ready to fetch your emails.`
          }
        } else {
          this.connectionStatus = {
            status: 'disconnected',
            title: 'Gmail Not Connected',
            message: 'Please connect your Gmail account first to view data.'
          }
        }
      } catch (error) {
        console.error('Connection check failed:', error)
        
        // Handle authentication errors
        if (error.response?.status === 401) {
          this.connectionStatus = {
            status: 'error',
            title: 'Authentication Error',
            message: 'Please log in again to access Gmail data.'
          }
        } else {
          this.connectionStatus = {
            status: 'error',
            title: 'Connection Error',
            message: 'Failed to check Gmail connection status.'
          }
        }
      }
    },

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
          console.log('=== GMAIL MESSAGES JSON DATA ===')
          console.log(JSON.stringify(response.data, null, 2))
          console.log('=== INDIVIDUAL MESSAGES ===')
          this.gmailMessages.forEach((msg, idx) => {
            console.log(`Message ${idx + 1}:`, JSON.stringify(msg, null, 2))
          })
        } else {
          throw new Error(response.data.error || 'Failed to fetch Gmail messages')
        }
      } catch (error) {
        console.error('Error fetching Gmail messages:', error)
        
        // Handle specific error types
        if (error.response?.status === 401) {
          this.gmailError = 'Authentication failed. Please log in again.'
        } else if (error.response?.status === 403) {
          this.gmailError = 'Access denied. Please check your Gmail connection.'
        } else if (error.response?.data?.error) {
          this.gmailError = error.response.data.error
        } else {
          this.gmailError = error.message || 'Failed to fetch Gmail messages'
        }
      } finally {
        this.gmailLoading = false
      }
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
          console.log('=== STORED GMAIL DATA JSON ===')
          console.log(JSON.stringify(response.data, null, 2))
          console.log('=== STRUCTURED DATA ===')
          console.log(JSON.stringify(structuredData, null, 2))
          
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
            console.log(`Loaded ${this.gmailMessages.length} structured Gmail messages with metadata:`, structuredData.metadata)
            console.log('=== CONVERTED UI DATA ===')
            console.log(JSON.stringify(this.gmailMessages, null, 2))
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

    previewImage(attachment) {
      if (attachment.is_image && attachment.data) {
        this.imagePreview = {
          filename: attachment.filename,
          data: `data:${attachment.mime_type};base64,${attachment.data}`,
          size: attachment.size,
          mime_type: attachment.mime_type
        }
      }
    },

    closeImagePreview() {
      this.imagePreview = null
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
    },

    goBack() {
      this.$router.push('/integrations/external')
    }
  }
}
</script>

<style scoped>
.gmail-data-container {
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

.gmail-data-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.gmail-data-header {
  background: #f8f9fa;
  border-bottom: 1px solid #e5e7eb;
  padding: 20px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  color: #2c3e50;
  margin: 0 0 5px 0;
  font-weight: 600;
  font-size: 1.8rem;
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-content h1 i {
  color: #ea4335;
  font-size: 1.5rem;
}

.header-description {
  color: #666;
  margin: 0;
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.status-section {
  margin: 20px 30px;
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

.status-card.loading {
  background: linear-gradient(135deg, #4285f4 0%, #3367d6 100%);
  color: white;
}

.status-card.disconnected {
  background: linear-gradient(135deg, #ea4335 0%, #d33b2c 100%);
  color: white;
}

.status-card.error {
  background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
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

.data-actions-section {
  padding: 20px 30px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafafa;
}

.actions-left {
  display: flex;
  gap: 10px;
}

.actions-right {
  display: flex;
  align-items: center;
}

.data-stats {
  display: flex;
  gap: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.stat-item i {
  color: #ea4335;
}

.messages-section {
  padding: 20px 30px;
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

.error-content {
  display: flex;
  align-items: center;
  gap: 15px;
  background: #ffebee;
  border: 1px solid #ffcdd2;
  border-radius: 8px;
  padding: 20px;
  color: #c62828;
}

.error-content i {
  font-size: 24px;
}

.error-text h4 {
  margin: 0 0 5px 0;
  font-size: 16px;
  font-weight: 600;
}

.error-text p {
  margin: 0;
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

.empty-content {
  text-align: center;
  padding: 40px 20px;
}

.empty-content i {
  font-size: 48px;
  color: #ccc;
  margin-bottom: 20px;
}

.empty-content h3 {
  color: #666;
  margin: 0 0 10px 0;
  font-size: 18px;
}

.empty-content p {
  color: #999;
  margin: 0 0 20px 0;
}

.messages-list {
  max-height: 600px;
  overflow-y: auto;
}

.message-item {
  padding: 20px;
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

.attachments-title {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 10px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.attachments-title i {
  color: #ea4335;
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

.download-btn, .preview-btn {
  background: #4285f4;
  color: white;
  border: none;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.download-btn:hover:not(:disabled), .preview-btn:hover:not(:disabled) {
  background: #3367d6;
}

.download-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.preview-btn {
  background: #34a853;
}

.preview-btn:hover:not(:disabled) {
  background: #2d8f47;
}

/* Image Preview Modal */
.image-preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 90%;
  max-height: 90%;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: #f8f9fa;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  color: #2c3e50;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
  text-align: center;
}

.preview-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 4px;
  margin-bottom: 15px;
}

.image-info {
  color: #666;
  font-size: 14px;
}

.image-info p {
  margin: 5px 0;
}

/* Button Styles */
.btn {
  padding: 10px 20px;
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

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-primary {
  background: #4285f4;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #3367d6;
  transform: translateY(-1px);
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
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

@media (max-width: 768px) {
  .gmail-data-container {
    margin-left: 0;
    margin-top: 80px;
    width: 100vw;
    padding: 10px;
  }
  
  .gmail-data-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .data-actions-section {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .actions-left {
    justify-content: center;
  }
  
  .data-stats {
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
  
  .btn {
    width: 100%;
    max-width: 250px;
    justify-content: center;
  }
}
</style>
