<template>
  <div class="events-approval-container">
    <!-- Header Section -->
    <div class="events-approval-header">
      <div class="events-approval-header-content">
        <div class="events-approval-title-section">
          <h1 class="events-approval-title">Events Approval</h1>
          <p class="events-approval-subtitle">Manage event approvals and review submissions</p>
        </div>
      </div>
    </div>

    <!-- Tabs Section -->
    <div class="events-approval-tabs">
      <div class="events-approval-tabs-container">
        <button
          @click="setActiveTab('my-events')"
          :class="[
            'events-approval-tab',
            activeTab === 'my-events' ? 'events-approval-tab-active' : 'events-approval-tab-inactive'
          ]"
        >
          <div class="events-approval-tab-content">
            <span class="events-approval-tab-title">My Events</span>
          </div>
        </button>
        <button
          @click="setActiveTab('for-review')"
          :class="[
            'events-approval-tab',
            activeTab === 'for-review' ? 'events-approval-tab-active' : 'events-approval-tab-inactive'
          ]"
        >
          <div class="events-approval-tab-content">
            <span class="events-approval-tab-title">Events for Review</span>
            <span v-if="eventsForReview.length > 0" class="events-approval-tab-badge">
              {{ eventsForReview.length }}
            </span>
          </div>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="events-approval-loading">
      <div class="events-approval-loading-content">
        <div class="events-approval-loading-spinner"></div>
        <p class="events-approval-loading-text">Loading events...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="events-approval-error">
      <div class="events-approval-error-content">
        <div class="events-approval-error-icon">
          <svg class="events-approval-error-svg" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="events-approval-error-details">
          <h3 class="events-approval-error-title">Error loading events</h3>
          <div class="events-approval-error-message">{{ error }}</div>
        </div>
      </div>
    </div>

    <!-- Tab Content -->
    <div v-else-if="activeTab === 'my-events'" class="events-approval-content">
      <!-- Rejected Events -->
      <div v-if="rejectedEvents.length > 0" class="events-approval-section">
        <div class="events-approval-section-header">
          <h2 class="events-approval-section-title events-approval-section-title-rejected">
            Rejected ({{ rejectedEvents.length }})
          </h2>
        </div>
        <div class="events-approval-table-container">
          <div class="events-approval-table-wrapper">
            <table class="events-approval-table">
              <thead class="events-approval-table-header">
                <tr>
                  <th class="events-approval-table-th events-approval-title-col">EVENT TITLE</th>
                  <th class="events-approval-table-th events-approval-id-col">ID</th>
                  <th class="events-approval-table-th events-approval-framework-col">FRAMEWORK</th>
                  <th class="events-approval-table-th events-approval-category-col">CATEGORY</th>
                  <th class="events-approval-table-th events-approval-owner-col">OWNER</th>
                  <th class="events-approval-table-th events-approval-status-col">STATUS</th>
                  <th class="events-approval-table-th events-approval-created-col">CREATED</th>
                </tr>
              </thead>
              <tbody class="events-approval-table-body">
                <tr v-for="(event, index) in rejectedEvents" :key="event.id" 
                    :class="`events-approval-table-row ${index % 2 === 0 ? 'events-row-even' : 'events-row-odd'}`">
                  <td class="events-approval-table-td events-approval-title-cell" data-label="Event Title">
                    <button
                      @click="setSelectedEvent(event)"
                      class="events-approval-title-link"
                    >
                      {{ event.title }}
                    </button>
                  </td>
                  <td class="events-approval-table-td events-approval-id-cell" data-label="ID">
                    <button
                      @click="setSelectedEvent(event)"
                      class="events-approval-id-link"
                    >
                      {{ event.id }}
                    </button>
                  </td>
                  <td class="events-approval-table-td events-approval-framework-cell" data-label="Framework">
                    <div class="events-approval-framework-status">
                      <span class="events-approval-status-text events-approval-framework-text">
                        {{ event.framework }}
                      </span>
                    </div>
                  </td>
                  <td class="events-approval-table-td events-approval-category-cell" data-label="Category">
                    {{ event.category }}
                  </td>
                  <td class="events-approval-table-td events-approval-owner-cell" data-label="Owner">
                    {{ event.owner }}
                  </td>
                  <td class="events-approval-table-td events-approval-status-cell" data-label="Status">
                    <div class="events-approval-status-display">
                      <span :class="`events-approval-status-dot ${getStatusColor(event.status)}`"></span>
                      <span :class="`events-approval-status-text ${getStatusColor(event.status)}`">
                        {{ event.status }}
                      </span>
                    </div>
                  </td>
                  <td class="events-approval-table-td events-approval-created-cell" data-label="Created">
                    {{ event.created_at }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Pending Review -->
      <div class="events-approval-section">
        <div class="events-approval-section-header">
          <h2 class="events-approval-section-title events-approval-section-title-pending">
            Pending Review ({{ pendingEvents.length }})
          </h2>
        </div>
        <div class="events-approval-table-container">
          <div class="events-approval-table-wrapper">
            <table class="events-approval-table">
              <thead class="events-approval-table-header">
                <tr>
                  <th class="events-approval-table-th events-approval-title-col">EVENT TITLE</th>
                  <th class="events-approval-table-th events-approval-id-col">ID</th>
                  <th class="events-approval-table-th events-approval-framework-col">FRAMEWORK</th>
                  <th class="events-approval-table-th events-approval-category-col">CATEGORY</th>
                  <th class="events-approval-table-th events-approval-owner-col">OWNER</th>
                  <th class="events-approval-table-th events-approval-status-col">STATUS</th>
                  <th class="events-approval-table-th events-approval-created-col">CREATED</th>
                </tr>
              </thead>
              <tbody class="events-approval-table-body">
                <tr v-for="(event, index) in pendingEvents" :key="event.id" 
                    :class="`events-approval-table-row ${index % 2 === 0 ? 'events-row-even' : 'events-row-odd'}`">
                  <td class="events-approval-table-td events-approval-title-cell" data-label="Event Title">
                    <button
                      @click="setSelectedEvent(event)"
                      class="events-approval-title-link"
                    >
                      {{ event.title }}
                    </button>
                  </td>
                  <td class="events-approval-table-td events-approval-id-cell" data-label="ID">
                    <button
                      @click="setSelectedEvent(event)"
                      class="events-approval-id-link"
                    >
                      {{ event.id }}
                    </button>
                  </td>
                  <td class="events-approval-table-td events-approval-framework-cell" data-label="Framework">
                    <div class="events-approval-framework-status">
                      <span class="events-approval-status-text events-approval-framework-text">
                        {{ event.framework }}
                      </span>
                    </div>
                  </td>
                  <td class="events-approval-table-td events-approval-category-cell" data-label="Category">
                    {{ event.category }}
                  </td>
                  <td class="events-approval-table-td events-approval-owner-cell" data-label="Owner">
                    {{ event.owner }}
                  </td>
                  <td class="events-approval-table-td events-approval-status-cell" data-label="Status">
                    <div class="events-approval-status-display">
                      <span :class="`events-approval-status-dot ${getStatusColor(event.status)}`"></span>
                      <span :class="`events-approval-status-text ${getStatusColor(event.status)}`">
                        {{ event.status }}
                      </span>
                    </div>
                  </td>
                  <td class="events-approval-table-td events-approval-created-cell" data-label="Created">
                    {{ event.created_at }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Approved -->
      <div class="events-approval-section">
        <div class="events-approval-section-header">
          <h2 class="events-approval-section-title events-approval-section-title-approved">
            Approved ({{ approvedEvents.length }})
          </h2>
        </div>
        <div class="events-approval-table-container">
          <div class="events-approval-table-wrapper">
            <table class="events-approval-table">
              <thead class="events-approval-table-header">
                <tr>
                  <th class="events-approval-table-th events-approval-title-col">EVENT TITLE</th>
                  <th class="events-approval-table-th events-approval-id-col">ID</th>
                  <th class="events-approval-table-th events-approval-framework-col">FRAMEWORK</th>
                  <th class="events-approval-table-th events-approval-category-col">CATEGORY</th>
                  <th class="events-approval-table-th events-approval-owner-col">OWNER</th>
                  <th class="events-approval-table-th events-approval-status-col">STATUS</th>
                  <th class="events-approval-table-th events-approval-created-col">CREATED</th>
                </tr>
              </thead>
              <tbody class="events-approval-table-body">
                <tr v-for="(event, index) in approvedEvents" :key="event.id" 
                    :class="`events-approval-table-row ${index % 2 === 0 ? 'events-row-even' : 'events-row-odd'}`">
                  <td class="events-approval-table-td events-approval-title-cell" data-label="Event Title">
                    <button
                      @click="setSelectedEvent(event)"
                      class="events-approval-title-link"
                    >
                      {{ event.title }}
                    </button>
                  </td>
                  <td class="events-approval-table-td events-approval-id-cell" data-label="ID">
                    <button
                      @click="setSelectedEvent(event)"
                      class="events-approval-id-link"
                    >
                      {{ event.id }}
                    </button>
                  </td>
                  <td class="events-approval-table-td events-approval-framework-cell" data-label="Framework">
                    <div class="events-approval-framework-status">
                      <span class="events-approval-status-text events-approval-framework-text">
                        {{ event.framework }}
                      </span>
                    </div>
                  </td>
                  <td class="events-approval-table-td events-approval-category-cell" data-label="Category">
                    {{ event.category }}
                  </td>
                  <td class="events-approval-table-td events-approval-owner-cell" data-label="Owner">
                    {{ event.owner }}
                  </td>
                  <td class="events-approval-table-td events-approval-status-cell" data-label="Status">
                    <div class="events-approval-status-display">
                      <span :class="`events-approval-status-dot ${getStatusColor(event.status)}`"></span>
                      <span :class="`events-approval-status-text ${getStatusColor(event.status)}`">
                        {{ event.status }}
                      </span>
                    </div>
                  </td>
                  <td class="events-approval-table-td events-approval-created-cell" data-label="Created">
                    {{ event.created_at }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="events-approval-content">
      <div class="events-approval-section">
        <div class="events-approval-section-header">
          <h2 class="events-approval-section-title events-approval-section-title-review">
            Events Awaiting Your Review ({{ eventsForReview.length }})
          </h2>
        </div>
        
        <!-- Empty State for Events for Review -->
        <div v-if="eventsForReview.length === 0" class="events-approval-empty">
          <div class="events-approval-empty-content">
            <div class="events-approval-empty-icon">
              <svg class="events-approval-empty-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
            </div>
            <h3 class="events-approval-empty-title">No events for review</h3>
            <p class="events-approval-empty-subtitle">There are no events currently awaiting your review.</p>
          </div>
        </div>
        
        <div v-else class="events-approval-table-container">
          <div class="events-approval-table-wrapper">
            <table class="events-approval-table">
              <thead class="events-approval-table-header">
                <tr>
                  <th class="events-approval-table-th events-approval-title-col">EVENT TITLE</th>
                  <th class="events-approval-table-th events-approval-id-col">ID</th>
                  <th class="events-approval-table-th events-approval-framework-col">FRAMEWORK</th>
                  <th class="events-approval-table-th events-approval-category-col">CATEGORY</th>
                  <th class="events-approval-table-th events-approval-owner-col">OWNER</th>
                  <th class="events-approval-table-th events-approval-status-col">STATUS</th>
                  <th class="events-approval-table-th events-approval-created-col">CREATED</th>
                  <th class="events-approval-table-th events-approval-actions-col">ACTIONS</th>
                </tr>
              </thead>
              <tbody class="events-approval-table-body">
                <tr v-for="(event, index) in eventsForReview" :key="event.id" 
                    :class="`events-approval-table-row ${index % 2 === 0 ? 'events-row-even' : 'events-row-odd'}`">
                  <td class="events-approval-table-td events-approval-title-cell" data-label="Event Title">
                    <button
                      @click="setSelectedEvent(event)"
                      class="events-approval-title-link"
                    >
                      {{ event.title }}
                    </button>
                  </td>
                  <td class="events-approval-table-td events-approval-id-cell" data-label="ID">
                    <button
                      @click="setSelectedEvent(event)"
                      class="events-approval-id-link"
                    >
                      {{ event.id }}
                    </button>
                  </td>
                  <td class="events-approval-table-td events-approval-framework-cell" data-label="Framework">
                    <div class="events-approval-framework-status">
                      <span class="events-approval-status-text events-approval-framework-text">
                        {{ event.framework }}
                      </span>
                    </div>
                  </td>
                  <td class="events-approval-table-td events-approval-category-cell" data-label="Category">
                    {{ event.category }}
                  </td>
                  <td class="events-approval-table-td events-approval-owner-cell" data-label="Owner">
                    {{ event.owner }}
                  </td>
                  <td class="events-approval-table-td events-approval-status-cell" data-label="Status">
                    <div class="events-approval-status-display">
                      <span :class="`events-approval-status-dot ${getStatusColor(event.status)}`"></span>
                      <span :class="`events-approval-status-text ${getStatusColor(event.status)}`">
                        {{ event.status }}
                      </span>
                    </div>
                  </td>
                  <td class="events-approval-table-td events-approval-created-cell" data-label="Created">
                    {{ event.created_at }}
                  </td>
                  <td class="events-approval-table-td events-approval-actions-cell" data-label="Actions">
                    <div class="events-approval-actions">
                       <button
                         @click="handleApprovalAction('approve', event)"
                         class="events-approval-btn-approve-new"
                         title="Approve"
                       >
                         Approve
                       </button>
                       <button
                         @click="handleApprovalAction('reject', event)"
                         class="events-approval-btn-reject-new"
                         title="Reject"
                       >
                         Reject
                       </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Event View Popup -->
    <EventViewPopup
      v-if="selectedEvent"
      :event="selectedEvent"
      @close="setSelectedEvent(null)"
      @edit="handleEdit"
      @attach-evidence="handleAttachEvidence"
      @approve="() => handleApprovalAction('approve', selectedEvent)"
      @reject="() => handleApprovalAction('reject', selectedEvent)"
      @archive="handleArchive"
    />


    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { eventService } from '../../services/api'
import EventViewPopup from './EventViewPopup.vue'
import { PopupService } from '../../modules/popus/popupService'
import PopupModal from '../../modules/popus/PopupModal.vue'
import axios from 'axios'
import eventDataService from '../../services/eventService' // NEW: Centralized event data service

export default {
  name: 'EventsApproval',
  components: {
    EventViewPopup,
    PopupModal
  },
  setup() {
    const activeTab = ref('my-events')
    const selectedEvent = ref(null)
    const approvalAction = ref('approve')
    const events = ref([])
    const loading = ref(false)
    const error = ref(null)
    const selectedFrameworkFromSession = ref(null)

    // Filter events for current user
    const currentUserId = localStorage.getItem('user_id')
    const myEvents = computed(() => events.value.filter(event => event.owner_id == currentUserId))
    const eventsForReview = computed(() => {
      // More inclusive filtering for events for review
      const filtered = events.value.filter(event => {
        // Show events that are assigned to current user as reviewer
        const isAssignedToMe = event.reviewer_id == currentUserId
        // OR show events with no reviewer assigned (for admin users)
        const hasNoReviewer = !event.reviewer_id || event.reviewer_id === null
        // AND status should be reviewable
        const isReviewableStatus = event.status === 'Pending Review' || 
                                  event.status === 'Pending Approval' || 
                                  event.status === 'Under Review'
        
        return (isAssignedToMe || hasNoReviewer) && isReviewableStatus
      })
      
      console.log('Events for review filtering:', {
        totalEvents: events.value.length,
        currentUserId: currentUserId,
        filteredCount: filtered.length,
        sampleFiltered: filtered.slice(0, 2)
      })
      
      return filtered
    })

    const rejectedEvents = computed(() => myEvents.value.filter(event => event.status === 'Rejected'))
    const pendingEvents = computed(() => myEvents.value.filter(event => event.status === 'Pending Review' || event.status === 'Pending Approval'))
    const approvedEvents = computed(() => myEvents.value.filter(event => event.status === 'Approved'))

    const setActiveTab = (tab) => {
      activeTab.value = tab
    }

    const setSelectedEvent = (event) => {
      selectedEvent.value = event
    }

    const handleApprovalAction = (action, event) => {
      approvalAction.value = action
      selectedEvent.value = event
      
      // Use popup module for approval actions
      if (action === 'approve') {
        PopupService.comment(
          `Please provide approval comments for event: "${event.title}"`,
          'Approve Event',
          (comment) => handleApprovalSubmit(comment)
        )
      } else if (action === 'reject') {
        PopupService.comment(
          `Please provide rejection reason for event: "${event.title}"`,
          'Reject Event',
          (comment) => handleApprovalSubmit(comment)
        )
      } else if (action === 'archive') {
        PopupService.confirm(
          `Are you sure you want to archive event: "${event.title}"?`,
          'Archive Event',
          () => handleApprovalSubmit(''),
          () => console.log('Archive cancelled')
        )
      }
    }



    const handleApprovalSubmit = async (comment) => {
      try {
        console.log('Handling approval submit:', { action: approvalAction.value, eventId: selectedEvent.value?.id, comment })
        
        if (!selectedEvent.value) {
          console.error('No selected event for approval')
          return
        }

        const eventId = selectedEvent.value.id
        const userId = localStorage.getItem('user_id')
        
        if (!userId) {
          console.error('No user ID found')
          return
        }

        const data = {
          user_id: userId,
          comments: comment || ''
        }

        let response
        if (approvalAction.value === 'approve') {
          response = await eventService.approveEvent(eventId, data)
        } else if (approvalAction.value === 'reject') {
          response = await eventService.rejectEvent(eventId, data)
        } else if (approvalAction.value === 'archive') {
          // Handle archive action
          console.log('Archive action not implemented yet')
          return
        }

        if (response && response.data.success) {
          // Show success message using popup module
          const actionText = approvalAction.value === 'approve' ? 'approved' : 
                           approvalAction.value === 'reject' ? 'rejected' : 'archived'
          const message = `Event "${selectedEvent.value?.title}" has been ${actionText} successfully!`
          const title = approvalAction.value === 'approve' ? 'Event Approved' : 
                       approvalAction.value === 'reject' ? 'Event Rejected' : 'Event Archived'
          
          // Use popup module for success message
          PopupService.success(message, title)
          
          // Refresh events list
          await fetchEvents()
        } else if (response) {
          // Show error message using popup module
          const errorMessage = response.data.message || 'Action failed'
          PopupService.error(errorMessage, 'Error')
        }
      } catch (error) {
        console.error('Error submitting approval:', error)
        // Show error message using popup module
        const errorMessage = error.response?.data?.message || error.message || 'Failed to submit action'
        PopupService.error(errorMessage, 'Error')
      }
    }

    const handleEdit = () => {
      console.log('Edit event:', selectedEvent.value.id)
      selectedEvent.value = null
    }

    const handleAttachEvidence = () => {
      console.log('Attach evidence for event:', selectedEvent.value.id)
      selectedEvent.value = null
    }

    const handleArchive = () => {
      console.log('Archive event:', selectedEvent.value.id)
      selectedEvent.value = null
    }

    // Check for selected framework from session (similar to other modules)
    const checkSelectedFrameworkFromSession = async () => {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in EventsApproval...')
        const response = await axios.get('/api/frameworks/get-selected/', {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        })
        
        console.log('🔍 DEBUG: Framework response in EventsApproval:', response.data)
        
        if (response.data && response.data.frameworkId) {
          const frameworkIdFromSession = response.data.frameworkId.toString()
          console.log('✅ DEBUG: Found selected framework in session for EventsApproval:', frameworkIdFromSession)
          
          // Set the selected framework from session
          selectedFrameworkFromSession.value = frameworkIdFromSession
          console.log('📊 DEBUG: Events are now filtered by framework:', frameworkIdFromSession)
          console.log('📊 DEBUG: selectedFrameworkFromSession.value set to:', selectedFrameworkFromSession.value)
        } else {
          console.log('ℹ️ DEBUG: No framework filter active - showing all events')
          selectedFrameworkFromSession.value = null
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework in EventsApproval:', error)
        selectedFrameworkFromSession.value = null
      }
    }

    const fetchEvents = async () => {
      try {
        loading.value = true
        error.value = null
        
        console.log('[EventsApproval] Checking for cached event data...')
        
        // ==========================================
        // NEW: Check if data is already cached from HomeView prefetch
        // ==========================================
        if (eventDataService.hasValidCache()) {
          console.log('[EventsApproval] ✅ Using cached event data from HomeView prefetch')
          events.value = eventDataService.getData('events') || []
          console.log('Events loaded from cache:', events.value.length)
          console.log('Current user ID:', currentUserId)
          console.log('Sample events:', events.value.slice(0, 3))
          
          // Debug filtering
          const eventsForReviewDebug = events.value.filter(event => 
            event.reviewer_id == currentUserId && (event.status === 'Pending Review' || event.status === 'Pending Approval')
          )
          console.log('Events for review (debug):', eventsForReviewDebug.length)
          console.log('Events with reviewer_id matching current user:', events.value.filter(event => event.reviewer_id == currentUserId))
          console.log('Events with Pending Review status:', events.value.filter(event => event.status === 'Pending Review'))
          console.log('Events with Pending Approval status:', events.value.filter(event => event.status === 'Pending Approval'))
          loading.value = false
          return
        }
        
        // ==========================================
        // Fallback: If cache is empty, wait for prefetch or fetch directly
        // ==========================================
        console.log('[EventsApproval] No cache found, checking for ongoing prefetch...')
        
        if (window.eventDataFetchPromise) {
          console.log('[EventsApproval] ⏳ Waiting for ongoing prefetch to complete...')
          await window.eventDataFetchPromise
          events.value = eventDataService.getData('events') || []
          console.log('Events loaded from prefetch:', events.value.length)
          loading.value = false
          return
        }
        
        // Last resort: Fetch from API
        console.log('[EventsApproval] 🔄 Fetching event data from API (cache miss)...')
        const response = await eventService.getEventsList()
        console.log('Events response:', response)
        if (response.data.success) {
          events.value = response.data.events
          // Cache the fetched data for future use
          eventDataService.setData('events', events.value)
          console.log('Events loaded from API:', events.value.length)
          console.log('Current user ID:', currentUserId)
          console.log('Sample events:', events.value.slice(0, 3))
          
          // Debug filtering
          const eventsForReviewDebug = events.value.filter(event => 
            event.reviewer_id == currentUserId && (event.status === 'Pending Review' || event.status === 'Pending Approval')
          )
          console.log('Events for review (debug):', eventsForReviewDebug.length)
          console.log('Events with reviewer_id matching current user:', events.value.filter(event => event.reviewer_id == currentUserId))
          console.log('Events with Pending Review status:', events.value.filter(event => event.status === 'Pending Review'))
          console.log('Events with Pending Approval status:', events.value.filter(event => event.status === 'Pending Approval'))
        } else {
          PopupService.error(response.data.message || 'Failed to fetch events', 'Error')
          console.error('API returned error:', response.data.message)
        }
      } catch (err) {
        console.error('Error fetching events:', err)
        console.error('Error details:', {
          message: err.message,
          response: err.response?.data,
          status: err.response?.status,
          config: err.config
        })
        
        // Provide more specific error messages using popup module
        if (err.code === 'ERR_NETWORK') {
          PopupService.error('Cannot connect to server. Please make sure the backend server is running on port 8000.', 'Network Error')
        } else if (err.response?.status === 404) {
          PopupService.error('Events endpoint not found. Please check the API configuration.', 'API Error')
        } else if (err.response?.status === 500) {
          PopupService.error('Server error. Please check the backend logs.', 'Server Error')
        } else {
          PopupService.error(`Failed to fetch events: ${err.message}`, 'Error')
        }
      } finally {
        loading.value = false
      }
    }

    const getStatusColor = (status) => {
      switch (status) {
        case 'Pending Review': return 'events-approval-status-pending-review'
        case 'Pending Approval': return 'events-approval-status-pending-approval'
        case 'Under Review': return 'events-approval-status-under-review'
        case 'Approved': return 'events-approval-status-approved'
        case 'Rejected': return 'events-approval-status-rejected'
        case 'Draft': return 'events-approval-status-draft'
        default: return 'events-approval-status-default'
      }
    }

    onMounted(async () => {
      // Check for framework selection from session
      await checkSelectedFrameworkFromSession()
      
      // Then fetch events
      await fetchEvents()
    })

    return {
      activeTab,
      selectedEvent,
      approvalAction,
      events,
      loading,
      error,
      selectedFrameworkFromSession,
      myEvents,
      eventsForReview,
      rejectedEvents,
      pendingEvents,
      approvedEvents,
      setActiveTab,
      setSelectedEvent,
      handleApprovalAction,
      handleApprovalSubmit,
      handleEdit,
      handleAttachEvidence,
      handleArchive,
      getStatusColor,
      fetchEvents
    }
  }
}
</script>

<style>
/* 
 * Events Approval Component Styles
 * All class names are prefixed with 'events-approval-' to prevent CSS conflicts with other pages
 * Title cells are configured to wrap to exactly 2 lines with ellipsis
 * All table cells are aligned to top for consistent vertical alignment
 */

/* Events Approval Container - Single container for whole page */
.events-approval-container {
  padding: 10px 5px;
  background: transparent;
  padding-top: 40px;
  border-radius: 0;
  box-shadow: none;
  border: none;
  min-height: 100vh;
  margin: 0;
  margin-left: -20px;
  max-width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
  width: 100%;
  position: relative;
}

/* Scoped wrapper to prevent CSS conflicts with other pages */
.events-approval-container * {
  box-sizing: border-box;
}

/* Events Approval Header */
.events-approval-header {
  margin-bottom: 12px;
}

.events-approval-header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.events-approval-title-section {
  flex: 1;
}

.events-approval-title {
  font-size: 1.7rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.events-approval-subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
  font-weight: 500;
}

/* Events Approval Tabs */
.events-approval-tabs {
  margin-bottom: 12px;
  display: flex;
  border-bottom: none;
}

.events-approval-tabs-container {
  display: flex;
}

.events-approval-tab {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  border: none;
  background: none;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  border-bottom: 2px solid transparent;
  outline: none;
  box-shadow: none;
}

.events-approval-tab:hover {
  background: none;
}

.events-approval-tab-active {
  background: none;
  border-bottom: 2px solid #3b82f6;
}

.events-approval-tab-inactive {
  color: #6b7280;
  border-bottom: 2px solid transparent;
}

.events-approval-tab-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.events-approval-tab-title {
  font-size: 0.95rem;
  font-weight: 600;
  transition: color 0.3s ease;
}

.events-approval-tab-active .events-approval-tab-title {
  color: #3b82f6;
}

.events-approval-tab-inactive .events-approval-tab-title {
  color: #6b7280;
}

.events-approval-tab-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

.events-approval-tab-active .events-approval-tab-badge {
  background: #3b82f6;
  color: #ffffff;
}

.events-approval-tab-inactive .events-approval-tab-badge {
  background: #e5e7eb;
  color: #6b7280;
}

/* Loading State */
.events-approval-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
}

.events-approval-loading-content {
  text-align: center;
}

.events-approval-loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: events-approval-spin 1s linear infinite;
  margin: 0 auto 16px;
}

.events-approval-loading-text {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
}

/* Error State */
.events-approval-error {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fecaca;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.events-approval-error-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.events-approval-error-icon {
  flex-shrink: 0;
}

.events-approval-error-svg {
  width: 24px;
  height: 24px;
  color: #ef4444;
}

.events-approval-error-details {
  flex: 1;
}

.events-approval-error-title {
  font-size: 1rem;
  font-weight: 600;
  color: #dc2626;
  margin: 0 0 8px 0;
}

.events-approval-error-message {
  font-size: 0.9rem;
  color: #991b1b;
  margin: 0;
}

/* Empty State */
.events-approval-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
}

.events-approval-empty-content {
  text-align: center;
}

.events-approval-empty-icon {
  margin-bottom: 16px;
}

.events-approval-empty-svg {
  width: 48px;
  height: 48px;
  color: #9ca3af;
  margin: 0 auto;
}

.events-approval-empty-title {
  font-size: 1.1rem;
  color: #6b7280;
  margin: 0 0 8px 0;
  font-weight: 600;
}

.events-approval-empty-subtitle {
  font-size: 0.9rem;
  color: #9ca3af;
  margin: 0;
}

/* Events Approval Content */
.events-approval-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Events Approval Section */
.events-approval-section {
  margin-bottom: 12px;
}

.events-approval-section-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}


