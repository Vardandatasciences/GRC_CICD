<!-- 
  AuditReportsView Component
  
  This component displays audit reports for a specific audit in a dedicated screen.
  It replaces the popup modal that was previously used in AuditorDashboard.
  
  Usage: Navigate to /audit-reports/:auditId where auditId is the audit ID
  
  Features:
  - Displays audit information at the top
  - Shows reports in a table format
  - Provides back navigation to dashboard
  - Handles loading, error, and empty states
  - Maintains the same API functionality as the original popup
-->
<template>
  <div class="audit-reports-view-container">
    <!-- Header with back button -->
    <div class="reports-header">
      <button class="back-button" @click="goBack">
        <i class="fas fa-arrow-left"></i>
      </button>
      <h1 class="reports-title">Audit Reports</h1>
    </div>

    <!-- Audit Info -->
    <div class="audit-info-card" v-if="currentAudit">
      <div class="audit-info-header">
        <h2>Audit Information</h2>
      </div>
      <div class="audit-info-content">
        <div class="info-row">
          <span class="info-label">Audit ID:</span>
          <span class="info-value">{{ currentAudit.audit_id }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Framework:</span>
          <span class="info-value">{{ currentAudit.framework }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Policy:</span>
          <span class="info-value">{{ currentAudit.policy }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">SubPolicy:</span>
          <span class="info-value">{{ currentAudit.subpolicy || 'N/A' }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Auditor:</span>
          <span class="info-value">{{ currentAudit.user }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Status:</span>
          <span class="info-value status-value" :class="getStatusClass(currentAudit.status)">
            {{ currentAudit.status }}
          </span>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-message">
      <i class="fas fa-spinner fa-spin"></i> Loading reports...
    </div>

    <!-- Error State -->
    <div v-else-if="reportsError" class="error-message">
      <i class="fas fa-exclamation-circle"></i> {{ reportsError }}
      <button @click="loadReports" class="retry-btn">Retry</button>
    </div>

    <!-- No Reports State -->
    <div v-else-if="processedReports.length === 0" class="no-reports-message">
      <i class="fas fa-folder-open"></i> No reports available for this audit
    </div>

    <!-- Reports Table -->
    <div v-else class="reports-table-container">
      <div class="table-header">
        <h3>Available Reports</h3>
        <span class="report-count">{{ processedReports.length }} report(s) found</span>
      </div>
      
      <div class="table-wrapper">
        <table class="reports-table">
          <thead>
            <tr>
              <th>Report Number</th>
              <th>Report ID</th>
              <th>Audit ID</th>
              <th>Framework</th>
              <th>Policy</th>
              <th>SubPolicy</th>
              <th>Auditor</th>
              <th>Reviewer</th>
              <th>Completion Date</th>
              <th>Document</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(report, index) in processedReports" :key="index">
              <td>{{ report.reportNumber }}</td>
              <td>{{ report.ReportId }}</td>
              <td>{{ report.AuditId }}</td>
              <td>{{ report.Framework || 'N/A' }}</td>
              <td>{{ report.Policy || 'N/A' }}</td>
              <td>{{ report.SubPolicy || 'N/A' }}</td>
              <td>{{ report.Auditor || 'N/A' }}</td>
              <td>{{ report.Reviewer || 'N/A' }}</td>
              <td>{{ report.CompletionDate || 'N/A' }}</td>
              <td class="report-url">
                <span class="file-name" :title="report.Report">
                  {{ getFileName(report.Report) }}
                </span>
              </td>
              <td class="actions-cell">
                <button class="action-btn view" @click="viewReport(report)" title="View Report">
                  <i class="fas fa-eye"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'AuditReportsView',
  data() {
    return {
      loading: false,
      reportsError: null,
      processedReports: [],
      currentAudit: null
    }
  },
  created() {
    // Get audit data from route params or localStorage
    this.loadAuditData();
    this.loadReports();
  },
  methods: {
    loadAuditData() {
      // Try to get audit data from route params first
      const auditId = this.$route.params.auditId;
      
      if (auditId) {
        // Try to get audit data from localStorage (set by dashboard)
        const auditData = localStorage.getItem(`audit_${auditId}_data`);
        if (auditData) {
          this.currentAudit = JSON.parse(auditData);
        } else {
          // Create basic audit info from ID
          this.currentAudit = {
            audit_id: auditId,
            framework: 'Loading...',
            policy: 'Loading...',
            subpolicy: '',
            user: 'Loading...',
            status: 'Loading...'
          };
        }
      }
    },

    async loadReports() {
      if (!this.$route.params.auditId) {
        this.reportsError = 'No audit ID provided';
        return;
      }

      this.loading = true;
      this.reportsError = null;

      try {
        console.log(`Fetching reports for audit ${this.$route.params.auditId}`);

        // Use the same API endpoint as the original popup
        let response;
        try {
          response = await axios.get(`/audit-report/${this.$route.params.auditId}/`);
        } catch (apiError) {
          console.error('Primary API failed, trying fallback:', apiError);
          
          // Fallback: Check if there's a reports field in localStorage
          const auditData = localStorage.getItem(`audit_${this.$route.params.auditId}_data`);
          if (auditData) {
            const audit = JSON.parse(auditData);
            const reportsField = audit.Reports || audit.reports;
            if (reportsField && typeof reportsField === 'string' && reportsField.startsWith('http')) {
              // Create a basic report entry from the URL
              this.processedReports = [{
                reportNumber: 'Report 1',
                ReportId: this.$route.params.auditId,
                AuditId: this.$route.params.auditId,
                PolicyId: null,
                SubPolicyId: null,
                FrameworkId: null,
                Report: reportsField,
                Title: audit.policy || 'N/A',
                Framework: audit.framework || 'N/A',
                Policy: audit.policy || 'N/A',
                SubPolicy: audit.subpolicy || 'N/A',
                Auditor: audit.user || 'N/A',
                Reviewer: audit.reviewer || 'N/A',
                CompletionDate: 'N/A'
              }];
              console.log('Using fallback report data:', this.processedReports);
              return;
            }
          }
          throw apiError; // Re-throw if no fallback data available
        }
        
        if (response.data && response.data.success && response.data.data) {
          const reportData = response.data.data;
          
          // Create a single report entry from the API response
          this.processedReports = [{
            reportNumber: 'Report 1',
            ReportId: reportData.ReportId,
            AuditId: reportData.AuditId,
            PolicyId: reportData.PolicyId,
            SubPolicyId: reportData.SubPolicyId,
            FrameworkId: reportData.FrameworkId,
            Report: reportData.Report,
            Title: reportData.Title || 'N/A',
            Framework: reportData.Framework || 'N/A',
            Policy: reportData.Policy || 'N/A',
            SubPolicy: reportData.SubPolicy || 'N/A',
            Auditor: reportData.Auditor || 'N/A',
            Reviewer: reportData.Reviewer || 'N/A',
            CompletionDate: reportData.CompletionDate || 'N/A'
          }];
          
          console.log('Reports loaded successfully:', this.processedReports);
        } else {
          this.reportsError = 'No reports available for this audit';
          this.processedReports = [];
        }
      } catch (error) {
        console.error('Error fetching reports:', error);
        if (error.response && error.response.status === 404) {
          this.reportsError = 'No reports found for this audit';
        } else {
          this.reportsError = 'Failed to load reports. Please try again.';
        }
        this.processedReports = [];
      } finally {
        this.loading = false;
      }
    },

    getFileName(url) {
      if (!url) return 'N/A';
      try {
        // Extract filename from URL
        const urlParts = url.split('/');
        const fileName = urlParts[urlParts.length - 1];
        // Remove any URL parameters
        return fileName.split('?')[0];
      } catch (error) {
        console.error('Error getting filename:', error);
        return 'N/A';
      }
    },

    viewReport(report) {
      if (report && report.Report) {
        window.open(report.Report, '_blank');
      }
    },

    getStatusClass(status) {
      if (status === 'Yet to Start') return 'status-yet';
      if (status === 'Work In Progress') return 'status-progress';
      if (status === 'Under review') return 'status-review';
      if (status === 'Completed') return 'status-completed';
      return '';
    },

    goBack() {
      this.$router.go(-1); // Go back to previous page
    }
  }
}
</script>

<style scoped>
.audit-reports-view-container {
  margin-left: 280px;
  margin-top: 20px;
  min-height: 100vh;
  max-width: calc(100vw - 180px);
  color: var(--text-primary);
  background: #ffffff;
  box-sizing: border-box;
  overflow-x: hidden;
  font-family: var(--font-family, inherit);
  padding: 16px;
}

.reports-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e2e8f0;
  position: relative;
}

.back-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 14px 13px 13px;
  border-radius: 6px;
  color: #000105;
  box-shadow: none!important;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
  position: absolute;
  left: 0;
  top: 3px;
}
 
.back-button i {
  font-size: 18px;
}
 
.back-button:hover {
  background: transparent;
}
.reports-title {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--form-header-text, var(--card-view-title-color, var(--text-primary)));
  margin-left: -800px;
  letter-spacing: 0.01em;
}

.audit-info-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.audit-info-header h2 {
  margin: 0 0 12px 0;
  color: #2d3748;
  font-size: 1.2rem;
  font-weight: 600;
}

.audit-info-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.info-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  font-weight: 600;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.info-value {
  font-size: 14px;
  color: #2d3748;
  font-weight: 500;
}

.status-value {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  min-width: 100px;
}

.status-value.status-yet {
  background: #e0e7ef;
  color: #334155;
}

.status-value.status-progress {
  background: #e3f0ff;
  color: #1976d2;
}

.status-value.status-review {
  background: #fff4e5;
  color: #b26a00;
}

.status-value.status-completed {
  background: #e6f9ec;
  color: #1aaf5d;
}

.reports-table-container {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f7fafc;
  border-bottom: 1px solid #e2e8f0;
}

.table-header h3 {
  margin: 0;
  color: #2d3748;
  font-size: 1.1rem;
  font-weight: 600;
}

.report-count {
  color: #718096;
  font-size: 12px;
  font-weight: 500;
}

.table-wrapper {
  overflow-x: auto;
}

.reports-table {
  width: 100%;
  border-collapse: collapse;
}

.reports-table th,
.reports-table td {
  padding: 10px 8px;
  text-align: left;
  border-bottom: 1px solid #f1f5f9;
  font-size: 12px;
}

.reports-table th {
  background: #f8fafc;
  font-weight: 600;
  color: #4a5568;
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 1;
  font-size: 11px;
}

.reports-table tbody tr:hover {
  background: #f8fafc;
}

.report-url {
  max-width: 200px;
  overflow: hidden;
}

.file-name {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #4299e1;
  cursor: pointer;
}

.actions-cell {
  white-space: nowrap;
}

.action-btn {
  padding: 6px 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 12px;
}

.action-btn.view {
  background: #ebf8ff;
  color: #4299e1;
}

.action-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.action-btn.view:hover {
  background: #bee3f8;
}

.loading-message,
.error-message,
.no-reports-message {
  text-align: center;
  padding: 40px;
  color: #718096;
  font-size: 16px;
}

.error-message {
  color: #e53e3e;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.loading-message {
  color: #4299e1;
}

.no-reports-message {
  color: #718096;
}

.retry-btn {
  background: #e53e3e;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.retry-btn:hover {
  background: #c53030;
}

.loading-message i,
.error-message i,
.no-reports-message i {
  margin-right: 8px;
}

/* Responsive styles */
@media screen and (max-width: 1200px) {
  .audit-reports-view-container {
    margin-left: 0;
    padding: 12px;
  }
  
  .audit-info-content {
    grid-template-columns: 1fr;
  }
  
  .reports-table th,
  .reports-table td {
    padding: 8px 6px;
    font-size: 11px;
  }
}

@media screen and (max-width: 768px) {
  .reports-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .reports-title {
    font-size: 1.5rem;
  }
  
  .table-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
}
</style>
