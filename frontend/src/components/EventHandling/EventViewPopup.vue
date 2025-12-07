<template>
  <div v-if="isOpen" class="event-popup-overlay" style="z-index: 9999999 !important;">
    <div class="event-popup-container" style="z-index: 10000000 !important;">
      <!-- Header -->
      <div class="event-popup-header">
        <div class="event-popup-title-section">
          <h2 class="event-popup-title">{{ event.title || event.EventTitle || 'Untitled Event' }}</h2>
          <p class="event-popup-subtitle">Event ID: {{ event.id || event.EventId || event.event_id || 'N/A' }}</p>
        </div>
        <button
          @click="$emit('close')"
          class="event-popup-close-btn"
        >
          <svg class="event-popup-close-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Actions -->
      <div class="event-popup-actions">
        <div class="event-popup-actions-left">
          <button
            v-if="showActionButtons && canEditEvents && (event.status || event.Status) !== 'Approved' && (event.status || event.Status) !== 'Rejected'"
            @click="$emit('edit')"
            class="event-popup-btn event-popup-btn-edit"
          >
            <svg class="event-popup-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
            Edit
          </button>
          <button
            v-if="showActionButtons && (event.status || event.Status) !== 'Approved' && (event.status || event.Status) !== 'Rejected'"
            @click="$emit('attach-evidence')"
            class="event-popup-btn event-popup-btn-attach"
          >
            <svg class="event-popup-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path>
            </svg>
            Attach Evidence
          </button>
          <button
            v-if="showActionButtons && showApprovalActions && canApproveEvents && (event.status || event.Status) === 'Pending Approval'"
            @click="$emit('approve')"
            class="event-popup-btn event-popup-btn-approve"
          >
            <svg class="event-popup-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            Approve
          </button>
          <button
            v-if="showActionButtons && showApprovalActions && canRejectEvents && (event.status || event.Status) === 'Pending Approval'"
            @click="$emit('reject')"
            class="event-popup-btn event-popup-btn-reject"
          >
            <svg class="event-popup-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
            Reject
          </button>
        </div>
        <div class="event-popup-actions-right">
          <button
            v-if="showActionButtons && canArchiveEvents"
            @click="$emit('archive')"
            class="event-popup-btn event-popup-btn-archive"
          >
            <svg class="event-popup-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-14 0a2 2 0 012-2h10a2 2 0 012 2"></path>
            </svg>
            Archive
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="event-popup-content">
        <!-- Basic Details -->
        <div class="event-popup-details-grid">
          <div class="event-popup-details-section">
            <h4 class="event-popup-section-title">Event Details</h4>
            <div class="event-popup-details-list">
              <div class="event-popup-detail-item">
                <span class="event-popup-detail-label">Framework</span>
                <p class="event-popup-detail-value">{{ event.framework || event.FrameworkName || 'N/A' }}</p>
              </div>
              <div class="event-popup-detail-item">
                <span class="event-popup-detail-label">Linked Module</span>
                <p class="event-popup-detail-value">{{ event.module || event.Module || 'N/A' }}</p>
              </div>
              <div class="event-popup-detail-item">
                <span class="event-popup-detail-label">Linked Record</span>
                <p class="event-popup-detail-value event-popup-detail-link">{{ event.linked_record_name || event.linkedRecord || event.LinkedRecordName || 'N/A' }}</p>
              </div>
              <div class="event-popup-detail-item">
                <span class="event-popup-detail-label">Category</span>
                <p class="event-popup-detail-value">{{ event.category || event.Category || 'N/A' }}</p>
              </div>
              <div class="event-popup-detail-item">
                <span class="event-popup-detail-label">Source</span>
                <p class="event-popup-detail-value">{{ event.source || event.sourceSystem || 'Manual' }}</p>
              </div>
              <div v-if="event.sourceSystem" class="event-popup-detail-item">
                <span class="event-popup-detail-label">Source System</span>
                <p class="event-popup-detail-value">{{ event.sourceSystem }}</p>
              </div>
              <div v-if="event.suggestedType" class="event-popup-detail-item">
                <span class="event-popup-detail-label">Suggested Type</span>
                <p class="event-popup-detail-value">{{ event.suggestedType }}</p>
              </div>
            </div>
          </div>

          <div class="event-popup-details-section">
            <h4 class="event-popup-section-title">Assignment & Status</h4>
            <div class="event-popup-details-list">
              <div class="event-popup-detail-item">
                <span class="event-popup-detail-label">Owner</span>
                <div class="event-popup-detail-value-with-icon">
                  <svg class="event-popup-detail-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                  </svg>
                  <p class="event-popup-detail-value">{{ event.owner || event.OwnerName || 'N/A' }}</p>
                </div>
              </div>
              <div class="event-popup-detail-item">
                <span class="event-popup-detail-label">Reviewer</span>
                <div class="event-popup-detail-value-with-icon">
                  <svg class="event-popup-detail-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                  </svg>
                  <p class="event-popup-detail-value">{{ event.reviewer || event.ReviewerName || 'N/A' }}</p>
                </div>
              </div>
              <div class="event-popup-detail-item">
                <span class="event-popup-detail-label">Recurrence</span>
                <p class="event-popup-detail-value">
                  {{ event.recurrence_type || event.recurrence || event.RecurrenceType || 'N/A' }}
                  <span v-if="event.frequency || event.Frequency"> ({{ event.frequency || event.Frequency }})</span>
                </p>
              </div>
              <div class="event-popup-detail-item">
                <span class="event-popup-detail-label">Date Created</span>
                <p class="event-popup-detail-value">{{ event.dateCreated || event.CreatedAt || 'N/A' }}</p>
              </div>
              <div v-if="event.timestamp" class="event-popup-detail-item">
                <span class="event-popup-detail-label">Last Updated</span>
                <p class="event-popup-detail-value">{{ event.timestamp }}</p>
              </div>
              <div class="event-popup-detail-item">
                <span class="event-popup-detail-label">Status</span>
                <span :class="`event-popup-status-badge ${getStatusColor(event.status || event.Status)}`">
                  {{ event.status || event.Status || 'N/A' }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Description -->
        <div class="event-popup-description-section">
          <h4 class="event-popup-section-title">Description</h4>
          <div class="event-popup-description-content">
            {{ event.description || event.Description || 'No description available' }}
          </div>
        </div>

        <!-- Evidence -->
        <div class="event-popup-evidence-section">
          <h4 class="event-popup-section-title">Evidence</h4>
          <div v-if="event.evidence && event.evidence.length > 0" class="event-popup-evidence-list">
            <div v-for="evidence in event.evidence" :key="evidence.id" class="event-popup-evidence-item">
              <div class="event-popup-evidence-info">
                <div class="event-popup-evidence-icon">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                  </svg>
                </div>
                <div class="event-popup-evidence-details">
                  <h5>{{ evidence.fileName }}</h5>
                  <p>Uploaded by {{ evidence.uploadedBy }} on {{ evidence.uploadDate }} • {{ evidence.size }}</p>
                </div>
              </div>
              <button 
                @click="downloadEvidence(evidence)"
                class="event-popup-evidence-download"
                :disabled="!getEvidenceDownloadUrl(evidence) || getEvidenceDownloadUrl(evidence) === '#'"
              >
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                Download
              </button>
            </div>
          </div>
          <div v-else class="event-popup-evidence-empty">
            <div class="event-popup-evidence-empty-icon">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
            </div>
            <p class="event-popup-evidence-empty-text">No evidence uploaded</p>
          </div>
        </div>

        <!-- Approval History -->
        <div>
          <h4 class="text-sm font-medium text-gray-900 mb-3">Approval History</h4>
          <div v-if="event.approvalHistory && event.approvalHistory.length > 0" class="space-y-3">
            <div v-for="(item, index) in event.approvalHistory" :key="index" class="flex items-start space-x-3 p-3 bg-gray-50 rounded-md">
              <div class="flex-shrink-0">
                <svg class="h-4 w-4 text-gray-400 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
              <div class="flex-1">
                <p class="text-sm font-medium text-gray-900">
                  {{ item.status }} by {{ item.user }}
                </p>
                <p class="text-xs text-gray-500">{{ item.date }}</p>
                <p v-if="item.comment" class="text-sm text-gray-700 mt-1 italic">"{{ item.comment }}"</p>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 bg-gray-50 rounded-md border border-gray-200">
            <p class="text-sm text-gray-500">No approval history available</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import { useEventPermissions } from '../../composables/useEventPermissions'
import PopupModal from '../../modules/popus/PopupModal.vue'

export default {
  name: 'EventViewPopup',
  components: {
    PopupModal
  },
  props: {
    event: {
      type: Object,
      required: true
    },
    isOpen: {
      type: Boolean,
      default: false
    },
    showApprovalActions: {
      type: Boolean,
      default: true
    },
    showActionButtons: {
      type: Boolean,
      default: true
    }
  },
  emits: ['close', 'edit', 'attach-evidence', 'approve', 'reject', 'archive'],
  setup() {
    // Event permissions
    const {
      canEditEvents,
      canApproveEvents,
      canRejectEvents,
      canArchiveEvents
    } = useEventPermissions()
    const getStatusColor = (status) => {
      switch (status) {
        case 'Approved': return 'event-popup-status-approved'
        case 'Pending Review': return 'event-popup-status-pending'
        case 'Pending Approval': return 'event-popup-status-pending'
        case 'Rejected': return 'event-popup-status-rejected'
        case 'Draft': return 'event-popup-status-draft'
        default: return 'event-popup-status-draft'
      }
    }

    const getEvidenceDownloadUrl = (evidence) => {
      console.log('DEBUG: EventViewPopup - Getting download URL for evidence:', evidence)
      
      // If it's a direct URL, return it
      if (evidence.url && evidence.url.startsWith('http')) {
        console.log('DEBUG: EventViewPopup - Using direct URL:', evidence.url)
        return evidence.url
      }
      
      // If it's an S3 URL, construct the download URL
      if (evidence.s3_url || evidence.url) {
        const s3Url = evidence.s3_url || evidence.url
        const filename = evidence.fileName || evidence.filename || evidence.name || 'evidence'
        
        console.log('DEBUG: EventViewPopup - S3 URL:', s3Url)
        console.log('DEBUG: EventViewPopup - Filename:', filename)
        
        // Extract S3 key from URL
        let s3Key = ''
        if (s3Url.includes('amazonaws.com')) {
          const urlParts = s3Url.split('amazonaws.com/')
          if (urlParts.length > 1) {
            s3Key = urlParts[1]
          }
        }
        
        console.log('DEBUG: EventViewPopup - Extracted S3 key:', s3Key)
        
        if (s3Key) {
          const userId = localStorage.getItem('user_id') || '1'
          const downloadUrl = `/api/events/s3/download/${encodeURIComponent(s3Key)}/${encodeURIComponent(filename)}/?user_id=${userId}`
          console.log('DEBUG: EventViewPopup - Generated download URL:', downloadUrl)
          return downloadUrl
        }
      }
      
      // Fallback to original URL
      console.log('DEBUG: EventViewPopup - Using fallback URL:', evidence.url || '#')
      return evidence.url || '#'
    }

    const downloadEvidence = (evidence) => {
      console.log('Attempting to download evidence:', evidence)
      
      const downloadUrl = getEvidenceDownloadUrl(evidence)
      
      if (!downloadUrl || downloadUrl === '#') {
        console.error('No valid URL available for evidence:', evidence)
        return
      }

      console.log('Final download URL:', downloadUrl)

      try {
        // For API endpoints, use fetch to check if the URL is valid first
        if (downloadUrl.startsWith('/api/')) {
          // Use window.location to navigate to the download URL
          window.location.href = downloadUrl
        } else {
          // For direct URLs, create a temporary anchor element
          const link = document.createElement('a')
          link.href = downloadUrl
          link.download = evidence.fileName || evidence.filename || evidence.name || 'evidence-file'
          link.target = '_blank'
          
          // Add to DOM, click, and remove
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
        }
        
        console.log('Download initiated for:', evidence.fileName || evidence.filename)
      } catch (error) {
        console.error('Error downloading evidence:', error)
        // Fallback: open in new tab
        window.open(downloadUrl, '_blank')
      }
    }

    return {
      getStatusColor,
      getEvidenceDownloadUrl,
      downloadEvidence,
      // Permission checks
      canEditEvents,
      canApproveEvents,
      canRejectEvents,
      canArchiveEvents
    }
  }
}
</script>

<style>
/* Event Popup Overlay - Highest Priority */
.event-popup-overlay {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  background: rgba(0, 0, 0, 0.5) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: 9999999 !important;
  backdrop-filter: blur(4px) !important;
  animation: event-popup-fadeIn 0.3s ease-out !important;
  isolation: isolate !important;
  contain: layout style paint !important;
  will-change: transform !important;
}

/* Event Popup Container - Highest Priority */
.event-popup-container {
  background: #ffffff !important;
  border-radius: 16px !important;
  box-shadow: 0 20px 25px rgba(0, 0, 0, 0.15), 0 10px 10px rgba(0, 0, 0, 0.04) !important;
  max-width: 900px !important;
  width: 90% !important;
  max-height: 90vh !important;
  overflow-y: auto !important;
  margin: 20px !important;
  animation: event-popup-slideIn 0.4s ease-out !important;
  position: relative !important;
  z-index: 10000000 !important;
  isolation: isolate !important;
  contain: layout style paint !important;
  will-change: transform !important;
}

/* Event Popup Header */
.event-popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-radius: 16px 16px 0 0;
}

