<template>
  <div class="task-section" :class="sectionConfig.statusClass">
    <div class="task-section-header" @click="toggleSection">
      <div class="header-left">
        <component 
          :is="isExpanded ? PhCaretDown : PhCaretRight" 
          :size="16" 
        />
        <div :class="['status-chip', sectionConfig.statusClass]">
          <component :is="headerIcon" :size="14" :weight="headerIconWeight" />
          <span>{{ sectionConfig.name }}</span>
        </div>
      </div>
      <div class="header-right">
      </div>
    </div>
    
    <div v-if="isExpanded">
      <table class="task-table">
        <thead>
          <tr>
            <th v-for="header in tableHeaders" :key="header.key" :class="header.className" :style="{ width: columnWidths[header.key] ? columnWidths[header.key] + 'px' : (header.width ? header.width : 'auto') }">
              {{ header.label }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in sortedTasks" :key="task.incidentId">
            <td v-for="header in tableHeaders" :key="header.key" :class="header.className" :style="{ width: columnWidths[header.key] ? columnWidths[header.key] + 'px' : (header.width ? header.width : 'auto') }">
              <template v-if="header.key === 'actions'">
                <div class="actions-cell">
                  <button class="view-details-btn" @click="$emit('taskClick', task)" title="View Details">
                    <i class="fas fa-eye"></i>
                  </button>
                  <button 
                    v-if="sectionConfig.name === 'Rejected Compliances (Edit & Resubmit)' || 
                          sectionConfig.name === 'Rejected Frameworks (Edit & Resubmit)' || 
                          sectionConfig.name === 'Rejected Policies (Edit & Resubmit)'" 
                    class="edit-btn" 
                    @click.stop="$emit('editTask', task)" 
                    title="Edit & Resubmit"
                  >
                    <i class="fas fa-edit"></i>
                  </button>
                </div>
              </template>
              <template v-else-if="['criticality','priority','status'].includes(header.key)">
                <span v-html="task[header.key]"></span>
              </template>
              <template v-else>
                <div 
                  class="cell-content"
                  :class="{ 'truncated': isTextTruncated(task[header.key]) }"
                  :title="isTextTruncated(task[header.key]) ? task[header.key] : ''"
                >
                  {{ task[header.key] }}
                </div>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
      <Pagination
        v-if="pagination"
        :current-page="pagination.currentPage"
        :total-pages="pagination.totalPages"
        :page-size="pagination.pageSize"
        :total-items="pagination.totalCount"
        :page-size-options="pagination.pageSizeOptions || [6, 15, 30, 50]"
        @update:page="handlePageChange"
        @update:pageSize="handlePageSizeChange"
      />
    </div>
  </div>
</template>

<script setup>
/* eslint-disable no-undef */
import { computed, ref, onMounted, onBeforeUnmount } from 'vue';
import Pagination from './Pagination.vue';
import { 
  PhCaretDown, 
  PhCaretRight, 
  PhCircleNotch,
  PhCircle,
  PhCheckCircle
} from '@phosphor-icons/vue';

const props = defineProps({
  sectionConfig: {
    type: Object,
    required: true
  },
  tableHeaders: {
    type: Array,
    required: true
  },
  isExpanded: {
    type: Boolean,
    default: true
  },
  pagination: {
    type: Object,
    default: null
  }
});

// Add debugging for pagination
console.log('CollapsibleTable props:', {
  sectionName: props.sectionConfig?.name,
  pagination: props.pagination,
  isExpanded: props.isExpanded,
  tasksCount: props.sectionConfig?.tasks?.length,
  paginationDetails: props.pagination ? {
    currentPage: props.pagination.currentPage,
    totalPages: props.pagination.totalPages,
    pageSize: props.pagination.pageSize,
    totalCount: props.pagination.totalCount
  } : null
});

const emit = defineEmits(['toggle', 'addTask', 'taskClick', 'editTask']);

const toggleSection = () => {
  emit('toggle');
};

const handlePageChange = (page) => {
  console.log('CollapsibleTable: Page change requested to:', page);
  if (props.pagination && props.pagination.onPageChange) {
    props.pagination.onPageChange(page);
  }
};

const handlePageSizeChange = (size) => {
  console.log('CollapsibleTable: Page size change requested to:', size);
  if (props.pagination && props.pagination.onPageSizeChange) {
    props.pagination.onPageSizeChange(size);
  }
};

const headerIcon = computed(() => {
  switch (props.sectionConfig.name) {
    case 'Pending':
    case 'Pending Review':
    case 'Open':
    case 'Assigned':
    case 'Yet to Start':
      return PhCircle;
    case 'In Progress':
    case 'Under Review':
    case 'Scheduled':
      return PhCircleNotch;
    case 'Completed':
    case 'Closed':
    case 'Approved':
      return PhCheckCircle;
    case 'Rejected':
      return PhCircle;
    case 'Not Assigned':
    case 'Unknown':
      return PhCircle;
    default:
      return PhCircle;
  }
});

const headerIconWeight = computed(() => {
  const status = props.sectionConfig.name;
  return (status === 'Pending' || status === 'Pending Review' || status === 'Open' || status === 'Rejected' || status === 'Assigned' || status === 'Not Assigned' || status === 'Yet to Start' || status === 'Unknown') ? 'light' : 'fill';
});

// Function to check if text should be truncated
const isTextTruncated = (text) => {
  if (!text || typeof text !== 'string') return false;
  return text.length > 50; // Adjust this threshold as needed
};

// Sorting state
const sortKey = ref('');
const sortOrder = ref('asc');


const sortedTasks = computed(() => {
  if (!sortKey.value) return props.sectionConfig.tasks;
  return [...props.sectionConfig.tasks].sort((a, b) => {
    const aVal = a[sortKey.value];
    const bVal = b[sortKey.value];
    if (aVal == null) return 1;
    if (bVal == null) return -1;
    if (aVal < bVal) return sortOrder.value === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });
});

// Resizable columns
const columnWidths = ref({});
const resizing = ref({ active: false, columnKey: null, startX: 0, startWidth: 0 });


const onResizeMove = (e) => {
  if (!resizing.value.active) return;
  const clientX = e.type.startsWith('touch') ? e.touches[0].clientX : e.clientX;
  const delta = clientX - resizing.value.startX;
  let newWidth = resizing.value.startWidth + delta;
  if (newWidth < 50) newWidth = 50;
  columnWidths.value = { ...columnWidths.value, [resizing.value.columnKey]: newWidth };
};

const onResizeEnd = () => {
  if (resizing.value.active) {
    resizing.value.active = false;
    resizing.value.columnKey = null;
  }
};

onMounted(() => {
  window.addEventListener('mousemove', onResizeMove);
  window.addEventListener('mouseup', onResizeEnd);
  window.addEventListener('touchmove', onResizeMove);
  window.addEventListener('touchend', onResizeEnd);
});
onBeforeUnmount(() => {
  window.removeEventListener('mousemove', onResizeMove);
  window.removeEventListener('mouseup', onResizeEnd);
  window.removeEventListener('touchmove', onResizeMove);
  window.removeEventListener('touchend', onResizeEnd);
});
</script>

<style>
/* CSS Variables for status colors */
:root {
  --chip-pending-text: #2196f3;
  --chip-pending-bg: #e3f2fd;
  --chip-pending-border: rgba(33, 150, 243, 0.3);
  --chip-pending-icon: #2196f3;
  
  --chip-inprogress-text: #ff9800;
  --chip-inprogress-bg: #fff8e1;
  --chip-inprogress-border: rgba(255, 152, 0, 0.3);
  --chip-inprogress-icon: #ff9800;
  
  --chip-completed-text: #4caf50;
  --chip-completed-bg: #e8f5e8;
  --chip-completed-border: rgba(76, 175, 80, 0.3);
  --chip-completed-icon: #4caf50;
  
  --chip-rejected-text: #f44336;
  --chip-rejected-bg: #ffebee;
  --chip-rejected-border: rgba(244, 67, 54, 0.3);
  --chip-rejected-icon: #f44336;
  
  --table-section-border: #e0e0e0;
  --table-section-bg: #ffffff;
  --table-header-text: #333333;
  --table-header-dots: #666666;
  --table-row-text: #333333;
  --table-subheader-text: #666666;
  --incident-primary: #6a5acd;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.task-section {
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  margin-bottom: 2rem;
  background: transparent !important;
  box-shadow: none !important;
}

.task-section.approved {
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.task-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 1.5rem 2rem;
  cursor: pointer;
  font-weight: 500;
  color: var(--table-header-text);
  transition: background-color 0.2s ease;
  border-radius: 12px 12px 0 0;
  background-color: white;
}

.task-section-header:hover {
  background-color: white;
}

.task-section-header:active {
  background-color: white;
}

.task-section-header .header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-section-header .header-right {
  color: var(--table-header-dots);
}

.toggle-icon {
  font-size: 14px;
  color: var(--table-header-text);
  transition: transform 0.2s ease;
}

.status-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 2px 8px;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
}

