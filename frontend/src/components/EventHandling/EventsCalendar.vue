<template>
  <div class="events-calendar-container">
    <!-- Header Section -->
    <div class="events-calendar-header">
      <div class="events-calendar-header-content">
        <div class="events-calendar-title-section">
          <h1 class="events-calendar-title">Events Calendar</h1>
          <p class="events-calendar-subtitle">Dedicated view for recurring and future events</p>
        </div>
        <div class="events-calendar-view-toggle">
          <button
            @click="setViewMode('table')"
            :class="[
              'events-calendar-view-btn',
              viewMode === 'table' ? 'events-calendar-view-btn-active' : 'events-calendar-view-btn-inactive'
            ]"
          >
            <svg class="events-calendar-view-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H6a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
            </svg>
            Table View
          </button>
          <button
            @click="setViewMode('calendar')"
            :class="[
              'events-calendar-view-btn',
              viewMode === 'calendar' ? 'events-calendar-view-btn-active' : 'events-calendar-view-btn-inactive'
            ]"
          >
            <svg class="events-calendar-view-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
            </svg>
            Calendar View
          </button>
        </div>
      </div>
    </div>

    <div v-if="viewMode === 'table'">
      <!-- Loading State -->
      <div v-if="loading" class="events-calendar-loading">
        <div class="events-calendar-loading-content">
          <div class="events-calendar-loading-spinner"></div>
          <p class="events-calendar-loading-text">Loading calendar events...</p>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="events-calendar-error">
        <div class="events-calendar-error-content">
          <div class="events-calendar-error-icon">
            <svg class="events-calendar-error-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </div>
          <p class="events-calendar-error-message">{{ error }}</p>
          <button @click="fetchEvents" class="events-calendar-error-retry">
            Try Again
          </button>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="calendarEvents.length === 0" class="events-calendar-empty">
        <div class="events-calendar-empty-content">
          <div class="events-calendar-empty-icon">
            <svg class="events-calendar-empty-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
            </svg>
          </div>
          <p class="events-calendar-empty-title">No recurring events found</p>
          <p class="events-calendar-empty-subtitle">Create recurring events with RecurrenceType='Recurring' to see them in the calendar view</p>
        </div>
      </div>

      <!-- Events Table -->
      <div v-else class="events-calendar-table-container">
        <div class="events-calendar-table-wrapper">
          <table class="events-calendar-table">
            <thead class="events-calendar-table-header">
              <tr>
                <th class="events-calendar-table-th events-calendar-title-col">EVENT TITLE</th>
                <th class="events-calendar-table-th events-calendar-id-col">EVENT ID</th>
                <th class="events-calendar-table-th events-calendar-category-col">CATEGORY</th>
                <th class="events-calendar-table-th events-calendar-date-col">SCHEDULED DATE</th>
                <th class="events-calendar-table-th events-calendar-recurrence-col">RECURRENCE</th>
                <th class="events-calendar-table-th events-calendar-status-col">STATUS</th>
              </tr>
            </thead>
            <tbody class="events-calendar-table-body">
              <tr v-for="(event, index) in calendarEvents" :key="event.id" 
                  :class="`events-calendar-table-row ${index % 2 === 0 ? 'events-row-even' : 'events-row-odd'}`">
                <td class="events-calendar-table-td events-calendar-title-cell" data-label="Event Title">
                  <button
                    @click="handleEventClick(event)"
                    class="events-calendar-title-link"
                  >
                    {{ event.title }}
                  </button>
                </td>
                <td class="events-calendar-table-td events-calendar-id-cell" data-label="Event ID">
                  {{ event.event_id }}
                </td>
                <td class="events-calendar-table-td events-calendar-category-cell" data-label="Category">
                  {{ event.category || 'N/A' }}
                </td>
                <td class="events-calendar-table-td events-calendar-date-cell" data-label="Scheduled Date">
                  {{ event.start_date || event.created_at }}
                </td>
                <td class="events-calendar-table-td events-calendar-recurrence-cell" data-label="Recurrence">
                  {{ event.frequency || 'N/A' }}
                </td>
                <td class="events-calendar-table-td events-calendar-status-cell" data-label="Status">
                  <div class="events-calendar-status-display">
                    <span :class="`events-calendar-status-dot ${getStatusColor(event.status)}`"></span>
                    <span :class="`events-calendar-status-text ${getStatusColor(event.status)}`">
                      {{ event.status }}
                    </span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-else>
      <!-- Calendar View -->
      <div class="events-calendar-view-container">
        <!-- Calendar Header -->
        <div class="events-calendar-view-header">
          <h3 class="events-calendar-view-title">
            {{ monthNames[currentDate.getMonth()] }} {{ currentDate.getFullYear() }}
          </h3>
          <div class="events-calendar-view-navigation">
            <button
              @click="previousMonth"
              class="events-calendar-nav-btn"
            >
              <svg class="events-calendar-nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
              </svg>
            </button>
            <button
              @click="nextMonth"
              class="events-calendar-nav-btn"
            >
              <svg class="events-calendar-nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
              </svg>
            </button>
          </div>
        </div>

        <!-- Calendar Grid -->
        <div class="events-calendar-grid">
          <div v-for="day in ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']" :key="day" class="events-calendar-day-header">
            {{ day }}
          </div>
          <div
            v-for="(day, index) in calendarDays"
            :key="index"
            :class="`events-calendar-day-cell ${
              day.getMonth() !== currentDate.getMonth() ? 'events-calendar-day-other-month' : 'events-calendar-day-current-month'
            }`"
          >
            <div class="events-calendar-day-number">{{ day.getDate() }}</div>
            <div class="events-calendar-day-events">
              <button
                v-for="event in getDayEvents(day)"
                :key="event.id"
                @click="handleEventClick(event)"
                :class="`events-calendar-event-item ${getCategoryColor(event.category)}`"
              >
                <div class="events-calendar-event-title">{{ event.title }}</div>
                <div class="events-calendar-event-category">{{ event.category }}</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Event View Popup -->
    <EventViewPopup
      v-if="selectedEvent"
      :event="selectedEvent"
      :is-open="showPopup"
      @close="closePopup"
      @edit="handleEdit"
      @attach-evidence="handleAttachEvidence"
      @approve="handleApprove"
      @reject="handleReject"
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
  name: 'EventsCalendar',
  components: {
    EventViewPopup,
    PopupModal
  },
  setup() {
    const viewMode = ref('table')
    const selectedEvent = ref(null)
    const showPopup = ref(false)
    const currentDate = ref(new Date())
    const events = ref([])
    const loading = ref(false)
    const error = ref(null)
    const selectedFrameworkFromSession = ref(null)

    const monthNames = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ]

    // Filter for recurring events only (calendar events)
    const calendarEvents = computed(() => {
      return events.value.filter(event => {
        // Only show recurring events in calendar
        return event.frequency && event.frequency !== 'Non-Recurring'
      })
    })

    const calendarDays = computed(() => {
      const year = currentDate.value.getFullYear()
      const month = currentDate.value.getMonth()
      const firstDay = new Date(year, month, 1)
      const startDate = new Date(firstDay)
      startDate.setDate(startDate.getDate() - firstDay.getDay())
      
      const days = []
      for (let i = 0; i < 42; i++) {
        const day = new Date(startDate)
        day.setDate(startDate.getDate() + i)
        days.push(day)
      }
      return days
    })

    const setViewMode = (mode) => {
      viewMode.value = mode
    }

    const handleEventClick = (event) => {
      selectedEvent.value = event
      showPopup.value = true
    }

    const closePopup = () => {
      showPopup.value = false
    }

    const handleEdit = () => {
      console.log('Edit event:', selectedEvent.value?.id)
      showPopup.value = false
    }

    const handleAttachEvidence = () => {
      console.log('Attach evidence for event:', selectedEvent.value?.id)
      showPopup.value = false
    }

    const handleApprove = () => {
      console.log('Approve event:', selectedEvent.value?.id)
      showPopup.value = false
    }

    const handleReject = () => {
      console.log('Reject event:', selectedEvent.value?.id)
      showPopup.value = false
    }

    const handleArchive = () => {
      console.log('Archive event:', selectedEvent.value?.id)
      showPopup.value = false
    }

    const previousMonth = () => {
      const year = currentDate.value.getFullYear()
      const month = currentDate.value.getMonth()
      currentDate.value = new Date(year, month - 1, 1)
    }

    const nextMonth = () => {
      const year = currentDate.value.getFullYear()
      const month = currentDate.value.getMonth()
      currentDate.value = new Date(year, month + 1, 1)
    }

    const getStatusColor = (status) => {
      switch (status) {
        case 'Approved': return 'events-calendar-status-approved'
        case 'Pending Review': return 'events-calendar-status-pending-review'
        case 'Rejected': return 'events-calendar-status-rejected'
        case 'Draft': return 'events-calendar-status-draft'
        case 'Under Review': return 'events-calendar-status-under-review'
        case 'Completed': return 'events-calendar-status-completed'
        case 'Cancelled': return 'events-calendar-status-cancelled'
        default: return 'events-calendar-status-default'
      }
    }

    const getCategoryColor = (category) => {
      // Define colors for common categories
      const colors = {
        'Access Review': 'events-calendar-category-access-review',
        'DR Drill': 'events-calendar-category-dr-drill',
        'Patch Mgmt': 'events-calendar-category-patch-mgmt',
        'Audit': 'events-calendar-category-audit',
        'Risk Review': 'events-calendar-category-risk-review',
        'Training': 'events-calendar-category-training',
        'Risk Assessment': 'events-calendar-category-risk-assessment',
        'Compliance': 'events-calendar-category-compliance',
        'Security': 'events-calendar-category-security',
        'Incident': 'events-calendar-category-incident',
        'Policy': 'events-calendar-category-policy',
        'Review': 'events-calendar-category-review',
        'Assessment': 'events-calendar-category-assessment',
        'Management': 'events-calendar-category-management'
      }
      
      // If exact match found, return it
      if (colors[category]) {
        return colors[category]
      }
      
      // For unknown categories, generate a consistent color based on category name
      const colorOptions = [
        'events-calendar-category-blue',
        'events-calendar-category-pink',
        'events-calendar-category-green',
        'events-calendar-category-purple',
        'events-calendar-category-orange',
        'events-calendar-category-indigo',
        'events-calendar-category-yellow',
        'events-calendar-category-teal',
        'events-calendar-category-red',
        'events-calendar-category-rose'
      ]
      
      // Generate consistent color based on category name hash
      if (category) {
        let hash = 0
        for (let i = 0; i < category.length; i++) {
          hash = category.charCodeAt(i) + ((hash << 5) - hash)
        }
        const colorIndex = Math.abs(hash) % colorOptions.length
        return colorOptions[colorIndex]
      }
      
      // Default fallback
      return 'events-calendar-category-default'
    }

    const getDayEvents = (day) => {
      // For recurring events, show them on specific days based on frequency
      return calendarEvents.value.filter(event => {
        if (!event.start_date) return false
        
        const eventDate = new Date(event.start_date)
        const currentDate = new Date(day)
        const currentYear = currentDate.getFullYear()
        const currentMonth = currentDate.getMonth()
        const currentDay = currentDate.getDate()
        const currentDayOfWeek = currentDate.getDay() // 0 = Sunday, 1 = Monday, etc.
        
        // Calculate days difference from event start date
        const daysDiff = Math.floor((currentDate - eventDate) / (1000 * 60 * 60 * 24))
        
        // Handle different frequency types for recurring events
        switch (event.frequency?.toLowerCase()) {
          case 'daily':
            return daysDiff >= 0 // Show every day from start date onwards
            
          case 'weekly':
            // Show on the same day of week as the original event
            return daysDiff >= 0 && currentDayOfWeek === eventDate.getDay()
            
          case 'biweekly':
            // Show every 2 weeks on the same day of week
            return daysDiff >= 0 && daysDiff % 14 === 0 && currentDayOfWeek === eventDate.getDay()
            
          case 'monthly':
            // Show on the same day of month
            return currentDay === eventDate.getDate() && 
                   currentDate >= eventDate
            
          case 'quarterly': {
            // Show every 3 months on the same day
            const monthsDiff = (currentYear - eventDate.getFullYear()) * 12 + (currentMonth - eventDate.getMonth())
            return currentDay === eventDate.getDate() && 
                   monthsDiff >= 0 && 
                   monthsDiff % 3 === 0
          }
            
          case 'biannual': {
            // Show every 6 months on the same day
            const biannualMonthsDiff = (currentYear - eventDate.getFullYear()) * 12 + (currentMonth - eventDate.getMonth())
            return currentDay === eventDate.getDate() && 
                   biannualMonthsDiff >= 0 && 
                   biannualMonthsDiff % 6 === 0
          }
            
          case 'annually':
          case 'yearly':
            // Show on the same date every year
            return currentDay === eventDate.getDate() && 
                   currentMonth === eventDate.getMonth() &&
                   currentYear >= eventDate.getFullYear()
            
          default:
            // For unknown frequencies, show only on the exact start date
            return currentDate.toDateString() === eventDate.toDateString()
        }
      })
    }

    // Check for selected framework from session (similar to other modules)
    const checkSelectedFrameworkFromSession = async () => {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in EventsCalendar...')
        const response = await axios.get('/api/frameworks/get-selected/', {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        })
        
        console.log('🔍 DEBUG: Framework response in EventsCalendar:', response.data)
        
        if (response.data && response.data.frameworkId) {
          const frameworkIdFromSession = response.data.frameworkId.toString()
          console.log('✅ DEBUG: Found selected framework in session for EventsCalendar:', frameworkIdFromSession)
          
          // Set the selected framework from session
          selectedFrameworkFromSession.value = frameworkIdFromSession
          console.log('📊 DEBUG: Events are now filtered by framework:', frameworkIdFromSession)
          console.log('📊 DEBUG: selectedFrameworkFromSession.value set to:', selectedFrameworkFromSession.value)
        } else {
          console.log('ℹ️ DEBUG: No framework filter active - showing all events')
          selectedFrameworkFromSession.value = null
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework in EventsCalendar:', error)
        selectedFrameworkFromSession.value = null
      }
    }

    const fetchEvents = async () => {
      try {
        loading.value = true
        error.value = null
        
        console.log('[EventsCalendar] Checking for cached event data...')
        
        // ==========================================
        // NEW: Check if data is already cached from HomeView prefetch
        // ==========================================
        if (eventDataService.hasValidCache()) {
          console.log('[EventsCalendar] ✅ Using cached event data from HomeView prefetch')
          events.value = eventDataService.getData('events') || []
          loading.value = false
          return
        }
        
        // ==========================================
        // Fallback: If cache is empty, wait for prefetch or fetch directly
        // ==========================================
        console.log('[EventsCalendar] No cache found, checking for ongoing prefetch...')
        
        if (window.eventDataFetchPromise) {
          console.log('[EventsCalendar] ⏳ Waiting for ongoing prefetch to complete...')
          await window.eventDataFetchPromise
          events.value = eventDataService.getData('events') || []
          loading.value = false
          return
        }
        
        // Last resort: Fetch from API
        console.log('[EventsCalendar] 🔄 Fetching event data from API (cache miss)...')
        const response = await eventService.getEventsForCalendar()
        if (response.data.success) {
          events.value = response.data.events
          // Cache the fetched data for future use
          eventDataService.setData('events', events.value)
        } else {
          error.value = response.data.message || 'Failed to fetch calendar events'
        }
      } catch (err) {
        console.error('Error fetching calendar events:', err)
        error.value = 'Failed to fetch calendar events. Please try again.'
        PopupService.error('Failed to fetch calendar events. Please try again.', 'Error')
      } finally {
        loading.value = false
      }
    }

    onMounted(async () => {
      // Check for framework selection from session
      await checkSelectedFrameworkFromSession()
      
      // Then fetch events
      await fetchEvents()
    })

    return {
      viewMode,
      events,
      calendarEvents,
      loading,
      error,
      selectedEvent,
      showPopup,
      currentDate,
      monthNames,
      calendarDays,
      selectedFrameworkFromSession,
      setViewMode,
      handleEventClick,
      closePopup,
      handleEdit,
      handleAttachEvidence,
      handleApprove,
      handleReject,
      handleArchive,
      previousMonth,
      nextMonth,
      getStatusColor,
      getCategoryColor,
      getDayEvents,
      fetchEvents
    }
  }
}
</script>

<style>
/* Events Calendar Container - Single container for whole page */
.events-calendar-container {
  padding: 24px;
  padding-top: 40px;
  min-height: 100vh;
  margin-left: -30px;
}

/* Events Calendar Header */
.events-calendar-header {
  margin-bottom: 32px;
}

.events-calendar-header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.events-calendar-title-section {
  flex: 1;
}

.events-calendar-title {
  font-size: 1.7rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.events-calendar-subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
  font-weight: 500;
}

/* View Toggle Buttons */
.events-calendar-view-toggle {
  display: flex;
  align-items: center;
  background: #f1f5f9;
  border-radius: 12px;
  padding: 4px;
  gap: 4px;
}

.events-calendar-view-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.events-calendar-view-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.events-calendar-view-btn-active {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.events-calendar-view-btn-inactive {
  background: #ffffff;
  color: #6b7280;
}

.events-calendar-view-btn-inactive:hover {
  background: #f8f9fa;
  color: #374151;
}

.events-calendar-view-icon {
  width: 16px;
  height: 16px;
}

/* Loading State */
.events-calendar-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
}

.events-calendar-loading-content {
  text-align: center;
}

.events-calendar-loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: events-calendar-spin 1s linear infinite;
  margin: 0 auto 16px;
}

.events-calendar-loading-text {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
}

/* Error State */
.events-calendar-error {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
}

.events-calendar-error-content {
  text-align: center;
}

.events-calendar-error-icon {
  margin-bottom: 16px;
}

.events-calendar-error-svg {
  width: 48px;
  height: 48px;
  color: #ef4444;
  margin: 0 auto;
}

.events-calendar-error-message {
  font-size: 1rem;
  color: #ef4444;
  margin: 0 0 16px 0;
}

.events-calendar-error-retry {
  padding: 12px 24px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.events-calendar-error-retry:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

/* Empty State */
.events-calendar-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
}

.events-calendar-empty-content {
  text-align: center;
}

.events-calendar-empty-icon {
  margin-bottom: 16px;
}

.events-calendar-empty-svg {
  width: 48px;
  height: 48px;
  color: #9ca3af;
  margin: 0 auto;
}

.events-calendar-empty-title {
  font-size: 1.1rem;
  color: #6b7280;
  margin: 0 0 8px 0;
  font-weight: 600;
}

.events-calendar-empty-subtitle {
  font-size: 0.9rem;
  color: #9ca3af;
  margin: 0;
}

/* Events Calendar Table */
.events-calendar-table-container {
  overflow: hidden;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.events-calendar-table-wrapper {
  overflow-x: auto;
  overflow-y: auto;
  max-height: calc(100vh - 200px);
}

.events-calendar-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 600px;
}

.events-calendar-table-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.events-calendar-table-th {
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

.events-calendar-title-col {
  min-width: 150px;
  max-width: 180px;
}

.events-calendar-id-col {
  min-width: 90px;
  max-width: 110px;
}

.events-calendar-category-col {
  min-width: 100px;
  max-width: 120px;
}

.events-calendar-date-col {
  min-width: 100px;
  max-width: 120px;
}

.events-calendar-recurrence-col {
  min-width: 100px;
  max-width: 120px;
}

.events-calendar-status-col {
  min-width: 100px;
  max-width: 120px;
}

.events-calendar-table-body {
  background: #ffffff;
  position: relative;
  z-index: 1;
  isolation: isolate;
}

.events-calendar-table-row {
  transition: all 0.2s ease;
  border-bottom: 1px solid #f3f4f6;
  position: relative;
  z-index: 1;
}

.events-calendar-table-row:hover {
  background: #f8f9fa;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.events-row-even {
  background: #ffffff;
}

.events-row-odd {
  background: #fafafa;
}

.events-calendar-table-td {
  padding: 12px 12px;
  font-size: 0.85rem;
  color: #374151;
  vertical-align: middle;
  text-align: left;
  position: relative;
  z-index: 1;
  background-color: inherit;
}

.events-calendar-title-cell {
  text-align: left;
  vertical-align: top;
  word-wrap: break-word;
  overflow: visible;
  position: static;
  z-index: 1;
}

/* Event Title Link - Simple black text, no background */
.events-calendar-title-link,
button.events-calendar-title-link,
.events-calendar-table-td button.events-calendar-title-link {
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

.events-calendar-title-link:hover,
button.events-calendar-title-link:hover,
.events-calendar-table-td button.events-calendar-title-link:hover {
  color: #3b82f6 !important;
  text-decoration: underline !important;
  background: transparent !important;
  background-color: transparent !important;
}

.events-calendar-id-cell {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 600;
}

.events-calendar-category-cell {
  font-weight: 500;
  color: #6b7280;
}

.events-calendar-date-cell {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.75rem;
  color: #6b7280;
}

.events-calendar-recurrence-cell {
  font-weight: 500;
  color: #374151;
}

.events-calendar-status-cell {
  text-align: left;
}

.events-calendar-status-display {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-height: 20px;
}

.events-calendar-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.events-calendar-status-text {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  line-height: 1;
  white-space: nowrap;
}

/* Status Dot Colors */
.events-calendar-status-dot.events-calendar-status-approved {
  background-color: #22c55e;
}

.events-calendar-status-dot.events-calendar-status-pending-review {
  background-color: #f59e0b;
}

.events-calendar-status-dot.events-calendar-status-rejected {
  background-color: #ef4444;
}

.events-calendar-status-dot.events-calendar-status-draft {
  background-color: #6b7280;
}

.events-calendar-status-dot.events-calendar-status-under-review {
  background-color: #3b82f6;
}

.events-calendar-status-dot.events-calendar-status-completed {
  background-color: #22c55e;
}

.events-calendar-status-dot.events-calendar-status-cancelled {
  background-color: #6b7280;
}

.events-calendar-status-dot.events-calendar-status-default {
  background-color: #6b7280;
}

/* Status Text Colors */
.events-calendar-status-text.events-calendar-status-approved {
  color: #22c55e;
}

.events-calendar-status-text.events-calendar-status-pending-review {
  color: #f59e0b;
}

.events-calendar-status-text.events-calendar-status-rejected {
  color: #ef4444;
}

.events-calendar-status-text.events-calendar-status-draft {
  color: #6b7280;
}

.events-calendar-status-text.events-calendar-status-under-review {
  color: #3b82f6;
}

.events-calendar-status-text.events-calendar-status-completed {
  color: #22c55e;
}

.events-calendar-status-text.events-calendar-status-cancelled {
  color: #6b7280;
}

.events-calendar-status-text.events-calendar-status-default {
  color: #6b7280;
}

/* Calendar View */
.events-calendar-view-container {
  overflow: hidden;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.events-calendar-view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  border-bottom: 1px solid #e5e7eb;
  background: #f8f9fa;
}

.events-calendar-view-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.events-calendar-view-navigation {
  display: flex;
  align-items: center;
  gap: 8px;
}

.events-calendar-nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  background: #ffffff;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.events-calendar-nav-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.events-calendar-nav-icon {
  width: 16px;
  height: 16px;
}

/* Calendar Grid */
.events-calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  background: #e5e7eb;
}

.events-calendar-day-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 12px 8px;
  text-align: center;
  font-size: 0.8rem;
  font-weight: 700;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.events-calendar-day-cell {
  background: #ffffff;
  min-height: 120px;
  padding: 8px;
  border: 1px solid #f3f4f6;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
}

.events-calendar-day-cell:hover {
  background: #f8f9fa;
}

.events-calendar-day-current-month {
  color: #1f2937;
}

.events-calendar-day-other-month {
  color: #9ca3af;
  background: #fafafa;
}

.events-calendar-day-number {
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: inherit;
}

.events-calendar-day-events {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  overflow: visible;
}

.events-calendar-event-item {
  width: 100%;
  text-align: left;
  padding: 6px 8px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.75rem;
  font-weight: 400;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  min-height: auto;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.events-calendar-event-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.events-calendar-event-title {
  font-weight: 400;
  margin-bottom: 2px;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: break-word;
  line-height: 1.2;
}

.events-calendar-event-category {
  font-size: 0.7rem;
  opacity: 0.8;
  white-space: normal;
  word-wrap: break-word;
  overflow-wrap: break-word;
  line-height: 1.1;
}

/* Category Colors */
.events-calendar-category-access-review {
  background: #ffffff;
  border: 2px solid #3b82f6;
  color: #1e40af;
}

.events-calendar-category-dr-drill {
  background: #ffffff;
  border: 2px solid #ec4899;
  color: #be185d;
}

.events-calendar-category-patch-mgmt {
  background: #ffffff;
  border: 2px solid #22c55e;
  color: #166534;
}

.events-calendar-category-audit {
  background: #ffffff;
  border: 2px solid #a855f7;
  color: #6b21a8;
}

.events-calendar-category-risk-review {
  background: #ffffff;
  border: 2px solid #f97316;
  color: #9a3412;
}

.events-calendar-category-training {
  background: #ffffff;
  border: 2px solid #6366f1;
  color: #3730a3;
}

.events-calendar-category-risk-assessment {
  background: #ffffff;
  border: 2px solid #f59e0b;
  color: #92400e;
}

.events-calendar-category-compliance {
  background: #ffffff;
  border: 2px solid #14b8a6;
  color: #134e4a;
}

.events-calendar-category-security {
  background: #ffffff;
  border: 2px solid #ef4444;
  color: #991b1b;
}

.events-calendar-category-incident {
  background: #ffffff;
  border: 2px solid #ec4899;
  color: #be185d;
}

.events-calendar-category-policy {
  background: #ffffff;
  border: 2px solid #06b6d4;
  color: #155e75;
}

.events-calendar-category-review {
  background: #ffffff;
  border: 2px solid #f59e0b;
  color: #92400e;
}

.events-calendar-category-assessment {
  background: #ffffff;
  border: 2px solid #84cc16;
  color: #365314;
}

.events-calendar-category-management {
  background: #ffffff;
  border: 2px solid #64748b;
  color: #475569;
}

/* Generic category colors */
.events-calendar-category-blue {
  background: #ffffff;
  border: 2px solid #3b82f6;
  color: #1e40af;
}

.events-calendar-category-pink {
  background: #ffffff;
  border: 2px solid #ec4899;
  color: #be185d;
}

.events-calendar-category-green {
  background: #ffffff;
  border: 2px solid #22c55e;
  color: #166534;
}

.events-calendar-category-purple {
  background: #ffffff;
  border: 2px solid #a855f7;
  color: #6b21a8;
}

.events-calendar-category-orange {
  background: #ffffff;
  border: 2px solid #f97316;
  color: #9a3412;
}

.events-calendar-category-indigo {
  background: #ffffff;
  border: 2px solid #6366f1;
  color: #3730a3;
}

.events-calendar-category-yellow {
  background: #ffffff;
  border: 2px solid #f59e0b;
  color: #92400e;
}

.events-calendar-category-teal {
  background: #ffffff;
  border: 2px solid #14b8a6;
  color: #134e4a;
}

.events-calendar-category-red {
  background: #ffffff;
  border: 2px solid #ef4444;
  color: #991b1b;
}

.events-calendar-category-rose {
  background: #ffffff;
  border: 2px solid #ec4899;
  color: #be185d;
}

.events-calendar-category-default {
  background: #ffffff;
  border: 2px solid #64748b;
  color: #475569;
}

/* Responsive Design */
@media (max-width: 768px) {
  .events-calendar-container {
    margin-left: 0;
    padding: 16px;
  }
  
  
  .events-calendar-title {
    font-size: 1.5rem;
  }
  
  .events-calendar-header-content {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .events-calendar-view-toggle {
    justify-content: center;
  }
  
  .events-calendar-view-btn {
    padding: 10px 16px;
    font-size: 0.85rem;
  }
  
  .events-calendar-table-th,
  .events-calendar-table-td {
    padding: 12px 8px;
  }
  
  .events-calendar-view-header {
    padding: 20px;
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .events-calendar-view-navigation {
    justify-content: center;
  }
  
  .events-calendar-day-cell {
    min-height: 80px;
    padding: 6px;
  }
  
  .events-calendar-event-item {
    padding: 4px 6px;
    font-size: 0.7rem;
  }
  
  .events-calendar-event-title {
    font-size: 0.7rem;
  }
  
  .events-calendar-event-category {
    font-size: 0.65rem;
  }
}

/* Animations */
@keyframes events-calendar-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes events-calendar-fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.events-calendar-table-container,
.events-calendar-view-container {
  animation: events-calendar-fadeIn 0.5s ease-out;
}

/* Focus states for accessibility */
.events-calendar-view-btn:focus,
.events-calendar-nav-btn:focus,
.events-calendar-title-link:focus,
.events-calendar-event-item:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Scrollbar styling */
.events-calendar-table-wrapper::-webkit-scrollbar {
  height: 8px;
}

.events-calendar-table-wrapper::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.events-calendar-table-wrapper::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.events-calendar-table-wrapper::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
