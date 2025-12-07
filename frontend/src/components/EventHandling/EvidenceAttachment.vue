<template>
  <div class="evidence-attachment-container">
    

    <div class="content-wrapper">
      <div class="attachment-section">
        <div class="section-header">
          <h2>Upload Evidence</h2>
          
        </div>

        <div class="upload-area">
          <!-- Initial Add Evidence Button -->
          <div v-if="!showOptions && !showUploadArea" class="upload-button-container">
            <button 
              class="attach-evidence-btn"
              @click="showEvidenceOptions"
              :disabled="uploading"
            >
              <i class="fas fa-paperclip"></i>
              Add an Evidence
            </button>
          </div>

          <!-- Evidence Options -->
          <div v-if="showOptions && !showUploadArea" class="evidence-options show">
            <h3>Choose Evidence Type</h3>
            <div class="options-container">
              <div class="option-card" @click="selectUploadOption">
                <div class="option-icon">
                  <i class="fas fa-upload"></i>
                </div>
                <h4>Upload an Evidence</h4>
                <p>Select from local system</p>
              </div>
              
              <div class="option-card" @click="selectLinkOption">
                <div class="option-icon">
                  <i class="fas fa-link"></i>
                </div>
                <h4>Link an Evidence</h4>
                <p>Search for evidence in  Riskavaire , integrations and document handling</p>
              </div>
            </div>
            
            <button class="back-btn" @click="goBack">
              <i class="fas fa-arrow-left"></i>
              Back
            </button>
          </div>

          <!-- Upload Area -->
          <div v-if="showUploadArea" class="file-upload-section show">
            <div class="upload-header">
              <h3>Upload Evidence Files</h3>
              <button class="back-btn small" @click="goBackToOptions">
                <i class="fas fa-arrow-left"></i>
                Back to Options
              </button>
            </div>
            
            <div class="upload-button-container">
              <button 
                class="select-files-btn"
                @click="triggerFileUpload"
                :disabled="uploading"
              >
                <i class="fas fa-folder-open"></i>
                {{ uploading ? 'Uploading...' : 'Select Files' }}
              </button>
              
              <input 
                ref="fileInput"
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.txt,.xlsx,.xls"
                @change="handleFileSelect"
                style="display: none;"
              />
            </div>

            <div class="file-info">
              <p class="supported-formats">
                <i class="fas fa-info-circle"></i>
                Supported formats: PDF, DOC, DOCX, JPG, PNG, TXT, XLSX, XLS
              </p>
              <p class="max-size">Maximum file size: 10MB per file</p>
            </div>
            
            <!-- Selected Files Display -->
            <div v-if="selectedFiles.length > 0" class="selected-files show">
              <h3>Selected Files ({{ selectedFiles.length }})</h3>
              <div class="file-list">
                <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
                  <div class="file-info-item">
                    <i class="fas fa-file"></i>
                    <div>
                      <div class="file-name">{{ file.name }}</div>
                      <div class="file-size">{{ formatFileSize(file.size) }}</div>
                    </div>
                  </div>
                  <button @click="removeFile(index)" class="remove-file-btn">
                    <i class="fas fa-times"></i>
                  </button>
                </div>
              </div>
              
              <div class="upload-actions">
                <button 
                  @click="uploadFiles" 
                  class="upload-btn"
                  :disabled="uploading || selectedFiles.length === 0"
                >
                  <i class="fas" :class="uploading ? 'fa-spinner fa-spin' : 'fa-upload'"></i>
                  {{ uploading ? 'Uploading...' : 'Upload Files' }}
                </button>
                <button 
                  @click="clearFiles" 
                  class="clear-btn"
                  :disabled="uploading"
                >
                  <i class="fas fa-trash"></i>
                  Clear All
                </button>
              </div>
            </div>
            
            <!-- Upload Progress -->
            <div v-if="uploading" class="upload-progress show">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
              </div>
              <p>Uploading files... {{ uploadProgress }}%</p>
            </div>
            
            <!-- Success Message -->
            <div v-if="uploadSuccess" class="success-message show">
              <i class="fas fa-check-circle"></i>
              Files uploaded successfully!
            </div>
          </div>

          <!-- Link Area (placeholder) -->
          <div v-if="showLinkArea" class="link-evidence-section show">
            <div class="link-header">
              <h3>Link Evidence</h3>
              <button class="back-btn small" @click="goBackToOptions">
                <i class="fas fa-arrow-left"></i>
                Back to Options
              </button>
            </div>
            
            <div class="search-container">
              <div class="search-input-container">
                <i class="fas fa-search"></i>
                <input 
                  type="text" 
                  placeholder="Search for evidence in  Riskavaire , integrations and document handling..."
                  class="search-input"
                  v-model="searchQuery"
                />
              </div>
              
              <div class="search-filters">
                <button 
                  @click="setActiveFilter('All')"
                  :class="['filter-btn', activeFilter === 'All' ? 'active' : '']"
                >
                  All
                </button>
                <button 
                  @click="setActiveFilter('Riskavaire')"
                  :class="['filter-btn', activeFilter === 'Riskavaire' ? 'active' : '']"
                >
                  Riskavaire
                </button>
                <button 
                  @click="setActiveFilter('Integrations')"
                  :class="['filter-btn', activeFilter === 'Integrations' ? 'active' : '']"
                >
                  Integrations
                </button>
                <button 
                  @click="setActiveFilter('Document Handling')"
                  :class="['filter-btn', activeFilter === 'Document Handling' ? 'active' : '']"
                >
                  Document Handling
                </button>
              </div>
              
              <div class="search-results">
                <!-- Loading State -->
                <div v-if="loadingEvents" class="loading-state">
                  <i class="fas fa-spinner fa-spin"></i>
                  <p>Loading events...</p>
                </div>
                
                <!-- Error State -->
                <div v-else-if="eventsError" class="error-state">
                  <i class="fas fa-exclamation-triangle"></i>
                  <p>{{ eventsError }}</p>
                  <button @click="fetchAllEvents" class="retry-btn">
                    <i class="fas fa-redo"></i>
                    Retry
                  </button>
                </div>
                
                <!-- No Results -->
                <div v-else-if="filteredEvents.length === 0" class="no-results-state">
                  <i class="fas fa-search"></i>
                  <p v-if="searchQuery.trim()">No events found matching your search.</p>
                  <p v-else-if="activeFilter === 'All'">No events available. Click on a filter to load events.</p>
                  <p v-else-if="activeFilter === 'Document Handling'">No document handling events found.</p>
                  <p v-else>No {{ activeFilter }} events found.</p>
                </div>
                
                <!-- Events List -->
                <div v-else class="events-list">
                  <div class="events-header">
                    <h4>{{ activeFilter }} Events ({{ filteredEvents.length }})</h4>
                    <button 
                      v-if="selectedEvents.length > 0"
                      @click="linkSelectedEvents"
                      class="link-selected-btn"
                    >
                      <i class="fas fa-link"></i>
                      Link {{ selectedEvents.length }} Event(s)
                    </button>
                  </div>
                  
                  <div class="event-items">
                    <div 
                      v-for="event in filteredEvents" 
                      :key="event.id"
                      :class="['event-item', isEventSelected(event) ? 'selected' : '']"
                      @click="selectEvent(event)"
                    >
                      <div class="event-checkbox">
                        <input 
                          type="checkbox" 
                          :checked="isEventSelected(event)"
                          @click.stop
                          @change="selectEvent(event)"
                        />
                      </div>
                      
                      <div class="event-content">
                        <div class="event-header-info">
                          <h5 class="event-title">{{ event.title }}</h5>
                          <span :class="[
                            'event-source', 
                            event.source === 'Jira' ? 'jira-source' : 
                            event.source === 'Document Handling System' ? 'document-source' : 
                            'riskavaire-source'
                          ]">
                            {{ event.source }}
                          </span>
                        </div>
                        
                        <div class="event-details">
                          <div class="event-meta">
                            <span class="event-framework">{{ event.framework }}</span>
                            <span class="event-separator">•</span>
                            <span class="event-timestamp">{{ event.timestamp }}</span>
                          </div>
                          
                          <p v-if="event.description" class="event-description">
                            {{ event.description.length > 100 ? event.description.substring(0, 100) + '...' : event.description }}
                          </p>
                          
                          <div class="event-status">
                            <span :class="['status-badge', 'status-' + (event.status || 'new').toLowerCase().replace(' ', '-')]">
                              {{ event.status || 'New' }}
                            </span>
                            <span v-if="event.priority" :class="['priority-badge', 'priority-' + (event.priority || 'medium').toLowerCase()]">
                              {{ event.priority }}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Selected Files Display -->
        <div v-if="selectedFiles.length > 0" class="selected-files show">
          <h3>Selected Files</h3>
          <div class="file-list">
            <div 
              v-for="(file, index) in selectedFiles" 
              :key="index"
              class="file-item"
            >
              <div class="file-info-item">
                <i class="fas fa-file"></i>
                <span class="file-name">{{ file.name }}</span>
                <span class="file-size">({{ formatFileSize(file.size) }})</span>
              </div>
              <button 
                class="remove-file-btn"
                @click="removeFile(index)"
                title="Remove file"
              >
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>
          
          <div class="upload-actions">
            <button 
              class="upload-btn"
              @click="uploadFiles"
              :disabled="uploading || selectedFiles.length === 0"
            >
              <i class="fas fa-upload"></i>
              Upload {{ selectedFiles.length }} file(s)
            </button>
            <button 
              class="clear-btn"
              @click="clearFiles"
              :disabled="uploading"
            >
              <i class="fas fa-trash"></i>
              Clear All
            </button>
          </div>
        </div>

        <!-- Upload Progress -->
        <div v-if="uploading" class="upload-progress show">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
          </div>
          <p>Uploading... {{ uploadProgress }}%</p>
        </div>

        <!-- Success Message -->
        <div v-if="uploadSuccess" class="success-message show">
          <i class="fas fa-check-circle"></i>
          Files uploaded successfully!
        </div>

        <!-- Error Message -->
        <div v-if="uploadError" class="error-message show">
          <i class="fas fa-exclamation-circle"></i>
          {{ uploadError }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { eventService } from '../../services/api'

export default {
  name: 'EvidenceAttachment',
  props: {
    incidentId: {
      type: [String, Number],
      default: null
    },
    riskInstanceId: {
      type: [String, Number],
      default: null
    },
    userId: {
      type: [String, Number],
      default: null
    }
  },
  emits: ['filesUploaded'],
  setup(props, { emit }) {
    const fileInput = ref(null)
    const selectedFiles = ref([])
    const uploading = ref(false)
    const uploadProgress = ref(0)
    const uploadSuccess = ref(false)
    const uploadError = ref('')
    const showOptions = ref(false)
    const showUploadArea = ref(false)
    const showLinkArea = ref(false)
    const searchQuery = ref('')
    
    // Event data
    const riskavaireEvents = ref([])
    const integrationEvents = ref([])
    const documentHandlingEvents = ref([])
    const loadingEvents = ref(false)
    const eventsError = ref('')
    const activeFilter = ref('All')
    const selectedEvents = ref([])
    
    // Available events based on active filter
    const filteredEvents = computed(() => {
      let events = []
      
      if (activeFilter.value === 'All') {
        events = [...riskavaireEvents.value, ...integrationEvents.value, ...documentHandlingEvents.value]
      } else if (activeFilter.value === 'Riskavaire') {
        events = riskavaireEvents.value
      } else if (activeFilter.value === 'Integrations') {
        events = integrationEvents.value
      } else if (activeFilter.value === 'Document Handling') {
        events = documentHandlingEvents.value
      }
      
      // Apply search filter if query exists
      if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase()
        events = events.filter(event => 
          event.title.toLowerCase().includes(query) ||
          event.description?.toLowerCase().includes(query) ||
          event.source.toLowerCase().includes(query)
        )
      }
      
      return events
    })

    const showEvidenceOptions = () => {
      showOptions.value = true
    }

    const selectUploadOption = () => {
      showOptions.value = false
      showUploadArea.value = true
      showLinkArea.value = false
    }

    const selectLinkOption = async () => {
      showOptions.value = false
      showUploadArea.value = false
      showLinkArea.value = true
      
      // Fetch events when link option is selected
      await fetchAllEvents()
    }

    const goBack = () => {
      showOptions.value = false
      showUploadArea.value = false
      showLinkArea.value = false
    }

    const goBackToOptions = () => {
      showOptions.value = true
      showUploadArea.value = false
      showLinkArea.value = false
    }

    const triggerFileUpload = () => {
      fileInput.value.click()
    }

    const handleFileSelect = (event) => {
      const files = Array.from(event.target.files)
      
      // Validate file size (10MB limit)
      const maxSize = 10 * 1024 * 1024 // 10MB in bytes
      const validFiles = files.filter(file => {
        if (file.size > maxSize) {
          uploadError.value = `File "${file.name}" is too large. Maximum size is 10MB.`
          setTimeout(() => {
            uploadError.value = ''
          }, 5000)
          return false
        }
        return true
      })

      selectedFiles.value = [...selectedFiles.value, ...validFiles]
      
      // Clear the input so the same file can be selected again if needed
      event.target.value = ''
    }

    const removeFile = (index) => {
      selectedFiles.value.splice(index, 1)
    }

    const clearFiles = () => {
      selectedFiles.value = []
      uploadSuccess.value = false
      uploadError.value = ''
    }

    const uploadFiles = async () => {
      if (selectedFiles.value.length === 0) {
        uploadError.value = 'Please select files to upload.'
        return
      }

      // Check consent before proceeding
      let consentConfig = null
      try {
        const consentService = (await import('@/services/consentService.js')).default;
        const { CONSENT_ACTIONS, checkConsentRequired } = await import('@/utils/consentManager.js');
        
        // Determine if this is for risk or incident based on prop names
        const isRiskContext = props.riskInstanceId !== undefined
        const actionType = isRiskContext ? CONSENT_ACTIONS.UPLOAD_RISK : CONSENT_ACTIONS.UPLOAD_INCIDENT
        
        // Check if consent is required
        const consentCheck = await checkConsentRequired(actionType)
        if (consentCheck.required && consentCheck.config) {
          consentConfig = consentCheck.config
          
          // Show consent modal
          const canProceed = await consentService.checkAndRequestConsent(actionType);
          
          // If user declined consent, stop here
          if (!canProceed) {
            console.log(`${isRiskContext ? 'Risk' : 'Incident'} evidence upload cancelled by user (consent declined)`);
            return;
          }
        }
      } catch (consentError) {
        console.error('Error checking consent:', consentError);
        // Continue with upload if consent check fails
      }

      uploading.value = true
      uploadProgress.value = 0
      uploadError.value = ''
      uploadSuccess.value = false

      try {
        const uploadedFiles = []
        const totalFiles = selectedFiles.value.length
        
        // Upload files one by one
        for (let i = 0; i < selectedFiles.value.length; i++) {
          const file = selectedFiles.value[i]
          
          // Create form data for file upload
          const formData = new FormData()
          formData.append('file', file)
          
          // Determine if this is for risk or incident based on prop names
          const isRiskContext = props.riskInstanceId !== undefined
          
          if (isRiskContext) {
            formData.append('risk_instance_id', props.riskInstanceId || props.incidentId || 'temp')
            formData.append('user_id', props.userId || 'temp')
          } else {
            formData.append('incident_id', props.incidentId || 'temp')
            formData.append('user_id', props.userId || 'temp')
          }
          
          // Include consent data if consent was required and accepted
          if (consentConfig) {
            formData.append('consent_accepted', 'true')
            formData.append('consent_config_id', consentConfig.config_id.toString())
            formData.append('framework_id', consentConfig.framework_id || localStorage.getItem('framework_id') || '1')
            console.log('📋 [Consent] Including consent data in upload request:', {
              consent_accepted: true,
              consent_config_id: consentConfig.config_id,
              framework_id: consentConfig.framework_id || localStorage.getItem('framework_id') || '1'
            })
          }
          
          try {
            // Make API call to upload file - use appropriate endpoint
            const uploadUrl = isRiskContext ? '/api/upload-risk-evidence-file/' : '/api/upload-evidence-file/'
            const response = await fetch(uploadUrl, {
              method: 'POST',
              body: formData,
              headers: {
                // Don't set Content-Type header for FormData, let browser set it with boundary
              }
            })
            
            if (response.ok) {
              const result = await response.json()
              console.log('Upload response for', file.name, ':', result)
              
              if (result.success && result.files && result.files.length > 0) {
                // Handle the actual backend response structure
                const uploadedFileData = result.files.find(f => f.fileName === file.name) || result.files[0]
                uploadedFiles.push({
                  fileName: file.name,
                  'aws-file_link': uploadedFileData['aws-file_link'],
                  's3_key': uploadedFileData['s3_key'],
                  'stored_name': uploadedFileData['stored_name'],
                  'file_id': uploadedFileData['file_id'],
                  'upload_type': uploadedFileData['upload_type'],
                  size: file.size,
                  uploadedAt: uploadedFileData.uploadedAt || new Date().toISOString()
                })
              } else {
                // Fallback for legacy response format
                uploadedFiles.push({
                  fileName: file.name,
                  'aws-file_link': result.file_url || result.url,
                  size: file.size,
                  uploadedAt: new Date().toISOString()
                })
              }
            } else {
              const errorResult = await response.json()
              throw new Error(errorResult.error || `Failed to upload ${file.name}`)
            }
          } catch (fileError) {
            console.error(`Error uploading ${file.name}:`, fileError)
            uploadError.value = `Failed to upload ${file.name}. Please try again.`
            uploading.value = false
            return
          }
          
          // Update progress
          uploadProgress.value = Math.round(((i + 1) / totalFiles) * 100)
        }

        // Emit uploaded files to parent component
        emit('filesUploaded', uploadedFiles)
        
        uploadSuccess.value = true
        selectedFiles.value = []
        uploadProgress.value = 100

        // Clear success message after 3 seconds
        setTimeout(() => {
          uploadSuccess.value = false
        }, 3000)

      } catch (error) {
        uploadError.value = 'Failed to upload files. Please try again.'
        console.error('Upload error:', error)
      } finally {
        uploading.value = false
      }
    }

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const formatDate = (date) => {
      return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
    
    // Event fetching functions
    const fetchRiskaVaireEvents = async () => {
      try {
        loadingEvents.value = true
        eventsError.value = ''
        
        const response = await eventService.getRiskaVaireEvents()
        
        if (response.data.success) {
          const events = response.data.events || []
          
          // Transform events to match the expected format
          riskavaireEvents.value = events.map(event => ({
            id: event.event_id,
            title: event.event_title,
            framework: event.framework,
            module: event.module,
            category: event.category,
            source: event.source || 'RiskaVaire Module',
            timestamp: event.created_at ? new Date(event.created_at).toLocaleDateString('en-US', {
              month: '2-digit',
              day: '2-digit',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            }) : 'N/A',
            status: event.status,
            linkedRecordType: event.linked_record_type,
            linkedRecordId: event.linked_record_id,
            linkedRecordName: event.linked_record_name,
            priority: event.priority,
            description: event.description,
            owner: event.owner,
            reviewer: event.reviewer,
            evidence: event.evidence || []
          }))
        } else {
          eventsError.value = response.data.message || 'Failed to fetch RiskaVaire events'
        }
      } catch (error) {
        console.error('Error fetching RiskaVaire events:', error)
        eventsError.value = 'Failed to fetch RiskaVaire events. Please try again.'
      }
    }
    
    const fetchIntegrationEvents = async () => {
      try {
        const response = await eventService.getIntegrationEvents()
        
        if (response.data.success) {
          const events = response.data.events || []
          
          // Transform events to match the expected format
          integrationEvents.value = events.map(event => ({
            id: event.id,
            title: event.summary || event.title,
            framework: event.project_name || 'Jira',
            module: event.issue_type || 'Issue',
            category: event.issue_type || 'Issue',
            source: 'Jira',
            timestamp: event.updated_date || event.created_date,
            status: event.status || 'New',
            linkedRecordType: event.issue_type,
            linkedRecordId: event.issue_key,
            linkedRecordName: event.summary,
            priority: event.priority || 'Medium',
            description: event.description,
            owner: event.assignee || 'Unassigned',
            reviewer: 'Pending Assignment',
            evidence: [],
            suggestedType: event.issue_type === 'Bug' ? 'Bug Report Event' : 
                          event.issue_type === 'Task' ? 'Task Completion Event' :
                          event.issue_type === 'Story' ? 'User Story Event' : 'General Event'
          }))
        } else {
          eventsError.value = response.data.message || 'Failed to fetch integration events'
        }
      } catch (error) {
        console.error('Error fetching integration events:', error)
        eventsError.value = 'Failed to fetch integration events. Please try again.'
      }
    }
    
    const fetchDocumentHandlingEvents = async () => {
      try {
        const response = await eventService.getFileOperations({
          limit: 50,
          show_all: true  // Show all records regardless of user_id
        })
        
        console.log('File operations API response:', response.data)
        
        if (response.data.success) {
          const events = response.data.events || []
          
          console.log(`Received ${events.length} file operations out of ${response.data.total_records || 'unknown'} total records`)
          
          // Events are already transformed in the backend to match the expected format
          documentHandlingEvents.value = events.map(event => ({
            id: event.id,
            title: event.title,
            framework: event.framework,
            module: event.module,
            category: event.category,
            source: event.source,
            timestamp: event.timestamp,
            status: event.status,
            linkedRecordType: event.linkedRecordType,
            linkedRecordId: event.linkedRecordId,
            linkedRecordName: event.linkedRecordName,
            priority: event.priority,
            description: event.description,
            owner: event.owner,
            reviewer: event.reviewer,
            evidence: event.evidence || [],
            file_data: event.file_data || {}
          }))
          
          console.log('Document handling events loaded:', documentHandlingEvents.value.length)
          console.log('First few events:', documentHandlingEvents.value.slice(0, 3))
        } else {
          console.error('Failed to fetch document handling events:', response.data.message)
          eventsError.value = response.data.message || 'Failed to fetch document handling events'
        }
      } catch (error) {
        console.error('Error fetching document handling events:', error)
        eventsError.value = 'Failed to fetch document handling events. Please try again.'
      }
    }
    
    const fetchAllEvents = async () => {
      loadingEvents.value = true
      eventsError.value = ''
      
      try {
        await Promise.all([
          fetchRiskaVaireEvents(),
          fetchIntegrationEvents(),
          fetchDocumentHandlingEvents()
        ])
      } catch (error) {
        console.error('Error fetching events:', error)
        eventsError.value = 'Failed to fetch events. Please try again.'
      } finally {
        loadingEvents.value = false
      }
    }
    
    // Filter handling
    const setActiveFilter = async (filter) => {
      activeFilter.value = filter
      
      // Fetch events if not already loaded
      if (filter === 'Riskavaire' && riskavaireEvents.value.length === 0) {
        await fetchRiskaVaireEvents()
      } else if (filter === 'Integrations' && integrationEvents.value.length === 0) {
        await fetchIntegrationEvents()
      } else if (filter === 'Document Handling' && documentHandlingEvents.value.length === 0) {
        await fetchDocumentHandlingEvents()
      }
    }
    
    // Event selection
    const selectEvent = (event) => {
      const index = selectedEvents.value.findIndex(e => e.id === event.id)
      if (index > -1) {
        selectedEvents.value.splice(index, 1)
      } else {
        selectedEvents.value.push(event)
      }
    }
    
    const isEventSelected = (event) => {
      return selectedEvents.value.some(e => e.id === event.id)
    }
    
    const linkSelectedEvents = async () => {
      if (selectedEvents.value.length > 0) {
        try {
          uploading.value = true
          uploadProgress.value = 0
          uploadError.value = ''
          
          console.log('Linking selected events:', selectedEvents.value)
          
          // Prepare the data for API call
          const isRiskContext = props.riskInstanceId !== null && props.riskInstanceId !== undefined && props.riskInstanceId !== ''
          const linkData = isRiskContext ? {
            risk_instance_id: props.riskInstanceId,
            user_id: props.userId,
            linked_events: selectedEvents.value
          } : {
            incident_id: props.incidentId,
            user_id: props.userId,
            linked_events: selectedEvents.value
          }
          
          console.log('Props check:', {
            riskInstanceId: props.riskInstanceId,
            incidentId: props.incidentId,
            isRiskContext: isRiskContext,
            linkData: linkData
          })
          
          console.log('Sending link data:', linkData)
          
          // Validate that we have the required data before making API call
          if (isRiskContext && (!props.riskInstanceId || props.riskInstanceId === null || props.riskInstanceId === '')) {
            console.error('Risk instance ID is missing for risk context')
            uploadError.value = 'Risk instance ID is required for evidence linking in risk context'
            return
          }
          
          if (!isRiskContext && (!props.incidentId || props.incidentId === null || props.incidentId === '')) {
            console.error('Incident ID is missing for incident context')
            uploadError.value = 'Incident ID is required for evidence linking in incident context'
            return
          }
          
          // Get JWT token from localStorage
          const token = localStorage.getItem('access_token')
          
          // Make API call to link evidence - use appropriate endpoint
          const linkUrl = isRiskContext ? '/api/risks/link-evidence/' : '/api/incidents/link-evidence/'
          const response = await fetch(linkUrl, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': token ? `Bearer ${token}` : '',
            },
            body: JSON.stringify(linkData)
          })
          
          if (response.ok) {
            const result = await response.json()
            console.log('Link response:', result)
            
            if (result.success) {
              // Transform linked events to match the uploaded files format for parent component
              const linkedEventsAsFiles = selectedEvents.value.map(event => ({
                fileName: `${event.title} (${event.source})`,
                'aws-file_link': `#linked-event-${event.id}`, // Use a placeholder URL for linked events
                size: 0, // Linked events don't have file size
                uploadedAt: new Date().toISOString(),
                type: 'linked_evidence',
                linkedEvent: event // Store the full event data
              }))
              
              // Emit the linked events as "uploaded files" to the parent component
              emit('filesUploaded', linkedEventsAsFiles)
              
              uploadSuccess.value = true
              selectedEvents.value = []
              uploadProgress.value = 100
              
              setTimeout(() => {
                uploadSuccess.value = false
                goBack()
              }, 2000)
            } else {
              uploadError.value = result.message || 'Failed to link selected events'
            }
          } else {
            const errorResult = await response.json().catch(() => ({ message: 'Unknown error' }))
            uploadError.value = errorResult.message || 'Failed to link selected events'
          }
        } catch (error) {
          console.error('Error linking events:', error)
          uploadError.value = 'Failed to link selected events. Please try again.'
        } finally {
          uploading.value = false
        }
      }
    }

    return {
      fileInput,
      selectedFiles,
      uploading,
      uploadProgress,
      uploadSuccess,
      uploadError,
      showOptions,
      showUploadArea,
      showLinkArea,
      searchQuery,
      // Event data
      riskavaireEvents,
      integrationEvents,
      documentHandlingEvents,
      loadingEvents,
      eventsError,
      activeFilter,
      selectedEvents,
      filteredEvents,
      // Functions
      showEvidenceOptions,
      selectUploadOption,
      selectLinkOption,
      goBack,
      goBackToOptions,
      triggerFileUpload,
      handleFileSelect,
      removeFile,
      clearFiles,
      uploadFiles,
      formatFileSize,
      formatDate,
      // Event functions
      fetchRiskaVaireEvents,
      fetchIntegrationEvents,
      fetchDocumentHandlingEvents,
      fetchAllEvents,
      setActiveFilter,
      selectEvent,
      isEventSelected,
      linkSelectedEvents
    }
  }
}
</script>

