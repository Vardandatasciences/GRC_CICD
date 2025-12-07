<template>
  <div class="events-queue-container">
    <!-- Header Section -->
    <div class="events-queue-header">
      <div class="events-queue-header-content">
        <div class="events-queue-title-section">
          <h1 class="events-queue-title">Events Queue</h1>
          <p class="events-queue-subtitle">Staging area for events from integrations and internal activities.</p>
        </div>
      </div>
    </div>

    <!-- Event Source Tabs -->
    <div class="events-queue-tabs">
      <div class="events-queue-tabs-container">
        <!-- From Integrations Tab - Only show to administrators and auditors -->
        <button
          v-if="showIntegrationsTab"
          @click="activeTab = 'integrations'"
          :class="[
            'events-queue-tab',
            activeTab === 'integrations' ? 'events-queue-tab-active' : 'events-queue-tab-inactive'
          ]"
        >
          <div class="events-queue-tab-content">
            <span class="events-queue-tab-title">From Integrations</span>
            <span class="events-queue-tab-badge">{{ integrationEvents.length }}</span>
          </div>
        </button>
        
        <!-- From RiskaVaire Activities Tab - Show to all users with event access -->
        <button
          v-if="showRiskaVaireTab"
          @click="activeTab = 'riskavaire'"
          :class="[
            'events-queue-tab',
            activeTab === 'riskavaire' ? 'events-queue-tab-active' : 'events-queue-tab-inactive'
          ]"
        >
          <div class="events-queue-tab-content">
            <span class="events-queue-tab-title">From RiskaVaire Activities</span>
            <span class="events-queue-tab-badge">{{ filteredRiskaVaireEvents.length }}</span>
          </div>
        </button>
      </div>
    </div>

    <!-- Filters Section -->
    <div class="events-queue-filters">
      <div class="events-queue-filters-content">
        <div class="events-queue-filters-left">
          <div class="events-queue-filters-controls">
            <div class="events-queue-filter-group">
              <select 
                v-model="filters.framework"
                class="events-queue-filter-select"
                :disabled="loadingFrameworks"
              >
                <option value="">{{ loadingFrameworks ? 'Loading frameworks...' : 'All Frameworks' }}</option>
                <option v-for="framework in frameworkOptions" :key="framework" :value="framework">
                  {{ framework }}
                </option>
              </select>
              <div v-if="frameworksError" class="events-queue-filter-error">
                {{ frameworksError }}
                <button @click="fetchFrameworks" class="events-queue-filter-retry">
                  Retry
                </button>
              </div>
            </div>
            <div class="events-queue-filter-group">
              <select 
                v-model="filters.module"
                class="events-queue-filter-select"
              >
                <option value="">All Modules</option>
                <option v-for="module in MODULES" :key="module" :value="module">
                  {{ module }}
                </option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Events Table -->
    <div class="events-queue-table-container">
      <div class="events-queue-table-wrapper">
        <table class="events-queue-table">
          <thead class="events-queue-table-header">
            <tr>
              <th class="events-queue-table-th events-queue-source-col">SOURCE SYSTEM</th>
              <th class="events-queue-table-th events-queue-title-col">RAW TITLE</th>
              <th v-if="activeTab === 'riskavaire'" class="events-queue-table-th events-queue-timestamp-col">TIMESTAMP</th>
              <th class="events-queue-table-th events-queue-actions-col">ACTIONS</th>
            </tr>
          </thead>
          <tbody class="events-queue-table-body">
            <tr v-for="(event, index) in filteredEvents" :key="event.id" 
                :class="`events-queue-table-row ${index % 2 === 0 ? 'events-row-even' : 'events-row-odd'}`">
              <td class="events-queue-table-td events-queue-source-cell" data-label="Source System">
                 {{ event.source || 'N/A' }}
               </td>
              <td class="events-queue-table-td events-queue-title-cell" data-label="Raw Title">
                <button
                  @click="handleEventClick(event)"
                  class="events-queue-title-link"
                >
                  {{ event.title }}
                </button>
              </td>
              <td v-if="activeTab === 'riskavaire'" class="events-queue-table-td events-queue-timestamp-cell" data-label="Timestamp">
                {{ event.timestamp }}
              </td>
              <td class="events-queue-table-td events-queue-actions-cell" data-label="Actions">
                <button
                  @click="handleTakeAction(event)"
                  class="events-queue-action-btn"
                >
                  Take Action
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Action Popup -->
    <div v-if="selectedItem && showPopup" class="events-queue-popup-overlay">
      <div class="events-queue-popup-container">
        <!-- Header -->
        <div class="events-queue-popup-header">
          <div class="events-queue-popup-title-section">
            <h2 class="events-queue-popup-title">Queue Item Details</h2>
          </div>
          <button
            @click="closePopup"
            class="events-queue-popup-close-btn"
          >
            <svg class="events-queue-popup-close-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
                 <!-- Content -->
        <div class="events-queue-popup-content">
           <!-- Top Information - Two Columns (only for integration events) -->
          <div v-if="selectedItem && selectedItem.source && selectedItem.source !== 'RiskaVaire Module'" class="events-queue-popup-details-grid">
             <!-- Left Column -->
            <div class="events-queue-popup-details-section">
              <div class="events-queue-popup-details-list">
               <!-- Source System -->
                <div class="events-queue-popup-detail-item">
                  <span class="events-queue-popup-detail-label">Source System</span>
                  <p class="events-queue-popup-detail-value">{{ selectedItem.source || 'Unknown' }}</p>
               </div>
               
               <!-- Suggested Type -->
                <div class="events-queue-popup-detail-item">
                  <span class="events-queue-popup-detail-label">Suggested Type</span>
                  <p class="events-queue-popup-detail-value">{{ selectedItem.suggestedType || 'Event' }}</p>
               </div>
               
               <!-- Status -->
                <div class="events-queue-popup-detail-item">
                  <span class="events-queue-popup-detail-label">Status</span>
                  <span :class="`events-queue-popup-status-badge ${getStatusBadgeClass(selectedItem.status)}`">
                   {{ selectedItem.status || 'New' }}
                 </span>
                </div>
               </div>
             </div>
             
             <!-- Right Column -->
            <div class="events-queue-popup-details-section">
              <div class="events-queue-popup-details-list">
               <!-- Raw Title -->
                <div class="events-queue-popup-detail-item">
                  <span class="events-queue-popup-detail-label">Raw Title</span>
                  <p class="events-queue-popup-detail-value">{{ selectedItem.title || 'N/A' }}</p>
               </div>
               
               <!-- Timestamp -->
                <div class="events-queue-popup-detail-item">
                  <span class="events-queue-popup-detail-label">Timestamp</span>
                  <p class="events-queue-popup-detail-value">{{ selectedItem.timestamp || selectedItem.createdAt || 'N/A' }}</p>
                </div>
               </div>
             </div>
           </div>
           
           <!-- Single column layout for RiskaVaire events -->
          <div v-else class="events-queue-popup-single-column">
            <div class="events-queue-popup-details-section">
              <div class="events-queue-popup-details-list">
             <!-- Source System -->
                <div class="events-queue-popup-detail-item">
                  <span class="events-queue-popup-detail-label">Source System</span>
                  <p class="events-queue-popup-detail-value">{{ selectedItem.source || 'Unknown' }}</p>
             </div>
             
             <!-- Raw Title -->
                <div class="events-queue-popup-detail-item">
                  <span class="events-queue-popup-detail-label">Raw Title</span>
                  <p class="events-queue-popup-detail-value">{{ selectedItem.title || 'N/A' }}</p>
             </div>
             
             <!-- Suggested Type -->
                <div class="events-queue-popup-detail-item">
                  <span class="events-queue-popup-detail-label">Suggested Type</span>
                  <p class="events-queue-popup-detail-value">{{ selectedItem.suggestedType || 'Event' }}</p>
             </div>
             
             <!-- Timestamp -->
                <div class="events-queue-popup-detail-item">
                  <span class="events-queue-popup-detail-label">Timestamp</span>
                  <p class="events-queue-popup-detail-value">{{ selectedItem.timestamp || selectedItem.createdAt || 'N/A' }}</p>
             </div>
             
             <!-- Status -->
                <div class="events-queue-popup-detail-item">
                  <span class="events-queue-popup-detail-label">Status</span>
                  <span :class="`events-queue-popup-status-badge ${getStatusBadgeClass(selectedItem.status)}`">
                 {{ selectedItem.status || 'New' }}
               </span>
                </div>
              </div>
             </div>
           </div>
           
           <!-- Event Details -->
          <div class="events-queue-popup-details-section">
            <label class="events-queue-popup-details-label">Event Details</label>
            <div class="events-queue-popup-details-content">
              <div class="events-queue-popup-details-grid-full">
                <div v-for="entry in filteredEventDetails" :key="entry.key" 
                     class="events-queue-popup-detail-row">
                  <span class="events-queue-popup-detail-key">{{ formatKey(entry.key) }}</span>
                  <span class="events-queue-popup-detail-val">{{ formatValue(entry.value) }}</span>
                </div>
              </div>
            </div>
          </div>
          </div>
        
                 <!-- Action Buttons -->
        <div class="events-queue-popup-actions">
           <!-- Integration Events (Gmail, Google Calendar, etc.) - Create Event and Archive buttons -->
           <template v-if="selectedItem && (selectedItem.source && selectedItem.source !== 'RiskaVaire Module' || activeTab === 'integrations')">
            <div class="events-queue-popup-actions-left">
              <button 
                @click="handleApprove" 
                class="events-queue-popup-btn events-queue-popup-btn-accept"
              >
                <svg class="events-queue-popup-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
               </svg>
               Create Event
             </button>
              <button @click="handleArchive" class="events-queue-popup-btn events-queue-popup-btn-archive">
                <svg class="events-queue-popup-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-14 0a2 2 0 012-2h10a2 2 0 012 2"></path>
               </svg>
               Archive
             </button>
            </div>
           </template>
           
           <!-- RiskaVaire Events - Create Event and Archive buttons -->
           <template v-else>
            <div class="events-queue-popup-actions-left">
              <button 
                @click="handleApprove" 
                class="events-queue-popup-btn events-queue-popup-btn-accept"
              >
                <svg class="events-queue-popup-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
               </svg>
               Create Event
             </button>
              <button @click="handleArchive" class="events-queue-popup-btn events-queue-popup-btn-archive">
                <svg class="events-queue-popup-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-14 0a2 2 0 012-2h10a2 2 0 012 2"></path>
               </svg>
               Archive
             </button>
            </div>
           </template>
        </div>
      </div>
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { eventService } from '../../services/api'
import { MODULES } from '../../utils/constants'
import { PopupService } from '../../modules/popus/popupService'
import PopupModal from '../../modules/popus/PopupModal.vue'
import AccessUtils from '../../utils/accessUtils'
import { useEventPermissions } from '../../composables/useEventPermissions'
import eventDataService from '../../services/eventService' // NEW: Centralized event data service