.event-popup-title-section {
  flex: 1;
}

.event-popup-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
  line-height: 1.3;
}

.event-popup-subtitle {
  font-size: 0.95rem;
  color: #6b7280;
  margin: 0;
  font-weight: 500;
}

.event-popup-close-btn {
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

.event-popup-close-btn:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.event-popup-close-icon {
  width: 24px;
  height: 24px;
}

/* Event Popup Actions */
.event-popup-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 32px;
  border-bottom: 1px solid #e5e7eb;
  background: #ffffff;
}

.event-popup-actions-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.event-popup-actions-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Event Popup Buttons */
.event-popup-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.event-popup-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.event-popup-btn-icon {
  width: 16px;
  height: 16px;
  stroke-width: 2.5;
}

/* Button Variants */
.event-popup-btn-edit {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.event-popup-btn-edit:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
}

.event-popup-btn-attach {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.event-popup-btn-attach:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

.event-popup-btn-approve {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.event-popup-btn-approve:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

.event-popup-btn-reject {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.event-popup-btn-reject:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
}

.event-popup-btn-archive {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
}

.event-popup-btn-archive:hover {
  background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
}

/* Event Popup Content */
.event-popup-content {
  padding: 32px;
  background: #ffffff;
}

/* Event Popup Details Grid */
.event-popup-details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
  margin-bottom: 32px;
}

.event-popup-details-section {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
}

.event-popup-section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 20px 0;
  padding-bottom: 12px;
  border-bottom: 2px solid #e5e7eb;
}