<style scoped>
.evidence-attachment-container {
  padding: 0;
  max-width: 100%;
  margin: 0;
  background: transparent;
  min-height: auto;
}

.content-wrapper {
  display: flex;
  justify-content: flex-start;
}

.attachment-section {
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  overflow: visible;
  width: 100%;
  max-width: 100%;
}

.section-header {
  padding: 0;
  border-bottom: none;
  background: transparent;
  display: none;
}

.section-header h2 {
  display: none;
}

.upload-area {
  padding: 0;
  text-align: left;
}

.upload-button-container {
  margin-bottom: 0;
}

.attach-evidence-btn {
  background: #f8f9fa;
  color: #6c757d;
  border: 1px solid #dee2e6;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  box-shadow: none;
}

.attach-evidence-btn:hover:not(:disabled) {
  background: #e9ecef;
  border-color: #adb5bd;
  transform: none;
  box-shadow: none;
}

.attach-evidence-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Hide all other elements by default */
.evidence-options,
.file-upload-section,
.link-evidence-section,
.selected-files,
.upload-progress,
.success-message,
.error-message {
  display: none;
}

/* Show elements when their respective conditions are met */
.evidence-options.show {
  display: block;
}

.file-upload-section.show {
  display: block;
}

.link-evidence-section.show {
  display: block;
}