.events-approval-section-title {
  font-size: 1rem;
  font-weight: 700;
  margin: 0;
}

.events-approval-section-title-rejected {
  color: #dc2626;
}

.events-approval-section-title-pending {
  color: #d97706;
}

.events-approval-section-title-approved {
  color: #16a34a;
}

.events-approval-section-title-review {
  color: #1f2937;
}

/* Events Approval Table */
.events-approval-table-container {
  overflow: hidden;
  border-radius: 0;
  border: none;
  max-width: 100%;
  width: 100%;
  position: relative;
}

.events-approval-table-wrapper {
  overflow-x: hidden;
  overflow-y: auto;
  max-height: calc(100vh - 200px);
  position: relative;
}

.events-approval-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 100%;
  table-layout: fixed;
  position: relative;
}

/* Ensure table cells don't inherit styles from other pages */
.events-approval-container .events-approval-table {
  border-spacing: 0;
}

/* Force title link to wrap to 2 lines */
.events-approval-container .events-approval-title-link {
  display: -webkit-box !important;
  -webkit-line-clamp: 2 !important;
  -webkit-box-orient: vertical !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  line-height: 1.5 !important;
  max-height: 2.55em !important;
  white-space: normal !important;
  word-wrap: break-word !important;
  word-break: break-word !important;
  overflow-wrap: break-word !important;
}

