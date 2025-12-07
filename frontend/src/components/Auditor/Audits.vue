<template>
  <div class="audits-container">
    <div class="audits-header">
      <h1>Audits</h1>
    </div>
    
    <!-- Error message at the top level -->
    <div v-if="error" class="error-message">
      {{ error }}
      <button @click="retryLoading" class="retry-btn">Retry</button>
    </div>

    <!-- Search bar only -->
    <div class="search-container">
      <div class="audits-search">
        <input type="text" placeholder="Search" v-model="searchQuery" @input="handleSearch" />
      </div>
      
      <!-- View Toggle Buttons -->
      <div class="view-toggle">
        <button 
          :class="['view-btn', { active: viewMode === 'list' }]" 
          @click="viewMode = 'list'"
        >
          <i class="fas fa-list"></i> List
        </button>
        <button 
          :class="['view-btn', { active: viewMode === 'card' }]" 
          @click="viewMode = 'card'"
        >
          <i class="fas fa-th-large"></i> Card
        </button>
      </div>
      
      <!-- Active Filters Display -->
      <div v-if="Object.keys(activeFilters).length > 0" class="active-filters">
        <span>Active Filters: </span>
        <span 
          v-for="(value, column) in activeFilters" 
          :key="column" 
          class="filter-badge"
        >
          {{ column }}: {{ value }}
          <span class="remove-filter" @click="applyFilter(column, '')">×</span>
        </span>
      </div>
    </div>

    <!-- Loading indicator -->
    <div v-if="loading" class="loading-indicator">
      Loading data, please wait...
    </div>

    <!-- Table View -->
    <div v-else-if="viewMode === 'list'" class="audits-table-wrapper">
      <table class="audits-table">
        <thead>
          <tr>
            <th>
              Frame work
              <span class="sort-icon" @click="toggleSortDropdown('framework')">▼</span>
            </th>
            <th>
              Policy
              <span class="sort-icon" @click="toggleSortDropdown('policy')">▼</span>
            </th>
            <th>
              Subpolicy
              <span class="sort-icon" @click="toggleSortDropdown('subpolicy')">▼</span>
            </th>
            <th>
              Auditor
              <span class="sort-icon" @click="toggleSortDropdown('auditor')">▼</span>
            </th>
            <th>
              Duedate
              <span class="sort-icon" @click="toggleSortDropdown('duedate')">▼</span>
            </th>
            <th>
              Frequency
              <span class="sort-icon" @click="toggleSortDropdown('frequency')">▼</span>
            </th>
            <th>
              Review
              <span class="sort-icon" @click="toggleSortDropdown('reviewer')">▼</span>
            </th>
            <th>
              Audit Type
              <span class="sort-icon" @click="toggleSortDropdown('audit_type')">▼</span>
            </th>
            <th>
              Status
              <span class="sort-icon" @click="toggleSortDropdown('status')">▼</span>
            </th>
            <th>
              Report
              <span class="sort-icon" @click="toggleSortDropdown('report')">▼</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="(row, idx) in filteredAuditData" 
            :key="idx"
            @click="row && row.audit_id ? viewAuditDetails(row.audit_id) : null"
            class="audit-row"
          >
            <td :title="row && row.framework || '-'">{{ formatCellText(row && row.framework || '-') }}</td>
            <td :title="row && row.policy || '-'">{{ formatCellText(row && row.policy || '-') }}</td>
            <td :title="row && row.subpolicy || '-'">{{ formatCellText(row && row.subpolicy || '-') }}</td>
            <td :title="row && row.auditor || '-'">{{ formatCellText(row && row.auditor || '-') }}</td>
            <td :title="row && row.duedate || '-'">{{ formatCellText(row && row.duedate || '-') }}</td>
            <td :title="row && row.frequency || '-'">{{ formatCellText(row && row.frequency || '-') }}</td>
            <td :title="row && row.reviewer || '-'">{{ formatCellText(row && row.reviewer || '-') }}</td>
            <td :title="row && row.audit_type || '-'">{{ formatCellText(row && row.audit_type || '-') }}</td>
            <td @click.stop>
              <div class="status-dropdown-container">
                <span 
                  :class="getStatusClass(row && row.status)"
                  class="status-badge status-clickable"
                  @click.stop="openStatusDropdown($event, idx)"
                >
                  {{ row && row.status || '-' }}
                  <i class="fas fa-chevron-down status-dropdown-icon"></i>
                </span>
                <div v-if="openStatusIdx === idx" class="status-options">
                  <div class="status-option" @click.stop="changeStatus($event, row, 'Completed')">
                    <span class="status-dot completed"></span> Completed
                  </div>
                  <div class="status-option" @click.stop="changeStatus($event, row, 'Work in Progress')">
                    <span class="status-dot progress"></span> Work in Progress
                  </div>
                  <div class="status-option" @click.stop="changeStatus($event, row, 'Yet to Start')">
                    <span class="status-dot start"></span> Yet to Start
                  </div>
                </div>
              </div>
            </td>
            <td :title="row && row.report || '-'">{{ formatCellText(row && row.report || '-') }}</td>
          </tr>
          <tr v-if="!filteredAuditData || filteredAuditData.length === 0">
            <td colspan="10" class="no-data">No audit data available</td>
          </tr>
          <tr v-else-if="filteredAuditData.length < 6" v-for="n in 6 - filteredAuditData.length" :key="'empty-' + n">
            <td v-for="i in 10" :key="i"></td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Card View -->
    <div v-else class="audits-card-wrapper">
      <div v-if="!filteredAuditData || filteredAuditData.length === 0" class="no-data">
        No audit data available
      </div>
      <div v-else class="audits-card-grid">
        <div 
          v-for="(row, idx) in filteredAuditData" 
          :key="idx" 
          class="audit-card"
          @click="row && row.audit_id ? viewAuditDetails(row.audit_id) : null"
        >
          <div class="card-header">
            <div class="card-framework">{{ formatCellText(row && row.framework || '-') }}</div>
            <div class="status-dropdown-container" @click.stop>
              <div 
                :class="getStatusClass(row && row.status)"
                class="status-badge status-clickable"
                @click.stop="openStatusDropdown($event, 'card-'+idx)"
              >
                {{ row && row.status || '-' }}
                <i class="fas fa-chevron-down status-dropdown-icon"></i>
              </div>
              <div v-if="openStatusIdx === 'card-'+idx" class="status-options">
                <div class="status-option" @click.stop="changeStatus($event, row, 'Completed')">
                  <span class="status-dot completed"></span> Completed
                </div>
                <div class="status-option" @click.stop="changeStatus($event, row, 'Work in Progress')">
                  <span class="status-dot progress"></span> Work in Progress
                </div>
                <div class="status-option" @click.stop="changeStatus($event, row, 'Yet to Start')">
                  <span class="status-dot start"></span> Yet to Start
                </div>
              </div>
            </div>
          </div>
          
          <div class="card-body">
            <div class="card-info-row">
              <div class="card-info-icon">📄</div>
              <div class="card-info-label">Policy:</div>
              <div class="card-info-value">{{ formatCellText(row && row.policy || '-') }}</div>
            </div>
            
            <div class="card-info-row">
              <div class="card-info-icon">📝</div>
              <div class="card-info-label">Subpolicy:</div>
              <div class="card-info-value">{{ formatCellText(row && row.subpolicy || '-') }}</div>
            </div>
            
            <div class="card-info-row">
              <div class="card-info-icon">👤</div>
              <div class="card-info-label">Auditor:</div>
              <div class="card-info-value">{{ formatCellText(row && row.auditor || '-') }}</div>
            </div>
            
            <div class="card-info-row">
              <div class="card-info-icon">📅</div>
              <div class="card-info-label">Due Date:</div>
              <div class="card-info-value">{{ formatCellText(row && row.duedate || '-') }}</div>
            </div>
            
            <div class="card-info-row">
              <div class="card-info-icon">🔄</div>
              <div class="card-info-label">Frequency:</div>
              <div class="card-info-value">{{ formatCellText(row && row.frequency || '-') }}</div>
            </div>
            
            <div class="card-info-row">
              <div class="card-info-icon">👁️</div>
              <div class="card-info-label">Reviewer:</div>
              <div class="card-info-value">{{ formatCellText(row && row.reviewer || '-') }}</div>
            </div>
          </div>
          
          <div class="card-footer">
            <div class="card-audit-type">
              <span>🏷️ {{ formatCellText(row && row.audit_type || '-') }}</span>
            </div>
            <div class="card-report">
              <span>📊 {{ row && row.report ? 'Report Available' : 'No Report' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Sort Dropdown (Positioned absolutely) -->
    <div v-if="activeDropdown" class="sort-dropdown-overlay">
      <div class="dropdown-content">
        <div class="dropdown-header">
          <span>Filter by {{ activeDropdown }}</span>
          <span class="close-dropdown" @click="activeDropdown = null">×</span>
        </div>
        <div class="dropdown-item" @click="applyFilter(activeDropdown, '')">Show All</div>
        <div 
          v-for="value in getUniqueValues(activeDropdown)" 
          :key="value" 
          class="dropdown-item" 
          @click="applyFilter(activeDropdown, value)"
        >
          {{ value }}
        </div>
      </div>
    </div>
    
    <!-- Audit Details Modal -->
    <div v-if="showAuditDetails && currentAudit" class="audits-modal">
      <div class="audits-modal-content audit-details-modal">
        <div class="modal-header">
          <h2>Audit Details</h2>
          <button type="button" class="close-btn" @click="closeAuditDetails">&times;</button>
        </div>
        
        <div v-if="loadingAuditDetails" class="loading-indicator">
          Loading audit details...
        </div>
        
        <div v-else-if="currentAudit" class="audit-details-content">
          <div class="audit-info">
            <div class="info-item">
              <strong>Framework:</strong> {{ currentAudit.framework || 'N/A' }}
            </div>
            <div class="info-item">
              <strong>Policy:</strong> {{ currentAudit.policy || 'N/A' }}
            </div>
            <div class="info-item">
              <strong>Subpolicy:</strong> {{ currentAudit.subpolicy || 'N/A' }}
            </div>
            <div class="info-item">
              <strong>Auditor:</strong> {{ currentAudit.auditor || 'N/A' }}
            </div>
            <div class="info-item">
              <strong>Assignee:</strong> {{ currentAudit.assignee || 'N/A' }}
            </div>
            <div class="info-item">
              <strong>Reviewer:</strong> {{ currentAudit.reviewer || 'N/A' }}
            </div>
            <div class="info-item">
              <strong>Due Date:</strong> {{ currentAudit.duedate || 'N/A' }}
            </div>
            <div class="info-item">
              <strong>Status:</strong> {{ currentAudit.status || 'N/A' }}
            </div>
            <div class="info-item">
              <strong>Completion:</strong> {{ currentAudit.completed_compliances || 0 }}/{{ currentAudit.total_compliances || 0 }}
            </div>
          </div>
          
          <div v-if="currentAudit.compliance_items && currentAudit.compliance_items.length > 0" class="compliance-items">
            <h3>Compliance Items</h3>
            <table class="compliance-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Description</th>
                  <th>Criticality</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in currentAudit.compliance_items" :key="item.ComplianceId">
                  <td>{{ item.ComplianceId }}</td>
                  <td>{{ item.ComplianceItemDescription }}</td>
                  <td>{{ formatCriticality(item.Criticality) }}</td>
                  <td>{{ item.status_text }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="no-compliance-items">
            <p>No compliance items found for this audit.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '../../data/api';
import auditorDataService from '@/services/auditorService'; // NEW: Use cached auditor data
import { AccessUtils } from '@/utils/accessUtils';

export default {
  name: 'AuditsView',
  data() {
    return {
      searchQuery: '',
      auditData: [],
      filteredAuditData: [],
      error: '',
      loading: true,
      showAuditDetails: false,
      currentAudit: null,
      loadingAuditDetails: false,
      activeDropdown: null,
      activeFilters: {},
      viewMode: 'list',
      openStatusIdx: null,
    };
  },
  mounted() {
    console.log("Audits component mounted, fetching data...");
    this.fetchAuditData();
    
    // Add click event listener to close dropdowns when clicking outside
    document.addEventListener('click', this.closeDropdownOnClickOutside);
  },
  beforeUnmount() {
    // Remove event listener when component is destroyed
    document.removeEventListener('click', this.closeDropdownOnClickOutside);
  },
  methods: {
    retryLoading() {
      this.fetchAuditData();
    },
    async fetchAuditData() {
      console.log('🔍 [Audits] Checking for cached audits data...');
      this.loading = true;
      this.error = '';
      
      // Check if prefetch was never started (user came directly to this page)
      if (!window.auditorDataFetchPromise && !auditorDataService.hasAuditsCache()) {
        console.log('🚀 [Audits] Starting prefetch now (user came directly to this page)...');
        window.auditorDataFetchPromise = auditorDataService.fetchAllAuditorData();
      }
      
      // Wait for prefetch if it's running
      if (window.auditorDataFetchPromise) {
        console.log('⏳ [Audits] Waiting for prefetch to complete...');
        try {
          await window.auditorDataFetchPromise;
          console.log('✅ [Audits] Prefetch completed');
        } catch (error) {
          console.warn('⚠️ [Audits] Prefetch failed, will fetch directly');
        }
      }
      
      // Try to get data from cache first
      if (auditorDataService.hasAuditsCache()) {
        console.log('✅ [Audits] Using cached audits data');
        const cachedAudits = auditorDataService.getData('audits') || [];
        console.log(`[Audits] Loaded ${cachedAudits.length} audits from cache (prefetched on Home page)`);
        
        if (Array.isArray(cachedAudits)) {
          this.auditData = cachedAudits;
          this.filteredAuditData = cachedAudits;
        } else {
          this.auditData = [];
          this.filteredAuditData = [];
        }
        this.loading = false;
      } else {
        // Fallback: Fetch from API if cache is empty
        console.log('⚠️ [Audits] No cached data found, fetching from API...');
      api.getAllAudits()
        .then(res => {
            console.log("Audit data received from API:", res.data);
          if (Array.isArray(res.data)) {
            this.auditData = res.data;
            this.filteredAuditData = res.data;
              // Update cache
              auditorDataService.setData('audits', res.data);
              console.log('ℹ️ [Audits] Cache updated after direct API fetch');
          } else {
            console.warn("Received non-array audit data:", res.data);
            this.auditData = [];
            this.filteredAuditData = [];
          }
          this.loading = false;
        })
        .catch(err => {
          console.error("Error fetching audit data:", err);
          // Handle access denied errors
          if (AccessUtils.handleApiError(err, 'audit data access')) {
            this.error = 'Access denied';
          } else {
            this.error = `Failed to load data: ${err.message || err}`;
          }
          this.auditData = [];
          this.filteredAuditData = [];
          this.loading = false;
        });
      }
    },
    handleSearch() {
      this.applyFilters();
    },
    toggleSortDropdown(column) {
      // If clicking on the same dropdown, close it
      if (this.activeDropdown === column) {
        this.activeDropdown = null;
      } else {
        this.activeDropdown = column;
      }
    },
    closeDropdownOnClickOutside(event) {
      // Don't close if clicking inside a dropdown
      if (event.target.closest('.sort-dropdown') || event.target.closest('.sort-icon')) {
        return;
      }
      this.activeDropdown = null;
    },
    getUniqueValues(column) {
      if (!Array.isArray(this.auditData)) return [];
      
      return [...new Set(
        this.auditData
          .map(item => item[column])
          .filter(Boolean) // Remove null/undefined
      )].sort();
    },
    applyFilter(column, value) {
      if (value === '') {
        // Remove filter for this column
        if (this.activeFilters[column]) {
          delete this.activeFilters[column];
        }
      } else {
        // Add or update filter for this column
        this.activeFilters[column] = value;
      }
      
      // Close the dropdown
      this.activeDropdown = null;
      
      // Apply all filters
      this.applyFilters();
    },
    applyFilters() {
      if (!Array.isArray(this.auditData)) {
        this.filteredAuditData = [];
        return;
      }
      
      // First apply search query
      const query = this.searchQuery.toLowerCase();
      let filtered = this.auditData;
      
      if (query) {
        filtered = filtered.filter(audit =>
          (audit.framework && audit.framework.toLowerCase().includes(query)) ||
          (audit.policy && audit.policy.toLowerCase().includes(query)) ||
          (audit.subpolicy && audit.subpolicy.toLowerCase().includes(query)) ||
          (audit.auditor && audit.auditor.toLowerCase().includes(query)) ||
          (audit.status && audit.status.toLowerCase().includes(query))
        );
      }
      
      // Then apply column filters
      for (const [column, value] of Object.entries(this.activeFilters)) {
        filtered = filtered.filter(item => item[column] === value);
      }
      
      this.filteredAuditData = filtered;
    },
    viewAuditDetails(auditId) {
      if (!auditId) {
        this.error = 'Invalid audit ID';
        return;
      }
      
      this.loadingAuditDetails = true;
      this.currentAudit = null;
      this.showAuditDetails = true;
      
      console.log("Fetching audit details for ID:", auditId);
      api.getAuditDetails(auditId)
        .then(response => {
          console.log("Audit details received:", response.data);
          this.currentAudit = response.data;
          this.loadingAuditDetails = false;
        })
        .catch(err => {
          console.error("Error fetching audit details:", err);
          // Handle access denied errors
          if (AccessUtils.handleApiError(err, 'audit details access')) {
            this.error = 'Access denied';
          } else {
            this.error = err.response?.data?.error || `Failed to load audit details: ${err.message || err}`;
          }
          this.loadingAuditDetails = false;
          this.showAuditDetails = false;
        });
    },
    closeAuditDetails() {
      this.showAuditDetails = false;
      this.currentAudit = null;
    },
    formatCriticality(value) {
      // Handle numeric criticality values
      if (value === 0 || value === '0') return 'Minor';
      if (value === 1 || value === '1') return 'Major'; 
      if (value === 2 || value === '2') return 'Not Applicable';
      
      // If it's already a string value, return as is
      if (typeof value === 'string' && isNaN(parseInt(value))) return value;
      
      // Default fallback
      return 'Not Specified';
    },
    getStatusClass(status) {
      // Implement your logic to determine the status class based on the status
      if (!status) return '';
      
      if (status.toLowerCase().includes('complete')) {
        return 'status-completed';
      } else if (status.toLowerCase().includes('progress')) {
        return 'status-progress';
      } else if (status.toLowerCase().includes('pending')) {
        return 'status-pending';
      } else if (status.toLowerCase().includes('start')) {
        return 'status-start';
      }
      
      return '';
    },
    formatCellText(text) {
      if (typeof text !== 'string') return text;
      
      // For very long text, cut it to avoid overflow issues
      if (text.length > 25) {
        return text.substring(0, 23) + '...';
      }
      
      return text;
    },
    openStatusDropdown(event, idx) {
      event.stopPropagation(); // Prevent row click event
      this.openStatusIdx = this.openStatusIdx === idx ? null : idx;
    },
    changeStatus(event, audit, newStatus) {
      event.stopPropagation(); // Prevent row click event
      
      if (!audit || !audit.audit_id) {
        this.error = 'Cannot update status: Invalid audit';
        return;
      }
      
      this.loading = true;
      this.error = '';
      
      // Call API to update status
      api.updateAuditStatus(audit.audit_id, newStatus)
        .then(response => {
          console.log("Status updated successfully:", response.data);
          // Update local data
          audit.status = newStatus;
          this.loading = false;
          this.openStatusIdx = null; // Close dropdown
        })
        .catch(err => {
          console.error("Error updating audit status:", err);
          this.error = `Failed to update status: ${err.message || err}`;
          this.loading = false;
        });
    },
  }
};
</script>

<style scoped>
@import './Audits.css';
</style> 