.status-chip.pending {
  color: var(--chip-pending-text);
  background-color: var(--chip-pending-bg);
  border-color: var(--chip-pending-border);
}

.status-chip.pending .ph-circle {
  color: var(--chip-pending-icon);
}

.status-chip.in-progress {
  color: var(--chip-inprogress-text);
  background-color: var(--chip-inprogress-bg);
  border-color: var(--chip-inprogress-border);
}

.status-chip.in-progress .ph-circle-notch {
  color: var(--chip-inprogress-icon);
  animation: spin 2s linear infinite;
}

.status-chip.completed {
  color: var(--chip-completed-text);
  background-color: var(--chip-completed-bg);
  border-color: var(--chip-completed-border);
}

.status-chip.completed .ph-check-circle {
  color: var(--chip-completed-icon);
}

.status-chip.rejected {
  color: var(--chip-rejected-text);
  background-color: transparent;
  border-color: var(--chip-rejected-border);
}

.task-section.rejected {
  background-color: transparent !important;
}

.task-section.rejected .task-section-header {
  background-color: transparent !important;
}

.task-section.rejected .task-table td {
  color: black !important;
}

.task-section.rejected .task-table td .cell-content {
  color: black !important;
}

/* Override color for action buttons in rejected section */
.task-section.rejected .task-table td .actions-cell,
.task-section.rejected .task-table td .actions-cell .view-details-btn,
.task-section.rejected .task-table td .actions-cell .edit-btn {
  color: inherit !important;
}