.events-approval-table-header {
  background: #ffffff;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.events-approval-table-th {
  padding: 12px 12px;
  text-align: left;
  font-size: 0.75rem;
  font-weight: 700;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid #e5e7eb;
  white-space: nowrap;
  vertical-align: top;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  background: #ffffff;
}

.events-approval-title-col {
  width: 240px;
  min-width: 240px;
  max-width: 240px;
  word-wrap: break-word;
  word-break: break-word;
}

.events-approval-id-col {
  width: 50px;
  min-width: 50px;
  max-width: 50px;
  word-wrap: break-word;
}

.events-approval-framework-col {
  width: 120px;
  min-width: 120px;
  max-width: 120px;
  word-wrap: break-word;
  white-space: normal;
}

.events-approval-category-col {
  width: 110px;
  min-width: 110px;
  max-width: 110px;
  word-wrap: break-word;
}

.events-approval-owner-col {
  width: 110px;
  min-width: 110px;
  max-width: 110px;
  word-wrap: break-word;
}

.events-approval-status-col {
  width: 130px;
  min-width: 130px;
  max-width: 130px;
  word-wrap: break-word;
}

.events-approval-created-col {
  width: 130px;
  min-width: 130px;
  max-width: 130px;
  word-wrap: break-word;
}

.events-approval-actions-col {
  width: 140px;
  min-width: 140px;
  max-width: 140px;
  word-wrap: break-word;
}