/* Event Popup Details List */
.event-popup-details-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.event-popup-detail-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.event-popup-detail-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.event-popup-detail-value {
  font-size: 0.95rem;
  font-weight: 500;
  color: #1f2937;
  margin: 0;
}

.event-popup-detail-value-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.event-popup-detail-icon {
  width: 16px;
  height: 16px;
  color: #9ca3af;
  flex-shrink: 0;
}

.event-popup-detail-link {
  color: #3b82f6;
  cursor: pointer;
  text-decoration: none;
}

.event-popup-detail-link:hover {
  color: #2563eb;
  text-decoration: underline;
}

/* Event Popup Status Badge */
.event-popup-status-badge {
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

.event-popup-status-approved {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  color: #155724;
  border-color: #c3e6cb;
}

.event-popup-status-pending {
  background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
  color: #856404;
  border-color: #ffeaa7;
}

.event-popup-status-rejected {
  background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
  color: #721c24;
  border-color: #f5c6cb;
}

.event-popup-status-draft {
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e0 100%);
  color: #4a5568;
  border-color: #cbd5e0;
}

/* Event Popup Description Section */
.event-popup-description-section {
  margin-bottom: 32px;
}

.event-popup-description-content {
  background: #f8f9fa;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  font-size: 0.95rem;
  color: #374151;
  line-height: 1.6;
  max-height: 200px;
  overflow-y: auto;
}

