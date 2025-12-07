<template>
  <div class="audit-finding-details-container">
    <div class="action-bar">
      <div class="action-buttons">
        <button class="btn btn-outline" @click="goBack">
          <i class="fas fa-arrow-left"></i>
          Back
        </button>
      </div>
    </div>
    
    <h1 class="finding-title">Audit Finding Details - ID {{ auditFindingId }}</h1>

    <!-- Error Message -->
    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-circle"></i>
      <span>{{ error }}</span>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-spinner">
      <i class="fas fa-circle-notch fa-spin"></i>
      <span>Loading audit finding details...</span>
    </div>

    <!-- Finding Content -->
    <div v-else-if="findingData" class="finding-content">
      
      <!-- Basic Information Section -->
      <div class="finding-section">
        <h2>Finding Information</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">Finding ID:</span>
            <span class="info-value">{{ findingData.AuditFindingsId }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Audit ID:</span>
            <span class="info-value">
              <a href="#" class="audit-link" @click.prevent="viewAuditReport(findingData.AuditId)">
                {{ findingData.AuditId }}
              </a>
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">Compliance ID:</span>
            <span class="info-value">{{ findingData.ComplianceId }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Auditor:</span>
            <span class="info-value">{{ findingData.AuditorName || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Status:</span>
            <span class="info-value" :class="getStatusClass(findingData.CheckStatus)">
              <i :class="getStatusIcon(findingData.CheckStatus)"></i>
              {{ findingData.CheckStatus }}
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">Severity:</span>
            <span class="info-value" :class="getSeverityClass(findingData.MajorMinorStatus)">
              {{ findingData.MajorMinorStatus }}
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">Criticality:</span>
            <span class="info-value" :class="getCriticalityClass(findingData.Criticality)">
              {{ findingData.Criticality || 'N/A' }}
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">Assigned Date:</span>
            <span class="info-value">{{ formatDate(findingData.AssignedDate) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Checked Date:</span>
            <span class="info-value">{{ formatDate(findingData.CheckedDate) }}</span>
          </div>
        </div>
      </div>

      <!-- Audit Context -->
      <div class="finding-section">
        <h2>Audit Context</h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">Audit Title:</span>
            <span class="info-value">{{ findingData.AuditTitle || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Framework:</span>
            <span class="info-value">{{ findingData.FrameworkName || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Policy:</span>
            <span class="info-value">{{ findingData.PolicyName || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Sub-Policy:</span>
            <span class="info-value">{{ findingData.SubPolicyName || 'N/A' }}</span>
          </div>
        </div>
        
        <div class="content-block">
          <h3>Audit Scope</h3>
          <p>{{ findingData.AuditScope || 'No scope provided' }}</p>
        </div>
        
        <div class="content-block">
          <h3>Audit Objective</h3>
          <p>{{ findingData.AuditObjective || 'No objective provided' }}</p>
        </div>
      </div>

      <!-- Compliance Information -->
      <div class="finding-section">
        <h2>Compliance Information</h2>
        <div class="content-block">
          <h3>Compliance Title</h3>
          <p>{{ findingData.ComplianceTitle || 'N/A' }}</p>
        </div>
        
        <div class="content-block">
          <h3>Compliance Description</h3>
          <p>{{ findingData.ComplianceItemDescription || 'No description available' }}</p>
        </div>
        
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">Mandatory/Optional:</span>
            <span class="info-value">{{ findingData.MandatoryOptional || 'N/A' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Is Risk:</span>
            <span class="info-value">{{ findingData.IsRisk ? 'Yes' : 'No' }}</span>
          </div>
        </div>
        
        <div v-if="findingData.Mitigation" class="content-block">
          <h3>Mitigation</h3>
          <p>{{ findingData.Mitigation }}</p>
        </div>
      </div>

      <!-- Finding Details -->
      <div class="finding-section">
        <h2>Finding Details</h2>
        
        <div v-if="findingData.DetailsOfFinding" class="content-block">
          <h3>Details of Finding</h3>
          <p>{{ findingData.DetailsOfFinding }}</p>
        </div>
        
        <div v-if="findingData.Impact" class="content-block">
          <h3>Impact</h3>
          <p>{{ findingData.Impact }}</p>
        </div>
        
        <div v-if="findingData.Recommendation" class="content-block">
          <h3>Recommendation</h3>
          <p>{{ findingData.Recommendation }}</p>
        </div>
        
        <div v-if="findingData.HowToVerify" class="content-block">
          <h3>How to Verify</h3>
          <p>{{ findingData.HowToVerify }}</p>
        </div>
        
        <div v-if="findingData.Comments" class="content-block">
          <h3>Comments</h3>
          <p>{{ findingData.Comments }}</p>
        </div>
        
        <div v-if="findingData.Evidence" class="content-block">
          <h3>Evidence</h3>
          <div class="evidence-content">
            <p>{{ findingData.Evidence }}</p>
          </div>
        </div>
        
        <div v-if="!findingData.DetailsOfFinding && !findingData.Impact && !findingData.Recommendation && !findingData.HowToVerify && !findingData.Comments && !findingData.Evidence" class="content-block">
          <p class="no-data">No additional finding details available</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { API_ENDPOINTS } from '../../config/api.js'

const route = useRoute()
const router = useRouter()

// Get route parameters
const auditFindingId = ref(route.params.id)

// State
const findingData = ref(null)
const loading = ref(false)
const error = ref(null)

// Fetch finding data on component mount
onMounted(async () => {
  await fetchFindingData()
})

// Methods
async function fetchFindingData() {
  try {
    loading.value = true
    error.value = null
    
          const response = await axios.get(API_ENDPOINTS.AUDIT_FINDINGS_DETAILS(auditFindingId.value))
    
    if (response.data && response.data.success) {
      findingData.value = response.data.data
    } else {
      throw new Error(response.data.message || 'Failed to fetch audit finding details')
    }
  } catch (err) {
    console.error('Error fetching audit finding details:', err)
    error.value = err.response?.data?.message || 'Failed to fetch audit finding details. Please try again.'
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

function getStatusClass(status) {
  if (!status) return ''
  const statusLower = status.toLowerCase()
  if (statusLower.includes('fully') || statusLower.includes('compliant')) {
    return 'status-compliant'
  }
  if (statusLower.includes('partially')) {
    return 'status-partially'
  }
  if (statusLower.includes('non') || statusLower.includes('not compliant')) {
    return 'status-non-compliant'
  }
  if (statusLower.includes('not applicable')) {
    return 'status-not-applicable'
  }
  return ''
}

function getStatusIcon(status) {
  if (!status) return 'fas fa-question-circle'
  const statusLower = status.toLowerCase()
  if (statusLower.includes('fully') || statusLower.includes('compliant')) {
    return 'fas fa-check-circle'
  }
  if (statusLower.includes('partially')) {
    return 'fas fa-exclamation-triangle'
  }
  if (statusLower.includes('non') || statusLower.includes('not compliant')) {
    return 'fas fa-times-circle'
  }
  if (statusLower.includes('not applicable')) {
    return 'fas fa-info-circle'
  }
  return 'fas fa-question-circle'
}

function getSeverityClass(severity) {
  if (!severity) return ''
  const severityLower = severity.toLowerCase()
  if (severityLower.includes('major')) {
    return 'severity-major'
  }
  if (severityLower.includes('minor')) {
    return 'severity-minor'
  }
  return ''
}

function getCriticalityClass(criticality) {
  if (!criticality) return ''
  const criticalityLower = criticality.toLowerCase()
  if (criticalityLower === 'high') {
    return 'criticality-high'
  }
  if (criticalityLower === 'medium') {
    return 'criticality-medium'
  }
  if (criticalityLower === 'low') {
    return 'criticality-low'
  }
  return ''
}

function goBack() {
  router.back()
}

function viewAuditReport(auditId) {
  if (auditId) {
    router.push(`/audit-report/${auditId}`)
  }
}
</script>

<style scoped>
.audit-finding-details-container {
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

.finding-title {
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

.finding-content {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.finding-section {
  padding: 24px;
  border-bottom: 1px solid #e5e7eb;
}

.finding-section:last-child {
  border-bottom: none;
}

.finding-section h2 {
  color: #1f2937;
  margin-bottom: 20px;
  font-size: 1.5rem;
  font-weight: 600;
  border-bottom: 2px solid #3b82f6;
  padding-bottom: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.info-label {
  font-weight: 600;
  color: #4b5563;
  font-size: 0.875rem;
}

.info-value {
  color: #1f2937;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 6px;
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

.evidence-content {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.no-data {
  color: #9ca3af;
  font-style: italic;
}

.audit-link {
  color: #2563eb;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.audit-link:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

/* Status classes */
.status-compliant {
  color: #15803d;
  font-weight: 600;
}

.status-partially {
  color: #d97706;
  font-weight: 600;
}

.status-non-compliant {
  color: #dc2626;
  font-weight: 600;
}

.status-not-applicable {
  color: #64748b;
  font-weight: 600;
}

/* Severity classes */
.severity-major {
  color: #dc2626;
  font-weight: 600;
}

.severity-minor {
  color: #f59e0b;
  font-weight: 600;
}

/* Criticality classes */
.criticality-high {
  color: #dc2626;
  font-weight: 600;
}

.criticality-medium {
  color: #f59e0b;
  font-weight: 600;
}

.criticality-low {
  color: #10b981;
  font-weight: 600;
}

/* Responsive Design */
@media (max-width: 768px) {
  .audit-finding-details-container {
    margin-left: 0;
    padding: 16px;
  }
  
  .action-bar {
    position: relative;
    top: 0;
    right: 0;
    margin-bottom: 20px;
  }
  
  .finding-title {
    margin-top: 0;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .finding-section {
    padding: 16px;
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.fa-spin {
  animation: spin 1s linear infinite;
}
</style> 