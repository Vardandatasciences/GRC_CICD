<template>
  <div v-if="isVisible" class="modal-overlay" @click.self="closeModal">
    <div class="modal-container">
      <div class="modal-header">
        <h2>Create Policy Acknowledgement Request</h2>
        <button class="close-btn" @click="closeModal">&times;</button>
      </div>

      <div class="modal-body">
        <!-- Policy Information -->
        <div class="policy-info-section">
          <h3>Policy Information</h3>
          <div class="form-group">
            <label class="policy-label">
              <span class="policy-label-text">Policy:</span>
            </label>
            <div class="policy-input-wrapper">
              <input
                type="text"
                :value="policy.name || policy.PolicyName"
                readonly
                class="form-input policy-input"
              />
              <span class="policy-version">Version: {{ policy.CurrentVersion || '1.0' }}</span>
            </div>
          </div>
        </div>

        <!-- Request Details -->
        <div class="request-details-section">
          <h3>Request Details</h3>
          
          <div class="form-group">
            <label for="title">Title: <span class="required">*</span></label>
            <div class="input-wrapper">
            <input
              id="title"
              v-model="formData.title"
              type="text"
              placeholder="e.g., Acknowledge Updated Security Policy"
              class="form-input"
              :class="{ 'error': errors.title }"
            />
            </div>
            <span v-if="errors.title" class="error-message">{{ errors.title }}</span>
          </div>

          <div class="form-group">
            <label for="description">Description (Optional):</label>
            <div class="input-wrapper">
            <textarea
              id="description"
              v-model="formData.description"
              placeholder="Provide details about what users should review..."
              class="form-textarea"
              rows="4"
            ></textarea>
            </div>
          </div>

          <div class="form-group">
            <label for="dueDate">Due Date (Optional):</label>
            <div class="input-wrapper">
            <input
              id="dueDate"
                v-model="formData.dueDateDisplay"
                type="text"
                placeholder="dd-mm-yyyy"
                class="form-input date-input"
                @focus="showDatePicker = true"
                @blur="handleDateBlur"
                @input="handleDateInput"
                @click="openDatePicker"
              />
              <input
              v-model="formData.dueDate"
              type="date"
                class="date-picker-hidden"
              :min="today"
                ref="datePickerRef"
                @change="handleDateChange"
            />
            </div>
          </div>
        </div>

        <!-- User Selection -->
        <div class="user-selection-section">
          <h3>Assign to Users <span class="required">*</span></h3>
          
          <div class="two-column-layout">
          <!-- Manual Email Input -->
            <div class="form-group email-column">
            <label for="manualEmail">Or Enter Email Addresses:</label>
              <div class="input-wrapper">
            <textarea
              id="manualEmail"
              v-model="formData.manualEmail"
              placeholder="Enter email addresses separated by commas (e.g., user1@example.com, user2@example.com)"
              class="form-textarea email-textarea"
              rows="3"
              @input="handleManualEmailChange"
            ></textarea>
              </div>
            <span v-if="errors.manualEmail" class="error-message">{{ errors.manualEmail }}</span>
          </div>
          
            <!-- User Selection Dropdown -->
            <div class="form-group user-column">
              <div class="input-wrapper">
                <input
                  v-model="userSearchDisplay"
                  type="text"
                  placeholder="Select users..."
                  class="form-input user-select-input"
                  @focus="handleUserListFocus"
                  @blur="handleUserListBlur"
                  @click="handleUserListFocus"
                  readonly
                />
              </div>
              
              <div v-if="showUserList" class="user-dropdown" @mousedown.prevent>
                <!-- Search bar inside dropdown -->
                <div class="user-dropdown-search">
                  <div class="search-icon">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2"/>
                      <path d="M21 21l-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <input
                    v-model="userSearch"
                    type="text"
                    placeholder="Search users..."
                    class="dropdown-search-input"
                    @input="filterUsers"
                    @mousedown.stop
                    @click.stop
                  />
                </div>

              <div v-if="!loadingUsers && filteredUsers.length > 0" class="user-list-header">
                <label class="checkbox-label">
                  <input
                    type="checkbox"
                    :checked="allUsersSelected"
                    @change="toggleAllUsers"
                      @mousedown.stop
                  />
                  <span>Select All ({{ filteredUsers.length }})</span>
                </label>
              </div>

              <div class="user-items">
                <div v-if="loadingUsers" class="loading-state">
                  <span class="spinner"></span> Loading users...
                </div>
                <div v-else-if="!filteredUsers || filteredUsers.length === 0" class="empty-state">
                  <p v-if="userSearch && userSearch.trim()">{{ `No users found matching "${userSearch}". Try adjusting your search.` }}</p>
                  <p v-else-if="!users || users.length === 0">No users available. Please check the console for errors.</p>
                  <p v-else>No users found. Try adjusting your search.</p>
                </div>
                <div v-else>
                  <div 
                    v-for="(user, index) in filteredUsers" 
                    :key="`user-${user.user_id || user.UserId || index}`" 
                    class="user-item-wrapper"
                  >
                    <label
                      class="user-item"
                      @mousedown.stop
                      @click.stop
                    >
                      <input
                        type="checkbox"
                        :value="user.user_id || user.UserId"
                        v-model="formData.targetUserIds"
                        @change="handleUserSelectionChange"
                        @mousedown.stop
                        @click.stop
                      />
                      <div class="user-info">
                        <span class="user-name">{{ 
                          (user.user_name || user.UserName || 'Unknown User') + 
                          (user.role ? ` (${user.role})` : '') + 
                          ` - ID: ${user.user_id || user.UserId || 'N/A'}`
                        }}</span>
                      </div>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <span v-if="errors.targetUserIds" class="error-message">{{ errors.targetUserIds }}</span>
            </div>
          </div>
        </div>

        <!-- Notification Options -->
        <div class="notification-section">
          <h3 class="notification-title">Notification Settings</h3>
          <div class="notification-options">
            <label class="notification-checkbox-label">
              <input type="checkbox" v-model="formData.sendNotifications" />
              <span>Send in-app notifications to selected users</span>
            </label>
            <label class="notification-checkbox-label">
              <input type="checkbox" v-model="formData.sendEmail" />
              <span>Send email notifications to selected users</span>
            </label>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="closeModal" :disabled="creating">
          Cancel
        </button>
        <button class="btn btn-primary" @click="createRequest" :disabled="creating">
          <span v-if="creating" class="spinner"></span>
          {{ creating ? 'Creating...' : 'Create Request' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { API_ENDPOINTS } from '../../config/api'
import { PopupService } from '@/modules/popus/popupService'

export default {
  name: 'CreateAcknowledgementModal',
  props: {
    isVisible: {
      type: Boolean,
      default: false
    },
    policy: {
      type: Object,
      required: true
    }
  },
  emits: ['close', 'created'],
  setup(props, { emit }) {
    const formData = ref({
      title: `Acknowledge ${props.policy.name || props.policy.PolicyName}`,
      description: '',
      dueDate: '',
      dueDateDisplay: '',
      targetUserIds: [],
      manualEmail: '',
      sendNotifications: true,
      sendEmail: true
    })

    const errors = ref({})
    const creating = ref(false)
    const loadingUsers = ref(false)
    const users = ref([])
    const userSearch = ref('')
    const userSearchDisplay = ref('')
    const filteredUsers = ref([])
    const showUserList = ref(false)
    const showDatePicker = ref(false)

    const today = computed(() => {
      const date = new Date()
      return date.toISOString().split('T')[0]
    })

    const allUsersSelected = computed(() => {
      return filteredUsers.value.length > 0 && 
             formData.value.targetUserIds.length === filteredUsers.value.length
    })

    const fetchUsers = async () => {
      try {
        loadingUsers.value = true
        const response = await axios.get(API_ENDPOINTS.GET_USERS_FOR_ACKNOWLEDGEMENT)
        
        console.log('📦 Full API response:', response.data)
        
        // Handle response structure: { success: true, users: [...], total_count: ... }
        let usersList = []
        if (response.data) {
          if (response.data.users && Array.isArray(response.data.users)) {
            usersList = response.data.users
            console.log('✅ Found users in response.data.users:', usersList.length)
          } else if (Array.isArray(response.data)) {
            usersList = response.data
            console.log('✅ Found users in response.data (array):', usersList.length)
          } else if (response.data.data && Array.isArray(response.data.data)) {
            usersList = response.data.data
            console.log('✅ Found users in response.data.data:', usersList.length)
          }
        }
        
        // Log first user to see structure
        if (usersList.length > 0) {
          console.log('👤 First user structure:', usersList[0])
        }
        
        // Ensure we have valid user objects
        usersList = usersList.filter(user => user && typeof user === 'object')
        
        console.log('📊 Filtered users count:', usersList.length)
        
        // Set users and filtered users - use reactive assignment
        const usersArray = usersList.map(user => ({ ...user }))
        users.value = usersArray
        
        // Initialize filteredUsers with all users - directly assign for immediate reactivity
        filteredUsers.value = usersArray
        
        // If there's a search term, apply filter
        if (userSearch.value && userSearch.value.trim()) {
          filterUsers()
        }
        
        console.log('✅ Successfully loaded', users.value.length, 'users')
        console.log('✅ filteredUsers length:', filteredUsers.value.length)
        console.log('✅ filteredUsers is array?', Array.isArray(filteredUsers.value))
        if (filteredUsers.value.length > 0) {
          console.log('✅ First user in filteredUsers:', filteredUsers.value[0])
          console.log('✅ First user name:', filteredUsers.value[0].full_name || filteredUsers.value[0].user_name || filteredUsers.value[0].UserName)
          console.log('✅ First user ID:', filteredUsers.value[0].user_id || filteredUsers.value[0].UserId)
        }
      } catch (error) {
        console.error('❌ Error fetching users:', error)
        console.error('Error response:', error.response?.data)
        PopupService.error(
          error.response?.data?.error || error.message || 'Failed to load users',
          'Error'
        )
        users.value = []
        filteredUsers.value = []
      } finally {
        loadingUsers.value = false
      }
    }

    const filterUsers = () => {
      const search = userSearch.value.toLowerCase().trim()
      if (!search) {
        filteredUsers.value = [...users.value]
        return
      }

      filteredUsers.value = users.value.filter(user => {
        // Search only by username
        const username = (user.user_name || user.UserName || '').toLowerCase()
        return username.includes(search)
      })
    }

    const toggleAllUsers = () => {
      if (allUsersSelected.value) {
        formData.value.targetUserIds = []
      } else {
        formData.value.targetUserIds = filteredUsers.value.map(u => u.user_id || u.UserId)
        // Clear manual email when users are selected
        if (formData.value.targetUserIds.length > 0) {
          formData.value.manualEmail = ''
        }
      }
    }

    const handleManualEmailChange = () => {
      // Clear errors when user types
      if (errors.value.manualEmail) {
        errors.value.manualEmail = null
      }
      // If manual email is entered, clear user selections and disable in-app notifications
      if (formData.value.manualEmail && formData.value.manualEmail.trim()) {
        formData.value.targetUserIds = []
        formData.value.sendNotifications = false
      }
    }

    const handleUserSelectionChange = () => {
      // Clear manual email when users are selected
      if (formData.value.targetUserIds.length > 0) {
        formData.value.manualEmail = ''
      }
      // Update display input to show selected count or names
      if (formData.value.targetUserIds.length > 0) {
        const selectedUsers = users.value.filter(u => {
          const userId = u.user_id || u.UserId
          return formData.value.targetUserIds.includes(userId)
        })
        if (selectedUsers.length === 1) {
          userSearchDisplay.value = selectedUsers[0].full_name || selectedUsers[0].user_name || selectedUsers[0].UserName
        } else {
          userSearchDisplay.value = `${selectedUsers.length} users selected`
        }
      } else {
        userSearchDisplay.value = ''
      }
    }

    const handleUserListFocus = () => {
      showUserList.value = true
      // Fetch users if not already loaded
      if (users.value.length === 0 && !loadingUsers.value) {
        fetchUsers()
      }
    }

    const handleUserListBlur = (event) => {
      // Don't close if clicking inside the dropdown
      const relatedTarget = event.relatedTarget
      if (relatedTarget && relatedTarget.closest('.user-dropdown')) {
        return
      }
      // Delay hiding to allow checkbox clicks
      setTimeout(() => {
        // Double check we're not clicking inside dropdown
        if (!document.activeElement || !document.activeElement.closest('.user-dropdown')) {
          showUserList.value = false
        }
      }, 300)
    }

    const datePickerRef = ref(null)

    const handleDateInput = (event) => {
      // Allow user to type dd-mm-yyyy format
      const value = event.target.value
      formData.value.dueDateDisplay = value
    }

    const handleDateChange = (event) => {
      const dateValue = event.target.value
      if (dateValue) {
        formData.value.dueDate = dateValue
        const date = new Date(dateValue)
        const day = String(date.getDate()).padStart(2, '0')
        const month = String(date.getMonth() + 1).padStart(2, '0')
        const year = date.getFullYear()
        formData.value.dueDateDisplay = `${day}-${month}-${year}`
      }
    }

    const openDatePicker = () => {
      if (datePickerRef.value) {
        datePickerRef.value.showPicker()
      }
    }

    const handleDateBlur = () => {
      // Try to parse dd-mm-yyyy format
      const displayValue = formData.value.dueDateDisplay
      if (displayValue) {
        const parts = displayValue.split('-')
        if (parts.length === 3) {
          const day = parts[0]
          const month = parts[1]
          const year = parts[2]
          if (day && month && year) {
            const dateStr = `${year}-${month}-${day}`
            const date = new Date(dateStr)
            if (!isNaN(date.getTime())) {
              formData.value.dueDate = dateStr
            }
          }
        }
      }
      showDatePicker.value = false
    }

    const validate = () => {
      errors.value = {}

      if (!formData.value.title.trim()) {
        errors.value.title = 'Title is required'
      }

      // Validate either users selected OR manual email provided
      const hasUsers = formData.value.targetUserIds.length > 0
      const hasManualEmail = formData.value.manualEmail && formData.value.manualEmail.trim()
      
      if (!hasUsers && !hasManualEmail) {
        errors.value.targetUserIds = 'Please select at least one user or enter an email address'
      }

      // Validate email format if manual email is provided
      if (hasManualEmail) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        // Split by comma and trim each email
        const emailList = formData.value.manualEmail
          .split(',')
          .map(email => email.trim())
          .filter(email => email.length > 0)
        
        if (emailList.length === 0) {
          errors.value.manualEmail = 'Please enter at least one email address'
        } else {
          // Validate each email
          const invalidEmails = emailList.filter(email => !emailRegex.test(email))
          if (invalidEmails.length > 0) {
            errors.value.manualEmail = `Invalid email address(es): ${invalidEmails.join(', ')}`
          }
        }
      }

      return Object.keys(errors.value).length === 0
    }

    const createRequest = async () => {
      if (!validate()) {
        return
      }

      try {
        creating.value = true

        // Parse multiple emails from comma-separated string
        let manualEmailValue = null
        if (formData.value.manualEmail && formData.value.manualEmail.trim()) {
          const emailList = formData.value.manualEmail
            .split(',')
            .map(email => email.trim())
            .filter(email => email.length > 0)
          
          // Send as string for single email (backward compatibility) or array for multiple
          if (emailList.length === 1) {
            manualEmailValue = emailList[0]
          } else if (emailList.length > 1) {
            manualEmailValue = emailList
          }
        }

        const requestData = {
          policy_id: props.policy.id || props.policy.PolicyId,
          policy_version: props.policy.CurrentVersion || '1.0',
          title: formData.value.title,
          description: formData.value.description,
          due_date: formData.value.dueDate || null,
          target_user_ids: formData.value.targetUserIds,
          manual_email: manualEmailValue,
          send_notifications: formData.value.sendNotifications && !formData.value.manualEmail,
          send_email: formData.value.sendEmail
        }

        const response = await axios.post(API_ENDPOINTS.CREATE_ACKNOWLEDGEMENT_REQUEST, requestData)

        // Don't show popup here - parent will handle it
        console.log('Acknowledgement request created:', response.data)
        
        emit('created', {
          ...response.data,
          acknowledgement_request_id: response.data.acknowledgement_request_id
        })
        closeModal()
      } catch (error) {
        console.error('Error creating acknowledgement request:', error)
        PopupService.error(
          error.response?.data?.error || 'Failed to create acknowledgement request',
          'Error'
        )
      } finally {
        creating.value = false
      }
    }

    const closeModal = () => {
      emit('close')
    }

    // Watch for modal visibility changes
    watch(() => props.isVisible, (newVal) => {
      if (newVal) {
        // Always fetch users when modal opens
        if (users.value.length === 0) {
          fetchUsers()
        } else {
          // If users already loaded, ensure filteredUsers is set
          if (filteredUsers.value.length === 0 && users.value.length > 0) {
            filteredUsers.value = [...users.value]
          }
        }
      } else {
        // Reset when modal closes
        showUserList.value = false
        userSearch.value = ''
        filteredUsers.value = users.value.length > 0 ? [...users.value] : []
      }
    })

    onMounted(() => {
      if (props.isVisible) {
        fetchUsers()
      }
    })

    return {
      formData,
      errors,
      creating,
      loadingUsers,
      users,
      userSearch,
      userSearchDisplay,
      filteredUsers,
      today,
      allUsersSelected,
      showUserList,
      showDatePicker,
      fetchUsers,
      filterUsers,
      toggleAllUsers,
      handleManualEmailChange,
      handleUserSelectionChange,
      handleUserListFocus,
      handleUserListBlur,
      handleDateBlur,
      handleDateInput,
      handleDateChange,
      openDatePicker,
      datePickerRef,
      createRequest,
      closeModal
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-container {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 900px;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease-out;
  overflow: hidden;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28px 32px;
  border-bottom: 2px solid #e5e7eb;
  background: #ffffff;
}

.modal-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  letter-spacing: -0.5px;
  padding-left: 0;
}

.modal-header h2::before,
.modal-header h2::after {
  display: none !important;
  content: none !important;
}

.close-btn {
  background: #f3f4f6;
  border: none;
  font-size: 24px;
  color: #6b7280;
  cursor: pointer;
  padding: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: all 0.2s;
  font-weight: 300;
  line-height: 1;
}

.close-btn:hover {
  background: #e5e7eb;
  color: #111827;
  transform: scale(1.05);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 32px 32px 32px;
  background: #ffffff;
}

.modal-body::-webkit-scrollbar {
  width: 8px;
}

.modal-body::-webkit-scrollbar-track {
  background: #f9fafb;
}

.modal-body::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

.policy-info-section {
  margin-bottom: 24px;
  margin-top: 0;
}

.policy-info-section h3 {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 20px 0;
}

.request-details-section {
  margin-bottom: 24px;
}

.request-details-section h3 {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 20px 0;
}

.form-section {
  margin-bottom: 36px;
  padding-bottom: 32px;
  border-bottom: 1px solid #e5e7eb;
}

.form-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.form-section h3 {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 20px 0;
}

.form-group {
  margin-bottom: 24px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 10px;
}

.required {
  color: #000000;
  font-weight: 700;
  margin-left: 2px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.input-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #6b7280;
  pointer-events: none;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.textarea-icon {
  top: 16px;
  transform: none;
  align-items: flex-start;
}

.calendar-icon {
  color: #6b7280;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 15px;
  transition: all 0.2s;
  background: #ffffff;
  color: #111827;
  font-family: inherit;
}

.user-select-input {
  cursor: pointer;
}

.user-select-input:read-only {
  cursor: pointer;
  background: #ffffff;
}

.form-textarea {
  padding-top: 12px;
  padding-left: 16px;
  resize: vertical;
  min-height: 100px;
  line-height: 1.5;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #000000;
  box-shadow: 0 0 0 4px rgba(0, 0, 0, 0.1);
  background: #ffffff;
}

.form-input:hover:not(:focus),
.form-textarea:hover:not(:focus) {
  border-color: #d1d5db;
}

.form-input.error,
.form-textarea.error {
  border-color: #000000;
  box-shadow: 0 0 0 4px rgba(0, 0, 0, 0.1);
}

.policy-label {
  margin-bottom: 10px;
}

.policy-label-text {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
}

.policy-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
  gap: 16px;
}

.policy-input {
  flex: 1;
  padding: 12px 16px;
  background: #f9fafb;
  cursor: not-allowed;
  border: 2px solid #86efac;
  color: #6b7280;
}

.policy-input:focus {
  border-color: #86efac;
  box-shadow: none;
  outline: none;
}

.policy-version {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
}

.user-selection-section {
  margin-bottom: 24px;
}

.user-selection-section h3 {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 20px 0;
}

.two-column-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.email-column,
.user-column {
  position: relative;
  display: flex;
  flex-direction: column;
}

.user-column .input-wrapper {
  margin-top: 32px; /* Match label height (15px font + line-height ~22px) + margin-bottom (10px) */
}

.user-column label {
  visibility: hidden;
  height: 0;
  margin: 0;
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-height: 450px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  text-align: left;
}

.user-dropdown-search {
  position: relative;
  padding: 12px;
  border-bottom: 1px solid #e5e7eb;
  background: #ffffff;
}

.user-dropdown-search .search-icon {
  position: absolute;
  left: 24px;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.dropdown-search-input {
  width: 100%;
  padding: 8px 12px 8px 36px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  background: #ffffff;
  color: #111827;
  font-family: inherit;
  transition: all 0.2s;
}

.dropdown-search-input:focus {
  outline: none;
  border-color: #6b7280;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.05);
}

.dropdown-search-input::placeholder {
  color: #9ca3af;
}

.loading-state {
  padding: 20px;
  text-align: center;
  color: #6b7280;
  font-size: 15px;
}

.loading-state .spinner {
  margin: 0 auto 16px;
}

.user-items::-webkit-scrollbar {
  width: 12px;
}

.user-items::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 6px;
}

.user-items::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 6px;
  border: 2px solid #f1f5f9;
}

.user-items::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.user-list-header {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
  background: #ffffff;
  position: sticky;
  top: 0;
  z-index: 10;
}

.user-items {
  padding: 8px 4px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  max-height: 280px;
  background: #ffffff;
  text-align: left;
  width: 100%;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
  color: #6b7280;
  font-size: 14px;
}

.user-item-wrapper {
  margin-bottom: 4px;
  text-align: left;
  width: 100%;
}

.user-item {
  display: flex;
  align-items: center;
  padding: 10px 8px 10px 8px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.15s ease;
  border: 1px solid #e5e7eb;
  width: 100%;
  box-sizing: border-box;
  background: #ffffff;
  min-height: 40px;
  text-align: left;
  justify-content: flex-start;
  margin: 0;
}

.user-item:hover {
  background: #dbeafe;
  border-color: #3b82f6;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.user-item:active {
  background: #bfdbfe;
  transform: translateX(0);
}

.user-item input[type="checkbox"] {
  margin-right: 10px;
  margin-left: 0;
  cursor: pointer;
  width: 16px;
  height: 16px;
  accent-color: #3b82f6;
  flex-shrink: 0;
  padding: 0;
}

.user-item input[type="checkbox"]:checked {
  accent-color: #2563eb;
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  text-align: left;
  justify-content: center;
  margin: 0;
  padding: 0;
}

.user-name {
  font-size: 13px;
  font-weight: 400;
  color: #374151;
  line-height: 1.5;
  display: block;
  visibility: visible;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  text-align: left;
  margin: 0;
  padding: 0;
  width: 100%;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-weight: 600;
  color: #111827;
  font-size: 14px;
  padding: 0;
  margin: 0;
}

.checkbox-label input[type="checkbox"] {
  margin-right: 10px;
  cursor: pointer;
  width: 16px;
  height: 16px;
  accent-color: #3b82f6;
  flex-shrink: 0;
}

.selected-count {
  margin-top: 20px;
  padding: 14px 18px;
  font-size: 15px;
  color: #000000;
  font-weight: 600;
  background: #f5f5f5;
  border-radius: 8px;
  border: 2px solid #000000;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.error-message {
  display: block;
  margin-top: 8px;
  font-size: 13px;
  color: #000000;
  font-weight: 500;
  padding-left: 4px;
}

.modal-footer {
  padding: 24px 32px;
  border-top: 2px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  background: #f9fafb;
}

.btn {
  padding: 12px 28px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 120px;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.btn-secondary {
  background: white;
  color: #374151;
  border: 2px solid #d1d5db;
}

.btn-secondary:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #9ca3af;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.btn-primary {
  background: #000000;
  color: white;
  border: 2px solid #000000;
}

.btn-primary:hover:not(:disabled) {
  background: #333333;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.spinner {
  width: 18px;
  height: 18px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Notification Settings Section */
.notification-section {
  margin-bottom: 24px;
}

.user-selection-section .form-group {
  position: relative;
}

.notification-title {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 700;
  color: #111827;
}

.notification-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  color: #374151;
  margin: 0;
  cursor: pointer;
  padding: 8px 0;
}

.notification-checkbox-label input[type="checkbox"] {
  width: 20px;
  height: 20px;
  margin: 0;
  cursor: pointer;
  flex-shrink: 0;
  accent-color: #000000;
}

.notification-checkbox-label span {
  white-space: nowrap;
}

.date-input {
  cursor: pointer;
}

.date-input::placeholder {
  color: #9ca3af;
}

.date-picker-hidden {
  position: absolute;
  opacity: 0;
  pointer-events: none;
  width: 0;
  height: 0;
}

.email-textarea {
  min-height: 80px;
  resize: vertical;
}

/* Responsive Design */
@media (max-width: 768px) {
  .modal-container {
    max-width: 95%;
    max-height: 95vh;
  }

  .modal-header {
    padding: 20px;
  }

  .modal-header h2 {
    font-size: 20px;
  }

  .modal-body {
    padding: 20px;
  }

  .form-section {
    margin-bottom: 24px;
    padding-bottom: 24px;
  }

  .two-column-layout {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .user-column label {
    visibility: visible;
    height: auto;
  }
}
</style>