.events-approval-table-body {
  background: transparent;
  position: relative;
  z-index: 1;
  isolation: isolate;
}

.events-approval-table-row {
  transition: all 0.2s ease;
  border-bottom: 1px solid #e5e7eb;
  position: relative;
  z-index: 1;
}

.events-approval-table-row:hover {
  background: #f9fafb !important;
  box-shadow: none !important;
}

.events-row-even {
  background: transparent;
}

.events-row-odd {
  background: transparent;
}

.events-approval-table-td {
  padding: 12px 12px;
  font-size: 0.85rem;
  color: #374151;
  vertical-align: middle;
  text-align: left;
  position: relative;
  z-index: 1;
  background-color: inherit;
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: break-word;
  overflow: hidden;
}

.events-approval-status-cell .events-approval-status-text {
  color: inherit !important;
}

.events-approval-title-cell {
  text-align: left;
  vertical-align: top;
  word-wrap: break-word;
  overflow: visible;
  position: static;
  z-index: 1;
  width: 240px;
  max-width: 240px;
}

.events-approval-title-link {
  color: #1f2937 !important;
  text-decoration: none !important;
  font-weight: 500 !important;
  font-size: 0.85rem;
  cursor: default;
  transition: all 0.2s ease;
  text-align: left !important;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
  max-height: 2.55em;
  width: 100%;
  max-width: 100%;
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  padding: 0 !important;
  line-height: 1.3;
  word-wrap: break-word;
  white-space: normal;
  box-shadow: none !important;
  outline: none;
  position: relative;
  z-index: 1;
  overflow: visible;
}

