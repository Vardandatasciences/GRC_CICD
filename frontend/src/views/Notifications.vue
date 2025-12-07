<template>
  <div class="notifications-page large">
    <div class="header-row">
      <h1>Notifications</h1>
      <button class="mark-all" @click="markAllAsRead" :disabled="loading">Mark All as Read</button>
    </div>
    <div class="search-filter-row">
      <input v-model="search" placeholder="Search notifications..." class="search-input" />
      <div class="filters">
        <select v-model="filterType">
          <option value="">All Types</option>
          <option v-for="type in moduleTypes" :key="type" :value="type">{{ type }}</option>
        </select>
        <select v-model="filterPriority">
          <option value="">All Priorities</option>
          <option v-for="priority in priorities" :key="priority" :value="priority">{{ priority }}</option>
        </select>
        <button class="analytics-btn" @click="showAnalytics = true">
          <svg width="18" height="18" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right:6px;"><rect x="2" y="10" width="2.5" height="6" rx="1" fill="#1976d2"/><rect x="6.5" y="6" width="2.5" height="10" rx="1" fill="#1976d2"/><rect x="11" y="2" width="2.5" height="14" rx="1" fill="#1976d2"/><rect x="15.5" y="13" width="2.5" height="3" rx="1" fill="#1976d2"/></svg>
          <span>Analytics</span>
        </button>
      </div>
    </div>
    
    <!-- Loading state -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading notifications...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadNotifications" class="retry-btn">Retry</button>
    </div>

    <!-- Notifications table -->
    <table v-else class="notifications-table">
      <thead>
        <tr>
          <th>Notification</th>
          <th>Priority</th>
          <th>Time</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="notification in filteredNotifications" :key="notification.id" :class="{ unread: !notification.status.isRead, clickable: isClickable(notification) }" @click="handleNotificationClick(notification)">
          <td>
            <div class="notification-main">
              <span :class="['module-icon', notification.category.toLowerCase()]">
                {{ moduleInitial(notification.category) }}
              </span>
              <div class="notification-text">
                <div class="notification-title">{{ notification.title }}</div>
                <div class="notification-description">{{ notification.message }}</div>
              </div>
            </div>
          </td>
          <td>
            <span :class="['priority', notification.priority.toLowerCase()]">
              {{ notification.priority }}
            </span>
          </td>
          <td>{{ formatTime(notification.createdAt) }}</td>
          <td>
            <div class="status-cell">
              <span :class="['status', notification.status.isRead ? 'read' : 'unread']">
                {{ notification.status.isRead ? 'Read' : 'Unread' }}
              </span>
              <button 
                v-if="!notification.status.isRead" 
                @click.stop="markAsRead(notification.id)" 
                class="action-btn read-btn"
                title="Mark as read"
              >
                ✓
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Empty state -->
    <div v-if="!loading && !error && filteredNotifications.length === 0" class="empty-state">
      <p>No notifications found</p>
    </div>

    <!-- Analytics Modal -->
    <div v-if="showAnalytics" class="modal-overlay" @click.self="showAnalytics = false">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Notifications Analytics</h2>
          <button class="close-btn" @click="showAnalytics = false">&times;</button>
        </div>
        <div class="modal-body">
          <Bar :data="barChartData" :options="barChartOptions" />
        </div>
      </div>
    </div>
    <!-- Modern Popup for New Notification -->
    <transition name="fade">
      <div v-if="showPopup" class="notification-popup">
        <div class="popup-type">{{ popupData.category ? popupData.category.toUpperCase() : 'NOTIFICATION' }}</div>
        <div class="popup-title">{{ popupData.title }}</div>
        <div class="popup-message">{{ popupData.message }}</div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Bar } from 'vue-chartjs';
import { API_BASE_URL } from '../config/api.js';
import {
  Chart,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
} from 'chart.js';
// Define component name to satisfy ESLint multi-word requirement
defineOptions({
  name: 'NotificationsPage'
});

Chart.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

const router = useRouter();

const showAnalytics = ref(false);
const loading = ref(false);
const error = ref(null);
const notifications = ref([]);
const stats = ref({});

