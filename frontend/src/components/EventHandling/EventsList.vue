<template>
  <div class="events-list-container">
    <!-- Header Section -->
    <div class="events-view-header">
      <div class="events-header-content">
        <div class="events-title-section">
          <h1 class="events-view-title">Events List</h1>
          <p class="events-view-subtitle">Repository of all created events</p>
        </div>
        <div class="events-header-actions">
          <router-link
            v-if="canCreateEvents"
            to="/event-handling/create"
            class="events-create-btn"
          >
            <svg class="events-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            Create Event
          </router-link>
        </div>
      </div>
    </div>

    <!-- Filters Section -->
    <div class="events-filters-section">
      <EventFilters :on-export="handleExport" :selected-framework-from-session="selectedFrameworkFromSession" @filter-change="handleFilterChange" />
    </div>

    <!-- Events Table - Fill remaining screen space -->
    <div class="events-content-wrapper">
      <!-- Loading State -->
      <div v-if="loading" class="events-loading-spinner">
        <div class="events-spinner-content">
          <div class="events-spinner-circle"></div>
          <p class="events-loading-text">Loading events...</p>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="events-error-state">
        <div class="events-error-content">
          <div class="events-error-icon">
            <svg class="events-error-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </div>
          <p class="events-error-message">{{ error }}</p>
          <button @click="fetchEvents" class="events-retry-btn">
            Try Again
          </button>
        </div>
      </div>

      <!-- Empty State -->
      <!-- <div v-else-if="filteredEvents.length === 0" class="events-empty-state">
        <div class="events-empty-content">
          <div class="events-empty-icon">
            <svg class="events-empty-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
            </svg>
          </div>
          <p class="events-empty-message">No events found</p>
          <router-link
            v-if="canCreateEvents"
            to="/event-handling/create"
            class="events-create-first-btn"
          >
            <svg class="events-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            Create Your First Event
          </router-link>
        </div>
      </div> -->

      <!-- Events by Status Groups -->
      <div v-else class="events-status-groups">
        <!-- Approved Events -->
        <div class="events-status-group">
          <div class="events-status-header" @click="toggleStatusGroup('approved')">
            <div class="events-status-header-content">
              <svg class="events-status-chevron" :class="{ 'events-status-chevron-open': expandedGroups.approved }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
              </svg>
              <span class="events-status-title">Approved Events</span>
              <span class="events-status-count">{{ getEventsByStatus('Approved').length }}</span>
            </div>
          </div>
          <div v-if="expandedGroups.approved" class="events-status-content">
            <div v-if="getEventsByStatus('Approved').length === 0" class="events-status-empty">
              No approved events found
            </div>
            <div v-else class="events-table-container">
              <div class="events-table-wrapper">
                <table class="events-table">
                  <thead class="events-table-header">
                    <tr>
                      <th class="events-table-th events-title-col">Event Title</th>
                      <th class="events-table-th events-id-col">Event ID</th>
                      <th class="events-table-th events-framework-col">Framework</th>
                      <th class="events-table-th events-module-col">Module</th>
                      <th class="events-table-th events-category-col">Category</th>
                      <th class="events-table-th events-owner-col">Owner</th>
                      <th class="events-table-th events-reviewer-col">Reviewer</th>
                      <th class="events-table-th events-created-col">Created At</th>
                    </tr>
                  </thead>
                  <tbody class="events-table-body">
                    <tr v-for="(event, index) in getEventsByStatus('Approved')" :key="event.id" 
                        class="events-table-row" 
                        :class="{ 'events-row-even': index % 2 === 0, 'events-row-odd': index % 2 !== 0 }">
                      <td class="events-table-td events-title-cell" data-label="Event Title">
                        <span
                          @click="handleEventClick(event)"
                          class="events-title-link"
                        >
                          {{ event.title }}
                        </span>
                      </td>
                      <td class="events-table-td events-id-cell" data-label="Event ID">
                        <span
                          @click="handleEventClick(event)"
                          class="events-id-link"
                        >
                          {{ event.event_id }}
                        </span>
                      </td>
                      <td class="events-table-td events-framework-cell" data-label="Framework">
                        {{ event.framework }}
                      </td>
                      <td class="events-table-td events-module-cell" data-label="Module">
                        {{ event.module }}
                      </td>
                      <td class="events-table-td events-category-cell" data-label="Category">
                        {{ event.category || 'N/A' }}
                      </td>
                      <td class="events-table-td events-owner-cell" data-label="Owner">
                        {{ event.owner }}
                      </td>
                      <td class="events-table-td events-reviewer-cell" data-label="Reviewer">
                        {{ event.reviewer }}
                      </td>
                      <td class="events-table-td events-created-cell" data-label="Created">
                        {{ event.created_at }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <!-- Pending Review Events -->
        <div class="events-status-group">
          <div class="events-status-header" @click="toggleStatusGroup('pending')">
            <div class="events-status-header-content">
              <svg class="events-status-chevron" :class="{ 'events-status-chevron-open': expandedGroups.pending }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
              </svg>
              <span class="events-status-title">Pending Review Events</span>
              <span class="events-status-count">{{ getEventsByStatus('Pending Review').length }}</span>
            </div>
          </div>
          <div v-if="expandedGroups.pending" class="events-status-content">
            <div v-if="getEventsByStatus('Pending Review').length === 0" class="events-status-empty">
              No pending review events found
            </div>
            <div v-else class="events-table-container">
              <div class="events-table-wrapper">
                <table class="events-table">
                  <thead class="events-table-header">
                    <tr>
                      <th class="events-table-th events-title-col">Event Title</th>
                      <th class="events-table-th events-id-col">Event ID</th>
                      <th class="events-table-th events-framework-col">Framework</th>
                      <th class="events-table-th events-module-col">Module</th>
                      <th class="events-table-th events-category-col">Category</th>
                      <th class="events-table-th events-owner-col">Owner</th>
                      <th class="events-table-th events-reviewer-col">Reviewer</th>
                      <th class="events-table-th events-created-col">Created</th>
                    </tr>
                  </thead>
                  <tbody class="events-table-body">
                    <tr v-for="(event, index) in getEventsByStatus('Pending Review')" :key="event.id" 
                        class="events-table-row" 
                        :class="{ 'events-row-even': index % 2 === 0, 'events-row-odd': index % 2 !== 0 }">
                      <td class="events-table-td events-title-cell" data-label="Event Title">
                        <span
                          @click="handleEventClick(event)"
                          class="events-title-link"
                        >
                          {{ event.title }}
                        </span>
                      </td>
                      <td class="events-table-td events-id-cell" data-label="Event ID">
                        <span
                          @click="handleEventClick(event)"
                          class="events-id-link"
                        >
                          {{ event.event_id }}
                        </span>
                      </td>
                      <td class="events-table-td events-framework-cell" data-label="Framework">
                        {{ event.framework }}
                      </td>
                      <td class="events-table-td events-module-cell" data-label="Module">
                        {{ event.module }}
                      </td>
                      <td class="events-table-td events-category-cell" data-label="Category">
                        {{ event.category || 'N/A' }}
                      </td>
                      <td class="events-table-td events-owner-cell" data-label="Owner">
                        {{ event.owner }}
                      </td>
                      <td class="events-table-td events-reviewer-cell" data-label="Reviewer">
                        {{ event.reviewer }}
                      </td>
                      <td class="events-table-td events-created-cell" data-label="Created">
                        {{ event.created_at }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <!-- Rejected Events -->
        <div class="events-status-group">
          <div class="events-status-header" @click="toggleStatusGroup('rejected')">
            <div class="events-status-header-content">
              <svg class="events-status-chevron" :class="{ 'events-status-chevron-open': expandedGroups.rejected }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
              </svg>
              <span class="events-status-title">Rejected Events</span>
              <span class="events-status-count">{{ getEventsByStatus('Rejected').length }}</span>
            </div>
          </div>
          <div v-if="expandedGroups.rejected" class="events-status-content">
            <div v-if="getEventsByStatus('Rejected').length === 0" class="events-status-empty">
              No rejected events found
            </div>
            <div v-else class="events-table-container">
              <div class="events-table-wrapper">
                <table class="events-table">
                  <thead class="events-table-header">
                    <tr>
                      <th class="events-table-th events-title-col">Event Title</th>
                      <th class="events-table-th events-id-col">Event ID</th>
                      <th class="events-table-th events-framework-col">Framework</th>
                      <th class="events-table-th events-module-col">Module</th>
                      <th class="events-table-th events-category-col">Category</th>
                      <th class="events-table-th events-owner-col">Owner</th>
                      <th class="events-table-th events-reviewer-col">Reviewer</th>
                      <th class="events-table-th events-created-col">Created</th>
                    </tr>
                  </thead>
                  <tbody class="events-table-body">
                    <tr v-for="(event, index) in getEventsByStatus('Rejected')" :key="event.id" 
                        class="events-table-row" 
                        :class="{ 'events-row-even': index % 2 === 0, 'events-row-odd': index % 2 !== 0 }">
                      <td class="events-table-td events-title-cell" data-label="Event Title">
                        <span
                          @click="handleEventClick(event)"
                          class="events-title-link"
                        >
                          {{ event.title }}
                        </span>
                      </td>
                      <td class="events-table-td events-id-cell" data-label="Event ID">
                        <span
                          @click="handleEventClick(event)"
                          class="events-id-link"
                        >
                          {{ event.event_id }}
                        </span>
                      </td>
                      <td class="events-table-td events-framework-cell" data-label="Framework">
                        {{ event.framework }}
                      </td>
                      <td class="events-table-td events-module-cell" data-label="Module">
                        {{ event.module }}
                      </td>
                      <td class="events-table-td events-category-cell" data-label="Category">
                        {{ event.category || 'N/A' }}
                      </td>
                      <td class="events-table-td events-owner-cell" data-label="Owner">
                        {{ event.owner }}
                      </td>
                      <td class="events-table-td events-reviewer-cell" data-label="Reviewer">
                        {{ event.reviewer }}
                      </td>
                      <td class="events-table-td events-created-cell" data-label="Created">
                        {{ event.created_at }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
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
      :show-approval-actions="isCurrentUserReviewer"
      @close="closePopup"
      @edit="handleEdit"
      @attach-evidence="handleAttachEvidence"
      @approve="handleApprove"
      @reject="handleReject"
      @archive="handleArchive"
    />

    <!-- Approval/Reject/Archive Modals -->
    <ApprovalModal
      :is-open="showApprovalModal"
      type="approve"
      :event-title="selectedEvent?.title || ''"
      @submit="handleModalSubmit"
      @cancel="handleModalCancel"
    />
    <ApprovalModal
      :is-open="showRejectModal"
      type="reject"
      :event-title="selectedEvent?.title || ''"
      @submit="handleModalSubmit"
      @cancel="handleModalCancel"
    />
    <ApprovalModal
      :is-open="showArchiveModal"
      type="archive"
      :event-title="selectedEvent?.title || ''"
      @submit="handleModalSubmit"
      @cancel="handleModalCancel"
    />

    <!-- Event Edit Modal -->
    <EventEditModal
      :is-open="showEditModal"
      :event="selectedEvent"
      @close="handleEditModalClose"
      @saved="handleEditSaved"
    />

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { eventService } from '../../services/api'
import { useEventPermissions } from '../../composables/useEventPermissions'
import EventFilters from './EventFilters.vue'
import EventViewPopup from './EventViewPopup.vue'
import ApprovalModal from './ApprovalModal.vue'
import EventEditModal from './EventEditModal.vue'
import { PopupService } from '../../modules/popus/popupService'
import PopupModal from '../../modules/popus/PopupModal.vue'
import AccessUtils from '../../utils/accessUtils'
import axios from 'axios'
import eventDataService from '../../services/eventService' // NEW: Centralized event data service

export default {
  name: 'EventsList',
  components: {
    EventFilters,
    EventViewPopup,
    ApprovalModal,
    EventEditModal,
    PopupModal
  },
  setup() {
    const router = useRouter()
    
    // Event permissions
    const {
      canViewAllEvents,
      canViewModuleEvents,
      canCreateEvents,
      canEditEvents,
      canApproveEvents,
      canRejectEvents,
      canArchiveEvents,
      canViewEventAnalytics,
      hasEventAccess,
      fetchEventPermissions,
      canViewModule,
      getFilteredModules
    } = useEventPermissions()
    
    const selectedEvent = ref(null)
    const showPopup = ref(false)
    const showEditModal = ref(false)
    const showApprovalModal = ref(false)
    const showRejectModal = ref(false)
    const showArchiveModal = ref(false)
    const modalType = ref('approve')
    const events = ref([])
    const filteredEvents = ref([])
    const loading = ref(false)
    const error = ref(null)
    const selectedFrameworkFromSession = ref(null)
    const filters = ref({
      framework: '',
      module: '',
      category: '',
      owner: ''
    })
    
    const expandedGroups = ref({
      approved: true,
      pending: true,
      rejected: false
    })

    // Export utility functions
    const exportToCSV = (data, filename) => {
      if (!data || data.length === 0) return
      
      const headers = Object.keys(data[0])
      const csvContent = [
        headers.join(','),
        ...data.map(row => 
          headers.map(header => {
            const value = row[header] || ''
            // Escape commas and quotes in CSV
            return `"${String(value).replace(/"/g, '""')}"`
          }).join(',')
        )
      ].join('\n')
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `${filename}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }

    const exportToJSON = (data, filename) => {
      if (!data || data.length === 0) return
      
      const jsonContent = JSON.stringify(data, null, 2)
      const blob = new Blob([jsonContent], { type: 'application/json' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `${filename}.json`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }

    const exportToXML = (data, filename) => {
      if (!data || data.length === 0) return
      
      let xmlContent = '<?xml version="1.0" encoding="UTF-8"?>\n<events>\n'
      
      data.forEach(row => {
        xmlContent += '  <event>\n'
        Object.keys(row).forEach(key => {
          const value = String(row[key] || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
          xmlContent += `    <${key.replace(/\s+/g, '_').toLowerCase()}>${value}</${key.replace(/\s+/g, '_').toLowerCase()}>\n`
        })
        xmlContent += '  </event>\n'
      })
      
      xmlContent += '</events>'
      
      const blob = new Blob([xmlContent], { type: 'application/xml' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `${filename}.xml`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }

    const exportToExcel = async (data, filename) => {
      try {
        // Create a proper CSV file that Excel can open
        const headers = Object.keys(data[0])
        const csvContent = [
          headers.join(','),
          ...data.map(row => 
            headers.map(header => {
              const value = row[header] || ''
              // Escape commas and quotes in CSV
              const escapedValue = String(value).replace(/"/g, '""')
              // Wrap in quotes if contains comma, quote, or newline
              if (escapedValue.includes(',') || escapedValue.includes('"') || escapedValue.includes('\n')) {
                return `"${escapedValue}"`
              }
              return escapedValue
            }).join(',')
          )
        ].join('\n')
        
        // Add BOM for proper UTF-8 encoding in Excel
        const BOM = '\uFEFF'
        const csvWithBOM = BOM + csvContent
        
        const blob = new Blob([csvWithBOM], { type: 'text/csv;charset=utf-8;' })
        const link = document.createElement('a')
        const url = URL.createObjectURL(blob)
        link.setAttribute('href', url)
        link.setAttribute('download', `${filename}.csv`)
        link.style.visibility = 'hidden'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
      } catch (error) {
        console.error('Excel export error:', error)
        throw new Error('Failed to export to Excel format')
      }
    }

    const exportToPDF = async (data, filename) => {
      try {
        // Create a print-ready HTML document that can be easily converted to PDF
        const headers = Object.keys(data[0])
        
        let htmlContent = `
          <!DOCTYPE html>
          <html>
            <head>
              <meta charset="UTF-8">
              <title>Events Export Report</title>
              <style>
                @page {
                  margin: 0.5in;
                  size: A4;
                }
                body { 
                  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                  margin: 0;
                  padding: 20px;
                  font-size: 11px;
                  line-height: 1.3;
                  color: #333;
                }
                .header {
                  text-align: center;
                  margin-bottom: 30px;
                  border-bottom: 3px solid #4CAF50;
                  padding-bottom: 15px;
                }
                .header h1 {
                  color: #2E7D32;
                  margin: 0;
                  font-size: 24px;
                  font-weight: bold;
                }
                .header .subtitle {
                  color: #666;
                  margin-top: 5px;
                  font-size: 14px;
                }
                .export-info {
                  background-color: #E8F5E8;
                  border: 1px solid #4CAF50;
                  padding: 15px;
                  border-radius: 8px;
                  margin-bottom: 25px;
                  font-size: 12px;
                }
                .export-info h3 {
                  margin: 0 0 10px 0;
                  color: #2E7D32;
                  font-size: 14px;
                }
                .export-info p {
                  margin: 5px 0;
                }
                table { 
                  border-collapse: collapse; 
                  width: 100%; 
                  margin-top: 10px;
                  font-size: 10px;
                }
                th, td { 
                  border: 1px solid #ddd; 
                  padding: 8px 6px; 
                  text-align: left; 
                  vertical-align: top;
                }
                th { 
                  background-color: #4CAF50; 
                  color: white; 
                  font-weight: bold; 
                  font-size: 11px;
                  text-transform: uppercase;
                  letter-spacing: 0.5px;
                }
                tr:nth-child(even) { 
                  background-color: #f8f9fa; 
                }
                tr:nth-child(odd) { 
                  background-color: white; 
                }
                .footer {
                  margin-top: 30px;
                  text-align: center;
                  font-size: 10px;
                  color: #666;
                  border-top: 1px solid #ddd;
                  padding-top: 15px;
                }
                @media print {
                  body { margin: 0; padding: 15px; }
                  .export-info { 
                    background-color: #f0f0f0 !important;
                    border: 1px solid #ccc !important;
                  }
                }
              </style>
            </head>
            <body>
              <div class="header">
                <h1>📊 Events Export Report</h1>
                <div class="subtitle">Comprehensive Events Data Export</div>
              </div>
              
              <div class="export-info">
                <h3>📋 Export Information</h3>
                <p><strong>Generated On:</strong> ${new Date().toLocaleString()}</p>
                <p><strong>Total Events:</strong> ${data.length}</p>
                <p><strong>Export Format:</strong> PDF-Ready HTML</p>
                <p><strong>Report Type:</strong> Complete Events Data</p>
              </div>
              
              <table>
                <thead>
                  <tr>
                    ${headers.map(header => `<th>${header}</th>`).join('')}
                  </tr>
                </thead>
                <tbody>
                  ${data.map(row => 
                    `<tr>${headers.map(header => `<td>${String(row[header] || '').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')}</td>`).join('')}</tr>`
                  ).join('')}
                </tbody>
              </table>
              
              <div class="footer">
                <p>This report was generated automatically by the Events Management System</p>
                <p>For best PDF results, use "Print to PDF" in your browser (Ctrl+P → Save as PDF)</p>
              </div>
            </body>
          </html>
        `
        
        // Create blob and download as HTML file
        const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' })
        const link = document.createElement('a')
        const url = URL.createObjectURL(blob)
        link.setAttribute('href', url)
        link.setAttribute('download', `${filename}_Report.html`)
        link.style.visibility = 'hidden'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
        
      } catch (error) {
        console.error('PDF export error:', error)
        throw new Error('Failed to export to PDF format')
      }
    }

    const handleExport = async (format) => {
      try {
        PopupService.success(`Starting export of events as ${format}...`, 'Export Started')
        
        // Get all events (not just filtered ones) for export
        const allEvents = events.value
        
        if (allEvents.length === 0) {
          PopupService.warning('No events available to export.', 'No Data')
          return
        }
        
        // Prepare data for export
        const exportData = allEvents.map(event => ({
          'Event ID': event.id || event.event_id || 'N/A',
          'Event Title': event.title || 'N/A',
          'Framework': event.framework,  // Backend now handles random assignment
          'Module': event.module,        // Backend now handles random assignment
          'Category': event.category || 'General',
          'Owner': event.owner || 'Not Assigned',
          'Reviewer': event.reviewer || 'Not Assigned',
          'Status': event.status || 'Pending Review',
          'Priority': event.priority || 'Medium',
          'Created Date': event.createdDate || event.created_date || event.created_at || 'N/A',
          'Updated Date': event.updatedDate || event.updated_date || 'N/A',
          'Description': event.description || 'No description'
        }))
        
        // Export based on format
        switch (format.toLowerCase()) {
          case 'excel':
            await exportToExcel(exportData, 'Events_Export')
            break
          case 'csv':
            await exportToCSV(exportData, 'Events_Export')
            break
          case 'json':
            await exportToJSON(exportData, 'Events_Export')
            break
          case 'pdf':
            await exportToPDF(exportData, 'Events_Export')
            break
          case 'xml':
            await exportToXML(exportData, 'Events_Export')
            break
          default:
            PopupService.error(`Unsupported export format: ${format}`, 'Export Error')
        }
        
        PopupService.success(`Events exported successfully as ${format}!`, 'Export Complete')
        
      } catch (error) {
        console.error('Export error:', error)
        PopupService.error(`Failed to export events: ${error.message}`, 'Export Error')
      }
    }

    const handleFilterChange = (newFilters) => {
      filters.value = newFilters
      applyFilters()
    }

    const applyFilters = () => {
      let filtered = [...events.value]

      if (filters.value.framework) {
        filtered = filtered.filter(event => event.framework === filters.value.framework)
      }
      if (filters.value.module) {
        filtered = filtered.filter(event => event.module === filters.value.module)
      }
      if (filters.value.category) {
        filtered = filtered.filter(event => event.category === filters.value.category)
      }
      if (filters.value.owner) {
        filtered = filtered.filter(event => event.owner === filters.value.owner)
      }

      filteredEvents.value = filtered
    }

    const handleEventClick = async (event) => {
      try {
        // Fetch detailed event information including evidence
        const response = await eventService.getEventDetails(event.id)
        if (response.data.success) {
          // Store the event data in sessionStorage for the event details page
          const eventDetailsData = {
            ...response.data.event,
            isFromList: true
          }
          sessionStorage.setItem('eventDetailsData', JSON.stringify(eventDetailsData))
          
          // Navigate to event details page
          router.push('/event-handling/details')
        } else {
          console.error('Failed to fetch event details:', response.data.message)
          PopupService.error('Failed to fetch event details. Please try again.', 'Error')
        }
      } catch (err) {
        console.error('Error fetching event details:', err)
        PopupService.error('Failed to load event details. Please try again.', 'Error')
      }
    }

    const closePopup = () => {
      showPopup.value = false
    }

    const handleEdit = () => {
      showPopup.value = false
      
      // Store the event data in sessionStorage for the event creation page to use
      if (selectedEvent.value) {
        sessionStorage.setItem('editEventData', JSON.stringify({
          id: selectedEvent.value.id,
          title: selectedEvent.value.title,
          description: selectedEvent.value.description,
          framework: selectedEvent.value.framework,
          module: selectedEvent.value.module,
          category: selectedEvent.value.category,
          owner: selectedEvent.value.owner,
          reviewer: selectedEvent.value.reviewer,
          recurrence: selectedEvent.value.recurrence_type || 'Non-Recurring',
          frequency: selectedEvent.value.frequency,
          startDate: selectedEvent.value.start_date,
          endDate: selectedEvent.value.end_date,
          evidence: selectedEvent.value.evidence || [], // Include existing evidence
          evidence_string: selectedEvent.value.evidence_string || '', // Include evidence string
          isEdit: true
        }))
      }
      
      // Navigate to event creation page
      router.push('/event-handling/create')
    }

    const handleAttachEvidence = () => {
      console.log('Attach evidence for event:', selectedEvent.value?.id)
      showPopup.value = false
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
        const eventId = selectedEvent.value?.id
        
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
        } else {
          // Handle archive or other actions
          console.log(`${modalType.value} event:`, eventId, comment)
        }
        
        if (response && response.data.success) {
          // Store status update for Events Queue to pick up
          const statusUpdate = {
            id: eventId,
            status: modalType.value === 'approve' ? 'Approved' : 
                   modalType.value === 'reject' ? 'Rejected' : 
                   modalType.value === 'archive' ? 'Archived' : 'Updated'
          }
          
          // Get existing updates or create new array
          const existingUpdates = sessionStorage.getItem('eventStatusUpdates')
          const updates = existingUpdates ? JSON.parse(existingUpdates) : []
          updates.push(statusUpdate)
          sessionStorage.setItem('eventStatusUpdates', JSON.stringify(updates))
          
          console.log('Stored status update for Events Queue:', statusUpdate)
          
          // Update the cache with the new status
          if (eventId) {
            eventDataService.updateEvent(eventId, { 
              status: statusUpdate.status 
            })
            console.log('[EventsList] ✅ Updated event status in cache:', eventId, statusUpdate.status)
          }
          
          // Refresh the events list
          await fetchEvents()
          alert(response.data.message)
        } else if (response) {
          alert(response.data.message || 'Action failed')
        }
        
        showApprovalModal.value = false
        showRejectModal.value = false
        showArchiveModal.value = false
        showPopup.value = false
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

    const handleEditModalClose = () => {
      showEditModal.value = false
    }

    const handleEditSaved = async (updatedEvent) => {
      try {
        console.log('Event saved, updating list...', updatedEvent)
        
        // Close the modal first
        showEditModal.value = false
        
        // Update the cache with the updated event
        if (updatedEvent && updatedEvent.id) {
          eventDataService.updateEvent(updatedEvent.id, updatedEvent)
          console.log('[EventsList] ✅ Updated event in cache:', updatedEvent.id)
        }
        
        // Refresh the entire events list to ensure we have the latest data
        console.log('Refreshing events list...')
        await fetchEvents()
        console.log('Events list refreshed successfully')
        
        // Show success message
        PopupService.success('Event updated successfully!', 'Success')
      } catch (error) {
        console.error('Error refreshing events list after update:', error)
        console.error('Error details:', error.message, error.stack)
        
        // Still show success for the update, but mention the refresh issue
        PopupService.warning('Event updated successfully, but there was an issue refreshing the list. Please refresh the page to see the latest changes.', 'Warning')
      }
    }

    const getStatusColor = (status) => {
      switch (status) {
        case 'Approved': return 'events-status-approved'
        case 'Pending Review': return 'events-status-pending'
        case 'Rejected': return 'events-status-rejected'
        case 'Draft': return 'events-status-draft'
        case 'Under Review': return 'events-status-under-review'
        case 'Completed': return 'events-status-completed'
        case 'Cancelled': return 'events-status-cancelled'
        default: return 'events-status-draft'
      }
    }

    const toggleStatusGroup = (group) => {
      expandedGroups.value[group] = !expandedGroups.value[group]
    }

    const getEventsByStatus = (status) => {
      if (status === 'Pending Review') {
        // Include both 'Pending Review' and 'Under Review' events in pending section
        return filteredEvents.value.filter(event => 
          event.status === 'Pending Review' || event.status === 'Under Review'
        )
      }
      return filteredEvents.value.filter(event => event.status === status)
    }

    // Check if current user is the reviewer for the selected event
    const isCurrentUserReviewer = computed(() => {
      if (!selectedEvent.value) return false
      const currentUserId = localStorage.getItem('user_id')
      return selectedEvent.value.reviewer_id == currentUserId
    })

    const fetchEvents = async () => {
      try {
        loading.value = true
        error.value = null
        
        // ==========================================
        // NEW: Check if data is already cached from HomeView prefetch
        // ==========================================
        console.log('[EventsList] Checking for cached event data...')
        
        if (eventDataService.hasValidCache()) {
          // Use cached data from HomeView prefetch
          console.log('[EventsList] ✅ Using cached event data from HomeView prefetch')
          events.value = eventDataService.getData('events') || []
          applyFilters() // Apply current filters to the cached data
          loading.value = false
          return
        }
        
        // ==========================================
        // Fallback: If cache is empty, wait for prefetch or fetch directly
        // ==========================================
        console.log('[EventsList] No cache found, checking for ongoing prefetch...')
        
        // Check if prefetch is in progress
        if (window.eventDataFetchPromise) {
          console.log('[EventsList] ⏳ Waiting for ongoing prefetch to complete...')
          await window.eventDataFetchPromise
          events.value = eventDataService.getData('events') || []
          applyFilters()
          loading.value = false
          return
        }
        
        // Last resort: Fetch directly from API
        console.log('[EventsList] 🔄 Fetching event data from API (cache miss)...')
        const response = await eventService.getEventsList()
        if (response.data.success) {
          events.value = response.data.events
          // Cache the fetched data for future use
          eventDataService.setData('events', events.value)
          applyFilters() // Apply current filters to the new data
        } else {
          PopupService.error(response.data.message || 'Failed to fetch events', 'Error')
        }
      } catch (err) {
        console.error('Error fetching events:', err)
        
        // Check if it's an access denied error (403)
        if (err.response && err.response.status === 403) {
          AccessUtils.showAccessDenied('Event Management - Events List', 'You don\'t have permission to view events. Required permission: event.view_all_event or event.view_module_event')
        } else {
          PopupService.error('Failed to fetch events. Please try again.', 'Error')
        }
      } finally {
        loading.value = false
      }
    }

    // Check for selected framework from session (similar to other modules)
    const checkSelectedFrameworkFromSession = async () => {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in EventsList...')
        const response = await axios.get('/api/frameworks/get-selected/', {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        })
        
        console.log('🔍 DEBUG: Framework response in EventsList:', response.data)
        
        if (response.data && response.data.frameworkId) {
          const frameworkIdFromSession = response.data.frameworkId.toString()
          console.log('✅ DEBUG: Found selected framework in session for EventsList:', frameworkIdFromSession)
          
          // Set the selected framework from session
          selectedFrameworkFromSession.value = frameworkIdFromSession
          console.log('📊 DEBUG: Events are now filtered by framework:', frameworkIdFromSession)
          console.log('📊 DEBUG: selectedFrameworkFromSession.value set to:', selectedFrameworkFromSession.value)
        } else {
          console.log('ℹ️ DEBUG: No framework filter active - showing all events')
          selectedFrameworkFromSession.value = null
        }
      } catch (error) {
        console.log('⚠️ DEBUG: Could not check framework selection from session:', error)
        // Continue without framework filtering indication
      }
    }

    const route = useRoute()
    
    onMounted(async () => {
      // Fetch user permissions first
      await fetchEventPermissions()
      
      // Check for framework selection from session
      await checkSelectedFrameworkFromSession()
      
      // Then fetch events
      await fetchEvents()
      
      // Add focus event listener to refresh events when user returns to page
      window.addEventListener('focus', handleWindowFocus)
      
      // Listen for unarchive events to refresh the events list
      window.addEventListener('eventUnarchived', handleEventUnarchived)
    })
    
    // Watch for route changes to refresh events list
    watch(() => route.path, async (newPath, oldPath) => {
      // If navigating to events list from create page, refresh the list
      if (newPath === '/event-handling/list' && oldPath === '/event-handling/create') {
        console.log('Navigated to events list from create page, refreshing events...')
        await fetchEvents()
      }
    })
    
    // Handle window focus to refresh events list
    const handleWindowFocus = async () => {
      console.log('Window focused, refreshing events list...')
      await fetchEvents()
    }
    
    // Handle event unarchived to refresh events list
    const handleEventUnarchived = async (event) => {
      console.log('Event unarchived, refreshing events list...', event.detail)
      await fetchEvents()
    }
    
    // Clean up event listeners when component unmounts
    const cleanup = () => {
      window.removeEventListener('focus', handleWindowFocus)
      window.removeEventListener('eventUnarchived', handleEventUnarchived)
    }
    
    // Add onUnmounted hook to clean up event listeners
    onUnmounted(() => {
      cleanup()
    })

    return {
      events,
      filteredEvents,
      loading,
      error,
      selectedEvent,
      showPopup,
      showEditModal,
      showApprovalModal,
      showRejectModal,
      showArchiveModal,
      modalType,
      isCurrentUserReviewer,
      expandedGroups,
      route,
      // Permission checks
      canViewAllEvents,
      canViewModuleEvents,
      canCreateEvents,
      canEditEvents,
      canApproveEvents,
      canRejectEvents,
      canArchiveEvents,
      canViewEventAnalytics,
      hasEventAccess,
      canViewModule,
      getFilteredModules,
      handleExport,
      handleFilterChange,
      handleEventClick,
      closePopup,
      handleEdit,
      handleAttachEvidence,
      handleApprove,
      handleReject,
      handleArchive,
      handleModalSubmit,
      handleModalCancel,
      handleEditModalClose,
      handleEditSaved,
      getStatusColor,
      toggleStatusGroup,
      getEventsByStatus,
      fetchEvents
    }
  }
}
</script>

<style>
/* Events List Container - Framework Explorer inspired styling */
.events-list-container {
  padding: 20px;
  background-color: transparent;
  min-height: 100vh;
  width: 100%;
  box-sizing: border-box;
  margin-left: -30px; /* Align with sidebar */
}

/* Header Section */
.events-view-header {
  background-color: transparent;
  border-bottom: none;
  padding: 20px 0;
  margin-bottom: 0;
}

.events-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 100%;
  margin: 0 auto;
  padding: 0 20px;
}

.events-title-section {
  flex: 1;
}

.events-view-title {
  font-size: 1.8rem;
  font-weight: 700;
  color: #344054;
  letter-spacing: 0.5px;
  margin: 0 0 8px 0;
}

.events-view-subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
  font-weight: 400;
}

.events-header-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}

/* Refresh Button */
.events-refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: transparent;
  color: #374151;
  border: none;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  margin-right: 12px;
}

.events-refresh-btn:hover:not(:disabled) {
  color: #1f2937;
}

.events-refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.events-btn-icon-spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Create Event Button */
.events-create-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: transparent;
  color: #374151;
  text-decoration: underline;
  border: none;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
}

.events-create-btn:hover {
  color: #1f2937;
  text-decoration: underline;
}

.events-btn-icon {
  width: 18px;
  height: 18px;
  stroke-width: 2.5;
}

/* Filters Section */
.events-filters-section {
  background-color: transparent;
  border-bottom: none;
  padding: 20px 0;
}

/* Content Wrapper */
.events-content-wrapper {
  background-color: transparent;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
  border: none;
  margin-top: 20px;
  min-height: 400px;
}

/* Loading State */
.events-loading-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.events-spinner-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.events-spinner-circle {
  width: 60px;
  height: 60px;
  border: 4px solid #f3f4f6;
  border-top: 4px solid #374151;
  border-radius: 50%;
  animation: events-spin 1s linear infinite;
}

.events-loading-text {
  color: #6b7280;
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0;
}

@keyframes events-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Error State */
.events-error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.events-error-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  text-align: center;
}

.events-error-icon {
  color: #ef4444;
}

.events-error-svg {
  width: 60px;
  height: 60px;
}

.events-error-message {
  color: #ef4444;
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0;
}

.events-retry-btn {
  padding: 12px 24px;
  background: transparent;
  color: #374151;
  border: none;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  text-decoration: underline;
}

.events-retry-btn:hover {
  color: #1f2937;
}

/* Empty State */
.events-empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.events-empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  text-align: center;
}

.events-empty-icon {
  color: #9ca3af;
}

.events-empty-svg {
  width: 60px;
  height: 60px;
}

.events-empty-message {
  color: #6b7280;
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0;
}

.events-create-first-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: transparent;
  color: #374151;
  text-decoration: underline;
  border: none;
  font-weight: 600;
  font-size: 0.95rem;
}

.events-create-first-btn:hover {
  color: #1f2937;
  text-decoration: underline;
}

/* Status Groups */
.events-status-groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.events-status-group {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e9ecef;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.events-status-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 1px solid #dee2e6;
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 0;
}

.events-status-header:hover {
  background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
}

.events-status-header-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
}

.events-status-chevron {
  width: 20px;
  height: 20px;
  color: #6b7280;
  transition: transform 0.3s ease;
  flex-shrink: 0;
}

.events-status-chevron-open {
  transform: rotate(90deg);
}

.events-status-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #374151;
  flex: 1;
}

.events-status-count {
  background: #f3f4f6;
  color: #374151;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  min-width: 24px;
  text-align: center;
  border: 1px solid #d1d5db;
}

.events-status-content {
  padding: 0;
  background: #ffffff;
}

.events-status-empty {
  padding: 40px 20px;
  text-align: center;
  color: #6b7280;
  font-style: italic;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

/* Table Container */
.events-table-container {
  width: 100%;
  overflow-x: visible;
  border-radius: 0;
  border: none;
  box-shadow: none;
}

.events-table-wrapper {
  width: 100%;
  overflow-x: visible;
}

/* Table Styling */
.events-table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  margin: 0;
  font-size: 0.9rem;
  table-layout: fixed;
}

.events-table-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 2px solid #dee2e6;
}

.events-table-th {
  padding: 16px 12px;
  text-align: left;
  font-weight: 600;
  color: #495057;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: normal;
  word-break: break-word;
  position: sticky;
  top: 0;
  z-index: 10;
  border-bottom: 2px solid #dee2e6;
}

.events-table-body {
  background-color: white;
}

.events-table-row {
  transition: all 0.2s ease;
  border-bottom: 1px solid #f1f3f4;
}

.events-row-even {
  background-color: white;
}

.events-row-odd {
  background-color: #fafbfc;
}

.events-table-td {
  padding: 16px 12px;
  color: #495057;
  vertical-align: middle;
  font-size: 0.8rem;
  border-bottom: 1px solid #f1f3f4;
  text-align: left;
  word-break: break-word;
}

.events-status-title,
.events-status-count {
  font-size: 0.9rem;
}

.events-table-row:last-child .events-table-td {
  border-bottom: none;
}

/* Column Widths */
.events-title-col {
  min-width: 0;
  max-width: none;
  text-align: left;
}

.events-id-col,
.events-framework-col,
.events-module-col,
.events-category-col,
.events-owner-col,
.events-reviewer-col,
.events-created-col,
.events-status-col {
  min-width: 0;
}

/* Cell Content */
.events-title-cell {
  font-weight: 500;
  text-align: left;
}

.events-title-link,
.events-id-link {
  background: none;
  border: none;
  color: #374151;
  font-weight: 500;
  cursor: pointer;
  text-decoration: underline;
  padding: 0;
  font-size: inherit;
  text-align: left;
  display: block;
  width: 100%;
  word-break: break-word;
}

.events-framework-cell {
  color: #6b7280;
}

/* Status Badges */
.events-status-badge {
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

/* Status Colors */
.events-status-approved {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  color: #155724;
  border-color: #c3e6cb;
}

.events-status-pending {
  background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
  color: #856404;
  border-color: #ffeaa7;
}

.events-status-rejected {
  background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
  color: #721c24;
  border-color: #f5c6cb;
}

.events-status-draft {
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e0 100%);
  color: #4a5568;
  border-color: #cbd5e0;
}

.events-status-under-review {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #1e40af;
  border-color: #bfdbfe;
}

.events-status-completed {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  color: #155724;
  border-color: #c3e6cb;
}

.events-status-cancelled {
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e0 100%);
  color: #4a5568;
  border-color: #cbd5e0;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .events-table {
    min-width: 1200px;
  }
  
  .events-table-container {
    overflow-x: auto;
  }
}

@media (max-width: 768px) {
  .events-list-container {
    padding: 15px;
    margin-left: 0; /* Remove sidebar margin on mobile */
  }
  
  .events-header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
    padding: 0 15px;
  }
  
  .events-header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .events-content-wrapper {
    padding: 15px;
    margin-top: 15px;
  }
  
  .events-view-title {
    font-size: 1.5rem;
  }
  
  .events-view-subtitle {
    font-size: 0.9rem;
  }
  
  /* Make table responsive on mobile */
  .events-table,
  .events-table thead,
  .events-table tbody,
  .events-table th,
  .events-table td,
  .events-table tr {
    display: block;
  }
  
  .events-table thead tr {
    position: absolute;
    top: -9999px;
    left: -9999px;
  }
  
  .events-table tr {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    margin-bottom: 10px;
    padding: 10px;
    background-color: white;
  }
  
  .events-table td {
    border: none;
    position: relative;
    padding: 8px 10px 8px 40%;
    border-bottom: 1px solid #f3f4f6;
  }
  
  .events-table td:before {
    content: attr(data-label) ": ";
    position: absolute;
    left: 6px;
    width: 35%;
    padding-right: 10px;
    white-space: nowrap;
    font-weight: 600;
    color: #4b5563;
  }
  
  .events-table td:last-child {
    border-bottom: none;
  }
}

/* Animation for smooth transitions */
@keyframes events-slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.events-table-row {
  animation: events-slideIn 0.3s ease-out;
}

/* Focus states for accessibility */
.events-refresh-btn:focus,
.events-create-btn:focus,
.events-retry-btn:focus,
.events-create-first-btn:focus,
.events-title-link:focus,
.events-id-link:focus {
  outline: 2px solid #374151;
  outline-offset: 2px;
}
</style>