.task-section.rejected .task-table td .actions-cell .view-details-btn {
  color: #3b82f6 !important;
}

.task-section.rejected .task-table td .actions-cell .edit-btn {
  color: #000000 !important;
}

.task-section.rejected .task-table td .actions-cell .view-details-btn i {
  color: #3b82f6 !important;
}

.task-section.rejected .task-table td .actions-cell .edit-btn i {
  color: #000000 !important;
}

/* Keep criticality column red for rejected tasks */
.task-section.rejected .task-table td:nth-child(4) {
  color: #f44336 !important;
}

.task-section.rejected .task-table td:nth-child(4) .cell-content {
  color: #f44336 !important;
}

.status-chip.rejected .ph-circle {
  color: var(--chip-rejected-icon);
}

/* Remove flex/grid for .task-list-header and .task-item, add table styling */
.task-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 0;
  table-layout: fixed !important; /* Fixed table layout for better column control */
  border: none !important;
  outline: none !important;
}

.task-table::-webkit-scrollbar {
  display: none !important;
}

.task-table {
  -ms-overflow-style: none !important;
  scrollbar-width: none !important;
}

.task-table th,
.task-table td {
  resize: none !important;
  user-select: none !important;
  -webkit-user-select: none !important;
  -moz-user-select: none !important;
  -ms-user-select: none !important;
}