const moduleTypes = ['policy', 'compliance', 'audit', 'risk', 'incident', 'common', 'account'];
const priorities = ['urgent', 'high', 'medium', 'low'];

const search = ref('');
const filterType = ref('');
const filterPriority = ref('');

// Mock user ID for demo purposes (keeping for future use)
// const userId = '507f1f77bcf86cd799439011';

const filteredNotifications = computed(() => {
  return notifications.value.filter(n => {
    // Check if this is an acknowledgement notification
    const isAcknowledgementNotification = n.title && (
      n.title.includes('Acknowledgement Request') || 
      n.title.includes('Policy Acknowledgement')
    );
    
    // Only hide read acknowledgement notifications (after policy is acknowledged)
    // Unread acknowledgement notifications should still be visible
    if (isAcknowledgementNotification && n.status.isRead) {
      return false; // Hide read acknowledgement notifications
    }
    // Unread acknowledgement notifications will continue to show (not filtered out)
    
    const matchesSearch =
      n.title.toLowerCase().includes(search.value.toLowerCase()) ||
      n.message.toLowerCase().includes(search.value.toLowerCase());
    const matchesType = !filterType.value || n.category === filterType.value;
    const matchesPriority = !filterPriority.value || n.priority === filterPriority.value;
    return matchesSearch && matchesType && matchesPriority;
  });
});

// Load notifications from backend
const loadNotifications = async () => {
  loading.value = true;
  error.value = null;
  try {
    // Get current user ID from localStorage
    const userId = localStorage.getItem('user_id') || 'default_user';
    
    // Try to load from backend first
    const response = await fetch(`${API_BASE_URL}/api/get-notifications/?user_id=${userId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      }
    });
    if (response.ok) {
      const data = await response.json();
      if (data.status === 'success') {
        notifications.value = data.notifications;
      } else {
        throw new Error('Failed to load notifications from backend');
      }
    } else {
      throw new Error('Backend not available');
    }
  } catch (err) {
    console.error('Error loading notifications:', err);
    // No fallback to dummy data - show empty state
    notifications.value = [];
    error.value = 'Failed to load notifications';
  } finally {
    loading.value = false;
  }
};

// Load notification statistics
const loadStats = async () => {
  try {
    // For now, use dummy stats
    stats.value = {
      total: notifications.value.length,
      unread: notifications.value.filter(n => !n.status.isRead).length
    };
  } catch (err) {
    console.error('Error loading stats:', err);
  }
};

// Popup state
const showPopup = ref(false);
const popupData = ref({});
// let popupTimeout = null; // Keeping for future use when triggerPopup is uncommented

// Show popup for new notification (keeping for future use)
// function triggerPopup(notification) {
//   popupData.value = notification;
//   showPopup.value = true;
//   if (popupTimeout) clearTimeout(popupTimeout);
//   popupTimeout = setTimeout(() => {
//     showPopup.value = false;
//   }, 5000);
// }

// Mark notification as read
const markAsRead = async (notificationId) => {
  // Update local state immediately for better UX
  const notification = notifications.value.find(n => n.id === notificationId);
  if (notification && !notification.status.isRead) {
    notification.status.isRead = true;
    notification.status.readAt = new Date();
  }
  // Try to update backend
  try {
    await fetch(`${API_BASE_URL}/api/mark-as-read/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ notification_id: notificationId })
    });
    // Reload notifications from backend to get the updated status
    await loadNotifications();
  } catch (error) {
    console.error('Error marking notification as read:', error);
  }
};