export default {
  name: 'EventsQueue',
  components: {
    PopupModal
  },
  setup() {
    const router = useRouter()
    
    // Event permissions
    const {
      canViewAllEvents,
      canViewModuleEvents,
      hasEventAccess,
      fetchEventPermissions,
      accessibleModules,
      isAdmin
    } = useEventPermissions()
    
    const selectedItem = ref(null)
    const showPopup = ref(false)
    const activeTab = ref('riskavaire')
    const loading = ref(false)
    const error = ref(null)
    const showEditForm = ref(false)
    const showAttachForm = ref(false)
    const editForm = ref({
      title: '',
      description: '',
      priority: 'Medium',
      reviewer: ''
    })
    const attachForm = ref({
      file: null
    })
    const users = ref([])
    
    // Data
    const integrationEvents = ref([])
    const riskavaireEvents = ref([])
    
    // Computed properties for RBAC-based tab visibility
    const showIntegrationsTab = computed(() => {
      // Only show to administrators and auditors
      return isAdmin.value || canViewAllEvents.value
    })
    
    const showRiskaVaireTab = computed(() => {
      // Show to all users with event access
      return hasEventAccess.value
    })
    
    const filteredRiskaVaireEvents = computed(() => {
      // If user can view all events, show all RiskaVaire events
      if (canViewAllEvents.value) {
        return riskavaireEvents.value
      }
      
      // If user can only view module events, filter by accessible modules
      if (canViewModuleEvents.value && accessibleModules.value.length > 0) {
        return riskavaireEvents.value.filter(event => 
          accessibleModules.value.includes(event.module)
        )
      }
      
      // If no permissions, return empty array
      return []
    })
    
    // Filters
    const filters = ref({
      framework: '',
      module: ''
    })
    
    // Filter options
    const frameworkOptions = ref([])
    const loadingFrameworks = ref(false)
    const frameworksError = ref(null)

    // Computed properties
    const filteredEvents = computed(() => {
      // Use filtered RiskaVaire events for RBAC-based filtering
      const events = activeTab.value === 'riskavaire' ? filteredRiskaVaireEvents.value : integrationEvents.value
      
      console.log('DEBUG: filteredEvents computed - activeTab:', activeTab.value)
      console.log('DEBUG: filteredEvents computed - events count:', events.length)
      console.log('DEBUG: filteredEvents computed - all events:', events)
      
      // Check for Microsoft Sentinel events
      const sentinelEventsInComputed = events.filter(e => e.source === 'Microsoft Sentinel')
      console.log('DEBUG: Microsoft Sentinel events in computed:', sentinelEventsInComputed)
      
      // Log detailed info for each Sentinel event
      sentinelEventsInComputed.forEach((event, index) => {
        console.log(`DEBUG: Sentinel Event ${index + 1}:`, {
          id: event.id,
          title: event.title,
          source: event.source,
          status: event.status,
          priority: event.priority,
          framework: event.framework,
          module: event.module,
          category: event.category,
          timestamp: event.timestamp,
          metadata: event.metadata
        })
      })
      
      let filtered = [...events]
      
      if (filters.value.framework) {
        console.log('DEBUG: Filtering by framework:', filters.value.framework)
        filtered = filtered.filter(event => event.framework === filters.value.framework)
      }
      if (filters.value.module) {
        console.log('DEBUG: Filtering by module:', filters.value.module)
        filtered = filtered.filter(event => event.module === filters.value.module)
      }
      
      console.log('DEBUG: Final filtered events count:', filtered.length)
      console.log('DEBUG: Final filtered events:', filtered)
      
      // Check for Microsoft Sentinel events after filtering
      const sentinelEventsAfterFilter = filtered.filter(e => e.source === 'Microsoft Sentinel')
      console.log('DEBUG: Microsoft Sentinel events after filtering:', sentinelEventsAfterFilter.length)
      
      return filtered
    })

    // Watch for permission changes and adjust active tab if needed
    watch([showIntegrationsTab, showRiskaVaireTab], ([showIntegrations, showRiskaVaire]) => {
      // If user doesn't have access to integrations tab but it's currently active, switch to riskavaire
      if (!showIntegrations && activeTab.value === 'integrations' && showRiskaVaire) {
        activeTab.value = 'riskavaire'
      }
      // If user doesn't have access to either tab, set to riskavaire as fallback
      if (!showIntegrations && !showRiskaVaire) {
        activeTab.value = 'riskavaire'
      }
    })

    const handleTakeAction = (item) => {
      // Store the event data in sessionStorage for the event details page
      sessionStorage.setItem('eventDetailsData', JSON.stringify({
        id: item.id,
        title: item.title,
        framework: item.framework,
        module: item.module,
        category: item.category,
        source: item.source,
        timestamp: item.timestamp,
        status: item.status,
        linkedRecordType: item.linkedRecordType,
        linkedRecordId: item.linkedRecordId,
        linkedRecordName: item.linkedRecordName,
        priority: item.priority,
        description: item.description,
        owner: item.owner,
        reviewer: item.reviewer,
        evidence: item.evidence || [],
        rawData: item.rawData || item,
        metadata: item.metadata,  // Add metadata field
        suggestedType: item.suggestedType,
        isFromQueue: true,
        queueType: activeTab.value
      }))
      
      // Navigate to event details page
      router.push('/event-handling/details')
    }

    const handleEventClick = (event) => {
      // Store the event data in sessionStorage for the event details page
      sessionStorage.setItem('eventDetailsData', JSON.stringify({
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
        rawData: event.rawData || event,
        metadata: event.metadata,  // Add metadata field
        suggestedType: event.suggestedType,
        isFromQueue: true,
        queueType: activeTab.value
      }))
      
      // Navigate to event details page
      router.push('/event-handling/details')
    }

    const closePopup = () => {
      showPopup.value = false
      selectedItem.value = null
      showEditForm.value = false
      showAttachForm.value = false
      editForm.value = {
        title: '',
        description: '',
        priority: 'Medium',
        reviewer: ''
      }
      attachForm.value = {
        file: null
      }
    }

    const handleEdit = () => {
      if (selectedItem.value) {
        editForm.value = {
          title: selectedItem.value.title || '',
          description: selectedItem.value.description || '',
          priority: selectedItem.value.priority || 'Medium',
          reviewer: selectedItem.value.reviewer || ''
        }
        showEditForm.value = true
      }
    }

    const handleAttachEvidence = () => {
      showAttachForm.value = true
    }

    const handleApprove = async () => {
      console.log('handleApprove called, selectedItem:', selectedItem.value)
      
      if (!selectedItem.value) {
        console.error('selectedItem is null in handleApprove')
        return
      }
      
      // Check if this is an integration event (Gmail, Google Calendar, etc.)
      if (selectedItem.value.source && selectedItem.value.source !== 'RiskaVaire Module' && 
          (selectedItem.value.rawData || activeTab.value === 'integrations')) {
        console.log('Processing integration event:', selectedItem.value)
        
        // Store the integration item data for the event creation form
        const integrationData = {
           source: selectedItem.value.source || 'Integration',
           rawData: selectedItem.value.rawData || selectedItem.value,
           title: selectedItem.value.title || 'New Event',
           description: (selectedItem.value.rawData && selectedItem.value.rawData.description) || 
                       selectedItem.value.description || '',
           priority: (selectedItem.value.rawData && selectedItem.value.rawData.priority) || 
                    selectedItem.value.priority || 'Medium',
           status: (selectedItem.value.rawData && selectedItem.value.rawData.status) || 
                  selectedItem.value.status || 'New',
           components: (selectedItem.value.rawData && selectedItem.value.rawData.components) || [],
           integrationItemId: selectedItem.value.id, // Store the ID for tracking
           // Additional fields for prefilling
           timestamp: selectedItem.value.timestamp || selectedItem.value.createdAt || new Date().toISOString(),
           suggestedType: selectedItem.value.suggestedType || 'Event',
           // Store the full popup data for the Source Information section
           popupData: {
             source: selectedItem.value.source || 'Integration',
             title: selectedItem.value.title || 'N/A',
             timestamp: selectedItem.value.timestamp || selectedItem.value.createdAt || 'N/A',
             status: selectedItem.value.status || 'New',
             suggestedType: selectedItem.value.suggestedType || 'Event',
             rawData: selectedItem.value.rawData || selectedItem.value
           }
         }
        
                 console.log('Integration data prepared:', integrationData)
        
        // Store in sessionStorage to pass to event creation form
        sessionStorage.setItem('integrationEventData', JSON.stringify(integrationData))
         
         // Update the status in the integration events list
         const eventIndex = integrationEvents.value.findIndex(e => e.id === selectedItem.value.id)
         if (eventIndex !== -1) {
           console.log('Updating status to Processing for event:', selectedItem.value.id)
           // Force reactivity by creating a new array
           const updatedEvents = [...integrationEvents.value]
           updatedEvents[eventIndex] = {
             ...updatedEvents[eventIndex],
             status: 'Processing'
           }
           integrationEvents.value = updatedEvents
           selectedItem.value.status = 'Processing'
           console.log('Updated event status:', integrationEvents.value[eventIndex])
         } else {
           console.error('Event not found in integration events list:', selectedItem.value.id)
         }
         
         // Close popup after data is stored
         closePopup()
        
        // Navigate to event creation form
        router.push('/event-handling/create')
      } else {
        // RiskaVaire event - Create Event
        console.log('Processing RiskaVaire event:', selectedItem.value)
        
        // Store the RiskaVaire event data for the event creation form
        const riskavaireData = {
           source: selectedItem.value.source || 'RiskaVaire Module',
           rawData: selectedItem.value,
           title: selectedItem.value.title || 'New Event',
           description: selectedItem.value.description || '',
           priority: selectedItem.value.priority || 'Medium',
           status: selectedItem.value.status || 'New',
           framework: selectedItem.value.framework || '',
           module: selectedItem.value.module || '',
           category: selectedItem.value.category || '',
           owner: selectedItem.value.owner || '',
           reviewer: selectedItem.value.reviewer || '',
           linkedRecordType: selectedItem.value.linkedRecordType || '',
           linkedRecordId: selectedItem.value.linkedRecordId || '',
           linkedRecordName: selectedItem.value.linkedRecordName || '',
           riskavaireItemId: selectedItem.value.id, // Store the ID for tracking
           // Additional fields for prefilling
           timestamp: selectedItem.value.timestamp || new Date().toISOString(),
           // Store the full popup data for the Source Information section
           popupData: {
             source: selectedItem.value.source || 'RiskaVaire Module',
             title: selectedItem.value.title || 'N/A',
             timestamp: selectedItem.value.timestamp || 'N/A',
             status: selectedItem.value.status || 'New',
             rawData: selectedItem.value
           }
         }
        
        console.log('RiskaVaire data prepared:', riskavaireData)
        
        // Store in sessionStorage to pass to event creation form
        sessionStorage.setItem('riskavaireEventData', JSON.stringify(riskavaireData))
         
         // Update the status in the RiskaVaire events list
         const eventIndex = riskavaireEvents.value.findIndex(e => e.id === selectedItem.value.id)
         if (eventIndex !== -1) {
           console.log('Updating status to Processing for RiskaVaire event:', selectedItem.value.id)
           // Force reactivity by creating a new array
           const updatedEvents = [...riskavaireEvents.value]
           updatedEvents[eventIndex] = {
             ...updatedEvents[eventIndex],
             status: 'Processing'
           }
           riskavaireEvents.value = updatedEvents
           selectedItem.value.status = 'Processing'
           console.log('Updated RiskaVaire event status:', riskavaireEvents.value[eventIndex])
         } else {
           console.error('RiskaVaire event not found in events list:', selectedItem.value.id)
         }
         
         // Close popup after data is stored
         closePopup()
        
        // Navigate to event creation form
        router.push('/event-handling/create')
      }
    }

    const handleReject = async () => {
      if (!selectedItem.value) return
      
      try {
        loading.value = true
        const response = await eventService.rejectEvent(selectedItem.value.id, {
          user_id: localStorage.getItem('user_id') || '2'
        })
        
        if (response.data.success) {
          // Update the event status in the local data
          const eventIndex = riskavaireEvents.value.findIndex(e => e.id === selectedItem.value.id)
          if (eventIndex !== -1) {
            riskavaireEvents.value[eventIndex].status = 'Rejected'
            selectedItem.value.status = 'Rejected'
          }
          alert('Event rejected successfully!')
        } else {
          alert('Failed to reject event: ' + response.data.message)
        }
      } catch (error) {
        console.error('Error rejecting event:', error)
        alert('Error rejecting event. Please try again.')
      } finally {
        loading.value = false
      }
    }

    const handleArchive = async () => {
      if (!selectedItem.value) return
      
      PopupService.confirm(
        'Are you sure you want to archive this event? This action will move the event to the archived section.',
        'Archive Event',
        async () => {
          await performArchive()
        },
        () => {
          console.log('Archive cancelled by user')
        }
      )
    }

    const performArchive = async () => {
      
      try {
        loading.value = true
        
        // Check if this is an integration event (Gmail, Google Calendar, etc.)
        if (selectedItem.value.source && selectedItem.value.source !== 'RiskaVaire Module' && selectedItem.value.rawData) {
          // For integration events, we need to mark them as archived in the integration database
          // Extract the numeric ID from the event ID (format: "integration_123")
          const integrationItemId = selectedItem.value.id.replace('integration_', '')
          
          const response = await eventService.createEventFromIntegration({
            user_id: localStorage.getItem('user_id') || '2',
            integration_item_id: integrationItemId,
            integration_type: selectedItem.value.source.toLowerCase().replace(' ', '_'),
            action: 'archive' // Add action parameter to indicate archiving
          })
          
          if (response.data.success) {
            // Remove the event from integration events list since it's now in the main events table
            const eventIndex = integrationEvents.value.findIndex(e => e.id === selectedItem.value.id)
            if (eventIndex !== -1) {
              integrationEvents.value.splice(eventIndex, 1)
            }
            
            let message = 'Integration event archived successfully!'
            if (response.data.event_id) {
              message += ` Event ID: ${response.data.event_id_generated}`
            }
            if (response.data.warning) {
              message += ` Warning: ${response.data.warning}`
            }
            
            PopupService.success(message, 'Archive Success')
            closePopup()
            // Refresh integration events to update the list
            fetchIntegrationEvents()
          } else {
            PopupService.error('Failed to archive integration event: ' + response.data.message, 'Archive Error')
          }
        } else {
          // RiskaVaire event archiving
          const response = await eventService.archiveEvent(selectedItem.value.id, {
            user_id: localStorage.getItem('user_id') || '2'
          })
          
          if (response.data.success) {
            // Remove the event from the local data
            const eventIndex = riskavaireEvents.value.findIndex(e => e.id === selectedItem.value.id)
            if (eventIndex !== -1) {
              riskavaireEvents.value.splice(eventIndex, 1)
            }
            PopupService.success('RiskaVaire event archived successfully!', 'Archive Success')
            closePopup()
            
            // Refresh RiskaVaire events to update the list
            fetchRiskaVaireEvents()
          } else {
            PopupService.error('Failed to archive RiskaVaire event: ' + response.data.message, 'Archive Error')
          }
        }
      } catch (error) {
        console.error('Error archiving event:', error)
        PopupService.error('Error archiving event. Please try again.', 'Archive Error')
      } finally {
        loading.value = false
      }
    }

    const saveEdit = async () => {
      if (!selectedItem.value) return
      
      try {
        loading.value = true
        const response = await eventService.updateEvent(selectedItem.value.id, {
          user_id: localStorage.getItem('user_id') || '2',
          title: editForm.value.title,
          description: editForm.value.description,
          priority: editForm.value.priority,
          reviewer: editForm.value.reviewer
        })
        
        if (response.data.success) {
          // Update the event in the local data
          const eventIndex = riskavaireEvents.value.findIndex(e => e.id === selectedItem.value.id)
          if (eventIndex !== -1) {
            riskavaireEvents.value[eventIndex].title = editForm.value.title
            riskavaireEvents.value[eventIndex].description = editForm.value.description
            riskavaireEvents.value[eventIndex].priority = editForm.value.priority
            riskavaireEvents.value[eventIndex].reviewer = editForm.value.reviewer
          }
          selectedItem.value.title = editForm.value.title
          selectedItem.value.description = editForm.value.description
          selectedItem.value.priority = editForm.value.priority
          selectedItem.value.reviewer = editForm.value.reviewer
          
          alert('Event updated successfully!')
          showEditForm.value = false
        } else {
          alert('Failed to update event: ' + response.data.message)
        }
      } catch (error) {
        console.error('Error updating event:', error)
        alert('Error updating event. Please try again.')
      } finally {
        loading.value = false
      }
    }

    const saveAttachEvidence = async () => {
      if (!selectedItem.value || !attachForm.value.file) return
      
      try {
        loading.value = true
        const formData = new FormData()
        formData.append('file', attachForm.value.file)
        formData.append('user_id', localStorage.getItem('user_id') || '2')
        
        const response = await eventService.attachEvidence(selectedItem.value.id, formData)
        
        if (response.data.success) {
          alert('Evidence attached successfully!')
          showAttachForm.value = false
          attachForm.value.file = null
          // Refresh the event data
          fetchRiskaVaireEvents()
        } else {
          alert('Failed to attach evidence: ' + response.data.message)
        }
      } catch (error) {
        console.error('Error attaching evidence:', error)
        alert('Error attaching evidence. Please try again.')
      } finally {
        loading.value = false
      }
    }

    const fetchUsers = async () => {
      try {
        const response = await eventService.getUsers()
        if (response.data.success) {
          users.value = response.data.users || []
        }
      } catch (error) {
        console.error('Error fetching users:', error)
      }
    }

    // Fetch frameworks from API (fallback only)
    const fetchFrameworks = async () => {
      loadingFrameworks.value = true
      frameworksError.value = null
      
      try {
        const response = await eventService.getFrameworks()
        if (response.data.success) {
          // Extract framework names from the response
          frameworkOptions.value = response.data.frameworks.map(fw => fw.FrameworkName || fw.name || fw.framework_name)
          console.log('DEBUG: Loaded frameworks from database:', frameworkOptions.value)
        } else {
          frameworksError.value = 'Failed to fetch frameworks'
          console.error('Failed to fetch frameworks:', response.data.message)
        }
      } catch (error) {
        console.error('Error fetching frameworks:', error)
        frameworksError.value = 'Error loading frameworks'
        // Fallback to hardcoded frameworks if API fails
        frameworkOptions.value = ['NIST', 'ISO 27001', 'COBIT', 'PCI DSS', 'HIPAA', 'SOX', 'GDPR']
        console.log('DEBUG: Using fallback frameworks:', frameworkOptions.value)
      } finally {
        loadingFrameworks.value = false
      }
    }

    const getStatusColor = (status) => {
      switch (status) {
        case 'Pending': return 'events-queue-status-pending'
        case 'Approved': return 'events-queue-status-approved'
        case 'Rejected': return 'events-queue-status-rejected'
        case 'Under Review': return 'events-queue-status-under-review'
        case 'Completed': return 'events-queue-status-completed'
        case 'New': return 'events-queue-status-new'
        case 'Processing': return 'events-queue-status-processing'
        case 'Parked': return 'events-queue-status-parked'
        case 'Archived': return 'events-queue-status-archived'
        default: return 'events-queue-status-default'
      }
    }

    const fetchRiskaVaireEvents = async () => {
      try {
        loading.value = true
        error.value = null
        
        console.log('[EventsQueue] Checking for cached event data...')
        
        // ==========================================
        // NEW: Check if data is already cached from HomeView prefetch
        // ==========================================
        if (eventDataService.hasValidCache()) {
          console.log('[EventsQueue] ✅ Using cached event data from HomeView prefetch')
          const cachedEvents = eventDataService.getData('events') || []
          // Filter for RiskaVaire events from cache
          const events = cachedEvents.filter(event => event.source === 'RiskaVaire Module' || !event.source)
          
          // Transform events to match the queue format
          riskavaireEvents.value = events.map(event => ({
            id: event.event_id || event.id,
            title: event.event_title || event.title,
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
          
          console.log('[EventsQueue] Loaded', riskavaireEvents.value.length, 'RiskaVaire events from cache')
          loading.value = false
          return
        }
        
        // ==========================================
        // Fallback: If cache is empty, wait for prefetch or fetch directly
        // ==========================================
        console.log('[EventsQueue] No cache found, checking for ongoing prefetch...')
        
        if (window.eventDataFetchPromise) {
          console.log('[EventsQueue] ⏳ Waiting for ongoing prefetch to complete...')
          await window.eventDataFetchPromise
          const cachedEvents = eventDataService.getData('events') || []
          const events = cachedEvents.filter(event => event.source === 'RiskaVaire Module' || !event.source)
          
          riskavaireEvents.value = events.map(event => ({
            id: event.event_id || event.id,
            title: event.event_title || event.title,
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
          
          loading.value = false
          return
        }
        
        console.log('DEBUG: Starting to fetch RiskaVaire events from API (cache miss)...')
        
        // Last resort: Fetch RiskaVaire events from the API
        const response = await eventService.getRiskaVaireEvents()
        
        console.log('DEBUG: API response received:', response)
        console.log('DEBUG: Response data:', response.data)
        console.log('DEBUG: Response success:', response.data?.success)
        
        // Check if response has the expected structure
        if (!response.data) {
          console.error('DEBUG: No response data received')
          PopupService.error('No response data received from server', 'Error')
          return
        }
        
        if (response.data.success) {
          const events = response.data.events || []
          console.log('DEBUG: Processing events:', events.length, 'events')
          
          // Transform events to match the queue format
          riskavaireEvents.value = events.map(event => {
            console.log('DEBUG: Processing event:', event)
            return {
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
            }
          })
          
          console.log('DEBUG: Transformed events:', riskavaireEvents.value)
          console.log('DEBUG: Successfully loaded', riskavaireEvents.value.length, 'RiskaVaire events')
          
          // Keep framework options sourced from database; do not overwrite here
          
        } else {
          console.log('DEBUG: API returned success=false:', response.data)
          PopupService.error(response.data.message || 'Failed to fetch RiskaVaire events', 'Error')
        }
      } catch (err) {
        console.error('DEBUG: Error fetching RiskaVaire events:', err)
        console.error('DEBUG: Error response:', err.response)
        console.error('DEBUG: Error status:', err.response?.status)
        console.error('DEBUG: Error data:', err.response?.data)
        
        // Check if it's an access denied error (403)
        if (err.response && err.response.status === 403) {
          AccessUtils.showAccessDenied('Event Management - Events Queue', 'You don\'t have permission to view the events queue. Required permission: event.view_all_event or event.view_module_event')
        } else {
          PopupService.error('Failed to fetch RiskaVaire events. Please try again.', 'Error')
        }
      } finally {
        loading.value = false
      }
    }

    const fetchIntegrationEvents = async () => {
      try {
        loading.value = true
        error.value = null
        
        console.log('[EventsQueue] Checking for cached integration event data...')
        
        // ==========================================
        // NEW: Check if data is already cached from HomeView prefetch
        // ==========================================
        if (eventDataService.hasIntegrationEventsCache()) {
          console.log('[EventsQueue] ✅ Using cached integration event data from HomeView prefetch')
          const events = eventDataService.getData('integrationEvents') || []
          console.log('DEBUG: Integration events from cache:', events)
          console.log('DEBUG: Total events count:', events.length)
          
          // Filter Microsoft Sentinel events for debugging
          const sentinelEvents = events.filter(event => event.source === 'Microsoft Sentinel')
          console.log('DEBUG: Microsoft Sentinel events:', sentinelEvents)
          console.log('DEBUG: Microsoft Sentinel events count:', sentinelEvents.length)
          
          // Transform events to match the queue format
          integrationEvents.value = events.map(event => ({
            id: event.id,
            title: event.title,
            framework: event.framework || 'Integration',
            module: event.module || 'Integration',
            category: event.category || 'Integration',
            source: event.source || 'Integration',
            timestamp: event.timestamp,
            status: event.status || 'New',
            linkedRecordType: event.linkedRecordType || 'Integration Event',
            linkedRecordId: event.linkedRecordId,
            linkedRecordName: event.linkedRecordName,
            priority: event.priority || 'Medium',
            description: event.description,
            owner: event.owner || 'Unassigned',
            reviewer: event.reviewer || 'Pending Assignment',
            evidence: event.evidence || [],
            metadata: event.metadata,
            suggestedType: event.suggestedType || 'General Event',
            rawData: event.rawData || event
          }))
          
          console.log('[EventsQueue] Loaded', integrationEvents.value.length, 'integration events from cache')
          loading.value = false
          return
        }
        
        // ==========================================
        // Fallback: If cache is empty, wait for prefetch or fetch directly
        // ==========================================
        console.log('[EventsQueue] No cache found, checking for ongoing prefetch...')
        
        if (window.eventDataFetchPromise) {
          console.log('[EventsQueue] ⏳ Waiting for ongoing prefetch to complete...')
          await window.eventDataFetchPromise
          const events = eventDataService.getData('integrationEvents') || []
          
          // Transform events to match the queue format
          integrationEvents.value = events.map(event => ({
            id: event.id,
            title: event.title,
            framework: event.framework || 'Integration',
            module: event.module || 'Integration',
            category: event.category || 'Integration',
            source: event.source || 'Integration',
            timestamp: event.timestamp,
            status: event.status || 'New',
            linkedRecordType: event.linkedRecordType || 'Integration Event',
            linkedRecordId: event.linkedRecordId,
            linkedRecordName: event.linkedRecordName,
            priority: event.priority || 'Medium',
            description: event.description,
            owner: event.owner || 'Unassigned',
            reviewer: event.reviewer || 'Pending Assignment',
            evidence: event.evidence || [],
            metadata: event.metadata,
            suggestedType: event.suggestedType || 'General Event',
            rawData: event.rawData || event
          }))
          
          loading.value = false
          return
        }
        
        // Last resort: Fetch directly from API
        console.log('[EventsQueue] 🔄 Fetching integration event data from API (cache miss)...')
        const response = await eventService.getIntegrationEvents()
        
        if (response.data.success) {
          const events = response.data.events || []
          console.log('DEBUG: Integration events received from API:', events)
          console.log('DEBUG: Total events count:', events.length)
          
          // Filter Microsoft Sentinel events for debugging
          const sentinelEvents = events.filter(event => event.source === 'Microsoft Sentinel')
          console.log('DEBUG: Microsoft Sentinel events:', sentinelEvents)
          console.log('DEBUG: Microsoft Sentinel events count:', sentinelEvents.length)
          
          // Transform events to match the queue format
          integrationEvents.value = events.map(event => ({
            id: event.id,
            title: event.title,
            framework: event.framework || 'Integration',
            module: event.module || 'Integration',
            category: event.category || 'Integration',
            source: event.source || 'Integration',  // Use actual source from database
            timestamp: event.timestamp,
            status: event.status || 'New',
            linkedRecordType: event.linkedRecordType || 'Integration Event',
            linkedRecordId: event.linkedRecordId,
            linkedRecordName: event.linkedRecordName,
            priority: event.priority || 'Medium',
            description: event.description,
            owner: event.owner || 'Unassigned',
            reviewer: event.reviewer || 'Pending Assignment',
            evidence: event.evidence || [],
            metadata: event.metadata,  // Add metadata field
            suggestedType: event.suggestedType || 'General Event',
            rawData: event.rawData || event
          }))
          
          // Cache the fetched data for future use
          eventDataService.setData('integrationEvents', events)
          console.log('[EventsQueue] ✅ Cached', events.length, 'integration events')
          
        } else {
          PopupService.error(response.data.message || 'Failed to fetch integration events', 'Error')
        }
      } catch (err) {
        console.error('Error fetching integration events:', err)
        
        // Check if it's an access denied error (403)
        if (err.response && err.response.status === 403) {
          AccessUtils.showAccessDenied('Event Management - Events Queue', 'You don\'t have permission to view the events queue. Required permission: event.view_all_event or event.view_module_event')
        } else {
          PopupService.error('Failed to fetch integration events. Please try again.', 'Error')
        }
      } finally {
        loading.value = false
      }
    }

    const refreshEvents = async () => {
      if (activeTab.value === 'riskavaire') {
        await fetchRiskaVaireEvents()
      } else if (activeTab.value === 'integrations') {
        await fetchIntegrationEvents()
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
        'Draft': 'bg-gray-100 text-gray-800'
      }
      return statusClasses[status] || 'bg-gray-100 text-gray-800'
    }

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

    // Computed property to filter event details for display
    const filteredEventDetails = computed(() => {
      if (!selectedItem.value) return []
      
      const data = selectedItem.value.rawData || selectedItem.value
      const filteredEntries = []
      
      for (const [key, value] of Object.entries(data)) {
        if (value !== null && value !== undefined && value !== '') {
          filteredEntries.push({ key, value })
        }
      }
      
      return filteredEntries
    })

    // Watch for filter changes
    watch([filters, activeTab], () => {
      // Filters are applied in computed property
    }, { deep: true })

    // Check for event creation completion when component mounts
    const checkEventCreationStatus = () => {
      const eventCreationStatus = sessionStorage.getItem('eventCreationStatus')
      if (eventCreationStatus) {
        try {
          const statusData = JSON.parse(eventCreationStatus)
          if (statusData.success) {
            // Handle integration events
            if (statusData.integrationItemId) {
              const eventIndex = integrationEvents.value.findIndex(e => e.id === statusData.integrationItemId)
              if (eventIndex !== -1) {
                console.log('Updating status to Completed for integration event:', statusData.integrationItemId)
                const updatedEvents = [...integrationEvents.value]
                updatedEvents[eventIndex] = {
                  ...updatedEvents[eventIndex],
                  status: 'Completed'
                }
                integrationEvents.value = updatedEvents
                console.log('Updated integration event status to Completed:', updatedEvents[eventIndex])
              }
            }
            
            // Handle RiskaVaire events
            if (statusData.riskavaireItemId) {
              const eventIndex = riskavaireEvents.value.findIndex(e => e.id === statusData.riskavaireItemId)
              if (eventIndex !== -1) {
                console.log('Updating status to Completed for RiskaVaire event:', statusData.riskavaireItemId)
                const updatedEvents = [...riskavaireEvents.value]
                updatedEvents[eventIndex] = {
                  ...updatedEvents[eventIndex],
                  status: 'Completed'
                }
                riskavaireEvents.value = updatedEvents
                console.log('Updated RiskaVaire event status to Completed:', updatedEvents[eventIndex])
              }
            }
          }
          // Clear the status from sessionStorage
          sessionStorage.removeItem('eventCreationStatus')
      } catch (error) {
          console.error('Error parsing event creation status:', error)
        }
      }
    }

    // Check for status updates from Events List page
    const checkStatusUpdates = () => {
      const statusUpdates = sessionStorage.getItem('eventStatusUpdates')
      if (statusUpdates) {
        try {
          const updates = JSON.parse(statusUpdates)
          console.log('Found status updates:', updates)
          
          updates.forEach(update => {
            // Update integration events
            const integrationIndex = integrationEvents.value.findIndex(e => e.id === update.id)
            if (integrationIndex !== -1) {
              console.log('Updating integration event status:', update.id, 'to', update.status)
              const updatedEvents = [...integrationEvents.value]
              updatedEvents[integrationIndex] = {
                ...updatedEvents[integrationIndex],
                status: update.status
              }
              integrationEvents.value = updatedEvents
            }
            
            // Update RiskaVaire events
            const riskavaireIndex = riskavaireEvents.value.findIndex(e => e.id === update.id)
            if (riskavaireIndex !== -1) {
              console.log('Updating RiskaVaire event status:', update.id, 'to', update.status)
              const updatedEvents = [...riskavaireEvents.value]
              updatedEvents[riskavaireIndex] = {
                ...updatedEvents[riskavaireIndex],
                status: update.status
              }
              riskavaireEvents.value = updatedEvents
            }
          })
          
          // Clear the updates from sessionStorage
          sessionStorage.removeItem('eventStatusUpdates')
      } catch (error) {
          console.error('Error parsing status updates:', error)
        }
      }
    }

    onMounted(async () => {
      // Fetch user permissions first
      await fetchEventPermissions()
      
      fetchRiskaVaireEvents()
      fetchIntegrationEvents()
      fetchUsers()
      fetchFrameworks()
      checkEventCreationStatus()
      checkStatusUpdates()
      
      // Set up periodic status sync every 3 seconds for better responsiveness
      const statusSyncInterval = setInterval(() => {
        checkStatusUpdates()
      }, 3000)
      
      // Clean up interval when component unmounts
      onUnmounted(() => {
        clearInterval(statusSyncInterval)
      })
      
      // Sync when user returns to this tab
      const handleVisibilityChange = () => {
        if (!document.hidden) {
          console.log('Page became visible, syncing status updates...')
          checkStatusUpdates()
        }
      }
      
      document.addEventListener('visibilitychange', handleVisibilityChange)
      
      // Listen for unarchive events to refresh the events queue
      const handleEventUnarchived = async (event) => {
        console.log('Event unarchived, refreshing events queue...', event.detail)
        await refreshEvents()
      }
      
      window.addEventListener('eventUnarchived', handleEventUnarchived)
      
      // Clean up event listeners
      onUnmounted(() => {
        document.removeEventListener('visibilitychange', handleVisibilityChange)
        window.removeEventListener('eventUnarchived', handleEventUnarchived)
      })
    })

    return {
      selectedItem,
      showPopup,
      activeTab,
      loading,
      error,
      showEditForm,
      showAttachForm,
      editForm,
      attachForm,
      users,
      integrationEvents,
      riskavaireEvents,
      filteredEvents,
      filters,
      frameworkOptions,
      loadingFrameworks,
      frameworksError,
      MODULES,
      // RBAC computed properties
      showIntegrationsTab,
      showRiskaVaireTab,
      filteredRiskaVaireEvents,
      handleTakeAction,
      handleEventClick,
      closePopup,
      handleEdit,
      handleAttachEvidence,
      handleApprove,
      handleReject,
      handleArchive,
      saveEdit,
      saveAttachEvidence,
      getStatusColor,
      fetchRiskaVaireEvents,
      fetchFrameworks,
      refreshEvents,
      getStatusBadgeClass,
      formatKey,
      formatValue,
      filteredEventDetails
    }
  }
}
</script>

<style>
/* Events Queue Container */
.events-queue-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding-top: 40px;
  background: #ffffff;
  margin-left: -30px;
}

/* Events Queue Header */
.events-queue-header {
  flex-shrink: 0;
  padding: 24px 32px;
  background: #ffffff;
  border-bottom: 1px solid #ffffff;
}

.events-queue-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.events-queue-title-section {
  flex: 1;
}

.events-queue-title {
  font-size: 1.7rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.events-queue-subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
  font-weight: 500;
}

/* Events Queue Tabs */
.events-queue-tabs {
  flex-shrink: 0;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
}

.events-queue-tabs-container {
  display: flex;
  padding: 0 32px;
}

.events-queue-tab {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  border: none;
  background: none;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  border-bottom: 3px solid transparent;
}

.events-queue-tab:hover {
  background: #f8f9fa;
}

.events-queue-tab-active {
  background: transparent;
  border-bottom-color: #3b82f6;
}

.events-queue-tab-inactive {
  color: #6b7280;
}

.events-queue-tab-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.events-queue-tab-title {
  font-size: 0.95rem;
  font-weight: 600;
  transition: color 0.3s ease;
}

.events-queue-tab-active .events-queue-tab-title {
  color: #374151;
}

.events-queue-tab-inactive .events-queue-tab-title {
  color: #6b7280;
}

.events-queue-tab-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

.events-queue-tab-active .events-queue-tab-badge {
  background: #e5e7eb;
  color: #6b7280;
}

.events-queue-tab-inactive .events-queue-tab-badge {
  background: #e5e7eb;
  color: #6b7280;
}

/* Events Queue Filters */
.events-queue-filters {
  flex-shrink: 0;
  padding: 20px 32px;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
}

.events-queue-filters-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.events-queue-filters-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.events-queue-filters-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.events-queue-filters-icon {
  width: 20px;
  height: 20px;
  color: #6b7280;
}

.events-queue-filters-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #374151;
  margin: 0;
}

.events-queue-filters-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.events-queue-filter-group {
  display: flex;
  flex-direction: column;
}

.events-queue-filter-select {
  padding: 8px 12px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  background: #ffffff;
  color: #374151;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  min-width: 150px;
}

.events-queue-filter-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.events-queue-filter-select:disabled {
  background: #f9fafb;
  color: #9ca3af;
  cursor: not-allowed;
}

.events-queue-filter-error {
  margin-top: 8px;
  font-size: 0.85rem;
  color: #dc2626;
  display: flex;
  align-items: center;
  gap: 8px;
}

.events-queue-filter-retry {
  color: #3b82f6;
  text-decoration: underline;
  cursor: pointer;
  font-weight: 500;
  background: none;
  border: none;
  padding: 0;
  font-size: 0.85rem;
}

.events-queue-filter-retry:hover {
  color: #2563eb;
}

/* Events Queue Table */
.events-queue-table-container {
  flex: 1;
  overflow: hidden;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  position: relative;
  z-index: 10;
}

.events-queue-table-wrapper {
  overflow-x: auto;
  overflow-y: auto;
  max-height: calc(100vh - 200px);
  position: relative;
}

.events-queue-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
}

.events-queue-table-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.events-queue-table-th {
  padding: 12px 12px;
  text-align: left;
  font-size: 0.75rem;
  font-weight: 700;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid #e5e7eb;
  white-space: nowrap;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.events-queue-actions-col {
  text-align: center;
}

.events-queue-source-col {
  min-width: 140px;
  max-width: 140px;
}

.events-queue-title-col {
  min-width: 300px;
}

.events-queue-timestamp-col {
  min-width: 160px;
  max-width: 160px;
}


.events-queue-actions-col {
  min-width: 140px;
  max-width: 140px;
}

.events-queue-table-body {
  background: #ffffff;
  position: relative;
  z-index: 1;
  isolation: isolate;
}

.events-queue-table-row {
  transition: all 0.2s ease;
  border-bottom: 1px solid #f3f4f6;
  position: relative;
  z-index: 1;
}

.events-queue-table-row:hover {
  background: #f8f9fa;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.events-row-even {
  background: #ffffff;
}

.events-row-odd {
  background: #fafafa;
}

.events-queue-table-td {
  padding: 12px 12px;
  font-size: 0.85rem;
  color: #374151;
  vertical-align: middle;
  text-align: left;
  position: relative;
  z-index: 1;
  background-color: inherit;
}

.events-queue-source-cell {
  font-weight: 500;
  color: #6b7280;
}

.events-queue-title-cell {
  text-align: left;
  vertical-align: top;
  word-wrap: break-word;
  overflow: visible;
  position: static;
  z-index: 1;
}

/* Override global button styles for events queue title links */
.events-queue-title-link,
button.events-queue-title-link,
.events-queue-table-td button.events-queue-title-link {
  color: #1f2937 !important;
  text-decoration: none !important;
  font-weight: 500 !important;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left !important;
  display: block;
  width: 100%;
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  padding: 0 !important;
  line-height: 1.3;
  word-wrap: break-word;
  white-space: normal;
  box-shadow: none !important;
  outline: none;
  font-size: 0.85rem;
  position: relative;
  z-index: 1;
  overflow: visible;
}

.events-queue-title-link:hover,
button.events-queue-title-link:hover,
.events-queue-table-td button.events-queue-title-link:hover {
  color: #3b82f6 !important;
  text-decoration: underline !important;
  background: transparent !important;
  background-color: transparent !important;
}

.events-queue-timestamp-cell {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.75rem;
  color: #6b7280;
}

.events-queue-actions-cell {
  text-align: center;
  vertical-align: middle;
}

.events-queue-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 18px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
  min-width: 100px;
  white-space: nowrap;
  position: relative;
  vertical-align: middle;
  margin: 0 !important;
}

.events-queue-action-btn:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

/* Events Queue Popup */
.events-queue-popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
  animation: events-queue-popup-fadeIn 0.3s ease-out;
}

.events-queue-popup-container {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 20px 25px rgba(0, 0, 0, 0.15), 0 10px 10px rgba(0, 0, 0, 0.04);
  max-width: 900px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  margin: 20px;
  animation: events-queue-popup-slideIn 0.4s ease-out;
  display: flex;
  flex-direction: column;
}

.events-queue-popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-radius: 16px 16px 0 0;
}

.events-queue-popup-title-section {
  flex: 1;
}

.events-queue-popup-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
  line-height: 1.3;
}