/* Set fixed column widths */
.task-table th:nth-child(1),
.task-table td:nth-child(1) {
  width: 10% !important; /* RISK ID */
}

.task-table th:nth-child(2),
.task-table td:nth-child(2) {
  width: 35% !important; /* RISK TITLE - Increased width for better text wrapping */
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  white-space: normal !important;
  hyphens: auto !important;
  line-height: 1.4 !important;
  max-width: 0 !important; /* Force text wrapping */
  overflow: hidden !important;
  padding: 10px 8px !important;
}

.task-table th:nth-child(3),
.task-table td:nth-child(3) {
  width: 15% !important; /* CATEGORY */
}

.task-table th:nth-child(4),
.task-table td:nth-child(4) {
  width: 12% !important; /* CRITICALITY */
}

.task-table th:nth-child(5),
.task-table td:nth-child(5) {
  width: 15% !important; /* ASSIGNED TO */
}

.task-table th:nth-child(6),
.task-table td:nth-child(6) {
  width: 13% !important; /* REVIEWER */
}

.task-table th:nth-child(7),
.task-table td:nth-child(7) {
  width: 10% !important; /* REVIEW COUNT */
}

.task-table th:nth-child(8),
.task-table td:nth-child(8) {
  width: 10% !important; /* ACTION */
}

.task-table thead {
  border: none !important;
  background: transparent !important;
}

.task-table thead tr {
  border: none !important;
  background: transparent !important;
}

.task-table thead th {
  border: none !important;
  border-bottom: none !important;
  background: transparent !important;
}

.task-table th *,
.task-table th div,
.task-table th span {
  border: none !important;
  background: transparent !important;
}
.task-table th {
  background: transparent !important;
  background-color: transparent !important;
  font-weight: 500;
  color: #495057;
  font-size: 11px !important;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  border: none !important;
  border-right: 1px solid #e0e0e0 !important;
  border-bottom: 1px solid #e0e0e0 !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  white-space: normal !important;
  line-height: 1.3 !important;
  padding: 6px 8px !important;
  margin: 0px !important;
  box-shadow: none !important;
  text-align: left;
  vertical-align: top;
}

/* Remove right border from last header column */
.task-table th:last-child {
  border-right: none !important;
}

.task-table td {
  padding: 8px 10px;
  text-align: left;
  vertical-align: top;
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
  border-bottom: 1px solid #e0e0e0;
  border-right: 1px solid #e0e0e0;
  border-left: 1px solid #e0e0e0;
  border-top: 1px solid #e0e0e0;
  font-size: 11px;
  line-height: 1.3;
}
.task-table tr:last-child td {
  border-bottom: none;
}

/* Cell content with proper text wrapping */
.cell-content {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: normal; /* Changed from nowrap to normal for text wrapping */
  cursor: default;
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
  line-height: 1.3;
  min-height: 18px; /* Ensure minimum height for content */
  font-size: 11px;
}

/* Specific styling for Risk Title column (2nd column) to prevent overflow */
.task-table td:nth-child(2) {
  overflow: hidden !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  white-space: normal !important;
  hyphens: auto !important;
  line-height: 1.3 !important;
  max-width: 0 !important;
  padding: 8px 6px !important;
  font-size: 11px !important;
}

.task-table td:nth-child(2) * {
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  white-space: normal !important;
  hyphens: auto !important;
  max-width: 100% !important;
  display: block !important;
}