// Mark all notifications as read (EXCEPT acknowledgement notifications - they must be acknowledged first)
const markAllAsRead = async () => {
  // Update local state immediately for better UX (but skip acknowledgement notifications)
  notifications.value.forEach(n => {
    // Don't mark acknowledgement notifications as read - they must be acknowledged first
    const isAcknowledgementNotification = n.title && (
      n.title.includes('Acknowledgement Request') || 
      n.title.includes('Policy Acknowledgement')
    )
    
    if (!n.status.isRead && !isAcknowledgementNotification) {
      n.status.isRead = true;
      n.status.readAt = new Date();
    }
  });
  
  // Try to update backend (backend should also exclude acknowledgement notifications)
  try {
    const userId = localStorage.getItem('user_id') || 'default_user';
    await fetch(`${API_BASE_URL}/api/mark-all-as-read/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        user_id: userId,
        exclude_acknowledgements: true // Tell backend to exclude acknowledgement notifications
      })
    });
    // Reload notifications to get updated status
    await loadNotifications();
  } catch (error) {
    console.error('Error marking all notifications as read:', error);
  }
};

// Format time for display
const formatTime = (timestamp) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffInMinutes = Math.floor((now - date) / (1000 * 60));
  
  if (diffInMinutes < 1) return 'Just now';
  if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`;
  
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) return `${diffInHours} hours ago`;
  
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) return `${diffInDays} days ago`;
  
  return date.toLocaleDateString();
};

function moduleInitial(module) {
  return module.charAt(0).toUpperCase();
}

// Check if notification is clickable (for acknowledgement notifications)
const isClickable = (notification) => {
  return notification.title && (
    notification.title.includes('Acknowledgement Request') ||
    notification.title.includes('Policy Acknowledgement')
  );
};

// Handle notification click
const handleNotificationClick = (notification) => {
  if (isClickable(notification)) {
    // Don't mark as read yet - keep notification visible until action is taken
    // Navigate to pending acknowledgements page
    router.push('/pending-acknowledgements');
  }
};

// Analytics Data
const barChartData = computed(() => {
  const data = {};
  moduleTypes.forEach(module => {
    data[module] = { urgent: 0, high: 0, medium: 0, low: 0 };
  });
  
  notifications.value.forEach(n => {
    if (data[n.category]) {
      data[n.category][n.priority]++;
    }
  });
  
  return {
    labels: moduleTypes.map(m => m.charAt(0).toUpperCase() + m.slice(1)),
    datasets: [
      {
        label: 'Urgent',
        backgroundColor: '#b71c1c',
        borderColor: '#b71c1c',
        data: moduleTypes.map(m => data[m].urgent),
      },
      {
        label: 'High',
        backgroundColor: '#ff6f00',
        borderColor: '#ff6f00',
        data: moduleTypes.map(m => data[m].high),
      },
      {
        label: 'Medium',
        backgroundColor: '#1565c0',
        borderColor: '#1565c0',
        data: moduleTypes.map(m => data[m].medium),
      },
      {
        label: 'Low',
        backgroundColor: '#37474f',
        borderColor: '#37474f',
        data: moduleTypes.map(m => data[m].low),
      },
    ],
  };
});

const barChartOptions = {
  responsive: true,
  plugins: {
    legend: { position: 'top' },
    title: { display: true, text: 'Notifications by Module and Priority' },
  },
  scales: {
    x: { stacked: true },
    y: { stacked: true, beginAtZero: true, precision: 0 },
  },
};

// Lifecycle hooks
onMounted(async () => {
  // Load initial data
  await loadNotifications();
  await loadStats();
});
</script>

<style scoped>
.notifications-page {
  max-width: 100%;
  margin: 10px 0 10px 280px;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  padding: 10px 20px;
}
.notifications-page.large {
  max-width: 100%;
}
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.header-row h1 {
  font-size: 2rem;
  margin-top: 30px;
  font-weight: 700;
}
.mark-all {
  background: #1976d2;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 8px 20px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.mark-all:hover:not(:disabled) {
  background: #1251a3;
}
.mark-all:disabled {
  background: #ccc;
  cursor: not-allowed;
}
.search-filter-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.search-input {
  flex: 1;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
  margin-right: 16px;
}
.filters {
  display: flex;
  align-items: center;
  background: transparent;
  border: none;
  box-shadow: none;
}
.filters select {
  margin-left: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}
.analytics-btn {
  margin-left: 8px;
  background: #fff;
  color: #1976d2;
  border: 1.5px solid #1976d2;
  border-radius: 6px;
  padding: 6px 8px;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  transition: none;
  display: flex;
  align-items: center;
}
.analytics-btn:hover {
  background: #fff;
  color: #1976d2;
  border: 1.5px solid #1976d2;
}

