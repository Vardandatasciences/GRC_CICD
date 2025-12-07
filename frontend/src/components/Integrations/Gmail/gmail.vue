<template>
  <div class="gmail-integration">
    <main class="integration-main">
      <div class="back-section">
        <button @click="goBack" class="back-button">
          <i class="fas fa-arrow-left"></i>
          Back to Gmail Connect
        </button>
      </div>
      
      <div class="welcome-section">
        <h2>Gmail & Calendar Integration</h2>
        <p>View your recent emails and upcoming calendar events</p>
      </div>

      <!-- Tab Navigation -->
      <div class="tab-navigation">
        <button 
          @click="activeTab = 'gmail'" 
          :class="['tab-btn', { active: activeTab === 'gmail' }]"
        >
          📧 Recent Gmail Messages
          <span class="count-badge">{{ gmailMessages.length }}</span>
        </button>
        <button 
          @click="activeTab = 'calendar'" 
          :class="['tab-btn', { active: activeTab === 'calendar' }]"
        >
          📅 Recent Calendar Events
          <span class="count-badge">{{ calendarEvents.length }}</span>
        </button>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Gmail Tab Content -->
        <div v-if="activeTab === 'gmail'" class="tab-panel">
          <div class="panel-header">
            <div class="header-left">
              <h3>📧 Recent Gmail Messages</h3>
              <!-- <span v-if="gmailMessages.length > 0" class="auto-save-indicator">
                ✅ Auto-saved to database
              </span> -->
            </div>
            <button @click="fetchGmailMessages" :disabled="gmailLoading" class="refresh-btn">
              {{ gmailLoading ? 'Loading...' : 'Refresh' }}
            </button>
          </div>
          
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
          
          <div v-else class="messages-table-container">
            <table class="messages-table">
              <thead>
                <tr>
                  <th class="subject-column">Subject</th>
                  <th class="from-column">From</th>
                  <th class="description-column">Description</th>
                  <th class="attachments-column">Attachments</th>
                  <th class="download-column">Download</th>
                  <th class="plus-column">+</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="message in gmailMessages" :key="message.id" class="message-row">
                  <!-- Subject Column -->
                  <td class="subject-cell">
                    <div class="subject-content">
                      <strong class="subject-title">{{ message.subject || 'No Subject' }}</strong>
                      <div class="message-meta">
                        <span class="message-date">{{ formatMessageDate(message.date) }}</span>
                        <span class="message-status" :class="message.status">{{ message.status }}</span>
                      </div>
                    </div>
                  </td>
                  
                  <!-- From Column -->
                  <td class="from-cell">
                    <div class="participant-info">
                      <strong class="participant-name">{{ message.sender_details?.name || 'Unknown' }}</strong>
                      <span class="participant-email">{{ message.sender_details?.email }}</span>
                    </div>
                  </td>
                  
                  <!-- Description Column -->
                  <td class="description-cell">
                    <div class="description-content">
                      <p class="message-snippet">{{ message.snippet || 'No description available' }}</p>
                    </div>
                  </td>
                  
                  <!-- Attachments Column -->
                  <td class="attachments-cell">
                    <div class="attachments-info">
                      <span v-if="message.has_attachments" class="attachment-count">
                        📎 {{ message.attachment_count }}
                      </span>
                      <span v-else class="no-attachments">—</span>
                    </div>
                  </td>
                  
                  <!-- Download Column -->
                  <td class="download-cell">
                    <div class="download-actions">
                      <button 
                        v-if="message.has_attachments"
                        @click="downloadAllAttachments(message)"
                        class="download-all-btn"
                        :disabled="downloadingAttachments.includes(message.id)"
                      >
                        {{ downloadingAttachments.includes(message.id) ? '⏳' : '⬇️ All' }}
                      </button>
                      <span v-else class="no-download">—</span>
                    </div>
                  </td>
                  
                  <!-- Plus Symbol Column -->
                  <td class="plus-cell">
                    <button 
                      class="plus-btn" 
                      :class="{ 'saved': savedMessages.includes(message.id) }"
                      @click="toggleMessageDetails(message.id)"
                      :title="savedMessages.includes(message.id) ? 'Saved to integration list' : 'Click to expand and save'"
                    >
                      <span v-if="savedMessages.includes(message.id)">✓</span>
                      <span v-else-if="expandedMessages.includes(message.id)">−</span>
                      <span v-else>+</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
            
            <!-- Expanded Message Details -->
            <div v-for="message in gmailMessages" :key="`details-${message.id}`" v-show="expandedMessages.includes(message.id)" class="message-details">
              <div class="details-content">
                <!-- <h4 class="details-title">Message Details</h4> -->
                
                <!-- CC Information -->
                <div v-if="message.cc_details" class="details-section">
                  <h5>CC:</h5>
                  <div class="participant-info">
                    <strong>{{ message.cc_details.name }}</strong>
                    <span class="participant-email">{{ message.cc_details.email }}</span>
                  </div>
                </div>
                
                <!-- Attachments Details -->
                <div v-if="message.has_attachments && message.attachments" class="details-section">
                  <h5>📎 Attachments ({{ message.attachment_count }})</h5>
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
                        <button 
                          v-if="attachment.is_image"
                          @click="previewImage(attachment)"
                          class="preview-btn"
                        >
                          👁️
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Calendar Tab Content -->
        <div v-if="activeTab === 'calendar'" class="tab-panel">
          <div class="panel-header">
            <h3>📅 Recent Calendar Events</h3>
            <button @click="fetchCalendarEvents" :disabled="calendarLoading" class="refresh-btn">
              {{ calendarLoading ? 'Loading...' : 'Refresh' }}
            </button>
          </div>
          
          <div v-if="calendarLoading" class="loading-state">
            <div class="spinner"></div>
            <p>Loading your events...</p>
          </div>
          
          <div v-else-if="calendarError" class="error-state">
            <p>❌ {{ calendarError }}</p>
            <button @click="fetchCalendarEvents" class="retry-btn">Try Again</button>
          </div>
          
          <div v-else-if="calendarEvents.length === 0" class="empty-state">
            <p>No calendar events found</p>
          </div>
          
          <div v-else class="messages-table-container">
            <table class="messages-table calendar-table">
              <thead>
                <tr>
                  <th class="event-title-column">Event Title</th>
                  <th class="event-time-column">Start Time</th>
                  <th class="event-time-column">End Time</th>
                  <th class="event-location-column">Location</th>
                  <th class="event-organizer-column">Organizer</th>
                  <th class="event-attendees-column">Attendees</th>
                  <th class="event-status-column">Status</th>
                  <th class="event-actions-column">Actions</th>
                  <th class="plus-column">+</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="event in calendarEvents" :key="event.id" class="message-row calendar-row">
                  <!-- Event Title Column -->
                  <td class="event-title-cell">
                    <div class="event-title-content">
                      <strong class="event-title-text">{{ event.title || 'No Title' }}</strong>
                    </div>
                  </td>
                  
                  <!-- Start Time Column -->
                  <td class="event-time-cell">
                    <div class="time-badge start-time">
                      {{ formatDateTime(event.start) }}
                    </div>
                  </td>
                  
                  <!-- End Time Column -->
                  <td class="event-time-cell">
                    <div v-if="event.end" class="time-badge end-time">
                      {{ formatDateTime(event.end) }}
                    </div>
                    <span v-else class="no-data">—</span>
                  </td>
                  
                  <!-- Location Column -->
                  <td class="event-location-cell">
                    <div v-if="event.location" class="location-info">
                      <span class="location-icon">📍</span>
                      <span class="location-text">{{ event.location }}</span>
                    </div>
                    <span v-else class="no-data">—</span>
                  </td>
                  
                  <!-- Organizer Column -->
                  <td class="event-organizer-cell">
                    <div v-if="event.organizer" class="organizer-info">
                      <strong class="organizer-name">{{ event.organizer.displayName || 'Organizer' }}</strong>
                      <span v-if="event.organizer.email" class="organizer-email">{{ event.organizer.email }}</span>
                    </div>
                    <span v-else class="no-data">—</span>
                  </td>
                  
                  <!-- Attendees Column -->
                  <td class="event-attendees-cell">
                    <div v-if="event.attendees && event.attendees.length > 0" class="attendees-count">
                      👥 {{ event.attendees.length }}
                    </div>
                    <span v-else class="no-data">—</span>
                  </td>
                  
                  <!-- Status Column -->
                  <td class="event-status-cell">
                    <span v-if="event.status" class="event-status-badge" :class="event.status">
                      {{ event.status }}
                    </span>
                    <span v-else class="no-data">—</span>
                  </td>
                  
                  <!-- Actions Column -->
                  <td class="event-actions-cell">
                    <a v-if="event.htmlLink" :href="event.htmlLink" target="_blank" class="view-calendar-btn" title="View in Google Calendar">
                      🔗
                    </a>
                    <span v-else class="no-data">—</span>
                  </td>
                  
                  <!-- Plus Symbol Column -->
                  <td class="plus-cell">
                    <button 
                      class="plus-btn" 
                      :class="{ 'saved': savedEvents.includes(event.id) }"
                      @click="toggleEventDetails(event.id)"
                      :title="savedEvents.includes(event.id) ? 'Saved to integration list' : 'Click to save'"
                    >
                      <span v-if="savedEvents.includes(event.id)">✓</span>
                      <span v-else>+</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>

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
  name: 'GmailIntegration',
  data() {
    return {
      userInfo: null,
      gmailMessages: [],
      calendarEvents: [],
      gmailLoading: false,
      calendarLoading: false,
      gmailError: '',
      calendarError: '',
      connected: false,
      activeTab: 'gmail', // Default to Gmail tab
      downloadingAttachments: [], // Track which attachments are being downloaded
      imagePreview: null, // For image preview modal
      expandedMessages: [], // Track which messages are expanded
      savedMessages: [], // Track which messages have been saved to integration_data_list
      savedEvents: [] // Track which events have been saved to integration_data_list
    }
  },
  async mounted() {
    // Check URL parameters for OAuth success or stored data loading
    const urlParams = new URLSearchParams(window.location.search)
    const oauthSuccess = urlParams.get('oauth_success')
    const loadStoredData = urlParams.get('loadStoredData')
    
    // Show success message if OAuth was successful
    if (oauthSuccess === 'true') {
      console.log('✅ Gmail OAuth connection successful!')
      // Wait a moment for the connection to be fully saved to database
      await new Promise(resolve => setTimeout(resolve, 2000))
    }
    
    await this.checkConnectionStatus()
    
    if (this.connected) {
      if (loadStoredData === 'true') {
        // Load stored data from database
        await this.loadStoredData()
      } else {
        // Fetch fresh data from Gmail API
        await Promise.all([
          this.fetchGmailMessages(),
          this.fetchCalendarEvents()
        ])
      }
    }
    
    // Clean up URL parameters
    if (oauthSuccess || loadStoredData) {
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  },
  methods: {
    parseEmailField(emailField) {
      // Handle empty or default values
      if (!emailField || emailField === 'Unknown Sender' || emailField === 'Unknown Recipient') {
        return {
          email: 'unknown@example.com',
          name: 'Unknown',
          domain: 'example.com'
        }
      }
      
      // Pattern to match various email formats:
      // 1. "Name" <email@domain.com>
      // 2. Name <email@domain.com>
      // 3. email@domain.com
      // 4. "Name" email@domain.com
      const emailPattern = /(?:"?([^"<>]+)"?\s*)?<?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>?/
      
      const match = emailField.match(emailPattern)
      if (match) {
        const namePart = match[1] ? match[1].trim() : ''
        const email = match[2].trim()
        const domain = email.split('@')[1] || ''
        
        // Clean up name (remove quotes and extra whitespace)
        let name = namePart.replace(/"/g, '').trim()
        
        // If name is empty or just whitespace, use email prefix
        if (!name) {
          name = email.split('@')[0]
        }
        
        return {
          email: email,
          name: name,
          domain: domain
        }
      }
      
      // Fallback for malformed email - try to extract just the email part
      const emailOnlyPattern = /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/
      const emailMatch = emailField.match(emailOnlyPattern)
      
      if (emailMatch) {
        const email = emailMatch[1]
        const domain = email.split('@')[1]
        return {
          email: email,
          name: email.split('@')[0],
          domain: domain
        }
      }
      
      // Final fallback
      return {
        email: emailField,
        name: emailField,
        domain: 'unknown'
      }
    },

    async checkConnectionStatus() {
      try {
        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
        const urlParams = new URLSearchParams(window.location.search)
        const oauthSuccess = urlParams.get('oauth_success')
        
        // If OAuth was successful, retry connection check up to 3 times
        let maxRetries = oauthSuccess === 'true' ? 3 : 1
        let retryCount = 0
        
        while (retryCount < maxRetries) {
          try {
            const response = await axios.get(`${API_BASE_URL}/api/gmail/connection-status/`, {
              params: { user_id: userId },
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token') || sessionStorage.getItem('access_token')}`
              }
            })
            
            if (response.data.success && response.data.connected) {
              this.connected = true
              this.userInfo = response.data.user_info || { name: 'Gmail User' }
              return // Success, exit the method
            }
          } catch (error) {
            console.warn(`Connection check attempt ${retryCount + 1} failed:`, error)
          }
          
          retryCount++
          if (retryCount < maxRetries) {
            // Wait 1 second before retrying
            await new Promise(resolve => setTimeout(resolve, 1000))
          }
        }
        
        // If we get here, connection check failed
        this.connected = false
        console.error('Connection check failed after all retries')
        
        // Only redirect if OAuth was not successful
        if (oauthSuccess !== 'true') {
          this.$router.push('/integrations/external')
        }
        
      } catch (error) {
        console.error('Connection check failed:', error)
        this.connected = false
        
        // Only redirect if OAuth was not successful
        const urlParams = new URLSearchParams(window.location.search)
        const oauthSuccess = urlParams.get('oauth_success')
        if (oauthSuccess !== 'true') {
          this.$router.push('/integrations/external')
        }
      }
    },

    async fetchGmailMessages() {
      this.gmailLoading = true
      this.gmailError = ''
      
      try {
        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
        const response = await axios.get(`${API_BASE_URL}/api/gmail/messages/`, {
          params: { user_id: userId },
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token') || sessionStorage.getItem('access_token')}`
          }
        })
        
        if (response.data.success) {
          // Parse the messages to add structured sender/receiver details
          this.gmailMessages = response.data.messages.map(msg => {
            // Parse sender and receiver details
            const senderDetails = this.parseEmailField(msg.from)
            const receiverDetails = this.parseEmailField(msg.to)
            const ccDetails = msg.cc ? this.parseEmailField(msg.cc) : null
            const bccDetails = msg.bcc ? this.parseEmailField(msg.bcc) : null
            
            return {
              ...msg,
              sender_details: senderDetails,
              receiver_details: receiverDetails,
              cc_details: ccDetails,
              bcc_details: bccDetails
            }
          })
          
          // Show success message that data has been automatically saved
          console.log(`✅ Successfully fetched ${this.gmailMessages.length} Gmail messages`)
          
          // Check if auto-save was successful
          if (response.data.auto_saved) {
            console.log(`✅ Messages automatically saved to database`)
            // Optional: Show a toast notification if available
            if (this.$toast) {
              this.$toast.success(`✅ Fetched and saved ${this.gmailMessages.length} messages to database`)
            }
          } else {
            console.warn(`⚠️ Messages fetched but auto-save failed: ${response.data.save_message}`)
            // Optional: Show a warning notification if available
            if (this.$toast) {
              this.$toast.warning(`⚠️ Messages fetched but auto-save failed`)
            }
          }
        } else {
          this.gmailError = response.data.error || 'Failed to fetch Gmail messages'
        }
      } catch (error) {
        this.gmailError = error.response?.data?.error || 'Failed to fetch Gmail messages'
        console.error('Gmail fetch error:', error)
      } finally {
        this.gmailLoading = false
      }
    },

    async fetchCalendarEvents() {
      this.calendarLoading = true
      this.calendarError = ''
      
      try {
        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
        console.log('Fetching calendar events for user:', userId)
        
        const response = await axios.get(`${API_BASE_URL}/api/gmail/calendar-events/`, {
          params: { user_id: userId },
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token') || sessionStorage.getItem('access_token')}`
          }
        })
        
        console.log('Calendar events response:', response.data)
        
        if (response.data.success) {
          this.calendarEvents = response.data.events || []
          console.log(`✅ Successfully fetched ${this.calendarEvents.length} calendar events`)
          
          // Show success message if toast is available
          if (this.$toast && this.calendarEvents.length > 0) {
            this.$toast.success(`Fetched ${this.calendarEvents.length} calendar events`)
          } else if (this.$toast && this.calendarEvents.length === 0) {
            this.$toast.info('No calendar events found in the selected time range')
          }
        } else {
          this.calendarError = response.data.error || 'Failed to fetch calendar events'
          console.error('Calendar fetch failed:', this.calendarError)
          
          // Show specific error messages
          if (response.data.error_type === 'permission_denied') {
            this.calendarError = 'Calendar access not granted. Please reconnect your Gmail account and allow calendar access.'
          }
        }
      } catch (error) {
        const errorMsg = error.response?.data?.error || 'Failed to fetch calendar events'
        this.calendarError = errorMsg
        console.error('Calendar fetch error:', error)
        console.error('Error details:', error.response?.data)
        
        // Show user-friendly error message
        if (this.$toast) {
          if (error.response?.status === 403) {
            this.$toast.error('Calendar permissions not granted. Please reconnect.')
          } else if (error.response?.status === 401) {
            this.$toast.error('Session expired. Please reconnect Gmail.')
          } else {
            this.$toast.error('Failed to fetch calendar events')
          }
        }
      } finally {
        this.calendarLoading = false
      }
    },

    formatDateTime(dateTime) {
      if (!dateTime) return 'No time specified'
      
      const date = new Date(dateTime)
      const now = new Date()
      const diffTime = date - now
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      
      // Format time
      const timeStr = date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      })
      
      // Past events
      if (diffDays < 0) {
        const daysPast = Math.abs(diffDays)
        if (daysPast === 0 || daysPast === 1) {
          return 'Yesterday at ' + timeStr
        } else if (daysPast < 7) {
          return `${daysPast} days ago at ${timeStr}`
        } else {
          return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
          }) + ' at ' + timeStr
        }
      }
      
      // Future events
      if (diffDays === 0) {
        return 'Today at ' + timeStr
      } else if (diffDays === 1) {
        return 'Tomorrow at ' + timeStr
      } else if (diffDays < 7) {
        // Show day of week for upcoming week
        const dayName = date.toLocaleDateString('en-US', { weekday: 'long' })
        return `${dayName} at ${timeStr}`
      } else if (diffDays < 30) {
        return date.toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric' 
        }) + ' at ' + timeStr
      } else {
        return date.toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric', 
          year: 'numeric' 
        }) + ' at ' + timeStr
      }
    },

    formatMessageDate(dateTime) {
      if (!dateTime) return 'No date'
      
      const date = new Date(dateTime)
      const now = new Date()
      const diffTime = now - date
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
      
      if (diffDays === 0) {
        return 'Today'
      } else if (diffDays === 1) {
        return 'Yesterday'
      } else if (diffDays < 7) {
        return `${diffDays} days ago`
      } else {
        return date.toLocaleDateString()
      }
    },

    formatFileSize(bytes) {
      if (!bytes) return '0 B'
      
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(1024))
      return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
    },

    async downloadAttachment(messageId, attachmentId, filename) {
      try {
        // Add to downloading list
        this.downloadingAttachments.push(attachmentId)
        
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
          // Convert base64 data to blob
          const byteCharacters = atob(response.data.data)
          const byteNumbers = new Array(byteCharacters.length)
          for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i)
          }
          const byteArray = new Uint8Array(byteNumbers)
          const blob = new Blob([byteArray], { type: response.data.mime_type })
          
          // Create download link
          const url = window.URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = filename
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          window.URL.revokeObjectURL(url)
          
          this.$toast.success(`Downloaded ${filename}`)
        } else {
          this.$toast.error(response.data.error || 'Failed to download attachment')
        }
      } catch (error) {
        console.error('Download error:', error)
        this.$toast.error('Failed to download attachment')
      } finally {
        // Remove from downloading list
        this.downloadingAttachments = this.downloadingAttachments.filter(id => id !== attachmentId)
      }
    },

    previewImage(attachment) {
      if (attachment.is_image && attachment.data) {
        this.imagePreview = {
          filename: attachment.filename,
          data: `data:${attachment.mime_type};base64,${attachment.data}`,
          size: attachment.size
        }
      }
    },

    closeImagePreview() {
      this.imagePreview = null
    },

    async toggleMessageDetails(messageId) {
      const index = this.expandedMessages.indexOf(messageId)
      if (index > -1) {
        this.expandedMessages.splice(index, 1)
      } else {
        this.expandedMessages.push(messageId)
        
        // Save the message data to integration_data_list table when expanding (clicking plus button)
        await this.saveMessageToIntegrationList(messageId)
      }
    },

    async saveMessageToIntegrationList(messageId) {
      try {
        // Find the message data
        const message = this.gmailMessages.find(msg => msg.id === messageId)
        
        if (!message) {
          console.error('Message not found:', messageId)
          return
        }

        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
        
        // Prepare the complete message data to send
        const messageData = {
          id: message.id,
          subject: message.subject || 'No Subject',
          from: message.from,
          to: message.to,
          cc: message.cc || '',
          bcc: message.bcc || '',
          date: message.date,
          snippet: message.snippet,
          has_attachments: message.has_attachments || false,
          attachment_count: message.attachment_count || 0,
          attachments: message.attachments || [],
          sender_details: message.sender_details,
          receiver_details: message.receiver_details,
          cc_details: message.cc_details,
          bcc_details: message.bcc_details,
          extracted_at: message.extracted_at || new Date().toISOString(),
          message_index: message.message_index,
          status: message.status || 'unread',
          priority: message.priority || 'normal'
        }

        // Send to backend
        const response = await axios.post(`${API_BASE_URL}/api/gmail/save-message-to-integration/`, {
          user_id: userId,
          message_data: messageData
        }, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token') || sessionStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.data.success) {
          console.log(`✅ Gmail message saved to integration_data_list (ID: ${response.data.integration_id})`)
          
          // Mark message as saved
          if (!this.savedMessages.includes(messageId)) {
            this.savedMessages.push(messageId)
          }
          
          // Show success notification if toast is available
          if (this.$toast) {
            this.$toast.success(`Message "${response.data.heading}" saved to integration list`)
          }
        } else {
          console.error('Failed to save message:', response.data.error)
          if (this.$toast) {
            this.$toast.error('Failed to save message to integration list')
          }
        }
      } catch (error) {
        console.error('Error saving message to integration list:', error)
        if (this.$toast) {
          this.$toast.error('Error saving message to integration list')
        }
      }
    },

    async downloadAllAttachments(message) {
      if (!message.has_attachments || !message.attachments) {
        return
      }

      // Add message ID to downloading list
      this.downloadingAttachments.push(message.id)

      try {
        // Download all attachments sequentially
        for (const attachment of message.attachments) {
          await this.downloadAttachment(message.id, attachment.id, attachment.filename)
          // Small delay between downloads
          await new Promise(resolve => setTimeout(resolve, 500))
        }
        
        if (this.$toast) {
          this.$toast.success(`Downloaded ${message.attachments.length} attachments`)
        }
      } catch (error) {
        console.error('Error downloading attachments:', error)
        if (this.$toast) {
          this.$toast.error('Failed to download some attachments')
        }
      } finally {
        // Remove from downloading list
        this.downloadingAttachments = this.downloadingAttachments.filter(id => id !== message.id)
      }
    },

    goBack() {
      this.$router.push('/integrations/gmail/connect')
    },

    async loadStoredData() {
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
              from: msg.sender?.full_address || msg.from || 'Unknown Sender',
              to: msg.receiver?.full_address || 'Unknown Recipient',
              cc: msg.cc?.full_address || '',
              bcc: msg.bcc?.full_address || '',
              date: msg.date,
              snippet: msg.message_content || msg.snippet,
              has_attachments: msg.has_attachments,
              attachment_count: msg.attachment_count,
              
              // Include structured sender/receiver details for display
              sender_details: {
                email: msg.sender?.email || 'unknown@example.com',
                name: msg.sender?.name || 'Unknown',
                domain: msg.sender?.domain || 'unknown'
              },
              receiver_details: {
                email: msg.receiver?.email || 'unknown@example.com',
                name: msg.receiver?.name || 'Unknown',
                domain: msg.receiver?.domain || 'unknown'
              },
              cc_details: msg.cc ? {
                email: msg.cc.email,
                name: msg.cc.name,
                domain: msg.cc.domain
              } : null,
              bcc_details: msg.bcc ? {
                email: msg.bcc.email,
                name: msg.bcc.name,
                domain: msg.bcc.domain
              } : null,
              
              attachments: msg.attachments.map(att => ({
                id: att.gmail_attachment_id || att.attachment_id,
                filename: att.filename,
                mime_type: att.mime_type,
                size: att.size,
                file_extension: att.file_extension,
                file_type: att.file_type,
                is_image: att.is_image,
                is_pdf: att.is_pdf,
                is_document: att.is_document,
                data: att.data,
                upload_date: att.upload_date,
                status: att.status
              })),
              
              // Include metadata
              extracted_at: msg.extracted_at,
              message_index: msg.message_index,
              status: msg.status,
              priority: msg.priority
            }))
            console.log(`Loaded ${this.gmailMessages.length} structured Gmail messages with metadata:`, structuredData.metadata)
          }
          // Note: Calendar events are not currently stored, so we'll fetch them fresh
          await this.fetchCalendarEvents()
        } else {
          console.log('No stored data found, fetching fresh data')
          await Promise.all([
            this.fetchGmailMessages(),
            this.fetchCalendarEvents()
          ])
        }
      } catch (error) {
        console.error('Error loading stored data:', error)
        // Fallback to fetching fresh data
        await Promise.all([
          this.fetchGmailMessages(),
          this.fetchCalendarEvents()
        ])
      }
    },

    toggleEventDetails(eventId) {
      // Check if already saved
      if (!this.savedEvents.includes(eventId)) {
        // Save the event to integration_data_list when clicking +
        this.saveEventToIntegrationList(eventId)
      }
    },

    async saveEventToIntegrationList(eventId) {
      try {
        // Find the event data
        const event = this.calendarEvents.find(evt => evt.id === eventId)
        
        if (!event) {
          console.error('Event not found:', eventId)
          return
        }

        const userId = localStorage.getItem('user_id') || sessionStorage.getItem('user_id') || 1
        
        // Prepare the event data to send
        const eventData = {
          id: event.id,
          title: event.title || 'No Title',
          start: event.start,
          end: event.end,
          location: event.location || '',
          description: event.description || '',
          status: event.status || '',
          htmlLink: event.htmlLink || '',
          created: event.created || '',
          updated: event.updated || '',
          organizer: event.organizer || {},
          creator: event.creator || {},
          attendees: event.attendees || [],
          extracted_at: new Date().toISOString()
        }

        // Send to backend (we'll create a new endpoint for this)
        const response = await axios.post(`${API_BASE_URL}/api/gmail/save-event-to-integration/`, {
          user_id: userId,
          event_data: eventData
        }, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token') || sessionStorage.getItem('access_token')}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.data.success) {
          console.log(`✅ Calendar event saved to integration_data_list (ID: ${response.data.integration_id})`)
          
          // Mark event as saved
          if (!this.savedEvents.includes(eventId)) {
            this.savedEvents.push(eventId)
          }
          
          // Show success notification if toast is available
          if (this.$toast) {
            this.$toast.success(`Event "${response.data.heading}" saved to integration list`)
          }
        } else {
          console.error('Failed to save event:', response.data.error)
          if (this.$toast) {
            this.$toast.error('Failed to save event to integration list')
          }
        }
      } catch (error) {
        console.error('Error saving event to integration list:', error)
        if (this.$toast) {
          this.$toast.error('Error saving event to integration list')
        }
      }
    },

    formatEventTimestamp(timestamp) {
      if (!timestamp) return 'Unknown'
      
      const date = new Date(timestamp)
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      })
    }

  }
}
</script>

