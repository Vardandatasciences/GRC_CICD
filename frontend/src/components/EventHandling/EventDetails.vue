<template>
  <div class="event-details-container">
    <!-- Header Section -->
    <div class="event-details-header">
      <div class="event-details-header-content">
        <div class="event-details-title-section">
          <button @click="goBack" class="event-details-back-btn">
            <svg class="event-details-back-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
            </svg>
            Back
          </button>
          <div class="event-details-title-info">
            <h1 class="event-details-title">{{ eventData.title || 'Untitled Event' }}</h1>
            <p class="event-details-subtitle">Event ID: {{ eventData.id || 'N/A' }}</p>
          </div>
        </div>
        <div class="event-details-header-actions">
          <!-- Show Create Event button when coming from queue -->
          <button
            v-if="showActionButtons && eventData.isFromQueue"
            @click="handleCreateEvent"
            class="event-details-action-btn event-details-create-btn"
          >
            <svg class="event-details-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
            Create Event
          </button>
          <!-- Show Edit button when coming from list or other sources -->
          <button
            v-else-if="showActionButtons && canEditEvents && eventData.status !== 'Approved' && eventData.status !== 'Rejected'"
            @click="handleEdit"
            class="event-details-action-btn event-details-edit-btn"
          >
            <svg class="event-details-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
            Edit
          </button>
          <button
            v-if="showActionButtons && canApproveEvents && eventData.status === 'Pending Approval'"
            @click="handleApprove"
            class="event-details-action-btn event-details-approve-btn"
          >
            <svg class="event-details-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            Approve
          </button>
          <button
            v-if="showActionButtons && canRejectEvents && eventData.status === 'Pending Approval'"
            @click="handleReject"
            class="event-details-action-btn event-details-reject-btn"
          >
            <svg class="event-details-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
            Reject
          </button>
          <button
            v-if="showActionButtons && canArchiveEvents"
            @click="handleArchive"
            class="event-details-action-btn event-details-archive-btn"
          >
            <svg class="event-details-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-14 0a2 2 0 012-2h10a2 2 0 012 2"></path>
            </svg>
            Archive
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="event-details-loading">
      <div class="event-details-loading-spinner">
        <div class="event-details-spinner"></div>
        <p>Loading event details...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="event-details-error">
      <div class="event-details-error-content">
        <div class="event-details-error-icon">
          <svg class="event-details-error-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
        <p class="event-details-error-message">{{ error }}</p>
        <div class="event-details-error-actions">
          <button @click="goBack" class="event-details-error-btn">
            Back to Events List
          </button>
          <button @click="loadEventData" class="event-details-error-btn event-details-error-retry">
            Try Again
          </button>
        </div>
      </div>
    </div>

    <!-- Content Section -->
    <div v-else class="event-details-content">
      <div class="event-details-grid">
        <!-- Left Column - Event Details -->
        <div class="event-details-main">
          <div class="event-details-section">
            <h3 class="event-details-section-title">Event Information</h3>
            <div class="event-details-info-grid">
              <div class="event-details-info-item">
                <span class="event-details-info-label">Framework</span>
                <span class="event-details-info-value">{{ eventData.framework || eventData.framework_name || 'Not Assigned' }}</span>
              </div>
              <div class="event-details-info-item">
                <span class="event-details-info-label">Module</span>
                <span class="event-details-info-value">{{ eventData.module || 'Not Assigned' }}</span>
              </div>
              <div class="event-details-info-item">
                <span class="event-details-info-label">Category</span>
                <span class="event-details-info-value">{{ eventData.category || 'Not Assigned' }}</span>
              </div>
              <div class="event-details-info-item">
                <span class="event-details-info-label">Status</span>
                <span :class="`event-details-status-badge ${getStatusBadgeClass(eventData.status)}`">
                  {{ eventData.status || 'Not Assigned' }}
                </span>
              </div>
              <div class="event-details-info-item">
                <span class="event-details-info-label">Priority</span>
                <span class="event-details-info-value">{{ eventData.priority || 'Not Assigned' }}</span>
              </div>
              <div class="event-details-info-item">
                <span class="event-details-info-label">Owner</span>
                <span class="event-details-info-value">{{ eventData.owner || eventData.owner_name || 'Not Assigned' }}</span>
              </div>
              <div class="event-details-info-item">
                <span class="event-details-info-label">Reviewer</span>
                <span class="event-details-info-value">{{ eventData.reviewer || eventData.reviewer_name || 'Not Assigned' }}</span>
              </div>
              <div class="event-details-info-item">
                <span class="event-details-info-label">Created</span>
                <span class="event-details-info-value">{{ eventData.timestamp || eventData.created_at || 'N/A' }}</span>
              </div>
            </div>
          </div>

          <!-- Description Section -->
          <div class="event-details-section" v-if="eventData.description">
            <h3 class="event-details-section-title">Description</h3>
            <div class="event-details-description">
              {{ eventData.description }}
            </div>
          </div>

          <!-- Linked Record Section -->
          <div class="event-details-section" v-if="eventData.linkedRecordName || eventData.linkedRecordId">
            <h3 class="event-details-section-title">Linked Record</h3>
            <div class="event-details-info-grid">
              <div class="event-details-info-item">
                <span class="event-details-info-label">Type</span>
                <span class="event-details-info-value">{{ eventData.linkedRecordType || 'N/A' }}</span>
              </div>
              <div class="event-details-info-item">
                <span class="event-details-info-label">ID</span>
                <span class="event-details-info-value">{{ eventData.linkedRecordId || 'N/A' }}</span>
              </div>
              <div class="event-details-info-item">
                <span class="event-details-info-label">Name</span>
                <span class="event-details-info-value">{{ eventData.linkedRecordName || 'N/A' }}</span>
              </div>
            </div>
          </div>

          <!-- Dynamic Fields Section -->
          <div class="event-details-section" v-if="eventData.dynamic_fields_data && Object.keys(eventData.dynamic_fields_data).length > 0">
            <h3 class="event-details-section-title">Additional Information</h3>
            <div class="event-details-info-grid">
              <div v-for="(value, key) in eventData.dynamic_fields_data" :key="key" class="event-details-info-item">
                <span class="event-details-info-label">{{ formatDynamicFieldLabel(key) }}</span>
                <span class="event-details-info-value">{{ formatDynamicFieldValue(value) }}</span>
              </div>
            </div>
          </div>

          <!-- Evidence Section -->
          <div class="event-details-section" v-if="eventData.evidence && eventData.evidence.length > 0">
            <h3 class="event-details-section-title">Evidence</h3>
            <div class="event-details-evidence-list">
              <div v-for="(evidence, index) in eventData.evidence" :key="index" class="event-details-evidence-item">
                <div class="event-details-evidence-info">
                  <span class="event-details-evidence-name">{{ evidence.name || evidence.filename || evidence.fileName || `Evidence ${index + 1}` }}</span>
                  <span class="event-details-evidence-type">{{ evidence.uploadDate || 'Unknown Date' }}</span>
                </div>
                <button v-if="evidence.url || evidence.s3_url" @click="downloadEvidence(evidence)" class="event-details-evidence-link event-details-evidence-button">
                  View
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column - Source Information -->
        <div class="event-details-sidebar">
          <div class="event-details-section">
            <h3 class="event-details-section-title">Source Information</h3>
            <div class="event-details-info-grid">
              <div class="event-details-info-item">
                <span class="event-details-info-label">Source System</span>
                <span class="event-details-info-value">{{ eventData.source_system || eventData.source || 'GRC System' }}</span>
              </div>
              <div class="event-details-info-item" v-if="eventData.suggestedType">
                <span class="event-details-info-label">Suggested Type</span>
                <span class="event-details-info-value">{{ eventData.suggestedType }}</span>
              </div>
              <div class="event-details-info-item" v-if="eventData.isFromQueue">
                <span class="event-details-info-label">Queue Type</span>
                <span class="event-details-info-value">{{ eventData.queueType || 'N/A' }}</span>
              </div>
            </div>
          </div>

          <!-- Metadata Section -->
          <div class="event-details-section" v-if="eventData.metadata && Object.keys(eventData.metadata).length > 0">
            <h3 class="event-details-section-title">Integration Metadata</h3>
            <div class="event-details-raw-data">
              <div v-for="entry in filteredMetadataDetails" :key="entry.key" class="event-details-raw-item">
                <span class="event-details-raw-key">{{ formatKey(entry.key) }}</span>
                <span class="event-details-raw-value">{{ formatValue(entry.value) }}</span>
              </div>
            </div>
          </div>


        </div>
      </div>
    </div>

    <!-- Approval/Reject/Archive Modals -->
    <ApprovalModal
      :is-open="showApprovalModal"
      type="approve"
      :event-title="eventData?.title || ''"
      @submit="handleModalSubmit"
      @cancel="handleModalCancel"
    />
    <ApprovalModal
      :is-open="showRejectModal"
      type="reject"
      :event-title="eventData?.title || ''"
      @submit="handleModalSubmit"
      @cancel="handleModalCancel"
    />
    <ApprovalModal
      :is-open="showArchiveModal"
      type="archive"
      :event-title="eventData?.title || ''"
      @submit="handleModalSubmit"
      @cancel="handleModalCancel"
    />

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useEventPermissions } from '../../composables/useEventPermissions'
import ApprovalModal from './ApprovalModal.vue'
import { PopupService } from '../../modules/popus/popupService'
import PopupModal from '../../modules/popus/PopupModal.vue'
import { eventService } from '../../services/api'