.events-approval-title-link:hover {
  color: #1f2937 !important;
  text-decoration: none !important;
  background: transparent !important;
  background-color: transparent !important;
}

.events-approval-id-cell {
  text-align: left;
  vertical-align: top;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 600;
  width: 50px;
  max-width: 50px;
}

.events-approval-id-link {
  color: #6b7280 !important;
  text-decoration: none;
  font-weight: 600;
  cursor: default;
  transition: all 0.2s ease;
  text-align: left;
  display: block;
  width: 100%;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  border-radius: 0 !important;
  margin: 0 0 0 -30px !important;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.75rem;
  line-height: 1.3;
  vertical-align: top;
}

.events-approval-id-link:hover {
  color: #6b7280 !important;
  text-decoration: none !important;
}

.events-approval-framework-cell {
  text-align: left;
  vertical-align: middle;
  word-wrap: break-word;
  word-break: break-word;
  white-space: normal;
  overflow-wrap: break-word;
}

.events-approval-framework-status {
  display: block;
  vertical-align: middle;
  word-wrap: break-word;
  word-break: break-word;
  white-space: normal;
  overflow-wrap: break-word;
  max-width: 100%;
}

.events-approval-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.events-approval-status-text {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  line-height: 1;
  white-space: nowrap;
  display: inline-block;
  visibility: visible !important;
  opacity: 1 !important;
}