.cell-content.truncated {
  position: relative;
  white-space: normal; /* Allow wrapping even for truncated content */
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.cell-content.truncated:hover::after {
  content: attr(title);
  position: absolute;
  left: 0;
  top: 100%;
  background: #333;
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  white-space: normal;
  max-width: 300px;
  word-wrap: break-word;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  margin-top: 4px;
}

/* Ensure the actions column has a minimum width */
.task-list-header .task-actions,
.task-item .task-actions {
  min-width: 140px;
  max-width: 180px;
}

/* Fix for Risk Workflow table - ensure proper column widths */
.task-table th:nth-child(7), /* Actions column */
.task-table td:nth-child(7) {
  min-width: 120px;
  max-width: 140px;
  width: 120px;
  white-space: nowrap;
  overflow: visible;
}

/* Ensure Risk Description column has proper width */
.task-table th:nth-child(5), /* Risk Description column */
.task-table td:nth-child(5) {
  min-width: 200px;
  max-width: 300px;
  word-wrap: break-word;
  overflow-wrap: break-word;
  white-space: normal;
}

/* Additional fixes for Risk Workflow table */
.task-table {
  table-layout: fixed;
  width: 100%;
  min-width: 800px; /* Ensure minimum width for all columns */
}

/* Ensure table container can scroll horizontally if needed */
.task-section {
  overflow-x: auto;
  overflow-y: visible;
}

/* Make sure all cells have proper box-sizing */
.task-table th,
.task-table td {
  box-sizing: border-box;
}

.incident-id {
  font-weight: 600;
  color: var(--table-row-text);
}

/* Responsive adjustments for better text wrapping */
@media screen and (max-width: 768px) {
  .task-table {
    font-size: 10px;
  }
  
  .task-table td {
    padding: 6px 8px;
  }
  
  .cell-content {
    font-size: 10px;
    line-height: 1.2;
    min-height: 14px;
  }
}

@media screen and (max-width: 480px) {
  .task-table {
    font-size: 9px;
  }
  
  .task-table td {
    padding: 4px 6px;
  }
  
  .cell-content {
    font-size: 9px;
    line-height: 1.1;
    min-height: 12px;
  }
}

.incident-title {
  font-weight: 500;
  color: var(--table-row-text);
}

.incident-priority {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.incident-status {
  display: flex;
  align-items: center;
}

.incident-origin {
  color: var(--table-row-text);
  font-size: 14px;
}

.incident-date {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--table-subheader-text);
  font-size: 14px;
}

.incident-time {
  color: var(--table-subheader-text);
  font-size: 14px;
}

.incident-description {
  color: var(--table-row-text);
  font-size: 14px;
}

.incident-actions {
  display: flex;
  justify-content: center;
  color: var(--table-header-dots);
  cursor: pointer;
}

.clickable-task-name {
  cursor: pointer;
  color: var(--table-row-text);
  text-decoration: none;
}

.clickable-task-name:hover {
  color: var(--incident-primary);
  text-decoration: underline;
}

/* Status Badge Styles */
.status-badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  min-width: 120px;
}

.status-badge.status-open {
  background-color: #fff3e0;
  color: #ff9800;
  border: 1px solid rgba(255, 152, 0, 0.3);
}

.status-badge.status-assigned {
  background-color: #e3f2fd;
  color: #2196f3;
  border: 1px solid rgba(33, 150, 243, 0.3);
}

.status-badge.status-closed {
  background-color: #e8f5e9;
  color: #4caf50;
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.status-badge.status-rejected {
  background-color: transparent;
  color: #f44336;
  border: 1px solid rgba(244, 67, 54, 0.3);
}

.status-badge.status-escalated {
  background-color: #f3e5f5;
  color: #9c27b0;
  border: 1px solid rgba(156, 39, 176, 0.3);
}

/* Action Button Styles */
.actions-dropdown {
  position: relative;
  display: inline-block;
  z-index: 9999;
}

.actions-button {
  background: linear-gradient(135deg, #7B6FDD 0%, #9B8CEB 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(123, 111, 221, 0.25);
  position: relative;
  animation: actionPulse 2s infinite ease-in-out, buttonBreath 3s infinite ease-in-out;
}

.actions-button:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 20px rgba(123, 111, 221, 0.4);
  background: linear-gradient(135deg, #8F7EE7 0%, #A994F1 100%);
  animation: buttonGlow 1.5s infinite ease-in-out;
}

.actions-button .gear-icon {
  animation: rotateGear 3s linear infinite;
}

.actions-button:hover .gear-icon {
  animation: rotateGear 1s linear infinite;
}

.dropdown-arrow {
  transition: transform 0.2s;
}

.dropdown-arrow.rotate {
  transform: rotate(180deg);
}

.actions-dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  min-width: 180px;
  background: #ffffff !important;
  border: 2px solid #d0d0d0;
  border-radius: 8px;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3), 0 5px 15px rgba(0, 0, 0, 0.2);
  z-index: 999999;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-10px);
  transition: all 0.3s ease;
  margin-top: 8px;
  backdrop-filter: blur(0px);
}

