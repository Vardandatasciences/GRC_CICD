<template>
  <div v-if="isOpen" class="event-edit-modal-overlay">
    <div class="event-edit-modal-container">
      <!-- Header -->
      <div class="event-edit-modal-header">
        <div class="event-edit-modal-title-section">
          <div class="event-edit-modal-icon-section">
            <svg class="event-edit-modal-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
          </div>
          <div class="event-edit-modal-title-content">
            <h2 class="event-edit-modal-title">Edit Event</h2>
            <p class="event-edit-modal-subtitle">Event ID: {{ event?.id || event?.event_id || 'N/A' }}</p>
          </div>
        </div>
        <button
          @click="$emit('close')"
          class="event-edit-modal-close-btn"
        >
          <svg class="event-edit-modal-close-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Content -->
      <div class="event-edit-modal-content">
        <form @submit.prevent="handleSubmit" class="event-edit-form">
          <!-- Basic Information -->
          <div class="event-edit-section">
            <h3 class="event-edit-section-title">Basic Information</h3>
            <div class="event-edit-form-grid">
              <div class="event-edit-form-group">
                <label class="event-edit-label">Event Title *</label>
                <input
                  v-model="formData.title"
                  type="text"
                  class="event-edit-input"
                  required
                  placeholder="Enter event title"
                />
              </div>
              
              <div class="event-edit-form-group">
                <label class="event-edit-label">Framework</label>
                <select v-model="formData.framework" class="event-edit-select" :disabled="frameworks.length === 0">
                  <option value="">{{ frameworks.length === 0 ? 'Loading frameworks...' : 'Select Framework' }}</option>
                  <option v-for="framework in frameworks" :key="framework.id" :value="framework.FrameworkName || framework.name">
                    {{ framework.FrameworkName || framework.name }}
                  </option>
                </select>
              </div>

              <div class="event-edit-form-group">
                <label class="event-edit-label">Module</label>
                <select v-model="formData.module" class="event-edit-select">
                  <option value="">Select Module</option>
                  <option v-for="module in modules" :key="module" :value="module">
                    {{ module }}
                  </option>
                </select>
              </div>

              <div class="event-edit-form-group">
                <label class="event-edit-label">Category</label>
                <input
                  v-model="formData.category"
                  type="text"
                  class="event-edit-input"
                  placeholder="Enter category"
                />
              </div>
            </div>
          </div>

          <!-- Description -->
          <div class="event-edit-section">
            <h3 class="event-edit-section-title">Description</h3>
            <div class="event-edit-form-group">
              <label class="event-edit-label">Event Description</label>
              <textarea
                v-model="formData.description"
                class="event-edit-textarea"
                rows="4"
                placeholder="Enter event description"
              ></textarea>
            </div>
          </div>

          <!-- Assignment -->
          <div class="event-edit-section">
            <h3 class="event-edit-section-title">Assignment</h3>
            <div class="event-edit-form-grid">
              <div class="event-edit-form-group">
                <label class="event-edit-label">Owner</label>
                <input
                  v-model="formData.owner"
                  type="text"
                  class="event-edit-input event-edit-input-readonly"
                  readonly
                  placeholder="Current user"
                />
              </div>

              <div class="event-edit-form-group">
                <label class="event-edit-label">Reviewer</label>
                <select v-model="formData.reviewer" class="event-edit-select">
                  <option value="">Select Reviewer</option>
                  <option v-for="user in users" :key="user.id" :value="user.name">
                    {{ user.name }}
                  </option>
                </select>
              </div>
            </div>
          </div>

          <!-- Recurrence -->
          <div class="event-edit-section">
            <h3 class="event-edit-section-title">Recurrence</h3>
            <div class="event-edit-form-grid">
              <div class="event-edit-form-group">
                <label class="event-edit-label">Recurrence Type</label>
                <select v-model="formData.recurrence_type" class="event-edit-select">
                  <option value="">Select Type</option>
                  <option value="None">None</option>
                  <option value="Daily">Daily</option>
                  <option value="Weekly">Weekly</option>
                  <option value="Monthly">Monthly</option>
                  <option value="Yearly">Yearly</option>
                </select>
              </div>

              <div class="event-edit-form-group">
                <label class="event-edit-label">Frequency</label>
                <input
                  v-model="formData.frequency"
                  type="number"
                  class="event-edit-input"
                  placeholder="Frequency (e.g., 1, 2, 3)"
                  min="1"
                />
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="event-edit-modal-actions">
            <button
              type="button"
              @click="$emit('close')"
              class="event-edit-modal-btn event-edit-modal-btn-cancel"
            >
              <svg class="event-edit-modal-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
              Cancel
            </button>
            <button
              type="submit"
              :disabled="loading"
              class="event-edit-modal-btn event-edit-modal-btn-save"
            >
              <svg v-if="loading" class="event-edit-modal-btn-icon event-edit-modal-spinner" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
              <svg v-else class="event-edit-modal-btn-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
              </svg>
              {{ loading ? 'Saving...' : 'Save Changes' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { eventService } from '../../services/api'
import { MODULES } from '../../utils/constants'
import PopupModal from '../../modules/popus/PopupModal.vue'
import axios from 'axios'

export default {
  name: 'EventEditModal',
  components: {
    PopupModal
  },
  props: {
    isOpen: {
      type: Boolean,
      default: false
    },
    event: {
      type: Object,
      required: true
    }
  },
  emits: ['close', 'saved'],
  setup(props, { emit }) {
    const loading = ref(false)
    const frameworks = ref([])
    const modules = ref(MODULES)
    const users = ref([])
    
    const formData = ref({
      title: '',
      framework: '',
      module: '',
      category: '',
      description: '',
      owner: '',
      reviewer: '',
      recurrence_type: '',
      frequency: ''
    })

    // Initialize form data when event changes
    watch(() => props.event, (newEvent) => {
      if (newEvent) {
        formData.value = {
          title: newEvent.title || newEvent.EventTitle || '',
          framework: newEvent.framework || newEvent.FrameworkName || '',
          module: newEvent.module || newEvent.Module || '',
          category: newEvent.category || newEvent.Category || '',
          description: newEvent.description || newEvent.Description || '',
          owner: newEvent.owner || newEvent.OwnerName || '', // Will be overridden by fetchCurrentUser
          reviewer: newEvent.reviewer || newEvent.ReviewerName || '',
          recurrence_type: newEvent.recurrence_type || newEvent.RecurrenceType || '',
          frequency: newEvent.frequency || newEvent.Frequency || ''
        }
        // Fetch current user to set owner after form data is initialized
        fetchCurrentUser()
      }
    }, { immediate: true })

    const fetchFrameworks = async () => {
      try {
        console.log('🚀 DEBUG: EventEditModal fetchFrameworks called - using /api/frameworks/ endpoint')
        const response = await axios.get('/api/frameworks/')
        console.log('🔍 DEBUG: Frameworks response in EventEditModal:', response.data)
        
        // Map the response to match the expected format
        frameworks.value = response.data.map(fw => ({
          FrameworkId: fw.FrameworkId,
          FrameworkName: fw.FrameworkName
        }))
        console.log('✅ DEBUG: Frameworks loaded in EventEditModal:', frameworks.value.length)
      } catch (error) {
        console.error('Error fetching frameworks:', error)
        // Fallback to static frameworks if API fails
        frameworks.value = [
          { id: 1, name: 'NIST', FrameworkName: 'NIST' },
          { id: 2, name: 'ISO 27001', FrameworkName: 'ISO 27001' },
          { id: 3, name: 'COBIT', FrameworkName: 'COBIT' },
          { id: 4, name: 'PCI DSS', FrameworkName: 'PCI DSS' },
          { id: 5, name: 'HIPAA', FrameworkName: 'HIPAA' },
          { id: 6, name: 'SOX', FrameworkName: 'SOX' },
          { id: 7, name: 'GDPR', FrameworkName: 'GDPR' }
        ]
      }
    }

    const fetchUsers = async () => {
      try {
        const userId = localStorage.getItem('user_id')
        if (!userId) {
          console.error('No user ID found in localStorage')
          return
        }
        
        const response = await eventService.getUsersForReviewer(userId)
        console.log('Users response:', response.data) // Debug log
        if (response.data.success) {
          users.value = response.data.users || []
          console.log('Users loaded:', users.value) // Debug log
        } else {
          console.error('Failed to fetch users:', response.data.message)
        }
      } catch (error) {
        console.error('Error fetching users:', error)
        // Fallback to empty array if API fails
        users.value = []
      }
    }

    const fetchCurrentUser = async () => {
      try {
        const userId = localStorage.getItem('user_id')
        if (!userId) {
          console.error('No user ID found in localStorage')
          return
        }
        
        const response = await eventService.getCurrentUser(userId)
        console.log('Current user response:', response.data) // Debug log
        if (response.data.success) {
          const currentUser = response.data.user
          formData.value.owner = currentUser.name
          console.log('Current user set as owner:', currentUser.name) // Debug log
        } else {
          console.error('Failed to fetch current user:', response.data.message)
        }
      } catch (error) {
        console.error('Error fetching current user:', error)
        // Fallback to default owner name
        formData.value.owner = 'Current User'
      }
    }

    const handleSubmit = async () => {
      try {
        loading.value = true
        
        const updateData = {
          title: formData.value.title,
          framework: formData.value.framework,
          module: formData.value.module,
          category: formData.value.category,
          description: formData.value.description,
          owner: formData.value.owner,
          reviewer: formData.value.reviewer,
          recurrence_type: formData.value.recurrence_type,
          frequency: formData.value.frequency
        }

        const eventId = props.event.id || props.event.event_id || props.event.EventId
        const response = await eventService.updateEvent(eventId, updateData)
        
        if (response.data.success) {
          // Emit the updated event data if available, otherwise emit the original event
          const updatedEvent = response.data.event || props.event
          emit('saved', updatedEvent)
          emit('close')
        } else {
          alert(response.data.message || 'Failed to update event')
        }
      } catch (error) {
        console.error('Error updating event:', error)
        alert('Failed to update event. Please try again.')
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      fetchFrameworks()
      fetchUsers()
      fetchCurrentUser()
    })

    // Also fetch data when modal opens
    watch(() => props.isOpen, (isOpen) => {
      if (isOpen) {
        if (frameworks.value.length === 0) {
          fetchFrameworks()
        }
        if (users.value.length === 0) {
          fetchUsers()
        }
        // Always fetch current user when modal opens to ensure owner is set
        fetchCurrentUser()
      }
    })

    return {
      loading,
      frameworks,
      modules,
      users,
      formData,
      handleSubmit
    }
  }
}
</script>

<style>
/* Event Edit Modal Overlay */
.event-edit-modal-overlay {
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
  animation: event-edit-modal-fadeIn 0.3s ease-out;
}

/* Event Edit Modal Container */
.event-edit-modal-container {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 20px 25px rgba(0, 0, 0, 0.15), 0 10px 10px rgba(0, 0, 0, 0.04);
  max-width: 800px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  margin: 20px;
  animation: event-edit-modal-slideIn 0.4s ease-out;
}

/* Event Edit Modal Header */
.event-edit-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-radius: 16px 16px 0 0;
}

.event-edit-modal-title-section {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.event-edit-modal-icon-section {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #1e40af;
  flex-shrink: 0;
}

.event-edit-modal-icon {
  width: 24px;
  height: 24px;
  stroke-width: 2.5;
}

.event-edit-modal-title-content {
  flex: 1;
}

.event-edit-modal-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 4px 0;
  line-height: 1.3;
}

.event-edit-modal-subtitle {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0;
  font-weight: 500;
}

.event-edit-modal-close-btn {
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

.event-edit-modal-close-btn:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.event-edit-modal-close-icon {
  width: 24px;
  height: 24px;
}

/* Event Edit Modal Content */
.event-edit-modal-content {
  padding: 32px;
  background: #ffffff;
}

/* Event Edit Form */
.event-edit-form {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.event-edit-section {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
}

.event-edit-section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 20px 0;
  padding-bottom: 12px;
  border-bottom: 2px solid #e5e7eb;
}

.event-edit-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.event-edit-form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.event-edit-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #374151;
}

.event-edit-input,
.event-edit-select,
.event-edit-textarea {
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.95rem;
  color: #374151;
  background: #ffffff;
  transition: all 0.3s ease;
  font-family: inherit;
}

.event-edit-input:focus,
.event-edit-select:focus,
.event-edit-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.event-edit-textarea {
  resize: vertical;
  min-height: 100px;
}

.event-edit-input::placeholder,
.event-edit-textarea::placeholder {
  color: #9ca3af;
  font-style: italic;
}

.event-edit-input-readonly {
  background-color: #f9fafb;
  color: #6b7280;
  cursor: not-allowed;
  border-color: #d1d5db;
}

.event-edit-input-readonly:focus {
  border-color: #d1d5db;
  box-shadow: none;
}

/* Event Edit Modal Actions */
.event-edit-modal-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.event-edit-modal-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  flex: 1;
  justify-content: center;
}