.selected-files.show {
  display: block;
}

.upload-progress.show {
  display: block;
}

.success-message.show {
  display: flex;
}

.error-message.show {
  display: flex;
}

/* Basic styles for when elements are shown */
.evidence-options,
.file-upload-section,
.link-evidence-section {
  padding: 30px;
  text-align: left;
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.selected-files {
  padding: 25px;
  border-top: 1px solid #ecf0f1;
  background: #f8f9fa;
}

.upload-progress {
  padding: 20px;
  text-align: center;
}

.success-message,
.error-message {
  padding: 15px;
  border-radius: 6px;
  margin: 15px 25px;
  align-items: center;
  gap: 10px;
  font-weight: 500;
}

.success-message {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.error-message {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

/* Minimal styles for form elements when shown */
.file-info {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.file-list {
  margin-bottom: 20px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: white;
  border-radius: 8px;
  margin-bottom: 10px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.file-info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.file-name {
  font-weight: 500;
  color: #2c3e50;
}

.file-size {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.remove-file-btn {
  background: #e74c3c;
  color: white;
  border: none;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.upload-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.upload-btn,
.clear-btn {
  padding: 12px 20px;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-btn {
  background: #27ae60;
  color: white;
}

.clear-btn {
  background: #95a5a6;
  color: white;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #ecf0f1;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3498db, #2980b9);
  transition: width 0.3s ease;
}

/* Basic button styles */
.back-btn {
  background: #95a5a6;
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.select-files-btn {
  background: linear-gradient(135deg, #27ae60, #229954);
  color: white;
  border: none;
  padding: 15px 30px;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
}

/* Hide file input */
input[type="file"] {
  display: none;
}

/* Additional styles for when elements are shown */
.evidence-options.show h3 {
  color: #2c3e50;
  font-size: 1.4rem;
  margin-bottom: 30px;
  font-weight: 600;
}

.options-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 25px;
  margin-bottom: 30px;
}

@media (max-width: 768px) {
  .options-container {
    grid-template-columns: 1fr;
  }
}

.option-card {
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  padding: 30px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.option-card:hover {
  border-color: #3498db;
  background: #f0f8ff;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(52, 152, 219, 0.2);
}

.option-icon {
  margin-bottom: 15px;
}

.option-icon i {
  font-size: 2.5rem;
  color: #3498db;
}

.option-card h4 {
  color: #2c3e50;
  font-size: 1.2rem;
  margin: 0 0 10px 0;
  font-weight: 600;
}

.option-card p {
  color: #7f8c8d;
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.4;
}

.back-btn.small {
  padding: 8px 15px;
  font-size: 0.9rem;
}

.upload-header,
.link-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ecf0f1;
}

.upload-header h3,
.link-header h3 {
  color: #2c3e50;
  font-size: 1.3rem;
  margin: 0;
  font-weight: 600;
}

.file-info p {
  margin: 5px 0;
}

.file-info i {
  margin-right: 5px;
  color: #3498db;
}

.selected-files.show h3 {
  color: #2c3e50;
  margin: 0 0 15px 0;
  font-size: 1.2rem;
}

.file-info-item i {
  color: #3498db;
  font-size: 1.1rem;
}

.remove-file-btn:hover {
  background: #c0392b;
}

.upload-btn:hover:not(:disabled) {
  background: #229954;
}

.clear-btn:hover:not(:disabled) {
  background: #7f8c8d;
}

.upload-btn:disabled,
.clear-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.select-files-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #229954, #1e8449);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(39, 174, 96, 0.4);
}

.select-files-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.back-btn:hover {
  background: #7f8c8d;
}

/* Link evidence specific styles */
.search-container {
  margin-top: 20px;
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.search-input-container {
  position: relative;
  margin-bottom: 20px;
}

.search-input-container i {
  position: absolute;
  left: 15px;
  top: 50%;
  transform: translateY(-50%);
  color: #7f8c8d;
  font-size: 1.1rem;
}

.search-input {
  width: 100%;
  padding: 15px 15px 15px 45px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.search-input:focus {
  outline: none;
  border-color: #3498db;
}

.search-filters {
  display: flex;
  gap: 10px;
  margin-bottom: 25px;
  flex-wrap: wrap;
}

.filter-btn {
  background: #f8f9fa;
  color: #6c757d;
  border: 1px solid #dee2e6;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn:hover {
  background: #e9ecef;
}

.filter-btn.active {
  background: #3498db;
  color: white;
  border-color: #3498db;
}

.search-results {
  min-height: 200px;
  max-height: 70vh;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 30px;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
}

/* Event Results Styles */
.loading-state,
.error-state,
.no-results-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  color: #7f8c8d;
}

.loading-state i {
  font-size: 2rem;
  margin-bottom: 15px;
  color: #3498db;
}

.error-state i {
  font-size: 2rem;
  margin-bottom: 15px;
  color: #e74c3c;
}

.no-results-state i {
  font-size: 2rem;
  margin-bottom: 15px;
  color: #95a5a6;
}

.retry-btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #2980b9;
}

.events-list {
  width: 100%;
  max-width: 100%;
  max-height: 60vh;
  overflow-y: auto;
  overflow-x: hidden;
  box-sizing: border-box;
  padding: 0;
}

.events-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #ecf0f1;
  margin-bottom: 12px;
}

.events-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 1rem;
  font-weight: 600;
}

.link-selected-btn {
  background: #27ae60;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.2s;
}

.link-selected-btn:hover {
  background: #229954;
}

.event-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.event-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  width: 100%;
  box-sizing: border-box;
  min-width: 0;
  word-wrap: break-word;
  overflow-wrap: break-word;
  margin-bottom: 8px;
}

.event-item:hover {
  border-color: #3498db;
  box-shadow: 0 2px 8px rgba(52, 152, 219, 0.1);
}

.event-item.selected {
  border-color: #3498db;
  background: #f0f8ff;
  box-shadow: 0 2px 8px rgba(52, 152, 219, 0.2);
}

.event-checkbox {
  margin-top: 2px;
}

.event-checkbox input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.event-content {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.event-header-info {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
  gap: 8px;
  width: 100%;
  min-width: 0;
  flex-wrap: wrap;
}

.event-title {
  margin: 0 0 4px 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: #2c3e50;
  line-height: 1.3;
  flex: 1;
  min-width: 0;
  word-wrap: break-word;
  overflow-wrap: break-word;
  overflow: hidden;
}

.event-source {
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  flex-shrink: 0;
}

.jira-source {
  background: #e3f2fd;
  color: #1976d2;
}

.riskavaire-source {
  background: #f3e5f5;
  color: #7b1fa2;
}

.document-source {
  background: #e8f5e8;
  color: #2e7d32;
}

.event-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.event-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: #7f8c8d;
}

.event-framework {
  font-weight: 500;
  color: #6b7280;
}

.event-separator {
  color: #bdc3c7;
}

.event-timestamp {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.event-description {
  margin: 0;
  font-size: 0.85rem;
  color: #555;
  line-height: 1.3;
  word-wrap: break-word;
  overflow-wrap: break-word;
  overflow: hidden;
}

.event-status {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}

.status-badge,
.priority-badge {
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-badge {
  background: #e9ecef;
  color: #6c757d;
}

.status-new {
  background: #e3f2fd;
  color: #1976d2;
}

.status-processing {
  background: #f3e5f5;
  color: #7b1fa2;
}

.status-completed {
  background: #e8f5e8;
  color: #2e7d32;
}

.status-approved {
  background: #e8f5e8;
  color: #2e7d32;
}

.status-rejected {
  background: #ffebee;
  color: #c62828;
}

.priority-badge {
  background: #f8f9fa;
  color: #6c757d;
}

.priority-high {
  background: #ffebee;
  color: #c62828;
}

.priority-medium {
  background: #fff3e0;
  color: #ef6c00;
}

.priority-low {
  background: #e8f5e8;
  color: #2e7d32;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .event-header-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .event-meta {
    flex-wrap: wrap;
  }
  
  .events-header {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  
  .link-selected-btn {
    align-self: flex-end;
  }
}
</style>