export default {
  name: 'EventDetails',
  components: {
    ApprovalModal,
    PopupModal
  },
  setup() {
    const router = useRouter()
    
    // Event permissions
    const {
      canEditEvents,
      canApproveEvents,
      canRejectEvents,
      canArchiveEvents,
      fetchEventPermissions
    } = useEventPermissions()
    
    const eventData = ref({})
    const showApprovalModal = ref(false)
    const showRejectModal = ref(false)
    const showArchiveModal = ref(false)
    const modalType = ref('approve')
    const showActionButtons = ref(true)
    const loading = ref(true)
    const error = ref(null)

    // Computed property to filter event details for display
    const filteredEventDetails = computed(() => {
      if (!eventData.value.rawData) return []
      
      const data = eventData.value.rawData
      const filteredEntries = []
      
      for (const [key, value] of Object.entries(data)) {
        if (value !== null && value !== undefined && value !== '') {
          filteredEntries.push({ key, value })
        }
      }
      
      return filteredEntries
    })

    // Computed property to filter metadata details for display
    const filteredMetadataDetails = computed(() => {
      console.log('DEBUG: filteredMetadataDetails computed - eventData.value.metadata:', eventData.value.metadata)
      if (!eventData.value.metadata) {
        console.log('DEBUG: No metadata found')
        return []
      }

      const metadata = eventData.value.metadata
      const filteredEntries = []

      for (const [key, value] of Object.entries(metadata)) {
        if (value !== null && value !== undefined && value !== '') {
          filteredEntries.push({ key, value })
        }
      }

      console.log('DEBUG: filteredMetadataDetails result:', filteredEntries)
      return filteredEntries
    })

    const formatKey = (key) => {
      // Convert camelCase and snake_case to readable format
      return key
        .replace(/([A-Z])/g, ' $1')
        .replace(/_/g, ' ')
        .replace(/^./, str => str.toUpperCase())
        .trim()
    }

    const formatValue = (value) => {
      if (Array.isArray(value)) {
        return value.length > 0 ? value.join(', ') : 'None'
      }
      if (typeof value === 'object' && value !== null) {
        return JSON.stringify(value, null, 2)
      }
      if (typeof value === 'boolean') {
        return value ? 'Yes' : 'No'
      }
      return String(value)
    }

    const formatDynamicFieldLabel = (key) => {
      // Convert camelCase and snake_case to readable format
      return key
        .replace(/([A-Z])/g, ' $1')
        .replace(/_/g, ' ')
        .replace(/^./, str => str.toUpperCase())
        .trim()
    }

    const formatDynamicFieldValue = (value) => {
      if (value === null || value === undefined) {
        return 'N/A'
      }
      if (Array.isArray(value)) {
        return value.length > 0 ? value.join(', ') : 'None'
      }
      if (typeof value === 'object') {
        return JSON.stringify(value, null, 2)
      }
      if (typeof value === 'boolean') {
        return value ? 'Yes' : 'No'
      }
      return String(value)
    }

    const getEvidenceDownloadUrl = (evidence) => {
      console.log('DEBUG: Getting download URL for evidence:', evidence)
      
      // Get the S3 URL from evidence object
      const s3Url = evidence.s3_url || evidence.url
      const filename = evidence.fileName || evidence.filename || evidence.name || 'evidence-file'
      
      console.log('DEBUG: S3 URL:', s3Url)
      console.log('DEBUG: Filename:', filename)
      
      if (!s3Url) {
        console.error('DEBUG: No S3 URL found in evidence object')
        return null
      }
      
      // Extract S3 key from URL
      let s3Key = ''
      if (s3Url.includes('amazonaws.com')) {
        // Handle S3 URLs like: https://bucket.s3.region.amazonaws.com/path/to/file.ext
        const urlParts = s3Url.split('amazonaws.com/')
        if (urlParts.length > 1) {
          s3Key = urlParts[1]
        }
       } else if (s3Url.includes('s3://')) {
         // Handle S3 protocol URLs like: s3://bucket/path/to/file.ext
         s3Key = s3Url.replace(/^s3:\/\/[^/]+\//, '')
      } else {
        // If it's already just the key or a relative path
        s3Key = s3Url.replace(/^\/+/, '') // Remove leading slashes
      }
      
      console.log('DEBUG: Extracted S3 key:', s3Key)
      
      if (!s3Key) {
        console.error('DEBUG: Could not extract S3 key from URL:', s3Url)
        return null
      }
      
       const userId = localStorage.getItem('user_id') || '1'
       const downloadUrl = `/api/s3/download/${encodeURIComponent(s3Key)}/${encodeURIComponent(filename)}/?user_id=${userId}`
       console.log('DEBUG: Generated download URL:', downloadUrl)
       return downloadUrl
    }

    const downloadEvidence = (evidence) => {
      console.log('EventDetails - Opening evidence in new tab:', evidence)
      
      // Get the S3 URL directly from evidence object
      const s3Url = evidence.s3_url || evidence.url
      
      if (!s3Url) {
        console.error('No S3 URL found in evidence object:', evidence)
        PopupService.error('Unable to open evidence: No file URL found', 'Error')
        return
      }

      console.log('EventDetails - Opening S3 URL:', s3Url)

      try {
        // Simply open the S3 URL in a new tab
        window.open(s3Url, '_blank')
        console.log('EventDetails - Evidence opened in new tab')
      } catch (error) {
        console.error('EventDetails - Error opening evidence:', error)
        PopupService.error('Failed to open evidence. Please try again.', 'Error')
      }
    }

    const getStatusBadgeClass = (status) => {
      const statusClasses = {
        'New': 'bg-blue-100 text-blue-800',
        'In Progress': 'bg-yellow-100 text-yellow-800',
        'Completed': 'bg-green-100 text-green-800',
        'Approved': 'bg-green-100 text-green-800',
        'Rejected': 'bg-red-100 text-red-800',
        'Processing': 'bg-purple-100 text-purple-800',
        'Archived': 'bg-gray-100 text-gray-800',
        'Draft': 'bg-gray-100 text-gray-800',
        'Pending Approval': 'bg-orange-100 text-orange-800',
        'Under Review': 'bg-blue-100 text-blue-800'
      }
      return statusClasses[status] || 'bg-gray-100 text-gray-800'
    }

    const goBack = () => {
      // Check if we came from queue or list
      if (eventData.value.isFromQueue) {
        router.push('/event-handling/queue')
      } else if (eventData.value.isFromList) {
        router.push('/event-handling/list')
      } else {
        router.push('/event-handling/dashboard')
      }
    }

    const handleEdit = () => {
      // Store the event data in sessionStorage for the event creation page to use
      sessionStorage.setItem('editEventData', JSON.stringify({
        id: eventData.value.id,
        title: eventData.value.title,
        description: eventData.value.description,
        framework: eventData.value.framework,
        module: eventData.value.module,
        category: eventData.value.category,
        owner: eventData.value.owner,
        reviewer: eventData.value.reviewer,
        recurrence: eventData.value.recurrence_type || 'Non-Recurring',
        frequency: eventData.value.frequency,
        startDate: eventData.value.start_date,
        endDate: eventData.value.end_date,
        evidence: eventData.value.evidence || [],
        evidence_string: eventData.value.evidence_string || '',
        isEdit: true
      }))
      
      // Navigate to event creation page
      router.push('/event-handling/create')
    }

    const handleCreateEvent = () => {
      // Store the queue event data in sessionStorage for the event creation page to use
      const createEventData = {
        source: eventData.value.source || 'RiskaVaire Module',
        rawData: eventData.value.rawData || eventData.value,
        title: eventData.value.title || 'New Event',
        description: eventData.value.description || '',
        priority: eventData.value.priority || 'Medium',
        status: eventData.value.status || 'New',
        framework: eventData.value.framework || '',
        module: eventData.value.module || '',
        category: eventData.value.category || '',
        owner: eventData.value.owner || '',
        reviewer: eventData.value.reviewer || '',
        linkedRecordType: eventData.value.linkedRecordType || '',
        linkedRecordId: eventData.value.linkedRecordId || '',
        linkedRecordName: eventData.value.linkedRecordName || '',
        queueItemId: eventData.value.id, // Store the queue item ID for tracking
        timestamp: eventData.value.timestamp || new Date().toISOString(),
        suggestedType: eventData.value.suggestedType || 'Event',
        // Store the full popup data for the Source Information section
        popupData: {
          source: eventData.value.source || 'RiskaVaire Module',
          title: eventData.value.title || 'N/A',
          timestamp: eventData.value.timestamp || 'N/A',
          status: eventData.value.status || 'New',
          queueType: eventData.value.queueType || 'N/A',
          rawData: eventData.value.rawData || eventData.value
        }
      }
      
      // Store in sessionStorage based on queue type
      if (eventData.value.queueType === 'integrations' || eventData.value.source === 'Jira') {
        sessionStorage.setItem('integrationEventData', JSON.stringify(createEventData))
      } else {
        sessionStorage.setItem('riskavaireEventData', JSON.stringify(createEventData))
      }
      
      // Navigate to event creation page
      router.push('/event-handling/create')
    }

    const handleApprove = () => {
      modalType.value = 'approve'
      showApprovalModal.value = true
    }

    const handleReject = () => {
      modalType.value = 'reject'
      showRejectModal.value = true
    }

    const handleArchive = () => {
      modalType.value = 'archive'
      showArchiveModal.value = true
    }

    const handleModalSubmit = async (comment) => {
      try {
        const userId = localStorage.getItem('user_id')
        const eventId = eventData.value?.id
        
        if (!userId || !eventId) {
          console.error('Missing user ID or event ID')
          return
        }
        
        const data = {
          user_id: userId,
          comments: comment || ''
        }
        
        let response
        if (modalType.value === 'approve') {
          response = await eventService.approveEvent(eventId, data)
        } else if (modalType.value === 'reject') {
          response = await eventService.rejectEvent(eventId, data)
        } else if (modalType.value === 'archive') {
          response = await eventService.archiveEvent(eventId, data)
        } else {
          // Handle other actions
          console.log(`${modalType.value} event:`, eventId, comment)
        }
        
        if (response && response.data.success) {
          // Update the event status locally
          eventData.value.status = modalType.value === 'approve' ? 'Approved' : 
                                 modalType.value === 'reject' ? 'Rejected' : 
                                 modalType.value === 'archive' ? 'Archived' : 'Updated'
          
          PopupService.success(response.data.message || 'Action completed successfully!', 'Success')
          
          // If archiving, navigate back to events list after a short delay
          if (modalType.value === 'archive') {
            setTimeout(() => {
              goBack()
            }, 1500) // Wait 1.5 seconds to show the success message
          }
        } else if (response) {
          PopupService.error(response.data.message || 'Action failed', 'Error')
        }
        
        showApprovalModal.value = false
        showRejectModal.value = false
        showArchiveModal.value = false
      } catch (error) {
        console.error('Error submitting action:', error)
        PopupService.error('Failed to submit action. Please try again.', 'Error')
      }
    }

    const handleModalCancel = () => {
      showApprovalModal.value = false
      showRejectModal.value = false
      showArchiveModal.value = false
    }

    const loadEventData = async () => {
      try {
        loading.value = true
        error.value = null
        
        const storedData = sessionStorage.getItem('eventDetailsData')
        if (storedData) {
          eventData.value = JSON.parse(storedData)
          console.log('Loaded event data:', eventData.value)
          console.log('DEBUG: Metadata exists:', !!eventData.value.metadata)
          console.log('DEBUG: Metadata content:', eventData.value.metadata)
          console.log('DEBUG: Metadata keys:', eventData.value.metadata ? Object.keys(eventData.value.metadata) : 'No metadata')
          
          // Fetch evidence details from backend if event has an ID and it's not an integration event
          if (eventData.value.id && !eventData.value.id.startsWith('integration_')) {
            await loadEvidenceDetails(eventData.value.id)
          }
        } else {
          console.error('No event data found in sessionStorage')
          error.value = 'No event data found. Please try clicking on an event again.'
          // Don't redirect immediately - show error message instead
        }
      } catch (error) {
        console.error('Error loading event data:', error)
        error.value = 'Failed to load event data. Please try again.'
        // Don't redirect immediately - show error message instead
      } finally {
        loading.value = false
      }
    }

    const loadEvidenceDetails = async (eventId) => {
      try {
        console.log('Loading evidence details for event:', eventId)
        const response = await fetch(`/api/events/${eventId}/evidence/details/`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        })

        if (response.ok) {
          const data = await response.json()
          if (data.success && data.evidence) {
            console.log('Evidence details loaded:', data.evidence)
            // Update the event data with detailed evidence information
            eventData.value.evidence = data.evidence
          }
        } else {
          console.error('Failed to load evidence details:', response.status)
        }
      } catch (error) {
        console.error('Error loading evidence details:', error)
      }
    }

    onMounted(async () => {
      // Fetch user permissions first
      await fetchEventPermissions()
      // Load event data
      await loadEventData()
    })

    return {
      eventData,
      showApprovalModal,
      showRejectModal,
      showArchiveModal,
      modalType,
      showActionButtons,
      loading,
      error,
      filteredEventDetails,
      filteredMetadataDetails,
      formatKey,
      formatValue,
      formatDynamicFieldLabel,
      formatDynamicFieldValue,
      getEvidenceDownloadUrl,
      downloadEvidence,
      getStatusBadgeClass,
      canEditEvents,
      canApproveEvents,
      canRejectEvents,
      canArchiveEvents,
      goBack,
      handleEdit,
      handleCreateEvent,
      handleApprove,
      handleReject,
      handleArchive,
      handleModalSubmit,
      handleModalCancel,
      loadEventData
    }
  }
}
</script>