/* Override font-weight for framework text specifically */
.events-approval-framework-status .events-approval-status-text.events-approval-framework-text {
  font-weight: normal !important;
  text-transform: none !important;
}


.events-approval-framework-text {
  color: #60A5FA;
  word-wrap: break-word;
  word-break: break-word;
  white-space: normal;
  overflow-wrap: break-word;
  display: block;
  max-width: 100%;
  font-weight: normal;
}

.events-approval-category-cell {
  font-weight: 500;
  color: #6b7280;
  vertical-align: middle;
}

.events-approval-owner-cell {
  font-weight: 500;
  color: #374151;
  vertical-align: middle;
}

.events-approval-status-cell {
  text-align: left;
  vertical-align: middle;
}

.events-approval-status-display {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-height: 20px;
}

.events-approval-status-display .events-approval-status-text {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
  margin: 0 !important;
  font-size: 0.75rem !important;
  font-weight: 600 !important;
  line-height: 1 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
}

/* Status dot colors */
.events-approval-status-pending-review {
  background-color: #FBBF24;
}

.events-approval-status-pending-approval {
  background-color: #FBBF24;
}

.events-approval-status-under-review {
  background-color: #60A5FA;
}

.events-approval-status-approved {
  background-color: #34D399;
}

.events-approval-status-rejected {
  background-color: #F87171;
}