.events-queue-popup-close-btn {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.events-queue-popup-close-btn:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.events-queue-popup-close-icon {
  width: 24px;
  height: 24px;
}

.events-queue-popup-content {
  padding: 32px;
  flex: 1;
  overflow-y: auto;
}

.events-queue-popup-details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
  margin-bottom: 32px;
}

.events-queue-popup-single-column {
  margin-bottom: 32px;
}

.events-queue-popup-details-section {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
}

.events-queue-popup-details-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.events-queue-popup-detail-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.events-queue-popup-detail-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.events-queue-popup-detail-value {
  font-size: 0.95rem;
  font-weight: 500;
  color: #1f2937;
  margin: 0;
}

.events-queue-popup-status-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border: 2px solid transparent;
}

.events-queue-popup-details-section {
  margin-top: 32px;
}

.events-queue-popup-details-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.events-queue-popup-details-content {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e5e7eb;
}

.events-queue-popup-details-grid-full {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.events-queue-popup-detail-row {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid #e5e7eb;
  align-items: start;
}

.events-queue-popup-detail-row:last-child {
  border-bottom: none;
}

.events-queue-popup-detail-key {
  font-size: 0.85rem;
  font-weight: 600;
  color: #374151;
  text-transform: capitalize;
  word-break: break-word;
}

.events-queue-popup-detail-val {
  font-size: 0.9rem;
  color: #1f2937;
  word-break: break-word;
  line-height: 1.4;
}

.events-queue-popup-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 24px 32px;
  border-top: 1px solid #e5e7eb;
  background: #f8f9fa;
  flex-shrink: 0;
  gap: 12px;
}