/* Evidence Section */
.event-popup-evidence-section {
  margin-bottom: 32px;
}

.event-popup-evidence-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.event-popup-evidence-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.event-popup-evidence-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
  transform: translateY(-1px);
}

.event-popup-evidence-info {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.event-popup-evidence-icon {
  width: 24px;
  height: 24px;
  color: #3b82f6;
  flex-shrink: 0;
}

.event-popup-evidence-details h5 {
  font-size: 1rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 6px 0;
  line-height: 1.4;
}

.event-popup-evidence-details p {
  font-size: 0.875rem;
  color: #64748b;
  margin: 0;
  line-height: 1.4;
}

.event-popup-evidence-download {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.event-popup-evidence-download:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
  transform: translateY(-1px);
}

.event-popup-evidence-download:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.event-popup-evidence-download:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

.event-popup-evidence-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  text-align: center;
}

.event-popup-evidence-empty-icon {
  width: 48px;
  height: 48px;
  color: #94a3b8;
  margin-bottom: 16px;
}

.event-popup-evidence-empty-text {
  font-size: 1rem;
  color: #64748b;
  margin: 0;
  font-weight: 500;
}

/* Approval History Section */
.event-popup-approval-section {
  margin-bottom: 32px;
}

.event-popup-approval-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.event-popup-approval-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #f8f9fa;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.event-popup-approval-icon {
  width: 20px;
  height: 20px;
  color: #9ca3af;
  margin-top: 2px;
  flex-shrink: 0;
}