/* Loading and Error States */
.loading-state, .error-state, .empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}
.loading-spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #1976d2;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.retry-btn {
  background: #1976d2;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  cursor: pointer;
  margin-top: 8px;
}

.notifications-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
  border: 1px solid #e5e7eb;
  overflow: hidden;
}
.notifications-table th, .notifications-table td {
  padding: 18px 16px;
  text-align: left;
  vertical-align: top;
}
.notifications-table tbody td,
.notifications-table tbody span,
.notifications-table tbody div {
  font-size: 0.85rem;
}
.notifications-table thead {
  background: #f7f7fa;
}
.notifications-table tbody tr.unread {
  background: transparent;
}
.notification-main {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}
.notification-text {
  display: flex;
  flex-direction: column;
}
.notification-title {
  font-weight: 700;
  font-size: 1.08rem;
  margin-bottom: 2px;
}
.notification-description {
  color: #636e72;
  font-size: 0.98rem;
}
.module-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 1.2rem;
  color: black;
}
.module-icon.policy { background: #dedfe0; }
.module-icon.compliance { background: #dedfe0; }
.module-icon.audit { background: #dedfe0; }
.module-icon.risk { background: #dedfe0; }
.module-icon.incident { background: #dedfe0; }
.module-icon.common { background: #dedfe0; }
.module-icon.account { background: #dedfe0; }
.priority {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 600;
  color: #333;
  display: inline-block;
  background: #f4f6fb;
  border: 1px solid #e0e0e0;
}
.priority.urgent { background: #fdeaea; color: #d7263d; border-color: #f8d7da; }
.priority.high { background: #fff4e1; color: #ff9800; border-color: #ffd699; }
.priority.medium { background: #e3f0fd; color: #1976d2; border-color: #90caf9; }
.priority.low { background: #eceff1; color: #607d8b; border-color: #cfd8dc; }
.status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 600;
  display: inline-block;
}
.status-cell {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-left: -12px;
}

/* Action Buttons */
.action-btn {
  background: none;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}
.read-btn:hover {
  background: #e8f5e8;
}
.read-btn {
  background: #e8f5e8;
  border: 1px solid #1976d2;
  color: #1976d2;
  border-radius: 4px;
  padding: 2px 10px;
  font-size: 0.85rem;
}

.read-btn.disabled {
  background: #fff3cd;
  border: 1px solid #ffc107;
  color: #856404;
  cursor: not-allowed;
  opacity: 0.8;
}
.archive-btn:hover {
  background: #fff3e0;
}

/* Clickable notification rows */
.notifications-table tbody tr.clickable {
  cursor: pointer;
}

.notifications-table tbody tr.clickable:hover {
  background-color: #f5f5f5 !important;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0,0,0,0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-content {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.12);
  padding: 24px 32px 32px 32px;
  min-width: 400px;
  max-width: 90vw;
  min-height: 320px;
  position: relative;
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  color: #888;
  cursor: pointer;
  line-height: 1;
}
.close-btn:hover {
  color: #1976d2;
}

/* Modern popup styles */
.notification-popup {
  position: fixed;
  left: 32px;
  bottom: 32px;
  min-width: 320px;
  max-width: 400px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(25, 118, 210, 0.18), 0 1.5px 6px rgba(0,0,0,0.08);
  padding: 20px 28px 18px 24px;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-left: 6px solid #1976d2;
  animation: popup-in 0.3s cubic-bezier(.4,0,.2,1);
}
.popup-type {
  font-size: 0.92rem;
  font-weight: 700;
  color: #1976d2;
  letter-spacing: 1px;
  margin-bottom: 2px;
}
.popup-title {
  font-size: 1.08rem;
  font-weight: 600;
  color: #222;
}
.popup-message {
  font-size: 0.98rem;
  color: #444;
}
@keyframes popup-in {
  from { opacity: 0; transform: translateY(40px); }
  to { opacity: 1; transform: translateY(0); }
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.4s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style> 