<style>
/* Event Details Container */
.event-details-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  margin-left: -30px;
}

/* Header Section */
.event-details-header {
  flex-shrink: 0;
  padding: 24px 32px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.event-details-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.event-details-title-section {
  display: flex;
  align-items: center;
  gap: 20px;
  flex: 1;
}

.event-details-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #f8f9fa;
  color: #6b7280;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.event-details-back-btn:hover {
  background: #e9ecef;
  color: #374151;
  border-color: #d1d5db;
}

.event-details-back-icon {
  width: 16px;
  height: 16px;
}

.event-details-title-info {
  flex: 1;
}

.event-details-title {
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.event-details-subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
  font-weight: 500;
}

.event-details-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.event-details-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.event-details-action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.event-details-btn-icon {
  width: 16px;
  height: 16px;
  stroke-width: 2.5;
}

.event-details-edit-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.event-details-edit-btn:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
}

.event-details-create-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.event-details-create-btn:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

.event-details-approve-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.event-details-approve-btn:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

.event-details-reject-btn {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.event-details-reject-btn:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
}

.event-details-archive-btn {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
}

.event-details-archive-btn:hover {
  background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
}

/* Loading State */
.event-details-loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
}

.event-details-loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.event-details-spinner {
  width: 60px;
  height: 60px;
  border: 4px solid #f3f4f6;
  border-top: 4px solid #374151;
  border-radius: 50%;
  animation: event-details-spin 1s linear infinite;
}