.event-popup-approval-details h5 {
  font-size: 0.9rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 4px 0;
}

.event-popup-approval-details p {
  font-size: 0.8rem;
  color: #6b7280;
  margin: 0 0 8px 0;
}

.event-popup-approval-comment {
  font-size: 0.85rem;
  color: #374151;
  font-style: italic;
  margin: 0;
}

/* Empty States */
.event-popup-empty-state {
  text-align: center;
  padding: 40px 20px;
  background: #f8f9fa;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.event-popup-empty-state p {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0;
}

/* Animations */
@keyframes event-popup-fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes event-popup-slideIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .event-popup-container {
    width: 95%;
    margin: 10px;
    max-height: 95vh;
  }
  
  .event-popup-header {
    padding: 20px;
  }
  
  .event-popup-title {
    font-size: 1.3rem;
  }
  
  .event-popup-actions {
    padding: 16px 20px;
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .event-popup-actions-left,
  .event-popup-actions-right {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .event-popup-content {
    padding: 20px;
  }
  
  .event-popup-details-grid {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .event-popup-details-section {
    padding: 20px;
  }
  
  .event-popup-btn {
    padding: 8px 12px;
    font-size: 0.85rem;
  }
}

/* Focus states for accessibility */
.event-popup-btn:focus,
.event-popup-close-btn:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Scrollbar styling */
.event-popup-container::-webkit-scrollbar {
  width: 8px;
}

.event-popup-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.event-popup-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.event-popup-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