.event-edit-modal-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.event-edit-modal-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.event-edit-modal-btn-icon {
  width: 16px;
  height: 16px;
  stroke-width: 2.5;
}

.event-edit-modal-spinner {
  animation: event-edit-modal-spin 1s linear infinite;
}

/* Button Variants */
.event-edit-modal-btn-cancel {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  color: #374151;
  border: 1px solid #d1d5db;
}

.event-edit-modal-btn-cancel:hover {
  background: linear-gradient(135deg, #e5e7eb 0%, #d1d5db 100%);
}

.event-edit-modal-btn-save {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #ffffff;
}

.event-edit-modal-btn-save:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

/* Animations */
@keyframes event-edit-modal-fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes event-edit-modal-slideIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes event-edit-modal-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Responsive Design */
@media (max-width: 768px) {
  .event-edit-modal-container {
    width: 95%;
    margin: 10px;
    max-height: 95vh;
  }
  
  .event-edit-modal-header {
    padding: 20px;
  }
  
  .event-edit-modal-title {
    font-size: 1.3rem;
  }
  
  .event-edit-modal-content {
    padding: 20px;
  }
  
  .event-edit-form-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .event-edit-modal-actions {
    flex-direction: column;
    gap: 12px;
  }
  
  .event-edit-modal-btn {
    width: 100%;
  }
  
  .event-edit-modal-title-section {
    gap: 12px;
  }
  
  .event-edit-modal-icon-section {
    width: 40px;
    height: 40px;
  }
  
  .event-edit-modal-icon {
    width: 20px;
    height: 20px;
  }
}

/* Focus states for accessibility */
.event-edit-modal-btn:focus,
.event-edit-modal-close-btn:focus,
.event-edit-input:focus,
.event-edit-select:focus,
.event-edit-textarea:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Scrollbar styling */
.event-edit-modal-container::-webkit-scrollbar {
  width: 8px;
}

.event-edit-modal-container::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.event-edit-modal-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.event-edit-modal-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