.events-approval-status-draft {
  background-color: #9CA3AF;
}

.events-approval-status-default {
  background-color: #9CA3AF;
}

/* Status text colors - with fallback */
.events-approval-status-text {
  color: #000000 !important; /* Fallback color */
}

.events-approval-status-pending-review.events-approval-status-text {
  color: #FBBF24 !important;
}

.events-approval-status-pending-approval.events-approval-status-text {
  color: #FBBF24 !important;
}

.events-approval-status-under-review.events-approval-status-text {
  color: #60A5FA !important;
}

.events-approval-status-approved.events-approval-status-text {
  color: #34D399 !important;
}

.events-approval-status-rejected.events-approval-status-text {
  color: #F87171 !important;
}

.events-approval-status-draft.events-approval-status-text {
  color: #9CA3AF !important;
}

.events-approval-status-default.events-approval-status-text {
  color: #9CA3AF !important;
}

.events-approval-created-cell {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.75rem;
  color: #6b7280;
  vertical-align: middle;
}

.events-approval-actions-cell {
  text-align: center;
  vertical-align: middle;
}

.events-approval-actions {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 3px;
}

.events-approval-action-btn {
  display: inline-block;
  padding: 0;
  border: none;
  background: transparent !important;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.2px;
  text-decoration: none;
  white-space: nowrap;
  box-shadow: none !important;
}

