<template>
  <div class="report-container">
    <div class="report-header">
      <div class="header-content">
        <button class="back-btn" @click="goBack">
          <i class="icon-arrow-left"></i> Back
        </button>
        <div class="header-title">
          <h1>Acknowledgement Report</h1>
          <p v-if="reportData">{{ reportData.acknowledgement_request.title }}</p>
        </div>
      </div>
      <button v-if="reportData" class="btn-export" @click="exportReport">
         Export Report
      </button>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner-large"></div>
      <p>Loading report...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <i class="icon-error"></i>
      <h3>Failed to Load Report</h3>
      <p>{{ error }}</p>
      <button class="btn-retry" @click="fetchReport">Retry</button>
    </div>

    <div v-else-if="reportData" class="report-content">
      <!-- Summary Cards -->
      <div class="summary-section">
        <div class="summary-card">
          <div class="card-content">
            <div class="card-label">Total Users Assigned</div>
            <div class="card-value">{{ reportData.acknowledgement_request.total_users }}</div>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-content">
            <div class="card-label">Acknowledged</div>
            <div class="card-value">{{ reportData.acknowledgement_request.acknowledged_count }}</div>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-content">
            <div class="card-label">Pending</div>
            <div class="card-value">{{ reportData.acknowledgement_request.pending_count }}</div>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-content">
            <div class="card-label">Completion</div>
            <div class="card-value">{{ reportData.acknowledgement_request.completion_percentage }}%</div>
          </div>
        </div>
      </div>

      <!-- User List -->
      <div class="users-section">
        <div class="section-header">
          <h2>User Acknowledgements</h2>
          <div class="filter-buttons">
            <button 
              @click="filterStatus = 'all'"
              :class="{ 'active': filterStatus === 'all' }"
            >
              All ({{ reportData.users ? reportData.users.length : 0 }})
            </button>
            <button 
              @click="filterStatus = 'Acknowledged'"
              :class="{ 'active': filterStatus === 'Acknowledged' }"
            >
              Acknowledged ({{ reportData.status_summary ? reportData.status_summary.acknowledged : 0 }})
            </button>
            <button 
              @click="filterStatus = 'Pending'"
              :class="{ 'active': filterStatus === 'Pending' }"
            >
              Pending ({{ reportData.status_summary ? reportData.status_summary.pending : 0 }})
            </button>
            <button 
              @click="filterStatus = 'Overdue'"
              :class="{ 'active': filterStatus === 'Overdue' }"
            >
              Overdue ({{ reportData.status_summary ? reportData.status_summary.overdue : 0 }})
            </button>
          </div>
        </div>

        <div v-if="!reportData.users || reportData.users.length === 0" class="empty-state">
          <i class="icon-empty"></i>
          <h3>No Reports Available</h3>
          <p>There are no reports for this policy.</p>
        </div>
        <div v-else class="table-container">
          <table class="users-table">
            <thead>
              <tr>
                <th>Policy</th>
                <th>Version</th>
                <th>Due Date</th>
                <th>Created By</th>
                <th>User</th>
                <th>Email</th>
                <th>User Status</th>
                <th>Assigned At</th>
                <th>Acknowledged At</th>
                <th>Comments</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in filteredUsers" :key="user.user_id">
                <td>{{ reportData.acknowledgement_request.policy_name }}</td>
                <td>{{ reportData.acknowledgement_request.policy_version }}</td>
                <td>
                  {{ reportData.acknowledgement_request.due_date
                    ? formatDate(reportData.acknowledgement_request.due_date)
                    : 'No due date' }}
                </td>
                <td>{{ reportData.acknowledgement_request.created_by }}</td>
                <td>{{ user.user_name }}</td>
                <td>{{ user.email }}</td>
                <td>
                  <span class="status-badge" :class="user.status.toLowerCase()">
                    {{ user.status }}
                  </span>
                </td>
                <td>{{ formatDateTime(user.assigned_at) }}</td>
                <td>
                  <span v-if="user.acknowledged_at">{{ formatDateTime(user.acknowledged_at) }}</span>
                  <span v-else class="no-data">—</span>
                </td>
                <td>
                  <span v-if="user.comments" class="comments-cell" :title="user.comments">
                    {{ truncate(user.comments, 50) }}
                  </span>
                  <span v-else class="no-data">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { API_ENDPOINTS } from '../../config/api'
import { PopupService } from '@/modules/popus/popupService'