.events-queue-popup-actions-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.events-queue-popup-btn {
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

.events-queue-popup-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.events-queue-popup-btn-icon {
  width: 16px;
  height: 16px;
  stroke-width: 2.5;
}

.events-queue-popup-btn-accept {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.events-queue-popup-btn-accept:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
}

.events-queue-popup-btn-edit {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.events-queue-popup-btn-edit:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
}

.events-queue-popup-btn-attach {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.events-queue-popup-btn-attach:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

.events-queue-popup-btn-approve {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.events-queue-popup-btn-approve:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

.events-queue-popup-btn-reject {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.events-queue-popup-btn-reject:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
}

.events-queue-popup-btn-archive {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
}

.events-queue-popup-btn-archive:hover {
  background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
}


/* Responsive Design */
@media (max-width: 768px) {
  .events-queue-container {
    margin-left: 0;
  }
  
  .events-queue-header {
    padding: 20px;
  }
  
  .events-queue-title {
    font-size: 1.5rem;
  }
  
  .events-queue-tabs-container {
    padding: 0 20px;
  }
  
  .events-queue-tab {
    padding: 12px 16px;
  }
  
  .events-queue-tab-content {
    flex-direction: column;
    gap: 4px;
  }
  
  .events-queue-filters {
    padding: 16px 20px;
  }
  
  .events-queue-filters-left {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .events-queue-filters-controls {
    flex-direction: column;
    gap: 12px;
  }
  
  .events-queue-filter-select {
    min-width: auto;
    width: 100%;
  }
  
  .events-queue-table-th,
  .events-queue-table-td {
    padding: 12px 8px;
  }
  
  .events-queue-popup-container {
    width: 95%;
    margin: 10px;
  }
  
  .events-queue-popup-header {
    padding: 20px;
  }
  
  .events-queue-popup-content {
    padding: 20px;
  }
  
  .events-queue-popup-details-grid {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .events-queue-popup-actions {
    padding: 20px;
    flex-direction: column;
    gap: 12px;
  }
  
  .events-queue-popup-actions-left {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .events-queue-popup-btn {
    padding: 10px 16px;
    font-size: 0.85rem;
  }
  
  .events-queue-popup-detail-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .events-queue-popup-detail-key {
    font-size: 0.8rem;
  }
  
  .events-queue-popup-detail-val {
    font-size: 0.85rem;
  }
}

/* Animations */
@keyframes events-queue-popup-fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes events-queue-popup-slideIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Focus states for accessibility */
.events-queue-tab:focus {
  outline: none;
}

.events-queue-filter-select:focus,
.events-queue-popup-btn:focus,
.events-queue-action-btn:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Scrollbar styling */
.events-queue-table-wrapper::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.events-queue-table-wrapper::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.events-queue-table-wrapper::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.events-queue-table-wrapper::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.events-queue-popup-container::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.events-queue-popup-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.events-queue-popup-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.events-queue-popup-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>


