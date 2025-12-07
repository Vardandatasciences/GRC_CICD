<template>
  <div class="audit-report-view-container">
    <div class="action-bar">
      <div class="action-buttons">
        <button class="btn btn-outline" @click="goBack">
          <i class="fas fa-arrow-left"></i>
          Back
        </button>
        <button class="btn btn-primary" @click="downloadReport" :disabled="downloading">
          <i class="fas fa-download" :class="{ 'fa-spin': downloading }"></i>
          {{ downloading ? 'Downloading...' : 'Download Report' }}
        </button>
      </div>
    </div>
    
    <h1 class="report-title">Audit Report - ID {{ auditId }}</h1>

    <!-- Error Message -->
    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-circle"></i>
      <span>{{ error }}</span>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-spinner">
      <i class="fas fa-circle-notch fa-spin"></i>
      <span>Loading audit report...</span>
    </div>

    <!-- Report Content -->
    <div v-else-if="reportData" class="report-content">
      <!-- Audit Information Section -->
      <div class="report-section">
        <h2>Audit Information</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">Title:</span>
            <span class="info-value">{{ reportData.Title || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Framework:</span>
            <span class="info-value">{{ reportData.Framework || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Policy:</span>
            <span class="info-value">{{ reportData.Policy || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Sub-Policy:</span>
            <span class="info-value">{{ reportData.SubPolicy || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Business Unit:</span>
            <span class="info-value">{{ reportData.BusinessUnit || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Auditor:</span>
            <span class="info-value">{{ reportData.Auditor || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Reviewer:</span>
            <span class="info-value">{{ reportData.Reviewer || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Completion Date:</span>
            <span class="info-value">{{ formatDate(reportData.CompletionDate) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Review Date:</span>
            <span class="info-value">{{ formatDate(reportData.ReviewDate) }}</span>
          </div>
        </div>
      </div>

      <!-- Audit Scope and Objective -->
      <div class="report-section">
        <h2>Audit Scope & Objective</h2>
        <div class="content-block">
          <h3>Scope</h3>
          <p>{{ reportData.Scope || 'No scope provided' }}</p>
        </div>
        <div class="content-block">
          <h3>Objective</h3>
          <p>{{ reportData.Objective || 'No objective provided' }}</p>
        </div>
      </div>

      <!-- Report Content -->
      <div class="report-section">
        <h2>Report Details</h2>
        <div v-if="isS3Url(reportData.Report)" class="s3-download-section">
          <p class="s3-info">Report is stored in cloud storage. Click below to download:</p>
          <a :href="reportData.Report" target="_blank" class="s3-download-link">
            <i class="fas fa-cloud-download-alt"></i>
            Download Report Document
          </a>
          <p class="s3-url">{{ reportData.Report }}</p>
        </div>
        <div v-else class="report-text" v-html="formatReportContent(reportData.Report)"></div>
      </div>

      <!-- Evidence Section -->
      <div v-if="reportData.AuditEvidence" class="report-section">
        <h2>Audit Evidence</h2>
        <div class="content-block">
          <p>{{ reportData.AuditEvidence }}</p>
        </div>
      </div>

      <!-- Comments Section -->
      <div class="report-section">
        <h2>Comments</h2>
        <div v-if="reportData.OverallAuditComments" class="content-block">
          <h3>Audit Comments</h3>
          <p>{{ reportData.OverallAuditComments }}</p>
        </div>
        <div v-if="reportData.OverallReviewComments" class="content-block">
          <h3>Review Comments</h3>
          <p>{{ reportData.OverallReviewComments }}</p>
        </div>
        <div v-if="!reportData.OverallAuditComments && !reportData.OverallReviewComments" class="content-block">
          <p class="no-data">No comments available</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { API_ENDPOINTS } from '../../config/api.js'

const route = useRoute()
const router = useRouter()

// Get route parameters
const auditId = ref(route.params.id)

// State
const reportData = ref(null)
const loading = ref(false)
const error = ref(null)
const downloading = ref(false)

// Fetch report data on component mount
onMounted(async () => {
  await fetchReportData()
})

// Methods
async function fetchReportData() {
  try {
    loading.value = true
    error.value = null
    
          const response = await axios.get(API_ENDPOINTS.AUDIT_REPORT(auditId.value))
    
    if (response.data && response.data.success) {
      reportData.value = response.data.data
    } else {
      throw new Error(response.data.message || 'Failed to fetch audit report')
    }
  } catch (err) {
    console.error('Error fetching audit report:', err)
    error.value = err.response?.data?.message || 'Failed to fetch audit report. Please try again.'
  } finally {
    loading.value = false
  }
}

function formatDate(dateString) {
  if (!dateString) return 'N/A'
  try {
    return new Date(dateString).toLocaleString()
  } catch {
    return dateString
  }
}

function formatReportContent(content) {
  if (!content) return 'No report content available'
  
  // Convert line breaks to HTML breaks and preserve formatting
  return content
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>')
}

function isS3Url(content) {
  if (!content) return false
  // Check if content is an S3 URL or similar cloud storage URL
  return content.includes('s3.') || content.includes('.amazonaws.com') || 
         content.startsWith('https://') && (content.includes('.s3') || content.includes('storage'))
}

function goBack() {
  router.back()
}

async function downloadReport() {
  try {
    downloading.value = true
    
    const response = await axios({
      url: `/generate-audit-report/${auditId.value}/`,
      method: 'GET',
      responseType: 'blob',
      timeout: 30000
    })

    // Create blob and download
    const blob = new Blob([response.data], { 
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' 
    })
    
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `audit_report_${auditId.value}.docx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
    
    ElMessage({
      message: 'Report downloaded successfully',
      type: 'success',
      duration: 3000
    })
  } catch (error) {
    console.error('Download error:', error)
    ElMessage({
      message: 'Failed to download report. Please try again.',
      type: 'error',
      duration: 5000
    })
  } finally {
    downloading.value = false
  }
}
</script>

<style scoped>
.audit-report-view-container {
  padding: 20px;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  margin-left: 280px;
  position: relative;
}

.action-bar {
  position: absolute;
  top: 24px;
  right: 40px;
  z-index: 10;
}

.action-buttons {
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 40px;
  white-space: nowrap;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: 1px solid #2563eb;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

.btn-outline {
  background: #ffffff;
  color: #64748b;
  border: 1px solid #d1d5db;
}

.btn-outline:hover {
  background: #f8fafc;
  color: #334155;
  border-color: #94a3b8;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(100, 116, 139, 0.15);
}

.report-title {
  color: #2c3e50;
  margin-bottom: 30px;
  font-weight: 600;
  margin-top: 60px;
}

.error-message {
  background-color: #fee2e2;
  border: 1px solid #ef4444;
  color: #b91c1c;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.loading-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #4b5563;
  margin: 40px 0;
  font-size: 16px;
}

.report-content {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.report-section {
  padding: 24px;
  border-bottom: 1px solid #e5e7eb;
}

.report-section:last-child {
  border-bottom: none;
}

.report-section h2 {
  color: #1f2937;
  margin-bottom: 20px;
  font-size: 1.5rem;
  font-weight: 600;
  border-bottom: 2px solid #3b82f6;
  padding-bottom: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  min-height: 80px;
}

.info-label {
  font-weight: 600;
  color: #4b5563;
  font-size: 0.875rem;
  margin-bottom: 4px;
}

.info-value {
  color: #1f2937;
  font-size: 1rem;
  line-height: 1.5;
  word-wrap: break-word;
  overflow-wrap: break-word;
  hyphens: auto;
  max-width: 100%;
}

.content-block {
  margin-bottom: 20px;
}

.content-block:last-child {
  margin-bottom: 0;
}

.content-block h3 {
  color: #374151;
  margin-bottom: 8px;
  font-size: 1.125rem;
  font-weight: 600;
}

.content-block p {
  color: #4b5563;
  line-height: 1.6;
  margin: 0;
}

.report-text {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  color: #374151;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.report-text p {
  margin-bottom: 12px;
}

.report-text p:last-child {
  margin-bottom: 0;
}

.no-data {
  color: #9ca3af;
  font-style: italic;
}

.s3-download-section {
  background: #f0f9ff;
  border: 2px solid #3b82f6;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
}

.s3-info {
  color: #1e40af;
  font-weight: 500;
  margin-bottom: 16px;
  font-size: 1.1rem;
}

.s3-download-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  font-size: 1.1rem;
  transition: all 0.2s ease;
  box-shadow: 0 4px 6px rgba(59, 130, 246, 0.25);
  margin-bottom: 16px;
}

.s3-download-link:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(59, 130, 246, 0.4);
  color: white;
  text-decoration: none;
}

.s3-download-link i {
  font-size: 1.2rem;
}

.s3-url {
  color: #64748b;
  font-size: 0.875rem;
  font-family: monospace;
  background: #f8fafc;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  margin-top: 12px;
  word-break: break-all;
}

/* Responsive Design */
@media (max-width: 768px) {
  .audit-report-view-container {
    margin-left: 0;
    padding: 16px;
  }
  
  .action-bar {
    position: relative;
    top: 0;
    right: 0;
    margin-bottom: 20px;
  }
  
  .action-buttons {
    justify-content: flex-end;
  }
  
  .report-title {
    margin-top: 0;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .info-item {
    min-height: auto;
    padding: 12px;
  }
  
  .report-section {
    padding: 16px;
  }
}

/* Additional styles for long text content */
.info-value {
  /* Ensure long text doesn't break layout */
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

/* Show full text on hover for truncated content */
.info-item:hover .info-value {
  overflow: visible;
  text-overflow: clip;
  display: block;
  position: relative;
  z-index: 10;
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  padding: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-top: 4px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.fa-spin {
  animation: spin 1s linear infinite;
}
</style> 