export default {
  name: 'AcknowledgementReport',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const loading = ref(false)
    const error = ref(null)
    const reportData = ref(null)
    const filterStatus = ref('all')

    const requestId = route.params.requestId

    const filteredUsers = computed(() => {
      if (!reportData.value || !reportData.value.users) return []
      
      if (filterStatus.value === 'all') {
        return reportData.value.users
      }
      
      return reportData.value.users.filter(user => user.status === filterStatus.value)
    })

    const fetchReport = async () => {
      try {
        loading.value = true
        error.value = null
        
        const response = await axios.get(API_ENDPOINTS.GET_ACKNOWLEDGEMENT_REPORT(requestId))
        reportData.value = response.data
      } catch (err) {
        console.error('Error fetching report:', err)
        error.value = err.response?.data?.error || 'Failed to load report'
        PopupService.error(error.value, 'Error')
      } finally {
        loading.value = false
      }
    }

    const exportReport = () => {
      if (!reportData.value) return

      const csvData = generateCSV()
      const blob = new Blob([csvData], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `acknowledgement-report-${requestId}-${Date.now()}.csv`
      a.click()
      window.URL.revokeObjectURL(url)

      PopupService.success('Report exported successfully', 'Export Complete')
    }

    const generateCSV = () => {
      const headers = [
        'Policy',
        'Version',
        'Due Date',
        'Created By',
        'User Name',
        'Email',
        'User Status',
        'Assigned At',
        'Acknowledged At',
        'Comments'
      ]

      const rows = reportData.value.users.map(user => [
        reportData.value.acknowledgement_request.policy_name,
        reportData.value.acknowledgement_request.policy_version,
        reportData.value.acknowledgement_request.due_date || '',
        reportData.value.acknowledgement_request.created_by,
        user.user_name,
        user.email,
        user.status,
        user.assigned_at,
        user.acknowledged_at || '',
        user.comments || ''
      ])

      return [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
      ].join('\n')
    }

    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const formatDateTime = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    const getUserInitials = (name) => {
      if (!name) return '??'
      const parts = name.split(/[\s._-]/)
      if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase()
      }
      return name.substring(0, 2).toUpperCase()
    }

    const truncate = (text, length) => {
      if (!text || text.length <= length) return text
      return text.substring(0, length) + '...'
    }

    const goBack = () => {
      router.back()
    }

    onMounted(() => {
      fetchReport()
    })

    return {
      loading,
      error,
      reportData,
      filterStatus,
      filteredUsers,
      fetchReport,
      exportReport,
      formatDate,
      formatDateTime,
      getUserInitials,
      truncate,
      goBack
    }
  }
}
</script>

<style scoped>
.report-container {
  margin-left: 260px; /* Account for sidebar width - same as CreatePolicy */
  padding: 20px 30px;
  padding-top: 40px;
  position: relative;
  min-height: calc(100vh - 80px);
  background: transparent;
  box-sizing: border-box;
  width: calc(100% - 260px); /* Subtract sidebar width */
  max-width: calc(100vw - 260px); /* Ensure it doesn't exceed viewport */
  overflow-x: hidden; /* Prevent horizontal overflow */
  overflow-y: auto; /* Allow vertical scrolling if needed */
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .report-container {
    margin-left: 0;
    width: 100%;
    padding: 10px;
  }
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  width: 100%;
  box-sizing: border-box;
  flex-wrap: wrap;
  gap: 16px;
}

.header-content {
  flex: 1;
}

.back-btn {
  background: white;
  border: 1px solid #e5e7eb;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.header-title h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
}

.header-title p {
  margin: 0;
  font-size: 16px;
  color: #6b7280;
}

.btn-export {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-export:hover {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.loading-state,
.error-state {
  padding: 80px 20px;
  text-align: center;
  background: white;
  border-radius: 12px;
}

.spinner-large {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 20px;
}

.error-state i {
  font-size: 48px;
  color: #ef4444;
  margin-bottom: 16px;
}

.btn-retry {
  margin-top: 16px;
  background: #3b82f6;
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 8px;
  cursor: pointer;
}

.report-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  padding: 0;
  margin: 0;
  overflow-x: hidden; /* Prevent horizontal overflow */
}

/* Ensure all child sections respect container width */
.report-content > * {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  overflow-x: hidden; /* Prevent horizontal overflow */
}

/* Exception: table container can scroll horizontally */
.report-content > .users-section {
  overflow-x: visible; /* Allow table container to handle scrolling */
}

.summary-section {
  display: grid;
  grid-template-columns: repeat(4, minmax(220px, 1fr)); /* Ensure minimum width for each card */
  gap: 20px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  overflow: visible;
  padding: 0;
  margin: 0;
  align-items: stretch;
}

/* Responsive: Stack cards on smaller screens */
@media (max-width: 1400px) {
  .summary-section {
    grid-template-columns: repeat(2, minmax(280px, 1fr));
  }
}

@media (max-width: 900px) {
  .summary-section {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}

.summary-card {
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 24px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  min-width: 220px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  overflow: visible;
  position: relative;
  flex-shrink: 0;
  min-height: 100px;
}

.summary-card:hover {
  background: transparent;
}

.card-icon {
  width: 60px;
  height: 60px;
  min-width: 60px;
  max-width: 60px;
  flex-shrink: 0;
  border-radius: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  border: 2px solid #e0e0e0;
  background: #fff;
  overflow: visible;
}

.card-icon.total {
  border-color: #333;
  color: #333;
}

.card-icon.acknowledged {
  border-color: #28a745;
  color: #28a745;
}

.card-icon.pending {
  border-color: #ffc107;
  color: #856404;
}

.card-icon.completion {
  border-color: #007bff;
  color: #007bff;
}

.card-content {
  flex: 1;
  min-width: 0;
  max-width: 100%;
  width: 100%;
  overflow: visible;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 0;
  box-sizing: border-box;
}

.card-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
  white-space: normal;
  overflow: visible;
  word-wrap: break-word;
  word-break: break-word;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 600;
  line-height: 1.4;
  width: 100%;
  display: block;
}

.card-value {
  font-size: 32px;
  font-weight: 700;
  color: #333;
  white-space: normal;
  overflow: visible;
  word-wrap: break-word;
  word-break: break-word;
  line-height: 1.2;
  display: block;
  min-height: 38px;
  width: 100%;
  box-sizing: border-box;
}

.progress-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  width: 100%;
  box-sizing: border-box;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.progress-bar {
  height: 12px;
  background: #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981 0%, #059669 100%);
  transition: width 0.3s ease;
}

.details-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  width: 100%;
  box-sizing: border-box;
  overflow-x: auto;
}