.events-approval-action-btn:hover {
  opacity: 0.8;
}

.events-approval-action-btn-approve {
  color: #10b981 !important;
}

.events-approval-action-btn-approve:hover {
  color: #059669 !important;
}

.events-approval-action-btn-reject {
  color: #ef4444 !important;
}

.events-approval-action-btn-reject:hover {
  color: #dc2626 !important;
}

/* New button styles - text only, no containers */
.events-approval-container .events-approval-btn-approve-new,
.events-approval-container button.events-approval-btn-approve-new {
  display: inline-block !important;
  padding: 0 !important;
  margin: 0 !important;
  border: none !important;
  background: transparent !important;
  background-color: transparent !important;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.85rem !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0px !important;
  text-decoration: none !important;
  white-space: nowrap !important;
  box-shadow: none !important;
  outline: none !important;
  color: #10b981 !important;
  text-align: center !important;
  -webkit-appearance: none !important;
  -moz-appearance: none !important;
  appearance: none !important;
}

.events-approval-container .events-approval-btn-approve-new:hover,
.events-approval-container button.events-approval-btn-approve-new:hover {
  color: #059669 !important;
  text-decoration: underline !important;
  background: transparent !important;
  background-color: transparent !important;
}

.events-approval-container .events-approval-btn-reject-new,
.events-approval-container button.events-approval-btn-reject-new {
  display: inline-block !important;
  padding: 0 !important;
  margin: 0 !important;
  border: none !important;
  background: transparent !important;
  background-color: transparent !important;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.85rem !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0px !important;
  text-decoration: none !important;
  white-space: nowrap !important;
  box-shadow: none !important;
  outline: none !important;
  color: #ef4444 !important;
  text-align: center !important;
  -webkit-appearance: none !important;
  -moz-appearance: none !important;
  appearance: none !important;
}

.events-approval-container .events-approval-btn-reject-new:hover,
.events-approval-container button.events-approval-btn-reject-new:hover {
  color: #dc2626 !important;
  text-decoration: underline !important;
  background: transparent !important;
  background-color: transparent !important;
}


/* Responsive Design */
@media (max-width: 768px) {
  .events-approval-container {
    margin-left: 0;
    padding: 16px;
  }
  
  .events-approval-title {
    font-size: 1.5rem;
  }
  
  .events-approval-tab {
    padding: 12px 16px;
  }
  
  .events-approval-tab-content {
    flex-direction: column;
    gap: 4px;
  }
  
  .events-approval-section-header {
    margin-bottom: 12px;
  }
  
  .events-approval-section-title {
    font-size: 1.1rem;
  }
  
  .events-approval-table-th,
  .events-approval-table-td {
    padding: 12px 8px;
  }
  
  .events-approval-actions {
    flex-direction: column;
    gap: 4px;
  }
  
  .events-approval-action-btn {
    padding: 6px 12px;
    font-size: 0.7rem;
  }
}

/* Animations */
@keyframes events-approval-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes events-approval-fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.events-approval-table-container {
  animation: events-approval-fadeIn 0.5s ease-out;
}

/* Focus states for accessibility */
.events-approval-tab:focus {
  outline: none;
  box-shadow: none;
}

.events-approval-title-link:focus,
.events-approval-id-link:focus,
.events-approval-action-btn:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Scrollbar styling */
.events-approval-table-wrapper::-webkit-scrollbar {
  height: 8px;
  width: 8px;
}

.events-approval-table-wrapper::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.events-approval-table-wrapper::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.events-approval-table-wrapper::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