.actions-dropdown-menu.show {
  opacity: 1 !important;
  visibility: visible !important;
  transform: translateY(0) !important;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 500;
  color: #333333 !important;
  text-decoration: none;
  transition: all 0.2s;
  cursor: pointer;
  border: none;
  background: #ffffff !important;
  background-color: #ffffff !important;
  width: 100%;
  text-align: left;
  position: relative;
  z-index: 1000000;
  opacity: 1 !important;
  filter: none !important;
  -webkit-backdrop-filter: none !important;
  backdrop-filter: none !important;
}

.dropdown-item:hover {
  background: #f0f0f0 !important;
  background-color: #f0f0f0 !important;
  color: #7B6FDD !important;
  transform: translateX(2px);
  opacity: 1 !important;
  filter: none !important;
  -webkit-backdrop-filter: none !important;
  backdrop-filter: none !important;
}

.dropdown-item:not(:last-child) {
  border-bottom: 1px solid #f0f0f0;
}

.dropdown-item i {
  width: 16px;
  text-align: center;
  font-size: 14px;
}

/* View Details Button for Processed Items */
.view-details-btn {
  background: transparent !important;
  color: #3b82f6 !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 8px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 0 !important;
  transition: all 0.2s ease !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  white-space: nowrap !important;
  min-width: auto !important;
  width: auto !important;
  height: auto !important;
  box-shadow: none !important;
  margin: 0 auto !important;
  visibility: visible !important;
  opacity: 1 !important;
  z-index: 99999 !important;
  position: relative !important;
}

.view-details-btn:hover {
  background: transparent !important;
  color: #1d4ed8 !important;
  transform: scale(1.1) !important;
  box-shadow: none !important;
}

.view-details-btn i {
  font-size: 18px;
}

/* Actions column styling */
.collapsible-table td:has(.view-details-btn) {
  text-align: center;
  vertical-align: middle;
  padding: 8px;
}

/* Override PolicyApprover.css styles for view-details-btn */
.collapsible-table .view-details-btn,
.collapsible-table-container .view-details-btn,
.task-table .view-details-btn,
td .view-details-btn,
.actions .view-details-btn {
  background: transparent !important;
  color: #3b82f6 !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 8px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 0 !important;
  transition: all 0.2s ease !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  white-space: nowrap !important;
  min-width: auto !important;
  width: auto !important;
  height: auto !important;
  box-shadow: none !important;
  margin: 0 auto !important;
  visibility: visible !important;
  opacity: 1 !important;
  z-index: 99999 !important;
  position: relative !important;
}

.collapsible-table .view-details-btn:hover,
.collapsible-table-container .view-details-btn:hover,
.task-table .view-details-btn:hover,
td .view-details-btn:hover,
.actions .view-details-btn:hover {
  background: transparent !important;
  color: #1d4ed8 !important;
  transform: scale(1.1) !important;
  box-shadow: none !important;
}

/* Edit Button Styles */
.edit-btn {
  background: transparent !important;
  color: #000000 !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 8px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 0 !important;
  transition: all 0.2s ease !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  white-space: nowrap !important;
  min-width: auto !important;
  width: auto !important;
  height: auto !important;
  box-shadow: none !important;
  margin: 0 auto !important;
  visibility: visible !important;
  opacity: 1 !important;
  z-index: 99999 !important;
  position: relative !important;
}