.details-section h2 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  font-size: 15px;
  color: #1f2937;
}

.description {
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.description p {
  margin: 8px 0 0 0;
  color: #374151;
  line-height: 1.6;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: capitalize;
}

.status-badge.active {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.completed {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.acknowledged {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.pending {
  background: #fef3c7;
  color: #92400e;
}

.status-badge.overdue {
  background: #fee2e2;
  color: #991b1b;
}

.status-badge.cancelled {
  background: #f3f4f6;
  color: #6b7280;
}

.users-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  overflow-x: visible; /* Let table-container handle scrolling */
  overflow-y: visible;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.section-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.filter-buttons {
  display: flex;
  gap: 8px;
}

.filter-buttons button {
  padding: 8px 16px;
  border: 1px solid #e5e7eb;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
  transition: all 0.2s;
}

.filter-buttons button:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.filter-buttons button.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.empty-state i {
  font-size: 64px;
  color: #9ca3af;
  margin-bottom: 16px;
  display: block;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #374151;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

.table-container {
  overflow-x: auto;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  -webkit-overflow-scrolling: touch;
  margin: 0;
  padding: 0;
}

/* Ensure tables don't overflow */
.table-container table {
  width: 100%;
  min-width: 1100px; /* Minimum width to maintain readability */
  table-layout: fixed; /* Fixed layout for better control */
  border-collapse: collapse;
}

.users-table thead {
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 10;
}

.users-table th {
  padding: 10px 8px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Column width distribution - optimize for content */
.users-table th:nth-child(1) { width: 14%; } /* Policy */
.users-table th:nth-child(2) { width: 7%; }  /* Version */
.users-table th:nth-child(3) { width: 9%; }  /* Due Date */
.users-table th:nth-child(4) { width: 11%; } /* Created By */
.users-table th:nth-child(5) { width: 11%; } /* User */
.users-table th:nth-child(6) { width: 14%; } /* Email */
.users-table th:nth-child(7) { width: 9%; }  /* User Status */
.users-table th:nth-child(8) { width: 11%; } /* Assigned At */
.users-table th:nth-child(9) { width: 11%; } /* Acknowledged At */
.users-table th:nth-child(10) { width: 3%; }  /* Comments */

.users-table td {
  padding: 12px 8px;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
  color: #374151;
  word-wrap: break-word;
  overflow-wrap: break-word;
  vertical-align: top;
  max-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Allow certain columns to wrap text for better readability */
.users-table td:nth-child(1), /* Policy */
.users-table td:nth-child(6) { /* Email */
  white-space: normal;
  word-break: break-word;
}

/* Keep dates and statuses on one line */
.users-table td:nth-child(2), /* Version */
.users-table td:nth-child(3), /* Due Date */
.users-table td:nth-child(7), /* User Status */
.users-table td:nth-child(8), /* Assigned At */
.users-table td:nth-child(9) { /* Acknowledged At */
  white-space: nowrap;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 12px;
}

.no-data {
  color: #9ca3af;
}

.comments-cell {
  display: block;
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: help;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Icon styles */
.icon-arrow-left::before { content: '←'; }
.icon-download::before { content: '⬇'; }
.icon-users::before { content: '👥'; }
.icon-check-circle::before { content: '✓'; }
.icon-clock::before { content: '🕐'; }
.icon-chart::before { content: '📊'; }
.icon-error::before { content: '⚠️'; }
.icon-empty::before { content: '📄'; }
</style>