@keyframes event-details-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.event-details-loading-spinner p {
  color: #6b7280;
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0;
}

/* Error State */
.event-details-error {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
}

.event-details-error-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  text-align: center;
  max-width: 500px;
}

.event-details-error-icon {
  color: #ef4444;
}

.event-details-error-svg {
  width: 60px;
  height: 60px;
}

.event-details-error-message {
  color: #ef4444;
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0;
}

.event-details-error-actions {
  display: flex;
  gap: 16px;
  margin-top: 10px;
}

.event-details-error-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #f3f4f6;
  color: #374151;
}

.event-details-error-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.event-details-error-retry {
  background: #3b82f6;
  color: white;
}

.event-details-error-retry:hover {
  background: #2563eb;
}

/* Content Section */
.event-details-content {
  flex: 1;
  padding: 32px;
  overflow-y: auto;
}

.event-details-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 32px;
  max-width: 1400px;
  margin: 0 auto;
}

.event-details-main {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.event-details-sidebar {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.event-details-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.event-details-section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 20px 0;
  padding-bottom: 12px;
  border-bottom: 2px solid #e5e7eb;
}

.event-details-info-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.event-details-info-item {
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 16px;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f3f4f6;
}

.event-details-info-item:last-child {
  border-bottom: none;
}

.event-details-info-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.event-details-info-value {
  font-size: 0.95rem;
  color: #1f2937;
  font-weight: 500;
}

.event-details-status-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.event-details-description {
  font-size: 1rem;
  color: #374151;
  line-height: 1.6;
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.event-details-evidence-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.event-details-evidence-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.event-details-evidence-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.event-details-evidence-name {
  font-weight: 600;
  color: #1f2937;
}

.event-details-evidence-type {
  font-size: 0.85rem;
  color: #6b7280;
}

.event-details-evidence-link {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 500;
  padding: 8px 16px;
  border: 1px solid #3b82f6;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.event-details-evidence-link:hover {
  background: #3b82f6;
  color: white;
}

.event-details-raw-data {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.event-details-raw-item {
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid #f3f4f6;
}

.event-details-raw-item:last-child {
  border-bottom: none;
}

.event-details-raw-key {
  font-size: 0.85rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: capitalize;
}

.event-details-raw-value {
  font-size: 0.9rem;
  color: #1f2937;
  word-break: break-word;
  line-height: 1.4;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .event-details-grid {
    grid-template-columns: 1fr;
    gap: 24px;
  }
}

@media (max-width: 768px) {
  .event-details-container {
    margin-left: 0;
  }
  
  .event-details-header {
    padding: 20px;
  }
  
  .event-details-header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }
  
  .event-details-title-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .event-details-header-actions {
    width: 100%;
    justify-content: flex-end;
    flex-wrap: wrap;
  }
  
  .event-details-content {
    padding: 20px;
  }
  
  .event-details-title {
    font-size: 1.5rem;
  }
  
  .event-details-info-item,
  .event-details-raw-item {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .event-details-info-label,
  .event-details-raw-key {
    font-size: 0.8rem;
  }
  
  .event-details-info-value,
  .event-details-raw-value {
    font-size: 0.85rem;
  }
}

/* Focus states for accessibility */
.event-details-back-btn:focus,
.event-details-action-btn:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}
</style>