.edit-btn:hover {
  background: transparent !important;
  color: #333333 !important;
  transform: scale(1.1) !important;
  box-shadow: none !important;
}

.edit-btn i {
  font-size: 18px;
  color: inherit !important;
}

/* Override for edit button in various contexts */
.collapsible-table .edit-btn,
.collapsible-table-container .edit-btn,
.task-table .edit-btn,
td .edit-btn,
.actions .edit-btn,
.actions-cell .edit-btn {
  background: transparent !important;
  color: #000000 !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 8px !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 0 !important;
  transition: all 0.2s ease !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  white-space: nowrap !important;
  min-width: auto !important;
  width: auto !important;
  height: auto !important;
  box-shadow: none !important;
  margin: 0 auto !important;
  visibility: visible !important;
  opacity: 1 !important;
  z-index: 99999 !important;
  position: relative !important;
}

.collapsible-table .edit-btn:hover,
.collapsible-table-container .edit-btn:hover,
.task-table .edit-btn:hover,
td .edit-btn:hover,
.actions .edit-btn:hover,
.actions-cell .edit-btn:hover {
  background: transparent !important;
  color: #333333 !important;
  transform: scale(1.1) !important;
  box-shadow: none !important;
}

/* Ensure icon color is properly set in all contexts */
.collapsible-table .edit-btn i,
.collapsible-table-container .edit-btn i,
.task-table .edit-btn i,
td .edit-btn i,
.actions .edit-btn i,
.actions-cell .edit-btn i {
  font-size: 18px !important;
  color: inherit !important;
}

.collapsible-table .edit-btn:hover i,
.collapsible-table-container .edit-btn:hover i,
.task-table .edit-btn:hover i,
td .edit-btn:hover i,
.actions .edit-btn:hover i,
.actions-cell .edit-btn:hover i {
  color: inherit !important;
}

/* Actions cell layout */
.actions-cell {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 12px !important;
}

/* Additional specific selectors for task-table to ensure edit button shows */
.task-table .actions-cell .edit-btn,
.task-table td .actions-cell .edit-btn {
  display: inline-flex !important;
  visibility: visible !important;
  opacity: 1 !important;
  color: #000000 !important;
}

.task-table .actions-cell .edit-btn i,
.task-table td .actions-cell .edit-btn i {
  color: #000000 !important;
  font-size: 18px !important;
  display: inline-block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.task-table .actions-cell .edit-btn:hover,
.task-table td .actions-cell .edit-btn:hover {
  color: #333333 !important;
}

.task-table .actions-cell .edit-btn:hover i,
.task-table td .actions-cell .edit-btn:hover i {
  color: #333333 !important;
}

/* Priority Classes */
.priority-high-priority {
  color: var(--priority-high-text);
}

.priority-normal-priority {
  color: var(--priority-normal-text);
}

.priority-low-priority {
  color: var(--priority-low-text);
}

.priority-none {
  color: var(--priority-none-text);
}

/* Keyframe Animations */
@keyframes actionPulse {
  0%, 100% {
    box-shadow: 0 2px 8px rgba(123, 111, 221, 0.25);
  }
  50% {
    box-shadow: 0 4px 16px rgba(123, 111, 221, 0.4);
  }
}

@keyframes rotateGear {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes buttonBreath {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
}

@keyframes buttonGlow {
  0%, 100% {
    box-shadow: 0 6px 20px rgba(123, 111, 221, 0.4);
  }
  50% {
    box-shadow: 0 8px 30px rgba(123, 111, 221, 0.6);
  }
}

/* Resize handle styles */
.resize-handle {
  position: absolute;
  right: 0;
  top: 0;
  width: 6px;
  height: 100%;
  cursor: col-resize;
  z-index: 10;
  background: transparent;
}
.resize-handle:hover {
  background: #e0e0e0;
}
</style>