<style scoped>
.gmail-integration {
  min-height: calc(100vh - 100px); /* Account for navbar and padding */
  background: #f8f9fa;
  margin-left: 220px; /* Account for sidebar width */
  margin-right: 0;
  margin-top:-60px; /* Add space below navbar */
  margin-bottom: 0;
  padding: 20px;
  box-sizing: border-box;
  width: calc(100vw - 280px); /* Full width minus sidebar */
}

/* Tab Navigation Styles */
.tab-navigation {
  display: flex;
  background: white;
  border-radius: 12px;
  padding: 8px;
  margin-bottom: 30px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.tab-btn {
  flex: 1;
  background: transparent;
  color: #666;
  border: none;
  padding: 15px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.tab-btn:hover {
  background: #f8f9fa;
  color: #333;
}

.tab-btn.active {
  background: #4285F4;
  color: white;
  box-shadow: 0 2px 8px rgba(66, 133, 244, 0.3);
}

.count-badge {
  background: #e74c3c;
  color: white;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 12px;
  margin-left: 8px;
  min-width: 20px;
  text-align: center;
  line-height: 1;
}

.tab-btn.active .count-badge {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

/* Tab Content Styles */
.tab-content {
  background: white;
  border-radius: 15px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.tab-panel {
  min-height: 500px;
}

.panel-header {
  background: #f8f9fa;
  padding: 20px 25px;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.auto-save-indicator {
  font-size: 12px;
  color: #28a745;
  font-weight: 500;
  background: #d4edda;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #c3e6cb;
  display: inline-block;
  width: fit-content;
}

.panel-header h3 {
  color: #333;
  font-size: 20px;
  margin: 0;
}

.integration-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
  width: 100%;
}

.back-section {
  margin-bottom: 30px;
}

.back-button {
  background: #6c757d;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.back-button:hover {
  background: #5a6268;
  transform: translateY(-1px);
}

.back-button i {
  font-size: 12px;
}

.welcome-section {
  text-align: center;
  margin-bottom: 40px;
  color: #333;
}

.welcome-section h2 {
  font-size: 32px;
  margin-bottom: 10px;
  color: #333;
}

.welcome-section p {
  font-size: 18px;
  color: #666;
}

/* Messages Table Styles */
.messages-table-container {
  overflow-x: auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.messages-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.messages-table thead {
  background: #f8f9fa;
  border-bottom: 2px solid #e9ecef;
}

.messages-table th {
  padding: 15px 12px;
  text-align: left;
  font-weight: 600;
  color: #495057;
  border-bottom: 2px solid #e9ecef;
  white-space: nowrap;
}

.messages-table td {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: top;
}

.message-row:hover {
  background: #f8f9fa;
}

.message-row:last-child td {
  border-bottom: none;
}

/* Column Widths */
.plus-column {
  width: 50px;
  text-align: center;
}

.subject-column {
  width: 30%;
  min-width: 200px;
}

.from-column {
  width: 25%;
  min-width: 150px;
}

.description-column {
  width: 30%;
  min-width: 200px;
}

.attachments-column {
  width: 80px;
  text-align: center;
}

.download-column {
  width: 100px;
  text-align: center;
}

/* Plus Button */
.plus-btn {
  background: #4285F4;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  transition: all 0.2s ease;
}

.plus-btn:hover {
  background: #3367d6;
  transform: scale(1.1);
}

.plus-btn.saved {
  background: #28a745;
  animation: pulse 0.5s ease-in-out;
}

.plus-btn.saved:hover {
  background: #218838;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}

/* Subject Cell */
.subject-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.subject-title {
  color: #333;
  font-size: 14px;
  line-height: 1.3;
  margin: 0;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.message-date {
  color: #666;
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
}

.message-status {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
}

.message-status.unread {
  background: #e3f2fd;
  color: #1976d2;
}

.message-status.read {
  background: #f3e5f5;
  color: #7b1fa2;
}

/* Participant Info */
.participant-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.participant-name {
  color: #333;
  font-size: 13px;
  font-weight: 600;
}

.participant-email {
  color: #666;
  font-size: 12px;
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
  display: inline-block;
}

/* Description Cell */
.description-content {
  max-width: 100%;
}

.message-snippet {
  color: #666;
  font-size: 13px;
  line-height: 1.4;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Attachments Cell */
.attachments-info {
  text-align: center;
}

.attachment-count {
  color: #1976d2;
  font-weight: 600;
  font-size: 13px;
}

.no-attachments {
  color: #999;
  font-size: 12px;
}

/* Download Cell */
.download-actions {
  text-align: center;
}

.download-all-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: background 0.2s ease;
}

.download-all-btn:hover:not(:disabled) {
  background: #218838;
}

.download-all-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.no-download {
  color: #999;
  font-size: 12px;
}

/* Message Details (Expanded) */
.message-details {
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
  padding: 20px;
  margin: 0;
}

.details-content {
  max-width: 100%;
}

.details-title {
  color: #333;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 15px 0;
}

.details-section {
  margin-bottom: 15px;
}

.details-section h5 {
  color: #495057;
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.list-item {
  padding: 20px 25px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s ease;
}

.list-item:hover {
  background: #f8f9fa;
}

.list-item:last-child {
  border-bottom: none;
}

.item-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 10px;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-title {
  color: #333;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 5px 0;
  line-height: 1.3;
  text-align: left;
}

.item-subtitle {
  color: #666;
  font-size: 14px;
  margin: 0;
  font-weight: 500;
  text-align: left;
}

.message-participants {
  margin-top: 8px;
}

.participant-row {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
  font-size: 13px;
}

.participant-label {
  color: #888;
  font-weight: 500;
  min-width: 40px;
  margin-right: 8px;
}

.participant-details {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.participant-details strong {
  color: #333;
  font-weight: 600;
}

.participant-email {
  color: #666;
  font-size: 12px;
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
}

.message-status {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
  margin-top: 4px;
}

.message-status.unread {
  background: #e3f2fd;
  color: #1976d2;
}

.message-status.read {
  background: #f3e5f5;
  color: #7b1fa2;
}

.item-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  min-width: 100px;
}

.item-date {
  color: #888;
  font-size: 12px;
  font-weight: 500;
  background: #f0f0f0;
  padding: 4px 8px;
  border-radius: 4px;
}

.item-content {
  margin-left: 0; /* Remove left margin since no icon */
  text-align: left;
}

.item-description {
  color: #666;
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
}

.refresh-btn {
  background: #4285F4;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s ease;
}

.refresh-btn:hover:not(:disabled) {
  background: #3367d6;
}

.refresh-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}


.loading-state, .error-state, .empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #4285F4;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-state {
  color: #e74c3c;
}

.retry-btn {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 10px;
}

.retry-btn:hover {
  background: #c0392b;
}

/* Attachment Styles */
.attachment-indicator {
  background: #e3f2fd;
  color: #1976d2;
  font-size: 11px;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: 8px;
}

.attachments-section {
  margin-top: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.attachments-title {
  color: #333;
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.attachments-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attachment-item {
  display: flex;
  align-items: center;
  padding: 10px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
  transition: all 0.2s ease;
}

.attachment-item:hover {
  border-color: #4285F4;
  box-shadow: 0 2px 8px rgba(66, 133, 244, 0.1);
}

.attachment-icon {
  font-size: 20px;
  margin-right: 12px;
  min-width: 24px;
}

.attachment-info {
  flex: 1;
  min-width: 0;
}

.attachment-name {
  font-weight: 500;
  color: #333;
  font-size: 14px;
  margin-bottom: 2px;
  word-break: break-word;
}

.attachment-details {
  font-size: 12px;
  color: #666;
}

.attachment-actions {
  display: flex;
  gap: 6px;
  margin-left: 12px;
}

.download-btn, .preview-btn {
  background: #4285F4;
  color: white;
  border: none;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.2s ease;
  min-width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.download-btn:hover:not(:disabled) {
  background: #3367d6;
}

.preview-btn {
  background: #34a853;
}

.preview-btn:hover {
  background: #2d8f47;
}

.download-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 90vw;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #e0e0e0;
  background: #f8f9fa;
}

.modal-header h3 {
  margin: 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #666;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.2s ease;
}

.close-btn:hover {
  background: #e0e0e0;
}

.modal-body {
  padding: 20px;
  text-align: center;
}

.preview-image {
  max-width: 100%;
  max-height: 60vh;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.image-info {
  margin-top: 15px;
  color: #666;
  font-size: 14px;
}

/* Calendar Table Specific Styles */
.calendar-table {
  background: white;
}

.calendar-row {
  border-left: 3px solid #4285F4;
}

.calendar-row:hover {
  background: #f8f9fa;
}

/* Calendar Table Column Widths */
.event-title-column {
  width: 20%;
  min-width: 180px;
}

.event-time-column {
  width: 15%;
  min-width: 140px;
}

.event-location-column {
  width: 15%;
  min-width: 120px;
}

.event-organizer-column {
  width: 15%;
  min-width: 150px;
}

.event-attendees-column {
  width: 10%;
  min-width: 80px;
  text-align: center;
}

.event-status-column {
  width: 10%;
  min-width: 80px;
  text-align: center;
}

.event-actions-column {
  width: 10%;
  min-width: 60px;
  text-align: center;
}

/* Calendar Table Cell Styles */
.event-title-cell {
  padding: 12px;
}

.event-title-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.event-title-text {
  color: #333;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.3;
}

.event-time-cell {
  padding: 12px;
  vertical-align: middle;
}

.time-badge {
  display: inline-block;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.time-badge.start-time {
  background: #e3f2fd;
  color: #1976d2;
  border: 1px solid #bbdefb;
}

.time-badge.end-time {
  background: #f3e5f5;
  color: #7b1fa2;
  border: 1px solid #e1bee7;
}

.event-location-cell {
  padding: 12px;
  max-width: 200px;
  word-wrap: break-word;
}

.location-info {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  max-width: 100%;
}

.location-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.location-text {
  font-size: 13px;
  color: #666;
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: break-word;
  white-space: normal;
  line-height: 1.4;
}

.event-organizer-cell {
  padding: 12px;
}

.organizer-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.organizer-name {
  font-size: 13px;
  color: #333;
  font-weight: 600;
}

.organizer-email {
  font-size: 11px;
  color: #666;
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.event-attendees-cell {
  padding: 12px;
  text-align: center;
}

.attendees-count {
  font-size: 13px;
  color: #1976d2;
  font-weight: 600;
}

.event-status-cell {
  padding: 12px;
  text-align: center;
}

.event-status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: capitalize;
}

.event-status-badge.confirmed {
  background: #d4edda;
  color: #155724;
}

.event-status-badge.tentative {
  background: #fff3cd;
  color: #856404;
}

.event-status-badge.cancelled {
  background: #f8d7da;
  color: #721c24;
  text-decoration: line-through;
}

.event-actions-cell {
  padding: 12px;
  text-align: center;
}

.view-calendar-btn {
  display: inline-block;
  font-size: 18px;
  text-decoration: none;
  color: #4285F4;
  transition: all 0.2s ease;
  padding: 4px;
}

.view-calendar-btn:hover {
  transform: scale(1.2);
  color: #3367d6;
}

.no-data {
  color: #999;
  font-size: 12px;
}

/* Expanded Event Details Styles */
.event-details {
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
  padding: 20px;
}

.event-description-text {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
  padding: 10px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.no-description {
  color: #999;
  font-style: italic;
  padding: 10px;
}

.attendees-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 10px;
  margin-top: 10px;
}

.attendee-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.attendee-info-detailed {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
  min-width: 0;
}

.attendee-info-detailed strong {
  color: #333;
  font-size: 13px;
  font-weight: 600;
}

.attendee-email-detailed {
  color: #666;
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attendee-status {
  flex-shrink: 0;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.status-badge.accepted {
  background: #d4edda;
  color: #155724;
}

.status-badge.declined {
  background: #f8d7da;
  color: #721c24;
}

.status-badge.tentative {
  background: #fff3cd;
  color: #856404;
}

.status-badge.pending {
  background: #e7e7e7;
  color: #666;
}

.event-metadata-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
  margin-top: 10px;
}

.metadata-item {
  padding: 10px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e9ecef;
  font-size: 13px;
  color: #666;
}

.metadata-item strong {
  color: #333;
  margin-right: 6px;
}

/* Remove old message/event styles as they're replaced by detailed-list styles */

@media (max-width: 768px) {
  .gmail-integration {
    margin-left: 0; /* Remove sidebar margin on mobile */
    margin-top: 80px; /* Ensure proper spacing on mobile */
    width: 100vw; /* Full width on mobile */
    padding: 10px;
  }
  
  .back-section {
    margin-bottom: 20px;
  }
  
  .back-button {
    padding: 8px 16px;
    font-size: 13px;
  }
  
  .tab-navigation {
    flex-direction: column;
    gap: 8px;
  }
  
  .tab-btn {
    padding: 12px 16px;
    font-size: 14px;
  }
  
  .count-badge {
    font-size: 11px;
    padding: 3px 6px;
    margin-left: 6px;
  }
  
  .item-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .item-meta {
    align-items: flex-start;
  }
  
  .item-content {
    margin-left: 0;
  }
  
  .integration-main {
    padding: 20px 10px;
  }
  
  .panel-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .header-left {
    width: 100%;
  }
  
  .auto-save-indicator {
    margin-top: 5px;
  }
  
  /* Table responsive styles */
  .messages-table-container {
    overflow-x: scroll;
  }
  
  .messages-table {
    min-width: 800px;
    font-size: 12px;
  }
  
  .messages-table th,
  .messages-table td {
    padding: 8px 6px;
  }
  
  .subject-column,
  .from-column,
  .description-column {
    min-width: 120px;
  }
  
  .plus-btn {
    width: 20px;
    height: 20px;
    font-size: 12px;
  }
  
  .participant-email {
    font-size: 10px;
    padding: 1px 4px;
  }
  
  .message-snippet {
    font-size: 11px;
    -webkit-line-clamp: 1;
    line-clamp: 1;
  }
  
  .download-all-btn {
    padding: 4px 8px;
    font-size: 10px;
  }
  
  .message-details {
    padding: 15px;
  }
  
  .details-title {
    font-size: 14px;
  }
  
  .attachment-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .attachment-actions {
    margin-left: 0;
    align-self: flex-end;
  }
  
  .attachments-section {
    padding: 10px;
  }
  
  .modal-content {
    max-width: 95vw;
    max-height: 95vh;
  }
  
  .modal-header {
    padding: 10px 15px;
  }
  
  .modal-body {
    padding: 15px;
  }
  
  .preview-image {
    max-height: 50vh;
  }
}
</style>
